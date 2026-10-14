import csv
from pathlib import Path
import pytest
from sgs_v2.battle_core import (BattleContext, BattleSystems, BattlePhase, BattleEngine,
    UnitRuntime, TroopType, LineupPosition, RandomSystem, EventBus, SkillSlot,
    create_yan_xing_zhen_runtime, create_yan_xing_zhen_definition, admit_and_install_formation_skill)
from sgs_v2.battle_core.formation_admission import FORMATION_SKILL_REGISTRY
from sgs_v2.battle_core.yan_xing_zhen import LEVEL_RATES, SKILL
from sgs_v2.battle_core.effects import ApplyStateEffect, RemoveStateEffect
from sgs_v2.battle_core.state_modifiers import (ATTRIBUTE_BONUS_STATE_ID, AttributeBonusParams,
    INCOMING_DAMAGE_REDUCTION_STATE_ID, IncomingDamageReductionParams)
from sgs_v2.battle_core.damage_rate_modifier import DAMAGE_RATE_STATE_ID, DamageRateParams
from sgs_v2.battle_core.round_team_transfer import ROUND_TEAM_TRANSFER_STATE_ID
from sgs_v2.battle_core.rule_hooks import RoundStartHook, UnitActionStartHook
from sgs_v2.battle_core.state_transfer_support import StateTransferSupport
from sgs_v2.battle_core.official_state_catalog import register_official_state_definitions
from sgs_v2.battle_core.provider_identity import SkillProviderRef
from sgs_v2.battle_core.enums import DamageType


def scene(provider=0, level=10, slot=SkillSlot.LEARNED_1, troop=TroopType.CAVALRY):
    units = [UnitRuntime(f"{team}{i}", f"{team}{i}", team, 10000, 10000,
        180, 180, 100-i, intelligence=180, troop_type=troop,
        lineup_position=pos) for team in ("A", "B") for i, pos in enumerate(LineupPosition)]
    ctx = BattleContext(battle_id="yan_xing", units={u.unit_id: u for u in units},
        random=RandomSystem(127), event_bus=EventBus())
    s = BattleSystems()
    rt = create_yan_xing_zhen_runtime(f"A{provider}", level=level, slot=slot)
    ctx.skill_runtimes.register(rt)
    ctx.current_phase = BattlePhase.PRE_BATTLE.value
    return ctx, s, rt


def install(ctx, s, rt):
    assert admit_and_install_formation_skill(ctx, s, rt).status.value == "SUCCESS"


def tick(ctx, s, round=1, decisions=(False, False, True)):
    ctx.current_round = round
    ctx.current_phase = BattlePhase.ROUND_START.value
    if decisions is not None:
        book = iter(decisions)
        ctx.random.chance = lambda probability: next(book)
    return s.rule_hook_system.process(ctx, RoundStartHook(round))


def attr(ctx, s, name):
    return s.attribute_system.get_defense(ctx, ctx.units[name])


def apply(ctx, s, sid, owner, params):
    return s.effect_executor.execute(ctx, ApplyStateEffect(sid, owner, "B0", "fixture", runtime_params=params)).state_instance


@pytest.mark.parametrize("level", range(1, 11))
def test_level_theft_conservation_and_expiry(level):
    ctx, s, rt = scene(level=level)
    install(ctx, s, rt)
    tick(ctx, s)
    amount = LEVEL_RATES[level-1][1]
    assert attr(ctx, s, "A0") == pytest.approx(180 + 3*amount)
    assert all(attr(ctx, s, f"B{i}") == pytest.approx(180-amount) for i in range(3))
    assert sum(attr(ctx, s, u) for u in ctx.units) == pytest.approx(1080)
    assert all(st.source_skill_slot == rt.skill_slot for st in ctx.states.find(state_id=ATTRIBUTE_BONUS_STATE_ID))
    s.state_lifecycle_system.expire_at(ctx, round_no=1, phase=BattlePhase.ROUND_END.value)
    assert all(attr(ctx, s, u) == 180 for u in ctx.units)


@pytest.mark.parametrize("provider", range(3))
@pytest.mark.parametrize("slot", list(SkillSlot))
def test_holder_is_not_forced_recipient_and_live_command(provider, slot):
    ctx, s, rt = scene(provider=provider, slot=slot)
    install(ctx, s, rt)
    apply(ctx, s, ATTRIBUTE_BONUS_STATE_ID, "A2", AttributeBonusParams("defense", -70))
    tick(ctx, s)
    assert ctx.metadata["round_team_transfer_history"][-1]["theft"]["target_id"] == "A2"
    assert attr(ctx, s, "A2") == 140


@pytest.mark.parametrize("troop", list(TroopType))
def test_all_troops_no_install_rng_and_idempotence(troop):
    ctx, s, rt = scene(troop=troop)
    before = ctx.random._rng.getstate()
    install(ctx, s, rt)
    assert ctx.random._rng.getstate() == before
    assert admit_and_install_formation_skill(ctx, s, rt).status.value == "REJECTED_ALREADY_INSTALLED"
    assert len(ctx.states.find(state_id=ROUND_TEAM_TRANSFER_STATE_ID)) == 1


def test_independent_probability_and_once_per_round():
    ctx, s, rt = scene()
    install(ctx, s, rt)
    calls = []
    outcomes = iter((False, True, False))
    ctx.random.chance = lambda p: (calls.append(p), next(outcomes))[1]
    tick(ctx, s, decisions=None)
    tick(ctx, s, decisions=None)
    assert calls == [.35, .35, .35]
    assert ctx.metadata["round_team_transfer_history"][0]["decisions"] == (False, True, False)
    assert not ctx.states.find(state_id=ATTRIBUTE_BONUS_STATE_ID)
    assert len(ctx.metadata["round_team_transfer_history"]) == 1


def test_defeated_and_disabled_provider_driver_removal_and_wrong_hook():
    for mode in ("dead", "disabled", "removed"):
        ctx, s, rt = scene()
        install(ctx, s, rt)
        ctx.current_round = 1
        ctx.current_phase = BattlePhase.UNIT_ACTION_START.value
        s.rule_hook_system.process(ctx, UnitActionStartHook(1, rt.owner_id))
        assert "round_team_transfer_history" not in ctx.metadata
        if mode == "dead":
            ctx.units[rt.owner_id].troops = 0
            s.defeat_cleanup_port.commit_defeat(ctx, rt.owner_id)
        elif mode == "disabled":
            rt.enabled = False
        else:
            s.effect_executor.execute(ctx, RemoveStateEffect(ctx.states.find(state_id=ROUND_TEAM_TRANSFER_STATE_ID)[0].instance_id))
        ctx.random.chance = lambda p: pytest.fail("inactive driver consumed RNG")
        tick(ctx, s, decisions=None)
        assert "round_team_transfer_history" not in ctx.metadata


def test_living_enemy_count_and_lowest_tie_order():
    ctx, s, rt = scene(provider=2)
    install(ctx, s, rt)
    ctx.units["B2"].troops = 0
    tick(ctx, s)
    row = ctx.metadata["round_team_transfer_history"][0]["theft"]
    assert row["target_id"] == "A0" and row["total"] == 20
    assert row["enemy_ids"] == ["B0", "B1"]


def test_reduction_transfer_and_unrelated_dimension_preserved():
    ctx, s, rt = scene()
    install(ctx, s, rt)
    original = apply(ctx, s, DAMAGE_RATE_STATE_ID, "B1", DamageRateParams(.2, -.3))
    ctx.current_round = 1
    ctx.current_phase = BattlePhase.ROUND_START.value
    ref = SkillProviderRef(rt.owner_id, rt.skill_slot, "20862")
    row = StateTransferSupport(s).transfer(ctx, original, "A2", ref, reduction=True)
    assert row["status"] == "TRANSFERRED"
    assert ctx.states.find(owner_id="B1", state_id=DAMAGE_RATE_STATE_ID)[0].runtime_params == DamageRateParams(.2, 0)
    new = ctx.states.find(owner_id="A2", state_id=DAMAGE_RATE_STATE_ID)[0]
    assert new.runtime_params == DamageRateParams(0, -.3)
    assert new.source_skill_id == "20862" and new.lifetime_spec.expires_round == 1
    assert not ctx.states.has_instance(original.instance_id)


def test_reduction_lane_random_target_once_and_multiple_damage_types():
    ctx, s, rt = scene()
    install(ctx, s, rt)
    for dtype in DamageType:
        apply(ctx, s, INCOMING_DAMAGE_REDUCTION_STATE_ID, "B1", IncomingDamageReductionParams(dtype, .2))
    selections = iter((ctx.units["B1"], ctx.units["A2"]))
    ctx.random.sample = lambda candidates, k: [next(selections)]
    tick(ctx, s, decisions=(True, False, False))
    states = ctx.states.find(state_id=INCOMING_DAMAGE_REDUCTION_STATE_ID)
    assert len(states) == len(list(DamageType)) and all(st.owner_id == "A2" for st in states)
    assert len(ctx.metadata["round_team_transfer_history"][0]["transfers"]) == len(states)


def test_negative_kind_transfer_preserves_source_when_destination_conflicts():
    ctx, s, rt = scene()
    install(ctx, s, rt)
    register_official_state_definitions(ctx.states)
    for name in ("A0", "A1"):
        s.state_lifecycle_system.apply(ctx, state_id="silence", owner_id=name)
    ctx.random.sample = lambda candidates, k: [ctx.units["B2"]]
    tick(ctx, s, decisions=(False, True, False))
    assert not ctx.states.find(owner_id="A0", state_id="silence")
    assert ctx.states.find(owner_id="A1", state_id="silence")
    assert ctx.states.find(owner_id="B2", state_id="silence")
    assert ctx.metadata["round_team_transfer_history"][0]["negative_kinds"] == ["silence"]
    assert [r["status"] for r in ctx.metadata["round_team_transfer_history"][0]["transfers"]] == ["TRANSFERRED", "UNSUPPORTED_BOUNDARY"]


def test_target_immunity_keeps_source_intact():
    ctx, s, rt = scene()
    install(ctx, s, rt)
    register_official_state_definitions(ctx.states)
    original = s.state_lifecycle_system.apply(ctx, state_id="silence", owner_id="A1")
    s.state_lifecycle_system.apply(ctx, state_id="insight", owner_id="B1")
    ctx.current_round = 1
    ctx.current_phase = BattlePhase.ROUND_START.value
    result = StateTransferSupport(s).transfer(ctx, original, "B1", SkillProviderRef(rt.owner_id, rt.skill_slot, "20862"))
    assert result["status"] == "REJECTED_ADMISSION"
    assert ctx.states.has_instance(original.instance_id)
    assert not ctx.states.find(owner_id="B1", state_id="silence")


def test_unknown_snapshot_transfer_fails_before_source_removal():
    ctx, s, rt = scene()
    install(ctx, s, rt)
    register_official_state_definitions(ctx.states)
    original = s.state_lifecycle_system.apply(ctx, state_id="taunt", owner_id="A1", source_id="B1")
    ctx.current_round = 1
    ctx.current_phase = BattlePhase.ROUND_START.value
    with pytest.raises(NotImplementedError, match="schema"):
        StateTransferSupport(s).transfer(ctx, original, "B1", SkillProviderRef(rt.owner_id, rt.skill_slot, "20862"))
    assert ctx.states.has_instance(original.instance_id)


def test_registry_and_actual_engine_seed_replay():
    assert FORMATION_SKILL_REGISTRY["20862"].definition_factory() == SKILL
    histories = []
    for _ in range(2):
        ctx, s, rt = scene()
        ctx.max_rounds = 3
        BattleEngine(ctx, s).run()
        histories.append(ctx.metadata["round_team_transfer_history"])
    assert histories[0] == histories[1]
    assert len(histories[0]) == 3


@pytest.mark.parametrize("level", (0, 11, True, 1.2))
def test_invalid_levels(level):
    with pytest.raises(ValueError):
        create_yan_xing_zhen_definition(level)


def test_invalid_lineup_global_preflight_no_state_or_rng():
    ctx, s, rt = scene()
    ctx.units["A1"].lineup_position = LineupPosition.COMMANDER
    before = ctx.random._rng.getstate()
    with pytest.raises(ValueError, match="lineup"):
        BattleEngine(ctx, s).run()
    assert not ctx.states.find()
    assert before == ctx.random._rng.getstate()


@pytest.mark.parametrize("level", range(1, 11))
def test_exact_static_description_values(level):
    rows = list(csv.DictReader((Path(__file__).parents[1] / "stages/stage14/yan_xing_evidence/static_levels.csv").open(encoding="utf-8-sig")))
    p, amount = LEVEL_RATES[level-1]
    assert f"{p*100:g}%概率" in rows[level-1]["description"]
    assert f"全体{amount:g}统率" in rows[level-1]["description"]


def test_transfer_expiry_and_provider_dependency():
    ctx, s, rt = scene()
    install(ctx, s, rt)
    original = apply(ctx, s, INCOMING_DAMAGE_REDUCTION_STATE_ID, "B1", IncomingDamageReductionParams(DamageType.WEAPON, .2))
    ctx.current_round = 1
    ctx.current_phase = BattlePhase.ROUND_START.value
    ref = SkillProviderRef(rt.owner_id, rt.skill_slot, "20862")
    result = StateTransferSupport(s).transfer(ctx, original, "A2", ref, reduction=True)
    state = ctx.states.get(result["new_instance_id"])
    assert s.state_effectiveness_policy.evaluate_state(ctx, state).effective
    rt.enabled = False
    assert not s.state_effectiveness_policy.evaluate_state(ctx, state).effective
    rt.enabled = True
    s.state_lifecycle_system.expire_at(ctx, round_no=1, phase=BattlePhase.ROUND_END.value)
    assert not ctx.states.has_instance(state.instance_id)


def test_feng_shi_reduction_uses_generic_modifier_after_transfer():
    from sgs_v2.battle_core.feng_shi_zhen import (FENG_SHI_ZHEN_MODIFIER_STATE_ID,
        FengShiZhenModifierParams, register_feng_shi_zhen_state)
    ctx, s, rt = scene()
    install(ctx, s, rt)
    register_feng_shi_zhen_state(ctx.states)
    original = apply(ctx, s, FENG_SHI_ZHEN_MODIFIER_STATE_ID, "B1", FengShiZhenModifierParams(0, -.25))
    ctx.current_round = 1
    ctx.current_phase = BattlePhase.ROUND_START.value
    ref = SkillProviderRef(rt.owner_id, rt.skill_slot, "20862")
    result = StateTransferSupport(s).transfer(ctx, original, "A2", ref, reduction=True)
    new = ctx.states.get(result["new_instance_id"])
    assert new.state_id == DAMAGE_RATE_STATE_ID and new.runtime_params.incoming_rate == -.25
    from sgs_v2.battle_core import DamageRequest, DamageSourceType
    rules = s.damage_rule_provider.collect(ctx, DamageRequest("B1", "A2", DamageType.WEAPON, DamageSourceType.SKILL))
    assert any(c.source.source_skill_id == "20862" and c.operand == .75 for c in rules.modifier_contributions)


def test_both_teams_keep_their_provider_identity_and_once_cursor():
    ctx, s, rt = scene()
    second = create_yan_xing_zhen_runtime("B2", slot=SkillSlot.LEARNED_2)
    ctx.skill_runtimes.register(second)
    install(ctx, s, rt)
    install(ctx, s, second)
    tick(ctx, s, decisions=(False, False, True, False, False, True))
    rows = ctx.metadata["round_team_transfer_history"]
    assert [(r["provider_id"], r["provider_slot"]) for r in rows] == [("A0", 1), ("B2", 2)]
    assert rows[1]["theft"]["target_id"] == "B0"
    assert sum(attr(ctx, s, u) for u in ctx.units) == pytest.approx(1080)


def test_attribute_theft_rejection_never_creates_half_transfer():
    from sgs_v2.battle_core.state_application import AdmissionDecision, AdmissionStatus
    ctx, s, rt = scene()
    install(ctx, s, rt)
    s.state_admission_policy.register_rule_adapter(lambda context, candidate:
        AdmissionDecision(AdmissionStatus.REJECT_SPECIAL_PROTECTION, "TEST_PROTECTED_TARGET")
        if candidate.state_id == ATTRIBUTE_BONUS_STATE_ID and candidate.owner_id == "B1" else None)
    tick(ctx, s)
    assert not ctx.states.find(state_id=ATTRIBUTE_BONUS_STATE_ID)
    assert all(attr(ctx, s, u) == 180 for u in ctx.units)
    assert ctx.metadata["round_team_transfer_history"][0]["theft_status"] == "REJECTED_ATOMIC_ATTRIBUTE_PREFLIGHT"


def test_existing_theft_modifiers_follow_provider_availability():
    ctx, s, rt = scene()
    install(ctx, s, rt)
    tick(ctx, s)
    rt.enabled = False
    assert all(attr(ctx, s, u) == 180 for u in ctx.units)
    rt.enabled = True
    assert attr(ctx, s, "A0") == 210


def test_two_negative_kinds_and_current_round_expiry():
    ctx, s, rt = scene()
    install(ctx, s, rt)
    register_official_state_definitions(ctx.states)
    for sid in ("silence", "weakness"):
        s.state_lifecycle_system.apply(ctx, state_id=sid, owner_id="A1")
    ctx.random.randint = lambda a, b: 2
    ctx.random.sample = lambda candidates, k: [ctx.units["B2"]]
    tick(ctx, s, decisions=(False, True, False))
    assert sorted(ctx.metadata["round_team_transfer_history"][0]["negative_kinds"]) == ["silence", "weakness"]
    assert not ctx.states.find(owner_id="A1")
    assert len(ctx.states.find(owner_id="B2")) == 2
    s.state_lifecycle_system.expire_at(ctx, round_no=1, phase=BattlePhase.ROUND_END.value)
    assert not ctx.states.find(owner_id="B2")
