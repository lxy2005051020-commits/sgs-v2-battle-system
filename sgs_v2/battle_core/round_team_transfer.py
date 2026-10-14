"""Generic three-lane round support: reduction/negative transfer and attribute theft."""
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from .action_start_role_split import RoleSplitRuleHookSystem
from .context import BattleContext
from .effect_result import EffectExecutionResult, ApplyStateEffectResult
from .state_application import StateCandidate, ApplicationDisposition
from .state_lifetime import StateLifetimeSpec
from .provider_validity import ProviderDependency
from .effects import ApplyStateEffect, EffectSourceRef
from .enums import BattlePhase
from .numeric_validation import validate_probability, validate_nonnegative_finite
from .operation_identity import SourceType
from .priority_target_system import PriorityTargetSystem
from .provider_identity import SkillProviderRef
from .rule_hooks import RoundStartHook
from .state_definition import StateDefinition
from .state_effectiveness import StateEffectivenessContribution, InactivityCause, LocalRuleCauseRef
from .state_modifiers import ATTRIBUTE_BONUS_STATE_ID, AttributeBonusParams
from .state_runtime_params import StateRuntimeParams
from .state_transfer_support import StateTransferSupport, is_incoming_reduction, is_negative_state
from .target_operation import (TargetOperationProducer, TargetRelation, TargetCardinality,
    TargetSelectorKind, TargetEligibilityContext, TargetOperationDomain, TargetPurpose)
if TYPE_CHECKING:
    from .battle_systems import BattleSystems

ROUND_TEAM_TRANSFER_STATE_ID = "runtime_round_team_transfer"


@dataclass(frozen=True, slots=True)
class RoundTeamTransferParams(StateRuntimeParams):
    probability: float
    attribute_amount: float

    def __post_init__(self):
        object.__setattr__(self, "probability", validate_probability(self.probability))
        object.__setattr__(self, "attribute_amount", validate_nonnegative_finite(self.attribute_amount, "attribute_amount"))


DEFINITION = StateDefinition(ROUND_TEAM_TRANSFER_STATE_ID, "回合团队状态转移与属性偷取",
                             runtime_params_type=RoundTeamTransferParams)


def register_round_team_transfer_state(registry) -> None:
    try:
        existing = registry.get_definition(DEFINITION.state_id)
    except KeyError:
        registry.register_definition(DEFINITION)
    else:
        if existing != DEFINITION:
            raise ValueError("incompatible round team transfer schema")


def round_transfer_effectiveness_adapter(context, state, session):
    if state.state_id != ROUND_TEAM_TRANSFER_STATE_ID:
        return StateEffectivenessContribution()
    runtime = context.skill_runtimes.get(state.source_id, state.source_skill_slot)
    provider = context.units.get(state.source_id)
    if (runtime is None or not runtime.enabled or runtime.definition.skill_id != state.source_skill_id
            or provider is None or not provider.is_alive):
        return StateEffectivenessContribution(inactivity_causes=(InactivityCause(
            "ROUND_TRANSFER_PROVIDER_UNAVAILABLE", LocalRuleCauseRef(state.instance_id)),))
    return StateEffectivenessContribution()


class RoundTeamTransferSupport:
    def __init__(self, systems: "BattleSystems") -> None:
        self._systems = systems
        self._targets = PriorityTargetSystem(systems.target_system)
        self._transfer = StateTransferSupport(systems)

    def _targets_for(self, context: BattleContext, ref: SkillProviderRef, key: str,
                     relation: TargetRelation, *, single: bool = True, random: bool = True):
        s = self._systems
        provider = context.get_unit(ref.owner_id)
        candidates = (s.target_system.allies(context, provider) if relation is TargetRelation.ALLY
                      else s.target_system.enemies(context, provider))
        operation = TargetOperationProducer.new_query(context, actor_id=ref.owner_id, producer_ref=ref,
            admitted_operation_key=key, relation=relation,
            cardinality=TargetCardinality.SINGLE if single else TargetCardinality.FIXED_ALL,
            selector_kind=TargetSelectorKind.RANDOM if random else TargetSelectorKind.DETERMINISTIC,
            eligibility_context=TargetEligibilityContext(TargetOperationDomain.SKILL,
                TargetPurpose.FRIENDLY_SUPPORT if relation is TargetRelation.ALLY else TargetPurpose.HOSTILE))
        decision = s.skill_target_policy.evaluate(context, operation, candidates)
        if not decision.supported or (single and len(decision.required_target_ids) > 1):
            raise NotImplementedError("unsupported round support target-policy boundary")
        candidates = [u for u in candidates if u.unit_id in decision.eligible_candidate_ids]
        if not single:
            return s.target_system.random_units(context, candidates, count=len(candidates))
        required = [u for u in candidates if u.unit_id in decision.required_target_ids]
        if required:
            return required
        if random:
            return s.target_system.random_units(context, candidates, count=1)
        return self._targets.lowest_attribute_units(context, candidates, s.attribute_system, "defense")[:1]

    def _states(self, context, units, predicate):
        return [state for u in units for state in context.states.find(owner_id=u.unit_id)
                if predicate(state) and self._systems.state_effectiveness_policy.evaluate_state(context, state).effective]

    def execute(self, context: BattleContext, hook: RoundStartHook) -> tuple[EffectExecutionResult, ...]:
        s = self._systems
        if context.ended or s.finalization_coordinator.is_latched_or_finalized:
            return ()
        results = []
        for driver in tuple(context.states.find(state_id=ROUND_TEAM_TRANSFER_STATE_ID)):
            if not s.state_effectiveness_policy.evaluate_state(context, driver).effective:
                continue
            cursors = context.metadata.setdefault("round_team_transfer_cursors", {})
            key = (driver.instance_id, driver.current_generation_id)
            if hook.round_no <= cursors.get(key, 0):
                continue
            p = driver.runtime_params
            if not isinstance(p, RoundTeamTransferParams):
                raise TypeError("round support requires typed params")
            ref = SkillProviderRef(driver.source_id, driver.source_skill_slot, driver.source_skill_id)
            # Draw all three independent lane decisions before any target RNG.
            decisions = tuple(context.random.chance(p.probability) for _ in range(3))
            row = {"round": hook.round_no, "provider_id": ref.owner_id,
                "provider_slot": int(ref.skill_slot), "skill_id": ref.skill_id,
                "probability": p.probability, "attribute_amount": p.attribute_amount,
                "decisions": decisions, "transfers": [], "theft": None}
            prefix = f"round-transfer:{driver.instance_id}:{hook.round_no}"
            if decisions[0]:
                enemies = self._targets_for(context, ref, prefix+":reduction-source", TargetRelation.ENEMY)
                allies = self._targets_for(context, ref, prefix+":reduction-target", TargetRelation.ALLY)
                states = self._states(context, enemies,
                    lambda state: is_incoming_reduction(state, context.current_round))
                # Preflight schemas before moving any member of this bundle.
                for state in states:
                    self._transfer.split_params(state, reduction=True, context=context, systems=s)
                if allies:
                    row["transfers"].extend(self._transfer.transfer(context, st, allies[0].unit_id,
                        ref, reduction=True) for st in states)
            if decisions[1]:
                # Source inspection is a read of team state, not a friendly
                # support application. A captured ally's negative state must
                # remain transferable without making that ally a buff target.
                allies = s.target_system.allies(context,context.get_unit(ref.owner_id))
                states = self._states(context, allies,
                    lambda state: is_negative_state(state, context.current_round))
                kinds = sorted({st.state_id for st in states})
                count = min(len(kinds), context.random.randint(1, 2)) if kinds else 0
                chosen = context.random.sample(kinds, count) if count and count < len(kinds) else kinds
                states = [st for st in states if st.state_id in chosen]
                for state in states:
                    self._transfer.split_params(state, reduction=False, context=context, systems=s)
                enemies = self._targets_for(context, ref, prefix+":negative-target", TargetRelation.ENEMY) if states else []
                row["negative_kinds"] = chosen
                if enemies:
                    row["transfers"].extend(self._transfer.transfer(context, st, enemies[0].unit_id,
                        ref) for st in states)
            if decisions[2]:
                allies = self._targets_for(context, ref, prefix+":attribute-target", TargetRelation.ALLY, random=False)
                enemies = self._targets_for(context, ref, prefix+":attribute-source", TargetRelation.ENEMY, single=False, random=False)
                if allies and enemies:
                    target = allies[0]
                    source = EffectSourceRef(SourceType.ACTIVE_SKILL, ref.owner_id, ref.skill_id, ref.skill_slot)
                    proposals = [StateCandidate(ATTRIBUTE_BONUS_STATE_ID, unit.unit_id,
                        AttributeBonusParams("defense", amount), source_id=ref.owner_id,
                        source_skill_id=ref.skill_id, source_skill_slot=ref.skill_slot,
                        lifetime_spec=StateLifetimeSpec.explicit_phase_expiry(
                            expires_round=hook.round_no, expires_phase=BattlePhase.ROUND_END.value),
                        provider_dependencies=(ProviderDependency(ref, "ROUND_SUPPORT_ATTRIBUTE_PROVIDER"),))
                        for unit, amount in [(u, -p.attribute_amount) for u in enemies]
                        + [(target, p.attribute_amount * len(enemies))]]
                    # A denied target or same-source conflict must not create half
                    # of the transfer. Reuse the paired-attribute admission pattern.
                    allowed = all(s.state_admission_policy.evaluate_candidate(context, candidate).allowed
                        and s.state_conflict_policy.evaluate_conflict(context, candidate,
                            tuple(context.states.find(owner_id=candidate.owner_id,
                                state_id=candidate.state_id))).disposition is ApplicationDisposition.CREATE
                        for candidate in proposals)
                    if allowed:
                        for candidate in proposals:
                            result = s.state_application_coordinator.apply_candidate(context, candidate)
                            if not result.committed:
                                raise RuntimeError("preflighted attribute transfer did not commit")
                            context.metadata.setdefault("state_transfer_providers", {})[result.instance.instance_id] = ref
                            declaration = ApplyStateEffect(ATTRIBUTE_BONUS_STATE_ID, candidate.owner_id,
                                ref.owner_id, ref.skill_id, hook.round_no, BattlePhase.ROUND_END.value,
                                candidate.runtime_params_candidate, source)
                            results.append(ApplyStateEffectResult(declaration, result.instance))
                        row["theft"] = {"target_id": target.unit_id, "enemy_ids": [u.unit_id for u in enemies],
                            "amount_per_enemy": p.attribute_amount, "total": p.attribute_amount * len(enemies)}
                    else:
                        row["theft_status"] = "REJECTED_ATOMIC_ATTRIBUTE_PREFLIGHT"
            cursors[key] = hook.round_no
            context.metadata.setdefault("round_team_transfer_history", []).append(row)
        return tuple(results)


class RoundTeamTransferRuleHookSystem(RoleSplitRuleHookSystem):
    def __init__(self, *args, round_transfer_support, **kwargs):
        super().__init__(*args, **kwargs)
        self._round_transfer_support = round_transfer_support

    def process(self, context, hook):
        ordinary = super().process(context, hook)
        if not isinstance(hook, RoundStartHook) or ordinary.batch_status != "COMPLETED":
            return ordinary
        results = self._round_transfer_support.execute(context, hook)
        return replace(ordinary, intent_results=ordinary.intent_results + results,
                       effect_results=ordinary.effect_results + results)
