"""Opt-in state gate composed over the frozen trigger collector."""
from __future__ import annotations

from .context import BattleContext
from .rule_hooks import RuleHook
from .rule_intent import RuleIntent
from .skill_runtime_registry import PersistentSourceSkillGateMode
from .stage10_state_params import ContinuousDamageStateParams
from .state_effectiveness import StateEffectivenessPolicy
from .trigger_system import TriggerSystem


class StateEffectivenessTriggerAdapter(TriggerSystem):
    """Reuse collection and after-damage behavior; gate only opted-in DOT intents."""

    def __init__(self, lifecycle_system=None, equipment_effectiveness_policy=None,
                 state_effectiveness_policy: StateEffectivenessPolicy | None = None):
        super().__init__(lifecycle_system, equipment_effectiveness_policy)
        self._state_policy = state_effectiveness_policy

    def collect(self, context: BattleContext, hook: RuleHook) -> tuple[RuleIntent, ...]:
        admitted = []
        for intent in super().collect(context, hook):
            descriptor = intent.execution_descriptor
            state = (context.states.get(descriptor.state_instance_id)
                     if descriptor.state_instance_id is not None else None)
            params = state.runtime_params if state is not None else None
            if (isinstance(params, ContinuousDamageStateParams)
                and params.source_skill_gate.mode is PersistentSourceSkillGateMode.QUERY_SKILL_RUNTIME
                and self._state_policy is not None
                and not self._state_policy.evaluate_state(context, state).effective):
                continue
            admitted.append(intent)
        return tuple(admitted)
