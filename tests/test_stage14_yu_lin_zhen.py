"""Authorized partial model and fail-closed full model acceptance tests."""
from dataclasses import replace
import csv
from pathlib import Path
import re
import pytest

from sgs_v2.battle_core import (BattleContext, BattleEngine, BattleSystems, BattlePhase,
    UnitRuntime, TroopType, LineupPosition, RandomSystem, EventBus, SkillSlot,
    SkillDefinition, SkillRuntime, SkillType, SkillTargetMode,
    FormationAdmissionStatus, admit_and_install_formation_skill, run_pre_battle_preparation_phases,
    create_yu_lin_zhen_definition, create_yu_lin_zhen_runtime)
from sgs_v2.battle_core.yu_lin_zhen import SKILL, LEVEL_RATES
from sgs_v2.battle_core.formation_admission import FORMATION_SKILL_REGISTRY, FormationAdmissionRejectedError
from sgs_v2.battle_core.skill_definition import ApplyStateSkillEffectSpec
from sgs_v2.battle_core.state_modifiers import ATTRIBUTE_BONUS_STATE_ID, AttributeBonusParams
from sgs_v2.battle_core.effects import RemoveStateEffect


def scene(provider="A1", level=10, troop=TroopType.SHIELD, command_only=True):
    units = [UnitRuntime(f"{team}{i}", f"{team}{i}", team, 5000, 5000,
        200, 180, 100-i, intelligence=240, troop_type=troop, lineup_position=pos)
        for team in ("A", "B") for i, pos in enumerate(LineupPosition)]
    ctx = BattleContext("yu_lin", {u.unit_id: u for u in units}, EventBus(), RandomSystem(7))
    ctx.current_phase = BattlePhase.PRE_BATTLE.value
    s = BattleSystems()
    rt = create_yu_lin_zhen_runtime(provider, level=level, command_only=command_only)
    ctx.skill_runtimes.register(rt)
    return ctx, s, rt


def install(ctx, s, rt):
    assert admit_and_install_formation_skill(ctx, s, rt).status is FormationAdmissionStatus.SUCCESS


def test_registry_and_exact_static_rows():
    assert FORMATION_SKILL_REGISTRY["20836"].definition_factory() == SKILL
    assert SKILL.skill_type is SkillType.FORMATION
    path = Path(__file__).parents[1] / "stages/stage14/yu_lin_evidence/static_levels.csv"
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 10
    for row, (bonus, chance, treatment) in zip(rows, LEVEL_RATES):
        assert row["base_id"] == "20836"
        assert float(re.search(r"统率提升([\d.]+)", row["description"])[1]) == bonus
        rates = [float(n)/100 for n in re.findall(r"([\d.]+)%", row["description"])]
        assert rates == pytest.approx([chance, chance, treatment])


@pytest.mark.parametrize("level", range(1, 11))
@pytest.mark.parametrize("provider", ["A0", "A1", "A2"])
@pytest.mark.parametrize("troop", list(TroopType))
def test_levels_roles_provider_provenance_and_no_rng(level, provider, troop):
    ctx, s, rt = scene(provider, level, troop)
    originals = {uid: unit.snapshot() for uid, unit in ctx.units.items()}
    rng = ctx.random._rng.getstate()
    install(ctx, s, rt)
    assert s.attribute_system.get_defense(ctx, ctx.units["A0"]) == 180
    assert s.attribute_system.get_defense(ctx, ctx.units["A1"]) == pytest.approx(180 + LEVEL_RATES[level-1][0])
    assert s.attribute_system.get_defense(ctx, ctx.units["A2"]) == pytest.approx(180 + LEVEL_RATES[level-1][0])
    assert s.attribute_system.get_defense(ctx, ctx.units["B1"]) == 180
    states = ctx.states.find()
    assert len(states) == 2 and {state.owner_id for state in states} == {"A1", "A2"}
    for state in states:
        assert state.state_id == ATTRIBUTE_BONUS_STATE_ID
        assert (state.source_id, state.source_skill_id, state.source_skill_slot) == (provider, "20836", rt.skill_slot)
        assert state.runtime_params == AttributeBonusParams("defense", LEVEL_RATES[level-1][0])
    assert ctx.random._rng.getstate() == rng
    assert {uid: unit.snapshot() for uid, unit in ctx.units.items()} == originals
    admission = ctx.metadata["yu_lin_admissions"][(provider, rt.skill_slot)]
    assert admission["mode"] == "COMMAND_ONLY" and len(admission["omitted"]) == 2


@pytest.mark.parametrize("method", ["direct", "scheduler", "engine"])
def test_full_mode_fails_before_states_events_rng_or_passives(method):
    ctx, s, rt = scene(command_only=False)
    passive = SkillDefinition("fixture_passive", "passive", 1, SkillTargetMode.SELF,
        (ApplyStateSkillEffectSpec(ATTRIBUTE_BONUS_STATE_ID, AttributeBonusParams("attack", 30)),),
        skill_type=SkillType.PASSIVE)
    ctx.skill_runtimes.register(SkillRuntime(passive, "A0", SkillSlot.INHERENT))
    rng = ctx.random._rng.getstate()
    before = {uid: unit.snapshot() for uid, unit in ctx.units.items()}
    with pytest.raises(NotImplementedError, match="触发概率.*治疗.*属性读取时点"):
        if method == "direct": admit_and_install_formation_skill(ctx, s, rt)
        elif method == "scheduler": run_pre_battle_preparation_phases(ctx, s)
        else: BattleEngine(context=ctx, systems=s).run()
    assert not ctx.states.find()
    assert not ctx.metadata.get("_stage14_installed_formation_keys")
    assert not ctx.metadata.get("yu_lin_admissions")
    assert ctx.random._rng.getstate() == rng
    assert {uid: unit.snapshot() for uid, unit in ctx.units.items()} == before
    assert not [event for event in ctx.event_bus.history if event.event_type.value.startswith("STATE_")]


@pytest.mark.parametrize("issue", ["dead", "position", "extra", "definition"])
def test_invalid_partial_mode_is_atomic(issue):
    ctx, s, rt = scene()
    if issue == "dead": ctx.units["A2"].troops = 0
    elif issue == "position": ctx.units["A2"].lineup_position = LineupPosition.COMMANDER
    elif issue == "extra":
        unit = replace(ctx.units["A2"], unit_id="A3")
        ctx.units[unit.unit_id] = unit
    else: rt.definition = replace(rt.definition, activation_rate=.5)
    rng = ctx.random._rng.getstate()
    with pytest.raises(ValueError): install(ctx, s, rt)
    assert not ctx.states.find() and not ctx.metadata.get("yu_lin_admissions")
    assert ctx.random._rng.getstate() == rng


def test_duplicate_disabled_full_and_engine_partial():
    ctx, s, rt = scene(command_only=False)
    rt.enabled = False
    run_pre_battle_preparation_phases(ctx, s)
    assert not ctx.states.find()
    ctx, s, rt = scene()
    BattleEngine(context=ctx, systems=s).run()
    assert ctx.metadata["yu_lin_admissions"][(rt.owner_id, rt.skill_slot)]["mode"] == "COMMAND_ONLY"
    ctx, s, rt = scene()
    install(ctx, s, rt)
    assert admit_and_install_formation_skill(ctx, s, rt).status is FormationAdmissionStatus.REJECTED_ALREADY_INSTALLED
    assert len(ctx.states.find()) == 2


def test_two_sides_cleanup_and_fixed_additive_amount():
    ctx, s, rt = scene()
    other = create_yu_lin_zhen_runtime("B2", level=1, command_only=True)
    ctx.skill_runtimes.register(other)
    run_pre_battle_preparation_phases(ctx, s)
    assert len(ctx.states.find()) == 4
    ctx.units["A2"].defense = 300
    assert s.attribute_system.get_defense(ctx, ctx.units["A2"]) == 355
    ctx.units[rt.owner_id].troops = 0
    s.defeat_cleanup_port.commit_defeat(ctx, rt.owner_id)
    assert not [state for state in ctx.states.find() if state.source_skill_id == "20836" and state.source_id == rt.owner_id]
    assert s.attribute_system.get_defense(ctx, ctx.units["A2"]) == 300
    assert s.attribute_system.get_defense(ctx, ctx.units["B1"]) == 207.5
    assert len(ctx.states.find()) == 2


def test_explicit_remove_and_same_team_exclusivity():
    ctx, s, rt = scene()
    install(ctx, s, rt)
    state = ctx.states.find(owner_id="A2")[0]
    s.effect_executor.execute(ctx, RemoveStateEffect(state.instance_id))
    assert s.attribute_system.get_defense(ctx, ctx.units["A2"]) == 180
    ctx, s, rt = scene()
    ctx.skill_runtimes.register(create_yu_lin_zhen_runtime("A2", command_only=True))
    with pytest.raises(FormationAdmissionRejectedError): run_pre_battle_preparation_phases(ctx, s)
    assert not ctx.states.find()


@pytest.mark.parametrize("level", [True, 0, 11, 1.5])
def test_invalid_level(level):
    with pytest.raises(ValueError): create_yu_lin_zhen_definition(level, command_only=True)


def test_partial_mode_requires_explicit_boolean():
    for value in (1, "yes", None):
        with pytest.raises(TypeError): create_yu_lin_zhen_definition(command_only=value)


def test_generic_validator_runs_before_passives_and_is_not_skill_id_specific():
    from sgs_v2.battle_core import (FormationSkillConfig, register_formation_skill_config,
                                  unregister_formation_skill_config)
    ctx, s, rt = scene()
    definition = replace(rt.definition, skill_id="synthetic_checked_formation", name="checked fixture")
    rt.definition = definition
    called = []

    def validator(context, runtime):
        called.append((context.battle_id, runtime.owner_id))
        raise NotImplementedError("fixture rules unavailable")

    register_formation_skill_config(FormationSkillConfig(
        definition.skill_id, definition.name, tuple(TroopType), lambda: definition,
        validator=validator))
    try:
        with pytest.raises(NotImplementedError, match="fixture rules unavailable"):
            run_pre_battle_preparation_phases(ctx, s)
        assert called == [(ctx.battle_id, rt.owner_id)]
        assert not ctx.states.find()
    finally:
        unregister_formation_skill_config(definition.skill_id)
