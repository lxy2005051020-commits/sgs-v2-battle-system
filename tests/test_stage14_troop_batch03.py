"""Real normal-hit / followup / recovery / combo regressions for batch03."""
from dataclasses import replace

import pytest

from tests.test_stage14_troop_batch01 import setup, settle
from sgs_v2.battle_core import (
    BattleEngine, BattlePhase, DamageType, EventType, OfficialStateId,
    StateCandidate, StateLifetimeSpec, TroopAdmissionStatus, TroopType,
    admit_and_install_troop_skill, create_bai_er_bing_runtime, create_da_ji_shi_runtime,
)
from sgs_v2.battle_core.execution_right_system import FutureBranchKind, admit_action_scope
from sgs_v2.battle_core.normal_attack_followup import (
    NORMAL_ATTACK_FOLLOWUP_STATE_ID, NormalAttackFollowupParams,
    ProbabilisticComboParams, FollowupTargetMode,
)
from sgs_v2.battle_core.skill_definition import DamageSkillEffectSpec
from sgs_v2.battle_core.state_runtime_params import EmptyStateRuntimeParams
from sgs_v2.battle_core.stage11_state_params import DisarmStateParams, StunStateParams
from sgs_v2.battle_core.execution_right_system import LegacyFinalizationBarrier

CASES = [(create_bai_er_bing_runtime, "BAI_ER_BING", .45),
         (create_da_ji_shi_runtime, "DA_JI_SHI", .35)]


def fixture(factory=create_bai_er_bing_runtime, *, holder="a1", commander=None):
    c, s, _ = setup(factory, TroopType.SPEAR)
    for u in c.units.values():
        u.intelligence = 100
    c.units["a2"].intelligence = 500
    if commander:
        c.units["a1"].name = commander
    rt = factory(holder)
    assert admit_and_install_troop_skill(c, s, rt).status is TroopAdmissionStatus.SUCCESS
    c.current_round = 1
    c.current_phase = BattlePhase.UNIT_ACTION.value
    return c, s, rt


def attack(c, s, actor="a2"):
    return s.normal_attack_system.execute(c, c.units[actor])


def followup_events(c, skill_id):
    return [e for e in c.event_bus.history if e.event_type is EventType.DAMAGE_DEALT
            and e.payload.get("source_skill_id") == skill_id]


@pytest.mark.parametrize("factory,special,probability", CASES)
def test_full_team_installation_and_single_followup(factory, special, probability):
    c, s, rt = fixture(factory)
    assert not c.random.probabilities
    assert all(c.units[uid].special_troop_id.value == special for uid in ("a1", "a2", "a3"))
    assert len(c.states.find(state_id=NORMAL_ATTACK_FOLLOWUP_STATE_ID)) == 3
    assert not c.states.find(owner_id="b1")
    result = attack(c, s)
    assert c.random.probabilities == [probability]
    events = followup_events(c, rt.definition.skill_id)
    assert len(events) == 1
    assert events[0].actor_id == "a2"
    if special == "BAI_ER_BING":
        assert events[0].target_id == result.actual_target_id
    else:
        assert s.attribute_system.get_attack(c, c.units["a2"]) == 134
    assert len([e for e in c.event_bus.history if e.event_type is EventType.NORMAL_ATTACK]) == 1


@pytest.mark.parametrize("commander,coefficient", [(None, 1.10), ("陈到", 1.30)])
def test_bai_er_commander_branch_with_deputy_holder(commander, coefficient):
    c, s, rt = fixture(holder="a3", commander=commander)
    state = c.states.find(owner_id="a2", state_id=NORMAL_ATTACK_FOLLOWUP_STATE_ID)[0]
    assert state.source_id == "a3"
    assert state.runtime_params.damage.coefficient == coefficient
    attack(c, s)
    assert len(followup_events(c, "20099")) == 1


def test_chen_dao_deputy_does_not_enable_commander_branch():
    c, s, rt = fixture()
    c.units["a2"].name = "陈到"
    assert c.states.find(owner_id="a2", state_id=NORMAL_ATTACK_FOLLOWUP_STATE_ID)[0].runtime_params.damage.coefficient == 1.1


def test_physical_performer_supplies_formula_and_receives_lifesteal():
    c, s, rt = fixture()
    c.units["a2"].troops = 8000
    c.units["a2"].wounded_troops = 2000
    c.units["a1"].intelligence = 1
    attack(c, s)
    event = followup_events(c, "20099")[0]
    assert event.actor_id == "a2"
    assert c.units["a2"].troops > 8000
    assert c.units["a1"].troops == 10000
    assert any(e.event_type is EventType.TROOPS_RECOVERED and e.target_id == "a2"
               for e in c.event_bus.history)


@pytest.mark.parametrize("factory,special,probability", CASES)
def test_failed_proc_has_no_damage_or_selector_rng(factory, special, probability):
    c, s, rt = fixture(factory)
    c.random.chance = lambda p: c.random.probabilities.append(p) or False
    attack(c, s)
    assert c.random.probabilities == [probability]
    assert not followup_events(c, rt.definition.skill_id)


@pytest.mark.parametrize("factory,special,probability", CASES)
@pytest.mark.parametrize("blocker", ["disabled", "intimidation", "disarm", "stun"])
def test_invalid_provider_or_blocked_normal_attack_does_not_roll(factory, special, probability, blocker):
    c, s, rt = fixture(factory)
    if blocker == "disabled":
        rt.enabled = False
    else:
        state = {"intimidation": OfficialStateId.INTIMIDATION,
                 "disarm": OfficialStateId.DISARM, "stun": OfficialStateId.STUN}[blocker]
        uid = "a1" if blocker == "intimidation" else "a2"
        s.state_application_coordinator.apply_candidate(c, StateCandidate(
            state_id=state.value, owner_id=uid, source_id="b1", source_skill_id="blocker",
            lifetime_spec=StateLifetimeSpec.round_calendar(expires_round=2),
            runtime_params_candidate={"disarm": DisarmStateParams(), "stun": StunStateParams()}.get(blocker, EmptyStateRuntimeParams())))
    attack(c, s)
    assert not followup_events(c, rt.definition.skill_id)
    assert not c.random.probabilities


def test_dead_inherited_target_is_not_replaced_and_does_not_roll():
    c, s, rt = fixture()
    c.units["b2"].troops = 0
    c.units["b3"].troops = 0
    # Kill a deputy while an enemy commander stays alive: battle itself continues.
    c.units["b2"].troops = 1
    s.target_system.random_enemy = lambda context, attacker: c.units["b2"]
    attack(c, s)
    assert c.units["b2"].troops == 0
    assert not followup_events(c, "20099")
    assert not c.random.probabilities


def test_zhang_he_only_commander_gets_probabilistic_combo_and_team_probability():
    c, s, rt = fixture(create_da_ji_shi_runtime, holder="a3", commander="张郃")
    combo = c.states.find(state_id=OfficialStateId.COMBO.value)
    assert len(combo) == 1 and combo[0].owner_id == "a1" and combo[0].source_id == "a3"
    assert isinstance(combo[0].runtime_params, ProbabilisticComboParams)
    assert combo[0].runtime_params.probability == .45
    attack(c, s)
    assert c.random.probabilities == [.4]


@pytest.mark.parametrize("success,count", [(True, 2), (False, 1)])
def test_combo_real_action_has_at_most_two_hits_and_each_hit_can_followup(success, count):
    c, s, rt = fixture(create_da_ji_shi_runtime, holder="a3", commander="张郃")
    def chance(p):
        c.random.probabilities.append(p)
        return success if p == .45 else True
    c.random.chance = chance
    # Bind coordinator exactly as the normal damage entrypoint does.
    s.finalization_coordinator.observe_legacy_barrier(c, LegacyFinalizationBarrier.ROUND_START_HOOKS_SETTLED)
    key = "test-action"
    permit = s.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, key)
    scope = admit_action_scope(c, s.future_admission_gate, permit, c.units["a1"], key)
    result = s.action_system.execute(c, c.units["a1"], scope)
    assert scope.physical_normal_attack_count == count
    assert len(followup_events(c, "20125")) == count
    assert c.random.probabilities == [.45] + [.4] * count
    assert (result.combo_attack_result is not None) == success


@pytest.mark.parametrize("factory,special,probability", CASES)
def test_wrong_troop_and_missing_slot_are_rejected_before_mutation(factory, special, probability):
    c, s, rt = setup(factory, TroopType.BOW)
    assert admit_and_install_troop_skill(c, s, rt).status is TroopAdmissionStatus.REJECTED_INVALID_TROOP
    assert not c.states.find()
    for u in c.units.values():
        u.troop_type = TroopType.SPEAR
    rt.skill_slot = None
    assert admit_and_install_troop_skill(c, s, rt).status is TroopAdmissionStatus.REJECTED_PROVIDER_SLOT_CONFLICT
    assert all(u.special_troop_id is None for u in c.units.values())


@pytest.mark.parametrize("factory,special,probability", CASES)
def test_engine_autoinstall_and_final_cleanup(factory, special, probability):
    c, s, rt = setup(factory, TroopType.SPEAR)
    for u in c.units.values():
        u.intelligence = 100
    c.skill_runtimes.register(rt)
    c.max_rounds = 1
    BattleEngine(c, s).run()
    assert followup_events(c, rt.definition.skill_id)
    assert c.ended and not c.states.find()


@pytest.mark.parametrize("value", [True, -.1, 1.01, float("nan"), float("inf")])
def test_generic_probability_parameters_reject_invalid_values(value):
    with pytest.raises((ValueError, TypeError)):
        ProbabilisticComboParams(probability=value)
    with pytest.raises((ValueError, TypeError)):
        NormalAttackFollowupParams(value, DamageSkillEffectSpec(DamageType.WEAPON), FollowupTargetMode.RANDOM_ENEMY)


@pytest.mark.parametrize("factory,special,probability", CASES)
def test_mounted_listener_survives_deputy_provider_death(factory, special, probability):
    c, s, rt = fixture(factory, holder="a3")
    c.units["a3"].troops = 0
    attack(c, s)
    assert len(followup_events(c, rt.definition.skill_id)) == 1
    assert c.random.probabilities == [probability]


@pytest.mark.parametrize("factory,special,probability", CASES)
def test_temporary_suppression_resumes_after_expiry_without_reinstall(factory, special, probability):
    c, s, rt = fixture(factory)
    s.state_application_coordinator.apply_candidate(c, StateCandidate(
        state_id=OfficialStateId.INTIMIDATION.value, owner_id="a1", source_id="b1", source_skill_id="blocker",
        lifetime_spec=StateLifetimeSpec.round_calendar(expires_round=2),
        runtime_params_candidate=EmptyStateRuntimeParams()))
    attack(c, s)
    assert not c.random.probabilities
    settle(c, s, 2, BattlePhase.ROUND_END.value)
    c.current_phase = BattlePhase.UNIT_ACTION.value
    attack(c, s)
    assert c.random.probabilities == [probability]
    assert len(followup_events(c, rt.definition.skill_id)) == 1


def test_da_ji_fresh_target_can_differ_from_normal_actual_target():
    c, s, rt = fixture(create_da_ji_shi_runtime)
    s.target_system.random_enemy = lambda context, attacker: c.units["b2"]
    s.target_system.random_units = lambda context, candidates, *, count: [c.units["b3"]]
    result = attack(c, s)
    assert result.actual_target_id == "b2"
    assert followup_events(c, "20125")[0].target_id == "b3"


def test_bai_er_damage_responds_to_performer_intelligence_not_provider():
    def run(actor_intelligence, holder_intelligence):
        c, s, rt = fixture()
        c.units["a2"].intelligence = actor_intelligence
        c.units["a1"].intelligence = holder_intelligence
        attack(c, s)
        return followup_events(c, "20099")[0].payload["base_damage"]
    assert run(500, 1) == run(500, 900)
    assert run(500, 1) > run(100, 1)


def test_zhang_he_as_deputy_has_no_commander_enhancement():
    c, s, _ = setup(create_da_ji_shi_runtime, TroopType.SPEAR)
    c.units["a2"].name = "张郃"
    admit_and_install_troop_skill(c, s, create_da_ji_shi_runtime("a2"))
    assert not c.states.find(state_id=OfficialStateId.COMBO.value)
    assert all(st.runtime_params.probability == .35
               for st in c.states.find(state_id=NORMAL_ATTACK_FOLLOWUP_STATE_ID))


@pytest.mark.parametrize("factory,special,probability", CASES)
def test_commander_kill_latches_victory_before_followup(factory, special, probability):
    c, s, rt = fixture(factory)
    c.units["b1"].troops = 1
    s.target_system.random_enemy = lambda context, attacker: c.units["b1"]
    attack(c, s)
    assert s.finalization_coordinator.is_latched_or_finalized
    assert not c.random.probabilities
    assert not followup_events(c, rt.definition.skill_id)


def test_disabled_provider_blocks_probabilistic_combo_without_rng():
    c, s, rt = fixture(create_da_ji_shi_runtime, holder="a3", commander="张郃")
    rt.enabled = False
    assert s.action_system._stage9_state_runtime.get_operational_combo(c, "a1") is None
    assert not c.random.probabilities


def test_generic_inherited_selection_rejects_wrong_cardinality():
    c, s, rt = fixture()
    with pytest.raises(ValueError, match="single enemy"):
        s.skill_resolver.resolve(c, rt, inherited_target_ids=("b1", "b2"))


@pytest.mark.parametrize("actual_target", ["b3", "a3"])
def test_bai_er_inherits_post_redirect_target_even_when_friendly(actual_target):
    c, s, rt = fixture()
    if actual_target == "b3":
        from sgs_v2.battle_core.stage9_state_params import GuardStateParams
        s.target_system.random_enemy = lambda context, attacker: c.units["b2"]
        state_id, owner, params = OfficialStateId.GUARD.value, "b2", GuardStateParams("b3")
    else:
        state_id, owner = OfficialStateId.CONFUSION.value, "a2"
        params = c.states.get_definition(state_id).runtime_params_type()
        s.target_system.random_units = lambda context, candidates, *, count: [c.units["a3"]]
    s.state_application_coordinator.apply_candidate(c, StateCandidate(
        state_id=state_id, owner_id=owner, source_id="b1", source_skill_id="test-control",
        lifetime_spec=StateLifetimeSpec.round_calendar(expires_round=2), runtime_params_candidate=params))
    result = attack(c, s)
    assert result.actual_target_id == actual_target
    assert followup_events(c, "20099")[0].target_id == actual_target
