from __future__ import annotations

import pytest

from sgs_v2.battle_core import (
    BattleContext,
    BattleSystems,
    DamageEffect,
    DamageRequest,
    DamageResult,
    DamageSourceType,
    DamageType,
    EventBus,
    EventType,
    LineupPosition,
    OfficialStateId,
    PeriodicDamageStateParams,
    PeriodicRecoveryStateParams,
    RandomSystem,
    RecoverEffect,
    RecoveryRequest,
    RoundStartHook,
    StateDefinition,
    StateLifecycleSystem,
    UnitRuntime,
    ROUND_START_TRIGGER_TAG,
    register_official_state_definitions,
)


def make_context() -> BattleContext:
    context = BattleContext(
        battle_id="stage7-provenance",
        units={
            "a1": UnitRuntime(
                "a1", "A1", "A", 1000, 700, 400, 100, 100,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "b1": UnitRuntime(
                "b1", "B1", "B", 1000, 700, 100, 100, 90,
                lineup_position=LineupPosition.COMMANDER,
            ),
        },
        event_bus=EventBus(),
        random=RandomSystem(91),
    )
    context.current_round = 1
    context.current_phase = "ROUND_START"
    register_official_state_definitions(context.states)
    return context


def register_damage_state(context: BattleContext) -> None:
    context.states.register_definition(
        StateDefinition(
            state_id="synthetic-damage",
            name="synthetic-damage",
            tags=frozenset({ROUND_START_TRIGGER_TAG}),
            runtime_params_type=PeriodicDamageStateParams,
        )
    )


def register_recovery_state(context: BattleContext) -> None:
    context.states.register_definition(
        StateDefinition(
            state_id="synthetic-recovery",
            name="synthetic-recovery",
            tags=frozenset({ROUND_START_TRIGGER_TAG}),
            runtime_params_type=PeriodicRecoveryStateParams,
        )
    )


def test_state_damage_provenance_survives_effect_request_result_and_event() -> None:
    context = make_context()
    register_damage_state(context)
    state = StateLifecycleSystem().apply(
        context,
        state_id="synthetic-damage",
        owner_id="b1",
        source_id="a1",
        source_skill_id="source-skill",
        runtime_params=PeriodicDamageStateParams(DamageType.WEAPON, 1.0),
    )
    systems = BattleSystems(
        weapon_random_percent_range=(90, 90),
        weapon_low_damage_floor_range=(5, 5),
    )

    effects = systems.trigger_system.collect(context, RoundStartHook(1))
    effect = effects[0]
    assert isinstance(effect, DamageEffect)
    assert effect.source_skill_id == "source-skill"
    assert effect.source_state_id == state.state_id
    assert effect.source_state_instance_id == state.instance_id

    request = effect.to_request()
    assert request.source_skill_id == "source-skill"
    assert request.source_state_id == state.state_id
    assert request.source_state_instance_id == state.instance_id

    result = systems.effect_executor.execute(context, effect)
    damage = result.resolution.damage  # type: ignore[union-attr]
    assert damage.source_skill_id == "source-skill"
    assert damage.source_state_id == state.state_id
    assert damage.source_state_instance_id == state.instance_id

    event = next(
        event for event in reversed(context.event_bus.history)
        if event.event_type is EventType.DAMAGE_DEALT
    )
    assert event.payload["source_skill_id"] == "source-skill"
    assert event.payload["source_state_id"] == state.state_id
    assert event.payload["source_state_instance_id"] == state.instance_id


def test_weakness_zero_damage_event_keeps_state_provenance() -> None:
    context = make_context()
    register_damage_state(context)
    state = StateLifecycleSystem().apply(
        context,
        state_id="synthetic-damage",
        owner_id="b1",
        source_id="a1",
        source_skill_id="source-skill",
        runtime_params=PeriodicDamageStateParams(DamageType.WEAPON, 1.0),
    )
    StateLifecycleSystem().apply(
        context,
        state_id=OfficialStateId.WEAKNESS.value,
        owner_id="a1",
        source_id="b1",
    )
    systems = BattleSystems()

    systems.rule_hook_system.process(context, RoundStartHook(1))

    event = next(
        event for event in reversed(context.event_bus.history)
        if event.event_type is EventType.DAMAGE_DEALT
    )
    assert event.payload["source_skill_id"] == "source-skill"
    assert event.payload["source_state_id"] == state.state_id
    assert event.payload["source_state_instance_id"] == state.instance_id


def test_state_recovery_provenance_survives_effect_request_result_and_recovered_event() -> None:
    context = make_context()
    register_recovery_state(context)
    context.get_unit("b1").troops = 500
    state = StateLifecycleSystem().apply(
        context,
        state_id="synthetic-recovery",
        owner_id="b1",
        source_id="a1",
        source_skill_id="heal-source-skill",
        runtime_params=PeriodicRecoveryStateParams(50),
    )
    systems = BattleSystems()

    effect = systems.trigger_system.collect(context, RoundStartHook(1))[0]
    assert isinstance(effect, RecoverEffect)
    request = effect.to_request()
    assert request.source_skill_id == "heal-source-skill"
    assert request.source_state_id == state.state_id
    assert request.source_state_instance_id == state.instance_id

    result = systems.effect_executor.execute(context, effect)
    recovery_request = result.resolution.request  # type: ignore[union-attr]
    assert recovery_request.source_skill_id == "heal-source-skill"
    assert recovery_request.source_state_id == state.state_id
    assert recovery_request.source_state_instance_id == state.instance_id

    event = next(
        event for event in reversed(context.event_bus.history)
        if event.event_type is EventType.TROOPS_RECOVERED
    )
    assert event.payload["source_skill_id"] == "heal-source-skill"
    assert event.payload["source_state_id"] == state.state_id
    assert event.payload["source_state_instance_id"] == state.instance_id


def test_prevented_recovery_event_keeps_state_provenance() -> None:
    context = make_context()
    register_recovery_state(context)
    state = StateLifecycleSystem().apply(
        context,
        state_id="synthetic-recovery",
        owner_id="b1",
        source_id="a1",
        source_skill_id="heal-source-skill",
        runtime_params=PeriodicRecoveryStateParams(50),
    )
    StateLifecycleSystem().apply(
        context,
        state_id=OfficialStateId.HEALING_BAN.value,
        owner_id="b1",
        source_id="a1",
    )
    systems = BattleSystems()

    systems.rule_hook_system.process(context, RoundStartHook(1))

    event = next(
        event for event in reversed(context.event_bus.history)
        if event.event_type is EventType.RECOVERY_PREVENTED
    )
    assert event.payload["source_skill_id"] == "heal-source-skill"
    assert event.payload["source_state_id"] == state.state_id
    assert event.payload["source_state_instance_id"] == state.instance_id


def test_none_none_and_complete_state_provenance_pairs_are_valid() -> None:
    DamageEffect(
        source_id="a1",
        target_id="b1",
        damage_type=DamageType.WEAPON,
        source_type=DamageSourceType.SKILL,
    )
    DamageRequest(
        source_id="a1",
        target_id="b1",
        damage_type=DamageType.WEAPON,
        source_type=DamageSourceType.SKILL,
        source_state_id="state-type",
        source_state_instance_id="state-000001",
    )
    RecoverEffect(source_id=None, target_id="b1", amount=1)
    RecoveryRequest(
        source_id=None,
        target_id="b1",
        amount=1,
        source_state_id="state-type",
        source_state_instance_id="state-000001",
    )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"source_state_id": "state-type", "source_state_instance_id": None},
        {"source_state_id": None, "source_state_instance_id": "state-000001"},
    ],
)
def test_effect_and_request_models_reject_partial_state_provenance(kwargs) -> None:
    with pytest.raises(ValueError):
        DamageEffect(
            source_id="a1",
            target_id="b1",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.SKILL,
            **kwargs,
        )
    with pytest.raises(ValueError):
        DamageRequest(
            source_id="a1",
            target_id="b1",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.SKILL,
            **kwargs,
        )
    with pytest.raises(ValueError):
        RecoverEffect(source_id=None, target_id="b1", amount=1, **kwargs)
    with pytest.raises(ValueError):
        RecoveryRequest(source_id=None, target_id="b1", amount=1, **kwargs)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"source_state_id": "state-type", "source_state_instance_id": None},
        {"source_state_id": None, "source_state_instance_id": "state-000001"},
    ],
)
def test_damage_result_rejects_partial_state_provenance(kwargs) -> None:
    with pytest.raises(ValueError):
        DamageResult(
            source_id="a1",
            target_id="b1",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.SKILL,
            coefficient=1.0,
            base_damage=10.0,
            scaled_damage=10.0,
            final_damage=10,
            **kwargs,
        )


def test_damage_result_preserves_stage6_positional_constructor_contract() -> None:
    result = DamageResult(
        "a1",
        "b1",
        DamageType.WEAPON,
        DamageSourceType.SKILL,
        1.0,
        100.0,
        100.0,
        100,
        "legacy-skill",
        True,
        OfficialStateId.WEAKNESS.value,
    )

    assert result.source_skill_id == "legacy-skill"
    assert result.prevented is True
    assert result.prevented_by_state_id == OfficialStateId.WEAKNESS.value
    assert result.source_state_id is None
    assert result.source_state_instance_id is None
