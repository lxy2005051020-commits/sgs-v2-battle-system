"""Reusable higher-of-force/intelligence policy; ties need an explicit rule."""
from dataclasses import dataclass

from .enums import DamageType
from .numeric_validation import validate_nonnegative_finite


@dataclass(frozen=True, slots=True)
class AttributeChoice:
    attribute: str
    value: float
    damage_type: DamageType


def higher_force_intelligence(force: float, intelligence: float, *,
                              tie_type: DamageType | None = None) -> AttributeChoice:
    force = validate_nonnegative_finite(force, "force")
    intelligence = validate_nonnegative_finite(intelligence, "intelligence")
    if tie_type is not None and not isinstance(tie_type, DamageType):
        raise TypeError("tie_type must be DamageType or None")
    if force == intelligence and tie_type is None:
        raise NotImplementedError("equal force/intelligence damage-type rule is unconfirmed")
    weapon = force > intelligence or (force == intelligence and tie_type is DamageType.WEAPON)
    return AttributeChoice("attack" if weapon else "intelligence",
        force if weapon else intelligence, DamageType.WEAPON if weapon else DamageType.STRATEGY)
