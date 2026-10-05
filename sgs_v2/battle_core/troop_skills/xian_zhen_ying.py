"""陷阵营 baseline; Gao Shun commander enhancement is explicitly user-deferred."""
from ..enums import BattlePhase, SpecialTroopId, TroopType
from ..context import BattleContext
from ..unit import UnitRuntime
from ..official_state_catalog import OfficialStateId
from ..skill_definition import ApplyStateSkillEffectSpec, SkillDefinition, SkillTargetMode, SkillType
from ..skill_runtime import SkillRuntime, SkillSlot
from ..stage10_state_params import FirstAidStateParams, RecoveryPotencyContext
from ..state_generation import PersistentLifecycleWindow
from ..state_modifiers import ATTRIBUTE_BONUS_STATE_ID, AttributeBonusParams
from ..troop_skill_config import TroopSkillConfig

GAO_SHUN_COMMANDER_ENHANCEMENT = None


def _definition(potency: RecoveryPotencyContext) -> SkillDefinition:
    return SkillDefinition("20096", "陷阵营", 1.0, SkillTargetMode.FIXED_ALL_TEAM, (
        ApplyStateSkillEffectSpec(ATTRIBUTE_BONUS_STATE_ID, AttributeBonusParams("attack", 22)),
        ApplyStateSkillEffectSpec(ATTRIBUTE_BONUS_STATE_ID, AttributeBonusParams("defense", 22)),
        ApplyStateSkillEffectSpec(OfficialStateId.FIRST_AID.value,
            FirstAidStateParams(probability=.40, recovery_potency_context=potency,
                lifecycle_window=PersistentLifecycleWindow(BattlePhase.PRE_BATTLE.value, 0, 1, 3)),
            expires_round=4, expires_phase=BattlePhase.ROUND_START.value),
    ), skill_type=SkillType.TROOP)


def create_xian_zhen_ying_definition() -> SkillDefinition:
    # Canonical template only: admission resolves the complete source snapshot.
    return _definition(RecoveryPotencyContext(base_rate=.60))


def resolve_definition(context: BattleContext, systems: object, owner: UnitRuntime) -> SkillDefinition:
    return _definition(RecoveryPotencyContext(base_rate=.60,
        source_troops_at_application=owner.troops,
        source_attribute_at_application=systems.attribute_system.get_intelligence(context, owner)))


SKILL = create_xian_zhen_ying_definition()
CONFIG = TroopSkillConfig("20096", "陷阵营", TroopType.SHIELD, SpecialTroopId.XIAN_ZHEN_YING,
                         create_xian_zhen_ying_definition, definition_resolver=resolve_definition)


def create_xian_zhen_ying_runtime(owner_id: str, *, slot: SkillSlot = SkillSlot.LEARNED_1,
                                 enabled: bool = True) -> SkillRuntime:
    return SkillRuntime(SKILL, owner_id, slot, enabled)
