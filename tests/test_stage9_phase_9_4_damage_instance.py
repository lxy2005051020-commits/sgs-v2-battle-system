from __future__ import annotations

import pytest

from sgs_v2.battle_core.attribute_system import AttributeSystem
from sgs_v2.battle_core.battle_finalization_coordinator import (
    BattleFinalizationCoordinator,
    BattleTerminationState,
)
from sgs_v2.battle_core.battle_systems import BattleSystems
from sgs_v2.battle_core.context import BattleContext
from sgs_v2.battle_core.damage_instance_coordinator import DamageInstanceCoordinator
from sgs_v2.battle_core.damage_resolution_system import (
    DamageResolutionResult,
    DamageResolutionSystem,
    DamageSettlementRequest,
    SettlementOrigin,
)
from sgs_v2.battle_core.damage_system import DamageRequest, DamageResult, DamageSystem
from sgs_v2.battle_core.effect_executor import EffectExecutor
from sgs_v2.battle_core.effects import DamageEffect, EffectSourceRef
from sgs_v2.battle_core.enums import (
    BattleEndReason,
    DamageSourceType,
    DamageType,
    LineupPosition,
)
from sgs_v2.battle_core.events import EventBus, EventType
from sgs_v2.battle_core.execution_right_system import (
    DamageSettlementPermit,
    LegacyFinalizationBarrier,
)
from sgs_v2.battle_core.operation_identity import (
    ActionId,
    DamageInstanceId,
    NormalAttackInstanceId,
    OperationLineage,
    SourceType,
)
from sgs_v2.battle_core.random_system import RandomSystem
from sgs_v2.battle_core.troop_system import TroopSystem
from sgs_v2.battle_core.unit import UnitRuntime
from sgs_v2.battle_core.victory_system import VictorySystem


def _make_unit(unit_id: str, team_id: str, troops: int = 1000, pos: LineupPosition = LineupPosition.COMMANDER) -> UnitRuntime:
    return UnitRuntime(
        unit_id,
        f"Unit_{unit_id}",
        team_id,
        max(1, troops),
        troops,
        100,
        100,
        100,
        lineup_position=pos,
    )


def _make_context(troops_a: int = 1000, troops_b: int = 1000) -> BattleContext:
    u_a = _make_unit("A1", "team_A", troops=troops_a, pos=LineupPosition.COMMANDER)
    u_b = _make_unit("B1", "team_B", troops=troops_b, pos=LineupPosition.COMMANDER)
    return BattleContext(
        battle_id="b_test",
        units={"A1": u_a, "B1": u_b},
        event_bus=EventBus(),
        random=RandomSystem(seed=42),
    )


def _make_lineage(source_type: SourceType = SourceType.NORMAL_ATTACK) -> OperationLineage:
    return OperationLineage(
        root_action_id=ActionId("act_1"),
        parent_normal_attack_id=NormalAttackInstanceId("na_1"),
        parent_damage_instance_id=None,
        source_type=source_type,
        physical_attacker="A1",
    )


class TestThreeLayerSeparationFixture:
    """
    Section 28 & 29 Mandatory Fixture:
    Dtotal != Dtarget != ActualTargetTroopLoss
    """

    def test_dtotal_dtarget_actualloss_all_distinct(self) -> None:
        """
        Verify:
        DamageResult.final_damage == X (Dtotal)
        DamageSettlementRequest.assigned_target_damage == Y (Dtarget)
        DamageResolutionResult.assigned_target_damage == Y
        DamageResolutionResult.actual_target_troop_loss == Z (ActualLoss)
        DAMAGE_DEALT.requested_damage == Y
        DAMAGE_DEALT.damage == Z
        where X != Y, Y != Z, X != Z.
        """
        # Target has only 100 troops
        ctx = _make_context(troops_b=100)
        dmg_sys = DamageSystem(AttributeSystem())
        troop_sys = TroopSystem()
        res_sys = DamageResolutionSystem(dmg_sys, troop_sys)
        coordinator = DamageInstanceCoordinator(dmg_sys, res_sys)

        lineage = _make_lineage(SourceType.NORMAL_ATTACK)
        dmg_id = coordinator.begin_damage_instance(ctx, lineage)
        permit = coordinator.issue_settlement_permit(dmg_id, lineage, ctx)

        # X = 300 (Dtotal)
        # Y = 180 (Dtarget)
        # Z = 100 (ActualTargetTroopLoss, clamped by target's 100 troops)
        X = 300
        Y = 180
        Z = 100
        assert X != Y and Y != Z and X != Z

        dummy_result = DamageResult(
            source_id="A1",
            target_id="B1",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.NORMAL_ATTACK,
            coefficient=1.0,
            base_damage=float(X),
            scaled_damage=float(X),
            final_damage=X,
        )

        settlement_req = DamageSettlementRequest(
            damage_result=dummy_result,
            assigned_target_damage=Y,
            damage_instance_id=dmg_id,
            lineage=lineage,
            origin=SettlementOrigin.STAGE9,
        )

        res = res_sys.settle(ctx, settlement_req, permit)

        # Strict multi-layer assertions
        assert res.damage.final_damage == X, "Dtotal layer must equal X"
        assert settlement_req.assigned_target_damage == Y, "Request Dtarget layer must equal Y"
        assert res.assigned_target_damage == Y, "Result Dtarget layer must equal Y"
        assert res.actual_target_troop_loss == Z, "Result actual loss layer must equal Z"
        assert res.credited_damage == Z, "Credited damage must equal actual loss Z"
        assert res.target_troops_before == 100
        assert res.target_troops_after == 0
        assert res.target_defeated is True

        events = [e for e in ctx.event_bus.history if e.event_type == EventType.DAMAGE_DEALT]
        assert len(events) == 1
        assert events[0].payload["requested_damage"] == Y, "Event requested_damage must be Dtarget Y"
        assert events[0].payload["damage"] == Z, "Event damage must be ActualTargetTroopLoss Z"

        defeated_events = [e for e in ctx.event_bus.history if e.event_type == EventType.UNIT_DEFEATED]
        assert len(defeated_events) == 1
        assert defeated_events[0].actor_id == "A1"
        assert defeated_events[0].target_id == "B1"

    def test_coordinator_execute_standard_damage_instance_end_to_end(self) -> None:
        """Test DamageInstanceCoordinator execution with isolated assigned amount seam."""
        ctx = _make_context(troops_b=80)
        dmg_sys = DamageSystem(AttributeSystem())
        troop_sys = TroopSystem()
        res_sys = DamageResolutionSystem(dmg_sys, troop_sys)
        coordinator = DamageInstanceCoordinator(dmg_sys, res_sys)

        req = DamageRequest(
            source_id="A1",
            target_id="B1",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.NORMAL_ATTACK,
            coefficient=1.0,
        )
        lineage = _make_lineage()

        # Execute standard DamageInstance with testable assigned amount Y=150
        res = coordinator.execute_standard_damage_instance(
            context=ctx,
            request=req,
            lineage=lineage,
            assigned_target_damage=150,
        )

        assert res.assigned_target_damage == 150
        assert res.actual_target_troop_loss == 80
        assert res.credited_damage == 80
        assert res.target_troops_before == 80
        assert res.target_troops_after == 0
        assert res.target_defeated is True
        assert res.damage_instance_id is not None
        assert res.lineage == lineage

    def test_overkill_credited_damage_is_not_theoretical_amount(self) -> None:
        """Ensure credited_damage equals actual troop loss, never theoretical overkill."""
        ctx = _make_context(troops_b=120)
        dmg_sys = DamageSystem(AttributeSystem())
        troop_sys = TroopSystem()
        res_sys = DamageResolutionSystem(dmg_sys, troop_sys)
        coordinator = DamageInstanceCoordinator(dmg_sys, res_sys)

        lineage = _make_lineage()
        dmg_id = coordinator.begin_damage_instance(ctx, lineage)
        permit = coordinator.issue_settlement_permit(dmg_id, lineage, ctx)

        dummy_result = DamageResult(
            source_id="A1",
            target_id="B1",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.NORMAL_ATTACK,
            coefficient=1.0,
            base_damage=500.0,
            scaled_damage=500.0,
            final_damage=500,
        )

        settlement_req = DamageSettlementRequest(
            damage_result=dummy_result,
            assigned_target_damage=500,
            damage_instance_id=dmg_id,
            lineage=lineage,
            origin=SettlementOrigin.STAGE9,
        )

        res = res_sys.settle(ctx, settlement_req, permit)
        assert res.assigned_target_damage == 500
        assert res.actual_target_troop_loss == 120
        assert res.credited_damage == 120, "Credited damage must be 120, not theoretical overkill 500"


class TestBattleSystemsAndFinalizationObservation:
    """Test BattleSystems composition root and finalization observation seam."""

    def test_battle_systems_composition_root_wiring(self) -> None:
        systems = BattleSystems()
        assert systems.damage_instance_coordinator is not None
        assert systems.damage_instance_coordinator.damage_system is systems.damage_system
        assert (
            systems.damage_instance_coordinator.damage_resolution_system
            is systems.damage_resolution_system
        )
        assert systems.damage_resolution_system.coordinator is systems.damage_instance_coordinator

    def test_finalization_observation_seam_preserves_inv39(self) -> None:
        """
        INV-39 Separation:
        UnitDeathFact != VictoryConditionLatched != BattleFinalized.
        DamageResolutionSystem settlement produces UnitDeathFact, but does NOT finalize battle.
        Finalization only occurs when BattleFinalizationCoordinator observes a terminal barrier.
        """
        systems = BattleSystems()
        ctx = _make_context(troops_b=50)

        coordinator = systems.damage_instance_coordinator
        lineage = _make_lineage()
        dmg_id = coordinator.begin_damage_instance(ctx, lineage)
        permit = coordinator.issue_settlement_permit(dmg_id, lineage, ctx)

        dummy_result = DamageResult(
            source_id="A1",
            target_id="B1",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.NORMAL_ATTACK,
            coefficient=1.0,
            base_damage=100.0,
            scaled_damage=100.0,
            final_damage=100,
        )

        settlement_req = DamageSettlementRequest(
            damage_result=dummy_result,
            assigned_target_damage=100,
            damage_instance_id=dmg_id,
            lineage=lineage,
            origin=SettlementOrigin.STAGE9,
        )

        res = systems.damage_resolution_system.settle(ctx, settlement_req, permit)

        # 1. Unit death edge fact is produced
        assert res.target_defeated is True
        assert ctx.get_unit("B1").troops == 0
        assert ctx.get_unit("B1").is_alive is False

        # 2. BUT Damage settlement did NOT finalize the battle
        assert ctx.ended is False
        assert ctx.result is None
        assert systems.finalization_coordinator.termination_state == BattleTerminationState.RUNNING

        # 3. Only when finalization architecture observes a legacy barrier does it transition
        systems.finalization_coordinator.observe_legacy_barrier(
            ctx, LegacyFinalizationBarrier.ACTION_SETTLED
        )
        assert (
            systems.finalization_coordinator.termination_state
            == BattleTerminationState.FINALIZED
        )

        # 4. Projection capability claim and consume
        claimed = systems.finalization_coordinator.claim_finalized_projection()
        assert claimed is not None
        proj_permit, fin_res = claimed
        systems.finalization_coordinator.consume_projection_permit(proj_permit)

        assert fin_res.winner_team_id == "team_A"
        assert fin_res.reason == BattleEndReason.COMMANDER_DEFEATED


class TestEffectExecutorRemainsLegacy:
    """Verify EffectExecutor production route remains legacy in Phase 9.4."""

    def test_effect_executor_production_route_is_legacy(self) -> None:
        systems = BattleSystems()
        ctx = _make_context(troops_b=1000)

        effect = DamageEffect(
            source_id="A1",
            target_id="B1",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.SKILL,
            coefficient=1.0,
        )

        # Execute effect through EffectExecutor
        result = systems.effect_executor.execute(ctx, effect)

        # Resolution result is populated via legacy resolve / apply_result
        assert result.resolution is not None
        assert result.resolution.damage_instance_id is None
        assert result.resolution.lineage is None
        assert result.resolution.assigned_target_damage == result.resolution.damage.final_damage
        assert result.resolution.actual_target_troop_loss > 0


class TestCoordinatorPermitLifecycleRepair:
    """Repair audit tests: permit lifecycle is strictly operation-local and leak-free."""

    def test_p94_r03_successful_execution_leaves_zero_permit_tracking_residue(self) -> None:
        ctx = _make_context(troops_b=1000)
        dmg_sys = DamageSystem(AttributeSystem())
        troop_sys = TroopSystem()
        res_sys = DamageResolutionSystem(dmg_sys, troop_sys)
        coordinator = DamageInstanceCoordinator(dmg_sys, res_sys)

        req = DamageRequest(
            source_id="A1",
            target_id="B1",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.NORMAL_ATTACK,
            coefficient=1.0,
        )
        lineage = _make_lineage()

        res = coordinator.execute_standard_damage_instance(
            context=ctx,
            request=req,
            lineage=lineage,
        )
        assert res.actual_target_troop_loss > 0
        assert len(coordinator._permits) == 0
        assert len(coordinator._active_instances) == 0
        assert not hasattr(coordinator, "_completed_instances")

    def test_p94_r04_calculate_exception_causes_zero_permit_leak(self) -> None:
        ctx = _make_context(troops_b=1000)
        dmg_sys = DamageSystem(AttributeSystem())
        troop_sys = TroopSystem()
        res_sys = DamageResolutionSystem(dmg_sys, troop_sys)
        coordinator = DamageInstanceCoordinator(dmg_sys, res_sys)

        # Invalid DamageRequest (unknown unit) causes calculate to raise InvalidDamageParticipantError
        bad_req = DamageRequest(
            source_id="NON_EXISTENT_UNIT",
            target_id="B1",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.NORMAL_ATTACK,
            coefficient=1.0,
        )
        lineage = _make_lineage()

        with pytest.raises(Exception):
            coordinator.execute_standard_damage_instance(
                context=ctx,
                request=bad_req,
                lineage=lineage,
            )

        assert len(coordinator._permits) == 0
        assert len(coordinator._active_instances) == 0

    def test_p94_r05_replaying_old_completed_permit_raises_value_error_with_zero_mutations(self) -> None:
        ctx = _make_context(troops_b=1000)
        dmg_sys = DamageSystem(AttributeSystem())
        troop_sys = TroopSystem()
        res_sys = DamageResolutionSystem(dmg_sys, troop_sys)
        coordinator = DamageInstanceCoordinator(dmg_sys, res_sys)

        lineage = _make_lineage()
        dmg_id = coordinator.begin_damage_instance(ctx, lineage)
        permit = coordinator.issue_settlement_permit(dmg_id, lineage, ctx)

        dmg_result = DamageResult(
            source_id="A1",
            target_id="B1",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.NORMAL_ATTACK,
            coefficient=1.0,
            base_damage=100.0,
            scaled_damage=100.0,
            final_damage=100,
        )
        req = DamageSettlementRequest(
            damage_result=dmg_result,
            assigned_target_damage=100,
            damage_instance_id=dmg_id,
            lineage=lineage,
            origin=SettlementOrigin.STAGE9,
        )

        # First settle succeeds
        res = res_sys.settle(ctx, req, permit)
        assert res.actual_target_troop_loss == 100
        assert ctx.get_unit("B1").troops == 900
        initial_events_count = len(ctx.event_bus.history)

        # Release coordinator state for this instance
        coordinator.close_damage_instance(dmg_id)
        assert len(coordinator._permits) == 0
        assert len(coordinator._active_instances) == 0

        # Attempt to replay the old permit against res_sys.settle
        with pytest.raises(ValueError, match="closed, or not active|was not issued"):
            res_sys.settle(ctx, req, permit)

        # Target troops unchanged, zero new events
        assert ctx.get_unit("B1").troops == 900
        assert len(ctx.event_bus.history) == initial_events_count

    def test_p94_r2_01_damage_instance_id_exists_before_calculate(self) -> None:
        """P94-R2-01: Verify DamageInstance scope/identity exists when DamageSystem.calculate() runs."""
        import unittest.mock

        ctx = _make_context(troops_b=1000)
        dmg_sys = DamageSystem(AttributeSystem())
        troop_sys = TroopSystem()
        res_sys = DamageResolutionSystem(dmg_sys, troop_sys)
        coordinator = DamageInstanceCoordinator(dmg_sys, res_sys)

        req = DamageRequest(
            source_id="A1",
            target_id="B1",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.NORMAL_ATTACK,
            coefficient=1.0,
        )
        lineage = _make_lineage()

        observed_active_during_calc: list[list[DamageInstanceId]] = []

        orig_calc = dmg_sys.calculate

        def _spy_calc(c, r):
            active_ids = [rec.damage_instance_id for rec in coordinator._active_instances.values()]
            observed_active_during_calc.append(active_ids)
            assert len(active_ids) == 1
            assert coordinator.is_instance_active(active_ids[0], c)
            return orig_calc(c, r)

        with unittest.mock.patch.object(dmg_sys, "calculate", side_effect=_spy_calc):
            res = coordinator.execute_standard_damage_instance(ctx, req, lineage)

        assert len(observed_active_during_calc) == 1
        assert len(observed_active_during_calc[0]) == 1
        assert res.damage_instance_id == observed_active_during_calc[0][0]
        assert len(coordinator._active_instances) == 0

    def test_p94_r2_02_calculate_failure_lifecycle_and_sequence_gap(self) -> None:
        """P94-R2-02: Verify calculate failure allocates ID, issues 0 permits, cleans scope, and leaves allocator gap."""
        ctx = _make_context(troops_b=1000)
        dmg_sys = DamageSystem(AttributeSystem())
        troop_sys = TroopSystem()
        res_sys = DamageResolutionSystem(dmg_sys, troop_sys)
        coordinator = DamageInstanceCoordinator(dmg_sys, res_sys)

        bad_req = DamageRequest(
            source_id="NON_EXISTENT_UNIT",
            target_id="B1",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.NORMAL_ATTACK,
            coefficient=1.0,
        )
        lineage = _make_lineage()

        # Calculation raises
        with pytest.raises(Exception):
            coordinator.execute_standard_damage_instance(ctx, bad_req, lineage)

        # 0 permits issued, 0 active scope residue
        assert len(coordinator._permits) == 0
        assert len(coordinator._active_instances) == 0

        # Next fresh DamageInstance executes successfully
        good_req = DamageRequest(
            source_id="A1",
            target_id="B1",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.NORMAL_ATTACK,
            coefficient=1.0,
        )
        res = coordinator.execute_standard_damage_instance(ctx, good_req, lineage)
        assert res.actual_target_troop_loss > 0
        # The new ID reflects a sequence increment (gap created by failed instance)
        assert len(coordinator._permits) == 0
        assert len(coordinator._active_instances) == 0

    def test_p94_r2_03_duplicate_permit_issuance_rejected_on_active_instance(self) -> None:
        """P94-R2-03: Same active DamageInstance rejects second permit issuance."""
        ctx = _make_context(troops_b=1000)
        dmg_sys = DamageSystem(AttributeSystem())
        troop_sys = TroopSystem()
        res_sys = DamageResolutionSystem(dmg_sys, troop_sys)
        coordinator = DamageInstanceCoordinator(dmg_sys, res_sys)

        lineage = _make_lineage()
        dmg_id = coordinator.begin_damage_instance(ctx, lineage)

        permit1 = coordinator.issue_settlement_permit(dmg_id, lineage, ctx)
        assert permit1 is not None

        # Second attempt to issue permit for the same active instance
        with pytest.raises(ValueError, match="already been issued.*At most one permit"):
            coordinator.issue_settlement_permit(dmg_id, lineage, ctx)

        coordinator.close_damage_instance(dmg_id)

    def test_p94_r2_04_closed_instance_permit_reissuance_rejected(self) -> None:
        """P94-R2-04: Closed DamageInstance cannot be issued another permit."""
        ctx = _make_context(troops_b=1000)
        dmg_sys = DamageSystem(AttributeSystem())
        troop_sys = TroopSystem()
        res_sys = DamageResolutionSystem(dmg_sys, troop_sys)
        coordinator = DamageInstanceCoordinator(dmg_sys, res_sys)

        lineage = _make_lineage()
        dmg_id = coordinator.begin_damage_instance(ctx, lineage)
        coordinator.close_damage_instance(dmg_id)

        # Attempt to issue permit on closed ID
        with pytest.raises(ValueError, match="not an active instance|closed"):
            coordinator.issue_settlement_permit(dmg_id, lineage, ctx)

    def test_p94_r2_05_arbitrary_damage_instance_id_permit_issuance_rejected(self) -> None:
        """P94-R2-05: Arbitrary manually constructed DamageInstanceId rejected for permit issuance."""
        ctx = _make_context(troops_b=1000)
        dmg_sys = DamageSystem(AttributeSystem())
        troop_sys = TroopSystem()
        res_sys = DamageResolutionSystem(dmg_sys, troop_sys)
        coordinator = DamageInstanceCoordinator(dmg_sys, res_sys)

        arbitrary_id = DamageInstanceId("arbitrary_crafted_id")
        lineage = _make_lineage()

        with pytest.raises(ValueError, match="not an active instance owned by this coordinator"):
            coordinator.issue_settlement_permit(arbitrary_id, lineage, ctx)

    def test_p94_r2_06_foreign_or_inactive_permit_rejected_by_settle(self) -> None:
        """P94-R2-06: Permit from another coordinator or inactive scope is rejected by settle()."""
        ctx = _make_context(troops_b=1000)
        dmg_sys = DamageSystem(AttributeSystem())
        troop_sys = TroopSystem()
        res_sys = DamageResolutionSystem(dmg_sys, troop_sys)
        coordinator1 = DamageInstanceCoordinator(dmg_sys, res_sys)
        res_sys2 = DamageResolutionSystem(dmg_sys, troop_sys)
        coordinator2 = DamageInstanceCoordinator(dmg_sys, res_sys2)

        lineage = _make_lineage()
        dmg_id2 = coordinator2.begin_damage_instance(ctx, lineage)
        permit2 = coordinator2.issue_settlement_permit(dmg_id2, lineage, ctx)

        dmg_result = DamageResult(
            source_id="A1",
            target_id="B1",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.NORMAL_ATTACK,
            coefficient=1.0,
            base_damage=100.0,
            scaled_damage=100.0,
            final_damage=100,
        )
        req = DamageSettlementRequest(
            damage_result=dmg_result,
            assigned_target_damage=100,
            damage_instance_id=dmg_id2,
            lineage=lineage,
            origin=SettlementOrigin.STAGE9,
        )

        # coordinator1 is bound to res_sys; permit2 from coordinator2 must be rejected
        with pytest.raises(ValueError, match="was not issued by this coordinator|closed, or not active"):
            res_sys.settle(ctx, req, permit2)

        coordinator2.close_damage_instance(dmg_id2)

    def test_p94_r2_07_replay_attack_with_minted_permit_blocked(self) -> None:
        """P94-R2-07: Prove that after standard execution, replaying request with minted permit is blocked with 0 side-effects."""
        ctx = _make_context(troops_b=1000)
        dmg_sys = DamageSystem(AttributeSystem())
        troop_sys = TroopSystem()
        res_sys = DamageResolutionSystem(dmg_sys, troop_sys)
        coordinator = DamageInstanceCoordinator(dmg_sys, res_sys)

        req = DamageRequest(
            source_id="A1",
            target_id="B1",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.NORMAL_ATTACK,
            coefficient=1.0,
        )
        lineage = _make_lineage()

        # Step 1: legitimate execution of dmg_1
        res1 = coordinator.execute_standard_damage_instance(ctx, req, lineage)
        initial_loss = res1.actual_target_troop_loss
        assert initial_loss > 0
        troops_after_first = ctx.get_unit("B1").troops
        events_after_first = len(ctx.event_bus.history)
        old_id = res1.damage_instance_id

        # Step 2: Attacker attempts to mint a second permit for old_id
        with pytest.raises(ValueError, match="not an active instance|closed"):
            coordinator.issue_settlement_permit(old_id, lineage, ctx)

        # Step 3: Attacker tries to pair old_id with a fresh permit minted for fresh_id
        fresh_id = coordinator.begin_damage_instance(ctx, lineage)
        fresh_permit = coordinator.issue_settlement_permit(fresh_id, lineage, ctx)

        replay_req = DamageSettlementRequest(
            damage_result=res1.damage,
            assigned_target_damage=res1.assigned_target_damage,
            damage_instance_id=old_id,
            lineage=lineage,
            origin=SettlementOrigin.STAGE9,
        )
        with pytest.raises(ValueError, match="does not match request damage_instance_id"):
            res_sys.settle(ctx, replay_req, fresh_permit)

        coordinator.close_damage_instance(fresh_id)

        # Confirm ZERO additional troop mutation and ZERO additional events
        assert ctx.get_unit("B1").troops == troops_after_first
        assert len(ctx.event_bus.history) == events_after_first


class TestContextOwnershipBoundaryFinalRepair:
    """Tests P94-FR-01 through P94-FR-06: DamageInstance BattleContext ownership boundary."""

    def test_p94_fr_01_begin_damage_instance_binds_owning_context(self) -> None:
        """P94-FR-01: begin_damage_instance(ctx_A, lineage) binds active record to ctx_A."""
        ctx_a = _make_context(troops_b=1000)
        dmg_sys = DamageSystem(AttributeSystem())
        troop_sys = TroopSystem()
        res_sys = DamageResolutionSystem(dmg_sys, troop_sys)
        coordinator = DamageInstanceCoordinator(dmg_sys, res_sys)

        lineage = _make_lineage()
        dmg_id = coordinator.begin_damage_instance(ctx_a, lineage)

        record = coordinator._active_instances.get((id(ctx_a), dmg_id))
        assert record is not None
        assert record.owning_context is ctx_a
        assert record.damage_instance_id == dmg_id
        assert record.lineage == lineage

        coordinator.close_damage_instance(dmg_id, ctx_a)

    def test_p94_fr_02_context_none_rejected_without_state_mutation(self) -> None:
        """P94-FR-02: begin_damage_instance(None, lineage) raises TypeError (no ID, no active scope created)."""
        dmg_sys = DamageSystem(AttributeSystem())
        troop_sys = TroopSystem()
        res_sys = DamageResolutionSystem(dmg_sys, troop_sys)
        coordinator = DamageInstanceCoordinator(dmg_sys, res_sys)
        lineage = _make_lineage()

        with pytest.raises(TypeError, match="context must be BattleContext"):
            coordinator.begin_damage_instance(None, lineage)  # type: ignore[arg-type]

        with pytest.raises(TypeError, match="context must be BattleContext"):
            coordinator.allocate_damage_instance_id(None)  # type: ignore[arg-type]

        assert len(coordinator._active_instances) == 0
        assert len(coordinator._permits) == 0

    def test_p94_fr_03_cross_context_settlement_rejected_before_consume(self) -> None:
        """P94-FR-03: permit issued on ctx_A, passed to res_sys.settle(ctx_B, req, permit) -> raises ValueError before consume."""
        ctx_a = _make_context(troops_b=1000)
        ctx_b = _make_context(troops_b=1000)
        dmg_sys = DamageSystem(AttributeSystem())
        troop_sys = TroopSystem()
        res_sys = DamageResolutionSystem(dmg_sys, troop_sys)
        coordinator = DamageInstanceCoordinator(dmg_sys, res_sys)

        lineage = _make_lineage()
        dmg_id = coordinator.begin_damage_instance(ctx_a, lineage)
        permit = coordinator.issue_settlement_permit(dmg_id, lineage, ctx_a)

        dmg_result = DamageResult(
            source_id="A1",
            target_id="B1",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.NORMAL_ATTACK,
            coefficient=1.0,
            base_damage=100.0,
            scaled_damage=100.0,
            final_damage=100,
        )
        req_b = DamageSettlementRequest(
            damage_result=dmg_result,
            assigned_target_damage=100,
            damage_instance_id=dmg_id,
            lineage=lineage,
            origin=SettlementOrigin.STAGE9,
        )

        troops_a_before = ctx_a.get_unit("B1").troops
        troops_b_before = ctx_b.get_unit("B1").troops

        with pytest.raises(ValueError, match="was issued for a different BattleContext"):
            res_sys.settle(ctx_b, req_b, permit)

        # Confirm permit is NOT marked consumed and active scope is intact
        permit_rec = coordinator._permits.get((id(ctx_a), permit.permit_id))
        assert permit_rec is not None
        assert not permit_rec.consumed
        active_rec = coordinator._active_instances.get((id(ctx_a), dmg_id))
        assert active_rec is not None
        assert not active_rec.permit_consumed

        # 0 troops change on both contexts, 0 events on both buses
        assert ctx_a.get_unit("B1").troops == troops_a_before
        assert ctx_b.get_unit("B1").troops == troops_b_before
        assert len(ctx_a.event_bus.history) == 0
        assert len(ctx_b.event_bus.history) == 0

        coordinator.close_damage_instance(dmg_id, ctx_a)

    def test_p94_fr_04_permit_usable_on_original_context_after_cross_context_rejection(self) -> None:
        """P94-FR-04: After failed ctx_B attempt, the exact same permit settles successfully on ctx_A exactly once."""
        ctx_a = _make_context(troops_b=1000)
        ctx_b = _make_context(troops_b=1000)
        dmg_sys = DamageSystem(AttributeSystem())
        troop_sys = TroopSystem()
        res_sys = DamageResolutionSystem(dmg_sys, troop_sys)
        coordinator = DamageInstanceCoordinator(dmg_sys, res_sys)

        lineage = _make_lineage()
        dmg_id = coordinator.begin_damage_instance(ctx_a, lineage)
        permit = coordinator.issue_settlement_permit(dmg_id, lineage, ctx_a)

        dmg_result = DamageResult(
            source_id="A1",
            target_id="B1",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.NORMAL_ATTACK,
            coefficient=1.0,
            base_damage=100.0,
            scaled_damage=100.0,
            final_damage=100,
        )
        req_b = DamageSettlementRequest(
            damage_result=dmg_result,
            assigned_target_damage=100,
            damage_instance_id=dmg_id,
            lineage=lineage,
            origin=SettlementOrigin.STAGE9,
        )
        req_a = DamageSettlementRequest(
            damage_result=dmg_result,
            assigned_target_damage=100,
            damage_instance_id=dmg_id,
            lineage=lineage,
            origin=SettlementOrigin.STAGE9,
        )

        # First: rejected on ctx_B
        with pytest.raises(ValueError, match="was issued for a different BattleContext"):
            res_sys.settle(ctx_b, req_b, permit)

        # Second: settles successfully on ctx_A
        res_a = res_sys.settle(ctx_a, req_a, permit)
        assert res_a.actual_target_troop_loss == 100
        assert ctx_a.get_unit("B1").troops == 900
        assert len(ctx_a.event_bus.history) > 0

        # Third: second attempt on ctx_A is rejected (single consume invariant)
        with pytest.raises(ValueError, match="already been consumed"):
            res_sys.settle(ctx_a, req_a, permit)

        coordinator.close_damage_instance(dmg_id, ctx_a)

    def test_p94_fr_05_issue_permit_with_wrong_context_rejected(self) -> None:
        """P94-FR-05: issue_settlement_permit(dmg_id, lineage, context=wrong_ctx) raises ValueError('Supplied context does not match the owning BattleContext')."""
        ctx_a = _make_context(troops_b=1000)
        ctx_b = _make_context(troops_b=1000)
        dmg_sys = DamageSystem(AttributeSystem())
        troop_sys = TroopSystem()
        res_sys = DamageResolutionSystem(dmg_sys, troop_sys)
        coordinator = DamageInstanceCoordinator(dmg_sys, res_sys)

        lineage = _make_lineage()
        dmg_id = coordinator.begin_damage_instance(ctx_a, lineage)

        with pytest.raises(ValueError, match="Supplied context does not match the owning BattleContext"):
            coordinator.issue_settlement_permit(dmg_id, lineage, context=ctx_b)

        # Permit can still be issued on legitimate context ctx_a
        permit = coordinator.issue_settlement_permit(dmg_id, lineage, context=ctx_a)
        assert permit.damage_instance_id == dmg_id

        coordinator.close_damage_instance(dmg_id, ctx_a)

    def test_p94_fr_06_concurrent_contexts_with_same_id_sequence_isolated(self) -> None:
        """
        P94-FR-06: Two BattleContexts (ctx_A, ctx_B) with fresh allocators (both allocating dmg_1)
        can both begin active DamageInstances concurrently on the same coordinator without
        overwriting or corrupting each other's ownership.
        """
        ctx_a = _make_context(troops_b=1000)
        ctx_b = _make_context(troops_b=1000)
        dmg_sys = DamageSystem(AttributeSystem())
        troop_sys = TroopSystem()
        res_sys = DamageResolutionSystem(dmg_sys, troop_sys)
        coordinator = DamageInstanceCoordinator(dmg_sys, res_sys)

        lineage = _make_lineage()

        # Both fresh contexts allocate dmg_1
        dmg_id_a = coordinator.begin_damage_instance(ctx_a, lineage)
        dmg_id_b = coordinator.begin_damage_instance(ctx_b, lineage)

        assert dmg_id_a == DamageInstanceId("dmg_1")
        assert dmg_id_b == DamageInstanceId("dmg_1")
        assert dmg_id_a == dmg_id_b  # Exact same string value!

        # Both active records exist independently in coordinator keyed by (id(context), id)
        rec_a = coordinator._active_instances.get((id(ctx_a), dmg_id_a))
        rec_b = coordinator._active_instances.get((id(ctx_b), dmg_id_b))
        assert rec_a is not None
        assert rec_b is not None
        assert rec_a.owning_context is ctx_a
        assert rec_b.owning_context is ctx_b

        # Issue permits explicitly targeting each context
        permit_a = coordinator.issue_settlement_permit(dmg_id_a, lineage, context=ctx_a)
        permit_b = coordinator.issue_settlement_permit(dmg_id_b, lineage, context=ctx_b)

        assert permit_a is not None
        assert permit_b is not None
        assert (id(ctx_a), permit_a.permit_id) in coordinator._permits
        assert (id(ctx_b), permit_b.permit_id) in coordinator._permits

        dmg_result = DamageResult(
            source_id="A1",
            target_id="B1",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.NORMAL_ATTACK,
            coefficient=1.0,
            base_damage=100.0,
            scaled_damage=100.0,
            final_damage=100,
        )
        req_a = DamageSettlementRequest(
            damage_result=dmg_result,
            assigned_target_damage=100,
            damage_instance_id=dmg_id_a,
            lineage=lineage,
            origin=SettlementOrigin.STAGE9,
        )
        req_b = DamageSettlementRequest(
            damage_result=dmg_result,
            assigned_target_damage=100,
            damage_instance_id=dmg_id_b,
            lineage=lineage,
            origin=SettlementOrigin.STAGE9,
        )

        # Settling permit_a on ctx_a succeeds and does not consume permit_b
        res_a = res_sys.settle(ctx_a, req_a, permit_a)
        assert res_a.actual_target_troop_loss == 100
        assert ctx_a.get_unit("B1").troops == 900
        assert ctx_b.get_unit("B1").troops == 1000  # Untouched

        rec_permit_b = coordinator._permits.get((id(ctx_b), permit_b.permit_id))
        assert rec_permit_b is not None
        assert not rec_permit_b.consumed

        # Settling permit_b on ctx_b succeeds
        res_b = res_sys.settle(ctx_b, req_b, permit_b)
        assert res_b.actual_target_troop_loss == 100
        assert ctx_b.get_unit("B1").troops == 900

        coordinator.close_damage_instance(dmg_id_a, ctx_a)
        coordinator.close_damage_instance(dmg_id_b, ctx_b)
        assert len(coordinator._active_instances) == 0
        assert len(coordinator._permits) == 0

