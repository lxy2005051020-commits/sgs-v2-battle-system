from __future__ import annotations

from pathlib import Path

from sgs_v2.battle_core import (
    BattleContext,
    BattleEngine,
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


def make_context(seed: int = 7) -> BattleContext:
    return BattleContext(
        battle_id=f"stage3-integration-{seed}",
        units={
            "a1": UnitRuntime(
                "a1", "A", "A", 100000, 100000, 1, 100000, 100,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "b1": UnitRuntime(
                "b1", "B", "B", 100000, 100000, 1, 100000, 90,
                lineup_position=LineupPosition.COMMANDER,
            ),
        },
        event_bus=EventBus(),
        random=RandomSystem(seed),
        max_rounds=1,
    )


def register_test_state(context: BattleContext) -> None:
    context.states.register_definition(StateDefinition("test_state", "测试状态"))


def test_context_and_battle_systems_expose_stage3_state_infrastructure() -> None:
    context = make_context()
    systems = BattleSystems()

    assert isinstance(context.states, StateRegistry)
    assert isinstance(systems.state_lifecycle_system, StateLifecycleSystem)


def test_engine_expires_round_start_before_round_started_and_round_end_after_round_ended() -> None:
    context = make_context(seed=11)
    systems = BattleSystems()
    register_test_state(context)

    start_instance = systems.state_lifecycle_system.apply(
        context,
        state_id="test_state",
        owner_id="b1",
        source_id="a1",
        expires_round=1,
        expires_phase="ROUND_START",
    )
    end_instance = systems.state_lifecycle_system.apply(
        context,
        state_id="test_state",
        owner_id="b1",
        source_id="a1",
        expires_round=1,
        expires_phase="ROUND_END",
    )

    BattleEngine(context=context, systems=systems).run()

    assert not context.states.has(owner_id="b1", state_id="test_state")

    events = list(context.event_bus.history)
    start_expired_index = next(
        index
        for index, event in enumerate(events)
        if event.event_type is EventType.STATE_EXPIRED
        and event.payload["instance_id"] == start_instance.instance_id
    )
    round_started_index = next(
        index
        for index, event in enumerate(events)
        if event.event_type is EventType.ROUND_STARTED
    )
    assert start_expired_index < round_started_index

    round_ended_index = next(
        index
        for index, event in enumerate(events)
        if event.event_type is EventType.ROUND_ENDED
    )
    end_expired_index = next(
        index
        for index, event in enumerate(events)
        if event.event_type is EventType.STATE_EXPIRED
        and event.payload["instance_id"] == end_instance.instance_id
    )
    assert round_ended_index < end_expired_index


def run_state_flow(seed: int) -> tuple[list[str], list[tuple[object, ...]]]:
    context = make_context(seed=seed)
    systems = BattleSystems()
    register_test_state(context)

    first = systems.state_lifecycle_system.apply(
        context,
        state_id="test_state",
        owner_id="b1",
        source_id="a1",
        source_skill_id="test_skill",
        expires_round=1,
        expires_phase="ROUND_START",
    )
    second = systems.state_lifecycle_system.apply(
        context,
        state_id="test_state",
        owner_id="a1",
        source_id="b1",
        expires_round=1,
        expires_phase="ROUND_END",
    )
    BattleEngine(context=context, systems=systems).run()

    state_events = [
        event
        for event in context.event_bus.history
        if event.event_type
        in {EventType.STATE_APPLIED, EventType.STATE_REMOVED, EventType.STATE_EXPIRED}
    ]
    normalized = [
        (
            event.event_type,
            event.phase,
            event.round_no,
            event.actor_id,
            event.target_id,
            tuple(sorted(event.payload.items())),
        )
        for event in state_events
    ]
    return [first.instance_id, second.instance_id], normalized


def test_same_configuration_and_seed_reproduce_state_ids_and_events() -> None:
    first_ids, first_events = run_state_flow(99)
    second_ids, second_events = run_state_flow(99)

    assert first_ids == second_ids == ["state-000001", "state-000002"]
    assert first_events == second_events


def test_stage3_production_code_does_not_hardcode_specific_state_rules() -> None:
    core_dir = Path(__file__).parents[1] / "sgs_v2" / "battle_core"
    engine_source = (core_dir / "engine.py").read_text(encoding="utf-8").lower()
    lifecycle_source = (core_dir / "state_lifecycle_system.py").read_text(
        encoding="utf-8"
    ).lower()

    for forbidden in ("disarm", "stun", "silence", "first_strike"):
        assert forbidden not in engine_source
        assert forbidden not in lifecycle_source

    for forbidden in (
        "target.troops",
        "unit.troops",
        "target.attack",
        "unit.attack +=",
        "uuid.uuid4",
        "import random",
        "if skill.name",
    ):
        assert forbidden not in lifecycle_source
