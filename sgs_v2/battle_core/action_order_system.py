from __future__ import annotations

from .attribute_system import AttributeSystem
from .context import BattleContext
from .unit import UnitRuntime


class ActionOrderSystem:
    """按最终速度生成一回合的行动顺序。"""

    def __init__(self, attribute_system: AttributeSystem) -> None:
        self._attributes = attribute_system

    def determine_order(self, context: BattleContext) -> list[UnitRuntime]:
        alive_units = [unit for unit in context.units.values() if unit.is_alive]
        speed_groups: dict[float, list[UnitRuntime]] = {}
        for unit in alive_units:
            speed = self._attributes.get_speed(context, unit)
            speed_groups.setdefault(speed, []).append(unit)

        result: list[UnitRuntime] = []
        for speed in sorted(speed_groups, reverse=True):
            group = speed_groups[speed]
            # 固定 shuffle 的输入顺序，使复现性不依赖 dict 插入顺序。
            group.sort(key=lambda unit: unit.unit_id)
            # 仅真正同速的单位才需要消耗随机数裁决先后。
            if len(group) > 1:
                context.random.shuffle(group)
            result.extend(group)
        return result
