from __future__ import annotations

from dataclasses import dataclass

from .state_runtime_params import EmptyStateRuntimeParams, StateRuntimeParams


@dataclass(frozen=True, slots=True)
class StateDefinition:
    """一种战斗状态的静态定义，不包含任何运行时效果。"""

    state_id: str
    name: str
    tags: frozenset[str] = frozenset()
    runtime_params_type: type[StateRuntimeParams] = EmptyStateRuntimeParams

    def __post_init__(self) -> None:
        if not self.state_id:
            raise ValueError("state_id cannot be empty")
        if not self.name:
            raise ValueError("state name cannot be empty")
        if not isinstance(self.runtime_params_type, type) or not issubclass(
            self.runtime_params_type, StateRuntimeParams
        ):
            raise TypeError(
                "runtime_params_type must be a StateRuntimeParams subclass"
            )

        object.__setattr__(self, "tags", frozenset(self.tags))
