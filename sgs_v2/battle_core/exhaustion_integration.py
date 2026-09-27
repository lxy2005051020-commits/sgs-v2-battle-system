from __future__ import annotations

from .effectiveness_transition import EffectivenessTransitionCoordinator, StateEffectivenessChanged
from .official_state_catalog import OfficialStateId
from .preparation_interruption import (
    PreparationInterruptionPort,
    PreparationInterruptionRequest,
    PreparationInterruptionScope,
    PreparationInterruptionTransitionAdapter,
)
from .skill_definition import SkillType
from .skill_permission import (
    SkillOperationKind,
    SkillPermissionDecision,
    SkillPermissionPolicy,
    SkillPermissionRequest,
    SkillPermissionStatus,
)
from .state_effectiveness import StateEffectivenessPolicy, StateEffectivenessStatus


EXHAUSTION_PERMISSION_RULE_ID = "690101_EXHAUSTION_ACTIVE_PERMISSION"
EXHAUSTION_PREPARATION_INTERRUPTION_RULE_ID = (
    "690101_EXHAUSTION_PREPARATION_INTERRUPTION"
)


def make_exhaustion_permission_adapter(
    state_effectiveness_policy: StateEffectivenessPolicy,
):
    """Deny only NEW ACTIVE operations while EXHAUSTION is effective."""

    if not isinstance(state_effectiveness_policy, StateEffectivenessPolicy):
        raise TypeError("state_effectiveness_policy must be StateEffectivenessPolicy")

    def exhaustion_permission_adapter(
        context: object,
        request: SkillPermissionRequest,
    ) -> SkillPermissionDecision | None:
        if request.operation_kind is not SkillOperationKind.NEW_ADMISSION:
            return None
        if request.skill_type is not SkillType.ACTIVE:
            return None
        if not state_effectiveness_policy.has_effective(
            context,
            request.actor_id,
            OfficialStateId.SILENCE.value,
        ):
            return None
        return SkillPermissionDecision(
            request=request,
            status=SkillPermissionStatus.DENY_STATE_PERMISSION,
            blocker_keys=(EXHAUSTION_PERMISSION_RULE_ID,),
        )

    return exhaustion_permission_adapter


def exhaustion_preparation_transition_request(
    context: object,
    transition: StateEffectivenessChanged,
) -> PreparationInterruptionRequest | None:
    """Map a true resident EXHAUSTION resume to the canonical interruption port.

    This covers SUPPRESSED/INACTIVE -> EFFECTIVE transitions for an already
    resident EXHAUSTION instance. A first CREATE application has no
    ABSENT -> EFFECTIVE transition in the current Shared Foundation coordinator,
    so production completion remains blocked until a concrete PREPARING owner
    and first-application command seam exist.
    """

    if not isinstance(transition, StateEffectivenessChanged):
        raise TypeError("transition must be StateEffectivenessChanged")
    if transition.before.status is StateEffectivenessStatus.EFFECTIVE:
        return None
    if transition.after.status is not StateEffectivenessStatus.EFFECTIVE:
        return None
    if not context.states.has_instance(transition.state_instance_id):
        return None

    instance = context.states.get(transition.state_instance_id)
    if instance.state_id != OfficialStateId.SILENCE.value:
        return None

    return PreparationInterruptionRequest(
        scope=PreparationInterruptionScope.HOLDER_ACTIVE,
        holder_id=instance.owner_id,
        cause_key=EXHAUSTION_PREPARATION_INTERRUPTION_RULE_ID,
    )


def register_exhaustion_integration(
    *,
    state_effectiveness_policy: StateEffectivenessPolicy,
    skill_permission_policy: SkillPermissionPolicy,
    effectiveness_transition_coordinator: EffectivenessTransitionCoordinator,
    preparation_interruption_port: PreparationInterruptionPort,
) -> PreparationInterruptionTransitionAdapter:
    """Install 690101 into the one canonical Shared Foundation owner graph."""

    if not isinstance(skill_permission_policy, SkillPermissionPolicy):
        raise TypeError("skill_permission_policy must be SkillPermissionPolicy")
    if not isinstance(
        effectiveness_transition_coordinator,
        EffectivenessTransitionCoordinator,
    ):
        raise TypeError(
            "effectiveness_transition_coordinator must be "
            "EffectivenessTransitionCoordinator"
        )
    if not hasattr(preparation_interruption_port, "interrupt"):
        raise TypeError("preparation_interruption_port must implement interrupt")

    skill_permission_policy.register_rule_adapter(
        make_exhaustion_permission_adapter(state_effectiveness_policy)
    )

    transition_adapter = PreparationInterruptionTransitionAdapter(
        preparation_interruption_port,
        state_request_factory=exhaustion_preparation_transition_request,
    )
    transition_adapter.bind(effectiveness_transition_coordinator)
    return transition_adapter
