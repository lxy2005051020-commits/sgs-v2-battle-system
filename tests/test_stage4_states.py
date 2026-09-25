from __future__ import annotations

import inspect
from dataclasses import fields
from pathlib import Path

import pytest

from sgs_v2.battle_core import (
    BattleContext,
    BattleSystems,
    DamageRequest,
    DamageSourceType,
    DamageType,
    EventBus,
    EventType,
    LineupPosition,
    OfficialStateId,
    RandomSystem,
    TargetSystem,
    TroopSystem,
    UnitRuntime,
    register_official_state_definitions,
)
from sgs_v2.battle_core.engine import BattleEngine
from sgs_v2.battle_core.state_lifecycle_system import StateLifecycleSystem


class CountingRandomSystem(RandomSystem):
    def __init__(self, seed: int) -> None:
        super().__init__(seed)
        self.choice_calls = 0
        self.randint_calls = 0
        self.shuffle_calls = 0
        self.sample_calls = 0

    def choice(self, values):
        self.choice_calls += 1
        return super().choice(values)

    def randint(self, a: int, b: int) -> int:
        self.randint_calls += 1
        return super().randint(a, b)

    def shuffle(self, values) -> None:
        self.shuffle_calls += 1
        super().shuffle(values)

    def sample(self, values, k: int):
        self.sample_calls += 1
        return super().sample(values, k)


class RecordingTargetSystem(TargetSystem):
    def __init__(self) -> None:
        self.random_enemy_calls = 0

    def random_enemy(self, context, unit):
        self.random_enemy_calls += 1
        return super().random_enemy(context, unit)


class RecordingTroopSystem(TroopSystem):
    def __init__(self) -> None:
        self.apply_damage_calls = 0

    def apply_damage(self, target, requested_damage):
        self.apply_damage_calls += 1
        return super().apply_damage(target, requested_damage)


def make_combat_context(seed: int = 7) -> BattleContext:
    context = BattleContext(
        battle_id=f"stage4-combat-{seed}",
        units={
            "a1": UnitRuntime(
                "a1", "A1", "A", 10000, 10000, 300, 200, 100,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "b1": UnitRuntime(
                "b1", "B1", "B", 10000, 10000, 200, 200, 90,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "b2": UnitRuntime(
                "b2", "B2", "B", 10000, 10000, 200, 200, 80,
                lineup_position=LineupPosition.DEPUTY_1,
            ),
        },
        event_bus=EventBus(),
        random=CountingRandomSystem(seed),
        max_rounds=1,
    )
    register_official_state_definitions(context.states)
    return context


def make_order_context(seed: int = 11) -> BattleContext:
    context = BattleContext(
        battle_id=f"stage4-order-{seed}",
        units={
            "a1": UnitRuntime(
                "a1", "A1", "A", 100, 100, 1, 1, 10,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "a2": UnitRuntime(
                "a2", "A2", "A", 100, 100, 1, 1, 200,
                lineup_position=LineupPosition.DEPUTY_1,
            ),
            "b1": UnitRuntime(
                "b1", "B1", "B", 100, 100, 1, 1, 100,
                lineup_position=LineupPosition.COMMANDER,
            ),
        },
        event_bus=EventBus(),
        random=CountingRandomSystem(seed),
    )
    register_official_state_definitions(context.states)
    return context


def apply_state(context: BattleContext, state_id: OfficialStateId, owner_id: str) -> None:
    StateLifecycleSystem().apply(
        context,
        state_id=state_id.value,
        owner_id=owner_id,
    )


def test_action_order_first_strike_normal_ambush_tiers_override_speed() -> None:
    context = make_order_context()
    apply_state(context, OfficialStateId.FIRST_STRIKE, "a1")
    apply_state(context, OfficialStateId.AMBUSH, "a2")

    order = BattleSystems().action_order_system.determine_order(context)
    assert [unit.unit_id for unit in order] == ["a1", "b1", "a2"]
    assert context.random.shuffle_calls == 0


def test_multiple_first_strike_units_order_by_effective_speed_without_rng() -> None:
    context = make_order_context()
    apply_state(context, OfficialStateId.FIRST_STRIKE, "a1")
    apply_state(context, OfficialStateId.FIRST_STRIKE, "a2")

    order = BattleSystems().action_order_system.determine_order(context)
    assert [unit.unit_id for unit in order] == ["a2", "a1", "b1"]
    assert context.random.shuffle_calls == 0


def test_multiple_ambush_units_order_by_effective_speed_without_rng() -> None:
    context = make_order_context()
    apply_state(context, OfficialStateId.AMBUSH, "a1")
    apply_state(context, OfficialStateId.AMBUSH, "a2")

    order = BattleSystems().action_order_system.determine_order(context)
    assert [unit.unit_id for unit in order] == ["b1", "a2", "a1"]
    assert context.random.shuffle_calls == 0


def test_action_order_exact_same_tier_and_speed_is_deterministic_without_rng() -> None:
    context = make_order_context(2026)
    context.get_unit("a1").speed = 100
    context.get_unit("a2").speed = 100
    context.get_unit("b1").speed = 100
    apply_state(context, OfficialStateId.FIRST_STRIKE, "a1")
    apply_state(context, OfficialStateId.FIRST_STRIKE, "a2")

    order = BattleSystems().action_order_system.determine_order(context)

    assert [unit.unit_id for unit in order] == ["a1", "a2", "b1"]
    assert context.random.shuffle_calls == 0


def test_first_strike_and_ambush_on_same_unit_cancel_to_normal_tier() -> None:
    context = make_order_context()
    apply_state(context, OfficialStateId.FIRST_STRIKE, "a1")
    apply_state(context, OfficialStateId.AMBUSH, "a1")
    apply_state(context, OfficialStateId.FIRST_STRIKE, "a2")

    order = BattleSystems().action_order_system.determine_order(context)
    assert [unit.unit_id for unit in order] == ["a2", "b1", "a1"]
    assert context.random.shuffle_calls == 0

    second = make_order_context(seed=12)
    apply_state(second, OfficialStateId.FIRST_STRIKE, "a1")
    apply_state(second, OfficialStateId.AMBUSH, "a1")
    apply_state(second, OfficialStateId.AMBUSH, "b1")

    second_order = BattleSystems().action_order_system.determine_order(second)
    assert [unit.unit_id for unit in second_order] == ["a2", "a1", "b1"]
    assert second.random.shuffle_calls == 0


def test_disarm_blocks_before_target_damage_rng_and_troop_system() -> None:
    context = make_combat_context(seed=31)
    apply_state(context, OfficialStateId.DISARM, "a1")
    targets = RecordingTargetSystem()
    troops = RecordingTroopSystem()
    systems = BattleSystems(target_system=targets, troop_system=troops)
    before = {unit_id: unit.troops for unit_id, unit in context.units.items()}

    result = systems.normal_attack_system.execute(context, context.get_unit("a1"))

    assert result.target_id is None
    assert result.damage is None
    assert result.troop_change is None
    assert targets.random_enemy_calls == 0
    assert context.random.choice_calls == 0
    assert context.random.randint_calls == 0
    assert troops.apply_damage_calls == 0
    assert {unit_id: unit.troops for unit_id, unit in context.units.items()} == before

    event = context.event_bus.history[-1]
    assert event.event_type is EventType.ACTION_BLOCKED
    assert event.payload == {
        "action_type": "NORMAL_ATTACK",
        "reason_state_id": OfficialStateId.DISARM.value,
    }


def test_stun_blocks_entire_action_before_normal_attack_and_rng() -> None:
    context = make_combat_context(seed=32)
    apply_state(context, OfficialStateId.STUN, "a1")
    targets = RecordingTargetSystem()
    troops = RecordingTroopSystem()
    systems = BattleSystems(target_system=targets, troop_system=troops)

    result = systems.action_system.execute(context, context.get_unit("a1"))

    assert result is None
    assert targets.random_enemy_calls == 0
    assert context.random.choice_calls == 0
    assert context.random.randint_calls == 0
    assert troops.apply_damage_calls == 0
    assert not any(
        event.event_type is EventType.NORMAL_ATTACK
        for event in context.event_bus.history
    )
    event = context.event_bus.history[-1]
    assert event.event_type is EventType.ACTION_BLOCKED
    assert event.payload == {
        "action_type": "ALL",
        "reason_state_id": OfficialStateId.STUN.value,
    }


def test_stun_plus_disarm_is_blocked_by_stun_at_action_system_layer() -> None:
    context = make_combat_context(seed=33)
    apply_state(context, OfficialStateId.STUN, "a1")
    apply_state(context, OfficialStateId.DISARM, "a1")
    targets = RecordingTargetSystem()
    systems = BattleSystems(target_system=targets)

    assert systems.action_system.execute(context, context.get_unit("a1")) is None
    assert targets.random_enemy_calls == 0

    blocked = [
        event for event in context.event_bus.history
        if event.event_type is EventType.ACTION_BLOCKED
    ]
    assert len(blocked) == 1
    assert blocked[0].payload["reason_state_id"] == OfficialStateId.STUN.value
    assert blocked[0].payload["action_type"] == "ALL"


def test_weakness_allows_formula_then_settles_legal_zero_damage() -> None:
    context = make_combat_context(seed=34)
    apply_state(context, OfficialStateId.WEAKNESS, "a1")
    targets = RecordingTargetSystem()
    troops = RecordingTroopSystem()
    systems = BattleSystems(target_system=targets, troop_system=troops)
    before = {unit_id: unit.troops for unit_id, unit in context.units.items()}

    result = systems.normal_attack_system.execute(context, context.get_unit("a1"))

    assert targets.random_enemy_calls == 1
    assert context.random.choice_calls == 1
    assert context.random.randint_calls > 0
    assert result.target_id in {"b1", "b2"}
    assert result.damage is not None
    assert result.damage.base_damage > 0
    assert result.damage.scaled_damage > 0
    assert result.damage.final_damage == 0
    assert result.damage.prevented is False
    assert result.damage.zeroed_by_state_id == OfficialStateId.WEAKNESS.value
    assert result.troop_change is not None
    assert result.troop_change.actual_change == 0
    assert troops.apply_damage_calls == 1
    assert {unit_id: unit.troops for unit_id, unit in context.units.items()} == before

    combat_events = [
        event.event_type for event in context.event_bus.history
        if event.event_type in {
            EventType.NORMAL_ATTACK,
            EventType.DAMAGE_PREVENTED,
            EventType.DAMAGE_DEALT,
        }
    ]
    assert combat_events == [EventType.NORMAL_ATTACK, EventType.DAMAGE_DEALT]


def test_weakness_strategy_damage_runs_formula_then_zeroes_result() -> None:
    context = make_combat_context(seed=35)
    context.get_unit("a1").intelligence = 300
    context.get_unit("b1").intelligence = 200
    apply_state(context, OfficialStateId.WEAKNESS, "a1")
    result = BattleSystems().damage_system.calculate(
        context,
        DamageRequest(
            source_id="a1",
            target_id="b1",
            damage_type=DamageType.STRATEGY,
            source_type=DamageSourceType.SKILL,
            coefficient=2.0,
        ),
    )

    assert result.base_damage > 0
    assert result.scaled_damage > 0
    assert result.final_damage == 0
    assert result.prevented is False
    assert result.zeroed_by_state_id == OfficialStateId.WEAKNESS.value
    assert context.random.randint_calls > 0


def test_stage4_architecture_boundaries_remain_intact() -> None:
    engine_source = inspect.getsource(BattleEngine).lower()
    lifecycle_source = inspect.getsource(StateLifecycleSystem).lower()
    for state_id in (
        OfficialStateId.FIRST_STRIKE.value,
        OfficialStateId.AMBUSH.value,
        OfficialStateId.DISARM.value,
        OfficialStateId.STUN.value,
        OfficialStateId.WEAKNESS.value,
    ):
        assert state_id not in engine_source
        assert state_id not in lifecycle_source

    runtime_fields = {field.name for field in fields(UnitRuntime)}
    assert {
        "can_attack",
        "is_stunned",
        "has_first_strike",
        "has_ambush",
        "is_weak",
    }.isdisjoint(runtime_fields)

    core_dir = Path(__file__).parents[1] / "sgs_v2" / "battle_core"
    for path in core_dir.glob("*.py"):
        if path.name == "random_system.py":
            continue
        assert "import random" not in path.read_text(encoding="utf-8")
