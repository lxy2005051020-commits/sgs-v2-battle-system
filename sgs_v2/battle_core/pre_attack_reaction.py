"""State-backed team reactions after canonical target resolution, before a hit.

Selection, attributes, damage, execution rights and finalization stay with their
existing owners. Budgets live in immutable per-battle state parameters.
"""
from dataclasses import dataclass, replace
from fractions import Fraction

from .dependency_evaluation import StateNode, ProviderNode
from .damage_system import DamageRequest
from .enums import DamageType, DamageSourceType, LineupPosition
from .events import EventType
from .execution_right_system import FutureBranchKind
from .execution_right_runtime import (DamageExecutionWork, DamageWorkKind,
    ExecutionRightSpec, ExecutionRightMode, ExecutionRightRequest, ExecutionRightEvaluationStatus)
from .operation_identity import OperationLineage, SourceType
from .provider_identity import SkillProviderRef
from .state_definition import StateDefinition
from .state_runtime_params import StateRuntimeParams
from .state_modifiers import ATTRIBUTE_BONUS_STATE_ID, AttributeBonusParams
from .target_resolution_system import TargetResolutionSystem

PRE_ATTACK_REACTION_STATE_ID = "runtime_team_pre_attack_reaction"


def loss_rate_bonus(initial_troops: int, current_troops: int, step: int = 250,
                    cap_steps: int = 40) -> Fraction:
    """User provisional model: each full loss step adds one rate point."""
    if any(type(v) is not int for v in (initial_troops, current_troops, step, cap_steps)):
        raise TypeError("troop and step values must be integers")
    if initial_troops < 0 or current_troops < 0 or step <= 0 or cap_steps < 0:
        raise ValueError("invalid troop-loss model parameters")
    return Fraction(min(max(0, initial_troops - current_troops) // step, cap_steps), 100)


@dataclass(frozen=True, slots=True)
class TeamPreAttackReactionParams(StateRuntimeParams):
    attribute_increment: int = 12
    max_stacks: int = 5
    base_rate: Fraction = Fraction(72, 100)
    loss_step: int = 250
    max_loss_steps: int = 40
    initial_troops: tuple[tuple[str, int], ...] = ()
    stacks: tuple[tuple[str, int], ...] = ()
    last_round: int = -1

    def __post_init__(self):
        for name in ("attribute_increment", "max_stacks", "loss_step", "max_loss_steps"):
            value = getattr(self, name)
            if type(value) is not int or value < 0 or (name == "loss_step" and value == 0):
                raise ValueError(f"invalid {name}")
        if not isinstance(self.base_rate, Fraction) or self.base_rate < 0:
            raise ValueError("base_rate must be a nonnegative Fraction")


REACTION_DEFINITION = StateDefinition(PRE_ATTACK_REACTION_STATE_ID,
    "友军主将受普攻前反应", runtime_params_type=TeamPreAttackReactionParams)


def register_pre_attack_reaction_definition(registry):
    try:
        resident = registry.get_definition(PRE_ATTACK_REACTION_STATE_ID)
    except KeyError:
        registry.register_definition(REACTION_DEFINITION)
    else:
        if resident != REACTION_DEFINITION:
            raise ValueError("incompatible pre-attack reaction schema")


class TeamPreAttackReactionSupport:
    def __init__(self, systems):
        self.systems = systems

    def react(self, context, attacker, target, normal_attack_id):
        s = self.systems
        if target.lineup_position is not LineupPosition.COMMANDER:
            return
        for marker in s.state_effectiveness_policy.effective_instances(
                context, target.unit_id, PRE_ATTACK_REACTION_STATE_ID):
            params = marker.runtime_params
            if params.last_round == context.current_round:
                continue
            if marker.source_id is None or marker.source_skill_slot is None:
                raise ValueError("pre-attack reaction requires canonical provider")
            if not context.units[marker.source_id].is_alive:
                continue
            provider = SkillProviderRef(marker.source_id, marker.source_skill_slot, marker.source_skill_id)
            if not s.dependency_evaluation_support.evaluate(context, ProviderNode(provider)).valid:
                continue
            deputies = sorted((u for u in s.target_system.allies(context, target)
                if u.lineup_position in (LineupPosition.DEPUTY_1, LineupPosition.DEPUTY_2)),
                key=lambda u: u.lineup_position)
            if not deputies:
                continue
            parent = str(normal_attack_id)
            permit = s.future_admission_gate.request_admission(FutureBranchKind.COUNTER_BATCH, parent)
            if permit is None:
                return
            s.future_admission_gate.consume_permit(permit, FutureBranchKind.COUNTER_BATCH, parent)
            batch_id = context.id_allocator.allocate_reaction_batch_id()
            capability = object()
            finalization = s.finalization_coordinator
            finalization._register_reaction(context, batch_id, capability)
            finalization.start_reaction(context, batch_id, capability)
            stacks = dict(params.stacks)
            try:
                # Reserve the round before dispatch so nested reactions cannot repeat.
                s.state_lifecycle_system.refresh(context, instance_id=marker.instance_id,
                    runtime_params=replace(params, last_round=context.current_round))
                for deputy in deputies:
                    if not deputy.is_alive:
                        continue
                    work = DamageExecutionWork(DamageWorkKind.COUNTER_DAMAGE,
                        ExecutionRightSpec(actor_permission=ExecutionRightMode.RECHECK_AT_EXECUTION),
                        ExecutionRightRequest(current_actor_id=deputy.unit_id,
                            actor_operation_kind=DamageWorkKind.COUNTER_DAMAGE.value,
                            historical_source_id=marker.source_id, damage_source_id=deputy.unit_id,
                            credit_owner_id=deputy.unit_id))
                    right = s.damage_instance_coordinator.evaluate_execution_right(context, work)
                    if right.status is ExecutionRightEvaluationStatus.UNSUPPORTED_BOUNDARY:
                        raise RuntimeError("pre-attack reaction reached unsupported execution-right boundary")
                    if not right.allowed:
                        continue
                    count = min(stacks.get(deputy.unit_id, 0) + 1, params.max_stacks)
                    stacks[deputy.unit_id] = count
                    bonuses = [x for x in context.states.find(owner_id=deputy.unit_id,
                        state_id=ATTRIBUTE_BONUS_STATE_ID) if x.source_id == marker.source_id
                        and x.source_skill_id == marker.source_skill_id
                        and x.source_skill_slot == marker.source_skill_slot
                        and x.runtime_params.attribute == "attack"]
                    bonus_params = AttributeBonusParams("attack", count * params.attribute_increment)
                    if bonuses:
                        s.state_lifecycle_system.refresh(context, instance_id=bonuses[0].instance_id,
                            runtime_params=bonus_params)
                    else:
                        bonus = s.state_lifecycle_system.apply(context, state_id=ATTRIBUTE_BONUS_STATE_ID,
                            owner_id=deputy.unit_id, source_id=marker.source_id,
                            source_skill_id=marker.source_skill_id, source_skill_slot=marker.source_skill_slot,
                            runtime_params=bonus_params)
                        s.dependency_evaluation_support.add_dependency(StateNode(bonus.instance_id), ProviderNode(provider))
                    coefficient = params.base_rate + loss_rate_bonus(
                        dict(params.initial_troops)[deputy.unit_id], deputy.troops,
                        params.loss_step, params.max_loss_steps)
                    context.event_bus.publish(event_type=EventType.COUNTER_EXECUTE,
                        phase=context.current_phase, round_no=context.current_round,
                        actor_id=deputy.unit_id, target_id=attacker.unit_id,
                        payload={"source_skill_id": marker.source_skill_id, "timing": "BEFORE_NORMAL_ATTACK",
                            "normal_attack_id": parent, "stacks": count, "coefficient": float(coefficient)})
                    if not attacker.is_alive:
                        context.event_bus.publish(event_type=EventType.COUNTER_ZERO_LOSS,
                            phase=context.current_phase, round_no=context.current_round,
                            actor_id=deputy.unit_id, target_id=attacker.unit_id,
                            payload={"source_skill_id": marker.source_skill_id, "actual_loss": 0})
                        continue
                    lineage = OperationLineage(None, normal_attack_id, None, SourceType.COUNTER,
                        deputy.unit_id, marker.source_skill_id, deputy.unit_id)
                    request = DamageRequest(deputy.unit_id, attacker.unit_id, DamageType.WEAPON,
                        DamageSourceType.COUNTER, coefficient=float(coefficient),
                        source_skill_id=marker.source_skill_id, source_state_id=marker.state_id,
                        source_state_instance_id=marker.instance_id)
                    s.damage_instance_coordinator.execute_partitioned_damage_instance(context,
                        request, lineage, admitted_reaction=(batch_id, capability))
                if marker.instance_id in context.states:
                    s.state_lifecycle_system.refresh(context, instance_id=marker.instance_id,
                        runtime_params=replace(params, last_round=context.current_round,
                            stacks=tuple(stacks.items())))
            finally:
                finalization.complete_reaction(context, batch_id, capability)


class ReactingTargetResolutionSystem(TargetResolutionSystem):
    """Compose a synchronous reaction after selection; never reroll a target."""
    def __init__(self, targets, state_runtime, reaction_support):
        super().__init__(targets, state_runtime)
        self.reactions = reaction_support

    def resolve(self, context, attacker, *, normal_attack_id, resolution_id=None):
        result = super().resolve(context, attacker, normal_attack_id=normal_attack_id,
            resolution_id=resolution_id)
        if result is None:
            return None
        actor = attacker if hasattr(attacker, "unit_id") else context.units[attacker]
        target = context.units[result.post_redirect_actual_target]
        self.reactions.react(context, actor, target, normal_attack_id)
        if not actor.is_alive or not target.is_alive or context.ended or self.reactions.systems.finalization_coordinator.is_latched_or_finalized:
            return None
        return result
