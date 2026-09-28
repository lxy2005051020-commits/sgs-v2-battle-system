from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable

from .provider_identity import EquipmentProviderRef
from .provider_validity import ProviderValidityPolicy, ProviderValidityStatus
from .state_effectiveness import SuppressionCause


class EquipmentContributionKind(str, Enum):
    ATTRIBUTE = "ATTRIBUTE"
    DAMAGE_MODIFIER = "DAMAGE_MODIFIER"
    RECOVERY_MODIFIER = "RECOVERY_MODIFIER"
    TRIGGER = "TRIGGER"
    SCHEDULED_TRIGGER = "SCHEDULED_TRIGGER"
    LIVE_EFFECT = "LIVE_EFFECT"


@dataclass(frozen=True, slots=True)
class EquipmentContributionRef:
    provider_ref: EquipmentProviderRef
    contribution_key: str
    kind: EquipmentContributionKind

    def __post_init__(self) -> None:
        if not isinstance(self.provider_ref, EquipmentProviderRef):
            raise TypeError("provider_ref must be an EquipmentProviderRef")
        if not isinstance(self.contribution_key, str) or not self.contribution_key.strip():
            raise ValueError("contribution_key cannot be empty or whitespace")
        if not isinstance(self.kind, EquipmentContributionKind):
            raise TypeError("kind must be an EquipmentContributionKind")


class EquipmentContributionResolutionStatus(str, Enum):
    FOUND = "FOUND"
    MISSING = "MISSING"
    IDENTITY_MISMATCH = "IDENTITY_MISMATCH"
    BASELINE_DISABLED = "BASELINE_DISABLED"


@dataclass(frozen=True, slots=True)
class EquipmentProviderRecord:
    provider_ref: EquipmentProviderRef
    enabled: bool = True
    payload: object | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.provider_ref, EquipmentProviderRef):
            raise TypeError("provider_ref must be an EquipmentProviderRef")
        if not isinstance(self.enabled, bool):
            raise TypeError("enabled must be bool")


@dataclass(frozen=True, slots=True)
class EquipmentContributionRecord:
    contribution_ref: EquipmentContributionRef
    baseline_enabled: bool = True
    payload: object | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.contribution_ref, EquipmentContributionRef):
            raise TypeError("contribution_ref must be an EquipmentContributionRef")
        if not isinstance(self.baseline_enabled, bool):
            raise TypeError("baseline_enabled must be bool")


@dataclass(frozen=True, slots=True)
class EquipmentContributionResolution:
    contribution_ref: EquipmentContributionRef
    status: EquipmentContributionResolutionStatus
    record: EquipmentContributionRecord | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.contribution_ref, EquipmentContributionRef):
            raise TypeError("contribution_ref must be an EquipmentContributionRef")
        if not isinstance(self.status, EquipmentContributionResolutionStatus):
            raise TypeError("status must be an EquipmentContributionResolutionStatus")
        if self.status in (
            EquipmentContributionResolutionStatus.FOUND,
            EquipmentContributionResolutionStatus.BASELINE_DISABLED,
        ):
            if not isinstance(self.record, EquipmentContributionRecord):
                raise TypeError("resolved contribution requires a record")
        elif self.record is not None:
            raise ValueError("unresolved contribution cannot carry a record")


class EquipmentContributionRegistry:
    __slots__ = ("_providers", "_contributions")

    def __init__(self) -> None:
        self._providers: dict[EquipmentProviderRef, EquipmentProviderRecord] = {}
        self._contributions: dict[EquipmentContributionRef, EquipmentContributionRecord] = {}

    def register_provider(
        self,
        provider_ref: EquipmentProviderRef,
        *,
        enabled: bool = True,
        payload: object | None = None,
    ) -> EquipmentProviderRecord:
        record = EquipmentProviderRecord(provider_ref, enabled, payload)
        existing = self._providers.get(provider_ref)
        if existing is not None and existing != record:
            raise ValueError(f"equipment provider already registered: {provider_ref!r}")
        self._providers[provider_ref] = record
        return record

    def register_contribution(
        self,
        contribution_ref: EquipmentContributionRef,
        *,
        baseline_enabled: bool = True,
        payload: object | None = None,
    ) -> EquipmentContributionRecord:
        if not isinstance(contribution_ref, EquipmentContributionRef):
            raise TypeError("contribution_ref must be an EquipmentContributionRef")
        if contribution_ref.provider_ref not in self._providers:
            raise KeyError(f"equipment provider is not registered: {contribution_ref.provider_ref!r}")
        record = EquipmentContributionRecord(contribution_ref, baseline_enabled, payload)
        existing = self._contributions.get(contribution_ref)
        if existing is not None and existing != record:
            raise ValueError(f"equipment contribution already registered: {contribution_ref!r}")
        self._contributions[contribution_ref] = record
        return record

    def resolve_provider(self, _context, provider_ref: EquipmentProviderRef):
        if not isinstance(provider_ref, EquipmentProviderRef):
            raise TypeError("provider_ref must be an EquipmentProviderRef")
        return self._providers.get(provider_ref)

    def resolve_contribution(
        self,
        contribution_ref: EquipmentContributionRef,
    ) -> EquipmentContributionResolution:
        if not isinstance(contribution_ref, EquipmentContributionRef):
            raise TypeError("contribution_ref must be an EquipmentContributionRef")
        record = self._contributions.get(contribution_ref)
        if record is not None:
            return EquipmentContributionResolution(
                contribution_ref,
                (
                    EquipmentContributionResolutionStatus.FOUND
                    if record.baseline_enabled
                    else EquipmentContributionResolutionStatus.BASELINE_DISABLED
                ),
                record,
            )
        for known_ref in self._contributions:
            if (
                known_ref.provider_ref == contribution_ref.provider_ref
                and known_ref.contribution_key == contribution_ref.contribution_key
            ):
                return EquipmentContributionResolution(
                    contribution_ref,
                    EquipmentContributionResolutionStatus.IDENTITY_MISMATCH,
                )
            if (
                known_ref.provider_ref.owner_id == contribution_ref.provider_ref.owner_id
                and known_ref.contribution_key == contribution_ref.contribution_key
                and known_ref.kind is contribution_ref.kind
            ):
                return EquipmentContributionResolution(
                    contribution_ref,
                    EquipmentContributionResolutionStatus.IDENTITY_MISMATCH,
                )
        return EquipmentContributionResolution(
            contribution_ref,
            EquipmentContributionResolutionStatus.MISSING,
        )

    def known_contributions(self) -> tuple[EquipmentContributionRef, ...]:
        return tuple(sorted(self._contributions, key=repr))


class EquipmentEffectivenessStatus(str, Enum):
    EFFECTIVE = "EFFECTIVE"
    SUPPRESSED = "SUPPRESSED"
    BASELINE_DISABLED = "BASELINE_DISABLED"
    MISSING = "MISSING"
    IDENTITY_MISMATCH = "IDENTITY_MISMATCH"
    UNSUPPORTED_BOUNDARY = "UNSUPPORTED_BOUNDARY"


@dataclass(frozen=True, slots=True)
class EquipmentEffectivenessContribution:
    suppression_causes: tuple[SuppressionCause, ...] = ()
    unsupported_boundary: bool = False

    def __post_init__(self) -> None:
        causes = tuple(self.suppression_causes)
        if any(not isinstance(item, SuppressionCause) for item in causes):
            raise TypeError("suppression_causes must contain SuppressionCause values")
        object.__setattr__(self, "suppression_causes", causes)
        if not isinstance(self.unsupported_boundary, bool):
            raise TypeError("unsupported_boundary must be bool")


@dataclass(frozen=True, slots=True)
class EquipmentEffectivenessDecision:
    contribution_ref: EquipmentContributionRef
    status: EquipmentEffectivenessStatus
    suppression_causes: tuple[SuppressionCause, ...] = ()

    @property
    def effective(self) -> bool:
        return self.status is EquipmentEffectivenessStatus.EFFECTIVE


EquipmentEffectivenessRuleAdapter = Callable[
    [object, EquipmentContributionRef],
    EquipmentEffectivenessContribution | None,
]


class EquipmentEffectivenessBoundaryError(RuntimeError):
    pass


class EquipmentEffectivenessPolicy:
    __slots__ = ("_registry", "_provider_policy", "_rule_adapters")

    def __init__(
        self,
        registry: EquipmentContributionRegistry,
        provider_policy: ProviderValidityPolicy,
    ) -> None:
        if not isinstance(registry, EquipmentContributionRegistry):
            raise TypeError("registry must be an EquipmentContributionRegistry")
        if not isinstance(provider_policy, ProviderValidityPolicy):
            raise TypeError("provider_policy must be a ProviderValidityPolicy")
        self._registry = registry
        self._provider_policy = provider_policy
        self._rule_adapters: list[EquipmentEffectivenessRuleAdapter] = []

    @property
    def registry(self) -> EquipmentContributionRegistry:
        return self._registry

    @property
    def provider_validity_policy(self) -> ProviderValidityPolicy:
        return self._provider_policy

    def register_rule_adapter(self, adapter: EquipmentEffectivenessRuleAdapter) -> None:
        if not callable(adapter):
            raise TypeError("adapter must be callable")
        if adapter not in self._rule_adapters:
            self._rule_adapters.append(adapter)

    @staticmethod
    def _decision(ref, status, causes=()):
        return EquipmentEffectivenessDecision(
            ref,
            status,
            tuple(sorted(set(causes), key=repr)),
        )

    def evaluate_contribution(
        self,
        context,
        contribution_ref: EquipmentContributionRef,
    ) -> EquipmentEffectivenessDecision:
        if not isinstance(contribution_ref, EquipmentContributionRef):
            raise TypeError("contribution_ref must be an EquipmentContributionRef")
        resolution = self._registry.resolve_contribution(contribution_ref)
        if resolution.status is EquipmentContributionResolutionStatus.MISSING:
            return self._decision(contribution_ref, EquipmentEffectivenessStatus.MISSING)
        if resolution.status is EquipmentContributionResolutionStatus.IDENTITY_MISMATCH:
            return self._decision(contribution_ref, EquipmentEffectivenessStatus.IDENTITY_MISMATCH)
        if resolution.status is EquipmentContributionResolutionStatus.BASELINE_DISABLED:
            return self._decision(contribution_ref, EquipmentEffectivenessStatus.BASELINE_DISABLED)

        provider = self._provider_policy.evaluate_provider(
            context,
            contribution_ref.provider_ref,
        )
        if provider.status is ProviderValidityStatus.MISSING:
            return self._decision(contribution_ref, EquipmentEffectivenessStatus.MISSING)
        if provider.status is ProviderValidityStatus.IDENTITY_MISMATCH:
            return self._decision(contribution_ref, EquipmentEffectivenessStatus.IDENTITY_MISMATCH)
        if provider.status is ProviderValidityStatus.BASELINE_DISABLED:
            return self._decision(contribution_ref, EquipmentEffectivenessStatus.BASELINE_DISABLED)

        causes: list[SuppressionCause] = list(provider.suppression_causes)
        unsupported = False
        for adapter in self._rule_adapters:
            contribution = adapter(context, contribution_ref)
            if contribution is None:
                continue
            if not isinstance(contribution, EquipmentEffectivenessContribution):
                raise TypeError("equipment effectiveness adapter returned invalid contribution")
            causes.extend(contribution.suppression_causes)
            unsupported = unsupported or contribution.unsupported_boundary

        if unsupported:
            return self._decision(
                contribution_ref,
                EquipmentEffectivenessStatus.UNSUPPORTED_BOUNDARY,
                causes,
            )
        if provider.status is ProviderValidityStatus.SUPPRESSED or causes:
            return self._decision(
                contribution_ref,
                EquipmentEffectivenessStatus.SUPPRESSED,
                causes,
            )
        return self._decision(contribution_ref, EquipmentEffectivenessStatus.EFFECTIVE)


@dataclass(frozen=True, slots=True)
class EquipmentContributionDependency:
    contribution_ref: EquipmentContributionRef
    rule_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.contribution_ref, EquipmentContributionRef):
            raise TypeError("contribution_ref must be an EquipmentContributionRef")
        if not isinstance(self.rule_id, str) or not self.rule_id.strip():
            raise ValueError("rule_id cannot be empty or whitespace")


@dataclass(frozen=True, slots=True)
class EquipmentAttributeContribution:
    contribution_ref: EquipmentContributionRef
    attribute: str
    amount: float

    def __post_init__(self) -> None:
        if not isinstance(self.contribution_ref, EquipmentContributionRef):
            raise TypeError("contribution_ref must be an EquipmentContributionRef")
        if self.contribution_ref.kind is not EquipmentContributionKind.ATTRIBUTE:
            raise ValueError("attribute contribution requires ATTRIBUTE kind")
        if not isinstance(self.attribute, str) or not self.attribute.strip():
            raise ValueError("attribute cannot be empty or whitespace")
        if isinstance(self.amount, bool) or not isinstance(self.amount, (int, float)):
            raise TypeError("amount must be numeric")
        object.__setattr__(self, "amount", float(self.amount))


class EquipmentTriggerGateStatus(str, Enum):
    ALLOW = "ALLOW"
    SKIP = "SKIP"
    UNSUPPORTED_BOUNDARY = "UNSUPPORTED_BOUNDARY"


@dataclass(frozen=True, slots=True)
class EquipmentTriggerGateDecision:
    dependency: EquipmentContributionDependency
    status: EquipmentTriggerGateStatus
    effectiveness: EquipmentEffectivenessDecision


class EquipmentTriggerGate:
    __slots__ = ("_policy",)

    def __init__(self, policy: EquipmentEffectivenessPolicy) -> None:
        if not isinstance(policy, EquipmentEffectivenessPolicy):
            raise TypeError("policy must be an EquipmentEffectivenessPolicy")
        self._policy = policy

    @property
    def equipment_effectiveness_policy(self) -> EquipmentEffectivenessPolicy:
        return self._policy

    def evaluate(
        self,
        context,
        dependency: EquipmentContributionDependency,
    ) -> EquipmentTriggerGateDecision:
        if not isinstance(dependency, EquipmentContributionDependency):
            raise TypeError("dependency must be an EquipmentContributionDependency")
        decision = self._policy.evaluate_contribution(
            context,
            dependency.contribution_ref,
        )
        if decision.status is EquipmentEffectivenessStatus.UNSUPPORTED_BOUNDARY:
            status = EquipmentTriggerGateStatus.UNSUPPORTED_BOUNDARY
        elif decision.effective:
            status = EquipmentTriggerGateStatus.ALLOW
        else:
            status = EquipmentTriggerGateStatus.SKIP
        return EquipmentTriggerGateDecision(dependency, status, decision)
