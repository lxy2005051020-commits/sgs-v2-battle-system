from __future__ import annotations

from dataclasses import dataclass, replace

from .damage_system import DamageRequest
from .enums import DamageSourceType, DamageType
from .events import EventType
from .execution_right_system import FutureBranchKind
from .operation_identity import CounterBatchEntryId, ReactionBatchId, OperationLineage, SourceType
from .reaction_permission_policy import ReactionPermissionPolicy
from .stage9_integerization import ExactRatio
from .skill_runtime import SkillSlot


@dataclass(frozen=True, slots=True)
class CounterBatchEntry:
    entry_id: CounterBatchEntryId
    reaction_batch_id: ReactionBatchId
    counter_instance_id: str
    owner_id: str
    source_id: str | None
    source_skill_id: str | None
    source_skill_slot: SkillSlot | None
    damage_rate: ExactRatio
    batch_order: int


@dataclass(frozen=True, slots=True, init=False)
class CounterBatch:
    batch_id: ReactionBatchId
    entries: tuple[CounterBatchEntry, ...]
    target_id: str
    parent_lineage: OperationLineage

    def __init__(self, *args, **kwargs):
        raise TypeError("Use CounterSystem.create_batch with an authentic permit")


@dataclass(frozen=True, slots=True)
class CounterEntryResult:
    entry: CounterBatchEntry
    executed: bool
    dead_target_terminal: bool
    actual_troop_loss: int
    damage_execution: object | None


class CounterSystem:
    def __init__(self, state_runtime, gate, damage_instances):
        self._states = state_runtime
        self._gate = gate
        self._finalization = gate.coordinator
        self._damage = damage_instances

    def create_batch(self, context, main, *, permit):
        self._finalization._validate_context(context)
        if not ReactionPermissionPolicy.can_trigger_counter(main.lineage.source_type):
            raise ValueError("Counter requires physical NormalAttack identity")
        self._gate.consume_permit(permit, FutureBranchKind.COUNTER_BATCH, str(main.lineage.parent_normal_attack_id))
        batch_id = context.id_allocator.allocate_reaction_batch_id()
        states = self._states.get_counter_effects(context, main.target_id)
        entries = tuple(CounterBatchEntry(context.id_allocator.allocate_counter_batch_entry_id(),
            batch_id, state.instance_id, state.owner_id, state.source_id, state.source_skill_id,
            state.source_skill_slot, state.runtime_params.damage_rate, order)
            for order, state in enumerate(states))
        cap = object.__new__(CounterBatch)
        for key, value in dict(batch_id=batch_id, entries=entries,
                target_id=main.lineage.physical_attacker, parent_lineage=replace(main.lineage, parent_damage_instance_id=main.damage_instance_id)).items():
            object.__setattr__(cap, key, value)
        self._finalization._register_reaction(context, batch_id, cap)
        return cap

    def execute(self, context, batch):
        self._finalization.start_reaction(context, batch.batch_id, batch)
        results = []
        try:
            for entry in batch.entries:
                owner = context.units.get(entry.owner_id)
                if owner is None or not owner.is_alive:
                    results.append(CounterEntryResult(entry, False, False, 0, None))
                    continue
                context.event_bus.publish(event_type=EventType.COUNTER_EXECUTE,
                    phase=context.current_phase, round_no=context.current_round,
                    actor_id=entry.owner_id, target_id=batch.target_id,
                    payload={"batch_id": str(batch.batch_id), "entry_id": str(entry.entry_id),
                        "source_skill_id": entry.source_skill_id, "source_type": SourceType.COUNTER.value})
                target = context.get_unit(batch.target_id)
                if not target.is_alive:
                    context.event_bus.publish(event_type=EventType.COUNTER_ZERO_LOSS,
                        phase=context.current_phase, round_no=context.current_round,
                        actor_id=entry.owner_id, target_id=target.unit_id,
                        payload={"entry_id": str(entry.entry_id), "actual_loss": 0,
                            "credit_owner": entry.owner_id, "source_skill_id": entry.source_skill_id,
                            "source_type": SourceType.COUNTER.value})
                    results.append(CounterEntryResult(entry, True, True, 0, None))
                    continue
                parent = batch.parent_lineage
                lineage = OperationLineage(parent.root_action_id, parent.parent_normal_attack_id,
                    parent.parent_damage_instance_id, SourceType.COUNTER, entry.owner_id,
                    entry.source_skill_id, entry.owner_id)
                request = DamageRequest(source_id=entry.owner_id, target_id=target.unit_id,
                    damage_type=DamageType.WEAPON, source_type=DamageSourceType.COUNTER,
                    coefficient=entry.damage_rate.numerator / entry.damage_rate.denominator,
                    source_skill_id=entry.source_skill_id,
                    source_state_id="counterattack", source_state_instance_id=entry.counter_instance_id)
                execution = self._damage.execute_partitioned_damage_instance(context, request, lineage,
                    admitted_reaction=(batch.batch_id, batch))
                results.append(CounterEntryResult(entry, True, False,
                    execution.resolution.actual_target_troop_loss, execution))
            return tuple(results)
        finally:
            self._finalization.complete_reaction(context, batch.batch_id, batch)
