"""Backward-compatible basis extension of the frozen ordinary treatment owner."""
from dataclasses import dataclass

from .stage9_integerization import ExactRatio
from .treatment_formula import TreatmentFormulaSystem, TreatmentFormulaResult, TreatmentModifierSnapshot, _as_fraction


@dataclass(frozen=True, slots=True)
class AdditiveTreatmentFormulaResult(TreatmentFormulaResult):
    base_addition: ExactRatio = ExactRatio(0, 1)


class AdditiveTreatmentFormulaSystem(TreatmentFormulaSystem):
    """Expose a separate additive basis while preserving the canonical CEIL topology.

    Zero-addition callers delegate unchanged to the frozen owner. Nonzero basis
    callers use its troop lookup and modifier snapshot pools, changing only the
    sum before multiplication. No source attribute or lookup row is fabricated.
    """

    def calculate(self, *, rate: int | float | ExactRatio, source_troops: int,
                  source_attribute: int | float,
                  modifiers: TreatmentModifierSnapshot | None = None,
                  base_addition: int | float | ExactRatio = 0) -> AdditiveTreatmentFormulaResult:
        addition = _as_fraction(base_addition, "base_addition")
        if addition < 0:
            raise ValueError("base_addition must be >= 0")
        # Reuse all canonical validation and the complete default formula path.
        baseline = super().calculate(rate=rate, source_troops=source_troops,
                                     source_attribute=source_attribute, modifiers=modifiers)
        if addition == 0:
            return AdditiveTreatmentFormulaResult(baseline.troop_function_value,
                baseline.source_attribute, baseline.nominal_recovery)
        snapshot = modifiers or TreatmentModifierSnapshot()
        raw = (_as_fraction(rate, "rate") *
               (baseline.troop_function_value + _as_fraction(source_attribute, "source_attribute") + addition) *
               snapshot.source_pool * snapshot.target_pool * snapshot.red_pool)
        nominal = (raw.numerator + raw.denominator - 1) // raw.denominator if raw > 0 else 0
        return AdditiveTreatmentFormulaResult(baseline.troop_function_value,
            baseline.source_attribute, nominal, ExactRatio(addition.numerator, addition.denominator))
