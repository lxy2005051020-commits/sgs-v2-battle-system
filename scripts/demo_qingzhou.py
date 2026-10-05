"""Deterministic engine demonstration of the explicitly provisional Qingzhou model."""
from pathlib import Path
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sgs_v2.battle_core import (
    BattleContext, BattleEngine, BattleSystems, EventBus, EventType, LineupPosition,
    RandomSystem, TroopType, UnitRuntime, create_qing_zhou_bing_runtime,
    register_official_state_definitions,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    units = {}
    for team in ("a", "b"):
        for i, position in enumerate(LineupPosition, 1):
            uid = f"{team}{i}"
            units[uid] = UnitRuntime(uid, uid, team, 10000, 10000,
                attack=200 if team == "a" else 300, defense=120, intelligence=100,
                speed=50 if team == "a" else 200, troop_type=TroopType.SPEAR,
                lineup_position=position)
    context = BattleContext("qingzhou-provisional-demo", units, EventBus(), RandomSystem(42), max_rounds=3)
    register_official_state_definitions(context.states)
    context.skill_runtimes.register(create_qing_zhou_bing_runtime("a3"))
    result = BattleEngine(context, BattleSystems()).run()
    selected = {EventType.STATE_APPLIED, EventType.COUNTER_EXECUTE,
                EventType.DAMAGE_DEALT, EventType.DIRECT_TROOP_LOSS,
                EventType.TROOPS_RECOVERED, EventType.RECOVERY_PREVENTED,
                EventType.RECOVERY_RESOLVED}
    report = {
        "status": "USER_PROVISIONAL_MODEL; NOT_EMPIRICALLY_FROZEN",
        "formula": "CEIL((B(N)+FORCE+enemy_team_actual_loss/10)*1.8)",
        "cao_cao_commander_enhancement": None,
        "source_snapshot": {"owner_id": "a3", "troops": 10000, "force": 200,
                            "read_time": "PRE_BATTLE"},
        "rounds_completed": result.rounds_completed,
        "final_troops": result.final_troops,
        "events": [{"sequence": e.sequence, "round": e.round_no, "phase": e.phase,
                    "type": e.event_type.value, "actor": e.actor_id, "target": e.target_id,
                    "payload": e.payload} for e in context.event_bus.history if e.event_type in selected],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
