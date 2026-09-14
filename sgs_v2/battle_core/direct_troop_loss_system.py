from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .context import BattleContext
from .events import EventType
from .operation_identity import (
    DamageInstanceId,
    DirectTroopLossId,
    OperationLineage,
    PartitionTransactionId,
    SourceType,
    _forbid_ordering,
)
from .troop_system import TroopChangeResult, TroopSystem


_DIRECT_LOSS_SOURCE_TYPES = frozenset(
    {SourceType.SHARE_DIRECT_LOSS, SourceType.DISTRIBUTION_DIRECT_LOSS}
)


@dataclass(frozen=True, slots=True, order=False)
class DirectTroopLossRequest:
    partition_transaction_id: PartitionTransactionId
    parent_damage_instance_id: DamageInstanceId
    source_type: SourceType
    physical_attacker: str | None
    physical_skill: str | None
    victim: str
    credit_owner: str | None
    theoretical_loss: int
    lineage: OperationLineage

    def __post_init__(self) -> None:
        if not isinstance(self.partition_transaction_id, PartitionTransactionId):
            raise TypeError("partition_transaction_id must be PartitionTransactionId")
        if not isinstance(self.parent_damage_instance_id, DamageInstanceId):
            raise TypeError("parent_damage_instance_id must be DamageInstanceId")
        if self.source_type not in _DIRECT_LOSS_SOURCE_TYPES:
            raise ValueError("source_type must be a direct-loss SourceType")
        if not isinstance(self.victim, str) or not self.victim.strip():
            raise ValueError("victim cannot be empty or whitespace")
        if isinstance(self.theoretical_loss, bool) or not isinstance(self.theoretical_loss, int):
            raise TypeError("theoretical_loss must be an int")
        if self.theoretical_loss < 0:
            raise ValueError("theoretical_loss must be >= 0")
        if not isinstance(self.lineage, OperationLineage):
            raise TypeError("lineage must be OperationLineage")
        if self.lineage.parent_damage_instance_id != self.parent_damage_instance_id:
            raise ValueError("direct-loss lineage must preserve parent DamageInstanceId")
        if self.lineage.source_type != self.source_type:
            raise ValueError("direct-loss lineage source_type mismatch")
        if self.lineage.physical_attacker != self.physical_attacker:
            raise ValueError("direct-loss physical_attacker must match lineage")
        if self.lineage.physical_skill != self.physical_skill:
            raise ValueError("direct-loss physical_skill must match lineage")
        if self.lineage.credit_owner != self.credit_owner:
            raise ValueError("direct-loss credit_owner must match lineage")

    def __lt__(self, other: Any) -> bool:
        _forbid_ordering("DirectTroopLossRequest", "<")

    def __le__(self, other: Any) -> bool:
        _forbid_ordering("DirectTroopLossRequest", "<=")

    def __gt__(self, other: Any) -> bool:
        _forbid_ordering("DirectTroopLossRequest", ">")

    def __ge__(self, other: Any) -> bool:
        _forbid_ordering("DirectTroopLossRequest", ">=")


@dataclass(frozen=True, slots=True, order=False)
class AttributedDirectTroopLoss:
    direct_loss_id: DirectTroopLossId
    partition_transaction_id: PartitionTransactionId
    parent_damage_instance_id: DamageInstanceId
    source_type: SourceType
    physical_attacker: str | None
    physical_skill: str | None
    victim: str
    credit_owner: str | None
    theoretical_loss: int
    actual_loss: int
    lineage: OperationLineage

    def __post_init__(self) -> None:
        if not isinstance(self.direct_loss_id, DirectTroopLossId):
            raise TypeError("direct_loss_id must be DirectTroopLossId")
        if self.source_type not in _DIRECT_LOSS_SOURCE_TYPES:
            raise ValueError("source_type must be a direct-loss SourceType")
        if self.actual_loss < 0 or self.actual_loss > self.theoretical_loss:
            raise ValueError("actual_loss must be within [0, theoretical_loss]")

    def __lt__(self, other: Any) -> bool:
        _forbid_ordering("AttributedDirectTroopLoss", "<")

    def __le__(self, other: Any) -> bool:
        _forbid_ordering("AttributedDirectTroopLoss", "<=")

    def __gt__(self, other: Any) -> bool:
        _forbid_ordering("AttributedDirectTroopLoss", ">")

    def __ge__(self, other: Any) -> bool:
        _forbid_ordering("AttributedDirectTroopLoss", ">=")


@dataclass(frozen=True, slots=True)
class DirectTroopLossResolution:
    loss: AttributedDirectTroopLoss
    troops_before: int
    troops_after: int
    troop_change: TroopChangeResult
    death_edge: bool


class DirectTroopLossResolver:
    """Unique destructive owner for Share/Distribution direct troop loss.

    This resolver deliberately has no DamageSystem or DamageResolutionSystem dependency.
    Direct loss is troop mutation + explicit attribution, never a second hit.
    """

    def __init__(self, troop_system: TroopSystem) -> None:
        if not isinstance(troop_system, TroopSystem):
            raise TypeError(f"troop_system must be TroopSystem, got {type(troop_system)}")
        self._troops = troop_system

    @property
    def troop_system(self) -> TroopSystem:
        return self._troops

    def resolve(
        self,
        context: BattleContext,
        request: DirectTroopLossRequest,
    ) -> DirectTroopLossResolution:
        if not isinstance(context, BattleContext):
            raise TypeError(f"context must be BattleContext, got {type(context)}")
        if not isinstance(request, DirectTroopLossRequest):
            raise TypeError(f"request must be DirectTroopLossRequest, got {type(request)}")

        victim = context.get_unit(request.victim)
        troops_before = victim.troops
        was_alive = victim.is_alive
        direct_loss_id = context.id_allocator.allocate_direct_troop_loss_id()

        troop_change = self._troops.apply_damage(victim, request.theoretical_loss)
        troops_after = victim.troops
        actual_loss = troops_before - troops_after
        death_edge = was_alive and not victim.is_alive

        fact = AttributedDirectTroopLoss(
            direct_loss_id=direct_loss_id,
            partition_transaction_id=request.partition_transaction_id,
            parent_damage_instance_id=request.parent_damage_instance_id,
            source_type=request.source_type,
            physical_attacker=request.physical_attacker,
            physical_skill=request.physical_skill,
            victim=request.victim,
            credit_owner=request.credit_owner,
            theoretical_loss=request.theoretical_loss,
            actual_loss=actual_loss,
            lineage=request.lineage,
        )

        context.event_bus.publish(
            event_type=EventType.DIRECT_TROOP_LOSS,
            phase=context.current_phase,
            round_no=context.current_round,
            actor_id=request.physical_attacker,
            target_id=request.victim,
            payload={
                "direct_loss_id": direct_loss_id.value,
                "partition_transaction_id": request.partition_transaction_id.value,
                "parent_damage_instance_id": request.parent_damage_instance_id.value,
                "source_type": request.source_type.value,
                "physical_skill": request.physical_skill,
                "credit_owner": request.credit_owner,
                "theoretical_loss": request.theoretical_loss,
                "actual_loss": actual_loss,
                "target_remaining_troops": troops_after,
            },
        )

        if death_edge:
            context.event_bus.publish(
                event_type=EventType.UNIT_DEFEATED,
                phase=context.current_phase,
                round_no=context.current_round,
                actor_id=request.physical_attacker,
                target_id=request.victim,
                payload={
                    "target_name": victim.name,
                    "source_type": request.source_type.value,
                    "direct_loss_id": direct_loss_id.value,
                },
            )

        return DirectTroopLossResolution(
            loss=fact,
            troops_before=troops_before,
            troops_after=troops_after,
            troop_change=troop_change,
            death_edge=death_edge,
        )
