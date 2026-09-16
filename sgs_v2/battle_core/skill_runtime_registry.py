from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from .skill_runtime import SkillRuntime, SkillSlot

if TYPE_CHECKING:
    pass


class PersistentSourceSkillGateMode(str, Enum):
    """
    Authoritative Stage 10 source-skill gating mode (STAGE10.md §12).
    - ALWAYS_ACTIVE: State existence itself authorizes source-side persistence (e.g. DOT ticks, active skill buffs).
    - QUERY_SKILL_RUNTIME: Queries authoritative SkillRuntime.enabled JIT (e.g. passive/command FIRST_AID or RECUPERATION).
    - EXTERNAL_LIFECYCLE: External owner controls physical state lifecycle.
    """

    ALWAYS_ACTIVE = "ALWAYS_ACTIVE"
    QUERY_SKILL_RUNTIME = "QUERY_SKILL_RUNTIME"
    EXTERNAL_LIFECYCLE = "EXTERNAL_LIFECYCLE"


@dataclass(frozen=True, slots=True)
class PersistentSourceSkillGate:
    """
    Typed configuration for evaluating source skill runtime status at opportunity execution time.
    """

    mode: PersistentSourceSkillGateMode = PersistentSourceSkillGateMode.ALWAYS_ACTIVE

    def __post_init__(self) -> None:
        if not isinstance(self.mode, PersistentSourceSkillGateMode):
            raise TypeError(
                f"mode must be a PersistentSourceSkillGateMode, got {type(self.mode)}"
            )

    @classmethod
    def always_active(cls) -> PersistentSourceSkillGate:
        return cls(PersistentSourceSkillGateMode.ALWAYS_ACTIVE)

    @classmethod
    def query_skill_runtime(cls) -> PersistentSourceSkillGate:
        return cls(PersistentSourceSkillGateMode.QUERY_SKILL_RUNTIME)

    @classmethod
    def external_lifecycle(cls) -> PersistentSourceSkillGate:
        return cls(PersistentSourceSkillGateMode.EXTERNAL_LIFECYCLE)


class SkillRuntimeRegistry:
    """
    Battle-scoped authoritative registry of loaded skill runtimes (STAGE10.md §11).
    Primary key: (owner_id, SkillSlot).
    Invariant: source unit defeat does NOT remove or mutate SkillRuntime entries.
    """

    __slots__ = ("_runtimes",)

    def __init__(self) -> None:
        self._runtimes: dict[tuple[str, SkillSlot], SkillRuntime] = {}

    def register(self, runtime: SkillRuntime, *, slot: SkillSlot | None = None) -> None:
        """
        Register an authoritative SkillRuntime reference.
        Duplicate (owner_id, slot) registration is strictly rejected.
        """
        if not isinstance(runtime, SkillRuntime):
            raise TypeError(f"runtime must be a SkillRuntime, got {type(runtime)}")

        target_slot = slot if slot is not None else runtime.skill_slot
        if target_slot is None:
            raise ValueError(
                f"SkillSlot is required to register SkillRuntime for owner '{runtime.owner_id}'"
            )
        if not isinstance(target_slot, SkillSlot):
            raise TypeError(f"slot must be a SkillSlot, got {type(target_slot)}")

        key = (runtime.owner_id, target_slot)
        if key in self._runtimes:
            raise ValueError(
                f"Duplicate SkillRuntime registration for owner '{runtime.owner_id}' "
                f"at slot {target_slot.name}"
            )

        self._runtimes[key] = runtime

    def lookup(
        self,
        owner_id: str,
        slot: SkillSlot,
        expected_skill_id: str | None = None,
    ) -> SkillRuntime:
        """
        Look up the authoritative SkillRuntime for (owner_id, slot).
        Validates existence and expected skill_id invariant.
        """
        if not isinstance(owner_id, str) or not owner_id.strip():
            raise ValueError("owner_id cannot be empty or whitespace")
        if not isinstance(slot, SkillSlot):
            raise TypeError(f"slot must be a SkillSlot, got {type(slot)}")

        key = (owner_id, slot)
        try:
            runtime = self._runtimes[key]
        except KeyError as exc:
            raise KeyError(
                f"No SkillRuntime registered for owner '{owner_id}' at slot {slot.name}"
            ) from exc

        if expected_skill_id is not None:
            if runtime.definition.skill_id != expected_skill_id:
                raise ValueError(
                    f"SkillRuntime skill_id mismatch for owner '{owner_id}' slot {slot.name}: "
                    f"expected '{expected_skill_id}', got '{runtime.definition.skill_id}'"
                )

        return runtime

    def get(self, owner_id: str, slot: SkillSlot) -> SkillRuntime | None:
        """Safe lookup returning None if not registered."""
        if not isinstance(slot, SkillSlot):
            return None
        return self._runtimes.get((owner_id, slot))

    def contains(self, owner_id: str, slot: SkillSlot) -> bool:
        """Check if a runtime is registered for (owner_id, slot)."""
        return (owner_id, slot) in self._runtimes

    def __contains__(self, key: tuple[str, SkillSlot]) -> bool:
        return key in self._runtimes

    def __len__(self) -> int:
        return len(self._runtimes)
