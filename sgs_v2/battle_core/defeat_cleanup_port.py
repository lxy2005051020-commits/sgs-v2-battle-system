from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

from .dependency_evaluation import StateNode
from .state_instance import StateInstance

if TYPE_CHECKING:
    from .context import BattleContext
    from .state_lifecycle_system import StateLifecycleSystem


class DefeatRemovalReason(str, Enum):
    OWNER_DEFEATED = "OWNER_DEFEATED"


@dataclass(frozen=True, slots=True)
class DefeatCleanupResult:
    """Synchronous cleanup result produced when an alive -> defeated edge is committed."""

    defeated_unit_id: str
    removed_states: tuple[StateInstance, ...]
    defeat_source_ref: Any = None
    round_no: int = 0
    phase: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.defeated_unit_id, str) or not self.defeated_unit_id.strip():
            raise ValueError("defeated_unit_id cannot be empty or whitespace")
        if not isinstance(self.removed_states, tuple):
            raise TypeError(f"removed_states must be a tuple of StateInstance, got {type(self.removed_states)}")
        for item in self.removed_states:
            if not isinstance(item, StateInstance):
                raise TypeError(f"All elements in removed_states must be StateInstance, got {type(item)}")


class DefeatCleanupPort:
    """
    Authoritative synchronous defeat cleanup coordinator (STAGE10.md §10).
    Called on the alive -> defeated transition across all destructive troop-loss paths.
    Coordinates hard defeat boundary:
    1. Removes all states attached to the defeated owner via StateLifecycleSystem.clear_owner_on_defeat.
    2. Guarantees deterministic instance_id order.
    3. Returns typed DefeatCleanupResult.
    """

    __slots__ = ("_lifecycle_system", "_transition_coordinator")

    def __init__(
        self,
        lifecycle_system: StateLifecycleSystem | None = None,
        *,
        transition_coordinator=None,
    ) -> None:
        self._lifecycle_system = lifecycle_system
        self._transition_coordinator = transition_coordinator

    def commit_defeat(
        self,
        context: BattleContext,
        defeated_unit_id: str,
        defeat_source_ref: Any = None,
    ) -> DefeatCleanupResult:
        if not isinstance(defeated_unit_id, str) or not defeated_unit_id.strip():
            raise ValueError("defeated_unit_id cannot be empty or whitespace")

        lifecycle = (
            self._lifecycle_system
            or getattr(getattr(context, "systems", None), "state_lifecycle_system", None)
        )
        if lifecycle is None:
            from .state_lifecycle_system import StateLifecycleSystem

            lifecycle = StateLifecycleSystem()

        resident_before = tuple(
            sorted(
                context.states.find(owner_id=defeated_unit_id),
                key=lambda item: item.instance_id,
            )
        )
        transition_snapshot = None
        if self._transition_coordinator is not None and resident_before:
            transition_snapshot = self._transition_coordinator.capture(
                context,
                tuple(StateNode(item.instance_id) for item in resident_before),
            )

        removed = lifecycle.clear_owner_on_defeat(context, defeated_unit_id)

        if (
            self._transition_coordinator is not None
            and transition_snapshot is not None
            and removed
        ):
            self._transition_coordinator.complete_removed_nodes(
                context,
                transition_snapshot,
                tuple(StateNode(item.instance_id) for item in removed),
            )

        return DefeatCleanupResult(
            defeated_unit_id=defeated_unit_id,
            removed_states=tuple(removed),
            defeat_source_ref=defeat_source_ref,
            round_no=context.current_round,
            phase=context.current_phase,
        )
