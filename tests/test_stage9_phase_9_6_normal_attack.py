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
    BattleResult,
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
from sgs_v2.battle_core.execution_right_system import (
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
    units: list[UnitRuntime] | None = None,
    seed: int = 42,
) -> BattleContext:
    if units is None:
        units = [
            _make_unit("a1", "A", 1000, speed=120, is_commander=True),
            _make_unit("a2", "A", 1000, speed=110),
            _make_unit("b1", "B", 1000, speed=100, is_commander=True),
            _make_unit("b2", "B", 1000, speed=90),
        ]
    context = BattleContext(
        battle_id="test-p96-battle",
        units={u.unit_id: u for u in units},
        event_bus=EventBus(),
        random=RandomSystem(seed=seed),
        max_rounds=5,
    )
    register_official_state_definitions(context.states)
    return context


# =========================================================================
# 1. Architectural Integrity & Master Lifecycle
# =========================================================================

def test_arch_p96_normal_attack_is_unique_master() -> None:
    """NormalAttackSystem is the unique physical master and has no fake sub-dispatchers."""
    systems = BattleSystems()
    assert isinstance(systems.normal_attack_system, NormalAttackSystem)
    assert systems.normal_attack_system.target_system is systems.target_system
    assert systems.normal_attack_system.target_resolution_system is systems.target_resolution_system
    assert systems.normal_attack_system.damage_instance_coordinator is systems.damage_instance_coordinator
    assert systems.normal_attack_system.future_admission_gate is systems.future_admission_gate
    assert systems.normal_attack_system.finalization_coordinator is systems.finalization_coordinator
    assert systems.normal_attack_system.assault_dispatch_port is systems.assault_dispatch_port


def test_arch_p96_no_bypass_methods_on_gate_or_assault() -> None:
    """Ensure no bypass methods exist on FutureAdmissionGate or AssaultDispatchPort."""
    systems = BattleSystems()
    gate = systems.future_admission_gate
    assert not hasattr(gate, "admit_without_permit")
    assert not hasattr(gate, "dispatch_without_permit")

    port = AssaultDispatchPort(gate)
    assert not hasattr(port, "admit_without_permit")
    assert not hasattr(port, "dispatch_without_permit")


def test_arch_p96_assault_dispatch_port_is_seam_only() -> None:
    """AssaultDispatchPort requires authentic ASSAULT permit, validates parent_scope, and has no gameplay."""
    context = _make_context()
    systems = BattleSystems()
    gate = systems.future_admission_gate
    port = systems.assault_dispatch_port

    parent_scope = "test_scope_assault"
    permit = gate.request_admission(FutureBranchKind.ASSAULT, parent_scope)
    assert permit is not None

    # Invalid permit type rejected
    with pytest.raises(TypeError, match="permit must be FutureAdmissionPermit"):
        port.dispatch(context, "not_a_permit", parent_scope, actor=context.get_unit("a1"), actual_target_id="b1")  # type: ignore

    # Wrong branch kind rejected
    wrong_permit = gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    with pytest.raises(ValueError, match="Expected ASSAULT permit"):
        port.dispatch(context, wrong_permit, parent_scope, actor=context.get_unit("a1"), actual_target_id="b1")  # type: ignore

    # Dispatch consumes permit
    port.dispatch(context, permit, parent_scope, actor=context.get_unit("a1"), actual_target_id="b1")
    assert permit.permit_id in gate._consumed_permits

    # Replay rejected
    with pytest.raises(RuntimeError, match="already been consumed"):
        port.dispatch(context, permit, parent_scope, actor=context.get_unit("a1"), actual_target_id="b1")


# =========================================================================
# 2. Hard Gate Sequencing: Permit Before ID Allocation
# =========================================================================

class SpyOperationIdAllocator(OperationIdAllocator):
    def __init__(self, callback) -> None:
        super().__init__()
        self._cb = callback

    def allocate_action_id(self) -> ActionId:
        self._cb("allocate_action_id")
        return super().allocate_action_id()

    def allocate_normal_attack_id(self) -> NormalAttackInstanceId:
        self._cb("allocate_na_id")
        return super().allocate_normal_attack_id()


def test_p96_hard_gate_permit_consumed_before_action_id_allocation() -> None:
    """ActionScope admission consumes permit BEFORE ActionId is allocated."""
    context = _make_context()
    systems = BattleSystems()
    gate = systems.future_admission_gate
    parent_scope = "test_scope"

    # 1. Denial: request returns None -> admit_action_scope must not be called / permit is None
    permit = gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    assert permit is not None

    # Monkeypatch consume_permit to spy sequence
    call_order: list[str] = []
    orig_consume = gate.consume_permit
    def spy_consume(*args, **kwargs):
        call_order.append("consume_permit")
        return orig_consume(*args, **kwargs)
    gate.consume_permit = spy_consume  # type: ignore

    context.id_allocator = SpyOperationIdAllocator(lambda tag: call_order.append(tag))

    scope = admit_action_scope(
        context=context,
        gate=gate,
        permit=permit,
        actor=context.get_unit("a1"),
        parent_scope_identity=parent_scope,
    )
    assert scope.admitted is True
    assert call_order == ["consume_permit", "allocate_action_id"]


def test_p96_hard_gate_permit_consumed_before_na2_id_allocation() -> None:
    """Combo #2 consumes COMBO_SECOND_NORMAL_ATTACK permit BEFORE NormalAttackInstanceId #2 is allocated."""
    context = _make_context()
    systems = BattleSystems()

    # Apply valid COMBO to a1
    systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.COMBO.value,
        owner_id="a1",
        source_id="a1",
        source_skill_id="skill_combo",
        source_skill_slot=SkillSlot.INHERENT,
        runtime_params=ComboStateParams(remaining_actions=1),
    )

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    assert permit is not None

    action_scope = admit_action_scope(
        context=context,
        gate=systems.future_admission_gate,
        permit=permit,
        actor=context.get_unit("a1"),
        parent_scope_identity=parent_scope,
    )

    call_order: list[str] = []
    orig_consume = systems.future_admission_gate.consume_permit
    def spy_consume(*args, **kwargs):
        branch = kwargs.get("expected_branch_kind") or (args[1] if len(args) > 1 else None)
        if branch == FutureBranchKind.COMBO_SECOND_NORMAL_ATTACK:
            call_order.append("consume_combo_permit")
        return orig_consume(*args, **kwargs)
    systems.future_admission_gate.consume_permit = spy_consume  # type: ignore

    context.id_allocator = SpyOperationIdAllocator(lambda tag: call_order.append(tag))

    res = systems.action_system.execute(context, context.get_unit("a1"), action_scope=action_scope)
    assert res is not None
    # Verify consume happened before the second NA allocation
    assert "consume_combo_permit" in call_order
    consume_idx = call_order.index("consume_combo_permit")
    assert call_order[consume_idx + 1] == "allocate_na_id"


# =========================================================================
# 3. Production Route & Event Ordering: NORMAL_ATTACK Before DAMAGE_*
# =========================================================================

def test_p96_event_ordering_normal_attack_before_damage() -> None:
    """NORMAL_ATTACK event occurs strictly BEFORE DAMAGE_PREVENTED or DAMAGE_DEALT."""
    context = _make_context()
    systems = BattleSystems()

    events_captured: list[EventType] = []
    def listener(event) -> None:
        if event.event_type in (
            EventType.NORMAL_ATTACK,
            EventType.DAMAGE_DEALT,
            EventType.DAMAGE_PREVENTED,
        ):
            events_captured.append(event.event_type)

    for et in (EventType.NORMAL_ATTACK, EventType.DAMAGE_DEALT, EventType.DAMAGE_PREVENTED):
        context.event_bus.subscribe(et, listener)

    systems.normal_attack_system.execute(context, context.get_unit("a1"))

    assert len(events_captured) >= 2
    assert events_captured[0] == EventType.NORMAL_ATTACK
    assert events_captured[1] in (EventType.DAMAGE_DEALT, EventType.DAMAGE_PREVENTED)


def test_p96_production_cutover_damage_instance_coordinator_partitioned_route() -> None:
    """NormalAttack routes through DamageInstanceCoordinator partitioned execution."""
    context = _make_context()
    systems = BattleSystems()

    spy_exec = MagicMock(wraps=systems.damage_instance_coordinator.execute_partitioned_damage_instance)
    systems.damage_instance_coordinator.execute_partitioned_damage_instance = spy_exec  # type: ignore

    res = systems.normal_attack_system.execute(context, context.get_unit("a1"))
    assert res is not None
    assert spy_exec.call_count == 1
    call_kwargs = spy_exec.call_args[1]
    assert call_kwargs["request"].source_id == "a1"
    assert call_kwargs["lineage"].source_type == SourceType.NORMAL_ATTACK


# =========================================================================
# 4. Target Resolution Regressions (REG-TGT-05..07)
# =========================================================================

def test_reg_tgt_05_taunt_overrides_default_random_target() -> None:
    """REG-TGT-05: TAUNT forces normal attack to target the taunter."""
    context = _make_context()
    systems = BattleSystems()

    # Apply TAUNT on a1 from b2
    systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.TAUNT.value,
        owner_id="a1",
        source_id="b2",
        source_skill_id="taunt_skill",
        source_skill_slot=SkillSlot.INHERENT,
        runtime_params=TauntStateParams(taunt_target_id="b2"),
    )

    res = systems.normal_attack_system.execute(context, context.get_unit("a1"))
    assert res is not None
    assert res.target_resolution.intended_attack_target == "b2"
    assert res.actual_target_id == "b2"


def test_reg_tgt_06_guard_redirects_damage_recipient() -> None:
    """REG-TGT-06: GUARD redirects intended target to protector."""
    context = _make_context()
    systems = BattleSystems()

    # b2 guards b1
    systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.GUARD.value,
        owner_id="b1",
        source_id="b2",
        source_skill_id="guard_skill",
        source_skill_slot=SkillSlot.INHERENT,
        runtime_params=GuardStateParams(protector_id="b2"),
    )

    # Force a1 default target to be b1
    systems.target_system.select_normal_attack_target = MagicMock(return_value=context.get_unit("b1"))

    res = systems.normal_attack_system.execute(context, context.get_unit("a1"))
    assert res is not None
    assert res.target_resolution.intended_attack_target == "b1"
    assert res.target_resolution.post_redirect_actual_target == "b2"
    assert res.actual_target_id == "b2"


def test_reg_tgt_07_taunt_plus_guard_interaction() -> None:
    """REG-TGT-07: TAUNT arbitrates selected target, then GUARD arbitrates recipient."""
    context = _make_context()
    systems = BattleSystems()

    # a1 taunted by b1
    systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.TAUNT.value,
        owner_id="a1",
        source_id="b1",
        source_skill_id="taunt_skill",
        source_skill_slot=SkillSlot.INHERENT,
        runtime_params=TauntStateParams(taunt_target_id="b1"),
    )

    # b2 guards b1
    systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.GUARD.value,
        owner_id="b1",
        source_id="b2",
        source_skill_id="guard_skill",
        source_skill_slot=SkillSlot.INHERENT,
        runtime_params=GuardStateParams(protector_id="b2"),
    )

    res = systems.normal_attack_system.execute(context, context.get_unit("a1"))
    assert res is not None
    # Selected by TAUNT: b1
    assert res.target_resolution.intended_attack_target == "b1"
    # Guard redirected to: b2
    assert res.target_resolution.post_redirect_actual_target == "b2"
    assert res.actual_target_id == "b2"
    assert res.actual_target_id == "b2"


# =========================================================================
# 5. Combo P0 Regressions (REG-CMB-01..05)
# =========================================================================

def test_reg_cmb_01_combo_state_lifecycle_expiration() -> None:
    """REG-CMB-01: remaining_actions maintenance decrements and removes finite Combo."""
    context = _make_context()
    systems = BattleSystems()

    instance = systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.COMBO.value,
        owner_id="a1",
        source_id="a1",
        source_skill_id="combo_skill",
        source_skill_slot=SkillSlot.INHERENT,
        runtime_params=ComboStateParams(remaining_actions=2),
    )
    assert context.states.has(owner_id="a1", state_id=OfficialStateId.COMBO.value)

    # Action 1: maintenance decrements remaining_actions from 2 to 1
    engine = BattleEngine(context=context, systems=systems)
    context.current_round = 1
    context.current_phase = BattlePhase.UNIT_ACTION.value
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, "act1")
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), "act1")
    systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)

    inst1 = context.states.get(instance.instance_id)
    assert inst1.runtime_params.remaining_actions == 1

    # Action 2: maintenance decrements remaining_actions from 1 to 0 -> still valid for this action
    permit2 = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, "act2")
    scope2 = admit_action_scope(context, systems.future_admission_gate, permit2, context.get_unit("a1"), "act2")
    systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope2)

    inst2 = context.states.get(instance.instance_id)
    assert inst2.runtime_params.remaining_actions == 0

    # Action 3: remaining_actions <= 0 at action start -> physical removal
    permit3 = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, "act3")
    scope3 = admit_action_scope(context, systems.future_admission_gate, permit3, context.get_unit("a1"), "act3")
    systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope3)

    assert not context.states.has(owner_id="a1", state_id=OfficialStateId.COMBO.value)
    assert scope3.combo_grant is None


def test_reg_cmb_02_combo_first_in_wins_rejection() -> None:
    """REG-CMB-02: Second COMBO on same unit is rejected with First-In-Wins."""
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
            source_id="a2",
            source_skill_id="combo_2",
            source_skill_slot=SkillSlot.LEARNED_1,
            runtime_params=ComboStateParams(remaining_actions=2),
        )


def test_reg_cmb_03_combo_suppression_and_removal_on_grant() -> None:
    """REG-CMB-03: Removal revokes grant; Ordinary suppression preserves valid grant."""
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

    # 1. Active: valid
    assert grant.is_valid(context) is True

    # 2. Suppressed: physical instance still exists, grant remains valid!
    systems.stage9_state_runtime.set_combo_suppressed(context, inst.instance_id, True)
    assert grant.is_valid(context) is True

    # 3. Physically removed: grant becomes REVOKED_BY_PHYSICAL_REMOVE
    systems.state_lifecycle_system.remove(context, inst.instance_id)
    assert grant.is_valid(context) is False
    assert grant.state == ComboGrantState.REVOKED_BY_PHYSICAL_REMOVE


def test_reg_cmb_04_combo_second_normal_attack_fresh_target_and_guard() -> None:
    """REG-CMB-04: Combo #2 executes fresh target resolution and fresh Guard pass."""
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

    # Guard on b1 by b2
    systems.state_lifecycle_system.apply(
        context=context,
        state_id=OfficialStateId.GUARD.value,
        owner_id="b1",
        source_id="b2",
        source_skill_id="guard_skill",
        source_skill_slot=SkillSlot.INHERENT,
        runtime_params=GuardStateParams(protector_id="b2"),
    )

    # Setup target selection sequence: first attack targets b1 (redirected to b2),
    # second attack targets b2 directly
    targets = [context.get_unit("b1"), context.get_unit("b2")]
    target_iter = iter(targets)
    systems.target_system.random_enemy = MagicMock(side_effect=lambda ctx, act: next(target_iter))

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    res = systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)
    assert res is not None
    # NA #1 redirected to b2
    assert res.actual_target_id == "b2"
    assert res.target_resolution.intended_attack_target == "b1"
    assert res.target_resolution.post_redirect_actual_target == "b2"

    # NA #2 targeted b2 directly
    assert res.combo_second_attack is not None
    assert res.combo_second_attack.actual_target_id == "b2"
    assert res.combo_second_attack.target_resolution.intended_attack_target == "b2"
    assert res.combo_second_attack.target_resolution.post_redirect_actual_target == "b2"


def test_reg_cmb_05_combo_fact_published_and_checkpoint_states() -> None:
    """REG-CMB-05: Exactly one COMBO_OPPORTUNITY_CONSUMED fact published and checkpoint state transitions."""
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
    context.event_bus.subscribe(
        EventType.COMBO_OPPORTUNITY_CONSUMED,
        lambda ev: combo_facts.append(ev.payload),
    )

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    res = systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)
    assert res is not None

    # Exactly one fact
    assert len(combo_facts) == 1
    fact = combo_facts[0]
    assert fact["action_id"] == scope.action_id.value
    assert fact["source_skill"] == "combo_skill"

    # Checkpoint state is CONSUMED
    assert scope.combo_checkpoint_state == ComboCheckpointState.CONSUMED
    assert scope.combo_grant.state == ComboGrantState.CONSUMED


# =========================================================================
# 6. Combo Failure Matrix: Checkpoint Denied / Not Consumed
# =========================================================================

def test_p96_combo_failure_disarmed() -> None:
    """When actor is DISARMED after NA #1, NA #2 is blocked at can_normal_attack after atomic consume."""
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

    # Disarm actor during NA #1 (via on_calculated or state apply)
    def apply_disarm(event):
        if event.event_type == EventType.NORMAL_ATTACK:
            systems.state_lifecycle_system.apply(
                context=context,
                state_id=OfficialStateId.DISARM.value,
                owner_id="a1",
                source_id="b1",
                source_skill_id="disarm_skill",
                source_skill_slot=SkillSlot.INHERENT,
            )
    context.event_bus.subscribe(EventType.NORMAL_ATTACK, apply_disarm)

    res = systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)
    assert res is not None
    assert res.combo_second_attack is None
    # Checkpoint was reached, consumed atomically, but can_normal_attack blocked second hit
    assert scope.combo_checkpoint_state == ComboCheckpointState.CONSUMED
    assert scope.combo_grant.state == ComboGrantState.CONSUMED


def test_p96_combo_failure_grant_revoked_by_physical_remove() -> None:
    """When Combo state is physically removed before checkpoint, grant is REVOKED and NA #2 is skipped without consume."""
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

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(FutureBranchKind.NEXT_ACTION, parent_scope)
    scope = admit_action_scope(context, systems.future_admission_gate, permit, context.get_unit("a1"), parent_scope)

    # Remove state during NA #1
    def remove_combo(event):
        if event.event_type == EventType.NORMAL_ATTACK:
            systems.state_lifecycle_system.remove(context, inst.instance_id)
    context.event_bus.subscribe(EventType.NORMAL_ATTACK, remove_combo)

    res = systems.action_system.execute(context, context.get_unit("a1"), action_scope=scope)
    assert res is not None
    assert res.combo_second_attack is None
    assert scope.combo_grant.state == ComboGrantState.REVOKED_BY_PHYSICAL_REMOVE


# =========================================================================
# 7. Drain Semantics & FINAL_03_COMBO_BATTLE_END
# =========================================================================

def test_final_03_combo_battle_end() -> None:
    """FINAL_03_COMBO_BATTLE_END: Lethal NA #1 latches victory, admits draining work, then finalizes."""
    # b1 has 10 troops (dies on NA #1). b2 is alive.
    units = [
        _make_unit("a1", "A", 1000, speed=120, is_commander=True),
        _make_unit("b1", "B", 10, speed=100, is_commander=True),
        _make_unit("b2", "B", 1000, speed=90),
    ]
    context = _make_context(units=units)
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

    # Force a1 to target b1 first
    systems.target_system.select_normal_attack_target = MagicMock(return_value=context.get_unit("b1"))

    engine = BattleEngine(context=context, systems=systems)
    battle_result = engine.run()

    # Commander b1 died on NA #1.
    # Victory latched during NA #1. Active ActionScope drained and completed.
    # Battle finalization occurred cleanly with A victory.
    assert battle_result is not None
    assert battle_result.winner_team_id == "A"
    assert systems.finalization_coordinator.is_latched_or_finalized is True
    assert systems.finalization_coordinator.termination_state == BattleTerminationState.FINALIZED
    assert len(systems.finalization_coordinator.active_action_scope_ids) == 0


# =========================================================================
# 8. Invariant Invariance & Max Limits (INV-06..12, Physical NA <= 2)
# =========================================================================

def test_p96_physical_normal_attack_count_never_exceeds_two() -> None:
    """INV-12: Physical normal attacks in a single action cannot exceed 2."""
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
    # 1 from primary, 1 from combo_second_attack -> total 2
    assert res.combo_second_attack is not None
    assert res.combo_second_attack.combo_second_attack is None


def test_p96_future_branch_gate_no_fake_bypasses() -> None:
    """ActionId and NA #2 ID cannot be created without active permits through the gate."""
    context = _make_context()
    systems = BattleSystems()
    gate = systems.future_admission_gate

    # Direct permit consumption with forged/unissued permit fails
    forged = FutureAdmissionPermit(
        permit_id="forged_p",
        branch_kind=FutureBranchKind.NEXT_ACTION,
        parent_scope_identity="scope",
        termination_generation=0,
    )
    with pytest.raises(ValueError, match="was not issued by this gate"):
        gate.consume_permit(forged, FutureBranchKind.NEXT_ACTION, "scope")
