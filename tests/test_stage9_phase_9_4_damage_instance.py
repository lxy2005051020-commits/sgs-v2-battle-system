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

        dmg_id = coordinator.allocate_damage_instance_id(ctx)
        lineage = _make_lineage(SourceType.NORMAL_ATTACK)
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

        dmg_id = coordinator.allocate_damage_instance_id(ctx)
        lineage = _make_lineage()
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
        dmg_id = coordinator.allocate_damage_instance_id(ctx)
        lineage = _make_lineage()
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
