from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, TYPE_CHECKING

from .operation_identity import ActionId, DamageInstanceId, FinalizationId, OperationIdAllocator

if TYPE_CHECKING:
    from .action_system import ActionSystem
    from .battle_finalization_coordinator import BattleFinalizationCoordinator
    from .context import BattleContext
    from .unit import UnitRuntime


def _forbid_ordering(cls_name: str, op: str) -> None:
    raise TypeError(
        f"{cls_name} does not support comparison operator '{op}'. "
        "Permit types cannot be used as gameplay ordering or priority comparators."
    )


class FutureBranchKind(str, Enum):
    """The exactly six global future branches in Stage9."""

    NEXT_ACTION = "NEXT_ACTION"
    ASSAULT = "ASSAULT"
    COMBO_SECOND_NORMAL_ATTACK = "COMBO_SECOND_NORMAL_ATTACK"
    COUNTER_BATCH = "COUNTER_BATCH"
    CHAIN_TRAVERSAL = "CHAIN_TRAVERSAL"
    CLEAVE_EFFECT = "CLEAVE_EFFECT"


class BattleTerminationState(str, Enum):
    """Semantic termination states owned exclusively by BattleFinalizationCoordinator."""

    RUNNING = "RUNNING"
    VICTORY_LATCHED = "VICTORY_LATCHED"
    DRAINING_ADMITTED_WORK = "DRAINING_ADMITTED_WORK"
    FINALIZED = "FINALIZED"


class LegacyFinalizationBarrier(str, Enum):
    """The six legacy macro checkpoints for compatibility observation."""

    INITIAL_SETTLED = "INITIAL_SETTLED"
    ROUND_START_HOOKS_SETTLED = "ROUND_START_HOOKS_SETTLED"
    UNIT_ACTION_START_HOOKS_SETTLED = "UNIT_ACTION_START_HOOKS_SETTLED"
    ACTION_SETTLED = "ACTION_SETTLED"
    ROUND_END_SETTLED = "ROUND_END_SETTLED"
    MAX_ROUND_SETTLED = "MAX_ROUND_SETTLED"


class PermitStatus(str, Enum):
    """Lifecycle status of a one-shot capability permit."""

    ISSUED = "ISSUED"
    CONSUMED = "CONSUMED"
    REVOKED = "REVOKED"


@dataclass(frozen=True, slots=True, order=False)
class FutureAdmissionPermit:
    """One-shot capability token required to allocate and admit a future branch."""

    permit_id: str
    branch_kind: FutureBranchKind
    parent_scope_identity: str
    termination_generation: int

    def __post_init__(self) -> None:
        if not isinstance(self.permit_id, str) or not self.permit_id.strip():
            raise ValueError("permit_id cannot be empty or whitespace")
        if not isinstance(self.branch_kind, FutureBranchKind):
            raise TypeError(f"branch_kind must be a FutureBranchKind, got {type(self.branch_kind)}")
        if not isinstance(self.parent_scope_identity, str) or not self.parent_scope_identity.strip():
            raise ValueError("parent_scope_identity cannot be empty or whitespace")
        if isinstance(self.termination_generation, bool) or not isinstance(self.termination_generation, int):
            raise TypeError("termination_generation must be an int")
        if self.termination_generation < 0:
            raise ValueError("termination_generation cannot be negative")

    def __lt__(self, other: Any) -> bool:
        _forbid_ordering("FutureAdmissionPermit", "<")

    def __le__(self, other: Any) -> bool:
        _forbid_ordering("FutureAdmissionPermit", "<=")

    def __gt__(self, other: Any) -> bool:
        _forbid_ordering("FutureAdmissionPermit", ">")

    def __ge__(self, other: Any) -> bool:
        _forbid_ordering("FutureAdmissionPermit", ">=")


@dataclass(frozen=True, slots=True, order=False)
class DamageSettlementPermit:
    """One-shot capability token required before destructive troop settlement of a DamageInstance."""

    permit_id: str
    damage_instance_id: DamageInstanceId

    def __post_init__(self) -> None:
        if not isinstance(self.permit_id, str) or not self.permit_id.strip():
            raise ValueError("permit_id cannot be empty or whitespace")
        if not isinstance(self.damage_instance_id, DamageInstanceId):
            raise TypeError(
                f"damage_instance_id must be DamageInstanceId, got {type(self.damage_instance_id)}"
            )

    def __lt__(self, other: Any) -> bool:
        _forbid_ordering("DamageSettlementPermit", "<")

    def __le__(self, other: Any) -> bool:
        _forbid_ordering("DamageSettlementPermit", "<=")

    def __gt__(self, other: Any) -> bool:
        _forbid_ordering("DamageSettlementPermit", ">")

    def __ge__(self, other: Any) -> bool:
        _forbid_ordering("DamageSettlementPermit", ">=")


@dataclass(frozen=True, slots=True, order=False)
class FinalizationProjectionPermit:
    """One-shot capability token required before legacy compatibility result/event projection."""

    permit_id: str
    finalization_id: FinalizationId

    def __post_init__(self) -> None:
        if not isinstance(self.permit_id, str) or not self.permit_id.strip():
            raise ValueError("permit_id cannot be empty or whitespace")
        if not isinstance(self.finalization_id, FinalizationId):
            raise TypeError(
                f"finalization_id must be FinalizationId, got {type(self.finalization_id)}"
            )

    def __lt__(self, other: Any) -> bool:
        _forbid_ordering("FinalizationProjectionPermit", "<")

    def __le__(self, other: Any) -> bool:
        _forbid_ordering("FinalizationProjectionPermit", "<=")

    def __gt__(self, other: Any) -> bool:
        _forbid_ordering("FinalizationProjectionPermit", ">")

    def __ge__(self, other: Any) -> bool:
        _forbid_ordering("FinalizationProjectionPermit", ">=")


class FutureAdmissionGate:
    """
    Single global future-admission authority in Stage9.
    Governs global future branches:
    NEXT_ACTION, ASSAULT, COMBO_SECOND_NORMAL_ATTACK, COUNTER_BATCH, CHAIN_TRAVERSAL, CLEAVE_EFFECT.
    Phase 9.2 production activates NEXT_ACTION; others maintain typed capability support.
    """

    def __init__(
        self,
        coordinator: BattleFinalizationCoordinator,
        id_allocator: OperationIdAllocator | None = None,
    ) -> None:
        from .battle_finalization_coordinator import BattleFinalizationCoordinator

        if not isinstance(coordinator, BattleFinalizationCoordinator):
            raise TypeError(
                f"coordinator must be BattleFinalizationCoordinator, got {type(coordinator)}"
            )
        self._coordinator = coordinator
        self._id_allocator = id_allocator or OperationIdAllocator()
        self._issued_permits: dict[str, FutureAdmissionPermit] = {}
        self._consumed_permits: set[str] = set()

    @property
    def coordinator(self) -> BattleFinalizationCoordinator:
        return self._coordinator

    def can_admit(self, branch_kind: FutureBranchKind) -> bool:
        if not isinstance(branch_kind, FutureBranchKind):
            raise TypeError(
                f"branch_kind must be FutureBranchKind, got {type(branch_kind)}"
            )
        return self._coordinator.termination_state == BattleTerminationState.RUNNING

    def request_admission(
        self,
        branch_kind: FutureBranchKind,
        parent_scope_identity: str,
        id_allocator: OperationIdAllocator | None = None,
    ) -> FutureAdmissionPermit | None:
        if not isinstance(branch_kind, FutureBranchKind):
            raise TypeError(
                f"branch_kind must be FutureBranchKind, got {type(branch_kind)}"
            )
        if not isinstance(parent_scope_identity, str) or not parent_scope_identity.strip():
            raise ValueError("parent_scope_identity cannot be empty or whitespace")

        if not self.can_admit(branch_kind):
            return None

        alloc = self._id_allocator
        if alloc is None:
            alloc = id_allocator or OperationIdAllocator()
            self._id_allocator = alloc

        permit_id = alloc.allocate_permit_id("prm_fwd")
        permit = FutureAdmissionPermit(
            permit_id=permit_id,
            branch_kind=branch_kind,
            parent_scope_identity=parent_scope_identity,
            termination_generation=self._coordinator.termination_generation,
        )
        self._issued_permits[permit.permit_id] = permit
        return permit

    def consume_permit(
        self,
        permit: FutureAdmissionPermit,
        expected_branch_kind: FutureBranchKind,
        expected_parent_scope_identity: str,
    ) -> None:
        if not isinstance(permit, FutureAdmissionPermit):
            raise TypeError(f"Expected FutureAdmissionPermit, got {type(permit)}")
        if not isinstance(expected_branch_kind, FutureBranchKind):
            raise TypeError(
                f"expected_branch_kind must be FutureBranchKind, got {type(expected_branch_kind)}"
            )
        if (
            not isinstance(expected_parent_scope_identity, str)
            or not expected_parent_scope_identity.strip()
        ):
            raise ValueError("expected_parent_scope_identity cannot be empty or whitespace")

        issued = self._issued_permits.get(permit.permit_id)
        if issued is None:
            raise ValueError(f"Permit {permit.permit_id} was not issued by this gate")
        if issued is not permit:
            raise ValueError(
                f"Permit capability authenticity failure: permit '{permit.permit_id}' "
                "is not the exact capability object issued by this gate"
            )
        if permit.permit_id in self._consumed_permits:
            raise RuntimeError(
                f"FutureAdmissionPermit {permit.permit_id} has already been consumed"
            )
        if permit.branch_kind != expected_branch_kind:
            raise ValueError(
                f"Branch kind mismatch: permit has {permit.branch_kind}, expected {expected_branch_kind}"
            )
        if permit.parent_scope_identity != expected_parent_scope_identity:
            raise ValueError(
                f"Parent scope identity mismatch: permit has {permit.parent_scope_identity}, "
                f"expected {expected_parent_scope_identity}"
            )
        if permit.termination_generation != self._coordinator.termination_generation:
            raise RuntimeError(
                f"Stale permit: termination generation changed from {permit.termination_generation} "
                f"to {self._coordinator.termination_generation}"
            )
        self._consumed_permits.add(permit.permit_id)


class LegacyActionDispatchAdapter:
    """
    Phase 9.2 compatibility bridge for NEXT_ACTION dispatch before Phase 9.6 real ActionScope.

    Responsibilities:
    - Receives gate-issued NEXT_ACTION FutureAdmissionPermit.
    - Validates branch kind and parent scope identity.
    - Consumes permit exactly once via gate.
    - Delegates to existing ActionSystem.execute.
    - Does NOT create ActionScope, does NOT allocate ActionId, does NOT do target selection,
      does NOT own NormalAttack lifecycle or finalization.
    """

    def __init__(
        self,
        action_system: Any,
        gate: FutureAdmissionGate,
    ) -> None:
        if not isinstance(gate, FutureAdmissionGate):
            raise TypeError(
                f"gate must be FutureAdmissionGate, got {type(gate)}"
            )
        self._action_system = action_system
        self._gate = gate

    @property
    def action_system(self) -> Any:
        if callable(self._action_system) and not hasattr(self._action_system, "execute"):
            return self._action_system()
        return self._action_system

    @property
    def gate(self) -> FutureAdmissionGate:
        return self._gate

    def dispatch(
        self,
        context: BattleContext,
        actor: UnitRuntime,
        permit: FutureAdmissionPermit,
        parent_scope_identity: str,
    ) -> None:
        if permit.branch_kind != FutureBranchKind.NEXT_ACTION:
            raise ValueError(
                f"LegacyActionDispatchAdapter only handles NEXT_ACTION, got {permit.branch_kind}"
            )
        self._gate.consume_permit(
            permit=permit,
            expected_branch_kind=FutureBranchKind.NEXT_ACTION,
            expected_parent_scope_identity=parent_scope_identity,
        )
        self.action_system.execute(context, actor)


class ComboGrantState(str, Enum):
    """Lifecycle state of an Action-local Combo grant."""

    VALID = "VALID"
    REVOKED_BY_PHYSICAL_REMOVE = "REVOKED_BY_PHYSICAL_REMOVE"
    CONSUMED = "CONSUMED"


@dataclass(slots=True)
class ComboActionGrant:
    """Action-local permission granted from a specific physical Combo StateInstance.

    Freezes source provenance at grant creation. Liveness check confirms physical
    instance still exists; physical removal before consume revokes the grant.
    Ordinary suppression does NOT retroactively revoke an already-valid grant.
    """

    action_id: ActionId
    granting_instance_id: str
    source_unit: str
    source_skill: str
    state: ComboGrantState = ComboGrantState.VALID

    def __post_init__(self) -> None:
        if not isinstance(self.action_id, ActionId):
            raise TypeError("action_id must be ActionId")
        if not isinstance(self.granting_instance_id, str) or not self.granting_instance_id.strip():
            raise ValueError("granting_instance_id cannot be empty or whitespace")
        if not isinstance(self.source_unit, str) or not self.source_unit.strip():
            raise ValueError("source_unit cannot be empty or whitespace")
        if not isinstance(self.source_skill, str) or not self.source_skill.strip():
            raise ValueError("source_skill cannot be empty or whitespace for a valid ComboActionGrant")
        if not isinstance(self.state, ComboGrantState):
            raise TypeError(f"state must be ComboGrantState, got {type(self.state)}")

    def is_valid(self, context: BattleContext) -> bool:
        if self.state != ComboGrantState.VALID:
            return False
        try:
            inst = context.states.get(self.granting_instance_id)
        except KeyError:
            inst = None
        if inst is None:
            self.state = ComboGrantState.REVOKED_BY_PHYSICAL_REMOVE
            return False
        return True

    def consume(self) -> None:
        if self.state != ComboGrantState.VALID:
            raise RuntimeError(f"Cannot consume ComboActionGrant in state {self.state.value}")
        self.state = ComboGrantState.CONSUMED

    def revoke_by_physical_remove(self) -> None:
        if self.state == ComboGrantState.VALID:
            self.state = ComboGrantState.REVOKED_BY_PHYSICAL_REMOVE


class ActionExecutionState(str, Enum):
    """Execution lifecycle state of an ActionScope."""

    ADMITTED = "ADMITTED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    TERMINAL = "TERMINAL"


class ComboCheckpointState(str, Enum):
    """State machine governing entry and consumption at the Combo Checkpoint boundary."""

    NOT_REACHED = "NOT_REACHED"
    REACHED = "REACHED"
    CONSUMED = "CONSUMED"
    BLOCKED = "BLOCKED"


@dataclass(slots=True)
class ActionScope:
    """Real Stage9 admitted Action unit of work.

    Maintains ActionId identity, actor, admitted status, combo grant,
    checkpoint state, physical normal attack count (<= 2), and terminal state.
    """

    action_id: ActionId
    actor_id: str
    admitted: bool = True
    combo_grant: ComboActionGrant | None = None
    combo_checkpoint_state: ComboCheckpointState = ComboCheckpointState.NOT_REACHED
    physical_normal_attack_count: int = 0
    terminal: bool = False
    execution_state: ActionExecutionState = ActionExecutionState.ADMITTED
    _coordinator: Any = None
    _owning_context_id: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.action_id, ActionId):
            raise TypeError("action_id must be ActionId")
        if not isinstance(self.actor_id, str) or not self.actor_id.strip():
            raise ValueError("actor_id cannot be empty or whitespace")
        if not isinstance(self.combo_checkpoint_state, ComboCheckpointState):
            raise TypeError(
                f"combo_checkpoint_state must be ComboCheckpointState, got {type(self.combo_checkpoint_state)}"
            )
        if not isinstance(self.execution_state, ActionExecutionState):
            raise TypeError(
                f"execution_state must be ActionExecutionState, got {type(self.execution_state)}"
            )

    def mark_terminal(self) -> None:
        self.terminal = True
        self.execution_state = ActionExecutionState.TERMINAL


def admit_action_scope(
    context: BattleContext,
    gate: FutureAdmissionGate,
    permit: FutureAdmissionPermit,
    actor: UnitRuntime,
    parent_scope_identity: str,
) -> ActionScope:
    """Factory admitting real ActionScope.

    Enforces strict architectural ordering:
    1. Pre-validates BattleContext against coordinator BEFORE permit consume or ActionId allocation.
    2. Validates exact issued capability and consumes NEXT_ACTION permit.
    3. ONLY AFTER successful consume: allocates ActionId from context.id_allocator.
    4. Constructs ActionScope with capability bindings.
    5. Registers exact scope object in coordinator barrier via private registration capability.
    6. Returns admitted ActionScope.
    """
    if not isinstance(gate, FutureAdmissionGate):
        raise TypeError("gate must be FutureAdmissionGate")
    if not isinstance(permit, FutureAdmissionPermit):
        raise TypeError("permit must be FutureAdmissionPermit")
    if permit.branch_kind != FutureBranchKind.NEXT_ACTION:
        raise ValueError(
            f"ActionScope admission requires NEXT_ACTION, got {permit.branch_kind.value}"
        )

    # Pre-validation BEFORE consuming permit or allocating ActionId:
    gate.coordinator._validate_context(context)

    # Step 1: Validate exact capability and consume permit FIRST
    gate.consume_permit(
        permit=permit,
        expected_branch_kind=FutureBranchKind.NEXT_ACTION,
        expected_parent_scope_identity=parent_scope_identity,
    )

    # Step 2: ONLY AFTER successful consume: allocate ActionId
    action_id = context.id_allocator.allocate_action_id()

    # Step 3: Construct ActionScope with capability bindings
    scope = ActionScope(
        action_id=action_id,
        actor_id=actor.unit_id,
        admitted=True,
        execution_state=ActionExecutionState.ADMITTED,
        _coordinator=gate.coordinator,
        _owning_context_id=id(context),
    )

    # Step 4: Register exact scope object in coordinator barrier via private registration
    gate.coordinator._register_admitted_action_scope(context, scope)

    return scope


class AssaultDispatchPort:
    """Stage9 typed admission seam for Assault skills.

    In Phase 9.6, this is seam-only: no gameplay logic, no trigger chances,
    no targeting, no damage formulas.
    Validates and consumes an authentic FutureAdmissionPermit(FutureBranchKind.ASSAULT).
    """

    def __init__(self, gate: FutureAdmissionGate) -> None:
        if not isinstance(gate, FutureAdmissionGate):
            raise TypeError(f"gate must be FutureAdmissionGate, got {type(gate)}")
        self._gate = gate

    @property
    def gate(self) -> FutureAdmissionGate:
        return self._gate

    def dispatch(
        self,
        context: BattleContext,
        permit: FutureAdmissionPermit,
        parent_scope_identity: str,
        *,
        actor: UnitRuntime,
        actual_target_id: str,
    ) -> None:
        if not isinstance(permit, FutureAdmissionPermit):
            raise TypeError("permit must be FutureAdmissionPermit")
        if permit.branch_kind != FutureBranchKind.ASSAULT:
            raise ValueError(f"Expected ASSAULT permit, got {permit.branch_kind.value}")
        # Pre-validate context BEFORE consuming permit!
        self._gate.coordinator._validate_context(context)
        self._gate.consume_permit(
            permit=permit,
            expected_branch_kind=FutureBranchKind.ASSAULT,
            expected_parent_scope_identity=parent_scope_identity,
        )
        # Seam-only in Phase 9.6: no default Assault producer registered.


