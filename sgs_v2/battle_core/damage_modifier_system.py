from __future__ import annotations

from typing import TYPE_CHECKING

from .context import BattleContext
from .damage_modifiers import (
    AppliedDamageModifier,
    DamageModifierContribution,
    DamageModifierKind,
    DamageModifierOperation,
    DamageModifierPhase,
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

    def resolve_phases(
        self,
        context: BattleContext,
        request: "DamageRequest",
        rules: DamageRuleCollection,
        scaled_damage: float,
        *,
        phases: frozenset[DamageModifierPhase],
        pierce_rate: float | None = None,
    ) -> DamageModifierResult:
        """Resolve a selected modifier phase set for Stage11 pipeline ownership.

        With 690221 active, eligible incoming reductions are pooled as reduction
        rates, capped at 90%, then proportionally transformed. The old resolve()
        remains unchanged for Stage8 callers and regression compatibility.
        """
        current = validate_nonnegative_finite(scaled_damage, "scaled_damage")
        applicable: list[DamageModifierContribution] = []
        for contribution in rules.modifier_contributions:
            contribution.validate_runtime_contract()
            if contribution.operation is DamageModifierOperation.REDUCTION_PIERCE:
                continue
            if (
                contribution.phase in phases
                and contribution.applies_to(request.damage_type, request.source_type)
            ):
                applicable.append(contribution)
        applicable.sort(key=lambda c: (c.phase_order, c.order_key))

        if pierce_rate is not None and not 0.0 <= pierce_rate <= 1.0:
            raise ValueError("pierce_rate must be in [0,1]")

        applied: list[AppliedDamageModifier] = []
        reduction_done = False
        for contribution in applicable:
            if (
                pierce_rate is not None
                and contribution.kind is DamageModifierKind.INCOMING_REDUCTION
            ):
                if reduction_done:
                    continue
                reduction_done = True
                admitted: list[DamageModifierContribution] = []
                for item in applicable:
                    if item.kind is not DamageModifierKind.INCOMING_REDUCTION:
                        continue
                    if resolve_probability(context, item.probability):
                        if not 0.0 <= item.operand <= 1.0:
                            raise ValueError(
                                "INCOMING_REDUCTION MULTIPLY_FACTOR must be in [0,1]"
                            )
                        admitted.append(item)
                if not admitted:
                    continue
                total_reduction = min(
                    sum(1.0 - item.operand for item in admitted),
                    0.90,
                )
                effective_reduction = total_reduction * (1.0 - pierce_rate)
                effective_factor = 1.0 - effective_reduction
                input_damage = current
                current = validate_nonnegative_finite(
                    current * effective_factor,
                    "modifier output",
                )
                applied.append(
                    AppliedDamageModifier(
                        contribution=admitted[0],
                        input_damage=input_damage,
                        output_damage=current,
                        original_operand=1.0 - total_reduction,
                        effective_operand=effective_factor,
                        pierce_contributor=None,
                    )
                )
                continue

            if not resolve_probability(context, contribution.probability):
                continue
            if contribution.operation is not DamageModifierOperation.MULTIPLY_FACTOR:
                raise ValueError(
                    f"unsupported damage modifier operation: {contribution.operation}"
                )
            input_damage = current
            current = validate_nonnegative_finite(
                current * contribution.operand,
                "modifier output",
            )
            applied.append(
                AppliedDamageModifier(
                    contribution=contribution,
                    input_damage=input_damage,
                    output_damage=current,
                    original_operand=contribution.operand,
                    effective_operand=contribution.operand,
                    pierce_contributor=None,
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
