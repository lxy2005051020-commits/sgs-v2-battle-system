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
    PROVIDER_DEFEATED = "PROVIDER_DEFEATED"


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

        # Gather every node affected by owner defeat AND formation-provider
        # cleanup BEFORE the first mutation. Stage10's transition coordinator
        # requires the complete pre-removal closure for linked consumers.
        resident_before = tuple(
            sorted(
                context.states.find(owner_id=defeated_unit_id),
                key=lambda item: item.instance_id,
            )
        )

        from .skill_definition import SkillType

        formation_sources = {
            (rt.definition.skill_id, rt.skill_slot)
            for rt in context.skill_runtimes.values()
            if rt.owner_id == defeated_unit_id
            and rt.definition.skill_type == SkillType.FORMATION
        }
        provided_elsewhere = tuple(
            sorted(
                (
                    inst for inst in context.states.find()
                    if inst.owner_id != defeated_unit_id
                    and inst.source_id == defeated_unit_id
                    and (inst.source_skill_id, inst.source_skill_slot) in formation_sources
                ),
                key=lambda item: item.instance_id,
            )
        )
        all_before = tuple(
            sorted((*resident_before, *provided_elsewhere), key=lambda item: item.instance_id)
        )
        transition_snapshot = None
        if self._transition_coordinator is not None and all_before:
            transition_snapshot = self._transition_coordinator.capture(
                context, tuple(StateNode(inst.instance_id) for inst in all_before)
            )

        # Existing frozen owner semantics remain unchanged: remove all
        # states on the defeated unit, then only foreign targets' effects
        # belonging to this unit's formation SkillRuntime provenance.
        removed = list(lifecycle.clear_owner_on_defeat(context, defeated_unit_id))
        for inst in provided_elsewhere:
            if inst.instance_id in context.states:
                removed.append(
                    lifecycle.remove(
                        context, inst.instance_id,
                        reason=DefeatRemovalReason.PROVIDER_DEFEATED.value,
                    )
                )

        all_removed = tuple(sorted(removed, key=lambda item: item.instance_id))
        if (
            self._transition_coordinator is not None
            and transition_snapshot is not None
            and all_removed
        ):
            self._transition_coordinator.complete_removed_nodes(
                context,
                transition_snapshot,
                tuple(StateNode(inst.instance_id) for inst in all_removed),
            )

        return DefeatCleanupResult(
            defeated_unit_id=defeated_unit_id,
            removed_states=all_removed,
            defeat_source_ref=defeat_source_ref,
            round_no=context.current_round,
            phase=context.current_phase,
        )
