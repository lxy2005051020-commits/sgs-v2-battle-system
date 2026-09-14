from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, TYPE_CHECKING

from .context import BattleContext
from .damage_system import DamageRequest, DamageResult, DamageSystem
from .events import EventType
from .execution_right_system import DamageSettlementPermit
from .operation_identity import DamageInstanceId, OperationLineage, _forbid_ordering
from .troop_system import TroopChangeResult, TroopSystem

if TYPE_CHECKING:
    from .damage_instance_coordinator import DamageInstanceCoordinator


class SettlementOrigin(str, Enum):
    STAGE9 = "STAGE9"
    LEGACY_COMPAT = "LEGACY_COMPAT"


@dataclass(frozen=True, slots=True, order=False)
class DamageSettlementRequest:
    """Stage9 显式伤害结算指令。"""

    damage_result: DamageResult
    assigned_target_damage: int
    damage_instance_id: DamageInstanceId | None
    lineage: OperationLineage | None
    origin: SettlementOrigin

    def __post_init__(self) -> None:
        if not isinstance(self.damage_result, DamageResult):
            raise TypeError(
                f"damage_result must be DamageResult, got {type(self.damage_result)}"
            )
        if isinstance(self.assigned_target_damage, bool) or not isinstance(
            self.assigned_target_damage, int
        ):
            raise TypeError("assigned_target_damage must be an int")
        if self.assigned_target_damage < 0:
            raise ValueError("assigned_target_damage must be >= 0")
        if not isinstance(self.origin, SettlementOrigin):
            raise TypeError(f"origin must be SettlementOrigin, got {type(self.origin)}")

        if self.origin == SettlementOrigin.STAGE9:
            if self.damage_instance_id is None:
                raise ValueError("damage_instance_id is required when origin is STAGE9")
            if not isinstance(self.damage_instance_id, DamageInstanceId):
                raise TypeError(
                    f"damage_instance_id must be DamageInstanceId, got {type(self.damage_instance_id)}"
                )
            if self.lineage is None:
                raise ValueError("lineage is required when origin is STAGE9")
            if not isinstance(self.lineage, OperationLineage):
                raise TypeError(
                    f"lineage must be OperationLineage, got {type(self.lineage)}"
                )
        elif self.origin == SettlementOrigin.LEGACY_COMPAT:
            if self.damage_instance_id is not None:
                raise ValueError(
                    "damage_instance_id must be None when origin is LEGACY_COMPAT"
                )
            if self.lineage is not None:
                raise ValueError("lineage must be None when origin is LEGACY_COMPAT")
            if self.assigned_target_damage != self.damage_result.final_damage:
                raise ValueError(
                    f"assigned_target_damage ({self.assigned_target_damage}) must equal "
                    f"damage_result.final_damage ({self.damage_result.final_damage}) "
                    "when origin is LEGACY_COMPAT"
                )

    def __lt__(self, other: Any) -> bool:
        _forbid_ordering("DamageSettlementRequest", "<")

    def __le__(self, other: Any) -> bool:
        _forbid_ordering("DamageSettlementRequest", "<=")

    def __gt__(self, other: Any) -> bool:
        _forbid_ordering("DamageSettlementRequest", ">")

    def __ge__(self, other: Any) -> bool:
        _forbid_ordering("DamageSettlementRequest", ">=")


@dataclass(frozen=True, slots=True, order=False)
class DamageResolutionResult:
    """
    Model A 统一伤害结算结果。

    四层伤害事实永久分离：
    - Dtotal: damage.final_damage (Stage8 理论计算上限)
    - Dtarget: assigned_target_damage (分配到目标的结算兵力)
    - ActualTargetTroopLoss: actual_target_troop_loss (目标实际损失兵力)
    - CreditedDamage: credited_damage (显式归因层，标准单体结算等于实际扣兵)
    """

    damage: DamageResult
    assigned_target_damage: int
    actual_target_troop_loss: int
    target_troops_before: int
    target_troops_after: int
    target_defeated: bool
    credited_damage: int
    troop_change: TroopChangeResult | None
    damage_instance_id: DamageInstanceId | None = None
    lineage: OperationLineage | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.damage, DamageResult):
            raise TypeError(f"damage must be DamageResult, got {type(self.damage)}")
        if isinstance(self.assigned_target_damage, bool) or not isinstance(
            self.assigned_target_damage, int
        ):
            raise TypeError("assigned_target_damage must be an int")
        if self.assigned_target_damage < 0:
            raise ValueError("assigned_target_damage must be >= 0")
        if isinstance(self.actual_target_troop_loss, bool) or not isinstance(
            self.actual_target_troop_loss, int
        ):
            raise TypeError("actual_target_troop_loss must be an int")
        if self.actual_target_troop_loss < 0:
            raise ValueError("actual_target_troop_loss must be >= 0")
        if isinstance(self.target_troops_before, bool) or not isinstance(
            self.target_troops_before, int
        ):
            raise TypeError("target_troops_before must be an int")
        if self.target_troops_before < 0:
            raise ValueError("target_troops_before must be >= 0")
        if isinstance(self.target_troops_after, bool) or not isinstance(
            self.target_troops_after, int
        ):
            raise TypeError("target_troops_after must be an int")
        if self.target_troops_after < 0:
            raise ValueError("target_troops_after must be >= 0")
        if not isinstance(self.target_defeated, bool):
            raise TypeError("target_defeated must be a bool")
        if isinstance(self.credited_damage, bool) or not isinstance(
            self.credited_damage, int
        ):
            raise TypeError("credited_damage must be an int")
        if self.credited_damage < 0:
            raise ValueError("credited_damage must be >= 0")
        if self.actual_target_troop_loss != (
            self.target_troops_before - self.target_troops_after
        ):
            raise ValueError(
                f"actual_target_troop_loss ({self.actual_target_troop_loss}) must equal "
                f"target_troops_before ({self.target_troops_before}) - "
                f"target_troops_after ({self.target_troops_after})"
            )
        if self.troop_change is not None and not isinstance(
            self.troop_change, TroopChangeResult
        ):
            raise TypeError(
                f"troop_change must be TroopChangeResult or None, got {type(self.troop_change)}"
            )
        if self.damage_instance_id is not None and not isinstance(
            self.damage_instance_id, DamageInstanceId
        ):
            raise TypeError(
                f"damage_instance_id must be DamageInstanceId or None, got {type(self.damage_instance_id)}"
            )
        if self.lineage is not None and not isinstance(self.lineage, OperationLineage):
            raise TypeError(
                f"lineage must be OperationLineage or None, got {type(self.lineage)}"
            )

    @property
    def dtotal(self) -> int:
        return self.damage.final_damage

    @property
    def requested_damage(self) -> int:
        return self.assigned_target_damage

    @property
    def defeated(self) -> bool:
        return self.target_defeated

    def __lt__(self, other: Any) -> bool:
        _forbid_ordering("DamageResolutionResult", "<")

    def __le__(self, other: Any) -> bool:
        _forbid_ordering("DamageResolutionResult", "<=")

    def __gt__(self, other: Any) -> bool:
        _forbid_ordering("DamageResolutionResult", ">")

    def __ge__(self, other: Any) -> bool:
        _forbid_ordering("DamageResolutionResult", ">=")


class DamageResolutionSystem:
    """统一协调理论伤害、实际扣兵与伤害结果事件。"""

    def __init__(
        self,
        damage_system: DamageSystem,
        troop_system: TroopSystem,
        *,
        coordinator: DamageInstanceCoordinator | None = None,
    ) -> None:
        self._damage = damage_system
        self._troops = troop_system
        self._coordinator = coordinator

    def bind_coordinator(self, coordinator: DamageInstanceCoordinator) -> None:
        self._coordinator = coordinator

    @property
    def coordinator(self) -> DamageInstanceCoordinator | None:
        return self._coordinator

    def calculate(
        self,
        context: BattleContext,
        request: DamageRequest,
    ) -> DamageResult:
        return self._damage.calculate(context, request)

    def resolve(
        self,
        context: BattleContext,
        request: DamageRequest,
    ) -> DamageResolutionResult:
        damage = self.calculate(context, request)
        return self.apply_result(context, damage)

    def apply_result(
        self,
        context: BattleContext,
        damage: DamageResult,
    ) -> DamageResolutionResult:
        """
        Legacy full-settlement wrapper (LEGACY_COMPAT).

        每次调用均作为独立的 legacy operation，不受 Stage9 DamageInstance replay guard 约束。
        禁止添加 optional assigned_amount 参数。
        """
        target = context.get_unit(damage.target_id)
        target_troops_before = target.troops

        provenance_payload = {
            "source_skill_id": damage.source_skill_id,
            "source_state_id": damage.source_state_id,
            "source_state_instance_id": damage.source_state_instance_id,
        }

        if damage.prevented:
            context.event_bus.publish(
                event_type=EventType.DAMAGE_PREVENTED,
                phase=context.current_phase,
                round_no=context.current_round,
                actor_id=damage.source_id,
                target_id=damage.target_id,
                payload={
                    "damage_type": damage.damage_type.value,
                    "source_type": damage.source_type.value,
                    "coefficient": damage.coefficient,
                    "base_damage": damage.base_damage,
                    "scaled_damage": damage.scaled_damage,
                    "requested_damage": damage.final_damage,
                    "reason_state_id": damage.prevented_by_state_id,
                    **provenance_payload,
                },
            )
            return DamageResolutionResult(
                damage=damage,
                assigned_target_damage=damage.final_damage,
                actual_target_troop_loss=0,
                target_troops_before=target_troops_before,
                target_troops_after=target_troops_before,
                target_defeated=False,
                credited_damage=0,
                troop_change=None,
                damage_instance_id=None,
                lineage=None,
            )

        was_alive = target.is_alive
        troop_change = self._troops.apply_damage(target, damage.final_damage)
        target_troops_after = target.troops
        actual_target_troop_loss = target_troops_before - target_troops_after

        context.event_bus.publish(
            event_type=EventType.DAMAGE_DEALT,
            phase=context.current_phase,
            round_no=context.current_round,
            actor_id=damage.source_id,
            target_id=damage.target_id,
            payload={
                "damage": troop_change.actual_change,
                "requested_damage": damage.final_damage,
                "damage_type": damage.damage_type.value,
                "source_type": damage.source_type.value,
                "coefficient": damage.coefficient,
                "base_damage": damage.base_damage,
                "scaled_damage": damage.scaled_damage,
                "target_remaining_troops": troop_change.remaining_troops,
                **provenance_payload,
            },
        )

        target_defeated = was_alive and not target.is_alive
        if target_defeated:
            context.event_bus.publish(
                event_type=EventType.UNIT_DEFEATED,
                phase=context.current_phase,
                round_no=context.current_round,
                actor_id=damage.source_id,
                target_id=damage.target_id,
                payload={"target_name": target.name},
            )

        return DamageResolutionResult(
            damage=damage,
            assigned_target_damage=damage.final_damage,
            actual_target_troop_loss=actual_target_troop_loss,
            target_troops_before=target_troops_before,
            target_troops_after=target_troops_after,
            target_defeated=target_defeated,
            credited_damage=actual_target_troop_loss,
            troop_change=troop_change,
            damage_instance_id=None,
            lineage=None,
        )

    def settle(
        self,
        context: BattleContext,
        request: DamageSettlementRequest,
        permit: DamageSettlementPermit,
    ) -> DamageResolutionResult:
        """
        Stage9 typed destructive settlement entry point.

        原子验证顺序：
        1. request.origin == STAGE9
        2. permit.damage_instance_id == request.damage_instance_id
        3. coordinator ownership, matching lineage, and unconsumed state
        4. 消费 permit (ONLY AFTER CONSUME 进行扣兵与事件发布)
        """
        if not isinstance(request, DamageSettlementRequest):
            raise TypeError(
                f"request must be DamageSettlementRequest, got {type(request)}"
            )
        if not isinstance(permit, DamageSettlementPermit):
            raise TypeError(f"permit must be DamageSettlementPermit, got {type(permit)}")

        if request.origin != SettlementOrigin.STAGE9:
            raise ValueError(
                f"DamageResolutionSystem.settle() requires STAGE9 origin, got {request.origin}"
            )

        if permit.damage_instance_id != request.damage_instance_id:
            raise ValueError(
                f"permit damage_instance_id ({permit.damage_instance_id}) does not match "
                f"request damage_instance_id ({request.damage_instance_id})"
            )

        if self._coordinator is None:
            raise ValueError(
                "DamageResolutionSystem has no registered DamageInstanceCoordinator to validate permit"
            )

        # 原子验证并消耗 permit (在任何扣兵与事件发布前必须先行消耗)
        self._coordinator.validate_and_consume_permit(permit=permit, request=request)

        damage = request.damage_result
        target = context.get_unit(damage.target_id)
        target_troops_before = target.troops

        provenance_payload = {
            "source_skill_id": damage.source_skill_id,
            "source_state_id": damage.source_state_id,
            "source_state_instance_id": damage.source_state_instance_id,
        }

        if damage.prevented:
            context.event_bus.publish(
                event_type=EventType.DAMAGE_PREVENTED,
                phase=context.current_phase,
                round_no=context.current_round,
                actor_id=damage.source_id,
                target_id=damage.target_id,
                payload={
                    "damage_type": damage.damage_type.value,
                    "source_type": damage.source_type.value,
                    "coefficient": damage.coefficient,
                    "base_damage": damage.base_damage,
                    "scaled_damage": damage.scaled_damage,
                    "requested_damage": damage.final_damage,
                    "reason_state_id": damage.prevented_by_state_id,
                    **provenance_payload,
                },
            )
            return DamageResolutionResult(
                damage=damage,
                assigned_target_damage=request.assigned_target_damage,
                actual_target_troop_loss=0,
                target_troops_before=target_troops_before,
                target_troops_after=target_troops_before,
                target_defeated=False,
                credited_damage=0,
                troop_change=None,
                damage_instance_id=request.damage_instance_id,
                lineage=request.lineage,
            )

        was_alive = target.is_alive
        troop_change = self._troops.apply_damage(target, request.assigned_target_damage)
        target_troops_after = target.troops
        actual_target_troop_loss = target_troops_before - target_troops_after
        credited_damage = actual_target_troop_loss

        context.event_bus.publish(
            event_type=EventType.DAMAGE_DEALT,
            phase=context.current_phase,
            round_no=context.current_round,
            actor_id=damage.source_id,
            target_id=damage.target_id,
            payload={
                "damage": actual_target_troop_loss,
                "requested_damage": request.assigned_target_damage,
                "damage_type": damage.damage_type.value,
                "source_type": damage.source_type.value,
                "coefficient": damage.coefficient,
                "base_damage": damage.base_damage,
                "scaled_damage": damage.scaled_damage,
                "target_remaining_troops": troop_change.remaining_troops,
                **provenance_payload,
            },
        )

        target_defeated = was_alive and not target.is_alive
        if target_defeated:
            context.event_bus.publish(
                event_type=EventType.UNIT_DEFEATED,
                phase=context.current_phase,
                round_no=context.current_round,
                actor_id=damage.source_id,
                target_id=damage.target_id,
                payload={"target_name": target.name},
            )

        return DamageResolutionResult(
            damage=damage,
            assigned_target_damage=request.assigned_target_damage,
            actual_target_troop_loss=actual_target_troop_loss,
            target_troops_before=target_troops_before,
            target_troops_after=target_troops_after,
            target_defeated=target_defeated,
            credited_damage=credited_damage,
            troop_change=troop_change,
            damage_instance_id=request.damage_instance_id,
            lineage=request.lineage,
        )

