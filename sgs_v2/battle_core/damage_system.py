from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .attribute_system import AttributeSystem
from .context import BattleContext
from .damage_formula_context import DamageDefensePolicy, DamageFormulaContext
from .damage_formula_policy_system import DamageFormulaPolicySystem
from .damage_modifier_system import DamageModifierSystem
from .damage_modifiers import DamageModifierPhase
from .damage_pipeline_trace import (
    DamagePipelineTrace,
    FrozenApplicationTrace,
    StageEvaluationStatus,
)
from .damage_prevention_system import (
    DamageAllowedResult,
    DamagePreventedResult,
    DamagePreventionSystem,
)
from .damage_probability import resolve_probability
from .damage_rule_provider import (
    DamageRuleCollection,
    DamageRuleProvider,
    StateDamageRuleProvider,
)
from .damage_state_rule_bindings import DEFAULT_STAGE8_STATE_RULE_BINDINGS
from .enums import (
    CalculationBasis,
    DamageCalculationBasis,
    DamageSourceType,
    DamageType,
    TroopType,
)
from .hit_resolution_system import HitPreventedResult, HitResolutionSystem
from .numeric_validation import validate_nonnegative_finite
from .stage10_state_params import (
    FrozenContinuousDamageBasis,
    FrozenSourceFormulaFacts,
)
from .state_generation import StateApplicationGenerationId
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
    calculation_basis: DamageCalculationBasis = DamageCalculationBasis.LIVE_RUNTIME
    frozen_basis: FrozenContinuousDamageBasis | None = None
    source_generation_id: StateApplicationGenerationId | None = None

    def __post_init__(self) -> None:
        if not self.source_id:
            raise ValueError("source_id cannot be empty")
        if not self.target_id:
            raise ValueError("target_id cannot be empty")
        if not isinstance(self.damage_type, DamageType):
            raise TypeError("damage_type must be a DamageType")
        if not isinstance(self.source_type, DamageSourceType):
            raise TypeError("source_type must be a DamageSourceType")
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
        if not isinstance(self.calculation_basis, DamageCalculationBasis):
            raise TypeError("calculation_basis must be a DamageCalculationBasis")
        if self.calculation_basis is DamageCalculationBasis.FROZEN_APPLICATION:
            if self.source_type is not DamageSourceType.CONTINUOUS:
                raise ValueError("FROZEN_APPLICATION is only authorized for CONTINUOUS damage")
            if self.frozen_basis is None:
                raise ValueError("frozen_basis is required for FROZEN_APPLICATION")
            if not isinstance(self.frozen_basis, FrozenContinuousDamageBasis):
                raise TypeError("frozen_basis must be a FrozenContinuousDamageBasis")
            if self.source_generation_id is None:
                raise ValueError("source_generation_id is required for FROZEN_APPLICATION")
            if not isinstance(self.source_generation_id, StateApplicationGenerationId):
                raise TypeError("source_generation_id must be a StateApplicationGenerationId")
        else:
            if self.frozen_basis is not None:
                raise ValueError("frozen_basis must be None for LIVE_RUNTIME")


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
    calculation_basis: DamageCalculationBasis = DamageCalculationBasis.LIVE_RUNTIME
    source_generation_id: StateApplicationGenerationId | None = None
    pipeline_trace: DamagePipelineTrace | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.damage_type, DamageType):
            raise TypeError("damage_type must be a DamageType")
        if not isinstance(self.source_type, DamageSourceType):
            raise TypeError("source_type must be a DamageSourceType")
        _validate_optional_state_id(self.source_state_id, "source_state_id")
        _validate_optional_state_id(
            self.source_state_instance_id,
            "source_state_instance_id",
        )
        _validate_state_provenance_pair(
            self.source_state_id,
            self.source_state_instance_id,
        )
        if not isinstance(self.calculation_basis, DamageCalculationBasis):
            raise TypeError("calculation_basis must be a DamageCalculationBasis")
        if self.source_generation_id is not None and not isinstance(
            self.source_generation_id, StateApplicationGenerationId
        ):
            raise TypeError("source_generation_id must be a StateApplicationGenerationId or None")

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
        self._rule_provider = (
            StateDamageRuleProvider(DEFAULT_STAGE8_STATE_RULE_BINDINGS)
            if rule_provider is None
            else rule_provider
        )
        self._prevention = (
            DamagePreventionSystem() if prevention_system is None else prevention_system
        )
        self._hit = (
            HitResolutionSystem()
            if hit_resolution_system is None
            else hit_resolution_system
        )
        self._formula_policy = (
            DamageFormulaPolicySystem()
            if formula_policy_system is None
            else formula_policy_system
        )
        self._modifiers = (
            DamageModifierSystem() if modifier_system is None else modifier_system
        )

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
        if not isinstance(rules, DamageRuleCollection):
            raise TypeError("DamageRuleProvider.collect() must return DamageRuleCollection")

        prevention_result = self._prevention.resolve(rules)
        if isinstance(prevention_result, DamagePreventedResult):
            frozen_trace = (
                FrozenApplicationTrace(
                    application_generation_id=request.source_generation_id
                    or request.frozen_basis.application_generation_id,
                    formula_policy_result=(
                        request.frozen_basis.formula_policy_result
                        if request.frozen_basis
                        else None
                    ),
                    source_formula_facts=(
                        request.frozen_basis.source_formula_facts
                        if request.frozen_basis
                        else None
                    ),
                    coefficient=request.coefficient,
                    locked_modifier_plan=(
                        request.frozen_basis.locked_modifier_plan
                        if request.frozen_basis
                        else ()
                    ),
                    locked_crit_context=(
                        request.frozen_basis.locked_crit_context
                        if request.frozen_basis
                        else None
                    ),
                )
                if request.calculation_basis is DamageCalculationBasis.FROZEN_APPLICATION
                else None
            )
            trace = DamagePipelineTrace(
                prevention_status=StageEvaluationStatus.EXECUTED,
                prevention_result=prevention_result,
                hit_status=StageEvaluationStatus.NOT_EVALUATED,
                hit_result=None,
                formula_policy_status=StageEvaluationStatus.NOT_EVALUATED,
                formula_policy_result=None,
                modifier_status=StageEvaluationStatus.NOT_EVALUATED,
                modifier_result=None,
                calculation_basis=request.calculation_basis,
                frozen_application_trace=frozen_trace,
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
            frozen_trace = (
                FrozenApplicationTrace(
                    application_generation_id=request.source_generation_id
                    or request.frozen_basis.application_generation_id,
                    formula_policy_result=(
                        request.frozen_basis.formula_policy_result
                        if request.frozen_basis
                        else None
                    ),
                    source_formula_facts=(
                        request.frozen_basis.source_formula_facts
                        if request.frozen_basis
                        else None
                    ),
                    coefficient=request.coefficient,
                    locked_modifier_plan=(
                        request.frozen_basis.locked_modifier_plan
                        if request.frozen_basis
                        else ()
                    ),
                    locked_crit_context=(
                        request.frozen_basis.locked_crit_context
                        if request.frozen_basis
                        else None
                    ),
                )
                if request.calculation_basis is DamageCalculationBasis.FROZEN_APPLICATION
                else None
            )
            trace = DamagePipelineTrace(
                prevention_status=StageEvaluationStatus.EXECUTED,
                prevention_result=prevention_result,
                hit_status=StageEvaluationStatus.EXECUTED,
                hit_result=hit_result,
                formula_policy_status=StageEvaluationStatus.NOT_EVALUATED,
                formula_policy_result=None,
                modifier_status=StageEvaluationStatus.NOT_EVALUATED,
                modifier_result=None,
                calculation_basis=request.calculation_basis,
                frozen_application_trace=frozen_trace,
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

        if request.calculation_basis is DamageCalculationBasis.FROZEN_APPLICATION:
            frozen_basis = request.frozen_basis
            assert frozen_basis is not None
            formula_policy_result = frozen_basis.formula_policy_result or DamageFormulaPolicyResult(
                DamageFormulaContext(), ()
            )
            formula_context = formula_policy_result.formula_context

            if frozen_basis.source_formula_facts is None:
                raise ValueError("FROZEN_APPLICATION requires source_formula_facts in basis")

            base_damage = self._calculate_base_damage_from_frozen_facts(
                context,
                frozen_basis.source_formula_facts,
                target,
                request.damage_type,
                formula_context,
            )
            scaled_damage = validate_nonnegative_finite(
                base_damage * request.coefficient,
                "scaled_damage",
            )

            current = scaled_damage
            for mod in frozen_basis.locked_modifier_plan:
                if mod.admitted:
                    current = validate_nonnegative_finite(current * mod.operand, "modifier output")

            target_mods = [
                c
                for c in rules.modifier_contributions
                if c.applies_to(request.damage_type, request.source_type)
                and c.phase in (DamageModifierPhase.INCOMING, DamageModifierPhase.SINGLE_HIT)
            ]
            if target_mods:
                target_mods.sort(key=lambda c: (c.phase_order, c.order_key))
                for c in target_mods:
                    if resolve_probability(context, c.probability):
                        current = validate_nonnegative_finite(current * c.operand, "modifier output")

            final_damage = max(1, int(current))

            frozen_trace = FrozenApplicationTrace(
                application_generation_id=request.source_generation_id
                or frozen_basis.application_generation_id,
                formula_policy_result=formula_policy_result,
                source_formula_facts=frozen_basis.source_formula_facts,
                coefficient=request.coefficient,
                locked_modifier_plan=frozen_basis.locked_modifier_plan,
                locked_crit_context=frozen_basis.locked_crit_context,
            )
            trace = DamagePipelineTrace(
                prevention_status=StageEvaluationStatus.EXECUTED,
                prevention_result=prevention_result,
                hit_status=StageEvaluationStatus.EXECUTED,
                hit_result=hit_result,
                formula_policy_status=StageEvaluationStatus.NOT_EVALUATED,
                formula_policy_result=None,
                modifier_status=StageEvaluationStatus.NOT_EVALUATED,
                modifier_result=None,
                calculation_basis=DamageCalculationBasis.FROZEN_APPLICATION,
                frozen_application_trace=frozen_trace,
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
                calculation_basis=request.calculation_basis,
                source_generation_id=request.source_generation_id,
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
            calculation_basis=DamageCalculationBasis.LIVE_RUNTIME,
            frozen_application_trace=None,
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
            calculation_basis=request.calculation_basis,
            source_generation_id=request.source_generation_id,
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

        if request.calculation_basis is DamageCalculationBasis.LIVE_RUNTIME:
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
            calculation_basis=request.calculation_basis,
            source_generation_id=request.source_generation_id,
        )

    def _calculate_base_damage_from_frozen_facts(
        self,
        context: BattleContext,
        frozen_facts: FrozenSourceFormulaFacts,
        target: UnitRuntime,
        damage_type: DamageType,
        formula_context: DamageFormulaContext,
    ) -> int:
        from math import ceil

        troops = frozen_facts.source_troops_at_application
        offense = frozen_facts.source_combat_attribute_at_application
        formula = (
            self._weapon_formula
            if damage_type is DamageType.WEAPON
            else self._strategy_formula
        )

        if formula_context.defense_policy is DamageDefensePolicy.IGNORE_RELEVANT_TARGET_DEFENSE:
            defense = 0.0
        else:
            if damage_type is DamageType.WEAPON:
                defense = self._attributes.get_defense(context, target)
            else:
                if target.intelligence is None:
                    raise NotImplementedError(
                        "strategy base damage requires an intelligence value for target"
                    )
                defense = self._attributes.get_intelligence(context, target)

        source_level_scale = 0.6 + 0.02 * frozen_facts.source_level_at_application
        target_level_scale = 0.6 + 0.02 * target.level

        x = (
            formula.troop_function(troops)
            + offense * source_level_scale
            - defense * target_level_scale
        )
        troop_floor = min(100, ceil(troops / 50))
        b0 = ceil(max(x, troop_floor))

        source_type = frozen_facts.source_troop_type_at_application
        target_type = target.troop_type
        if source_type is TroopType.SPEAR and target_type is TroopType.CAVALRY:
            counter_mult = 1.12
        elif source_type is TroopType.CAVALRY and target_type is TroopType.SPEAR:
            counter_mult = 0.88
        else:
            counter_mult = 1.0

        b1 = ceil(b0 * counter_mult)

        morale_multiplier = 1 - 0.007 * max(0, 100 - frozen_facts.source_morale_at_application)
        b2 = ceil(b1 * morale_multiplier)

        random_percent = context.random.randint(*formula.random_percent_range)
        d0 = ceil(b2 * random_percent / 100)

        low_damage_floor = context.random.randint(*formula.low_damage_floor_range)
        return max(d0, low_damage_floor)

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
