from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .context import BattleContext
from .damage_system import DamageResult
from .operation_identity import DamageInstanceId, PartitionTransactionId, _forbid_ordering
from .stage9_integerization import (
    ExactRatio,
    round_half_up_divide_int,
    round_half_up_product_int_ratio,
)
from .stage9_state_params import DamageShareStateParams, DistributionStateParams
from .stage9_state_runtime import Stage9StateRuntime


class DamagePartitionKind(str, Enum):
    NONE = "NONE"
    SHARE = "SHARE"
    DISTRIBUTION = "DISTRIBUTION"


class DistributionRuntimeAuthority(str, Enum):
    FROZEN_P0 = "FROZEN_P0"
    PROJECT_RUNTIME_DEFAULT = "PROJECT_RUNTIME_DEFAULT"


@dataclass(frozen=True, slots=True, order=False)
class NoPartitionPlan:
    parent_damage_instance_id: DamageInstanceId
    target_id: str
    dtotal: int
    kind: DamagePartitionKind = DamagePartitionKind.NONE

    def __lt__(self, other: Any) -> bool:
        _forbid_ordering("NoPartitionPlan", "<")

    def __le__(self, other: Any) -> bool:
        _forbid_ordering("NoPartitionPlan", "<=")

    def __gt__(self, other: Any) -> bool:
        _forbid_ordering("NoPartitionPlan", ">")

    def __ge__(self, other: Any) -> bool:
        _forbid_ordering("NoPartitionPlan", ">=")


@dataclass(frozen=True, slots=True, order=False)
class DamageShareTransactionPlan:
    partition_transaction_id: PartitionTransactionId
    parent_damage_instance_id: DamageInstanceId
    target_id: str
    sharer_id: str
    dtotal: int
    ratio: ExactRatio
    dsharer_theoretical: int
    dtarget: int
    kind: DamagePartitionKind = DamagePartitionKind.SHARE

    def __post_init__(self) -> None:
        if self.dtarget + self.dsharer_theoretical != self.dtotal:
            raise ValueError("Share plan must conserve Dtotal exactly")

    def __lt__(self, other: Any) -> bool:
        _forbid_ordering("DamageShareTransactionPlan", "<")

    def __le__(self, other: Any) -> bool:
        _forbid_ordering("DamageShareTransactionPlan", "<=")

    def __gt__(self, other: Any) -> bool:
        _forbid_ordering("DamageShareTransactionPlan", ">")

    def __ge__(self, other: Any) -> bool:
        _forbid_ordering("DamageShareTransactionPlan", ">=")


@dataclass(frozen=True, slots=True, order=False)
class DistributionTransactionPlan:
    partition_transaction_id: PartitionTransactionId
    parent_damage_instance_id: DamageInstanceId
    target_id: str
    participant_ids: tuple[str, ...]
    participant_count: int
    dtotal: int
    ratio: ExactRatio
    dtarget: int
    dtransfer: int
    dparticipant: int
    runtime_authority: DistributionRuntimeAuthority = DistributionRuntimeAuthority.PROJECT_RUNTIME_DEFAULT
    kind: DamagePartitionKind = DamagePartitionKind.DISTRIBUTION

    def __post_init__(self) -> None:
        if self.participant_count != len(self.participant_ids):
            raise ValueError("participant_count must equal immutable participant_ids length")
        if self.participant_count < 0:
            raise ValueError("participant_count cannot be negative")
        if self.dtarget < 0 or self.dtransfer < 0 or self.dparticipant < 0:
            raise ValueError("Distribution amounts cannot be negative")
        if self.dtransfer != self.dtotal - self.dtarget:
            raise ValueError("dtransfer must equal dtotal - dtarget")

    @property
    def n(self) -> int:
        return self.participant_count

    def __lt__(self, other: Any) -> bool:
        _forbid_ordering("DistributionTransactionPlan", "<")

    def __le__(self, other: Any) -> bool:
        _forbid_ordering("DistributionTransactionPlan", "<=")

    def __gt__(self, other: Any) -> bool:
        _forbid_ordering("DistributionTransactionPlan", ">")

    def __ge__(self, other: Any) -> bool:
        _forbid_ordering("DistributionTransactionPlan", ">=")


DamagePartitionPlan = NoPartitionPlan | DamageShareTransactionPlan | DistributionTransactionPlan


class DamagePartitionCoordinator:
    """Read-only Stage9 partition arbitrator and immutable plan builder.

    It owns state reads, eligibility, precedence, transaction identity, and exact
    integerization only. It never calculates damage, settles damage, mutates troops,
    writes state, or finalizes battle.
    """

    def __init__(self, state_runtime: Stage9StateRuntime) -> None:
        if not isinstance(state_runtime, Stage9StateRuntime):
            raise TypeError(
                f"state_runtime must be Stage9StateRuntime, got {type(state_runtime)}"
            )
        self._state_runtime = state_runtime

    @property
    def state_runtime(self) -> Stage9StateRuntime:
        return self._state_runtime

    def plan(
        self,
        context: BattleContext,
        damage_instance_id: DamageInstanceId,
        damage_result: DamageResult,
    ) -> DamagePartitionPlan:
        if not isinstance(context, BattleContext):
            raise TypeError(f"context must be BattleContext, got {type(context)}")
        if not isinstance(damage_instance_id, DamageInstanceId):
            raise TypeError(
                f"damage_instance_id must be DamageInstanceId, got {type(damage_instance_id)}"
            )
        if not isinstance(damage_result, DamageResult):
            raise TypeError(f"damage_result must be DamageResult, got {type(damage_result)}")
        if damage_result.prevented:
            raise ValueError("Prevented DamageResult must not enter partition planning")

        dtotal = damage_result.final_damage
        if isinstance(dtotal, bool) or not isinstance(dtotal, int) or dtotal < 0:
            raise ValueError("DamageResult.final_damage must be a non-negative int")
        target_id = damage_result.target_id

        # Frozen precedence: DAMAGE_SHARE > DISTRIBUTION. A legal zero Dtotal still
        # reaches these live reads and can produce a real transaction identity.
        share = self._state_runtime.get_operational_damage_share(context, target_id)
        if share is not None:
            params = share.runtime_params
            assert isinstance(params, DamageShareStateParams)
            self._validate_partition_ratio(params.ratio, "DamageShare")
            tx_id = context.id_allocator.allocate_partition_transaction_id()
            dsharer = round_half_up_product_int_ratio(dtotal, params.ratio)
            dtarget = dtotal - dsharer
            return DamageShareTransactionPlan(
                partition_transaction_id=tx_id,
                parent_damage_instance_id=damage_instance_id,
                target_id=target_id,
                sharer_id=params.sharer_id,
                dtotal=dtotal,
                ratio=params.ratio,
                dsharer_theoretical=dsharer,
                dtarget=dtarget,
            )

        distribution = self._state_runtime.get_operational_distribution(context, target_id)
        if distribution is not None:
            params = distribution.runtime_params
            assert isinstance(params, DistributionStateParams)
            self._validate_partition_ratio(params.ratio, "Distribution")
            tx_id = context.id_allocator.allocate_partition_transaction_id()
            participant_ids = self._distribution_participant_ids(context, target_id)
            n = len(participant_ids)
            if n == 0:
                dtarget = dtotal
                dtransfer = 0
                dparticipant = 0
            else:
                retained_ratio = ExactRatio(
                    params.ratio.denominator - params.ratio.numerator,
                    params.ratio.denominator,
                )
                dtarget = round_half_up_product_int_ratio(dtotal, retained_ratio)
                dtransfer = dtotal - dtarget
                dparticipant = round_half_up_divide_int(dtransfer, n)
            return DistributionTransactionPlan(
                partition_transaction_id=tx_id,
                parent_damage_instance_id=damage_instance_id,
                target_id=target_id,
                participant_ids=participant_ids,
                participant_count=n,
                dtotal=dtotal,
                ratio=params.ratio,
                dtarget=dtarget,
                dtransfer=dtransfer,
                dparticipant=dparticipant,
            )

        return NoPartitionPlan(
            parent_damage_instance_id=damage_instance_id,
            target_id=target_id,
            dtotal=dtotal,
        )

    @staticmethod
    def _validate_partition_ratio(ratio: ExactRatio, mechanism: str) -> None:
        if not isinstance(ratio, ExactRatio):
            raise TypeError(f"{mechanism} ratio must be ExactRatio")
        if ratio.numerator < 0 or ratio.numerator > ratio.denominator:
            raise ValueError(f"{mechanism} ratio must be within [0, 1]")

    @staticmethod
    def _distribution_participant_ids(
        context: BattleContext,
        target_id: str,
    ) -> tuple[str, ...]:
        target = context.get_unit(target_id)
        participants = [
            unit
            for unit in context.units.values()
            if unit.team_id == target.team_id
            and unit.unit_id != target_id
            and unit.is_alive
        ]
        # Global lineup slot is the frozen gameplay comparator.
        participants.sort(key=lambda unit: unit.lineup_position)
        return tuple(unit.unit_id for unit in participants)

    @staticmethod
    def participant_is_jit_valid(
        context: BattleContext,
        plan: DistributionTransactionPlan,
        participant_id: str,
    ) -> bool:
        if participant_id not in plan.participant_ids:
            raise ValueError(
                f"participant '{participant_id}' is not part of the immutable Distribution plan"
            )
        target = context.get_unit(plan.target_id)
        participant = context.get_unit(participant_id)
        return (
            participant.unit_id != target.unit_id
            and participant.team_id == target.team_id
            and participant.is_alive
        )
