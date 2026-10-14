"""Adversarial fixtures for the authorized partial Yu Lin merge scope."""
import pytest
from sgs_v2.battle_core import (BattleContext, BattleSystems, BattlePhase, EventBus,
    RandomSystem, UnitRuntime, TroopType, LineupPosition, SkillSlot,
    create_yu_lin_zhen_runtime, create_yan_xing_zhen_runtime,
    run_pre_battle_preparation_phases, admit_and_install_formation_skill)
from sgs_v2.battle_core.official_state_catalog import OfficialStateId
from sgs_v2.battle_core.state_modifiers import ATTRIBUTE_BONUS_STATE_ID


def fixture(*, full=False, slot=SkillSlot.LEARNED_2):
    units = {f"{team}{i}": UnitRuntime(f"{team}{i}", f"audit-{team}{i}", team,
        8000, 8000, 155, 150+i*20, 120-i, intelligence=200,
        troop_type=TroopType.SHIELD, lineup_position=position)
        for team in ("red", "blue") for i, position in enumerate(LineupPosition)}
    ctx = BattleContext("yu-lin-merge-audit", units, EventBus(), RandomSystem(431))
    s = BattleSystems()
    rt = create_yu_lin_zhen_runtime("red2", slot=slot, command_only=not full)
    ctx.skill_runtimes.register(rt)
    ctx.current_phase = BattlePhase.PRE_BATTLE.value
    return ctx, s, rt


@pytest.mark.parametrize("slot", list(SkillSlot))
def test_provider_slot_and_fixed_bonus_survive_rounds_without_reaction_states(slot):
    ctx, s, rt = fixture(slot=slot)
    run_pre_battle_preparation_phases(ctx, s)
    for round_no in (1, 3, 4, 5, 8):
        ctx.current_round = round_no
        for owner, expected in (("red0",150),("red1",225),("red2",245),("blue1",170)):
            assert s.attribute_system.get_defense(ctx, ctx.units[owner]) == expected
        assert len(ctx.states.find()) == 2
        assert not ctx.states.find(state_id=OfficialStateId.BARRIER.value)
        assert not ctx.states.find(state_id=OfficialStateId.FIRST_AID.value)
    assert all(state.source_skill_slot is slot for state in ctx.states.find())


def test_opposing_valid_formation_does_not_install_before_invalid_definition_rejection():
    from dataclasses import replace
    ctx, s, rt = fixture(full=True)
    rt.definition = replace(rt.definition, activation_rate=.5)
    ctx.skill_runtimes.register(create_yan_xing_zhen_runtime("blue0"))
    before = ctx.random._rng.getstate()
    with pytest.raises(ValueError, match="canonical definition"):
        run_pre_battle_preparation_phases(ctx, s)
    assert not ctx.states.find() and not ctx.metadata.get("yan_xing_admissions")
    assert ctx.random._rng.getstate() == before


def test_yu_lin_and_yan_xing_install_and_cleanup_are_isolated():
    ctx, s, rt = fixture()
    ctx.skill_runtimes.register(create_yan_xing_zhen_runtime("blue0"))
    run_pre_battle_preparation_phases(ctx, s)
    assert len(ctx.states.find(state_id=ATTRIBUTE_BONUS_STATE_ID)) == 2
    assert ctx.metadata["yan_xing_admissions"]
    ctx.units["blue0"].troops = 0
    s.defeat_cleanup_port.commit_defeat(ctx, "blue0")
    assert len(ctx.states.find()) == 2
    assert s.attribute_system.get_defense(ctx, ctx.units["red1"]) == 225
    ctx.units[rt.owner_id].troops = 0
    s.defeat_cleanup_port.commit_defeat(ctx, rt.owner_id)
    assert not ctx.states.find()


def test_wrong_phase_rejects_without_installation_or_rng():
    ctx, s, rt = fixture()
    ctx.current_phase = BattlePhase.ROUND_START.value
    before = ctx.random._rng.getstate()
    assert admit_and_install_formation_skill(ctx,s,rt).status.value == "REJECTED_PHASE_ILLEGAL"
    assert not ctx.states.find() and ctx.random._rng.getstate() == before
