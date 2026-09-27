from __future__ import annotations

import ast
from dataclasses import fields
from pathlib import Path

import pytest

from sgs_v2.battle_core import (
    BattleContext,
    BattleSystems,
    DamageSkillEffectSpec,
    DamageType,
    EventBus,
    LineupPosition,
    LocalRuleCauseRef,
    NoopPreparationInterruptionPort,
    PreparationInterruptionRequest,
    PreparationInterruptionResult,
    PreparationInterruptionScope,
    PreparationInterruptionStatus,
    PreparationInterruptionTransitionAdapter,
    PreparationMode,
    RandomSystem,
    SkillDefinition,
    SkillOperationAdmissionRequest,
    SkillOperationAdmissionStatus,
    SkillOperationKind,
    SkillPermissionDecision,
    SkillPermissionRequest,
    SkillPermissionStatus,
    SkillProviderRef,
    SkillResolutionStatus,
    SkillRuntime,
    SkillSlot,
    SkillTargetMode,
    SkillType,
    SuppressionCause,
    TargetCardinality,
    TargetEligibilityContext,
    TargetOperationDomain,
    TargetOperationProducer,
    TargetPolicyContribution,
    TargetPurpose,
    TargetQueryMode,
    TargetRelation,
    TargetSelectionProvenance,
    TargetSelectionResult,
    TargetSelectorKind,
    UnitRuntime,
)


class CountingRandomSystem(RandomSystem):
    def __init__(self, seed: int = 1, *, chance_result: bool | None = None) -> None:
        super().__init__(seed)
        self.chance_result = chance_result
        self.chance_calls = 0
        self.sample_calls = 0

    def chance(self, probability: float) -> bool:
        self.chance_calls += 1
        if self.chance_result is not None:
            return self.chance_result
        return super().chance(probability)

    def sample(self, values, k):  # type: ignore[no-untyped-def]
        self.sample_calls += 1
        return super().sample(values, k)


class RecordingTargetSystem:
    pass


class FakePreparationInterruptionPort:
    def __init__(self, preparing: tuple[SkillProviderRef, ...] = ()) -> None:
        self.preparing = list(preparing)
        self.requests: list[PreparationInterruptionRequest] = []

    def interrupt(self, context, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        if request.scope is PreparationInterruptionScope.HOLDER_ACTIVE:
            matched = [
                item for item in self.preparing
                if item.owner_id == request.holder_id
            ]
            if not matched:
                return PreparationInterruptionResult(
                    request,
                    PreparationInterruptionStatus.NOT_PREPARING,
                )
        else:
            assert request.provider_ref is not None
            if request.provider_ref not in self.preparing:
                same_holder = any(
                    item.owner_id == request.holder_id
                    for item in self.preparing
                )
                return PreparationInterruptionResult(
                    request,
                    (
                        PreparationInterruptionStatus.PROVIDER_NOT_MATCHED
                        if same_holder
                        else PreparationInterruptionStatus.NOT_PREPARING
                    ),
                )
            matched = [request.provider_ref]

        for item in matched:
            if item in self.preparing:
                self.preparing.remove(item)
        return PreparationInterruptionResult(
            request,
            PreparationInterruptionStatus.INTERRUPTED,
            tuple(matched),
        )


def make_context(
    random_system: RandomSystem | None = None,
    *,
    living_enemy: bool = True,
    second_enemy: bool = True,
) -> BattleContext:
    units = {
        "a": UnitRuntime(
            "a", "A", "A", 1000, 1000, 300, 100, 100,
            lineup_position=LineupPosition.COMMANDER,
        ),
        "b": UnitRuntime(
            "b", "B", "B", 1000, 1000 if living_enemy else 0, 100, 100, 90,
            lineup_position=LineupPosition.COMMANDER,
        ),
    }
    if second_enemy:
        units["c"] = UnitRuntime(
            "c", "C", "B", 1000, 1000 if living_enemy else 0, 100, 100, 80,
            lineup_position=LineupPosition.DEPUTY_1,
        )
    return BattleContext(
        battle_id="round3",
        units=units,
        event_bus=EventBus(),
        random=random_system or RandomSystem(1),
    )


def definition(
    *,
    rate: float = 1.0,
    skill_id: str = "synthetic.round3",
    skill_type: SkillType = SkillType.ACTIVE,
    preparation_mode: PreparationMode = PreparationMode.NONE,
) -> SkillDefinition:
    return SkillDefinition(
        skill_id=skill_id,
        name="Synthetic Round3",
        activation_rate=rate,
        target_mode=SkillTargetMode.SINGLE_RANDOM_ENEMY,
        effect_specs=(DamageSkillEffectSpec(DamageType.WEAPON),),
        skill_type=skill_type,
        preparation_mode=preparation_mode,
    )


def runtime(
    *,
    rate: float = 1.0,
    enabled: bool = True,
    skill_id: str = "synthetic.round3",
    slot: SkillSlot = SkillSlot.INHERENT,
) -> SkillRuntime:
    return SkillRuntime(
        definition(rate=rate, skill_id=skill_id),
        owner_id="a",
        skill_slot=slot,
        enabled=enabled,
    )


def provider_ref(
    skill_id: str = "synthetic.round3",
    slot: SkillSlot = SkillSlot.INHERENT,
) -> SkillProviderRef:
    return SkillProviderRef("a", slot, skill_id)


def admission_request(ref: SkillProviderRef | None = None) -> SkillOperationAdmissionRequest:
    return SkillOperationAdmissionRequest(
        actor_id="a",
        provider_ref=ref or provider_ref(),
        skill_type=SkillType.ACTIVE,
        preparation_mode=PreparationMode.NONE,
        operation_kind=SkillOperationKind.NEW_ADMISSION,
    )


def permission_request(ref: SkillProviderRef | None = None) -> SkillPermissionRequest:
    return SkillPermissionRequest(
        actor_id="a",
        provider_ref=ref or provider_ref(),
        skill_type=SkillType.ACTIVE,
        preparation_mode=PreparationMode.NONE,
        operation_kind=SkillOperationKind.NEW_ADMISSION,
    )


def deny_permission(_context, request):  # type: ignore[no-untyped-def]
    return SkillPermissionDecision(
        request=request,
        status=SkillPermissionStatus.DENY_STATE_PERMISSION,
        blocker_keys=("synthetic-deny",),
    )


def suppress_provider(_context, _provider, _session):  # type: ignore[no-untyped-def]
    return (
        SuppressionCause(
            "synthetic-suppression",
            LocalRuleCauseRef("synthetic-cause"),
        ),
    )


def make_operation(context: BattleContext, *, cardinality=TargetCardinality.SINGLE, count=None):
    ref = provider_ref()
    return TargetOperationProducer.new_query(
        context,
        actor_id="a",
        producer_ref=ref,
        admitted_operation_key="skill:a:0:synthetic.round3",
        relation=TargetRelation.ENEMY,
        cardinality=cardinality,
        selector_kind=TargetSelectorKind.RANDOM,
        eligibility_context=TargetEligibilityContext(
            TargetOperationDomain.SKILL,
            TargetPurpose.HOSTILE,
        ),
        requested_count=count,
    )


def test_legacy_skill_definition_maps_active_none() -> None:
    item = SkillDefinition(
        "legacy",
        "Legacy",
        1.0,
        SkillTargetMode.SINGLE_RANDOM_ENEMY,
        (DamageSkillEffectSpec(DamageType.WEAPON),),
    )
    assert item.skill_type is SkillType.ACTIVE
    assert item.preparation_mode is PreparationMode.NONE


@pytest.mark.parametrize("kind", list(SkillType))
def test_skill_type_schema_supports_frozen_taxonomy(kind: SkillType) -> None:
    item = definition(skill_type=kind)
    assert item.skill_type is kind


def test_permission_allow() -> None:
    systems = BattleSystems()
    decision = systems.skill_permission_policy.evaluate(
        make_context(),
        permission_request(),
    )
    assert decision.status is SkillPermissionStatus.ALLOW
    assert decision.allowed


def test_permission_synthetic_deny() -> None:
    systems = BattleSystems()
    systems.skill_permission_policy.register_rule_adapter(deny_permission)
    decision = systems.skill_permission_policy.evaluate(
        make_context(),
        permission_request(),
    )
    assert decision.status is SkillPermissionStatus.DENY_STATE_PERMISSION
    assert decision.blocker_keys == ("synthetic-deny",)


def test_permission_continuation_is_not_readmitted() -> None:
    systems = BattleSystems()
    systems.skill_permission_policy.register_rule_adapter(deny_permission)
    request = permission_request()
    request = SkillPermissionRequest(
        actor_id=request.actor_id,
        provider_ref=request.provider_ref,
        skill_type=request.skill_type,
        preparation_mode=request.preparation_mode,
        operation_kind=SkillOperationKind.CONTINUATION,
    )
    decision = systems.skill_permission_policy.evaluate(make_context(), request)
    assert decision.status is SkillPermissionStatus.CONTINUATION_NOT_REEVALUATED
    assert decision.allowed


def test_permission_query_zero_rng() -> None:
    rng = RandomSystem(77)
    context = make_context(rng)
    systems = BattleSystems()
    systems.skill_permission_policy.evaluate(context, permission_request())
    observed = context.random.random()
    expected = RandomSystem(77).random()
    assert observed == expected


def test_permission_query_zero_event() -> None:
    context = make_context()
    systems = BattleSystems()
    before = context.event_bus.history
    systems.skill_permission_policy.evaluate(context, permission_request())
    assert context.event_bus.history == before


def test_permission_does_not_mutate_runtime_enabled() -> None:
    context = make_context()
    item = runtime(enabled=True)
    context.skill_runtimes.register(item)
    systems = BattleSystems()
    systems.skill_permission_policy.register_rule_adapter(deny_permission)
    systems.skill_permission_policy.evaluate(context, permission_request())
    assert item.enabled is True


def test_provider_valid_permission_allow() -> None:
    context = make_context()
    item = runtime()
    context.skill_runtimes.register(item)
    systems = BattleSystems()
    decision = systems.skill_operation_admission_coordinator.evaluate(
        context,
        admission_request(),
    )
    assert decision.status is SkillOperationAdmissionStatus.ALLOW
    assert decision.admitted


def test_provider_missing_denies_before_activation_rng() -> None:
    rng = CountingRandomSystem(chance_result=True)
    context = make_context(rng)
    systems = BattleSystems()
    result = systems.skill_resolver.resolve(context, runtime(rate=0.5))
    assert result.status is SkillResolutionStatus.DISABLED
    assert rng.chance_calls == 0
    assert rng.sample_calls == 0


def test_provider_identity_mismatch_denies_before_activation_rng() -> None:
    rng = CountingRandomSystem(chance_result=True)
    context = make_context(rng)
    registered = runtime(skill_id="registered")
    context.skill_runtimes.register(registered)
    systems = BattleSystems()
    attempted = runtime(rate=0.5, skill_id="attempted")
    result = systems.skill_resolver.resolve(context, attempted)
    assert result.status is SkillResolutionStatus.DISABLED
    assert rng.chance_calls == 0
    assert rng.sample_calls == 0


def test_provider_baseline_disabled_denies_before_activation_rng() -> None:
    rng = CountingRandomSystem(chance_result=True)
    context = make_context(rng)
    item = runtime(rate=0.5, enabled=False)
    context.skill_runtimes.register(item)
    systems = BattleSystems()
    result = systems.skill_resolver.resolve(context, item)
    assert result.status is SkillResolutionStatus.DISABLED
    assert rng.chance_calls == 0
    assert rng.sample_calls == 0


def test_provider_suppressed_denies_before_activation_rng() -> None:
    rng = CountingRandomSystem(chance_result=True)
    context = make_context(rng)
    item = runtime(rate=0.5)
    context.skill_runtimes.register(item)
    systems = BattleSystems()
    systems.provider_validity_policy.register_rule_adapter(suppress_provider)
    result = systems.skill_resolver.resolve(context, item)
    assert result.status is SkillResolutionStatus.DISABLED
    assert rng.chance_calls == 0
    assert rng.sample_calls == 0


def test_permission_denied_before_activation_rng() -> None:
    rng = CountingRandomSystem(chance_result=True)
    context = make_context(rng)
    item = runtime(rate=0.5)
    context.skill_runtimes.register(item)
    systems = BattleSystems()
    systems.skill_permission_policy.register_rule_adapter(deny_permission)
    result = systems.skill_resolver.resolve(context, item)
    assert result.status is SkillResolutionStatus.DISABLED
    assert rng.chance_calls == 0
    assert rng.sample_calls == 0


def test_denied_skill_creates_no_target_operation() -> None:
    context = make_context()
    item = runtime()
    context.skill_runtimes.register(item)
    systems = BattleSystems()
    systems.skill_permission_policy.register_rule_adapter(deny_permission)
    systems.skill_resolver.resolve(context, item)
    assert str(context.id_allocator.allocate_target_operation_id()) == "top_1"


def test_failed_activation_consumes_no_target_rng_and_no_target_operation() -> None:
    rng = CountingRandomSystem(chance_result=False)
    context = make_context(rng)
    item = runtime(rate=0.5)
    context.skill_runtimes.register(item)
    systems = BattleSystems()
    result = systems.skill_resolver.resolve(context, item)
    assert result.status is SkillResolutionStatus.ACTIVATION_FAILED
    assert rng.chance_calls == 1
    assert rng.sample_calls == 0
    assert str(context.id_allocator.allocate_target_operation_id()) == "top_1"


def test_no_valid_target_preserves_legacy_pre_activation_short_circuit() -> None:
    rng = CountingRandomSystem(chance_result=True)
    context = make_context(rng, living_enemy=False)
    item = runtime(rate=0.5)
    context.skill_runtimes.register(item)
    systems = BattleSystems()
    result = systems.skill_resolver.resolve(context, item)
    assert result.status is SkillResolutionStatus.NO_VALID_TARGET
    assert rng.chance_calls == 0
    assert str(context.id_allocator.allocate_target_operation_id()) == "top_1"


def test_existing_single_random_enemy_behavior_preserved() -> None:
    legacy_context = make_context(RandomSystem(13))
    production_context = make_context(RandomSystem(13))
    item = runtime()
    production_context.skill_runtimes.register(item)
    legacy = BattleSystems().skill_resolver
    # Slotless direct construction remains the compatibility seam.
    slotless = SkillRuntime(item.definition, "a", skill_slot=None)
    legacy_result = legacy.resolve(legacy_context, slotless)
    production_result = BattleSystems().skill_resolver.resolve(production_context, item)
    assert legacy_result.status is production_result.status
    assert legacy_result.target_ids == production_result.target_ids
    assert len(legacy_result.effects) == len(production_result.effects) == 1
    assert legacy_result.effects[0].target_id == production_result.effects[0].target_id
    assert legacy_result.effects[0].damage_type == production_result.effects[0].damage_type
    assert legacy_result.effects[0].coefficient == production_result.effects[0].coefficient


def test_existing_skill_result_surface_preserved() -> None:
    names = [field.name for field in fields(__import__(
        "sgs_v2.battle_core.skill_resolver",
        fromlist=["SkillResolutionResult"],
    ).SkillResolutionResult)]
    assert names == ["skill_id", "owner_id", "status", "target_ids", "effects"]


def test_holder_active_interruption_request() -> None:
    first = provider_ref()
    second = SkillProviderRef("a", SkillSlot.LEARNED_1, "synthetic.second")
    fake = FakePreparationInterruptionPort((first, second))
    request = PreparationInterruptionRequest(
        PreparationInterruptionScope.HOLDER_ACTIVE,
        "a",
        "synthetic-transition",
    )
    result = fake.interrupt(None, request)
    assert result.status is PreparationInterruptionStatus.INTERRUPTED
    assert result.interrupted_provider_refs == (first, second)
    assert fake.preparing == []


def test_provider_specific_interruption_request() -> None:
    first = provider_ref()
    second = SkillProviderRef("a", SkillSlot.LEARNED_1, "synthetic.second")
    fake = FakePreparationInterruptionPort((first, second))
    request = PreparationInterruptionRequest(
        PreparationInterruptionScope.PROVIDER,
        "a",
        "synthetic-transition",
        first,
    )
    result = fake.interrupt(None, request)
    assert result.interrupted_provider_refs == (first,)
    assert fake.preparing == [second]


def test_not_preparing_result() -> None:
    fake = FakePreparationInterruptionPort()
    request = PreparationInterruptionRequest(
        PreparationInterruptionScope.HOLDER_ACTIVE,
        "a",
        "synthetic-transition",
    )
    assert fake.interrupt(None, request).status is PreparationInterruptionStatus.NOT_PREPARING


def test_provider_not_matched_result() -> None:
    existing = provider_ref()
    absent = SkillProviderRef("a", SkillSlot.LEARNED_1, "synthetic.absent")
    fake = FakePreparationInterruptionPort((existing,))
    request = PreparationInterruptionRequest(
        PreparationInterruptionScope.PROVIDER,
        "a",
        "synthetic-transition",
        absent,
    )
    assert fake.interrupt(None, request).status is PreparationInterruptionStatus.PROVIDER_NOT_MATCHED


def test_no_duplicate_interruption() -> None:
    existing = provider_ref()
    fake = FakePreparationInterruptionPort((existing,))
    request = PreparationInterruptionRequest(
        PreparationInterruptionScope.PROVIDER,
        "a",
        "synthetic-transition",
        existing,
    )
    assert fake.interrupt(None, request).status is PreparationInterruptionStatus.INTERRUPTED
    assert fake.interrupt(None, request).status is PreparationInterruptionStatus.NOT_PREPARING


def test_noop_port_cannot_claim_concrete_interruption() -> None:
    request = PreparationInterruptionRequest(
        PreparationInterruptionScope.HOLDER_ACTIVE,
        "a",
        "synthetic-transition",
    )
    result = NoopPreparationInterruptionPort().interrupt(None, request)
    assert result.status is PreparationInterruptionStatus.NOT_PREPARING
    assert result.interrupted_provider_refs == ()


def test_transition_adapter_binds_generic_state_port() -> None:
    systems = BattleSystems()
    before = len(systems.effectiveness_transition_coordinator._state_ports)
    adapter = PreparationInterruptionTransitionAdapter(
        systems.preparation_interruption_port,
        state_request_factory=lambda _context, _transition: None,
    )
    adapter.bind(systems.effectiveness_transition_coordinator)
    assert len(systems.effectiveness_transition_coordinator._state_ports) == before + 1


def test_new_query_allocates_new_operation_id() -> None:
    context = make_context()
    first = make_operation(context)
    second = make_operation(context)
    assert str(first.operation_id) == "top_1"
    assert str(second.operation_id) == "top_2"
    assert first.operation_id != second.operation_id


@pytest.mark.parametrize(
    ("mode", "provenance"),
    [
        (TargetQueryMode.INHERIT_RESOLVED, TargetSelectionProvenance.INHERITED),
        (TargetQueryMode.DERIVE_FROM_RESOLVED, TargetSelectionProvenance.DERIVED),
        (TargetQueryMode.LOCK_RESOLVED, TargetSelectionProvenance.LOCKED),
    ],
)
def test_continuation_modes_reuse_operation_identity(mode, provenance) -> None:  # type: ignore[no-untyped-def]
    context = make_context()
    operation = make_operation(context)
    selected = TargetSelectionResult(
        operation.operation_id,
        ("b",),
        TargetSelectionProvenance.FRESH_SELECTED,
    )
    continued = TargetOperationProducer.continue_from(selected, mode)
    assert continued.operation_id == selected.operation_id
    assert continued.provenance is provenance
    assert str(context.id_allocator.allocate_target_operation_id()) == "top_2"


def test_derived_target_can_change_targets_without_requery() -> None:
    context = make_context()
    operation = make_operation(context)
    selected = TargetSelectionResult(
        operation.operation_id,
        ("b",),
        TargetSelectionProvenance.FRESH_SELECTED,
    )
    derived = TargetOperationProducer.continue_from(
        selected,
        TargetQueryMode.DERIVE_FROM_RESOLVED,
        target_ids=("c",),
    )
    assert derived.operation_id == operation.operation_id
    assert derived.target_ids == ("c",)
    assert str(context.id_allocator.allocate_target_operation_id()) == "top_2"


def test_new_query_cannot_be_faked_as_continuation() -> None:
    context = make_context()
    operation = make_operation(context)
    selected = TargetSelectionResult(
        operation.operation_id,
        ("b",),
        TargetSelectionProvenance.FRESH_SELECTED,
    )
    with pytest.raises(ValueError, match="fresh TargetOperation"):
        TargetOperationProducer.continue_from(selected, TargetQueryMode.NEW_QUERY)


def test_operation_id_value_equality() -> None:
    context = make_context()
    operation = make_operation(context)
    other = type(operation.operation_id)(str(operation.operation_id))
    assert operation.operation_id == other
    assert operation.operation_id is not other


def test_operation_id_not_used_as_gameplay_priority() -> None:
    context = make_context()
    first = make_operation(context).operation_id
    second = make_operation(context).operation_id
    with pytest.raises(TypeError, match="does not support"):
        _ = first < second


def test_no_constraints_preserves_candidates() -> None:
    context = make_context()
    systems = BattleSystems()
    decision = systems.skill_target_policy.evaluate(
        context,
        make_operation(context),
        [context.get_unit("b"), context.get_unit("c")],
    )
    assert decision.eligible_candidate_ids == ("b", "c")
    assert decision.required_target_ids == ()
    assert decision.excluded_target_ids == ()
    assert decision.preserve_cardinality


def test_required_target_constraint() -> None:
    context = make_context()
    systems = BattleSystems()
    systems.skill_target_policy.register_rule_adapter(
        lambda _ctx, _op, _raw: TargetPolicyContribution(
            required_target_ids=("c",),
        )
    )
    decision = systems.skill_target_policy.evaluate(
        context,
        make_operation(context),
        [context.get_unit("b"), context.get_unit("c")],
    )
    assert decision.required_target_ids == ("c",)


def test_excluded_target_constraint() -> None:
    context = make_context()
    systems = BattleSystems()
    systems.skill_target_policy.register_rule_adapter(
        lambda _ctx, _op, _raw: TargetPolicyContribution(
            excluded_target_ids=("b",),
        )
    )
    decision = systems.skill_target_policy.evaluate(
        context,
        make_operation(context),
        [context.get_unit("b"), context.get_unit("c")],
    )
    assert decision.eligible_candidate_ids == ("c",)
    assert decision.excluded_target_ids == ("b",)


@pytest.mark.parametrize(
    ("cardinality", "count"),
    [
        (TargetCardinality.SINGLE, None),
        (TargetCardinality.CHOOSE_N, 2),
        (TargetCardinality.FIXED_ALL, None),
    ],
)
def test_preserve_cardinality_representation(cardinality, count) -> None:  # type: ignore[no-untyped-def]
    context = make_context()
    systems = BattleSystems()
    operation = make_operation(context, cardinality=cardinality, count=count)
    decision = systems.skill_target_policy.evaluate(
        context,
        operation,
        [context.get_unit("b"), context.get_unit("c")],
    )
    assert decision.operation.cardinality is cardinality
    assert decision.preserve_cardinality


def test_policy_query_consumes_zero_rng() -> None:
    context = make_context(RandomSystem(55))
    systems = BattleSystems()
    systems.skill_target_policy.evaluate(
        context,
        make_operation(context),
        [context.get_unit("b"), context.get_unit("c")],
    )
    assert context.random.random() == RandomSystem(55).random()


def test_random_selector_remains_rng_owner() -> None:
    rng = CountingRandomSystem()
    context = make_context(rng)
    item = runtime()
    context.skill_runtimes.register(item)
    systems = BattleSystems()
    result = systems.skill_resolver.resolve(context, item)
    assert result.status is SkillResolutionStatus.RESOLVED
    assert rng.sample_calls == 1


def test_synthetic_required_single_avoids_target_rng() -> None:
    rng = CountingRandomSystem()
    context = make_context(rng)
    item = runtime()
    context.skill_runtimes.register(item)
    systems = BattleSystems()
    systems.skill_target_policy.register_rule_adapter(
        lambda _ctx, _op, _raw: TargetPolicyContribution(
            required_target_ids=("c",),
        )
    )
    result = systems.skill_resolver.resolve(context, item)
    assert result.target_ids == ("c",)
    assert rng.sample_calls == 0


def test_synthetic_exclusion_changes_fresh_eligible_pool_only() -> None:
    rng = CountingRandomSystem()
    context = make_context(rng)
    item = runtime()
    context.skill_runtimes.register(item)
    systems = BattleSystems()
    systems.skill_target_policy.register_rule_adapter(
        lambda _ctx, _op, _raw: TargetPolicyContribution(
            excluded_target_ids=("b",),
        )
    )
    result = systems.skill_resolver.resolve(context, item)
    assert result.target_ids == ("c",)
    assert rng.sample_calls == 0


def test_battle_systems_wires_single_round3_foundation_graph() -> None:
    systems = BattleSystems()
    assert (
        systems.skill_operation_admission_coordinator.provider_validity_policy
        is systems.provider_validity_policy
    )
    assert (
        systems.skill_operation_admission_coordinator.skill_permission_policy
        is systems.skill_permission_policy
    )
    assert systems.skill_resolver._admission_coordinator is systems.skill_operation_admission_coordinator
    assert systems.skill_resolver._target_policy is systems.skill_target_policy
    assert systems.recovery_opportunity_system._provider_validity_policy is systems.provider_validity_policy
    assert systems.preparation_interruption_port is systems.preparation_state_owner
    assert not isinstance(
        systems.preparation_interruption_port,
        NoopPreparationInterruptionPort,
    )


def test_normal_attack_domain_does_not_depend_on_skill_target_policy() -> None:
    root = Path(__file__).parents[1] / "sgs_v2" / "battle_core"
    target_resolution = (root / "target_resolution_system.py").read_text(encoding="utf-8")
    skill_policy = (root / "skill_target_policy.py").read_text(encoding="utf-8")
    assert "SkillTargetPolicy" not in target_resolution
    assert "TargetResolutionSystem" not in skill_policy


def test_round3_policy_modules_use_no_random_module_or_context_random() -> None:
    root = Path(__file__).parents[1] / "sgs_v2" / "battle_core"
    for name in (
        "skill_permission.py",
        "skill_operation_admission.py",
        "preparation_interruption.py",
        "skill_target_policy.py",
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


def test_round3_modules_contain_no_stage12_gameplay_switches() -> None:
    root = Path(__file__).parents[1] / "sgs_v2" / "battle_core"
    forbidden = (
        "690089",
        "690101",
        "690107",
        "690108",
        "690222",
        "690109",
        "690110",
    )
    for name in (
        "skill_permission.py",
        "skill_operation_admission.py",
        "preparation_interruption.py",
        "target_operation.py",
        "skill_target_policy.py",
    ):
        source = (root / name).read_text(encoding="utf-8")
        assert all(token not in source for token in forbidden)


def test_skill_resolver_has_no_fallback_provider_policy_construction() -> None:
    path = Path(__file__).parents[1] / "sgs_v2" / "battle_core" / "skill_resolver.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    constructed = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "ProviderValidityPolicy" not in constructed


def test_target_operation_id_is_distinct_from_normal_attack_resolution_id() -> None:
    context = make_context()
    target_operation_id = make_operation(context).operation_id
    target_resolution_id = context.id_allocator.allocate_target_resolution_id()
    assert type(target_operation_id) is not type(target_resolution_id)
