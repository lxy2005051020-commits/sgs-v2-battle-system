from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from .enums import BattlePhase
from .events import EventType
from .official_state_catalog import OfficialStateId
from .skill_runtime import SkillSlot
from .stage9_state_params import (
    DamageShareStateParams,
    DistributionStateParams,
    GuardStateParams,
    TauntStateParams,
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


class StateLifecycleSystem:
    """状态加入、显式移除与自然到期的唯一正式写入口。"""

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

        actual_runtime_params = (
            EmptyStateRuntimeParams()
            if runtime_params is None
            else runtime_params
        )
        if not isinstance(actual_runtime_params, definition.runtime_params_type):
            raise TypeError(
                "runtime_params type mismatch for state "
                f"{state_id}: expected {definition.runtime_params_type.__name__}, "
                f"got {type(actual_runtime_params).__name__}"
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

        if instance.state_id not in (OfficialStateId.GUARD.value, OfficialStateId.TAUNT.value):
            raise ValueError(
                f"Runtime parameter maintenance is not authorized for state '{instance.state_id}' in Phase 9.3"
            )

        definition = context.states.get_definition(instance.state_id)
        if not isinstance(runtime_params, definition.runtime_params_type):
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

        updated = dataclasses.replace(instance, runtime_params=runtime_params)
        return context.states.replace(updated)

    def remove(
        self,
        context: BattleContext,
        instance_id: str,
    ) -> StateInstance:
        instance = context.states.remove(instance_id)
        context.event_bus.publish(
            event_type=EventType.STATE_REMOVED,
            phase=context.current_phase,
            round_no=context.current_round,
            actor_id=instance.source_id,
            target_id=instance.owner_id,
            payload=self._event_payload(instance),
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
        return payload
