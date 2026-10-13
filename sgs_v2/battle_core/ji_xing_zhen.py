"""Lv10 箕形阵. User formula; installation-time STR snapshot is provisional.

The role-dependent split uses TargetSystem once and retains the other deputy.
Effects, expiry, damage pooling and provider cleanup retain canonical owners.
"""
from .context import BattleContext
from .dependency_evaluation import ProviderNode, StateNode
from .effects import ApplyStateEffect, EffectSourceRef
from .enums import BattlePhase, DamageType, LineupPosition, TroopType
from .numeric_validation import validate_finite_number
from .operation_identity import SourceType
from .outgoing_damage_reduction import (
    OUTGOING_DAMAGE_REDUCTION_STATE_ID, OutgoingDamageReductionParams,
    register_outgoing_reduction_state,
)
from .provider_identity import SkillProviderRef
from .skill_definition import ApplyStateSkillEffectSpec, SkillDefinition, SkillTargetMode, SkillType
from .skill_runtime import SkillRuntime, SkillSlot
from .state_modifiers import (INCOMING_DAMAGE_REDUCTION_STATE_ID,
                             IncomingDamageReductionParams, register_modifier_state_definitions)

JI_XING_ZHEN_SKILL_ID = "20178"
JI_XING_ZHEN_NAME = "箕形阵"
JI_XING_ZHEN_APPLICABLE_TROOPS = tuple(TroopType)
SCALING_PROVENANCE = "USER_SPECIFIED_FORMULA / NOT_CLIENT_EMPIRICALLY_FROZEN"
SNAPSHOT_PROVENANCE = "PROVISIONAL_INSTALLATION_TIME_PROVIDER_ATTACK"


def calculate_reduction_rate(strength: float) -> float:
    strength = validate_finite_number(strength, "strength")
    # 16/150 is in percentage points: convert to the runtime's [0, 1] rate.
    # Reject out-of-domain results instead of inventing an unconfirmed cap.
    return OutgoingDamageReductionParams(.40 + .16 / 150 * (strength - 100)).rate


def create_ji_xing_zhen_definition() -> SkillDefinition:
    return SkillDefinition(
        JI_XING_ZHEN_SKILL_ID, JI_XING_ZHEN_NAME, 1.0, SkillTargetMode.SELF,
        (ApplyStateSkillEffectSpec(OUTGOING_DAMAGE_REDUCTION_STATE_ID,
                                  OutgoingDamageReductionParams(.40)),),
        skill_type=SkillType.FORMATION,
    )


SKILL = create_ji_xing_zhen_definition()


def create_ji_xing_zhen_runtime(owner_id: str, *,
                               slot: SkillSlot = SkillSlot.LEARNED_1) -> SkillRuntime:
    return SkillRuntime(SKILL, owner_id, slot)


def install_ji_xing_zhen(context: BattleContext, systems: object,
                        runtime: SkillRuntime) -> None:
    if runtime.definition != SKILL or runtime.skill_slot is None:
        raise ValueError("箕形阵 requires canonical Lv10 definition and provider slot")
    loaded = context.skill_runtimes.get(runtime.owner_id, runtime.skill_slot)
    if loaded is None or loaded.definition != SKILL:
        raise ValueError("unsupported loaded 箕形阵 definition")
    provider = context.get_unit(runtime.owner_id)
    enemies = systems.target_system.enemies(context, provider)
    commanders = [u for u in enemies if u.lineup_position is LineupPosition.COMMANDER]
    deputies = sorted((u for u in systems.target_system.allies(context, provider)
                       if u.lineup_position in (LineupPosition.DEPUTY_1, LineupPosition.DEPUTY_2)),
                      key=lambda u: u.lineup_position.value)
    if len(commanders) != 1 or len(deputies) != 2:
        raise ValueError("箕形阵 requires one enemy commander and two living friendly deputies")
    strength = systems.attribute_system.get_attack(context, provider)
    rate = calculate_reduction_rate(strength)
    # Validate schemas before selection RNG or effect mutation.
    register_modifier_state_definitions(context.states)
    if context.states.get_definition(INCOMING_DAMAGE_REDUCTION_STATE_ID).runtime_params_type is not IncomingDamageReductionParams:
        raise ValueError("incompatible incoming reduction schema")
    register_outgoing_reduction_state(context.states)
    weapon_deputy = systems.target_system.random_units(context, deputies, count=1)[0]
    strategy_deputy = next(u for u in deputies if u.unit_id != weapon_deputy.unit_id)
    ref = EffectSourceRef(SourceType.ACTIVE_SKILL, runtime.owner_id,
                          JI_XING_ZHEN_SKILL_ID, runtime.skill_slot)
    tree = (
        (commanders[0], OUTGOING_DAMAGE_REDUCTION_STATE_ID, OutgoingDamageReductionParams(rate)),
        (weapon_deputy, INCOMING_DAMAGE_REDUCTION_STATE_ID, IncomingDamageReductionParams(DamageType.WEAPON, .20)),
        (strategy_deputy, INCOMING_DAMAGE_REDUCTION_STATE_ID, IncomingDamageReductionParams(DamageType.STRATEGY, .20)),
    )
    provider_ref = SkillProviderRef(runtime.owner_id, runtime.skill_slot, JI_XING_ZHEN_SKILL_ID)
    for target, state_id, params in tree:
        result = systems.effect_executor.execute(context, ApplyStateEffect(
            state_id, target.unit_id, runtime.owner_id, JI_XING_ZHEN_SKILL_ID,
            expires_round=4, expires_phase=BattlePhase.ROUND_START.value,
            runtime_params=params, source_ref=ref,
        ))
        systems.dependency_evaluation_support.add_dependency(
            StateNode(result.state_instance.instance_id), ProviderNode(provider_ref))
    context.metadata.setdefault("ji_xing_snapshots", {})[(runtime.owner_id, runtime.skill_slot)] = {
        "strength": strength, "reduction_rate": rate, "enemy_commander_id": commanders[0].unit_id,
        "weapon_deputy_id": weapon_deputy.unit_id, "strategy_deputy_id": strategy_deputy.unit_id,
        "provenance": SCALING_PROVENANCE, "snapshot_provenance": SNAPSHOT_PROVENANCE,
    }
