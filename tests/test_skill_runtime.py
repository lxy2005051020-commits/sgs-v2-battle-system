from __future__ import annotations

from dataclasses import fields

import pytest

from sgs_v2.battle_core import (
    DamageSkillEffectSpec,
    DamageType,
    SkillDefinition,
    SkillRuntime,
    SkillTargetMode,
)


def make_definition() -> SkillDefinition:
    return SkillDefinition(
        skill_id="synthetic.weapon_damage",
        name="Synthetic Weapon Damage",
        activation_rate=1.0,
        target_mode=SkillTargetMode.SINGLE_RANDOM_ENEMY,
        effect_specs=(DamageSkillEffectSpec(DamageType.WEAPON),),
    )


def test_skill_runtime_binds_definition_owner_and_defaults_enabled() -> None:
    definition = make_definition()
    runtime = SkillRuntime(definition=definition, owner_id="a1")

    assert runtime.definition is definition
    assert runtime.owner_id == "a1"
    assert runtime.enabled is True
    assert not hasattr(runtime, "__dict__")


def test_skill_runtime_instances_share_definition_but_keep_independent_state() -> None:
    definition = make_definition()
    first = SkillRuntime(definition=definition, owner_id="a1")
    second = SkillRuntime(definition=definition, owner_id="a2")

    first.enabled = False

    assert first.definition is second.definition
    assert first.enabled is False
    assert second.enabled is True


def test_skill_runtime_has_only_minimal_stage6_fields() -> None:
    field_names = {item.name for item in fields(SkillRuntime)}
    assert field_names == {"definition", "owner_id", "enabled"}
    for forbidden in (
        "runtime_data",
        "metadata",
        "context",
        "battle_context",
        "battle_systems",
        "target_system",
        "effect_executor",
        "activation_count",
        "trigger_count",
        "cooldown",
        "charges",
    ):
        assert forbidden not in field_names


def test_skill_runtime_validates_owner_and_enabled_shape() -> None:
    definition = make_definition()
    with pytest.raises(ValueError, match="owner_id"):
        SkillRuntime(definition=definition, owner_id="")
    with pytest.raises(TypeError, match="enabled"):
        SkillRuntime(definition=definition, owner_id="a1", enabled=1)  # type: ignore[arg-type]
