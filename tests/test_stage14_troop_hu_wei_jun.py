from fractions import Fraction
import pytest

from test_stage14_troop_batch01 import setup
from sgs_v2.battle_core import (BattlePhase, EventType, TroopType, TroopAdmissionStatus,
    OfficialStateId, StateCandidate, StateLifetimeSpec, admit_and_install_troop_skill,
    create_hu_wei_jun_runtime, SkillSlot)
from sgs_v2.battle_core.pre_attack_reaction import (
    loss_rate_bonus, PRE_ATTACK_REACTION_STATE_ID, TeamPreAttackReactionParams)
from sgs_v2.battle_core.state_runtime_params import EmptyStateRuntimeParams
from sgs_v2.battle_core.troop_admission import TROOP_SKILL_REGISTRY
from sgs_v2.battle_core.troop_skills.hu_wei_jun import SKILL, CONFIG


def fixture(holder="a1", name=None):
    c, s, _ = setup(create_hu_wei_jun_runtime, TroopType.SHIELD)
    if name:
        c.units["a1"].name = name
    rt = create_hu_wei_jun_runtime(holder)
    assert admit_and_install_troop_skill(c, s, rt).status is TroopAdmissionStatus.SUCCESS
    c.current_round = 1
    c.current_phase = BattlePhase.UNIT_ACTION.value
    s.target_system.random_enemy = lambda context, attacker: c.units["a1"]
    return c, s, rt


def counters(c):
    return [e for e in c.event_bus.history if e.event_type is EventType.COUNTER_EXECUTE
        and e.payload.get("source_skill_id") == "20154"]


@pytest.mark.parametrize("loss,expected", [(0, 0), (249, 0), (250, 1), (499, 1),
    (500, 2), (9749, 38), (9750, 39), (9999, 39), (10000, 40)])
def test_loss_rate_points_and_cap(loss, expected):
    assert loss_rate_bonus(10000, 10000-loss) == Fraction(expected, 100)
    assert Fraction(72, 100) + loss_rate_bonus(10000, 10000-loss) <= Fraction(112, 100)
    assert loss_rate_bonus(20000, 5000) == Fraction(40, 100)


def test_invalid_parameters_and_no_bonus_above_entry():
    assert loss_rate_bonus(8000, 9000) == 0
    with pytest.raises(TypeError):
        loss_rate_bonus(True, 100)
    with pytest.raises(ValueError):
        TeamPreAttackReactionParams(loss_step=0)


def test_registry_admission_provenance_and_duplicate_guard():
    c, s, rt = fixture("a2")
    assert TROOP_SKILL_REGISTRY["20154"] is CONFIG
    assert rt.definition is SKILL
    assert all(c.units[x].special_troop_id.value == "HU_WEI_JUN" for x in ("a1", "a2", "a3"))
    markers = c.states.find(state_id=PRE_ATTACK_REACTION_STATE_ID)
    assert len(markers) == 1 and markers[0].owner_id == "a1"
    assert markers[0].source_id == "a2" and markers[0].source_skill_slot is SkillSlot.LEARNED_1
    c.current_phase = BattlePhase.PRE_BATTLE.value
    assert admit_and_install_troop_skill(c, s, rt).status is TroopAdmissionStatus.REJECTED_ALREADY_INSTALLED


def test_before_hit_order_performer_and_round_budget():
    c, s, rt = fixture()
    result = s.normal_attack_system.execute(c, c.units["b2"])
    assert result.actual_target_id == "a1"
    events = counters(c)
    assert [e.actor_id for e in events] == ["a2", "a3"]
    assert all(e.target_id == "b2" for e in events)
    normal = next(e for e in c.event_bus.history if e.event_type is EventType.NORMAL_ATTACK)
    history = list(c.event_bus.history)
    assert all(history.index(e) < history.index(normal) for e in events)
    assert s.attribute_system.get_attack(c, c.units["a2"]) == 132
    assert c.units["a2"].attack == 120
    damage = [e for e in history if e.event_type is EventType.DAMAGE_DEALT
        and e.payload.get("source_skill_id") == "20154"]
    assert len(damage) == 2 and all(e.payload["source_type"] == "COUNTER" for e in damage)
    s.normal_attack_system.execute(c, c.units["b3"])
    assert len(counters(c)) == 2
    c.current_round = 2
    s.normal_attack_system.execute(c, c.units["b3"])
    assert len(counters(c)) == 4
    assert s.attribute_system.get_attack(c, c.units["a3"]) == 144


def test_five_stack_cap_damage_continues():
    c, s, rt = fixture()
    for round_no in range(1, 8):
        c.current_round = round_no
        s.normal_attack_system.execute(c, c.units["b2"])
    assert len(counters(c)) == 14
    assert s.attribute_system.get_attack(c, c.units["a2"]) == 180
    assert s.attribute_system.get_attack(c, c.units["a3"]) == 180


def test_individual_entry_loss_and_healing_reduces_bonus():
    c, s, rt = fixture()
    c.units["a2"].troops = 9200
    c.units["a3"].troops = 2000
    s.normal_attack_system.execute(c, c.units["b2"])
    assert [e.payload["coefficient"] for e in counters(c)] == [.75, 1.04]
    c.units["a2"].troops = 9800
    c.current_round = 2
    s.normal_attack_system.execute(c, c.units["b2"])
    assert counters(c)[2].payload["coefficient"] == .72


def test_deputy_target_does_not_trigger_or_consume_budget():
    c, s, rt = fixture()
    s.target_system.random_enemy = lambda context, attacker: c.units["a2"]
    s.normal_attack_system.execute(c, c.units["b2"])
    assert not counters(c)
    s.target_system.random_enemy = lambda context, attacker: c.units["a1"]
    s.normal_attack_system.execute(c, c.units["b2"])
    assert len(counters(c)) == 2


def test_dead_deputy_skipped_and_attacker_killed_cancels_normal_hit():
    c, s, rt = fixture()
    c.units["b2"].troops = 1
    before = c.units["a1"].troops
    result = s.normal_attack_system.execute(c, c.units["b2"])
    assert c.units["b2"].troops == 0 and result.damage is None
    assert c.units["a1"].troops == before
    assert len(counters(c)) == 2
    assert any(e.event_type is EventType.COUNTER_ZERO_LOSS for e in c.event_bus.history)
    assert not any(e.event_type is EventType.NORMAL_ATTACK for e in c.event_bus.history)
    c, s, rt = fixture()
    c.units["a2"].troops = 0
    s.normal_attack_system.execute(c, c.units["b2"])
    assert [e.actor_id for e in counters(c)] == ["a3"]


def test_provider_disabled_and_death_block_reaction():
    c, s, rt = fixture("a2")
    rt.enabled = False
    s.normal_attack_system.execute(c, c.units["b2"])
    assert not counters(c)
    rt.enabled = True
    c.units["a2"].troops = 0
    s.normal_attack_system.execute(c, c.units["b2"])
    assert not counters(c)


def test_provider_intimidation_suppresses_and_resumes():
    c, s, rt = fixture("a2")
    applied = s.state_application_coordinator.apply_candidate(c, StateCandidate(
        state_id=OfficialStateId.INTIMIDATION.value, owner_id="a2", source_id="b1",
        source_skill_id="blocker", lifetime_spec=StateLifetimeSpec.round_calendar(expires_round=2),
        runtime_params_candidate=EmptyStateRuntimeParams()))
    s.normal_attack_system.execute(c, c.units["b2"])
    assert not counters(c)
    from sgs_v2.battle_core import StateNode
    roots = (StateNode(applied.instance.instance_id),)
    before = s.effectiveness_transition_coordinator.capture(c, roots)
    s.state_lifecycle_system.remove(c, applied.instance.instance_id)
    s.effectiveness_transition_coordinator.complete_removed_nodes(c, before, roots)
    s.normal_attack_system.execute(c, c.units["b2"])
    assert len(counters(c)) == 2


@pytest.mark.parametrize("name,bonus", [("典韦", 25), ("许褚", 25), ("曹操", 0)])
def test_catalog_commander_bonus(name, bonus):
    c, s, rt = fixture("a2", name)
    assert s.attribute_system.get_defense(c, c.units["a1"]) == 120 + bonus
    assert s.attribute_system.get_defense(c, c.units["a2"]) == 120


def test_wrong_troop_rejected_without_identity_mutation():
    c, s, rt = setup(create_hu_wei_jun_runtime, TroopType.SPEAR)
    assert admit_and_install_troop_skill(c, s, rt).status is TroopAdmissionStatus.REJECTED_INVALID_TROOP
    assert all(u.special_troop_id is None for u in c.units.values())
