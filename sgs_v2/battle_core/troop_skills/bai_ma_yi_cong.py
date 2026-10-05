"""白马义从: full-level baseline; commander scaling deliberately unspecified."""
from ..enums import BattlePhase, SpecialTroopId, TroopType
from ..official_state_catalog import OfficialStateId
from ..skill_definition import ApplyStateSkillEffectSpec, SkillDefinition, SkillTargetMode, SkillType
from ..skill_runtime import SkillRuntime, SkillSlot
from ..stage11_state_params import Stage11TimedFlagParams
from ..state_modifiers import ACTIVATION_RATE_BONUS_STATE_ID, ActivationRateBonusParams
from ..troop_skill_config import TroopSkillConfig

COMMANDER_SCALING = None  # User-deferred, not a zero-valued formula.
COMMANDER_DURATION = None  # Whether both effects extend to R4 remains unconfirmed.


def create_bai_ma_yi_cong_definition() -> SkillDefinition:
    return SkillDefinition(
        skill_id="20075", name="白马义从", activation_rate=1.0,
        target_mode=SkillTargetMode.FIXED_ALL_TEAM, skill_type=SkillType.TROOP,
        effect_specs=(
            ApplyStateSkillEffectSpec(
                OfficialStateId.FIRST_STRIKE.value, Stage11TimedFlagParams(),
                expires_round=3, expires_phase=BattlePhase.ROUND_START.value,
            ),
            ApplyStateSkillEffectSpec(
                ACTIVATION_RATE_BONUS_STATE_ID, ActivationRateBonusParams(SkillType.ACTIVE, 0.10),
                expires_round=3, expires_phase=BattlePhase.ROUND_START.value,
            ),
        ),
    )


SKILL = create_bai_ma_yi_cong_definition()
CONFIG = TroopSkillConfig("20075", "白马义从", TroopType.BOW, SpecialTroopId.BAI_MA_YI_CONG,
                         create_bai_ma_yi_cong_definition)


def create_bai_ma_yi_cong_runtime(owner_id: str, *, slot: SkillSlot = SkillSlot.LEARNED_1,
                                 enabled: bool = True) -> SkillRuntime:
    return SkillRuntime(SKILL, owner_id=owner_id, skill_slot=slot, enabled=enabled)
