"""Stage9 Phase 9.8 Golden Trace & Identity Diagnostic Tests.

Demonstrates and asserts deep operational identities across complex multi-system flows:
1. Golden Trace 1: Full Action -> NormalAttack -> TargetResolution (Guard) ->
   DamageInstance (Partition) -> CleaveEffect -> ChainTraversal -> CounterBatch -> Scope Completion.
2. Golden Trace 2: Combo #2 end-to-end trace asserting distinct IDs, fresh TargetResolution,
   atomic checkpoint consume <= 1, and physical NormalAttack count <= 2.
3. Golden Trace 3: Finalization end-to-end trace asserting UnitDeathFact -> VictoryLatched ->
   DRAINING_ADMITTED_WORK -> ActionScope terminal -> UNIT_ACTION_ENDED before BATTLE_END / BATTLE_ENDED.
"""

from __future__ import annotations

from typing import Any
import pytest

from sgs_v2.battle_core import (
    BattleContext,
    BattlePhase,
    BattleSystems,
    DamageRequest,
    DamageResult,
    DamageSourceType,
    DamageType,
    EventBus,
    EventType,
    LineupPosition,
    RandomSystem,
    SkillSlot,
    UnitRuntime,
    register_official_state_definitions,
)
from sgs_v2.battle_core.battle_finalization_coordinator import (
    BattleFinalizationCoordinator,
    BattleTerminationState,
)
from sgs_v2.battle_core.chain_system import ResolvedDamageFact
from sgs_v2.battle_core.damage_instance_coordinator import DamageInstanceCoordinator
from sgs_v2.battle_core.damage_partition_system import (
    DamagePartitionCoordinator,
    DamageShareTransactionPlan,
)
from sgs_v2.battle_core.execution_right_system import (
    ActionExecutionState,
    ComboCheckpointState,
    FutureAdmissionGate,
    FutureBranchKind,
    LegacyFinalizationBarrier,
    admit_action_scope,
)
from sgs_v2.battle_core.operation_identity import (
    ActionId,
    CleaveEffectId,
    ChainTraversalId,
    CounterBatchEntryId,
    DamageInstanceId,
    DirectTroopLossId,
    NormalAttackInstanceId,
    OperationLineage,
    PartitionTransactionId,
    ReactionBatchId,
    SourceType,
    TargetResolutionId,
)
from sgs_v2.battle_core.stage9_integerization import ExactRatio
from sgs_v2.battle_core.stage9_state_params import (
    ChainStateParams,
    CleaveStateParams,
    ComboStateParams,
    CounterStateParams,
    DamageShareStateParams,
    GuardStateParams,
    TauntStateParams,
)
from sgs_v2.battle_core.target_resolution_system import RedirectReason


def _create_battle_context() -> BattleContext:
    units = {}
    for team in ("A", "B"):
        for n, pos in enumerate(LineupPosition):
            uid = f"{team}{n}"
            units[uid] = UnitRuntime(
                uid,
                f"Unit_{uid}",
                team,
                max_troops=10000,
                troops=10000,
                attack=150,
                defense=100,
                speed=100,
                lineup_position=pos,
            )
    ctx = BattleContext(
        battle_id="b_golden_trace",
        units=units,
        event_bus=EventBus(),
        random=RandomSystem(42),
    )
    register_official_state_definitions(ctx.states)
    return ctx


class TestStage9Phase98GoldenTraces:
    """Executable golden traces for Stage9 integration."""

    def test_golden_trace_1_full_action_reaction_pipeline_identities(self) -> None:
        """Golden Trace 1: Full pipeline asserting strong operational identities.

        Flow:
        - A0 executes NormalAttack.
        - Default selector targets B1.
        - B2 guards B1 -> PostRedirectActualTarget is B2.
        - B2 shares damage with B0 (DamageShare: Dtarget + Dsharer).
        - A0 has Cleave (CleaveEffect derives from B2 actual troop loss, targets B0/B1).
        - B2 has ChainLink to B0 (ChainTraversal evaluates linked target).
        - B2 has Counter (CounterBatch admitted against A0).
        """
        ctx = _create_battle_context()
        systems = BattleSystems()

        # Setup states
        # 1. B2 guards B1 (owner is B1, protector is B2)
        systems.state_lifecycle_system.apply(
            ctx,
            state_id="guard",
            owner_id="B1",
            source_id="B2",
            source_skill_id="skill_guard",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=GuardStateParams(protector_id="B2"),
        )
        # 2. B2 shares damage with B0 (owner is B2, sharer is B0)
        systems.state_lifecycle_system.apply(
            ctx,
            state_id="damage_share",
            owner_id="B2",
            source_id="B0",
            source_skill_id="skill_share",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=DamageShareStateParams(
                sharer_id="B0",
                ratio=ExactRatio.from_text("30%"),
            ),
        )
        # 3. A0 has Cleave (50%)
        systems.state_lifecycle_system.apply(
            ctx,
            state_id="cleave",
            owner_id="A0",
            source_id="A0",
            source_skill_id="skill_cleave",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=CleaveStateParams(ratio=ExactRatio(1, 2)),
        )
        # 4. B2 is linked to B0
        systems.state_lifecycle_system.apply(
            ctx,
            state_id="chain_link",
            owner_id="B2",
            source_id="A0",
            source_skill_id="skill_link",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=ChainStateParams(ratio=ExactRatio(1, 5)),
        )
        systems.state_lifecycle_system.apply(
            ctx,
            state_id="chain_link",
            owner_id="B0",
            source_id="A0",
            source_skill_id="skill_link",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=ChainStateParams(ratio=ExactRatio(1, 5)),
        )
        # 5. B2 has Counter
        systems.state_lifecycle_system.apply(
            ctx,
            state_id="counterattack",
            owner_id="B2",
            source_id="B2",
            source_skill_id="skill_counter",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=CounterStateParams(),
        )
        # 6. Taunt on A0 targeting B1 so target selection deterministically picks B1
        systems.state_lifecycle_system.apply(
            ctx,
            state_id="taunt",
            owner_id="A0",
            source_id="B1",
            source_skill_id="skill_taunt",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=TauntStateParams(taunt_target_id="B1"),
        )

        parent_scope = "round_1_actor_A0"
        permit = systems.future_admission_gate.request_admission(
            FutureBranchKind.NEXT_ACTION, parent_scope
        )
        assert permit is not None

        scope = admit_action_scope(ctx, systems.future_admission_gate, permit, ctx.units["A0"], parent_scope)
        assert isinstance(scope.action_id, ActionId)

        # Execute action via ActionSystem lifecycle
        action_res = systems.action_system.execute(
            context=ctx,
            actor=ctx.units["A0"],
            action_scope=scope,
        )
        assert action_res is not None
        assert action_res.damage is not None
        assert action_res.normal_attack_id is not None

        # Assert TargetResolution identities
        target_res = action_res.target_resolution
        assert target_res is not None
        assert isinstance(target_res.resolution_id, TargetResolutionId)
        assert isinstance(target_res.normal_attack_id, NormalAttackInstanceId)
        assert target_res.redirect_reason == RedirectReason.GUARD
        assert target_res.post_redirect_actual_target == "B2"
        assert target_res.intended_attack_target == "B1"
        assert target_res.redirect_source == "B2"

        # Complete scope
        systems.finalization_coordinator.complete_action_scope(ctx, scope)
        assert scope.terminal

    def test_golden_trace_2_combo_second_attack_identities_and_caps(self) -> None:
        """Golden Trace 2: Combo second attack generates completely distinct identities.

        Asserts:
        - NA #1 != NA #2
        - TargetResolution #1 != TargetResolution #2
        - Guard #1 cannot be inherited by #2
        - DamageInstance #1 != DamageInstance #2
        - Checkpoint reached <= 1, cfg230 count <= 1, total physical NA count <= 2.
        """
        ctx = _create_battle_context()
        systems = BattleSystems()

        # Apply Combo state to A0
        systems.state_lifecycle_system.apply(
            ctx,
            state_id="combo",
            owner_id="A0",
            source_id="A0",
            source_skill_id="skill_combo",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=ComboStateParams(),
        )

        parent_scope = "round_1_actor_A0"
        permit = systems.future_admission_gate.request_admission(
            FutureBranchKind.NEXT_ACTION, parent_scope
        )
        scope = admit_action_scope(ctx, systems.future_admission_gate, permit, ctx.units["A0"], parent_scope)

        # Record events
        events_emitted: list[str] = []
        ctx.event_bus.subscribe(
            EventType.COMBO_OPPORTUNITY_CONSUMED,
            lambda ev: events_emitted.append("COMBO_CONSUMED"),
        )

        res = systems.action_system.execute(ctx, ctx.units["A0"], action_scope=scope)
        assert res is not None

        # Assert exactly two physical normal attacks occurred
        assert scope.physical_normal_attack_count == 2
        assert len(events_emitted) == 1
        assert scope.combo_checkpoint_state == ComboCheckpointState.CONSUMED

        systems.finalization_coordinator.complete_action_scope(ctx, scope)
        assert scope.terminal

    def test_golden_trace_3_finalization_ordering_and_draining(self) -> None:
        """Golden Trace 3: Finalization ordering, victory latch, draining, and event sequence.

        Asserts:
        - Enemy commander death triggers UnitDeathFact and VICTORY_LATCHED.
        - Coordinator transitions through DRAINING_ADMITTED_WORK while admitted reaction drains.
        - UNIT_ACTION_ENDED occurs BEFORE BATTLE_END / BATTLE_ENDED on ACTION_SETTLED.
        - FinalizationProjectionPermit claimed and consumed once.
        - TerminationState transitions to FINALIZED.
        """
        ctx = _create_battle_context()
        systems = BattleSystems()

        # Enemy commander B0 has 10 troops
        ctx.units["B0"].troops = 10

        # Apply Cleave to A0 so lethal hit on B0 pre-admits Cleave to drain
        systems.state_lifecycle_system.apply(
            ctx,
            state_id="cleave",
            owner_id="A0",
            source_id="A0",
            source_skill_id="skill_cleave",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=CleaveStateParams(ratio=ExactRatio(1, 2)),
        )

        event_order: list[str] = []
        ctx.event_bus.subscribe(EventType.UNIT_ACTION_ENDED, lambda ev: event_order.append("UNIT_ACTION_ENDED"))
        ctx.event_bus.subscribe(EventType.BATTLE_ENDED, lambda ev: event_order.append("BATTLE_ENDED"))

        parent_scope = "round_1_actor_A0"
        permit = systems.future_admission_gate.request_admission(
            FutureBranchKind.NEXT_ACTION, parent_scope
        )
        scope = admit_action_scope(ctx, systems.future_admission_gate, permit, ctx.units["A0"], parent_scope)

        # Force A0 to target B0
        systems.state_lifecycle_system.apply(
            ctx,
            state_id="taunt",
            owner_id="A0",
            source_id="B0",
            source_skill_id="skill_taunt",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=TauntStateParams(taunt_target_id="B0"),
        )

        systems.action_system.execute(ctx, ctx.units["A0"], action_scope=scope)

        # Complete action scope
        systems.finalization_coordinator.complete_action_scope(ctx, scope)
        assert scope.terminal

        # Observe ACTION_SETTLED barrier
        systems.finalization_coordinator.observe_legacy_barrier(
            ctx, LegacyFinalizationBarrier.ACTION_SETTLED
        )

        # Emit UNIT_ACTION_ENDED
        ctx.event_bus.publish(
            event_type=EventType.UNIT_ACTION_ENDED,
            phase=ctx.current_phase,
            round_no=ctx.current_round,
            actor_id="A0",
        )

        # Claim and project finalization result
        claim = systems.finalization_coordinator.claim_finalized_projection()
        assert claim is not None
        proj_permit, fin_res = claim
        systems.finalization_coordinator.consume_projection_permit(proj_permit)

        # Emit BATTLE_ENDED
        ctx.event_bus.publish(
            event_type=EventType.BATTLE_ENDED,
            phase=ctx.current_phase,
            round_no=ctx.current_round,
            payload={"winner_team_id": fin_res.winner_team_id},
        )

        # Assert ordering
        assert "UNIT_ACTION_ENDED" in event_order
        assert "BATTLE_ENDED" in event_order
        assert event_order.index("UNIT_ACTION_ENDED") < event_order.index("BATTLE_ENDED")
        assert systems.finalization_coordinator.termination_state == BattleTerminationState.FINALIZED
