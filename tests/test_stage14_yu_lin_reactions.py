from dataclasses import replace
import pytest
from sgs_v2.battle_core import (BattleContext, BattleSystems, EventBus, RandomSystem,
    UnitRuntime, LineupPosition, TroopType, BattlePhase, EventType, SkillSlot,
    create_yu_lin_zhen_runtime, run_pre_battle_preparation_phases, DamageType, DamageSourceType)
from sgs_v2.battle_core.after_damage_support import (AFTER_DAMAGE_SUPPORT_STATE_ID,
    AfterDamageSupportParams)
from sgs_v2.battle_core.damage_aftermath_port import DamageAftermathFact, DamageHitTopology, DamageZeroLossCause
from sgs_v2.battle_core.operation_identity import SourceType
from sgs_v2.battle_core.effects import DamageEffect, ApplyStateEffect, EffectSourceRef
from sgs_v2.battle_core.official_state_catalog import OfficialStateId, register_official_state_definitions
from sgs_v2.battle_core.stage11_state_params import ResistanceStateParams, Stage11TimedFlagParams
from sgs_v2.battle_core.state_modifiers import RECEIVED_RECOVERY_BONUS_STATE_ID, ReceivedRecoveryBonusParams
from sgs_v2.battle_core.stage9_integerization import ExactRatio


def fixture(level=10, provider="A1", slot=SkillSlot.LEARNED_1):
    units = {f"{t}{i}": UnitRuntime(f"{t}{i}", f"{t}{i}", t, 10000, 8000,
        200, 180, 100-i, intelligence=240, troop_type=TroopType.SHIELD, lineup_position=p)
        for t in ("A", "B") for i,p in enumerate(LineupPosition)}
    ctx = BattleContext("yu_lin_reactions", units, EventBus(), RandomSystem(29))
    s = BattleSystems()
    register_official_state_definitions(ctx.states)
    rt = create_yu_lin_zhen_runtime(provider, level=level, slot=slot)
    ctx.skill_runtimes.register(rt)
    ctx.current_phase = BattlePhase.PRE_BATTLE.value
    run_pre_battle_preparation_phases(ctx, s)
    ctx.current_phase = BattlePhase.UNIT_ACTION.value
    return ctx, s, rt


def fact(ctx, target="A1", key="hit", loss=0, source=SourceType.NORMAL_ATTACK,
         topology=DamageHitTopology.RESOLVED_HIT, cause=DamageZeroLossCause.SETTLED_ZERO):
    return DamageAftermathFact(key, target, source, DamageType.WEAPON, loss, loss,
        ctx.units[target].troops, not ctx.units[target].is_alive, topology,
        cause if loss == 0 and topology is DamageHitTopology.RESOLVED_HIT else None,
        source_unit_id="B0")


def rolls(ctx, success=True):
    seen = []
    ctx.random.chance = lambda p: seen.append(p) or success
    return seen


@pytest.mark.parametrize("level", range(1,11))
def test_exact_level_probability_and_treatment_source(level):
    from sgs_v2.battle_core.yu_lin_zhen import LEVEL_RATES
    ctx,s,rt = fixture(level)
    calls = rolls(ctx)
    ctx.current_round = 1
    s.damage_aftermath_port.commit_aftermath(ctx, fact(ctx))
    assert calls == [LEVEL_RATES[level-1][1]]
    assert len(ctx.states.find(state_id="barrier", owner_id="A1")) == 1
    ctx.units[rt.owner_id].troops = 3200
    ctx.current_round = 5
    expected = s.treatment_formula_system.calculate(rate=LEVEL_RATES[level-1][2],
        source_troops=3200, source_attribute=0).nominal_recovery
    s.damage_aftermath_port.commit_aftermath(ctx, fact(ctx, "A0", "heal"))
    history = ctx.metadata["after_damage_support_history"][-1]
    event = [e for e in ctx.event_bus.history if e.event_type is EventType.TROOPS_RECOVERED][-1]
    assert calls == [LEVEL_RATES[level-1][1]]*2
    assert history["source_troops"] == 3200 and history["nominal_recovery"] == expected
    assert event.actor_id == rt.owner_id and event.target_id == "A0"
    assert event.payload["actual_recovery"] == min(expected, 2000)


@pytest.mark.parametrize("round_no,target,eligible", [(0,"A1",False),(1,"A0",False),
    (1,"A1",True),(3,"A2",True),(4,"A1",False),(4,"A0",False),
    (5,"A0",True),(8,"A0",True),(5,"A2",False),(1,"B1",False)])
def test_exact_role_and_round_windows(round_no,target,eligible):
    ctx,s,_=fixture()
    ctx.current_round=round_no
    seen=rolls(ctx,False)
    s.damage_aftermath_port.commit_aftermath(ctx,fact(ctx,target))
    assert seen == ([.25] if eligible else [])


@pytest.mark.parametrize("target,round_no", [("A1",1),("A0",5)])
@pytest.mark.parametrize("cause", list(DamageZeroLossCause))
def test_all_settled_zero_causes_are_eligible(target,round_no,cause):
    ctx,s,_=fixture()
    ctx.current_round=round_no
    seen=rolls(ctx)
    s.damage_aftermath_port.commit_aftermath(ctx,fact(ctx,target,cause=cause))
    assert seen == [.25]


@pytest.mark.parametrize("source", list(SourceType))
def test_topology_and_reaction_permission(source):
    ctx,s,_=fixture()
    ctx.current_round=1
    seen=rolls(ctx,False)
    s.damage_aftermath_port.commit_aftermath(ctx,fact(ctx,source=source))
    eligible=source in {SourceType.NORMAL_ATTACK,SourceType.ACTIVE_SKILL,SourceType.ASSAULT,
        SourceType.PERIODIC_DAMAGE,SourceType.CLEAVE,SourceType.COUNTER}
    assert seen == ([.25] if eligible else [])
    s.damage_aftermath_port.commit_aftermath(ctx,fact(ctx,key="miss",source=source,
        topology=DamageHitTopology.NO_RESOLVED_HIT_EVASION_OR_MISS))
    assert len(seen) == int(eligible)


@pytest.mark.parametrize("success", [False,True])
def test_same_fact_never_rerolls_and_new_hits_have_no_round_cap(success):
    ctx,s,_=fixture()
    ctx.current_round=1
    seen=rolls(ctx,success)
    hit=fact(ctx)
    s.damage_aftermath_port.commit_aftermath(ctx,hit)
    s.damage_aftermath_port.commit_aftermath(ctx,hit)
    for n in range(5): s.damage_aftermath_port.commit_aftermath(ctx,fact(ctx,key=f"new-{n}"))
    assert seen == [.25]*6
    assert len(ctx.states.find(state_id="barrier",owner_id="A1")) == int(success)


def test_existing_barrier_not_refreshed_overwritten_or_stacked():
    ctx,s,_=fixture()
    ctx.current_round=1
    old=s.effect_executor.execute(ctx,ApplyStateEffect("barrier","A1","B1","other",
        runtime_params=ResistanceStateParams(2),expires_round=3,
        expires_phase=BattlePhase.ROUND_START.value)).state_instance
    seen=rolls(ctx)
    s.damage_aftermath_port.commit_aftermath(ctx,fact(ctx))
    assert ctx.states.find(state_id="barrier",owner_id="A1") == [old]
    assert old.runtime_params.remaining_uses == 2
    assert old.expires_round == 3 and seen == [.25]
    assert ctx.metadata["after_damage_support_history"][-1]["status"] == "REJECTED_EXISTING_STATE"


def test_real_damage_consumes_then_zero_hit_replenishes_barrier():
    ctx,s,rt=fixture()
    ctx.current_round=1
    seen=rolls(ctx)
    effect=DamageEffect("B0","A2",DamageType.WEAPON,DamageSourceType.SKILL,
        source_skill_id="fixture",source_ref=EffectSourceRef(SourceType.ACTIVE_SKILL, "B0", "fixture"))
    s.effect_executor.execute(ctx,effect)
    old=ctx.states.find(state_id="barrier",owner_id="A2")[0]
    before=ctx.units["A2"].troops
    s.effect_executor.execute(ctx,effect)
    new=ctx.states.find(state_id="barrier",owner_id="A2")[0]
    assert ctx.units["A2"].troops == before and new.instance_id != old.instance_id
    assert seen == [.25,.25]
    ctx.current_round=4
    s.effect_executor.execute(ctx,effect)
    assert not ctx.states.find(state_id="barrier",owner_id="A2") and seen == [.25,.25]


@pytest.mark.parametrize("provider", ["A0","A1","A2"])
@pytest.mark.parametrize("slot", list(SkillSlot))
def test_provider_death_and_disabling_gate_no_rng(provider,slot):
    ctx,s,rt=fixture(provider=provider,slot=slot)
    ctx.current_round=1
    seen=rolls(ctx)
    rt.enabled=False
    s.damage_aftermath_port.commit_aftermath(ctx,fact(ctx,"A2"))
    assert not seen
    rt.enabled=True
    s.damage_aftermath_port.commit_aftermath(ctx,fact(ctx,"A2",key="enabled"))
    assert seen == [.25]
    ctx.units[provider].troops=0
    s.defeat_cleanup_port.commit_defeat(ctx,provider)
    assert not [x for x in ctx.states.find() if x.source_skill_id == "20836"]
    s.damage_aftermath_port.commit_aftermath(ctx,fact(ctx,"A0",key="dead"))
    assert seen == [.25]


def test_healing_ban_capacity_and_live_source_changes():
    ctx,s,rt=fixture()
    ctx.current_round=5
    seen=rolls(ctx)
    s.effect_executor.execute(ctx,ApplyStateEffect("healing_ban","A0",
        runtime_params=Stage11TimedFlagParams()))
    before=ctx.units["A0"].troops
    s.damage_aftermath_port.commit_aftermath(ctx,fact(ctx,"A0"))
    assert ctx.units["A0"].troops == before and seen == [.25]
    ban=ctx.states.find(state_id="healing_ban")[0]
    s.state_lifecycle_system.remove(ctx,ban.instance_id)
    ctx.units[rt.owner_id].troops=1000
    s.damage_aftermath_port.commit_aftermath(ctx,fact(ctx,"A0",key="new"))
    assert ctx.metadata["after_damage_support_history"][-1]["source_troops"] == 1000
    assert ctx.units["A0"].troops <= 10000


def test_dead_target_and_battle_end_are_ineligible():
    ctx,s,_=fixture()
    ctx.current_round=1
    seen=rolls(ctx)
    ctx.units["A2"].troops=0
    s.damage_aftermath_port.commit_aftermath(ctx,fact(ctx,"A2"))
    ctx.ended=True
    s.damage_aftermath_port.commit_aftermath(ctx,fact(ctx))
    assert not seen


def test_real_normal_attack_after_damage_path():
    ctx,s,_=fixture()
    ctx.current_round=1
    rolls(ctx)
    ctx.random.sample=lambda candidates,k: [next(u for u in candidates if u.unit_id=="A2")]
    s.normal_attack_system.execute(ctx,ctx.units["B0"])
    assert len(ctx.states.find(state_id="barrier",owner_id="A2")) == 1
    assert ctx.metadata["after_damage_support_history"][-1]["actual_loss"] > 0


def test_generation_refresh_allows_a_new_operation_but_battles_stay_isolated():
    ctx,s,_=fixture()
    ctx.current_round=5
    seen=rolls(ctx,False)
    hit=fact(ctx,"A0")
    s.damage_aftermath_port.commit_aftermath(ctx,hit)
    driver=ctx.states.find(state_id=AFTER_DAMAGE_SUPPORT_STATE_ID,owner_id="A0")[0]
    s.state_lifecycle_system.refresh(ctx,instance_id=driver.instance_id,runtime_params=driver.runtime_params)
    s.damage_aftermath_port.commit_aftermath(ctx,hit)
    assert seen == [.25,.25]
    other,systems,_=fixture()
    other.current_round=5
    recorded=rolls(other,False)
    systems.damage_aftermath_port.commit_aftermath(other,fact(other,"A0"))
    assert recorded==[.25]


def test_recovery_modifiers_apply_once_and_full_target_still_rolls():
    ctx,s,_=fixture()
    ctx.current_round=5
    seen=rolls(ctx)
    s.effect_executor.execute(ctx,ApplyStateEffect(RECEIVED_RECOVERY_BONUS_STATE_ID,"A0",
        runtime_params=ReceivedRecoveryBonusParams(ExactRatio(1,5))))
    before=ctx.units["A0"].troops
    s.damage_aftermath_port.commit_aftermath(ctx,fact(ctx,"A0"))
    nominal=ctx.metadata["after_damage_support_history"][-1]["nominal_recovery"]
    from math import ceil
    assert ctx.units["A0"].troops-before == min(ceil(nominal*1.2),2000)
    ctx.units["A0"].troops=10000
    ctx.units["A0"].wounded_troops=0
    s.damage_aftermath_port.commit_aftermath(ctx,fact(ctx,"A0",key="full"))
    assert seen == [.25,.25] and ctx.units["A0"].troops==10000


@pytest.mark.parametrize("kwargs", [dict(probability=1.1,first_round=1,recovery_rate=.3),
    dict(probability=.2,first_round=True,recovery_rate=.3),
    dict(probability=.2,first_round=5,last_round=3,recovery_rate=.3),
    dict(probability=.2,first_round=1),dict(probability=.2,first_round=1,recovery_rate=-1)])
def test_generic_invalid_params(kwargs):
    with pytest.raises((ValueError,TypeError)): AfterDamageSupportParams(**kwargs)
