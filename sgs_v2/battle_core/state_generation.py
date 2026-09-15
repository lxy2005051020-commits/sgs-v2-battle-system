from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .skill_runtime import SkillSlot
from .state_runtime_params import StateRuntimeParams

if TYPE_CHECKING:
    from .stage10_state_params import (
        FrozenContinuousDamageBasis,
        RecoveryPotencyContext,
    )


def _forbid_ordering(cls_name: str, op: str) -> None:
    raise TypeError(
        f"{cls_name} does not support comparison operator '{op}'. "
        "Generation IDs cannot be used as gameplay ordering or priority comparators."
    )


@dataclass(frozen=True, slots=True, order=False)
class StateApplicationGenerationId:
    """
    Immutable typed identity of a single successful state application or refresh generation.
    Distinct from physical StateInstance.instance_id.
    """

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError(
                f"StateApplicationGenerationId value must be a str, got {type(self.value)}"
            )
        if not self.value.strip():
            raise ValueError("StateApplicationGenerationId value cannot be empty or whitespace")

    def __str__(self) -> str:
        return self.value

    def __lt__(self, other: Any) -> bool:
        _forbid_ordering("StateApplicationGenerationId", "<")

    def __le__(self, other: Any) -> bool:
        _forbid_ordering("StateApplicationGenerationId", "<=")

    def __gt__(self, other: Any) -> bool:
        _forbid_ordering("StateApplicationGenerationId", ">")

    def __ge__(self, other: Any) -> bool:
        _forbid_ordering("StateApplicationGenerationId", ">=")


@dataclass(frozen=True, slots=True)
class PersistentLifecycleWindow:
    """
    Immutable lifecycle window metadata for a persistent state generation (STAGE10.md §7.1).
    """

    application_phase: str
    application_round: int
    first_eligible_round: int
    last_eligible_round: int
    max_opportunities_per_owner_round: int = 1

    def __post_init__(self) -> None:
        if not isinstance(self.application_phase, str) or not self.application_phase.strip():
            raise ValueError("application_phase cannot be empty or whitespace")
        if not isinstance(self.application_round, int) or isinstance(self.application_round, bool):
            raise TypeError("application_round must be an int")
        if self.application_round < 0:
            raise ValueError("application_round must be >= 0")
        if not isinstance(self.first_eligible_round, int) or isinstance(self.first_eligible_round, bool):
            raise TypeError("first_eligible_round must be an int")
        if self.first_eligible_round < 1:
            raise ValueError("first_eligible_round must be >= 1")
        if not isinstance(self.last_eligible_round, int) or isinstance(self.last_eligible_round, bool):
            raise TypeError("last_eligible_round must be an int")
        if self.last_eligible_round < self.first_eligible_round:
            raise ValueError("last_eligible_round must be >= first_eligible_round")
        if self.max_opportunities_per_owner_round != 1:
            raise ValueError("max_opportunities_per_owner_round must be exactly 1")

    def is_round_eligible(self, current_round: int) -> bool:
        return self.first_eligible_round <= current_round <= self.last_eligible_round

    def is_expired(self, current_round: int) -> bool:
        return current_round >= self.last_eligible_round


class StateGenerationAllocator:
    """
    Deterministic allocator for StateApplicationGenerationId.
    Single authoritative owner of generation identity allocation in BattleContext.
    """

    __slots__ = ("_generation_seq",)

    def __init__(self, initial_seq: int = 0) -> None:
        self._generation_seq = initial_seq

    def allocate(self, prefix: str = "gen") -> StateApplicationGenerationId:
        self._generation_seq += 1
        return StateApplicationGenerationId(f"{prefix}_{self._generation_seq}")


@dataclass(frozen=True, slots=True)
class StateGenerationSnapshot:
    """
    Immutable snapshot of application-time state generation facts (STAGE10.md §13.1).
    Captured when an opportunity is collected or generation is established.
    Work produced by this generation must NEVER JIT-read future generation params.
    """

    physical_instance_id: str
    application_generation_id: StateApplicationGenerationId
    state_id: str
    owner_id: str
    source_id: str | None = None
    source_skill_id: str | None = None
    source_skill_slot: SkillSlot | None = None
    runtime_params: StateRuntimeParams | None = None
    lifecycle_window: PersistentLifecycleWindow | None = None
    frozen_damage_basis: FrozenContinuousDamageBasis | None = None
    recovery_potency_context: RecoveryPotencyContext | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.physical_instance_id, str) or not self.physical_instance_id.strip():
            raise ValueError("physical_instance_id cannot be empty or whitespace")
        if not isinstance(self.application_generation_id, StateApplicationGenerationId):
            raise TypeError(
                f"application_generation_id must be a StateApplicationGenerationId, got {type(self.application_generation_id)}"
            )
        if not isinstance(self.state_id, str) or not self.state_id.strip():
            raise ValueError("state_id cannot be empty or whitespace")
        if not isinstance(self.owner_id, str) or not self.owner_id.strip():
            raise ValueError("owner_id cannot be empty or whitespace")
        if self.source_id is not None and (not isinstance(self.source_id, str) or not self.source_id.strip()):
            raise ValueError("source_id cannot be empty or whitespace when provided")
        if self.source_skill_id is not None and (not isinstance(self.source_skill_id, str) or not self.source_skill_id.strip()):
            raise ValueError("source_skill_id cannot be empty or whitespace when provided")
        if self.source_skill_slot is not None and not isinstance(self.source_skill_slot, SkillSlot):
            raise TypeError(f"source_skill_slot must be a SkillSlot or None, got {type(self.source_skill_slot)}")
        if self.runtime_params is not None and not isinstance(self.runtime_params, StateRuntimeParams):
            raise TypeError(f"runtime_params must be a StateRuntimeParams or None, got {type(self.runtime_params)}")
        if self.lifecycle_window is not None and not isinstance(self.lifecycle_window, PersistentLifecycleWindow):
            raise TypeError(f"lifecycle_window must be a PersistentLifecycleWindow or None, got {type(self.lifecycle_window)}")
