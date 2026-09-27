from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable

from .dependency_evaluation import DependencyEvaluationSupport, ProviderNode, _EvaluationSession
from .provider_identity import (
    EquipmentProviderRef,
    ProviderRef,
    ProviderResolutionStatus,
    SkillProviderRef,
)
from .state_effectiveness import SuppressionCause


class ProviderValidityStatus(str, Enum):
    VALID = "VALID"
    SUPPRESSED = "SUPPRESSED"
    BASELINE_DISABLED = "BASELINE_DISABLED"
    MISSING = "MISSING"
    IDENTITY_MISMATCH = "IDENTITY_MISMATCH"


@dataclass(frozen=True, slots=True)
class ProviderValidityDecision:
    provider_ref: ProviderRef
    status: ProviderValidityStatus
    suppression_causes: tuple[SuppressionCause, ...] = ()

    @property
    def valid(self) -> bool:
        return self.status is ProviderValidityStatus.VALID


@dataclass(frozen=True, slots=True)
class ProviderDependency:
    provider_ref: ProviderRef
    rule_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.provider_ref, (SkillProviderRef, EquipmentProviderRef)):
            raise TypeError("provider_ref must be a typed ProviderRef")
        if not isinstance(self.rule_id, str) or not self.rule_id.strip():
            raise ValueError("rule_id cannot be empty or whitespace")


ProviderSuppressionRuleAdapter = Callable[
    [object, ProviderRef, _EvaluationSession],
    tuple[SuppressionCause, ...],
]


class ProviderValidityPolicy:
    """Canonical production truth for current Provider validity."""

    __slots__ = ("_dependencies", "_rule_adapters", "_equipment_resolver")

    def __init__(
        self,
        dependencies: DependencyEvaluationSupport,
        *,
        equipment_resolver=None,
    ) -> None:
        if not isinstance(dependencies, DependencyEvaluationSupport):
            raise TypeError("dependencies must be DependencyEvaluationSupport")
        self._dependencies = dependencies
        self._rule_adapters: list[ProviderSuppressionRuleAdapter] = []
        self._equipment_resolver = equipment_resolver

    @property
    def dependency_support(self) -> DependencyEvaluationSupport:
        return self._dependencies

    def register_rule_adapter(self, adapter: ProviderSuppressionRuleAdapter) -> None:
        if not callable(adapter):
            raise TypeError("adapter must be callable")
        if adapter in self._rule_adapters:
            return
        self._rule_adapters.append(adapter)

    @staticmethod
    def _decision(
        provider_ref: ProviderRef,
        status: ProviderValidityStatus,
        causes=(),
    ) -> ProviderValidityDecision:
        return ProviderValidityDecision(
            provider_ref=provider_ref,
            status=status,
            suppression_causes=tuple(sorted(set(causes), key=repr)),
        )

    def evaluate_node(
        self,
        context,
        node,
        session: _EvaluationSession,
    ) -> ProviderValidityDecision:
        if not isinstance(node, ProviderNode):
            raise TypeError("ProviderValidityPolicy can only evaluate ProviderNode")
        provider_ref = node.provider_ref

        if isinstance(provider_ref, SkillProviderRef):
            resolution = context.skill_runtimes.resolve_provider(provider_ref)
            if resolution.status is ProviderResolutionStatus.MISSING:
                return self._decision(provider_ref, ProviderValidityStatus.MISSING)
            if resolution.status is ProviderResolutionStatus.IDENTITY_MISMATCH:
                return self._decision(provider_ref, ProviderValidityStatus.IDENTITY_MISMATCH)
            runtime = resolution.runtime
            assert runtime is not None
            if not runtime.enabled:
                return self._decision(provider_ref, ProviderValidityStatus.BASELINE_DISABLED)
        elif isinstance(provider_ref, EquipmentProviderRef):
            if self._equipment_resolver is None:
                return self._decision(provider_ref, ProviderValidityStatus.MISSING)
            equipment = self._equipment_resolver(context, provider_ref)
            if equipment is None:
                return self._decision(provider_ref, ProviderValidityStatus.MISSING)
            if getattr(equipment, "enabled", True) is False:
                return self._decision(provider_ref, ProviderValidityStatus.BASELINE_DISABLED)
        else:
            raise TypeError("unsupported ProviderRef")

        suppression: list[SuppressionCause] = []
        for adapter in self._rule_adapters:
            suppression.extend(tuple(adapter(context, provider_ref, session)))

        if suppression:
            return self._decision(provider_ref, ProviderValidityStatus.SUPPRESSED, suppression)
        return self._decision(provider_ref, ProviderValidityStatus.VALID)

    def evaluate_provider(
        self,
        context,
        provider_ref: ProviderRef,
    ) -> ProviderValidityDecision:
        if not isinstance(provider_ref, (SkillProviderRef, EquipmentProviderRef)):
            raise TypeError("provider_ref must be a typed ProviderRef")
        return self._dependencies.evaluate(context, ProviderNode(provider_ref))
