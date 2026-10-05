"""Runtime behavior for Wudang / Xianzhen, including real DOT and recovery lanes."""
from dataclasses import replace

import pytest

from test_stage14_troop_batch01 import setup, settle, probe
from sgs_v2.battle_core import (
    BattleEngine, BattlePhase, DamageEffect, DamageSourceType, DamageType, EventType,
    OfficialStateId, StateCandidate, StateLifetimeSpec, TroopAdmissionStatus, TroopType,
    UnitActionStartHook, admit_and_install_troop_skill, calculate_wu_dang_damage_rate,
    create_wu_dang_fei_jun_runtime, create_xian_zhen_ying_runtime,
    SkillType, SkillSlot,
)
from sgs_v2.battle_core.pending_work import PendingWorkTimingPoint, PendingWorkStatus
from sgs_v2.battle_core.damage_aftermath_port import DamageAftermathFact, DamageHitTopology
from sgs_v2.battle_core.operation_identity import SourceType
from sgs_v2.battle_core.state_runtime_params import EmptyStateRuntimeParams
from sgs_v2.battle_core.effects import EffectSourceRef
from sgs_v2.battle_core.troop_skills.xian_zhen_ying import GAO_SHUN_COMMANDER_ENHANCEMENT

CASES = [(create_wu_dang_fei_jun_runtime, TroopType.BOW, "WU_DANG_FEI_JUN"),
         (create_xian_zhen_ying_runtime, TroopType.SHIELD, "XIAN_ZHEN_YING")]


def fixture(factory=create_wu_dang_fei_jun_runtime, troop=TroopType.BOW):
    context, systems, runtime = setup(factory, troop)
    for unit in context.units.values():
        unit.intelligence = 100
    context.units["a1"].intelligence = 650
    return context, systems, runtime


def opening(context, systems):
    context.current_round = 1
    context.current_phase = BattlePhase.ROUND_START.value
    return systems.pending_work_system.process(context, PendingWorkTimingPoint(1, BattlePhase.ROUND_START))


def tick(context, systems, target, round_no):
    context.current_round = round_no
    context.current_phase = BattlePhase.UNIT_ACTION_START.value
    context.action_progress.set_current_acting_unit(target)
    context.action_progress.mark_action_start(target, round_no)
    return systems.rule_hook_system.process(context, UnitActionStartHook(round_no, target))


@pytest.mark.parametrize("intelligence,rate", [(0, .8), (349, .8), (350, .8),
    (500, .88), (650, .96), (1850, 1.6)])
def test_user_damage_rate_formula(intelligence, rate):
    assert calculate_wu_dang_damage_rate(intelligence) == pytest.approx(rate)


@pytest.mark.parametrize("value", [True, -1, float("nan"), float("inf")])
def test_rate_rejects_invalid_attributes(value):
    with pytest.raises((TypeError, ValueError)):
        calculate_wu_dang_damage_rate(value)


@pytest.mark.parametrize("factory,troop,special", CASES)
def test_prebattle_conversion_and_persistent_attributes(factory, troop, special):
    context, systems, runtime = fixture(factory, troop)
    assert admit_and_install_troop_skill(context, systems, runtime).status is TroopAdmissionStatus.SUCCESS
    for uid in ("a1", "a2", "a3"):
        unit = context.units[uid]
        assert unit.special_troop_id.value == special and unit.troop_type is troop
        assert systems.attribute_system.get_defense(context, unit) == unit.defense + 22
        if troop is TroopType.BOW:
            assert systems.attribute_system.get_speed(context, unit) == unit.speed + 22
        else:
            assert systems.attribute_system.get_attack(context, unit) == unit.attack + 22
    assert not context.states.find(owner_id="b1")
    assert not context.random.probabilities
    settle(context, systems, 4)
    assert systems.attribute_system.get_defense(context, context.units["a2"]) == 142


@pytest.mark.parametrize("commander,targets", [("a1", 2), ("王平", 3)])
def test_wudang_opening_target_count_and_source_basis(commander, targets):
    context, systems, runtime = fixture()
    context.units["a1"].name = commander
    admit_and_install_troop_skill(context, systems, runtime)
    assert not context.states.find(state_id=OfficialStateId.POISON.value)
    opening(context, systems)
    poison = context.states.find(state_id=OfficialStateId.POISON.value)
    assert len(poison) == targets
    assert len({s.owner_id for s in poison}) == targets
    for state in poison:
        assert state.owner_id.startswith("b")
        basis = state.runtime_params.frozen_damage_basis
        assert basis.coefficient == pytest.approx(.96)
        assert basis.source_skill_id == "20100" and basis.source_unit_id == "a1"
        assert basis.application_generation_id == state.current_generation_id
        assert basis.physical_state_instance_id == state.instance_id
        assert basis.source_formula_facts.source_combat_attribute_at_application == 650
        assert state.lifecycle_window.first_eligible_round == 1
        assert state.lifecycle_window.last_eligible_round == 3
    opening(context, systems)
    assert len(context.states.find(state_id=OfficialStateId.POISON.value)) == targets


def test_wangping_deputy_does_not_select_all_enemies():
    context, systems, runtime = fixture()
    context.units["a2"].name = "王平"
    admit_and_install_troop_skill(context, systems, runtime)
    opening(context, systems)
    assert len(context.states.find(state_id=OfficialStateId.POISON.value)) == 2


def test_poison_real_ticks_preserve_frozen_source_until_round_four():
    context, systems, runtime = fixture()
    runtime = create_wu_dang_fei_jun_runtime("a2")
    context.units["a2"].intelligence = 650
    admit_and_install_troop_skill(context, systems, runtime)
    opening(context, systems)
    poison = context.states.find(state_id=OfficialStateId.POISON.value)[0]
    target = context.units[poison.owner_id]
    before = target.troops
    context.units["a2"].intelligence = 999
    context.units["a2"].troops = 0
    for round_no in (1, 2, 3):
        result = tick(context, systems, target.unit_id, round_no)
        assert len(result.effect_results) == 1
        assert target.troops < before
        before = target.troops
        assert poison.runtime_params.frozen_damage_basis.coefficient == pytest.approx(.96)
        assert poison.runtime_params.frozen_damage_basis.source_formula_facts.source_combat_attribute_at_application == 650
    settle(context, systems, 4)
    assert not tick(context, systems, target.unit_id, 4).effect_results
    assert target.troops == before


@pytest.mark.parametrize("blocker", ["death", "disabled", "intimidation"])
def test_opening_work_is_cancelled_when_source_is_invalid(blocker):
    context, systems, runtime = fixture()
    admit_and_install_troop_skill(context, systems, runtime)
    if blocker == "death": context.units["a1"].troops = 0
    elif blocker == "disabled": runtime.enabled = False
    else:
        systems.state_application_coordinator.apply_candidate(context, StateCandidate(
            state_id=OfficialStateId.INTIMIDATION.value, owner_id="a1", source_id="b1",
            source_skill_id="690222", lifetime_spec=StateLifetimeSpec.round_calendar(expires_round=2),
            runtime_params_candidate=EmptyStateRuntimeParams()))
    opening(context, systems)
    assert not context.states.find(state_id=OfficialStateId.POISON.value)
    assert context.pending_work.trace[-1].status is PendingWorkStatus.CANCELLED
    assert not context.random.probabilities


def test_poison_is_suppressed_then_resumes_without_changing_snapshot():
    context, systems, runtime = fixture()
    admit_and_install_troop_skill(context, systems, runtime)
    opening(context, systems)
    poison = context.states.find(state_id=OfficialStateId.POISON.value)[0]
    systems.state_application_coordinator.apply_candidate(context, StateCandidate(
        state_id=OfficialStateId.INTIMIDATION.value, owner_id="a1", source_id="b1",
        source_skill_id="690222", lifetime_spec=StateLifetimeSpec.round_calendar(expires_round=2),
        runtime_params_candidate=EmptyStateRuntimeParams()))
    before = context.units[poison.owner_id].troops
    tick(context, systems, poison.owner_id, 1)
    assert context.units[poison.owner_id].troops == before
    settle(context, systems, 2, BattlePhase.ROUND_END.value)
    before = context.units[poison.owner_id].troops
    tick(context, systems, poison.owner_id, 3)
    assert context.units[poison.owner_id].troops < before


def fact(context, target="a2"):
    return DamageAftermathFact(damage_instance_id="test-settled-hit", target_id=target,
        source_type=SourceType.NORMAL_ATTACK, damage_type=DamageType.WEAPON,
        assigned_target_damage=100, actual_target_troop_loss=100,
        target_troops_after=context.units[target].troops, target_defeated=False,
        hit_topology=DamageHitTopology.RESOLVED_HIT)


def test_xianzhen_snapshot_and_after_damage_recovery_through_formula_owner():
    context, systems, runtime = fixture(create_xian_zhen_ying_runtime, TroopType.SHIELD)
    admit_and_install_troop_skill(context, systems, runtime)
    state = context.states.find(owner_id="a2", state_id=OfficialStateId.FIRST_AID.value)[0]
    potency = state.runtime_params.recovery_potency_context
    assert potency.source_troops_at_application == 10000
    assert potency.source_attribute_at_application == 650
    assert potency.base_rate == .6 and state.runtime_params.probability == .4
    context.units["a1"].intelligence = 999
    context.units["a1"].troops = 0
    target = context.units["a2"]
    target.troops = 8000
    target.wounded_troops = 2000
    context.current_round = 1
    context.current_phase = BattlePhase.UNIT_ACTION.value
    opportunities = systems.trigger_system.collect_after_damage(context, "a2", fact(context))
    assert len(opportunities) == 1
    result = systems.recovery_opportunity_system.execute(context, opportunities[0])
    expected = systems.treatment_formula_system.calculate(rate=.6, source_troops=10000,
                                                          source_attribute=650).nominal_recovery
    assert result.executed and result.resolution.actual_recovery == expected
    assert context.random.probabilities == [.4]
    assert result.resolution.request.source_id == "a1"
    settle(context, systems, 4)
    assert not systems.trigger_system.collect_after_damage(context, "a2", fact(context))


def test_xianzhen_real_damage_pipeline_triggers_first_aid():
    context, systems, runtime = fixture(create_xian_zhen_ying_runtime, TroopType.SHIELD)
    admit_and_install_troop_skill(context, systems, runtime)
    context.current_round = 1
    context.current_phase = BattlePhase.UNIT_ACTION.value
    hit_runtime = probe(SkillType.ACTIVE)
    hit_runtime.owner_id = "b1"
    context.skill_runtimes.register(hit_runtime)
    systems.effect_executor.execute(context, DamageEffect("b1", "a2", DamageType.WEAPON,
        DamageSourceType.SKILL, coefficient=.5, source_skill_id="probe",
        source_ref=EffectSourceRef(SourceType.ACTIVE_SKILL, source_unit_id="b1",
                                   source_skill_id="probe", source_skill_slot=SkillSlot.LEARNED_2)))
    recoveries = [event for event in context.event_bus.history if event.event_type is EventType.TROOPS_RECOVERED]
    assert recoveries
    assert recoveries[-1].payload["source_skill_id"] == "20096"
    assert .4 in context.random.probabilities


@pytest.mark.parametrize("factory,troop,special", CASES)
def test_engine_automatic_integration_and_finalization(factory, troop, special):
    context, systems, runtime = fixture(factory, troop)
    context.skill_runtimes.register(runtime)
    BattleEngine(context, systems).run()
    assert context.units["a2"].special_troop_id.value == special
    assert not context.states.find()
    assert systems.attribute_system.get_defense(context, context.units["a2"]) == 120
    if troop is TroopType.BOW:
        poison_apps = [e for e in context.event_bus.history if e.event_type is EventType.STATE_APPLIED
                       and e.payload.get("state_id") == OfficialStateId.POISON.value]
        assert len(poison_apps) == 2
        assert all(e.round_no == 1 and e.phase == BattlePhase.ROUND_START.value for e in poison_apps)


@pytest.mark.parametrize("factory,troop,special", CASES)
@pytest.mark.parametrize("failure", ["disabled", "wrong_troop", "mixed", "phase"])
def test_new_skill_admission_rejection_is_atomic(factory, troop, special, failure):
    context, systems, runtime = fixture(factory, troop)
    if failure == "disabled": runtime.enabled = False
    if failure == "wrong_troop": context.units["a1"].troop_type = TroopType.CAVALRY
    if failure == "mixed": context.units["a3"].troop_type = TroopType.CAVALRY
    if failure == "phase": context.current_phase = BattlePhase.ROUND_END.value
    assert admit_and_install_troop_skill(context, systems, runtime).status is not TroopAdmissionStatus.SUCCESS
    assert not context.states.find() and not context.pending_work.trace
    assert all(u.special_troop_id is None for u in context.units.values())


def test_gaoshun_enhancement_stays_blank_with_baseline_effects():
    context, systems, runtime = fixture(create_xian_zhen_ying_runtime, TroopType.SHIELD)
    context.units["a1"].name = "高顺"
    admit_and_install_troop_skill(context, systems, runtime)
    assert GAO_SHUN_COMMANDER_ENHANCEMENT is None
    state = context.states.find(owner_id="a2", state_id=OfficialStateId.FIRST_AID.value)[0]
    assert state.runtime_params.probability == .4
    assert state.runtime_params.recovery_potency_context.base_rate == .6


@pytest.mark.parametrize("factory,troop,special", CASES)
def test_missing_intelligence_rejected_before_mutation(factory, troop, special):
    context, systems, runtime = fixture(factory, troop)
    context.units["a1"].intelligence = None
    with pytest.raises(ValueError, match="intelligence"):
        admit_and_install_troop_skill(context, systems, runtime)
    assert not context.states.find() and not context.pending_work.trace
    assert all(u.special_troop_id is None for u in context.units.values())


def test_wudang_formula_uses_holder_instead_of_commander_or_target():
    context, systems, _ = fixture()
    runtime = create_wu_dang_fei_jun_runtime("a2")
    context.units["a1"].name = "王平"
    context.units["a2"].intelligence = 500
    admit_and_install_troop_skill(context, systems, runtime)
    context.units["a2"].intelligence = 650  # live opening read, then frozen for all ticks
    opening(context, systems)
    states = context.states.find(state_id=OfficialStateId.POISON.value)
    assert len(states) == 3
    assert all(s.source_id == "a2" and s.runtime_params.frozen_damage_basis.coefficient == pytest.approx(.96)
               for s in states)


def test_xianzhen_failed_probability_has_no_heal_and_only_one_roll():
    context, systems, runtime = fixture(create_xian_zhen_ying_runtime, TroopType.SHIELD)
    admit_and_install_troop_skill(context, systems, runtime)
    context.current_round = 1
    context.units["a2"].troops = 8000
    context.units["a2"].wounded_troops = 2000
    calls = []
    def fail(probability):
        calls.append(probability)
        return False
    context.random.chance = fail
    opportunity = systems.trigger_system.collect_after_damage(context, "a2", fact(context))[0]
    result = systems.recovery_opportunity_system.execute(context, opportunity)
    assert not result.executed and result.reason == "PROBABILITY_FAILED"
    assert calls == [.4] and context.units["a2"].troops == 8000


def test_xianzhen_suppression_restoration_and_missed_windows():
    context, systems, runtime = fixture(create_xian_zhen_ying_runtime, TroopType.SHIELD)
    admit_and_install_troop_skill(context, systems, runtime)
    systems.state_application_coordinator.apply_candidate(context, StateCandidate(
        state_id=OfficialStateId.INTIMIDATION.value, owner_id="a1", source_id="b1",
        source_skill_id="690222", lifetime_spec=StateLifetimeSpec.round_calendar(expires_round=2),
        runtime_params_candidate=EmptyStateRuntimeParams()))
    context.current_round = 1
    context.units["a2"].troops = 8000
    context.units["a2"].wounded_troops = 2000
    opportunity = systems.trigger_system.collect_after_damage(context, "a2", fact(context))[0]
    result = systems.recovery_opportunity_system.execute(context, opportunity)
    assert not result.executed and not context.random.probabilities
    assert systems.attribute_system.get_defense(context, context.units["a2"]) == 120
    settle(context, systems, 2, BattlePhase.ROUND_END.value)
    context.current_round = 3
    opportunity = systems.trigger_system.collect_after_damage(context, "a2", fact(context))[0]
    assert systems.recovery_opportunity_system.execute(context, opportunity).executed
    assert context.random.probabilities == [.4]
    settle(context, systems, 4)
    assert not systems.trigger_system.collect_after_damage(context, "a2", fact(context))
    assert systems.attribute_system.get_defense(context, context.units["a2"]) == 142


def test_poison_legacy_always_active_gate_is_not_changed_by_adapter():
    from sgs_v2.battle_core.skill_runtime_registry import PersistentSourceSkillGate
    context, systems, runtime = fixture()
    admit_and_install_troop_skill(context, systems, runtime)
    opening(context, systems)
    state = context.states.find(state_id=OfficialStateId.POISON.value)[0]
    systems.state_lifecycle_system.refresh(context, instance_id=state.instance_id,
        source_id=state.source_id, source_skill_id=state.source_skill_id,
        source_skill_slot=state.source_skill_slot, lifecycle_window=state.lifecycle_window,
        runtime_params=replace(state.runtime_params, source_skill_gate=PersistentSourceSkillGate.always_active()))
    systems.state_application_coordinator.apply_candidate(context, StateCandidate(
        state_id=OfficialStateId.INTIMIDATION.value, owner_id="a1", source_id="b1",
        source_skill_id="690222", lifetime_spec=StateLifetimeSpec.round_calendar(expires_round=2),
        runtime_params_candidate=EmptyStateRuntimeParams()))
    before = context.units[state.owner_id].troops
    tick(context, systems, state.owner_id, 1)
    assert context.units[state.owner_id].troops < before


def test_default_two_target_contract_remains_fail_closed_for_one_enemy():
    context, systems, runtime = fixture()
    admit_and_install_troop_skill(context, systems, runtime)
    context.units["b2"].troops = 0
    context.units["b3"].troops = 0
    with pytest.raises(ValueError, match="insufficient candidates"):
        opening(context, systems)
    assert not context.states.find(state_id=OfficialStateId.POISON.value)


def test_opening_repeat_admission_does_not_schedule_again():
    context, systems, runtime = fixture()
    admit_and_install_troop_skill(context, systems, runtime)
    count = len(context.pending_work.trace)
    result = admit_and_install_troop_skill(context, systems, create_wu_dang_fei_jun_runtime("a3"))
    assert result.status is TroopAdmissionStatus.REJECTED_ALREADY_INSTALLED
    assert len(context.pending_work.trace) == count
