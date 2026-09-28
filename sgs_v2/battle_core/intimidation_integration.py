from __future__ import annotations

from .dependency_evaluation import (
    DependencyEvaluationSupport,
    DependencyNode,
    ProviderNode,
    StateNode,
)
from .effectiveness_transition import (
    EffectivenessTransitionCoordinator,
    ProviderValidityChanged,
)
from .equipment_effectiveness import (
    EquipmentContributionRegistry,
    EquipmentEffectivenessPolicy,
    EquipmentEffectivenessStatus,
)
from .official_state_catalog import OfficialStateId
from .preparation_interruption import (
    PreparationInterruptionPort,
    PreparationInterruptionRequest,
    PreparationInterruptionScope,
    PreparationInterruptionTransitionAdapter,
)
from .provider_identity import (
    EquipmentProviderRef,
    ProviderResolutionStatus,
    SkillProviderRef,
)
from .provider_validity import ProviderValidityPolicy, ProviderValidityStatus
from .skill_definition import PreparationMode, SkillType
from .skill_runtime import SkillSlot
from .state_application import (
    AdmissionDecision,
    AdmissionStatus,
    ApplicationDisposition,
    StateApplicationCommitAugmentation,
    StateApplicationCoordinator,
    StateCandidate,
    StateConflictDecision,
)
from .state_effectiveness import (
    ProviderCauseRef,
    StateCauseRef,
    StateEffectivenessContribution,
    StateEffectivenessPolicy,
    StateEffectivenessStatus,
    SuppressionCause,
)
from .state_removal import (
    RemovalDecision,
    RemovalDecisionStatus,
    RemovalOperation,
    StateRemovalPolicy,
)


INTIMIDATION_GANGYI_ADMISSION_RULE_ID = (
    "690222_INTIMIDATION_GANGYI_REJECTION"
)
INTIMIDATION_REFRESH_RULE_ID = "690222_INTIMIDATION_SAME_SOURCE_REFRESH"
INTIMIDATION_MULTISOURCE_BOUNDARY_RULE_ID = (
    "690222_INTIMIDATION_MULTISOURCE_UNSUPPORTED"
)
INTIMIDATION_EMPTY_POOL_BOUNDARY_RULE_ID = (
    "690222_INTIMIDATION_EMPTY_ELIGIBLE_POOL_UNSUPPORTED"
)
INTIMIDATION_PROVIDER_SUPPRESSION_RULE_ID = (
    "690222_INTIMIDATION_BOUND_PROVIDER_SUPPRESSION"
)
INTIMIDATION_SOURCE_PROVIDER_DEPENDENCY_RULE_ID = (
    "690222_INTIMIDATION_SOURCE_PROVIDER_DEPENDENCY"
)
INTIMIDATION_DEPENDENT_PROVIDER_RULE_ID = (
    "690222_INTIMIDATION_PROVIDER_DEPENDENCY"
)
INTIMIDATION_ORDINARY_CLEANSE_RULE_ID = (
    "690222_INTIMIDATION_TESTED_GENERIC_CLEANSE_REJECT"
)
INTIMIDATION_REMOVAL_BOUNDARY_RULE_ID = (
    "690222_INTIMIDATION_SPECIALIZED_REMOVAL_UNSUPPORTED"
)
INTIMIDATION_PREPARATION_INTERRUPTION_RULE_ID = (
    "690222_INTIMIDATION_PREPARATION_PROVIDER_INTERRUPTION"
)

INTIMIDATION_SUPPORTED_SKILL_TYPES: frozenset[SkillType] = frozenset(
    {
        SkillType.ACTIVE,
        SkillType.ASSAULT,
        SkillType.PASSIVE,
        SkillType.COMMAND,
        SkillType.TROOP,
    }
)


def intimidation_eligible_provider_pool(
    context,
    holder_id: str,
) -> tuple[SkillProviderRef, ...]:
    """Enumerate the frozen 690222 supported loaded Provider domain.

    PREPARATION_ACTIVE is represented by ACTIVE + PreparationMode.REQUIRED and
    is therefore included through SkillType.ACTIVE. ProviderValidity is
    deliberately not an eligibility filter: this is loaded identity selection.
    """

    providers: list[SkillProviderRef] = []
    for slot in SkillSlot:
        runtime = context.skill_runtimes.get(holder_id, slot)
        if runtime is None:
            continue
        if runtime.definition.skill_type not in INTIMIDATION_SUPPORTED_SKILL_TYPES:
            continue
        provider_ref = SkillProviderRef(
            owner_id=holder_id,
            skill_slot=slot,
            skill_id=runtime.definition.skill_id,
        )
        resolution = context.skill_runtimes.resolve_provider(provider_ref)
        if resolution.status is not ProviderResolutionStatus.FOUND:
            raise RuntimeError(
                "loaded SkillRuntime failed canonical Provider identity validation"
            )
        providers.append(provider_ref)

    return tuple(
        sorted(
            providers,
            key=lambda ref: (int(ref.skill_slot), ref.skill_id),
        )
    )


def _gangyi_is_effective(
    context,
    owner_id: str,
    *,
    equipment_contribution_registry: EquipmentContributionRegistry,
    equipment_effectiveness_policy: EquipmentEffectivenessPolicy,
) -> bool:
    provider_ref = EquipmentProviderRef(owner_id, "刚毅")
    record = equipment_contribution_registry.resolve_provider(context, provider_ref)
    if record is None or not record.enabled:
        return False

    matching = tuple(
        ref
        for ref in equipment_contribution_registry.known_contributions()
        if ref.provider_ref == provider_ref
        and (
            ref.contribution_key == "刚毅"
            or ref.provider_ref.provider_key == "刚毅"
        )
    )
    if not matching:
        # A registered enabled provider is already an explicit production fact;
        # contribution detail may be absent in minimal battle fixtures.
        return True

    return any(
        equipment_effectiveness_policy.evaluate_contribution(
            context, contribution_ref
        ).status
        is EquipmentEffectivenessStatus.EFFECTIVE
        for contribution_ref in matching
    )


def make_intimidation_admission_adapter(
    equipment_contribution_registry: EquipmentContributionRegistry,
    equipment_effectiveness_policy: EquipmentEffectivenessPolicy,
):
    def intimidation_admission_adapter(context, candidate: StateCandidate):
        if candidate.state_id != OfficialStateId.INTIMIDATION.value:
            return None
        if not _gangyi_is_effective(
            context,
            candidate.owner_id,
            equipment_contribution_registry=equipment_contribution_registry,
            equipment_effectiveness_policy=equipment_effectiveness_policy,
        ):
            return None
        return AdmissionDecision(
            AdmissionStatus.REJECT_SPECIAL_PROTECTION,
            INTIMIDATION_GANGYI_ADMISSION_RULE_ID,
            reason_provider_ref=EquipmentProviderRef(
                candidate.owner_id,
                "刚毅",
            ),
        )

    return intimidation_admission_adapter


def intimidation_conflict_adapter(_context, candidate: StateCandidate, residents):
    if candidate.state_id != OfficialStateId.INTIMIDATION.value:
        return None
    if not residents:
        return None
    if len(residents) != 1:
        return StateConflictDecision(
            ApplicationDisposition.UNSUPPORTED_BOUNDARY,
            INTIMIDATION_MULTISOURCE_BOUNDARY_RULE_ID,
            existing_instance_id=residents[0].instance_id,
        )

    existing = residents[0]
    same_source = (
        existing.source_id == candidate.source_id
        and existing.source_skill_id == candidate.source_skill_id
        and existing.source_skill_slot == candidate.source_skill_slot
    )
    if not same_source:
        return StateConflictDecision(
            ApplicationDisposition.UNSUPPORTED_BOUNDARY,
            INTIMIDATION_MULTISOURCE_BOUNDARY_RULE_ID,
            existing_instance_id=existing.instance_id,
        )
    return StateConflictDecision(
        ApplicationDisposition.REFRESH,
        INTIMIDATION_REFRESH_RULE_ID,
        existing_instance_id=existing.instance_id,
    )


def _merge_replacements(
    base,
    overlay,
) -> tuple[tuple[DependencyNode, tuple[DependencyNode, ...]], ...]:
    merged = {
        consumer: set(values)
        for consumer, values in base
    }
    for consumer, values in overlay:
        merged[consumer] = set(values)
    return tuple(
        (
            consumer,
            tuple(sorted(values, key=repr)),
        )
        for consumer, values in sorted(
            merged.items(), key=lambda item: repr(item[0])
        )
    )


def _binding_overlay(
    dependencies: DependencyEvaluationSupport,
    *,
    base_replacements,
    prospective_node: StateNode,
    old_provider_ref: SkillProviderRef | None,
    new_provider_ref: SkillProviderRef,
):
    base_map = {
        consumer: set(values)
        for consumer, values in base_replacements
    }
    overlay: dict[DependencyNode, set[DependencyNode]] = {}

    if old_provider_ref is not None:
        old_node = ProviderNode(old_provider_ref)
        old_values = set(
            base_map.get(
                old_node,
                dependencies.prerequisites(old_node),
            )
        )
        old_values.discard(prospective_node)
        overlay[old_node] = old_values

    new_node = ProviderNode(new_provider_ref)
    new_values = set(
        overlay.get(
            new_node,
            base_map.get(
                new_node,
                dependencies.prerequisites(new_node),
            ),
        )
    )
    new_values.add(prospective_node)
    overlay[new_node] = new_values

    return tuple(
        (
            consumer,
            tuple(sorted(values, key=repr)),
        )
        for consumer, values in sorted(
            overlay.items(), key=lambda item: repr(item[0])
        )
    )


def make_intimidation_commit_augmentation_adapter(
    dependencies: DependencyEvaluationSupport,
):
    """Resolve CREATE/REFRESH binding only after generic rejection prechecks.

    Every possible binding topology is cycle-validated before the first binding
    RNG draw. That preserves rejected/precommit-failure zero-RNG semantics while
    still committing the selected binding and dependency edge atomically.
    """

    def intimidation_commit_augmentation_adapter(
        context,
        candidate: StateCandidate,
        residents,
        prospective_node: StateNode,
        base_dependency_replacements,
        removed_nodes,
        disposition: ApplicationDisposition,
    ):
        if candidate.state_id != OfficialStateId.INTIMIDATION.value:
            return None
        if disposition not in (
            ApplicationDisposition.CREATE,
            ApplicationDisposition.REFRESH,
        ):
            return StateApplicationCommitAugmentation(
                unsupported_reason_rule_id=(
                    INTIMIDATION_MULTISOURCE_BOUNDARY_RULE_ID
                )
            )

        pool = intimidation_eligible_provider_pool(context, candidate.owner_id)
        if not pool:
            return StateApplicationCommitAugmentation(
                unsupported_reason_rule_id=(
                    INTIMIDATION_EMPTY_POOL_BOUNDARY_RULE_ID
                )
            )

        old_provider_ref: SkillProviderRef | None = None
        if disposition is ApplicationDisposition.REFRESH:
            if len(residents) != 1:
                return StateApplicationCommitAugmentation(
                    unsupported_reason_rule_id=(
                        INTIMIDATION_MULTISOURCE_BOUNDARY_RULE_ID
                    )
                )
            old_provider_ref = residents[0].bound_provider_ref
            if old_provider_ref is None:
                raise RuntimeError(
                    "resident INTIMIDATION has no canonical bound Provider identity"
                )

        # Preflight each reachable binding result before RNG. A dependency cycle
        # is a transaction failure, not an RNG-consuming failed application.
        overlays: dict[
            SkillProviderRef,
            tuple[tuple[DependencyNode, tuple[DependencyNode, ...]], ...],
        ] = {}
        for provider_ref in pool:
            overlay = _binding_overlay(
                dependencies,
                base_replacements=base_dependency_replacements,
                prospective_node=prospective_node,
                old_provider_ref=old_provider_ref,
                new_provider_ref=provider_ref,
            )
            trial = _merge_replacements(
                base_dependency_replacements,
                overlay,
            )
            dependencies.validate_dependency_replacements(
                trial,
                remove_nodes=removed_nodes,
            )
            overlays[provider_ref] = overlay

        if len(pool) == 1:
            selected = pool[0]
        else:
            selected = context.random.choice(pool)

        return StateApplicationCommitAugmentation(
            binding_payload=selected,
            dependency_replacements=overlays[selected],
        )

    return intimidation_commit_augmentation_adapter


def intimidation_provider_suppression_adapter(
    context,
    provider_ref,
    session,
):
    if not isinstance(provider_ref, SkillProviderRef):
        return ()

    causes: list[SuppressionCause] = []
    for prerequisite, decision in session.prerequisite_decisions(
        ProviderNode(provider_ref)
    ):
        if not isinstance(prerequisite, StateNode):
            continue
        if not context.states.has_instance(prerequisite.instance_id):
            continue
        state = context.states.get(prerequisite.instance_id)
        if state.state_id != OfficialStateId.INTIMIDATION.value:
            continue
        if state.owner_id != provider_ref.owner_id:
            continue
        if state.bound_provider_ref != provider_ref:
            continue
        if decision.status is not StateEffectivenessStatus.EFFECTIVE:
            continue
        generation_id = state.current_generation_id
        if generation_id is None:
            raise RuntimeError(
                "resident INTIMIDATION must have application generation identity"
            )
        causes.append(
            SuppressionCause(
                INTIMIDATION_PROVIDER_SUPPRESSION_RULE_ID,
                StateCauseRef(state.instance_id, generation_id),
            )
        )
    return tuple(causes)


def intimidation_state_effectiveness_adapter(context, instance, session):
    """Propagate only explicit ProviderDependency edges.

    For INTIMIDATION itself these are source-Provider dependencies. For other
    states they are explicit provider-owned behavior dependencies, such as a
    Provider-owned Insight or Provocation. Source attribution alone creates no
    edge and therefore cannot propagate suppression.
    """

    causes: list[SuppressionCause] = []
    for prerequisite, decision in session.prerequisite_decisions(
        StateNode(instance.instance_id)
    ):
        if not isinstance(prerequisite, ProviderNode):
            continue

        if instance.state_id == OfficialStateId.INTIMIDATION.value:
            if decision.status is ProviderValidityStatus.VALID:
                continue
            causes.append(
                SuppressionCause(
                    INTIMIDATION_SOURCE_PROVIDER_DEPENDENCY_RULE_ID,
                    ProviderCauseRef(prerequisite.provider_ref),
                )
            )
            continue

        if decision.status is not ProviderValidityStatus.SUPPRESSED:
            continue
        if not any(
            cause.rule_id == INTIMIDATION_PROVIDER_SUPPRESSION_RULE_ID
            for cause in decision.suppression_causes
        ):
            continue
        causes.append(
            SuppressionCause(
                INTIMIDATION_DEPENDENT_PROVIDER_RULE_ID,
                ProviderCauseRef(prerequisite.provider_ref),
            )
        )

    return StateEffectivenessContribution(
        suppression_causes=tuple(causes)
    )


def intimidation_preparation_transition_request(
    context,
    transition: ProviderValidityChanged,
) -> PreparationInterruptionRequest | None:
    if not isinstance(transition, ProviderValidityChanged):
        raise TypeError("transition must be ProviderValidityChanged")
    if transition.after.status is not ProviderValidityStatus.SUPPRESSED:
        return None
    if not any(
        cause.rule_id == INTIMIDATION_PROVIDER_SUPPRESSION_RULE_ID
        for cause in transition.after.suppression_causes
    ):
        return None

    provider_ref = transition.provider_node.provider_ref
    if not isinstance(provider_ref, SkillProviderRef):
        return None
    resolution = context.skill_runtimes.resolve_provider(provider_ref)
    if resolution.status is not ProviderResolutionStatus.FOUND:
        return None
    runtime = resolution.runtime
    assert runtime is not None
    if runtime.definition.skill_type is not SkillType.ACTIVE:
        return None
    if runtime.definition.preparation_mode is not PreparationMode.REQUIRED:
        return None

    return PreparationInterruptionRequest(
        scope=PreparationInterruptionScope.PROVIDER,
        holder_id=provider_ref.owner_id,
        provider_ref=provider_ref,
        cause_key=INTIMIDATION_PREPARATION_INTERRUPTION_RULE_ID,
    )


def intimidation_removal_adapter(_context, operation, state_instance):
    if state_instance.state_id != OfficialStateId.INTIMIDATION.value:
        return None
    if operation is RemovalOperation.ORDINARY_CLEANSE:
        return RemovalDecision(
            RemovalDecisionStatus.REJECT_CONTRACT_PROTECTED,
            operation,
            INTIMIDATION_ORDINARY_CLEANSE_RULE_ID,
        )
    if operation in (
        RemovalOperation.SPECIALIZED_CLEANSE,
        RemovalOperation.SCRIPTED_GAMEPLAY_REMOVE,
    ):
        return RemovalDecision(
            RemovalDecisionStatus.UNSUPPORTED_BOUNDARY,
            operation,
            INTIMIDATION_REMOVAL_BOUNDARY_RULE_ID,
        )
    return None


def register_intimidation_integration(
    *,
    state_admission_policy,
    state_conflict_policy,
    state_effectiveness_policy: StateEffectivenessPolicy,
    provider_validity_policy: ProviderValidityPolicy,
    state_application_coordinator: StateApplicationCoordinator,
    state_removal_policy: StateRemovalPolicy,
    effectiveness_transition_coordinator: EffectivenessTransitionCoordinator,
    preparation_interruption_port: PreparationInterruptionPort,
    equipment_contribution_registry: EquipmentContributionRegistry,
    equipment_effectiveness_policy: EquipmentEffectivenessPolicy,
    dependencies: DependencyEvaluationSupport,
) -> PreparationInterruptionTransitionAdapter:
    """Install 690222 adapters into canonical Shared Foundation owners."""

    state_admission_policy.register_rule_adapter(
        make_intimidation_admission_adapter(
            equipment_contribution_registry,
            equipment_effectiveness_policy,
        )
    )
    state_conflict_policy.register_rule_adapter(
        intimidation_conflict_adapter
    )
    state_effectiveness_policy.register_rule_adapter(
        intimidation_state_effectiveness_adapter
    )
    provider_validity_policy.register_rule_adapter(
        intimidation_provider_suppression_adapter
    )
    state_application_coordinator.register_commit_augmentation_adapter(
        make_intimidation_commit_augmentation_adapter(dependencies)
    )
    state_removal_policy.register_rule_adapter(
        intimidation_removal_adapter
    )

    transition_adapter = PreparationInterruptionTransitionAdapter(
        preparation_interruption_port,
        provider_request_factory=(
            intimidation_preparation_transition_request
        ),
    )
    transition_adapter.bind(effectiveness_transition_coordinator)
    return transition_adapter
