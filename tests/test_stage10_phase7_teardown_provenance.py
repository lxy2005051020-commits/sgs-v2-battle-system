from __future__ import annotations

import pytest
from typing import Any
from unittest.mock import MagicMock

from sgs_v2.battle_core import (
    BattleContext,
    BattleEngine,
    BattlePhase,
    BattleResult,
    BattleSystems,
    BattleTerminationState,
    DamageAftermathFact,
    DamageEffect,
    DamageHitTopology,
    DamageRequest,
    DamageResult,
    DamageSourceType,
    DamageType,
    DefeatCleanupPort,
    EventBus,
    EventType,
    ExactRatio,
    FirstAidStateParams,
    FutureBranchKind,
    LegacyFinalizationBarrier,
    LineupPosition,
    OfficialStateId,
    OperationIdAllocator,
    OperationLineage,
    RandomSystem,
    RecoveryModelKind,
    RecoveryOpportunity,
    RecoveryOpportunityKind,
    RecoveryPotencyContext,
    RecoveryRequest,
    RuleIntentExecutionDescriptor,
    RuleIntentKind,
    SourceType,
    StateApplicationGenerationId,
    StateDefinition,
    StateGenerationAllocator,
    StateInstance,
    StateLifecycleSystem,
    TroopType,
    UnitRuntime,
    register_official_state_definitions,
)
from sgs_v2.battle_core.battle_finalization_coordinator import (
    BattleFinalizationCoordinator,
    FinalizationProjectionPermit,
    FinalizationResult,
)
from sgs_v2.battle_core.execution_right_system import admit_action_scope
from sgs_v2.battle_core.stage10_state_params import (
    ContinuousDamageStateParams,
    FrozenContinuousDamageBasis,
    RecuperationStateParams,
)
from sgs_v2.battle_core.stage9_state_params import (
    ComboStateParams,
    TauntStateParams,
)


def create_phase7_context() -> tuple[BattleContext, BattleSystems]:
    lifecycle = StateLifecycleSystem()
    defeat_cleanup = DefeatCleanupPort(lifecycle)
    systems = BattleSystems(
        state_lifecycle_system=lifecycle,
        defeat_cleanup_port=defeat_cleanup,
    )
    context = BattleContext(
        battle_id="test_stage10_phase7_battle",
        units={
            "a1": UnitRuntime(
                "a1", "Commander_A1", "team_a", 1000, 1000, 200.0, 100.0, 100.0,
                lineup_position=LineupPosition.COMMANDER,
                intelligence=200.0,
                troop_type=TroopType.CAVALRY,
            ),
            "a2": UnitRuntime(
                "a2", "Deputy_A2", "team_a", 1000, 1000, 180.0, 90.0, 95.0,
                lineup_position=LineupPosition.DEPUTY_1,
                intelligence=180.0,
                troop_type=TroopType.CAVALRY,
            ),
            "b1": UnitRuntime(
                "b1", "Commander_B1", "team_b", 1000, 1000, 150.0, 120.0, 90.0,
                lineup_position=LineupPosition.COMMANDER,
                intelligence=150.0,
                troop_type=TroopType.SHIELD,
            ),
            "b2": UnitRuntime(
                "b2", "Deputy_B2", "team_b", 1000, 1000, 140.0, 110.0, 85.0,
                lineup_position=LineupPosition.DEPUTY_1,
                intelligence=140.0,
                troop_type=TroopType.SHIELD,
            ),
        },
        event_bus=EventBus(),
        random=RandomSystem(42),
    )
    context.current_round = 1
    context.current_phase = BattlePhase.UNIT_ACTION.value
    register_official_state_definitions(context.states)
    return context, systems


def test_01_finite_state_remains_at_battle_end_cleared() -> None:
    context, systems = create_phase7_context()
    context.current_round = 1
    context.current_phase = BattlePhase.UNIT_ACTION.value

    inst = systems.state_lifecycle_system.apply(
        context,
        state_id=OfficialStateId.BURN.value,
        owner_id="b1",
        source_id="a1",
        source_skill_id="fire_skill",
        duration_rounds=3,
    )
    assert inst.instance_id in context.states

    cleared = systems.state_lifecycle_system.clear_all_on_battle_end(context)
    assert len(cleared) == 1
    assert cleared[0].instance_id == inst.instance_id
    assert inst.instance_id not in context.states
    assert len(context.states.find()) == 0

    events = [e for e in context.event_bus.history if e.event_type == EventType.STATE_CLEARED_ON_BATTLE_END]
    assert len(events) == 1
    event = events[0]
    assert event.target_id == "b1"
    assert event.actor_id == "a1"
    assert event.payload["state_id"] == OfficialStateId.BURN.value
    assert event.payload["state_instance_id"] == inst.instance_id
    assert event.payload["state_owner_id"] == "b1"
    assert event.payload["clear_reason"] == "BATTLE_END"
    assert event.payload["current_generation_id"] == str(inst.current_generation_id)


def test_02_until_battle_end_state_cleared() -> None:
    context, systems = create_phase7_context()
    context.states.register_definition(
        StateDefinition(
            state_id="permanent_buff",
            name="Permanent Buff",
        )
    )

    inst = systems.state_lifecycle_system.apply(
        context,
        state_id="permanent_buff",
        owner_id="a1",
        source_id="a1",
    )
    assert inst.expires_round is None
    assert inst.lifecycle_window is None
    assert inst.instance_id in context.states

    cleared = systems.state_lifecycle_system.clear_all_on_battle_end(context)
    assert len(cleared) == 1
    assert cleared[0].instance_id == inst.instance_id
    assert len(context.states.find()) == 0

    events = [e for e in context.event_bus.history if e.event_type == EventType.STATE_CLEARED_ON_BATTLE_END]
    assert len(events) == 1
    assert events[0].payload["state_id"] == "permanent_buff"
    assert events[0].payload["clear_reason"] == "BATTLE_END"


def test_03_external_lifecycle_state_cleared() -> None:
    context, systems = create_phase7_context()

    taunt_inst = systems.state_lifecycle_system.apply(
        context,
        state_id=OfficialStateId.TAUNT.value,
        owner_id="b1",
        source_id="a1",
        runtime_params=TauntStateParams(taunt_target_id="a1"),
    )
    combo_inst = systems.state_lifecycle_system.apply(
        context,
        state_id=OfficialStateId.COMBO.value,
        owner_id="a1",
        source_id="a1",
        runtime_params=ComboStateParams(remaining_actions=1),
    )
    assert taunt_inst.instance_id in context.states
    assert combo_inst.instance_id in context.states

    cleared = systems.state_lifecycle_system.clear_all_on_battle_end(context)
    assert len(cleared) == 2
    assert len(context.states.find()) == 0

    cleared_ids = {inst.instance_id for inst in cleared}
    assert cleared_ids == {taunt_inst.instance_id, combo_inst.instance_id}


def test_04_multiple_states_deterministic_clear_order() -> None:
    context, systems = create_phase7_context()

    i1 = systems.state_lifecycle_system.apply(
        context,
        state_id=OfficialStateId.BURN.value,
        owner_id="b1",
        source_id="a1",
        duration_rounds=2,
    )
    i2 = systems.state_lifecycle_system.apply(
        context,
        state_id=OfficialStateId.FIRST_AID.value,
        owner_id="a1",
        source_id="a1",
        duration_rounds=2,
        runtime_params=FirstAidStateParams(
            probability=1.0,
            recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT,
            recovery_potency_context=RecoveryPotencyContext(treatment_amount=80),
        ),
    )
    i3 = systems.state_lifecycle_system.apply(
        context,
        state_id=OfficialStateId.POISON.value,
        owner_id="b2",
        source_id="a2",
        duration_rounds=2,
    )
    i4 = systems.state_lifecycle_system.apply(
        context,
        state_id=OfficialStateId.RECUPERATION.value,
        owner_id="a2",
        source_id="a2",
        duration_rounds=2,
        runtime_params=RecuperationStateParams(
            probability=1.0,
            recovery_potency_context=RecoveryPotencyContext(treatment_amount=80),
        ),
    )

    expected_order = sorted([i1, i2, i3, i4], key=lambda x: x.instance_id)

    cleared = systems.state_lifecycle_system.clear_all_on_battle_end(context)
    assert [inst.instance_id for inst in cleared] == [x.instance_id for x in expected_order]

    events = [e for e in context.event_bus.history if e.event_type == EventType.STATE_CLEARED_ON_BATTLE_END]
    assert [e.payload["state_instance_id"] for e in events] == [x.instance_id for x in expected_order]


def test_05_already_owner_death_cleared_state_no_duplicate_event() -> None:
    context, systems = create_phase7_context()

    inst_b2 = systems.state_lifecycle_system.apply(
        context,
        state_id=OfficialStateId.BURN.value,
        owner_id="b2",
        source_id="a1",
        duration_rounds=2,
    )
    inst_a1 = systems.state_lifecycle_system.apply(
        context,
        state_id=OfficialStateId.FIRST_AID.value,
        owner_id="a1",
        source_id="a1",
        duration_rounds=2,
        runtime_params=FirstAidStateParams(
            probability=1.0,
            recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT,
            recovery_potency_context=RecoveryPotencyContext(treatment_amount=80),
        ),
    )

    context.units["b2"].troops = 0
    systems.defeat_cleanup_port.commit_defeat(context, "b2", defeat_source_ref="a1")
    assert inst_b2.instance_id not in context.states

    removed_events = [e for e in context.event_bus.history if e.event_type == EventType.STATE_REMOVED]
    assert len(removed_events) == 1
    assert removed_events[0].payload["instance_id"] == inst_b2.instance_id
    assert removed_events[0].payload["reason"] == "OWNER_DEFEATED"

    cleared = systems.state_lifecycle_system.clear_all_on_battle_end(context)
    assert len(cleared) == 1
    assert cleared[0].instance_id == inst_a1.instance_id

    cleared_events = [e for e in context.event_bus.history if e.event_type == EventType.STATE_CLEARED_ON_BATTLE_END]
    assert len(cleared_events) == 1
    assert cleared_events[0].payload["state_instance_id"] == inst_a1.instance_id

    all_b2_events = [
        e for e in context.event_bus.history
        if (e.payload.get("state_instance_id") == inst_b2.instance_id or e.payload.get("instance_id") == inst_b2.instance_id)
        and e.event_type in (EventType.STATE_REMOVED, EventType.STATE_CLEARED_ON_BATTLE_END)
    ]
    assert len(all_b2_events) == 1
    assert all_b2_events[0].event_type == EventType.STATE_REMOVED


def test_06_teardown_idempotency() -> None:
    context, systems = create_phase7_context()

    systems.state_lifecycle_system.apply(
        context,
        state_id=OfficialStateId.BURN.value,
        owner_id="b1",
        source_id="a1",
        duration_rounds=2,
    )
    first_clear = systems.state_lifecycle_system.clear_all_on_battle_end(context)
    assert len(first_clear) == 1
    events_after_first = len([e for e in context.event_bus.history if e.event_type == EventType.STATE_CLEARED_ON_BATTLE_END])
    assert events_after_first == 1

    second_clear = systems.state_lifecycle_system.clear_all_on_battle_end(context)
    assert second_clear == []
    events_after_second = len([e for e in context.event_bus.history if e.event_type == EventType.STATE_CLEARED_ON_BATTLE_END])
    assert events_after_second == 1


def test_07_registry_empty_no_ghost_states_definitions_preserved() -> None:
    context, systems = create_phase7_context()

    systems.state_lifecycle_system.apply(
        context,
        state_id=OfficialStateId.POISON.value,
        owner_id="a2",
        source_id="b1",
        duration_rounds=2,
    )
    assert len(context.states.find()) == 1

    systems.state_lifecycle_system.clear_all_on_battle_end(context)

    assert len(context.states.find()) == 0
    assert len(context.states._instances) == 0

    poison_def = context.states.get_definition(OfficialStateId.POISON.value)
    assert poison_def is not None
    assert poison_def.state_id == OfficialStateId.POISON.value


def test_08_battle_end_events_observation_only() -> None:
    context, systems = create_phase7_context()

    inst = systems.state_lifecycle_system.apply(
        context,
        state_id=OfficialStateId.BURN.value,
        owner_id="b1",
        source_id="a1",
        duration_rounds=2,
    )

    observed_payloads: list[dict[str, Any]] = []

    def spy_observer(event: Any) -> None:
        observed_payloads.append(event.payload)

    context.event_bus.subscribe(EventType.STATE_CLEARED_ON_BATTLE_END, spy_observer)

    systems.state_lifecycle_system.clear_all_on_battle_end(context)

    assert len(observed_payloads) == 1
    p = observed_payloads[0]
    assert p["state_instance_id"] == inst.instance_id
    assert p["state_id"] == OfficialStateId.BURN.value
    assert p["state_owner_id"] == "b1"
    assert p["source_id"] == "a1"
    assert p["clear_reason"] == "BATTLE_END"
    assert p["reason"] == "BATTLE_END"


def test_09_no_new_rule_intent_during_teardown() -> None:
    context, systems = create_phase7_context()

    systems.state_lifecycle_system.apply(
        context,
        state_id=OfficialStateId.BURN.value,
        owner_id="b1",
        source_id="a1",
        duration_rounds=2,
    )

    systems.rule_hook_system.process = MagicMock(side_effect=RuntimeError("Should not be called"))  # type: ignore[method-assign]
    systems.trigger_system.collect = MagicMock(side_effect=RuntimeError("Should not be called"))  # type: ignore[method-assign]

    cleared = systems.state_lifecycle_system.clear_all_on_battle_end(context)
    assert len(cleared) == 1
    systems.rule_hook_system.process.assert_not_called()
    systems.trigger_system.collect.assert_not_called()


def test_10_no_recovery_during_teardown() -> None:
    context, systems = create_phase7_context()

    systems.state_lifecycle_system.apply(
        context,
        state_id=OfficialStateId.FIRST_AID.value,
        owner_id="a1",
        source_id="a1",
        duration_rounds=2,
        runtime_params=FirstAidStateParams(
            probability=1.0,
            recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT,
            recovery_potency_context=RecoveryPotencyContext(treatment_amount=80),
        ),
    )

    systems.recovery_system.resolve = MagicMock(side_effect=RuntimeError("Should not be called"))  # type: ignore[method-assign]
    systems.recovery_opportunity_system.evaluate_and_resolve = MagicMock(side_effect=RuntimeError("Should not be called"))  # type: ignore[method-assign]

    cleared = systems.state_lifecycle_system.clear_all_on_battle_end(context)
    assert len(cleared) == 1
    systems.recovery_system.resolve.assert_not_called()
    systems.recovery_opportunity_system.evaluate_and_resolve.assert_not_called()


def test_11_admitted_work_drains_before_teardown() -> None:
    context, systems = create_phase7_context()

    inst = systems.state_lifecycle_system.apply(
        context,
        state_id=OfficialStateId.BURN.value,
        owner_id="a1",
        source_id="b1",
        duration_rounds=2,
    )

    coordinator = systems.finalization_coordinator
    alloc = context.id_allocator

    parent_scope = "round_1_actor_a1"
    permit = systems.future_admission_gate.request_admission(
        branch_kind=FutureBranchKind.NEXT_ACTION,
        parent_scope_identity=parent_scope,
        id_allocator=context.id_allocator,
    )
    assert permit is not None
    scope = admit_action_scope(
        context=context,
        gate=systems.future_admission_gate,
        permit=permit,
        actor=context.get_unit("a1"),
        parent_scope_identity=parent_scope,
    )

    dmg_id = alloc.allocate_damage_instance_id()
    coordinator.admit_damage_instance(context, dmg_id)

    context.units["b1"].troops = 0
    coordinator.observe_damage_instance_death(context, dmg_id)

    assert coordinator.termination_state in (
        BattleTerminationState.VICTORY_LATCHED,
        BattleTerminationState.DRAINING_ADMITTED_WORK,
    )
    assert inst.instance_id in context.states

    coordinator.complete_damage_instance(context, dmg_id)
    assert coordinator.termination_state == BattleTerminationState.DRAINING_ADMITTED_WORK
    assert inst.instance_id in context.states

    coordinator.complete_action_scope(context, scope)

    assert coordinator.termination_state == BattleTerminationState.FINALIZED
    claim = coordinator.claim_finalized_projection()
    assert claim is not None
    proj_permit, fin_res = claim

    coordinator.consume_projection_permit(proj_permit)

    assert inst.instance_id not in context.states
    assert len(context.states.find()) == 0


def test_12_final_battle_result_occurs_after_legal_teardown_checkpoint() -> None:
    context, systems = create_phase7_context()
    engine = BattleEngine(context=context, systems=systems)

    context.units["b1"].troops = 10
    systems.state_lifecycle_system.apply(
        context,
        state_id=OfficialStateId.BURN.value,
        owner_id="a1",
        source_id="b1",
        duration_rounds=3,
    )

    result = engine.run()
    assert isinstance(result, BattleResult)
    assert context.ended is True

    assert len(context.states.find()) == 0
    assert len(context.states._instances) == 0

    cleared_events = [e for e in context.event_bus.history if e.event_type == EventType.STATE_CLEARED_ON_BATTLE_END]
    assert len(cleared_events) >= 1


def test_13_g1_work_and_g2_current_state_provenance_separation() -> None:
    context, systems = create_phase7_context()

    inst = systems.state_lifecycle_system.apply(
        context,
        state_id=OfficialStateId.BURN.value,
        owner_id="b1",
        source_id="a1",
        source_skill_id="fire_v1",
        duration_rounds=2,
    )
    g1 = inst.current_generation_id
    assert g1 is not None

    dmg_request = DamageRequest(
        source_id="a1",
        target_id="b1",
        damage_type=DamageType.STRATEGY,
        source_type=DamageSourceType.CONTINUOUS,
        coefficient=1.0,
        source_skill_id="fire_v1",
        source_state_id=OfficialStateId.BURN.value,
        source_state_instance_id=inst.instance_id,
        source_generation_id=g1,
    )

    refreshed_inst = systems.state_lifecycle_system.refresh(
        context,
        instance_id=inst.instance_id,
        source_id="a1",
        source_skill_id="fire_v2",
        duration_rounds=3,
    )
    g2 = refreshed_inst.current_generation_id
    assert g2 != g1
    assert refreshed_inst.instance_id == inst.instance_id

    systems.damage_resolution_system.resolve(context, dmg_request)

    dmg_events = [e for e in context.event_bus.history if e.event_type == EventType.DAMAGE_DEALT]
    assert len(dmg_events) == 1
    assert dmg_events[0].payload["source_generation_id"] == str(g1)
    assert dmg_events[0].payload["source_skill_id"] == "fire_v1"

    systems.state_lifecycle_system.clear_all_on_battle_end(context)

    teardown_events = [e for e in context.event_bus.history if e.event_type == EventType.STATE_CLEARED_ON_BATTLE_END]
    assert len(teardown_events) == 1
    assert teardown_events[0].payload["current_generation_id"] == str(g2)
    assert teardown_events[0].payload["application_generation_id"] == str(g2)
    assert teardown_events[0].payload["source_skill_id"] == "fire_v2"

    assert dmg_events[0].payload["source_generation_id"] == str(g1)


def test_14_source_dead_historical_provenance_preserved() -> None:
    context, systems = create_phase7_context()

    fa_inst = systems.state_lifecycle_system.apply(
        context,
        state_id=OfficialStateId.FIRST_AID.value,
        owner_id="a2",
        source_id="a1",
        source_skill_id="sacred_aid",
        duration_rounds=2,
        runtime_params=FirstAidStateParams(
            probability=1.0,
            recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT,
            recovery_potency_context=RecoveryPotencyContext(treatment_amount=80),
        ),
    )
    gen_id = fa_inst.current_generation_id

    context.units["a1"].troops = 0
    systems.defeat_cleanup_port.commit_defeat(context, "a1", defeat_source_ref="b1")

    cleared = systems.state_lifecycle_system.clear_all_on_battle_end(context)
    assert len(cleared) == 1
    assert cleared[0].instance_id == fa_inst.instance_id

    events = [e for e in context.event_bus.history if e.event_type == EventType.STATE_CLEARED_ON_BATTLE_END]
    assert len(events) == 1
    p = events[0].payload
    assert p["state_instance_id"] == fa_inst.instance_id
    assert p["state_id"] == OfficialStateId.FIRST_AID.value
    assert p["state_owner_id"] == "a2"
    assert p["source_id"] == "a1"
    assert p["source_skill_id"] == "sacred_aid"
    assert p["current_generation_id"] == str(gen_id)
    assert p["clear_reason"] == "BATTLE_END"


def test_15_damage_and_recovery_generation_identities_separate() -> None:
    context, systems = create_phase7_context()

    fa_inst = systems.state_lifecycle_system.apply(
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
    gen_fa = fa_inst.current_generation_id

    burn_inst = systems.state_lifecycle_system.apply(
        context,
        state_id=OfficialStateId.BURN.value,
        owner_id="b1",
        source_id="a1",
        duration_rounds=2,
    )
    gen_burn = burn_inst.current_generation_id

    assert gen_fa != gen_burn

    aftermath_fact = DamageAftermathFact(
        damage_instance_id=str(context.id_allocator.allocate_damage_instance_id()),
        target_id="b1",
        source_type=SourceType.PERIODIC_DAMAGE,
        damage_type=DamageType.STRATEGY,
        assigned_target_damage=100,
        actual_target_troop_loss=100,
        target_troops_after=900,
        target_defeated=False,
        hit_topology=DamageHitTopology.RESOLVED_HIT,
        source_state_generation=gen_burn,
    )

    context.units["b1"].troops = 900
    systems.damage_aftermath_port.commit_aftermath(context, aftermath_fact)

    rec_events = [e for e in context.event_bus.history if e.event_type == EventType.TROOPS_RECOVERED]
    assert len(rec_events) == 1
    assert rec_events[0].payload["source_generation_id"] == str(gen_fa)

    systems.state_lifecycle_system.clear_all_on_battle_end(context)

    td_events = [e for e in context.event_bus.history if e.event_type == EventType.STATE_CLEARED_ON_BATTLE_END]
    assert len(td_events) == 2
    td_burn = next(e for e in td_events if e.payload["state_id"] == OfficialStateId.BURN.value)
    td_fa = next(e for e in td_events if e.payload["state_id"] == OfficialStateId.FIRST_AID.value)
    assert td_burn.payload["current_generation_id"] == str(gen_burn)
    assert td_fa.payload["current_generation_id"] == str(gen_fa)
