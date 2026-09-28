from __future__ import annotations

import pytest
from typing import Any

from sgs_v2.battle_core import (
    AbortedRuleIntentResult,
    BattleContext,
    BattlePhase,
    BattleSystems,
    DamageCalculationBasis,
    DamageDefensePolicy,
    DamageEffect,
    DamageEffectResult,
    DamageModifierPhase,
    DamageSourceType,
    DamageType,
    EventBus,
    ExecutionRightDecisionKind,
    ExecutionRightReason,
    LineupPosition,
    OfficialStateId,
    RandomSystem,
    RuleIntentKind,
    StateApplicationGenerationId,
    TroopType,
    UnitActionStartHook,
    UnitRuntime,
    register_official_state_definitions,
)
from sgs_v2.battle_core.continuous_damage_basis_producer import (
    ContinuousDamageApplicationRequest,
    ContinuousDamageBasisProducer,
)
from sgs_v2.battle_core.stage10_state_params import (
    ContinuousDamageStateParams,
    FrozenContinuousDamageBasis,
    FrozenSourceFormulaFacts,
)


def create_test_context() -> tuple[BattleContext, BattleSystems]:
    systems = BattleSystems()
    context = BattleContext(
        battle_id="test_stage10_phase4_battle",
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
        random=RandomSystem(42),
    )
    register_official_state_definitions(context.states)
    context.current_round = 1
    context.current_phase = BattlePhase.ROUND_START.value
    return context, systems


# ============================================================================
# 1. Trigger & Lifecycle Integration Tests
# ============================================================================
class TestTriggerAndLifecycleIntegration:
    def test_burn_triggers_at_action_start_with_frozen_lane(self) -> None:
        context, systems = create_test_context()

        # Apply BURN to b1 before b1's action in Round 1
        inst = systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.BURN.value,
            owner_id="b1",
            source_id="a1",
            duration_rounds=1,
        )
        assert inst is not None
        assert isinstance(inst.runtime_params, ContinuousDamageStateParams)
        assert inst.runtime_params.frozen_damage_basis is not None
        assert inst.runtime_params.frozen_damage_basis.damage_type == DamageType.STRATEGY

        # Enter UNIT_ACTION_START for b1
        context.current_phase = BattlePhase.UNIT_ACTION_START.value
        context.action_progress.set_current_acting_unit("b1")
        context.action_progress.mark_action_start("b1", 1)

        hook = UnitActionStartHook(round_no=1, actor_id="b1")
        resolution = systems.rule_hook_system.process(context, hook)

        # Assert exactly one intent executed
        assert len(resolution.intent_results) == 1
        res = resolution.intent_results[0]
        assert isinstance(res, DamageEffectResult)
        dmg_res = res.resolution.damage
        assert dmg_res is not None
        assert dmg_res.calculation_basis == DamageCalculationBasis.FROZEN_APPLICATION
        assert dmg_res.pipeline_trace is not None
        assert dmg_res.pipeline_trace.calculation_basis == DamageCalculationBasis.FROZEN_APPLICATION
        assert dmg_res.pipeline_trace.frozen_application_trace is not None
        assert dmg_res.final_damage > 0

        # Natural expiration at action start
        systems.state_lifecycle_system.expire_eligible_states(context, "b1")
        assert inst.instance_id not in context.states

        # Advance to Round 2: ensure no leak
        context.current_round = 2
        context.action_progress.set_current_acting_unit("b1")
        context.action_progress.mark_action_start("b1", 2)
        hook_r2 = UnitActionStartHook(round_no=2, actor_id="b1")
        res_r2 = systems.rule_hook_system.process(context, hook_r2)
        assert len(res_r2.intent_results) == 0

    def test_continuous_damage_applied_after_action_start_defers_to_next_round(self) -> None:
        context, systems = create_test_context()

        # b1 acts first in Round 1
        context.current_phase = BattlePhase.UNIT_ACTION.value
        context.action_progress.set_current_acting_unit("b1")
        context.action_progress.mark_action_start("b1", 1)

        # Apply BURN to b1 AFTER b1's action start opportunity has elapsed
        inst = systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.BURN.value,
            owner_id="b1",
            source_id="a1",
            duration_rounds=1,
        )
        assert inst is not None
        # In Round 1, window starts at Round 2 because b1 already consumed Round 1 action start
        assert inst.lifecycle_window is not None
        assert inst.lifecycle_window.first_eligible_round == 2

        # Trying to trigger in Round 1 yields nothing
        effects = systems.trigger_system.collect(context, UnitActionStartHook(1, "b1"))
        assert len(effects) == 0

        # In Round 2, b1 begins action -> eligible
        context.current_round = 2
        context.current_phase = BattlePhase.UNIT_ACTION_START.value
        context.action_progress.set_current_acting_unit("b1")
        context.action_progress.mark_action_start("b1", 2)

        effects_r2 = systems.trigger_system.collect(context, UnitActionStartHook(2, "b1"))
        assert len(effects_r2) == 1
        assert effects_r2[0].calculation_basis == DamageCalculationBasis.FROZEN_APPLICATION

    def test_second_action_start_in_same_round_suppressed(self) -> None:
        context, systems = create_test_context()

        systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.POISON.value,
            owner_id="b1",
            source_id="a1",
            duration_rounds=2,
        )

        context.current_phase = BattlePhase.UNIT_ACTION_START.value
        context.action_progress.set_current_acting_unit("b1")
        context.action_progress.mark_action_start("b1", 1)

        hook = UnitActionStartHook(1, "b1")
        effects1 = systems.trigger_system.collect(context, hook)
        assert len(effects1) == 1

        # Simulate a duplicate/synthetic mark in same round
        context.action_progress.mark_action_start("b1", 1)
        effects2 = systems.trigger_system.collect(context, hook)
        assert len(effects2) == 0


# ============================================================================
# 2. 6 Continuous Damage States Route Mapping Tests
# ============================================================================
class TestContinuousDamageRoutes:
    @pytest.mark.parametrize(
        ("state_id", "expected_route"),
        [
            (OfficialStateId.BURN.value, DamageType.STRATEGY),
            (OfficialStateId.FLOOD.value, DamageType.STRATEGY),
            (OfficialStateId.POISON.value, DamageType.STRATEGY),
            (OfficialStateId.SANDSTORM.value, DamageType.STRATEGY),
            (OfficialStateId.ROUT.value, DamageType.WEAPON),
        ],
    )
    def test_standard_five_states_route_mapping(
        self, state_id: str, expected_route: DamageType
    ) -> None:
        context, systems = create_test_context()

        inst = systems.state_lifecycle_system.apply(
            context,
            state_id=state_id,
            owner_id="b1",
            source_id="a1",
            duration_rounds=1,
        )
        assert inst is not None
        assert isinstance(inst.runtime_params, ContinuousDamageStateParams)
        assert inst.runtime_params.frozen_damage_basis is not None
        assert inst.runtime_params.frozen_damage_basis.damage_type == expected_route
        assert inst.runtime_params.frozen_damage_basis.formula_policy_result.formula_context.defense_policy == DamageDefensePolicy.NORMAL

        context.current_phase = BattlePhase.UNIT_ACTION_START.value
        context.action_progress.set_current_acting_unit("b1")
        context.action_progress.mark_action_start("b1", 1)

        hook = UnitActionStartHook(1, "b1")
        resolution = systems.rule_hook_system.process(context, hook)
        res = resolution.intent_results[0]
        assert isinstance(res, DamageEffectResult)
        dmg_res = res.resolution.damage
        assert dmg_res is not None
        assert dmg_res.damage_type == expected_route

    def test_rebellion_dynamic_route_selection_and_ignore_defense(self) -> None:
        # Case A: Attacker attack (300) > intelligence (100) -> Route = WEAPON
        context, systems = create_test_context()
        context.units["a1"].attack = 300.0
        context.units["a1"].intelligence = 100.0

        inst_weapon = systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.REBELLION.value,
            owner_id="b1",
            source_id="a1",
            duration_rounds=1,
        )
        assert inst_weapon is not None
        basis_weapon = inst_weapon.runtime_params.frozen_damage_basis
        assert basis_weapon is not None
        assert basis_weapon.damage_type == DamageType.WEAPON
        assert basis_weapon.formula_policy_result.formula_context.defense_policy == DamageDefensePolicy.IGNORE_RELEVANT_TARGET_DEFENSE

        # Case B: Attacker attack (100) < intelligence (300) -> Route = STRATEGY
        context.units["a1"].attack = 100.0
        context.units["a1"].intelligence = 300.0

        producer = systems.continuous_damage_basis_producer
        basis_strategy = producer.capture(
            context,
            ContinuousDamageApplicationRequest(
                source_id="a1",
                target_id="b1",
                state_id=OfficialStateId.REBELLION.value,
                application_generation_id=StateApplicationGenerationId("gen_reb_strat"),
            ),
        )
        assert basis_strategy.damage_type == DamageType.STRATEGY
        assert basis_strategy.formula_policy_result.formula_context.defense_policy == DamageDefensePolicy.IGNORE_RELEVANT_TARGET_DEFENSE


# ============================================================================
# 3. Frozen Source Replay Tests
# ============================================================================
class TestFrozenSourceReplay:
    def test_source_attribute_mutation_post_application_does_not_affect_damage(self) -> None:
        context, systems = create_test_context()

        # Apply BURN when source has intelligence = 250, troops = 1000
        inst = systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.BURN.value,
            owner_id="b1",
            source_id="a1",
            duration_rounds=2,
        )
        assert inst is not None

        # Record baseline damage calculation from frozen lane
        context.current_phase = BattlePhase.UNIT_ACTION_START.value
        context.action_progress.set_current_acting_unit("b1")
        context.action_progress.mark_action_start("b1", 1)

        context.random = RandomSystem(42)
        resolution1 = systems.rule_hook_system.process(context, UnitActionStartHook(1, "b1"))
        res0 = resolution1.intent_results[0]
        assert isinstance(res0, DamageEffectResult)
        baseline_damage = res0.resolution.damage.final_damage

        # Drastically mutate source attributes: intelligence reduced to 10, troops down to 50
        context.units["a1"].intelligence = 10.0
        context.units["a1"].attack = 10.0
        context.units["a1"].troops = 50

        # Calculate damage again with mutated live source
        effect = systems.trigger_system._effects_for_state(inst)[0]
        assert isinstance(effect, DamageEffect)
        req = effect.to_request()
        context.random = RandomSystem(42)
        result_mutated = systems.damage_system.calculate(context, req)

        # Final damage must match baseline EXACTLY because source facts are frozen!
        assert result_mutated.final_damage == baseline_damage
        assert result_mutated.pipeline_trace.frozen_application_trace.source_formula_facts.source_combat_attribute_at_application == 250.0
        assert result_mutated.pipeline_trace.frozen_application_trace.source_formula_facts.source_troops_at_application == 1000

    def test_source_dead_at_tick_executes_damage(self) -> None:
        context, systems = create_test_context()

        # Apply ROUT to b1
        systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.ROUT.value,
            owner_id="b1",
            source_id="a1",
            duration_rounds=1,
        )

        # Kill source completely (troops = 0)
        context.units["a1"].troops = 0
        assert not context.units["a1"].is_alive

        # Target b1 begins action
        context.current_phase = BattlePhase.UNIT_ACTION_START.value
        context.action_progress.set_current_acting_unit("b1")
        context.action_progress.mark_action_start("b1", 1)

        resolution = systems.rule_hook_system.process(context, UnitActionStartHook(1, "b1"))
        assert len(resolution.intent_results) == 1
        res = resolution.intent_results[0]
        assert isinstance(res, DamageEffectResult)
        dmg_res = res.resolution.damage
        assert dmg_res is not None
        assert dmg_res.final_damage > 0
        assert dmg_res.calculation_basis == DamageCalculationBasis.FROZEN_APPLICATION


# ============================================================================
# 4. Dynamic Target Evaluation Tests
# ============================================================================
class TestDynamicTargetEvaluation:
    def test_target_defense_dynamic_at_tick(self) -> None:
        context, systems = create_test_context()

        # Apply ROUT to b1
        inst = systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.ROUT.value,
            owner_id="b1",
            source_id="a1",
            duration_rounds=2,
        )
        assert inst is not None
        effect = systems.trigger_system._effects_for_state(inst)[0]
        assert isinstance(effect, DamageEffect)

        # Baseline: b1 defense = 120.0
        context.units["b1"].defense = 120.0
        result_low_def = systems.damage_system.calculate(context, effect.to_request())

        # High defense: b1 defense = 350.0
        context.units["b1"].defense = 350.0
        result_high_def = systems.damage_system.calculate(context, effect.to_request())

        # Low defense should take strictly more damage than high defense
        assert result_low_def.final_damage > result_high_def.final_damage

    def test_rebellion_ignores_target_defense(self) -> None:
        context, systems = create_test_context()

        # Apply REBELLION (source attack 200 > intelligence 100 -> WEAPON)
        context.units["a1"].attack = 200.0
        context.units["a1"].intelligence = 100.0
        inst = systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.REBELLION.value,
            owner_id="b1",
            source_id="a1",
            duration_rounds=2,
        )
        assert inst is not None
        effect = systems.trigger_system._effects_for_state(inst)[0]
        assert isinstance(effect, DamageEffect)

        # Target defense = 50.0
        context.random = RandomSystem(42)
        res1 = systems.damage_system.calculate(context, effect.to_request())

        # Target defense = 500.0
        context.random = RandomSystem(42)
        res2 = systems.damage_system.calculate(context, effect.to_request())

        # Since REBELLION policy is IGNORE_RELEVANT_TARGET_DEFENSE, both damages must be equal!
        assert res1.pipeline_trace.frozen_application_trace.formula_policy_result.formula_context.defense_policy == DamageDefensePolicy.IGNORE_RELEVANT_TARGET_DEFENSE
        assert res1.final_damage == res2.final_damage


# ============================================================================
# 5. Generation Provenance & Refresh Audit Tests
# ============================================================================
class TestGenerationProvenanceAndAuditTrace:
    def test_generation_id_provenance_through_pipeline_trace(self) -> None:
        context, systems = create_test_context()

        inst = systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.BURN.value,
            owner_id="b1",
            source_id="a1",
            duration_rounds=1,
        )
        assert inst is not None
        gen_id = inst.current_generation_id
        basis = inst.runtime_params.frozen_damage_basis
        assert basis.application_generation_id == gen_id

        context.current_phase = BattlePhase.UNIT_ACTION_START.value
        context.action_progress.set_current_acting_unit("b1")
        context.action_progress.mark_action_start("b1", 1)

        resolution = systems.rule_hook_system.process(context, UnitActionStartHook(1, "b1"))
        res = resolution.intent_results[0]
        assert isinstance(res, DamageEffectResult)
        dmg_res = res.resolution.damage
        assert dmg_res.source_generation_id == gen_id
        assert dmg_res.pipeline_trace.calculation_basis == DamageCalculationBasis.FROZEN_APPLICATION
        assert dmg_res.pipeline_trace.frozen_application_trace.application_generation_id == gen_id

    def test_refresh_allocates_new_generation_and_updates_basis(self) -> None:
        context, systems = create_test_context()

        # Initial apply -> G1
        inst1 = systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.POISON.value,
            owner_id="b1",
            source_id="a1",
            duration_rounds=2,
        )
        gen1 = inst1.current_generation_id

        # Source gets buffed
        context.units["a1"].intelligence = 350.0

        # Refresh with new duration -> G2
        inst2 = systems.state_lifecycle_system.refresh(
            context,
            instance_id=inst1.instance_id,
            duration_rounds=3,
        )
        gen2 = inst2.current_generation_id
        assert gen2 != gen1
        basis2 = inst2.runtime_params.frozen_damage_basis
        assert basis2.application_generation_id == gen2
        assert basis2.source_formula_facts.source_combat_attribute_at_application == 350.0


# ============================================================================
# 6. Defeat / Abort Scope Tests
# ============================================================================
class TestDefeatAbortScope:
    def test_mid_batch_owner_defeat_aborts_remainder_intents(self) -> None:
        context, systems = create_test_context()

        # Apply two continuous damage states on b1: BURN and FLOOD
        inst_burn = systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.BURN.value,
            owner_id="b1",
            source_id="a1",
            duration_rounds=1,
        )
        inst_flood = systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.FLOOD.value,
            owner_id="b1",
            source_id="a1",
            duration_rounds=1,
        )

        # Set b1 troops low so the first damage defeats b1
        context.units["b1"].troops = 10

        context.current_phase = BattlePhase.UNIT_ACTION_START.value
        context.action_progress.set_current_acting_unit("b1")
        context.action_progress.mark_action_start("b1", 1)

        hook = UnitActionStartHook(1, "b1")
        resolution = systems.rule_hook_system.process(context, hook)

        # We had 2 intents in the batch
        assert len(resolution.intent_results) == 2

        # First intent (BURN) executed and defeated b1
        res1 = resolution.intent_results[0]
        assert isinstance(res1, DamageEffectResult)
        assert not context.units["b1"].is_alive

        # Second intent (FLOOD) must be aborted because owner b1 was defeated in batch!
        res2 = resolution.intent_results[1]
        assert isinstance(res2, AbortedRuleIntentResult)
        assert res2.reason == ExecutionRightReason.OWNER_DEFEATED
        assert res2.decision_kind == ExecutionRightDecisionKind.ABORT_OWNER_STATE_REMAINDER
