from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass

import pytest

from sgs_v2.battle_core import (
    ApplyStateSkillEffectSpec,
    DamageSkillEffectSpec,
    DamageType,
    SkillDefinition,
    SkillTargetMode,
)


def make_definition(**overrides: object) -> SkillDefinition:
    values: dict[str, object] = {
        "skill_id": "synthetic.weapon_damage",
        "name": "Synthetic Weapon Damage",
        "activation_rate": 1.0,
        "target_mode": SkillTargetMode.SINGLE_RANDOM_ENEMY,
        "effect_specs": (
            DamageSkillEffectSpec(DamageType.WEAPON, coefficient=1.25),
        ),
    }
    values.update(overrides)
    return SkillDefinition(**values)  # type: ignore[arg-type]


def test_skill_definition_is_frozen_slotted_and_uses_tuple_specs() -> None:
    definition = make_definition(
        effect_specs=[DamageSkillEffectSpec(DamageType.WEAPON)]
    )

    assert is_dataclass(definition)
    assert not hasattr(definition, "__dict__")
    assert isinstance(definition.effect_specs, tuple)
    with pytest.raises(FrozenInstanceError):
        definition.name = "changed"  # type: ignore[misc]


def test_skill_definition_validates_required_fields_and_activation_rate() -> None:
    for field_name in ("skill_id", "name"):
        with pytest.raises(ValueError):
            make_definition(**{field_name: ""})

    for rate in (-0.01, 1.01):
        with pytest.raises(ValueError, match="activation_rate"):
            make_definition(activation_rate=rate)

    with pytest.raises(ValueError, match="effect_specs"):
        make_definition(effect_specs=())


def test_skill_effect_specs_are_typed_immutable_and_validated() -> None:
    damage = DamageSkillEffectSpec(DamageType.WEAPON, coefficient=0.5)
    state = ApplyStateSkillEffectSpec("690084")

    assert not hasattr(damage, "__dict__")
    assert not hasattr(state, "__dict__")
    with pytest.raises(FrozenInstanceError):
        damage.coefficient = 2.0  # type: ignore[misc]
    with pytest.raises(ValueError, match="coefficient"):
        DamageSkillEffectSpec(DamageType.WEAPON, coefficient=-0.1)
    with pytest.raises(ValueError, match="state_id"):
        ApplyStateSkillEffectSpec("")


def test_skill_definition_has_no_stage6_escape_hatch_fields() -> None:
    field_names = {item.name for item in fields(SkillDefinition)}
    assert field_names == {
        "skill_id",
        "name",
        "activation_rate",
        "target_mode",
        "effect_specs",
    }
    for forbidden in (
        "metadata",
        "params",
        "runtime_data",
        "handler",
        "custom_handler",
        "callable",
        "category",
        "skill_type",
        "timing",
        "trigger_type",
        "cooldown",
        "charges",
    ):
        assert forbidden not in field_names
