from __future__ import annotations

from typing import TYPE_CHECKING

from .official_state_catalog import OfficialStateId
from .stage9_state_params import (
    ComboStateParams,
    CleaveStateParams,
    ChainStateParams,
    CounterStateParams,
    DamageShareStateParams,
    DistributionStateParams,
    GuardStateParams,
    SuppressionReason,
    TauntLifecycleState,
    TauntStateParams,
)
from .state_instance import StateInstance
from .state_lifecycle_system import StateLifecycleSystem

if TYPE_CHECKING:
    from .context import BattleContext

__all__ = [
    "Stage9StateRuntime",
    "SuppressionReason",
    "TauntLifecycleState",
]


class Stage9StateRuntime:
    """Typed read / maintenance adapter over BattleContext.states (StateRegistry).

    Stage9StateRuntime is NOT a second state storage, NOT a StateRegistry replacement,
    and NOT a state lifecycle writer. All physical state storage remains strictly in
    StateRegistry, and all state mutations remain strictly in StateLifecycleSystem.
    """

    def __init__(
        self,
        state_lifecycle_system: StateLifecycleSystem,
        counter_operationality=None,
    ) -> None:
        if not isinstance(state_lifecycle_system, StateLifecycleSystem):
            raise TypeError(
                f"state_lifecycle_system must be a StateLifecycleSystem, got {type(state_lifecycle_system)}"
            )
        self._lifecycle = state_lifecycle_system
        self._counter_operationality = counter_operationality

    @property
    def lifecycle(self) -> StateLifecycleSystem:
        return self._lifecycle

    @staticmethod
    def _unique_instance(
        instances: tuple[StateInstance, ...],
        *,
        state_name: str,
        owner_id: str,
    ) -> StateInstance | None:
        if not instances:
            return None
        if len(instances) != 1:
            raise ValueError(
                f"{state_name} requires exactly one physical instance per owner; "
                f"found {len(instances)} on '{owner_id}'"
            )
        return instances[0]

    def get_operational_damage_share(
        self,
        context: BattleContext,
        target_id: str,
    ) -> StateInstance | None:
        """Fresh DamageInstance-time read of the target's operational Share state."""
        instance = self._unique_instance(
            context.states.find(
                owner_id=target_id,
                state_id=OfficialStateId.DAMAGE_SHARE.value,
            ),
            state_name="DAMAGE_SHARE",
            owner_id=target_id,
        )
        if instance is None:
            return None
        if not isinstance(instance.runtime_params, DamageShareStateParams):
            raise TypeError("DAMAGE_SHARE state requires DamageShareStateParams")
        sharer_id = instance.runtime_params.sharer_id
        if sharer_id == target_id:
            return None
        sharer = context.units.get(sharer_id)
        if sharer is None or not sharer.is_alive or sharer.troops <= 0:
            return None
        return instance

    def get_cleave_effects(self, context, actor_id):
        from .skill_runtime import SkillSlot
        instances = context.states.find(owner_id=actor_id, state_id=OfficialStateId.CLEAVE.value)
        slots = set()
        for instance in instances:
            if not isinstance(instance.runtime_params, CleaveStateParams):
                raise TypeError("CLEAVE requires CleaveStateParams")
            if not isinstance(instance.source_skill_slot, SkillSlot):
                raise ValueError("Cleave SKILL_SLOT_ORDER requires authoritative source_skill_slot")
            if instance.source_skill_slot in slots:
                raise ValueError("Duplicate Cleave skill slot is an invalid loadout")
            slots.add(instance.source_skill_slot)
        return tuple(sorted(instances, key=lambda item: item.source_skill_slot))

    def get_operational_chain(self, context, target_id):
        target = context.units.get(target_id)
        if target is None or not target.is_alive:
            return None
        instance = self._unique_instance(context.states.find(owner_id=target_id, state_id=OfficialStateId.CHAIN_LINK.value), state_name="CHAIN", owner_id=target_id)
        if instance is not None and not isinstance(instance.runtime_params, ChainStateParams):
            raise TypeError("CHAIN requires ChainStateParams")
        return instance

    def get_counter_effects(self, context, holder_id):
        holder = context.units.get(holder_id)
        if holder is None or not holder.is_alive:
            return ()
        instances = context.states.find(owner_id=holder_id, state_id=OfficialStateId.COUNTERATTACK.value)
        for instance in instances:
            if not isinstance(instance.runtime_params, CounterStateParams):
                raise TypeError("COUNTER requires CounterStateParams")
        if self._counter_operationality is not None:
            instances = tuple(item for item in instances if self._counter_operationality(context, item))
        # Stable registration for sources without a slot is Counter's isolated
        # PROJECT_DETERMINISTIC_DEFAULT; not empirically proven / not official order.
        return tuple(sorted(instances, key=lambda item: (item.source_skill_slot is None, item.source_skill_slot if item.source_skill_slot is not None else 0)))

    def get_operational_distribution(
        self,
        context: BattleContext,
        target_id: str,
    ) -> StateInstance | None:
        """Fresh DamageInstance-time read of the target's operational Distribution state."""
        instance = self._unique_instance(
            context.states.find(
                owner_id=target_id,
                state_id=OfficialStateId.DAMAGE_SPLIT.value,
            ),
            state_name="DISTRIBUTION",
            owner_id=target_id,
        )
        if instance is None:
            return None
        if not isinstance(instance.runtime_params, DistributionStateParams):
            raise TypeError("DISTRIBUTION state requires DistributionStateParams")
        return instance

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
    ) -> frozenset[SuppressionReason]:
        suppressors: set[SuppressionReason] = set()
        if isinstance(taunt_instance.runtime_params, TauntStateParams):
            suppressors.update(taunt_instance.runtime_params.suppressors)
        if self.has_operational_insight(context, taunt_instance.owner_id):
            suppressors.add(SuppressionReason.INSIGHT)
        return frozenset(suppressors)

    def get_taunt_lifecycle_state(
        self,
        context: BattleContext,
        taunt_instance: StateInstance,
    ) -> TauntLifecycleState:
        suppressors = self.get_taunt_suppressors(context, taunt_instance)
        if suppressors:
            return TauntLifecycleState.SUPPRESSED
        return TauntLifecycleState.ACTIVE

    def is_taunt_operational(
        self,
        context: BattleContext,
        taunt_instance: StateInstance,
    ) -> bool:
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
        return context.states.has(
            owner_id=unit_id,
            state_id=OfficialStateId.INSIGHT.value,
        )

    def set_guard_disabled(
        self,
        context: BattleContext,
        instance_id: str,
        is_disabled: bool,
    ) -> StateInstance:
        instance = context.states.get(instance_id)
        if not isinstance(instance.runtime_params, GuardStateParams):
            raise TypeError(f"State instance {instance_id} is not a Guard state")
        new_params = GuardStateParams(
            protector_id=instance.runtime_params.protector_id,
            is_disabled=is_disabled,
        )
        return self._lifecycle.update_runtime_params(context, instance_id, new_params)

    def set_taunt_suppressors(
        self,
        context: BattleContext,
        instance_id: str,
        suppressors: frozenset[SuppressionReason] | set[SuppressionReason],
    ) -> StateInstance:
        instance = context.states.get(instance_id)
        if not isinstance(instance.runtime_params, TauntStateParams):
            raise TypeError(f"State instance {instance_id} is not a Taunt state")
        new_params = TauntStateParams(
            taunt_target_id=instance.runtime_params.taunt_target_id,
            suppressors=frozenset(suppressors),
        )
        return self._lifecycle.update_runtime_params(context, instance_id, new_params)

    def get_operational_combo(
        self,
        context: BattleContext,
        unit_id: str,
    ) -> StateInstance | None:
        """Returns operational Combo StateInstance on unit_id if active and not suppressed, else None."""
        instances = context.states.find(
            owner_id=unit_id,
            state_id=OfficialStateId.COMBO.value,
        )
        if not instances:
            return None
        instance = instances[0]
        params = instance.runtime_params
        if isinstance(params, ComboStateParams) and params.is_suppressed:
            return None
        return instance

    def set_combo_suppressed(
        self,
        context: BattleContext,
        instance_id: str,
        is_suppressed: bool,
    ) -> StateInstance:
        """Testing / seam helper to toggle suppression on a physical Combo instance."""
        instance = context.states.get(instance_id)
        if not isinstance(instance.runtime_params, ComboStateParams):
            raise TypeError(
                f"State instance {instance_id} is not a Combo state with ComboStateParams"
            )
        new_params = ComboStateParams(
            remaining_actions=instance.runtime_params.remaining_actions,
            is_suppressed=is_suppressed,
        )
        return self._lifecycle.update_runtime_params(context, instance_id, new_params)
