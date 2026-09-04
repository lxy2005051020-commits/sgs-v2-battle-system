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
        applied_phase="UNIT_ACTION",
        expires_round=3,
        expires_phase="ROUND_START",
    )


def make_registry() -> StateRegistry:
    registry = StateRegistry()
    registry.register_definition(StateDefinition("test_state", "测试状态"))
    return registry


def test_definition_registration_and_duplicate_rejection() -> None:
    registry = make_registry()
    assert registry.get_definition("test_state").name == "测试状态"

    with pytest.raises(ValueError, match="already registered"):
        registry.register_definition(StateDefinition("test_state", "另一个定义"))


def test_instance_validation_rejects_invalid_expiry_anchor() -> None:
    with pytest.raises(ValueError, match="both be set"):
        StateInstance(
            instance_id="state-000001",
            state_id="test_state",
            owner_id="b1",
            source_id=None,
            source_skill_id=None,
            applied_round=1,
            applied_phase="ROUND_START",
            expires_round=2,
        )

    with pytest.raises(ValueError, match="expires_round"):
        StateInstance(
            instance_id="state-000001",
            state_id="test_state",
            owner_id="b1",
            source_id=None,
            source_skill_id=None,
            applied_round=2,
            applied_phase="ROUND_START",
            expires_round=1,
            expires_phase="ROUND_END",
        )

    with pytest.raises(ValueError, match="ROUND_START or ROUND_END"):
        StateInstance(
            instance_id="state-000001",
            state_id="test_state",
            owner_id="b1",
            source_id=None,
            source_skill_id=None,
            applied_round=1,
            applied_phase="ROUND_START",
            expires_round=2,
            expires_phase="UNIT_ACTION_END",
        )


def test_registry_add_get_find_has_and_remove() -> None:
    registry = make_registry()
    first = make_instance("state-000001")
    second = make_instance("state-000002", owner_id="b2", source_id="a2")

    registry.add(first)
    registry.add(second)

    assert registry.get(first.instance_id) is first
    assert registry.has(owner_id="b1", state_id="test_state")
    assert registry.find(owner_id="b1") == [first]
    assert registry.find(state_id="test_state") == [first, second]
    assert registry.find(source_id="a2") == [second]
    assert registry.states_of("b2") == [second]

    returned = registry.find()
    returned.clear()
    assert registry.find() == [first, second]

    assert registry.remove(first.instance_id) is first
    assert not registry.has(owner_id="b1", state_id="test_state")


def test_registry_rejects_unknown_definition_and_duplicate_instance_id() -> None:
    registry = StateRegistry()
    unknown = make_instance("state-000001")
    with pytest.raises(KeyError, match="unknown state_id"):
        registry.add(unknown)

    registry.register_definition(StateDefinition("test_state", "测试状态"))
    registry.add(unknown)
    with pytest.raises(ValueError, match="already exists"):
        registry.add(unknown)


def test_remove_unknown_instance_is_explicit() -> None:
    registry = make_registry()
    with pytest.raises(KeyError, match="unknown state instance"):
        registry.remove("state-999999")


def test_same_state_can_have_multiple_instances_in_stable_order() -> None:
    registry = make_registry()
    instances = [
        make_instance("custom-a"),
        make_instance("custom-b"),
        make_instance("custom-c"),
    ]
    for instance in instances:
        registry.add(instance)

    assert registry.states_of("b1") == instances


def test_instance_ids_are_deterministic_and_skip_existing_ids() -> None:
    first = make_registry()
    second = make_registry()

    assert first.next_instance_id() == "state-000001"
    assert first.next_instance_id() == "state-000002"
    assert second.next_instance_id() == "state-000001"
    assert second.next_instance_id() == "state-000002"

    third = make_registry()
    third.add(make_instance("state-000001"))
    assert third.next_instance_id() == "state-000002"
