from dataclasses import replace

import pytest

from test_stage14_troop_batch01 import setup, settle
from sgs_v2.battle_core import (BattlePhase, TroopType, TroopAdmissionStatus, SkillSlot,
    OfficialStateId, StateCandidate, StateLifetimeSpec, SkillDefinition, SkillRuntime,
    SkillTargetMode, SkillType, ApplyStateSkillEffectSpec, admit_and_install_troop_skill, create_xian_deng_si_shi_runtime)
from sgs_v2.battle_core.troop_skills.xian_deng_si_shi import (
    calculate_trigger_probability, calculate_steal_amount, SKILL, CONFIG)
from sgs_v2.battle_core.troop_admission import TROOP_SKILL_REGISTRY
from sgs_v2.battle_core.damage_received_reaction import DAMAGE_RECEIVED_REACTION_STATE_ID
from sgs_v2.battle_core.damage_aftermath_port import (
    DamageAftermathFact, DamageHitTopology, create_damage_aftermath_fact)
from sgs_v2.battle_core.operation_identity import SourceType
from sgs_v2.battle_core.enums import DamageType
from sgs_v2.battle_core.state_runtime_params import EmptyStateRuntimeParams
from sgs_v2.battle_core.stage11_state_params import Stage11TimedFlagParams
from sgs_v2.battle_core.state_modifiers import (
    ATTRIBUTE_BONUS_STATE_ID, ACTIVATION_RATE_BONUS_STATE_ID, AttributeBonusParams)


def fixture(command=500, commander=None, holder="a1"):
    c, s, _ = setup(create_xian_deng_si_shi_runtime, TroopType.BOW)
    c.units[holder].defense = command
    if commander:
        c.units["a1"].name = commander
    rt = create_xian_deng_si_shi_runtime(holder)
    assert admit_and_install_troop_skill(c, s, rt).status is TroopAdmissionStatus.SUCCESS
    c.current_round = 1
    c.current_phase = BattlePhase.UNIT_ACTION.value
    return c, s, rt


def fact(c, key="hit", target="a2", attacker="b2", loss=1):
    return DamageAftermathFact(key, target, SourceType.NORMAL_ATTACK, DamageType.WEAPON,
        loss, loss, c.units[target].troops, not c.units[target].is_alive,
        DamageHitTopology.RESOLVED_HIT, source_unit_id=attacker)


def emit(c, s, key="hit", **kwargs):
    f = fact(c, key, **kwargs)
    s.damage_aftermath_port.commit_aftermath(c, f)
    return f


def rate(s, c, kind=SkillType.ACTIVE, owner="b2"):
    rt = SkillRuntime(SkillDefinition("probe", "probe", .50, SkillTargetMode.FIXED_ALL_ENEMIES,
        (ApplyStateSkillEffectSpec("weakness"),), skill_type=kind), owner, SkillSlot.LEARNED_2)
    return s.state_modifier_support.activation_rate(c, rt)


@pytest.mark.parametrize("x,expected", [(0,.60),(100,.635),(500,.775),(600,.835),
    (799,.9544),(800,.95),(900,.95)])
def test_exact_piecewise_probability(x, expected):
    assert calculate_trigger_probability(x) == pytest.approx(expected)


@pytest.mark.parametrize("x,expected", [(0,21),(100,23),(300,26),(500,29),
    (588,30),(589,31),(620,31),(650,31),(2000,31),(1e308,31)])
def test_recommended_steal_fit_and_cap(x, expected):
    assert calculate_steal_amount(x) == expected


@pytest.mark.parametrize("value", [True, float("nan"), float("inf"), -1, "500"])
def test_invalid_formula_inputs(value):
    with pytest.raises((TypeError, ValueError)):
        calculate_trigger_probability(value)
    with pytest.raises((TypeError, ValueError)):
        calculate_steal_amount(value)


def test_registry_conversion_and_frozen_opening_final_command():
    c, s, _ = setup(create_xian_deng_si_shi_runtime, TroopType.BOW)
    from sgs_v2.battle_core.state_modifiers import register_modifier_state_definitions
    register_modifier_state_definitions(c.states)
    s.state_lifecycle_system.apply(c, owner_id="a1", state_id=ATTRIBUTE_BONUS_STATE_ID,
        runtime_params=AttributeBonusParams("defense", 380))
    rt = create_xian_deng_si_shi_runtime("a1")
    assert rt.definition is SKILL and TROOP_SKILL_REGISTRY["20246"] is CONFIG
    assert admit_and_install_troop_skill(c, s, rt).status is TroopAdmissionStatus.SUCCESS
    assert all(c.units[u].special_troop_id.value == "XIAN_DENG_SI_SHI" for u in ("a1","a2","a3"))
    markers = c.states.find(state_id=DAMAGE_RECEIVED_REACTION_STATE_ID)
    assert len(markers) == 3 and all(m.runtime_params.probability == .775 for m in markers)
    assert all(m.runtime_params.steal_amount == 29 for m in markers)
    assert all(m.source_id == "a1" and m.source_skill_slot is SkillSlot.LEARNED_1 for m in markers)
    c.units["a1"].defense = 800
    c.current_round = 1
    c.current_phase = BattlePhase.UNIT_ACTION.value
    c.units["a2"].troops = 8000
    emit(c,s)
    assert c.random.probabilities[-1] == .775
    assert s.attribute_system.get_defense(c,c.units["a2"]) == 149


def test_actual_normal_hit_steals_from_actual_target_attacker():
    c,s,_ = fixture()
    s.target_system.random_enemy = lambda context, actor: c.units["a2"]
    s.normal_attack_system.execute(c,c.units["b2"])
    assert s.attribute_system.get_defense(c,c.units["a2"]) == 149
    assert s.attribute_system.get_defense(c,c.units["b2"]) == 91
    assert s.attribute_system.get_defense(c,c.units["a3"]) == 120
    assert c.units["a2"].defense == 120 and c.units["b2"].defense == 120
    assert not c.states.find(state_id=ACTIVATION_RATE_BONUS_STATE_ID)


@pytest.mark.parametrize("troops,max_troops,attacker_troops,steals", [
    (5000,10000,5000,False),(4000,10000,5000,True),
    (6000,20000,5000,True),(6000,10000,5000,False)])
def test_percentage_comparison_and_equal_enters_rate_branch(troops,max_troops,attacker_troops,steals):
    c,s,_ = fixture()
    c.units["a2"].troops = troops
    c.units["a2"].max_troops = max_troops
    c.units["b2"].troops = attacker_troops
    emit(c,s)
    assert s.attribute_system.get_defense(c,c.units["a2"]) == (149 if steals else 120)
    assert rate(s,c) == pytest.approx(.50 if steals else .47)
    assert rate(s,c,SkillType.ASSAULT) == .50


@pytest.mark.parametrize("commander,cap", [(None,4),("麹义",5),("麴义",5),("鞠义",5),("曹操",4)])
@pytest.mark.parametrize("steals", [True,False])
def test_stack_caps_and_no_half_transfer(commander,cap,steals):
    c,s,_ = fixture(commander=commander)
    c.units["a2"].troops = 8000 if steals else 10000
    for i in range(8):
        emit(c,s,str(i))
    assert s.attribute_system.get_defense(c,c.units["a2"]) == (120 + 29*cap if steals else 120)
    assert s.attribute_system.get_defense(c,c.units["b2"]) == (120 - 29*cap if steals else 120)
    assert rate(s,c) == pytest.approx(.50 if steals else .50 - .03*cap)


def test_independent_expiry_and_reuse_capacity():
    c,s,_ = fixture()
    c.units["a2"].troops = 8000
    emit(c,s,"r1")
    c.current_round = 2
    emit(c,s,"r2")
    assert s.attribute_system.get_defense(c,c.units["a2"]) == 178
    settle(c,s,3)
    assert s.attribute_system.get_defense(c,c.units["a2"]) == 149
    assert s.attribute_system.get_defense(c,c.units["b2"]) == 91
    settle(c,s,4)
    assert s.attribute_system.get_defense(c,c.units["a2"]) == 120
    assert s.attribute_system.get_defense(c,c.units["b2"]) == 120


def test_rng_failure_duplicate_and_battle_isolation():
    c,s,_ = fixture()
    c.units["a2"].troops = 8000
    emit(c,s)
    count = len(c.random.probabilities)
    emit(c,s)
    assert len(c.random.probabilities) == count
    assert s.attribute_system.get_defense(c,c.units["a2"]) == 149
    c2,s2,_ = fixture()
    c2.units["a2"].troops = 8000
    c2.random.chance = lambda probability: False
    emit(c2,s2)
    assert s2.attribute_system.get_defense(c2,c2.units["a2"]) == 120
    c3,s3,_ = fixture()
    c3.units["a2"].troops = 8000
    emit(c3,s3)
    assert s3.attribute_system.get_defense(c3,c3.units["a2"]) == 149


@pytest.mark.parametrize("case", ["miss","zero","dead_target","dead_provider","disabled","missing_source","ally","ended"])
def test_no_trigger_or_rng_for_ineligible_facts(case):
    c,s,rt = fixture(holder="a3")
    c.units["a2"].troops = 8000
    f = fact(c)
    if case == "miss": f = replace(f, hit_topology=DamageHitTopology.NO_RESOLVED_HIT_EVASION_OR_MISS)
    if case == "zero": f = replace(f, actual_target_troop_loss=0)
    if case == "dead_target": c.units["a2"].troops=0
    if case == "dead_provider": c.units["a3"].troops=0
    if case == "disabled": rt.enabled=False
    if case == "missing_source": f=replace(f,source_unit_id=None)
    if case == "ally": f=replace(f,source_unit_id="a1")
    if case == "ended": c.ended=True
    count=len(c.random.probabilities)
    s.damage_aftermath_port.commit_aftermath(c,f)
    assert len(c.random.probabilities)==count
    assert s.attribute_system.get_defense(c,c.units["a2"])==120


def test_ambush_immunity_canonical_and_legacy_ingress():
    c,s,rt = fixture()
    p=StateCandidate(OfficialStateId.AMBUSH.value,"a2",Stage11TimedFlagParams(),
        source_id="b2",lifetime_spec=StateLifetimeSpec.round_calendar(expires_round=3))
    r=s.state_application_coordinator.apply_candidate(c,p)
    assert not r.committed and not c.states.find(owner_id="a2",state_id="ambush")
    legacy=s.state_lifecycle_system.apply(c,owner_id="a2",state_id="ambush",source_id="b2")
    assert not s.state_effectiveness_policy.evaluate_state(c,legacy).effective
    rt.enabled=False
    assert s.state_effectiveness_policy.evaluate_state(c,legacy).effective


def test_provider_intimidation_suppresses_and_resumes():
    c,s,_=fixture()
    c.units["a2"].troops=8000
    r=s.state_application_coordinator.apply_candidate(c,StateCandidate("intimidation","a1",
        EmptyStateRuntimeParams(),source_id="b1",source_skill_id="blocker",
        lifetime_spec=StateLifetimeSpec.round_calendar(expires_round=3)))
    emit(c,s,"blocked")
    assert not c.random.probabilities
    from sgs_v2.battle_core import StateNode
    roots=(StateNode(r.instance.instance_id),)
    before=s.effectiveness_transition_coordinator.capture(c,roots)
    s.state_lifecycle_system.remove(c,r.instance.instance_id)
    s.effectiveness_transition_coordinator.complete_removed_nodes(c,before,roots)
    emit(c,s,"resumed")
    assert s.attribute_system.get_defense(c,c.units["a2"])==149


def test_factory_retains_physical_damage_source():
    from types import SimpleNamespace
    f=create_damage_aftermath_fact(damage_instance_id="x",target_id="a2",
        source_type=SourceType.ACTIVE_SKILL,damage_type=DamageType.WEAPON,assigned_target_damage=1,
        actual_target_troop_loss=1,target_troops_after=9000,target_defeated=False,
        damage_result=SimpleNamespace(source_id="b2"))
    assert f.source_unit_id=="b2"


@pytest.mark.parametrize("source,damage_source", [(SourceType.ACTIVE_SKILL,"SKILL"),
    (SourceType.ASSAULT,"SKILL"),(SourceType.PERIODIC_DAMAGE,"CONTINUOUS"),(SourceType.COUNTER,"COUNTER")])
def test_production_damage_ingresses_retain_attacker(source,damage_source):
    from sgs_v2.battle_core.damage_system import DamageRequest
    from sgs_v2.battle_core.enums import DamageSourceType
    from sgs_v2.battle_core.operation_identity import OperationLineage
    c,s,_=fixture()
    request=DamageRequest("b2","a2",DamageType.WEAPON,DamageSourceType(damage_source),source_skill_id="incoming")
    lineage=OperationLineage(None,None,None,source,"b2","incoming","b2")
    s.damage_instance_coordinator.execute_partitioned_damage_instance(c,request,lineage)
    assert s.attribute_system.get_defense(c,c.units["a2"])==149
    assert s.attribute_system.get_defense(c,c.units["b2"])==91


def test_generic_bounded_modifier_duplicate_cap_and_validation():
    from sgs_v2.battle_core.state_modifiers import BoundedAttributeBonusParams
    c,s,_=fixture()
    for key,committed in (("one",True),("one",False),("two",True),("three",False)):
        p=StateCandidate(ATTRIBUTE_BONUS_STATE_ID,"a3",
            BoundedAttributeBonusParams("speed",10,key,"generic",2),source_id="b1",source_skill_id="generic")
        assert s.state_application_coordinator.apply_candidate(c,p).committed is committed
    assert s.attribute_system.get_speed(c,c.units["a3"])==30
    with pytest.raises(ValueError): BoundedAttributeBonusParams("speed",10,"key","group",0)
    with pytest.raises(ValueError): BoundedAttributeBonusParams("speed",10,1,"group",2)


def test_invalid_admission_and_no_duplicate_installation():
    c,s,rt=setup(create_xian_deng_si_shi_runtime,TroopType.SPEAR)
    assert admit_and_install_troop_skill(c,s,rt).status is TroopAdmissionStatus.REJECTED_INVALID_TROOP
    assert not c.states.find() and all(u.special_troop_id is None for u in c.units.values())
    c,s,rt=fixture()
    c.current_phase=BattlePhase.PRE_BATTLE.value
    n=len(c.states.find())
    assert admit_and_install_troop_skill(c,s,rt).status is TroopAdmissionStatus.REJECTED_ALREADY_INSTALLED
    assert len(c.states.find())==n


def test_full_engine_installs_and_finalizes_cleanly():
    from sgs_v2.battle_core import BattleEngine
    c,s,rt=setup(create_xian_deng_si_shi_runtime,TroopType.BOW)
    c.units["a1"].defense=500
    c.skill_runtimes.register(rt)
    result=BattleEngine(c,s).run()
    assert c.ended and result.rounds_completed>0
    assert not c.states.find()
    assert any(e.payload.get("source_skill_id")=="20246" and
        e.payload.get("runtime_params_type")=="BoundedAttributeBonusParams" for e in c.event_bus.history)


def test_real_cleave_damage_reacts_for_each_secondary_target():
    from sgs_v2.battle_core.stage9_state_params import CleaveStateParams
    from sgs_v2.battle_core.stage9_integerization import ExactRatio
    c,s,_=fixture()
    s.state_lifecycle_system.apply(c,owner_id="b2",state_id="cleave",source_id="b2",
        source_skill_id="incoming_cleave",source_skill_slot=SkillSlot.INHERENT,
        runtime_params=CleaveStateParams(ExactRatio(1,2)))
    s.target_system.random_enemy=lambda context,actor:c.units["a2"]
    s.normal_attack_system.execute(c,c.units["b2"])
    assert s.attribute_system.get_defense(c,c.units["a1"])==529
    assert s.attribute_system.get_defense(c,c.units["a2"])==149
    assert s.attribute_system.get_defense(c,c.units["a3"])==149
    assert s.attribute_system.get_defense(c,c.units["b2"])==33
