"""大戟士 full-level baseline including the Zhang He commander branch."""
from ..enums import DamageType, LineupPosition, SpecialTroopId, TroopType
from ..normal_attack_followup import FollowupTargetMode, NormalAttackFollowupParams, ProbabilisticComboParams, NORMAL_ATTACK_FOLLOWUP_STATE_ID
from ..official_state_catalog import OfficialStateId
from ..skill_definition import ApplyStateSkillEffectSpec, DamageSkillEffectSpec, SkillDefinition, SkillTargetMode, SkillType
from ..skill_runtime import SkillRuntime, SkillSlot
from ..state_modifiers import ATTRIBUTE_BONUS_STATE_ID, AttributeBonusParams
from ..troop_skill_config import TroopSkillConfig


def _zhang_he_commands(context, owner) -> bool:
    return any(u.team_id == owner.team_id and u.lineup_position is LineupPosition.COMMANDER
               and u.name == "张郃" for u in context.units.values())


def _definition(probability: float) -> SkillDefinition:
    return SkillDefinition("20125", "大戟士", 1.0, SkillTargetMode.FIXED_ALL_TEAM, (
        ApplyStateSkillEffectSpec(ATTRIBUTE_BONUS_STATE_ID, AttributeBonusParams("attack", 14)),
        ApplyStateSkillEffectSpec(NORMAL_ATTACK_FOLLOWUP_STATE_ID,
            NormalAttackFollowupParams(probability, DamageSkillEffectSpec(DamageType.WEAPON, 1.22),
                FollowupTargetMode.RANDOM_ENEMY)),
    ), skill_type=SkillType.TROOP)


def create_da_ji_shi_definition() -> SkillDefinition:
    return _definition(.35)


def resolve_definition(context, systems, owner) -> SkillDefinition:
    return _definition(.40 if _zhang_he_commands(context, owner) else .35)


def resolve_supplemental_definition(context, systems, owner) -> SkillDefinition | None:
    if not _zhang_he_commands(context, owner):
        return None
    return SkillDefinition("20125", "大戟士", 1.0, SkillTargetMode.TEAM_COMMANDER, (
        ApplyStateSkillEffectSpec(OfficialStateId.COMBO.value, ProbabilisticComboParams(probability=.45)),
    ), skill_type=SkillType.TROOP)


SKILL = create_da_ji_shi_definition()
CONFIG = TroopSkillConfig("20125", "大戟士", TroopType.SPEAR, SpecialTroopId.DA_JI_SHI,
    create_da_ji_shi_definition, requires_provider_slot=True, definition_resolver=resolve_definition,
    supplemental_definition_resolver=resolve_supplemental_definition)


def create_da_ji_shi_runtime(owner_id: str, *, slot: SkillSlot = SkillSlot.LEARNED_1,
                            enabled: bool = True) -> SkillRuntime:
    return SkillRuntime(SKILL, owner_id, slot, enabled)
