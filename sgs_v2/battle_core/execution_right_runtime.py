from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable

from .equipment_effectiveness import (
    EquipmentContributionDependency,
    EquipmentEffectivenessPolicy,
    EquipmentEffectivenessStatus,
)
from .provider_identity import ProviderRef, EquipmentProviderRef, SkillProviderRef
from .provider_validity import ProviderValidityPolicy, ProviderValidityStatus
from .state_effectiveness import StateEffectivenessPolicy, StateEffectivenessStatus


class ExecutionRightDimension(str, Enum):
    ACTOR_PERMISSION = "ACTOR_PERMISSION"
    PROVIDER_VALIDITY = "PROVIDER_VALIDITY"
    TARGET_ELIGIBILITY = "TARGET_ELIGIBILITY"
    EQUIPMENT_CONTRIBUTION = "EQUIPMENT_CONTRIBUTION"
    STATE_EFFECTIVENESS = "STATE_EFFECTIVENESS"


class ExecutionRightMode(str, Enum):
    SNAPSHOT_AT_ADMISSION = "SNAPSHOT_AT_ADMISSION"
    RECHECK_AT_EXECUTION = "RECHECK_AT_EXECUTION"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNSUPPORTED_BOUNDARY = "UNSUPPORTED_BOUNDARY"


@dataclass(frozen=True, slots=True)
class ExecutionRightSpec:
    actor_permission: ExecutionRightMode = ExecutionRightMode.NOT_APPLICABLE
    provider_validity: ExecutionRightMode = ExecutionRightMode.NOT_APPLICABLE
    target_eligibility: ExecutionRightMode = ExecutionRightMode.NOT_APPLICABLE
    equipment_contribution: ExecutionRightMode = ExecutionRightMode.NOT_APPLICABLE
    state_effectiveness: ExecutionRightMode = ExecutionRightMode.NOT_APPLICABLE

    def __post_init__(self) -> None:
        if any(
            not isinstance(value, ExecutionRightMode)
            for value in (
                self.actor_permission,
                self.provider_validity,
                self.target_eligibility,
                self.equipment_contribution,
                self.state_effectiveness,
            )
        ):
            raise TypeError("all dimensions must be ExecutionRightMode")

    def mode_for(self, dimension: ExecutionRightDimension) -> ExecutionRightMode:
        if not isinstance(dimension, ExecutionRightDimension):
            raise TypeError("dimension must be ExecutionRightDimension")
        return {
            ExecutionRightDimension.ACTOR_PERMISSION: self.actor_permission,
            ExecutionRightDimension.PROVIDER_VALIDITY: self.provider_validity,
            ExecutionRightDimension.TARGET_ELIGIBILITY: self.target_eligibility,
            ExecutionRightDimension.EQUIPMENT_CONTRIBUTION: self.equipment_contribution,
            ExecutionRightDimension.STATE_EFFECTIVENESS: self.state_effectiveness,
        }[dimension]


class CurrentActorPermissionStatus(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    UNSUPPORTED_BOUNDARY = "UNSUPPORTED_BOUNDARY"


@dataclass(frozen=True, slots=True)
class CurrentActorPermissionRequest:
    actor_id: str
    operation_kind: str

    def __post_init__(self) -> None:
        if not isinstance(self.actor_id, str) or not self.actor_id.strip():
            raise ValueError("actor_id cannot be empty or whitespace")
        if not isinstance(self.operation_kind, str) or not self.operation_kind.strip():
            raise ValueError("operation_kind cannot be empty or whitespace")


@dataclass(frozen=True, slots=True)
class CurrentActorPermissionDecision:
    request: CurrentActorPermissionRequest
    status: CurrentActorPermissionStatus
    blocker_keys: tuple[str, ...] = ()

    @property
    def allowed(self) -> bool:
        return self.status is CurrentActorPermissionStatus.ALLOW


CurrentActorPermissionAdapter = Callable[
    [object, CurrentActorPermissionRequest],
    CurrentActorPermissionDecision | None,
]


class CurrentActorPermissionPolicy:
    __slots__ = ("_adapters",)

    def __init__(self) -> None:
        self._adapters: list[CurrentActorPermissionAdapter] = []

    def register_rule_adapter(self, adapter: CurrentActorPermissionAdapter) -> None:
        if not callable(adapter):
            raise TypeError("adapter must be callable")
        if adapter not in self._adapters:
            self._adapters.append(adapter)

    def evaluate(self, context, request: CurrentActorPermissionRequest):
        if not isinstance(request, CurrentActorPermissionRequest):
            raise TypeError("request must be CurrentActorPermissionRequest")
        blockers: list[str] = []
        denied = False
        unsupported = False
        for adapter in self._adapters:
            decision = adapter(context, request)
            if decision is None:
                continue
            if not isinstance(decision, CurrentActorPermissionDecision):
                raise TypeError("actor adapter returned invalid decision")
            if decision.request != request:
                raise ValueError("actor adapter returned decision for another request")
            blockers.extend(decision.blocker_keys)
            denied = denied or decision.status is CurrentActorPermissionStatus.DENY
            unsupported = unsupported or (
                decision.status is CurrentActorPermissionStatus.UNSUPPORTED_BOUNDARY
            )
        status = CurrentActorPermissionStatus.ALLOW
        if unsupported:
            status = CurrentActorPermissionStatus.UNSUPPORTED_BOUNDARY
        elif denied:
            status = CurrentActorPermissionStatus.DENY
        return CurrentActorPermissionDecision(request, status, tuple(sorted(set(blockers))))


class ExecutionTargetEligibilityStatus(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    UNSUPPORTED_BOUNDARY = "UNSUPPORTED_BOUNDARY"


@dataclass(frozen=True, slots=True)
class ExecutionTargetEligibilityRequest:
    actor_id: str | None
    target_id: str
    operation_kind: str

    def __post_init__(self) -> None:
        if self.actor_id is not None and (
            not isinstance(self.actor_id, str) or not self.actor_id.strip()
        ):
            raise ValueError("actor_id must be None or non-empty")
        if not isinstance(self.target_id, str) or not self.target_id.strip():
            raise ValueError("target_id cannot be empty")
        if not isinstance(self.operation_kind, str) or not self.operation_kind.strip():
            raise ValueError("operation_kind cannot be empty")


@dataclass(frozen=True, slots=True)
class ExecutionTargetEligibilityDecision:
    request: ExecutionTargetEligibilityRequest
    status: ExecutionTargetEligibilityStatus
    blocker_keys: tuple[str, ...] = ()

    @property
    def allowed(self) -> bool:
        return self.status is ExecutionTargetEligibilityStatus.ALLOW


ExecutionTargetEligibilityAdapter = Callable[
    [object, ExecutionTargetEligibilityRequest],
    ExecutionTargetEligibilityDecision | None,
]


class ExecutionTargetEligibilityPolicy:
    __slots__ = ("_adapters",)

    def __init__(self) -> None:
        self._adapters: list[ExecutionTargetEligibilityAdapter] = []

    def register_rule_adapter(self, adapter: ExecutionTargetEligibilityAdapter) -> None:
        if not callable(adapter):
            raise TypeError("adapter must be callable")
        if adapter not in self._adapters:
            self._adapters.append(adapter)

    def evaluate(self, context, request: ExecutionTargetEligibilityRequest):
        if not isinstance(request, ExecutionTargetEligibilityRequest):
            raise TypeError("request must be ExecutionTargetEligibilityRequest")
        blockers: list[str] = []
        denied = False
        unsupported = False
        for adapter in self._adapters:
            decision = adapter(context, request)
            if decision is None:
                continue
            if not isinstance(decision, ExecutionTargetEligibilityDecision):
                raise TypeError("target adapter returned invalid decision")
            if decision.request != request:
                raise ValueError("target adapter returned decision for another request")
            blockers.extend(decision.blocker_keys)
            denied = denied or decision.status is ExecutionTargetEligibilityStatus.DENY
            unsupported = unsupported or (
                decision.status is ExecutionTargetEligibilityStatus.UNSUPPORTED_BOUNDARY
            )
        status = ExecutionTargetEligibilityStatus.ALLOW
        if unsupported:
            status = ExecutionTargetEligibilityStatus.UNSUPPORTED_BOUNDARY
        elif denied:
            status = ExecutionTargetEligibilityStatus.DENY
        return ExecutionTargetEligibilityDecision(request, status, tuple(sorted(set(blockers))))


@dataclass(frozen=True, slots=True)
class RecoveryExecutionPreventionRequest:
    source_id: str | None
    target_id: str
    modified_recovery: int


@dataclass(frozen=True, slots=True)
class RecoveryExecutionPreventionContribution:
    reason_key: str
    priority: int = 0
    unsupported_boundary: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.reason_key, str) or not self.reason_key.strip():
            raise ValueError("reason_key cannot be empty")
        if isinstance(self.priority, bool) or not isinstance(self.priority, int):
            raise TypeError("priority must be int")


class RecoveryExecutionPreventionStatus(str, Enum):
    ALLOW = "ALLOW"
    PREVENT = "PREVENT"
    UNSUPPORTED_BOUNDARY = "UNSUPPORTED_BOUNDARY"


@dataclass(frozen=True, slots=True)
class RecoveryExecutionPreventionDecision:
    request: RecoveryExecutionPreventionRequest
    status: RecoveryExecutionPreventionStatus
    causes: tuple[RecoveryExecutionPreventionContribution, ...] = ()


class RecoveryExecutionPreventionPolicy:
    __slots__ = ("_adapters",)

    def __init__(self) -> None:
        self._adapters = []

    def register_rule_adapter(self, adapter) -> None:
        if not callable(adapter):
            raise TypeError("adapter must be callable")
        if adapter not in self._adapters:
            self._adapters.append(adapter)

    def evaluate(self, context, request: RecoveryExecutionPreventionRequest):
        if not isinstance(request, RecoveryExecutionPreventionRequest):
            raise TypeError("request must be RecoveryExecutionPreventionRequest")
        causes = []
        for adapter in self._adapters:
            contribution = adapter(context, request)
            if contribution is None:
                continue
            if not isinstance(contribution, RecoveryExecutionPreventionContribution):
                raise TypeError("recovery prevention adapter returned invalid contribution")
            causes.append(contribution)
        ordered = tuple(sorted(causes, key=lambda item: (item.priority, item.reason_key)))
        if any(item.unsupported_boundary for item in ordered):
            status = RecoveryExecutionPreventionStatus.UNSUPPORTED_BOUNDARY
        elif ordered:
            status = RecoveryExecutionPreventionStatus.PREVENT
        else:
            status = RecoveryExecutionPreventionStatus.ALLOW
        return RecoveryExecutionPreventionDecision(request, status, ordered)


class ExecutionRightEvaluationStatus(str, Enum):
    ALLOW = "ALLOW"
    DENY_ACTOR = "DENY_ACTOR"
    DENY_PROVIDER = "DENY_PROVIDER"
    DENY_TARGET = "DENY_TARGET"
    DENY_EQUIPMENT = "DENY_EQUIPMENT"
    DENY_STATE = "DENY_STATE"
    UNSUPPORTED_BOUNDARY = "UNSUPPORTED_BOUNDARY"


@dataclass(frozen=True, slots=True)
class ExecutionRightRequest:
    current_actor_id: str | None = None
    origin_provider: ProviderRef | None = None
    target_id: str | None = None
    equipment_dependency: EquipmentContributionDependency | None = None
    state_instance_id: str | None = None
    actor_operation_kind: str = "GENERIC"
    target_operation_kind: str = "GENERIC"
    historical_source_id: str | None = None
    effect_holder_id: str | None = None
    damage_source_id: str | None = None
    credit_owner_id: str | None = None

    def __post_init__(self) -> None:
        if self.origin_provider is not None and not isinstance(
            self.origin_provider, (SkillProviderRef, EquipmentProviderRef)
        ):
            raise TypeError("origin_provider must be typed ProviderRef")
        if self.equipment_dependency is not None and not isinstance(
            self.equipment_dependency, EquipmentContributionDependency
        ):
            raise TypeError("equipment_dependency must be typed dependency")


@dataclass(frozen=True, slots=True)
class ExecutionRightDimensionDecision:
    dimension: ExecutionRightDimension
    mode: ExecutionRightMode
    result_key: str


@dataclass(frozen=True, slots=True)
class ExecutionRightEvaluation:
    status: ExecutionRightEvaluationStatus
    checked_dimensions: tuple[ExecutionRightDimension, ...] = ()
    decisions: tuple[ExecutionRightDimensionDecision, ...] = ()

    @property
    def allowed(self) -> bool:
        return self.status is ExecutionRightEvaluationStatus.ALLOW


class ExecutionRightSupport:
    __slots__ = ("_actor_policy","_provider_policy","_target_policy","_equipment_policy","_state_policy")

    def __init__(
        self,
        *,
        actor_policy: CurrentActorPermissionPolicy,
        provider_policy: ProviderValidityPolicy,
        target_policy: ExecutionTargetEligibilityPolicy,
        equipment_policy: EquipmentEffectivenessPolicy,
        state_policy: StateEffectivenessPolicy,
    ) -> None:
        self._actor_policy = actor_policy
        self._provider_policy = provider_policy
        self._target_policy = target_policy
        self._equipment_policy = equipment_policy
        self._state_policy = state_policy

    @property
    def actor_permission_policy(self): return self._actor_policy
    @property
    def provider_validity_policy(self): return self._provider_policy
    @property
    def target_eligibility_policy(self): return self._target_policy
    @property
    def equipment_effectiveness_policy(self): return self._equipment_policy
    @property
    def state_effectiveness_policy(self): return self._state_policy

    def evaluate(self, context, spec: ExecutionRightSpec, request: ExecutionRightRequest):
        if not isinstance(spec, ExecutionRightSpec):
            raise TypeError("spec must be ExecutionRightSpec")
        if not isinstance(request, ExecutionRightRequest):
            raise TypeError("request must be ExecutionRightRequest")
        checked=[]; decisions=[]
        def boundary(d,m,key):
            checked.append(d); decisions.append(ExecutionRightDimensionDecision(d,m,key))
            return ExecutionRightEvaluation(
                ExecutionRightEvaluationStatus.UNSUPPORTED_BOUNDARY,
                tuple(checked),tuple(decisions)
            )
        for d in ExecutionRightDimension:
            m=spec.mode_for(d)
            if m in (ExecutionRightMode.SNAPSHOT_AT_ADMISSION,ExecutionRightMode.NOT_APPLICABLE):
                continue
            if m is ExecutionRightMode.UNSUPPORTED_BOUNDARY:
                return boundary(d,m,"SPEC_UNSUPPORTED")
            if d is ExecutionRightDimension.ACTOR_PERMISSION:
                if request.current_actor_id is None: return boundary(d,m,"MISSING_CURRENT_ACTOR")
                r=self._actor_policy.evaluate(context,CurrentActorPermissionRequest(request.current_actor_id,request.actor_operation_kind))
                checked.append(d); decisions.append(ExecutionRightDimensionDecision(d,m,r.status.value))
                if r.status is CurrentActorPermissionStatus.UNSUPPORTED_BOUNDARY:
                    return ExecutionRightEvaluation(ExecutionRightEvaluationStatus.UNSUPPORTED_BOUNDARY,tuple(checked),tuple(decisions))
                if not r.allowed:
                    return ExecutionRightEvaluation(ExecutionRightEvaluationStatus.DENY_ACTOR,tuple(checked),tuple(decisions))
            elif d is ExecutionRightDimension.PROVIDER_VALIDITY:
                if request.origin_provider is None: return boundary(d,m,"MISSING_PROVIDER")
                r=self._provider_policy.evaluate_provider(context,request.origin_provider)
                checked.append(d); decisions.append(ExecutionRightDimensionDecision(d,m,r.status.value))
                if r.status is not ProviderValidityStatus.VALID:
                    return ExecutionRightEvaluation(ExecutionRightEvaluationStatus.DENY_PROVIDER,tuple(checked),tuple(decisions))
            elif d is ExecutionRightDimension.TARGET_ELIGIBILITY:
                if request.target_id is None: return boundary(d,m,"MISSING_TARGET")
                r=self._target_policy.evaluate(context,ExecutionTargetEligibilityRequest(request.current_actor_id,request.target_id,request.target_operation_kind))
                checked.append(d); decisions.append(ExecutionRightDimensionDecision(d,m,r.status.value))
                if r.status is ExecutionTargetEligibilityStatus.UNSUPPORTED_BOUNDARY:
                    return ExecutionRightEvaluation(ExecutionRightEvaluationStatus.UNSUPPORTED_BOUNDARY,tuple(checked),tuple(decisions))
                if not r.allowed:
                    return ExecutionRightEvaluation(ExecutionRightEvaluationStatus.DENY_TARGET,tuple(checked),tuple(decisions))
            elif d is ExecutionRightDimension.EQUIPMENT_CONTRIBUTION:
                if request.equipment_dependency is None: return boundary(d,m,"MISSING_EQUIPMENT_DEPENDENCY")
                r=self._equipment_policy.evaluate_contribution(context,request.equipment_dependency.contribution_ref)
                checked.append(d); decisions.append(ExecutionRightDimensionDecision(d,m,r.status.value))
                if r.status is EquipmentEffectivenessStatus.UNSUPPORTED_BOUNDARY:
                    return ExecutionRightEvaluation(ExecutionRightEvaluationStatus.UNSUPPORTED_BOUNDARY,tuple(checked),tuple(decisions))
                if not r.effective:
                    return ExecutionRightEvaluation(ExecutionRightEvaluationStatus.DENY_EQUIPMENT,tuple(checked),tuple(decisions))
            elif d is ExecutionRightDimension.STATE_EFFECTIVENESS:
                if request.state_instance_id is None: return boundary(d,m,"MISSING_STATE_INSTANCE")
                checked.append(d)
                if not context.states.has_instance(request.state_instance_id):
                    decisions.append(ExecutionRightDimensionDecision(d,m,"STATE_MISSING"))
                    return ExecutionRightEvaluation(ExecutionRightEvaluationStatus.DENY_STATE,tuple(checked),tuple(decisions))
                r=self._state_policy.evaluate_state(context,context.states.get(request.state_instance_id))
                decisions.append(ExecutionRightDimensionDecision(d,m,r.status.value))
                if r.status is not StateEffectivenessStatus.EFFECTIVE:
                    return ExecutionRightEvaluation(ExecutionRightEvaluationStatus.DENY_STATE,tuple(checked),tuple(decisions))
        return ExecutionRightEvaluation(ExecutionRightEvaluationStatus.ALLOW,tuple(checked),tuple(decisions))


class DamageWorkKind(str, Enum):
    NEW_ACTOR_DRIVEN_DAMAGE = "NEW_ACTOR_DRIVEN_DAMAGE"
    COUNTER_DAMAGE = "COUNTER_DAMAGE"
    ATTACHED_EXISTING_DOT = "ATTACHED_EXISTING_DOT"
    FREE_PROXY_DAMAGE = "FREE_PROXY_DAMAGE"
    ALREADY_CREATED_DAMAGE_REQUEST = "ALREADY_CREATED_DAMAGE_REQUEST"
    OTHER_BOUNDED = "OTHER_BOUNDED"


@dataclass(frozen=True, slots=True)
class DamageExecutionWork:
    work_kind: DamageWorkKind
    spec: ExecutionRightSpec
    request: ExecutionRightRequest


class DamageExecutionRightPort:
    __slots__ = ("_support",)

    def __init__(self, support: ExecutionRightSupport) -> None:
        if not isinstance(support, ExecutionRightSupport):
            raise TypeError("support must be ExecutionRightSupport")
        self._support=support

    @property
    def execution_right_support(self): return self._support

    def evaluate(self,context,work:DamageExecutionWork):
        if not isinstance(work,DamageExecutionWork):
            raise TypeError("work must be DamageExecutionWork")
        return self._support.evaluate(context,work.spec,work.request)
