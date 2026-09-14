from __future__ import annotations

from typing import TYPE_CHECKING

from .official_state_catalog import OfficialStateId
from .stage9_state_params import GuardStateParams
from .state_instance import StateInstance
from .state_lifecycle_system import StateLifecycleSystem

if TYPE_CHECKING:
    from .context import BattleContext


class Stage9StateRuntime:
    """Typed read / maintenance adapter over BattleContext.states (StateRegistry).

    Stage9StateRuntime is NOT a second state storage, NOT a StateRegistry replacement,
    and NOT a state lifecycle writer. All physical state storage remains strictly in
    StateRegistry, and all state mutations remain strictly in StateLifecycleSystem.
    """

    def __init__(
        self,
        state_lifecycle_system: StateLifecycleSystem,
    ) -> None:
        if not isinstance(state_lifecycle_system, StateLifecycleSystem):
            raise TypeError(
                f"state_lifecycle_system must be a StateLifecycleSystem, got {type(state_lifecycle_system)}"
            )
        self._lifecycle = state_lifecycle_system

    @property
    def lifecycle(self) -> StateLifecycleSystem:
        return self._lifecycle

    def get_operational_confusion(
        self,
        context: BattleContext,
        unit_id: str,
    ) -> StateInstance | None:
        """Return operational Confusion StateInstance on unit_id if active, else None.

        Insight is application immunity only, not runtime suppression of existing instances (Confusion P0).
        """
        instances = context.states.find(
            owner_id=unit_id,
            state_id=OfficialStateId.CONFUSION.value,
        )
        if not instances:
            return None
        return instances[0]

    def get_operational_taunt(
        self,
        context: BattleContext,
        unit_id: str,
    ) -> StateInstance | None:
        """Return operational Taunt StateInstance on unit_id if active and source is alive, else None.

        If the Taunt source unit is dead, Taunt silent-fails at targeting resolution (returns None),
        though the physical Taunt instance remains in registry.
        Taunt existing-state suppression is not an ad-hoc targeting Insight filter.
        """
        instances = context.states.find(
            owner_id=unit_id,
            state_id=OfficialStateId.TAUNT.value,
        )
        if not instances:
            return None
        taunt = instances[0]
        target_unit_id = self.get_taunt_target_unit_id(taunt)
        if target_unit_id is None:
            return None
        target_unit = context.get_unit(target_unit_id)
        if not target_unit.is_alive:
            return None
        return taunt

    def get_taunt_target_unit_id(self, instance: StateInstance) -> str | None:
        """Get the unit_id that the taunted holder is forced to attack.

        Authoritative forced target is strictly instance.source_id (the taunter).
        """
        return instance.source_id

    def get_guard_protector(
        self,
        context: BattleContext,
        intended_target_id: str,
        attacker_id: str | None = None,
    ) -> str | None:
        """Find an alive protector for intended_target_id under Guard, if any.

        State_Owner = PROTECTED_TARGET / HOLDER (owner_id == intended_target_id).
        Protector identity is explicit and immutable: inst.runtime_params.protector_id
        (if GuardStateParams with protector_id set) or inst.source_id.
        Protector must be alive, cannot be intended_target_id (no self-guard),
        and cannot be the attacker.
        Protector-owned reverse Guard representation is rejected.
        Guard is single-pass non-recursive (no chain guard).
        """
        for inst in context.states.find(
            owner_id=intended_target_id,
            state_id=OfficialStateId.GUARD.value,
        ):
            protector_id: str | None = None
            if (
                isinstance(inst.runtime_params, GuardStateParams)
                and inst.runtime_params.protector_id
            ):
                protector_id = inst.runtime_params.protector_id
            elif inst.source_id:
                protector_id = inst.source_id

            if protector_id and protector_id != intended_target_id:
                if attacker_id is not None and protector_id == attacker_id:
                    continue
                protector = context.get_unit(protector_id)
                if protector.is_alive:
                    return protector_id

        return None

    def has_operational_insight(
        self,
        context: BattleContext,
        unit_id: str,
    ) -> bool:
        """Return True if unit_id has active Insight state."""
        return context.states.has(
            owner_id=unit_id,
            state_id=OfficialStateId.INSIGHT.value,
        )
