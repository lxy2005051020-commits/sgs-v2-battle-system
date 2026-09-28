from __future__ import annotations

import inspect

import pytest

from sgs_v2.battle_core import (
    BattleContext, BattlePhase, BattleSystems, DamageSkillEffectSpec, DamageType,
    EmptyStateRuntimeParams, EquipmentContributionKind, EquipmentContributionRef,
    EquipmentEffectivenessStatus, EquipmentProviderRef, EventBus, EventType,
    LineupPosition, OfficialStateId, PreparationMode, ProviderDependency,
    ProviderNode, ProviderValidityStatus, RandomSystem, SkillDefinition,
    SkillOperationAdmissionRequest, SkillOperationAdmissionStatus,
    SkillOperationKind, SkillProviderRef, SkillResolutionStatus, SkillRuntime,
    SkillSlot, SkillTargetMode, SkillType, StateLifetimeSpec, StateNode,
    UnitRuntime, register_official_state_definitions,
)
from sgs_v2.battle_core import false_report_integration as fr_module
from sgs_v2.battle_core.false_report_integration import (
    FALSE_REPORT_EQUAL_REAPPLICATION_RULE_ID,
    FALSE_REPORT_PROVIDER_SUPPRESSION_RULE_ID,
)
from sgs_v2.battle_core.state_application import (
    AdmissionDecision, AdmissionStatus, StateApplicationResultStatus, StateCandidate,
)
from sgs_v2.battle_core.state_effectiveness import (
    LocalRuleCauseRef, StateEffectivenessContribution, StateEffectivenessStatus,
    SuppressionCause,
)
from sgs_v2.battle_core.state_removal import RemovalOperation, StateRemovalResultStatus


class CountingRandomSystem(RandomSystem):
    def __init__(self, seed: int = 690107, chance_result: bool | None = None) -> None:
        super().__init__(seed)
        self.chance_result = chance_result
        self.chance_calls = 0
        self.sample_calls = 0

    def chance(self, probability: float) -> bool:
        self.chance_calls += 1
        return self.chance_result if self.chance_result is not None else super().chance(probability)

    def sample(self, values, k):  # type: ignore[no-untyped-def]
        self.sample_calls += 1
        return super().sample(values, k)


def make_context(random_system: RandomSystem | None = None) -> BattleContext:
    context = BattleContext(
        battle_id="stage12-690107",
        units={
            "a": UnitRuntime("a", "A", "A", 1000, 1000, 300, 100, 100, lineup_position=LineupPosition.COMMANDER),
            "b": UnitRuntime("b", "B", "B", 1000, 1000, 100, 100, 90, lineup_position=LineupPosition.COMMANDER),
            "c": UnitRuntime("c", "C", "B", 1000, 1000, 100, 100, 80, lineup_position=LineupPosition.DEPUTY_1),
        },
        event_bus=EventBus(), random=random_system or RandomSystem(690107),
    )
    register_official_state_definitions(context.states)
    context.current_round = 1
    context.current_phase = BattlePhase.UNIT_ACTION.value
    return context


def runtime(*, owner="a", slot=SkillSlot.INHERENT, skill_id="fr-provider",
            skill_type=SkillType.PASSIVE, preparation=PreparationMode.NONE,
            enabled=True, rate=0.5) -> SkillRuntime:
    return SkillRuntime(
        definition=SkillDefinition(
            skill_id=skill_id, name=skill_id, activation_rate=rate,
            target_mode=SkillTargetMode.SINGLE_RANDOM_ENEMY,
            effect_specs=(DamageSkillEffectSpec(DamageType.WEAPON),),
            skill_type=skill_type, preparation_mode=preparation,
        ),
        owner_id=owner, skill_slot=slot, enabled=enabled,
    )


def register_runtime(context: BattleContext, **kwargs) -> SkillRuntime:
    item = runtime(**kwargs)
    context.skill_runtimes.register(item)
    return item


def pref(item: SkillRuntime) -> SkillProviderRef:
    assert item.skill_slot is not None
    return SkillProviderRef(item.owner_id, item.skill_slot, item.definition.skill_id)


def candidate(state_id: str, *, owner="a", source="b", source_skill_id=None,
              source_skill_slot=None, lifetime=None, strength=None, dependencies=()) -> StateCandidate:
    return StateCandidate(
        state_id=state_id, owner_id=owner, source_id=source,
        source_skill_id=source_skill_id, source_skill_slot=source_skill_slot,
        runtime_params_candidate=EmptyStateRuntimeParams(), lifetime_spec=lifetime,
        strength=strength, provider_dependencies=tuple(dependencies),
        application_provenance="stage12-690107-test",
    )


def apply_fr(systems: BattleSystems, context: BattleContext, *, owner="a", source="b",
             lifetime=None, strength=None):
    return systems.state_application_coordinator.apply_candidate(
        context, candidate(
            OfficialStateId.FALSE_REPORT.value, owner=owner, source=source,
            source_skill_id="false-report-source", source_skill_slot=SkillSlot.LEARNED_1,
            lifetime=lifetime, strength=strength,
        )
    )


def admit(systems: BattleSystems, context: BattleContext, item: SkillRuntime,
          operation=SkillOperationKind.NEW_ADMISSION):
    return systems.skill_operation_admission_coordinator.evaluate(
        context,
        SkillOperationAdmissionRequest(
            actor_id=item.owner_id, provider_ref=pref(item),
            skill_type=item.definition.skill_type,
            preparation_mode=item.definition.preparation_mode,
            operation_kind=operation,
        ),
    )


def remove_fr(systems: BattleSystems, context: BattleContext, instance_id: str,
              operation=RemovalOperation.ORDINARY_CLEANSE):
    return systems.state_removal_coordinator.remove(
        context, operation=operation, instance_id=instance_id,
    )


def register_equipment(systems: BattleSystems, key: str, kind=EquipmentContributionKind.LIVE_EFFECT):
    provider = EquipmentProviderRef("a", key)
    systems.equipment_contribution_registry.register_provider(provider)
    ref = EquipmentContributionRef(provider, key, kind)
    systems.equipment_contribution_registry.register_contribution(ref)
    return ref


def test_false_report_application_and_effective_truth() -> None:
    context, systems = make_context(), BattleSystems()
    result = apply_fr(systems, context)
    assert result.status is StateApplicationResultStatus.APPLIED
    assert result.instance is not None
    assert systems.state_effectiveness_policy.evaluate_state(context, result.instance).effective


def test_false_report_zero_rng() -> None:
    rng = CountingRandomSystem()
    context, systems = make_context(rng), BattleSystems()
    apply_fr(systems, context)
    assert (rng.chance_calls, rng.sample_calls) == (0, 0)


@pytest.mark.parametrize(
    "skill_type, expected",
    [
        (SkillType.PASSIVE, ProviderValidityStatus.SUPPRESSED),
        (SkillType.COMMAND, ProviderValidityStatus.SUPPRESSED),
        (SkillType.ACTIVE, ProviderValidityStatus.VALID),
        (SkillType.ASSAULT, ProviderValidityStatus.VALID),
        (SkillType.TROOP, ProviderValidityStatus.VALID),
        (SkillType.FORMATION, ProviderValidityStatus.VALID),
    ],
)
def test_false_report_provider_scope(skill_type, expected) -> None:
    context = make_context()
    item = register_runtime(context, skill_type=skill_type)
    systems = BattleSystems()
    apply_fr(systems, context)
    assert systems.provider_validity_policy.evaluate_provider(context, pref(item)).status is expected


def test_false_report_ownership_and_identity_preserved() -> None:
    context = make_context()
    target = register_runtime(context, skill_type=SkillType.PASSIVE)
    other = register_runtime(context, owner="b", skill_id="other", skill_type=SkillType.PASSIVE)
    systems = BattleSystems()
    apply_fr(systems, context)
    assert systems.provider_validity_policy.evaluate_provider(context, pref(target)).status is ProviderValidityStatus.SUPPRESSED
    assert systems.provider_validity_policy.evaluate_provider(context, pref(other)).status is ProviderValidityStatus.VALID
    assert target.enabled is True
    assert context.skill_runtimes.resolve_provider(pref(target)).runtime is target


def test_normal_attack_under_fr() -> None:
    context, systems = make_context(), BattleSystems()
    apply_fr(systems, context)
    before = sum(e.event_type is EventType.NORMAL_ATTACK for e in context.event_bus.history)
    systems.normal_attack_system.execute(context, context.get_unit("a"))
    assert sum(e.event_type is EventType.NORMAL_ATTACK for e in context.event_bus.history) == before + 1


def test_prep_active_and_assault_admission_under_fr() -> None:
    context = make_context()
    active = register_runtime(context, skill_type=SkillType.ACTIVE, preparation=PreparationMode.REQUIRED)
    assault = register_runtime(context, slot=SkillSlot.LEARNED_1, skill_id="assault", skill_type=SkillType.ASSAULT)
    systems = BattleSystems()
    apply_fr(systems, context)
    assert admit(systems, context, active).status is SkillOperationAdmissionStatus.ALLOW
    assert admit(systems, context, active, SkillOperationKind.CONTINUATION).status is SkillOperationAdmissionStatus.ALLOW
    assert admit(systems, context, assault).status is SkillOperationAdmissionStatus.ALLOW


def test_expiry_restores_provider_future_only() -> None:
    rng = CountingRandomSystem(chance_result=True)
    context = make_context(rng)
    item = register_runtime(context, skill_type=SkillType.PASSIVE)
    systems = BattleSystems()
    fr = apply_fr(systems, context, lifetime=StateLifetimeSpec.holder_action_window(1)).instance
    assert fr is not None
    assert systems.skill_resolver.resolve(context, item).status is SkillResolutionStatus.DISABLED
    assert rng.chance_calls == 0
    due = systems.state_lifecycle_system.due_at_action_start(context, "a")
    before = systems.effectiveness_transition_coordinator.capture(context, tuple(StateNode(x.instance_id) for x in due))
    removed = systems.state_lifecycle_system.settle_action_start_lifetimes(context, "a")
    systems.effectiveness_transition_coordinator.complete_removed_nodes(context, before, tuple(StateNode(x.instance_id) for x in removed))
    assert systems.provider_validity_policy.evaluate_provider(context, pref(item)).status is ProviderValidityStatus.VALID
    assert rng.chance_calls == 0


def test_cleanse_immediate_resume_and_unknown_cleanse_boundary() -> None:
    context = make_context()
    item = register_runtime(context, skill_type=SkillType.COMMAND)
    systems = BattleSystems()
    fr = apply_fr(systems, context).instance
    assert fr is not None
    blocked = remove_fr(systems, context, fr.instance_id, RemovalOperation.SPECIALIZED_CLEANSE)
    assert blocked.status is StateRemovalResultStatus.UNSUPPORTED_BOUNDARY
    assert systems.provider_validity_policy.evaluate_provider(context, pref(item)).status is ProviderValidityStatus.SUPPRESSED
    removed = remove_fr(systems, context, fr.instance_id)
    assert removed.status is StateRemovalResultStatus.REMOVED
    assert systems.provider_validity_policy.evaluate_provider(context, pref(item)).status is ProviderValidityStatus.VALID


def test_insight_does_not_reject_or_suppress_false_report() -> None:
    context, systems = make_context(), BattleSystems()
    systems.state_application_coordinator.apply_candidate(context, candidate(OfficialStateId.INSIGHT.value))
    fr = apply_fr(systems, context).instance
    assert fr is not None
    assert systems.state_effectiveness_policy.evaluate_state(context, fr).effective


def test_provider_invalid_precedes_exhaustion_permission() -> None:
    context = make_context()
    passive = register_runtime(context, skill_type=SkillType.PASSIVE)
    active = register_runtime(context, slot=SkillSlot.LEARNED_1, skill_id="active", skill_type=SkillType.ACTIVE)
    systems = BattleSystems()
    apply_fr(systems, context)
    systems.state_application_coordinator.apply_candidate(context, candidate(OfficialStateId.SILENCE.value))
    p = admit(systems, context, passive)
    assert p.status is SkillOperationAdmissionStatus.DENY_PROVIDER_INVALID and p.permission_decision is None
    assert admit(systems, context, active).status is SkillOperationAdmissionStatus.DENY_PERMISSION


def test_equal_reapplication_rejected_no_refresh() -> None:
    context, systems = make_context(), BattleSystems()
    first = apply_fr(systems, context).instance
    assert first is not None
    generation = first.current_generation_id
    second = apply_fr(systems, context, source="c")
    assert second.status is StateApplicationResultStatus.REJECTED_CONFLICT
    assert second.reason_rule_id == FALSE_REPORT_EQUAL_REAPPLICATION_RULE_ID
    assert context.states.get(first.instance_id).current_generation_id == generation


def test_explicit_strength_boundary() -> None:
    context, systems = make_context(), BattleSystems()
    assert apply_fr(systems, context, strength=2.0).status is StateApplicationResultStatus.UNSUPPORTED_BOUNDARY


def test_source_death_does_not_remove_false_report_but_holder_death_does() -> None:
    context, systems = make_context(), BattleSystems()
    fr = apply_fr(systems, context, source="b").instance
    assert fr is not None
    context.get_unit("b").troops = 0
    systems.defeat_cleanup_port.commit_defeat(context, "b")
    assert context.states.has_instance(fr.instance_id)
    context.get_unit("a").troops = 0
    systems.defeat_cleanup_port.commit_defeat(context, "a")
    assert not context.states.has_instance(fr.instance_id)


def test_explicit_provider_dependency_pair_and_restore() -> None:
    context = make_context()
    source_provider = register_runtime(context, skill_type=SkillType.COMMAND)
    systems = BattleSystems()
    fr = apply_fr(systems, context).instance
    assert fr is not None
    dep = systems.state_application_coordinator.apply_candidate(
        context,
        candidate(
            OfficialStateId.PROVOKE.value, owner="c", source="a",
            dependencies=(ProviderDependency(pref(source_provider), "PAIR"),),
        ),
    ).instance
    assert dep is not None
    assert systems.state_effectiveness_policy.evaluate_state(context, dep).status is StateEffectivenessStatus.SUPPRESSED
    remove_fr(systems, context, fr.instance_id)
    assert systems.state_effectiveness_policy.evaluate_state(context, dep).effective


def test_attribution_is_not_provider_dependency() -> None:
    context = make_context()
    source_provider = register_runtime(context, skill_type=SkillType.COMMAND)
    systems = BattleSystems()
    apply_fr(systems, context)
    dep = systems.state_application_coordinator.apply_candidate(
        context,
        candidate(
            OfficialStateId.PROVOKE.value, owner="c", source="a",
            source_skill_id=source_provider.definition.skill_id,
            source_skill_slot=SkillSlot.INHERENT,
        ),
    ).instance
    assert dep is not None
    assert systems.dependency_evaluation_support.prerequisites(StateNode(dep.instance_id)) == ()
    assert systems.state_effectiveness_policy.evaluate_state(context, dep).effective


@pytest.mark.parametrize("key", ["踩踏", "刚毅", "天公", "妖气", "忍让", "躲闪", "祝福", "忠诚", "集智", "周旋"])
def test_tested_equipment_special_scope(key: str) -> None:
    context, systems = make_context(), BattleSystems()
    ref = register_equipment(systems, key)
    apply_fr(systems, context)
    assert systems.equipment_effectiveness_policy.evaluate_contribution(context, ref).status is EquipmentEffectivenessStatus.SUPPRESSED


@pytest.mark.parametrize("key", ["灵动", "援助", "无双", "雄烈"])
def test_bounded_equipment_special_scope(key: str) -> None:
    context, systems = make_context(), BattleSystems()
    ref = register_equipment(systems, key)
    apply_fr(systems, context)
    assert systems.equipment_effectiveness_policy.evaluate_contribution(context, ref).status is EquipmentEffectivenessStatus.UNSUPPORTED_BOUNDARY


def test_ordinary_equipment_attribute_not_generalized() -> None:
    context, systems = make_context(), BattleSystems()
    ref = register_equipment(systems, "ordinary-armor", EquipmentContributionKind.ATTRIBUTE)
    apply_fr(systems, context)
    assert systems.equipment_effectiveness_policy.evaluate_contribution(context, ref).status is EquipmentEffectivenessStatus.EFFECTIVE


def test_self_suppression_and_multiple_causes_restore_correctly() -> None:
    context = make_context()
    item = register_runtime(context, skill_type=SkillType.PASSIVE)
    systems = BattleSystems()
    fr = apply_fr(systems, context).instance
    assert fr is not None
    context.metadata["causes"] = {"A", "B"}

    def adapter(ctx, inst, _session):
        if inst.instance_id != fr.instance_id:
            return StateEffectivenessContribution()
        return StateEffectivenessContribution(
            suppression_causes=tuple(
                SuppressionCause(f"TEST_{k}", LocalRuleCauseRef(k))
                for k in sorted(ctx.metadata["causes"])
            )
        )

    systems.state_effectiveness_policy.register_rule_adapter(adapter)
    assert systems.provider_validity_policy.evaluate_provider(context, pref(item)).status is ProviderValidityStatus.VALID
    context.metadata["causes"] = {"B"}
    assert systems.provider_validity_policy.evaluate_provider(context, pref(item)).status is ProviderValidityStatus.VALID
    context.metadata["causes"] = set()
    assert systems.provider_validity_policy.evaluate_provider(context, pref(item)).status is ProviderValidityStatus.SUPPRESSED


def test_baseline_precedence_and_query_zero_event() -> None:
    context = make_context()
    item = register_runtime(context, skill_type=SkillType.PASSIVE, enabled=False)
    systems = BattleSystems()
    apply_fr(systems, context)
    before = context.event_bus.history
    decision = systems.provider_validity_policy.evaluate_provider(context, pref(item))
    assert decision.status is ProviderValidityStatus.BASELINE_DISABLED
    assert decision.suppression_causes == ()
    assert context.event_bus.history == before


def test_provider_dependency_graph_and_static_architecture_guards() -> None:
    context = make_context()
    item = register_runtime(context, skill_type=SkillType.PASSIVE)
    systems = BattleSystems()
    fr = apply_fr(systems, context).instance
    assert fr is not None
    assert systems.dependency_evaluation_support.prerequisites(ProviderNode(pref(item))) == (StateNode(fr.instance_id),)
    source = inspect.getsource(fr_module)
    assert ".enabled =" not in source
    assert "context.random" not in source and "import random" not in source
    assert "ActionSystem" not in source and "NormalAttackSystem" not in source
    assert "EffectSourceRef" not in source
    assert "FalseReportRuntime" not in source
    assert FALSE_REPORT_PROVIDER_SUPPRESSION_RULE_ID in source


def _special_protection(rule_id: str):
    def adapter(_context, incoming: StateCandidate):
        if incoming.state_id == OfficialStateId.FALSE_REPORT.value:
            return AdmissionDecision(AdmissionStatus.REJECT_SPECIAL_PROTECTION, rule_id)
        return None
    return adapter


@pytest.mark.parametrize("rule_id", ["TEST_YIYIDAILAO", "TEST_GANGYI_SUCCESS"])
def test_special_protection_seam_can_reject_false_report(rule_id: str) -> None:
    context, systems = make_context(), BattleSystems()
    systems.state_admission_policy.register_rule_adapter(_special_protection(rule_id))
    assert apply_fr(systems, context).status is StateApplicationResultStatus.REJECTED_ADMISSION
