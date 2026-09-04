from sgs_v2.battle_core import (
    BattleContext,
    BattleEngine,
    BattleSystems,
    EventBus,
    EventType,
    LineupPosition,
    RandomSystem,
    UnitRuntime,
)


def format_event(event, context: BattleContext) -> str:
    """把底层 BattleEvent 格式化成一行中文战报。"""

    def unit_name(unit_id: str | None) -> str:
        if unit_id is None:
            return "未知单位"
        unit = context.units.get(unit_id)
        return unit.name if unit is not None else unit_id

    actor = unit_name(event.actor_id)
    target = unit_name(event.target_id)
    round_no = event.round_no
    payload = event.payload

    if event.event_type == EventType.BATTLE_STARTED:
        return f"战斗开始，最大回合数为 {payload.get('max_rounds', '?')} 回合。"

    if event.event_type == EventType.ROUND_STARTED:
        return f"第 {round_no} 回合开始。"

    if event.event_type == EventType.ACTION_ORDER_DECIDED:
        order_ids = payload.get("order", [])
        order_names = [unit_name(unit_id) for unit_id in order_ids]
        return f"第 {round_no} 回合行动顺序：{' → '.join(order_names)}。"

    if event.event_type == EventType.UNIT_ACTION_STARTED:
        return f"第 {round_no} 回合，{actor} 开始行动。"

    if event.event_type == EventType.NORMAL_ATTACK:
        return f"第 {round_no} 回合，{actor} 对 {target} 发动普通攻击。"

    if event.event_type == EventType.DAMAGE_DEALT:
        damage = payload.get("damage", "?")
        remain = payload.get("target_remaining_troops", "?")
        return f"第 {round_no} 回合，{actor} 对 {target} 造成 {damage} 点兵力伤害，{target} 剩余兵力 {remain}。"

    if event.event_type == EventType.UNIT_DEFEATED:
        return f"第 {round_no} 回合，{target} 兵力归零，无法继续战斗。"

    if event.event_type == EventType.UNIT_ACTION_ENDED:
        return f"第 {round_no} 回合，{actor} 行动结束。"

    if event.event_type == EventType.ROUND_ENDED:
        team_troops = payload.get("team_troops", {})
        troop_text = "，".join(
            f"{team_id}队剩余总兵力 {troops}"
            for team_id, troops in team_troops.items()
        )
        return f"第 {round_no} 回合结束，{troop_text}。"

    if event.event_type == EventType.BATTLE_ENDED:
        winner = payload.get("winner_team_id")
        reason = payload.get("reason")
        reason_text = {
            "TEAM_ELIMINATED": "敌方全军无法继续战斗",
            "COMMANDER_DEFEATED": "敌方主将阵亡",
            "MAX_ROUNDS": "达到最大回合数",
            "DRAW": "双方战平",
        }.get(reason, str(reason))
        if winner is None:
            return f"战斗结束，结果为平局。结束原因：{reason_text}。"
        return f"战斗结束，{winner}队获胜。结束原因：{reason_text}。"

    if event.event_type == EventType.PHASE_ENTERED:
        phase_name = {
            "PRE_BATTLE": "战前准备",
            "ROUND_START": "回合开始",
            "ACTION_ORDER": "行动顺序计算",
            "UNIT_ACTION_START": "单位行动开始",
            "UNIT_ACTION": "单位行动",
            "UNIT_ACTION_END": "单位行动结束",
            "ROUND_END": "回合结束",
            "BATTLE_END": "战斗结束",
        }.get(event.phase, event.phase)
        return f"[系统] 进入阶段：{phase_name}。"

    return f"第 {round_no} 回合，发生事件：{event.event_type.value}。"


def main() -> None:
    event_bus = EventBus()

    units = {
        "a1": UnitRuntime(
            unit_id="a1",
            name="A队主将",
            team_id="A",
            max_troops=1000,
            troops=1000,
            attack=240,
            defense=140,
            speed=120,
            lineup_position=LineupPosition.COMMANDER,
        ),
        "a2": UnitRuntime(
            unit_id="a2",
            name="A队第一副将",
            team_id="A",
            max_troops=900,
            troops=900,
            attack=210,
            defense=130,
            speed=105,
            lineup_position=LineupPosition.DEPUTY_1,
        ),
        "b1": UnitRuntime(
            unit_id="b1",
            name="B队主将",
            team_id="B",
            max_troops=1000,
            troops=1000,
            attack=230,
            defense=145,
            speed=115,
            lineup_position=LineupPosition.COMMANDER,
        ),
        "b2": UnitRuntime(
            unit_id="b2",
            name="B队第一副将",
            team_id="B",
            max_troops=900,
            troops=900,
            attack=205,
            defense=125,
            speed=110,
            lineup_position=LineupPosition.DEPUTY_1,
        ),
    }

    context = BattleContext(
        battle_id="stage1-demo",
        units=units,
        event_bus=event_bus,
        random=RandomSystem(seed=20260904),
        max_rounds=8,
    )

    engine = BattleEngine(
        context=context,
        systems=BattleSystems(damage_scale=4.0),
    )
    result = engine.run()

    reason_text = {
        "TEAM_ELIMINATED": "敌方全军无法继续战斗",
        "COMMANDER_DEFEATED": "敌方主将阵亡",
        "MAX_ROUNDS": "达到最大回合数",
        "DRAW": "双方战平",
    }.get(result.reason.value, result.reason.value)

    print("=== 战斗结果 ===")
    print(f"胜方：{result.winner_team_id or '平局'}")
    print(f"结束原因：{reason_text}")
    print(f"完成回合：{result.rounds_completed}")
    print(f"最终兵力：{result.final_troops}")
    print(f"事件总数：{len(event_bus.history)}")

    print("\n=== 前 20 条战报事件 ===")
    for event in event_bus.history[:]:
        print(format_event(event, context))


if __name__ == "__main__":
    main()
