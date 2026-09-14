from __future__ import annotations

from .context import BattleContext
from .unit import UnitRuntime


class TargetSystem:
    """唯一的目标查询与随机选择入口。"""

    def allies(
        self,
        context: BattleContext,
        unit: UnitRuntime,
        *,
        alive_only: bool = True,
        include_self: bool = True,
    ) -> list[UnitRuntime]:
        allies = self._filter_by_team(
            context, unit.team_id, alive_only=alive_only
        )
        if not include_self:
            return [candidate for candidate in allies if candidate.unit_id != unit.unit_id]
        return allies

    def enemies(
        self,
        context: BattleContext,
        unit: UnitRuntime,
        *,
        alive_only: bool = True,
    ) -> list[UnitRuntime]:
        units = [candidate for candidate in context.units.values()
                 if candidate.team_id != unit.team_id]
        return [candidate for candidate in units if candidate.is_alive] if alive_only else units

    def random_enemy(
        self,
        context: BattleContext,
        unit: UnitRuntime,
    ) -> UnitRuntime | None:
        enemies = self.enemies(context, unit, alive_only=True)
        if not enemies:
            return None
        if len(enemies) == 1:
            return enemies[0]
        return context.random.choice(enemies)

    def random_allies(
        self,
        context: BattleContext,
        unit: UnitRuntime,
        *,
        count: int = 1,
        include_self: bool = True,
    ) -> list[UnitRuntime]:
        allies = self.allies(context, unit, alive_only=True, include_self=include_self)
        return self.random_units(context, allies, count=count)

    def random_units(
        self,
        context: BattleContext,
        candidates: list[UnitRuntime],
        *,
        count: int,
    ) -> list[UnitRuntime]:
        if count < 0:
            raise ValueError("count must be >= 0")

        actual_count = min(count, len(candidates))
        if actual_count == 0:
            return []

        # 候选全部都会被选中时不消耗随机数。
        # 固定结算顺序遵循阵容位置：主将 -> 第一副将 -> 第二副将。
        if actual_count == len(candidates):
            return sorted(
                candidates,
                key=lambda unit: (
                    unit.team_id,
                    int(unit.lineup_position),
                    unit.unit_id,
                ),
            )

        return context.random.sample(candidates, actual_count)

    @staticmethod
    def _filter_by_team(
        context: BattleContext,
        team_id: str,
        *,
        alive_only: bool,
    ) -> list[UnitRuntime]:
        units = [candidate for candidate in context.units.values()
                 if candidate.team_id == team_id]
        return [candidate for candidate in units if candidate.is_alive] if alive_only else units
