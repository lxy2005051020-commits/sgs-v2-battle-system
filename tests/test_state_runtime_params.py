from __future__ import annotations

from dataclasses import dataclass

import pytest

from sgs_v2.battle_core import (
    BattleContext,
    BattlePhase,
    EmptyStateRuntimeParams,
    EventBus,
    EventType,
    LineupPosition,
    RandomSystem,
    StateDefinition,
    StateLifecycleSystem,
    StateRuntimeParams,
    UnitRuntime,
)


@dataclass(frozen=True, slots=True)
class SampleStateParams(StateRuntimeParams):
    coefficient: float
    charges: int


def make_context() -> BattleContext:
    context = BattleContext(
        battle_id="stage5-state-params",
        units={
            "a1": UnitRuntime(
                "a1", "A1", "A", 1000, 1000, 100, 100, 100,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "b1": UnitRuntime(
                "b1", "B1", "B", 1000, 1000, 100, 100, 90,
                lineup_position=LineupPosition.COMMANDER,
            ),
        },
        event_bus=EventBus(),
        random=RandomSystem(5),
    )
    context.current_round = 1
    context.current_phase = BattlePhase.ACTION_ORDER.value
    return context


def test_default_state_runtime_params_preserve_stage3_compatibility() -> None:
    context = make_context()
    context.states.register_definition(
        StateDefinition(state_id="plain", name="普通测试状态")
    )

    instance = StateLifecycleSystem().apply(
        context,
        state_id="plain",
        owner_id="b1",
        source_id="a1",
    )

    assert isinstance(instance.runtime_params, EmptyStateRuntimeParams)
    event = context.event_bus.history[-1]
    assert event.event_type is EventType.STATE_APPLIED
    assert event.payload["runtime_params_type"] == "EmptyStateRuntimeParams"
    assert event.payload["runtime_params"] == {}


def test_definition_schema_accepts_matching_frozen_runtime_params() -> None:
    context = make_context()
    context.states.register_definition(
        StateDefinition(
            state_id="parameterized",
            name="参数测试状态",
            runtime_params_type=SampleStateParams,
        )
    )
    params = SampleStateParams(coefficient=1.25, charges=2)

    instance = StateLifecycleSystem().apply(
        context,
        state_id="parameterized",
        owner_id="b1",
        source_id="a1",
        source_skill_id="test-skill",
        runtime_params=params,
    )

    assert instance.runtime_params == params
    event = context.event_bus.history[-1]
    assert event.payload["runtime_params_type"] == "SampleStateParams"
    assert event.payload["runtime_params"] == {
        "coefficient": 1.25,
        "charges": 2,
    }


def test_definition_schema_rejects_wrong_or_missing_runtime_params() -> None:
    context = make_context()
    context.states.register_definition(
        StateDefinition(
            state_id="parameterized",
            name="参数测试状态",
            runtime_params_type=SampleStateParams,
        )
    )
    lifecycle = StateLifecycleSystem()

    with pytest.raises(TypeError, match="runtime_params type mismatch"):
        lifecycle.apply(
            context,
            state_id="parameterized",
            owner_id="b1",
            source_id="a1",
        )

    with pytest.raises(TypeError, match="runtime_params type mismatch"):
        lifecycle.apply(
            context,
            state_id="parameterized",
            owner_id="b1",
            source_id="a1",
            runtime_params=EmptyStateRuntimeParams(),
        )


def test_same_state_multiple_instances_can_carry_different_typed_params() -> None:
    context = make_context()
    context.states.register_definition(
        StateDefinition(
            state_id="parameterized",
            name="参数测试状态",
            runtime_params_type=SampleStateParams,
        )
    )
    lifecycle = StateLifecycleSystem()

    first = lifecycle.apply(
        context,
        state_id="parameterized",
        owner_id="b1",
        source_id="a1",
        runtime_params=SampleStateParams(coefficient=1.0, charges=1),
    )
    second = lifecycle.apply(
        context,
        state_id="parameterized",
        owner_id="b1",
        source_id="a1",
        runtime_params=SampleStateParams(coefficient=1.5, charges=3),
    )

    assert context.states.states_of("b1") == [first, second]
    assert first.runtime_params != second.runtime_params


def test_runtime_params_are_immutable() -> None:
    params = SampleStateParams(coefficient=1.0, charges=1)
    with pytest.raises(Exception):
        params.charges = 2  # type: ignore[misc]
