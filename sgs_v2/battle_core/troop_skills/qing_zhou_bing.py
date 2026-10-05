"""青州兵 full-level baseline with a user-authorized provisional damage basis.

The Cao Cao command-scaling extension is deliberately an empty placeholder.
The battle module only declares existing state/target/scheduled-recovery specs.
"""
from ..context import BattleContext
from ..enums import BattlePhase, SpecialTroopId, TroopType
from ..official_state_catalog import OfficialStateId
from ..scheduled_team_recovery import ScheduledTeamRecoverySpec
from ..skill_definition import ApplyStateSkillEffectSpec, SkillDefinition, SkillTargetMode, SkillType
from ..skill_runtime import SkillRuntime, SkillSlot
from ..stage10_state_params import RecoveryPotencyContext
from ..stage9_integerization import ExactRatio
from ..provider_gated_counter import ProviderGatedCounterParams
from ..troop_skill_config import TroopSkillConfig
from ..unit import UnitRuntime

CAO_CAO_COMMANDER_ENHANCEMENT = None
PROVISIONAL_DAMAGE_BASIS_RATIO = ExactRatio(1, 10)
PROVISIONAL_BASIS_MODEL_KEY = "QINGZHOU_USER_PROVISIONAL_TEAM_ACTUAL_LOSS_V1"


def create_qing_zhou_bing_definition() -> SkillDefinition:
    return SkillDefinition("20153", "青州兵", 1.0, SkillTargetMode.CHOOSE_N_RANDOM_TEAM,
        (ApplyStateSkillEffectSpec(OfficialStateId.COUNTERATTACK.value,
            ProviderGatedCounterParams(ExactRatio(72, 100)),
            expires_round=3, expires_phase=BattlePhase.ROUND_START.value),),
        skill_type=SkillType.TROOP, target_count=2)


def resolve_scheduled_recovery(context: BattleContext, systems: object, owner: UnitRuntime) -> ScheduledTeamRecoverySpec:
    return ScheduledTeamRecoverySpec(due_round=3, first_damage_round=1, last_damage_round=2,
        potency=RecoveryPotencyContext(base_rate=1.80, source_troops_at_application=owner.troops,
            source_attribute_at_application=systems.attribute_system.get_attack(context, owner)),
        damage_basis_ratio=PROVISIONAL_DAMAGE_BASIS_RATIO,
        basis_model_key=PROVISIONAL_BASIS_MODEL_KEY)


def resolve_definition(context: BattleContext, systems: object, owner: UnitRuntime) -> SkillDefinition:
    # Preserve Stage12's explicit insufficient-candidate boundary before mutation.
    if len(systems.target_system.allies(context, owner, include_self=True)) < 2:
        raise NotImplementedError("青州兵: 少于两名存活武将时的群体反击目标规则尚未确认")
    return create_qing_zhou_bing_definition()


SKILL = create_qing_zhou_bing_definition()
CONFIG = TroopSkillConfig("20153", "青州兵", TroopType.SPEAR, SpecialTroopId.QING_ZHOU_BING,
    create_qing_zhou_bing_definition, requires_provider_slot=True,
    definition_resolver=resolve_definition,
    scheduled_recovery_resolver=resolve_scheduled_recovery)


def create_qing_zhou_bing_runtime(owner_id: str, *, slot: SkillSlot = SkillSlot.LEARNED_1,
                                 enabled: bool = True) -> SkillRuntime:
    return SkillRuntime(SKILL, owner_id, slot, enabled)
