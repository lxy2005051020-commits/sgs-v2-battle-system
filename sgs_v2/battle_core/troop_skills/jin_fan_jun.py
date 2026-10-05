"""锦帆军 full-level bounded integration with explicit formula placeholders.

Research contract:
MC-STAGE14-JIN-FAN-JUN-01

The real attack-scaling formula for rout damage and the real Gan Ning
highest-attribute trigger formula remain OPEN. Runtime uses explicit placeholder
policies so they can be replaced in-place later without changing the trigger
or owner architecture.
"""
from ..enums import DamageType, LineupPosition, SpecialTroopId, TroopType
from ..normal_attack_followup import (
    FollowupTargetMode,
    NormalAttackFollowupParams,
    TargetStateBranchFollowup,
    NORMAL_ATTACK_FOLLOWUP_STATE_ID,
)
from ..official_state_catalog import OfficialStateId
from ..skill_definition import (
    ApplyStateSkillEffectSpec,
    DamageSkillEffectSpec,
    SkillDefinition,
    SkillTargetMode,
    SkillType,
)
from ..skill_runtime import SkillRuntime, SkillSlot
from ..stage9_integerization import ExactRatio
from ..stage11_state_params import CriticalStateParams
from ..troop_skill_config import TroopSkillConfig


JIN_FAN_BASE_TRIGGER_PROBABILITY = 0.45
JIN_FAN_ROUT_COEFFICIENT_PLACEHOLDER = 0.64
GAN_NING_TRIGGER_PROBABILITY_PLACEHOLDER = 0.45
GAN_NING_ALLY_CRIT_CHANCE = 0.06

# Explicit research boundaries. None means "formula not frozen", not zero.
JIN_FAN_ROUT_SCALING_FORMULA = None
GAN_NING_TRIGGER_PROBABILITY_FORMULA = None


def rout_coefficient_placeholder() -> float:
    """Temporary project-authorized placeholder, not the real 武力 scaling formula."""
    return JIN_FAN_ROUT_COEFFICIENT_PLACEHOLDER


def gan_ning_trigger_probability_placeholder() -> float:
    """Temporary project-authorized placeholder, not the real highest-attribute formula."""
    return GAN_NING_TRIGGER_PROBABILITY_PLACEHOLDER


def _definition(trigger_probability: float, rout_coefficient: float) -> SkillDefinition:
    return SkillDefinition(
        "20152",
        "锦帆军",
        1.0,
        SkillTargetMode.FIXED_ALL_TEAM,
        (
            ApplyStateSkillEffectSpec(
                NORMAL_ATTACK_FOLLOWUP_STATE_ID,
                NormalAttackFollowupParams(
                    trigger_probability,
                    TargetStateBranchFollowup(
                        OfficialStateId.ROUT.value,
                        DamageSkillEffectSpec(DamageType.WEAPON, 1.10),
                        duration=2,
                        continuous_damage_coefficient=rout_coefficient,
                        recovery_ratio=ExactRatio(30, 100),
                    ),
                    FollowupTargetMode.INHERIT_ACTUAL_TARGET,
                ),
            ),
        ),
        skill_type=SkillType.TROOP,
    )


def create_jin_fan_jun_definition() -> SkillDefinition:
    return _definition(
        JIN_FAN_BASE_TRIGGER_PROBABILITY,
        rout_coefficient_placeholder(),
    )


def _gan_ning_commands(context, owner) -> bool:
    return any(
        u.team_id == owner.team_id
        and u.name == "甘宁"
        and u.lineup_position is LineupPosition.COMMANDER
        for u in context.units.values()
    )


def resolve_definition(context, systems, owner) -> SkillDefinition:
    trigger_probability = (
        gan_ning_trigger_probability_placeholder()
        if _gan_ning_commands(context, owner)
        else JIN_FAN_BASE_TRIGGER_PROBABILITY
    )
    return _definition(trigger_probability, rout_coefficient_placeholder())


def resolve_supplemental_definition(context, systems, owner) -> SkillDefinition | None:
    """Gan Ning commander grants +6% crit to the two non-commanders only."""
    if not _gan_ning_commands(context, owner):
        return None
    return SkillDefinition(
        "20152",
        "锦帆军",
        1.0,
        SkillTargetMode.TEAM_NON_COMMANDERS,
        (
            ApplyStateSkillEffectSpec(
                OfficialStateId.CRITICAL.value,
                CriticalStateParams(chance=GAN_NING_ALLY_CRIT_CHANCE, bonus=1.0),
            ),
        ),
        skill_type=SkillType.TROOP,
    )


SKILL = create_jin_fan_jun_definition()
CONFIG = TroopSkillConfig(
    "20152",
    "锦帆军",
    TroopType.BOW,
    SpecialTroopId.JIN_FAN_JUN,
    create_jin_fan_jun_definition,
    requires_provider_slot=True,
    definition_resolver=resolve_definition,
    supplemental_definition_resolver=resolve_supplemental_definition,
)


def create_jin_fan_jun_runtime(
    owner_id: str,
    *,
    slot: SkillSlot = SkillSlot.LEARNED_1,
    enabled: bool = True,
) -> SkillRuntime:
    return SkillRuntime(SKILL, owner_id, slot, enabled)
