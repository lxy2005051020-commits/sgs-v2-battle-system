"""One-shot shared treatment budget composed over existing scheduling/settlement owners.

Damage input is a projection of already-settled facts, never an EventBus handler
that triggers gameplay. PendingWork owns timing/rights; this adapter owns only
the treatment-family basis and allocation, not damage, troop mutation or RNG.
"""
from __future__ import annotations

from dataclasses import dataclass

from .context import BattleContext
from .additive_treatment_formula import AdditiveTreatmentFormulaSystem, AdditiveTreatmentFormulaResult
from .enums import BattlePhase
from .events import EventType
from .execution_right_runtime import ExecutionRightMode, ExecutionRightRequest, ExecutionRightSpec
from .operation_identity import OperationLineage, SourceType
from .pending_work import (
    PendingWork, PendingWorkDispatchResult, PendingWorkExecutionFrame,
    PendingWorkReadPolicy, PendingWorkScheduleSpec, PendingWorkSystem,
    PendingWorkValidityPolicy, ScheduleKind, SourceValidityMode, TargetValidityMode, WorkReadMode,
)
from .provider_identity import SkillProviderRef
from .recovery_system import RecoveryModifierPolicy, RecoveryRequest, RecoveryResolvedResult, RecoveryResult, RecoverySystem
from .recovery_capacity import recoverable_capacity
from .skill_runtime import SkillRuntime
from .stage10_state_params import RecoveryPotencyContext
from .stage9_integerization import ExactRatio
from .priority_target_system import PriorityTargetSystem
from .treatment_formula import TreatmentModifierSnapshot


@dataclass(frozen=True, slots=True)
class ScheduledTeamRecoverySpec:
    due_round: int
    first_damage_round: int
    last_damage_round: int
    potency: RecoveryPotencyContext
    damage_basis_ratio: ExactRatio = ExactRatio(0, 1)
    basis_model_key: str = "SETTLED_ENEMY_TEAM_LOSS"
    base_addition: ExactRatio = ExactRatio(0, 1)

    def __post_init__(self) -> None:
        for key in ("due_round", "first_damage_round", "last_damage_round"):
            value = getattr(self, key)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{key} must be int")
        if not 1 <= self.first_damage_round <= self.last_damage_round < self.due_round:
            raise ValueError("damage window must finish before the scheduled recovery round")
        if not isinstance(self.potency, RecoveryPotencyContext):
            raise TypeError("potency must be RecoveryPotencyContext")
        if self.potency.source_troops_at_application is None or self.potency.frozen_treatment_attribute() is None:
            raise ValueError("shared treatment requires complete frozen source inputs")
        if self.potency.treatment_amount or self.potency.ratio:
            raise ValueError("shared treatment requires the ordinary treatment-rate lane")
        if not isinstance(self.damage_basis_ratio, ExactRatio):
            raise TypeError("damage_basis_ratio must be ExactRatio")
        if self.damage_basis_ratio.numerator < 0:
            raise ValueError("damage_basis_ratio must be nonnegative")
        if not isinstance(self.base_addition, ExactRatio):
            raise TypeError("base_addition must be ExactRatio")
        if self.base_addition.numerator < 0:
            raise ValueError("base_addition must be nonnegative")
        if not isinstance(self.basis_model_key, str) or not self.basis_model_key.strip():
            raise ValueError("basis_model_key must be nonempty")


@dataclass(frozen=True, slots=True)
class SettledTeamLossBasis:
    actual_loss: int
    event_sequences: tuple[int, ...]


def project_settled_enemy_team_loss(
    context: BattleContext, *, team_id: str, first_round: int, last_round: int,
    after_sequence: int = 0,
) -> SettledTeamLossBasis:
    """Main-target loss plus Share/Distribution participants, each exactly once.

    DAMAGE_DEALT carries actual primary loss, not the pre-partition total.
    DIRECT_TROOP_LOSS carries participant actual loss. Other damage events and
    requested/theoretical values are deliberately excluded. Primary facts use
    the canonical event sequence; direct-loss facts additionally have loss IDs.
    """
    total = 0
    sequences = []
    seen = set()
    for event in context.event_bus.history:
        if event.sequence <= after_sequence or not first_round <= event.round_no <= last_round:
            continue
        if event.event_type not in (EventType.DAMAGE_DEALT, EventType.DIRECT_TROOP_LOSS):
            continue
        source = context.units.get(event.actor_id)
        target = context.units.get(event.target_id)
        if source is None or target is None or source.team_id == team_id or target.team_id != team_id:
            continue
        direct = event.event_type is EventType.DIRECT_TROOP_LOSS
        identity = (event.event_type, event.payload["direct_loss_id"] if direct else event.sequence)
        if identity in seen:
            continue
        amount = event.payload["actual_loss" if direct else "damage"]
        if isinstance(amount, bool) or not isinstance(amount, int):
            raise TypeError("settled damage facts require integer actual loss")
        if amount < 0:
            raise ValueError("settled damage facts require nonnegative actual loss")
        seen.add(identity)
        total += amount
        sequences.append(event.sequence)
    return SettledTeamLossBasis(total, tuple(sequences))


@dataclass(frozen=True, slots=True)
class SharedTeamRecoveryResult:
    loss_basis: SettledTeamLossBasis
    formula: AdditiveTreatmentFormulaResult
    allocations: tuple[RecoveryResult, ...]
    remaining_nominal: int


def _ratio_data(value: ExactRatio) -> tuple[int, int]:
    return value.numerator, value.denominator


class ScheduledTeamRecoverySupport:
    WORK_KIND = "SCHEDULED_TEAM_RECOVERY"

    def __init__(self, pending: PendingWorkSystem, formula: AdditiveTreatmentFormulaSystem,
                 recovery: RecoverySystem, targets: PriorityTargetSystem) -> None:
        self._pending = pending
        self._formula = formula
        self._recovery = recovery
        self._targets = targets
        pending.register_dispatcher(self.WORK_KIND, self._dispatch)

    def schedule(self, context: BattleContext, runtime: SkillRuntime,
                 spec: ScheduledTeamRecoverySpec) -> PendingWork:
        if not isinstance(spec, ScheduledTeamRecoverySpec):
            raise TypeError("spec must be ScheduledTeamRecoverySpec")
        if runtime.skill_slot is None:
            raise ValueError("scheduled treatment requires canonical provider slot")
        owner = context.get_unit(runtime.owner_id)
        potency = spec.potency
        mods = potency.treatment_modifier_snapshot
        snapshot = {
            "owner_id": owner.unit_id, "team_id": owner.team_id,
            "skill_id": runtime.definition.skill_id,
            "source_troops": potency.source_troops_at_application,
            "source_attribute": potency.frozen_treatment_attribute(), "rate": potency.base_rate,
            "base_addition": _ratio_data(spec.base_addition),
            "source_deltas": tuple(_ratio_data(x) for x in mods.source_side_deltas),
            "target_deltas": tuple(_ratio_data(x) for x in mods.target_side_deltas),
            "red_multiplier": _ratio_data(mods.red_pool_multiplier),
            "damage_ratio": _ratio_data(spec.damage_basis_ratio),
            "first_round": spec.first_damage_round, "last_round": spec.last_damage_round,
            "after_sequence": context.event_bus.history[-1].sequence if context.event_bus.history else 0,
            "basis_model_key": spec.basis_model_key,
        }
        return self._pending.create(context, work_kind=self.WORK_KIND,
            parent_lineage=OperationLineage(None, None, None, SourceType.ACTIVE_SKILL,
                physical_attacker=owner.unit_id, physical_skill=runtime.definition.skill_id,
                credit_owner=owner.unit_id),
            schedule_spec=PendingWorkScheduleSpec(ScheduleKind.SPECIFIC_ROUND_PHASE,
                phase=BattlePhase.ROUND_START, round_no=spec.due_round),
            execution_right_spec=ExecutionRightSpec(provider_validity=ExecutionRightMode.RECHECK_AT_EXECUTION),
            execution_right_request=ExecutionRightRequest(
                origin_provider=SkillProviderRef(owner.unit_id, runtime.skill_slot, runtime.definition.skill_id),
                historical_source_id=owner.unit_id),
            validity_policy=PendingWorkValidityPolicy(source=SourceValidityMode.SOURCE_MUST_BE_ALIVE,
                target=TargetValidityMode.IDENTITY_LOCKED),
            snapshot_payload=snapshot,
            read_policy=PendingWorkReadPolicy(tuple((key, WorkReadMode.SNAPSHOT_AT_CREATION) for key in snapshot)),
        )

    def _dispatch(self, context: BattleContext, frame: PendingWorkExecutionFrame) -> PendingWorkDispatchResult:
        data = frame.snapshot
        basis = project_settled_enemy_team_loss(context, team_id=data["team_id"],
            first_round=data["first_round"], last_round=data["last_round"],
            after_sequence=data["after_sequence"])
        damage_ratio = ExactRatio(*data["damage_ratio"])
        fixed = ExactRatio(*data["base_addition"])
        addition = ExactRatio(
            fixed.numerator * damage_ratio.denominator + basis.actual_loss * damage_ratio.numerator * fixed.denominator,
            fixed.denominator * damage_ratio.denominator,
        )
        formula = self._formula.calculate(rate=data["rate"], source_troops=data["source_troops"],
            source_attribute=data["source_attribute"], base_addition=addition,
            modifiers=TreatmentModifierSnapshot(
                source_side_deltas=tuple(ExactRatio(*x) for x in data["source_deltas"]),
                target_side_deltas=tuple(ExactRatio(*x) for x in data["target_deltas"]),
                red_pool_multiplier=ExactRatio(*data["red_multiplier"])))
        remaining = formula.nominal_recovery
        results = []
        owner = context.get_unit(data["owner_id"])
        # One priority snapshot, each target visited once. Capacity and healing
        # prevention stay authoritative in RecoverySystem/TroopSystem.
        for target in self._targets.lowest_troop_allies(context, owner):
            if remaining == 0:
                break
            if not target.is_alive:
                continue
            amount = min(remaining, recoverable_capacity(target))
            if amount == 0:
                continue
            result = self._recovery.resolve(context, RecoveryRequest(
                source_id=owner.unit_id, target_id=target.unit_id, amount=amount,
                source_skill_id=data["skill_id"], modifier_policy=RecoveryModifierPolicy.APPLY))
            results.append(result)
            # The shared budget is nominal. Recipient modifiers change actual
            # healing, never mint a second nominal pool. Prevention consumes none.
            if isinstance(result, RecoveryResolvedResult):
                remaining -= amount
        summary = SharedTeamRecoveryResult(basis, formula, tuple(results), remaining)
        context.event_bus.publish(event_type=EventType.RECOVERY_RESOLVED,
            phase=context.current_phase, round_no=context.current_round, actor_id=owner.unit_id,
            payload={"source_skill_id": data["skill_id"], "work_id": str(frame.work.work_id),
                "basis_model_key": data["basis_model_key"], "damage_basis": basis.actual_loss,
                "damage_event_sequences": basis.event_sequences, "damage_ratio": data["damage_ratio"],
                "source_troops": data["source_troops"], "source_attribute": data["source_attribute"],
                "troop_function_value": formula.troop_function_value,
                "base_addition": _ratio_data(formula.base_addition), "rate": data["rate"],
                "nominal_recovery": formula.nominal_recovery, "remaining_nominal": remaining,
                "target_order": tuple(result.request.target_id for result in results)})
        return PendingWorkDispatchResult(context.id_allocator.allocate_recovery_operation_id(), frame.lineage, summary)
