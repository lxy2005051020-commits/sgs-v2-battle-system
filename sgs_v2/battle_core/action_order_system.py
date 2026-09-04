from __future__ import annotations

from .attribute_system import AttributeSystem
from .context import BattleContext
from .official_state_catalog import OfficialStateId
from .unit import UnitRuntime


class UnresolvedStateInteractionError(RuntimeError):
    """官方资料不足以确定多个状态组合的最终规则时抛出。"""


class ActionOrderSystem:
    """按状态优先级层、最终速度和必要的随机裁决生成行动顺序。"""

    FIRST_STRIKE_PRIORITY = 1
    NORMAL_PRIORITY = 0
    AMBUSH_PRIORITY = -1

    def __init__(self, attribute_system: AttributeSystem) -> None:
        self._attributes = attribute_system

    def determine_order(self, context: BattleContext) -> list[UnitRuntime]:
        alive_units = [unit for unit in context.units.values() if unit.is_alive]
        order_groups: dict[tuple[int, float], list[UnitRuntime]] = {}

        for unit in alive_units:
            priority = self._priority_tier(context, unit)
            speed = self._attributes.get_speed(context, unit)
            order_groups.setdefault((priority, speed), []).append(unit)

        result: list[UnitRuntime] = []
        for priority, speed in sorted(order_groups, reverse=True):
            group = order_groups[(priority, speed)]
            # 固定 shuffle 输入顺序，使复现性不依赖 context.units 插入顺序。
            group.sort(key=lambda unit: unit.unit_id)
            # 只有 priority tier 与最终速度都完全相同时才是真正并列。
            if len(group) > 1:
                context.random.shuffle(group)
            result.extend(group)
        return result

    def _priority_tier(self, context: BattleContext, unit: UnitRuntime) -> int:
        has_first_strike = context.states.has(
            owner_id=unit.unit_id,
            state_id=OfficialStateId.FIRST_STRIKE.value,
        )
        has_ambush = context.states.has(
            owner_id=unit.unit_id,
            state_id=OfficialStateId.AMBUSH.value,
        )

        if has_first_strike and has_ambush:
            raise UnresolvedStateInteractionError(
                "unresolved state interaction: "
                f"unit {unit.unit_id!r} has both "
                f"{OfficialStateId.FIRST_STRIKE.value!r} and "
                f"{OfficialStateId.AMBUSH.value!r}"
            )
        if has_first_strike:
            return self.FIRST_STRIKE_PRIORITY
        if has_ambush:
            return self.AMBUSH_PRIORITY
        return self.NORMAL_PRIORITY
