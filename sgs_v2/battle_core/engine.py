from __future__ import annotations

from dataclasses import dataclass

from .battle_finalization_coordinator import FinalizationResult
from .battle_systems import BattleSystems
from .context import BattleContext, BattleResult
from .enums import BattlePhase
from .events import EventType
from .execution_right_system import (
    FutureBranchKind,
    LegacyFinalizationBarrier,
    admit_action_scope,
)
from .rule_hooks import RoundStartHook, UnitActionStartHook


@dataclass(slots=True)
class BattleEngine:
    """战斗推进器；不认识具体状态或具体 Effect 类型。"""

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

        # Barrier 1: INITIAL_SETTLED
        self.systems.finalization_coordinator.observe_legacy_barrier(
            self.context,
            LegacyFinalizationBarrier.INITIAL_SETTLED,
        )
        claim = self.systems.finalization_coordinator.claim_finalized_projection()
        if claim is not None:
            permit, fin_res = claim
            self.systems.finalization_coordinator.consume_projection_permit(permit)
            return self._apply_finalized_battle_result(fin_res)

        for round_no in range(1, self.context.max_rounds + 1):
            self.context.current_round = round_no

            self._enter_phase(BattlePhase.ROUND_START)
            self.systems.state_lifecycle_system.expire_at(
                self.context,
                round_no=round_no,
                phase=BattlePhase.ROUND_START.value,
            )
            self.context.event_bus.publish(
                event_type=EventType.ROUND_STARTED,
                phase=self.context.current_phase,
                round_no=round_no,
            )
            self.systems.rule_hook_system.process(
                self.context,
                RoundStartHook(round_no=round_no),
            )

            # Barrier 2: ROUND_START_HOOKS_SETTLED
            self.systems.finalization_coordinator.observe_legacy_barrier(
                self.context,
                LegacyFinalizationBarrier.ROUND_START_HOOKS_SETTLED,
            )
            claim = self.systems.finalization_coordinator.claim_finalized_projection()
            if claim is not None:
                permit, fin_res = claim
                self.systems.finalization_coordinator.consume_projection_permit(permit)
                return self._apply_finalized_battle_result(fin_res)

            self._enter_phase(BattlePhase.ACTION_ORDER)
            order = self.systems.action_order_system.determine_order(self.context)
            self.context.event_bus.publish(
                event_type=EventType.ACTION_ORDER_DECIDED,
                phase=self.context.current_phase,
                round_no=round_no,
                payload={"order": [u.unit_id for u in order]},
            )

            for actor in order:
                if not actor.is_alive:
                    continue

                self._enter_phase(BattlePhase.UNIT_ACTION_START)
                self.context.event_bus.publish(
                    event_type=EventType.UNIT_ACTION_STARTED,
                    phase=self.context.current_phase,
                    round_no=round_no,
                    actor_id=actor.unit_id,
                )
                self.systems.rule_hook_system.process(
                    self.context,
                    UnitActionStartHook(
                        round_no=round_no,
                        actor_id=actor.unit_id,
                    ),
                )

                # Barrier 3: UNIT_ACTION_START_HOOKS_SETTLED
                self.systems.finalization_coordinator.observe_legacy_barrier(
                    self.context,
                    LegacyFinalizationBarrier.UNIT_ACTION_START_HOOKS_SETTLED,
                )

                if (
                    actor.is_alive
                    and not self.systems.finalization_coordinator.is_latched_or_finalized
                ):
                    parent_scope = f"round_{round_no}_actor_{actor.unit_id}"
                    permit = self.systems.future_admission_gate.request_admission(
                        branch_kind=FutureBranchKind.NEXT_ACTION,
                        parent_scope_identity=parent_scope,
                        id_allocator=self.context.id_allocator,
                    )
                    if permit is not None:
                        self._enter_phase(BattlePhase.UNIT_ACTION)
                        action_scope = admit_action_scope(
                            context=self.context,
                            gate=self.systems.future_admission_gate,
                            permit=permit,
                            actor=actor,
                            parent_scope_identity=parent_scope,
                        )
                        try:
                            self.systems.action_system.execute(
                                context=self.context,
                                actor=actor,
                                action_scope=action_scope,
                            )
                        finally:
                            action_scope.mark_terminal()
                            self.systems.finalization_coordinator.complete_action_scope(
                                context=self.context,
                                scope=action_scope,
                            )
                        # Barrier 4: ACTION_SETTLED
                        self.systems.finalization_coordinator.observe_legacy_barrier(
                            self.context,
                            LegacyFinalizationBarrier.ACTION_SETTLED,
                        )

                self._enter_phase(BattlePhase.UNIT_ACTION_END)
                self.context.event_bus.publish(
                    event_type=EventType.UNIT_ACTION_ENDED,
                    phase=self.context.current_phase,
                    round_no=round_no,
                    actor_id=actor.unit_id,
                )

                claim = self.systems.finalization_coordinator.claim_finalized_projection()
                if claim is not None:
                    permit, fin_res = claim
                    self.systems.finalization_coordinator.consume_projection_permit(permit)
                    return self._apply_finalized_battle_result(fin_res)

            self._enter_phase(BattlePhase.ROUND_END)
            self.context.event_bus.publish(
                event_type=EventType.ROUND_ENDED,
                phase=self.context.current_phase,
                round_no=round_no,
                payload={"team_troops": self.context.troop_totals_by_team()},
            )
            self.systems.state_lifecycle_system.expire_at(
                self.context,
                round_no=round_no,
                phase=BattlePhase.ROUND_END.value,
            )

            # Barrier 5: ROUND_END_SETTLED
            self.systems.finalization_coordinator.observe_legacy_barrier(
                self.context,
                LegacyFinalizationBarrier.ROUND_END_SETTLED,
            )
            claim = self.systems.finalization_coordinator.claim_finalized_projection()
            if claim is not None:
                permit, fin_res = claim
                self.systems.finalization_coordinator.consume_projection_permit(permit)
                return self._apply_finalized_battle_result(fin_res)

        # Barrier 6: MAX_ROUND_SETTLED
        self.systems.finalization_coordinator.observe_legacy_barrier(
            self.context,
            LegacyFinalizationBarrier.MAX_ROUND_SETTLED,
        )
        claim = self.systems.finalization_coordinator.claim_finalized_projection()
        if claim is None:
            raise RuntimeError("MAX_ROUND_SETTLED failed to produce finalization result")
        permit, fin_res = claim
        self.systems.finalization_coordinator.consume_projection_permit(permit)
        return self._apply_finalized_battle_result(fin_res)

    def _enter_phase(self, phase: BattlePhase) -> None:
        self.context.current_phase = phase.value
        self.context.event_bus.publish(
            event_type=EventType.PHASE_ENTERED,
            phase=phase.value,
            round_no=self.context.current_round,
            payload={"phase": phase.value},
        )

    def _apply_finalized_battle_result(
        self,
        result: FinalizationResult,
    ) -> BattleResult:
        legacy_result = BattleResult(
            winner_team_id=result.winner_team_id,
            reason=result.reason,
            rounds_completed=result.rounds_completed,
            final_troops=dict(result.final_troops_snapshot),
        )
        self.context.ended = True
        self.context.result = legacy_result

        self._enter_phase(BattlePhase.BATTLE_END)
        self.context.event_bus.publish(
            event_type=EventType.BATTLE_ENDED,
            phase=self.context.current_phase,
            round_no=self.context.current_round,
            payload={
                "winner_team_id": legacy_result.winner_team_id,
                "reason": legacy_result.reason.value,
                "rounds_completed": legacy_result.rounds_completed,
                "final_troops": legacy_result.final_troops,
            },
        )
        return legacy_result
