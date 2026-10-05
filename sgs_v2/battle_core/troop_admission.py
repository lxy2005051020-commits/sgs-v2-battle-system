from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .context import BattleContext
from .dependency_evaluation import ProviderNode, StateNode
from .enums import BattlePhase, LineupPosition, SpecialTroopId, TroopType
from .official_state_catalog import OfficialStateId
from .provider_identity import SkillProviderRef
from .skill_definition import (
    ApplyStateSkillEffectSpec,
    PreparationMode,
    SkillDefinition,
    SkillTargetMode,
    SkillType,
)
from .skill_runtime import SkillRuntime, SkillSlot
from .stage11_state_params import CriticalStateParams
from .unit import UnitRuntime
from .troop_skill_config import TroopSkillConfig
from .state_modifiers import register_modifier_state_definitions
from .troop_skills.bai_ma_yi_cong import CONFIG as BAI_MA_YI_CONG_CONFIG
from .troop_skills.hu_bao_qi import CONFIG as HU_BAO_QI_CONFIG
from .troop_skills.wu_dang_fei_jun import CONFIG as WU_DANG_FEI_JUN_CONFIG
from .troop_skills.xian_zhen_ying import CONFIG as XIAN_ZHEN_YING_CONFIG
from .troop_skills.bai_er_bing import CONFIG as BAI_ER_BING_CONFIG
from .troop_skills.da_ji_shi import CONFIG as DA_JI_SHI_CONFIG
from .troop_skills.teng_jia_bing import CONFIG as TENG_JIA_BING_CONFIG
from .troop_skills.jin_fan_jun import CONFIG as JIN_FAN_JUN_CONFIG
from .state_application_reaction import register_application_reaction_definitions
from .normal_attack_followup import register_followup_state_definition


class TroopAdmissionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    REJECTED_PHASE_ILLEGAL = "REJECTED_PHASE_ILLEGAL"
    REJECTED_ALREADY_INSTALLED = "REJECTED_ALREADY_INSTALLED"
    REJECTED_BASELINE_DISABLED = "REJECTED_BASELINE_DISABLED"
    REJECTED_INVALID_TROOP = "REJECTED_INVALID_TROOP"
    REJECTED_TEAM_INVARIANT_VIOLATION = "REJECTED_TEAM_INVARIANT_VIOLATION"
    REJECTED_NOT_FOUND = "REJECTED_NOT_FOUND"
    REJECTED_CONFLICTING_SPECIAL_TROOP = "REJECTED_CONFLICTING_SPECIAL_TROOP"
    REJECTED_PROVIDER_SLOT_CONFLICT = "REJECTED_PROVIDER_SLOT_CONFLICT"


class TroopAdmissionRejectedError(RuntimeError):
    """Raised when troop skill admission is rejected during PRE_BATTLE."""

    def __init__(self, status: TroopAdmissionStatus, skill_id: str, owner_id: str, reason: str | None = None) -> None:
        super().__init__(
            f"Troop skill admission rejected: status={status}, skill_id={skill_id}, owner_id={owner_id}, reason={reason}"
        )
        self.status = status
        self.skill_id = skill_id
        self.owner_id = owner_id
        self.reason = reason


@dataclass(frozen=True, slots=True)
class TroopAdmissionResult:
    status: TroopAdmissionStatus
    skill_id: str
    owner_id: str
    special_troop_id: SpecialTroopId | None = None
    converted_unit_ids: tuple[str, ...] = ()
    reason: str | None = None


def process_pre_battle_troop_skills(context: BattleContext, systems: object) -> None:
    """Scan registered SkillRuntimes for TROOP skills and auto-admit them during PRE_BATTLE."""
    troop_runtimes = [
        rt for rt in context.skill_runtimes.values()
        if rt.definition.skill_type == SkillType.TROOP and rt.enabled
    ]
    for rt in troop_runtimes:
        result = admit_and_install_troop_skill(context, systems, rt)
        if result.status == TroopAdmissionStatus.REJECTED_ALREADY_INSTALLED:
            continue
        if result.status != TroopAdmissionStatus.SUCCESS:
            raise TroopAdmissionRejectedError(
                status=result.status,
                skill_id=result.skill_id,
                owner_id=result.owner_id,
                reason=result.reason,
            )


XILIANG_CAVALRY_SKILL_ID = "20097"
XILIANG_CAVALRY_SKILL_NAME = "西凉铁骑"
XILIANG_CAVALRY_CRIT_CHANCE = 0.25
XILIANG_CAVALRY_CRIT_BONUS = 1.0
XILIANG_CAVALRY_DURATION_EXPIRES_ROUND = 4
XILIANG_CAVALRY_SPEED_BASELINE = 57.0
XILIANG_CAVALRY_SPEED_SCALE_DENOMINATOR = 800.0


def calculate_xiliang_crit_chance(base_rate: float, combat_speed: float) -> float:
    """冻结公式：BaseRate(LV) * (1 + (CombatSpeed - 57) / 800)."""
    if isinstance(base_rate, bool) or not isinstance(base_rate, (int, float)):
        raise TypeError("base_rate must be numeric")
    if isinstance(combat_speed, bool) or not isinstance(combat_speed, (int, float)):
        raise TypeError("combat_speed must be numeric")
    return float(base_rate) * (
        1.0
        + (float(combat_speed) - XILIANG_CAVALRY_SPEED_BASELINE)
        / XILIANG_CAVALRY_SPEED_SCALE_DENOMINATOR
    )


def _create_xiliang_cavalry_definition_with_crit(crit_chance: float) -> SkillDefinition:
    params = CriticalStateParams(
        chance=float(crit_chance),
        bonus=XILIANG_CAVALRY_CRIT_BONUS,
    )
    return SkillDefinition(
        skill_id=XILIANG_CAVALRY_SKILL_ID,
        name=XILIANG_CAVALRY_SKILL_NAME,
        activation_rate=1.0,
        target_mode=SkillTargetMode.FIXED_ALL_TEAM,
        effect_specs=(
            ApplyStateSkillEffectSpec(
                state_id=OfficialStateId.CRITICAL.value,
                runtime_params=params,
                expires_round=XILIANG_CAVALRY_DURATION_EXPIRES_ROUND,
                expires_phase=BattlePhase.ROUND_START.value,
            ),
        ),
        skill_type=SkillType.TROOP,
        preparation_mode=PreparationMode.NONE,
    )


def _resolve_xiliang_definition(
    context: BattleContext,
    systems: object,
    owner: UnitRuntime,
) -> SkillDefinition:
    """Resolve the current PRE_BATTLE Xiliang crit rate.

    If the canonical team commander is Ma Teng, read his current final combat
    speed from AttributeSystem and apply the frozen speed-scaling formula.
    Otherwise use the frozen full-level base rate (25%).
    """
    team_units = [u for u in context.units.values() if u.team_id == owner.team_id]
    commander = next(
        (u for u in team_units if u.lineup_position is LineupPosition.COMMANDER),
        None,
    )
    crit_chance = XILIANG_CAVALRY_CRIT_CHANCE
    if commander is not None and commander.name == "马腾":
        attribute_system = getattr(systems, "attribute_system", None)
        if attribute_system is None:
            raise RuntimeError("Xiliang Cavalry Ma Teng scaling requires AttributeSystem")
        combat_speed = attribute_system.get_speed(context, commander)
        crit_chance = calculate_xiliang_crit_chance(
            XILIANG_CAVALRY_CRIT_CHANCE,
            combat_speed,
        )
    return _create_xiliang_cavalry_definition_with_crit(crit_chance)

def create_xiliang_cavalry_definition() -> SkillDefinition:
    """创建满级西凉铁骑基础定义；马腾缩放在 PRE_BATTLE 通过 AttributeSystem 动态解析。"""
    return _create_xiliang_cavalry_definition_with_crit(XILIANG_CAVALRY_CRIT_CHANCE)


XILIANG_CAVALRY_CONFIG = TroopSkillConfig(
    skill_id=XILIANG_CAVALRY_SKILL_ID,
    name=XILIANG_CAVALRY_SKILL_NAME,
    required_troop_type=TroopType.CAVALRY,
    target_special_troop_id=SpecialTroopId.XILIANG_CAVALRY,
    definition_factory=create_xiliang_cavalry_definition,
    definition_resolver=_resolve_xiliang_definition,
)

# Canonical Registry: key is strictly the canonical skill_id
TROOP_SKILL_REGISTRY: dict[str, TroopSkillConfig] = {
    XILIANG_CAVALRY_SKILL_ID: XILIANG_CAVALRY_CONFIG,
    BAI_MA_YI_CONG_CONFIG.skill_id: BAI_MA_YI_CONG_CONFIG,
    HU_BAO_QI_CONFIG.skill_id: HU_BAO_QI_CONFIG,
    WU_DANG_FEI_JUN_CONFIG.skill_id: WU_DANG_FEI_JUN_CONFIG,
    XIAN_ZHEN_YING_CONFIG.skill_id: XIAN_ZHEN_YING_CONFIG,
    BAI_ER_BING_CONFIG.skill_id: BAI_ER_BING_CONFIG,
    DA_JI_SHI_CONFIG.skill_id: DA_JI_SHI_CONFIG,
    TENG_JIA_BING_CONFIG.skill_id: TENG_JIA_BING_CONFIG,
    JIN_FAN_JUN_CONFIG.skill_id: JIN_FAN_JUN_CONFIG,
}


def resolve_opening_troop_definition(context, systems, skill_id: str, owner_id: str) -> SkillDefinition:
    cfg = TROOP_SKILL_REGISTRY[skill_id]
    if cfg.opening_definition_resolver is None:
        raise ValueError("troop skill has no opening definition")
    return cfg.opening_definition_resolver(context, systems, context.units[owner_id])


def create_xiliang_cavalry_runtime(
    owner_id: str,
    *,
    slot: SkillSlot = SkillSlot.LEARNED_1,
    enabled: bool = True,
) -> SkillRuntime:
    """生产环境构造西凉铁骑技能运行时实例。

    收口生产工厂参数：必须严格绑定法定冻结参数 (skill_id='20097', 25% crit, TroopType.CAVALRY)。
    生产调用方无权通过工厂覆盖核心数值。
    """
    defn = create_xiliang_cavalry_definition()
    return SkillRuntime(
        definition=defn,
        owner_id=owner_id,
        skill_slot=slot,
        enabled=enabled,
    )


def admit_and_install_troop_skill(
    context: BattleContext,
    systems,
    runtime: SkillRuntime,
) -> TroopAdmissionResult:
    """通用兵种准入校验、特殊兵种身份转换、战法解析与规则依赖图注入原语。

    处理规范：
    1. Phase Guard: 仅允许在 PRE_BATTLE 阶段执行准入。Mid-battle 尝试一律拒绝。
    2. Canonical Registry Lookup: 仅按 canonical skill_id 查表，拒绝 Name Spoofing。
    3. Duplicate Guard: 若当前队伍已经确立该特殊兵种身份或已安装，防止重复安装累加。
    4. 基础兵种准入与队伍一致性校验 (Team Troop Invariant Preflight): 校验持有者及同队所有武将基础兵种必须一致且匹配。
    5. Dynamic Definition Resolution: 在 mutation 前解析依赖 PRE_BATTLE 当前属性的技能参数（如马腾速度缩放）。
    6. 原子准入 (Atomic Mutation): 所有预检与动态参数解析通过后，方可原子写入身份并执行 Effect。
    7. 规则依赖图注入 (Rule Dependency Edge): 绑定 StateNode -> ProviderNode 依赖，实现威慑抑制与 DEATH-E。
    """
    # 1. Phase Guard
    if context.current_phase != BattlePhase.PRE_BATTLE.value:
        return TroopAdmissionResult(
            status=TroopAdmissionStatus.REJECTED_PHASE_ILLEGAL,
            skill_id=runtime.definition.skill_id,
            owner_id=runtime.owner_id,
            reason=f"Troop skills can only be admitted during PRE_BATTLE phase, current phase is {context.current_phase}",
        )

    # Baseline-disabled runtimes never enter troop admission and must not mutate identity/effects.
    if not runtime.enabled:
        return TroopAdmissionResult(
            status=TroopAdmissionStatus.REJECTED_BASELINE_DISABLED,
            skill_id=runtime.definition.skill_id,
            owner_id=runtime.owner_id,
            reason="baseline-disabled troop runtime is not admitted",
        )

    owner = context.get_unit(runtime.owner_id)
    if owner is None:
        return TroopAdmissionResult(
            status=TroopAdmissionStatus.REJECTED_NOT_FOUND,
            skill_id=runtime.definition.skill_id,
            owner_id=runtime.owner_id,
            reason=f"owner unit '{runtime.owner_id}' not found in battle context",
        )

    # 2. Canonical Lookup by skill_id only (Reject Name Spoof)
    cfg = TROOP_SKILL_REGISTRY.get(runtime.definition.skill_id)
    if cfg is None:
        return TroopAdmissionResult(
            status=TroopAdmissionStatus.REJECTED_NOT_FOUND,
            skill_id=runtime.definition.skill_id,
            owner_id=runtime.owner_id,
            reason=f"unsupported troop skill id '{runtime.definition.skill_id}'",
        )

    # 3. Duplicate Installation Prevention
    team_units = [u for u in context.units.values() if u.team_id == owner.team_id]
    if any(u.special_troop_id not in (None, cfg.target_special_troop_id) for u in team_units):
        return TroopAdmissionResult(
            status=TroopAdmissionStatus.REJECTED_CONFLICTING_SPECIAL_TROOP,
            skill_id=runtime.definition.skill_id, owner_id=runtime.owner_id,
            reason="team already has a different special troop identity",
        )
    if owner.special_troop_id == cfg.target_special_troop_id:
        return TroopAdmissionResult(
            status=TroopAdmissionStatus.REJECTED_ALREADY_INSTALLED,
            skill_id=runtime.definition.skill_id,
            owner_id=runtime.owner_id,
            special_troop_id=owner.special_troop_id,
            reason=f"Troop skill '{cfg.name}' is already installed for team {owner.team_id}",
        )

    # 4. 基础兵种准入与队伍一致性预检 (Team Troop Invariant Preflight)
    if owner.troop_type != cfg.required_troop_type:
        return TroopAdmissionResult(
            status=TroopAdmissionStatus.REJECTED_INVALID_TROOP,
            skill_id=runtime.definition.skill_id,
            owner_id=runtime.owner_id,
            reason=(
                f"{cfg.name} requires base troop {cfg.required_troop_type.value}, "
                f"got {owner.troop_type.value if owner.troop_type else 'None'}"
            ),
        )

    # Team Invariant: All active members in the same team must have identical base troop type matching requirement
    for u in team_units:
        if u.troop_type != cfg.required_troop_type:
            return TroopAdmissionResult(
                status=TroopAdmissionStatus.REJECTED_TEAM_INVARIANT_VIOLATION,
                skill_id=runtime.definition.skill_id,
                owner_id=runtime.owner_id,
                reason=(
                    f"Team troop invariant violation: unit '{u.unit_id}' has troop type "
                    f"'{u.troop_type.value if u.troop_type else 'None'}', expected '{cfg.required_troop_type.value}'"
                ),
            )

    # A resident slot must identify this exact runtime, never an unrelated provider.
    if runtime.skill_slot is not None:
        resident = context.skill_runtimes.get(runtime.owner_id, runtime.skill_slot)
        if resident is not None and resident is not runtime:
            return TroopAdmissionResult(
                status=TroopAdmissionStatus.REJECTED_PROVIDER_SLOT_CONFLICT,
                skill_id=runtime.definition.skill_id, owner_id=runtime.owner_id,
                reason="provider slot already belongs to another runtime",
            )

    # 5. Skill-specific PRE_BATTLE definition resolution happens before mutation.
    if (cfg.opening_definition_resolver is not None or cfg.requires_provider_slot) and runtime.skill_slot is None:
        return TroopAdmissionResult(
            status=TroopAdmissionStatus.REJECTED_PROVIDER_SLOT_CONFLICT,
            skill_id=runtime.definition.skill_id, owner_id=runtime.owner_id,
            reason="opening skill requires canonical provider slot",
        )
    # 西凉铁骑在马腾统领时通过 AttributeSystem 读取当前最终实战速度并套用冻结公式。
    effective_definition = (
        cfg.definition_resolver(context, systems, owner)
        if cfg.definition_resolver is not None
        else cfg.definition_factory()
    )
    effective_runtime = SkillRuntime(
        definition=effective_definition,
        owner_id=runtime.owner_id,
        skill_slot=runtime.skill_slot,
        enabled=runtime.enabled,
    )

    supplemental = (cfg.supplemental_definition_resolver(context, systems, owner)
                    if cfg.supplemental_definition_resolver is not None else None)
    # --- ATOMIC PREFLIGHT COMPLETE; PERFORM MUTATION ---

    register_modifier_state_definitions(context.states)
    register_application_reaction_definitions(context.states)
    register_followup_state_definition(context.states)

    # 6. 特殊兵种身份绑定：全队同盟友军转换为特殊兵种
    converted_ids = []
    for u in team_units:
        u.special_troop_id = cfg.target_special_troop_id
        converted_ids.append(u.unit_id)

    # 7. 注册 runtime (若未注册)
    if runtime.skill_slot is not None:
        existing = context.skill_runtimes.get(runtime.owner_id, runtime.skill_slot)
        if existing is None:
            context.skill_runtimes.register(runtime)

    provider_ref = (
        SkillProviderRef(
            owner_id=runtime.owner_id,
            skill_slot=runtime.skill_slot,
            skill_id=runtime.definition.skill_id,
        )
        if runtime.skill_slot is not None
        else None
    )

    # 8. PRE_BATTLE 解析技能并执行 Effect
    res = systems.skill_resolver.resolve(context, effective_runtime)
    effects = list(res.effects)
    if supplemental is not None:
        extra_runtime = SkillRuntime(supplemental, runtime.owner_id, runtime.skill_slot, runtime.enabled)
        effects.extend(systems.skill_resolver.resolve(context, extra_runtime).effects)
    for effect in effects:
        exec_res = systems.effect_executor.execute(context, effect)
        # 9. 自动挂接 Provider 依赖边，以实现威慑抑制传播
        if (
            provider_ref is not None
            and getattr(exec_res, "state_instance", None) is not None
            and hasattr(systems, "dependency_evaluation_support")
        ):
            instance = exec_res.state_instance
            systems.dependency_evaluation_support.add_dependency(
                StateNode(instance.instance_id),
                ProviderNode(provider_ref),
            )

    if cfg.opening_definition_resolver is not None:
        systems.scheduled_skill_support.schedule(context, runtime)

    return TroopAdmissionResult(
        status=TroopAdmissionStatus.SUCCESS,
        skill_id=runtime.definition.skill_id,
        owner_id=runtime.owner_id,
        special_troop_id=cfg.target_special_troop_id,
        converted_unit_ids=tuple(converted_ids),
    )

