from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from .skill_definition import SkillDefinition


class SkillSlot(IntEnum):
    """Authoritative holder-specific runtime skill slot domain {0, 1, 2}."""

    INHERENT = 0
    LEARNED_1 = 1
    LEARNED_2 = 2


@dataclass(frozen=True, slots=True)
class LoadedSkillRef:
    """Holder-specific loaded skill provenance."""

    owner_id: str
    definition: SkillDefinition
    skill_slot: SkillSlot

    def __post_init__(self) -> None:
        if not isinstance(self.owner_id, str) or not self.owner_id.strip():
            raise ValueError("owner_id cannot be empty")
        if not isinstance(self.definition, SkillDefinition):
            raise TypeError("definition must be a SkillDefinition")
        if not isinstance(self.skill_slot, SkillSlot):
            raise TypeError(f"skill_slot must be a SkillSlot, got {type(self.skill_slot)}")


@dataclass(frozen=True, slots=True)
class LoadedSkillSet:
    """Validated loadout collection for a specific holder."""

    owner_id: str
    loaded: tuple[LoadedSkillRef, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.owner_id, str) or not self.owner_id.strip():
            raise ValueError("owner_id cannot be empty")
        if not isinstance(self.loaded, tuple):
            object.__setattr__(self, "loaded", tuple(self.loaded))
        seen_slots: set[SkillSlot] = set()
        for ref in self.loaded:
            if not isinstance(ref, LoadedSkillRef):
                raise TypeError(f"All items in loaded must be LoadedSkillRef, got {type(ref)}")
            if ref.owner_id != self.owner_id:
                raise ValueError(
                    f"LoadedSkillRef owner_id '{ref.owner_id}' does not match LoadedSkillSet owner_id '{self.owner_id}'"
                )
            if ref.skill_slot in seen_slots:
                raise ValueError(
                    f"Duplicate SkillSlot {ref.skill_slot} for owner '{self.owner_id}'"
                )
            seen_slots.add(ref.skill_slot)


@dataclass(slots=True)
class SkillRuntime:
    """某携带者在当前战斗中的最小技能运行事实。"""

    definition: SkillDefinition
    owner_id: str
    skill_slot: SkillSlot | None = None
    enabled: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.definition, SkillDefinition):
            raise TypeError("definition must be a SkillDefinition")
        if not isinstance(self.owner_id, str) or not self.owner_id.strip():
            raise ValueError("owner_id cannot be empty")
        if self.skill_slot is not None and not isinstance(self.skill_slot, SkillSlot):
            raise TypeError(f"skill_slot must be a SkillSlot or None, got {type(self.skill_slot)}")
        if not isinstance(self.enabled, bool):
            raise TypeError("enabled must be a bool")

    @classmethod
    def from_loaded(
        cls,
        ref: LoadedSkillRef,
        *,
        enabled: bool = True,
    ) -> SkillRuntime:
        if not isinstance(ref, LoadedSkillRef):
            raise TypeError(f"ref must be a LoadedSkillRef, got {type(ref)}")
        return cls(
            definition=ref.definition,
            owner_id=ref.owner_id,
            skill_slot=ref.skill_slot,
            enabled=enabled,
        )


