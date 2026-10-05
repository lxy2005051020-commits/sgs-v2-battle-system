"""Level 10 reduction and independent 藤甲兵效果 from incoming burn."""
from ..context import BattleContext
from ..enums import DamageType, LineupPosition, SpecialTroopId, TroopType
from ..official_state_catalog import OfficialStateId
from ..state_application_reaction import APPLICATION_DAMAGE_REACTION_STATE_ID, ApplicationDamageReactionParams
from ..numeric_validation import validate_nonnegative_finite, validate_probability
from ..skill_definition import ApplyStateSkillEffectSpec, SkillDefinition, SkillTargetMode, SkillType
from ..skill_runtime import SkillRuntime, SkillSlot
from ..state_modifiers import INCOMING_DAMAGE_REDUCTION_STATE_ID, IncomingDamageReductionParams
from ..troop_skill_config import TroopSkillConfig
from ..unit import UnitRuntime


def calculate_teng_jia_reduction(combat_defense: float) -> float:
    """Return a ratio, without rounding or inventing a formula cap."""
    defense = validate_nonnegative_finite(combat_defense, "combat_defense")
    return .24 * (1.0 + (defense - 100.0) / 350.0)


def _definition(rate: float, burn_coefficient: float = 3.0) -> SkillDefinition:
    # Unsupported out-of-range formula values fail before admission mutation.
    validate_probability(rate, "reduction_rate")
    return SkillDefinition("20095", "藤甲兵", 1.0, SkillTargetMode.FIXED_ALL_TEAM, (
        ApplyStateSkillEffectSpec(INCOMING_DAMAGE_REDUCTION_STATE_ID,
            IncomingDamageReductionParams(DamageType.WEAPON, rate)),
        ApplyStateSkillEffectSpec(APPLICATION_DAMAGE_REACTION_STATE_ID,
            ApplicationDamageReactionParams(OfficialStateId.BURN.value, burn_coefficient)),
    ), skill_type=SkillType.TROOP)


def create_teng_jia_bing_definition() -> SkillDefinition:
    """Canonical level-10 template at 100 defense; admission resolves the holder."""
    return _definition(.24)


def resolve_definition(context: BattleContext, systems: object, owner: UnitRuntime) -> SkillDefinition:
    commander = next((u for u in context.units.values() if u.team_id == owner.team_id
                      and u.lineup_position is LineupPosition.COMMANDER), None)
    coefficient = 2.5 if commander is not None and commander.name == "兀突骨" else 3.0
    return _definition(calculate_teng_jia_reduction(systems.attribute_system.get_defense(context, owner)), coefficient)


SKILL = create_teng_jia_bing_definition()
CONFIG = TroopSkillConfig("20095", "藤甲兵", TroopType.SHIELD, SpecialTroopId.TENG_JIA_BING,
    create_teng_jia_bing_definition, requires_provider_slot=True, definition_resolver=resolve_definition)


def create_teng_jia_bing_runtime(owner_id: str, *, slot: SkillSlot = SkillSlot.LEARNED_1,
                                 enabled: bool = True) -> SkillRuntime:
    """Create the level-10 troop skill runtime."""
    return SkillRuntime(SKILL, owner_id, slot, enabled)
