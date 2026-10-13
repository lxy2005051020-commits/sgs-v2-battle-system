from dataclasses import replace
import csv
from pathlib import Path
import re
import pytest
from sgs_v2.battle_core import (BattleContext, BattleSystems, BattleEngine, BattlePhase,
    EventBus, RandomSystem, UnitRuntime, TroopType, LineupPosition, SkillSlot,
    SkillDefinition, SkillRuntime, SkillTargetMode, SkillType, DamageRequest,
    DamageType, DamageSourceType, FormationAdmissionStatus, admit_and_install_formation_skill,
    run_pre_battle_preparation_phases)
from sgs_v2.battle_core.qian_long_zhen import SKILL, LEVEL_RATES, create_qian_long_zhen_runtime, create_qian_long_zhen_definition
from sgs_v2.battle_core.commander_effect import COMMANDER_EFFECT_ROLE_STATE_ID
from sgs_v2.battle_core.formation_admission import FORMATION_SKILL_REGISTRY
from sgs_v2.battle_core.skill_definition import DamageSkillEffectSpec, ApplyStateSkillEffectSpec
from sgs_v2.battle_core.state_definition import StateDefinition
from sgs_v2.battle_core.state_modifiers import ATTRIBUTE_BONUS_STATE_ID, AttributeBonusParams
from sgs_v2.battle_core.effects import RemoveStateEffect


def scene(provider="A1", level=10, troop=TroopType.CAVALRY, commander_branch=False):
    units = [UnitRuntime(f"{team}{i}", f"{team}{i}", team, 5000, 5000, 200, 180, 100,
        intelligence=240, troop_type=troop, lineup_position=pos, faction=("魏", "蜀", "吴")[i])
        for team in ("A", "B") for i, pos in enumerate(LineupPosition)]
    ctx = BattleContext("qian_long", {u.unit_id: u for u in units}, EventBus(), RandomSystem(7))
    ctx.current_phase = BattlePhase.PRE_BATTLE.value
    systems = BattleSystems()
    rt = create_qian_long_zhen_runtime(provider, level=level)
    ctx.skill_runtimes.register(rt)
    for i in range(3):
        definition = SkillDefinition(f"inherent_{i}", "fixture", 1.0,
            SkillTargetMode.SINGLE_DETERMINISTIC_ENEMY,
            (DamageSkillEffectSpec(DamageType.WEAPON, 1),),
            commander_effect_specs=((DamageSkillEffectSpec(DamageType.STRATEGY, .5),)
                                    if i > 0 or commander_branch else ()))
        ctx.skill_runtimes.register(SkillRuntime(definition, f"A{i}", SkillSlot.INHERENT))
    return ctx, systems, rt


def install(ctx, systems, rt):
    assert admit_and_install_formation_skill(ctx, systems, rt).status is FormationAdmissionStatus.SUCCESS


def test_registry_and_all_exact_source_rows():
    assert FORMATION_SKILL_REGISTRY["22040"].definition_factory() == SKILL
    with (Path(__file__).resolve().parents[1] / "stages/stage14/qian_long_evidence/static_levels.csv").open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 10
    for row, (normal, reduced) in zip(rows, LEVEL_RATES):
        numbers = [float(number) / 100 for number in re.findall(r"([\d.]+)%", row["description"])]
        assert numbers == pytest.approx([normal, .15, normal, normal, reduced])


@pytest.mark.parametrize("provider", ["A0", "A1", "A2"])
@pytest.mark.parametrize("troop", list(TroopType))
@pytest.mark.parametrize("branch", [False, True])
def test_roles_snapshots_and_no_rng(provider, troop, branch):
    ctx, s, rt = scene(provider, troop=troop, commander_branch=branch)
    rng = ctx.random._rng.getstate()
    original = ctx.units["A0"].snapshot()
    install(ctx, s, rt)
    fraction = .05 if branch else .15
    for attr in ("attack", "intelligence", "speed", "defense"):
        assert getattr(s.attribute_system, f"get_{attr}")(ctx, ctx.units["A0"]) == pytest.approx(original[attr] * (1 + fraction))
    assert ctx.units["A0"].snapshot() == original
    assert ctx.random._rng.getstate() == rng
    assert len(ctx.states.find()) == 10
    assert [s.commander_effect_policy.enabled(ctx, f"A{i}") for i in range(3)] == [False, True, True]
    assert not s.commander_effect_policy.enabled(ctx, "B1")
    assert s.commander_effect_policy.enabled(ctx, "B0")
    assert [ctx.units[f"A{i}"].lineup_position for i in range(3)] == list(LineupPosition)


@pytest.mark.parametrize("level", range(1, 11))
@pytest.mark.parametrize("branch", [False, True])
def test_all_level_attribute_branches(level, branch):
    ctx, s, rt = scene(level=level, commander_branch=branch)
    install(ctx, s, rt)
    assert s.attribute_system.get_attack(ctx, ctx.units["A0"]) == pytest.approx(200 * (1 + LEVEL_RATES[level-1][int(branch)]))


@pytest.mark.parametrize("dtype", list(DamageType))
@pytest.mark.parametrize("source,target,rate", [("A0","B0",-.15),("A1","B0",.15),
    ("A2","B0",.15),("B0","A1",-.15),("B0","A2",-.15),("B0","A0",0)])
def test_actual_damage_pipeline(dtype, source, target, rate):
    ctx, s, rt = scene()
    install(ctx, s, rt)
    trace = s.damage_system.calculate(ctx, DamageRequest(source, target, dtype, DamageSourceType.SKILL)).pipeline_trace.modifier_result
    assert trace.output_damage == pytest.approx(trace.input_damage * (1 + rate))
    for applied in trace.applied_modifiers:
        assert applied.contribution.source.source_skill_id == "22040"


def test_commander_presence_in_disabled_learned_slot_and_retained_snapshot():
    ctx, s, rt = scene()
    base = ctx.skill_runtimes.get("A2", SkillSlot.INHERENT).definition
    ctx.skill_runtimes.register(SkillRuntime(base, "A0", SkillSlot.LEARNED_2, enabled=False))
    from sgs_v2.battle_core.state_modifiers import register_modifier_state_definitions
    register_modifier_state_definitions(ctx.states)
    s.state_lifecycle_system.apply(ctx, state_id=ATTRIBUTE_BONUS_STATE_ID,
        owner_id="A0", runtime_params=AttributeBonusParams("attack", 100))
    install(ctx, s, rt)
    assert s.attribute_system.get_attack(ctx, ctx.units["A0"]) == 315
    ctx.units["A0"].attack = 500
    assert s.attribute_system.get_attack(ctx, ctx.units["A0"]) == 615


def test_commander_branch_shared_activation_and_selection():
    ctx, s, rt = scene(commander_branch=True)
    inherent = ctx.skill_runtimes.get("A0", SkillSlot.INHERENT)
    before = s.skill_resolver.resolve(ctx, inherent)
    assert len(before.effects) == 2 and {e.target_id for e in before.effects} == {"B0"}
    deputy = ctx.skill_runtimes.get("A1", SkillSlot.INHERENT)
    assert len(s.skill_resolver.resolve(ctx, deputy).effects) == 1
    install(ctx, s, rt)
    assert len(s.skill_resolver.resolve(ctx, inherent).effects) == 1
    assert len(s.skill_resolver.resolve(ctx, deputy).effects) == 2
    deputy.definition = replace(deputy.definition, activation_rate=0)
    assert not s.skill_resolver.resolve(ctx, deputy).effects


def test_opening_passive_states_switch_effectiveness_without_reapplying():
    ctx, s, rt = scene()
    for i in range(3):
        for state_id in (f"ordinary_{i}", f"commander_{i}"):
            ctx.states.register_definition(StateDefinition(state_id, state_id))
        inherent = ctx.skill_runtimes.get(f"A{i}", SkillSlot.INHERENT)
        inherent.definition = SkillDefinition(f"passive_{i}", "passive", 1,
            SkillTargetMode.SELF, (ApplyStateSkillEffectSpec(f"ordinary_{i}"),),
            skill_type=SkillType.PASSIVE,
            commander_effect_specs=(ApplyStateSkillEffectSpec(f"commander_{i}"),))
    from sgs_v2.battle_core import process_pre_battle_passive_skills
    process_pre_battle_passive_skills(ctx, s)
    states = [ctx.states.find(owner_id=f"A{i}", state_id=f"commander_{i}")[0] for i in range(3)]
    assert [s.state_effectiveness_policy.evaluate_state(ctx, state).effective for state in states] == [True,False,False]
    generations = [state.current_generation_id for state in states]
    install(ctx, s, rt)
    assert [s.state_effectiveness_policy.evaluate_state(ctx, state).effective for state in states] == [False,True,True]
    assert [ctx.states.get(state.instance_id).current_generation_id for state in states] == generations
    assert all(s.state_effectiveness_policy.evaluate_state(ctx, ctx.states.find(state_id=f"ordinary_{i}")[0]).effective for i in range(3))


@pytest.mark.parametrize("issue", ["faction", "intelligence", "dead", "position", "definition"])
def test_invalid_input_has_no_effect_or_rng(issue):
    ctx, s, rt = scene()
    if issue == "faction": ctx.units["A2"].faction = None
    if issue == "intelligence": ctx.units["A0"].intelligence = None
    if issue == "dead": ctx.units["A2"].troops = 0
    if issue == "position": ctx.units["A2"].lineup_position = LineupPosition.DEPUTY_1
    if issue == "definition": rt.definition = replace(rt.definition, activation_rate=.5)
    rng = ctx.random._rng.getstate()
    with pytest.raises(ValueError): install(ctx, s, rt)
    assert not ctx.states.find() and not ctx.metadata.get("_stage14_installed_formation_keys")
    assert ctx.random._rng.getstate() == rng


def test_wrong_factions_disabled_scheduler_duplicate_and_cleanup():
    ctx, s, rt = scene()
    ctx.units["A2"].faction = "魏"
    install(ctx, s, rt)
    assert not ctx.states.find()
    ctx, s, rt = scene()
    rt.enabled = False
    run_pre_battle_preparation_phases(ctx, s)
    assert not ctx.states.find()
    ctx, s, rt = scene()
    run_pre_battle_preparation_phases(ctx, s)
    assert len(ctx.states.find()) == 10
    assert admit_and_install_formation_skill(ctx, s, rt).status is FormationAdmissionStatus.REJECTED_ALREADY_INSTALLED
    ctx.units[rt.owner_id].troops = 0
    s.defeat_cleanup_port.commit_defeat(ctx, rt.owner_id)
    assert not ctx.states.find()
    assert s.commander_effect_policy.enabled(ctx, "A0")
    assert not s.commander_effect_policy.enabled(ctx, "A2")


def test_role_state_removal_and_battle_isolation():
    ctx, s, rt = scene()
    install(ctx, s, rt)
    state = ctx.states.find(owner_id="A2", state_id=COMMANDER_EFFECT_ROLE_STATE_ID)[0]
    s.effect_executor.execute(ctx, RemoveStateEffect(state.instance_id))
    assert not s.commander_effect_policy.enabled(ctx, "A2")
    other, _, _ = scene()
    assert not s.commander_effect_policy.enabled(other, "A1")


def test_engine_and_invalid_level():
    ctx, s, rt = scene()
    ctx.current_phase = "NOT_STARTED"
    BattleEngine(context=ctx, systems=s).run()
    assert ctx.metadata["qian_long_snapshots"][(rt.owner_id, rt.skill_slot)]["eligible"]
    for level in (True, 0, 11, 1.5):
        with pytest.raises(ValueError): create_qian_long_zhen_definition(level)
