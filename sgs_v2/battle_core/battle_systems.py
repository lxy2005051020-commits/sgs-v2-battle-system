from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from .action_order_system import ActionOrderSystem
from .action_system import ActionSystem
from .attribute_system import AttributeSystem
from .damage_system import DamageSystem
from .normal_attack_system import NormalAttackSystem
from .target_system import TargetSystem
from .troop_system import TroopSystem
from .victory_system import VictorySystem


@dataclass(slots=True)
class BattleSystems:
    """阶段 2 BattleSystem 组合根，供 BattleEngine 使用。"""

    attribute_system: AttributeSystem = field(default_factory=AttributeSystem)
    target_system: TargetSystem = field(default_factory=TargetSystem)
    troop_system: TroopSystem = field(default_factory=TroopSystem)
    victory_system: VictorySystem = field(default_factory=VictorySystem)

    weapon_troop_function_table: Mapping[int, int] | None = None
    weapon_random_percent_range: tuple[int, int] = (86, 94)
    weapon_low_damage_floor_range: tuple[int, int] = (5, 15)

    strategy_troop_function_table: Mapping[int, int] | None = None
    strategy_random_percent_range: tuple[int, int] = (86, 94)
    strategy_low_damage_floor_range: tuple[int, int] = (5, 15)

    action_order_system: ActionOrderSystem = field(init=False)
    damage_system: DamageSystem = field(init=False)
    normal_attack_system: NormalAttackSystem = field(init=False)
    action_system: ActionSystem = field(init=False)

    def __post_init__(self) -> None:
        self.action_order_system = ActionOrderSystem(self.attribute_system)
        self.damage_system = DamageSystem(
            self.attribute_system,
            weapon_troop_function_table=self.weapon_troop_function_table,
            weapon_random_percent_range=self.weapon_random_percent_range,
            weapon_low_damage_floor_range=self.weapon_low_damage_floor_range,
            strategy_troop_function_table=self.strategy_troop_function_table,
            strategy_random_percent_range=self.strategy_random_percent_range,
            strategy_low_damage_floor_range=self.strategy_low_damage_floor_range,
        )
        self.normal_attack_system = NormalAttackSystem(
            self.target_system, self.damage_system, self.troop_system
        )
        self.action_system = ActionSystem(self.normal_attack_system)
