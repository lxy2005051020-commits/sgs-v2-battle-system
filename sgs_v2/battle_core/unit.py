from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class UnitRuntime:
    """
    单位在“一场战斗内”的运行态。

    注意：
    - attack / defense / speed 目前只是阶段 1 的基础值。
    - 后续 AttributeSystem 上线后，最终属性必须由 AttributeSystem 计算，
      不允许战法直接修改这些最终值。
    - troops 是阶段 1 无战法验收所需的最小运行字段。
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

    def __post_init__(self) -> None:
        if not self.unit_id:
            raise ValueError("unit_id cannot be empty")
        if not self.team_id:
            raise ValueError("team_id cannot be empty")
        if self.max_troops <= 0:
            raise ValueError("max_troops must be > 0")
        if not 0 <= self.troops <= self.max_troops:
            raise ValueError("troops must be within [0, max_troops]")

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
            "is_alive": self.is_alive,
        }
