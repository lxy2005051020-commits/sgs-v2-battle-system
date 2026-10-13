"""Reusable qualification contract verified through production entrypoints."""
from dataclasses import replace
import pytest
from tests.test_stage14_qian_long_zhen import scene, install
from sgs_v2.battle_core import SkillSlot, SkillRuntime, SkillType, SkillTargetMode
from sgs_v2.battle_core.skill_definition import (ApplyStateSkillEffectSpec,
    DamageSkillEffectSpec, RecoverySkillEffectSpec)
from sgs_v2.battle_core.enums import DamageType
from sgs_v2.battle_core.state_modifiers import (ATTRIBUTE_BONUS_STATE_ID,
    AttributeBonusParams, register_modifier_state_definitions)
from sgs_v2.battle_core.skill_resolver import SkillResolver
from sgs_v2.battle_core.effects import RemoveStateEffect
from sgs_v2.battle_core.commander_effect import COMMANDER_EFFECT_ROLE_STATE_ID


def test_resolver_uses_one_activation_roll_and_one_target_draw():
    ctx, s, rt = scene()
    install(ctx, s, rt)
    skill = ctx.skill_runtimes.get("A2", SkillSlot.INHERENT)
    skill.definition = replace(skill.definition, activation_rate=.9,
        target_mode=SkillTargetMode.SINGLE_RANDOM_ENEMY)
    control, _, _ = scene()
    assert control.random.chance(.9)
    # TargetSystem's single random selection uses the battle RNG's choice.
    from sgs_v2.battle_core.target_system import TargetSystem
    target = TargetSystem().random_enemy(control, control.units["A2"])
    result = s.skill_resolver.resolve(ctx, skill)
    assert len(result.effects) == 2
    assert {effect.target_id for effect in result.effects} == {target.unit_id}
    assert ctx.random._rng.getstate() == control.random._rng.getstate()


def test_real_persistent_attribute_effect_gates_by_source_not_recipient():
    ctx, s, rt = scene()
    register_modifier_state_definitions(ctx.states)
    skill = ctx.skill_runtimes.get("A2", SkillSlot.INHERENT)
    skill.definition = replace(skill.definition, target_mode=SkillTargetMode.FIXED_ALL_TEAM,
        commander_effect_specs=(ApplyStateSkillEffectSpec(ATTRIBUTE_BONUS_STATE_ID,
                                AttributeBonusParams("attack", 40)),))
    for effect in s.skill_resolver.resolve(ctx, skill).effects:
        # This test executes persistent effects only, without the ordinary hit.
        from sgs_v2.battle_core.effects import ApplyStateEffect
        if isinstance(effect, ApplyStateEffect): s.effect_executor.execute(ctx, effect)
    assert [s.attribute_system.get_attack(ctx, ctx.units[f"A{i}"]) for i in range(3)] == [200]*3
    install(ctx, s, rt)
    assert [s.attribute_system.get_attack(ctx, ctx.units[f"A{i}"]) for i in range(3)] == [270,240,240]
    role = ctx.states.find(owner_id="A2", state_id=COMMANDER_EFFECT_ROLE_STATE_ID)[0]
    s.effect_executor.execute(ctx, RemoveStateEffect(role.instance_id))
    assert [s.attribute_system.get_attack(ctx, ctx.units[f"A{i}"]) for i in range(3)] == [230,200,200]


def test_unregistered_runtime_and_missing_policy_fail_closed():
    ctx, s, rt = scene()
    skill = ctx.skill_runtimes.get("A2", SkillSlot.INHERENT)
    with pytest.raises(NotImplementedError): SkillResolver(s.target_system).resolve(ctx, skill)
    copied = SkillRuntime(skill.definition, skill.owner_id, skill.skill_slot)
    with pytest.raises(ValueError): s.skill_resolver.resolve(ctx, copied)
    skill.enabled = False
    assert not s.skill_resolver.resolve(ctx, skill).effects


@pytest.mark.parametrize("bad", [object(), "commander"])
def test_invalid_commander_spec_schema(bad):
    ctx, _, _ = scene()
    definition = ctx.skill_runtimes.get("A0", SkillSlot.INHERENT).definition
    with pytest.raises(TypeError): replace(definition, commander_effect_specs=(bad,))


def test_ambiguous_persistent_ids_and_immediate_opening_effects_rejected():
    ctx, _, _ = scene()
    definition = ctx.skill_runtimes.get("A0", SkillSlot.INHERENT).definition
    with pytest.raises(ValueError): replace(definition,
        effect_specs=(ApplyStateSkillEffectSpec("same"),),
        commander_effect_specs=(ApplyStateSkillEffectSpec("same"),))
    for kind in (SkillType.PASSIVE, SkillType.COMMAND):
        for spec in (DamageSkillEffectSpec(DamageType.WEAPON), RecoverySkillEffectSpec(10)):
            with pytest.raises(ValueError): replace(definition, skill_type=kind, commander_effect_specs=(spec,))


def test_two_opposing_formations_and_cleanup_are_isolated():
    ctx, s, rt = scene()
    from sgs_v2.battle_core import create_qian_long_zhen_runtime
    other = create_qian_long_zhen_runtime("B1")
    ctx.skill_runtimes.register(other)
    install(ctx, s, rt)
    install(ctx, s, other)
    ctx.units["A1"].troops = 0
    s.defeat_cleanup_port.commit_defeat(ctx, "A1")
    assert len(ctx.states.find()) == 10
    assert not s.commander_effect_policy.enabled(ctx, "B0")
    assert s.commander_effect_policy.enabled(ctx, "B2")
