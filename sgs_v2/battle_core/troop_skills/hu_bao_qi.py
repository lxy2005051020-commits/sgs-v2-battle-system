"""虎豹骑: full-level baseline; commander scaling deliberately unspecified."""
from ..enums import BattlePhase, SpecialTroopId, TroopType
from ..skill_definition import ApplyStateSkillEffectSpec, SkillDefinition, SkillTargetMode, SkillType
from ..skill_runtime import SkillRuntime, SkillSlot
from ..state_modifiers import (
    ACTIVATION_RATE_BONUS_STATE_ID, ATTRIBUTE_BONUS_STATE_ID,
    ActivationRateBonusParams, AttributeBonusParams,
)
from ..troop_skill_config import TroopSkillConfig

COMMANDER_SCALING = None  # User-deferred, not a zero-valued formula.


def create_hu_bao_qi_definition() -> SkillDefinition:
    return SkillDefinition(
        skill_id="20098", name="虎豹骑", activation_rate=1.0,
        target_mode=SkillTargetMode.FIXED_ALL_TEAM, skill_type=SkillType.TROOP,
        effect_specs=(
            ApplyStateSkillEffectSpec(ATTRIBUTE_BONUS_STATE_ID, AttributeBonusParams("attack", 40.0)),
            ApplyStateSkillEffectSpec(
                ACTIVATION_RATE_BONUS_STATE_ID, ActivationRateBonusParams(SkillType.ASSAULT, 0.10),
                expires_round=4, expires_phase=BattlePhase.ROUND_START.value,
            ),
        ),
    )


SKILL = create_hu_bao_qi_definition()
CONFIG = TroopSkillConfig("20098", "虎豹骑", TroopType.CAVALRY, SpecialTroopId.HU_BAO_QI,
                         create_hu_bao_qi_definition)


def create_hu_bao_qi_runtime(owner_id: str, *, slot: SkillSlot = SkillSlot.LEARNED_1,
                            enabled: bool = True) -> SkillRuntime:
    return SkillRuntime(SKILL, owner_id=owner_id, skill_slot=slot, enabled=enabled)
