from __future__ import annotations

import pytest
from typing import Any
from unittest.mock import MagicMock

from sgs_v2.battle_core import (
    BattleContext,
    BattlePhase,
    BattleSystems,
    DamageAftermathFact,
    DamageAftermathPort,
    DamageAftermathSystem,
    AftermathResult,
    create_damage_aftermath_fact,
    DamageEffect,
    DamageEffectResult,
    DamageHitTopology,
    DamagePreventionContribution,
    DamagePreventionReason,
    DamagePreventionRuleKind,
    DamageRuleCollection,
    DamageRuleFamily,
    DamageSourceType,
    DamageType,
    DamageZeroLossCause,
    DefeatCleanupPort,
    DefeatCleanupResult,
    DirectTroopLossRequest,
    EventBus,
    EventType,
    ExactRatio,
    FirstAidStateParams,
    FutureBranchKind,
    HitPreventionCategory,
    HitRuleContribution,
    HitRuleKind,
    LineupPosition,
    NormalAttackSystem,
    OfficialStateId,
    OperationLineage,
    RandomSystem,
    ReactionPermissionPolicy,
    RecoveryModelKind,
    RecoveryOpportunityKind,
    RecoveryPotencyContext,
    RuleContributionSource,
    RuleIntentExecutionDescriptor,
    RuleIntentKind,
    SourceType,
    StateApplicationGenerationId,
    StateDamageRuleProvider,
    StateLifecycleSystem,
    TroopType,
    UnitActionStartHook,
    UnitRuntime,
    register_official_state_definitions,
)
from sgs_v2.battle_core.chain_system import ResolvedDamageFact
from sgs_v2.battle_core.cleave_derived_damage_system import (
    CleaveDerivedDamageRequest,
    CleaveDerivedDamageResolver,
)
from sgs_v2.battle_core.damage_instance_coordinator import DamageInstanceCoordinator
from sgs_v2.battle_core.effects import EffectSourceRef
from sgs_v2.battle_core.operation_identity import CleaveEffectId
from sgs_v2.battle_core.rule_intent import AbortedRuleIntentResult
from sgs_v2.battle_core.stage9_state_params import (
    ChainStateParams,
    CounterStateParams,
    DamageShareStateParams,
    DistributionStateParams,
)


class SpyDefeatCleanupPort:
    def __init__(self, lifecycle: StateLifecycleSystem):
        self._lifecycle = lifecycle
        self.call_count = 0
        self.calls: list[tuple[str, Any]] = []

    def commit_defeat(
        self,
        context: BattleContext,
        defeated_unit_id: str,
        defeat_source_ref: Any = None,
    ) -> DefeatCleanupResult:
        self.call_count += 1
        self.calls.append((defeated_unit_id, defeat_source_ref))
        removed = self._lifecycle.clear_owner_on_defeat(context, defeated_unit_id)
        return DefeatCleanupResult(
            defeated_unit_id=defeated_unit_id,
            removed_states=tuple(removed),
            defeat_source_ref=defeat_source_ref,
            round_no=getattr(context, "current_round", 0),
            phase=getattr(context, "current_phase", ""),
        )


def create_test_context(cleanup_port: Any = None) -> tuple[BattleContext, BattleSystems]:
    lifecycle = StateLifecycleSystem()
    defeat_cleanup = cleanup_port or DefeatCleanupPort(lifecycle)
    systems = BattleSystems(
        state_lifecycle_system=lifecycle,
        defeat_cleanup_port=defeat_cleanup,
    )
    context = BattleContext(
        battle_id="test_stage10_phase6_battle",
        units={
            "a1": UnitRuntime(
                "a1", "Attacker_A1", "team_a", 1000, 1000, 200.0, 100.0, 100.0,
                lineup_position=LineupPosition.COMMANDER,
                intelligence=250.0,
                troop_type=TroopType.CAVALRY,
            ),
            "b1": UnitRuntime(
                "b1", "Defender_B1", "team_b", 1000, 1000, 150.0, 120.0, 90.0,
                lineup_position=LineupPosition.COMMANDER,
                intelligence=150.0,
                troop_type=TroopType.SHIELD,
            ),
            "b2": UnitRuntime(
                "b2", "Deputy_B2", "team_b", 1000, 1000, 100.0, 80.0, 80.0,
                lineup_position=LineupPosition.DEPUTY_1,
                intelligence=100.0,
                troop_type=TroopType.SHIELD,
            ),
            "b3": UnitRuntime(
                "b3", "Deputy_B3", "team_b", 1000, 1000, 100.0, 80.0, 80.0,
                lineup_position=LineupPosition.DEPUTY_2,
                intelligence=100.0,
                troop_type=TroopType.SHIELD,
            ),
        },
        event_bus=EventBus(),
        random=RandomSystem(seed=42),
    )
    context.current_round = 1
    context.current_phase = BattlePhase.UNIT_ACTION.value
    # Deterministic enemy targeting to b1
    systems.target_system.random_enemy = lambda ctx, unit: ctx.units["b1"]
    register_official_state_definitions(context.states)
    return context, systems


class TestNormalAttackAftermath:
    def test_normal_attack_resolved_hit_triggers_first_aid(self) -> None:
        context, systems = create_test_context()

        systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.FIRST_AID.value,
            owner_id="b1",
            source_id="b1",
            duration_rounds=2,
            runtime_params=FirstAidStateParams(
                probability=1.0,
                recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT,
                recovery_potency_context=RecoveryPotencyContext(treatment_amount=80),
            ),
        )

        recovery_events = []
        context.event_bus.subscribe(
            EventType.TROOPS_RECOVERED,
            lambda event: recovery_events.append(event),
        )

        execution = systems.normal_attack_system.execute(context, context.units["a1"])

        assert execution.damage is not None
        assert execution.resolution is not None
        assert execution.resolution.actual_target_troop_loss > 0
        assert len(recovery_events) == 1
        assert recovery_events[0].payload["actual_recovery"] == 80


class TestActiveSkillAftermath:
    def test_active_skill_resolved_hit_triggers_first_aid(self) -> None:
        context, systems = create_test_context()

        systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.FIRST_AID.value,
            owner_id="b1",
            source_id="b1",
            duration_rounds=2,
            runtime_params=FirstAidStateParams(
                probability=1.0,
                recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT,
                recovery_potency_context=RecoveryPotencyContext(treatment_amount=120),
            ),
        )

        recovery_events = []
        context.event_bus.subscribe(
            EventType.TROOPS_RECOVERED,
            lambda event: recovery_events.append(event),
        )

        dmg_source_ref = EffectSourceRef(
            stage9_source_type=SourceType.ACTIVE_SKILL,
            source_unit_id="a1",
            source_skill_id="sk_slash",
        )
        desc = RuleIntentExecutionDescriptor(
            intent_kind=RuleIntentKind.EFFECT,
            intent_owner_id="a1",
            state_owner_id="a1",
            target_id="b1",
            source_ref=dmg_source_ref,
        )
        dmg = DamageEffect(
            source_id="a1",
            target_id="b1",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.SKILL,
            source_skill_id="sk_slash",
            coefficient=1.0,
            source_ref=dmg_source_ref,
            execution_descriptor=desc,
        )

        systems.effect_executor.execute(context, dmg)

        assert len(recovery_events) == 1
        assert recovery_events[0].payload["actual_recovery"] == 120


class TestZeroLossResolvedHit:
    def test_settled_zero_loss_hit_triggers_first_aid(self) -> None:
        context, systems = create_test_context()

        systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.WEAKNESS.value,
            owner_id="a1",
            source_id="b1",
            duration_rounds=1,
        )

        systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.FIRST_AID.value,
            owner_id="b1",
            source_id="b1",
            duration_rounds=2,
            runtime_params=FirstAidStateParams(
                probability=1.0,
                recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT,
                recovery_potency_context=RecoveryPotencyContext(treatment_amount=50),
            ),
        )

        aftermath_facts = []
        original_commit = systems.damage_aftermath_port.commit_aftermath

        def spy_commit(ctx, fact):
            aftermath_facts.append(fact)
            return original_commit(ctx, fact)

        systems.damage_aftermath_port.commit_aftermath = spy_commit

        systems.normal_attack_system.execute(context, context.units["a1"])

        assert len(aftermath_facts) == 1
        fact = aftermath_facts[0]
        assert fact.hit_topology == DamageHitTopology.RESOLVED_HIT
        assert fact.actual_target_troop_loss == 0
        assert fact.zero_loss_cause == DamageZeroLossCause.WEAKNESS_ZERO

        # Also verify pure SETTLED_ZERO
        fact_settled = create_damage_aftermath_fact(
            damage_instance_id="dmg_zero_settled",
            target_id="b1",
            source_type=SourceType.NORMAL_ATTACK,
            damage_type=DamageType.WEAPON,
            assigned_target_damage=0,
            actual_target_troop_loss=0,
            target_troops_after=1000,
            target_defeated=False,
            hit_topology=DamageHitTopology.RESOLVED_HIT,
        )
        assert fact_settled.zero_loss_cause == DamageZeroLossCause.SETTLED_ZERO
        res = systems.damage_aftermath_port.commit_aftermath(context, fact_settled)
        assert len(res.opportunity_results) == 1
        assert res.opportunity_results[0].executed


class TestEvasionMissAftermath:
    def test_evasion_miss_creates_zero_opportunity(self) -> None:
        context, systems = create_test_context()

        class MockEvasionRuleProvider:
            provider_key = "mock_evasion"

            def collect(self, ctx, req):
                return DamageRuleCollection(
                    hit_contributions=(
                        HitRuleContribution(
                            kind=HitRuleKind.PROBABILISTIC_PREVENTION,
                            category=HitPreventionCategory.EVASION_LIKE,
                            probability=1.0,
                            source=RuleContributionSource(
                                owner_id="b1",
                                applied_by_unit_id="b1",
                                source_skill_id=None,
                                source_state_id=None,
                                source_state_instance_id=None,
                                origin_key="evasion_1",
                            ),
                            order_key="evasion_1",
                        ),
                    )
                )

        systems.damage_system._rule_provider = MockEvasionRuleProvider()

        systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.FIRST_AID.value,
            owner_id="b1",
            source_id="b1",
            duration_rounds=2,
            runtime_params=FirstAidStateParams(
                probability=1.0,
                recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT,
                recovery_potency_context=RecoveryPotencyContext(treatment_amount=100),
            ),
        )

        recovery_events = []
        context.event_bus.subscribe(
            EventType.TROOPS_RECOVERED,
            lambda event: recovery_events.append(event),
        )

        aftermath_facts = []
        original_commit = systems.damage_aftermath_port.commit_aftermath

        def spy_commit(ctx, fact):
            aftermath_facts.append(fact)
            return original_commit(ctx, fact)

        systems.damage_aftermath_port.commit_aftermath = spy_commit

        systems.normal_attack_system.execute(context, context.units["a1"])

        assert len(aftermath_facts) == 1
        fact = aftermath_facts[0]
        assert fact.hit_topology == DamageHitTopology.NO_RESOLVED_HIT_EVASION_OR_MISS
        assert len(recovery_events) == 0


class TestFatalDamageAftermath:
    def test_fatal_damage_rejects_first_aid_and_commits_defeat_exactly_once(self) -> None:
        context, systems = create_test_context()

        systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.FIRST_AID.value,
            owner_id="b1",
            source_id="b1",
            duration_rounds=2,
            runtime_params=FirstAidStateParams(
                probability=1.0,
                recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT,
                recovery_potency_context=RecoveryPotencyContext(treatment_amount=100),
            ),
        )

        context.units["b1"].troops = 10

        cleanup_invocations = []
        orig_clear = systems.state_lifecycle_system.clear_owner_on_defeat

        def spy_clear(ctx, unit_id):
            cleanup_invocations.append(unit_id)
            return orig_clear(ctx, unit_id)

        systems.state_lifecycle_system.clear_owner_on_defeat = spy_clear

        recovery_events = []
        context.event_bus.subscribe(
            EventType.TROOPS_RECOVERED,
            lambda event: recovery_events.append(event),
        )

        execution = systems.normal_attack_system.execute(context, context.units["a1"])

        assert not context.units["b1"].is_alive
        assert len(recovery_events) == 0
        assert len(cleanup_invocations) == 1
        assert cleanup_invocations[0] == "b1"


class TestPeriodicDOTAftermath:
    def test_periodic_continuous_dot_triggers_first_aid(self) -> None:
        context, systems = create_test_context()

        inst_burn = systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.BURN.value,
            owner_id="b1",
            source_id="a1",
            duration_rounds=1,
        )
        assert inst_burn is not None

        systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.FIRST_AID.value,
            owner_id="b1",
            source_id="b1",
            duration_rounds=2,
            runtime_params=FirstAidStateParams(
                probability=1.0,
                recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT,
                recovery_potency_context=RecoveryPotencyContext(treatment_amount=50),
            ),
        )

        recovery_events = []
        context.event_bus.subscribe(
            EventType.TROOPS_RECOVERED,
            lambda event: recovery_events.append(event),
        )

        context.current_phase = BattlePhase.UNIT_ACTION_START.value
        context.action_progress.set_current_acting_unit("b1")
        context.action_progress.mark_action_start("b1", 1)

        resolution = systems.rule_hook_system.process(context, UnitActionStartHook(1, "b1"))

        assert len(resolution.intent_results) == 1
        assert isinstance(resolution.intent_results[0], DamageEffectResult)
        assert len(recovery_events) == 1
        assert recovery_events[0].payload["actual_recovery"] == 50


class TestFatalDOTAftermath:
    def test_fatal_dot_commits_defeat_once_and_aborts_remainder(self) -> None:
        context, systems = create_test_context()

        systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.BURN.value,
            owner_id="b1",
            source_id="a1",
            duration_rounds=1,
        )
        systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.FLOOD.value,
            owner_id="b1",
            source_id="a1",
            duration_rounds=1,
        )

        context.units["b1"].troops = 5

        cleanup_invocations = []
        orig_clear = systems.state_lifecycle_system.clear_owner_on_defeat

        def spy_clear(ctx, unit_id):
            cleanup_invocations.append(unit_id)
            return orig_clear(ctx, unit_id)

        systems.state_lifecycle_system.clear_owner_on_defeat = spy_clear

        context.current_phase = BattlePhase.UNIT_ACTION_START.value
        context.action_progress.set_current_acting_unit("b1")
        context.action_progress.mark_action_start("b1", 1)

        resolution = systems.rule_hook_system.process(context, UnitActionStartHook(1, "b1"))

        assert not context.units["b1"].is_alive
        assert len(cleanup_invocations) == 1
        assert cleanup_invocations[0] == "b1"
        assert len(resolution.intent_results) == 2
        assert isinstance(resolution.intent_results[0], DamageEffectResult)
        assert isinstance(resolution.intent_results[1], AbortedRuleIntentResult)


class TestCounterAftermath:
    def test_counter_damage_triggers_first_aid(self) -> None:
        context, systems = create_test_context()

        systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.FIRST_AID.value,
            owner_id="a1",
            source_id="a1",
            duration_rounds=2,
            runtime_params=FirstAidStateParams(
                probability=1.0,
                recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT,
                recovery_potency_context=RecoveryPotencyContext(treatment_amount=70),
            ),
        )

        systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.COUNTERATTACK.value,
            owner_id="b1",
            source_id="b1",
            duration_rounds=2,
            runtime_params=CounterStateParams(),
        )

        aftermath_facts = []
        original_commit = systems.damage_aftermath_port.commit_aftermath

        def spy_commit(ctx, fact):
            aftermath_facts.append(fact)
            return original_commit(ctx, fact)

        systems.damage_aftermath_port.commit_aftermath = spy_commit

        recovery_events = []
        context.event_bus.subscribe(
            EventType.TROOPS_RECOVERED,
            lambda event: recovery_events.append(event),
        )

        execution = systems.normal_attack_system.execute(context, context.units["a1"])

        counter_facts = [f for f in aftermath_facts if f.source_type == SourceType.COUNTER]
        assert len(counter_facts) == 1
        assert counter_facts[0].target_id == "a1"
        assert len(recovery_events) == 1
        assert recovery_events[0].target_id == "a1"
        assert recovery_events[0].payload["actual_recovery"] == 70


class TestAssaultAftermath:
    def test_assault_permission_allows_first_aid(self) -> None:
        assert ReactionPermissionPolicy.can_trigger_recovery(SourceType.ASSAULT)

        context, systems = create_test_context()
        context.units["b1"].troops = 850

        systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.FIRST_AID.value,
            owner_id="b1",
            source_id="b1",
            duration_rounds=2,
            runtime_params=FirstAidStateParams(
                probability=1.0,
                recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT,
                recovery_potency_context=RecoveryPotencyContext(treatment_amount=90),
            ),
        )

        fact = create_damage_aftermath_fact(
            damage_instance_id="dmg_assault_1",
            target_id="b1",
            source_type=SourceType.ASSAULT,
            damage_type=DamageType.WEAPON,
            assigned_target_damage=200,
            actual_target_troop_loss=150,
            target_troops_after=850,
            target_defeated=False,
            hit_topology=DamageHitTopology.RESOLVED_HIT,
        )

        res = systems.damage_aftermath_port.commit_aftermath(context, fact)
        assert isinstance(res, AftermathResult)
        assert len(res.opportunity_results) == 1
        assert res.opportunity_results[0].executed
        assert res.opportunity_results[0].resolution.actual_recovery == 90


class TestShareDirectLossExclusion:
    def test_share_direct_loss_never_enters_aftermath(self) -> None:
        context, systems = create_test_context()

        systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.FIRST_AID.value,
            owner_id="b2",
            source_id="b2",
            duration_rounds=2,
            runtime_params=FirstAidStateParams(
                probability=1.0,
                recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT,
                recovery_potency_context=RecoveryPotencyContext(treatment_amount=100),
            ),
        )

        systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.DAMAGE_SHARE.value,
            owner_id="b1",
            source_id="b2",
            duration_rounds=2,
            runtime_params=DamageShareStateParams(
                sharer_id="b2",
                ratio=ExactRatio(3, 10),
            ),
        )

        aftermath_facts = []
        original_commit = systems.damage_aftermath_port.commit_aftermath

        def spy_commit(ctx, fact):
            aftermath_facts.append(fact)
            return original_commit(ctx, fact)

        systems.damage_aftermath_port.commit_aftermath = spy_commit

        execution = systems.normal_attack_system.execute(context, context.units["a1"])

        assert context.units["b2"].troops < 1000
        sharer_aftermath = [f for f in aftermath_facts if f.target_id == "b2"]
        assert len(sharer_aftermath) == 0
        assert all(f.source_type != SourceType.SHARE_DIRECT_LOSS for f in aftermath_facts)


class TestDistributionDirectLossExclusion:
    def test_distribution_direct_loss_never_enters_aftermath(self) -> None:
        context, systems = create_test_context()

        systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.FIRST_AID.value,
            owner_id="b2",
            source_id="b2",
            duration_rounds=2,
            runtime_params=FirstAidStateParams(
                probability=1.0,
                recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT,
                recovery_potency_context=RecoveryPotencyContext(treatment_amount=100),
            ),
        )

        fact = create_damage_aftermath_fact(
            damage_instance_id="dmg_dist_1",
            target_id="b2",
            source_type=SourceType.DISTRIBUTION_DIRECT_LOSS,
            damage_type=DamageType.WEAPON,
            assigned_target_damage=100,
            actual_target_troop_loss=100,
            target_troops_after=900,
            target_defeated=False,
            hit_topology=DamageHitTopology.RESOLVED_HIT,
        )

        res = systems.damage_aftermath_port.commit_aftermath(context, fact)
        assert isinstance(res, AftermathResult)
        assert len(res.opportunity_results) == 1
        assert not res.executed
        assert res.opportunity_results[0].reason == "INELIGIBLE_HIT_OR_SOURCE"

    def test_real_distribution_direct_loss_never_enters_aftermath(self) -> None:
        """Real runtime test: participant in Distribution settlement never calls DamageAftermathPort."""
        context, systems = create_test_context()

        # Distribution state applied on b1
        systems.state_lifecycle_system.apply(
            context,
            state_id="damage_split",
            owner_id="b1",
            source_id="b1",
            duration_rounds=2,
            runtime_params=DistributionStateParams(ratio=ExactRatio(1, 2)),
        )

        # FIRST_AID state applied on b2 (participant in team_b)
        systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.FIRST_AID.value,
            owner_id="b2",
            source_id="b2",
            duration_rounds=2,
            runtime_params=FirstAidStateParams(
                probability=1.0,
                recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT,
                recovery_potency_context=RecoveryPotencyContext(treatment_amount=100),
            ),
        )

        aftermath_facts = []
        original_commit = systems.damage_aftermath_port.commit_aftermath

        def spy_commit(ctx, fact):
            aftermath_facts.append(fact)
            return original_commit(ctx, fact)

        systems.damage_aftermath_port.commit_aftermath = spy_commit

        recovery_events = []
        context.event_bus.subscribe(
            EventType.TROOPS_RECOVERED,
            lambda event: recovery_events.append(event),
        )

        # Normal attack on b1 triggers Distribution transaction
        systems.normal_attack_system.execute(context, context.units["a1"])

        # Real participant b2 suffered real DirectTroopLoss
        assert context.units["b2"].troops < 1000
        # Participant b2 NEVER had aftermath called
        b2_aftermath = [f for f in aftermath_facts if f.target_id == "b2"]
        assert len(b2_aftermath) == 0
        # No distribution direct loss fact ever enters aftermath
        assert all(f.source_type != SourceType.DISTRIBUTION_DIRECT_LOSS for f in aftermath_facts)
        # b2 never recovered
        b2_recoveries = [e for e in recovery_events if e.target_id == "b2"]
        assert len(b2_recoveries) == 0


class TestChainTrueFeedbackExclusion:
    def test_chain_feedback_blocked_from_aftermath(self) -> None:
        assert not ReactionPermissionPolicy.can_trigger_recovery(SourceType.CHAIN_TRUE_FEEDBACK)

        context, systems = create_test_context()

        systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.FIRST_AID.value,
            owner_id="b2",
            source_id="b2",
            duration_rounds=2,
            runtime_params=FirstAidStateParams(
                probability=1.0,
                recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT,
                recovery_potency_context=RecoveryPotencyContext(treatment_amount=100),
            ),
        )

        fact = create_damage_aftermath_fact(
            damage_instance_id="dmg_chain_1",
            target_id="b2",
            source_type=SourceType.CHAIN_TRUE_FEEDBACK,
            damage_type=DamageType.STRATEGY,
            assigned_target_damage=150,
            actual_target_troop_loss=150,
            target_troops_after=850,
            target_defeated=False,
            hit_topology=DamageHitTopology.RESOLVED_HIT,
        )

        res = systems.damage_aftermath_port.commit_aftermath(context, fact)
        assert isinstance(res, AftermathResult)
        assert len(res.opportunity_results) == 1
        assert not res.executed
        assert res.opportunity_results[0].reason == "INELIGIBLE_HIT_OR_SOURCE"

    def test_real_chain_true_feedback_never_enters_aftermath(self) -> None:
        """Real runtime test: victim in Chain true feedback never calls DamageAftermathPort."""
        context, systems = create_test_context()

        # Link b1 and b2
        systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.CHAIN_LINK.value,
            owner_id="b1",
            source_id="a1",
            duration_rounds=2,
            runtime_params=ChainStateParams(ratio=ExactRatio(1, 2)),
        )
        systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.CHAIN_LINK.value,
            owner_id="b2",
            source_id="a1",
            duration_rounds=2,
            runtime_params=ChainStateParams(ratio=ExactRatio(1, 2)),
        )

        # FIRST_AID state applied on b2
        systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.FIRST_AID.value,
            owner_id="b2",
            source_id="b2",
            duration_rounds=2,
            runtime_params=FirstAidStateParams(
                probability=1.0,
                recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT,
                recovery_potency_context=RecoveryPotencyContext(treatment_amount=100),
            ),
        )

        aftermath_facts = []
        original_commit = systems.damage_aftermath_port.commit_aftermath

        def spy_commit(ctx, fact):
            aftermath_facts.append(fact)
            return original_commit(ctx, fact)

        systems.damage_aftermath_port.commit_aftermath = spy_commit

        recovery_events = []
        context.event_bus.subscribe(
            EventType.TROOPS_RECOVERED,
            lambda event: recovery_events.append(event),
        )

        # Execute Chain traversal on trigger b1 -> candidate b2
        fact = ResolvedDamageFact(
            damage_instance_id=context.id_allocator.allocate_damage_instance_id(),
            target_id="b1",
            lineage=OperationLineage(
                root_action_id=None,
                parent_normal_attack_id=None,
                parent_damage_instance_id=None,
                source_type=SourceType.NORMAL_ATTACK,
                physical_attacker="a1",
                physical_skill=None,
                credit_owner="a1",
            ),
            damage_type=DamageType.WEAPON,
            assigned_target_damage=200,
            actual_target_troop_loss=200,
        )
        permit = systems.future_admission_gate.request_admission(
            FutureBranchKind.CHAIN_TRAVERSAL, str(fact.damage_instance_id)
        )
        assert permit is not None
        traversal = systems.chain_system.create_traversal(context, fact, permit=permit)
        results = systems.chain_system.execute(context, traversal)

        assert len(results) == 1
        assert results[0].actual_troop_loss > 0
        assert context.units["b2"].troops < 1000
        # b2 chain feedback NEVER invoked aftermath
        b2_aftermath = [f for f in aftermath_facts if f.target_id == "b2"]
        assert len(b2_aftermath) == 0
        b2_recoveries = [e for e in recovery_events if e.target_id == "b2"]
        assert len(b2_recoveries) == 0


class TestCleaveOrderingTrace:
    def test_cleave_ordering_settle_share_aftermath_attacker_recovery_callbacks(self) -> None:
        ordering_trace: list[str] = []

        context, systems = create_test_context()

        systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.DAMAGE_SHARE.value,
            owner_id="b2",
            source_id="b3",
            duration_rounds=2,
            runtime_params=DamageShareStateParams(
                sharer_id="b3",
                ratio=ExactRatio(2, 10),
            ),
        )

        systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.FIRST_AID.value,
            owner_id="b2",
            source_id="b2",
            duration_rounds=2,
            runtime_params=FirstAidStateParams(
                probability=1.0,
                recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT,
                recovery_potency_context=RecoveryPotencyContext(treatment_amount=60),
            ),
        )

        orig_apply = systems.troop_system.apply_damage
        def spy_apply_damage(unit, amount):
            if unit.unit_id == "b2":
                ordering_trace.append("TARGET_SETTLED")
            elif unit.unit_id == "b3":
                ordering_trace.append("SHARER_DIRECT_LOSS")
            return orig_apply(unit, amount)
        systems.troop_system.apply_damage = spy_apply_damage

        orig_commit_aftermath = systems.damage_aftermath_port.commit_aftermath
        def spy_aftermath(ctx, fact):
            ordering_trace.append("TARGET_AFTERMATH")
            return orig_commit_aftermath(ctx, fact)
        systems.damage_aftermath_port.commit_aftermath = spy_aftermath

        def spy_attacker_recovery(ctx, rec):
            ordering_trace.append("ATTACKER_RECOVERY")
        systems.cleave_derived_damage_resolver._attacker_recovery = spy_attacker_recovery

        orig_accept = systems.damage_callbacks.accept
        def spy_callbacks(ctx, fact, **kwargs):
            ordering_trace.append("DAMAGE_CALLBACKS")
            return orig_accept(ctx, fact, **kwargs)
        systems.damage_callbacks.accept = spy_callbacks

        request = CleaveDerivedDamageRequest(
            damage_instance_id=context.id_allocator.allocate_damage_instance_id(),
            cleave_effect_id=CleaveEffectId("clv_1"),
            lineage=OperationLineage(
                root_action_id=None,
                parent_normal_attack_id=None,
                parent_damage_instance_id=None,
                source_type=SourceType.CLEAVE,
                physical_attacker="a1",
                physical_skill="sk_cleave",
                credit_owner="a1",
            ),
            damage_type=DamageType.WEAPON,
            base_amount=200,
            ratio=ExactRatio(1, 1),
            secondary_target="b2",
        )

        res = systems.cleave_derived_damage_resolver._resolve(context, None, request)

        assert ordering_trace == [
            "TARGET_SETTLED",
            "SHARER_DIRECT_LOSS",
            "TARGET_AFTERMATH",
            "ATTACKER_RECOVERY",
            "DAMAGE_CALLBACKS",
        ]


class TestMultiHitAftermath:
    def test_multi_hit_three_surviving_hits_produce_three_independent_recoveries(self) -> None:
        """Section 8: 3 resolved hits produce 3 independent FIRST_AID opportunities and executions."""
        context, systems = create_test_context()

        systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.FIRST_AID.value,
            owner_id="b1",
            source_id="b1",
            duration_rounds=2,
            runtime_params=FirstAidStateParams(
                probability=1.0,
                recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT,
                recovery_potency_context=RecoveryPotencyContext(treatment_amount=50),
            ),
        )

        aftermath_results = []
        original_commit = systems.damage_aftermath_port.commit_aftermath

        def spy_commit(ctx, fact):
            res = original_commit(ctx, fact)
            aftermath_results.append(res)
            return res

        systems.damage_aftermath_port.commit_aftermath = spy_commit

        chance_calls = 0
        orig_chance = context.random.chance

        def spy_chance(prob):
            nonlocal chance_calls
            chance_calls += 1
            return orig_chance(prob)

        context.random.chance = spy_chance

        recovery_events = []
        context.event_bus.subscribe(
            EventType.TROOPS_RECOVERED,
            lambda event: recovery_events.append(event),
        )

        dmg_source_ref = EffectSourceRef(
            stage9_source_type=SourceType.ACTIVE_SKILL,
            source_unit_id="a1",
            source_skill_id="sk_multihit",
        )

        # Execute 3 separate DamageEffect hits
        for i in range(1, 4):
            desc = RuleIntentExecutionDescriptor(
                intent_kind=RuleIntentKind.EFFECT,
                intent_owner_id="a1",
                state_owner_id="a1",
                target_id="b1",
                source_ref=dmg_source_ref,
            )
            dmg = DamageEffect(
                source_id="a1",
                target_id="b1",
                damage_type=DamageType.WEAPON,
                source_type=DamageSourceType.SKILL,
                source_skill_id="sk_multihit",
                coefficient=0.8,
                source_ref=dmg_source_ref,
                execution_descriptor=desc,
            )
            systems.effect_executor.execute(context, dmg)
            assert context.units["b1"].is_alive

        # Formal assertions per Section 8
        assert len(aftermath_results) == 3, "DamageAftermathPort calls must equal 3"
        for idx, res in enumerate(aftermath_results):
            assert len(res.opportunity_results) == 1, f"Hit {idx+1} must produce 1 FIRST_AID opportunity"
            assert res.opportunity_results[0].executed is True, f"Hit {idx+1} opportunity must be admitted and executed"
        assert chance_calls == 3, "RandomSystem.chance calls must equal 3 (one draw per admitted opportunity)"
        assert len(recovery_events) == 3, "Recovery executions must equal 3"
        for event in recovery_events:
            assert event.payload["actual_recovery"] == 50

    def test_multi_hit_zero_loss_second_hit_still_triggers_independent_first_aid(self) -> None:
        """Section 9: Hit 2 with actual loss = 0 still produces an independent FIRST_AID opportunity."""
        context, systems = create_test_context()

        systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.FIRST_AID.value,
            owner_id="b1",
            source_id="b1",
            duration_rounds=2,
            runtime_params=FirstAidStateParams(
                probability=1.0,
                recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT,
                recovery_potency_context=RecoveryPotencyContext(treatment_amount=50),
            ),
        )
        context.units["b1"].troops = 800

        aftermath_results = []
        original_commit = systems.damage_aftermath_port.commit_aftermath

        def spy_commit(ctx, fact):
            res = original_commit(ctx, fact)
            aftermath_results.append(res)
            return res

        systems.damage_aftermath_port.commit_aftermath = spy_commit

        # Hit 1: Positive loss
        fact1 = create_damage_aftermath_fact(
            damage_instance_id="dmg_multi_1",
            target_id="b1",
            source_type=SourceType.ACTIVE_SKILL,
            damage_type=DamageType.WEAPON,
            assigned_target_damage=100,
            actual_target_troop_loss=100,
            target_troops_after=700,
            target_defeated=False,
            hit_topology=DamageHitTopology.RESOLVED_HIT,
        )
        systems.damage_aftermath_port.commit_aftermath(context, fact1)

        # Hit 2: Zero loss (settled zero)
        fact2 = create_damage_aftermath_fact(
            damage_instance_id="dmg_multi_2",
            target_id="b1",
            source_type=SourceType.ACTIVE_SKILL,
            damage_type=DamageType.WEAPON,
            assigned_target_damage=0,
            actual_target_troop_loss=0,
            target_troops_after=750,
            target_defeated=False,
            hit_topology=DamageHitTopology.RESOLVED_HIT,
            zero_loss_cause=DamageZeroLossCause.SETTLED_ZERO,
        )
        systems.damage_aftermath_port.commit_aftermath(context, fact2)

        # Hit 3: Positive loss
        fact3 = create_damage_aftermath_fact(
            damage_instance_id="dmg_multi_3",
            target_id="b1",
            source_type=SourceType.ACTIVE_SKILL,
            damage_type=DamageType.WEAPON,
            assigned_target_damage=100,
            actual_target_troop_loss=100,
            target_troops_after=700,
            target_defeated=False,
            hit_topology=DamageHitTopology.RESOLVED_HIT,
        )
        systems.damage_aftermath_port.commit_aftermath(context, fact3)

        assert len(aftermath_results) == 3
        # Every hit, including zero loss hit 2, gets an admitted and executed FIRST_AID opportunity
        for idx, res in enumerate(aftermath_results):
            assert len(res.opportunity_results) == 1, f"Hit {idx+1} must produce 1 opportunity"
            assert res.opportunity_results[0].executed is True, f"Hit {idx+1} must execute recovery"


class TestAdmissionOwnershipSingleTruth:
    def test_reaction_permission_policy_queried_solely_by_recovery_opportunity_system(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Section 15: ReactionPermissionPolicy is queried exactly once per opportunity by RecoveryOpportunitySystem."""
        context, systems = create_test_context()

        systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.FIRST_AID.value,
            owner_id="b1",
            source_id="b1",
            duration_rounds=2,
            runtime_params=FirstAidStateParams(
                probability=1.0,
                recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT,
                recovery_potency_context=RecoveryPotencyContext(treatment_amount=50),
            ),
        )

        orig_can_trigger = ReactionPermissionPolicy.can_trigger_recovery
        query_log: list[SourceType] = []

        def spy_can_trigger(source_type: SourceType) -> bool:
            query_log.append(source_type)
            return orig_can_trigger(source_type)

        monkeypatch.setattr(ReactionPermissionPolicy, "can_trigger_recovery", staticmethod(spy_can_trigger))

        # Single normal attack damage event
        systems.normal_attack_system.execute(context, context.units["a1"])

        # Exactly ONE call across the entire aftermath + recovery pipeline
        assert len(query_log) == 1
        assert query_log[0] == SourceType.NORMAL_ATTACK


class TestExactlyOnceAftermathInvocation:
    def test_single_damage_event_invokes_aftermath_exactly_once(self) -> None:
        context, systems = create_test_context()

        commit_counter = 0
        orig_commit = systems.damage_aftermath_port.commit_aftermath

        def counting_commit(ctx, fact):
            nonlocal commit_counter
            commit_counter += 1
            return orig_commit(ctx, fact)

        systems.damage_aftermath_port.commit_aftermath = counting_commit

        systems.normal_attack_system.execute(context, context.units["a1"])

        assert commit_counter == 1


class TestDefeatCleanupConformanceSpy:
    def test_defeat_cleanup_committed_exactly_once_on_unit_death(self) -> None:
        # 1. Standard damage fatal
        spy1 = SpyDefeatCleanupPort(StateLifecycleSystem())
        c1, s1 = create_test_context(cleanup_port=spy1)
        c1.units["b1"].troops = 10
        s1.normal_attack_system.execute(c1, c1.units["a1"])
        assert spy1.call_count == 1
        assert spy1.calls[0][0] == "b1"

        # 2. Periodic DOT fatal
        spy2 = SpyDefeatCleanupPort(StateLifecycleSystem())
        c2, s2 = create_test_context(cleanup_port=spy2)
        s2.state_lifecycle_system.apply(c2, state_id=OfficialStateId.BURN.value, owner_id="b1", source_id="a1", duration_rounds=1)
        c2.units["b1"].troops = 10
        c2.current_phase = BattlePhase.UNIT_ACTION_START.value
        c2.action_progress.set_current_acting_unit("b1")
        c2.action_progress.mark_action_start("b1", 1)
        s2.rule_hook_system.process(c2, UnitActionStartHook(1, "b1"))
        assert spy2.call_count == 1
        assert spy2.calls[0][0] == "b1"

        # 3. Cleave target fatal
        spy3 = SpyDefeatCleanupPort(StateLifecycleSystem())
        c3, s3 = create_test_context(cleanup_port=spy3)
        c3.units["b2"].troops = 10
        req = CleaveDerivedDamageRequest(
            damage_instance_id=c3.id_allocator.allocate_damage_instance_id(),
            cleave_effect_id=CleaveEffectId("clv_conformance"),
            lineage=OperationLineage(None, None, None, SourceType.CLEAVE, "a1", "sk", "a1"),
            damage_type=DamageType.WEAPON,
            base_amount=100,
            ratio=ExactRatio(1, 1),
            secondary_target="b2",
        )
        s3.finalization_coordinator._active_damage_instances[req.damage_instance_id] = None
        s3.cleave_derived_damage_resolver._resolve(c3, None, req)
        assert spy3.call_count == 1
        assert spy3.calls[0][0] == "b2"

        # 4. Distribution participant fatal
        spy4 = SpyDefeatCleanupPort(StateLifecycleSystem())
        c4, s4 = create_test_context(cleanup_port=spy4)
        s4.state_lifecycle_system.apply(
            c4,
            state_id="damage_split",
            owner_id="b1",
            source_id="b1",
            duration_rounds=2,
            runtime_params=DistributionStateParams(ratio=ExactRatio(1, 2)),
        )
        c4.units["b2"].troops = 5  # dies from direct loss
        s4.normal_attack_system.execute(c4, c4.units["a1"])
        assert not c4.units["b2"].is_alive
        b2_calls = [call for call in spy4.calls if call[0] == "b2"]
        assert len(b2_calls) == 1, "Distribution participant death must commit DefeatCleanup exactly once"


class TestFullTroopAftermath:
    def test_full_troop_target_aftermath_reaches_recovery_evaluation(self) -> None:
        context, systems = create_test_context()

        assert context.units["b1"].troops == context.units["b1"].max_troops

        systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.FIRST_AID.value,
            owner_id="b1",
            source_id="b1",
            duration_rounds=2,
            runtime_params=FirstAidStateParams(
                probability=1.0,
                recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT,
                recovery_potency_context=RecoveryPotencyContext(treatment_amount=50),
            ),
        )

        fact = create_damage_aftermath_fact(
            damage_instance_id="dmg_full_1",
            target_id="b1",
            source_type=SourceType.NORMAL_ATTACK,
            damage_type=DamageType.WEAPON,
            assigned_target_damage=0,
            actual_target_troop_loss=0,
            target_troops_after=1000,
            target_defeated=False,
            hit_topology=DamageHitTopology.RESOLVED_HIT,
            zero_loss_cause=DamageZeroLossCause.SETTLED_ZERO,
        )

        res = systems.damage_aftermath_port.commit_aftermath(context, fact)
        assert isinstance(res, AftermathResult)
        assert len(res.opportunity_results) == 1
        assert res.opportunity_results[0].executed


class TestGenerationProvenance:
    def test_damage_source_generation_and_recovery_generation_are_preserved(self) -> None:
        context, systems = create_test_context()

        inst_burn = systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.BURN.value,
            owner_id="b1",
            source_id="a1",
            duration_rounds=1,
        )
        gen_burn = inst_burn.current_generation_id

        inst_fa = systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.FIRST_AID.value,
            owner_id="b1",
            source_id="b1",
            duration_rounds=2,
            runtime_params=FirstAidStateParams(
                probability=1.0,
                recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT,
                recovery_potency_context=RecoveryPotencyContext(treatment_amount=30),
            ),
        )
        gen_fa = inst_fa.current_generation_id
        assert gen_burn != gen_fa

        captured_facts = []
        orig_commit = systems.damage_aftermath_port.commit_aftermath
        def spy_commit(ctx, fact):
            captured_facts.append(fact)
            return orig_commit(ctx, fact)
        systems.damage_aftermath_port.commit_aftermath = spy_commit

        context.current_phase = BattlePhase.UNIT_ACTION_START.value
        context.action_progress.set_current_acting_unit("b1")
        context.action_progress.mark_action_start("b1", 1)

        resolution = systems.rule_hook_system.process(context, UnitActionStartHook(1, "b1"))

        assert len(captured_facts) == 1
        fact = captured_facts[0]
        assert fact.source_state_generation == gen_burn

        res = resolution.intent_results[0]
        assert isinstance(res, DamageEffectResult)
