from __future__ import annotations

from dataclasses import dataclass

from .context import BattleContext
from .damage_system import DamageRequest, DamageResult, DamageSystem
from .events import EventType
from .troop_system import TroopChangeResult, TroopSystem


@dataclass(frozen=True, slots=True)
class DamageResolutionResult:
    damage: DamageResult
    troop_change: TroopChangeResult | None
    target_defeated: bool


class DamageResolutionSystem:
    """统一协调理论伤害、实际扣兵与伤害结果事件。

    DamageSystem 继续只负责计算；TroopSystem 继续是唯一兵力写入口。
    两阶段 API 允许 NormalAttackSystem 在 DAMAGE_* 事实之前保留
    Stage 4 已冻结的 NORMAL_ATTACK 事件顺序。
    """

    def __init__(
        self,
        damage_system: DamageSystem,
        troop_system: TroopSystem,
    ) -> None:
        self._damage = damage_system
        self._troops = troop_system

    def calculate(
        self,
        context: BattleContext,
        request: DamageRequest,
    ) -> DamageResult:
        return self._damage.calculate(context, request)

    def resolve(
        self,
        context: BattleContext,
        request: DamageRequest,
    ) -> DamageResolutionResult:
        damage = self.calculate(context, request)
        return self.apply_result(context, damage)

    def apply_result(
        self,
        context: BattleContext,
        damage: DamageResult,
    ) -> DamageResolutionResult:
        if damage.prevented:
            context.event_bus.publish(
                event_type=EventType.DAMAGE_PREVENTED,
                phase=context.current_phase,
                round_no=context.current_round,
                actor_id=damage.source_id,
                target_id=damage.target_id,
                payload={
                    "damage_type": damage.damage_type.value,
                    "source_type": damage.source_type.value,
                    "coefficient": damage.coefficient,
                    "base_damage": damage.base_damage,
                    "scaled_damage": damage.scaled_damage,
                    "requested_damage": damage.final_damage,
                    "reason_state_id": damage.prevented_by_state_id,
                },
            )
            return DamageResolutionResult(
                damage=damage,
                troop_change=None,
                target_defeated=False,
            )

        target = context.get_unit(damage.target_id)
        was_alive = target.is_alive
        troop_change = self._troops.apply_damage(target, damage.final_damage)

        context.event_bus.publish(
            event_type=EventType.DAMAGE_DEALT,
            phase=context.current_phase,
            round_no=context.current_round,
            actor_id=damage.source_id,
            target_id=damage.target_id,
            payload={
                "damage": troop_change.actual_change,
                "requested_damage": damage.final_damage,
                "damage_type": damage.damage_type.value,
                "source_type": damage.source_type.value,
                "coefficient": damage.coefficient,
                "base_damage": damage.base_damage,
                "scaled_damage": damage.scaled_damage,
                "target_remaining_troops": troop_change.remaining_troops,
            },
        )

        target_defeated = was_alive and not target.is_alive
        if target_defeated:
            context.event_bus.publish(
                event_type=EventType.UNIT_DEFEATED,
                phase=context.current_phase,
                round_no=context.current_round,
                actor_id=damage.source_id,
                target_id=damage.target_id,
                payload={"target_name": target.name},
            )

        return DamageResolutionResult(
            damage=damage,
            troop_change=troop_change,
            target_defeated=target_defeated,
        )
