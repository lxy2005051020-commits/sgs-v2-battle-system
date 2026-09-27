from __future__ import annotations

from sgs_v2.battle_core import (
    BattleContext,
    EventBus,
    LineupPosition,
    RandomSystem,
    SkillProviderRef,
    SkillResolver,
    SkillSlot,
    SkillTargetPolicy,
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
    TargetSystem,
    UnitRuntime,
)


class CountingRandomSystem(RandomSystem):
    def __init__(self, seed: int = 1) -> None:
        super().__init__(seed)
        self.sample_calls: list[tuple[int, int]] = []

    def sample(self, values, k):  # type: ignore[no-untyped-def]
        self.sample_calls.append((len(values), k))
        return super().sample(values, k)


class RecordingTargetSystem(TargetSystem):
    def __init__(self) -> None:
        self.calls: list[tuple[tuple[str, ...], int]] = []
        self.returned: list[tuple[str, ...]] = []

    def random_units(self, context, candidates, *, count):  # type: ignore[no-untyped-def]
        self.calls.append((tuple(item.unit_id for item in candidates), count))
        result = super().random_units(context, candidates, count=count)
        self.returned.append(tuple(item.unit_id for item in result))
        return result


def make_context(seed: int = 17) -> BattleContext:
    units = {
        "a": UnitRuntime(
            "a", "A", "A", 1000, 1000, 300, 100, 100,
            lineup_position=LineupPosition.COMMANDER,
        ),
        "b": UnitRuntime(
            "b", "B", "B", 1000, 1000, 100, 100, 90,
            lineup_position=LineupPosition.COMMANDER,
        ),
        "c": UnitRuntime(
            "c", "C", "B", 1000, 1000, 100, 100, 80,
            lineup_position=LineupPosition.DEPUTY_1,
        ),
        "d": UnitRuntime(
            "d", "D", "B", 1000, 1000, 100, 100, 70,
            lineup_position=LineupPosition.DEPUTY_2,
        ),
    }
    return BattleContext(
        battle_id="bu-p02-governance",
        units=units,
        event_bus=EventBus(),
        random=CountingRandomSystem(seed),
    )


def make_operation(
    context: BattleContext,
    *,
    count: int = 2,
    selector_kind: TargetSelectorKind = TargetSelectorKind.RANDOM,
):
    return TargetOperationProducer.new_query(
        context,
        actor_id="a",
        producer_ref=SkillProviderRef(
            "a",
            SkillSlot.INHERENT,
            "synthetic.bu-p02",
        ),
        admitted_operation_key="skill:a:0:synthetic.bu-p02",
        relation=TargetRelation.ENEMY,
        cardinality=TargetCardinality.CHOOSE_N,
        selector_kind=selector_kind,
        eligibility_context=TargetEligibilityContext(
            TargetOperationDomain.SKILL,
            TargetPurpose.HOSTILE,
        ),
        requested_count=count,
    )


def enemy_candidates(context: BattleContext):
    return [
        context.get_unit("b"),
        context.get_unit("c"),
        context.get_unit("d"),
    ]


def select(
    context: BattleContext,
    target_system: TargetSystem,
    *,
    count: int = 2,
    required_target_ids: tuple[str, ...] = ("c",),
):
    resolver = SkillResolver(target_system)
    return resolver._select_policy_targets(
        context,
        make_operation(context, count=count),
        enemy_candidates(context),
        required_target_ids,
    )


def test_choose_n_required_target_preserves_n() -> None:
    context = make_context()
    result = select(context, TargetSystem(), count=2)
    assert len(result) == 2
    assert "c" in {item.unit_id for item in result}


def test_choose_n_required_target_exactly_once() -> None:
    context = make_context()
    policy = SkillTargetPolicy()
    policy.register_rule_adapter(
        lambda _ctx, _op, _raw: TargetPolicyContribution(
            required_target_ids=("c", "c"),
        )
    )
    operation = make_operation(context)
    decision = policy.evaluate(context, operation, enemy_candidates(context))
    assert decision.required_target_ids == ("c",)

    resolver = SkillResolver(TargetSystem())
    result = resolver._select_policy_targets(
        context,
        operation,
        enemy_candidates(context),
        decision.required_target_ids,
    )
    assert [item.unit_id for item in result].count("c") == 1


def test_choose_n_required_target_rng_owner_is_target_system() -> None:
    context = make_context()
    target_system = RecordingTargetSystem()
    result = select(context, target_system, count=2)
    assert len(result) == 2
    assert target_system.calls == [(("b", "d"), 1)]


def test_choose_n_policy_consumes_zero_rng() -> None:
    context = make_context(seed=31)
    policy = SkillTargetPolicy()
    policy.register_rule_adapter(
        lambda _ctx, _op, _raw: TargetPolicyContribution(
            required_target_ids=("c",),
        )
    )
    policy.evaluate(context, make_operation(context), enemy_candidates(context))
    observed = context.random.random()
    expected = RandomSystem(31).random()
    assert observed == expected


def test_choose_n_new_query_replay_deterministic() -> None:
    first_context = make_context(seed=43)
    second_context = make_context(seed=43)
    first = select(first_context, TargetSystem(), count=2)
    second = select(second_context, TargetSystem(), count=2)
    assert tuple(item.unit_id for item in first) == tuple(item.unit_id for item in second)


def test_choose_n_subsequent_rng_stream_stable() -> None:
    context = make_context(seed=71)
    select(context, TargetSystem(), count=2)

    expected_rng = RandomSystem(71)
    expected_rng.sample([0, 1], 1)

    assert context.random.random() == expected_rng.random()


def test_choose_n_n_equals_one_zero_target_draw_if_required_fills_slot() -> None:
    context = make_context(seed=53)
    result = select(context, TargetSystem(), count=1)
    assert tuple(item.unit_id for item in result) == ("c",)
    assert context.random.sample_calls == []


def continuation_fixture(seed: int = 59) -> tuple[BattleContext, TargetSelectionResult]:
    context = make_context(seed=seed)
    operation = make_operation(context)
    selected = TargetSelectionResult(
        operation.operation_id,
        ("c", "b"),
        TargetSelectionProvenance.FRESH_SELECTED,
    )
    return context, selected


def test_inherited_result_does_not_reselect() -> None:
    context, selected = continuation_fixture()
    continued = TargetOperationProducer.continue_from(
        selected,
        TargetQueryMode.INHERIT_RESOLVED,
    )
    assert continued.target_ids == selected.target_ids
    assert continued.provenance is TargetSelectionProvenance.INHERITED
    assert context.random.sample_calls == []


def test_derived_result_does_not_reselect() -> None:
    context, selected = continuation_fixture()
    continued = TargetOperationProducer.continue_from(
        selected,
        TargetQueryMode.DERIVE_FROM_RESOLVED,
        target_ids=("c", "d"),
    )
    assert continued.target_ids == ("c", "d")
    assert continued.provenance is TargetSelectionProvenance.DERIVED
    assert context.random.sample_calls == []


def test_locked_result_does_not_reselect() -> None:
    context, selected = continuation_fixture()
    continued = TargetOperationProducer.continue_from(
        selected,
        TargetQueryMode.LOCK_RESOLVED,
    )
    assert continued.target_ids == selected.target_ids
    assert continued.provenance is TargetSelectionProvenance.LOCKED
    assert context.random.sample_calls == []


def test_required_target_reserved_before_random_fill() -> None:
    context = make_context()
    target_system = RecordingTargetSystem()
    result = select(context, target_system, count=2)
    assert result[0].unit_id == "c"
    assert target_system.calls == [(("b", "d"), 1)]


def test_random_fill_excludes_required_target() -> None:
    context = make_context()
    target_system = RecordingTargetSystem()
    select(context, target_system, count=2)
    candidates, _count = target_system.calls[0]
    assert "c" not in candidates


def test_random_fill_count_is_n_minus_required_count() -> None:
    context = make_context()
    target_system = RecordingTargetSystem()
    select(context, target_system, count=3)
    assert target_system.calls == [(("b", "d"), 2)]
    assert context.random.sample_calls == []


def test_no_post_selector_replacement() -> None:
    context = make_context()
    target_system = RecordingTargetSystem()
    result = select(context, target_system, count=2)
    assert tuple(item.unit_id for item in result) == (
        "c",
        *target_system.returned[0],
    )
