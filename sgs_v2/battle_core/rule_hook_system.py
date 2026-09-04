from __future__ import annotations

from dataclasses import dataclass

from .context import BattleContext
from .effect_executor import EffectExecutor
from .effect_result import (
    ApplyStateEffectResult,
    DamageEffectResult,
    DeferredEffectResult,
    EffectExecutionResult,
    RecoverEffectResult,
    RemoveStateEffectResult,
)
from .rule_hooks import RoundStartHook, RuleHook, UnitActionStartHook
from .trigger_system import TriggerSystem


_EFFECT_RESULT_TYPES = (
    DamageEffectResult,
    ApplyStateEffectResult,
    RemoveStateEffectResult,
    RecoverEffectResult,
    DeferredEffectResult,
)


@dataclass(frozen=True, slots=True)
class HookResolutionResult:
    hook: RuleHook
    effect_results: tuple[EffectExecutionResult, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.hook, (RoundStartHook, UnitActionStartHook)):
            raise TypeError("hook must be a RuleHook")
        try:
            canonical = tuple(self.effect_results)
        except TypeError as exc:
            raise TypeError("effect_results must be iterable") from exc
        for result in canonical:
            if not isinstance(result, _EFFECT_RESULT_TYPES):
                raise TypeError(
                    "effect_results must contain only EffectExecutionResult variants"
                )
        object.__setattr__(self, "effect_results", canonical)


class RuleHookSystem:
    """最小 hook 协调层：validate -> TriggerSystem -> EffectExecutor。"""

    def __init__(
        self,
        trigger_system: TriggerSystem,
        effect_executor: EffectExecutor,
    ) -> None:
        self._trigger = trigger_system
        self._executor = effect_executor

    def process(
        self,
        context: BattleContext,
        hook: RuleHook,
    ) -> HookResolutionResult:
        if not isinstance(hook, (RoundStartHook, UnitActionStartHook)):
            raise TypeError("hook must be a RuleHook")
        if hook.round_no != context.current_round:
            raise ValueError(
                "hook.round_no must match context.current_round"
            )

        if isinstance(hook, UnitActionStartHook):
            if hook.actor_id not in context.units:
                raise KeyError(f"unknown hook actor_id: {hook.actor_id}")
            actor = context.units[hook.actor_id]
            if not actor.is_alive:
                raise ValueError("UnitActionStartHook actor must be alive")

        effects = self._trigger.collect(context, hook)
        results = tuple(
            self._executor.execute(context, effect)
            for effect in effects
        )
        return HookResolutionResult(
            hook=hook,
            effect_results=results,
        )
