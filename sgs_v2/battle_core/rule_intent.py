from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

from .effect_result import EffectExecutionResult
from .effects import Effect, EffectSourceRef
from .recovery_system import RecoveryResult
from .skill_runtime_registry import PersistentSourceSkillGate
from .stage10_state_params import RecoveryModelKind, RecoveryPotencyContext
from .state_generation import StateApplicationGenerationId

if TYPE_CHECKING:
    pass


class RuleIntentKind(str, Enum):
    """Discriminator for the sibling RuleIntent hierarchy (STAGE10.md §4.1)."""

    EFFECT = "EFFECT"
    RECOVERY_OPPORTUNITY = "RECOVERY_OPPORTUNITY"


class RecoveryOpportunityKind(str, Enum):
    """
    Authoritative enum for Stage 10 recovery opportunities (STAGE10.md §22.1).
    - FIRST_AID_AFTER_DAMAGE: Triggered by resolved damage hit aftermath.
    - RECUPERATION_ACTION_START: Triggered at unit action start.
    Inference via aftermath_fact is None is strictly prohibited.
    """

    FIRST_AID_AFTER_DAMAGE = "FIRST_AID_AFTER_DAMAGE"
    RECUPERATION_ACTION_START = "RECUPERATION_ACTION_START"


class ExecutionRightDecisionKind(str, Enum):
    """Authoritative decision kind returned by ExecutionRightSystem (STAGE10.md §4.2)."""

    ALLOW = "ALLOW"
    REJECT_CURRENT = "REJECT_CURRENT"
    ABORT_OWNER_STATE_REMAINDER = "ABORT_OWNER_STATE_REMAINDER"
    ABORT_HOOK = "ABORT_HOOK"


class ExecutionRightReason(str, Enum):
    """Explicit typed reason for non-ALLOW ExecutionRight decisions (STAGE10.md §4.2)."""

    TARGET_DEFEATED = "TARGET_DEFEATED"
    OWNER_DEFEATED = "OWNER_DEFEATED"
    STATE_NOT_FOUND = "STATE_NOT_FOUND"
    SUPPRESSED = "SUPPRESSED"
    BATTLE_FINALIZED = "BATTLE_FINALIZED"
    INVALID_TARGET = "INVALID_TARGET"


@dataclass(frozen=True, slots=True)
class RuleIntentExecutionDescriptor:
    """
    Immutable typed descriptor carried by every RuleIntent (STAGE10.md §4.1.1).
    Eliminates duck-typing and introspection in ExecutionRightSystem and RuleHookSystem.
    Precondition invariant S10-FG-H01: intent_owner_id must never be empty.
    """

    intent_kind: RuleIntentKind
    intent_owner_id: str
    state_owner_id: str | None = None
    target_id: str | None = None
    source_ref: EffectSourceRef | None = None
    state_instance_id: str | None = None
    state_generation_id: StateApplicationGenerationId | None = None
    execution_domain: str = "STATE_RESOLUTION"

    def __post_init__(self) -> None:
        if not isinstance(self.intent_kind, RuleIntentKind):
            raise TypeError(
                f"intent_kind must be a RuleIntentKind, got {type(self.intent_kind)}"
            )
        if not isinstance(self.intent_owner_id, str) or not self.intent_owner_id.strip():
            raise ValueError("intent_owner_id cannot be empty or whitespace")
        if self.state_owner_id is not None and (
            not isinstance(self.state_owner_id, str) or not self.state_owner_id.strip()
        ):
            raise ValueError("state_owner_id cannot be empty or whitespace when provided")
        if self.target_id is not None and (
            not isinstance(self.target_id, str) or not self.target_id.strip()
        ):
            raise ValueError("target_id cannot be empty or whitespace when provided")
        if self.source_ref is not None and not isinstance(self.source_ref, EffectSourceRef):
            raise TypeError(
                f"source_ref must be an EffectSourceRef or None, got {type(self.source_ref)}"
            )
        if self.state_instance_id is not None and (
            not isinstance(self.state_instance_id, str) or not self.state_instance_id.strip()
        ):
            raise ValueError("state_instance_id cannot be empty or whitespace when provided")
        if self.state_generation_id is not None and not isinstance(
            self.state_generation_id, StateApplicationGenerationId
        ):
            raise TypeError(
                f"state_generation_id must be a StateApplicationGenerationId or None, got {type(self.state_generation_id)}"
            )
        if not isinstance(self.execution_domain, str) or not self.execution_domain.strip():
            raise ValueError("execution_domain cannot be empty or whitespace")


@dataclass(frozen=True, slots=True)
class RecoveryOpportunity:
    """
    Immutable representation of an admitted or candidate recovery opportunity (STAGE10.md §20, §22).
    Sibling of Effect in the RuleIntent model.
    """

    opportunity_kind: RecoveryOpportunityKind
    execution_descriptor: RuleIntentExecutionDescriptor
    probability: float
    recovery_model_kind: RecoveryModelKind = RecoveryModelKind.TREATMENT_AMOUNT
    recovery_potency_context: RecoveryPotencyContext | None = None
    source_skill_gate: PersistentSourceSkillGate = field(
        default_factory=PersistentSourceSkillGate.always_active
    )

    def __post_init__(self) -> None:
        if not isinstance(self.opportunity_kind, RecoveryOpportunityKind):
            raise TypeError(
                f"opportunity_kind must be a RecoveryOpportunityKind, got {type(self.opportunity_kind)}"
            )
        if not isinstance(self.execution_descriptor, RuleIntentExecutionDescriptor):
            raise TypeError(
                f"execution_descriptor must be a RuleIntentExecutionDescriptor, got {type(self.execution_descriptor)}"
            )
        if not isinstance(self.recovery_model_kind, RecoveryModelKind):
            raise TypeError(
                f"recovery_model_kind must be a RecoveryModelKind, got {type(self.recovery_model_kind)}"
            )
        if not isinstance(self.source_skill_gate, PersistentSourceSkillGate):
            raise TypeError(
                f"source_skill_gate must be a PersistentSourceSkillGate, got {type(self.source_skill_gate)}"
            )


@dataclass(frozen=True, slots=True)
class RecoveryOpportunityResult:
    """Result of evaluating and potentially resolving a RecoveryOpportunity."""

    opportunity: RecoveryOpportunity
    resolution: RecoveryResult | None = None
    executed: bool = False
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class AbortedRuleIntentResult:
    """Result recorded when an intent is aborted or rejected by ExecutionRightSystem."""

    descriptor: RuleIntentExecutionDescriptor
    decision_kind: ExecutionRightDecisionKind
    reason: ExecutionRightReason


# Unified sibling RuleIntent representation
RuleIntent = Effect | RecoveryOpportunity

# Unified result outcome
RuleIntentResult = (
    EffectExecutionResult
    | RecoveryOpportunityResult
    | AbortedRuleIntentResult
)
