from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StateDefinition:
    """一种战斗状态的静态定义，不包含任何运行时效果。"""

    state_id: str
    name: str
    tags: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not self.state_id:
            raise ValueError("state_id cannot be empty")
        if not self.name:
            raise ValueError("state name cannot be empty")

        object.__setattr__(self, "tags", frozenset(self.tags))
