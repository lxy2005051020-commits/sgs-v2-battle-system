from __future__ import annotations

from sgs_v2.battle_core import (
    AttributeSystem,
    BattleContext,
    DamageFormulaContext,
    DamageDefensePolicy,
    DamageModifierContribution,
    DamageModifierKind,
    DamageModifierOperation,
    DamageModifierPhase,
    DamageRequest,
    DamageRuleCollection,
    DamageRuleFamily,
    DamageSourceType,
    DamageSystem,
    DamageType,
    EventBus,
    HitPreventionCategory,
    HitRuleContribution,
    HitRuleKind,
    LineupPosition,
    RandomSystem,
    Stage8ProbabilityParams,
    StateDamageRuleProvider,
    StateDefinition,
    StateLifecycleSystem,
    StateRuleAdapter,
    StateRuleBinding,
    StrategyBaseDamageFormula,
    UnitRuntime,
)


class CountingRandomSystem(RandomSystem):
    def __init__(self, seed: int) -> None:
        super().__init__(seed)
        self.randint_calls = 0
        self.chance_calls = 0

    def randint(self, a: int, b: int) -> int:
        self.randint_calls += 1
        return super().randint(a, b)

    def chance(self, probability: float) -> bool:
        self.chance_calls += 1
        return super().chance(probability)


def make_context(seed: int = 71) -> BattleContext:
    return BattleContext(
        battle_id=f"stage8-hardening-{seed}",
        units={
            "a": UnitRuntime(
                "a",
                "A",
                "A",
                10000,
                10000,
                300,
                180,
                100,
                lineup_position=LineupPosition.COMMANDER,
                intelligence=300,
            ),
            "b": UnitRuntime(
                "b",
                "B",
                "B",
                10000,
                10000,
                200,
                200,
                90,
                lineup_position=LineupPosition.COMMANDER,
                intelligence=250,
            ),
        },
        event_bus=EventBus(),
        random=CountingRandomSystem(seed),
    )


def request(damage_type: DamageType = DamageType.WEAPON) -> DamageRequest:
    return DamageRequest(
        source_id="a",
        target_id="b",
        damage_type=damage_type,
        source_type=DamageSourceType.SKILL,
    )


def test_strategy_normal_formula_context_is_exactly_backward_compatible() -> None:
    old_context = make_context(72)
    new_context = make_context(72)
    formula = StrategyBaseDamageFormula(AttributeSystem())

    old_damage = formula.calculate(
        old_context,
        old_context.get_unit("a"),
        old_context.get_unit("b"),
    )
    new_damage = formula.calculate(
        new_context,
        new_context.get_unit("a"),
        new_context.get_unit("b"),
        formula_context=DamageFormulaContext(DamageDefensePolicy.NORMAL),
    )

    assert new_damage == old_damage
    assert old_context.random.randint_calls == 2
    assert new_context.random.randint_calls == 2
    assert old_context.random.chance_calls == new_context.random.chance_calls == 0


def test_strategy_ignore_policy_zeroes_only_target_intelligence_defense_input() -> None:
    normal_context = make_context(73)
    ignored_context = make_context(73)
    formula = StrategyBaseDamageFormula(
        AttributeSystem(),
        random_percent_range=(90, 90),
        low_damage_floor_range=(5, 5),
    )

    normal_damage = formula.calculate(
        normal_context,
        normal_context.get_unit("a"),
        normal_context.get_unit("b"),
    )
    ignored_damage = formula.calculate(
        ignored_context,
        ignored_context.get_unit("a"),
        ignored_context.get_unit("b"),
        formula_context=DamageFormulaContext(
            DamageDefensePolicy.IGNORE_RELEVANT_TARGET_DEFENSE
        ),
    )

    assert ignored_damage > normal_damage
    assert normal_context.random.randint_calls == ignored_context.random.randint_calls == 2


def test_damage_system_collects_exactly_one_rule_snapshot_per_request() -> None:
    class FalseyCountingProvider:
        provider_key = "falsey-counting"

        def __init__(self) -> None:
            self.calls = 0

        def __bool__(self) -> bool:
            return False

        def collect(self, context, damage_request):
            self.calls += 1
            return DamageRuleCollection()

    context = make_context(74)
    provider = FalseyCountingProvider()
    system = DamageSystem(
        AttributeSystem(),
        weapon_random_percent_range=(90, 90),
        weapon_low_damage_floor_range=(5, 5),
        rule_provider=provider,
    )

    result = system.calculate(context, request())

    assert result.final_damage > 0
    assert provider.calls == 1


def _evasion_builder(instance, source, damage_request):
    if instance.owner_id != damage_request.target_id:
        return None
    params = instance.runtime_params
    assert isinstance(params, Stage8ProbabilityParams)
    return HitRuleContribution(
        kind=HitRuleKind.PROBABILISTIC_PREVENTION,
        category=HitPreventionCategory.EVASION_LIKE,
        probability=params.probability,
        source=source,
        order_key=source.origin_key,
    )


def test_hit_trace_preserves_multiple_state_contributors_and_decisive_source() -> None:
    context = make_context(75)
    for state_id in ("synthetic_evasion_zero", "synthetic_evasion_one"):
        context.states.register_definition(
            StateDefinition(
                state_id=state_id,
                name=state_id,
                runtime_params_type=Stage8ProbabilityParams,
            )
        )
    lifecycle = StateLifecycleSystem()
    first = lifecycle.apply(
        context,
        state_id="synthetic_evasion_zero",
        owner_id="b",
        runtime_params=Stage8ProbabilityParams(0.0),
    )
    second = lifecycle.apply(
        context,
        state_id="synthetic_evasion_one",
        owner_id="b",
        runtime_params=Stage8ProbabilityParams(1.0),
    )
    provider = StateDamageRuleProvider(
        (
            StateRuleBinding(
                "synthetic_evasion_zero",
                (
                    StateRuleAdapter(
                        "zero",
                        DamageRuleFamily.HIT,
                        _evasion_builder,
                    ),
                ),
            ),
            StateRuleBinding(
                "synthetic_evasion_one",
                (
                    StateRuleAdapter(
                        "one",
                        DamageRuleFamily.HIT,
                        _evasion_builder,
                    ),
                ),
            ),
        )
    )
    system = DamageSystem(AttributeSystem(), rule_provider=provider)

    result = system.calculate(context, request())
    hit = result.pipeline_trace.hit_result

    assert result.prevented is True
    assert [source.source_state_instance_id for source in hit.contributors] == [
        first.instance_id,
        second.instance_id,
    ]
    assert hit.decisive_source.source_state_instance_id == second.instance_id
    assert context.random.chance_calls == 0
    assert context.random.randint_calls == 0


def _critical_builder(instance, source, damage_request):
    if instance.owner_id != damage_request.source_id:
        return None
    params = instance.runtime_params
    assert isinstance(params, Stage8ProbabilityParams)
    return DamageModifierContribution(
        phase=DamageModifierPhase.CRITICAL,
        kind=DamageModifierKind.CRITICAL_MULTIPLIER,
        operation=DamageModifierOperation.MULTIPLY_FACTOR,
        operand=2.0,
        probability=params.probability,
        damage_types=frozenset({DamageType.WEAPON}),
        source=source,
        order_key=source.origin_key,
    )


def _critical_system(context: BattleContext, probability: float) -> DamageSystem:
    state_id = "synthetic_critical"
    context.states.register_definition(
        StateDefinition(
            state_id=state_id,
            name=state_id,
            runtime_params_type=Stage8ProbabilityParams,
        )
    )
    StateLifecycleSystem().apply(
        context,
        state_id=state_id,
        owner_id="a",
        runtime_params=Stage8ProbabilityParams(probability),
    )
    provider = StateDamageRuleProvider(
        (
            StateRuleBinding(
                state_id,
                (
                    StateRuleAdapter(
                        "critical",
                        DamageRuleFamily.MODIFIER,
                        _critical_builder,
                    ),
                ),
            ),
        )
    )
    return DamageSystem(
        AttributeSystem(),
        weapon_random_percent_range=(90, 90),
        weapon_low_damage_floor_range=(5, 5),
        rule_provider=provider,
    )


def test_critical_probability_zero_skips_rng_and_modifier() -> None:
    context = make_context(76)
    result = _critical_system(context, 0.0).calculate(context, request())

    assert context.random.chance_calls == 0
    assert context.random.randint_calls == 2
    assert result.pipeline_trace.modifier_result.applied_modifiers == ()


def test_critical_mid_probability_uses_exactly_one_context_chance_roll() -> None:
    context = make_context(77)
    _critical_system(context, 0.5).calculate(context, request())

    assert context.random.chance_calls == 1
    assert context.random.randint_calls == 2
