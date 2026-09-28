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

        # Instrument spies on production execution points
        captured_executions: list[Any] = []
        orig_exec_dmg = systems.damage_instance_coordinator.execute_partitioned_damage_instance
        def spy_exec_dmg(*args: Any, **kwargs: Any) -> Any:
            res = orig_exec_dmg(*args, **kwargs)
            captured_executions.append(res)
            return res
        systems.damage_instance_coordinator.execute_partitioned_damage_instance = spy_exec_dmg  # type: ignore[assignment]

        captured_cleave_effects: list[Any] = []
        orig_cleave_exec = systems.cleave_system.execute
        def spy_cleave_exec(c: Any, eff: Any) -> Any:
            captured_cleave_effects.append(eff)
            return orig_cleave_exec(c, eff)
        systems.cleave_system.execute = spy_cleave_exec  # type: ignore[assignment]

        captured_chain_traversals: list[Any] = []
        orig_chain_exec = systems.chain_system.execute
        def spy_chain_exec(c: Any, trav: Any) -> Any:
            captured_chain_traversals.append(trav)
            return orig_chain_exec(c, trav)
        systems.chain_system.execute = spy_chain_exec  # type: ignore[assignment]

        captured_counter_batches: list[Any] = []
        orig_counter_exec = systems.counter_system.execute
        def spy_counter_exec(c: Any, b: Any) -> Any:
            captured_counter_batches.append(b)
            return orig_counter_exec(c, b)
        systems.counter_system.execute = spy_counter_exec  # type: ignore[assignment]

        # Execute action via ActionSystem lifecycle
        action_res = systems.action_system.execute(
            context=ctx,
            actor=ctx.units["A0"],
            action_scope=scope,
        )
        assert action_res is not None
        assert action_res.damage is not None
        assert action_res.normal_attack_id is not None

        # 1. ActionId
        action_id = scope.action_id
        assert isinstance(action_id, ActionId)

        # 2. NormalAttackInstanceId
        na_id = action_res.normal_attack_id
        assert isinstance(na_id, NormalAttackInstanceId)

        # 3. TargetResolutionId
        target_res = action_res.target_resolution
        assert target_res is not None
        assert isinstance(target_res.resolution_id, TargetResolutionId)
        assert target_res.normal_attack_id == na_id
        assert target_res.redirect_reason == RedirectReason.GUARD
        assert target_res.intended_attack_target == "B1"
        assert target_res.post_redirect_actual_target == "B2"
        assert target_res.redirect_source == "B2"

        # 4. DamageInstanceId & PartitionTransactionId & DirectTroopLossId
        assert len(captured_executions) >= 1
        main_dmg_exec = captured_executions[0]
        dmg_id = main_dmg_exec.damage_instance_id
        assert isinstance(dmg_id, DamageInstanceId)

        plan = main_dmg_exec.partition_plan
        assert isinstance(plan, DamageShareTransactionPlan)
        ptn_id = plan.partition_transaction_id
        assert isinstance(ptn_id, PartitionTransactionId)


        assert len(main_dmg_exec.direct_losses) == 1
        direct_loss = main_dmg_exec.direct_losses[0]
        assert isinstance(direct_loss.direct_loss_id, DirectTroopLossId)
        dtl_id = direct_loss.direct_loss_id

        # 5. CleaveEffectId
        assert len(captured_cleave_effects) >= 1
        cleave_effect = captured_cleave_effects[0]
        cleave_id = cleave_effect.effect_id
        assert isinstance(cleave_id, CleaveEffectId)

        # 6. ChainTraversalId
        assert len(captured_chain_traversals) >= 1
        main_chains = [t for t in captured_chain_traversals if t.work.parent_damage_instance_id == dmg_id]
        assert len(main_chains) == 1
        chain_traversal = main_chains[0]
        chain_id = chain_traversal.traversal_id
        assert isinstance(chain_id, ChainTraversalId)


        # 7. ReactionBatchId & CounterBatchEntryId
        assert len(captured_counter_batches) >= 1
        counter_batch = captured_counter_batches[0]
        batch_id = counter_batch.batch_id
        assert isinstance(batch_id, ReactionBatchId)
        assert len(counter_batch.entries) >= 1
        entry_id = counter_batch.entries[0].entry_id
        assert isinstance(entry_id, CounterBatchEntryId)

        # Assert all 10 operational identities are mutually distinct
        all_ids = [
            action_id,
            na_id,
            target_res.resolution_id,
            dmg_id,
            ptn_id,
            dtl_id,
            cleave_id,
            chain_id,
            batch_id,
            entry_id,
        ]
        assert len(all_ids) == len({str(i) for i in all_ids}) == 10

        # Assert Lineage correctness across all production operations
        assert main_dmg_exec.resolution.lineage.root_action_id == action_id
        assert main_dmg_exec.resolution.lineage.parent_normal_attack_id == na_id
        assert main_dmg_exec.resolution.lineage.source_type == SourceType.NORMAL_ATTACK

        assert direct_loss.partition_transaction_id == ptn_id
        assert direct_loss.parent_damage_instance_id == dmg_id
        assert direct_loss.lineage.source_type == SourceType.SHARE_DIRECT_LOSS

        assert cleave_effect.lineage.root_action_id == action_id
        assert cleave_effect.lineage.parent_normal_attack_id == na_id
        assert cleave_effect.lineage.parent_damage_instance_id == dmg_id
        assert cleave_effect.lineage.source_type == SourceType.CLEAVE

        assert chain_traversal.work.parent_damage_instance_id == dmg_id
        assert chain_traversal.work.trigger_provenance.root_action_id == action_id

        assert counter_batch.parent_lineage.root_action_id == action_id
        assert counter_batch.parent_lineage.parent_normal_attack_id == na_id
        assert counter_batch.parent_lineage.parent_damage_instance_id == dmg_id

        # Complete scope
        systems.finalization_coordinator.complete_action_scope(ctx, scope)
        assert scope.terminal

    def test_golden_trace_2_combo_second_attack_identities_and_caps(self) -> None:
        """Golden Trace 2: Combo second attack generates completely distinct identities.

        Asserts:
        - NA #1 != NA #2
        - TargetResolution #1 != TargetResolution #2
        - DamageInstance #1 != DamageInstance #2
        - Both attacks share the exact same root ActionId
        - Checkpoint reached count == 1, cfg230 count == 1, total physical NA count == 2
        - No recursive reopening
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
        assert res.combo_second_attack is not None

        na1 = res
        na2 = res.combo_second_attack

        # Assert distinct identities
        assert isinstance(na1.normal_attack_id, NormalAttackInstanceId)
        assert isinstance(na2.normal_attack_id, NormalAttackInstanceId)
        assert na1.normal_attack_id != na2.normal_attack_id

        assert na1.target_resolution is not None and na2.target_resolution is not None
        assert isinstance(na1.target_resolution.resolution_id, TargetResolutionId)
        assert isinstance(na2.target_resolution.resolution_id, TargetResolutionId)
        assert na1.target_resolution.resolution_id != na2.target_resolution.resolution_id

        assert na1.resolution is not None and na2.resolution is not None
        assert isinstance(na1.resolution.damage_instance_id, DamageInstanceId)
        assert isinstance(na2.resolution.damage_instance_id, DamageInstanceId)
        assert na1.resolution.damage_instance_id != na2.resolution.damage_instance_id

        # Assert both attacks share identical root ActionId
        assert na1.resolution.lineage is not None and na2.resolution.lineage is not None
        assert na1.resolution.lineage.root_action_id == scope.action_id
        assert na2.resolution.lineage.root_action_id == scope.action_id

        # Assert exactly two physical normal attacks occurred
        assert scope.physical_normal_attack_count == 2
        # Assert Combo checkpoint count = 1, state is CONSUMED
        assert scope.combo_checkpoint_state == ComboCheckpointState.CONSUMED
        # Assert cfg230 count = 1
        assert len(events_emitted) == 1

        # Assert no recursive reopening
        assert na2.combo_second_attack is None

        systems.finalization_coordinator.complete_action_scope(ctx, scope)
        assert scope.terminal

    def test_golden_trace_3_finalization_ordering_and_draining(self) -> None:
        """Golden Trace 3: Finalization ordering, victory latch, draining, and event sequence.

        Asserts:
        - Enemy commander death triggers UnitDeathFact and VICTORY_LATCHED.
        - Coordinator transitions through DRAINING_ADMITTED_WORK while admitted reaction drains.
        - UNIT_ACTION_ENDED occurs BEFORE BATTLE_END / BATTLE_ENDED on ACTION_SETTLED.
        - FinalizationProjectionPermit claimed and consumed once by BattleEngine.
        - UnitDeathFact != VictoryLatched != BattleFinalized distinction proven.
        """
        from sgs_v2.battle_core.engine import BattleEngine

        ctx = _create_battle_context()
        systems = BattleSystems()

        # Enemy commander B0 has 10 troops
        ctx.units["B0"].troops = 10
        # Give A0 dominant speed so A0 acts first
        ctx.units["A0"].speed = 999
        for uid, u in ctx.units.items():
            if uid != "A0":
                u.speed = 10

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

        event_order: list[str] = []
        ctx.event_bus.subscribe(
            EventType.UNIT_ACTION_ENDED, lambda ev: event_order.append("UNIT_ACTION_ENDED")
        )
        ctx.event_bus.subscribe(
            EventType.PHASE_ENTERED, lambda ev: event_order.append(f"PHASE_{ev.phase}")
        )
        ctx.event_bus.subscribe(
            EventType.BATTLE_ENDED, lambda ev: event_order.append("BATTLE_ENDED")
        )

        # Assert initial state: RUNNING
        coord = systems.finalization_coordinator
        assert coord.termination_state == BattleTerminationState.RUNNING

        # Run authentic BattleEngine
        engine = BattleEngine(context=ctx, systems=systems)
        res = engine.run()
        assert res is not None

        # Assert event counts
        assert event_order.count("UNIT_ACTION_ENDED") == 1
        assert event_order.count("PHASE_BATTLE_END") == 1
        assert event_order.count("BATTLE_ENDED") == 1

        # Assert event ordering: UNIT_ACTION_ENDED occurs BEFORE PHASE_BATTLE_END and BATTLE_ENDED
        idx_action_ended = event_order.index("UNIT_ACTION_ENDED")
        idx_phase_end = event_order.index("PHASE_BATTLE_END")
        idx_battle_ended = event_order.index("BATTLE_ENDED")
        assert idx_action_ended < idx_phase_end < idx_battle_ended

        # Assert projection permit was claimed and consumed exactly once
        assert coord._projection_consumed is True
        assert coord.claim_finalized_projection() is None

        # Assert BattleFinalized state
        assert coord.termination_state == BattleTerminationState.FINALIZED
        assert ctx.ended is True
        assert ctx.result is not None
        assert ctx.result.winner_team_id == "A"

    def test_golden_trace_3_distinction_death_fact_victory_latched_finalized(self) -> None:
        """Distinct stages: UnitDeathFact != VictoryLatched != BattleFinalized."""
        ctx = _create_battle_context()
        systems = BattleSystems()
        coord = systems.finalization_coordinator

        # Stage 0: Initial
        assert coord.termination_state == BattleTerminationState.RUNNING

        # Stage 1: Admit damage instance, then UnitDeathFact on commander B0
        dmg_id = DamageInstanceId("dmg_gt3")
        coord.admit_damage_instance(ctx, dmg_id)
        ctx.units["B0"].troops = 0
        coord.observe_damage_instance_death(ctx, dmg_id)


        # Stage 2: Victory is Latched / Draining admitted work, NOT yet Finalized!
        assert coord.is_latched_or_finalized is True
        assert coord.termination_state != BattleTerminationState.FINALIZED
        assert coord.termination_state == BattleTerminationState.DRAINING_ADMITTED_WORK
        # Projection cannot be claimed yet while latched/draining
        assert coord.claim_finalized_projection() is None

        # Stage 3: Admitted damage instance completes -> BattleFinalized
        coord.complete_damage_instance(ctx, dmg_id)
        assert coord.termination_state == BattleTerminationState.FINALIZED


        # Stage 4: Projection permit claimed and consumed
        claim = coord.claim_finalized_projection()
        assert claim is not None
        permit, fin_res = claim
        coord.consume_projection_permit(permit)
        assert coord._projection_consumed is True

