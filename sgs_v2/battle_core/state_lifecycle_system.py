from __future__ import annotations

from typing import TYPE_CHECKING

from .events import EventType
from .state_instance import AUTO_EXPIRY_PHASES, StateInstance

if TYPE_CHECKING:
    from .context import BattleContext


class StateLifecycleSystem:
    """状态加入、显式移除与自动过期的唯一正式写入口。"""

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

        StateInstance.validate_expiry(
            applied_round=context.current_round,
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
        self._publish(context, EventType.STATE_APPLIED, instance)
        return instance

    def remove(
        self,
        context: BattleContext,
        instance_id: str,
    ) -> StateInstance:
        instance = context.states.remove(instance_id)
        self._publish(context, EventType.STATE_REMOVED, instance)
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
        if phase not in AUTO_EXPIRY_PHASES:
            raise ValueError(
                "automatic state expiry only supports ROUND_START and ROUND_END"
            )

        expired = [
            instance
            for instance in context.states.find()
            if instance.expires_round == round_no
            and instance.expires_phase == phase
        ]
        for instance in expired:
            context.states.remove(instance.instance_id)
            self._publish(
                context,
                EventType.STATE_EXPIRED,
                instance,
                round_no=round_no,
                phase=phase,
            )
        return expired

    @staticmethod
    def _publish(
        context: BattleContext,
        event_type: EventType,
        instance: StateInstance,
        *,
        round_no: int | None = None,
        phase: str | None = None,
    ) -> None:
        context.event_bus.publish(
            event_type=event_type,
            phase=context.current_phase if phase is None else phase,
            round_no=context.current_round if round_no is None else round_no,
            actor_id=instance.source_id,
            target_id=instance.owner_id,
            payload={
                "instance_id": instance.instance_id,
                "state_id": instance.state_id,
                "owner_id": instance.owner_id,
                "source_id": instance.source_id,
                "source_skill_id": instance.source_skill_id,
                "applied_round": instance.applied_round,
                "applied_phase": instance.applied_phase,
                "expires_round": instance.expires_round,
                "expires_phase": instance.expires_phase,
            },
        )
