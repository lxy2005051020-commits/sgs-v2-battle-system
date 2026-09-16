from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol

from .enums import DamageType
from .operation_identity import SourceType
from .state_generation import StateApplicationGenerationId


class DamageHitTopology(str, Enum):
    """Authoritative hit topology enum (STAGE10.md §15.1)."""

    RESOLVED_HIT = "RESOLVED_HIT"
    NO_RESOLVED_HIT_EVASION_OR_MISS = "NO_RESOLVED_HIT_EVASION_OR_MISS"


class DamageZeroLossCause(str, Enum):
    """Authoritative zero-loss classification enum (STAGE10.md §15.1)."""

    WEAKNESS_ZERO = "WEAKNESS_ZERO"
    BARRIER_ZERO = "BARRIER_ZERO"
    SETTLED_ZERO = "SETTLED_ZERO"


@dataclass(frozen=True, slots=True)
class DamageAftermathFact:
    """
    Typed damage aftermath fact emitted after hit resolution & troop loss settlement.
    Required for FIRST_AID_AFTER_DAMAGE recovery opportunities (STAGE10.md §15.1).
    """

    damage_instance_id: str
    target_id: str
    source_type: SourceType
    damage_type: DamageType
    assigned_target_damage: int
    actual_target_troop_loss: int
    target_troops_after: int
    target_defeated: bool
    hit_topology: DamageHitTopology
    zero_loss_cause: DamageZeroLossCause | None = None
    source_state_generation: StateApplicationGenerationId | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.damage_instance_id, str) or not self.damage_instance_id.strip():
            raise ValueError("damage_instance_id cannot be empty or whitespace")
        if not isinstance(self.target_id, str) or not self.target_id.strip():
            raise ValueError("target_id cannot be empty or whitespace")
        if not isinstance(self.source_type, SourceType):
            raise TypeError(f"source_type must be a SourceType, got {type(self.source_type)}")
        if not isinstance(self.damage_type, DamageType):
            raise TypeError(f"damage_type must be a DamageType, got {type(self.damage_type)}")
        if isinstance(self.assigned_target_damage, bool) or not isinstance(
            self.assigned_target_damage, int
        ):
            raise TypeError("assigned_target_damage must be an int")
        if self.assigned_target_damage < 0:
            raise ValueError("assigned_target_damage must be >= 0")
        if isinstance(self.actual_target_troop_loss, bool) or not isinstance(
            self.actual_target_troop_loss, int
        ):
            raise TypeError("actual_target_troop_loss must be an int")
        if self.actual_target_troop_loss < 0:
            raise ValueError("actual_target_troop_loss must be >= 0")
        if isinstance(self.target_troops_after, bool) or not isinstance(
            self.target_troops_after, int
        ):
            raise TypeError("target_troops_after must be an int")
        if self.target_troops_after < 0:
            raise ValueError("target_troops_after must be >= 0")
        if not isinstance(self.target_defeated, bool):
            raise TypeError("target_defeated must be a bool")
        if not isinstance(self.hit_topology, DamageHitTopology):
            raise TypeError(
                f"hit_topology must be a DamageHitTopology, got {type(self.hit_topology)}"
            )
        if self.zero_loss_cause is not None and not isinstance(
            self.zero_loss_cause, DamageZeroLossCause
        ):
            raise TypeError(
                f"zero_loss_cause must be a DamageZeroLossCause or None, got {type(self.zero_loss_cause)}"
            )
        if self.source_state_generation is not None and not isinstance(
            self.source_state_generation, StateApplicationGenerationId
        ):
            raise TypeError(
                f"source_state_generation must be a StateApplicationGenerationId or None, got {type(self.source_state_generation)}"
            )


class DamageAftermathPort(Protocol):
    """
    Port interface for damage aftermath commitment (STAGE10.md §15, §23).
    Shared checkpoint across standard damage, periodic damage, counter, assault, and cleave.
    Formally integrated in Phase 6.
    """

    def commit_aftermath(self, context: Any, aftermath_fact: DamageAftermathFact) -> Any:
        ...
