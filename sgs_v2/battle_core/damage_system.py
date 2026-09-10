from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .attribute_system import AttributeSystem
from .context import BattleContext
from .damage_formula_context import DamageDefensePolicy, DamageFormulaContext
from .damage_formula_policy_system import DamageFormulaPolicySystem
from .damage_modifier_system import DamageModifierSystem
from .damage_pipeline_trace import DamagePipelineTrace, StageEvaluationStatus
from .damage_prevention_system import (
    DamageAllowedResult,
    DamagePreventedResult,
    DamagePreventionSystem,
)
from .damage_rule_provider import DamageRuleProvider, StateDamageRuleProvider
from .damage_state_rule_bindings import DEFAULT_STAGE8_STATE_RULE_BINDINGS
from .enums import DamageSourceType, DamageType
from .hit_resolution_system import HitPreventedResult, HitResolutionSystem
from .numeric_validation import validate_nonnegative_finite
from .strategy_damage_formula import StrategyBaseDamageFormula
from .unit import UnitRuntime
from .weapon_damage_formula import WeaponBaseDamageFormula


def _validate_optional_state_id(value: str | None, field_name: str) -> None:
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


class InvalidDamageParticipantError(ValueError):
    """DamageRequest source/target is missing or already dead before rule discovery."""


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
        coefficient = validate_nonnegative_finite(self.coefficient, "coefficient")
        object.__setattr__(self, "coefficient", coefficient)
        _validate_optional_state_id(self.source_state_id, "source_state_id")
        _validate_optional_state_id(
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
    prevented: bool = False
    prevented_by_state_id: str | None = None
    source_state_id: str | None = None
    source_state_instance_id: str | None = None
    pipeline_trace: DamagePipelineTrace | None = None

    def __post_init__(self) -> None:
        _validate_optional_state_id(self.source_state_id, "source_state_id")
        _validate_optional_state_id(
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
        rule_provider: DamageRuleProvider | None = None,
        prevention_system: DamagePreventionSystem | None = None,
        hit_resolution_system: HitResolutionSystem | None = None,
        formula_policy_system: DamageFormulaPolicySystem | None = None,
        modifier_system: DamageModifierSystem | None = None,
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
        self._rule_provider = rule_provider or StateDamageRuleProvider(
            DEFAULT_STAGE8_STATE_RULE_BINDINGS
        )
        self._prevention = prevention_system or DamagePreventionSystem()
        self._hit = hit_resolution_system or HitResolutionSystem()
        self._formula_policy = formula_policy_system or DamageFormulaPolicySystem()
        self._modifiers = modifier_system or DamageModifierSystem()

    def weapon_troop_function(self, troops: int) -> int:
        """暴露兵刃 F(N) 便于查表回归测试。"""
        return self._weapon_formula.troop_function(troops)

    def strategy_troop_function(self, troops: int) -> int:
        """暴露谋略 F(N) 便于查表回归测试。"""
        return self._strategy_formula.troop_function(troops)

    def calculate(
        self,
        context: BattleContext,
        request: DamageRequest,
    ) -> DamageResult:
        source, target = self._validate_participants(context, request)
        rules = self._rule_provider.collect(context, request)

        prevention_result = self._prevention.resolve(rules)
        if isinstance(prevention_result, DamagePreventedResult):
            trace = DamagePipelineTrace(
                prevention_status=StageEvaluationStatus.EXECUTED,
                prevention_result=prevention_result,
                hit_status=StageEvaluationStatus.NOT_EVALUATED,
                hit_result=None,
                formula_policy_status=StageEvaluationStatus.NOT_EVALUATED,
                formula_policy_result=None,
                modifier_status=StageEvaluationStatus.NOT_EVALUATED,
                modifier_result=None,
            )
            return self._prevented_result(
                request,
                trace,
                prevention_result.decisive_source.source_state_id,
            )
        if not isinstance(prevention_result, DamageAllowedResult):
            raise TypeError("DamagePreventionSystem returned an invalid result")

        hit_result = self._hit.resolve(context, request, rules)
        if isinstance(hit_result, HitPreventedResult):
            trace = DamagePipelineTrace(
                prevention_status=StageEvaluationStatus.EXECUTED,
                prevention_result=prevention_result,
                hit_status=StageEvaluationStatus.EXECUTED,
                hit_result=hit_result,
                formula_policy_status=StageEvaluationStatus.NOT_EVALUATED,
                formula_policy_result=None,
                modifier_status=StageEvaluationStatus.NOT_EVALUATED,
                modifier_result=None,
            )
            prevented_by_state_id = (
                None
                if hit_result.decisive_source is None
                else hit_result.decisive_source.source_state_id
            )
            return self._prevented_result(
                request,
                trace,
                prevented_by_state_id,
            )

        formula_policy_result = self._formula_policy.resolve(request, rules)
        formula_context = formula_policy_result.formula_context
        if request.damage_type is DamageType.WEAPON:
            base_damage = self._calculate_weapon_base_damage(
                context,
                source,
                target,
                formula_context=formula_context,
            )
        elif request.damage_type is DamageType.STRATEGY:
            base_damage = self._calculate_strategy_base_damage(
                context,
                source,
                target,
                formula_context=formula_context,
            )
        else:
            raise ValueError(f"unsupported damage type: {request.damage_type}")

        scaled_damage = validate_nonnegative_finite(
            base_damage * request.coefficient,
            "scaled_damage",
        )
        modifier_result = self._modifiers.resolve(
            context,
            request,
            rules,
            scaled_damage,
        )
        modified_damage = validate_nonnegative_finite(
            modifier_result.output_damage,
            "modified_damage",
        )
        final_damage = max(1, int(modified_damage))

        trace = DamagePipelineTrace(
            prevention_status=StageEvaluationStatus.EXECUTED,
            prevention_result=prevention_result,
            hit_status=StageEvaluationStatus.EXECUTED,
            hit_result=hit_result,
            formula_policy_status=StageEvaluationStatus.EXECUTED,
            formula_policy_result=formula_policy_result,
            modifier_status=StageEvaluationStatus.EXECUTED,
            modifier_result=modifier_result,
        )
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
            pipeline_trace=trace,
        )

    @staticmethod
    def _validate_participants(
        context: BattleContext,
        request: DamageRequest,
    ) -> tuple[UnitRuntime, UnitRuntime]:
        try:
            source = context.get_unit(request.source_id)
        except KeyError as exc:
            raise InvalidDamageParticipantError(
                f"damage source does not exist: {request.source_id}"
            ) from exc
        try:
            target = context.get_unit(request.target_id)
        except KeyError as exc:
            raise InvalidDamageParticipantError(
                f"damage target does not exist: {request.target_id}"
            ) from exc
        if source.troops <= 0:
            raise InvalidDamageParticipantError(
                f"damage source is dead: {request.source_id}"
            )
        if target.troops <= 0:
            raise InvalidDamageParticipantError(
                f"damage target is dead: {request.target_id}"
            )
        return source, target

    @staticmethod
    def _prevented_result(
        request: DamageRequest,
        trace: DamagePipelineTrace,
        prevented_by_state_id: str | None,
    ) -> DamageResult:
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
            prevented=True,
            prevented_by_state_id=prevented_by_state_id,
            source_state_id=request.source_state_id,
            source_state_instance_id=request.source_state_instance_id,
            pipeline_trace=trace,
        )

    def _calculate_weapon_base_damage(
        self,
        context: BattleContext,
        source: UnitRuntime,
        target: UnitRuntime,
        *,
        formula_context: DamageFormulaContext | None = None,
    ) -> int:
        if (
            formula_context is None
            or formula_context.defense_policy is DamageDefensePolicy.NORMAL
        ):
            return self._weapon_formula.calculate(context, source, target)
        return self._weapon_formula.calculate(
            context,
            source,
            target,
            formula_context=formula_context,
        )

    def _calculate_strategy_base_damage(
        self,
        context: BattleContext,
        source: UnitRuntime,
        target: UnitRuntime,
        *,
        formula_context: DamageFormulaContext | None = None,
    ) -> int:
        if (
            formula_context is None
            or formula_context.defense_policy is DamageDefensePolicy.NORMAL
        ):
            return self._strategy_formula.calculate(context, source, target)
        return self._strategy_formula.calculate(
            context,
            source,
            target,
            formula_context=formula_context,
        )
