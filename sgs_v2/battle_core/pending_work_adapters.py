"""Opt-in mechanism bridge; no automatic legacy tick migration."""
from dataclasses import asdict

from .pending_work import PendingWorkDispatchResult, freeze_payload
from .rule_intent import RecoveryOpportunity, RecoveryOpportunityKind


def recuperation_dispatcher(recovery_opportunity_system, opportunity: RecoveryOpportunity):
    """Preserve the frozen opportunity descriptor, admission, RNG and settlement."""
    if not isinstance(opportunity, RecoveryOpportunity):
        raise TypeError("opportunity must be RecoveryOpportunity")
    if opportunity.opportunity_kind is not RecoveryOpportunityKind.RECUPERATION_ACTION_START:
        raise ValueError("adapter only accepts existing Recuperation")

    def dispatch(context, frame):
        if frame.work.target_ref != opportunity.execution_descriptor.target_id:
            raise ValueError("work target differs from locked Recuperation target")
        expected = freeze_payload(asdict(opportunity.recovery_potency_context))
        if frame.snapshot.get("recovery_potency") != expected:
            raise ValueError("work must explicitly carry the frozen Recuperation potency")
        operation_id = context.id_allocator.allocate_recovery_operation_id()
        result = recovery_opportunity_system.execute(context, opportunity)
        return PendingWorkDispatchResult(operation_id, frame.lineage, result)

    return dispatch
