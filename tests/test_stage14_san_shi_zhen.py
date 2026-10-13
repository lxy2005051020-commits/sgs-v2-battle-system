import csv
import re
from pathlib import Path

import pytest

from sgs_v2.battle_core import (BattleContext, BattleSystems, BattlePhase, BattleEngine,
    EventBus, RandomSystem, UnitRuntime, TroopType, LineupPosition, SkillSlot,
    SkillDefinition, SkillTargetMode, SkillType, SkillRuntime,
    DamageRequest, DamageSourceType, DamageType, FormationAdmissionStatus,
    admit_and_install_formation_skill, run_pre_battle_preparation_phases)
from sgs_v2.battle_core.san_shi_zhen import SKILL, LEVEL_RATES, create_san_shi_zhen_runtime
from sgs_v2.battle_core.formation_admission import FORMATION_SKILL_REGISTRY
from sgs_v2.battle_core.action_start_role_split import ROLE_SPLIT_STATE_ID, RoleSplitParams
from sgs_v2.battle_core.damage_rate_modifier import DAMAGE_RATE_STATE_ID, DamageRateParams
from sgs_v2.battle_core.rule_hooks import UnitActionStartHook
from sgs_v2.battle_core.state_modifiers import (ACTIVATION_RATE_BONUS_STATE_ID,
    ActivationRateBonusParams, register_modifier_state_definitions)
from sgs_v2.battle_core.effects import RemoveStateEffect
from sgs_v2.battle_core.skill_definition import DamageSkillEffectSpec
from sgs_v2.battle_core.priority_target_system import PriorityTargetSystem


def attack_skill(owner="A0", slot=SkillSlot.INHERENT, kind=SkillType.ACTIVE, enabled=True):
    return SkillRuntime(SkillDefinition(f"test_{owner}_{int(slot)}", "test", .40,
        SkillTargetMode.SINGLE_DETERMINISTIC_ENEMY, (DamageSkillEffectSpec(DamageType.WEAPON, 1.0),),
        skill_type=kind), owner, slot, enabled)


def scene(level=10, provider="A1", kind=SkillType.ACTIVE, troop=TroopType.CAVALRY):
    units = [UnitRuntime(unit_id=f"{team}{i}", name=f"{team}{i}", team_id=team,
        max_troops=6000, troops=5000, attack=150, defense=150, speed=100-i,
        intelligence=180, troop_type=troop, lineup_position=pos,
        faction=("魏", "蜀", "吴")[i])
        for team in ("A", "B") for i, pos in enumerate(LineupPosition)]
    ctx = BattleContext("san_shi", {u.unit_id: u for u in units}, EventBus(), RandomSystem(7))
    ctx.current_phase = BattlePhase.PRE_BATTLE.value
    s = BattleSystems()
    register_modifier_state_definitions(ctx.states)
    rt = create_san_shi_zhen_runtime(provider, level=level)
    ctx.skill_runtimes.register(rt)
    ctx.skill_runtimes.register(attack_skill(kind=kind))
    return ctx, s, rt


def install(ctx, s, rt):
    assert admit_and_install_formation_skill(ctx, s, rt).status is FormationAdmissionStatus.SUCCESS


def tick(ctx, s, round_no=1, actor="A1"):
    ctx.current_round = round_no
    ctx.current_phase = BattlePhase.UNIT_ACTION_START.value
    return s.rule_hook_system.process(ctx, UnitActionStartHook(round_no, actor))


def split(ctx):
    return {u: next(x.runtime_params for x in ctx.states.find(owner_id=u, state_id=DAMAGE_RATE_STATE_ID)
                   if x.source_skill_id == "22012") for u in ("A1", "A2")}


def test_canonical_registry():
    assert FORMATION_SKILL_REGISTRY["22012"].definition_factory() == SKILL
    assert SKILL.skill_type is SkillType.FORMATION


@pytest.mark.parametrize("level", range(1, 11))
def test_all_level_rates_match_raw_static_and_behavior(level):
    path = Path(__file__).resolve().parents[1] / "stages/stage14/san_shi_evidence/static_levels.csv"
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    raw = rows[level-1]["description"]
    assert tuple(float(x)/100 for x in re.findall(r"([\d.]+)%", raw)) == pytest.approx(LEVEL_RATES[level-1])
    ctx, s, rt = scene(level)
    install(ctx, s, rt)
    tick(ctx, s)
    bonus, reduction, increase = LEVEL_RATES[level-1]
    assert s.state_modifier_support.activation_rate(ctx, ctx.skill_runtimes.get("A0", SkillSlot.INHERENT)) == pytest.approx(.4 + bonus)
    assert split(ctx)["A1"].incoming_rate == -reduction
    assert split(ctx)["A2"].outgoing_rate == increase


@pytest.mark.parametrize("kind", [SkillType.ACTIVE, SkillType.ASSAULT])
def test_bonus_only_commander_inherent_correct_type_and_expiry(kind):
    ctx, s, rt = scene(kind=kind)
    install(ctx, s, rt)
    inherent = ctx.skill_runtimes.get("A0", SkillSlot.INHERENT)
    assert s.state_modifier_support.activation_rate(ctx, inherent) == pytest.approx(.56)
    assert s.state_modifier_support.activation_rate(ctx, attack_skill(slot=SkillSlot.LEARNED_1, kind=kind)) == .40
    assert s.state_modifier_support.activation_rate(ctx, attack_skill(owner="A2", kind=kind)) == .40
    other = SkillType.ASSAULT if kind is SkillType.ACTIVE else SkillType.ACTIVE
    assert s.state_modifier_support.activation_rate(ctx, attack_skill(kind=other)) == .40
    for r in range(1, 6):
        ctx.current_round = r
        assert s.state_modifier_support.activation_rate(ctx, inherent) == pytest.approx(.56)
    ctx.current_round = 6
    ctx.current_phase = BattlePhase.ROUND_START.value
    s.state_lifecycle_system.expire_at(ctx, round_no=6, phase=ctx.current_phase)
    assert s.state_modifier_support.activation_rate(ctx, inherent) == .40
    tick(ctx, s, 6)
    assert split(ctx)["A1"].incoming_rate == -.30


def test_tie_then_swap_clears_old_effects_once_and_keeps_other_provider():
    ctx, s, rt = scene()
    install(ctx, s, rt)
    tick(ctx, s)
    old_ids = {x.instance_id for x in ctx.states.find(state_id=DAMAGE_RATE_STATE_ID)}
    other = s.state_lifecycle_system.apply(ctx, state_id=DAMAGE_RATE_STATE_ID,
        owner_id="A1", source_id="B1", source_skill_id="other",
        runtime_params=DamageRateParams(outgoing_rate=.1))
    tick(ctx, s)  # Replay cannot reset states or mint extra contributions.
    assert old_ids <= {x.instance_id for x in ctx.states.find()}
    s.troop_system.apply_damage(ctx.units["A2"], 200)
    tick(ctx, s, 2)
    assert not old_ids & {x.instance_id for x in ctx.states.find()}
    assert ctx.states.has_instance(other.instance_id)
    assert split(ctx)["A2"].incoming_rate == -.30
    assert split(ctx)["A1"].outgoing_rate == .25
    # Recovery changes NET loss; a tie returns reduction to deputy 1.
    s.troop_system.restore(ctx.units["A2"], 200)
    tick(ctx, s, 3)
    assert split(ctx)["A1"].incoming_rate == -.30
    assert len(ctx.metadata["action_start_role_split_history"]) == 3


def test_entry_snapshot_not_max_or_lowest_current_troops():
    ctx, s, rt = scene()
    ctx.units["A1"].troops = 3500
    install(ctx, s, rt)
    s.troop_system.apply_damage(ctx.units["A2"], 100)
    tick(ctx, s)
    assert split(ctx)["A2"].incoming_rate == -.30


@pytest.mark.parametrize("dtype", list(DamageType))
def test_canonical_damage_pipeline_for_both_damage_types(dtype):
    ctx, s, rt = scene()
    install(ctx, s, rt)
    tick(ctx, s)
    for source, target, factor in (("B0", "A1", .70), ("A2", "B0", 1.25),
                                   ("A1", "B0", 1.0), ("B0", "A2", 1.0)):
        result = s.damage_system.calculate(ctx, DamageRequest(source, target, dtype, DamageSourceType.SKILL))
        mod = result.pipeline_trace.modifier_result
        assert mod.output_damage == pytest.approx(mod.input_damage * factor)
        for item in mod.applied_modifiers:
            assert item.contribution.source.source_skill_id == "22012"
            assert item.contribution.source.applied_by_unit_id == "A1"


@pytest.mark.parametrize("kind", [SkillType.PASSIVE, SkillType.COMMAND, SkillType.FORMATION])
def test_ineligible_inherent_type_no_effect(kind):
    ctx, s, rt = scene(kind=kind)
    # Direct admission avoids generic team formation-limit rejection for synthetic inherent FORMATION.
    install(ctx, s, rt) if kind is not SkillType.FORMATION else None
    if kind is SkillType.FORMATION:
        from sgs_v2.battle_core.san_shi_zhen import install_san_shi_zhen
        install_san_shi_zhen(ctx, s, rt)
    assert not ctx.states.find()


def test_same_faction_no_effect():
    ctx, s, rt = scene()
    ctx.units["A2"].faction = "魏"
    install(ctx, s, rt)
    assert not ctx.states.find()
    assert not ctx.metadata["san_shi_admissions"][(rt.owner_id, rt.skill_slot)]["eligible"]


def test_missing_faction_fails_before_states_or_rng():
    ctx, s, rt = scene()
    ctx.units["A2"].faction = None
    before = ctx.random._rng.getstate()
    with pytest.raises(ValueError, match="explicit faction"):
        install(ctx, s, rt)
    assert not ctx.states.find()
    assert ctx.random._rng.getstate() == before


@pytest.mark.parametrize("provider", ["A0", "A1", "A2"])
def test_provider_action_only_and_defeat_cleanup(provider):
    ctx, s, rt = scene(provider=provider)
    install(ctx, s, rt)
    tick(ctx, s, actor="B0")
    assert not ctx.states.find(state_id=DAMAGE_RATE_STATE_ID)
    tick(ctx, s, actor=provider)
    assert len(ctx.states.find(state_id=DAMAGE_RATE_STATE_ID)) == 2
    s.troop_system.apply_damage(ctx.units[provider], 5000)
    s.defeat_cleanup_port.commit_defeat(ctx, provider)
    assert not [x for x in ctx.states.find() if x.source_skill_id == "22012"]


def test_missing_living_deputy_clears_old_and_skips():
    ctx, s, rt = scene(provider="A0")
    install(ctx, s, rt)
    tick(ctx, s, actor="A0")
    s.troop_system.apply_damage(ctx.units["A2"], 5000)
    s.defeat_cleanup_port.commit_defeat(ctx, "A2")
    tick(ctx, s, 2, "A0")
    assert not ctx.states.find(state_id=DAMAGE_RATE_STATE_ID)
    assert ctx.metadata["action_start_role_split_history"][-1]["status"] == "MISSING_LIVING_DEPUTY_PAIR"


def test_driver_removal_suppresses_old_effect_and_stops_trigger():
    ctx, s, rt = scene()
    install(ctx, s, rt)
    tick(ctx, s)
    driver = ctx.states.find(state_id=ROLE_SPLIT_STATE_ID)[0]
    s.effect_executor.execute(ctx, RemoveStateEffect(driver.instance_id))
    req = DamageRequest("B0", "A1", DamageType.WEAPON, DamageSourceType.SKILL)
    assert not s.damage_rule_provider.collect(ctx, req).modifier_contributions
    tick(ctx, s, 2)
    assert len(ctx.metadata["action_start_role_split_history"]) == 1


def test_disabled_formation_duplicate_and_finalized():
    ctx, s, rt = scene()
    rt.enabled = False
    assert admit_and_install_formation_skill(ctx, s, rt).status is FormationAdmissionStatus.REJECTED_BASELINE_DISABLED
    assert not ctx.states.find()
    rt.enabled = True
    install(ctx, s, rt)
    assert admit_and_install_formation_skill(ctx, s, rt).status is FormationAdmissionStatus.REJECTED_ALREADY_INSTALLED
    ctx.ended = True
    tick(ctx, s)
    assert not ctx.states.find(state_id=DAMAGE_RATE_STATE_ID)


@pytest.mark.parametrize("troop", list(TroopType))
def test_all_troops_and_prebattle_scheduler(troop):
    ctx, s, rt = scene(troop=troop)
    run_pre_battle_preparation_phases(ctx, s)
    assert len(ctx.states.find()) == 2


def test_full_engine_real_action_trigger_round6_and_seed_reproducibility():
    histories = []
    for _ in range(2):
        ctx, s, rt = scene()
        ctx.max_rounds = 6
        engine = BattleEngine(ctx, s)
        engine.run()
        history = ctx.metadata["action_start_role_split_history"]
        assert [x["round"] for x in history] == list(range(1, 7))
        assert all(x["actor_id"] == "A1" for x in history)
        assert not ctx.states.find(state_id=ACTIVATION_RATE_BONUS_STATE_ID)
        histories.append(history)
    assert histories[0] == histories[1]


def test_generic_slot_filter_legacy_addition_cap_and_independent_dimensions():
    ctx, s, rt = scene()
    params = [ActivationRateBonusParams(SkillType.ACTIVE, .2),
              ActivationRateBonusParams(SkillType.ACTIVE, .3, skill_slot=SkillSlot.INHERENT),
              ActivationRateBonusParams(SkillType.ACTIVE, .4, skill_slot=SkillSlot.LEARNED_1)]
    for p in params:
        s.state_lifecycle_system.apply(ctx, state_id=ACTIVATION_RATE_BONUS_STATE_ID,
            owner_id="A0", source_id="B0", source_skill_id="generic", runtime_params=p)
    assert len(ctx.states.find()) == 3
    assert s.state_modifier_support.activation_rate(ctx, attack_skill()) == pytest.approx(.9)
    assert s.state_modifier_support.activation_rate(ctx, attack_skill(slot=SkillSlot.LEARNED_1)) == 1.0
    with pytest.raises(TypeError):
        ActivationRateBonusParams(SkillType.ACTIVE, .1, skill_slot=0)


@pytest.mark.parametrize("level", [0, 11, True, 2.5])
def test_invalid_level(level):
    with pytest.raises(ValueError):
        create_san_shi_zhen_runtime("A1", level=level)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1.1, True])
def test_generic_damage_rate_invalid(value):
    with pytest.raises((ValueError, TypeError)):
        DamageRateParams(outgoing_rate=value)


def test_generic_selector_pair_schema_and_faction_validation():
    ctx, s, rt = scene()
    assert [u.unit_id for u in PriorityTargetSystem(s.target_system).most_lost_troop_deputies(
        ctx, ctx.units["A0"], {"A1": 5000, "A2": 5000})] == ["A1", "A2"]
    with pytest.raises(ValueError):
        RoleSplitParams((("A1", 5000), ("A1", 5000)), .3, .25)
    with pytest.raises(ValueError):
        UnitRuntime("x", "x", "X", 5000, 5000, 100, 100, 100, faction=" ")


@pytest.mark.parametrize("kind", [SkillType.ACTIVE, SkillType.ASSAULT])
def test_real_skill_resolver_consumes_scoped_bonus(kind):
    ctx, s, rt = scene(kind=kind)
    install(ctx, s, rt)
    ctx.current_round = 1
    ctx.current_phase = BattlePhase.UNIT_ACTION.value
    calls = []
    ctx.random.chance = lambda rate: calls.append(rate) or True
    inherent = ctx.skill_runtimes.get("A0", SkillSlot.INHERENT)
    assert s.skill_resolver.resolve(ctx, inherent).effects
    learned = attack_skill(slot=SkillSlot.LEARNED_1, kind=kind)
    ctx.skill_runtimes.register(learned)
    assert s.skill_resolver.resolve(ctx, learned).effects
    assert calls == pytest.approx([.56, .40])


def test_missing_inherent_no_effect_and_noncanonical_definition_rejected():
    ctx, s, rt = scene()
    # A new context carries the formation but no implicit/default inherent tactic.
    from sgs_v2.battle_core.skill_runtime_registry import SkillRuntimeRegistry
    ctx.skill_runtimes = SkillRuntimeRegistry()
    ctx.skill_runtimes.register(rt)
    install(ctx, s, rt)
    assert not ctx.states.find()
    ctx, s, rt = scene()
    from dataclasses import replace
    rt.definition = replace(SKILL, activation_rate=.5)
    with pytest.raises(ValueError, match="canonical loaded"):
        install(ctx, s, rt)
    assert not ctx.states.find()
