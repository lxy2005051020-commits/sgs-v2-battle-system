from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .context import BattleContext
from .enums import BattlePhase, SpecialTroopId, TroopType
from .events import EventType
from .official_state_catalog import OfficialStateId
from .skill_definition import (
    ApplyStateSkillEffectSpec,
    PreparationMode,
    SkillDefinition,
    SkillTargetMode,
    SkillType,
)
from .skill_runtime import SkillRuntime, SkillSlot
from .stage11_state_params import CriticalStateParams


class TroopAdmissionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    REJECTED_INVALID_TROOP = "REJECTED_INVALID_TROOP"
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


def create_xiliang_cavalry_definition(
    *,
    skill_id: str = XILIANG_CAVALRY_SKILL_ID,
    name: str = XILIANG_CAVALRY_SKILL_NAME,
    crit_chance: float = XILIANG_CAVALRY_CRIT_CHANCE,
) -> SkillDefinition:
    """创建符合冻结合同的西凉铁骑技能规格定义。

    合同要点：
    - 类型：TROOP (兵种战法)
    - 准备模式：NONE
    - 发动率：1.0 (战前必定生效)
    - 目标域：FIXED_ALL_TEAM (我军全体 3 人)
    - 效果：挂载 OfficialStateId.CRITICAL (690070)，会心几率 25%，持续前 3 回合 (expires_round=4, phase=ROUND_START)
    """
    params = CriticalStateParams(
        chance=crit_chance,
        bonus=XILIANG_CAVALRY_CRIT_BONUS,
    )
    return SkillDefinition(
        skill_id=skill_id,
        name=name,
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


def create_xiliang_cavalry_runtime(
    owner_id: str,
    *,
    slot: SkillSlot = SkillSlot.LEARNED_1,
    skill_id: str = XILIANG_CAVALRY_SKILL_ID,
    name: str = XILIANG_CAVALRY_SKILL_NAME,
    crit_chance: float = XILIANG_CAVALRY_CRIT_CHANCE,
    enabled: bool = True,
) -> SkillRuntime:
    """创建西凉铁骑技能运行时实例。"""
    defn = create_xiliang_cavalry_definition(
        skill_id=skill_id,
        name=name,
        crit_chance=crit_chance,
    )
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
    """在 PRE_BATTLE 阶段执行兵种准入校验、特殊兵种身份转换并执行战法解析与效果挂载。

    规则要求：
    1. 准入校验：检查所属单位及队伍基础兵种是否匹配（西凉铁骑要求 TroopType.CAVALRY）。
       若不匹配，拒绝准入并返回 REJECTED_INVALID_TROOP，不改变兵种身份，不挂载效果。
    2. 身份转换：成功准入后，将同队所有武将的 special_troop_id 标记为 SpecialTroopId.XILIANG_CAVALRY，
       而基础 troop_type 保持不变（继承基础骑兵克制）。
    3. 战法注册与解析：将 runtime 注册至 context.skill_runtimes（若尚未注册），
       并通过 systems.skill_resolver 解析出有序 Effect，最后由 systems.effect_executor 执行。
    """
    owner = context.get_unit(runtime.owner_id)
    if owner is None:
        return TroopAdmissionResult(
            status=TroopAdmissionStatus.REJECTED_NOT_FOUND,
            skill_id=runtime.definition.skill_id,
            owner_id=runtime.owner_id,
            reason=f"owner unit '{runtime.owner_id}' not found in battle context",
        )

    # 1. 基础兵种准入校验
    if runtime.definition.skill_id == XILIANG_CAVALRY_SKILL_ID or runtime.definition.name == XILIANG_CAVALRY_SKILL_NAME:
        if owner.troop_type != TroopType.CAVALRY:
            return TroopAdmissionResult(
                status=TroopAdmissionStatus.REJECTED_INVALID_TROOP,
                skill_id=runtime.definition.skill_id,
                owner_id=runtime.owner_id,
                reason=f"Xiliang Cavalry requires base troop CAVALRY, got {owner.troop_type}",
            )

        # 2. 特殊兵种身份绑定：全队同盟友军转换为西凉铁骑
        team_units = [u for u in context.units.values() if u.team_id == owner.team_id]
        converted_ids = []
        for u in team_units:
            u.special_troop_id = SpecialTroopId.XILIANG_CAVALRY
            converted_ids.append(u.unit_id)

        # 3. 注册 runtime (若未注册)
        if runtime.skill_slot is not None:
            existing = context.skill_runtimes.get(runtime.owner_id, runtime.skill_slot)
            if existing is None:
                context.skill_runtimes.register(runtime)

        # 4. PRE_BATTLE 解析技能并执行 Effect
        res = systems.skill_resolver.resolve(context, runtime)
        for effect in res.effects:
            systems.effect_executor.execute(context, effect)

        return TroopAdmissionResult(
            status=TroopAdmissionStatus.SUCCESS,
            skill_id=runtime.definition.skill_id,
            owner_id=runtime.owner_id,
            special_troop_id=SpecialTroopId.XILIANG_CAVALRY,
            converted_unit_ids=tuple(converted_ids),
        )

    return TroopAdmissionResult(
        status=TroopAdmissionStatus.REJECTED_NOT_FOUND,
        skill_id=runtime.definition.skill_id,
        owner_id=runtime.owner_id,
        reason=f"unsupported troop skill id '{runtime.definition.skill_id}'",
    )
