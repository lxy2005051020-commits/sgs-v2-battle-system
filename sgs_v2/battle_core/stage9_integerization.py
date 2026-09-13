from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import math
from typing import Any


@dataclass(frozen=True, slots=True, order=False)
class ExactRatio:
    """Canonical exact rational representation for Stage9 mechanism calculations.

    Invariants:
    - denominator > 0
    - gcd(|numerator|, denominator) == 1
    - sign normalized to numerator
    - zero canonical form: 0 / 1
    - immutable
    - no generic from_float
    """

    numerator: int
    denominator: int

    def __init__(self, numerator: int, denominator: int = 1) -> None:
        if isinstance(numerator, bool) or not isinstance(numerator, int):
            raise TypeError(f"numerator must be an int, got {type(numerator)}")
        if isinstance(denominator, bool) or not isinstance(denominator, int):
            raise TypeError(f"denominator must be an int, got {type(denominator)}")
        if denominator == 0:
            raise ZeroDivisionError("denominator cannot be zero")

        # Canonical zero
        if numerator == 0:
            object.__setattr__(self, "numerator", 0)
            object.__setattr__(self, "denominator", 1)
            return

        # Sign normalization: denominator must always be positive
        num = numerator
        den = denominator
        if den < 0:
            num = -num
            den = -den

        # gcd reduction
        common = math.gcd(abs(num), den)
        if common > 1:
            num //= common
            den //= common

        object.__setattr__(self, "numerator", num)
        object.__setattr__(self, "denominator", den)

    def __str__(self) -> str:
        return f"{self.numerator}/{self.denominator}"

    def __repr__(self) -> str:
        return f"ExactRatio({self.numerator}, {self.denominator})"

    @classmethod
    def from_text(cls, text: str) -> ExactRatio:
        """Create ExactRatio from raw textual representation (e.g. '0.54', '28.28%', '27/50')."""
        if not isinstance(text, str):
            raise TypeError("text must be a str")
        cleaned = text.strip()
        if not cleaned:
            raise ValueError("text cannot be empty")

        if "/" in cleaned:
            parts = cleaned.split("/")
            if len(parts) != 2:
                raise ValueError(f"Invalid fraction string: {cleaned}")
            return cls(int(parts[0].strip()), int(parts[1].strip()))

        is_percent = False
        if cleaned.endswith("%"):
            is_percent = True
            cleaned = cleaned[:-1].strip()

        dec = Decimal(cleaned)
        # Decimal to rational
        sign, digits, exponent = dec.as_tuple()
        if exponent >= 0:
            numerator = int(dec)
            denominator = 1
        else:
            scale = -exponent
            denominator = 10**scale
            numerator = int(dec * denominator)

        if is_percent:
            denominator *= 100

        return cls(numerator, denominator)

    @classmethod
    def from_percent(cls, pct: int | str | Decimal) -> ExactRatio:
        """Create ExactRatio from percentage (e.g. 54 -> 54/100 -> 27/50)."""
        if isinstance(pct, bool):
            raise TypeError("pct cannot be a bool")
        if isinstance(pct, int):
            return cls(pct, 100)
        if isinstance(pct, (str, Decimal)):
            s = str(pct).strip()
            if s.endswith("%"):
                return cls.from_text(s)
            return cls.from_text(f"{s}%")
        raise TypeError(f"pct must be int, str, or Decimal, got {type(pct)}")

    @classmethod
    def from_basis_points(cls, bp: int) -> ExactRatio:
        """Create ExactRatio from basis points (1 bp = 1/10000)."""
        if isinstance(bp, bool) or not isinstance(bp, int):
            raise TypeError("bp must be an int")
        return cls(bp, 10000)

    # Note: NO generic from_float(...) method is provided or permitted.


def exact_ratio_from_legacy_config_float(raw_loaded_value: float) -> ExactRatio:
    """Explicit, non-generic legacy configuration float adapter.

    Constraints:
    - raw loaded scalar only
    - never a computed float
    - uses Decimal(str(raw_loaded_value))
    - clearly documented as compatibility-only
    - cannot recover precision lost before this boundary
    """
    if isinstance(raw_loaded_value, bool) or not isinstance(raw_loaded_value, float):
        raise TypeError("raw_loaded_value must be a float")
    if not math.isfinite(raw_loaded_value):
        raise ValueError("raw_loaded_value must be finite")
    return ExactRatio.from_text(str(raw_loaded_value))


def floor_product_int_ratio(base: int, ratio: ExactRatio) -> int:
    """Exact floor product: floor(base * ratio.numerator / ratio.denominator)."""
    if isinstance(base, bool) or not isinstance(base, int):
        raise TypeError("base must be an int")
    if not isinstance(ratio, ExactRatio):
        raise TypeError(f"ratio must be an ExactRatio, got {type(ratio)}")
    return (base * ratio.numerator) // ratio.denominator


def round_half_up_product_int_ratio(base: int, ratio: ExactRatio) -> int:
    """Exact round-half-up product of integer base and ExactRatio."""
    if isinstance(base, bool) or not isinstance(base, int):
        raise TypeError("base must be an int")
    if not isinstance(ratio, ExactRatio):
        raise TypeError(f"ratio must be an ExactRatio, got {type(ratio)}")

    num = base * ratio.numerator
    den = ratio.denominator
    if num >= 0:
        return (num * 2 + den) // (den * 2)
    return (num * 2 - den) // (den * 2)


def round_half_up_divide_int(numerator: int, denominator: int) -> int:
    """Exact round-half-up integer division: round_half_up(numerator / denominator)."""
    if isinstance(numerator, bool) or not isinstance(numerator, int):
        raise TypeError("numerator must be an int")
    if isinstance(denominator, bool) or not isinstance(denominator, int):
        raise TypeError("denominator must be an int")
    if denominator <= 0:
        raise ValueError("denominator must be positive")

    if numerator >= 0:
        return (numerator * 2 + denominator) // (denominator * 2)
    return (numerator * 2 - denominator) // (denominator * 2)
