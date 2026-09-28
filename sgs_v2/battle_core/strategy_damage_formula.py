from __future__ import annotations

from .context import BattleContext
from .damage_formula_context import DamageDefensePolicy, DamageFormulaContext
from .unit import UnitRuntime
from .weapon_damage_formula import WeaponBaseDamageFormula


class StrategyBaseDamageFormula(WeaponBaseDamageFormula):
    """基础谋略伤害。

    与基础兵刃伤害共享同一套 F(N) 查表、等级缩放、兵种克制、士气、
    随机层和低伤害下限；属性对抗改为攻击者智力 vs 防守者智力。
    """

    def calculate(
        self,
        context: BattleContext,
        source: UnitRuntime,
        target: UnitRuntime,
        *,
        formula_context: DamageFormulaContext | None = None,
    ) -> int:
        formula_context = formula_context or DamageFormulaContext()
        if source.intelligence is None:
            raise NotImplementedError(
                "strategy base damage requires an intelligence value for source"
            )
        if (
            formula_context.defense_policy is DamageDefensePolicy.NORMAL
            and target.intelligence is None
        ):
            raise NotImplementedError(
                "strategy base damage requires an intelligence value for target"
            )
        return super().calculate(
            context,
            source,
            target,
            formula_context=formula_context,
        )

    def _source_combat_attribute(
        self,
        context: BattleContext,
        source: UnitRuntime,
    ) -> float:
        return self._attributes.get_intelligence(context, source)

    def _target_combat_attribute(
        self,
        context: BattleContext,
        target: UnitRuntime,
    ) -> float:
        return self._attributes.get_intelligence(context, target)
