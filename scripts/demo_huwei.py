"""Deterministic engine demo; generated events are engineering evidence only."""
from pathlib import Path
from fractions import Fraction
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sgs_v2.battle_core import (BattleContext, BattleEngine, BattleSystems, EventBus,
    LineupPosition, RandomSystem, TroopType, UnitRuntime, create_hu_wei_jun_runtime,
    register_official_state_definitions)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    units = {}
    for team in ("a", "b"):
        for i, position in enumerate(LineupPosition, 1):
            uid = f"{team}{i}"
            units[uid] = UnitRuntime(uid, uid, team, 10000, 10000, attack=180,
                defense=120, intelligence=100, speed=50 if team == "a" else 200,
                troop_type=TroopType.SHIELD if team == "a" else TroopType.SPEAR,
                lineup_position=position)
    context = BattleContext("huwei-provisional-demo", units, EventBus(), RandomSystem(42), max_rounds=6)
    register_official_state_definitions(context.states)
    context.skill_runtimes.register(create_hu_wei_jun_runtime("a3"))
    result = BattleEngine(context, BattleSystems()).run()
    report = {
        "status": "USER_PROVISIONAL_MODEL; NOT_EMPIRICALLY_FROZEN",
        "formula": "0.72 + min(max(0, entry_troops-current_troops)//250, 40)/100",
        "rounds_completed": result.rounds_completed,
        "final_troops": result.final_troops,
        "events": [{"sequence": e.sequence, "round": e.round_no, "phase": e.phase,
            "type": e.event_type.value, "actor": e.actor_id, "target": e.target_id,
            "payload": e.payload} for e in context.event_bus.history],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    def exact_json(value):
        if isinstance(value, Fraction):
            return {"numerator": value.numerator, "denominator": value.denominator}
        raise TypeError(f"Unsupported event value: {type(value).__name__}")
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2,
        default=exact_json)+"\n", encoding="utf-8")
    print(f"PASS: {result.rounds_completed} rounds; {len(report['events'])} events; {args.output}")


if __name__ == "__main__":
    main()
