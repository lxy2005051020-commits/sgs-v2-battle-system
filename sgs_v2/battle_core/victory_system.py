from __future__ import annotations

from .context import BattleContext, BattleResult
from .enums import BattleEndReason


class VictorySystem:
    """统一判定主将阵亡、全军、最大回合和战平。"""

    def check(self, context: BattleContext) -> BattleResult | None:
        team_ids = {unit.team_id for unit in context.units.values()}

        # 主将阵亡是最高优先级结束条件。
        defeated_commander_teams = {
            team_id
            for team_id in team_ids
            if not context.commander_of(team_id).is_alive
        }

        if defeated_commander_teams:
            surviving_teams = team_ids - defeated_commander_teams
            if len(surviving_teams) == 1:
                return self._build_result(
                    context,
                    winner_team_id=next(iter(surviving_teams)),
                    reason=BattleEndReason.COMMANDER_DEFEATED,
                )
            return self._build_result(
                context,
                winner_team_id=None,
                reason=BattleEndReason.DRAW,
            )

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
