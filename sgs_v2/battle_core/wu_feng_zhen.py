"""武锋阵22031: user-specified live commander reduction; state-backed support."""
from dataclasses import dataclass
from .damage_rate_modifier import register_damage_rate_state
from .dependency_evaluation import ProviderNode, StateNode
from .effects import ApplyStateEffect, EffectSourceRef
from .enums import LineupPosition, TroopType, BattlePhase
from .probabilistic_target_priority import (TARGET_PRIORITY_STATE_ID, TargetPriorityParams,
                                           register_target_priority_state)
from .operation_identity import SourceType
from .periodic_team_support import (PERIODIC_TEAM_SUPPORT_STATE_ID, PeriodicTeamSupportParams,
                                    RecoveryTargetMode, register_periodic_team_support_state)
from .provider_identity import SkillProviderRef
from .skill_definition import ApplyStateSkillEffectSpec, SkillDefinition, SkillTargetMode, SkillType
from .skill_runtime import SkillRuntime, SkillSlot
from .state_runtime_params import StateRuntimeParams

WU_FENG_ZHEN_SKILL_ID = "22031"
WU_FENG_ZHEN_NAME = "武锋阵"
WU_FENG_ZHEN_APPLICABLE_TROOPS = tuple(TroopType)
# (recovery rate, outgoing increase), exact client display rows.
LEVEL_RATES = ((.92, .075), (1.022, .083), (1.124, .092), (1.227, .10),
               (1.329, .108), (1.431, .117), (1.533, .125), (1.636, .133),
               (1.738, .142), (1.84, .15))


@dataclass(frozen=True, slots=True)
class WuFengOptions(StateRuntimeParams):
    level: int = 10
    deputies_only: bool = False
    recovery_target_mode: RecoveryTargetMode | None = RecoveryTargetMode.RANDOM_ALLIES

    def __post_init__(self):
        if type(self.level) is not int or not 1 <= self.level <= 10:
            raise ValueError("level must be an integer in [1, 10]")
        if type(self.deputies_only) is not bool:
            raise TypeError("deputies_only must be bool")
        if self.recovery_target_mode is not None and not isinstance(self.recovery_target_mode, RecoveryTargetMode):
            raise TypeError("recovery_target_mode must be RecoveryTargetMode")
        if self.recovery_target_mode is None:
            raise ValueError("runtime requires an explicit recovery target model")
        if self.recovery_target_mode is not RecoveryTargetMode.RANDOM_ALLIES:
            raise ValueError("武锋阵 requires random recovery among the performer's two teammates")
        if not self.deputies_only and self.level != 10:
            raise NotImplementedError("only Lv10 command scaling is confirmed; other levels support deputies_only=True")


def create_wu_feng_zhen_definition(level=10, *, deputies_only=False,
                                  recovery_target_mode=RecoveryTargetMode.RANDOM_ALLIES):
    return SkillDefinition(WU_FENG_ZHEN_SKILL_ID, WU_FENG_ZHEN_NAME, 1.0, SkillTargetMode.SELF,
        (ApplyStateSkillEffectSpec(PERIODIC_TEAM_SUPPORT_STATE_ID,
            WuFengOptions(level, deputies_only, recovery_target_mode)),), skill_type=SkillType.FORMATION)


SKILL = create_wu_feng_zhen_definition()


def create_wu_feng_zhen_runtime(owner_id, *, slot=SkillSlot.LEARNED_1, level=10,
                               deputies_only=False, recovery_target_mode=RecoveryTargetMode.RANDOM_ALLIES, enabled=True):
    return SkillRuntime(create_wu_feng_zhen_definition(level, deputies_only=deputies_only,
                        recovery_target_mode=recovery_target_mode), owner_id, slot, enabled)


def _options(context, owner_id, slot):
    loaded = context.skill_runtimes.get(owner_id, slot)
    if loaded is None or slot is None:
        raise ValueError("武锋阵 requires a canonical loaded runtime and slot")
    specs = loaded.definition.effect_specs
    options = specs[0].runtime_params if len(specs) == 1 and isinstance(specs[0], ApplyStateSkillEffectSpec) else None
    if not isinstance(options, WuFengOptions) or loaded.definition != create_wu_feng_zhen_definition(
            options.level, deputies_only=options.deputies_only, recovery_target_mode=options.recovery_target_mode):
        raise ValueError("unsupported 武锋阵 definition")
    return options


def install_wu_feng_zhen(context, systems, runtime):
    options = _options(context, runtime.owner_id, runtime.skill_slot)
    provider = context.get_unit(runtime.owner_id)
    team = sorted(systems.target_system.allies(context, provider), key=lambda u: (u.lineup_position or 0, u.unit_id))
    if len(team) != 3 or [u.lineup_position for u in team] != list(LineupPosition):
        raise ValueError("武锋阵 requires a complete living three-unit lineup")
    if len({u.troop_type for u in team}) != 1:
        raise ValueError("武锋阵 requires one explicit current team troop type")
    if any(u.troop_aptitude not in ("S", "A", "B", "C") for u in team):
        raise ValueError("武锋阵 requires explicit current-troop aptitude S/A/B/C")
    eligible = len({u.troop_aptitude for u in team}) == 3
    context.metadata.setdefault("wu_feng_admissions", {})[(runtime.owner_id, runtime.skill_slot)] = {
        "eligible": eligible, "level": options.level, "mode": "DEPUTIES_ONLY" if options.deputies_only else "FULL_LV10",
        "omitted": ["COMMANDER_PRIORITY", "COMMAND_SCALED_REDUCTION"] if options.deputies_only else [],
        "recovery_target_mode": options.recovery_target_mode.value,
        "timing": "USER_CONFIRMED_PROVIDER_ACTION", "aptitudes": {u.unit_id: u.troop_aptitude for u in team}}
    if not eligible:
        return
    deputies = sorted(team[1:], key=lambda u: "CBAS".index(u.troop_aptitude))
    recovery, increase = LEVEL_RATES[options.level - 1]
    register_damage_rate_state(context.states)
    register_periodic_team_support_state(context.states)
    if not options.deputies_only:
        register_target_priority_state(context.states)
    ref = SkillProviderRef(runtime.owner_id, runtime.skill_slot, WU_FENG_ZHEN_SKILL_ID)
    result = systems.effect_executor.execute(context, ApplyStateEffect(
        PERIODIC_TEAM_SUPPORT_STATE_ID, runtime.owner_id, runtime.owner_id, ref.skill_id,
        runtime_params=PeriodicTeamSupportParams(deputies[0].unit_id, deputies[1].unit_id,
                                                recovery, increase, options.recovery_target_mode),
        source_ref=EffectSourceRef(SourceType.ACTIVE_SKILL, ref.owner_id, ref.skill_id, ref.skill_slot)))
    systems.dependency_evaluation_support.add_dependency(StateNode(result.state_instance.instance_id), ProviderNode(ref))
    if not options.deputies_only:
        # 0.1 percentage point per command point = 0.001 in runtime fractions.
        result = systems.effect_executor.execute(context, ApplyStateEffect(
            TARGET_PRIORITY_STATE_ID, team[0].unit_id, ref.owner_id, ref.skill_id,
            expires_round=6, expires_phase=BattlePhase.ROUND_START.value,
            runtime_params=TargetPriorityParams(.8, .30, .001, 100),
            source_ref=EffectSourceRef(SourceType.ACTIVE_SKILL, ref.owner_id, ref.skill_id, ref.skill_slot)))
        systems.dependency_evaluation_support.add_dependency(StateNode(result.state_instance.instance_id), ProviderNode(ref))
