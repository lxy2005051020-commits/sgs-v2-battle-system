"""Jinfan bounded-runtime tests. Placeholder formulas remain explicit research boundaries."""
from dataclasses import replace

import pytest

from sgs_v2.battle_core import (
    BattleEngine, BattlePhase, EventType, OfficialStateId, StateCandidate,
    StateLifetimeSpec, TroopAdmissionStatus, TroopType, admit_and_install_troop_skill,
    create_jin_fan_jun_runtime,
)
from sgs_v2.battle_core.normal_attack_followup import (
    NORMAL_ATTACK_FOLLOWUP_STATE_ID, FollowupTargetMode,
    NormalAttackFollowupParams, TargetStateBranchFollowup,
)
from sgs_v2.battle_core.stage9_integerization import ExactRatio
from sgs_v2.battle_core.stage10_state_params import ContinuousDamageStateParams
from sgs_v2.battle_core.stage11_state_params import DisarmStateParams, StunStateParams
from sgs_v2.battle_core.state_runtime_params import EmptyStateRuntimeParams
from sgs_v2.battle_core.troop_admission import TROOP_SKILL_REGISTRY
from sgs_v2.battle_core.troop_skills.jin_fan_jun import CONFIG, SKILL
from tests.test_stage14_troop_batch01 import setup, settle
from tests.test_stage14_troop_batch02 import tick
from tests.test_stage14_troop_batch03 import attack, followup_events


def fixture(monkeypatch, *, install=True):
    c, s, _ = setup(create_jin_fan_jun_runtime, TroopType.BOW)
    rt = create_jin_fan_jun_runtime("a3")
    if install:
        assert admit_and_install_troop_skill(c, s, rt).status is TroopAdmissionStatus.SUCCESS
        c.current_round = 1
        c.current_phase = BattlePhase.UNIT_ACTION.value
    s.target_system.random_enemy = lambda context, actor: c.units["b2"]
    return c, s, rt


def test_placeholder_formula_allows_production_admission():
    c, s, _ = setup(create_jin_fan_jun_runtime, TroopType.BOW)
    rt = create_jin_fan_jun_runtime("a3")
    assert admit_and_install_troop_skill(c, s, rt).status is TroopAdmissionStatus.SUCCESS
    assert all(c.units[uid].special_troop_id.value == "JIN_FAN_JUN" for uid in ("a1", "a2", "a3"))
    followups = c.states.find(state_id=NORMAL_ATTACK_FOLLOWUP_STATE_ID)
    assert len(followups) == 3
    assert all(st.runtime_params.probability == .45 for st in followups)
    assert all(st.runtime_params.damage.continuous_damage_coefficient == .64 for st in followups)


def test_gan_ning_crit_targets_only_two_non_commanders():
    c, s, _ = setup(create_jin_fan_jun_runtime, TroopType.BOW)
    c.units["a1"].name = "甘宁"
    rt = create_jin_fan_jun_runtime("a3")
    assert admit_and_install_troop_skill(c, s, rt).status is TroopAdmissionStatus.SUCCESS
    crits = c.states.find(state_id=OfficialStateId.CRITICAL.value)
    assert {st.owner_id for st in crits} == {"a2", "a3"}
    assert all(st.runtime_params.chance == .06 for st in crits)
    assert not c.states.find(owner_id="a1", state_id=OfficialStateId.CRITICAL.value)
    followups = c.states.find(state_id=NORMAL_ATTACK_FOLLOWUP_STATE_ID)
    assert len(followups) == 3
    assert all(st.runtime_params.probability == .45 for st in followups)


def test_registry_and_public_runtime_identity():
    assert TROOP_SKILL_REGISTRY["20152"] is CONFIG
    assert CONFIG.definition_factory() == SKILL
    assert create_jin_fan_jun_runtime("a1").definition is SKILL


def test_conversion_and_provider_binding(monkeypatch):
    c, s, rt = fixture(monkeypatch)
    assert all(c.units[uid].special_troop_id.value == "JIN_FAN_JUN" for uid in ("a1", "a2", "a3"))
    states = c.states.find(state_id=NORMAL_ATTACK_FOLLOWUP_STATE_ID)
    assert len(states) == 3
    assert all(st.source_id == "a3" and st.source_skill_slot == rt.skill_slot for st in states)
    assert not c.states.find(owner_id="b1") and not c.random.probabilities


def test_first_proc_applies_dot_from_physical_attacker_without_direct_damage(monkeypatch):
    c, s, rt = fixture(monkeypatch)
    c.units["a2"].attack = 440
    result = attack(c, s)
    rout = c.states.find(state_id=OfficialStateId.ROUT.value)
    assert len(rout) == 1 and rout[0].owner_id == result.actual_target_id
    assert rout[0].source_id == "a2" and rout[0].source_skill_slot is None
    basis = rout[0].runtime_params.frozen_damage_basis
    assert basis.source_unit_id == "a2"
    assert basis.source_formula_facts.source_combat_attribute_at_application == 440
    assert basis.coefficient == .64
    assert c.random.probabilities == [.45]
    assert not followup_events(c, "20152")


def test_second_proc_preserves_dot_and_recovers_only_performer(monkeypatch):
    c, s, rt = fixture(monkeypatch)
    attack(c, s)
    state = c.states.find(state_id=OfficialStateId.ROUT.value)[0]
    generation = state.current_generation_id
    c.units["a2"].troops = 8000
    c.units["a2"].wounded_troops = 2000
    attack(c, s)
    damage = followup_events(c, "20152")
    assert len(damage) == 1 and damage[0].actor_id == "a2" and damage[0].target_id == "b2"
    recovery = [e for e in c.event_bus.history if e.event_type is EventType.TROOPS_RECOVERED]
    assert len(recovery) == 1 and recovery[0].target_id == "a2"
    assert c.units["a2"].troops > 8000 and c.units["a3"].troops == 10000
    assert state.current_generation_id == generation
    assert c.random.probabilities == [.45, .45]


@pytest.mark.parametrize("acted,first,last", [(False, 1, 2), (True, 2, 3)])
def test_two_owner_action_opportunities_and_frozen_formula(monkeypatch, acted, first, last):
    c, s, rt = fixture(monkeypatch)
    if acted:
        c.action_progress.mark_action_start("b2", 1)
    attack(c, s)
    state = c.states.find(state_id=OfficialStateId.ROUT.value)[0]
    assert (state.lifecycle_window.first_eligible_round, state.lifecycle_window.last_eligible_round) == (first, last)
    source_attack = state.runtime_params.frozen_damage_basis.source_formula_facts.source_combat_attribute_at_application
    c.units["a2"].attack = 999
    c.units["a2"].troops = 0
    for round_no in range(first, last + 1):
        before = c.units["b2"].troops
        assert tick(c, s, "b2", round_no).effect_results
        assert c.units["b2"].troops < before
    assert state.runtime_params.frozen_damage_basis.source_formula_facts.source_combat_attribute_at_application == source_attack
    settle(c, s, last + 1)
    assert not tick(c, s, "b2", last + 1).effect_results


def test_failed_proc_does_not_apply_state_or_repeat_target_selection(monkeypatch):
    c, s, rt = fixture(monkeypatch)
    c.random.chance = lambda p: False
    attack(c, s)
    assert not c.states.find(state_id=OfficialStateId.ROUT.value)
    assert not followup_events(c, "20152")


@pytest.mark.parametrize("blocker", ["disabled", "intimidation", "disarm", "stun"])
def test_provider_and_action_blockers_do_not_roll(monkeypatch, blocker):
    c, s, rt = fixture(monkeypatch)
    if blocker == "disabled":
        rt.enabled = False
    else:
        state_id = {"intimidation": OfficialStateId.INTIMIDATION,
                    "disarm": OfficialStateId.DISARM, "stun": OfficialStateId.STUN}[blocker]
        s.state_application_coordinator.apply_candidate(c, StateCandidate(
            state_id=state_id.value, owner_id="a3" if blocker == "intimidation" else "a2",
            source_id="b1", source_skill_id="blocker",
            lifetime_spec=StateLifetimeSpec.round_calendar(expires_round=2),
            runtime_params_candidate={"disarm": DisarmStateParams(), "stun": StunStateParams()}.get(blocker, EmptyStateRuntimeParams())))
    attack(c, s)
    assert not c.random.probabilities
    assert not c.states.find(state_id=OfficialStateId.ROUT.value)


def test_mounted_listener_survives_deputy_provider_death(monkeypatch):
    c, s, rt = fixture(monkeypatch)
    c.units["a3"].troops = 0
    attack(c, s)
    assert c.random.probabilities == [.45]
    assert c.states.find(state_id=OfficialStateId.ROUT.value)


def test_dead_inherited_target_is_not_replaced(monkeypatch):
    c, s, rt = fixture(monkeypatch)
    c.units["b2"].troops = 1
    attack(c, s)
    assert not c.random.probabilities and not c.states.find(state_id=OfficialStateId.ROUT.value)


def test_healing_ban_prevents_damage_derived_recovery(monkeypatch):
    c, s, rt = fixture(monkeypatch)
    attack(c, s)
    c.units["a2"].troops = 8000
    c.units["a2"].wounded_troops = 2000
    s.state_lifecycle_system.apply(c, state_id=OfficialStateId.HEALING_BAN.value, owner_id="a2")
    attack(c, s)
    assert followup_events(c, "20152") and c.units["a2"].troops == 8000


def test_engine_candidate_autoinstall_and_cleanup(monkeypatch):
    c, s, rt = fixture(monkeypatch, install=False)
    c.skill_runtimes.register(rt)
    c.max_rounds = 2
    BattleEngine(c, s).run()
    assert c.ended and not c.states.find()
    assert any(e.event_type is EventType.STATE_APPLIED and e.payload.get("state_id") == "rout"
               for e in c.event_bus.history)


@pytest.mark.parametrize("field,value", [("duration", True), ("duration", 0),
    ("continuous_damage_coefficient", float("nan")), ("continuous_damage_coefficient", -.1),
    ("recovery_ratio", ExactRatio(2)), ("state_id", "")])
def test_generic_branch_validation(field, value):
    with pytest.raises((ValueError, TypeError)):
        replace(SKILL.effect_specs[0].runtime_params.damage, **{field: value})


def test_generic_branch_rejects_random_retargeting():
    with pytest.raises(ValueError, match="inherited"):
        NormalAttackFollowupParams(.45, SKILL.effect_specs[0].runtime_params.damage, FollowupTargetMode.RANDOM_ENEMY)


def test_recovery_amount_uses_followup_damage_amount_and_ceil(monkeypatch):
    c, s, rt = fixture(monkeypatch)
    attack(c, s)
    c.units["a2"].troops = 8000
    c.units["a2"].wounded_troops = 2000
    executions = []
    original = s.effect_executor.execute
    def recording(context, effect):
        result = original(context, effect)
        if getattr(effect, "source_skill_id", None) == "20152" and hasattr(result, "resolution"):
            executions.append(result)
        return result
    monkeypatch.setattr(s.effect_executor, "execute", recording)
    requests = []
    original_recover = s.recovery_system.resolve
    def recovering(context, request):
        requests.append(request)
        return original_recover(context, request)
    monkeypatch.setattr(s.recovery_system, "resolve", recovering)
    attack(c, s)
    assert len(executions) == len(requests) == 1
    damage_amount = executions[0].resolution.assigned_target_damage
    assert requests[0].amount == (damage_amount * 3 + 9) // 10
    assert requests[0].source_state_instance_id == c.states.find(
        owner_id="a2", state_id=NORMAL_ATTACK_FOLLOWUP_STATE_ID)[0].instance_id


def test_target_state_from_another_source_enables_branch(monkeypatch):
    c, s, rt = fixture(monkeypatch)
    s.state_lifecycle_system.apply(c, state_id=OfficialStateId.ROUT.value, owner_id="b2",
        source_id="a1", source_skill_id="other", runtime_params=ContinuousDamageStateParams())
    attack(c, s)
    assert len(followup_events(c, "20152")) == 1
    assert len(c.states.find(state_id=OfficialStateId.ROUT.value)) == 1


def test_missing_coefficient_cannot_execute_dot_when_generic_guard_is_exercised(monkeypatch):
    spec = SKILL.effect_specs[0]
    params = replace(spec.runtime_params,
        damage=replace(spec.runtime_params.damage, continuous_damage_coefficient=None))
    candidate = replace(SKILL, effect_specs=(replace(spec, runtime_params=params),))
    monkeypatch.setitem(TROOP_SKILL_REGISTRY, "20152", replace(
        CONFIG, definition_factory=lambda: candidate, definition_resolver=None,
        supplemental_definition_resolver=None))
    c, s, rt = setup(create_jin_fan_jun_runtime, TroopType.BOW)
    admit_and_install_troop_skill(c, s, rt)
    c.current_round = 1
    c.current_phase = BattlePhase.UNIT_ACTION.value
    with pytest.raises(NotImplementedError, match="confirmed coefficient"):
        attack(c, s)
    assert not c.states.find(state_id=OfficialStateId.ROUT.value)
