"""User formula regressions and canonical 八门 effect/formation integration."""
import pytest
import csv
import re
from pathlib import Path

from sgs_v2.battle_core import (BattleContext, BattlePhase, BattleSystems,
    DamageRequest, DamageSourceType, DamageType, EventBus, LineupPosition,
    RandomSystem, SkillSlot, TroopType, UnitRuntime,
    FormationAdmissionStatus, admit_and_install_formation_skill,
    run_pre_battle_preparation_phases)
from sgs_v2.battle_core.ba_men_jin_suo_zhen import (
    BASE_REDUCTION_RATES, SKILL, calculate_reduction_rate,
    create_ba_men_jin_suo_zhen_definition, create_ba_men_jin_suo_zhen_runtime)
from sgs_v2.battle_core.damage_modifier_system import DamageModifierSystem
from sgs_v2.battle_core.damage_modifiers import DamageModifierPhase
from sgs_v2.battle_core.feng_shi_zhen import create_feng_shi_zhen_runtime
from sgs_v2.battle_core.formation_admission import (
    FORMATION_SKILL_REGISTRY, FormationAdmissionRejectedError)
from sgs_v2.battle_core.official_state_catalog import OfficialStateId, register_official_state_definitions
from sgs_v2.battle_core.outgoing_damage_reduction import (
    OUTGOING_DAMAGE_REDUCTION_STATE_ID as OD, OutgoingDamageReductionParams,
    register_outgoing_reduction_state)
from sgs_v2.battle_core.state_modifiers import (ATTRIBUTE_BONUS_STATE_ID, AttributeBonusParams,
    register_modifier_state_definitions)


def scene(*, level=10, intelligence=200, enemies=3, troop=TroopType.CAVALRY, seed=12):
    units = {}
    positions = tuple(LineupPosition)
    for team, count in (("A", 3), ("B", enemies)):
        for i in range(count):
            uid = f"{team}{i}"
            units[uid] = UnitRuntime(unit_id=uid, name=uid, team_id=team,
                max_troops=10000, troops=10000, attack=200, defense=200,
                intelligence=intelligence if uid == "A1" else 100,
                speed=10 if uid == "A0" else 100, troop_type=troop,
                lineup_position=positions[i])
    ctx = BattleContext(battle_id="ba_men", units=units,
                        random=RandomSystem(seed), event_bus=EventBus())
    systems = BattleSystems()
    register_official_state_definitions(ctx.states)
    register_modifier_state_definitions(ctx.states)
    ctx.metadata["attacker_team_id"] = "A"
    runtime = create_ba_men_jin_suo_zhen_runtime("A1", level=level)
    ctx.skill_runtimes.register(runtime)
    ctx.current_phase = BattlePhase.PRE_BATTLE.value
    return ctx, systems, runtime


def install(ctx, systems, runtime):
    assert admit_and_install_formation_skill(ctx, systems, runtime).status is FormationAdmissionStatus.SUCCESS


def damage(ctx, systems, source, target, dtype=DamageType.WEAPON,
           stype=DamageSourceType.SKILL):
    req = DamageRequest(source, target, dtype, stype)
    rules = systems.damage_rule_provider.collect(ctx, req)
    return DamageModifierSystem().resolve_phases(ctx, req, rules, 1000,
        phases=frozenset((DamageModifierPhase.OUTGOING, DamageModifierPhase.INCOMING))).output_damage


@pytest.mark.parametrize("intelligence,expected", [(0, .2184), (50, .2592),
    (100, .30), (200, .3816), (300, .4632), (400, .5448)])
def test_user_formula_above_and_below_balance_point(intelligence, expected):
    assert calculate_reduction_rate(.30, intelligence) == pytest.approx(expected)


@pytest.mark.parametrize("level,base", tuple(enumerate(BASE_REDUCTION_RATES, start=1)))
def test_all_levels_use_exact_static_base_rates(level, base):
    ctx, systems, runtime = scene(level=level, intelligence=100)
    install(ctx, systems, runtime)
    states = ctx.states.find(state_id=OD)
    assert len(states) == 2
    assert all(s.runtime_params.rate == base for s in states)
    assert ctx.metadata["ba_men_snapshots"][("A1", SkillSlot.LEARNED_1)]["level"] == level


@pytest.mark.parametrize("level", [0, 11, True, 1.5])
def test_invalid_level_fails_closed(level):
    with pytest.raises(ValueError):
        create_ba_men_jin_suo_zhen_definition(level)


@pytest.mark.parametrize("intelligence", [float("nan"), float("inf"), 10000])
def test_unrepresentable_formula_does_not_invent_cap(intelligence):
    ctx, systems, runtime = scene(intelligence=intelligence)
    before = ctx.random._rng.getstate()
    with pytest.raises(ValueError):
        install(ctx, systems, runtime)
    assert not ctx.states.find()
    assert before == ctx.random._rng.getstate()
    assert "_stage14_installed_formation_keys" not in ctx.metadata


def test_negative_extreme_formula_fails_without_clamping():
    with pytest.raises(ValueError):
        calculate_reduction_rate(.3, -1000)


def test_clean_registry_and_default_full_level():
    assert SKILL.skill_id == "20025"
    assert SKILL.name == "八门金锁阵"
    assert SKILL.skill_type.value == "FORMATION"
    config = FORMATION_SKILL_REGISTRY["20025"]
    assert config.definition_factory() == SKILL
    assert config.installer is not None
    assert set(config.applicable_troops) == set(TroopType)


def test_level_constants_match_preserved_static_export():
    source = Path(__file__).resolve().parents[1] / "stages/stage14/ba_men_evidence/static_levels.csv"
    with source.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 10
    for row in rows:
        assert row["base_id"] == "20025"
        assert row["name"] == "八门金锁阵"
        match = re.search(r"伤害降低([0-9.]+)%", row["description"])
        assert match is not None
        assert BASE_REDUCTION_RATES[int(row["level"]) - 1] == float(match.group(1)) / 100


@pytest.mark.parametrize("troop", tuple(TroopType))
def test_all_base_troops_auto_install(troop):
    ctx, systems, _ = scene(troop=troop)
    run_pre_battle_preparation_phases(ctx, systems)
    assert len(ctx.states.find(state_id=OD)) == 2
    assert len(ctx.states.find(state_id=OfficialStateId.FIRST_STRIKE.value)) == 1


@pytest.mark.parametrize("enemies", [1, 2, 3])
def test_unique_enemy_targets_and_actual_first_strike(enemies):
    ctx, systems, runtime = scene(enemies=enemies)
    install(ctx, systems, runtime)
    states = ctx.states.find(state_id=OD)
    targets = {s.owner_id for s in states}
    assert len(targets) == min(2, enemies)
    assert targets <= {uid for uid in ctx.units if uid.startswith("B")}
    for state in ctx.states.find():
        assert state.source_id == "A1"
        assert state.source_skill_id == "20025"
        assert state.source_skill_slot is SkillSlot.LEARNED_1
        assert state.expires_round == 4
        assert state.expires_phase == BattlePhase.ROUND_START.value
    first = ctx.states.find(state_id=OfficialStateId.FIRST_STRIKE.value)
    assert [s.owner_id for s in first] == ["A0"]
    assert systems.action_order_system.determine_order(ctx)[0].unit_id == "A0"


def test_seed_replay_and_no_reselection_across_rounds():
    targets = []
    for _ in range(2):
        ctx, systems, runtime = scene()
        install(ctx, systems, runtime)
        targets.append(tuple(s.owner_id for s in ctx.states.find(state_id=OD)))
        rng = ctx.random._rng.getstate()
        for round_no in (1, 2, 3):
            ctx.current_round = round_no
            for uid in targets[-1]:
                assert damage(ctx, systems, uid, "A2") == pytest.approx(618.4)
        assert rng == ctx.random._rng.getstate()
    assert targets[0] == targets[1]


@pytest.mark.parametrize("dtype", (DamageType.WEAPON, DamageType.STRATEGY))
@pytest.mark.parametrize("stype", (DamageSourceType.NORMAL_ATTACK, DamageSourceType.SKILL))
def test_outgoing_both_damage_types_not_incoming(dtype, stype):
    ctx, systems, runtime = scene()
    install(ctx, systems, runtime)
    selected = {s.owner_id for s in ctx.states.find(state_id=OD)}
    for uid in ("B0", "B1", "B2"):
        assert damage(ctx, systems, uid, "A2", dtype, stype) == pytest.approx(
            618.4 if uid in selected else 1000)
        assert damage(ctx, systems, "A2", uid, dtype, stype) == pytest.approx(1000)


def test_snapshot_reads_attribute_system_and_never_recomputes():
    ctx, systems, runtime = scene(intelligence=100)
    systems.state_lifecycle_system.apply(ctx, state_id=ATTRIBUTE_BONUS_STATE_ID,
        owner_id="A1", runtime_params=AttributeBonusParams("intelligence", 100))
    install(ctx, systems, runtime)
    target = ctx.states.find(state_id=OD)[0].owner_id
    assert damage(ctx, systems, target, "A2") == pytest.approx(618.4)
    ctx.units["A1"].intelligence = 400
    assert damage(ctx, systems, target, "A2") == pytest.approx(618.4)


def test_round_four_expiry_removes_reduction_and_first_strike():
    ctx, systems, runtime = scene()
    install(ctx, systems, runtime)
    selected = ctx.states.find(state_id=OD)[0].owner_id
    for r in (1, 2, 3):
        ctx.current_round = r
        systems.state_lifecycle_system.expire_at(ctx, round_no=r, phase=BattlePhase.ROUND_START.value)
        assert damage(ctx, systems, selected, "A0") == pytest.approx(618.4)
    ctx.current_round = 4
    systems.state_lifecycle_system.expire_at(ctx, round_no=4, phase=BattlePhase.ROUND_START.value)
    assert not ctx.states.find(state_id=OD)
    assert not ctx.states.find(state_id=OfficialStateId.FIRST_STRIKE.value)
    assert damage(ctx, systems, selected, "A0") == pytest.approx(1000)
    assert systems.action_order_system.determine_order(ctx)[0].unit_id != "A0"


def test_provider_death_cleans_enemy_and_commander_but_preserves_other_sources():
    ctx, systems, runtime = scene()
    install(ctx, systems, runtime)
    target = ctx.states.find(state_id=OD)[0].owner_id
    systems.state_lifecycle_system.apply(ctx, state_id=OD, owner_id=target,
        source_id="A2", source_skill_id="other", runtime_params=OutgoingDamageReductionParams(.1))
    ctx.units["A1"].troops = 0
    systems.defeat_cleanup_port.commit_defeat(ctx, "A1")
    assert not [s for s in ctx.states.find() if s.source_skill_id == "20025"]
    assert damage(ctx, systems, target, "A0") == pytest.approx(900)


def test_foreign_feng_shi_outgoing_adds_and_incoming_multiplies():
    ctx, systems, runtime = scene(enemies=2)
    ctx.skill_runtimes.register(create_feng_shi_zhen_runtime("B1", slot=SkillSlot.LEARNED_2))
    run_pre_battle_preparation_phases(ctx, systems)
    # B commander OI +30% and 八门 OD -38.16% are a same-side additive pool.
    assert damage(ctx, systems, "B0", "A2") == pytest.approx(918.4)
    # B deputy OD -15% and 八门 OD -38.16% also add.
    assert damage(ctx, systems, "B1", "A2") == pytest.approx(468.4)
    # A unchanged outgoing, B deputy incoming -25% is the other layer.
    assert damage(ctx, systems, "A2", "B1") == pytest.approx(750)


def test_exclusivity_and_disabled_runtime_are_rng_free():
    ctx, systems, runtime = scene()
    ctx.skill_runtimes.register(create_feng_shi_zhen_runtime("A2", slot=SkillSlot.LEARNED_2))
    rng = ctx.random._rng.getstate()
    with pytest.raises(FormationAdmissionRejectedError):
        run_pre_battle_preparation_phases(ctx, systems)
    assert not ctx.states.find()
    assert ctx.random._rng.getstate() == rng
    ctx, systems, runtime = scene()
    runtime.enabled = False
    run_pre_battle_preparation_phases(ctx, systems)
    assert not ctx.states.find()


def test_repeat_install_is_rejected_without_rng_or_mutation():
    ctx, systems, runtime = scene()
    install(ctx, systems, runtime)
    before = ctx.random._rng.getstate()
    states = ctx.states.find()
    result = admit_and_install_formation_skill(ctx, systems, runtime)
    assert result.status is FormationAdmissionStatus.REJECTED_ALREADY_INSTALLED
    assert ctx.random._rng.getstate() == before
    assert ctx.states.find() == states


def test_generic_reduction_pool_and_floor():
    ctx, systems, _ = scene()
    register_outgoing_reduction_state(ctx.states)
    for skill, rate in (("generic1", .6), ("generic2", .5)):
        systems.state_lifecycle_system.apply(ctx, state_id=OD, owner_id="B0",
            source_id="A0", source_skill_id=skill, runtime_params=OutgoingDamageReductionParams(rate))
    # Shared damage owner enforces the already-frozen 10% outgoing floor.
    assert damage(ctx, systems, "B0", "A2") == pytest.approx(100)


@pytest.mark.parametrize("dtype", (DamageType.WEAPON, DamageType.STRATEGY))
def test_production_damage_trace_contains_ba_men_and_clears_on_death(dtype):
    ctx, systems, runtime = scene(enemies=2)
    install(ctx, systems, runtime)
    req = DamageRequest("B0", "A2", dtype, DamageSourceType.SKILL)
    before = systems.damage_system.calculate(ctx, req)
    applied = before.pipeline_trace.modifier_result.applied_modifiers
    reduction = [x.contribution for x in applied if x.contribution.source.source_skill_id == "20025"]
    assert len(reduction) == 1
    assert reduction[0].operand == pytest.approx(.6184)
    assert reduction[0].phase is DamageModifierPhase.OUTGOING
    ctx.units["A1"].troops = 0
    systems.defeat_cleanup_port.commit_defeat(ctx, "A1")
    after = systems.damage_system.calculate(ctx, req)
    assert all(x.contribution.source.source_skill_id != "20025"
        for x in after.pipeline_trace.modifier_result.applied_modifiers)


def test_production_battle_engine_installs_once_and_expires_before_round_four():
    from sgs_v2.battle_core import BattleEngine, EventType
    ctx, systems, _ = scene()
    ctx.max_rounds = 4
    applied, expired, orders = [], [], []
    ctx.event_bus.subscribe(EventType.STATE_APPLIED,
        lambda e: applied.append(e) if e.payload.get("source_skill_id") == "20025" else None)
    ctx.event_bus.subscribe(EventType.STATE_EXPIRED,
        lambda e: expired.append(e) if e.payload.get("source_skill_id") == "20025" else None)
    ctx.event_bus.subscribe(EventType.ACTION_ORDER_DECIDED, orders.append)
    ctx.current_phase = "NOT_STARTED"
    assert BattleEngine(context=ctx, systems=systems).run() is not None
    assert len(applied) == 3
    assert all(e.phase == BattlePhase.PRE_BATTLE.value for e in applied)
    assert len(expired) == 3
    assert all(e.round_no == 4 and e.phase == BattlePhase.ROUND_START.value for e in expired)
    assert len(orders) == 4
    assert all(e.payload["order"][0] == "A0" for e in orders[:3])
    assert orders[3].payload["order"][0] != "A0"


def test_public_loader_round_trip():
    from sgs_v2.battle_core import (BA_MEN_JIN_SUO_ZHEN_SKILL_ID,
        create_ba_men_jin_suo_zhen_runtime as loader)
    rt = loader("A0", slot=SkillSlot.LEARNED_2, level=1)
    assert rt.definition.skill_id == BA_MEN_JIN_SUO_ZHEN_SKILL_ID == "20025"
    assert rt.definition.effect_specs[0].runtime_params.rate == .15
    assert rt.skill_slot is SkillSlot.LEARNED_2
