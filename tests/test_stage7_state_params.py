from __future__ import annotations

from math import inf, nan

import pytest

from sgs_v2.battle_core import (
    DamageType,
    PeriodicDamageStateParams,
    PeriodicRecoveryStateParams,
)


def test_periodic_damage_params_normalize_numeric_coefficient_to_float() -> None:
    params = PeriodicDamageStateParams(DamageType.WEAPON, 2)
    assert params.damage_type is DamageType.WEAPON
    assert params.coefficient == 2.0
    assert isinstance(params.coefficient, float)


@pytest.mark.parametrize("bad_type", ["WEAPON", 1, None])
def test_periodic_damage_params_require_damage_type_enum(bad_type) -> None:
    with pytest.raises(TypeError):
        PeriodicDamageStateParams(bad_type, 1.0)  # type: ignore[arg-type]


@pytest.mark.parametrize("coefficient", [True, "1", None])
def test_periodic_damage_params_reject_non_numeric_or_bool(coefficient) -> None:
    with pytest.raises(TypeError):
        PeriodicDamageStateParams(DamageType.WEAPON, coefficient)  # type: ignore[arg-type]


@pytest.mark.parametrize("coefficient", [nan, inf, -inf, -0.1])
def test_periodic_damage_params_reject_non_finite_or_negative(coefficient) -> None:
    with pytest.raises(ValueError):
        PeriodicDamageStateParams(DamageType.STRATEGY, coefficient)


def test_periodic_recovery_params_accept_zero_and_positive_ints() -> None:
    assert PeriodicRecoveryStateParams(0).amount == 0
    assert PeriodicRecoveryStateParams(25).amount == 25


@pytest.mark.parametrize("amount", [True, 1.5, "1", None])
def test_periodic_recovery_params_reject_non_int_or_bool(amount) -> None:
    with pytest.raises(TypeError):
        PeriodicRecoveryStateParams(amount)  # type: ignore[arg-type]


def test_periodic_recovery_params_reject_negative() -> None:
    with pytest.raises(ValueError):
        PeriodicRecoveryStateParams(-1)
