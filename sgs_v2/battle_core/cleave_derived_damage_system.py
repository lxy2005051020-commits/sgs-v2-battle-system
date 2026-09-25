from __future__ import annotations

from dataclasses import dataclass, replace

from .chain_system import ResolvedDamageFact
from .damage_partition_system import DamageShareTransactionPlan, DistributionTransactionPlan
from .damage_rule_provider import DamageRuleCollection
from .damage_rule_models import HitPreventionCategory, HitRuleKind
from .direct_troop_loss_system import DirectTroopLossRequest
from .enums import DamageType
from .events import EventType
from .hit_resolution_system import HitPreventedResult, HitAllowedResult
from .operation_identity import CleaveEffectId, DamageInstanceId, OperationLineage, SourceType
from .damage_aftermath_port import (
    DamageHitTopology,
    DamageZeroLossCause,
    create_damage_aftermath_fact,
)
from .reaction_permission_policy import ReactionPermissionPolicy
from .stage9_integerization import ExactRatio, floor_product_int_ratio



@dataclass(frozen=True, slots=True)
class CleaveDerivedDamageRequest:
    damage_instance_id: DamageInstanceId
    cleave_effect_id: CleaveEffectId
    lineage: OperationLineage
    damage_type: DamageType
    base_amount: int
    ratio: ExactRatio
    secondary_target: str
    base_fact: str = "ACTUAL_TARGET_TROOP_LOSS"

    def __post_init__(self):
        if not isinstance(self.damage_instance_id, DamageInstanceId) or not isinstance(self.cleave_effect_id, CleaveEffectId):
            raise TypeError("Cleave requires typed operation identities")
        if not isinstance(self.lineage, OperationLineage) or self.lineage.source_type is not SourceType.CLEAVE:
            raise ValueError("Cleave requires CLEAVE lineage")
        if not isinstance(self.damage_type, DamageType) or not isinstance(self.ratio, ExactRatio):
            raise TypeError("Cleave requires typed damage type and ExactRatio")
        if type(self.base_amount) is not int or self.base_amount < 0 or self.ratio.numerator < 0:
            raise ValueError("Cleave base and ratio must be nonnegative")
        if self.base_fact != "ACTUAL_TARGET_TROOP_LOSS":
            raise ValueError("Cleave base fact is frozen")

    @property
    def source_type(self):
        return SourceType.CLEAVE

    @property
    def source_id(self):
        return self.lineage.physical_attacker

    @property
    def target_id(self):
        return self.secondary_target


@dataclass(frozen=True, slots=True)
class CleaveRecoveryFact:
    """Separate attacker recovery input; never reused as a FirstAid basis.

    Distribution's external participant attribution is deliberately delegated to
    the 690094/690095 owner. None means that Cleave has made no basis decision.
    """
    primary_damage: ResolvedDamageFact
    partition_kind: object
    attacker_recovery_basis: int | None
    external_participant_authority: str | None


@dataclass(frozen=True, slots=True)
class CleaveDerivedDamageResult:
    request: CleaveDerivedDamageRequest
    calculated_damage: int
    assigned_target_damage: int
    actual_target_troop_loss: int
    target_troops_before: int
    target_troops_after: int
    prevented: bool
    partition_plan: object | None
    direct_losses: tuple
    recovery: CleaveRecoveryFact | None


class CleaveDerivedDamageResolver:
    """Derived hit, shared partition math, exact troop commit, and typed callbacks.

    No standard DamageRequest/Result is synthesized. Hit and recovery effect
    adapters retain their own evidence-gated semantics; no new official state
    binding or recovery formula is invented by this owner.
    """

    def __init__(self, *, troops, partition, direct_loss, finalization, hit_resolution,
                 hit_rules, damage_callbacks, first_aid=None, attacker_recovery=None,
                 consume_hit_prevention=None, damage_aftermath_port=None, defeat_cleanup_port=None,
                 stage11_state_runtime=None):
        self._troops = troops
        self._partition = partition
        self._direct_loss = direct_loss
        self._finalization = finalization
        self._hit = hit_resolution
        self._hit_rules = hit_rules
        self._callbacks = damage_callbacks
        self._first_aid = first_aid
        self._attacker_recovery = attacker_recovery
        self._consume_hit_prevention = consume_hit_prevention
        self._damage_aftermath_port = damage_aftermath_port
        self._defeat_cleanup = defeat_cleanup_port
        self._stage11 = stage11_state_runtime
        self._requests = {}


    def _issue_request(self, context, effect, target_id):
        self._finalization.validate_reaction(context, effect.effect_id, effect, executing=True)
        request = CleaveDerivedDamageRequest(
            context.id_allocator.allocate_damage_instance_id(), effect.effect_id,
            effect.lineage, effect.damage_type, effect.base_amount, effect.ratio, target_id,
        )
        self._requests[request.damage_instance_id] = (context, effect, request)
        return request

    def resolve(self, context, effect, request):
        self._finalization.validate_reaction(context, effect.effect_id, effect, executing=True)
        if not isinstance(request, CleaveDerivedDamageRequest):
            raise TypeError("Expected CleaveDerivedDamageRequest")
        record = self._requests.get(request.damage_instance_id)
        if record is None or record[0] is not context or record[1] is not effect or record[2] is not request:
            raise ValueError("Unknown, forged, foreign, or consumed derived settlement capability")
        del self._requests[request.damage_instance_id]  # consume before any mutation
        self._finalization.admit_reaction_local_damage(context, request.damage_instance_id, effect.effect_id, effect)
        try:
            return self._resolve(context, effect, request)
        finally:
            self._finalization.complete_damage_instance(context, request.damage_instance_id)

    def _resolve(self, context, effect, request):
        amount = floor_product_int_ratio(request.base_amount, request.ratio)
        target = context.get_unit(request.secondary_target)
        before = target.troops
        # Only HIT contributions enter the existing hit resolver; no prevention,
        # base formula, modifier or Crit stage is called on this route.
        rules = self._hit_rules.collect(context, request)
        hit = HitAllowedResult(())
        for category, allowed in (
            (HitPreventionCategory.EVASION_LIKE, ReactionPermissionPolicy.can_trigger_evasion(request.source_type)),
            (HitPreventionCategory.IMMUNITY_LIKE, ReactionPermissionPolicy.can_trigger_resistance(request.source_type)),
        ):
            if not allowed:
                continue
            hit = self._hit.resolve(context, request, DamageRuleCollection(hit_contributions=tuple(
                item for item in rules.hit_contributions
                if item.category is category or item.kind is HitRuleKind.BYPASS)))
            if isinstance(hit, HitPreventedResult):
                break
        if isinstance(hit, HitPreventedResult):
            if self._consume_hit_prevention is not None:
                self._consume_hit_prevention(context, request, hit)
            self._event(context, EventType.DAMAGE_PREVENTED, request, {"requested_damage": amount})
            return CleaveDerivedDamageResult(request, amount, 0, 0, before, before, True, None, (), None)

        if self._stage11 is not None and request.source_id is not None:
            stage11_hit = self._stage11.resolve_hit(
                context,
                source_id=request.source_id,
                target_id=request.target_id,
            )
            if stage11_hit.prevented:
                self._event(
                    context,
                    EventType.DAMAGE_PREVENTED,
                    request,
                    {
                        "requested_damage": amount,
                        "reason_state_id": stage11_hit.prevented_by_state_id,
                    },
                )
                return CleaveDerivedDamageResult(
                    request, amount, 0, 0, before, before, True, None, (), None
                )

        weakness_zero = bool(
            self._stage11 is not None
            and request.source_id is not None
            and self._stage11.weakness_active(context, request.source_id)
        )
        if weakness_zero:
            amount = 0

        if not ReactionPermissionPolicy.can_enter_partition(request.source_type):
            raise ValueError("Cleave partition permission required")
        plan = self._partition.plan_derived(context, request.damage_instance_id, target.unit_id, amount)
        losses = []

        def direct(victim_id, value, source_type):
            lineage = replace(request.lineage, source_type=source_type, parent_damage_instance_id=request.damage_instance_id)
            loss = self._direct_loss.resolve(context, DirectTroopLossRequest(
                partition_transaction_id=plan.partition_transaction_id,
                parent_damage_instance_id=request.damage_instance_id,
                source_type=source_type, physical_attacker=lineage.physical_attacker,
                physical_skill=lineage.physical_skill, victim=victim_id,
                credit_owner=lineage.credit_owner, theoretical_loss=value, lineage=lineage,
            ))
            losses.append(loss.loss)
            if loss.death_edge:
                self._finalization.observe_damage_instance_death(context, request.damage_instance_id)

        if isinstance(plan, DistributionTransactionPlan):
            for participant in plan.participant_ids:
                if self._partition.participant_is_jit_valid(context, plan, participant):
                    direct(participant, plan.dparticipant, SourceType.DISTRIBUTION_DIRECT_LOSS)
        assigned = plan.dtarget if isinstance(plan, (DamageShareTransactionPlan, DistributionTransactionPlan)) else plan.dtotal
        before = target.troops
        was_alive = target.is_alive
        self._troops.apply_damage(target, assigned)
        actual = before - target.troops
        self._event(context, EventType.DAMAGE_DEALT, request, {
            "requested_damage": assigned, "damage": actual, "calculated_damage": amount,
            "target_remaining_troops": target.troops,
        })
        death = was_alive and not target.is_alive
        if death:
            self._event(context, EventType.UNIT_DEFEATED, request, {"target_name": target.name})
            defeat_cleanup = (
                self._defeat_cleanup
                or getattr(getattr(context, "systems", None), "defeat_cleanup_port", None)
            )
            if defeat_cleanup is not None:
                defeat_cleanup.commit_defeat(context, target.unit_id, defeat_source_ref=request.source_id)
            self._finalization.observe_damage_instance_death(context, request.damage_instance_id)

        if isinstance(plan, DamageShareTransactionPlan) and not death:
            sharer = context.units.get(plan.sharer_id)
            if sharer is not None and sharer.is_alive:
                direct(plan.sharer_id, plan.dsharer_theoretical, SourceType.SHARE_DIRECT_LOSS)

        fact = ResolvedDamageFact(request.damage_instance_id, target.unit_id, request.lineage,
                                  request.damage_type, assigned, actual)
        share_actual = (
            sum(int(item.actual_loss) for item in losses)
            if isinstance(plan, DamageShareTransactionPlan)
            else 0
        )
        recovery_basis = actual + share_actual
        recovery = CleaveRecoveryFact(
            fact,
            plan.kind,
            recovery_basis,
            "PROJECT_RUNTIME_DEFAULT: distribution external loss excluded"
            if isinstance(plan, DistributionTransactionPlan)
            else None,
        )
        aftermath_port = (
            self._damage_aftermath_port
            or getattr(getattr(context, "systems", None), "damage_aftermath_port", None)
        )
        if aftermath_port is not None:
            aftermath_fact = create_damage_aftermath_fact(
                damage_instance_id=request.damage_instance_id,
                target_id=target.unit_id,
                source_type=request.source_type,
                damage_type=request.damage_type,
                assigned_target_damage=assigned,
                actual_target_troop_loss=actual,
                target_troops_after=target.troops,
                target_defeated=death,
                hit_topology=DamageHitTopology.RESOLVED_HIT,
                zero_loss_cause=(
                    DamageZeroLossCause.WEAKNESS_ZERO
                    if weakness_zero
                    else (DamageZeroLossCause.SETTLED_ZERO if actual == 0 else None)
                ),
            )
            aftermath_port.commit_aftermath(context, aftermath_fact)
        if ReactionPermissionPolicy.can_trigger_recovery(request.source_type):
            if self._first_aid is not None:
                self._first_aid(context, fact)  # its own contract; not attacker recovery basis
            if self._attacker_recovery is not None:
                self._attacker_recovery(context, recovery)
        self._callbacks.accept(context, fact)
        return CleaveDerivedDamageResult(request, amount, assigned, actual, before,
            before - actual, False, plan, tuple(losses), recovery)


    @staticmethod
    def _event(context, event, request, payload):
        context.event_bus.publish(event_type=event, phase=context.current_phase,
            round_no=context.current_round, actor_id=request.source_id, target_id=request.target_id,
            payload={**payload, "source_type": SourceType.CLEAVE.value,
                "damage_type": request.damage_type.value, "normal_attack_identity": False,
                "damage_instance_id": str(request.damage_instance_id),
                "cleave_effect_id": str(request.cleave_effect_id),
                "source_skill_id": request.lineage.physical_skill,
                "credit_owner": request.lineage.credit_owner})
