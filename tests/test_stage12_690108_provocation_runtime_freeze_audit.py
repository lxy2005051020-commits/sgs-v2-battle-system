from __future__ import annotations

import inspect

import pytest

from sgs_v2.battle_core import (
    ApplyStateEffect,
    BattlePhase,
    BattleSystems,
    DamageSkillEffectSpec,
    DamageType,
    EffectSourceRef,
    OfficialStateId,
    ProviderDependency,
    RandomSystem,
    SkillDefinition,
    SkillResolutionStatus,
    SkillRuntime,
    SkillSlot,
    SkillTargetMode,
    SkillType,
    SourceType,
    StateApplicationResultStatus,
    StateLifetimeSpec,
    StateNode,
    TargetCardinality,
    TargetOperationProducer,
    TargetPolicyContribution,
    TargetQueryMode,
    TargetRelation,
    TargetSelectionProvenance,
    TargetSelectionResult,
    TargetSelectorKind,
)
from sgs_v2.battle_core import provocation_integration as provocation_module
from sgs_v2.battle_core import skill_resolver as skill_resolver_module
from sgs_v2.battle_core.provocation_integration import (
    PROVOCATION_CONFUSION_PREEMPTION_KEY,
    PROVOCATION_REAPPLICATION_BOUNDARY_RULE_ID,
)
from tests.test_stage12_690108_provocation import (
    CountingRandomSystem,
    apply_provocation,
    apply_state,
    capture_operation,
    make_context,
    operation,
    provider_ref,
    register_source_provider,
    resolve_skill,
    runtime,
    settle_due,
)


def choose_n(seed: int, count: int, source: str = "b"):
    rng = CountingRandomSystem(seed)
    context, systems = make_context(random_system=rng), BattleSystems()
    apply_provocation(systems, context, source=source)
    result = resolve_skill(
        systems,
        context,
        runtime(mode=SkillTargetMode.CHOOSE_N_RANDOM_ENEMIES, target_count=count),
    )
    return context, systems, rng, result


def test_choose_n_rd_sf_005_reserve_first_exact_population() -> None:
    _c, _s, rng, result = choose_n(8101, 2, "c")
    assert result.target_ids[0] == "c"
    assert rng.sample_populations == [("b", "d")]
    assert rng.sample_ks == [1]


def test_choose_n_rd_sf_005_downstream_rng_stream_stable() -> None:
    context, _s, rng, _result = choose_n(8102, 2)
    expected = RandomSystem(8102)
    expected.sample([0, 1], 1)
    assert (rng.sample_calls, rng.sample_ks) == (1, [1])
    assert context.random.random() == expected.random()


def test_choose_n_n1_has_zero_selector_rng() -> None:
    _c, _s, rng, result = choose_n(8103, 1, "d")
    assert result.target_ids == ("d",)
    assert rng.sample_calls == 0


def test_choose_n_exact_fill_has_zero_selector_rng() -> None:
    _c, _s, rng, result = choose_n(8104, 3)
    assert set(result.target_ids) == {"b", "c", "d"}
    assert rng.sample_calls == 0


def test_choose_n_excess_pool_has_exactly_one_sample() -> None:
    _c, _s, rng, result = choose_n(8105, 2)
    assert len(result.target_ids) == 2 and result.target_ids.count("b") == 1
    assert (rng.sample_calls, rng.sample_ks, rng.sample_populations) == (
        1,
        [1],
        [("c", "d")],
    )


def test_bu_p09_remains_unsupported() -> None:
    context, systems = make_context(seed=8106), BattleSystems()
    apply_provocation(systems, context, source="b")
    with pytest.raises(ValueError, match="unsupported Skill target-policy boundary"):
        resolve_skill(
            systems,
            context,
            runtime(mode=SkillTargetMode.CHOOSE_N_RANDOM_ENEMIES, target_count=4),
        )


def test_resolved_target_never_rewritten_after_provocation_resume() -> None:
    context, systems = make_context(seed=8107), BattleSystems()
    provoke = apply_provocation(
        systems,
        context,
        source="b",
        lifetime=StateLifetimeSpec.round_calendar(expires_round=3),
    ).instance
    captured = capture_operation(systems)
    fresh = resolve_skill(systems, context, runtime())
    resolved = TargetSelectionResult(
        captured[-1].operation_id,
        fresh.target_ids,
        TargetSelectionProvenance.FRESH_SELECTED,
    )
    snapshot = (resolved.operation_id, resolved.target_ids, resolved.provenance)
    apply_state(
        systems,
        context,
        OfficialStateId.INSIGHT.value,
        lifetime=StateLifetimeSpec.round_calendar(expires_round=2),
    )
    assert provoke is not None and not systems.state_effectiveness_policy.evaluate_state(context, provoke).effective
    settle_due(systems, context, round_no=2, phase=BattlePhase.ROUND_END.value)
    continued = TargetOperationProducer.continue_from(resolved, TargetQueryMode.INHERIT_RESOLVED)
    assert (resolved.operation_id, resolved.target_ids, resolved.provenance) == snapshot
    assert continued.target_ids == resolved.target_ids


def test_new_query_rechecks_source_eligibility() -> None:
    context, systems = make_context(seed=8108), BattleSystems()
    apply_provocation(systems, context, source="b")
    item = runtime()
    context.get_unit("b").troops = 0
    assert "b" not in resolve_skill(systems, context, item).target_ids
    context.get_unit("b").troops = 1000
    assert resolve_skill(systems, context, item).target_ids == ("b",)


def test_illegal_source_never_inserted() -> None:
    context, systems = make_context(seed=8109), BattleSystems()
    provoke = apply_provocation(systems, context, source="b").instance
    systems.skill_target_policy.register_rule_adapter(
        lambda *_: TargetPolicyContribution(excluded_target_ids=("b",))
    )
    result = resolve_skill(systems, context, runtime())
    assert provoke is not None and context.states.has_instance(provoke.instance_id)
    assert "b" not in result.target_ids


def test_exhaustion_short_circuits_before_target_operation(monkeypatch) -> None:
    context, systems = make_context(seed=8110), BattleSystems()
    apply_provocation(systems, context, source="b")
    apply_state(systems, context, OfficialStateId.SILENCE.value)
    created = []
    original = TargetOperationProducer.new_query

    def record(*args, **kwargs):
        created.append(1)
        return original(*args, **kwargs)

    monkeypatch.setattr(TargetOperationProducer, "new_query", staticmethod(record))
    assert resolve_skill(systems, context, runtime()).status is SkillResolutionStatus.DISABLED
    assert created == []


def test_false_report_holder_does_not_suppress_source_provider() -> None:
    context, systems = make_context(seed=8111), BattleSystems()
    source_provider = register_source_provider(context, owner="b")
    apply_state(systems, context, OfficialStateId.FALSE_REPORT.value, owner="a", source="c")
    provoke = apply_provocation(
        systems,
        context,
        source="b",
        dependencies=(ProviderDependency(provider_ref(source_provider), "PAIR"),),
    ).instance
    assert provoke is not None and systems.state_effectiveness_policy.evaluate_state(context, provoke).effective


@pytest.mark.parametrize(
    "source_skill_id,source_skill_slot",
    [
        (None, None),
        ("provocation-source-provider", None),
        (None, SkillSlot.INHERENT),
        ("provocation-source-provider", SkillSlot.INHERENT),
    ],
)
def test_attribution_without_dependency_does_not_suppress(source_skill_id, source_skill_slot) -> None:
    context, systems = make_context(seed=8112), BattleSystems()
    register_source_provider(context, owner="b")
    apply_state(systems, context, OfficialStateId.FALSE_REPORT.value, owner="b", source="a")
    provoke = apply_provocation(
        systems,
        context,
        source="b",
        source_skill_id=source_skill_id,
        source_skill_slot=source_skill_slot,
    ).instance
    assert provoke is not None
    assert systems.dependency_evaluation_support.prerequisites(StateNode(provoke.instance_id)) == ()
    assert systems.state_effectiveness_policy.evaluate_state(context, provoke).effective


def test_effect_source_ref_attribution_without_dependency_does_not_suppress() -> None:
    context, systems = make_context(seed=8113), BattleSystems()
    source_provider = register_source_provider(context)
    apply_state(systems, context, OfficialStateId.FALSE_REPORT.value, owner="b", source="a")
    executed = systems.effect_executor.execute(
        context,
        ApplyStateEffect(
            state_id=OfficialStateId.PROVOKE.value,
            owner_id="a",
            source_id="b",
            source_ref=EffectSourceRef(
                SourceType.ACTIVE_SKILL,
                source_unit_id="b",
                source_skill_id=source_provider.definition.skill_id,
                source_skill_slot=source_provider.skill_slot,
            ),
        ),
    )
    provoke = executed.state_instance
    assert systems.dependency_evaluation_support.prerequisites(StateNode(provoke.instance_id)) == ()
    assert systems.state_effectiveness_policy.evaluate_state(context, provoke).effective


def test_source_death_keeps_state_resident_but_unforced() -> None:
    context, systems = make_context(seed=8114), BattleSystems()
    provoke = apply_provocation(systems, context, source="b").instance
    context.get_unit("b").troops = 0
    systems.defeat_cleanup_port.commit_defeat(context, "b")
    assert provoke is not None and context.states.has_instance(provoke.instance_id)
    assert "b" not in resolve_skill(systems, context, runtime()).target_ids


@pytest.mark.parametrize("source", ["b", "c"])
def test_bu_p06_remains_unsupported(source: str) -> None:
    context, systems = make_context(seed=8115), BattleSystems()
    assert apply_provocation(systems, context, source="b").status is StateApplicationResultStatus.APPLIED
    result = apply_provocation(systems, context, source=source)
    assert result.status is StateApplicationResultStatus.UNSUPPORTED_BOUNDARY
    assert result.reason_rule_id == PROVOCATION_REAPPLICATION_BOUNDARY_RULE_ID


@pytest.mark.parametrize(
    "mode,count,cardinality,selector",
    [
        (SkillTargetMode.SINGLE_RANDOM_ENEMY, None, TargetCardinality.SINGLE, TargetSelectorKind.RANDOM),
        (SkillTargetMode.SINGLE_DETERMINISTIC_ENEMY, None, TargetCardinality.SINGLE, TargetSelectorKind.DETERMINISTIC),
        (SkillTargetMode.CHOOSE_N_RANDOM_ENEMIES, 2, TargetCardinality.CHOOSE_N, TargetSelectorKind.RANDOM),
        (SkillTargetMode.CHOOSE_N_DETERMINISTIC_ENEMIES, 2, TargetCardinality.CHOOSE_N, TargetSelectorKind.DETERMINISTIC),
        (SkillTargetMode.FIXED_ALL_ENEMIES, None, TargetCardinality.FIXED_ALL, TargetSelectorKind.DETERMINISTIC),
    ],
)
def test_producer_mapping_all_supported_skill_target_modes(mode, count, cardinality, selector) -> None:
    context, systems = make_context(seed=8116), BattleSystems()
    captured = capture_operation(systems)
    resolve_skill(systems, context, runtime(mode=mode, target_count=count))
    op = captured[-1]
    assert (op.relation, op.cardinality, op.selector_kind, op.requested_count) == (
        TargetRelation.ENEMY,
        cardinality,
        selector,
        count,
    )


@pytest.mark.parametrize("relation,candidates", [(TargetRelation.ALLY, ("x",)), (TargetRelation.SELF, ("a",))])
def test_relation_boundary_ally_and_self_are_not_redirected(relation, candidates) -> None:
    context, systems = make_context(seed=8117), BattleSystems()
    apply_provocation(systems, context, source="b")
    assert systems.skill_target_policy.evaluate(
        context,
        operation(context, relation=relation),
        candidates,
    ).required_target_ids == ()


def test_confusion_owned_operation_preempts_provocation() -> None:
    context, systems = make_context(seed=8118), BattleSystems()
    apply_provocation(systems, context, source="b")
    apply_state(systems, context, OfficialStateId.CONFUSION.value, source="c")
    decision = systems.skill_target_policy.evaluate(
        context,
        operation(context, restriction_keys=(PROVOCATION_CONFUSION_PREEMPTION_KEY,)),
        ("b", "c", "d"),
    )
    assert decision.required_target_ids == ()


def test_provider_invalid_short_circuits_before_target_operation(monkeypatch) -> None:
    context, systems = make_context(seed=8119), BattleSystems()
    apply_provocation(systems, context, source="b")
    item = runtime(skill_id="audit.command-provider", skill_type=SkillType.COMMAND)
    context.skill_runtimes.register(item)
    apply_state(systems, context, OfficialStateId.FALSE_REPORT.value, owner="a", source="c")
    created = []
    original = TargetOperationProducer.new_query

    def record(*args, **kwargs):
        created.append(1)
        return original(*args, **kwargs)

    monkeypatch.setattr(TargetOperationProducer, "new_query", staticmethod(record))
    assert systems.skill_resolver.resolve(context, item).status is SkillResolutionStatus.DISABLED
    assert created == []


def test_suppression_lifetime_continues_and_expired_provocation_does_not_resume() -> None:
    context, systems = make_context(seed=8120), BattleSystems()
    provoke = apply_provocation(
        systems,
        context,
        source="b",
        lifetime=StateLifetimeSpec.round_calendar(expires_round=2),
    ).instance
    apply_state(
        systems,
        context,
        OfficialStateId.INSIGHT.value,
        lifetime=StateLifetimeSpec.round_calendar(expires_round=3),
    )
    assert provoke is not None and not systems.state_effectiveness_policy.evaluate_state(context, provoke).effective
    removed = settle_due(systems, context, round_no=2, phase=BattlePhase.ROUND_END.value)
    assert provoke.instance_id in {item.instance_id for item in removed}
    settle_due(systems, context, round_no=3, phase=BattlePhase.ROUND_END.value)
    assert not context.states.has(owner_id="a", state_id=OfficialStateId.PROVOKE.value)


def test_resume_preserves_same_instance_generation_and_uses_zero_rng() -> None:
    rng = CountingRandomSystem(8121)
    context, systems = make_context(random_system=rng), BattleSystems()
    provoke = apply_provocation(
        systems,
        context,
        source="b",
        lifetime=StateLifetimeSpec.round_calendar(expires_round=4),
    ).instance
    assert provoke is not None
    identity = (provoke.instance_id, provoke.current_generation_id)
    before = (rng.sample_calls, rng.choice_calls, rng.chance_calls)
    apply_state(
        systems,
        context,
        OfficialStateId.INSIGHT.value,
        lifetime=StateLifetimeSpec.round_calendar(expires_round=2),
    )
    settle_due(systems, context, round_no=2, phase=BattlePhase.ROUND_END.value)
    resumed = context.states.get(provoke.instance_id)
    assert (resumed.instance_id, resumed.current_generation_id) == identity
    assert (rng.sample_calls, rng.choice_calls, rng.chance_calls) == before


def test_effect_multiplicity_allocates_one_target_operation() -> None:
    context, systems = make_context(seed=8122), BattleSystems()
    apply_provocation(systems, context, source="b")
    captured = capture_operation(systems)
    item = SkillRuntime(
        SkillDefinition(
            skill_id="audit.multi-effect",
            name="audit.multi-effect",
            activation_rate=1.0,
            target_mode=SkillTargetMode.SINGLE_RANDOM_ENEMY,
            effect_specs=(
                DamageSkillEffectSpec(DamageType.WEAPON),
                DamageSkillEffectSpec(DamageType.STRATEGY),
            ),
            skill_type=SkillType.ACTIVE,
        ),
        owner_id="a",
        skill_slot=SkillSlot.INHERENT,
    )
    assert len(resolve_skill(systems, context, item).effects) == 2
    assert len(captured) == 1


def test_new_query_identity_is_fresh_and_continuation_reuses_old_identity() -> None:
    context, systems = make_context(seed=8123), BattleSystems()
    apply_provocation(systems, context, source="b")
    captured = capture_operation(systems)
    item = runtime()
    first = resolve_skill(systems, context, item)
    resolve_skill(systems, context, item)
    assert captured[0].operation_id != captured[1].operation_id
    selected = TargetSelectionResult(
        captured[0].operation_id,
        first.target_ids,
        TargetSelectionProvenance.FRESH_SELECTED,
    )
    assert TargetOperationProducer.continue_from(
        selected,
        TargetQueryMode.LOCK_RESOLVED,
    ).operation_id == captured[0].operation_id


def test_canonical_wiring_and_static_architecture_guards() -> None:
    systems = BattleSystems()
    assert systems.skill_resolver._target_policy is systems.skill_target_policy
    assert systems.skill_resolver._target_system is systems.target_system
    assert systems.normal_attack_system.target_system is systems.target_system
    assert systems.target_resolution_system._target_system is systems.target_system
    source = inspect.getsource(provocation_module)
    for token in (
        "ProvocationRuntime",
        "ForcedTargetManager",
        "ProvocationTargetResolver",
        "context.random",
        ".sample(",
        ".choice(",
        "EventBus",
        ".publish(",
        "PROVOCATION_FORCED_TARGET",
        "NormalAttackSystem",
        "ActionSystem",
        "TargetResolutionSystem",
    ):
        assert token not in source
    resolver_source = inspect.getsource(skill_resolver_module.SkillResolver._select_policy_targets)
    assert "slots = count - len(required)" in resolver_source
    assert "random_units" in resolver_source
    assert "replace" not in resolver_source.lower()
