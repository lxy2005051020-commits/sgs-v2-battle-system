from __future__ import annotations

from .dependency_evaluation import ProviderNode, StateNode
from .equipment_effectiveness import (
    EquipmentContributionRef,
    EquipmentEffectivenessContribution,
    EquipmentEffectivenessPolicy,
)
from .official_state_catalog import OfficialStateId
from .provider_identity import SkillProviderRef
from .provider_validity import ProviderValidityPolicy, ProviderValidityStatus
from .skill_definition import SkillType
from .skill_runtime import SkillSlot
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


FALSE_REPORT_PROVIDER_SUPPRESSION_RULE_ID = (
    "690107_FALSE_REPORT_PROVIDER_SUPPRESSION"
)
FALSE_REPORT_PROVIDER_DEPENDENCY_RULE_ID = (
    "690107_FALSE_REPORT_PROVIDER_DEPENDENCY"
)
FALSE_REPORT_EQUAL_REAPPLICATION_RULE_ID = (
    "690107_FALSE_REPORT_EQUAL_REAPPLICATION_REJECT"
)
FALSE_REPORT_STRENGTH_BOUNDARY_RULE_ID = (
    "690107_FALSE_REPORT_STRENGTH_UNSUPPORTED"
)
FALSE_REPORT_ORDINARY_CLEANSE_RULE_ID = (
    "690107_FALSE_REPORT_TESTED_ORDINARY_CLEANSE"
)
FALSE_REPORT_EQUIPMENT_SUPPRESSION_RULE_ID = (
    "690107_FALSE_REPORT_TESTED_EQUIPMENT_SPECIAL_SUPPRESSION"
)
FALSE_REPORT_EQUIPMENT_BOUNDARY_RULE_ID = (
    "690107_FALSE_REPORT_EQUIPMENT_SPECIAL_UNSUPPORTED"
)

FALSE_REPORT_SUPPRESSED_SKILL_TYPES: frozenset[SkillType] = frozenset(
    {SkillType.PASSIVE, SkillType.COMMAND}
)

# Research-confirmed persistent Equipment Specials.  They remain equipment
# identities; they are deliberately not reclassified as PASSIVE/COMMAND.
FALSE_REPORT_TESTED_EQUIPMENT_SPECIAL_KEYS: frozenset[str] = frozenset(
    {
        "踩踏",
        "刚毅",
        "天公",
        "增气",
        "忍让",
        "躲闪",
        "祝福",
        "忠诚",
        "集智",
        "周旋",
    }
)

# The frozen contract explicitly records these nearby specials as observed only
# after their relevant effect had already been consumed/expired/completed.  They
# therefore provide a concrete UNSUPPORTED_BOUNDARY discriminator without
# turning every unrelated equipment contribution into an unknown special.
FALSE_REPORT_BOUNDED_EQUIPMENT_SPECIAL_KEYS: frozenset[str] = frozenset(
    {"灵动", "援助", "无双", "雄烈"}
)


def false_report_admission_adapter(_context, candidate: StateCandidate):
    """Reject only the unfrozen explicit strength dimension.

    Ordinary Insight is intentionally absent from this adapter.  Insight's own
    frozen protected set explicitly excludes FALSE_REPORT.
    """

    if candidate.state_id != OfficialStateId.FALSE_REPORT.value:
        return None
    if candidate.strength is None:
        return None
    return AdmissionDecision(
        AdmissionStatus.REJECT_UNSUPPORTED_BOUNDARY,
        FALSE_REPORT_STRENGTH_BOUNDARY_RULE_ID,
    )


def false_report_conflict_adapter(_context, candidate: StateCandidate, residents):
    """All admitted FALSE_REPORT instances use the standard equal-strength lane."""

    if candidate.state_id != OfficialStateId.FALSE_REPORT.value:
        return None
    if not residents:
        return None
    # Explicit numeric strength never reaches this point because admission marks
    # that stronger/weaker dimension unsupported.  Every supported resident is
    # therefore the frozen equal-strength case, independent of source identity.
    return StateConflictDecision(
        ApplicationDisposition.REJECT_CONFLICT,
        FALSE_REPORT_EQUAL_REAPPLICATION_RULE_ID,
        existing_instance_id=residents[0].instance_id,
    )


def false_report_application_dependency_adapter(
    context,
    candidate: StateCandidate,
    _residents,
    prospective_node: StateNode,
):
    """Bind target-owned PASSIVE/COMMAND providers to this FALSE_REPORT state.

    Edge direction is consumer -> prerequisite:
        ProviderNode(target provider) -> StateNode(FALSE_REPORT)
    This makes transitions propagate through the canonical dependency graph and
    keeps holder ownership separate from historical source attribution.
    """

    if candidate.state_id != OfficialStateId.FALSE_REPORT.value:
        return None

    additions: list[tuple[ProviderNode, StateNode]] = []
    for slot in SkillSlot:
        runtime = context.skill_runtimes.get(candidate.owner_id, slot)
        if runtime is None:
            continue
        if runtime.definition.skill_type not in FALSE_REPORT_SUPPRESSED_SKILL_TYPES:
            continue
        provider_ref = SkillProviderRef(
            owner_id=candidate.owner_id,
            skill_slot=slot,
            skill_id=runtime.definition.skill_id,
        )
        additions.append((ProviderNode(provider_ref), prospective_node))

    if not additions:
        return None
    return StateApplicationDependencyDelta(tuple(additions))


def make_false_report_provider_suppression_adapter(
    state_effectiveness_policy: StateEffectivenessPolicy,
):
    if not isinstance(state_effectiveness_policy, StateEffectivenessPolicy):
        raise TypeError("state_effectiveness_policy must be StateEffectivenessPolicy")

    def false_report_provider_suppression_adapter(context, provider_ref, session):
        if not isinstance(provider_ref, SkillProviderRef):
            return ()

        runtime = context.skill_runtimes.get(
            provider_ref.owner_id,
            provider_ref.skill_slot,
        )
        if runtime is None or runtime.definition.skill_id != provider_ref.skill_id:
            return ()
        if runtime.definition.skill_type not in FALSE_REPORT_SUPPRESSED_SKILL_TYPES:
            return ()

        causes: list[SuppressionCause] = []
        for prerequisite, decision in session.prerequisite_decisions(
            ProviderNode(provider_ref)
        ):
            if not isinstance(prerequisite, StateNode):
                continue
            if not context.states.has_instance(prerequisite.instance_id):
                continue
            false_report = context.states.get(prerequisite.instance_id)
            if false_report.state_id != OfficialStateId.FALSE_REPORT.value:
                continue
            if false_report.owner_id != provider_ref.owner_id:
                continue
            if decision.status is not StateEffectivenessStatus.EFFECTIVE:
                continue
            generation_id = false_report.current_generation_id
            if generation_id is None:
                raise RuntimeError(
                    "resident FALSE_REPORT must have application generation identity"
                )
            causes.append(
                SuppressionCause(
                    FALSE_REPORT_PROVIDER_SUPPRESSION_RULE_ID,
                    StateCauseRef(
                        false_report.instance_id,
                        generation_id,
                    ),
                )
            )
        return tuple(causes)

    return false_report_provider_suppression_adapter


def false_report_provider_dependency_effectiveness_adapter(
    context,
    instance,
    session,
):
    """Propagate only explicit ProviderDependency edges suppressed by FALSE_REPORT."""

    causes: list[SuppressionCause] = []
    for prerequisite, decision in session.prerequisite_decisions(
        StateNode(instance.instance_id)
    ):
        if not isinstance(prerequisite, ProviderNode):
            continue
        if decision.status is not ProviderValidityStatus.SUPPRESSED:
            continue
        if not any(
            cause.rule_id == FALSE_REPORT_PROVIDER_SUPPRESSION_RULE_ID
            for cause in decision.suppression_causes
        ):
            continue
        causes.append(
            SuppressionCause(
                FALSE_REPORT_PROVIDER_DEPENDENCY_RULE_ID,
                ProviderCauseRef(prerequisite.provider_ref),
            )
        )
    return StateEffectivenessContribution(suppression_causes=tuple(causes))


def _equipment_special_key(contribution_ref: EquipmentContributionRef) -> str | None:
    for value in (
        contribution_ref.provider_ref.provider_key,
        contribution_ref.contribution_key,
    ):
        if value in FALSE_REPORT_TESTED_EQUIPMENT_SPECIAL_KEYS:
            return value
        if value in FALSE_REPORT_BOUNDED_EQUIPMENT_SPECIAL_KEYS:
            return value
    return None


def make_false_report_equipment_effectiveness_adapter(
    state_effectiveness_policy: StateEffectivenessPolicy,
):
    if not isinstance(state_effectiveness_policy, StateEffectivenessPolicy):
        raise TypeError("state_effectiveness_policy must be StateEffectivenessPolicy")

    def false_report_equipment_effectiveness_adapter(
        context,
        contribution_ref: EquipmentContributionRef,
    ):
        if not isinstance(contribution_ref, EquipmentContributionRef):
            raise TypeError("contribution_ref must be EquipmentContributionRef")

        false_reports = state_effectiveness_policy.effective_instances(
            context,
            contribution_ref.provider_ref.owner_id,
            OfficialStateId.FALSE_REPORT.value,
        )
        if not false_reports:
            return None

        key = _equipment_special_key(contribution_ref)
        if key in FALSE_REPORT_BOUNDED_EQUIPMENT_SPECIAL_KEYS:
            return EquipmentEffectivenessContribution(unsupported_boundary=True)
        if key not in FALSE_REPORT_TESTED_EQUIPMENT_SPECIAL_KEYS:
            # No typed "Equipment Special" classifier exists in the Shared
            # Foundation.  Unknown unrelated equipment contributions are left to
            # their own owners rather than being silently generalized by FR.
            return None

        causes_list: list[SuppressionCause] = []
        for item in false_reports:
            generation_id = item.current_generation_id
            if generation_id is None:
                raise RuntimeError(
                    "resident FALSE_REPORT must have application generation identity"
                )
            causes_list.append(
                SuppressionCause(
                    FALSE_REPORT_EQUIPMENT_SUPPRESSION_RULE_ID,
                    StateCauseRef(item.instance_id, generation_id),
                )
            )
        causes = tuple(causes_list)
        return EquipmentEffectivenessContribution(suppression_causes=causes)

    return false_report_equipment_effectiveness_adapter


def false_report_removal_adapter(_context, operation, state_instance):
    if state_instance.state_id != OfficialStateId.FALSE_REPORT.value:
        return None
    if operation is RemovalOperation.ORDINARY_CLEANSE:
        return RemovalDecision(
            RemovalDecisionStatus.ALLOW,
            operation,
            FALSE_REPORT_ORDINARY_CLEANSE_RULE_ID,
        )
    if operation in (
        RemovalOperation.SPECIALIZED_CLEANSE,
        RemovalOperation.SCRIPTED_GAMEPLAY_REMOVE,
    ):
        return RemovalDecision(
            RemovalDecisionStatus.UNSUPPORTED_BOUNDARY,
            operation,
            "690107_FALSE_REPORT_REMOVAL_UNSUPPORTED_BOUNDARY",
        )
    return None


def register_false_report_integration(
    *,
    state_admission_policy,
    state_conflict_policy,
    state_effectiveness_policy: StateEffectivenessPolicy,
    provider_validity_policy: ProviderValidityPolicy,
    equipment_effectiveness_policy: EquipmentEffectivenessPolicy,
    state_application_coordinator,
    state_removal_policy: StateRemovalPolicy,
) -> None:
    """Install 690107 adapters into the canonical Stage12 owner graph."""

    if not isinstance(state_effectiveness_policy, StateEffectivenessPolicy):
        raise TypeError("state_effectiveness_policy must be StateEffectivenessPolicy")
    if not isinstance(provider_validity_policy, ProviderValidityPolicy):
        raise TypeError("provider_validity_policy must be ProviderValidityPolicy")
    if not isinstance(equipment_effectiveness_policy, EquipmentEffectivenessPolicy):
        raise TypeError("equipment_effectiveness_policy must be EquipmentEffectivenessPolicy")
    if not isinstance(state_removal_policy, StateRemovalPolicy):
        raise TypeError("state_removal_policy must be StateRemovalPolicy")

    state_admission_policy.register_rule_adapter(false_report_admission_adapter)
    state_conflict_policy.register_rule_adapter(false_report_conflict_adapter)
    state_application_coordinator.register_dependency_rule_adapter(
        false_report_application_dependency_adapter
    )
    provider_validity_policy.register_rule_adapter(
        make_false_report_provider_suppression_adapter(state_effectiveness_policy)
    )
    state_effectiveness_policy.register_rule_adapter(
        false_report_provider_dependency_effectiveness_adapter
    )
    equipment_effectiveness_policy.register_rule_adapter(
        make_false_report_equipment_effectiveness_adapter(
            state_effectiveness_policy
        )
    )
    state_removal_policy.register_rule_adapter(false_report_removal_adapter)
