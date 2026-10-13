"""Separate adversarial harness for the Qian Long merge boundary."""
from dataclasses import replace
import pytest
from tests.test_stage14_qian_long_zhen import scene, install
from sgs_v2.battle_core import (SkillSlot, SkillType, SkillTargetMode, SkillRuntime,
    SkillDefinition, process_pre_battle_command_skills)
from sgs_v2.battle_core.skill_definition import ApplyStateSkillEffectSpec
from sgs_v2.battle_core.state_definition import StateDefinition
from sgs_v2.battle_core.effects import ApplyStateEffect
from sgs_v2.battle_core.state_modifiers import (ATTRIBUTE_BONUS_STATE_ID,
    AttributeBonusParams, register_modifier_state_definitions)


def test_inherited_assault_target_is_never_rerolled():
    ctx, s, rt = scene()
    install(ctx, s, rt)
    skill = ctx.skill_runtimes.get("A2", SkillSlot.INHERENT)
    skill.definition = replace(skill.definition, skill_type=SkillType.ASSAULT,
        target_mode=SkillTargetMode.SINGLE_RANDOM_ENEMY)
    rng = ctx.random._rng.getstate()
    result = s.skill_resolver.resolve(ctx, skill, inherited_target_ids=("A0",))
    assert len(result.effects) == 2 and all(effect.target_id == "A0" for effect in result.effects)
    assert ctx.random._rng.getstate() == rng


def test_command_opening_branch_uses_deputy_qualification():
    ctx, s, rt = scene()
    install(ctx, s, rt)
    for i in (0, 2):
        for key in (f"command_plain_{i}", f"command_branch_{i}"):
            ctx.states.register_definition(StateDefinition(key, key))
        skill = ctx.skill_runtimes.get(f"A{i}", SkillSlot.INHERENT)
        skill.definition = SkillDefinition(f"command_{i}", "audit", 1,
            SkillTargetMode.SELF, (ApplyStateSkillEffectSpec(f"command_plain_{i}"),),
            skill_type=SkillType.COMMAND,
            commander_effect_specs=(ApplyStateSkillEffectSpec(f"command_branch_{i}"),))
    process_pre_battle_command_skills(ctx, s)
    for i in (0, 2):
        assert s.state_effectiveness_policy.evaluate_state(ctx, ctx.states.find(state_id=f"command_plain_{i}")[0]).effective
        assert s.state_effectiveness_policy.evaluate_state(ctx, ctx.states.find(state_id=f"command_branch_{i}")[0]).effective is (i == 2)


def test_same_state_in_other_slot_stays_ordinary():
    ctx, s, rt = scene(commander_branch=True)
    register_modifier_state_definitions(ctx.states)
    inherent = ctx.skill_runtimes.get("A0", SkillSlot.INHERENT)
    inherent.definition = replace(inherent.definition,
        target_mode=SkillTargetMode.SELF,
        commander_effect_specs=(ApplyStateSkillEffectSpec(ATTRIBUTE_BONUS_STATE_ID,
            AttributeBonusParams("attack", 40)),))
    ordinary = SkillRuntime(SkillDefinition("ordinary_learned", "ordinary", 1,
        SkillTargetMode.SELF, (ApplyStateSkillEffectSpec(ATTRIBUTE_BONUS_STATE_ID,
            AttributeBonusParams("attack", 40)),)), "A0", SkillSlot.LEARNED_2)
    ctx.skill_runtimes.register(ordinary)
    for skill in (inherent, ordinary):
        for effect in s.skill_resolver.resolve(ctx, skill).effects:
            if isinstance(effect, ApplyStateEffect): s.effect_executor.execute(ctx, effect)
    assert s.attribute_system.get_attack(ctx, ctx.units["A0"]) == 280
    install(ctx, s, rt)
    # Installation snapshot sees 280; commander branch stops, ordinary +40 persists.
    assert s.attribute_system.get_attack(ctx, ctx.units["A0"]) == 254
    states = ctx.states.find(owner_id="A0", state_id=ATTRIBUTE_BONUS_STATE_ID)
    enabled = {state.source_skill_slot: s.state_effectiveness_policy.evaluate_state(ctx, state).effective
               for state in states if state.source_skill_id != "22040"}
    assert enabled == {SkillSlot.INHERENT: False, SkillSlot.LEARNED_2: True}


@pytest.mark.parametrize("slot", list(SkillSlot))
def test_arbitrary_slot_commander_presence_selects_reduced_rate(slot):
    ctx, s, rt = scene()
    if slot is SkillSlot.INHERENT:
        skill = ctx.skill_runtimes.get("A0", slot)
        skill.definition = ctx.skill_runtimes.get("A2", SkillSlot.INHERENT).definition
    else:
        ctx.skill_runtimes.register(SkillRuntime(
            ctx.skill_runtimes.get("A2", SkillSlot.INHERENT).definition, "A0", slot))
    install(ctx, s, rt)
    assert s.attribute_system.get_attack(ctx, ctx.units["A0"]) == 210


def test_generic_qualification_does_not_change_real_team_commander():
    ctx, s, rt = scene()
    install(ctx, s, rt)
    assert ctx.commander_of("A").unit_id == "A0"
    ctx.units["A1"].troops = 0
    s.defeat_cleanup_port.commit_defeat(ctx, "A1")
    assert ctx.commander_of("A").unit_id == "A0"
    assert s.commander_effect_policy.enabled(ctx, "A0")
    assert not s.commander_effect_policy.enabled(ctx, "A2")
