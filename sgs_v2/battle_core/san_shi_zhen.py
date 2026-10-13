"""三势阵 22012. Static rates; user-confirmed tie and replacement rules.

Provider action-start timing and entry-minus-current troop loss are explicit
model assumptions, rather than claims of client mechanism verification.
"""
from typing import TYPE_CHECKING
from .context import BattleContext
if TYPE_CHECKING:
    from .battle_systems import BattleSystems
from .action_start_role_split import ROLE_SPLIT_STATE_ID, RoleSplitParams, register_role_split_state
from .damage_rate_modifier import register_damage_rate_state
from .dependency_evaluation import ProviderNode, StateNode
from .effects import ApplyStateEffect, EffectSourceRef
from .enums import BattlePhase, LineupPosition, TroopType
from .operation_identity import SourceType
from .provider_identity import SkillProviderRef
from .skill_definition import ApplyStateSkillEffectSpec, SkillDefinition, SkillTargetMode, SkillType
from .skill_runtime import SkillRuntime, SkillSlot
from .state_modifiers import (ACTIVATION_RATE_BONUS_STATE_ID, ActivationRateBonusParams,
                             register_modifier_state_definitions)

SAN_SHI_ZHEN_SKILL_ID = "22012"
SAN_SHI_ZHEN_NAME = "三势阵"
SAN_SHI_ZHEN_APPLICABLE_TROOPS = tuple(TroopType)
# Each tuple is (activation bonus, incoming reduction, outgoing increase).
# Exact display values from all ten client static rows, not interpolation.
LEVEL_RATES = (
    (.08, .15, .125), (.089, .167, .139), (.098, .183, .153),
    (.107, .20, .167), (.116, .217, .181), (.124, .233, .194),
    (.133, .25, .208), (.142, .267, .222), (.151, .283, .236),
    (.16, .30, .25),
)


def create_san_shi_zhen_definition(level: int = 10) -> SkillDefinition:
    if type(level) is not int or not 1 <= level <= 10:
        raise ValueError("三势阵 level must be an integer in [1, 10]")
    return SkillDefinition(SAN_SHI_ZHEN_SKILL_ID, SAN_SHI_ZHEN_NAME, 1.0,
        SkillTargetMode.SELF,
        (ApplyStateSkillEffectSpec(ACTIVATION_RATE_BONUS_STATE_ID,
            ActivationRateBonusParams(SkillType.ACTIVE, LEVEL_RATES[level - 1][0],
                                      skill_slot=SkillSlot.INHERENT)),),
        skill_type=SkillType.FORMATION)


SKILL = create_san_shi_zhen_definition()


def create_san_shi_zhen_runtime(owner_id: str, *, slot: SkillSlot = SkillSlot.LEARNED_1,
                               level: int = 10, enabled: bool = True) -> SkillRuntime:
    return SkillRuntime(create_san_shi_zhen_definition(level), owner_id, slot, enabled)


def install_san_shi_zhen(context: BattleContext, systems: "BattleSystems", runtime: SkillRuntime) -> None:
    loaded = context.skill_runtimes.get(runtime.owner_id, runtime.skill_slot)
    definitions = tuple(create_san_shi_zhen_definition(i) for i in range(1, 11))
    if loaded is None or loaded.definition not in definitions or runtime.skill_slot is None:
        raise ValueError("三势阵 requires canonical loaded definition and provider slot")
    provider = context.get_unit(runtime.owner_id)
    team = sorted(systems.target_system.allies(context, provider, include_self=True),
                  key=lambda u: u.lineup_position)
    if len(team) != 3 or [u.lineup_position for u in team] != list(LineupPosition):
        raise ValueError("三势阵 requires a complete living three-unit lineup")
    if any(u.faction is None for u in team):
        raise ValueError("三势阵 requires explicit faction data; unknown faction is not inferred")
    level = definitions.index(loaded.definition) + 1
    inherent = context.skill_runtimes.get(team[0].unit_id, SkillSlot.INHERENT)
    eligible = (len({u.faction for u in team}) == 3 and inherent is not None
                and inherent.definition.skill_type in (SkillType.ACTIVE, SkillType.ASSAULT))
    context.metadata.setdefault("san_shi_admissions", {})[(runtime.owner_id, runtime.skill_slot)] = {
        "eligible": eligible, "level": level, "commander_id": team[0].unit_id,
        "factions": {u.unit_id: u.faction for u in team},
        "rules": "TIE_DEPUTY_1 / CLEAR_OLD_EFFECTS / USER_CONFIRMED",
        "model_assumptions": "PROVIDER_ACTION_START / ENTRY_MINUS_CURRENT_TROOPS / NOT_CLIENT_FROZEN"}
    if not eligible:
        return
    register_modifier_state_definitions(context.states)
    register_damage_rate_state(context.states)
    register_role_split_state(context.states)
    activation, reduction, increase = LEVEL_RATES[level - 1]
    ref = SkillProviderRef(runtime.owner_id, runtime.skill_slot, SAN_SHI_ZHEN_SKILL_ID)
    source = EffectSourceRef(SourceType.ACTIVE_SKILL, ref.owner_id, ref.skill_id, ref.skill_slot)
    effects = (
        ApplyStateEffect(ACTIVATION_RATE_BONUS_STATE_ID, team[0].unit_id, ref.owner_id, ref.skill_id,
            expires_round=6, expires_phase=BattlePhase.ROUND_START.value,
            runtime_params=ActivationRateBonusParams(inherent.definition.skill_type, activation,
                                                    skill_slot=SkillSlot.INHERENT), source_ref=source),
        ApplyStateEffect(ROLE_SPLIT_STATE_ID, ref.owner_id, ref.owner_id, ref.skill_id,
            runtime_params=RoleSplitParams(tuple((u.unit_id, u.troops) for u in team[1:]),
                                          reduction, increase), source_ref=source),
    )
    for effect in effects:
        result = systems.effect_executor.execute(context, effect)
        systems.dependency_evaluation_support.add_dependency(
            StateNode(result.state_instance.instance_id), ProviderNode(ref))
