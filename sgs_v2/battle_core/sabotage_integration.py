from __future__ import annotations

from .dependency_evaluation import ProviderNode, StateNode
from .equipment_effectiveness import (
    EquipmentContributionRegistry,
    EquipmentEffectivenessPolicy,
    EquipmentEffectivenessStatus,
)
from .official_state_catalog import OfficialStateId
from .provider_identity import EquipmentProviderRef
from .provider_validity import ProviderValidityPolicy, ProviderValidityStatus
from .state_application import (
    AdmissionDecision,
    AdmissionStatus,
    ApplicationDisposition,
    StateApplicationDependencyDelta,
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


SABOTAGE_GANGYI_ADMISSION_RULE_ID = "690109_SABOTAGE_GANGYI_REJECTION"
SABOTAGE_STRENGTH_BOUNDARY_RULE_ID = "690109_SABOTAGE_STRENGTH_UNSUPPORTED"
SABOTAGE_EQUAL_REAPPLICATION_RULE_ID = "690109_SABOTAGE_EQUAL_REAPPLICATION_REJECT"
SABOTAGE_MULTISOURCE_BOUNDARY_RULE_ID = "690109_SABOTAGE_MULTISOURCE_UNSUPPORTED"
SABOTAGE_PROVIDER_SUPPRESSION_RULE_ID = "690109_SABOTAGE_EQUIPMENT_PROVIDER_SUPPRESSION"
SABOTAGE_PROVIDER_DEPENDENCY_RULE_ID = "690109_SABOTAGE_EQUIPMENT_PROVIDER_DEPENDENCY"
SABOTAGE_ORDINARY_CLEANSE_RULE_ID = "690109_SABOTAGE_OBSERVED_ORDINARY_CLEANSE"
SABOTAGE_REMOVAL_BOUNDARY_RULE_ID = "690109_SABOTAGE_REMOVAL_UNSUPPORTED_BOUNDARY"


def _gangyi_is_effective(
    context,
    owner_id: str,
    *,
    equipment_contribution_registry: EquipmentContributionRegistry,
    equipment_effectiveness_policy: EquipmentEffectivenessPolicy,
) -> bool:
    """Return the canonical effectiveness of the observed holder-level Gangyi provider."""

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
        # This mirrors the already-frozen 690222 Gangyi admission seam: an
        # explicitly registered enabled Gangyi provider is itself a production
        # fact even when a minimal fixture omits contribution detail.
        return True

    return any(
        equipment_effectiveness_policy.evaluate_contribution(
            context,
            contribution_ref,
        ).status
        is EquipmentEffectivenessStatus.EFFECTIVE
        for contribution_ref in matching
    )


def make_sabotage_admission_adapter(
    equipment_contribution_registry: EquipmentContributionRegistry,
    equipment_effectiveness_policy: EquipmentEffectivenessPolicy,
):
    """Install only frozen target-side admission boundaries.

    Effective Insight rejection is already owned by the canonical 690089
    admission adapter because EQUIPMENT_DISABLE belongs to its observed protected
    set.  This adapter therefore owns only Gangyi and the ungoverned numeric
    strength dimension.
    """

    def sabotage_admission_adapter(context, candidate: StateCandidate):
        if candidate.state_id != OfficialStateId.EQUIPMENT_DISABLE.value:
            return None

        # Research freezes the observed equal-or-stronger rejection but does not
        # freeze a numeric strength orientation or stronger/weaker replacement
        # mapping for StateCandidate.strength.
        if candidate.strength is not None:
            return AdmissionDecision(
                AdmissionStatus.REJECT_UNSUPPORTED_BOUNDARY,
                SABOTAGE_STRENGTH_BOUNDARY_RULE_ID,
            )

        if not _gangyi_is_effective(
            context,
            candidate.owner_id,
            equipment_contribution_registry=equipment_contribution_registry,
            equipment_effectiveness_policy=equipment_effectiveness_policy,
        ):
            return None

        return AdmissionDecision(
            AdmissionStatus.REJECT_SPECIAL_PROTECTION,
            SABOTAGE_GANGYI_ADMISSION_RULE_ID,
            reason_provider_ref=EquipmentProviderRef(candidate.owner_id, "刚毅"),
        )

    return sabotage_admission_adapter


def sabotage_conflict_adapter(_context, candidate: StateCandidate, residents):
    """Reject the frozen supported reapplication without refresh or replacement."""

    if candidate.state_id != OfficialStateId.EQUIPMENT_DISABLE.value:
        return None
    if not residents:
        return None
    if len(residents) != 1:
        return StateConflictDecision(
            ApplicationDisposition.UNSUPPORTED_BOUNDARY,
            SABOTAGE_MULTISOURCE_BOUNDARY_RULE_ID,
            existing_instance_id=residents[0].instance_id,
        )

    return StateConflictDecision(
        ApplicationDisposition.REJECT_CONFLICT,
        SABOTAGE_EQUAL_REAPPLICATION_RULE_ID,
        existing_instance_id=residents[0].instance_id,
    )


def make_sabotage_application_dependency_adapter(
    equipment_contribution_registry: EquipmentContributionRegistry,
):
    """Bind already-loaded target equipment Providers to the Sabotage state.

    Edge direction is:
        ProviderNode(target EquipmentProviderRef) -> StateNode(SABOTAGE)

    This does not infer dependencies from attribution.  Dynamic in-battle
    equipment creation/change remains the frozen B-SAB-09 boundary.
    """

    def sabotage_application_dependency_adapter(
        _context,
        candidate: StateCandidate,
        _residents,
        prospective_node: StateNode,
    ):
        if candidate.state_id != OfficialStateId.EQUIPMENT_DISABLE.value:
            return None

        provider_refs = {
            ref.provider_ref
            for ref in equipment_contribution_registry.known_contributions()
            if ref.provider_ref.owner_id == candidate.owner_id
        }
        if not provider_refs:
            return None

        additions = tuple(
            (ProviderNode(provider_ref), prospective_node)
            for provider_ref in sorted(provider_refs, key=repr)
        )
        return StateApplicationDependencyDelta(additions)

    return sabotage_application_dependency_adapter


def sabotage_provider_suppression_adapter(context, provider_ref, session):
    """Suppress target-owned equipment Providers only while Sabotage is effective."""

    if not isinstance(provider_ref, EquipmentProviderRef):
        return ()

    causes: list[SuppressionCause] = []
    for prerequisite, decision in session.prerequisite_decisions(
        ProviderNode(provider_ref)
    ):
        if not isinstance(prerequisite, StateNode):
            continue
        if not context.states.has_instance(prerequisite.instance_id):
            continue

        sabotage = context.states.get(prerequisite.instance_id)
        if sabotage.state_id != OfficialStateId.EQUIPMENT_DISABLE.value:
            continue
        if sabotage.owner_id != provider_ref.owner_id:
            continue
        if decision.status is not StateEffectivenessStatus.EFFECTIVE:
            continue

        generation_id = sabotage.current_generation_id
        if generation_id is None:
            raise RuntimeError(
                "resident SABOTAGE must have application generation identity"
            )
        causes.append(
            SuppressionCause(
                SABOTAGE_PROVIDER_SUPPRESSION_RULE_ID,
                StateCauseRef(sabotage.instance_id, generation_id),
            )
        )

    return tuple(causes)


def sabotage_provider_dependency_effectiveness_adapter(
    context,
    instance,
    session,
):
    """Propagate Sabotage only through explicit equipment Provider dependencies."""

    causes: list[SuppressionCause] = []
    for prerequisite, decision in session.prerequisite_decisions(
        StateNode(instance.instance_id)
    ):
        if not isinstance(prerequisite, ProviderNode):
            continue
        if not isinstance(prerequisite.provider_ref, EquipmentProviderRef):
            continue
        if decision.status is not ProviderValidityStatus.SUPPRESSED:
            continue
        if not any(
            cause.rule_id == SABOTAGE_PROVIDER_SUPPRESSION_RULE_ID
            for cause in decision.suppression_causes
        ):
            continue

        causes.append(
            SuppressionCause(
                SABOTAGE_PROVIDER_DEPENDENCY_RULE_ID,
                ProviderCauseRef(prerequisite.provider_ref),
            )
        )

    return StateEffectivenessContribution(
        suppression_causes=tuple(causes),
    )


def sabotage_removal_adapter(_context, operation, state_instance):
    if state_instance.state_id != OfficialStateId.EQUIPMENT_DISABLE.value:
        return None

    if operation is RemovalOperation.ORDINARY_CLEANSE:
        return RemovalDecision(
            RemovalDecisionStatus.ALLOW,
            operation,
            SABOTAGE_ORDINARY_CLEANSE_RULE_ID,
        )

    if operation in (
        RemovalOperation.SPECIALIZED_CLEANSE,
        RemovalOperation.SCRIPTED_GAMEPLAY_REMOVE,
    ):
        return RemovalDecision(
            RemovalDecisionStatus.UNSUPPORTED_BOUNDARY,
            operation,
            SABOTAGE_REMOVAL_BOUNDARY_RULE_ID,
        )

    # NATURAL_EXPIRY / OWNER_DEFEAT_CLEANUP / BATTLE_TEARDOWN are infrastructure
    # facts owned by StateRemovalPolicy before mechanism adapters are consulted.
    # No source-death special case is synthesized here.
    return None


def register_sabotage_integration(
    *,
    state_admission_policy,
    state_conflict_policy,
    state_effectiveness_policy: StateEffectivenessPolicy,
    provider_validity_policy: ProviderValidityPolicy,
    equipment_contribution_registry: EquipmentContributionRegistry,
    equipment_effectiveness_policy: EquipmentEffectivenessPolicy,
    state_application_coordinator,
    state_removal_policy: StateRemovalPolicy,
) -> None:
    """Install 690109 into the canonical Stage12 Shared Foundation graph."""

    if not isinstance(state_effectiveness_policy, StateEffectivenessPolicy):
        raise TypeError("state_effectiveness_policy must be StateEffectivenessPolicy")
    if not isinstance(provider_validity_policy, ProviderValidityPolicy):
        raise TypeError("provider_validity_policy must be ProviderValidityPolicy")
    if not isinstance(equipment_contribution_registry, EquipmentContributionRegistry):
        raise TypeError("equipment_contribution_registry must be EquipmentContributionRegistry")
    if not isinstance(equipment_effectiveness_policy, EquipmentEffectivenessPolicy):
        raise TypeError("equipment_effectiveness_policy must be EquipmentEffectivenessPolicy")
    if not isinstance(state_removal_policy, StateRemovalPolicy):
        raise TypeError("state_removal_policy must be StateRemovalPolicy")

    state_admission_policy.register_rule_adapter(
        make_sabotage_admission_adapter(
            equipment_contribution_registry,
            equipment_effectiveness_policy,
        )
    )
    state_conflict_policy.register_rule_adapter(
        sabotage_conflict_adapter
    )
    state_application_coordinator.register_dependency_rule_adapter(
        make_sabotage_application_dependency_adapter(
            equipment_contribution_registry
        )
    )
    provider_validity_policy.register_rule_adapter(
        sabotage_provider_suppression_adapter
    )
    state_effectiveness_policy.register_rule_adapter(
        sabotage_provider_dependency_effectiveness_adapter
    )
    state_removal_policy.register_rule_adapter(
        sabotage_removal_adapter
    )
