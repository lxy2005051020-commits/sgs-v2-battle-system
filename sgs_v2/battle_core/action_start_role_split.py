"""Opt-in, state-backed deputy redistribution after the ordinary action-start batch.

Target queries, effect execution, state lifetime and damage calculation keep their
existing owners. A driver can be used by any provider; no tactic identity is read.
"""
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING
from .context import BattleContext
from .effect_result import EffectExecutionResult
from .rule_hook_system import HookResolutionResult
from .rule_hooks import RuleHook
from .state_registry import StateRegistry
if TYPE_CHECKING:
    from .battle_systems import BattleSystems

from .damage_rate_modifier import DAMAGE_RATE_STATE_ID, DamageRateParams
from .dependency_evaluation import ProviderNode, StateNode
from .effects import ApplyStateEffect, EffectSourceRef, RemoveStateEffect
from .numeric_validation import validate_probability
from .operation_identity import SourceType
from .priority_target_system import PriorityTargetSystem
from .provider_identity import SkillProviderRef
from .rule_hooks import UnitActionStartHook
from .state_definition import StateDefinition
from .state_runtime_params import StateRuntimeParams
from .periodic_team_support import PeriodicTeamSupportRuleHookSystem

ROLE_SPLIT_STATE_ID = "runtime_action_start_role_split"


@dataclass(frozen=True, slots=True)
class RoleSplitParams(StateRuntimeParams):
    initial_troops: tuple[tuple[str, int], ...]
    reduction_rate: float
    increase_rate: float

    def __post_init__(self):
        initial = tuple(self.initial_troops)
        if len(initial) != 2 or len({uid for uid, _ in initial}) != 2:
            raise ValueError("role split requires two distinct deputy snapshots")
        for uid, troops in initial:
            if not isinstance(uid, str) or not uid.strip() or type(troops) is not int or troops <= 0:
                raise ValueError("invalid deputy entry troop snapshot")
        object.__setattr__(self, "initial_troops", initial)
        for key in ("reduction_rate", "increase_rate"):
            object.__setattr__(self, key, validate_probability(getattr(self, key), key))


ROLE_SPLIT_DEFINITION = StateDefinition(ROLE_SPLIT_STATE_ID, "行动前副将损兵分配",
                                      runtime_params_type=RoleSplitParams)


def register_role_split_state(registry: StateRegistry) -> None:
    try:
        current = registry.get_definition(ROLE_SPLIT_STATE_ID)
    except KeyError:
        registry.register_definition(ROLE_SPLIT_DEFINITION)
    else:
        if current != ROLE_SPLIT_DEFINITION:
            raise ValueError("incompatible role split schema")


class ActionStartRoleSplitSupport:
    def __init__(self, systems: "BattleSystems") -> None:
        self._systems = systems
        self._targets = PriorityTargetSystem(systems.target_system)

    def execute(self, context: BattleContext, hook: UnitActionStartHook) -> tuple[EffectExecutionResult, ...]:
        s = self._systems
        if context.ended or s.finalization_coordinator.is_latched_or_finalized:
            return ()
        states = s.state_effectiveness_policy.effective_instances(
            context, hook.actor_id, ROLE_SPLIT_STATE_ID)
        results = []
        for driver in states:
            params = driver.runtime_params
            if not isinstance(params, RoleSplitParams):
                raise TypeError("role split requires RoleSplitParams")
            ref = SkillProviderRef(driver.source_id, driver.source_skill_slot, driver.source_skill_id)
            key = (driver.instance_id, driver.current_generation_id)
            book = context.metadata.setdefault("action_start_role_split_cursors", {})
            if book.get(key) == hook.round_no:
                continue
            deputies = self._targets.most_lost_troop_deputies(
                context, context.get_unit(driver.owner_id), dict(params.initial_troops))
            # Remove only this provider's split effects, including an inactive
            # or defeated old target. Other providers' contributions survive.
            for old in context.states.find(state_id=DAMAGE_RATE_STATE_ID, source_id=ref.owner_id):
                if (old.source_skill_id, old.source_skill_slot) == (ref.skill_id, ref.skill_slot):
                    results.append(s.effect_executor.execute(context, RemoveStateEffect(old.instance_id)))
            targets = []
            if len(deputies) == 2:
                source = EffectSourceRef(SourceType.ACTIVE_SKILL, ref.owner_id, ref.skill_id, ref.skill_slot)
                for unit, rates in ((deputies[0], DamageRateParams(incoming_rate=-params.reduction_rate,
                                                                  prerequisite_state_id=driver.instance_id)),
                                    (deputies[1], DamageRateParams(outgoing_rate=params.increase_rate,
                                                                  prerequisite_state_id=driver.instance_id))):
                    result = s.effect_executor.execute(context, ApplyStateEffect(
                        DAMAGE_RATE_STATE_ID, unit.unit_id, ref.owner_id, ref.skill_id,
                        runtime_params=rates, source_ref=source))
                    s.dependency_evaluation_support.add_dependency(
                        StateNode(result.state_instance.instance_id), ProviderNode(ref))
                    results.append(result)
                    targets.append(unit.unit_id)
            book[key] = hook.round_no
            context.metadata.setdefault("action_start_role_split_history", []).append({
                "round": hook.round_no, "actor_id": hook.actor_id, "source_skill_id": ref.skill_id,
                "provider_id": ref.owner_id, "provider_slot": int(ref.skill_slot),
                "reduction_target_id": targets[0] if targets else None,
                "increase_target_id": targets[1] if targets else None,
                "losses": {u.unit_id: dict(params.initial_troops)[u.unit_id] - u.troops for u in deputies},
                "status": "APPLIED" if targets else "MISSING_LIVING_DEPUTY_PAIR"})
        return tuple(results)


class RoleSplitRuleHookSystem(PeriodicTeamSupportRuleHookSystem):
    def __init__(self, *args, role_split_support, **kwargs):
        super().__init__(*args, **kwargs)
        self._role_split_support = role_split_support

    def process(self, context: BattleContext, hook: RuleHook) -> HookResolutionResult:
        ordinary = super().process(context, hook)
        if not isinstance(hook, UnitActionStartHook) or ordinary.batch_status != "COMPLETED":
            return ordinary
        results = self._role_split_support.execute(context, hook)
        return replace(ordinary, intent_results=ordinary.intent_results + results,
                       effect_results=ordinary.effect_results + results)
