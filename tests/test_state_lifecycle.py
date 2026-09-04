from __future__ import annotations

import pytest

from sgs_v2.battle_core import (
    BattleContext,
    BattlePhase,
    EventBus,
    EventType,
    LineupPosition,
    RandomSystem,
    StateDefinition,
    StateLifecycleSystem,
    UnitRuntime,
)


def make_context(seed: int = 7) -> BattleContext:
    units = {
        "a1": UnitRuntime(
            unit_id="a1",
            name="A1",
            team_id="A",
            max_troops=1000,
            troops=1000,
            attack=100,
            defense=100,
            speed=100,
            intelligence=100,
            lineup_position=LineupPosition.COMMANDER,
        ),
        "b1": UnitRuntime(
            unit_id="b1",
            name="B1",
            team_id="B",
            max_troops=1000,
            troops=1000,
            attack=100,
            defense=100,
            speed=100,
            intelligence=100,
            lineup_position=LineupPosition.COMMANDER,
        ),
    }
    context = BattleContext(
        battle_id=f"state-lifecycle-{seed}",
        units=units,
        event_bus=EventBus(),
        random=RandomSystem(seed=seed),
    )
    context.states.register_definition(
        StateDefinition(state_id="test_state", name="测试状态")
    )
    context.current_round = 1
    context.current_phase = BattlePhase.ACTION_ORDER.value
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


def test_apply_rejects_unreachable_expiration_anchors() -> None:
    lifecycle = StateLifecycleSystem()
    context = make_context()

    with pytest.raises(ValueError, match="future lifecycle node"):
        lifecycle.apply(
            context,
            state_id="test_state",
            owner_id="b1",
            source_id="a1",
            expires_round=1,
            expires_phase=BattlePhase.ROUND_START.value,
        )

    context.current_round = 0
    context.current_phase = "NOT_STARTED"
    with pytest.raises(ValueError, match="expires_round must be >= 1"):
        lifecycle.apply(
            context,
            state_id="test_state",
            owner_id="b1",
            source_id="a1",
            expires_round=0,
            expires_phase=BattlePhase.ROUND_START.value,
        )


def test_apply_allows_same_round_future_round_end_anchor() -> None:
    lifecycle = StateLifecycleSystem()
    context = make_context()

    instance = lifecycle.apply(
        context,
        state_id="test_state",
        owner_id="b1",
        source_id="a1",
        expires_round=1,
        expires_phase=BattlePhase.ROUND_END.value,
    )

    assert instance.expires_round == 1
    assert instance.expires_phase == BattlePhase.ROUND_END.value


def test_apply_creates_deterministic_instance_and_event() -> None:
    lifecycle = StateLifecycleSystem()
    context = make_context()

    instance = lifecycle.apply(
        context,
        state_id="test_state",
        owner_id="b1",
        source_id="a1",
        source_skill_id="skill-001",
        expires_round=3,
        expires_phase=BattlePhase.ROUND_START.value,
    )

    assert instance.instance_id == "state-000001"
    assert context.states.get(instance.instance_id) == instance

    event = context.event_bus.history[-1]
    assert event.event_type is EventType.STATE_APPLIED
    assert event.actor_id == "a1"
    assert event.target_id == "b1"
    assert event.payload == {
        "instance_id": "state-000001",
        "state_id": "test_state",
        "owner_id": "b1",
        "source_id": "a1",
        "source_skill_id": "skill-001",
        "applied_round": 1,
        "applied_phase": BattlePhase.ACTION_ORDER.value,
        "expires_round": 3,
        "expires_phase": BattlePhase.ROUND_START.value,
        "runtime_params_type": "EmptyStateRuntimeParams",
        "runtime_params": {},
    }


def test_permanent_state_does_not_expire() -> None:
    lifecycle = StateLifecycleSystem()
    context = make_context()
    instance = lifecycle.apply(
        context,
        state_id="test_state",
        owner_id="b1",
        source_id="a1",
    )

    assert lifecycle.expire_at(
        context,
        round_no=8,
        phase=BattlePhase.ROUND_END.value,
    ) == []
    assert context.states.get(instance.instance_id) == instance


def test_round_start_and_round_end_expiration_publish_expired_events() -> None:
    lifecycle = StateLifecycleSystem()
    context = make_context()
    start_instance = lifecycle.apply(
        context,
        state_id="test_state",
        owner_id="b1",
        source_id="a1",
        expires_round=2,
        expires_phase=BattlePhase.ROUND_START.value,
    )
    end_instance = lifecycle.apply(
        context,
        state_id="test_state",
        owner_id="b1",
        source_id="a1",
        expires_round=2,
        expires_phase=BattlePhase.ROUND_END.value,
    )

    expired_start = lifecycle.expire_at(
        context,
        round_no=2,
        phase=BattlePhase.ROUND_START.value,
    )
    assert expired_start == [start_instance]
    assert context.states.states_of("b1") == [end_instance]

    expired_end = lifecycle.expire_at(
        context,
        round_no=2,
        phase=BattlePhase.ROUND_END.value,
    )
    assert expired_end == [end_instance]
    assert context.states.states_of("b1") == []

    expired_events = [
        event
        for event in context.event_bus.history
        if event.event_type is EventType.STATE_EXPIRED
    ]
    assert [event.payload["instance_id"] for event in expired_events] == [
        start_instance.instance_id,
        end_instance.instance_id,
    ]


def test_explicit_remove_publishes_removed_not_expired() -> None:
    lifecycle = StateLifecycleSystem()
    context = make_context()
    instance = lifecycle.apply(
        context,
        state_id="test_state",
        owner_id="b1",
        source_id="a1",
    )

    removed = lifecycle.remove(context, instance.instance_id)
    assert removed == instance

    event_types = [event.event_type for event in context.event_bus.history]
    assert event_types[-1] is EventType.STATE_REMOVED
    assert EventType.STATE_EXPIRED not in event_types


def test_lifecycle_does_not_modify_unit_runtime_combat_values() -> None:
    lifecycle = StateLifecycleSystem()
    context = make_context()
    owner = context.get_unit("b1")
    before = (
        owner.troops,
        owner.attack,
        owner.defense,
        owner.intelligence,
        owner.speed,
    )

    instance = lifecycle.apply(
        context,
        state_id="test_state",
        owner_id="b1",
        source_id="a1",
        expires_round=1,
        expires_phase=BattlePhase.ROUND_END.value,
    )
    lifecycle.remove(context, instance.instance_id)

    after = (
        owner.troops,
        owner.attack,
        owner.defense,
        owner.intelligence,
        owner.speed,
    )
    assert after == before
