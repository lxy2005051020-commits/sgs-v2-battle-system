from __future__ import annotations

from pathlib import Path

import pytest

from sgs_v2.battle_core import (
    AdmissionDecision,
    AdmissionStatus,
    BattlePhase,
    BattleSystems,
    EmptyStateRuntimeParams,
    EquipmentProviderRef,
    EventType,
    OfficialStateId,
    ProviderDependency,
    ProviderNode,
    ProviderValidityStatus,
    RandomSystem,
    RemovalOperation,
    SkillOperationAdmissionStatus,
    SkillSlot,
    SkillType,
    StateApplicationCoordinator,
    StateApplicationResultStatus,
    StateCandidate,
    StateEffectivenessStatus,
    StateLifetimeSpec,
    StateNode,
    StateRemovalResultStatus,
    StateTransactionPreconditionError,
)
from sgs_v2.battle_core.intimidation_integration import (
    INTIMIDATION_EMPTY_POOL_BOUNDARY_RULE_ID,
    INTIMIDATION_PROVIDER_SUPPRESSION_RULE_ID,
    intimidation_eligible_provider_pool,
)
from tests.test_stage12_690222_intimidation import (
    CountingRandomSystem,
    SequenceChoiceRandomSystem,
    admit,
    apply_false_report,
    apply_intimidation,
    apply_simple_state,
    make_context,
    pref,
    remove_state,
    settle_due,
    skill,
)


def test_single_candidate_binding_zero_rng() -> None:
    rng = CountingRandomSystem(92001)
    context = make_context(rng)
    runtime = skill(context, skill_id="single")
    systems = BattleSystems()

    result = apply_intimidation(systems, context)

    assert result.status is StateApplicationResultStatus.APPLIED
    assert result.instance is not None
    assert result.instance.bound_provider_ref == pref(runtime)
    assert rng.choice_calls == []
    assert rng.random() == RandomSystem(92001).random()


def test_multi_candidate_binding_exactly_one_choice() -> None:
    rng = CountingRandomSystem(92002)
    context = make_context(rng)
    skill(context, slot=SkillSlot.LEARNED_2, skill_id="z", skill_type=SkillType.TROOP)
    skill(context, slot=SkillSlot.INHERENT, skill_id="m", skill_type=SkillType.ACTIVE)
    skill(context, slot=SkillSlot.LEARNED_1, skill_id="a", skill_type=SkillType.COMMAND)
    systems = BattleSystems()

    pool = intimidation_eligible_provider_pool(context, "a")
    result = apply_intimidation(systems, context)

    assert result.instance is not None
    assert len(rng.choice_calls) == 1
    assert rng.choice_calls[0] == pool
    assert tuple(ref.skill_slot for ref in pool) == (
        SkillSlot.INHERENT,
        SkillSlot.LEARNED_1,
        SkillSlot.LEARNED_2,
    )


def test_rd_sf_006_downstream_rng_stream_stable() -> None:
    seed = 92003
    rng = CountingRandomSystem(seed)
    context = make_context(rng)
    skill(context, slot=SkillSlot.INHERENT, skill_id="a")
    skill(context, slot=SkillSlot.LEARNED_1, skill_id="b")
    skill(context, slot=SkillSlot.LEARNED_2, skill_id="c")
    systems = BattleSystems()
    pool = intimidation_eligible_provider_pool(context, "a")

    result = apply_intimidation(systems, context)
    assert result.instance is not None

    expected = RandomSystem(seed)
    expected_selected = expected.choice(pool)
    expected_next = expected.random()

    assert result.instance.bound_provider_ref == expected_selected
    assert rng.choice_calls == [pool]
    assert context.random.random() == expected_next


def test_rejected_create_zero_binding_rng() -> None:
    rng = CountingRandomSystem(92004)
    context = make_context(rng)
    skill(context, skill_id="eligible")
    systems = BattleSystems()

    def reject_intimidation(_context, incoming):
        if incoming.state_id != OfficialStateId.INTIMIDATION.value:
            return None
        return AdmissionDecision(
            AdmissionStatus.REJECT_INVALID_TARGET,
            "AUDIT_FORCED_PRECOMMIT_REJECTION",
        )

    systems.state_admission_policy.register_rule_adapter(reject_intimidation)
    result = apply_intimidation(systems, context)

    assert result.status is StateApplicationResultStatus.REJECTED_ADMISSION
    assert rng.choice_calls == []
    assert str(context.generation_allocator.allocate()) == "gen_1"
    assert not context.states.has(
        owner_id="a",
        state_id=OfficialStateId.INTIMIDATION.value,
    )


def test_gangyi_rejection_zero_binding_rng() -> None:
    rng = CountingRandomSystem(92005)
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


def test_refresh_rerolls_binding() -> None:
    rng = SequenceChoiceRandomSystem((0, 1))
    context = make_context(rng)
    first = skill(context, slot=SkillSlot.INHERENT, skill_id="first")
    second = skill(context, slot=SkillSlot.LEARNED_1, skill_id="second")
    systems = BattleSystems()

    created = apply_intimidation(systems, context)
    assert created.instance is not None
    old_generation = created.instance.current_generation_id
    assert created.instance.bound_provider_ref == pref(first)

    refreshed = apply_intimidation(systems, context)

    assert refreshed.status is StateApplicationResultStatus.REFRESHED
    assert refreshed.instance is not None
    assert refreshed.instance.bound_provider_ref == pref(second)
    assert refreshed.instance.current_generation_id != old_generation
    assert len(rng.choice_calls) == 2


def test_refresh_same_provider_still_new_generation() -> None:
    rng = SequenceChoiceRandomSystem((0, 0))
    context = make_context(rng)
    first = skill(context, slot=SkillSlot.INHERENT, skill_id="first")
    skill(context, slot=SkillSlot.LEARNED_1, skill_id="second")
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


def test_refresh_failure_preserves_old_binding(monkeypatch) -> None:
    rng = SequenceChoiceRandomSystem((0, 1))
    context = make_context(rng)
    first = skill(context, slot=SkillSlot.INHERENT, skill_id="first")
    skill(context, slot=SkillSlot.LEARNED_1, skill_id="second")
    systems = BattleSystems()

    created = apply_intimidation(
        systems,
        context,
        lifetime=StateLifetimeSpec.round_calendar(expires_round=2),
    )
    assert created.instance is not None
    old = context.states.get(created.instance.instance_id)
    original = StateApplicationCoordinator._assert_preconditions
    calls = {"count": 0}

    def fail_after_binding(self, *args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 2:
            raise StateTransactionPreconditionError(
                "audit injected post-binding precondition failure"
            )
        return original(self, *args, **kwargs)

    monkeypatch.setattr(
        StateApplicationCoordinator,
        "_assert_preconditions",
        fail_after_binding,
    )

    with pytest.raises(StateTransactionPreconditionError):
        apply_intimidation(
            systems,
            context,
            lifetime=StateLifetimeSpec.round_calendar(expires_round=3),
        )

    current = context.states.get(old.instance_id)
    assert current.bound_provider_ref == pref(first) == old.bound_provider_ref
    assert current.current_generation_id == old.current_generation_id
    assert current.lifetime_spec == old.lifetime_spec
    assert len(rng.choice_calls) == 2
    assert systems.provider_validity_policy.evaluate_provider(
        context, pref(first)
    ).status is ProviderValidityStatus.SUPPRESSED


def test_dependency_cycle_refresh_preserves_old_binding() -> None:
    from sgs_v2.battle_core import DependencyCycleError

    rng = SequenceChoiceRandomSystem((0,))
    context = make_context(rng)
    first = skill(context, slot=SkillSlot.INHERENT, skill_id="first")
    skill(context, slot=SkillSlot.LEARNED_1, skill_id="second")
    systems = BattleSystems()

    created = apply_intimidation(
        systems,
        context,
        lifetime=StateLifetimeSpec.round_calendar(expires_round=2),
    )
    assert created.instance is not None
    old = context.states.get(created.instance.instance_id)

    with pytest.raises(DependencyCycleError):
        apply_intimidation(
            systems,
            context,
            lifetime=StateLifetimeSpec.round_calendar(expires_round=3),
            dependencies=(ProviderDependency(pref(first), "audit-cycle"),),
        )

    current = context.states.get(old.instance_id)
    assert current.bound_provider_ref == old.bound_provider_ref
    assert current.current_generation_id == old.current_generation_id
    assert current.lifetime_spec == old.lifetime_spec
    assert rng.choice_calls and len(rng.choice_calls) == 1
    assert systems.dependency_evaluation_support.prerequisites(
        ProviderNode(pref(first))
    ) == (StateNode(old.instance_id),)


def test_resume_retains_binding_zero_rng() -> None:
    rng = SequenceChoiceRandomSystem((0,))
    context = make_context(rng)
    target_a = skill(context, owner="a", slot=SkillSlot.INHERENT, skill_id="target-a")
    skill(context, owner="a", slot=SkillSlot.LEARNED_1, skill_id="target-b")
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
        dependencies=(ProviderDependency(pref(source), "source-dependency"),),
    )
    assert created.instance is not None
    snapshot = (
        created.instance.bound_provider_ref,
        created.instance.current_generation_id,
        created.instance.lifetime_spec,
    )
    assert created.instance.bound_provider_ref == pref(target_a)
    assert len(rng.choice_calls) == 1

    false_report = apply_false_report(systems, context, owner="b", source="a")
    assert false_report.instance is not None
    assert systems.state_effectiveness_policy.evaluate_state(
        context, context.states.get(created.instance.instance_id)
    ).status is StateEffectivenessStatus.SUPPRESSED

    remove_state(
        systems,
        context,
        false_report.instance.instance_id,
        RemovalOperation.ORDINARY_CLEANSE,
    )

    resumed = context.states.get(created.instance.instance_id)
    assert (
        resumed.bound_provider_ref,
        resumed.current_generation_id,
        resumed.lifetime_spec,
    ) == snapshot
    assert len(rng.choice_calls) == 1


def test_initial_suppressed_stores_binding_without_provider_effect() -> None:
    rng = CountingRandomSystem(92010)
    context = make_context(rng)
    target = skill(context, owner="a", skill_id="target")
    source = skill(
        context,
        owner="b",
        skill_id="source-passive",
        skill_type=SkillType.PASSIVE,
    )
    systems = BattleSystems()
    false_report = apply_false_report(systems, context, owner="b", source="a")
    assert false_report.instance is not None

    result = apply_intimidation(
        systems,
        context,
        source="b",
        source_skill_id=source.definition.skill_id,
        source_skill_slot=source.skill_slot,
        dependencies=(ProviderDependency(pref(source), "source-dependency"),),
    )

    assert result.instance is not None
    assert result.instance.bound_provider_ref == pref(target)
    assert systems.state_effectiveness_policy.evaluate_state(
        context, result.instance
    ).status is StateEffectivenessStatus.SUPPRESSED
    assert systems.provider_validity_policy.evaluate_provider(
        context, pref(target)
    ).status is ProviderValidityStatus.VALID
    assert rng.choice_calls == []


def test_create_interrupts_exact_bound_preparing_provider() -> None:
    rng = SequenceChoiceRandomSystem((0,))
    context = make_context(rng)
    first = skill(
        context,
        slot=SkillSlot.INHERENT,
        skill_id="prep-first",
        preparation=__import__("sgs_v2.battle_core", fromlist=["PreparationMode"]).PreparationMode.REQUIRED,
    )
    second = skill(
        context,
        slot=SkillSlot.LEARNED_1,
        skill_id="prep-second",
        preparation=__import__("sgs_v2.battle_core", fromlist=["PreparationMode"]).PreparationMode.REQUIRED,
    )
    systems = BattleSystems()
    systems.preparation_state_owner.begin_preparing(
        holder_id="a",
        provider_ref=pref(first),
        admitted_operation_id="first-op",
    )
    systems.preparation_state_owner.begin_preparing(
        holder_id="a",
        provider_ref=pref(second),
        admitted_operation_id="second-op",
    )

    result = apply_intimidation(systems, context)
    assert result.instance is not None
    assert result.instance.bound_provider_ref == pref(first)

    remaining = systems.preparation_state_owner.get_preparing("a")
    assert tuple(record.provider_ref for record in remaining) == (pref(second),)


def test_refresh_interrupts_new_bound_provider_only() -> None:
    from sgs_v2.battle_core import PreparationMode

    rng = SequenceChoiceRandomSystem((0, 1))
    context = make_context(rng)
    skill(
        context,
        slot=SkillSlot.INHERENT,
        skill_id="old",
        preparation=PreparationMode.REQUIRED,
    )
    new = skill(
        context,
        slot=SkillSlot.LEARNED_1,
        skill_id="new",
        preparation=PreparationMode.REQUIRED,
    )
    other = skill(
        context,
        slot=SkillSlot.LEARNED_2,
        skill_id="other",
        preparation=PreparationMode.REQUIRED,
    )
    systems = BattleSystems()
    apply_intimidation(systems, context)

    systems.preparation_state_owner.begin_preparing(
        holder_id="a",
        provider_ref=pref(new),
        admitted_operation_id="new-op",
    )
    systems.preparation_state_owner.begin_preparing(
        holder_id="a",
        provider_ref=pref(other),
        admitted_operation_id="other-op",
    )

    refreshed = apply_intimidation(systems, context)
    assert refreshed.instance is not None
    assert refreshed.instance.bound_provider_ref == pref(new)

    remaining = systems.preparation_state_owner.get_preparing("a")
    assert tuple(record.provider_ref for record in remaining) == (pref(other),)


def test_resume_interrupts_retained_bound_provider_only() -> None:
    from sgs_v2.battle_core import PreparationMode

    rng = SequenceChoiceRandomSystem((0,))
    context = make_context(rng)
    retained = skill(
        context,
        owner="a",
        slot=SkillSlot.INHERENT,
        skill_id="retained",
        preparation=PreparationMode.REQUIRED,
    )
    other = skill(
        context,
        owner="a",
        slot=SkillSlot.LEARNED_1,
        skill_id="other",
        preparation=PreparationMode.REQUIRED,
    )
    source = skill(
        context,
        owner="b",
        skill_id="source-passive",
        skill_type=SkillType.PASSIVE,
    )
    systems = BattleSystems()
    false_report = apply_false_report(systems, context, owner="b", source="a")
    assert false_report.instance is not None

    created = apply_intimidation(
        systems,
        context,
        source="b",
        source_skill_id=source.definition.skill_id,
        source_skill_slot=source.skill_slot,
        dependencies=(ProviderDependency(pref(source), "source-dependency"),),
    )
    assert created.instance is not None
    assert created.instance.bound_provider_ref == pref(retained)

    systems.preparation_state_owner.begin_preparing(
        holder_id="a",
        provider_ref=pref(retained),
        admitted_operation_id="retained-op",
    )
    systems.preparation_state_owner.begin_preparing(
        holder_id="a",
        provider_ref=pref(other),
        admitted_operation_id="other-op",
    )

    remove_state(
        systems,
        context,
        false_report.instance.instance_id,
        RemovalOperation.ORDINARY_CLEANSE,
    )

    remaining = systems.preparation_state_owner.get_preparing("a")
    assert tuple(record.provider_ref for record in remaining) == (pref(other),)
    assert len(rng.choice_calls) == 1


def test_false_report_and_intimidation_suppression_compose() -> None:
    context = make_context()
    runtime = skill(
        context,
        skill_type=SkillType.PASSIVE,
        skill_id="shared-passive",
    )
    systems = BattleSystems()

    intimidation = apply_intimidation(systems, context)
    false_report = apply_false_report(systems, context, owner="a", source="b")
    assert intimidation.instance is not None
    assert false_report.instance is not None

    both = systems.provider_validity_policy.evaluate_provider(context, pref(runtime))
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


def test_exhaustion_provider_validity_precedence() -> None:
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
        source_skill_id="exhaustion",
        source_skill_slot=SkillSlot.LEARNED_2,
    )
    assert exhaustion.status is StateApplicationResultStatus.APPLIED

    decision = admit(systems, context, runtime)
    assert decision.status is SkillOperationAdmissionStatus.DENY_PROVIDER_INVALID
    assert decision.permission_decision is None


def test_explicit_provider_dependency_propagates() -> None:
    context = make_context()
    runtime = skill(
        context,
        owner="a",
        skill_type=SkillType.PASSIVE,
        skill_id="insight-provider",
    )
    systems = BattleSystems()
    dependent = apply_simple_state(
        systems,
        context,
        OfficialStateId.INSIGHT.value,
        owner="a",
        source="b",
        source_skill_id="insight-source",
        source_skill_slot=SkillSlot.LEARNED_2,
        dependencies=(ProviderDependency(pref(runtime), "explicit-provider-dependency"),),
    )
    assert dependent.instance is not None

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


def test_attribution_without_dependency_does_not_propagate() -> None:
    context = make_context()
    runtime = skill(
        context,
        owner="a",
        skill_type=SkillType.PASSIVE,
        skill_id="attributed-provider",
    )
    systems = BattleSystems()
    dependent = apply_simple_state(
        systems,
        context,
        OfficialStateId.INSIGHT.value,
        owner="a",
        source="a",
        source_skill_id=runtime.definition.skill_id,
        source_skill_slot=runtime.skill_slot,
        dependencies=(),
    )
    assert dependent.instance is not None

    apply_intimidation(systems, context)

    assert systems.provider_validity_policy.evaluate_provider(
        context, pref(runtime)
    ).status is ProviderValidityStatus.SUPPRESSED
    assert systems.state_effectiveness_policy.evaluate_state(
        context, dependent.instance
    ).status is StateEffectivenessStatus.EFFECTIVE


def test_generic_cleanse_does_not_remove_intimidation() -> None:
    context = make_context()
    skill(context)
    systems = BattleSystems()
    result = apply_intimidation(systems, context)
    assert result.instance is not None

    removed = remove_state(
        systems,
        context,
        result.instance.instance_id,
        RemovalOperation.ORDINARY_CLEANSE,
    )

    assert removed.status is StateRemovalResultStatus.REJECTED
    assert context.states.has_instance(result.instance.instance_id)


def test_source_death_boundary_not_silently_defined() -> None:
    context = make_context()
    skill(context, owner="a", skill_id="target")
    systems = BattleSystems()
    result = apply_intimidation(
        systems,
        context,
        source="b",
        source_skill_id="source-intimidation",
        source_skill_slot=SkillSlot.LEARNED_1,
    )
    assert result.instance is not None

    context.get_unit("b").troops = 0
    systems.state_lifecycle_system.clear_owner_on_defeat(context, "b")

    assert context.states.has_instance(result.instance.instance_id)
    assert context.states.get(result.instance.instance_id).owner_id == "a"


def test_empty_pool_remains_unsupported() -> None:
    rng = CountingRandomSystem(92020)
    context = make_context(rng)
    systems = BattleSystems()

    result = apply_intimidation(systems, context)

    assert result.status is StateApplicationResultStatus.UNSUPPORTED_BOUNDARY
    assert result.reason_rule_id == INTIMIDATION_EMPTY_POOL_BOUNDARY_RULE_ID
    assert rng.choice_calls == []
    assert not context.states.has(
        owner_id="a",
        state_id=OfficialStateId.INTIMIDATION.value,
    )


def test_talent_remains_unsupported() -> None:
    rng = CountingRandomSystem(92021)
    context = make_context(rng)
    skill(context, skill_type=SkillType.TALENT)
    systems = BattleSystems()

    assert intimidation_eligible_provider_pool(context, "a") == ()
    result = apply_intimidation(systems, context)

    assert result.status is StateApplicationResultStatus.UNSUPPORTED_BOUNDARY
    assert rng.choice_calls == []


def test_formation_never_enters_binding_pool() -> None:
    rng = CountingRandomSystem(92022)
    context = make_context(rng)
    eligible = skill(
        context,
        slot=SkillSlot.INHERENT,
        skill_id="eligible",
        skill_type=SkillType.ACTIVE,
    )
    skill(
        context,
        slot=SkillSlot.LEARNED_1,
        skill_id="formation",
        skill_type=SkillType.FORMATION,
    )
    systems = BattleSystems()

    assert intimidation_eligible_provider_pool(context, "a") == (pref(eligible),)
    result = apply_intimidation(systems, context)

    assert result.instance is not None
    assert result.instance.bound_provider_ref == pref(eligible)
    assert rng.choice_calls == []


def test_normal_attack_never_enters_binding_pool() -> None:
    rng = CountingRandomSystem(92023)
    context = make_context(rng)
    eligible = skill(context, skill_type=SkillType.ACTIVE)
    systems = BattleSystems()

    assert intimidation_eligible_provider_pool(context, "a") == (pref(eligible),)
    result = apply_intimidation(systems, context)
    assert result.instance is not None
    assert rng.choice_calls == []

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


def test_same_envelope_no_ghost_resume_or_prep_interrupt() -> None:
    from sgs_v2.battle_core import PreparationMode

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

    intimidation = apply_intimidation(
        systems,
        context,
        source="b",
        source_skill_id=source.definition.skill_id,
        source_skill_slot=source.skill_slot,
        lifetime=StateLifetimeSpec.round_calendar(expires_round=2),
        dependencies=(ProviderDependency(pref(source), "source-dependency"),),
    )
    assert intimidation.instance is not None

    false_report = systems.state_application_coordinator.apply_candidate(
        context,
        StateCandidate(
            state_id=OfficialStateId.FALSE_REPORT.value,
            owner_id="b",
            source_id="a",
            source_skill_id="false-report-source",
            source_skill_slot=SkillSlot.LEARNED_2,
            runtime_params_candidate=EmptyStateRuntimeParams(),
            lifetime_spec=StateLifetimeSpec.round_calendar(expires_round=2),
            application_provenance="690222-same-envelope-audit",
        ),
    )
    assert false_report.instance is not None
    assert systems.state_effectiveness_policy.evaluate_state(
        context, context.states.get(intimidation.instance.instance_id)
    ).status is StateEffectivenessStatus.SUPPRESSED

    systems.preparation_state_owner.begin_preparing(
        holder_id="a",
        provider_ref=pref(target),
        admitted_operation_id="same-envelope-prep",
    )

    context.current_round = 2
    context.current_phase = BattlePhase.ROUND_END.value
    removed = settle_due(
        systems,
        context,
        round_no=2,
        phase=BattlePhase.ROUND_END.value,
    )

    assert {item.instance_id for item in removed} == {
        intimidation.instance.instance_id,
        false_report.instance.instance_id,
    }
    assert systems.preparation_state_owner.is_preparing("a")
    assert not context.states.has_instance(intimidation.instance.instance_id)


def test_troop_provider_can_be_bound_and_become_provider_suppressed() -> None:
    context = make_context()
    troop = skill(
        context,
        skill_id="troop-provider",
        skill_type=SkillType.TROOP,
    )
    systems = BattleSystems()

    result = apply_intimidation(systems, context)

    assert result.instance is not None
    assert result.instance.bound_provider_ref == pref(troop)
    decision = systems.provider_validity_policy.evaluate_provider(context, pref(troop))
    assert decision.status is ProviderValidityStatus.SUPPRESSED
    assert any(
        cause.rule_id == INTIMIDATION_PROVIDER_SUPPRESSION_RULE_ID
        for cause in decision.suppression_causes
    )


def test_one_state_one_binding_and_no_stack_count() -> None:
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


def test_query_and_binding_emit_no_intimidation_public_events() -> None:
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


def test_static_architecture_has_no_intimidation_god_object_or_rng_leak() -> None:
    root = Path(__file__).resolve().parents[1]
    battle_core = root / "sgs_v2" / "battle_core"
    intimidation_source = (battle_core / "intimidation_integration.py").read_text(
        encoding="utf-8"
    )

    assert "import random" not in intimidation_source
    assert "from random" not in intimidation_source
    assert ".publish(" not in intimidation_source
    assert "enabled = False" not in intimidation_source

    joined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in battle_core.glob("*.py")
    )
    assert "class IntimidationRuntime" not in joined
    assert "class IntimidationManager" not in joined
    assert "class IntimidationEngine" not in joined


def test_canonical_wiring_has_single_shared_owner_instances() -> None:
    root = Path(__file__).resolve().parents[1]
    source = (
        root / "sgs_v2" / "battle_core" / "battle_systems.py"
    ).read_text(encoding="utf-8")

    assert source.count(
        "self.dependency_evaluation_support = DependencyEvaluationSupport()"
    ) == 1
    assert source.count(
        "self.state_effectiveness_policy = StateEffectivenessPolicy("
    ) == 1
    assert source.count(
        "self.provider_validity_policy = ProviderValidityPolicy("
    ) == 1
    assert source.count(
        "self.effectiveness_transition_coordinator = EffectivenessTransitionCoordinator("
    ) == 1
    assert source.count("self.preparation_state_owner = PreparationStateOwner()") == 1
