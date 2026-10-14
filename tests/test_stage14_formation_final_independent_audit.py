"""Independent Stage14 nine-formation acceptance/falsification suite.

Runs on canonical production objects. Deliberately does NOT borrow any
formation-specific fixture; all 36 same-team conflicts and 81 opposing-team
configurations are enumerated from a pinned nine-formation inventory.

Evidence of runtime compatibility is not evidence of client gameplay truth.
"""
from __future__ import annotations

from itertools import combinations, product

import pytest

from sgs_v2.battle_core import (
    BattleContext,
    BattlePhase,
    BattleSystems,
    EventBus,
    LineupPosition,
    RandomSystem,
    SkillRuntime,
    SkillSlot,
    SkillType,
    TroopType,
    UnitRuntime,
    register_pre_battle_passive_processor,
    unregister_pre_battle_passive_processor,
    run_pre_battle_preparation_phases,
)
from sgs_v2.battle_core.formation_admission import (
    FORMATION_SKILL_REGISTRY,
    FormationAdmissionRejectedError,
    FormationAdmissionStatus,
    validate_team_formation_limits,
)
from sgs_v2.battle_core.official_state_catalog import register_official_state_definitions
from sgs_v2.battle_core.state_modifiers import register_modifier_state_definitions

# Current 2026-08-08 static-export-derived Runtime IDs, NOT legacy Research
# catalog identifiers. Deliberately pin both identity and Chinese name.
CURRENT_FORMATIONS = {
    "20066": "锋矢阵",
    "20025": "八门金锁阵",
    "20178": "箕形阵",
    "22012": "三势阵",
    "22031": "武锋阵",
    "22039": "形一阵",
    "22040": "潜龙阵",
    "20836": "鱼鳞阵",
    "20862": "雁行阵",
}
IDS = tuple(CURRENT_FORMATIONS)


def _scene(seed=20261014):
    positions = tuple(LineupPosition)
    units = {}
    for team in ("A", "B"):
        for i, pos in enumerate(positions):
            unit_id = f"{team}{i}"
            units[unit_id] = UnitRuntime(
                unit_id=unit_id, name=unit_id, team_id=team,
                max_troops=10000, troops=8500,
                attack=220, defense=200, intelligence=250,
                speed=180 - i * 3 - (0 if team == "A" else 8),
                lineup_position=pos, troop_type=TroopType.SHIELD,
                faction=("WEI", "SHU", "WU")[i],
                troop_aptitude=("S", "A", "B")[i],
            )
    context = BattleContext(
        battle_id=f"formation_audit_{seed}",
        units=units, event_bus=EventBus(), random=RandomSystem(seed),
    )
    context.metadata["attacker_team_id"] = "B"
    context.current_phase = BattlePhase.PRE_BATTLE.value
    register_official_state_definitions(context.states)
    register_modifier_state_definitions(context.states)
    return context, BattleSystems()


def _equip(context, skill_id, owner_id):
    definition = FORMATION_SKILL_REGISTRY[skill_id].definition_factory()
    runtime = SkillRuntime(definition, owner_id, SkillSlot.LEARNED_1)
    context.skill_runtimes.register(runtime)
    return runtime


def test_independent_nine_skill_registry_snapshot_and_unique_names():
    assert set(FORMATION_SKILL_REGISTRY) == set(CURRENT_FORMATIONS)
    assert len(set(CURRENT_FORMATIONS.values())) == 9
    assert len(set(FORMATION_SKILL_REGISTRY)) == 9


@pytest.mark.parametrize("skill_id,name", tuple(CURRENT_FORMATIONS.items()))
def test_each_registered_formation_has_canonical_definition_and_installer(skill_id, name):
    config = FORMATION_SKILL_REGISTRY[skill_id]
    actual = config.definition_factory()
    assert config.skill_id == actual.skill_id == skill_id
    assert config.name == actual.name == name
    assert actual.skill_type is SkillType.FORMATION
    assert actual.activation_rate == 1.0
    assert callable(config.installer)
    assert config.requires_provider_slot


@pytest.mark.parametrize("first_id,second_id", tuple(combinations(IDS, 2)))
def test_every_same_team_pair_fails_before_any_passive_effect_or_rng(first_id, second_id):
    context, systems = _scene()
    _equip(context, first_id, "A0")
    _equip(context, second_id, "A1")
    called = []

    def observation(c, s):
        called.append("passive_ran")
        c.random.random()

    register_pre_battle_passive_processor(observation)
    before_rng = context.random._rng.getstate()
    try:
        with pytest.raises(FormationAdmissionRejectedError) as excinfo:
            run_pre_battle_preparation_phases(context, systems)
    finally:
        unregister_pre_battle_passive_processor(observation)

    assert excinfo.value.status is FormationAdmissionStatus.REJECTED_TEAM_FORMATION_EXCEEDED
    assert not called
    assert context.random._rng.getstate() == before_rng
    assert not context.states.find()
    assert not context.metadata.get("_stage14_installed_formation_keys")
    assert len(context.skill_runtimes) == 2


@pytest.mark.parametrize("a_skill,b_skill", tuple(product(IDS, IDS)))
def test_every_cross_team_pair_is_exclusivity_legal(a_skill, b_skill):
    """Only checks *team formation limit*, NOT per-skill eligibility/effects."""
    context, systems = _scene()
    _equip(context, a_skill, "A1")
    _equip(context, b_skill, "B2")
    assert validate_team_formation_limits(context) is None
    assert len(context.skill_runtimes) == 2
    assert not context.states.find()


def test_no_formation_equipped_preserves_rng_and_no_installation():
    context, systems = _scene()
    before_rng = context.random._rng.getstate()
    run_pre_battle_preparation_phases(context, systems)
    assert not context.states.find()
    assert context.random._rng.getstate() == before_rng
    assert not context.metadata.get("_stage14_installed_formation_keys")


def test_opposing_real_feng_shi_and_ba_men_install_and_defeat_are_source_isolated():
    """Two actual production installers, full preparation scheduler and death port."""
    context, systems = _scene()
    feng = _equip(context, "20066", "A0")
    ba_men = _equip(context, "20025", "B1")
    run_pre_battle_preparation_phases(context, systems)

    states = context.states.find()
    feng_states = [s for s in states if s.source_skill_id == "20066"]
    ba_men_states = [s for s in states if s.source_skill_id == "20025"]
    assert len(feng_states) == 3
    assert len(ba_men_states) == 3
    assert {s.source_id for s in feng_states} == {"A0"}
    assert {s.source_id for s in ba_men_states} == {"B1"}
    assert len(context.metadata["_stage14_installed_formation_keys"]) == 2

    context.units["A0"].troops = 0
    systems.defeat_cleanup_port.commit_defeat(context, "A0")
    # Ba Men may lose a state held on the *dead target* A0 (normal owner-death
    # semantics), but its independent B0 FIRST_STRIKE must not be source-cleaned.
    remaining = context.states.find()
    assert not any(s.source_skill_id == "20066" for s in remaining)
    assert any(s.source_skill_id == "20025" and s.owner_id == "B0" for s in remaining)
    assert context.skill_runtimes.get(feng.owner_id, feng.skill_slot) is feng
    assert context.skill_runtimes.get(ba_men.owner_id, ba_men.skill_slot) is ba_men
