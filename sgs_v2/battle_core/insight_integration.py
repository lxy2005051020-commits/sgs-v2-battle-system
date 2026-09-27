from __future__ import annotations

from .dependency_evaluation import StateNode
from .official_state_catalog import OfficialStateId
from .state_application import (
    AdmissionDecision,
    AdmissionStatus,
    ApplicationDisposition,
    StateApplicationDependencyDelta,
    StateCandidate,
    StateConflictDecision,
)
from .state_effectiveness import (
    StateCauseRef,
    StateEffectivenessContribution,
    StateEffectivenessStatus,
    SuppressionCause,
)


INSIGHT_ADMISSION_RULE_ID = "690089_INSIGHT_PROTECTED_CONTROL_ADMISSION"
INSIGHT_SUPPRESSION_RULE_ID = "690089_INSIGHT_RESIDENT_CONTROL_SUPPRESSION"
INSIGHT_REAPPLICATION_RULE_ID = "PD_INS_002_PRESENT_INSIGHT_REJECTS_REAPPLICATION"


INSIGHT_PROTECTED_STATE_IDS: frozenset[str] = frozenset(
    {
        OfficialStateId.SILENCE.value,
        OfficialStateId.DISARM.value,
        OfficialStateId.CONFUSION.value,
        OfficialStateId.WEAKNESS.value,
        OfficialStateId.HEALING_BAN.value,
        OfficialStateId.TAUNT.value,
        OfficialStateId.PROVOKE.value,
        OfficialStateId.EQUIPMENT_DISABLE.value,
        OfficialStateId.STUN.value,
    }
)


INSIGHT_EXPLICIT_NON_PROTECTED_STATE_IDS: frozenset[str] = frozenset(
    {
        OfficialStateId.FALSE_REPORT.value,
        OfficialStateId.INTIMIDATION.value,
        OfficialStateId.CAPTURE.value,
    }
)


def make_insight_admission_adapter(state_effectiveness_policy):
    """Build the zero-RNG incoming protected-control admission adapter."""

    def insight_admission_adapter(context, candidate: StateCandidate):
        if candidate.state_id not in INSIGHT_PROTECTED_STATE_IDS:
            return None
        effective_insights = state_effectiveness_policy.effective_instances(
            context,
            candidate.owner_id,
            OfficialStateId.INSIGHT.value,
        )
        if not effective_insights:
            return None
        insight = effective_insights[0]
        return AdmissionDecision(
            AdmissionStatus.REJECT_SPECIAL_PROTECTION,
            INSIGHT_ADMISSION_RULE_ID,
            reason_state_instance_id=insight.instance_id,
        )

    return insight_admission_adapter


def insight_conflict_adapter(context, candidate: StateCandidate, residents):
    """PD-INS-002: any PRESENT canonical Insight rejects incoming Insight."""

    del context
    if candidate.state_id != OfficialStateId.INSIGHT.value:
        return None
    if not residents:
        return None
    return StateConflictDecision(
        ApplicationDisposition.REJECT_CONFLICT,
        INSIGHT_REAPPLICATION_RULE_ID,
        existing_instance_id=residents[0].instance_id,
    )


def insight_application_dependency_adapter(
    context,
    candidate: StateCandidate,
    residents,
    prospective_node: StateNode,
):
    """Bind protected controls to PRESENT Insight without making query-time scans.

    The edge direction is:
        protected StateNode -> Insight StateNode

    This is deliberately based on Insight residency, not current effectiveness.
    If Insight is currently suppressed, the binding remains so that a later
    SUPPRESSED -> EFFECTIVE transition can suppress the still-live control
    without reapplication or generation churn.
    """

    del residents
    additions: list[tuple[StateNode, StateNode]] = []

    if candidate.state_id == OfficialStateId.INSIGHT.value:
        for protected_id in sorted(INSIGHT_PROTECTED_STATE_IDS):
            for protected in context.states.find(
                owner_id=candidate.owner_id,
                state_id=protected_id,
            ):
                additions.append(
                    (StateNode(protected.instance_id), prospective_node)
                )
    elif candidate.state_id in INSIGHT_PROTECTED_STATE_IDS:
        for insight in context.states.find(
            owner_id=candidate.owner_id,
            state_id=OfficialStateId.INSIGHT.value,
        ):
            additions.append(
                (prospective_node, StateNode(insight.instance_id))
            )

    if not additions:
        return None
    return StateApplicationDependencyDelta(tuple(additions))


def insight_effectiveness_adapter(context, instance, session):
    """Contribute Insight suppression only through explicit state dependencies."""

    if instance.state_id not in INSIGHT_PROTECTED_STATE_IDS:
        return StateEffectivenessContribution()

    causes: list[SuppressionCause] = []
    for prerequisite, decision in session.prerequisite_decisions(
        StateNode(instance.instance_id)
    ):
        if not isinstance(prerequisite, StateNode):
            continue
        if not context.states.has_instance(prerequisite.instance_id):
            continue
        insight = context.states.get(prerequisite.instance_id)
        if insight.state_id != OfficialStateId.INSIGHT.value:
            continue
        if decision.status is not StateEffectivenessStatus.EFFECTIVE:
            continue
        if insight.current_generation_id is None:
            raise RuntimeError(
                "resident Insight must have application generation identity"
            )
        causes.append(
            SuppressionCause(
                INSIGHT_SUPPRESSION_RULE_ID,
                StateCauseRef(
                    insight.instance_id,
                    insight.current_generation_id,
                ),
            )
        )

    return StateEffectivenessContribution(
        suppression_causes=tuple(causes),
    )


def register_insight_integration(
    *,
    state_admission_policy,
    state_conflict_policy,
    state_effectiveness_policy,
    state_application_coordinator,
) -> None:
    """Install the 690089 adapters into the one canonical Shared Foundation graph."""

    state_admission_policy.register_rule_adapter(
        make_insight_admission_adapter(state_effectiveness_policy)
    )
    state_conflict_policy.register_rule_adapter(insight_conflict_adapter)
    state_effectiveness_policy.register_rule_adapter(
        insight_effectiveness_adapter
    )
    state_application_coordinator.register_dependency_rule_adapter(
        insight_application_dependency_adapter
    )
