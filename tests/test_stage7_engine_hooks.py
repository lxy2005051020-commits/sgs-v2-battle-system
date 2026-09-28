from __future__ import annotations

from sgs_v2.battle_core import (
    BattleContext,
    BattleEngine,
    BattleSystems,
    DamageType,
    EventBus,
    EventType,
    LineupPosition,
    PeriodicDamageStateParams,
    RandomSystem,
    StateDefinition,
    StateLifecycleSystem,
    UnitRuntime,
    ROUND_START_TRIGGER_TAG,
    UNIT_ACTION_START_TRIGGER_TAG,
)


class RecordingActionSystem:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def execute(self, context, actor, action_scope=None):
        self.calls.append(actor.unit_id)
        return None


def make_two_commander_context(*, b_troops: int = 1000, b_speed: int = 100) -> BattleContext:
    return BattleContext(
        battle_id="stage7-engine",
        units={
            "a1": UnitRuntime(
                "a1", "A1", "A", 1000, 1000, 1000, 0, 80,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "b1": UnitRuntime(
                "b1", "B1", "B", 1000, b_troops, 1, 0, b_speed,
                lineup_position=LineupPosition.COMMANDER,
            ),
        },
        event_bus=EventBus(),
        random=RandomSystem(81),
        max_rounds=1,
    )


def register_periodic_damage(context: BattleContext, state_id: str, tag: str) -> None:
    context.states.register_definition(
        StateDefinition(
            state_id=state_id,
            name=state_id,
            tags=frozenset({tag}),
            runtime_params_type=PeriodicDamageStateParams,
        )
    )


def test_round_start_expiration_happens_before_round_hook() -> None:
    context = make_two_commander_context()
    register_periodic_damage(context, "expiring", ROUND_START_TRIGGER_TAG)
    state = StateLifecycleSystem().apply(
        context,
        state_id="expiring",
        owner_id="b1",
        source_id="a1",
        expires_round=1,
        expires_phase="ROUND_START",
        runtime_params=PeriodicDamageStateParams(DamageType.WEAPON, 1000.0),
    )
    systems = BattleSystems()
    recorder = RecordingActionSystem()
    systems.action_system = recorder  # type: ignore[assignment]

    BattleEngine(context=context, systems=systems).run()

    event_types = [event.event_type for event in context.event_bus.history]
    assert EventType.STATE_EXPIRED in event_types
    assert event_types.index(EventType.STATE_EXPIRED) < event_types.index(EventType.ROUND_STARTED)
    assert not context.states.has(owner_id="b1", state_id=state.state_id)
    assert not any(event.event_type is EventType.DAMAGE_DEALT for event in context.event_bus.history)


def test_round_started_fact_precedes_round_hook_effect_fact() -> None:
    context = make_two_commander_context()
    register_periodic_damage(context, "round-hit", ROUND_START_TRIGGER_TAG)
    StateLifecycleSystem().apply(
        context,
        state_id="round-hit",
        owner_id="b1",
        source_id="a1",
        runtime_params=PeriodicDamageStateParams(DamageType.WEAPON, 0.01),
    )
    systems = BattleSystems(
        weapon_random_percent_range=(90, 90),
        weapon_low_damage_floor_range=(5, 5),
    )
    recorder = RecordingActionSystem()
    systems.action_system = recorder  # type: ignore[assignment]

    BattleEngine(context=context, systems=systems).run()

    event_types = [event.event_type for event in context.event_bus.history]
    assert event_types.index(EventType.ROUND_STARTED) < event_types.index(EventType.DAMAGE_DEALT)


def test_round_hook_lethal_commander_damage_is_checked_before_action_order() -> None:
    context = make_two_commander_context(b_troops=1)
    register_periodic_damage(context, "round-lethal", ROUND_START_TRIGGER_TAG)
    StateLifecycleSystem().apply(
        context,
        state_id="round-lethal",
        owner_id="b1",
        source_id="a1",
        runtime_params=PeriodicDamageStateParams(DamageType.WEAPON, 1000.0),
    )
    systems = BattleSystems(
        weapon_random_percent_range=(90, 90),
        weapon_low_damage_floor_range=(5, 5),
    )
    recorder = RecordingActionSystem()
    systems.action_system = recorder  # type: ignore[assignment]

    BattleEngine(context=context, systems=systems).run()

    assert context.get_unit("b1").troops == 0
    assert recorder.calls == []
    event_types = [event.event_type for event in context.event_bus.history]
    assert EventType.BATTLE_ENDED in event_types
    assert EventType.ACTION_ORDER_DECIDED not in event_types


def test_unit_action_hook_kills_deputy_skips_action_but_closes_lifecycle() -> None:
    context = BattleContext(
        battle_id="stage7-kill-deputy",
        units={
            "a1": UnitRuntime(
                "a1", "A1", "A", 1000, 1000, 1000, 0, 80,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "b1": UnitRuntime(
                "b1", "B1", "B", 1000, 1000, 1, 0, 90,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "b2": UnitRuntime(
                "b2", "B2", "B", 1, 1, 1, 0, 200,
                lineup_position=LineupPosition.DEPUTY_1,
            ),
        },
        event_bus=EventBus(),
        random=RandomSystem(82),
        max_rounds=1,
    )
    register_periodic_damage(context, "action-lethal", UNIT_ACTION_START_TRIGGER_TAG)
    StateLifecycleSystem().apply(
        context,
        state_id="action-lethal",
        owner_id="b2",
        source_id="a1",
        runtime_params=PeriodicDamageStateParams(DamageType.WEAPON, 1000.0),
    )
    systems = BattleSystems(
        weapon_random_percent_range=(90, 90),
        weapon_low_damage_floor_range=(5, 5),
    )
    recorder = RecordingActionSystem()
    systems.action_system = recorder  # type: ignore[assignment]

    BattleEngine(context=context, systems=systems).run()

    assert "b2" not in recorder.calls
    ended = [
        event for event in context.event_bus.history
        if event.event_type is EventType.UNIT_ACTION_ENDED and event.actor_id == "b2"
    ]
    assert len(ended) == 1


def test_unit_action_hook_kills_commander_closes_action_then_battle() -> None:
    context = make_two_commander_context(b_troops=1, b_speed=200)
    register_periodic_damage(context, "action-lethal", UNIT_ACTION_START_TRIGGER_TAG)
    StateLifecycleSystem().apply(
        context,
        state_id="action-lethal",
        owner_id="b1",
        source_id="a1",
        runtime_params=PeriodicDamageStateParams(DamageType.WEAPON, 1000.0),
    )
    systems = BattleSystems(
        weapon_random_percent_range=(90, 90),
        weapon_low_damage_floor_range=(5, 5),
    )
    recorder = RecordingActionSystem()
    systems.action_system = recorder  # type: ignore[assignment]

    BattleEngine(context=context, systems=systems).run()

    assert "b1" not in recorder.calls
    history = list(context.event_bus.history)
    action_end_index = next(
        index for index, event in enumerate(history)
        if event.event_type is EventType.UNIT_ACTION_ENDED and event.actor_id == "b1"
    )
    battle_end_index = next(
        index for index, event in enumerate(history)
        if event.event_type is EventType.BATTLE_ENDED
    )
    assert action_end_index < battle_end_index


def test_nonlethal_unit_action_hook_preserves_original_action_flow() -> None:
    context = make_two_commander_context(b_troops=1000, b_speed=200)
    register_periodic_damage(context, "action-small", UNIT_ACTION_START_TRIGGER_TAG)
    StateLifecycleSystem().apply(
        context,
        state_id="action-small",
        owner_id="b1",
        source_id="a1",
        runtime_params=PeriodicDamageStateParams(DamageType.WEAPON, 0.01),
    )
    systems = BattleSystems(
        weapon_random_percent_range=(90, 90),
        weapon_low_damage_floor_range=(5, 5),
    )
    recorder = RecordingActionSystem()
    systems.action_system = recorder  # type: ignore[assignment]

    BattleEngine(context=context, systems=systems).run()

    assert "b1" in recorder.calls
    history = list(context.event_bus.history)
    start_index = next(
        index for index, event in enumerate(history)
        if event.event_type is EventType.UNIT_ACTION_STARTED and event.actor_id == "b1"
    )
    damage_index = next(
        index for index, event in enumerate(history)
        if event.event_type is EventType.DAMAGE_DEALT and event.target_id == "b1"
    )
    end_index = next(
        index for index, event in enumerate(history)
        if event.event_type is EventType.UNIT_ACTION_ENDED and event.actor_id == "b1"
    )
    assert start_index < damage_index < end_index
