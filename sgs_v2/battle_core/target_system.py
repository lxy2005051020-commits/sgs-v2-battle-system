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
    ) -> list[UnitRuntime]:
        return self._filter_by_team(
            context, unit.team_id, alive_only=alive_only
        )

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
        # 结果唯一时不消耗随机流。
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
        allies = self.allies(context, unit, alive_only=True)
        if not include_self:
            allies = [candidate for candidate in allies if candidate.unit_id != unit.unit_id]
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

        # 所有候选都会被选中时，目标集合已经唯一，不应消耗随机流。
        # 使用 unit_id 作为规范顺序，避免结果依赖 context.units 的插入顺序。
        if actual_count == len(candidates):
            return sorted(candidates, key=lambda unit: unit.unit_id)

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
