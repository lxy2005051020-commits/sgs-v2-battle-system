"""飞熊军 full-level USER_SPECIFIED_FINAL_ADDITIVE_MODEL (2026-10-12).

20247 is a research-table identity, pending raw client identity verification.
User rule: actual team recovery / 10 is added to each target's FINAL damage;
two targets share one snapshot; recovery during damage is for the next batch.
This is an authorized provisional model, not battle-report gameplay proof.
"""
from ..context import BattleContext
from ..enums import DamageType, LineupPosition, SpecialTroopId, TroopType
from ..action_start_recovery_damage import ACTION_START_RECOVERY_DAMAGE_STATE_ID, ActionStartRecoveryDamageParams
from ..received_recovery_modifier import RECEIVED_RECOVERY_BONUS_STATE_ID, ReceivedRecoveryBonusParams
from ..skill_definition import ApplyStateSkillEffectSpec, SkillDefinition, SkillTargetMode, SkillType
from ..skill_runtime import SkillRuntime, SkillSlot
from ..stage9_integerization import ExactRatio
from ..troop_skill_config import TroopSkillConfig
from ..unit import UnitRuntime

FEI_XIONG_TRIGGER_PROBABILITY = .60
FEI_XIONG_BASE_DAMAGE_COEFFICIENT = .64
FEI_XIONG_DAMAGE_TARGET_COUNT = 2
FEI_XIONG_ACTUAL_RECOVERY_DAMAGE_RATIO = ExactRatio(1, 10)
FEI_XIONG_FINAL_DAMAGE_MODEL_KEY = 'FEIXIONG_USER_ACTUAL_RECOVERY_FINAL_ADDITION_V1'


def _definition(rate: ExactRatio) -> SkillDefinition:
    return SkillDefinition("20247", "飞熊军", 1.0, SkillTargetMode.FIXED_ALL_TEAM,
        (ApplyStateSkillEffectSpec(RECEIVED_RECOVERY_BONUS_STATE_ID, ReceivedRecoveryBonusParams(rate)),),
        skill_type=SkillType.TROOP)


def create_fei_xiong_jun_definition() -> SkillDefinition:
    """PRE_BATTLE recovery declaration; action state is supplemental on commander."""
    return _definition(ExactRatio(16, 100))


def resolve_recovery_definition(context: BattleContext, systems: object, owner: UnitRuntime) -> SkillDefinition:
    commander = next((u for u in context.units.values()
        if u.team_id == owner.team_id and u.lineup_position is LineupPosition.COMMANDER), None)
    if commander is None:
        raise ValueError("飞熊军 requires a canonical team commander")
    return _definition(ExactRatio(20 if commander.name == "董卓" else 16, 100))


def resolve_definition(context: BattleContext, systems: object, owner: UnitRuntime) -> SkillDefinition:
    return resolve_recovery_definition(context, systems, owner)


def resolve_supplemental_definition(context: BattleContext, systems: object, owner: UnitRuntime) -> SkillDefinition:
    # User-specified actual recovery / 10 is FINAL damage addition, not a
    # coefficient increment and not the pre-modifier additive basis lane.
    return SkillDefinition('20247', '飞熊军', 1.0, SkillTargetMode.TEAM_COMMANDER,
        (ApplyStateSkillEffectSpec(ACTION_START_RECOVERY_DAMAGE_STATE_ID,
            ActionStartRecoveryDamageParams(FEI_XIONG_TRIGGER_PROBABILITY, DamageType.STRATEGY,
                FEI_XIONG_BASE_DAMAGE_COEFFICIENT, FEI_XIONG_DAMAGE_TARGET_COUNT,
                FEI_XIONG_ACTUAL_RECOVERY_DAMAGE_RATIO, FEI_XIONG_FINAL_DAMAGE_MODEL_KEY,
                after_sequence=context.event_bus.history[-1].sequence if context.event_bus.history else 0)),),
        skill_type=SkillType.TROOP)


SKILL = create_fei_xiong_jun_definition()
CONFIG = TroopSkillConfig("20247", "飞熊军", TroopType.CAVALRY, SpecialTroopId.FEI_XIONG_JUN,
    create_fei_xiong_jun_definition, requires_provider_slot=True, definition_resolver=resolve_definition,
    supplemental_definition_resolver=resolve_supplemental_definition)


def create_fei_xiong_jun_runtime(owner_id: str, *, slot: SkillSlot = SkillSlot.LEARNED_1,
                               enabled: bool = True) -> SkillRuntime:
    return SkillRuntime(SKILL, owner_id, slot, enabled)
