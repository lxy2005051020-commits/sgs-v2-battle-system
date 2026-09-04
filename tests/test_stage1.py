from __future__ import annotations

from sgs_v2.battle_core import (
    BattleContext,
    BattleEngine,
    BattleSystems,
    BattlePhase,
    EventBus,
    EventType,
    LineupPosition,
    RandomSystem,
    UnitRuntime,
)


def make_context(seed: int = 7) -> BattleContext:
    units = {
        "a": UnitRuntime(
            unit_id="a",
            name="A",
            team_id="A",
            max_troops=300,
            troops=300,
            attack=220,
            defense=100,
            speed=100,
            lineup_position=LineupPosition.COMMANDER,
        ),
        "b": UnitRuntime(
            unit_id="b",
            name="B",
            team_id="B",
            max_troops=300,
            troops=300,
            attack=210,
            defense=100,
            speed=100,
            lineup_position=LineupPosition.COMMANDER,
        ),
    }
    return BattleContext(
        battle_id=f"test-{seed}",
        units=units,
        event_bus=EventBus(),
        random=RandomSystem(seed=seed),
        max_rounds=8,
    )


def run_once(seed: int = 7):
    context = make_context(seed)
    engine = BattleEngine(
        context=context,
        systems=BattleSystems(damage_scale=5.0),
    )
    result = engine.run()
    return context, result


def test_no_skill_battle_completes() -> None:
    context, result = run_once()
    assert context.ended is True
    assert context.result == result
    assert context.current_phase == BattlePhase.BATTLE_END.value


def test_required_major_phases_emit_events() -> None:
    context, _ = run_once()
    entered = {
        event.payload["phase"]
        for event in context.event_bus.history
        if event.event_type == EventType.PHASE_ENTERED
    }
    assert BattlePhase.PRE_BATTLE.value in entered
    assert BattlePhase.ROUND_START.value in entered
    assert BattlePhase.ACTION_ORDER.value in entered
    assert BattlePhase.UNIT_ACTION_START.value in entered
    assert BattlePhase.UNIT_ACTION.value in entered
    assert BattlePhase.UNIT_ACTION_END.value in entered
    assert BattlePhase.BATTLE_END.value in entered


def test_event_sequence_is_strictly_increasing() -> None:
    context, _ = run_once()
    sequences = [event.sequence for event in context.event_bus.history]
    assert sequences == list(range(1, len(sequences) + 1))


def test_same_seed_is_reproducible() -> None:
    context1, result1 = run_once(seed=1234)
    context2, result2 = run_once(seed=1234)

    assert result1 == result2

    compact1 = [
        (
            e.event_type.value,
            e.round_no,
            e.actor_id,
            e.target_id,
            e.payload,
        )
        for e in context1.event_bus.history
    ]
    compact2 = [
        (
            e.event_type.value,
            e.round_no,
            e.actor_id,
            e.target_id,
            e.payload,
        )
        for e in context2.event_bus.history
    ]
    assert compact1 == compact2


def test_defeated_unit_does_not_act_after_death() -> None:
    context = BattleContext(
        battle_id="death-skip",
        units={
            "fast": UnitRuntime(
                unit_id="fast",
                name="Fast",
                team_id="A",
                max_troops=500,
                troops=500,
                attack=1000,
                defense=100,
                speed=200,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "slow": UnitRuntime(
                unit_id="slow",
                name="Slow",
                team_id="B",
                max_troops=10,
                troops=10,
                attack=100,
                defense=0,
                speed=1,
                lineup_position=LineupPosition.COMMANDER,
            ),
        },
        event_bus=EventBus(),
        random=RandomSystem(seed=1),
        max_rounds=1,
    )
    BattleEngine(
        context=context,
        systems=BattleSystems(damage_scale=10.0),
    ).run()

    started_actor_ids = [
        e.actor_id
        for e in context.event_bus.history
        if e.event_type == EventType.UNIT_ACTION_STARTED
    ]
    assert started_actor_ids == ["fast"]
