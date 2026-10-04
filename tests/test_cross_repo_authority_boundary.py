"""Offline engineering boundary: no local research bodies or floating authority pins."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]


def test_battle_consumes_immutable_research_references_without_research_trees() -> None:
    for path in ("research", "stages/stage9/research", "stages/stage11/research"):
        assert not (ROOT / path).exists()
    references = json.loads((ROOT / "docs/runtime/RESEARCH_AUTHORITY_REFERENCES.json").read_text(encoding="utf-8"))
    assert references
    commits = set()
    for reference in references.values():
        assert reference["repository"] == "lxy2005051020-commits/sgs-state-mechanics-research"
        assert re.fullmatch(r"[a-f0-9]{40}", reference["commit"])
        assert reference["path"] and not reference["path"].startswith("/")
        assert ".." not in Path(reference["path"]).parts
        assert reference["status"] in {"FROZEN", "CURRENT", "HISTORICAL", "REFERENCE_ONLY"}
        commits.add(reference["commit"])
    assert len(commits) == 1


def test_stage9_closed_contracts_have_explicit_frozen_external_authority() -> None:
    references = json.loads((ROOT / "docs/runtime/RESEARCH_AUTHORITY_REFERENCES.json").read_text(encoding="utf-8"))
    for name in (
        "STAGE9_COUNTERATTACK_MECHANICS_FREEZE_RECORD.md",
        "STAGE9_DISTRIBUTION_MECHANICS_FREEZE_RECORD.md",
        "STAGE9_CHAIN_MECHANICS_FREEZE_RECORD.md",
        "STAGE9_TAUNT_MECHANICS_FREEZE_RECORD.md",
        "STAGE9_EXECUTION_RIGHT_AND_DEATH_SCOPE_CONTRACT.md",
        "STAGE9_BATTLE_FINALIZATION_BARRIER_CONTRACT.md",
    ):
        ref = references["stages/stage9/research/core_arbitration_v2/" + name]
        assert ref["path"] == "stage9_core_arbitration/core_arbitration_v2/" + name
        assert ref["status"] == "FROZEN"
