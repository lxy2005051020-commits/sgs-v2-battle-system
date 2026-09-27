from __future__ import annotations

from pathlib import Path

import pytest

from sgs_v2.battle_core import (
    AttributeSystem,
    BattleContext,
    BattleSystems,
    DamageModifierContribution,
    DamageModifierKind,
    DamageModifierOperation,
    DamageModifierPhase,
    DamageModifierSystem,
    DamageRequest,
    DamageRuleCollection,
    DamageSourceType,
    DamageType,
    DamageWorkKind,
    DependencyEvaluationSupport,
    EmptyStateRuntimeParams,
    EquipmentAttributeContribution,
    EquipmentContributionDependency,
    EquipmentContributionKind,
    EquipmentContributionRef,
    EquipmentContributionRegistry,
    EquipmentEffectivenessContribution,
    EquipmentEffectivenessPolicy,
    EquipmentEffectivenessStatus,
    EquipmentProviderRef,
    EquipmentTriggerGateStatus,
    EventBus,
    EventType,
    ExecutionRightDimension,
    ExecutionRightEvaluationStatus,
    ExecutionRightMode,
    ExecutionRightRequest,
    ExecutionRightSpec,
    ExecutionRightSupport,
    ExecutionTargetEligibilityDecision,
    ExecutionTargetEligibilityPolicy,
    ExecutionTargetEligibilityStatus,
    ExactRatio,
    LineupPosition,
    LocalRuleCauseRef,
    ProviderValidityPolicy,
    RandomSystem,
    RecoveryExecutionPreventionContribution,
    RecoveryExecutionPreventionPolicy,
    RecoveryModifierContribution,
    RecoveryModifierPolicy,
    RecoveryPreventionReason,
    RecoveryRequest,
    RecoverySystem,
    RuleContributionSource,
    StateDefinition,
    StateEffectivenessContribution,
    StateEffectivenessPolicy,
    StateInstance,
    StateNode,
    SuppressionCause,
    TriggerSystem,
    TroopSystem,
    UnitRuntime,
    CurrentActorPermissionDecision,
    CurrentActorPermissionPolicy,
    CurrentActorPermissionStatus,
)
from sgs_v2.battle_core.execution_right_runtime import (
    DamageExecutionWork,
)


class CountingRandomSystem(RandomSystem):
    def __init__(self, seed: int = 44) -> None:
        super().__init__(seed)
        self.chance_calls = 0
        self.sample_calls = 0

    def chance(self, probability: float) -> bool:
        self.chance_calls += 1
        return super().chance(probability)

    def sample(self, values, k):  # type: ignore[no-untyped-def]
        self.sample_calls += 1
        return super().sample(values, k)


def make_context(random_system: RandomSystem | None = None) -> BattleContext:
    ctx = BattleContext(
        battle_id="stage12-round4",
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
        random=random_system or RandomSystem(44),
    )
    ctx.current_round = 1
    ctx.current_phase = "UNIT_ACTION"
    return ctx


def make_equipment_foundation(
    *,
    kind: EquipmentContributionKind = EquipmentContributionKind.ATTRIBUTE,
    provider_enabled: bool = True,
    contribution_enabled: bool = True,
):
    deps = DependencyEvaluationSupport()
    state_policy = StateEffectivenessPolicy(deps)
    registry = EquipmentContributionRegistry()
    provider_ref = EquipmentProviderRef("a", "weapon:alpha")
    registry.register_provider(provider_ref, enabled=provider_enabled, payload=object())
    ref = EquipmentContributionRef(provider_ref, "main", kind)
    registry.register_contribution(ref, baseline_enabled=contribution_enabled, payload=object())
    provider_policy = ProviderValidityPolicy(
        deps,
        equipment_resolver=registry.resolve_provider,
    )
    deps.bind_evaluators(
        state_evaluator=state_policy.evaluate_node,
        provider_evaluator=provider_policy.evaluate_node,
    )
    equipment_policy = EquipmentEffectivenessPolicy(registry, provider_policy)
    return deps, state_policy, registry, provider_policy, equipment_policy, ref


def metadata_equipment_adapter(context, _ref):
    keys = tuple(context.metadata.get("equipment_causes", ()))
    causes = tuple(
        SuppressionCause(key, LocalRuleCauseRef(key))
        for key in keys
    )
    return EquipmentEffectivenessContribution(
        suppression_causes=causes,
        unsupported_boundary=bool(context.metadata.get("equipment_unsupported", False)),
    )


def make_execution_support(kind=EquipmentContributionKind.TRIGGER):
    deps, state, registry, provider, equipment, ref = make_equipment_foundation(kind=kind)
    actor = CurrentActorPermissionPolicy()
    target = ExecutionTargetEligibilityPolicy()
    support = ExecutionRightSupport(
        actor_policy=actor,
        provider_policy=provider,
        target_policy=target,
        equipment_policy=equipment,
        state_policy=state,
    )
    return support, actor, target, equipment, ref


def damage_source() -> RuleContributionSource:
    return RuleContributionSource(
        owner_id="a",
        applied_by_unit_id="a",
        source_skill_id="skill.synthetic",
        source_state_id=None,
        source_state_instance_id=None,
        origin_key="round4.synthetic",
    )


def damage_request() -> DamageRequest:
    return DamageRequest(
        source_id="a",
        target_id="b",
        damage_type=DamageType.WEAPON,
        source_type=DamageSourceType.SKILL,
    )


def add_synthetic_state(ctx: BattleContext, instance_id: str = "state-round4") -> StateInstance:
    ctx.states.register_definition(
        StateDefinition(
            state_id="round4.synthetic",
            name="round4.synthetic",
            runtime_params_type=EmptyStateRuntimeParams,
        )
    )
    inst = StateInstance(
        instance_id=instance_id,
        state_id="round4.synthetic",
        owner_id="a",
        source_id="b",
        source_skill_id="synthetic",
        applied_round=1,
        applied_phase="UNIT_ACTION",
    )
    ctx.states.add(inst)
    return inst


def test_equipment_contribution_ref_value_identity() -> None:
    p = EquipmentProviderRef("a", "weapon:alpha")
    a = EquipmentContributionRef(p, "x", EquipmentContributionKind.ATTRIBUTE)
    b = EquipmentContributionRef(p, "x", EquipmentContributionKind.ATTRIBUTE)
    assert a == b
    assert hash(a) == hash(b)


def test_same_provider_different_contribution_key_not_equal() -> None:
    p = EquipmentProviderRef("a", "weapon:alpha")
    assert EquipmentContributionRef(p, "x", EquipmentContributionKind.ATTRIBUTE) != EquipmentContributionRef(
        p, "y", EquipmentContributionKind.ATTRIBUTE
    )


def test_same_key_different_owner_not_equal() -> None:
    a = EquipmentContributionRef(
        EquipmentProviderRef("a", "weapon:alpha"), "x", EquipmentContributionKind.ATTRIBUTE
    )
    b = EquipmentContributionRef(
        EquipmentProviderRef("b", "weapon:alpha"), "x", EquipmentContributionKind.ATTRIBUTE
    )
    assert a != b


def test_contribution_kind_part_of_identity_or_contract_as_frozen() -> None:
    p = EquipmentProviderRef("a", "weapon:alpha")
    assert EquipmentContributionRef(p, "x", EquipmentContributionKind.ATTRIBUTE) != EquipmentContributionRef(
        p, "x", EquipmentContributionKind.TRIGGER
    )


def test_missing_equipment_contribution() -> None:
    _, _, registry, _, policy, ref = make_equipment_foundation()
    missing = EquipmentContributionRef(ref.provider_ref, "missing", ref.kind)
    assert registry.resolve_contribution(missing).status.value == "MISSING"
    assert policy.evaluate_contribution(make_context(), missing).status is EquipmentEffectivenessStatus.MISSING


def test_identity_mismatch_equipment_contribution() -> None:
    _, _, registry, _, policy, ref = make_equipment_foundation()
    mismatch = EquipmentContributionRef(
        ref.provider_ref, ref.contribution_key, EquipmentContributionKind.TRIGGER
    )
    assert registry.resolve_contribution(mismatch).status.value == "IDENTITY_MISMATCH"
    assert policy.evaluate_contribution(make_context(), mismatch).status is EquipmentEffectivenessStatus.IDENTITY_MISMATCH


def test_equipment_contribution_effective() -> None:
    *_, policy, ref = make_equipment_foundation()
    assert policy.evaluate_contribution(make_context(), ref).status is EquipmentEffectivenessStatus.EFFECTIVE


def test_equipment_contribution_baseline_disabled() -> None:
    *_, policy, ref = make_equipment_foundation(contribution_enabled=False)
    assert policy.evaluate_contribution(make_context(), ref).status is EquipmentEffectivenessStatus.BASELINE_DISABLED


def test_equipment_provider_baseline_disabled() -> None:
    *_, policy, ref = make_equipment_foundation(provider_enabled=False)
    assert policy.evaluate_contribution(make_context(), ref).status is EquipmentEffectivenessStatus.BASELINE_DISABLED


def test_single_suppression_cause() -> None:
    *_, policy, ref = make_equipment_foundation()
    policy.register_rule_adapter(metadata_equipment_adapter)
    ctx = make_context()
    ctx.metadata["equipment_causes"] = ("A",)
    decision = policy.evaluate_contribution(ctx, ref)
    assert decision.status is EquipmentEffectivenessStatus.SUPPRESSED
    assert len(decision.suppression_causes) == 1


def test_multiple_suppression_causes() -> None:
    *_, policy, ref = make_equipment_foundation()
    policy.register_rule_adapter(metadata_equipment_adapter)
    ctx = make_context()
    ctx.metadata["equipment_causes"] = ("A", "B")
    assert len(policy.evaluate_contribution(ctx, ref).suppression_causes) == 2


def test_remove_one_cause_still_suppressed() -> None:
    *_, policy, ref = make_equipment_foundation()
    policy.register_rule_adapter(metadata_equipment_adapter)
    ctx = make_context()
    ctx.metadata["equipment_causes"] = ("A", "B")
    assert policy.evaluate_contribution(ctx, ref).status is EquipmentEffectivenessStatus.SUPPRESSED
    ctx.metadata["equipment_causes"] = ("B",)
    assert policy.evaluate_contribution(ctx, ref).status is EquipmentEffectivenessStatus.SUPPRESSED


def test_remove_last_cause_effective() -> None:
    *_, policy, ref = make_equipment_foundation()
    policy.register_rule_adapter(metadata_equipment_adapter)
    ctx = make_context()
    ctx.metadata["equipment_causes"] = ("A",)
    assert policy.evaluate_contribution(ctx, ref).status is EquipmentEffectivenessStatus.SUPPRESSED
    ctx.metadata["equipment_causes"] = ()
    assert policy.evaluate_contribution(ctx, ref).status is EquipmentEffectivenessStatus.EFFECTIVE


def test_unsupported_boundary_explicit() -> None:
    *_, policy, ref = make_equipment_foundation()
    policy.register_rule_adapter(metadata_equipment_adapter)
    ctx = make_context()
    ctx.metadata["equipment_unsupported"] = True
    assert policy.evaluate_contribution(ctx, ref).status is EquipmentEffectivenessStatus.UNSUPPORTED_BOUNDARY


def test_policy_zero_rng() -> None:
    rng = CountingRandomSystem()
    *_, policy, ref = make_equipment_foundation()
    policy.evaluate_contribution(make_context(rng), ref)
    assert rng.chance_calls == rng.sample_calls == 0


def test_policy_zero_event() -> None:
    ctx = make_context()
    *_, policy, ref = make_equipment_foundation()
    before = ctx.event_bus.history
    policy.evaluate_contribution(ctx, ref)
    assert ctx.event_bus.history == before


def test_suppressed_contribution_retains_provider_object_and_identity() -> None:
    _, _, registry, _, policy, ref = make_equipment_foundation()
    policy.register_rule_adapter(metadata_equipment_adapter)
    ctx = make_context()
    provider_record = registry.resolve_provider(ctx, ref.provider_ref)
    ctx.metadata["equipment_causes"] = ("A",)
    policy.evaluate_contribution(ctx, ref)
    ctx.metadata["equipment_causes"] = ()
    policy.evaluate_contribution(ctx, ref)
    assert registry.resolve_provider(ctx, ref.provider_ref) is provider_record
    assert registry.resolve_contribution(ref).record.contribution_ref == ref


def test_synthetic_equipment_attribute_filtered_when_suppressed() -> None:
    *_, policy, ref = make_equipment_foundation(kind=EquipmentContributionKind.ATTRIBUTE)
    policy.register_rule_adapter(metadata_equipment_adapter)
    system = AttributeSystem(equipment_effectiveness_policy=policy)
    system.register_equipment_contribution_provider(
        lambda _c, _u, _a: (EquipmentAttributeContribution(ref, "attack", 25),)
    )
    ctx = make_context()
    assert system.get_attack(ctx, ctx.units["a"]) == 125
    ctx.metadata["equipment_causes"] = ("A",)
    assert system.get_attack(ctx, ctx.units["a"]) == 100


def test_attribute_resume_has_no_cumulative_drift() -> None:
    *_, policy, ref = make_equipment_foundation()
    policy.register_rule_adapter(metadata_equipment_adapter)
    system = AttributeSystem(equipment_effectiveness_policy=policy)
    system.register_equipment_contribution_provider(
        lambda _c, _u, _a: (EquipmentAttributeContribution(ref, "attack", 10),)
    )
    ctx = make_context()
    assert system.get_attack(ctx, ctx.units["a"]) == 110
    ctx.metadata["equipment_causes"] = ("A",)
    assert system.get_attack(ctx, ctx.units["a"]) == 100
    ctx.metadata["equipment_causes"] = ()
    assert system.get_attack(ctx, ctx.units["a"]) == 110


def test_no_equipment_rule_preserves_existing_attribute_behavior() -> None:
    ctx = make_context()
    assert AttributeSystem().get_attack(ctx, ctx.units["a"]) == 100


def equipment_damage_contribution(ref, order_key="10", probability=1.0):
    return DamageModifierContribution(
        phase=DamageModifierPhase.OUTGOING,
        kind=DamageModifierKind.OUTGOING_INCREASE,
        operation=DamageModifierOperation.MULTIPLY_FACTOR,
        operand=2.0,
        source=damage_source(),
        order_key=order_key,
        probability=probability,
        equipment_contribution_ref=ref,
    )


def test_synthetic_equipment_damage_modifier_filtered() -> None:
    *_, policy, ref = make_equipment_foundation(kind=EquipmentContributionKind.DAMAGE_MODIFIER)
    policy.register_rule_adapter(metadata_equipment_adapter)
    system = DamageModifierSystem(policy)
    ctx = make_context()
    rules = DamageRuleCollection(modifier_contributions=(equipment_damage_contribution(ref),))
    assert system.resolve(ctx, damage_request(), rules, 10).output_damage == 20
    ctx.metadata["equipment_causes"] = ("A",)
    assert system.resolve(ctx, damage_request(), rules, 10).output_damage == 10


def test_modifier_order_key_unchanged_after_filtering() -> None:
    *_, policy, ref = make_equipment_foundation(kind=EquipmentContributionKind.DAMAGE_MODIFIER)
    policy.register_rule_adapter(metadata_equipment_adapter)
    generic = DamageModifierContribution(
        DamageModifierPhase.OUTGOING,
        DamageModifierKind.OUTGOING_INCREASE,
        DamageModifierOperation.MULTIPLY_FACTOR,
        1.5,
        damage_source(),
        "20",
    )
    ctx = make_context()
    ctx.metadata["equipment_causes"] = ("A",)
    result = DamageModifierSystem(policy).resolve(
        ctx,
        damage_request(),
        DamageRuleCollection(modifier_contributions=(equipment_damage_contribution(ref, "10"), generic)),
        10,
    )
    assert [x.contribution.order_key for x in result.applied_modifiers] == ["20"]


def test_old_settled_damage_not_affected_by_later_suppression() -> None:
    *_, policy, ref = make_equipment_foundation(kind=EquipmentContributionKind.DAMAGE_MODIFIER)
    policy.register_rule_adapter(metadata_equipment_adapter)
    ctx = make_context()
    system = DamageModifierSystem(policy)
    rules = DamageRuleCollection(modifier_contributions=(equipment_damage_contribution(ref),))
    old = system.resolve(ctx, damage_request(), rules, 10)
    ctx.metadata["equipment_causes"] = ("A",)
    new = system.resolve(ctx, damage_request(), rules, 10)
    assert old.output_damage == 20
    assert new.output_damage == 10


def test_filtered_damage_modifier_consumes_no_modifier_rng() -> None:
    rng = CountingRandomSystem()
    *_, policy, ref = make_equipment_foundation(kind=EquipmentContributionKind.DAMAGE_MODIFIER)
    policy.register_rule_adapter(metadata_equipment_adapter)
    ctx = make_context(rng)
    ctx.metadata["equipment_causes"] = ("A",)
    rules = DamageRuleCollection(
        modifier_contributions=(equipment_damage_contribution(ref, probability=0.5),)
    )
    DamageModifierSystem(policy).resolve(ctx, damage_request(), rules, 10)
    assert rng.chance_calls == 0


def test_synthetic_equipment_recovery_modifier_filtered() -> None:
    *_, policy, ref = make_equipment_foundation(kind=EquipmentContributionKind.RECOVERY_MODIFIER)
    policy.register_rule_adapter(metadata_equipment_adapter)
    provider = lambda _c, _r: RecoveryModifierContribution(ExactRatio(3, 2), ref)
    system = RecoverySystem(
        TroopSystem(),
        recovery_modifier_provider=provider,
        equipment_effectiveness_policy=policy,
    )
    ctx = make_context()
    ctx.units["b"].troops = 900
    req = RecoveryRequest("a", "b", 5, modifier_policy=RecoveryModifierPolicy.APPLY)
    assert system.resolve(ctx, req).modified_recovery == 8
    ctx.units["b"].troops = 900
    ctx.metadata["equipment_causes"] = ("A",)
    assert system.resolve(ctx, req).modified_recovery == 5


def test_recovery_second_ceil_order_preserved() -> None:
    *_, policy, ref = make_equipment_foundation(kind=EquipmentContributionKind.RECOVERY_MODIFIER)
    seen = []
    prevention = RecoveryExecutionPreventionPolicy()
    prevention.register_rule_adapter(
        lambda _c, r: (
            seen.append(r.modified_recovery)
            or RecoveryExecutionPreventionContribution("synthetic")
        )
    )
    system = RecoverySystem(
        TroopSystem(),
        recovery_modifier_provider=lambda _c, _r: RecoveryModifierContribution(ExactRatio(3, 2), ref),
        equipment_effectiveness_policy=policy,
        execution_prevention_policy=prevention,
    )
    ctx = make_context()
    ctx.units["b"].troops = 900
    result = system.resolve(
        ctx,
        RecoveryRequest("a", "b", 5, modifier_policy=RecoveryModifierPolicy.APPLY),
    )
    assert seen == [8]
    assert result.reason is RecoveryPreventionReason.FOUNDATION_POLICY
    assert result.modified_recovery == 8


def test_existing_healing_block_order_preserved() -> None:
    source = Path("sgs_v2/battle_core/recovery_system.py").read_text(encoding="utf-8")
    resolve_body = source[source.index("    def resolve("):]
    assert resolve_body.index("modified_recovery = self._apply_recovery_modifier") < resolve_body.index(
        "healing_ban_id = OfficialStateId.HEALING_BAN.value"
    )
    assert resolve_body.index("self._execution_prevention_policy.evaluate") < resolve_body.index(
        "healing_ban_id = OfficialStateId.HEALING_BAN.value"
    )


def test_equipment_dependent_trigger_effective_executes() -> None:
    *_, policy, ref = make_equipment_foundation(kind=EquipmentContributionKind.TRIGGER)
    trigger = TriggerSystem(equipment_effectiveness_policy=policy)
    decision = trigger.evaluate_equipment_dependency(
        make_context(), EquipmentContributionDependency(ref, "synthetic")
    )
    assert decision.status is EquipmentTriggerGateStatus.ALLOW


def test_equipment_dependent_trigger_suppressed_skips() -> None:
    *_, policy, ref = make_equipment_foundation(kind=EquipmentContributionKind.TRIGGER)
    policy.register_rule_adapter(metadata_equipment_adapter)
    ctx = make_context()
    ctx.metadata["equipment_causes"] = ("A",)
    decision = TriggerSystem(equipment_effectiveness_policy=policy).evaluate_equipment_dependency(
        ctx, EquipmentContributionDependency(ref, "synthetic")
    )
    assert decision.status is EquipmentTriggerGateStatus.SKIP


def test_suppressed_trigger_not_replayed_on_resume() -> None:
    *_, policy, ref = make_equipment_foundation(kind=EquipmentContributionKind.SCHEDULED_TRIGGER)
    policy.register_rule_adapter(metadata_equipment_adapter)
    ctx = make_context()
    gate = TriggerSystem(equipment_effectiveness_policy=policy)
    dep = EquipmentContributionDependency(ref, "scheduled")
    ctx.metadata["equipment_causes"] = ("A",)
    skipped = gate.evaluate_equipment_dependency(ctx, dep)
    ctx.metadata["equipment_causes"] = ()
    future = gate.evaluate_equipment_dependency(ctx, dep)
    assert skipped.status is EquipmentTriggerGateStatus.SKIP
    assert future.status is EquipmentTriggerGateStatus.ALLOW
    assert not hasattr(gate, "replay_queue")


def test_attribution_only_trigger_does_not_gain_equipment_dependency() -> None:
    source = Path("sgs_v2/battle_core/trigger_system.py").read_text(encoding="utf-8")
    start = source.index("    def evaluate_equipment_dependency")
    end = source.index("    def collect(", start)
    body = source[start:end]
    assert "EffectSourceRef" not in body
    assert "source_ref" not in body


def test_explicit_equipment_dependency_propagates() -> None:
    *_, ref = make_equipment_foundation()[-2:]
    dep = EquipmentContributionDependency(ref, "live")
    assert dep.contribution_ref == ref


def test_effect_source_ref_alone_does_not_propagate() -> None:
    source = Path("sgs_v2/battle_core/equipment_effectiveness.py").read_text(encoding="utf-8")
    assert "EffectSourceRef" not in source


def test_remote_effect_dependency_uses_provider_owner_not_holder_identity() -> None:
    p = EquipmentProviderRef("a", "weapon:alpha")
    dep = EquipmentContributionDependency(
        EquipmentContributionRef(p, "remote", EquipmentContributionKind.LIVE_EFFECT),
        "remote",
    )
    holder_id = "b"
    assert dep.contribution_ref.provider_ref.owner_id == "a"
    assert dep.contribution_ref.provider_ref.owner_id != holder_id


def test_modes_are_per_dimension() -> None:
    spec = ExecutionRightSpec(
        actor_permission=ExecutionRightMode.NOT_APPLICABLE,
        provider_validity=ExecutionRightMode.SNAPSHOT_AT_ADMISSION,
        target_eligibility=ExecutionRightMode.RECHECK_AT_EXECUTION,
        equipment_contribution=ExecutionRightMode.UNSUPPORTED_BOUNDARY,
    )
    assert spec.mode_for(ExecutionRightDimension.PROVIDER_VALIDITY) is ExecutionRightMode.SNAPSHOT_AT_ADMISSION
    assert spec.mode_for(ExecutionRightDimension.TARGET_ELIGIBILITY) is ExecutionRightMode.RECHECK_AT_EXECUTION


def test_snapshot_dimension_not_rechecked() -> None:
    support, actor, _, _, _ = make_execution_support()
    actor.register_rule_adapter(
        lambda _c, r: CurrentActorPermissionDecision(r, CurrentActorPermissionStatus.DENY, ("x",))
    )
    result = support.evaluate(
        make_context(),
        ExecutionRightSpec(actor_permission=ExecutionRightMode.SNAPSHOT_AT_ADMISSION),
        ExecutionRightRequest(current_actor_id="a"),
    )
    assert result.allowed
    assert result.checked_dimensions == ()


def test_jit_dimension_rechecked() -> None:
    support, actor, _, _, _ = make_execution_support()
    actor.register_rule_adapter(
        lambda _c, r: CurrentActorPermissionDecision(r, CurrentActorPermissionStatus.DENY, ("x",))
    )
    result = support.evaluate(
        make_context(),
        ExecutionRightSpec(actor_permission=ExecutionRightMode.RECHECK_AT_EXECUTION),
        ExecutionRightRequest(current_actor_id="a"),
    )
    assert result.status is ExecutionRightEvaluationStatus.DENY_ACTOR


def test_not_applicable_dimension_skipped() -> None:
    support, *_ = make_execution_support()
    result = support.evaluate(
        make_context(),
        ExecutionRightSpec(actor_permission=ExecutionRightMode.NOT_APPLICABLE),
        ExecutionRightRequest(),
    )
    assert result.allowed and result.checked_dimensions == ()


def test_execution_right_unsupported_boundary_is_explicit() -> None:
    support, *_ = make_execution_support()
    result = support.evaluate(
        make_context(),
        ExecutionRightSpec(actor_permission=ExecutionRightMode.UNSUPPORTED_BOUNDARY),
        ExecutionRightRequest(),
    )
    assert result.status is ExecutionRightEvaluationStatus.UNSUPPORTED_BOUNDARY


def test_execution_right_evaluation_zero_rng() -> None:
    rng = CountingRandomSystem()
    support, *_ = make_execution_support()
    support.evaluate(
        make_context(rng),
        ExecutionRightSpec(actor_permission=ExecutionRightMode.RECHECK_AT_EXECUTION),
        ExecutionRightRequest(current_actor_id="a"),
    )
    assert rng.chance_calls == rng.sample_calls == 0


def test_execution_right_evaluation_zero_event() -> None:
    ctx = make_context()
    support, *_ = make_execution_support()
    support.evaluate(
        ctx,
        ExecutionRightSpec(actor_permission=ExecutionRightMode.RECHECK_AT_EXECUTION),
        ExecutionRightRequest(current_actor_id="a"),
    )
    assert ctx.event_bus.history == ()


@pytest.mark.parametrize(
    "spec",
    [
        ExecutionRightSpec(
            provider_validity=ExecutionRightMode.SNAPSHOT_AT_ADMISSION,
            target_eligibility=ExecutionRightMode.RECHECK_AT_EXECUTION,
        ),
        ExecutionRightSpec(
            target_eligibility=ExecutionRightMode.SNAPSHOT_AT_ADMISSION,
            provider_validity=ExecutionRightMode.RECHECK_AT_EXECUTION,
        ),
        ExecutionRightSpec(
            actor_permission=ExecutionRightMode.NOT_APPLICABLE,
            equipment_contribution=ExecutionRightMode.RECHECK_AT_EXECUTION,
        ),
    ],
)
def test_mixed_stability_modes_can_coexist(spec: ExecutionRightSpec) -> None:
    assert len({spec.actor_permission, spec.provider_validity, spec.target_eligibility, spec.equipment_contribution}) >= 2


def test_provider_snapshot_target_jit_can_coexist() -> None:
    test_mixed_stability_modes_can_coexist(
        ExecutionRightSpec(
            provider_validity=ExecutionRightMode.SNAPSHOT_AT_ADMISSION,
            target_eligibility=ExecutionRightMode.RECHECK_AT_EXECUTION,
        )
    )


def test_target_snapshot_provider_jit_can_coexist() -> None:
    test_mixed_stability_modes_can_coexist(
        ExecutionRightSpec(
            target_eligibility=ExecutionRightMode.SNAPSHOT_AT_ADMISSION,
            provider_validity=ExecutionRightMode.RECHECK_AT_EXECUTION,
        )
    )


def test_actor_not_applicable_equipment_jit_can_coexist() -> None:
    test_mixed_stability_modes_can_coexist(
        ExecutionRightSpec(
            actor_permission=ExecutionRightMode.NOT_APPLICABLE,
            equipment_contribution=ExecutionRightMode.RECHECK_AT_EXECUTION,
        )
    )


def test_current_actor_distinct_from_historical_source() -> None:
    request = ExecutionRightRequest(current_actor_id="a", historical_source_id="b")
    assert request.current_actor_id != request.historical_source_id


def test_free_proxy_uses_current_actor_permission() -> None:
    support, actor, *_ = make_execution_support()
    actor.register_rule_adapter(
        lambda _c, r: (
            CurrentActorPermissionDecision(r, CurrentActorPermissionStatus.DENY, ("actor-b",))
            if r.actor_id == "b" else None
        )
    )
    result = support.evaluate(
        make_context(),
        ExecutionRightSpec(actor_permission=ExecutionRightMode.RECHECK_AT_EXECUTION),
        ExecutionRightRequest(current_actor_id="a", historical_source_id="b"),
    )
    assert result.allowed


def test_origin_provider_does_not_override_current_actor() -> None:
    support, actor, _, _, ref = make_execution_support()
    actor.register_rule_adapter(
        lambda _c, r: CurrentActorPermissionDecision(r, CurrentActorPermissionStatus.DENY, ("actor",))
    )
    result = support.evaluate(
        make_context(),
        ExecutionRightSpec(actor_permission=ExecutionRightMode.RECHECK_AT_EXECUTION),
        ExecutionRightRequest(current_actor_id="b", origin_provider=ref.provider_ref),
    )
    assert result.status is ExecutionRightEvaluationStatus.DENY_ACTOR


def test_attached_dot_actor_permission_not_applicable() -> None:
    support, *_ = make_execution_support()
    work = DamageExecutionWork(
        DamageWorkKind.ATTACHED_EXISTING_DOT,
        ExecutionRightSpec(actor_permission=ExecutionRightMode.NOT_APPLICABLE),
        ExecutionRightRequest(historical_source_id="a"),
    )
    assert support.evaluate(make_context(), work.spec, work.request).allowed


def test_new_actor_damage_actor_permission_jit() -> None:
    support, actor, *_ = make_execution_support()
    actor.register_rule_adapter(
        lambda _c, r: CurrentActorPermissionDecision(r, CurrentActorPermissionStatus.DENY, ("deny",))
    )
    work = DamageExecutionWork(
        DamageWorkKind.NEW_ACTOR_DRIVEN_DAMAGE,
        ExecutionRightSpec(actor_permission=ExecutionRightMode.RECHECK_AT_EXECUTION),
        ExecutionRightRequest(current_actor_id="a"),
    )
    assert support.evaluate(make_context(), work.spec, work.request).status is ExecutionRightEvaluationStatus.DENY_ACTOR


def test_already_created_request_can_be_explicit_boundary() -> None:
    support, *_ = make_execution_support()
    work = DamageExecutionWork(
        DamageWorkKind.ALREADY_CREATED_DAMAGE_REQUEST,
        ExecutionRightSpec(actor_permission=ExecutionRightMode.UNSUPPORTED_BOUNDARY),
        ExecutionRightRequest(current_actor_id="a"),
    )
    assert support.evaluate(make_context(), work.spec, work.request).status is ExecutionRightEvaluationStatus.UNSUPPORTED_BOUNDARY


def test_counter_work_kind_is_distinct() -> None:
    assert DamageWorkKind.COUNTER_DAMAGE is not DamageWorkKind.NEW_ACTOR_DRIVEN_DAMAGE


def test_free_proxy_work_kind_is_distinct() -> None:
    assert DamageWorkKind.FREE_PROXY_DAMAGE is not DamageWorkKind.ATTACHED_EXISTING_DOT


def test_execution_right_does_not_recheck_unspecified_dimensions() -> None:
    support, _, target, _, _ = make_execution_support()
    calls = []
    target.register_rule_adapter(lambda _c, r: (calls.append(r) or None))
    result = support.evaluate(
        make_context(),
        ExecutionRightSpec(actor_permission=ExecutionRightMode.RECHECK_AT_EXECUTION),
        ExecutionRightRequest(current_actor_id="a", target_id="b"),
    )
    assert result.allowed
    assert calls == []


def test_jit_dimension_observes_changed_validity() -> None:
    support, actor, *_ = make_execution_support()
    ctx = make_context()
    def adapter(c, r):
        if c.metadata.get("deny_actor"):
            return CurrentActorPermissionDecision(r, CurrentActorPermissionStatus.DENY, ("changed",))
        return None
    actor.register_rule_adapter(adapter)
    spec = ExecutionRightSpec(actor_permission=ExecutionRightMode.RECHECK_AT_EXECUTION)
    req = ExecutionRightRequest(current_actor_id="a")
    assert support.evaluate(ctx, spec, req).allowed
    ctx.metadata["deny_actor"] = True
    assert support.evaluate(ctx, spec, req).status is ExecutionRightEvaluationStatus.DENY_ACTOR


def transition_state_adapter(context, instance, _session):
    if instance.instance_id in set(context.metadata.get("blocked_states", ())):
        return StateEffectivenessContribution(
            suppression_causes=(
                SuppressionCause("round4.transition", LocalRuleCauseRef("round4.transition")),
            )
        )
    return StateEffectivenessContribution()


def test_effective_to_suppressed_event_once() -> None:
    systems = BattleSystems()
    ctx = make_context()
    inst = add_synthetic_state(ctx)
    systems.state_effectiveness_policy.register_rule_adapter(transition_state_adapter)
    before = systems.effectiveness_transition_coordinator.capture(ctx, (StateNode(inst.instance_id),))
    ctx.metadata["blocked_states"] = (inst.instance_id,)
    systems.effectiveness_transition_coordinator.settle(ctx, before, (StateNode(inst.instance_id),))
    assert [e.event_type for e in ctx.event_bus.history].count(EventType.STATE_SUPPRESSED) == 1


def test_suppressed_to_effective_event_once() -> None:
    systems = BattleSystems()
    ctx = make_context()
    inst = add_synthetic_state(ctx)
    systems.state_effectiveness_policy.register_rule_adapter(transition_state_adapter)
    ctx.metadata["blocked_states"] = (inst.instance_id,)
    before = systems.effectiveness_transition_coordinator.capture(ctx, (StateNode(inst.instance_id),))
    ctx.metadata["blocked_states"] = ()
    systems.effectiveness_transition_coordinator.settle(ctx, before, (StateNode(inst.instance_id),))
    assert [e.event_type for e in ctx.event_bus.history].count(EventType.STATE_RESUMED) == 1


def test_same_status_emits_no_event() -> None:
    systems = BattleSystems()
    ctx = make_context()
    inst = add_synthetic_state(ctx)
    before = systems.effectiveness_transition_coordinator.capture(ctx, (StateNode(inst.instance_id),))
    systems.effectiveness_transition_coordinator.settle(ctx, before, (StateNode(inst.instance_id),))
    assert not any(e.event_type in (EventType.STATE_SUPPRESSED, EventType.STATE_RESUMED) for e in ctx.event_bus.history)


def test_remove_one_of_multiple_causes_emits_no_resume() -> None:
    systems = BattleSystems()
    ctx = make_context()
    inst = add_synthetic_state(ctx)
    def adapter(c, _i, _s):
        return StateEffectivenessContribution(
            suppression_causes=tuple(
                SuppressionCause(key, LocalRuleCauseRef(key))
                for key in c.metadata.get("causes", ())
            )
        )
    systems.state_effectiveness_policy.register_rule_adapter(adapter)
    ctx.metadata["causes"] = ("A", "B")
    before = systems.effectiveness_transition_coordinator.capture(ctx, (StateNode(inst.instance_id),))
    ctx.metadata["causes"] = ("B",)
    systems.effectiveness_transition_coordinator.settle(ctx, before, (StateNode(inst.instance_id),))
    assert not any(e.event_type is EventType.STATE_RESUMED for e in ctx.event_bus.history)


def test_failed_transaction_emits_no_transition_event() -> None:
    systems = BattleSystems()
    ctx = make_context()
    inst = add_synthetic_state(ctx)
    before = systems.effectiveness_transition_coordinator.capture(ctx, (StateNode(inst.instance_id),))
    # A rejected/failed envelope never performs a committed mutation; settling unchanged
    # canonical facts therefore produces no transition fact.
    systems.effectiveness_transition_coordinator.settle(ctx, before, (StateNode(inst.instance_id),))
    assert ctx.event_bus.history == ()


def test_single_equipment_contribution_registry() -> None:
    systems = BattleSystems()
    assert systems.equipment_effectiveness_policy.registry is systems.equipment_contribution_registry


def test_single_equipment_effectiveness_policy() -> None:
    systems = BattleSystems()
    assert systems.attribute_system.equipment_effectiveness_policy is systems.equipment_effectiveness_policy
    assert systems.trigger_system.equipment_effectiveness_policy is systems.equipment_effectiveness_policy


def test_execution_right_support_uses_canonical_provider_policy() -> None:
    systems = BattleSystems()
    assert systems.execution_right_support.provider_validity_policy is systems.provider_validity_policy


def test_equipment_consumers_share_same_equipment_policy() -> None:
    systems = BattleSystems()
    assert systems.recovery_system.equipment_effectiveness_policy is systems.equipment_effectiveness_policy
    assert systems.damage_system._modifiers.equipment_effectiveness_policy is systems.equipment_effectiveness_policy
    assert systems.execution_right_support.equipment_effectiveness_policy is systems.equipment_effectiveness_policy


def test_static_round4_architecture_guards() -> None:
    files = [
        Path("sgs_v2/battle_core/equipment_effectiveness.py"),
        Path("sgs_v2/battle_core/execution_right_runtime.py"),
    ]
    joined = "\n".join(path.read_text(encoding="utf-8") for path in files)
    assert "import random" not in joined
    assert "context.random" not in joined
    assert "GlobalExecutionRightManager" not in joined
    assert ".enabled = False" not in joined
    assert ".enabled = True" not in joined
    for state_id in ("690089", "690101", "690107", "690108", "690222", "690109", "690110"):
        assert state_id not in joined


def test_no_fallback_equipment_effectiveness_policy_construction() -> None:
    consumers = [
        Path("sgs_v2/battle_core/attribute_system.py"),
        Path("sgs_v2/battle_core/damage_modifier_system.py"),
        Path("sgs_v2/battle_core/recovery_system.py"),
        Path("sgs_v2/battle_core/trigger_system.py"),
    ]
    for path in consumers:
        text = path.read_text(encoding="utf-8")
        assert "EquipmentEffectivenessPolicy()" not in text


def test_damage_coordinator_has_generic_execution_right_hook() -> None:
    systems = BattleSystems()
    work = DamageExecutionWork(
        DamageWorkKind.OTHER_BOUNDED,
        ExecutionRightSpec(),
        ExecutionRightRequest(),
    )
    assert systems.damage_instance_coordinator.evaluate_execution_right(make_context(), work).allowed


def test_committed_public_state_fact_runs_after_internal_transition_ports() -> None:
    systems = BattleSystems()
    ctx = make_context()
    inst = add_synthetic_state(ctx)
    systems.state_effectiveness_policy.register_rule_adapter(transition_state_adapter)

    observations: list[tuple[str, int]] = []
    systems.effectiveness_transition_coordinator.register_state_transition_port(
        lambda context, _transition: observations.append(
            ("internal", len(context.event_bus.history))
        )
    )

    before = systems.effectiveness_transition_coordinator.capture(
        ctx,
        (StateNode(inst.instance_id),),
    )
    ctx.metadata["blocked_states"] = (inst.instance_id,)
    systems.effectiveness_transition_coordinator.settle(
        ctx,
        before,
        (StateNode(inst.instance_id),),
    )

    assert observations == [("internal", 0)]
    assert len(ctx.event_bus.history) == 1
    assert ctx.event_bus.history[0].event_type is EventType.STATE_SUPPRESSED
