from __future__ import annotations

import pytest

from sgs_v2.battle_core import (
    BattleContext,
    DamageDefensePolicy,
    DamageFormulaPolicyContribution,
    DamageFormulaPolicySystem,
    DamageModifierContribution,
    DamageModifierKind,
    DamageModifierOperation,
    DamageModifierPhase,
    DamageModifierSystem,
    DamageRequest,
    DamageRuleCollection,
    DamageSourceType,
    DamageType,
    EventBus,
    HitPreventionCategory,
    HitResolutionSystem,
    HitRuleContribution,
    HitRuleKind,
    LineupPosition,
    RandomSystem,
    RuleContributionSource,
    UnitRuntime,
)


class CountingRandomSystem(RandomSystem):
    def __init__(self, seed: int = 821) -> None:
        super().__init__(seed)
        self.randint_calls = 0
        self.chance_calls = 0

    def randint(self, a: int, b: int) -> int:
        self.randint_calls += 1
        return super().randint(a, b)

    def chance(self, probability: float) -> bool:
        self.chance_calls += 1
        return super().chance(probability)


class NonCanonicalFrozenScope(frozenset):
    def __contains__(self, item: object) -> bool:
        return True


def semantic_scope(items: list[object], alias: set[object]) -> frozenset:
    class MutableSemanticFrozenScope(frozenset):
        def __contains__(self, item: object) -> bool:
            return item in alias

    return MutableSemanticFrozenScope(items)


def make_context(seed: int = 821) -> BattleContext:
    return BattleContext(
        battle_id=f"stage8-second-reaudit-{seed}",
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


def req() -> DamageRequest:
    return DamageRequest("a", "b", DamageType.WEAPON, DamageSourceType.SKILL)


def src(key: str) -> RuleContributionSource:
    return RuleContributionSource(None, None, None, None, None, key)


def hit_prevention(key: str) -> HitRuleContribution:
    return HitRuleContribution(
        kind=HitRuleKind.DETERMINISTIC_PREVENTION,
        source=src(key),
        order_key=key,
        category=HitPreventionCategory.IMMUNITY_LIKE,
    )


def formula_policy(key: str) -> DamageFormulaPolicyContribution:
    return DamageFormulaPolicyContribution(
        defense_policy=DamageDefensePolicy.NORMAL,
        source=src(key),
        order_key=key,
    )


def modifier(probability: float, key: str) -> DamageModifierContribution:
    return DamageModifierContribution(
        phase=DamageModifierPhase.CRITICAL,
        kind=DamageModifierKind.CRITICAL_MULTIPLIER,
        operation=DamageModifierOperation.MULTIPLY_FACTOR,
        operand=2.0,
        source=src(key),
        order_key=key,
        probability=probability,
    )


def assert_zero_rng(context: BattleContext) -> None:
    assert context.random.chance_calls == 0
    assert context.random.randint_calls == 0


def test_hit_runtime_rejects_frozenset_subclass_damage_types_before_filtering() -> None:
    context = make_context(822)
    contribution = hit_prevention("hit-damage-subclass")
    object.__setattr__(
        contribution,
        "damage_types",
        NonCanonicalFrozenScope([DamageType.STRATEGY]),
    )
    rules = DamageRuleCollection(hit_contributions=[contribution])

    with pytest.raises(TypeError, match="damage_types must be a frozenset"):
        HitResolutionSystem().resolve(context, req(), rules)

    assert_zero_rng(context)


def test_hit_runtime_rejects_frozenset_subclass_source_types_before_filtering() -> None:
    context = make_context(823)
    contribution = hit_prevention("hit-source-subclass")
    object.__setattr__(
        contribution,
        "source_types",
        NonCanonicalFrozenScope([DamageSourceType.NORMAL_ATTACK]),
    )
    rules = DamageRuleCollection(hit_contributions=[contribution])

    with pytest.raises(TypeError, match="source_types must be a frozenset"):
        HitResolutionSystem().resolve(context, req(), rules)

    assert_zero_rng(context)


def test_hit_runtime_rejects_frozenset_subclass_bypass_categories_before_filtering() -> None:
    context = make_context(824)
    contribution = HitRuleContribution(
        kind=HitRuleKind.BYPASS,
        source=src("hit-bypass-subclass"),
        order_key="hit-bypass-subclass",
        bypass_categories=[HitPreventionCategory.EVASION_LIKE],
    )
    object.__setattr__(
        contribution,
        "bypass_categories",
        NonCanonicalFrozenScope([HitPreventionCategory.EVASION_LIKE]),
    )
    rules = DamageRuleCollection(hit_contributions=[contribution])

    with pytest.raises(TypeError, match="bypass_categories must be a frozenset"):
        HitResolutionSystem().resolve(context, req(), rules)

    assert_zero_rng(context)


def test_formula_policy_runtime_rejects_frozenset_subclass_damage_types() -> None:
    contribution = formula_policy("formula-damage-subclass")
    object.__setattr__(
        contribution,
        "damage_types",
        NonCanonicalFrozenScope([DamageType.STRATEGY]),
    )
    rules = DamageRuleCollection(formula_policy_contributions=[contribution])

    with pytest.raises(TypeError, match="damage_types must be a frozenset"):
        DamageFormulaPolicySystem().resolve(req(), rules)


def test_formula_policy_runtime_rejects_frozenset_subclass_source_types() -> None:
    contribution = formula_policy("formula-source-subclass")
    object.__setattr__(
        contribution,
        "source_types",
        NonCanonicalFrozenScope([DamageSourceType.NORMAL_ATTACK]),
    )
    rules = DamageRuleCollection(formula_policy_contributions=[contribution])

    with pytest.raises(TypeError, match="source_types must be a frozenset"):
        DamageFormulaPolicySystem().resolve(req(), rules)


@pytest.mark.parametrize("field", ["damage_types", "source_types"])
@pytest.mark.parametrize("probability", [0.0, 1.0, 0.5])
def test_modifier_runtime_rejects_frozenset_subclass_before_rng(
    field: str,
    probability: float,
) -> None:
    context = make_context(825)
    contribution = modifier(probability, f"modifier-{field}-{probability}")
    malformed = (
        NonCanonicalFrozenScope([DamageType.STRATEGY])
        if field == "damage_types"
        else NonCanonicalFrozenScope([DamageSourceType.NORMAL_ATTACK])
    )
    object.__setattr__(contribution, field, malformed)
    rules = DamageRuleCollection(modifier_contributions=[contribution])

    with pytest.raises(TypeError, match=f"{field} must be a frozenset"):
        DamageModifierSystem().resolve(context, req(), rules, 100.0)

    assert_zero_rng(context)


def test_mutable_semantic_alias_cannot_change_runtime_scope_semantics() -> None:
    context = make_context(826)
    alias: set[object] = {DamageType.WEAPON}
    contribution = modifier(0.5, "modifier-semantic-alias")
    object.__setattr__(
        contribution,
        "damage_types",
        semantic_scope([DamageType.STRATEGY], alias),
    )
    rules = DamageRuleCollection(modifier_contributions=[contribution])

    with pytest.raises(TypeError, match="damage_types must be a frozenset"):
        DamageModifierSystem().resolve(context, req(), rules, 100.0)
    assert_zero_rng(context)

    alias.clear()
    with pytest.raises(TypeError, match="damage_types must be a frozenset"):
        DamageModifierSystem().resolve(context, req(), rules, 100.0)
    assert_zero_rng(context)


@pytest.mark.parametrize(
    "scope",
    [
        NonCanonicalFrozenScope([DamageType.WEAPON]),
        (DamageType.WEAPON,),
        [DamageType.WEAPON],
        {DamageType.WEAPON},
    ],
)
def test_constructor_still_canonicalizes_legal_iterables_to_exact_frozenset(scope) -> None:
    contribution = DamageModifierContribution(
        phase=DamageModifierPhase.CRITICAL,
        kind=DamageModifierKind.CRITICAL_MULTIPLIER,
        operation=DamageModifierOperation.MULTIPLY_FACTOR,
        operand=2.0,
        source=src("constructor-canonical"),
        order_key="constructor-canonical",
        damage_types=scope,
    )

    assert type(contribution.damage_types) is frozenset
    assert contribution.damage_types == frozenset({DamageType.WEAPON})
