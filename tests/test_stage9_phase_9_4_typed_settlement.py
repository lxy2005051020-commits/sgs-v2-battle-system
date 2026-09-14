from __future__ import annotations

import pytest

from sgs_v2.battle_core.attribute_system import AttributeSystem
from sgs_v2.battle_core.context import BattleContext
from sgs_v2.battle_core.damage_instance_coordinator import DamageInstanceCoordinator
from sgs_v2.battle_core.damage_resolution_system import (
    DamageResolutionResult,
    DamageResolutionSystem,
    DamageSettlementRequest,
    SettlementOrigin,
)
from sgs_v2.battle_core.damage_system import DamageRequest, DamageResult, DamageSystem
from sgs_v2.battle_core.enums import DamageSourceType, DamageType, LineupPosition
from sgs_v2.battle_core.events import EventBus, EventType
from sgs_v2.battle_core.execution_right_system import DamageSettlementPermit
from sgs_v2.battle_core.operation_identity import (
    ActionId,
    DamageInstanceId,
    NormalAttackInstanceId,
    OperationIdAllocator,
    OperationLineage,
    SourceType,
)
from sgs_v2.battle_core.random_system import RandomSystem
from sgs_v2.battle_core.troop_system import TroopSystem
from sgs_v2.battle_core.unit import UnitRuntime


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
    )


def _make_dummy_damage_result(
    source_id: str = "A1",
    target_id: str = "B1",
    final_damage: int = 300,
    prevented: bool = False,
) -> DamageResult:
    return DamageResult(
        source_id=source_id,
        target_id=target_id,
        damage_type=DamageType.WEAPON,
        source_type=DamageSourceType.NORMAL_ATTACK,
        coefficient=1.0,
        base_damage=float(final_damage),
        scaled_damage=float(final_damage),
        final_damage=final_damage,
        prevented=prevented,
        prevented_by_state_id="IRON_SHIELD" if prevented else None,
    )


class TestSettlementOriginAndRequests:
    """Test SettlementOrigin and DamageSettlementRequest contracts."""

    def test_settlement_origin_enum_values(self) -> None:
        assert SettlementOrigin.STAGE9.value == "STAGE9"
        assert SettlementOrigin.LEGACY_COMPAT.value == "LEGACY_COMPAT"
        assert len(SettlementOrigin) == 2

    def test_damage_settlement_request_stage9_valid(self) -> None:
        dmg = _make_dummy_damage_result(final_damage=300)
        lineage = _make_lineage()
        dmg_id = DamageInstanceId("dmg_1")
        req = DamageSettlementRequest(
            damage_result=dmg,
            assigned_target_damage=180,
            damage_instance_id=dmg_id,
            lineage=lineage,
            origin=SettlementOrigin.STAGE9,
        )
        assert req.damage_result == dmg
        assert req.assigned_target_damage == 180
        assert req.damage_instance_id == dmg_id
        assert req.lineage == lineage
        assert req.origin == SettlementOrigin.STAGE9

    def test_damage_settlement_request_stage9_requires_ids(self) -> None:
        dmg = _make_dummy_damage_result(final_damage=300)
        lineage = _make_lineage()
        dmg_id = DamageInstanceId("dmg_1")

        with pytest.raises(ValueError, match="damage_instance_id is required"):
            DamageSettlementRequest(
                damage_result=dmg,
                assigned_target_damage=180,
                damage_instance_id=None,
                lineage=lineage,
                origin=SettlementOrigin.STAGE9,
            )

        with pytest.raises(ValueError, match="lineage is required"):
            DamageSettlementRequest(
                damage_result=dmg,
                assigned_target_damage=180,
                damage_instance_id=dmg_id,
                lineage=None,
                origin=SettlementOrigin.STAGE9,
            )

    def test_damage_settlement_request_legacy_compat_valid(self) -> None:
        dmg = _make_dummy_damage_result(final_damage=250)
        req = DamageSettlementRequest(
            damage_result=dmg,
            assigned_target_damage=250,
            damage_instance_id=None,
            lineage=None,
            origin=SettlementOrigin.LEGACY_COMPAT,
        )
        assert req.damage_result == dmg
        assert req.assigned_target_damage == 250
        assert req.damage_instance_id is None
        assert req.lineage is None
        assert req.origin == SettlementOrigin.LEGACY_COMPAT

    def test_damage_settlement_request_legacy_compat_rejects_ids_or_amount_mismatch(self) -> None:
        dmg = _make_dummy_damage_result(final_damage=250)
        lineage = _make_lineage()
        dmg_id = DamageInstanceId("dmg_1")

        with pytest.raises(ValueError, match="damage_instance_id must be None"):
            DamageSettlementRequest(
                damage_result=dmg,
                assigned_target_damage=250,
                damage_instance_id=dmg_id,
                lineage=None,
                origin=SettlementOrigin.LEGACY_COMPAT,
            )

        with pytest.raises(ValueError, match="lineage must be None"):
            DamageSettlementRequest(
                damage_result=dmg,
                assigned_target_damage=250,
                damage_instance_id=None,
                lineage=lineage,
                origin=SettlementOrigin.LEGACY_COMPAT,
            )

        with pytest.raises(ValueError, match="must equal damage_result.final_damage"):
            DamageSettlementRequest(
                damage_result=dmg,
                assigned_target_damage=200,
                damage_instance_id=None,
                lineage=None,
                origin=SettlementOrigin.LEGACY_COMPAT,
            )

    def test_damage_settlement_request_immutability_and_forbid_ordering(self) -> None:
        dmg = _make_dummy_damage_result(final_damage=250)
        req = DamageSettlementRequest(
            damage_result=dmg,
            assigned_target_damage=250,
            damage_instance_id=None,
            lineage=None,
            origin=SettlementOrigin.LEGACY_COMPAT,
        )
        with pytest.raises(AttributeError):
            req.assigned_target_damage = 300  # type: ignore

        with pytest.raises(TypeError, match="does not support comparison operator '<'"):
            _ = req < req  # type: ignore


class TestDamageResolutionResultModelA:
    """Test Model A DamageResolutionResult properties, validations, and compatibility."""

    def test_model_a_creation_and_properties(self) -> None:
        dmg = _make_dummy_damage_result(final_damage=300)
        res = DamageResolutionResult(
            damage=dmg,
            assigned_target_damage=180,
            actual_target_troop_loss=100,
            target_troops_before=100,
            target_troops_after=0,
            target_defeated=True,
            credited_damage=100,
            troop_change=None,
            damage_instance_id=DamageInstanceId("dmg_1"),
            lineage=_make_lineage(),
        )
        # Authoritative fields
        assert res.damage.final_damage == 300
        assert res.assigned_target_damage == 180
        assert res.actual_target_troop_loss == 100
        assert res.target_troops_before == 100
        assert res.target_troops_after == 0
        assert res.target_defeated is True
        assert res.credited_damage == 100

        # Compatibility read-only projections
        assert res.dtotal == 300
        assert res.requested_damage == 180  # Compatibility projection to Dtarget
        assert res.defeated is True

        # Ensure DamageResult.requested_damage remains Dtotal
        assert res.damage.requested_damage == 300

    def test_model_a_rejects_arithmetic_mismatch(self) -> None:
        dmg = _make_dummy_damage_result(final_damage=300)
        with pytest.raises(ValueError, match="actual_target_troop_loss .* must equal"):
            DamageResolutionResult(
                damage=dmg,
                assigned_target_damage=180,
                actual_target_troop_loss=100,
                target_troops_before=100,
                target_troops_after=50,  # 100 - 50 = 50 != 100
                target_defeated=False,
                credited_damage=100,
                troop_change=None,
            )

    def test_model_a_forbids_ordering(self) -> None:
        dmg = _make_dummy_damage_result(final_damage=300)
        res = DamageResolutionResult(
            damage=dmg,
            assigned_target_damage=180,
            actual_target_troop_loss=100,
            target_troops_before=100,
            target_troops_after=0,
            target_defeated=True,
            credited_damage=100,
            troop_change=None,
        )
        with pytest.raises(TypeError, match="does not support comparison operator '<'"):
            _ = res < res  # type: ignore


class TestDamageResolutionSystemSettle:
    """Test settle() atomic permit validation, one-shot consume, and replay blocking."""

    def test_settle_successful_one_shot(self) -> None:
        ctx = _make_context(troops_b=1000)
        dmg_sys = DamageSystem(AttributeSystem())
        troop_sys = TroopSystem()
        res_sys = DamageResolutionSystem(dmg_sys, troop_sys)
        coordinator = DamageInstanceCoordinator(dmg_sys, res_sys)

        dmg_id = coordinator.allocate_damage_instance_id(ctx)
        lineage = _make_lineage()
        permit = coordinator.issue_settlement_permit(dmg_id, lineage, ctx)

        dmg_result = _make_dummy_damage_result(final_damage=300)
        req = DamageSettlementRequest(
            damage_result=dmg_result,
            assigned_target_damage=180,
            damage_instance_id=dmg_id,
            lineage=lineage,
            origin=SettlementOrigin.STAGE9,
        )

        res = res_sys.settle(ctx, req, permit)
        assert res.damage.final_damage == 300
        assert res.assigned_target_damage == 180
        assert res.actual_target_troop_loss == 180
        assert res.target_troops_before == 1000
        assert res.target_troops_after == 820
        assert res.target_defeated is False
        assert res.credited_damage == 180
        assert ctx.get_unit("B1").troops == 820

        # Check DAMAGE_DEALT event
        events = [e for e in ctx.event_bus.history if e.event_type == EventType.DAMAGE_DEALT]
        assert len(events) == 1
        assert events[0].payload["requested_damage"] == 180  # Dtarget
        assert events[0].payload["damage"] == 180  # Actual loss

    def test_settle_replay_protection_blocks_second_consume(self) -> None:
        ctx = _make_context(troops_b=1000)
        dmg_sys = DamageSystem(AttributeSystem())
        troop_sys = TroopSystem()
        res_sys = DamageResolutionSystem(dmg_sys, troop_sys)
        coordinator = DamageInstanceCoordinator(dmg_sys, res_sys)

        dmg_id = coordinator.allocate_damage_instance_id(ctx)
        lineage = _make_lineage()
        permit = coordinator.issue_settlement_permit(dmg_id, lineage, ctx)

        dmg_result = _make_dummy_damage_result(final_damage=300)
        req = DamageSettlementRequest(
            damage_result=dmg_result,
            assigned_target_damage=180,
            damage_instance_id=dmg_id,
            lineage=lineage,
            origin=SettlementOrigin.STAGE9,
        )

        # First settlement succeeds
        res_sys.settle(ctx, req, permit)
        assert ctx.get_unit("B1").troops == 820
        initial_event_count = len(ctx.event_bus.history)

        # Replayed settlement MUST be rejected with domain error
        with pytest.raises(ValueError, match="has already been consumed"):
            res_sys.settle(ctx, req, permit)

        # Assert ZERO side effects on replay attempt
        assert ctx.get_unit("B1").troops == 820  # Troops completely unchanged
        assert len(ctx.event_bus.history) == initial_event_count  # Zero new events

    def test_settle_rejects_fake_permit(self) -> None:
        ctx = _make_context(troops_b=1000)
        dmg_sys = DamageSystem(AttributeSystem())
        troop_sys = TroopSystem()
        res_sys = DamageResolutionSystem(dmg_sys, troop_sys)
        coordinator = DamageInstanceCoordinator(dmg_sys, res_sys)

        dmg_id = coordinator.allocate_damage_instance_id(ctx)
        lineage = _make_lineage()
        # Create a fake permit not issued by coordinator
        fake_permit = DamageSettlementPermit(
            permit_id="fake_permit_999",
            damage_instance_id=dmg_id,
        )

        dmg_result = _make_dummy_damage_result(final_damage=300)
        req = DamageSettlementRequest(
            damage_result=dmg_result,
            assigned_target_damage=180,
            damage_instance_id=dmg_id,
            lineage=lineage,
            origin=SettlementOrigin.STAGE9,
        )

        with pytest.raises(ValueError, match="was not issued by this coordinator"):
            res_sys.settle(ctx, req, fake_permit)

        assert ctx.get_unit("B1").troops == 1000
        assert len(ctx.event_bus.history) == 0

    def test_settle_rejects_cross_instance_mismatch(self) -> None:
        ctx = _make_context(troops_b=1000)
        dmg_sys = DamageSystem(AttributeSystem())
        troop_sys = TroopSystem()
        res_sys = DamageResolutionSystem(dmg_sys, troop_sys)
        coordinator = DamageInstanceCoordinator(dmg_sys, res_sys)

        id_a = DamageInstanceId("dmg_A")
        id_b = DamageInstanceId("dmg_B")
        lineage = _make_lineage()

        permit_a = coordinator.issue_settlement_permit(id_a, lineage, ctx)

        dmg_result = _make_dummy_damage_result(final_damage=300)
        # Request B paired with Permit A
        req_b = DamageSettlementRequest(
            damage_result=dmg_result,
            assigned_target_damage=180,
            damage_instance_id=id_b,
            lineage=lineage,
            origin=SettlementOrigin.STAGE9,
        )

        with pytest.raises(ValueError, match="does not match request damage_instance_id"):
            res_sys.settle(ctx, req_b, permit_a)

        assert ctx.get_unit("B1").troops == 1000
        assert len(ctx.event_bus.history) == 0

    def test_settle_rejects_lineage_mismatch(self) -> None:
        ctx = _make_context(troops_b=1000)
        dmg_sys = DamageSystem(AttributeSystem())
        troop_sys = TroopSystem()
        res_sys = DamageResolutionSystem(dmg_sys, troop_sys)
        coordinator = DamageInstanceCoordinator(dmg_sys, res_sys)

        dmg_id = coordinator.allocate_damage_instance_id(ctx)
        lineage_issued = _make_lineage(SourceType.NORMAL_ATTACK)
        lineage_request = _make_lineage(SourceType.ACTIVE_SKILL)

        permit = coordinator.issue_settlement_permit(dmg_id, lineage_issued, ctx)

        dmg_result = _make_dummy_damage_result(final_damage=300)
        req = DamageSettlementRequest(
            damage_result=dmg_result,
            assigned_target_damage=180,
            damage_instance_id=dmg_id,
            lineage=lineage_request,
            origin=SettlementOrigin.STAGE9,
        )

        with pytest.raises(ValueError, match="OperationLineage mismatch"):
            res_sys.settle(ctx, req, permit)

        assert ctx.get_unit("B1").troops == 1000
        assert len(ctx.event_bus.history) == 0

    def test_settle_prevented_damage_zero_mutation(self) -> None:
        ctx = _make_context(troops_b=1000)
        dmg_sys = DamageSystem(AttributeSystem())
        troop_sys = TroopSystem()
        res_sys = DamageResolutionSystem(dmg_sys, troop_sys)
        coordinator = DamageInstanceCoordinator(dmg_sys, res_sys)

        dmg_id = coordinator.allocate_damage_instance_id(ctx)
        lineage = _make_lineage()
        permit = coordinator.issue_settlement_permit(dmg_id, lineage, ctx)

        dmg_result = _make_dummy_damage_result(final_damage=300, prevented=True)
        req = DamageSettlementRequest(
            damage_result=dmg_result,
            assigned_target_damage=180,
            damage_instance_id=dmg_id,
            lineage=lineage,
            origin=SettlementOrigin.STAGE9,
        )

        res = res_sys.settle(ctx, req, permit)
        assert res.actual_target_troop_loss == 0
        assert res.credited_damage == 0
        assert res.troop_change is None
        assert res.target_defeated is False
        assert ctx.get_unit("B1").troops == 1000

        # DAMAGE_PREVENTED is observed, but no DAMAGE_DEALT or UNIT_DEFEATED
        prevented_events = [e for e in ctx.event_bus.history if e.event_type == EventType.DAMAGE_PREVENTED]
        dealt_events = [e for e in ctx.event_bus.history if e.event_type == EventType.DAMAGE_DEALT]
        defeated_events = [e for e in ctx.event_bus.history if e.event_type == EventType.UNIT_DEFEATED]
        assert len(prevented_events) == 1
        assert len(dealt_events) == 0
        assert len(defeated_events) == 0


class TestLegacyCompatibility:
    """Test legacy resolve() and apply_result() remain completely compatible."""

    def test_legacy_apply_result_works_repeatedly(self) -> None:
        ctx = _make_context(troops_b=1000)
        dmg_sys = DamageSystem(AttributeSystem())
        troop_sys = TroopSystem()
        res_sys = DamageResolutionSystem(dmg_sys, troop_sys)

        dmg_result = _make_dummy_damage_result(final_damage=100)

        # First call
        res1 = res_sys.apply_result(ctx, dmg_result)
        assert res1.damage.final_damage == 100
        assert res1.assigned_target_damage == 100
        assert res1.actual_target_troop_loss == 100
        assert res1.credited_damage == 100
        assert res1.damage_instance_id is None
        assert res1.lineage is None
        assert ctx.get_unit("B1").troops == 900

        # Second legacy call succeeds because legacy API is not subject to Stage9 one-shot replay guard
        res2 = res_sys.apply_result(ctx, dmg_result)
        assert res2.actual_target_troop_loss == 100
        assert ctx.get_unit("B1").troops == 800

    def test_legacy_apply_result_has_no_assigned_amount_parameter(self) -> None:
        dmg_sys = DamageSystem(AttributeSystem())
        troop_sys = TroopSystem()
        res_sys = DamageResolutionSystem(dmg_sys, troop_sys)

        import inspect
        sig = inspect.signature(res_sys.apply_result)
        param_names = list(sig.parameters.keys())
        assert param_names == ["context", "damage"], (
            "apply_result must only accept context and damage; "
            "no optional assigned_amount parameter is permitted."
        )

    def test_p94_r01_resolve_traverses_typed_settle_legacy(self) -> None:
        import unittest.mock

        ctx = _make_context(troops_b=1000)
        dmg_sys = DamageSystem(AttributeSystem())
        troop_sys = TroopSystem()
        res_sys = DamageResolutionSystem(dmg_sys, troop_sys)

        req = DamageRequest(
            source_id="A1",
            target_id="B1",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.NORMAL_ATTACK,
            coefficient=1.0,
        )

        with unittest.mock.patch.object(
            res_sys, "_settle_legacy", wraps=res_sys._settle_legacy
        ) as spy:
            res = res_sys.resolve(ctx, req)
            spy.assert_called_once()
            called_ctx, called_req = spy.call_args[0]
            assert isinstance(called_req, DamageSettlementRequest)
            assert called_req.origin == SettlementOrigin.LEGACY_COMPAT
            assert called_req.damage_instance_id is None
            assert called_req.lineage is None
            assert called_req.assigned_target_damage == res.damage.final_damage
            assert res.damage_instance_id is None
            assert res.lineage is None
            assert res.actual_target_troop_loss > 0

    def test_p94_r02_apply_result_traverses_typed_settle_legacy_with_unchanged_signature(self) -> None:
        import inspect
        import unittest.mock

        ctx = _make_context(troops_b=1000)
        dmg_sys = DamageSystem(AttributeSystem())
        troop_sys = TroopSystem()
        res_sys = DamageResolutionSystem(dmg_sys, troop_sys)

        sig = inspect.signature(res_sys.apply_result)
        params = list(sig.parameters.values())
        assert [p.name for p in params] == ["context", "damage"]
        assert all(p.default == inspect.Parameter.empty for p in params)

        dmg_result = _make_dummy_damage_result(final_damage=250)
        with unittest.mock.patch.object(
            res_sys, "_settle_legacy", wraps=res_sys._settle_legacy
        ) as spy:
            res = res_sys.apply_result(ctx, dmg_result)
            spy.assert_called_once()
            called_ctx, called_req = spy.call_args[0]
            assert isinstance(called_req, DamageSettlementRequest)
            assert called_req.origin == SettlementOrigin.LEGACY_COMPAT
            assert called_req.damage_instance_id is None
            assert called_req.lineage is None
            assert called_req.assigned_target_damage == 250
            assert res.actual_target_troop_loss == 250
            assert res.damage_instance_id is None
            assert res.lineage is None

    def test_p94_r06_damage_resolution_result_rejects_damage_instance_id_without_lineage(self) -> None:
        dmg_result = _make_dummy_damage_result(final_damage=100)
        dmg_id = DamageInstanceId("test_id")
        with pytest.raises(ValueError, match="damage_instance_id and lineage must either both be None"):
            DamageResolutionResult(
                damage=dmg_result,
                assigned_target_damage=100,
                actual_target_troop_loss=100,
                target_troops_before=1000,
                target_troops_after=900,
                target_defeated=False,
                credited_damage=100,
                troop_change=None,
                damage_instance_id=dmg_id,
                lineage=None,
            )

    def test_p94_r07_damage_resolution_result_rejects_lineage_without_damage_instance_id(self) -> None:
        dmg_result = _make_dummy_damage_result(final_damage=100)
        lineage = _make_lineage()
        with pytest.raises(ValueError, match="damage_instance_id and lineage must either both be None"):
            DamageResolutionResult(
                damage=dmg_result,
                assigned_target_damage=100,
                actual_target_troop_loss=100,
                target_troops_before=1000,
                target_troops_after=900,
                target_defeated=False,
                credited_damage=100,
                troop_change=None,
                damage_instance_id=None,
                lineage=lineage,
            )
