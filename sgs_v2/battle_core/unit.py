from __future__ import annotations

from dataclasses import dataclass

from .enums import LineupPosition


@dataclass(slots=True)
class UnitRuntime:
    """
    单位在“一场战斗内”的运行态。

    注意：
    - attack / defense / speed 是基础值；最终属性由 AttributeSystem 统一计算。
    - troops 的实际增减只能由 TroopSystem 执行。
    - lineup_position 明确表示主将/第一副将/第二副将。
    - is_commander 仅保留为兼容字段，真实主将身份统一由 lineup_position 决定。
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

    def __post_init__(self) -> None:
        if not self.unit_id:
            raise ValueError("unit_id cannot be empty")
        if not self.team_id:
            raise ValueError("team_id cannot be empty")
        if self.max_troops <= 0:
            raise ValueError("max_troops must be > 0")
        if not 0 <= self.troops <= self.max_troops:
            raise ValueError("troops must be within [0, max_troops]")

        # 兼容旧构造方式：显式 is_commander=True 且未给阵容位置时，视为主将。
        if self.lineup_position is None and self.is_commander:
            self.lineup_position = LineupPosition.COMMANDER

        # 一旦指定阵容位置，主将身份只由阵容位置决定，避免出现两套真相。
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
            "speed": self.speed,
            "is_commander": self.is_commander,
            "lineup_position": (
                self.lineup_position.name if self.lineup_position is not None else None
            ),
            "is_alive": self.is_alive,
        }
