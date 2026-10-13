"""Opt-in selector priority with immutable query-bound direct-damage receipts.

The pure SkillTargetPolicy remains RNG-free. Selection delegates cardinality and
random tail choice to SkillResolver; EffectExecutor and damage owners are unchanged.
"""
from __future__ import annotations
from dataclasses import dataclass, fields
from contextvars import ContextVar
from typing import TYPE_CHECKING

from .additive_damage import FinalAdditiveDamageRequest
from .damage_probability import resolve_probability
from .damage_modifiers import (DamageModifierContribution, DamageModifierKind,
    DamageModifierOperation, DamageModifierPhase)
from .damage_rule_models import RuleContributionSource
from .damage_rule_provider import DamageRuleCollection
from .effects import DamageEffect
from .enums import DamageSourceType
from .numeric_validation import validate_probability, validate_finite_number
from .operation_identity import TargetOperationId
from .skill_runtime import SkillSlot
from .state_generation import StateApplicationGenerationId
from .skill_resolver import SkillResolver
from .state_definition import StateDefinition
from .state_runtime_params import StateRuntimeParams
from .target_operation import TargetRelation, TargetPurpose, TargetSelectorKind, TargetCardinality
if TYPE_CHECKING:
    from .context import BattleContext
    from .state_registry import StateRegistry

TARGET_PRIORITY_STATE_ID = "runtime_probabilistic_target_priority"


@dataclass(frozen=True, slots=True)
class TargetPriorityParams(StateRuntimeParams):
    probability: float
    reduction_base: float
    reduction_slope: float
    reduction_reference: float
    reduction_attribute: str = "defense"
    first_round: int = 1

    def __post_init__(self):
        object.__setattr__(self, "probability", validate_probability(self.probability))
        object.__setattr__(self, "reduction_base", validate_probability(self.reduction_base))
        for key in ("reduction_slope", "reduction_reference"):
            object.__setattr__(self, key, validate_finite_number(getattr(self, key), key))
        if self.reduction_attribute not in ("attack", "defense", "intelligence", "speed"):
            raise ValueError("unsupported live reduction attribute")
        if type(self.first_round) is not int or self.first_round < 0:
            raise ValueError("first_round must be a nonnegative integer")


DEFINITION = StateDefinition(TARGET_PRIORITY_STATE_ID, "概率战法目标优先",
                             runtime_params_type=TargetPriorityParams)


def register_target_priority_state(registry: StateRegistry) -> None:
    try:
        existing = registry.get_definition(TARGET_PRIORITY_STATE_ID)
    except KeyError:
        registry.register_definition(DEFINITION)
    else:
        if existing != DEFINITION:
            raise ValueError("incompatible target priority schema")


def target_priority_effectiveness_adapter(context, state, session):
    from .state_effectiveness import StateEffectivenessContribution, InactivityCause, LocalRuleCauseRef
    if state.state_id != TARGET_PRIORITY_STATE_ID:
        return StateEffectivenessContribution()
    runtime = context.skill_runtimes.get(state.source_id, state.source_skill_slot)
    provider = context.units.get(state.source_id)
    if (runtime is None or not runtime.enabled or runtime.definition.skill_id != state.source_skill_id
            or provider is None or not provider.is_alive
            or context.current_round < state.runtime_params.first_round
            or (state.expires_round is not None and context.current_round >= state.expires_round)):
        return StateEffectivenessContribution(inactivity_causes=(InactivityCause(
            "TARGET_PRIORITY_PROVIDER_UNAVAILABLE", LocalRuleCauseRef(state.instance_id)),))
    return StateEffectivenessContribution()


@dataclass(frozen=True, slots=True)
class TargetPriorityReceipt:
    operation_id: TargetOperationId
    source_id: str
    source_skill_id: str
    source_skill_slot: SkillSlot
    target_id: str
    priority_state_instance_id: str
    priority_generation_id: StateApplicationGenerationId
    round_no: int
    context_scope: int


@dataclass(frozen=True, slots=True)
class QueryBoundDamageRequest(FinalAdditiveDamageRequest):
    target_priority_receipt: TargetPriorityReceipt | None = None

    def __post_init__(self):
        FinalAdditiveDamageRequest.__post_init__(self)
        if self.target_priority_receipt is not None and not isinstance(self.target_priority_receipt, TargetPriorityReceipt):
            raise TypeError("target_priority_receipt must be TargetPriorityReceipt or None")


@dataclass(frozen=True, slots=True)
class QueryBoundDamageEffect(DamageEffect):
    target_priority_receipt: TargetPriorityReceipt | None = None

    def to_request(self) -> QueryBoundDamageRequest:
        ordinary = DamageEffect.to_request(self)
        values = {f.name: getattr(ordinary, f.name, 0.0) for f in fields(FinalAdditiveDamageRequest)}
        return QueryBoundDamageRequest(**values, target_priority_receipt=self.target_priority_receipt)


class TargetPrioritySkillResolver(SkillResolver):
    """Peripheral selector adapter; no policy, core resolver or engine replacement."""
    def __init__(self, *args, effectiveness_policy, **kwargs):
        super().__init__(*args, **kwargs)
        self._effectiveness = effectiveness_policy
        self._receipts = ContextVar("target_priority_receipts", default=())

    def resolve(self, *args, **kwargs):
        token = self._receipts.set(())
        try:
            return super().resolve(*args, **kwargs)
        finally:
            self._receipts.reset(token)

    def _select_policy_targets(self, context, operation, candidates, required_target_ids):
        if (operation.relation is not TargetRelation.ENEMY
                or operation.eligibility_context.purpose is not TargetPurpose.HOSTILE
                or operation.selector_kind is TargetSelectorKind.EXPLICIT
                or "CONFUSION_CONTROLS_TARGET_DECISION" in operation.eligibility_context.restriction_keys):
            return super()._select_policy_targets(context, operation, candidates, required_target_ids)
        count = (1 if operation.cardinality is TargetCardinality.SINGLE else operation.requested_count)
        if (operation.cardinality is not TargetCardinality.FIXED_ALL
                and (len(candidates) < count or len(required_target_ids) > count)):
            # Canonical owner raises unsupported cardinality before any priority RNG.
            return super()._select_policy_targets(context, operation, candidates, required_target_ids)
        candidates_with_state = []
        for unit in candidates:
            for state in self._effectiveness.effective_instances(context, unit.unit_id, TARGET_PRIORITY_STATE_ID):
                candidates_with_state.append((unit, state))
        if not candidates_with_state:
            return super()._select_policy_targets(context, operation, candidates, required_target_ids)
        if len(candidates_with_state) != 1:
            raise ValueError("multiple target-priority sources require an arbitration contract")
        unit, state = candidates_with_state[0]
        if (operation.cardinality is not TargetCardinality.FIXED_ALL and unit.unit_id not in required_target_ids
                and len(required_target_ids) == count):
            return super()._select_policy_targets(context, operation, candidates, required_target_ids)
        params = state.runtime_params
        if not isinstance(params, TargetPriorityParams):
            raise TypeError("target priority requires typed params")
        success = resolve_probability(context, params.probability)
        required = required_target_ids
        if success:
            if unit.unit_id not in required and operation.cardinality is not TargetCardinality.FIXED_ALL:
                required = required + (unit.unit_id,)
            self._receipts.set((TargetPriorityReceipt(operation.operation_id, operation.actor_id,
                operation.producer_ref.skill_id, operation.producer_ref.skill_slot, unit.unit_id,
                state.instance_id, state.current_generation_id, context.current_round, id(context)),))
        context.metadata.setdefault("target_priority_history", []).append({
            "operation_id": str(operation.operation_id), "actor_id": operation.actor_id,
            "source_skill_id": operation.producer_ref.skill_id, "round": context.current_round,
            "priority_target_id": unit.unit_id, "success": success,
            "priority_state_instance_id": state.instance_id})
        return super()._select_policy_targets(context, operation, candidates, required)

    def _build_effect(self, *, context, runtime, target, spec):
        effect = super()._build_effect(context=context, runtime=runtime, target=target, spec=spec)
        if not isinstance(effect, DamageEffect):
            return effect
        receipts = [r for r in self._receipts.get() if (r.source_id, r.source_skill_id, r.source_skill_slot,
            r.target_id) == (runtime.owner_id, runtime.definition.skill_id, runtime.skill_slot, target.unit_id)]
        if not receipts:
            return effect
        return QueryBoundDamageEffect(**{f.name: getattr(effect, f.name) for f in fields(DamageEffect)},
                                     target_priority_receipt=receipts[0])


class QueryBoundReductionProvider:
    def __init__(self, policy, attributes, base_provider):
        self._policy, self._attributes, self._base = policy, attributes, base_provider

    def collect(self, context: BattleContext, request):
        base = self._base.collect(context, request)
        receipt = getattr(request, "target_priority_receipt", None)
        if receipt is None or request.source_type is not DamageSourceType.SKILL or request.source_state_id is not None:
            return base
        if (receipt.source_id, receipt.source_skill_id, receipt.target_id, receipt.round_no, receipt.context_scope) != (
                request.source_id, request.source_skill_id, request.target_id, context.current_round, id(context)):
            return base
        states = [state for state in self._policy.effective_instances(context, request.target_id, TARGET_PRIORITY_STATE_ID)
                  if (state.instance_id, state.current_generation_id) == (
                      receipt.priority_state_instance_id, receipt.priority_generation_id)]
        if not states:
            return base
        state = states[0]
        params = state.runtime_params
        unit = context.get_unit(request.target_id)
        attribute = getattr(self._attributes, f"get_{params.reduction_attribute}")(context, unit)
        rate = params.reduction_base + params.reduction_slope * (attribute - params.reduction_reference)
        # Out-of-domain formula values are explicit; no invented clamp/cap.
        validate_probability(rate, "live reduction rate")
        origin = f"query_reduction:{receipt.operation_id}:{state.instance_id}"
        modifier = DamageModifierContribution(phase=DamageModifierPhase.INCOMING,
            kind=DamageModifierKind.INCOMING_REDUCTION, operation=DamageModifierOperation.MULTIPLY_FACTOR,
            operand=1-rate, source=RuleContributionSource(state.owner_id, state.source_id,
                state.source_skill_id, state.state_id, state.instance_id, origin), order_key=origin)
        return DamageRuleCollection(base.prevention_contributions, base.hit_contributions,
            base.formula_policy_contributions, base.modifier_contributions + (modifier,))
