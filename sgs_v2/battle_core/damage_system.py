from __future__ import annotations

from dataclasses import dataclass

from .attribute_system import AttributeSystem
from .context import BattleContext
from .unit import UnitRuntime


@dataclass(frozen=True, slots=True)
class DamageResult:
    attacker_id: str
    target_id: str
    requested_damage: int


class DamageSystem:
    """计算伤害；不直接改变目标兵力。"""

    def __init__(self, attribute_system: AttributeSystem, *, damage_scale: float = 1.0) -> None:
        if damage_scale < 0:
            raise ValueError("damage_scale must be >= 0")
        self._attributes = attribute_system
        self.damage_scale = damage_scale

    def calculate_normal_attack(
        self,
        context: BattleContext,
        attacker: UnitRuntime,
        target: UnitRuntime,
    ) -> DamageResult:
        attack = self._attributes.get_attack(context, attacker)
        defense = self._attributes.get_defense(context, target)
        raw = attack * 100.0 / max(1.0, 100.0 + defense)
        requested_damage = max(1, int(raw * self.damage_scale))
        return DamageResult(
            attacker_id=attacker.unit_id,
            target_id=target.unit_id,
            requested_damage=requested_damage,
        )
