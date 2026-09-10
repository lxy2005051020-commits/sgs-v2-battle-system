from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .damage_formula_policy_system import DamageFormulaPolicyResult
from .damage_modifiers import DamageModifierResult
from .damage_prevention_system import DamageAllowedResult, DamagePreventedResult
from .hit_resolution_system import HitAllowedResult, HitPreventedResult


class StageEvaluationStatus(str, Enum):
    EXECUTED = "EXECUTED"
    NOT_EVALUATED = "NOT_EVALUATED"


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

    def __post_init__(self) -> None:
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
