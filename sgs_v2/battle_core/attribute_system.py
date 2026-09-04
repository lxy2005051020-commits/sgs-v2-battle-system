from __future__ import annotations

from typing import Protocol, TYPE_CHECKING

from .unit import UnitRuntime

if TYPE_CHECKING:
    from .context import BattleContext


class AttributeModifierProvider(Protocol):
    """阶段 4 的 AttributeModifierState 需要满足的最小接口。"""

    def modify_attribute(
        self,
        *,
        context: BattleContext,
        unit: UnitRuntime,
        attribute: str,
        base_value: float,
    ) -> float:
        ...


class AttributeSystem:
    """统一计算单位的最终属性。

    阶段 2 暂无属性修正，最终值等于基础值。阶段 4 可注入
    AttributeModifierState，而无需让伤害、行动顺序等调用方改变读取方式。
    """

    def __init__(self, modifier_provider: AttributeModifierProvider | None = None) -> None:
        self._modifier_provider = modifier_provider

    def get_attack(self, context: BattleContext, unit: UnitRuntime) -> float:
        return self._get(context, unit, "attack", unit.attack)

    def get_defense(self, context: BattleContext, unit: UnitRuntime) -> float:
        return self._get(context, unit, "defense", unit.defense)

    def get_intelligence(self, context: BattleContext, unit: UnitRuntime) -> float:
        if unit.intelligence is None:
            raise ValueError(f"unit {unit.unit_id} has no intelligence value")
        return self._get(context, unit, "intelligence", unit.intelligence)

    def get_speed(self, context: BattleContext, unit: UnitRuntime) -> float:
        return self._get(context, unit, "speed", unit.speed)

    def _get(
        self,
        context: BattleContext,
        unit: UnitRuntime,
        attribute: str,
        base_value: float,
    ) -> float:
        if self._modifier_provider is None:
            return base_value
        return self._modifier_provider.modify_attribute(
            context=context,
            unit=unit,
            attribute=attribute,
            base_value=base_value,
        )
