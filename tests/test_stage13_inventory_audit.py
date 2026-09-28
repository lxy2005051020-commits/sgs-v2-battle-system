from __future__ import annotations

from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STAGE13 = ROOT / "stages" / "stage13"

REQUIRED_DOCS = (
    "STAGE13_CORE_GAMEPLAY_MECHANISM_INVENTORY.md",
    "STAGE13_CORE_GAMEPLAY_GAP_LEDGER.md",
    "STAGE13_CORE_RUNTIME_OWNER_MATRIX.md",
    "STAGE13_CORE_MECHANISM_TEST_MATRIX.md",
    "STAGE13_RESEARCH_GAP_LEDGER.md",
    "STAGE13_RUNTIME_GOVERNANCE_LEDGER.md",
)

CLASSIFICATIONS = {
    "ALREADY_IMPLEMENTED",
    "PARTIAL",
    "MISSING",
    "RESEARCH_REQUIRED",
    "RUNTIME_GOVERNANCE_REQUIRED",
    "UNSUPPORTED",
    "NOT_NEEDED",
}


def _read(name: str) -> str:
    return (STAGE13 / name).read_text(encoding="utf-8")


def test_stage13_inventory_authorities_exist() -> None:
    for name in REQUIRED_DOCS:
        assert (STAGE13 / name).is_file(), name


def test_stage13_inventory_has_exactly_48_classified_mechanisms() -> None:
    text = _read("STAGE13_CORE_GAMEPLAY_MECHANISM_INVENTORY.md")
    rows = [line for line in text.splitlines() if line.startswith("| CGM-")]
    assert len(rows) == 48

    parsed = []
    for row in rows:
        columns = [column.strip() for column in row.strip().strip("|").split("|")]
        assert len(columns) == 9, row
        assert columns[6] in CLASSIFICATIONS, row
        assert columns[7] in {"YES", "NO"}, row
        parsed.append(columns[6])

    assert Counter(parsed) == Counter(
        {
            "ALREADY_IMPLEMENTED": 22,
            "PARTIAL": 16,
            "MISSING": 4,
            "RESEARCH_REQUIRED": 2,
            "RUNTIME_GOVERNANCE_REQUIRED": 1,
            "UNSUPPORTED": 1,
            "NOT_NEEDED": 2,
        }
    )


def test_stage13_entry_gate_is_active_but_engine_not_frozen() -> None:
    index = _read("README.md")
    assert "STAGE13_ENTRY_GATE                = PASS" in index
    assert "Stage13 Active                    = YES" in index
    assert "Core Gameplay Engine              = NOT YET FROZEN" in index
    assert "Skill Runtime Readiness           = NOT YET READY" in index


def test_stage13_preserves_distribution_research_debt() -> None:
    inventory = _read("STAGE13_CORE_GAMEPLAY_MECHANISM_INVENTORY.md")
    research = _read("STAGE13_RESEARCH_GAP_LEDGER.md")
    assert "690086 DISTRIBUTION / DSTS9-B02         OPEN / UNOBSERVED" in inventory
    assert "DSTS9-B02" in research
    assert "DO_NOT_AUTO_REOPEN" in research


def test_stage13_research_and_runtime_governance_are_separate() -> None:
    research = _read("STAGE13_RESEARCH_GAP_LEDGER.md")
    governance = _read("STAGE13_RUNTIME_GOVERNANCE_LEDGER.md")

    assert "RQ13-001" in research
    assert "RQ13-002" in research
    assert "RESEARCH_REQUIRED" in research

    assert "RG13-001" in governance
    assert "RG13-010" in governance
    assert "No Stage13-A row above is a Default" in governance


def test_stage13_does_not_activate_skill_runtime() -> None:
    index = _read("README.md")
    assert "full skill runtimes remain deferred" in index.lower()
    assert "Stage14+" in index
    assert "Skill Runtime Readiness = READY" in index
    assert "Skill Runtime Readiness           = NOT YET READY" in index


def test_stage13_next_is_unique_closure_planning() -> None:
    inventory = _read("STAGE13_CORE_GAMEPLAY_MECHANISM_INVENTORY.md")
    index = _read("README.md")
    token = "STAGE13_B_GAP_CLASSIFICATION_AND_CLOSURE_PLANNING"
    assert token in inventory
    assert token in index
