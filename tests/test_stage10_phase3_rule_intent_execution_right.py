from __future__ import annotations

from typing import Any
import pytest

from sgs_v2.battle_core import (
    AbortedRuleIntentResult,
    BattleContext,
    BattlePhase,
    DamageEffect,
    DamageEffectResult,
    DamageResolutionResult,
    DamageSourceType,
    DamageType,
    EffectExecutionResult,
    EffectExecutor,
    EffectSourceRef,
    EventBus,
    ExecutionRightDecision,
    ExecutionRightDecisionKind,
    ExecutionRightReason,
    ExecutionRightSystem,
    HookResolutionResult,
    LineupPosition,
    RandomSystem,
    RecoverEffect,
    RecoverEffectResult,
    RecoveryModelKind,
    RecoveryOpportunity,
    RecoveryOpportunityKind,
    RecoveryOpportunityResult,
    RoundStartHook,
    RuleHookSystem,
    RuleIntent,
    RuleIntentExecutionDescriptor,
    RuleIntentKind,
    SourceType,
    StateApplicationGenerationId,
    StateDefinition,
    StateInstance,
    StateLifecycleSystem,
    TriggerSystem,
    UnitActionStartHook,
    UnitRuntime,
)


def make_test_context() -> BattleContext:
    context = BattleContext(
        battle_id="test_phase3_battle",
        units={
            "p1": UnitRuntime(
                "p1", "Commander_P1", "team_a", 1000, 1000, 100, 100, 100,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "p2": UnitRuntime(
                "p2", "Commander_P2", "team_b", 1000, 100, 100, 100, 90,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "p3": UnitRuntime(
                "p3", "Deputy_P3", "team_b", 1000, 500, 100, 100, 80,
                lineup_position=LineupPosition.DEPUTY_1,
            ),
            "p4": UnitRuntime(
                "p4", "Deputy_P4", "team_a", 1000, 500, 100, 100, 70,
                lineup_position=LineupPosition.DEPUTY_1,
            ),
        },
        event_bus=EventBus(),
        random=RandomSystem(42),
    )
    context.current_round = 1
    context.current_phase = BattlePhase.ROUND_START.value
    return context


class TestRuleIntentExecutionDescriptor:
    def test_descriptor_immutability_and_required_fields(self) -> None:
        desc = RuleIntentExecutionDescriptor(
            intent_kind=RuleIntentKind.EFFECT,
            intent_owner_id="p1",
            state_owner_id="p1",
            target_id="p2",
            state_instance_id="state-000001",
            state_generation_id=StateApplicationGenerationId("gen_1"),
            execution_domain="STATE_RESOLUTION",
        )
        assert desc.intent_kind == RuleIntentKind.EFFECT
        assert desc.intent_owner_id == "p1"
        assert desc.state_owner_id == "p1"
        assert desc.target_id == "p2"
        assert desc.state_instance_id == "state-000001"
        assert desc.state_generation_id == StateApplicationGenerationId("gen_1")
        assert desc.execution_domain == "STATE_RESOLUTION"

        with pytest.raises((AttributeError, TypeError)):
            desc.intent_owner_id = "p2"  # type: ignore[misc]

    def test_descriptor_rejects_empty_intent_owner(self) -> None:
        with pytest.raises(ValueError, match="intent_owner_id"):
            RuleIntentExecutionDescriptor(
                intent_kind=RuleIntentKind.EFFECT,
                intent_owner_id="",
            )

        with pytest.raises(ValueError, match="intent_owner_id"):
            RuleIntentExecutionDescriptor(
                intent_kind=RuleIntentKind.EFFECT,
                intent_owner_id="   ",
            )


class TestExecutionRightSystemEvaluation:
    def test_alive_owner_and_alive_target_allows(self) -> None:
        context = make_test_context()
        ers = ExecutionRightSystem()
        desc = RuleIntentExecutionDescriptor(
            intent_kind=RuleIntentKind.EFFECT,
            intent_owner_id="p1",
            state_owner_id="p1",
            target_id="p2",
        )
        decision = ers.evaluate_rule_intent(desc, context)
        assert decision.decision_kind == ExecutionRightDecisionKind.ALLOW
        assert decision.reason is None

    def test_alive_owner_and_dead_target_rejects_current_target_defeated(self) -> None:
        context = make_test_context()
        context.get_unit("p2").troops = 0
        assert not context.get_unit("p2").is_alive

        ers = ExecutionRightSystem()
        desc = RuleIntentExecutionDescriptor(
            intent_kind=RuleIntentKind.EFFECT,
            intent_owner_id="p1",
            state_owner_id="p1",
            target_id="p2",
        )
        decision = ers.evaluate_rule_intent(desc, context)
        assert decision.decision_kind == ExecutionRightDecisionKind.REJECT_CURRENT
        assert decision.reason == ExecutionRightReason.TARGET_DEFEATED

    def test_dead_state_owner_aborts_owner_state_remainder(self) -> None:
        context = make_test_context()
        context.get_unit("p1").troops = 0
        assert not context.get_unit("p1").is_alive

        ers = ExecutionRightSystem()
        desc = RuleIntentExecutionDescriptor(
            intent_kind=RuleIntentKind.EFFECT,
            intent_owner_id="p1",
            state_owner_id="p1",
            target_id="p3",
        )
        decision = ers.evaluate_rule_intent(desc, context)
        assert decision.decision_kind == ExecutionRightDecisionKind.ABORT_OWNER_STATE_REMAINDER
        assert decision.reason == ExecutionRightReason.OWNER_DEFEATED

    def test_missing_state_instance_rejects_current_state_not_found(self) -> None:
        context = make_test_context()
        ers = ExecutionRightSystem()
        desc = RuleIntentExecutionDescriptor(
            intent_kind=RuleIntentKind.EFFECT,
            intent_owner_id="p1",
            state_owner_id="p1",
            target_id="p2",
            state_instance_id="nonexistent-state-9999",
        )
        decision = ers.evaluate_rule_intent(desc, context)
        assert decision.decision_kind == ExecutionRightDecisionKind.REJECT_CURRENT
        assert decision.reason == ExecutionRightReason.STATE_NOT_FOUND

    def test_battle_finalized_aborts_hook(self) -> None:
        context = make_test_context()
        context.ended = True

        ers = ExecutionRightSystem()
        desc = RuleIntentExecutionDescriptor(
            intent_kind=RuleIntentKind.EFFECT,
            intent_owner_id="p1",
            state_owner_id="p1",
            target_id="p2",
        )
        decision = ers.evaluate_rule_intent(desc, context)
        assert decision.decision_kind == ExecutionRightDecisionKind.ABORT_HOOK
        assert decision.reason == ExecutionRightReason.BATTLE_FINALIZED

    def test_official_stun_does_not_suppress_generic_rule_intent(self) -> None:
        context = make_test_context()
        context.states.register_definition(StateDefinition(state_id="stun", name="震慑"))
        StateLifecycleSystem().apply(context, state_id="stun", owner_id="p1")

        ers = ExecutionRightSystem()
        desc = RuleIntentExecutionDescriptor(
            intent_kind=RuleIntentKind.EFFECT,
            intent_owner_id="p1",
            state_owner_id="p1",
            target_id="p2",
        )
        decision = ers.evaluate_rule_intent(desc, context)
        assert decision.decision_kind == ExecutionRightDecisionKind.ALLOW
        assert decision.reason is None

    def test_no_duck_typing_enforcement_raises_on_arbitrary_object(self) -> None:
        context = make_test_context()
        ers = ExecutionRightSystem()

        class FakeIntent:
            intent_owner_id = "p1"
            state_owner_id = "p1"
            target_id = "p2"

        with pytest.raises(TypeError, match="RuleIntentExecutionDescriptor"):
            ers.evaluate_rule_intent(FakeIntent(), context)  # type: ignore[arg-type]


class TestHardeningH01Preconditions:
    def test_rule_hook_system_asserts_execution_descriptor_is_not_none(self) -> None:
        context = make_test_context()
        lifecycle = StateLifecycleSystem()

        class MissingDescriptorEffect:
            execution_descriptor = None

        class MockTrigger(TriggerSystem):
            def collect(self, ctx: BattleContext, hook: Any) -> tuple[Any, ...]:
                return (MissingDescriptorEffect(),)

        hook_system = RuleHookSystem(MockTrigger(), EffectExecutor(state_lifecycle_system=lifecycle))

        with pytest.raises(AssertionError, match="RuleIntent must carry an execution_descriptor"):
            hook_system.process(context, RoundStartHook(1))

    def test_rule_hook_system_asserts_intent_owner_id_populated(self) -> None:
        context = make_test_context()
        lifecycle = StateLifecycleSystem()

        class EmptyOwnerDescriptor:
            pass

        # Use mock descriptor with empty intent_owner_id to trigger S10-FG-H01 assertion
        class MockDesc:
            intent_owner_id = ""

        class BadIntent:
            execution_descriptor = MockDesc()

        class MockTrigger(TriggerSystem):
            def collect(self, ctx: BattleContext, hook: Any) -> tuple[Any, ...]:
                return (BadIntent(),)

        hook_system = RuleHookSystem(MockTrigger(), EffectExecutor(state_lifecycle_system=lifecycle))
        with pytest.raises(AssertionError, match="intent_owner_id must be populated"):
            hook_system.process(context, RoundStartHook(1))


class TestTargetDefeatedNormativeABCDTimeline:
    """
    S10-R3-B01 Normative A/B/C/D Test (§4.3.1):
    Intent A: owner P1, target P2. Deals damage to P2, killing P2.
    Intent B: owner P1, target P2. Target P2 is dead -> REJECT_CURRENT(TARGET_DEFEATED).
    Intent C: owner P1, target P3. Target P3 is alive -> executes!
    Intent D: owner P4, target P3. Target P3 is alive -> executes!
    """

    def test_target_defeated_rejects_only_current_and_continues_batch(self) -> None:
        context = make_test_context()
        lifecycle = StateLifecycleSystem()

        executed_intents: list[str] = []

        class FakeExecutor(EffectExecutor):
            def __init__(self) -> None:
                super().__init__(state_lifecycle_system=lifecycle)

            def execute(self, ctx: BattleContext, effect: Any) -> Any:
                name = effect.source_skill_id
                executed_intents.append(name)
                if name == "Intent_A":
                    # Kills P2!
                    ctx.get_unit("p2").troops = 0
                return RecoverEffectResult(
                    effect=effect if isinstance(effect, RecoverEffect) else RecoverEffect(source_id="p1", target_id="p1", amount=1),
                    resolution=None,  # type: ignore[arg-type]
                )

        desc_a = RuleIntentExecutionDescriptor(
            intent_kind=RuleIntentKind.EFFECT,
            intent_owner_id="p1",
            state_owner_id="p1",
            target_id="p2",
        )
        eff_a = RecoverEffect(
            source_id="p1", target_id="p2", amount=10, source_skill_id="Intent_A",
            execution_descriptor=desc_a,
        )

        desc_b = RuleIntentExecutionDescriptor(
            intent_kind=RuleIntentKind.EFFECT,
            intent_owner_id="p1",
            state_owner_id="p1",
            target_id="p2",
        )
        eff_b = RecoverEffect(
            source_id="p1", target_id="p2", amount=10, source_skill_id="Intent_B",
            execution_descriptor=desc_b,
        )

        desc_c = RuleIntentExecutionDescriptor(
            intent_kind=RuleIntentKind.EFFECT,
            intent_owner_id="p1",
            state_owner_id="p1",
            target_id="p3",
        )
        eff_c = RecoverEffect(
            source_id="p1", target_id="p3", amount=10, source_skill_id="Intent_C",
            execution_descriptor=desc_c,
        )

        desc_d = RuleIntentExecutionDescriptor(
            intent_kind=RuleIntentKind.EFFECT,
            intent_owner_id="p4",
            state_owner_id="p4",
            target_id="p3",
        )
        eff_d = RecoverEffect(
            source_id="p4", target_id="p3", amount=10, source_skill_id="Intent_D",
            execution_descriptor=desc_d,
        )

        class MockTrigger(TriggerSystem):
            def collect(self, ctx: BattleContext, hook: Any) -> tuple[Any, ...]:
                return (eff_a, eff_b, eff_c, eff_d)

        hook_system = RuleHookSystem(MockTrigger(), FakeExecutor())
        res = hook_system.process(context, RoundStartHook(1))

        # Invariant 1: Exactly A, C, D executed! Intent B was skipped!
        assert executed_intents == ["Intent_A", "Intent_C", "Intent_D"]

        # Invariant 2: len(intent_results) == 4
        assert len(res.intent_results) == 4

        # Intent A result: executed
        assert not isinstance(res.intent_results[0], AbortedRuleIntentResult)

        # Intent B result: rejected current due to TARGET_DEFEATED
        res_b = res.intent_results[1]
        assert isinstance(res_b, AbortedRuleIntentResult)
        assert res_b.decision_kind == ExecutionRightDecisionKind.REJECT_CURRENT
        assert res_b.reason == ExecutionRightReason.TARGET_DEFEATED

        # Intent C result: executed
        assert not isinstance(res.intent_results[2], AbortedRuleIntentResult)

        # Intent D result: executed
        assert not isinstance(res.intent_results[3], AbortedRuleIntentResult)

        # Batch completed (not aborted by target defeat)
        assert res.batch_status == "COMPLETED"


class TestOwnerDefeatedNormativeTimeline:
    """
    S10-R3-B01 Owner Death Timeline (§4.3.2):
    Intent A: owner P1, target P1. Deals lethal damage to P1, killing P1.
    Intent B: owner P1, target P2. State owner P1 dead -> ABORT_OWNER_STATE_REMAINDER(OWNER_DEFEATED).
    Intent C: owner P1, target P3. State owner P1 dead -> discarded / aborted.
    Intent D: owner P4, target P3. Owner P4 is alive -> executes!
    """

    def test_owner_death_aborts_owner_state_remainder_and_continues_other_owners(self) -> None:
        context = make_test_context()
        lifecycle = StateLifecycleSystem()

        executed_intents: list[str] = []

        class FakeExecutor(EffectExecutor):
            def __init__(self) -> None:
                super().__init__(state_lifecycle_system=lifecycle)

            def execute(self, ctx: BattleContext, effect: Any) -> Any:
                name = effect.source_skill_id
                executed_intents.append(name)
                if name == "Intent_A":
                    # Kills P1!
                    ctx.get_unit("p1").troops = 0
                return RecoverEffectResult(
                    effect=effect if isinstance(effect, RecoverEffect) else RecoverEffect(source_id="p1", target_id="p1", amount=1),
                    resolution=None,  # type: ignore[arg-type]
                )

        desc_a = RuleIntentExecutionDescriptor(
            intent_kind=RuleIntentKind.EFFECT,
            intent_owner_id="p1",
            state_owner_id="p1",
            target_id="p1",
        )
        eff_a = RecoverEffect(
            source_id="p1", target_id="p1", amount=10, source_skill_id="Intent_A",
            execution_descriptor=desc_a,
        )

        desc_b = RuleIntentExecutionDescriptor(
            intent_kind=RuleIntentKind.EFFECT,
            intent_owner_id="p1",
            state_owner_id="p1",
            target_id="p2",
        )
        eff_b = RecoverEffect(
            source_id="p1", target_id="p2", amount=10, source_skill_id="Intent_B",
            execution_descriptor=desc_b,
        )

        desc_c = RuleIntentExecutionDescriptor(
            intent_kind=RuleIntentKind.EFFECT,
            intent_owner_id="p1",
            state_owner_id="p1",
            target_id="p3",
        )
        eff_c = RecoverEffect(
            source_id="p1", target_id="p3", amount=10, source_skill_id="Intent_C",
            execution_descriptor=desc_c,
        )

        desc_d = RuleIntentExecutionDescriptor(
            intent_kind=RuleIntentKind.EFFECT,
            intent_owner_id="p4",
            state_owner_id="p4",
            target_id="p3",
        )
        eff_d = RecoverEffect(
            source_id="p4", target_id="p3", amount=10, source_skill_id="Intent_D",
            execution_descriptor=desc_d,
        )

        class MockTrigger(TriggerSystem):
            def collect(self, ctx: BattleContext, hook: Any) -> tuple[Any, ...]:
                return (eff_a, eff_b, eff_c, eff_d)

        hook_system = RuleHookSystem(MockTrigger(), FakeExecutor())
        res = hook_system.process(context, RoundStartHook(1))

        # Invariant 1: Exactly A and D executed! B and C belonging to P1 were discarded!
        assert executed_intents == ["Intent_A", "Intent_D"]

        # Invariant 2: len(intent_results) == 4
        assert len(res.intent_results) == 4

        # Intent A: executed
        assert not isinstance(res.intent_results[0], AbortedRuleIntentResult)

        # Intent B: aborted by OWNER_DEFEATED
        res_b = res.intent_results[1]
        assert isinstance(res_b, AbortedRuleIntentResult)
        assert res_b.decision_kind == ExecutionRightDecisionKind.ABORT_OWNER_STATE_REMAINDER
        assert res_b.reason == ExecutionRightReason.OWNER_DEFEATED

        # Intent C: aborted by OWNER_DEFEATED
        res_c = res.intent_results[2]
        assert isinstance(res_c, AbortedRuleIntentResult)
        assert res_c.decision_kind == ExecutionRightDecisionKind.ABORT_OWNER_STATE_REMAINDER
        assert res_c.reason == ExecutionRightReason.OWNER_DEFEATED

        # Intent D: executed for unrelated living owner P4!
        assert not isinstance(res.intent_results[3], AbortedRuleIntentResult)

        # Batch status marked aborted by target defeat
        assert res.batch_status == "ABORTED_BY_TARGET_DEFEAT"
        assert res.aborting_intent_index == 1


class TestMixedOrderingAndRecoveryOpportunityBoundary:
    def test_mixed_intent_ordering_preserved(self) -> None:
        """
        Tests that batch: [Effect A, RecoveryOpportunity B, Effect C]
        executes strictly in order [A, B, C].
        """
        context = make_test_context()
        lifecycle = StateLifecycleSystem()

        order_trace: list[str] = []

        class FakeExecutor(EffectExecutor):
            def __init__(self) -> None:
                super().__init__(state_lifecycle_system=lifecycle)

            def execute(self, ctx: BattleContext, effect: Any) -> Any:
                order_trace.append(effect.source_skill_id)
                return RecoverEffectResult(
                    effect=effect if isinstance(effect, RecoverEffect) else RecoverEffect(source_id="p1", target_id="p1", amount=1),
                    resolution=None,  # type: ignore[arg-type]
                )

        def fake_recovery_handler(ctx: BattleContext, opp: RecoveryOpportunity) -> RecoveryOpportunityResult:
            order_trace.append(opp.execution_descriptor.execution_domain)
            return RecoveryOpportunityResult(
                opportunity=opp,
                resolution=None,
                executed=True,
            )

        desc_a = RuleIntentExecutionDescriptor(
            intent_kind=RuleIntentKind.EFFECT,
            intent_owner_id="p1",
            state_owner_id="p1",
            target_id="p1",
        )
        eff_a = RecoverEffect(
            source_id="p1", target_id="p1", amount=10, source_skill_id="Effect_A",
            execution_descriptor=desc_a,
        )

        desc_b = RuleIntentExecutionDescriptor(
            intent_kind=RuleIntentKind.RECOVERY_OPPORTUNITY,
            intent_owner_id="p1",
            state_owner_id="p1",
            target_id="p1",
            execution_domain="Recovery_Opportunity_B",
        )
        opp_b = RecoveryOpportunity(
            opportunity_kind=RecoveryOpportunityKind.RECUPERATION_ACTION_START,
            execution_descriptor=desc_b,
            probability=1.0,
            recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT,
        )

        desc_c = RuleIntentExecutionDescriptor(
            intent_kind=RuleIntentKind.EFFECT,
            intent_owner_id="p1",
            state_owner_id="p1",
            target_id="p1",
        )
        eff_c = RecoverEffect(
            source_id="p1", target_id="p1", amount=10, source_skill_id="Effect_C",
            execution_descriptor=desc_c,
        )

        class MockTrigger(TriggerSystem):
            def collect(self, ctx: BattleContext, hook: Any) -> tuple[Any, ...]:
                return (eff_a, opp_b, eff_c)

        hook_system = RuleHookSystem(MockTrigger(), FakeExecutor())
        hook_system.recovery_opportunity_handler = fake_recovery_handler

        res = hook_system.process(context, RoundStartHook(1))

        # Invariant: Strict sequence [Effect_A, Recovery_Opportunity_B, Effect_C]
        assert order_trace == ["Effect_A", "Recovery_Opportunity_B", "Effect_C"]
        assert len(res.intent_results) == 3
        assert isinstance(res.intent_results[1], RecoveryOpportunityResult)
        assert res.intent_results[1].executed is True


class TestGenerationPreservationAcrossRefresh:
    def test_g1_descriptor_survives_g2_refresh(self) -> None:
        """
        G1 creates Intent I1 with descriptor.state_generation_id = G1.
        Same physical state refreshes to G2.
        Evaluation of I1 retains G1 descriptor facts and evaluates to ALLOW because physical state is alive.
        """
        context = make_test_context()
        lifecycle = StateLifecycleSystem()

        context.states.register_definition(StateDefinition(state_id="burn", name="灼烧"))
        inst1 = lifecycle.apply(context, state_id="burn", owner_id="p2", source_id="p1", duration_rounds=1)
        g1_id = inst1.current_generation_id

        # Intent I1 created under G1
        desc_g1 = RuleIntentExecutionDescriptor(
            intent_kind=RuleIntentKind.EFFECT,
            intent_owner_id="p2",
            state_owner_id="p2",
            target_id="p2",
            state_instance_id=inst1.instance_id,
            state_generation_id=g1_id,
        )

        # State refreshes to G2 on p2
        inst2 = lifecycle.refresh(context, instance_id=inst1.instance_id, source_id="p4", duration_rounds=2)
        g2_id = inst2.current_generation_id
        assert g2_id != g1_id

        # Evaluate I1
        ers = ExecutionRightSystem()
        decision = ers.evaluate_rule_intent(desc_g1, context)

        # Invariant: descriptor retains G1
        assert desc_g1.state_generation_id == g1_id
        # Invariant: physical state exists -> evaluates to ALLOW!
        assert decision.decision_kind == ExecutionRightDecisionKind.ALLOW


class TestOwnerIdentityDivergence:
    """
    Closure Audit: Verify that OWNER_DEFEATED abort scope strictly checks state_owner_id,
    and never conflates intent_owner_id with state_owner_id.
    """

    def test_state_owner_defeat_with_different_intent_owners(self) -> None:
        """
        Normative divergence test 1:
        Intent A: intent_owner=p2, state_owner=p1, target=p2
        Intent B: intent_owner=p3, state_owner=p1, target=p3
        Intent C: intent_owner=p1, state_owner=p4, target=p3

        P1 (state owner) is defeated. P2, P3, P4 are alive.
        Expected:
        A -> ABORT_OWNER_STATE_REMAINDER(OWNER_DEFEATED)
        B -> discarded because state_owner == p1
        C -> evaluates independently and executes because state_owner == p4 (alive)
        """
        context = make_test_context()
        p1 = context.units["p1"]
        p1.troops = 0

        desc_a = RuleIntentExecutionDescriptor(
            intent_kind=RuleIntentKind.EFFECT,
            intent_owner_id="p2",
            state_owner_id="p1",
            target_id="p2",
        )
        desc_b = RuleIntentExecutionDescriptor(
            intent_kind=RuleIntentKind.EFFECT,
            intent_owner_id="p3",
            state_owner_id="p1",
            target_id="p3",
        )
        desc_c = RuleIntentExecutionDescriptor(
            intent_kind=RuleIntentKind.EFFECT,
            intent_owner_id="p1",
            state_owner_id="p4",
            target_id="p3",
        )

        eff_a = RecoverEffect(source_id="p2", target_id="p2", amount=50, execution_descriptor=desc_a)
        eff_b = RecoverEffect(source_id="p3", target_id="p3", amount=50, execution_descriptor=desc_b)
        eff_c = RecoverEffect(source_id="p4", target_id="p3", amount=50, execution_descriptor=desc_c)

        class MockTrigger:
            def collect(self, ctx: BattleContext, hook: Any) -> tuple[Any, ...]:
                return (eff_a, eff_b, eff_c)

        executed_intents: list[Any] = []

        class MockExecutor:
            def execute(self, ctx: BattleContext, eff: Any) -> Any:
                executed_intents.append(eff)
                return RecoverEffectResult(
                    effect=eff,
                    resolution=None,  # type: ignore[arg-type]
                )

        hook_system = RuleHookSystem(MockTrigger(), MockExecutor())
        res = hook_system.process(context, RoundStartHook(1))

        # A is aborted by OWNER_DEFEATED
        assert isinstance(res.intent_results[0], AbortedRuleIntentResult)
        assert res.intent_results[0].decision_kind == ExecutionRightDecisionKind.ABORT_OWNER_STATE_REMAINDER
        assert res.intent_results[0].reason == ExecutionRightReason.OWNER_DEFEATED
        assert res.intent_results[0].descriptor.intent_owner_id == "p2"
        assert res.intent_results[0].descriptor.state_owner_id == "p1"

        # B is discarded because state_owner == p1
        assert isinstance(res.intent_results[1], AbortedRuleIntentResult)
        assert res.intent_results[1].decision_kind == ExecutionRightDecisionKind.ABORT_OWNER_STATE_REMAINDER
        assert res.intent_results[1].reason == ExecutionRightReason.OWNER_DEFEATED
        assert res.intent_results[1].descriptor.intent_owner_id == "p3"
        assert res.intent_results[1].descriptor.state_owner_id == "p1"

        # C is evaluated and EXECUTED because state_owner == p4 (alive)
        assert isinstance(res.intent_results[2], RecoverEffectResult)
        assert len(executed_intents) == 1
        assert executed_intents[0] is eff_c

    def test_same_intent_owner_different_state_owners(self) -> None:
        """
        Normative divergence test 2:
        Intent A: intent_owner=p1, state_owner=p2, target=p1
        Intent B: intent_owner=p1, state_owner=p3, target=p1

        P2 (state owner of A) is defeated.
        P3 (state owner of B) is alive.
        P1 (intent owner) is alive.
        Expected:
        A -> ABORT_OWNER_STATE_REMAINDER(OWNER_DEFEATED) for state_owner p2
        B -> evaluated and executes because state_owner is p3 (not p2).
             Must NOT be discarded just because intent_owner is p1!
        """
        context = make_test_context()
        p2 = context.units["p2"]
        p2.troops = 0

        desc_a = RuleIntentExecutionDescriptor(
            intent_kind=RuleIntentKind.EFFECT,
            intent_owner_id="p1",
            state_owner_id="p2",
            target_id="p1",
        )
        desc_b = RuleIntentExecutionDescriptor(
            intent_kind=RuleIntentKind.EFFECT,
            intent_owner_id="p1",
            state_owner_id="p3",
            target_id="p1",
        )

        eff_a = RecoverEffect(source_id="p1", target_id="p1", amount=50, execution_descriptor=desc_a)
        eff_b = RecoverEffect(source_id="p1", target_id="p1", amount=50, execution_descriptor=desc_b)

        class MockTrigger:
            def collect(self, ctx: BattleContext, hook: Any) -> tuple[Any, ...]:
                return (eff_a, eff_b)

        executed_intents: list[Any] = []

        class MockExecutor:
            def execute(self, ctx: BattleContext, eff: Any) -> Any:
                executed_intents.append(eff)
                return RecoverEffectResult(
                    effect=eff,
                    resolution=None,  # type: ignore[arg-type]
                )

        hook_system = RuleHookSystem(MockTrigger(), MockExecutor())
        res = hook_system.process(context, RoundStartHook(1))

        # A is aborted by OWNER_DEFEATED
        assert isinstance(res.intent_results[0], AbortedRuleIntentResult)
        assert res.intent_results[0].decision_kind == ExecutionRightDecisionKind.ABORT_OWNER_STATE_REMAINDER
        assert res.intent_results[0].reason == ExecutionRightReason.OWNER_DEFEATED
        assert res.intent_results[0].descriptor.state_owner_id == "p2"

        # B is NOT discarded, but executes normally!
        assert isinstance(res.intent_results[1], RecoverEffectResult)
        assert len(executed_intents) == 1
        assert executed_intents[0] is eff_b

