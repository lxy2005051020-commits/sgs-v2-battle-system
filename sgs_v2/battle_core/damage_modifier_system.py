from __future__ import annotations

from typing import TYPE_CHECKING

from .context import BattleContext
from .damage_modifiers import (
    AppliedDamageModifier,
    DamageModifierContribution,
    DamageModifierKind,
    DamageModifierOperation,
    DamageModifierResult,
)
from .damage_probability import resolve_probability
from .damage_rule_provider import DamageRuleCollection
from .numeric_validation import validate_nonnegative_finite

if TYPE_CHECKING:
    from .damage_system import DamageRequest


class DamageModifierSystem:
    """Apply typed damage modifiers after coefficient scaling, with deterministic order."""

    def resolve(
        self,
        context: BattleContext,
        request: "DamageRequest",
        rules: DamageRuleCollection,
        scaled_damage: float,
    ) -> DamageModifierResult:
        current = validate_nonnegative_finite(scaled_damage, "scaled_damage")

        # Validate every typed contribution before scope filtering or probability resolution.
        # Malformed input must never become RNG-dependent behavior.
        for contribution in rules.modifier_contributions:
            contribution.validate_runtime_contract()
            if contribution.operation not in {
                DamageModifierOperation.MULTIPLY_FACTOR,
                DamageModifierOperation.REDUCTION_PIERCE,
            }:
                raise ValueError(
                    f"unsupported damage modifier operation: {contribution.operation}"
                )

        applicable = tuple(
            contribution
            for contribution in rules.modifier_contributions
            if contribution.applies_to(request.damage_type, request.source_type)
        )

        pierce = tuple(
            contribution
            for contribution in applicable
            if contribution.operation is DamageModifierOperation.REDUCTION_PIERCE
        )
        if len(pierce) > 1:
            raise ValueError(
                "multiple reduction-pierce contributions require evidenced aggregation semantics"
            )
        if pierce and pierce[0].probability != 1.0:
            raise ValueError("reduction-pierce infrastructure is deterministic in Stage 8")

        ordered = tuple(
            sorted(
                (
                    contribution
                    for contribution in applicable
                    if contribution.operation is not DamageModifierOperation.REDUCTION_PIERCE
                ),
                key=lambda contribution: (contribution.phase_order, contribution.order_key),
            )
        )

        applied: list[AppliedDamageModifier] = []
        for contribution in ordered:
            if not resolve_probability(context, contribution.probability):
                continue
            if contribution.operation is not DamageModifierOperation.MULTIPLY_FACTOR:
                raise ValueError(
                    f"unsupported damage modifier operation: {contribution.operation}"
                )

            original_operand = contribution.operand
            effective_operand = original_operand
            pierce_source = None
            if contribution.kind is DamageModifierKind.INCOMING_REDUCTION and pierce:
                effective_operand = self._pierced_reduction_factor(
                    original_operand,
                    pierce[0].operand,
                )
                pierce_source = pierce[0].source

            input_damage = current
            current = validate_nonnegative_finite(
                input_damage * effective_operand,
                "modifier output",
            )
            applied.append(
                AppliedDamageModifier(
                    contribution=contribution,
                    input_damage=input_damage,
                    output_damage=current,
                    original_operand=original_operand,
                    effective_operand=effective_operand,
                    pierce_contributor=pierce_source,
                )
            )

        return DamageModifierResult(
            input_damage=validate_nonnegative_finite(scaled_damage, "scaled_damage"),
            output_damage=current,
            applied_modifiers=tuple(applied),
        )

    @staticmethod
    def _pierced_reduction_factor(original_factor: float, pierce_rate: float) -> float:
        if not 0.0 <= original_factor <= 1.0:
            raise ValueError(
                "INCOMING_REDUCTION MULTIPLY_FACTOR must be in [0, 1] for pierce"
            )
        reduction_rate = 1.0 - original_factor
        effective_reduction_rate = reduction_rate * (1.0 - pierce_rate)
        return validate_nonnegative_finite(
            1.0 - effective_reduction_rate,
            "effective incoming reduction operand",
        )
