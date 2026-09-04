from __future__ import annotations

from dataclasses import dataclass

from .context import BattleContext
from .damage_resolution_system import DamageResolutionSystem
from .damage_system import DamageRequest, DamageResult
from .enums import DamageSourceType, DamageType
from .events import EventType
from .official_state_catalog import OfficialStateId
from .target_system import TargetSystem
from .troop_system import TroopChangeResult
from .unit import UnitRuntime


@dataclass(frozen=True, slots=True)
class NormalAttackResult:
    actor_id: str
    target_id: str | None
    damage: DamageResult | None
    troop_change: TroopChangeResult | None


class NormalAttackSystem:
    """组织一次普通攻击的状态门控、选目标、伤害请求与普攻事实。"""

    def __init__(
        self,
        target_system: TargetSystem,
        damage_resolution_system: DamageResolutionSystem,
    ) -> None:
        self._targets = target_system
        self._damage_resolution = damage_resolution_system

    def execute(self, context: BattleContext, actor: UnitRuntime) -> NormalAttackResult:
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
            return NormalAttackResult(actor.unit_id, None, None, None)

        target = self._targets.random_enemy(context, actor)
        if target is None:
            return NormalAttackResult(actor.unit_id, None, None, None)

        request = DamageRequest(
            source_id=actor.unit_id,
            target_id=target.unit_id,
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.NORMAL_ATTACK,
            coefficient=1.0,
        )
        damage = self._damage_resolution.calculate(context, request)

        # Stage 4 已冻结：NORMAL_ATTACK 必须先于 DAMAGE_PREVENTED / DAMAGE_DEALT。
        context.event_bus.publish(
            event_type=EventType.NORMAL_ATTACK,
            phase=context.current_phase,
            round_no=context.current_round,
            actor_id=actor.unit_id,
            target_id=target.unit_id,
            payload={
                "damage_type": damage.damage_type.value,
                "source_type": damage.source_type.value,
                "coefficient": damage.coefficient,
                "base_damage": damage.base_damage,
                "scaled_damage": damage.scaled_damage,
                "requested_damage": damage.final_damage,
                "prevented": damage.prevented,
                "prevented_by_state_id": damage.prevented_by_state_id,
            },
        )

        resolution = self._damage_resolution.apply_result(context, damage)
        return NormalAttackResult(
            actor.unit_id,
            target.unit_id,
            resolution.damage,
            resolution.troop_change,
        )
