from dataclasses import replace
import pytest
from sgs_v2.battle_core import (BattleContext, BattleSystems, BattlePhase, BattleEngine,
    EventBus, RandomSystem, UnitRuntime, TroopType, LineupPosition, SkillSlot,
    SkillDefinition, SkillTargetMode, SkillType, SkillRuntime, DamageRequest,
    DamageSourceType, DamageType, FormationAdmissionStatus,
    admit_and_install_formation_skill, run_pre_battle_preparation_phases)
from sgs_v2.battle_core.xing_yi_zhen import SKILL, create_xing_yi_zhen_runtime
from sgs_v2.battle_core.formation_admission import FORMATION_SKILL_REGISTRY
from sgs_v2.battle_core.skill_definition import DamageSkillEffectSpec
from sgs_v2.battle_core.damage_rate_modifier import RoundDamageRateParams, DAMAGE_RATE_STATE_ID
from sgs_v2.battle_core.state_modifiers import ATTRIBUTE_BONUS_STATE_ID, AttributeBonusParams, register_modifier_state_definitions
from sgs_v2.battle_core.effects import RemoveStateEffect


def scene(provider="A1", kind=SkillType.ACTIVE, troop=TroopType.CAVALRY):
    units = [UnitRuntime(f"{team}{i}", f"{team}{i}", team, 5000, 5000,
        250, 175, 100-i, intelligence=210, troop_type=troop, lineup_position=pos)
        for team in ("A", "B") for i, pos in enumerate(LineupPosition)]
    ctx = BattleContext("xing_yi", {u.unit_id: u for u in units}, EventBus(), RandomSystem(7))
    ctx.current_phase = BattlePhase.PRE_BATTLE.value
    systems = BattleSystems()
    rt = create_xing_yi_zhen_runtime(provider)
    ctx.skill_runtimes.register(rt)
    for i in range(3):
        ctx.skill_runtimes.register(SkillRuntime(SkillDefinition(f"inherent_{i}", "test", .4,
            SkillTargetMode.SINGLE_DETERMINISTIC_ENEMY,
            (DamageSkillEffectSpec(DamageType.WEAPON, 1),), skill_type=kind),
            f"A{i}", SkillSlot.INHERENT))
    return ctx, systems, rt


def install(ctx, s, rt):
    assert admit_and_install_formation_skill(ctx, s, rt).status is FormationAdmissionStatus.SUCCESS


def modifiers(ctx, s, source, target, dtype=DamageType.WEAPON):
    return s.damage_rule_provider.collect(ctx,
        DamageRequest(source, target, dtype, DamageSourceType.SKILL)).modifier_contributions


def test_registry_and_source_static():
    import csv
    from pathlib import Path
    assert FORMATION_SKILL_REGISTRY["22039"].definition_factory() == SKILL
    with (Path(__file__).resolve().parents[1] / "stages/stage14/xing_yi_evidence/static_levels.csv").open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 10 and rows[-1]["base_id"] == "22039"
    assert "最高属性提高60点" in rows[-1]["description"]
    assert "伤害提高16%" in rows[-1]["description"]


@pytest.mark.parametrize("provider", ["A0", "A1", "A2"])
@pytest.mark.parametrize("troop", list(TroopType))
def test_targets_attribute_and_no_rng(provider, troop):
    ctx, s, rt = scene(provider, troop=troop)
    rng = ctx.random._rng.getstate()
    install(ctx, s, rt)
    assert ctx.random._rng.getstate() == rng
    assert s.attribute_system.get_attack(ctx, ctx.units[provider]) == 310
    allies = {u for u in ("A0", "A1", "A2") if u != provider}
    assert {x.owner_id for x in ctx.states.find(state_id=DAMAGE_RATE_STATE_ID)} == allies
    assert {x.owner_id for x in ctx.states.find(state_id=ATTRIBUTE_BONUS_STATE_ID)} == {provider}
    assert not modifiers(ctx, s, provider, "B0")


@pytest.mark.parametrize("dtype", list(DamageType))
@pytest.mark.parametrize("round_no,outgoing,incoming", [(1,-.30,-.30),(2,-.20,-.20),
    (3,-.10,-.10),(4,.16,.01),(5,.32,.02),(6,.48,.03),(8,.80,.05),(10,1.12,.07)])
def test_real_damage_pipeline_curve(round_no, outgoing, incoming, dtype):
    ctx, s, rt = scene()
    install(ctx, s, rt)
    original_ids = {x.instance_id for x in ctx.states.find()}
    ctx.current_round = round_no
    for source, target, rate in [("A0", "B0", outgoing), ("B0", "A2", incoming)]:
        request = DamageRequest(source, target, dtype, DamageSourceType.SKILL)
        trace = s.damage_system.calculate(ctx, request).pipeline_trace.modifier_result
        assert trace.output_damage == pytest.approx(trace.input_damage * (1 + rate))
        assert len(trace.applied_modifiers) == 1
        origin = trace.applied_modifiers[0].contribution.source
        assert origin.source_skill_id == "22039" and origin.applied_by_unit_id == "A1"
    assert {x.instance_id for x in ctx.states.find()} == original_ids


@pytest.mark.parametrize("attribute", ["attack", "defense", "intelligence", "speed"])
def test_snapshot_effective_highest_retained(attribute):
    ctx, s, rt = scene()
    register_modifier_state_definitions(ctx.states)
    s.state_lifecycle_system.apply(ctx, state_id=ATTRIBUTE_BONUS_STATE_ID, owner_id="A1",
        runtime_params=AttributeBonusParams(attribute, 300))
    install(ctx, s, rt)
    snap = ctx.metadata["xing_yi_snapshots"][(rt.owner_id, rt.skill_slot)]
    assert snap["highest_attribute"] == attribute
    ctx.units["A1"].speed = 1000
    own = [x for x in ctx.states.find(state_id=ATTRIBUTE_BONUS_STATE_ID) if x.source_skill_id == "22039"]
    assert len(own) == 1 and own[0].runtime_params == AttributeBonusParams(attribute, 60)


def test_wrong_types_have_no_effect():
    ctx, s, rt = scene()
    other = ctx.skill_runtimes.get("A2", SkillSlot.INHERENT)
    other.definition = replace(other.definition, skill_type=SkillType.ASSAULT)
    install(ctx, s, rt)
    assert not ctx.states.find()
    assert not ctx.metadata["xing_yi_snapshots"][(rt.owner_id, rt.skill_slot)]["eligible"]


@pytest.mark.parametrize("invalid", ["tie", "missing_intelligence", "missing_inherent", "dead", "noncanonical"])
def test_failures_before_effects_rng_or_install_marker(invalid):
    ctx, s, rt = scene()
    if invalid == "tie": ctx.units["A1"].intelligence = 250
    if invalid == "missing_intelligence": ctx.units["A1"].intelligence = None
    if invalid == "missing_inherent":
        from sgs_v2.battle_core.skill_runtime_registry import SkillRuntimeRegistry
        skills = ctx.skill_runtimes.values()
        ctx.skill_runtimes = SkillRuntimeRegistry()
        for skill in skills:
            if (skill.owner_id, skill.skill_slot) != ("A2", SkillSlot.INHERENT):
                ctx.skill_runtimes.register(skill)
    if invalid == "dead": ctx.units["A2"].troops = 0
    if invalid == "noncanonical": rt.definition = replace(SKILL, activation_rate=.5)
    rng = ctx.random._rng.getstate()
    with pytest.raises((ValueError, NotImplementedError)):
        install(ctx, s, rt)
    assert not ctx.states.find()
    assert not ctx.metadata.get("_stage14_installed_formation_keys")
    assert ctx.random._rng.getstate() == rng


def test_scheduler_duplicate_and_defeat_cleanup():
    ctx, s, rt = scene()
    run_pre_battle_preparation_phases(ctx, s)
    assert len(ctx.states.find()) == 3
    ctx.current_phase = BattlePhase.PRE_BATTLE.value
    assert admit_and_install_formation_skill(ctx, s, rt).status is FormationAdmissionStatus.REJECTED_ALREADY_INSTALLED
    ctx.units["A1"].troops = 0
    s.defeat_cleanup_port.commit_defeat(ctx, "A1")
    assert not ctx.states.find() and not modifiers(ctx, s, "A0", "B0")


def test_disabled_provider_and_removed_modifier():
    ctx, s, rt = scene()
    rt.enabled = False
    run_pre_battle_preparation_phases(ctx, s)
    assert not ctx.states.find()
    ctx, s, rt = scene()
    install(ctx, s, rt)
    rate = ctx.states.find(owner_id="A0", state_id=DAMAGE_RATE_STATE_ID)[0]
    s.effect_executor.execute(ctx, RemoveStateEffect(rate.instance_id))
    ctx.current_round = 5
    assert not modifiers(ctx, s, "A0", "B0")
    assert modifiers(ctx, s, "A2", "B0")[0].operand == pytest.approx(1.32)


def test_engine_installs_once():
    ctx, s, rt = scene()
    ctx.current_phase = "NOT_STARTED"
    BattleEngine(context=ctx, systems=s).run()
    assert ctx.metadata["xing_yi_snapshots"][(rt.owner_id, rt.skill_slot)]["eligible"]


def test_generic_round_curve_independent_of_tactic():
    p = RoundDamageRateParams(opening_rates=((-0.5, -0.2),), outgoing_step=.1, incoming_step=.03)
    assert p.rates_at(0) == (-.5, -.2)
    assert p.rates_at(3) == pytest.approx((.2, .06))
    for value in [-1, True, 1.5]:
        with pytest.raises(ValueError): p.rates_at(value)


@pytest.mark.parametrize("kwargs", [dict(opening_rates=()), dict(opening_rates=((0,),)),
    dict(opening_rates=((float("nan"), 0),)), dict(outgoing_step=-.1),
    dict(incoming_step=True), dict(outgoing_rate=.1)])
def test_generic_curve_invalid_schema(kwargs):
    options = dict(opening_rates=((-0.3, -0.3),))
    options.update(kwargs)
    with pytest.raises((ValueError, TypeError)): RoundDamageRateParams(**options)
