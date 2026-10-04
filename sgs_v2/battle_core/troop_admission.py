from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Callable

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


class TroopAdmissionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    REJECTED_PHASE_ILLEGAL = "REJECTED_PHASE_ILLEGAL"
    REJECTED_ALREADY_INSTALLED = "REJECTED_ALREADY_INSTALLED"
    REJECTED_INVALID_TROOP = "REJECTED_INVALID_TROOP"
    REJECTED_TEAM_INVARIANT_VIOLATION = "REJECTED_TEAM_INVARIANT_VIOLATION"
    REJECTED_COMMANDER_SCALING_UNRESOLVED = "REJECTED_COMMANDER_SCALING_UNRESOLVED"
    REJECTED_NOT_FOUND = "REJECTED_NOT_FOUND"


@dataclass(frozen=True, slots=True)
class TroopAdmissionResult:
    status: TroopAdmissionStatus
    skill_id: str
    owner_id: str
    special_troop_id: SpecialTroopId | None = None
    converted_unit_ids: tuple[str, ...] = ()
    reason: str | None = None


XILIANG_CAVALRY_SKILL_ID = "20097"
XILIANG_CAVALRY_SKILL_NAME = "西凉铁骑"
XILIANG_CAVALRY_CRIT_CHANCE = 0.25
XILIANG_CAVALRY_CRIT_BONUS = 1.0
XILIANG_CAVALRY_DURATION_EXPIRES_ROUND = 4


@dataclass(frozen=True, slots=True)
class TroopSkillConfig:
    """静态兵种战法配置声明，支持通用准入与挂载扩展。"""

    skill_id: str
    name: str
    required_troop_type: TroopType
    target_special_troop_id: SpecialTroopId
    definition_factory: Callable[[], SkillDefinition]
    # 统领特殊加成校验函数：返回 None 表示通过，返回错误字符串表示触发 Fail Closed
    commander_clause_validator: Callable[[BattleContext, UnitRuntime], str | None] | None = None


def _validate_xiliang_commander_clause(context: BattleContext, owner: UnitRuntime) -> str | None:
    """校验西凉铁骑马腾统领条款。

    根据合同与规范：
    - 若马腾统领，则提高会心几率受速度影响；
    - 当前官方未公开速度拟合数学公式，属于 BOUNDED_UNKNOWN；
    - 依据项目治理准则，系统必须明确 Fail Closed，严禁静默降级为固定 25% 或胡乱猜测公式。
    - 统领身份识别统一采用 Canonical Truth: lineup_position == LineupPosition.COMMANDER。
      is_commander 仅为兼容字段，不得作为主将判定依据。
    - 注意：当前 Runtime 尚未建立独立的 general_id/hero_id 模板体系，name-based 识别为显式临时边界 (TEMPORARY EXPLICIT BOUNDARY)。
    """
    team_units = [u for u in context.units.values() if u.team_id == owner.team_id]
    commander = next((u for u in team_units if u.lineup_position is LineupPosition.COMMANDER), None)
    if commander is not None and commander.name == "马腾":
        return (
            "Ma Teng commander scaling clause ('若马腾统领，则提高会心几率受速度影响') "
            "is BOUNDED_UNKNOWN (speed formula unverified). Configuration fails closed."
        )
    return None


def create_xiliang_cavalry_definition() -> SkillDefinition:
    """创建符合冻结合同的西凉铁骑技能规格定义。

    合同要点：
    - 类型：TROOP (兵种战法)
    - 准备模式：NONE
    - 发动率：1.0 (战前必定生效)
    - 目标域：FIXED_ALL_TEAM (我军全体 3 人)
    - 效果：挂载 OfficialStateId.CRITICAL (690070)，会心几率 25%，持续前 3 回合 (expires_round=4, phase=ROUND_START)
    """
    params = CriticalStateParams(
        chance=XILIANG_CAVALRY_CRIT_CHANCE,
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


XILIANG_CAVALRY_CONFIG = TroopSkillConfig(
    skill_id=XILIANG_CAVALRY_SKILL_ID,
    name=XILIANG_CAVALRY_SKILL_NAME,
    required_troop_type=TroopType.CAVALRY,
    target_special_troop_id=SpecialTroopId.XILIANG_CAVALRY,
    definition_factory=create_xiliang_cavalry_definition,
    commander_clause_validator=_validate_xiliang_commander_clause,
)

# Canonical Registry: key is strictly the canonical skill_id
TROOP_SKILL_REGISTRY: dict[str, TroopSkillConfig] = {
    XILIANG_CAVALRY_SKILL_ID: XILIANG_CAVALRY_CONFIG,
}


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
    5. 统领条款检查 (Fail Closed): 若包含未解析的公式条款，执行严格的 Fail Closed 拒绝。
    6. 原子准入 (Atomic Mutation): 所有预检通过后，方可原子写入身份并解析执行 Effect。
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

    # 5. 统领特殊加成检查 (Fail Closed)
    if cfg.commander_clause_validator is not None:
        rejection_reason = cfg.commander_clause_validator(context, owner)
        if rejection_reason is not None:
            return TroopAdmissionResult(
                status=TroopAdmissionStatus.REJECTED_COMMANDER_SCALING_UNRESOLVED,
                skill_id=runtime.definition.skill_id,
                owner_id=runtime.owner_id,
                reason=rejection_reason,
            )

    # --- ATOMIC PREFLIGHT COMPLETE; PERFORM MUTATION ---

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
    res = systems.skill_resolver.resolve(context, runtime)
    for effect in res.effects:
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

    return TroopAdmissionResult(
        status=TroopAdmissionStatus.SUCCESS,
        skill_id=runtime.definition.skill_id,
        owner_id=runtime.owner_id,
        special_troop_id=cfg.target_special_troop_id,
        converted_unit_ids=tuple(converted_ids),
    )

