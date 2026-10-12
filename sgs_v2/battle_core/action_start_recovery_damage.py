"""State-backed action-start damage using a snapshot of settled team recovery.

No EventBus callbacks: read already-settled recovery facts at a typed hook.
The cursor is consumed before damage execution; recovery caused during the
effect batch stays after that boundary and therefore belongs to the next batch.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from .context import BattleContext
from .effects import EffectSourceRef
from .effect_result import DamageDeniedEffectResult, EffectExecutionResult
from .enums import DamageType
from .events import EventType
from .execution_right_runtime import CurrentActorPermissionRequest, CurrentActorPermissionStatus, DamageWorkKind
from .numeric_validation import validate_probability, validate_nonnegative_finite
from .operation_identity import SourceType
from .provider_identity import SkillProviderRef
from .rule_hooks import RuleHook, UnitActionStartHook
from .rule_hook_system import HookResolutionResult, RuleHookSystem
from .skill_definition import DamageSkillEffectSpec, SkillDefinition, SkillTargetMode, SkillType
from .skill_resolver import SkillResolutionStatus
from .skill_runtime import SkillRuntime
from .stage9_integerization import ExactRatio
from .state_runtime_params import StateRuntimeParams

if TYPE_CHECKING:
    from .battle_systems import BattleSystems

ACTION_START_RECOVERY_DAMAGE_STATE_ID = 'runtime_action_start_recovery_damage'
RECOVERY_DAMAGE_CURSORS_KEY = 'action_start_recovery_damage_cursors'


@dataclass(frozen=True, slots=True)
class ActionStartRecoveryDamageParams(StateRuntimeParams):
    probability: float
    damage_type: DamageType
    coefficient: float
    target_count: int
    recovery_damage_ratio: ExactRatio
    basis_model_key: str
    after_sequence: int = 0

    def __post_init__(self):
        object.__setattr__(self, 'probability', validate_probability(self.probability, 'probability'))
        object.__setattr__(self, 'coefficient', validate_nonnegative_finite(self.coefficient, 'coefficient'))
        if not isinstance(self.damage_type, DamageType):
            raise TypeError('damage_type must be DamageType')
        for key in ('target_count', 'after_sequence'):
            value = getattr(self, key)
            if type(value) is not int or value < (1 if key == 'target_count' else 0):
                raise ValueError(f'{key} must be a valid nonnegative integer')
        if not isinstance(self.recovery_damage_ratio, ExactRatio):
            raise TypeError('recovery_damage_ratio must be ExactRatio')
        if self.recovery_damage_ratio.numerator < 0:
            raise ValueError('recovery_damage_ratio must be nonnegative')
        if not isinstance(self.basis_model_key, str) or not self.basis_model_key.strip():
            raise ValueError('basis_model_key must be nonempty')


@dataclass(frozen=True, slots=True)
class SettledRecoverySnapshot:
    actual_recovery: int
    event_sequences: tuple[int, ...]
    through_sequence: int


@dataclass(frozen=True, slots=True)
class RecoveryDamageCursor:
    """Battle-scoped execution bookkeeping, not physical unit state mutation."""
    after_sequence: int
    last_attempt_round: int = 0


def recovery_damage_cursor(context: BattleContext, state) -> RecoveryDamageCursor:
    book = context.metadata.get(RECOVERY_DAMAGE_CURSORS_KEY, {})
    if not isinstance(book, dict):
        raise TypeError('recovery damage cursor book must be dict')
    key = f'{state.instance_id}:{state.current_generation_id}'
    cursor = book.get(key, RecoveryDamageCursor(state.runtime_params.after_sequence))
    if not isinstance(cursor, RecoveryDamageCursor):
        raise TypeError('recovery damage cursor must be typed')
    return cursor


def project_settled_team_recovery(context: BattleContext, *, team_id: str,
                                  after_sequence: int) -> SettledRecoverySnapshot:
    """Count team-caused actual healing once; exclude nominal/prevented facts."""
    history = context.event_bus.history
    cutoff = history[-1].sequence if history else 0
    total = 0
    sequences = []
    for event in history:
        if event.sequence <= after_sequence or event.event_type is not EventType.TROOPS_RECOVERED:
            continue
        source = context.units.get(event.actor_id)
        if source is None or source.team_id != team_id:
            continue
        amount = event.payload['actual_recovery']
        if type(amount) is not int or amount < 0:
            raise ValueError('settled recovery requires nonnegative integer actual_recovery')
        total += amount
        sequences.append(event.sequence)
    return SettledRecoverySnapshot(total, tuple(sequences), cutoff)


class ActionStartRecoveryDamageSupport:
    def __init__(self, systems: BattleSystems):
        self._systems = systems

    def execute(self, context: BattleContext, hook: UnitActionStartHook) -> tuple[EffectExecutionResult, ...]:
        s = self._systems
        if context.ended or s.finalization_coordinator.is_latched_or_finalized:
            return ()
        actor = context.get_unit(hook.actor_id)
        states = s.state_effectiveness_policy.effective_instances(
            context, actor.unit_id, ACTION_START_RECOVERY_DAMAGE_STATE_ID)
        results = []
        for state in states:
            if context.ended or s.finalization_coordinator.is_latched_or_finalized:
                break
            params = state.runtime_params
            if not isinstance(params, ActionStartRecoveryDamageParams):
                raise TypeError('action-start recovery damage requires typed parameters')
            cursor = recovery_damage_cursor(context, state)
            if cursor.last_attempt_round == hook.round_no:
                continue
            if state.source_skill_slot is None:
                raise ValueError('action-start damage requires a canonical provider slot')
            ref = SkillProviderRef(state.source_id, state.source_skill_slot, state.source_skill_id)
            if not s.provider_validity_policy.evaluate_provider(context, ref).valid:
                continue
            provider_unit = context.get_unit(state.source_id)
            if not provider_unit.is_alive or not actor.is_alive:
                continue
            actor_right = s.current_actor_permission_policy.evaluate(context,
                CurrentActorPermissionRequest(actor.unit_id, DamageWorkKind.NEW_ACTOR_DRIVEN_DAMAGE.value))
            if actor_right.status is CurrentActorPermissionStatus.UNSUPPORTED_BOUNDARY:
                raise RuntimeError('action-start damage actor permission unsupported')
            if not actor_right.allowed:
                continue
            snapshot = project_settled_team_recovery(context, team_id=actor.team_id,
                                                     after_sequence=cursor.after_sequence)
            provider = context.skill_runtimes.lookup(ref.owner_id, ref.skill_slot, ref.skill_id)
            definition = SkillDefinition(ref.skill_id, provider.definition.name, params.probability,
                SkillTargetMode.CHOOSE_N_RANDOM_ENEMIES,
                (DamageSkillEffectSpec(params.damage_type, params.coefficient),),
                skill_type=SkillType.TROOP, target_count=params.target_count)
            runtime = SkillRuntime(definition, provider.owner_id, provider.skill_slot, provider.enabled)
            resolution = s.skill_resolver.resolve(context, runtime)
            # Failure/no target preserves accumulated recovery, but a repeated
            # call for this actor in the same round cannot mint another attempt.
            next_cursor = replace(cursor, last_attempt_round=hook.round_no)
            if resolution.status is SkillResolutionStatus.RESOLVED:
                next_cursor = replace(next_cursor, after_sequence=snapshot.through_sequence)
            # Physical states stay immutable. The existing lifecycle contract
            # deliberately permits runtime-param maintenance only for selected
            # official states. Per-battle execution cursors therefore live in
            # BattleContext.metadata, keyed by state identity AND generation.
            book = context.metadata.setdefault(RECOVERY_DAMAGE_CURSORS_KEY, {})
            book[f'{state.instance_id}:{state.current_generation_id}'] = next_cursor
            if resolution.status is not SkillResolutionStatus.RESOLVED:
                continue
            addition = (snapshot.actual_recovery * params.recovery_damage_ratio.numerator
                        / params.recovery_damage_ratio.denominator)
            context.event_bus.publish(event_type=EventType.DAMAGE_RESOLVED,
                phase=context.current_phase, round_no=context.current_round,
                actor_id=actor.unit_id, payload={'event_kind': 'ACCUMULATED_RECOVERY_SNAPSHOT',
                    'source_skill_id': ref.skill_id, 'provider_id': ref.owner_id,
                    'basis_model_key': params.basis_model_key,
                    'actual_recovery_snapshot': snapshot.actual_recovery,
                    'recovery_event_sequences': snapshot.event_sequences,
                    'through_sequence': snapshot.through_sequence,
                    'target_ids': resolution.target_ids, 'coefficient': params.coefficient,
                    'final_additive_damage_per_target': addition,
                    'reset_policy': 'CONSUME_BEFORE_DAMAGE; DURING_DAMAGE_RECOVERY_NEXT_BATCH'})
            for effect in resolution.effects:
                if context.ended or s.finalization_coordinator.is_latched_or_finalized:
                    break
                # The provider owns selection/admission; the state holder is the
                # performer. Never fabricate a provider slot on a teammate.
                adapted = replace(effect, source_id=actor.unit_id, source_state_id=state.state_id,
                    source_state_instance_id=state.instance_id,
                    source_ref=EffectSourceRef(SourceType.ACTIVE_SKILL,
                        source_unit_id=actor.unit_id, source_skill_id=ref.skill_id),
                    final_additive_damage=addition)
                results.append(s.effect_executor.execute(context, adapted))
        return tuple(results)


class AccumulatedRecoveryRuleHookSystem(RuleHookSystem):
    """Compose opt-in action-start work after the unchanged ordinary hook batch."""
    def __init__(self, trigger_system, effect_executor, support: ActionStartRecoveryDamageSupport):
        super().__init__(trigger_system, effect_executor)
        self._support = support

    def process(self, context: BattleContext, hook: RuleHook) -> HookResolutionResult:
        ordinary = super().process(context, hook)
        if not isinstance(hook, UnitActionStartHook) or ordinary.batch_status != 'COMPLETED':
            return ordinary
        results = self._support.execute(context, hook)
        return replace(ordinary, intent_results=ordinary.intent_results + results,
                       effect_results=ordinary.effect_results + tuple(
                           r for r in results if not isinstance(r, DamageDeniedEffectResult)))
