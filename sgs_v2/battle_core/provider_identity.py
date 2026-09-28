from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias

from .skill_runtime import SkillRuntime, SkillSlot


@dataclass(frozen=True, slots=True)
class SkillProviderRef:
    """Stable identity for one loaded skill provider."""

    owner_id: str
    skill_slot: SkillSlot
    skill_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.owner_id, str) or not self.owner_id.strip():
            raise ValueError("owner_id cannot be empty or whitespace")
        if not isinstance(self.skill_slot, SkillSlot):
            raise TypeError(f"skill_slot must be a SkillSlot, got {type(self.skill_slot)}")
        if not isinstance(self.skill_id, str) or not self.skill_id.strip():
            raise ValueError("skill_id cannot be empty or whitespace")


@dataclass(frozen=True, slots=True)
class EquipmentProviderRef:
    """Stable identity for a non-skill equipment contribution provider."""

    owner_id: str
    provider_key: str

    def __post_init__(self) -> None:
        if not isinstance(self.owner_id, str) or not self.owner_id.strip():
            raise ValueError("owner_id cannot be empty or whitespace")
        if not isinstance(self.provider_key, str) or not self.provider_key.strip():
            raise ValueError("provider_key cannot be empty or whitespace")


ProviderRef: TypeAlias = SkillProviderRef | EquipmentProviderRef


class ProviderResolutionStatus(str, Enum):
    FOUND = "FOUND"
    MISSING = "MISSING"
    IDENTITY_MISMATCH = "IDENTITY_MISMATCH"


@dataclass(frozen=True, slots=True)
class SkillProviderResolution:
    provider_ref: SkillProviderRef
    status: ProviderResolutionStatus
    runtime: SkillRuntime | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.provider_ref, SkillProviderRef):
            raise TypeError("provider_ref must be a SkillProviderRef")
        if not isinstance(self.status, ProviderResolutionStatus):
            raise TypeError("status must be a ProviderResolutionStatus")
        if self.status is ProviderResolutionStatus.FOUND:
            if not isinstance(self.runtime, SkillRuntime):
                raise TypeError("FOUND resolution requires a SkillRuntime")
        elif self.runtime is not None:
            raise ValueError("non-FOUND resolution cannot carry a runtime")
