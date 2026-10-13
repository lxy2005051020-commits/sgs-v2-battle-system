"""潜龙阵22040: exact static level rates and user-confirmed attribute snapshot."""
from typing import TYPE_CHECKING
from .context import BattleContext
from .commander_effect import (COMMANDER_EFFECT_ROLE_STATE_ID, CommanderEffectRoleParams,
                               register_commander_effect_role_state)
from .damage_rate_modifier import DAMAGE_RATE_STATE_ID, DamageRateParams, register_damage_rate_state
from .dependency_evaluation import ProviderNode, StateNode
from .effects import ApplyStateEffect, EffectSourceRef
from .enums import LineupPosition, TroopType
from .operation_identity import SourceType
from .provider_identity import SkillProviderRef
from .skill_definition import ApplyStateSkillEffectSpec, SkillDefinition, SkillTargetMode, SkillType
from .skill_runtime import SkillRuntime, SkillSlot
from .state_modifiers import ATTRIBUTE_BONUS_STATE_ID, AttributeBonusParams, register_modifier_state_definitions

if TYPE_CHECKING:
    from .battle_systems import BattleSystems

QIAN_LONG_ZHEN_SKILL_ID = "22040"
QIAN_LONG_ZHEN_NAME = "潜龙阵"
QIAN_LONG_ZHEN_APPLICABLE_TROOPS = tuple(TroopType)
# (ordinary commander attribute/deputy damage rate, reduced commander attribute rate)
LEVEL_RATES = ((.075, .025), (.083, .028), (.092, .031), (.10, .033),
               (.108, .036), (.117, .039), (.125, .042), (.133, .044),
               (.142, .047), (.15, .05))
ATTRIBUTES = ("attack", "intelligence", "speed", "defense")


def create_qian_long_zhen_definition(level: int = 10) -> SkillDefinition:
    if type(level) is not int or not 1 <= level <= 10:
        raise ValueError("潜龙阵 level must be an integer in [1, 10]")
    return SkillDefinition(QIAN_LONG_ZHEN_SKILL_ID, QIAN_LONG_ZHEN_NAME, 1.0,
        SkillTargetMode.SELF, (ApplyStateSkillEffectSpec(DAMAGE_RATE_STATE_ID,
        DamageRateParams(outgoing_rate=LEVEL_RATES[level - 1][0])),), skill_type=SkillType.FORMATION)


SKILL = create_qian_long_zhen_definition()


def create_qian_long_zhen_runtime(owner_id: str, *, slot: SkillSlot = SkillSlot.LEARNED_1,
                                  level: int = 10, enabled: bool = True) -> SkillRuntime:
    return SkillRuntime(create_qian_long_zhen_definition(level), owner_id, slot, enabled)


def install_qian_long_zhen(context: BattleContext, systems: "BattleSystems",
                           runtime: SkillRuntime) -> None:
    loaded = context.skill_runtimes.get(runtime.owner_id, runtime.skill_slot)
    definitions = tuple(create_qian_long_zhen_definition(i) for i in range(1, 11))
    if loaded is None or loaded.definition not in definitions or runtime.skill_slot is None:
        raise ValueError("潜龙阵 requires canonical loaded definition and provider slot")
    provider = context.get_unit(runtime.owner_id)
    team = sorted(systems.target_system.allies(context, provider, include_self=True),
                  key=lambda unit: unit.lineup_position or 0)
    if len(team) != 3 or [unit.lineup_position for unit in team] != list(LineupPosition):
        raise ValueError("潜龙阵 requires a complete living three-unit lineup")
    if any(unit.faction is None for unit in team):
        raise ValueError("潜龙阵 requires explicit factions")
    level = definitions.index(loaded.definition) + 1
    eligible = len({unit.faction for unit in team}) == 3
    snapshot = {"eligible": eligible, "level": level, "commander_id": team[0].unit_id,
                "factions": {unit.unit_id: unit.faction for unit in team}}
    if not eligible:
        context.metadata.setdefault("qian_long_snapshots", {})[(runtime.owner_id, runtime.skill_slot)] = snapshot
        return
    commander = team[0]
    commander_skills = [skill for skill in context.skill_runtimes.values()
                        if skill.owner_id == commander.unit_id]
    has_commander_effect = any(skill.definition.commander_effect_specs for skill in commander_skills)
    # Capture all four attributes BEFORE applying any formation effect. This
    # user-approved snapshot remains fixed after later buffs or qualification changes.
    attributes = {attribute: getattr(systems.attribute_system, f"get_{attribute}")(context, commander)
                  for attribute in ATTRIBUTES}
    deputy_rate, reduced_rate = LEVEL_RATES[level - 1]
    attribute_rate = reduced_rate if has_commander_effect else deputy_rate
    register_commander_effect_role_state(context.states)
    register_damage_rate_state(context.states)
    register_modifier_state_definitions(context.states)
    ref = SkillProviderRef(runtime.owner_id, runtime.skill_slot, QIAN_LONG_ZHEN_SKILL_ID)
    source = EffectSourceRef(SourceType.ACTIVE_SKILL, ref.owner_id, ref.skill_id, ref.skill_slot)
    effects = [ApplyStateEffect(COMMANDER_EFFECT_ROLE_STATE_ID, unit.unit_id, ref.owner_id,
        ref.skill_id, runtime_params=CommanderEffectRoleParams(unit is not commander), source_ref=source)
        for unit in team]
    effects.extend(ApplyStateEffect(ATTRIBUTE_BONUS_STATE_ID, commander.unit_id, ref.owner_id,
        ref.skill_id, runtime_params=AttributeBonusParams(attribute, attributes[attribute] * attribute_rate),
        source_ref=source) for attribute in ATTRIBUTES)
    effects.extend(ApplyStateEffect(DAMAGE_RATE_STATE_ID, unit.unit_id, ref.owner_id, ref.skill_id,
        runtime_params=(DamageRateParams(outgoing_rate=-.15) if unit is commander else
                        DamageRateParams(outgoing_rate=deputy_rate, incoming_rate=-deputy_rate)),
        source_ref=source) for unit in team)
    for effect in effects:
        result = systems.effect_executor.execute(context, effect)
        systems.dependency_evaluation_support.add_dependency(
            StateNode(result.state_instance.instance_id), ProviderNode(ref))
    snapshot.update({"has_commander_effect": has_commander_effect, "attributes": attributes,
        "attribute_rate": attribute_rate, "deputy_rate": deputy_rate,
        "attribute_provenance": "USER_CONFIRMED_INSTALLATION_EFFECTIVE_ATTRIBUTE_FIXED_INCREMENT",
        "provenance": "STATIC_DESCRIPTION / NOT_CLIENT_EMPIRICALLY_FROZEN"})
    context.metadata.setdefault("qian_long_snapshots", {})[(runtime.owner_id, runtime.skill_slot)] = snapshot
