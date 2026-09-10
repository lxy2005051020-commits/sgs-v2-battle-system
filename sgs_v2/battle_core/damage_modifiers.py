from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .damage_rule_models import RuleContributionSource
from .enums import DamageSourceType, DamageType
from .numeric_validation import validate_nonnegative_finite, validate_probability


class DamageModifierKind(str, Enum):
    CRITICAL_MULTIPLIER = "CRITICAL_MULTIPLIER"
    OUTGOING_INCREASE = "OUTGOING_INCREASE"
    OUTGOING_REDUCTION = "OUTGOING_REDUCTION"
    INCOMING_INCREASE = "INCOMING_INCREASE"
    INCOMING_REDUCTION = "INCOMING_REDUCTION"
    SINGLE_HIT_ADJUSTMENT = "SINGLE_HIT_ADJUSTMENT"
    REDUCTION_PIERCE = "REDUCTION_PIERCE"


class DamageModifierOperation(str, Enum):
    MULTIPLY_FACTOR = "MULTIPLY_FACTOR"
    REDUCTION_PIERCE = "REDUCTION_PIERCE"


class DamageModifierPhase(str, Enum):
    CRITICAL = "CRITICAL"
    OUTGOING = "OUTGOING"
    INCOMING = "INCOMING"
    SINGLE_HIT = "SINGLE_HIT"


_PHASE_ORDER = {
    DamageModifierPhase.CRITICAL: 0,
    DamageModifierPhase.OUTGOING: 1,
    DamageModifierPhase.INCOMING: 2,
    DamageModifierPhase.SINGLE_HIT: 3,
}


@dataclass(frozen=True, slots=True)
class DamageModifierContribution:
    phase: DamageModifierPhase
    kind: DamageModifierKind
    operation: DamageModifierOperation
    operand: float
    source: RuleContributionSource
    order_key: str
    probability: float = 1.0
    damage_types: frozenset[DamageType] | None = None
    source_types: frozenset[DamageSourceType] | None = None

    def __post_init__(self) -> None:
        if not self.order_key:
            raise ValueError("order_key cannot be empty")
        operand = validate_nonnegative_finite(self.operand, "modifier operand")
        probability = validate_probability(self.probability)
        object.__setattr__(self, "operand", operand)
        object.__setattr__(self, "probability", probability)

        if self.operation is DamageModifierOperation.REDUCTION_PIERCE:
            if self.kind is not DamageModifierKind.REDUCTION_PIERCE:
                raise ValueError("REDUCTION_PIERCE operation requires REDUCTION_PIERCE kind")
            if not 0.0 <= operand <= 1.0:
                raise ValueError("reduction pierce rate must be in [0, 1]")
        elif self.kind is DamageModifierKind.REDUCTION_PIERCE:
            raise ValueError("REDUCTION_PIERCE kind requires REDUCTION_PIERCE operation")

    def applies_to(self, damage_type: DamageType, source_type: DamageSourceType) -> bool:
        return (
            (self.damage_types is None or damage_type in self.damage_types)
            and (self.source_types is None or source_type in self.source_types)
        )

    @property
    def phase_order(self) -> int:
        return _PHASE_ORDER[self.phase]


@dataclass(frozen=True, slots=True)
class AppliedDamageModifier:
    contribution: DamageModifierContribution
    input_damage: float
    output_damage: float
    original_operand: float
    effective_operand: float
    pierce_contributor: RuleContributionSource | None = None


@dataclass(frozen=True, slots=True)
class DamageModifierResult:
    input_damage: float
    output_damage: float
    applied_modifiers: tuple[AppliedDamageModifier, ...]
