from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .state_definition import StateDefinition
from .state_registry import StateRegistry


class OfficialStateCategory(str, Enum):
    CONTINUOUS = "CONTINUOUS"
    FUNCTIONAL = "FUNCTIONAL"
    CONTROL = "CONTROL"
    OTHER = "OTHER"


class OfficialStateId(str, Enum):
    BURN = "burn"
    FLOOD = "flood"
    POISON = "poison"
    ROUT = "rout"
    SANDSTORM = "sandstorm"
    REBELLION = "rebellion"
    FIRST_AID = "first_aid"
    RECUPERATION = "recuperation"

    COMBO = "combo"
    EVASION = "evasion"
    BARRIER = "barrier"
    CLEAVE = "cleave"
    COUNTERATTACK = "counterattack"
    DAMAGE_SPLIT = "damage_split"
    DAMAGE_SHARE = "damage_share"
    INSIGHT = "insight"
    FIRST_STRIKE = "first_strike"
    AMBUSH = "ambush"
    SURE_HIT = "sure_hit"
    DEFENSE_PIERCE = "defense_pierce"
    WEAPON_LIFESTEAL = "weapon_lifesteal"
    STRATEGY_LIFESTEAL = "strategy_lifesteal"
    CHAIN_LINK = "chain_link"
    GUARD = "guard"
    VIGILANCE = "vigilance"

    SILENCE = "silence"
    DISARM = "disarm"
    CONFUSION = "confusion"
    WEAKNESS = "weakness"
    HEALING_BAN = "healing_ban"
    TAUNT = "taunt"
    FALSE_REPORT = "false_report"
    PROVOKE = "provoke"
    EQUIPMENT_DISABLE = "equipment_disable"
    CAPTURE = "capture"
    STUN = "stun"

    CRITICAL = "critical"
    STRATEGY_CRITICAL = "strategy_critical"
    DAMAGE_REDUCTION_PIERCE = "damage_reduction_pierce"
    INTIMIDATION = "intimidation"


@dataclass(frozen=True, slots=True)
class OfficialStateEntry:
    state_id: OfficialStateId
    name: str
    hint_id: int
    category: OfficialStateCategory
    official_text: str


OFFICIAL_STATE_CATALOG: tuple[OfficialStateEntry, ...] = (
    OfficialStateEntry(OfficialStateId.BURN, "灼烧", 690072, OfficialStateCategory.CONTINUOUS, "持续性状态，每回合持续对武将部队造成伤害"),
    OfficialStateEntry(OfficialStateId.FLOOD, "水攻", 690073, OfficialStateCategory.CONTINUOUS, "持续性状态，拥有该状态的武将行动时将受到伤害"),
    OfficialStateEntry(OfficialStateId.POISON, "中毒", 690074, OfficialStateCategory.CONTINUOUS, "持续性状态，拥有该状态的武将行动时将受到伤害"),
    OfficialStateEntry(OfficialStateId.ROUT, "溃逃", 690075, OfficialStateCategory.CONTINUOUS, "持续性状态，拥有该状态的武将行动时将受到伤害"),
    OfficialStateEntry(OfficialStateId.SANDSTORM, "沙暴", 690076, OfficialStateCategory.CONTINUOUS, "持续性状态，拥有该状态的武将行动时将受到伤害"),
    OfficialStateEntry(OfficialStateId.REBELLION, "叛逃", 690077, OfficialStateCategory.CONTINUOUS, "持续性状态，每回合对武将部队造成伤害，无视防御"),
    OfficialStateEntry(OfficialStateId.FIRST_AID, "急救", 690078, OfficialStateCategory.CONTINUOUS, "持续性状态，受到伤害时恢复兵力"),
    OfficialStateEntry(OfficialStateId.RECUPERATION, "休整", 690079, OfficialStateCategory.CONTINUOUS, "持续性状态，每回合恢复一次兵力"),

    OfficialStateEntry(OfficialStateId.COMBO, "连击", 690081, OfficialStateCategory.FUNCTIONAL, "功能性增益状态，每回合可额外进行一次普通攻击"),
    OfficialStateEntry(OfficialStateId.EVASION, "规避", 690082, OfficialStateCategory.FUNCTIONAL, "功能性增益状态，可回避伤害，规避几率为非线性叠加"),
    OfficialStateEntry(OfficialStateId.BARRIER, "抵御", 690083, OfficialStateCategory.FUNCTIONAL, "功能性增益状态，可免疫伤害"),
    OfficialStateEntry(OfficialStateId.CLEAVE, "群攻", 690084, OfficialStateCategory.FUNCTIONAL, "功能性增益状态，普通攻击对目标同部队其他武将造成伤害"),
    OfficialStateEntry(OfficialStateId.COUNTERATTACK, "反击", 690085, OfficialStateCategory.FUNCTIONAL, "功能性增益状态，受到普通攻击时对攻击者造成伤害"),
    OfficialStateEntry(OfficialStateId.DAMAGE_SPLIT, "分摊", 690086, OfficialStateCategory.FUNCTIONAL, "功能性增益状态，各目标分别承担一部分伤害"),
    OfficialStateEntry(OfficialStateId.DAMAGE_SHARE, "分担", 690087, OfficialStateCategory.FUNCTIONAL, "功能性增益状态，为目标承担一部分伤害"),
    OfficialStateEntry(OfficialStateId.INSIGHT, "洞察", 690089, OfficialStateCategory.FUNCTIONAL, "功能性增益状态，可免疫控制状态"),
    OfficialStateEntry(OfficialStateId.FIRST_STRIKE, "先攻", 690090, OfficialStateCategory.FUNCTIONAL, "功能性增益状态，让武将在回合内优先行动，多名武将同时拥有先攻状态时则根据速度高低决定行动顺序"),
    OfficialStateEntry(OfficialStateId.AMBUSH, "遇袭", 690091, OfficialStateCategory.FUNCTIONAL, "功能性减益状态，让武将在回合内延后行动，多名武将同时拥有先攻状态时则根据速度高低决定行动顺序"),
    OfficialStateEntry(OfficialStateId.SURE_HIT, "必中", 690092, OfficialStateCategory.FUNCTIONAL, "功能性增益状态，发动战法及普通攻击命中目标时无视规避及抵御"),
    OfficialStateEntry(OfficialStateId.DEFENSE_PIERCE, "破阵", 690093, OfficialStateCategory.FUNCTIONAL, "功能性增益状态，造成伤害时无视目标统率及智力"),
    OfficialStateEntry(OfficialStateId.WEAPON_LIFESTEAL, "倒戈", 690094, OfficialStateCategory.FUNCTIONAL, "功能性增益状态，造成兵刃伤害时，根据伤害量恢复自身一定兵力"),
    OfficialStateEntry(OfficialStateId.STRATEGY_LIFESTEAL, "攻心", 690095, OfficialStateCategory.FUNCTIONAL, "功能性增益状态，造成谋略伤害时，根据伤害量恢复自身一定兵力"),
    OfficialStateEntry(OfficialStateId.CHAIN_LINK, "铁索连环", 690097, OfficialStateCategory.FUNCTIONAL, "功能性减益状态，任一目标受到伤害时，反馈一定百分比的伤害给其他目标"),
    OfficialStateEntry(OfficialStateId.GUARD, "援护", 690098, OfficialStateCategory.FUNCTIONAL, "功能性增益状态，为目标承担普通攻击"),
    OfficialStateEntry(OfficialStateId.VIGILANCE, "警戒", 690099, OfficialStateCategory.FUNCTIONAL, "功能性增益状态，可减少单次受到的伤害"),

    OfficialStateEntry(OfficialStateId.SILENCE, "计穷", 690101, OfficialStateCategory.CONTROL, "控制状态，无法发动主动战法"),
    OfficialStateEntry(OfficialStateId.DISARM, "缴械", 690102, OfficialStateCategory.CONTROL, "控制状态，无法发动普通攻击"),
    OfficialStateEntry(OfficialStateId.CONFUSION, "混乱", 690103, OfficialStateCategory.CONTROL, "控制状态，战法和普通攻击无差别选择目标"),
    OfficialStateEntry(OfficialStateId.WEAKNESS, "虚弱", 690104, OfficialStateCategory.CONTROL, "控制状态，无法造成伤害"),
    OfficialStateEntry(OfficialStateId.HEALING_BAN, "禁疗", 690105, OfficialStateCategory.CONTROL, "控制状态，无法恢复兵力"),
    OfficialStateEntry(OfficialStateId.TAUNT, "嘲讽", 690106, OfficialStateCategory.CONTROL, "控制状态，强迫目标的普通攻击以自身为目标"),
    OfficialStateEntry(OfficialStateId.FALSE_REPORT, "伪报", 690107, OfficialStateCategory.CONTROL, "控制状态，无视洞察效果，暂时使目标的指挥战法和被动战法失效"),
    OfficialStateEntry(OfficialStateId.PROVOKE, "挑拨", 690108, OfficialStateCategory.CONTROL, "控制状态，强迫目标施放的战法选择自己"),
    OfficialStateEntry(OfficialStateId.EQUIPMENT_DISABLE, "破坏", 690109, OfficialStateCategory.CONTROL, "控制状态，使目标的装备失效"),
    OfficialStateEntry(OfficialStateId.CAPTURE, "捕获", 690110, OfficialStateCategory.CONTROL, "控制状态，无法行动和造成伤害、禁用指挥和被动战法、进入禁疗状态、无法被其友方武将选中"),
    OfficialStateEntry(OfficialStateId.STUN, "震慑", 690111, OfficialStateCategory.CONTROL, "控制状态，无法行动"),

    OfficialStateEntry(OfficialStateId.CRITICAL, "会心", 690070, OfficialStateCategory.OTHER, "有概率造成双倍兵刃伤害"),
    OfficialStateEntry(OfficialStateId.STRATEGY_CRITICAL, "奇谋", 690069, OfficialStateCategory.OTHER, "有概率造成双倍谋略伤害"),
    OfficialStateEntry(OfficialStateId.DAMAGE_REDUCTION_PIERCE, "看破", 690221, OfficialStateCategory.OTHER, "造成伤害时无视目标一定比例的受到伤害降低效果"),
    OfficialStateEntry(OfficialStateId.INTIMIDATION, "威慑", 690222, OfficialStateCategory.OTHER, "使目标1个战法失效，阵法除外"),
)


def register_official_state_definitions(registry: StateRegistry) -> None:
    """将官方静态目录显式转换并注册为 Stage 3 的最小 StateDefinition。"""
    for entry in OFFICIAL_STATE_CATALOG:
        registry.register_definition(
            StateDefinition(
                state_id=entry.state_id.value,
                name=entry.name,
                tags=frozenset({entry.category.value}),
            )
        )
