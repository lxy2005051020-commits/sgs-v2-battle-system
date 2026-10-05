"""无当飞军: stat aura plus one-shot opening poison through existing owners."""
from ..enums import BattlePhase, LineupPosition, SpecialTroopId, TroopType
from ..context import BattleContext
from ..unit import UnitRuntime
from ..numeric_validation import validate_nonnegative_finite
from ..official_state_catalog import OfficialStateId
from ..skill_definition import ApplyStateSkillEffectSpec, SkillDefinition, SkillTargetMode, SkillType
from ..skill_runtime import SkillRuntime, SkillSlot
from ..skill_runtime_registry import PersistentSourceSkillGate
from ..stage10_state_params import ContinuousDamageStateParams
from ..state_generation import PersistentLifecycleWindow
from ..state_modifiers import ATTRIBUTE_BONUS_STATE_ID, AttributeBonusParams
from ..troop_skill_config import TroopSkillConfig


def calculate_wu_dang_damage_rate(source_intelligence: float) -> float:
    """User-confirmed full-level Rate(I_A): no cap or intermediate rounding."""
    intelligence = validate_nonnegative_finite(source_intelligence, "source_intelligence")
    return 0.80 * (1.0 + max(0.0, intelligence - 350.0) / 1500.0)


def create_wu_dang_fei_jun_definition() -> SkillDefinition:
    return SkillDefinition("20100", "无当飞军", 1.0, SkillTargetMode.FIXED_ALL_TEAM, (
        ApplyStateSkillEffectSpec(ATTRIBUTE_BONUS_STATE_ID, AttributeBonusParams("defense", 22)),
        ApplyStateSkillEffectSpec(ATTRIBUTE_BONUS_STATE_ID, AttributeBonusParams("speed", 22)),
    ), skill_type=SkillType.TROOP)


def resolve_definition(context: BattleContext, systems: object, owner: UnitRuntime) -> SkillDefinition:
    # Fail before identity / state mutation if the opening formula has no source input.
    calculate_wu_dang_damage_rate(systems.attribute_system.get_intelligence(context, owner))
    return create_wu_dang_fei_jun_definition()


def resolve_opening_definition(context: BattleContext, systems: object, owner: UnitRuntime) -> SkillDefinition:
    commander = next((unit for unit in context.units.values() if unit.team_id == owner.team_id
                      and unit.lineup_position is LineupPosition.COMMANDER), None)
    all_enemies = commander is not None and commander.name == "王平"
    rate = calculate_wu_dang_damage_rate(systems.attribute_system.get_intelligence(context, owner))
    return SkillDefinition("20100", "无当飞军", 1.0,
        SkillTargetMode.FIXED_ALL_ENEMIES if all_enemies else SkillTargetMode.CHOOSE_N_RANDOM_ENEMIES,
        (ApplyStateSkillEffectSpec(OfficialStateId.POISON.value,
            ContinuousDamageStateParams(
                lifecycle_window=PersistentLifecycleWindow(BattlePhase.ROUND_START.value, 1, 1, 3),
                source_skill_gate=PersistentSourceSkillGate.query_skill_runtime(),
            ), expires_round=4, expires_phase=BattlePhase.ROUND_START.value,
            continuous_damage_coefficient=rate),),
        skill_type=SkillType.TROOP, target_count=None if all_enemies else 2)


SKILL = create_wu_dang_fei_jun_definition()
CONFIG = TroopSkillConfig("20100", "无当飞军", TroopType.BOW, SpecialTroopId.WU_DANG_FEI_JUN,
                         create_wu_dang_fei_jun_definition, definition_resolver=resolve_definition,
                         opening_definition_resolver=resolve_opening_definition)


def create_wu_dang_fei_jun_runtime(owner_id: str, *, slot: SkillSlot = SkillSlot.LEARNED_1,
                                  enabled: bool = True) -> SkillRuntime:
    return SkillRuntime(SKILL, owner_id, slot, enabled)
