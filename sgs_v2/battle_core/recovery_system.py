from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .context import BattleContext
from .events import EventType
from .official_state_catalog import OfficialStateId
from .troop_system import TroopChangeResult, TroopSystem


def _validate_required_id(value: str, field_name: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a str")
    if not value.strip():
        raise ValueError(f"{field_name} cannot be empty or whitespace")


def _validate_optional_id(value: str | None, field_name: str) -> None:
    if value is None:
        return
    _validate_required_id(value, field_name)


def _validate_state_provenance_pair(
    source_state_id: str | None,
    source_state_instance_id: str | None,
) -> None:
    if (source_state_id is None) != (source_state_instance_id is None):
        raise ValueError(
            "source_state_id and source_state_instance_id must both be set or both be None"
        )


@dataclass(frozen=True, slots=True)
class RecoveryRequest:
    source_id: str | None
    target_id: str
    amount: int
    source_skill_id: str | None = None
    source_state_id: str | None = None
    source_state_instance_id: str | None = None

    def __post_init__(self) -> None:
        _validate_optional_id(self.source_id, "source_id")
        _validate_required_id(self.target_id, "target_id")
        _validate_optional_id(self.source_skill_id, "source_skill_id")
        _validate_optional_id(self.source_state_id, "source_state_id")
        _validate_optional_id(
            self.source_state_instance_id,
            "source_state_instance_id",
        )
        _validate_state_provenance_pair(
            self.source_state_id,
            self.source_state_instance_id,
        )
        if isinstance(self.amount, bool) or not isinstance(self.amount, int):
            raise TypeError("amount must be an int")
        if self.amount < 0:
            raise ValueError("amount must be >= 0")


class RecoveryPreventionReason(str, Enum):
    HEALING_BAN = "HEALING_BAN"
    TARGET_DEFEATED = "TARGET_DEFEATED"


@dataclass(frozen=True, slots=True)
class RecoveryResolvedResult:
    request: RecoveryRequest
    troop_change: TroopChangeResult

    def __post_init__(self) -> None:
        if not isinstance(self.request, RecoveryRequest):
            raise TypeError("request must be a RecoveryRequest")
        if not isinstance(self.troop_change, TroopChangeResult):
            raise TypeError("troop_change must be a TroopChangeResult")


@dataclass(frozen=True, slots=True)
class RecoveryPreventedResult:
    request: RecoveryRequest
    reason: RecoveryPreventionReason
    reason_state_id: str | None

    def __post_init__(self) -> None:
        if not isinstance(self.request, RecoveryRequest):
            raise TypeError("request must be a RecoveryRequest")
        if not isinstance(self.reason, RecoveryPreventionReason):
            raise TypeError("reason must be a RecoveryPreventionReason")

        healing_ban_id = OfficialStateId.HEALING_BAN.value
        if self.reason is RecoveryPreventionReason.HEALING_BAN:
            if self.reason_state_id != healing_ban_id:
                raise ValueError(
                    "HEALING_BAN prevention must use the official healing_ban state id"
                )
        elif self.reason is RecoveryPreventionReason.TARGET_DEFEATED:
            if self.reason_state_id is not None:
                raise ValueError(
                    "TARGET_DEFEATED prevention cannot include reason_state_id"
                )


RecoveryResult = RecoveryResolvedResult | RecoveryPreventedResult


class RecoverySystem:
    """统一恢复规则入口；兵力实际写入仍只由 TroopSystem.restore 完成。"""

    def __init__(self, troop_system: TroopSystem) -> None:
        self._troops = troop_system

    def resolve(
        self,
        context: BattleContext,
        request: RecoveryRequest,
    ) -> RecoveryResult:
        if not isinstance(request, RecoveryRequest):
            raise TypeError("request must be a RecoveryRequest")

        target = context.get_unit(request.target_id)

        if not target.is_alive:
            return self._prevent(
                context,
                request,
                RecoveryPreventionReason.TARGET_DEFEATED,
                reason_state_id=None,
            )

        healing_ban_id = OfficialStateId.HEALING_BAN.value
        if context.states.has(owner_id=target.unit_id, state_id=healing_ban_id):
            return self._prevent(
                context,
                request,
                RecoveryPreventionReason.HEALING_BAN,
                reason_state_id=healing_ban_id,
            )

        troop_change = self._troops.restore(target, request.amount)
        result = RecoveryResolvedResult(
            request=request,
            troop_change=troop_change,
        )

        if troop_change.actual_change > 0:
            context.event_bus.publish(
                event_type=EventType.TROOPS_RECOVERED,
                phase=context.current_phase,
                round_no=context.current_round,
                actor_id=request.source_id,
                target_id=request.target_id,
                payload={
                    "source_id": request.source_id,
                    "source_skill_id": request.source_skill_id,
                    "source_state_id": request.source_state_id,
                    "source_state_instance_id": request.source_state_instance_id,
                    "target_id": request.target_id,
                    "requested_recovery": request.amount,
                    "actual_recovery": troop_change.actual_change,
                    "remaining_troops": troop_change.remaining_troops,
                },
            )

        return result

    @staticmethod
    def _prevent(
        context: BattleContext,
        request: RecoveryRequest,
        reason: RecoveryPreventionReason,
        *,
        reason_state_id: str | None,
    ) -> RecoveryPreventedResult:
        result = RecoveryPreventedResult(
            request=request,
            reason=reason,
            reason_state_id=reason_state_id,
        )
        context.event_bus.publish(
            event_type=EventType.RECOVERY_PREVENTED,
            phase=context.current_phase,
            round_no=context.current_round,
            actor_id=request.source_id,
            target_id=request.target_id,
            payload={
                "source_id": request.source_id,
                "source_skill_id": request.source_skill_id,
                "source_state_id": request.source_state_id,
                "source_state_instance_id": request.source_state_instance_id,
                "target_id": request.target_id,
                "requested_recovery": request.amount,
                "reason": reason.value,
                "reason_state_id": reason_state_id,
            },
        )
        return result
