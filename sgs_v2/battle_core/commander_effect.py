"""Commander-effect qualification is independent of physical lineup identity.

Declarations live in SkillDefinition. Ordinary and commander state IDs must be
disjoint, allowing provenance to identify resident commander states exactly.
No tactic IDs, skill-name inference or substitute executor are used here.
"""
from dataclasses import dataclass
from .context import BattleContext
from .dependency_evaluation import StateNode, _EvaluationSession
from .enums import LineupPosition
from .skill_definition import ApplyStateSkillEffectSpec
from .state_definition import StateDefinition
from .state_runtime_params import StateRuntimeParams
from .state_instance import StateInstance
from .state_registry import StateRegistry
from .state_effectiveness import (StateEffectivenessContribution, InactivityCause,
                                  LocalRuleCauseRef, StateEffectivenessPolicy)

COMMANDER_EFFECT_ROLE_STATE_ID = "runtime_commander_effect_qualification"


@dataclass(frozen=True, slots=True)
class CommanderEffectRoleParams(StateRuntimeParams):
    enabled: bool

    def __post_init__(self) -> None:
        if type(self.enabled) is not bool:
            raise TypeError("commander-effect qualification must be bool")


ROLE_DEFINITION = StateDefinition(COMMANDER_EFFECT_ROLE_STATE_ID,
    "主将效果资格", runtime_params_type=CommanderEffectRoleParams)


def register_commander_effect_role_state(registry: StateRegistry) -> None:
    try:
        existing = registry.get_definition(COMMANDER_EFFECT_ROLE_STATE_ID)
    except KeyError:
        registry.register_definition(ROLE_DEFINITION)
    else:
        if existing != ROLE_DEFINITION:
            raise ValueError("incompatible commander-effect qualification schema")


class CommanderEffectPolicy:
    def __init__(self, effectiveness_policy: StateEffectivenessPolicy) -> None:
        self._effectiveness = effectiveness_policy

    def enabled(self, context: BattleContext, actor_id: str, *,
                session: _EvaluationSession | None = None) -> bool:
        unit = context.get_unit(actor_id)
        if not unit.is_alive:
            return False
        active = []
        for state in context.states.find(owner_id=actor_id, state_id=COMMANDER_EFFECT_ROLE_STATE_ID):
            decision = (session.evaluate(StateNode(state.instance_id)) if session is not None
                        else self._effectiveness.evaluate_state(context, state))
            if decision.effective:
                active.append(state.runtime_params.enabled)
        if len(active) > 1:
            raise ValueError("multiple commander-effect overrides require an arbitration contract")
        return active[0] if active else unit.lineup_position is LineupPosition.COMMANDER

    def state_adapter(self, context: BattleContext, state: StateInstance,
                      session: _EvaluationSession) -> StateEffectivenessContribution:
        runtime = context.skill_runtimes.get(state.source_id, state.source_skill_slot)
        if runtime is None or runtime.definition.skill_id != state.source_skill_id:
            return StateEffectivenessContribution()
        commander_states = {spec.state_id for spec in runtime.definition.commander_effect_specs
                            if isinstance(spec, ApplyStateSkillEffectSpec)}
        if state.state_id not in commander_states:
            return StateEffectivenessContribution()
        if self.enabled(context, runtime.owner_id, session=session):
            return StateEffectivenessContribution()
        return StateEffectivenessContribution(inactivity_causes=(InactivityCause(
            "COMMANDER_EFFECT_NOT_QUALIFIED", LocalRuleCauseRef(runtime.owner_id)),))
