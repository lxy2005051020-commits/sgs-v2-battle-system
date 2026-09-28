from __future__ import annotations

from sgs_v2.battle_core import (
    BattleContext,
    DamageEffect,
    DamageType,
    EventBus,
    LineupPosition,
    PeriodicDamageStateParams,
    PeriodicRecoveryStateParams,
    RandomSystem,
    RecoverEffect,
    RoundStartHook,
    StateDefinition,
    StateInstance,
    StateLifecycleSystem,
    TriggerSystem,
    UNIT_ACTION_START_TRIGGER_TAG,
    UnitActionStartHook,
    UnitRuntime,
    ROUND_START_TRIGGER_TAG,
    register_official_state_definitions,
    OfficialStateId,
)


def make_context() -> BattleContext:
    context = BattleContext(
        battle_id="stage7-trigger",
        units={
            "a1": UnitRuntime(
                "a1", "A1", "A", 1000, 1000, 300, 100, 80,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "b1": UnitRuntime(
                "b1", "B1", "B", 1000, 1000, 100, 100, 90,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "b2": UnitRuntime(
                "b2", "B2", "B", 1000, 1000, 100, 100, 70,
                lineup_position=LineupPosition.DEPUTY_1,
            ),
        },
        event_bus=EventBus(),
        random=RandomSystem(9),
    )
    context.current_round = 1
    context.current_phase = "ACTION_ORDER"
    return context


def register_damage_definition(context: BattleContext, state_id: str, tag: str) -> None:
    context.states.register_definition(
        StateDefinition(
            state_id=state_id,
            name=state_id,
            tags=frozenset({tag}),
            runtime_params_type=PeriodicDamageStateParams,
        )
    )


def test_round_start_collects_only_round_tagged_typed_states() -> None:
    context = make_context()
    register_damage_definition(context, "round-damage", ROUND_START_TRIGGER_TAG)
    register_damage_definition(context, "action-damage", UNIT_ACTION_START_TRIGGER_TAG)
    lifecycle = StateLifecycleSystem()
    lifecycle.apply(
        context,
        state_id="round-damage",
        owner_id="b1",
        source_id="a1",
        source_skill_id="skill-r",
        runtime_params=PeriodicDamageStateParams(DamageType.WEAPON, 1.25),
    )
    lifecycle.apply(
        context,
        state_id="action-damage",
        owner_id="b1",
        source_id="a1",
        runtime_params=PeriodicDamageStateParams(DamageType.WEAPON, 2.0),
    )

    effects = TriggerSystem().collect(context, RoundStartHook(1))

    assert len(effects) == 1
    effect = effects[0]
    assert isinstance(effect, DamageEffect)
    assert effect.coefficient == 1.25
    assert effect.source_skill_id == "skill-r"
    assert effect.source_state_id == "round-damage"
    assert effect.source_state_instance_id == "state-000001"


def test_unit_action_start_only_collects_states_owned_by_actor() -> None:
    context = make_context()
    register_damage_definition(context, "action-damage", UNIT_ACTION_START_TRIGGER_TAG)
    lifecycle = StateLifecycleSystem()
    lifecycle.apply(
        context,
        state_id="action-damage",
        owner_id="b1",
        source_id="a1",
        runtime_params=PeriodicDamageStateParams(DamageType.WEAPON, 1.0),
    )
    lifecycle.apply(
        context,
        state_id="action-damage",
        owner_id="b2",
        source_id="a1",
        runtime_params=PeriodicDamageStateParams(DamageType.WEAPON, 2.0),
    )

    effects = TriggerSystem().collect(context, UnitActionStartHook(1, "b2"))

    assert len(effects) == 1
    assert isinstance(effects[0], DamageEffect)
    assert effects[0].target_id == "b2"
    assert effects[0].coefficient == 2.0


def test_trigger_system_supports_synthetic_periodic_recovery_without_executing_it() -> None:
    context = make_context()
    context.states.register_definition(
        StateDefinition(
            state_id="round-recovery",
            name="round-recovery",
            tags=frozenset({ROUND_START_TRIGGER_TAG}),
            runtime_params_type=PeriodicRecoveryStateParams,
        )
    )
    state = StateLifecycleSystem().apply(
        context,
        state_id="round-recovery",
        owner_id="b1",
        source_id="a1",
        source_skill_id="heal-skill",
        runtime_params=PeriodicRecoveryStateParams(88),
    )
    before_troops = context.get_unit("b1").troops
    before_history = tuple(context.event_bus.history)
    before_states = tuple(context.states.find())

    effects = TriggerSystem().collect(context, RoundStartHook(1))

    assert effects == (
        RecoverEffect(
            source_id="a1",
            target_id="b1",
            amount=88,
            source_skill_id="heal-skill",
            source_state_id="round-recovery",
            source_state_instance_id=state.instance_id,
        ),
    )
    assert context.get_unit("b1").troops == before_troops
    assert tuple(context.event_bus.history) == before_history
    assert tuple(context.states.find()) == before_states


def test_multiple_instances_are_sorted_by_instance_id_not_registry_insertion() -> None:
    context = make_context()
    register_damage_definition(context, "synthetic", ROUND_START_TRIGGER_TAG)
    later_id = StateInstance(
        instance_id="state-000010",
        state_id="synthetic",
        owner_id="b1",
        source_id="a1",
        source_skill_id=None,
        applied_round=1,
        applied_phase="ACTION_ORDER",
        runtime_params=PeriodicDamageStateParams(DamageType.WEAPON, 10.0),
    )
    earlier_id = StateInstance(
        instance_id="state-000002",
        state_id="synthetic",
        owner_id="b1",
        source_id="a1",
        source_skill_id=None,
        applied_round=1,
        applied_phase="ACTION_ORDER",
        runtime_params=PeriodicDamageStateParams(DamageType.WEAPON, 2.0),
    )
    context.states.add(later_id)
    context.states.add(earlier_id)

    effects = TriggerSystem().collect(context, RoundStartHook(1))

    assert [effect.source_state_instance_id for effect in effects] == [
        "state-000002",
        "state-000010",
    ]
    assert [effect.coefficient for effect in effects if isinstance(effect, DamageEffect)] == [
        2.0,
        10.0,
    ]


def test_unrelated_hook_produces_no_effects() -> None:
    context = make_context()
    register_damage_definition(context, "action-only", UNIT_ACTION_START_TRIGGER_TAG)
    StateLifecycleSystem().apply(
        context,
        state_id="action-only",
        owner_id="b1",
        source_id="a1",
        runtime_params=PeriodicDamageStateParams(DamageType.WEAPON, 1.0),
    )
    assert TriggerSystem().collect(context, RoundStartHook(1)) == ()


def test_official_periodic_states_remain_deferred_by_evidence_gate() -> None:
    context = make_context()
    register_official_state_definitions(context.states)
    StateLifecycleSystem().apply(
        context,
        state_id=OfficialStateId.BURN.value,
        owner_id="b1",
        source_id="a1",
    )
    StateLifecycleSystem().apply(
        context,
        state_id=OfficialStateId.RECUPERATION.value,
        owner_id="b1",
        source_id="a1",
    )

    assert TriggerSystem().collect(context, RoundStartHook(1)) == ()
