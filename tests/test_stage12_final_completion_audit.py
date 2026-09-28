from __future__ import annotations

import ast
import re
from pathlib import Path

from sgs_v2.battle_core.equipment_effectiveness import EquipmentContributionKind
from sgs_v2.battle_core.insight_integration import (
    INSIGHT_EXPLICIT_NON_PROTECTED_STATE_IDS,
    INSIGHT_PROTECTED_STATE_IDS,
)
from sgs_v2.battle_core.official_state_catalog import OFFICIAL_STATE_CATALOG, OfficialStateId

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "sgs_v2" / "battle_core"
STAGE12 = ROOT / "stages" / "stage12"
TESTS = ROOT / "tests"
FINAL_AUTHORITY = STAGE12 / "STAGE12_FINAL_COMPLETION_FREEZE_AUDIT.md"

SEVEN = {
    "690089_INSIGHT": ("insight_integration.py", "STAGE12_690089_INSIGHT_RUNTIME_FREEZE_AUDIT.md"),
    "690101_EXHAUSTION": ("exhaustion_integration.py", "STAGE12_690101_EXHAUSTION_RUNTIME_FREEZE_AUDIT.md"),
    "690107_FALSE_REPORT": ("false_report_integration.py", "STAGE12_690107_FALSE_REPORT_RUNTIME_FREEZE_AUDIT.md"),
    "690108_PROVOCATION": ("provocation_integration.py", "STAGE12_690108_PROVOCATION_RUNTIME_FREEZE_AUDIT.md"),
    "690222_INTIMIDATION": ("intimidation_integration.py", "STAGE12_690222_INTIMIDATION_RUNTIME_FREEZE_AUDIT.md"),
    "690109_SABOTAGE": ("sabotage_integration.py", "STAGE12_690109_SABOTAGE_RUNTIME_FREEZE_AUDIT.md"),
    "690110_CAPTURE": ("capture_integration.py", "STAGE12_690110_CAPTURE_RUNTIME_FREEZE_AUDIT.md"),
}

CANONICAL_OWNER_CLASSES = {
    "StateEffectivenessPolicy", "ProviderValidityPolicy", "SkillPermissionPolicy",
    "SkillOperationAdmissionCoordinator", "SkillTargetPolicy", "TargetSystem",
    "TargetResolutionSystem", "RecoverySystem", "EquipmentEffectivenessPolicy",
    "DependencyEvaluationSupport", "EffectivenessTransitionCoordinator",
    "ExecutionRightSpec", "PreparationStateOwner", "PreparationInterruptionPort",
    "StateLifecycleSystem", "StateRegistry", "StateAdmissionPolicy",
    "StateConflictPolicy", "StateRemovalPolicy",
}

def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def _class_counts() -> dict[str, int]:
    counts = {name: 0 for name in CANONICAL_OWNER_CLASSES}
    for path in CORE.glob("*.py"):
        tree = ast.parse(_text(path), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.AsyncFunctionDef)) and node.name in counts:
                counts[node.name] += 1
    return counts

def _assert_anchor(path: str, name: str) -> None:
    source = _text(TESTS / path)
    assert f"def {name}(" in source, f"missing executable anchor {path}::{name}"

def test_stage12_all_seven_runtime_authorities_exist() -> None:
    assert len(SEVEN) == 7
    for _state, (integration, authority) in SEVEN.items():
        assert (CORE / integration).is_file()
        assert (STAGE12 / authority).is_file()

def test_stage12_all_seven_runtime_statuses_are_frozen() -> None:
    for state, (_integration, authority) in SEVEN.items():
        text = _text(STAGE12 / authority).upper()
        assert "PASS" in text, state
        assert "FROZEN" in text, state
        assert "BLOCKER" in text, state

def test_stage12_no_shadow_state_effectiveness_owner() -> None:
    assert _class_counts()["StateEffectivenessPolicy"] == 1

def test_stage12_no_shadow_provider_validity_owner() -> None:
    assert _class_counts()["ProviderValidityPolicy"] == 1

def test_stage12_no_shadow_skill_target_owner() -> None:
    assert _class_counts()["SkillTargetPolicy"] == 1

def test_stage12_no_shadow_equipment_effectiveness_owner() -> None:
    assert _class_counts()["EquipmentEffectivenessPolicy"] == 1

def test_stage12_all_canonical_owners_are_unique() -> None:
    assert _class_counts() == {name: 1 for name in CANONICAL_OWNER_CLASSES}

def test_stage12_only_canonical_rng_is_used() -> None:
    offenders: list[str] = []
    for path in CORE.glob("*.py"):
        source = _text(path)
        for pattern in (r"^\s*import\s+random\b", r"^\s*from\s+random\b", r"numpy\.random", r"np\.random", r"\brandom\.Random\s*\("):
            if re.search(pattern, source, flags=re.MULTILINE) and path.name != "random_system.py":
                offenders.append(path.name)
    assert offenders == []

def test_stage12_insight_protected_set_exact() -> None:
    expected = {
        OfficialStateId.SILENCE.value, OfficialStateId.DISARM.value,
        OfficialStateId.CONFUSION.value, OfficialStateId.WEAKNESS.value,
        OfficialStateId.HEALING_BAN.value, OfficialStateId.TAUNT.value,
        OfficialStateId.PROVOKE.value, OfficialStateId.EQUIPMENT_DISABLE.value,
        OfficialStateId.STUN.value,
    }
    assert INSIGHT_PROTECTED_STATE_IDS == expected
    assert INSIGHT_EXPLICIT_NON_PROTECTED_STATE_IDS == {
        OfficialStateId.FALSE_REPORT.value,
        OfficialStateId.INTIMIDATION.value,
        OfficialStateId.CAPTURE.value,
    }

def test_stage12_provider_suppression_causes_compose() -> None:
    _assert_anchor("test_stage12_690107_false_report.py", "test_self_suppression_and_multiple_causes_restore_correctly")
    _assert_anchor("test_stage12_690222_intimidation.py", "test_false_report_and_intimidation_suppression_causes_compose")
    _assert_anchor("test_stage12_690110_capture_runtime_freeze_audit.py", "test_capture_false_report_suppression_causes_compose")
    _assert_anchor("test_stage12_690110_capture_runtime_freeze_audit.py", "test_capture_intimidation_suppression_causes_compose")

def test_stage12_equipment_contribution_causes_remain_typed() -> None:
    assert {kind.value for kind in EquipmentContributionKind} == {
        "ATTRIBUTE", "DAMAGE_MODIFIER", "RECOVERY_MODIFIER",
        "TRIGGER", "SCHEDULED_TRIGGER", "LIVE_EFFECT",
    }
    source = _text(CORE / "equipment_effectiveness.py")
    assert "suppression_causes: tuple[SuppressionCause, ...]" in source
    assert "equipment_disabled" not in source

def test_stage12_capture_stun_does_not_consume_stun() -> None:
    _assert_anchor("test_stage12_690110_capture.py", "test_capture_plus_stun_does_not_consume_stun_counter")
    _assert_anchor("test_stage12_690110_capture_runtime_freeze_audit.py", "test_capture_does_not_consume_stun_when_capture_blocks_action")

def test_stage12_capture_damage_three_way_discriminator() -> None:
    _assert_anchor("test_stage12_690110_capture.py", "test_capture_damage_denial_preempts_weakness_zero_damage_path")
    _assert_anchor("test_stage12_690110_capture.py", "test_counter_opportunity_exists_but_counter_damage_is_denied")
    _assert_anchor("test_stage12_690110_capture.py", "test_attached_active_origin_dot_continues_after_capture")

def test_stage12_provocation_capture_target_domains_remain_separate() -> None:
    provocation = _text(CORE / "provocation_integration.py")
    capture = _text(CORE / "capture_integration.py")
    assert "TargetOperationDomain.SKILL" in provocation
    assert "TargetRelation.ENEMY" in provocation
    assert "TargetRelation.ALLY" in capture
    assert "TargetSystem" not in provocation
    _assert_anchor("test_stage12_shared_foundation_round3.py", "test_normal_attack_domain_does_not_depend_on_skill_target_policy")

def test_stage12_intimidation_refresh_vs_resume() -> None:
    _assert_anchor("test_stage12_690222_intimidation_runtime_freeze_audit.py", "test_refresh_rerolls_binding")
    _assert_anchor("test_stage12_690222_intimidation_runtime_freeze_audit.py", "test_resume_retains_binding_zero_rng")

def test_stage12_sabotage_resume_has_no_replay() -> None:
    _assert_anchor("test_stage12_690109_sabotage_runtime_freeze_audit.py", "test_audit_recovery_modifier_future_only_resume_no_backfill")
    _assert_anchor("test_stage12_690109_sabotage_runtime_freeze_audit.py", "test_audit_scheduled_window_missed_under_sabotage_is_not_replayed")

def test_stage12_same_envelope_has_no_ghost_resume() -> None:
    _assert_anchor("test_stage12_690089_insight.py", "test_same_envelope_insight_and_protected_expiry_has_no_transient_resume")
    _assert_anchor("test_stage12_690101_exhaustion.py", "test_same_envelope_insight_and_exhaustion_expiry_has_no_ghost_denial")
    _assert_anchor("test_stage12_690222_intimidation_runtime_freeze_audit.py", "test_same_envelope_no_ghost_resume_or_prep_interrupt")
    _assert_anchor("test_stage12_690109_sabotage_runtime_freeze_audit.py", "test_audit_same_envelope_insight_and_sabotage_expiry_emits_no_provider_ghost_transition")

def test_stage12_runtime_defaults_preserve_provenance() -> None:
    ledger = _text(STAGE12 / "STAGE12_RUNTIME_DEFAULT_LEDGER.md")
    for i in range(1, 7):
        token = f"RD-SF-00{i}"
        assert token in ledger
        section = ledger.split(f"## {token}", 1)[1]
        section = section.split("\n## ", 1)[0]
        assert "PROJECT_RUNTIME_DEFAULT" in section
        assert "NOT_EMPIRICALLY_FROZEN" in section

def test_stage12_bounded_unknowns_have_no_production_leak() -> None:
    provocation = _text(CORE / "provocation_integration.py")
    intimidation = _text(CORE / "intimidation_integration.py")
    sabotage = _text(CORE / "sabotage_integration.py")
    capture = _text(CORE / "capture_integration.py")
    assert "BU-P06" in provocation and "UNSUPPORTED_BOUNDARY" in provocation
    assert "UNSUPPORTED_BOUNDARY" in intimidation
    assert "SkillType.TALENT" not in intimidation.split("INTIMIDATION_SUPPORTED_SKILL_TYPES", 1)[1].split("}", 1)[0]
    assert "B-SAB-09" in sabotage and "UNSUPPORTED_BOUNDARY" in sabotage
    assert "Q70-Q74" in capture and "UNSUPPORTED_BOUNDARY" in capture
    _assert_anchor("test_stage12_690110_capture.py", "test_already_created_damage_request_boundary_is_not_guessed")
    _assert_anchor("test_stage12_690110_capture.py", "test_all_allies_targeting_remains_bounded")
    _assert_anchor("test_stage12_690110_capture.py", "test_unverified_equipment_categories_remain_bounded")

def test_official_40_state_runtime_coverage_is_complete() -> None:
    assert len(OFFICIAL_STATE_CATALOG) == 40
    assert len({entry.hint_id for entry in OFFICIAL_STATE_CATALOG}) == 40
    assert len({entry.state_id for entry in OFFICIAL_STATE_CATALOG}) == 40
    assert FINAL_AUTHORITY.is_file()
    rows = [line for line in _text(FINAL_AUTHORITY).splitlines() if re.match(r"^\|\s*690\d+\s*\|", line)]
    assert len(rows) == 40
    assert all("RUNTIME_FROZEN_TO_CONTRACT" in row for row in rows)

def test_690086_research_debt_is_not_laundered_into_complete() -> None:
    text = _text(FINAL_AUTHORITY)
    assert "690086" in text and "DSTS9-B02" in text and "OPEN / UNOBSERVED" in text
    assert "Research FROZEN = 39 / 40" in text
    assert "Strict Complete = 39 / 40" in text
    assert "Runtime FROZEN TO CONTRACT = 40 / 40" in text

def test_stage13_remains_inactive_before_final_gate() -> None:
    names = {path.name.lower() for path in CORE.glob("*.py")}
    assert not any("stage13" in name or "assault_runtime" in name for name in names)
    assert "Stage13 Active = NO" in _text(FINAL_AUTHORITY)

def test_stage12_cross_state_matrix_has_executable_anchors() -> None:
    anchors = {
        "INSIGHT×EXHAUSTION": ("test_stage12_690101_exhaustion.py", "test_resident_exhaustion_suppressed_by_insight_allows_active"),
        "INSIGHT×PROVOCATION": ("test_stage12_690108_provocation.py", "test_insight_rejects_incoming_provocation"),
        "INSIGHT×SABOTAGE": ("test_stage12_690109_sabotage.py", "test_later_insight_suppresses_resident_sabotage_then_same_instance_resumes"),
        "INSIGHT×CAPTURE": ("test_stage12_690110_capture.py", "test_insight_does_not_reject_capture"),
        "FALSE_REPORT×PROVOCATION": ("test_stage12_690108_provocation.py", "test_false_report_source_provider_dependency_suppresses_and_restores_provocation"),
        "FALSE_REPORT×INTIMIDATION": ("test_stage12_690222_intimidation.py", "test_false_report_and_intimidation_suppression_causes_compose"),
        "FALSE_REPORT×SABOTAGE": ("test_stage12_690109_sabotage.py", "test_false_report_and_sabotage_causes_compose_sabotage_removed_first"),
        "EXHAUSTION×PROVOCATION": ("test_stage12_shared_foundation_round3.py", "test_denied_skill_creates_no_target_operation"),
        "EXHAUSTION×INTIMIDATION": ("test_stage12_690222_intimidation.py", "test_exhaustion_ordering_is_provider_validity_before_skill_permission"),
        "PROVOCATION×INTIMIDATION": ("test_stage12_shared_foundation_round3.py", "test_target_operation_id_is_distinct_from_normal_attack_resolution_id"),
        "INTIMIDATION×CAPTURE": ("test_stage12_690110_capture_runtime_freeze_audit.py", "test_capture_intimidation_suppression_causes_compose"),
        "SABOTAGE×CAPTURE": ("test_stage12_690110_capture_runtime_freeze_audit.py", "test_capture_and_sabotage_equipment_scopes_remain_distinct"),
        "FALSE_REPORT×CAPTURE": ("test_stage12_690110_capture_runtime_freeze_audit.py", "test_capture_false_report_suppression_causes_compose"),
    }
    assert len(anchors) == 13
    for path, name in anchors.values():
        _assert_anchor(path, name)

def test_stage12_no_god_object_or_shadow_runtime() -> None:
    forbidden = {"Stage12Runtime", "Stage12Manager", "StateCompositeManager", "ControlRuntime"}
    found: set[str] = set()
    for path in CORE.glob("*.py"):
        tree = ast.parse(_text(path), filename=str(path))
        found.update(node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef) and node.name in forbidden)
    assert found == set()

def test_stage12_all_seven_use_one_composition_root() -> None:
    source = _text(CORE / "battle_systems.py")
    for state, (integration, _authority) in SEVEN.items():
        register = "register_" + integration.removesuffix("_integration.py") + "_integration"
        assert source.count(register + "(") == 1, state

def test_stage12_application_cycle_atomicity_anchor_exists() -> None:
    _assert_anchor("test_stage12_shared_foundation_round2.py", "test_cycle_validation_failure_commits_nothing")

def test_stage12_runtime_default_and_bounded_governance_authorities_exist() -> None:
    assert (STAGE12 / "STAGE12_RUNTIME_DEFAULT_LEDGER.md").is_file()
    assert (STAGE12 / "STAGE12_RNG_EVENT_DEFAULT_GOVERNANCE.md").is_file()
    assert (STAGE12 / "STAGE12_CONTRACT_RUNTIME_MAPPING.md").is_file()
