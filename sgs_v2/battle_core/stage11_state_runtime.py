from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from enum import Enum

from .context import BattleContext
from .enums import DamageType
from .official_state_catalog import OfficialStateId
from .stage11_state_params import (
    AlertStateParams,
    CriticalStateParams,
    DamageReductionPierceStateParams,
    DisarmStateParams,
    EvasionStateParams,
    LifeStealStateParams,
    ResistanceStateParams,
    Stage11TimedFlagParams,
    StunStateParams,
)
from .state_instance import StateInstance
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .state_lifecycle_system import StateLifecycleSystem


class ContractBoundaryViolation(RuntimeError):
    """Raised when frozen research explicitly forbids inventing a runtime answer."""


class Stage11DamageFamily(str, Enum):
    NORMAL_ATTACK = "NORMAL_ATTACK"
    ASSAULT_SKILL = "ASSAULT_SKILL"
    ACTIVE_SKILL = "ACTIVE_SKILL"
    PERIODIC_DAMAGE = "PERIODIC_DAMAGE"
    COUNTERATTACK = "COUNTERATTACK"
    CLEAVE = "CLEAVE"
    COMMAND_XIEFANWEI = "COMMAND_DAMAGE_XIEFANWEI"
    REACTION_YIZHIBAOYUAN = "TACTIC_REACTION_YIZHIBAOYUAN"
    EQUIPMENT_CAITA = "EQUIPMENT_TRAIT_CAITA"
    EQUIPMENT_CHONGZHEN = "EQUIPMENT_TRAIT_CHONGZHEN"
    EQUIPMENT_JINGJI = "EQUIPMENT_TRAIT_JINGJI"
    COUNTER_QILINGSANJUN = "COUNTERATTACK_QILINGSANJUN"


class SeeThroughEligibility(str, Enum):
    SUPPORTED_APPLICABLE = "SUPPORTED_APPLICABLE"
    SUPPORTED_NO_INVOCATION = "SUPPORTED_NO_INVOCATION"
    UNSUPPORTED_UNKNOWN = "UNSUPPORTED_UNKNOWN"


@dataclass(frozen=True, slots=True)
class CriticalOutcome:
    triggered: bool
    chance: float
    bonus: float
    state_id: str | None


@dataclass(frozen=True, slots=True)
class Stage11HitOutcome:
    prevented: bool
    prevented_by_state_id: str | None
    evasion_probability: float
    sure_hit: bool
    resistance_consumed_instance_id: str | None = None


@dataclass(frozen=True, slots=True)
class AlertAdjustment:
    input_damage: float
    output_damage: float
    consumed_instance_id: str | None


class Stage11StateRuntime:
    """Read/arbitration façade for Stage11 states.

    StateRegistry remains physical storage. StateLifecycleSystem remains the only
    physical mutation owner; this class only asks that owner to replace/remove
    typed instances after a gameplay decision.
    """

    def __init__(self, lifecycle: "StateLifecycleSystem") -> None:
        if not hasattr(lifecycle, "update_runtime_params") or not hasattr(lifecycle, "remove"):
            raise TypeError("lifecycle must provide StateLifecycleSystem mutation seams")
        self._lifecycle = lifecycle

    @staticmethod
    def _ordered(instances: list[StateInstance] | tuple[StateInstance, ...]) -> tuple[StateInstance, ...]:
        return tuple(sorted(instances, key=lambda item: (item.applied_round, item.instance_id)))

    def instances(
        self, context: BattleContext, owner_id: str, state_id: OfficialStateId | str
    ) -> tuple[StateInstance, ...]:
        sid = state_id.value if isinstance(state_id, OfficialStateId) else state_id
        return self._ordered(context.states.find(owner_id=owner_id, state_id=sid))

    def is_effective(self, context: BattleContext, instance: StateInstance) -> bool:
        params = instance.runtime_params
        if bool(getattr(params, "is_suppressed", False)):
            return False
        if bool(getattr(params, "source_dependent", False)):
            source_id = instance.source_id
            if source_id is None:
                return False
            source = context.units.get(source_id)
            if source is None or not source.is_alive:
                return False
        if isinstance(params, ResistanceStateParams) and params.remaining_uses <= 0:
            return False
        if isinstance(params, AlertStateParams) and params.remaining_uses <= 0:
            return False
        if isinstance(params, StunStateParams) and params.remaining_blocks <= 0:
            return False
        return True

    def effective_instances(
        self, context: BattleContext, owner_id: str, state_id: OfficialStateId | str
    ) -> tuple[StateInstance, ...]:
        return tuple(
            item for item in self.instances(context, owner_id, state_id)
            if self.is_effective(context, item)
        )

    def has_effective(
        self, context: BattleContext, owner_id: str, state_id: OfficialStateId | str
    ) -> bool:
        return bool(self.effective_instances(context, owner_id, state_id))

    @staticmethod
    def _roll(context: BattleContext, probability: float) -> bool:
        if probability <= 0.0:
            return False
        if probability >= 1.0:
            return True
        return context.random.chance(probability)

    def _replace(self, context: BattleContext, instance: StateInstance, params) -> StateInstance:
        return self._lifecycle.update_runtime_params(
            context, instance.instance_id, params
        )

    def _consume_resistance(
        self, context: BattleContext, instance: StateInstance
    ) -> None:
        params = instance.runtime_params
        if not isinstance(params, ResistanceStateParams):
            raise TypeError("690083 RESISTANCE requires ResistanceStateParams")
        if params.remaining_uses <= 0:
            return
        new_uses = params.remaining_uses - 1
        if new_uses == 0:
            self._lifecycle.remove(context, instance.instance_id)
        else:
            self._replace(
                context, instance,
                dataclasses.replace(params, remaining_uses=new_uses),
            )

    def resolve_hit(
        self,
        context: BattleContext,
        *,
        source_id: str,
        target_id: str,
    ) -> Stage11HitOutcome:
        sure_hit = self.has_effective(
            context, source_id, OfficialStateId.SURE_HIT
        )
        evasion_probability = 0.0
        if not sure_hit:
            complement = 1.0
            for inst in self.effective_instances(
                context, target_id, OfficialStateId.EVASION
            ):
                params = inst.runtime_params
                if not isinstance(params, EvasionStateParams):
                    raise TypeError("690082 EVASION requires EvasionStateParams")
                complement *= 1.0 - params.probability
            evasion_probability = 1.0 - complement
            if self._roll(context, evasion_probability):
                return Stage11HitOutcome(
                    prevented=True,
                    prevented_by_state_id=OfficialStateId.EVASION.value,
                    evasion_probability=evasion_probability,
                    sure_hit=False,
                )

        resistance = self.effective_instances(
            context, target_id, OfficialStateId.BARRIER
        )
        if resistance:
            instance = resistance[0]
            self._consume_resistance(context, instance)
            if not sure_hit:
                return Stage11HitOutcome(
                    prevented=True,
                    prevented_by_state_id=OfficialStateId.BARRIER.value,
                    evasion_probability=evasion_probability,
                    sure_hit=False,
                    resistance_consumed_instance_id=instance.instance_id,
                )
            return Stage11HitOutcome(
                prevented=False,
                prevented_by_state_id=None,
                evasion_probability=evasion_probability,
                sure_hit=True,
                resistance_consumed_instance_id=instance.instance_id,
            )

        return Stage11HitOutcome(
            prevented=False,
            prevented_by_state_id=None,
            evasion_probability=evasion_probability,
            sure_hit=sure_hit,
        )

    def resolve_critical(
        self,
        context: BattleContext,
        *,
        source_id: str,
        damage_type: DamageType,
    ) -> CriticalOutcome:
        state_id = (
            OfficialStateId.CRITICAL
            if damage_type is DamageType.WEAPON
            else OfficialStateId.STRATEGY_CRITICAL
        )
        instances = self.effective_instances(context, source_id, state_id)
        if not instances:
            return CriticalOutcome(False, 0.0, 0.0, None)

        chance = 0.0
        bonus = 0.0
        for inst in instances:
            params = inst.runtime_params
            if not isinstance(params, CriticalStateParams):
                raise TypeError(f"{state_id.value} requires CriticalStateParams")
            chance += params.chance
            bonus += params.bonus
        chance = min(chance, 1.0)
        return CriticalOutcome(
            triggered=self._roll(context, chance),
            chance=chance,
            bonus=bonus,
            state_id=state_id.value,
        )

    def break_formation_active(self, context: BattleContext, source_id: str) -> bool:
        return self.has_effective(
            context, source_id, OfficialStateId.DEFENSE_PIERCE
        )

    def weakness_active(self, context: BattleContext, source_id: str) -> bool:
        return self.has_effective(
            context, source_id, OfficialStateId.WEAKNESS
        )

    def healing_block_active(self, context: BattleContext, target_id: str) -> bool:
        return self.has_effective(
            context, target_id, OfficialStateId.HEALING_BAN
        )

    def disarm_blocks(self, context: BattleContext, actor_id: str) -> bool:
        instances = self.effective_instances(
            context, actor_id, OfficialStateId.DISARM
        )
        if not instances:
            return False
        instance = instances[0]
        params = instance.runtime_params
        if not isinstance(params, DisarmStateParams):
            raise TypeError("690102 DISARM requires DisarmStateParams")
        return self._roll(context, params.block_probability)

    def see_through_rate(
        self,
        context: BattleContext,
        source_id: str,
        family: Stage11DamageFamily,
    ) -> float | None:
        instances = self.effective_instances(
            context, source_id, OfficialStateId.DAMAGE_REDUCTION_PIERCE
        )
        if not instances:
            return None
        if len(instances) != 1:
            raise ContractBoundaryViolation(
                "690221 multiple active instances lack frozen generic composition semantics"
            )
        params = instances[0].runtime_params
        if not isinstance(params, DamageReductionPierceStateParams):
            raise TypeError(
                "690221 DAMAGE_REDUCTION_PIERCE requires DamageReductionPierceStateParams"
            )
        eligibility = self.see_through_eligibility(family)
        if eligibility is SeeThroughEligibility.UNSUPPORTED_UNKNOWN:
            raise ContractBoundaryViolation(
                f"Damage family {family.value} is UNSUPPORTED_UNKNOWN for State 690221"
            )
        if eligibility is SeeThroughEligibility.SUPPORTED_NO_INVOCATION:
            return None
        return params.rate

    @staticmethod
    def see_through_eligibility(
        family: Stage11DamageFamily,
    ) -> SeeThroughEligibility:
        if family in {
            Stage11DamageFamily.NORMAL_ATTACK,
            Stage11DamageFamily.ASSAULT_SKILL,
            Stage11DamageFamily.COMMAND_XIEFANWEI,
            Stage11DamageFamily.REACTION_YIZHIBAOYUAN,
        }:
            return SeeThroughEligibility.SUPPORTED_APPLICABLE
        if family in {
            Stage11DamageFamily.EQUIPMENT_CAITA,
            Stage11DamageFamily.EQUIPMENT_CHONGZHEN,
            Stage11DamageFamily.EQUIPMENT_JINGJI,
            Stage11DamageFamily.COUNTER_QILINGSANJUN,
        }:
            return SeeThroughEligibility.SUPPORTED_NO_INVOCATION
        return SeeThroughEligibility.UNSUPPORTED_UNKNOWN

    def adjust_alert(
        self,
        context: BattleContext,
        *,
        target_id: str,
        candidate_damage: float,
    ) -> AlertAdjustment:
        if candidate_damage <= 0.0:
            return AlertAdjustment(candidate_damage, candidate_damage, None)
        for instance in self.effective_instances(
            context, target_id, OfficialStateId.VIGILANCE
        ):
            params = instance.runtime_params
            if not isinstance(params, AlertStateParams):
                raise TypeError("690099 ALERT requires AlertStateParams")
            # PROJECT_RUNTIME_DEFAULT: strict greater-than; equality is unobserved.
            if candidate_damage <= params.threshold:
                continue
            factor = 1.0 - (params.reduction_rate.numerator / params.reduction_rate.denominator)
            output = candidate_damage * factor
            new_uses = params.remaining_uses - 1
            if new_uses == 0:
                self._lifecycle.remove(context, instance.instance_id)
            else:
                self._replace(
                    context,
                    instance,
                    dataclasses.replace(params, remaining_uses=new_uses),
                )
            return AlertAdjustment(
                input_damage=candidate_damage,
                output_damage=output,
                consumed_instance_id=instance.instance_id,
            )
        return AlertAdjustment(candidate_damage, candidate_damage, None)

    def lifesteal_instances(
        self, context: BattleContext, source_id: str, damage_type: DamageType
    ) -> tuple[StateInstance, ...]:
        sid = (
            OfficialStateId.WEAPON_LIFESTEAL
            if damage_type is DamageType.WEAPON
            else OfficialStateId.STRATEGY_LIFESTEAL
        )
        result = self.effective_instances(context, source_id, sid)
        for item in result:
            if not isinstance(item.runtime_params, LifeStealStateParams):
                raise TypeError(f"{sid.value} requires LifeStealStateParams")
        return result

    def maintain_action_start(
        self, context: BattleContext, owner_id: str
    ) -> None:
        """Advance generic holder-action-start clocks.

        STUN has its own opportunity-consumption clock and is handled by
        consume_stun_natural_action().
        """
        for instance in tuple(context.states.states_of(owner_id)):
            params = instance.runtime_params
            if isinstance(params, StunStateParams):
                continue
            remaining = getattr(params, "remaining_action_starts", None)
            if remaining is None:
                continue
            if remaining <= 1:
                self._lifecycle.remove(context, instance.instance_id)
                continue
            self._replace(
                context,
                instance,
                dataclasses.replace(params, remaining_action_starts=remaining - 1),
            )

    def consume_stun_natural_action(
        self, context: BattleContext, owner_id: str
    ) -> bool:
        instances = self.instances(context, owner_id, OfficialStateId.STUN)
        if not instances:
            return False
        instance = instances[0]
        params = instance.runtime_params
        if not isinstance(params, StunStateParams):
            raise TypeError("690111 STUN requires StunStateParams")
        if params.remaining_blocks <= 0:
            self._lifecycle.remove(context, instance.instance_id)
            return False
        if not self.is_effective(context, instance):
            return False
        self._replace(
            context,
            instance,
            dataclasses.replace(params, remaining_blocks=params.remaining_blocks - 1),
        )
        return True
