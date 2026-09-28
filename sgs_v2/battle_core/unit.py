from __future__ import annotations

from dataclasses import dataclass, field

from .enums import LineupPosition, TroopType


@dataclass(slots=True)
class UnitRuntime:
    """
    单位在“一场战斗内”的运行态。

    注意：
    - attack / defense / intelligence / speed 是基础值；最终属性由 AttributeSystem 统一计算。
    - troops 的实际增减只能由 TroopSystem 执行。
    - lineup_position 明确表示主将/第一副将/第二副将。
    - is_commander 仅保留为兼容字段，真实主将身份统一由 lineup_position 决定。
    - level / morale / troop_type 供基础伤害公式读取；默认值保持旧构造调用兼容。
    - intelligence 使用 keyword-only 字段，避免改变旧的 UnitRuntime 位置参数含义。
    """

    unit_id: str
    name: str
    team_id: str

    max_troops: int
    troops: int

    attack: float
    defense: float
    speed: float

    is_commander: bool = False
    lineup_position: LineupPosition | None = None

    level: int = 50
    morale: int = 100
    troop_type: TroopType | None = None
    intelligence: float | None = field(default=None, kw_only=True)

    def __post_init__(self) -> None:
        if not self.unit_id:
            raise ValueError("unit_id cannot be empty")
        if not self.team_id:
            raise ValueError("team_id cannot be empty")
        if self.max_troops <= 0:
            raise ValueError("max_troops must be > 0")
        if not 0 <= self.troops <= self.max_troops:
            raise ValueError("troops must be within [0, max_troops]")
        if self.level <= 0:
            raise ValueError("level must be > 0")
        if not 0 <= self.morale <= 100:
            raise ValueError("morale must be within [0, 100]")
        if self.intelligence is not None and self.intelligence < 0:
            raise ValueError("intelligence must be >= 0")

        if self.lineup_position is None and self.is_commander:
            self.lineup_position = LineupPosition.COMMANDER

        if self.lineup_position is not None:
            self.is_commander = self.lineup_position is LineupPosition.COMMANDER

    @property
    def is_alive(self) -> bool:
        return self.troops > 0

    def snapshot(self) -> dict[str, object]:
        return {
            "unit_id": self.unit_id,
            "name": self.name,
            "team_id": self.team_id,
            "max_troops": self.max_troops,
            "troops": self.troops,
            "attack": self.attack,
            "defense": self.defense,
            "intelligence": self.intelligence,
            "speed": self.speed,
            "is_commander": self.is_commander,
            "lineup_position": (
                self.lineup_position.name if self.lineup_position is not None else None
            ),
            "level": self.level,
            "morale": self.morale,
            "troop_type": self.troop_type.value if self.troop_type is not None else None,
            "is_alive": self.is_alive,
        }
