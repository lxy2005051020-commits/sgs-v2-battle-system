from __future__ import annotations

import inspect

import pytest

from sgs_v2.battle_core import (
    BattleContext,
    BattlePhase,
    BattleSystems,
    DamageSkillEffectSpec,
    DamageType,
    EmptyStateRuntimeParams,
    EventBus,
    EventType,
    LineupPosition,
    OfficialStateId,
    ProviderDependency,
    RandomSystem,
    RemovalOperation,
    SkillDefinition,
    SkillProviderRef,
    SkillResolutionStatus,
    SkillRuntime,
    SkillSlot,
    SkillTargetMode,
    SkillType,
    StateApplicationResultStatus,
    StateCandidate,
    StateLifetimeSpec,
    StateNode,
    TargetCardinality,
    TargetEligibilityContext,
    TargetOperationDomain,
    TargetOperationProducer,
    TargetPolicyBoundary,
    TargetPolicyContribution,
    TargetPurpose,
    TargetQueryMode,
    TargetRelation,
    TargetSelectionProvenance,
    TargetSelectionResult,
    TargetSelectorKind,
    TauntStateParams,
    UnitRuntime,
    register_official_state_definitions,
)
from sgs_v2.battle_core import provocation_integration as provoke_module
from sgs_v2.battle_core.provocation_integration import (
    PROVOCATION_CONFUSION_PREEMPTION_KEY,
    PROVOCATION_REAPPLICATION_BOUNDARY_RULE_ID,
)


class CountingRandomSystem(RandomSystem):
    def __init__(self, seed: int = 690108) -> None:
        super().__init__(seed)
        self.sample_calls = 0
        self.sample_ks: list[int] = []
        self.sample_populations: list[tuple[str, ...]] = []
        self.choice_calls = 0
        self.chance_calls = 0

    def sample(self, values, k):  # type: ignore[no-untyped-def]
        self.sample_calls += 1
        self.sample_ks.append(k)
        self.sample_populations.append(
            tuple(getattr(item, "unit_id", str(item)) for item in values)
        )
        return super().sample(values, k)

    def choice(self, values):  # type: ignore[no-untyped-def]
        self.choice_calls += 1
        return super().choice(values)

    def chance(self, probability: float) -> bool:
        self.chance_calls += 1
        return super().chance(probability)


def make_context(
    seed: int = 690108,
    random_system: RandomSystem | None = None,
) -> BattleContext:
    context = BattleContext(
        battle_id=f"stage12-provocation-{seed}",
        units={
            "a": UnitRuntime(
                "a", "A", "A", 1000, 1000, 300, 100, 100,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "x": UnitRuntime(
                "x", "X", "A", 1000, 1000, 100, 100, 95,
                lineup_position=LineupPosition.DEPUTY_1,
            ),
            "b": UnitRuntime(
                "b", "B", "B", 1000, 1000, 100, 100, 90,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "c": UnitRuntime(
                "c", "C", "B", 1000, 1000, 100, 100, 85,
                lineup_position=LineupPosition.DEPUTY_1,
            ),
            "d": UnitRuntime(
                "d", "D", "B", 1000, 1000, 100, 100, 80,
                lineup_position=LineupPosition.DEPUTY_2,
            ),
        },
        event_bus=EventBus(),
        random=random_system or CountingRandomSystem(seed),
    )
    register_official_state_definitions(context.states)
    context.current_round = 1
    context.current_phase = BattlePhase.ACTION_ORDER.value
    return context


def runtime(
    *,
    mode: SkillTargetMode = SkillTargetMode.SINGLE_RANDOM_ENEMY,
    target_count: int | None = None,
    restriction_keys: tuple[str, ...] = (),
    owner: str = "a",
    slot: SkillSlot = SkillSlot.INHERENT,
    skill_id: str = "provocation-target-skill",
    skill_type: SkillType = SkillType.ACTIVE,
    activation_rate: float = 1.0,
) -> SkillRuntime:
    return SkillRuntime(
        definition=SkillDefinition(
            skill_id=skill_id,
            name=skill_id,
            activation_rate=activation_rate,
            target_mode=mode,
            target_count=target_count,
            target_restriction_keys=restriction_keys,
            effect_specs=(DamageSkillEffectSpec(DamageType.WEAPON),),
            skill_type=skill_type,
        ),
        owner_id=owner,
        skill_slot=slot,
    )


def state_candidate(
    state_id: str,
    *,
    owner: str = "a",
    source: str | None = "b",
    source_skill_id: str | None = None,
    source_skill_slot: SkillSlot | None = None,
    lifetime: StateLifetimeSpec | None = None,
    dependencies: tuple[ProviderDependency, ...] = (),
    runtime_params=None,
) -> StateCandidate:
    if runtime_params is None:
        runtime_params = EmptyStateRuntimeParams()
    return StateCandidate(
        state_id=state_id,
        owner_id=owner,
        source_id=source,
        source_skill_id=source_skill_id,
        source_skill_slot=source_skill_slot,
        runtime_params_candidate=runtime_params,
        lifetime_spec=lifetime,
        provider_dependencies=dependencies,
        application_provenance="stage12-690108-contract-test",
    )


def apply_state(
    systems: BattleSystems,
    context: BattleContext,
    state_id: str,
    **kwargs,
):
    return systems.state_application_coordinator.apply_candidate(
        context,
        state_candidate(state_id, **kwargs),
    )


def apply_provocation(
    systems: BattleSystems,
    context: BattleContext,
    **kwargs,
):
    return apply_state(
        systems,
        context,
        OfficialStateId.PROVOKE.value,
        **kwargs,
    )


def register_source_provider(
    context: BattleContext,
    *,
    owner: str = "b",
    slot: SkillSlot = SkillSlot.INHERENT,
    skill_id: str = "provocation-source-provider",
    skill_type: SkillType = SkillType.COMMAND,
) -> SkillRuntime:
    item = runtime(
        owner=owner,
        slot=slot,
        skill_id=skill_id,
        skill_type=skill_type,
    )
    context.skill_runtimes.register(item)
    return item


def provider_ref(item: SkillRuntime) -> SkillProviderRef:
    assert item.skill_slot is not None
    return SkillProviderRef(
        item.owner_id,
        item.skill_slot,
        item.definition.skill_id,
    )


def operation(
    context: BattleContext,
    *,
    relation: TargetRelation = TargetRelation.ENEMY,
    cardinality: TargetCardinality = TargetCardinality.SINGLE,
    selector: TargetSelectorKind = TargetSelectorKind.RANDOM,
    requested_count: int | None = None,
    restriction_keys: tuple[str, ...] = (),
):
    return TargetOperationProducer.new_query(
        context,
        actor_id="a",
        producer_ref=SkillProviderRef(
            "a", SkillSlot.INHERENT, "operation-fixture"
        ),
        admitted_operation_key="stage12-690108-operation-fixture",
        relation=relation,
        cardinality=cardinality,
        selector_kind=selector,
        eligibility_context=TargetEligibilityContext(
            domain=TargetOperationDomain.SKILL,
            purpose=(
                TargetPurpose.HOSTILE
                if relation is TargetRelation.ENEMY
                else TargetPurpose.FRIENDLY_SUPPORT
                if relation is TargetRelation.ALLY
                else TargetPurpose.SELF
            ),
            restriction_keys=restriction_keys,
        ),
        requested_count=requested_count,
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


def event_count(context: BattleContext, event_type: EventType) -> int:
    return sum(
        1
        for event in context.event_bus.history
        if event.event_type is event_type
    )


def capture_operation(systems: BattleSystems):
    captured = []

    def adapter(_context, target_operation, _raw_ids):
        captured.append(target_operation)
        return None

    systems.skill_target_policy.register_rule_adapter(adapter)
    return captured


def resolve_skill(
    systems: BattleSystems,
    context: BattleContext,
    item: SkillRuntime,
):
    """Resolve through the production provider registry/admission path."""

    assert item.skill_slot is not None
    existing = context.skill_runtimes.get(item.owner_id, item.skill_slot)
    if existing is None:
        context.skill_runtimes.register(item)
    elif existing is not item:
        raise ValueError("test fixture attempted to replace an occupied skill slot")
    return systems.skill_resolver.resolve(context, item)


def test_provocation_application_and_effective_truth() -> None:
    context, systems = make_context(), BattleSystems()
    result = apply_provocation(systems, context)
    assert result.status is StateApplicationResultStatus.APPLIED
    assert result.instance is not None
    assert systems.state_effectiveness_policy.evaluate_state(
        context, result.instance
    ).effective


def test_provocation_application_consumes_zero_rng() -> None:
    rng = CountingRandomSystem()
    context, systems = make_context(random_system=rng), BattleSystems()
    apply_provocation(systems, context)
    assert (rng.chance_calls, rng.sample_calls, rng.choice_calls) == (0, 0, 0)


def test_provocation_natural_expiry() -> None:
    context, systems = make_context(), BattleSystems()
    item = apply_provocation(
        systems,
        context,
        lifetime=StateLifetimeSpec.round_calendar(expires_round=2),
    ).instance
    assert item is not None
    removed = settle_due(
        systems,
        context,
        round_no=2,
        phase=BattlePhase.ROUND_END.value,
    )
    assert item.instance_id in {x.instance_id for x in removed}
    assert not context.states.has_instance(item.instance_id)


@pytest.mark.parametrize("source", ["b", "c"])
def test_provocation_reapplication_remains_bu_p06_unsupported(source: str) -> None:
    context, systems = make_context(), BattleSystems()
    first = apply_provocation(systems, context, source="b")
    assert first.status is StateApplicationResultStatus.APPLIED
    second = apply_provocation(systems, context, source=source)
    assert second.status is StateApplicationResultStatus.UNSUPPORTED_BOUNDARY
    assert (
        second.reason_rule_id
        == PROVOCATION_REAPPLICATION_BOUNDARY_RULE_ID
    )


def test_single_admissible_source_is_forced_with_zero_target_rng() -> None:
    rng = CountingRandomSystem()
    context, systems = make_context(random_system=rng), BattleSystems()
    apply_provocation(systems, context, source="b")
    result = resolve_skill(systems, context, runtime())
    assert result.status is SkillResolutionStatus.RESOLVED
    assert result.target_ids == ("b",)
    assert rng.sample_calls == 0


def test_single_deterministic_selector_is_also_forced() -> None:
    rng = CountingRandomSystem()
    context, systems = make_context(random_system=rng), BattleSystems()
    apply_provocation(systems, context, source="d")
    result = resolve_skill(systems, 
        context,
        runtime(mode=SkillTargetMode.SINGLE_DETERMINISTIC_ENEMY),
    )
    assert result.target_ids == ("d",)
    assert rng.sample_calls == 0


def test_illegal_source_not_in_raw_candidates_does_not_force_and_state_remains() -> None:
    context, systems = make_context(seed=7), BattleSystems()
    item = apply_provocation(systems, context, source="x").instance
    assert item is not None
    result = resolve_skill(systems, context, runtime())
    assert result.target_ids[0] in {"b", "c", "d"}
    assert context.states.has_instance(item.instance_id)


def test_dead_source_does_not_force_and_state_remains() -> None:
    context, systems = make_context(seed=8), BattleSystems()
    item = apply_provocation(systems, context, source="b").instance
    assert item is not None
    context.get_unit("b").troops = 0
    result = resolve_skill(systems, context, runtime())
    assert result.target_ids[0] in {"c", "d"}
    assert context.states.has_instance(item.instance_id)


def test_wrong_relation_does_not_force_source() -> None:
    context, systems = make_context(), BattleSystems()
    apply_provocation(systems, context, source="b")
    decision = systems.skill_target_policy.evaluate(
        context,
        operation(context, relation=TargetRelation.ALLY),
        ("x",),
    )
    assert decision.required_target_ids == ()


def test_explicit_exclusion_makes_source_illegal_without_consuming_state() -> None:
    context, systems = make_context(seed=11), BattleSystems()
    item = apply_provocation(systems, context, source="b").instance
    assert item is not None

    def exclude_b(_context, _operation, _raw_ids):
        return TargetPolicyContribution(excluded_target_ids=("b",))

    systems.skill_target_policy.register_rule_adapter(exclude_b)
    result = resolve_skill(systems, context, runtime())
    assert result.target_ids[0] in {"c", "d"}
    assert context.states.has_instance(item.instance_id)


def test_choose_n_includes_source_exactly_once_and_preserves_cardinality() -> None:
    context, systems = make_context(seed=12), BattleSystems()
    apply_provocation(systems, context, source="b")
    result = resolve_skill(systems, 
        context,
        runtime(
            mode=SkillTargetMode.CHOOSE_N_RANDOM_ENEMIES,
            target_count=2,
        ),
    )
    assert len(result.target_ids) == 2
    assert result.target_ids.count("b") == 1


def test_choose_n_reserve_first_excludes_source_and_samples_n_minus_one() -> None:
    rng = CountingRandomSystem(13)
    context, systems = make_context(random_system=rng), BattleSystems()
    apply_provocation(systems, context, source="b")
    resolve_skill(systems, 
        context,
        runtime(
            mode=SkillTargetMode.CHOOSE_N_RANDOM_ENEMIES,
            target_count=2,
        ),
    )
    assert rng.sample_calls == 1
    assert rng.sample_ks == [1]
    assert "b" not in rng.sample_populations[0]


def test_choose_n_n_equals_one_consumes_zero_sample_rng() -> None:
    rng = CountingRandomSystem(14)
    context, systems = make_context(random_system=rng), BattleSystems()
    apply_provocation(systems, context, source="b")
    result = resolve_skill(systems, 
        context,
        runtime(
            mode=SkillTargetMode.CHOOSE_N_RANDOM_ENEMIES,
            target_count=1,
        ),
    )
    assert result.target_ids == ("b",)
    assert rng.sample_calls == 0


def test_choose_n_full_remaining_fill_consumes_zero_sample_rng() -> None:
    rng = CountingRandomSystem(15)
    context, systems = make_context(random_system=rng), BattleSystems()
    apply_provocation(systems, context, source="b")
    result = resolve_skill(systems, 
        context,
        runtime(
            mode=SkillTargetMode.CHOOSE_N_RANDOM_ENEMIES,
            target_count=3,
        ),
    )
    assert set(result.target_ids) == {"b", "c", "d"}
    assert len(result.target_ids) == 3
    assert rng.sample_calls == 0


def test_choose_n_deterministic_selector_preserves_source_and_uses_zero_rng() -> None:
    rng = CountingRandomSystem(16)
    context, systems = make_context(random_system=rng), BattleSystems()
    apply_provocation(systems, context, source="d")
    result = resolve_skill(systems, 
        context,
        runtime(
            mode=SkillTargetMode.CHOOSE_N_DETERMINISTIC_ENEMIES,
            target_count=2,
        ),
    )
    assert result.target_ids[0] == "d"
    assert len(result.target_ids) == 2
    assert rng.sample_calls == 0


def test_choose_n_replay_preserves_result_rng_topology_and_downstream_stream() -> None:
    outputs = []
    for _ in range(2):
        rng = CountingRandomSystem(17)
        context, systems = make_context(random_system=rng), BattleSystems()
        apply_provocation(systems, context, source="b")
        result = resolve_skill(systems, 
            context,
            runtime(
                mode=SkillTargetMode.CHOOSE_N_RANDOM_ENEMIES,
                target_count=2,
            ),
        )
        outputs.append(
            (
                result.target_ids,
                rng.sample_calls,
                tuple(rng.sample_ks),
                tuple(rng.sample_populations),
                context.random.random(),
            )
        )
    assert outputs[0] == outputs[1]


def test_choose_n_insufficient_candidates_is_explicit_unsupported_boundary() -> None:
    context, systems = make_context(), BattleSystems()
    apply_provocation(systems, context, source="b")
    with pytest.raises(ValueError, match="unsupported Skill target-policy boundary"):
        resolve_skill(systems, 
            context,
            runtime(
                mode=SkillTargetMode.CHOOSE_N_RANDOM_ENEMIES,
                target_count=4,
            ),
        )


def test_choose_n_illegal_source_preserves_original_selector_behavior() -> None:
    outputs = []
    for with_provocation in (False, True):
        rng = CountingRandomSystem(18)
        context, systems = make_context(random_system=rng), BattleSystems()
        if with_provocation:
            apply_provocation(systems, context, source="x")
        result = resolve_skill(systems, 
            context,
            runtime(
                mode=SkillTargetMode.CHOOSE_N_RANDOM_ENEMIES,
                target_count=2,
            ),
        )
        outputs.append((result.target_ids, rng.sample_calls))
    assert outputs[0] == outputs[1]


def test_fixed_all_is_unchanged_when_source_is_legal() -> None:
    rng = CountingRandomSystem(19)
    context, systems = make_context(random_system=rng), BattleSystems()
    apply_provocation(systems, context, source="b")
    result = resolve_skill(systems, 
        context,
        runtime(mode=SkillTargetMode.FIXED_ALL_ENEMIES),
    )
    assert result.target_ids == ("b", "c", "d")
    assert rng.sample_calls == 0


def test_fixed_all_does_not_insert_illegal_source() -> None:
    context, systems = make_context(), BattleSystems()
    apply_provocation(systems, context, source="x")
    result = resolve_skill(systems, 
        context,
        runtime(mode=SkillTargetMode.FIXED_ALL_ENEMIES),
    )
    assert set(result.target_ids) == {"b", "c", "d"}
    assert "x" not in result.target_ids


@pytest.mark.parametrize(
    "query_mode, provenance",
    [
        (TargetQueryMode.INHERIT_RESOLVED, TargetSelectionProvenance.INHERITED),
        (TargetQueryMode.DERIVE_FROM_RESOLVED, TargetSelectionProvenance.DERIVED),
        (TargetQueryMode.LOCK_RESOLVED, TargetSelectionProvenance.LOCKED),
    ],
)
def test_resolved_continuations_do_not_reenter_provocation(
    query_mode,
    provenance,
) -> None:
    context, systems = make_context(), BattleSystems()
    apply_provocation(systems, context, source="b")
    captured = capture_operation(systems)
    fresh = resolve_skill(systems, context, runtime())
    assert fresh.target_ids == ("b",)
    assert len(captured) == 1

    selected = TargetSelectionResult(
        operation_id=captured[0].operation_id,
        target_ids=fresh.target_ids,
        provenance=TargetSelectionProvenance.FRESH_SELECTED,
    )
    context.get_unit("b").troops = 0
    continued = TargetOperationProducer.continue_from(selected, query_mode)
    assert continued.target_ids == ("b",)
    assert continued.provenance is provenance
    assert len(captured) == 1


def test_independent_new_query_reevaluates_source_admissibility() -> None:
    context, systems = make_context(seed=20), BattleSystems()
    apply_provocation(systems, context, source="b")
    item = runtime()
    context.get_unit("b").troops = 0
    first = resolve_skill(systems, context, item)
    assert first.target_ids[0] in {"c", "d"}

    context.get_unit("b").troops = 1000
    second = resolve_skill(systems, context, item)
    assert second.target_ids == ("b",)


def test_insight_rejects_incoming_provocation() -> None:
    context, systems = make_context(), BattleSystems()
    apply_state(systems, context, OfficialStateId.INSIGHT.value)
    result = apply_provocation(systems, context)
    assert result.status is StateApplicationResultStatus.REJECTED_ADMISSION
    assert not context.states.has(
        owner_id="a",
        state_id=OfficialStateId.PROVOKE.value,
    )


def test_later_insight_suppresses_then_resume_affects_future_query_only() -> None:
    context, systems = make_context(seed=21), BattleSystems()
    provoke = apply_provocation(
        systems,
        context,
        lifetime=StateLifetimeSpec.round_calendar(expires_round=3),
    ).instance
    assert provoke is not None
    captured = capture_operation(systems)
    item = runtime()
    first = resolve_skill(systems, context, item)
    selected = TargetSelectionResult(
        operation_id=captured[-1].operation_id,
        target_ids=first.target_ids,
        provenance=TargetSelectionProvenance.FRESH_SELECTED,
    )
    assert selected.target_ids == ("b",)

    insight = apply_state(
        systems,
        context,
        OfficialStateId.INSIGHT.value,
        lifetime=StateLifetimeSpec.round_calendar(expires_round=2),
    ).instance
    assert insight is not None
    assert not systems.state_effectiveness_policy.evaluate_state(
        context, provoke
    ).effective

    inherited = TargetOperationProducer.continue_from(
        selected,
        TargetQueryMode.INHERIT_RESOLVED,
    )
    assert inherited.target_ids == ("b",)

    settle_due(
        systems,
        context,
        round_no=2,
        phase=BattlePhase.ROUND_END.value,
    )
    current = context.states.get(provoke.instance_id)
    assert systems.state_effectiveness_policy.evaluate_state(
        context, current
    ).effective
    future = resolve_skill(systems, context, item)
    assert future.target_ids == ("b",)


def test_same_envelope_insight_and_provocation_expiry_has_no_transient_resume() -> None:
    context, systems = make_context(), BattleSystems()
    provoke = apply_provocation(
        systems,
        context,
        lifetime=StateLifetimeSpec.round_calendar(expires_round=2),
    ).instance
    insight = apply_state(
        systems,
        context,
        OfficialStateId.INSIGHT.value,
        lifetime=StateLifetimeSpec.round_calendar(expires_round=2),
    ).instance
    assert provoke is not None and insight is not None
    before = event_count(context, EventType.STATE_RESUMED)
    removed = settle_due(
        systems,
        context,
        round_no=2,
        phase=BattlePhase.ROUND_END.value,
    )
    assert {x.instance_id for x in removed} == {
        provoke.instance_id,
        insight.instance_id,
    }
    assert event_count(context, EventType.STATE_RESUMED) == before


def test_exhaustion_denial_short_circuits_before_target_policy() -> None:
    context, systems = make_context(), BattleSystems()
    apply_provocation(systems, context)
    apply_state(systems, context, OfficialStateId.SILENCE.value)
    invocations = []

    def counter(_context, _operation, _raw_ids):
        invocations.append("target-policy")
        return None

    systems.skill_target_policy.register_rule_adapter(counter)
    result = resolve_skill(systems, context, runtime())
    assert result.status is SkillResolutionStatus.DISABLED
    assert invocations == []


def test_false_report_source_provider_dependency_suppresses_and_restores_provocation() -> None:
    context, systems = make_context(), BattleSystems()
    source_provider = register_source_provider(context)
    apply_state(
        systems,
        context,
        OfficialStateId.FALSE_REPORT.value,
        owner="b",
        source="a",
    )
    provoke = apply_provocation(
        systems,
        context,
        source="b",
        dependencies=(
            ProviderDependency(provider_ref(source_provider), "PAIR"),
        ),
    ).instance
    assert provoke is not None
    assert not systems.state_effectiveness_policy.evaluate_state(
        context, provoke
    ).effective

    false_report = context.states.find(
        owner_id="b",
        state_id=OfficialStateId.FALSE_REPORT.value,
    )[0]
    systems.state_removal_coordinator.remove(
        context,
        operation=RemovalOperation.NATURAL_EXPIRY,
        instance_id=false_report.instance_id,
    )
    current = context.states.get(provoke.instance_id)
    assert systems.state_effectiveness_policy.evaluate_state(
        context, current
    ).effective
    assert resolve_skill(systems, context, runtime()).target_ids == ("b",)


@pytest.mark.parametrize(
    "source_skill_id, source_skill_slot",
    [
        ("provocation-source-provider", None),
        (None, SkillSlot.INHERENT),
        ("provocation-source-provider", SkillSlot.INHERENT),
    ],
)
def test_attribution_fields_do_not_infer_provider_dependency(
    source_skill_id,
    source_skill_slot,
) -> None:
    context, systems = make_context(), BattleSystems()
    register_source_provider(context)
    apply_state(
        systems,
        context,
        OfficialStateId.FALSE_REPORT.value,
        owner="b",
        source="a",
    )
    provoke = apply_provocation(
        systems,
        context,
        source="b",
        source_skill_id=source_skill_id,
        source_skill_slot=source_skill_slot,
    ).instance
    assert provoke is not None
    assert systems.dependency_evaluation_support.prerequisites(
        StateNode(provoke.instance_id)
    ) == ()
    assert systems.state_effectiveness_policy.evaluate_state(
        context, provoke
    ).effective


def test_false_report_on_holder_does_not_invalidate_external_source_provider() -> None:
    context, systems = make_context(), BattleSystems()
    source_provider = register_source_provider(context)
    apply_state(
        systems,
        context,
        OfficialStateId.FALSE_REPORT.value,
        owner="a",
        source="c",
    )
    provoke = apply_provocation(
        systems,
        context,
        source="b",
        dependencies=(
            ProviderDependency(provider_ref(source_provider), "PAIR"),
        ),
    ).instance
    assert provoke is not None
    assert systems.state_effectiveness_policy.evaluate_state(
        context, provoke
    ).effective


def test_confusion_preempts_only_when_operation_marks_confusion_as_target_owner() -> None:
    context, systems = make_context(), BattleSystems()
    apply_provocation(systems, context, source="b")
    apply_state(
        systems,
        context,
        OfficialStateId.CONFUSION.value,
        source="c",
    )
    controlled = systems.skill_target_policy.evaluate(
        context,
        operation(
            context,
            restriction_keys=(PROVOCATION_CONFUSION_PREEMPTION_KEY,),
        ),
        ("b", "c", "d"),
    )
    ordinary = systems.skill_target_policy.evaluate(
        context,
        operation(context),
        ("b", "c", "d"),
    )
    assert controlled.required_target_ids == ()
    assert ordinary.required_target_ids == ("b",)


def test_skill_definition_maps_confusion_arbitration_metadata_to_operation() -> None:
    context, systems = make_context(), BattleSystems()
    captured = capture_operation(systems)
    resolve_skill(systems, 
        context,
        runtime(
            restriction_keys=(PROVOCATION_CONFUSION_PREEMPTION_KEY,),
        ),
    )
    assert captured[-1].eligibility_context.restriction_keys == (
        PROVOCATION_CONFUSION_PREEMPTION_KEY,
    )


def test_taunt_does_not_influence_skill_target_policy() -> None:
    context, systems = make_context(), BattleSystems()
    apply_provocation(systems, context, source="b")
    apply_state(
        systems,
        context,
        OfficialStateId.TAUNT.value,
        source="c",
        runtime_params=TauntStateParams(taunt_target_id="c"),
    )
    result = resolve_skill(systems, context, runtime())
    assert result.target_ids == ("b",)


def test_provocation_does_not_influence_normal_attack_target_resolution() -> None:
    outcomes = []
    for with_provocation in (False, True):
        context, systems = make_context(seed=22), BattleSystems()
        if with_provocation:
            apply_provocation(systems, context, source="b")
        resolved = systems.target_resolution_system.resolve(
            context,
            "a",
            normal_attack_id=context.id_allocator.allocate_normal_attack_id(),
        )
        assert resolved is not None
        outcomes.append(resolved.intended_attack_target)
    assert outcomes[0] == outcomes[1]


def test_source_death_does_not_remove_provocation() -> None:
    context, systems = make_context(), BattleSystems()
    provoke = apply_provocation(systems, context, source="b").instance
    assert provoke is not None
    context.get_unit("b").troops = 0
    systems.defeat_cleanup_port.commit_defeat(context, "b")
    assert context.states.has_instance(provoke.instance_id)


def test_target_policy_query_emits_no_event() -> None:
    context, systems = make_context(), BattleSystems()
    apply_provocation(systems, context, source="b")
    before = tuple(context.event_bus.history)
    systems.skill_target_policy.evaluate(
        context,
        operation(context),
        ("b", "c", "d"),
    )
    assert tuple(context.event_bus.history) == before


@pytest.mark.parametrize(
    "mode, target_count, cardinality, selector",
    [
        (
            SkillTargetMode.SINGLE_RANDOM_ENEMY,
            None,
            TargetCardinality.SINGLE,
            TargetSelectorKind.RANDOM,
        ),
        (
            SkillTargetMode.CHOOSE_N_RANDOM_ENEMIES,
            2,
            TargetCardinality.CHOOSE_N,
            TargetSelectorKind.RANDOM,
        ),
        (
            SkillTargetMode.FIXED_ALL_ENEMIES,
            None,
            TargetCardinality.FIXED_ALL,
            TargetSelectorKind.DETERMINISTIC,
        ),
    ],
)
def test_production_skill_definition_maps_to_frozen_target_operation(
    mode,
    target_count,
    cardinality,
    selector,
) -> None:
    context, systems = make_context(seed=23), BattleSystems()
    captured = capture_operation(systems)
    resolve_skill(systems, 
        context,
        runtime(mode=mode, target_count=target_count),
    )
    op = captured[-1]
    assert op.relation is TargetRelation.ENEMY
    assert op.cardinality is cardinality
    assert op.selector_kind is selector
    assert op.requested_count == target_count
    assert op.eligibility_context.domain is TargetOperationDomain.SKILL
    assert op.eligibility_context.purpose is TargetPurpose.HOSTILE


def test_legacy_single_random_enemy_behavior_has_no_drift() -> None:
    outputs = []
    for _ in range(2):
        rng = CountingRandomSystem(24)
        context, systems = make_context(random_system=rng), BattleSystems()
        result = resolve_skill(systems, 
            context,
            runtime(mode=SkillTargetMode.SINGLE_RANDOM_ENEMY),
        )
        outputs.append(
            (result.target_ids, rng.sample_calls, tuple(rng.sample_ks))
        )
    assert outputs[0] == outputs[1]
    assert outputs[0][1:] == (1, (1,))


def test_provocation_static_architecture_guards() -> None:
    source = inspect.getsource(provoke_module)
    assert "context.random" not in source
    assert "import random" not in source
    assert "EventBus" not in source
    assert "NormalAttackSystem" not in source
    assert "ActionSystem" not in source
    assert "TargetResolutionSystem" not in source
    assert "TargetSystem" not in source
    assert "EffectSourceRef" not in source
    assert "source_skill_id" not in source
    assert "source_skill_slot" not in source
    assert "sample" not in source
    assert "replacement" not in source.lower()
