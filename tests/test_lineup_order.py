from __future__ import annotations

from sgs_v2.battle_core import (
    BattleContext,
    EventBus,
    LineupPosition,
    RandomSystem,
    TargetSystem,
    UnitRuntime,
)


def test_full_selection_uses_commander_then_deputy_order_without_randomness() -> None:
    units = {
        "enemy-2": UnitRuntime(
            "enemy-2", "第二副将", "B", 100, 100, 1, 1, 1,
            lineup_position=LineupPosition.DEPUTY_2,
        ),
        "actor": UnitRuntime(
            "actor", "攻击方", "A", 100, 100, 1, 1, 1,
            lineup_position=LineupPosition.COMMANDER,
        ),
        "enemy-1": UnitRuntime(
            "enemy-1", "第一副将", "B", 100, 100, 1, 1, 1,
            lineup_position=LineupPosition.DEPUTY_1,
        ),
        "enemy-main": UnitRuntime(
            "enemy-main", "主将", "B", 100, 100, 1, 1, 1,
            lineup_position=LineupPosition.COMMANDER,
        ),
    }
    context = BattleContext(
        battle_id="lineup-order",
        units=units,
        event_bus=EventBus(),
        random=RandomSystem(20260904),
    )

    targets = TargetSystem()
    enemies = targets.enemies(context, context.get_unit("actor"))
    selected = targets.random_units(context, enemies, count=99)

    assert [unit.unit_id for unit in selected] == [
        "enemy-main",
        "enemy-1",
        "enemy-2",
    ]

    # 全选结果确定，不应消耗随机流。
    assert context.random.random() == RandomSystem(20260904).random()
