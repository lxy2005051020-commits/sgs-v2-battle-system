"""Reusable settled-hit support: state grants or ordinary unscaled treatment.

Composes the aftermath port and canonical effect/formula/lifecycle owners.
State identities and round windows are data; no formation IDs occur here.
"""
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING
from .context import BattleContext
from .damage_aftermath_port import DamageAftermathFact, DamageAftermathPort, DamageHitTopology, AftermathResult
from .effects import ApplyStateEffect, EffectSourceRef, RecoverEffect
from .effect_result import EffectExecutionResult
from .numeric_validation import validate_probability, validate_nonnegative_finite
from .operation_identity import SourceType
from .provider_identity import SkillProviderRef
from .provider_validity import ProviderValidityStatus
from .reaction_permission_policy import ReactionPermissionPolicy
from .recovery_system import RecoveryModifierPolicy
from .skill_definition import ApplyStateSkillEffectSpec
from .stage9_integerization import ExactRatio
from .state_definition import StateDefinition
from .state_registry import StateRegistry
from .state_runtime_params import StateRuntimeParams
from .treatment_formula import TreatmentModifierSnapshot

if TYPE_CHECKING:
    from .battle_systems import BattleSystems

AFTER_DAMAGE_SUPPORT_STATE_ID = "runtime_after_damage_support"


@dataclass(frozen=True, slots=True)
class AfterDamageSupportParams(StateRuntimeParams):
    probability: float
    first_round: int
    last_round: int | None = None
    state_spec: ApplyStateSkillEffectSpec | None = None
    recovery_rate: float | None = None
    reject_existing_state: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "probability", validate_probability(self.probability, "probability"))
        if type(self.first_round) is not int or self.first_round < 1:
            raise ValueError("first_round must be positive integer")
        if self.last_round is not None and (type(self.last_round) is not int or self.last_round < self.first_round):
            raise ValueError("last_round must be >= first_round")
        if (self.state_spec is None) == (self.recovery_rate is None):
            raise ValueError("exactly one state_spec or recovery_rate is required")
        if self.state_spec is not None and not isinstance(self.state_spec, ApplyStateSkillEffectSpec):
            raise TypeError("state_spec must be ApplyStateSkillEffectSpec")
        if self.recovery_rate is not None:
            object.__setattr__(self, "recovery_rate", validate_nonnegative_finite(self.recovery_rate, "recovery_rate"))
        if type(self.reject_existing_state) is not bool:
            raise TypeError("reject_existing_state must be bool")
        if self.reject_existing_state and self.state_spec is None:
            raise ValueError("reject_existing_state requires a state grant")


DEFINITION = StateDefinition(AFTER_DAMAGE_SUPPORT_STATE_ID, "受击后支援",
                             runtime_params_type=AfterDamageSupportParams)


def register_after_damage_support_state(registry: StateRegistry) -> None:
    try:
        resident = registry.get_definition(DEFINITION.state_id)
    except KeyError:
        registry.register_definition(DEFINITION)
    else:
        if resident != DEFINITION:
            raise ValueError("incompatible after-damage support schema")


class AfterDamageSupportPort:
    def __init__(self, upstream: DamageAftermathPort, systems: "BattleSystems") -> None:
        self.upstream = upstream
        self.systems = systems

    def commit_aftermath(self, context: BattleContext, fact: DamageAftermathFact) -> AftermathResult:
        if not isinstance(fact, DamageAftermathFact):
            raise TypeError("expected DamageAftermathFact")
        # Existing attribute reactions and first aid retain their order. Support
        # follows them; this peripheral ordering is an explicit engineering model.
        ordinary = self.upstream.commit_aftermath(context, fact)
        results = self.react(context, fact)
        # Preserve the upstream typed recovery-opportunity results. Canonical
        # support effects remain observable through events and support history.
        return replace(ordinary, executed=ordinary.executed or bool(results))

    def react(self, context: BattleContext, fact: DamageAftermathFact) -> tuple[EffectExecutionResult, ...]:
        s = self.systems
        if context.ended or s.finalization_coordinator.is_latched_or_finalized:
            return ()
        if fact.hit_topology is not DamageHitTopology.RESOLVED_HIT or fact.target_defeated:
            return ()
        target = context.units.get(fact.target_id)
        if target is None or not target.is_alive:
            return ()
        drivers = s.state_effectiveness_policy.effective_instances(
            context, target.unit_id, AFTER_DAMAGE_SUPPORT_STATE_ID)
        # Dormant adapter must not add qualification queries to the frozen
        # first-aid lane when no support has been installed.
        if not drivers or not ReactionPermissionPolicy.can_trigger_recovery(fact.source_type):
            return ()
        results = []
        for driver in drivers:
            params = driver.runtime_params
            if not isinstance(params, AfterDamageSupportParams):
                raise TypeError("support requires typed params")
            if (context.current_round < params.first_round or
                    params.last_round is not None and context.current_round > params.last_round):
                continue
            if driver.source_id is None or driver.source_skill_slot is None or driver.source_skill_id is None:
                raise ValueError("support requires canonical provider provenance")
            ref = SkillProviderRef(driver.source_id, driver.source_skill_slot, driver.source_skill_id)
            provider = context.units.get(ref.owner_id)
            if provider is None or not provider.is_alive:
                continue
            if s.provider_validity_policy.evaluate_provider(context, ref).status is not ProviderValidityStatus.VALID:
                continue
            cursors = context.metadata.setdefault("after_damage_support_cursors", set())
            key = (driver.instance_id, driver.current_generation_id, fact.damage_instance_id)
            if key in cursors:
                continue
            # Cursor is battle-scoped and committed BEFORE RNG/effects, including
            # failures and nonstacking rejection. Nested replay cannot reroll.
            cursors.add(key)
            row = {"damage_instance_id": fact.damage_instance_id, "round": context.current_round,
                   "target_id": target.unit_id, "provider_id": ref.owner_id,
                   "provider_slot": int(ref.skill_slot), "skill_id": ref.skill_id,
                   "driver_instance_id": driver.instance_id, "actual_loss": fact.actual_target_troop_loss,
                   "probability": params.probability}
            context.metadata.setdefault("after_damage_support_history", []).append(row)
            if not context.random.chance(params.probability):
                row["status"] = "PROBABILITY_FAILED"
                continue
            if params.state_spec is not None:
                spec = params.state_spec
                # Declarative nonstacking grant precondition; actual application,
                # conflict, admission and consumption remain canonical owners.
                if params.reject_existing_state and context.states.find(owner_id=target.unit_id, state_id=spec.state_id):
                    row["status"] = "REJECTED_EXISTING_STATE"
                    continue
                result = s.effect_executor.execute(context, ApplyStateEffect(spec.state_id,
                    target.unit_id, ref.owner_id, ref.skill_id,
                    runtime_params=spec.runtime_params, expires_round=spec.expires_round,
                    expires_phase=spec.expires_phase,
                    source_ref=EffectSourceRef(SourceType.ACTIVE_SKILL, ref.owner_id, ref.skill_id, ref.skill_slot)))
                row.update(kind="STATE_GRANT", state_id=spec.state_id, status="APPLIED")
            else:
                source_troops = provider.troops
                nominal = s.treatment_formula_system.calculate(rate=params.recovery_rate,
                    source_troops=source_troops, source_attribute=0,
                    modifiers=TreatmentModifierSnapshot(
                        red_pool_multiplier=ExactRatio(100 + 2 * provider.advancement_stars, 100)))
                result = s.effect_executor.execute(context, RecoverEffect(ref.owner_id,
                    target.unit_id, nominal.nominal_recovery, source_skill_id=ref.skill_id,
                    source_state_id=driver.state_id, source_state_instance_id=driver.instance_id,
                    modifier_policy=RecoveryModifierPolicy.APPLY))
                row.update(kind="RECOVERY", source_troops=source_troops, source_attribute=0,
                    base_rate=params.recovery_rate, nominal_recovery=nominal.nominal_recovery,
                    status="EXECUTED")
            results.append(result)
        return tuple(results)
