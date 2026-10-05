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
from .dependency_evaluation import ProviderNode
from .enums import DamageType
from .execution_right_system import AssaultDispatchPort
from .numeric_validation import validate_probability, validate_nonnegative_finite
from .attribute_choice import higher_force_intelligence
from .priority_target_system import FastestTargetSystem
from .stage9_integerization import ExactRatio
from .stage10_state_params import ContinuousDamageStateParams, RecoveryPotencyContext
from .skill_definition import RecoverySkillEffectSpec
from .stage11_state_runtime import Stage11DamageFamily
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
            object.__setattr__(
                self,
                "continuous_damage_coefficient",
                validate_nonnegative_finite(
                    self.continuous_damage_coefficient,
                    "continuous_damage_coefficient",
                ),
            )
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
        if (
            isinstance(self.damage, TargetStateBranchFollowup)
            and self.target_mode is not FollowupTargetMode.INHERIT_ACTUAL_TARGET
        ):
            raise ValueError("target-state branch requires inherited actual target")


@dataclass(frozen=True, slots=True)
class BranchedNormalAttackFollowupParams(NormalAttackFollowupParams):
    recovery_potency: RecoveryPotencyContext | None = None
    fastest_only: bool = False
    higher_attribute_damage: bool = False
    speed_damage_ratio: float = 0.0
    tie_damage_type: DamageType | None = None
    fixed_performer_id: str | None = None
    recovery_from_performer: bool = False
    live_recovery_attribute: bool = False
    damage_family: Stage11DamageFamily | None = None

    def __post_init__(self):
        NormalAttackFollowupParams.__post_init__(self)
        if self.recovery_potency is not None and not isinstance(self.recovery_potency, RecoveryPotencyContext):
            raise TypeError("recovery_potency must be RecoveryPotencyContext or None")
        if type(self.fastest_only) is not bool or type(self.higher_attribute_damage) is not bool:
            raise TypeError("followup conditions must be bool")
        if self.tie_damage_type is not None and not isinstance(self.tie_damage_type, DamageType):
            raise TypeError("tie_damage_type must be DamageType or None")
        if self.fixed_performer_id is not None and (not isinstance(self.fixed_performer_id, str)
                or not self.fixed_performer_id.strip()):
            raise ValueError("fixed_performer_id must be a nonempty string or None")
        if type(self.recovery_from_performer) is not bool:
            raise TypeError("recovery_from_performer must be bool")
        if type(self.live_recovery_attribute) is not bool:
            raise TypeError("live_recovery_attribute must be bool")
        if self.damage_family is not None and not isinstance(self.damage_family, Stage11DamageFamily):
            raise TypeError("damage_family must be Stage11DamageFamily or None")
        object.__setattr__(self, "speed_damage_ratio", validate_nonnegative_finite(
            self.speed_damage_ratio, "speed_damage_ratio"))


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
    def __init__(
        self,
        gate,
        resolver,
        executor,
        state_policy,
        *,
        targets=None,
        attributes=None,
        treatment_formula=None,
        basis_producer=None,
        recovery_system=None,
        lifecycle_system=None,
    ):
        super().__init__(gate)
        self._resolver = resolver
        self._executor = executor
        self._state_policy = state_policy
        self._targets = targets
        self._attributes = attributes
        self._treatment_formula = treatment_formula
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
            if isinstance(params, BranchedNormalAttackFollowupParams):
                self._dispatch_branch(context, state, params, provider, actor, actual_target_id)
                continue
            if isinstance(params.damage, TargetStateBranchFollowup):
                self._dispatch_target_state_branch(
                    context,
                    state,
                    params,
                    provider,
                    actor,
                    actual_target_id,
                )
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


    def _dispatch_target_state_branch(
        self,
        context,
        state,
        params,
        provider,
        actor,
        actual_target_id,
    ):
        branch = params.damage
        if not isinstance(branch, TargetStateBranchFollowup):
            raise TypeError("target-state branch dispatch requires TargetStateBranchFollowup")

        target_has_state = bool(
            self._state_policy.effective_instances(
                context,
                actual_target_id,
                branch.state_id,
            )
        )
        definition = SkillDefinition(
            state.source_skill_id,
            provider.definition.name,
            params.probability,
            SkillTargetMode.SINGLE_RANDOM_ENEMY,
            (branch.damage,),
            skill_type=SkillType.TROOP,
        )
        runtime = SkillRuntime(
            definition,
            provider.owner_id,
            provider.skill_slot,
            provider.enabled,
        )
        result = self._resolver(
            context,
            runtime,
            inherited_target_ids=(actual_target_id,),
        )
        if result.effects and not target_has_state:
            self._apply_continuous_state(
                context,
                actor,
                state,
                branch,
                actual_target_id,
            )
            return

        for effect in result.effects:
            effect = replace(
                effect,
                source_id=actor.unit_id,
                source_state_id=state.state_id,
                source_state_instance_id=state.instance_id,
                source_ref=EffectSourceRef(
                    SourceType.ACTIVE_SKILL,
                    source_unit_id=actor.unit_id,
                    source_skill_id=state.source_skill_id,
                ),
            )
            execution = self._executor(context, effect)
            if not isinstance(execution, DamageEffectResult) or not actor.is_alive:
                continue
            ratio = branch.recovery_ratio
            if ratio.numerator == 0:
                continue
            if self._recovery is None:
                raise RuntimeError(
                    "damage-derived recovery requires canonical recovery system"
                )
            basis = execution.resolution.assigned_target_damage
            amount = (
                basis * ratio.numerator + ratio.denominator - 1
            ) // ratio.denominator
            if amount:
                self._recovery.resolve(
                    context,
                    RecoveryRequest(
                        actor.unit_id,
                        actor.unit_id,
                        amount,
                        source_skill_id=state.source_skill_id,
                        source_state_id=state.state_id,
                        source_state_instance_id=state.instance_id,
                        source_generation_id=state.current_generation_id,
                        modifier_policy=RecoveryModifierPolicy.APPLY,
                    ),
                )

    def _apply_continuous_state(
        self,
        context,
        actor,
        provider_state,
        branch,
        target_id,
    ):
        if branch.continuous_damage_coefficient is None:
            raise NotImplementedError(
                "continuous followup rate requires a confirmed coefficient"
            )
        if self._basis_producer is None or self._lifecycle is None:
            raise RuntimeError(
                "continuous followup requires canonical basis and lifecycle owners"
            )
        basis = self._basis_producer.capture(
            context,
            ContinuousDamageApplicationRequest(
                source_id=actor.unit_id,
                target_id=target_id,
                state_id=branch.state_id,
                application_generation_id=context.generation_allocator.allocate(
                    prefix="capture"
                ),
                coefficient=branch.continuous_damage_coefficient,
                source_skill_id=provider_state.source_skill_id,
            ),
        )
        window = self._lifecycle.calculate_lifecycle_window(
            context,
            owner_id=target_id,
            duration_rounds=branch.duration,
        )
        self._executor(
            context,
            ApplyStateEffect(
                branch.state_id,
                target_id,
                source_id=actor.unit_id,
                source_skill_id=provider_state.source_skill_id,
                expires_round=window.last_eligible_round + 1,
                expires_phase="ROUND_START",
                runtime_params=ContinuousDamageStateParams(
                    lifecycle_window=window,
                    frozen_damage_basis=basis,
                ),
                source_ref=EffectSourceRef(
                    SourceType.ACTIVE_SKILL,
                    source_unit_id=actor.unit_id,
                    source_skill_id=provider_state.source_skill_id,
                ),
            ),
        )

    def _dispatch_branch(self, context, state, params, provider, actor, actual_target_id):
        ref = SkillProviderRef(provider.owner_id, provider.skill_slot, state.source_skill_id)
        if not self._state_policy.dependency_support.evaluate(context, ProviderNode(ref)).valid:
            return
        if not context.units[provider.owner_id].is_alive:
            return
        if params.fixed_performer_id is not None and actor.unit_id != params.fixed_performer_id:
            return
        if params.fastest_only:
            fastest = FastestTargetSystem(self._targets).fastest_allies(context, actor, self._attributes)
            if actor not in fastest:
                return
            if len(fastest) != 1:
                raise NotImplementedError("equal maximum-speed followup performer rule is unconfirmed")
        # One mutually exclusive branch draw, before fresh target selection.
        damage_branch = context.random.chance(params.probability)
        if damage_branch:
            damage = params.damage
            if params.higher_attribute_damage:
                choice = higher_force_intelligence(
                    self._attributes.get_attack(context, actor),
                    self._attributes.get_intelligence(context, actor), tie_type=params.tie_damage_type)
                damage = replace(damage, damage_type=choice.damage_type)
            mode, specs, count = SkillTargetMode.SINGLE_RANDOM_ENEMY, (damage,), None
            inherited = ((actual_target_id,) if params.target_mode is FollowupTargetMode.INHERIT_ACTUAL_TARGET
                         else None)
        else:
            potency = params.recovery_potency
            if potency is None:
                raise ValueError("recovery branch requires application-time potency snapshot")
            recovery_source = actor if params.recovery_from_performer else context.units[provider.owner_id]
            attribute = (max(self._attributes.get_attack(context, recovery_source),
                             self._attributes.get_intelligence(context, recovery_source))
                         if params.live_recovery_attribute else potency.frozen_treatment_attribute())
            amount = self._treatment_formula.calculate(rate=potency.base_rate,
                source_troops=potency.source_troops_at_application,
                source_attribute=attribute,
                modifiers=potency.treatment_modifier_snapshot).nominal_recovery
            mode, specs, count = SkillTargetMode.CHOOSE_N_RANDOM_TEAM, (RecoverySkillEffectSpec(amount),), 1
            inherited = None
        definition = SkillDefinition(state.source_skill_id, provider.definition.name, 1.0,
            mode, specs, skill_type=SkillType.TROOP, target_count=count)
        runtime = SkillRuntime(definition, provider.owner_id, provider.skill_slot, provider.enabled)
        result = self._resolver(context, runtime, inherited_target_ids=inherited)
        for effect in result.effects:
            if damage_branch:
                effect = replace(effect, source_id=actor.unit_id,
                    stage11_family=params.damage_family,
                    additive_damage=self._attributes.get_speed(context, actor) * params.speed_damage_ratio,
                    source_state_id=state.state_id, source_state_instance_id=state.instance_id,
                    source_ref=EffectSourceRef(SourceType.ACTIVE_SKILL,
                        source_unit_id=actor.unit_id, source_skill_id=state.source_skill_id))
            else:
                effect = replace(effect, source_id=actor.unit_id if params.recovery_from_performer else effect.source_id,
                    source_state_id=state.state_id,
                    source_state_instance_id=state.instance_id)
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
