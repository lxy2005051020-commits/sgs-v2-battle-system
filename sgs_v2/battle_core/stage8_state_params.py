from __future__ import annotations

from dataclasses import dataclass

from .numeric_validation import validate_nonnegative_finite, validate_probability
from .state_runtime_params import StateRuntimeParams


@dataclass(frozen=True, slots=True)
class Stage8ProbabilityParams(StateRuntimeParams):
    probability: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "probability",
            validate_probability(self.probability),
        )


@dataclass(frozen=True, slots=True)
class Stage8ModifierParams(StateRuntimeParams):
    operand: float
    probability: float = 1.0

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "operand",
            validate_nonnegative_finite(self.operand, "modifier operand"),
        )
        object.__setattr__(
            self,
            "probability",
            validate_probability(self.probability),
        )


@dataclass(frozen=True, slots=True)
class Stage8PierceParams(StateRuntimeParams):
    rate: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "rate",
            validate_probability(self.rate, "pierce rate"),
        )
