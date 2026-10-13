"""鱼鳞阵20836: confirmed deputy command bonus; full model fails closed.

Static base probabilities are evidence, never substitutes for unknown scaling.
"""
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .context import BattleContext
from .dependency_evaluation import ProviderNode, StateNode
from .effects import ApplyStateEffect, EffectSourceRef
from .enums import LineupPosition, TroopType
from .operation_identity import SourceType
from .provider_identity import SkillProviderRef
from .skill_definition import ApplyStateSkillEffectSpec, SkillDefinition, SkillTargetMode, SkillType
from .skill_runtime import SkillRuntime, SkillSlot
from .state_modifiers import ATTRIBUTE_BONUS_STATE_ID, AttributeBonusParams, register_modifier_state_definitions
from .state_runtime_params import StateRuntimeParams

if TYPE_CHECKING:
    from .battle_systems import BattleSystems

YU_LIN_ZHEN_SKILL_ID = "20836"
YU_LIN_ZHEN_NAME = "鱼鳞阵"
YU_LIN_ZHEN_APPLICABLE_TROOPS = tuple(TroopType)
# Exact static display rows: (deputy command, base probability, base treatment rate).
LEVEL_RATES = ((27.5, .125, .15), (30.6, .139, .167), (33.6, .153, .183),
               (36.7, .167, .20), (39.7, .181, .217), (42.8, .194, .233),
               (45.8, .208, .25), (48.9, .222, .267), (51.9, .236, .283),
               (55., .25, .30))
MISSING_RULES = ("主将武力和统率对触发概率的缩放公式",
                 "统率对治疗的缩放公式及治疗来源",
                 "属性读取时点（开场快照或受击实时）")
OMITTED_BRANCHES = ("DEPUTY_BARRIER_AFTER_DAMAGE_ROUNDS_1_3",
                    "COMMANDER_RECOVERY_AFTER_DAMAGE_FROM_ROUND_5")


@dataclass(frozen=True, slots=True)
class YuLinOptions(StateRuntimeParams):
    level: int = 10
    command_only: bool = False

    def __post_init__(self) -> None:
        if type(self.level) is not int or not 1 <= self.level <= 10:
            raise ValueError("鱼鳞阵 level must be an integer in [1, 10]")
        if type(self.command_only) is not bool:
            raise TypeError("command_only must be bool")


def create_yu_lin_zhen_definition(level: int = 10, *, command_only: bool = False) -> SkillDefinition:
    # Options are an installer declaration, not a directly executable state spec.
    # This is the existing role-aware FormationSkillConfig installer convention.
    return SkillDefinition(YU_LIN_ZHEN_SKILL_ID, YU_LIN_ZHEN_NAME, 1.0,
        SkillTargetMode.TEAM_NON_COMMANDERS,
        (ApplyStateSkillEffectSpec(ATTRIBUTE_BONUS_STATE_ID, YuLinOptions(level, command_only)),),
        skill_type=SkillType.FORMATION)


SKILL = create_yu_lin_zhen_definition()


def create_yu_lin_zhen_runtime(owner_id: str, *, slot: SkillSlot = SkillSlot.LEARNED_1,
        level: int = 10, command_only: bool = False, enabled: bool = True) -> SkillRuntime:
    return SkillRuntime(create_yu_lin_zhen_definition(level, command_only=command_only),
                        owner_id, slot, enabled)


def validate_yu_lin_zhen(context: BattleContext, runtime: SkillRuntime) -> None:
    """Pure validation shared by global preflight and direct installation."""
    specs = runtime.definition.effect_specs
    options = (specs[0].runtime_params if len(specs) == 1
               and isinstance(specs[0], ApplyStateSkillEffectSpec) else None)
    if not isinstance(options, YuLinOptions) or runtime.definition != create_yu_lin_zhen_definition(
            options.level, command_only=options.command_only):
        raise ValueError("unsupported 鱼鳞阵 canonical definition")
    if not options.command_only:
        raise NotImplementedError("鱼鳞阵完整模式缺少已确认规则：" + "；".join(MISSING_RULES)
            + "。仅统率模式必须显式设置 command_only=True；不会用基础概率代替缩放。")
    provider = context.get_unit(runtime.owner_id)
    team = [unit for unit in context.units.values() if unit.team_id == provider.team_id]
    if (len(team) != 3 or not all(unit.is_alive for unit in team)
            or sorted(unit.lineup_position or 0 for unit in team) != list(LineupPosition)):
        raise ValueError("鱼鳞阵 requires a complete living three-unit lineup")


def install_yu_lin_zhen(context: BattleContext, systems: "BattleSystems", runtime: SkillRuntime) -> None:
    loaded = context.skill_runtimes.get(runtime.owner_id, runtime.skill_slot)
    if loaded is None or runtime.skill_slot is None:
        raise ValueError("鱼鳞阵 requires a canonical loaded runtime and provider slot")
    validate_yu_lin_zhen(context, loaded)
    options = loaded.definition.effect_specs[0].runtime_params
    provider = context.get_unit(runtime.owner_id)
    deputies = sorted(systems.target_system.allies(context, provider, include_self=True),
                      key=lambda unit: unit.lineup_position)[1:]
    register_modifier_state_definitions(context.states)
    ref = SkillProviderRef(runtime.owner_id, runtime.skill_slot, YU_LIN_ZHEN_SKILL_ID)
    source = EffectSourceRef(SourceType.ACTIVE_SKILL, ref.owner_id, ref.skill_id, ref.skill_slot)
    bonus, probability, treatment_rate = LEVEL_RATES[options.level - 1]
    for deputy in deputies:
        result = systems.effect_executor.execute(context, ApplyStateEffect(
            ATTRIBUTE_BONUS_STATE_ID, deputy.unit_id, ref.owner_id, ref.skill_id,
            runtime_params=AttributeBonusParams("defense", bonus), source_ref=source))
        systems.dependency_evaluation_support.add_dependency(
            StateNode(result.state_instance.instance_id), ProviderNode(ref))
    context.metadata.setdefault("yu_lin_admissions", {})[(ref.owner_id, ref.skill_slot)] = {
        "level": options.level, "mode": "COMMAND_ONLY", "deputy_ids": tuple(u.unit_id for u in deputies),
        "command_bonus": bonus, "omitted": OMITTED_BRANCHES, "missing_rules": MISSING_RULES,
        "static_base_probability_not_executed": probability,
        "static_base_treatment_rate_not_executed": treatment_rate,
        "provenance": "STATIC_DESCRIPTION / USER_APPROVED_PARTIAL / NOT_GAMEPLAY_FROZEN"}
