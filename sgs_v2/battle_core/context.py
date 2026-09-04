from __future__ import annotations

from dataclasses import dataclass, field

from .events import EventBus
from .random_system import RandomSystem
from .state_registry import StateRegistry
from .unit import UnitRuntime
from .enums import BattleEndReason, LineupPosition


@dataclass(frozen=True, slots=True)
class BattleResult:
    winner_team_id: str | None
    reason: BattleEndReason
    rounds_completed: int
    final_troops: dict[str, int]


@dataclass(slots=True)
class BattleContext:
    """
    一场战斗的唯一上下文容器。

    BattleEngine / BattleSystem / SkillRuntime 后续都通过 context 协作，
    避免模块之间私下抓全局变量。
    """

    battle_id: str
    units: dict[str, UnitRuntime]
    event_bus: EventBus
    random: RandomSystem
    max_rounds: int = 8

    states: StateRegistry = field(default_factory=StateRegistry)
    current_round: int = 0
    current_phase: str = "NOT_STARTED"
    ended: bool = False
    result: BattleResult | None = None

    metadata: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.battle_id:
            raise ValueError("battle_id cannot be empty")
        if not self.units:
            raise ValueError("battle must contain at least one unit")
        if self.max_rounds <= 0:
            raise ValueError("max_rounds must be > 0")

        for key, unit in self.units.items():
            if key != unit.unit_id:
                raise ValueError(
                    f"unit key '{key}' does not match "
                    f"UnitRuntime.unit_id '{unit.unit_id}'"
                )

        team_ids = {unit.team_id for unit in self.units.values()}
        if len(team_ids) < 2:
            raise ValueError("battle must contain at least two teams")

        for team_id in team_ids:
            team_units = [u for u in self.units.values() if u.team_id == team_id]
            if not 1 <= len(team_units) <= 3:
                raise ValueError("each team must contain between 1 and 3 units")

            commanders = [
                u for u in team_units
                if u.lineup_position is LineupPosition.COMMANDER
            ]
            if len(commanders) != 1:
                raise ValueError(
                    f"team '{team_id}' must contain exactly one commander"
                )

            used_positions: set[LineupPosition] = set()
            for unit in team_units:
                if unit.lineup_position is None:
                    raise ValueError(
                        f"unit '{unit.unit_id}' must define lineup_position"
                    )
                if unit.lineup_position in used_positions:
                    raise ValueError(
                        f"team '{team_id}' has duplicate lineup position "
                        f"{unit.lineup_position.name}"
                    )
                used_positions.add(unit.lineup_position)

            expected_positions = {
                LineupPosition.COMMANDER,
                *(
                    [LineupPosition.DEPUTY_1]
                    if len(team_units) >= 2 else []
                ),
                *(
                    [LineupPosition.DEPUTY_2]
                    if len(team_units) >= 3 else []
                ),
            }
            if used_positions != expected_positions:
                raise ValueError(
                    f"team '{team_id}' lineup positions must be contiguous from commander"
                )

    def get_unit(self, unit_id: str) -> UnitRuntime:
        try:
            return self.units[unit_id]
        except KeyError as exc:
            raise KeyError(f"unknown unit_id: {unit_id}") from exc

    def commander_of(self, team_id: str) -> UnitRuntime:
        return self.unit_at_position(team_id, LineupPosition.COMMANDER)

    def unit_at_position(
        self,
        team_id: str,
        position: LineupPosition,
    ) -> UnitRuntime:
        for unit in self.units.values():
            if unit.team_id == team_id and unit.lineup_position is position:
                return unit
        raise KeyError(
            f"team '{team_id}' has no unit at position {position.name}"
        )

    def alive_team_ids(self) -> set[str]:
        return {u.team_id for u in self.units.values() if u.is_alive}

    def troop_totals_by_team(self) -> dict[str, int]:
        totals: dict[str, int] = {}
        for unit in self.units.values():
            totals[unit.team_id] = totals.get(unit.team_id, 0) + unit.troops
        return totals
