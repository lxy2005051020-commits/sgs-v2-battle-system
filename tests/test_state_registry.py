from __future__ import annotations

import pytest

from sgs_v2.battle_core import StateDefinition, StateInstance, StateRegistry


def make_instance(
    instance_id: str,
    *,
    owner_id: str = "b1",
    source_id: str | None = "a1",
) -> StateInstance:
    return StateInstance(
        instance_id=instance_id,
        state_id="test_state",
        owner_id=owner_id,
        source_id=source_id,
        source_skill_id="test_skill",
        applied_round=1,
        applied_phase="ACTION_ORDER",
        expires_round=3,
        expires_phase="ROUND_START",
    )


def make_registry() -> StateRegistry:
    registry = StateRegistry()
    registry.register_definition(
        StateDefinition(state_id="test_state", name="测试状态")
    )
    return registry


def test_definition_registration_and_duplicate_rejection() -> None:
    registry = StateRegistry()
    definition = StateDefinition(state_id="test_state", name="测试状态")

    registry.register_definition(definition)
    assert registry.get_definition("test_state") == definition

    with pytest.raises(ValueError, match="already registered"):
        registry.register_definition(
            StateDefinition(state_id="test_state", name="另一个定义")
        )


def test_instance_add_query_and_remove() -> None:
    registry = make_registry()
    instance = make_instance("state-000001")

    registry.add(instance)

    assert registry.get(instance.instance_id) == instance
    assert registry.states_of("b1") == [instance]
    assert registry.find(state_id="test_state") == [instance]
    assert registry.find(source_id="a1") == [instance]
    assert registry.has(owner_id="b1", state_id="test_state") is True

    assert registry.remove(instance.instance_id) == instance
    assert registry.has(owner_id="b1", state_id="test_state") is False

    with pytest.raises(KeyError, match="unknown state instance"):
        registry.remove(instance.instance_id)


def test_same_state_multiple_instances_coexist_in_stable_order() -> None:
    registry = make_registry()
    first = make_instance("state-000001", source_id="a1")
    second = make_instance("state-000002", source_id="a2")

    registry.add(first)
    registry.add(second)

    assert registry.states_of("b1") == [first, second]
    assert registry.find(state_id="test_state") == [first, second]

    result = registry.states_of("b1")
    result.clear()
    assert registry.states_of("b1") == [first, second]


def test_instance_ids_are_deterministic_and_do_not_use_randomness() -> None:
    first = StateRegistry()
    second = StateRegistry()

    assert [first.next_instance_id() for _ in range(3)] == [
        "state-000001",
        "state-000002",
        "state-000003",
    ]
    assert [second.next_instance_id() for _ in range(3)] == [
        "state-000001",
        "state-000002",
        "state-000003",
    ]


def test_instance_requires_complete_valid_expiration_anchor() -> None:
    with pytest.raises(ValueError, match="both be set"):
        StateInstance(
            instance_id="state-000001",
            state_id="test_state",
            owner_id="b1",
            source_id=None,
            source_skill_id=None,
            applied_round=1,
            applied_phase="ACTION_ORDER",
            expires_round=2,
            expires_phase=None,
        )

    with pytest.raises(ValueError, match="ROUND_START or ROUND_END"):
        StateInstance(
            instance_id="state-000001",
            state_id="test_state",
            owner_id="b1",
            source_id=None,
            source_skill_id=None,
            applied_round=1,
            applied_phase="ACTION_ORDER",
            expires_round=2,
            expires_phase="UNIT_ACTION_END",
        )
