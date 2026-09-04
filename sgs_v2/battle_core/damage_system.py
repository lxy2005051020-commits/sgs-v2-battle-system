from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .attribute_system import AttributeSystem
from .context import BattleContext
from .enums import DamageSourceType, DamageType
from .unit import UnitRuntime
from .weapon_damage_formula import WeaponBaseDamageFormula


@dataclass(frozen=True, slots=True)
class DamageRequest:
    """一次伤害结算请求。

    DamageType 决定使用基础兵刃伤害或基础谋略伤害；
    coefficient 只负责对基础伤害进行倍率缩放。
    """

    source_id: str
    target_id: str
    damage_type: DamageType
    source_type: DamageSourceType
    coefficient: float = 1.0
    source_skill_id: str | None = None

    def __post_init__(self) -> None:
        if not self.source_id:
            raise ValueError("source_id cannot be empty")
        if not self.target_id:
            raise ValueError("target_id cannot be empty")
        if self.coefficient < 0:
            raise ValueError("coefficient must be >= 0")


@dataclass(frozen=True, slots=True)
class DamageResult:
    source_id: str
    target_id: str
    damage_type: DamageType
    source_type: DamageSourceType
    coefficient: float
    base_damage: float
    scaled_damage: float
    final_damage: int
    source_skill_id: str | None = None

    @property
    def requested_damage(self) -> int:
        """兼容旧调用方；正式字段为 final_damage。"""
        return self.final_damage


class DamageSystem:
    """统一计算伤害；不直接改变目标兵力。

    - WEAPON 已接入 NORMAL_ATTACK_FORMULA_V1.md 的基础兵刃伤害公式。
    - STRATEGY 仍等待基础谋略公式。
    - 基础伤害先由 DamageType 决定，再由 coefficient 做战法倍率缩放。
    - TroopSystem 仍是唯一实际扣兵入口，因此击杀封顶不在这里重复实现。
    """

    def __init__(
        self,
        attribute_system: AttributeSystem,
        *,
        damage_scale: float = 1.0,
        weapon_troop_function_table: Mapping[int, int] | None = None,
        weapon_random_percent_range: tuple[int, int] = (86, 94),
        weapon_low_damage_floor_range: tuple[int, int] = (5, 15),
    ) -> None:
        if damage_scale < 0:
            raise ValueError("damage_scale must be >= 0")
        self._attributes = attribute_system
        self._weapon_formula = WeaponBaseDamageFormula(
            attribute_system,
            troop_function_table=weapon_troop_function_table,
            random_percent_range=weapon_random_percent_range,
            low_damage_floor_range=weapon_low_damage_floor_range,
        )
        # 旧阶段全局倍率继续保留在 coefficient 之后，仅用于兼容现有测试/调用。
        # 正式增减伤系统完成后应移除，而不是并入基础公式。
        self.damage_scale = damage_scale

    def weapon_troop_function(self, troops: int) -> int:
        """暴露 F(N) 便于查表回归测试。"""
        return self._weapon_formula.troop_function(troops)

    def calculate(
        self,
        context: BattleContext,
        request: DamageRequest,
    ) -> DamageResult:
        source = context.get_unit(request.source_id)
        target = context.get_unit(request.target_id)

        if request.damage_type is DamageType.WEAPON:
            base_damage = self._calculate_weapon_base_damage(context, source, target)
        elif request.damage_type is DamageType.STRATEGY:
            base_damage = self._calculate_strategy_base_damage(context, source, target)
        else:
            raise ValueError(f"unsupported damage type: {request.damage_type}")

        scaled_damage = base_damage * request.coefficient
        modified_damage = scaled_damage * self.damage_scale
        final_damage = max(1, int(modified_damage))

        return DamageResult(
            source_id=request.source_id,
            target_id=request.target_id,
            damage_type=request.damage_type,
            source_type=request.source_type,
            coefficient=request.coefficient,
            base_damage=base_damage,
            scaled_damage=scaled_damage,
            final_damage=final_damage,
            source_skill_id=request.source_skill_id,
        )

    def calculate_normal_attack(
        self,
        context: BattleContext,
        attacker: UnitRuntime,
        target: UnitRuntime,
    ) -> DamageResult:
        """兼容旧接口；普通攻击正式走 DamageRequest。"""
        return self.calculate(
            context,
            DamageRequest(
                source_id=attacker.unit_id,
                target_id=target.unit_id,
                damage_type=DamageType.WEAPON,
                source_type=DamageSourceType.NORMAL_ATTACK,
                coefficient=1.0,
            ),
        )

    def _calculate_weapon_base_damage(
        self,
        context: BattleContext,
        source: UnitRuntime,
        target: UnitRuntime,
    ) -> int:
        return self._weapon_formula.calculate(context, source, target)

    def _calculate_strategy_base_damage(
        self,
        context: BattleContext,
        source: UnitRuntime,
        target: UnitRuntime,
    ) -> float:
        raise NotImplementedError(
            "strategy base damage is not implemented yet; "
            "the intelligence-based base formula must be defined first"
        )
