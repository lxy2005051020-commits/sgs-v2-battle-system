from __future__ import annotations

import ast
from pathlib import Path

from sgs_v2.battle_core import (
    BattleContext,
    BattleEngine,
    BattleSystems,
    EventBus,
    LineupPosition,
    RandomSystem,
    UnitRuntime,
)


CORE_DIR = Path(__file__).parents[1] / "sgs_v2" / "battle_core"
SKILL_FILES = (
    CORE_DIR / "skill_definition.py",
    CORE_DIR / "skill_runtime.py",
    CORE_DIR / "skill_resolver.py",
)


def parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def imported_modules(path: Path) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(parse(path)):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[-1] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split(".")[-1])
    return modules


def test_python_random_remains_isolated_to_random_system() -> None:
    for path in CORE_DIR.glob("*.py"):
        if path.name == "random_system.py":
            continue
        tree = parse(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(alias.name != "random" for alias in node.names)
            if isinstance(node, ast.ImportFrom):
                assert node.module != "random"


def test_skill_modules_do_not_import_bottom_execution_systems() -> None:
    forbidden = {
        "troop_system",
        "damage_system",
        "damage_resolution_system",
        "state_registry",
        "state_lifecycle_system",
        "effect_executor",
        "battle_systems",
        "random",
    }
    for path in SKILL_FILES:
        assert imported_modules(path).isdisjoint(forbidden)


def test_skill_modules_do_not_write_troops_or_state_registry() -> None:
    for path in SKILL_FILES:
        tree = parse(path)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets = []
                if isinstance(node, ast.Assign):
                    targets = node.targets
                else:
                    targets = [node.target]
                assert not any(
                    isinstance(target, ast.Attribute) and target.attr == "troops"
                    for target in targets
                )
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr not in {"add", "remove"}:
                    continue
                owner = node.func.value
                assert not (
                    isinstance(owner, ast.Attribute)
                    and owner.attr == "states"
                )


def test_skill_resolver_only_uses_chance_directly_from_context_random() -> None:
    resolver_tree = parse(CORE_DIR / "skill_resolver.py")
    forbidden_random_methods = {"random", "choice", "sample", "randint", "shuffle"}
    for node in ast.walk(resolver_tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in forbidden_random_methods


def test_production_skill_modules_do_not_know_synthetic_skill_ids() -> None:
    forbidden = {
        "synthetic.weapon_damage",
        "synthetic.disarm",
        "synthetic.damage_and_disarm",
        "synthetic.probabilistic_damage",
    }
    for path in SKILL_FILES:
        constants = {
            node.value
            for node in ast.walk(parse(path))
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        }
        assert constants.isdisjoint(forbidden)


def test_battle_engine_has_no_skill_import_or_skill_resolver_call() -> None:
    engine_path = CORE_DIR / "engine.py"
    assert all(not module.startswith("skill") for module in imported_modules(engine_path))

    for node in ast.walk(parse(engine_path)):
        if not isinstance(node, ast.Attribute):
            continue
        assert node.attr != "skill_resolver"


def test_battle_engine_run_does_not_auto_resolve_stage6_skills() -> None:
    context = BattleContext(
        battle_id="stage6-engine-generic",
        units={
            "a1": UnitRuntime(
                "a1", "A1", "A", 1000, 1000, 100, 100, 100,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "b1": UnitRuntime(
                "b1", "B1", "B", 1000, 1000, 100, 100, 90,
                lineup_position=LineupPosition.COMMANDER,
            ),
        },
        event_bus=EventBus(),
        random=RandomSystem(71),
        max_rounds=1,
    )
    systems = BattleSystems()

    def forbidden_resolve(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("BattleEngine must not auto-resolve skills in Stage 6")

    systems.skill_resolver.resolve = forbidden_resolve  # type: ignore[method-assign]
    BattleEngine(context, systems).run()
