from __future__ import annotations

from unittest.mock import MagicMock
import pytest

from sgs_v2.battle_core.battle_finalization_coordinator import (
    BattleFinalizationCoordinator,
    BattleTerminationRecord,
    FinalizationResult,
)
from sgs_v2.battle_core.battle_systems import BattleSystems
from sgs_v2.battle_core.context import BattleContext, BattleResult
from sgs_v2.battle_core.engine import BattleEngine
from sgs_v2.battle_core.enums import BattleEndReason, BattlePhase, DamageType, LineupPosition
from sgs_v2.battle_core.events import EventBus, EventType
from sgs_v2.battle_core.execution_right_system import (
    BattleTerminationState,
    FinalizationProjectionPermit,
    LegacyFinalizationBarrier,
)
from sgs_v2.battle_core.operation_identity import FinalizationId, OperationIdAllocator
from sgs_v2.battle_core.random_system import RandomSystem
from sgs_v2.battle_core.rule_hooks import RoundStartHook, UnitActionStartHook
from sgs_v2.battle_core.state_definition import StateDefinition
from sgs_v2.battle_core.state_lifecycle_system import StateLifecycleSystem
from sgs_v2.battle_core.stage7_state_params import PeriodicDamageStateParams
from sgs_v2.battle_core.trigger_system import ROUND_START_TRIGGER_TAG, UNIT_ACTION_START_TRIGGER_TAG
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


def _make_context(a_troops: int = 1000, b_troops: int = 1000, max_rounds: int = 3) -> BattleContext:
    return BattleContext(
        battle_id="test_b",
        units={
            "a1": _make_unit("a1", "team_a", True, a_troops),
            "b1": _make_unit("b1", "team_b", True, b_troops),
        },
        event_bus=EventBus(),
        random=RandomSystem(42),
        max_rounds=max_rounds,
    )


# =========================================================================
# 1. Six Legacy Finalization Barriers Compatibility Tests
# =========================================================================

def test_barrier_1_initial_settled() -> None:
    """Barrier 1: INITIAL_SETTLED occurs at pre-battle before round 1."""
    # Team B commander dead before battle starts
    context = _make_context(b_troops=0)
    systems = BattleSystems()
    engine = BattleEngine(context=context, systems=systems)

    result = engine.run()

    assert result.winner_team_id == "team_a"
    assert result.reason == BattleEndReason.COMMANDER_DEFEATED
    assert result.rounds_completed == 0
    assert context.ended is True
    assert context.current_round == 0

    event_types = [e.event_type for e in context.event_bus.history]
    assert event_types == [
        EventType.PHASE_ENTERED,  # PRE_BATTLE
        EventType.BATTLE_STARTED,
        EventType.PHASE_ENTERED,  # BATTLE_END
        EventType.BATTLE_ENDED,
    ]
    # Verify BATTLE_END and BATTLE_ENDED exactly once
    assert event_types.count(EventType.BATTLE_ENDED) == 1
    assert [e.payload.get("phase") for e in context.event_bus.history if e.event_type == EventType.PHASE_ENTERED] == [
        "PRE_BATTLE",
        "BATTLE_END",
    ]


def test_barrier_2_round_start_hooks_settled() -> None:
    """Barrier 2: ROUND_START_HOOKS_SETTLED occurs after RoundStartHook completes."""
    context = _make_context()
    context.states.register_definition(
        StateDefinition(
            state_id="dot_round_start",
            name="dot_round_start",
            tags=frozenset({ROUND_START_TRIGGER_TAG}),
            runtime_params_type=PeriodicDamageStateParams,
        )
    )
    # Lethal periodic damage on b1 triggering at ROUND_START
    StateLifecycleSystem().apply(
        context,
        state_id="dot_round_start",
        owner_id="b1",
        source_id="a1",
        runtime_params=PeriodicDamageStateParams(DamageType.WEAPON, 1500.0),
    )
    systems = BattleSystems()
    engine = BattleEngine(context=context, systems=systems)

    result = engine.run()

    assert result.winner_team_id == "team_a"
    assert result.reason == BattleEndReason.COMMANDER_DEFEATED
    assert result.rounds_completed == 1
    assert context.ended is True

    event_types = [e.event_type for e in context.event_bus.history]
    assert EventType.ROUND_STARTED in event_types
    assert EventType.DAMAGE_DEALT in event_types
    assert EventType.UNIT_DEFEATED in event_types
    assert EventType.BATTLE_ENDED in event_types

    # Event order: ROUND_STARTED -> DAMAGE_DEALT -> UNIT_DEFEATED -> BATTLE_ENDED
    idx_round_start = event_types.index(EventType.ROUND_STARTED)
    idx_damage = event_types.index(EventType.DAMAGE_DEALT)
    idx_defeat = event_types.index(EventType.UNIT_DEFEATED)
    idx_battle_end = event_types.index(EventType.BATTLE_ENDED)

    assert idx_round_start < idx_damage < idx_defeat < idx_battle_end
    # Ensure no UNIT_ACTION occurred because round start hook ended the battle
    assert EventType.UNIT_ACTION_STARTED not in event_types
    assert event_types.count(EventType.BATTLE_ENDED) == 1


def test_barrier_3_unit_action_start_hooks_settled_preserves_action_ended() -> None:
    """
    Barrier 3: UNIT_ACTION_START_HOOKS_SETTLED.
    Crucial regression check: when UnitActionStartHook causes commander death,
    ActionSystem.execute is skipped, BUT UNIT_ACTION_END and UNIT_ACTION_ENDED
    must be published BEFORE BATTLE_END and BATTLE_ENDED.
    """
    context = _make_context()
    context.states.register_definition(
        StateDefinition(
            state_id="dot_unit_start",
            name="dot_unit_start",
            tags=frozenset({UNIT_ACTION_START_TRIGGER_TAG}),
            runtime_params_type=PeriodicDamageStateParams,
        )
    )
    # Lethal periodic damage on b1 when b1 action starts
    # Make b1 faster so b1 acts first
    context.get_unit("b1").speed = 200
    StateLifecycleSystem().apply(
        context,
        state_id="dot_unit_start",
        owner_id="b1",
        source_id="a1",
        runtime_params=PeriodicDamageStateParams(DamageType.WEAPON, 1500.0),
    )
    systems = BattleSystems()
    engine = BattleEngine(context=context, systems=systems)

    result = engine.run()

    assert result.winner_team_id == "team_a"
    assert result.reason == BattleEndReason.COMMANDER_DEFEATED
    assert context.ended is True

    event_types = [e.event_type for e in context.event_bus.history]
    assert EventType.UNIT_ACTION_STARTED in event_types
    assert EventType.UNIT_ACTION_ENDED in event_types
    assert EventType.BATTLE_ENDED in event_types

    idx_action_start = event_types.index(EventType.UNIT_ACTION_STARTED)
    idx_defeat = event_types.index(EventType.UNIT_DEFEATED)
    idx_action_end = event_types.index(EventType.UNIT_ACTION_ENDED)
    idx_battle_end = event_types.index(EventType.BATTLE_ENDED)

    # Observable order: UNIT_ACTION_STARTED -> UNIT_DEFEATED -> UNIT_ACTION_ENDED -> BATTLE_ENDED
    assert idx_action_start < idx_defeat < idx_action_end < idx_battle_end
    # NormalAttack must NOT have executed
    assert EventType.NORMAL_ATTACK not in event_types
    assert event_types.count(EventType.BATTLE_ENDED) == 1


def test_barrier_4_action_settled_ordering_preserved() -> None:
    """
    Barrier 4: ACTION_SETTLED.
    Crucial frozen requirement:
    ActionSystem.execute -> ACTION_SETTLED observation/latch ->
    UNIT_ACTION_END -> UNIT_ACTION_ENDED -> projection claim/consume ->
    BATTLE_END -> BATTLE_ENDED.
    BATTLE_END and BATTLE_ENDED must NOT occur before UNIT_ACTION_ENDED!
    """
    # a1 deals enough damage to kill b1 (b_troops=50)
    context = _make_context(b_troops=50)
    context.get_unit("a1").speed = 200
    systems = BattleSystems(
        weapon_random_percent_range=(90, 90),
        weapon_low_damage_floor_range=(10, 10),
    )
    engine = BattleEngine(context=context, systems=systems)

    result = engine.run()

    assert result.winner_team_id == "team_a"
    assert result.reason == BattleEndReason.COMMANDER_DEFEATED
    assert context.ended is True

    event_types = [e.event_type for e in context.event_bus.history]
    idx_normal_attack = event_types.index(EventType.NORMAL_ATTACK)
    idx_damage = event_types.index(EventType.DAMAGE_DEALT)
    idx_defeat = event_types.index(EventType.UNIT_DEFEATED)
    idx_unit_action_ended = event_types.index(EventType.UNIT_ACTION_ENDED)
    idx_battle_ended = event_types.index(EventType.BATTLE_ENDED)

    assert idx_normal_attack < idx_damage < idx_defeat < idx_unit_action_ended < idx_battle_ended
    assert event_types.count(EventType.BATTLE_ENDED) == 1

    # Check phase transitions
    phases = [e.payload.get("phase") for e in context.event_bus.history if e.event_type == EventType.PHASE_ENTERED]
    idx_phase_action_end = phases.index("UNIT_ACTION_END")
    idx_phase_battle_end = phases.index("BATTLE_END")
    assert idx_phase_action_end < idx_phase_battle_end


def test_barrier_5_round_end_settled() -> None:
    """Barrier 5: ROUND_END_SETTLED occurs after ROUND_ENDED and ROUND_END state expiry."""
    context = _make_context()
    context.states.register_definition(
        StateDefinition(
            state_id="dot_round_end",
            name="dot_round_end",
            tags=frozenset({"ROUND_END"}),
            runtime_params_type=PeriodicDamageStateParams,
        )
    )
    # Give both high defense so normal attack doesn't kill
    context.get_unit("a1").defense = 9999
    context.get_unit("b1").defense = 9999
    # Apply lethal dot expiring at ROUND_END
    StateLifecycleSystem().apply(
        context,
        state_id="dot_round_end",
        owner_id="b1",
        source_id="a1",
        expires_round=1,
        expires_phase="ROUND_END",
        runtime_params=PeriodicDamageStateParams(DamageType.WEAPON, 1500.0),
    )
    # Hook StateLifecycleSystem to kill b1 on expiration for this test
    orig_expire = StateLifecycleSystem.expire_at

    def expire_with_death(self, ctx, round_no, phase):  # type: ignore[no-untyped-def]
        res = orig_expire(self, ctx, round_no=round_no, phase=phase)
        if phase == "ROUND_END":
            ctx.get_unit("b1").troops = 0
        return res

    systems = BattleSystems()
    systems.state_lifecycle_system.expire_at = expire_with_death.__get__(  # type: ignore[method-assign]
        systems.state_lifecycle_system
    )
    engine = BattleEngine(context=context, systems=systems)

    result = engine.run()

    assert result.winner_team_id == "team_a"
    assert result.reason == BattleEndReason.COMMANDER_DEFEATED
    assert context.ended is True

    event_types = [e.event_type for e in context.event_bus.history]
    assert EventType.ROUND_ENDED in event_types
    assert EventType.BATTLE_ENDED in event_types
    assert event_types.index(EventType.ROUND_ENDED) < event_types.index(EventType.BATTLE_ENDED)
    assert event_types.count(EventType.BATTLE_ENDED) == 1


def test_barrier_6_max_round_settled_evaluates_exactly_once() -> None:
    """Barrier 6: MAX_ROUND_SETTLED resolves max rounds and calls evaluator exactly once."""
    context = _make_context(a_troops=800, b_troops=500, max_rounds=1)
    context.get_unit("a1").defense = 9999
    context.get_unit("b1").defense = 9999

    systems = BattleSystems()
    # Spy on resolve_max_rounds
    resolve_spy = MagicMock(wraps=systems.victory_system.resolve_max_rounds)
    systems.victory_system.resolve_max_rounds = resolve_spy  # type: ignore[method-assign]

    engine = BattleEngine(context=context, systems=systems)
    result = engine.run()

    assert result.winner_team_id == "team_a"
    assert result.reason == BattleEndReason.MAX_ROUNDS
    assert result.rounds_completed == 1
    assert context.ended is True

    # Evaluator called exactly once
    assert resolve_spy.call_count == 1
    event_types = [e.event_type for e in context.event_bus.history]
    assert event_types.count(EventType.BATTLE_ENDED) == 1


# =========================================================================
# 2. FinalizationResult Deep Immutability Tests
# =========================================================================

def test_finalization_result_deep_immutability() -> None:
    """FinalizationResult is a frozen deep-immutable value object."""
    snapshot = (("a1", 800), ("b1", 600))
    res = FinalizationResult(
        finalization_id=FinalizationId("fin_1"),
        winner_team_id="team_a",
        reason=BattleEndReason.COMMANDER_DEFEATED,
        rounds_completed=2,
        final_troops_snapshot=snapshot,
    )

    # Dataclass is frozen
    with pytest.raises(Exception):
        res.rounds_completed = 3  # type: ignore[misc]

    # Snapshot is immutable tuple
    assert isinstance(res.final_troops_snapshot, tuple)
    assert res.final_troops_snapshot == (("a1", 800), ("b1", 600))

    # Reject mutable types for snapshot
    with pytest.raises(TypeError):
        FinalizationResult(
            finalization_id=FinalizationId("fin_2"),
            winner_team_id="team_a",
            reason=BattleEndReason.COMMANDER_DEFEATED,
            rounds_completed=1,
            final_troops_snapshot=[("a1", 100)],  # type: ignore[arg-type]
        )

    # Rejects comparison operators
    with pytest.raises(TypeError, match="does not support comparison operator"):
        _ = res < res  # type: ignore[operator]
    with pytest.raises(TypeError, match="does not support comparison operator"):
        _ = res <= res  # type: ignore[operator]
    with pytest.raises(TypeError, match="does not support comparison operator"):
        _ = res > res  # type: ignore[operator]
    with pytest.raises(TypeError, match="does not support comparison operator"):
        _ = res >= res  # type: ignore[operator]


def test_finalization_result_snapshot_detached_from_live_units() -> None:
    """Modifying live units or context after finalization does not alter FinalizationResult."""
    context = _make_context(b_troops=0)
    coordinator = BattleFinalizationCoordinator(VictorySystem())
    coordinator.observe_legacy_barrier(context, LegacyFinalizationBarrier.INITIAL_SETTLED)

    fin_res = coordinator.finalization_result
    assert fin_res is not None

    # Mutate live unit troops
    context.get_unit("a1").troops = 0
    context.get_unit("b1").troops = 9999

    # Snapshot retains original values
    snapshot_dict = dict(fin_res.final_troops_snapshot)
    assert snapshot_dict["a1"] == 1000
    assert snapshot_dict["b1"] == 0


# =========================================================================
# 3. Exactly-Once Creation & Permit Lifecycle Tests
# =========================================================================

def test_finalization_result_created_exactly_once() -> None:
    """Repeated calls to observe_legacy_barrier do not create duplicate results or IDs."""
    context = _make_context(b_troops=0)
    alloc = OperationIdAllocator()
    coordinator = BattleFinalizationCoordinator(VictorySystem(), id_allocator=alloc)

    coordinator.observe_legacy_barrier(context, LegacyFinalizationBarrier.INITIAL_SETTLED)
    first_res = coordinator.finalization_result
    assert first_res is not None
    assert coordinator.termination_state == BattleTerminationState.FINALIZED

    # Call again with different barriers
    coordinator.observe_legacy_barrier(context, LegacyFinalizationBarrier.ROUND_START_HOOKS_SETTLED)
    coordinator.observe_legacy_barrier(context, LegacyFinalizationBarrier.MAX_ROUND_SETTLED)

    # Identical instance and ID
    assert coordinator.finalization_result is first_res
    assert coordinator.finalization_result.finalization_id == first_res.finalization_id


def test_projection_permit_claim_and_consume_once() -> None:
    """Projection permit can be claimed once and consumed once."""
    context = _make_context(b_troops=0)
    coordinator = BattleFinalizationCoordinator(VictorySystem())
    coordinator.observe_legacy_barrier(context, LegacyFinalizationBarrier.INITIAL_SETTLED)

    # First claim succeeds
    claim = coordinator.claim_finalized_projection()
    assert claim is not None
    permit, result = claim
    assert isinstance(permit, FinalizationProjectionPermit)
    assert isinstance(result, FinalizationResult)

    # Second claim returns None
    second_claim = coordinator.claim_finalized_projection()
    assert second_claim is None

    # First consume succeeds
    coordinator.consume_projection_permit(permit)

    # Second consume raises RuntimeError
    with pytest.raises(RuntimeError, match="already been consumed"):
        coordinator.consume_projection_permit(permit)


def test_projection_permit_consume_validation() -> None:
    """Wrong permit or mismatched finalization ID is rejected before side effects."""
    context = _make_context(b_troops=0)
    coordinator = BattleFinalizationCoordinator(VictorySystem())
    coordinator.observe_legacy_barrier(context, LegacyFinalizationBarrier.INITIAL_SETTLED)

    claim = coordinator.claim_finalized_projection()
    assert claim is not None
    valid_permit, _ = claim

    # Wrong permit ID
    wrong_permit = FinalizationProjectionPermit(
        permit_id="forged_prm",
        finalization_id=valid_permit.finalization_id,
    )
    with pytest.raises(ValueError, match="not issued by this coordinator"):
        coordinator.consume_projection_permit(wrong_permit)

    # Wrong finalization ID
    mismatched_id_permit = FinalizationProjectionPermit(
        permit_id=valid_permit.permit_id,
        finalization_id=FinalizationId("fin_wrong"),
    )
    with pytest.raises(ValueError, match="does not match"):
        coordinator.consume_projection_permit(mismatched_id_permit)

    # Non-permit type
    with pytest.raises(TypeError):
        coordinator.consume_projection_permit("not_a_permit")  # type: ignore[arg-type]


def test_failed_consume_produces_no_side_effects() -> None:
    """Failed permit consumption causes 0 side effects on BattleContext."""
    context = _make_context(b_troops=0)
    systems = BattleSystems()
    engine = BattleEngine(context=context, systems=systems)

    # Coordinator finalizes
    systems.finalization_coordinator.observe_legacy_barrier(
        context, LegacyFinalizationBarrier.INITIAL_SETTLED
    )
    claim = systems.finalization_coordinator.claim_finalized_projection()
    assert claim is not None

    forged_permit = FinalizationProjectionPermit(
        permit_id="forged",
        finalization_id=FinalizationId("fin_fake"),
    )

    with pytest.raises(ValueError):
        systems.finalization_coordinator.consume_projection_permit(forged_permit)

    # Verify context is completely unpolluted
    assert context.ended is False
    assert context.result is None
    assert EventType.BATTLE_ENDED not in [e.event_type for e in context.event_bus.history]


# =========================================================================
# 4. No Re-evaluation During Projection & Already Ended Battle
# =========================================================================

def test_victory_system_no_projection_reevaluation() -> None:
    """During projection, VictorySystem.check is evaluated 0 times."""
    context = _make_context(b_troops=0)
    systems = BattleSystems()
    check_spy = MagicMock(wraps=systems.victory_system.check)
    systems.victory_system.check = check_spy  # type: ignore[method-assign]

    engine = BattleEngine(context=context, systems=systems)
    engine.run()

    # Initial barrier checked once, projection checked 0 times
    assert check_spy.call_count == 1


def test_run_on_already_ended_battle() -> None:
    """Running BattleEngine on already ended battle returns context.result without side effects."""
    context = _make_context(b_troops=0)
    systems = BattleSystems()
    engine = BattleEngine(context=context, systems=systems)

    first_result = engine.run()
    event_count = len(context.event_bus.history)

    # Run again on the already-ended context
    second_result = engine.run()

    assert second_result is first_result
    # No new events emitted
    assert len(context.event_bus.history) == event_count


# =========================================================================
# 5. Invariants & Architecture Guarantees
# =========================================================================

def test_inv_39_death_fact_not_equal_to_finalized_or_ended() -> None:
    """
    INV-39: UnitDeathFact != VictoryLatched != FINALIZED != context.ended.
    """
    context = _make_context()
    coordinator = BattleFinalizationCoordinator(VictorySystem())

    # 1. Death fact occurs: unit troops becomes 0
    context.get_unit("b1").troops = 0
    # At this point:
    assert context.get_unit("b1").is_alive is False
    # But coordinator is still RUNNING
    assert coordinator.termination_state == BattleTerminationState.RUNNING
    # And context.ended is still False
    assert context.ended is False

    # 2. Coordinator observes barrier:
    coordinator.observe_legacy_barrier(context, LegacyFinalizationBarrier.ACTION_SETTLED)
    # Now coordinator is FINALIZED
    assert coordinator.termination_state == BattleTerminationState.FINALIZED
    # BUT context.ended is STILL False until compatibility projection!
    assert context.ended is False

    # 3. Projection occurs
    claim = coordinator.claim_finalized_projection()
    assert claim is not None
    permit, result = claim
    coordinator.consume_projection_permit(permit)
    # Compatibility projection
    legacy_res = BattleResult(
        winner_team_id=result.winner_team_id,
        reason=result.reason,
        rounds_completed=result.rounds_completed,
        final_troops=dict(result.final_troops_snapshot),
    )
    context.ended = True
    context.result = legacy_res
    assert context.ended is True


def test_inv_41_coordinator_unique_semantic_owner() -> None:
    """
    INV-41: Only BattleFinalizationCoordinator owns BattleTerminationState.
    BattleEngine does not modify termination_state.
    """
    context = _make_context(b_troops=0)
    systems = BattleSystems()
    engine = BattleEngine(context=context, systems=systems)

    assert systems.finalization_coordinator.termination_state == BattleTerminationState.RUNNING
    engine.run()
    # State transitioned by coordinator
    assert systems.finalization_coordinator.termination_state == BattleTerminationState.FINALIZED
    # Engine only updated context.ended
    assert context.ended is True


def test_arch_8_event_bus_facts_only() -> None:
    """Architecture #8: EventBus does not orchestrate finalization."""
    bus = EventBus()
    # Confirm EventBus only records and notifies, cannot trigger finalization
    assert not hasattr(bus, "finalize")
    assert not hasattr(bus, "terminate")


def test_arch_9_battle_systems_composition_root() -> None:
    """Architecture #9: BattleSystems is the service composition root."""
    systems = BattleSystems()
    assert isinstance(systems.finalization_coordinator, BattleFinalizationCoordinator)
    assert systems.finalization_coordinator.victory_system is systems.victory_system
    assert systems.future_admission_gate.coordinator is systems.finalization_coordinator
    assert systems.legacy_action_dispatch_adapter.gate is systems.future_admission_gate
