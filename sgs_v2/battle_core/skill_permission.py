from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable

from .provider_identity import SkillProviderRef
from .skill_definition import PreparationMode, SkillType


class SkillOperationKind(str, Enum):
    NEW_ADMISSION = "NEW_ADMISSION"
    CONTINUATION = "CONTINUATION"


class SkillPermissionStatus(str, Enum):
    ALLOW = "ALLOW"
    DENY_STATE_PERMISSION = "DENY_STATE_PERMISSION"
    DENY_UNSUPPORTED_BOUNDARY = "DENY_UNSUPPORTED_BOUNDARY"
    CONTINUATION_NOT_REEVALUATED = "CONTINUATION_NOT_REEVALUATED"


@dataclass(frozen=True, slots=True)
class SkillPermissionRequest:
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
        if not isinstance(self.skill_type, SkillType):
            raise TypeError("skill_type must be a SkillType")
        if not isinstance(self.preparation_mode, PreparationMode):
            raise TypeError("preparation_mode must be a PreparationMode")
        if not isinstance(self.operation_kind, SkillOperationKind):
            raise TypeError("operation_kind must be a SkillOperationKind")


@dataclass(frozen=True, slots=True)
class SkillPermissionDecision:
    request: SkillPermissionRequest
    status: SkillPermissionStatus
    blocker_keys: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.request, SkillPermissionRequest):
            raise TypeError("request must be a SkillPermissionRequest")
        if not isinstance(self.status, SkillPermissionStatus):
            raise TypeError("status must be a SkillPermissionStatus")
        blockers = tuple(self.blocker_keys)
        if any(not isinstance(item, str) or not item.strip() for item in blockers):
            raise ValueError("blocker_keys must contain non-empty strings")
        object.__setattr__(self, "blocker_keys", blockers)

    @property
    def allowed(self) -> bool:
        return self.status in (
            SkillPermissionStatus.ALLOW,
            SkillPermissionStatus.CONTINUATION_NOT_REEVALUATED,
        )


SkillPermissionRuleAdapter = Callable[
    [object, SkillPermissionRequest],
    SkillPermissionDecision | None,
]


class SkillPermissionPolicy:
    """Pure holder-level permission policy for creating a Skill operation."""

    __slots__ = ("_rule_adapters",)

    def __init__(self) -> None:
        self._rule_adapters: list[SkillPermissionRuleAdapter] = []

    def register_rule_adapter(self, adapter: SkillPermissionRuleAdapter) -> None:
        if not callable(adapter):
            raise TypeError("adapter must be callable")
        if adapter in self._rule_adapters:
            return
        self._rule_adapters.append(adapter)

    def evaluate(
        self,
        context: object,
        request: SkillPermissionRequest,
    ) -> SkillPermissionDecision:
        if not isinstance(request, SkillPermissionRequest):
            raise TypeError("request must be a SkillPermissionRequest")

        if request.operation_kind is SkillOperationKind.CONTINUATION:
            return SkillPermissionDecision(
                request=request,
                status=SkillPermissionStatus.CONTINUATION_NOT_REEVALUATED,
            )

        blockers: list[str] = []
        denied = False
        unsupported = False
        for adapter in self._rule_adapters:
            decision = adapter(context, request)
            if decision is None:
                continue
            if not isinstance(decision, SkillPermissionDecision):
                raise TypeError(
                    "SkillPermission rule adapter must return "
                    "SkillPermissionDecision or None"
                )
            if decision.request != request:
                raise ValueError("SkillPermission adapter returned a decision for another request")
            blockers.extend(decision.blocker_keys)
            if decision.status is SkillPermissionStatus.DENY_UNSUPPORTED_BOUNDARY:
                unsupported = True
            elif decision.status is SkillPermissionStatus.DENY_STATE_PERMISSION:
                denied = True

        status = SkillPermissionStatus.ALLOW
        if unsupported:
            status = SkillPermissionStatus.DENY_UNSUPPORTED_BOUNDARY
        elif denied:
            status = SkillPermissionStatus.DENY_STATE_PERMISSION

        return SkillPermissionDecision(
            request=request,
            status=status,
            blocker_keys=tuple(sorted(set(blockers))),
        )
