from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .attribute_system import AttributeSystem
from .context import BattleContext
from .enums import DamageSourceType, DamageType
from .official_state_catalog import OfficialStateId
from .strategy_damage_formula import StrategyBaseDamageFormula
from .unit import UnitRuntime
from .weapon_damage_formula import WeaponBaseDamageFormula


def _validate_optional_id(value: str | None, field_name: str) -> None:
    if value is None:
        return
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a str when provided")
    if not value.strip():
        raise ValueError(f"{field_name} cannot be empty or whitespace when provided")


def _validate_state_provenance_pair(
    source_state_id: str | None,
    source_state_instance_id: str | None,
) -> None:
    if (source_state_id is None) != (source_state_instance_id is None):
        raise ValueError(
            "source_state_id and source_state_instance_id must both be set or both be None"
        )


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
    source_state_id: str | None = None
    source_state_instance_id: str | None = None

    def __post_init__(self) -> None:
        if not self.source_id:
            raise ValueError("source_id cannot be empty")
        if not self.target_id:
            raise ValueError("target_id cannot be empty")
        if self.coefficient < 0:
            raise ValueError("coefficient must be >= 0")
        _validate_optional_id(self.source_skill_id, "source_skill_id")
        _validate_optional_id(self.source_state_id, "source_state_id")
        _validate_optional_id(
            self.source_state_instance_id,
            "source_state_instance_id",
        )
        _validate_state_provenance_pair(
            self.source_state_id,
            self.source_state_instance_id,
        )


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
    source_state_id: str | None = None
    source_state_instance_id: str | None = None
    prevented: bool = False
    prevented_by_state_id: str | None = None

    def __post_init__(self) -> None:
        _validate_optional_id(self.source_skill_id, "source_skill_id")
        _validate_optional_id(self.source_state_id, "source_state_id")
        _validate_optional_id(
            self.source_state_instance_id,
            "source_state_instance_id",
        )
        _validate_state_provenance_pair(
            self.source_state_id,
            self.source_state_instance_id,
        )

    @property
    def requested_damage(self) -> int:
        """兼容旧调用方；正式字段为 final_damage。"""
        return self.final_damage


class DamageSystem:
    """统一计算理论伤害；不直接改变目标兵力。"""

    def __init__(
        self,
        attribute_system: AttributeSystem,
        *,
        weapon_troop_function_table: Mapping[int, int] | None = None,
        weapon_random_percent_range: tuple[int, int] = (86, 94),
        weapon_low_damage_floor_range: tuple[int, int] = (5, 15),
        strategy_troop_function_table: Mapping[int, int] | None = None,
        strategy_random_percent_range: tuple[int, int] = (86, 94),
        strategy_low_damage_floor_range: tuple[int, int] = (5, 15),
    ) -> None:
        self._attributes = attribute_system
        self._weapon_formula = WeaponBaseDamageFormula(
            attribute_system,
            troop_function_table=weapon_troop_function_table,
            random_percent_range=weapon_random_percent_range,
            low_damage_floor_range=weapon_low_damage_floor_range,
        )
        self._strategy_formula = StrategyBaseDamageFormula(
            attribute_system,
            troop_function_table=strategy_troop_function_table,
            random_percent_range=strategy_random_percent_range,
            low_damage_floor_range=strategy_low_damage_floor_range,
        )

    def weapon_troop_function(self, troops: int) -> int:
        return self._weapon_formula.troop_function(troops)

    def strategy_troop_function(self, troops: int) -> int:
        return self._strategy_formula.troop_function(troops)

    def calculate(
        self,
        context: BattleContext,
        request: DamageRequest,
    ) -> DamageResult:
        source = context.get_unit(request.source_id)
        target = context.get_unit(request.target_id)

        weakness_state_id = OfficialStateId.WEAKNESS.value
        if context.states.has(owner_id=source.unit_id, state_id=weakness_state_id):
            return DamageResult(
                source_id=request.source_id,
                target_id=request.target_id,
                damage_type=request.damage_type,
                source_type=request.source_type,
                coefficient=request.coefficient,
                base_damage=0,
                scaled_damage=0,
                final_damage=0,
                source_skill_id=request.source_skill_id,
                source_state_id=request.source_state_id,
                source_state_instance_id=request.source_state_instance_id,
                prevented=True,
                prevented_by_state_id=weakness_state_id,
            )

        if request.damage_type is DamageType.WEAPON:
            base_damage = self._calculate_weapon_base_damage(context, source, target)
        elif request.damage_type is DamageType.STRATEGY:
            base_damage = self._calculate_strategy_base_damage(context, source, target)
        else:
            raise ValueError(f"unsupported damage type: {request.damage_type}")

        scaled_damage = base_damage * request.coefficient
        final_damage = max(1, int(scaled_damage))

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
            source_state_id=request.source_state_id,
            source_state_instance_id=request.source_state_instance_id,
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
    ) -> int:
        return self._strategy_formula.calculate(context, source, target)
