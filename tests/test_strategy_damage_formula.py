from __future__ import annotations

from sgs_v2.battle_core import (
    BattleContext,
    BattleSystems,
    DamageRequest,
    DamageSourceType,
    DamageType,
    EventBus,
    LineupPosition,
    RandomSystem,
    UnitRuntime,
)


def make_context(
    *,
    source_troops: int = 10000,
    source_attack: float = 999,
    source_intelligence: float = 300,
    target_defense: float = 999,
    target_intelligence: float = 200,
    source_level: int = 50,
    target_level: int = 50,
    seed: int = 1,
) -> BattleContext:
    return BattleContext(
        battle_id="strategy-formula",
        units={
            "a": UnitRuntime(
                unit_id="a",
                name="A",
                team_id="A",
                max_troops=source_troops,
                troops=source_troops,
                attack=source_attack,
                defense=100,
                speed=100,
                lineup_position=LineupPosition.COMMANDER,
                level=source_level,
                intelligence=source_intelligence,
            ),
            "b": UnitRuntime(
                unit_id="b",
                name="B",
                team_id="B",
                max_troops=10000,
                troops=10000,
                attack=100,
                defense=target_defense,
                speed=90,
                lineup_position=LineupPosition.COMMANDER,
                level=target_level,
                intelligence=target_intelligence,
            ),
        },
        event_bus=EventBus(),
        random=RandomSystem(seed),
    )


def calculate_strategy(context: BattleContext, systems: BattleSystems, coefficient: float = 1.0):
    return systems.damage_system.calculate(
        context,
        DamageRequest(
            source_id="a",
            target_id="b",
            damage_type=DamageType.STRATEGY,
            source_type=DamageSourceType.SKILL,
            coefficient=coefficient,
        ),
    )


def test_strategy_uses_same_full_troop_lookup_table() -> None:
    damage = BattleSystems().damage_system
    assert damage.strategy_troop_function(1) == 2
    assert damage.strategy_troop_function(2000) == 240
    assert damage.strategy_troop_function(2001) == 238
    assert damage.strategy_troop_function(4999) == 429
    assert damage.strategy_troop_function(5000) == 429
    assert damage.strategy_troop_function(10000) == 529


def test_strategy_base_damage_uses_intelligence_vs_intelligence() -> None:
    context = make_context()
    systems = BattleSystems(
        strategy_random_percent_range=(90, 90),
        strategy_low_damage_floor_range=(5, 5),
    )

    # F(10000)=529; Sa=Sd=1.6; X=529+300*1.6-200*1.6=689.
    # B0=B1=B2=689; ceil(689*90/100)=621.
    result = calculate_strategy(context, systems)
    assert result.base_damage == 621
    assert result.final_damage == 621


def test_strategy_ignores_weapon_attack_and_target_defense() -> None:
    first = calculate_strategy(
        make_context(source_attack=1, target_defense=1),
        BattleSystems(
            strategy_random_percent_range=(90, 90),
            strategy_low_damage_floor_range=(5, 5),
        ),
    )
    second = calculate_strategy(
        make_context(source_attack=5000, target_defense=5000),
        BattleSystems(
            strategy_random_percent_range=(90, 90),
            strategy_low_damage_floor_range=(5, 5),
        ),
    )
    assert first.base_damage == second.base_damage == 621


def test_strategy_changes_when_target_intelligence_changes() -> None:
    low_int_target = calculate_strategy(
        make_context(target_intelligence=100),
        BattleSystems(
            strategy_random_percent_range=(90, 90),
            strategy_low_damage_floor_range=(5, 5),
        ),
    )
    high_int_target = calculate_strategy(
        make_context(target_intelligence=300),
        BattleSystems(
            strategy_random_percent_range=(90, 90),
            strategy_low_damage_floor_range=(5, 5),
        ),
    )
    assert low_int_target.base_damage > high_int_target.base_damage


def test_strategy_coefficient_scales_intelligence_base_damage() -> None:
    context = make_context()
    systems = BattleSystems(
        strategy_random_percent_range=(90, 90),
        strategy_low_damage_floor_range=(5, 5),
    )
    result = calculate_strategy(context, systems, coefficient=1.5)
    assert result.base_damage == 621
    assert result.scaled_damage == 931.5
    assert result.final_damage == 931
