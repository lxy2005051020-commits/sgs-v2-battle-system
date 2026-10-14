"""Independent structural/frozen-owner audit; gameplay evidence is out of scope."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "3c23534ecd33ff8a72160bf106e4838daa6cdce2"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    checks = {}
    # Independent of the existing D1 manifest: compare current owners to the
    # actual implementation baseline including Engine and Shared Foundation.
    for name in ("engine.py", "effect_executor.py", "state_lifecycle_system.py",
        "state_application.py", "state_removal.py", "state_effectiveness.py",
        "damage_system.py", "damage_instance_coordinator.py", "recovery_system.py",
        "target_system.py", "trigger_system.py", "random_system.py"):
        relative = "sgs_v2/battle_core/"+name
        before = subprocess.run(["git", "show", BASELINE+":"+relative], cwd=ROOT,
                                capture_output=True, check=True).stdout.replace(b"\r\n", b"\n")
        after = (ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
        checks[relative+":unchanged"] = hashlib.sha256(before).digest() == hashlib.sha256(after).digest()
    for name in ("round_team_transfer.py", "state_transfer_support.py", "state_transfer_policy.py", "transferred_potency.py", "yan_xing_zhen.py"):
        path = ROOT / "sgs_v2/battle_core" / name
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        checks[name+":no_independent_random"] = not any(isinstance(node, ast.Import)
            and any(alias.name == "random" for alias in node.names) for node in ast.walk(tree))
        checks[name+":no_direct_state_or_troop_mutation"] = not any(
            isinstance(node, ast.Assign) and any(isinstance(target, ast.Attribute)
                and target.attr in ("troops", "defense", "attack", "intelligence", "speed")
                for target in node.targets) for node in ast.walk(tree))
        if name != "yan_xing_zhen.py":
            checks[name+":no_tactic_id_special_case"] = "20862" not in source and "雁行阵" not in source
    evidence = ROOT / "stages/stage14/yan_xing_evidence"
    manifest = json.loads((evidence / "source_manifest.json").read_text(encoding="utf-8"))
    for key in ("source_csv", "source_json"):
        checks[key+":source_hash"] = hashlib.sha256(Path(manifest[key]).read_bytes()).hexdigest() == manifest[key+"_sha256"]
    for name in ("audit_stage13_d1.json", "audit_qingzhou.json"):
        checks[name+":PASS"] = json.loads((ROOT / "stages/stage14/yan_xing_complete_evidence" / name).read_text())["verdict"] == "PASS"
    demo = json.loads((ROOT / "stages/stage14/yan_xing_complete_evidence/demo_runs.json").read_text(encoding="utf-8"))
    checks["three_seeds_full_engine_8_rounds"] = len(demo["runs"]) == 3 and all(
        len(run["round_history"]) == 8 for run in demo["runs"])
    report = {"audit": "Yan Xing completion independent structural and baseline-owner audit",
        "baseline": BASELINE, "checks": checks,
        "verdict": "PASS" if all(checks.values()) else "FAIL",
        "scope": "automated engineering audit; complete non-scaling transfer model; NOT_GAMEPLAY_FROZEN"}
    content = json.dumps(report, ensure_ascii=False, indent=2)+"\n"
    if args.output:
        args.output.write_text(content, encoding="utf-8")
    print(report["verdict"], len(checks), "checks")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
