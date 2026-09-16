from __future__ import annotations

import unittest.mock
import pytest
from typing import Any

from sgs_v2.battle_core import (
    AbortedRuleIntentResult,
    ActionProgressTracker,
    BattleContext,
    BattlePhase,
    BattleSystems,
    DamageAftermathFact,
    DamageCalculationBasis,
    DamageDefensePolicy,
    DamageEffect,
    DamageEffectResult,
    DamageHitTopology,
    DamageModifierPhase,
    DamageResolutionResult,
    DamageSourceType,
    DamageType,
    DamageZeroLossCause,
    EffectExecutionResult,
    EffectExecutor,
    EffectSourceRef,
    EventBus,
    EventType,
    ExecutionRightDecisionKind,
    ExecutionRightReason,
    ExecutionRightSystem,
    LineupPosition,
    OfficialStateId,
    OperationIdAllocator,
    PersistentLifecycleWindow,
    PersistentSourceSkillGate,
    PersistentSourceSkillGateMode,
    RandomSystem,
    ReactionPermissionPolicy,
    RecoverEffect,
    RecoveryModelKind,
    RecoveryOpportunity,
    RecoveryOpportunityKind,
    RecoveryOpportunityResult,
    RecoveryOpportunitySystem,
    RecoveryPreventedResult,
    RecoveryPreventionReason,
    RecoveryResolvedResult,
    RecoverySystem,
    RoundStartHook,
    RuleHookSystem,
    RuleIntent,
    RuleIntentExecutionDescriptor,
    RuleIntentKind,
    SkillDefinition,
    SkillRuntime,
    SkillRuntimeRegistry,
    SkillSlot,
    SkillTargetMode,
    SourceType,
    StateApplicationGenerationId,
    StateDefinition,
    StateInstance,
    StateLifecycleSystem,
    StateRegistry,
    TroopType,
    UnitActionStartHook,
    UnitRuntime,
    register_official_state_definitions,
)
from sgs_v2.battle_core.skill_definition import DamageSkillEffectSpec
from sgs_v2.battle_core.stage10_state_params import (
    FirstAidStateParams,
    RecoveryPotencyContext,
    RecuperationStateParams,
)


def create_test_context() -> tuple[BattleContext, BattleSystems]:
    systems = BattleSystems()
    context = BattleContext(
        battle_id="test_stage10_phase5_battle",
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
        },
        event_bus=EventBus(),
        random=RandomSystem(seed=42),
    )
    register_official_state_definitions(context.states)
    return context, systems


def register_mock_skill_runtime(
    context: BattleContext,
    owner_id: str,
    slot: SkillSlot = SkillSlot.LEARNED_1,
    enabled: bool = True,
    skill_id: str = "sk_test",
) -> SkillRuntime:
    defn = SkillDefinition(
        skill_id=skill_id,
        name="Mock Skill",
        activation_rate=1.0,
        target_mode=SkillTargetMode.SINGLE_RANDOM_ENEMY,
        effect_specs=(DamageSkillEffectSpec(damage_type=DamageType.WEAPON, coefficient=1.0),),
    )
    rt = SkillRuntime(
        skill_slot=slot,
        owner_id=owner_id,
        definition=defn,
    )
    rt.enabled = enabled
    context.skill_runtimes.register(rt)
    return rt


def create_test_aftermath_fact(
    damage_instance_id: str = "dmg_1",
    target_id: str = "b1",
    source_type: SourceType = SourceType.NORMAL_ATTACK,
    damage_type: DamageType = DamageType.WEAPON,
    assigned_target_damage: int = 100,
    actual_target_troop_loss: int = 100,
    target_troops_after: int = 700,
    target_defeated: bool = False,
    hit_topology: DamageHitTopology = DamageHitTopology.RESOLVED_HIT,
    zero_loss_cause: DamageZeroLossCause | None = None,
    source_state_generation: StateApplicationGenerationId | None = None,
) -> DamageAftermathFact:
    return DamageAftermathFact(
        damage_instance_id=damage_instance_id,
        target_id=target_id,
        source_type=source_type,
        damage_type=damage_type,
        assigned_target_damage=assigned_target_damage,
        actual_target_troop_loss=actual_target_troop_loss,
        target_troops_after=target_troops_after,
        target_defeated=target_defeated,
        hit_topology=hit_topology,
        zero_loss_cause=zero_loss_cause,
        source_state_generation=source_state_generation,
    )


def make_first_aid_opportunity(
    source_actor_id: str,
    target_actor_id: str,
    source_skill_id: str,
    aftermath_fact: DamageAftermathFact,
    recovery_amount: int = 100,
    probability: float = 1.0,
    source_skill_slot: SkillSlot = SkillSlot.LEARNED_1,
    source_skill_gate: PersistentSourceSkillGate | None = None,
    source_generation_id: StateApplicationGenerationId | None = None,
    state_instance_id: str | None = None,
) -> RecoveryOpportunity:
    desc = RuleIntentExecutionDescriptor(
        intent_kind=RuleIntentKind.RECOVERY_OPPORTUNITY,
        intent_owner_id=target_actor_id,
        state_owner_id=source_actor_id,
        target_id=target_actor_id,
        source_ref=EffectSourceRef(
            stage9_source_type=aftermath_fact.source_type,
            source_unit_id=source_actor_id,
            source_skill_id=source_skill_id,
            source_skill_slot=source_skill_slot,
        ),
        state_instance_id=state_instance_id,
        state_generation_id=source_generation_id,
        execution_domain="STATE_RESOLUTION",
    )
    return RecoveryOpportunity(
        opportunity_kind=RecoveryOpportunityKind.FIRST_AID_AFTER_DAMAGE,
        execution_descriptor=desc,
        probability=probability,
        recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT,
        recovery_potency_context=RecoveryPotencyContext(treatment_amount=recovery_amount),
        source_skill_gate=source_skill_gate or PersistentSourceSkillGate.always_active(),
        aftermath_fact=aftermath_fact,
    )


def make_recuperation_opportunity(
    source_actor_id: str,
    target_actor_id: str,
    source_skill_id: str,
    recovery_amount: int = 100,
    probability: float = 1.0,
    source_skill_slot: SkillSlot = SkillSlot.LEARNED_1,
    source_skill_gate: PersistentSourceSkillGate | None = None,
    source_generation_id: StateApplicationGenerationId | None = None,
    state_instance_id: str | None = None,
) -> RecoveryOpportunity:
    desc = RuleIntentExecutionDescriptor(
        intent_kind=RuleIntentKind.RECOVERY_OPPORTUNITY,
        intent_owner_id=target_actor_id,
        state_owner_id=source_actor_id,
        target_id=target_actor_id,
        source_ref=EffectSourceRef(
            stage9_source_type=SourceType.ACTIVE_SKILL,
            source_unit_id=source_actor_id,
            source_skill_id=source_skill_id,
            source_skill_slot=source_skill_slot,
        ),
        state_instance_id=state_instance_id,
        state_generation_id=source_generation_id,
        execution_domain="STATE_RESOLUTION",
    )
    return RecoveryOpportunity(
        opportunity_kind=RecoveryOpportunityKind.RECUPERATION_ACTION_START,
        execution_descriptor=desc,
        probability=probability,
        recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT,
        recovery_potency_context=RecoveryPotencyContext(treatment_amount=recovery_amount),
        source_skill_gate=source_skill_gate or PersistentSourceSkillGate.always_active(),
        aftermath_fact=None,
    )


# ==============================================================================
# 1. Hardening H02: RECUPERATION Isolation & Invariant Rejection
# ==============================================================================

class TestHardeningH02RecuperationIsolation:
    def test_recuperation_does_not_query_aftermath_or_reaction_permission(self) -> None:
        context, systems = create_test_context()
        recov_sys = systems.recovery_opportunity_system

        # b1 is damaged to 500
        context.units["b1"].troops = 500

        opp = make_recuperation_opportunity(
            source_actor_id="a1",
            target_actor_id="b1",
            source_skill_id="sk_recup",
            recovery_amount=100,
            probability=1.0,
            source_skill_slot=SkillSlot.LEARNED_1,
        )

        assert opp.aftermath_fact is None
        assert opp.opportunity_kind == RecoveryOpportunityKind.RECUPERATION_ACTION_START

        with unittest.mock.patch.object(
            ReactionPermissionPolicy, "can_trigger_recovery", wraps=ReactionPermissionPolicy.can_trigger_recovery
        ) as mock_policy:
            result = recov_sys.execute(context, opp)

            # S10-FG-H02 invariant: ReactionPermissionPolicy MUST NOT be called!
            mock_policy.assert_not_called()

        assert result.executed is True
        assert result.resolution is not None
        assert result.resolution.actual_recovery == 100
        assert context.units["b1"].troops == 600

    def test_recuperation_rejects_non_none_aftermath_fact_invariant(self) -> None:
        dummy_aftermath = create_test_aftermath_fact(
            damage_instance_id="dmg_test",
            target_id="b1",
            source_type=SourceType.ACTIVE_SKILL,
            assigned_target_damage=100,
            actual_target_troop_loss=100,
            target_troops_after=500,
            target_defeated=False,
            hit_topology=DamageHitTopology.RESOLVED_HIT,
        )

        # 1) Direct constructor rejection
        with pytest.raises(ValueError, match="S10-FG-H02"):
            RecoveryOpportunity(
                opportunity_kind=RecoveryOpportunityKind.RECUPERATION_ACTION_START,
                execution_descriptor=RuleIntentExecutionDescriptor(
                    intent_kind=RuleIntentKind.RECOVERY_OPPORTUNITY,
                    intent_owner_id="b1",
                    state_owner_id="a1",
                    target_id="b1",
                ),
                probability=1.0,
                recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT,
                recovery_potency_context=RecoveryPotencyContext(treatment_amount=100),
                aftermath_fact=dummy_aftermath,
            )

        # 2) Execution rejection if somehow passed to execute()
        context, systems = create_test_context()
        recov_sys = systems.recovery_opportunity_system
        valid_opp = make_recuperation_opportunity(
            source_actor_id="a1",
            target_actor_id="b1",
            source_skill_id="sk_test",
            recovery_amount=100,
            probability=1.0,
        )
        with pytest.raises(ValueError, match="S10-FG-H02"):
            recov_sys.execute(context, valid_opp, aftermath_fact=dummy_aftermath)


# ==============================================================================
# 2. First Aid Admission Path: Resolved Hits, Zero-Loss Causes, Exclusions
# ==============================================================================

class TestFirstAidAdmissionPath:
    def test_first_aid_resolved_hit_positive_loss_admitted(self) -> None:
        context, systems = create_test_context()
        recov_sys = systems.recovery_opportunity_system
        context.units["b1"].troops = 800

        aftermath = create_test_aftermath_fact(
            damage_instance_id="dmg_1",
            target_id="b1",
            source_type=SourceType.NORMAL_ATTACK,
            assigned_target_damage=200,
            actual_target_troop_loss=200,
            target_troops_after=800,
            target_defeated=False,
            hit_topology=DamageHitTopology.RESOLVED_HIT,
        )
        opp = make_first_aid_opportunity(
            source_actor_id="b1",
            target_actor_id="b1",
            source_skill_id="sk_first_aid",
            aftermath_fact=aftermath,
            recovery_amount=100,
            probability=1.0,
        )

        result = recov_sys.execute(context, opp)
        assert result.executed is True
        assert result.resolution is not None
        assert result.resolution.actual_recovery == 100
        assert context.units["b1"].troops == 900

    @pytest.mark.parametrize(
        "zero_loss_cause",
        [
            DamageZeroLossCause.WEAKNESS_ZERO,
            DamageZeroLossCause.BARRIER_ZERO,
            DamageZeroLossCause.SETTLED_ZERO,
        ],
    )
    def test_first_aid_zero_loss_causes_admitted(
        self, zero_loss_cause: DamageZeroLossCause
    ) -> None:
        context, systems = create_test_context()
        recov_sys = systems.recovery_opportunity_system
        context.units["b1"].troops = 800

        aftermath = create_test_aftermath_fact(
            damage_instance_id="dmg_zero",
            target_id="b1",
            source_type=SourceType.NORMAL_ATTACK,
            assigned_target_damage=0,
            actual_target_troop_loss=0,
            target_troops_after=800,
            target_defeated=False,
            hit_topology=DamageHitTopology.RESOLVED_HIT,
            zero_loss_cause=zero_loss_cause,
        )
        opp = make_first_aid_opportunity(
            source_actor_id="b1",
            target_actor_id="b1",
            source_skill_id="sk_first_aid",
            aftermath_fact=aftermath,
            recovery_amount=50,
            probability=1.0,
        )

        result = recov_sys.execute(context, opp)
        assert result.executed is True
        assert result.resolution is not None
        assert result.resolution.actual_recovery == 50
        assert context.units["b1"].troops == 850

    def test_first_aid_evaded_hit_excluded(self) -> None:
        context, systems = create_test_context()
        recov_sys = systems.recovery_opportunity_system
        context.units["b1"].troops = 800

        aftermath = create_test_aftermath_fact(
            damage_instance_id="dmg_evaded",
            target_id="b1",
            source_type=SourceType.NORMAL_ATTACK,
            assigned_target_damage=0,
            actual_target_troop_loss=0,
            target_troops_after=800,
            target_defeated=False,
            hit_topology=DamageHitTopology.NO_RESOLVED_HIT_EVASION_OR_MISS,
        )
        opp = make_first_aid_opportunity(
            source_actor_id="b1",
            target_actor_id="b1",
            source_skill_id="sk_first_aid",
            aftermath_fact=aftermath,
            recovery_amount=50,
            probability=1.0,
        )

        result = recov_sys.execute(context, opp)
        assert result.executed is False
        assert result.reason == "INELIGIBLE_HIT_OR_SOURCE"
        assert context.units["b1"].troops == 800

    def test_first_aid_fatal_hit_excluded_cannot_revive(self) -> None:
        context, systems = create_test_context()
        recov_sys = systems.recovery_opportunity_system
        context.units["b1"].troops = 0

        aftermath = create_test_aftermath_fact(
            damage_instance_id="dmg_fatal",
            target_id="b1",
            source_type=SourceType.NORMAL_ATTACK,
            assigned_target_damage=1000,
            actual_target_troop_loss=1000,
            target_troops_after=0,
            target_defeated=True,
            hit_topology=DamageHitTopology.RESOLVED_HIT,
        )
        opp = make_first_aid_opportunity(
            source_actor_id="b1",
            target_actor_id="b1",
            source_skill_id="sk_first_aid",
            aftermath_fact=aftermath,
            recovery_amount=500,
            probability=1.0,
        )

        result = recov_sys.execute(context, opp)
        # Target is dead, gate 1 or gate 2 rejects; NO revival!
        assert result.executed is False
        assert result.reason == "TARGET_DEFEATED"
        assert context.units["b1"].troops == 0
        assert not context.units["b1"].is_alive


# ==============================================================================
# 3. Source Family Permission Matrix (Stage9 Addendum §4.2 & §4.3)
# ==============================================================================

class TestSourceFamilyPermissionMatrix:
    @pytest.mark.parametrize(
        "admitted_source",
        [
            SourceType.NORMAL_ATTACK,
            SourceType.ACTIVE_SKILL,
            SourceType.PERIODIC_DAMAGE,
            SourceType.CLEAVE,
            SourceType.COUNTER,
            SourceType.ASSAULT,  # Explicitly admitted per Stage9 Addendum §4.3
        ],
    )
    def test_admitted_sources(self, admitted_source: SourceType) -> None:
        assert ReactionPermissionPolicy.can_trigger_recovery(admitted_source) is True

        context, systems = create_test_context()
        recov_sys = systems.recovery_opportunity_system
        context.units["b1"].troops = 800

        aftermath = create_test_aftermath_fact(
            damage_instance_id="dmg_adm",
            target_id="b1",
            source_type=admitted_source,
            assigned_target_damage=100,
            actual_target_troop_loss=100,
            target_troops_after=800,
            target_defeated=False,
            hit_topology=DamageHitTopology.RESOLVED_HIT,
        )
        opp = make_first_aid_opportunity(
            source_actor_id="b1",
            target_actor_id="b1",
            source_skill_id="sk_first_aid",
            aftermath_fact=aftermath,
            recovery_amount=50,
            probability=1.0,
        )
        result = recov_sys.execute(context, opp)
        assert result.executed is True
        assert result.resolution is not None
        assert result.resolution.actual_recovery == 50

    @pytest.mark.parametrize(
        "blocked_source",
        [
            SourceType.CHAIN_TRUE_FEEDBACK,
            SourceType.SHARE_DIRECT_LOSS,
            SourceType.DISTRIBUTION_DIRECT_LOSS,
        ],
    )
    def test_blocked_sources(self, blocked_source: SourceType) -> None:
        assert ReactionPermissionPolicy.can_trigger_recovery(blocked_source) is False

        context, systems = create_test_context()
        recov_sys = systems.recovery_opportunity_system
        context.units["b1"].troops = 800

        aftermath = create_test_aftermath_fact(
            damage_instance_id="dmg_blk",
            target_id="b1",
            source_type=blocked_source,
            assigned_target_damage=100,
            actual_target_troop_loss=100,
            target_troops_after=800,
            target_defeated=False,
            hit_topology=DamageHitTopology.RESOLVED_HIT,
        )
        opp = make_first_aid_opportunity(
            source_actor_id="b1",
            target_actor_id="b1",
            source_skill_id="sk_first_aid",
            aftermath_fact=aftermath,
            recovery_amount=50,
            probability=1.0,
        )
        result = recov_sys.execute(context, opp)
        assert result.executed is False
        assert result.reason == "INELIGIBLE_HIT_OR_SOURCE"


# ==============================================================================
# 4. Deterministic RNG & Full-Troop Policy
# ==============================================================================

class TestRngDeterminismAndFullTroopPolicy:
    def test_rng_determinism_probability_zero_and_one(self) -> None:
        context, systems = create_test_context()
        recov_sys = systems.recovery_opportunity_system
        context.units["b1"].troops = 800

        # p = 0.0: exactly 1 draw consuming RNG
        opp_0 = make_recuperation_opportunity(
            source_actor_id="a1",
            target_actor_id="b1",
            source_skill_id="sk_recup",
            recovery_amount=100,
            probability=0.0,
        )
        with unittest.mock.patch.object(
            context.random, "chance", wraps=context.random.chance
        ) as mock_chance:
            res_0 = recov_sys.execute(context, opp_0)
            assert mock_chance.call_count == 1
            mock_chance.assert_called_with(0.0)

        assert res_0.executed is False
        assert res_0.reason == "PROBABILITY_FAILED"

        # p = 1.0: exactly 1 draw consuming RNG
        opp_1 = make_recuperation_opportunity(
            source_actor_id="a1",
            target_actor_id="b1",
            source_skill_id="sk_recup",
            recovery_amount=100,
            probability=1.0,
        )
        with unittest.mock.patch.object(
            context.random, "chance", wraps=context.random.chance
        ) as mock_chance:
            res_1 = recov_sys.execute(context, opp_1)
            assert mock_chance.call_count == 1
            mock_chance.assert_called_with(1.0)

        assert res_1.executed is True
        assert res_1.resolution is not None
        assert res_1.resolution.actual_recovery == 100

    def test_full_troops_one_draw_actual_zero(self) -> None:
        context, systems = create_test_context()
        recov_sys = systems.recovery_opportunity_system

        # b1 is at full troops: 1000 / 1000 -> recoverable_gap == 0
        assert context.units["b1"].troops == 1000
        assert context.units["b1"].max_troops == 1000

        opp = make_recuperation_opportunity(
            source_actor_id="a1",
            target_actor_id="b1",
            source_skill_id="sk_recup",
            recovery_amount=100,
            probability=1.0,
        )

        events_captured = []
        context.event_bus.subscribe(
            EventType.TROOPS_RECOVERED,
            lambda event: events_captured.append(event),
        )

        with unittest.mock.patch.object(
            context.random, "chance", wraps=context.random.chance
        ) as mock_chance:
            result = recov_sys.execute(context, opp)
            # Full troops does NOT suppress RNG draw
            assert mock_chance.call_count == 1

        assert result.executed is True
        assert result.resolution is not None
        assert result.resolution.actual_recovery == 0
        assert context.units["b1"].troops == 1000

        # Invariant per test_full_target_without_ban_resolves_zero_and_emits_no_recovery_fact:
        # Full target resolves actual_recovery == 0 and emits no TROOPS_RECOVERED event
        assert len(events_captured) == 0


# ==============================================================================
# 5. Dynamic Healing Ban (Apply after State, Remove before Resolve)
# ==============================================================================

class TestDynamicHealingBan:
    def test_healing_ban_applied_prevents_recovery(self) -> None:
        context, systems = create_test_context()
        recov_sys = systems.recovery_opportunity_system
        context.units["b1"].troops = 800

        gen_id = StateApplicationGenerationId("gen_1")
        opp = make_recuperation_opportunity(
            source_actor_id="a1",
            target_actor_id="b1",
            source_skill_id="sk_recup",
            recovery_amount=100,
            probability=1.0,
            source_generation_id=gen_id,
        )

        # Apply HEALING_BAN to b1
        systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.HEALING_BAN.value,
            owner_id="b1",
            source_id="a1",
            duration_rounds=2,
        )

        events_captured = []
        context.event_bus.subscribe(
            EventType.RECOVERY_PREVENTED,
            lambda event: events_captured.append(event),
        )

        result = recov_sys.execute(context, opp)
        assert result.executed is True
        assert result.resolution is not None
        assert isinstance(result.resolution, RecoveryPreventedResult)
        assert result.resolution.reason == RecoveryPreventionReason.HEALING_BAN
        assert result.resolution.source_generation_id == gen_id
        assert context.units["b1"].troops == 800

        assert len(events_captured) == 1
        assert events_captured[0].payload["source_generation_id"] == str(gen_id)

    def test_healing_ban_removed_allows_recovery(self) -> None:
        context, systems = create_test_context()
        recov_sys = systems.recovery_opportunity_system
        context.units["b1"].troops = 800

        ban_inst = systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.HEALING_BAN.value,
            owner_id="b1",
            source_id="a1",
            duration_rounds=2,
        )

        # Now remove HEALING_BAN before recovery executes
        systems.state_lifecycle_system.remove(context, instance_id=ban_inst.instance_id)

        opp = make_recuperation_opportunity(
            source_actor_id="a1",
            target_actor_id="b1",
            source_skill_id="sk_recup",
            recovery_amount=100,
            probability=1.0,
        )
        result = recov_sys.execute(context, opp)
        assert result.executed is True
        assert isinstance(result.resolution, RecoveryResolvedResult)
        assert result.resolution.actual_recovery == 100
        assert context.units["b1"].troops == 900


# ==============================================================================
# 6. Persistent Source Skill Gate & Source Death Attribution
# ==============================================================================

class TestPersistentSourceSkillGateAndSourceDeath:
    def test_source_skill_disabled_suppresses_without_rng(self) -> None:
        context, systems = create_test_context()
        recov_sys = systems.recovery_opportunity_system
        context.units["b1"].troops = 800

        # Register skill runtime for a1, slot 1, disabled = True
        register_mock_skill_runtime(
            context,
            owner_id="a1",
            slot=SkillSlot.LEARNED_1,
            enabled=False,
            skill_id="sk_recup",
        )

        opp = make_recuperation_opportunity(
            source_actor_id="a1",
            target_actor_id="b1",
            source_skill_id="sk_recup",
            recovery_amount=100,
            probability=1.0,
            source_skill_slot=SkillSlot.LEARNED_1,
            source_skill_gate=PersistentSourceSkillGate.query_skill_runtime(),
        )

        with unittest.mock.patch.object(
            context.random, "chance", wraps=context.random.chance
        ) as mock_chance:
            result = recov_sys.execute(context, opp)
            # Gate 4 rejects: 0 RNG calls
            assert mock_chance.call_count == 0

        assert result.executed is False
        assert result.reason == "SKILL_TEMPORARILY_DISABLED"
        assert context.units["b1"].troops == 800

    def test_source_unit_dead_with_enabled_skill_still_allows_recovery(self) -> None:
        context, systems = create_test_context()
        recov_sys = systems.recovery_opportunity_system
        context.units["b1"].troops = 800

        # Kill source actor a1
        context.units["a1"].troops = 0
        assert not context.units["a1"].is_alive

        # Skill runtime is enabled
        register_mock_skill_runtime(
            context,
            owner_id="a1",
            slot=SkillSlot.LEARNED_1,
            enabled=True,
            skill_id="sk_recup",
        )

        opp = make_recuperation_opportunity(
            source_actor_id="a1",
            target_actor_id="b1",
            source_skill_id="sk_recup",
            recovery_amount=100,
            probability=1.0,
            source_skill_slot=SkillSlot.LEARNED_1,
            source_skill_gate=PersistentSourceSkillGate.query_skill_runtime(),
        )

        result = recov_sys.execute(context, opp)
        # Dead source with enabled skill DOES NOT prevent recovery!
        assert result.executed is True
        assert result.resolution is not None
        assert result.resolution.actual_recovery == 100
        assert context.units["b1"].troops == 900


# ==============================================================================
# 7. Generation Provenance & Refresh
# ==============================================================================

class TestGenerationProvenanceAndRefresh:
    def test_source_generation_id_preserved_across_refresh(self) -> None:
        context, systems = create_test_context()
        context.current_round = 1
        recov_sys = systems.recovery_opportunity_system
        context.units["b1"].troops = 700

        # 1) Apply state at G1
        st_inst = systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.FIRST_AID.value,
            owner_id="b1",
            source_id="a1",
            duration_rounds=2,
            runtime_params=FirstAidStateParams(
                probability=1.0,
                recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT,
                recovery_potency_context=RecoveryPotencyContext(treatment_amount=100),
            ),
        )
        g1 = st_inst.current_generation_id
        assert g1 is not None

        # 2) Opportunity created with G1
        aftermath = create_test_aftermath_fact(
            damage_instance_id="dmg_prov",
            target_id="b1",
            source_type=SourceType.NORMAL_ATTACK,
            assigned_target_damage=100,
            actual_target_troop_loss=100,
            target_troops_after=700,
            target_defeated=False,
            hit_topology=DamageHitTopology.RESOLVED_HIT,
        )
        opp = make_first_aid_opportunity(
            source_actor_id="a1",
            target_actor_id="b1",
            source_skill_id="sk_fa",
            aftermath_fact=aftermath,
            recovery_amount=100,
            probability=1.0,
            source_generation_id=g1,
            state_instance_id=st_inst.instance_id,
        )

        # 3) Refresh state to G2
        refreshed_inst = systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.FIRST_AID.value,
            owner_id="b1",
            source_id="a1",
            duration_rounds=2,
            runtime_params=FirstAidStateParams(
                probability=1.0,
                recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT,
                recovery_potency_context=RecoveryPotencyContext(treatment_amount=200),
            ),
        )
        g2 = refreshed_inst.current_generation_id
        assert g2 is not None
        assert g1 != g2
        assert refreshed_inst.instance_id == st_inst.instance_id

        # 4) Execute G1 opportunity: must retain G1 generation id & potency!
        events = []
        context.event_bus.subscribe(
            EventType.TROOPS_RECOVERED,
            lambda event: events.append(event),
        )

        res = recov_sys.execute(context, opp)
        assert res.executed is True
        assert res.source_generation_id == g1
        assert res.resolution is not None
        assert res.resolution.actual_recovery == 100
        assert res.resolution.source_generation_id == g1

        assert len(events) == 1
        assert events[0].payload["source_generation_id"] == str(g1)
        assert events[0].payload["actual_recovery"] == 100


# ==============================================================================
# 8. Action-Start RECUPERATION Integration & Mixed RuleIntent Ordering
# ==============================================================================

class TestActionStartRecuperationIntegration:
    def test_action_start_recuperation_collected_and_executed(self) -> None:
        context, systems = create_test_context()
        hook_system = systems.rule_hook_system
        context.current_round = 1
        context.units["a1"].troops = 800

        # Apply RECUPERATION state to a1 before a1 acts
        systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.RECUPERATION.value,
            owner_id="a1",
            source_id="a1",
            source_skill_id="sk_recup",
            duration_rounds=2,
            runtime_params=RecuperationStateParams(
                probability=1.0,
                recovery_potency_context=RecoveryPotencyContext(treatment_amount=150),
            ),
        )

        # Enter UNIT_ACTION_START for a1
        context.current_phase = BattlePhase.UNIT_ACTION_START.value
        context.action_progress.set_current_acting_unit("a1")
        context.action_progress.mark_action_start("a1", 1)

        hook = UnitActionStartHook(round_no=1, actor_id="a1")
        res = hook_system.process(context, hook)

        assert res.batch_status == "COMPLETED"
        assert len(res.intent_results) == 1
        intent_res = res.intent_results[0]
        assert isinstance(intent_res, RecoveryOpportunityResult)
        assert intent_res.executed is True
        assert intent_res.resolution is not None
        assert intent_res.resolution.actual_recovery == 150
        assert context.units["a1"].troops == 950

    def test_mixed_rule_intent_ordering_and_lethal_dot_abort(self) -> None:
        context, systems = create_test_context()
        context.current_round = 1
        context.current_phase = BattlePhase.UNIT_ACTION_START.value
        context.action_progress.set_current_acting_unit("a1")
        context.action_progress.mark_action_start("a1", 1)

        # Unit a1 has only 100 troops remaining
        context.units["a1"].troops = 100

        # Build a mixed batch: Intent 1 = Lethal Continuous Damage, Intent 2 = Recuperation on a1
        dot_source_ref = EffectSourceRef(
            stage9_source_type=SourceType.ACTIVE_SKILL,
            source_unit_id="b1",
            source_skill_id="sk_dot",
        )
        desc_dot = RuleIntentExecutionDescriptor(
            intent_kind=RuleIntentKind.EFFECT,
            intent_owner_id="a1",
            state_owner_id="a1",
            target_id="a1",
            source_ref=dot_source_ref,
        )
        dmg_eff = DamageEffect(
            source_id="b1",
            target_id="a1",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.SKILL,
            source_skill_id="sk_dot",
            coefficient=100.0,
            source_ref=dot_source_ref,
            execution_descriptor=desc_dot,
        )

        opp_recup = make_recuperation_opportunity(
            source_actor_id="a1",
            target_actor_id="a1",
            source_skill_id="sk_recup",
            recovery_amount=100,
            probability=1.0,
        )

        class MockMixedTrigger(systems.trigger_system.__class__):
            def collect(self, ctx: BattleContext, hook: Any) -> tuple[Any, ...]:
                return (dmg_eff, opp_recup)

        hook_system = RuleHookSystem(MockMixedTrigger(), systems.effect_executor)
        hook_system.recovery_opportunity_system = systems.recovery_opportunity_system

        hook = UnitActionStartHook(round_no=1, actor_id="a1")
        res = hook_system.process(context, hook)

        # 1) Lethal DOT resolves first, a1 is killed (0 troops)
        assert context.units["a1"].troops == 0
        assert not context.units["a1"].is_alive

        # 2) Mixed batch processed both intents, but second intent (recovery on dead a1) was cleanly aborted
        assert len(res.intent_results) == 2
        res_dot = res.intent_results[0]
        res_recup = res.intent_results[1]

        assert isinstance(res_dot, EffectExecutionResult)
        assert isinstance(res_recup, AbortedRuleIntentResult)
        assert res_recup.decision_kind in (
            ExecutionRightDecisionKind.ABORT_OWNER_STATE_REMAINDER,
            ExecutionRightDecisionKind.REJECT_CURRENT,
        )
        assert res_recup.reason in (
            ExecutionRightReason.OWNER_DEFEATED,
            ExecutionRightReason.TARGET_DEFEATED,
        )


# ==============================================================================
# 9. Phase Boundary Audit: No Silent Phase 6 Aftermath Integration
# ==============================================================================

class TestPhase6AftermathIntegrationReadiness:
    def test_stage9_damage_paths_trigger_first_aid_in_phase6(self) -> None:
        """
        Verify that Stage 9 damage pipelines (damage_instance_coordinator, etc.)
        now correctly instantiate DamageAftermathPort and trigger FIRST_AID opportunities in Phase 6.
        """
        context, systems = create_test_context()
        context.current_round = 1
        context.current_phase = BattlePhase.UNIT_ACTION.value

        # Apply FIRST_AID to b1
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

        # Execute direct damage effect on b1
        dmg_source_ref = EffectSourceRef(
            stage9_source_type=SourceType.ACTIVE_SKILL,
            source_unit_id="a1",
            source_skill_id="sk_strike",
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
            source_skill_id="sk_strike",
            coefficient=1.0,
            source_ref=dmg_source_ref,
            execution_descriptor=desc,
        )

        captured_recovery_events = []
        context.event_bus.subscribe(
            EventType.TROOPS_RECOVERED,
            lambda event: captured_recovery_events.append(event),
        )

        systems.effect_executor.execute(context, dmg)

        # Phase 6 integration check: Damage aftermath was invoked and FIRST_AID triggered!
        assert len(captured_recovery_events) == 1

