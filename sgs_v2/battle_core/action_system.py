from __future__ import annotations

from .context import BattleContext
from .normal_attack_system import NormalAttackResult, NormalAttackSystem
from .unit import UnitRuntime


class ActionSystem:
    """处理一个单位的一次完整行动。

    阶段 2 只调度普通攻击；阶段 4 的震慑等状态将在此统一阻止整次行动。
    """

    def __init__(self, normal_attack_system: NormalAttackSystem) -> None:
        self._normal_attack = normal_attack_system

    def execute(self, context: BattleContext, actor: UnitRuntime) -> NormalAttackResult | None:
        if not actor.is_alive:
            return None
        return self._normal_attack.execute(context, actor)
