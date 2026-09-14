from __future__ import annotations

from dataclasses import dataclass

from .stage9_integerization import ExactRatio
from .state_runtime_params import StateRuntimeParams


@dataclass(frozen=True, slots=True)
class CleaveStateParams(StateRuntimeParams):
    """Runtime parameters for Cleave state (e.g. state 690061)."""

    ratio: ExactRatio

    def __post_init__(self) -> None:
        if not isinstance(self.ratio, ExactRatio):
            raise TypeError(f"ratio must be an ExactRatio, got {type(self.ratio)}")
        if self.ratio.numerator < 0:
            raise ValueError("Cleave ratio cannot be negative")


@dataclass(frozen=True, slots=True)
class ChainStateParams(StateRuntimeParams):
    """Runtime parameters for Chain state (e.g. state 690071)."""

    ratio: ExactRatio

    def __post_init__(self) -> None:
        if not isinstance(self.ratio, ExactRatio):
            raise TypeError(f"ratio must be an ExactRatio, got {type(self.ratio)}")
        if self.ratio.numerator < 0:
            raise ValueError("Chain ratio cannot be negative")


@dataclass(frozen=True, slots=True)
class DamageShareStateParams(StateRuntimeParams):
    """Runtime parameters for Damage Share state."""

    sharer_id: str
    ratio: ExactRatio

    def __post_init__(self) -> None:
        if not isinstance(self.sharer_id, str) or not self.sharer_id.strip():
            raise ValueError("sharer_id cannot be empty or whitespace")
        if not isinstance(self.ratio, ExactRatio):
            raise TypeError(f"ratio must be an ExactRatio, got {type(self.ratio)}")
        if self.ratio.numerator < 0:
            raise ValueError("DamageShare ratio cannot be negative")


@dataclass(frozen=True, slots=True)
class DistributionStateParams(StateRuntimeParams):
    """Runtime parameters for Distribution state."""

    ratio: ExactRatio

    def __post_init__(self) -> None:
        if not isinstance(self.ratio, ExactRatio):
            raise TypeError(f"ratio must be an ExactRatio, got {type(self.ratio)}")
        if self.ratio.numerator < 0:
            raise ValueError("Distribution ratio cannot be negative")


@dataclass(frozen=True, slots=True)
class TauntStateParams(StateRuntimeParams):
    """Runtime parameters for Taunt state (e.g. state 690021)."""

    taunt_target_id: str | None = None

    def __post_init__(self) -> None:
        if self.taunt_target_id is not None:
            if not isinstance(self.taunt_target_id, str) or not self.taunt_target_id.strip():
                raise ValueError("taunt_target_id cannot be empty or whitespace when provided")


@dataclass(frozen=True, slots=True)
class GuardStateParams(StateRuntimeParams):
    """Runtime parameters for Guard state (e.g. state 690098).

    State_Owner: PROTECTED_TARGET / HOLDER
    Linked_Entity: PROTECTOR
    """

    protector_id: str | None = None

    def __post_init__(self) -> None:
        if self.protector_id is not None:
            if not isinstance(self.protector_id, str) or not self.protector_id.strip():
                raise ValueError("protector_id cannot be empty or whitespace when provided")


@dataclass(frozen=True, slots=True)
class CounterStateParams(StateRuntimeParams):
    """Runtime parameters for Counter state (e.g. state 690041)."""

    damage_rate: ExactRatio = ExactRatio(1, 1)

    def __post_init__(self) -> None:
        if not isinstance(self.damage_rate, ExactRatio):
            raise TypeError(f"damage_rate must be an ExactRatio, got {type(self.damage_rate)}")
        if self.damage_rate.numerator < 0:
            raise ValueError("Counter damage_rate cannot be negative")


@dataclass(frozen=True, slots=True)
class ComboStateParams(StateRuntimeParams):
    """Runtime parameters for Combo state (e.g. state 690081)."""
    pass
