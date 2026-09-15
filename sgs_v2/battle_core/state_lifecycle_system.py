from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from .enums import BattlePhase
from .events import EventType
from .official_state_catalog import (
    OfficialStateId,
    get_stage10_persistent_params_type,
)
from .skill_runtime import SkillSlot
from .stage9_state_params import (
    ComboStateParams,
    DamageShareStateParams,
    DistributionStateParams,
    GuardStateParams,
    TauntStateParams,
)
from .stage10_state_params import (
    ContinuousDamageStateParams,
    FirstAidStateParams,
    RecuperationStateParams,
)
from .state_generation import (
    PersistentLifecycleWindow,
    StateApplicationGenerationId,
    StateGenerationAllocator,
)
from .state_instance import StateInstance
from .state_runtime_params import (
    EmptyStateRuntimeParams,
    StateRuntimeParams,
    state_runtime_params_event_payload,
)

if TYPE_CHECKING:
    from .context import BattleContext


_AUTO_EXPIRE_PHASES = frozenset(
    {
        BattlePhase.ROUND_START.value,
        BattlePhase.ROUND_END.value,
    }
)

_PHASE_ORDER = {
    "NOT_STARTED": -1,
    BattlePhase.PRE_BATTLE.value: 0,
    BattlePhase.ROUND_START.value: 1,
    BattlePhase.ACTION_ORDER.value: 2,
    BattlePhase.UNIT_ACTION_START.value: 3,
    BattlePhase.UNIT_ACTION.value: 4,
    BattlePhase.UNIT_ACTION_END.value: 5,
    BattlePhase.ROUND_END.value: 6,
    BattlePhase.BATTLE_END.value: 7,
}


_STAGE10_PERSISTENT_STATE_IDS = frozenset(
    {
        OfficialStateId.BURN.value,
        OfficialStateId.FLOOD.value,
        OfficialStateId.POISON.value,
        OfficialStateId.ROUT.value,
        OfficialStateId.SANDSTORM.value,
        OfficialStateId.REBELLION.value,
        OfficialStateId.FIRST_AID.value,
        OfficialStateId.RECUPERATION.value,
    }
)


def _is_stage10_persistent_state(
    state_id: str,
    runtime_params: StateRuntimeParams | None = None,
    duration_rounds: int | None = None,
    lifecycle_window: PersistentLifecycleWindow | None = None,
) -> bool:
    if state_id in _STAGE10_PERSISTENT_STATE_IDS:
        return True
    if isinstance(
        runtime_params,
        (ContinuousDamageStateParams, FirstAidStateParams, RecuperationStateParams),
    ):
        return True
    if duration_rounds is not None or lifecycle_window is not None:
        return True
    return False


class StateLifecycleSystem:
    """状态加入、显式移除与自然到期的唯一正式写入口。"""

    def __init__(self, allocator: StateGenerationAllocator | None = None) -> None:
        self._allocator = allocator or StateGenerationAllocator()

    def calculate_lifecycle_window(
        self,
        context: BattleContext,
        *,
        owner_id: str,
        duration_rounds: int,
    ) -> PersistentLifecycleWindow:
        if not isinstance(duration_rounds, int) or isinstance(duration_rounds, bool):
            raise TypeError("duration_rounds must be an int")
        if duration_rounds < 1:
            raise ValueError("duration_rounds must be >= 1")

        if (
            context.current_round == 0
            or context.current_phase == BattlePhase.PRE_BATTLE.value
        ):
            return PersistentLifecycleWindow(
                application_phase=BattlePhase.PRE_BATTLE.value,
                application_round=0,
                first_eligible_round=1,
                last_eligible_round=duration_rounds,
                max_opportunities_per_owner_round=1,
            )

        app_round = context.current_round
        app_phase = context.current_phase
        if context.action_progress.has_acted_in_round(owner_id, app_round):
            first_eligible = app_round + 1
            last_eligible = app_round + duration_rounds
        else:
            first_eligible = app_round
            last_eligible = app_round + duration_rounds - 1

        return PersistentLifecycleWindow(
            application_phase=app_phase,
            application_round=app_round,
            first_eligible_round=first_eligible,
            last_eligible_round=last_eligible,
            max_opportunities_per_owner_round=1,
        )

    def apply(
        self,
        context: BattleContext,
        *,
        state_id: str,
        owner_id: str,
        source_id: str | None = None,
        source_skill_id: str | None = None,
        source_skill_slot: SkillSlot | None = None,
        expires_round: int | None = None,
        expires_phase: str | None = None,
        runtime_params: StateRuntimeParams | None = None,
        duration_rounds: int | None = None,
        lifecycle_window: PersistentLifecycleWindow | None = None,
    ) -> StateInstance:
        definition = context.states.get_definition(state_id)
        context.get_unit(owner_id)
        if source_id is not None:
            context.get_unit(source_id)

        if source_skill_slot is not None and not isinstance(source_skill_slot, SkillSlot):
            raise TypeError(
                f"source_skill_slot must be a SkillSlot or None, got {type(source_skill_slot)}"
            )

        if source_id is not None and source_skill_id is not None:
            for existing in context.states.find(
                owner_id=owner_id,
                state_id=state_id,
                source_id=source_id,
            ):
                if existing.source_skill_id == source_skill_id:
                    if existing.source_skill_slot != source_skill_slot:
                        raise ValueError(
                            f"same-source reapply slot mismatch for state '{state_id}' on unit '{owner_id}': "
                            f"existing slot is {existing.source_skill_slot}, incoming slot is {source_skill_slot}"
                        )

        self._validate_expiration(
            applied_round=context.current_round,
            applied_phase=context.current_phase,
            expires_round=expires_round,
            expires_phase=expires_phase,
        )

        is_stage10_persistent = _is_stage10_persistent_state(
            state_id=state_id,
            runtime_params=runtime_params,
            duration_rounds=duration_rounds,
            lifecycle_window=lifecycle_window,
        )

        if runtime_params is None:
            if definition.runtime_params_type is EmptyStateRuntimeParams:
                actual_runtime_params = EmptyStateRuntimeParams()
            else:
                try:
                    actual_runtime_params = definition.runtime_params_type()
                except TypeError:
                    actual_runtime_params = EmptyStateRuntimeParams()
        else:
            actual_runtime_params = runtime_params

        if not isinstance(actual_runtime_params, definition.runtime_params_type):
            if is_stage10_persistent:
                expected_stage10_type = get_stage10_persistent_params_type(state_id)
                if not isinstance(actual_runtime_params, expected_stage10_type):
                    raise TypeError(
                        "runtime_params type mismatch for state "
                        f"{state_id}: expected {expected_stage10_type.__name__}, "
                        f"got {type(actual_runtime_params).__name__}"
                    )
            else:
                raise TypeError(
                    "runtime_params type mismatch for state "
                    f"{state_id}: expected {definition.runtime_params_type.__name__}, "
                    f"got {type(actual_runtime_params).__name__}"
                )

        if state_id == OfficialStateId.COMBO.value:
            existing_combo = context.states.find(
                owner_id=owner_id,
                state_id=OfficialStateId.COMBO.value,
            )
            if existing_combo:
                raise ValueError(
                    f"COMBO already exists on unit '{owner_id}', cannot stack (First-In-Wins)"
                )

        if state_id == OfficialStateId.GUARD.value and isinstance(actual_runtime_params, GuardStateParams):
            context.get_unit(actual_runtime_params.protector_id)
            if actual_runtime_params.protector_id == owner_id:
                raise ValueError(
                    f"Self-guard is forbidden: protector_id '{actual_runtime_params.protector_id}' "
                    f"cannot equal owner_id '{owner_id}'"
                )
        if state_id == OfficialStateId.TAUNT.value and isinstance(actual_runtime_params, TauntStateParams):
            if (
                actual_runtime_params.taunt_target_id is not None
                and actual_runtime_params.taunt_target_id != source_id
            ):
                raise ValueError(
                    f"taunt_target_id '{actual_runtime_params.taunt_target_id}' "
                    f"cannot disagree with authoritative source_id '{source_id}'"
                )
        if state_id == OfficialStateId.DAMAGE_SHARE.value:
            assert isinstance(actual_runtime_params, DamageShareStateParams)
            context.get_unit(actual_runtime_params.sharer_id)
            if actual_runtime_params.sharer_id == owner_id:
                raise ValueError("Self-share is forbidden")
        if state_id == OfficialStateId.DAMAGE_SPLIT.value:
            assert isinstance(actual_runtime_params, DistributionStateParams)

        # Phase 9.5 authoritative partition application arbitration. This remains
        # inside the sole state mutation owner and does not create a stacking framework.
        self._apply_partition_precedence(context, state_id=state_id, owner_id=owner_id)

        # Phase 9.7 source-bound coexistence / refresh and Chain single-instance
        # replacement. Physical mutation remains with this lifecycle owner.
        if state_id in (OfficialStateId.CLEAVE.value, OfficialStateId.COUNTERATTACK.value, OfficialStateId.CHAIN_LINK.value):
            for existing in context.states.find(owner_id=owner_id, state_id=state_id):
                if state_id == OfficialStateId.CHAIN_LINK.value or (
                    existing.source_id == source_id and existing.source_skill_id == source_skill_id
                ):
                    self.remove(context, existing.instance_id)

        is_stage10_persistent = _is_stage10_persistent_state(
            state_id=state_id,
            runtime_params=actual_runtime_params,
            duration_rounds=duration_rounds,
            lifecycle_window=lifecycle_window,
        )

        if is_stage10_persistent:
            existing_states = context.states.find(owner_id=owner_id, state_id=state_id)
            if existing_states:
                existing = existing_states[0]
                return self.refresh(
                    context,
                    instance_id=existing.instance_id,
                    source_id=source_id,
                    source_skill_id=source_skill_id,
                    source_skill_slot=source_skill_slot,
                    duration_rounds=duration_rounds,
                    lifecycle_window=lifecycle_window,
                    runtime_params=actual_runtime_params,
                )

            if lifecycle_window is not None:
                actual_window = lifecycle_window
            elif duration_rounds is not None:
                actual_window = self.calculate_lifecycle_window(
                    context, owner_id=owner_id, duration_rounds=duration_rounds
                )
            elif hasattr(actual_runtime_params, "lifecycle_window"):
                actual_window = getattr(actual_runtime_params, "lifecycle_window", None)
            else:
                actual_window = None

            allocator = getattr(context, "generation_allocator", None) or self._allocator
            gen_id = allocator.allocate()
            inst_id = context.states.next_instance_id()

            if isinstance(
                actual_runtime_params,
                (ContinuousDamageStateParams, FirstAidStateParams, RecuperationStateParams),
            ):
                actual_runtime_params = dataclasses.replace(
                    actual_runtime_params,
                    application_generation_id=gen_id,
                    lifecycle_window=actual_window,
                )
                if (
                    isinstance(actual_runtime_params, ContinuousDamageStateParams)
                    and actual_runtime_params.frozen_damage_basis is not None
                ):
                    updated_basis = dataclasses.replace(
                        actual_runtime_params.frozen_damage_basis,
                        application_generation_id=gen_id,
                        physical_state_instance_id=inst_id,
                        source_unit_id=source_id or actual_runtime_params.frozen_damage_basis.source_unit_id,
                    )
                    actual_runtime_params = dataclasses.replace(
                        actual_runtime_params,
                        frozen_damage_basis=updated_basis,
                    )

            instance = StateInstance(
                instance_id=inst_id,
                state_id=state_id,
                owner_id=owner_id,
                source_id=source_id,
                source_skill_id=source_skill_id,
                source_skill_slot=source_skill_slot,
                applied_round=context.current_round,
                applied_phase=context.current_phase,
                expires_round=expires_round,
                expires_phase=expires_phase,
                runtime_params=actual_runtime_params,
                current_generation_id=gen_id,
                lifecycle_window=actual_window,
            )
            context.states.add(instance)

            context.event_bus.publish(
                event_type=EventType.STATE_APPLIED,
                phase=context.current_phase,
                round_no=context.current_round,
                actor_id=source_id,
                target_id=owner_id,
                payload=self._event_payload(instance),
            )
            return instance

        allocator = getattr(context, "generation_allocator", None) or self._allocator
        gen_id = allocator.allocate()
        instance = StateInstance(
            instance_id=context.states.next_instance_id(),
            state_id=state_id,
            owner_id=owner_id,
            source_id=source_id,
            source_skill_id=source_skill_id,
            source_skill_slot=source_skill_slot,
            applied_round=context.current_round,
            applied_phase=context.current_phase,
            expires_round=expires_round,
            expires_phase=expires_phase,
            runtime_params=actual_runtime_params,
            current_generation_id=gen_id,
        )
        context.states.add(instance)

        context.event_bus.publish(
            event_type=EventType.STATE_APPLIED,
            phase=context.current_phase,
            round_no=context.current_round,
            actor_id=source_id,
            target_id=owner_id,
            payload=self._event_payload(instance),
        )
        return instance

    def _apply_partition_precedence(
        self,
        context: BattleContext,
        *,
        state_id: str,
        owner_id: str,
    ) -> None:
        if state_id not in (
            OfficialStateId.DAMAGE_SHARE.value,
            OfficialStateId.DAMAGE_SPLIT.value,
        ):
            return

        existing_share = context.states.find(
            owner_id=owner_id,
            state_id=OfficialStateId.DAMAGE_SHARE.value,
        )
        existing_distribution = context.states.find(
            owner_id=owner_id,
            state_id=OfficialStateId.DAMAGE_SPLIT.value,
        )

        if state_id == OfficialStateId.DAMAGE_SPLIT.value and existing_share:
            raise ValueError(
                "DISTRIBUTION application rejected because operational precedence is DAMAGE_SHARE > DISTRIBUTION"
            )

        # One physical instance per partition family. Incoming Share terminally
        # replaces Distribution; the removed Distribution cannot resurrect later.
        to_remove: tuple[StateInstance, ...]
        if state_id == OfficialStateId.DAMAGE_SHARE.value:
            to_remove = existing_share + existing_distribution
        else:
            to_remove = existing_distribution
        for existing in to_remove:
            self.remove(context, existing.instance_id)

    def update_runtime_params(
        self,
        context: BattleContext,
        instance_id: str,
        runtime_params: StateRuntimeParams,
    ) -> StateInstance:
        """Update runtime parameters of an existing state instance in StateRegistry.

        StateRegistry remains the sole physical storage, and StateLifecycleSystem
        remains the sole physical mutation owner.
        """
        instance = context.states.get(instance_id)

        if instance.state_id not in (
            OfficialStateId.GUARD.value,
            OfficialStateId.TAUNT.value,
            OfficialStateId.COMBO.value,
        ):
            raise ValueError(
                f"Runtime parameter maintenance is not authorized for state '{instance.state_id}' in Phase 9.6"
            )

        definition = context.states.get_definition(instance.state_id)
        if not isinstance(runtime_params, definition.runtime_params_type):
            if self._is_stage10_persistent_state(instance.state_id):
                expected_stage10_type = get_stage10_persistent_params_type(instance.state_id)
                if not isinstance(runtime_params, expected_stage10_type):
                    raise TypeError(
                        f"runtime_params type mismatch for state {instance.state_id}: "
                        f"expected {expected_stage10_type.__name__}, "
                        f"got {type(runtime_params).__name__}"
                    )
            else:
                raise TypeError(
                    f"runtime_params type mismatch for state {instance.state_id}: "
                    f"expected {definition.runtime_params_type.__name__}, "
                    f"got {type(runtime_params).__name__}"
                )

        if instance.state_id == OfficialStateId.GUARD.value:
            assert isinstance(runtime_params, GuardStateParams)
            if isinstance(instance.runtime_params, GuardStateParams):
                if runtime_params.protector_id != instance.runtime_params.protector_id:
                    raise ValueError(
                        f"Guard protector_id is immutable: existing '{instance.runtime_params.protector_id}' "
                        f"cannot be changed to '{runtime_params.protector_id}'"
                    )
            context.get_unit(runtime_params.protector_id)
            if runtime_params.protector_id == instance.owner_id:
                raise ValueError(
                    f"Self-guard is forbidden: protector_id '{runtime_params.protector_id}' "
                    f"cannot equal owner_id '{instance.owner_id}'"
                )

        if instance.state_id == OfficialStateId.TAUNT.value:
            assert isinstance(runtime_params, TauntStateParams)
            if isinstance(instance.runtime_params, TauntStateParams):
                if runtime_params.taunt_target_id != instance.runtime_params.taunt_target_id:
                    raise ValueError(
                        f"Taunt taunt_target_id is immutable: existing '{instance.runtime_params.taunt_target_id}' "
                        f"cannot be changed to '{runtime_params.taunt_target_id}'"
                    )
            if (
                runtime_params.taunt_target_id is not None
                and runtime_params.taunt_target_id != instance.source_id
            ):
                raise ValueError(
                    f"taunt_target_id '{runtime_params.taunt_target_id}' "
                    f"cannot disagree with authoritative source_id '{instance.source_id}'"
                )

        if instance.state_id == OfficialStateId.COMBO.value:
            assert isinstance(runtime_params, ComboStateParams)

        updated = dataclasses.replace(instance, runtime_params=runtime_params)
        return context.states.replace(updated)

    def process_combo_action_start(
        self,
        context: BattleContext,
        actor_id: str,
    ) -> StateInstance | None:
        """Maintains temporary Combo status at holder ACTION_START.

        P0 Lifecycle maintenance:
        1. If remaining_actions <= 0: physically remove instance (REG-CMB-01).
        2. If remaining_actions > 0: decrement remaining_actions by 1.
        3. Returns the surviving StateInstance or None if removed / none exists.
        """
        instances = context.states.find(
            owner_id=actor_id,
            state_id=OfficialStateId.COMBO.value,
        )
        if not instances:
            return None
        instance = instances[0]
        params = instance.runtime_params
        if isinstance(params, ComboStateParams) and params.remaining_actions is not None:
            if params.remaining_actions <= 0:
                self.remove(context, instance.instance_id)
                return None
            else:
                new_params = ComboStateParams(
                    remaining_actions=params.remaining_actions - 1,
                    is_suppressed=params.is_suppressed,
                )
                return self.update_runtime_params(context, instance.instance_id, new_params)
        return instance

    def refresh(
        self,
        context: BattleContext,
        *,
        instance_id: str,
        source_id: str | None = None,
        source_skill_id: str | None = None,
        source_skill_slot: SkillSlot | None = None,
        duration_rounds: int | None = None,
        lifecycle_window: PersistentLifecycleWindow | None = None,
        runtime_params: StateRuntimeParams | None = None,
    ) -> StateInstance:
        existing = context.states.get(instance_id)

        allocator = getattr(context, "generation_allocator", None) or self._allocator
        new_gen_id = allocator.allocate()

        if lifecycle_window is not None:
            new_window = lifecycle_window
        elif duration_rounds is not None:
            new_window = self.calculate_lifecycle_window(
                context, owner_id=existing.owner_id, duration_rounds=duration_rounds
            )
        else:
            new_window = (
                getattr(runtime_params, "lifecycle_window", None)
                or existing.lifecycle_window
            )

        new_source_id = source_id if source_id is not None else existing.source_id
        new_source_skill_id = (
            source_skill_id if source_skill_id is not None else existing.source_skill_id
        )
        new_source_skill_slot = (
            source_skill_slot if source_skill_slot is not None else existing.source_skill_slot
        )

        new_params = runtime_params if runtime_params is not None else existing.runtime_params

        if isinstance(
            new_params,
            (ContinuousDamageStateParams, FirstAidStateParams, RecuperationStateParams),
        ):
            new_params = dataclasses.replace(
                new_params,
                application_generation_id=new_gen_id,
                lifecycle_window=new_window,
            )
            if (
                isinstance(new_params, ContinuousDamageStateParams)
                and new_params.frozen_damage_basis is not None
            ):
                updated_basis = dataclasses.replace(
                    new_params.frozen_damage_basis,
                    application_generation_id=new_gen_id,
                    physical_state_instance_id=existing.instance_id,
                    source_unit_id=new_source_id or new_params.frozen_damage_basis.source_unit_id,
                )
                new_params = dataclasses.replace(
                    new_params,
                    frozen_damage_basis=updated_basis,
                )

        updated = dataclasses.replace(
            existing,
            source_id=new_source_id,
            source_skill_id=new_source_skill_id,
            source_skill_slot=new_source_skill_slot,
            applied_round=context.current_round,
            applied_phase=context.current_phase,
            runtime_params=new_params,
            current_generation_id=new_gen_id,
            lifecycle_window=new_window,
        )
        context.states.replace(updated)

        payload = {
            "physical_instance_id": existing.instance_id,
            "state_id": existing.state_id,
            "owner_id": existing.owner_id,
            "old_application_generation_id": str(existing.current_generation_id),
            "new_application_generation_id": str(new_gen_id),
            "old_source_id": existing.source_id,
            "new_source_id": new_source_id,
            "old_source_skill_id": existing.source_skill_id,
            "new_source_skill_id": new_source_skill_id,
            "old_source_skill_slot": existing.source_skill_slot,
            "new_source_skill_slot": new_source_skill_slot,
            "old_first_eligible_round": (
                existing.lifecycle_window.first_eligible_round
                if existing.lifecycle_window
                else None
            ),
            "new_first_eligible_round": (
                new_window.first_eligible_round if new_window else None
            ),
            "old_last_eligible_round": (
                existing.lifecycle_window.last_eligible_round
                if existing.lifecycle_window
                else None
            ),
            "new_last_eligible_round": (
                new_window.last_eligible_round if new_window else None
            ),
            "old_runtime_params_type": type(existing.runtime_params).__name__,
            "new_runtime_params_type": type(new_params).__name__,
        }
        context.event_bus.publish(
            event_type=EventType.STATE_REFRESHED,
            phase=context.current_phase,
            round_no=context.current_round,
            actor_id=new_source_id,
            target_id=existing.owner_id,
            payload=payload,
        )
        return updated

    def is_generation_eligible_at_action_start(
        self,
        context: BattleContext,
        instance: StateInstance,
        generation_id: StateApplicationGenerationId | None = None,
    ) -> bool:
        if instance.lifecycle_window is None:
            return False
        if (
            generation_id is not None
            and instance.current_generation_id != generation_id
        ):
            return False
        window = instance.lifecycle_window
        if not window.is_round_eligible(context.current_round):
            return False
        if (
            context.action_progress.current_acting_unit is not None
            and context.action_progress.current_acting_unit != instance.owner_id
        ):
            return False
        if not context.action_progress.has_consumed_action_start(
            instance.owner_id, context.current_round
        ):
            return False
        if not context.action_progress.is_action_start_opportunity_eligible(
            instance.owner_id, context.current_round
        ):
            return False
        return True

    def is_state_eligible_at_action_start(
        self,
        context: BattleContext,
        instance: StateInstance,
    ) -> bool:
        return self.is_generation_eligible_at_action_start(
            context, instance, instance.current_generation_id
        )

    def expire_state(
        self,
        context: BattleContext,
        instance_id: str,
        *,
        expected_generation_id: StateApplicationGenerationId | None = None,
        reason: str = "DURATION_EXPIRED",
    ) -> StateInstance | None:
        if instance_id not in context.states:
            return None
        instance = context.states.get(instance_id)
        if (
            expected_generation_id is not None
            and instance.current_generation_id != expected_generation_id
        ):
            return None

        context.states.remove(instance_id)
        payload = self._event_payload(instance)
        payload["application_generation_id"] = str(instance.current_generation_id)
        payload["reason"] = reason
        context.event_bus.publish(
            event_type=EventType.STATE_EXPIRED,
            phase=context.current_phase,
            round_no=context.current_round,
            actor_id=instance.source_id,
            target_id=instance.owner_id,
            payload=payload,
        )
        return instance

    def expire_if_current_generation(
        self,
        context: BattleContext,
        instance_id: str,
        generation_id: StateApplicationGenerationId,
        *,
        reason: str = "DURATION_EXPIRED",
    ) -> StateInstance | None:
        return self.expire_state(
            context,
            instance_id,
            expected_generation_id=generation_id,
            reason=reason,
        )

    def expire_eligible_states(
        self,
        context: BattleContext,
        owner_id: str,
    ) -> list[StateInstance]:
        expired: list[StateInstance] = []
        owner_instances = [
            inst
            for inst in context.states.find(owner_id=owner_id)
            if inst.lifecycle_window is not None
        ]
        for inst in owner_instances:
            if context.current_round >= inst.lifecycle_window.last_eligible_round:
                res = self.expire_state(
                    context,
                    inst.instance_id,
                    expected_generation_id=inst.current_generation_id,
                )
                if res is not None:
                    expired.append(res)
        return expired

    def clear_owner_on_defeat(
        self,
        context: BattleContext,
        owner_id: str,
    ) -> list[StateInstance]:
        owner_instances = sorted(
            context.states.find(owner_id=owner_id),
            key=lambda x: x.instance_id,
        )
        removed: list[StateInstance] = []
        for inst in owner_instances:
            context.states.remove(inst.instance_id)
            payload = self._event_payload(inst)
            payload["application_generation_id"] = str(inst.current_generation_id)
            payload["removal_reason"] = "OWNER_DEFEATED"
            payload["reason"] = "OWNER_DEFEATED"
            context.event_bus.publish(
                event_type=EventType.STATE_REMOVED,
                phase=context.current_phase,
                round_no=context.current_round,
                actor_id=inst.source_id,
                target_id=inst.owner_id,
                payload=payload,
            )
            removed.append(inst)
        return removed

    def remove(
        self,
        context: BattleContext,
        instance_id: str,
        *,
        reason: str | None = None,
    ) -> StateInstance:
        instance = context.states.remove(instance_id)
        payload = self._event_payload(instance)
        if reason is not None:
            payload["removal_reason"] = reason
            payload["reason"] = reason
        context.event_bus.publish(
            event_type=EventType.STATE_REMOVED,
            phase=context.current_phase,
            round_no=context.current_round,
            actor_id=instance.source_id,
            target_id=instance.owner_id,
            payload=payload,
        )
        return instance

    def expire_at(
        self,
        context: BattleContext,
        *,
        round_no: int,
        phase: str,
    ) -> list[StateInstance]:
        if round_no < 0:
            raise ValueError("round_no must be >= 0")
        if phase not in _AUTO_EXPIRE_PHASES:
            raise ValueError("phase must be ROUND_START or ROUND_END")

        expired = [
            instance
            for instance in context.states.find()
            if instance.expires_round == round_no
            and instance.expires_phase == phase
        ]

        for instance in expired:
            context.states.remove(instance.instance_id)
            context.event_bus.publish(
                event_type=EventType.STATE_EXPIRED,
                phase=phase,
                round_no=round_no,
                actor_id=instance.source_id,
                target_id=instance.owner_id,
                payload=self._event_payload(instance),
            )

        return expired

    @staticmethod
    def _validate_expiration(
        *,
        applied_round: int,
        applied_phase: str,
        expires_round: int | None,
        expires_phase: str | None,
    ) -> None:
        has_round = expires_round is not None
        has_phase = expires_phase is not None
        if has_round != has_phase:
            raise ValueError(
                "expires_round and expires_phase must both be set or both be None"
            )
        if expires_round is None:
            return
        if expires_round < 1:
            raise ValueError("expires_round must be >= 1")
        if expires_round < applied_round:
            raise ValueError("expires_round must be >= applied_round")
        if expires_phase not in _AUTO_EXPIRE_PHASES:
            raise ValueError("expires_phase must be ROUND_START or ROUND_END")

        if expires_round > applied_round:
            return

        try:
            applied_phase_order = _PHASE_ORDER[applied_phase]
        except KeyError as exc:
            raise ValueError(
                f"unknown applied_phase for expiration validation: {applied_phase}"
            ) from exc

        expires_phase_order = _PHASE_ORDER[expires_phase]
        if expires_phase_order <= applied_phase_order:
            raise ValueError(
                "expiration anchor must be a future lifecycle node"
            )

    @staticmethod
    def _event_payload(instance: StateInstance) -> dict[str, object]:
        params_type, params_payload = state_runtime_params_event_payload(
            instance.runtime_params
        )
        payload: dict[str, object] = {
            "instance_id": instance.instance_id,
            "state_id": instance.state_id,
            "owner_id": instance.owner_id,
            "source_id": instance.source_id,
            "source_skill_id": instance.source_skill_id,
            "applied_round": instance.applied_round,
            "applied_phase": instance.applied_phase,
            "expires_round": instance.expires_round,
            "expires_phase": instance.expires_phase,
            "runtime_params_type": params_type,
            "runtime_params": params_payload,
        }
        if instance.source_skill_slot is not None:
            payload["source_skill_slot"] = instance.source_skill_slot
        if instance.lifecycle_window is not None:
            if instance.current_generation_id is not None:
                payload["application_generation_id"] = str(instance.current_generation_id)
            payload["first_eligible_round"] = instance.lifecycle_window.first_eligible_round
            payload["last_eligible_round"] = instance.lifecycle_window.last_eligible_round
        return payload
