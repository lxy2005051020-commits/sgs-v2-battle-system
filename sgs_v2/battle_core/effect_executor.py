from __future__ import annotations

from .context import BattleContext
from .damage_instance_coordinator import DamageInstanceCoordinator
from .effect_result import (
    ApplyStateEffectResult,
    DamageEffectResult,
    DeferredEffectResult,
    EffectExecutionResult,
    RecoverEffectResult,
    RemoveStateEffectResult,
)
from .effects import ApplyStateEffect, DamageEffect, Effect, RecoverEffect, RemoveStateEffect
from .recovery_system import RecoverySystem
from .state_lifecycle_system import StateLifecycleSystem


class EffectExecutor:
    """把纯数据 Effect 路由到已有 BattleSystem。"""

    RECOVERY_DEFERRED_REASON = "RECOVERY_SYSTEM_NOT_AVAILABLE"

    def __init__(
        self,
        damage_instance_coordinator: DamageInstanceCoordinator,
        state_lifecycle_system: StateLifecycleSystem,
        recovery_system: RecoverySystem | None = None,
    ) -> None:
        if not isinstance(damage_instance_coordinator, DamageInstanceCoordinator):
            raise TypeError(
                "damage_instance_coordinator must be DamageInstanceCoordinator"
            )
        self._damage_instances = damage_instance_coordinator
        self._state_lifecycle = state_lifecycle_system
        self._recovery = recovery_system

    def execute(
        self,
        context: BattleContext,
        effect: Effect,
    ) -> EffectExecutionResult:
        if isinstance(effect, DamageEffect):
            execution = self._damage_instances.execute_damage_effect(context, effect)
            return DamageEffectResult(
                effect=effect,
                resolution=execution.resolution,
                damage_instance_id=execution.damage_instance_id,
                partition_plan=execution.partition_plan,
                direct_losses=execution.direct_losses,
            )

        if isinstance(effect, ApplyStateEffect):
            source_skill_slot = (
                effect.source_ref.source_skill_slot
                if effect.source_ref is not None
                else None
            )
            instance = self._state_lifecycle.apply(
                context,
                state_id=effect.state_id,
                owner_id=effect.owner_id,
                source_id=effect.source_id,
                source_skill_id=effect.source_skill_id,
                source_skill_slot=source_skill_slot,
                expires_round=effect.expires_round,
                expires_phase=effect.expires_phase,
                runtime_params=effect.runtime_params,
            )
            return ApplyStateEffectResult(
                effect=effect,
                state_instance=instance,
            )

        if isinstance(effect, RemoveStateEffect):
            removed = self._state_lifecycle.remove(context, effect.instance_id)
            return RemoveStateEffectResult(
                effect=effect,
                removed_state=removed,
            )

        if isinstance(effect, RecoverEffect):
            if self._recovery is None:
                return DeferredEffectResult(
                    effect=effect,
                    reason=self.RECOVERY_DEFERRED_REASON,
                )
            resolution = self._recovery.resolve(context, effect.to_request())
            return RecoverEffectResult(
                effect=effect,
                resolution=resolution,
            )

        raise TypeError(f"unsupported effect type: {type(effect).__name__}")
