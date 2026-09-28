from __future__ import annotations

import inspect

import pytest

from sgs_v2.battle_core import (
    AdmissionStatus,
    BattleContext,
    BattlePhase,
    BattleSystems,
    DamageSkillEffectSpec,
    DamageType,
    DependencyCycleError,
    EffectSourceRef,
    EmptyStateRuntimeParams,
    EquipmentProviderRef,
    EventBus,
    EventType,
    LineupPosition,
    OfficialStateId,
    PreparationMode,
    ProviderDependency,
    ProviderNode,
    ProviderValidityStatus,
    RandomSystem,
    RecoveryOpportunity,
    RecoveryOpportunityKind,
    RemovalOperation,
    RuleIntentExecutionDescriptor,
    RuleIntentKind,
    SkillDefinition,
    SkillOperationAdmissionRequest,
    SkillOperationAdmissionStatus,
    SkillOperationKind,
    SkillProviderRef,
    SkillRuntime,
    SkillSlot,
    SkillTargetMode,
    SourceType,
    SkillType,
    StateApplicationResultStatus,
    StateCandidate,
    StateEffectivenessStatus,
    StateLifetimeSpec,
    StateNode,
    StateRemovalResultStatus,
    PersistentSourceSkillGate,
    UnitRuntime,
    register_official_state_definitions,
)
from sgs_v2.battle_core import intimidation_integration as intimidation_module
from sgs_v2.battle_core.intimidation_integration import (
    INTIMIDATION_EMPTY_POOL_BOUNDARY_RULE_ID,
    INTIMIDATION_PROVIDER_SUPPRESSION_RULE_ID,
    INTIMIDATION_SUPPORTED_SKILL_TYPES,
    intimidation_eligible_provider_pool,
)


class CountingRandomSystem(RandomSystem):
    def __init__(self, seed: int = 690222) -> None:
        super().__init__(seed)
        self.choice_calls: list[tuple[object, ...]] = []
        self.chance_calls = 0

    def choice(self, values):  # type: ignore[no-untyped-def]
        self.choice_calls.append(tuple(values))
        return super().choice(values)

    def chance(self, probability: float) -> bool:
        self.chance_calls += 1
        return super().chance(probability)


class SequenceChoiceRandomSystem(CountingRandomSystem):
    def __init__(self, indices: tuple[int, ...]) -> None:
        super().__init__(690222)
        self._indices = list(indices)

    def choice(self, values):  # type: ignore[no-untyped-def]
        self.choice_calls.append(tuple(values))
        if not self._indices:
            raise AssertionError("unexpected extra binding choice")
        return values[self._indices.pop(0)]


def make_context(rng: RandomSystem | None = None) -> BattleContext:
    context = BattleContext(
        battle_id="stage12-690222",
        units={
            "a": UnitRuntime(
                "a", "A", "A", 1000, 1000, 300, 100, 100,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "b": UnitRuntime(
                "b", "B", "B", 1000, 1000, 100, 100, 90,
                lineup_position=LineupPosition.COMMANDER,
            ),
        },
        event_bus=EventBus(),
        random=rng or RandomSystem(690222),
    )
    register_official_state_definitions(context.states)
    context.current_round = 1
    context.current_phase = BattlePhase.UNIT_ACTION.value
    return context


def skill(
    context: BattleContext,
    *,
    owner: str = "a",
    slot: SkillSlot = SkillSlot.INHERENT,
    skill_id: str = "skill",
    skill_type: SkillType = SkillType.ACTIVE,
    preparation: PreparationMode = PreparationMode.NONE,
    enabled: bool = True,
) -> SkillRuntime:
    runtime = SkillRuntime(
        definition=SkillDefinition(
            skill_id=skill_id,
            name=skill_id,
            activation_rate=1.0,
            target_mode=SkillTargetMode.SINGLE_RANDOM_ENEMY,
            effect_specs=(DamageSkillEffectSpec(DamageType.WEAPON),),
            skill_type=skill_type,
            preparation_mode=preparation,
        ),
        owner_id=owner,
        skill_slot=slot,
        enabled=enabled,
    )
    context.skill_runtimes.register(runtime)
    return runtime


def pref(runtime: SkillRuntime) -> SkillProviderRef:
    assert runtime.skill_slot is not None
    return SkillProviderRef(
        runtime.owner_id,
        runtime.skill_slot,
        runtime.definition.skill_id,
    )


def candidate(
    *,
    owner: str = "a",
    source: str = "b",
    source_skill_id: str = "source-intimidation",
    source_skill_slot: SkillSlot = SkillSlot.LEARNED_1,
    lifetime: StateLifetimeSpec | None = None,
    dependencies: tuple[ProviderDependency, ...] = (),
) -> StateCandidate:
    return StateCandidate(
        state_id=OfficialStateId.INTIMIDATION.value,
        owner_id=owner,
        source_id=source,
        source_skill_id=source_skill_id,
        source_skill_slot=source_skill_slot,
        runtime_params_candidate=EmptyStateRuntimeParams(),
        lifetime_spec=lifetime,
        provider_dependencies=dependencies,
        application_provenance="stage12-690222-runtime-test",
    )


def apply_intimidation(
    systems: BattleSystems,
    context: BattleContext,
    **kwargs,
):
    return systems.state_application_coordinator.apply_candidate(
        context,
        candidate(**kwargs),
    )


def apply_simple_state(
    systems: BattleSystems,
    context: BattleContext,
    state_id: str,
    *,
    owner: str,
    source: str,
    source_skill_id: str,
    source_skill_slot: SkillSlot,
    dependencies: tuple[ProviderDependency, ...] = (),
):
    return systems.state_application_coordinator.apply_candidate(
        context,
        StateCandidate(
            state_id=state_id,
            owner_id=owner,
            source_id=source,
            source_skill_id=source_skill_id,
            source_skill_slot=source_skill_slot,
            runtime_params_candidate=EmptyStateRuntimeParams(),
            provider_dependencies=dependencies,
            application_provenance="stage12-690222-cross-state-test",
        ),
    )


def apply_false_report(
    systems: BattleSystems,
    context: BattleContext,
    *,
    owner: str,
    source: str,
):
    return apply_simple_state(
        systems,
        context,
        OfficialStateId.FALSE_REPORT.value,
        owner=owner,
        source=source,
        source_skill_id="false-report-source",
        source_skill_slot=SkillSlot.LEARNED_2,
    )


def remove_state(
    systems: BattleSystems,
    context: BattleContext,
    instance_id: str,
    operation: RemovalOperation,
):
    return systems.state_removal_coordinator.remove(
        context,
        operation=operation,
        instance_id=instance_id,
    )


def admit(systems: BattleSystems, context: BattleContext, runtime: SkillRuntime):
    return systems.skill_operation_admission_coordinator.evaluate(
        context,
        SkillOperationAdmissionRequest(
            actor_id=runtime.owner_id,
            provider_ref=pref(runtime),
            skill_type=runtime.definition.skill_type,
            preparation_mode=runtime.definition.preparation_mode,
            operation_kind=SkillOperationKind.NEW_ADMISSION,
        ),
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
    before = systems.effectiveness_transition_coordinator.capture(
        context,
        roots,
    )
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


@pytest.mark.parametrize(
    "skill_type,preparation",
    [
        (SkillType.ACTIVE, PreparationMode.NONE),
        (SkillType.ACTIVE, PreparationMode.REQUIRED),
        (SkillType.ASSAULT, PreparationMode.NONE),
        (SkillType.PASSIVE, PreparationMode.NONE),
        (SkillType.COMMAND, PreparationMode.NONE),
        (SkillType.TROOP, PreparationMode.NONE),
    ],
)
def test_supported_eligible_taxonomy_binds_exact_loaded_provider(
    skill_type,
    preparation,
) -> None:
    context = make_context()
    runtime = skill(
        context,
        skill_type=skill_type,
        preparation=preparation,
    )
    systems = BattleSystems()

    result = apply_intimidation(systems, context)

    assert result.status is StateApplicationResultStatus.APPLIED
    assert result.instance is not None
    assert result.instance.bound_provider_ref == pref(runtime)
    assert INTIMIDATION_SUPPORTED_SKILL_TYPES == frozenset(
        {
            SkillType.ACTIVE,
            SkillType.ASSAULT,
            SkillType.PASSIVE,
            SkillType.COMMAND,
            SkillType.TROOP,
        }
    )


@pytest.mark.parametrize("excluded", [SkillType.FORMATION, SkillType.TALENT])
def test_formation_and_talent_never_enter_supported_pool(excluded) -> None:
    rng = CountingRandomSystem()
    context = make_context(rng)
    skill(context, skill_type=excluded)
    systems = BattleSystems()

    result = apply_intimidation(systems, context)

    assert result.status is StateApplicationResultStatus.UNSUPPORTED_BOUNDARY
    assert result.reason_rule_id == INTIMIDATION_EMPTY_POOL_BOUNDARY_RULE_ID
    assert rng.choice_calls == []
    assert not context.states.has(
        owner_id="a",
        state_id=OfficialStateId.INTIMIDATION.value,
    )


def test_normal_attack_is_never_candidate_and_remains_available() -> None:
    context = make_context()
    skill(context, skill_type=SkillType.ACTIVE)
    systems = BattleSystems()
    result = apply_intimidation(systems, context)
    assert result.status is StateApplicationResultStatus.APPLIED

    before = sum(
        event.event_type is EventType.NORMAL_ATTACK
        for event in context.event_bus.history
    )
    systems.normal_attack_system.execute(context, context.get_unit("a"))
    after = sum(
        event.event_type is EventType.NORMAL_ATTACK
        for event in context.event_bus.history
    )
    assert after == before + 1


def test_rd_sf_002_pool_order_and_multi_candidate_exactly_one_choice() -> None:
    rng = CountingRandomSystem(23)
    context = make_context(rng)
    p2 = skill(
        context,
        slot=SkillSlot.LEARNED_2,
        skill_id="skill.z",
        skill_type=SkillType.TROOP,
    )
    p0 = skill(
        context,
        slot=SkillSlot.INHERENT,
        skill_id="skill.m",
        skill_type=SkillType.ACTIVE,
    )
    p1 = skill(
        context,
        slot=SkillSlot.LEARNED_1,
        skill_id="skill.a",
        skill_type=SkillType.COMMAND,
    )
    systems = BattleSystems()

    pool = intimidation_eligible_provider_pool(context, "a")
    assert pool == (pref(p0), pref(p1), pref(p2))

    result = apply_intimidation(systems, context)
    assert result.status is StateApplicationResultStatus.APPLIED
    assert rng.choice_calls == [pool]


def test_single_candidate_create_consumes_zero_binding_rng() -> None:
    rng = CountingRandomSystem(17)
    context = make_context(rng)
    runtime = skill(context)
    systems = BattleSystems()

    result = apply_intimidation(systems, context)

    assert result.instance is not None
    assert result.instance.bound_provider_ref == pref(runtime)
    assert rng.choice_calls == []
    assert rng.random() == RandomSystem(17).random()


def test_single_candidate_refresh_consumes_zero_binding_rng() -> None:
    rng = CountingRandomSystem(19)
    context = make_context(rng)
    runtime = skill(context, skill_id="single-refresh-provider")
    systems = BattleSystems()

    created = apply_intimidation(
        systems,
        context,
        lifetime=StateLifetimeSpec.round_calendar(expires_round=2),
    )
    assert created.instance is not None
    old_generation = created.instance.current_generation_id

    refreshed = apply_intimidation(
        systems,
        context,
        lifetime=StateLifetimeSpec.round_calendar(expires_round=3),
    )

    assert refreshed.status is StateApplicationResultStatus.REFRESHED
    assert refreshed.instance is not None
    assert refreshed.instance.bound_provider_ref == pref(runtime)
    assert refreshed.instance.current_generation_id != old_generation
    assert refreshed.instance.lifetime_spec == StateLifetimeSpec.round_calendar(
        expires_round=3
    )
    assert rng.choice_calls == []


def test_gangyi_rejects_before_binding_rng_and_generation_commit() -> None:
    rng = CountingRandomSystem(31)
    context = make_context(rng)
    skill(context)
    systems = BattleSystems()
    systems.equipment_contribution_registry.register_provider(
        EquipmentProviderRef("a", "刚毅")
    )

    result = apply_intimidation(systems, context)

    assert result.status is StateApplicationResultStatus.REJECTED_ADMISSION
    assert result.admission_decision is not None
    assert result.admission_decision.status is AdmissionStatus.REJECT_SPECIAL_PROTECTION
    assert rng.choice_calls == []
    assert str(context.generation_allocator.allocate()) == "gen_1"
    assert not context.states.has(
        owner_id="a",
        state_id=OfficialStateId.INTIMIDATION.value,
    )


def test_binding_is_full_provider_identity_and_source_is_separate() -> None:
    context = make_context()
    runtime = skill(
        context,
        owner="a",
        slot=SkillSlot.LEARNED_2,
        skill_id="target-provider",
    )
    systems = BattleSystems()

    result = apply_intimidation(
        systems,
        context,
        source="b",
        source_skill_id="source-provider",
        source_skill_slot=SkillSlot.INHERENT,
    )

    assert result.instance is not None
    assert result.instance.bound_provider_ref == SkillProviderRef(
        "a", SkillSlot.LEARNED_2, "target-provider"
    )
    assert result.instance.source_id == "b"
    assert result.instance.source_skill_id == "source-provider"
    assert result.instance.source_skill_slot is SkillSlot.INHERENT
    assert result.instance.bound_provider_ref != SkillProviderRef(
        "b", SkillSlot.INHERENT, "source-provider"
    )
    assert runtime.enabled is True


@pytest.mark.parametrize(
    "skill_type",
    [
        SkillType.ACTIVE,
        SkillType.ASSAULT,
        SkillType.PASSIVE,
        SkillType.COMMAND,
        SkillType.TROOP,
    ],
)
def test_bound_provider_is_suppressed_without_disabling_runtime(skill_type) -> None:
    context = make_context()
    runtime = skill(context, skill_type=skill_type)
    systems = BattleSystems()
    result = apply_intimidation(systems, context)
    assert result.instance is not None

    decision = systems.provider_validity_policy.evaluate_provider(
        context,
        pref(runtime),
    )
    assert decision.status is ProviderValidityStatus.SUPPRESSED
    assert any(
        cause.rule_id == INTIMIDATION_PROVIDER_SUPPRESSION_RULE_ID
        for cause in decision.suppression_causes
    )
    assert runtime.enabled is True
    assert context.skill_runtimes.resolve_provider(pref(runtime)).runtime is runtime


@pytest.mark.parametrize("skill_type", [SkillType.ACTIVE, SkillType.ASSAULT])
def test_active_and_assault_production_admission_reads_provider_validity(
    skill_type,
) -> None:
    context = make_context()
    runtime = skill(context, skill_type=skill_type)
    systems = BattleSystems()
    apply_intimidation(systems, context)

    decision = admit(systems, context, runtime)

    assert decision.status is SkillOperationAdmissionStatus.DENY_PROVIDER_INVALID
    assert decision.permission_decision is None


@pytest.mark.parametrize("skill_type", [SkillType.PASSIVE, SkillType.COMMAND])
def test_passive_and_command_future_opportunity_consumer_gates_and_restores_without_replay(
    skill_type,
) -> None:
    rng = CountingRandomSystem(29)
    context = make_context(rng)
    runtime = skill(
        context,
        skill_type=skill_type,
        skill_id=f"{skill_type.value.lower()}-future-provider",
    )
    systems = BattleSystems()
    intimidation = apply_intimidation(systems, context)
    assert intimidation.instance is not None

    descriptor = RuleIntentExecutionDescriptor(
        intent_kind=RuleIntentKind.RECOVERY_OPPORTUNITY,
        intent_owner_id="a",
        state_owner_id="a",
        target_id="a",
        source_ref=EffectSourceRef(
            stage9_source_type=SourceType.ACTIVE_SKILL,
            source_unit_id="a",
            source_skill_id=runtime.definition.skill_id,
            source_skill_slot=runtime.skill_slot,
        ),
        execution_domain="STATE_RESOLUTION",
    )
    opportunity = RecoveryOpportunity(
        opportunity_kind=RecoveryOpportunityKind.RECUPERATION_ACTION_START,
        execution_descriptor=descriptor,
        probability=1.0,
        source_skill_gate=PersistentSourceSkillGate.query_skill_runtime(),
    )

    suppressed = systems.recovery_opportunity_system.evaluate_and_resolve(
        context,
        opportunity,
    )
    assert suppressed.executed is False
    assert suppressed.reason == "SKILL_TEMPORARILY_DISABLED"
    assert rng.chance_calls == 0

    remove_state(
        systems,
        context,
        intimidation.instance.instance_id,
        RemovalOperation.NATURAL_EXPIRY,
    )
    # Restoration itself creates no retroactive opportunity and consumes no RNG.
    assert rng.chance_calls == 0

    restored_future = systems.recovery_opportunity_system.evaluate_and_resolve(
        context,
        opportunity,
    )
    assert restored_future.reason != "SKILL_TEMPORARILY_DISABLED"
    assert rng.chance_calls == 1


def test_exhaustion_ordering_is_provider_validity_before_skill_permission() -> None:
    context = make_context()
    runtime = skill(context, skill_type=SkillType.ACTIVE)
    systems = BattleSystems()
    apply_intimidation(systems, context)
    exhaustion = apply_simple_state(
        systems,
        context,
        OfficialStateId.SILENCE.value,
        owner="a",
        source="b",
        source_skill_id="exhaustion-source",
        source_skill_slot=SkillSlot.LEARNED_2,
    )
    assert exhaustion.status is StateApplicationResultStatus.APPLIED

    decision = admit(systems, context, runtime)

    assert decision.status is SkillOperationAdmissionStatus.DENY_PROVIDER_INVALID
    assert decision.permission_decision is None


def test_refresh_rerolls_atomically_to_new_provider() -> None:
    rng = SequenceChoiceRandomSystem((0, 1))
    context = make_context(rng)
    first = skill(
        context,
        slot=SkillSlot.INHERENT,
        skill_id="a-provider",
    )
    second = skill(
        context,
        slot=SkillSlot.LEARNED_1,
        skill_id="b-provider",
    )
    systems = BattleSystems()

    created = apply_intimidation(systems, context)
    assert created.instance is not None
    old_id = created.instance.instance_id
    old_generation = created.instance.current_generation_id
    assert created.instance.bound_provider_ref == pref(first)

    refreshed = apply_intimidation(systems, context)

    assert refreshed.status is StateApplicationResultStatus.REFRESHED
    assert refreshed.instance is not None
    assert refreshed.instance.instance_id == old_id
    assert refreshed.instance.current_generation_id != old_generation
    assert refreshed.instance.bound_provider_ref == pref(second)
    assert len(rng.choice_calls) == 2
    assert systems.provider_validity_policy.evaluate_provider(
        context, pref(first)
    ).status is ProviderValidityStatus.VALID
    assert systems.provider_validity_policy.evaluate_provider(
        context, pref(second)
    ).status is ProviderValidityStatus.SUPPRESSED


def test_same_provider_refresh_is_still_new_decision_and_refreshes_lifetime() -> None:
    rng = SequenceChoiceRandomSystem((0, 0))
    context = make_context(rng)
    first = skill(
        context,
        slot=SkillSlot.INHERENT,
        skill_id="a-provider",
    )
    skill(
        context,
        slot=SkillSlot.LEARNED_1,
        skill_id="b-provider",
    )
    systems = BattleSystems()
    created = apply_intimidation(
        systems,
        context,
        lifetime=StateLifetimeSpec.round_calendar(expires_round=2),
    )
    assert created.instance is not None
    old_generation = created.instance.current_generation_id

    refreshed = apply_intimidation(
        systems,
        context,
        lifetime=StateLifetimeSpec.round_calendar(expires_round=3),
    )

    assert refreshed.instance is not None
    assert refreshed.instance.bound_provider_ref == pref(first)
    assert refreshed.instance.current_generation_id != old_generation
    assert refreshed.instance.lifetime_spec == StateLifetimeSpec.round_calendar(
        expires_round=3
    )
    assert len(rng.choice_calls) == 2


def test_refresh_cycle_failure_is_atomic_and_consumes_no_new_binding_rng() -> None:
    rng = SequenceChoiceRandomSystem((0,))
    context = make_context(rng)
    first = skill(
        context,
        slot=SkillSlot.INHERENT,
        skill_id="a-provider",
    )
    skill(
        context,
        slot=SkillSlot.LEARNED_1,
        skill_id="b-provider",
    )
    systems = BattleSystems()
    created = apply_intimidation(
        systems,
        context,
        lifetime=StateLifetimeSpec.round_calendar(expires_round=2),
    )
    assert created.instance is not None
    old = created.instance

    with pytest.raises(DependencyCycleError):
        apply_intimidation(
            systems,
            context,
            lifetime=StateLifetimeSpec.round_calendar(expires_round=3),
            dependencies=(
                ProviderDependency(pref(first), "test-cycle"),
            ),
        )

    current = context.states.get(old.instance_id)
    assert current.current_generation_id == old.current_generation_id
    assert current.bound_provider_ref == old.bound_provider_ref
    assert current.lifetime_spec == old.lifetime_spec
    assert len(rng.choice_calls) == 1
    assert systems.dependency_evaluation_support.prerequisites(
        ProviderNode(pref(first))
    ) == (StateNode(old.instance_id),)


def test_preparation_create_interrupts_only_bound_provider() -> None:
    rng = SequenceChoiceRandomSystem((0,))
    context = make_context(rng)
    first = skill(
        context,
        slot=SkillSlot.INHERENT,
        skill_id="prep-a",
        preparation=PreparationMode.REQUIRED,
    )
    second = skill(
        context,
        slot=SkillSlot.LEARNED_1,
        skill_id="prep-b",
        preparation=PreparationMode.REQUIRED,
    )
    systems = BattleSystems()
    systems.preparation_state_owner.begin_preparing(
        holder_id="a",
        provider_ref=pref(first),
        admitted_operation_id="op-a",
    )
    systems.preparation_state_owner.begin_preparing(
        holder_id="a",
        provider_ref=pref(second),
        admitted_operation_id="op-b",
    )

    result = apply_intimidation(systems, context)
    assert result.instance is not None
    assert result.instance.bound_provider_ref == pref(first)

    remaining = systems.preparation_state_owner.get_preparing("a")
    assert tuple(record.provider_ref for record in remaining) == (pref(second),)


def test_refresh_interrupts_new_preparing_provider_not_old_provider() -> None:
    rng = SequenceChoiceRandomSystem((0, 1))
    context = make_context(rng)
    first = skill(
        context,
        slot=SkillSlot.INHERENT,
        skill_id="prep-a",
        preparation=PreparationMode.REQUIRED,
    )
    second = skill(
        context,
        slot=SkillSlot.LEARNED_1,
        skill_id="prep-b",
        preparation=PreparationMode.REQUIRED,
    )
    systems = BattleSystems()
    apply_intimidation(systems, context)
    systems.preparation_state_owner.begin_preparing(
        holder_id="a",
        provider_ref=pref(second),
        admitted_operation_id="op-b",
    )

    refreshed = apply_intimidation(systems, context)

    assert refreshed.instance is not None
    assert refreshed.instance.bound_provider_ref == pref(second)
    assert not systems.preparation_state_owner.is_preparing("a")
    assert systems.provider_validity_policy.evaluate_provider(
        context, pref(first)
    ).status is ProviderValidityStatus.VALID


def test_source_dependency_suppression_and_resume_preserve_binding_generation_lifetime_and_rng() -> None:
    rng = CountingRandomSystem(47)
    context = make_context(rng)
    target = skill(context, owner="a", skill_id="target-active")
    source = skill(
        context,
        owner="b",
        skill_id="source-passive",
        skill_type=SkillType.PASSIVE,
    )
    systems = BattleSystems()

    created = apply_intimidation(
        systems,
        context,
        source="b",
        source_skill_id=source.definition.skill_id,
        source_skill_slot=source.skill_slot,
        lifetime=StateLifetimeSpec.round_calendar(expires_round=3),
        dependencies=(
            ProviderDependency(pref(source), "observed-source-provider"),
        ),
    )
    assert created.instance is not None
    snapshot = (
        created.instance.bound_provider_ref,
        created.instance.current_generation_id,
        created.instance.lifetime_spec,
    )
    assert systems.provider_validity_policy.evaluate_provider(
        context, pref(target)
    ).status is ProviderValidityStatus.SUPPRESSED

    false_report = apply_false_report(
        systems,
        context,
        owner="b",
        source="a",
    )
    assert false_report.instance is not None
    resident = context.states.get(created.instance.instance_id)
    assert systems.state_effectiveness_policy.evaluate_state(
        context, resident
    ).status is StateEffectivenessStatus.SUPPRESSED
    assert systems.provider_validity_policy.evaluate_provider(
        context, pref(target)
    ).status is ProviderValidityStatus.VALID
    choices_before_resume = len(rng.choice_calls)

    removed = remove_state(
        systems,
        context,
        false_report.instance.instance_id,
        RemovalOperation.ORDINARY_CLEANSE,
    )
    assert removed.status is StateRemovalResultStatus.REMOVED

    resumed = context.states.get(created.instance.instance_id)
    assert (
        resumed.bound_provider_ref,
        resumed.current_generation_id,
        resumed.lifetime_spec,
    ) == snapshot
    assert systems.state_effectiveness_policy.evaluate_state(
        context, resumed
    ).status is StateEffectivenessStatus.EFFECTIVE
    assert systems.provider_validity_policy.evaluate_provider(
        context, pref(target)
    ).status is ProviderValidityStatus.SUPPRESSED
    assert len(rng.choice_calls) == choices_before_resume == 0


def test_resume_interrupts_same_preparing_provider_with_zero_binding_rng() -> None:
    rng = CountingRandomSystem(53)
    context = make_context(rng)
    target = skill(
        context,
        owner="a",
        skill_id="target-prep",
        preparation=PreparationMode.REQUIRED,
    )
    source = skill(
        context,
        owner="b",
        skill_id="source-passive",
        skill_type=SkillType.PASSIVE,
    )
    systems = BattleSystems()
    false_report = apply_false_report(
        systems, context, owner="b", source="a"
    )
    assert false_report.instance is not None

    created = apply_intimidation(
        systems,
        context,
        source="b",
        source_skill_id=source.definition.skill_id,
        source_skill_slot=source.skill_slot,
        dependencies=(
            ProviderDependency(pref(source), "observed-source-provider"),
        ),
    )
    assert created.instance is not None
    assert systems.state_effectiveness_policy.evaluate_state(
        context, created.instance
    ).status is StateEffectivenessStatus.SUPPRESSED
    systems.preparation_state_owner.begin_preparing(
        holder_id="a",
        provider_ref=pref(target),
        admitted_operation_id="resume-op",
    )

    remove_state(
        systems,
        context,
        false_report.instance.instance_id,
        RemovalOperation.ORDINARY_CLEANSE,
    )

    assert not systems.preparation_state_owner.is_preparing("a")
    assert context.states.get(
        created.instance.instance_id
    ).bound_provider_ref == pref(target)
    assert rng.choice_calls == []


def test_initially_suppressed_application_stores_binding_without_active_consequence() -> None:
    context = make_context()
    target = skill(
        context,
        owner="a",
        skill_id="target-prep",
        preparation=PreparationMode.REQUIRED,
    )
    source = skill(
        context,
        owner="b",
        skill_id="source-passive",
        skill_type=SkillType.PASSIVE,
    )
    systems = BattleSystems()
    false_report = apply_false_report(
        systems, context, owner="b", source="a"
    )
    assert false_report.instance is not None
    systems.preparation_state_owner.begin_preparing(
        holder_id="a",
        provider_ref=pref(target),
        admitted_operation_id="initial-suppressed-op",
    )

    result = apply_intimidation(
        systems,
        context,
        source="b",
        source_skill_id=source.definition.skill_id,
        source_skill_slot=source.skill_slot,
        dependencies=(
            ProviderDependency(pref(source), "observed-source-provider"),
        ),
    )

    assert result.instance is not None
    assert result.instance.bound_provider_ref == pref(target)
    assert systems.state_effectiveness_policy.evaluate_state(
        context, result.instance
    ).status is StateEffectivenessStatus.SUPPRESSED
    assert systems.provider_validity_policy.evaluate_provider(
        context, pref(target)
    ).status is ProviderValidityStatus.VALID
    assert systems.preparation_state_owner.is_preparing("a")


def test_expires_while_source_suppressed_does_not_resume_or_resuppress() -> None:
    rng = CountingRandomSystem(61)
    context = make_context(rng)
    target = skill(context, owner="a", skill_id="target-active")
    source = skill(
        context,
        owner="b",
        skill_id="source-passive",
        skill_type=SkillType.PASSIVE,
    )
    systems = BattleSystems()
    created = apply_intimidation(
        systems,
        context,
        source="b",
        source_skill_id=source.definition.skill_id,
        source_skill_slot=source.skill_slot,
        lifetime=StateLifetimeSpec.round_calendar(expires_round=2),
        dependencies=(
            ProviderDependency(pref(source), "observed-source-provider"),
        ),
    )
    assert created.instance is not None
    false_report = apply_false_report(
        systems, context, owner="b", source="a"
    )
    assert false_report.instance is not None

    context.current_round = 2
    context.current_phase = BattlePhase.ROUND_END.value
    removed = settle_due(
        systems,
        context,
        round_no=2,
        phase=BattlePhase.ROUND_END.value,
    )
    assert [item.instance_id for item in removed] == [created.instance.instance_id]
    assert systems.provider_validity_policy.evaluate_provider(
        context, pref(target)
    ).status is ProviderValidityStatus.VALID
    choices_before = len(rng.choice_calls)

    remove_state(
        systems,
        context,
        false_report.instance.instance_id,
        RemovalOperation.ORDINARY_CLEANSE,
    )

    assert not context.states.has_instance(created.instance.instance_id)
    assert systems.provider_validity_policy.evaluate_provider(
        context, pref(target)
    ).status is ProviderValidityStatus.VALID
    assert len(rng.choice_calls) == choices_before == 0


def test_ordinary_insight_does_not_reject_intimidation() -> None:
    context = make_context()
    skill(context)
    systems = BattleSystems()
    insight = apply_simple_state(
        systems,
        context,
        OfficialStateId.INSIGHT.value,
        owner="a",
        source="b",
        source_skill_id="insight-source",
        source_skill_slot=SkillSlot.LEARNED_2,
    )
    assert insight.status is StateApplicationResultStatus.APPLIED

    result = apply_intimidation(systems, context)

    assert result.status is StateApplicationResultStatus.APPLIED
    assert result.instance is not None


@pytest.mark.parametrize(
    "dependent_state_id",
    [OfficialStateId.INSIGHT.value, OfficialStateId.PROVOKE.value],
)
def test_selected_provider_dependency_cascade_is_explicit_and_resumes(
    dependent_state_id,
) -> None:
    context = make_context()
    runtime = skill(
        context,
        skill_type=SkillType.PASSIVE,
        skill_id="dependent-provider",
    )
    systems = BattleSystems()
    dependent = apply_simple_state(
        systems,
        context,
        dependent_state_id,
        owner="a",
        source="b",
        source_skill_id=f"{dependent_state_id}-source",
        source_skill_slot=SkillSlot.LEARNED_2,
        dependencies=(
            ProviderDependency(pref(runtime), "explicit-provider-dependency"),
        ),
    )
    assert dependent.instance is not None
    assert systems.state_effectiveness_policy.evaluate_state(
        context, dependent.instance
    ).effective

    intimidation = apply_intimidation(systems, context)
    assert intimidation.instance is not None
    assert systems.state_effectiveness_policy.evaluate_state(
        context, dependent.instance
    ).status is StateEffectivenessStatus.SUPPRESSED

    remove_state(
        systems,
        context,
        intimidation.instance.instance_id,
        RemovalOperation.NATURAL_EXPIRY,
    )
    assert systems.state_effectiveness_policy.evaluate_state(
        context, context.states.get(dependent.instance.instance_id)
    ).status is StateEffectivenessStatus.EFFECTIVE


def test_attribution_without_provider_dependency_does_not_gate_intimidation() -> None:
    context = make_context()
    target = skill(context, owner="a", skill_id="target-active")
    source = skill(
        context,
        owner="b",
        skill_id="attributed-source",
        skill_type=SkillType.PASSIVE,
    )
    systems = BattleSystems()
    intimidation = apply_intimidation(
        systems,
        context,
        source="b",
        source_skill_id=source.definition.skill_id,
        source_skill_slot=source.skill_slot,
        dependencies=(),
    )
    assert intimidation.instance is not None

    false_report = apply_false_report(
        systems, context, owner="b", source="a"
    )
    assert false_report.instance is not None

    assert systems.state_effectiveness_policy.evaluate_state(
        context, intimidation.instance
    ).status is StateEffectivenessStatus.EFFECTIVE
    assert systems.provider_validity_policy.evaluate_provider(
        context, pref(target)
    ).status is ProviderValidityStatus.SUPPRESSED


def test_false_report_and_intimidation_suppression_causes_compose() -> None:
    context = make_context()
    runtime = skill(
        context,
        skill_type=SkillType.PASSIVE,
        skill_id="shared-passive",
    )
    systems = BattleSystems()
    intimidation = apply_intimidation(systems, context)
    false_report = apply_false_report(
        systems, context, owner="a", source="b"
    )
    assert intimidation.instance is not None
    assert false_report.instance is not None

    both = systems.provider_validity_policy.evaluate_provider(
        context, pref(runtime)
    )
    assert both.status is ProviderValidityStatus.SUPPRESSED
    assert len(both.suppression_causes) >= 2

    remove_state(
        systems,
        context,
        intimidation.instance.instance_id,
        RemovalOperation.NATURAL_EXPIRY,
    )
    assert systems.provider_validity_policy.evaluate_provider(
        context, pref(runtime)
    ).status is ProviderValidityStatus.SUPPRESSED

    remove_state(
        systems,
        context,
        false_report.instance.instance_id,
        RemovalOperation.ORDINARY_CLEANSE,
    )
    assert systems.provider_validity_policy.evaluate_provider(
        context, pref(runtime)
    ).status is ProviderValidityStatus.VALID


def test_removal_boundaries_generic_cleanse_rejects_specialized_is_unsupported() -> None:
    context = make_context()
    skill(context)
    systems = BattleSystems()
    result = apply_intimidation(systems, context)
    assert result.instance is not None

    ordinary = remove_state(
        systems,
        context,
        result.instance.instance_id,
        RemovalOperation.ORDINARY_CLEANSE,
    )
    assert ordinary.status is StateRemovalResultStatus.REJECTED
    assert context.states.has_instance(result.instance.instance_id)

    specialized = remove_state(
        systems,
        context,
        result.instance.instance_id,
        RemovalOperation.SPECIALIZED_CLEANSE,
    )
    assert specialized.status is StateRemovalResultStatus.UNSUPPORTED_BOUNDARY
    assert context.states.has_instance(result.instance.instance_id)


def test_refresh_is_one_state_one_binding_not_stack_count() -> None:
    rng = SequenceChoiceRandomSystem((0, 1))
    context = make_context(rng)
    skill(context, slot=SkillSlot.INHERENT, skill_id="a")
    skill(context, slot=SkillSlot.LEARNED_1, skill_id="b")
    systems = BattleSystems()

    first = apply_intimidation(systems, context)
    second = apply_intimidation(systems, context)

    assert first.instance is not None and second.instance is not None
    residents = context.states.find(
        owner_id="a",
        state_id=OfficialStateId.INTIMIDATION.value,
    )
    assert len(residents) == 1
    assert residents[0].instance_id == first.instance.instance_id
    assert residents[0].bound_provider_ref == second.instance.bound_provider_ref
    assert not hasattr(residents[0], "stack_count")


def test_multisource_application_remains_unsupported_and_consumes_zero_new_rng() -> None:
    rng = CountingRandomSystem(71)
    context = make_context(rng)
    skill(context, slot=SkillSlot.INHERENT, skill_id="a")
    skill(context, slot=SkillSlot.LEARNED_1, skill_id="b")
    systems = BattleSystems()
    first = apply_intimidation(systems, context)
    assert first.instance is not None
    choices_before = len(rng.choice_calls)

    second = apply_intimidation(
        systems,
        context,
        source_skill_id="different-source",
        source_skill_slot=SkillSlot.LEARNED_2,
    )

    assert second.status is StateApplicationResultStatus.UNSUPPORTED_BOUNDARY
    assert len(rng.choice_calls) == choices_before


def test_binding_replay_same_seed_pool_and_downstream_rng_state() -> None:
    def run(seed: int):
        rng = CountingRandomSystem(seed)
        context = make_context(rng)
        skill(context, slot=SkillSlot.INHERENT, skill_id="a")
        skill(context, slot=SkillSlot.LEARNED_1, skill_id="b")
        skill(context, slot=SkillSlot.LEARNED_2, skill_id="c")
        systems = BattleSystems()
        result = apply_intimidation(systems, context)
        assert result.instance is not None
        return (
            result.instance.bound_provider_ref,
            tuple(rng.choice_calls),
            rng.random(),
        )

    assert run(83) == run(83)


def test_provider_query_and_binding_add_no_new_public_event_types() -> None:
    context = make_context()
    runtime = skill(context)
    systems = BattleSystems()
    result = apply_intimidation(systems, context)
    assert result.instance is not None

    before = tuple(context.event_bus.history)
    systems.provider_validity_policy.evaluate_provider(context, pref(runtime))
    assert tuple(context.event_bus.history) == before
    assert not hasattr(EventType, "INTIMIDATION_BOUND_PROVIDER")
    assert not hasattr(EventType, "PROVIDER_SUPPRESSED")
    assert not hasattr(EventType, "PROVIDER_RESUMED")


def test_integration_has_no_random_module_or_public_event_emission() -> None:
    source = inspect.getsource(intimidation_module)
    assert "import random" not in source
    assert "EventType" not in source
    assert ".publish(" not in source
    assert "enabled = False" not in source
