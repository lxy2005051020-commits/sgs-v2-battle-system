from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum

from .enums import DamageType
from .numeric_validation import validate_nonnegative_finite
from .skill_runtime import SkillSlot
from .skill_runtime_registry import (
    PersistentSourceSkillGate,
    PersistentSourceSkillGateMode,
)
from .state_generation import (
    PersistentLifecycleWindow,
    StateApplicationGenerationId,
)
from .state_runtime_params import StateRuntimeParams


def _validate_probability(val: float, name: str = "probability") -> float:
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        raise TypeError(f"{name} must be a float, got {type(val)}")
    if math.isnan(val) or math.isinf(val):
        raise ValueError(f"{name} must be a finite number")
    if not (0.0 <= float(val) <= 1.0):
        raise ValueError(f"{name} must be between 0.0 and 1.0, got {val}")
    return float(val)


class RecoveryModelKind(str, Enum):
    """
    Authoritative recovery calculation model kind (STAGE10.md §17, §29).
    - TREATMENT_AMOUNT: Recovery amount based on caster attributes & treatment rate (e.g. 青囊, 陷阵营).
    - TRIGGER_DAMAGE_RATIO: Recovery amount based on triggering damage loss ratio (e.g. 草船借箭).
    """

    TREATMENT_AMOUNT = "TREATMENT_AMOUNT"
    TRIGGER_DAMAGE_RATIO = "TRIGGER_DAMAGE_RATIO"


@dataclass(frozen=True, slots=True)
class RecoveryPotencyContext:
    """
    Application-time frozen recovery potency facts (STAGE10.md §13.3, §29).
    Contains base rates, ratios, amounts, and application-time caster attributes.
    """

    base_rate: float = 0.0
    ratio: float = 0.0
    treatment_amount: int = 0
    source_intellect: int | None = None
    source_command: int | None = None

    def __post_init__(self) -> None:
        base_rate = validate_nonnegative_finite(self.base_rate, "base_rate")
        ratio = validate_nonnegative_finite(self.ratio, "ratio")
        object.__setattr__(self, "base_rate", base_rate)
        object.__setattr__(self, "ratio", ratio)
        if isinstance(self.treatment_amount, bool) or not isinstance(self.treatment_amount, int):
            raise TypeError("treatment_amount must be an int")
        if self.treatment_amount < 0:
            raise ValueError("treatment_amount cannot be negative")
        if self.source_intellect is not None:
            if isinstance(self.source_intellect, bool) or not isinstance(self.source_intellect, int):
                raise TypeError("source_intellect must be an int or None")
            if self.source_intellect < 0:
                raise ValueError("source_intellect cannot be negative")
        if self.source_command is not None:
            if isinstance(self.source_command, bool) or not isinstance(self.source_command, int):
                raise TypeError("source_command must be an int or None")
            if self.source_command < 0:
                raise ValueError("source_command cannot be negative")


@dataclass(frozen=True, slots=True)
class FrozenContinuousDamageBasis:
    """
    Composition point for application-time frozen continuous damage facts (STAGE8_ADDENDUM §6, STAGE10.md §29).
    Replayed through DamageSystem on the authorized FROZEN_APPLICATION lane.
    """

    application_generation_id: StateApplicationGenerationId
    source_unit_id: str
    damage_type: DamageType
    coefficient: float = 1.0
    source_skill_id: str | None = None
    source_skill_slot: SkillSlot | None = None
    source_state_id: str | None = None
    physical_state_instance_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.application_generation_id, StateApplicationGenerationId):
            raise TypeError(
                f"application_generation_id must be a StateApplicationGenerationId, got {type(self.application_generation_id)}"
            )
        if not isinstance(self.source_unit_id, str) or not self.source_unit_id.strip():
            raise ValueError("source_unit_id cannot be empty or whitespace")
        if not isinstance(self.damage_type, DamageType):
            raise TypeError(f"damage_type must be a DamageType, got {type(self.damage_type)}")
        coef = validate_nonnegative_finite(self.coefficient, "coefficient")
        object.__setattr__(self, "coefficient", coef)
        if self.source_skill_id is not None and (not isinstance(self.source_skill_id, str) or not self.source_skill_id.strip()):
            raise ValueError("source_skill_id cannot be empty or whitespace when provided")
        if self.source_skill_slot is not None and not isinstance(self.source_skill_slot, SkillSlot):
            raise TypeError(f"source_skill_slot must be a SkillSlot or None, got {type(self.source_skill_slot)}")
        if self.source_state_id is not None and (not isinstance(self.source_state_id, str) or not self.source_state_id.strip()):
            raise ValueError("source_state_id cannot be empty or whitespace when provided")
        if self.physical_state_instance_id is not None and (not isinstance(self.physical_state_instance_id, str) or not self.physical_state_instance_id.strip()):
            raise ValueError("physical_state_instance_id cannot be empty or whitespace when provided")


@dataclass(frozen=True, slots=True)
class ContinuousDamageStateParams(StateRuntimeParams):
    """
    Authoritative runtime parameters for continuous damage states (STAGE10.md §29).
    Covers BURN (690072), FLOOD (690073), POISON (690074), ROUT (690075),
    SANDSTORM (690076), REBELLION (690077).
    """

    application_generation_id: StateApplicationGenerationId | None = None
    lifecycle_window: PersistentLifecycleWindow | None = None
    frozen_damage_basis: FrozenContinuousDamageBasis | None = None
    source_skill_gate: PersistentSourceSkillGate = field(
        default_factory=PersistentSourceSkillGate.always_active
    )

    def __post_init__(self) -> None:
        if self.application_generation_id is not None and not isinstance(
            self.application_generation_id, StateApplicationGenerationId
        ):
            raise TypeError(
                f"application_generation_id must be a StateApplicationGenerationId or None, got {type(self.application_generation_id)}"
            )
        if self.lifecycle_window is not None and not isinstance(
            self.lifecycle_window, PersistentLifecycleWindow
        ):
            raise TypeError(
                f"lifecycle_window must be a PersistentLifecycleWindow or None, got {type(self.lifecycle_window)}"
            )
        if self.frozen_damage_basis is not None and not isinstance(
            self.frozen_damage_basis, FrozenContinuousDamageBasis
        ):
            raise TypeError(
                f"frozen_damage_basis must be a FrozenContinuousDamageBasis or None, got {type(self.frozen_damage_basis)}"
            )
        if not isinstance(self.source_skill_gate, PersistentSourceSkillGate):
            raise TypeError(
                f"source_skill_gate must be a PersistentSourceSkillGate, got {type(self.source_skill_gate)}"
            )


@dataclass(frozen=True, slots=True)
class FirstAidStateParams(StateRuntimeParams):
    """
    Authoritative runtime parameters for FIRST_AID state (690078, STAGE10.md §29).
    Evaluated as an after-damage reaction recovery opportunity.
    """

    probability: float
    recovery_model_kind: RecoveryModelKind
    application_generation_id: StateApplicationGenerationId | None = None
    lifecycle_window: PersistentLifecycleWindow | None = None
    recovery_potency_context: RecoveryPotencyContext | None = None
    source_skill_gate: PersistentSourceSkillGate = field(
        default_factory=PersistentSourceSkillGate.query_skill_runtime
    )

    def __post_init__(self) -> None:
        prob = _validate_probability(self.probability, "probability")
        object.__setattr__(self, "probability", prob)
        if not isinstance(self.recovery_model_kind, RecoveryModelKind):
            raise TypeError(
                f"recovery_model_kind must be a RecoveryModelKind, got {type(self.recovery_model_kind)}"
            )
        if self.application_generation_id is not None and not isinstance(
            self.application_generation_id, StateApplicationGenerationId
        ):
            raise TypeError(
                f"application_generation_id must be a StateApplicationGenerationId or None, got {type(self.application_generation_id)}"
            )
        if self.lifecycle_window is not None and not isinstance(
            self.lifecycle_window, PersistentLifecycleWindow
        ):
            raise TypeError(
                f"lifecycle_window must be a PersistentLifecycleWindow or None, got {type(self.lifecycle_window)}"
            )
        if self.recovery_potency_context is not None and not isinstance(
            self.recovery_potency_context, RecoveryPotencyContext
        ):
            raise TypeError(
                f"recovery_potency_context must be a RecoveryPotencyContext or None, got {type(self.recovery_potency_context)}"
            )
        if not isinstance(self.source_skill_gate, PersistentSourceSkillGate):
            raise TypeError(
                f"source_skill_gate must be a PersistentSourceSkillGate, got {type(self.source_skill_gate)}"
            )


@dataclass(frozen=True, slots=True)
class RecuperationStateParams(StateRuntimeParams):
    """
    Authoritative runtime parameters for RECUPERATION state (690079, STAGE10.md §29).
    Evaluated as a turn-based action-start recovery opportunity.
    """

    probability: float
    application_generation_id: StateApplicationGenerationId | None = None
    lifecycle_window: PersistentLifecycleWindow | None = None
    recovery_potency_context: RecoveryPotencyContext | None = None
    source_skill_gate: PersistentSourceSkillGate = field(
        default_factory=PersistentSourceSkillGate.query_skill_runtime
    )

    def __post_init__(self) -> None:
        prob = _validate_probability(self.probability, "probability")
        object.__setattr__(self, "probability", prob)
        if self.application_generation_id is not None and not isinstance(
            self.application_generation_id, StateApplicationGenerationId
        ):
            raise TypeError(
                f"application_generation_id must be a StateApplicationGenerationId or None, got {type(self.application_generation_id)}"
            )
        if self.lifecycle_window is not None and not isinstance(
            self.lifecycle_window, PersistentLifecycleWindow
        ):
            raise TypeError(
                f"lifecycle_window must be a PersistentLifecycleWindow or None, got {type(self.lifecycle_window)}"
            )
        if self.recovery_potency_context is not None and not isinstance(
            self.recovery_potency_context, RecoveryPotencyContext
        ):
            raise TypeError(
                f"recovery_potency_context must be a RecoveryPotencyContext or None, got {type(self.recovery_potency_context)}"
            )
        if not isinstance(self.source_skill_gate, PersistentSourceSkillGate):
            raise TypeError(
                f"source_skill_gate must be a PersistentSourceSkillGate, got {type(self.source_skill_gate)}"
            )
