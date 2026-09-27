from __future__ import annotations

from .official_state_catalog import OfficialStateId
from .skill_target_policy import (
    SkillTargetPolicy,
    TargetPolicyBoundary,
    TargetPolicyContribution,
)
from .state_application import (
    ApplicationDisposition,
    StateConflictDecision,
)
from .state_effectiveness import StateEffectivenessPolicy
from .target_operation import (
    TargetCardinality,
    TargetOperation,
    TargetOperationDomain,
    TargetPurpose,
    TargetRelation,
)


PROVOCATION_TARGET_RULE_ID = "690108_PROVOCATION_REQUIRED_SOURCE"
PROVOCATION_REAPPLICATION_BOUNDARY_RULE_ID = (
    "690108_PROVOCATION_REAPPLICATION_UNSUPPORTED"
)
PROVOCATION_MULTISOURCE_BOUNDARY_RULE_ID = (
    "690108_PROVOCATION_MULTISOURCE_UNSUPPORTED"
)
PROVOCATION_CHOOSE_N_INSUFFICIENT_RULE_ID = (
    "690108_PROVOCATION_CHOOSE_N_INSUFFICIENT_UNSUPPORTED"
)

# Existing TargetEligibilityContext.restriction_keys is the frozen generic seam
# for operation-specific arbitration metadata. The presence of this key means
# Confusion owns the current target decision; Provocation must not add Source.
PROVOCATION_CONFUSION_PREEMPTION_KEY = "CONFUSION_CONTROLS_TARGET_DECISION"


def provocation_conflict_adapter(_context, candidate, residents):
    """Keep BU-P06 explicit instead of inventing reapplication/multi-source law."""

    if candidate.state_id != OfficialStateId.PROVOKE.value:
        return None
    if not residents:
        return None
    return StateConflictDecision(
        ApplicationDisposition.UNSUPPORTED_BOUNDARY,
        PROVOCATION_REAPPLICATION_BOUNDARY_RULE_ID,
        existing_instance_id=residents[0].instance_id,
    )


def make_provocation_target_adapter(
    state_effectiveness_policy: StateEffectivenessPolicy,
):
    """Build the zero-RNG, zero-event SkillTargetPolicy contribution.

    The adapter only constrains a fresh canonical Skill TargetOperation. Source
    legality remains owned by the operation-local candidate/exclusion pipeline.
    """

    if not isinstance(state_effectiveness_policy, StateEffectivenessPolicy):
        raise TypeError("state_effectiveness_policy must be StateEffectivenessPolicy")

    def provocation_target_adapter(
        context,
        operation: TargetOperation,
        raw_candidate_ids: tuple[str, ...],
    ) -> TargetPolicyContribution | None:
        if operation.eligibility_context.domain is not TargetOperationDomain.SKILL:
            return None
        if operation.relation is not TargetRelation.ENEMY:
            return None
        if operation.eligibility_context.purpose is not TargetPurpose.HOSTILE:
            return None

        active = state_effectiveness_policy.effective_instances(
            context,
            operation.actor_id,
            OfficialStateId.PROVOKE.value,
        )
        if not active:
            return None

        # Legacy/corrupt multi-resident snapshots remain an explicit BU-P06
        # boundary. Normal production application prevents creating this shape.
        if len(active) != 1:
            return TargetPolicyContribution(
                boundary=TargetPolicyBoundary.UNSUPPORTED,
            )

        if (
            PROVOCATION_CONFUSION_PREEMPTION_KEY
            in operation.eligibility_context.restriction_keys
            and state_effectiveness_policy.has_effective(
                context,
                operation.actor_id,
                OfficialStateId.CONFUSION.value,
            )
        ):
            return None

        provocation = active[0]
        source_id = provocation.source_id
        if source_id is None or source_id not in raw_candidate_ids:
            return None

        # FIXED_ALL already contains every legal eligible target. Provocation
        # must not collapse or mutate the set.
        if operation.cardinality is TargetCardinality.FIXED_ALL:
            return None

        if (
            operation.cardinality is TargetCardinality.CHOOSE_N
            and operation.requested_count is not None
            and len(raw_candidate_ids) < operation.requested_count
        ):
            return TargetPolicyContribution(
                boundary=TargetPolicyBoundary.UNSUPPORTED,
            )

        return TargetPolicyContribution(
            required_target_ids=(source_id,),
            preserve_cardinality=True,
        )

    return provocation_target_adapter


def register_provocation_integration(
    *,
    state_conflict_policy,
    state_effectiveness_policy: StateEffectivenessPolicy,
    skill_target_policy: SkillTargetPolicy,
) -> None:
    """Install 690108 into the canonical Stage12 owner graph."""

    if not isinstance(state_effectiveness_policy, StateEffectivenessPolicy):
        raise TypeError("state_effectiveness_policy must be StateEffectivenessPolicy")
    if not isinstance(skill_target_policy, SkillTargetPolicy):
        raise TypeError("skill_target_policy must be SkillTargetPolicy")

    state_conflict_policy.register_rule_adapter(provocation_conflict_adapter)
    skill_target_policy.register_rule_adapter(
        make_provocation_target_adapter(state_effectiveness_policy)
    )
