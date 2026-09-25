from __future__ import annotations

from dataclasses import dataclass

from .numeric_validation import validate_probability
from .stage9_integerization import ExactRatio
from .state_runtime_params import StateRuntimeParams


def _remaining(value: int | None, name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an int or None")
    if value < 0:
        raise ValueError(f"{name} cannot be negative")
    return value


def _flag(value: bool, name: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be a bool")
    return value


def _ratio01(value: ExactRatio, name: str) -> ExactRatio:
    if not isinstance(value, ExactRatio):
        raise TypeError(f"{name} must be an ExactRatio")
    if value.numerator < 0 or value.numerator > value.denominator:
        raise ValueError(f"{name} must be within [0, 1]")
    return value


@dataclass(frozen=True, slots=True)
class Stage11TimedFlagParams(StateRuntimeParams):
    remaining_action_starts: int | None = None
    is_suppressed: bool = False
    source_dependent: bool = False
    strength: float = 1.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "remaining_action_starts", _remaining(
            self.remaining_action_starts, "remaining_action_starts"
        ))
        _flag(self.is_suppressed, "is_suppressed")
        _flag(self.source_dependent, "source_dependent")
        if isinstance(self.strength, bool) or not isinstance(self.strength, (int, float)):
            raise TypeError("strength must be numeric")
        if float(self.strength) < 0.0:
            raise ValueError("strength cannot be negative")
        object.__setattr__(self, "strength", float(self.strength))


@dataclass(frozen=True, slots=True)
class EvasionStateParams(StateRuntimeParams):
    probability: float = 1.0
    remaining_action_starts: int | None = None
    is_suppressed: bool = False
    source_dependent: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "probability", validate_probability(self.probability))
        object.__setattr__(self, "remaining_action_starts", _remaining(
            self.remaining_action_starts, "remaining_action_starts"
        ))
        _flag(self.is_suppressed, "is_suppressed")
        _flag(self.source_dependent, "source_dependent")


@dataclass(frozen=True, slots=True)
class ResistanceStateParams(StateRuntimeParams):
    remaining_uses: int = 1
    remaining_action_starts: int | None = None
    is_suppressed: bool = False
    source_dependent: bool = False

    def __post_init__(self) -> None:
        if isinstance(self.remaining_uses, bool) or not isinstance(self.remaining_uses, int):
            raise TypeError("remaining_uses must be an int")
        if self.remaining_uses < 0:
            raise ValueError("remaining_uses cannot be negative")
        object.__setattr__(self, "remaining_action_starts", _remaining(
            self.remaining_action_starts, "remaining_action_starts"
        ))
        _flag(self.is_suppressed, "is_suppressed")
        _flag(self.source_dependent, "source_dependent")


@dataclass(frozen=True, slots=True)
class DisarmStateParams(StateRuntimeParams):
    block_probability: float = 1.0
    remaining_action_starts: int | None = None
    is_suppressed: bool = False
    source_dependent: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "block_probability", validate_probability(
                self.block_probability, "block_probability"
            )
        )
        object.__setattr__(self, "remaining_action_starts", _remaining(
            self.remaining_action_starts, "remaining_action_starts"
        ))
        _flag(self.is_suppressed, "is_suppressed")
        _flag(self.source_dependent, "source_dependent")


@dataclass(frozen=True, slots=True)
class StunStateParams(StateRuntimeParams):
    remaining_blocks: int = 1
    is_suppressed: bool = False
    source_dependent: bool = False

    def __post_init__(self) -> None:
        if isinstance(self.remaining_blocks, bool) or not isinstance(self.remaining_blocks, int):
            raise TypeError("remaining_blocks must be an int")
        if self.remaining_blocks < 0:
            raise ValueError("remaining_blocks cannot be negative")
        _flag(self.is_suppressed, "is_suppressed")
        _flag(self.source_dependent, "source_dependent")


@dataclass(frozen=True, slots=True)
class CriticalStateParams(StateRuntimeParams):
    chance: float = 0.0
    bonus: float = 1.0
    remaining_action_starts: int | None = None
    is_suppressed: bool = False
    source_dependent: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "chance", validate_probability(self.chance, "chance"))
        if isinstance(self.bonus, bool) or not isinstance(self.bonus, (int, float)):
            raise TypeError("bonus must be numeric")
        if float(self.bonus) < 0.0:
            raise ValueError("bonus cannot be negative")
        object.__setattr__(self, "bonus", float(self.bonus))
        object.__setattr__(self, "remaining_action_starts", _remaining(
            self.remaining_action_starts, "remaining_action_starts"
        ))
        _flag(self.is_suppressed, "is_suppressed")
        _flag(self.source_dependent, "source_dependent")


@dataclass(frozen=True, slots=True)
class DamageReductionPierceStateParams(StateRuntimeParams):
    rate: float = 0.0
    remaining_action_starts: int | None = None
    is_suppressed: bool = False
    source_dependent: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "rate", validate_probability(self.rate, "pierce rate"))
        object.__setattr__(self, "remaining_action_starts", _remaining(
            self.remaining_action_starts, "remaining_action_starts"
        ))
        _flag(self.is_suppressed, "is_suppressed")
        _flag(self.source_dependent, "source_dependent")


@dataclass(frozen=True, slots=True)
class LifeStealStateParams(StateRuntimeParams):
    ratio: ExactRatio = ExactRatio(0, 1)
    remaining_action_starts: int | None = None
    is_suppressed: bool = False
    source_dependent: bool = False

    def __post_init__(self) -> None:
        _ratio01(self.ratio, "ratio")
        object.__setattr__(self, "remaining_action_starts", _remaining(
            self.remaining_action_starts, "remaining_action_starts"
        ))
        _flag(self.is_suppressed, "is_suppressed")
        _flag(self.source_dependent, "source_dependent")


@dataclass(frozen=True, slots=True)
class AlertStateParams(StateRuntimeParams):
    remaining_uses: int = 1
    reduction_rate: ExactRatio = ExactRatio(0, 1)
    threshold: int = 600
    remaining_action_starts: int | None = None
    is_suppressed: bool = False
    source_dependent: bool = False
    provider_key: str | None = None

    def __post_init__(self) -> None:
        if isinstance(self.remaining_uses, bool) or not isinstance(self.remaining_uses, int):
            raise TypeError("remaining_uses must be an int")
        if self.remaining_uses < 0:
            raise ValueError("remaining_uses cannot be negative")
        _ratio01(self.reduction_rate, "reduction_rate")
        if isinstance(self.threshold, bool) or not isinstance(self.threshold, int):
            raise TypeError("threshold must be an int")
        if self.threshold < 0:
            raise ValueError("threshold cannot be negative")
        object.__setattr__(self, "remaining_action_starts", _remaining(
            self.remaining_action_starts, "remaining_action_starts"
        ))
        _flag(self.is_suppressed, "is_suppressed")
        _flag(self.source_dependent, "source_dependent")
        if self.provider_key is not None and (
            not isinstance(self.provider_key, str) or not self.provider_key.strip()
        ):
            raise ValueError("provider_key cannot be empty when provided")
