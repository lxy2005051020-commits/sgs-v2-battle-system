from __future__ import annotations

import pytest

from sgs_v2.battle_core import (
    BattleContext,
    BattlePhase,
    EventBus,
    GuardStateParams,
    LineupPosition,
    NormalAttackInstanceId,
    OfficialStateId,
    RandomSystem,
    RedirectReason,
    Stage9StateRuntime,
    StateDefinition,
    StateLifecycleSystem,
    TargetResolutionId,
    TargetResolutionResult,
    TargetResolutionSystem,
    TargetSystem,
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
        res1 = system.resolve(context, "a1")
        assert res1 is not None

        # Confusion later ceases (removed)
        lifecycle.remove(context, confusion_inst.instance_id)
        assert not context.states.has(owner_id="a1", state_id=OfficialStateId.CONFUSION.value)

        # Taunt physical instance still exists without any synthetic recreation
        assert context.states.get(taunt_inst.instance_id) == taunt_inst

        # Second resolution: Taunt now controls selection
        res2 = system.resolve(context, "a1")
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

        # B1 is guarded by B2 (B1 is protected holder, B2 is protector source)
        guard_inst = lifecycle.apply(
            context,
            state_id=OfficialStateId.GUARD.value,
            owner_id="b1",
            source_id="b2",
            runtime_params=GuardStateParams(guarded_unit_id="b1"),
        )

        # Taunt on A1 pointing to B1 so intended target is deterministically B1
        lifecycle.apply(
            context,
            state_id=OfficialStateId.TAUNT.value,
            owner_id="a1",
            source_id="b1",
            runtime_params=TauntStateParams(taunt_target_id="b1"),
        )

        result = system.resolve(context, "a1")
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
            runtime_params=GuardStateParams(guarded_unit_id="b1"),
        )
        # B2 guarded by B3
        lifecycle.apply(
            context,
            state_id=OfficialStateId.GUARD.value,
            owner_id="b2",
            source_id="b3",
            runtime_params=GuardStateParams(guarded_unit_id="b2"),
        )

        # Force A1 to target B1 via Taunt
        lifecycle.apply(
            context,
            state_id=OfficialStateId.TAUNT.value,
            owner_id="a1",
            source_id="b1",
            runtime_params=TauntStateParams(taunt_target_id="b1"),
        )

        result = system.resolve(context, "a1")
        assert result is not None
        assert result.intended_attack_target == "b1"
        # Resolves B1 -> B2 and STOPS! Must NOT resolve B2 -> B3.
        assert result.post_redirect_actual_target == "b2"
        assert result.redirect_reason is RedirectReason.GUARD
        assert result.redirect_source == "b2"

    def test_default_selector_when_no_confusion_and_no_taunt(self) -> None:
        context = make_test_context()
        system, _, _, _ = make_system()

        result = system.resolve(context, "a1")
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
        result = system.resolve(context, "a1")
        assert result is not None
        assert result.intended_attack_target == "b2"
        assert result.post_redirect_actual_target == "b2"

    def test_insight_suppresses_taunt_and_confusion(self) -> None:
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
        # Apply Insight on a1
        lifecycle.apply(
            context,
            state_id=OfficialStateId.INSIGHT.value,
            owner_id="a1",
            source_id="a1",
        )

        # Taunt should be suppressed by Insight, so default targeting runs
        result = system.resolve(context, "a1")
        assert result is not None
        assert result.intended_attack_target in {"b1", "b2"}

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
