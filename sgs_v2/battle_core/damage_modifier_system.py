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
from .equipment_effectiveness import (
    EquipmentEffectivenessBoundaryError,
    EquipmentEffectivenessPolicy,
    EquipmentEffectivenessStatus,
)
from .damage_rule_provider import DamageRuleCollection
from .numeric_validation import validate_nonnegative_finite

if TYPE_CHECKING:
    from .damage_system import DamageRequest


class DamageModifierSystem:
    """Apply typed damage modifiers after coefficient scaling, with deterministic order."""

    def __init__(
        self,
        equipment_effectiveness_policy: EquipmentEffectivenessPolicy | None = None,
    ) -> None:
        self._equipment_effectiveness_policy = equipment_effectiveness_policy

    @property
    def equipment_effectiveness_policy(self) -> EquipmentEffectivenessPolicy | None:
        return self._equipment_effectiveness_policy

    def _equipment_contribution_effective(
        self,
        context: BattleContext,
        contribution: DamageModifierContribution,
    ) -> bool:
        ref = contribution.equipment_contribution_ref
        if ref is None:
            return True
        if self._equipment_effectiveness_policy is None:
            raise RuntimeError("equipment-owned damage modifier has no effectiveness policy")
        decision = self._equipment_effectiveness_policy.evaluate_contribution(context, ref)
        if decision.status is EquipmentEffectivenessStatus.UNSUPPORTED_BOUNDARY:
            raise EquipmentEffectivenessBoundaryError(
                f"unsupported equipment damage-modifier boundary: {ref!r}"
            )
        return decision.effective

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
                DamageModifierOperation.SUBTRACT_FLAT,
                DamageModifierOperation.REDUCTION_PIERCE,
            }:
                raise ValueError(
                    f"unsupported damage modifier operation: {contribution.operation}"
                )

        applicable = tuple(
            contribution
            for contribution in rules.modifier_contributions
            if (
                contribution.applies_to(request.damage_type, request.source_type)
                and self._equipment_contribution_effective(context, contribution)
            )
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
            if contribution.operation is DamageModifierOperation.SUBTRACT_FLAT:
                input_damage = current
                current = max(0.0, current - contribution.operand)
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
        """Resolve selected phases using the Stage13-B2 aggregation contract.

        Ordinary outgoing and incoming skill modifiers are algebraic same-side
        pools. The two sides remain separate multiplicative layers. Incoming
        reduction pierce transforms only the reduction part of the incoming pool.
        CRITICAL and SINGLE_HIT remain typed non-pool phases.
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
                and self._equipment_contribution_effective(context, contribution)
            ):
                applicable.append(contribution)
        applicable.sort(key=lambda c: (c.phase_order, c.order_key))

        if pierce_rate is not None and not 0.0 <= pierce_rate <= 1.0:
            raise ValueError("pierce_rate must be in [0,1]")

        admitted: list[DamageModifierContribution] = []
        for contribution in applicable:
            if contribution.operation not in {
                DamageModifierOperation.MULTIPLY_FACTOR,
                DamageModifierOperation.SUBTRACT_FLAT,
            }:
                raise ValueError(
                    f"unsupported damage modifier operation: {contribution.operation}"
                )
            if resolve_probability(context, contribution.probability):
                admitted.append(contribution)

        applied: list[AppliedDamageModifier] = []

        def apply_linear_phase(
            phase: DamageModifierPhase,
            increase_kind: DamageModifierKind,
            reduction_kind: DamageModifierKind,
            *,
            reduction_scale: float = 1.0,
        ) -> None:
            nonlocal current
            phase_items = [item for item in admitted if item.phase is phase]
            if not phase_items:
                return

            phase_base = current
            raw_net = 0.0
            for item in phase_items:
                if item.kind is increase_kind:
                    if item.operand < 1.0:
                        raise ValueError(
                            f"{increase_kind.value} MULTIPLY_FACTOR must be >= 1"
                        )
                    raw_net += item.operand - 1.0
                elif item.kind is reduction_kind:
                    if not 0.0 <= item.operand <= 1.0:
                        raise ValueError(
                            f"{reduction_kind.value} MULTIPLY_FACTOR must be in [0,1]"
                        )
                    raw_net -= (1.0 - item.operand) * reduction_scale
                else:
                    # Non-pool contribution in this phase keeps legacy typed
                    # multiplicative behavior rather than being silently folded.
                    input_damage = current
                    current = validate_nonnegative_finite(
                        current * item.operand,
                        "modifier output",
                    )
                    applied.append(
                        AppliedDamageModifier(
                            contribution=item,
                            input_damage=input_damage,
                            output_damage=current,
                            original_operand=item.operand,
                            effective_operand=item.operand,
                            pierce_contributor=None,
                        )
                    )
                    phase_base = current
                    raw_net = 0.0
                    continue

                input_damage = current
                factor = max(0.10, 1.0 + raw_net)
                current = validate_nonnegative_finite(
                    phase_base * factor,
                    "modifier output",
                )
                applied.append(
                    AppliedDamageModifier(
                        contribution=item,
                        input_damage=input_damage,
                        output_damage=current,
                        original_operand=item.operand,
                        effective_operand=(
                            0.0 if input_damage == 0.0 else current / input_damage
                        ),
                        pierce_contributor=None,
                    )
                )

        # Legacy/synthetic critical contributions remain their own typed phase.
        for item in [x for x in admitted if x.phase is DamageModifierPhase.CRITICAL]:
            input_damage = current
            current = validate_nonnegative_finite(
                current * item.operand,
                "modifier output",
            )
            applied.append(
                AppliedDamageModifier(
                    contribution=item,
                    input_damage=input_damage,
                    output_damage=current,
                    original_operand=item.operand,
                    effective_operand=item.operand,
                    pierce_contributor=None,
                )
            )

        apply_linear_phase(
            DamageModifierPhase.OUTGOING,
            DamageModifierKind.OUTGOING_INCREASE,
            DamageModifierKind.OUTGOING_REDUCTION,
        )
        apply_linear_phase(
            DamageModifierPhase.INCOMING,
            DamageModifierKind.INCOMING_INCREASE,
            DamageModifierKind.INCOMING_REDUCTION,
            reduction_scale=1.0 if pierce_rate is None else 1.0 - pierce_rate,
        )

        for item in [x for x in admitted if x.phase is DamageModifierPhase.SINGLE_HIT]:
            input_damage = current
            if item.operation is DamageModifierOperation.SUBTRACT_FLAT:
                current = max(0.0, current - item.operand)
            else:
                current = validate_nonnegative_finite(
                    current * item.operand,
                    "modifier output",
                )
            applied.append(
                AppliedDamageModifier(
                    contribution=item,
                    input_damage=input_damage,
                    output_damage=current,
                    original_operand=item.operand,
                    effective_operand=item.operand,
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
