from __future__ import annotations

from typing import Protocol, TYPE_CHECKING

from .unit import UnitRuntime
from .equipment_effectiveness import (
    EquipmentAttributeContribution,
    EquipmentEffectivenessBoundaryError,
    EquipmentEffectivenessPolicy,
    EquipmentEffectivenessStatus,
)

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

    def __init__(
        self,
        modifier_provider: AttributeModifierProvider | None = None,
        equipment_effectiveness_policy: EquipmentEffectivenessPolicy | None = None,
    ) -> None:
        self._modifier_provider = modifier_provider
        self._additional_modifier_providers: list[AttributeModifierProvider] = []
        self._equipment_effectiveness_policy = equipment_effectiveness_policy
        self._equipment_contribution_providers: list[object] = []

    @property
    def equipment_effectiveness_policy(self) -> EquipmentEffectivenessPolicy | None:
        return self._equipment_effectiveness_policy

    def bind_equipment_effectiveness_policy(
        self,
        policy: EquipmentEffectivenessPolicy,
    ) -> None:
        if not isinstance(policy, EquipmentEffectivenessPolicy):
            raise TypeError("policy must be EquipmentEffectivenessPolicy")
        if self._equipment_effectiveness_policy not in (None, policy):
            raise RuntimeError("AttributeSystem equipment policy is already bound")
        self._equipment_effectiveness_policy = policy

    def register_equipment_contribution_provider(self, provider) -> None:
        if not callable(provider):
            raise TypeError("provider must be callable")
        if provider not in self._equipment_contribution_providers:
            self._equipment_contribution_providers.append(provider)

    def get_attack(self, context: BattleContext, unit: UnitRuntime) -> float:
        return self._get(context, unit, "attack", unit.attack)

    def register_modifier_provider(self, provider: AttributeModifierProvider) -> None:
        if not callable(getattr(provider, "modify_attribute", None)):
            raise TypeError("modifier provider must expose modify_attribute")
        if provider is not self._modifier_provider and provider not in self._additional_modifier_providers:
            self._additional_modifier_providers.append(provider)

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
        value = base_value
        if self._modifier_provider is not None:
            value = self._modifier_provider.modify_attribute(
                context=context,
                unit=unit,
                attribute=attribute,
                base_value=base_value,
            )
        for modifier in tuple(self._additional_modifier_providers):
            value = modifier.modify_attribute(
                context=context, unit=unit, attribute=attribute, base_value=value,
            )
        for provider in tuple(self._equipment_contribution_providers):
            for contribution in tuple(provider(context, unit, attribute)):
                if not isinstance(contribution, EquipmentAttributeContribution):
                    raise TypeError("equipment attribute provider returned invalid contribution")
                if contribution.attribute != attribute:
                    continue
                if self._equipment_effectiveness_policy is None:
                    raise RuntimeError("equipment contribution has no effectiveness policy")
                decision = self._equipment_effectiveness_policy.evaluate_contribution(
                    context, contribution.contribution_ref
                )
                if decision.status is EquipmentEffectivenessStatus.UNSUPPORTED_BOUNDARY:
                    raise EquipmentEffectivenessBoundaryError(
                        f"unsupported equipment attribute boundary: {contribution.contribution_ref!r}"
                    )
                if decision.effective:
                    value += contribution.amount
        return value
