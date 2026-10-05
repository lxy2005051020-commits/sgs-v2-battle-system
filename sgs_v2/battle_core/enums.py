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


class TroopType(str, Enum):
    """单位当前兵种。

    当前基础兵刃公式只确认了枪兵与骑兵之间的克制倍率；
    其余已检验组合暂按 1.0 处理。
    """

    CAVALRY = "CAVALRY"
    SHIELD = "SHIELD"
    BOW = "BOW"
    SPEAR = "SPEAR"
    SIEGE = "SIEGE"


class SpecialTroopId(str, Enum):
    """进阶特殊兵种身份标识 (Stage14-0 Foundation & Pilot).

    特殊兵种身份与基础四大兵种家族解耦，保持 base_troop_type 不变以继承基础克制拓扑。
    """

    XILIANG_CAVALRY = "XILIANG_CAVALRY"  # 西凉铁骑 (Base: CAVALRY)
    BAI_MA_YI_CONG = "BAI_MA_YI_CONG"  # 白马义从 (Base: BOW)
    HU_BAO_QI = "HU_BAO_QI"  # 虎豹骑 (Base: CAVALRY)
    WU_DANG_FEI_JUN = "WU_DANG_FEI_JUN"  # 无当飞军 (Base: BOW)
    BAI_ER_BING = "BAI_ER_BING"
    DA_JI_SHI = "DA_JI_SHI"
    QING_ZHOU_BING = "QING_ZHOU_BING"
    HU_WEI_JUN = "HU_WEI_JUN"
    XIAN_DENG_SI_SHI = "XIAN_DENG_SI_SHI"
    TENG_JIA_BING = "TENG_JIA_BING"
    XIAN_ZHEN_YING = "XIAN_ZHEN_YING"  # 陷阵营 (Base: SHIELD)


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


class DamageCalculationBasis(str, Enum):
    """伤害计算基础 (STAGE8_ADDENDUM §4, STAGE10.md §5)."""

    LIVE_RUNTIME = "LIVE_RUNTIME"
    FROZEN_APPLICATION = "FROZEN_APPLICATION"


CalculationBasis = DamageCalculationBasis

