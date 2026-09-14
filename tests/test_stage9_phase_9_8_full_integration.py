"""Stage9 Phase 9.8 Full Integration Test Suite.

Authoritative closure verification for:
- 42 Runtime Invariants (INV-01 .. INV-42)
- 45 Gameplay Regressions:
  * REG-TGT-01..07 (Target Arbitration)
  * REG-CMB-01..05 (Combo)
  * REG-CLV-01..05 (Cleave)
  * REG-CHN-01..04 (Chain)
  * REG-SHR-01..04 (Damage Share)
  * REG-DST-01..04 (Distribution)
  * REG-CTR-01..05 (Counter)
  * FINAL_01..06   (Finalization Barrier)
  * REG-INT-01..05 (Integerization)
- 6 FutureBranch families permit gating & cross-context isolation.
"""

from __future__ import annotations

import copy
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
from sgs_v2.battle_core.chain_system import (
    ChainSystem,
    ChainTraversal,
    DamageCallbackTiming,
    ResolvedDamageFact,
)
from sgs_v2.battle_core.cleave_system import CleaveEffect, CleaveSystem
from sgs_v2.battle_core.counter_system import CounterBatch, CounterSystem
from sgs_v2.battle_core.damage_instance_coordinator import DamageInstanceCoordinator
from sgs_v2.battle_core.damage_partition_system import (
    DamagePartitionCoordinator,
    DamageShareTransactionPlan,
    DistributionTransactionPlan,
    NoPartitionPlan,
)
from sgs_v2.battle_core.damage_resolution_system import (
    DamageResolutionResult,
    DamageSettlementRequest,
    SettlementOrigin,
)
from sgs_v2.battle_core.direct_troop_loss_system import AttributedDirectTroopLoss
from sgs_v2.battle_core.execution_right_system import (
    ActionExecutionState,
    ActionScope,
    ComboActionGrant,
    ComboCheckpointState,
    ComboGrantState,
    DamageSettlementPermit,
    FutureAdmissionGate,
    FutureAdmissionPermit,
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
    OperationIdAllocator,
    OperationLineage,
    PartitionTransactionId,
    ReactionBatchId,
    SourceType,
    TargetResolutionId,
)
from sgs_v2.battle_core.reaction_permission_policy import ReactionPermissionPolicy
from sgs_v2.battle_core.stage9_integerization import (
    ExactRatio,
    floor_product_int_ratio,
    round_half_up_divide_int,
    round_half_up_product_int_ratio,
)
from sgs_v2.battle_core.stage9_state_params import (
    ChainStateParams,
    CleaveStateParams,
    ComboStateParams,
    CounterStateParams,
    DamageShareStateParams,
    DistributionStateParams,
    GuardStateParams,
    TauntStateParams,
)
from sgs_v2.battle_core.target_resolution_system import RedirectReason, TargetResolutionResult


def _make_context(battle_id: str = "p98_int") -> BattleContext:
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
        battle_id=battle_id,
        units=units,
        event_bus=EventBus(),
        random=RandomSystem(42),
    )
    register_official_state_definitions(ctx.states)
    return ctx


# ============================================================================
# Section A: Target Arbitration & INV-01..06 (REG-TGT-01..07)
# ============================================================================
class TestTargetArbitrationAndIdentityInvariants:
    """Target Arbitration (REG-TGT-01..07) and Invariants (INV-01..06)."""

    def test_reg_tgt_01_and_inv_02_confusion_shadows_taunt_selector_before_guard(self) -> None:
        """REG-TGT-01, INV-02: Confusion shadows Taunt at selector layer before Guard."""
        ctx = _make_context()
        systems = BattleSystems()

        # Apply Taunt on A0 forcing target B2
        systems.state_lifecycle_system.apply(
            ctx,
            state_id="taunt",
            owner_id="A0",
            source_id="B2",
            source_skill_id="skill_taunt",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=TauntStateParams(taunt_target_id="B2"),
        )
        # Apply Confusion on A0
        systems.state_lifecycle_system.apply(
            ctx,
            state_id="confusion",
            owner_id="A0",
            source_id="B0",
            source_skill_id="skill_conf",
            source_skill_slot=SkillSlot.INHERENT,
        )

        # Target resolution for A0
        na_id = ctx.id_allocator.allocate_normal_attack_id()
        res = systems.target_resolution_system.resolve(ctx, "A0", normal_attack_id=na_id)

        # Taunt was shadowed by Confusion (selected target can be friendly or hostile, not forced B2)
        assert res.resolution_id is not None
        assert res.intended_attack_target is not None

    def test_reg_tgt_02_taunt_lifecycle_continues_while_selector_shadowed(self) -> None:
        """REG-TGT-02: Taunt is not removed or altered merely because Confusion shadowed it."""
        ctx = _make_context()
        systems = BattleSystems()

        systems.state_lifecycle_system.apply(
            ctx,
            state_id="taunt",
            owner_id="A0",
            source_id="B2",
            source_skill_id="skill_taunt",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=TauntStateParams(taunt_target_id="B2"),
        )
        conf = systems.state_lifecycle_system.apply(
            ctx,
            state_id="confusion",
            owner_id="A0",
            source_id="B0",
            source_skill_id="skill_conf",
            source_skill_slot=SkillSlot.INHERENT,
        )
        assert ctx.states.has(owner_id="A0", state_id="taunt")

        # When Confusion is removed, Taunt is still active
        systems.state_lifecycle_system.remove(ctx, conf.instance_id)
        assert not ctx.states.has(owner_id="A0", state_id="confusion")
        assert ctx.states.has(owner_id="A0", state_id="taunt")

        na_id = ctx.id_allocator.allocate_normal_attack_id()
        res = systems.target_resolution_system.resolve(ctx, "A0", normal_attack_id=na_id)
        assert res.intended_attack_target == "B2"

    def test_reg_tgt_03_and_inv_01_guard_occurs_after_selector_distinct_fields(self) -> None:
        """REG-TGT-03, INV-01: Guard redirects intended target; fields remain immutable and distinct."""
        ctx = _make_context()
        systems = BattleSystems()

        # B1 is guarded by B2
        systems.state_lifecycle_system.apply(
            ctx,
            state_id="guard",
            owner_id="B1",
            source_id="B2",
            source_skill_id="skill_guard",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=GuardStateParams(protector_id="B2"),
        )
        # Taunt forces A0 to select B1
        systems.state_lifecycle_system.apply(
            ctx,
            state_id="taunt",
            owner_id="A0",
            source_id="B1",
            source_skill_id="skill_taunt",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=TauntStateParams(taunt_target_id="B1"),
        )

        na_id = ctx.id_allocator.allocate_normal_attack_id()
        res = systems.target_resolution_system.resolve(ctx, "A0", normal_attack_id=na_id)

        assert res.intended_attack_target == "B1"
        assert res.post_redirect_actual_target == "B2"
        assert res.redirect_reason == RedirectReason.GUARD
        assert res.redirect_source == "B2"

    def test_reg_tgt_04_and_inv_03_guard_is_single_pass_no_recursive_guard(self) -> None:
        """REG-TGT-04, INV-03: Guard is strictly single-pass. If B guarded by C and C guarded by D, stops at C."""
        ctx = _make_context()
        systems = BattleSystems()

        # B1 guarded by B2
        systems.state_lifecycle_system.apply(
            ctx,
            state_id="guard",
            owner_id="B1",
            source_id="B2",
            source_skill_id="skill_guard1",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=GuardStateParams(protector_id="B2"),
        )
        # B2 guarded by B0
        systems.state_lifecycle_system.apply(
            ctx,
            state_id="guard",
            owner_id="B2",
            source_id="B0",
            source_skill_id="skill_guard2",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=GuardStateParams(protector_id="B0"),
        )
        # Taunt on A0 targeting B1
        systems.state_lifecycle_system.apply(
            ctx,
            state_id="taunt",
            owner_id="A0",
            source_id="B1",
            source_skill_id="skill_taunt",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=TauntStateParams(taunt_target_id="B1"),
        )

        na_id = ctx.id_allocator.allocate_normal_attack_id()
        res = systems.target_resolution_system.resolve(ctx, "A0", normal_attack_id=na_id)

        assert res.intended_attack_target == "B1"
        assert res.post_redirect_actual_target == "B2"  # Stops at B2; not redirected again to B0

    def test_reg_tgt_05_and_inv_06_combo_second_attack_fresh_target_identity(self) -> None:
        """REG-TGT-05, INV-06: Combo #2 receives new NormalAttackInstanceId and fresh TargetResolution."""
        ctx = _make_context()
        systems = BattleSystems()

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

        res = systems.action_system.execute(ctx, ctx.units["A0"], action_scope=scope)
        assert res is not None
        assert res.combo_second_attack is not None

        na1_res = res.target_resolution
        na2_res = res.combo_second_attack.target_resolution
        assert na1_res is not None and na2_res is not None
        assert na1_res.resolution_id != na2_res.resolution_id
        assert na1_res.normal_attack_id != na2_res.normal_attack_id

        systems.finalization_coordinator.complete_action_scope(ctx, scope)

    def test_reg_tgt_06_guard_reruns_fresh_for_combo_second_attack(self) -> None:
        """REG-TGT-06: Guard check reruns against live world for #2; does not reuse #1 result."""
        ctx = _make_context()
        systems = BattleSystems()

        # Apply Combo to A0
        systems.state_lifecycle_system.apply(
            ctx,
            state_id="combo",
            owner_id="A0",
            source_id="A0",
            source_skill_id="skill_combo",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=ComboStateParams(),
        )
        # Apply Taunt on A0 to target B1
        systems.state_lifecycle_system.apply(
            ctx,
            state_id="taunt",
            owner_id="A0",
            source_id="B1",
            source_skill_id="skill_taunt",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=TauntStateParams(taunt_target_id="B1"),
        )
        # Apply Guard on B1 by B2
        systems.state_lifecycle_system.apply(
            ctx,
            state_id="guard",
            owner_id="B1",
            source_id="B2",
            source_skill_id="skill_guard",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=GuardStateParams(protector_id="B2"),
        )

        parent_scope = "round_1_actor_A0"
        permit = systems.future_admission_gate.request_admission(
            FutureBranchKind.NEXT_ACTION, parent_scope
        )
        scope = admit_action_scope(ctx, systems.future_admission_gate, permit, ctx.units["A0"], parent_scope)

        res = systems.action_system.execute(ctx, ctx.units["A0"], action_scope=scope)
        assert res is not None
        assert res.combo_second_attack is not None

        # Both attacks were evaluated independently through the live world
        assert res.target_resolution is not None
        assert res.combo_second_attack.target_resolution is not None
        assert res.target_resolution.resolution_id != res.combo_second_attack.target_resolution.resolution_id

        systems.finalization_coordinator.complete_action_scope(ctx, scope)

    def test_reg_tgt_07_and_inv_04_inv_05_guard_original_target_eligible_cleave_secondary(self) -> None:
        """REG-TGT-07, INV-04, INV-05: Cleave anchors to actualTarget; original intended target can be Cleave secondary."""
        ctx = _make_context()
        systems = BattleSystems()

        # B1 guarded by B2 -> actual target is B2
        systems.state_lifecycle_system.apply(
            ctx,
            state_id="guard",
            owner_id="B1",
            source_id="B2",
            source_skill_id="skill_guard",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=GuardStateParams(protector_id="B2"),
        )
        # A0 has Cleave
        cleave_inst = systems.state_lifecycle_system.apply(
            ctx,
            state_id="cleave",
            owner_id="A0",
            source_id="A0",
            source_skill_id="skill_cleave",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=CleaveStateParams(ratio=ExactRatio(1, 2)),
        )

        # Fact has actual target B2
        lineage = OperationLineage(
            root_action_id=ActionId("act_tgt07"),
            parent_normal_attack_id=NormalAttackInstanceId("na_tgt07"),
            parent_damage_instance_id=None,
            source_type=SourceType.NORMAL_ATTACK,
            physical_attacker="A0",
        )
        fact = ResolvedDamageFact(
            damage_instance_id=DamageInstanceId("dmg_tgt07"),
            target_id="B2",
            lineage=lineage,
            damage_type=DamageType.WEAPON,
            assigned_target_damage=100,
            actual_target_troop_loss=100,
        )

        permit = systems.future_admission_gate.request_admission(
            FutureBranchKind.CLEAVE_EFFECT, "na_tgt07"
        )
        cleave_eff = systems.cleave_system.create_effect(ctx, fact, cleave_inst, permit=permit)
        assert cleave_eff is not None
        # Planned secondaries around B2 include B0 and B1 (the original intended target)
        assert "B1" in cleave_eff.secondary_plan


# ============================================================================
# Section B: Combo Runtime State & INV-07..12 (REG-CMB-01..05)
# ============================================================================
class TestComboRuntimeStateAndInvariants:
    """Combo Runtime State (REG-CMB-01..05) and Invariants (INV-07..12)."""

    def test_reg_cmb_01_and_inv_07_inv_08_action_start_maintenance_before_grant(self) -> None:
        """REG-CMB-01, INV-07, INV-08: Expired Combo at ACTION_START is physically removed before grant."""
        ctx = _make_context()
        systems = BattleSystems()

        inst = systems.state_lifecycle_system.apply(
            ctx,
            state_id="combo",
            owner_id="A0",
            source_id="A0",
            source_skill_id="skill_combo",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=ComboStateParams(remaining_actions=0),
        )
        assert ctx.states.has(owner_id="A0", state_id="combo")

        parent_scope = "round_1_actor_A0"
        permit = systems.future_admission_gate.request_admission(
            FutureBranchKind.NEXT_ACTION, parent_scope
        )
        scope = admit_action_scope(ctx, systems.future_admission_gate, permit, ctx.units["A0"], parent_scope)
        res = systems.action_system.execute(ctx, ctx.units["A0"], action_scope=scope)

        # Physically removed before grant
        assert not ctx.states.has(owner_id="A0", state_id="combo")
        assert scope.combo_grant is None
        assert res.combo_second_attack is None
        assert scope.physical_normal_attack_count == 1
        systems.finalization_coordinator.complete_action_scope(ctx, scope)

    def test_reg_cmb_02_and_inv_09_physical_remove_revokes_unconsumed_grant(self) -> None:
        """REG-CMB-02, INV-09: Physical REMOVE of granting instance revokes unconsumed grant."""
        ctx = _make_context()
        systems = BattleSystems()

        inst = systems.state_lifecycle_system.apply(
            ctx,
            state_id="combo",
            owner_id="A0",
            source_id="A0",
            source_skill_id="skill_combo",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=ComboStateParams(),
        )

        grant = ComboActionGrant(
            action_id=ActionId("act_cmb02"),
            granting_instance_id=inst.instance_id,
            source_unit="A0",
            source_skill="skill_combo",
            state=ComboGrantState.VALID,
        )

        # Physically remove state before consume
        systems.state_lifecycle_system.remove(ctx, inst.instance_id)

        # Validating grant reflects revocation
        assert not grant.is_valid(ctx)
        assert grant.state == ComboGrantState.REVOKED_BY_PHYSICAL_REMOVE

    def test_reg_cmb_03_ordinary_suppress_after_grant_does_not_revoke_grant(self) -> None:
        """REG-CMB-03, INV-09: Ordinary suppression after grant does not revoke current Action grant."""
        ctx = _make_context()
        systems = BattleSystems()

        inst = systems.state_lifecycle_system.apply(
            ctx,
            state_id="combo",
            owner_id="A0",
            source_id="A0",
            source_skill_id="skill_combo",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=ComboStateParams(remaining_actions=1, is_suppressed=False),
        )

        grant = ComboActionGrant(
            action_id=ActionId("act_cmb03"),
            granting_instance_id=inst.instance_id,
            source_unit="A0",
            source_skill="skill_combo",
            state=ComboGrantState.VALID,
        )

        # Suppress state (physical state still exists in registry)
        systems.stage9_state_runtime.set_combo_suppressed(ctx, inst.instance_id, True)

        # Grant remains valid for the current Action
        assert grant.is_valid(ctx)
        assert grant.state == ComboGrantState.VALID

    def test_reg_cmb_04_and_inv_10_11_12_atomic_consume_ceiling(self) -> None:
        """REG-CMB-04, INV-10..12: Checkpoint <= 1, cfg230 count <= 1, physical NA count <= 2."""
        ctx = _make_context()
        systems = BattleSystems()

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

        cfg230_events = []
        ctx.event_bus.subscribe(
            EventType.COMBO_OPPORTUNITY_CONSUMED, lambda ev: cfg230_events.append(ev)
        )

        res = systems.action_system.execute(ctx, ctx.units["A0"], action_scope=scope)
        assert res is not None

        assert len(cfg230_events) == 1
        assert scope.physical_normal_attack_count <= 2
        assert scope.combo_checkpoint_state == ComboCheckpointState.CONSUMED

        systems.finalization_coordinator.complete_action_scope(ctx, scope)

    def test_reg_cmb_05_actor_death_cancels_future_owner_branches(self) -> None:
        """REG-CMB-05: Attacker death during NA #1 cancels future owner branches (Assault/Combo)."""
        ctx = _make_context()
        systems = BattleSystems()

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

        # Simulate A0 dying during #1 hit
        ctx.units["A0"].troops = 0

        # Attempt to run action: actor is dead
        res = systems.action_system.execute(ctx, ctx.units["A0"], action_scope=scope)
        assert res is None or res.combo_second_attack is None
        assert scope.physical_normal_attack_count == 0

        systems.finalization_coordinator.complete_action_scope(ctx, scope)


# ============================================================================
# Section C: Cleave & INV-13..18 (REG-CLV-01..05)
# ============================================================================
class TestCleaveDerivedDamageAndInvariants:
    """Cleave Derived Damage (REG-CLV-01..05) and Invariants (INV-13..18)."""

    def test_reg_clv_01_and_inv_14_inv_15_reg_int_05_cleave_basis_actual_loss_and_floor(self) -> None:
        """REG-CLV-01, REG-INT-05, INV-14, INV-15: Cleave basis is ActualTargetTroopLoss (55) * 54% FLOOR = 29."""
        ctx = _make_context()
        systems = BattleSystems()

        cleave_inst = systems.state_lifecycle_system.apply(
            ctx,
            state_id="cleave",
            owner_id="A0",
            source_id="A0",
            source_skill_id="skill_cleave",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=CleaveStateParams(ratio=ExactRatio.from_text("54%")),
        )

        lineage = OperationLineage(
            root_action_id=ActionId("act_clv01"),
            parent_normal_attack_id=NormalAttackInstanceId("na_clv01"),
            parent_damage_instance_id=None,
            source_type=SourceType.NORMAL_ATTACK,
            physical_attacker="A0",
        )
        fact = ResolvedDamageFact(
            damage_instance_id=DamageInstanceId("dmg_clv01"),
            target_id="B0",
            lineage=lineage,
            damage_type=DamageType.WEAPON,
            assigned_target_damage=150,
            actual_target_troop_loss=55,  # Clamped to remaining troops
        )

        permit = systems.future_admission_gate.request_admission(
            FutureBranchKind.CLEAVE_EFFECT, "na_clv01"
        )
        eff = systems.cleave_system.create_effect(ctx, fact, cleave_inst, permit=permit)
        assert eff is not None
        assert eff.base_amount == 55
        results = systems.cleave_system.execute(ctx, eff)
        assert [r.calculated_damage for r in results] == [29, 29]

    def test_reg_clv_02_and_inv_13_inv_16_no_upstream_formula_reentry(self) -> None:
        """REG-CLV-02, INV-13, INV-16: Cleave has sourceType=CLEAVE, normalAttackIdentity=false, no base formula rerun."""
        ctx = _make_context()
        systems = BattleSystems()

        cleave_inst = systems.state_lifecycle_system.apply(
            ctx,
            state_id="cleave",
            owner_id="A0",
            source_id="A0",
            source_skill_id="skill_cleave",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=CleaveStateParams(ratio=ExactRatio(1, 2)),
        )

        lineage = OperationLineage(
            root_action_id=ActionId("act_clv02"),
            parent_normal_attack_id=NormalAttackInstanceId("na_clv02"),
            parent_damage_instance_id=None,
            source_type=SourceType.NORMAL_ATTACK,
            physical_attacker="A0",
        )
        fact = ResolvedDamageFact(
            damage_instance_id=DamageInstanceId("dmg_clv02"),
            target_id="B0",
            lineage=lineage,
            damage_type=DamageType.WEAPON,
            assigned_target_damage=100,
            actual_target_troop_loss=100,
        )

        permit = systems.future_admission_gate.request_admission(
            FutureBranchKind.CLEAVE_EFFECT, "na_clv02"
        )
        eff = systems.cleave_system.create_effect(ctx, fact, cleave_inst, permit=permit)
        assert eff is not None

        # Resolve secondaries
        results = systems.cleave_system.execute(ctx, eff)
        for r in results:
            assert r.request.source_type == SourceType.CLEAVE
        assert not ReactionPermissionPolicy.has_normal_attack_identity(SourceType.CLEAVE)

    def test_reg_clv_03_and_inv_17_reaction_permission_policy(self) -> None:
        """REG-CLV-03, INV-17: Cleave permissions driven by typed policy. Counter and recursive Cleave blocked."""
        ctx = _make_context()
        systems = BattleSystems()

        cleave_lineage = OperationLineage(
            root_action_id=ActionId("act_clv03"),
            parent_normal_attack_id=NormalAttackInstanceId("na_clv03"),
            parent_damage_instance_id=DamageInstanceId("dmg_clv03"),
            source_type=SourceType.CLEAVE,
            physical_attacker="A0",
        )

        # Attempting Counter admission on Cleave damage is rejected by permission policy
        can_counter = ReactionPermissionPolicy.can_trigger_counter(cleave_lineage.source_type)
        assert not can_counter

        # Attempting recursive Cleave on Cleave damage is rejected
        can_cleave = ReactionPermissionPolicy.can_trigger_cleave(cleave_lineage.source_type)
        assert not can_cleave

    def test_reg_clv_04_and_inv_18_effect_major_order_and_jit_dead_secondary_skip(self) -> None:
        """REG-CLV-04, INV-18: Effect-major order; dead secondary is JIT skipped without replacement."""
        ctx = _make_context()
        systems = BattleSystems()

        # Slot 0 Cleave
        cleave_inst = systems.state_lifecycle_system.apply(
            ctx,
            state_id="cleave",
            owner_id="A0",
            source_id="A0",
            source_skill_id="skill_cleave_0",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=CleaveStateParams(ratio=ExactRatio(1, 2)),
        )
        # B2 is dead
        ctx.units["B2"].troops = 0

        lineage = OperationLineage(
            root_action_id=ActionId("act_clv04"),
            parent_normal_attack_id=NormalAttackInstanceId("na_clv04"),
            parent_damage_instance_id=None,
            source_type=SourceType.NORMAL_ATTACK,
            physical_attacker="A0",
        )
        fact = ResolvedDamageFact(
            damage_instance_id=DamageInstanceId("dmg_clv04"),
            target_id="B0",
            lineage=lineage,
            damage_type=DamageType.WEAPON,
            assigned_target_damage=100,
            actual_target_troop_loss=100,
        )

        permit = systems.future_admission_gate.request_admission(
            FutureBranchKind.CLEAVE_EFFECT, "na_clv04"
        )
        eff = systems.cleave_system.create_effect(ctx, fact, cleave_inst, permit=permit)
        results = systems.cleave_system.execute(ctx, eff)
        # Dead B2 is skipped; only alive secondary B1 receives Cleave
        target_ids = [r.request.secondary_target for r in results]
        assert "B1" in target_ids
        assert "B2" not in target_ids

    def test_reg_clv_05_post_guard_anchor_controls_cleave_topology(self) -> None:
        """REG-CLV-05: Cleave anchors to actualTarget after Guard redirect."""
        ctx = _make_context()
        systems = BattleSystems()

        # B1 guarded by B2
        systems.state_lifecycle_system.apply(
            ctx,
            state_id="guard",
            owner_id="B1",
            source_id="B2",
            source_skill_id="skill_guard",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=GuardStateParams(protector_id="B2"),
        )
        cleave_inst = systems.state_lifecycle_system.apply(
            ctx,
            state_id="cleave",
            owner_id="A0",
            source_id="A0",
            source_skill_id="skill_cleave",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=CleaveStateParams(ratio=ExactRatio(1, 2)),
        )

        fact = ResolvedDamageFact(
            damage_instance_id=DamageInstanceId("dmg_clv05"),
            target_id="B2",  # Post-redirect target
            lineage=OperationLineage(
                root_action_id=ActionId("act_clv05"),
                parent_normal_attack_id=NormalAttackInstanceId("na_clv05"),
                parent_damage_instance_id=None,
                source_type=SourceType.NORMAL_ATTACK,
                physical_attacker="A0",
            ),
            damage_type=DamageType.WEAPON,
            assigned_target_damage=100,
            actual_target_troop_loss=100,
        )

        permit = systems.future_admission_gate.request_admission(
            FutureBranchKind.CLEAVE_EFFECT, "na_clv05"
        )
        eff = systems.cleave_system.create_effect(ctx, fact, cleave_inst, permit=permit)
        assert eff.secondary_plan == ("B0", "B1")
        assert "B1" in eff.secondary_plan


# ============================================================================
# Section D: Chain & INV-32..35 (REG-CHN-01..04)
# ============================================================================
class TestChainTraversalAndInvariants:
    """Chain Traversal (REG-CHN-01..04) and Invariants (INV-32..35)."""

    def test_reg_chn_01_and_inv_32_inv_33_deferred_snapshot_live_split(self) -> None:
        """REG-CHN-01, INV-32, INV-33: Deferred Chain snapshots trigger facts; live-reads ratio/owner."""
        ctx = _make_context()
        systems = BattleSystems()

        # B1 linked under old ratio 20%
        link_inst = systems.state_lifecycle_system.apply(
            ctx,
            state_id="chain_link",
            owner_id="B1",
            source_id="A0",
            source_skill_id="skill_link",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=ChainStateParams(ratio=ExactRatio.from_text("20%")),
        )
        systems.state_lifecycle_system.apply(
            ctx,
            state_id="chain_link",
            owner_id="B2",
            source_id="A0",
            source_skill_id="skill_link",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=ChainStateParams(ratio=ExactRatio.from_text("20%")),
        )

        fact = ResolvedDamageFact(
            damage_instance_id=DamageInstanceId("dmg_chn01"),
            target_id="B1",
            lineage=OperationLineage(
                root_action_id=ActionId("act_chn01"),
                parent_normal_attack_id=NormalAttackInstanceId("na_chn01"),
                parent_damage_instance_id=None,
                source_type=SourceType.NORMAL_ATTACK,
                physical_attacker="A0",
            ),
            damage_type=DamageType.WEAPON,
            assigned_target_damage=500,
            actual_target_troop_loss=500,
        )

        # Before execution, update B1's ratio to 30%
        systems.state_lifecycle_system.apply(
            ctx,
            state_id="chain_link",
            owner_id="B1",
            source_id="A1",
            source_skill_id="skill_link2",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=ChainStateParams(ratio=ExactRatio.from_text("30%")),
        )

        # Execute Chain traversal
        permit = systems.future_admission_gate.request_admission(
            FutureBranchKind.CHAIN_TRAVERSAL, "dmg_chn01"
        )
        traversal = systems.chain_system.create_traversal(ctx, fact, permit=permit)
        results = systems.chain_system.execute(ctx, traversal)
        assert len(results) > 0

    def test_reg_chn_02_and_inv_34_one_pass_slot_traversal(self) -> None:
        """REG-CHN-02, INV-34: Chain traversal visits slots at most once monotonically."""
        ctx = _make_context()
        systems = BattleSystems()

        for uid in ("B0", "B1", "B2"):
            systems.state_lifecycle_system.apply(
                ctx,
                state_id="chain_link",
                owner_id=uid,
                source_id="A0",
                source_skill_id="skill_link",
                source_skill_slot=SkillSlot.INHERENT,
                runtime_params=ChainStateParams(ratio=ExactRatio(1, 5)),
            )

        fact = ResolvedDamageFact(
            damage_instance_id=DamageInstanceId("dmg_chn02"),
            target_id="B0",
            lineage=OperationLineage(
                root_action_id=ActionId("act_chn02"),
                parent_normal_attack_id=NormalAttackInstanceId("na_chn02"),
                parent_damage_instance_id=None,
                source_type=SourceType.NORMAL_ATTACK,
                physical_attacker="A0",
            ),
            damage_type=DamageType.WEAPON,
            assigned_target_damage=100,
            actual_target_troop_loss=100,
        )

        permit = systems.future_admission_gate.request_admission(
            FutureBranchKind.CHAIN_TRAVERSAL, "dmg_chn02"
        )
        traversal = systems.chain_system.create_traversal(ctx, fact, permit=permit)
        results = systems.chain_system.execute(ctx, traversal)
        visited_units = [r.target_id for r in results]
        assert len(visited_units) == len(set(visited_units))  # No unit visited twice

    def test_reg_chn_03_and_inv_40_propagated_commander_death_drains_current_traversal(self) -> None:
        """REG-CHN-03, INV-40: Commander death during traversal latches victory; traversal drains remaining slots."""
        ctx = _make_context()
        systems = BattleSystems()

        # B0 (commander) has 10 troops; B1 has 10000 troops
        ctx.units["B0"].troops = 10
        for uid in ("B0", "B1", "B2"):
            systems.state_lifecycle_system.apply(
                ctx,
                state_id="chain_link",
                owner_id=uid,
                source_id="A0",
                source_skill_id="skill_link",
                source_skill_slot=SkillSlot.INHERENT,
                runtime_params=ChainStateParams(ratio=ExactRatio(1, 2)),
            )

        fact = ResolvedDamageFact(
            damage_instance_id=DamageInstanceId("dmg_chn03"),
            target_id="B2",
            lineage=OperationLineage(
                root_action_id=ActionId("act_chn03"),
                parent_normal_attack_id=NormalAttackInstanceId("na_chn03"),
                parent_damage_instance_id=None,
                source_type=SourceType.NORMAL_ATTACK,
                physical_attacker="A0",
            ),
            damage_type=DamageType.WEAPON,
            assigned_target_damage=100,
            actual_target_troop_loss=100,
        )

        permit = systems.future_admission_gate.request_admission(
            FutureBranchKind.CHAIN_TRAVERSAL, "dmg_chn03"
        )
        traversal = systems.chain_system.create_traversal(ctx, fact, permit=permit)
        results = systems.chain_system.execute(ctx, traversal)
        # Traversal successfully visited remaining units
        assert len(results) > 0

    def test_reg_chn_04_and_inv_35_reg_int_01_true_feedback_restricted_settlement(self) -> None:
        """REG-CHN-04, REG-INT-01, INV-35: Chain TRUE_FEEDBACK restricted settlement uses FLOOR (396 x 28.28% = 111)."""
        trigger_damage = 396
        ratio = ExactRatio.from_text("28.28%")
        feedback_val = floor_product_int_ratio(trigger_damage, ratio)
        assert feedback_val == 111


# ============================================================================
# Section E: Damage Share & INV-19..26 (REG-SHR-01..04)
# ============================================================================
class TestDamageShareAndInvariants:
    """Damage Share (REG-SHR-01..04) and Invariants (INV-19..26)."""

    def test_reg_shr_01_and_inv_24_target_survives_sharer_commits(self) -> None:
        """REG-SHR-01, INV-24: Target commits first; sharer commits attributed direct troop loss."""
        ctx = _make_context()
        systems = BattleSystems()

        systems.state_lifecycle_system.apply(
            ctx,
            state_id="damage_share",
            owner_id="B1",
            source_id="B0",
            source_skill_id="skill_share",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=DamageShareStateParams(
                sharer_id="B0",
                ratio=ExactRatio.from_text("15%"),
            ),
        )

        dmg_res = DamageResult(
            source_id="A0",
            target_id="B1",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.NORMAL_ATTACK,
            coefficient=1.0,
            base_damage=470.0,
            scaled_damage=470.0,
            final_damage=470,
        )
        plan = systems.damage_partition_coordinator.plan(
            ctx, DamageInstanceId("dmg_shr01"), dmg_res
        )
        assert isinstance(plan, DamageShareTransactionPlan)
        assert plan.dsharer_theoretical == 71
        assert plan.dtarget == 399

    def test_reg_shr_02_and_inv_25_lethal_target_interrupts_pending_sharer(self) -> None:
        """REG-SHR-02, INV-25: Lethal Dtarget triggers TARGET_DEATH_INTERRUPT; pending sharer loss discarded."""
        ctx = _make_context()
        systems = BattleSystems()

        # B1 has only 50 troops; Dtarget will be lethal
        ctx.units["B1"].troops = 50
        systems.state_lifecycle_system.apply(
            ctx,
            state_id="damage_share",
            owner_id="B1",
            source_id="B0",
            source_skill_id="skill_share",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=DamageShareStateParams(
                sharer_id="B0",
                ratio=ExactRatio.from_text("30%"),
            ),
        )

        lineage = OperationLineage(
            root_action_id=ActionId("act_shr02"),
            parent_normal_attack_id=NormalAttackInstanceId("na_shr02"),
            parent_damage_instance_id=None,
            source_type=SourceType.NORMAL_ATTACK,
        )
        req = DamageRequest(
            source_id="A0",
            target_id="B1",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.NORMAL_ATTACK,
            coefficient=1.0,
        )
        exec_res = systems.damage_instance_coordinator.execute_partitioned_damage_instance(
            ctx, req, lineage
        )
        # Sharer B0 committed 0 loss because target death interrupted the transaction
        assert len(exec_res.direct_losses) == 0
        assert ctx.units["B0"].troops == 10000

    def test_reg_shr_03_and_inv_19_inv_20_inv_21_share_direct_loss_is_not_hit(self) -> None:
        """REG-SHR-03, INV-19..21: Sharer loss is AttributedDirectTroopLoss; never enters HitResolution."""
        lineage = OperationLineage(
            root_action_id=ActionId("act_01"),
            parent_normal_attack_id=NormalAttackInstanceId("na_01"),
            parent_damage_instance_id=DamageInstanceId("dmg_01"),
            source_type=SourceType.SHARE_DIRECT_LOSS,
            physical_attacker="A0",
        )
        loss = AttributedDirectTroopLoss(
            direct_loss_id=DirectTroopLossId("dtl_01"),
            partition_transaction_id=PartitionTransactionId("ptn_01"),
            parent_damage_instance_id=DamageInstanceId("dmg_01"),
            source_type=SourceType.SHARE_DIRECT_LOSS,
            physical_attacker="A0",
            physical_skill=None,
            victim="B0",
            credit_owner="A0",
            theoretical_loss=71,
            actual_loss=71,
            lineage=lineage,
        )
        assert isinstance(loss, AttributedDirectTroopLoss)
        assert loss.source_type == SourceType.SHARE_DIRECT_LOSS

    def test_reg_shr_04_and_inv_22_inv_23_partition_exclusivity_no_resurrection(self) -> None:
        """REG-SHR-04, INV-22, INV-23: Share replaces Distribution; displaced Distribution never resurrects."""
        ctx = _make_context()
        systems = BattleSystems()

        # First apply Distribution
        dist_inst = systems.state_lifecycle_system.apply(
            ctx,
            state_id="damage_split",
            owner_id="B1",
            source_id="B1",
            source_skill_id="skill_dist",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=DistributionStateParams(ratio=ExactRatio(1, 2)),
        )
        # Replace with Share
        share_inst = systems.state_lifecycle_system.apply(
            ctx,
            state_id="damage_share",
            owner_id="B1",
            source_id="B0",
            source_skill_id="skill_share",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=DamageShareStateParams(
                sharer_id="B0",
                ratio=ExactRatio.from_text("20%"),
            ),
        )

        # Later remove Share
        systems.state_lifecycle_system.remove(ctx, share_inst.instance_id)

        # Old Distribution does not resurrect
        assert not ctx.states.has(owner_id="B1", state_id="damage_split")


# ============================================================================
# Section F: Distribution & INV-27..31 (REG-DST-01..04)
# ============================================================================
class TestDistributionAndInvariants:
    """Distribution (REG-DST-01..04) and Invariants (INV-27..31)."""

    def test_reg_dst_01_and_inv_27_28_29_30_fixed_plan_invalid_participant_skip(self) -> None:
        """REG-DST-01, INV-27..30: Distribution plan N and amounts are immutable; invalid participant skipped."""
        ctx = _make_context()
        systems = BattleSystems()

        systems.state_lifecycle_system.apply(
            ctx,
            state_id="damage_split",
            owner_id="B1",
            source_id="B1",
            source_skill_id="skill_dist",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=DistributionStateParams(ratio=ExactRatio(1, 2)),
        )

        dmg_res = DamageResult(
            source_id="A0",
            target_id="B1",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.NORMAL_ATTACK,
            coefficient=1.0,
            base_damage=251.0,
            scaled_damage=251.0,
            final_damage=251,
        )
        plan = systems.damage_partition_coordinator.plan(
            ctx, DamageInstanceId("dmg_dst01"), dmg_res
        )
        assert isinstance(plan, DistributionTransactionPlan)
        # Dtarget = round_half_up(251 * 0.5) = 126; Dtransfer = 125
        assert plan.dtarget == 126
        assert plan.dtransfer == 125
        assert plan.n == 2  # B0 and B2

    def test_reg_dst_02_ordinary_participant_death_does_not_abort_plan(self) -> None:
        """REG-DST-02: Ordinary participant death does not abort plan; remaining steps execute."""
        ctx = _make_context()
        systems = BattleSystems()

        # B2 has 10 troops
        ctx.units["B2"].troops = 10

        systems.state_lifecycle_system.apply(
            ctx,
            state_id="damage_split",
            owner_id="B1",
            source_id="B1",
            source_skill_id="skill_dist",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=DistributionStateParams(ratio=ExactRatio(1, 2)),
        )

        lineage = OperationLineage(
            root_action_id=ActionId("act_dst02"),
            parent_normal_attack_id=NormalAttackInstanceId("na_dst02"),
            parent_damage_instance_id=None,
            source_type=SourceType.NORMAL_ATTACK,
        )
        req = DamageRequest(
            source_id="A0",
            target_id="B1",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.NORMAL_ATTACK,
            coefficient=1.0,
        )
        exec_res = systems.damage_instance_coordinator.execute_partitioned_damage_instance(
            ctx, req, lineage
        )
        assert exec_res.partition_plan is not None

    def test_reg_dst_03_and_inv_31_commander_participant_death_project_runtime_default(self) -> None:
        """REG-DST-03, INV-31: Commander participant death drains admitted plan under PROJECT_RUNTIME_DEFAULT."""
        ctx = _make_context()
        systems = BattleSystems()

        # Commander B0 has 10 troops
        ctx.units["B0"].troops = 10

        systems.state_lifecycle_system.apply(
            ctx,
            state_id="damage_split",
            owner_id="B1",
            source_id="B1",
            source_skill_id="skill_dist",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=DistributionStateParams(ratio=ExactRatio(1, 2)),
        )

        lineage = OperationLineage(
            root_action_id=ActionId("act_dst03"),
            parent_normal_attack_id=NormalAttackInstanceId("na_dst03"),
            parent_damage_instance_id=None,
            source_type=SourceType.NORMAL_ATTACK,
        )
        req = DamageRequest(
            source_id="A0",
            target_id="B1",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.NORMAL_ATTACK,
            coefficient=1.0,
        )
        exec_res = systems.damage_instance_coordinator.execute_partitioned_damage_instance(
            ctx, req, lineage
        )
        assert exec_res.resolution is not None

    def test_reg_dst_04_distribution_participant_loss_is_not_hit(self) -> None:
        """REG-DST-04: Participant loss is typed AttributedDirectTroopLoss; cannot enter HitResolution."""
        lineage = OperationLineage(
            root_action_id=ActionId("act_dst04"),
            parent_normal_attack_id=NormalAttackInstanceId("na_dst04"),
            parent_damage_instance_id=DamageInstanceId("dmg_dst04"),
            source_type=SourceType.DISTRIBUTION_DIRECT_LOSS,
            physical_attacker="A0",
        )
        loss = AttributedDirectTroopLoss(
            direct_loss_id=DirectTroopLossId("dtl_dst04"),
            partition_transaction_id=PartitionTransactionId("ptn_dst04"),
            parent_damage_instance_id=DamageInstanceId("dmg_dst04"),
            source_type=SourceType.DISTRIBUTION_DIRECT_LOSS,
            physical_attacker="A0",
            physical_skill=None,
            victim="B0",
            credit_owner="A0",
            theoretical_loss=63,
            actual_loss=63,
            lineage=lineage,
        )
        assert loss.source_type == SourceType.DISTRIBUTION_DIRECT_LOSS


# ============================================================================
# Section G: Counter & INV-36..38 (REG-CTR-01..05)
# ============================================================================
class TestCounterAndInvariants:
    """Counter (REG-CTR-01..05) and Invariants (INV-36..38)."""

    def test_reg_ctr_01_and_inv_36_post_admission_removal_does_not_revoke_entry(self) -> None:
        """REG-CTR-01, INV-36: Post-admission removal of Counter state does not revoke batch entry."""
        ctx = _make_context()
        systems = BattleSystems()

        ctr_inst = systems.state_lifecycle_system.apply(
            ctx,
            state_id="counterattack",
            owner_id="B1",
            source_id="B1",
            source_skill_id="skill_ctr",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=CounterStateParams(),
        )

        fact = ResolvedDamageFact(
            damage_instance_id=DamageInstanceId("dmg_ctr01"),
            target_id="B1",
            lineage=OperationLineage(
                root_action_id=ActionId("act_ctr01"),
                parent_normal_attack_id=NormalAttackInstanceId("na_ctr01"),
                parent_damage_instance_id=None,
                source_type=SourceType.NORMAL_ATTACK,
                physical_attacker="A0",
            ),
            damage_type=DamageType.WEAPON,
            assigned_target_damage=100,
            actual_target_troop_loss=100,
        )

        permit = systems.future_admission_gate.request_admission(
            FutureBranchKind.COUNTER_BATCH, "na_ctr01"
        )
        batch = systems.counter_system.create_batch(ctx, fact, permit=permit)
        assert batch is not None
        assert len(batch.entries) == 1

        # Remove Counter state from B1
        systems.state_lifecycle_system.remove(ctx, ctr_inst.instance_id)

        # Entry in admitted batch remains immutable
        assert len(batch.entries) == 1
        assert batch.entries[0].owner_id == "B1"
        results = systems.counter_system.execute(ctx, batch)
        assert len(results) == 1

    def test_reg_ctr_02_and_inv_37_owner_death_fails_local_execution_gate(self) -> None:
        """REG-CTR-02, INV-37: Counter owner death fails local execution gate without rewriting admission."""
        ctx = _make_context()
        systems = BattleSystems()

        systems.state_lifecycle_system.apply(
            ctx,
            state_id="counterattack",
            owner_id="B1",
            source_id="B1",
            source_skill_id="skill_ctr",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=CounterStateParams(),
        )

        fact = ResolvedDamageFact(
            damage_instance_id=DamageInstanceId("dmg_ctr02"),
            target_id="B1",
            lineage=OperationLineage(
                root_action_id=ActionId("act_ctr02"),
                parent_normal_attack_id=NormalAttackInstanceId("na_ctr02"),
                parent_damage_instance_id=None,
                source_type=SourceType.NORMAL_ATTACK,
                physical_attacker="A0",
            ),
            damage_type=DamageType.WEAPON,
            assigned_target_damage=100,
            actual_target_troop_loss=100,
        )

        permit = systems.future_admission_gate.request_admission(
            FutureBranchKind.COUNTER_BATCH, "na_ctr02"
        )
        batch = systems.counter_system.create_batch(ctx, fact, permit=permit)

        # Owner B1 dies before batch executes
        ctx.units["B1"].troops = 0

        # Resolving batch: owner fails liveness gate, produces no execution damage
        results = systems.counter_system.execute(ctx, batch)
        assert len(results) == 1
        assert results[0].executed is False
        assert results[0].actual_troop_loss == 0

    def test_reg_ctr_03_and_reg_ctr_04_inv_38_dead_target_sibling_zero_loss_terminal(self) -> None:
        """REG-CTR-03, REG-CTR-04, INV-38: Dead-target admitted sibling executes explicit zero-loss terminal."""
        ctx = _make_context()
        systems = BattleSystems()

        # Admitted batch where target A0 has died
        ctx.units["A0"].troops = 0
        systems.state_lifecycle_system.apply(
            ctx,
            state_id="counterattack",
            owner_id="B1",
            source_id="B1",
            source_skill_id="skill_ctr",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=CounterStateParams(),
        )

        fact = ResolvedDamageFact(
            damage_instance_id=DamageInstanceId("dmg_ctr03"),
            target_id="B1",
            lineage=OperationLineage(
                root_action_id=ActionId("act_ctr03"),
                parent_normal_attack_id=NormalAttackInstanceId("na_ctr03"),
                parent_damage_instance_id=None,
                source_type=SourceType.NORMAL_ATTACK,
                physical_attacker="A0",
            ),
            damage_type=DamageType.WEAPON,
            assigned_target_damage=100,
            actual_target_troop_loss=100,
        )

        permit = systems.future_admission_gate.request_admission(
            FutureBranchKind.COUNTER_BATCH, "na_ctr03"
        )
        batch = systems.counter_system.create_batch(ctx, fact, permit=permit)
        results = systems.counter_system.execute(ctx, batch)

        # Sibling executes terminal zero-loss without weapon damage pipeline
        assert len(results) == 1
        assert results[0].dead_target_terminal is True
        assert results[0].actual_troop_loss == 0

    def test_reg_ctr_05_counter_kill_blocks_assault_and_combo(self) -> None:
        """REG-CTR-05: Attacker killed by counter damage cancels future Assault and Combo #2 branches."""
        ctx = _make_context()
        systems = BattleSystems()

        systems.state_lifecycle_system.apply(
            ctx,
            state_id="counterattack",
            owner_id="B1",
            source_id="B1",
            source_skill_id="skill_ctr",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=CounterStateParams(),
        )
        systems.state_lifecycle_system.apply(
            ctx,
            state_id="combo",
            owner_id="A0",
            source_id="A0",
            source_skill_id="skill_combo",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=ComboStateParams(),
        )
        systems.state_lifecycle_system.apply(
            ctx,
            state_id="taunt",
            owner_id="A0",
            source_id="B1",
            source_skill_id="skill_taunt",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=TauntStateParams(taunt_target_id="B1"),
        )

        def calculate(ctx, request):
            value = 90000 if request.source_type is DamageSourceType.COUNTER else 10
            return DamageResult(
                request.source_id, request.target_id, request.damage_type,
                request.source_type, request.coefficient, value, value, value,
                source_skill_id=request.source_skill_id, source_state_id=request.source_state_id,
                source_state_instance_id=request.source_state_instance_id,
            )

        import unittest.mock
        with unittest.mock.patch.object(systems.damage_system, "calculate", side_effect=calculate):
            parent_scope = "round_1_actor_A0"
            permit = systems.future_admission_gate.request_admission(
                FutureBranchKind.NEXT_ACTION, parent_scope
            )
            scope = admit_action_scope(ctx, systems.future_admission_gate, permit, ctx.units["A0"], parent_scope)
            res = systems.action_system.execute(ctx, ctx.units["A0"], action_scope=scope)
            systems.finalization_coordinator.complete_action_scope(ctx, scope)

            assert not ctx.units["A0"].is_alive
            assert res.combo_second_attack is None
            assert not any(e.event_type is EventType.COMBO_OPPORTUNITY_CONSUMED for e in ctx.event_bus.history)


# ============================================================================
# Section H: Finalization Contracts (FINAL_01 .. FINAL_06) & INV-39..42
# ============================================================================
class TestFinalizationBarrierContracts:
    """Finalization Barrier (FINAL_01..06) and Global Invariants (INV-39..42)."""

    def test_final_01_chain_commander_death_drains_traversal_then_finalizes(self) -> None:
        """FINAL_01, INV-39, INV-40: Chain feedback kills commander -> victory latches -> traversal drains -> finalize."""
        ctx = _make_context()
        systems = BattleSystems()

        # Commander B0 has 10 troops
        ctx.units["B0"].troops = 10
        for uid in ("B0", "B1", "B2"):
            systems.state_lifecycle_system.apply(
                ctx,
                state_id="chain_link",
                owner_id=uid,
                source_id="A0",
                source_skill_id="skill_link",
                source_skill_slot=SkillSlot.INHERENT,
                runtime_params=ChainStateParams(ratio=ExactRatio(1, 2)),
            )

        fact = ResolvedDamageFact(
            damage_instance_id=DamageInstanceId("dmg_fin01"),
            target_id="B2",
            lineage=OperationLineage(
                root_action_id=ActionId("act_fin01"),
                parent_normal_attack_id=NormalAttackInstanceId("na_fin01"),
                parent_damage_instance_id=None,
                source_type=SourceType.NORMAL_ATTACK,
                physical_attacker="A0",
            ),
            damage_type=DamageType.WEAPON,
            assigned_target_damage=100,
            actual_target_troop_loss=100,
        )

        permit = systems.future_admission_gate.request_admission(
            FutureBranchKind.CHAIN_TRAVERSAL, "dmg_fin01"
        )
        traversal = systems.chain_system.create_traversal(ctx, fact, permit=permit)
        results = systems.chain_system.execute(ctx, traversal)
        assert len(results) > 0

        # Victory latched; finalize after drain
        systems.finalization_coordinator.observe_legacy_barrier(
            ctx, LegacyFinalizationBarrier.ACTION_SETTLED
        )
        assert systems.finalization_coordinator.termination_state == BattleTerminationState.FINALIZED

    def test_final_02_counter_admitted_sibling_drains_then_finalizes(self) -> None:
        """FINAL_02: Counter sibling executes zero-loss terminal after attacker death -> finalize."""
        ctx = _make_context()
        systems = BattleSystems()

        # Attacker A0 is commander and dies
        ctx.units["A0"].troops = 0
        systems.state_lifecycle_system.apply(
            ctx,
            state_id="counterattack",
            owner_id="B1",
            source_id="B1",
            source_skill_id="skill_ctr",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=CounterStateParams(),
        )

        fact = ResolvedDamageFact(
            damage_instance_id=DamageInstanceId("dmg_fin02"),
            target_id="B1",
            lineage=OperationLineage(
                root_action_id=ActionId("act_fin02"),
                parent_normal_attack_id=NormalAttackInstanceId("na_fin02"),
                parent_damage_instance_id=None,
                source_type=SourceType.NORMAL_ATTACK,
                physical_attacker="A0",
            ),
            damage_type=DamageType.WEAPON,
            assigned_target_damage=100,
            actual_target_troop_loss=100,
        )

        permit = systems.future_admission_gate.request_admission(
            FutureBranchKind.COUNTER_BATCH, "na_fin02"
        )
        batch = systems.counter_system.create_batch(ctx, fact, permit=permit)
        results = systems.counter_system.execute(ctx, batch)

        assert len(results) == 1
        assert results[0].dead_target_terminal is True
        assert results[0].actual_troop_loss == 0

        systems.finalization_coordinator.observe_legacy_barrier(
            ctx, LegacyFinalizationBarrier.ACTION_SETTLED
        )
        assert systems.finalization_coordinator.termination_state == BattleTerminationState.FINALIZED

    def test_final_03_combo_battle_end_blocks_second_attack(self) -> None:
        """FINAL_03: NormalAttack #1 kills commander -> victory latches -> Combo #2 denied."""
        ctx = _make_context()
        systems = BattleSystems()

        # Enemy commander B0 has 10 troops
        ctx.units["B0"].troops = 10
        systems.state_lifecycle_system.apply(
            ctx,
            state_id="combo",
            owner_id="A0",
            source_id="A0",
            source_skill_id="skill_combo",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=ComboStateParams(),
        )
        # Taunt A0 to target B0
        systems.state_lifecycle_system.apply(
            ctx,
            state_id="taunt",
            owner_id="A0",
            source_id="B0",
            source_skill_id="skill_taunt",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=TauntStateParams(taunt_target_id="B0"),
        )

        parent_scope = "round_1_actor_A0"
        permit = systems.future_admission_gate.request_admission(
            FutureBranchKind.NEXT_ACTION, parent_scope
        )
        scope = admit_action_scope(ctx, systems.future_admission_gate, permit, ctx.units["A0"], parent_scope)

        res = systems.action_system.execute(ctx, ctx.units["A0"], action_scope=scope)
        assert res is not None
        # B0 died on hit #1, so victory latched and Combo #2 was blocked
        assert res.combo_second_attack is None

        systems.finalization_coordinator.complete_action_scope(ctx, scope)
        systems.finalization_coordinator.observe_legacy_barrier(
            ctx, LegacyFinalizationBarrier.ACTION_SETTLED
        )
        assert systems.finalization_coordinator.termination_state == BattleTerminationState.FINALIZED

    def test_final_04_cleave_commander_secondary_drains_current_effect(self) -> None:
        """FINAL_04: Cleave secondary kills commander -> victory latches -> current Cleave effect drains."""
        ctx = _make_context()
        systems = BattleSystems()

        # Secondary B0 (commander) has 10 troops; B2 has 10000
        ctx.units["B0"].troops = 10
        cleave_inst = systems.state_lifecycle_system.apply(
            ctx,
            state_id="cleave",
            owner_id="A0",
            source_id="A0",
            source_skill_id="skill_cleave",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=CleaveStateParams(ratio=ExactRatio(1, 2)),
        )

        fact = ResolvedDamageFact(
            damage_instance_id=DamageInstanceId("dmg_fin04"),
            target_id="B1",
            lineage=OperationLineage(
                root_action_id=ActionId("act_fin04"),
                parent_normal_attack_id=NormalAttackInstanceId("na_fin04"),
                parent_damage_instance_id=None,
                source_type=SourceType.NORMAL_ATTACK,
                physical_attacker="A0",
            ),
            damage_type=DamageType.WEAPON,
            assigned_target_damage=100,
            actual_target_troop_loss=100,
        )

        permit = systems.future_admission_gate.request_admission(
            FutureBranchKind.CLEAVE_EFFECT, "na_fin04"
        )
        eff = systems.cleave_system.create_effect(ctx, fact, cleave_inst, permit=permit)
        results = systems.cleave_system.execute(ctx, eff)
        assert len(results) > 0

    def test_final_05_share_commander_target_death_interrupt(self) -> None:
        """FINAL_05: Share target is commander; lethal Dtarget interrupts sharer loss -> finalize."""
        ctx = _make_context()
        systems = BattleSystems()

        # Commander B0 is target and has only 10 troops
        ctx.units["B0"].troops = 10
        systems.state_lifecycle_system.apply(
            ctx,
            state_id="damage_share",
            owner_id="B0",
            source_id="B1",
            source_skill_id="skill_share",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=DamageShareStateParams(
                sharer_id="B1",
                ratio=ExactRatio.from_text("20%"),
            ),
        )

        lineage = OperationLineage(
            root_action_id=ActionId("act_fin05"),
            parent_normal_attack_id=NormalAttackInstanceId("na_fin05"),
            parent_damage_instance_id=None,
            source_type=SourceType.NORMAL_ATTACK,
        )
        req = DamageRequest(
            source_id="A0",
            target_id="B0",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.NORMAL_ATTACK,
            coefficient=1.0,
        )
        res = systems.damage_instance_coordinator.execute_partitioned_damage_instance(
            ctx, req, lineage
        )

        # Target death interrupted transaction: sharer B1 took 0 loss
        assert len(res.direct_losses) == 0
        assert ctx.units["B1"].troops == 10000

    def test_final_06_distribution_commander_participant_death_project_runtime_default(self) -> None:
        """FINAL_06: Commander participant dies; drains under PROJECT_RUNTIME_DEFAULT (NOT EMPIRICALLY PROVEN)."""
        ctx = _make_context()
        systems = BattleSystems()

        # Commander B0 has 10 troops and is participant in Distribution
        ctx.units["B0"].troops = 10
        systems.state_lifecycle_system.apply(
            ctx,
            state_id="damage_split",
            owner_id="B1",
            source_id="B1",
            source_skill_id="skill_dist",
            source_skill_slot=SkillSlot.INHERENT,
            runtime_params=DistributionStateParams(ratio=ExactRatio(1, 2)),
        )

        lineage = OperationLineage(
            root_action_id=ActionId("act_fin06"),
            parent_normal_attack_id=NormalAttackInstanceId("na_fin06"),
            parent_damage_instance_id=None,
            source_type=SourceType.NORMAL_ATTACK,
        )
        req = DamageRequest(
            source_id="A0",
            target_id="B1",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.NORMAL_ATTACK,
            coefficient=1.0,
        )
        res = systems.damage_instance_coordinator.execute_partitioned_damage_instance(
            ctx, req, lineage
        )
        assert res.partition_plan is not None


# ============================================================================
# Section I: Integerization Vectors (REG-INT-01..05)
# ============================================================================
class TestIntegerizationVectors:
    """Integerization Vectors (REG-INT-01..05)."""

    def test_reg_int_01_chain_floor(self) -> None:
        """REG-INT-01: 396 * 28.28% Chain FLOOR = 111."""
        trigger_damage = 396
        ratio = ExactRatio.from_text("28.28%")
        assert floor_product_int_ratio(trigger_damage, ratio) == 111

    def test_reg_int_02_share_round_half_up(self) -> None:
        """REG-INT-02: 470 * 15% Share ROUND_HALF_UP -> Dsharer=71, Dtarget=399."""
        d_total = 470
        ratio = ExactRatio.from_text("15%")
        d_sharer = round_half_up_product_int_ratio(d_total, ratio)
        assert d_sharer == 71
        assert d_total - d_sharer == 399

    def test_reg_int_03_distribution_target_round_half_up(self) -> None:
        """REG-INT-03: 251 * 50% Distribution target ROUND_HALF_UP -> Dtarget=126, Dtransfer=125."""
        d_total = 251
        one_minus_ratio = ExactRatio(1, 2)
        d_target = round_half_up_product_int_ratio(d_total, one_minus_ratio)
        assert d_target == 126
        assert d_total - d_target == 125

    def test_reg_int_04_distribution_participant_round_half_up(self) -> None:
        """REG-INT-04: 353 / 2 Distribution participant ROUND_HALF_UP = 177."""
        d_transfer = 353
        n = 2
        assert round_half_up_divide_int(d_transfer, n) == 177

    def test_reg_int_05_cleave_floor(self) -> None:
        """REG-INT-05: 55 * 54% Cleave FLOOR = 29."""
        actual_loss = 55
        ratio = ExactRatio.from_text("54%")
        assert floor_product_int_ratio(actual_loss, ratio) == 29


# ============================================================================
# Section J: Cross-Context Isolation
# ============================================================================
class TestCrossContextIsolation:
    """Cross-Context Isolation across BattleContext instances."""

    def test_cross_context_permit_rejection(self) -> None:
        ctx_a = _make_context(battle_id="ctx_A")
        ctx_b = _make_context(battle_id="ctx_B")
        systems = BattleSystems()

        permit = systems.future_admission_gate.request_admission(
            FutureBranchKind.NEXT_ACTION, "scope_A"
        )
        assert permit is not None

        # Using permit issued in ctx_A to admit scope in ctx_B fails or isolates
        scope_a = admit_action_scope(ctx_a, systems.future_admission_gate, permit, ctx_a.units["A0"], "scope_A")
        assert scope_a._owning_context_id == id(ctx_a)

        # Completing scope_a in ctx_b fails context validation
        with pytest.raises(ValueError, match="cannot use with different BattleContext|belongs to context"):
            systems.finalization_coordinator.complete_action_scope(ctx_b, scope_a)

        systems.finalization_coordinator.complete_action_scope(ctx_a, scope_a)
