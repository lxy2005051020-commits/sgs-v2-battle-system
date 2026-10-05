"""Reproduce local verification and a seeded, inspectable full-engine example."""
from dataclasses import asdict
from pathlib import Path
import json
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sgs_v2.battle_core import (BattleContext, BattleSystems, BattleEngine, EventBus,
    RandomSystem, UnitRuntime, TroopType, LineupPosition, register_official_state_definitions,
    create_xian_deng_si_shi_runtime)


def main():
    root = Path(__file__).resolve().parents[1]
    out = root / "stages" / "stage14" / "xiandeng_evidence"
    out.mkdir(parents=True, exist_ok=True)
    checks = {}
    for name, args in (("focused", ["tests/test_stage14_troop_xian_deng_si_shi.py"]), ("full", [])):
        result = subprocess.run([sys.executable, "-m", "pytest", *args, "-q", "--tb=short"],
            cwd=root, text=True, encoding="utf-8", errors="replace", capture_output=True)
        (out / f"{name}_pytest.txt").write_text(result.stdout + result.stderr, encoding="utf-8")
        checks[name] = {"exit_code": result.returncode, "summary": result.stdout.strip().splitlines()[-1]}
        print(name, checks[name])
    units = {}
    for side in ("a", "b"):
        for i, position in enumerate(LineupPosition, 1):
            uid = f"{side}{i}"
            units[uid] = UnitRuntime(uid, uid, side, 10000, 10000, 120,
                500 if uid == "a1" else 120, 10 if side == "a" else 200,
                troop_type=TroopType.BOW if side == "a" else TroopType.SPEAR,
                lineup_position=position)
    context = BattleContext("xiandeng-seeded-demo", units, EventBus(), RandomSystem(42), max_rounds=5)
    register_official_state_definitions(context.states)
    context.skill_runtimes.register(create_xian_deng_si_shi_runtime("a1"))
    systems = BattleSystems()
    battle_result = BattleEngine(context, systems).run()
    (out / "demo_events.json").write_text(json.dumps([asdict(e) for e in context.event_bus.history],
        ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    checks["demo"] = {"seed": 42, "result": asdict(battle_result),
        "ended": context.ended, "remaining_states": len(context.states.find()),
        "event_count": len(context.event_bus.history), "model": "XIANDENG_USER_OPENING_COMMAND_FIT_V1"}
    checks["registry"] = subprocess.run([sys.executable, "-c",
        "from sgs_v2.battle_core.troop_admission import TROOP_SKILL_REGISTRY; "
        "from sgs_v2.battle_core.troop_skills.xian_deng_si_shi import SKILL,CONFIG; "
        "assert TROOP_SKILL_REGISTRY['20246'] is CONFIG; assert CONFIG.definition_factory()==SKILL"], cwd=root).returncode
    checks["runtime_base"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    checks["status"] = "LOCAL_VERIFIED_NOT_PUBLISHED"
    (out / "verification.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    if any(checks[k]["exit_code"] for k in ("focused", "full")) or checks["registry"]:
        raise SystemExit(1)
    assert context.ended and not context.states.find()


if __name__ == "__main__":
    main()
