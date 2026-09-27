from __future__ import annotations

import ast
from pathlib import Path

import pytest

from sgs_v2.battle_core import (
    BattleContext,
    BattleSystems,
    ContinuousDamageStateParams,
    DamageSkillEffectSpec,
    DamageType,
    DependencyCycleError,
    DependencyEvaluationSupport,
    EmptyStateRuntimeParams,
    EquipmentProviderRef,
    EventBus,
    FrozenContinuousDamageBasis,
    InactivityCause,
    LineupPosition,
    LocalRuleCauseRef,
    PersistentSourceSkillGate,
    ProviderResolutionStatus,
    ProviderValidityPolicy,
    ProviderValidityStatus,
    RandomSystem,
    RecoveryModelKind,
    RecoveryOpportunity,
    RecoveryOpportunityKind,
    RecoveryPotencyContext,
    RuleIntentExecutionDescriptor,
    RuleIntentKind,
    SkillDefinition,
    SkillProviderRef,
    SkillRuntime,
    SkillRuntimeRegistry,
    SkillSlot,
    SkillTargetMode,
    SourceType,
    StateApplicationGenerationId,
    StateDefinition,
    StateEffectivenessContribution,
    StateEffectivenessPolicy,
    StateEffectivenessStatus,
    StateInstance,
    StateNode,
    SuppressionCause,
    TriggerSystem,
    UnitRuntime,
)
from sgs_v2.battle_core.effects import EffectSourceRef


def make_context(seed: int = 123) -> BattleContext:
    return BattleContext(
        battle_id=f"stage12-foundation-{seed}",
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


def make_skill_runtime(
    *,
    owner_id: str = "a",
    slot: SkillSlot = SkillSlot.LEARNED_1,
    skill_id: str = "skill-x",
    enabled: bool = True,
) -> SkillRuntime:
    definition = SkillDefinition(
        skill_id=skill_id,
        name=skill_id,
        activation_rate=1.0,
        target_mode=SkillTargetMode.SINGLE_RANDOM_ENEMY,
        effect_specs=(
            DamageSkillEffectSpec(
                damage_type=DamageType.WEAPON,
                coefficient=1.0,
            ),
        ),
    )
    return SkillRuntime(
        definition=definition,
        owner_id=owner_id,
        skill_slot=slot,
        enabled=enabled,
    )


def make_foundation():
    dependencies = DependencyEvaluationSupport()
    state_policy = StateEffectivenessPolicy(dependencies)
    provider_policy = ProviderValidityPolicy(dependencies)
    dependencies.bind_evaluators(
        state_evaluator=state_policy.evaluate_node,
        provider_evaluator=provider_policy.evaluate_node,
    )
    return dependencies, state_policy, provider_policy


def add_simple_state(context: BattleContext, instance_id: str = "state-x") -> StateInstance:
    context.states.register_definition(
        StateDefinition(
            state_id="synthetic",
            name="Synthetic",
            runtime_params_type=EmptyStateRuntimeParams,
        )
    )
    instance = StateInstance(
        instance_id=instance_id,
        state_id="synthetic",
        owner_id="a",
        source_id=None,
        source_skill_id=None,
        applied_round=1,
        applied_phase="ACTION_ORDER",
    )
    context.states.add(instance)
    return instance


def test_skill_provider_ref_same_fields_equal() -> None:
    left = SkillProviderRef("a", SkillSlot.INHERENT, "skill-x")
    right = SkillProviderRef("a", SkillSlot.INHERENT, "skill-x")
    assert left == right
    assert hash(left) == hash(right)


def test_same_skill_different_owner_not_equal() -> None:
    assert SkillProviderRef("a", SkillSlot.INHERENT, "x") != SkillProviderRef(
        "b", SkillSlot.INHERENT, "x"
    )


def test_same_owner_different_slot_not_equal() -> None:
    assert SkillProviderRef("a", SkillSlot.INHERENT, "x") != SkillProviderRef(
        "a", SkillSlot.LEARNED_1, "x"
    )


def test_same_owner_slot_different_skill_not_equal() -> None:
    assert SkillProviderRef("a", SkillSlot.INHERENT, "x") != SkillProviderRef(
        "a", SkillSlot.INHERENT, "y"
    )


def test_inherent_slot_zero_is_valid_identity() -> None:
    ref = SkillProviderRef("a", SkillSlot.INHERENT, "x")
    assert int(ref.skill_slot) == 0


def test_equipment_provider_not_skill_provider() -> None:
    equipment = EquipmentProviderRef("a", "weapon:trait")
    assert not isinstance(equipment, SkillProviderRef)


def test_provider_lookup_found() -> None:
    registry = SkillRuntimeRegistry()
    runtime = make_skill_runtime()
    registry.register(runtime)
    decision = registry.resolve_provider(
        SkillProviderRef("a", SkillSlot.LEARNED_1, "skill-x")
    )
    assert decision.status is ProviderResolutionStatus.FOUND
    assert decision.runtime is runtime


def test_provider_lookup_missing() -> None:
    registry = SkillRuntimeRegistry()
    decision = registry.resolve_provider(
        SkillProviderRef("a", SkillSlot.INHERENT, "skill-x")
    )
    assert decision.status is ProviderResolutionStatus.MISSING


def test_provider_lookup_identity_mismatch() -> None:
    registry = SkillRuntimeRegistry()
    registry.register(make_skill_runtime(skill_id="actual"))
    decision = registry.resolve_provider(
        SkillProviderRef("a", SkillSlot.LEARNED_1, "expected")
    )
    assert decision.status is ProviderResolutionStatus.IDENTITY_MISMATCH


def test_slot_zero_lookup_does_not_skip() -> None:
    registry = SkillRuntimeRegistry()
    runtime = make_skill_runtime(slot=SkillSlot.INHERENT)
    registry.register(runtime)
    decision = registry.resolve_provider(
        SkillProviderRef("a", SkillSlot.INHERENT, "skill-x")
    )
    assert decision.status is ProviderResolutionStatus.FOUND
    assert decision.runtime is runtime


def test_dependency_graph_acyclic() -> None:
    deps = DependencyEvaluationSupport()
    a, b = StateNode("a"), StateNode("b")
    assert deps.add_dependency(a, b) is True
    deps.validate_acyclic()
    assert deps.prerequisites(a) == (b,)


def test_dependency_graph_nested() -> None:
    deps = DependencyEvaluationSupport()
    a, b, c = StateNode("a"), StateNode("b"), StateNode("c")
    deps.add_dependency(a, b)
    deps.add_dependency(b, c)
    assert deps.affected_closure(c) == (a, b, c)


def test_duplicate_edge_deduplicated() -> None:
    deps = DependencyEvaluationSupport()
    a, b = StateNode("a"), StateNode("b")
    assert deps.add_dependency(a, b) is True
    assert deps.add_dependency(a, b) is False
    assert deps.prerequisites(a) == (b,)


def test_cycle_raises_dependency_cycle_error() -> None:
    deps = DependencyEvaluationSupport()
    a, b = StateNode("a"), StateNode("b")
    deps.add_dependency(a, b)
    with pytest.raises(DependencyCycleError):
        deps.add_dependency(b, a)


def test_cycle_path_is_explicit() -> None:
    deps = DependencyEvaluationSupport()
    a, b, c = StateNode("a"), StateNode("b"), StateNode("c")
    deps.add_dependency(a, b)
    deps.add_dependency(b, c)
    with pytest.raises(DependencyCycleError) as exc:
        deps.add_dependency(c, a)
    assert exc.value.cycle_path[0] == c
    assert exc.value.cycle_path[-1] == c
    assert a in exc.value.cycle_path
    assert b in exc.value.cycle_path


def test_cycle_validation_commits_nothing() -> None:
    deps = DependencyEvaluationSupport()
    a, b = StateNode("a"), StateNode("b")
    deps.add_dependency(a, b)
    before = deps.prerequisites(b)
    with pytest.raises(DependencyCycleError):
        deps.add_dependency(b, a)
    assert deps.prerequisites(b) == before


def _metadata_state_adapter(context, instance, _session):
    causes = tuple(
        SuppressionCause(rule_id, LocalRuleCauseRef(subject))
        for rule_id, subject in context.metadata.get("suppression_causes", ())
    )
    inactivity = tuple(
        InactivityCause(rule_id, LocalRuleCauseRef(subject))
        for rule_id, subject in context.metadata.get("inactivity_causes", ())
    )
    return StateEffectivenessContribution(causes, inactivity)


def test_effective_without_blocker() -> None:
    context = make_context()
    instance = add_simple_state(context)
    _, policy, _ = make_foundation()
    assert policy.evaluate_state(context, instance).status is StateEffectivenessStatus.EFFECTIVE


def test_single_suppression_cause() -> None:
    context = make_context()
    instance = add_simple_state(context)
    _, policy, _ = make_foundation()
    policy.register_rule_adapter(_metadata_state_adapter)
    context.metadata["suppression_causes"] = (("RULE_A", "a"),)
    decision = policy.evaluate_state(context, instance)
    assert decision.status is StateEffectivenessStatus.SUPPRESSED
    assert len(decision.suppression_causes) == 1


def test_multiple_suppression_causes() -> None:
    context = make_context()
    instance = add_simple_state(context)
    _, policy, _ = make_foundation()
    policy.register_rule_adapter(_metadata_state_adapter)
    context.metadata["suppression_causes"] = (("RULE_A", "a"), ("RULE_B", "b"))
    assert len(policy.evaluate_state(context, instance).suppression_causes) == 2


def test_remove_one_cause_still_suppressed() -> None:
    context = make_context()
    instance = add_simple_state(context)
    _, policy, _ = make_foundation()
    policy.register_rule_adapter(_metadata_state_adapter)
    context.metadata["suppression_causes"] = (("RULE_A", "a"), ("RULE_B", "b"))
    assert policy.evaluate_state(context, instance).status is StateEffectivenessStatus.SUPPRESSED
    context.metadata["suppression_causes"] = (("RULE_B", "b"),)
    assert policy.evaluate_state(context, instance).status is StateEffectivenessStatus.SUPPRESSED


def test_remove_last_cause_effective() -> None:
    context = make_context()
    instance = add_simple_state(context)
    _, policy, _ = make_foundation()
    policy.register_rule_adapter(_metadata_state_adapter)
    context.metadata["suppression_causes"] = (("RULE_A", "a"),)
    assert policy.evaluate_state(context, instance).status is StateEffectivenessStatus.SUPPRESSED
    context.metadata["suppression_causes"] = ()
    assert policy.evaluate_state(context, instance).status is StateEffectivenessStatus.EFFECTIVE


def test_removed_instance_not_valid_effectiveness_query() -> None:
    context = make_context()
    instance = add_simple_state(context)
    _, policy, _ = make_foundation()
    context.states.remove(instance.instance_id)
    with pytest.raises(KeyError):
        policy.evaluate_state(context, instance)


def _metadata_provider_adapter(context, provider_ref, _session):
    return tuple(
        SuppressionCause(rule_id, LocalRuleCauseRef(subject))
        for rule_id, subject in context.metadata.get("provider_causes", ())
    )


def test_provider_valid() -> None:
    context = make_context()
    context.skill_runtimes.register(make_skill_runtime())
    _, _, policy = make_foundation()
    decision = policy.evaluate_provider(
        context, SkillProviderRef("a", SkillSlot.LEARNED_1, "skill-x")
    )
    assert decision.status is ProviderValidityStatus.VALID


def test_provider_missing() -> None:
    context = make_context()
    _, _, policy = make_foundation()
    decision = policy.evaluate_provider(
        context, SkillProviderRef("a", SkillSlot.LEARNED_1, "skill-x")
    )
    assert decision.status is ProviderValidityStatus.MISSING


def test_provider_identity_mismatch() -> None:
    context = make_context()
    context.skill_runtimes.register(make_skill_runtime(skill_id="actual"))
    _, _, policy = make_foundation()
    decision = policy.evaluate_provider(
        context, SkillProviderRef("a", SkillSlot.LEARNED_1, "expected")
    )
    assert decision.status is ProviderValidityStatus.IDENTITY_MISMATCH


def test_provider_baseline_disabled() -> None:
    context = make_context()
    context.skill_runtimes.register(make_skill_runtime(enabled=False))
    _, _, policy = make_foundation()
    decision = policy.evaluate_provider(
        context, SkillProviderRef("a", SkillSlot.LEARNED_1, "skill-x")
    )
    assert decision.status is ProviderValidityStatus.BASELINE_DISABLED


def test_provider_single_suppression() -> None:
    context = make_context()
    context.skill_runtimes.register(make_skill_runtime())
    _, _, policy = make_foundation()
    policy.register_rule_adapter(_metadata_provider_adapter)
    context.metadata["provider_causes"] = (("P-A", "a"),)
    decision = policy.evaluate_provider(
        context, SkillProviderRef("a", SkillSlot.LEARNED_1, "skill-x")
    )
    assert decision.status is ProviderValidityStatus.SUPPRESSED
    assert len(decision.suppression_causes) == 1


def test_provider_multiple_suppression_causes() -> None:
    context = make_context()
    context.skill_runtimes.register(make_skill_runtime())
    _, _, policy = make_foundation()
    policy.register_rule_adapter(_metadata_provider_adapter)
    context.metadata["provider_causes"] = (("P-A", "a"), ("P-B", "b"))
    decision = policy.evaluate_provider(
        context, SkillProviderRef("a", SkillSlot.LEARNED_1, "skill-x")
    )
    assert decision.status is ProviderValidityStatus.SUPPRESSED
    assert len(decision.suppression_causes) == 2


def test_battle_systems_single_state_effectiveness_policy() -> None:
    systems = BattleSystems()
    assert systems.stage9_state_runtime._state_effectiveness_policy is systems.state_effectiveness_policy
    assert systems.stage11_state_runtime._state_effectiveness_policy is systems.state_effectiveness_policy


def test_battle_systems_single_provider_validity_policy() -> None:
    systems = BattleSystems()
    assert systems.recovery_opportunity_system._provider_validity_policy is systems.provider_validity_policy


def test_stage9_and_stage11_receive_same_effectiveness_policy() -> None:
    systems = BattleSystems()
    assert (
        systems.stage9_state_runtime._state_effectiveness_policy
        is systems.stage11_state_runtime._state_effectiveness_policy
    )


def test_skill_and_recovery_receive_same_provider_policy_when_migrated() -> None:
    systems = BattleSystems()
    assert systems.recovery_opportunity_system._provider_validity_policy is systems.provider_validity_policy


def test_no_duplicate_dependency_evaluation_support() -> None:
    systems = BattleSystems()
    assert systems.state_effectiveness_policy.dependency_support is systems.dependency_evaluation_support
    assert systems.provider_validity_policy.dependency_support is systems.dependency_evaluation_support


def test_recovery_gate_handles_inherent_slot_zero() -> None:
    context = make_context(seed=77)
    systems = BattleSystems()
    context.units["b"].troops = 500
    context.skill_runtimes.register(
        make_skill_runtime(
            slot=SkillSlot.INHERENT,
            skill_id="heal-zero",
            enabled=False,
        )
    )
    opportunity = RecoveryOpportunity(
        opportunity_kind=RecoveryOpportunityKind.RECUPERATION_ACTION_START,
        execution_descriptor=RuleIntentExecutionDescriptor(
            intent_kind=RuleIntentKind.RECOVERY_OPPORTUNITY,
            intent_owner_id="b",
            state_owner_id="a",
            target_id="b",
            source_ref=EffectSourceRef(
                stage9_source_type=SourceType.ACTIVE_SKILL,
                source_unit_id="a",
                source_skill_id="heal-zero",
                source_skill_slot=SkillSlot.INHERENT,
            ),
            execution_domain="STATE_RESOLUTION",
        ),
        probability=1.0,
        recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT,
        recovery_potency_context=RecoveryPotencyContext(treatment_amount=100),
        source_skill_gate=PersistentSourceSkillGate.query_skill_runtime(),
        aftermath_fact=None,
    )
    result = systems.recovery_opportunity_system.execute(context, opportunity)
    assert result.executed is False
    assert result.reason == "SKILL_TEMPORARILY_DISABLED"
    assert context.random.random() == RandomSystem(77).random()


def test_trigger_provenance_preserves_inherent_slot_zero() -> None:
    generation = StateApplicationGenerationId("gen-trigger-zero")
    basis = FrozenContinuousDamageBasis(
        application_generation_id=generation,
        source_unit_id="a",
        damage_type=DamageType.WEAPON,
        coefficient=1.0,
        source_skill_id="basis-skill",
        source_skill_slot=SkillSlot.INHERENT,
    )
    instance = StateInstance(
        instance_id="state-trigger-zero",
        state_id="synthetic-dot",
        owner_id="b",
        source_id="a",
        source_skill_id="instance-skill",
        source_skill_slot=SkillSlot.LEARNED_2,
        applied_round=1,
        applied_phase="ACTION_ORDER",
        runtime_params=ContinuousDamageStateParams(
            application_generation_id=generation,
            frozen_damage_basis=basis,
        ),
    )
    intents = TriggerSystem._intents_for_state(instance)
    assert len(intents) == 1
    assert intents[0].source_ref is not None
    assert intents[0].source_ref.source_skill_slot is SkillSlot.INHERENT


def test_foundation_modules_do_not_import_random_or_consume_context_random() -> None:
    root = Path(__file__).parents[1] / "sgs_v2" / "battle_core"
    for name in (
        "provider_identity.py",
        "dependency_evaluation.py",
        "state_effectiveness.py",
        "provider_validity.py",
    ):
        source = (root / name).read_text(encoding="utf-8")
        tree = ast.parse(source)
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


def test_no_production_fallback_construction_of_canonical_policy() -> None:
    path = Path(__file__).parents[1] / "sgs_v2" / "battle_core" / "battle_systems.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    canonical = {"StateEffectivenessPolicy", "ProviderValidityPolicy"}
    for node in ast.walk(tree):
        if not isinstance(node, ast.BoolOp) or not isinstance(node.op, ast.Or):
            continue
        called = {
            child.func.id
            for child in ast.walk(node)
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
        }
        assert not (called & canonical)


def test_foundation_policies_do_not_mutate_registries() -> None:
    root = Path(__file__).parents[1] / "sgs_v2" / "battle_core"
    for name in ("state_effectiveness.py", "provider_validity.py"):
        tree = ast.parse((root / name).read_text(encoding="utf-8"))
        mutators = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        assert not (mutators & {"add", "remove", "replace", "register_definition"})
