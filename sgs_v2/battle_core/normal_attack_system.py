from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Any

from .battle_finalization_coordinator import BattleFinalizationCoordinator
from .context import BattleContext
from .damage_instance_coordinator import DamageInstanceCoordinator
from .damage_resolution_system import DamageResolutionResult, DamageResolutionSystem
from .damage_system import DamageRequest, DamageResult
from .enums import DamageSourceType, DamageType
from .events import EventType
from .execution_right_system import (
    ActionScope,
    AssaultDispatchPort,
    ComboCheckpointState,
    FutureAdmissionGate,
    FutureBranchKind,
)
from .official_state_catalog import OfficialStateId
from .operation_identity import (
    ActionId,
    NormalAttackInstanceId,
    OperationLineage,
    SourceType,
    TargetResolutionId,
)
from .stage9_state_runtime import Stage9StateRuntime
from .target_resolution_system import RedirectReason, TargetResolutionResult, TargetResolutionSystem
from .target_system import TargetSystem
from .troop_system import TroopChangeResult
from .unit import UnitRuntime


@dataclass(frozen=True, slots=True)
class NormalAttackResult:
    """Immutable result of a NormalAttack master execution."""

    actor_id: str
    target_id: str | None
    damage: DamageResult | None
    troop_change: TroopChangeResult | None
    normal_attack_id: NormalAttackInstanceId | None = None
    target_resolution: TargetResolutionResult | None = None
    resolution: DamageResolutionResult | None = None
    combo_attack_result: NormalAttackResult | None = None

    @property
    def actual_target_id(self) -> str | None:
        if self.target_resolution is not None:
            return self.target_resolution.post_redirect_actual_target
        return self.target_id

    @property
    def combo_second_attack(self) -> NormalAttackResult | None:
        return self.combo_attack_result


class NormalAttackSystem:
    """Unique physical NormalAttack lifecycle master in Stage9.

    Responsibilities:
    - Normal attack permission
    - NormalAttackInstanceId lifecycle
    - Target-resolution orchestration
    - Target lock (post_redirect_actual_target)
    - Main normal-hit dispatch through Stage9 DamageInstanceCoordinator
    - Ordered phase orchestration (Event ordering: NORMAL_ATTACK before DAMAGE_PREVENTED / DAMAGE_DEALT)
    - Assault admission boundary
    - Combo checkpoint boundary
    - Result assembly
    """

    def __init__(
        self,
        target_resolution_system: TargetResolutionSystem | TargetSystem | None = None,
        damage_instance_coordinator: DamageInstanceCoordinator | DamageResolutionSystem | None = None,
        *,
        future_admission_gate: FutureAdmissionGate | None = None,
        finalization_coordinator: BattleFinalizationCoordinator | None = None,
        assault_dispatch_port: AssaultDispatchPort | None = None,
        target_system: TargetSystem | None = None,
        damage_resolution_system: DamageResolutionSystem | None = None,
        state_runtime: Stage9StateRuntime | None = None,
    ) -> None:
        self._target_resolution_system: TargetResolutionSystem | None = None
        self._damage_instance_coordinator: DamageInstanceCoordinator | None = None
        self._targets: TargetSystem | None = target_system
        self._damage_resolution: DamageResolutionSystem | None = damage_resolution_system

        if isinstance(target_resolution_system, TargetResolutionSystem):
            self._target_resolution_system = target_resolution_system
        elif isinstance(target_resolution_system, TargetSystem):
            self._targets = target_resolution_system

        if isinstance(damage_instance_coordinator, DamageInstanceCoordinator):
            self._damage_instance_coordinator = damage_instance_coordinator
        elif isinstance(damage_instance_coordinator, DamageResolutionSystem):
            self._damage_resolution = damage_instance_coordinator

        self._future_admission_gate = future_admission_gate
        self._finalization_coordinator = finalization_coordinator
        self._assault_dispatch_port = assault_dispatch_port
        self._state_runtime = state_runtime

    @property
    def target_system(self) -> TargetSystem | None:
        return self._targets

    @property
    def target_resolution_system(self) -> TargetResolutionSystem | None:
        return self._target_resolution_system

    @property
    def damage_instance_coordinator(self) -> DamageInstanceCoordinator | None:
        return self._damage_instance_coordinator

    @property
    def future_admission_gate(self) -> FutureAdmissionGate | None:
        return self._future_admission_gate

    @property
    def finalization_coordinator(self) -> BattleFinalizationCoordinator | None:
        return self._finalization_coordinator

    @property
    def assault_dispatch_port(self) -> AssaultDispatchPort | None:
        return self._assault_dispatch_port

    @property
    def state_runtime(self) -> Stage9StateRuntime | None:
        return self._state_runtime

    def can_normal_attack(self, context: BattleContext, actor: UnitRuntime) -> bool:
        """Evaluates standard live normal attack permission (alive, no DISARM, no STUN)."""
        if not actor.is_alive or actor.troops <= 0:
            return False
        disarm_state_id = OfficialStateId.DISARM.value
        if context.states.has(owner_id=actor.unit_id, state_id=disarm_state_id):
            return False
        stun_state_id = OfficialStateId.STUN.value
        if context.states.has(owner_id=actor.unit_id, state_id=stun_state_id):
            return False
        return True

    def _is_latched_or_finalized(self) -> bool:
        if self._finalization_coordinator is not None:
            return self._finalization_coordinator.is_latched_or_finalized
        if self._future_admission_gate is not None:
            return self._future_admission_gate.coordinator.is_latched_or_finalized
        return False

    def execute(
        self,
        context: BattleContext,
        actor: UnitRuntime,
        action_scope: ActionScope | None = None,
    ) -> NormalAttackResult:
        """Executes NormalAttack #1 and orchestrates the pre-checkpoint lifecycle and Combo #2."""
        if action_scope is not None:
            coordinator = getattr(action_scope, "_coordinator", None)
            if coordinator is None:
                raise RuntimeError(
                    f"ActionScope '{action_scope.action_id}' has no coordinator capability binding"
                )
            coordinator.validate_and_consume_primary_normal_attack(
                context=context,
                scope=action_scope,
                expected_actor_id=actor.unit_id,
            )

        if not actor.is_alive or actor.troops <= 0:
            return NormalAttackResult(actor.unit_id, None, None, None, normal_attack_id=None)

        stun_state_id = OfficialStateId.STUN.value
        if context.states.has(owner_id=actor.unit_id, state_id=stun_state_id):
            context.event_bus.publish(
                event_type=EventType.ACTION_BLOCKED,
                phase=context.current_phase,
                round_no=context.current_round,
                actor_id=actor.unit_id,
                payload={
                    "action_type": "ALL",
                    "reason_state_id": stun_state_id,
                },
            )
            return NormalAttackResult(actor.unit_id, None, None, None, normal_attack_id=None)

        disarm_state_id = OfficialStateId.DISARM.value
        if context.states.has(owner_id=actor.unit_id, state_id=disarm_state_id):
            context.event_bus.publish(
                event_type=EventType.ACTION_BLOCKED,
                phase=context.current_phase,
                round_no=context.current_round,
                actor_id=actor.unit_id,
                payload={
                    "action_type": "NORMAL_ATTACK",
                    "reason_state_id": disarm_state_id,
                },
            )
            return NormalAttackResult(actor.unit_id, None, None, None, normal_attack_id=None)

        if action_scope is not None:
            action_scope.physical_normal_attack_count += 1

        na_1_id = context.id_allocator.allocate_normal_attack_id()
        return self._execute_single_hit(
            context=context,
            actor=actor,
            action_scope=action_scope,
            normal_attack_id=na_1_id,
            target_resolution=None,
            combo_checkpoint_allowed=True,
        )

    def _execute_single_hit(
        self,
        context: BattleContext,
        actor: UnitRuntime,
        action_scope: ActionScope | None,
        normal_attack_id: NormalAttackInstanceId,
        target_resolution: TargetResolutionResult | None,
        combo_checkpoint_allowed: bool,
    ) -> NormalAttackResult:
        # Step 1: Fresh Target Resolution
        if target_resolution is None:
            if self._target_resolution_system is not None:
                target_resolution = self._target_resolution_system.resolve(
                    context,
                    actor,
                    normal_attack_id=normal_attack_id,
                )
            elif self._targets is not None:
                legacy_target = self._targets.random_enemy(context, actor)
                if legacy_target is not None:
                    target_resolution = TargetResolutionResult(
                        resolution_id=context.id_allocator.allocate_target_resolution_id(),
                        normal_attack_id=normal_attack_id,
                        intended_attack_target=legacy_target.unit_id,
                        post_redirect_actual_target=legacy_target.unit_id,
                        redirect_source=None,
                        redirect_reason=RedirectReason.NONE,
                    )

        if target_resolution is None:
            return NormalAttackResult(
                actor.unit_id,
                None,
                None,
                None,
                normal_attack_id=normal_attack_id,
            )

        # Step 3: Target lock
        actual_target_id = target_resolution.post_redirect_actual_target
        intended_target_id = target_resolution.intended_attack_target
        target_res_id = target_resolution.resolution_id
        root_action_id: ActionId | None = action_scope.action_id if action_scope is not None else None

        # Step 4: Lineage & Request
        lineage = OperationLineage(
            root_action_id=root_action_id,
            parent_normal_attack_id=normal_attack_id,
            parent_damage_instance_id=None,
            source_type=SourceType.NORMAL_ATTACK,
            physical_attacker=actor.unit_id,
            physical_skill=None,
            credit_owner=actor.unit_id,
        )
        request = DamageRequest(
            source_id=actor.unit_id,
            target_id=actual_target_id,
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.NORMAL_ATTACK,
            coefficient=1.0,
        )

        # Step 5: NORMAL_ATTACK event observation hook
        def on_calculated(damage: DamageResult) -> None:
            context.event_bus.publish(
                event_type=EventType.NORMAL_ATTACK,
                phase=context.current_phase,
                round_no=context.current_round,
                actor_id=actor.unit_id,
                target_id=actual_target_id,
                payload={
                    "damage_type": damage.damage_type.value,
                    "source_type": damage.source_type.value,
                    "coefficient": damage.coefficient,
                    "base_damage": damage.base_damage,
                    "scaled_damage": damage.scaled_damage,
                    "requested_damage": damage.final_damage,
                    "prevented": damage.prevented,
                    "prevented_by_state_id": damage.prevented_by_state_id,
                    "action_id": str(root_action_id) if root_action_id else None,
                    "normal_attack_id": str(normal_attack_id),
                    "target_resolution_id": str(target_res_id),
                    "intended_target": intended_target_id,
                    "actual_target": actual_target_id,
                },
            )

        # Step 6: Dispatch via Stage9 DamageInstanceCoordinator
        if self._damage_instance_coordinator is not None:
            execution = self._damage_instance_coordinator.execute_partitioned_damage_instance(
                context=context,
                request=request,
                lineage=lineage,
                on_calculated=on_calculated,
            )
            damage_result = execution.damage_result
            resolution_result = execution.resolution
            troop_change = execution.resolution.troop_change
        elif self._damage_resolution is not None:
            damage_result = self._damage_resolution.calculate(context, request)
            on_calculated(damage_result)
            resolution_result = self._damage_resolution.apply_result(context, damage_result)
            troop_change = resolution_result.troop_change
        else:
            raise RuntimeError("NormalAttackSystem requires damage execution capability")

        hit_result = NormalAttackResult(
            actor_id=actor.unit_id,
            target_id=actual_target_id,
            damage=damage_result,
            troop_change=troop_change,
            normal_attack_id=normal_attack_id,
            target_resolution=target_resolution,
            resolution=resolution_result,
        )

        # Step 7: Pre-checkpoint synchronous lifecycle
        # A. Assault admission seam (runs for all physical normal attacks: NA #1 and NA #2)
        if (
            self._assault_dispatch_port is not None
            and self._future_admission_gate is not None
            and actor.is_alive
            and not self._is_latched_or_finalized()
        ):
            parent_scope = f"normal_attack_{normal_attack_id}_actor_{actor.unit_id}"
            assault_permit = self._future_admission_gate.request_admission(
                branch_kind=FutureBranchKind.ASSAULT,
                parent_scope_identity=parent_scope,
            )
            if assault_permit is not None:
                self._assault_dispatch_port.dispatch(
                    context=context,
                    permit=assault_permit,
                    parent_scope_identity=parent_scope,
                    actor=actor,
                    actual_target_id=actual_target_id,
                )

        if not combo_checkpoint_allowed:
            return hit_result

        # B. Combo Checkpoint
        if action_scope is not None and action_scope.combo_checkpoint_state == ComboCheckpointState.NOT_REACHED:
            # Checkpoint Local Gate:
            # 1. Attacker alive? (REG-CMB-05)
            if not actor.is_alive or actor.troops <= 0:
                return hit_result

            # 2. Battle lifecycle permits reaching this boundary? (FINAL_03)
            if self._is_latched_or_finalized():
                return hit_result

            # Only when local gates pass: transition to REACHED
            action_scope.combo_checkpoint_state = ComboCheckpointState.REACHED

            # 3. Valid Action grant? (REG-CMB-02, REG-CMB-03)
            grant = action_scope.combo_grant
            if grant is None or not grant.is_valid(context):
                return hit_result

            # Atomic Consume: grant -> CONSUMED, checkpoint -> CONSUMED (REG-CMB-04)
            grant.consume()
            action_scope.combo_checkpoint_state = ComboCheckpointState.CONSUMED

            # cfg230-equivalent fact emission
            context.event_bus.publish(
                event_type=EventType.COMBO_OPPORTUNITY_CONSUMED,
                phase=context.current_phase,
                round_no=context.current_round,
                actor_id=actor.unit_id,
                payload={
                    "action_id": str(action_scope.action_id),
                    "granting_instance_id": grant.granting_instance_id,
                    "source_unit": grant.source_unit,
                    "source_skill": grant.source_skill,
                },
            )

            # Standard can_normal_attack live gate for #2:
            if not actor.is_alive or actor.troops <= 0:
                return hit_result

            stun_state_id = OfficialStateId.STUN.value
            if context.states.has(owner_id=actor.unit_id, state_id=stun_state_id):
                context.event_bus.publish(
                    event_type=EventType.ACTION_BLOCKED,
                    phase=context.current_phase,
                    round_no=context.current_round,
                    actor_id=actor.unit_id,
                    payload={"action_type": "ALL", "reason_state_id": stun_state_id},
                )
                return hit_result

            disarm_state_id = OfficialStateId.DISARM.value
            if context.states.has(owner_id=actor.unit_id, state_id=disarm_state_id):
                context.event_bus.publish(
                    event_type=EventType.ACTION_BLOCKED,
                    phase=context.current_phase,
                    round_no=context.current_round,
                    actor_id=actor.unit_id,
                    payload={"action_type": "NORMAL_ATTACK", "reason_state_id": disarm_state_id},
                )
                return hit_result

            # FutureAdmission gate for COMBO_SECOND_NORMAL_ATTACK:
            if self._future_admission_gate is None:
                raise RuntimeError(
                    "NormalAttackSystem requires FutureAdmissionGate to admit COMBO_SECOND_NORMAL_ATTACK"
                )

            parent_scope = f"combo_action_{action_scope.action_id}_actor_{actor.unit_id}"
            permit = self._future_admission_gate.request_admission(
                branch_kind=FutureBranchKind.COMBO_SECOND_NORMAL_ATTACK,
                parent_scope_identity=parent_scope,
            )
            if permit is None:
                return hit_result

            # STRICT ARCHITECTURAL GATE: consume permit BEFORE allocating NA #2 ID
            self._future_admission_gate.consume_permit(
                permit=permit,
                expected_branch_kind=FutureBranchKind.COMBO_SECOND_NORMAL_ATTACK,
                expected_parent_scope_identity=parent_scope,
            )

            # ONLY AFTER permit consumed: increment physical count and allocate NA #2 ID
            action_scope.physical_normal_attack_count += 1
            na_2_id = context.id_allocator.allocate_normal_attack_id()

            # Dispatch NA #2 with fresh target resolution and combo_checkpoint_allowed = False (INV-10, INV-11, INV-12)
            # NA #2 will execute its own Assault seam, but cannot open another Combo checkpoint
            hit_2_result = self._execute_single_hit(
                context=context,
                actor=actor,
                action_scope=action_scope,
                normal_attack_id=na_2_id,
                target_resolution=None,
                combo_checkpoint_allowed=False,
            )
            hit_result = dataclasses.replace(hit_result, combo_attack_result=hit_2_result)

        return hit_result
