from __future__ import annotations

import pytest

from sgs_v2.battle_core import (
    BattleContext,
    EventBus,
    EventType,
    LineupPosition,
    RandomSystem,
    StateDefinition,
    StateLifecycleSystem,
    UnitRuntime,
)


def make_context(seed: int = 7) -> BattleContext:
    context = BattleContext(
        battle_id=f"state-lifecycle-{seed}",
        units={
            "a1": UnitRuntime(
                "a1", "A", "A", 1000, 1000, 100, 100, 100,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "b1": UnitRuntime(
                "b1", "B", "B", 1000, 1000, 100, 100, 90,
                lineup_position=LineupPosition.COMMANDER,
            ),
        },
        event_bus=EventBus(),
        random=RandomSystem(seed),
    )
    context.states.register_definition(StateDefinition("test_state", "测试状态"))
    return context


def test_apply_validates_definition_owner_and_source() -> None:
    lifecycle = StateLifecycleSystem()
    context = make_context()

    with pytest.raises(KeyError, match="unknown state_id"):
        lifecycle.apply(context, state_id="missing", owner_id="b1")

    with pytest.raises(KeyError, match="unknown unit_id"):
        lifecycle.apply(context, state_id="test_state", owner_id="missing")

    with pytest.raises(KeyError, match="unknown unit_id"):
        lifecycle.apply(
            context,
            state_id="test_state",
            owner_id="b1",
            source_id="missing",
        )


def test_apply_generates_deterministic_ids_and_applied_event() -> None:
    lifecycle = StateLifecycleSystem()
    context = make_context()
    context.current_round = 1
    context.current_phase = "UNIT_ACTION"

    first = lifecycle.apply(
        context,
        state_id="test_state",
        owner_id="b1",
        source_id="a1",
        source_skill_id="test_skill",
        expires_round=3,
        expires_phase="ROUND_START",
    )
    second = lifecycle.apply(
        context,
        state_id="test_state",
        owner_id="b1",
        source_id="a1",
    )

    assert first.instance_id == "state-000001"
    assert second.instance_id == "state-000002"
    assert first.applied_round == 1
    assert first.applied_phase == "UNIT_ACTION"

    event = context.event_bus.history[-2]
    assert event.event_type is EventType.STATE_APPLIED
    assert event.actor_id == "a1"
    assert event.target_id == "b1"
    assert event.payload == {
        "instance_id": "state-000001",
        "state_id": "test_state",
        "owner_id": "b1",
        "source_id": "a1",
        "source_skill_id": "test_skill",
        "applied_round": 1,
        "applied_phase": "UNIT_ACTION",
        "expires_round": 3,
        "expires_phase": "ROUND_START",
    }


def test_failed_apply_does_not_consume_instance_id() -> None:
    lifecycle = StateLifecycleSystem()
    context = make_context()
    context.current_round = 1
    context.current_phase = "UNIT_ACTION"

    with pytest.raises(ValueError, match="both be set"):
        lifecycle.apply(
            context,
            state_id="test_state",
            owner_id="b1",
            expires_round=2,
        )

    instance = lifecycle.apply(
        context,
        state_id="test_state",
        owner_id="b1",
    )
    assert instance.instance_id == "state-000001"


def test_permanent_state_does_not_expire_automatically() -> None:
    lifecycle = StateLifecycleSystem()
    context = make_context()
    instance = lifecycle.apply(
        context,
        state_id="test_state",
        owner_id="b1",
        source_id="a1",
    )

    assert lifecycle.expire_at(context, round_no=1, phase="ROUND_START") == []
    assert lifecycle.expire_at(context, round_no=1, phase="ROUND_END") == []
    assert context.states.get(instance.instance_id) is instance


def test_round_start_and_round_end_expiry_remove_instances_and_publish_events() -> None:
    lifecycle = StateLifecycleSystem()
    context = make_context()
    context.current_round = 1
    context.current_phase = "UNIT_ACTION"

    round_start = lifecycle.apply(
        context,
        state_id="test_state",
        owner_id="b1",
        source_id="a1",
        expires_round=2,
        expires_phase="ROUND_START",
    )
    round_end = lifecycle.apply(
        context,
        state_id="test_state",
        owner_id="b1",
        source_id="a1",
        expires_round=2,
        expires_phase="ROUND_END",
    )

    expired_start = lifecycle.expire_at(
        context,
        round_no=2,
        phase="ROUND_START",
    )
    assert expired_start == [round_start]
    assert context.states.find() == [round_end]

    expired_end = lifecycle.expire_at(
        context,
        round_no=2,
        phase="ROUND_END",
    )
    assert expired_end == [round_end]
    assert context.states.find() == []

    expired_events = [
        event
        for event in context.event_bus.history
        if event.event_type is EventType.STATE_EXPIRED
    ]
    assert [event.payload["instance_id"] for event in expired_events] == [
        "state-000001",
        "state-000002",
    ]
    assert [event.phase for event in expired_events] == ["ROUND_START", "ROUND_END"]


def test_explicit_remove_uses_distinct_removed_event() -> None:
    lifecycle = StateLifecycleSystem()
    context = make_context()
    instance = lifecycle.apply(
        context,
        state_id="test_state",
        owner_id="b1",
        source_id=None,
    )

    removed = lifecycle.remove(context, instance.instance_id)
    assert removed is instance
    assert not context.states.has(owner_id="b1", state_id="test_state")

    event = context.event_bus.history[-1]
    assert event.event_type is EventType.STATE_REMOVED
    assert event.actor_id is None
    assert event.target_id == "b1"


def test_lifecycle_does_not_modify_unit_runtime_or_consume_randomness() -> None:
    lifecycle = StateLifecycleSystem()
    context = make_context(seed=123)
    owner = context.get_unit("b1")
    snapshot_before = owner.snapshot()
    expected_random = RandomSystem(123).random()

    instance = lifecycle.apply(
        context,
        state_id="test_state",
        owner_id="b1",
        source_id="a1",
    )
    lifecycle.remove(context, instance.instance_id)

    assert owner.snapshot() == snapshot_before
    assert context.random.random() == expected_random
