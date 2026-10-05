from dataclasses import replace

import pytest

from tests.test_stage14_troop_batch01 import setup
from sgs_v2.battle_core import (BattlePhase, DamageType, EventType, OfficialStateId,
    TroopType, TroopAdmissionStatus, admit_and_install_troop_skill, create_xie_fan_wei_runtime)
from sgs_v2.battle_core.attribute_choice import higher_force_intelligence
from sgs_v2.battle_core.additive_damage import AdditiveDamageRequest as DamageRequest
from sgs_v2.battle_core.effects import DamageEffect
from sgs_v2.battle_core.enums import DamageSourceType
from sgs_v2.battle_core.normal_attack_followup import NORMAL_ATTACK_FOLLOWUP_STATE_ID
from sgs_v2.battle_core.state_modifiers import ATTRIBUTE_BONUS_STATE_ID, AttributeBonusParams


def fixture(*, success=True, force=400, intelligence=100, speeds=None):
    c, s, rt = setup(create_xie_fan_wei_runtime, TroopType.SPEAR)
    for u in c.units.values():
        u.intelligence = 100
    c.units['a1'].attack, c.units['a1'].intelligence = 200, 500
    c.units['a2'].speed = 100
    for uid, speed in (speeds or {}).items():
        c.units[uid].speed = speed
    c.units['a2'].attack, c.units['a2'].intelligence = force, intelligence
    c.random.chance = lambda p: c.random.probabilities.append(p) or success
    assert admit_and_install_troop_skill(c, s, rt).status is TroopAdmissionStatus.SUCCESS
    c.current_round, c.current_phase = 1, BattlePhase.UNIT_ACTION.value
    return c, s, rt


def attack(c, s, uid='a2'):
    return s.normal_attack_system.execute(c, c.units[uid])


def damage_events(c):
    return [e for e in c.event_bus.history if e.event_type is EventType.DAMAGE_DEALT
            and e.payload.get('source_skill_id') == '20248']


def test_admission_speed_bonus_provider_and_registry():
    from sgs_v2.battle_core.troop_admission import TROOP_SKILL_REGISTRY
    from sgs_v2.battle_core.troop_skills.xie_fan_wei import SKILL
    c, s, rt = fixture()
    assert TROOP_SKILL_REGISTRY['20248'].definition_factory() == SKILL
    for uid, speed in [('a1', 46), ('a2', 136), ('a3', 46)]:
        assert c.units[uid].special_troop_id.value == 'XIE_FAN_WEI'
        assert s.attribute_system.get_speed(c, c.units[uid]) == speed
        state = c.states.find(owner_id=uid, state_id=NORMAL_ATTACK_FOLLOWUP_STATE_ID)[0]
        assert state.source_id == 'a1' and state.source_skill_slot == rt.skill_slot
        assert state.runtime_params.live_recovery_attribute
        assert state.runtime_params.recovery_potency.source_troops_at_application == 10000
        assert state.runtime_params.recovery_potency.source_attribute_at_application is None
    assert not c.random.probabilities
    assert not c.states.find(owner_id='b1')


@pytest.mark.parametrize('force,intelligence,kind', [(400, 100, DamageType.WEAPON), (100, 400, DamageType.STRATEGY)])
def test_real_hit_selects_formula_and_adds_speed_once(force, intelligence, kind):
    c, s, _ = fixture(force=force, intelligence=intelligence)
    attack(c, s)
    assert c.random.probabilities == [.3]
    events = damage_events(c)
    assert len(events) == 1
    event = events[0]
    assert event.actor_id == 'a2'
    assert event.payload['damage_type'] == kind.value
    assert event.payload['scaled_damage'] == pytest.approx(event.payload['base_damage'] * .36 + 136 * .4)
    assert not any(e.event_type is EventType.TROOPS_RECOVERED for e in c.event_bus.history)


def test_damage_branch_uses_live_final_attributes():
    c, s, _ = fixture()
    s.state_lifecycle_system.apply(c, state_id=ATTRIBUTE_BONUS_STATE_ID, owner_id='a2',
        source_id='a2', runtime_params=AttributeBonusParams('intelligence', 500))
    attack(c, s)
    assert damage_events(c)[0].payload['damage_type'] == 'STRATEGY'


def test_performer_is_fixed_before_battle_despite_later_speed_changes():
    c, s, _ = fixture()
    attack(c, s, 'a3')
    assert not c.random.probabilities and not damage_events(c)
    s.state_lifecycle_system.apply(c, state_id=ATTRIBUTE_BONUS_STATE_ID, owner_id='a3',
        source_id='a3', runtime_params=AttributeBonusParams('speed', 200))
    attack(c, s, 'a2')
    assert c.random.probabilities == [.3]
    assert damage_events(c)[0].actor_id == 'a2'
    attack(c, s, 'a3')
    assert c.random.probabilities == [.3]
    assert len(damage_events(c)) == 1


@pytest.mark.parametrize('force,intelligence', [(500, 200), (200, 500), (500, 500)])
def test_healing_uses_live_performer_attribute_and_opening_troops(force, intelligence):
    c, s, rt = setup(create_xie_fan_wei_runtime, TroopType.SPEAR)
    for u in c.units.values():
        u.intelligence = 100
    c.units['a1'].attack, c.units['a1'].intelligence = 1, 2
    c.units['a2'].attack, c.units['a2'].intelligence = 1, 2
    c.units['a2'].speed = 100
    assert admit_and_install_troop_skill(c, s, rt).status is TroopAdmissionStatus.SUCCESS
    expected = s.treatment_formula_system.calculate(rate=.72, source_troops=10000, source_attribute=500).nominal_recovery
    for u in s.target_system.allies(c, c.units['a1']):
        u.troops, u.wounded_troops = 5000, 5000
    c.units['a2'].attack, c.units['a2'].intelligence = force, intelligence
    c.random.chance = lambda p: c.random.probabilities.append(p) or False
    selections = []
    def sample(items, count):
        selections.append((tuple(u.unit_id for u in items), count))
        return [c.units['a1']]
    c.random.sample = sample
    c.current_round, c.current_phase = 1, BattlePhase.UNIT_ACTION.value
    attack(c, s)
    assert selections == [(('a1', 'a2', 'a3'), 1)]
    assert c.units['a1'].troops == 5000 + expected
    assert c.units['a2'].troops == c.units['a3'].troops == 5000
    assert c.random.probabilities == [.3] and not damage_events(c)
    healing = [e for e in c.event_bus.history if e.event_type is EventType.TROOPS_RECOVERED]
    assert healing[0].actor_id == 'a2'


@pytest.mark.parametrize('success', [True, False])
def test_disabled_provider_suppresses_both_branches_without_rng(success):
    c, s, rt = fixture(success=success)
    rt.enabled = False
    attack(c, s)
    assert not c.random.probabilities and not damage_events(c)


@pytest.mark.parametrize('speeds,expected', [
    ({'a1': 100, 'a2': 100, 'a3': 100}, 'a1'),
    ({'a1': 10, 'a2': 100, 'a3': 100}, 'a2'),
    ({'a1': 10, 'a2': 20, 'a3': 100}, 'a3'),
])
def test_opening_speed_ties_use_canonical_lineup_order(speeds, expected):
    c, s, _ = fixture(speeds=speeds)
    for uid in ('a1', 'a2', 'a3'):
        attack(c, s, uid)
    assert c.random.probabilities == [.3]
    assert damage_events(c)[0].actor_id == expected


def test_attribute_tie_selects_weapon():
    c, s, _ = fixture(force=400, intelligence=400)
    attack(c, s)
    assert damage_events(c)[0].payload['damage_type'] == 'WEAPON'
    assert higher_force_intelligence(400, 400, tie_type=DamageType.WEAPON).damage_type is DamageType.WEAPON


@pytest.mark.parametrize('value', [-1, float('inf'), float('nan'), True])
def test_additive_damage_validation(value):
    with pytest.raises((ValueError, TypeError)):
        DamageRequest('a1', 'b1', DamageType.WEAPON, DamageSourceType.SKILL, additive_damage=value)


def test_additive_input_roundtrip_and_zero_preserves_old_formula():
    effect = DamageEffect('a1', 'b1', DamageType.WEAPON, DamageSourceType.SKILL, additive_damage=40)
    assert effect.to_request().additive_damage == 40
    c, s, _ = fixture()
    request = effect.to_request()
    result = s.damage_system.calculate(c, request)
    assert result.scaled_damage == pytest.approx(result.base_damage + 40)
    result = s.damage_system.calculate(c, replace(request, additive_damage=0))
    assert result.scaled_damage == result.base_damage


def test_additive_basis_with_zero_coefficient_and_no_leak_to_next_request():
    from sgs_v2.battle_core.damage_system import DamageRequest as PlainRequest
    c, s, _ = fixture()
    added = s.damage_system.calculate(c, DamageRequest('a2', 'b2', DamageType.WEAPON,
        DamageSourceType.SKILL, coefficient=0, additive_damage=57))
    assert added.scaled_damage == 57
    assert type(added.base_damage) is float
    plain = s.damage_system.calculate(c, PlainRequest('a2', 'b2', DamageType.WEAPON,
        DamageSourceType.SKILL))
    assert plain.scaled_damage == plain.base_damage


def test_additive_basis_still_obeys_weakness():
    c, s, _ = fixture()
    s.state_lifecycle_system.apply(c, state_id=OfficialStateId.WEAKNESS.value,
        owner_id='a2', source_id='b1')
    result = s.damage_system.calculate(c, DamageRequest('a2', 'b2', DamageType.WEAPON,
        DamageSourceType.SKILL, additive_damage=1000))
    assert result.final_damage == 0


@pytest.mark.parametrize('case', ['dead_provider', 'intimidation', 'disarm', 'finalization'])
def test_reaction_gates_no_branch_draw(case):
    c, s, _ = fixture()
    if case == 'dead_provider':
        c.units['a1'].troops = 0
    elif case == 'finalization':
        c.units['b1'].troops = 1
        s.target_system.random_enemy = lambda context, attacker: c.units['b1']
    else:
        from sgs_v2.battle_core import StateCandidate, StateLifetimeSpec
        from sgs_v2.battle_core.state_runtime_params import EmptyStateRuntimeParams
        from sgs_v2.battle_core.stage11_state_params import DisarmStateParams
        s.state_application_coordinator.apply_candidate(c, StateCandidate(
            state_id=(OfficialStateId.INTIMIDATION if case == 'intimidation' else OfficialStateId.DISARM).value,
            owner_id='a1' if case == 'intimidation' else 'a2', source_id='b1', source_skill_id='blocker',
            lifetime_spec=StateLifetimeSpec.round_calendar(expires_round=2),
            runtime_params_candidate=EmptyStateRuntimeParams() if case == 'intimidation' else DisarmStateParams()))
    attack(c, s)
    assert not c.random.probabilities and not damage_events(c)


@pytest.mark.parametrize('blocked', [False, True])
def test_random_healing_respects_capacity_and_ban_without_retarget(blocked):
    c, s, _ = fixture(success=False)
    c.units['a3'].troops, c.units['a3'].wounded_troops = 9990, 10
    c.random.sample = lambda candidates, count: [c.units['a3']]
    if blocked:
        s.state_lifecycle_system.apply(c, state_id=OfficialStateId.HEALING_BAN.value,
            owner_id='a3', source_id='b1')
    attack(c, s)
    assert c.units['a3'].troops == (9990 if blocked else 10000)
    assert c.random.probabilities == [.3]
    assert not damage_events(c)


def test_user_authorized_two_stage_healing_integerization_is_421():
    from sgs_v2.battle_core import BattleSystems
    from sgs_v2.battle_core.stage9_integerization import ExactRatio
    s = BattleSystems(recovery_modifier_provider=lambda context, request: ExactRatio(11, 10))
    c, _, rt = setup(create_xie_fan_wei_runtime, TroopType.SPEAR, systems=s)
    for u in c.units.values():
        u.intelligence = 0
    c.units['a2'].attack, c.units['a2'].speed = 1, 100
    assert admit_and_install_troop_skill(c, s, rt).status is TroopAdmissionStatus.SUCCESS
    c.units['a3'].troops, c.units['a3'].wounded_troops = 5000, 5000
    c.random.sample = lambda candidates, count: [c.units['a3']]
    c.random.chance = lambda p: c.random.probabilities.append(p) or False
    c.current_round, c.current_phase = 1, BattlePhase.UNIT_ACTION.value
    attack(c, s)
    assert c.units['a3'].troops == 5421


def test_damage_uses_troop_family_and_can_invoke_see_through():
    from sgs_v2.battle_core.stage11_state_params import DamageReductionPierceStateParams
    from sgs_v2.battle_core.stage11_state_runtime import Stage11DamageFamily
    c, s, _ = fixture()
    s.state_lifecycle_system.apply(c, state_id=OfficialStateId.DAMAGE_REDUCTION_PIERCE.value,
        owner_id='a2', source_id='a2', runtime_params=DamageReductionPierceStateParams(rate=.4))
    seen = []
    original = s.stage11_state_runtime.see_through_rate
    def observe(context, uid, family):
        rate = original(context, uid, family)
        seen.append((uid, family, rate))
        return rate
    s.stage11_state_runtime.see_through_rate = observe
    attack(c, s)
    assert ('a2', Stage11DamageFamily.COMMAND_XIEFANWEI, .4) in seen
    assert len(damage_events(c)) == 1


@pytest.mark.parametrize('kind', ['evasion', 'resistance', 'zero'])
def test_prevented_or_zero_loss_normal_attack_still_triggers(kind):
    from sgs_v2.battle_core.stage11_state_params import EvasionStateParams, ResistanceStateParams
    c, s, _ = fixture()
    s.target_system.random_enemy = lambda context, actor: c.units['b2']
    if kind == 'zero':
        s.state_lifecycle_system.apply(c, state_id=OfficialStateId.WEAKNESS.value,
            owner_id='a2', source_id='b1')
    else:
        s.state_lifecycle_system.apply(c,
            state_id=(OfficialStateId.EVASION if kind == 'evasion' else OfficialStateId.BARRIER).value,
            owner_id='b2', source_id='b2', runtime_params=EvasionStateParams() if kind == 'evasion' else ResistanceStateParams())
    attack(c, s)
    assert .3 in c.random.probabilities
    # Only the probability draw selects healing; prevented damage never falls back.
    assert not any(e.event_type is EventType.TROOPS_RECOVERED for e in c.event_bus.history)


def test_fixed_performer_death_does_not_promote_next_fastest():
    c, s, _ = fixture()
    c.units['a2'].troops = 0
    attack(c, s, 'a3')
    assert not c.random.probabilities and not damage_events(c)


@pytest.mark.parametrize('attribute', ['attack', 'intelligence'])
def test_live_healing_attribute_includes_current_state_modifiers(attribute):
    c, s, _ = fixture(success=False, force=100, intelligence=100)
    c.units['a3'].troops, c.units['a3'].wounded_troops = 5000, 5000
    c.random.sample = lambda candidates, count: [c.units['a3']]
    s.state_lifecycle_system.apply(c, state_id=ATTRIBUTE_BONUS_STATE_ID,
        owner_id='a2', source_id='a2', runtime_params=AttributeBonusParams(attribute, 600))
    expected = s.treatment_formula_system.calculate(rate=.72,
        source_troops=10000, source_attribute=700).nominal_recovery
    attack(c, s)
    assert c.units['a3'].troops == 5000 + expected
