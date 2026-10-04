from dataclasses import FrozenInstanceError, replace, asdict

import pytest

from sgs_v2.battle_core import (
    BattleContext, BattleSystems, BattleEngine, BattlePhase, EventBus,
    LineupPosition, RandomSystem, UnitRuntime,
)
from sgs_v2.battle_core.execution_right_runtime import (
    ExecutionRightSpec, ExecutionRightMode, ExecutionRightRequest,
    ExecutionTargetEligibilityDecision, ExecutionTargetEligibilityStatus,
)
from sgs_v2.battle_core.operation_identity import (
    OperationLineage, SourceType, PendingWorkId, OperationIdAllocator,
)
from sgs_v2.battle_core.pending_work import (
    PendingWorkStatus as Status, PendingWorkScheduleSpec as Schedule,
    ScheduleKind, PendingWorkTimingPoint as Point, WorkLifetimeSpec,
    WorkLifetimeKind, PendingWorkReadPolicy, WorkReadMode,
    PendingWorkValidityPolicy, SourceValidityMode, TargetValidityMode,
    PendingWorkDispatchResult, PendingWorkSystem,
)
from sgs_v2.battle_core.pending_work_adapters import recuperation_dispatcher
from sgs_v2.battle_core.provider_identity import SkillProviderRef
from sgs_v2.battle_core.skill_runtime import SkillRuntime, SkillSlot, SkillDefinition
from sgs_v2.battle_core.skill_definition import SkillTargetMode, DamageSkillEffectSpec
from sgs_v2.battle_core.enums import DamageType
from sgs_v2.battle_core.rule_intent import (
    RecoveryOpportunity, RecoveryOpportunityKind, RecoveryModelKind,
    RuleIntentExecutionDescriptor, RuleIntentKind,
)
from sgs_v2.battle_core.stage10_state_params import RecoveryPotencyContext
from sgs_v2.battle_core.state_generation import StateApplicationGenerationId
from sgs_v2.battle_core.execution_right_system import LegacyFinalizationBarrier


def fixture():
    units = {
        key: UnitRuntime(key, key, team, 1000, troops, 100, 100, speed,
                         lineup_position=position, wounded_troops=wounds)
        for key, team, position, troops, wounds, speed in (
            ("a", "A", LineupPosition.COMMANDER, 1000, 0, 110),
            ("s", "A", LineupPosition.DEPUTY_1, 1000, 0, 100),
            ("b", "B", LineupPosition.COMMANDER, 100, 900, 90),
        )
    }
    context = BattleContext("d1", units, EventBus(), RandomSystem(7), max_rounds=2)
    context.current_round = 1
    context.current_phase = BattlePhase.ROUND_END.value
    systems = BattleSystems(weapon_troop_function_table={i: i for i in range(1, 10001)})
    fired = []

    def dispatch(ctx, frame):
        fired.append(frame)
        return PendingWorkDispatchResult(ctx.id_allocator.allocate_effect_operation_id(), frame.lineage)

    systems.pending_work_system.register_dispatcher("fixture", dispatch)
    return context, systems, fired


def create(context, systems, **kwargs):
    options = dict(
        work_kind="fixture",
        parent_lineage=OperationLineage(None, None, None, SourceType.PERIODIC_DAMAGE, physical_attacker="s"),
        schedule_spec=Schedule(ScheduleKind.SPECIFIC_ROUND_PHASE, BattlePhase.ROUND_START, 2),
        execution_right_request=ExecutionRightRequest(historical_source_id="s", target_id="b"),
    )
    options.update(kwargs)
    return systems.pending_work_system.create(context, **options)


def tick(context, systems, round_no=2, phase=BattlePhase.ROUND_START, actor=None, **kwargs):
    context.current_round = round_no
    context.current_phase = phase.value
    return systems.pending_work_system.process(context, Point(round_no, phase, actor, **kwargs))


def test_t1_delay_exactly_once_and_no_terminal_replay():
    c, s, fired = fixture()
    work = create(c, s)
    assert tick(c, s, 1, BattlePhase.ROUND_END) == ()
    assert len(tick(c, s)) == 1
    assert tick(c, s) == ()
    assert len(fired) == 1
    assert c.pending_work.get(work.work_id).status is Status.COMPLETED
    with pytest.raises(ValueError):
        s.pending_work_system.cancel(c, work.work_id)
    with pytest.raises(FrozenInstanceError):
        work.status = Status.PENDING


@pytest.mark.parametrize("required, expected", [(False, Status.COMPLETED), (True, Status.CANCELLED)])
def test_t2_t3_source_death_policy(required, expected):
    c, s, fired = fixture()
    mode = SourceValidityMode.SOURCE_MUST_BE_ALIVE if required else SourceValidityMode.SOURCE_INDEPENDENT_AFTER_CREATION
    work = create(c, s, validity_policy=PendingWorkValidityPolicy(source=mode))
    s.troop_system.apply_damage(c.units["s"], 1000)
    tick(c, s)
    assert c.pending_work.get(work.work_id).status is expected
    assert len(fired) == (0 if required else 1)


def provider_fixture(c):
    # INHERENT is slot 0; no truthiness shortcut is allowed.
    runtime = SkillRuntime(SkillDefinition("skill", "skill", 1.0, SkillTargetMode.SINGLE_RANDOM_ENEMY, (DamageSkillEffectSpec(DamageType.WEAPON),)), "s", SkillSlot.INHERENT)
    c.skill_runtimes.register(runtime)
    return runtime, SkillProviderRef("s", SkillSlot.INHERENT, "skill")


def test_t4_live_provider_invalidation_zero_dispatch_zero_rng():
    c, s, fired = fixture()
    runtime, ref = provider_fixture(c)
    work = create(c, s,
        execution_right_request=ExecutionRightRequest(origin_provider=ref, target_id="b"),
        execution_right_spec=ExecutionRightSpec(provider_validity=ExecutionRightMode.RECHECK_AT_EXECUTION))
    runtime.enabled = False
    tick(c, s)
    assert c.pending_work.get(work.work_id).terminal_reason == "DENY_PROVIDER"
    assert fired == [] and c.event_bus.history == ()
    assert c.random.random() == RandomSystem(7).random()


def test_t5_target_death_cancels():
    c, s, fired = fixture()
    work = create(c, s)
    s.troop_system.apply_damage(c.units["b"], 100)
    tick(c, s)
    assert c.pending_work.get(work.work_id).terminal_reason == "TARGET_INVALID"
    assert fired == []


def test_t6_order_is_explicit_sequence_not_lexical_ids_or_dictionary():
    traces = []
    for _ in range(3):
        c, s, fired = fixture()
        works = [create(c, s) for _ in range(12)]
        # Invert storage order and cross pw_9 / pw_10; sequence still governs.
        c.pending_work._records = dict(reversed(list(c.pending_work._records.items())))
        tick(c, s)
        assert [frame.work.work_id for frame in fired] == [work.work_id for work in works]
        traces.append(c.pending_work.trace)
    assert traces[0] == traces[1] == traces[2]
    with pytest.raises(TypeError):
        PendingWorkId("pw_1") < PendingWorkId("pw_2")


def test_t7_pending_never_holds_finalization_barrier_and_no_resurrection():
    c, s, fired = fixture()
    work = create(c, s)
    s.troop_system.apply_damage(c.units["b"], 100)
    s.finalization_coordinator.observe_legacy_barrier(c, LegacyFinalizationBarrier.ACTION_SETTLED)
    assert s.finalization_coordinator.finalization_result is not None
    assert not s.finalization_coordinator.has_admitted_work
    tick(c, s)
    assert fired == []
    assert c.pending_work.get(work.work_id).status is Status.CANCELLED
    with pytest.raises(RuntimeError, match="admission closed"):
        create(c, s)


def test_t8_snapshot_deep_freeze_and_live_read_split():
    c, s, fired = fixture()
    payload = {"formula": {"rate": [3, 4]}}
    s.pending_work_system.register_live_reader("wounded", lambda ctx, work: ctx.units[work.target_ref].wounded_troops)
    create(c, s, snapshot_payload=payload, read_policy=PendingWorkReadPolicy((
        ("formula", WorkReadMode.SNAPSHOT_AT_CREATION), ("wounded", WorkReadMode.LIVE_AT_EXECUTION))))
    payload["formula"]["rate"][0] = 999
    s.troop_system.restore(c.units["b"], 10)
    tick(c, s)
    assert fired[0].snapshot["formula"]["rate"] == (3, 4)
    assert fired[0].live["wounded"] == 890
    with pytest.raises(TypeError):
        fired[0].snapshot["formula"]["rate"] = 999


def test_creation_really_evaluates_snapshot_admission_then_does_not_recheck():
    c, s, fired = fixture()
    runtime, ref = provider_fixture(c)
    spec = ExecutionRightSpec(provider_validity=ExecutionRightMode.SNAPSHOT_AT_ADMISSION)
    request = ExecutionRightRequest(origin_provider=ref, target_id="b")
    runtime.enabled = False
    with pytest.raises(ValueError, match="DENY_PROVIDER"):
        create(c, s, execution_right_spec=spec, execution_right_request=request)
    assert c.pending_work.all() == ()
    runtime.enabled = True
    create(c, s, execution_right_spec=spec, execution_right_request=request)
    runtime.enabled = False
    tick(c, s)
    assert len(fired) == 1


def test_live_target_relation_eligibility_is_owned_by_existing_policy():
    c, s, fired = fixture()
    s.execution_target_eligibility_policy.register_rule_adapter(lambda ctx, req:
        ExecutionTargetEligibilityDecision(req, ExecutionTargetEligibilityStatus.ALLOW
            if ctx.units[req.target_id].team_id == "B" else ExecutionTargetEligibilityStatus.DENY))
    work = create(c, s, execution_right_spec=ExecutionRightSpec(target_eligibility=ExecutionRightMode.RECHECK_AT_EXECUTION))
    c.units["b"].team_id = "A"
    tick(c, s)
    assert fired == []
    assert c.pending_work.get(work.work_id).terminal_reason == "DENY_TARGET"


def test_locked_target_relation_can_remain_independent_by_explicit_policy():
    c, s, fired = fixture()
    create(c, s, validity_policy=PendingWorkValidityPolicy(target=TargetValidityMode.IDENTITY_LOCKED))
    c.units["b"].team_id = "A"
    tick(c, s)
    assert len(fired) == 1


@pytest.mark.parametrize("kind, phase, actor", [
    (ScheduleKind.NEXT_PHASE, BattlePhase.ROUND_START, None),
    (ScheduleKind.NEXT_PHASE, BattlePhase.ROUND_END, None),
    (ScheduleKind.NEXT_ACTION_START, BattlePhase.UNIT_ACTION_START, "b"),
])
def test_next_phase_and_holder_next_action_start(kind, phase, actor):
    c, s, fired = fixture()
    create(c, s, schedule_spec=Schedule(kind, phase, actor_id=actor))
    if actor:
        tick(c, s, 2, phase, "a")
        assert fired == []
    tick(c, s, 2, phase, actor)
    assert len(fired) == 1


def test_holder_already_started_waits_for_next_round():
    c, s, fired = fixture()
    c.current_phase = BattlePhase.UNIT_ACTION_START.value
    c.action_progress.mark_action_start("b", 1)
    create(c, s, schedule_spec=Schedule(ScheduleKind.NEXT_ACTION_START, BattlePhase.UNIT_ACTION_START, actor_id="b"))
    tick(c, s, 1, BattlePhase.UNIT_ACTION_START, "b")
    assert fired == []
    tick(c, s, 2, BattlePhase.UNIT_ACTION_START, "b")
    assert len(fired) == 1


def test_future_trigger_matches_key_and_occurrence_exactly_once():
    c, s, fired = fixture()
    create(c, s, schedule_spec=Schedule(ScheduleKind.FUTURE_TRIGGER, trigger_key="future"))
    tick(c, s, 1, BattlePhase.ROUND_END, trigger_key="other", occurrence=1)
    assert fired == []
    tick(c, s, 1, BattlePhase.ROUND_END, trigger_key="future", occurrence=1)
    tick(c, s, 1, BattlePhase.ROUND_END, trigger_key="future", occurrence=2)
    assert len(fired) == 1


@pytest.mark.parametrize("lifetime", [WorkLifetimeSpec(), WorkLifetimeSpec(WorkLifetimeKind.UNTIL_EXECUTED)])
def test_one_shot_lifetimes(lifetime):
    c, s, fired = fixture()
    create(c, s, lifetime_spec=lifetime)
    tick(c, s)
    tick(c, s, 3)
    assert len(fired) == 1


def test_until_round_inclusive_deadline_and_no_catchup():
    c, s, fired = fixture()
    first = create(c, s, lifetime_spec=WorkLifetimeSpec(WorkLifetimeKind.UNTIL_ROUND, 2))
    second = create(c, s, schedule_spec=Schedule(ScheduleKind.FUTURE_TRIGGER, trigger_key="absent"),
                    lifetime_spec=WorkLifetimeSpec(WorkLifetimeKind.UNTIL_ROUND, 2))
    tick(c, s)
    tick(c, s, 3)
    assert c.pending_work.get(first.work_id).status is Status.COMPLETED
    assert c.pending_work.get(second.work_id).status is Status.EXPIRED
    assert len(fired) == 1


def test_missed_exact_phase_expires_never_backfills():
    c, s, fired = fixture()
    work = create(c, s)
    tick(c, s, 2, BattlePhase.ROUND_END)
    assert c.pending_work.get(work.work_id).status is Status.EXPIRED and fired == []


def test_repeat_seam_explicitly_rejected_before_allocation():
    c, s, _ = fixture()
    with pytest.raises(NotImplementedError, match="reserved"):
        create(c, s, lifetime_spec=WorkLifetimeSpec(WorkLifetimeKind.REPEAT_N_TIMES))
    assert c.pending_work.all() == ()


def test_cancelled_work_never_reexecutes():
    c, s, fired = fixture()
    work = create(c, s)
    s.pending_work_system.cancel(c, work.work_id)
    tick(c, s)
    assert fired == []
    with pytest.raises(ValueError, match="illegal"):
        s.pending_work_system._transition(c, work.work_id, Status.EXECUTING, "forged")


def test_dispatch_exception_fails_closed_and_never_retries():
    c, s, _ = fixture()
    def boom(ctx, frame):
        raise RuntimeError("fixture fault")
    s.pending_work_system.register_dispatcher("fault", boom)
    work = create(c, s, work_kind="fault")
    with pytest.raises(RuntimeError, match="fixture fault"):
        tick(c, s)
    assert c.pending_work.get(work.work_id).terminal_reason == "DISPATCH_FAILED"
    assert tick(c, s) == ()


def test_sibling_cancel_and_nested_creation_not_in_current_due_batch():
    c, s, fired = fixture()
    def dispatch(ctx, frame):
        s.pending_work_system.cancel(ctx, sibling.work_id)
        create(ctx, s, schedule_spec=Schedule(ScheduleKind.NEXT_PHASE, BattlePhase.ROUND_START))
        return PendingWorkDispatchResult(ctx.id_allocator.allocate_effect_operation_id(), frame.lineage)
    s.pending_work_system.register_dispatcher("nested", dispatch)
    create(c, s, work_kind="nested")
    sibling = create(c, s)
    tick(c, s)
    assert fired == []
    tick(c, s, 3)
    assert len(fired) == 1


def test_reentrant_dispatch_rejected():
    c, s, _ = fixture()
    s.pending_work_system.register_dispatcher("recursive", lambda ctx, frame: tick(ctx, s))
    work = create(c, s, work_kind="recursive")
    with pytest.raises(RuntimeError, match="reentrant"):
        tick(c, s)
    assert c.pending_work.get(work.work_id).status is Status.CANCELLED


def test_unique_owner_and_cross_battle_isolation():
    c, s, _ = fixture()
    create(c, s)
    other = PendingWorkSystem(s.execution_right_support, s.future_admission_gate)
    with pytest.raises(ValueError, match="canonical owner"):
        other.process(c, Point(1, BattlePhase.ROUND_END))
    c2, _, _ = fixture()
    with pytest.raises(ValueError, match="battle-scoped"):
        s.pending_work_system.cancel_future(c2)


def test_allocator_counter_is_independent_and_lineage_preserves_all_parents():
    c, s, fired = fixture()
    allocator = c.id_allocator
    parent = OperationLineage(
        allocator.allocate_action_id(), allocator.allocate_normal_attack_id(),
        allocator.allocate_damage_instance_id(), SourceType.PERIODIC_DAMAGE,
        parent_skill_operation_id=allocator.allocate_skill_operation_id(),
        parent_effect_operation_id=allocator.allocate_effect_operation_id(),
        parent_recovery_operation_id=allocator.allocate_recovery_operation_id(),
        parent_state_generation_id=StateApplicationGenerationId("gen_1"),
    )
    work = create(c, s, parent_lineage=parent)
    result = tick(c, s)[0]
    assert result.lineage == replace(parent, parent_pending_work_id=work.work_id)
    assert c.pending_work.trace[-1].operation_id == result.operation_id
    assert str(allocator.allocate_action_id()) == "act_2"
    assert str(allocator.allocate_damage_instance_id()) == "dmg_2"


@pytest.mark.parametrize("payload", [{"v": object()}, {"v": float("nan")}, {"v": lambda: 1}])
def test_opaque_and_nonfinite_snapshot_rejected(payload):
    c, s, _ = fixture()
    with pytest.raises(TypeError):
        create(c, s, snapshot_payload=payload, read_policy=PendingWorkReadPolicy((("v", WorkReadMode.SNAPSHOT_AT_CREATION),)))
    assert c.pending_work.all() == ()


def test_missing_or_undeclared_read_dimensions_fail_closed():
    c, s, _ = fixture()
    with pytest.raises(ValueError, match="exactly match"):
        create(c, s, snapshot_payload={"secret": 1})
    with pytest.raises(ValueError, match="no live reader"):
        create(c, s, read_policy=PendingWorkReadPolicy((("absent", WorkReadMode.LIVE_AT_EXECUTION),)))


def test_past_schedule_invalid_clock_and_duplicate_registration_rejected():
    c, s, _ = fixture()
    with pytest.raises(ValueError, match="future"):
        create(c, s, schedule_spec=Schedule(ScheduleKind.SPECIFIC_ROUND_PHASE, BattlePhase.ROUND_START, 1))
    with pytest.raises(ValueError, match="clock"):
        s.pending_work_system.process(c, Point(2, BattlePhase.ROUND_START))
    with pytest.raises(ValueError, match="registered"):
        s.pending_work_system.register_dispatcher("fixture", lambda *_: None)
    tick(c, s)
    with pytest.raises(ValueError, match="backwards"):
        tick(c, s, 1)


def opportunity(probability):
    return RecoveryOpportunity(
        opportunity_kind=RecoveryOpportunityKind.RECUPERATION_ACTION_START,
        execution_descriptor=RuleIntentExecutionDescriptor(
            intent_kind=RuleIntentKind.RECOVERY_OPPORTUNITY,
            intent_owner_id="b", state_owner_id="b", target_id="b"),
        probability=probability, recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT,
        recovery_potency_context=RecoveryPotencyContext(
            base_rate=0.5, source_troops_at_application=1000, source_attribute_at_application=100.0),
        aftermath_fact=None,
    )


@pytest.mark.parametrize("probability", [0.0, 0.5, 1.0])
def test_real_recuperation_adapter_same_results_rng_and_entire_domain_event_trace(probability):
    baseline, owners, _ = fixture()
    adapted, systems, _ = fixture()
    intent = opportunity(probability)
    baseline.current_round = 2
    baseline.current_phase = BattlePhase.UNIT_ACTION_START.value
    expected = owners.recovery_opportunity_system.execute(baseline, intent)
    systems.pending_work_system.register_dispatcher("recuperation", recuperation_dispatcher(systems.recovery_opportunity_system, intent))
    create(adapted, systems, work_kind="recuperation",
        snapshot_payload={"recovery_potency": asdict(intent.recovery_potency_context)},
        read_policy=PendingWorkReadPolicy((("recovery_potency", WorkReadMode.SNAPSHOT_AT_CREATION),)),
        schedule_spec=Schedule(ScheduleKind.NEXT_ACTION_START, BattlePhase.UNIT_ACTION_START, actor_id="b"))
    actual = tick(adapted, systems, 2, BattlePhase.UNIT_ACTION_START, "b")[0].result
    assert actual == expected
    assert adapted.event_bus.history == baseline.event_bus.history
    assert [(u.troops, u.wounded_troops) for u in adapted.units.values()] == [(u.troops, u.wounded_troops) for u in baseline.units.values()]
    assert [adapted.random.random() for _ in range(8)] == [baseline.random.random() for _ in range(8)]


def test_engine_drives_work_and_cancels_unreached_work_at_max_round_exit():
    c, s, fired = fixture()
    c.current_round = 0
    c.current_phase = "NOT_STARTED"
    create(c, s, schedule_spec=Schedule(ScheduleKind.SPECIFIC_ROUND_PHASE, BattlePhase.ROUND_START, 1))
    future = create(c, s, schedule_spec=Schedule(ScheduleKind.FUTURE_TRIGGER, trigger_key="never"))
    BattleEngine(c, s).run()
    assert len(fired) == 1 and c.ended
    assert c.pending_work.get(future.work_id).status is Status.CANCELLED
    assert next(t for t in c.pending_work.trace if t.status is Status.EXECUTING).phase == BattlePhase.ROUND_START.value


def test_real_state_producer_recuperation_adapter_keeps_generation_events_and_rng():
    from sgs_v2.battle_core import register_official_state_definitions, OfficialStateId, UnitActionStartHook
    from sgs_v2.battle_core.stage10_state_params import RecuperationStateParams
    from sgs_v2.battle_core.skill_runtime_registry import PersistentSourceSkillGate
    baseline, owners, _ = fixture()
    adapted, systems, _ = fixture()
    states = []
    for ctx, sys in ((baseline, owners), (adapted, systems)):
        register_official_state_definitions(ctx.states)
        states.append(sys.state_lifecycle_system.apply(ctx,
            state_id=OfficialStateId.RECUPERATION.value, owner_id="b", source_id="s",
            source_skill_id="recup", duration_rounds=2,
            runtime_params=RecuperationStateParams(
                probability=1.0, recovery_potency_context=opportunity(1.0).recovery_potency_context,
                source_skill_gate=PersistentSourceSkillGate.always_active())))
    intent = systems.recovery_opportunity_system.make_recuperation_opportunity(states[1])
    systems.pending_work_system.register_dispatcher("state_recup", recuperation_dispatcher(systems.recovery_opportunity_system, intent))
    work = create(adapted, systems, work_kind="state_recup",
        parent_lineage=OperationLineage(None, None, None, SourceType.PERIODIC_DAMAGE,
                                       parent_state_generation_id=states[1].current_generation_id),
        snapshot_payload={"recovery_potency": asdict(intent.recovery_potency_context)},
        read_policy=PendingWorkReadPolicy((("recovery_potency", WorkReadMode.SNAPSHOT_AT_CREATION),)),
        execution_right_spec=ExecutionRightSpec(state_effectiveness=ExecutionRightMode.RECHECK_AT_EXECUTION),
        execution_right_request=ExecutionRightRequest(target_id="b", historical_source_id="s", state_instance_id=states[1].instance_id),
        schedule_spec=Schedule(ScheduleKind.NEXT_ACTION_START, BattlePhase.UNIT_ACTION_START, actor_id="b"))
    baseline.current_round = 2
    baseline.current_phase = BattlePhase.UNIT_ACTION_START.value
    baseline.action_progress.set_current_acting_unit("b")
    baseline.action_progress.mark_action_start("b", 2)
    collected = owners.trigger_system.collect(baseline, UnitActionStartHook(2, "b"))
    assert len(collected) == 1 and collected[0] == intent
    expected = owners.recovery_opportunity_system.execute(baseline, collected[0])
    # Source formula inputs change in both worlds; application potency remains fixed.
    baseline.units["s"].intelligence = adapted.units["s"].intelligence = 999
    actual = tick(adapted, systems, 2, BattlePhase.UNIT_ACTION_START, "b")[0]
    assert actual.result == expected
    assert actual.lineage.parent_state_generation_id == states[1].current_generation_id
    assert actual.lineage.parent_pending_work_id == work.work_id
    assert adapted.event_bus.history == baseline.event_bus.history
    assert adapted.units["b"].snapshot() == baseline.units["b"].snapshot()
    assert adapted.random.random() == baseline.random.random()
