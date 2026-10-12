from __future__ import annotations

from typing import TYPE_CHECKING

from .enums import LineupPosition
from .unit import UnitRuntime

if TYPE_CHECKING:
    from .attribute_system import AttributeSystem
    from .context import BattleContext


class PreBattleOrderSystem:
    """Deterministic ordering owner for PRE_BATTLE preparation phase skills.

    Implements:
    - RULE-01/RULE-04: Order by effective real-time speed descending at the current phase point.
    - Tiebreaker: attacker first (context.metadata.get("attacker_team_id")).
    - Intra-team tiebreaker: deterministic lineup position (COMMANDER, DEPUTY_1, DEPUTY_2), then unit_id.
    - Zero RNG consumption.
    - No Natural-Round First Strike / Ambush / Priority tier pollution.
    """

    __slots__ = ("_attributes",)

    def __init__(self, attribute_system: AttributeSystem) -> None:
        self._attributes = attribute_system

    def determine_order(
        self,
        context: BattleContext,
        units: list[UnitRuntime] | tuple[UnitRuntime, ...] | None = None,
    ) -> list[UnitRuntime]:
        """Determine deterministic execution order among alive candidate units for PRE_BATTLE."""
        if units is None:
            candidates = [u for u in context.units.values() if u.is_alive]
        else:
            candidates = [u for u in units if u.is_alive]

        if not candidates:
            return []

        # Read attacker_team_id strictly from context.metadata
        attacker_team_id = context.metadata.get("attacker_team_id")
        known_team_ids = {u.team_id for u in context.units.values()}

        valid_attacker_id: str | None = None
        if isinstance(attacker_team_id, str) and attacker_team_id in known_team_ids:
            valid_attacker_id = attacker_team_id

        # Group candidates by current effective speed
        # Speed is read dynamically through AttributeSystem
        speed_map: dict[str, float] = {
            u.unit_id: self._attributes.get_speed(context, u) for u in candidates
        }

        # A cross-team same-speed tie cannot be resolved without a real attacker.
        # Never silently substitute team-id lexical order for RULE-04.
        if valid_attacker_id is None:
            speed_teams: dict[float, set[str]] = {}
            for u in candidates:
                speed_teams.setdefault(speed_map[u.unit_id], set()).add(u.team_id)
            if any(len(teams) > 1 for teams in speed_teams.values()):
                raise ValueError(
                    "valid attacker_team_id metadata required for cross-team "
                    "equal-speed PRE_BATTLE ordering"
                )

        def sort_key(unit: UnitRuntime):
            speed = speed_map[unit.unit_id]
            # Higher speed first (-speed)
            # Attacker priority: 0 for attacker, 1 for others (if valid attacker exists)
            is_attacker_rank = 0 if (valid_attacker_id is not None and unit.team_id == valid_attacker_id) else 1
            lineup_pos = int(unit.lineup_position) if unit.lineup_position is not None else 99
            return (-speed, is_attacker_rank, unit.team_id, lineup_pos, unit.unit_id)

        return sorted(candidates, key=sort_key)
