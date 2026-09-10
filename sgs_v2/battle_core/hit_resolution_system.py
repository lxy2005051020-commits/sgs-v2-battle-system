from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .context import BattleContext
from .damage_probability import resolve_probability
from .damage_rule_models import (
    HitPreventionCategory,
    HitRuleContribution,
    HitRuleKind,
    RuleContributionSource,
)
from .damage_rule_provider import DamageRuleCollection
from .damage_system import DamageRequest


class HitPreventionReason(str, Enum):
    IMMUNITY_LIKE = "IMMUNITY_LIKE"
    EVASION_LIKE = "EVASION_LIKE"


@dataclass(frozen=True, slots=True)
class HitAllowedResult:
    contributors: tuple[RuleContributionSource, ...]
    decisive_source: RuleContributionSource | None = None


@dataclass(frozen=True, slots=True)
class HitPreventedResult:
    reason: HitPreventionReason
    contributors: tuple[RuleContributionSource, ...]
    decisive_source: RuleContributionSource | None


HitResolutionResult = HitAllowedResult | HitPreventedResult


class HitResolutionSystem:
    """Generic hit/prevention/bypass resolution over typed contributions."""

    def resolve(
        self,
        context: BattleContext,
        request: DamageRequest,
        rules: DamageRuleCollection,
    ) -> HitResolutionResult:
        applicable = tuple(
            sorted(
                (
                    contribution
                    for contribution in rules.hit_contributions
                    if contribution.applies_to(request.damage_type, request.source_type)
                ),
                key=lambda contribution: contribution.order_key,
            )
        )

        bypass_categories: set[HitPreventionCategory] = set()
        for contribution in applicable:
            if contribution.kind is HitRuleKind.BYPASS:
                bypass_categories.update(contribution.bypass_categories)

        evaluated_sources: list[RuleContributionSource] = []
        for contribution in applicable:
            if contribution.kind is HitRuleKind.BYPASS:
                evaluated_sources.append(contribution.source)
                continue
            if contribution.category in bypass_categories:
                continue

            evaluated_sources.append(contribution.source)
            if contribution.kind is HitRuleKind.DETERMINISTIC_PREVENTION:
                return self._prevented(contribution, tuple(evaluated_sources))
            if contribution.kind is HitRuleKind.PROBABILISTIC_PREVENTION:
                if resolve_probability(context, contribution.probability):
                    return self._prevented(contribution, tuple(evaluated_sources))
                continue
            raise ValueError(f"unsupported hit rule kind: {contribution.kind}")

        return HitAllowedResult(contributors=tuple(evaluated_sources))

    @staticmethod
    def _prevented(
        contribution: HitRuleContribution,
        contributors: tuple[RuleContributionSource, ...],
    ) -> HitPreventedResult:
        if contribution.category is HitPreventionCategory.IMMUNITY_LIKE:
            reason = HitPreventionReason.IMMUNITY_LIKE
        elif contribution.category is HitPreventionCategory.EVASION_LIKE:
            reason = HitPreventionReason.EVASION_LIKE
        else:
            raise ValueError("hit prevention contribution requires a category")
        return HitPreventedResult(
            reason=reason,
            contributors=contributors,
            decisive_source=contribution.source,
        )
