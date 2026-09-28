from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from .enums import BattlePhase


class StateLifetimeDomain(str, Enum):
    ROUND_CALENDAR = "ROUND_CALENDAR"
    HOLDER_ACTION_WINDOW = "HOLDER_ACTION_WINDOW"
    EXPLICIT_PHASE_EXPIRY = "EXPLICIT_PHASE_EXPIRY"


_PHASE_EXPIRY_VALUES = frozenset(
    {
        BattlePhase.ROUND_START.value,
        BattlePhase.ROUND_END.value,
    }
)


@dataclass(frozen=True, slots=True)
class StateLifetimeSpec:
    """Typed physical lifetime metadata for Shared Foundation states.

    This object describes physical residency only. Behavioral counters such as
    STUN.remaining_blocks remain in their owning runtime params and are never
    interpreted as a generic lifetime countdown.
    """

    domain: StateLifetimeDomain
    expires_round: int | None = None
    expires_phase: str | None = None
    remaining_holder_action_windows: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.domain, StateLifetimeDomain):
            raise TypeError("domain must be a StateLifetimeDomain")

        if self.domain in (
            StateLifetimeDomain.ROUND_CALENDAR,
            StateLifetimeDomain.EXPLICIT_PHASE_EXPIRY,
        ):
            if self.remaining_holder_action_windows is not None:
                raise ValueError(
                    "round/phase lifetime cannot carry holder action windows"
                )
            if not isinstance(self.expires_round, int) or isinstance(
                self.expires_round, bool
            ):
                raise TypeError("expires_round must be an int for round/phase lifetime")
            if self.expires_round < 1:
                raise ValueError("expires_round must be >= 1")
            if self.expires_phase not in _PHASE_EXPIRY_VALUES:
                raise ValueError("expires_phase must be ROUND_START or ROUND_END")
            return

        if self.domain is StateLifetimeDomain.HOLDER_ACTION_WINDOW:
            if self.expires_round is not None or self.expires_phase is not None:
                raise ValueError(
                    "holder action-window lifetime cannot carry round/phase expiry"
                )
            if not isinstance(self.remaining_holder_action_windows, int) or isinstance(
                self.remaining_holder_action_windows, bool
            ):
                raise TypeError(
                    "remaining_holder_action_windows must be an int for holder action-window lifetime"
                )
            if self.remaining_holder_action_windows < 1:
                raise ValueError("remaining_holder_action_windows must be >= 1")
            return

        raise ValueError(f"unsupported lifetime domain: {self.domain}")

    @classmethod
    def round_calendar(
        cls,
        *,
        expires_round: int,
        expires_phase: str = BattlePhase.ROUND_END.value,
    ) -> "StateLifetimeSpec":
        return cls(
            domain=StateLifetimeDomain.ROUND_CALENDAR,
            expires_round=expires_round,
            expires_phase=expires_phase,
        )

    @classmethod
    def holder_action_window(cls, windows: int) -> "StateLifetimeSpec":
        return cls(
            domain=StateLifetimeDomain.HOLDER_ACTION_WINDOW,
            remaining_holder_action_windows=windows,
        )

    @classmethod
    def explicit_phase_expiry(
        cls,
        *,
        expires_round: int,
        expires_phase: str,
    ) -> "StateLifetimeSpec":
        return cls(
            domain=StateLifetimeDomain.EXPLICIT_PHASE_EXPIRY,
            expires_round=expires_round,
            expires_phase=expires_phase,
        )

    def is_due_at(self, *, round_no: int, phase: str) -> bool:
        if self.domain is StateLifetimeDomain.HOLDER_ACTION_WINDOW:
            return False
        return self.expires_round == round_no and self.expires_phase == phase

    def advance_holder_action_window(self) -> tuple["StateLifetimeSpec | None", bool]:
        """Advance one physical holder-action window and report whether it is due."""
        if self.domain is not StateLifetimeDomain.HOLDER_ACTION_WINDOW:
            return self, False
        remaining = self.remaining_holder_action_windows
        assert remaining is not None
        if remaining <= 1:
            return None, True
        return replace(self, remaining_holder_action_windows=remaining - 1), False
