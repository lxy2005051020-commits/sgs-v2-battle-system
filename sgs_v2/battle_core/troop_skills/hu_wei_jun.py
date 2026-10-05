"""虎卫军 baseline; loss scaling is a user-authorized provisional rate model."""
from ..enums import LineupPosition, SpecialTroopId, TroopType
from ..pre_attack_reaction import PRE_ATTACK_REACTION_STATE_ID, TeamPreAttackReactionParams
from ..skill_definition import ApplyStateSkillEffectSpec, SkillDefinition, SkillTargetMode, SkillType
from ..skill_runtime import SkillRuntime, SkillSlot
from ..state_modifiers import ATTRIBUTE_BONUS_STATE_ID, AttributeBonusParams
from ..troop_skill_config import TroopSkillConfig

PROVISIONAL_LOSS_MODEL_KEY = "HUWEI_USER_PROVISIONAL_LOSS_RATE_POINTS_V1"


def _definition(initial_troops=()):
    return SkillDefinition("20154", "虎卫军", 1.0, SkillTargetMode.TEAM_COMMANDER,
        (ApplyStateSkillEffectSpec(PRE_ATTACK_REACTION_STATE_ID,
            TeamPreAttackReactionParams(initial_troops=initial_troops)),), skill_type=SkillType.TROOP)


def create_hu_wei_jun_definition():
    return _definition()


def resolve_definition(context, systems, owner):
    team = systems.target_system.allies(context, owner)
    if sum(u.lineup_position is LineupPosition.COMMANDER for u in team) != 1:
        raise ValueError("虎卫军 requires exactly one live canonical commander")
    return _definition(tuple((u.unit_id, u.troops) for u in team))


def resolve_commander_bonus(context, systems, owner):
    commander = next(u for u in systems.target_system.allies(context, owner)
        if u.lineup_position is LineupPosition.COMMANDER)
    if commander.name not in ("典韦", "许褚"):
        return None
    # The current catalog specifies 25; retain it rather than infer a level curve.
    return SkillDefinition("20154", "虎卫军", 1.0, SkillTargetMode.TEAM_COMMANDER,
        (ApplyStateSkillEffectSpec(ATTRIBUTE_BONUS_STATE_ID, AttributeBonusParams("defense", 25)),),
        skill_type=SkillType.TROOP)


SKILL = create_hu_wei_jun_definition()
CONFIG = TroopSkillConfig("20154", "虎卫军", TroopType.SHIELD, SpecialTroopId.HU_WEI_JUN,
    create_hu_wei_jun_definition, requires_provider_slot=True,
    definition_resolver=resolve_definition, supplemental_definition_resolver=resolve_commander_bonus)


def create_hu_wei_jun_runtime(owner_id, *, slot=SkillSlot.LEARNED_1, enabled=True):
    return SkillRuntime(SKILL, owner_id, slot, enabled)
