from __future__ import annotations

from typing import get_args

import pytest

from sgs_v2.battle_core import (
    BattleContext,
    BattleSystems,
    DamageType,
    EventBus,
    HookResolutionResult,
    LineupPosition,
    PeriodicDamageStateParams,
    PeriodicRecoveryStateParams,
    RandomSystem,
    RecoverEffectResult,
    RoundStartHook,
    RuleHook,
    RuleHookSystem,
    StateDefinition,
    StateLifecycleSystem,
    UnitActionStartHook,
    UnitRuntime,
    ROUND_START_TRIGGER_TAG,
)


def make_context() -> BattleContext:
    context = BattleContext(
        battle_id="stage7-rule-hook",
        units={
            "a1": UnitRuntime(
                "a1", "A1", "A", 1000, 500, 500, 100, 100,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "b1": UnitRuntime(
                "b1", "B1", "B", 1000, 1000, 100, 100, 90,
                lineup_position=LineupPosition.COMMANDER,
            ),
        },
        event_bus=EventBus(),
        random=RandomSystem(71),
    )
    context.current_round = 1
    context.current_phase = "ROUND_START"
    return context


def test_rule_hook_union_alias_is_explicit_two_variant_union() -> None:
    assert set(get_args(RuleHook)) == {RoundStartHook, UnitActionStartHook}


@pytest.mark.parametrize("round_no", [True, 0, -1, 1.5, "1"])
def test_round_start_hook_rejects_invalid_round_no(round_no) -> None:
    with pytest.raises((TypeError, ValueError)):
        RoundStartHook(round_no)  # type: ignore[arg-type]


@pytest.mark.parametrize("actor_id", ["", "   ", 1, None])
def test_unit_action_start_hook_rejects_invalid_actor_id(actor_id) -> None:
    with pytest.raises((TypeError, ValueError)):
        UnitActionStartHook(1, actor_id)  # type: ignore[arg-type]


def test_rule_hook_system_rejects_round_mismatch() -> None:
    context = make_context()
    systems = BattleSystems()
    with pytest.raises(ValueError, match="current_round"):
        systems.rule_hook_system.process(context, RoundStartHook(2))


def test_rule_hook_system_rejects_missing_action_actor() -> None:
    context = make_context()
    systems = BattleSystems()
    with pytest.raises(KeyError, match="actor_id"):
        systems.rule_hook_system.process(
            context,
            UnitActionStartHook(1, "missing"),
        )


def test_rule_hook_system_rejects_dead_action_actor_at_boundary() -> None:
    context = make_context()
    context.get_unit("b1").troops = 0
    systems = BattleSystems()
    with pytest.raises(ValueError, match="alive"):
        systems.rule_hook_system.process(
            context,
            UnitActionStartHook(1, "b1"),
        )


def test_hook_resolution_result_canonicalizes_empty_iterable_to_tuple() -> None:
    result = HookResolutionResult(
        hook=RoundStartHook(1),
        effect_results=[],  # type: ignore[arg-type]
    )
    assert result.hook == RoundStartHook(1)
    assert result.effect_results == ()
    assert isinstance(result.effect_results, tuple)


def test_hook_resolution_result_rejects_illegal_result_member() -> None:
    with pytest.raises(TypeError, match="EffectExecutionResult"):
        HookResolutionResult(
            hook=RoundStartHook(1),
            effect_results=(object(),),  # type: ignore[arg-type]
        )


def test_no_effect_hook_returns_typed_empty_result_not_none() -> None:
    context = make_context()
    result = BattleSystems().rule_hook_system.process(context, RoundStartHook(1))
    assert isinstance(result, HookResolutionResult)
    assert result.hook == RoundStartHook(1)
    assert result.effect_results == ()


def test_hook_atomic_batch_executes_later_effect_after_earlier_lethal_effect() -> None:
    context = BattleContext(
        battle_id="stage7-atomic-batch",
        units={
            "a1": UnitRuntime(
                "a1", "A1", "A", 1000, 500, 1000, 0, 100,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "b1": UnitRuntime(
                "b1", "B1", "B", 1, 1, 1, 0, 90,
                lineup_position=LineupPosition.COMMANDER,
            ),
        },
        event_bus=EventBus(),
        random=RandomSystem(72),
    )
    context.current_round = 1
    context.current_phase = "ROUND_START"
    context.states.register_definition(
        StateDefinition(
            state_id="01-lethal",
            name="lethal",
            tags=frozenset({ROUND_START_TRIGGER_TAG}),
            runtime_params_type=PeriodicDamageStateParams,
        )
    )
    context.states.register_definition(
        StateDefinition(
            state_id="02-recover",
            name="recover",
            tags=frozenset({ROUND_START_TRIGGER_TAG}),
            runtime_params_type=PeriodicRecoveryStateParams,
        )
    )
    lifecycle = StateLifecycleSystem()
    first = lifecycle.apply(
        context,
        state_id="01-lethal",
        owner_id="b1",
        source_id="a1",
        runtime_params=PeriodicDamageStateParams(DamageType.WEAPON, 1000.0),
    )
    second = lifecycle.apply(
        context,
        state_id="02-recover",
        owner_id="a1",
        source_id="a1",
        runtime_params=PeriodicRecoveryStateParams(100),
    )
    assert first.instance_id < second.instance_id

    systems = BattleSystems(
        weapon_random_percent_range=(90, 90),
        weapon_low_damage_floor_range=(5, 5),
    )
    result = systems.rule_hook_system.process(context, RoundStartHook(1))

    assert context.get_unit("b1").troops == 0
    assert context.get_unit("a1").troops == 600
    assert len(result.effect_results) == 2
    assert isinstance(result.effect_results[1], RecoverEffectResult)


def test_rule_hook_system_constructor_has_only_trigger_and_executor_dependencies() -> None:
    import inspect

    parameters = list(inspect.signature(RuleHookSystem.__init__).parameters)
    assert parameters == ["self", "trigger_system", "effect_executor"]
