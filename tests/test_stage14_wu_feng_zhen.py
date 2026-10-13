import csv
from pathlib import Path
import pytest
from sgs_v2.battle_core import (BattleContext, BattleSystems, BattlePhase, BattleEngine,
    UnitRuntime, TroopType, LineupPosition, RandomSystem, EventBus, SkillSlot,
    DamageRequest, DamageType, DamageSourceType, EventType, SkillRuntime,
    create_wu_feng_zhen_runtime, create_wu_feng_zhen_definition, RecoveryTargetMode,
    admit_and_install_formation_skill)
from sgs_v2.battle_core.periodic_team_support import (PERIODIC_TEAM_SUPPORT_STATE_ID,
    PeriodicTeamSupportParams)
from sgs_v2.battle_core.damage_rate_modifier import DAMAGE_RATE_STATE_ID
from sgs_v2.battle_core.effects import RemoveStateEffect
from sgs_v2.battle_core.rule_hooks import UnitActionStartHook, RoundStartHook
from sgs_v2.battle_core.wu_feng_zhen import LEVEL_RATES, SKILL
from sgs_v2.battle_core.formation_admission import FORMATION_SKILL_REGISTRY


def scene(provider=0, level=10, mode=RecoveryTargetMode.RANDOM_ALLIES, aptitudes=("S", "B", "A"), troop=TroopType.CAVALRY):
    units = [UnitRuntime(f"a{i}", f"a{i}", "A", 10000, 8000 if i == 0 else 10000,
             180, 180, 100-i, intelligence=180, troop_type=troop,
             troop_aptitude=aptitudes[i], lineup_position=pos)
             for i, pos in enumerate(LineupPosition)]
    units += [UnitRuntime("b0", "b0", "B", 10000, 10000, 180, 180, 90,
              intelligence=180, troop_type=troop, lineup_position=LineupPosition.COMMANDER)]
    ctx = BattleContext(battle_id="wu_feng", units={u.unit_id: u for u in units}, random=RandomSystem(127), event_bus=EventBus())
    s = BattleSystems()
    rt = create_wu_feng_zhen_runtime(f"a{provider}", level=level, deputies_only=True,
                                   recovery_target_mode=mode)
    ctx.skill_runtimes.register(rt)
    ctx.current_phase = BattlePhase.PRE_BATTLE.value
    return ctx, s, rt


def install(ctx, s, rt):
    assert admit_and_install_formation_skill(ctx, s, rt).status.value == "SUCCESS"


def act(ctx, s, actor, round):
    ctx.current_round = round
    ctx.current_phase = BattlePhase.UNIT_ACTION_START.value
    return s.rule_hook_system.process(ctx, UnitActionStartHook(round, actor))


def test_registry():
    assert FORMATION_SKILL_REGISTRY["22031"].definition_factory() == SKILL
    assert SKILL.skill_type.value == "FORMATION"


@pytest.mark.parametrize("level", range(1, 11))
def test_static_levels_and_behavior(level):
    rows = list(csv.DictReader((Path(__file__).parents[1] / "stages/stage14/wu_feng_evidence/static_levels.csv").open(encoding="utf-8-sig")))
    recovery, increase = LEVEL_RATES[level-1]
    def pct(rate):
        return f"{rate*100:.1f}".rstrip("0").rstrip(".")
    assert f"治疗率{pct(recovery)}%" in rows[level-1]["description"]
    assert f"伤害提高{pct(increase)}%" in rows[level-1]["description"]
    ctx, s, rt = scene(level=level)
    install(ctx, s, rt)
    act(ctx, s, rt.owner_id, 1)
    expected = s.treatment_formula_system.calculate(rate=recovery, source_troops=10000, source_attribute=0).nominal_recovery
    event = next(e for e in ctx.event_bus.history if e.event_type is EventType.TROOPS_RECOVERED)
    assert event.actor_id == "a1" and event.target_id == "a0"
    assert event.payload["actual_recovery"] == min(expected, 2000)
    act(ctx, s, rt.owner_id, 2)
    states = ctx.states.find(state_id=DAMAGE_RATE_STATE_ID)
    assert len(states) == 1 and states[0].owner_id == "a2"
    assert states[0].runtime_params.outgoing_rate == pytest.approx(increase)


@pytest.mark.parametrize("provider", range(3))
def test_provider_drives_not_deputies_and_only_once(provider):
    ctx, s, rt = scene(provider=provider)
    install(ctx, s, rt)
    for i in range(3):
        if i != provider:
            act(ctx, s, f"a{i}", 1)
    assert "periodic_team_support_history" not in ctx.metadata
    act(ctx, s, rt.owner_id, 1)
    act(ctx, s, rt.owner_id, 1)
    assert len(ctx.metadata["periodic_team_support_history"]) == 1


def test_additive_stacks_round_two_four_six_eight():
    ctx, s, rt = scene()
    install(ctx, s, rt)
    for n in (2, 4, 6, 8):
        act(ctx, s, rt.owner_id, n)
        rate = ctx.states.find(state_id=DAMAGE_RATE_STATE_ID)[0].runtime_params.outgoing_rate
        assert rate == pytest.approx(.15*n/2)
    assert ctx.metadata["periodic_team_support_history"][-1]["cumulative_increase_rate"] == pytest.approx(.60)


@pytest.mark.parametrize("dtype", list(DamageType))
def test_formal_damage_pipeline_and_driver_removal(dtype):
    ctx, s, rt = scene()
    install(ctx, s, rt)
    act(ctx, s, rt.owner_id, 2)
    req = DamageRequest("a2", "b0", dtype, DamageSourceType.SKILL)
    result = s.damage_system.calculate(ctx, req)
    contributions = [m.contribution for m in result.pipeline_trace.modifier_result.applied_modifiers
                     if m.contribution.source.source_skill_id == "22031"]
    assert len(contributions) == 1 and contributions[0].operand == pytest.approx(1.15)
    driver = ctx.states.find(state_id=PERIODIC_TEAM_SUPPORT_STATE_ID)[0]
    s.effect_executor.execute(ctx, RemoveStateEffect(driver.instance_id))
    assert not [m for m in s.damage_rule_provider.collect(ctx, req).modifier_contributions
                if m.source.source_skill_id == "22031"]
    act(ctx, s, rt.owner_id, 4)
    assert len(ctx.metadata["periodic_team_support_history"]) == 1


def test_full_level_ten_and_unconfirmed_lower_level_scaling():
    assert create_wu_feng_zhen_runtime("a0").definition == SKILL
    with pytest.raises(NotImplementedError):
        create_wu_feng_zhen_runtime("a0", level=9)
    with pytest.raises(ValueError, match="explicit recovery target"):
        create_wu_feng_zhen_runtime("a0", deputies_only=True, recovery_target_mode=None)
    ctx, s, rt = scene()
    rt.definition = SKILL
    install(ctx, s, rt)
    assert len(ctx.states.find()) == 2


@pytest.mark.parametrize("aptitudes", [(None, "B", "A"), ("S", None, "A")])
def test_unknown_aptitude_is_atomic(aptitudes):
    ctx, s, rt = scene(aptitudes=aptitudes)
    with pytest.raises(ValueError, match="explicit current-troop aptitude"):
        install(ctx, s, rt)
    assert not ctx.states.find()


def test_duplicate_aptitude_installs_no_effect():
    ctx, s, rt = scene(aptitudes=("S", "A", "A"))
    install(ctx, s, rt)
    assert not ctx.states.find()
    assert not ctx.metadata["wu_feng_admissions"][(rt.owner_id, rt.skill_slot)]["eligible"]


@pytest.mark.parametrize("troop", list(TroopType))
def test_all_static_allowed_troops(troop):
    ctx, s, rt = scene(troop=troop)
    install(ctx, s, rt)
    assert len(ctx.states.find(state_id=PERIODIC_TEAM_SUPPORT_STATE_ID)) == 1


def test_provider_defeat_and_disabled_runtime():
    for defeated in (False, True):
        ctx, s, rt = scene()
        install(ctx, s, rt)
        act(ctx, s, rt.owner_id, 2)
        if defeated:
            ctx.units[rt.owner_id].troops = 0
            s.defeat_cleanup_port.commit_defeat(ctx, rt.owner_id)
        else:
            rt.enabled = False
        if defeated:
            with pytest.raises(ValueError, match="actor must be alive"):
                act(ctx, s, rt.owner_id, 4)
        else:
            act(ctx, s, rt.owner_id, 4)
        assert len(ctx.metadata["periodic_team_support_history"]) == 1
        assert not [m for m in s.damage_rule_provider.collect(ctx,
            DamageRequest("a2", "b0", DamageType.WEAPON, DamageSourceType.SKILL)).modifier_contributions
            if m.source.source_skill_id == "22031"]


@pytest.mark.parametrize("dead_id,round", [("a1", 1), ("a2", 2)])
def test_dead_role_no_reassignment(dead_id, round):
    ctx, s, rt = scene()
    install(ctx, s, rt)
    ctx.units[dead_id].troops = 0
    act(ctx, s, rt.owner_id, round)
    assert "DEFEATED" in ctx.metadata["periodic_team_support_history"][-1]["status"]


def test_random_mode_seed_and_excludes_performer():
    histories = []
    for _ in range(2):
        ctx, s, rt = scene(mode=RecoveryTargetMode.RANDOM_TEAM)
        install(ctx, s, rt)
        for n in (1, 3, 5, 7):
            act(ctx, s, rt.owner_id, n)
        histories.append(ctx.metadata["periodic_team_support_history"])
    assert histories[0] == histories[1]
    assert all(row["target_id"] in ("a0", "a2") for row in histories[0])


def test_full_engine_seed_reproducibility():
    histories = []
    for _ in range(2):
        ctx, s, rt = scene()
        BattleEngine(context=ctx, systems=s).run()
        histories.append(ctx.metadata["periodic_team_support_history"])
    assert histories[0] == histories[1]
    assert {row["kind"] for row in histories[0]} == {"RECOVERY", "OUTGOING_INCREASE"}


def test_generic_params_validate():
    with pytest.raises(ValueError):
        PeriodicTeamSupportParams("a", "a", 1, .1, RecoveryTargetMode.RANDOM_TEAM)
    with pytest.raises(ValueError):
        UnitRuntime("a", "a", "A", 1, 1, 1, 1, 1, troop_aptitude="D")


def test_role_order_is_aptitude_not_deputy_slot():
    ctx, s, rt = scene(aptitudes=("B", "S", "A"))
    install(ctx, s, rt)
    driver = ctx.states.find(state_id=PERIODIC_TEAM_SUPPORT_STATE_ID)[0]
    assert driver.runtime_params.recovery_actor_id == "a2"
    assert driver.runtime_params.increase_target_id == "a1"


def test_recovery_reads_performer_live_troops_not_provider_attribute():
    ctx, s, rt = scene()
    install(ctx, s, rt)
    ctx.units["a1"].troops = 4000
    ctx.units["a1"].intelligence = 900
    act(ctx, s, rt.owner_id, 1)
    row = ctx.metadata["periodic_team_support_history"][-1]
    expected = s.treatment_formula_system.calculate(rate=1.84, source_troops=4000, source_attribute=0)
    assert row["source_troops"] == 4000
    assert row["nominal_recovery"] == expected.nominal_recovery


def test_healing_ban_keeps_canonical_recovery_prevention():
    from sgs_v2.battle_core.official_state_catalog import OfficialStateId, register_official_state_definitions
    from sgs_v2.battle_core.stage11_state_params import Stage11TimedFlagParams
    ctx, s, rt = scene()
    install(ctx, s, rt)
    register_official_state_definitions(ctx.states)
    s.state_lifecycle_system.apply(ctx, state_id=OfficialStateId.HEALING_BAN.value,
                                  owner_id="a0", runtime_params=Stage11TimedFlagParams())
    act(ctx, s, rt.owner_id, 1)
    assert ctx.units["a0"].troops == 8000


def test_round_start_does_not_trigger_and_install_is_idempotent():
    ctx, s, rt = scene()
    install(ctx, s, rt)
    assert admit_and_install_formation_skill(ctx, s, rt).status.value == "REJECTED_ALREADY_INSTALLED"
    ctx.current_round = 1
    ctx.current_phase = BattlePhase.ROUND_START.value
    s.rule_hook_system.process(ctx, RoundStartHook(1))
    assert "periodic_team_support_history" not in ctx.metadata


def test_recovery_selection_honors_canonical_target_policy_exclusion():
    from sgs_v2.battle_core.skill_target_policy import TargetPolicyContribution
    ctx, s, rt = scene()
    install(ctx, s, rt)
    s.skill_target_policy.register_rule_adapter(
        lambda context, operation, candidates: TargetPolicyContribution(excluded_target_ids=("a0",)))
    act(ctx, s, rt.owner_id, 1)
    assert ctx.metadata["periodic_team_support_history"][-1]["target_id"] != "a0"
