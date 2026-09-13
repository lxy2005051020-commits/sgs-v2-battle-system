from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True, order=False)
class Stage9TraceEntry:
    """Diagnostic trace entry.

    Diagnostic only:
    - Never gameplay authority
    - Never orchestration owner
    - Never used for target, reaction ordering, finalization, damage, admission, or state mutation decisions.
    """

    sequence_number: int
    category: str
    operation_id: str | None
    payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.sequence_number, bool) or not isinstance(self.sequence_number, int):
            raise TypeError("sequence_number must be an int")
        if not isinstance(self.category, str) or not self.category.strip():
            raise ValueError("category cannot be empty or whitespace")
        if self.operation_id is not None:
            if not isinstance(self.operation_id, str) or not self.operation_id.strip():
                raise ValueError("operation_id cannot be empty or whitespace when provided")
        if not isinstance(self.payload, dict):
            raise TypeError("payload must be a dict")


class Stage9DiagnosticTraceSink:
    """Bounded ring trace sink for Stage9 diagnostic and observation events.

    Invariants:
    - Bounded ring buffer: drops oldest entries when max_capacity is reached.
    - Purely diagnostic: has zero control-flow or gameplay authority.
    - Cannot decide target, reaction, finalization, damage, admission, or state mutation.
    """

    __slots__ = ("_max_capacity", "_sequence_counter", "_entries")

    def __init__(self, max_capacity: int = 1000) -> None:
        if isinstance(max_capacity, bool) or not isinstance(max_capacity, int):
            raise TypeError("max_capacity must be an int")
        if max_capacity <= 0:
            raise ValueError("max_capacity must be positive")
        self._max_capacity = max_capacity
        self._sequence_counter = 0
        self._entries: deque[Stage9TraceEntry] = deque(maxlen=max_capacity)

    @property
    def max_capacity(self) -> int:
        return self._max_capacity

    @property
    def count(self) -> int:
        return len(self._entries)

    def record(
        self,
        category: str,
        operation_id: str | None = None,
        **payload: Any,
    ) -> Stage9TraceEntry:
        self._sequence_counter += 1
        entry = Stage9TraceEntry(
            sequence_number=self._sequence_counter,
            category=category,
            operation_id=operation_id,
            payload=payload,
        )
        self._entries.append(entry)
        return entry

    def get_entries(self) -> tuple[Stage9TraceEntry, ...]:
        return tuple(self._entries)

    def clear(self) -> None:
        self._entries.clear()

    def filter_by_category(self, category: str) -> list[Stage9TraceEntry]:
        return [entry for entry in self._entries if entry.category == category]

    def filter_by_operation(self, operation_id: str) -> list[Stage9TraceEntry]:
        return [entry for entry in self._entries if entry.operation_id == operation_id]
