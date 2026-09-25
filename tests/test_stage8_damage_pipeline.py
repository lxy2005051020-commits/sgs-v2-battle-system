from __future__ import annotations

import ast
import math
from dataclasses import fields
from pathlib import Path

import pytest

from sgs_v2.battle_core import (
    AttributeSystem,
    BattleContext,
    BattleSystems,
    DamageDefensePolicy,
    DamageEffect,
    DamageFormulaContext,
    DamageFormulaPolicyContribution,
    DamageModifierContribution,
    DamageModifierKind,
    DamageModifierOperation,
    DamageModifierPhase,
    DamagePreventionContribution,
    DamagePreventionRuleKind,
    DamageRequest,
    DamageResult,
    DamageRuleFamily,
    DamageSourceType,
    DamageSystem,
    DamageType,
    EmptyStateRuntimeParams,
    EventBus,
    EventType,
    HitPreventionCategory,
    HitRuleContribution,
    HitRuleKind,
    InvalidDamageParticipantError,
    LineupPosition,
    OfficialStateId,
    RandomSystem,
    RuleContributionSource,
    Stage8ModifierParams,
    Stage8PierceParams,
    Stage8ProbabilityParams,
    StageEvaluationStatus,
    StateDamageRuleProvider,
    StateDefinition,
    StateLifecycleSystem,
    StateRuleAdapter,
    StateRuleBinding,
    UnitRuntime,
    WeaponBaseDamageFormula,
    default_stage8_official_binding_state_ids,
    register_official_state_definitions,
)
from sgs_v2.battle_core.damage_state_rule_bindings import (
    DEFAULT_STAGE8_STATE_RULE_BINDINGS,
)


DEFER_STAGE8_STATES = {
    "evasion",
    "barrier",
    "sure_hit",
    "defense_pierce",
    "vigilance",
    "critical",
    "strategy_critical",
    "damage_reduction_pierce",
    "rebellion",
}


class CountingRandomSystem(RandomSystem):
    def __init__(self, seed: int = 7) -> None:
        super().__init__(seed)
        self.randint_calls = 0
        self.chance_calls = 0

    def randint(self, a: int, b: int) -> int:
        self.randint_calls += 1
        return super().randint(a, b)

    def chance(self, probability: float) -> bool:
        self.chance_calls += 1
        return super().chance(probability)


def make_context(*, seed: int = 7) -> BattleContext:
    context = BattleContext(
        battle_id=f"stage8-{seed}",
        units={
            "a1": UnitRuntime(
                "a1", "A1", "A", 10000, 10000, 300, 200, 100,
                lineup_position=LineupPosition.COMMANDER,
                intelligence=280,
            ),
            "a2": UnitRuntime(
                "a2", "A2", "A", 10000, 10000, 250, 180, 90,
                lineup_position=LineupPosition.DEPUTY_1,
                intelligence=240,
            ),
            "b1": UnitRuntime(
                "b1", "B1", "B", 10000, 10000, 200, 200, 80,
                lineup_position=LineupPosition.COMMANDER,
                intelligence=220,
            ),
        },
        event_bus=EventBus(),
        random=CountingRandomSystem(seed),
    )
    register_official_state_definitions(context.states)
    return context


def request(
    *,
    damage_type: DamageType = DamageType.WEAPON,
    source_type: DamageSourceType = DamageSourceType.SKILL,
    coefficient: float = 1.0,
) -> DamageRequest:
    return DamageRequest(
        source_id="a1",
        target_id="b1",
        damage_type=damage_type,
        source_type=source_type,
        coefficient=coefficient,
        source_skill_id="stage8-test-skill",
    )


def system_with_provider(provider: StateDamageRuleProvider) -> DamageSystem:
    return DamageSystem(
        AttributeSystem(),
        weapon_random_percent_range=(90, 90),
        weapon_low_damage_floor_range=(5, 5),
        strategy_random_percent_range=(90, 90),
        strategy_low_damage_floor_range=(5, 5),
        rule_provider=provider,
    )


def register_synthetic(
    context: BattleContext,
    state_id: str,
    params_type: type = EmptyStateRuntimeParams,
) -> None:
    context.states.register_definition(
        StateDefinition(
            state_id=state_id,
            name=state_id,
            runtime_params_type=params_type,
        )
    )


def apply_synthetic(
    context: BattleContext,
    state_id: str,
    *,
    owner_id: str,
    source_id: str | None = None,
    source_skill_id: str | None = None,
    runtime_params=None,
):
    return StateLifecycleSystem().apply(
        context,
        state_id=state_id,
        owner_id=owner_id,
        source_id=source_id,
        source_skill_id=source_skill_id,
        runtime_params=runtime_params,
    )


def barrier_builder(instance, source, damage_request):
    if instance.owner_id != damage_request.target_id:
        return None
    return HitRuleContribution(
        kind=HitRuleKind.DETERMINISTIC_PREVENTION,
        category=HitPreventionCategory.IMMUNITY_LIKE,
        source=source,
        order_key=source.origin_key,
    )


def evasion_builder(instance, source, damage_request):
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


def bypass_builder(instance, source, damage_request):
    if instance.owner_id != damage_request.source_id:
        return None
    return HitRuleContribution(
        kind=HitRuleKind.BYPASS,
        bypass_categories=frozenset(
            {
                HitPreventionCategory.IMMUNITY_LIKE,
                HitPreventionCategory.EVASION_LIKE,
            }
        ),
        source=source,
        order_key=source.origin_key,
    )


def ignore_defense_builder(instance, source, damage_request):
    if instance.owner_id != damage_request.source_id:
        return None
    return DamageFormulaPolicyContribution(
        defense_policy=DamageDefensePolicy.IGNORE_RELEVANT_TARGET_DEFENSE,
        source=source,
        order_key=source.origin_key,
    )


def critical_builder(instance, source, damage_request):
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


def modifier_builder(
    *,
    phase: DamageModifierPhase,
    kind: DamageModifierKind,
):
    def build(instance, source, damage_request):
        params = instance.runtime_params
        assert isinstance(params, Stage8ModifierParams)
        return DamageModifierContribution(
            phase=phase,
            kind=kind,
            operation=DamageModifierOperation.MULTIPLY_FACTOR,
            operand=params.operand,
            probability=params.probability,
            source=source,
            order_key=source.origin_key,
        )

    return build


def pierce_builder(instance, source, damage_request):
    params = instance.runtime_params
    assert isinstance(params, Stage8PierceParams)
    return DamageModifierContribution(
        phase=DamageModifierPhase.INCOMING,
        kind=DamageModifierKind.REDUCTION_PIERCE,
        operation=DamageModifierOperation.REDUCTION_PIERCE,
        operand=params.rate,
        source=source,
        order_key=source.origin_key,
    )


def binding(state_id: str, family: DamageRuleFamily, builder) -> StateRuleBinding:
    return StateRuleBinding(
        state_id=state_id,
        adapters=(
            StateRuleAdapter(
                adapter_key=f"{state_id}-adapter",
                family=family,
                build=builder,
            ),
        ),
    )


def test_default_production_binding_excludes_stage11_weakness() -> None:
    assert default_stage8_official_binding_state_ids() == set()
    assert {b.state_id for b in DEFAULT_STAGE8_STATE_RULE_BINDINGS}.isdisjoint(
        DEFER_STAGE8_STATES | {OfficialStateId.WEAKNESS.value}
    )


def test_provider_is_read_only_deterministic_and_preserves_state_provenance() -> None:
    context = make_context()
    register_synthetic(context, "synthetic_barrier")
    first = apply_synthetic(
        context,
        "synthetic_barrier",
        owner_id="b1",
        source_id="a2",
        source_skill_id="support-skill",
    )
    provider = StateDamageRuleProvider(
        (binding("synthetic_barrier", DamageRuleFamily.HIT, barrier_builder),)
    )
    before_events = len(context.event_bus.history)
    before_random = context.random.randint_calls, context.random.chance_calls
    before_states = tuple(instance.instance_id for instance in context.states.find())

    rules_1 = provider.collect(context, request())
    rules_2 = provider.collect(context, request())

    assert rules_1 == rules_2
    assert len(rules_1.hit_contributions) == 1
    contribution = rules_1.hit_contributions[0]
    assert contribution.source.owner_id == "b1"
    assert contribution.source.applied_by_unit_id == "a2"
    assert contribution.source.source_skill_id == "support-skill"
    assert contribution.source.source_state_id == "synthetic_barrier"
    assert contribution.source.source_state_instance_id == first.instance_id
    assert len(context.event_bus.history) == before_events
    assert (context.random.randint_calls, context.random.chance_calls) == before_random
    assert tuple(instance.instance_id for instance in context.states.find()) == before_states


def test_provider_rejects_duplicate_state_bindings_and_duplicate_adapter_keys() -> None:
    adapter = StateRuleAdapter(
        adapter_key="same",
        family=DamageRuleFamily.HIT,
        build=barrier_builder,
    )
    with pytest.raises(ValueError, match="duplicate adapter_key"):
        StateRuleBinding("synthetic", (adapter, adapter))
    one = StateRuleBinding("synthetic", (adapter,))
    with pytest.raises(ValueError, match="duplicate state_id"):
        StateDamageRuleProvider((one, one))


def test_weakness_zeroes_after_formula_without_prevention_short_circuit() -> None:
    context = make_context(seed=31)
    StateLifecycleSystem().apply(
        context,
        state_id=OfficialStateId.WEAKNESS.value,
        owner_id="a1",
        source_id="a2",
        source_skill_id="weakness-source",
    )
    systems = BattleSystems()
    before_events = len(context.event_bus.history)

    result = systems.damage_system.calculate(context, request())

    assert result.prevented is False
    assert result.prevented_by_state_id is None
    assert result.zeroed_by_state_id == OfficialStateId.WEAKNESS.value
    assert result.base_damage > 0
    assert result.scaled_damage > 0
    assert result.final_damage == 0
    assert context.random.randint_calls > 0
    assert context.random.chance_calls == 0
    assert len(context.event_bus.history) == before_events
    assert result.pipeline_trace is not None
    trace = result.pipeline_trace
    assert trace.prevention_status is StageEvaluationStatus.EXECUTED
    assert trace.hit_status is StageEvaluationStatus.EXECUTED
    assert trace.formula_policy_status is StageEvaluationStatus.EXECUTED
    assert trace.modifier_status is StageEvaluationStatus.EXECUTED


def test_synthetic_hit_probability_zero_and_one_do_not_consume_rng() -> None:
    provider = StateDamageRuleProvider(
        (binding("synthetic_evasion", DamageRuleFamily.HIT, evasion_builder),)
    )

    zero = make_context(seed=32)
    register_synthetic(zero, "synthetic_evasion", Stage8ProbabilityParams)
    apply_synthetic(
        zero,
        "synthetic_evasion",
        owner_id="b1",
        runtime_params=Stage8ProbabilityParams(0.0),
    )
    result_zero = system_with_provider(provider).calculate(zero, request())
    assert result_zero.prevented is False
    assert zero.random.chance_calls == 0
    assert zero.random.randint_calls == 2

    one = make_context(seed=33)
    register_synthetic(one, "synthetic_evasion", Stage8ProbabilityParams)
    apply_synthetic(
        one,
        "synthetic_evasion",
        owner_id="b1",
        runtime_params=Stage8ProbabilityParams(1.0),
    )
    result_one = system_with_provider(provider).calculate(one, request())
    assert result_one.prevented is True
    assert one.random.chance_calls == 0
    assert one.random.randint_calls == 0


def test_synthetic_hit_mid_probability_uses_exactly_one_context_chance_roll() -> None:
    context = make_context(seed=34)
    register_synthetic(context, "synthetic_evasion", Stage8ProbabilityParams)
    apply_synthetic(
        context,
        "synthetic_evasion",
        owner_id="b1",
        runtime_params=Stage8ProbabilityParams(0.5),
    )
    provider = StateDamageRuleProvider(
        (binding("synthetic_evasion", DamageRuleFamily.HIT, evasion_builder),)
    )

    system_with_provider(provider).calculate(context, request())
    assert context.random.chance_calls == 1


def test_synthetic_bypass_skips_barrier_and_evasion_without_evasion_rng() -> None:
    context = make_context(seed=35)
    register_synthetic(context, "synthetic_barrier")
    register_synthetic(context, "synthetic_evasion", Stage8ProbabilityParams)
    register_synthetic(context, "synthetic_bypass")
    apply_synthetic(context, "synthetic_barrier", owner_id="b1")
    apply_synthetic(
        context,
        "synthetic_evasion",
        owner_id="b1",
        runtime_params=Stage8ProbabilityParams(0.5),
    )
    apply_synthetic(context, "synthetic_bypass", owner_id="a1")
    provider = StateDamageRuleProvider(
        (
            binding("synthetic_barrier", DamageRuleFamily.HIT, barrier_builder),
            binding("synthetic_evasion", DamageRuleFamily.HIT, evasion_builder),
            binding("synthetic_bypass", DamageRuleFamily.HIT, bypass_builder),
        )
    )

    result = system_with_provider(provider).calculate(context, request())
    assert result.prevented is False
    assert context.random.chance_calls == 0
    assert context.random.randint_calls == 2


def test_normal_formula_context_is_differentially_identical_and_rng_equivalent() -> None:
    context_old = make_context(seed=41)
    context_new = make_context(seed=41)
    formula = WeaponBaseDamageFormula(AttributeSystem())

    old = formula.calculate(
        context_old,
        context_old.get_unit("a1"),
        context_old.get_unit("b1"),
    )
    new = formula.calculate(
        context_new,
        context_new.get_unit("a1"),
        context_new.get_unit("b1"),
        formula_context=DamageFormulaContext(DamageDefensePolicy.NORMAL),
    )

    assert old == new
    assert context_old.random.randint_calls == context_new.random.randint_calls == 2


def test_synthetic_formula_policy_ignores_only_target_relevant_defense() -> None:
    normal_context = make_context(seed=42)
    ignore_context = make_context(seed=42)
    register_synthetic(ignore_context, "synthetic_ignore_defense")
    apply_synthetic(ignore_context, "synthetic_ignore_defense", owner_id="a1")
    provider = StateDamageRuleProvider(
        (
            binding(
                "synthetic_ignore_defense",
                DamageRuleFamily.FORMULA_POLICY,
                ignore_defense_builder,
            ),
        )
    )

    normal = BattleSystems(
        weapon_random_percent_range=(90, 90),
        weapon_low_damage_floor_range=(5, 5),
    ).damage_system.calculate(normal_context, request())
    ignored = system_with_provider(provider).calculate(ignore_context, request())

    assert ignored.base_damage > normal.base_damage
    assert ignore_context.random.randint_calls == normal_context.random.randint_calls == 2
    assert ignored.pipeline_trace.formula_policy_result.formula_context.defense_policy is (
        DamageDefensePolicy.IGNORE_RELEVANT_TARGET_DEFENSE
    )


def test_modifier_phase_order_and_trace_are_deterministic() -> None:
    context = make_context(seed=43)
    specs = (
        ("incoming", DamageModifierPhase.INCOMING, DamageModifierKind.INCOMING_INCREASE, 1.1),
        ("critical_like", DamageModifierPhase.CRITICAL, DamageModifierKind.CRITICAL_MULTIPLIER, 2.0),
        ("outgoing", DamageModifierPhase.OUTGOING, DamageModifierKind.OUTGOING_INCREASE, 1.2),
        ("single", DamageModifierPhase.SINGLE_HIT, DamageModifierKind.SINGLE_HIT_ADJUSTMENT, 0.5),
    )
    bindings = []
    for state_id, phase, kind, operand in specs:
        register_synthetic(context, state_id, Stage8ModifierParams)
        apply_synthetic(
            context,
            state_id,
            owner_id="a1" if phase is not DamageModifierPhase.INCOMING else "b1",
            runtime_params=Stage8ModifierParams(operand),
        )
        bindings.append(binding(state_id, DamageRuleFamily.MODIFIER, modifier_builder(phase=phase, kind=kind)))

    result = system_with_provider(StateDamageRuleProvider(tuple(bindings))).calculate(
        context,
        request(),
    )
    applied = result.pipeline_trace.modifier_result.applied_modifiers
    assert [item.contribution.phase for item in applied] == [
        DamageModifierPhase.CRITICAL,
        DamageModifierPhase.OUTGOING,
        DamageModifierPhase.INCOMING,
        DamageModifierPhase.SINGLE_HIT,
    ]
    for previous, current in zip(applied, applied[1:]):
        assert previous.output_damage == current.input_damage
    assert result.final_damage == max(1, int(applied[-1].output_damage))


def test_synthetic_critical_wrong_damage_type_does_not_roll_rng() -> None:
    context = make_context(seed=44)
    register_synthetic(context, "synthetic_critical", Stage8ProbabilityParams)
    apply_synthetic(
        context,
        "synthetic_critical",
        owner_id="a1",
        runtime_params=Stage8ProbabilityParams(0.5),
    )
    provider = StateDamageRuleProvider(
        (binding("synthetic_critical", DamageRuleFamily.MODIFIER, critical_builder),)
    )

    result = system_with_provider(provider).calculate(
        context,
        request(damage_type=DamageType.STRATEGY),
    )
    assert result.prevented is False
    assert context.random.chance_calls == 0
    assert context.random.randint_calls == 2
    assert result.pipeline_trace.modifier_result.applied_modifiers == ()


def test_synthetic_critical_probability_one_doubles_without_chance_rng() -> None:
    base_context = make_context(seed=45)
    critical_context = make_context(seed=45)
    register_synthetic(critical_context, "synthetic_critical", Stage8ProbabilityParams)
    apply_synthetic(
        critical_context,
        "synthetic_critical",
        owner_id="a1",
        runtime_params=Stage8ProbabilityParams(1.0),
    )
    provider = StateDamageRuleProvider(
        (binding("synthetic_critical", DamageRuleFamily.MODIFIER, critical_builder),)
    )

    base = BattleSystems(
        weapon_random_percent_range=(90, 90),
        weapon_low_damage_floor_range=(5, 5),
    ).damage_system.calculate(base_context, request())
    critical = system_with_provider(provider).calculate(critical_context, request())
    assert critical.final_damage == int(base.scaled_damage * 2.0)
    assert critical_context.random.chance_calls == 0


def test_reduction_pierce_only_changes_incoming_reduction_operand() -> None:
    context = make_context(seed=46)
    register_synthetic(context, "incoming_reduction", Stage8ModifierParams)
    register_synthetic(context, "incoming_increase", Stage8ModifierParams)
    register_synthetic(context, "pierce", Stage8PierceParams)
    apply_synthetic(
        context,
        "incoming_reduction",
        owner_id="b1",
        runtime_params=Stage8ModifierParams(0.8),
    )
    apply_synthetic(
        context,
        "incoming_increase",
        owner_id="b1",
        runtime_params=Stage8ModifierParams(1.2),
    )
    pierce_instance = apply_synthetic(
        context,
        "pierce",
        owner_id="a1",
        runtime_params=Stage8PierceParams(0.5),
    )
    provider = StateDamageRuleProvider(
        (
            binding(
                "incoming_reduction",
                DamageRuleFamily.MODIFIER,
                modifier_builder(
                    phase=DamageModifierPhase.INCOMING,
                    kind=DamageModifierKind.INCOMING_REDUCTION,
                ),
            ),
            binding(
                "incoming_increase",
                DamageRuleFamily.MODIFIER,
                modifier_builder(
                    phase=DamageModifierPhase.INCOMING,
                    kind=DamageModifierKind.INCOMING_INCREASE,
                ),
            ),
            binding("pierce", DamageRuleFamily.MODIFIER, pierce_builder),
        )
    )

    result = system_with_provider(provider).calculate(context, request())
    applied = result.pipeline_trace.modifier_result.applied_modifiers
    reduction = next(
        item for item in applied
        if item.contribution.kind is DamageModifierKind.INCOMING_REDUCTION
    )
    increase = next(
        item for item in applied
        if item.contribution.kind is DamageModifierKind.INCOMING_INCREASE
    )
    assert reduction.original_operand == pytest.approx(0.8)
    assert reduction.effective_operand == pytest.approx(0.9)
    assert reduction.pierce_contributor.source_state_instance_id == pierce_instance.instance_id
    assert increase.original_operand == increase.effective_operand == pytest.approx(1.2)
    assert increase.pierce_contributor is None


def test_dead_source_and_dead_target_fail_before_rng_event_or_rule_discovery() -> None:
    class FailingProvider:
        provider_key = "failing"

        def collect(self, context, damage_request):
            raise AssertionError("rule discovery must not run for dead participant")

    for dead_id in ("a1", "b1"):
        context = make_context(seed=47)
        context.get_unit(dead_id).troops = 0
        before_events = len(context.event_bus.history)
        system = DamageSystem(AttributeSystem(), rule_provider=FailingProvider())
        with pytest.raises(InvalidDamageParticipantError):
            system.calculate(context, request())
        assert context.random.randint_calls == 0
        assert context.random.chance_calls == 0
        assert len(context.event_bus.history) == before_events


def test_public_numeric_boundaries_reject_bool_nan_inf_and_negative() -> None:
    bad_coefficients = [True, math.nan, math.inf, -math.inf, -0.1]
    for value in bad_coefficients:
        with pytest.raises((TypeError, ValueError)):
            request(coefficient=value)
        with pytest.raises((TypeError, ValueError)):
            DamageEffect(
                source_id="a1",
                target_id="b1",
                damage_type=DamageType.WEAPON,
                source_type=DamageSourceType.SKILL,
                coefficient=value,
            )

    for value in (True, math.nan, math.inf, -math.inf, -0.1, 1.1):
        with pytest.raises((TypeError, ValueError)):
            Stage8ProbabilityParams(value)
        with pytest.raises((TypeError, ValueError)):
            Stage8PierceParams(value)

    for value in (True, math.nan, math.inf, -math.inf, -0.1):
        with pytest.raises((TypeError, ValueError)):
            Stage8ModifierParams(value)


def test_damage_result_positional_compatibility_keeps_pipeline_trace_at_tail() -> None:
    names = [field.name for field in fields(DamageResult)]
    assert names[-1] == "pipeline_trace"
    legacy = DamageResult(
        "a1",
        "b1",
        DamageType.WEAPON,
        DamageSourceType.SKILL,
        1.0,
        100.0,
        100.0,
        100,
    )
    assert legacy.pipeline_trace is None


def test_manual_and_battle_systems_damage_construction_use_same_default_pipeline() -> None:
    left = make_context(seed=48)
    right = make_context(seed=48)
    manual = DamageSystem(
        AttributeSystem(),
        weapon_random_percent_range=(90, 90),
        weapon_low_damage_floor_range=(5, 5),
    )
    canonical = BattleSystems(
        weapon_random_percent_range=(90, 90),
        weapon_low_damage_floor_range=(5, 5),
    ).damage_system

    assert manual.calculate(left, request()) == canonical.calculate(right, request())


def test_damage_calculation_never_publishes_battle_fact() -> None:
    context = make_context(seed=49)
    before = context.event_bus.history
    BattleSystems().damage_system.calculate(context, request())
    assert context.event_bus.history == before


def test_normal_attack_event_order_regression_is_preserved() -> None:
    context = make_context(seed=50)
    result = BattleSystems().normal_attack_system.execute(context, context.get_unit("a1"))
    assert result.damage is not None
    combat_events = [
        event.event_type
        for event in context.event_bus.history
        if event.event_type in {EventType.NORMAL_ATTACK, EventType.DAMAGE_DEALT}
    ]
    assert combat_events == [EventType.NORMAL_ATTACK, EventType.DAMAGE_DEALT]


def test_stage8_architecture_resolvers_do_not_reference_official_ids_or_side_effect_systems() -> None:
    core = Path(__file__).parents[1] / "sgs_v2" / "battle_core"
    resolver_files = (
        "damage_prevention_system.py",
        "hit_resolution_system.py",
        "damage_formula_policy_system.py",
        "damage_modifier_system.py",
    )
    forbidden_import_modules = {
        "official_state_catalog",
        "troop_system",
        "damage_resolution_system",
        "effect_executor",
        "random",
    }
    for filename in resolver_files:
        tree = ast.parse((core / filename).read_text(encoding="utf-8"))
        imports = {
            alias.name.split(".")[-1]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imports.update(
            (node.module or "").split(".")[-1]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        )
        assert imports.isdisjoint(forbidden_import_modules)
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
        assert not any(
            isinstance(call.func, ast.Attribute) and call.func.attr == "publish"
            for call in calls
        )


def test_evidence_matrix_verdicts_and_defer_binding_guard() -> None:
    matrix = (
        Path(__file__).parents[1]
        / "stages"
        / "stage8"
        / "STAGE8_EVIDENCE_MATRIX.md"
    ).read_text(encoding="utf-8")
    verdicts = []
    for line in matrix.splitlines():
        if not line.startswith("| `") or line.startswith("| `state_id`"):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if len(cells) >= 2:
            verdicts.append((cells[0], cells[-1]))

    assert verdicts
    assert {verdict for _, verdict in verdicts} <= {"PASS_STAGE8", "DEFER"}
    deferred = {state_id for state_id, verdict in verdicts if verdict == "DEFER"}
    assert DEFER_STAGE8_STATES <= deferred
    assert default_stage8_official_binding_state_ids().isdisjoint(deferred)
