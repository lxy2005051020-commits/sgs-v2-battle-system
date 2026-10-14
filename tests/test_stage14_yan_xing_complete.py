"""Non-scaling transfer model: real snapshots, bindings and lifecycle behavior."""
from dataclasses import replace
import pytest
from tests.test_stage14_yan_xing_zhen import scene,install,apply,attr,tick
from sgs_v2.battle_core import (BattlePhase,SkillSlot,SkillDefinition,SkillRuntime,SkillType,SkillTargetMode,
    DamageType,DamageRequest,DamageSourceType)
from sgs_v2.battle_core.official_state_catalog import register_official_state_definitions
from sgs_v2.battle_core.skill_definition import ApplyStateSkillEffectSpec
from sgs_v2.battle_core.state_definition import StateDefinition
from sgs_v2.battle_core.state_modifiers import ATTRIBUTE_BONUS_STATE_ID,AttributeBonusParams,BoundedAttributeBonusParams
from sgs_v2.battle_core.damage_rate_modifier import DAMAGE_RATE_STATE_ID,DamageRateParams,RoundDamageRateParams
from sgs_v2.battle_core.probabilistic_target_priority import (TARGET_PRIORITY_STATE_ID,TargetPriorityParams,
    register_target_priority_state)
from sgs_v2.battle_core.state_transfer_support import StateTransferSupport
from sgs_v2.battle_core.provider_identity import SkillProviderRef
from sgs_v2.battle_core.stage10_state_params import ContinuousDamageStateParams
from sgs_v2.battle_core.stage9_state_params import ChainStateParams
from sgs_v2.battle_core.stage9_integerization import ExactRatio
from sgs_v2.battle_core.dependency_evaluation import StateNode
from sgs_v2.battle_core.rule_hooks import UnitActionStartHook
from sgs_v2.battle_core.state_removal import RemovalOperation
from sgs_v2.battle_core.state_application import StateCandidate
from sgs_v2.battle_core.state_runtime_params import EmptyStateRuntimeParams


def ready():
    ctx,s,rt=scene()
    ctx.metadata['attacker_team_id']='A'
    register_official_state_definitions(ctx.states)
    install(ctx,s,rt)
    return ctx,s,rt,SkillProviderRef(rt.owner_id,rt.skill_slot,'20862')


def transfer(ctx,s,ref,state,target='B1',reduction=False):
    ctx.current_round=1
    ctx.current_phase=BattlePhase.ROUND_START.value
    result=StateTransferSupport(s).transfer(ctx,state,target,ref,reduction=reduction)
    assert result['status']=='TRANSFERRED',result
    return ctx.states.get(result['new_instance_id']),result


@pytest.mark.parametrize('sid',('burn','flood','poison','rout','sandstorm','rebellion'))
def test_each_continuous_state_keeps_potency_and_rebinds_tick_provenance(sid):
    ctx,s,rt,ref=ready()
    original=s.state_lifecycle_system.apply(ctx,state_id=sid,owner_id='A2',source_id='B2',
        source_skill_id='original-dot',runtime_params=ContinuousDamageStateParams(),duration_rounds=2)
    old=original.runtime_params.frozen_damage_basis
    # Transfer must not recapture the changed original source or transfer provider.
    ctx.units['B2'].intelligence=900
    ctx.units[rt.owner_id].intelligence=999
    new,_=transfer(ctx,s,ref,original)
    basis=new.runtime_params.frozen_damage_basis
    assert basis.source_formula_facts==old.source_formula_facts
    assert basis.locked_modifier_plan==old.locked_modifier_plan
    assert basis.coefficient==old.coefficient
    assert basis.source_unit_id==ref.owner_id and basis.source_skill_id=='20862'
    assert basis.application_generation_id==new.current_generation_id
    assert basis.physical_state_instance_id==new.instance_id
    assert basis.historical_source.application_generation_id==new.current_generation_id
    assert basis.historical_source.physical_state_instance_id==new.instance_id
    assert not ctx.states.has_instance(original.instance_id)
    ctx.current_phase=BattlePhase.UNIT_ACTION_START.value
    ctx.action_progress.set_current_acting_unit('B1')
    ctx.action_progress.mark_action_start('B1',1)
    intents=s.trigger_system.collect(ctx,UnitActionStartHook(1,'B1'))
    assert len(intents)==1
    effect=intents[0]
    assert effect.source_id==ref.owner_id and effect.target_id=='B1'
    before=ctx.units['B1'].troops
    s.effect_executor.execute(ctx,effect)
    assert ctx.units['B1'].troops<before
    s.state_lifecycle_system.expire_at(ctx,round_no=1,phase=BattlePhase.ROUND_END.value)
    assert not ctx.states.has_instance(new.instance_id)


@pytest.mark.parametrize('sid',('silence','disarm','confusion','weakness','healing_ban','taunt','false_report','provoke','equipment_disable','capture','stun','ambush','chain_link'))
def test_all_non_dot_negative_kinds_transfer_and_expire(sid):
    ctx,s,rt,ref=ready()
    params=ChainStateParams(ExactRatio(1,5)) if sid=='chain_link' else None
    original=s.state_lifecycle_system.apply(ctx,state_id=sid,owner_id='A2',source_id='B2',runtime_params=params)
    new,_=transfer(ctx,s,ref,original)
    assert new.owner_id=='B1' and new.source_id==ref.owner_id
    assert not ctx.states.has_instance(original.instance_id)
    if sid=='taunt':
        assert new.runtime_params.taunt_target_id==ref.owner_id
    s.state_lifecycle_system.expire_at(ctx,round_no=1,phase=BattlePhase.ROUND_END.value)
    assert not ctx.states.has_instance(new.instance_id)


def put_active(ctx,owner,slot=SkillSlot.INHERENT):
    ctx.states.register_definition(StateDefinition('fixture-passive-'+owner,'fixture'))
    runtime=SkillRuntime(SkillDefinition('active-'+owner,'active',1.,SkillTargetMode.SELF,
        (ApplyStateSkillEffectSpec('fixture-passive-'+owner),),skill_type=SkillType.ACTIVE),owner,slot)
    ctx.skill_runtimes.register(runtime)
    return runtime


def test_intimidation_rebinds_legal_target_skill_and_releases_original_holder():
    ctx,s,rt,ref=ready()
    old_rt=put_active(ctx,'A2')
    new_rt=put_active(ctx,'B1',SkillSlot.LEARNED_2)
    original=s.state_application_coordinator.apply_candidate(ctx,StateCandidate(
            'intimidation','A2',EmptyStateRuntimeParams(),source_id='B2')).instance
    assert original.bound_provider_ref.owner_id=='A2'
    new,_=transfer(ctx,s,ref,original)
    assert new.bound_provider_ref.owner_id=='B1' and new.bound_provider_ref.skill_slot==SkillSlot.LEARNED_2
    assert s.provider_validity_policy.evaluate_provider(ctx,SkillProviderRef('A2',old_rt.skill_slot,old_rt.definition.skill_id)).valid
    assert not s.provider_validity_policy.evaluate_provider(ctx,new.bound_provider_ref).valid


def test_live_reduction_moves_snapshot_keeps_priority_and_other_dimensions():
    ctx,s,rt,ref=ready()
    register_target_priority_state(ctx.states)
    source=s.state_lifecycle_system.apply(ctx,state_id=TARGET_PRIORITY_STATE_ID,owner_id='B2',
        source_id='B2',runtime_params=TargetPriorityParams(.8,.3,.001,100),expires_round=6,expires_phase='ROUND_START')
    new,_=transfer(ctx,s,ref,source,target='A1',reduction=True)
    assert new.state_id==DAMAGE_RATE_STATE_ID
    assert new.runtime_params.incoming_rate==pytest.approx(-.38)
    remaining=ctx.states.get(source.instance_id)
    assert remaining.runtime_params.probability==.8
    assert remaining.runtime_params.reduction_base==remaining.runtime_params.reduction_slope==0
    ctx.units['B2'].defense=600
    assert new.runtime_params.incoming_rate==pytest.approx(-.38)


def test_curve_snapshots_reduction_and_preserves_future_positive_lane():
    ctx,s,rt,ref=ready()
    source=apply(ctx,s,DAMAGE_RATE_STATE_ID,'B2',RoundDamageRateParams(opening_rates=((.1,-.2),),outgoing_step=.1,incoming_step=.1))
    new,_=transfer(ctx,s,ref,source,target='A1',reduction=True)
    assert type(new.runtime_params) is DamageRateParams and new.runtime_params.incoming_rate==-.2
    remaining=ctx.states.get(source.instance_id).runtime_params
    assert remaining.rates_at(1)==(.1,0) and remaining.rates_at(2)==(.1,.1)


def test_associated_attribute_child_moves_and_rebinds_parent():
    ctx,s,rt,ref=ready()
    source=s.state_lifecycle_system.apply(ctx,state_id='silence',owner_id='A2',source_id='B2')
    child=apply(ctx,s,DAMAGE_RATE_STATE_ID,'A2',DamageRateParams(incoming_rate=.3,prerequisite_state_id=source.instance_id))
    s.dependency_evaluation_support.add_dependency(StateNode(child.instance_id),StateNode(source.instance_id))
    new,row=transfer(ctx,s,ref,source)
    new_child=ctx.states.get(row['identity_rebindings'][child.instance_id])
    assert new_child.owner_id=='B1'
    assert new_child.runtime_params.prerequisite_state_id==new.instance_id
    assert StateNode(new.instance_id) in s.dependency_evaluation_support.prerequisites(StateNode(new_child.instance_id))
    assert not ctx.states.has_instance(child.instance_id)


def test_same_kind_overwrites_and_keeps_other_attributes_and_positive_effects():
    ctx,s,rt,ref=ready()
    source=apply(ctx,s,ATTRIBUTE_BONUS_STATE_ID,'A2',BoundedAttributeBonusParams('defense',-50,'layer1','fixture',3))
    old=apply(ctx,s,ATTRIBUTE_BONUS_STATE_ID,'B1',AttributeBonusParams('defense',-20))
    apply(ctx,s,ATTRIBUTE_BONUS_STATE_ID,'B1',AttributeBonusParams('speed',-10))
    s.state_lifecycle_system.apply(ctx,state_id=ATTRIBUTE_BONUS_STATE_ID,owner_id='B1',source_id='A2',source_skill_id='other',runtime_params=AttributeBonusParams('defense',30))
    new,_=transfer(ctx,s,ref,source)
    assert new.runtime_params.amount==-50 and type(new.runtime_params) is AttributeBonusParams
    assert not ctx.states.has_instance(old.instance_id)
    assert attr(ctx,s,'B1')==160
    assert s.attribute_system.get_speed(ctx,ctx.units['B1'])==89


def test_preflight_immunity_rejects_whole_associated_bundle_without_loss():
    ctx,s,rt,ref=ready()
    source=s.state_lifecycle_system.apply(ctx,state_id='silence',owner_id='A2')
    child=apply(ctx,s,ATTRIBUTE_BONUS_STATE_ID,'A2',AttributeBonusParams('defense',-20))
    s.dependency_evaluation_support.add_dependency(StateNode(child.instance_id),StateNode(source.instance_id))
    s.state_lifecycle_system.apply(ctx,state_id='insight',owner_id='B1')
    before=tuple(ctx.states.find())
    ctx.current_round=1
    ctx.current_phase='ROUND_START'
    result=StateTransferSupport(s).transfer(ctx,source,'B1',ref)
    assert result['status']=='REJECTED_ADMISSION'
    assert tuple(ctx.states.find())==before


def test_ordinary_control_removal_policy_is_not_changed_by_transfer_model():
    ctx,s,rt,ref=ready()
    original=s.state_lifecycle_system.apply(ctx,state_id='capture',owner_id='A2')
    assert not s.state_removal_policy.evaluate_removal(ctx,RemovalOperation.ORDINARY_CLEANSE,original).allowed
    assert not s.state_removal_policy.evaluate_removal(ctx,RemovalOperation.SCRIPTED_GAMEPLAY_REMOVE,original).allowed
    new,_=transfer(ctx,s,ref,original)
    assert not ctx.metadata['_state_transfer_removal_permits']
    assert not s.state_removal_policy.evaluate_removal(ctx,RemovalOperation.ORDINARY_CLEANSE,new).allowed


def test_actual_round_lane_transfers_capture_from_captured_ally():
    ctx,s,rt,ref=ready()
    source=s.state_lifecycle_system.apply(ctx,state_id='capture',owner_id='A2')
    ctx.random.sample=lambda candidates,k:[ctx.units['B1']]
    tick(ctx,s,decisions=(False,True,False))
    assert not ctx.states.has_instance(source.instance_id)
    assert len(ctx.states.find(owner_id='B1',state_id='capture'))==1
    assert ctx.metadata['round_team_transfer_history'][-1]['transfers'][0]['status']=='TRANSFERRED'


def test_associated_dot_child_keeps_extra_coefficient_and_new_parent_generation():
    from sgs_v2.battle_core.state_application_reaction import (APPLICATION_DAMAGE_REACTION_STATE_ID,
        TROOP_DAMAGE_EFFECT_STATE_ID,ApplicationDamageReactionParams,register_application_reaction_definitions)
    ctx,s,rt,ref=ready()
    register_application_reaction_definitions(ctx.states)
    s.state_lifecycle_system.apply(ctx,state_id=APPLICATION_DAMAGE_REACTION_STATE_ID,owner_id='A2',
        runtime_params=ApplicationDamageReactionParams('burn',.5))
    source=s.state_lifecycle_system.apply(ctx,state_id='burn',owner_id='A2',source_id='B2',
        runtime_params=ContinuousDamageStateParams(),duration_rounds=2)
    child=ctx.states.find(owner_id='A2',state_id=TROOP_DAMAGE_EFFECT_STATE_ID)[0]
    # New-target reaction must not add another independent copy during cloning.
    s.state_lifecycle_system.apply(ctx,state_id=APPLICATION_DAMAGE_REACTION_STATE_ID,owner_id='B1',
        runtime_params=ApplicationDamageReactionParams('burn',.9))
    new,row=transfer(ctx,s,ref,source)
    children=ctx.states.find(owner_id='B1',state_id=TROOP_DAMAGE_EFFECT_STATE_ID)
    assert len(children)==1
    copied=children[0]
    assert copied.instance_id==row['identity_rebindings'][child.instance_id]
    assert copied.runtime_params.parent_state_instance_id==new.instance_id
    assert copied.runtime_params.frozen_damage_basis.coefficient==.5
    assert copied.runtime_params.frozen_damage_basis.application_generation_id==copied.current_generation_id
    assert not ctx.states.has_instance(child.instance_id)
    s.state_lifecycle_system.expire_at(ctx,round_no=1,phase='ROUND_END')
    assert not ctx.states.has_instance(new.instance_id) and not ctx.states.has_instance(copied.instance_id)


def test_implicit_prerequisite_reference_is_discovered_without_graph_edge():
    ctx,s,rt,ref=ready()
    source=s.state_lifecycle_system.apply(ctx,state_id='silence',owner_id='A2')
    child=apply(ctx,s,DAMAGE_RATE_STATE_ID,'A2',DamageRateParams(incoming_rate=.2,prerequisite_state_id=source.instance_id))
    new,row=transfer(ctx,s,ref,source)
    copied=ctx.states.get(row['identity_rebindings'][child.instance_id])
    assert copied.runtime_params.prerequisite_state_id==new.instance_id and copied.owner_id=='B1'
    assert s.state_effectiveness_policy.evaluate_state(ctx,copied).effective


def test_existing_dot_is_overwritten_and_expiry_does_not_use_old_window():
    ctx,s,rt,ref=ready()
    source=s.state_lifecycle_system.apply(ctx,state_id='poison',owner_id='A2',source_id='B2',
        runtime_params=ContinuousDamageStateParams(),duration_rounds=3)
    old=s.state_lifecycle_system.apply(ctx,state_id='poison',owner_id='B1',source_id='A2',
        runtime_params=ContinuousDamageStateParams(),duration_rounds=5)
    new,row=transfer(ctx,s,ref,source)
    assert not ctx.states.has_instance(old.instance_id)
    assert len(ctx.states.find(owner_id='B1',state_id='poison'))==1
    s.state_lifecycle_system.expire_at(ctx,round_no=1,phase='ROUND_END')
    assert not ctx.states.has_instance(new.instance_id)


@pytest.mark.parametrize('reason',('disabled','dead','removed','stale','target_dead'))
def test_rejected_direct_transfer_has_no_state_or_rng_changes(reason):
    ctx,s,rt,ref=ready()
    source=s.state_lifecycle_system.apply(ctx,state_id='silence',owner_id='A2')
    if reason=='disabled': rt.enabled=False
    if reason=='dead': ctx.units[rt.owner_id].troops=0
    if reason=='removed': s.state_lifecycle_system.remove(ctx,source.instance_id)
    if reason=='stale':
        from sgs_v2.battle_core.state_generation import StateApplicationGenerationId
        source=replace(source,current_generation_id=StateApplicationGenerationId('old-generation'))
    if reason=='target_dead': ctx.units['B1'].troops=0
    before=tuple(ctx.states.find())
    rng=ctx.random._rng.getstate()
    result=StateTransferSupport(s).transfer(ctx,source,'B1',ref)
    assert result['status'] in ('SOURCE_NOT_RESIDENT','SOURCE_GENERATION_CHANGED','PROVIDER_UNAVAILABLE','TARGET_UNAVAILABLE')
    assert tuple(ctx.states.find())==before and ctx.random._rng.getstate()==rng


def test_transfer_does_not_remove_unrelated_positive_damage_lane():
    ctx,s,rt,ref=ready()
    source=apply(ctx,s,DAMAGE_RATE_STATE_ID,'A2',DamageRateParams(outgoing_rate=-.2))
    positive=apply(ctx,s,DAMAGE_RATE_STATE_ID,'B1',DamageRateParams(outgoing_rate=.3))
    new,_=transfer(ctx,s,ref,source)
    assert ctx.states.get(positive.instance_id).runtime_params.outgoing_rate==.3
    assert new.runtime_params.outgoing_rate==-.2


@pytest.mark.parametrize('bounded',(False,True))
def test_activation_debuff_transfer_overwrites_same_scope_and_preserves_other_scopes(bounded):
    from sgs_v2.battle_core.state_modifiers import (ACTIVATION_RATE_BONUS_STATE_ID,
        ActivationRateBonusParams,BoundedActivationRateBonusParams)
    ctx,s,rt,ref=ready()
    sid=ACTIVATION_RATE_BONUS_STATE_ID
    params=(BoundedActivationRateBonusParams(SkillType.ACTIVE,-.12,'key','group',3)
        if bounded else ActivationRateBonusParams(SkillType.ACTIVE,-.12))
    original=apply(ctx,s,sid,'A2',params)
    old=apply(ctx,s,sid,'B1',ActivationRateBonusParams(SkillType.ACTIVE,-.05))
    other=apply(ctx,s,sid,'B1',ActivationRateBonusParams(SkillType.ASSAULT,-.06))
    positive=apply(ctx,s,sid,'B1',ActivationRateBonusParams(SkillType.ACTIVE,.04))
    scoped=apply(ctx,s,sid,'B1',ActivationRateBonusParams(SkillType.ACTIVE,-.02,skill_slot=SkillSlot.LEARNED_1))
    active=put_active(ctx,'B1',SkillSlot.LEARNED_2)
    assert s.state_modifier_support.activation_rate(ctx,active)==pytest.approx(.99)
    new,_=transfer(ctx,s,ref,original)
    assert s.state_modifier_support.activation_rate(ctx,active)==pytest.approx(.92)
    assert type(new.runtime_params) is ActivationRateBonusParams
    assert new.runtime_params.amount==-.12
    assert not ctx.states.has_instance(old.instance_id)
    assert all(ctx.states.has_instance(x.instance_id) for x in (other,positive,scoped))
    assert not ctx.states.has_instance(original.instance_id)
    s.state_lifecycle_system.expire_at(ctx,round_no=1,phase=BattlePhase.ROUND_END.value)
    assert not ctx.states.has_instance(new.instance_id)
