from __future__ import annotations

import inspect

import pytest

from sgs_v2.battle_core import (
    BattlePhase,
    BattleSystems,
    EmptyStateRuntimeParams,
    EquipmentAttributeContribution,
    EquipmentContributionKind,
    EquipmentContributionRef,
    EquipmentProviderRef,
    OfficialStateId,
    ProviderDependency,
    ProviderNode,
    ProviderValidityStatus,
    RandomSystem,
    RemovalOperation,
    StateApplicationResultStatus,
    StateCandidate,
    StateEffectivenessStatus,
    StateLifetimeSpec,
    StateNode,
    StateRemovalResultStatus,
)
from sgs_v2.battle_core import sabotage_integration as sabotage_module
from sgs_v2.battle_core.damage_modifier_system import DamageModifierSystem
from sgs_v2.battle_core.dependency_evaluation import DependencyCycleError
from sgs_v2.battle_core.equipment_effectiveness import (
    EquipmentContributionDependency,
    EquipmentEffectivenessBoundaryError,
    EquipmentEffectivenessStatus,
    EquipmentTriggerGateStatus,
)
from sgs_v2.battle_core.execution_right_runtime import (
    ExecutionRightEvaluationStatus,
    ExecutionRightMode,
    ExecutionRightRequest,
    ExecutionRightSpec,
)
from sgs_v2.battle_core.false_report_integration import (
    FALSE_REPORT_EQUIPMENT_SUPPRESSION_RULE_ID,
)
from sgs_v2.battle_core.recovery_system import (
    RecoveryModifierContribution,
    RecoveryModifierPolicy,
    RecoveryRequest,
)
from sgs_v2.battle_core.sabotage_integration import (
    SABOTAGE_EQUAL_REAPPLICATION_RULE_ID,
    SABOTAGE_GANGYI_ADMISSION_RULE_ID,
    SABOTAGE_PROVIDER_SUPPRESSION_RULE_ID,
    SABOTAGE_STRENGTH_BOUNDARY_RULE_ID,
)
from sgs_v2.battle_core.stage9_integerization import ExactRatio
from tests.test_stage12_690109_sabotage import (
    CountingRandomSystem,
    _damage_request,
    _damage_rules,
    apply_sabotage,
    apply_state,
    assert_effective,
    assert_suppressed,
    make_context,
    register_equipment,
    remove_state,
    settle_due,
)


def test_audit_apply_consumes_zero_rng_and_preserves_downstream_stream() -> None:
    seed = 109001
    rng = CountingRandomSystem(seed)
    context, systems = make_context(rng), BattleSystems()
    register_equipment(systems, kind=EquipmentContributionKind.ATTRIBUTE)

    result = apply_sabotage(systems, context)

    assert result.status is StateApplicationResultStatus.APPLIED
    assert (rng.chance_calls, rng.choice_calls, rng.sample_calls) == (0, 0, 0)
    assert rng.random() == RandomSystem(seed).random()


def test_audit_multiple_contributions_on_one_provider_share_one_suppression_truth() -> None:
    context, systems = make_context(), BattleSystems()
    provider_ref, first = register_equipment(
        systems,
        provider_key="weapon:multi",
        kind=EquipmentContributionKind.ATTRIBUTE,
        contribution_key="weapon:multi:attribute",
    )
    _, second = register_equipment(
        systems,
        provider_key="weapon:multi",
        kind=EquipmentContributionKind.TRIGGER,
        contribution_key="weapon:multi:trigger",
    )
    _, third = register_equipment(
        systems,
        provider_key="weapon:multi",
        kind=EquipmentContributionKind.LIVE_EFFECT,
        contribution_key="weapon:multi:live",
    )

    sabotage = apply_sabotage(systems, context).instance
    assert sabotage is not None
    assert systems.dependency_evaluation_support.prerequisites(
        ProviderNode(provider_ref)
    ) == (StateNode(sabotage.instance_id),)
    for ref in (first, second, third):
        assert_suppressed(systems, context, ref)

    remove_state(systems, context, sabotage.instance_id)
    for ref in (first, second, third):
        assert_effective(systems, context, ref)


def test_audit_baseline_disabled_precedes_sabotage_and_stays_disabled_after_restore() -> None:
    context, systems = make_context(), BattleSystems()
    _, ref = register_equipment(
        systems,
        provider_key="armor:disabled",
        kind=EquipmentContributionKind.ATTRIBUTE,
        enabled=False,
    )

    sabotage = apply_sabotage(systems, context).instance
    assert sabotage is not None
    assert systems.equipment_effectiveness_policy.evaluate_contribution(
        context, ref
    ).status is EquipmentEffectivenessStatus.BASELINE_DISABLED

    remove_state(systems, context, sabotage.instance_id)
    assert systems.equipment_effectiveness_policy.evaluate_contribution(
        context, ref
    ).status is EquipmentEffectivenessStatus.BASELINE_DISABLED


def test_audit_missing_contribution_remains_missing_under_sabotage() -> None:
    context, systems = make_context(), BattleSystems()
    register_equipment(systems, provider_key="weapon:real")
    apply_sabotage(systems, context)
    missing = EquipmentContributionRef(
        EquipmentProviderRef("a", "weapon:missing"),
        "weapon:missing:attribute",
        EquipmentContributionKind.ATTRIBUTE,
    )

    assert systems.equipment_effectiveness_policy.evaluate_contribution(
        context, missing
    ).status is EquipmentEffectivenessStatus.MISSING


def test_audit_contribution_identity_mismatch_precedes_sabotage() -> None:
    context, systems = make_context(), BattleSystems()
    provider_ref, _ = register_equipment(
        systems,
        provider_key="weapon:mismatch",
        contribution_key="same-key",
        kind=EquipmentContributionKind.ATTRIBUTE,
    )
    apply_sabotage(systems, context)
    mismatched = EquipmentContributionRef(
        provider_ref,
        "same-key",
        EquipmentContributionKind.TRIGGER,
    )

    assert systems.equipment_effectiveness_policy.evaluate_contribution(
        context, mismatched
    ).status is EquipmentEffectivenessStatus.IDENTITY_MISMATCH


def test_audit_repeated_suppress_restore_cycles_do_not_replace_equipment_record() -> None:
    context, systems = make_context(), BattleSystems()
    payload = object()
    provider_ref, ref = register_equipment(
        systems,
        provider_key="treasure:stable",
        kind=EquipmentContributionKind.ATTRIBUTE,
        payload=payload,
    )
    record = systems.equipment_contribution_registry.resolve_provider(
        context, provider_ref
    )

    for _ in range(3):
        sabotage = apply_sabotage(systems, context).instance
        assert sabotage is not None
        assert_suppressed(systems, context, ref)
        remove_state(systems, context, sabotage.instance_id)
        assert_effective(systems, context, ref)
        assert systems.equipment_contribution_registry.resolve_provider(
            context, provider_ref
        ) is record

    assert record is not None and record.payload is payload and record.enabled is True


def test_audit_dynamic_attribute_hits_real_consumer_unsupported_boundary() -> None:
    context, systems = make_context(), BattleSystems()
    apply_sabotage(systems, context)
    _, ref = register_equipment(
        systems,
        provider_key="dynamic:attribute",
        kind=EquipmentContributionKind.ATTRIBUTE,
    )

    def provider(_context, unit, attribute):  # type: ignore[no-untyped-def]
        if unit.unit_id == "a" and attribute == "attack":
            return (EquipmentAttributeContribution(ref, "attack", 20.0),)
        return ()

    systems.attribute_system.register_equipment_contribution_provider(provider)

    with pytest.raises(EquipmentEffectivenessBoundaryError):
        systems.attribute_system.get_attack(context, context.get_unit("a"))


def test_audit_dynamic_trigger_gate_surfaces_unsupported_boundary() -> None:
    context, systems = make_context(), BattleSystems()
    apply_sabotage(systems, context)
    _, ref = register_equipment(
        systems,
        provider_key="dynamic:trigger",
        kind=EquipmentContributionKind.TRIGGER,
    )

    decision = systems.trigger_system.evaluate_equipment_dependency(
        context,
        EquipmentContributionDependency(ref, "audit-dynamic-trigger"),
    )

    assert decision.status is EquipmentTriggerGateStatus.UNSUPPORTED_BOUNDARY


def test_audit_dynamic_execution_right_surfaces_unsupported_boundary() -> None:
    context, systems = make_context(), BattleSystems()
    apply_sabotage(systems, context)
    _, ref = register_equipment(
        systems,
        provider_key="dynamic:scheduled",
        kind=EquipmentContributionKind.SCHEDULED_TRIGGER,
    )
    result = systems.execution_right_support.evaluate(
        context,
        ExecutionRightSpec(
            equipment_contribution=ExecutionRightMode.RECHECK_AT_EXECUTION
        ),
        ExecutionRightRequest(
            equipment_dependency=EquipmentContributionDependency(
                ref, "audit-dynamic-scheduled"
            )
        ),
    )

    assert result.status is ExecutionRightEvaluationStatus.UNSUPPORTED_BOUNDARY


def test_audit_damage_modifier_suppression_skips_owned_probability_rng_then_resumes() -> None:
    rng = CountingRandomSystem(109010)
    context, systems = make_context(rng), BattleSystems()
    _, ref = register_equipment(
        systems,
        kind=EquipmentContributionKind.DAMAGE_MODIFIER,
    )
    modifier = DamageModifierSystem(systems.equipment_effectiveness_policy)
    sabotage = apply_sabotage(systems, context).instance
    assert sabotage is not None

    during = modifier.resolve(
        context,
        _damage_request(),
        _damage_rules(ref, probability=0.5),
        100.0,
    )
    assert during.output_damage == 100.0
    assert rng.chance_calls == 0

    remove_state(systems, context, sabotage.instance_id)
    modifier.resolve(
        context,
        _damage_request(),
        _damage_rules(ref, probability=0.5),
        100.0,
    )
    assert rng.chance_calls == 1


def test_audit_recovery_modifier_future_only_resume_no_backfill() -> None:
    provider_ref = EquipmentProviderRef("a", "treasure:audit-prayer")
    ref = EquipmentContributionRef(
        provider_ref,
        "treasure:audit-prayer:recovery",
        EquipmentContributionKind.RECOVERY_MODIFIER,
    )

    def modifier_provider(_context, _request):  # type: ignore[no-untyped-def]
        return RecoveryModifierContribution(
            ExactRatio(3, 2),
            equipment_contribution_ref=ref,
        )

    systems = BattleSystems(recovery_modifier_provider=modifier_provider)
    context = make_context()
    systems.equipment_contribution_registry.register_provider(provider_ref)
    systems.equipment_contribution_registry.register_contribution(ref)
    request = RecoveryRequest(
        source_id="a",
        target_id="a",
        amount=100,
        modifier_policy=RecoveryModifierPolicy.APPLY,
    )

    context.get_unit("a").troops = 400
    sabotage = apply_sabotage(systems, context).instance
    assert sabotage is not None
    during = systems.recovery_system.resolve(context, request)
    assert during.modified_recovery == 100
    assert context.get_unit("a").troops == 500

    remove_state(systems, context, sabotage.instance_id)
    after = systems.recovery_system.resolve(context, request)
    assert after.modified_recovery == 150
    assert context.get_unit("a").troops == 650


def test_audit_scheduled_window_missed_under_sabotage_is_not_replayed() -> None:
    context, systems = make_context(), BattleSystems()
    _, ref = register_equipment(
        systems,
        kind=EquipmentContributionKind.SCHEDULED_TRIGGER,
    )
    spec = ExecutionRightSpec(
        equipment_contribution=ExecutionRightMode.RECHECK_AT_EXECUTION,
    )
    request = ExecutionRightRequest(
        equipment_dependency=EquipmentContributionDependency(
            ref, "audit-window"
        ),
    )
    executed: list[int] = []

    if systems.execution_right_support.evaluate(context, spec, request).allowed:
        executed.append(1)
    sabotage = apply_sabotage(systems, context).instance
    assert sabotage is not None
    if systems.execution_right_support.evaluate(context, spec, request).allowed:
        executed.append(2)
    remove_state(systems, context, sabotage.instance_id)
    if systems.execution_right_support.evaluate(context, spec, request).allowed:
        executed.append(3)

    assert executed == [1, 3]


def test_audit_local_dependent_effect_can_expire_while_sabotage_remains() -> None:
    context, systems = make_context(), BattleSystems()
    provider_ref, _ = register_equipment(
        systems,
        kind=EquipmentContributionKind.LIVE_EFFECT,
    )
    effect = apply_state(
        systems,
        context,
        OfficialStateId.PROVOKE.value,
        owner="a",
        source="a",
        lifetime=StateLifetimeSpec.round_calendar(expires_round=2),
        dependencies=(ProviderDependency(provider_ref, "audit-local"),),
    ).instance
    assert effect is not None
    sabotage = apply_sabotage(
        systems,
        context,
        lifetime=StateLifetimeSpec.round_calendar(expires_round=3),
    ).instance
    assert sabotage is not None
    assert systems.state_effectiveness_policy.evaluate_state(
        context, effect
    ).status is StateEffectivenessStatus.SUPPRESSED

    context.current_round = 2
    context.current_phase = BattlePhase.ROUND_END.value
    removed = settle_due(
        systems, context, round_no=2, phase=BattlePhase.ROUND_END.value
    )
    assert [item.instance_id for item in removed] == [effect.instance_id]
    assert context.states.has_instance(sabotage.instance_id)

    remove_state(systems, context, sabotage.instance_id)
    assert not context.states.has_instance(effect.instance_id)


def test_audit_remote_dependent_effect_expiry_does_not_resurrect_after_owner_restore() -> None:
    context, systems = make_context(), BattleSystems()
    provider_ref, _ = register_equipment(
        systems,
        owner="a",
        provider_key="weapon:audit-remote",
        kind=EquipmentContributionKind.LIVE_EFFECT,
    )
    remote = apply_state(
        systems,
        context,
        OfficialStateId.PROVOKE.value,
        owner="b",
        source="a",
        lifetime=StateLifetimeSpec.round_calendar(expires_round=2),
        dependencies=(ProviderDependency(provider_ref, "audit-remote"),),
    ).instance
    assert remote is not None
    sabotage = apply_sabotage(
        systems,
        context,
        owner="a",
        source="c",
        lifetime=StateLifetimeSpec.round_calendar(expires_round=3),
    ).instance
    assert sabotage is not None

    context.current_round = 2
    context.current_phase = BattlePhase.ROUND_END.value
    settle_due(systems, context, round_no=2, phase=BattlePhase.ROUND_END.value)
    assert not context.states.has_instance(remote.instance_id)

    remove_state(systems, context, sabotage.instance_id)
    assert not context.states.has_instance(remote.instance_id)


def test_audit_remote_holder_sabotage_does_not_close_owner_equipment_provider() -> None:
    context, systems = make_context(), BattleSystems()
    provider_ref, ref = register_equipment(
        systems,
        owner="a",
        provider_key="weapon:owner-a",
        kind=EquipmentContributionKind.LIVE_EFFECT,
    )
    remote = apply_state(
        systems,
        context,
        OfficialStateId.PROVOKE.value,
        owner="b",
        source="a",
        dependencies=(ProviderDependency(provider_ref, "audit-owner-bound"),),
    ).instance
    assert remote is not None

    apply_sabotage(systems, context, owner="b", source="c")

    assert_effective(systems, context, ref)
    assert systems.provider_validity_policy.evaluate_provider(
        context, provider_ref
    ).status is ProviderValidityStatus.VALID
    assert systems.state_effectiveness_policy.evaluate_state(context, remote).effective


def test_audit_attribution_without_dependency_remains_detached() -> None:
    context, systems = make_context(), BattleSystems()
    register_equipment(
        systems,
        owner="a",
        provider_key="weapon:audit-attribution",
        kind=EquipmentContributionKind.LIVE_EFFECT,
    )
    detached = apply_state(
        systems,
        context,
        OfficialStateId.PROVOKE.value,
        owner="b",
        source="a",
    ).instance
    assert detached is not None

    apply_sabotage(systems, context, owner="a", source="c")

    assert systems.dependency_evaluation_support.prerequisites(
        StateNode(detached.instance_id)
    ) == ()
    assert systems.state_effectiveness_policy.evaluate_state(context, detached).effective


def test_audit_source_death_does_not_synthesize_sabotage_removal() -> None:
    context, systems = make_context(), BattleSystems()
    _, ref = register_equipment(systems, owner="a")
    sabotage = apply_sabotage(systems, context, owner="a", source="b").instance
    assert sabotage is not None

    context.get_unit("b").troops = 0
    systems.defeat_cleanup_port.commit_defeat(context, "b")

    assert context.states.has_instance(sabotage.instance_id)
    assert_suppressed(systems, context, ref)


def test_audit_holder_defeat_cleanup_removes_resident_sabotage_as_infrastructure() -> None:
    context, systems = make_context(), BattleSystems()
    _, ref = register_equipment(systems, owner="a")
    sabotage = apply_sabotage(systems, context, owner="a", source="b").instance
    assert sabotage is not None

    context.get_unit("a").troops = 0
    systems.defeat_cleanup_port.commit_defeat(context, "a")

    assert not context.states.has_instance(sabotage.instance_id)
    assert_effective(systems, context, ref)


def test_audit_insight_rejection_allocates_no_sabotage_generation_and_no_rng() -> None:
    seed = 109019
    rng = CountingRandomSystem(seed)
    context, systems = make_context(rng), BattleSystems()
    register_equipment(systems)
    insight = apply_state(
        systems,
        context,
        OfficialStateId.INSIGHT.value,
        owner="a",
        source="b",
    )
    assert insight.status is StateApplicationResultStatus.APPLIED

    result = apply_sabotage(systems, context)

    assert result.status is StateApplicationResultStatus.REJECTED_ADMISSION
    assert str(context.generation_allocator.allocate()) == "gen_2"
    assert rng.random() == RandomSystem(seed).random()


def test_audit_insight_suppress_resume_preserves_sabotage_identity_lifetime_and_rng() -> None:
    seed = 109020
    rng = CountingRandomSystem(seed)
    context, systems = make_context(rng), BattleSystems()
    _, ref = register_equipment(systems)
    sabotage = apply_sabotage(
        systems,
        context,
        lifetime=StateLifetimeSpec.round_calendar(expires_round=4),
    ).instance
    assert sabotage is not None
    snapshot = (
        sabotage.instance_id,
        sabotage.current_generation_id,
        sabotage.lifetime_spec,
    )

    insight = apply_state(
        systems,
        context,
        OfficialStateId.INSIGHT.value,
        owner="a",
        source="b",
    ).instance
    assert insight is not None
    assert_effective(systems, context, ref)

    remove_state(
        systems, context, insight.instance_id, RemovalOperation.NATURAL_EXPIRY
    )

    resumed = context.states.get(sabotage.instance_id)
    assert (
        resumed.instance_id,
        resumed.current_generation_id,
        resumed.lifetime_spec,
    ) == snapshot
    assert_suppressed(systems, context, ref)
    assert rng.random() == RandomSystem(seed).random()


def test_audit_same_envelope_insight_and_sabotage_expiry_emits_no_provider_ghost_transition() -> None:
    context, systems = make_context(), BattleSystems()
    provider_ref, ref = register_equipment(systems)
    lifetime = StateLifetimeSpec.round_calendar(expires_round=2)
    sabotage = apply_sabotage(systems, context, lifetime=lifetime).instance
    assert sabotage is not None
    insight = apply_state(
        systems,
        context,
        OfficialStateId.INSIGHT.value,
        owner="a",
        lifetime=lifetime,
    ).instance
    assert insight is not None
    assert_effective(systems, context, ref)

    transitions = []
    systems.effectiveness_transition_coordinator.register_provider_transition_port(
        lambda _context, transition: transitions.append(transition)
    )

    context.current_round = 2
    context.current_phase = BattlePhase.ROUND_END.value
    settle_due(systems, context, round_no=2, phase=BattlePhase.ROUND_END.value)

    assert systems.provider_validity_policy.evaluate_provider(
        context, provider_ref
    ).status is ProviderValidityStatus.VALID
    assert transitions == []


def test_audit_baseline_disabled_gangyi_does_not_reject_sabotage() -> None:
    context, systems = make_context(), BattleSystems()
    register_equipment(
        systems,
        provider_key="刚毅",
        contribution_key="刚毅",
        enabled=False,
    )

    result = apply_sabotage(systems, context)

    assert result.status is StateApplicationResultStatus.APPLIED


def test_audit_enabled_gangyi_provider_without_contribution_still_rejects() -> None:
    context, systems = make_context(), BattleSystems()
    systems.equipment_contribution_registry.register_provider(
        EquipmentProviderRef("a", "刚毅")
    )

    result = apply_sabotage(systems, context)

    assert result.status is StateApplicationResultStatus.REJECTED_ADMISSION
    assert result.reason_rule_id == SABOTAGE_GANGYI_ADMISSION_RULE_ID


def test_audit_false_report_suppressed_gangyi_does_not_reject_sabotage() -> None:
    context, systems = make_context(), BattleSystems()
    register_equipment(
        systems,
        provider_key="刚毅",
        contribution_key="刚毅",
        kind=EquipmentContributionKind.LIVE_EFFECT,
    )
    false_report = apply_state(
        systems,
        context,
        OfficialStateId.FALSE_REPORT.value,
        owner="a",
        source="b",
    )
    assert false_report.status is StateApplicationResultStatus.APPLIED

    result = apply_sabotage(systems, context)

    assert result.status is StateApplicationResultStatus.APPLIED


def test_audit_equal_reapplication_consumes_no_new_generation_or_dependency_edge() -> None:
    context, systems = make_context(), BattleSystems()
    provider_ref, _ = register_equipment(systems)
    first = apply_sabotage(systems, context).instance
    assert first is not None
    before_edges = systems.dependency_evaluation_support.prerequisites(
        ProviderNode(provider_ref)
    )

    second = apply_sabotage(systems, context, owner="a", source="c")

    assert second.status is StateApplicationResultStatus.REJECTED_CONFLICT
    assert second.reason_rule_id == SABOTAGE_EQUAL_REAPPLICATION_RULE_ID
    assert systems.dependency_evaluation_support.prerequisites(
        ProviderNode(provider_ref)
    ) == before_edges == (StateNode(first.instance_id),)
    assert str(context.generation_allocator.allocate()) == "gen_2"


def test_audit_numeric_strength_boundary_consumes_no_generation() -> None:
    context, systems = make_context(), BattleSystems()

    result = apply_sabotage(systems, context, strength=2.0)

    assert result.status is StateApplicationResultStatus.UNSUPPORTED_BOUNDARY
    assert result.reason_rule_id == SABOTAGE_STRENGTH_BOUNDARY_RULE_ID
    assert str(context.generation_allocator.allocate()) == "gen_1"


def test_audit_specialized_removal_boundary_preserves_state_and_topology() -> None:
    context, systems = make_context(), BattleSystems()
    provider_ref, ref = register_equipment(systems)
    sabotage = apply_sabotage(systems, context).instance
    assert sabotage is not None
    before_edges = systems.dependency_evaluation_support.prerequisites(
        ProviderNode(provider_ref)
    )

    result = remove_state(
        systems,
        context,
        sabotage.instance_id,
        RemovalOperation.SPECIALIZED_CLEANSE,
    )

    assert result.status is StateRemovalResultStatus.UNSUPPORTED_BOUNDARY
    assert context.states.has_instance(sabotage.instance_id)
    assert systems.dependency_evaluation_support.prerequisites(
        ProviderNode(provider_ref)
    ) == before_edges
    assert_suppressed(systems, context, ref)


def test_audit_false_report_and_sabotage_causes_do_not_restore_early() -> None:
    context, systems = make_context(), BattleSystems()
    _, ref = register_equipment(
        systems,
        provider_key="踩踏",
        contribution_key="踩踏",
        kind=EquipmentContributionKind.TRIGGER,
    )
    false_report = apply_state(
        systems,
        context,
        OfficialStateId.FALSE_REPORT.value,
        owner="a",
    ).instance
    assert false_report is not None
    sabotage = apply_sabotage(systems, context).instance
    assert sabotage is not None

    both = systems.equipment_effectiveness_policy.evaluate_contribution(
        context, ref
    )
    assert both.status is EquipmentEffectivenessStatus.SUPPRESSED
    assert any(
        cause.rule_id == FALSE_REPORT_EQUIPMENT_SUPPRESSION_RULE_ID
        for cause in both.suppression_causes
    )
    assert any(
        cause.rule_id == SABOTAGE_PROVIDER_SUPPRESSION_RULE_ID
        for cause in both.suppression_causes
    )

    remove_state(systems, context, false_report.instance_id)
    assert_suppressed(systems, context, ref)
    remove_state(systems, context, sabotage.instance_id)
    assert_effective(systems, context, ref)


def test_audit_dependency_cycle_fails_before_commit_and_preserves_provider_topology() -> None:
    context, systems = make_context(), BattleSystems()
    provider_ref, ref = register_equipment(systems)
    assert systems.dependency_evaluation_support.prerequisites(
        ProviderNode(provider_ref)
    ) == ()

    with pytest.raises(DependencyCycleError):
        apply_sabotage(
            systems,
            context,
            dependencies=(ProviderDependency(provider_ref, "audit-cycle"),),
        )

    assert not context.states.has(
        owner_id="a",
        state_id=OfficialStateId.EQUIPMENT_DISABLE.value,
    )
    assert systems.dependency_evaluation_support.prerequisites(
        ProviderNode(provider_ref)
    ) == ()
    assert_effective(systems, context, ref)
    assert str(context.generation_allocator.allocate()) == "gen_1"


def test_audit_dynamic_equipment_created_while_sabotage_suppressed_becomes_boundary_on_resume() -> None:
    context, systems = make_context(), BattleSystems()
    register_equipment(systems, provider_key="weapon:initial")
    sabotage = apply_sabotage(systems, context).instance
    assert sabotage is not None
    insight = apply_state(
        systems,
        context,
        OfficialStateId.INSIGHT.value,
        owner="a",
    ).instance
    assert insight is not None

    _, dynamic = register_equipment(
        systems,
        provider_key="weapon:dynamic-during-insight",
        kind=EquipmentContributionKind.ATTRIBUTE,
    )
    assert_effective(systems, context, dynamic)

    remove_state(
        systems, context, insight.instance_id, RemovalOperation.NATURAL_EXPIRY
    )

    assert systems.equipment_effectiveness_policy.evaluate_contribution(
        context, dynamic
    ).status is EquipmentEffectivenessStatus.UNSUPPORTED_BOUNDARY


def test_audit_equipment_policy_queries_are_public_event_silent() -> None:
    context, systems = make_context(), BattleSystems()
    provider_ref, ref = register_equipment(systems)
    apply_sabotage(systems, context)
    before = tuple(context.event_bus.history)

    systems.provider_validity_policy.evaluate_provider(context, provider_ref)
    systems.equipment_effectiveness_policy.evaluate_contribution(context, ref)

    assert tuple(context.event_bus.history) == before


def test_audit_canonical_wiring_uses_one_shared_equipment_policy() -> None:
    systems = BattleSystems()

    assert systems.attribute_system.equipment_effectiveness_policy is systems.equipment_effectiveness_policy
    assert systems.trigger_system.equipment_effectiveness_policy is systems.equipment_effectiveness_policy
    assert systems.recovery_system.equipment_effectiveness_policy is systems.equipment_effectiveness_policy
    assert systems.execution_right_support.equipment_effectiveness_policy is systems.equipment_effectiveness_policy
    assert systems.equipment_effectiveness_policy.provider_validity_policy is systems.provider_validity_policy


def test_audit_static_architecture_has_no_sabotage_god_object_or_capture_leakage() -> None:
    source = inspect.getsource(sabotage_module)

    assert "SabotageRuntime" not in source
    assert "SabotageManager" not in source
    assert "SabotageEngine" not in source
    assert "import random" not in source
    assert "context.random" not in source
    assert "EventBus" not in source
    assert ".enabled =" not in source
    assert "OfficialStateId.CAPTURE" not in source
    assert "690110" not in source
