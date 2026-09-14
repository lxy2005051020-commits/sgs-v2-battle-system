from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, TYPE_CHECKING

from .enums import BattleEndReason
from .execution_right_system import (
    BattleTerminationState,
    FinalizationProjectionPermit,
    LegacyFinalizationBarrier,
    _forbid_ordering,
)
from .operation_identity import ActionId, DamageInstanceId, FinalizationId, OperationIdAllocator, CleaveEffectId, ChainTraversalId, ReactionBatchId
from .victory_system import VictorySystem

if TYPE_CHECKING:
    from .context import BattleContext, BattleResult


@dataclass(frozen=True, slots=True, order=False)
class FinalizationResult:
    """Frozen deep-immutable representation of battle finalization outcome."""

    finalization_id: FinalizationId
    winner_team_id: str | None
    reason: BattleEndReason
    rounds_completed: int
    final_troops_snapshot: tuple[tuple[str, int], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.finalization_id, FinalizationId):
            raise TypeError(
                f"finalization_id must be FinalizationId, got {type(self.finalization_id)}"
            )
        if self.winner_team_id is not None:
            if not isinstance(self.winner_team_id, str) or not self.winner_team_id.strip():
                raise ValueError("winner_team_id cannot be empty or whitespace when provided")
        if not isinstance(self.reason, BattleEndReason):
            raise TypeError(f"reason must be BattleEndReason, got {type(self.reason)}")
        if (
            isinstance(self.rounds_completed, bool)
            or not isinstance(self.rounds_completed, int)
            or self.rounds_completed < 0
        ):
            raise ValueError(
                f"rounds_completed must be non-negative int, got {self.rounds_completed}"
            )
        if not isinstance(self.final_troops_snapshot, tuple):
            raise TypeError(
                f"final_troops_snapshot must be a tuple, got {type(self.final_troops_snapshot)}"
            )
        for entry in self.final_troops_snapshot:
            if not isinstance(entry, tuple) or len(entry) != 2:
                raise TypeError(
                    f"Each entry in final_troops_snapshot must be a 2-tuple, got {entry}"
                )
            unit_id, troops = entry
            if not isinstance(unit_id, str) or not unit_id.strip():
                raise ValueError(f"unit_id must be non-empty str, got {unit_id}")
            if isinstance(troops, bool) or not isinstance(troops, int) or troops < 0:
                raise ValueError(f"troops must be non-negative int, got {troops}")

    def __lt__(self, other: Any) -> bool:
        _forbid_ordering("FinalizationResult", "<")

    def __le__(self, other: Any) -> bool:
        _forbid_ordering("FinalizationResult", "<=")

    def __gt__(self, other: Any) -> bool:
        _forbid_ordering("FinalizationResult", ">")

    def __ge__(self, other: Any) -> bool:
        _forbid_ordering("FinalizationResult", ">=")


@dataclass(frozen=True, slots=True, order=False)
class BattleTerminationRecord:
    """Small immutable record of semantic termination status."""

    state: BattleTerminationState
    termination_generation: int
    winner_team_id: str | None = None
    reason: BattleEndReason | None = None
    finalization_id: FinalizationId | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.state, BattleTerminationState):
            raise TypeError(f"state must be BattleTerminationState, got {type(self.state)}")
        if (
            isinstance(self.termination_generation, bool)
            or not isinstance(self.termination_generation, int)
            or self.termination_generation < 0
        ):
            raise ValueError("termination_generation must be non-negative int")
        if self.finalization_id is not None and not isinstance(
            self.finalization_id, FinalizationId
        ):
            raise TypeError(
                f"finalization_id must be FinalizationId or None, got {type(self.finalization_id)}"
            )
        if self.reason is not None and not isinstance(self.reason, BattleEndReason):
            raise TypeError(
                f"reason must be BattleEndReason or None, got {type(self.reason)}"
            )

    def __lt__(self, other: Any) -> bool:
        _forbid_ordering("BattleTerminationRecord", "<")

    def __le__(self, other: Any) -> bool:
        _forbid_ordering("BattleTerminationRecord", "<=")

    def __gt__(self, other: Any) -> bool:
        _forbid_ordering("BattleTerminationRecord", ">")

    def __ge__(self, other: Any) -> bool:
        _forbid_ordering("BattleTerminationRecord", ">=")


@dataclass(slots=True)
class ActionScopeAdmissionRecord:
    """Coordinator-owned authoritative admission record for an ActionScope."""

    action_id: ActionId
    actor_id: str
    scope_object: Any
    owning_context_id: int
    execution_state: Any  # ActionExecutionState
    primary_normal_attack_executed: bool = False


class ReactionOperationState(str, Enum):
    ADMITTED = "ADMITTED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"


@dataclass(slots=True)
class _ReactionAdmissionRecord:
    owning_context: Any
    operation_id: CleaveEffectId | ChainTraversalId | ReactionBatchId
    capability: Any
    state: ReactionOperationState = ReactionOperationState.ADMITTED


class BattleFinalizationCoordinator:
    """Unique semantic owner of battle termination and finalization.

    Phase 9.5 adds a real admitted DamageInstance barrier. Unit death may latch
    victory while that DamageInstance (including its local partition transaction)
    continues to drain; finalization occurs only after the admitted instance closes.
    """

    def __init__(
        self,
        victory_system: VictorySystem,
        id_allocator: OperationIdAllocator | None = None,
    ) -> None:
        if not isinstance(victory_system, VictorySystem):
            raise TypeError(
                f"victory_system must be VictorySystem, got {type(victory_system)}"
            )
        self._victory_system = victory_system
        self._id_allocator = id_allocator
        self._owning_context: BattleContext | None = None
        self._termination_state: BattleTerminationState = BattleTerminationState.RUNNING
        self._termination_generation: int = 0
        self._termination_record: BattleTerminationRecord | None = None
        self._finalization_result: FinalizationResult | None = None
        self._projection_permit: FinalizationProjectionPermit | None = None
        self._projection_claimed: bool = False
        self._projection_consumed: bool = False
        self._active_damage_instances: dict[DamageInstanceId, None] = {}
        self._reaction_records: dict[Any, _ReactionAdmissionRecord] = {}
        self._action_scope_records: dict[ActionId, ActionScopeAdmissionRecord] = {}
        self._latched_winner_team_id: str | None = None
        self._latched_reason: BattleEndReason | None = None

    @property
    def owning_context(self) -> BattleContext | None:
        return self._owning_context

    def _validate_context(self, context: BattleContext) -> None:
        from .context import BattleContext

        if not isinstance(context, BattleContext):
            raise TypeError(f"context must be BattleContext, got {type(context)}")
        if self._owning_context is not None and self._owning_context is not context:
            raise ValueError(
                f"BattleFinalizationCoordinator is already bound to BattleContext {id(self._owning_context)}, "
                f"cannot use with different BattleContext {id(context)}"
            )

    def _bind_or_validate_context(self, context: BattleContext) -> None:
        self._validate_context(context)
        if self._owning_context is None:
            self._owning_context = context

    @property
    def victory_system(self) -> VictorySystem:
        return self._victory_system

    @property
    def termination_state(self) -> BattleTerminationState:
        return self._termination_state

    @property
    def termination_generation(self) -> int:
        return self._termination_generation

    @property
    def termination_record(self) -> BattleTerminationRecord | None:
        return self._termination_record

    @property
    def finalization_result(self) -> FinalizationResult | None:
        return self._finalization_result

    @property
    def active_damage_instance_ids(self) -> tuple[DamageInstanceId, ...]:
        return tuple(self._active_damage_instances)

    @property
    def active_action_scope_ids(self) -> tuple[ActionId, ...]:
        from .execution_right_system import ActionExecutionState
        return tuple(
            aid for aid, rec in self._action_scope_records.items()
            if rec.execution_state in (ActionExecutionState.ADMITTED, ActionExecutionState.EXECUTING)
        )

    @property
    def has_admitted_work(self) -> bool:
        return bool(self._active_damage_instances or self.active_action_scope_ids or self._reaction_records)

    def _register_reaction(self, context, operation_id, capability) -> None:
        """Called only by permit-consuming mechanism factories, never by ID alone."""
        self._validate_context(context)
        if not isinstance(operation_id, (CleaveEffectId, ChainTraversalId, ReactionBatchId)):
            raise TypeError("Expected a typed reaction operation identity")
        if self.is_latched_or_finalized or operation_id in self._reaction_records:
            raise RuntimeError("Reaction cannot be newly admitted or replayed")
        self._bind_or_validate_context(context)
        self._reaction_records[operation_id] = _ReactionAdmissionRecord(context, operation_id, capability)

    def validate_reaction(self, context, operation_id, capability, *, executing=False):
        self._validate_context(context)
        record = self._reaction_records.get(operation_id)
        if record is None or record.capability is not capability or record.owning_context is not context:
            raise ValueError("Unknown, completed, forged, or foreign reaction capability")
        if executing and record.state is not ReactionOperationState.EXECUTING:
            raise RuntimeError("Reaction is not executing")
        return record.state

    def start_reaction(self, context, operation_id, capability) -> None:
        state = self.validate_reaction(context, operation_id, capability)
        if state is not ReactionOperationState.ADMITTED:
            raise RuntimeError("Reaction execution is one-shot")
        self._reaction_records[operation_id].state = ReactionOperationState.EXECUTING

    def complete_reaction(self, context, operation_id, capability) -> None:
        self.validate_reaction(context, operation_id, capability)
        record = self._reaction_records.pop(operation_id)
        record.state = ReactionOperationState.COMPLETED
        if self.is_latched_or_finalized and not self.has_admitted_work:
            self._finalize(context)

    def observe_reaction_death(self, context, operation_id, capability) -> None:
        self.validate_reaction(context, operation_id, capability, executing=True)
        if self.is_latched_or_finalized:
            return
        result = self._victory_system.check(context)
        if result is not None:
            self._latch_victory(result)
            self._termination_state = BattleTerminationState.DRAINING_ADMITTED_WORK
            self._refresh_latched_record()

    def admit_reaction_local_damage(self, context, damage_instance_id, operation_id, capability) -> None:
        """Existing admitted work may start a local damage microstep after latch."""
        self.validate_reaction(context, operation_id, capability, executing=True)
        if not isinstance(damage_instance_id, DamageInstanceId):
            raise TypeError("damage_instance_id must be DamageInstanceId")
        if damage_instance_id in self._active_damage_instances:
            raise ValueError("DamageInstance already admitted")
        self._active_damage_instances[damage_instance_id] = None

    @property
    def is_latched_or_finalized(self) -> bool:
        return self._termination_state in (
            BattleTerminationState.VICTORY_LATCHED,
            BattleTerminationState.DRAINING_ADMITTED_WORK,
            BattleTerminationState.FINALIZED,
        )

    def admit_damage_instance(
        self,
        context: BattleContext,
        damage_instance_id: DamageInstanceId,
    ) -> None:
        if not isinstance(damage_instance_id, DamageInstanceId):
            raise TypeError("damage_instance_id must be DamageInstanceId")
        self._validate_context(context)
        if self._termination_state != BattleTerminationState.RUNNING:
            raise RuntimeError(
                f"Cannot admit new DamageInstance while termination state is {self._termination_state.value}"
            )
        if damage_instance_id in self._active_damage_instances:
            raise ValueError(f"DamageInstance '{damage_instance_id}' is already admitted")
        self._bind_or_validate_context(context)
        self._active_damage_instances[damage_instance_id] = None

    def admit_action_scope(
        self,
        context: BattleContext,
        action_scope: Any,
    ) -> None:
        """Public direct admission bypass is strictly forbidden in Phase 9.6."""
        if isinstance(action_scope, ActionId):
            raise TypeError(
                "ActionId-only admission is forbidden in Phase 9.6; ActionScope capability is required"
            )
        raise RuntimeError(
            "Direct coordinator admission of ActionScope is forbidden; "
            "ActionScope must be admitted via admit_action_scope factory with authentic NEXT_ACTION permit"
        )

    def _register_admitted_action_scope(
        self,
        context: BattleContext,
        scope: Any,
    ) -> None:
        """Internal capability-bound registration called exclusively by admit_action_scope factory."""
        from .execution_right_system import ActionExecutionState, ActionScope

        if not isinstance(scope, ActionScope):
            raise TypeError(f"scope must be ActionScope, got {type(scope)}")
        self._validate_context(context)
        if self._termination_state != BattleTerminationState.RUNNING:
            raise RuntimeError(
                f"Cannot admit new ActionScope while termination state is {self._termination_state.value}"
            )
        if scope.action_id in self._action_scope_records:
            raise ValueError(f"ActionScope '{scope.action_id}' is already admitted")
        self._bind_or_validate_context(context)

        record = ActionScopeAdmissionRecord(
            action_id=scope.action_id,
            actor_id=scope.actor_id,
            scope_object=scope,
            owning_context_id=id(context),
            execution_state=ActionExecutionState.ADMITTED,
            primary_normal_attack_executed=False,
        )
        self._action_scope_records[scope.action_id] = record

    def complete_action_scope(
        self,
        context: BattleContext,
        scope: Any,
    ) -> None:
        from .execution_right_system import ActionExecutionState, ActionScope

        if isinstance(scope, ActionId):
            raise TypeError(
                "complete_action_scope requires exact ActionScope capability, not naked ActionId"
            )
        if not isinstance(scope, ActionScope):
            raise TypeError(f"scope must be ActionScope, got {type(scope)}")

        self._validate_context(context)
        if scope.action_id not in self._action_scope_records:
            raise ValueError(
                f"ActionScope '{scope.action_id}' is not active in finalization barrier"
            )
        record = self._action_scope_records[scope.action_id]
        if record.scope_object is not scope:
            raise ValueError(
                f"ActionScope object identity mismatch for action_id '{scope.action_id}'"
            )
        if record.owning_context_id != id(context):
            raise ValueError(
                f"ActionScope '{scope.action_id}' belongs to context {record.owning_context_id}, "
                f"not execution context {id(context)}"
            )
        if record.execution_state == ActionExecutionState.COMPLETED:
            raise RuntimeError(
                f"ActionScope '{scope.action_id}' has already been completed"
            )

        self._bind_or_validate_context(context)
        record.execution_state = ActionExecutionState.COMPLETED
        scope.execution_state = ActionExecutionState.COMPLETED
        scope.terminal = True

        if self._termination_state in (
            BattleTerminationState.VICTORY_LATCHED,
            BattleTerminationState.DRAINING_ADMITTED_WORK,
        ):
            if self.has_admitted_work:
                self._termination_state = BattleTerminationState.DRAINING_ADMITTED_WORK
                self._refresh_latched_record()
            else:
                self._finalize(context)

    def validate_action_scope(
        self,
        context: BattleContext,
        scope: Any,
        expected_actor_id: str | None = None,
    ) -> None:
        """Validate ActionScope authenticity, context binding, immutable actor ownership, and state."""
        from .execution_right_system import ActionExecutionState, ActionScope

        if not isinstance(scope, ActionScope):
            raise TypeError(f"scope must be ActionScope, got {type(scope)}")
        self._validate_context(context)
        if scope._coordinator is not self:
            raise RuntimeError(
                f"ActionScope '{scope.action_id}' was not admitted by this coordinator"
            )
        if scope.action_id not in self._action_scope_records:
            raise ValueError(
                f"ActionScope '{scope.action_id}' is not active in coordinator"
            )
        record = self._action_scope_records[scope.action_id]
        if record.owning_context_id != id(context):
            raise ValueError(
                f"ActionScope '{scope.action_id}' belongs to context {record.owning_context_id}, "
                f"not execution context {id(context)}"
            )
        if record.scope_object is not scope:
            raise ValueError(
                f"ActionScope object identity mismatch for action_id '{scope.action_id}'"
            )
        if expected_actor_id is not None and record.actor_id != expected_actor_id:
            raise ValueError(
                f"ActionScope actor mismatch: admission record actor is '{record.actor_id}', "
                f"expected executing actor '{expected_actor_id}'"
            )
        if (
            record.execution_state in (ActionExecutionState.COMPLETED, ActionExecutionState.TERMINAL)
            or scope.terminal
            or scope.execution_state == ActionExecutionState.TERMINAL
        ):
            state_str = (
                record.execution_state.value
                if record.execution_state in (ActionExecutionState.COMPLETED, ActionExecutionState.TERMINAL)
                else scope.execution_state.value
            )
            raise RuntimeError(
                f"ActionScope '{scope.action_id}' is already terminal ({state_str})"
            )
        if record.execution_state != ActionExecutionState.ADMITTED:
            raise RuntimeError(
                f"ActionScope '{scope.action_id}' has already been executed or is in state {record.execution_state.value}"
            )
        # Atomically transition coordinator authoritative record to EXECUTING
        record.execution_state = ActionExecutionState.EXECUTING
        scope.execution_state = ActionExecutionState.EXECUTING

    def validate_and_consume_primary_normal_attack(
        self,
        context: BattleContext,
        scope: Any,
        expected_actor_id: str | None = None,
    ) -> None:
        """Validate ActionScope lifecycle state is EXECUTING and enforce single primary NormalAttack entry."""
        from .execution_right_system import ActionExecutionState, ActionScope

        if not isinstance(scope, ActionScope):
            raise TypeError(f"scope must be ActionScope, got {type(scope)}")
        self._validate_context(context)
        if scope._coordinator is not self:
            raise RuntimeError(
                f"ActionScope '{scope.action_id}' was not admitted by this coordinator"
            )
        if scope.action_id not in self._action_scope_records:
            raise ValueError(
                f"ActionScope '{scope.action_id}' is not active in coordinator"
            )
        record = self._action_scope_records[scope.action_id]
        if record.owning_context_id != id(context):
            raise ValueError(
                f"ActionScope '{scope.action_id}' belongs to context {record.owning_context_id}, "
                f"not execution context {id(context)}"
            )
        if record.scope_object is not scope:
            raise ValueError(
                f"ActionScope object identity mismatch for action_id '{scope.action_id}'"
            )
        if expected_actor_id is not None and record.actor_id != expected_actor_id:
            raise ValueError(
                f"ActionScope actor mismatch: admission record actor is '{record.actor_id}', "
                f"expected executing actor '{expected_actor_id}'"
            )
        if record.execution_state == ActionExecutionState.ADMITTED:
            raise RuntimeError(
                f"ActionScope '{scope.action_id}' is merely ADMITTED; must be executed via ActionSystem lifecycle before calling NormalAttackSystem"
            )
        if record.execution_state in (ActionExecutionState.COMPLETED, ActionExecutionState.TERMINAL):
            raise RuntimeError(
                f"ActionScope '{scope.action_id}' is already {record.execution_state.value}"
            )
        if record.execution_state != ActionExecutionState.EXECUTING:
            raise RuntimeError(
                f"ActionScope '{scope.action_id}' is not in EXECUTING state (state: {record.execution_state.value})"
            )
        if record.primary_normal_attack_executed:
            raise RuntimeError(
                f"Primary NormalAttack entry for ActionScope '{scope.action_id}' has already been consumed"
            )
        record.primary_normal_attack_executed = True

    def observe_damage_instance_death(
        self,
        context: BattleContext,
        damage_instance_id: DamageInstanceId,
    ) -> None:
        if not isinstance(damage_instance_id, DamageInstanceId):
            raise TypeError("damage_instance_id must be DamageInstanceId")
        self._validate_context(context)
        if damage_instance_id not in self._active_damage_instances:
            raise ValueError(
                f"DamageInstance '{damage_instance_id}' is not active in finalization barrier"
            )
        self._bind_or_validate_context(context)
        if self._termination_state == BattleTerminationState.FINALIZED:
            return
        if self._termination_state in (
            BattleTerminationState.VICTORY_LATCHED,
            BattleTerminationState.DRAINING_ADMITTED_WORK,
        ):
            return
        eval_result = self._victory_system.check(context)
        if eval_result is None:
            return
        self._latch_victory(eval_result)
        if self.has_admitted_work:
            self._termination_state = BattleTerminationState.DRAINING_ADMITTED_WORK
            self._refresh_latched_record()
        else:
            self._finalize(context)

    def complete_damage_instance(
        self,
        context: BattleContext,
        damage_instance_id: DamageInstanceId,
    ) -> None:
        if not isinstance(damage_instance_id, DamageInstanceId):
            raise TypeError("damage_instance_id must be DamageInstanceId")
        self._validate_context(context)
        if damage_instance_id not in self._active_damage_instances:
            raise ValueError(
                f"DamageInstance '{damage_instance_id}' is not active in finalization barrier"
            )
        self._bind_or_validate_context(context)
        self._active_damage_instances.pop(damage_instance_id)
        if self._termination_state in (
            BattleTerminationState.VICTORY_LATCHED,
            BattleTerminationState.DRAINING_ADMITTED_WORK,
        ):
            if self.has_admitted_work:
                self._termination_state = BattleTerminationState.DRAINING_ADMITTED_WORK
                self._refresh_latched_record()
            else:
                self._finalize(context)

    def observe_legacy_barrier(
        self,
        context: BattleContext,
        barrier: LegacyFinalizationBarrier,
    ) -> None:
        if not isinstance(barrier, LegacyFinalizationBarrier):
            raise TypeError(
                f"barrier must be LegacyFinalizationBarrier, got {type(barrier)}"
            )
        self._validate_context(context)
        self._bind_or_validate_context(context)
        if self._termination_state == BattleTerminationState.FINALIZED:
            return

        if self._termination_state in (
            BattleTerminationState.VICTORY_LATCHED,
            BattleTerminationState.DRAINING_ADMITTED_WORK,
        ):
            if not self.has_admitted_work:
                self._finalize(context)
            return

        if barrier == LegacyFinalizationBarrier.MAX_ROUND_SETTLED:
            eval_result = self._victory_system.resolve_max_rounds(context)
        else:
            eval_result = self._victory_system.check(context)
        if eval_result is None:
            return

        self._latch_victory(eval_result)
        if self.has_admitted_work:
            self._termination_state = BattleTerminationState.DRAINING_ADMITTED_WORK
            self._refresh_latched_record()
            return
        self._finalize(context)

    def _latch_victory(self, eval_result: BattleResult) -> None:
        if self._termination_state != BattleTerminationState.RUNNING:
            return
        self._termination_state = BattleTerminationState.VICTORY_LATCHED
        self._termination_generation += 1
        self._latched_winner_team_id = eval_result.winner_team_id
        self._latched_reason = eval_result.reason
        self._refresh_latched_record()

    def _refresh_latched_record(self) -> None:
        self._termination_record = BattleTerminationRecord(
            state=self._termination_state,
            termination_generation=self._termination_generation,
            winner_team_id=self._latched_winner_team_id,
            reason=self._latched_reason,
            finalization_id=None,
        )

    def _finalize(self, context: BattleContext) -> None:
        self._bind_or_validate_context(context)
        if self._termination_state == BattleTerminationState.FINALIZED:
            return
        if self.has_admitted_work:
            raise RuntimeError("Cannot finalize while admitted work remains")
        if self._latched_reason is None:
            raise RuntimeError("Cannot finalize without a latched victory result")

        alloc = getattr(context, "id_allocator", None) or self._id_allocator
        if alloc is None:
            alloc = OperationIdAllocator()
            self._id_allocator = alloc

        finalization_id = alloc.allocate_finalization_id()
        permit_id = alloc.allocate_permit_id("prm_fin")
        sorted_units = sorted(context.units.values(), key=lambda u: u.unit_id)
        snapshot = tuple((u.unit_id, int(u.troops)) for u in sorted_units)

        self._termination_state = BattleTerminationState.FINALIZED
        self._finalization_result = FinalizationResult(
            finalization_id=finalization_id,
            winner_team_id=self._latched_winner_team_id,
            reason=self._latched_reason,
            rounds_completed=context.current_round,
            final_troops_snapshot=snapshot,
        )
        self._projection_permit = FinalizationProjectionPermit(
            permit_id=permit_id,
            finalization_id=finalization_id,
        )
        self._termination_record = BattleTerminationRecord(
            state=self._termination_state,
            termination_generation=self._termination_generation,
            winner_team_id=self._latched_winner_team_id,
            reason=self._latched_reason,
            finalization_id=finalization_id,
        )

    def claim_finalized_projection(
        self,
    ) -> tuple[FinalizationProjectionPermit, FinalizationResult] | None:
        if self._termination_state != BattleTerminationState.FINALIZED:
            return None
        if self._projection_claimed:
            return None
        if self._finalization_result is None or self._projection_permit is None:
            return None
        self._projection_claimed = True
        return (self._projection_permit, self._finalization_result)

    def consume_projection_permit(
        self,
        permit: FinalizationProjectionPermit,
    ) -> None:
        if not isinstance(permit, FinalizationProjectionPermit):
            raise TypeError(
                f"Expected FinalizationProjectionPermit, got {type(permit)}"
            )
        if self._projection_permit is None or self._finalization_result is None:
            raise RuntimeError(
                "No finalization projection permit was issued by this coordinator"
            )
        if permit.permit_id != self._projection_permit.permit_id:
            raise ValueError(
                f"Permit ID mismatch: permit {permit.permit_id} was not issued by this coordinator"
            )
        if permit.finalization_id != self._finalization_result.finalization_id:
            raise ValueError(
                f"FinalizationId mismatch: permit finalization_id {permit.finalization_id} "
                f"does not match {self._finalization_result.finalization_id}"
            )
        if permit is not self._projection_permit:
            raise ValueError(
                f"Permit capability authenticity failure: permit '{permit.permit_id}' "
                "is not the exact capability object issued by this coordinator"
            )
        if self._projection_consumed:
            raise RuntimeError(
                "FinalizationProjectionPermit has already been consumed"
            )
        self._projection_consumed = True
