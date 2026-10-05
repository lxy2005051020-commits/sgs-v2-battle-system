"""State-backed followups composed at the existing, permit-gated normal-hit seam.

No EventBus callbacks, troop mutations, damage formulas or recursive normal hits.
The provider selects the fresh skill target; the physical attacker supplies damage
attributes and receives attacker recovery. Provider and performer stay distinct.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from .effects import ApplyStateEffect, EffectSourceRef
from .effect_result import DamageEffectResult
from .continuous_damage_basis_producer import ContinuousDamageApplicationRequest
from .recovery_system import RecoveryModifierPolicy, RecoveryRequest
from .numeric_validation import validate_nonnegative_finite
from .stage9_integerization import ExactRatio
from .stage10_state_params import ContinuousDamageStateParams
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
class TargetStateBranchFollowup:
    """Inherited-target branch: existing state -> damage, otherwise install DOT.

    Recovery uses the settled followup damage amount and CEIL. Concrete tactics
    must explicitly authorize this basis; it is not inferred from troop loss.
    """

    state_id: str
    damage: DamageSkillEffectSpec
    duration: int
    continuous_damage_coefficient: float | None = None
    recovery_ratio: ExactRatio = ExactRatio(0)

    def __post_init__(self) -> None:
        if not isinstance(self.state_id, str) or not self.state_id.strip():
            raise ValueError("state_id must be non-empty")
        if not isinstance(self.damage, DamageSkillEffectSpec):
            raise TypeError("damage must be DamageSkillEffectSpec")
        if isinstance(self.duration, bool) or not isinstance(self.duration, int):
            raise TypeError("duration must be int")
        if self.duration < 1:
            raise ValueError("duration must be positive")
        if self.continuous_damage_coefficient is not None:
            object.__setattr__(self, "continuous_damage_coefficient", validate_nonnegative_finite(
                self.continuous_damage_coefficient, "continuous_damage_coefficient"))
        if not isinstance(self.recovery_ratio, ExactRatio):
            raise TypeError("recovery_ratio must be ExactRatio")
        if not 0 <= self.recovery_ratio.numerator <= self.recovery_ratio.denominator:
            raise ValueError("recovery_ratio must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class NormalAttackFollowupParams(StateRuntimeParams):
    probability: float
    damage: DamageSkillEffectSpec | TargetStateBranchFollowup
    target_mode: FollowupTargetMode

    def __post_init__(self) -> None:
        object.__setattr__(self, "probability", validate_probability(self.probability, "probability"))
        if not isinstance(self.damage, (DamageSkillEffectSpec, TargetStateBranchFollowup)):
            raise TypeError("damage must be DamageSkillEffectSpec or TargetStateBranchFollowup")
        if not isinstance(self.target_mode, FollowupTargetMode):
            raise TypeError("target_mode must be FollowupTargetMode")
        if isinstance(self.damage, TargetStateBranchFollowup) and self.target_mode is not FollowupTargetMode.INHERIT_ACTUAL_TARGET:
            raise ValueError("target-state branch requires inherited actual target")


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
    def __init__(self, gate, resolver, executor, state_policy, *, basis_producer=None, recovery_system=None,
                 lifecycle_system=None):
        super().__init__(gate)
        self._resolver = resolver
        self._executor = executor
        self._state_policy = state_policy
        self._basis_producer = basis_producer
        self._recovery = recovery_system
        self._lifecycle = lifecycle_system

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
            branch = params.damage if isinstance(params.damage, TargetStateBranchFollowup) else None
            target_has_state = branch is not None and bool(self._state_policy.effective_instances(
                context, actual_target_id, branch.state_id))
            definition = SkillDefinition(state.source_skill_id, provider.definition.name,
                params.probability, SkillTargetMode.SINGLE_RANDOM_ENEMY,
                (branch.damage if branch is not None else params.damage,),
                skill_type=SkillType.TROOP)
            runtime = SkillRuntime(definition, provider.owner_id, provider.skill_slot, provider.enabled)
            inherited = ((actual_target_id,) if params.target_mode is FollowupTargetMode.INHERIT_ACTUAL_TARGET
                         else None)
            result = self._resolver(context, runtime, inherited_target_ids=inherited)
            if branch is not None and result.effects and not target_has_state:
                self._apply_continuous_state(context, actor, state, branch, actual_target_id)
                continue
            for effect in result.effects:
                # No fabricated skill slot on a teammate. The mounted state retains
                # the original provider; damage attribution belongs to its performer.
                effect = replace(effect, source_id=actor.unit_id,
                    source_state_id=state.state_id, source_state_instance_id=state.instance_id,
                    source_ref=EffectSourceRef(SourceType.ACTIVE_SKILL,
                        source_unit_id=actor.unit_id, source_skill_id=state.source_skill_id))
                execution = self._executor(context, effect)
                if branch is not None and isinstance(execution, DamageEffectResult) and actor.is_alive:
                    if self._recovery is None and branch.recovery_ratio.numerator:
                        raise RuntimeError("damage-derived recovery requires canonical recovery system")
                    ratio = branch.recovery_ratio
                    basis = execution.resolution.assigned_target_damage
                    amount = (basis * ratio.numerator + ratio.denominator - 1) // ratio.denominator
                    if amount:
                        self._recovery.resolve(context, RecoveryRequest(
                            actor.unit_id, actor.unit_id, amount,
                            source_skill_id=state.source_skill_id,
                            source_state_id=state.state_id, source_state_instance_id=state.instance_id,
                            source_generation_id=state.current_generation_id,
                            modifier_policy=RecoveryModifierPolicy.APPLY))

    def _apply_continuous_state(self, context, actor, provider_state, branch, target_id):
        if branch.continuous_damage_coefficient is None:
            raise NotImplementedError("continuous followup rate requires a confirmed coefficient")
        if self._basis_producer is None or self._lifecycle is None:
            raise RuntimeError("continuous followup requires canonical basis and lifecycle owners")
        # DOT source and frozen formula belong to the physical attacker. Provider
        # identity remains on the mounted followup; never fabricate its skill slot
        # on a teammate. This persistent DOT uses the existing always-active gate.
        basis = self._basis_producer.capture(context, ContinuousDamageApplicationRequest(
            source_id=actor.unit_id, target_id=target_id, state_id=branch.state_id,
            application_generation_id=context.generation_allocator.allocate(prefix="capture"),
            coefficient=branch.continuous_damage_coefficient,
            source_skill_id=provider_state.source_skill_id))
        window = self._lifecycle.calculate_lifecycle_window(
            context, owner_id=target_id, duration_rounds=branch.duration)
        self._executor(context, ApplyStateEffect(
            branch.state_id, target_id, source_id=actor.unit_id,
            source_skill_id=provider_state.source_skill_id,
            expires_round=window.last_eligible_round + 1, expires_phase="ROUND_START",
            runtime_params=ContinuousDamageStateParams(lifecycle_window=window, frozen_damage_basis=basis),
            source_ref=EffectSourceRef(SourceType.ACTIVE_SKILL,
                source_unit_id=actor.unit_id, source_skill_id=provider_state.source_skill_id)))


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
