from __future__ import annotations

from dataclasses import dataclass

from .unit import UnitRuntime


@dataclass(frozen=True, slots=True)
class TroopChangeResult:
    requested_change: int
    actual_change: int
    remaining_troops: int
    wounded_before: int = 0
    wounded_after: int = 0
    wounded_generated: int = 0
    wounded_consumed: int = 0


class TroopSystem:
    """唯一执行兵力增减的 BattleSystem。"""

    def apply_damage(self, target: UnitRuntime, requested_damage: int) -> TroopChangeResult:
        if isinstance(requested_damage, bool) or not isinstance(requested_damage, int):
            raise TypeError("requested_damage must be an int")
        if requested_damage < 0:
            raise ValueError("requested_damage must be >= 0")
        wounded_before = target.wounded_troops
        assert wounded_before is not None
        actual_damage = min(target.troops, requested_damage)
        target.troops -= actual_damage
        wounded_generated = (actual_damage * 90) // 100
        if target.troops == 0:
            # Stage13-B1 Tier-C canonical runtime default: defeated units do not
            # retain recoverable capacity.
            target.wounded_troops = 0
        else:
            missing = target.max_troops - target.troops
            target.wounded_troops = min(
                missing,
                wounded_before + wounded_generated,
            )
        return TroopChangeResult(
            requested_change=requested_damage,
            actual_change=actual_damage,
            remaining_troops=target.troops,
            wounded_before=wounded_before,
            wounded_after=target.wounded_troops,
            wounded_generated=wounded_generated,
        )

    def restore(self, target: UnitRuntime, requested_recovery: int) -> TroopChangeResult:
        if isinstance(requested_recovery, bool) or not isinstance(
            requested_recovery, int
        ):
            raise TypeError("requested_recovery must be an int")
        if requested_recovery < 0:
            raise ValueError("requested_recovery must be >= 0")
        wounded_before = target.wounded_troops
        assert wounded_before is not None
        missing = target.max_troops - target.troops
        actual_recovery = min(missing, wounded_before, requested_recovery)
        target.troops += actual_recovery
        target.wounded_troops = max(0, wounded_before - actual_recovery)
        return TroopChangeResult(
            requested_change=requested_recovery,
            actual_change=actual_recovery,
            remaining_troops=target.troops,
            wounded_before=wounded_before,
            wounded_after=target.wounded_troops,
            wounded_consumed=actual_recovery,
        )

    def decay_wounded(self, target: UnitRuntime) -> int:
        """Apply the Stage13-B1 round-transition wounded-pool decay."""
        wounded_before = target.wounded_troops
        assert wounded_before is not None
        if not target.is_alive:
            target.wounded_troops = 0
            return 0
        target.wounded_troops = (wounded_before * 90) // 100
        return target.wounded_troops

    def decay_wounded_all(self, targets) -> None:
        for target in targets:
            if not isinstance(target, UnitRuntime):
                raise TypeError("targets must contain UnitRuntime values")
            self.decay_wounded(target)
