"""Reproducible multi-seed full-engine demonstration of the bounded base model."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sgs_v2.battle_core import (BattleContext, BattleSystems, BattleEngine,
    UnitRuntime, TroopType, LineupPosition, RandomSystem, EventBus,
    create_yan_xing_zhen_runtime)


def run(seed):
    units = [UnitRuntime(f"{team}{i}", f"{team}{i}", team, 10000, 10000,
        160, 180+i*10, 100-i, intelligence=170, troop_type=TroopType.CAVALRY,
        lineup_position=pos) for team in ("A", "B") for i, pos in enumerate(LineupPosition)]
    context = BattleContext(battle_id=f"yan_xing_{seed}", units={u.unit_id:u for u in units},
        random=RandomSystem(seed), event_bus=EventBus(), max_rounds=8)
    context.skill_runtimes.register(create_yan_xing_zhen_runtime("A1"))
    result = BattleEngine(context, BattleSystems()).run()
    return {"seed": seed, "result": {"winner": result.winner_team_id,
        "reason": result.reason.value, "rounds": result.rounds_completed},
        "admission": list(context.metadata["yan_xing_admissions"].values()),
        "round_history": context.metadata.get("round_team_transfer_history", [])}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    artifact = {"provenance": "USER_APPROVED_BASE_VALUE_MODEL / NOT_GAMEPLAY_FROZEN",
                "runs": [run(seed) for seed in (7, 41, 127)]}
    content = json.dumps(artifact, ensure_ascii=False, indent=2)+"\n"
    if args.output:
        args.output.write_text(content, encoding="utf-8")
    print(json.dumps({"seeds": [r["seed"] for r in artifact["runs"]],
        "round_counts": [len(r["round_history"]) for r in artifact["runs"]],
        "theft_executions": [sum(row["theft"] is not None for row in r["round_history"]) for r in artifact["runs"]]}))
