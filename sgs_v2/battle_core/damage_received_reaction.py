"""Typed post-loss reaction composed over the public damage aftermath port.

The upstream port retains recovery authority. This adapter selects no new target,
changes no troops/base attributes and uses canonical state admission/lifetimes.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING
from .context import BattleContext
from .state_registry import StateRegistry
from .damage_aftermath_port import DamageAftermathPort, AftermathResult
if TYPE_CHECKING:
    from .battle_systems import BattleSystems

from .damage_aftermath_port import DamageAftermathFact, DamageHitTopology
from .state_runtime_params import StateRuntimeParams
from .state_definition import StateDefinition
from .state_application import StateCandidate, ApplicationDisposition
from .state_lifetime import StateLifetimeSpec
from .provider_identity import SkillProviderRef
from .dependency_evaluation import ProviderNode
from .provider_validity import ProviderDependency
from .state_modifiers import (ATTRIBUTE_BONUS_STATE_ID, ACTIVATION_RATE_BONUS_STATE_ID,
    BoundedAttributeBonusParams, BoundedActivationRateBonusParams)
from .skill_definition import SkillType
from .numeric_validation import validate_probability, validate_nonnegative_finite

DAMAGE_RECEIVED_REACTION_STATE_ID = "runtime_damage_received_attribute_reaction"


@dataclass(frozen=True, slots=True)
class DamageReceivedReactionParams(StateRuntimeParams):
    probability: float
    attribute: str
    steal_amount: float
    active_rate_reduction: float
    max_stacks: int
    duration_rounds: int = 2
    source_attribute_at_application: float | None = None
    scaling_model_key: str | None = None
    processed_damage_ids: tuple[str, ...] = ()

    def __post_init__(self):
        object.__setattr__(self, "probability", validate_probability(self.probability, "probability"))
        object.__setattr__(self, "steal_amount", validate_nonnegative_finite(self.steal_amount, "steal_amount"))
        object.__setattr__(self, "active_rate_reduction", validate_probability(self.active_rate_reduction, "active_rate_reduction"))
        if self.attribute not in ("attack", "defense", "intelligence", "speed"):
            raise ValueError("unsupported reaction attribute")
        for n in ("max_stacks", "duration_rounds"):
            if type(getattr(self, n)) is not int or getattr(self, n) < 1:
                raise ValueError(f"{n} must be a positive integer")
        object.__setattr__(self, "processed_damage_ids", tuple(self.processed_damage_ids))
        if self.source_attribute_at_application is not None:
            object.__setattr__(self, "source_attribute_at_application", validate_nonnegative_finite(
                self.source_attribute_at_application, "source_attribute_at_application"))
        if self.scaling_model_key is not None and (not isinstance(self.scaling_model_key, str) or not self.scaling_model_key.strip()):
            raise ValueError("scaling_model_key must be nonempty when supplied")


DEFINITION = StateDefinition(DAMAGE_RECEIVED_REACTION_STATE_ID, "受伤后属性反应",
    runtime_params_type=DamageReceivedReactionParams)


def register_damage_received_reaction_definition(registry: StateRegistry) -> None:
    try:
        resident = registry.get_definition(DEFINITION.state_id)
    except KeyError:
        registry.register_definition(DEFINITION)
    else:
        if resident != DEFINITION:
            raise ValueError("incompatible damage received reaction schema")


class DamageReceivedReactionPort:
    def __init__(self, upstream: DamageAftermathPort, systems: BattleSystems) -> None:
        self.upstream = upstream
        self.systems = systems

    def commit_aftermath(self, context: BattleContext, fact: DamageAftermathFact) -> AftermathResult:
        if not isinstance(fact, DamageAftermathFact):
            raise TypeError("expected DamageAftermathFact")
        # Evaluate the branch on the settled hit, before any first-aid recovery.
        self.react(context, fact)
        return self.upstream.commit_aftermath(context, fact)

    def react(self, context: BattleContext, fact: DamageAftermathFact) -> None:
        s = self.systems
        if context.ended or s.finalization_coordinator.is_latched_or_finalized:
            return
        if fact.hit_topology is not DamageHitTopology.RESOLVED_HIT or fact.actual_target_troop_loss <= 0 or fact.target_defeated:
            return
        target = context.units.get(fact.target_id)
        attacker = context.units.get(fact.source_unit_id)
        if target is None or attacker is None or not target.is_alive or not attacker.is_alive or target.team_id == attacker.team_id:
            return
        for marker in s.state_effectiveness_policy.effective_instances(context, target.unit_id, DAMAGE_RECEIVED_REACTION_STATE_ID):
            params = marker.runtime_params
            if fact.damage_instance_id in params.processed_damage_ids:
                continue
            if marker.source_id is None or marker.source_skill_slot is None:
                raise ValueError("reaction requires a canonical provider")
            if not context.units[marker.source_id].is_alive:
                continue
            provider = SkillProviderRef(marker.source_id, marker.source_skill_slot, marker.source_skill_id)
            if not s.dependency_evaluation_support.evaluate(context, ProviderNode(provider)).valid:
                continue
            s.state_lifecycle_system.refresh(context, instance_id=marker.instance_id,
                runtime_params=replace(params, processed_damage_ids=params.processed_damage_ids + (fact.damage_instance_id,)))
            if not context.random.chance(params.probability):
                continue
            key = f"{fact.damage_instance_id}:{target.unit_id}"
            # Exact cross multiplication, using the post-hit troop snapshot.
            steal = fact.target_troops_after * attacker.max_troops < attacker.troops * target.max_troops
            lifetime = StateLifetimeSpec.round_calendar(expires_round=context.current_round + params.duration_rounds,
                expires_phase="ROUND_START")
            deps = (ProviderDependency(provider, "DAMAGE_RECEIVED_REACTION_PROVIDER"),)

            def candidate(owner_id, state_id, payload):
                return StateCandidate(state_id=state_id, owner_id=owner_id, runtime_params_candidate=payload,
                    source_id=marker.source_id, source_skill_id=marker.source_skill_id,
                    source_skill_slot=marker.source_skill_slot, lifetime_spec=lifetime, provider_dependencies=deps,
                    application_provenance=key)

            if steal:
                group = "received_attribute_transfer"
                proposals = (
                    candidate(attacker.unit_id, ATTRIBUTE_BONUS_STATE_ID,
                        BoundedAttributeBonusParams(params.attribute, -params.steal_amount, key, group, params.max_stacks)),
                    candidate(target.unit_id, ATTRIBUTE_BONUS_STATE_ID,
                        BoundedAttributeBonusParams(params.attribute, params.steal_amount, key, group, params.max_stacks)),
                )
            else:
                proposals = (candidate(attacker.unit_id, ACTIVATION_RATE_BONUS_STATE_ID,
                    BoundedActivationRateBonusParams(SkillType.ACTIVE, -params.active_rate_reduction,
                        key, "received_active_rate_reduction", params.max_stacks)),)
            # Preflight both sides before a transfer so a cap cannot leave half a pair.
            if any(not s.state_admission_policy.evaluate_candidate(context, p).allowed or
                s.state_conflict_policy.evaluate_conflict(context, p, tuple(context.states.find(
                    owner_id=p.owner_id, state_id=p.state_id))).disposition is not ApplicationDisposition.CREATE
                for p in proposals):
                continue
            for p in proposals:
                result = s.state_application_coordinator.apply_candidate(context, p)
                if not result.committed:
                    raise RuntimeError("preflighted reaction state did not commit")
