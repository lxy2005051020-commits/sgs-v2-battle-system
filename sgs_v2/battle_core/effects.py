from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .damage_system import DamageRequest
from .enums import DamageCalculationBasis, DamageSourceType, DamageType
from .numeric_validation import validate_nonnegative_finite
from .operation_identity import SourceType
from .recovery_system import RecoveryRequest
from .skill_runtime import SkillSlot
from .stage10_state_params import FrozenContinuousDamageBasis
from .state_generation import StateApplicationGenerationId
from .state_runtime_params import EmptyStateRuntimeParams, StateRuntimeParams

if TYPE_CHECKING:
    from .rule_intent import RuleIntentExecutionDescriptor


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


def _validate_execution_descriptor(descriptor: object) -> None:
    if descriptor is None:
        return
    if type(descriptor).__name__ != "RuleIntentExecutionDescriptor":
        raise TypeError(
            f"execution_descriptor must be a RuleIntentExecutionDescriptor or None, got {type(descriptor)}"
        )


@dataclass(frozen=True, slots=True)
class EffectSourceRef:
    """Stage9 canonical pre-operation effect provenance."""

    stage9_source_type: SourceType
    source_unit_id: str | None = None
    source_skill_id: str | None = None
    source_skill_slot: SkillSlot | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.stage9_source_type, SourceType):
            raise TypeError(
                f"stage9_source_type must be a SourceType, got {type(self.stage9_source_type)}"
            )
        _validate_optional_id(self.source_unit_id, "source_unit_id")
        _validate_optional_id(self.source_skill_id, "source_skill_id")
        if self.source_skill_slot is not None and not isinstance(self.source_skill_slot, SkillSlot):
            raise TypeError(
                f"source_skill_slot must be a SkillSlot or None, got {type(self.source_skill_slot)}"
            )
        if self.stage9_source_type == SourceType.ACTIVE_SKILL:
            if self.source_unit_id is None or not self.source_unit_id.strip():
                raise ValueError("source_unit_id is required for ACTIVE_SKILL EffectSourceRef")
            if self.source_skill_id is None or not self.source_skill_id.strip():
                raise ValueError("source_skill_id is required for ACTIVE_SKILL EffectSourceRef")


@dataclass(frozen=True, slots=True)
class DamageEffect:
    source_id: str
    target_id: str
    damage_type: DamageType
    source_type: DamageSourceType
    coefficient: float = 1.0
    source_skill_id: str | None = None
    source_state_id: str | None = None
    source_state_instance_id: str | None = None
    source_ref: EffectSourceRef | None = None
    execution_descriptor: RuleIntentExecutionDescriptor | None = field(
        default=None, compare=False
    )
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
        _validate_optional_id(self.source_state_id, "source_state_id")
        _validate_optional_id(
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
        if self.source_ref is not None:
            if not isinstance(self.source_ref, EffectSourceRef):
                raise TypeError("source_ref must be an EffectSourceRef or None")
            if self.source_ref.source_unit_id is not None and self.source_ref.source_unit_id != self.source_id:
                raise ValueError(
                    f"source_ref.source_unit_id '{self.source_ref.source_unit_id}' does not match source_id '{self.source_id}'"
                )
            if self.source_skill_id is not None and self.source_ref.source_skill_id is not None:
                if self.source_ref.source_skill_id != self.source_skill_id:
                    raise ValueError(
                        f"source_ref.source_skill_id '{self.source_ref.source_skill_id}' does not match source_skill_id '{self.source_skill_id}'"
                    )
        _validate_execution_descriptor(self.execution_descriptor)

    def to_request(self) -> DamageRequest:
        return DamageRequest(
            source_id=self.source_id,
            target_id=self.target_id,
            damage_type=self.damage_type,
            source_type=self.source_type,
            coefficient=self.coefficient,
            source_skill_id=self.source_skill_id,
            source_state_id=self.source_state_id,
            source_state_instance_id=self.source_state_instance_id,
            calculation_basis=self.calculation_basis,
            frozen_basis=self.frozen_basis,
            source_generation_id=self.source_generation_id,
        )


@dataclass(frozen=True, slots=True)
class ApplyStateEffect:
    state_id: str
    owner_id: str
    source_id: str | None = None
    source_skill_id: str | None = None
    expires_round: int | None = None
    expires_phase: str | None = None
    runtime_params: StateRuntimeParams = field(
        default_factory=EmptyStateRuntimeParams
    )
    source_ref: EffectSourceRef | None = None
    execution_descriptor: RuleIntentExecutionDescriptor | None = field(
        default=None, compare=False
    )

    def __post_init__(self) -> None:
        if not self.state_id:
            raise ValueError("state_id cannot be empty")
        if not self.owner_id:
            raise ValueError("owner_id cannot be empty")
        if self.source_id == "":
            raise ValueError("source_id cannot be empty when provided")
        if self.source_skill_id == "":
            raise ValueError("source_skill_id cannot be empty when provided")
        if self.source_ref is not None:
            if not isinstance(self.source_ref, EffectSourceRef):
                raise TypeError("source_ref must be an EffectSourceRef or None")
            if self.source_id is not None and self.source_ref.source_unit_id is not None:
                if self.source_ref.source_unit_id != self.source_id:
                    raise ValueError(
                        f"source_ref.source_unit_id '{self.source_ref.source_unit_id}' does not match source_id '{self.source_id}'"
                    )
            if self.source_skill_id is not None and self.source_ref.source_skill_id is not None:
                if self.source_ref.source_skill_id != self.source_skill_id:
                    raise ValueError(
                        f"source_ref.source_skill_id '{self.source_ref.source_skill_id}' does not match source_skill_id '{self.source_skill_id}'"
                    )
        _validate_execution_descriptor(self.execution_descriptor)


@dataclass(frozen=True, slots=True)
class RemoveStateEffect:
    instance_id: str
    execution_descriptor: RuleIntentExecutionDescriptor | None = field(
        default=None, compare=False
    )

    def __post_init__(self) -> None:
        if not self.instance_id:
            raise ValueError("instance_id cannot be empty")
        _validate_execution_descriptor(self.execution_descriptor)


@dataclass(frozen=True, slots=True)
class RecoverEffect:
    """Stage 7 正式恢复意图合同；Effect 本身保持纯数据、无副作用。"""

    source_id: str | None
    target_id: str
    amount: int
    source_skill_id: str | None = None
    source_state_id: str | None = None
    source_state_instance_id: str | None = None
    execution_descriptor: RuleIntentExecutionDescriptor | None = field(
        default=None, compare=False
    )

    def __post_init__(self) -> None:
        _validate_optional_id(self.source_id, "source_id")
        if not isinstance(self.target_id, str):
            raise TypeError("target_id must be a str")
        if not self.target_id.strip():
            raise ValueError("target_id cannot be empty or whitespace")
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
        if isinstance(self.amount, bool) or not isinstance(self.amount, int):
            raise TypeError("amount must be an int")
        if self.amount < 0:
            raise ValueError("amount must be >= 0")
        _validate_execution_descriptor(self.execution_descriptor)

    def to_request(self) -> RecoveryRequest:
        return RecoveryRequest(
            source_id=self.source_id,
            target_id=self.target_id,
            amount=self.amount,
            source_skill_id=self.source_skill_id,
            source_state_id=self.source_state_id,
            source_state_instance_id=self.source_state_instance_id,
        )


Effect = DamageEffect | ApplyStateEffect | RemoveStateEffect | RecoverEffect
