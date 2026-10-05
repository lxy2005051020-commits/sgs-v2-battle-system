"""锦帆军 current-text candidate; Research formula admission remains closed.

Official 2026-04-29 text establishes 45%, 64%, 110%, 30%, and 6%.
The attack-dependent DOT rate and Gan Ning highest-attribute probability are
unconfirmed. Never replace either formula with its nominal text value.
"""
from ..enums import DamageType, LineupPosition, SpecialTroopId, TroopType
from ..normal_attack_followup import (
    FollowupTargetMode, NormalAttackFollowupParams, TargetStateBranchFollowup,
    NORMAL_ATTACK_FOLLOWUP_STATE_ID,
)
from ..official_state_catalog import OfficialStateId
from ..skill_definition import ApplyStateSkillEffectSpec, DamageSkillEffectSpec, SkillDefinition, SkillTargetMode, SkillType
from ..skill_runtime import SkillRuntime, SkillSlot
from ..stage9_integerization import ExactRatio
from ..troop_skill_config import TroopSkillConfig


def create_jin_fan_jun_definition() -> SkillDefinition:
    return SkillDefinition("20152", "锦帆军", 1.0, SkillTargetMode.FIXED_ALL_TEAM, (
        ApplyStateSkillEffectSpec(NORMAL_ATTACK_FOLLOWUP_STATE_ID,
            NormalAttackFollowupParams(.45, TargetStateBranchFollowup(
                OfficialStateId.ROUT.value, DamageSkillEffectSpec(DamageType.WEAPON, 1.10),
                duration=2, recovery_ratio=ExactRatio(30, 100)),
                FollowupTargetMode.INHERIT_ACTUAL_TARGET)),
    ), skill_type=SkillType.TROOP)


def resolve_definition(context, systems, owner) -> SkillDefinition:
    gan_ning_commands = any(u.team_id == owner.team_id and u.name == "甘宁"
        and u.lineup_position is LineupPosition.COMMANDER for u in context.units.values())
    if gan_ning_commands:
        raise NotImplementedError("锦帆军: 甘宁最高属性触发概率公式、溃逃武力缩放公式尚未确认")
    raise NotImplementedError("锦帆军: 溃逃武力缩放公式尚未确认")


SKILL = create_jin_fan_jun_definition()
CONFIG = TroopSkillConfig("20152", "锦帆军", TroopType.BOW, SpecialTroopId.JIN_FAN_JUN,
    create_jin_fan_jun_definition, requires_provider_slot=True, definition_resolver=resolve_definition)


def create_jin_fan_jun_runtime(owner_id: str, *, slot: SkillSlot = SkillSlot.LEARNED_1,
                               enabled: bool = True) -> SkillRuntime:
    return SkillRuntime(SKILL, owner_id, slot, enabled)
