from __future__ import annotations

from dataclasses import dataclass

from .skill_definition import SkillDefinition


@dataclass(slots=True)
class SkillRuntime:
    """某携带者在当前战斗中的最小技能运行事实。"""

    definition: SkillDefinition
    owner_id: str
    enabled: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.definition, SkillDefinition):
            raise TypeError("definition must be a SkillDefinition")
        if not isinstance(self.owner_id, str) or not self.owner_id.strip():
            raise ValueError("owner_id cannot be empty")
        if not isinstance(self.enabled, bool):
            raise TypeError("enabled must be a bool")
