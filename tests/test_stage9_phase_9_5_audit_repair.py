from __future__ import annotations

import pytest

from sgs_v2.battle_core import (
    BattleContext,
    BattleEngine,
    BattleSystems,
    DamageInstanceId,
    EventBus,
    FinalizationProjectionPermit,
    FutureAdmissionGate,
    FutureAdmissionPermit,
    FutureBranchKind,
    LegacyFinalizationBarrier,
    LineupPosition,
    OperationIdAllocator,
    RandomSystem,
    UnitRuntime,
    VictorySystem,
)
from sgs_v2.battle_core.battle_finalization_coordinator import (
    BattleFinalizationCoordinator,
    BattleTerminationState,
)


def _unit(
    unit_id: str,
    team_id: str,
    position: LineupPosition,
    *,
    troops: int = 1000,
) -> UnitRuntime:
    return UnitRuntime(
        unit_id,
        unit_id.upper(),
        team_id,
        1000,
        troops,
        300,
        100,
        100,
        lineup_position=position,
    )


def make_context(battle_id: str = "test-ctx", *, a_troops: int = 1000, b_troops: int = 1000) -> BattleContext:
    units = {
        "a1": _unit("a1", "A", LineupPosition.COMMANDER, troops=a_troops),
        "b1": _unit("b1", "B", LineupPosition.COMMANDER, troops=b_troops),
    }
    return BattleContext(
        battle_id=battle_id,
        units=units,
        event_bus=EventBus(),
        random=RandomSystem(42),
        max_rounds=5,
        id_allocator=OperationIdAllocator(),
    )


def test_p95_rpr_01_finalization_coordinator_binds_first_battle_context() -> None:
    """P95-RPR-01: BattleFinalizationCoordinator permanently binds the first legitimate BattleContext."""
    coordinator = BattleFinalizationCoordinator(VictorySystem())
    assert coordinator.owning_context is None

    ctx_a = make_context("ctx_a")
    ctx_b = make_context("ctx_b")

    # Invalid argument types must reject BEFORE binding
    with pytest.raises(TypeError):
        coordinator.admit_damage_instance(ctx_a, "invalid_id")  # type: ignore[arg-type]
    assert coordinator.owning_context is None

    with pytest.raises(TypeError):
        coordinator.observe_legacy_barrier(ctx_a, "invalid_barrier")  # type: ignore[arg-type]
    assert coordinator.owning_context is None

    # First legitimate call binds ctx_a
    dmg_1 = ctx_a.id_allocator.allocate_damage_instance_id()
    coordinator.admit_damage_instance(ctx_a, dmg_1)
    assert coordinator.owning_context is ctx_a

    # Subsequent call with ctx_a succeeds
    coordinator.observe_damage_instance_death(ctx_a, dmg_1)
    assert coordinator.owning_context is ctx_a


def test_p95_rpr_02_foreign_battle_context_admission_rejected() -> None:
    """P95-RPR-02: foreign BattleContext admission rejected without state mutation or victory evaluation."""
    coordinator = BattleFinalizationCoordinator(VictorySystem())
    ctx_a = make_context("ctx_a")
    ctx_b = make_context("ctx_b")

    alloc_a = OperationIdAllocator()
    alloc_b = OperationIdAllocator()
    dmg_a = alloc_a.allocate_damage_instance_id()
    dmg_b = alloc_b.allocate_damage_instance_id()

    # Both allocators produce the same sequence ID
    assert dmg_a == dmg_b

    # Legitimate admission on ctx_a
    coordinator.admit_damage_instance(ctx_a, dmg_a)
    assert coordinator.owning_context is ctx_a
    assert dmg_a in coordinator.active_damage_instance_ids

    # Foreign admission attempt on ctx_b must be rejected before mutation
    with pytest.raises(ValueError, match="already bound to BattleContext"):
        coordinator.admit_damage_instance(ctx_b, dmg_b)

    # State remains unmutated
    assert coordinator.active_damage_instance_ids == (dmg_a,)
    assert coordinator.termination_state == BattleTerminationState.RUNNING
    assert coordinator.finalization_result is None
    assert coordinator._projection_permit is None


def test_p95_rpr_03_foreign_observe_complete_barrier_rejected_without_mutation() -> None:
    """P95-RPR-03: foreign observe/complete/barrier rejected before mutation, ctx_a lifecycle intact."""
    coordinator = BattleFinalizationCoordinator(VictorySystem())
    ctx_a = make_context("ctx_a")
    ctx_b = make_context("ctx_b")

    dmg_1 = ctx_a.id_allocator.allocate_damage_instance_id()
    coordinator.admit_damage_instance(ctx_a, dmg_1)

    # Foreign observe death rejected
    with pytest.raises(ValueError, match="already bound to BattleContext"):
        coordinator.observe_damage_instance_death(ctx_b, dmg_1)

    # Foreign complete rejected
    with pytest.raises(ValueError, match="already bound to BattleContext"):
        coordinator.complete_damage_instance(ctx_b, dmg_1)

    # Foreign barrier rejected
    with pytest.raises(ValueError, match="already bound to BattleContext"):
        coordinator.observe_legacy_barrier(ctx_b, LegacyFinalizationBarrier.ACTION_SETTLED)

    # ctx_a lifecycle intact
    assert dmg_1 in coordinator.active_damage_instance_ids
    assert coordinator.termination_state == BattleTerminationState.RUNNING

    # Legitimate complete on ctx_a succeeds
    coordinator.complete_damage_instance(ctx_a, dmg_1)
    assert dmg_1 not in coordinator.active_damage_instance_ids


def test_p95_rpr_04_equal_value_forged_finalization_projection_permit_rejected() -> None:
    """P95-RPR-04: equal-value forged FinalizationProjectionPermit rejected, legitimate permit usable."""
    coordinator = BattleFinalizationCoordinator(VictorySystem())
    ctx_a = make_context("ctx_a", b_troops=0)  # Team B defeated immediately

    coordinator.observe_legacy_barrier(ctx_a, LegacyFinalizationBarrier.INITIAL_SETTLED)
    claim = coordinator.claim_finalized_projection()
    assert claim is not None
    legitimate_permit, fin_res = claim

    # Forged clone with identical values
    forged = FinalizationProjectionPermit(
        permit_id=legitimate_permit.permit_id,
        finalization_id=legitimate_permit.finalization_id,
    )
    assert forged == legitimate_permit
    assert forged is not legitimate_permit

    # Forged consume rejected
    with pytest.raises(ValueError, match="Permit capability authenticity failure"):
        coordinator.consume_projection_permit(forged)

    assert coordinator._projection_consumed is False

    # Legitimate consume succeeds exactly once
    coordinator.consume_projection_permit(legitimate_permit)
    assert coordinator._projection_consumed is True

    # Replay rejected
    with pytest.raises(RuntimeError, match="already been consumed"):
        coordinator.consume_projection_permit(legitimate_permit)


def test_p95_rpr_05_cross_coordinator_equal_value_projection_permit_rejected() -> None:
    """P95-RPR-05: cross-coordinator equal-value projection permit rejected."""
    alloc_a = OperationIdAllocator()
    alloc_b = OperationIdAllocator()

    coord_a = BattleFinalizationCoordinator(VictorySystem(), id_allocator=alloc_a)
    coord_b = BattleFinalizationCoordinator(VictorySystem(), id_allocator=alloc_b)

    ctx_a = make_context("ctx_a", b_troops=0)
    ctx_b = make_context("ctx_b", b_troops=0)
    ctx_a.id_allocator = alloc_a
    ctx_b.id_allocator = alloc_b

    coord_a.observe_legacy_barrier(ctx_a, LegacyFinalizationBarrier.INITIAL_SETTLED)
    coord_b.observe_legacy_barrier(ctx_b, LegacyFinalizationBarrier.INITIAL_SETTLED)

    claim_a = coord_a.claim_finalized_projection()
    claim_b = coord_b.claim_finalized_projection()
    assert claim_a is not None and claim_b is not None

    permit_a, _ = claim_a
    permit_b, _ = claim_b

    assert permit_a.permit_id == permit_b.permit_id
    assert permit_a.finalization_id == permit_b.finalization_id
    assert permit_a == permit_b
    assert permit_a is not permit_b

    # Cross consume: passing permit_a to coord_b must be rejected
    with pytest.raises(ValueError, match="Permit capability authenticity failure"):
        coord_b.consume_projection_permit(permit_a)

    assert coord_b._projection_consumed is False
    assert coord_a._projection_consumed is False


def test_p95_rpr_06_foreign_projection_rejection_leaves_both_legitimate_permits_usable() -> None:
    """P95-RPR-06: foreign projection rejection leaves both legitimate permits usable exactly once."""
    alloc_a = OperationIdAllocator()
    alloc_b = OperationIdAllocator()

    coord_a = BattleFinalizationCoordinator(VictorySystem(), id_allocator=alloc_a)
    coord_b = BattleFinalizationCoordinator(VictorySystem(), id_allocator=alloc_b)

    ctx_a = make_context("ctx_a", b_troops=0)
    ctx_b = make_context("ctx_b", b_troops=0)
    ctx_a.id_allocator = alloc_a
    ctx_b.id_allocator = alloc_b

    coord_a.observe_legacy_barrier(ctx_a, LegacyFinalizationBarrier.INITIAL_SETTLED)
    coord_b.observe_legacy_barrier(ctx_b, LegacyFinalizationBarrier.INITIAL_SETTLED)

    claim_a = coord_a.claim_finalized_projection()
    claim_b = coord_b.claim_finalized_projection()
    assert claim_a is not None and claim_b is not None
    permit_a, _ = claim_a
    permit_b, _ = claim_b

    # Cross attempt rejected
    with pytest.raises(ValueError, match="Permit capability authenticity failure"):
        coord_b.consume_projection_permit(permit_a)

    # Legitimate permits on both coordinators succeed exactly once
    coord_a.consume_projection_permit(permit_a)
    coord_b.consume_projection_permit(permit_b)

    assert coord_a._projection_consumed is True
    assert coord_b._projection_consumed is True


def test_p95_rpr_07_equal_value_forged_future_admission_permit_rejected() -> None:
    """P95-RPR-07: equal-value forged FutureAdmissionPermit rejected, legitimate permit usable."""
    coordinator = BattleFinalizationCoordinator(VictorySystem())
    gate = FutureAdmissionGate(coordinator)

    permit = gate.request_admission(
        FutureBranchKind.NEXT_ACTION,
        parent_scope_identity="scope_root",
    )
    assert permit is not None

    forged = FutureAdmissionPermit(
        permit_id=permit.permit_id,
        branch_kind=permit.branch_kind,
        parent_scope_identity=permit.parent_scope_identity,
        termination_generation=permit.termination_generation,
    )
    assert forged == permit
    assert forged is not permit

    # Forged consume rejected
    with pytest.raises(ValueError, match="Permit capability authenticity failure"):
        gate.consume_permit(
            forged,
            expected_branch_kind=FutureBranchKind.NEXT_ACTION,
            expected_parent_scope_identity="scope_root",
        )

    assert permit.permit_id not in gate._consumed_permits

    # Legitimate permit succeeds exactly once
    gate.consume_permit(
        permit,
        expected_branch_kind=FutureBranchKind.NEXT_ACTION,
        expected_parent_scope_identity="scope_root",
    )
    assert permit.permit_id in gate._consumed_permits

    # Replay rejected
    with pytest.raises(RuntimeError, match="already been consumed"):
        gate.consume_permit(
            permit,
            expected_branch_kind=FutureBranchKind.NEXT_ACTION,
            expected_parent_scope_identity="scope_root",
        )


def test_p95_rpr_08_cross_gate_equal_value_permit_collision_rejected() -> None:
    """P95-RPR-08: cross-gate equal-value permit collision rejected."""
    alloc_a = OperationIdAllocator()
    alloc_b = OperationIdAllocator()

    coord_a = BattleFinalizationCoordinator(VictorySystem(), id_allocator=alloc_a)
    coord_b = BattleFinalizationCoordinator(VictorySystem(), id_allocator=alloc_b)

    gate_a = FutureAdmissionGate(coord_a, id_allocator=alloc_a)
    gate_b = FutureAdmissionGate(coord_b, id_allocator=alloc_b)

    permit_a = gate_a.request_admission(FutureBranchKind.NEXT_ACTION, "scope_root")
    permit_b = gate_b.request_admission(FutureBranchKind.NEXT_ACTION, "scope_root")
    assert permit_a is not None and permit_b is not None

    assert permit_a.permit_id == permit_b.permit_id
    assert permit_a.branch_kind == permit_b.branch_kind
    assert permit_a.parent_scope_identity == permit_b.parent_scope_identity
    assert permit_a.termination_generation == permit_b.termination_generation
    assert permit_a == permit_b
    assert permit_a is not permit_b

    # Cross gate consume rejected
    with pytest.raises(ValueError, match="Permit capability authenticity failure"):
        gate_b.consume_permit(
            permit_a,
            expected_branch_kind=FutureBranchKind.NEXT_ACTION,
            expected_parent_scope_identity="scope_root",
        )

    assert permit_a.permit_id not in gate_b._consumed_permits
    assert permit_b.permit_id not in gate_b._consumed_permits
    assert permit_a.permit_id not in gate_a._consumed_permits


def test_p95_rpr_09_foreign_future_admission_attempt_consumes_neither_legitimate_capability() -> None:
    """P95-RPR-09: foreign FutureAdmission attempt consumes neither capability, both remain usable."""
    alloc_a = OperationIdAllocator()
    alloc_b = OperationIdAllocator()

    coord_a = BattleFinalizationCoordinator(VictorySystem(), id_allocator=alloc_a)
    coord_b = BattleFinalizationCoordinator(VictorySystem(), id_allocator=alloc_b)

    gate_a = FutureAdmissionGate(coord_a, id_allocator=alloc_a)
    gate_b = FutureAdmissionGate(coord_b, id_allocator=alloc_b)

    permit_a = gate_a.request_admission(FutureBranchKind.NEXT_ACTION, "scope_root")
    permit_b = gate_b.request_admission(FutureBranchKind.NEXT_ACTION, "scope_root")
    assert permit_a is not None and permit_b is not None

    # Foreign consume attempt on gate_b
    with pytest.raises(ValueError, match="Permit capability authenticity failure"):
        gate_b.consume_permit(
            permit_a,
            expected_branch_kind=FutureBranchKind.NEXT_ACTION,
            expected_parent_scope_identity="scope_root",
        )

    # Legitimate permits on both gates succeed
    gate_a.consume_permit(
        permit_a,
        expected_branch_kind=FutureBranchKind.NEXT_ACTION,
        expected_parent_scope_identity="scope_root",
    )
    gate_b.consume_permit(
        permit_b,
        expected_branch_kind=FutureBranchKind.NEXT_ACTION,
        expected_parent_scope_identity="scope_root",
    )

    assert permit_a.permit_id in gate_a._consumed_permits
    assert permit_b.permit_id in gate_b._consumed_permits


def test_battle_engine_systems_reuse_fails_fast() -> None:
    """BattleEngine fails fast if systems instance is erroneously reused with a different BattleContext."""
    systems = BattleSystems()
    ctx_a = make_context("ctx_a", b_troops=0)
    engine_a = BattleEngine(ctx_a, systems)
    engine_a.run()
    assert ctx_a.ended is True

    # Reusing the same systems for ctx_b must fail fast before corrupting finalization
    ctx_b = make_context("ctx_b", b_troops=0)
    engine_b = BattleEngine(ctx_b, systems)
    with pytest.raises(ValueError, match="already bound to BattleContext"):
        engine_b.run()