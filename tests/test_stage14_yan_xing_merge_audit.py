"""Independent adversarial fixture for the bounded Yan Xing merge contract."""
import pytest
from sgs_v2.battle_core import (BattleContext, BattleSystems, BattlePhase, UnitRuntime,
    TroopType, LineupPosition, EventBus, RandomSystem, create_yan_xing_zhen_runtime,
    admit_and_install_formation_skill)
from sgs_v2.battle_core.damage_rate_modifier import DAMAGE_RATE_STATE_ID, DamageRateParams, RoundDamageRateParams
from sgs_v2.battle_core.effects import ApplyStateEffect
from sgs_v2.battle_core.state_transfer_support import (StateTransferSupport, is_incoming_reduction,
    is_negative_state)
from sgs_v2.battle_core.state_modifiers import INCOMING_DAMAGE_REDUCTION_STATE_ID, IncomingDamageReductionParams
from sgs_v2.battle_core.enums import DamageType
from sgs_v2.battle_core.dependency_evaluation import StateNode, ProviderNode
from sgs_v2.battle_core.provider_identity import SkillProviderRef
from sgs_v2.battle_core.rule_hooks import RoundStartHook
from sgs_v2.battle_core.state_removal import RemovalOperation


def fixture():
    units = {f"{team}{i}": UnitRuntime(f"{team}{i}", f"audit-{team}{i}", team,
        8000, 8000, 155, 150+i*20, 120-i, intelligence=200,
        troop_type=TroopType.CAVALRY, lineup_position=position)
        for team in ("red", "blue") for i, position in enumerate(LineupPosition)}
    context = BattleContext("yan-xing-merge-audit", units, EventBus(), RandomSystem(431))
    systems = BattleSystems()
    runtime = create_yan_xing_zhen_runtime("red1")
    context.skill_runtimes.register(runtime)
    context.current_phase = BattlePhase.PRE_BATTLE.value
    assert admit_and_install_formation_skill(context, systems, runtime).status.value == "SUCCESS"
    return context, systems, SkillProviderRef(runtime.owner_id, runtime.skill_slot, runtime.definition.skill_id)


def put(context, systems, owner, params, state_id=DAMAGE_RATE_STATE_ID, expiry=None):
    return systems.effect_executor.execute(context, ApplyStateEffect(state_id, owner,
        expires_round=expiry, expires_phase=BattlePhase.ROUND_END.value if expiry else None,
        runtime_params=params)).state_instance


@pytest.mark.parametrize("round_no,negative,reduction", [(1,True,True),(2,True,True),(3,False,False),(4,True,False)])
def test_round_curve_classification_reads_effective_round(round_no, negative, reduction):
    context, systems, _ = fixture()
    curve = put(context, systems, "blue0", RoundDamageRateParams(
        opening_rates=((-0.2,-0.1),(-0.1,-0.2),(0,0)), outgoing_step=.1, incoming_step=.1))
    assert is_incoming_reduction(curve, round_no) is reduction
    assert is_negative_state(curve, round_no) is negative


def test_inactive_curve_is_not_mistaken_for_transferable_reduction():
    context, systems, _ = fixture()
    put(context, systems, "blue0", RoundDamageRateParams(opening_rates=((0,0),), outgoing_step=.1))
    context.current_round = 3
    context.current_phase = BattlePhase.ROUND_START.value
    decisions = iter((True,False,False))
    context.random.chance = lambda probability: next(decisions)
    context.random.sample = lambda candidates, k: [next(u for u in candidates if u.unit_id in ("blue0", "red0"))]
    systems.rule_hook_system.process(context, RoundStartHook(3))
    assert context.metadata["round_team_transfer_history"][0]["transfers"] == []


def test_active_dynamic_curve_still_fails_closed_without_removal():
    context, systems, ref = fixture()
    curve = put(context, systems, "blue0", RoundDamageRateParams(opening_rates=((0,-.2),)))
    context.current_round = 1
    context.current_phase = BattlePhase.ROUND_START.value
    before = tuple(context.states.find())
    with pytest.raises(NotImplementedError, match="schema"):
        StateTransferSupport(systems).transfer(context, curve, "red2", ref, reduction=True)
    assert tuple(context.states.find()) == before


def test_source_with_dependents_fails_before_any_state_or_generation_mutation():
    context, systems, ref = fixture()
    source = put(context, systems, "blue0", DamageRateParams(.3,-.2))
    consumer = put(context, systems, "blue1", DamageRateParams(.1,0))
    systems.dependency_evaluation_support.add_dependency(StateNode(consumer.instance_id), StateNode(source.instance_id))
    context.current_round = 1
    context.current_phase = BattlePhase.ROUND_START.value
    before = tuple(context.states.find())
    with pytest.raises(NotImplementedError, match="dependent-state"):
        StateTransferSupport(systems).transfer(context, source, "red2", ref, reduction=True)
    assert tuple(context.states.find()) == before
    assert systems.dependency_evaluation_support.prerequisites(StateNode(consumer.instance_id)) == (StateNode(source.instance_id),)


def test_mixed_rate_remainder_preserves_lifetime_and_dependencies():
    context, systems, ref = fixture()
    source = put(context, systems, "blue0", DamageRateParams(.3,-.2), expiry=5)
    systems.dependency_evaluation_support.add_dependency(StateNode(source.instance_id), ProviderNode(ref))
    context.current_round = 1
    context.current_phase = BattlePhase.ROUND_START.value
    result = StateTransferSupport(systems).transfer(context, source, "red2", ref, reduction=True)
    assert result["status"] == "TRANSFERRED"
    remainder = context.states.find(owner_id="blue0",state_id=DAMAGE_RATE_STATE_ID)[0]
    assert remainder.runtime_params == DamageRateParams(.3,0)
    assert remainder.lifetime_spec.expires_round == 5
    assert ProviderNode(ref) in systems.dependency_evaluation_support.prerequisites(StateNode(remainder.instance_id))
    systems.state_lifecycle_system.expire_at(context, round_no=1, phase=BattlePhase.ROUND_END.value)
    assert context.states.has_instance(remainder.instance_id)
    systems.state_lifecycle_system.expire_at(context, round_no=5, phase=BattlePhase.ROUND_END.value)
    assert not context.states.has_instance(remainder.instance_id)


def test_transfer_removal_permission_is_not_available_to_other_callers():
    context, systems, ref = fixture()
    source = put(context, systems, "blue0", IncomingDamageReductionParams(DamageType.WEAPON,.2),
        state_id=INCOMING_DAMAGE_REDUCTION_STATE_ID)
    denied = systems.state_removal_coordinator.remove(context,
        operation=RemovalOperation.SCRIPTED_GAMEPLAY_REMOVE, instance_id=source.instance_id)
    assert denied.removed_instance is None
    context.current_round = 1
    context.current_phase = BattlePhase.ROUND_START.value
    assert StateTransferSupport(systems).transfer(context,source,"red2",ref,reduction=True)["status"] == "TRANSFERRED"
    assert not context.metadata["_state_transfer_removal_permits"]


def test_direct_transfer_cannot_remove_an_unrelated_positive_effect():
    context, systems, ref = fixture()
    source = put(context, systems, "blue0", DamageRateParams(.3,0))
    context.current_round = 1
    context.current_phase = BattlePhase.ROUND_START.value
    before = tuple(context.states.find())
    result = StateTransferSupport(systems).transfer(context,source,"red2",ref,reduction=True)
    assert result["status"] == "NO_ELIGIBLE_DIMENSION"
    assert tuple(context.states.find()) == before
