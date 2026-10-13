import pytest

from sgs_v2.battle_core import (
    BattleContext, BattleSystems, BattlePhase, BattleEngine, EventBus,
    DamageRequest, DamageSourceType, DamageType, LineupPosition, RandomSystem,
    SkillSlot, TroopType, UnitRuntime, FormationAdmissionStatus,
    admit_and_install_formation_skill, run_pre_battle_preparation_phases,
)
from sgs_v2.battle_core.ji_xing_zhen import (
    SKILL, calculate_reduction_rate, create_ji_xing_zhen_runtime,
)
from sgs_v2.battle_core.formation_admission import FORMATION_SKILL_REGISTRY
from sgs_v2.battle_core.outgoing_damage_reduction import OutgoingDamageReductionParams
from sgs_v2.battle_core.state_modifiers import (
    ATTRIBUTE_BONUS_STATE_ID, AttributeBonusParams, register_modifier_state_definitions,
)


def scene(seed=7):
    units = [UnitRuntime(
        unit_id=f"{team}{i}", name=f"{team}{i}", team_id=team,
        max_troops=5000, troops=5000, attack=250, defense=175,
        intelligence=210, speed=100, troop_type=TroopType.CAVALRY,
        lineup_position=pos,
    ) for team in ("A", "B") for i, pos in enumerate(LineupPosition)]
    ctx = BattleContext(battle_id="ji_xing", units={u.unit_id: u for u in units},
                        random=RandomSystem(seed), event_bus=EventBus())
    ctx.current_phase = BattlePhase.PRE_BATTLE.value
    systems = BattleSystems()
    register_modifier_state_definitions(ctx.states)
    runtime = create_ji_xing_zhen_runtime("A1")
    ctx.skill_runtimes.register(runtime)
    return ctx, systems, runtime


def install(ctx, systems, rt):
    assert admit_and_install_formation_skill(ctx, systems, rt).status is FormationAdmissionStatus.SUCCESS
    return ctx.metadata["ji_xing_snapshots"][(rt.owner_id, rt.skill_slot)]


def contributions(ctx, systems, source, target, dtype):
    request = DamageRequest(source, target, dtype, DamageSourceType.SKILL)
    return systems.damage_rule_provider.collect(ctx, request).modifier_contributions


@pytest.mark.parametrize("strength,expected", [(0, .29333333333333333), (100, .40), (250, .56), (400, .72)])
def test_formula_percentage_points(strength, expected):
    assert calculate_reduction_rate(strength) == pytest.approx(expected)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1000, 1000, True])
def test_formula_rejects_invalid_or_unsupported_extremes(value):
    with pytest.raises((ValueError, TypeError)):
        calculate_reduction_rate(value)


def test_registry():
    config = FORMATION_SKILL_REGISTRY["20178"]
    assert config.definition_factory() == SKILL
    assert SKILL.name == "箕形阵"
    assert SKILL.skill_type.value == "FORMATION"


@pytest.mark.parametrize("dtype,key", [(DamageType.WEAPON, "weapon_deputy_id"),
                                      (DamageType.STRATEGY, "strategy_deputy_id")])
def test_real_damage_pipeline_and_identity(dtype, key):
    ctx, systems, rt = scene()
    snap = install(ctx, systems, rt)
    assert snap["weapon_deputy_id"] != snap["strategy_deputy_id"]
    assert {snap["weapon_deputy_id"], snap["strategy_deputy_id"]} == {"A1", "A2"}
    request = DamageRequest("B0", snap[key], dtype, DamageSourceType.SKILL)
    result = systems.damage_system.calculate(ctx, request)
    modifier = result.pipeline_trace.modifier_result
    assert modifier.output_damage == pytest.approx(modifier.input_damage * .44 * .80)
    assert len(modifier.applied_modifiers) == 2
    for item in modifier.applied_modifiers:
        assert item.contribution.source.source_skill_id == "20178"
        assert item.contribution.source.applied_by_unit_id == "A1"
    assert len(contributions(ctx, systems, "B1", snap[key], dtype)) == 1
    assert len(contributions(ctx, systems, "B0", "A0", dtype)) == 1
    other = snap["strategy_deputy_id" if dtype is DamageType.WEAPON else "weapon_deputy_id"]
    assert len(contributions(ctx, systems, "B1", other, dtype)) == 0


def test_snapshot_reads_effective_provider_strength_then_retains_it():
    ctx, systems, rt = scene()
    systems.state_lifecycle_system.apply(ctx, state_id=ATTRIBUTE_BONUS_STATE_ID,
        owner_id="A1", runtime_params=AttributeBonusParams("attack", 150))
    snap = install(ctx, systems, rt)
    assert snap["strength"] == 400
    assert snap["reduction_rate"] == pytest.approx(.72)
    ctx.units["A1"].attack = 100
    assert contributions(ctx, systems, "B0", "A0", DamageType.WEAPON)[0].operand == pytest.approx(.28)


def test_expiry_and_duplicate_installation():
    ctx, systems, rt = scene()
    install(ctx, systems, rt)
    assert admit_and_install_formation_skill(ctx, systems, rt).status is FormationAdmissionStatus.REJECTED_ALREADY_INSTALLED
    for round_no in (1, 2, 3):
        ctx.current_round = round_no
        assert contributions(ctx, systems, "B0", "A0", DamageType.WEAPON)
    ctx.current_round = 4
    ctx.current_phase = BattlePhase.ROUND_START.value
    systems.state_lifecycle_system.expire_at(ctx, round_no=4, phase=BattlePhase.ROUND_START.value)
    assert not contributions(ctx, systems, "B0", "A0", DamageType.WEAPON)
    assert not [s for s in ctx.states.find() if s.source_skill_id == "20178"]


def test_provider_defeat_clears_both_sides():
    ctx, systems, rt = scene()
    install(ctx, systems, rt)
    ctx.units["A1"].troops = 0
    systems.defeat_cleanup_port.commit_defeat(ctx, "A1")
    assert not [s for s in ctx.states.find() if s.source_skill_id == "20178"]
    assert not contributions(ctx, systems, "B0", "A2", DamageType.WEAPON)


def test_seeded_assignment_and_prebattle_scheduler():
    snapshots = []
    for _ in range(2):
        ctx, systems, rt = scene()
        run_pre_battle_preparation_phases(ctx, systems)
        snapshots.append(ctx.metadata["ji_xing_snapshots"][(rt.owner_id, rt.skill_slot)])
    assert snapshots[0] == snapshots[1]
    selected = set()
    for seed in range(20):
        ctx, systems, rt = scene(seed)
        selected.add(install(ctx, systems, rt)["weapon_deputy_id"])
    assert selected == {"A1", "A2"}


def test_incomplete_lineup_fails_before_rng_or_effects():
    ctx, systems, rt = scene()
    ctx.units["A2"].troops = 0
    rng_state = ctx.random._rng.getstate()
    with pytest.raises(ValueError, match="two living"):
        install(ctx, systems, rt)
    assert ctx.random._rng.getstate() == rng_state
    assert not [s for s in ctx.states.find() if s.source_skill_id == "20178"]


def test_engine_installs_formation():
    ctx, systems, rt = scene()
    ctx.current_phase = "NOT_STARTED"
    BattleEngine(context=ctx, systems=systems).run()
    assert (rt.owner_id, rt.skill_slot) in ctx.metadata["ji_xing_snapshots"]


@pytest.mark.parametrize("rate", [-.01, 1.01, float("nan"), True])
def test_reusable_outgoing_params_validation(rate):
    with pytest.raises((ValueError, TypeError)):
        OutgoingDamageReductionParams(rate)
