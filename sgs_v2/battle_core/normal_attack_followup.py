"""State-backed followups composed at the existing, permit-gated normal-hit seam.

No EventBus callbacks, troop mutations, damage formulas or recursive normal hits.
The provider selects the fresh skill target; the physical attacker supplies damage
attributes and receives attacker recovery. Provider and performer stay distinct.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from .effects import EffectSourceRef
from .dependency_evaluation import ProviderNode
from .enums import DamageType
from .execution_right_system import AssaultDispatchPort
from .numeric_validation import validate_probability
from .official_state_catalog import OfficialStateId
from .operation_identity import SourceType
from .provider_identity import SkillProviderRef
from .skill_definition import DamageSkillEffectSpec, SkillDefinition, SkillTargetMode, SkillType
from .skill_runtime import SkillRuntime
from .stage9_state_params import ComboStateParams
from .stage9_state_runtime import Stage9StateRuntime
from .state_definition import StateDefinition
from .state_runtime_params import StateRuntimeParams

NORMAL_ATTACK_FOLLOWUP_STATE_ID = "runtime_normal_attack_followup"


class FollowupTargetMode(str, Enum):
    INHERIT_ACTUAL_TARGET = "INHERIT_ACTUAL_TARGET"
    RANDOM_ENEMY = "RANDOM_ENEMY"


@dataclass(frozen=True, slots=True)
class NormalAttackFollowupParams(StateRuntimeParams):
    probability: float
    damage: DamageSkillEffectSpec
    target_mode: FollowupTargetMode

    def __post_init__(self) -> None:
        object.__setattr__(self, "probability", validate_probability(self.probability, "probability"))
        if not isinstance(self.damage, DamageSkillEffectSpec):
            raise TypeError("damage must be DamageSkillEffectSpec")
        if not isinstance(self.target_mode, FollowupTargetMode):
            raise TypeError("target_mode must be FollowupTargetMode")


@dataclass(frozen=True, slots=True)
class ProbabilisticComboParams(ComboStateParams):
    probability: float = 1.0

    def __post_init__(self) -> None:
        ComboStateParams.__post_init__(self)
        object.__setattr__(self, "probability", validate_probability(self.probability, "probability"))


FOLLOWUP_STATE_DEFINITION = StateDefinition(
    NORMAL_ATTACK_FOLLOWUP_STATE_ID, "普攻后追加伤害", runtime_params_type=NormalAttackFollowupParams)


def register_followup_state_definition(registry) -> None:
    try:
        resident = registry.get_definition(NORMAL_ATTACK_FOLLOWUP_STATE_ID)
    except KeyError:
        registry.register_definition(FOLLOWUP_STATE_DEFINITION)
    else:
        if resident != FOLLOWUP_STATE_DEFINITION:
            raise ValueError("incompatible followup state schema")


class NormalAttackFollowupPort(AssaultDispatchPort):
    def __init__(self, gate, resolver, executor, state_policy):
        super().__init__(gate)
        self._resolver = resolver
        self._executor = executor
        self._state_policy = state_policy

    def dispatch(self, context, permit, parent_scope_identity, *, actor, actual_target_id):
        # Frozen owner validates and consumes the authentic permit before gameplay.
        super().dispatch(context, permit, parent_scope_identity,
                         actor=actor, actual_target_id=actual_target_id)
        for state in self._state_policy.effective_instances(context, actor.unit_id,
                                                          NORMAL_ATTACK_FOLLOWUP_STATE_ID):
            if context.ended or not actor.is_alive or self.gate.coordinator.is_latched_or_finalized:
                break
            params = state.runtime_params
            if state.source_id is None or state.source_skill_slot is None:
                raise ValueError("followup requires canonical provider provenance")
            provider = context.skill_runtimes.get(state.source_id, state.source_skill_slot)
            if provider is None or provider.definition.skill_id != state.source_skill_id:
                continue
            definition = SkillDefinition(state.source_skill_id, provider.definition.name,
                params.probability, SkillTargetMode.SINGLE_RANDOM_ENEMY, (params.damage,),
                skill_type=SkillType.TROOP)
            runtime = SkillRuntime(definition, provider.owner_id, provider.skill_slot, provider.enabled)
            inherited = ((actual_target_id,) if params.target_mode is FollowupTargetMode.INHERIT_ACTUAL_TARGET
                         else None)
            result = self._resolver(context, runtime, inherited_target_ids=inherited)
            for effect in result.effects:
                # No fabricated skill slot on a teammate. The mounted state retains
                # the original provider; damage attribution belongs to its performer.
                effect = replace(effect, source_id=actor.unit_id,
                    source_state_id=state.state_id, source_state_instance_id=state.instance_id,
                    source_ref=EffectSourceRef(SourceType.ACTIVE_SKILL,
                        source_unit_id=actor.unit_id, source_skill_id=state.source_skill_id))
                self._executor(context, effect)


class ProbabilisticComboRuntime(Stage9StateRuntime):
    """Opt-in action grant probability; frozen ActionSystem still owns the grant."""

    def get_operational_combo(self, context, unit_id):
        instance = super().get_operational_combo(context, unit_id)
        if instance is None or not isinstance(instance.runtime_params, ProbabilisticComboParams):
            return instance
        if not self._state_effectiveness_policy.evaluate_state(context, instance).effective:
            return None
        if instance.source_id is None or instance.source_skill_slot is None or instance.source_skill_id is None:
            raise ValueError("probabilistic combo requires canonical provider provenance")
        provider = SkillProviderRef(instance.source_id, instance.source_skill_slot, instance.source_skill_id)
        if not self._state_effectiveness_policy.dependency_support.evaluate(context, ProviderNode(provider)).valid:
            return None
        probability = instance.runtime_params.probability
        if probability == 0 or (probability < 1 and not context.random.chance(probability)):
            return None
        return instance
