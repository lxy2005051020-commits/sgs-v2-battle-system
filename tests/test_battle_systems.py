from __future__ import annotations

from pathlib import Path

from sgs_v2.battle_core import (
    AttributeSystem,
    BattleContext,
    BattleEndReason,
    BattleEngine,
    BattleSystems,
    EventBus,
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
            "a": UnitRuntime("a", "A", "A", 100, 100, 100, 100, 10),
            "a2": UnitRuntime("a2", "A2", "A", 100, 0, 100, 100, 20),
            "b": UnitRuntime("b", "B", "B", 100, 100, 100, 100, 10),
            "b2": UnitRuntime("b2", "B2", "B", 100, 100, 100, 100, 20),
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
            "a": UnitRuntime("a", "A", "A", 100, 100, 1, 1, 1),
            "b": UnitRuntime("b", "B", "B", 100, 100, 1, 1, 1),
        },
        event_bus=EventBus(),
        random=RandomSystem(123),
    )
    target = TargetSystem().random_enemy(context, context.get_unit("a"))
    assert target is context.get_unit("b")
    assert context.random.random() == RandomSystem(123).random()


def test_target_system_full_selection_does_not_consume_randomness_and_is_stable() -> None:
    context = make_context(seed=321)
    targets = TargetSystem()
    candidates = [context.get_unit("b2"), context.get_unit("b")]

    selected = targets.random_units(context, candidates, count=99)

    assert [unit.unit_id for unit in selected] == ["b", "b2"]
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


def test_damage_calculation_does_not_change_troops_until_troop_system_applies_it() -> None:
    context = make_context()
    systems = BattleSystems(damage_scale=2.0)
    damage = systems.damage_system.calculate_normal_attack(
        context, context.get_unit("a"), context.get_unit("b")
    )
    target = context.get_unit("b")
    assert target.troops == 100
    change = systems.troop_system.apply_damage(target, damage.requested_damage)
    assert change.actual_change == damage.requested_damage
    assert target.troops == 0


def test_troop_system_clamps_damage_and_recovery() -> None:
    unit = UnitRuntime("x", "X", "A", 100, 10, 1, 1, 1)
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
                "wrong": UnitRuntime("real", "A", "A", 100, 100, 1, 1, 1),
                "enemy": UnitRuntime("enemy", "B", "B", 100, 100, 1, 1, 1),
            },
            event_bus=EventBus(),
            random=RandomSystem(1),
        )


def test_battle_with_no_alive_units_ends_immediately_as_draw() -> None:
    context = BattleContext(
        battle_id="all-dead",
        units={
            "a": UnitRuntime("a", "A", "A", 100, 0, 100, 100, 100, True),
            "b": UnitRuntime("b", "B", "B", 100, 0, 100, 100, 100, True),
        },
        event_bus=EventBus(),
        random=RandomSystem(1),
    )
    result = BattleEngine(context=context, systems=BattleSystems()).run()
    assert result.winner_team_id is None
    assert result.reason is BattleEndReason.DRAW
    assert result.rounds_completed == 0
    assert not any(event.round_no > 0 for event in context.event_bus.history)


def test_action_order_does_not_consume_randomness_for_unique_speeds() -> None:
    context = BattleContext(
        battle_id="unique-speeds",
        units={
            "a": UnitRuntime("a", "A", "A", 10, 10, 1, 1, 100),
            "b": UnitRuntime("b", "B", "B", 10, 10, 1, 1, 90),
            "c": UnitRuntime("c", "C", "B", 10, 10, 1, 1, 80),
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
        all_units = {
            unit_id: UnitRuntime(unit_id, unit_id, "A" if unit_id < "c" else "B", 10, 10, 1, 1, 100)
            for unit_id in unit_order
        }
        return BattleContext("tied-order", all_units, EventBus(), RandomSystem(77))

    first = make_tied_context(["a", "b", "c"])
    second = make_tied_context(["c", "a", "b"])
    systems = BattleSystems()
    assert [unit.unit_id for unit in systems.action_order_system.determine_order(first)] == [
        unit.unit_id for unit in systems.action_order_system.determine_order(second)
    ]
