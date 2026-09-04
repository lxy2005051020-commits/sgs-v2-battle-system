from __future__ import annotations

import pytest

from sgs_v2.battle_core import (
    BattleContext,
    BattleSystems,
    DamageRequest,
    DamageSourceType,
    DamageType,
    EventBus,
    LineupPosition,
    RandomSystem,
    TroopType,
    UnitRuntime,
)


def make_context(
    *,
    source_troops: int = 10000,
    source_attack: float = 300,
    target_defense: float = 200,
    source_level: int = 50,
    target_level: int = 50,
    source_morale: int = 100,
    source_troop_type: TroopType | None = None,
    target_troop_type: TroopType | None = None,
    target_troops: int = 10000,
    seed: int = 1,
) -> BattleContext:
    return BattleContext(
        battle_id="weapon-formula",
        units={
            "a": UnitRuntime(
                unit_id="a",
                name="A",
                team_id="A",
                max_troops=max(1, source_troops),
                troops=source_troops,
                attack=source_attack,
                defense=100,
                speed=100,
                lineup_position=LineupPosition.COMMANDER,
                level=source_level,
                morale=source_morale,
                troop_type=source_troop_type,
            ),
            "b": UnitRuntime(
                unit_id="b",
                name="B",
                team_id="B",
                max_troops=max(1, target_troops),
                troops=target_troops,
                attack=100,
                defense=target_defense,
                speed=90,
                lineup_position=LineupPosition.COMMANDER,
                level=target_level,
                troop_type=target_troop_type,
            ),
        },
        event_bus=EventBus(),
        random=RandomSystem(seed),
    )


def calculate_base(context: BattleContext, systems: BattleSystems) -> float:
    return systems.damage_system.calculate(
        context,
        DamageRequest(
            source_id="a",
            target_id="b",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.NORMAL_ATTACK,
        ),
    ).base_damage


def test_weapon_troop_function_uses_full_lookup_table() -> None:
    damage = BattleSystems().damage_system

    assert damage.weapon_troop_function(1) == 2
    assert damage.weapon_troop_function(10) == 2
    assert damage.weapon_troop_function(11) == 3
    assert damage.weapon_troop_function(2000) == 240
    assert damage.weapon_troop_function(2001) == 238
    assert damage.weapon_troop_function(2005) == 238
    assert damage.weapon_troop_function(2006) == 239
    assert damage.weapon_troop_function(4999) == 429
    assert damage.weapon_troop_function(5000) == 429
    assert damage.weapon_troop_function(6000) == 456
    assert damage.weapon_troop_function(7000) == 478
    assert damage.weapon_troop_function(8000) == 497
    assert damage.weapon_troop_function(9000) == 514
    assert damage.weapon_troop_function(10000) == 529


def test_complete_troop_function_table_can_be_injected_for_regression() -> None:
    exact_table = {troops: 999 for troops in range(1, 10001)}
    damage = BattleSystems(weapon_troop_function_table=exact_table).damage_system

    assert damage.weapon_troop_function(1) == 999
    assert damage.weapon_troop_function(2001) == 999
    assert damage.weapon_troop_function(4999) == 999
    assert damage.weapon_troop_function(10000) == 999


def test_weapon_troop_function_rejects_values_outside_full_table() -> None:
    damage = BattleSystems().damage_system

    with pytest.raises(ValueError, match="lookup-table range"):
        damage.weapon_troop_function(0)
    with pytest.raises(ValueError, match="lookup-table range"):
        damage.weapon_troop_function(10001)


def test_weapon_base_damage_matches_formula_with_fixed_random_layers() -> None:
    context = make_context()
    systems = BattleSystems(
        weapon_random_percent_range=(90, 90),
        weapon_low_damage_floor_range=(5, 5),
    )

    # 查表 F(10000)=529; Sa=Sd=1.6; X=529+300*1.6-200*1.6=689.
    # B0=B1=B2=689; ceil(689*90/100)=621.
    assert calculate_base(context, systems) == 621


def test_weapon_base_damage_applies_spear_cavalry_counter_and_morale() -> None:
    context = make_context(
        source_morale=90,
        source_troop_type=TroopType.SPEAR,
        target_troop_type=TroopType.CAVALRY,
    )
    systems = BattleSystems(
        weapon_random_percent_range=(90, 90),
        weapon_low_damage_floor_range=(5, 5),
    )

    # B0=689; spear->cavalry: ceil(689*1.12)=772.
    # morale 90 => 0.93: ceil(772*0.93)=718.
    # R=90: ceil(718*0.9)=647.
    assert calculate_base(context, systems) == 647


def test_weapon_base_damage_applies_cavalry_spear_disadvantage() -> None:
    context = make_context(
        source_troop_type=TroopType.CAVALRY,
        target_troop_type=TroopType.SPEAR,
    )
    systems = BattleSystems(
        weapon_random_percent_range=(90, 90),
        weapon_low_damage_floor_range=(5, 5),
    )

    # B0=689; cavalry->spear: ceil(689*0.88)=607; R=90 => 547.
    assert calculate_base(context, systems) == 547


def test_weapon_base_damage_uses_post_random_low_damage_floor() -> None:
    context = make_context(
        source_troops=1,
        source_attack=0,
        target_defense=1000,
        target_troops=100,
    )
    systems = BattleSystems(
        weapon_random_percent_range=(86, 86),
        weapon_low_damage_floor_range=(15, 15),
    )

    assert calculate_base(context, systems) == 15


def test_formula_uses_current_troops_at_the_moment_of_each_attack() -> None:
    context = make_context(source_troops=10000)
    systems = BattleSystems(
        weapon_random_percent_range=(90, 90),
        weapon_low_damage_floor_range=(5, 5),
    )

    first = calculate_base(context, systems)
    context.get_unit("a").troops = 5000
    second = calculate_base(context, systems)

    assert first == 621
    assert second == 531
    assert second < first


def test_troop_system_remains_the_only_kill_cap_layer() -> None:
    context = make_context(target_troops=10)
    systems = BattleSystems(
        weapon_random_percent_range=(90, 90),
        weapon_low_damage_floor_range=(5, 5),
    )

    result = systems.damage_system.calculate(
        context,
        DamageRequest(
            source_id="a",
            target_id="b",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.NORMAL_ATTACK,
            coefficient=1.0,
        ),
    )
    assert result.final_damage == 621
    assert context.get_unit("b").troops == 10

    change = systems.troop_system.apply_damage(context.get_unit("b"), result.final_damage)
    assert change.actual_change == 10
    assert context.get_unit("b").troops == 0
