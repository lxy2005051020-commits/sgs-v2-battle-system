"""Generic signed incoming/outgoing rates; canonical damage pools own arithmetic."""
from dataclasses import dataclass
from typing import TYPE_CHECKING
from .context import BattleContext

from .damage_modifiers import (DamageModifierContribution, DamageModifierKind,
                              DamageModifierOperation, DamageModifierPhase)
from .damage_rule_models import RuleContributionSource
from .damage_rule_provider import DamageRuleCollection, DamageRuleProvider
from .enums import DamageType
from .numeric_validation import validate_finite_number
from .state_definition import StateDefinition
from .state_runtime_params import StateRuntimeParams
from .dependency_evaluation import StateNode
from .state_effectiveness import (StateEffectivenessPolicy, StateEffectivenessContribution, InactivityCause,
    SuppressionCause, LocalRuleCauseRef, StateCauseRef)
from .state_instance import StateInstance
from .state_registry import StateRegistry
from .dependency_evaluation import _EvaluationSession
if TYPE_CHECKING:
    from .damage_system import DamageRequest

DAMAGE_RATE_STATE_ID = "runtime_damage_rate_modifier"


@dataclass(frozen=True, slots=True)
class DamageRateParams(StateRuntimeParams):
    outgoing_rate: float = 0.0
    incoming_rate: float = 0.0
    prerequisite_state_id: str | None = None

    def __post_init__(self):
        if self.prerequisite_state_id is not None and (
                not isinstance(self.prerequisite_state_id, str) or not self.prerequisite_state_id.strip()):
            raise ValueError("prerequisite_state_id must be nonblank or None")
        for key in ("outgoing_rate", "incoming_rate"):
            object.__setattr__(self, key, validate_finite_number(
                getattr(self, key), key, minimum=-1.0))


@dataclass(frozen=True, slots=True)
class RoundDamageRateParams(DamageRateParams):
    """Opening round rates followed by an additive per-round ramp.

    Round zero uses round one's opening rates for PRE_BATTLE visibility.
    The curve is declarative; collection never mutates states or consumes RNG.
    """

    opening_rates: tuple[tuple[float, float], ...] = ()
    outgoing_step: float = 0.0
    incoming_step: float = 0.0

    def __post_init__(self):
        DamageRateParams.__post_init__(self)
        if self.outgoing_rate != 0 or self.incoming_rate != 0:
            raise ValueError("round curves require zero static rates")
        rows = tuple(tuple(row) for row in self.opening_rates)
        if not rows or any(len(row) != 2 for row in rows):
            raise ValueError("opening_rates requires nonempty outgoing/incoming pairs")
        object.__setattr__(self, "opening_rates", tuple(
            tuple(validate_finite_number(v, "opening rate", minimum=-1.0) for v in row)
            for row in rows))
        for key in ("outgoing_step", "incoming_step"):
            object.__setattr__(self, key, validate_finite_number(
                getattr(self, key), key, minimum=0))

    def rates_at(self, round_no: int) -> tuple[float, float]:
        if type(round_no) is not int or round_no < 0:
            raise ValueError("round_no must be a nonnegative integer")
        index = max(1, round_no)
        if index <= len(self.opening_rates):
            return self.opening_rates[index - 1]
        stacks = index - len(self.opening_rates)
        return self.outgoing_step * stacks, self.incoming_step * stacks


DAMAGE_RATE_DEFINITION = StateDefinition(DAMAGE_RATE_STATE_ID, "伤害增减修饰",
                                        runtime_params_type=DamageRateParams)


def damage_rate_prerequisite_adapter(context: BattleContext, state: StateInstance,
                                     session: _EvaluationSession) -> StateEffectivenessContribution:
    """Follow an optional driver without dangling graph edges after its removal."""
    params = state.runtime_params
    if not isinstance(params, DamageRateParams) or params.prerequisite_state_id is None:
        return StateEffectivenessContribution()
    driver_id = params.prerequisite_state_id
    if not context.states.has_instance(driver_id):
        return StateEffectivenessContribution(inactivity_causes=(InactivityCause(
            "DAMAGE_RATE_PREREQUISITE_REMOVED", LocalRuleCauseRef(driver_id)),))
    driver = context.states.get(driver_id)
    decision = session.evaluate(StateNode(driver_id))
    if decision.effective:
        return StateEffectivenessContribution()
    return StateEffectivenessContribution(suppression_causes=(SuppressionCause(
        "DAMAGE_RATE_PREREQUISITE_INEFFECTIVE", StateCauseRef(driver_id, driver.current_generation_id)),))


def register_damage_rate_state(registry: StateRegistry) -> None:
    try:
        current = registry.get_definition(DAMAGE_RATE_STATE_ID)
    except KeyError:
        registry.register_definition(DAMAGE_RATE_DEFINITION)
    else:
        if current != DAMAGE_RATE_DEFINITION:
            raise ValueError("incompatible signed damage rate schema")


class DamageRateModifierProvider:
    def __init__(self, policy: StateEffectivenessPolicy, base_provider: DamageRuleProvider) -> None:
        self._policy, self._base = policy, base_provider

    def collect(self, context: BattleContext, request: "DamageRequest") -> DamageRuleCollection:
        base = self._base.collect(context, request)
        modifiers = list(base.modifier_contributions)
        for unit_id, phase, key, positive, negative in (
            (request.source_id, DamageModifierPhase.OUTGOING, "outgoing_rate",
             DamageModifierKind.OUTGOING_INCREASE, DamageModifierKind.OUTGOING_REDUCTION),
            (request.target_id, DamageModifierPhase.INCOMING, "incoming_rate",
             DamageModifierKind.INCOMING_INCREASE, DamageModifierKind.INCOMING_REDUCTION),
        ):
            for state in self._policy.effective_instances(context, unit_id, DAMAGE_RATE_STATE_ID):
                if not isinstance(state.runtime_params, DamageRateParams):
                    raise TypeError("damage rate state requires DamageRateParams")
                params = state.runtime_params
                rate = (params.rates_at(context.current_round)[0 if key == "outgoing_rate" else 1]
                        if isinstance(params, RoundDamageRateParams) else getattr(params, key))
                if rate == 0:
                    continue
                origin = f"damage_rate:{state.instance_id}:{phase.value}"
                modifiers.append(DamageModifierContribution(
                    phase=phase, kind=positive if rate > 0 else negative,
                    operation=DamageModifierOperation.MULTIPLY_FACTOR, operand=1 + rate,
                    source=RuleContributionSource(state.owner_id, state.source_id,
                        state.source_skill_id, state.state_id, state.instance_id, origin),
                    order_key=origin, damage_types=frozenset(DamageType)))
        return DamageRuleCollection(base.prevention_contributions, base.hit_contributions,
                                    base.formula_policy_contributions, tuple(modifiers))
