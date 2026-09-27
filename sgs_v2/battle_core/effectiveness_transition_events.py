from __future__ import annotations

from .effectiveness_transition import StateEffectivenessChanged
from .events import EventType
from .state_effectiveness import StateEffectivenessStatus


class StateEffectivenessEventAdapter:
    """Publish only committed true state suppression/resume facts."""

    def __call__(self, context, transition: StateEffectivenessChanged) -> None:
        if not isinstance(transition, StateEffectivenessChanged):
            raise TypeError("transition must be StateEffectivenessChanged")
        before = transition.before.status
        after = transition.after.status
        if (
            before is StateEffectivenessStatus.EFFECTIVE
            and after is StateEffectivenessStatus.SUPPRESSED
        ):
            event_type = EventType.STATE_SUPPRESSED
        elif (
            before is StateEffectivenessStatus.SUPPRESSED
            and after is StateEffectivenessStatus.EFFECTIVE
        ):
            event_type = EventType.STATE_RESUMED
        else:
            return

        owner_id = None
        state_id = None
        if context.states.has_instance(transition.state_instance_id):
            instance = context.states.get(transition.state_instance_id)
            owner_id = instance.owner_id
            state_id = instance.state_id

        context.event_bus.publish(
            event_type=event_type,
            phase=context.current_phase,
            round_no=context.current_round,
            actor_id=owner_id,
            target_id=owner_id,
            payload={
                "state_id": state_id,
                "state_instance_id": transition.state_instance_id,
                "application_generation_id": str(
                    transition.after.application_generation_id
                ),
                "before_status": before.value,
                "after_status": after.value,
            },
        )
