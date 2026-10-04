"""Stage13-D1 scheduling only; gameplay remains in mechanism dispatch owners."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from enum import Enum
from math import isfinite
from types import MappingProxyType

from .enums import BattlePhase
from .execution_right_runtime import (
    ExecutionRightDimension, ExecutionRightMode, ExecutionRightRequest,
    ExecutionRightSpec, ExecutionRightSupport,
)
from .operation_identity import (
    PendingWorkId, OperationLineage, DamageInstanceId, EffectOperationId,
    RecoveryOperationId,
)


def _integer(value, name, minimum=1):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be int")
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")


def _key(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty str")


def freeze_payload(value):
    """Data-only deep freeze; mutable/opaque domain objects cannot leak through."""
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float and isfinite(value):
        return value
    if isinstance(value, Mapping):
        for key in value:
            _key(key, "payload key")
        return MappingProxyType({key: freeze_payload(item) for key, item in value.items()})
    if isinstance(value, (tuple, list)):
        return tuple(freeze_payload(item) for item in value)
    raise TypeError("payload must contain finite immutable data, not gameplay objects")


class PendingWorkStatus(str, Enum):
    PENDING = "PENDING"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class ScheduleKind(str, Enum):
    SPECIFIC_ROUND_PHASE = "SPECIFIC_ROUND_PHASE"
    NEXT_PHASE = "NEXT_PHASE"
    NEXT_ACTION_START = "NEXT_ACTION_START"
    FUTURE_TRIGGER = "FUTURE_TRIGGER"


_PHASES = (BattlePhase.ROUND_START, BattlePhase.UNIT_ACTION_START, BattlePhase.ROUND_END)
_PHASE_RANK = {phase.value: index for index, phase in enumerate(BattlePhase)}


@dataclass(frozen=True, slots=True)
class PendingWorkScheduleSpec:
    kind: ScheduleKind
    phase: BattlePhase | None = None
    round_no: int | None = None
    actor_id: str | None = None
    trigger_key: str | None = None

    def __post_init__(self):
        if not isinstance(self.kind, ScheduleKind):
            raise TypeError("kind must be ScheduleKind")
        if self.kind is ScheduleKind.FUTURE_TRIGGER:
            _key(self.trigger_key, "trigger_key")
            if any(item is not None for item in (self.phase, self.round_no, self.actor_id)):
                raise ValueError("trigger schedule cannot carry phase/round/actor")
            return
        if self.phase not in _PHASES or not isinstance(self.phase, BattlePhase):
            raise ValueError("schedule phase must be a supported BattlePhase")
        if self.trigger_key is not None:
            raise ValueError("phase schedule cannot carry trigger_key")
        if self.phase is BattlePhase.UNIT_ACTION_START:
            _key(self.actor_id, "actor_id")
        elif self.actor_id is not None:
            raise ValueError("actor_id requires action-start phase")
        if self.kind is ScheduleKind.NEXT_ACTION_START and self.phase is not BattlePhase.UNIT_ACTION_START:
            raise ValueError("NEXT_ACTION_START requires UNIT_ACTION_START")
        if self.kind is ScheduleKind.SPECIFIC_ROUND_PHASE:
            _integer(self.round_no, "round_no")
        elif self.round_no is not None:
            raise ValueError("only specific schedule carries round_no")


class WorkLifetimeKind(str, Enum):
    ONE_SHOT = "ONE_SHOT"
    UNTIL_EXECUTED = "UNTIL_EXECUTED"
    UNTIL_ROUND = "UNTIL_ROUND"
    REPEAT_N_TIMES = "REPEAT_N_TIMES"  # RESERVED; fail closed, never pretend supported


@dataclass(frozen=True, slots=True)
class WorkLifetimeSpec:
    kind: WorkLifetimeKind = WorkLifetimeKind.ONE_SHOT
    until_round: int | None = None

    def __post_init__(self):
        if not isinstance(self.kind, WorkLifetimeKind):
            raise TypeError("kind must be WorkLifetimeKind")
        if self.kind is WorkLifetimeKind.REPEAT_N_TIMES:
            raise NotImplementedError("REPEAT_N_TIMES is a reserved D1 extension seam")
        if self.kind is WorkLifetimeKind.UNTIL_ROUND:
            _integer(self.until_round, "until_round")
        elif self.until_round is not None:
            raise ValueError("until_round requires UNTIL_ROUND")


class SourceValidityMode(str, Enum):
    SOURCE_INDEPENDENT_AFTER_CREATION = "SOURCE_INDEPENDENT_AFTER_CREATION"
    SOURCE_MUST_BE_ALIVE = "SOURCE_MUST_BE_ALIVE"


class TargetValidityMode(str, Enum):
    IDENTITY_LOCKED = "IDENTITY_LOCKED"
    TARGET_MUST_REMAIN_ALIVE = "TARGET_MUST_REMAIN_ALIVE"


@dataclass(frozen=True, slots=True)
class PendingWorkValidityPolicy:
    source: SourceValidityMode = SourceValidityMode.SOURCE_INDEPENDENT_AFTER_CREATION
    target: TargetValidityMode = TargetValidityMode.TARGET_MUST_REMAIN_ALIVE

    def __post_init__(self):
        if not isinstance(self.source, SourceValidityMode) or not isinstance(self.target, TargetValidityMode):
            raise TypeError("validity modes must be typed")


class WorkReadMode(str, Enum):
    SNAPSHOT_AT_CREATION = "SNAPSHOT_AT_CREATION"
    LIVE_AT_EXECUTION = "LIVE_AT_EXECUTION"


@dataclass(frozen=True, slots=True)
class PendingWorkReadPolicy:
    dimensions: tuple[tuple[str, WorkReadMode], ...] = ()

    def __post_init__(self):
        object.__setattr__(self, "dimensions", tuple(tuple(item) for item in self.dimensions))
        keys = []
        for key, mode in self.dimensions:
            _key(key, "dimension")
            if not isinstance(mode, WorkReadMode):
                raise TypeError("read mode must be WorkReadMode")
            keys.append(key)
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate read dimension")


@dataclass(frozen=True, slots=True)
class PendingWorkTimingPoint:
    round_no: int
    phase: BattlePhase
    actor_id: str | None = None
    trigger_key: str | None = None
    occurrence: int = 0

    def __post_init__(self):
        _integer(self.round_no, "round_no")
        _integer(self.occurrence, "occurrence", 0)
        if not isinstance(self.phase, BattlePhase):
            raise TypeError("phase must be BattlePhase")
        if self.trigger_key is not None:
            _key(self.trigger_key, "trigger_key")
            if self.actor_id is not None or self.occurrence < 1:
                raise ValueError("trigger needs positive occurrence and no actor")
        elif self.phase not in _PHASES:
            raise ValueError("unsupported engine timing phase")
        elif self.phase is BattlePhase.UNIT_ACTION_START:
            _key(self.actor_id, "actor_id")
        elif self.actor_id is not None:
            raise ValueError("actor requires action-start")


@dataclass(frozen=True, slots=True)
class PendingWork:
    work_id: PendingWorkId
    creation_sequence: int
    work_kind: str
    parent_lineage: OperationLineage
    created_round: int
    created_phase: str
    schedule_spec: PendingWorkScheduleSpec
    lifetime_spec: WorkLifetimeSpec
    execution_right_spec: ExecutionRightSpec
    execution_right_request: ExecutionRightRequest
    validity_policy: PendingWorkValidityPolicy
    snapshot_payload: Mapping
    read_policy: PendingWorkReadPolicy
    earliest_round: int
    status: PendingWorkStatus = PendingWorkStatus.PENDING
    terminal_reason: str | None = None

    @property
    def source_ref(self):
        return self.execution_right_request.historical_source_id

    @property
    def provider_ref(self):
        return self.execution_right_request.origin_provider

    @property
    def target_ref(self):
        return self.execution_right_request.target_id


@dataclass(frozen=True, slots=True)
class PendingWorkExecutionFrame:
    work: PendingWork
    lineage: OperationLineage
    snapshot: Mapping
    live: Mapping


@dataclass(frozen=True, slots=True)
class PendingWorkDispatchResult:
    operation_id: DamageInstanceId | EffectOperationId | RecoveryOperationId
    lineage: OperationLineage
    result: object = field(default=None, compare=False)

    def __post_init__(self):
        if not isinstance(self.operation_id, (DamageInstanceId, EffectOperationId, RecoveryOperationId)):
            raise TypeError("dispatch must return a typed child operation")
        if not isinstance(self.lineage, OperationLineage):
            raise TypeError("dispatch must return OperationLineage")


@dataclass(frozen=True, slots=True)
class PendingWorkTrace:
    work_id: PendingWorkId
    status: PendingWorkStatus
    round_no: int
    phase: str
    reason: str
    lineage: OperationLineage
    operation_id: DamageInstanceId | EffectOperationId | RecoveryOperationId | None = None


class PendingWorkRegistry:
    """Per-context storage only. Immutable snapshots, explicit sequence order."""

    def __init__(self):
        self._records = {}
        self._trace = []
        self._sequence = 0
        self._owner = None

    def get(self, work_id: PendingWorkId) -> PendingWork:
        if not isinstance(work_id, PendingWorkId):
            raise TypeError("work_id must be PendingWorkId")
        return self._records[work_id]

    def all(self) -> tuple[PendingWork, ...]:
        return tuple(sorted(self._records.values(), key=lambda work: work.creation_sequence))

    @property
    def trace(self) -> tuple[PendingWorkTrace, ...]:
        return tuple(self._trace)


class PendingWorkSystem:
    """Sole lifecycle/dispatch owner; no formulas, troop writes or PRNG."""

    def __init__(self, execution_right_support: ExecutionRightSupport, future_admission_gate):
        self._rights = execution_right_support
        self._gate = future_admission_gate
        self._context = None
        self._dispatchers = {}
        self._live_readers = {}
        self._seen_points = set()
        self._last_clock = None
        self._dispatching = False

    def _registry(self, context):
        if self._context is not None and self._context is not context:
            raise ValueError("PendingWorkSystem is battle-scoped")
        coordinator_context = getattr(self._gate.coordinator, "owning_context", None)
        if coordinator_context is not None and coordinator_context is not context:
            raise ValueError("finalization owner belongs to another battle")
        registry = context.pending_work
        if registry._owner is not None and registry._owner is not self:
            raise ValueError("registry already has its canonical owner")
        self._context = context
        registry._owner = self
        return registry

    def register_dispatcher(self, work_kind: str, dispatcher: Callable):
        _key(work_kind, "work_kind")
        if not callable(dispatcher):
            raise TypeError("dispatcher must be callable")
        if work_kind in self._dispatchers:
            raise ValueError("dispatcher already registered")
        self._dispatchers[work_kind] = dispatcher

    def register_live_reader(self, dimension: str, reader: Callable):
        _key(dimension, "dimension")
        if not callable(reader):
            raise TypeError("reader must be callable")
        if dimension in self._live_readers:
            raise ValueError("reader already registered")
        self._live_readers[dimension] = reader

    def _open(self, context):
        return not context.ended and self._gate.can_admit_pending_work()

    def create(self, context, *, work_kind: str, parent_lineage: OperationLineage,
               schedule_spec: PendingWorkScheduleSpec,
               execution_right_request: ExecutionRightRequest,
               lifetime_spec: WorkLifetimeSpec = WorkLifetimeSpec(),
               execution_right_spec: ExecutionRightSpec = ExecutionRightSpec(),
               validity_policy: PendingWorkValidityPolicy = PendingWorkValidityPolicy(),
               snapshot_payload: Mapping | None = None,
               read_policy: PendingWorkReadPolicy = PendingWorkReadPolicy()) -> PendingWork:
        registry = self._registry(context)
        for value, expected in (
            (parent_lineage, OperationLineage), (schedule_spec, PendingWorkScheduleSpec),
            (execution_right_request, ExecutionRightRequest), (lifetime_spec, WorkLifetimeSpec),
            (execution_right_spec, ExecutionRightSpec), (validity_policy, PendingWorkValidityPolicy),
            (read_policy, PendingWorkReadPolicy),
        ):
            if not isinstance(value, expected):
                raise TypeError(f"expected {expected.__name__}")
        if not self._open(context):
            raise RuntimeError("future work admission closed")
        if work_kind not in self._dispatchers:
            raise ValueError("no dispatcher for work kind")
        snapshot = freeze_payload({} if snapshot_payload is None else snapshot_payload)
        if not isinstance(snapshot, Mapping):
            raise TypeError("snapshot payload must be a mapping")
        declared_snapshot = {key for key, mode in read_policy.dimensions if mode is WorkReadMode.SNAPSHOT_AT_CREATION}
        if set(snapshot) != declared_snapshot:
            raise ValueError("snapshot keys must exactly match declared snapshot dimensions")
        for key, mode in read_policy.dimensions:
            if mode is WorkReadMode.LIVE_AT_EXECUTION and key not in self._live_readers:
                raise ValueError(f"no live reader for {key}")
        if validity_policy.source is SourceValidityMode.SOURCE_MUST_BE_ALIVE:
            _key(execution_right_request.historical_source_id, "required source")
        if validity_policy.target is TargetValidityMode.TARGET_MUST_REMAIN_ALIVE:
            _key(execution_right_request.target_id, "required target")
        # SNAPSHOT_AT_ADMISSION must be proven now; live dimensions also preflight.
        admission_spec = ExecutionRightSpec(**{
            dimension.value.lower(): (
                ExecutionRightMode.RECHECK_AT_EXECUTION
                if execution_right_spec.mode_for(dimension) is ExecutionRightMode.SNAPSHOT_AT_ADMISSION
                else execution_right_spec.mode_for(dimension)
            ) for dimension in ExecutionRightDimension
        })
        decision = self._rights.evaluate(context, admission_spec, execution_right_request)
        if not decision.allowed:
            raise ValueError(f"creation execution right denied: {decision.status.value}")
        earliest = max(1, context.current_round)
        if schedule_spec.phase is not None:
            current_rank = _PHASE_RANK.get(context.current_phase, -1)
            schedule_rank = _PHASE_RANK[schedule_spec.phase.value]
            past = schedule_rank < current_rank
            if schedule_spec.phase is BattlePhase.UNIT_ACTION_START:
                past = past or context.action_progress.has_consumed_action_start(schedule_spec.actor_id, context.current_round)
            else:
                past = past or schedule_rank == current_rank
            if past:
                earliest = context.current_round + 1
        if schedule_spec.round_no is not None and schedule_spec.round_no < earliest:
            raise ValueError("specific timing point is not in the future")
        if lifetime_spec.until_round is not None and lifetime_spec.until_round < earliest:
            raise ValueError("lifetime already elapsed")
        if not self._open(context):
            raise RuntimeError("future work admission closed during preflight")
        registry._sequence += 1
        work = PendingWork(
            context.id_allocator.allocate_pending_work_id(), registry._sequence, work_kind,
            parent_lineage, context.current_round, context.current_phase, schedule_spec,
            lifetime_spec, execution_right_spec, execution_right_request, validity_policy,
            snapshot, read_policy, earliest,
        )
        registry._records[work.work_id] = work
        self._trace(context, work, "CREATED")
        return work

    def _trace(self, context, work, reason, operation_id=None, lineage=None):
        context.pending_work._trace.append(PendingWorkTrace(
            work.work_id, work.status, context.current_round, context.current_phase,
            reason, lineage or work.parent_lineage, operation_id,
        ))

    def _transition(self, context, work_id, status, reason):
        registry = self._registry(context)
        work = registry.get(work_id)
        allowed = {
            PendingWorkStatus.PENDING: (PendingWorkStatus.EXECUTING, PendingWorkStatus.CANCELLED, PendingWorkStatus.EXPIRED),
            PendingWorkStatus.EXECUTING: (PendingWorkStatus.COMPLETED, PendingWorkStatus.CANCELLED),
        }
        if status not in allowed.get(work.status, ()):
            raise ValueError(f"illegal work transition {work.status.value} -> {status.value}")
        terminal = status in (PendingWorkStatus.COMPLETED, PendingWorkStatus.CANCELLED, PendingWorkStatus.EXPIRED)
        work = replace(work, status=status, terminal_reason=reason if terminal else None)
        registry._records[work_id] = work
        self._trace(context, work, reason)
        return work

    def cancel(self, context, work_id: PendingWorkId, reason: str = "EXPLICIT_CANCEL"):
        _key(reason, "reason")
        work = self._registry(context).get(work_id)
        if work.status is not PendingWorkStatus.PENDING:
            raise ValueError("only pending work can be explicitly cancelled")
        return self._transition(context, work_id, PendingWorkStatus.CANCELLED, reason)

    def cancel_future(self, context):
        for work in self._registry(context).all():
            if work.status is PendingWorkStatus.PENDING:
                self.cancel(context, work.work_id, "BATTLE_ADMISSION_CLOSED")

    @staticmethod
    def _alive(context, unit_id):
        return unit_id in context.units and context.units[unit_id].is_alive

    def _invalid_reason(self, context, work):
        if work.validity_policy.source is SourceValidityMode.SOURCE_MUST_BE_ALIVE and not self._alive(context, work.source_ref):
            return "SOURCE_INVALID"
        if work.validity_policy.target is TargetValidityMode.TARGET_MUST_REMAIN_ALIVE and not self._alive(context, work.target_ref):
            return "TARGET_INVALID"
        decision = self._rights.evaluate(context, work.execution_right_spec, work.execution_right_request)
        return None if decision.allowed else decision.status.value

    @staticmethod
    def _matches(work, point):
        spec = work.schedule_spec
        if point.round_no < work.earliest_round:
            return False
        if spec.kind is ScheduleKind.FUTURE_TRIGGER:
            return point.trigger_key == spec.trigger_key
        return (point.trigger_key is None and point.phase is spec.phase
                and point.actor_id == spec.actor_id
                and (spec.round_no is None or point.round_no == spec.round_no))

    @staticmethod
    def _expired(work, point):
        deadline = work.lifetime_spec.until_round
        if deadline is not None and point.round_no > deadline:
            return True
        spec = work.schedule_spec
        if spec.round_no is None:
            return False
        return (point.round_no > spec.round_no or (
            point.round_no == spec.round_no and _PHASE_RANK[point.phase.value] > _PHASE_RANK[spec.phase.value]
        ))

    def process(self, context, point: PendingWorkTimingPoint) -> tuple[PendingWorkDispatchResult, ...]:
        registry = self._registry(context)
        if not isinstance(point, PendingWorkTimingPoint):
            raise TypeError("point must be PendingWorkTimingPoint")
        if self._dispatching:
            raise RuntimeError("reentrant pending work dispatch")
        if point.round_no != context.current_round or point.phase.value != context.current_phase:
            raise ValueError("timing point must match the live engine clock")
        if not self._open(context):
            self.cancel_future(context)
            return ()
        clock = (point.round_no, _PHASE_RANK[point.phase.value])
        if self._last_clock is not None and clock < self._last_clock:
            raise ValueError("pending work clock cannot move backwards")
        if point in self._seen_points:
            return ()
        self._last_clock = clock
        self._seen_points.add(point)
        due = []
        for work in registry.all():
            if work.status is not PendingWorkStatus.PENDING:
                continue
            if self._expired(work, point):
                self._transition(context, work.work_id, PendingWorkStatus.EXPIRED, "TIMING_ELAPSED")
            elif self._matches(work, point):
                due.append(work.work_id)
        results = []
        self._dispatching = True
        try:
            for work_id in due:
                work = registry.get(work_id)  # earlier dispatch may have cancelled it
                if work.status is not PendingWorkStatus.PENDING:
                    continue
                if not self._open(context):
                    self.cancel_future(context)
                    break
                reason = self._invalid_reason(context, work)
                if reason is not None:
                    self.cancel(context, work_id, reason)
                    continue
                if not self._open(context):
                    self.cancel_future(context)
                    break
                work = self._transition(context, work_id, PendingWorkStatus.EXECUTING, "DISPATCH_STARTED")
                try:
                    live = freeze_payload({key: self._live_readers[key](context, work)
                        for key, mode in work.read_policy.dimensions if mode is WorkReadMode.LIVE_AT_EXECUTION})
                    if not self._open(context):
                        self._transition(context, work_id, PendingWorkStatus.CANCELLED, "BATTLE_ADMISSION_CLOSED")
                        self.cancel_future(context)
                        break
                    lineage = replace(work.parent_lineage, parent_pending_work_id=work_id)
                    frame = PendingWorkExecutionFrame(work, lineage, work.snapshot_payload, live)
                    result = self._dispatchers[work.work_kind](context, frame)
                    if not isinstance(result, PendingWorkDispatchResult) or result.lineage != lineage:
                        raise TypeError("dispatcher must return matching child operation lineage")
                except Exception:
                    self._transition(context, work_id, PendingWorkStatus.CANCELLED, "DISPATCH_FAILED")
                    raise
                self._transition(context, work_id, PendingWorkStatus.COMPLETED, "DISPATCH_COMPLETED")
                self._trace(context, registry.get(work_id), "CHILD_OPERATION", result.operation_id, result.lineage)
                results.append(result)
            if not self._open(context):
                self.cancel_future(context)
        finally:
            self._dispatching = False
            if not self._open(context):
                self.cancel_future(context)
        return tuple(results)
