from __future__ import annotations

from .context import BattleContext
from .events import EventType
from .normal_attack_system import NormalAttackResult, NormalAttackSystem
from .official_state_catalog import OfficialStateId
from .unit import UnitRuntime


class ActionSystem:
    """处理一个单位的一次完整行动。"""

    def __init__(self, normal_attack_system: NormalAttackSystem) -> None:
        self._normal_attack = normal_attack_system

    def execute(self, context: BattleContext, actor: UnitRuntime) -> NormalAttackResult | None:
        if not actor.is_alive:
            return None

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
            return None

        return self._normal_attack.execute(context, actor)
