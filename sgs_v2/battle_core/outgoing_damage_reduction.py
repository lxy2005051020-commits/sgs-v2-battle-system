"""Reusable state-backed outgoing reductions; core owns pools and floors."""
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .context import BattleContext
from .damage_modifiers import (DamageModifierContribution, DamageModifierKind,
    DamageModifierOperation, DamageModifierPhase)
from .damage_rule_models import RuleContributionSource
from .damage_rule_provider import DamageRuleCollection, DamageRuleProvider
from .enums import DamageType
from .numeric_validation import validate_probability
from .state_definition import StateDefinition
from .state_effectiveness import StateEffectivenessPolicy
from .state_registry import StateRegistry
from .state_runtime_params import StateRuntimeParams

if TYPE_CHECKING:
    from .damage_system import DamageRequest

OUTGOING_DAMAGE_REDUCTION_STATE_ID = "runtime_outgoing_damage_reduction"


@dataclass(frozen=True, slots=True)
class OutgoingDamageReductionParams(StateRuntimeParams):
    rate: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "rate", validate_probability(self.rate))


OUTGOING_DAMAGE_REDUCTION_DEFINITION = StateDefinition(
    OUTGOING_DAMAGE_REDUCTION_STATE_ID, "造成伤害降低",
    runtime_params_type=OutgoingDamageReductionParams,
)


def register_outgoing_reduction_state(registry: StateRegistry) -> None:
    try:
        resident = registry.get_definition(OUTGOING_DAMAGE_REDUCTION_STATE_ID)
    except KeyError:
        registry.register_definition(OUTGOING_DAMAGE_REDUCTION_DEFINITION)
    else:
        if resident != OUTGOING_DAMAGE_REDUCTION_DEFINITION:
            raise ValueError("incompatible outgoing reduction state schema")


class OutgoingDamageReductionProvider:
    provider_key = "outgoing_damage_reduction"

    def __init__(self, policy: StateEffectivenessPolicy,
                 base_provider: DamageRuleProvider) -> None:
        self._policy = policy
        self._base = base_provider

    def collect(self, context: BattleContext, request: "DamageRequest") -> DamageRuleCollection:
        base = self._base.collect(context, request)
        modifiers = list(base.modifier_contributions)
        for state in self._policy.effective_instances(
            context, request.source_id, OUTGOING_DAMAGE_REDUCTION_STATE_ID
        ):
            params = state.runtime_params
            if not isinstance(params, OutgoingDamageReductionParams):
                raise TypeError("outgoing reduction requires typed params")
            origin = f"{self.provider_key}:{state.instance_id}"
            modifiers.append(DamageModifierContribution(
                phase=DamageModifierPhase.OUTGOING,
                kind=DamageModifierKind.OUTGOING_REDUCTION,
                operation=DamageModifierOperation.MULTIPLY_FACTOR,
                operand=1.0 - params.rate,
                source=RuleContributionSource(state.owner_id, state.source_id,
                    state.source_skill_id, state.state_id, state.instance_id, origin),
                order_key=origin,
                damage_types=frozenset((DamageType.WEAPON, DamageType.STRATEGY)),
            ))
        return DamageRuleCollection(base.prevention_contributions, base.hit_contributions,
            base.formula_policy_contributions, tuple(modifiers))
