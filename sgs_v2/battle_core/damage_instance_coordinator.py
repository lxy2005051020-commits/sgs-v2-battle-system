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
class _ActiveDamageInstanceRecord:
    damage_instance_id: DamageInstanceId
    lineage: OperationLineage
    owning_context: BattleContext
    permit_id: str | None = None
    permit_issued: bool = False
    permit_consumed: bool = False
    closed: bool = False


@dataclass(slots=True)
class _PermitRecord:
    permit: DamageSettlementPermit
    damage_instance_id: DamageInstanceId
    lineage: OperationLineage
    owning_context: BattleContext
    consumed: bool = False


class DamageInstanceCoordinator:
    """
    Stage9 Standard DamageInstance Orchestration Owner.

    Responsibilities:
    - Allocate DamageInstanceId and begin active DamageInstance scope bound to BattleContext
    - Own DamageInstance-local active scope and permit registry
    - Issue at most one DamageSettlementPermit per active DamageInstance
    - Validate issuer ownership, context ownership, and unconsumed state
    - Preserve OperationLineage
    - Call DamageSystem.calculate while DamageInstance identity is active
    - Form typed DamageSettlementRequest
    - Call DamageResolutionSystem.settle
    - Close active DamageInstance scope and release operation-local state

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

        # Active operation-local scope & permit tracking keyed by (id(context), id) (zero battle-long leak)
        self._active_instances: dict[tuple[int, DamageInstanceId], _ActiveDamageInstanceRecord] = {}
        self._permits: dict[tuple[int, str], _PermitRecord] = {}

        # Bind this coordinator to the resolution system
        self._damage_resolution.bind_coordinator(self)

    @property
    def damage_system(self) -> DamageSystem:
        return self._damage_system

    @property
    def damage_resolution_system(self) -> DamageResolutionSystem:
        return self._damage_resolution

    def allocate_damage_instance_id(
        self,
        context: BattleContext,
    ) -> DamageInstanceId:
        if context is None or not isinstance(context, BattleContext):
            raise TypeError(f"context must be BattleContext, got {type(context)}")
        return context.id_allocator.allocate_damage_instance_id()

    def begin_damage_instance(
        self,
        context: BattleContext,
        lineage: OperationLineage,
    ) -> DamageInstanceId:
        """
        Begin an active coordinator-owned DamageInstance scope bound to a BattleContext.
        Allocates fresh DamageInstanceId from context.id_allocator, registers active record, and binds lineage.
        """
        if context is None or not isinstance(context, BattleContext):
            raise TypeError(f"context must be BattleContext, got {type(context)}")
        if lineage is None or not isinstance(lineage, OperationLineage):
            raise TypeError(
                f"lineage must be OperationLineage, got {type(lineage)}"
            )
        damage_instance_id = context.id_allocator.allocate_damage_instance_id()
        record = _ActiveDamageInstanceRecord(
            damage_instance_id=damage_instance_id,
            lineage=lineage,
            owning_context=context,
        )
        self._active_instances[(id(context), damage_instance_id)] = record
        return damage_instance_id

    def is_instance_active(
        self,
        damage_instance_id: DamageInstanceId,
        context: BattleContext | None = None,
    ) -> bool:
        """Check whether a DamageInstance is currently active and not closed."""
        if context is not None:
            record = self._active_instances.get((id(context), damage_instance_id))
            return record is not None and not record.closed
        for (c_id, d_id), record in self._active_instances.items():
            if d_id == damage_instance_id and not record.closed:
                return True
        return False

    def issue_settlement_permit(
        self,
        damage_instance_id: DamageInstanceId,
        lineage: OperationLineage,
        context: BattleContext | None = None,
    ) -> DamageSettlementPermit:
        """
        Issue exactly one DamageSettlementPermit for an active coordinator-owned DamageInstance.
        Rejects arbitrary IDs, closed IDs, mismatched lineages, duplicate requests, and foreign contexts.
        """
        if not isinstance(damage_instance_id, DamageInstanceId):
            raise TypeError(
                f"damage_instance_id must be DamageInstanceId, got {type(damage_instance_id)}"
            )
        if not isinstance(lineage, OperationLineage):
            raise TypeError(f"lineage must be OperationLineage, got {type(lineage)}")

        record: _ActiveDamageInstanceRecord | None = None
        if context is not None:
            if not isinstance(context, BattleContext):
                raise TypeError(f"context must be BattleContext, got {type(context)}")
            record = self._active_instances.get((id(context), damage_instance_id))
        else:
            matching = [
                r for (c_id, d_id), r in self._active_instances.items()
                if d_id == damage_instance_id
            ]
            if len(matching) == 1:
                record = matching[0]
            elif len(matching) > 1:
                raise ValueError(
                    f"Ambiguous active DamageInstanceId '{damage_instance_id}' across multiple contexts; "
                    "context must be provided"
                )

        if record is None:
            # Check if this damage_instance_id exists under another context
            for (c_id, d_id), r in self._active_instances.items():
                if d_id == damage_instance_id:
                    raise ValueError(
                        f"Supplied context does not match the owning BattleContext of DamageInstance '{damage_instance_id}'"
                    )
            raise ValueError(
                f"DamageInstanceId '{damage_instance_id}' is not an active instance "
                "owned by this coordinator (unknown, closed, or never begun)"
            )

        if context is not None and context is not record.owning_context:
            raise ValueError(
                f"Supplied context does not match the owning BattleContext of DamageInstance '{damage_instance_id}'"
            )

        if record.closed:
            raise ValueError(
                f"DamageInstanceId '{damage_instance_id}' is closed; cannot issue permit"
            )

        if record.lineage != lineage:
            raise ValueError(
                f"OperationLineage mismatch: instance was begun with {record.lineage}, "
                f"permit requested with {lineage}"
            )

        if record.permit_issued:
            raise ValueError(
                f"A DamageSettlementPermit has already been issued for {damage_instance_id}. "
                "At most one permit per DamageInstance lifetime."
            )

        owning_ctx = record.owning_context
        permit_id = owning_ctx.id_allocator.allocate_permit_id("dsp")
        permit = DamageSettlementPermit(
            permit_id=permit_id,
            damage_instance_id=damage_instance_id,
        )
        permit_record = _PermitRecord(
            permit=permit,
            damage_instance_id=damage_instance_id,
            lineage=lineage,
            owning_context=owning_ctx,
            consumed=False,
        )
        self._permits[(id(owning_ctx), permit_id)] = permit_record
        record.permit_id = permit_id
        record.permit_issued = True
        return permit

    def validate_and_consume_permit(
        self,
        context: BattleContext,
        permit: DamageSettlementPermit,
        request: DamageSettlementRequest,
    ) -> None:
        """
        Validate that the permit was issued by this coordinator for the provided context,
        belongs to an active DamageInstanceId and OperationLineage, and is unconsumed.
        Atomically mark it consumed.
        """
        if not isinstance(context, BattleContext):
            raise TypeError(f"context must be BattleContext, got {type(context)}")
        if not isinstance(permit, DamageSettlementPermit):
            raise TypeError(f"permit must be DamageSettlementPermit, got {type(permit)}")
        if not isinstance(request, DamageSettlementRequest):
            raise TypeError(
                f"request must be DamageSettlementRequest, got {type(request)}"
            )

        # 1. Pre-check: Check if this exact capability object was issued for a different context
        for (c_id, p_id), r in self._permits.items():
            if r.permit is permit and r.owning_context is not context:
                raise ValueError(
                    f"Permit '{permit.permit_id}' was issued for a different BattleContext "
                    f"({r.owning_context.battle_id} != {context.battle_id})"
                )

        # 2. Check if a permit record exists for this context
        permit_key = (id(context), permit.permit_id)
        record = self._permits.get(permit_key)

        if record is None:
            raise ValueError(
                f"Permit '{permit.permit_id}' was not issued by this coordinator, closed, or not active"
            )

        # 3. Exact capability object authenticity check (reject forged clones having identical fields)
        if record.permit is not permit:
            raise ValueError(
                f"Permit capability authenticity failure: permit '{permit.permit_id}' is not the exact "
                "issued capability object for this record (forged clone rejected)"
            )

        if record.owning_context is not context:
            raise ValueError(
                f"Permit '{permit.permit_id}' owning context mismatch"
            )

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

        active_record = self._active_instances.get((id(context), permit.damage_instance_id))
        if active_record is None or active_record.closed:
            raise ValueError(
                f"DamageInstance '{permit.damage_instance_id}' is no longer active"
            )

        if active_record.owning_context is not context:
            raise ValueError(
                f"DamageInstance '{permit.damage_instance_id}' was not begun in this BattleContext"
            )

        if active_record.permit_consumed:
            raise ValueError(
                f"DamageInstance '{permit.damage_instance_id}' permit has already been consumed"
            )

        # Atomic consume before any side effects (ONLY reached if all checks above pass!)
        record.consumed = True
        active_record.permit_consumed = True

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

        Phase 9.4 frozen orchestration sequence:
        1. Validate context, request, and lineage
        2. Begin DamageInstance scope on context (allocate DamageInstanceId, register active record)
        3. Call DamageSystem.calculate() -> freeze Dtotal while DamageInstance identity is active
        4. Determine isolated Dtarget
        5. Issue exactly one DamageSettlementPermit for this active DamageInstance
        6. Form typed DamageSettlementRequest
        7. Call DamageResolutionSystem.settle()
        8. Close / release active DamageInstance scope in finally block
        9. Return DamageResolutionResult
        """
        if not isinstance(context, BattleContext):
            raise TypeError(f"context must be BattleContext, got {type(context)}")
        if not isinstance(request, DamageRequest):
            raise TypeError(f"request must be DamageRequest, got {type(request)}")
        if not isinstance(lineage, OperationLineage):
            raise TypeError(f"lineage must be OperationLineage, got {type(lineage)}")

        # Step 1: begin DamageInstance identity FIRST on context
        damage_instance_id = self.begin_damage_instance(context, lineage)

        try:
            # Step 2: calculate while DamageInstance identity is already active
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

            # Step 3: issue exactly one permit for this active DamageInstance
            permit = self.issue_settlement_permit(damage_instance_id, lineage, context)

            settlement_request = DamageSettlementRequest(
                damage_result=damage_result,
                assigned_target_damage=target_amount,
                damage_instance_id=damage_instance_id,
                lineage=lineage,
                origin=SettlementOrigin.STAGE9,
            )

            # Step 4: atomic settle
            return self._damage_resolution.settle(
                context=context,
                request=settlement_request,
                permit=permit,
            )
        finally:
            self.close_damage_instance(damage_instance_id, context)

    def close_damage_instance(
        self,
        damage_instance_id: DamageInstanceId,
        context: BattleContext,
    ) -> None:
        """Close active DamageInstance scope and release operation-local state."""
        if context is None or not isinstance(context, BattleContext):
            raise TypeError(f"context must be BattleContext, got {type(context)}")
        if not isinstance(damage_instance_id, DamageInstanceId):
            raise TypeError(
                f"damage_instance_id must be DamageInstanceId, got {type(damage_instance_id)}"
            )

        record = self._active_instances.pop((id(context), damage_instance_id), None)
        if record is not None:
            record.closed = True
            if record.permit_id is not None:
                self._permits.pop((id(context), record.permit_id), None)

    def release_damage_instance(
        self,
        damage_instance_id: DamageInstanceId,
        context: BattleContext,
    ) -> None:
        """Release operation-local permit state for a completed instance."""
        if context is None or not isinstance(context, BattleContext):
            raise TypeError(f"context must be BattleContext, got {type(context)}")
        if not isinstance(damage_instance_id, DamageInstanceId):
            raise TypeError(
                f"damage_instance_id must be DamageInstanceId, got {type(damage_instance_id)}"
            )
        self.close_damage_instance(damage_instance_id, context)
