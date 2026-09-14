from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .context import BattleContext
from .damage_resolution_system import (
    DamageResolutionResult,
    DamageResolutionSystem,
    DamageSettlementRequest,
    SettlementOrigin,
)
from .damage_system import DamageRequest, DamageResult, DamageSystem
from .execution_right_system import DamageSettlementPermit
from .operation_identity import (
    DamageInstanceId,
    OperationIdAllocator,
    OperationLineage,
    _forbid_ordering,
)


@dataclass(slots=True)
class _PermitRecord:
    permit: DamageSettlementPermit
    lineage: OperationLineage
    consumed: bool = False


class DamageInstanceCoordinator:
    """
    Stage9 Standard DamageInstance Orchestration Owner.

    Responsibilities:
    - Allocate DamageInstanceId
    - Own DamageInstance-local permit registry/state
    - Issue at most one DamageSettlementPermit per DamageInstanceId
    - Validate issuer ownership and unconsumed state
    - Preserve OperationLineage
    - Call DamageSystem.calculate to freeze Dtotal
    - Form typed DamageSettlementRequest
    - Call DamageResolutionSystem.settle
    - Complete/release local settlement capability state

    Non-responsibilities (deferred to Phase 9.5+):
    - Partition semantics (Share / Distribution)
    - DirectTroopLoss
    - Cleave / Chain / Counter
    - NormalAttack master
    - EffectExecutor production routing
    """

    def __init__(
        self,
        damage_system: DamageSystem,
        damage_resolution_system: DamageResolutionSystem,
        *,
        id_allocator: OperationIdAllocator | None = None,
    ) -> None:
        if not isinstance(damage_system, DamageSystem):
            raise TypeError(
                f"damage_system must be DamageSystem, got {type(damage_system)}"
            )
        if not isinstance(damage_resolution_system, DamageResolutionSystem):
            raise TypeError(
                f"damage_resolution_system must be DamageResolutionSystem, got {type(damage_resolution_system)}"
            )
        self._damage_system = damage_system
        self._damage_resolution = damage_resolution_system
        self._id_allocator = id_allocator

        # Operation-local permit tracking
        self._permits: dict[str, _PermitRecord] = {}
        self._instance_to_permit_id: dict[DamageInstanceId, str] = {}
        self._completed_instances: set[DamageInstanceId] = set()

        # Bind this coordinator to the resolution system
        self._damage_resolution.bind_coordinator(self)

    @property
    def damage_system(self) -> DamageSystem:
        return self._damage_system

    @property
    def damage_resolution_system(self) -> DamageResolutionSystem:
        return self._damage_resolution

    def _get_allocator(self, context: BattleContext | None = None) -> OperationIdAllocator:
        if (
            context is not None
            and hasattr(context, "id_allocator")
            and context.id_allocator is not None
        ):
            return context.id_allocator
        if self._id_allocator is not None:
            return self._id_allocator
        self._id_allocator = OperationIdAllocator()
        return self._id_allocator

    def allocate_damage_instance_id(
        self,
        context: BattleContext | None = None,
    ) -> DamageInstanceId:
        allocator = self._get_allocator(context)
        return allocator.allocate_damage_instance_id()

    def issue_settlement_permit(
        self,
        damage_instance_id: DamageInstanceId,
        lineage: OperationLineage,
        context: BattleContext | None = None,
    ) -> DamageSettlementPermit:
        if not isinstance(damage_instance_id, DamageInstanceId):
            raise TypeError(
                f"damage_instance_id must be DamageInstanceId, got {type(damage_instance_id)}"
            )
        if not isinstance(lineage, OperationLineage):
            raise TypeError(f"lineage must be OperationLineage, got {type(lineage)}")

        if damage_instance_id in self._instance_to_permit_id:
            raise ValueError(
                f"A DamageSettlementPermit has already been issued for {damage_instance_id}. "
                "At most one permit per DamageInstance."
            )

        allocator = self._get_allocator(context)
        permit_id = allocator.allocate_permit_id("dsp")
        permit = DamageSettlementPermit(
            permit_id=permit_id,
            damage_instance_id=damage_instance_id,
        )
        record = _PermitRecord(permit=permit, lineage=lineage, consumed=False)
        self._permits[permit_id] = record
        self._instance_to_permit_id[damage_instance_id] = permit_id
        return permit

    def validate_and_consume_permit(
        self,
        permit: DamageSettlementPermit,
        request: DamageSettlementRequest,
    ) -> None:
        """
        Validate that the permit was issued by this coordinator, belongs to the request's
        DamageInstanceId and OperationLineage, and is unconsumed. Atomically mark it consumed.
        """
        if not isinstance(permit, DamageSettlementPermit):
            raise TypeError(f"permit must be DamageSettlementPermit, got {type(permit)}")
        if not isinstance(request, DamageSettlementRequest):
            raise TypeError(
                f"request must be DamageSettlementRequest, got {type(request)}"
            )

        record = self._permits.get(permit.permit_id)
        if record is None:
            raise ValueError(
                f"Permit '{permit.permit_id}' was not issued by this coordinator (fake or unknown permit)"
            )

        if record.permit != permit:
            raise ValueError("Permit record mismatch")

        if permit.damage_instance_id != request.damage_instance_id:
            raise ValueError(
                f"Permit damage_instance_id ({permit.damage_instance_id}) does not match "
                f"request damage_instance_id ({request.damage_instance_id})"
            )

        if record.consumed:
            raise ValueError(
                f"Permit '{permit.permit_id}' has already been consumed (replay blocked)"
            )

        if record.lineage != request.lineage:
            raise ValueError(
                f"OperationLineage mismatch: permit issued with {record.lineage}, "
                f"request provided {request.lineage}"
            )

        # Atomic consume before any side effects
        record.consumed = True

    def execute_standard_damage_instance(
        self,
        context: BattleContext,
        request: DamageRequest,
        lineage: OperationLineage,
        *,
        assigned_target_damage: int | None = None,
    ) -> DamageResolutionResult:
        """
        Execute an isolated standard DamageInstance.

        Phase 9.4 orchestration sequence:
        1. Allocate DamageInstanceId
        2. Issue at most one DamageSettlementPermit
        3. Call DamageSystem.calculate() -> freeze Dtotal
        4. Form typed DamageSettlementRequest (Dtarget = assigned_target_damage or Dtotal)
        5. Call DamageResolutionSystem.settle()
        6. Mark instance completed
        7. Return DamageResolutionResult
        """
        if not isinstance(request, DamageRequest):
            raise TypeError(f"request must be DamageRequest, got {type(request)}")
        if not isinstance(lineage, OperationLineage):
            raise TypeError(f"lineage must be OperationLineage, got {type(lineage)}")

        damage_instance_id = self.allocate_damage_instance_id(context)
        permit = self.issue_settlement_permit(damage_instance_id, lineage, context)

        damage_result = self._damage_system.calculate(context, request)

        if assigned_target_damage is None:
            target_amount = damage_result.final_damage
        else:
            if isinstance(assigned_target_damage, bool) or not isinstance(
                assigned_target_damage, int
            ):
                raise TypeError("assigned_target_damage must be an int")
            if assigned_target_damage < 0:
                raise ValueError("assigned_target_damage must be >= 0")
            target_amount = assigned_target_damage

        settlement_request = DamageSettlementRequest(
            damage_result=damage_result,
            assigned_target_damage=target_amount,
            damage_instance_id=damage_instance_id,
            lineage=lineage,
            origin=SettlementOrigin.STAGE9,
        )

        result = self._damage_resolution.settle(
            context=context,
            request=settlement_request,
            permit=permit,
        )

        self._completed_instances.add(damage_instance_id)
        return result

    def release_damage_instance(self, damage_instance_id: DamageInstanceId) -> None:
        """Release operation-local permit state for a completed instance."""
        permit_id = self._instance_to_permit_id.pop(damage_instance_id, None)
        if permit_id:
            self._permits.pop(permit_id, None)
        self._completed_instances.discard(damage_instance_id)
