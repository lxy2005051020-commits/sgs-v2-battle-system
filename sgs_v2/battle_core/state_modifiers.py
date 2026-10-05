"""Typed additive modifiers backed by canonical state storage and effectiveness.

IDs below are internal Runtime representations, not official client state IDs.
Mutation, expiry, provider suppression and finalization remain existing owners.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .context import BattleContext
from .numeric_validation import validate_finite_number
from .skill_definition import SkillType
from .skill_runtime import SkillRuntime
from .state_definition import StateDefinition
from .state_effectiveness import StateEffectivenessPolicy
from .state_application import ApplicationDisposition, StateCandidate, StateConflictDecision
from .state_instance import StateInstance
from .state_registry import StateRegistry
from .state_runtime_params import StateRuntimeParams
from .unit import UnitRuntime
from .enums import DamageType
from .damage_rule_provider import DamageRuleCollection, DamageRuleProvider, StateDamageRuleProvider
from .damage_rule_models import RuleContributionSource
from .damage_modifiers import DamageModifierContribution, DamageModifierKind, DamageModifierOperation, DamageModifierPhase

if TYPE_CHECKING:
    from .damage_system import DamageRequest

ATTRIBUTE_BONUS_STATE_ID = "runtime_attribute_bonus"
ACTIVATION_RATE_BONUS_STATE_ID = "runtime_activation_rate_bonus"
INCOMING_DAMAGE_REDUCTION_STATE_ID = "runtime_incoming_damage_reduction"


@dataclass(frozen=True, slots=True)
class IncomingDamageReductionParams(StateRuntimeParams):
    damage_type: DamageType
    rate: float

    def __post_init__(self) -> None:
        if not isinstance(self.damage_type, DamageType):
            raise TypeError("damage_type must be DamageType")
        object.__setattr__(self, "rate", validate_finite_number(self.rate, "rate", minimum=0, maximum=1))


@dataclass(frozen=True, slots=True)
class AttributeBonusParams(StateRuntimeParams):
    attribute: str
    amount: float

    def __post_init__(self) -> None:
        if self.attribute not in ("attack", "defense", "intelligence", "speed"):
            raise ValueError("unsupported attribute")
        object.__setattr__(self, "amount", validate_finite_number(self.amount, "amount"))


@dataclass(frozen=True, slots=True)
class ActivationRateBonusParams(StateRuntimeParams):
    skill_type: SkillType
    amount: float

    def __post_init__(self) -> None:
        if not isinstance(self.skill_type, SkillType) or self.skill_type not in (SkillType.ACTIVE, SkillType.ASSAULT):
            raise ValueError("activation bonus requires ACTIVE or ASSAULT")
        object.__setattr__(self, "amount", validate_finite_number(self.amount, "amount"))


def _validate_stack(params):
    if any(not isinstance(v, str) or not v.strip() for v in (params.stack_key, params.stack_group)):
        raise ValueError("bounded modifiers require stack key and group")
    if type(params.max_stacks) is not int or params.max_stacks < 1:
        raise ValueError("max_stacks must be a positive integer")


@dataclass(frozen=True, slots=True)
class BoundedAttributeBonusParams(AttributeBonusParams):
    stack_key: str
    stack_group: str
    max_stacks: int

    def __post_init__(self):
        AttributeBonusParams.__post_init__(self)
        _validate_stack(self)


@dataclass(frozen=True, slots=True)
class BoundedActivationRateBonusParams(ActivationRateBonusParams):
    stack_key: str
    stack_group: str
    max_stacks: int

    def __post_init__(self):
        ActivationRateBonusParams.__post_init__(self)
        _validate_stack(self)


MODIFIER_STATE_DEFINITIONS = (
    StateDefinition(INCOMING_DAMAGE_REDUCTION_STATE_ID, "受到伤害降低", runtime_params_type=IncomingDamageReductionParams),
    StateDefinition(ATTRIBUTE_BONUS_STATE_ID, "属性修饰", runtime_params_type=AttributeBonusParams),
    StateDefinition(ACTIVATION_RATE_BONUS_STATE_ID, "发动率修饰", runtime_params_type=ActivationRateBonusParams),
)


def modifier_conflict_rule(context: BattleContext, candidate: StateCandidate,
                           residents: tuple[StateInstance, ...]) -> StateConflictDecision | None:
    """Distinct provider/dimension contributions coexist; duplicates cannot stack.

    This is an internal additive-contribution policy, not a general rule for
    stacking arbitrary official game states.
    """
    if candidate.state_id not in (ATTRIBUTE_BONUS_STATE_ID, ACTIVATION_RATE_BONUS_STATE_ID, INCOMING_DAMAGE_REDUCTION_STATE_ID):
        return None
    params = candidate.runtime_params_candidate
    dimension = getattr(params, "attribute", getattr(params, "skill_type", getattr(params, "damage_type", None)))
    if isinstance(params, (BoundedAttributeBonusParams, BoundedActivationRateBonusParams)):
        matches = tuple(r for r in residents
            if (r.source_id, r.source_skill_id, r.source_skill_slot) ==
               (candidate.source_id, candidate.source_skill_id, candidate.source_skill_slot)
            and getattr(r.runtime_params, "stack_group", None) == params.stack_group
            and getattr(r.runtime_params, "attribute", getattr(r.runtime_params, "skill_type", None)) == dimension)
        if any(r.runtime_params.stack_key == params.stack_key for r in matches):
            return StateConflictDecision(ApplicationDisposition.REJECT_CONFLICT, "MODIFIER_DUPLICATE_STACK")
        if len(matches) >= params.max_stacks:
            return StateConflictDecision(ApplicationDisposition.REJECT_CONFLICT, "MODIFIER_STACK_CAP")
        return StateConflictDecision(ApplicationDisposition.CREATE, "MODIFIER_STACK_CREATE")
    for resident in residents:
        resident_dimension = getattr(resident.runtime_params, "attribute",
                                     getattr(resident.runtime_params, "skill_type", getattr(resident.runtime_params, "damage_type", None)))
        if (resident.source_id, resident.source_skill_id, resident.source_skill_slot, resident_dimension) == (
            candidate.source_id, candidate.source_skill_id, candidate.source_skill_slot, dimension,
        ):
            return StateConflictDecision(ApplicationDisposition.REJECT_CONFLICT, "MODIFIER_DUPLICATE_SOURCE")
    return StateConflictDecision(ApplicationDisposition.CREATE, "MODIFIER_DISTINCT_SOURCE_CREATE")


def register_modifier_state_definitions(registry: StateRegistry) -> None:
    for definition in MODIFIER_STATE_DEFINITIONS:
        try:
            resident = registry.get_definition(definition.state_id)
        except KeyError:
            registry.register_definition(definition)
        else:
            if resident != definition:
                raise ValueError(f"incompatible modifier schema: {definition.state_id}")


class StateModifierSupport:
    def __init__(self, state_effectiveness_policy: StateEffectivenessPolicy) -> None:
        self._policy = state_effectiveness_policy

    def modify_attribute(self, *, context: BattleContext, unit: UnitRuntime,
                         attribute: str, base_value: float) -> float:
        return base_value + sum(
            item.runtime_params.amount
            for item in self._policy.effective_instances(context, unit.unit_id, ATTRIBUTE_BONUS_STATE_ID)
            if isinstance(item.runtime_params, AttributeBonusParams)
            and item.runtime_params.attribute == attribute
        )

    def activation_rate(self, context: BattleContext, runtime: SkillRuntime) -> float:
        bonus = sum(
            item.runtime_params.amount
            for item in self._policy.effective_instances(context, runtime.owner_id, ACTIVATION_RATE_BONUS_STATE_ID)
            if isinstance(item.runtime_params, ActivationRateBonusParams)
            and item.runtime_params.skill_type is runtime.definition.skill_type
        )
        return min(1.0, max(0.0, runtime.definition.activation_rate + bonus))


class IncomingDamageReductionProvider:
    """Compose typed effective target modifiers with the caller's rule provider.

    The canonical damage modifier system owns pooling, floors and pierce.
    """
    provider_key = "incoming_damage_reduction"

    def __init__(self, policy: StateEffectivenessPolicy, base_provider: DamageRuleProvider | None = None) -> None:
        self._policy = policy
        self._base = base_provider if base_provider is not None else StateDamageRuleProvider(())

    def collect(self, context: BattleContext, request: DamageRequest) -> DamageRuleCollection:
        base = self._base.collect(context, request)
        modifiers = list(base.modifier_contributions)
        for item in self._policy.effective_instances(context, request.target_id, INCOMING_DAMAGE_REDUCTION_STATE_ID):
            params = item.runtime_params
            if not isinstance(params, IncomingDamageReductionParams):
                raise TypeError("incoming reduction requires IncomingDamageReductionParams")
            if params.damage_type is not request.damage_type:
                continue
            origin = f"{self.provider_key}:{item.instance_id}"
            modifiers.append(DamageModifierContribution(
                phase=DamageModifierPhase.INCOMING,
                kind=DamageModifierKind.INCOMING_REDUCTION,
                operation=DamageModifierOperation.MULTIPLY_FACTOR,
                operand=1.0 - params.rate,
                source=RuleContributionSource(item.owner_id, item.source_id, item.source_skill_id,
                    item.state_id, item.instance_id, origin),
                order_key=origin, damage_types=frozenset({params.damage_type}),
            ))
        return DamageRuleCollection(base.prevention_contributions, base.hit_contributions,
                                    base.formula_policy_contributions, tuple(modifiers))
