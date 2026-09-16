from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TYPE_CHECKING

from .damage_aftermath_port import DamageAftermathFact
from .effects import Effect, EffectSourceRef
from .recovery_system import RecoveryResult
from .skill_runtime_registry import PersistentSourceSkillGate
from .stage10_state_params import RecoveryModelKind, RecoveryPotencyContext
from .state_generation import PersistentLifecycleWindow, StateApplicationGenerationId

if TYPE_CHECKING:
    from .effect_result import EffectExecutionResult


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
class ExecutionRightDecision:
    """Authoritative decision object returned by ExecutionRightSystem (STAGE10.md §4.2)."""

    decision_kind: ExecutionRightDecisionKind
    reason: ExecutionRightReason | None = None
    detail: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.decision_kind, ExecutionRightDecisionKind):
            raise TypeError(
                f"decision_kind must be an ExecutionRightDecisionKind, got {type(self.decision_kind)}"
            )
        if self.reason is not None and not isinstance(self.reason, ExecutionRightReason):
            raise TypeError(
                f"reason must be an ExecutionRightReason or None, got {type(self.reason)}"
            )

    @classmethod
    def allow(cls) -> ExecutionRightDecision:
        return cls(ExecutionRightDecisionKind.ALLOW)

    @classmethod
    def reject_current(
        cls, reason: ExecutionRightReason, detail: str | None = None
    ) -> ExecutionRightDecision:
        return cls(ExecutionRightDecisionKind.REJECT_CURRENT, reason=reason, detail=detail)

    @classmethod
    def abort_owner_state_remainder(
        cls, reason: ExecutionRightReason, detail: str | None = None
    ) -> ExecutionRightDecision:
        return cls(
            ExecutionRightDecisionKind.ABORT_OWNER_STATE_REMAINDER,
            reason=reason,
            detail=detail,
        )

    @classmethod
    def abort_hook(
        cls, reason: ExecutionRightReason, detail: str | None = None
    ) -> ExecutionRightDecision:
        return cls(ExecutionRightDecisionKind.ABORT_HOOK, reason=reason, detail=detail)


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
    lifecycle_window: PersistentLifecycleWindow | None = None
    aftermath_fact: DamageAftermathFact | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.opportunity_kind, RecoveryOpportunityKind):
            raise TypeError(
                f"opportunity_kind must be a RecoveryOpportunityKind, got {type(self.opportunity_kind)}"
            )
        if not isinstance(self.execution_descriptor, RuleIntentExecutionDescriptor):
            raise TypeError(
                f"execution_descriptor must be a RuleIntentExecutionDescriptor, got {type(self.execution_descriptor)}"
            )
        if isinstance(self.probability, bool) or not isinstance(self.probability, (int, float)):
            raise TypeError(f"probability must be a float, got {type(self.probability)}")
        if not (0.0 <= float(self.probability) <= 1.0):
            raise ValueError(f"probability must be in [0.0, 1.0], got {self.probability}")
        object.__setattr__(self, "probability", float(self.probability))

        if not isinstance(self.recovery_model_kind, RecoveryModelKind):
            raise TypeError(
                f"recovery_model_kind must be a RecoveryModelKind, got {type(self.recovery_model_kind)}"
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
        if self.lifecycle_window is not None and not isinstance(
            self.lifecycle_window, PersistentLifecycleWindow
        ):
            raise TypeError(
                f"lifecycle_window must be a PersistentLifecycleWindow or None, got {type(self.lifecycle_window)}"
            )
        if self.aftermath_fact is not None and not isinstance(
            self.aftermath_fact, DamageAftermathFact
        ):
            raise TypeError(
                f"aftermath_fact must be a DamageAftermathFact or None, got {type(self.aftermath_fact)}"
            )

        # S10-FG-H02 invariant check:
        if self.opportunity_kind == RecoveryOpportunityKind.RECUPERATION_ACTION_START:
            if self.aftermath_fact is not None:
                raise ValueError(
                    "S10-FG-H02 invariant violation: DamageAftermathFact must be None for RECUPERATION_ACTION_START"
                )


@dataclass(frozen=True, slots=True)
class RecoveryOpportunityResult:
    """Result of evaluating and potentially resolving a RecoveryOpportunity."""

    opportunity: RecoveryOpportunity
    resolution: RecoveryResult | None = None
    executed: bool = False
    reason: str | None = None

    @property
    def source_generation_id(self) -> StateApplicationGenerationId | None:
        if self.resolution is not None:
            return self.resolution.source_generation_id
        return self.opportunity.execution_descriptor.state_generation_id


@dataclass(frozen=True, slots=True)
class AbortedRuleIntentResult:
    """Result recorded when an intent is aborted or rejected by ExecutionRightSystem."""

    descriptor: RuleIntentExecutionDescriptor
    decision_kind: ExecutionRightDecisionKind
    reason: ExecutionRightReason
    intent: RuleIntent | None = None


# Unified sibling RuleIntent representation
RuleIntent = Effect | RecoveryOpportunity

# Unified result outcome
if TYPE_CHECKING:
    RuleIntentResult = (
        EffectExecutionResult
        | RecoveryOpportunityResult
        | AbortedRuleIntentResult
    )
else:
    RuleIntentResult = Any
