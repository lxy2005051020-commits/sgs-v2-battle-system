from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .preparation_interruption import (
    PreparationInterruptionRequest,
    PreparationInterruptionResult,
    PreparationInterruptionScope,
    PreparationInterruptionStatus,
)
from .provider_identity import SkillProviderRef


class PreparationStatus(str, Enum):
    PREPARING = "PREPARING"


@dataclass(frozen=True, slots=True)
class PreparationRecord:
    """Minimal identity for one already-admitted Active operation that is PREPARING."""

    holder_id: str
    provider_ref: SkillProviderRef
    skill_id: str
    admitted_operation_id: str
    status: PreparationStatus = PreparationStatus.PREPARING

    def __post_init__(self) -> None:
        if not isinstance(self.holder_id, str) or not self.holder_id.strip():
            raise ValueError("holder_id cannot be empty or whitespace")
        if not isinstance(self.provider_ref, SkillProviderRef):
            raise TypeError("provider_ref must be a SkillProviderRef")
        if self.provider_ref.owner_id != self.holder_id:
            raise ValueError("provider_ref owner must match holder_id")
        if not isinstance(self.skill_id, str) or not self.skill_id.strip():
            raise ValueError("skill_id cannot be empty or whitespace")
        if self.provider_ref.skill_id != self.skill_id:
            raise ValueError("skill_id must match provider_ref.skill_id")
        if (
            not isinstance(self.admitted_operation_id, str)
            or not self.admitted_operation_id.strip()
        ):
            raise ValueError("admitted_operation_id cannot be empty or whitespace")
        if self.status is not PreparationStatus.PREPARING:
            raise ValueError("PreparationRecord status must be PREPARING")


class PreparationStateOwner:
    """Minimal Stage12 PREPARING truth owner.

    This component stores only already-admitted Active work that is currently
    PREPARING. It performs no admission, RNG, target selection, round
    progression, or prepared-skill execution. Stage15 may later adopt or
    replace this storage behind the stable PreparationInterruptionPort.
    """

    __slots__ = ("_records",)

    def __init__(self) -> None:
        self._records: dict[str, PreparationRecord] = {}

    def begin_preparing(
        self,
        *,
        holder_id: str,
        provider_ref: SkillProviderRef,
        admitted_operation_id: str,
    ) -> PreparationRecord:
        """Record one already-admitted Active operation as PREPARING."""

        record = PreparationRecord(
            holder_id=holder_id,
            provider_ref=provider_ref,
            skill_id=provider_ref.skill_id,
            admitted_operation_id=admitted_operation_id,
        )
        if admitted_operation_id in self._records:
            raise ValueError(
                f"admitted operation is already PREPARING: {admitted_operation_id}"
            )
        self._records[admitted_operation_id] = record
        return record

    def is_preparing(self, holder_id: str) -> bool:
        return bool(self.get_preparing(holder_id))

    def get_preparing(self, holder_id: str) -> tuple[PreparationRecord, ...]:
        if not isinstance(holder_id, str) or not holder_id.strip():
            raise ValueError("holder_id cannot be empty or whitespace")
        return tuple(
            sorted(
                (
                    record
                    for record in self._records.values()
                    if record.holder_id == holder_id
                ),
                key=lambda item: item.admitted_operation_id,
            )
        )

    def clear_preparing(self, admitted_operation_id: str) -> PreparationRecord | None:
        if (
            not isinstance(admitted_operation_id, str)
            or not admitted_operation_id.strip()
        ):
            raise ValueError("admitted_operation_id cannot be empty or whitespace")
        return self._records.pop(admitted_operation_id, None)

    def interrupt(
        self,
        context: object,
        request: PreparationInterruptionRequest,
    ) -> PreparationInterruptionResult:
        del context
        if not isinstance(request, PreparationInterruptionRequest):
            raise TypeError("request must be a PreparationInterruptionRequest")

        holder_records = self.get_preparing(request.holder_id)
        if not holder_records:
            return PreparationInterruptionResult(
                request=request,
                status=PreparationInterruptionStatus.NOT_PREPARING,
            )

        if request.scope is PreparationInterruptionScope.HOLDER_ACTIVE:
            matched = holder_records
        elif request.scope is PreparationInterruptionScope.PROVIDER:
            assert request.provider_ref is not None
            matched = tuple(
                record
                for record in holder_records
                if record.provider_ref == request.provider_ref
            )
            if not matched:
                return PreparationInterruptionResult(
                    request=request,
                    status=PreparationInterruptionStatus.PROVIDER_NOT_MATCHED,
                )
        else:
            return PreparationInterruptionResult(
                request=request,
                status=PreparationInterruptionStatus.UNSUPPORTED,
            )

        # Remove every matched record before returning. A repeated command can
        # therefore observe only NOT_PREPARING / PROVIDER_NOT_MATCHED, never the
        # same successful interruption twice.
        for record in matched:
            self._records.pop(record.admitted_operation_id, None)

        interrupted_provider_refs: list[SkillProviderRef] = []
        for record in matched:
            if record.provider_ref not in interrupted_provider_refs:
                interrupted_provider_refs.append(record.provider_ref)

        return PreparationInterruptionResult(
            request=request,
            status=PreparationInterruptionStatus.INTERRUPTED,
            interrupted_provider_refs=tuple(interrupted_provider_refs),
        )
