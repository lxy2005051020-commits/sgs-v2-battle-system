from __future__ import annotations

import ast
from pathlib import Path

import pytest

from sgs_v2.battle_core import (
    AdmissionDecision,
    AdmissionStatus,
    ApplicationDisposition,
    BattleContext,
    BattlePhase,
    BattleSystems,
    ComboStateParams,
    DependencyCycleError,
    DamageSkillEffectSpec,
    DamageType,
    EmptyStateRuntimeParams,
    EventBus,
    EventType,
    LineupPosition,
    LocalRuleCauseRef,
    ProviderDependency,
    ProviderNode,
    ProviderValidityStatus,
    RandomSystem,
    RemovalDecision,
    RemovalDecisionStatus,
    RemovalOperation,
    SkillDefinition,
    SkillProviderRef,
    SkillRuntime,
    SkillSlot,
    SkillTargetMode,
    StateApplicationGenerationId,
    StateApplicationResultStatus,
    StateApplicationTransaction,
    StateCandidate,
    StateConflictDecision,
    StateDefinition,
    StateEffectivenessContribution,
    StateEffectivenessStatus,
    StateInstance,
    StateLifetimeDomain,
    StateLifetimeSpec,
    StateNode,
    StateRemovalResultStatus,
    SuppressionCause,
    UnitRuntime,
    register_official_state_definitions,
)
from sgs_v2.battle_core.official_state_catalog import OfficialStateId
from sgs_v2.battle_core.stage11_state_params import StunStateParams


def make_context(seed: int = 1202) -> BattleContext:
    context = BattleContext(
        battle_id=f"stage12-round2-{seed}",
        units={
            "a": UnitRuntime(
                "a", "A", "A", 1000, 1000, 100, 100, 100,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "b": UnitRuntime(
                "b", "B", "B", 1000, 1000, 100, 100, 90,
                lineup_position=LineupPosition.COMMANDER,
            ),
        },
        event_bus=EventBus(),
        random=RandomSystem(seed),
    )
    context.current_round = 1
    context.current_phase = BattlePhase.ACTION_ORDER.value
    return context


def register_synthetic(
    context: BattleContext,
    state_id: str = "synthetic",
    runtime_params_type=EmptyStateRuntimeParams,
) -> None:
    context.states.register_definition(
        StateDefinition(
            state_id=state_id,
            name=state_id,
            runtime_params_type=runtime_params_type,
        )
    )


def candidate(
    state_id: str = "synthetic",
    *,
    lifetime_spec: StateLifetimeSpec | None = None,
    provider_dependencies=(),
    runtime_params=None,
) -> StateCandidate:
    return StateCandidate(
        state_id=state_id,
        owner_id="b",
        source_id="a",
        source_skill_id="skill-source",
        source_skill_slot=SkillSlot.LEARNED_1,
        runtime_params_candidate=runtime_params or EmptyStateRuntimeParams(),
        lifetime_spec=lifetime_spec,
        provider_dependencies=tuple(provider_dependencies),
        application_provenance="synthetic-round2-test",
    )


def refresh_adapter(_context, _candidate, residents):
    return StateConflictDecision(
        ApplicationDisposition.REFRESH,
        "TEST_REFRESH",
        existing_instance_id=residents[0].instance_id,
    )


def replace_adapter(_context, _candidate, residents):
    return StateConflictDecision(
        ApplicationDisposition.REPLACE,
        "TEST_REPLACE",
        existing_instance_id=residents[0].instance_id,
    )


def reject_conflict_adapter(_context, _candidate, residents):
    return StateConflictDecision(
        ApplicationDisposition.REJECT_CONFLICT,
        "TEST_REJECT_CONFLICT",
        existing_instance_id=residents[0].instance_id,
    )


def reject_admission_adapter(_context, _candidate):
    return AdmissionDecision(
        AdmissionStatus.REJECT_IMMUNITY,
        "TEST_ADMISSION_IMMUNITY",
    )


def allow_removal_adapter(_context, operation, _instance):
    return RemovalDecision(
        RemovalDecisionStatus.ALLOW,
        operation,
        "TEST_REMOVAL_ALLOW",
    )


def reject_removal_adapter(_context, operation, _instance):
    return RemovalDecision(
        RemovalDecisionStatus.REJECT_CONTRACT_PROTECTED,
        operation,
        "TEST_REMOVAL_PROTECTED",
    )


def make_skill_runtime() -> SkillRuntime:
    return SkillRuntime(
        definition=SkillDefinition(
            skill_id="skill-provider",
            name="skill-provider",
            activation_rate=1.0,
            target_mode=SkillTargetMode.SINGLE_RANDOM_ENEMY,
            effect_specs=(
                DamageSkillEffectSpec(
                    damage_type=DamageType.WEAPON,
                    coefficient=1.0,
                ),
            ),
        ),
        owner_id="a",
        skill_slot=SkillSlot.LEARNED_1,
        enabled=True,
    )


def state_metadata_adapter(context, instance, _session):
    blocked = set(context.metadata.get("blocked_instances", ()))
    if instance.instance_id not in blocked:
        return StateEffectivenessContribution()
    return StateEffectivenessContribution(
        suppression_causes=(
            SuppressionCause(
                "TEST_STATE_SUPPRESSION",
                LocalRuleCauseRef(instance.instance_id),
            ),
        )
    )


def provider_metadata_adapter(context, provider_ref, _session):
    blocked = set(context.metadata.get("blocked_providers", ()))
    if provider_ref not in blocked:
        return ()
    return (
        SuppressionCause(
            "TEST_PROVIDER_SUPPRESSION",
            LocalRuleCauseRef(repr(provider_ref)),
        ),
    )


def add_resident(
    context: BattleContext,
    systems: BattleSystems,
    *,
    state_id: str = "synthetic",
    lifetime_spec: StateLifetimeSpec | None = None,
) -> StateInstance:
    result = systems.state_application_coordinator.apply_candidate(
        context,
        candidate(state_id, lifetime_spec=lifetime_spec),
    )
    assert result.committed
    assert result.instance is not None
    return result.instance


def test_admission_allow_has_no_side_effect() -> None:
    context = make_context()
    register_synthetic(context)
    systems = BattleSystems()
    before_events = context.event_bus.history
    decision = systems.state_admission_policy.evaluate_candidate(
        context, candidate()
    )
    assert decision.status is AdmissionStatus.ALLOW
    assert context.states.find() == []
    assert context.event_bus.history == before_events


def test_admission_reject_allocates_no_generation() -> None:
    context = make_context()
    register_synthetic(context)
    systems = BattleSystems()
    systems.state_admission_policy.register_rule_adapter(
        reject_admission_adapter
    )
    result = systems.state_application_coordinator.apply_candidate(
        context, candidate()
    )
    assert result.status is StateApplicationResultStatus.REJECTED_ADMISSION
    assert context.generation_allocator.allocate().value == "gen_1"


def test_admission_reject_preserves_existing_instance() -> None:
    context = make_context()
    register_synthetic(context)
    systems = BattleSystems()
    existing = add_resident(context, systems)
    before_events = context.event_bus.history
    systems.state_admission_policy.register_rule_adapter(
        reject_admission_adapter
    )
    result = systems.state_application_coordinator.apply_candidate(
        context, candidate()
    )
    assert result.status is StateApplicationResultStatus.REJECTED_ADMISSION
    assert context.states.get(existing.instance_id) == existing
    assert context.event_bus.history == before_events


def test_admission_policy_consumes_zero_rng() -> None:
    context = make_context(seed=33)
    register_synthetic(context)
    systems = BattleSystems()
    systems.state_admission_policy.evaluate_candidate(context, candidate())
    assert context.random.random() == RandomSystem(33).random()


def test_admission_query_emits_no_event() -> None:
    context = make_context()
    register_synthetic(context)
    systems = BattleSystems()
    systems.state_admission_policy.evaluate_candidate(context, candidate())
    assert context.event_bus.history == ()


def test_create_disposition() -> None:
    context = make_context()
    register_synthetic(context)
    systems = BattleSystems()
    decision = systems.state_conflict_policy.evaluate_conflict(
        context, candidate(), ()
    )
    assert decision.disposition is ApplicationDisposition.CREATE


def test_refresh_disposition() -> None:
    context = make_context()
    register_synthetic(context)
    systems = BattleSystems()
    existing = add_resident(context, systems)
    systems.state_conflict_policy.register_rule_adapter(refresh_adapter)
    decision = systems.state_conflict_policy.evaluate_conflict(
        context, candidate(), (existing,)
    )
    assert decision.disposition is ApplicationDisposition.REFRESH
    assert decision.existing_instance_id == existing.instance_id


def test_replace_disposition() -> None:
    context = make_context()
    register_synthetic(context)
    systems = BattleSystems()
    existing = add_resident(context, systems)
    systems.state_conflict_policy.register_rule_adapter(replace_adapter)
    decision = systems.state_conflict_policy.evaluate_conflict(
        context, candidate(), (existing,)
    )
    assert decision.disposition is ApplicationDisposition.REPLACE


def test_reject_conflict_disposition() -> None:
    context = make_context()
    register_synthetic(context)
    systems = BattleSystems()
    existing = add_resident(context, systems)
    systems.state_conflict_policy.register_rule_adapter(
        reject_conflict_adapter
    )
    decision = systems.state_conflict_policy.evaluate_conflict(
        context, candidate(), (existing,)
    )
    assert decision.disposition is ApplicationDisposition.REJECT_CONFLICT


def test_unsupported_conflict_is_explicit() -> None:
    context = make_context()
    register_synthetic(context)
    systems = BattleSystems()
    existing = add_resident(context, systems)
    decision = systems.state_conflict_policy.evaluate_conflict(
        context, candidate(), (existing,)
    )
    assert decision.disposition is ApplicationDisposition.UNSUPPORTED_BOUNDARY


def test_conflict_policy_consumes_zero_rng() -> None:
    context = make_context(seed=34)
    register_synthetic(context)
    systems = BattleSystems()
    systems.state_conflict_policy.evaluate_conflict(context, candidate(), ())
    assert context.random.random() == RandomSystem(34).random()


def test_create_new_instance_new_generation() -> None:
    context = make_context()
    register_synthetic(context)
    systems = BattleSystems()
    result = systems.state_application_coordinator.apply_candidate(
        context, candidate()
    )
    assert result.status is StateApplicationResultStatus.APPLIED
    assert result.instance is not None
    assert result.instance.instance_id == "state-000001"
    assert str(result.instance.current_generation_id) == "gen_1"


def test_refresh_same_instance_new_generation() -> None:
    context = make_context()
    register_synthetic(context)
    systems = BattleSystems()
    original = add_resident(context, systems)
    old_generation = original.current_generation_id
    systems.state_conflict_policy.register_rule_adapter(refresh_adapter)
    result = systems.state_application_coordinator.apply_candidate(
        context, candidate()
    )
    assert result.status is StateApplicationResultStatus.REFRESHED
    assert result.instance is not None
    assert result.instance.instance_id == original.instance_id
    assert result.instance.current_generation_id != old_generation


def test_replace_new_instance_new_generation() -> None:
    context = make_context()
    register_synthetic(context)
    systems = BattleSystems()
    original = add_resident(context, systems)
    old_generation = original.current_generation_id
    systems.state_conflict_policy.register_rule_adapter(replace_adapter)
    result = systems.state_application_coordinator.apply_candidate(
        context, candidate()
    )
    assert result.status is StateApplicationResultStatus.REPLACED
    assert result.instance is not None
    assert result.instance.instance_id != original.instance_id
    assert result.instance.current_generation_id != old_generation
    assert original.instance_id not in context.states


def test_reject_allocates_no_generation() -> None:
    context = make_context()
    register_synthetic(context)
    systems = BattleSystems()
    add_resident(context, systems)
    systems.state_conflict_policy.register_rule_adapter(
        reject_conflict_adapter
    )
    result = systems.state_application_coordinator.apply_candidate(
        context, candidate()
    )
    assert result.status is StateApplicationResultStatus.REJECTED_CONFLICT
    assert context.generation_allocator.allocate().value == "gen_2"


def test_cycle_validation_failure_commits_nothing() -> None:
    context = make_context()
    register_synthetic(context)
    systems = BattleSystems()
    provider = SkillProviderRef(
        "a", SkillSlot.LEARNED_1, "skill-provider"
    )
    planned = StateNode(context.states.peek_next_instance_id())
    systems.dependency_evaluation_support.add_dependency(
        ProviderNode(provider), planned
    )
    with pytest.raises(DependencyCycleError):
        systems.state_application_coordinator.apply_candidate(
            context,
            candidate(
                provider_dependencies=(
                    ProviderDependency(provider, "TEST_PROVIDER_DEPENDENCY"),
                )
            ),
        )
    assert context.states.find() == []
    assert context.event_bus.history == ()
    assert context.generation_allocator.allocate().value == "gen_1"


def _invalid_refresh_transaction(
    existing: StateInstance,
) -> StateApplicationTransaction:
    return StateApplicationTransaction(
        disposition=ApplicationDisposition.REFRESH,
        candidate=candidate(
            lifetime_spec=StateLifetimeSpec.round_calendar(
                expires_round=8,
                expires_phase=BattlePhase.ROUND_END.value,
            )
        ),
        new_generation_id=StateApplicationGenerationId("manual-new-generation"),
        final_runtime_params=EmptyStateRuntimeParams(),
        final_lifetime_spec=StateLifetimeSpec.round_calendar(
            expires_round=8,
            expires_phase=BattlePhase.ROUND_END.value,
        ),
        expected_resident_generations=(
            (
                existing.instance_id,
                StateApplicationGenerationId("wrong-generation"),
            ),
        ),
        dependency_prerequisites=(),
        expected_existing_instance_id=existing.instance_id,
        expected_existing_generation_id=StateApplicationGenerationId(
            "wrong-generation"
        ),
    )


def test_precondition_failure_commits_nothing() -> None:
    context = make_context()
    register_synthetic(context)
    systems = BattleSystems()
    existing = systems.state_lifecycle_system.apply(
        context,
        state_id="synthetic",
        owner_id="b",
        source_id="a",
        expires_round=3,
        expires_phase=BattlePhase.ROUND_END.value,
    )
    before = context.states.get(existing.instance_id)
    with pytest.raises(RuntimeError, match="precondition mismatch"):
        systems.state_lifecycle_system.commit_application_transaction(
            context, _invalid_refresh_transaction(existing)
        )
    assert context.states.get(existing.instance_id) == before


def test_refresh_failure_preserves_old_instance() -> None:
    context = make_context()
    register_synthetic(context)
    systems = BattleSystems()
    existing = systems.state_lifecycle_system.apply(
        context, state_id="synthetic", owner_id="b", source_id="a"
    )
    with pytest.raises(RuntimeError):
        systems.state_lifecycle_system.commit_application_transaction(
            context, _invalid_refresh_transaction(existing)
        )
    assert context.states.get(existing.instance_id).instance_id == existing.instance_id


def test_refresh_failure_preserves_old_generation() -> None:
    context = make_context()
    register_synthetic(context)
    systems = BattleSystems()
    existing = systems.state_lifecycle_system.apply(
        context, state_id="synthetic", owner_id="b", source_id="a"
    )
    with pytest.raises(RuntimeError):
        systems.state_lifecycle_system.commit_application_transaction(
            context, _invalid_refresh_transaction(existing)
        )
    assert (
        context.states.get(existing.instance_id).current_generation_id
        == existing.current_generation_id
    )


def test_refresh_failure_preserves_old_timer() -> None:
    context = make_context()
    register_synthetic(context)
    systems = BattleSystems()
    existing = systems.state_lifecycle_system.apply(
        context,
        state_id="synthetic",
        owner_id="b",
        source_id="a",
        expires_round=3,
        expires_phase=BattlePhase.ROUND_END.value,
    )
    with pytest.raises(RuntimeError):
        systems.state_lifecycle_system.commit_application_transaction(
            context, _invalid_refresh_transaction(existing)
        )
    current = context.states.get(existing.instance_id)
    assert current.expires_round == 3
    assert current.expires_phase == BattlePhase.ROUND_END.value
    assert current.lifetime_spec is None


def test_failed_transaction_emits_no_commit_event() -> None:
    context = make_context()
    register_synthetic(context)
    systems = BattleSystems()
    existing = systems.state_lifecycle_system.apply(
        context, state_id="synthetic", owner_id="b", source_id="a"
    )
    before = context.event_bus.history
    with pytest.raises(RuntimeError):
        systems.state_lifecycle_system.commit_application_transaction(
            context, _invalid_refresh_transaction(existing)
        )
    assert context.event_bus.history == before


def test_gameplay_removal_requires_policy_allow() -> None:
    context = make_context()
    register_synthetic(context)
    systems = BattleSystems()
    existing = add_resident(context, systems)
    result = systems.state_removal_coordinator.remove(
        context,
        operation=RemovalOperation.ORDINARY_CLEANSE,
        instance_id=existing.instance_id,
    )
    assert result.status is StateRemovalResultStatus.UNSUPPORTED_BOUNDARY
    assert existing.instance_id in context.states


def test_rejected_removal_preserves_state() -> None:
    context = make_context()
    register_synthetic(context)
    systems = BattleSystems()
    existing = add_resident(context, systems)
    systems.state_removal_policy.register_rule_adapter(
        reject_removal_adapter
    )
    before = context.states.get(existing.instance_id)
    result = systems.state_removal_coordinator.remove(
        context,
        operation=RemovalOperation.ORDINARY_CLEANSE,
        instance_id=existing.instance_id,
    )
    assert result.status is StateRemovalResultStatus.REJECTED
    assert context.states.get(existing.instance_id) == before


def test_allowed_gameplay_removal_commits_once() -> None:
    context = make_context()
    register_synthetic(context)
    systems = BattleSystems()
    existing = add_resident(context, systems)
    systems.state_removal_policy.register_rule_adapter(
        allow_removal_adapter
    )
    result = systems.state_removal_coordinator.remove(
        context,
        operation=RemovalOperation.ORDINARY_CLEANSE,
        instance_id=existing.instance_id,
    )
    assert result.status is StateRemovalResultStatus.REMOVED
    assert existing.instance_id not in context.states
    removed_events = [
        item for item in context.event_bus.history
        if item.event_type is EventType.STATE_REMOVED
    ]
    assert len(removed_events) == 1


def test_natural_expiry_does_not_use_cleanse_eligibility() -> None:
    context = make_context()
    register_synthetic(context)
    systems = BattleSystems()
    existing = add_resident(context, systems)
    systems.state_removal_policy.register_rule_adapter(
        reject_removal_adapter
    )
    decision = systems.state_removal_policy.evaluate_removal(
        context, RemovalOperation.NATURAL_EXPIRY, existing
    )
    assert decision.allowed


def test_battle_teardown_not_blocked_by_cleanse_policy() -> None:
    context = make_context()
    register_synthetic(context)
    systems = BattleSystems()
    existing = add_resident(context, systems)
    systems.state_removal_policy.register_rule_adapter(
        reject_removal_adapter
    )
    decision = systems.state_removal_policy.evaluate_removal(
        context, RemovalOperation.BATTLE_TEARDOWN, existing
    )
    assert decision.allowed


def test_removal_policy_consumes_zero_rng() -> None:
    context = make_context(seed=35)
    register_synthetic(context)
    systems = BattleSystems()
    existing = add_resident(context, systems)
    systems.state_removal_policy.evaluate_removal(
        context, RemovalOperation.ORDINARY_CLEANSE, existing
    )
    assert context.random.random() == RandomSystem(35).random()


def test_suppressed_state_lifetime_continues() -> None:
    context = make_context()
    register_synthetic(context)
    systems = BattleSystems()
    systems.state_effectiveness_policy.register_rule_adapter(
        state_metadata_adapter
    )
    existing = add_resident(
        context,
        systems,
        lifetime_spec=StateLifetimeSpec.holder_action_window(2),
    )
    context.metadata["blocked_instances"] = (existing.instance_id,)
    assert (
        systems.state_effectiveness_policy.evaluate_state(context, existing).status
        is StateEffectivenessStatus.SUPPRESSED
    )
    removed = systems.state_lifecycle_system.settle_action_start_lifetimes(
        context, "b"
    )
    assert removed == []
    current = context.states.get(existing.instance_id)
    assert current.lifetime_spec is not None
    assert current.lifetime_spec.remaining_holder_action_windows == 1


def test_expired_suppressed_state_is_removed() -> None:
    context = make_context()
    register_synthetic(context)
    systems = BattleSystems()
    systems.state_effectiveness_policy.register_rule_adapter(
        state_metadata_adapter
    )
    existing = add_resident(
        context,
        systems,
        lifetime_spec=StateLifetimeSpec.round_calendar(
            expires_round=2,
            expires_phase=BattlePhase.ROUND_START.value,
        ),
    )
    context.metadata["blocked_instances"] = (existing.instance_id,)
    context.current_round = 2
    context.current_phase = BattlePhase.ROUND_START.value
    removed = systems.state_lifecycle_system.expire_at(
        context,
        round_no=2,
        phase=BattlePhase.ROUND_START.value,
    )
    assert [item.instance_id for item in removed] == [existing.instance_id]
    assert existing.instance_id not in context.states


def test_removed_state_never_resumes() -> None:
    context = make_context()
    register_synthetic(context)
    systems = BattleSystems()
    systems.state_effectiveness_policy.register_rule_adapter(
        state_metadata_adapter
    )
    existing = add_resident(
        context,
        systems,
        lifetime_spec=StateLifetimeSpec.round_calendar(
            expires_round=2,
            expires_phase=BattlePhase.ROUND_START.value,
        ),
    )
    context.metadata["blocked_instances"] = (existing.instance_id,)
    context.current_round = 2
    context.current_phase = BattlePhase.ROUND_START.value
    systems.state_lifecycle_system.expire_at(
        context,
        round_no=2,
        phase=BattlePhase.ROUND_START.value,
    )
    context.metadata["blocked_instances"] = ()
    with pytest.raises(KeyError):
        systems.state_effectiveness_policy.evaluate_state(context, existing)


def test_stage12_lifetime_spec_does_not_enter_stage10_persistence() -> None:
    context = make_context()
    register_synthetic(context)
    systems = BattleSystems()
    result = systems.state_application_coordinator.apply_candidate(
        context,
        candidate(
            lifetime_spec=StateLifetimeSpec.round_calendar(
                expires_round=3,
                expires_phase=BattlePhase.ROUND_END.value,
            )
        ),
    )
    assert result.instance is not None
    assert result.instance.lifecycle_window is None
    assert result.instance.expires_round is None
    assert result.instance.lifetime_spec is not None
    assert result.instance.lifetime_spec.domain is StateLifetimeDomain.ROUND_CALENDAR


def test_behavioral_counter_is_not_physical_lifetime() -> None:
    context = make_context()
    register_synthetic(context, "stun-like", StunStateParams)
    systems = BattleSystems()
    result = systems.state_application_coordinator.apply_candidate(
        context,
        candidate(
            "stun-like",
            runtime_params=StunStateParams(remaining_blocks=2),
        ),
    )
    assert result.instance is not None
    assert result.instance.lifetime_spec is None
    systems.state_lifecycle_system.settle_action_start_lifetimes(context, "b")
    current = context.states.get(result.instance.instance_id)
    assert isinstance(current.runtime_params, StunStateParams)
    assert current.runtime_params.remaining_blocks == 2


def _make_two_due_states(context, systems):
    register_synthetic(context, "cause")
    register_synthetic(context, "dependent")
    life = StateLifetimeSpec.round_calendar(
        expires_round=2,
        expires_phase=BattlePhase.ROUND_START.value,
    )
    cause = add_resident(context, systems, state_id="cause", lifetime_spec=life)
    dependent = add_resident(
        context, systems, state_id="dependent", lifetime_spec=life
    )
    return cause, dependent


def test_same_envelope_due_set_removed_before_recompute() -> None:
    context = make_context()
    systems = BattleSystems()
    cause, dependent = _make_two_due_states(context, systems)
    snapshots = []

    def observe(_event):
        snapshots.append(
            (
                context.states.has_instance(cause.instance_id),
                context.states.has_instance(dependent.instance_id),
            )
        )

    context.event_bus.subscribe(EventType.STATE_EXPIRED, observe)
    context.current_round = 2
    context.current_phase = BattlePhase.ROUND_START.value
    systems.state_lifecycle_system.expire_at(
        context,
        round_no=2,
        phase=BattlePhase.ROUND_START.value,
    )
    assert snapshots == [(False, False), (False, False)]


def test_same_envelope_no_transient_resume() -> None:
    context = make_context()
    systems = BattleSystems()
    cause, dependent = _make_two_due_states(context, systems)

    def dependency_adapter(ctx, instance, _session):
        if instance.instance_id != dependent.instance_id:
            return StateEffectivenessContribution()
        if ctx.states.has_instance(cause.instance_id):
            return StateEffectivenessContribution(
                suppression_causes=(
                    SuppressionCause(
                        "TEST_CAUSE",
                        LocalRuleCauseRef(cause.instance_id),
                    ),
                )
            )
        return StateEffectivenessContribution()

    systems.state_effectiveness_policy.register_rule_adapter(
        dependency_adapter
    )
    systems.dependency_evaluation_support.add_dependency(
        StateNode(dependent.instance_id),
        StateNode(cause.instance_id),
    )
    observed = []
    systems.effectiveness_transition_coordinator.register_state_transition_port(
        lambda _ctx, transition: observed.append(transition)
    )
    context.current_round = 2
    context.current_phase = BattlePhase.ROUND_START.value
    due = systems.state_lifecycle_system.due_at(
        context, round_no=2, phase=BattlePhase.ROUND_START.value
    )
    before = systems.effectiveness_transition_coordinator.capture(
        context, tuple(StateNode(item.instance_id) for item in due)
    )
    removed = systems.state_lifecycle_system.expire_at(
        context, round_no=2, phase=BattlePhase.ROUND_START.value
    )
    systems.effectiveness_transition_coordinator.complete_removed_nodes(
        context,
        before,
        tuple(StateNode(item.instance_id) for item in removed),
    )
    assert observed == []


def test_same_envelope_order_is_deterministic() -> None:
    context = make_context()
    register_synthetic(context)
    systems = BattleSystems()
    life = StateLifetimeSpec.round_calendar(
        expires_round=2,
        expires_phase=BattlePhase.ROUND_START.value,
    )
    second = StateInstance(
        instance_id="state-000002",
        state_id="synthetic",
        owner_id="b",
        source_id="a",
        source_skill_id=None,
        applied_round=1,
        applied_phase=BattlePhase.ACTION_ORDER.value,
        lifetime_spec=life,
    )
    first = StateInstance(
        instance_id="state-000001",
        state_id="synthetic",
        owner_id="b",
        source_id="a",
        source_skill_id=None,
        applied_round=1,
        applied_phase=BattlePhase.ACTION_ORDER.value,
        lifetime_spec=life,
    )
    context.states.add(second)
    context.states.add(first)
    context.current_round = 2
    context.current_phase = BattlePhase.ROUND_START.value
    removed = systems.state_lifecycle_system.expire_at(
        context, round_no=2, phase=BattlePhase.ROUND_START.value
    )
    assert [item.instance_id for item in removed] == [
        "state-000001",
        "state-000002",
    ]


def test_rd_sf_003_provenance_remains_project_default() -> None:
    path = (
        Path(__file__).parents[1]
        / "stages"
        / "stage12"
        / "STAGE12_RUNTIME_DEFAULT_LEDGER.md"
    )
    text = path.read_text(encoding="utf-8")
    assert "RD-SF-003" in text
    assert "Same-envelope lifecycle settlement ordering" in text
    assert "PROJECT_RUNTIME_DEFAULT" in text


def _transition_fixture():
    context = make_context()
    register_synthetic(context, "cause")
    register_synthetic(context, "target")
    systems = BattleSystems()
    systems.state_effectiveness_policy.register_rule_adapter(
        state_metadata_adapter
    )
    cause = add_resident(context, systems, state_id="cause")
    target = add_resident(context, systems, state_id="target")
    systems.dependency_evaluation_support.add_dependency(
        StateNode(target.instance_id),
        StateNode(cause.instance_id),
    )
    return context, systems, cause, target


def test_effective_to_suppressed_transition_once() -> None:
    context, systems, cause, target = _transition_fixture()
    before = systems.effectiveness_transition_coordinator.capture(
        context, (StateNode(cause.instance_id),)
    )
    context.metadata["blocked_instances"] = (target.instance_id,)
    transitions = systems.effectiveness_transition_coordinator.settle(
        context, before, (StateNode(cause.instance_id),)
    )
    target_transitions = [
        item for item in transitions
        if getattr(item, "state_instance_id", None) == target.instance_id
    ]
    assert len(target_transitions) == 1
    assert target_transitions[0].before.status is StateEffectivenessStatus.EFFECTIVE
    assert target_transitions[0].after.status is StateEffectivenessStatus.SUPPRESSED


def test_suppressed_to_effective_transition_once() -> None:
    context, systems, cause, target = _transition_fixture()
    context.metadata["blocked_instances"] = (target.instance_id,)
    before = systems.effectiveness_transition_coordinator.capture(
        context, (StateNode(cause.instance_id),)
    )
    context.metadata["blocked_instances"] = ()
    transitions = systems.effectiveness_transition_coordinator.settle(
        context, before, (StateNode(cause.instance_id),)
    )
    target_transitions = [
        item for item in transitions
        if getattr(item, "state_instance_id", None) == target.instance_id
    ]
    assert len(target_transitions) == 1
    assert target_transitions[0].after.status is StateEffectivenessStatus.EFFECTIVE


def test_remove_one_of_two_causes_no_resume_transition() -> None:
    context = make_context()
    for state_id in ("cause-a", "cause-b", "target"):
        register_synthetic(context, state_id)
    systems = BattleSystems()

    causes = {}

    def adapter(ctx, instance, _session):
        if instance.state_id != "target":
            return StateEffectivenessContribution()
        active = [
            value for key, value in causes.items()
            if ctx.states.has_instance(value.instance_id)
        ]
        return StateEffectivenessContribution(
            suppression_causes=tuple(
                SuppressionCause(
                    f"CAUSE_{item.state_id}",
                    LocalRuleCauseRef(item.instance_id),
                )
                for item in active
            )
        )

    systems.state_effectiveness_policy.register_rule_adapter(adapter)
    cause_a = add_resident(context, systems, state_id="cause-a")
    cause_b = add_resident(context, systems, state_id="cause-b")
    target = add_resident(context, systems, state_id="target")
    causes.update(a=cause_a, b=cause_b)
    for cause in (cause_a, cause_b):
        systems.dependency_evaluation_support.add_dependency(
            StateNode(target.instance_id), StateNode(cause.instance_id)
        )

    before = systems.effectiveness_transition_coordinator.capture(
        context, (StateNode(cause_a.instance_id),)
    )
    systems.state_lifecycle_system.remove(context, cause_a.instance_id)
    transitions = systems.effectiveness_transition_coordinator.complete_removed_nodes(
        context, before, (StateNode(cause_a.instance_id),)
    )
    assert all(
        getattr(item, "state_instance_id", None) != target.instance_id
        for item in transitions
    )


def test_remove_last_cause_one_resume_transition() -> None:
    context = make_context()
    for state_id in ("cause", "target"):
        register_synthetic(context, state_id)
    systems = BattleSystems()
    cause = add_resident(context, systems, state_id="cause")
    target = add_resident(context, systems, state_id="target")

    def adapter(ctx, instance, _session):
        if (
            instance.instance_id == target.instance_id
            and ctx.states.has_instance(cause.instance_id)
        ):
            return StateEffectivenessContribution(
                suppression_causes=(
                    SuppressionCause(
                        "CAUSE",
                        LocalRuleCauseRef(cause.instance_id),
                    ),
                )
            )
        return StateEffectivenessContribution()

    systems.state_effectiveness_policy.register_rule_adapter(adapter)
    systems.dependency_evaluation_support.add_dependency(
        StateNode(target.instance_id), StateNode(cause.instance_id)
    )
    before = systems.effectiveness_transition_coordinator.capture(
        context, (StateNode(cause.instance_id),)
    )
    systems.state_lifecycle_system.remove(context, cause.instance_id)
    transitions = systems.effectiveness_transition_coordinator.complete_removed_nodes(
        context, before, (StateNode(cause.instance_id),)
    )
    target_transitions = [
        item for item in transitions
        if getattr(item, "state_instance_id", None) == target.instance_id
    ]
    assert len(target_transitions) == 1
    assert target_transitions[0].after.status is StateEffectivenessStatus.EFFECTIVE


def test_resume_transition_is_not_refresh() -> None:
    context, systems, cause, target = _transition_fixture()
    context.metadata["blocked_instances"] = (target.instance_id,)
    suppressed = context.states.get(target.instance_id)
    generation_before = suppressed.current_generation_id
    lifetime_before = suppressed.lifetime_spec
    events_before = context.event_bus.history
    before = systems.effectiveness_transition_coordinator.capture(
        context, (StateNode(cause.instance_id),)
    )
    context.metadata["blocked_instances"] = ()
    transitions = systems.effectiveness_transition_coordinator.settle(
        context, before, (StateNode(cause.instance_id),)
    )
    assert any(
        getattr(item, "state_instance_id", None) == target.instance_id
        for item in transitions
    )
    current = context.states.get(target.instance_id)
    assert current.instance_id == suppressed.instance_id
    assert current.current_generation_id == generation_before
    assert current.lifetime_spec == lifetime_before
    assert context.event_bus.history == events_before


def test_duplicate_query_no_transition() -> None:
    context, systems, cause, _target = _transition_fixture()
    before = systems.effectiveness_transition_coordinator.capture(
        context, (StateNode(cause.instance_id),)
    )
    assert (
        systems.effectiveness_transition_coordinator.settle(
            context, before, (StateNode(cause.instance_id),)
        )
        == ()
    )


def test_dependency_closure_only_recomputes_affected_nodes() -> None:
    context = make_context()
    for state_id in ("cause", "target", "unrelated"):
        register_synthetic(context, state_id)
    systems = BattleSystems()
    cause = add_resident(context, systems, state_id="cause")
    target = add_resident(context, systems, state_id="target")
    unrelated = add_resident(context, systems, state_id="unrelated")
    counts = {}

    def counting_adapter(_ctx, instance, _session):
        counts[instance.instance_id] = counts.get(instance.instance_id, 0) + 1
        return StateEffectivenessContribution()

    systems.state_effectiveness_policy.register_rule_adapter(counting_adapter)
    systems.dependency_evaluation_support.add_dependency(
        StateNode(target.instance_id), StateNode(cause.instance_id)
    )
    systems.effectiveness_transition_coordinator.capture(
        context, (StateNode(cause.instance_id),)
    )
    systems.effectiveness_transition_coordinator.settle(
        context,
        systems.effectiveness_transition_coordinator.capture(
            context, (StateNode(cause.instance_id),)
        ),
        (StateNode(cause.instance_id),),
    )
    assert counts.get(unrelated.instance_id, 0) == 0
    assert counts.get(cause.instance_id, 0) > 0
    assert counts.get(target.instance_id, 0) > 0


def _provider_transition_fixture():
    context = make_context()
    register_synthetic(context, "cause")
    systems = BattleSystems()
    context.skill_runtimes.register(make_skill_runtime())
    systems.provider_validity_policy.register_rule_adapter(
        provider_metadata_adapter
    )
    cause = add_resident(context, systems, state_id="cause")
    provider = SkillProviderRef(
        "a", SkillSlot.LEARNED_1, "skill-provider"
    )
    systems.dependency_evaluation_support.add_dependency(
        ProviderNode(provider), StateNode(cause.instance_id)
    )
    return context, systems, cause, provider


def test_valid_to_suppressed_transition() -> None:
    context, systems, cause, provider = _provider_transition_fixture()
    before = systems.effectiveness_transition_coordinator.capture(
        context, (StateNode(cause.instance_id),)
    )
    context.metadata["blocked_providers"] = (provider,)
    transitions = systems.effectiveness_transition_coordinator.settle(
        context, before, (StateNode(cause.instance_id),)
    )
    provider_transitions = [
        item for item in transitions if hasattr(item, "provider_node")
    ]
    assert len(provider_transitions) == 1
    assert provider_transitions[0].before.status is ProviderValidityStatus.VALID
    assert provider_transitions[0].after.status is ProviderValidityStatus.SUPPRESSED


def test_suppressed_to_valid_transition() -> None:
    context, systems, cause, provider = _provider_transition_fixture()
    context.metadata["blocked_providers"] = (provider,)
    before = systems.effectiveness_transition_coordinator.capture(
        context, (StateNode(cause.instance_id),)
    )
    context.metadata["blocked_providers"] = ()
    transitions = systems.effectiveness_transition_coordinator.settle(
        context, before, (StateNode(cause.instance_id),)
    )
    provider_transitions = [
        item for item in transitions if hasattr(item, "provider_node")
    ]
    assert len(provider_transitions) == 1
    assert provider_transitions[0].after.status is ProviderValidityStatus.VALID


def test_multiple_provider_causes_no_false_resume() -> None:
    context, systems, cause, provider = _provider_transition_fixture()
    register_synthetic(context, "cause-2")
    cause2 = add_resident(context, systems, state_id="cause-2")
    systems.dependency_evaluation_support.add_dependency(
        ProviderNode(provider), StateNode(cause2.instance_id)
    )

    active = {cause.instance_id, cause2.instance_id}

    def cause_adapter(ctx, ref, _session):
        if ref != provider:
            return ()
        return tuple(
            SuppressionCause(key, LocalRuleCauseRef(key))
            for key in sorted(active)
            if ctx.states.has_instance(key)
        )

    systems.provider_validity_policy._rule_adapters.clear()
    systems.provider_validity_policy.register_rule_adapter(cause_adapter)
    before = systems.effectiveness_transition_coordinator.capture(
        context, (StateNode(cause.instance_id),)
    )
    systems.state_lifecycle_system.remove(context, cause.instance_id)
    transitions = systems.effectiveness_transition_coordinator.complete_removed_nodes(
        context, before, (StateNode(cause.instance_id),)
    )
    assert all(not hasattr(item, "provider_node") for item in transitions)


def test_legacy_apply_conflict_surface_preserved() -> None:
    context = make_context()
    register_official_state_definitions(context.states)
    systems = BattleSystems()
    systems.state_lifecycle_system.apply(
        context,
        state_id=OfficialStateId.COMBO.value,
        owner_id="b",
        source_id="a",
        runtime_params=ComboStateParams(),
    )
    with pytest.raises(ValueError, match="COMBO already exists"):
        systems.state_lifecycle_system.apply(
            context,
            state_id=OfficialStateId.COMBO.value,
            owner_id="b",
            source_id="a",
            runtime_params=ComboStateParams(),
        )


def test_battle_systems_wires_single_round2_foundation_graph() -> None:
    systems = BattleSystems()
    assert (
        systems.state_application_coordinator._dependencies
        is systems.dependency_evaluation_support
    )
    assert (
        systems.effectiveness_transition_coordinator.dependency_support
        is systems.dependency_evaluation_support
    )
    assert (
        systems.state_application_coordinator._lifecycle
        is systems.state_lifecycle_system
    )
    assert (
        systems.state_removal_coordinator._lifecycle
        is systems.state_lifecycle_system
    )


def test_round2_policy_modules_do_not_directly_mutate_state_registry() -> None:
    root = Path(__file__).parents[1] / "sgs_v2" / "battle_core"
    for name in ("state_application.py", "state_removal.py"):
        tree = ast.parse((root / name).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not isinstance(func, ast.Attribute):
                continue
            if func.attr not in {"add", "remove", "replace"}:
                continue
            rendered = ast.unparse(func.value)
            assert "context.states" not in rendered


def test_only_lifecycle_performs_round2_physical_state_write() -> None:
    root = Path(__file__).parents[1] / "sgs_v2" / "battle_core"
    for name in (
        "state_application.py",
        "state_removal.py",
        "effectiveness_transition.py",
        "state_lifetime.py",
    ):
        source = (root / name).read_text(encoding="utf-8")
        assert "context.states.add(" not in source
        assert "context.states.remove(" not in source
        assert "context.states.replace(" not in source


def test_application_coordinator_calls_lifecycle_not_registry_writer() -> None:
    path = Path(__file__).parents[1] / "sgs_v2" / "battle_core" / "state_application.py"
    source = path.read_text(encoding="utf-8")
    assert "commit_application_transaction" in source
    assert "context.states.add(" not in source
    assert "context.states.remove(" not in source
    assert "context.states.replace(" not in source


def test_lifecycle_does_not_instantiate_application_coordinator() -> None:
    path = (
        Path(__file__).parents[1]
        / "sgs_v2"
        / "battle_core"
        / "state_lifecycle_system.py"
    )
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    constructed = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "StateApplicationCoordinator" not in constructed


def test_transition_coordinator_does_not_mutate_registry() -> None:
    path = (
        Path(__file__).parents[1]
        / "sgs_v2"
        / "battle_core"
        / "effectiveness_transition.py"
    )
    source = path.read_text(encoding="utf-8")
    assert "context.states.add(" not in source
    assert "context.states.remove(" not in source
    assert "context.states.replace(" not in source


def test_round2_foundation_contains_no_stage12_gameplay_switches() -> None:
    root = Path(__file__).parents[1] / "sgs_v2" / "battle_core"
    forbidden = (
        "INSIGHT",
        "EXHAUSTION",
        "FALSE_REPORT",
        "PROVOCATION",
        "INTIMIDATION",
        "SABOTAGE",
        "CAPTURE",
        "690089",
        "690101",
        "690107",
        "690108",
        "690222",
        "690109",
        "690110",
    )
    for name in (
        "state_application.py",
        "state_removal.py",
        "state_lifetime.py",
        "effectiveness_transition.py",
    ):
        source = (root / name).read_text(encoding="utf-8")
        assert all(token not in source for token in forbidden)


def test_round2_transaction_modules_use_no_random_module_or_context_random() -> None:
    root = Path(__file__).parents[1] / "sgs_v2" / "battle_core"
    for name in (
        "state_application.py",
        "state_removal.py",
        "state_lifetime.py",
        "effectiveness_transition.py",
    ):
        tree = ast.parse((root / name).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(alias.name != "random" for alias in node.names)
            if isinstance(node, ast.ImportFrom):
                assert node.module != "random"
            if isinstance(node, ast.Attribute):
                assert not (
                    isinstance(node.value, ast.Name)
                    and node.value.id == "context"
                    and node.attr == "random"
                )
