from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .context import BattleContext
from .enums import SpecialTroopId, TroopType
from .skill_definition import SkillDefinition
from .unit import UnitRuntime


@dataclass(frozen=True, slots=True)
class TroopSkillConfig:
    """Static declaration consumed by the shared PRE_BATTLE admission owner."""

    skill_id: str
    name: str
    required_troop_type: TroopType
    target_special_troop_id: SpecialTroopId
    definition_factory: Callable[[], SkillDefinition]
    definition_resolver: Callable[[BattleContext, object, UnitRuntime], SkillDefinition] | None = None
    opening_definition_resolver: Callable[[BattleContext, object, UnitRuntime], SkillDefinition] | None = None
