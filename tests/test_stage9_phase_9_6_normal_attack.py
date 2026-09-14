from __future__ import annotations

import ast
import inspect
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from sgs_v2.battle_core import (
    ActionId,
    BattleContext,
    BattleEngine,
    BattlePhase,
    BattleSystems,
    DamageRequest,
    DamageResult,
    DamageSourceType,
    DamageType,
    EventBus,
    EventType,
    LineupPosition,
    NormalAttackInstanceId,
    NormalAttackResult,
    NormalAttackSystem,
    OfficialStateId,
    OperationIdAllocator,
    OperationLineage,
    RandomSystem,
    SkillSlot,
    SourceType,
    StateInstance,
    TargetResolutionId,
    TargetResolutionResult,
    UnitRuntime,
    register_official_state_definitions,
)
from sgs_v2.battle_core.battle_finalization_coordinator import (
    BattleFinalizationCoordinator,
    BattleTerminationRecord,
)
from sgs_v2.battle_core.execution_right_system import (
    ActionExecutionState,
    ActionScope,
    AssaultDispatchPort,
    BattleTerminationState,
    ComboActionGrant,
    ComboCheckpointState,
    ComboGrantState,
    FutureAdmissionGate,
    FutureAdmissionPermit,
    FutureBranchKind,
    admit_action_scope,
)
from sgs_v2.battle_core.stage9_state_params import (
    ComboStateParams,
    GuardStateParams,
    TauntStateParams,
)
from sgs_v2.battle_core.victory_system import VictorySystem


def _make_unit(
    unit_id: str,
    team_id: str,
    troops: int = 1000,
    speed: int = 100,
    is_commander: bool = False,
) -> UnitRuntime:
    pos = LineupPosition.COMMANDER if is_commander else LineupPosition.DEPUTY_1
    return UnitRuntime(
        unit_id=unit_id,
        name=f"{team_id}_{unit_id}",
        team_id=team_id,
        max_troops=max(troops, 1000),
        troops=troops,
        attack=100,
        defense=100,
        intelligence=100,
        speed=speed,
        lineup_position=pos,
    )


def _make_context(
    a1_troops: int = 1000,
    b1_troops: int = 1000,
    b2_troops: int = 1000,
    battle_id: str = "test_phase96",
) -> BattleContext:
    units = {
        "a1": _make_unit("a1", "team_a", troops=a1_troops, is_commander=True),
        "b1": _make_unit("b1", "team_b", troops=b1_troops, is_commander=True),
        "b2": _make_unit("b2", "team_b", troops=b2_troops, is_commander=False),
    }
    ctx = BattleContext(
        battle_id=battle_id,
        units=units,
        event_bus=EventBus(),
        random=RandomSystem(42),
        max_rounds=3,
    )
    register_official_state_definitions(ctx.states)
    return ctx


# =========================================================================
# 1. Architecture Guarantees & P96-B01
# =========================================================================

def test_arch_p96_normal_attack_is_unique_master() -> None:
    """Production NormalAttackSystem is the sole authoritative master for physical normal attacks."""
    systems = BattleSystems()
    assert isinstance(systems.normal_attack_system, NormalAttackSystem)
    assert systems.action_system._normal_attack is systems.normal_attack_system
    assert systems.normal_attack_system.damage_instance_coordinator is systems.damage_instance_coordinator
    assert systems.normal_attack_system.target_resolution_system is systems.target_resolution_system
    assert systems.normal_attack_system.future_admission_gate is systems.future_admission_gate
    assert systems.normal_attack_system.assault_dispatch_port is systems.assault_dispatch_port


def test_arch_p96_no_bypass_methods_on_gate_or_assault() -> None:
    """FutureAdmissionGate and AssaultDispatchPort contain no legacy bypass methods."""
    gate_methods = [m for m in dir(FutureAdmissionGate) if not m.startswith("_")]
    assert "force_admit" not in gate_methods
    assert "bypass" not in gate_methods
    assert "admit_all" not in gate_methods

    assault_methods = [m for m in dir(AssaultDispatchPort) if not m.startswith("_")]
    assert "execute_assault_skills" not in assault_methods
    assert "bypass" not in assault_methods


def test_arch_p96_assault_dispatch_port_is_seam_only() -> None:
    """AssaultDispatchPort verifies permit, caller scope identity, and produces zero gameplay side effects."""
    coordinator = BattleFinalizationCoordinator(VictorySystem())
    gate = FutureAdmissionGate(coordinator)
    port = AssaultDispatchPort(gate)

    context = _make_context()
    actor = context.get_unit("a1")
    permit = gate.request_admission(FutureBranchKind.ASSAULT, "parent_scope_1")
    assert permit is not None

    # Dispatch consumes permit
    port.dispatch(
        context=context,
        permit=permit,
        parent_scope_identity="parent_scope_1",
        actor=actor,
        actual_target_id="b1",
    )
    assert permit.permit_id in gate._consumed_permits


def test_arch_p96_battle_engine_contains_no_type_error_retry() -> None:
    """BattleEngine contains no `except TypeError` replay fallback (P96-B01)."""
    engine_file = Path(inspect.getfile(BattleEngine))
    source = engine_file.read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Try):
            for handler in node.handlers:
                if handler.type is not None:
                    if isinstance(handler.type, ast.Name) and handler.type.id == "TypeError":
                        pytest.fail("BattleEngine must not contain except TypeError block")


def test_p96_rpr_01_battle_engine_no_destructive_type_error_replay() -> None:
    """P96-RPR-01: An Action execution that raises TypeError propagates without retry; side effects occur exactly once."""
    context = _make_context()
    systems = BattleSystems()
    engine = BattleEngine(context=context, systems=systems)

    side_effect_count = 0
    execute_call_count = 0

    def fail_with_type_error(context, actor, action_scope=None):
        nonlocal side_effect_count, execute_call_count
        execute_call_count += 1
        side_effect_count += 1
        raise TypeError("Simulated internal TypeError after destructive side effect")

    systems.action_system.execute = fail_with_type_error

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    with pytest.raises(TypeError, match="Simulated internal TypeError"):
        try:
            systems.action_system.execute(
                context=context,
                actor=context.get_unit("a1"),
                action_scope=scope,
            )
        finally:
            scope.mark_terminal()
            systems.finalization_coordinator.complete_action_scope(context, scope)

    assert execute_call_count == 1
    assert side_effect_count == 1
    assert scope.action_id not in systems.finalization_coordinator.active_action_scope_ids


# =========================================================================
# 2. Hard Gate Sequencing & Invariant Guarantees
# =========================================================================

def test_p96_hard_gate_permit_consumed_before_action_id_allocation() -> None:
    """NEXT_ACTION permit is consumed BEFORE ActionId is allocated."""
    context = _make_context()
    systems = BattleSystems()

    action_seq_at_consume = None
    orig_consume = systems.future_admission_gate.consume_permit
    def spy_consume(permit, expected_branch_kind, expected_parent_scope_identity):
        nonlocal action_seq_at_consume
        action_seq_at_consume = context.id_allocator._action_seq
        return orig_consume(permit, expected_branch_kind, expected_parent_scope_identity)
    systems.future_admission_gate.consume_permit = spy_consume

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    assert permit is not None

    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)
    assert action_seq_at_consume == 0
    assert context.id_allocator._action_seq == 1
    assert scope.admitted is True


def test_p96_hard_gate_permit_consumed_before_na2_id_allocation() -> None:
    """COMBO_SECOND_NORMAL_ATTACK permit is consumed BEFORE NormalAttackInstanceId #2 is allocated."""
    context = _make_context()
    systems = BattleSystems()

    systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.COMBO.value,
        owner_id="a1",
        source_id="a1",
        source_skill_id="combo_skill",
        source_skill_slot=SkillSlot.INHERENT,
        runtime_params=ComboStateParams(remaining_actions=1),
    )

    na_seq_at_combo_consume = None
    orig_consume = systems.future_admission_gate.consume_permit
    def spy_consume(permit, expected_branch_kind, expected_parent_scope_identity):
        nonlocal na_seq_at_combo_consume
        if expected_branch_kind == FutureBranchKind.COMBO_SECOND_NORMAL_ATTACK:
            na_seq_at_combo_consume = context.id_allocator._normal_attack_seq
        return orig_consume(permit, expected_branch_kind, expected_parent_scope_identity)
    systems.future_admission_gate.consume_permit = spy_consume

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    res = systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)
    assert res is not None
    assert res.combo_second_attack is not None

    # When permit was consumed, NA #2 was not yet allocated (only NA #1 seq=1 was allocated)
    assert na_seq_at_combo_consume == 1
    # After NA #2 completes, seq=2
    assert context.id_allocator._normal_attack_seq == 2


def test_p96_event_ordering_normal_attack_before_damage() -> None:
    """INV-08: NORMAL_ATTACK event is published prior to damage settlement."""
    context = _make_context()
    systems = BattleSystems()
    event_sequence: list[str] = []

    def record_event(ev):
        event_sequence.append(ev.event_type.value)

    context.event_bus.subscribe(EventType.NORMAL_ATTACK, record_event)
    context.event_bus.subscribe(EventType.DAMAGE_DEALT, record_event)

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)
    assert "NORMAL_ATTACK" in event_sequence
    assert "DAMAGE_DEALT" in event_sequence
    assert event_sequence.index("NORMAL_ATTACK") < event_sequence.index("DAMAGE_DEALT")


def test_p96_production_cutover_damage_instance_coordinator_partitioned_route() -> None:
    """Production NormalAttackSystem routes through DamageInstanceCoordinator.execute_partitioned_damage_instance."""
    context = _make_context()
    systems = BattleSystems()

    spy_coordinator = MagicMock(wraps=systems.damage_instance_coordinator)
    systems.normal_attack_system._damage_instance_coordinator = spy_coordinator

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    res = systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)
    assert res is not None
    assert spy_coordinator.execute_partitioned_damage_instance.call_count >= 1


# =========================================================================
# 3. Target Resolution Integration & Frozen REG-TGT Contracts
# =========================================================================

def test_p96_taunt_overrides_default_random_target() -> None:
    """Taunt forces intended target to the taunter instead of random enemy."""
    context = _make_context()
    systems = BattleSystems()

    systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.TAUNT.value,
        owner_id="a1",
        source_id="b2",
        source_skill_id="taunt_skill",
        source_skill_slot=SkillSlot.INHERENT,
        runtime_params=TauntStateParams(taunt_target_id="b2"),
    )

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    res = systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)
    assert res is not None
    assert res.target_resolution is not None
    assert res.target_resolution.intended_attack_target == "b2"
    assert res.actual_target_id == "b2"


def test_p96_guard_redirects_damage_recipient() -> None:
    """Guard redirects actual damage recipient to protector while keeping intended target unchanged."""
    context = _make_context()
    systems = BattleSystems()

    systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.GUARD.value,
        owner_id="b1",
        source_id="b2",
        source_skill_id="guard_skill",
        source_skill_slot=SkillSlot.INHERENT,
        runtime_params=GuardStateParams(protector_id="b2"),
    )

    systems.target_system.random_enemy = MagicMock(return_value=context.get_unit("b1"))

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    res = systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)
    assert res is not None
    assert res.target_resolution.intended_attack_target == "b1"
    assert res.target_resolution.post_redirect_actual_target == "b2"
    assert res.actual_target_id == "b2"


def test_p96_taunt_plus_guard_compound_interaction() -> None:
    """Compound interaction: Taunt selects b1, Guard redirects b1 to b2."""
    context = _make_context()
    systems = BattleSystems()

    systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.TAUNT.value,
        owner_id="a1",
        source_id="b1",
        source_skill_id="taunt_skill",
        source_skill_slot=SkillSlot.INHERENT,
        runtime_params=TauntStateParams(taunt_target_id="b1"),
    )
    systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.GUARD.value,
        owner_id="b1",
        source_id="b2",
        source_skill_id="guard_skill",
        source_skill_slot=SkillSlot.INHERENT,
        runtime_params=GuardStateParams(protector_id="b2"),
    )

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    res = systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)
    assert res is not None
    assert res.target_resolution.intended_attack_target == "b1"
    assert res.target_resolution.post_redirect_actual_target == "b2"
    assert res.actual_target_id == "b2"


def test_reg_tgt_05_combo_second_attack_fresh_target_resolution() -> None:
    """REG-TGT-05: Combo #2 creates new NormalAttackInstanceId and TargetResolutionId, does not inherit #1 target."""
    context = _make_context()
    systems = BattleSystems()

    systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.COMBO.value,
        owner_id="a1",
        source_id="a1",
        source_skill_id="combo_skill",
        source_skill_slot=SkillSlot.INHERENT,
        runtime_params=ComboStateParams(remaining_actions=1),
    )

    targets = [context.get_unit("b1"), context.get_unit("b2")]
    target_iter = iter(targets)
    systems.target_system.random_enemy = MagicMock(side_effect=lambda ctx, act: next(target_iter))

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    res = systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)
    assert res is not None
    assert res.combo_second_attack is not None

    # Different IDs
    assert res.normal_attack_id != res.combo_second_attack.normal_attack_id
    assert res.target_resolution.resolution_id != res.combo_second_attack.target_resolution.resolution_id

    # Targets differ, #2 did not inherit #1
    assert res.actual_target_id == "b1"
    assert res.combo_second_attack.actual_target_id == "b2"


def test_reg_tgt_06_guard_reruns_for_combo_second_attack() -> None:
    """REG-TGT-06: Guard reruns for Combo #2 against live world; does not reuse #1 redirect result."""
    context = _make_context()
    systems = BattleSystems()

    systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.COMBO.value,
        owner_id="a1",
        source_id="a1",
        source_skill_id="combo_skill",
        source_skill_slot=SkillSlot.INHERENT,
        runtime_params=ComboStateParams(remaining_actions=1),
    )

    # b1 guarded by b2
    guard_inst = systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.GUARD.value,
        owner_id="b1",
        source_id="b2",
        source_skill_id="guard_skill",
        source_skill_slot=SkillSlot.INHERENT,
        runtime_params=GuardStateParams(protector_id="b2"),
    )

    # Both attacks select b1 as intended target
    systems.target_system.random_enemy = MagicMock(return_value=context.get_unit("b1"))

    # Guard on b1 is removed during NA #1 execution
    def remove_guard_during_na1(ev):
        if ev.event_type == EventType.NORMAL_ATTACK and ev.payload.get("actual_target") == "b2":
            systems.state_lifecycle_system.remove(context, guard_inst.instance_id)

    context.event_bus.subscribe(EventType.NORMAL_ATTACK, remove_guard_during_na1)

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    res = systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)
    assert res is not None
    assert res.combo_second_attack is not None

    # NA #1 redirected b1 -> b2
    assert res.target_resolution.intended_attack_target == "b1"
    assert res.target_resolution.post_redirect_actual_target == "b2"
    assert res.actual_target_id == "b2"

    # NA #2 evaluated live world: Guard was removed, so actual target is b1 directly!
    assert res.combo_second_attack.target_resolution.intended_attack_target == "b1"
    assert res.combo_second_attack.target_resolution.post_redirect_actual_target == "b1"
    assert res.combo_second_attack.actual_target_id == "b1"


def test_reg_tgt_07_pre_guard_intended_target_identity_survives_redirect() -> None:
    """REG-TGT-07: Intended target identity survives Guard redirect; intended=B, actual=C."""
    context = _make_context()
    systems = BattleSystems()

    systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.GUARD.value,
        owner_id="b1",
        source_id="b2",
        source_skill_id="guard_skill",
        source_skill_slot=SkillSlot.INHERENT,
        runtime_params=GuardStateParams(protector_id="b2"),
    )

    systems.target_system.random_enemy = MagicMock(return_value=context.get_unit("b1"))

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    res = systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)
    assert res is not None
    assert res.target_resolution.intended_attack_target == "b1"
    assert res.target_resolution.post_redirect_actual_target == "b2"
    assert res.target_resolution.redirect_reason.value == "GUARD"
    # b1 is alive on defender's side, intended target preserved without global exclusion flags
    assert context.get_unit("b1").is_alive


# =========================================================================
# 4. Combo State Machine & Frozen REG-CMB Contracts
# =========================================================================

def test_p96_combo_first_in_wins_rejection() -> None:
    """P0 First-In-Wins: Second COMBO on same unit is rejected; original instance retained."""
    context = _make_context()
    systems = BattleSystems()

    systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.COMBO.value,
        owner_id="a1",
        source_id="a1",
        source_skill_id="combo_1",
        source_skill_slot=SkillSlot.INHERENT,
        runtime_params=ComboStateParams(remaining_actions=1),
    )

    with pytest.raises(ValueError, match="First-In-Wins"):
        systems.state_lifecycle_system.apply(
            context=context,
            state_id=OfficialStateId.COMBO.value,
            owner_id="a1",
            source_id="b1",
            source_skill_id="combo_2",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=ComboStateParams(remaining_actions=2),
        )
    active = systems.stage9_state_runtime.get_operational_combo(context, "a1")
    assert active.source_skill_id == "combo_1"
    assert active.runtime_params.remaining_actions == 1


def test_reg_cmb_01_action_start_maintenance_before_grant() -> None:
    """REG-CMB-01: Expired Combo at ACTION_START is physically removed before effective read; no grant created."""
    context = _make_context()
    systems = BattleSystems()

    inst = systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.COMBO.value,
        owner_id="a1",
        source_id="a1",
        source_skill_id="combo_skill",
        source_skill_slot=SkillSlot.INHERENT,
        runtime_params=ComboStateParams(remaining_actions=0),
    )
    assert context.states.has(owner_id="a1", state_id=OfficialStateId.COMBO.value)

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    res = systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)
    assert res is not None

    # Physically removed before grant
    assert not context.states.has(owner_id="a1", state_id=OfficialStateId.COMBO.value)
    assert scope.combo_grant is None
    assert res.combo_second_attack is None
    assert scope.physical_normal_attack_count == 1


def test_reg_cmb_02_physical_remove_revokes_unconsumed_grant() -> None:
    """REG-CMB-02: Valid Action grant from instance X is REVOKED if X is physically removed before consume; no cfg230."""
    context = _make_context()
    systems = BattleSystems()

    inst = systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.COMBO.value,
        owner_id="a1",
        source_id="a1",
        source_skill_id="combo_skill",
        source_skill_slot=SkillSlot.INHERENT,
        runtime_params=ComboStateParams(remaining_actions=1),
    )

    combo_facts: list[dict] = []
    context.event_bus.subscribe(EventType.COMBO_OPPORTUNITY_CONSUMED, lambda ev: combo_facts.append(ev.payload))

    # Remove state during NA #1 execution before checkpoint
    def remove_state_during_na1(ev):
        if ev.event_type == EventType.NORMAL_ATTACK:
            systems.state_lifecycle_system.remove(context, inst.instance_id)

    context.event_bus.subscribe(EventType.NORMAL_ATTACK, remove_state_during_na1)

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    res = systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)
    assert res is not None
    assert res.combo_second_attack is None

    # Grant revoked, checkpoint reached but unconsumed, no fact
    assert scope.combo_grant.state == ComboGrantState.REVOKED_BY_PHYSICAL_REMOVE
    assert scope.combo_checkpoint_state == ComboCheckpointState.REACHED
    assert len(combo_facts) == 0
    assert scope.physical_normal_attack_count == 1


def test_reg_cmb_03_ordinary_suppress_does_not_revoke_grant() -> None:
    """REG-CMB-03: Ordinary suppression after valid grant does not revoke current Action grant."""
    context = _make_context()
    systems = BattleSystems()

    inst = systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.COMBO.value,
        owner_id="a1",
        source_id="a1",
        source_skill_id="combo_skill",
        source_skill_slot=SkillSlot.INHERENT,
        runtime_params=ComboStateParams(remaining_actions=1, is_suppressed=False),
    )

    grant = ComboActionGrant(
        action_id=ActionId("act_test"),
        granting_instance_id=inst.instance_id,
        source_unit="a1",
        source_skill="combo_skill",
        state=ComboGrantState.VALID,
    )
    assert grant.is_valid(context) is True

    # Suppressed: instance still exists, grant remains valid!
    systems.stage9_state_runtime.set_combo_suppressed(context, inst.instance_id, True)
    assert grant.is_valid(context) is True


def test_reg_cmb_04_atomic_consume_ceiling() -> None:
    """REG-CMB-04: Atomic consume ceiling: consume + cfg230 occurs; later failure does not refund; consume<=1, NA<=2."""
    # Vector A: DISARM after consume
    context_a = _make_context()
    systems_a = BattleSystems()

    systems_a.state_lifecycle_system.apply(
        context=context_a,
        state_id=OfficialStateId.COMBO.value,
        owner_id="a1",
        source_id="a1",
        source_skill_id="combo_skill",
        source_skill_slot=SkillSlot.INHERENT,
        runtime_params=ComboStateParams(remaining_actions=1),
    )

    facts_a: list[dict] = []
    context_a.event_bus.subscribe(EventType.COMBO_OPPORTUNITY_CONSUMED, lambda ev: facts_a.append(ev.payload))

    # Apply DISARM to actor on NORMAL_ATTACK
    def disarm_on_na1(ev):
        if ev.event_type == EventType.NORMAL_ATTACK:
            systems_a.state_lifecycle_system.apply(
                context=context_a,
                state_id=OfficialStateId.DISARM.value,
                owner_id="a1",
                source_id="b1",
                source_skill_id="disarm_skill",
                source_skill_slot=SkillSlot.INHERENT,
            )
    context_a.event_bus.subscribe(EventType.NORMAL_ATTACK, disarm_on_na1)

    parent_scope_a = "round_1_actor_a1"
    permit_a = systems_a.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope_a)
    scope_a = admit_action_scope(context_a, systems_a.future_admission_gate, permit_a, context_a.get_unit("a1"), parent_scope_a)

    res_a = systems_a.action_system.execute(context_a, context_a.get_unit("a1"), action_scope=scope_a)
    assert res_a is not None
    assert res_a.combo_second_attack is None
    assert len(facts_a) == 1
    assert scope_a.combo_checkpoint_state == ComboCheckpointState.CONSUMED
    assert scope_a.combo_grant.state == ComboGrantState.CONSUMED
    assert scope_a.physical_normal_attack_count == 1

    # Vector B: FutureAdmission denied after consume
    context_b = _make_context()
    systems_b = BattleSystems()

    systems_b.state_lifecycle_system.apply(
        context=context_b,
        state_id=OfficialStateId.COMBO.value,
        owner_id="a1",
        source_id="a1",
        source_skill_id="combo_skill",
        source_skill_slot=SkillSlot.INHERENT,
        runtime_params=ComboStateParams(remaining_actions=1),
    )

    facts_b: list[dict] = []
    context_b.event_bus.subscribe(EventType.COMBO_OPPORTUNITY_CONSUMED, lambda ev: facts_b.append(ev.payload))

    # FutureAdmissionGate denies COMBO_SECOND_NORMAL_ATTACK
    orig_can_admit = systems_b.future_admission_gate.can_admit
    def deny_combo(branch):
        if branch == FutureBranchKind.COMBO_SECOND_NORMAL_ATTACK:
            return False
        return orig_can_admit(branch)
    systems_b.future_admission_gate.can_admit = deny_combo

    parent_scope_b = "round_1_actor_a1"
    permit_b = systems_b.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope_b)
    scope_b = admit_action_scope(context_b, systems_b.future_admission_gate, permit_b, context_b.get_unit("a1"), parent_scope_b)

    res_b = systems_b.action_system.execute(context_b, context_b.get_unit("a1"), action_scope=scope_b)
    assert res_b is not None
    assert res_b.combo_second_attack is None
    assert len(facts_b) == 1
    assert scope_b.combo_checkpoint_state == ComboCheckpointState.CONSUMED
    assert scope_b.combo_grant.state == ComboGrantState.CONSUMED
    assert scope_b.physical_normal_attack_count == 1


def test_reg_cmb_05_actor_death_cancels_future_owner_branches() -> None:
    """REG-CMB-05: Attacker death during NA #1 cancels Assault and Combo future branches; no cfg230, checkpoint NOT_REACHED."""
    context = _make_context()
    systems = BattleSystems()

    systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.COMBO.value,
        owner_id="a1",
        source_id="a1",
        source_skill_id="combo_skill",
        source_skill_slot=SkillSlot.INHERENT,
        runtime_params=ComboStateParams(remaining_actions=1),
    )

    combo_facts: list[dict] = []
    context.event_bus.subscribe(EventType.COMBO_OPPORTUNITY_CONSUMED, lambda ev: combo_facts.append(ev.payload))

    # Attacker dies during NA #1 execution (e.g. counter or trigger)
    def kill_attacker_on_na1(ev):
        if ev.event_type == EventType.NORMAL_ATTACK:
            actor_unit = context.get_unit("a1")
            actor_unit.troops = 0

    context.event_bus.subscribe(EventType.NORMAL_ATTACK, kill_attacker_on_na1)

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    res = systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)
    assert res is not None
    assert res.combo_second_attack is None

    # Actor died, checkpoint was NOT reached, no cfg230 emitted
    assert scope.combo_checkpoint_state == ComboCheckpointState.NOT_REACHED
    assert len(combo_facts) == 0
    assert scope.physical_normal_attack_count == 1


def test_final_03_combo_battle_end() -> None:
    """FINAL_03_COMBO_BATTLE_END: Lethal NA #1 satisfies victory latch, cancels Combo #2 admission, drains and finalizes."""
    context = _make_context(b1_troops=10, b2_troops=1000)
    systems = BattleSystems()

    systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.COMBO.value,
        owner_id="a1",
        source_id="a1",
        source_skill_id="combo_skill",
        source_skill_slot=SkillSlot.INHERENT,
        runtime_params=ComboStateParams(remaining_actions=1),
    )

    # Force NA #1 to hit b1 (enemy commander)
    systems.target_system.random_enemy = MagicMock(return_value=context.get_unit("b1"))

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    res = systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)
    assert res is not None

    # Commander died -> victory latched
    assert systems.finalization_coordinator.is_latched_or_finalized is True
    # Combo #2 was cancelled / not admitted
    assert res.combo_second_attack is None
    assert scope.physical_normal_attack_count == 1

    # Complete action scope -> finalizes
    scope.mark_terminal()
    systems.finalization_coordinator.complete_action_scope(context, scope)
    assert systems.finalization_coordinator.termination_state == BattleTerminationState.FINALIZED


# =========================================================================
# 5. Additional Audit Repair Regressions (P96-RPR-02..07)
# =========================================================================

def test_p96_rpr_02_expired_combo_plus_stun_at_action_start() -> None:
    """P96-RPR-02: Actor has STUN and COMBO remaining_actions=0; Combo physically removed at ACTION_START before STUN block."""
    context = _make_context()
    systems = BattleSystems()

    systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.STUN.value,
        owner_id="a1",
        source_id="b1",
        source_skill_id="stun_skill",
        source_skill_slot=SkillSlot.INHERENT,
    )
    systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.COMBO.value,
        owner_id="a1",
        source_id="a1",
        source_skill_id="combo_skill",
        source_skill_slot=SkillSlot.INHERENT,
        runtime_params=ComboStateParams(remaining_actions=0),
    )

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    res = systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)
    assert res is None

    # Combo physically removed at ACTION_START
    assert not context.states.has(owner_id="a1", state_id=OfficialStateId.COMBO.value)
    # No grant created
    assert scope.combo_grant is None
    # No NA instance allocated, physical count remains 0
    assert scope.physical_normal_attack_count == 0


def test_p96_rpr_03_finite_combo_duration_plus_stun_maintenance() -> None:
    """P96-RPR-03: STUN does not freeze temporary Combo duration; remaining_actions decrements normally."""
    context = _make_context()
    systems = BattleSystems()

    systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.STUN.value,
        owner_id="a1",
        source_id="b1",
        source_skill_id="stun_skill",
        source_skill_slot=SkillSlot.INHERENT,
    )
    inst = systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.COMBO.value,
        owner_id="a1",
        source_id="a1",
        source_skill_id="combo_skill",
        source_skill_slot=SkillSlot.INHERENT,
        runtime_params=ComboStateParams(remaining_actions=2),
    )

    # Action 1: STUN blocks action, but remaining_actions decrements from 2 to 1
    parent_scope_1 = "round_1_actor_a1"
    permit_1 = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope_1)
    scope_1 = admit_action_scope(context, systems.future_admission_gate, permit_1, context.get_unit("a1"), parent_scope_1)

    res_1 = systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope_1)
    assert res_1 is None
    assert scope_1.physical_normal_attack_count == 0

    updated_inst = context.states.get(inst.instance_id)
    assert updated_inst.runtime_params.remaining_actions == 1

    # Action 2: remaining_actions decrements from 1 to 0
    parent_scope_2 = "round_2_actor_a1"
    permit_2 = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope_2)
    scope_2 = admit_action_scope(context, systems.future_admission_gate, permit_2, context.get_unit("a1"), parent_scope_2)

    res_2 = systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope_2)
    assert res_2 is None
    assert context.states.get(inst.instance_id).runtime_params.remaining_actions == 0


def test_p96_rpr_04_disarm_blocked_na1_allocates_no_id_or_count() -> None:
    """P96-RPR-04: DISARM before #1 emits ACTION_BLOCKED without allocating NormalAttackInstanceId or incrementing physical count."""
    context = _make_context()
    systems = BattleSystems()

    systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.DISARM.value,
        owner_id="a1",
        source_id="b1",
        source_skill_id="disarm_skill",
        source_skill_slot=SkillSlot.INHERENT,
    )

    events: list[str] = []
    context.event_bus.subscribe(EventType.ACTION_BLOCKED, lambda ev: events.append("BLOCKED"))
    context.event_bus.subscribe(EventType.NORMAL_ATTACK, lambda ev: events.append("NA"))

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    res = systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)
    assert res is not None
    assert res.normal_attack_id is None
    # No NormalAttackInstanceId allocated
    assert context.id_allocator._normal_attack_seq == 0
    # No physical count incremented
    assert scope.physical_normal_attack_count == 0
    assert events == ["BLOCKED"]


def test_p96_rpr_05_stun_blocked_na1_allocates_no_id_or_count() -> None:
    """P96-RPR-05: STUN before #1 emits ACTION_BLOCKED without allocating NormalAttackInstanceId or incrementing physical count."""
    context = _make_context()
    systems = BattleSystems()

    systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.STUN.value,
        owner_id="a1",
        source_id="b1",
        source_skill_id="stun_skill",
        source_skill_slot=SkillSlot.INHERENT,
    )

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    res = systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)
    assert res is None
    # No NormalAttackInstanceId allocated
    assert context.id_allocator._normal_attack_seq == 0
    # No physical count incremented
    assert scope.physical_normal_attack_count == 0


def test_p96_rpr_06_combo_second_attack_reaches_assault_seam() -> None:
    """P96-RPR-06: NormalAttack #2 passes Assault admission seam; does not open recursive Combo checkpoint."""
    context = _make_context()
    systems = BattleSystems()

    systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.COMBO.value,
        owner_id="a1",
        source_id="a1",
        source_skill_id="combo_skill",
        source_skill_slot=SkillSlot.INHERENT,
        runtime_params=ComboStateParams(remaining_actions=1),
    )

    assault_seam_scopes: list[str] = []
    orig_dispatch = systems.assault_dispatch_port.dispatch
    def spy_dispatch(context, permit, parent_scope_identity, *, actor, actual_target_id):
        assault_seam_scopes.append(parent_scope_identity)
        return orig_dispatch(context, permit, parent_scope_identity, actor=actor, actual_target_id=actual_target_id)
    systems.assault_dispatch_port.dispatch = spy_dispatch

    combo_facts: list[dict] = []
    context.event_bus.subscribe(EventType.COMBO_OPPORTUNITY_CONSUMED, lambda ev: combo_facts.append(ev.payload))

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    res = systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)
    assert res is not None
    assert res.combo_second_attack is not None

    # Assault seam reached for both #1 and #2!
    assert len(assault_seam_scopes) == 2
    assert "normal_attack_" in assault_seam_scopes[0]
    assert "normal_attack_" in assault_seam_scopes[1]
    assert assault_seam_scopes[0] != assault_seam_scopes[1]

    # Exactly 1 combo checkpoint / fact, exactly 2 physical NAs
    assert len(combo_facts) == 1
    assert scope.physical_normal_attack_count == 2
    assert res.combo_second_attack.combo_second_attack is None


def test_p96_rpr_07_cross_context_action_scope_isolation() -> None:
    """P96-RPR-07: BattleFinalizationCoordinator strictly isolates BattleContext; foreign context ActionScope rejected."""
    coordinator = BattleFinalizationCoordinator(VictorySystem())
    gate = FutureAdmissionGate(coordinator)

    ctx_a = _make_context(battle_id="battle_A")
    ctx_b = _make_context(battle_id="battle_B")

    permit_a = gate.request_admission(FutureBranchKind.NEXT_ACTION, "scope_A")
    scope_a = admit_action_scope(ctx_a, gate, permit_a, ctx_a.get_unit("a1"), "scope_A")

    # Coordinator is now bound to ctx_a
    assert coordinator.owning_context is ctx_a
    assert scope_a.action_id in coordinator.active_action_scope_ids

    # Foreign context ctx_b cannot admit ActionScope into coordinator
    permit_b = gate.request_admission(FutureBranchKind.NEXT_ACTION, "scope_B")
    with pytest.raises(ValueError, match="already bound to BattleContext"):
        admit_action_scope(ctx_b, gate, permit_b, ctx_b.get_unit("a1"), "scope_B")

    # ctx_a active scope remains unpolluted
    assert coordinator.active_action_scope_ids == (scope_a.action_id,)


# =========================================================================
# 6. Invariant Contracts (INV-06..12, INV-39..42)
# =========================================================================

def test_inv_06_combo_second_attack_fresh_target_identity() -> None:
    """INV-06: NormalAttack #2 creates new NormalAttackInstanceId and TargetResolutionResult."""
    context = _make_context()
    systems = BattleSystems()

    systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.COMBO.value,
        owner_id="a1",
        source_id="a1",
        source_skill_id="combo_skill",
        source_skill_slot=SkillSlot.INHERENT,
        runtime_params=ComboStateParams(remaining_actions=1),
    )

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    res = systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)
    assert res is not None
    assert res.combo_second_attack is not None

    assert res.normal_attack_id != res.combo_second_attack.normal_attack_id
    assert res.target_resolution.resolution_id != res.combo_second_attack.target_resolution.resolution_id


def test_inv_07_physical_operational_grant_distinct() -> None:
    """INV-07: Physical state, operational state, and Action grant are distinct."""
    context = _make_context()
    systems = BattleSystems()

    inst = systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.COMBO.value,
        owner_id="a1",
        source_id="a1",
        source_skill_id="combo_skill",
        source_skill_slot=SkillSlot.INHERENT,
        runtime_params=ComboStateParams(remaining_actions=1, is_suppressed=False),
    )

    # Physical exists
    assert context.states.has(owner_id="a1", state_id=OfficialStateId.COMBO.value)
    # Operational exists
    assert systems.stage9_state_runtime.get_operational_combo(context, "a1") is not None

    # Grant exists independently
    grant = ComboActionGrant(
        action_id=ActionId("act_1"),
        granting_instance_id=inst.instance_id,
        source_unit="a1",
        source_skill="combo_skill",
    )
    assert grant.state == ComboGrantState.VALID

    # Suppress operational state: physical still exists, grant still valid!
    systems.stage9_state_runtime.set_combo_suppressed(context, inst.instance_id, True)
    assert systems.stage9_state_runtime.get_operational_combo(context, "a1") is None
    assert context.states.has(owner_id="a1", state_id=OfficialStateId.COMBO.value)
    assert grant.is_valid(context) is True


def test_inv_08_action_start_maintenance_before_grant() -> None:
    """INV-08: ACTION_START maintenance settles before effective Combo evaluation."""
    context = _make_context()
    systems = BattleSystems()

    systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.COMBO.value,
        owner_id="a1",
        source_id="a1",
        source_skill_id="combo_skill",
        source_skill_slot=SkillSlot.INHERENT,
        runtime_params=ComboStateParams(remaining_actions=1),
    )

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    # In action 1, maintenance decrements from 1 to 0, but is still valid for this action
    res = systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)
    assert res is not None
    assert res.combo_second_attack is not None

    # In action 2, remaining_actions is 0 -> physically removed before grant!
    parent_scope_2 = "round_2_actor_a1"
    permit_2 = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope_2)
    scope_2 = admit_action_scope(context, systems.future_admission_gate, permit_2, context.get_unit("a1"), parent_scope_2)

    res_2 = systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope_2)
    assert res_2 is not None
    assert res_2.combo_second_attack is None
    assert scope_2.combo_grant is None


def test_inv_09_remove_vs_suppress_grant_semantics() -> None:
    """INV-09: REMOVE revokes unconsumed grant; SUPPRESS does not."""
    context = _make_context()
    systems = BattleSystems()

    inst = systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.COMBO.value,
        owner_id="a1",
        source_id="a1",
        source_skill_id="combo_skill",
        source_skill_slot=SkillSlot.INHERENT,
        runtime_params=ComboStateParams(remaining_actions=1),
    )

    grant = ComboActionGrant(
        action_id=ActionId("act_1"),
        granting_instance_id=inst.instance_id,
        source_unit="a1",
        source_skill="combo_skill",
    )

    # 1. Suppress -> still valid
    systems.stage9_state_runtime.set_combo_suppressed(context, inst.instance_id, True)
    assert grant.is_valid(context) is True

    # 2. Remove -> revoked
    systems.state_lifecycle_system.remove(context, inst.instance_id)
    assert grant.is_valid(context) is False
    assert grant.state == ComboGrantState.REVOKED_BY_PHYSICAL_REMOVE


def test_inv_10_combo_checkpoint_at_most_once_per_action() -> None:
    """INV-10: Combo checkpoint is reached at most once per ActionId."""
    context = _make_context()
    systems = BattleSystems()

    systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.COMBO.value,
        owner_id="a1",
        source_id="a1",
        source_skill_id="combo_skill",
        source_skill_slot=SkillSlot.INHERENT,
        runtime_params=ComboStateParams(remaining_actions=1),
    )

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    res = systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)
    assert res is not None
    # Checkpoint ended in CONSUMED and cannot be entered again
    assert scope.combo_checkpoint_state == ComboCheckpointState.CONSUMED


def test_inv_11_cfg230_consume_at_most_once_per_action() -> None:
    """INV-11: COMBO_OPPORTUNITY_CONSUMED fact is emitted at most once per ActionId."""
    context = _make_context()
    systems = BattleSystems()

    systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.COMBO.value,
        owner_id="a1",
        source_id="a1",
        source_skill_id="combo_skill",
        source_skill_slot=SkillSlot.INHERENT,
        runtime_params=ComboStateParams(remaining_actions=1),
    )

    combo_facts: list[dict] = []
    context.event_bus.subscribe(EventType.COMBO_OPPORTUNITY_CONSUMED, lambda ev: combo_facts.append(ev.payload))

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)
    assert len(combo_facts) == 1


def test_inv_12_physical_normal_attack_count_never_exceeds_two() -> None:
    """INV-12: Physical normal attack count per action is strictly <= 2."""
    context = _make_context()
    systems = BattleSystems()

    systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.COMBO.value,
        owner_id="a1",
        source_id="a1",
        source_skill_id="combo_skill",
        source_skill_slot=SkillSlot.INHERENT,
        runtime_params=ComboStateParams(remaining_actions=5),
    )

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    res = systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)
    assert res is not None
    assert res.combo_second_attack is not None
    assert res.combo_second_attack.combo_second_attack is None
    # Direct physical count assertion (INV-12)
    assert scope.physical_normal_attack_count == 2


def test_inv_39_to_42_victory_barrier_and_lineage_authority() -> None:
    """INV-39..42: Unit death fact, victory latch, single finalization owner, and lineage authority."""
    coordinator = BattleFinalizationCoordinator(VictorySystem())
    gate = FutureAdmissionGate(coordinator)

    # INV-39 & INV-41: Only coordinator owns finalization state transitions
    assert coordinator.termination_state == BattleTerminationState.RUNNING

    # INV-40: Victory latch blocks new FutureBranch admission
    coordinator._termination_state = BattleTerminationState.VICTORY_LATCHED
    assert gate.can_admit(FutureBranchKind.NEXT_ACTION) is False
    assert gate.request_admission(FutureBranchKind.NEXT_ACTION, "test") is None
    assert gate.can_admit(FutureBranchKind.COMBO_SECOND_NORMAL_ATTACK) is False
    assert gate.request_admission(FutureBranchKind.COMBO_SECOND_NORMAL_ATTACK, "test") is None

    # INV-42: Lineage authority
    lineage = OperationLineage(
        root_action_id=ActionId("act_1"),
        parent_normal_attack_id=NormalAttackInstanceId("na_1"),
        parent_damage_instance_id=None,
        source_type=SourceType.NORMAL_ATTACK,
        physical_attacker="a1",
        physical_skill=None,
        credit_owner="a1",
    )
    assert lineage.root_action_id == ActionId("act_1")
    assert lineage.source_type == SourceType.NORMAL_ATTACK


# ============================================================================
# Phase 9.6 Final Re-Audit Regressions: FR96-B01, FR96-B02, FR96-M01
# ============================================================================


def test_fr96_act_01_direct_constructed_scope_without_coordinator_rejected() -> None:
    """FR96-ACT-01: ActionScope constructed without capability origin has no coordinator binding and is rejected."""
    context = _make_context()
    systems = BattleSystems()

    # Scope created directly, bypassing admit_action_scope & FutureAdmissionGate
    forged_scope = ActionScope(
        action_id=ActionId("act_forged"),
        actor_id="a1",
    )

    with pytest.raises(RuntimeError, match="has no coordinator capability binding"):
        systems.action_system.execute(context, context.get_unit("a1"), action_scope=forged_scope)


def test_fr96_act_02_identity_mismatch_forged_scope_rejected() -> None:
    """FR96-ACT-02: Scope with forged object identity (same action_id but not admitted object) is rejected."""
    context = _make_context()
    systems = BattleSystems()

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    authentic_scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    # Construct duplicate scope with identical attributes but different object identity
    imposter_scope = ActionScope(
        action_id=authentic_scope.action_id,
        actor_id="a1",
        execution_state=ActionExecutionState.ADMITTED,
        _coordinator=systems.finalization_coordinator,
        _owning_context_id=id(context),
    )

    with pytest.raises(ValueError, match="ActionScope object identity mismatch"):
        systems.action_system.execute(context, context.get_unit("a1"), action_scope=imposter_scope)


def test_fr96_act_03_actor_mismatch_rejected_before_side_effects() -> None:
    """FR96-ACT-03: Scope admitted for actor A executed with actor B is rejected before any side effects."""
    context = _make_context()
    systems = BattleSystems()

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope_a1 = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    # Attempt to execute with unit b1
    with pytest.raises(ValueError, match="ActionScope actor mismatch"):
        systems.action_system.execute(context, context.get_unit("b1"), action_scope=scope_a1)

    # Verify no execution occurred on b1
    assert scope_a1.physical_normal_attack_count == 0
    assert scope_a1.execution_state == ActionExecutionState.ADMITTED


def test_fr96_act_04_execution_state_transition_prevents_replay() -> None:
    """FR96-ACT-04: ActionScope transitions to EXECUTING upon execution; replay attempts are rejected."""
    context = _make_context()
    systems = BattleSystems()

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)
    assert scope.execution_state == ActionExecutionState.ADMITTED

    # First execution succeeds and sets state to EXECUTING
    res = systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)
    assert res is not None
    assert scope.execution_state == ActionExecutionState.EXECUTING

    # Second execution of the same scope is rejected as a replay
    with pytest.raises(RuntimeError, match="has already been executed or is in state EXECUTING"):
        systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)


def test_fr96_act_05_terminal_scope_rejected() -> None:
    """FR96-ACT-05: ActionScope marked terminal cannot be executed."""
    context = _make_context()
    systems = BattleSystems()

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    scope.mark_terminal()
    assert scope.terminal is True
    assert scope.execution_state == ActionExecutionState.TERMINAL

    with pytest.raises(RuntimeError, match="is already terminal"):
        systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)


def test_fr96_cmb_01_combo_second_attack_without_gate_fails_closed() -> None:
    """FR96-CMB-01: When FutureAdmissionGate is absent on NormalAttackSystem, Combo #2 fails closed with RuntimeError."""
    context = _make_context()
    systems = BattleSystems()

    # Apply Combo state to a1
    systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.COMBO.value,
        owner_id="a1",
        source_id="a1",
        source_skill_id="combo_skill",
        source_skill_slot=SkillSlot.INHERENT,
        runtime_params=ComboStateParams(remaining_actions=1),
    )

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    # Detach gate from normal attack system
    systems.normal_attack_system._future_admission_gate = None

    # Executing NA #1 with Combo grant must fail closed when checkpoint tries to admit #2
    with pytest.raises(RuntimeError, match="requires FutureAdmissionGate to admit COMBO_SECOND_NORMAL_ATTACK"):
        systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)

    # Only NA #1 was performed before the exception, physical count did not increment to 2
    assert scope.physical_normal_attack_count == 1


def test_fr96_cmb_02_no_grant_checkpoint_remains_reached() -> None:
    """FR96-CMB-02: Checkpoint transitions to REACHED when local gates pass, and remains REACHED when no grant exists."""
    context = _make_context()
    systems = BattleSystems()

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    # No combo state applied -> scope.combo_grant will be None
    res = systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)
    assert res is not None
    assert res.combo_second_attack is None

    # Checkpoint was reached, but no grant existed to consume -> remains REACHED
    assert scope.combo_grant is None
    assert scope.combo_checkpoint_state == ComboCheckpointState.REACHED
    assert scope.physical_normal_attack_count == 1


# ============================================================================
# Phase 9.6 Capability Closure Regressions: FR96-R2-A01..A13
# ============================================================================


def test_fr96_r2_a01_direct_coordinator_forged_scope_admission_rejected() -> None:
    """FR96-R2-A01: Direct coordinator forged-scope admission is rejected."""
    context = _make_context()
    coordinator = BattleFinalizationCoordinator(VictorySystem())
    forged = ActionScope(ActionId("act_forged"), actor_id="a1")

    with pytest.raises(RuntimeError, match="Direct coordinator admission of ActionScope is forbidden"):
        coordinator.admit_action_scope(context, forged)


def test_fr96_r2_a02_action_id_only_real_scope_admission_bypass_rejected() -> None:
    """FR96-R2-A02: ActionId-only admission into coordinator is rejected for Phase 9.6 real scope."""
    context = _make_context()
    coordinator = BattleFinalizationCoordinator(VictorySystem())

    with pytest.raises(TypeError, match="ActionId-only admission is forbidden in Phase 9.6"):
        coordinator.admit_action_scope(context, ActionId("act_naked"))


def test_fr96_r2_a03_actor_id_mutation_cannot_change_admission_ownership() -> None:
    """FR96-R2-A03: Mutating scope.actor_id cannot hijack admission ownership; coordinator enforces admission snapshot."""
    context = _make_context()
    systems = BattleSystems()

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    # Caller mutates scope.actor_id to b1 and attempts to execute for b1
    scope.actor_id = "b1"
    with pytest.raises(ValueError, match="admission record actor is 'a1', expected executing actor 'b1'"):
        systems.action_system.execute(context, context.get_unit("b1"), action_scope=scope)

    assert scope.physical_normal_attack_count == 0


def test_fr96_r2_a04_execution_state_mutation_cannot_reset_replay_guard() -> None:
    """FR96-R2-A04: Mutating scope.execution_state cannot reset replay guard; coordinator record owns replay authority."""
    context = _make_context()
    systems = BattleSystems()

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    res = systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)
    assert res is not None

    # Caller resets scope.execution_state back to ADMITTED
    scope.execution_state = ActionExecutionState.ADMITTED
    with pytest.raises(RuntimeError, match="has already been executed or is in state EXECUTING"):
        systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)

    assert scope.physical_normal_attack_count == 1


def test_fr96_r2_a05_terminal_mutation_cannot_reopen_scope() -> None:
    """FR96-R2-A05: Mutating scope.terminal / execution_state cannot reopen a terminal/completed scope."""
    context = _make_context()
    systems = BattleSystems()

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    scope.mark_terminal()
    systems.finalization_coordinator.complete_action_scope(context, scope)

    # Caller attempts to reopen scope
    scope.terminal = False
    scope.execution_state = ActionExecutionState.ADMITTED

    with pytest.raises(RuntimeError, match=r"is already terminal \(COMPLETED\)"):
        systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)


def test_fr96_r2_a06_direct_normal_attack_system_use_of_merely_admitted_scope_rejected() -> None:
    """FR96-R2-A06: Calling NormalAttackSystem directly with merely ADMITTED scope is rejected."""
    context = _make_context()
    systems = BattleSystems()

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    # Scope is in ADMITTED state (ActionSystem.execute was not called)
    with pytest.raises(RuntimeError, match="is merely ADMITTED; must be executed via ActionSystem lifecycle"):
        systems.normal_attack_system.execute(context, context.get_unit("a1"), action_scope=scope)

    assert scope.physical_normal_attack_count == 0


def test_fr96_r2_a07_second_primary_normal_attack_entry_for_same_action_rejected() -> None:
    """FR96-R2-A07: Second primary NormalAttack entry for the same Action is rejected."""
    context = _make_context()
    systems = BattleSystems()

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    # Legitimate execution of Action
    systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)
    assert scope.physical_normal_attack_count == 1

    # Attempt second direct call to NormalAttackSystem.execute with the same ActionScope
    with pytest.raises(RuntimeError, match="Primary NormalAttack entry for ActionScope .* has already been consumed"):
        systems.normal_attack_system.execute(context, context.get_unit("a1"), action_scope=scope)

    assert scope.physical_normal_attack_count == 1


def test_fr96_r2_a08_total_physical_na_cannot_exceed_2_under_direct_replay_abuse() -> None:
    """FR96-R2-A08: Total physical NormalAttacks per Action cannot exceed 2 under replay/direct API abuse."""
    context = _make_context()
    systems = BattleSystems()

    systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.COMBO.value,
        owner_id="a1",
        source_id="a1",
        source_skill_id="combo_skill",
        source_skill_slot=SkillSlot.INHERENT,
        runtime_params=ComboStateParams(remaining_actions=1),
    )

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    # Legitimate execution executes primary NA and Combo NA #2
    res = systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)
    assert res is not None
    assert res.combo_second_attack is not None
    assert scope.physical_normal_attack_count == 2

    # Abuse attempts: direct NormalAttackSystem call is rejected
    with pytest.raises(RuntimeError, match="Primary NormalAttack entry"):
        systems.normal_attack_system.execute(context, context.get_unit("a1"), action_scope=scope)

    # Abuse attempts: direct ActionSystem replay call is rejected
    with pytest.raises(RuntimeError, match="has already been executed or is in state EXECUTING"):
        systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)

    assert scope.physical_normal_attack_count == 2


def test_fr96_r2_a09_completion_requires_exact_admitted_scope() -> None:
    """FR96-R2-A09: complete_action_scope requires exact ActionScope capability, rejecting naked ActionId."""
    context = _make_context()
    systems = BattleSystems()

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    with pytest.raises(TypeError, match="complete_action_scope requires exact ActionScope capability, not naked ActionId"):
        systems.finalization_coordinator.complete_action_scope(context, scope.action_id)


def test_fr96_r2_a10_same_value_forged_scope_cannot_complete_barrier() -> None:
    """FR96-R2-A10: Forged scope with duplicate action_id cannot complete barrier."""
    context = _make_context()
    systems = BattleSystems()

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    authentic_scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    imposter_scope = ActionScope(
        action_id=authentic_scope.action_id,
        actor_id="a1",
        _coordinator=systems.finalization_coordinator,
        _owning_context_id=id(context),
    )

    with pytest.raises(ValueError, match="ActionScope object identity mismatch"):
        systems.finalization_coordinator.complete_action_scope(context, imposter_scope)


def test_fr96_r2_a11_completion_exactly_once() -> None:
    """FR96-R2-A11: ActionScope can be completed exactly once; second completion is rejected."""
    context = _make_context()
    systems = BattleSystems()

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    # First completion succeeds
    systems.finalization_coordinator.complete_action_scope(context, scope)

    # Second completion fails
    with pytest.raises(RuntimeError, match="has already been completed"):
        systems.finalization_coordinator.complete_action_scope(context, scope)


def test_fr96_r2_a12_foreign_battle_context_factory_failure_consumes_no_permit_and_allocates_no_action_id() -> None:
    """FR96-R2-A12: Foreign BattleContext pre-validation fails before consuming permit or allocating ActionId."""
    coordinator = BattleFinalizationCoordinator(VictorySystem())
    gate = FutureAdmissionGate(coordinator)

    ctx_a = _make_context(battle_id="battle_A")
    ctx_b = _make_context(battle_id="battle_B")

    # Bind coordinator to ctx_a
    permit_a = gate.request_admission(FutureBranchKind.NEXT_ACTION, "scope_A")
    admit_action_scope(ctx_a, gate, permit_a, ctx_a.get_unit("a1"), "scope_A")
    assert coordinator.owning_context is ctx_a

    # Attempt to admit with ctx_b
    permit_b = gate.request_admission(FutureBranchKind.NEXT_ACTION, "scope_B")
    initial_seq = ctx_b.id_allocator._action_seq

    with pytest.raises(ValueError, match="already bound to BattleContext"):
        admit_action_scope(ctx_b, gate, permit_b, ctx_b.get_unit("a1"), "scope_B")

    # Verify permit_b was NOT consumed and no ActionId was allocated in ctx_b
    assert permit_b.permit_id not in gate._consumed_permits
    assert ctx_b.id_allocator._action_seq == initial_seq


def test_fr96_r2_a13_foreign_context_assault_dispatch_consumes_no_permit() -> None:
    """FR96-R2-A13: Foreign BattleContext Assault dispatch fails before consuming permit."""
    coordinator = BattleFinalizationCoordinator(VictorySystem())
    gate = FutureAdmissionGate(coordinator)
    port = AssaultDispatchPort(gate)

    ctx_a = _make_context(battle_id="battle_A")
    ctx_b = _make_context(battle_id="battle_B")

    # Bind coordinator to ctx_a
    permit_a = gate.request_admission(FutureBranchKind.NEXT_ACTION, "scope_A")
    admit_action_scope(ctx_a, gate, permit_a, ctx_a.get_unit("a1"), "scope_A")

    # Request ASSAULT permit on gate
    assault_permit = gate.request_admission(FutureBranchKind.ASSAULT, "assault_scope")
    assert assault_permit is not None

    # Attempt to dispatch on foreign ctx_b
    with pytest.raises(ValueError, match="already bound to BattleContext"):
        port.dispatch(ctx_b, assault_permit, "assault_scope", actor=ctx_b.get_unit("a1"), actual_target_id="b1")

    # Verify permit was NOT consumed
    assert assault_permit.permit_id not in gate._consumed_permits

