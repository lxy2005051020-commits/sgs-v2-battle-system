from __future__ import annotations

import inspect

from sgs_v2.battle_core import (
    BattleContext,
    BattleEngine,
    BattlePhase,
    BattleSystems,
    EventBus,
    EventType,
    LineupPosition,
    RandomSystem,
    StateDefinition,
    StateLifecycleSystem,
    StateRegistry,
    UnitRuntime,
)


def make_context(seed: int = 17) -> BattleContext:
    units = {
        "a1": UnitRuntime(
            unit_id="a1",
            name="A1",
            team_id="A",
            max_troops=10000,
            troops=10000,
            attack=1,
            defense=10000,
            speed=101,
            intelligence=100,
            lineup_position=LineupPosition.COMMANDER,
        ),
        "b1": UnitRuntime(
            unit_id="b1",
            name="B1",
            team_id="B",
            max_troops=10000,
            troops=10000,
            attack=1,
            defense=10000,
            speed=100,
            intelligence=100,
            lineup_position=LineupPosition.COMMANDER,
        ),
    }
    context = BattleContext(
        battle_id=f"stage3-{seed}",
        units=units,
        event_bus=EventBus(),
        random=RandomSystem(seed=seed),
        max_rounds=1,
    )
    context.states.register_definition(
        StateDefinition(state_id="test_state", name="测试状态")
    )
    return context


def test_context_and_systems_expose_stage3_components() -> None:
    context = make_context()
    systems = BattleSystems()

    assert isinstance(context.states, StateRegistry)
    assert isinstance(systems.state_lifecycle_system, StateLifecycleSystem)


def test_engine_expires_round_start_before_round_started() -> None:
    context = make_context()
    systems = BattleSystems()
    instance = systems.state_lifecycle_system.apply(
        context,
        state_id="test_state",
        owner_id="b1",
        source_id="a1",
        expires_round=1,
        expires_phase=BattlePhase.ROUND_START.value,
    )

    BattleEngine(context=context, systems=systems).run()

    assert context.states.has(owner_id="b1", state_id="test_state") is False

    events = list(context.event_bus.history)
    expired_index = next(
        index
        for index, event in enumerate(events)
        if event.event_type is EventType.STATE_EXPIRED
        and event.payload["instance_id"] == instance.instance_id
    )
    round_started_index = next(
        index
        for index, event in enumerate(events)
        if event.event_type is EventType.ROUND_STARTED
        and event.round_no == 1
    )
    assert expired_index < round_started_index


def test_engine_expires_round_end_after_round_ended() -> None:
    context = make_context()
    systems = BattleSystems()
    instance = systems.state_lifecycle_system.apply(
        context,
        state_id="test_state",
        owner_id="b1",
        source_id="a1",
        expires_round=1,
        expires_phase=BattlePhase.ROUND_END.value,
    )

    BattleEngine(context=context, systems=systems).run()

    events = list(context.event_bus.history)
    round_ended_index = next(
        index
        for index, event in enumerate(events)
        if event.event_type is EventType.ROUND_ENDED
        and event.round_no == 1
    )
    expired_index = next(
        index
        for index, event in enumerate(events)
        if event.event_type is EventType.STATE_EXPIRED
        and event.payload["instance_id"] == instance.instance_id
    )
    assert round_ended_index < expired_index


def run_state_flow(seed: int) -> tuple[str, list[tuple[object, ...]]]:
    context = make_context(seed)
    systems = BattleSystems()
    instance = systems.state_lifecycle_system.apply(
        context,
        state_id="test_state",
        owner_id="b1",
        source_id="a1",
        source_skill_id="test-skill",
        expires_round=1,
        expires_phase=BattlePhase.ROUND_END.value,
    )
    BattleEngine(context=context, systems=systems).run()

    state_events = [
        (
            event.event_type.value,
            event.round_no,
            event.phase,
            event.actor_id,
            event.target_id,
            event.payload,
        )
        for event in context.event_bus.history
        if event.event_type
        in {
            EventType.STATE_APPLIED,
            EventType.STATE_REMOVED,
            EventType.STATE_EXPIRED,
        }
    ]
    return instance.instance_id, state_events


def test_same_flow_has_same_instance_id_and_state_events() -> None:
    first_id, first_events = run_state_flow(1234)
    second_id, second_events = run_state_flow(1234)

    assert first_id == second_id == "state-000001"
    assert first_events == second_events


def test_engine_does_not_know_specific_state_names() -> None:
    source = inspect.getsource(BattleEngine).lower()
    for forbidden in ("disarm", "stun", "silence", "first_strike"):
        assert forbidden not in source


def test_lifecycle_source_does_not_modify_troops_directly() -> None:
    source = inspect.getsource(StateLifecycleSystem)
    assert ".troops" not in source
    assert "import random" not in source
