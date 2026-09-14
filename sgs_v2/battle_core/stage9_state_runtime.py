from __future__ import annotations

from typing import TYPE_CHECKING

from .official_state_catalog import OfficialStateId
from .stage9_state_params import GuardStateParams, TauntStateParams
from .state_instance import StateInstance
from .state_lifecycle_system import StateLifecycleSystem
from .state_registry import StateRegistry

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
        state_lifecycle_system: StateLifecycleSystem | None = None,
        state_registry: StateRegistry | None = None,
    ) -> None:
        self._lifecycle = (
            state_lifecycle_system
            if state_lifecycle_system is not None
            else StateLifecycleSystem()
        )
        self._registry = state_registry

    @property
    def lifecycle(self) -> StateLifecycleSystem:
        return self._lifecycle

    @property
    def registry(self) -> StateRegistry | None:
        return self._registry

    def _resolve_registry(self, context: BattleContext | None = None) -> StateRegistry:
        if context is not None:
            return context.states
        if self._registry is not None:
            return self._registry
        raise ValueError(
            "No StateRegistry available: provide context or initialize with state_registry"
        )

    def get_operational_confusion(
        self,
        context: BattleContext,
        unit_id: str,
    ) -> StateInstance | None:
        """Return operational Confusion StateInstance on unit_id if active, else None.

        If unit_id has operational Insight, Confusion is suppressed (returns None).
        """
        registry = self._resolve_registry(context)
        instances = registry.find(
            owner_id=unit_id,
            state_id=OfficialStateId.CONFUSION.value,
        )
        if not instances:
            return None
        if self.has_operational_insight(context, unit_id):
            return None
        return instances[0]

    def get_operational_taunt(
        self,
        context: BattleContext,
        unit_id: str,
    ) -> StateInstance | None:
        """Return operational Taunt StateInstance on unit_id if active and source is alive, else None.

        If unit_id has operational Insight, Taunt is suppressed (returns None).
        If the Taunt source unit is dead, Taunt silent-fails at targeting resolution (returns None),
        though the physical Taunt instance remains in registry.
        """
        registry = self._resolve_registry(context)
        instances = registry.find(
            owner_id=unit_id,
            state_id=OfficialStateId.TAUNT.value,
        )
        if not instances:
            return None
        if self.has_operational_insight(context, unit_id):
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
        """Get the unit_id that the taunted holder is forced to attack."""
        if (
            isinstance(instance.runtime_params, TauntStateParams)
            and instance.runtime_params.taunt_target_id
        ):
            return instance.runtime_params.taunt_target_id
        return instance.source_id

    def get_guard_protector(
        self,
        context: BattleContext,
        intended_target_id: str,
        attacker_id: str | None = None,
    ) -> str | None:
        """Find an alive protector for intended_target_id under Guard, if any.

        Checks:
        1. Guard buff where intended_target_id is holder (owner_id == intended_target_id),
           and protector is source_id.
        2. Guard buff where protector is holder (owner_id != intended_target_id),
           and guarded_unit_id == intended_target_id.
        Protector must be alive, cannot be intended_target_id (no self-guard),
        and cannot be the attacker.
        """
        registry = self._resolve_registry(context)

        # 1. intended_target is holder
        for inst in registry.find(
            owner_id=intended_target_id,
            state_id=OfficialStateId.GUARD.value,
        ):
            protector_id = inst.source_id
            if protector_id and protector_id != intended_target_id:
                if attacker_id is not None and protector_id == attacker_id:
                    continue
                protector = context.get_unit(protector_id)
                if protector.is_alive:
                    return protector_id

        # 2. protector is holder with GuardStateParams(guarded_unit_id=intended_target_id)
        for inst in registry.find(
            state_id=OfficialStateId.GUARD.value,
        ):
            if inst.owner_id == intended_target_id:
                continue
            if isinstance(inst.runtime_params, GuardStateParams):
                if inst.runtime_params.guarded_unit_id == intended_target_id:
                    protector_id = inst.owner_id
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
        registry = self._resolve_registry(context)
        return registry.has(
            owner_id=unit_id,
            state_id=OfficialStateId.INSIGHT.value,
        )
