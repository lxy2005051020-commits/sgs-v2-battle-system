"""One-shot skill application bridge: PendingWork schedules, existing owners execute."""
from __future__ import annotations

from typing import Callable

from .context import BattleContext
from .dependency_evaluation import ProviderNode, StateNode
from .dependency_evaluation import DependencyEvaluationSupport
from .effect_executor import EffectExecutor
from .enums import BattlePhase
from .execution_right_runtime import ExecutionRightMode, ExecutionRightRequest, ExecutionRightSpec
from .operation_identity import OperationLineage, SourceType
from .pending_work import (
    PendingWorkDispatchResult, PendingWorkExecutionFrame, PendingWorkReadPolicy,
    PendingWorkScheduleSpec, PendingWorkValidityPolicy, ScheduleKind, SourceValidityMode,
    TargetValidityMode, WorkReadMode,
    PendingWorkSystem, PendingWork,
)
from .provider_identity import SkillProviderRef
from .skill_definition import SkillDefinition
from .skill_runtime import SkillRuntime, SkillSlot
from .skill_resolver import SkillResolver


class ScheduledSkillSupport:
    WORK_KIND = "SCHEDULED_SKILL_APPLICATION"

    def __init__(self, pending_work_system: PendingWorkSystem, skill_resolver: SkillResolver,
                 effect_executor: EffectExecutor, dependencies: DependencyEvaluationSupport,
                 definition_resolver: Callable[[BattleContext, str, str], SkillDefinition]):
        self._pending = pending_work_system
        self._resolver = skill_resolver
        self._executor = effect_executor
        self._dependencies = dependencies
        self._definition_resolver = definition_resolver
        self._pending.register_dispatcher(self.WORK_KIND, self._dispatch)

    def schedule(self, context: BattleContext, runtime: SkillRuntime, *, round_no: int = 1) -> PendingWork:
        if runtime.skill_slot is None:
            raise ValueError("scheduled skill requires canonical provider slot")
        ref = SkillProviderRef(runtime.owner_id, runtime.skill_slot, runtime.definition.skill_id)
        return self._pending.create(
            context, work_kind=self.WORK_KIND,
            parent_lineage=OperationLineage(None, None, None, SourceType.ACTIVE_SKILL,
                                           physical_attacker=runtime.owner_id,
                                           physical_skill=runtime.definition.skill_id, credit_owner=runtime.owner_id),
            schedule_spec=PendingWorkScheduleSpec(ScheduleKind.SPECIFIC_ROUND_PHASE,
                                                  phase=BattlePhase.ROUND_START, round_no=round_no),
            execution_right_spec=ExecutionRightSpec(provider_validity=ExecutionRightMode.RECHECK_AT_EXECUTION),
            execution_right_request=ExecutionRightRequest(origin_provider=ref,
                                                            historical_source_id=runtime.owner_id),
            validity_policy=PendingWorkValidityPolicy(source=SourceValidityMode.SOURCE_MUST_BE_ALIVE,
                                                      target=TargetValidityMode.IDENTITY_LOCKED),
            snapshot_payload={"skill_id": runtime.definition.skill_id, "owner_id": runtime.owner_id,
                              "slot": int(runtime.skill_slot)},
            read_policy=PendingWorkReadPolicy(tuple((key, WorkReadMode.SNAPSHOT_AT_CREATION)
                                                   for key in ("skill_id", "owner_id", "slot"))),
        )

    def _dispatch(self, context: BattleContext, frame: PendingWorkExecutionFrame) -> PendingWorkDispatchResult:
        data = frame.snapshot
        definition = self._definition_resolver(context, data["skill_id"], data["owner_id"])
        if definition.skill_id != data["skill_id"]:
            raise ValueError("scheduled definition must preserve canonical skill identity")
        runtime = SkillRuntime(definition, data["owner_id"], SkillSlot(data["slot"]))
        resolution = self._resolver.resolve(context, runtime)
        ref = SkillProviderRef(runtime.owner_id, runtime.skill_slot, definition.skill_id)
        results = []
        for effect in resolution.effects:
            result = self._executor.execute(context, effect)
            instance = getattr(result, "state_instance", None)
            if instance is not None:
                self._dependencies.add_dependency(StateNode(instance.instance_id), ProviderNode(ref))
            results.append(result)
        return PendingWorkDispatchResult(context.id_allocator.allocate_effect_operation_id(),
                                         frame.lineage, tuple(results))
