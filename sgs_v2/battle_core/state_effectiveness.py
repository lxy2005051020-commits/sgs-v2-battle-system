from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, TypeAlias

from .dependency_evaluation import DependencyEvaluationSupport, StateNode, _EvaluationSession
from .provider_identity import EquipmentProviderRef, ProviderRef, SkillProviderRef
from .state_generation import StateApplicationGenerationId
from .state_instance import StateInstance


@dataclass(frozen=True, slots=True)
class StateCauseRef:
    state_instance_id: str
    application_generation_id: StateApplicationGenerationId

    def __post_init__(self) -> None:
        if not isinstance(self.state_instance_id, str) or not self.state_instance_id.strip():
            raise ValueError("state_instance_id cannot be empty or whitespace")
        if not isinstance(self.application_generation_id, StateApplicationGenerationId):
            raise TypeError("application_generation_id must be a StateApplicationGenerationId")


@dataclass(frozen=True, slots=True)
class ProviderCauseRef:
    provider_ref: ProviderRef

    def __post_init__(self) -> None:
        if not isinstance(self.provider_ref, (SkillProviderRef, EquipmentProviderRef)):
            raise TypeError("provider_ref must be a typed ProviderRef")


@dataclass(frozen=True, slots=True)
class LocalRuleCauseRef:
    subject_key: str

    def __post_init__(self) -> None:
        if not isinstance(self.subject_key, str) or not self.subject_key.strip():
            raise ValueError("subject_key cannot be empty or whitespace")


CauseRef: TypeAlias = StateCauseRef | ProviderCauseRef | LocalRuleCauseRef


@dataclass(frozen=True, slots=True)
class SuppressionCause:
    rule_id: str
    source_ref: CauseRef

    def __post_init__(self) -> None:
        if not isinstance(self.rule_id, str) or not self.rule_id.strip():
            raise ValueError("rule_id cannot be empty or whitespace")
        if not isinstance(self.source_ref, (StateCauseRef, ProviderCauseRef, LocalRuleCauseRef)):
            raise TypeError("source_ref must be a stable CauseRef")


@dataclass(frozen=True, slots=True)
class InactivityCause:
    rule_id: str
    source_ref: CauseRef

    def __post_init__(self) -> None:
        if not isinstance(self.rule_id, str) or not self.rule_id.strip():
            raise ValueError("rule_id cannot be empty or whitespace")
        if not isinstance(self.source_ref, (StateCauseRef, ProviderCauseRef, LocalRuleCauseRef)):
            raise TypeError("source_ref must be a stable CauseRef")


@dataclass(frozen=True, slots=True)
class StateEffectivenessContribution:
    suppression_causes: tuple[SuppressionCause, ...] = ()
    inactivity_causes: tuple[InactivityCause, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "suppression_causes", tuple(self.suppression_causes))
        object.__setattr__(self, "inactivity_causes", tuple(self.inactivity_causes))


class StateEffectivenessStatus(str, Enum):
    EFFECTIVE = "EFFECTIVE"
    SUPPRESSED = "SUPPRESSED"
    INACTIVE = "INACTIVE"


@dataclass(frozen=True, slots=True)
class StateEffectivenessDecision:
    state_instance_id: str
    application_generation_id: StateApplicationGenerationId
    status: StateEffectivenessStatus
    suppression_causes: tuple[SuppressionCause, ...] = ()
    inactivity_causes: tuple[InactivityCause, ...] = ()

    @property
    def effective(self) -> bool:
        return self.status is StateEffectivenessStatus.EFFECTIVE


StateEffectivenessRuleAdapter = Callable[
    [object, StateInstance, _EvaluationSession],
    StateEffectivenessContribution,
]


class StateEffectivenessPolicy:
    """Canonical production truth for resident state gameplay authority."""

    __slots__ = ("_dependencies", "_rule_adapters")

    def __init__(self, dependencies: DependencyEvaluationSupport) -> None:
        if not isinstance(dependencies, DependencyEvaluationSupport):
            raise TypeError("dependencies must be DependencyEvaluationSupport")
        self._dependencies = dependencies
        self._rule_adapters: list[StateEffectivenessRuleAdapter] = []

    @property
    def dependency_support(self) -> DependencyEvaluationSupport:
        return self._dependencies

    def register_rule_adapter(self, adapter: StateEffectivenessRuleAdapter) -> None:
        if not callable(adapter):
            raise TypeError("adapter must be callable")
        if adapter in self._rule_adapters:
            return
        self._rule_adapters.append(adapter)

    @staticmethod
    def _stable_unique(items):
        return tuple(sorted(set(items), key=repr))

    def evaluate_node(
        self,
        context,
        node,
        session: _EvaluationSession,
    ) -> StateEffectivenessDecision:
        if not isinstance(node, StateNode):
            raise TypeError("StateEffectivenessPolicy can only evaluate StateNode")
        instance = context.states.get(node.instance_id)

        suppression: list[SuppressionCause] = []
        inactivity: list[InactivityCause] = []
        for adapter in self._rule_adapters:
            contribution = adapter(context, instance, session)
            if not isinstance(contribution, StateEffectivenessContribution):
                raise TypeError("state effectiveness adapter returned invalid contribution")
            suppression.extend(contribution.suppression_causes)
            inactivity.extend(contribution.inactivity_causes)

        suppression_tuple = self._stable_unique(suppression)
        inactivity_tuple = self._stable_unique(inactivity)
        if inactivity_tuple:
            status = StateEffectivenessStatus.INACTIVE
        elif suppression_tuple:
            status = StateEffectivenessStatus.SUPPRESSED
        else:
            status = StateEffectivenessStatus.EFFECTIVE

        return StateEffectivenessDecision(
            state_instance_id=instance.instance_id,
            application_generation_id=instance.current_generation_id,
            status=status,
            suppression_causes=suppression_tuple,
            inactivity_causes=inactivity_tuple,
        )

    def evaluate_state(self, context, state_instance: StateInstance) -> StateEffectivenessDecision:
        if not isinstance(state_instance, StateInstance):
            raise TypeError("state_instance must be a StateInstance")
        if not context.states.has_instance(state_instance.instance_id):
            raise KeyError(f"state instance is not resident: {state_instance.instance_id}")
        return self._dependencies.evaluate(context, StateNode(state_instance.instance_id))

    def effective_instances(
        self,
        context,
        owner_id: str,
        state_id: str,
    ) -> tuple[StateInstance, ...]:
        instances = sorted(
            context.states.find(owner_id=owner_id, state_id=state_id),
            key=lambda item: item.instance_id,
        )
        return tuple(item for item in instances if self.evaluate_state(context, item).effective)

    def has_effective(self, context, owner_id: str, state_id: str) -> bool:
        return bool(self.effective_instances(context, owner_id, state_id))
