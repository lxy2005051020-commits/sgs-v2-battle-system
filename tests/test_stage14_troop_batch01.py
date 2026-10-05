"""Behavioral regression for the full-level baseline batch and generic seams."""
from dataclasses import replace

import pytest

from sgs_v2.battle_core import (
    BattleContext, BattleEngine, BattlePhase, BattleSystems, EventBus,
    LineupPosition, OfficialStateId, RandomSystem, SkillDefinition, SkillRuntime,
    SkillSlot, SkillTargetMode, SkillType, ApplyStateSkillEffectSpec,
    StateCandidate, StateLifetimeSpec, StateNode, TroopAdmissionStatus, TroopType,
    UnitRuntime, admit_and_install_troop_skill, create_bai_ma_yi_cong_runtime,
    create_hu_bao_qi_runtime, create_xiliang_cavalry_runtime,
    register_official_state_definitions, AttributeSystem,
)
from sgs_v2.battle_core.skill_resolver import SkillResolutionStatus
from sgs_v2.battle_core.state_modifiers import (
    ACTIVATION_RATE_BONUS_STATE_ID, ATTRIBUTE_BONUS_STATE_ID,
    ActivationRateBonusParams, AttributeBonusParams, register_modifier_state_definitions,
)
from sgs_v2.battle_core.state_runtime_params import EmptyStateRuntimeParams


class RecordingRandom(RandomSystem):
    def __init__(self):
        super().__init__(42)
        self.probabilities = []

    def chance(self, probability):
        self.probabilities.append(probability)
        return True


CASES = [(create_bai_ma_yi_cong_runtime, TroopType.BOW, "BAI_MA_YI_CONG", 3, SkillType.ACTIVE),
         (create_hu_bao_qi_runtime, TroopType.CAVALRY, "HU_BAO_QI", 4, SkillType.ASSAULT)]


def setup(factory, troop, *, systems=None):
    units = {}
    for team in ("a", "b"):
        for i, position in enumerate(LineupPosition, 1):
            uid = f"{team}{i}"
            units[uid] = UnitRuntime(
                unit_id=uid, name=uid, team_id=team, max_troops=10000, troops=10000,
                attack=120, defense=120, speed=10 if team == "a" else 200,
                troop_type=troop if team == "a" else TroopType.SPEAR,
                lineup_position=position,
            )
    context = BattleContext(battle_id="batch01", units=units, event_bus=EventBus(),
                            random=RecordingRandom(), max_rounds=5)
    register_official_state_definitions(context.states)
    context.current_phase = BattlePhase.PRE_BATTLE.value
    return context, systems or BattleSystems(), factory("a1")


def settle(context, systems, round_no, phase=BattlePhase.ROUND_START.value):
    context.current_round = round_no
    context.current_phase = phase
    due = systems.state_lifecycle_system.due_at(context, round_no=round_no, phase=phase)
    before = systems.effectiveness_transition_coordinator.capture(
        context, tuple(StateNode(s.instance_id) for s in due))
    removed = systems.state_lifecycle_system.expire_at(context, round_no=round_no, phase=phase)
    systems.effectiveness_transition_coordinator.complete_removed_nodes(
        context, before, tuple(StateNode(s.instance_id) for s in removed))


def probe(skill_type, rate=0.35):
    return SkillRuntime(SkillDefinition(
        skill_id="probe", name="probe", activation_rate=rate, skill_type=skill_type,
        target_mode=SkillTargetMode.FIXED_ALL_ENEMIES,
        effect_specs=(ApplyStateSkillEffectSpec(OfficialStateId.WEAKNESS.value),),
    ), owner_id="a2", skill_slot=SkillSlot.LEARNED_2)


@pytest.mark.parametrize("factory,troop,special,expiry,kind", CASES)
def test_conversion_team_effects_and_exact_round_window(factory, troop, special, expiry, kind):
    context, systems, runtime = setup(factory, troop)
    result = admit_and_install_troop_skill(context, systems, runtime)
    assert result.status is TroopAdmissionStatus.SUCCESS
    assert result.converted_unit_ids == ("a1", "a2", "a3")
    assert not context.random.probabilities  # deterministic installation
    for uid in ("a1", "a2", "a3"):
        assert context.units[uid].special_troop_id.value == special
        assert context.units[uid].troop_type is troop
        states = context.states.find(owner_id=uid)
        assert len(states) == 2
        assert all(s.source_id == "a1" and s.source_skill_id == runtime.definition.skill_id for s in states)
    assert not context.states.find(owner_id="b1")
    for round_no in range(1, expiry):
        settle(context, systems, round_no)
        assert systems.state_modifier_support.activation_rate(context, probe(kind)) == pytest.approx(.45)
        assert systems.state_modifier_support.activation_rate(context, probe(
            SkillType.ASSAULT if kind is SkillType.ACTIVE else SkillType.ACTIVE)) == .35
        if troop is TroopType.BOW:
            assert systems.action_order_system.determine_order(context)[0].team_id == "a"
        else:
            assert systems.attribute_system.get_attack(context, context.units["a2"]) == 160
            assert context.units["a2"].attack == 120  # raw data intact
    settle(context, systems, expiry)
    assert systems.state_modifier_support.activation_rate(context, probe(kind)) == .35
    if troop is TroopType.BOW:
        assert systems.action_order_system.determine_order(context)[0].team_id == "b"
    else:
        assert systems.attribute_system.get_attack(context, context.units["a2"]) == 160


@pytest.mark.parametrize("factory,troop,special,expiry,kind", CASES)
def test_resolver_consumes_type_specific_rate_once(factory, troop, special, expiry, kind):
    context, systems, runtime = setup(factory, troop)
    admit_and_install_troop_skill(context, systems, runtime)
    context.current_round = 1
    candidate = probe(kind)
    context.skill_runtimes.register(candidate)
    assert systems.skill_resolver.resolve(context, candidate).status is SkillResolutionStatus.RESOLVED
    assert context.random.probabilities == pytest.approx([.45])
    assert candidate.definition.activation_rate == .35
    settle(context, systems, expiry)
    systems.skill_resolver.resolve(context, candidate)
    assert context.random.probabilities == pytest.approx([.45, .35])


@pytest.mark.parametrize("factory,troop,special,expiry,kind", CASES)
def test_intimidation_suppression_restore_and_clock(factory, troop, special, expiry, kind):
    context, systems, runtime = setup(factory, troop)
    admit_and_install_troop_skill(context, systems, runtime)
    systems.state_application_coordinator.apply_candidate(context, StateCandidate(
        state_id=OfficialStateId.INTIMIDATION.value, owner_id="a1", source_id="b1",
        source_skill_id="690222", lifetime_spec=StateLifetimeSpec.round_calendar(expires_round=2),
        runtime_params_candidate=EmptyStateRuntimeParams(),
    ))
    assert systems.state_modifier_support.activation_rate(context, probe(kind)) == .35
    assert context.units["a2"].special_troop_id.value == special
    if troop is TroopType.BOW:
        assert systems.action_order_system.determine_order(context)[0].team_id == "b"
    else:
        assert systems.attribute_system.get_attack(context, context.units["a2"]) == 120
    settle(context, systems, 2, BattlePhase.ROUND_END.value)
    assert systems.state_modifier_support.activation_rate(context, probe(kind)) == pytest.approx(.45)
    settle(context, systems, expiry)
    assert systems.state_modifier_support.activation_rate(context, probe(kind)) == .35


@pytest.mark.parametrize("factory,troop,special,expiry,kind", CASES)
def test_provider_death_preserves_mounted_ally_effects(factory, troop, special, expiry, kind):
    context, systems, runtime = setup(factory, troop)
    admit_and_install_troop_skill(context, systems, runtime)
    context.units["a1"].troops = 0
    assert systems.state_modifier_support.activation_rate(context, probe(kind)) == pytest.approx(.45)
    if troop is TroopType.CAVALRY:
        assert systems.attribute_system.get_attack(context, context.units["a2"]) == 160
    settle(context, systems, expiry)
    assert systems.state_modifier_support.activation_rate(context, probe(kind)) == .35


@pytest.mark.parametrize("factory,troop,special,expiry,kind", CASES)
@pytest.mark.parametrize("failure", ["disabled", "phase", "wrong_troop", "mixed_team"])
def test_admission_rejects_without_mutation(factory, troop, special, expiry, kind, failure):
    context, systems, runtime = setup(factory, troop)
    expected = {
        "disabled": TroopAdmissionStatus.REJECTED_BASELINE_DISABLED,
        "phase": TroopAdmissionStatus.REJECTED_PHASE_ILLEGAL,
        "wrong_troop": TroopAdmissionStatus.REJECTED_INVALID_TROOP,
        "mixed_team": TroopAdmissionStatus.REJECTED_TEAM_INVARIANT_VIOLATION,
    }[failure]
    if failure == "disabled": runtime.enabled = False
    if failure == "phase": context.current_phase = BattlePhase.UNIT_ACTION.value
    if failure == "wrong_troop": context.units["a1"].troop_type = TroopType.SHIELD
    if failure == "mixed_team": context.units["a3"].troop_type = TroopType.SHIELD
    assert admit_and_install_troop_skill(context, systems, runtime).status is expected
    assert not context.states.find()
    assert all(u.special_troop_id is None for u in context.units.values())


@pytest.mark.parametrize("factory,troop,special,expiry,kind", CASES)
def test_repeat_install_and_canonical_definition(factory, troop, special, expiry, kind):
    context, systems, runtime = setup(factory, troop)
    runtime.definition = replace(runtime.definition, effect_specs=(ApplyStateSkillEffectSpec(OfficialStateId.STUN.value),))
    assert admit_and_install_troop_skill(context, systems, runtime).status is TroopAdmissionStatus.SUCCESS
    assert not context.states.find(state_id=OfficialStateId.STUN.value)
    count = len(context.states.find())
    assert admit_and_install_troop_skill(context, systems, factory("a3")).status is TroopAdmissionStatus.REJECTED_ALREADY_INSTALLED
    assert len(context.states.find()) == count


def test_conflicting_cavalry_skills_rejected_atomically():
    context, systems, runtime = setup(create_hu_bao_qi_runtime, TroopType.CAVALRY)
    admit_and_install_troop_skill(context, systems, runtime)
    before = tuple(context.states.find())
    result = admit_and_install_troop_skill(context, systems, create_xiliang_cavalry_runtime("a3"))
    assert result.status is TroopAdmissionStatus.REJECTED_CONFLICTING_SPECIAL_TROOP
    assert tuple(context.states.find()) == before


@pytest.mark.parametrize("factory,troop,special,expiry,kind", CASES)
def test_automatic_engine_install_expiry_and_finalization(factory, troop, special, expiry, kind):
    context, systems, runtime = setup(factory, troop)
    context.skill_runtimes.register(runtime)
    BattleEngine(context, systems=systems).run()
    assert all(context.units[u].special_troop_id.value == special for u in ("a1", "a2", "a3"))
    assert not context.states.find()
    assert systems.state_modifier_support.activation_rate(context, probe(kind)) == .35
    assert systems.attribute_system.get_attack(context, context.units["a2"]) == 120


def test_modifier_extension_preserves_existing_attribute_provider():
    class Existing:
        def modify_attribute(self, *, base_value, attribute, **kwargs):
            return base_value + (7 if attribute == "attack" else 0)
    systems = BattleSystems(attribute_system=AttributeSystem(Existing()))
    context, systems, runtime = setup(create_hu_bao_qi_runtime, TroopType.CAVALRY, systems=systems)
    admit_and_install_troop_skill(context, systems, runtime)
    assert systems.attribute_system.get_attack(context, context.units["a2"]) == 167


@pytest.mark.parametrize("base,bonus,expected", [(0, .1, .1), (.95, .1, 1), (.05, -.1, 0)])
def test_generic_additive_probability_clamping(base, bonus, expected):
    context, systems, _ = setup(create_hu_bao_qi_runtime, TroopType.CAVALRY)
    register_modifier_state_definitions(context.states)
    systems.state_application_coordinator.apply_candidate(context, StateCandidate(
        state_id=ACTIVATION_RATE_BONUS_STATE_ID, owner_id="a2",
        runtime_params_candidate=ActivationRateBonusParams(SkillType.ACTIVE, bonus),
    ))
    assert systems.state_modifier_support.activation_rate(context, probe(SkillType.ACTIVE, base)) == expected


@pytest.mark.parametrize("value", [True, float("nan"), float("inf")])
def test_modifier_params_reject_invalid_numbers(value):
    with pytest.raises((TypeError, ValueError)):
        AttributeBonusParams("attack", value)
    with pytest.raises((TypeError, ValueError)):
        ActivationRateBonusParams(SkillType.ACTIVE, value)


def test_user_deferred_fields_remain_blank():
    from sgs_v2.battle_core.troop_skills import bai_ma_yi_cong, hu_bao_qi
    assert bai_ma_yi_cong.COMMANDER_SCALING is None
    assert bai_ma_yi_cong.COMMANDER_DURATION is None
    assert hu_bao_qi.COMMANDER_SCALING is None


@pytest.mark.parametrize("factory,troop,special,expiry,kind", CASES)
def test_no_catch_up_when_suppression_outlasts_bonus(factory, troop, special, expiry, kind):
    context, systems, runtime = setup(factory, troop)
    admit_and_install_troop_skill(context, systems, runtime)
    systems.state_application_coordinator.apply_candidate(context, StateCandidate(
        state_id=OfficialStateId.INTIMIDATION.value, owner_id="a1", source_id="b1",
        source_skill_id="690222", lifetime_spec=StateLifetimeSpec.round_calendar(expires_round=5),
        runtime_params_candidate=EmptyStateRuntimeParams(),
    ))
    settle(context, systems, expiry)
    assert not context.states.find(state_id=ACTIVATION_RATE_BONUS_STATE_ID)
    settle(context, systems, 5, BattlePhase.ROUND_END.value)
    assert systems.state_modifier_support.activation_rate(context, probe(kind)) == .35
    if troop is TroopType.CAVALRY:
        assert systems.attribute_system.get_attack(context, context.units["a2"]) == 160
    else:
        assert not context.states.find(state_id=OfficialStateId.FIRST_STRIKE.value)


@pytest.mark.parametrize("factory,troop,special,expiry,kind", CASES)
def test_false_report_does_not_suppress_troop_provider(factory, troop, special, expiry, kind):
    context, systems, runtime = setup(factory, troop)
    admit_and_install_troop_skill(context, systems, runtime)
    systems.state_application_coordinator.apply_candidate(context, StateCandidate(
        state_id=OfficialStateId.FALSE_REPORT.value, owner_id="a1", source_id="b1",
        source_skill_id="690107", lifetime_spec=StateLifetimeSpec.round_calendar(expires_round=2),
        runtime_params_candidate=EmptyStateRuntimeParams(),
    ))
    assert systems.state_modifier_support.activation_rate(context, probe(kind)) == pytest.approx(.45)


@pytest.mark.parametrize("factory,troop,special,expiry,kind", CASES)
def test_provider_slot_collision_rejected_before_identity_change(factory, troop, special, expiry, kind):
    context, systems, runtime = setup(factory, troop)
    unrelated = probe(SkillType.ACTIVE)
    unrelated.owner_id = "a1"
    unrelated.skill_slot = runtime.skill_slot
    context.skill_runtimes.register(unrelated)
    assert admit_and_install_troop_skill(context, systems, runtime).status is TroopAdmissionStatus.REJECTED_PROVIDER_SLOT_CONFLICT
    assert not context.states.find()
    assert all(u.special_troop_id is None for u in context.units.values())


def test_generic_multiple_sources_add_without_mutating_skill():
    context, systems, _ = setup(create_hu_bao_qi_runtime, TroopType.CAVALRY)
    register_modifier_state_definitions(context.states)
    for source, bonus in [("a1", .1), ("a3", .05)]:
        systems.state_application_coordinator.apply_candidate(context, StateCandidate(
            state_id=ACTIVATION_RATE_BONUS_STATE_ID, owner_id="a2", source_id=source,
            runtime_params_candidate=ActivationRateBonusParams(SkillType.ACTIVE, bonus),
        ))
    rt = probe(SkillType.ACTIVE)
    assert systems.state_modifier_support.activation_rate(context, rt) == pytest.approx(.5)
    assert rt.definition.activation_rate == .35


@pytest.mark.parametrize("base,expected,calls", [(0, .1, [.1]), (.95, 1, [])])
def test_zero_and_one_rate_rng_boundary(base, expected, calls):
    context, systems, runtime = setup(create_bai_ma_yi_cong_runtime, TroopType.BOW)
    admit_and_install_troop_skill(context, systems, runtime)
    candidate = probe(SkillType.ACTIVE, base)
    context.skill_runtimes.register(candidate)
    assert systems.skill_resolver.resolve(context, candidate).status is SkillResolutionStatus.RESOLVED
    assert context.random.probabilities == calls


def test_duplicate_modifier_source_is_rejected():
    context, systems, _ = setup(create_hu_bao_qi_runtime, TroopType.CAVALRY)
    register_modifier_state_definitions(context.states)
    candidate = StateCandidate(state_id=ATTRIBUTE_BONUS_STATE_ID, owner_id="a2", source_id="a1",
                               runtime_params_candidate=AttributeBonusParams("attack", 40))
    assert systems.state_application_coordinator.apply_candidate(context, candidate).committed
    assert not systems.state_application_coordinator.apply_candidate(context, candidate).committed
    assert systems.attribute_system.get_attack(context, context.units["a2"]) == 160
