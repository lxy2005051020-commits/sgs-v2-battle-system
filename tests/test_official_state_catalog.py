from __future__ import annotations

from collections import Counter

from sgs_v2.battle_core import (
    OFFICIAL_STATE_CATALOG,
    OfficialStateCategory,
    OfficialStateId,
    StateRegistry,
    register_official_state_definitions,
)


EXPECTED_HINT_IDS = {
    "burn": 690072,
    "flood": 690073,
    "poison": 690074,
    "rout": 690075,
    "sandstorm": 690076,
    "rebellion": 690077,
    "first_aid": 690078,
    "recuperation": 690079,
    "combo": 690081,
    "evasion": 690082,
    "barrier": 690083,
    "cleave": 690084,
    "counterattack": 690085,
    "damage_split": 690086,
    "damage_share": 690087,
    "insight": 690089,
    "first_strike": 690090,
    "ambush": 690091,
    "sure_hit": 690092,
    "defense_pierce": 690093,
    "weapon_lifesteal": 690094,
    "strategy_lifesteal": 690095,
    "chain_link": 690097,
    "guard": 690098,
    "vigilance": 690099,
    "silence": 690101,
    "disarm": 690102,
    "confusion": 690103,
    "weakness": 690104,
    "healing_ban": 690105,
    "taunt": 690106,
    "false_report": 690107,
    "provoke": 690108,
    "equipment_disable": 690109,
    "capture": 690110,
    "stun": 690111,
    "critical": 690070,
    "strategy_critical": 690069,
    "damage_reduction_pierce": 690221,
    "intimidation": 690222,
}


def test_official_catalog_has_exactly_40_concrete_states_and_expected_categories() -> None:
    assert len(OFFICIAL_STATE_CATALOG) == 40
    counts = Counter(entry.category for entry in OFFICIAL_STATE_CATALOG)
    assert counts == {
        OfficialStateCategory.CONTINUOUS: 8,
        OfficialStateCategory.FUNCTIONAL: 17,
        OfficialStateCategory.CONTROL: 11,
        OfficialStateCategory.OTHER: 4,
    }


def test_official_catalog_identifiers_hint_ids_and_names_are_unique() -> None:
    state_ids = [entry.state_id.value for entry in OFFICIAL_STATE_CATALOG]
    hint_ids = [entry.hint_id for entry in OFFICIAL_STATE_CATALOG]
    names = [entry.name for entry in OFFICIAL_STATE_CATALOG]

    assert len(state_ids) == len(set(state_ids)) == 40
    assert len(hint_ids) == len(set(hint_ids)) == 40
    assert len(names) == len(set(names)) == 40


def test_all_40_hint_ids_match_official_v1_catalog() -> None:
    actual = {
        entry.state_id.value: entry.hint_id
        for entry in OFFICIAL_STATE_CATALOG
    }
    assert actual == EXPECTED_HINT_IDS


def test_required_representative_hint_ids_are_fixed() -> None:
    by_id = {entry.state_id: entry for entry in OFFICIAL_STATE_CATALOG}
    assert by_id[OfficialStateId.FIRST_STRIKE].hint_id == 690090
    assert by_id[OfficialStateId.AMBUSH].hint_id == 690091
    assert by_id[OfficialStateId.DISARM].hint_id == 690102
    assert by_id[OfficialStateId.WEAKNESS].hint_id == 690104
    assert by_id[OfficialStateId.STUN].hint_id == 690111


def test_ambush_official_text_is_preserved_without_correcting_suspected_typo() -> None:
    ambush = next(
        entry for entry in OFFICIAL_STATE_CATALOG
        if entry.state_id is OfficialStateId.AMBUSH
    )
    assert ambush.official_text == (
        "功能性减益状态，让武将在回合内延后行动，"
        "多名武将同时拥有先攻状态时则根据速度高低决定行动顺序"
    )


def test_non_concrete_official_terms_are_not_catalog_entries() -> None:
    forbidden = {
        "功能性状态",
        "功能状态",
        "控制状态",
        "战斗属性",
        "会心伤害",
        "奇谋伤害",
    }
    assert forbidden.isdisjoint({entry.name for entry in OFFICIAL_STATE_CATALOG})


def test_official_catalog_registers_minimal_stage3_definitions_explicitly() -> None:
    registry = StateRegistry()
    register_official_state_definitions(registry)

    for entry in OFFICIAL_STATE_CATALOG:
        definition = registry.get_definition(entry.state_id.value)
        assert definition.state_id == entry.state_id.value
        assert definition.name == entry.name
        assert definition.tags == frozenset({entry.category.value})
