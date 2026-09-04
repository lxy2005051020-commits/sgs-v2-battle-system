from __future__ import annotations

from dataclasses import dataclass

from .unit import UnitRuntime


@dataclass(frozen=True, slots=True)
class TroopChangeResult:
    requested_change: int
    actual_change: int
    remaining_troops: int


class TroopSystem:
    """唯一执行兵力增减的 BattleSystem。"""

    def apply_damage(self, target: UnitRuntime, requested_damage: int) -> TroopChangeResult:
        if requested_damage < 0:
            raise ValueError("requested_damage must be >= 0")
        actual_damage = min(target.troops, requested_damage)
        target.troops -= actual_damage
        return TroopChangeResult(
            requested_change=requested_damage,
            actual_change=actual_damage,
            remaining_troops=target.troops,
        )

    def restore(self, target: UnitRuntime, requested_recovery: int) -> TroopChangeResult:
        """为后续治疗保留同一兵力写入入口。"""
        if requested_recovery < 0:
            raise ValueError("requested_recovery must be >= 0")
        actual_recovery = min(target.max_troops - target.troops, requested_recovery)
        target.troops += actual_recovery
        return TroopChangeResult(
            requested_change=requested_recovery,
            actual_change=actual_recovery,
            remaining_troops=target.troops,
        )
