from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .damage_formula_policy_system import DamageFormulaPolicyResult
from .damage_modifiers import DamageModifierResult
from .damage_prevention_system import DamagePermissionResult
from .hit_resolution_system import HitResolutionResult


class StageEvaluationStatus(str, Enum):
    EXECUTED = "EXECUTED"
    NOT_EVALUATED = "NOT_EVALUATED"


@dataclass(frozen=True, slots=True)
class DamagePipelineTrace:
    prevention_status: StageEvaluationStatus
    prevention_result: DamagePermissionResult | None
    hit_status: StageEvaluationStatus
    hit_result: HitResolutionResult | None
    formula_policy_status: StageEvaluationStatus
    formula_policy_result: DamageFormulaPolicyResult | None
    modifier_status: StageEvaluationStatus
    modifier_result: DamageModifierResult | None

    def __post_init__(self) -> None:
        self._validate_stage(
            "prevention", self.prevention_status, self.prevention_result
        )
        self._validate_stage("hit", self.hit_status, self.hit_result)
        self._validate_stage(
            "formula_policy", self.formula_policy_status, self.formula_policy_result
        )
        self._validate_stage("modifier", self.modifier_status, self.modifier_result)

    @staticmethod
    def _validate_stage(
        stage_name: str,
        status: StageEvaluationStatus,
        result: object | None,
    ) -> None:
        if status is StageEvaluationStatus.EXECUTED and result is None:
            raise ValueError(f"{stage_name} EXECUTED requires a result")
        if status is StageEvaluationStatus.NOT_EVALUATED and result is not None:
            raise ValueError(f"{stage_name} NOT_EVALUATED requires result=None")
