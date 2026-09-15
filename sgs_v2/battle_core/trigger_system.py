from __future__ import annotations

from .context import BattleContext
from .effects import DamageEffect, Effect, EffectSourceRef, RecoverEffect
from .enums import DamageSourceType
from .operation_identity import SourceType
from .rule_hooks import RoundStartHook, RuleHook, UnitActionStartHook
from .stage7_state_params import (
    PeriodicDamageStateParams,
    PeriodicRecoveryStateParams,
)
from .rule_intent import (
    RuleIntent,
    RuleIntentExecutionDescriptor,
    RuleIntentKind,
)
from .state_instance import StateInstance


ROUND_START_TRIGGER_TAG = "RULE_HOOK:ROUND_START"
UNIT_ACTION_START_TRIGGER_TAG = "RULE_HOOK:UNIT_ACTION_START"


class TriggerSystem:
    """读取当前状态与 typed hook，只产生确定顺序的 Effect，不执行副作用。"""

    def collect(
        self,
        context: BattleContext,
        hook: RuleHook,
    ) -> tuple[Effect, ...]:
        if not isinstance(hook, (RoundStartHook, UnitActionStartHook)):
            raise TypeError("hook must be a RuleHook")

        matched: list[StateInstance] = []
        for instance in context.states.find():
            if isinstance(hook, UnitActionStartHook) and instance.owner_id != hook.actor_id:
                continue
            definition = context.states.get_definition(instance.state_id)
            required_tag = (
                ROUND_START_TRIGGER_TAG
                if isinstance(hook, RoundStartHook)
                else UNIT_ACTION_START_TRIGGER_TAG
            )
            if required_tag in definition.tags:
                matched.append(instance)

        effects: list[Effect] = []
        for instance in sorted(matched, key=lambda item: item.instance_id):
            effects.extend(self._effects_for_state(instance))
        return tuple(effects)

    @staticmethod
    def _effects_for_state(instance: StateInstance) -> tuple[Effect, ...]:
        params = instance.runtime_params

        if isinstance(params, PeriodicDamageStateParams):
            if instance.source_id is None:
                raise ValueError(
                    "periodic damage state requires source_id for DamageSystem attribution"
                )
            source_ref = EffectSourceRef(
                stage9_source_type=SourceType.PERIODIC_DAMAGE,
                source_unit_id=instance.source_id,
                source_skill_id=instance.source_skill_id,
                source_skill_slot=instance.source_skill_slot,
            )
            desc = RuleIntentExecutionDescriptor(
                intent_kind=RuleIntentKind.EFFECT,
                intent_owner_id=instance.owner_id,
                state_owner_id=instance.owner_id,
                target_id=instance.owner_id,
                source_ref=source_ref,
                state_instance_id=instance.instance_id,
                state_generation_id=instance.current_generation_id,
                execution_domain="STATE_RESOLUTION",
            )
            return (
                DamageEffect(
                    source_id=instance.source_id,
                    target_id=instance.owner_id,
                    damage_type=params.damage_type,
                    source_type=DamageSourceType.CONTINUOUS,
                    coefficient=params.coefficient,
                    source_skill_id=instance.source_skill_id,
                    source_state_id=instance.state_id,
                    source_state_instance_id=instance.instance_id,
                    source_ref=source_ref,
                    execution_descriptor=desc,
                ),
            )

        if isinstance(params, PeriodicRecoveryStateParams):
            desc = RuleIntentExecutionDescriptor(
                intent_kind=RuleIntentKind.EFFECT,
                intent_owner_id=instance.owner_id,
                state_owner_id=instance.owner_id,
                target_id=instance.owner_id,
                state_instance_id=instance.instance_id,
                state_generation_id=instance.current_generation_id,
                execution_domain="STATE_RESOLUTION",
            )
            return (
                RecoverEffect(
                    source_id=instance.source_id,
                    target_id=instance.owner_id,
                    amount=params.amount,
                    source_skill_id=instance.source_skill_id,
                    source_state_id=instance.state_id,
                    source_state_instance_id=instance.instance_id,
                    execution_descriptor=desc,
                ),
            )

        return ()
