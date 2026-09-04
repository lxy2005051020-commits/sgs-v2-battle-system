from __future__ import annotations

from enum import Enum, IntEnum


class BattlePhase(str, Enum):
    PRE_BATTLE = "PRE_BATTLE"
    ROUND_START = "ROUND_START"
    ACTION_ORDER = "ACTION_ORDER"
    UNIT_ACTION_START = "UNIT_ACTION_START"
    UNIT_ACTION = "UNIT_ACTION"
    UNIT_ACTION_END = "UNIT_ACTION_END"
    ROUND_END = "ROUND_END"
    BATTLE_END = "BATTLE_END"


class BattleEndReason(str, Enum):
    TEAM_ELIMINATED = "TEAM_ELIMINATED"
    COMMANDER_DEFEATED = "COMMANDER_DEFEATED"
    MAX_ROUNDS = "MAX_ROUNDS"
    DRAW = "DRAW"


class LineupPosition(IntEnum):
    """武将在队伍中的固定阵容位置，也是确定性结算的默认顺序。"""

    COMMANDER = 0
    DEPUTY_1 = 1
    DEPUTY_2 = 2


class DamageType(str, Enum):
    """伤害性质，同时决定 DamageSystem 使用哪一种基础伤害公式。"""

    WEAPON = "WEAPON"          # 兵刃伤害：基础兵刃伤害 × coefficient
    STRATEGY = "STRATEGY"      # 谋略伤害：基础谋略伤害 × coefficient


class DamageSourceType(str, Enum):
    """伤害来源维度，与兵刃/谋略的伤害性质相互独立。"""

    NORMAL_ATTACK = "NORMAL_ATTACK"
    SKILL = "SKILL"
    CONTINUOUS = "CONTINUOUS"
    COUNTER = "COUNTER"
