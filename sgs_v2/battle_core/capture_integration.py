from __future__ import annotations

from .dependency_evaluation import ProviderNode, StateNode
from .equipment_effectiveness import (
    EquipmentContributionKind,
    EquipmentContributionRef,
    EquipmentEffectivenessContribution,
    EquipmentEffectivenessPolicy,
)
from .execution_right_runtime import (
    CurrentActorPermissionDecision,
    CurrentActorPermissionPolicy,
    CurrentActorPermissionRequest,
    CurrentActorPermissionStatus,
    DamageWorkKind,
    RecoveryExecutionPreventionContribution,
    RecoveryExecutionPreventionPolicy,
)
from .official_state_catalog import OfficialStateId
from .provider_identity import SkillProviderRef
from .provider_validity import ProviderValidityPolicy, ProviderValidityStatus
from .skill_definition import SkillType
from .skill_runtime import SkillSlot
from .skill_target_policy import (
    SkillTargetPolicy,
    TargetPolicyBoundary,
    TargetPolicyContribution,
)
from .state_application import (
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
from .target_operation import (
    TargetCardinality,
    TargetOperation,
    TargetOperationDomain,
    TargetPurpose,
    TargetRelation,
)


CAPTURE_ACTOR_PERMISSION_RULE_ID = "690110_CAPTURE_CURRENT_ACTOR_PERMISSION"
CAPTURE_PROVIDER_SUPPRESSION_RULE_ID = "690110_CAPTURE_PROVIDER_SUPPRESSION"
CAPTURE_PROVIDER_DEPENDENCY_RULE_ID = "690110_CAPTURE_PROVIDER_DEPENDENCY"
CAPTURE_RECOVERY_PREVENTION_RULE_ID = "690110_CAPTURE_RECOVERY_ZERO"
CAPTURE_FRIENDLY_TARGET_RULE_ID = "690110_CAPTURE_FRIENDLY_TARGET_EXCLUSION"
CAPTURE_FRIENDLY_FIXED_ALL_BOUNDARY_RULE_ID = (
    "690110_CAPTURE_ALL_ALLIES_UNSUPPORTED"
)
CAPTURE_EQUIPMENT_ATTRIBUTE_RULE_ID = "690110_CAPTURE_EQUIPMENT_ATTRIBUTE"
CAPTURE_EQUIPMENT_NON_ATTRIBUTE_BOUNDARY_RULE_ID = (
    "690110_CAPTURE_EQUIPMENT_NON_ATTRIBUTE_UNSUPPORTED"
)
CAPTURE_REAPPLICATION_BOUNDARY_RULE_ID = (
    "690110_CAPTURE_REAPPLICATION_UNSUPPORTED"
)
CAPTURE_ORDINARY_CLEANSE_RULE_ID = "690110_CAPTURE_ORDINARY_CLEANSE_PROTECTED"
CAPTURE_REMOVAL_BOUNDARY_RULE_ID = "690110_CAPTURE_REMOVAL_UNSUPPORTED"

CAPTURE_SUPPRESSED_SKILL_TYPES: frozenset[SkillType] = frozenset(
    {SkillType.PASSIVE, SkillType.COMMAND}
)
CAPTURE_ACTOR_DENIED_OPERATION_KINDS: frozenset[str] = frozenset(
    {
        "NATURAL_ACTION",
        DamageWorkKind.NEW_ACTOR_DRIVEN_DAMAGE.value,
        DamageWorkKind.COUNTER_DAMAGE.value,
    }
)


def _effective_captures(
    policy: StateEffectivenessPolicy,
    context,
    owner_id: str,
):
    return policy.effective_instances(
        context,
        owner_id,
        OfficialStateId.CAPTURE.value,
    )


def _state_causes(instances, rule_id: str) -> tuple[SuppressionCause, ...]:
    causes: list[SuppressionCause] = []
    for instance in instances:
        generation_id = instance.current_generation_id
        if generation_id is None:
            raise RuntimeError(
                "resident CAPTURE must have application generation identity"
            )
        causes.append(
            SuppressionCause(
                rule_id,
                StateCauseRef(instance.instance_id, generation_id),
            )
        )
    return tuple(causes)


def capture_conflict_adapter(_context, candidate: StateCandidate, residents):
    """Keep Q70-Q74 explicit instead of inventing state-level stacking law."""

    if candidate.state_id != OfficialStateId.CAPTURE.value:
        return None
    if not residents:
        return None
    return StateConflictDecision(
        ApplicationDisposition.UNSUPPORTED_BOUNDARY,
        CAPTURE_REAPPLICATION_BOUNDARY_RULE_ID,
        existing_instance_id=residents[0].instance_id,
    )


def capture_application_dependency_adapter(
    context,
    candidate: StateCandidate,
    _residents,
    prospective_node: StateNode,
):
    """Bind loaded PASSIVE/COMMAND Providers to the resident Capture fact.

    The edge is dependency topology only. It never mutates SkillRuntime.enabled and
    never turns attribution metadata into a ProviderDependency.
    """

    if candidate.state_id != OfficialStateId.CAPTURE.value:
        return None

    additions: list[tuple[ProviderNode, StateNode]] = []
    for slot in SkillSlot:
        runtime = context.skill_runtimes.get(candidate.owner_id, slot)
        if runtime is None:
            continue
        if runtime.definition.skill_type not in CAPTURE_SUPPRESSED_SKILL_TYPES:
            continue
        additions.append(
            (
                ProviderNode(
                    SkillProviderRef(
                        candidate.owner_id,
                        slot,
                        runtime.definition.skill_id,
                    )
                ),
                prospective_node,
            )
        )

    if not additions:
        return None
    return StateApplicationDependencyDelta(tuple(additions))


def make_capture_actor_permission_adapter(
    state_effectiveness_policy: StateEffectivenessPolicy,
):
    """Deny only the frozen current-actor operation categories."""

    def capture_actor_permission_adapter(
        context,
        request: CurrentActorPermissionRequest,
    ):
        if request.operation_kind not in CAPTURE_ACTOR_DENIED_OPERATION_KINDS:
            return None
        captures = _effective_captures(
            state_effectiveness_policy,
            context,
            request.actor_id,
        )
        if not captures:
            return None
        return CurrentActorPermissionDecision(
            request,
            CurrentActorPermissionStatus.DENY,
            (CAPTURE_ACTOR_PERMISSION_RULE_ID,),
        )

    return capture_actor_permission_adapter


def make_capture_provider_suppression_adapter(
    state_effectiveness_policy: StateEffectivenessPolicy,
):
    """Suppress only explicitly Capture-bound PASSIVE/COMMAND Providers."""

    def capture_provider_suppression_adapter(context, provider_ref, session):
        if not isinstance(provider_ref, SkillProviderRef):
            return ()

        runtime = context.skill_runtimes.get(
            provider_ref.owner_id,
            provider_ref.skill_slot,
        )
        if runtime is None or runtime.definition.skill_id != provider_ref.skill_id:
            return ()
        if runtime.definition.skill_type not in CAPTURE_SUPPRESSED_SKILL_TYPES:
            return ()

        causes: list[SuppressionCause] = []
        for prerequisite, decision in session.prerequisite_decisions(
            ProviderNode(provider_ref)
        ):
            if not isinstance(prerequisite, StateNode):
                continue
            if not context.states.has_instance(prerequisite.instance_id):
                continue
            capture = context.states.get(prerequisite.instance_id)
            if capture.state_id != OfficialStateId.CAPTURE.value:
                continue
            if capture.owner_id != provider_ref.owner_id:
                continue
            if decision.status is not StateEffectivenessStatus.EFFECTIVE:
                continue
            generation_id = capture.current_generation_id
            if generation_id is None:
                raise RuntimeError(
                    "resident CAPTURE must have application generation identity"
                )
            causes.append(
                SuppressionCause(
                    CAPTURE_PROVIDER_SUPPRESSION_RULE_ID,
                    StateCauseRef(capture.instance_id, generation_id),
                )
            )
        return tuple(causes)

    return capture_provider_suppression_adapter


def capture_provider_dependency_effectiveness_adapter(
    _context,
    instance,
    session,
):
    """Propagate Capture only through explicit ProviderDependency edges."""

    causes: list[SuppressionCause] = []
    for prerequisite, decision in session.prerequisite_decisions(
        StateNode(instance.instance_id)
    ):
        if not isinstance(prerequisite, ProviderNode):
            continue
        if decision.status is not ProviderValidityStatus.SUPPRESSED:
            continue
        if not any(
            cause.rule_id == CAPTURE_PROVIDER_SUPPRESSION_RULE_ID
            for cause in decision.suppression_causes
        ):
            continue
        causes.append(
            SuppressionCause(
                CAPTURE_PROVIDER_DEPENDENCY_RULE_ID,
                ProviderCauseRef(prerequisite.provider_ref),
            )
        )
    return StateEffectivenessContribution(suppression_causes=tuple(causes))


def make_capture_recovery_prevention_adapter(
    state_effectiveness_policy: StateEffectivenessPolicy,
):
    def capture_recovery_prevention_adapter(context, request):
        if not _effective_captures(
            state_effectiveness_policy,
            context,
            request.target_id,
        ):
            return None
        return RecoveryExecutionPreventionContribution(
            CAPTURE_RECOVERY_PREVENTION_RULE_ID,
        )

    return capture_recovery_prevention_adapter


def make_capture_target_adapter(
    state_effectiveness_policy: StateEffectivenessPolicy,
):
    """Exclude captured holders only from fresh friendly SINGLE/CHOOSE_N queries."""

    def capture_target_adapter(
        context,
        operation: TargetOperation,
        raw_candidate_ids: tuple[str, ...],
    ):
        if operation.eligibility_context.domain is not TargetOperationDomain.SKILL:
            return None
        if operation.relation is not TargetRelation.ALLY:
            return None
        if operation.eligibility_context.purpose is not TargetPurpose.FRIENDLY_SUPPORT:
            return None

        captured_ids = tuple(
            candidate_id
            for candidate_id in raw_candidate_ids
            if _effective_captures(
                state_effectiveness_policy,
                context,
                candidate_id,
            )
        )
        if not captured_ids:
            return None

        if operation.cardinality is TargetCardinality.FIXED_ALL:
            return TargetPolicyContribution(
                boundary=TargetPolicyBoundary.UNSUPPORTED,
            )
        if operation.cardinality not in (
            TargetCardinality.SINGLE,
            TargetCardinality.CHOOSE_N,
        ):
            return None

        return TargetPolicyContribution(
            excluded_target_ids=captured_ids,
            preserve_cardinality=True,
        )

    return capture_target_adapter


def make_capture_equipment_effectiveness_adapter(
    state_effectiveness_policy: StateEffectivenessPolicy,
):
    """Implement ATTRIBUTE only; keep every other equipment category bounded."""

    def capture_equipment_effectiveness_adapter(
        context,
        contribution_ref: EquipmentContributionRef,
    ):
        captures = _effective_captures(
            state_effectiveness_policy,
            context,
            contribution_ref.provider_ref.owner_id,
        )
        if not captures:
            return None

        if contribution_ref.kind is not EquipmentContributionKind.ATTRIBUTE:
            return EquipmentEffectivenessContribution(
                unsupported_boundary=True,
            )

        return EquipmentEffectivenessContribution(
            suppression_causes=_state_causes(
                captures,
                CAPTURE_EQUIPMENT_ATTRIBUTE_RULE_ID,
            )
        )

    return capture_equipment_effectiveness_adapter


def capture_removal_adapter(_context, operation, state_instance):
    if state_instance.state_id != OfficialStateId.CAPTURE.value:
        return None
    if operation is RemovalOperation.ORDINARY_CLEANSE:
        return RemovalDecision(
            RemovalDecisionStatus.REJECT_CONTRACT_PROTECTED,
            operation,
            CAPTURE_ORDINARY_CLEANSE_RULE_ID,
        )
    if operation in (
        RemovalOperation.SPECIALIZED_CLEANSE,
        RemovalOperation.SCRIPTED_GAMEPLAY_REMOVE,
    ):
        return RemovalDecision(
            RemovalDecisionStatus.UNSUPPORTED_BOUNDARY,
            operation,
            CAPTURE_REMOVAL_BOUNDARY_RULE_ID,
        )
    return None


def register_capture_integration(
    *,
    state_conflict_policy,
    state_effectiveness_policy: StateEffectivenessPolicy,
    provider_validity_policy: ProviderValidityPolicy,
    current_actor_permission_policy: CurrentActorPermissionPolicy,
    recovery_execution_prevention_policy: RecoveryExecutionPreventionPolicy,
    skill_target_policy: SkillTargetPolicy,
    equipment_effectiveness_policy: EquipmentEffectivenessPolicy,
    state_application_coordinator,
    state_removal_policy: StateRemovalPolicy,
) -> None:
    """Install 690110 typed contributions into the canonical owner graph."""

    state_conflict_policy.register_rule_adapter(capture_conflict_adapter)
    state_application_coordinator.register_dependency_rule_adapter(
        capture_application_dependency_adapter
    )
    current_actor_permission_policy.register_rule_adapter(
        make_capture_actor_permission_adapter(state_effectiveness_policy)
    )
    provider_validity_policy.register_rule_adapter(
        make_capture_provider_suppression_adapter(state_effectiveness_policy)
    )
    state_effectiveness_policy.register_rule_adapter(
        capture_provider_dependency_effectiveness_adapter
    )
    recovery_execution_prevention_policy.register_rule_adapter(
        make_capture_recovery_prevention_adapter(state_effectiveness_policy)
    )
    skill_target_policy.register_rule_adapter(
        make_capture_target_adapter(state_effectiveness_policy)
    )
    equipment_effectiveness_policy.register_rule_adapter(
        make_capture_equipment_effectiveness_adapter(state_effectiveness_policy)
    )
    state_removal_policy.register_rule_adapter(capture_removal_adapter)
