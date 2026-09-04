from __future__ import annotations

from pathlib import Path

from sgs_v2.battle_core import (
    AttributeSystem,
    BattleContext,
    BattleEndReason,
    BattleEngine,
    BattleSystems,
    DamageRequest,
    DamageSourceType,
    DamageType,
    EventBus,
    LineupPosition,
    RandomSystem,
    TargetSystem,
    TroopSystem,
    UnitRuntime,
)
import pytest


def make_context(seed: int = 7) -> BattleContext:
    return BattleContext(
        battle_id=f"systems-{seed}",
        units={
            "a": UnitRuntime("a", "A", "A", 100, 100, 100, 100, 10, lineup_position=LineupPosition.COMMANDER),
            "a2": UnitRuntime("a2", "A2", "A", 100, 0, 100, 100, 20, lineup_position=LineupPosition.DEPUTY_1),
            "b": UnitRuntime("b", "B", "B", 100, 100, 100, 100, 10, lineup_position=LineupPosition.COMMANDER),
            "b2": UnitRuntime("b2", "B2", "B", 100, 100, 100, 100, 20, lineup_position=LineupPosition.DEPUTY_1),
        },
        event_bus=EventBus(),
        random=RandomSystem(seed),
    )


def test_target_system_filters_living_units_and_uses_random_system() -> None:
    context = make_context()
    targets = TargetSystem()
    actor = context.get_unit("a")
    assert [unit.unit_id for unit in targets.allies(context, actor)] == ["a"]
    assert [unit.unit_id for unit in targets.enemies(context, actor)] == ["b", "b2"]
    assert [unit.unit_id for unit in targets.random_units(
        context, targets.enemies(context, actor), count=5
    )] == ["b", "b2"]


def test_target_system_does_not_consume_randomness_when_only_one_enemy_exists() -> None:
    context = BattleContext(
        battle_id="single-enemy",
        units={
            "a": UnitRuntime("a", "A", "A", 100, 100, 1, 1, 1, lineup_position=LineupPosition.COMMANDER),
            "b": UnitRuntime("b", "B", "B", 100, 100, 1, 1, 1, lineup_position=LineupPosition.COMMANDER),
        },
        event_bus=EventBus(),
        random=RandomSystem(123),
    )
    target = TargetSystem().random_enemy(context, context.get_unit("a"))
    assert target is context.get_unit("b")
    assert context.random.random() == RandomSystem(123).random()


def test_target_system_full_selection_does_not_consume_randomness_and_uses_lineup_order() -> None:
    context = BattleContext(
        battle_id="full-selection",
        units={
            "a": UnitRuntime("a", "A", "A", 100, 100, 1, 1, 1, lineup_position=LineupPosition.COMMANDER),
            "b2": UnitRuntime("b2", "B2", "B", 100, 100, 1, 1, 1, lineup_position=LineupPosition.DEPUTY_1),
            "b3": UnitRuntime("b3", "B3", "B", 100, 100, 1, 1, 1, lineup_position=LineupPosition.DEPUTY_2),
            "b1": UnitRuntime("b1", "B1", "B", 100, 100, 1, 1, 1, lineup_position=LineupPosition.COMMANDER),
        },
        event_bus=EventBus(),
        random=RandomSystem(321),
    )
    targets = TargetSystem()
    candidates = [context.get_unit("b3"), context.get_unit("b1"), context.get_unit("b2")]

    selected = targets.random_units(context, candidates, count=99)

    assert [unit.unit_id for unit in selected] == ["b1", "b2", "b3"]
    assert context.random.random() == RandomSystem(321).random()


def test_target_system_empty_selection_does_not_consume_randomness() -> None:
    context = make_context(seed=654)
    selected = TargetSystem().random_units(context, [], count=3)
    assert selected == []
    assert context.random.random() == RandomSystem(654).random()


def test_attribute_system_is_the_source_of_final_attributes() -> None:
    class Modifier:
        def modify_attribute(self, *, context, unit, attribute, base_value):
            return base_value + {"attack": 30, "defense": 20, "speed": 40}[attribute]

    context = make_context()
    attributes = AttributeSystem(Modifier())
    unit = context.get_unit("a")
    assert attributes.get_attack(context, unit) == 130
    assert attributes.get_defense(context, unit) == 120
    assert attributes.get_speed(context, unit) == 50


def test_action_order_uses_final_speed_and_seeded_tie_breakers() -> None:
    class SpeedModifier:
        def modify_attribute(self, *, context, unit, attribute, base_value):
            return 99 if attribute == "speed" and unit.unit_id == "a" else base_value

    context = make_context(seed=99)
    systems = BattleSystems(attribute_system=AttributeSystem(SpeedModifier()))
    assert [unit.unit_id for unit in systems.action_order_system.determine_order(context)] == [
        "a", "b2", "b"
    ]


def test_damage_request_weapon_coefficient_scales_base_damage() -> None:
    context = make_context()
    systems = BattleSystems()
    result = systems.damage_system.calculate(
        context,
        DamageRequest(
            source_id="a",
            target_id="b",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.SKILL,
            coefficient=1.8,
            source_skill_id="test_skill",
        ),
    )

    assert result.damage_type is DamageType.WEAPON
    assert result.source_type is DamageSourceType.SKILL
    assert result.coefficient == 1.8
    assert result.scaled_damage == pytest.approx(result.base_damage * 1.8)
    assert result.final_damage == max(1, int(result.scaled_damage))
    assert result.source_skill_id == "test_skill"


def test_damage_request_strategy_uses_separate_base_damage_path() -> None:
    context = make_context()
    systems = BattleSystems()
    with pytest.raises(NotImplementedError, match="strategy base damage"):
        systems.damage_system.calculate(
            context,
            DamageRequest(
                source_id="a",
                target_id="b",
                damage_type=DamageType.STRATEGY,
                source_type=DamageSourceType.SKILL,
                coefficient=1.5,
            ),
        )


def test_damage_request_rejects_negative_coefficient() -> None:
    with pytest.raises(ValueError, match="coefficient"):
        DamageRequest(
            source_id="a",
            target_id="b",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.SKILL,
            coefficient=-0.1,
        )


def test_damage_calculation_does_not_change_troops_until_troop_system_applies_it() -> None:
    context = make_context()
    systems = BattleSystems(damage_scale=2.0)
    damage = systems.damage_system.calculate_normal_attack(
        context, context.get_unit("a"), context.get_unit("b")
    )
    target = context.get_unit("b")
    assert target.troops == 100
    change = systems.troop_system.apply_damage(target, damage.final_damage)
    expected_actual = min(100, damage.final_damage)
    assert change.actual_change == expected_actual
    assert target.troops == 100 - expected_actual


def test_normal_attack_routes_through_weapon_damage_request() -> None:
    context = BattleContext(
        battle_id="normal-attack-request",
        units={
            "a": UnitRuntime("a", "A", "A", 100, 100, 100, 100, 100, lineup_position=LineupPosition.COMMANDER),
            "b": UnitRuntime("b", "B", "B", 100, 100, 100, 100, 90, lineup_position=LineupPosition.COMMANDER),
        },
        event_bus=EventBus(),
        random=RandomSystem(1),
    )
    result = BattleSystems().normal_attack_system.execute(context, context.get_unit("a"))
    assert result.damage is not None
    assert result.damage.damage_type is DamageType.WEAPON
    assert result.damage.source_type is DamageSourceType.NORMAL_ATTACK
    assert result.damage.coefficient == 1.0


def test_troop_system_clamps_damage_and_recovery() -> None:
    unit = UnitRuntime("x", "X", "A", 100, 10, 1, 1, 1, lineup_position=LineupPosition.COMMANDER)
    troops = TroopSystem()
    assert troops.apply_damage(unit, 99).actual_change == 10
    assert unit.troops == 0
    assert troops.restore(unit, 150).actual_change == 100
    assert unit.troops == 100


def test_stage1_temporary_rules_source_has_been_removed() -> None:
    core_dir = Path(__file__).parents[1] / "sgs_v2" / "battle_core"
    assert not (core_dir / "stage1_rules.py").exists()


def test_context_rejects_mismatched_unit_key() -> None:
    with pytest.raises(ValueError, match="does not match"):
        BattleContext(
            battle_id="mismatched-key",
            units={
                "wrong": UnitRuntime("real", "A", "A", 100, 100, 1, 1, 1, lineup_position=LineupPosition.COMMANDER),
                "enemy": UnitRuntime("enemy", "B", "B", 100, 100, 1, 1, 1, lineup_position=LineupPosition.COMMANDER),
            },
            event_bus=EventBus(),
            random=RandomSystem(1),
        )


def test_context_rejects_duplicate_lineup_positions() -> None:
    with pytest.raises(ValueError, match="duplicate lineup position"):
        BattleContext(
            battle_id="duplicate-position",
            units={
                "a1": UnitRuntime("a1", "A1", "A", 100, 100, 1, 1, 1, lineup_position=LineupPosition.COMMANDER),
                "a2": UnitRuntime("a2", "A2", "A", 100, 100, 1, 1, 1, lineup_position=LineupPosition.DEPUTY_1),
                "a3": UnitRuntime("a3", "A3", "A", 100, 100, 1, 1, 1, lineup_position=LineupPosition.DEPUTY_1),
                "b1": UnitRuntime("b1", "B1", "B", 100, 100, 1, 1, 1, lineup_position=LineupPosition.COMMANDER),
            },
            event_bus=EventBus(),
            random=RandomSystem(1),
        )


def test_context_requires_contiguous_lineup_positions() -> None:
    with pytest.raises(ValueError, match="contiguous"):
        BattleContext(
            battle_id="missing-deputy-one",
            units={
                "a1": UnitRuntime("a1", "A1", "A", 100, 100, 1, 1, 1, lineup_position=LineupPosition.COMMANDER),
                "a3": UnitRuntime("a3", "A3", "A", 100, 100, 1, 1, 1, lineup_position=LineupPosition.DEPUTY_2),
                "b1": UnitRuntime("b1", "B1", "B", 100, 100, 1, 1, 1, lineup_position=LineupPosition.COMMANDER),
            },
            event_bus=EventBus(),
            random=RandomSystem(1),
        )


def test_battle_with_no_alive_units_ends_immediately_as_draw() -> None:
    context = BattleContext(
        battle_id="all-dead",
        units={
            "a": UnitRuntime("a", "A", "A", 100, 0, 100, 100, 100, lineup_position=LineupPosition.COMMANDER),
            "b": UnitRuntime("b", "B", "B", 100, 0, 100, 100, 100, lineup_position=LineupPosition.COMMANDER),
        },
        event_bus=EventBus(),
        random=RandomSystem(1),
    )
    result = BattleEngine(context=context, systems=BattleSystems()).run()
    assert result.winner_team_id is None
    assert result.reason is BattleEndReason.DRAW
    assert result.rounds_completed == 0
    assert not any(event.round_no > 0 for event in context.event_bus.history)


def test_commander_defeat_ends_battle_even_if_deputy_is_alive() -> None:
    context = BattleContext(
        battle_id="commander-defeat",
        units={
            "a1": UnitRuntime("a1", "A主将", "A", 100, 100, 1000, 0, 200, lineup_position=LineupPosition.COMMANDER),
            "a2": UnitRuntime("a2", "A副将", "A", 100, 100, 1, 1, 1, lineup_position=LineupPosition.DEPUTY_1),
            "b1": UnitRuntime("b1", "B主将", "B", 10, 10, 1, 0, 100, lineup_position=LineupPosition.COMMANDER),
            "b2": UnitRuntime("b2", "B副将", "B", 100, 100, 1, 1, 1, lineup_position=LineupPosition.DEPUTY_1),
        },
        event_bus=EventBus(),
        random=RandomSystem(1),
        max_rounds=1,
    )
    result = BattleEngine(context=context, systems=BattleSystems(damage_scale=10.0)).run()
    assert result.winner_team_id == "A"
    assert result.reason is BattleEndReason.COMMANDER_DEFEATED
    assert context.get_unit("b2").is_alive


def test_action_order_does_not_consume_randomness_for_unique_speeds() -> None:
    context = BattleContext(
        battle_id="unique-speeds",
        units={
            "a": UnitRuntime("a", "A", "A", 10, 10, 1, 1, 100, lineup_position=LineupPosition.COMMANDER),
            "b": UnitRuntime("b", "B", "B", 10, 10, 1, 1, 90, lineup_position=LineupPosition.COMMANDER),
            "c": UnitRuntime("c", "C", "B", 10, 10, 1, 1, 80, lineup_position=LineupPosition.DEPUTY_1),
        },
        event_bus=EventBus(),
        random=RandomSystem(123),
    )
    systems = BattleSystems()
    assert [unit.unit_id for unit in systems.action_order_system.determine_order(context)] == [
        "a", "b", "c"
    ]

    expected_random = RandomSystem(123).random()
    assert context.random.random() == expected_random


def test_action_order_shuffle_is_stable_across_unit_dict_insertion_order() -> None:
    def make_tied_context(unit_order: list[str]) -> BattleContext:
        all_units_map = {
            "a": UnitRuntime("a", "a", "A", 10, 10, 1, 1, 100, lineup_position=LineupPosition.COMMANDER),
            "b": UnitRuntime("b", "b", "A", 10, 10, 1, 1, 100, lineup_position=LineupPosition.DEPUTY_1),
            "c": UnitRuntime("c", "c", "B", 10, 10, 1, 1, 100, lineup_position=LineupPosition.COMMANDER),
        }
        all_units = {unit_id: all_units_map[unit_id] for unit_id in unit_order}
        return BattleContext("tied-order", all_units, EventBus(), RandomSystem(77))

    first = make_tied_context(["a", "b", "c"])
    second = make_tied_context(["c", "a", "b"])
    systems = BattleSystems()
    assert [unit.unit_id for unit in systems.action_order_system.determine_order(first)] == [
        unit.unit_id for unit in systems.action_order_system.determine_order(second)
    ]
