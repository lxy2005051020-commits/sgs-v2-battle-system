from __future__ import annotations

from .context import BattleContext
from .damage_resolution_system import DamageResolutionSystem
from .effect_result import (
    ApplyStateEffectResult,
    DamageEffectResult,
    DeferredEffectResult,
    EffectExecutionResult,
    RemoveStateEffectResult,
)
from .effects import ApplyStateEffect, DamageEffect, Effect, RecoverEffect, RemoveStateEffect
from .state_lifecycle_system import StateLifecycleSystem


class EffectExecutor:
    """把纯数据 Effect 路由到已有 BattleSystem。

    本类不计算伤害、不修改兵力、不直接写 StateRegistry，也不消费 RNG。
    """

    RECOVERY_DEFERRED_REASON = "RECOVERY_SYSTEM_NOT_AVAILABLE"

    def __init__(
        self,
        damage_resolution_system: DamageResolutionSystem,
        state_lifecycle_system: StateLifecycleSystem,
    ) -> None:
        self._damage_resolution = damage_resolution_system
        self._state_lifecycle = state_lifecycle_system

    def execute(
        self,
        context: BattleContext,
        effect: Effect,
    ) -> EffectExecutionResult:
        if isinstance(effect, DamageEffect):
            resolution = self._damage_resolution.resolve(
                context,
                effect.to_request(),
            )
            return DamageEffectResult(effect=effect, resolution=resolution)

        if isinstance(effect, ApplyStateEffect):
            instance = self._state_lifecycle.apply(
                context,
                state_id=effect.state_id,
                owner_id=effect.owner_id,
                source_id=effect.source_id,
                source_skill_id=effect.source_skill_id,
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
            return DeferredEffectResult(
                effect=effect,
                reason=self.RECOVERY_DEFERRED_REASON,
            )

        raise TypeError(f"unsupported effect type: {type(effect).__name__}")
