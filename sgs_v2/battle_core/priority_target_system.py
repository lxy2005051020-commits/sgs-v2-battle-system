"""Read-only deterministic priority extension of the frozen target owner."""
from .context import BattleContext
from .target_system import TargetSystem
from .unit import UnitRuntime


class PriorityTargetSystem(TargetSystem):
    def __init__(self, targets: TargetSystem | None = None) -> None:
        self._targets = targets or self

    def lowest_troop_allies(self, context: BattleContext, unit: UnitRuntime) -> list[UnitRuntime]:
        return sorted(self._targets.allies(context, unit, include_self=True),
                      key=lambda candidate: (candidate.troops, candidate.lineup_position))


class FastestTargetSystem(PriorityTargetSystem):
    """Maximum-speed query over the frozen target owner; ties remain explicit."""
    def fastest_allies(self, context, unit, attributes):
        candidates = self._targets.allies(context, unit)
        if not candidates:
            return []
        speeds = {u.unit_id: attributes.get_speed(context, u) for u in candidates}
        maximum = max(speeds.values())
        return [u for u in candidates if speeds[u.unit_id] == maximum]
