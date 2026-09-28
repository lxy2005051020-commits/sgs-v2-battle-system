from __future__ import annotations

from dataclasses import dataclass


def _validate_round_no(round_no: int) -> None:
    if isinstance(round_no, bool) or not isinstance(round_no, int):
        raise TypeError("round_no must be an int")
    if round_no < 1:
        raise ValueError("round_no must be >= 1")


def _validate_actor_id(actor_id: str) -> None:
    if not isinstance(actor_id, str):
        raise TypeError("actor_id must be a str")
    if not actor_id.strip():
        raise ValueError("actor_id cannot be empty or whitespace")


@dataclass(frozen=True, slots=True)
class RoundStartHook:
    round_no: int

    def __post_init__(self) -> None:
        _validate_round_no(self.round_no)


@dataclass(frozen=True, slots=True)
class UnitActionStartHook:
    round_no: int
    actor_id: str

    def __post_init__(self) -> None:
        _validate_round_no(self.round_no)
        _validate_actor_id(self.actor_id)


RuleHook = RoundStartHook | UnitActionStartHook
