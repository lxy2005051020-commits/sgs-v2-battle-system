"""Stage14 F1 Feng Shi Zhen: real 20066 Gameplay, no synthetic formulas."""
from __future__ import annotations

import pytest

from sgs_v2.battle_core import (
    BattleContext,
    BattlePhase,
    BattleSystems,
    DamageRequest,
    DamageSourceType,
    DamageType,
    EventBus,
    LineupPosition,
    RandomSystem,
    SkillRuntime,
    SkillSlot,
    TroopType,
    UnitRuntime,
    FormationAdmissionStatus,
    admit_and_install_formation_skill,
    run_pre_battle_preparation_phases,
)
from sgs_v2.battle_core.damage_modifier_system import DamageModifierSystem
from sgs_v2.battle_core.damage_modifiers import (
    DamageModifierContribution,
    DamageModifierKind,
    DamageModifierOperation,
    DamageModifierPhase,
)
from sgs_v2.battle_core.damage_rule_models import RuleContributionSource
from sgs_v2.battle_core.damage_rule_provider import DamageRuleCollection
from sgs_v2.battle_core.feng_shi_zhen import (
    FENG_SHI_ZHEN_SKILL_ID,
    FENG_SHI_ZHEN_MODIFIER_STATE_ID,
    FENG_SHI_ZHEN_APPLICABLE_TROOPS,
    FengShiZhenModifierParams,
    create_feng_shi_zhen_definition,
)
from sgs_v2.battle_core.formation_admission import (
    FORMATION_SKILL_REGISTRY,
    FormationAdmissionRejectedError,
)


def _unit(
    name: str, team: str, pos: LineupPosition,
    troop: TroopType = TroopType.CAVALRY,
    speed: float = 100.0,
) -> UnitRuntime:
    return UnitRuntime(
        unit_id=name, name=name, team_id=team,
        max_troops=3000, troops=3000,
        attack=230.0, defense=175.0, speed=speed,
        intelligence=210.0, troop_type=troop, lineup_position=pos,
    )


def _scene(
    *,
    team_troop: TroopType = TroopType.CAVALRY,
    both: bool = False,
    size: int = 3,
    provider_position: LineupPosition = LineupPosition.DEPUTY_1,
):
    positions = (LineupPosition.COMMANDER, LineupPosition.DEPUTY_1, LineupPosition.DEPUTY_2)
    a_units = [
        _unit(f"a{i}", "A", pos, team_troop, speed=110.0 + (3-i))
        for i, pos in enumerate(positions[:size])
    ]
    b_units = [
        _unit(f"b{i}", "B", pos, TroopType.SHIELD, speed=110.0)
        for i, pos in enumerate(positions[:3 if both else 1])
    ]
    ctx = BattleContext(
        battle_id="f1_feng_shi", units={u.unit_id: u for u in (*a_units, *b_units)},
        random=RandomSystem(1427), event_bus=EventBus(),
    )
    ctx.metadata["attacker_team_id"] = "B"  # attacker need not be 'my'/A
    systems = BattleSystems()
    a_provider = next(u for u in a_units if u.lineup_position is provider_position)
    a_runtime = SkillRuntime(
        create_feng_shi_zhen_definition(), a_provider.unit_id, SkillSlot.LEARNED_1
    )
    ctx.skill_runtimes.register(a_runtime)
    b_runtime = None
    if both:
        b_runtime = SkillRuntime(
            create_feng_shi_zhen_definition(), b_units[2].unit_id, SkillSlot.LEARNED_2
        )
        ctx.skill_runtimes.register(b_runtime)
    ctx.current_phase = BattlePhase.PRE_BATTLE.value
    return ctx, systems, a_runtime, b_runtime


def _install(ctx, systems, runtime):
    result = admit_and_install_formation_skill(ctx, systems, runtime)
    assert result.status is FormationAdmissionStatus.SUCCESS
    return result


def _state(ctx, unit_id):
    matches = ctx.states.find(owner_id=unit_id, state_id=FENG_SHI_ZHEN_MODIFIER_STATE_ID)
    assert len(matches) == 1
    return matches[0]


def _rules(ctx, systems, src, target, d_type=DamageType.WEAPON, source_type=DamageSourceType.SKILL):
    request = DamageRequest(src, target, d_type, source_type)
    return request, systems.damage_rule_provider.collect(ctx, request)


def _damage(ctx, systems, src, target, *, dtype=DamageType.WEAPON, stype=DamageSourceType.SKILL):
    req, rules = _rules(ctx, systems, src, target, dtype, stype)
    return DamageModifierSystem().resolve_phases(
        ctx, req, rules, 1000.0,
        phases=frozenset((DamageModifierPhase.OUTGOING, DamageModifierPhase.INCOMING)),
    ).output_damage


def test_feng_shi_zhen_id_and_canonical_registry():
    definition = create_feng_shi_zhen_definition()
    assert definition.skill_id == "20066"
    assert definition.name == "锋矢阵"
    assert definition.skill_type.value == "FORMATION"
    config = FORMATION_SKILL_REGISTRY[FENG_SHI_ZHEN_SKILL_ID]
    assert config.definition_factory() == definition
    assert set(config.applicable_troops) == {
        TroopType.CAVALRY, TroopType.SHIELD, TroopType.SPEAR,
    }
    assert config.installer is not None
    assert FENG_SHI_ZHEN_APPLICABLE_TROOPS == config.applicable_troops


@pytest.mark.parametrize("troop", (TroopType.CAVALRY, TroopType.SHIELD, TroopType.SPEAR))
def test_feng_shi_zhen_three_legal_base_troops(troop):
    ctx, systems, runtime, _ = _scene(team_troop=troop)
    _install(ctx, systems, runtime)
    assert len(ctx.states.find(state_id=FENG_SHI_ZHEN_MODIFIER_STATE_ID)) == 3


@pytest.mark.parametrize("troop", (TroopType.BOW, TroopType.SIEGE))
def test_feng_shi_zhen_forbidden_troop_is_atomic(troop):
    ctx, systems, runtime, _ = _scene(team_troop=troop)
    rng = ctx.random.getstate() if hasattr(ctx.random, "getstate") else None
    result = admit_and_install_formation_skill(ctx, systems, runtime)
    assert result.status is FormationAdmissionStatus.REJECTED_INVALID_TROOP
    assert ctx.states.find() == []
    assert "_stage14_installed_formation_keys" not in ctx.metadata
    if rng is not None:
        assert ctx.random.getstate() == rng
    with pytest.raises(FormationAdmissionRejectedError):
        run_pre_battle_preparation_phases(ctx, systems)
    assert ctx.states.find() == []


@pytest.mark.parametrize("provider_position", (
    LineupPosition.COMMANDER, LineupPosition.DEPUTY_1, LineupPosition.DEPUTY_2,
))
def test_feng_shi_zhen_role_scaling_independent_of_carrier(provider_position):
    ctx, systems, runtime, _ = _scene(provider_position=provider_position)
    _install(ctx, systems, runtime)
    for name, outgoing, incoming in (
        ("a0", 0.30, 0.20), ("a1", -0.15, -0.25), ("a2", -0.15, -0.25),
    ):
        state = _state(ctx, name)
        assert isinstance(state.runtime_params, FengShiZhenModifierParams)
        assert state.runtime_params.outgoing_rate == pytest.approx(outgoing)
        assert state.runtime_params.incoming_rate == pytest.approx(incoming)
        assert state.source_id == runtime.owner_id
        assert state.source_skill_id == "20066"
        assert state.source_skill_slot is SkillSlot.LEARNED_1
    assert len(ctx.states.find(state_id=FENG_SHI_ZHEN_MODIFIER_STATE_ID)) == 3


@pytest.mark.parametrize("dtype", (DamageType.WEAPON, DamageType.STRATEGY))
@pytest.mark.parametrize("source_type", (DamageSourceType.NORMAL_ATTACK, DamageSourceType.SKILL))
def test_feng_shi_zhen_actual_four_quadrant_damage(dtype, source_type):
    ctx, systems, runtime, _ = _scene()
    _install(ctx, systems, runtime)
    assert _damage(ctx, systems, "a0", "b0", dtype=dtype, stype=source_type) == pytest.approx(1300.0)
    assert _damage(ctx, systems, "b0", "a0", dtype=dtype, stype=source_type) == pytest.approx(1200.0)
    assert _damage(ctx, systems, "a1", "b0", dtype=dtype, stype=source_type) == pytest.approx(850.0)
    assert _damage(ctx, systems, "b0", "a1", dtype=dtype, stype=source_type) == pytest.approx(750.0)


def test_feng_shi_zhen_both_teams_incoming_and_outgoing_multiply_layers():
    ctx, systems, rt_a, rt_b = _scene(both=True)
    _install(ctx, systems, rt_a)
    _install(ctx, systems, rt_b)
    # A commander +30% OUT; B commander +20% IN: different multiplier layers.
    assert _damage(ctx, systems, "a0", "b0") == pytest.approx(1560.0)
    # B commander +30% OUT; A deputy -25% IN, not a same-pool sum.
    assert _damage(ctx, systems, "b0", "a1") == pytest.approx(975.0)
    assert len(ctx.states.find(state_id=FENG_SHI_ZHEN_MODIFIER_STATE_ID)) == 6


def test_feng_shi_zhen_same_outgoing_pool_addition_not_multiplication():
    ctx, systems, runtime, _ = _scene()
    _install(ctx, systems, runtime)
    req, rules = _rules(ctx, systems, "a0", "b0")
    unrelated = DamageModifierContribution(
        phase=DamageModifierPhase.OUTGOING,
        kind=DamageModifierKind.OUTGOING_REDUCTION,
        operation=DamageModifierOperation.MULTIPLY_FACTOR,
        operand=1.0 - 0.3344,
        source=RuleContributionSource("a0", "b0", "BAMEN", None, None, "synthetic_bamen"),
        order_key="synthetic_bamen",
    )
    merged = DamageRuleCollection(
        rules.prevention_contributions, rules.hit_contributions,
        rules.formula_policy_contributions,
        (*rules.modifier_contributions, unrelated),
    )
    result = DamageModifierSystem().resolve_phases(
        ctx, req, merged, 1000,
        phases=frozenset((DamageModifierPhase.OUTGOING,)),
    )
    # Full-level +30% -33.44% => -3.44% same pool, never 1.30*0.6656.
    assert result.output_damage == pytest.approx(965.6)


def test_feng_shi_zhen_provider_death_immediately_clears_foreign_targets():
    ctx, systems, runtime, _ = _scene()
    _install(ctx, systems, runtime)
    assert _damage(ctx, systems, "a0", "b0") == pytest.approx(1300.0)
    assert _damage(ctx, systems, "b0", "a2") == pytest.approx(750.0)
    # The provider is a deputy: all affected ally state nodes must clear.
    ctx.units[runtime.owner_id].troops = 0
    result = systems.defeat_cleanup_port.commit_defeat(ctx, runtime.owner_id)
    assert len(result.removed_states) == 3
    assert ctx.states.find(state_id=FENG_SHI_ZHEN_MODIFIER_STATE_ID) == []
    assert _damage(ctx, systems, "a0", "b0") == pytest.approx(1000.0)
    assert _damage(ctx, systems, "b0", "a2") == pytest.approx(1000.0)
    assert ctx.skill_runtimes.get(runtime.owner_id, runtime.skill_slot) is runtime
    assert systems.defeat_cleanup_port.commit_defeat(ctx, runtime.owner_id).removed_states == ()


def test_feng_shi_zhen_two_provider_death_isolation():
    ctx, systems, rt_a, rt_b = _scene(both=True)
    _install(ctx, systems, rt_a)
    _install(ctx, systems, rt_b)
    ctx.units[rt_a.owner_id].troops = 0
    systems.defeat_cleanup_port.commit_defeat(ctx, rt_a.owner_id)
    states = ctx.states.find(state_id=FENG_SHI_ZHEN_MODIFIER_STATE_ID)
    assert len(states) == 3
    assert all(x.source_id == rt_b.owner_id for x in states)
    assert _damage(ctx, systems, "b0", "a0") == pytest.approx(1300.0)


def test_feng_shi_zhen_duplicate_installer_does_not_double_count_or_rng():
    ctx, systems, runtime, _ = _scene()
    _install(ctx, systems, runtime)
    before = tuple(s.instance_id for s in ctx.states.find())
    assert admit_and_install_formation_skill(ctx, systems, runtime).status is FormationAdmissionStatus.REJECTED_ALREADY_INSTALLED
    assert tuple(s.instance_id for s in ctx.states.find()) == before
    assert _damage(ctx, systems, "a0", "b0") == pytest.approx(1300.0)


@pytest.mark.parametrize("size", (1, 2, 3))
def test_feng_shi_zhen_does_not_invent_missing_deputies(size):
    # For size=1 provider must be the commander; BattleContext remains legal.
    position = LineupPosition.COMMANDER if size == 1 else LineupPosition.DEPUTY_1
    ctx, systems, runtime, _ = _scene(size=size, provider_position=position)
    _install(ctx, systems, runtime)
    assert len(ctx.states.find(state_id=FENG_SHI_ZHEN_MODIFIER_STATE_ID)) == size


def test_feng_shi_zhen_prebattle_scheduler_real_integration():
    ctx, systems, runtime, _ = _scene()
    run_pre_battle_preparation_phases(ctx, systems)
    assert len(ctx.states.find(state_id=FENG_SHI_ZHEN_MODIFIER_STATE_ID)) == 3
    assert _damage(ctx, systems, "a0", "b0") == pytest.approx(1300.0)


@pytest.mark.parametrize("dtype", (DamageType.WEAPON, DamageType.STRATEGY))
def test_feng_shi_zhen_real_damage_system_pipeline(dtype):
    """Production DamageSystem must consume the formation adapter, not only a stand-alone pool."""
    ctx, systems, runtime, _ = _scene()
    _install(ctx, systems, runtime)
    req = DamageRequest("a0", "b0", dtype, DamageSourceType.NORMAL_ATTACK)
    result = systems.damage_system.calculate(ctx, req)
    assert not result.prevented
    assert result.final_damage > 0
    assert result.pipeline_trace is not None
    modifier = result.pipeline_trace.modifier_result
    assert modifier is not None
    feng_contributions = [
        x.contribution for x in modifier.applied_modifiers
        if x.contribution.source.source_skill_id == FENG_SHI_ZHEN_SKILL_ID
    ]
    assert len(feng_contributions) == 1
    assert feng_contributions[0].kind is DamageModifierKind.OUTGOING_INCREASE
    assert feng_contributions[0].operand == pytest.approx(1.30)
    assert modifier.output_damage == pytest.approx(modifier.input_damage * 1.30)


def test_feng_shi_zhen_real_damage_system_two_layers():
    ctx, systems, rt_a, rt_b = _scene(both=True)
    _install(ctx, systems, rt_a)
    _install(ctx, systems, rt_b)
    req = DamageRequest("a0", "b0", DamageType.WEAPON, DamageSourceType.SKILL)
    result = systems.damage_system.calculate(ctx, req)
    assert result.pipeline_trace is not None
    modifier = result.pipeline_trace.modifier_result
    assert modifier is not None
    contributions = [
        a.contribution for a in modifier.applied_modifiers
        if a.contribution.source.source_skill_id == FENG_SHI_ZHEN_SKILL_ID
    ]
    assert [c.phase for c in contributions] == [
        DamageModifierPhase.OUTGOING, DamageModifierPhase.INCOMING
    ]
    assert modifier.output_damage == pytest.approx(modifier.input_damage * 1.30 * 1.20)


def test_feng_shi_zhen_actual_damage_after_provider_defeat():
    ctx, systems, runtime, _ = _scene()
    _install(ctx, systems, runtime)
    req = DamageRequest("a0", "b0", DamageType.WEAPON, DamageSourceType.SKILL)
    before = systems.damage_system.calculate(ctx, req)
    assert before.pipeline_trace is not None
    assert before.pipeline_trace.modifier_result is not None
    assert any(
        x.contribution.source.source_skill_id == FENG_SHI_ZHEN_SKILL_ID
        for x in before.pipeline_trace.modifier_result.applied_modifiers
    )
    ctx.units[runtime.owner_id].troops = 0
    systems.defeat_cleanup_port.commit_defeat(ctx, runtime.owner_id)
    after = systems.damage_system.calculate(ctx, req)
    assert after.pipeline_trace is not None
    assert after.pipeline_trace.modifier_result is not None
    assert all(
        x.contribution.source.source_skill_id != FENG_SHI_ZHEN_SKILL_ID
        for x in after.pipeline_trace.modifier_result.applied_modifiers
    )


def test_feng_shi_zhen_real_battle_engine_prebattle_applies_once():
    """The production BattleEngine dispatch must install F1 through PRE_BATTLE."""
    from sgs_v2.battle_core import BattleEngine, EventType

    ctx, systems, runtime, _ = _scene()
    applied = []

    def on_applied(event):
        if event.payload.get("state_id") == FENG_SHI_ZHEN_MODIFIER_STATE_ID:
            applied.append((event.phase, event.actor_id, event.target_id))

    ctx.event_bus.subscribe(EventType.STATE_APPLIED, on_applied)
    # A new battle starts from the real engine's NOT_STARTED boundary.
    ctx.current_phase = "NOT_STARTED"
    result = BattleEngine(context=ctx, systems=systems).run()
    assert result is not None
    assert len(applied) == 3
    assert all(phase == BattlePhase.PRE_BATTLE.value for phase, _, _ in applied)
    assert {target for _, _, target in applied} == {"a0", "a1", "a2"}
    assert all(actor == runtime.owner_id for _, actor, _ in applied)
