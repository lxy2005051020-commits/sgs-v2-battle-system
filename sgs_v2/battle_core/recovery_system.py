from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from .context import BattleContext
from .events import EventType
from .official_state_catalog import OfficialStateId
from .stage9_integerization import ExactRatio
from .state_generation import StateApplicationGenerationId
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


class RecoveryModifierPolicy(str, Enum):
    NONE = "NONE"
    APPLY = "APPLY"


@dataclass(frozen=True, slots=True)
class RecoveryRequest:
    source_id: str | None
    target_id: str
    amount: int
    source_skill_id: str | None = None
    source_state_id: str | None = None
    source_state_instance_id: str | None = None
    source_generation_id: StateApplicationGenerationId | None = None
    modifier_policy: RecoveryModifierPolicy = RecoveryModifierPolicy.NONE

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
        if self.source_generation_id is not None and not isinstance(
            self.source_generation_id, StateApplicationGenerationId
        ):
            raise TypeError("source_generation_id must be a StateApplicationGenerationId or None")
        if not isinstance(self.modifier_policy, RecoveryModifierPolicy):
            raise TypeError("modifier_policy must be a RecoveryModifierPolicy")
        if isinstance(self.amount, bool) or not isinstance(self.amount, int):
            raise TypeError("amount must be an int")
        if self.amount < 0:
            raise ValueError("amount must be >= 0")

    @property
    def base_amount(self) -> int:
        """Recovery quantity before the canonical recovery-modifier stage."""
        return self.amount


RecoveryModifierProvider = Callable[[BattleContext, RecoveryRequest], ExactRatio]


class RecoveryPreventionReason(str, Enum):
    HEALING_BAN = "HEALING_BAN"
    TARGET_DEFEATED = "TARGET_DEFEATED"


@dataclass(frozen=True, slots=True)
class RecoveryResolvedResult:
    request: RecoveryRequest
    troop_change: TroopChangeResult
    source_generation_id: StateApplicationGenerationId | None = None
    modified_recovery: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.request, RecoveryRequest):
            raise TypeError("request must be a RecoveryRequest")
        if not isinstance(self.troop_change, TroopChangeResult):
            raise TypeError("troop_change must be a TroopChangeResult")
        if self.source_generation_id is not None and not isinstance(
            self.source_generation_id, StateApplicationGenerationId
        ):
            raise TypeError("source_generation_id must be a StateApplicationGenerationId or None")
        if self.modified_recovery is not None:
            if isinstance(self.modified_recovery, bool) or not isinstance(self.modified_recovery, int):
                raise TypeError("modified_recovery must be an int or None")
            if self.modified_recovery < 0:
                raise ValueError("modified_recovery must be >= 0")

    @property
    def actual_recovery(self) -> int:
        return self.troop_change.actual_change

    @property
    def settled_request_amount(self) -> int:
        return self.request.amount if self.modified_recovery is None else self.modified_recovery


@dataclass(frozen=True, slots=True)
class RecoveryPreventedResult:
    request: RecoveryRequest
    reason: RecoveryPreventionReason
    reason_state_id: str | None
    source_generation_id: StateApplicationGenerationId | None = None
    modified_recovery: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.request, RecoveryRequest):
            raise TypeError("request must be a RecoveryRequest")
        if not isinstance(self.reason, RecoveryPreventionReason):
            raise TypeError("reason must be a RecoveryPreventionReason")
        if self.source_generation_id is not None and not isinstance(
            self.source_generation_id, StateApplicationGenerationId
        ):
            raise TypeError("source_generation_id must be a StateApplicationGenerationId or None")
        if self.modified_recovery is not None:
            if isinstance(self.modified_recovery, bool) or not isinstance(self.modified_recovery, int):
                raise TypeError("modified_recovery must be an int or None")
            if self.modified_recovery < 0:
                raise ValueError("modified_recovery must be >= 0")

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

    @property
    def settled_request_amount(self) -> int:
        return self.request.amount if self.modified_recovery is None else self.modified_recovery


RecoveryResult = RecoveryResolvedResult | RecoveryPreventedResult


class RecoverySystem:
    """统一恢复结算入口；Recovery Modifier 的 second CEIL 只在这里发生。"""

    def __init__(
        self,
        troop_system: TroopSystem,
        stage11_state_runtime=None,
        recovery_modifier_provider: RecoveryModifierProvider | None = None,
    ) -> None:
        if recovery_modifier_provider is not None and not callable(recovery_modifier_provider):
            raise TypeError("recovery_modifier_provider must be callable or None")
        self._troops = troop_system
        self._stage11 = stage11_state_runtime
        self._recovery_modifier_provider = recovery_modifier_provider

    @staticmethod
    def _ceil_ratio(base: int, ratio: ExactRatio) -> int:
        if isinstance(base, bool) or not isinstance(base, int):
            raise TypeError("base must be an int")
        if not isinstance(ratio, ExactRatio):
            raise TypeError("recovery modifier provider must return ExactRatio")
        if base < 0:
            raise ValueError("base must be >= 0")
        if ratio.numerator < 0:
            raise ValueError("recovery modifier ratio must be >= 0")
        if base == 0 or ratio.numerator == 0:
            return 0
        num = base * ratio.numerator
        den = ratio.denominator
        return (num + den - 1) // den

    def _apply_recovery_modifier(
        self,
        context: BattleContext,
        request: RecoveryRequest,
    ) -> int:
        if request.amount == 0 or request.modifier_policy is RecoveryModifierPolicy.NONE:
            return request.amount

        ratio = (
            ExactRatio(1, 1)
            if self._recovery_modifier_provider is None
            else self._recovery_modifier_provider(context, request)
        )
        return self._ceil_ratio(request.amount, ratio)

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
                modified_recovery=None,
            )

        modified_recovery = self._apply_recovery_modifier(context, request)

        healing_ban_id = OfficialStateId.HEALING_BAN.value
        if self._stage11 is not None:
            healing_banned = self._stage11.healing_block_active(
                context, target.unit_id
            )
        else:
            healing_banned = context.states.has(
                owner_id=target.unit_id, state_id=healing_ban_id
            )

        if modified_recovery > 0 and healing_banned:
            return self._prevent(
                context,
                request,
                RecoveryPreventionReason.HEALING_BAN,
                reason_state_id=healing_ban_id,
                modified_recovery=modified_recovery,
            )

        troop_change = self._troops.restore(target, modified_recovery)
        result = RecoveryResolvedResult(
            request=request,
            troop_change=troop_change,
            source_generation_id=request.source_generation_id,
            modified_recovery=modified_recovery,
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
                    "source_generation_id": (
                        str(request.source_generation_id)
                        if request.source_generation_id
                        else None
                    ),
                    "target_id": request.target_id,
                    "base_recovery": request.amount,
                    "modified_recovery": modified_recovery,
                    "requested_recovery": modified_recovery,
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
        modified_recovery: int | None,
    ) -> RecoveryPreventedResult:
        result = RecoveryPreventedResult(
            request=request,
            reason=reason,
            reason_state_id=reason_state_id,
            source_generation_id=request.source_generation_id,
            modified_recovery=modified_recovery,
        )
        settled_request = request.amount if modified_recovery is None else modified_recovery
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
                "source_generation_id": (
                    str(request.source_generation_id)
                    if request.source_generation_id
                    else None
                ),
                "target_id": request.target_id,
                "base_recovery": request.amount,
                "modified_recovery": modified_recovery,
                "requested_recovery": settled_request,
                "reason": reason.value,
                "reason_state_id": reason_state_id,
            },
        )
        return result
