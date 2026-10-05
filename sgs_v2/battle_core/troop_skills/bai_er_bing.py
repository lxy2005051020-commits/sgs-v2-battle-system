"""白毦兵 full-level baseline, with separate holder and physical performer."""
from ..enums import DamageType, LineupPosition, SpecialTroopId, TroopType
from ..normal_attack_followup import FollowupTargetMode, NormalAttackFollowupParams, NORMAL_ATTACK_FOLLOWUP_STATE_ID
from ..official_state_catalog import OfficialStateId
from ..skill_definition import ApplyStateSkillEffectSpec, DamageSkillEffectSpec, SkillDefinition, SkillTargetMode, SkillType
from ..skill_runtime import SkillRuntime, SkillSlot
from ..stage11_state_params import LifeStealStateParams
from ..stage9_integerization import ExactRatio
from ..troop_skill_config import TroopSkillConfig


def _definition(coefficient: float) -> SkillDefinition:
    return SkillDefinition("20099", "白毦兵", 1.0, SkillTargetMode.FIXED_ALL_TEAM, (
        ApplyStateSkillEffectSpec(OfficialStateId.STRATEGY_LIFESTEAL.value,
            LifeStealStateParams(ratio=ExactRatio(12, 100))),
        ApplyStateSkillEffectSpec(NORMAL_ATTACK_FOLLOWUP_STATE_ID,
            NormalAttackFollowupParams(.45, DamageSkillEffectSpec(DamageType.STRATEGY, coefficient),
                FollowupTargetMode.INHERIT_ACTUAL_TARGET)),
    ), skill_type=SkillType.TROOP)


def create_bai_er_bing_definition() -> SkillDefinition:
    return _definition(1.10)


def resolve_definition(context, systems, owner) -> SkillDefinition:
    commander = next((u for u in context.units.values() if u.team_id == owner.team_id
                      and u.lineup_position is LineupPosition.COMMANDER), None)
    return _definition(1.30 if commander is not None and commander.name == "陈到" else 1.10)


SKILL = create_bai_er_bing_definition()
CONFIG = TroopSkillConfig("20099", "白毦兵", TroopType.SPEAR, SpecialTroopId.BAI_ER_BING,
                         create_bai_er_bing_definition, requires_provider_slot=True, definition_resolver=resolve_definition)


def create_bai_er_bing_runtime(owner_id: str, *, slot: SkillSlot = SkillSlot.LEARNED_1,
                               enabled: bool = True) -> SkillRuntime:
    return SkillRuntime(SKILL, owner_id, slot, enabled)
