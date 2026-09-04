from __future__ import annotations

from .state_definition import StateDefinition
from .state_instance import StateInstance


class StateRegistry:
    """一场战斗中的状态定义、实例存储与确定性查询中心。"""

    def __init__(self) -> None:
        self._definitions: dict[str, StateDefinition] = {}
        self._instances: dict[str, StateInstance] = {}
        self._next_instance_sequence = 1

    def register_definition(self, definition: StateDefinition) -> None:
        if definition.state_id in self._definitions:
            raise ValueError(
                f"state definition already registered: {definition.state_id}"
            )
        self._definitions[definition.state_id] = definition

    def get_definition(self, state_id: str) -> StateDefinition:
        try:
            return self._definitions[state_id]
        except KeyError as exc:
            raise KeyError(f"unknown state_id: {state_id}") from exc

    def next_instance_id(self) -> str:
        instance_id = f"state-{self._next_instance_sequence:06d}"
        self._next_instance_sequence += 1
        return instance_id

    def add(self, instance: StateInstance) -> StateInstance:
        if instance.state_id not in self._definitions:
            raise KeyError(f"unknown state_id: {instance.state_id}")
        if instance.instance_id in self._instances:
            raise ValueError(
                f"state instance already exists: {instance.instance_id}"
            )
        self._instances[instance.instance_id] = instance
        return instance

    def get(self, instance_id: str) -> StateInstance:
        try:
            return self._instances[instance_id]
        except KeyError as exc:
            raise KeyError(f"unknown state instance: {instance_id}") from exc

    def remove(self, instance_id: str) -> StateInstance:
        try:
            return self._instances.pop(instance_id)
        except KeyError as exc:
            raise KeyError(f"unknown state instance: {instance_id}") from exc

    def has(self, *, owner_id: str, state_id: str) -> bool:
        return any(
            instance.owner_id == owner_id and instance.state_id == state_id
            for instance in self._instances.values()
        )

    def find(
        self,
        *,
        owner_id: str | None = None,
        state_id: str | None = None,
        source_id: str | None = None,
    ) -> list[StateInstance]:
        return [
            instance
            for instance in self._instances.values()
            if (owner_id is None or instance.owner_id == owner_id)
            and (state_id is None or instance.state_id == state_id)
            and (source_id is None or instance.source_id == source_id)
        ]

    def states_of(self, owner_id: str) -> list[StateInstance]:
        return self.find(owner_id=owner_id)
