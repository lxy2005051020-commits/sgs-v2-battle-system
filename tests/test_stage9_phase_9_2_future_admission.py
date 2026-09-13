from __future__ import annotations

from unittest.mock import MagicMock
import pytest

from sgs_v2.battle_core.action_system import ActionSystem
from sgs_v2.battle_core.battle_finalization_coordinator import (
    BattleFinalizationCoordinator,
    BattleTerminationRecord,
)
from sgs_v2.battle_core.battle_systems import BattleSystems
from sgs_v2.battle_core.context import BattleContext
from sgs_v2.battle_core.engine import BattleEngine
from sgs_v2.battle_core.enums import LineupPosition
from sgs_v2.battle_core.events import EventBus, EventType
from sgs_v2.battle_core.execution_right_system import (
    BattleTerminationState,
    FutureAdmissionGate,
    FutureAdmissionPermit,
    FutureBranchKind,
    LegacyActionDispatchAdapter,
    LegacyFinalizationBarrier,
)
from sgs_v2.battle_core.operation_identity import OperationIdAllocator
from sgs_v2.battle_core.random_system import RandomSystem
from sgs_v2.battle_core.unit import UnitRuntime
from sgs_v2.battle_core.victory_system import VictorySystem


def _make_unit(unit_id: str, team_id: str, is_commander: bool = True, troops: int = 1000) -> UnitRuntime:
    return UnitRuntime(
        unit_id=unit_id,
        name=unit_id,
        team_id=team_id,
        max_troops=max(1000, troops),
        troops=troops,
        attack=100,
        defense=100,
        speed=100,
        is_commander=is_commander,
        lineup_position=LineupPosition.COMMANDER if is_commander else LineupPosition.DEPUTY_1,
        intelligence=100,
    )


def _make_context(a_troops: int = 1000, b_troops: int = 1000) -> BattleContext:
    return BattleContext(
        battle_id="test_fa_b",
        units={
            "a1": _make_unit("a1", "team_a", True, a_troops),
            "b1": _make_unit("b1", "team_b", True, b_troops),
        },
        event_bus=EventBus(),
        random=RandomSystem(42),
        max_rounds=3,
    )


# =========================================================================
# 1. NEXT_ACTION Admission & Dispatch Happy Path
# =========================================================================

def test_next_action_admission_and_dispatch_happy_path() -> None:
    """RUNNING state allows NEXT_ACTION permit, adapter consumes and executes action once."""
    context = _make_context()
    coordinator = BattleFinalizationCoordinator(VictorySystem())
    gate = FutureAdmissionGate(coordinator)
    mock_action_system = MagicMock(spec=ActionSystem)
    adapter = LegacyActionDispatchAdapter(action_system=mock_action_system, gate=gate)

    parent_scope = "round_1_actor_a1"
    permit = gate.request_admission(
        branch_kind=FutureBranchKind.NEXT_ACTION,
        parent_scope_identity=parent_scope,
    )
    assert permit is not None
    assert permit.branch_kind == FutureBranchKind.NEXT_ACTION
    assert permit.parent_scope_identity == parent_scope
    assert permit.termination_generation == 0

    # Dispatch executes ActionSystem.execute once
    actor = context.get_unit("a1")
    adapter.dispatch(
        context=context,
        actor=actor,
        permit=permit,
        parent_scope_identity=parent_scope,
    )

    mock_action_system.execute.assert_called_once_with(context, actor)


# =========================================================================
# 2. Permit Reuse and Validation Rejections
# =========================================================================

def test_next_action_permit_reuse_rejected() -> None:
    """A consumed NEXT_ACTION permit cannot be reused; second consume fails before execute."""
    context = _make_context()
    coordinator = BattleFinalizationCoordinator(VictorySystem())
    gate = FutureAdmissionGate(coordinator)
    mock_action_system = MagicMock(spec=ActionSystem)
    adapter = LegacyActionDispatchAdapter(action_system=mock_action_system, gate=gate)

    parent_scope = "round_1_actor_a1"
    permit = gate.request_admission(
        branch_kind=FutureBranchKind.NEXT_ACTION,
        parent_scope_identity=parent_scope,
    )
    assert permit is not None

    actor = context.get_unit("a1")
    adapter.dispatch(context, actor, permit, parent_scope)
    assert mock_action_system.execute.call_count == 1

    # Attempt reuse
    with pytest.raises(RuntimeError, match="already been consumed"):
        adapter.dispatch(context, actor, permit, parent_scope)

    # ActionSystem was NOT called a second time
    assert mock_action_system.execute.call_count == 1


def test_next_action_permit_wrong_branch_kind_rejected() -> None:
    """LegacyActionDispatchAdapter rejects permits that are not NEXT_ACTION."""
    context = _make_context()
    coordinator = BattleFinalizationCoordinator(VictorySystem())
    gate = FutureAdmissionGate(coordinator)
    mock_action_system = MagicMock(spec=ActionSystem)
    adapter = LegacyActionDispatchAdapter(action_system=mock_action_system, gate=gate)

    parent_scope = "round_1_actor_a1"
    permit = gate.request_admission(
        branch_kind=FutureBranchKind.ASSAULT,
        parent_scope_identity=parent_scope,
    )
    assert permit is not None

    actor = context.get_unit("a1")
    with pytest.raises(ValueError, match="only handles NEXT_ACTION"):
        adapter.dispatch(context, actor, permit, parent_scope)

    mock_action_system.execute.assert_not_called()


def test_next_action_permit_wrong_parent_scope_rejected() -> None:
    """Gate rejects permit consumption when parent_scope_identity does not match issuance."""
    coordinator = BattleFinalizationCoordinator(VictorySystem())
    gate = FutureAdmissionGate(coordinator)

    permit = gate.request_admission(
        branch_kind=FutureBranchKind.NEXT_ACTION,
        parent_scope_identity="scope_correct",
    )
    assert permit is not None

    with pytest.raises(ValueError, match="Parent scope identity mismatch"):
        gate.consume_permit(
            permit=permit,
            expected_branch_kind=FutureBranchKind.NEXT_ACTION,
            expected_parent_scope_identity="scope_wrong",
        )


def test_next_action_permit_unissued_rejected() -> None:
    """Gate rejects a forged permit that was not issued by it."""
    coordinator = BattleFinalizationCoordinator(VictorySystem())
    gate = FutureAdmissionGate(coordinator)

    forged = FutureAdmissionPermit(
        permit_id="forged_prm",
        branch_kind=FutureBranchKind.NEXT_ACTION,
        parent_scope_identity="scope_1",
        termination_generation=0,
    )
    with pytest.raises(ValueError, match="was not issued by this gate"):
        gate.consume_permit(
            permit=forged,
            expected_branch_kind=FutureBranchKind.NEXT_ACTION,
            expected_parent_scope_identity="scope_1",
        )


def test_stale_termination_generation_rejected() -> None:
    """Permit issued before victory latch is rejected if consumed after latch increments generation."""
    context = _make_context(b_troops=0)
    coordinator = BattleFinalizationCoordinator(VictorySystem())
    gate = FutureAdmissionGate(coordinator)

    # Issue permit while RUNNING (generation = 0)
    permit = gate.request_admission(
        branch_kind=FutureBranchKind.NEXT_ACTION,
        parent_scope_identity="scope_gen",
    )
    assert permit is not None
    assert permit.termination_generation == 0

    # Coordinator observes death/victory -> generation increments
    coordinator.observe_legacy_barrier(context, LegacyFinalizationBarrier.INITIAL_SETTLED)
    assert coordinator.termination_generation > 0

    # Attempting to consume stale permit raises RuntimeError
    with pytest.raises(RuntimeError, match="Stale permit"):
        gate.consume_permit(
            permit=permit,
            expected_branch_kind=FutureBranchKind.NEXT_ACTION,
            expected_parent_scope_identity="scope_gen",
        )


# =========================================================================
# 3. INV-40: Victory Latch Blocks New NEXT_ACTION
# =========================================================================

def test_inv_40_victory_latched_blocks_new_next_action() -> None:
    """
    INV-40: After victory latch, no new NEXT_ACTION permit can be issued,
    even if legacy context.ended is still False.
    """
    context = _make_context(b_troops=0)
    coordinator = BattleFinalizationCoordinator(VictorySystem())
    gate = FutureAdmissionGate(coordinator)

    assert gate.can_admit(FutureBranchKind.NEXT_ACTION) is True

    # Latch/finalize in coordinator
    coordinator.observe_legacy_barrier(context, LegacyFinalizationBarrier.INITIAL_SETTLED)
    assert coordinator.termination_state == BattleTerminationState.FINALIZED
    # Notice: context.ended is STILL False!
    assert context.ended is False

    # Gate blocks future admission based on semantic termination state, NOT context.ended!
    assert gate.can_admit(FutureBranchKind.NEXT_ACTION) is False
    permit = gate.request_admission(
        branch_kind=FutureBranchKind.NEXT_ACTION,
        parent_scope_identity="scope_latched",
    )
    assert permit is None


# =========================================================================
# 4. Dead Actor Skips Gate Request
# =========================================================================

def test_dead_actor_skips_without_requesting_permit() -> None:
    """BattleEngine does not request permit for an actor that is not alive."""
    context = _make_context()
    context.get_unit("b1").troops = 0  # b1 is dead

    systems = BattleSystems()
    # Spy on gate.request_admission
    spy_request = MagicMock(wraps=systems.future_admission_gate.request_admission)
    systems.future_admission_gate.request_admission = spy_request  # type: ignore[method-assign]

    engine = BattleEngine(context=context, systems=systems)
    engine.run()

    # Verify no permit was requested with actor_b1 in parent_scope
    for call in spy_request.call_args_list:
        _, kwargs = call
        parent_scope = kwargs.get("parent_scope_identity", "")
        assert "actor_b1" not in parent_scope


# =========================================================================
# 5. Typed Capability Support for All Six Future Branches
# =========================================================================

def test_all_six_future_branches_typed_capability_support() -> None:
    """All 6 FutureBranchKinds are recognized by FutureAdmissionGate."""
    coordinator = BattleFinalizationCoordinator(VictorySystem())
    gate = FutureAdmissionGate(coordinator)

    for branch in FutureBranchKind:
        # RUNNING -> can admit
        assert gate.can_admit(branch) is True
        permit = gate.request_admission(branch, f"parent_for_{branch.value}")
        assert permit is not None
        assert permit.branch_kind == branch
        # Consuming the permit succeeds
        gate.consume_permit(permit, branch, f"parent_for_{branch.value}")

    # Now transition coordinator to FINALIZED
    context = _make_context(b_troops=0)
    coordinator.observe_legacy_barrier(context, LegacyFinalizationBarrier.INITIAL_SETTLED)

    for branch in FutureBranchKind:
        # FINALIZED -> cannot admit
        assert gate.can_admit(branch) is False
        assert gate.request_admission(branch, f"parent_for_{branch.value}") is None


# =========================================================================
# 6. Stage9 Admitted-Operation Set Is Empty (Phase 9.2 Guarantee)
# =========================================================================

def test_empty_stage9_operation_set() -> None:
    """
    Phase 9.2 architectural guarantee:
    ActionScope count = 0
    DamageInstance scope count = 0
    ReactionBatch scope count = 0
    No stub operation scopes exist.
    """
    import sgs_v2.battle_core as bc

    # Confirm no fake/stub scope classes are introduced in Phase 9.2
    assert not hasattr(bc, "ActionScope")
    assert not hasattr(bc, "FakeActionScope")
    assert not hasattr(bc, "DamageInstanceCoordinator")
    assert not hasattr(bc, "ReactionBatchCoordinator")
