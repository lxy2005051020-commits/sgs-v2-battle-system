from __future__ import annotations


class ActionProgressTracker:
    """
    Battle-scoped progress tracker for action-start timing (STAGE10.md §9).
    Tracks when a unit reaches UNIT_ACTION_START timing in a specific combat round.
    Invariant: exactly one persistent action-start opportunity window per owner per round.
    Control effects (stun/amnesia) may suppress subsequent actions, but do NOT refund the window.
    """

    __slots__ = ("_consumed_action_starts", "_current_acting_unit")

    def __init__(self) -> None:
        self._consumed_action_starts: set[tuple[str, int]] = set()
        self._current_acting_unit: str | None = None

    @property
    def current_acting_unit(self) -> str | None:
        """The unit currently at the active action lifecycle node, if any."""
        return self._current_acting_unit

    def set_current_acting_unit(self, unit_id: str | None) -> None:
        """Set or clear the unit currently acting."""
        if unit_id is not None and (not isinstance(unit_id, str) or not unit_id.strip()):
            raise ValueError("unit_id cannot be empty or whitespace when provided")
        self._current_acting_unit = unit_id

    def mark_action_start(self, owner_id: str, round_num: int) -> bool:
        """
        Record that owner reached UNIT_ACTION_START timing in round_num.
        Returns True on the first mark in this round, False on subsequent duplicate/synthetic marks.
        """
        if not isinstance(owner_id, str) or not owner_id.strip():
            raise ValueError("owner_id cannot be empty or whitespace")
        if not isinstance(round_num, int) or isinstance(round_num, bool):
            raise TypeError("round_num must be an int")
        if round_num < 1:
            raise ValueError("round_num must be >= 1")

        key = (owner_id, round_num)
        if key in self._consumed_action_starts:
            return False

        self._consumed_action_starts.add(key)
        return True

    def has_consumed_action_start(self, owner_id: str, round_num: int) -> bool:
        """Check if the owner has already reached action start in the given round."""
        return (owner_id, round_num) in self._consumed_action_starts

    def has_acted_in_round(self, owner_id: str, round_num: int) -> bool:
        """Lifecycle-perspective alias for has_consumed_action_start."""
        return self.has_consumed_action_start(owner_id, round_num)
