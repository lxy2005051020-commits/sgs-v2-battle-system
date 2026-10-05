"""Reusable state-backed immunity with admission and resident-effect readers."""
from dataclasses import dataclass

from .state_runtime_params import StateRuntimeParams
from .state_definition import StateDefinition
from .state_application import AdmissionDecision, AdmissionStatus
from .state_effectiveness import StateCauseRef, StateEffectivenessContribution, SuppressionCause
from .dependency_evaluation import ProviderNode
from .provider_identity import SkillProviderRef

SELECTIVE_IMMUNITY_STATE_ID = "runtime_selective_state_immunity"


@dataclass(frozen=True, slots=True)
class SelectiveStateImmunityParams(StateRuntimeParams):
    protected_state_ids: tuple[str, ...]

    def __post_init__(self):
        if not self.protected_state_ids or any(not isinstance(s, str) or not s for s in self.protected_state_ids):
            raise ValueError("immunity requires nonempty state ids")
        if SELECTIVE_IMMUNITY_STATE_ID in self.protected_state_ids:
            raise ValueError("immunity cannot protect itself")
        object.__setattr__(self, "protected_state_ids", tuple(self.protected_state_ids))


DEFINITION = StateDefinition(SELECTIVE_IMMUNITY_STATE_ID, "指定状态免疫",
    runtime_params_type=SelectiveStateImmunityParams)


def register_selective_immunity_definition(registry):
    try:
        resident = registry.get_definition(DEFINITION.state_id)
    except KeyError:
        registry.register_definition(DEFINITION)
    else:
        if resident != DEFINITION:
            raise ValueError("incompatible selective immunity schema")


def register_selective_immunity_support(admission, effectiveness):
    def protecting(context, owner_id, state_id):
        # Filter the protected dimension before querying provider dependencies.
        # Unrelated controls (e.g. provider intimidation) must never recurse into
        # the immunity state whose provider they govern.
        return tuple(s for s in context.states.find(owner_id=owner_id, state_id=SELECTIVE_IMMUNITY_STATE_ID)
            if state_id in s.runtime_params.protected_state_ids
            and (s.source_skill_slot is None or effectiveness.dependency_support.evaluate(context,
                ProviderNode(SkillProviderRef(s.source_id, s.source_skill_slot, s.source_skill_id))).valid)
            and effectiveness.evaluate_state(context, s).effective)

    def admit(context, candidate):
        if candidate.state_id == SELECTIVE_IMMUNITY_STATE_ID:
            return None
        markers = protecting(context, candidate.owner_id, candidate.state_id)
        if markers:
            return AdmissionDecision(AdmissionStatus.REJECT_IMMUNITY, "SELECTIVE_STATE_IMMUNITY",
                reason_state_instance_id=markers[0].instance_id)
        return None

    def evaluate(context, instance, session):
        # Also cover states installed through the legacy lifecycle ingress.
        if instance.state_id == SELECTIVE_IMMUNITY_STATE_ID:
            return StateEffectivenessContribution()
        markers = protecting(context, instance.owner_id, instance.state_id)
        return StateEffectivenessContribution(suppression_causes=tuple(
            SuppressionCause("SELECTIVE_STATE_IMMUNITY", StateCauseRef(s.instance_id, s.current_generation_id))
            for s in markers))

    admission.register_rule_adapter(admit)
    effectiveness.register_rule_adapter(evaluate)
