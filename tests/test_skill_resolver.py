from __future__ import annotations

from sgs_v2.battle_core import (
    ApplyStateEffect,
    ApplyStateSkillEffectSpec,
    BattleContext,
    DamageEffect,
    DamageSkillEffectSpec,
    DamageType,
    EventBus,
    LineupPosition,
    RandomSystem,
    SkillDefinition,
    SkillResolutionStatus,
    SkillResolver,
    SkillRuntime,
    SkillTargetMode,
    TargetSystem,
    UnitRuntime,
)


class CountingRandomSystem(RandomSystem):
    def __init__(self, seed: int = 1, *, chance_result: bool | None = None) -> None:
        super().__init__(seed)
        self.chance_result = chance_result
        self.chance_calls = 0
        self.sample_calls = 0
        self.choice_calls = 0

    def chance(self, probability: float) -> bool:
        self.chance_calls += 1
        if self.chance_result is not None:
            return self.chance_result
        return super().chance(probability)

    def sample(self, values, k):  # type: ignore[no-untyped-def]
        self.sample_calls += 1
        return super().sample(values, k)

    def choice(self, values):  # type: ignore[no-untyped-def]
        self.choice_calls += 1
        return super().choice(values)


class RecordingTargetSystem(TargetSystem):
    def __init__(self) -> None:
        self.enemy_queries = 0
        self.random_unit_queries = 0

    def enemies(self, context, unit, *, alive_only=True):  # type: ignore[no-untyped-def]
        self.enemy_queries += 1
        return super().enemies(context, unit, alive_only=alive_only)

    def random_units(self, context, candidates, *, count):  # type: ignore[no-untyped-def]
        self.random_unit_queries += 1
        return super().random_units(context, candidates, count=count)


def make_context(
    random_system: RandomSystem,
    *,
    second_enemy: bool = True,
    living_enemy: bool = True,
) -> BattleContext:
    units = {
        "a1": UnitRuntime(
            "a1", "A1", "A", 10000, 10000, 400, 100, 100,
            lineup_position=LineupPosition.COMMANDER,
        ),
        "b1": UnitRuntime(
            "b1", "B1", "B", 10000, 10000 if living_enemy else 0, 100, 100, 90,
            lineup_position=LineupPosition.COMMANDER,
        ),
    }
    if second_enemy:
        units["b2"] = UnitRuntime(
            "b2", "B2", "B", 10000, 9000 if living_enemy else 0, 100, 100, 80,
            lineup_position=LineupPosition.DEPUTY_1,
        )
    return BattleContext(
        battle_id="stage6-resolver",
        units=units,
        event_bus=EventBus(),
        random=random_system,
    )


def damage_definition(rate: float) -> SkillDefinition:
    return SkillDefinition(
        skill_id="synthetic.probabilistic_damage",
        name="Synthetic Probabilistic Damage",
        activation_rate=rate,
        target_mode=SkillTargetMode.SINGLE_RANDOM_ENEMY,
        effect_specs=(
            DamageSkillEffectSpec(DamageType.WEAPON, coefficient=1.25),
        ),
    )


def test_disabled_runtime_short_circuits_before_target_and_rng() -> None:
    random_system = CountingRandomSystem()
    context = make_context(random_system)
    targets = RecordingTargetSystem()
    resolver = SkillResolver(targets)

    result = resolver.resolve(
        context,
        SkillRuntime(damage_definition(0.5), "a1", enabled=False),
    )

    assert result.status is SkillResolutionStatus.DISABLED
    assert result.target_ids == ()
    assert result.effects == ()
    assert targets.enemy_queries == 0
    assert targets.random_unit_queries == 0
    assert random_system.chance_calls == 0
    assert random_system.sample_calls == 0


def test_no_valid_target_consumes_no_activation_or_target_rng() -> None:
    random_system = CountingRandomSystem()
    context = make_context(random_system, living_enemy=False)
    targets = RecordingTargetSystem()

    result = SkillResolver(targets).resolve(
        context,
        SkillRuntime(damage_definition(0.5), "a1"),
    )

    assert result.status is SkillResolutionStatus.NO_VALID_TARGET
    assert result.target_ids == ()
    assert result.effects == ()
    assert targets.enemy_queries == 1
    assert targets.random_unit_queries == 0
    assert random_system.chance_calls == 0
    assert random_system.sample_calls == 0


def test_zero_percent_activation_consumes_no_rng_and_never_selects_target() -> None:
    random_system = CountingRandomSystem()
    context = make_context(random_system)
    targets = RecordingTargetSystem()

    result = SkillResolver(targets).resolve(
        context,
        SkillRuntime(damage_definition(0.0), "a1"),
    )

    assert result.status is SkillResolutionStatus.ACTIVATION_FAILED
    assert random_system.chance_calls == 0
    assert random_system.sample_calls == 0
    assert targets.random_unit_queries == 0


def test_hundred_percent_activation_skips_chance_and_uses_target_system() -> None:
    random_system = CountingRandomSystem()
    context = make_context(random_system)
    targets = RecordingTargetSystem()

    result = SkillResolver(targets).resolve(
        context,
        SkillRuntime(damage_definition(1.0), "a1"),
    )

    assert result.status is SkillResolutionStatus.RESOLVED
    assert len(result.target_ids) == 1
    assert len(result.effects) == 1
    assert isinstance(result.effects[0], DamageEffect)
    assert random_system.chance_calls == 0
    assert targets.random_unit_queries == 1
    assert random_system.sample_calls == 1
    assert random_system.choice_calls == 0


def test_single_candidate_target_selection_consumes_no_target_rng() -> None:
    random_system = CountingRandomSystem()
    context = make_context(random_system, second_enemy=False)
    targets = RecordingTargetSystem()

    result = SkillResolver(targets).resolve(
        context,
        SkillRuntime(damage_definition(1.0), "a1"),
    )

    assert result.status is SkillResolutionStatus.RESOLVED
    assert result.target_ids == ("b1",)
    assert targets.random_unit_queries == 1
    assert random_system.chance_calls == 0
    assert random_system.sample_calls == 0


def test_probabilistic_activation_calls_chance_exactly_once_and_failure_skips_target() -> None:
    random_system = CountingRandomSystem(chance_result=False)
    context = make_context(random_system)
    targets = RecordingTargetSystem()

    result = SkillResolver(targets).resolve(
        context,
        SkillRuntime(damage_definition(0.35), "a1"),
    )

    assert result.status is SkillResolutionStatus.ACTIVATION_FAILED
    assert result.target_ids == ()
    assert result.effects == ()
    assert random_system.chance_calls == 1
    assert targets.random_unit_queries == 0
    assert random_system.sample_calls == 0


def test_probabilistic_success_calls_chance_once_then_selects_target() -> None:
    random_system = CountingRandomSystem(chance_result=True)
    context = make_context(random_system)
    targets = RecordingTargetSystem()

    result = SkillResolver(targets).resolve(
        context,
        SkillRuntime(damage_definition(0.35), "a1"),
    )

    assert result.status is SkillResolutionStatus.RESOLVED
    assert random_system.chance_calls == 1
    assert targets.random_unit_queries == 1
    assert random_system.sample_calls == 1


def test_same_seed_reproduces_activation_target_and_effects() -> None:
    definition = damage_definition(0.5)

    first = SkillResolver(TargetSystem()).resolve(
        make_context(RandomSystem(1)),
        SkillRuntime(definition, "a1"),
    )
    second = SkillResolver(TargetSystem()).resolve(
        make_context(RandomSystem(1)),
        SkillRuntime(definition, "a1"),
    )

    assert first == second
    assert first.status is SkillResolutionStatus.RESOLVED
    assert len(first.target_ids) == 1


def test_same_resolver_changes_effects_from_typed_definition_data_not_skill_id_logic() -> None:
    context = make_context(RandomSystem(5), second_enemy=False)
    resolver = SkillResolver(TargetSystem())
    damage = SkillDefinition(
        skill_id="synthetic.same-id",
        name="Synthetic Damage",
        activation_rate=1.0,
        target_mode=SkillTargetMode.SINGLE_RANDOM_ENEMY,
        effect_specs=(DamageSkillEffectSpec(DamageType.WEAPON),),
    )
    state = SkillDefinition(
        skill_id="synthetic.same-id",
        name="Synthetic State",
        activation_rate=1.0,
        target_mode=SkillTargetMode.SINGLE_RANDOM_ENEMY,
        effect_specs=(ApplyStateSkillEffectSpec("690084"),),
    )

    damage_result = resolver.resolve(context, SkillRuntime(damage, "a1"))
    state_result = resolver.resolve(context, SkillRuntime(state, "a1"))

    assert isinstance(damage_result.effects[0], DamageEffect)
    assert isinstance(state_result.effects[0], ApplyStateEffect)
