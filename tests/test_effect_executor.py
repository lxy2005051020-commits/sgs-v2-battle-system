from __future__ import annotations

import inspect
from dataclasses import FrozenInstanceError

import pytest

from sgs_v2.battle_core import (
    ApplyStateEffect,
    ApplyStateEffectResult,
    BattleContext,
    BattleEngine,
    BattleSystems,
    DamageEffect,
    DamageEffectResult,
    DamageSourceType,
    DamageType,
    EffectExecutionStatus,
    EventBus,
    EventType,
    LineupPosition,
    OfficialStateId,
    RandomSystem,
    RecoverEffect,
    RecoverEffectResult,
    RecoveryResolvedResult,
    RemoveStateEffect,
    RemoveStateEffectResult,
    UnitRuntime,
    register_official_state_definitions,
)
from sgs_v2.battle_core.effect_executor import EffectExecutor


def make_context(seed: int = 21) -> BattleContext:
    context = BattleContext(
        battle_id=f"stage5-effect-{seed}",
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


def test_damage_effect_routes_through_shared_damage_resolution_system() -> None:
    context = make_context()
    systems = BattleSystems(
        weapon_random_percent_range=(90, 90),
        weapon_low_damage_floor_range=(5, 5),
    )
    before = context.get_unit("b1").troops
    effect = DamageEffect(
        source_id="a1",
        target_id="b1",
        damage_type=DamageType.WEAPON,
        source_type=DamageSourceType.SKILL,
        coefficient=1.25,
        source_skill_id="test-skill",
    )

    result = systems.effect_executor.execute(context, effect)

    assert isinstance(result, DamageEffectResult)
    assert result.status is EffectExecutionStatus.RESOLVED
    assert result.resolution.damage.source_skill_id == "test-skill"
    assert result.resolution.troop_change is not None
    assert context.get_unit("b1").troops < before
    assert any(
        event.event_type is EventType.DAMAGE_DEALT
        for event in context.event_bus.history
    )


def test_apply_and_remove_state_effects_route_through_lifecycle() -> None:
    context = make_context(seed=22)
    systems = BattleSystems()
    apply_effect = ApplyStateEffect(
        state_id=OfficialStateId.DISARM.value,
        owner_id="b1",
        source_id="a1",
        source_skill_id="test-skill",
    )

    applied = systems.effect_executor.execute(context, apply_effect)
    assert isinstance(applied, ApplyStateEffectResult)
    assert context.states.has(owner_id="b1", state_id=OfficialStateId.DISARM.value)
    assert context.event_bus.history[-1].event_type is EventType.STATE_APPLIED

    removed = systems.effect_executor.execute(
        context,
        RemoveStateEffect(applied.state_instance.instance_id),
    )
    assert isinstance(removed, RemoveStateEffectResult)
    assert removed.removed_state == applied.state_instance
    assert not context.states.has(owner_id="b1", state_id=OfficialStateId.DISARM.value)
    assert context.event_bus.history[-1].event_type is EventType.STATE_REMOVED


def test_recover_effect_routes_through_recovery_system() -> None:
    context = make_context(seed=23)
    context.get_unit("b1").troops = 5000
    systems = BattleSystems()

    result = systems.effect_executor.execute(
        context,
        RecoverEffect(
            source_id="a1",
            target_id="b1",
            amount=1200,
            source_skill_id="test-skill",
        ),
    )

    assert isinstance(result, RecoverEffectResult)
    assert result.status is EffectExecutionStatus.RESOLVED
    assert isinstance(result.resolution, RecoveryResolvedResult)
    assert result.resolution.troop_change.actual_change == 1200
    assert context.get_unit("b1").troops == 6200
    assert context.event_bus.history[-1].event_type is EventType.TROOPS_RECOVERED


def test_effect_objects_are_immutable() -> None:
    effect = DamageEffect(
        source_id="a1",
        target_id="b1",
        damage_type=DamageType.WEAPON,
        source_type=DamageSourceType.SKILL,
    )
    with pytest.raises(FrozenInstanceError):
        effect.coefficient = 2.0  # type: ignore[misc]


def test_effect_executor_does_not_own_rng_troop_or_registry_mutation_logic() -> None:
    source = inspect.getsource(EffectExecutor)
    assert "import random" not in source
    assert ".random" not in source
    assert ".troops" not in source
    assert ".states.add" not in source
    assert ".states.remove" not in source


def test_battle_engine_does_not_know_concrete_effect_types() -> None:
    source = inspect.getsource(BattleEngine)
    for forbidden in (
        "DamageEffect",
        "ApplyStateEffect",
        "RemoveStateEffect",
        "RecoverEffect",
        "EffectExecutor",
    ):
        assert forbidden not in source
