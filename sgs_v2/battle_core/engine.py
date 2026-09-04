from __future__ import annotations

from dataclasses import dataclass

from .context import BattleContext, BattleResult
from .enums import BattlePhase
from .events import EventType
from .battle_systems import BattleSystems


@dataclass(slots=True)
class BattleEngine:
    """
    战斗推进器。

    Engine 只负责：
    - 推进阶段
    - 推进回合
    - 调用规则/系统
    - 在关键节点检查战斗是否结束
    - 发出明确 Event

    Engine 不认识任何具体战法名称。
    """

    context: BattleContext
    systems: BattleSystems

    def run(self) -> BattleResult:
        if self.context.ended:
            if self.context.result is None:
                raise RuntimeError("battle ended without a result")
            return self.context.result

        self._enter_phase(BattlePhase.PRE_BATTLE)
        self.context.event_bus.publish(
            event_type=EventType.BATTLE_STARTED,
            phase=self.context.current_phase,
            round_no=0,
            payload={
                "battle_id": self.context.battle_id,
                "max_rounds": self.context.max_rounds,
                "units": [u.snapshot() for u in self.context.units.values()],
            },
        )

        initial_result = self.systems.victory_system.check(self.context)
        if initial_result is not None:
            return self._finish(initial_result)

        for round_no in range(1, self.context.max_rounds + 1):
            self.context.current_round = round_no

            self._enter_phase(BattlePhase.ROUND_START)
            self.context.event_bus.publish(
                event_type=EventType.ROUND_STARTED,
                phase=self.context.current_phase,
                round_no=round_no,
            )

            self._enter_phase(BattlePhase.ACTION_ORDER)
            order = self.systems.action_order_system.determine_order(self.context)
            self.context.event_bus.publish(
                event_type=EventType.ACTION_ORDER_DECIDED,
                phase=self.context.current_phase,
                round_no=round_no,
                payload={"order": [u.unit_id for u in order]},
            )

            for actor in order:
                # 顺序表生成后，单位可能已经被前一个单位击败。
                if not actor.is_alive:
                    continue

                self._enter_phase(BattlePhase.UNIT_ACTION_START)
                self.context.event_bus.publish(
                    event_type=EventType.UNIT_ACTION_STARTED,
                    phase=self.context.current_phase,
                    round_no=round_no,
                    actor_id=actor.unit_id,
                )

                self._enter_phase(BattlePhase.UNIT_ACTION)
                self.systems.action_system.execute(self.context, actor)

                result = self.systems.victory_system.check(self.context)

                self._enter_phase(BattlePhase.UNIT_ACTION_END)
                self.context.event_bus.publish(
                    event_type=EventType.UNIT_ACTION_ENDED,
                    phase=self.context.current_phase,
                    round_no=round_no,
                    actor_id=actor.unit_id,
                )

                if result is not None:
                    return self._finish(result)

            self._enter_phase(BattlePhase.ROUND_END)
            self.context.event_bus.publish(
                event_type=EventType.ROUND_ENDED,
                phase=self.context.current_phase,
                round_no=round_no,
                payload={"team_troops": self.context.troop_totals_by_team()},
            )

            result = self.systems.victory_system.check(self.context)
            if result is not None:
                return self._finish(result)

        return self._finish(self.systems.victory_system.resolve_max_rounds(self.context))

    def _enter_phase(self, phase: BattlePhase) -> None:
        self.context.current_phase = phase.value
        self.context.event_bus.publish(
            event_type=EventType.PHASE_ENTERED,
            phase=phase.value,
            round_no=self.context.current_round,
            payload={"phase": phase.value},
        )

    def _finish(self, result: BattleResult) -> BattleResult:
        self.context.ended = True
        self.context.result = result

        self._enter_phase(BattlePhase.BATTLE_END)
        self.context.event_bus.publish(
            event_type=EventType.BATTLE_ENDED,
            phase=self.context.current_phase,
            round_no=self.context.current_round,
            payload={
                "winner_team_id": result.winner_team_id,
                "reason": result.reason.value,
                "rounds_completed": result.rounds_completed,
                "final_troops": result.final_troops,
            },
        )
        return result
