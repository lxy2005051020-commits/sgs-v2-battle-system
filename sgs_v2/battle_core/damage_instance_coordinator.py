from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, TYPE_CHECKING

from .battle_finalization_coordinator import BattleFinalizationCoordinator
from .context import BattleContext
from .chain_system import ResolvedDamageFact
from .damage_aftermath_port import create_damage_aftermath_fact
from .damage_partition_system import (
    DamagePartitionCoordinator,
    DamagePartitionPlan,
    DamageShareTransactionPlan,
    DistributionTransactionPlan,
    NoPartitionPlan,
)
from .damage_resolution_system import (
    DamageResolutionResult,
    DamageResolutionSystem,
    DamageSettlementRequest,
    SettlementOrigin,
)
from .damage_system import DamageRequest, DamageResult, DamageSystem
from .direct_troop_loss_system import (
    AttributedDirectTroopLoss,
    DirectTroopLossRequest,
    DirectTroopLossResolver,
)
from .enums import DamageSourceType
from .execution_right_system import DamageSettlementPermit
from .operation_identity import (
    ReactionBatchId,
    DamageInstanceId,
    OperationIdAllocator,
    OperationLineage,
    SourceType,
    _forbid_ordering,
)

if TYPE_CHECKING:
    from .effects import DamageEffect


class PartitionExecutionStatus(str, Enum):
    NONE = "NONE"
    COMPLETED = "COMPLETED"
    TARGET_DEATH_INTERRUPT = "TARGET_DEATH_INTERRUPT"


@dataclass(frozen=True, slots=True, order=False)
class DamageInstanceExecution:
    damage_instance_id: DamageInstanceId
    damage_result: DamageResult
    resolution: DamageResolutionResult
    partition_plan: DamagePartitionPlan | None
    partition_status: PartitionExecutionStatus
    direct_losses: tuple[AttributedDirectTroopLoss, ...]

    def __lt__(self, other: Any) -> bool:
        _forbid_ordering("DamageInstanceExecution", "<")

    def __le__(self, other: Any) -> bool:
        _forbid_ordering("DamageInstanceExecution", "<=")

    def __gt__(self, other: Any) -> bool:
        _forbid_ordering("DamageInstanceExecution", ">")

    def __ge__(self, other: Any) -> bool:
        _forbid_ordering("DamageInstanceExecution", ">=")


@dataclass(slots=True)
class _ActiveDamageInstanceRecord:
    damage_instance_id: DamageInstanceId
    lineage: OperationLineage
    owning_context: BattleContext
    permit_id: str | None = None
    permit_issued: bool = False
    permit_consumed: bool = False
    closed: bool = False


@dataclass(slots=True)
class _PermitRecord:
    permit: DamageSettlementPermit
    damage_instance_id: DamageInstanceId
    lineage: OperationLineage
    owning_context: BattleContext
    consumed: bool = False


class DamageInstanceCoordinator:
    """Stage9 DamageInstance orchestration owner.

    Phase 9.5 production path owns exactly-once Stage8 calculation, exactly-one
    partition arbitration, one target settlement permit, separate attributed direct
    troop-loss commits, and the real DamageInstance finalization barrier.
    """

    def __init__(
        self,
        damage_system: DamageSystem,
        damage_resolution_system: DamageResolutionSystem,
        *,
        partition_coordinator: DamagePartitionCoordinator | None = None,
        direct_troop_loss_resolver: DirectTroopLossResolver | None = None,
        finalization_coordinator: BattleFinalizationCoordinator | None = None,
        id_allocator: OperationIdAllocator | None = None,
        resolved_damage_callback=None,
        damage_aftermath_port: Any = None,
        defeat_cleanup_port: Any = None,
        attacker_recovery_system: Any = None,
    ) -> None:
        if not isinstance(damage_system, DamageSystem):
            raise TypeError(
                f"damage_system must be DamageSystem, got {type(damage_system)}"
            )
        if not isinstance(damage_resolution_system, DamageResolutionSystem):
            raise TypeError(
                f"damage_resolution_system must be DamageResolutionSystem, got {type(damage_resolution_system)}"
            )
        if partition_coordinator is not None and not isinstance(
            partition_coordinator, DamagePartitionCoordinator
        ):
            raise TypeError("partition_coordinator must be DamagePartitionCoordinator or None")
        if direct_troop_loss_resolver is not None and not isinstance(
            direct_troop_loss_resolver, DirectTroopLossResolver
        ):
            raise TypeError("direct_troop_loss_resolver must be DirectTroopLossResolver or None")
        if finalization_coordinator is not None and not isinstance(
            finalization_coordinator, BattleFinalizationCoordinator
        ):
            raise TypeError("finalization_coordinator must be BattleFinalizationCoordinator or None")
        self._damage_system = damage_system
        self._damage_resolution = damage_resolution_system
        self._partition = partition_coordinator
        self._direct_loss = direct_troop_loss_resolver
        self._finalization = finalization_coordinator
        self._id_allocator = id_allocator
        self._resolved_damage_callback = resolved_damage_callback
        self._damage_aftermath_port = damage_aftermath_port
        self._defeat_cleanup = defeat_cleanup_port
        self._attacker_recovery = attacker_recovery_system
        self._active_instances: dict[tuple[int, DamageInstanceId], _ActiveDamageInstanceRecord] = {}
        self._permits: dict[tuple[int, str], _PermitRecord] = {}
        self._damage_resolution.bind_coordinator(self)


    @property
    def damage_system(self) -> DamageSystem:
        return self._damage_system

    @property
    def damage_resolution_system(self) -> DamageResolutionSystem:
        return self._damage_resolution

    @property
    def partition_coordinator(self) -> DamagePartitionCoordinator | None:
        return self._partition

    @property
    def direct_troop_loss_resolver(self) -> DirectTroopLossResolver | None:
        return self._direct_loss

    @property
    def finalization_coordinator(self) -> BattleFinalizationCoordinator | None:
        return self._finalization

    def allocate_damage_instance_id(self, context: BattleContext) -> DamageInstanceId:
        if context is None or not isinstance(context, BattleContext):
            raise TypeError(f"context must be BattleContext, got {type(context)}")
        return context.id_allocator.allocate_damage_instance_id()

    def begin_damage_instance(
        self,
        context: BattleContext,
        lineage: OperationLineage,
    ) -> DamageInstanceId:
        if context is None or not isinstance(context, BattleContext):
            raise TypeError(f"context must be BattleContext, got {type(context)}")
        if lineage is None or not isinstance(lineage, OperationLineage):
            raise TypeError(f"lineage must be OperationLineage, got {type(lineage)}")
        damage_instance_id = context.id_allocator.allocate_damage_instance_id()
        self._active_instances[(id(context), damage_instance_id)] = _ActiveDamageInstanceRecord(
            damage_instance_id=damage_instance_id,
            lineage=lineage,
            owning_context=context,
        )
        return damage_instance_id

    def is_instance_active(
        self,
        damage_instance_id: DamageInstanceId,
        context: BattleContext | None = None,
    ) -> bool:
        if context is not None:
            record = self._active_instances.get((id(context), damage_instance_id))
            return record is not None and not record.closed
        return any(
            d_id == damage_instance_id and not record.closed
            for (_, d_id), record in self._active_instances.items()
        )

    def issue_settlement_permit(
        self,
        damage_instance_id: DamageInstanceId,
        lineage: OperationLineage,
        context: BattleContext | None = None,
    ) -> DamageSettlementPermit:
        if not isinstance(damage_instance_id, DamageInstanceId):
            raise TypeError("damage_instance_id must be DamageInstanceId")
        if not isinstance(lineage, OperationLineage):
            raise TypeError("lineage must be OperationLineage")

        record: _ActiveDamageInstanceRecord | None = None
        if context is not None:
            if not isinstance(context, BattleContext):
                raise TypeError(f"context must be BattleContext, got {type(context)}")
            record = self._active_instances.get((id(context), damage_instance_id))
        else:
            matching = [
                r
                for (_, d_id), r in self._active_instances.items()
                if d_id == damage_instance_id
            ]
            if len(matching) == 1:
                record = matching[0]
            elif len(matching) > 1:
                raise ValueError(
                    f"Ambiguous active DamageInstanceId '{damage_instance_id}' across multiple contexts; context must be provided"
                )

        if record is None:
            for (_, d_id), _record in self._active_instances.items():
                if d_id == damage_instance_id:
                    raise ValueError(
                        f"Supplied context does not match the owning BattleContext of DamageInstance '{damage_instance_id}'"
                    )
            raise ValueError(
                f"DamageInstanceId '{damage_instance_id}' is not an active instance owned by this coordinator"
            )
        if context is not None and context is not record.owning_context:
            raise ValueError("Supplied context does not match DamageInstance owning context")
        if record.closed:
            raise ValueError(f"DamageInstanceId '{damage_instance_id}' is closed")
        if record.lineage != lineage:
            raise ValueError("OperationLineage mismatch for settlement permit")
        if record.permit_issued:
            raise ValueError(
                f"A DamageSettlementPermit has already been issued for {damage_instance_id}. "
                "At most one permit may be issued per active DamageInstance."
            )

        owning_ctx = record.owning_context
        permit_id = owning_ctx.id_allocator.allocate_permit_id("dsp")
        permit = DamageSettlementPermit(
            permit_id=permit_id,
            damage_instance_id=damage_instance_id,
        )
        self._permits[(id(owning_ctx), permit_id)] = _PermitRecord(
            permit=permit,
            damage_instance_id=damage_instance_id,
            lineage=lineage,
            owning_context=owning_ctx,
        )
        record.permit_id = permit_id
        record.permit_issued = True
        return permit

    def validate_and_consume_permit(
        self,
        context: BattleContext,
        permit: DamageSettlementPermit,
        request: DamageSettlementRequest,
    ) -> None:
        if not isinstance(context, BattleContext):
            raise TypeError(f"context must be BattleContext, got {type(context)}")
        if not isinstance(permit, DamageSettlementPermit):
            raise TypeError("permit must be DamageSettlementPermit")
        if not isinstance(request, DamageSettlementRequest):
            raise TypeError("request must be DamageSettlementRequest")

        for (_, _), record in self._permits.items():
            if record.permit is permit and record.owning_context is not context:
                raise ValueError(
                    f"Permit '{permit.permit_id}' was issued for a different BattleContext"
                )

        permit_record = self._permits.get((id(context), permit.permit_id))
        if permit_record is None:
            raise ValueError(
                f"Permit '{permit.permit_id}' was not issued by this coordinator, closed, or not active"
            )
        if permit_record.permit is not permit:
            raise ValueError(
                f"Permit capability authenticity failure for '{permit.permit_id}'"
            )
        if permit_record.owning_context is not context:
            raise ValueError("Permit owning context mismatch")
        if permit.damage_instance_id != request.damage_instance_id:
            raise ValueError("Permit DamageInstanceId does not match settlement request")
        if permit_record.consumed:
            raise ValueError(
                f"Permit '{permit.permit_id}' has already been consumed (replay blocked)"
            )
        if permit_record.lineage != request.lineage:
            raise ValueError("OperationLineage mismatch between permit and settlement request")

        active_record = self._active_instances.get((id(context), permit.damage_instance_id))
        if active_record is None or active_record.closed:
            raise ValueError(f"DamageInstance '{permit.damage_instance_id}' is no longer active")
        if active_record.owning_context is not context:
            raise ValueError("DamageInstance owning context mismatch")
        if active_record.permit_consumed:
            raise ValueError("DamageInstance settlement permit has already been consumed")

        permit_record.consumed = True
        active_record.permit_consumed = True

    def execute_standard_damage_instance(
        self,
        context: BattleContext,
        request: DamageRequest,
        lineage: OperationLineage,
        *,
        assigned_target_damage: int | None = None,
    ) -> DamageResolutionResult:
        """Phase 9.4-compatible isolated/lower-level one-shot settlement seam."""
        if not isinstance(context, BattleContext):
            raise TypeError(f"context must be BattleContext, got {type(context)}")
        if not isinstance(request, DamageRequest):
            raise TypeError(f"request must be DamageRequest, got {type(request)}")
        if not isinstance(lineage, OperationLineage):
            raise TypeError(f"lineage must be OperationLineage, got {type(lineage)}")

        damage_instance_id = self.begin_damage_instance(context, lineage)
        try:
            damage_result = self._damage_system.calculate(context, request)
            if assigned_target_damage is None:
                target_amount = damage_result.final_damage
            else:
                if isinstance(assigned_target_damage, bool) or not isinstance(assigned_target_damage, int):
                    raise TypeError("assigned_target_damage must be an int")
                if assigned_target_damage < 0:
                    raise ValueError("assigned_target_damage must be >= 0")
                target_amount = assigned_target_damage
            permit = self.issue_settlement_permit(damage_instance_id, lineage, context)
            settlement_request = DamageSettlementRequest(
                damage_result=damage_result,
                assigned_target_damage=target_amount,
                damage_instance_id=damage_instance_id,
                lineage=lineage,
                origin=SettlementOrigin.STAGE9,
            )
            return self._damage_resolution.settle(
                context=context,
                request=settlement_request,
                permit=permit,
            )
        finally:
            self.close_damage_instance(damage_instance_id, context)

    def execute_damage_effect(
        self,
        context: BattleContext,
        effect: DamageEffect,
    ) -> DamageInstanceExecution:
        """Production Phase 9.5 ingress from authoritative EffectSourceRef."""
        from .effects import DamageEffect

        if not isinstance(effect, DamageEffect):
            raise TypeError(f"effect must be DamageEffect, got {type(effect)}")
        source_ref = effect.source_ref
        if source_ref is None:
            raise ValueError(
                "Production DamageEffect requires authoritative EffectSourceRef; reverse DamageSourceType inference is forbidden"
            )
        self._validate_production_source(effect)
        lineage = OperationLineage(
            root_action_id=None,
            parent_normal_attack_id=None,
            parent_damage_instance_id=None,
            source_type=source_ref.stage9_source_type,
            physical_attacker=source_ref.source_unit_id,
            physical_skill=source_ref.source_skill_id,
            credit_owner=source_ref.source_unit_id,
        )
        return self.execute_partitioned_damage_instance(
            context=context,
            request=effect.to_request(),
            lineage=lineage,
        )

    @staticmethod
    def _validate_production_source(effect: DamageEffect) -> None:
        source_ref = effect.source_ref
        assert source_ref is not None
        if source_ref.source_unit_id != effect.source_id:
            raise ValueError("EffectSourceRef source unit must match DamageEffect.source_id")
        if source_ref.source_skill_id != effect.source_skill_id:
            raise ValueError("EffectSourceRef source skill must match DamageEffect.source_skill_id")
        expected_stage8: DamageSourceType
        if source_ref.stage9_source_type == SourceType.ACTIVE_SKILL:
            expected_stage8 = DamageSourceType.SKILL
        elif source_ref.stage9_source_type == SourceType.PERIODIC_DAMAGE:
            expected_stage8 = DamageSourceType.CONTINUOUS
        else:
            raise ValueError(
                f"SourceType {source_ref.stage9_source_type.value} is not an authorized Phase 9.5 production DamageEffect source"
            )
        if effect.source_type != expected_stage8:
            raise ValueError(
                f"DamageEffect Stage8 source_type {effect.source_type.value} conflicts with authoritative Stage9 source_ref {source_ref.stage9_source_type.value}"
            )
        if source_ref.stage9_source_type == SourceType.PERIODIC_DAMAGE:
            if effect.source_state_id is None or effect.source_state_instance_id is None:
                raise ValueError("PERIODIC_DAMAGE requires state provenance IDs")

    def execute_partitioned_damage_instance(
        self,
        context: BattleContext,
        request: DamageRequest,
        lineage: OperationLineage,
        *,
        on_calculated: Callable[[DamageResult], None] | None = None,
        resolved_fact_consumer=None,
        admitted_reaction=None,
        on_target_settled=None,
    ) -> DamageInstanceExecution:
        """Full Phase 9.5 transaction used by production DamageEffect."""
        if self._partition is None or self._direct_loss is None or self._finalization is None:
            raise RuntimeError("Phase 9.5 production infrastructure is not fully bound")
        if not isinstance(context, BattleContext):
            raise TypeError(f"context must be BattleContext, got {type(context)}")
        if not isinstance(request, DamageRequest):
            raise TypeError(f"request must be DamageRequest, got {type(request)}")
        if not isinstance(lineage, OperationLineage):
            raise TypeError(f"lineage must be OperationLineage, got {type(lineage)}")

        if admitted_reaction is not None:
            if (not isinstance(admitted_reaction[0], ReactionBatchId)
                    or lineage.source_type is not SourceType.COUNTER
                    or request.source_type is not DamageSourceType.COUNTER):
                raise ValueError("Only an admitted Counter batch can extend standard local damage")
            self._finalization.validate_reaction(context, *admitted_reaction, executing=True)

        def finish(execution):
            # Attacker recovery consumes settled actual loss exactly once per parent
            # DamageInstance. It runs before derived callback admission and never
            # turns Share/Distribution direct loss into a second recovery trigger.
            if self._attacker_recovery is not None:
                self._attacker_recovery.resolve_parent_damage(
                    context,
                    lineage=lineage,
                    damage_result=execution.damage_result,
                    resolution=execution.resolution,
                    partition_plan=execution.partition_plan,
                    direct_losses=execution.direct_losses,
                )
            # Forward a resolved fact only. No state lookup, Chain rule, or permit logic.
            callback = resolved_fact_consumer if resolved_fact_consumer is not None else self._resolved_damage_callback
            if callback is not None and not execution.damage_result.prevented:
                callback(context, ResolvedDamageFact(execution.damage_instance_id,
                    execution.damage_result.target_id, lineage, execution.damage_result.damage_type,
                    execution.resolution.assigned_target_damage,
                    execution.resolution.actual_target_troop_loss))
            return execution

        damage_instance_id = self.begin_damage_instance(context, lineage)
        finalization_admitted = False
        try:
            if admitted_reaction is None:
                self._finalization.admit_damage_instance(context, damage_instance_id)
            else:
                self._finalization.admit_reaction_local_damage(context, damage_instance_id, *admitted_reaction)
            finalization_admitted = True
            damage_result = self._damage_system.calculate(context, request)
            if on_calculated is not None:
                on_calculated(damage_result)

            if damage_result.prevented:
                permit = self.issue_settlement_permit(damage_instance_id, lineage, context)
                resolution = self._settle_target(
                    context=context,
                    damage_instance_id=damage_instance_id,
                    lineage=lineage,
                    damage_result=damage_result,
                    assigned_target_damage=0,
                    permit=permit,
                )
                if on_target_settled is not None:
                    on_target_settled(context, resolution, damage_result)
                self._commit_aftermath(context, lineage, resolution, damage_result, damage_instance_id)
                return finish(DamageInstanceExecution(
                    damage_instance_id=damage_instance_id,
                    damage_result=damage_result,
                    resolution=resolution,
                    partition_plan=None,
                    partition_status=PartitionExecutionStatus.NONE,
                    direct_losses=(),
                ))

            plan = self._partition.plan(context, damage_instance_id, damage_result)
            permit = self.issue_settlement_permit(damage_instance_id, lineage, context)
            direct_losses: list[AttributedDirectTroopLoss] = []

            if isinstance(plan, DamageShareTransactionPlan):
                resolution = self._settle_target(
                    context=context,
                    damage_instance_id=damage_instance_id,
                    lineage=lineage,
                    damage_result=damage_result,
                    assigned_target_damage=plan.dtarget,
                    permit=permit,
                )
                if on_target_settled is not None:
                    on_target_settled(context, resolution, damage_result)
                self._observe_target_death(context, damage_instance_id, resolution)
                if resolution.target_defeated:
                    self._commit_aftermath(context, lineage, resolution, damage_result, damage_instance_id)
                    return finish(DamageInstanceExecution(
                        damage_instance_id=damage_instance_id,
                        damage_result=damage_result,
                        resolution=resolution,
                        partition_plan=plan,
                        partition_status=PartitionExecutionStatus.TARGET_DEATH_INTERRUPT,
                        direct_losses=(),
                    ))

                sharer = context.units.get(plan.sharer_id)
                if sharer is not None and sharer.is_alive and sharer.troops > 0:
                    direct = self._commit_direct_loss(
                        context=context,
                        plan=plan,
                        parent_lineage=lineage,
                        victim_id=plan.sharer_id,
                        theoretical_loss=plan.dsharer_theoretical,
                        source_type=SourceType.SHARE_DIRECT_LOSS,
                    )
                    direct_losses.append(direct.loss)
                    if direct.death_edge:
                        self._finalization.observe_damage_instance_death(
                            context, damage_instance_id
                        )
                self._commit_aftermath(context, lineage, resolution, damage_result, damage_instance_id)
                return finish(DamageInstanceExecution(
                    damage_instance_id=damage_instance_id,
                    damage_result=damage_result,
                    resolution=resolution,
                    partition_plan=plan,
                    partition_status=PartitionExecutionStatus.COMPLETED,
                    direct_losses=tuple(direct_losses),
                ))

            if isinstance(plan, DistributionTransactionPlan):
                for participant_id in plan.participant_ids:
                    if not self._partition.participant_is_jit_valid(
                        context, plan, participant_id
                    ):
                        continue
                    direct = self._commit_direct_loss(
                        context=context,
                        plan=plan,
                        parent_lineage=lineage,
                        victim_id=participant_id,
                        theoretical_loss=plan.dparticipant,
                        source_type=SourceType.DISTRIBUTION_DIRECT_LOSS,
                    )
                    direct_losses.append(direct.loss)
                    if direct.death_edge:
                        self._finalization.observe_damage_instance_death(
                            context, damage_instance_id
                        )

                resolution = self._settle_target(
                    context=context,
                    damage_instance_id=damage_instance_id,
                    lineage=lineage,
                    damage_result=damage_result,
                    assigned_target_damage=plan.dtarget,
                    permit=permit,
                )
                if on_target_settled is not None:
                    on_target_settled(context, resolution, damage_result)
                self._observe_target_death(context, damage_instance_id, resolution)
                self._commit_aftermath(context, lineage, resolution, damage_result, damage_instance_id)
                return finish(DamageInstanceExecution(
                    damage_instance_id=damage_instance_id,
                    damage_result=damage_result,
                    resolution=resolution,
                    partition_plan=plan,
                    partition_status=PartitionExecutionStatus.COMPLETED,
                    direct_losses=tuple(direct_losses),
                ))

            assert isinstance(plan, NoPartitionPlan)
            resolution = self._settle_target(
                context=context,
                damage_instance_id=damage_instance_id,
                lineage=lineage,
                damage_result=damage_result,
                assigned_target_damage=plan.dtotal,
                permit=permit,
            )
            if on_target_settled is not None:
                on_target_settled(context, resolution, damage_result)
            self._observe_target_death(context, damage_instance_id, resolution)
            self._commit_aftermath(context, lineage, resolution, damage_result, damage_instance_id)
            return finish(DamageInstanceExecution(
                damage_instance_id=damage_instance_id,
                damage_result=damage_result,
                resolution=resolution,
                partition_plan=plan,
                partition_status=PartitionExecutionStatus.NONE,
                direct_losses=(),
            ))
        finally:
            self.close_damage_instance(damage_instance_id, context)
            if finalization_admitted:
                self._finalization.complete_damage_instance(context, damage_instance_id)

    def _commit_aftermath(
        self,
        context: BattleContext,
        lineage: OperationLineage,
        resolution: DamageResolutionResult,
        damage_result: DamageResult,
        damage_instance_id: DamageInstanceId,
    ) -> Any:
        aftermath_port = (
            self._damage_aftermath_port
            or getattr(getattr(context, "systems", None), "damage_aftermath_port", None)
        )
        if aftermath_port is None:
            return None

        from .damage_aftermath_port import create_damage_aftermath_fact

        fact = create_damage_aftermath_fact(
            damage_instance_id=resolution.damage_instance_id or damage_instance_id,
            target_id=damage_result.target_id,
            source_type=lineage.source_type,
            damage_type=damage_result.damage_type,
            assigned_target_damage=resolution.assigned_target_damage,
            actual_target_troop_loss=resolution.actual_target_troop_loss,
            target_troops_after=resolution.target_troops_after,
            target_defeated=resolution.target_defeated,
            damage_result=damage_result,
        )
        return aftermath_port.commit_aftermath(context, fact)

    def _settle_target(
        self,
        *,
        context: BattleContext,
        damage_instance_id: DamageInstanceId,
        lineage: OperationLineage,
        damage_result: DamageResult,
        assigned_target_damage: int,
        permit: DamageSettlementPermit,
    ) -> DamageResolutionResult:
        settlement_request = DamageSettlementRequest(
            damage_result=damage_result,
            assigned_target_damage=assigned_target_damage,
            damage_instance_id=damage_instance_id,
            lineage=lineage,
            origin=SettlementOrigin.STAGE9,
        )
        return self._damage_resolution.settle(
            context,
            settlement_request,
            permit,
        )

    def _commit_direct_loss(
        self,
        *,
        context: BattleContext,
        plan: DamageShareTransactionPlan | DistributionTransactionPlan,
        parent_lineage: OperationLineage,
        victim_id: str,
        theoretical_loss: int,
        source_type: SourceType,
    ):
        assert self._direct_loss is not None
        lineage = OperationLineage(
            root_action_id=parent_lineage.root_action_id,
            parent_normal_attack_id=parent_lineage.parent_normal_attack_id,
            parent_damage_instance_id=plan.parent_damage_instance_id,
            source_type=source_type,
            physical_attacker=parent_lineage.physical_attacker,
            physical_skill=parent_lineage.physical_skill,
            credit_owner=parent_lineage.credit_owner,
        )
        request = DirectTroopLossRequest(
            partition_transaction_id=plan.partition_transaction_id,
            parent_damage_instance_id=plan.parent_damage_instance_id,
            source_type=source_type,
            physical_attacker=parent_lineage.physical_attacker,
            physical_skill=parent_lineage.physical_skill,
            victim=victim_id,
            credit_owner=parent_lineage.credit_owner,
            theoretical_loss=theoretical_loss,
            lineage=lineage,
        )
        return self._direct_loss.resolve(context, request)

    def _observe_target_death(
        self,
        context: BattleContext,
        damage_instance_id: DamageInstanceId,
        resolution: DamageResolutionResult,
    ) -> None:
        if resolution.target_defeated:
            assert self._finalization is not None
            self._finalization.observe_damage_instance_death(
                context, damage_instance_id
            )

    def close_damage_instance(
        self,
        damage_instance_id: DamageInstanceId,
        context: BattleContext,
    ) -> None:
        if context is None or not isinstance(context, BattleContext):
            raise TypeError(f"context must be BattleContext, got {type(context)}")
        if not isinstance(damage_instance_id, DamageInstanceId):
            raise TypeError("damage_instance_id must be DamageInstanceId")
        record = self._active_instances.pop((id(context), damage_instance_id), None)
        if record is not None:
            record.closed = True
            if record.permit_id is not None:
                self._permits.pop((id(context), record.permit_id), None)

    def release_damage_instance(
        self,
        damage_instance_id: DamageInstanceId,
        context: BattleContext,
    ) -> None:
        self.close_damage_instance(damage_instance_id, context)
