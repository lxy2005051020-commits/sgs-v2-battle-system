from __future__ import annotations

import pytest

from sgs_v2.battle_core import (
    AttributeSystem, BattleContext, DamageAllowedResult, DamageDefensePolicy,
    DamageEffect, DamageFormulaContext, DamageFormulaPolicyContribution,
    DamageFormulaPolicyResult, DamageFormulaPolicySystem, DamageModifierContribution,
    DamageModifierKind, DamageModifierOperation, DamageModifierPhase,
    DamageModifierResult, DamageModifierSystem, DamagePipelineTrace,
    DamagePreventionContribution, DamagePreventionRuleKind, DamagePreventionSystem,
    DamageRequest, DamageResult, DamageRuleCollection, DamageRuleFamily,
    DamageSourceType, DamageSystem, DamageType, EventBus, HitAllowedResult,
    HitPreventionCategory, HitResolutionSystem, HitRuleContribution, HitRuleKind,
    InvalidDamageParticipantError, LineupPosition, RandomSystem,
    RuleContributionSource, StageEvaluationStatus, StateRuleAdapter,
    StateRuleBinding, UnitRuntime,
)


class CountingRandomSystem(RandomSystem):
    def __init__(self, seed: int = 801) -> None:
        super().__init__(seed)
        self.randint_calls = 0
        self.chance_calls = 0

    def randint(self, a: int, b: int) -> int:
        self.randint_calls += 1
        return super().randint(a, b)

    def chance(self, probability: float) -> bool:
        self.chance_calls += 1
        return super().chance(probability)


def make_context(seed: int = 801) -> BattleContext:
    return BattleContext(
        battle_id=f"stage8-audit-repair-{seed}",
        units={
            "a": UnitRuntime("a", "A", "A", 10000, 10000, 300, 180, 100,
                             lineup_position=LineupPosition.COMMANDER, intelligence=300),
            "b": UnitRuntime("b", "B", "B", 10000, 10000, 200, 200, 90,
                             lineup_position=LineupPosition.COMMANDER, intelligence=250),
        },
        event_bus=EventBus(),
        random=CountingRandomSystem(seed),
    )


def req(source_id: str = "a", target_id: str = "b") -> DamageRequest:
    return DamageRequest(source_id, target_id, DamageType.WEAPON, DamageSourceType.SKILL)


def src(key: str = "audit") -> RuleContributionSource:
    return RuleContributionSource(None, None, None, None, None, key)


def prevention(key: str = "p") -> DamagePreventionContribution:
    return DamagePreventionContribution(
        DamagePreventionRuleKind.GENERIC_PREVENTION, src(key), key
    )


def modifier(probability: float = 1.0, *, key: str = "m",
             phase: DamageModifierPhase = DamageModifierPhase.CRITICAL) -> DamageModifierContribution:
    return DamageModifierContribution(
        phase=phase,
        kind=DamageModifierKind.CRITICAL_MULTIPLIER,
        operation=DamageModifierOperation.MULTIPLY_FACTOR,
        operand=2.0,
        source=src(key),
        order_key=key,
        probability=probability,
    )


def test_collection_and_binding_canonicalize_mutable_inputs() -> None:
    p = prevention()
    values = [p]
    rules = DamageRuleCollection(prevention_contributions=values)
    values.clear()
    assert isinstance(rules.prevention_contributions, tuple)
    assert rules.prevention_contributions == (p,)

    adapter = StateRuleAdapter(
        "a", DamageRuleFamily.PREVENTION,
        lambda instance, source, damage_request: None,
    )
    adapters = [adapter]
    binding = StateRuleBinding("synthetic", adapters)
    adapters.clear()
    assert isinstance(binding.adapters, tuple)
    assert binding.adapters == (adapter,)


@pytest.mark.parametrize("field", [
    "prevention_contributions", "hit_contributions",
    "formula_policy_contributions", "modifier_contributions",
])
def test_collection_rejects_wrong_element_types(field: str) -> None:
    with pytest.raises(TypeError):
        DamageRuleCollection(**{field: [object()]})


def test_binding_rejects_wrong_adapter_type() -> None:
    with pytest.raises(TypeError, match="StateRuleAdapter"):
        StateRuleBinding("synthetic", [object()])


def test_collection_duplicate_order_keys_fail_at_construction() -> None:
    with pytest.raises(ValueError, match="duplicate order_key"):
        DamageRuleCollection(prevention_contributions=[prevention("x"), prevention("x")])
    with pytest.raises(ValueError, match="duplicate order_key"):
        DamageRuleCollection(modifier_contributions=[modifier(key="x"), modifier(key="x")])
    rules = DamageRuleCollection(modifier_contributions=[
        modifier(key="x", phase=DamageModifierPhase.CRITICAL),
        DamageModifierContribution(
            DamageModifierPhase.OUTGOING, DamageModifierKind.OUTGOING_INCREASE,
            DamageModifierOperation.MULTIPLY_FACTOR, 1.1, src("x"), "x"
        ),
    ])
    assert len(rules.modifier_contributions) == 2


def test_damage_system_uses_immutable_provider_snapshot() -> None:
    class Provider:
        provider_key = "audit-provider"
        def __init__(self) -> None:
            self.items = [prevention("provider")]
            self.calls = 0
        def collect(self, context, damage_request):
            self.calls += 1
            out = DamageRuleCollection(prevention_contributions=self.items)
            self.items.clear()
            return out

    context = make_context(802)
    provider = Provider()
    result = DamageSystem(AttributeSystem(), rule_provider=provider).calculate(context, req())
    assert provider.calls == 1
    assert result.prevented and result.final_damage == 0
    assert context.random.randint_calls == context.random.chance_calls == 0


@pytest.mark.parametrize("builder", [
    lambda: StateRuleAdapter("bad", "PREVENTION", lambda i, s, r: None),
    lambda: DamagePreventionContribution("BAD", src(), "p"),
    lambda: HitRuleContribution("BAD", src(), "h", category=HitPreventionCategory.IMMUNITY_LIKE),
    lambda: HitRuleContribution(HitRuleKind.DETERMINISTIC_PREVENTION, src(), "h", category="IMMUNITY_LIKE"),
    lambda: DamageFormulaContext("NORMAL"),
    lambda: DamageFormulaPolicyContribution("NORMAL", src(), "f"),
    lambda: DamageModifierContribution("CRITICAL", DamageModifierKind.CRITICAL_MULTIPLIER,
                                       DamageModifierOperation.MULTIPLY_FACTOR, 2.0, src(), "m"),
    lambda: DamageModifierContribution(DamageModifierPhase.CRITICAL, "CRITICAL_MULTIPLIER",
                                       DamageModifierOperation.MULTIPLY_FACTOR, 2.0, src(), "m"),
    lambda: DamageModifierContribution(DamageModifierPhase.CRITICAL, DamageModifierKind.CRITICAL_MULTIPLIER,
                                       "MULTIPLY_FACTOR", 2.0, src(), "m"),
    lambda: DamageRequest("a", "b", "WEAPON", DamageSourceType.SKILL),
    lambda: DamageRequest("a", "b", DamageType.WEAPON, "SKILL"),
    lambda: DamageEffect("a", "b", "WEAPON", DamageSourceType.SKILL),
])
def test_string_pseudo_enums_are_rejected(builder) -> None:
    with pytest.raises(TypeError):
        builder()


@pytest.mark.parametrize("probability", [0.0, 1.0, 0.5])
def test_unsupported_modifier_operation_fails_before_rng(probability: float) -> None:
    context = make_context(803)
    bad = modifier(probability, key=f"bad-{probability}")
    object.__setattr__(bad, "operation", "ADD_FLAT")
    rules = DamageRuleCollection(modifier_contributions=[bad])
    with pytest.raises(TypeError, match="DamageModifierOperation"):
        DamageModifierSystem().resolve(context, req(), rules, 100.0)
    assert context.random.chance_calls == context.random.randint_calls == 0


@pytest.mark.parametrize("probability,calls", [(0.0, 0), (1.0, 0), (0.5, 1)])
def test_valid_modifier_probability_rng_contract(probability: float, calls: int) -> None:
    context = make_context(804)
    DamageModifierSystem().resolve(
        context, req(), DamageRuleCollection(modifier_contributions=[modifier(probability)]), 100.0
    )
    assert context.random.chance_calls == calls
    assert context.random.randint_calls == 0


def _trace_kwargs() -> dict[str, object]:
    return {
        "prevention_status": StageEvaluationStatus.EXECUTED,
        "prevention_result": DamageAllowedResult(()),
        "hit_status": StageEvaluationStatus.EXECUTED,
        "hit_result": HitAllowedResult(()),
        "formula_policy_status": StageEvaluationStatus.EXECUTED,
        "formula_policy_result": DamageFormulaPolicyResult(DamageFormulaContext(), ()),
        "modifier_status": StageEvaluationStatus.EXECUTED,
        "modifier_result": DamageModifierResult(100.0, 100.0, ()),
    }


@pytest.mark.parametrize("bad", ["EXECUTED", "NOT_EVALUATED", None, object()])
def test_trace_rejects_non_enum_status(bad: object) -> None:
    kwargs = _trace_kwargs()
    kwargs["prevention_status"] = bad
    with pytest.raises(TypeError, match="StageEvaluationStatus"):
        DamagePipelineTrace(**kwargs)


def test_trace_status_result_invariants_and_result_type() -> None:
    kwargs = _trace_kwargs(); kwargs["prevention_result"] = None
    with pytest.raises(ValueError, match="EXECUTED requires a result"):
        DamagePipelineTrace(**kwargs)
    kwargs = _trace_kwargs(); kwargs["modifier_status"] = StageEvaluationStatus.NOT_EVALUATED
    with pytest.raises(ValueError, match="NOT_EVALUATED requires result=None"):
        DamagePipelineTrace(**kwargs)
    kwargs = _trace_kwargs(); kwargs["hit_result"] = kwargs["formula_policy_result"]
    with pytest.raises(TypeError, match="hit_result"):
        DamagePipelineTrace(**kwargs)


def test_canonical_normal_trace_still_valid() -> None:
    trace = DamagePipelineTrace(**_trace_kwargs())
    assert trace.modifier_status is StageEvaluationStatus.EXECUTED


class CountingProvider:
    provider_key = "audit-counting"
    def __init__(self) -> None: self.calls = 0
    def collect(self, context, damage_request):
        self.calls += 1
        return DamageRuleCollection()


class CountingFormula:
    def __init__(self) -> None: self.calls = 0
    def calculate(self, context, source, target, **kwargs):
        self.calls += 1
        return 100


def assert_invalid_participant(context: BattleContext, damage_request: DamageRequest) -> None:
    provider = CountingProvider()
    formula = CountingFormula()
    system = DamageSystem(AttributeSystem(), rule_provider=provider)
    system._weapon_formula = formula
    before_events = tuple(context.event_bus.history)
    before_troops = {k: v.troops for k, v in context.units.items()}
    with pytest.raises(InvalidDamageParticipantError):
        system.calculate(context, damage_request)
    assert provider.calls == formula.calls == 0
    assert context.random.randint_calls == context.random.chance_calls == 0
    assert tuple(context.event_bus.history) == before_events
    assert {k: v.troops for k, v in context.units.items()} == before_troops


@pytest.mark.parametrize("mode", ["missing_source", "missing_target", "dead_source", "dead_target"])
def test_invalid_participant_short_circuits_entire_pipeline(mode: str) -> None:
    context = make_context(805)
    damage_request = req()
    if mode == "missing_source": damage_request = req("missing", "b")
    elif mode == "missing_target": damage_request = req("a", "missing")
    elif mode == "dead_source": context.get_unit("a").troops = 0
    else: context.get_unit("b").troops = 0
    assert_invalid_participant(context, damage_request)
