"""Behavioral wiring tests; the user-provisional model is not empirical evidence."""
from dataclasses import replace
from fractions import Fraction
from math import ceil

import pytest

from test_stage14_troop_batch01 import setup, settle
from sgs_v2.battle_core import (
    BattleEngine, BattlePhase, BattleSystems, DamageEffect, DamageSourceType, DamageType,
    EventType, ExactRatio, OfficialStateId, StateCandidate, StateLifetimeSpec,
    TroopAdmissionStatus, TroopType, admit_and_install_troop_skill, create_qing_zhou_bing_runtime,
)
from sgs_v2.battle_core.additive_treatment_formula import AdditiveTreatmentFormulaSystem
from sgs_v2.battle_core.pending_work import PendingWorkStatus, PendingWorkTimingPoint
from sgs_v2.battle_core.scheduled_team_recovery import (
    ScheduledTeamRecoverySpec, project_settled_enemy_team_loss,
)
from sgs_v2.battle_core.stage10_state_params import RecoveryPotencyContext
from sgs_v2.battle_core.stage10_state_params import ContinuousDamageStateParams
from sgs_v2.battle_core.state_generation import PersistentLifecycleWindow
from sgs_v2.battle_core import (
    ApplyStateSkillEffectSpec, SkillDefinition, SkillRuntime, SkillTargetMode, UnitActionStartHook,
)
from sgs_v2.battle_core.stage11_state_params import Stage11TimedFlagParams
from sgs_v2.battle_core.effects import EffectSourceRef
from sgs_v2.battle_core.operation_identity import SourceType
from sgs_v2.battle_core.stage9_state_params import DamageShareStateParams, DistributionStateParams
from sgs_v2.battle_core.state_runtime_params import EmptyStateRuntimeParams
from sgs_v2.battle_core.treatment_formula import TreatmentFormulaSystem, TreatmentModifierSnapshot
from sgs_v2.battle_core.troop_admission import TROOP_SKILL_REGISTRY
from sgs_v2.battle_core.troop_skills.qing_zhou_bing import (
    CONFIG, SKILL, CAO_CAO_COMMANDER_ENHANCEMENT, PROVISIONAL_DAMAGE_BASIS_RATIO,
)


def fixture(*, holder="a1", systems=None, install=True):
    c, s, _ = setup(create_qing_zhou_bing_runtime, TroopType.SPEAR, systems=systems)
    c.units[holder].attack = 200
    c.units[holder].intelligence = 999
    rt = create_qing_zhou_bing_runtime(holder)
    if install:
        assert admit_and_install_troop_skill(c, s, rt).status is TroopAdmissionStatus.SUCCESS
    return c, s, rt


def due(c, s, round_no=3):
    settle(c, s, round_no)
    return s.pending_work_system.process(c, PendingWorkTimingPoint(round_no, BattlePhase.ROUND_START))


def state(c, s, state_id, uid="a1", params=None, *, expires_round=5):
    return s.state_application_coordinator.apply_candidate(c, StateCandidate(
        state_id=state_id.value, owner_id=uid, source_id="b1", source_skill_id="blocker",
        lifetime_spec=StateLifetimeSpec.round_calendar(expires_round=expires_round),
        runtime_params_candidate=params or (Stage11TimedFlagParams()
            if state_id is OfficialStateId.HEALING_BAN else EmptyStateRuntimeParams())))


def damage(c, s, target="a2", *, source="b2", round_no=1, damage_type=DamageType.WEAPON,
           source_type=DamageSourceType.SKILL, coefficient=1.0):
    c.current_round = round_no
    c.current_phase = BattlePhase.UNIT_ACTION.value
    return s.effect_executor.execute(c, DamageEffect(source, target, damage_type,
        coefficient=coefficient, source_type=source_type, source_skill_id="probe-damage",
        source_ref=EffectSourceRef(SourceType.ACTIVE_SKILL, source, "probe-damage")))


def wound(c, uid, troops, wounded=None):
    u = c.units[uid]
    u.troops = troops
    u.wounded_troops = 10000 - troops if wounded is None else wounded
    u._wounded_pool_authoritative = True


def publish_loss(c, *, source="b2", target="a2", amount=1001, round_no=1,
                 kind=EventType.DAMAGE_DEALT, **extra):
    return c.event_bus.publish(event_type=kind, phase=BattlePhase.UNIT_ACTION.value,
        round_no=round_no, actor_id=source, target_id=target,
        payload={"damage": amount, "actual_loss": amount, **extra})


def test_registry_and_placeholder_and_conversion():
    assert TROOP_SKILL_REGISTRY["20153"] is CONFIG
    assert create_qing_zhou_bing_runtime("a1").definition is SKILL
    assert CAO_CAO_COMMANDER_ENHANCEMENT is None
    assert PROVISIONAL_DAMAGE_BASIS_RATIO == ExactRatio(1, 10)
    c, s, rt = fixture()
    assert all(c.units[x].special_troop_id.value == "QING_ZHOU_BING" for x in ("a1", "a2", "a3"))
    assert all(c.units[x].troop_type is TroopType.SPEAR for x in ("a1", "a2", "a3"))
    assert not c.states.find(owner_id="b1")
    counters = c.states.find(state_id=OfficialStateId.COUNTERATTACK.value)
    assert len(counters) == 2 and len({x.owner_id for x in counters}) == 2
    assert all(x.source_id == "a1" and x.source_skill_id == "20153" for x in counters)
    assert all(x.runtime_params.damage_rate == ExactRatio(18, 25) for x in counters)
    assert len(c.pending_work.all()) == 1
    assert not c.random.probabilities
    assert admit_and_install_troop_skill(c, s, rt).status is TroopAdmissionStatus.REJECTED_ALREADY_INSTALLED
    assert len(c.pending_work.all()) == 1


def test_counter_selection_includes_holder_and_uses_single_selector():
    c, s, rt = fixture(install=False)
    calls = []
    def sample(candidates, count):
        calls.append((tuple(u.unit_id for u in candidates), count))
        return candidates[:count]
    c.random.sample = sample
    admit_and_install_troop_skill(c, s, rt)
    assert calls == [(('a1', 'a2', 'a3'), 2)]
    assert {x.owner_id for x in c.states.find(state_id=OfficialStateId.COUNTERATTACK.value)} == {"a1", "a2"}


@pytest.mark.parametrize("round_no", [1, 2])
def test_normal_attack_reuses_actual_attacker_counter_and_damage_owner(round_no):
    c, s, rt = fixture()
    counter = c.states.find(state_id=OfficialStateId.COUNTERATTACK.value)[0]
    s.target_system.random_enemy = lambda context, attacker: c.units[counter.owner_id]
    c.current_round = round_no
    c.current_phase = BattlePhase.UNIT_ACTION.value
    result = s.normal_attack_system.execute(c, c.units["b2"])
    events = [e for e in c.event_bus.history if e.event_type is EventType.DAMAGE_DEALT
              and e.payload.get("source_skill_id") == "20153"]
    assert result.actual_target_id == counter.owner_id
    assert len(events) == 1
    assert events[0].actor_id == counter.owner_id and events[0].target_id == "b2"
    assert events[0].payload["source_type"] == "COUNTER"
    assert events[0].payload["coefficient"] == .72


def test_skill_damage_is_not_a_counter_trigger_and_round_three_expires_counter():
    c, s, rt = fixture()
    target = c.states.find(state_id=OfficialStateId.COUNTERATTACK.value)[0].owner_id
    damage(c, s, target)
    assert not any(e.event_type is EventType.COUNTER_EXECUTE for e in c.event_bus.history)
    due(c, s)
    assert not c.states.find(state_id=OfficialStateId.COUNTERATTACK.value)
    s.target_system.random_enemy = lambda context, attacker: c.units[target]
    c.current_phase = BattlePhase.UNIT_ACTION.value
    s.normal_attack_system.execute(c, c.units["b2"])
    assert not any(e.event_type is EventType.COUNTER_EXECUTE for e in c.event_bus.history)


@pytest.mark.parametrize("D", [0, 1, 10, 1001, 10000])
def test_damage_basis_is_added_before_rate_and_preserves_fraction_and_force(D):
    c, s, rt = fixture()
    wound(c, "a2", 1000)
    publish_loss(c, amount=D)
    result = due(c, s)[0].result
    b = s.treatment_formula_system.troop_function(10000)
    expected = ceil((b + 200 + Fraction(D, 10)) * Fraction(18, 10))
    assert result.loss_basis.actual_loss == D
    assert result.formula.nominal_recovery == expected
    assert result.formula.source_attribute == 200
    assert result.formula.base_addition == ExactRatio(D, 10)
    assert c.units["a2"].troops == 1000 + expected
    assert due(c, s) == ()


def test_shared_budget_lowest_first_and_lineup_tiebreak_and_wound_capacity():
    c, s, rt = fixture()
    wound(c, "a2", 4000, 100)
    wound(c, "a3", 4000, 200)
    wound(c, "a1", 8000, 2000)
    result = due(c, s)[0].result
    assert [r.request.target_id for r in result.allocations] == ["a2", "a3", "a1"]
    assert [r.request.amount for r in result.allocations[:2]] == [100, 200]
    assert sum(r.request.amount for r in result.allocations) == result.formula.nominal_recovery
    assert result.remaining_nominal == 0
    assert c.units["a2"].troops == 4100 and c.units["a3"].troops == 4200


def test_zero_capacity_and_dead_allies_do_not_receive_treatment():
    c, s, rt = fixture()
    wound(c, "a2", 0, 0)
    wound(c, "a3", 3000, 0)
    result = due(c, s)[0].result
    assert result.allocations == ()
    assert result.remaining_nominal == result.formula.nominal_recovery
    assert c.units["a2"].troops == 0


def test_healing_ban_skips_without_spending_shared_nominal_pool():
    c, s, rt = fixture()
    wound(c, "a2", 1000)
    wound(c, "a3", 2000)
    state(c, s, OfficialStateId.HEALING_BAN, "a2")
    result = due(c, s)[0].result
    assert c.units["a2"].troops == 1000
    assert c.units["a3"].troops == 2000 + result.formula.nominal_recovery
    assert len(result.allocations) == 2
    assert result.remaining_nominal == 0


def test_recipient_modifier_uses_existing_settlement_and_nominal_budget_once():
    systems = BattleSystems(recovery_modifier_provider=lambda c, r: ExactRatio(3, 2))
    c, s, rt = fixture(systems=systems)
    wound(c, "a2", 1000)
    result = due(c, s)[0].result
    amount = result.formula.nominal_recovery
    assert result.allocations[0].modified_recovery == ceil(Fraction(amount * 3, 2))
    assert result.remaining_nominal == 0
    assert c.units["a2"].troops == 1000 + ceil(Fraction(amount * 3, 2))


def test_source_snapshot_and_cao_cao_placeholder():
    c, s, rt = fixture(holder="a3", install=False)
    c.units["a1"].name = "曹操"
    c.units["a1"].defense = 9999
    admit_and_install_troop_skill(c, s, rt)
    wound(c, "a2", 1000)
    c.units["a3"].attack = 999
    c.units["a3"].troops = 8000
    result = due(c, s)[0].result
    assert result.formula.source_attribute == 200
    assert result.formula.troop_function_value == s.treatment_formula_system.troop_function(10000)
    assert result.formula.nominal_recovery == ceil(Fraction((result.formula.troop_function_value + 200) * 18, 10))


@pytest.mark.parametrize("blocker", ["death", "disabled", "intimidation"])
def test_scheduled_recovery_rechecks_provider_at_due_time(blocker):
    c, s, rt = fixture(holder="a3")
    wound(c, "a2", 1000)
    if blocker == "death":
        wound(c, "a3", 0, 0)
    elif blocker == "disabled":
        rt.enabled = False
    else:
        state(c, s, OfficialStateId.INTIMIDATION, "a3", expires_round=2)
    assert due(c, s) == ()
    assert c.units["a2"].troops == 1000
    assert c.pending_work.all()[0].status is PendingWorkStatus.CANCELLED
    assert c.units["a2"].special_troop_id.value == "QING_ZHOU_BING"


def test_no_early_treatment_and_exact_third_round_once():
    c, s, rt = fixture()
    wound(c, "a2", 1000)
    assert due(c, s, 1) == () and due(c, s, 2) == ()
    assert c.units["a2"].troops == 1000
    assert len(due(c, s, 3)) == 1
    assert due(c, s, 4) == ()


def test_damage_projection_filters_direction_window_and_duplicate_event_families():
    c, s, rt = fixture()
    publish_loss(c, amount=100)
    publish_loss(c, amount=200, round_no=2, target="a3")
    publish_loss(c, amount=999, source="a1", target="b1")
    publish_loss(c, amount=888, source="a1", target="a2")
    publish_loss(c, amount=777, round_no=0)
    publish_loss(c, amount=666, round_no=3)
    publish_loss(c, amount=555, kind=EventType.DAMAGE_RESOLVED)
    publish_loss(c, amount=40, kind=EventType.DIRECT_TROOP_LOSS, direct_loss_id="one")
    publish_loss(c, amount=40, kind=EventType.DIRECT_TROOP_LOSS, direct_loss_id="one")
    result = project_settled_enemy_team_loss(c, team_id="a", first_round=1, last_round=2)
    assert result.actual_loss == 340 and len(result.event_sequences) == 3


@pytest.mark.parametrize("family", ["share", "distribution"])
def test_real_partition_counts_actual_primary_and_participant_losses_once(family):
    c, s, rt = fixture()
    if family == "share":
        state(c, s, OfficialStateId.DAMAGE_SHARE, "a2", DamageShareStateParams("a3", ExactRatio(1, 2)))
    else:
        state(c, s, OfficialStateId.DAMAGE_SPLIT, "a2", DistributionStateParams(ExactRatio(1, 2)))
    before = sum(c.units[x].troops for x in ("a1", "a2", "a3"))
    damage(c, s)
    actual = before - sum(c.units[x].troops for x in ("a1", "a2", "a3"))
    assert actual > 0
    assert any(e.event_type is EventType.DIRECT_TROOP_LOSS for e in c.event_bus.history)
    result = due(c, s)[0].result
    assert result.loss_basis.actual_loss == actual


@pytest.mark.parametrize("damage_type", [DamageType.WEAPON, DamageType.STRATEGY])
def test_real_weapon_and_strategy_losses_are_included(damage_type):
    c, s, rt = fixture()
    c.units["b2"].intelligence = 300
    c.units["a2"].intelligence = 100
    before = c.units["a2"].troops
    damage(c, s, damage_type=damage_type)
    loss = before - c.units["a2"].troops
    assert loss > 0
    assert due(c, s)[0].result.loss_basis.actual_loss == loss


def test_real_engine_installs_treatment_and_finalizes_without_residual_work():
    c, s, rt = fixture(install=False)
    c.skill_runtimes.register(rt)
    c.max_rounds = 3
    result = BattleEngine(c, s).run()
    summaries = [e for e in c.event_bus.history if e.event_type is EventType.RECOVERY_RESOLVED
                 and e.payload.get("source_skill_id") == "20153"]
    assert result.rounds_completed == 3 and len(summaries) == 1
    assert summaries[0].round_no == 3 and summaries[0].phase == "ROUND_START"
    assert summaries[0].payload["damage_basis"] > 0
    assert not c.states.find()
    assert all(w.status is not PendingWorkStatus.PENDING for w in c.pending_work.all())


def test_early_finalization_cancels_future_treatment():
    c, s, rt = fixture(install=False)
    c.skill_runtimes.register(rt)
    c.max_rounds = 1
    BattleEngine(c, s).run()
    assert not any(e.event_type is EventType.RECOVERY_RESOLVED for e in c.event_bus.history)
    assert c.pending_work.all()[0].status is PendingWorkStatus.CANCELLED


def test_admission_rejects_wrong_troop_missing_slot_and_bad_source_before_mutation():
    c, s, rt = fixture(install=False)
    c.units["a1"].troop_type = TroopType.BOW
    assert admit_and_install_troop_skill(c, s, rt).status is TroopAdmissionStatus.REJECTED_INVALID_TROOP
    c.units["a1"].troop_type = TroopType.SPEAR
    no_slot = create_qing_zhou_bing_runtime("a1", slot=None)
    assert admit_and_install_troop_skill(c, s, no_slot).status is TroopAdmissionStatus.REJECTED_PROVIDER_SLOT_CONFLICT
    c.units["a1"].attack = float("nan")
    with pytest.raises(ValueError):
        admit_and_install_troop_skill(c, s, rt)
    assert not c.states.find() and not c.pending_work.all()
    assert all(u.special_troop_id is None for u in c.units.values())


@pytest.mark.parametrize("addition", [0, ExactRatio(1001, 10)])
def test_generic_additive_formula_preserves_modifiers_and_final_ceil(addition):
    table = {i: 300 for i in range(1, 10001)}
    f = AdditiveTreatmentFormulaSystem(troop_function_table=table)
    mods = TreatmentModifierSnapshot(source_side_deltas=(ExactRatio(1, 10),),
        target_side_deltas=(ExactRatio(-1, 5),), red_pool_multiplier=ExactRatio(21, 20))
    result = f.calculate(rate=1.8, source_troops=10000, source_attribute=200,
                         base_addition=addition, modifiers=mods)
    term = Fraction(0) if addition == 0 else Fraction(1001, 10)
    assert result.nominal_recovery == ceil((500 + term) * Fraction(18, 10) * Fraction(11, 10) * Fraction(4, 5) * Fraction(21, 20))
    assert result.source_attribute == 200 and result.troop_function_value == 300
    if addition == 0:
        old = TreatmentFormulaSystem(troop_function_table=table).calculate(rate=1.8,
            source_troops=10000, source_attribute=200, modifiers=mods)
        assert result.nominal_recovery == old.nominal_recovery


@pytest.mark.parametrize("value", [True, -1, float("nan"), float("inf"), ExactRatio(-1, 2)])
def test_additive_formula_rejects_invalid_basis(value):
    with pytest.raises((TypeError, ValueError)):
        AdditiveTreatmentFormulaSystem().calculate(rate=1.8, source_troops=10000,
            source_attribute=200, base_addition=value)


def test_shared_spec_requires_complete_source_and_consistent_damage_window():
    with pytest.raises(ValueError):
        ScheduledTeamRecoverySpec(3, 1, 2, RecoveryPotencyContext(base_rate=1.8))
    potency = RecoveryPotencyContext(base_rate=1.8, source_troops_at_application=10000,
                                     source_attribute_at_application=200)
    spec = ScheduledTeamRecoverySpec(3, 1, 2, potency)
    with pytest.raises(ValueError):
        replace(spec, last_damage_round=3)
    with pytest.raises(ValueError):
        replace(spec, damage_basis_ratio=ExactRatio(-1, 10))


@pytest.mark.parametrize("blocker", ["disabled", "intimidation"])
def test_counter_temporary_provider_suppression_and_resume_preserves_state(blocker):
    c, s, rt = fixture(holder="a3")
    counter = c.states.find(state_id=OfficialStateId.COUNTERATTACK.value)[0]
    if blocker == "disabled":
        rt.enabled = False
    else:
        state(c, s, OfficialStateId.INTIMIDATION, "a3", expires_round=2)
    assert s.stage9_state_runtime.get_counter_effects(c, counter.owner_id) == ()
    assert c.states.get(counter.instance_id) is counter
    if blocker == "disabled":
        rt.enabled = True
    else:
        settle(c, s, 2, phase=BattlePhase.ROUND_END.value)
    assert counter in s.stage9_state_runtime.get_counter_effects(c, counter.owner_id)


def test_deputy_provider_death_preserves_installed_counter_but_cancels_holder_work():
    c, s, rt = fixture(holder="a3", install=False)
    c.random.sample = lambda pool, n: pool[:n]
    admit_and_install_troop_skill(c, s, rt)
    wound(c, "a3", 0, 0)
    s.target_system.random_enemy = lambda context, attacker: c.units["a2"]
    c.current_round = 1
    c.current_phase = BattlePhase.UNIT_ACTION.value
    s.normal_attack_system.execute(c, c.units["b2"])
    assert any(e.event_type is EventType.COUNTER_EXECUTE and e.actor_id == "a2"
               for e in c.event_bus.history)
    assert due(c, s) == ()
    assert c.pending_work.all()[0].status is PendingWorkStatus.CANCELLED


def test_enemy_counter_damage_is_recorded_through_real_normal_attack_chain():
    from sgs_v2.battle_core.stage9_state_params import CounterStateParams
    c, s, rt = fixture()
    state(c, s, OfficialStateId.COUNTERATTACK, "b2", CounterStateParams(ExactRatio(1, 1)))
    s.target_system.random_enemy = lambda context, attacker: c.units["b2"]
    c.current_round = 1
    c.current_phase = BattlePhase.UNIT_ACTION.value
    before = c.units["a2"].troops
    s.normal_attack_system.execute(c, c.units["a2"])
    actual = before - c.units["a2"].troops
    assert actual > 0
    assert due(c, s)[0].result.loss_basis.actual_loss == actual


def test_periodic_damage_counts_frozen_physical_enemy_source():
    c, s, rt = fixture()
    dot = SkillRuntime(SkillDefinition("probe-dot", "probe", 1.0,
        SkillTargetMode.SINGLE_RANDOM_ENEMY,
        (ApplyStateSkillEffectSpec(OfficialStateId.ROUT.value,
            ContinuousDamageStateParams(lifecycle_window=PersistentLifecycleWindow(
                BattlePhase.PRE_BATTLE.value, 0, 1, 2)),
            continuous_damage_coefficient=.64),)), "b2")
    c.random.sample = lambda pool, n: [next(u for u in pool if u.unit_id == "a2")]
    for effect in s.skill_resolver.resolve(c, dot).effects:
        s.effect_executor.execute(c, effect)
    c.current_round = 1
    c.current_phase = BattlePhase.UNIT_ACTION_START.value
    c.action_progress.set_current_acting_unit("a2")
    c.action_progress.mark_action_start("a2", 1)
    before = c.units["a2"].troops
    s.rule_hook_system.process(c, UnitActionStartHook(1, "a2"))
    actual = before - c.units["a2"].troops
    assert actual > 0
    assert due(c, s)[0].result.loss_basis.actual_loss == actual


@pytest.mark.parametrize("size", [1, 2])
def test_two_member_team_uses_no_rng_and_single_member_fails_before_mutation(size):
    c, s, rt = fixture(install=False)
    for uid in ("a3", "a2")[:3-size]:
        c.units.pop(uid)
    calls = []
    c.random.sample = lambda pool, n: calls.append(n) or pool[:n]
    if size == 1:
        with pytest.raises(NotImplementedError, match="少于两名"):
            admit_and_install_troop_skill(c, s, rt)
        assert not c.pending_work.all() and not c.states.find()
        assert c.units["a1"].special_troop_id is None
    else:
        admit_and_install_troop_skill(c, s, rt)
        assert len(c.states.find(state_id=OfficialStateId.COUNTERATTACK.value)) == 2
    assert calls == []


@pytest.mark.parametrize("amount", [True, -1, 1.5])
def test_damage_projection_rejects_malformed_settled_input(amount):
    c, s, rt = fixture()
    publish_loss(c, amount=amount)
    with pytest.raises((TypeError, ValueError)):
        project_settled_enemy_team_loss(c, team_id="a", first_round=1, last_round=2)
