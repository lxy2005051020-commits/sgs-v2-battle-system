"""Integration regressions for composing both action-start formation adapters."""
from tests.test_stage14_san_shi_zhen import scene, install, tick
from sgs_v2.battle_core import create_wu_feng_zhen_runtime, SkillSlot
from sgs_v2.battle_core.damage_rate_modifier import DAMAGE_RATE_STATE_ID
from sgs_v2.battle_core.formation_admission import FORMATION_SKILL_REGISTRY


def dual_scene():
    ctx, systems, san = scene()
    for i, aptitude in enumerate(("S", "B", "A")):
        ctx.units[f"B{i}"].troop_aptitude = aptitude
    wu = create_wu_feng_zhen_runtime("B1", slot=SkillSlot.LEARNED_1)
    ctx.skill_runtimes.register(wu)
    install(ctx, systems, san)
    install(ctx, systems, wu)
    return ctx, systems, san, wu


def test_nine_canonical_definitions_and_two_opposing_action_drivers():
    assert set(FORMATION_SKILL_REGISTRY) == {"20066", "20025", "20178", "22012", "22031", "22039", "22040", "20836", "20862"}
    ctx, s, san, wu = dual_scene()
    tick(ctx, s, round_no=2, actor=san.owner_id)
    tick(ctx, s, round_no=2, actor=wu.owner_id)
    assert len(ctx.metadata["action_start_role_split_history"]) == 1
    assert len(ctx.metadata["periodic_team_support_history"]) == 1
    wu_states = ctx.states.find(state_id=DAMAGE_RATE_STATE_ID, source_id=wu.owner_id)
    assert len(wu_states) == 1 and wu_states[0].runtime_params.outgoing_rate == .15
    tick(ctx, s, round_no=4, actor=san.owner_id)
    assert len(ctx.states.find(state_id=DAMAGE_RATE_STATE_ID, source_id=wu.owner_id)) == 1


def test_defeated_provider_does_not_remove_other_formation_driver():
    ctx, s, san, wu = dual_scene()
    tick(ctx, s, round_no=2, actor=san.owner_id)
    tick(ctx, s, round_no=2, actor=wu.owner_id)
    ctx.units[san.owner_id].troops = 0
    s.defeat_cleanup_port.commit_defeat(ctx, san.owner_id)
    tick(ctx, s, round_no=4, actor=wu.owner_id)
    states = ctx.states.find(state_id=DAMAGE_RATE_STATE_ID, source_id=wu.owner_id)
    assert len(states) == 1 and states[0].runtime_params.outgoing_rate == .30
    assert not ctx.states.find(state_id=DAMAGE_RATE_STATE_ID, source_id=san.owner_id)
