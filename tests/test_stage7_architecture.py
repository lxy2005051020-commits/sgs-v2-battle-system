from __future__ import annotations

import ast
import inspect
from pathlib import Path

from sgs_v2.battle_core import BattleEngine, RecoverySystem, RuleHookSystem, TriggerSystem


CORE_DIR = Path(__file__).parents[1] / "sgs_v2" / "battle_core"
ROOT_DIR = Path(__file__).parents[1]


def module_ast(name: str) -> ast.Module:
    return ast.parse((CORE_DIR / name).read_text(encoding="utf-8"))


def imported_modules(tree: ast.Module) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.add(node.module)
    return modules


def assigned_attribute_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = []
            if isinstance(node, ast.Assign):
                targets = node.targets
            else:
                targets = [node.target]
            for target in targets:
                for child in ast.walk(target):
                    if isinstance(child, ast.Attribute):
                        names.add(child.attr)
    return names


def called_attributes(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            names.add(node.func.attr)
    return names


def test_trigger_system_has_no_forbidden_execution_dependencies_or_mutations() -> None:
    tree = module_ast("trigger_system.py")
    imports = imported_modules(tree)
    forbidden_import_fragments = {
        "random",
        "troop_system",
        "damage_system",
        "damage_resolution_system",
        "state_lifecycle_system",
        "effect_executor",
    }
    assert not any(
        any(fragment in module for fragment in forbidden_import_fragments)
        for module in imports
    )
    assert "troops" not in assigned_attribute_names(tree)
    calls = called_attributes(tree)
    assert "add" not in calls
    assert "remove" not in calls
    assert "apply_damage" not in calls
    assert "restore" not in calls
    assert "execute" not in calls


def test_recovery_system_has_only_troop_system_as_troop_mutation_boundary() -> None:
    tree = module_ast("recovery_system.py")
    imports = imported_modules(tree)
    for forbidden in ("trigger_system", "effect_executor", "victory_system"):
        assert not any(forbidden in module for module in imports)
    assert "troops" not in assigned_attribute_names(tree)
    calls = called_attributes(tree)
    assert "apply_damage" not in calls
    assert "execute" not in calls
    assert "check" not in calls
    assert "restore" in calls


def test_rule_hook_system_has_only_trigger_and_executor_coordination_dependencies() -> None:
    tree = module_ast("rule_hook_system.py")
    imports = imported_modules(tree)
    assert not any("victory_system" in module for module in imports)
    assert not any("official_state_catalog" in module for module in imports)
    source = inspect.getsource(RuleHookSystem)
    for concrete in (
        "burn",
        "poison",
        "flood",
        "rout",
        "sandstorm",
        "recuperation",
        "healing_ban",
    ):
        assert concrete not in source


def test_battle_engine_has_no_concrete_state_or_effect_branches() -> None:
    source = inspect.getsource(BattleEngine)
    for forbidden in (
        "OfficialStateId",
        "DamageEffect",
        "RecoverEffect",
        "burn",
        "poison",
        "flood",
        "rout",
        "sandstorm",
        "recuperation",
        "healing_ban",
    ):
        assert forbidden not in source


def test_event_bus_does_not_import_stage7_rule_execution_modules() -> None:
    imports = imported_modules(module_ast("events.py"))
    for forbidden in ("trigger_system", "rule_hook_system", "recovery_system"):
        assert not any(forbidden in module for module in imports)


def test_damage_system_stage7_boundary_does_not_gain_recovery_or_trigger_execution() -> None:
    tree = module_ast("damage_system.py")
    imports = imported_modules(tree)
    for forbidden in (
        "recovery_system",
        "trigger_system",
        "rule_hook_system",
        "effect_executor",
        "troop_system",
    ):
        assert not any(forbidden in module for module in imports)
    calls = called_attributes(tree)
    assert "restore" not in calls
    assert "apply_damage" not in calls


def test_evidence_matrix_gate_keeps_official_periodic_states_deferred() -> None:
    matrix = (
        ROOT_DIR
        / "research"
        / "stage7_evidence_matrix"
        / "STAGE7_EVIDENCE_MATRIX.md"
    ).read_text(encoding="utf-8")
    deferred = (
        "burn",
        "flood",
        "poison",
        "rout",
        "sandstorm",
        "recuperation",
        "rebellion",
        "first_aid",
        "weapon_lifesteal",
        "strategy_lifesteal",
    )
    for state_id in deferred:
        row = next(line for line in matrix.splitlines() if line.startswith(f"| `{state_id}` |"))
        assert "`DEFER`" in row
    healing_row = next(
        line for line in matrix.splitlines()
        if line.startswith("| `healing_ban` |")
    )
    assert "`PASS_STAGE7`" in healing_row


def test_official_catalog_does_not_sneak_in_periodic_trigger_runtime_mapping() -> None:
    source = (CORE_DIR / "official_state_catalog.py").read_text(encoding="utf-8")
    assert "ROUND_START_TRIGGER_TAG" not in source
    assert "UNIT_ACTION_START_TRIGGER_TAG" not in source
    assert "PeriodicDamageStateParams" not in source
    assert "PeriodicRecoveryStateParams" not in source


def test_stage7_public_systems_are_real_types_for_ast_audit_imports() -> None:
    assert TriggerSystem.__name__ == "TriggerSystem"
    assert RecoverySystem.__name__ == "RecoverySystem"
    assert RuleHookSystem.__name__ == "RuleHookSystem"
