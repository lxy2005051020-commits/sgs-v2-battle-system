"""Independent engineering harness: frozen-owner comparison and engine-trace oracle.

This is an automated runtime audit, not a second human reviewer or gameplay
research. Its oracle uses the declared provisional contract, never the adapter's
formula output as its expected value.
"""
import argparse
import ast
from fractions import Fraction
import hashlib
import json
from math import ceil
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
GENERIC = (
    "additive_treatment_formula.py", "scheduled_team_recovery.py",
    "priority_target_system.py", "recovery_capacity.py", "provider_gated_counter.py",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    checks = {}
    manifest = json.loads((ROOT / "stages/stage13/STAGE13_D1_FROZEN_OWNER_HASHES.json").read_text(encoding="utf-8"))
    hashes = {}
    for path, expected in manifest["sha256_lf"].items():
        actual = hashlib.sha256((ROOT / path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        hashes[path] = {"actual": actual, "expected": expected, "pass": actual == expected}
    checks["frozen_owners_unchanged"] = all(v["pass"] for v in hashes.values())
    for name in GENERIC:
        source = (ROOT / "sgs_v2/battle_core" / name).read_text(encoding="utf-8")
        tree = ast.parse(source)
        mutations = []
        random_imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store):
                if node.attr in {"troops", "wounded_troops", "_wounded_pool_authoritative"}:
                    mutations.append(node.lineno)
            if isinstance(node, ast.Import):
                random_imports.extend(a.name for a in node.names if a.name == "random")
            if isinstance(node, ast.ImportFrom) and node.module == "random":
                random_imports.append(node.module)
        checks[f"{name}:no_troop_mutation_or_random"] = not mutations and not random_imports
        checks[f"{name}:no_tactic_id_coupling"] = "20153" not in source and "qing_zhou" not in source.lower()
    run = subprocess.run([sys.executable, str(ROOT / "scripts/demo_qingzhou.py")],
                         cwd=ROOT, text=True, encoding="utf-8", capture_output=True)
    checks["engine_demo_exit_zero"] = run.returncode == 0
    observed = {}
    if run.returncode == 0:
        demo = json.loads(run.stdout)
        summaries = [e for e in demo["events"] if e["type"] == "RECOVERY_RESOLVED"]
        checks["one_third_round_summary"] = len(summaries) == 1 and summaries[0]["round"] == 3
        if summaries:
            event = summaries[0]
            summary = event["payload"]
            loss_events = [e for e in demo["events"] if e["round"] in (1, 2)
                           and e["actor"] and e["actor"].startswith("b")
                           and e["target"] and e["target"].startswith("a")
                           and e["type"] in {"DAMAGE_DEALT", "DIRECT_TROOP_LOSS"}]
            expected_loss = sum(e["payload"]["damage" if e["type"] == "DAMAGE_DEALT" else "actual_loss"]
                                for e in loss_events)
            table = {}
            import csv
            with (ROOT / "data/normal_attack/troop_function_table_1_10000.csv").open(encoding="utf-8-sig", newline="") as file:
                for row in csv.DictReader(file):
                    table[int(row["N"])] = int(row["F_兵力函数"])
            snapshot = demo["source_snapshot"]
            b = table[snapshot["troops"]]
            expected_pool = ceil((b + snapshot["force"] + Fraction(expected_loss, 10)) * Fraction(18, 10))
            checks["loss_sum_matches_settled_trace"] = summary["damage_basis"] == expected_loss
            checks["loss_provenance_matches_trace"] = summary["damage_event_sequences"] == [e["sequence"] for e in loss_events]
            checks["formula_matches_independent_fraction_oracle"] = summary["nominal_recovery"] == expected_pool
            checks["distinct_base_and_force"] = summary["source_attribute"] == snapshot["force"] and summary["troop_function_value"] == b
            checks["before_third_round_action_damage"] = all(e["sequence"] > event["sequence"]
                for e in demo["events"] if e["round"] == 3 and e["type"] == "DAMAGE_DEALT")
            checks["cao_cao_placeholder"] = demo["cao_cao_commander_enhancement"] is None
            checks["counter_round_window"] = all(e["round"] in (1, 2)
                for e in demo["events"] if e["type"] == "COUNTER_EXECUTE")
            checks["counter_executed"] = any(e["type"] == "COUNTER_EXECUTE" for e in demo["events"])
            observed = {"damage_basis": expected_loss, "troop_function": b, "force": snapshot["force"],
                        "expected_pool": expected_pool, "actual_pool": summary["nominal_recovery"]}
    report = {"audit": "Qingzhou automated independent engineering audit", "verdict": "PASS" if all(checks.values()) else "FAIL",
        "scope": "runtime wiring and user-provisional formula; no empirical gameplay freeze", "checks": checks,
        "frozen_owner_checks": hashes, "observed": observed, "demo_stderr": run.stderr}
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text)
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
