"""Generic provider-action parity driver over canonical effects and formula owners."""
from __future__ import annotations
from dataclasses import dataclass, replace
from enum import Enum
from typing import TYPE_CHECKING
from .context import BattleContext
from .effect_result import EffectExecutionResult
from .rule_hooks import RuleHook
from .rule_hook_system import HookResolutionResult
from .state_registry import StateRegistry
if TYPE_CHECKING:
    from .battle_systems import BattleSystems

from .damage_rate_modifier import DAMAGE_RATE_STATE_ID, DamageRateParams
from .dependency_evaluation import ProviderNode, StateNode
from .effects import ApplyStateEffect, EffectSourceRef, RecoverEffect, RemoveStateEffect
from .numeric_validation import validate_nonnegative_finite
from .operation_identity import SourceType
from .priority_target_system import PriorityTargetSystem
from .provider_identity import SkillProviderRef
from .recovery_system import RecoveryModifierPolicy
from .rule_hooks import UnitActionStartHook
from .state_definition import StateDefinition
from .state_effectiveness import StateEffectivenessContribution, InactivityCause, LocalRuleCauseRef
from .state_runtime_params import StateRuntimeParams
from .temporary_damage_pool import PoolRuleHookSystem
from .treatment_formula import TreatmentModifierSnapshot
from .stage9_integerization import ExactRatio
from .target_operation import (TargetOperationProducer, TargetRelation, TargetCardinality,
    TargetSelectorKind, TargetEligibilityContext, TargetOperationDomain, TargetPurpose)

PERIODIC_TEAM_SUPPORT_STATE_ID = "runtime_periodic_team_support"


class RecoveryTargetMode(str, Enum):
    RANDOM_ALLIES = "RANDOM_ALLIES"
    RANDOM_TEAM = "RANDOM_ALLIES"  # Compatibility alias; performer is excluded.
    LOWEST_TROOPS = "LOWEST_TROOPS"


@dataclass(frozen=True, slots=True)
class PeriodicTeamSupportParams(StateRuntimeParams):
    recovery_actor_id: str
    increase_target_id: str
    recovery_rate: float
    increase_rate: float
    recovery_target_mode: RecoveryTargetMode

    def __post_init__(self):
        for key in ("recovery_actor_id", "increase_target_id"):
            value = getattr(self, key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{key} must be nonblank")
        if self.recovery_actor_id == self.increase_target_id:
            raise ValueError("periodic support requires distinct role identities")
        for key in ("recovery_rate", "increase_rate"):
            object.__setattr__(self, key, validate_nonnegative_finite(getattr(self, key), key))
        if not isinstance(self.recovery_target_mode, RecoveryTargetMode):
            raise TypeError("recovery_target_mode must be RecoveryTargetMode")


DEFINITION = StateDefinition(PERIODIC_TEAM_SUPPORT_STATE_ID, "行动时奇偶回合团队支援",
                             runtime_params_type=PeriodicTeamSupportParams)


def periodic_support_effectiveness_adapter(context, state, session):
    if state.state_id != PERIODIC_TEAM_SUPPORT_STATE_ID:
        return StateEffectivenessContribution()
    runtime = context.skill_runtimes.get(state.source_id, state.source_skill_slot)
    provider = context.units.get(state.source_id)
    if (runtime is None or not runtime.enabled or runtime.definition.skill_id != state.source_skill_id
            or provider is None or not provider.is_alive):
        return StateEffectivenessContribution(inactivity_causes=(InactivityCause(
            "PERIODIC_SUPPORT_PROVIDER_UNAVAILABLE", LocalRuleCauseRef(state.instance_id)),))
    return StateEffectivenessContribution()


def register_periodic_team_support_state(registry: StateRegistry) -> None:
    try:
        existing = registry.get_definition(DEFINITION.state_id)
    except KeyError:
        registry.register_definition(DEFINITION)
    else:
        if existing != DEFINITION:
            raise ValueError("incompatible periodic support schema")


class PeriodicTeamSupport:
    def __init__(self, systems: BattleSystems) -> None:
        self._systems = systems
        self._priority_targets = PriorityTargetSystem(systems.target_system)

    def execute(self, context: BattleContext, hook: UnitActionStartHook) -> tuple[EffectExecutionResult, ...]:
        s = self._systems
        if context.ended or s.finalization_coordinator.is_latched_or_finalized:
            return ()
        results = []
        for driver in s.state_effectiveness_policy.effective_instances(
                context, hook.actor_id, PERIODIC_TEAM_SUPPORT_STATE_ID):
            params = driver.runtime_params
            if not isinstance(params, PeriodicTeamSupportParams):
                raise TypeError("periodic support requires typed params")
            key = (driver.instance_id, driver.current_generation_id)
            cursors = context.metadata.setdefault("periodic_team_support_cursors", {})
            if hook.round_no <= cursors.get(key, 0):
                continue
            provider = SkillProviderRef(driver.source_id, driver.source_skill_slot, driver.source_skill_id)
            row = {"round": hook.round_no, "provider_id": provider.owner_id,
                   "provider_slot": int(provider.skill_slot), "skill_id": provider.skill_id,
                   "driver_instance_id": driver.instance_id}
            if hook.round_no % 2:
                actor = context.get_unit(params.recovery_actor_id)
                row.update(kind="RECOVERY", performer_id=actor.unit_id)
                if actor.is_alive:
                    candidates = s.target_system.allies(context, actor, include_self=False)
                    # Provider owns this fresh target operation; teammate remains
                    # recovery performer. Do not invent an equipped slot on teammate.
                    operation = TargetOperationProducer.new_query(context,
                        actor_id=provider.owner_id, producer_ref=provider,
                        admitted_operation_key=f"periodic:{driver.instance_id}:{hook.round_no}",
                        relation=TargetRelation.ALLY, cardinality=TargetCardinality.SINGLE,
                        selector_kind=(TargetSelectorKind.RANDOM if params.recovery_target_mode
                            is RecoveryTargetMode.RANDOM_TEAM else TargetSelectorKind.DETERMINISTIC),
                        eligibility_context=TargetEligibilityContext(
                            TargetOperationDomain.SKILL, TargetPurpose.FRIENDLY_SUPPORT))
                    decision = s.skill_target_policy.evaluate(context, operation, candidates)
                    if not decision.supported or len(decision.required_target_ids) > 1:
                        raise ValueError("unsupported periodic recovery target-policy boundary")
                    candidates = [u for u in candidates if u.unit_id in decision.eligible_candidate_ids]
                    required = [u for u in candidates if u.unit_id in decision.required_target_ids]
                    if params.recovery_target_mode is RecoveryTargetMode.RANDOM_TEAM:
                        targets = required or s.target_system.random_units(context, candidates, count=1)
                    else:
                        priority = self._priority_targets.lowest_troop_allies(context, actor)
                        targets = required or [u for u in priority if u.unit_id in decision.eligible_candidate_ids][:1]
                    for target in targets:
                        # No attribute influence is declared for this lane. Current
                        # performer troops and advancement are read at this trigger.
                        source_troops = actor.troops
                        nominal = s.treatment_formula_system.calculate(
                            rate=params.recovery_rate, source_troops=source_troops, source_attribute=0,
                            modifiers=TreatmentModifierSnapshot(
                                red_pool_multiplier=ExactRatio(100 + 2 * actor.advancement_stars, 100)))
                        results.append(s.effect_executor.execute(context, RecoverEffect(
                            actor.unit_id, target.unit_id, nominal.nominal_recovery,
                            source_skill_id=provider.skill_id, source_state_id=driver.state_id,
                            source_state_instance_id=driver.instance_id,
                            modifier_policy=RecoveryModifierPolicy.APPLY)))
                        row.update(target_id=target.unit_id, source_troops=source_troops,
                                   nominal_recovery=nominal.nominal_recovery)
                    row["status"] = "APPLIED" if targets else "NO_LIVING_TARGET"
                else:
                    row["status"] = "PERFORMER_DEFEATED"
            else:
                target = context.get_unit(params.increase_target_id)
                row.update(kind="OUTGOING_INCREASE", target_id=target.unit_id)
                if target.is_alive:
                    old_states = [old for old in context.states.find(
                        owner_id=target.unit_id, state_id=DAMAGE_RATE_STATE_ID, source_id=provider.owner_id)
                        if (old.source_skill_id, old.source_skill_slot) == (provider.skill_id, provider.skill_slot)
                        and isinstance(old.runtime_params, DamageRateParams)
                        and old.runtime_params.prerequisite_state_id == driver.instance_id]
                    # Same-source stacks are one additive rate, not exponential factors.
                    rate = params.increase_rate + sum(old.runtime_params.outgoing_rate for old in old_states)
                    for old in old_states:
                        results.append(s.effect_executor.execute(context, RemoveStateEffect(old.instance_id)))
                    effect = ApplyStateEffect(DAMAGE_RATE_STATE_ID, target.unit_id,
                        provider.owner_id, provider.skill_id,
                        runtime_params=DamageRateParams(outgoing_rate=rate,
                                                       prerequisite_state_id=driver.instance_id),
                        source_ref=EffectSourceRef(SourceType.ACTIVE_SKILL, provider.owner_id,
                                                  provider.skill_id, provider.skill_slot))
                    result = s.effect_executor.execute(context, effect)
                    s.dependency_evaluation_support.add_dependency(
                        StateNode(result.state_instance.instance_id), ProviderNode(provider))
                    results.append(result)
                    row.update(status="APPLIED", cumulative_increase_rate=rate)
                else:
                    row["status"] = "TARGET_DEFEATED"
            cursors[key] = hook.round_no
            context.metadata.setdefault("periodic_team_support_history", []).append(row)
        return tuple(results)


class PeriodicTeamSupportRuleHookSystem(PoolRuleHookSystem):
    def __init__(self, *args, periodic_support, **kwargs):
        super().__init__(*args, **kwargs)
        self._periodic_support = periodic_support

    def process(self, context: BattleContext, hook: RuleHook) -> HookResolutionResult:
        ordinary = super().process(context, hook)
        if not isinstance(hook, UnitActionStartHook) or ordinary.batch_status != "COMPLETED":
            return ordinary
        results = self._periodic_support.execute(context, hook)
        return replace(ordinary, intent_results=ordinary.intent_results + results,
                       effect_results=ordinary.effect_results + results)
