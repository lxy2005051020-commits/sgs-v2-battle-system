from __future__ import annotations

import pytest

from sgs_v2.battle_core import (
    BattleContext,
    BattleEngine,
    BattlePhase,
    BattleSystems,
    DependencyCycleError,
    EmptyStateRuntimeParams,
    EventBus,
    EventType,
    LineupPosition,
    OfficialStateId,
    ProviderDependency,
    ProviderNode,
    RandomSystem,
    RemovalOperation,
    SkillProviderRef,
    SkillSlot,
    StateApplicationResultStatus,
    StateCandidate,
    StateEffectivenessContribution,
    StateEffectivenessStatus,
    StateLifetimeSpec,
    StateNode,
    SuppressionCause,
    LocalRuleCauseRef,
    UnitRuntime,
    register_official_state_definitions,
)


def make_context(seed: int = 69008999) -> BattleContext:
    context = BattleContext(
        battle_id=f"stage12-insight-freeze-audit-{seed}",
        units={
            "a0": UnitRuntime(
                "a0", "A0", "A", 1000, 1000, 100, 100, 100,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "b0": UnitRuntime(
                "b0", "B0", "B", 1000, 1000, 100, 100, 90,
                lineup_position=LineupPosition.COMMANDER,
            ),
        },
        event_bus=EventBus(),
        random=RandomSystem(seed),
    )
    register_official_state_definitions(context.states)
    context.current_round = 1
    context.current_phase = BattlePhase.ACTION_ORDER.value
    return context


def candidate(
    state_id: str,
    *,
    lifetime_spec: StateLifetimeSpec | None = None,
) -> StateCandidate:
    return StateCandidate(
        state_id=state_id,
        owner_id="a0",
        source_id="b0",
        source_skill_id=f"audit-source-{state_id}",
        source_skill_slot=SkillSlot.LEARNED_1,
        runtime_params_candidate=EmptyStateRuntimeParams(),
        lifetime_spec=lifetime_spec,
        application_provenance="stage12-690089-runtime-freeze-audit",
    )


def apply(
    systems: BattleSystems,
    context: BattleContext,
    state_id: str,
    *,
    lifetime_spec: StateLifetimeSpec | None = None,
):
    return systems.state_application_coordinator.apply_candidate(
        context,
        candidate(state_id, lifetime_spec=lifetime_spec),
    )


def event_count(context: BattleContext, event_type: EventType) -> int:
    return sum(
        1 for event in context.event_bus.history
        if event.event_type is event_type
    )


def settle_due(
    systems: BattleSystems,
    context: BattleContext,
    *,
    round_no: int,
    phase: str,
):
    due = systems.state_lifecycle_system.due_at(
        context,
        round_no=round_no,
        phase=phase,
    )
    roots = tuple(StateNode(item.instance_id) for item in due)
    before = systems.effectiveness_transition_coordinator.capture(context, roots)
    removed = systems.state_lifecycle_system.expire_at(
        context,
        round_no=round_no,
        phase=phase,
    )
    systems.effectiveness_transition_coordinator.complete_removed_nodes(
        context,
        before,
        tuple(StateNode(item.instance_id) for item in removed),
    )
    return removed


def test_insight_dependency_cycle_rejects_atomically() -> None:
    context = make_context()
    systems = BattleSystems()
    protected = apply(
        systems, context, OfficialStateId.CONFUSION.value
    ).instance
    assert protected is not None

    prospective_insight = StateNode(context.states.peek_next_instance_id())
    protected_node = StateNode(protected.instance_id)
    provider_ref = SkillProviderRef(
        "a0", SkillSlot.LEARNED_1, "audit-cycle-provider"
    )
    provider_node = ProviderNode(provider_ref)
    systems.dependency_evaluation_support.add_dependency(
        provider_node, protected_node
    )

    generation_before = context.generation_allocator._generation_seq
    events_before = context.event_bus.history

    insight_candidate = candidate(OfficialStateId.INSIGHT.value)
    insight_candidate = StateCandidate(
        state_id=insight_candidate.state_id,
        owner_id=insight_candidate.owner_id,
        source_id=insight_candidate.source_id,
        source_skill_id=insight_candidate.source_skill_id,
        source_skill_slot=insight_candidate.source_skill_slot,
        runtime_params_candidate=insight_candidate.runtime_params_candidate,
        lifetime_spec=insight_candidate.lifetime_spec,
        provider_dependencies=(
            ProviderDependency(provider_ref, "AUDIT_CYCLE_PROVIDER"),
        ),
        application_provenance=insight_candidate.application_provenance,
    )

    with pytest.raises(DependencyCycleError):
        systems.state_application_coordinator.apply_candidate(
            context, insight_candidate
        )

    assert not context.states.has(
        owner_id="a0", state_id=OfficialStateId.INSIGHT.value
    )
    assert context.generation_allocator._generation_seq == generation_before
    assert context.event_bus.history == events_before
    assert systems.dependency_evaluation_support.prerequisites(
        protected_node
    ) == ()
    assert systems.dependency_evaluation_support.prerequisites(
        provider_node
    ) == (protected_node,)
    assert systems.dependency_evaluation_support.prerequisites(
        prospective_insight
    ) == ()


def test_insight_dependency_cleanup_on_natural_expiry() -> None:
    context = make_context()
    systems = BattleSystems()
    protected = apply(
        systems,
        context,
        OfficialStateId.CONFUSION.value,
        lifetime_spec=StateLifetimeSpec.round_calendar(expires_round=4),
    ).instance
    insight = apply(
        systems,
        context,
        OfficialStateId.INSIGHT.value,
        lifetime_spec=StateLifetimeSpec.round_calendar(expires_round=2),
    ).instance
    assert protected is not None and insight is not None

    protected_node = StateNode(protected.instance_id)
    insight_node = StateNode(insight.instance_id)
    assert systems.dependency_evaluation_support.prerequisites(
        protected_node
    ) == (insight_node,)

    settle_due(
        systems,
        context,
        round_no=2,
        phase=BattlePhase.ROUND_END.value,
    )

    assert context.states.has_instance(protected.instance_id)
    assert not context.states.has_instance(insight.instance_id)
    assert systems.dependency_evaluation_support.prerequisites(
        protected_node
    ) == ()
    assert systems.dependency_evaluation_support.dependents(
        insight_node
    ) == ()


def test_insight_dependency_cleanup_on_real_battle_teardown() -> None:
    context = make_context()
    systems = BattleSystems()
    protected = apply(
        systems, context, OfficialStateId.CONFUSION.value
    ).instance
    insight = apply(
        systems, context, OfficialStateId.INSIGHT.value
    ).instance
    assert protected is not None and insight is not None

    protected_node = StateNode(protected.instance_id)
    insight_node = StateNode(insight.instance_id)
    assert systems.dependency_evaluation_support.prerequisites(
        protected_node
    ) == (insight_node,)

    context.get_unit("b0").troops = 0
    BattleEngine(context, systems).run()

    assert context.states.find() == []
    assert systems.dependency_evaluation_support.prerequisites(
        protected_node
    ) == ()
    assert systems.dependency_evaluation_support.dependents(
        insight_node
    ) == ()


@pytest.mark.parametrize(
    "state_id",
    (
        OfficialStateId.FALSE_REPORT.value,
        OfficialStateId.INTIMIDATION.value,
        OfficialStateId.CAPTURE.value,
    ),
)
def test_negative_exclusion_resident_is_not_suppressed(
    state_id: str,
) -> None:
    context = make_context()
    systems = BattleSystems()
    excluded = apply(systems, context, state_id).instance
    assert excluded is not None

    apply(systems, context, OfficialStateId.INSIGHT.value)

    assert systems.state_effectiveness_policy.evaluate_state(
        context, excluded
    ).status is StateEffectivenessStatus.EFFECTIVE
    assert systems.dependency_evaluation_support.prerequisites(
        StateNode(excluded.instance_id)
    ) == ()


def test_present_vs_effective_discriminator_in_one_fixture() -> None:
    context = make_context()
    systems = BattleSystems()

    def suppress_insight(_context, instance, _session):
        if instance.state_id != OfficialStateId.INSIGHT.value:
            return StateEffectivenessContribution()
        return StateEffectivenessContribution(
            suppression_causes=(
                SuppressionCause(
                    "AUDIT_SUPPRESS_INSIGHT",
                    LocalRuleCauseRef("runtime-freeze-audit"),
                ),
            )
        )

    systems.state_effectiveness_policy.register_rule_adapter(suppress_insight)
    insight = apply(
        systems, context, OfficialStateId.INSIGHT.value
    ).instance
    assert insight is not None
    assert systems.state_effectiveness_policy.evaluate_state(
        context, insight
    ).status is StateEffectivenessStatus.SUPPRESSED

    control = apply(
        systems, context, OfficialStateId.CONFUSION.value
    )
    duplicate_insight = apply(
        systems, context, OfficialStateId.INSIGHT.value
    )

    assert control.status is StateApplicationResultStatus.APPLIED
    assert duplicate_insight.status is StateApplicationResultStatus.REJECTED_CONFLICT


def test_suppressed_insight_dependency_cascade_has_single_transitions() -> None:
    context = make_context()
    systems = BattleSystems()
    gate = {"suppressed": False}

    def conditional_insight_suppressor(_context, instance, _session):
        if (
            instance.state_id != OfficialStateId.INSIGHT.value
            or not gate["suppressed"]
        ):
            return StateEffectivenessContribution()
        return StateEffectivenessContribution(
            suppression_causes=(
                SuppressionCause(
                    "AUDIT_DYNAMIC_INSIGHT_SUPPRESSION",
                    LocalRuleCauseRef("runtime-freeze-audit"),
                ),
            )
        )

    systems.state_effectiveness_policy.register_rule_adapter(
        conditional_insight_suppressor
    )
    protected = apply(
        systems, context, OfficialStateId.CONFUSION.value
    ).instance
    insight = apply(
        systems, context, OfficialStateId.INSIGHT.value
    ).instance
    assert protected is not None and insight is not None
    assert systems.state_effectiveness_policy.evaluate_state(
        context, protected
    ).status is StateEffectivenessStatus.SUPPRESSED

    insight_node = StateNode(insight.instance_id)
    before = systems.effectiveness_transition_coordinator.capture(
        context, (insight_node,)
    )
    suppress_before = event_count(context, EventType.STATE_SUPPRESSED)
    resume_before = event_count(context, EventType.STATE_RESUMED)

    gate["suppressed"] = True
    transitions = systems.effectiveness_transition_coordinator.settle(
        context, before, (insight_node,)
    )

    assert systems.state_effectiveness_policy.evaluate_state(
        context, insight
    ).status is StateEffectivenessStatus.SUPPRESSED
    assert systems.state_effectiveness_policy.evaluate_state(
        context, protected
    ).status is StateEffectivenessStatus.EFFECTIVE
    assert len(transitions) == 2
    assert event_count(
        context, EventType.STATE_SUPPRESSED
    ) == suppress_before + 1
    assert event_count(
        context, EventType.STATE_RESUMED
    ) == resume_before + 1

    before = systems.effectiveness_transition_coordinator.capture(
        context, (insight_node,)
    )
    gate["suppressed"] = False
    transitions = systems.effectiveness_transition_coordinator.settle(
        context, before, (insight_node,)
    )

    assert systems.state_effectiveness_policy.evaluate_state(
        context, insight
    ).status is StateEffectivenessStatus.EFFECTIVE
    assert systems.state_effectiveness_policy.evaluate_state(
        context, protected
    ).status is StateEffectivenessStatus.SUPPRESSED
    assert len(transitions) == 2
    assert event_count(
        context, EventType.STATE_SUPPRESSED
    ) == suppress_before + 2
    assert event_count(
        context, EventType.STATE_RESUMED
    ) == resume_before + 2
