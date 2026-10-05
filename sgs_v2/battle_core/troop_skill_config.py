from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .context import BattleContext
from .enums import SpecialTroopId, TroopType
from .skill_definition import SkillDefinition
from .unit import UnitRuntime
from .scheduled_team_recovery import ScheduledTeamRecoverySpec


@dataclass(frozen=True, slots=True)
class TroopSkillConfig:
    """Static declaration consumed by the shared PRE_BATTLE admission owner."""

    skill_id: str
    name: str
    required_troop_type: TroopType
    target_special_troop_id: SpecialTroopId
    definition_factory: Callable[[], SkillDefinition]
    requires_provider_slot: bool = False
    definition_resolver: Callable[[BattleContext, object, UnitRuntime], SkillDefinition] | None = None
    supplemental_definition_resolver: Callable[[BattleContext, object, UnitRuntime], SkillDefinition | None] | None = None
    opening_definition_resolver: Callable[[BattleContext, object, UnitRuntime], SkillDefinition] | None = None
    scheduled_recovery_resolver: Callable[[BattleContext, object, UnitRuntime], ScheduledTeamRecoverySpec] | None = None
