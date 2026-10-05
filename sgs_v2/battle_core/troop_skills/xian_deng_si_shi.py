"""先登死士 full-level baseline, with user-supplied fitted command scaling."""
from decimal import Decimal, ROUND_HALF_UP

from ..enums import TroopType, SpecialTroopId, LineupPosition
from ..numeric_validation import validate_nonnegative_finite
from ..official_state_catalog import OfficialStateId
from ..skill_definition import SkillDefinition, SkillTargetMode, SkillType, ApplyStateSkillEffectSpec
from ..skill_runtime import SkillRuntime, SkillSlot
from ..troop_skill_config import TroopSkillConfig
from ..selective_state_immunity import SELECTIVE_IMMUNITY_STATE_ID, SelectiveStateImmunityParams
from ..damage_received_reaction import DAMAGE_RECEIVED_REACTION_STATE_ID, DamageReceivedReactionParams

USER_FIT_MODEL_KEY = "XIANDENG_USER_OPENING_COMMAND_FIT_V1"


def _command(value):
    return Decimal(str(validate_nonnegative_finite(value, "opening_command")))


def calculate_trigger_probability(command: float) -> float:
    x = _command(command)
    if x <= 500:
        return float(Decimal("0.60") + Decimal("0.035") * x / 100)
    if x < 800:
        return float(Decimal("0.775") + Decimal("0.06") * (x - 500) / 100)
    return .95


def calculate_steal_amount(command: float) -> int:
    x = _command(command)
    raw = 21 * (1 + x / 1300)
    if raw >= 31:
        return 31
    return min(31, int(raw.quantize(Decimal(1), rounding=ROUND_HALF_UP)))


def _definition(command=0, max_stacks=4):
    return SkillDefinition("20246", "先登死士", 1.0, SkillTargetMode.FIXED_ALL_TEAM, (
        ApplyStateSkillEffectSpec(SELECTIVE_IMMUNITY_STATE_ID,
            SelectiveStateImmunityParams((OfficialStateId.AMBUSH.value,))),
        ApplyStateSkillEffectSpec(DAMAGE_RECEIVED_REACTION_STATE_ID,
            DamageReceivedReactionParams(calculate_trigger_probability(command), "defense",
                calculate_steal_amount(command), .03, max_stacks,
                source_attribute_at_application=command, scaling_model_key=USER_FIT_MODEL_KEY)),
    ), skill_type=SkillType.TROOP)


def create_xian_deng_si_shi_definition():
    return _definition()


def resolve_definition(context, systems, owner):
    commander = next((u for u in context.units.values() if u.team_id == owner.team_id
        and u.lineup_position is LineupPosition.COMMANDER), None)
    cap = 5 if commander is not None and commander.name in ("麹义", "麴义", "麯义", "鞠义") else 4
    # Capture once at PRE_BATTLE admission; subsequent attribute changes cannot rescale it.
    return _definition(systems.attribute_system.get_defense(context, owner), cap)


SKILL = create_xian_deng_si_shi_definition()
CONFIG = TroopSkillConfig("20246", "先登死士", TroopType.BOW, SpecialTroopId.XIAN_DENG_SI_SHI,
    create_xian_deng_si_shi_definition, requires_provider_slot=True, definition_resolver=resolve_definition)


def create_xian_deng_si_shi_runtime(owner_id: str, *, slot: SkillSlot = SkillSlot.LEARNED_1,
                                   enabled: bool = True) -> SkillRuntime:
    return SkillRuntime(SKILL, owner_id, slot, enabled)
