from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Iterable

from .target_operation import TargetOperation


class TargetPolicyBoundary(str, Enum):
    NONE = "NONE"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True, slots=True)
class TargetPolicyContribution:
    required_target_ids: tuple[str, ...] = ()
    excluded_target_ids: tuple[str, ...] = ()
    preserve_cardinality: bool = True
    boundary: TargetPolicyBoundary = TargetPolicyBoundary.NONE

    def __post_init__(self) -> None:
        required = tuple(self.required_target_ids)
        excluded = tuple(self.excluded_target_ids)
        if any(not isinstance(item, str) or not item.strip() for item in required + excluded):
            raise ValueError("target ids must contain non-empty strings")
        if not isinstance(self.preserve_cardinality, bool):
            raise TypeError("preserve_cardinality must be a bool")
        if not isinstance(self.boundary, TargetPolicyBoundary):
            raise TypeError("boundary must be a TargetPolicyBoundary")
        object.__setattr__(self, "required_target_ids", required)
        object.__setattr__(self, "excluded_target_ids", excluded)


@dataclass(frozen=True, slots=True)
class TargetPolicyDecision:
    operation: TargetOperation
    eligible_candidate_ids: tuple[str, ...]
    required_target_ids: tuple[str, ...]
    excluded_target_ids: tuple[str, ...]
    preserve_cardinality: bool
    boundary: TargetPolicyBoundary = TargetPolicyBoundary.NONE

    @property
    def supported(self) -> bool:
        return self.boundary is TargetPolicyBoundary.NONE


SkillTargetRuleAdapter = Callable[
    [object, TargetOperation, tuple[str, ...]],
    TargetPolicyContribution | None,
]


class SkillTargetPolicy:
    """Pure constraint policy for already-admitted fresh Skill target operations."""

    __slots__ = ("_rule_adapters",)

    def __init__(self) -> None:
        self._rule_adapters: list[SkillTargetRuleAdapter] = []

    def register_rule_adapter(self, adapter: SkillTargetRuleAdapter) -> None:
        if not callable(adapter):
            raise TypeError("adapter must be callable")
        if adapter in self._rule_adapters:
            return
        self._rule_adapters.append(adapter)

    @staticmethod
    def _candidate_ids(raw_candidates: Iterable[object]) -> tuple[str, ...]:
        ids: list[str] = []
        for candidate in raw_candidates:
            candidate_id = (
                candidate
                if isinstance(candidate, str)
                else getattr(candidate, "unit_id", None)
            )
            if not isinstance(candidate_id, str) or not candidate_id.strip():
                raise TypeError("raw candidates must be unit-id strings or expose unit_id")
            if candidate_id not in ids:
                ids.append(candidate_id)
        return tuple(ids)

    def evaluate(
        self,
        context: object,
        operation: TargetOperation,
        raw_candidates: Iterable[object],
    ) -> TargetPolicyDecision:
        if not isinstance(operation, TargetOperation):
            raise TypeError("operation must be a TargetOperation")
        raw_ids = self._candidate_ids(raw_candidates)

        required: set[str] = set()
        excluded: set[str] = set()
        preserve_cardinality = True
        boundary = TargetPolicyBoundary.NONE

        for adapter in self._rule_adapters:
            contribution = adapter(context, operation, raw_ids)
            if contribution is None:
                continue
            if not isinstance(contribution, TargetPolicyContribution):
                raise TypeError(
                    "SkillTarget rule adapter must return "
                    "TargetPolicyContribution or None"
                )
            required.update(contribution.required_target_ids)
            excluded.update(contribution.excluded_target_ids)
            preserve_cardinality = (
                preserve_cardinality and contribution.preserve_cardinality
            )
            if contribution.boundary is TargetPolicyBoundary.UNSUPPORTED:
                boundary = TargetPolicyBoundary.UNSUPPORTED

        eligible = tuple(item for item in raw_ids if item not in excluded)
        legal_required = tuple(item for item in eligible if item in required)
        ordered_excluded = tuple(item for item in raw_ids if item in excluded)
        ordered_excluded += tuple(
            sorted(item for item in excluded if item not in raw_ids)
        )

        return TargetPolicyDecision(
            operation=operation,
            eligible_candidate_ids=eligible,
            required_target_ids=legal_required,
            excluded_target_ids=ordered_excluded,
            preserve_cardinality=preserve_cardinality,
            boundary=boundary,
        )
