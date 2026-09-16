from __future__ import annotations

import math
from typing import TYPE_CHECKING

from .damage_aftermath_port import DamageAftermathFact, DamageHitTopology
from .effects import EffectSourceRef
from .operation_identity import SourceType
from .reaction_permission_policy import ReactionPermissionPolicy
from .recovery_system import RecoveryRequest, RecoverySystem
from .rule_intent import (
    RecoveryOpportunity,
    RecoveryOpportunityKind,
    RecoveryOpportunityResult,
    RuleIntentExecutionDescriptor,
    RuleIntentKind,
)
from .skill_runtime_registry import (
    PersistentSourceSkillGate,
    PersistentSourceSkillGateMode,
    SkillRuntimeRegistry,
)
from .stage10_state_params import RecoveryModelKind, RecoveryPotencyContext
from .state_generation import PersistentLifecycleWindow, StateGenerationSnapshot
from .state_instance import StateInstance

if TYPE_CHECKING:
    from .context import BattleContext


class RecoveryOpportunitySystem:
    """
    Unified authoritative recovery opportunity engine (STAGE10.md §18, §22).
    Evaluates both FIRST_AID_AFTER_DAMAGE reactions and RECUPERATION_ACTION_START opportunities.

    Enforces:
    - Normalized Gate Sequence: Gates 1 through 5.
    - S10-FG-H02: RECUPERATION operates with aftermath_fact=None and never queries ReactionPermissionPolicy.
    - Zero-loss eligibility: resolved hits with 0 loss are eligible for FIRST_AID.
    - Evasion / miss exclusion: no resolved hit -> rejected with 0 RNG draws.
    - Fatal damage exclusion: target defeated -> rejected with 0 RNG draws; cannot revive.
    - Simulator Determinism Policy: exactly one context.random.chance(probability) draw per admitted opportunity.
    - Dynamic Healing Ban: evaluated JIT by RecoverySystem.
    - End-to-end generation provenance: retains application generation ID through results.
    """

    def __init__(
        self,
        recovery_system: RecoverySystem,
        skill_runtime_registry: SkillRuntimeRegistry | None = None,
    ) -> None:
        if not isinstance(recovery_system, RecoverySystem):
            raise TypeError(f"recovery_system must be a RecoverySystem, got {type(recovery_system)}")
        self._recovery_system = recovery_system
        self._skill_runtimes = skill_runtime_registry

    def execute(
        self,
        context: BattleContext,
        opportunity: RecoveryOpportunity,
        aftermath_fact: DamageAftermathFact | None = None,
    ) -> RecoveryOpportunityResult:
        """Alias for evaluate_and_resolve."""
        return self.evaluate_and_resolve(context, opportunity, aftermath_fact=aftermath_fact)

    def evaluate_and_resolve(
        self,
        context: BattleContext,
        opportunity: RecoveryOpportunity,
        aftermath_fact: DamageAftermathFact | None = None,
    ) -> RecoveryOpportunityResult:
        if not isinstance(opportunity, RecoveryOpportunity):
            raise TypeError(f"opportunity must be a RecoveryOpportunity, got {type(opportunity)}")

        # S10-FG-H02 Hardening Invariant:
        # RECUPERATION_ACTION_START must operate with DamageAftermathFact = None and never query ReactionPermissionPolicy.
        # Passing an explicit dummy DamageAftermathFact to an action-start opportunity raises an invariant violation.
        if opportunity.opportunity_kind == RecoveryOpportunityKind.RECUPERATION_ACTION_START:
            if aftermath_fact is not None or getattr(opportunity, "aftermath_fact", None) is not None:
                raise ValueError(
                    "S10-FG-H02 invariant violation: DamageAftermathFact must be None for RECUPERATION_ACTION_START"
                )

        target_id = (
            opportunity.execution_descriptor.target_id
            or opportunity.execution_descriptor.intent_owner_id
        )
        if target_id not in context.units:
            return RecoveryOpportunityResult(
                opportunity=opportunity,
                resolution=None,
                executed=False,
                reason="INVALID_TARGET",
            )
        target = context.units[target_id]

        # Gate 1: Target Validity & Alive Gate (Shared)
        # Validate target unit exists and target.is_alive == True.
        # If dead or None: reject opportunity (TARGET_DEFEATED / INVALID_TARGET); NO RNG call.
        if not target.is_alive:
            return RecoveryOpportunityResult(
                opportunity=opportunity,
                resolution=None,
                executed=False,
                reason="TARGET_DEFEATED",
            )

        # Gate 2: Hit Topology & Reaction Permission Gate (Kind-Specific)
        if opportunity.opportunity_kind == RecoveryOpportunityKind.FIRST_AID_AFTER_DAMAGE:
            aftermath = aftermath_fact or getattr(opportunity, "aftermath_fact", None)
            if aftermath is None:
                return RecoveryOpportunityResult(
                    opportunity=opportunity,
                    resolution=None,
                    executed=False,
                    reason="INELIGIBLE_HIT_OR_SOURCE",
                )
            if aftermath.hit_topology != DamageHitTopology.RESOLVED_HIT:
                return RecoveryOpportunityResult(
                    opportunity=opportunity,
                    resolution=None,
                    executed=False,
                    reason="INELIGIBLE_HIT_OR_SOURCE",
                )
            if aftermath.target_defeated:
                return RecoveryOpportunityResult(
                    opportunity=opportunity,
                    resolution=None,
                    executed=False,
                    reason="TARGET_DEFEATED",
                )
            # ReactionPermissionPolicy is the sole authority for damage aftermath recovery eligibility
            if not ReactionPermissionPolicy.can_trigger_recovery(aftermath.source_type):
                return RecoveryOpportunityResult(
                    opportunity=opportunity,
                    resolution=None,
                    executed=False,
                    reason="INELIGIBLE_HIT_OR_SOURCE",
                )
        elif opportunity.opportunity_kind == RecoveryOpportunityKind.RECUPERATION_ACTION_START:
            # Gate 2 is NOT_APPLICABLE: skipped completely.
            # Never queries ReactionPermissionPolicy!
            aftermath = None
        else:
            raise ValueError(f"Unknown RecoveryOpportunityKind: {opportunity.opportunity_kind}")

        # Gate 3: Opportunity Lifecycle Window Gate (Shared)
        # Validate current combat round is within [first_eligible_round, last_eligible_round].
        window = getattr(opportunity, "lifecycle_window", None)
        if window is None and opportunity.execution_descriptor.state_instance_id:
            state_inst = context.states.get(opportunity.execution_descriptor.state_instance_id)
            if state_inst is not None:
                window = state_inst.lifecycle_window
        if window is not None:
            if not window.is_round_eligible(context.current_round):
                return RecoveryOpportunityResult(
                    opportunity=opportunity,
                    resolution=None,
                    executed=False,
                    reason="LIFECYCLE_WINDOW_EXPIRED",
                )

        # Gate 4: Source Skill Enablement Gate (Shared)
        # Query PersistentSourceSkillGate.
        # When mode == QUERY_SKILL_RUNTIME: query SkillRuntimeRegistry.
        # If disabled: suppress opportunity (SKILL_TEMPORARILY_DISABLED); NO RNG draw. Clock continues.
        gate = opportunity.source_skill_gate
        if gate.mode == PersistentSourceSkillGateMode.QUERY_SKILL_RUNTIME:
            registry = self._skill_runtimes or getattr(context, "skill_runtimes", None)
            source_ref = opportunity.execution_descriptor.source_ref
            if registry is not None and source_ref is not None:
                if source_ref.source_unit_id and source_ref.source_skill_slot:
                    skill_rt = registry.get(
                        source_ref.source_unit_id, source_ref.source_skill_slot
                    )
                    if skill_rt is not None and not skill_rt.enabled:
                        return RecoveryOpportunityResult(
                            opportunity=opportunity,
                            resolution=None,
                            executed=False,
                            reason="SKILL_TEMPORARILY_DISABLED",
                        )

        # Gate 5: Simulator RNG Probability Draw (Shared Engine Tail)
        # All pre-conditions satisfied -> Opportunity becomes ADMITTED.
        # Consume exactly one context.random.chance(probability) call.
        # recoverable_gap == 0 does NOT suppress this draw; full troops proceed to draw.
        prob = opportunity.probability
        if not (0.0 <= prob <= 1.0):
            raise ValueError(f"probability must be between 0.0 and 1.0, got {prob}")

        roll_success = context.random.chance(prob)
        if not roll_success:
            return RecoveryOpportunityResult(
                opportunity=opportunity,
                resolution=None,
                executed=False,
                reason="PROBABILITY_FAILED",
            )

        # Tail: Potency Calculation & RecoveryRequest (Shared Engine Tail)
        if opportunity.recovery_model_kind == RecoveryModelKind.TRIGGER_DAMAGE_RATIO:
            loss = aftermath.actual_target_troop_loss if aftermath is not None else 0
            ratio = (
                opportunity.recovery_potency_context.ratio
                if opportunity.recovery_potency_context
                else 0.0
            )
            nominal_amount = int(round(loss * ratio))
        else:  # TREATMENT_AMOUNT
            nominal_amount = 0
            if opportunity.recovery_potency_context is not None:
                potency = opportunity.recovery_potency_context
                if potency.treatment_amount > 0:
                    nominal_amount = potency.treatment_amount
                elif potency.base_rate > 0:
                    if potency.source_intellect is not None:
                        nominal_amount = int(
                            round(potency.base_rate * (100 + potency.source_intellect))
                        )
                    else:
                        nominal_amount = int(round(potency.base_rate))

        source_ref = opportunity.execution_descriptor.source_ref
        source_id = source_ref.source_unit_id if source_ref else None
        source_skill_id = source_ref.source_skill_id if source_ref else None
        state_inst_id = opportunity.execution_descriptor.state_instance_id
        source_state_id = None
        if state_inst_id and state_inst_id in context.states:
            state_inst = context.states.get(state_inst_id)
            source_state_id = state_inst.state_id

        if not (source_state_id and state_inst_id):
            source_state_id = None
            state_inst_id = None

        source_gen_id = opportunity.execution_descriptor.state_generation_id

        request = RecoveryRequest(
            source_id=source_id,
            target_id=target_id,
            amount=nominal_amount,
            source_skill_id=source_skill_id,
            source_state_id=source_state_id,
            source_state_instance_id=state_inst_id,
            source_generation_id=source_gen_id,
        )

        recovery_result = self._recovery_system.resolve(context, request)
        return RecoveryOpportunityResult(
            opportunity=opportunity,
            resolution=recovery_result,
            executed=True,
            reason=None,
        )

    def resolve_opportunity(
        self,
        context: BattleContext,
        opportunity: RecoveryOpportunity,
        aftermath_fact: DamageAftermathFact | None = None,
    ) -> RecoveryOpportunityResult:
        """Alias for evaluate_and_resolve."""
        return self.evaluate_and_resolve(context, opportunity, aftermath_fact)

    def __call__(
        self,
        context: BattleContext,
        opportunity: RecoveryOpportunity,
        aftermath_fact: DamageAftermathFact | None = None,
    ) -> RecoveryOpportunityResult:
        return self.evaluate_and_resolve(context, opportunity, aftermath_fact)

    @classmethod
    def make_first_aid_opportunity(
        cls,
        state_source: StateInstance | StateGenerationSnapshot,
        aftermath_fact: DamageAftermathFact,
    ) -> RecoveryOpportunity:
        """Construct a typed RecoveryOpportunity for FIRST_AID_AFTER_DAMAGE."""
        if not isinstance(aftermath_fact, DamageAftermathFact):
            raise TypeError(
                f"aftermath_fact must be a DamageAftermathFact, got {type(aftermath_fact)}"
            )

        params = state_source.runtime_params
        gen_id = (
            getattr(state_source, "current_generation_id", None)
            or getattr(state_source, "application_generation_id", None)
        )
        prob = getattr(params, "probability", 1.0)
        model_kind = getattr(
            params, "recovery_model_kind", RecoveryModelKind.TREATMENT_AMOUNT
        )
        potency = (
            getattr(params, "recovery_potency_context", None)
            or getattr(state_source, "recovery_potency_context", None)
        )
        gate = getattr(
            params, "source_skill_gate", PersistentSourceSkillGate.always_active()
        )
        window = (
            getattr(params, "lifecycle_window", None)
            or getattr(state_source, "lifecycle_window", None)
        )
        inst_id = getattr(state_source, "instance_id", None)

        source_unit_id = getattr(state_source, "source_id", None)
        source_skill_id = getattr(state_source, "source_skill_id", None)
        source_ref = (
            EffectSourceRef(
                stage9_source_type=SourceType.ACTIVE_SKILL,
                source_unit_id=source_unit_id,
                source_skill_id=source_skill_id,
                source_skill_slot=source_skill_slot,
            )
            if source_unit_id and source_skill_id
            else None
        )

        desc = RuleIntentExecutionDescriptor(
            intent_kind=RuleIntentKind.RECOVERY_OPPORTUNITY,
            intent_owner_id=aftermath_fact.target_id,
            state_owner_id=state_source.owner_id,
            target_id=aftermath_fact.target_id,
            source_ref=source_ref,
            state_instance_id=inst_id,
            state_generation_id=gen_id,
            execution_domain="STATE_RESOLUTION",
        )

        return RecoveryOpportunity(
            opportunity_kind=RecoveryOpportunityKind.FIRST_AID_AFTER_DAMAGE,
            execution_descriptor=desc,
            probability=prob,
            recovery_model_kind=model_kind,
            recovery_potency_context=potency,
            source_skill_gate=gate,
            lifecycle_window=window,
            aftermath_fact=aftermath_fact,
        )

    @classmethod
    def make_recuperation_opportunity(
        cls,
        state_source: StateInstance | StateGenerationSnapshot,
    ) -> RecoveryOpportunity:
        """Construct a typed RecoveryOpportunity for RECUPERATION_ACTION_START."""
        params = state_source.runtime_params
        gen_id = (
            getattr(state_source, "current_generation_id", None)
            or getattr(state_source, "application_generation_id", None)
        )
        prob = getattr(params, "probability", 1.0)
        model_kind = getattr(
            params, "recovery_model_kind", RecoveryModelKind.TREATMENT_AMOUNT
        )
        potency = (
            getattr(params, "recovery_potency_context", None)
            or getattr(state_source, "recovery_potency_context", None)
        )
        gate = getattr(
            params, "source_skill_gate", PersistentSourceSkillGate.always_active()
        )
        window = (
            getattr(params, "lifecycle_window", None)
            or getattr(state_source, "lifecycle_window", None)
        )
        inst_id = getattr(state_source, "instance_id", None)

        source_unit_id = getattr(state_source, "source_id", None)
        source_skill_id = getattr(state_source, "source_skill_id", None)
        source_skill_slot = getattr(state_source, "source_skill_slot", None)

        source_ref = (
            EffectSourceRef(
                stage9_source_type=SourceType.ACTIVE_SKILL,
                source_unit_id=source_unit_id,
                source_skill_id=source_skill_id,
                source_skill_slot=source_skill_slot,
            )
            if source_unit_id and source_skill_id
            else None
        )

        desc = RuleIntentExecutionDescriptor(
            intent_kind=RuleIntentKind.RECOVERY_OPPORTUNITY,
            intent_owner_id=state_source.owner_id,
            state_owner_id=state_source.owner_id,
            target_id=state_source.owner_id,
            source_ref=source_ref,
            state_instance_id=inst_id,
            state_generation_id=gen_id,
            execution_domain="STATE_RESOLUTION",
        )

        return RecoveryOpportunity(
            opportunity_kind=RecoveryOpportunityKind.RECUPERATION_ACTION_START,
            execution_descriptor=desc,
            probability=prob,
            recovery_model_kind=model_kind,
            recovery_potency_context=potency,
            source_skill_gate=gate,
            lifecycle_window=window,
            aftermath_fact=None,
        )
