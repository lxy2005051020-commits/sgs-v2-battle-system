"""八门金锁阵: user-specified scaling, confirmed admission-time INT snapshot.

Level rates come from the supplied client's named static export, not interpolation.
Selection, effects, lifetime and source cleanup stay with their canonical owners.
"""
from dataclasses import replace

from .context import BattleContext
from .dependency_evaluation import ProviderNode, StateNode
from .enums import BattlePhase, LineupPosition, TroopType
from .numeric_validation import validate_finite_number
from .official_state_catalog import OfficialStateId
from .outgoing_damage_reduction import (OUTGOING_DAMAGE_REDUCTION_STATE_ID,
    OutgoingDamageReductionParams, register_outgoing_reduction_state)
from .provider_identity import SkillProviderRef
from .skill_definition import (ApplyStateSkillEffectSpec, SkillDefinition,
    SkillTargetMode, SkillType)
from .skill_runtime import SkillRuntime, SkillSlot
from .stage11_state_params import Stage11TimedFlagParams

BA_MEN_JIN_SUO_ZHEN_SKILL_ID = "20025"
BA_MEN_JIN_SUO_ZHEN_NAME = "八门金锁阵"
BASE_REDUCTION_RATES = (.15, .166, .182, .198, .214, .23, .247, .264, .281, .30)
BA_MEN_APPLICABLE_TROOPS = tuple(TroopType)
SCALING_PROVENANCE = "USER_SPECIFIED_FORMULA / NOT_CLIENT_EMPIRICALLY_FROZEN"


def calculate_reduction_rate(base_rate: float, intelligence: float) -> float:
    base = validate_finite_number(base_rate, "base_rate", minimum=0, maximum=1)
    intelligence = validate_finite_number(intelligence, "intelligence")
    # Do not round to display precision or silently invent an extreme-value cap.
    return OutgoingDamageReductionParams(
        base * (1 + .272 * (intelligence - 100) / 100)
    ).rate


def _definition(rate: float) -> SkillDefinition:
    return SkillDefinition(
        BA_MEN_JIN_SUO_ZHEN_SKILL_ID, BA_MEN_JIN_SUO_ZHEN_NAME, 1.0,
        SkillTargetMode.CHOOSE_N_RANDOM_ENEMIES,
        (ApplyStateSkillEffectSpec(OUTGOING_DAMAGE_REDUCTION_STATE_ID,
            OutgoingDamageReductionParams(rate), expires_round=4,
            expires_phase=BattlePhase.ROUND_START.value),),
        skill_type=SkillType.FORMATION, target_count=2,
    )


def create_ba_men_jin_suo_zhen_definition(level: int = 10) -> SkillDefinition:
    if type(level) is not int or not 1 <= level <= 10:
        raise ValueError("八门金锁阵 level must be an integer in [1, 10]")
    return _definition(BASE_REDUCTION_RATES[level - 1])


SKILL = create_ba_men_jin_suo_zhen_definition()


def create_ba_men_jin_suo_zhen_runtime(owner_id: str, *,
    slot: SkillSlot = SkillSlot.LEARNED_1, level: int = 10, enabled: bool = True
) -> SkillRuntime:
    return SkillRuntime(create_ba_men_jin_suo_zhen_definition(level), owner_id, slot, enabled)


def install_ba_men_jin_suo_zhen(context: BattleContext, systems: object,
                              runtime: SkillRuntime) -> None:
    if runtime.definition.skill_id != BA_MEN_JIN_SUO_ZHEN_SKILL_ID or runtime.skill_slot is None:
        raise ValueError("八门金锁阵 requires canonical identity and provider slot")
    # Admission's effective factory is canonical Lv10; the authoritative loaded
    # runtime retains its actual level. Admission registers it before this seam.
    loaded = context.skill_runtimes.get(runtime.owner_id, runtime.skill_slot)
    if loaded is None:
        raise ValueError("八门金锁阵 requires a registered loaded runtime")
    definitions = tuple(create_ba_men_jin_suo_zhen_definition(i) for i in range(1, 11))
    if loaded.definition not in definitions:
        raise ValueError("unsupported 八门金锁阵 loaded definition")
    level = definitions.index(loaded.definition) + 1
    provider = context.get_unit(runtime.owner_id)
    commanders = [u for u in context.units.values()
        if u.team_id == provider.team_id and u.lineup_position is LineupPosition.COMMANDER
        and u.is_alive]
    if len(commanders) != 1:
        raise ValueError("八门金锁阵 requires one living team commander")
    intelligence = systems.attribute_system.get_intelligence(context, provider)
    rate = calculate_reduction_rate(BASE_REDUCTION_RATES[level - 1], intelligence)
    # Official catalogs are part of the production BattleContext setup. Detect
    # an incomplete setup before selector RNG or any target-state mutation.
    first_definition = context.states.get_definition(OfficialStateId.FIRST_STRIKE.value)
    if first_definition.runtime_params_type is not Stage11TimedFlagParams:
        raise ValueError("八门金锁阵 requires the official first-strike schema")
    register_outgoing_reduction_state(context.states)
    enemy_count = sum(u.is_alive and u.team_id != provider.team_id for u in context.units.values())
    reduction_definition = replace(_definition(rate), target_count=min(2, enemy_count) or 2)
    reduction_runtime = replace(runtime, definition=reduction_definition)
    first_strike_definition = SkillDefinition(
        BA_MEN_JIN_SUO_ZHEN_SKILL_ID, BA_MEN_JIN_SUO_ZHEN_NAME, 1.0,
        SkillTargetMode.TEAM_COMMANDER,
        (ApplyStateSkillEffectSpec(OfficialStateId.FIRST_STRIKE.value,
            Stage11TimedFlagParams(), expires_round=4,
            expires_phase=BattlePhase.ROUND_START.value),),
        skill_type=SkillType.FORMATION,
    )
    # Generate both effect branches through the real selectors before execution.
    reduction = systems.skill_resolver.resolve(context, reduction_runtime)
    first_strike = systems.skill_resolver.resolve(
        context, replace(runtime, definition=first_strike_definition))
    provider_ref = SkillProviderRef(runtime.owner_id, runtime.skill_slot,
                                   BA_MEN_JIN_SUO_ZHEN_SKILL_ID)
    for effect in (*reduction.effects, *first_strike.effects):
        result = systems.effect_executor.execute(context, effect)
        systems.dependency_evaluation_support.add_dependency(
            StateNode(result.state_instance.instance_id), ProviderNode(provider_ref))
    context.metadata.setdefault("ba_men_snapshots", {})[
        (runtime.owner_id, runtime.skill_slot)
    ] = {"level": level, "base_rate": BASE_REDUCTION_RATES[level - 1],
        "intelligence": intelligence, "reduction_rate": rate,
        "enemy_target_ids": reduction.target_ids, "commander_ids": first_strike.target_ids,
        "provenance": SCALING_PROVENANCE}
