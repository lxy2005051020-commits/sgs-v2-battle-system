from __future__ import annotations

import pytest

from sgs_v2.battle_core import (
    BattleContext,
    BattlePhase,
    BattleSystems,
    EventBus,
    GuardStateParams,
    LineupPosition,
    NormalAttackInstanceId,
    OfficialStateId,
    RandomSystem,
    RedirectReason,
    SkillSlot,
    Stage9StateRuntime,
    StateDefinition,
    StateLifecycleSystem,
    SuppressionReason,
    TargetResolutionId,
    TargetResolutionResult,
    TargetResolutionSystem,
    TargetSystem,
    TauntLifecycleState,
    TauntStateParams,
    UnitRuntime,
)


def make_test_context() -> BattleContext:
    """Create a standard 4-unit context: A1 (commander), A2 (deputy) vs B1 (commander), B2 (deputy)."""
    units = {
        "a1": UnitRuntime(
            "a1", "武将A1", "A", 1000, 1000, 100, 100, 100,
            lineup_position=LineupPosition.COMMANDER,
        ),
        "a2": UnitRuntime(
            "a2", "武将A2", "A", 1000, 1000, 100, 100, 90,
            lineup_position=LineupPosition.DEPUTY_1,
        ),
        "b1": UnitRuntime(
            "b1", "武将B1", "B", 1000, 1000, 100, 100, 95,
            lineup_position=LineupPosition.COMMANDER,
        ),
        "b2": UnitRuntime(
            "b2", "武将B2", "B", 1000, 1000, 100, 100, 85,
            lineup_position=LineupPosition.DEPUTY_1,
        ),
    }
    context = BattleContext(
        battle_id="test-target-resolution",
        units=units,
        event_bus=EventBus(),
        random=RandomSystem(42),
    )
    context.current_round = 1
    context.current_phase = BattlePhase.UNIT_ACTION.value

    # Register needed definitions
    context.states.register_definition(
        StateDefinition(
            state_id=OfficialStateId.CONFUSION.value,
            name="混乱",
        )
    )
    context.states.register_definition(
        StateDefinition(
            state_id=OfficialStateId.TAUNT.value,
            name="嘲讽",
            runtime_params_type=TauntStateParams,
        )
    )
    context.states.register_definition(
        StateDefinition(
            state_id=OfficialStateId.GUARD.value,
            name="援护",
            runtime_params_type=GuardStateParams,
        )
    )
    context.states.register_definition(
        StateDefinition(
            state_id=OfficialStateId.INSIGHT.value,
            name="洞察",
        )
    )
    return context


def make_system() -> tuple[TargetResolutionSystem, Stage9StateRuntime, TargetSystem, StateLifecycleSystem]:
    lifecycle = StateLifecycleSystem()
    state_runtime = Stage9StateRuntime(state_lifecycle_system=lifecycle)
    target_system = TargetSystem()
    target_resolution = TargetResolutionSystem(target_system, state_runtime)
    return target_resolution, state_runtime, target_system, lifecycle


class TestTargetResolutionArbitration:
    """Target resolution contracts for Phase 9.3."""

    def test_reg_tgt_01_confusion_shadows_taunt_selector(self) -> None:
        """REG-TGT-01 — Confusion shadows Taunt selector.

        Given an actor has operational Confusion and an otherwise operational Taunt.
        When a new NormalAttack performs selector arbitration.
        Then the Confusion selector decides the intended/pre-redirect target;
        Taunt is shadowed for that selection only and is not removed or suppressed by that fact.
        """
        context = make_test_context()
        system, state_runtime, _, lifecycle = make_system()

        # Apply Taunt on a1 pointing to b1
        taunt_inst = lifecycle.apply(
            context,
            state_id=OfficialStateId.TAUNT.value,
            owner_id="a1",
            source_id="b1",
            runtime_params=TauntStateParams(taunt_target_id="b1"),
        )
        # Apply Confusion on a1
        confusion_inst = lifecycle.apply(
            context,
            state_id=OfficialStateId.CONFUSION.value,
            owner_id="a1",
            source_id="b2",
        )

        # Resolve target for a1
        na_id = context.id_allocator.allocate_normal_attack_id()
        result = system.resolve(context, "a1", normal_attack_id=na_id)

        assert result is not None
        # Confusion pool for a1: all alive units except a1 -> {a2, b1, b2}
        assert result.intended_attack_target in {"a2", "b1", "b2"}
        assert result.intended_attack_target != "a1"

        # Taunt is shadowed for this selection only, NOT removed, NOT suppressed
        assert context.states.has(owner_id="a1", state_id=OfficialStateId.TAUNT.value)
        assert context.states.get(taunt_inst.instance_id) == taunt_inst
        # Taunt is still operational according to its own state
        assert state_runtime.get_operational_taunt(context, "a1") is not None

    def test_reg_tgt_02_taunt_lifecycle_continues_while_selector_is_shadowed(self) -> None:
        """REG-TGT-02 — Taunt lifecycle continues while selector is shadowed.

        Given Taunt physically exists and remains lifecycle-valid while Confusion controls the current target selection.
        When Confusion later ceases before a future NormalAttack.
        Then the future NormalAttack may read the still-existing Taunt according to Taunt's own
        operational/source-liveness rules; no synthetic Taunt refresh/removal occurred merely because
        Confusion previously shadowed it.
        """
        context = make_test_context()
        system, _, _, lifecycle = make_system()

        taunt_inst = lifecycle.apply(
            context,
            state_id=OfficialStateId.TAUNT.value,
            owner_id="a1",
            source_id="b1",
            runtime_params=TauntStateParams(taunt_target_id="b1"),
        )
        confusion_inst = lifecycle.apply(
            context,
            state_id=OfficialStateId.CONFUSION.value,
            owner_id="a1",
            source_id="b2",
        )

        # First resolution: Confusion shadows Taunt
        na_id1 = context.id_allocator.allocate_normal_attack_id()
        res1 = system.resolve(context, "a1", normal_attack_id=na_id1)
        assert res1 is not None

        # Confusion later ceases (removed)
        lifecycle.remove(context, confusion_inst.instance_id)
        assert not context.states.has(owner_id="a1", state_id=OfficialStateId.CONFUSION.value)

        # Taunt physical instance still exists without any synthetic recreation
        assert context.states.get(taunt_inst.instance_id) == taunt_inst

        # Second resolution: Taunt now controls selection
        na_id2 = context.id_allocator.allocate_normal_attack_id()
        res2 = system.resolve(context, "a1", normal_attack_id=na_id2)
        assert res2 is not None
        assert res2.intended_attack_target == "b1"
        assert res2.post_redirect_actual_target == "b1"
        assert res2.redirect_reason == RedirectReason.NONE

    def test_reg_tgt_03_guard_occurs_after_selector(self) -> None:
        """REG-TGT-03 — Guard occurs after selector.

        Given selector arbitration chooses B as intended target and B is validly guarded by C.
        When target resolution completes.
        Then intendedAttackTarget=B, exactly one Guard pass runs, postRedirectActualTarget=C,
        and B retains selection provenance only.
        """
        context = make_test_context()
        system, _, _, lifecycle = make_system()

        # B1 is guarded by B2 (B1 is protected holder, B2 is protector)
        guard_inst = lifecycle.apply(
            context,
            state_id=OfficialStateId.GUARD.value,
            owner_id="b1",
            source_id="b2",
            runtime_params=GuardStateParams(protector_id="b2"),
        )

        # Taunt on A1 pointing to B1 so intended target is deterministically B1
        lifecycle.apply(
            context,
            state_id=OfficialStateId.TAUNT.value,
            owner_id="a1",
            source_id="b1",
            runtime_params=TauntStateParams(taunt_target_id="b1"),
        )

        na_id = context.id_allocator.allocate_normal_attack_id()
        result = system.resolve(context, "a1", normal_attack_id=na_id)
        assert result is not None
        assert result.intended_attack_target == "b1"
        assert result.post_redirect_actual_target == "b2"
        assert result.redirect_reason is RedirectReason.GUARD
        assert result.redirect_source == "b2"

    def test_reg_tgt_04_guard_is_single_pass(self) -> None:
        """REG-TGT-04 — Guard is single-pass.

        Given B is guarded by C and C is itself guarded by D.
        When A attacks B.
        Then the attack resolves B→C and stops; C is not recursively redirected to D.
        """
        context = make_test_context()
        # Add third enemy unit B3
        context.units["b3"] = UnitRuntime(
            "b3", "武将B3", "B", 1000, 1000, 100, 100, 80,
            lineup_position=LineupPosition.DEPUTY_2,
        )

        system, _, _, lifecycle = make_system()

        # B1 guarded by B2
        lifecycle.apply(
            context,
            state_id=OfficialStateId.GUARD.value,
            owner_id="b1",
            source_id="b2",
            runtime_params=GuardStateParams(protector_id="b2"),
        )
        # B2 guarded by B3
        lifecycle.apply(
            context,
            state_id=OfficialStateId.GUARD.value,
            owner_id="b2",
            source_id="b3",
            runtime_params=GuardStateParams(protector_id="b3"),
        )

        # Force A1 to target B1 via Taunt
        lifecycle.apply(
            context,
            state_id=OfficialStateId.TAUNT.value,
            owner_id="a1",
            source_id="b1",
            runtime_params=TauntStateParams(taunt_target_id="b1"),
        )

        na_id = context.id_allocator.allocate_normal_attack_id()
        result = system.resolve(context, "a1", normal_attack_id=na_id)
        assert result is not None
        assert result.intended_attack_target == "b1"
        # Resolves B1 -> B2 and STOPS! Must NOT resolve B2 -> B3.
        assert result.post_redirect_actual_target == "b2"
        assert result.redirect_reason is RedirectReason.GUARD
        assert result.redirect_source == "b2"

    def test_default_selector_when_no_confusion_and_no_taunt(self) -> None:
        context = make_test_context()
        system, _, _, _ = make_system()

        na_id = context.id_allocator.allocate_normal_attack_id()
        result = system.resolve(context, "a1", normal_attack_id=na_id)
        assert result is not None
        # Must choose an alive enemy {b1, b2}
        assert result.intended_attack_target in {"b1", "b2"}
        assert result.post_redirect_actual_target == result.intended_attack_target
        assert result.redirect_reason is RedirectReason.NONE
        assert result.redirect_source is None

    def test_dead_taunt_source_falls_back_to_default(self) -> None:
        context = make_test_context()
        system, _, _, lifecycle = make_system()

        # Apply Taunt pointing to b1
        lifecycle.apply(
            context,
            state_id=OfficialStateId.TAUNT.value,
            owner_id="a1",
            source_id="b1",
            runtime_params=TauntStateParams(taunt_target_id="b1"),
        )
        # Kill b1
        b1 = context.get_unit("b1")
        b1.troops = 0
        assert not b1.is_alive

        # Resolution should silent-fail Taunt and fall back to default (b2 is only alive enemy)
        na_id = context.id_allocator.allocate_normal_attack_id()
        result = system.resolve(context, "a1", normal_attack_id=na_id)
        assert result is not None
        assert result.intended_attack_target == "b2"
        assert result.post_redirect_actual_target == "b2"

    def test_target_resolution_result_immutability_and_validation(self) -> None:
        res_id = TargetResolutionId("res-001")
        na_id = NormalAttackInstanceId("na-001")

        result = TargetResolutionResult(
            resolution_id=res_id,
            normal_attack_id=na_id,
            intended_attack_target="b1",
            post_redirect_actual_target="b1",
            redirect_source=None,
            redirect_reason=RedirectReason.NONE,
        )

        with pytest.raises((AttributeError, TypeError)):
            result.intended_attack_target = "b2"  # type: ignore[misc]

        # Incompatible redirect fields
        with pytest.raises(ValueError, match="redirect_source must be None"):
            TargetResolutionResult(
                resolution_id=res_id,
                normal_attack_id=na_id,
                intended_attack_target="b1",
                post_redirect_actual_target="b1",
                redirect_source="b2",
                redirect_reason=RedirectReason.NONE,
            )

        with pytest.raises(ValueError, match="redirect_source is required"):
            TargetResolutionResult(
                resolution_id=res_id,
                normal_attack_id=na_id,
                intended_attack_target="b1",
                post_redirect_actual_target="b2",
                redirect_source=None,
                redirect_reason=RedirectReason.GUARD,
            )

    def test_target_resolution_id_forbids_comparisons(self) -> None:
        id1 = TargetResolutionId("tr-001")
        id2 = TargetResolutionId("tr-002")

        with pytest.raises(TypeError, match="does not support comparison operator"):
            _ = id1 < id2
        with pytest.raises(TypeError, match="does not support comparison operator"):
            _ = id1 <= id2
        with pytest.raises(TypeError, match="does not support comparison operator"):
            _ = id1 > id2
        with pytest.raises(TypeError, match="does not support comparison operator"):
            _ = id1 >= id2


class TestPhase93RepairAuthorityRegressions:
    """Explicit regression tests for Phase 9.3 authority contracts."""

    def test_arch_p93_01_stage9_state_runtime_cannot_self_construct_lifecycle(self) -> None:
        """ARCH-P93-01: Stage9StateRuntime cannot self-construct StateLifecycleSystem."""
        with pytest.raises(TypeError):
            Stage9StateRuntime()  # type: ignore[call-arg]
        with pytest.raises(TypeError):
            Stage9StateRuntime(None)  # type: ignore[arg-type]
        with pytest.raises(TypeError):
            Stage9StateRuntime("invalid")  # type: ignore[arg-type]

    def test_arch_p93_02_battle_systems_is_production_composition_root(self) -> None:
        """ARCH-P93-02: BattleSystems is production composition root for Stage9StateRuntime."""
        systems = BattleSystems()
        assert systems.stage9_state_runtime.lifecycle is systems.state_lifecycle_system
        assert systems.target_resolution_system._state_runtime is systems.stage9_state_runtime
        assert systems.target_resolution_system._target_system is systems.target_system

    def test_arch_p93_03_target_resolution_system_cannot_allocate_normal_attack_id(self) -> None:
        """ARCH-P93-03: TargetResolutionSystem cannot allocate NormalAttackInstanceId."""
        context = make_test_context()
        system, _, _, _ = make_system()

        with pytest.raises(TypeError):
            system.resolve(context, "a1")  # type: ignore[call-arg]
        with pytest.raises(TypeError):
            system.resolve(context, "a1", normal_attack_id=None)  # type: ignore[arg-type]

        before_alloc_count = context.id_allocator._normal_attack_seq
        na_id = context.id_allocator.allocate_normal_attack_id()
        assert context.id_allocator._normal_attack_seq == before_alloc_count + 1

        system.resolve(context, "a1", normal_attack_id=na_id)
        # Verify resolve did NOT increment normal attack counter
        assert context.id_allocator._normal_attack_seq == before_alloc_count + 1

    def test_arch_p93_04_target_resolution_system_allocates_only_target_resolution_id(self) -> None:
        """ARCH-P93-04: TargetResolutionSystem allocates only TargetResolutionId."""
        context = make_test_context()
        system, _, _, _ = make_system()

        na_id = context.id_allocator.allocate_normal_attack_id()
        tr_before = context.id_allocator._target_resolution_seq
        res = system.resolve(context, "a1", normal_attack_id=na_id)
        assert res is not None
        assert context.id_allocator._target_resolution_seq == tr_before + 1
        assert res.resolution_id.value.startswith("tr_")

        # Explicit resolution_id provided: no allocation occurs
        custom_tr = TargetResolutionId("tr-custom-42")
        tr_count_before = context.id_allocator._target_resolution_seq
        res_custom = system.resolve(
            context, "a1", normal_attack_id=na_id, resolution_id=custom_tr
        )
        assert res_custom is not None
        assert res_custom.resolution_id == custom_tr
        assert context.id_allocator._target_resolution_seq == tr_count_before

    def test_p0_cfs_p93_01_insight_immunity_not_reinterpreted_as_jit_confusion_suppression(self) -> None:
        """P0-CFS-P93-01: Insight application immunity is not silently reinterpreted as JIT Confusion suppression."""
        context = make_test_context()
        system, state_runtime, _, lifecycle = make_system()

        lifecycle.apply(
            context,
            state_id=OfficialStateId.CONFUSION.value,
            owner_id="a1",
            source_id="b2",
        )
        lifecycle.apply(
            context,
            state_id=OfficialStateId.INSIGHT.value,
            owner_id="a1",
            source_id="a1",
        )

        # Confusion is still operational (Insight does not suppress existing instances)
        confusion = state_runtime.get_operational_confusion(context, "a1")
        assert confusion is not None

        na_id = context.id_allocator.allocate_normal_attack_id()
        result = system.resolve(context, "a1", normal_attack_id=na_id)
        assert result is not None
        # Resolves via Confusion selector: candidates are alive allies (without self) + alive enemies
        assert result.intended_attack_target in {"a2", "b1", "b2"}
        assert result.intended_attack_target != "a1"

    def test_p93_r2_tnt_01_existing_taunt_plus_insight_operationally_suppressed_no_override(self) -> None:
        """P93-R2-TNT-01: existing Taunt + Insight -> physical state remains, Taunt operationally SUPPRESSED, no Taunt override."""
        context = make_test_context()
        system, state_runtime, _, lifecycle = make_system()

        taunt_inst = lifecycle.apply(
            context,
            state_id=OfficialStateId.TAUNT.value,
            owner_id="a1",
            source_id="b1",
            runtime_params=TauntStateParams(taunt_target_id="b1"),
        )
        insight_inst = lifecycle.apply(
            context,
            state_id=OfficialStateId.INSIGHT.value,
            owner_id="a1",
            source_id="a1",
        )

        # 1. Physical state remains in context.states
        instances = context.states.find(owner_id="a1", state_id=OfficialStateId.TAUNT.value)
        assert len(instances) == 1
        assert instances[0].instance_id == taunt_inst.instance_id

        # 2. Taunt is operationally SUPPRESSED
        suppressors = state_runtime.get_taunt_suppressors(context, taunt_inst)
        assert SuppressionReason.INSIGHT.value in suppressors
        assert state_runtime.get_taunt_lifecycle_state(context, taunt_inst) == TauntLifecycleState.SUPPRESSED
        assert state_runtime.is_taunt_operational(context, taunt_inst) is False
        assert state_runtime.get_operational_taunt(context, "a1") is None

        # 3. No Taunt override during target resolution: regular targeting occurs
        na_id = context.id_allocator.allocate_normal_attack_id()
        result = system.resolve(context, "a1", normal_attack_id=na_id)
        assert result is not None
        assert result.intended_attack_target in {"b1", "b2"}

    def test_p93_r2_tnt_02_remove_final_suppressor_taunt_becomes_operational(self) -> None:
        """P93-R2-TNT-02: remove final suppressor -> Taunt becomes operational again."""
        context = make_test_context()
        system, state_runtime, _, lifecycle = make_system()

        taunt_inst = lifecycle.apply(
            context,
            state_id=OfficialStateId.TAUNT.value,
            owner_id="a1",
            source_id="b1",
            runtime_params=TauntStateParams(taunt_target_id="b1"),
        )
        insight_inst = lifecycle.apply(
            context,
            state_id=OfficialStateId.INSIGHT.value,
            owner_id="a1",
            source_id="a1",
        )
        assert state_runtime.get_taunt_lifecycle_state(context, taunt_inst) == TauntLifecycleState.SUPPRESSED
        assert state_runtime.get_operational_taunt(context, "a1") is None

        # Remove Insight
        lifecycle.remove(context, insight_inst.instance_id)

        # Now Taunt becomes operational again
        assert state_runtime.get_taunt_suppressors(context, taunt_inst) == frozenset()
        assert state_runtime.get_taunt_lifecycle_state(context, taunt_inst) == TauntLifecycleState.ACTIVE
        assert state_runtime.is_taunt_operational(context, taunt_inst) is True
        assert state_runtime.get_operational_taunt(context, "a1") == taunt_inst

        na_id = context.id_allocator.allocate_normal_attack_id()
        result = system.resolve(context, "a1", normal_attack_id=na_id)
        assert result is not None
        assert result.intended_attack_target == "b1"

    def test_p93_r2_tnt_03_suppressed_taunt_still_occupies_slot(self) -> None:
        """P93-R2-TNT-03: suppressed Taunt still occupies slot."""
        context = make_test_context()
        system, state_runtime, _, lifecycle = make_system()

        taunt_inst = lifecycle.apply(
            context,
            state_id=OfficialStateId.TAUNT.value,
            owner_id="a1",
            source_id="b1",
            source_skill_id="taunt_skill",
            source_skill_slot=SkillSlot.LEARNED_1,
            runtime_params=TauntStateParams(taunt_target_id="b1"),
        )
        lifecycle.apply(
            context,
            state_id=OfficialStateId.INSIGHT.value,
            owner_id="a1",
            source_id="a1",
        )
        assert state_runtime.get_taunt_lifecycle_state(context, taunt_inst) == TauntLifecycleState.SUPPRESSED

        # Suppressed Taunt is physically present and occupies registry/slot:
        # Re-applying same state with slot mismatch must raise ValueError
        with pytest.raises(ValueError, match="same-source reapply slot mismatch"):
            lifecycle.apply(
                context,
                state_id=OfficialStateId.TAUNT.value,
                owner_id="a1",
                source_id="b1",
                source_skill_id="taunt_skill",
                source_skill_slot=SkillSlot.LEARNED_2,
                runtime_params=TauntStateParams(taunt_target_id="b1"),
            )
        # Registry still holds the single suppressed instance
        instances = context.states.find(owner_id="a1", state_id=OfficialStateId.TAUNT.value)
        assert len(instances) == 1

    def test_p93_r2_tnt_04_source_dead_remains_independent_from_suppression_lifecycle(self) -> None:
        """P93-R2-TNT-04: source dead remains independent from suppression lifecycle."""
        context = make_test_context()
        system, state_runtime, _, lifecycle = make_system()

        taunt_inst = lifecycle.apply(
            context,
            state_id=OfficialStateId.TAUNT.value,
            owner_id="a1",
            source_id="b1",
            runtime_params=TauntStateParams(taunt_target_id="b1"),
        )
        # Without suppressors, lifecycle state is ACTIVE
        assert state_runtime.get_taunt_lifecycle_state(context, taunt_inst) == TauntLifecycleState.ACTIVE
        assert state_runtime.is_taunt_operational(context, taunt_inst) is True

        # Source unit dies
        context.get_unit("b1").troops = 0
        assert not context.get_unit("b1").is_alive

        # Lifecycle state remains ACTIVE (death of source does NOT mutate/suppress lifecycle state)
        assert state_runtime.get_taunt_lifecycle_state(context, taunt_inst) == TauntLifecycleState.ACTIVE
        # BUT operationally invalid because source is dead
        assert state_runtime.is_taunt_operational(context, taunt_inst) is False
        assert state_runtime.get_operational_taunt(context, "a1") is None

        # Targeting does not force dead source
        na_id = context.id_allocator.allocate_normal_attack_id()
        result = system.resolve(context, "a1", normal_attack_id=na_id)
        assert result is not None
        assert result.intended_attack_target == "b2"

    def test_p93_r2_tnt_05_taunt_target_authority_cannot_disagree_with_source_id(self) -> None:
        """P93-R2-TNT-05: Taunt target authority cannot disagree with source_id."""
        context = make_test_context()
        system, state_runtime, _, lifecycle = make_system()

        # Contradictory taunt_target_id != source_id is rejected at apply-time
        with pytest.raises(ValueError, match="cannot disagree with authoritative source_id"):
            lifecycle.apply(
                context,
                state_id=OfficialStateId.TAUNT.value,
                owner_id="a1",
                source_id="b1",
                runtime_params=TauntStateParams(taunt_target_id="b2"),
            )

        # Matching taunt_target_id == source_id succeeds
        taunt_inst = lifecycle.apply(
            context,
            state_id=OfficialStateId.TAUNT.value,
            owner_id="a1",
            source_id="b1",
            runtime_params=TauntStateParams(taunt_target_id="b1"),
        )
        assert state_runtime.get_taunt_target_unit_id(taunt_inst) == "b1"

        # None taunt_target_id succeeds and defaults to source_id
        taunt_inst_none = lifecycle.apply(
            context,
            state_id=OfficialStateId.TAUNT.value,
            owner_id="a2",
            source_id="b2",
            runtime_params=TauntStateParams(taunt_target_id=None),
        )
        assert state_runtime.get_taunt_target_unit_id(taunt_inst_none) == "b2"

    def test_p93_r2_grd_01_disabled_guard_physically_remains_but_does_not_redirect(self) -> None:
        """P93-R2-GRD-01: disabled Guard physically remains but does not redirect."""
        context = make_test_context()
        system, state_runtime, _, lifecycle = make_system()

        guard_inst = lifecycle.apply(
            context,
            state_id=OfficialStateId.GUARD.value,
            owner_id="b1",
            source_id="b2",
            runtime_params=GuardStateParams(protector_id="b2", is_disabled=True),
        )

        # 1. Guard physically exists in StateRegistry
        instances = context.states.find(owner_id="b1", state_id=OfficialStateId.GUARD.value)
        assert len(instances) == 1
        assert instances[0].instance_id == guard_inst.instance_id

        # 2. Guard is not operational and returns no protector
        assert state_runtime.is_guard_operational(context, guard_inst) is False
        assert state_runtime.get_guard_protector(context, "b1", attacker_id="a1") is None

        # 3. Normal attack targeting B1 does not redirect
        lifecycle.apply(
            context,
            state_id=OfficialStateId.TAUNT.value,
            owner_id="a1",
            source_id="b1",
            runtime_params=TauntStateParams(taunt_target_id="b1"),
        )
        na_id = context.id_allocator.allocate_normal_attack_id()
        result = system.resolve(context, "a1", normal_attack_id=na_id)
        assert result is not None
        assert result.intended_attack_target == "b1"
        assert result.post_redirect_actual_target == "b1"
        assert result.redirect_reason is RedirectReason.NONE

    def test_p93_r2_grd_02_re_enabled_operational_guard_may_redirect_again(self) -> None:
        """P93-R2-GRD-02: re-enabled operational Guard may redirect again."""
        context = make_test_context()
        system, state_runtime, _, lifecycle = make_system()

        guard_inst = lifecycle.apply(
            context,
            state_id=OfficialStateId.GUARD.value,
            owner_id="b1",
            source_id="b2",
            runtime_params=GuardStateParams(protector_id="b2", is_disabled=True),
        )
        assert state_runtime.is_guard_operational(context, guard_inst) is False

        # Re-enable via lifecycle.update_runtime_params
        updated_inst = lifecycle.update_runtime_params(
            context,
            guard_inst.instance_id,
            GuardStateParams(protector_id="b2", is_disabled=False),
        )
        assert updated_inst.runtime_params.is_disabled is False
        assert state_runtime.is_guard_operational(context, updated_inst) is True
        assert state_runtime.get_guard_protector(context, "b1", attacker_id="a1") == "b2"

        lifecycle.apply(
            context,
            state_id=OfficialStateId.TAUNT.value,
            owner_id="a1",
            source_id="b1",
            runtime_params=TauntStateParams(taunt_target_id="b1"),
        )
        na_id = context.id_allocator.allocate_normal_attack_id()
        result = system.resolve(context, "a1", normal_attack_id=na_id)
        assert result is not None
        assert result.intended_attack_target == "b1"
        assert result.post_redirect_actual_target == "b2"
        assert result.redirect_reason is RedirectReason.GUARD

    def test_p93_r2_grd_03_attacker_equals_protector_is_legal(self) -> None:
        """P93-R2-GRD-03: attacker == protector is legal."""
        context = make_test_context()
        system, state_runtime, _, lifecycle = make_system()

        # B1 is guarded by A1 (A1 is attacker on Team A)
        guard_inst = lifecycle.apply(
            context,
            state_id=OfficialStateId.GUARD.value,
            owner_id="b1",
            source_id="a1",
            runtime_params=GuardStateParams(protector_id="a1"),
        )
        assert state_runtime.is_guard_operational(context, guard_inst) is True

        # Attacker is A1: attacker == protector is allowed
        protector = state_runtime.get_guard_protector(context, "b1", attacker_id="a1")
        assert protector == "a1"

        lifecycle.apply(
            context,
            state_id=OfficialStateId.TAUNT.value,
            owner_id="a1",
            source_id="b1",
            runtime_params=TauntStateParams(taunt_target_id="b1"),
        )
        na_id = context.id_allocator.allocate_normal_attack_id()
        result = system.resolve(context, "a1", normal_attack_id=na_id)
        assert result is not None
        assert result.intended_attack_target == "b1"
        assert result.post_redirect_actual_target == "a1"
        assert result.redirect_reason is RedirectReason.GUARD

    def test_p93_r2_grd_04_dead_protector_does_not_redirect(self) -> None:
        """P93-R2-GRD-04: dead protector does not redirect."""
        context = make_test_context()
        system, state_runtime, _, lifecycle = make_system()

        guard_inst = lifecycle.apply(
            context,
            state_id=OfficialStateId.GUARD.value,
            owner_id="b1",
            source_id="b2",
            runtime_params=GuardStateParams(protector_id="b2"),
        )

        # Kill protector B2
        context.get_unit("b2").troops = 0
        assert not context.get_unit("b2").is_alive

        assert state_runtime.is_guard_operational(context, guard_inst) is False
        assert state_runtime.get_guard_protector(context, "b1", attacker_id="a1") is None

        lifecycle.apply(
            context,
            state_id=OfficialStateId.TAUNT.value,
            owner_id="a1",
            source_id="b1",
            runtime_params=TauntStateParams(taunt_target_id="b1"),
        )
        na_id = context.id_allocator.allocate_normal_attack_id()
        result = system.resolve(context, "a1", normal_attack_id=na_id)
        assert result is not None
        assert result.intended_attack_target == "b1"
        assert result.post_redirect_actual_target == "b1"
        assert result.redirect_reason is RedirectReason.NONE

    def test_p93_r2_grd_05_protector_explicit_identity_required(self) -> None:
        """P93-R2-GRD-05: protector explicit identity required."""
        context = make_test_context()
        system, state_runtime, _, lifecycle = make_system()

        # Missing protector_id raises TypeError
        with pytest.raises(TypeError):
            GuardStateParams()  # type: ignore[call-arg]

        # Empty string protector_id raises ValueError
        with pytest.raises(ValueError, match="protector_id must be a non-empty string"):
            GuardStateParams(protector_id="")

        # Self-guard (owner_id == protector_id) is rejected by StateLifecycleSystem
        with pytest.raises(ValueError, match="Self-guard is forbidden"):
            lifecycle.apply(
                context,
                state_id=OfficialStateId.GUARD.value,
                owner_id="b1",
                source_id="b2",
                runtime_params=GuardStateParams(protector_id="b1"),
            )

        # Immutability
        params = GuardStateParams(protector_id="b2")
        with pytest.raises((AttributeError, TypeError)):
            params.protector_id = "b3"  # type: ignore[misc]

    def test_p93_r2_grd_06_protector_identity_and_source_unit_provenance_remain_distinct(self) -> None:
        """P93-R2-GRD-06: protector identity and sourceUnit provenance remain distinct."""
        context = make_test_context()
        context.units["b3"] = UnitRuntime(
            "b3", "武将B3", "B", 1000, 1000, 100, 100, 80,
            lineup_position=LineupPosition.DEPUTY_2,
        )
        system, state_runtime, _, lifecycle = make_system()

        # Source is B3 (e.g. support caster), protector is B2, holder is B1
        guard_inst = lifecycle.apply(
            context,
            state_id=OfficialStateId.GUARD.value,
            owner_id="b1",
            source_id="b3",
            runtime_params=GuardStateParams(protector_id="b2"),
        )
        assert guard_inst.owner_id == "b1"
        assert guard_inst.source_id == "b3"
        assert guard_inst.runtime_params.protector_id == "b2"

        # Redirect returns protector B2, NOT caster B3
        protector = state_runtime.get_guard_protector(context, "b1", attacker_id="a1")
        assert protector == "b2"
        assert protector != guard_inst.source_id

        lifecycle.apply(
            context,
            state_id=OfficialStateId.TAUNT.value,
            owner_id="a1",
            source_id="b1",
            runtime_params=TauntStateParams(taunt_target_id="b1"),
        )
        na_id = context.id_allocator.allocate_normal_attack_id()
        result = system.resolve(context, "a1", normal_attack_id=na_id)
        assert result is not None
        assert result.intended_attack_target == "b1"
        assert result.post_redirect_actual_target == "b2"
        assert result.redirect_reason is RedirectReason.GUARD

    def test_p93_r2_grd_07_guard_remains_single_pass(self) -> None:
        """P93-R2-GRD-07: Guard remains single-pass."""
        context = make_test_context()
        context.units["b3"] = UnitRuntime(
            "b3", "武将B3", "B", 1000, 1000, 100, 100, 80,
            lineup_position=LineupPosition.DEPUTY_2,
        )
        system, _, _, lifecycle = make_system()

        lifecycle.apply(
            context,
            state_id=OfficialStateId.GUARD.value,
            owner_id="b1",
            source_id="b2",
            runtime_params=GuardStateParams(protector_id="b2"),
        )
        lifecycle.apply(
            context,
            state_id=OfficialStateId.GUARD.value,
            owner_id="b2",
            source_id="b3",
            runtime_params=GuardStateParams(protector_id="b3"),
        )
        lifecycle.apply(
            context,
            state_id=OfficialStateId.TAUNT.value,
            owner_id="a1",
            source_id="b1",
            runtime_params=TauntStateParams(taunt_target_id="b1"),
        )

        na_id = context.id_allocator.allocate_normal_attack_id()
        result = system.resolve(context, "a1", normal_attack_id=na_id)
        assert result is not None
        assert result.intended_attack_target == "b1"
        assert result.post_redirect_actual_target == "b2"
        assert result.redirect_reason is RedirectReason.GUARD

    def test_target_p93_01_confusion_legal_candidate_consumes_target_system_authority(self) -> None:
        """TARGET-P93-01: Confusion legal candidate construction consumes TargetSystem authority."""
        context = make_test_context()
        system, _, target_system, lifecycle = make_system()

        lifecycle.apply(
            context,
            state_id=OfficialStateId.CONFUSION.value,
            owner_id="a1",
            source_id="b2",
        )

        allies_calls = []
        orig_allies = target_system.allies

        def spy_allies(ctx, unit, *, alive_only=True, include_self=True):
            allies_calls.append((unit.unit_id, alive_only, include_self))
            return orig_allies(ctx, unit, alive_only=alive_only, include_self=include_self)

        enemies_calls = []
        orig_enemies = target_system.enemies

        def spy_enemies(ctx, unit, *, alive_only=True):
            enemies_calls.append((unit.unit_id, alive_only))
            return orig_enemies(ctx, unit, alive_only=alive_only)

        target_system.allies = spy_allies  # type: ignore[assignment]
        target_system.enemies = spy_enemies  # type: ignore[assignment]

        na_id = context.id_allocator.allocate_normal_attack_id()
        result = system.resolve(context, "a1", normal_attack_id=na_id)
        assert result is not None

        assert len(allies_calls) == 1
        assert allies_calls[0] == ("a1", True, False)
        assert len(enemies_calls) == 1
        assert enemies_calls[0] == ("a1", True)

    def test_target_p93_02_no_extra_rng_call_introduced(self) -> None:
        """TARGET-P93-02: No extra RNG call introduced."""
        context = make_test_context()
        system, _, _, lifecycle = make_system()

        lifecycle.apply(
            context,
            state_id=OfficialStateId.CONFUSION.value,
            owner_id="a1",
            source_id="b2",
        )

        rng_sample_calls = 0
        orig_sample = context.random.sample

        def counted_sample(pop, k):
            nonlocal rng_sample_calls
            rng_sample_calls += 1
            return orig_sample(pop, k)

        context.random.sample = counted_sample  # type: ignore[assignment]

        na_id = context.id_allocator.allocate_normal_attack_id()
        result = system.resolve(context, "a1", normal_attack_id=na_id)
        assert result is not None
        # With 3 candidates {a2, b1, b2}, random_units calls sample exactly once
        assert rng_sample_calls == 1

        # When only 1 candidate exists (kill a2 and b1)
        context.get_unit("a2").troops = 0
        context.get_unit("b1").troops = 0
        rng_sample_calls = 0
        na_id2 = context.id_allocator.allocate_normal_attack_id()
        result2 = system.resolve(context, "a1", normal_attack_id=na_id2)
        assert result2 is not None
        assert result2.intended_attack_target == "b2"
        # Deterministic when actual_count == len(candidates): 0 RNG calls
        assert rng_sample_calls == 0
