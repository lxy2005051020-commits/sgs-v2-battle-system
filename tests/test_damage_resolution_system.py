from __future__ import annotations

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
    StateLifecycleSystem,
    TroopSystem,
    UnitRuntime,
    register_official_state_definitions,
)


class RecordingTroopSystem(TroopSystem):
    def __init__(self) -> None:
        self.apply_damage_calls = 0

    def apply_damage(self, target, requested_damage):
        self.apply_damage_calls += 1
        return super().apply_damage(target, requested_damage)


def make_context(*, target_troops: int = 10000, seed: int = 11) -> BattleContext:
    context = BattleContext(
        battle_id=f"stage5-damage-resolution-{seed}",
        units={
            "a1": UnitRuntime(
                "a1", "A1", "A", 10000, 10000, 500, 100, 100,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "b1": UnitRuntime(
                "b1", "B1", "B", max(1, target_troops), target_troops, 100, 0, 90,
                lineup_position=LineupPosition.COMMANDER,
            ),
        },
        event_bus=EventBus(),
        random=RandomSystem(seed),
    )
    register_official_state_definitions(context.states)
    return context


def request() -> DamageRequest:
    return DamageRequest(
        source_id="a1",
        target_id="b1",
        damage_type=DamageType.WEAPON,
        source_type=DamageSourceType.SKILL,
        coefficient=1.0,
        source_skill_id="test-skill",
    )


def test_damage_resolution_routes_actual_damage_through_troop_system() -> None:
    context = make_context()
    troops = RecordingTroopSystem()
    systems = BattleSystems(
        troop_system=troops,
        weapon_random_percent_range=(90, 90),
        weapon_low_damage_floor_range=(5, 5),
    )
    before = context.get_unit("b1").troops

    result = systems.damage_resolution_system.resolve(context, request())

    assert result.damage.final_damage > 0
    assert result.troop_change is not None
    assert result.target_defeated is False
    assert troops.apply_damage_calls == 1
    assert context.get_unit("b1").troops == before - result.troop_change.actual_change
    assert context.event_bus.history[-1].event_type is EventType.DAMAGE_DEALT


def test_weakness_settles_legal_zero_through_troop_system() -> None:
    context = make_context(seed=12)
    StateLifecycleSystem().apply(
        context,
        state_id=OfficialStateId.WEAKNESS.value,
        owner_id="a1",
    )
    troops = RecordingTroopSystem()
    systems = BattleSystems(troop_system=troops)
    before = context.get_unit("b1").troops

    result = systems.damage_resolution_system.resolve(context, request())

    assert result.damage.prevented is False
    assert result.damage.zeroed_by_state_id == OfficialStateId.WEAKNESS.value
    assert result.damage.final_damage == 0
    assert result.troop_change is not None
    assert result.troop_change.actual_change == 0
    assert troops.apply_damage_calls == 1
    assert context.get_unit("b1").troops == before
    assert context.event_bus.history[-1].event_type is EventType.DAMAGE_DEALT


def test_damage_resolution_publishes_unit_defeated_after_damage_dealt() -> None:
    context = make_context(target_troops=10, seed=13)
    systems = BattleSystems(
        weapon_random_percent_range=(90, 90),
        weapon_low_damage_floor_range=(5, 5),
    )

    result = systems.damage_resolution_system.resolve(context, request())

    assert result.target_defeated is True
    assert context.get_unit("b1").troops == 0
    combat_events = [
        event.event_type
        for event in context.event_bus.history
        if event.event_type in {EventType.DAMAGE_DEALT, EventType.UNIT_DEFEATED}
    ]
    assert combat_events == [EventType.DAMAGE_DEALT, EventType.UNIT_DEFEATED]


def test_damage_system_calculation_still_does_not_modify_troops() -> None:
    context = make_context(seed=14)
    systems = BattleSystems(
        weapon_random_percent_range=(90, 90),
        weapon_low_damage_floor_range=(5, 5),
    )
    before = context.get_unit("b1").troops

    result = systems.damage_system.calculate(context, request())

    assert result.final_damage > 0
    assert context.get_unit("b1").troops == before
