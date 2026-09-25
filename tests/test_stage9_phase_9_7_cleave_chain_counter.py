from __future__ import annotations

import ast
import copy
import inspect
from dataclasses import replace, FrozenInstanceError
from pathlib import Path

import pytest

from sgs_v2.battle_core import (
    BattleContext, BattleSystems, EventBus, EventType, RandomSystem, UnitRuntime,
    LineupPosition, register_official_state_definitions, DamageResult, DamageRequest,
    DamageSourceType, DamageType, SkillSlot, OfficialStateId,
)
from sgs_v2.battle_core.operation_identity import OperationLineage, SourceType
from sgs_v2.battle_core.stage9_integerization import ExactRatio
from sgs_v2.battle_core.stage9_state_params import (
    CleaveStateParams, ChainStateParams, CounterStateParams, DamageShareStateParams,
    DistributionStateParams, GuardStateParams, TauntStateParams, ComboStateParams,
)
from sgs_v2.battle_core.chain_system import (
    ResolvedDamageFact, DamageCallbackTiming, ChainTraversal, ChainSystem,
)
from sgs_v2.battle_core.cleave_system import CleaveEffect
from sgs_v2.battle_core.counter_system import CounterBatch
from sgs_v2.battle_core.execution_right_system import (
    FutureBranchKind, BattleTerminationState, LegacyFinalizationBarrier, admit_action_scope,
)
from sgs_v2.battle_core.battle_finalization_coordinator import ReactionOperationState
from sgs_v2.battle_core.reaction_permission_policy import ReactionPermissionPolicy
from sgs_v2.battle_core.damage_rule_models import (
    HitRuleContribution, HitRuleKind, HitPreventionCategory, RuleContributionSource,
)
from sgs_v2.battle_core.damage_rule_provider import DamageRuleCollection
from sgs_v2.battle_core.recovery_system import RecoveryRequest
from sgs_v2.battle_core.effects import DamageEffect, EffectSourceRef


def context():
    units = {}
    for side in ('a', 'b'):
        for n, pos in enumerate(LineupPosition):
            uid = f'{side}{n}'
            units[uid] = UnitRuntime(uid, uid, side, 10000, 5000, 150, 100, 100,
                                    lineup_position=pos)
    ctx = BattleContext('phase97', units, EventBus(), RandomSystem(17))
    register_official_state_definitions(ctx.states)
    return ctx


def state(ctx, systems, kind, owner, params, *, source='a0', skill=None, slot=None):
    return systems.state_lifecycle_system.apply(ctx, state_id=kind, owner_id=owner,
        runtime_params=params, source_id=source, source_skill_id=skill, source_skill_slot=slot)


def main_fact(ctx, *, target='b1', amount=55, source_type=SourceType.NORMAL_ATTACK):
    return ResolvedDamageFact(ctx.id_allocator.allocate_damage_instance_id(), target,
        OperationLineage(ctx.id_allocator.allocate_action_id(), ctx.id_allocator.allocate_normal_attack_id(),
            None, source_type, 'a0', None, 'a0'), DamageType.WEAPON, amount, amount)


def cleave(ctx, systems, *, slot=SkillSlot.INHERENT, ratio=ExactRatio(27, 50)):
    return state(ctx, systems, 'cleave', 'a0', CleaveStateParams(ratio),
                 skill=f'cleave_{slot}', slot=slot)


def link(ctx, systems, target, ratio=ExactRatio(1, 2), source='a0'):
    return state(ctx, systems, 'chain_link', target, ChainStateParams(ratio), source=source, skill='link')


def counter(ctx, systems, skill='C1', slot=SkillSlot.INHERENT):
    return state(ctx, systems, 'counterattack', 'b1', CounterStateParams(),
                 source='b1', skill=skill, slot=slot)


def batch(ctx, systems, fact):
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.COUNTER_BATCH,
        str(fact.lineage.parent_normal_attack_id))
    return systems.counter_system.create_batch(ctx, fact, permit=permit)


def effect(ctx, systems, fact, instance):
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.CLEAVE_EFFECT,
        str(fact.lineage.parent_normal_attack_id))
    return systems.cleave_system.create_effect(ctx, fact, instance, permit=permit)


def fixed_damage(monkeypatch, systems, amount):
    requests = []
    def calculate(ctx, request):
        requests.append(request)
        value = amount(request) if callable(amount) else amount
        return DamageResult(request.source_id, request.target_id, request.damage_type,
            request.source_type, request.coefficient, value, value, value,
            source_skill_id=request.source_skill_id, source_state_id=request.source_state_id,
            source_state_instance_id=request.source_state_instance_id)
    monkeypatch.setattr(systems.damage_system, 'calculate', calculate)
    return requests


def attack(ctx, systems):
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, 'test_action')
    scope = admit_action_scope(ctx, systems.future_admission_gate, permit, ctx.units['a0'], 'test_action')
    try:
        return systems.action_system.execute(ctx, ctx.units['a0'], action_scope=scope)
    finally:
        systems.finalization_coordinator.complete_action_scope(ctx, scope)


def test_reg_clv_01_reg_int_05_main_overkill_uses_actual_loss(monkeypatch):
    ctx, systems = context(), BattleSystems()
    ctx.units['b1'].troops = 55
    cleave(ctx, systems)
    state(ctx, systems, 'taunt', 'a0', TauntStateParams('b1'), source='b1')
    requests = fixed_damage(monkeypatch, systems, 900)
    result = attack(ctx, systems)
    assert result.resolution.assigned_target_damage == 900
    assert result.resolution.actual_target_troop_loss == 55
    assert [ctx.units[u].troops for u in ('b0', 'b2')] == [4971, 4971]
    assert len(requests) == 1
    facts = [e for e in ctx.event_bus.history if e.payload.get('source_type') == 'CLEAVE' and e.event_type is EventType.DAMAGE_DEALT]
    assert [e.payload['calculated_damage'] for e in facts] == [29, 29]


def test_reg_clv_02_inv_13_16_no_formula_modifier_crit_or_standard_result(monkeypatch):
    ctx, systems = context(), BattleSystems()
    instance = cleave(ctx, systems)
    def forbidden(*args, **kwargs):
        pytest.fail('Cleave entered upstream Stage8 formula/modifier/Crit')
    monkeypatch.setattr(systems.damage_system, 'calculate', forbidden)
    monkeypatch.setattr(systems.damage_system._modifiers, 'resolve', forbidden)
    result = systems.cleave_system.execute(ctx, effect(ctx, systems, main_fact(ctx), instance))
    assert [r.calculated_damage for r in result] == [29, 29]
    assert all(r.request.source_type is SourceType.CLEAVE for r in result)
    assert all(not isinstance(r.request, DamageRequest) for r in result)
    assert not ReactionPermissionPolicy.has_normal_attack_identity(SourceType.CLEAVE)


def test_p97_clv_rec_01_share_target_death_recovery_uses_assigned_sum():
    received, first_aid = [], []
    systems = BattleSystems(cleave_attacker_recovery=lambda ctx, fact: received.append(fact),
                            cleave_first_aid=lambda ctx, fact: first_aid.append(fact))
    ctx = context()
    ctx.units['b0'].troops = 0  # no commander in the planned secondary queue
    ctx.units['b2'].troops = 55
    instance = cleave(ctx, systems, ratio=ExactRatio(1, 1))
    state(ctx, systems, 'damage_share', 'b2', DamageShareStateParams('b1', ExactRatio(15, 100)))
    result, = systems.cleave_system.execute(ctx, effect(ctx, systems, main_fact(ctx, amount=314), instance))
    assert result.assigned_target_damage == 267
    assert result.actual_target_troop_loss == 55
    assert result.partition_plan.primary_assigned_damage == 267
    assert result.partition_plan.shared_assigned_damage == 47
    assert result.recovery.attacker_recovery_basis == 267 + 47
    assert received[0].attacker_recovery_basis == 267 + 47
    assert first_aid[0].actual_target_troop_loss == 55
    assert result.direct_losses == ()  # lethal Share target discards pending sharer
    assert ctx.units['b1'].troops == 5000


def test_p97_clv_rec_02_distribution_keeps_explicit_project_default():
    received = []
    ctx, systems = context(), BattleSystems(cleave_attacker_recovery=lambda ctx, fact: received.append(fact))
    instance = cleave(ctx, systems, ratio=ExactRatio(1, 1))
    state(ctx, systems, 'damage_split', 'b0', DistributionStateParams(ExactRatio(1, 2)))
    result = systems.cleave_system.execute(ctx, effect(ctx, systems, main_fact(ctx, amount=100), instance))[0]
    assert result.assigned_target_damage == 50
    assert sum(loss.actual_loss for loss in result.direct_losses) == 50
    assert result.recovery.attacker_recovery_basis == 50
    assert received[0].external_participant_authority == 'PROJECT_RUNTIME_DEFAULT: distribution external loss excluded'
    assert received[0].primary_damage.assigned_target_damage == 50


def test_reg_clv_03_separate_recovery_contracts_reach_real_recovery_system():
    ctx = context()
    observed = []
    systems = BattleSystems()
    def recover(ctx, fact):
        observed.append(fact.attacker_recovery_basis)
        systems.recovery_system.resolve(ctx, RecoveryRequest('a0', 'a0', fact.attacker_recovery_basis // 10))
    systems.cleave_derived_damage_resolver._attacker_recovery = recover
    cleave(ctx, systems, ratio=ExactRatio(1, 1))
    systems.cleave_system.resolve(ctx, main_fact(ctx, amount=100))
    assert observed == [100, 100]
    assert ctx.units['a0'].troops == 5020
    assert len([e for e in ctx.event_bus.history if e.event_type is EventType.TROOPS_RECOVERED]) == 2


@pytest.mark.parametrize('evasion', [True, False])
def test_reg_clv_03_evasion_before_resistance_consumption(evasion):
    consumed = []
    src = RuleContributionSource(None, None, None, None, None, 'fixture')
    rules = DamageRuleCollection(hit_contributions=(
        HitRuleContribution(HitRuleKind.DETERMINISTIC_PREVENTION, src, '0-resistance', HitPreventionCategory.IMMUNITY_LIKE),
        HitRuleContribution(HitRuleKind.PROBABILISTIC_PREVENTION, src, '9-evasion', HitPreventionCategory.EVASION_LIKE, probability=1 if evasion else 0),
    ))
    class Provider:
        def collect(self, ctx, request):
            assert request.source_type is SourceType.CLEAVE
            return rules
    systems = BattleSystems(cleave_hit_rules=Provider(),
        cleave_hit_consumption=lambda ctx, req, hit: consumed.append(hit.reason.value))
    ctx = context()
    cleave(ctx, systems)
    result = systems.cleave_system.resolve(ctx, main_fact(ctx))
    assert all(r.prevented for r in result)
    assert consumed == (['EVASION_LIKE'] if evasion else ['IMMUNITY_LIKE']) * 2
    assert [ctx.units[u].troops for u in ('b0', 'b2')] == [5000, 5000]
    assert all(r.partition_plan is None for r in result)


def test_reg_clv_04_inv_18_effect_major_and_jit_skip(monkeypatch):
    ctx, systems = context(), BattleSystems()
    cleave(ctx, systems, slot=SkillSlot.LEARNED_2)
    cleave(ctx, systems, slot=SkillSlot.INHERENT)
    order = []
    original = systems.cleave_derived_damage_resolver.resolve
    def resolve(ctx, cap, req):
        order.append((cap.lineage.physical_skill, req.target_id))
        result = original(ctx, cap, req)
        if len(order) == 1:
            systems.troop_system.apply_damage(ctx.units['b2'], 10000)
        return result
    monkeypatch.setattr(systems.cleave_derived_damage_resolver, 'resolve', resolve)
    systems.cleave_system.resolve(ctx, main_fact(ctx))
    assert order == [('cleave_0', 'b0'), ('cleave_2', 'b0')]


def test_reg_clv_04_all_source_zero_targets_before_source_two(monkeypatch):
    ctx, systems = context(), BattleSystems()
    cleave(ctx, systems, slot=SkillSlot.LEARNED_2)
    cleave(ctx, systems)
    results = systems.cleave_system.resolve(ctx, main_fact(ctx))
    assert [(r.request.lineage.physical_skill, r.request.target_id) for r in results] == [
        ('cleave_0', 'b0'), ('cleave_0', 'b2'), ('cleave_2', 'b0'), ('cleave_2', 'b2')]


def test_reg_clv_05_reg_tgt_07_guard_original_target_is_secondary(monkeypatch):
    ctx, systems = context(), BattleSystems()
    cleave(ctx, systems)
    state(ctx, systems, 'taunt', 'a0', TauntStateParams('b1'), source='b1')
    state(ctx, systems, 'guard', 'b1', GuardStateParams('b2'), source='b2')
    fixed_damage(monkeypatch, systems, 100)
    result = attack(ctx, systems)
    assert result.target_resolution.intended_attack_target == 'b1'
    assert result.target_resolution.post_redirect_actual_target == 'b2'
    assert ctx.units['b1'].troops == 4946
    assert ctx.units['b2'].troops == 4900


def test_inv_18_missing_required_slot_is_domain_error():
    ctx, systems = context(), BattleSystems()
    state(ctx, systems, 'cleave', 'a0', CleaveStateParams(ExactRatio(1, 2)), skill='missing')
    with pytest.raises(ValueError, match='source_skill_slot'):
        systems.cleave_system.resolve(ctx, main_fact(ctx))
    assert ctx.id_allocator._cleave_effect_seq == 0


@pytest.mark.parametrize('alive_count', [0, 1, 2])
def test_reg_clv_04_secondary_count_is_live_plan(alive_count):
    ctx, systems = context(), BattleSystems()
    for uid in ('b0', 'b2')[alive_count:]:
        ctx.units[uid].troops = 0
    instance = cleave(ctx, systems)
    cap = effect(ctx, systems, main_fact(ctx), instance)
    assert len(cap.secondary_plan) == alive_count
    assert len(systems.cleave_system.execute(ctx, cap)) == alive_count


def test_final_04_inv_40_current_cleave_drains_later_effect_blocked(monkeypatch):
    ctx, systems = context(), BattleSystems()
    ctx.units['b0'].troops = 10
    cleave(ctx, systems)
    cleave(ctx, systems, slot=SkillSlot.LEARNED_2)
    observations = []
    original = systems.cleave_derived_damage_resolver.resolve
    def resolve(ctx, cap, request):
        result = original(ctx, cap, request)
        observations.append((ctx.units['b0'].troops, systems.finalization_coordinator.termination_state,
                             systems.finalization_coordinator.has_admitted_work))
        return result
    monkeypatch.setattr(systems.cleave_derived_damage_resolver, 'resolve', resolve)
    result = systems.cleave_system.resolve(ctx, main_fact(ctx))
    assert len(result) == 2 and ctx.units['b2'].troops == 4971
    assert ctx.id_allocator._cleave_effect_seq == 1
    assert observations[0] == (0, BattleTerminationState.DRAINING_ADMITTED_WORK, True)
    assert systems.finalization_coordinator.termination_state is BattleTerminationState.FINALIZED
    assert not systems.finalization_coordinator.has_admitted_work


def test_reg_clv_04_attacker_death_is_local_gate(monkeypatch):
    ctx, systems = context(), BattleSystems()
    cleave(ctx, systems)
    original = systems.cleave_derived_damage_resolver.resolve
    def resolve(ctx, cap, req):
        result = original(ctx, cap, req)
        systems.troop_system.apply_damage(ctx.units['a0'], 10000)
        return result
    monkeypatch.setattr(systems.cleave_derived_damage_resolver, 'resolve', resolve)
    result = systems.cleave_system.resolve(ctx, main_fact(ctx))
    assert len(result) == 1 and ctx.units['b2'].troops == 5000


def test_reg_chn_01_inv_32_33_current_state_replaces_owner_ratio():
    ctx, systems = context(), BattleSystems()
    link(ctx, systems, 'b1', ExactRatio(1, 5))
    link(ctx, systems, 'b2')
    pending = systems.damage_callbacks.accept(ctx, main_fact(ctx, amount=500), timing=DamageCallbackTiming.AFTER_CLEAVE)
    link(ctx, systems, 'b1', ExactRatio(3, 10), source='a2')
    result, = systems.chain_system.execute(ctx, pending)
    assert pending.work.trigger_damage == 500
    assert result.calculated_damage == 150
    assert result.lineage.credit_owner == 'a2'


@pytest.mark.parametrize('removed', [True, False])
def test_reg_chn_01_trigger_removed_or_dead_cancels(removed):
    ctx, systems = context(), BattleSystems()
    instance = link(ctx, systems, 'b1')
    link(ctx, systems, 'b2')
    work = systems.damage_callbacks.accept(ctx, main_fact(ctx), timing=DamageCallbackTiming.AFTER_CLEAVE)
    if removed:
        systems.state_lifecycle_system.remove(ctx, instance.instance_id)
    else:
        ctx.units['b1'].troops = 0
    assert systems.chain_system.execute(ctx, work) == ()
    assert not systems.finalization_coordinator.has_admitted_work


def test_reg_chn_02_inv_34_monotonic_cursor_live_later_slot(monkeypatch):
    ctx, systems = context(), BattleSystems()
    link(ctx, systems, 'b0')
    link(ctx, systems, 'b1')
    original = systems.chain_system._settle_feedback
    def settle(ctx, traversal, uid, amount, lineage):
        result = original(ctx, traversal, uid, amount, lineage)
        if uid == 'b0':
            link(ctx, systems, 'b2')
            link(ctx, systems, 'b0', ExactRatio(9, 10))
        return result
    monkeypatch.setattr(systems.chain_system, '_settle_feedback', settle)
    systems.damage_callbacks.accept(ctx, main_fact(ctx, amount=100))
    events = ctx.event_bus.history
    assert [e.target_id for e in events if e.event_type is EventType.CHAIN_FEEDBACK] == ['b0', 'b2']
    assert [e.payload['cursor'] for e in events if e.event_type is EventType.CHAIN_SLOT_VISITED] == [0, 1, 2]


def test_reg_chn_03_final_01_current_broadcast_drains_after_commander_death(monkeypatch):
    ctx, systems = context(), BattleSystems()
    ctx.units['b0'].troops = 10
    for uid in ('b0', 'b1', 'b2'):
        link(ctx, systems, uid)
    states = []
    original = systems.chain_system._settle_feedback
    def settle(*args):
        result = original(*args)
        states.append(systems.finalization_coordinator.termination_state)
        return result
    monkeypatch.setattr(systems.chain_system, '_settle_feedback', settle)
    systems.damage_callbacks.accept(ctx, main_fact(ctx, amount=100))
    assert ctx.units['b2'].troops == 4950
    assert states == [BattleTerminationState.DRAINING_ADMITTED_WORK] * 2
    assert systems.finalization_coordinator.termination_state is BattleTerminationState.FINALIZED


def test_reg_chn_04_reg_int_01_inv_35_restricted_feedback(monkeypatch):
    ctx, systems = context(), BattleSystems()
    link(ctx, systems, 'b1', ExactRatio(2828, 10000))
    link(ctx, systems, 'b2')
    def forbidden(*a, **kw):
        pytest.fail('TRUE_FEEDBACK entered a forbidden pipeline')
    monkeypatch.setattr(systems.damage_system, 'calculate', forbidden)
    monkeypatch.setattr(systems.damage_partition_coordinator, 'plan', forbidden)
    monkeypatch.setattr(systems.recovery_system, 'resolve', forbidden)
    systems.damage_callbacks.accept(ctx, main_fact(ctx, amount=396))
    assert ctx.units['b2'].troops == 4889
    assert ctx.id_allocator._chain_traversal_seq == 1


def test_reg_chn_01_dead_applier_does_not_cancel_valid_link():
    ctx, systems = context(), BattleSystems()
    ctx.units['a2'].troops = 0
    link(ctx, systems, 'b1', source='a2')
    link(ctx, systems, 'b2')
    systems.damage_callbacks.accept(ctx, main_fact(ctx, amount=100))
    assert ctx.units['b2'].troops == 4950
    e = next(e for e in ctx.event_bus.history if e.event_type is EventType.CHAIN_FEEDBACK)
    assert e.payload['credit_owner'] == 'a2'


def test_reg_chn_04_zero_resolved_damage_still_traverses():
    ctx, systems = context(), BattleSystems()
    link(ctx, systems, 'b1')
    link(ctx, systems, 'b2')
    systems.damage_callbacks.accept(ctx, main_fact(ctx, amount=0))
    assert ctx.id_allocator._chain_traversal_seq == 1
    assert len([e for e in ctx.event_bus.history if e.event_type is EventType.CHAIN_FEEDBACK]) == 1


def test_reg_ctr_01_inv_36_immutable_batch_after_state_removed(monkeypatch):
    ctx, systems = context(), BattleSystems()
    counter(ctx, systems)
    instance = counter(ctx, systems, 'C2', SkillSlot.LEARNED_2)
    cap = batch(ctx, systems, main_fact(ctx))
    systems.state_lifecycle_system.remove(ctx, instance.instance_id)
    fixed_damage(monkeypatch, systems, 10)
    result = systems.counter_system.execute(ctx, cap)
    assert len(cap.entries) == len(result) == 2
    assert all(r.executed for r in result)
    with pytest.raises(FrozenInstanceError):
        cap.entries = ()


@pytest.mark.parametrize('periodic', [False, True])
def test_production_damage_effect_reaches_shared_chain_callback(periodic):
    ctx, systems = context(), BattleSystems()
    link(ctx, systems, 'b1')
    link(ctx, systems, 'b2')
    source = SourceType.PERIODIC_DAMAGE if periodic else SourceType.ACTIVE_SKILL
    effect_data = DamageEffect('a0', 'b1', DamageType.WEAPON,
        DamageSourceType.CONTINUOUS if periodic else DamageSourceType.SKILL,
        source_skill_id='source', source_state_id='burn' if periodic else None,
        source_state_instance_id='burn_fixture' if periodic else None,
        source_ref=EffectSourceRef(source, 'a0', 'source', SkillSlot.INHERENT))
    result = systems.effect_executor.execute(ctx, effect_data)
    loss = result.resolution.actual_target_troop_loss
    assert loss > 0
    assert ctx.units['b2'].troops == 5000 - loss // 2
    assert not systems.finalization_coordinator.has_admitted_work


def test_positive_counter_real_formula_share_and_chain():
    ctx, systems = context(), BattleSystems()
    counter(ctx, systems)
    link(ctx, systems, 'a0', source='b2')
    link(ctx, systems, 'a2', source='b2')
    state(ctx, systems, 'damage_share', 'a0', DamageShareStateParams('a1', ExactRatio(1, 4)))
    result = systems.counter_system.execute(ctx, batch(ctx, systems, main_fact(ctx)))[0]
    assert result.actual_troop_loss > 0
    assert result.damage_execution.damage_result.source_type is DamageSourceType.COUNTER
    assert ctx.units['a1'].troops < 5000
    assert ctx.units['a2'].troops == 5000 - result.actual_troop_loss // 2
    assert not systems.finalization_coordinator.has_admitted_work


def test_share_nonlethal_recovery_uses_primary_plus_shared_assignment():
    ctx, systems = context(), BattleSystems()
    instance = cleave(ctx, systems, ratio=ExactRatio(1, 1))
    state(ctx, systems, 'damage_share', 'b0', DamageShareStateParams('b1', ExactRatio(3, 20)))
    result = systems.cleave_system.execute(ctx, effect(ctx, systems, main_fact(ctx, amount=314), instance))[0]
    assert result.partition_plan.primary_assigned_damage == 267
    assert result.partition_plan.shared_assigned_damage == 47
    assert result.recovery.attacker_recovery_basis == 267 + 47
    assert result.actual_target_troop_loss == 267
    assert sum(loss.actual_loss for loss in result.direct_losses) == 47


def test_cleave_removed_future_source_is_skipped_at_effect_boundary():
    ctx, systems = context(), BattleSystems()
    cleave(ctx, systems)
    later = cleave(ctx, systems, slot=SkillSlot.LEARNED_2)
    def remove_later(ctx, fact):
        if any(item is later for item in ctx.states.find(owner_id='a0', state_id='cleave')):
            systems.state_lifecycle_system.remove(ctx, later.instance_id)
    systems.cleave_derived_damage_resolver._attacker_recovery = remove_later
    assert len(systems.cleave_system.resolve(ctx, main_fact(ctx))) == 2
    assert ctx.id_allocator._cleave_effect_seq == 1


def test_reg_ctr_01_operationality_only_at_admission(monkeypatch):
    operational = [True]
    ctx, systems = context(), BattleSystems(counter_operationality=lambda ctx, state: operational[0])
    counter(ctx, systems)
    cap = batch(ctx, systems, main_fact(ctx))
    operational[0] = False
    fixed_damage(monkeypatch, systems, 10)
    assert systems.counter_system.execute(ctx, cap)[0].executed
    assert systems.stage9_state_runtime.get_counter_effects(ctx, 'b1') == ()


def test_reg_ctr_02_inv_37_dead_owner_cancels_without_execute_event():
    ctx, systems = context(), BattleSystems()
    counter(ctx, systems)
    cap = batch(ctx, systems, main_fact(ctx))
    ctx.units['b1'].troops = 0
    result = systems.counter_system.execute(ctx, cap)
    assert not result[0].executed
    assert not any(e.event_type is EventType.COUNTER_EXECUTE for e in ctx.event_bus.history)


def test_reg_ctr_03_reg_ctr_04_final_02_inv_38_zero_terminal(monkeypatch):
    ctx, systems = context(), BattleSystems()
    counter(ctx, systems)
    counter(ctx, systems, 'C2', SkillSlot.LEARNED_2)
    cap = batch(ctx, systems, main_fact(ctx))
    requests = fixed_damage(monkeypatch, systems, 9000)
    result = systems.counter_system.execute(ctx, cap)
    assert len(requests) == 1 and requests[0].source_type is DamageSourceType.COUNTER
    assert result[1].executed and result[1].dead_target_terminal
    assert result[1].actual_troop_loss == 0 and result[1].damage_execution is None
    assert len([e for e in ctx.event_bus.history if e.event_type is EventType.COUNTER_EXECUTE]) == 2
    assert systems.finalization_coordinator.termination_state is BattleTerminationState.FINALIZED
    assert not systems.finalization_coordinator.has_admitted_work


def test_reg_ctr_04_dead_target_no_hit_formula_partition_chain(monkeypatch):
    ctx, systems = context(), BattleSystems()
    counter(ctx, systems)
    cap = batch(ctx, systems, main_fact(ctx))
    ctx.units['a0'].troops = 0
    def forbidden(*a, **kw):
        pytest.fail('Dead-target Counter entered positive pipeline')
    monkeypatch.setattr(systems.damage_system, 'calculate', forbidden)
    monkeypatch.setattr(systems.damage_system._hit, 'resolve', forbidden)
    monkeypatch.setattr(systems.damage_partition_coordinator, 'plan', forbidden)
    monkeypatch.setattr(systems.damage_callbacks, 'accept', forbidden)
    assert systems.counter_system.execute(ctx, cap)[0].dead_target_terminal


def test_reg_ctr_05_counter_kill_blocks_assault_combo(monkeypatch):
    ctx, systems = context(), BattleSystems()
    counter(ctx, systems)
    state(ctx, systems, 'combo', 'a0', ComboStateParams(), skill='combo_source')
    state(ctx, systems, 'taunt', 'a0', TauntStateParams('b1'), source='b1')
    requests = fixed_damage(monkeypatch, systems, lambda req: 9000 if req.source_type is DamageSourceType.COUNTER else 10)
    result = attack(ctx, systems)
    assert len(requests) == 2
    assert result.combo_attack_result is None
    assert not any(e.event_type is EventType.COMBO_OPPORTUNITY_CONSUMED for e in ctx.event_bus.history)


@pytest.mark.parametrize('source', [SourceType.NORMAL_ATTACK, SourceType.ACTIVE_SKILL, SourceType.PERIODIC_DAMAGE, SourceType.CLEAVE, SourceType.COUNTER])
def test_inv_17_42_shared_callback_all_eligible_sources(source):
    ctx, systems = context(), BattleSystems()
    link(ctx, systems, 'b1')
    link(ctx, systems, 'b2')
    systems.damage_callbacks.accept(ctx, main_fact(ctx, source_type=source, amount=100))
    assert ctx.units['b2'].troops == 4950


@pytest.mark.parametrize('source', [SourceType.CHAIN_TRUE_FEEDBACK, SourceType.SHARE_DIRECT_LOSS, SourceType.DISTRIBUTION_DIRECT_LOSS])
def test_inv_17_42_forbidden_callbacks_allocate_no_traversal(source):
    ctx, systems = context(), BattleSystems()
    link(ctx, systems, 'b1')
    systems.damage_callbacks.accept(ctx, main_fact(ctx, source_type=source))
    assert ctx.id_allocator._chain_traversal_seq == 0


@pytest.mark.parametrize('source', [SourceType.CLEAVE, SourceType.COUNTER, SourceType.CHAIN_TRUE_FEEDBACK])
def test_inv_17_42_no_recursive_cleave_counter(source):
    assert not ReactionPermissionPolicy.can_trigger_counter(source)
    assert not ReactionPermissionPolicy.can_trigger_cleave(source)


def factory_setup(kind):
    ctx, systems = context(), BattleSystems()
    fact = main_fact(ctx)
    if kind == 'cleave':
        instance = cleave(ctx, systems)
        branch, parent = FutureBranchKind.CLEAVE_EFFECT, str(fact.lineage.parent_normal_attack_id)
        factory = lambda permit: systems.cleave_system.create_effect(ctx, fact, instance, permit=permit)
        owner = systems.cleave_system
        identity = lambda cap: cap.effect_id
    elif kind == 'chain':
        link(ctx, systems, 'b1')
        branch, parent = FutureBranchKind.CHAIN_TRAVERSAL, str(fact.damage_instance_id)
        factory = lambda permit: systems.chain_system.create_traversal(ctx, fact, permit=permit)
        owner = systems.chain_system
        identity = lambda cap: cap.traversal_id
    else:
        counter(ctx, systems)
        branch, parent = FutureBranchKind.COUNTER_BATCH, str(fact.lineage.parent_normal_attack_id)
        factory = lambda permit: systems.counter_system.create_batch(ctx, fact, permit=permit)
        owner = systems.counter_system
        identity = lambda cap: cap.batch_id
    return ctx, systems, branch, parent, factory, owner, identity


def allocation_state(ctx):
    return tuple(getattr(ctx.id_allocator, n) for n in ('_cleave_effect_seq', '_chain_traversal_seq', '_reaction_batch_seq', '_counter_entry_seq'))


@pytest.mark.parametrize('kind', ['cleave', 'chain', 'counter'])
@pytest.mark.parametrize('fault', ['missing', 'forged', 'cross_gate', 'replay', 'wrong_parent', 'wrong_branch'])
def test_inv_40_no_bypass_before_identity_allocation(kind, fault):
    ctx, systems, branch, parent, factory, owner, identity = factory_setup(kind)
    gate = systems.future_admission_gate
    permit = gate.request_admission(branch, parent)
    if fault == 'missing':
        permit = None
    elif fault == 'forged':
        permit = replace(permit)
    elif fault == 'cross_gate':
        permit = BattleSystems().future_admission_gate.request_admission(branch, parent)
    elif fault == 'replay':
        cap = factory(permit)
        systems.finalization_coordinator.complete_reaction(ctx, identity(cap), cap)
    elif fault == 'wrong_parent':
        permit = gate.request_admission(branch, 'wrong_parent')
    elif fault == 'wrong_branch':
        permit = gate.request_admission(FutureBranchKind.NEXT_ACTION, parent)
    before = allocation_state(ctx)
    with pytest.raises((ValueError, TypeError, RuntimeError)):
        factory(permit)
    assert allocation_state(ctx) == before


@pytest.mark.parametrize('kind', ['cleave', 'chain', 'counter'])
def test_inv_39_40_41_real_barrier_capability_lifecycle(kind):
    ctx, systems, branch, parent, factory, owner, identity = factory_setup(kind)
    cap = factory(systems.future_admission_gate.request_admission(branch, parent))
    coord = systems.finalization_coordinator
    assert coord.validate_reaction(ctx, identity(cap), cap) is ReactionOperationState.ADMITTED
    assert coord.has_admitted_work
    coord.start_reaction(ctx, identity(cap), cap)
    assert coord.validate_reaction(ctx, identity(cap), cap) is ReactionOperationState.EXECUTING
    ctx.units['a0'].troops = 0
    coord.observe_reaction_death(ctx, identity(cap), cap)
    assert coord.termination_state is BattleTerminationState.DRAINING_ADMITTED_WORK
    for future in FutureBranchKind:
        assert systems.future_admission_gate.request_admission(future, 'blocked') is None
    coord.complete_reaction(ctx, identity(cap), cap)
    assert not coord.has_admitted_work
    assert coord.termination_state is BattleTerminationState.FINALIZED
    with pytest.raises(ValueError):
        coord.complete_reaction(ctx, identity(cap), cap)


@pytest.mark.parametrize('kind', ['cleave', 'chain', 'counter'])
def test_inv_40_cross_context_and_same_value_forgery_rejected(kind):
    ca, sa, ba, pa, fa, oa, ia = factory_setup(kind)
    cb, sb, bb, pb, fb, ob, ib = factory_setup(kind)
    a = fa(sa.future_admission_gate.request_admission(ba, pa))
    b = fb(sb.future_admission_gate.request_admission(bb, pb))
    assert ia(a) == ib(b)
    before = tuple(u.troops for u in cb.units.values())
    for ctx, cap in ((cb, a), (ca, copy.copy(a))):
        with pytest.raises((ValueError, RuntimeError)):
            oa.execute(ctx, cap)
        with pytest.raises((ValueError, RuntimeError)):
            sa.finalization_coordinator.complete_reaction(ctx, ia(a), cap)
    assert tuple(u.troops for u in cb.units.values()) == before
    assert sa.finalization_coordinator.has_admitted_work
    assert sb.finalization_coordinator.has_admitted_work


@pytest.mark.parametrize('cls', [CleaveEffect, ChainTraversal, CounterBatch])
def test_inv_40_raw_production_operation_construction_forbidden(cls):
    with pytest.raises(TypeError):
        cls()


def test_p97_production_deferred_main_chain_after_cleave(monkeypatch):
    ctx, systems = context(), BattleSystems()
    cleave(ctx, systems)
    for uid in ('b0', 'b1', 'b2'):
        link(ctx, systems, uid)
    state(ctx, systems, 'taunt', 'a0', TauntStateParams('b1'), source='b1')
    counter(ctx, systems)
    fixed_damage(monkeypatch, systems, 100)
    attack(ctx, systems)
    events = ctx.event_bus.history
    cleaves = [e.sequence for e in events if e.event_type is EventType.DAMAGE_DEALT and e.payload.get('source_type') == 'CLEAVE']
    main_chain = [e.sequence for e in events if e.event_type is EventType.CHAIN_FEEDBACK and e.payload['traversal_id'] == 'chn_1']
    counters = [e.sequence for e in events if e.event_type is EventType.COUNTER_EXECUTE]
    assert len(cleaves) == 2
    assert max(cleaves) < min(main_chain) < min(counters)
    assert systems.finalization_coordinator.has_admitted_work is False


def test_p97_architecture_no_self_admission_or_local_finalization():
    root = Path(__file__).resolve().parents[1] / 'sgs_v2' / 'battle_core'
    for name in ('cleave_system.py', 'cleave_derived_damage_system.py', 'chain_system.py', 'counter_system.py'):
        source = (root / name).read_text(encoding='utf-8')
        assert 'context.ended =' not in source and 'context.result =' not in source
        assert 'DamageSourceType.NORMAL_ATTACK' not in source
    for cls in (ChainSystem,):
        assert 'request_admission' not in inspect.getsource(cls)
    from sgs_v2.battle_core.counter_system import CounterSystem
    assert 'request_admission' not in inspect.getsource(CounterSystem)
    source = (root / 'damage_instance_coordinator.py').read_text(encoding='utf-8')
    assert 'get_operational_chain' not in source and 'CHAIN_TRAVERSAL' not in source


@pytest.mark.parametrize('kind', ['cleave', 'chain'])
def test_non_counter_scope_cannot_open_standard_formula_route(kind):
    ctx, systems, branch, parent, factory, owner, identity = factory_setup(kind)
    cap = factory(systems.future_admission_gate.request_admission(branch, parent))
    systems.finalization_coordinator.start_reaction(ctx, identity(cap), cap)
    fact = main_fact(ctx, source_type=SourceType.COUNTER)
    before = ctx.id_allocator._damage_instance_seq
    request = DamageRequest('a0', 'b1', DamageType.WEAPON, DamageSourceType.COUNTER)
    with pytest.raises(ValueError):
        systems.damage_instance_coordinator.execute_partitioned_damage_instance(ctx, request,
            fact.lineage, admitted_reaction=(identity(cap), cap))
    assert ctx.id_allocator._damage_instance_seq == before
    systems.finalization_coordinator.complete_reaction(ctx, identity(cap), cap)


def test_p97_rpr_01_main_target_commander_lethal_cleave(monkeypatch):
    """P97-RPR-01: Main NormalAttack target commander death admits current Cleave and drains secondaries before battle finalization."""
    ctx, systems = context(), BattleSystems()
    ctx.units['b0'].troops = 50
    cleave(ctx, systems)
    state(ctx, systems, 'taunt', 'a0', TauntStateParams('b0'), source='b0')
    requests = fixed_damage(monkeypatch, systems, 100)

    drain_observations = []
    orig_resolve = systems.cleave_derived_damage_resolver.resolve

    def resolve_spy(c, cap, req):
        drain_observations.append({
            'has_admitted_work': systems.finalization_coordinator.has_admitted_work,
            'termination_state': systems.finalization_coordinator.termination_state,
            'commander_troops': c.units['b0'].troops,
            'target_id': req.target_id,
            'cleave_effect_id': cap.effect_id.value,
        })
        return orig_resolve(c, cap, req)

    monkeypatch.setattr(systems.cleave_derived_damage_resolver, 'resolve', resolve_spy)

    result = attack(ctx, systems)

    # 1. Main commander died
    assert ctx.units['b0'].troops == 0
    assert result.resolution.actual_target_troop_loss == 50

    # 2. Current/first CleaveEffect was admitted and drained
    assert len(drain_observations) == 2
    for obs in drain_observations:
        assert obs['has_admitted_work'] is True
        assert obs['termination_state'] is BattleTerminationState.DRAINING_ADMITTED_WORK
        assert obs['commander_troops'] == 0
        assert obs['cleave_effect_id'] == 'clv_1'

    # 3. Secondary plan executed and secondaries received Cleave damage (50 * 27 / 50 = 27)
    assert ctx.units['b1'].troops == 4973
    assert ctx.units['b2'].troops == 4973

    # 4. Battle did not finalize before Cleave reached terminal state; finalized only after action scope complete
    assert systems.finalization_coordinator.has_admitted_work is False
    assert systems.finalization_coordinator.termination_state is BattleTerminationState.FINALIZED


def test_p97_rpr_02_main_commander_death_blocks_later_independent_cleave(monkeypatch):
    """P97-RPR-02: Main commander death permits current Cleave to drain but blocks subsequent independent Cleave admission."""
    ctx, systems = context(), BattleSystems()
    ctx.units['b0'].troops = 50
    cleave(ctx, systems, slot=SkillSlot.INHERENT)
    cleave(ctx, systems, slot=SkillSlot.LEARNED_2)
    state(ctx, systems, 'taunt', 'a0', TauntStateParams('b0'), source='b0')
    requests = fixed_damage(monkeypatch, systems, 100)

    executed_cleaves = []
    orig_resolve = systems.cleave_derived_damage_resolver.resolve

    def resolve_spy(c, cap, req):
        executed_cleaves.append((cap.effect_id.value, cap.lineage.physical_skill, req.target_id))
        return orig_resolve(c, cap, req)

    monkeypatch.setattr(systems.cleave_derived_damage_resolver, 'resolve', resolve_spy)

    result = attack(ctx, systems)

    # Commander died
    assert ctx.units['b0'].troops == 0

    # Exactly 1 CleaveEffect was allocated (Slot 0 admitted, Slot 2 blocked)
    assert ctx.id_allocator._cleave_effect_seq == 1
    assert len(executed_cleaves) == 2
    assert all(cid == 'clv_1' for cid, _, _ in executed_cleaves)
    assert all(skill == 'cleave_0' for _, skill, _ in executed_cleaves)
    assert {target for _, _, target in executed_cleaves} == {'b1', 'b2'}


def test_p97_rpr_03_normal_attack_resisted_still_cleaves():
    """P97-RPR-03: Resisted NormalAttack (IMMUNITY_LIKE) yields 0 loss but still admits Cleave (base 0) and CounterBatch."""
    src = RuleContributionSource(None, None, None, None, None, 'fixture')
    rules = DamageRuleCollection(hit_contributions=(
        HitRuleContribution(HitRuleKind.DETERMINISTIC_PREVENTION, src, '0-resistance', HitPreventionCategory.IMMUNITY_LIKE),
    ))

    class ResistedRuleProvider:
        def collect(self, ctx, request):
            if request.target_id == 'b1' and request.source_type == SourceType.NORMAL_ATTACK:
                return rules
            return DamageRuleCollection()

    systems = BattleSystems(damage_rule_provider=ResistedRuleProvider())
    ctx = context()
    cleave(ctx, systems)
    counter(ctx, systems)
    state(ctx, systems, 'taunt', 'a0', TauntStateParams('b1'), source='b1')

    result = attack(ctx, systems)

    # NormalAttack identity and resolution exist
    assert result.normal_attack_id is not None
    assert result.resolution is not None
    assert result.damage.prevented is True
    assert result.damage.pipeline_trace.hit_result.reason.value == 'IMMUNITY_LIKE'
    assert result.resolution.actual_target_troop_loss == 0

    # CleaveEffect is admitted with base 0
    assert ctx.id_allocator._cleave_effect_seq == 1

    # Secondary Cleave damage events executed with calculated_damage = 0
    events = ctx.event_bus.history
    cleave_events = [e for e in events if e.event_type is EventType.DAMAGE_DEALT and e.payload.get('source_type') == 'CLEAVE']
    assert len(cleave_events) == 2
    for ce in cleave_events:
        assert ce.payload['calculated_damage'] == 0
        assert ce.payload['damage'] == 0
        assert ce.payload['target_remaining_troops'] == 5000

    # CounterBatch was also admitted and executed
    counter_events = [e for e in events if e.event_type is EventType.COUNTER_EXECUTE]
    assert len(counter_events) == 1


@pytest.mark.parametrize('state_id', [OfficialStateId.DISARM.value, OfficialStateId.STUN.value])
def test_p97_rpr_04_blocked_normal_attack_has_no_cleave(state_id):
    """P97-RPR-04: Blocked action (DISARM / STUN) does not allocate NormalAttack, Cleave, or CounterBatch."""
    ctx, systems = context(), BattleSystems()
    cleave(ctx, systems)
    counter(ctx, systems)
    systems.state_lifecycle_system.apply(
        context=ctx,
        state_id=state_id,
        owner_id='a0',
        source_id='b1',
        source_skill_id='test_skill',
        source_skill_slot=SkillSlot.INHERENT,
    )

    result = attack(ctx, systems)

    # Action blocked: no normal attack instance allocated
    assert result is None or result.normal_attack_id is None
    assert ctx.id_allocator._normal_attack_seq == 0

    # No CleaveEffect allocated
    assert ctx.id_allocator._cleave_effect_seq == 0

    # No CounterBatch allocated
    assert getattr(ctx.id_allocator, '_counter_batch_seq', 0) == 0

    # No Cleave or Counter events
    events = ctx.event_bus.history
    cleave_events = [e for e in events if e.payload.get('source_type') == 'CLEAVE']
    counter_events = [e for e in events if e.event_type is EventType.COUNTER_EXECUTE]
    assert len(cleave_events) == 0
    assert len(counter_events) == 0

