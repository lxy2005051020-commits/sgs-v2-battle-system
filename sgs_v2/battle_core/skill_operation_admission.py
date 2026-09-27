from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .provider_identity import SkillProviderRef
from .provider_validity import ProviderValidityDecision, ProviderValidityPolicy
from .skill_definition import PreparationMode, SkillType
from .skill_permission import (
    SkillOperationKind,
    SkillPermissionDecision,
    SkillPermissionPolicy,
    SkillPermissionRequest,
    SkillPermissionStatus,
)


@dataclass(frozen=True, slots=True)
class SkillOperationAdmissionRequest:
    actor_id: str
    provider_ref: SkillProviderRef
    skill_type: SkillType
    preparation_mode: PreparationMode
    operation_kind: SkillOperationKind = SkillOperationKind.NEW_ADMISSION

    def __post_init__(self) -> None:
        if not isinstance(self.actor_id, str) or not self.actor_id.strip():
            raise ValueError("actor_id cannot be empty or whitespace")
        if not isinstance(self.provider_ref, SkillProviderRef):
            raise TypeError("provider_ref must be a SkillProviderRef")
        if self.provider_ref.owner_id != self.actor_id:
            raise ValueError("actor_id must match provider_ref.owner_id")
        if not isinstance(self.skill_type, SkillType):
            raise TypeError("skill_type must be a SkillType")
        if not isinstance(self.preparation_mode, PreparationMode):
            raise TypeError("preparation_mode must be a PreparationMode")
        if not isinstance(self.operation_kind, SkillOperationKind):
            raise TypeError("operation_kind must be a SkillOperationKind")

    def permission_request(self) -> SkillPermissionRequest:
        return SkillPermissionRequest(
            actor_id=self.actor_id,
            provider_ref=self.provider_ref,
            skill_type=self.skill_type,
            preparation_mode=self.preparation_mode,
            operation_kind=self.operation_kind,
        )


class SkillOperationAdmissionStatus(str, Enum):
    ALLOW = "ALLOW"
    DENY_PROVIDER_INVALID = "DENY_PROVIDER_INVALID"
    DENY_PERMISSION = "DENY_PERMISSION"
    UNSUPPORTED_BOUNDARY = "UNSUPPORTED_BOUNDARY"


@dataclass(frozen=True, slots=True)
class SkillOperationAdmissionDecision:
    request: SkillOperationAdmissionRequest
    status: SkillOperationAdmissionStatus
    provider_decision: ProviderValidityDecision
    permission_decision: SkillPermissionDecision | None = None

    @property
    def admitted(self) -> bool:
        return self.status is SkillOperationAdmissionStatus.ALLOW


class SkillOperationAdmissionCoordinator:
    """Composes Provider validity and holder permission before any owned RNG."""

    __slots__ = ("_provider_validity_policy", "_skill_permission_policy")

    def __init__(
        self,
        provider_validity_policy: ProviderValidityPolicy,
        skill_permission_policy: SkillPermissionPolicy,
    ) -> None:
        if not isinstance(provider_validity_policy, ProviderValidityPolicy):
            raise TypeError("provider_validity_policy must be ProviderValidityPolicy")
        if not isinstance(skill_permission_policy, SkillPermissionPolicy):
            raise TypeError("skill_permission_policy must be SkillPermissionPolicy")
        self._provider_validity_policy = provider_validity_policy
        self._skill_permission_policy = skill_permission_policy

    @property
    def provider_validity_policy(self) -> ProviderValidityPolicy:
        return self._provider_validity_policy

    @property
    def skill_permission_policy(self) -> SkillPermissionPolicy:
        return self._skill_permission_policy

    def evaluate(
        self,
        context: object,
        request: SkillOperationAdmissionRequest,
    ) -> SkillOperationAdmissionDecision:
        if not isinstance(request, SkillOperationAdmissionRequest):
            raise TypeError("request must be a SkillOperationAdmissionRequest")

        provider_decision = self._provider_validity_policy.evaluate_provider(
            context,
            request.provider_ref,
        )
        if not provider_decision.valid:
            return SkillOperationAdmissionDecision(
                request=request,
                status=SkillOperationAdmissionStatus.DENY_PROVIDER_INVALID,
                provider_decision=provider_decision,
            )

        permission_decision = self._skill_permission_policy.evaluate(
            context,
            request.permission_request(),
        )
        if (
            permission_decision.status
            is SkillPermissionStatus.DENY_UNSUPPORTED_BOUNDARY
        ):
            status = SkillOperationAdmissionStatus.UNSUPPORTED_BOUNDARY
        elif not permission_decision.allowed:
            status = SkillOperationAdmissionStatus.DENY_PERMISSION
        else:
            status = SkillOperationAdmissionStatus.ALLOW

        return SkillOperationAdmissionDecision(
            request=request,
            status=status,
            provider_decision=provider_decision,
            permission_decision=permission_decision,
        )
