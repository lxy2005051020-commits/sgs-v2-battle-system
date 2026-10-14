"""鱼鳞阵20836: user-approved base-rate reactions; attribute scaling deferred."""
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
from .after_damage_support import (AFTER_DAMAGE_SUPPORT_STATE_ID, AfterDamageSupportParams,
                                   register_after_damage_support_state)
from .official_state_catalog import OfficialStateId, OFFICIAL_STATE_CATALOG
from .state_definition import StateDefinition
from .stage11_state_params import ResistanceStateParams

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
                 "统率对治疗的缩放公式",
                 "属性缩放读取时点（开场快照或受击实时）")
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
    if not options.command_only:
        register_after_damage_support_state(context.states)
        entry = next(entry for entry in OFFICIAL_STATE_CATALOG if entry.state_id is OfficialStateId.BARRIER)
        definition = StateDefinition(entry.state_id.value, entry.name,
            frozenset({entry.category.value}), ResistanceStateParams)
        try:
            existing = context.states.get_definition(definition.state_id)
        except KeyError:
            context.states.register_definition(definition)
        else:
            if existing != definition:
                raise ValueError("incompatible official barrier schema")
    ref = SkillProviderRef(runtime.owner_id, runtime.skill_slot, YU_LIN_ZHEN_SKILL_ID)
    source = EffectSourceRef(SourceType.ACTIVE_SKILL, ref.owner_id, ref.skill_id, ref.skill_slot)
    bonus, probability, treatment_rate = LEVEL_RATES[options.level - 1]
    effects = [ApplyStateEffect(
            ATTRIBUTE_BONUS_STATE_ID, deputy.unit_id, ref.owner_id, ref.skill_id,
            runtime_params=AttributeBonusParams("defense", bonus), source_ref=source)
            for deputy in deputies]
    if not options.command_only:
        effects.extend(ApplyStateEffect(AFTER_DAMAGE_SUPPORT_STATE_ID, deputy.unit_id,
            ref.owner_id, ref.skill_id, runtime_params=AfterDamageSupportParams(probability, 1, 3,
                state_spec=ApplyStateSkillEffectSpec(OfficialStateId.BARRIER.value, ResistanceStateParams(1)),
                reject_existing_state=True), source_ref=source) for deputy in deputies)
        commander = next(unit for unit in systems.target_system.allies(context, provider, include_self=True)
                         if unit.lineup_position is LineupPosition.COMMANDER)
        effects.append(ApplyStateEffect(AFTER_DAMAGE_SUPPORT_STATE_ID, commander.unit_id,
            ref.owner_id, ref.skill_id, runtime_params=AfterDamageSupportParams(probability, 5,
                recovery_rate=treatment_rate), source_ref=source))
    for effect in effects:
        result = systems.effect_executor.execute(context, effect)
        systems.dependency_evaluation_support.add_dependency(
            StateNode(result.state_instance.instance_id), ProviderNode(ref))
    context.metadata.setdefault("yu_lin_admissions", {})[(ref.owner_id, ref.skill_slot)] = {
        "level": options.level, "mode": "COMMAND_ONLY" if options.command_only else "BASE_VALUE_REACTIONS",
        "deputy_ids": tuple(u.unit_id for u in deputies), "command_bonus": bonus,
        "omitted": OMITTED_BRANCHES if options.command_only else (), "deferred_rules": MISSING_RULES,
        "base_probability": probability, "base_treatment_rate": treatment_rate,
        "recovery_troops": "USER_CONFIRMED_PROVIDER_LIVE_AT_REACTION", "zero_loss_eligible": True,
        "barrier_duration": "NO_DESCRIPTION_LIMIT_UNTIL_CONSUMED_OR_FORMATION_PROVIDER_DEFEAT",
        "reaction_order": "AFTER_EXISTING_AFTERMATH_REACTIONS_ENGINEERING_MODEL",
        "provenance": "USER_APPROVED_BASE_VALUE_MODEL / ATTRIBUTE_SCALING_DEFERRED / NOT_GAMEPLAY_FROZEN"}
