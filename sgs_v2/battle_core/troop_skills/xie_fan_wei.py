"""解烦卫 full-level declaration; higher-attribute semantics authorized by user."""
from ..enums import DamageType, SpecialTroopId, TroopType
from ..normal_attack_followup import (BranchedNormalAttackFollowupParams,
    FollowupTargetMode, NORMAL_ATTACK_FOLLOWUP_STATE_ID)
from ..skill_definition import (ApplyStateSkillEffectSpec, DamageSkillEffectSpec,
    SkillDefinition, SkillTargetMode, SkillType)
from ..skill_runtime import SkillRuntime, SkillSlot
from ..stage10_state_params import RecoveryPotencyContext
from ..state_modifiers import ATTRIBUTE_BONUS_STATE_ID, AttributeBonusParams
from ..troop_skill_config import TroopSkillConfig
from ..priority_target_system import FastestTargetSystem
from ..stage11_state_runtime import Stage11DamageFamily


def _definition(potency=None, performer_id=None):
    return SkillDefinition("20248", "解烦卫", 1.0, SkillTargetMode.FIXED_ALL_TEAM, (
        ApplyStateSkillEffectSpec(ATTRIBUTE_BONUS_STATE_ID, AttributeBonusParams("speed", 36)),
        ApplyStateSkillEffectSpec(NORMAL_ATTACK_FOLLOWUP_STATE_ID,
            BranchedNormalAttackFollowupParams(.30, DamageSkillEffectSpec(DamageType.WEAPON, .36),
                FollowupTargetMode.RANDOM_ENEMY, recovery_potency=potency,
                fixed_performer_id=performer_id, higher_attribute_damage=True, speed_damage_ratio=.40,
                tie_damage_type=DamageType.WEAPON, recovery_from_performer=True,
                live_recovery_attribute=True,
                damage_family=Stage11DamageFamily.COMMAND_XIEFANWEI)),
    ), skill_type=SkillType.TROOP)


def create_xie_fan_wei_definition():
    return _definition()


def resolve_definition(context, systems, owner):
    # Fix the performer before combat. A uniform +36 cannot change this ordering.
    fastest = FastestTargetSystem(systems.target_system).fastest_allies(context, owner, systems.attribute_system)
    performer = min(fastest, key=lambda unit: (unit.lineup_position, unit.unit_id))
    # Only troops remain frozen; healing reads the performer's live final attributes.
    return _definition(RecoveryPotencyContext(base_rate=.72,
        source_troops_at_application=performer.troops), performer.unit_id)


SKILL = create_xie_fan_wei_definition()
CONFIG = TroopSkillConfig("20248", "解烦卫", TroopType.SPEAR, SpecialTroopId.XIE_FAN_WEI,
    create_xie_fan_wei_definition, requires_provider_slot=True, definition_resolver=resolve_definition)


def create_xie_fan_wei_runtime(owner_id: str, *, slot: SkillSlot = SkillSlot.LEARNED_1,
                               enabled: bool = True) -> SkillRuntime:
    return SkillRuntime(SKILL, owner_id, slot, enabled)
