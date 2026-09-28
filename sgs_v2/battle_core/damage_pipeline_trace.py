from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from typing import Any, TYPE_CHECKING

from .damage_formula_policy_system import DamageFormulaPolicyResult
from .damage_modifiers import DamageModifierResult
from .damage_prevention_system import DamageAllowedResult, DamagePreventedResult
from .enums import DamageCalculationBasis
from .hit_resolution_system import HitAllowedResult, HitPreventedResult

if TYPE_CHECKING:
    from .stage10_state_params import FrozenSourceFormulaFacts
    from .state_generation import StateApplicationGenerationId


class StageEvaluationStatus(str, Enum):
    EXECUTED = "EXECUTED"
    NOT_EVALUATED = "NOT_EVALUATED"


@dataclass(frozen=True, slots=True)
class FrozenApplicationTrace:
    """
    Provenance trace captured for the FROZEN_APPLICATION theoretical-damage lane (STAGE8_ADDENDUM §12).
    """

    application_generation_id: Any  # StateApplicationGenerationId
    formula_policy_result: DamageFormulaPolicyResult | None
    source_formula_facts: Any | None  # FrozenSourceFormulaFacts
    coefficient: float
    locked_modifier_plan: tuple[Any, ...] = ()
    locked_crit_context: object | None = None


@dataclass(frozen=True, slots=True)
class DamagePipelineTrace:
    prevention_status: StageEvaluationStatus
    prevention_result: DamageAllowedResult | DamagePreventedResult | None
    hit_status: StageEvaluationStatus
    hit_result: HitAllowedResult | HitPreventedResult | None
    formula_policy_status: StageEvaluationStatus
    formula_policy_result: DamageFormulaPolicyResult | None
    modifier_status: StageEvaluationStatus
    modifier_result: DamageModifierResult | None
    calculation_basis: DamageCalculationBasis = DamageCalculationBasis.LIVE_RUNTIME
    frozen_application_trace: FrozenApplicationTrace | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.calculation_basis, DamageCalculationBasis):
            raise TypeError(
                f"calculation_basis must be a DamageCalculationBasis, got {type(self.calculation_basis)}"
            )
        if self.calculation_basis is DamageCalculationBasis.LIVE_RUNTIME:
            if self.frozen_application_trace is not None:
                raise ValueError("frozen_application_trace must be None for LIVE_RUNTIME")
        elif self.calculation_basis is DamageCalculationBasis.FROZEN_APPLICATION:
            if self.frozen_application_trace is None:
                raise ValueError("frozen_application_trace is required for FROZEN_APPLICATION")

        self._validate_stage(
            "prevention",
            self.prevention_status,
            self.prevention_result,
            (DamageAllowedResult, DamagePreventedResult),
        )
        self._validate_stage(
            "hit",
            self.hit_status,
            self.hit_result,
            (HitAllowedResult, HitPreventedResult),
        )
        self._validate_stage(
            "formula_policy",
            self.formula_policy_status,
            self.formula_policy_result,
            (DamageFormulaPolicyResult,),
        )
        self._validate_stage(
            "modifier",
            self.modifier_status,
            self.modifier_result,
            (DamageModifierResult,),
        )

    @staticmethod
    def _validate_stage(
        stage_name: str,
        status: StageEvaluationStatus,
        result: object | None,
        expected_result_types: tuple[type, ...],
    ) -> None:
        if not isinstance(status, StageEvaluationStatus):
            raise TypeError(f"{stage_name}_status must be a StageEvaluationStatus")
        if status is StageEvaluationStatus.EXECUTED:
            if result is None:
                raise ValueError(f"{stage_name} EXECUTED requires a result")
            if not isinstance(result, expected_result_types):
                expected = " or ".join(
                    result_type.__name__ for result_type in expected_result_types
                )
                raise TypeError(f"{stage_name}_result must be {expected}")
            return
        if result is not None:
            raise ValueError(f"{stage_name} NOT_EVALUATED requires result=None")

