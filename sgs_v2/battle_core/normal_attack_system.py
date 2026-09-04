from __future__ import annotations

from dataclasses import dataclass

from .context import BattleContext
from .damage_system import DamageResult, DamageSystem
from .events import EventType
from .target_system import TargetSystem
from .troop_system import TroopChangeResult, TroopSystem
from .unit import UnitRuntime


@dataclass(frozen=True, slots=True)
class NormalAttackResult:
    actor_id: str
    target_id: str | None
    damage: DamageResult | None
    troop_change: TroopChangeResult | None


class NormalAttackSystem:
    """组织一次普通攻击的选目标、算伤害、扣兵与事件发出。"""

    def __init__(
        self,
        target_system: TargetSystem,
        damage_system: DamageSystem,
        troop_system: TroopSystem,
    ) -> None:
        self._targets = target_system
        self._damage = damage_system
        self._troops = troop_system

    def execute(self, context: BattleContext, actor: UnitRuntime) -> NormalAttackResult:
        target = self._targets.random_enemy(context, actor)
        if target is None:
            return NormalAttackResult(actor.unit_id, None, None, None)

        damage = self._damage.calculate_normal_attack(context, actor, target)
        context.event_bus.publish(
            event_type=EventType.NORMAL_ATTACK,
            phase=context.current_phase,
            round_no=context.current_round,
            actor_id=actor.unit_id,
            target_id=target.unit_id,
            payload={"requested_damage": damage.requested_damage},
        )
        troop_change = self._troops.apply_damage(target, damage.requested_damage)
        context.event_bus.publish(
            event_type=EventType.DAMAGE_DEALT,
            phase=context.current_phase,
            round_no=context.current_round,
            actor_id=actor.unit_id,
            target_id=target.unit_id,
            payload={
                "damage": troop_change.actual_change,
                "target_remaining_troops": troop_change.remaining_troops,
            },
        )
        if not target.is_alive:
            context.event_bus.publish(
                event_type=EventType.UNIT_DEFEATED,
                phase=context.current_phase,
                round_no=context.current_round,
                actor_id=actor.unit_id,
                target_id=target.unit_id,
                payload={"target_name": target.name},
            )
        return NormalAttackResult(actor.unit_id, target.unit_id, damage, troop_change)
