"""Independent D1 audit: frozen-owner hashes plus separate adversarial harness."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / "stages/stage13/STAGE13_D1_FROZEN_OWNER_HASHES.json").read_text(encoding="utf-8"))
    checks = {}
    for path, expected in manifest["sha256_lf"].items():
        actual = hashlib.sha256((root / path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        checks[path] = {"expected": expected, "actual": actual, "pass": actual == expected}
    run = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests/test_stage13_d1_adversarial_audit.py"],
        cwd=root, text=True, capture_output=True,
    )
    passed = all(item["pass"] for item in checks.values()) and run.returncode == 0
    report = {
        "audit": "Stage13-D1 independent runtime audit",
        "provenance": "ENGINEERING_POLICY; independent harness and frozen-source comparison, not a second human reviewer",
        "baseline_runtime_sha": manifest["baseline_runtime_sha"],
        "baseline_research_sha": manifest["baseline_research_sha"],
        "frozen_owner_checks": checks,
        "adversarial_exit_code": run.returncode,
        "adversarial_output": run.stdout + run.stderr,
        "verdict": "PASS" if passed else "FAIL",
    }
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    print(output)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
