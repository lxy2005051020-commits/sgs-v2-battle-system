from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DamageDefensePolicy(str, Enum):
    NORMAL = "NORMAL"
    IGNORE_RELEVANT_TARGET_DEFENSE = "IGNORE_RELEVANT_TARGET_DEFENSE"


@dataclass(frozen=True, slots=True)
class DamageFormulaContext:
    defense_policy: DamageDefensePolicy = DamageDefensePolicy.NORMAL
