from __future__ import annotations

import math
from numbers import Real


def validate_finite_number(
    value: Real,
    field_name: str,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    """Validate a public numeric input without relying on Python coercion quirks."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{field_name} must be a real number and cannot be bool")

    numeric = float(value)
    if not math.isfinite(numeric):
        raise ValueError(f"{field_name} must be finite")
    if minimum is not None and numeric < minimum:
        raise ValueError(f"{field_name} must be >= {minimum}")
    if maximum is not None and numeric > maximum:
        raise ValueError(f"{field_name} must be <= {maximum}")
    return numeric


def validate_probability(value: Real, field_name: str = "probability") -> float:
    return validate_finite_number(value, field_name, minimum=0.0, maximum=1.0)


def validate_nonnegative_finite(value: Real, field_name: str) -> float:
    return validate_finite_number(value, field_name, minimum=0.0)
