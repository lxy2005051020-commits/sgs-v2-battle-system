"""雁行阵20862: user-approved base-value model; attribute scaling deferred."""
from dataclasses import dataclass
from .dependency_evaluation import ProviderNode, StateNode
from .effects import ApplyStateEffect, EffectSourceRef
from .enums import LineupPosition, TroopType
from .operation_identity import SourceType
from .provider_identity import SkillProviderRef
from .round_team_transfer import (ROUND_TEAM_TRANSFER_STATE_ID, RoundTeamTransferParams,
                                 register_round_team_transfer_state)
from .skill_definition import ApplyStateSkillEffectSpec, SkillDefinition, SkillTargetMode, SkillType
from .skill_runtime import SkillRuntime, SkillSlot
from .state_modifiers import register_modifier_state_definitions
from .damage_rate_modifier import register_damage_rate_state
from .state_runtime_params import StateRuntimeParams

YAN_XING_ZHEN_SKILL_ID = "20862"
YAN_XING_ZHEN_NAME = "雁行阵"
YAN_XING_ZHEN_APPLICABLE_TROOPS = tuple(TroopType)
LEVEL_RATES = ((.175, 5.), (.194, 5.6), (.214, 6.1), (.233, 6.7), (.253, 7.2),
               (.272, 7.8), (.292, 8.3), (.311, 8.9), (.331, 9.4), (.35, 10.))
PROVENANCE = "USER_APPROVED_BASE_VALUE_MODEL / ATTRIBUTE_SCALING_DEFERRED / NOT_GAMEPLAY_FROZEN"


@dataclass(frozen=True, slots=True)
class YanXingOptions(StateRuntimeParams):
    level: int = 10

    def __post_init__(self):
        if type(self.level) is not int or not 1 <= self.level <= 10:
            raise ValueError("雁行阵 level must be an integer in [1, 10]")


def create_yan_xing_zhen_definition(level: int = 10) -> SkillDefinition:
    return SkillDefinition(YAN_XING_ZHEN_SKILL_ID, YAN_XING_ZHEN_NAME, 1., SkillTargetMode.SELF,
        (ApplyStateSkillEffectSpec(ROUND_TEAM_TRANSFER_STATE_ID, YanXingOptions(level)),),
        skill_type=SkillType.FORMATION)


SKILL = create_yan_xing_zhen_definition()


def create_yan_xing_zhen_runtime(owner_id: str, *, slot: SkillSlot = SkillSlot.LEARNED_1,
        level: int = 10, enabled: bool = True) -> SkillRuntime:
    return SkillRuntime(create_yan_xing_zhen_definition(level), owner_id, slot, enabled)


def validate_yan_xing_zhen(context, runtime):
    specs = runtime.definition.effect_specs
    options = specs[0].runtime_params if len(specs) == 1 and isinstance(specs[0], ApplyStateSkillEffectSpec) else None
    if not isinstance(options, YanXingOptions) or runtime.definition != create_yan_xing_zhen_definition(options.level):
        raise ValueError("unsupported 雁行阵 canonical definition")
    provider = context.get_unit(runtime.owner_id)
    team = [u for u in context.units.values() if u.team_id == provider.team_id]
    if (len(team) != 3 or not all(u.is_alive for u in team)
            or sorted(u.lineup_position or 0 for u in team) != list(LineupPosition)):
        raise ValueError("雁行阵 requires a complete living three-unit lineup")


def install_yan_xing_zhen(context, systems, runtime):
    loaded = context.skill_runtimes.get(runtime.owner_id, runtime.skill_slot)
    if loaded is None or runtime.skill_slot is None:
        raise ValueError("雁行阵 requires a canonical loaded runtime and provider slot")
    validate_yan_xing_zhen(context, loaded)
    level = loaded.definition.effect_specs[0].runtime_params.level
    probability, amount = LEVEL_RATES[level - 1]
    register_round_team_transfer_state(context.states)
    register_modifier_state_definitions(context.states)
    register_damage_rate_state(context.states)
    ref = SkillProviderRef(runtime.owner_id, runtime.skill_slot, YAN_XING_ZHEN_SKILL_ID)
    result = systems.effect_executor.execute(context, ApplyStateEffect(
        ROUND_TEAM_TRANSFER_STATE_ID, ref.owner_id, ref.owner_id, ref.skill_id,
        runtime_params=RoundTeamTransferParams(probability, amount),
        source_ref=EffectSourceRef(SourceType.ACTIVE_SKILL, ref.owner_id, ref.skill_id, ref.skill_slot)))
    systems.dependency_evaluation_support.add_dependency(StateNode(result.state_instance.instance_id), ProviderNode(ref))
    context.metadata.setdefault("yan_xing_admissions", {})[(ref.owner_id, ref.skill_slot)] = {
        "level": level, "probability": probability, "amount_per_enemy": amount,
        "provenance": PROVENANCE, "timing": "USER_APPROVED_ROUND_START",
        "tie_break": "COMMANDER_DEPUTY_1_DEPUTY_2", "expiry": "CURRENT_ROUND_END",
        "deferred": ["probability_command_scaling", "steal_amount_command_scaling"],
        "transfer_model": "USER_APPROVED_COMPLETE_TRANSFER_WITHOUT_ATTRIBUTE_SCALING",
        "snapshot_rule": "preserve_potency_rebind_provider; dynamic_reduction_snapshot_at_transfer",
        "same_kind_rule": "replace_same_dimension; no_stacking; original_target_immunity"}
