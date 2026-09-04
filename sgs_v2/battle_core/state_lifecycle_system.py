from __future__ import annotations

from typing import TYPE_CHECKING

from .enums import BattlePhase
from .events import EventType
from .state_instance import StateInstance

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
        expires_round: int | None = None,
        expires_phase: str | None = None,
    ) -> StateInstance:
        context.states.get_definition(state_id)
        context.get_unit(owner_id)
        if source_id is not None:
            context.get_unit(source_id)

        self._validate_expiration(
            applied_round=context.current_round,
            applied_phase=context.current_phase,
            expires_round=expires_round,
            expires_phase=expires_phase,
        )

        instance = StateInstance(
            instance_id=context.states.next_instance_id(),
            state_id=state_id,
            owner_id=owner_id,
            source_id=source_id,
            source_skill_id=source_skill_id,
            applied_round=context.current_round,
            applied_phase=context.current_phase,
            expires_round=expires_round,
            expires_phase=expires_phase,
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
        return {
            "instance_id": instance.instance_id,
            "state_id": instance.state_id,
            "owner_id": instance.owner_id,
            "source_id": instance.source_id,
            "source_skill_id": instance.source_skill_id,
            "applied_round": instance.applied_round,
            "applied_phase": instance.applied_phase,
            "expires_round": instance.expires_round,
            "expires_phase": instance.expires_phase,
        }
