from __future__ import annotations

import inspect

import pytest

from sgs_v2.battle_core import (
    BattleSystems,
    DamageDeniedEffectResult,
    DamageExecutionWork,
    DamageWorkKind,
    EquipmentContributionKind,
    EquipmentContributionRef,
    EquipmentEffectivenessStatus,
    EquipmentProviderRef,
    EventType,
    ExecutionRightEvaluationStatus,
    ExecutionRightMode,
    ExecutionRightRequest,
    ExecutionRightSpec,
    OfficialStateId,
    ProviderDependency,
    ProviderValidityStatus,
    RecoveryPreventedResult,
    RecoveryRequest,
    RemovalOperation,
    SkillResolutionStatus,
    SkillSlot,
    SkillTargetMode,
    SkillType,
    StateApplicationResultStatus,
    StateEffectivenessStatus,
    StateLifetimeSpec,
    StateNode,
    StateRemovalResultStatus,
    TargetOperationProducer,
    TargetQueryMode,
    TargetSelectionProvenance,
    TargetSelectionResult,
)
from sgs_v2.battle_core import capture_integration as capture_module
from sgs_v2.battle_core.capture_integration import (
    CAPTURE_EQUIPMENT_ATTRIBUTE_RULE_ID,
    CAPTURE_PROVIDER_SUPPRESSION_RULE_ID,
    CAPTURE_RECOVERY_PREVENTION_RULE_ID,
)
from sgs_v2.battle_core.false_report_integration import FALSE_REPORT_PROVIDER_SUPPRESSION_RULE_ID
from sgs_v2.battle_core.intimidation_integration import INTIMIDATION_PROVIDER_SUPPRESSION_RULE_ID
from sgs_v2.battle_core.stage11_state_params import Stage11TimedFlagParams, StunStateParams
from tests.test_stage12_690110_capture import (
    CountingRandomSystem,
    active_damage_effect,
    apply_capture,
    apply_state,
    create_counter_batch,
    expire_holder_action_window,
    make_context,
    natural_action,
    periodic_damage_effect,
    provider_ref,
    register_equipment_attribute,
    register_runtime,
)
from tests.test_stage12_690222_intimidation import (
    apply_intimidation,
    make_context as make_intimidation_context,
    pref as intimidation_provider_ref,
    skill as intimidation_skill,
)


def test_capture_natural_action_short_circuits_normal_attack_and_rng(monkeypatch) -> None:
    rng = CountingRandomSystem(110001)
    context, systems = make_context(rng), BattleSystems()
    apply_capture(systems, context, owner="a")
    monkeypatch.setattr(
        systems.normal_attack_system,
        "execute",
        lambda *_a, **_k: pytest.fail("Capture reached NormalAttackSystem"),
    )
    assert natural_action(systems, context, "a") is None
    assert (rng.choice_calls, rng.sample_calls) == (0, 0)
    assert not any(e.event_type is EventType.NORMAL_ATTACK and e.actor_id == "a" for e in context.event_bus.history)


def test_capture_does_not_consume_stun_when_capture_blocks_action() -> None:
    context, systems = make_context(), BattleSystems()
    stun = apply_state(
        systems, context, OfficialStateId.STUN.value, owner="a",
        runtime_params=StunStateParams(remaining_blocks=2),
    ).instance
    assert stun is not None
    apply_capture(systems, context, owner="a")
    assert natural_action(systems, context, "a") is None
    current = context.states.get(stun.instance_id)
    assert isinstance(current.runtime_params, StunStateParams)
    assert current.runtime_params.remaining_blocks == 2


def test_capture_new_actor_damage_denied_before_damage_request(monkeypatch) -> None:
    context, systems = make_context(), BattleSystems()
    apply_capture(systems, context, owner="a")
    seq = context.id_allocator._damage_instance_seq
    monkeypatch.setattr(
        systems.damage_system,
        "calculate",
        lambda *_a, **_k: pytest.fail("Capture reached DamageSystem.calculate"),
    )
    result = systems.effect_executor.execute(context, active_damage_effect(source="a", target="b"))
    assert isinstance(result, DamageDeniedEffectResult)
    assert result.execution_right.status is ExecutionRightEvaluationStatus.DENY_ACTOR
    assert context.id_allocator._damage_instance_seq == seq


def test_capture_counter_opportunity_survives_but_damage_denied(monkeypatch) -> None:
    context, systems = make_context(), BattleSystems()
    batch = create_counter_batch(systems, context, owner="b", attacker="a")
    entries = tuple(batch.entries)
    assert entries
    apply_capture(systems, context, owner="b", source="a")
    monkeypatch.setattr(
        systems.damage_system,
        "calculate",
        lambda *_a, **_k: pytest.fail("Capture counter reached damage math"),
    )
    result = systems.counter_system.execute(context, batch)
    assert tuple(batch.entries) == entries
    assert all(item.executed and item.actual_troop_loss == 0 and item.damage_execution is None for item in result)
    assert any(e.event_type is EventType.COUNTER_EXECUTE and e.actor_id == "b" for e in context.event_bus.history)


def test_capture_attached_dot_continues() -> None:
    context, systems = make_context(), BattleSystems()
    apply_capture(systems, context, owner="a")
    before = context.get_unit("b").troops
    result = systems.effect_executor.execute(context, periodic_damage_effect(source="a", target="b"))
    assert not isinstance(result, DamageDeniedEffectResult)
    assert context.get_unit("b").troops < before


def test_capture_no_universal_source_id_damage_gate() -> None:
    context, systems = make_context(), BattleSystems()
    apply_capture(systems, context, owner="a")
    direct = systems.effect_executor.execute(context, active_damage_effect(source="a", target="b"))
    counter = systems.counter_system.execute(context, create_counter_batch(systems, context, owner="a", attacker="b"))
    before = context.get_unit("b").troops
    dot = systems.effect_executor.execute(context, periodic_damage_effect(source="a", target="b"))
    assert isinstance(direct, DamageDeniedEffectResult)
    assert counter and all(x.actual_troop_loss == 0 and x.damage_execution is None for x in counter)
    assert not isinstance(dot, DamageDeniedEffectResult)
    assert context.get_unit("b").troops < before


def test_capture_free_proxy_uses_current_actor() -> None:
    context, systems = make_context(), BattleSystems()
    apply_capture(systems, context, owner="a")
    work = DamageExecutionWork(
        DamageWorkKind.FREE_PROXY_DAMAGE,
        ExecutionRightSpec(actor_permission=ExecutionRightMode.RECHECK_AT_EXECUTION),
        ExecutionRightRequest(
            current_actor_id="b",
            actor_operation_kind=DamageWorkKind.FREE_PROXY_DAMAGE.value,
            historical_source_id="a",
            damage_source_id="a",
        ),
    )
    assert systems.damage_instance_coordinator.evaluate_execution_right(context, work).allowed


def test_q16_already_created_damage_request_remains_unsupported() -> None:
    context, systems = make_context(), BattleSystems()
    work = DamageExecutionWork(
        DamageWorkKind.ALREADY_CREATED_DAMAGE_REQUEST,
        ExecutionRightSpec(actor_permission=ExecutionRightMode.UNSUPPORTED_BOUNDARY),
        ExecutionRightRequest(
            current_actor_id="a",
            actor_operation_kind=DamageWorkKind.ALREADY_CREATED_DAMAGE_REQUEST.value,
        ),
    )
    assert systems.damage_instance_coordinator.evaluate_execution_right(context, work).status is ExecutionRightEvaluationStatus.UNSUPPORTED_BOUNDARY


def _provider_under_capture(skill_type: SkillType):
    rng = CountingRandomSystem(110010, chance_result=True)
    context = make_context(rng)
    runtime = register_runtime(context, skill_type=skill_type, skill_id=f"audit-{skill_type.value}", activation_rate=0.5)
    systems = BattleSystems()
    apply_capture(systems, context, owner="a")
    decision = systems.provider_validity_policy.evaluate_provider(context, provider_ref(runtime))
    result = systems.skill_resolver.resolve(context, runtime)
    return rng, runtime, decision, result


def test_capture_passive_provider_suppressed_without_runtime_disable() -> None:
    rng, runtime, decision, result = _provider_under_capture(SkillType.PASSIVE)
    assert runtime.enabled is True
    assert decision.status is ProviderValidityStatus.SUPPRESSED
    assert result.status is SkillResolutionStatus.DISABLED
    assert rng.chance_calls == 0


def test_capture_command_provider_suppressed_without_runtime_disable() -> None:
    rng, runtime, decision, result = _provider_under_capture(SkillType.COMMAND)
    assert runtime.enabled is True
    assert decision.status is ProviderValidityStatus.SUPPRESSED
    assert result.status is SkillResolutionStatus.DISABLED
    assert rng.chance_calls == 0


def test_detached_passive_without_dependency_does_not_follow_provider() -> None:
    context = make_context()
    runtime = register_runtime(context, skill_type=SkillType.PASSIVE, skill_id="detached-passive")
    systems = BattleSystems()
    apply_capture(systems, context, owner="a")
    detached = apply_state(
        systems, context, OfficialStateId.PROVOKE.value, owner="c", source="a",
        source_skill_id=runtime.definition.skill_id, source_skill_slot=SkillSlot.INHERENT,
    ).instance
    assert detached is not None
    assert systems.dependency_evaluation_support.prerequisites(StateNode(detached.instance_id)) == ()
    assert systems.state_effectiveness_policy.evaluate_state(context, detached).effective


def test_explicit_provider_dependency_does_follow_provider() -> None:
    context = make_context()
    runtime = register_runtime(context, skill_type=SkillType.PASSIVE, skill_id="dependent-passive")
    systems = BattleSystems()
    apply_capture(systems, context, owner="a", lifetime=StateLifetimeSpec.holder_action_window(1))
    dependent = apply_state(
        systems, context, OfficialStateId.PROVOKE.value, owner="c", source="a",
        dependencies=(ProviderDependency(provider_ref(runtime), "audit-explicit"),),
    ).instance
    assert dependent is not None
    assert systems.state_effectiveness_policy.evaluate_state(context, dependent).status is StateEffectivenessStatus.SUPPRESSED
    expire_holder_action_window(systems, context, "a")
    assert systems.state_effectiveness_policy.evaluate_state(context, dependent).effective


def test_capture_false_report_suppression_causes_compose() -> None:
    context = make_context()
    runtime = register_runtime(context, skill_type=SkillType.PASSIVE, skill_id="compose-passive")
    systems = BattleSystems()
    apply_state(systems, context, OfficialStateId.FALSE_REPORT.value, owner="a")
    apply_capture(systems, context, owner="a", lifetime=StateLifetimeSpec.holder_action_window(1))
    both = systems.provider_validity_policy.evaluate_provider(context, provider_ref(runtime))
    ids = {c.rule_id for c in both.suppression_causes}
    assert {CAPTURE_PROVIDER_SUPPRESSION_RULE_ID, FALSE_REPORT_PROVIDER_SUPPRESSION_RULE_ID} <= ids
    expire_holder_action_window(systems, context, "a")
    after = systems.provider_validity_policy.evaluate_provider(context, provider_ref(runtime))
    assert after.status is ProviderValidityStatus.SUPPRESSED
    assert all(c.rule_id != CAPTURE_PROVIDER_SUPPRESSION_RULE_ID for c in after.suppression_causes)


def test_capture_intimidation_suppression_causes_compose() -> None:
    context = make_intimidation_context()
    runtime = intimidation_skill(context, skill_id="capture-intimidation-passive", skill_type=SkillType.PASSIVE)
    systems = BattleSystems()
    intimidation = apply_intimidation(systems, context)
    assert intimidation.instance is not None
    capture = apply_capture(systems, context, owner="a", source="b")
    assert capture.instance is not None
    both = systems.provider_validity_policy.evaluate_provider(context, intimidation_provider_ref(runtime))
    ids = {c.rule_id for c in both.suppression_causes}
    assert {CAPTURE_PROVIDER_SUPPRESSION_RULE_ID, INTIMIDATION_PROVIDER_SUPPRESSION_RULE_ID} <= ids
    systems.state_removal_coordinator.remove(context, operation=RemovalOperation.NATURAL_EXPIRY, instance_id=capture.instance.instance_id)
    after = systems.provider_validity_policy.evaluate_provider(context, intimidation_provider_ref(runtime))
    assert after.status is ProviderValidityStatus.SUPPRESSED
    assert any(c.rule_id == INTIMIDATION_PROVIDER_SUPPRESSION_RULE_ID for c in after.suppression_causes)


def test_capture_received_recovery_zero_via_real_recovery_system() -> None:
    context, systems = make_context(), BattleSystems()
    context.get_unit("a").troops = 4000
    apply_capture(systems, context, owner="a")
    result = systems.recovery_system.resolve(context, RecoveryRequest("b", "a", 500))
    assert isinstance(result, RecoveryPreventedResult)
    assert result.reason_key == CAPTURE_RECOVERY_PREVENTION_RULE_ID
    assert context.get_unit("a").troops == 4000


def test_capture_self_recovery_target_remains_targetable() -> None:
    context = make_context()
    runtime = register_runtime(context, owner="a", target_mode=SkillTargetMode.SELF, skill_id="self-recovery-target")
    systems = BattleSystems()
    apply_capture(systems, context, owner="a")
    selection = systems.skill_resolver.resolve(context, runtime)
    context.get_unit("a").troops = 4000
    recovery = systems.recovery_system.resolve(context, RecoveryRequest("a", "a", 300))
    assert selection.status is SkillResolutionStatus.RESOLVED and selection.target_ids == ("a",)
    assert isinstance(recovery, RecoveryPreventedResult)


def test_capture_healing_block_composition() -> None:
    context, systems = make_context(), BattleSystems()
    context.get_unit("a").troops = 4000
    apply_capture(systems, context, owner="a")
    apply_state(systems, context, OfficialStateId.HEALING_BAN.value, owner="a", runtime_params=Stage11TimedFlagParams())
    result = systems.recovery_system.resolve(context, RecoveryRequest("b", "a", 500))
    assert isinstance(result, RecoveryPreventedResult)
    assert CAPTURE_RECOVERY_PREVENTION_RULE_ID in result.internal_reason_keys
    assert "HEALING_BAN" in result.internal_reason_keys


def _target_spy(monkeypatch, mode: SkillTargetMode):
    rng = CountingRandomSystem(110020)
    context = make_context(rng)
    runtime = register_runtime(context, owner="a", target_mode=mode, target_count=1 if "CHOOSE_N" in mode.value else None, skill_id=f"target-{mode.value}")
    systems = BattleSystems()
    apply_capture(systems, context, owner="x", source="b")
    seen = []
    original = systems.target_system.random_units
    def spy(ctx, candidates, *, count):
        seen.append(tuple(x.unit_id for x in candidates))
        return original(ctx, candidates, count=count)
    monkeypatch.setattr(systems.target_system, "random_units", spy)
    result = systems.skill_resolver.resolve(context, runtime)
    return rng, seen, result


def test_capture_friendly_single_filters_before_rng(monkeypatch) -> None:
    rng, seen, result = _target_spy(monkeypatch, SkillTargetMode.SINGLE_RANDOM_ALLY)
    assert result.target_ids == ("y",) and seen == [("y",)] and rng.sample_calls == 0


def test_capture_friendly_choose_n_filters_before_rng(monkeypatch) -> None:
    rng, seen, result = _target_spy(monkeypatch, SkillTargetMode.CHOOSE_N_RANDOM_ALLIES)
    assert result.target_ids == ("y",) and seen == [("y",)] and rng.sample_calls == 0


def test_capture_all_allies_remains_unsupported() -> None:
    context = make_context()
    runtime = register_runtime(context, owner="a", target_mode=SkillTargetMode.FIXED_ALL_ALLIES, skill_id="all-allies")
    systems = BattleSystems()
    apply_capture(systems, context, owner="x", source="b")
    with pytest.raises(ValueError, match="unsupported Skill target-policy boundary"):
        systems.skill_resolver.resolve(context, runtime)


def _resolved_target(context):
    return TargetSelectionResult(
        operation_id=context.id_allocator.allocate_target_operation_id(),
        target_ids=("x",),
        provenance=TargetSelectionProvenance.FRESH_SELECTED,
    )


def test_capture_locked_target_not_requeried() -> None:
    context, systems = make_context(), BattleSystems()
    apply_capture(systems, context, owner="x", source="b")
    previous = _resolved_target(context)
    locked = TargetOperationProducer.continue_from(previous, TargetQueryMode.LOCK_RESOLVED)
    assert locked.target_ids == ("x",) and locked.operation_id == previous.operation_id


def test_capture_delayed_friendly_work_boundary_preserved() -> None:
    context, systems = make_context(), BattleSystems()
    apply_capture(systems, context, owner="x", source="b")
    previous = _resolved_target(context)
    inherited = TargetOperationProducer.continue_from(previous, TargetQueryMode.INHERIT_RESOLVED)
    assert inherited.target_ids == ("x",) and inherited.operation_id == previous.operation_id


def test_capture_equipment_attribute_suppressed() -> None:
    context, systems = make_context(), BattleSystems()
    provider, ref = register_equipment_attribute(systems, owner="a", amount=50)
    record = systems.equipment_contribution_registry.resolve_provider(context, provider)
    base = context.get_unit("a").attack
    apply_capture(systems, context, owner="a", lifetime=StateLifetimeSpec.holder_action_window(1))
    decision = systems.equipment_effectiveness_policy.evaluate_contribution(context, ref)
    assert decision.status is EquipmentEffectivenessStatus.SUPPRESSED
    assert any(c.rule_id == CAPTURE_EQUIPMENT_ATTRIBUTE_RULE_ID for c in decision.suppression_causes)
    assert systems.attribute_system.get_attack(context, context.get_unit("a")) == base
    assert systems.equipment_contribution_registry.resolve_provider(context, provider) is record
    expire_holder_action_window(systems, context, "a")
    assert systems.attribute_system.get_attack(context, context.get_unit("a")) == base + 50


def test_capture_equipment_non_attribute_not_generalized() -> None:
    for kind in (
        EquipmentContributionKind.DAMAGE_MODIFIER,
        EquipmentContributionKind.RECOVERY_MODIFIER,
        EquipmentContributionKind.TRIGGER,
        EquipmentContributionKind.SCHEDULED_TRIGGER,
        EquipmentContributionKind.LIVE_EFFECT,
    ):
        context, systems = make_context(), BattleSystems()
        provider = EquipmentProviderRef("a", f"audit:{kind.value}")
        systems.equipment_contribution_registry.register_provider(provider)
        ref = EquipmentContributionRef(provider, "audit", kind)
        systems.equipment_contribution_registry.register_contribution(ref)
        apply_capture(systems, context, owner="a")
        assert systems.equipment_effectiveness_policy.evaluate_contribution(context, ref).status is EquipmentEffectivenessStatus.UNSUPPORTED_BOUNDARY


def test_capture_and_sabotage_equipment_scopes_remain_distinct() -> None:
    def trigger_decision(state_id: str):
        context, systems = make_context(), BattleSystems()
        provider = EquipmentProviderRef("a", "audit:trigger")
        systems.equipment_contribution_registry.register_provider(provider)
        ref = EquipmentContributionRef(provider, "audit:trigger", EquipmentContributionKind.TRIGGER)
        systems.equipment_contribution_registry.register_contribution(ref)
        apply_state(systems, context, state_id, owner="a")
        return systems.equipment_effectiveness_policy.evaluate_contribution(context, ref)
    assert trigger_decision(OfficialStateId.CAPTURE.value).status is EquipmentEffectivenessStatus.UNSUPPORTED_BOUNDARY
    assert trigger_decision(OfficialStateId.EQUIPMENT_DISABLE.value).status is EquipmentEffectivenessStatus.SUPPRESSED


def test_insight_does_not_reject_capture() -> None:
    context, systems = make_context(), BattleSystems()
    apply_state(systems, context, OfficialStateId.INSIGHT.value, owner="a")
    assert apply_capture(systems, context, owner="a").status is StateApplicationResultStatus.APPLIED


def test_ordinary_cleanse_does_not_remove_capture() -> None:
    context, systems = make_context(), BattleSystems()
    capture = apply_capture(systems, context, owner="a").instance
    assert capture is not None
    result = systems.state_removal_coordinator.remove(context, operation=RemovalOperation.ORDINARY_CLEANSE, instance_id=capture.instance_id)
    assert result.status is StateRemovalResultStatus.REJECTED
    assert context.states.has_instance(capture.instance_id)


def test_source_death_does_not_remove_capture() -> None:
    context, systems = make_context(), BattleSystems()
    capture = apply_capture(systems, context, owner="a", source="b").instance
    assert capture is not None
    context.get_unit("b").troops = 0
    systems.defeat_cleanup_port.commit_defeat(context, "b")
    assert context.states.has_instance(capture.instance_id)
    assert systems.state_effectiveness_policy.evaluate_state(context, capture).effective


def test_capture_reapplication_remains_unsupported() -> None:
    context, systems = make_context(), BattleSystems()
    first = apply_capture(systems, context, owner="a", source="b").instance
    assert first is not None
    second = apply_capture(systems, context, owner="a", source="c")
    assert second.status is StateApplicationResultStatus.UNSUPPORTED_BOUNDARY
    assert context.states.has_instance(first.instance_id)
    assert str(context.generation_allocator.allocate()) == "gen_2"


def test_capture_restoration_is_future_only() -> None:
    rng = CountingRandomSystem(110040, chance_result=True)
    context = make_context(rng)
    runtime = register_runtime(context, skill_type=SkillType.PASSIVE, skill_id="future-only", activation_rate=0.5)
    systems = BattleSystems()
    apply_capture(systems, context, owner="a", lifetime=StateLifetimeSpec.holder_action_window(1))
    assert systems.skill_resolver.resolve(context, runtime).status is SkillResolutionStatus.DISABLED
    assert rng.chance_calls == 0
    expire_holder_action_window(systems, context, "a")
    assert rng.chance_calls == 0
    systems.skill_resolver.resolve(context, runtime)
    assert rng.chance_calls == 1


def test_capture_canonical_wiring_and_static_architecture() -> None:
    systems = BattleSystems()
    source = inspect.getsource(capture_module)
    assert systems.action_system._current_actor_permission_policy is systems.current_actor_permission_policy
    assert systems.damage_instance_coordinator.execution_right_port is systems.damage_execution_right_port
    assert systems.recovery_system.execution_prevention_policy is systems.recovery_execution_prevention_policy
    assert systems.skill_resolver._target_policy is systems.skill_target_policy
    assert systems.state_application_coordinator._lifecycle is systems.state_lifecycle_system
    assert systems.state_removal_coordinator._policy is systems.state_removal_policy
    for forbidden in (
        "CaptureRuntime", "CaptureManager", "CaptureEngine", "import random",
        "context.random", "event_bus.publish", ".enabled =", "unregister",
        "20228", "暗箭难防", "TargetQueryMode", "LOCK_RESOLVED", "INHERIT_RESOLVED",
    ):
        assert forbidden not in source


def test_capture_execution_right_dimensions_are_specific() -> None:
    systems = BattleSystems()
    active = systems.damage_instance_coordinator._damage_effect_execution_work(active_damage_effect())
    dot = systems.damage_instance_coordinator._damage_effect_execution_work(periodic_damage_effect())
    assert active.work_kind is DamageWorkKind.NEW_ACTOR_DRIVEN_DAMAGE
    assert active.spec.actor_permission is ExecutionRightMode.RECHECK_AT_EXECUTION
    assert active.spec.provider_validity is ExecutionRightMode.NOT_APPLICABLE
    assert active.spec.target_eligibility is ExecutionRightMode.NOT_APPLICABLE
    assert dot.work_kind is DamageWorkKind.ATTACHED_EXISTING_DOT
    assert dot.spec.actor_permission is ExecutionRightMode.NOT_APPLICABLE


def test_capture_provider_scope_negative() -> None:
    for skill_type in (SkillType.ACTIVE, SkillType.ASSAULT, SkillType.TROOP, SkillType.FORMATION, SkillType.TALENT):
        context = make_context()
        runtime = register_runtime(context, skill_type=skill_type, skill_id=f"negative-{skill_type.value}")
        systems = BattleSystems()
        apply_capture(systems, context, owner="a")
        assert systems.provider_validity_policy.evaluate_provider(context, provider_ref(runtime)).status is ProviderValidityStatus.VALID
