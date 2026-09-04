from __future__ import annotations

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
    damage_scale: float = 1.0

    action_order_system: ActionOrderSystem = field(init=False)
    damage_system: DamageSystem = field(init=False)
    normal_attack_system: NormalAttackSystem = field(init=False)
    action_system: ActionSystem = field(init=False)

    def __post_init__(self) -> None:
        self.action_order_system = ActionOrderSystem(self.attribute_system)
        self.damage_system = DamageSystem(
            self.attribute_system, damage_scale=self.damage_scale
        )
        self.normal_attack_system = NormalAttackSystem(
            self.target_system, self.damage_system, self.troop_system
        )
        self.action_system = ActionSystem(self.normal_attack_system)
