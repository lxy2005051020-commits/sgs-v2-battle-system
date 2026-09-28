from __future__ import annotations

from .context import BattleContext
from .numeric_validation import validate_probability


def resolve_probability(context: BattleContext, probability: float) -> bool:
    probability = validate_probability(probability)
    if probability == 0.0:
        return False
    if probability == 1.0:
        return True
    return context.random.chance(probability)
