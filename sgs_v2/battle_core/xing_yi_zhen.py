"""Lv10 形一阵: static description and user-confirmed round curve.

The highest-attribute read uses an installation snapshot. Until a tie rule is
confirmed, ties fail closed before any effect is applied. No hidden tie order.
"""
from .context import BattleContext
from .damage_rate_modifier import (DAMAGE_RATE_STATE_ID, RoundDamageRateParams,
                                   register_damage_rate_state)
from .dependency_evaluation import ProviderNode, StateNode
from .effects import ApplyStateEffect, EffectSourceRef
from .enums import LineupPosition, TroopType
from .operation_identity import SourceType
from .provider_identity import SkillProviderRef
from .skill_definition import (ApplyStateSkillEffectSpec, SkillDefinition,
                               SkillTargetMode, SkillType)
from .skill_runtime import SkillRuntime, SkillSlot
from .state_modifiers import (ATTRIBUTE_BONUS_STATE_ID, AttributeBonusParams,
                              register_modifier_state_definitions)

XING_YI_ZHEN_SKILL_ID = "22039"
XING_YI_ZHEN_NAME = "形一阵"
XING_YI_ZHEN_APPLICABLE_TROOPS = tuple(TroopType)
ROUND_CURVE = RoundDamageRateParams(
    opening_rates=((-0.30, -0.30), (-0.20, -0.20), (-0.10, -0.10)),
    outgoing_step=0.16, incoming_step=0.01)


def create_xing_yi_zhen_definition() -> SkillDefinition:
    return SkillDefinition(XING_YI_ZHEN_SKILL_ID, XING_YI_ZHEN_NAME, 1.0,
        SkillTargetMode.SELF,
        (ApplyStateSkillEffectSpec(DAMAGE_RATE_STATE_ID, ROUND_CURVE),),
        skill_type=SkillType.FORMATION)


SKILL = create_xing_yi_zhen_definition()


def create_xing_yi_zhen_runtime(owner_id: str, *,
                               slot: SkillSlot = SkillSlot.LEARNED_1,
                               enabled: bool = True) -> SkillRuntime:
    return SkillRuntime(SKILL, owner_id, slot, enabled)


def install_xing_yi_zhen(context: BattleContext, systems: object,
                        runtime: SkillRuntime) -> None:
    loaded = context.skill_runtimes.get(runtime.owner_id, runtime.skill_slot)
    if (runtime.definition != SKILL or runtime.skill_slot is None
            or loaded is None or loaded.definition != SKILL):
        raise ValueError("形一阵 requires canonical loaded Lv10 definition and provider slot")
    provider = context.get_unit(runtime.owner_id)
    team = sorted(systems.target_system.allies(context, provider, include_self=True),
                  key=lambda unit: unit.lineup_position)
    if len(team) != 3 or [unit.lineup_position for unit in team] != list(LineupPosition):
        raise ValueError("形一阵 requires a complete living three-unit lineup")
    inherent = [context.skill_runtimes.get(unit.unit_id, SkillSlot.INHERENT) for unit in team]
    if any(skill is None for skill in inherent):
        raise ValueError("形一阵 requires explicit inherent tactics for all three units")
    eligible = len({skill.definition.skill_type for skill in inherent}) == 1
    if not eligible:
        context.metadata.setdefault("xing_yi_snapshots", {})[(runtime.owner_id, runtime.skill_slot)] = {
            "eligible": False, "reason": "INHERENT_TYPES_DIFFER"}
        return
    # Read all four EFFECTIVE attributes before installing the attribute bonus.
    attributes = {key: getattr(systems.attribute_system, f"get_{key}")(context, provider)
                  for key in ("attack", "defense", "intelligence", "speed")}
    maximum = max(attributes.values())
    highest = [key for key, value in attributes.items() if value == maximum]
    if len(highest) != 1:
        raise NotImplementedError("形一阵 highest-attribute tie rule is unconfirmed")
    register_modifier_state_definitions(context.states)
    register_damage_rate_state(context.states)
    ref = SkillProviderRef(runtime.owner_id, runtime.skill_slot, XING_YI_ZHEN_SKILL_ID)
    source = EffectSourceRef(SourceType.ACTIVE_SKILL, ref.owner_id, ref.skill_id, ref.skill_slot)
    effects = [ApplyStateEffect(ATTRIBUTE_BONUS_STATE_ID, ref.owner_id, ref.owner_id,
        ref.skill_id, runtime_params=AttributeBonusParams(highest[0], 60), source_ref=source)]
    allies = [unit for unit in team if unit.unit_id != provider.unit_id]
    effects.extend(ApplyStateEffect(DAMAGE_RATE_STATE_ID, unit.unit_id, ref.owner_id,
        ref.skill_id, runtime_params=ROUND_CURVE, source_ref=source) for unit in allies)
    for effect in effects:
        result = systems.effect_executor.execute(context, effect)
        systems.dependency_evaluation_support.add_dependency(
            StateNode(result.state_instance.instance_id), ProviderNode(ref))
    context.metadata.setdefault("xing_yi_snapshots", {})[(runtime.owner_id, runtime.skill_slot)] = {
        "eligible": True, "attributes": attributes, "highest_attribute": highest[0],
        "target_ids": tuple(unit.unit_id for unit in allies),
        "curve_provenance": "USER_CONFIRMED_ROUND_CURVE / NOT_CLIENT_EMPIRICALLY_FROZEN",
        "snapshot_provenance": "PROVISIONAL_INSTALLATION_EFFECTIVE_ATTRIBUTE_SNAPSHOT / TIE_FAIL_CLOSED"}
