from __future__ import annotations

from dataclasses import dataclass

from .attribute_system import AttributeSystem
from .context import BattleContext
from .enums import DamageSourceType, DamageType
from .unit import UnitRuntime


@dataclass(frozen=True, slots=True)
class DamageRequest:
    """一次伤害结算请求。

    DamageType 决定使用基础兵刃伤害或基础谋略伤害；
    coefficient 只负责对基础伤害进行倍率缩放。
    """

    source_id: str
    target_id: str
    damage_type: DamageType
    source_type: DamageSourceType
    coefficient: float = 1.0
    source_skill_id: str | None = None

    def __post_init__(self) -> None:
        if not self.source_id:
            raise ValueError("source_id cannot be empty")
        if not self.target_id:
            raise ValueError("target_id cannot be empty")
        if self.coefficient < 0:
            raise ValueError("coefficient must be >= 0")


@dataclass(frozen=True, slots=True)
class DamageResult:
    source_id: str
    target_id: str
    damage_type: DamageType
    source_type: DamageSourceType
    coefficient: float
    base_damage: float
    scaled_damage: float
    final_damage: int
    source_skill_id: str | None = None

    @property
    def requested_damage(self) -> int:
        """兼容旧调用方；正式字段为 final_damage。"""
        return self.final_damage


class DamageSystem:
    """统一计算伤害；不直接改变目标兵力。

    当前只完成伤害结算骨架：
    - WEAPON -> 基础兵刃伤害
    - STRATEGY -> 基础谋略伤害
    - 基础伤害 × coefficient -> scaled_damage
    - 后续增减伤等修正再作用于 scaled_damage

    基础兵刃/谋略的真实公式尚未封版。
    """

    def __init__(self, attribute_system: AttributeSystem, *, damage_scale: float = 1.0) -> None:
        if damage_scale < 0:
            raise ValueError("damage_scale must be >= 0")
        self._attributes = attribute_system
        # 暂时保留阶段 2 的全局占位倍率，仅用于兼容现有无战法测试。
        self.damage_scale = damage_scale

    def calculate(
        self,
        context: BattleContext,
        request: DamageRequest,
    ) -> DamageResult:
        source = context.get_unit(request.source_id)
        target = context.get_unit(request.target_id)

        if request.damage_type is DamageType.WEAPON:
            base_damage = self._calculate_weapon_base_damage(context, source, target)
        elif request.damage_type is DamageType.STRATEGY:
            base_damage = self._calculate_strategy_base_damage(context, source, target)
        else:
            raise ValueError(f"unsupported damage type: {request.damage_type}")

        scaled_damage = base_damage * request.coefficient

        # 阶段 2 兼容倍率仍保留在最终取整前；待真实基础伤害公式确定后移除。
        modified_damage = scaled_damage * self.damage_scale
        final_damage = max(1, int(modified_damage))

        return DamageResult(
            source_id=request.source_id,
            target_id=request.target_id,
            damage_type=request.damage_type,
            source_type=request.source_type,
            coefficient=request.coefficient,
            base_damage=base_damage,
            scaled_damage=scaled_damage,
            final_damage=final_damage,
            source_skill_id=request.source_skill_id,
        )

    def calculate_normal_attack(
        self,
        context: BattleContext,
        attacker: UnitRuntime,
        target: UnitRuntime,
    ) -> DamageResult:
        """兼容旧接口；普通攻击正式走 DamageRequest。"""
        return self.calculate(
            context,
            DamageRequest(
                source_id=attacker.unit_id,
                target_id=target.unit_id,
                damage_type=DamageType.WEAPON,
                source_type=DamageSourceType.NORMAL_ATTACK,
                coefficient=1.0,
            ),
        )

    def _calculate_weapon_base_damage(
        self,
        context: BattleContext,
        source: UnitRuntime,
        target: UnitRuntime,
    ) -> float:
        """基础兵刃伤害占位公式；下一阶段再替换为实测/校准公式。"""
        attack = self._attributes.get_attack(context, source)
        defense = self._attributes.get_defense(context, target)
        return attack * 100.0 / max(1.0, 100.0 + defense)

    def _calculate_strategy_base_damage(
        self,
        context: BattleContext,
        source: UnitRuntime,
        target: UnitRuntime,
    ) -> float:
        """基础谋略伤害占位入口。

        当前 UnitRuntime 尚未接入智力属性，因此不能伪造真实谋略伤害公式。
        在基础伤害模型封版前，显式拒绝谋略伤害结算。
        """
        raise NotImplementedError(
            "strategy base damage is not implemented yet; "
            "the intelligence-based base formula must be defined first"
        )
