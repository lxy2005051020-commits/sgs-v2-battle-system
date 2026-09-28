from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .damage_rule_models import (
    DamagePreventionContribution,
    DamagePreventionRuleKind,
    RuleContributionSource,
)
from .damage_rule_provider import DamageRuleCollection


class DamagePreventionReason(str, Enum):
    SOURCE_CANNOT_DEAL_DAMAGE = "SOURCE_CANNOT_DEAL_DAMAGE"
    RULE_PREVENTED = "RULE_PREVENTED"


@dataclass(frozen=True, slots=True)
class DamageAllowedResult:
    contributors: tuple[RuleContributionSource, ...]


@dataclass(frozen=True, slots=True)
class DamagePreventedResult:
    reason: DamagePreventionReason
    contributors: tuple[RuleContributionSource, ...]
    decisive_source: RuleContributionSource


DamagePermissionResult = DamageAllowedResult | DamagePreventedResult


class DamagePreventionSystem:
    """Resolve typed prevention contributions without knowing concrete state ids."""

    def resolve(self, rules: DamageRuleCollection) -> DamagePermissionResult:
        for contribution in rules.prevention_contributions:
            contribution.validate_runtime_contract()
        contributions = tuple(
            sorted(
                rules.prevention_contributions,
                key=lambda contribution: contribution.order_key,
            )
        )
        sources = tuple(contribution.source for contribution in contributions)
        if not contributions:
            return DamageAllowedResult(contributors=())

        decisive = contributions[0]
        return DamagePreventedResult(
            reason=self._reason_for(decisive),
            contributors=sources,
            decisive_source=decisive.source,
        )

    @staticmethod
    def _reason_for(contribution: DamagePreventionContribution) -> DamagePreventionReason:
        contribution.validate_runtime_contract()
        if contribution.kind is DamagePreventionRuleKind.SOURCE_CANNOT_DEAL_DAMAGE:
            return DamagePreventionReason.SOURCE_CANNOT_DEAL_DAMAGE
        if contribution.kind is DamagePreventionRuleKind.GENERIC_PREVENTION:
            return DamagePreventionReason.RULE_PREVENTED
        raise ValueError(f"unsupported prevention rule kind: {contribution.kind}")
