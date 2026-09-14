from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from .official_state_catalog import OfficialStateId
from .stage9_state_params import GuardStateParams, TauntStateParams
from .state_instance import StateInstance
from .state_lifecycle_system import StateLifecycleSystem

if TYPE_CHECKING:
    from .context import BattleContext


class TauntLifecycleState(str, Enum):
    ACTIVE = "ACTIVE"
    SUPPRESSED = "SUPPRESSED"


class SuppressionReason(str, Enum):
    INSIGHT = "INSIGHT"
    SOURCE_SKILL_DISABLED = "SOURCE_SKILL_DISABLED"


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

    def get_taunt_suppressors(
        self,
        context: BattleContext,
        taunt_instance: StateInstance,
    ) -> set[str]:
        """Return the set of active suppressors for a Taunt instance.

        Multi-suppressor model (Taunt P0):
        - INSIGHT: holder has active Insight state (Insight is a state-level suppressor of existing Taunt)
        - SOURCE_SKILL_DISABLED or other reasons specified on TauntStateParams.suppressors
        """
        suppressors: set[str] = set()
        if isinstance(taunt_instance.runtime_params, TauntStateParams):
            suppressors.update(taunt_instance.runtime_params.suppressors)
        if self.has_operational_insight(context, taunt_instance.owner_id):
            suppressors.add(SuppressionReason.INSIGHT.value)
        return suppressors

    def get_taunt_lifecycle_state(
        self,
        context: BattleContext,
        taunt_instance: StateInstance,
    ) -> TauntLifecycleState:
        """Evaluate Taunt lifecycle state: ACTIVE <-> SUPPRESSED."""
        suppressors = self.get_taunt_suppressors(context, taunt_instance)
        if suppressors:
            return TauntLifecycleState.SUPPRESSED
        return TauntLifecycleState.ACTIVE

    def is_taunt_operational(
        self,
        context: BattleContext,
        taunt_instance: StateInstance,
    ) -> bool:
        """A Taunt instance is operational if it is ACTIVE and its source unit is alive.

        Note: source unit liveness is independent from lifecycleState.
        """
        if self.get_taunt_lifecycle_state(context, taunt_instance) != TauntLifecycleState.ACTIVE:
            return False
        target_unit_id = self.get_taunt_target_unit_id(taunt_instance)
        if target_unit_id is None:
            return False
        target_unit = context.get_unit(target_unit_id)
        return target_unit.is_alive

    def get_operational_taunt(
        self,
        context: BattleContext,
        unit_id: str,
    ) -> StateInstance | None:
        """Return operational Taunt StateInstance on unit_id if active and source is alive, else None."""
        instances = context.states.find(
            owner_id=unit_id,
            state_id=OfficialStateId.TAUNT.value,
        )
        if not instances:
            return None
        taunt = instances[0]
        if not self.is_taunt_operational(context, taunt):
            return None
        return taunt

    def get_taunt_target_unit_id(self, instance: StateInstance) -> str | None:
        """Get the unit_id that the taunted holder is forced to attack.

        Authoritative forced target is strictly instance.source_id (the taunter).
        Structural invariant: TauntStateParams.taunt_target_id cannot disagree with source_id.
        """
        if (
            isinstance(instance.runtime_params, TauntStateParams)
            and instance.runtime_params.taunt_target_id is not None
            and instance.runtime_params.taunt_target_id != instance.source_id
        ):
            raise ValueError(
                f"TauntStateParams.taunt_target_id ({instance.runtime_params.taunt_target_id}) "
                f"cannot disagree with authoritative source_id ({instance.source_id})"
            )
        return instance.source_id

    def is_guard_operational(
        self,
        context: BattleContext,
        guard_instance: StateInstance,
    ) -> bool:
        """A Guard instance is operational if it is not disabled and its protector is alive."""
        if not isinstance(guard_instance.runtime_params, GuardStateParams):
            return False
        if guard_instance.runtime_params.is_disabled:
            return False
        protector_id = guard_instance.runtime_params.protector_id
        if not protector_id or protector_id == guard_instance.owner_id:
            return False
        protector = context.get_unit(protector_id)
        return protector.is_alive

    def get_guard_protector(
        self,
        context: BattleContext,
        intended_target_id: str,
        attacker_id: str | None = None,
    ) -> str | None:
        """Find an alive operational protector for intended_target_id under Guard, if any.

        State_Owner = PROTECTED_TARGET / HOLDER (owner_id == intended_target_id).
        Protector identity is explicit on GuardStateParams.protector_id.
        Protector is distinct from sourceUnit provenance (no guessing from source_id).
        Protector must be alive, cannot be intended_target_id (no self-guard).
        Attacker == protector is legally allowed (Guard P0).
        Disabled Guard does not redirect (Guard Cover Check).
        Protector-owned reverse Guard representation is rejected.
        Guard is single-pass non-recursive (no chain guard).
        """
        for inst in context.states.find(
            owner_id=intended_target_id,
            state_id=OfficialStateId.GUARD.value,
        ):
            if not self.is_guard_operational(context, inst):
                continue
            assert isinstance(inst.runtime_params, GuardStateParams)
            return inst.runtime_params.protector_id

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
