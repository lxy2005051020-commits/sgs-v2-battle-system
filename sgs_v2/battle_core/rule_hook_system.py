from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

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
from .effects import (
    ApplyStateEffect,
    DamageEffect,
    Effect,
    RecoverEffect,
    RemoveStateEffect,
)
from .execution_right_system import ExecutionRightSystem
from .rule_hooks import RoundStartHook, RuleHook, UnitActionStartHook
from .rule_intent import (
    AbortedRuleIntentResult,
    ExecutionRightDecisionKind,
    ExecutionRightReason,
    RecoveryOpportunity,
    RecoveryOpportunityResult,
    RuleIntent,
    RuleIntentExecutionDescriptor,
    RuleIntentResult,
)
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
    """
    Hook execution result contract (STAGE7.md §11, STAGE7_STAGE10_COMPATIBILITY_ADDENDUM.md §7).
    Maintains 100% backward compatibility with Stage 7 effect_results while exposing
    the full Stage 10 intent_results union (including AbortedRuleIntentResult and RecoveryOpportunityResult).
    """

    hook: RuleHook
    intent_results: tuple[RuleIntentResult, ...] = ()
    effect_results: tuple[EffectExecutionResult, ...] = ()
    batch_status: str = "COMPLETED"
    aborting_intent_index: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.hook, (RoundStartHook, UnitActionStartHook)):
            raise TypeError("hook must be a RuleHook")

        # Canonicalize effect_results if provided
        try:
            canonical_effects = tuple(self.effect_results)
        except TypeError as exc:
            raise TypeError("effect_results must be iterable") from exc
        for result in canonical_effects:
            if not isinstance(result, _EFFECT_RESULT_TYPES):
                raise TypeError(
                    "effect_results must contain only EffectExecutionResult variants"
                )
        object.__setattr__(self, "effect_results", canonical_effects)

        # Canonicalize intent_results
        try:
            canonical_intents = tuple(self.intent_results)
        except TypeError as exc:
            raise TypeError("intent_results must be iterable") from exc
        object.__setattr__(self, "intent_results", canonical_intents)

        # Synchronize projections between effect_results and intent_results
        if not canonical_intents and canonical_effects:
            object.__setattr__(self, "intent_results", canonical_effects)
        elif not canonical_effects and canonical_intents:
            projected = tuple(
                r for r in canonical_intents if isinstance(r, _EFFECT_RESULT_TYPES)
            )
            object.__setattr__(self, "effect_results", projected)


class RuleHookSystem:
    """
    Stage 7 & Stage 10 rule hook orchestration and ordered intent dispatch owner.
    - Collects deterministic batch via TriggerSystem.
    - Evaluates per-intent execution right via ExecutionRightSystem (no duck typing).
    - Enforces abort scopes (REJECT_CURRENT, ABORT_OWNER_STATE_REMAINDER, ABORT_HOOK).
    - Routes admitted intents pure to EffectExecutor or recovery dispatcher.
    - Preserves mixed Effect / RecoveryOpportunity ordering.
    """

    def __init__(
        self,
        trigger_system: TriggerSystem,
        effect_executor: EffectExecutor,
    ) -> None:
        self._trigger = trigger_system
        self._executor = effect_executor
        self._execution_right = ExecutionRightSystem()
        self._recovery_opportunity_system: object | None = None
        self._recovery_opportunity_handler: (
            Callable[[BattleContext, RecoveryOpportunity], RecoveryOpportunityResult] | None
        ) = None

    @property
    def execution_right_system(self) -> ExecutionRightSystem:
        return self._execution_right

    @execution_right_system.setter
    def execution_right_system(self, system: ExecutionRightSystem) -> None:
        if not isinstance(system, ExecutionRightSystem):
            raise TypeError("execution_right_system must be an ExecutionRightSystem")
        self._execution_right = system

    @property
    def recovery_opportunity_system(self) -> object | None:
        return self._recovery_opportunity_system

    @recovery_opportunity_system.setter
    def recovery_opportunity_system(self, system: object | None) -> None:
        self._recovery_opportunity_system = system

    @property
    def recovery_opportunity_handler(
        self,
    ) -> Callable[[BattleContext, RecoveryOpportunity], RecoveryOpportunityResult] | None:
        return self._recovery_opportunity_handler

    @recovery_opportunity_handler.setter
    def recovery_opportunity_handler(
        self,
        handler: Callable[[BattleContext, RecoveryOpportunity], RecoveryOpportunityResult] | None,
    ) -> None:
        self._recovery_opportunity_handler = handler

    def process(
        self,
        context: BattleContext,
        hook: RuleHook,
    ) -> HookResolutionResult:
        if not isinstance(hook, (RoundStartHook, UnitActionStartHook)):
            raise TypeError("hook must be a RuleHook")
        if hook.round_no != context.current_round:
            raise ValueError("hook.round_no must match context.current_round")

        if isinstance(hook, UnitActionStartHook):
            if hook.actor_id not in context.units:
                raise KeyError(f"unknown hook actor_id: {hook.actor_id}")
            actor = context.units[hook.actor_id]
            if not actor.is_alive:
                raise ValueError("UnitActionStartHook actor must be alive")

        intents = self._trigger.collect(context, hook)
        intent_results: list[RuleIntentResult] = []
        aborted_state_owner_ids: set[str] = set()
        batch_status = "COMPLETED"
        aborting_intent_index: int | None = None

        ers = getattr(context, "execution_right", None) or self._execution_right

        for idx, intent in enumerate(intents):
            # Precondition invariant S10-FG-H01:
            desc = getattr(intent, "execution_descriptor", None)
            assert desc is not None, "RuleIntent must carry an execution_descriptor"
            assert desc.intent_owner_id, "intent_owner_id must be populated"

            # Check if this intent belongs to an owner whose state remainder was aborted
            if desc.state_owner_id is not None and desc.state_owner_id in aborted_state_owner_ids:
                intent_results.append(
                    AbortedRuleIntentResult(
                        descriptor=desc,
                        decision_kind=ExecutionRightDecisionKind.ABORT_OWNER_STATE_REMAINDER,
                        reason=ExecutionRightReason.OWNER_DEFEATED,
                        intent=intent,
                    )
                )
                continue

            # Query authoritative execution right decision
            decision = ers.evaluate_rule_intent(desc, context)

            if decision.decision_kind == ExecutionRightDecisionKind.ALLOW:
                if isinstance(
                    intent,
                    (DamageEffect, ApplyStateEffect, RemoveStateEffect, RecoverEffect),
                ):
                    result = self._executor.execute(context, intent)
                    intent_results.append(result)
                elif isinstance(intent, RecoveryOpportunity):
                    handler = (
                        self._recovery_opportunity_handler
                        or self._recovery_opportunity_system
                        or getattr(context, "recovery_opportunity_system", None)
                    )
                    if handler is not None:
                        if hasattr(handler, "evaluate_and_resolve"):
                            res = handler.evaluate_and_resolve(context, intent)
                        elif callable(handler):
                            res = handler(context, intent)
                        else:
                            raise TypeError("Invalid recovery opportunity handler")
                    else:
                        res = RecoveryOpportunityResult(
                            opportunity=intent,
                            resolution=None,
                            executed=False,
                            reason="NO_RECOVERY_OPPORTUNITY_HANDLER",
                        )
                    intent_results.append(res)
                else:
                    raise TypeError(f"Unknown RuleIntent variant: {type(intent)}")

            elif decision.decision_kind == ExecutionRightDecisionKind.REJECT_CURRENT:
                # Scope: ONLY the current intent is rejected.
                # Batch continues for subsequent intents!
                intent_results.append(
                    AbortedRuleIntentResult(
                        descriptor=desc,
                        decision_kind=decision.decision_kind,
                        reason=decision.reason or ExecutionRightReason.TARGET_DEFEATED,
                        intent=intent,
                    )
                )

            elif decision.decision_kind == ExecutionRightDecisionKind.ABORT_OWNER_STATE_REMAINDER:
                # Scope: Current intent + all remaining intents belonging to this state_owner_id!
                if desc.state_owner_id is not None:
                    aborted_state_owner_ids.add(desc.state_owner_id)
                if batch_status == "COMPLETED":
                    batch_status = "ABORTED_BY_TARGET_DEFEAT"
                    aborting_intent_index = idx
                intent_results.append(
                    AbortedRuleIntentResult(
                        descriptor=desc,
                        decision_kind=decision.decision_kind,
                        reason=decision.reason or ExecutionRightReason.OWNER_DEFEATED,
                        intent=intent,
                    )
                )

            elif decision.decision_kind == ExecutionRightDecisionKind.ABORT_HOOK:
                # Scope: Entire hook batch terminates immediately.
                batch_status = "ABORTED_HOOK"
                if aborting_intent_index is None:
                    aborting_intent_index = idx
                intent_results.append(
                    AbortedRuleIntentResult(
                        descriptor=desc,
                        decision_kind=decision.decision_kind,
                        reason=decision.reason or ExecutionRightReason.BATTLE_FINALIZED,
                        intent=intent,
                    )
                )
                for rem_intent in intents[idx + 1 :]:
                    rem_desc = getattr(rem_intent, "execution_descriptor", None)
                    assert rem_desc is not None, "RuleIntent must carry an execution_descriptor"
                    intent_results.append(
                        AbortedRuleIntentResult(
                            descriptor=rem_desc,
                            decision_kind=ExecutionRightDecisionKind.ABORT_HOOK,
                            reason=decision.reason or ExecutionRightReason.BATTLE_FINALIZED,
                            intent=rem_intent,
                        )
                    )
                break

        return HookResolutionResult(
            hook=hook,
            intent_results=tuple(intent_results),
            batch_status=batch_status,
            aborting_intent_index=aborting_intent_index,
        )
