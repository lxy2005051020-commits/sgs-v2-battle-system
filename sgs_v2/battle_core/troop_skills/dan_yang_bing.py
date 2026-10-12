"""丹阳兵 level 10; generation ratio 1.0 confirmed by user 2026-10-12.

User correction: split generation equally among living teammates, round UP
per recipient; each unit owns its pool. Decay/absorption still round down.
"""
from ..enums import LineupPosition, SpecialTroopId, TroopType
from ..skill_definition import ApplyStateSkillEffectSpec, SkillDefinition, SkillTargetMode, SkillType
from ..skill_runtime import SkillRuntime, SkillSlot
from ..state_modifiers import ATTRIBUTE_BONUS_STATE_ID, AttributeBonusParams
from ..temporary_damage_pool import TEMPORARY_DAMAGE_POOL_STATE_ID, TemporaryDamagePoolParams
from ..troop_skill_config import TroopSkillConfig


def create_dan_yang_bing_definition():
    return SkillDefinition("20245", "丹阳兵", 1.0, SkillTargetMode.FIXED_ALL_TEAM,
        (ApplyStateSkillEffectSpec(ATTRIBUTE_BONUS_STATE_ID, AttributeBonusParams("defense", 36)),),
        skill_type=SkillType.TROOP)


def resolve_supplemental_definition(context, systems, owner):
    commander = next(u for u in context.units.values()
        if u.team_id == owner.team_id and u.lineup_position is LineupPosition.COMMANDER)
    return SkillDefinition("20245", "丹阳兵", 1.0, SkillTargetMode.FIXED_ALL_TEAM,
        (ApplyStateSkillEffectSpec(TEMPORARY_DAMAGE_POOL_STATE_ID,
            TemporaryDamagePoolParams(.40 if commander.name == "陶谦" else .36)),),
        skill_type=SkillType.TROOP)


SKILL = create_dan_yang_bing_definition()
CONFIG = TroopSkillConfig("20245", "丹阳兵", TroopType.SHIELD, SpecialTroopId.DAN_YANG_BING,
    create_dan_yang_bing_definition, requires_provider_slot=True,
    supplemental_definition_resolver=resolve_supplemental_definition)


def create_dan_yang_bing_runtime(owner_id, *, slot=SkillSlot.LEARNED_1, enabled=True):
    return SkillRuntime(SKILL, owner_id, slot, enabled)
