from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, TypeAlias

from .dependency_evaluation import StateNode
from .state_instance import StateInstance


class RemovalOperation(str, Enum):
    ORDINARY_CLEANSE = "ORDINARY_CLEANSE"
    SPECIALIZED_CLEANSE = "SPECIALIZED_CLEANSE"
    SCRIPTED_GAMEPLAY_REMOVE = "SCRIPTED_GAMEPLAY_REMOVE"
    NATURAL_EXPIRY = "NATURAL_EXPIRY"
    OWNER_DEFEAT_CLEANUP = "OWNER_DEFEAT_CLEANUP"
    BATTLE_TEARDOWN = "BATTLE_TEARDOWN"


_INFRASTRUCTURE_REMOVALS = frozenset(
    {
        RemovalOperation.NATURAL_EXPIRY,
        RemovalOperation.OWNER_DEFEAT_CLEANUP,
        RemovalOperation.BATTLE_TEARDOWN,
    }
)


class RemovalDecisionStatus(str, Enum):
    ALLOW = "ALLOW"
    REJECT_CONTRACT_PROTECTED = "REJECT_CONTRACT_PROTECTED"
    REJECT_INVALID_OPERATION = "REJECT_INVALID_OPERATION"
    UNSUPPORTED_BOUNDARY = "UNSUPPORTED_BOUNDARY"


@dataclass(frozen=True, slots=True)
class RemovalDecision:
    status: RemovalDecisionStatus
    operation: RemovalOperation
    reason_rule_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.status, RemovalDecisionStatus):
            raise TypeError("status must be RemovalDecisionStatus")
        if not isinstance(self.operation, RemovalOperation):
            raise TypeError("operation must be RemovalOperation")
        if not isinstance(self.reason_rule_id, str) or not self.reason_rule_id.strip():
            raise ValueError("reason_rule_id cannot be empty or whitespace")

    @property
    def allowed(self) -> bool:
        return self.status is RemovalDecisionStatus.ALLOW


RemovalRuleAdapter: TypeAlias = Callable[
    [object, RemovalOperation, StateInstance],
    RemovalDecision | None,
]


class StateRemovalPolicy:
    """Pure gameplay removal eligibility policy.

    Infrastructure removals are lifecycle facts and intentionally bypass
    ordinary cleanse eligibility.
    """

    __slots__ = ("_rule_adapters",)

    def __init__(self) -> None:
        self._rule_adapters: list[RemovalRuleAdapter] = []

    def register_rule_adapter(self, adapter: RemovalRuleAdapter) -> None:
        if not callable(adapter):
            raise TypeError("adapter must be callable")
        if adapter not in self._rule_adapters:
            self._rule_adapters.append(adapter)

    def evaluate_removal(
        self,
        context,
        operation: RemovalOperation,
        state_instance: StateInstance,
    ) -> RemovalDecision:
        if not isinstance(operation, RemovalOperation):
            return RemovalDecision(
                RemovalDecisionStatus.REJECT_INVALID_OPERATION,
                RemovalOperation.SCRIPTED_GAMEPLAY_REMOVE,
                "SF_REMOVAL_INVALID_OPERATION",
            )
        if not isinstance(state_instance, StateInstance):
            raise TypeError("state_instance must be StateInstance")

        if operation in _INFRASTRUCTURE_REMOVALS:
            return RemovalDecision(
                RemovalDecisionStatus.ALLOW,
                operation,
                "SF_REMOVAL_INFRASTRUCTURE_ALLOW",
            )

        for adapter in self._rule_adapters:
            decision = adapter(context, operation, state_instance)
            if decision is None:
                continue
            if not isinstance(decision, RemovalDecision):
                raise TypeError("removal adapter returned invalid decision")
            if decision.operation is not operation:
                raise ValueError("removal adapter changed operation identity")
            return decision

        return RemovalDecision(
            RemovalDecisionStatus.UNSUPPORTED_BOUNDARY,
            operation,
            "SF_REMOVAL_UNSUPPORTED_GAMEPLAY_BOUNDARY",
        )


class StateRemovalResultStatus(str, Enum):
    REMOVED = "REMOVED"
    REJECTED = "REJECTED"
    UNSUPPORTED_BOUNDARY = "UNSUPPORTED_BOUNDARY"


@dataclass(frozen=True, slots=True)
class StateRemovalResult:
    status: StateRemovalResultStatus
    decision: RemovalDecision
    removed_instance: StateInstance | None = None


class StateRemovalCoordinator:
    """Non-writing gameplay removal orchestrator."""

    __slots__ = ("_policy", "_lifecycle", "_transition_coordinator")

    def __init__(self, *, policy: StateRemovalPolicy, lifecycle, transition_coordinator) -> None:
        if not isinstance(policy, StateRemovalPolicy):
            raise TypeError("policy must be StateRemovalPolicy")
        self._policy = policy
        self._lifecycle = lifecycle
        self._transition_coordinator = transition_coordinator

    def remove(
        self,
        context,
        *,
        operation: RemovalOperation,
        instance_id: str,
    ) -> StateRemovalResult:
        instance = context.states.get(instance_id)
        decision = self._policy.evaluate_removal(context, operation, instance)
        if decision.status is RemovalDecisionStatus.UNSUPPORTED_BOUNDARY:
            return StateRemovalResult(
                StateRemovalResultStatus.UNSUPPORTED_BOUNDARY,
                decision,
            )
        if not decision.allowed:
            return StateRemovalResult(StateRemovalResultStatus.REJECTED, decision)

        expected_generation = instance.current_generation_id
        before = self._transition_coordinator.capture(
            context, (StateNode(instance.instance_id),)
        )
        current = context.states.get(instance.instance_id)
        if current.current_generation_id != expected_generation:
            raise RuntimeError("removal precondition generation changed before commit")

        removed = self._lifecycle.remove(
            context,
            instance.instance_id,
            reason=operation.value,
        )
        self._transition_coordinator.complete_removed_nodes(
            context,
            before,
            (StateNode(removed.instance_id),),
        )
        return StateRemovalResult(
            StateRemovalResultStatus.REMOVED,
            decision,
            removed_instance=removed,
        )
