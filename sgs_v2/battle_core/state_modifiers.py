"""Typed additive modifiers backed by canonical state storage and effectiveness.

IDs below are internal Runtime representations, not official client state IDs.
Mutation, expiry, provider suppression and finalization remain existing owners.
"""
from __future__ import annotations

from dataclasses import dataclass

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

ATTRIBUTE_BONUS_STATE_ID = "runtime_attribute_bonus"
ACTIVATION_RATE_BONUS_STATE_ID = "runtime_activation_rate_bonus"


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


MODIFIER_STATE_DEFINITIONS = (
    StateDefinition(ATTRIBUTE_BONUS_STATE_ID, "属性修饰", runtime_params_type=AttributeBonusParams),
    StateDefinition(ACTIVATION_RATE_BONUS_STATE_ID, "发动率修饰", runtime_params_type=ActivationRateBonusParams),
)


def modifier_conflict_rule(context: BattleContext, candidate: StateCandidate,
                           residents: tuple[StateInstance, ...]) -> StateConflictDecision | None:
    """Distinct provider/dimension contributions coexist; duplicates cannot stack.

    This is an internal additive-contribution policy, not a general rule for
    stacking arbitrary official game states.
    """
    if candidate.state_id not in (ATTRIBUTE_BONUS_STATE_ID, ACTIVATION_RATE_BONUS_STATE_ID):
        return None
    params = candidate.runtime_params_candidate
    dimension = getattr(params, "attribute", getattr(params, "skill_type", None))
    for resident in residents:
        resident_dimension = getattr(resident.runtime_params, "attribute",
                                     getattr(resident.runtime_params, "skill_type", None))
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
