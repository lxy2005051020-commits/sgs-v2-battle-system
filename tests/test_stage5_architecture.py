from __future__ import annotations

import inspect
from pathlib import Path

from sgs_v2.battle_core import (
    BattleEngine,
    DamageResolutionSystem,
    EffectExecutor,
    NormalAttackSystem,
    StateLifecycleSystem,
)


def test_normal_attack_no_longer_owns_damage_application_or_damage_result_events() -> None:
    source = inspect.getsource(NormalAttackSystem)
    assert "apply_damage" not in source
    assert "event_type=EventType.DAMAGE_DEALT" not in source
    assert "event_type=EventType.DAMAGE_PREVENTED" not in source
    assert "event_type=EventType.UNIT_DEFEATED" not in source


def test_damage_resolution_owns_damage_application_and_result_events() -> None:
    source = inspect.getsource(DamageResolutionSystem)
    assert "apply_damage" in source
    assert "EventType.DAMAGE_DEALT" in source
    assert "EventType.DAMAGE_PREVENTED" in source
    assert "EventType.UNIT_DEFEATED" in source


def test_effect_executor_does_not_bypass_state_lifecycle_or_troop_boundaries() -> None:
    source = inspect.getsource(EffectExecutor)
    assert ".states." not in source
    assert ".troops" not in source
    assert "apply_damage" not in source
    assert "restore(" not in source


def test_stage5_does_not_teach_battle_engine_about_effects() -> None:
    source = inspect.getsource(BattleEngine).lower()
    assert "effectexecutor" not in source
    for forbidden in (
        "damageeffect",
        "applystateeffect",
        "removestateeffect",
        "recovereffect",
    ):
        assert forbidden not in source


def test_state_lifecycle_still_does_not_execute_combat_rules() -> None:
    source = inspect.getsource(StateLifecycleSystem).lower()
    for forbidden in (
        "apply_damage",
        "restore(",
        "random_enemy",
        "damageeffect",
        "recovereffect",
    ):
        assert forbidden not in source


def test_python_random_is_still_isolated_to_random_system() -> None:
    core_dir = Path(__file__).parents[1] / "sgs_v2" / "battle_core"
    for path in core_dir.glob("*.py"):
        if path.name == "random_system.py":
            continue
        assert "import random" not in path.read_text(encoding="utf-8")
