from __future__ import annotations

from sgs_v2.battle_core import (
    BattleContext,
    BattleSystems,
    EventBus,
    EventType,
    LineupPosition,
    OfficialStateId,
    RandomSystem,
    StateLifecycleSystem,
    UnitRuntime,
    register_official_state_definitions,
)


def make_context(seed: int) -> BattleContext:
    context = BattleContext(
        battle_id=f"stage5-normal-attack-{seed}",
        units={
            "a1": UnitRuntime(
                "a1", "A1", "A", 10000, 10000, 300, 100, 100,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "b1": UnitRuntime(
                "b1", "B1", "B", 10000, 10000, 100, 100, 90,
                lineup_position=LineupPosition.COMMANDER,
            ),
        },
        event_bus=EventBus(),
        random=RandomSystem(seed),
    )
    register_official_state_definitions(context.states)
    return context


def test_normal_attack_keeps_stage4_damage_dealt_event_order() -> None:
    context = make_context(31)
    BattleSystems().normal_attack_system.execute(context, context.get_unit("a1"))

    events = [
        event.event_type
        for event in context.event_bus.history
        if event.event_type in {
            EventType.NORMAL_ATTACK,
            EventType.DAMAGE_DEALT,
            EventType.DAMAGE_PREVENTED,
        }
    ]
    assert events == [EventType.NORMAL_ATTACK, EventType.DAMAGE_DEALT]


def test_weakness_keeps_legal_zero_damage_dealt_event_order() -> None:
    context = make_context(32)
    StateLifecycleSystem().apply(
        context,
        state_id=OfficialStateId.WEAKNESS.value,
        owner_id="a1",
    )

    BattleSystems().normal_attack_system.execute(context, context.get_unit("a1"))

    events = [
        event.event_type
        for event in context.event_bus.history
        if event.event_type in {
            EventType.NORMAL_ATTACK,
            EventType.DAMAGE_DEALT,
            EventType.DAMAGE_PREVENTED,
        }
    ]
    assert events == [EventType.NORMAL_ATTACK, EventType.DAMAGE_DEALT]
