from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .operation_identity import DamageInstanceId, FinalizationId


def _forbid_ordering(cls_name: str, op: str) -> None:
    raise TypeError(
        f"{cls_name} does not support comparison operator '{op}'. "
        "Permit types cannot be used as gameplay ordering or priority comparators."
    )


class FutureBranchKind(str, Enum):
    """The exactly six global future branches in Stage9."""

    NEXT_ACTION = "NEXT_ACTION"
    ASSAULT = "ASSAULT"
    COMBO_SECOND_NORMAL_ATTACK = "COMBO_SECOND_NORMAL_ATTACK"
    COUNTER_BATCH = "COUNTER_BATCH"
    CHAIN_TRAVERSAL = "CHAIN_TRAVERSAL"
    CLEAVE_EFFECT = "CLEAVE_EFFECT"


class BattleTerminationState(str, Enum):
    """Semantic termination states owned exclusively by BattleFinalizationCoordinator."""

    RUNNING = "RUNNING"
    VICTORY_LATCHED = "VICTORY_LATCHED"
    DRAINING_ADMITTED_WORK = "DRAINING_ADMITTED_WORK"
    FINALIZED = "FINALIZED"


class LegacyFinalizationBarrier(str, Enum):
    """The six legacy macro checkpoints for compatibility observation."""

    INITIAL_SETTLED = "INITIAL_SETTLED"
    ROUND_START_HOOKS_SETTLED = "ROUND_START_HOOKS_SETTLED"
    UNIT_ACTION_START_HOOKS_SETTLED = "UNIT_ACTION_START_HOOKS_SETTLED"
    ACTION_SETTLED = "ACTION_SETTLED"
    ROUND_END_SETTLED = "ROUND_END_SETTLED"
    MAX_ROUND_SETTLED = "MAX_ROUND_SETTLED"


class PermitStatus(str, Enum):
    """Lifecycle status of a one-shot capability permit."""

    ISSUED = "ISSUED"
    CONSUMED = "CONSUMED"
    REVOKED = "REVOKED"


@dataclass(frozen=True, slots=True, order=False)
class FutureAdmissionPermit:
    """One-shot capability token required to allocate and admit a future branch."""

    permit_id: str
    branch_kind: FutureBranchKind
    parent_scope_identity: str
    termination_generation: int

    def __post_init__(self) -> None:
        if not isinstance(self.permit_id, str) or not self.permit_id.strip():
            raise ValueError("permit_id cannot be empty or whitespace")
        if not isinstance(self.branch_kind, FutureBranchKind):
            raise TypeError(f"branch_kind must be a FutureBranchKind, got {type(self.branch_kind)}")
        if not isinstance(self.parent_scope_identity, str) or not self.parent_scope_identity.strip():
            raise ValueError("parent_scope_identity cannot be empty or whitespace")
        if isinstance(self.termination_generation, bool) or not isinstance(self.termination_generation, int):
            raise TypeError("termination_generation must be an int")
        if self.termination_generation < 0:
            raise ValueError("termination_generation cannot be negative")

    def __lt__(self, other: Any) -> bool:
        _forbid_ordering("FutureAdmissionPermit", "<")

    def __le__(self, other: Any) -> bool:
        _forbid_ordering("FutureAdmissionPermit", "<=")

    def __gt__(self, other: Any) -> bool:
        _forbid_ordering("FutureAdmissionPermit", ">")

    def __ge__(self, other: Any) -> bool:
        _forbid_ordering("FutureAdmissionPermit", ">=")


@dataclass(frozen=True, slots=True, order=False)
class DamageSettlementPermit:
    """One-shot capability token required before destructive troop settlement of a DamageInstance."""

    permit_id: str
    damage_instance_id: DamageInstanceId

    def __post_init__(self) -> None:
        if not isinstance(self.permit_id, str) or not self.permit_id.strip():
            raise ValueError("permit_id cannot be empty or whitespace")
        if not isinstance(self.damage_instance_id, DamageInstanceId):
            raise TypeError(
                f"damage_instance_id must be DamageInstanceId, got {type(self.damage_instance_id)}"
            )

    def __lt__(self, other: Any) -> bool:
        _forbid_ordering("DamageSettlementPermit", "<")

    def __le__(self, other: Any) -> bool:
        _forbid_ordering("DamageSettlementPermit", "<=")

    def __gt__(self, other: Any) -> bool:
        _forbid_ordering("DamageSettlementPermit", ">")

    def __ge__(self, other: Any) -> bool:
        _forbid_ordering("DamageSettlementPermit", ">=")


@dataclass(frozen=True, slots=True, order=False)
class FinalizationProjectionPermit:
    """One-shot capability token required before legacy compatibility result/event projection."""

    permit_id: str
    finalization_id: FinalizationId

    def __post_init__(self) -> None:
        if not isinstance(self.permit_id, str) or not self.permit_id.strip():
            raise ValueError("permit_id cannot be empty or whitespace")
        if not isinstance(self.finalization_id, FinalizationId):
            raise TypeError(
                f"finalization_id must be FinalizationId, got {type(self.finalization_id)}"
            )

    def __lt__(self, other: Any) -> bool:
        _forbid_ordering("FinalizationProjectionPermit", "<")

    def __le__(self, other: Any) -> bool:
        _forbid_ordering("FinalizationProjectionPermit", "<=")

    def __gt__(self, other: Any) -> bool:
        _forbid_ordering("FinalizationProjectionPermit", ">")

    def __ge__(self, other: Any) -> bool:
        _forbid_ordering("FinalizationProjectionPermit", ">=")
