from __future__ import annotations

from .attribute_system import AttributeSystem
from .context import BattleContext
from .official_state_catalog import OfficialStateId
from .unit import UnitRuntime


class ActionOrderSystem:
    """Frozen Stage11 primary-action ordering owner."""

    FIRST_STRIKE_PRIORITY = 1
    NORMAL_PRIORITY = 0
    AMBUSH_PRIORITY = -1

    def __init__(self, attribute_system: AttributeSystem, stage11_state_runtime=None) -> None:
        self._attributes = attribute_system
        self._stage11 = stage11_state_runtime

    def determine_order(self, context: BattleContext) -> list[UnitRuntime]:
        alive_units = [unit for unit in context.units.values() if unit.is_alive]
        groups: dict[tuple[int, float], list[UnitRuntime]] = {}
        for unit in alive_units:
            priority = self._priority_tier(context, unit)
            speed = self._attributes.get_speed(context, unit)
            groups.setdefault((priority, speed), []).append(unit)

        result: list[UnitRuntime] = []
        for priority, speed in sorted(groups, reverse=True):
            group = groups[(priority, speed)]
            team_ids = {unit.team_id for unit in group}
            attacker_team_id = context.metadata.get("attacker_team_id")
            if len(team_ids) > 1:
                if not isinstance(attacker_team_id, str) or attacker_team_id not in team_ids:
                    # PROJECT_RUNTIME_DEFAULT for legacy BattleContext callers that
                    # predate explicit attacker/defender metadata. Production setup
                    # should provide attacker_team_id; the fallback is deterministic
                    # and consumes no RNG.
                    attacker_team_id = sorted(team_ids)[0]
                group.sort(
                    key=lambda unit: (
                        0 if unit.team_id == attacker_team_id else 1,
                        int(unit.lineup_position),
                    )
                )
            else:
                group.sort(key=lambda unit: int(unit.lineup_position))
            result.extend(group)
        return result

    def _has(self, context: BattleContext, unit_id: str, state_id: OfficialStateId) -> bool:
        if self._stage11 is not None:
            return self._stage11.has_effective(context, unit_id, state_id)
        return context.states.has(owner_id=unit_id, state_id=state_id.value)

    def _priority_tier(self, context: BattleContext, unit: UnitRuntime) -> int:
        has_first = self._has(context, unit.unit_id, OfficialStateId.FIRST_STRIKE)
        has_surprise = self._has(context, unit.unit_id, OfficialStateId.AMBUSH)
        if has_first and not has_surprise:
            return self.FIRST_STRIKE_PRIORITY
        if has_surprise and not has_first:
            return self.AMBUSH_PRIORITY
        return self.NORMAL_PRIORITY
