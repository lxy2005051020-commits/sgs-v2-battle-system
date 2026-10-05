"""Preparation snapshot, real damage and provider-lifecycle regression."""
import pytest

from tests.test_stage14_troop_batch01 import setup, settle
from sgs_v2.battle_core import (
    BattleEngine, BattlePhase, BattleSystems, DamageRequest, DamageType, DamageSourceType,
    OfficialStateId, StateCandidate, StateLifetimeSpec, TroopType, TroopAdmissionStatus,
    SkillSlot, create_teng_jia_bing_runtime, calculate_teng_jia_reduction,
    admit_and_install_troop_skill,
)
from sgs_v2.battle_core.state_modifiers import (
    ATTRIBUTE_BONUS_STATE_ID, AttributeBonusParams, register_modifier_state_definitions,
    INCOMING_DAMAGE_REDUCTION_STATE_ID, IncomingDamageReductionParams,
)
from sgs_v2.battle_core.state_runtime_params import EmptyStateRuntimeParams
from sgs_v2.battle_core.damage_rule_provider import DamageRuleCollection
from sgs_v2.battle_core.troop_admission import TROOP_SKILL_REGISTRY
from sgs_v2.battle_core.troop_skills.teng_jia_bing import SKILL


def fixture(defense=100, holder="a1", systems=None):
    c, s, _ = setup(create_teng_jia_bing_runtime, TroopType.SHIELD, systems=systems or BattleSystems(weapon_random_percent_range=(90, 90), strategy_random_percent_range=(90, 90)))
    for unit in c.units.values(): unit.intelligence = 100
    c.units[holder].defense = defense
    return c, s, create_teng_jia_bing_runtime(holder)


def damage(c, s, kind=DamageType.WEAPON, source=DamageSourceType.SKILL, target="a2"):
    return s.damage_system.calculate(c, DamageRequest("b1", target, kind, source, 1.0))


@pytest.mark.parametrize("defense,expected", [(0, 6/35), (100, .24), (200, 54/175),
    (350, 72/175), (450, .48), (800, .72)])
def test_formula_anchor_points(defense, expected):
    assert calculate_teng_jia_reduction(defense) == pytest.approx(expected)


@pytest.mark.parametrize("value", [True, "100", None, -1, float("inf"), float("nan")])
def test_invalid_attributes(value):
    with pytest.raises((TypeError, ValueError)):
        calculate_teng_jia_reduction(value)


@pytest.mark.parametrize("holder", ["a1", "a3"])
def test_prebattle_holder_snapshot_and_allied_targets(holder):
    c, s, rt = fixture(450, holder)
    assert admit_and_install_troop_skill(c, s, rt).status is TroopAdmissionStatus.SUCCESS
    states = c.states.find(state_id=INCOMING_DAMAGE_REDUCTION_STATE_ID)
    assert {x.owner_id for x in states} == {"a1", "a2", "a3"}
    assert all(x.source_id == holder and x.source_skill_id == "20095" for x in states)
    assert all(x.runtime_params.rate == pytest.approx(.48) for x in states)
    assert all(c.units[x].special_troop_id.value == "TENG_JIA_BING" for x in ("a1", "a2", "a3"))
    assert all(c.units[x].troop_type is TroopType.SHIELD for x in ("a1", "a2", "a3"))
    c.units[holder].defense = 100
    settle(c, s, 8)
    assert all(x.runtime_params.rate == pytest.approx(.48) for x in states)
    assert not c.random.probabilities
    assert admit_and_install_troop_skill(c, s, rt).status is TroopAdmissionStatus.REJECTED_PHASE_ILLEGAL


def test_prior_attribute_modifier_is_visible_and_later_changes_do_not_recalculate():
    c, s, rt = fixture()
    register_modifier_state_definitions(c.states)
    s.state_application_coordinator.apply_candidate(c, StateCandidate(
        state_id=ATTRIBUTE_BONUS_STATE_ID, owner_id="a1", source_id="a1", source_skill_id="earlier",
        runtime_params_candidate=AttributeBonusParams("defense", 350)))
    admit_and_install_troop_skill(c, s, rt)
    assert c.states.find(state_id=INCOMING_DAMAGE_REDUCTION_STATE_ID)[0].runtime_params.rate == pytest.approx(.48)


@pytest.mark.parametrize("kind", list(DamageType))
@pytest.mark.parametrize("source", list(DamageSourceType))
def test_actual_damage_pipeline_weapon_only(kind, source):
    c, s, rt = fixture(450)
    baseline = damage(c, s, kind, source)
    admit_and_install_troop_skill(c, s, rt)
    result = damage(c, s, kind, source)
    expected_factor = .52 if kind is DamageType.WEAPON else 1.0
    assert result.pipeline_trace.modifier_result.output_damage == pytest.approx(
        baseline.pipeline_trace.modifier_result.output_damage * expected_factor)


def test_provider_suppression_restore_and_death():
    c, s, rt = fixture()
    baseline = damage(c, s).pipeline_trace.modifier_result.output_damage
    admit_and_install_troop_skill(c, s, rt)
    assert damage(c, s).pipeline_trace.modifier_result.output_damage == pytest.approx(baseline * .76)
    s.state_application_coordinator.apply_candidate(c, StateCandidate(
        state_id=OfficialStateId.INTIMIDATION.value, owner_id="a1", source_id="b1", source_skill_id="690222",
        lifetime_spec=StateLifetimeSpec.round_calendar(expires_round=2),
        runtime_params_candidate=EmptyStateRuntimeParams()))
    assert damage(c, s).pipeline_trace.modifier_result.output_damage == pytest.approx(baseline)
    settle(c, s, 2, BattlePhase.ROUND_END.value)
    assert damage(c, s).pipeline_trace.modifier_result.output_damage == pytest.approx(baseline * .76)
    c.units["a1"].troops = 0
    assert damage(c, s).pipeline_trace.modifier_result.output_damage == pytest.approx(baseline * .76)


@pytest.mark.parametrize("case", ["wrong_troop", "mixed", "disabled", "no_slot", "out_of_range"])
def test_rejection_before_mutation(case):
    c, s, rt = fixture()
    if case == "wrong_troop": c.units["a1"].troop_type = TroopType.BOW
    elif case == "mixed": c.units["a2"].troop_type = TroopType.BOW
    elif case == "disabled": rt.enabled = False
    elif case == "no_slot": rt = create_teng_jia_bing_runtime("a1", slot=None)
    else: c.units["a1"].defense = 2000
    if case == "out_of_range":
        with pytest.raises(ValueError): admit_and_install_troop_skill(c, s, rt)
    else:
        assert admit_and_install_troop_skill(c, s, rt).status is not TroopAdmissionStatus.SUCCESS
    assert not c.states.find()
    assert all(u.special_troop_id is None for u in c.units.values())


def test_engine_auto_admission_and_canonical_registry():
    c, s, rt = fixture()
    c.skill_runtimes.register(rt)
    c.max_rounds = 1
    BattleEngine(c, s).run()
    applications = [e for e in c.event_bus.history if e.event_type.value == "STATE_APPLIED"
                    and e.payload.get("state_id") == INCOMING_DAMAGE_REDUCTION_STATE_ID]
    assert len(applications) == 3
    assert all(e.phase == BattlePhase.PRE_BATTLE.value for e in applications)
    assert not c.states.find()  # battle finalization clears mounted states
    assert TROOP_SKILL_REGISTRY["20095"].definition_factory() == SKILL


def test_duplicate_install_cannot_stack():
    c, s, rt = fixture()
    admit_and_install_troop_skill(c, s, rt)
    assert admit_and_install_troop_skill(c, s, rt).status is TroopAdmissionStatus.REJECTED_ALREADY_INSTALLED
    assert len(c.states.find(state_id=INCOMING_DAMAGE_REDUCTION_STATE_ID)) == 3


def test_generic_provider_preserves_custom_rule_collection():
    class CustomProvider:
        provider_key = "custom"
        calls = 0
        def collect(self, context, request):
            self.calls += 1
            return DamageRuleCollection()
    provider = CustomProvider()
    c, s, rt = fixture(systems=BattleSystems(damage_rule_provider=provider))
    admit_and_install_troop_skill(c, s, rt)
    damage(c, s)
    assert provider.calls == 1


@pytest.mark.parametrize("rate", [-.1, 1.1, float("nan"), True])
def test_generic_params_validation(rate):
    with pytest.raises((ValueError, TypeError)):
        IncomingDamageReductionParams(DamageType.WEAPON, rate)


from sgs_v2.battle_core.stage10_state_params import ContinuousDamageStateParams
from sgs_v2.battle_core.state_generation import PersistentLifecycleWindow
from sgs_v2.battle_core.state_application_reaction import TROOP_DAMAGE_EFFECT_STATE_ID
from sgs_v2.battle_core.state_application import StateConflictDecision, ApplicationDisposition
from tests.test_stage14_troop_batch02 import tick
from sgs_v2.battle_core import SkillDefinition, SkillRuntime, SkillTargetMode, SkillType, ApplyStateSkillEffectSpec
from types import SimpleNamespace


def apply_burn(c, s, *, source="b1", duration=3, target="a2"):
    definition = SkillDefinition("burn_probe", "burn probe", 1, SkillTargetMode.SINGLE_RANDOM_ENEMY,
        (ApplyStateSkillEffectSpec(OfficialStateId.BURN.value,
            ContinuousDamageStateParams(lifecycle_window=PersistentLifecycleWindow(BattlePhase.PRE_BATTLE.value, 0, 1, duration)),
            continuous_damage_coefficient=1.0),), skill_type=SkillType.ACTIVE)
    runtime = SkillRuntime(definition, source, SkillSlot.LEARNED_2)
    c.current_round = 1
    c.current_phase = BattlePhase.UNIT_ACTION.value
    if c.skill_runtimes.get(source, SkillSlot.LEARNED_2) is None:
        c.skill_runtimes.register(runtime)
    effects = s.skill_resolver.resolve(c, runtime, inherited_target_ids=(target,)).effects
    for effect in effects: s.effect_executor.execute(c, effect)
    return SimpleNamespace(instance=c.states.find(state_id=OfficialStateId.BURN.value, owner_id=target)[0])


from sgs_v2.battle_core.state_removal import RemovalOperation, RemovalDecision, RemovalDecisionStatus
from sgs_v2.battle_core import EventType


@pytest.mark.parametrize("operation", [RemovalOperation.ORDINARY_CLEANSE, RemovalOperation.SPECIALIZED_CLEANSE])
def test_successful_burn_cleanse_removes_only_associated_effect(operation):
    c, s, rt = fixture()
    admit_and_install_troop_skill(c, s, rt)
    parent = apply_burn(c, s).instance
    other = apply_burn(c, s, target="a3").instance
    def permit_burn(context, op, state):
        if state.state_id == OfficialStateId.BURN.value:
            return RemovalDecision(RemovalDecisionStatus.ALLOW, op, "TEST_BURN_CLEANSE_ALLOWED")
    s.state_removal_policy.register_rule_adapter(permit_burn)
    seen = []
    def observe(event):
        if event.payload.get("instance_id") == parent.instance_id:
            seen.append(tuple(x.instance_id for x in c.states.find(owner_id="a2", state_id=TROOP_DAMAGE_EFFECT_STATE_ID)))
    c.event_bus.subscribe(EventType.STATE_REMOVED, observe)
    result = s.state_removal_coordinator.remove(c, operation=operation, instance_id=parent.instance_id)
    assert result.removed_instance.instance_id == parent.instance_id
    assert seen == [()]  # observers cannot see an orphaned extra effect
    assert not c.states.find(owner_id="a2", state_id=TROOP_DAMAGE_EFFECT_STATE_ID)
    assert not c.states.find(owner_id="a2", state_id=OfficialStateId.BURN.value)
    assert len(c.states.find(owner_id="a3", state_id=TROOP_DAMAGE_EFFECT_STATE_ID)) == 1
    assert other.instance_id in c.states
    assert not tick(c, s, "a2", 1).effect_results
    assert c.states.find(owner_id="a2", state_id=INCOMING_DAMAGE_REDUCTION_STATE_ID)


def test_rejected_cleanse_keeps_both_states_and_damage():
    c, s, rt = fixture()
    admit_and_install_troop_skill(c, s, rt)
    parent = apply_burn(c, s).instance
    def reject(context, op, state):
        return RemovalDecision(RemovalDecisionStatus.REJECT_CONTRACT_PROTECTED, op, "TEST_CLEANSE_REJECTED")
    s.state_removal_policy.register_rule_adapter(reject)
    result = s.state_removal_coordinator.remove(c, operation=RemovalOperation.ORDINARY_CLEANSE,
                                               instance_id=parent.instance_id)
    assert result.removed_instance is None
    assert len(c.states.find(state_id=TROOP_DAMAGE_EFFECT_STATE_ID)) == 1
    assert len(tick(c, s, "a2", 1).effect_results) == 2


def test_refreshed_parent_cleanse_removes_refreshed_extra():
    c, s, rt = fixture()
    admit_and_install_troop_skill(c, s, rt)
    parent = apply_burn(c, s).instance
    apply_burn(c, s, duration=5)
    extra = c.states.find(state_id=TROOP_DAMAGE_EFFECT_STATE_ID)[0]
    assert extra.lifecycle_window.last_eligible_round == 5
    s.state_lifecycle_system.remove(c, parent.instance_id, reason="ORDINARY_CLEANSE")
    assert extra.instance_id not in c.states


def test_stale_expiry_does_not_remove_current_parent_or_extra():
    c, s, rt = fixture()
    admit_and_install_troop_skill(c, s, rt)
    parent = apply_burn(c, s).instance
    apply_burn(c, s, duration=5)
    assert s.state_lifecycle_system.expire_state(c, parent.instance_id,
        expected_generation_id=parent.current_generation_id) is None
    assert c.states.find(state_id=TROOP_DAMAGE_EFFECT_STATE_ID)
    s.state_lifecycle_system.expire_state(c, parent.instance_id)
    assert not c.states.find(state_id=TROOP_DAMAGE_EFFECT_STATE_ID)


@pytest.mark.parametrize("commander,expected", [(None, 3.0), ("兀突骨", 2.5)])
def test_extra_effect_source_coexistence_snapshot_and_real_ticks(commander, expected):
    c, s, rt = fixture()
    if commander: c.units["a1"].name = commander
    c.units["a1"].intelligence = 999  # must not be the formula source
    c.units["b1"].intelligence = 350
    admit_and_install_troop_skill(c, s, rt)
    original = apply_burn(c, s).instance
    extra = c.states.find(state_id=TROOP_DAMAGE_EFFECT_STATE_ID)[0]
    assert extra.state_id != OfficialStateId.BURN.value
    assert c.states.get_definition(extra.state_id).name == "藤甲兵效果"
    assert len(c.states.find(state_id=OfficialStateId.BURN.value)) == 1
    basis = extra.runtime_params.frozen_damage_basis
    assert basis.coefficient == expected and basis.source_unit_id == "b1"
    assert basis.source_formula_facts.source_combat_attribute_at_application == 350
    assert basis.source_formula_facts.source_troops_at_application == 10000
    assert basis.physical_state_instance_id == extra.instance_id
    assert basis.application_generation_id == extra.current_generation_id
    assert extra.lifecycle_window == original.lifecycle_window
    c.units["b1"].intelligence = 1
    c.units["b1"].troops = 0
    result = tick(c, s, "a2", 1)
    assert len(result.effect_results) == 2
    events = [e for e in c.event_bus.history if e.event_type.value == "DAMAGE_DEALT"]
    assert {e.payload.get("source_state_id") for e in events} == {OfficialStateId.BURN.value, extra.state_id}
    assert all(e.actor_id == "b1" for e in events)
    assert len(c.states.find(state_id=TROOP_DAMAGE_EFFECT_STATE_ID)) == 1  # no recursion
    assert not tick(c, s, "a2", 1).effect_results  # one opportunity per owner/round


def test_nonburn_does_not_trigger_and_wutugu_deputy_does_not_reduce_rate():
    c, s, rt = fixture()
    c.units["a3"].name = "兀突骨"
    admit_and_install_troop_skill(c, s, rt)
    s.state_application_coordinator.apply_candidate(c, StateCandidate(
        state_id=OfficialStateId.POISON.value, owner_id="a2", source_id="b1",
        runtime_params_candidate=ContinuousDamageStateParams(
            lifecycle_window=PersistentLifecycleWindow(BattlePhase.PRE_BATTLE.value, 0, 1, 3))))
    assert not c.states.find(state_id=TROOP_DAMAGE_EFFECT_STATE_ID)
    apply_burn(c, s)
    assert c.states.find(state_id=TROOP_DAMAGE_EFFECT_STATE_ID)[0].runtime_params.frozen_damage_basis.coefficient == 3


def test_refresh_updates_extra_without_stacking_and_effects_expire():
    c, s, rt = fixture()
    admit_and_install_troop_skill(c, s, rt)
    def refresh_burn(context, candidate, residents):
        if candidate.state_id == OfficialStateId.BURN.value:
            return StateConflictDecision(ApplicationDisposition.REFRESH, "TEST_BURN_REFRESH",
                                         existing_instance_id=residents[0].instance_id)
    s.state_conflict_policy.register_rule_adapter(refresh_burn)
    apply_burn(c, s)
    old = c.states.find(state_id=TROOP_DAMAGE_EFFECT_STATE_ID)[0]
    c.units["b1"].intelligence = 400
    apply_burn(c, s, duration=4)
    extra = c.states.find(state_id=TROOP_DAMAGE_EFFECT_STATE_ID)
    assert len(extra) == 1 and extra[0].instance_id == old.instance_id
    assert extra[0].current_generation_id != old.current_generation_id
    assert extra[0].runtime_params.frozen_damage_basis.source_formula_facts.source_combat_attribute_at_application == 400
    assert extra[0].lifecycle_window.last_eligible_round == 4
    tick(c, s, "a2", 1)
    tick(c, s, "a2", 4)
    s.state_lifecycle_system.settle_action_start_lifetimes(c, "a2")
    assert not c.states.find(state_id=TROOP_DAMAGE_EFFECT_STATE_ID)


def test_without_troop_skill_no_extra_effect():
    c, s, rt = fixture()
    apply_burn(c, s)
    assert not c.states.find(state_id=TROOP_DAMAGE_EFFECT_STATE_ID)
