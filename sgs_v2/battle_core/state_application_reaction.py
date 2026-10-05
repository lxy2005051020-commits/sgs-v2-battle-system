"""State-backed application reactions composed after canonical state commit.

The adapter delegates all state mutation and generation handling to the existing
coordinator. It observes successful applications, including refreshes, without
using EventBus as a command channel or modifying the frozen coordinator.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from .context import BattleContext
from .state_instance import StateInstance
from .state_registry import StateRegistry
from .dependency_evaluation import StateNode

from .numeric_validation import validate_nonnegative_finite
from .stage10_state_params import ContinuousDamageStateParams
from .state_application import StateApplicationCoordinator, StateCandidate, StateApplicationResult
from .state_definition import StateDefinition
from .state_runtime_params import StateRuntimeParams
from .state_lifecycle_system import StateLifecycleSystem

APPLICATION_DAMAGE_REACTION_STATE_ID = "runtime_application_damage_reaction"
TROOP_DAMAGE_EFFECT_STATE_ID = "runtime_troop_damage_effect"


@dataclass(frozen=True, slots=True)
class ApplicationDamageReactionParams(StateRuntimeParams):
    trigger_state_id: str
    coefficient: float

    def __post_init__(self) -> None:
        if not isinstance(self.trigger_state_id, str) or not self.trigger_state_id.strip():
            raise ValueError("trigger_state_id must be non-empty")
        object.__setattr__(self, "coefficient", validate_nonnegative_finite(self.coefficient, "coefficient"))


@dataclass(frozen=True, slots=True)
class AssociatedContinuousDamageParams(ContinuousDamageStateParams):
    parent_state_instance_id: str = ""


REACTION_DEFINITIONS = (
    StateDefinition(APPLICATION_DAMAGE_REACTION_STATE_ID, "状态施加时追加持续伤害", runtime_params_type=ApplicationDamageReactionParams),
    StateDefinition(TROOP_DAMAGE_EFFECT_STATE_ID, "藤甲兵效果", runtime_params_type=AssociatedContinuousDamageParams),
)


def register_application_reaction_definitions(registry: StateRegistry) -> None:
    for definition in REACTION_DEFINITIONS:
        try:
            resident = registry.get_definition(definition.state_id)
        except KeyError:
            registry.register_definition(definition)
        else:
            if resident != definition:
                raise ValueError("incompatible application reaction definition")


class ReactingStateApplicationCoordinator(StateApplicationCoordinator):
    """Generic post-commit adapter for one state-backed continuous-damage reaction."""
    def apply_candidate(self, context: BattleContext, candidate: StateCandidate) -> StateApplicationResult:
        result = super().apply_candidate(context, candidate)
        if not result.committed or result.instance is None:
            return result
        self.react(context, result.instance)
        return result

    def react(self, context: BattleContext, parent: StateInstance) -> None:
        markers = self._state_effectiveness_policy.effective_instances(
            context, parent.owner_id, APPLICATION_DAMAGE_REACTION_STATE_ID)
        for marker in markers:
            reaction = marker.runtime_params
            if parent.state_id != reaction.trigger_state_id:
                continue
            params = parent.runtime_params
            if not isinstance(params, ContinuousDamageStateParams) or params.frozen_damage_basis is None:
                raise ValueError("application reaction requires a frozen continuous damage basis")
            # Preserve the original source's captured troops/intelligence and
            # outgoing plan; change only this independent effect's coefficient.
            basis = replace(params.frozen_damage_basis, coefficient=reaction.coefficient,
                            source_state_id=TROOP_DAMAGE_EFFECT_STATE_ID, historical_source=None)
            extra_params = AssociatedContinuousDamageParams(
                lifecycle_window=parent.lifecycle_window, frozen_damage_basis=basis,
                source_skill_gate=params.source_skill_gate,
                parent_state_instance_id=parent.instance_id)
            self._lifecycle.apply(context,
                state_id=TROOP_DAMAGE_EFFECT_STATE_ID, owner_id=parent.owner_id,
                source_id=parent.source_id, source_skill_id=parent.source_skill_id,
                source_skill_slot=parent.source_skill_slot,
                runtime_params=extra_params, lifecycle_window=parent.lifecycle_window,
                expires_round=parent.expires_round, expires_phase=parent.expires_phase)


class ReactingStateLifecycleSystem(StateLifecycleSystem):
    """Cover the existing legacy EffectExecutor ingress without replacing it."""
    reaction_port = None
    association_transition_coordinator = None
    _applying = False

    @staticmethod
    def associated_states(context: BattleContext, parent_id: str) -> tuple[StateInstance, ...]:
        return tuple(sorted((s for s in context.states.find()
            if isinstance(s.runtime_params, AssociatedContinuousDamageParams)
            and s.runtime_params.parent_state_instance_id == parent_id),
            key=lambda s: s.instance_id))

    def remove(self, context: BattleContext, instance_id: str, *, reason: str | None = None) -> StateInstance:
        # Called only after the removal coordinator's eligibility/precondition
        # checks. Remove children before publishing the parent's removal fact.
        context.states.get(instance_id)
        for child in self.associated_states(context, instance_id):
            transition = self.association_transition_coordinator
            roots = (StateNode(child.instance_id),)
            before = transition.capture(context, roots) if transition is not None else None
            self.remove(context, child.instance_id, reason=reason or "PARENT_STATE_REMOVED")
            if transition is not None:
                transition.complete_removed_nodes(context, before, roots)
        return super().remove(context, instance_id, reason=reason)

    def expire_state(self, context: BattleContext, instance_id: str, *,
                     expected_generation_id=None, reason: str = "DURATION_EXPIRED") -> StateInstance | None:
        if instance_id not in context.states:
            return None
        parent = context.states.get(instance_id)
        if expected_generation_id is not None and parent.current_generation_id != expected_generation_id:
            return None
        for child in self.associated_states(context, instance_id):
            self.expire_state(context, child.instance_id, reason=reason)
        return super().expire_state(context, instance_id,
            expected_generation_id=expected_generation_id, reason=reason)

    def _commit_expiry_batch(self, context: BattleContext, instances, **kwargs) -> list[StateInstance]:
        expanded = {s.instance_id: s for s in instances if s.instance_id in context.states}
        pending = list(expanded)
        while pending:
            for child in self.associated_states(context, pending.pop()):
                if child.instance_id not in expanded:
                    expanded[child.instance_id] = child
                    pending.append(child.instance_id)
        return super()._commit_expiry_batch(context, expanded.values(), **kwargs)

    def apply(self, context: BattleContext, **kwargs) -> StateInstance:
        self._applying = True
        try:
            result = super().apply(context, **kwargs)
        finally:
            self._applying = False
        if self.reaction_port is not None:
            self.reaction_port(context, result)
        return result

    def refresh(self, context: BattleContext, **kwargs) -> StateInstance:
        result = super().refresh(context, **kwargs)
        if not self._applying and self.reaction_port is not None:
            self.reaction_port(context, result)
        return result
