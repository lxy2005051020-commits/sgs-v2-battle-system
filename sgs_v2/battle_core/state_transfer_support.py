"""Reusable, bounded state transfer through canonical application/removal owners.

Complex snapshots and relationship-bearing params are explicit boundaries.
Transfer provenance is recorded separately from the new application provider.
"""
from dataclasses import replace
from typing import TYPE_CHECKING
from .context import BattleContext
from .state_instance import StateInstance
from .provider_identity import SkillProviderRef
from .state_runtime_params import StateRuntimeParams
if TYPE_CHECKING:
    from .battle_systems import BattleSystems

from .damage_rate_modifier import DAMAGE_RATE_STATE_ID, DamageRateParams, RoundDamageRateParams
from .feng_shi_zhen import FENG_SHI_ZHEN_MODIFIER_STATE_ID, FengShiZhenModifierParams
from .probabilistic_target_priority import TARGET_PRIORITY_STATE_ID
from .outgoing_damage_reduction import OUTGOING_DAMAGE_REDUCTION_STATE_ID, OutgoingDamageReductionParams
from .dependency_evaluation import StateNode
from .state_effectiveness import StateEffectivenessContribution, InactivityCause, LocalRuleCauseRef
from .provider_validity import ProviderDependency
from .enums import BattlePhase
from .official_state_catalog import OFFICIAL_STATE_CATALOG, OfficialStateCategory
from .state_application import StateCandidate
from .state_lifetime import StateLifetimeSpec
from .state_modifiers import (ATTRIBUTE_BONUS_STATE_ID, AttributeBonusParams,
    INCOMING_DAMAGE_REDUCTION_STATE_ID, IncomingDamageReductionParams)
from .state_removal import RemovalDecision, RemovalDecisionStatus, RemovalOperation
from .state_runtime_params import EmptyStateRuntimeParams
from .stage11_state_params import Stage11TimedFlagParams, DisarmStateParams, StunStateParams

NEGATIVE_STATE_IDS = frozenset(e.state_id.value for e in OFFICIAL_STATE_CATALOG
    if e.category is OfficialStateCategory.CONTROL) | frozenset((
        "burn", "flood", "poison", "rout", "sandstorm", "rebellion", "ambush", "chain_link"))


def is_negative_state(state: StateInstance) -> bool:
    p = state.runtime_params
    return (state.state_id in NEGATIVE_STATE_IDS
        or (state.state_id == ATTRIBUTE_BONUS_STATE_ID and isinstance(p, AttributeBonusParams) and p.amount < 0)
        or (state.state_id == DAMAGE_RATE_STATE_ID and isinstance(p, DamageRateParams)
            and (p.outgoing_rate < 0 or p.incoming_rate > 0))
        or (state.state_id == FENG_SHI_ZHEN_MODIFIER_STATE_ID and isinstance(p, FengShiZhenModifierParams)
            and (p.outgoing_rate < 0 or p.incoming_rate > 0))
        or state.state_id == OUTGOING_DAMAGE_REDUCTION_STATE_ID)


def is_incoming_reduction(state: StateInstance) -> bool:
    p = state.runtime_params
    return ((state.state_id == INCOMING_DAMAGE_REDUCTION_STATE_ID
             and isinstance(p, IncomingDamageReductionParams) and p.rate > 0)
        or (state.state_id == DAMAGE_RATE_STATE_ID and isinstance(p, DamageRateParams)
            and (p.incoming_rate < 0 or isinstance(p, RoundDamageRateParams)))
        or (state.state_id == FENG_SHI_ZHEN_MODIFIER_STATE_ID and isinstance(p, FengShiZhenModifierParams)
            and p.incoming_rate < 0)
        or state.state_id == TARGET_PRIORITY_STATE_ID)


def transfer_removal_adapter(context, operation, state):
    # Authorize exactly the source instance of a preflighted transfer, never
    # arbitrary scripted removals. Earlier protection adapters still take priority.
    if (operation is RemovalOperation.SCRIPTED_GAMEPLAY_REMOVE
            and state.instance_id in context.metadata.get("_state_transfer_removal_permits", ())):
        return RemovalDecision(RemovalDecisionStatus.ALLOW, operation, "RUNTIME_TRANSFER_SOURCE_REMOVE")
    return None


def transfer_effectiveness_adapter(context, state, session):
    ref = context.metadata.get("state_transfer_providers", {}).get(state.instance_id)
    if ref is None:
        return StateEffectivenessContribution()
    runtime = context.skill_runtimes.get(ref.owner_id, ref.skill_slot)
    unit = context.units.get(ref.owner_id)
    if runtime is None or not runtime.enabled or runtime.definition.skill_id != ref.skill_id or unit is None or not unit.is_alive:
        return StateEffectivenessContribution(inactivity_causes=(InactivityCause(
            "TRANSFER_PROVIDER_UNAVAILABLE", LocalRuleCauseRef(state.instance_id)),))
    return StateEffectivenessContribution()


class StateTransferSupport:
    def __init__(self, systems: "BattleSystems") -> None:
        self._systems = systems

    @staticmethod
    def split_params(state: StateInstance, *, reduction: bool) -> tuple[StateRuntimeParams, StateRuntimeParams | None]:
        p = state.runtime_params
        if type(p) is IncomingDamageReductionParams and reduction:
            return p, None
        if type(p) is AttributeBonusParams and not reduction and p.amount < 0:
            return p, None
        if type(p) is OutgoingDamageReductionParams and not reduction:
            return p, None
        if type(p) is FengShiZhenModifierParams:
            incoming = p.incoming_rate if (p.incoming_rate < 0 if reduction else p.incoming_rate > 0) else 0
            outgoing = p.outgoing_rate if not reduction and p.outgoing_rate < 0 else 0
            rest = FengShiZhenModifierParams(p.outgoing_rate-outgoing, p.incoming_rate-incoming)
            return DamageRateParams(outgoing, incoming), rest if rest.outgoing_rate or rest.incoming_rate else None
        if type(p) is DamageRateParams:
            if p.prerequisite_state_id is not None:
                raise NotImplementedError("state transfer requires a confirmed prerequisite rebinding rule")
            incoming = p.incoming_rate if (p.incoming_rate < 0 if reduction else p.incoming_rate > 0) else 0
            outgoing = p.outgoing_rate if not reduction and p.outgoing_rate < 0 else 0
            moved = DamageRateParams(outgoing, incoming)
            rest = DamageRateParams(p.outgoing_rate - outgoing, p.incoming_rate - incoming)
            return moved, rest if rest.outgoing_rate or rest.incoming_rate else None
        if not reduction and type(p) in (EmptyStateRuntimeParams, Stage11TimedFlagParams,
                                         DisarmStateParams, StunStateParams):
            if isinstance(p, EmptyStateRuntimeParams):
                return p, None
            # Expiry is the new round boundary; action counters must not truncate it.
            if type(p) is StunStateParams:
                return replace(p, source_dependent=False), None
            return replace(p, remaining_action_starts=None, source_dependent=False), None
        raise NotImplementedError(f"unsupported state transfer schema: {state.state_id}/{type(p).__name__}; "
                                  "snapshot/relationship transfer rules remain unconfirmed")

    def transfer(self, context: BattleContext, state: StateInstance, target_id: str,
                 provider: SkillProviderRef, *, reduction: bool = False) -> dict[str, object]:
        s = self._systems
        moved, remainder = self.split_params(state, reduction=reduction)
        new_state_id = DAMAGE_RATE_STATE_ID if type(state.runtime_params) is FengShiZhenModifierParams else state.state_id
        original_dependencies = s.dependency_evaluation_support.prerequisites(StateNode(state.instance_id))
        candidate = StateCandidate(new_state_id, target_id, moved,
            source_id=provider.owner_id, source_skill_id=provider.skill_id,
            source_skill_slot=provider.skill_slot,
            lifetime_spec=StateLifetimeSpec.explicit_phase_expiry(
                expires_round=context.current_round, expires_phase=BattlePhase.ROUND_END.value),
            provider_dependencies=(ProviderDependency(provider, "RUNTIME_TRANSFER_PROVIDER"),),
            application_provenance=f"TRANSFER:{state.instance_id}:{state.current_generation_id}")
        # Rejection leaves the source intact (e.g. insight or conflict).
        permits = context.metadata.setdefault("_state_transfer_removal_permits", set())
        permits.add(state.instance_id)
        try:
            removal = s.state_removal_policy.evaluate_removal(
                context, RemovalOperation.SCRIPTED_GAMEPLAY_REMOVE, state)
            if not removal.allowed:
                return {"status": "SOURCE_REMOVE_REJECTED", "reason": removal.reason_rule_id}
            result = s.state_application_coordinator.apply_candidate(context, candidate)
            if not result.committed:
                return {"status": result.status.value, "reason": result.reason_rule_id}
            context.metadata.setdefault("state_transfer_providers", {})[result.instance.instance_id] = provider
            removed = s.state_removal_coordinator.remove(context,
                operation=RemovalOperation.SCRIPTED_GAMEPLAY_REMOVE, instance_id=state.instance_id)
            if removed.removed_instance is None:
                raise RuntimeError("preflighted transfer source removal did not commit")
            if remainder is not None:
                # Keep unrelated dimensions, original provider and original expiry.
                lifetime = state.lifetime_spec
                if lifetime is None and state.expires_round is not None:
                    lifetime = StateLifetimeSpec.explicit_phase_expiry(
                        expires_round=state.expires_round, expires_phase=state.expires_phase)
                rest_result = s.state_application_coordinator.apply_candidate(context, StateCandidate(
                    state.state_id, state.owner_id, remainder, source_id=state.source_id,
                    source_skill_id=state.source_skill_id, source_skill_slot=state.source_skill_slot,
                    lifetime_spec=lifetime))
                if not rest_result.committed:
                    raise RuntimeError("transfer remainder restoration did not commit")
                for prerequisite in original_dependencies:
                    s.dependency_evaluation_support.add_dependency(StateNode(rest_result.instance.instance_id), prerequisite)
            return {"status": "TRANSFERRED", "original_instance_id": state.instance_id,
                "original_generation_id": state.current_generation_id.value,
                "original_source_id": state.source_id, "original_skill_id": state.source_skill_id,
                "original_slot": int(state.source_skill_slot) if state.source_skill_slot is not None else None,
                "source_owner_id": state.owner_id, "target_id": target_id,
                "new_instance_id": result.instance.instance_id, "state_id": state.state_id}
        finally:
            permits.discard(state.instance_id)
