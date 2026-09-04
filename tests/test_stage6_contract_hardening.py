from __future__ import annotations

import ast
from pathlib import Path

import pytest

from sgs_v2.battle_core import (
    DamageEffect,
    DamageSkillEffectSpec,
    DamageSourceType,
    DamageType,
    SkillDefinition,
    SkillResolutionResult,
    SkillResolutionStatus,
    SkillTargetMode,
)


CORE_DIR = Path(__file__).parents[1] / "sgs_v2" / "battle_core"


def make_definition(**overrides: object) -> SkillDefinition:
    values: dict[str, object] = {
        "skill_id": "synthetic.audit",
        "name": "Synthetic Audit",
        "activation_rate": 0.5,
        "target_mode": SkillTargetMode.SINGLE_RANDOM_ENEMY,
        "effect_specs": (DamageSkillEffectSpec(DamageType.WEAPON),),
    }
    values.update(overrides)
    return SkillDefinition(**values)  # type: ignore[arg-type]


def make_damage_effect() -> DamageEffect:
    return DamageEffect(
        source_id="a1",
        target_id="b1",
        damage_type=DamageType.WEAPON,
        source_type=DamageSourceType.SKILL,
        source_skill_id="synthetic.audit",
    )


def test_skill_definition_rejects_non_finite_and_bool_activation_rates() -> None:
    for rate in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(ValueError, match="activation_rate"):
            make_definition(activation_rate=rate)

    for rate in (True, False, "0.5", None):
        with pytest.raises(TypeError, match="activation_rate"):
            make_definition(activation_rate=rate)


def test_skill_definition_canonicalizes_integer_activation_rate_to_float() -> None:
    definition = make_definition(activation_rate=1)

    assert definition.activation_rate == 1.0
    assert isinstance(definition.activation_rate, float)


def test_damage_skill_effect_spec_rejects_non_finite_bool_and_invalid_types() -> None:
    for coefficient in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(ValueError, match="coefficient"):
            DamageSkillEffectSpec(DamageType.WEAPON, coefficient=coefficient)

    for coefficient in (True, False, "1.0", None):
        with pytest.raises(TypeError, match="coefficient"):
            DamageSkillEffectSpec(  # type: ignore[arg-type]
                DamageType.WEAPON,
                coefficient=coefficient,
            )


def test_damage_skill_effect_spec_canonicalizes_integer_coefficient_to_float() -> None:
    spec = DamageSkillEffectSpec(DamageType.WEAPON, coefficient=2)

    assert spec.coefficient == 2.0
    assert isinstance(spec.coefficient, float)


@pytest.mark.parametrize("status", ["garbage", "DISABLED", 1, None])
def test_skill_resolution_result_rejects_non_enum_status(status: object) -> None:
    with pytest.raises(TypeError, match="SkillResolutionStatus"):
        SkillResolutionResult(
            skill_id="synthetic.audit",
            owner_id="a1",
            status=status,  # type: ignore[arg-type]
            target_ids=(),
            effects=(),
        )


@pytest.mark.parametrize(
    ("skill_id", "owner_id"),
    [
        ("", "a1"),
        ("   ", "a1"),
        ("synthetic.audit", ""),
        ("synthetic.audit", "   "),
    ],
)
def test_skill_resolution_result_rejects_empty_or_blank_identity(
    skill_id: str,
    owner_id: str,
) -> None:
    with pytest.raises(ValueError):
        SkillResolutionResult(
            skill_id=skill_id,
            owner_id=owner_id,
            status=SkillResolutionStatus.DISABLED,
            target_ids=(),
            effects=(),
        )


def test_skill_resolution_result_rejects_resolved_without_effects() -> None:
    with pytest.raises(ValueError, match="effects"):
        SkillResolutionResult(
            skill_id="synthetic.audit",
            owner_id="a1",
            status=SkillResolutionStatus.RESOLVED,
            target_ids=("b1",),
            effects=(),
        )


def test_skill_resolution_result_rejects_failed_payloads_independently() -> None:
    effect = make_damage_effect()

    with pytest.raises(ValueError, match="must not contain"):
        SkillResolutionResult(
            skill_id="synthetic.audit",
            owner_id="a1",
            status=SkillResolutionStatus.ACTIVATION_FAILED,
            target_ids=("b1",),
            effects=(),
        )

    with pytest.raises(ValueError, match="must not contain"):
        SkillResolutionResult(
            skill_id="synthetic.audit",
            owner_id="a1",
            status=SkillResolutionStatus.ACTIVATION_FAILED,
            target_ids=(),
            effects=(effect,),
        )


def test_skill_resolver_does_not_branch_on_skill_identity() -> None:
    path = CORE_DIR / "skill_resolver.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    for node in ast.walk(tree):
        expression: ast.AST | None = None
        if isinstance(node, ast.If):
            expression = node.test
        elif isinstance(node, ast.Match):
            expression = node.subject
        if expression is None:
            continue

        identity_attributes = {
            child.attr
            for child in ast.walk(expression)
            if isinstance(child, ast.Attribute)
            and child.attr in {"skill_id", "name"}
        }
        assert not identity_attributes


def test_skill_resolver_chance_calls_only_context_random() -> None:
    path = CORE_DIR / "skill_resolver.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    chance_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "chance"
    ]

    assert chance_calls
    for call in chance_calls:
        receiver = call.func.value
        assert isinstance(receiver, ast.Attribute)
        assert receiver.attr == "random"
        assert isinstance(receiver.value, ast.Name)
        assert receiver.value.id == "context"
