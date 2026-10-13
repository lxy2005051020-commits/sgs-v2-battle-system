"""Adversarial integration checks for PR72; not empirical gameplay evidence."""
import pytest

from test_stage14_xing_yi_zhen import scene, install, modifiers
from sgs_v2.battle_core import (SkillSlot, DamageType, DamageRequest, DamageSourceType,
                               run_pre_battle_preparation_phases)
from sgs_v2.battle_core.xing_yi_zhen import create_xing_yi_zhen_runtime
from sgs_v2.battle_core.damage_rate_modifier import DAMAGE_RATE_STATE_ID, DamageRateParams
from sgs_v2.battle_core.effects import ApplyStateEffect, EffectSourceRef
from sgs_v2.battle_core.operation_identity import SourceType
from sgs_v2.battle_core.skill_runtime import SkillRuntime


@pytest.mark.parametrize("dtype", list(DamageType))
def test_opposing_formations_curve_and_defeat_are_isolated(dtype):
    ctx, s, rt = scene()
    for i in range(3):
        definition = ctx.skill_runtimes.get(f"A{i}", SkillSlot.INHERENT).definition
        ctx.skill_runtimes.register(SkillRuntime(definition, f"B{i}", SkillSlot.INHERENT))
    ctx.skill_runtimes.register(create_xing_yi_zhen_runtime("B1"))
    ctx.metadata["attacker_team_id"] = "A"
    run_pre_battle_preparation_phases(ctx, s)
    assert len(ctx.states.find()) == 6
    for round_no, expected in [(1, .7 * .7), (3, .9 * .9), (4, 1.16 * 1.01), (8, 1.8 * 1.05)]:
        ctx.current_round = round_no
        trace = s.damage_system.calculate(ctx,
            DamageRequest("A0", "B0", dtype, DamageSourceType.SKILL)).pipeline_trace.modifier_result
        assert trace.output_damage == pytest.approx(trace.input_damage * expected)
        assert {x.contribution.source.applied_by_unit_id for x in trace.applied_modifiers} == {"A1", "B1"}
    ctx.units["A1"].troops = 0
    s.defeat_cleanup_port.commit_defeat(ctx, "A1")
    remaining = ctx.states.find()
    assert len(remaining) == 3 and {x.source_id for x in remaining} == {"B1"}
    assert len(modifiers(ctx, s, "A0", "B0", dtype)) == 1


def test_provider_disabled_after_install_preserves_existing_resident_states():
    ctx, s, rt = scene()
    install(ctx, s, rt)
    before = {x.instance_id for x in ctx.states.find()}
    rt.enabled = False
    ctx.current_round = 5
    # Runtime.enabled gates installation, not retroactive removal of the
    # existing ALWAYS_ACTIVE modifier states. Keep the inherited owner contract.
    assert modifiers(ctx, s, "A0", "B0")[0].operand == pytest.approx(1.32)
    assert s.attribute_system.get_attack(ctx, ctx.units["A1"]) == 310
    rt.enabled = True
    assert modifiers(ctx, s, "A0", "B0")[0].operand == pytest.approx(1.32)
    assert s.attribute_system.get_attack(ctx, ctx.units["A1"]) == 310
    assert before == {x.instance_id for x in ctx.states.find()}


def test_other_source_static_modifier_keeps_canonical_aggregation_and_identity():
    ctx, s, rt = scene()
    install(ctx, s, rt)
    result = s.effect_executor.execute(ctx, ApplyStateEffect(DAMAGE_RATE_STATE_ID,
        "A0", "B1", "other_skill", runtime_params=DamageRateParams(outgoing_rate=.25),
        source_ref=EffectSourceRef(SourceType.ACTIVE_SKILL, "B1", "other_skill", SkillSlot.LEARNED_2)))
    ctx.current_round = 4
    trace = s.damage_system.calculate(ctx,
        DamageRequest("A0", "B0", DamageType.WEAPON, DamageSourceType.SKILL)).pipeline_trace.modifier_result
    # Canonical Stage13 same-side pooling adds percentage-point contributions.
    assert trace.output_damage == pytest.approx(trace.input_damage * 1.41)
    assert {x.contribution.source.source_skill_id for x in trace.applied_modifiers} == {"22039", "other_skill"}
    ctx.units["A1"].troops = 0
    s.defeat_cleanup_port.commit_defeat(ctx, "A1")
    assert ctx.states.has_instance(result.state_instance.instance_id)
    assert modifiers(ctx, s, "A0", "B0")[0].operand == 1.25


def test_round_queries_cannot_accumulate_states_or_consume_rng():
    ctx, s, rt = scene()
    install(ctx, s, rt)
    before = {x.instance_id for x in ctx.states.find()}
    rng = ctx.random._rng.getstate()
    for round_no in range(1, 21):
        ctx.current_round = round_no
        for _ in range(3):
            modifiers(ctx, s, "A0", "B0")
            modifiers(ctx, s, "B0", "A2")
    assert before == {x.instance_id for x in ctx.states.find()}
    assert ctx.random._rng.getstate() == rng
