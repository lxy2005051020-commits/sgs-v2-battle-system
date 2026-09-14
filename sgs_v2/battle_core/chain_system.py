from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from .enums import DamageType
from .execution_right_system import FutureBranchKind
from .operation_identity import DamageInstanceId, OperationLineage, ChainTraversalId, SourceType
from .reaction_permission_policy import ReactionPermissionPolicy
from .stage9_integerization import floor_product_int_ratio
from .events import EventType


@dataclass(frozen=True, slots=True)
class ResolvedDamageFact:
    damage_instance_id: DamageInstanceId
    target_id: str
    lineage: OperationLineage
    damage_type: DamageType
    assigned_target_damage: int
    actual_target_troop_loss: int

    def __post_init__(self):
        if not isinstance(self.target_id, str) or not self.target_id:
            raise ValueError("Resolved damage requires a target identity")
        if not isinstance(self.damage_instance_id, DamageInstanceId):
            raise TypeError("Expected DamageInstanceId")
        if not isinstance(self.lineage, OperationLineage) or not isinstance(self.damage_type, DamageType):
            raise TypeError("Expected typed lineage and damage type")
        for amount in (self.assigned_target_damage, self.actual_target_troop_loss):
            if type(amount) is not int or amount < 0:
                raise ValueError("Damage facts require nonnegative integer amounts")


class DamageCallbackTiming(str, Enum):
    INLINE = "INLINE"
    AFTER_CLEAVE = "AFTER_CLEAVE"


class DamageCallbackAdmissionPoint:
    """The sole CHAIN_TRAVERSAL global gate caller; no other reaction ownership."""

    def __init__(self, gate, chain, state_runtime):
        self._gate = gate
        self._chain = chain
        self._states = state_runtime

    def accept(self, context, fact, *, timing=DamageCallbackTiming.INLINE):
        if not isinstance(fact, ResolvedDamageFact) or not isinstance(timing, DamageCallbackTiming):
            raise TypeError("Expected resolved fact and typed timing")
        self._gate.coordinator._validate_context(context)
        if not ReactionPermissionPolicy.can_trigger_chain(fact.lineage.source_type):
            return None
        if self._states.get_operational_chain(context, fact.target_id) is None:
            return None
        parent = str(fact.damage_instance_id)
        permit = self._gate.request_admission(FutureBranchKind.CHAIN_TRAVERSAL, parent)
        if permit is None:
            return None
        work = self._chain.create_traversal(context, fact, permit=permit)
        if timing is DamageCallbackTiming.INLINE:
            self._chain.execute(context, work)
            return None
        return work


@dataclass(frozen=True, slots=True)
class ChainDeferredWork:
    parent_damage_instance_id: DamageInstanceId
    trigger_node_id: str
    trigger_damage: int
    trigger_provenance: OperationLineage


@dataclass(frozen=True, slots=True, init=False)
class ChainTraversal:
    traversal_id: ChainTraversalId
    work: ChainDeferredWork

    def __init__(self, *args, **kwargs):
        raise TypeError("Use ChainSystem.create_traversal with an authentic permit")


@dataclass(frozen=True, slots=True)
class ChainFeedbackResult:
    damage_instance_id: DamageInstanceId
    traversal_id: ChainTraversalId
    target_id: str
    lineage: OperationLineage
    calculated_damage: int
    actual_troop_loss: int
    credited_damage: int


class ChainSystem:
    """One admitted traversal, monotonic slot cursor, restricted feedback only."""

    def __init__(self, state_runtime, gate, troops):
        self._states = state_runtime
        self._gate = gate
        self._finalization = gate.coordinator
        self._troops = troops

    def cancel(self, context, traversal):
        self._finalization.complete_reaction(context, traversal.traversal_id, traversal)

    def create_traversal(self, context, fact, *, permit):
        self._finalization._validate_context(context)
        if not isinstance(fact, ResolvedDamageFact):
            raise TypeError("Expected ResolvedDamageFact")
        if not ReactionPermissionPolicy.can_trigger_chain(fact.lineage.source_type):
            raise ValueError("Source is forbidden from creating Chain")
        self._gate.consume_permit(permit, FutureBranchKind.CHAIN_TRAVERSAL, str(fact.damage_instance_id))
        traversal_id = context.id_allocator.allocate_chain_traversal_id()
        cap = object.__new__(ChainTraversal)
        object.__setattr__(cap, "traversal_id", traversal_id)
        object.__setattr__(cap, "work", ChainDeferredWork(fact.damage_instance_id,
            fact.target_id, fact.actual_target_troop_loss, fact.lineage))
        self._finalization._register_reaction(context, traversal_id, cap)
        return cap

    def execute(self, context, traversal):
        self._finalization.start_reaction(context, traversal.traversal_id, traversal)
        results = []
        work = traversal.work
        try:
            trigger = context.units.get(work.trigger_node_id)
            if trigger is None:
                return ()
            # Immutable battle-slot roster, not a snapshot of linked/alive candidates.
            slots = tuple(unit.unit_id for unit in sorted(context.units.values(),
                key=lambda unit: unit.lineup_position) if unit.team_id == trigger.team_id)
            for cursor, unit_id in enumerate(slots):
                current = self._states.get_operational_chain(context, work.trigger_node_id)
                if current is None:
                    break  # local trigger liveness/state, never global re-admission
                context.event_bus.publish(event_type=EventType.CHAIN_SLOT_VISITED,
                    phase=context.current_phase, round_no=context.current_round,
                    target_id=unit_id, payload={"traversal_id": str(traversal.traversal_id), "cursor": cursor})
                if unit_id == work.trigger_node_id:
                    continue
                candidate = context.units.get(unit_id)
                if candidate is None or candidate.team_id != trigger.team_id:
                    continue
                if self._states.get_operational_chain(context, unit_id) is None:
                    continue
                lineage = replace(work.trigger_provenance,
                    parent_damage_instance_id=work.parent_damage_instance_id,
                    source_type=SourceType.CHAIN_TRUE_FEEDBACK,
                    physical_attacker=current.source_id, physical_skill=current.source_skill_id,
                    credit_owner=current.source_id)
                amount = floor_product_int_ratio(work.trigger_damage, current.runtime_params.ratio)
                results.append(self._settle_feedback(context, traversal, unit_id, amount, lineage))
            return tuple(results)
        finally:
            self._finalization.complete_reaction(context, traversal.traversal_id, traversal)

    def _settle_feedback(self, context, traversal, target_id, amount, lineage):
        self._finalization.validate_reaction(context, traversal.traversal_id, traversal, executing=True)
        target = context.get_unit(target_id)
        damage_id = context.id_allocator.allocate_damage_instance_id()
        before = target.troops
        self._troops.apply_damage(target, amount)
        actual = before - target.troops
        result = ChainFeedbackResult(damage_id, traversal.traversal_id, target_id, lineage, amount, actual, actual)
        context.event_bus.publish(event_type=EventType.CHAIN_FEEDBACK,
            phase=context.current_phase, round_no=context.current_round,
            actor_id=lineage.physical_attacker, target_id=target_id,
            payload={"source_type": SourceType.CHAIN_TRUE_FEEDBACK.value,
                "damage_instance_id": str(damage_id), "traversal_id": str(traversal.traversal_id),
                "parent_damage_instance_id": str(traversal.work.parent_damage_instance_id),
                "source_skill_id": lineage.physical_skill, "credit_owner": lineage.credit_owner,
                "calculated_damage": amount, "actual_loss": actual, "credited_damage": actual})
        if before > 0 and not target.is_alive:
            context.event_bus.publish(event_type=EventType.UNIT_DEFEATED,
                phase=context.current_phase, round_no=context.current_round,
                actor_id=lineage.physical_attacker, target_id=target_id,
                payload={"target_name": target.name, "source_type": SourceType.CHAIN_TRUE_FEEDBACK.value})
            self._finalization.observe_reaction_death(context, traversal.traversal_id, traversal)
        return result
