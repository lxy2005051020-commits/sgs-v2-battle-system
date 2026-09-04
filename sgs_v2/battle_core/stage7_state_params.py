from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from .enums import DamageType
from .state_runtime_params import StateRuntimeParams


@dataclass(frozen=True, slots=True)
class PeriodicDamageStateParams(StateRuntimeParams):
    damage_type: DamageType
    coefficient: float

    def __post_init__(self) -> None:
        if not isinstance(self.damage_type, DamageType):
            raise TypeError("damage_type must be a DamageType")
        if isinstance(self.coefficient, bool) or not isinstance(
            self.coefficient, (int, float)
        ):
            raise TypeError("coefficient must be an int or float")
        try:
            normalized = float(self.coefficient)
        except OverflowError as exc:
            raise ValueError("coefficient must be finite") from exc
        if not isfinite(normalized):
            raise ValueError("coefficient must be finite")
        if normalized < 0:
            raise ValueError("coefficient must be >= 0")
        object.__setattr__(self, "coefficient", normalized)


@dataclass(frozen=True, slots=True)
class PeriodicRecoveryStateParams(StateRuntimeParams):
    amount: int

    def __post_init__(self) -> None:
        if isinstance(self.amount, bool) or not isinstance(self.amount, int):
            raise TypeError("amount must be an int")
        if self.amount < 0:
            raise ValueError("amount must be >= 0")
