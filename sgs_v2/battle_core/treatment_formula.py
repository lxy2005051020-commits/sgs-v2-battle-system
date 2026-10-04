from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from fractions import Fraction
from math import isfinite

from .stage9_integerization import ExactRatio
from .weapon_damage_formula import (
    WeaponBaseDamageFormula,
    _load_repository_troop_function_table,
)


def _as_fraction(value: int | float | ExactRatio, field_name: str) -> Fraction:
    if isinstance(value, ExactRatio):
        return Fraction(value.numerator, value.denominator)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be an int, float, or ExactRatio")
    if not isfinite(float(value)):
        raise ValueError(f"{field_name} must be finite")
    return Fraction(Decimal(str(value)))


def _sum_pool(terms: tuple[ExactRatio, ...], field_name: str) -> Fraction:
    total = Fraction(1, 1)
    for term in terms:
        if not isinstance(term, ExactRatio):
            raise TypeError(f"{field_name} must contain ExactRatio values")
        total += Fraction(term.numerator, term.denominator)
    if total < 0:
        raise ValueError(f"{field_name} cannot produce a negative multiplier")
    return total


@dataclass(frozen=True, slots=True)
class TreatmentModifierSnapshot:
    """Application-time frozen ordinary-treatment modifier topology.

    Same-side ordinary modifiers are signed deltas and combine algebraically:
        M_side = 1 + sum(deltas)

    Source-side and target-side pools then multiply. Red-degree / advancement is
    deliberately isolated as its own multiplier pool.
    """

    source_side_deltas: tuple[ExactRatio, ...] = ()
    target_side_deltas: tuple[ExactRatio, ...] = ()
    red_pool_multiplier: ExactRatio = field(default_factory=lambda: ExactRatio(1, 1))

    def __post_init__(self) -> None:
        source = tuple(self.source_side_deltas)
        target = tuple(self.target_side_deltas)
        object.__setattr__(self, "source_side_deltas", source)
        object.__setattr__(self, "target_side_deltas", target)
        _sum_pool(source, "source_side_deltas")
        _sum_pool(target, "target_side_deltas")
        if not isinstance(self.red_pool_multiplier, ExactRatio):
            raise TypeError("red_pool_multiplier must be ExactRatio")
        if self.red_pool_multiplier.numerator < 0:
            raise ValueError("red_pool_multiplier must be >= 0")

    @property
    def source_pool(self) -> Fraction:
        return _sum_pool(self.source_side_deltas, "source_side_deltas")

    @property
    def target_pool(self) -> Fraction:
        return _sum_pool(self.target_side_deltas, "target_side_deltas")

    @property
    def red_pool(self) -> Fraction:
        return Fraction(
            self.red_pool_multiplier.numerator,
            self.red_pool_multiplier.denominator,
        )


@dataclass(frozen=True, slots=True)
class TreatmentFormulaResult:
    troop_function_value: int
    source_attribute: float
    nominal_recovery: int


class TreatmentFormulaSystem:
    """Stage13-B3 canonical ordinary treatment-rate formula.

    H = CEIL(
        Rate
        * (F(N) + Attr)
        * SourceOrdinaryPool
        * TargetOrdinaryPool
        * RedPool
    )

    F(N) reuses the repository's canonical troop-function table. Persistent
    treatment must pass application-time frozen inputs to this system.
    """

    def __init__(
        self,
        *,
        troop_function_table: Mapping[int, int] | None = None,
    ) -> None:
        table = (
            _load_repository_troop_function_table()
            if troop_function_table is None
            else troop_function_table
        )
        self._troop_function_table = WeaponBaseDamageFormula._validate_troop_function_table(
            table
        )

    def troop_function(self, troops: int) -> int:
        if isinstance(troops, bool) or not isinstance(troops, int):
            raise TypeError("source_troops must be an int")
        if not 1 <= troops <= 10000:
            raise ValueError("source_troops must be within lookup-table range [1, 10000]")
        return self._troop_function_table[troops]

    def calculate(
        self,
        *,
        rate: int | float | ExactRatio,
        source_troops: int,
        source_attribute: int | float,
        modifiers: TreatmentModifierSnapshot | None = None,
    ) -> TreatmentFormulaResult:
        rate_fraction = _as_fraction(rate, "rate")
        if rate_fraction < 0:
            raise ValueError("rate must be >= 0")

        attribute_fraction = _as_fraction(source_attribute, "source_attribute")
        if attribute_fraction < 0:
            raise ValueError("source_attribute must be >= 0")

        modifier_snapshot = modifiers or TreatmentModifierSnapshot()
        if not isinstance(modifier_snapshot, TreatmentModifierSnapshot):
            raise TypeError("modifiers must be a TreatmentModifierSnapshot or None")

        troop_term = self.troop_function(source_troops)
        raw = rate_fraction * (Fraction(troop_term, 1) + attribute_fraction)
        modified = (
            raw
            * modifier_snapshot.source_pool
            * modifier_snapshot.target_pool
            * modifier_snapshot.red_pool
        )

        if modified <= 0:
            nominal = 0
        else:
            nominal = (modified.numerator + modified.denominator - 1) // modified.denominator

        return TreatmentFormulaResult(
            troop_function_value=troop_term,
            source_attribute=float(attribute_fraction),
            nominal_recovery=nominal,
        )
