"""Read-only deterministic priority extension of the frozen target owner."""
from .context import BattleContext
from .target_system import TargetSystem
from .unit import UnitRuntime
from .enums import LineupPosition


class PriorityTargetSystem(TargetSystem):
    def __init__(self, targets: TargetSystem | None = None) -> None:
        self._targets = targets or self

    def lowest_troop_allies(self, context: BattleContext, unit: UnitRuntime) -> list[UnitRuntime]:
        return sorted(self._targets.allies(context, unit, include_self=True),
                      key=lambda candidate: (candidate.troops, candidate.lineup_position))

    def lowest_attribute_units(self, context, candidates, attributes, attribute):
        """Live attribute priority; ties follow canonical lineup then unit ID."""
        getters = {"attack": attributes.get_attack, "defense": attributes.get_defense,
                   "intelligence": attributes.get_intelligence, "speed": attributes.get_speed}
        if attribute not in getters:
            raise ValueError("unsupported priority attribute")
        return sorted(candidates, key=lambda u: (getters[attribute](context, u), u.lineup_position, u.unit_id))

    def most_lost_troop_deputies(self, context: BattleContext, unit: UnitRuntime,
                                initial_troops: dict[str, int]) -> list[UnitRuntime]:
        """Descending net loss since entry; ties use the canonical deputy slot."""
        candidates = [u for u in self._targets.allies(context, unit, include_self=True)
                      if u.lineup_position in (LineupPosition.DEPUTY_1, LineupPosition.DEPUTY_2)
                      and u.unit_id in initial_troops]
        return sorted(candidates, key=lambda u: (-(initial_troops[u.unit_id] - u.troops),
                                                 u.lineup_position, u.unit_id))


class FastestTargetSystem(PriorityTargetSystem):
    """Maximum-speed query over the frozen target owner; ties remain explicit."""
    def fastest_allies(self, context, unit, attributes):
        candidates = self._targets.allies(context, unit)
        if not candidates:
            return []
        speeds = {u.unit_id: attributes.get_speed(context, u) for u in candidates}
        maximum = max(speeds.values())
        return [u for u in candidates if speeds[u.unit_id] == maximum]
