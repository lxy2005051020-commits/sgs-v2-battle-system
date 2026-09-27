from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, TypeAlias

from .dependency_evaluation import DependencyEvaluationSupport, DependencyNode, ProviderNode, StateNode
from .provider_validity import ProviderDependency
from .skill_runtime import SkillSlot
from .state_generation import StateApplicationGenerationId
from .state_instance import StateInstance
from .state_lifetime import StateLifetimeSpec
from .state_runtime_params import StateRuntimeParams, validate_state_runtime_params


class AdmissionStatus(str, Enum):
    ALLOW = "ALLOW"
    REJECT_IMMUNITY = "REJECT_IMMUNITY"
    REJECT_SPECIAL_PROTECTION = "REJECT_SPECIAL_PROTECTION"
    REJECT_INVALID_TARGET = "REJECT_INVALID_TARGET"
    REJECT_UNSUPPORTED_BOUNDARY = "REJECT_UNSUPPORTED_BOUNDARY"


@dataclass(frozen=True, slots=True)
class AdmissionDecision:
    status: AdmissionStatus
    reason_rule_id: str
    reason_state_instance_id: str | None = None
    reason_provider_ref: object | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.status, AdmissionStatus):
            raise TypeError("status must be AdmissionStatus")
        if not isinstance(self.reason_rule_id, str) or not self.reason_rule_id.strip():
            raise ValueError("reason_rule_id cannot be empty or whitespace")

    @property
    def allowed(self) -> bool:
        return self.status is AdmissionStatus.ALLOW


@dataclass(frozen=True, slots=True)
class StateCandidate:
    """Non-resident proposal for one state application.

    The candidate intentionally carries no physical instance identity and no
    application generation identity.
    """

    state_id: str
    owner_id: str
    runtime_params_candidate: StateRuntimeParams
    source_id: str | None = None
    source_skill_id: str | None = None
    source_skill_slot: SkillSlot | None = None
    lifetime_spec: StateLifetimeSpec | None = None
    strength: float | None = None
    priority: int | None = None
    provider_dependencies: tuple[ProviderDependency, ...] = ()
    application_provenance: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.state_id, str) or not self.state_id.strip():
            raise ValueError("state_id cannot be empty or whitespace")
        if not isinstance(self.owner_id, str) or not self.owner_id.strip():
            raise ValueError("owner_id cannot be empty or whitespace")
        if self.source_id is not None and (
            not isinstance(self.source_id, str) or not self.source_id.strip()
        ):
            raise ValueError("source_id cannot be empty or whitespace when provided")
        if self.source_skill_id is not None and (
            not isinstance(self.source_skill_id, str) or not self.source_skill_id.strip()
        ):
            raise ValueError("source_skill_id cannot be empty or whitespace when provided")
        if self.source_skill_slot is not None and not isinstance(
            self.source_skill_slot, SkillSlot
        ):
            raise TypeError("source_skill_slot must be SkillSlot or None")
        validate_state_runtime_params(self.runtime_params_candidate)
        if self.lifetime_spec is not None and not isinstance(
            self.lifetime_spec, StateLifetimeSpec
        ):
            raise TypeError("lifetime_spec must be StateLifetimeSpec or None")
        if self.strength is not None:
            if isinstance(self.strength, bool) or not isinstance(
                self.strength, (int, float)
            ):
                raise TypeError("strength must be numeric or None")
            object.__setattr__(self, "strength", float(self.strength))
        if self.priority is not None and (
            isinstance(self.priority, bool) or not isinstance(self.priority, int)
        ):
            raise TypeError("priority must be int or None")
        object.__setattr__(self, "provider_dependencies", tuple(self.provider_dependencies))
        for dependency in self.provider_dependencies:
            if not isinstance(dependency, ProviderDependency):
                raise TypeError("provider_dependencies must contain ProviderDependency")
        if self.application_provenance is not None and (
            not isinstance(self.application_provenance, str)
            or not self.application_provenance.strip()
        ):
            raise ValueError(
                "application_provenance cannot be empty or whitespace when provided"
            )


AdmissionRuleAdapter: TypeAlias = Callable[
    [object, StateCandidate],
    AdmissionDecision | None,
]


class StateAdmissionPolicy:
    """Pure target-side admission decision owner."""

    __slots__ = ("_rule_adapters",)

    def __init__(self) -> None:
        self._rule_adapters: list[AdmissionRuleAdapter] = []

    def register_rule_adapter(self, adapter: AdmissionRuleAdapter) -> None:
        if not callable(adapter):
            raise TypeError("adapter must be callable")
        if adapter not in self._rule_adapters:
            self._rule_adapters.append(adapter)

    def evaluate_candidate(self, context, candidate: StateCandidate) -> AdmissionDecision:
        if not isinstance(candidate, StateCandidate):
            raise TypeError("candidate must be StateCandidate")
        for adapter in self._rule_adapters:
            decision = adapter(context, candidate)
            if decision is None:
                continue
            if not isinstance(decision, AdmissionDecision):
                raise TypeError("admission adapter returned invalid decision")
            if not decision.allowed:
                return decision
        return AdmissionDecision(AdmissionStatus.ALLOW, "SF_ADMISSION_DEFAULT_ALLOW")


class ApplicationDisposition(str, Enum):
    CREATE = "CREATE"
    REFRESH = "REFRESH"
    REPLACE = "REPLACE"
    REJECT_CONFLICT = "REJECT_CONFLICT"
    UNSUPPORTED_BOUNDARY = "UNSUPPORTED_BOUNDARY"


@dataclass(frozen=True, slots=True)
class StateConflictDecision:
    disposition: ApplicationDisposition
    reason_rule_id: str
    existing_instance_id: str | None = None
    runtime_params_override: StateRuntimeParams | None = None
    lifetime_spec_override: StateLifetimeSpec | None = None
    binding_payload: object | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.disposition, ApplicationDisposition):
            raise TypeError("disposition must be ApplicationDisposition")
        if not isinstance(self.reason_rule_id, str) or not self.reason_rule_id.strip():
            raise ValueError("reason_rule_id cannot be empty or whitespace")
        if self.runtime_params_override is not None:
            validate_state_runtime_params(self.runtime_params_override)
        if self.lifetime_spec_override is not None and not isinstance(
            self.lifetime_spec_override, StateLifetimeSpec
        ):
            raise TypeError("lifetime_spec_override must be StateLifetimeSpec or None")


ConflictRuleAdapter: TypeAlias = Callable[
    [object, StateCandidate, tuple[StateInstance, ...]],
    StateConflictDecision | None,
]


@dataclass(frozen=True, slots=True)
class StateApplicationDependencyDelta:
    """Mechanism-owned dependency edges committed with one state application."""

    additions: tuple[tuple[DependencyNode, DependencyNode], ...] = ()

    def __post_init__(self) -> None:
        normalized = tuple(self.additions)
        for edge in normalized:
            if not isinstance(edge, tuple) or len(edge) != 2:
                raise TypeError("dependency additions must be (consumer, prerequisite) pairs")
            consumer, prerequisite = edge
            if not isinstance(consumer, (StateNode, ProviderNode)):
                raise TypeError("dependency consumer must be a DependencyNode")
            if not isinstance(prerequisite, (StateNode, ProviderNode)):
                raise TypeError("dependency prerequisite must be a DependencyNode")
        object.__setattr__(self, "additions", normalized)


ApplicationDependencyRuleAdapter: TypeAlias = Callable[
    [object, StateCandidate, tuple[StateInstance, ...], StateNode],
    StateApplicationDependencyDelta | None,
]


class StateConflictPolicy:
    """Pure post-admission state conflict decision owner."""

    __slots__ = ("_rule_adapters",)

    def __init__(self) -> None:
        self._rule_adapters: list[ConflictRuleAdapter] = []

    def register_rule_adapter(self, adapter: ConflictRuleAdapter) -> None:
        if not callable(adapter):
            raise TypeError("adapter must be callable")
        if adapter not in self._rule_adapters:
            self._rule_adapters.append(adapter)

    def evaluate_conflict(
        self,
        context,
        candidate: StateCandidate,
        resident_matches: tuple[StateInstance, ...],
    ) -> StateConflictDecision:
        if not isinstance(candidate, StateCandidate):
            raise TypeError("candidate must be StateCandidate")
        residents = tuple(sorted(tuple(resident_matches), key=lambda item: item.instance_id))
        if not residents:
            return StateConflictDecision(
                ApplicationDisposition.CREATE,
                "SF_CONFLICT_NO_RESIDENT_CREATE",
            )
        for adapter in self._rule_adapters:
            decision = adapter(context, candidate, residents)
            if decision is None:
                continue
            if not isinstance(decision, StateConflictDecision):
                raise TypeError("conflict adapter returned invalid decision")
            return decision
        return StateConflictDecision(
            ApplicationDisposition.UNSUPPORTED_BOUNDARY,
            "SF_CONFLICT_UNSUPPORTED_EXISTING_STATE",
        )


@dataclass(frozen=True, slots=True)
class StateApplicationTransaction:
    """Immutable, fully-authorized physical commit plan."""

    disposition: ApplicationDisposition
    candidate: StateCandidate
    new_generation_id: StateApplicationGenerationId
    final_runtime_params: StateRuntimeParams
    final_lifetime_spec: StateLifetimeSpec | None
    expected_resident_generations: tuple[
        tuple[str, StateApplicationGenerationId], ...
    ]
    dependency_prerequisites: tuple[DependencyNode, ...]
    expected_existing_instance_id: str | None = None
    expected_existing_generation_id: StateApplicationGenerationId | None = None
    planned_new_instance_id: str | None = None
    binding_payload: object | None = None

    def __post_init__(self) -> None:
        if self.disposition not in (
            ApplicationDisposition.CREATE,
            ApplicationDisposition.REFRESH,
            ApplicationDisposition.REPLACE,
        ):
            raise ValueError("transaction disposition must be a commit disposition")
        if not isinstance(self.candidate, StateCandidate):
            raise TypeError("candidate must be StateCandidate")
        if not isinstance(self.new_generation_id, StateApplicationGenerationId):
            raise TypeError("new_generation_id must be StateApplicationGenerationId")
        validate_state_runtime_params(self.final_runtime_params)
        if self.final_lifetime_spec is not None and not isinstance(
            self.final_lifetime_spec, StateLifetimeSpec
        ):
            raise TypeError("final_lifetime_spec must be StateLifetimeSpec or None")
        object.__setattr__(
            self, "expected_resident_generations", tuple(self.expected_resident_generations)
        )
        object.__setattr__(
            self, "dependency_prerequisites", tuple(self.dependency_prerequisites)
        )


class StateApplicationResultStatus(str, Enum):
    APPLIED = "APPLIED"
    REFRESHED = "REFRESHED"
    REPLACED = "REPLACED"
    REJECTED_ADMISSION = "REJECTED_ADMISSION"
    REJECTED_CONFLICT = "REJECTED_CONFLICT"
    UNSUPPORTED_BOUNDARY = "UNSUPPORTED_BOUNDARY"


@dataclass(frozen=True, slots=True)
class StateApplicationResult:
    status: StateApplicationResultStatus
    reason_rule_id: str
    instance: StateInstance | None = None
    admission_decision: AdmissionDecision | None = None
    conflict_decision: StateConflictDecision | None = None

    @property
    def committed(self) -> bool:
        return self.status in (
            StateApplicationResultStatus.APPLIED,
            StateApplicationResultStatus.REFRESHED,
            StateApplicationResultStatus.REPLACED,
        )


class StateTransactionPreconditionError(RuntimeError):
    pass


class StateApplicationCoordinator:
    """Canonical non-writing orchestrator for Shared Foundation state ingress."""

    __slots__ = (
        "_admission_policy",
        "_conflict_policy",
        "_lifecycle",
        "_dependencies",
        "_transition_coordinator",
        "_dependency_rule_adapters",
    )

    def __init__(
        self,
        *,
        admission_policy: StateAdmissionPolicy,
        conflict_policy: StateConflictPolicy,
        lifecycle,
        dependencies: DependencyEvaluationSupport,
        transition_coordinator=None,
    ) -> None:
        if not isinstance(admission_policy, StateAdmissionPolicy):
            raise TypeError("admission_policy must be StateAdmissionPolicy")
        if not isinstance(conflict_policy, StateConflictPolicy):
            raise TypeError("conflict_policy must be StateConflictPolicy")
        if not isinstance(dependencies, DependencyEvaluationSupport):
            raise TypeError("dependencies must be DependencyEvaluationSupport")
        self._admission_policy = admission_policy
        self._conflict_policy = conflict_policy
        self._lifecycle = lifecycle
        self._dependencies = dependencies
        self._transition_coordinator = transition_coordinator
        self._dependency_rule_adapters: list[ApplicationDependencyRuleAdapter] = []

    def register_dependency_rule_adapter(
        self,
        adapter: ApplicationDependencyRuleAdapter,
    ) -> None:
        if not callable(adapter):
            raise TypeError("dependency rule adapter must be callable")
        if adapter not in self._dependency_rule_adapters:
            self._dependency_rule_adapters.append(adapter)

    @property
    def admission_policy(self) -> StateAdmissionPolicy:
        return self._admission_policy

    @property
    def conflict_policy(self) -> StateConflictPolicy:
        return self._conflict_policy

    def _validate_candidate(self, context, candidate: StateCandidate) -> None:
        definition = context.states.get_definition(candidate.state_id)
        context.get_unit(candidate.owner_id)
        if candidate.source_id is not None:
            context.get_unit(candidate.source_id)
        if not isinstance(
            candidate.runtime_params_candidate, definition.runtime_params_type
        ):
            raise TypeError(
                "runtime_params type mismatch for state "
                f"{candidate.state_id}: expected {definition.runtime_params_type.__name__}, "
                f"got {type(candidate.runtime_params_candidate).__name__}"
            )

    @staticmethod
    def _resident_snapshot(
        residents: tuple[StateInstance, ...],
    ) -> tuple[tuple[str, StateApplicationGenerationId], ...]:
        return tuple(
            (instance.instance_id, instance.current_generation_id)
            for instance in sorted(residents, key=lambda item: item.instance_id)
        )

    def _assert_preconditions(
        self,
        context,
        *,
        candidate: StateCandidate,
        expected: tuple[tuple[str, StateApplicationGenerationId], ...],
        existing_instance_id: str | None,
        existing_generation_id: StateApplicationGenerationId | None,
    ) -> None:
        current = tuple(
            sorted(
                context.states.find(
                    owner_id=candidate.owner_id,
                    state_id=candidate.state_id,
                ),
                key=lambda item: item.instance_id,
            )
        )
        if self._resident_snapshot(current) != expected:
            raise StateTransactionPreconditionError(
                "resident state set changed before application commit"
            )
        if existing_instance_id is not None:
            if existing_instance_id not in context.states:
                raise StateTransactionPreconditionError(
                    "expected existing state disappeared before application commit"
                )
            existing = context.states.get(existing_instance_id)
            if existing.current_generation_id != existing_generation_id:
                raise StateTransactionPreconditionError(
                    "expected existing state generation changed before application commit"
                )

    @staticmethod
    def _dependency_prerequisites(
        candidate: StateCandidate,
    ) -> tuple[DependencyNode, ...]:
        return tuple(
            sorted(
                {ProviderNode(item.provider_ref) for item in candidate.provider_dependencies},
                key=repr,
            )
        )

    def _dependency_replacements(
        self,
        context,
        *,
        candidate: StateCandidate,
        residents: tuple[StateInstance, ...],
        prospective_node: StateNode,
        candidate_prerequisites: tuple[DependencyNode, ...],
    ) -> tuple[tuple[DependencyNode, tuple[DependencyNode, ...]], ...]:
        replacement_map: dict[DependencyNode, set[DependencyNode]] = {
            prospective_node: set(candidate_prerequisites)
        }
        for adapter in self._dependency_rule_adapters:
            delta = adapter(context, candidate, residents, prospective_node)
            if delta is None:
                continue
            if not isinstance(delta, StateApplicationDependencyDelta):
                raise TypeError("application dependency adapter returned invalid delta")
            for consumer, prerequisite in delta.additions:
                if consumer not in replacement_map:
                    replacement_map[consumer] = set(
                        self._dependencies.prerequisites(consumer)
                    )
                replacement_map[consumer].add(prerequisite)
        return tuple(
            (
                consumer,
                tuple(sorted(prerequisites, key=repr)),
            )
            for consumer, prerequisites in sorted(
                replacement_map.items(), key=lambda item: repr(item[0])
            )
        )

    def apply_candidate(
        self,
        context,
        candidate: StateCandidate,
    ) -> StateApplicationResult:
        self._validate_candidate(context, candidate)

        admission = self._admission_policy.evaluate_candidate(context, candidate)
        if admission.status is AdmissionStatus.REJECT_UNSUPPORTED_BOUNDARY:
            return StateApplicationResult(
                StateApplicationResultStatus.UNSUPPORTED_BOUNDARY,
                admission.reason_rule_id,
                admission_decision=admission,
            )
        if not admission.allowed:
            return StateApplicationResult(
                StateApplicationResultStatus.REJECTED_ADMISSION,
                admission.reason_rule_id,
                admission_decision=admission,
            )

        residents = tuple(
            sorted(
                context.states.find(
                    owner_id=candidate.owner_id,
                    state_id=candidate.state_id,
                ),
                key=lambda item: item.instance_id,
            )
        )
        conflict = self._conflict_policy.evaluate_conflict(
            context, candidate, residents
        )
        if conflict.disposition is ApplicationDisposition.UNSUPPORTED_BOUNDARY:
            return StateApplicationResult(
                StateApplicationResultStatus.UNSUPPORTED_BOUNDARY,
                conflict.reason_rule_id,
                admission_decision=admission,
                conflict_decision=conflict,
            )
        if conflict.disposition is ApplicationDisposition.REJECT_CONFLICT:
            return StateApplicationResult(
                StateApplicationResultStatus.REJECTED_CONFLICT,
                conflict.reason_rule_id,
                admission_decision=admission,
                conflict_decision=conflict,
            )

        existing: StateInstance | None = None
        if conflict.disposition in (
            ApplicationDisposition.REFRESH,
            ApplicationDisposition.REPLACE,
        ):
            if conflict.existing_instance_id is None:
                raise StateTransactionPreconditionError(
                    "refresh/replace decision must identify the existing instance"
                )
            matches = [
                item
                for item in residents
                if item.instance_id == conflict.existing_instance_id
            ]
            if len(matches) != 1:
                raise StateTransactionPreconditionError(
                    "conflict decision referenced a non-resident instance"
                )
            existing = matches[0]

        expected_residents = self._resident_snapshot(residents)
        expected_existing_id = existing.instance_id if existing is not None else None
        expected_existing_generation = (
            existing.current_generation_id if existing is not None else None
        )
        final_params = (
            conflict.runtime_params_override
            if conflict.runtime_params_override is not None
            else candidate.runtime_params_candidate
        )
        final_lifetime = (
            conflict.lifetime_spec_override
            if conflict.lifetime_spec_override is not None
            else candidate.lifetime_spec
        )
        prerequisites = self._dependency_prerequisites(candidate)

        planned_new_instance_id: str | None = None
        if conflict.disposition in (
            ApplicationDisposition.CREATE,
            ApplicationDisposition.REPLACE,
        ):
            planned_new_instance_id = context.states.peek_next_instance_id()
            prospective_node = StateNode(planned_new_instance_id)
        else:
            assert existing is not None
            prospective_node = StateNode(existing.instance_id)

        removed_nodes: tuple[DependencyNode, ...] = ()
        if conflict.disposition is ApplicationDisposition.REPLACE:
            assert existing is not None
            removed_nodes = (StateNode(existing.instance_id),)

        dependency_replacements = self._dependency_replacements(
            context,
            candidate=candidate,
            residents=residents,
            prospective_node=prospective_node,
            candidate_prerequisites=prerequisites,
        )
        self._dependencies.validate_dependency_replacements(
            dependency_replacements,
            remove_nodes=removed_nodes,
        )
        self._assert_preconditions(
            context,
            candidate=candidate,
            expected=expected_residents,
            existing_instance_id=expected_existing_id,
            existing_generation_id=expected_existing_generation,
        )

        transition_snapshot = None
        transition_roots = tuple(
            sorted(
                {
                    prospective_node,
                    *removed_nodes,
                    *(
                        node
                        for consumer, dependency_values in dependency_replacements
                        for node in (consumer, *dependency_values)
                    ),
                },
                key=repr,
            )
        )
        if self._transition_coordinator is not None:
            transition_snapshot = self._transition_coordinator.capture(
                context,
                transition_roots,
            )

        allocator = getattr(context, "generation_allocator", None)
        if allocator is None:
            raise RuntimeError("BattleContext has no generation allocator")
        new_generation_id = allocator.allocate()

        transaction = StateApplicationTransaction(
            disposition=conflict.disposition,
            candidate=candidate,
            new_generation_id=new_generation_id,
            final_runtime_params=final_params,
            final_lifetime_spec=final_lifetime,
            expected_resident_generations=expected_residents,
            dependency_prerequisites=prerequisites,
            expected_existing_instance_id=expected_existing_id,
            expected_existing_generation_id=expected_existing_generation,
            planned_new_instance_id=planned_new_instance_id,
            binding_payload=conflict.binding_payload,
        )

        instance = self._lifecycle.commit_application_transaction(context, transaction)

        self._dependencies.replace_dependencies_many(
            dependency_replacements,
            remove_nodes=removed_nodes,
        )

        if self._transition_coordinator is not None and transition_snapshot is not None:
            self._transition_coordinator.settle(
                context,
                transition_snapshot,
                transition_roots,
            )

        status_map = {
            ApplicationDisposition.CREATE: StateApplicationResultStatus.APPLIED,
            ApplicationDisposition.REFRESH: StateApplicationResultStatus.REFRESHED,
            ApplicationDisposition.REPLACE: StateApplicationResultStatus.REPLACED,
        }
        return StateApplicationResult(
            status_map[conflict.disposition],
            conflict.reason_rule_id,
            instance=instance,
            admission_decision=admission,
            conflict_decision=conflict,
        )
