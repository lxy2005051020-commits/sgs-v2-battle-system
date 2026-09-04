from __future__ import annotations

from sgs_v2.battle_core import (
    ApplyStateEffect,
    ApplyStateEffectResult,
    ApplyStateSkillEffectSpec,
    BattleContext,
    BattleSystems,
    DamageEffect,
    DamageEffectResult,
    DamageSkillEffectSpec,
    DamageType,
    DeferredEffectResult,
    EffectExecutionStatus,
    EventBus,
    EventType,
    LineupPosition,
    OfficialStateId,
    RandomSystem,
    RecoverEffect,
    SkillDefinition,
    SkillResolutionStatus,
    SkillRuntime,
    SkillTargetMode,
    UnitRuntime,
    register_official_state_definitions,
)


def make_context(seed: int = 31) -> BattleContext:
    context = BattleContext(
        battle_id=f"stage6-integration-{seed}",
        units={
            "a1": UnitRuntime(
                "a1", "A1", "A", 10000, 10000, 400, 100, 100,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "b1": UnitRuntime(
                "b1", "B1", "B", 10000, 10000, 100, 100, 90,
                lineup_position=LineupPosition.COMMANDER,
            ),
        },
        event_bus=EventBus(),
        random=RandomSystem(seed),
    )
    register_official_state_definitions(context.states)
    return context


def weapon_definition() -> SkillDefinition:
    return SkillDefinition(
        skill_id="synthetic.weapon_damage",
        name="Synthetic Weapon Damage",
        activation_rate=1.0,
        target_mode=SkillTargetMode.SINGLE_RANDOM_ENEMY,
        effect_specs=(
            DamageSkillEffectSpec(DamageType.WEAPON, coefficient=1.25),
        ),
    )


def disarm_definition() -> SkillDefinition:
    return SkillDefinition(
        skill_id="synthetic.disarm",
        name="Synthetic Disarm",
        activation_rate=1.0,
        target_mode=SkillTargetMode.SINGLE_RANDOM_ENEMY,
        effect_specs=(
            ApplyStateSkillEffectSpec(OfficialStateId.DISARM.value),
        ),
    )


def combination_definition() -> SkillDefinition:
    return SkillDefinition(
        skill_id="synthetic.damage_and_disarm",
        name="Synthetic Damage And Disarm",
        activation_rate=1.0,
        target_mode=SkillTargetMode.SINGLE_RANDOM_ENEMY,
        effect_specs=(
            DamageSkillEffectSpec(DamageType.WEAPON, coefficient=1.0),
            ApplyStateSkillEffectSpec(OfficialStateId.DISARM.value),
        ),
    )


def test_skill_resolve_produces_damage_effect_without_side_effect_then_executor_applies_it() -> None:
    context = make_context()
    systems = BattleSystems(
        weapon_random_percent_range=(90, 90),
        weapon_low_damage_floor_range=(5, 5),
    )
    runtime = SkillRuntime(weapon_definition(), "a1")
    before_troops = context.get_unit("b1").troops
    before_events = tuple(context.event_bus.history)

    result = systems.skill_resolver.resolve(context, runtime)

    assert result.status is SkillResolutionStatus.RESOLVED
    assert result.target_ids == ("b1",)
    assert len(result.effects) == 1
    effect = result.effects[0]
    assert isinstance(effect, DamageEffect)
    assert effect.source_id == "a1"
    assert effect.target_id == "b1"
    assert effect.source_skill_id == "synthetic.weapon_damage"
    assert context.get_unit("b1").troops == before_troops
    assert tuple(context.event_bus.history) == before_events

    execution = systems.effect_executor.execute(context, effect)

    assert isinstance(execution, DamageEffectResult)
    assert context.get_unit("b1").troops < before_troops
    assert execution.resolution.damage.source_skill_id == "synthetic.weapon_damage"
    assert any(
        event.event_type is EventType.DAMAGE_DEALT
        for event in context.event_bus.history
    )


def test_skill_resolve_produces_state_effect_without_side_effect_then_executor_applies_it() -> None:
    context = make_context(seed=32)
    systems = BattleSystems()
    runtime = SkillRuntime(disarm_definition(), "a1")

    assert not context.states.has(
        owner_id="b1",
        state_id=OfficialStateId.DISARM.value,
    )
    result = systems.skill_resolver.resolve(context, runtime)

    assert result.status is SkillResolutionStatus.RESOLVED
    effect = result.effects[0]
    assert isinstance(effect, ApplyStateEffect)
    assert effect.owner_id == "b1"
    assert effect.source_id == "a1"
    assert effect.source_skill_id == "synthetic.disarm"
    assert not context.states.has(
        owner_id="b1",
        state_id=OfficialStateId.DISARM.value,
    )

    execution = systems.effect_executor.execute(context, effect)

    assert isinstance(execution, ApplyStateEffectResult)
    assert context.states.has(
        owner_id="b1",
        state_id=OfficialStateId.DISARM.value,
    )
    assert context.event_bus.history[-1].event_type is EventType.STATE_APPLIED


def test_multi_effect_resolution_preserves_declaration_and_execution_order() -> None:
    context = make_context(seed=33)
    systems = BattleSystems(
        weapon_random_percent_range=(90, 90),
        weapon_low_damage_floor_range=(5, 5),
    )
    result = systems.skill_resolver.resolve(
        context,
        SkillRuntime(combination_definition(), "a1"),
    )

    assert tuple(type(effect) for effect in result.effects) == (
        DamageEffect,
        ApplyStateEffect,
    )
    before_troops = context.get_unit("b1").troops
    assert not context.states.has(
        owner_id="b1",
        state_id=OfficialStateId.DISARM.value,
    )

    for effect in result.effects:
        systems.effect_executor.execute(context, effect)

    assert context.get_unit("b1").troops < before_troops
    assert context.states.has(
        owner_id="b1",
        state_id=OfficialStateId.DISARM.value,
    )
    event_types = [event.event_type for event in context.event_bus.history]
    assert event_types.index(EventType.DAMAGE_DEALT) < event_types.index(
        EventType.STATE_APPLIED
    )


def test_battle_systems_composes_resolver_with_shared_target_system_only() -> None:
    systems = BattleSystems()
    assert systems.skill_resolver._target_system is systems.target_system
    assert not hasattr(systems.skill_resolver, "_effect_executor")
    assert not hasattr(systems.skill_resolver, "_battle_systems")


def test_stage5_recover_effect_remains_deferred() -> None:
    context = make_context(seed=34)
    systems = BattleSystems()
    context.get_unit("b1").troops = 5000
    before = context.get_unit("b1").troops

    result = systems.effect_executor.execute(
        context,
        RecoverEffect(
            source_id="a1",
            target_id="b1",
            amount=1000,
            source_skill_id="synthetic.not-a-stage6-skill",
        ),
    )

    assert isinstance(result, DeferredEffectResult)
    assert result.status is EffectExecutionStatus.DEFERRED
    assert result.reason == "RECOVERY_SYSTEM_NOT_AVAILABLE"
    assert context.get_unit("b1").troops == before
