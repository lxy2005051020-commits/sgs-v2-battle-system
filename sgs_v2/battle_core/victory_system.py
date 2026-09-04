from __future__ import annotations

from .context import BattleContext, BattleResult
from .enums import BattleEndReason


class VictorySystem:
    """统一判定全军、主将、最大回合和战平。"""

    def check(self, context: BattleContext) -> BattleResult | None:
        alive_teams = context.alive_team_ids()
        if len(alive_teams) == 0:
            return self._build_result(
                context,
                winner_team_id=None,
                reason=BattleEndReason.DRAW,
            )
        if len(alive_teams) == 1:
            return self._build_result(
                context,
                winner_team_id=next(iter(alive_teams)),
                reason=BattleEndReason.TEAM_ELIMINATED,
            )

        teams_with_commanders = {
            unit.team_id for unit in context.units.values() if unit.is_commander
        }
        for team_id in teams_with_commanders:
            commanders = [
                unit for unit in context.units.values()
                if unit.team_id == team_id and unit.is_commander
            ]
            if commanders and not any(unit.is_alive for unit in commanders):
                surviving_enemies = {
                    unit.team_id for unit in context.units.values()
                    if unit.team_id != team_id and unit.is_alive
                }
                if len(surviving_enemies) == 1:
                    return self._build_result(
                        context,
                        winner_team_id=next(iter(surviving_enemies)),
                        reason=BattleEndReason.COMMANDER_DEFEATED,
                    )
        return None

    def resolve_max_rounds(self, context: BattleContext) -> BattleResult:
        totals = context.troop_totals_by_team()
        if not totals:
            return self._build_result(context, winner_team_id=None, reason=BattleEndReason.DRAW)
        max_troops = max(totals.values())
        winners = [team_id for team_id, troops in totals.items() if troops == max_troops]
        return self._build_result(
            context,
            winner_team_id=winners[0] if len(winners) == 1 else None,
            reason=BattleEndReason.MAX_ROUNDS if len(winners) == 1 else BattleEndReason.DRAW,
        )

    @staticmethod
    def _build_result(
        context: BattleContext,
        *,
        winner_team_id: str | None,
        reason: BattleEndReason,
    ) -> BattleResult:
        return BattleResult(
            winner_team_id=winner_team_id,
            reason=reason,
            rounds_completed=context.current_round,
            final_troops={unit.unit_id: unit.troops for unit in context.units.values()},
        )
