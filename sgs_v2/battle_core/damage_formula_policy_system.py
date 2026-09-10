from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .damage_formula_context import DamageDefensePolicy, DamageFormulaContext
from .damage_rule_models import RuleContributionSource
from .damage_rule_provider import DamageRuleCollection

if TYPE_CHECKING:
    from .damage_system import DamageRequest


@dataclass(frozen=True, slots=True)
class DamageFormulaPolicyResult:
    formula_context: DamageFormulaContext
    contributors: tuple[RuleContributionSource, ...]


class DamageFormulaPolicySystem:
    """Resolve the only typed policy input allowed into frozen base formulas."""

    def resolve(
        self,
        request: "DamageRequest",
        rules: DamageRuleCollection,
    ) -> DamageFormulaPolicyResult:
        contributions = tuple(
            sorted(
                (
                    contribution
                    for contribution in rules.formula_policy_contributions
                    if contribution.applies_to(request.damage_type, request.source_type)
                ),
                key=lambda contribution: contribution.order_key,
            )
        )
        if any(
            contribution.defense_policy
            is DamageDefensePolicy.IGNORE_RELEVANT_TARGET_DEFENSE
            for contribution in contributions
        ):
            policy = DamageDefensePolicy.IGNORE_RELEVANT_TARGET_DEFENSE
        else:
            policy = DamageDefensePolicy.NORMAL

        return DamageFormulaPolicyResult(
            formula_context=DamageFormulaContext(defense_policy=policy),
            contributors=tuple(contribution.source for contribution in contributions),
        )
