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
