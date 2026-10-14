"""Separate adversarial fixture for transfer completion and ordinary contracts."""
import pytest
from sgs_v2.battle_core import (BattleContext,BattleSystems,BattleEngine,EventBus,RandomSystem,
    UnitRuntime,TroopType,LineupPosition,create_yan_xing_zhen_runtime,admit_and_install_formation_skill,
    SkillRuntime,SkillDefinition,SkillType,SkillSlot,SkillTargetMode)
from sgs_v2.battle_core.state_transfer_support import StateTransferSupport
from sgs_v2.battle_core.official_state_catalog import register_official_state_definitions
from sgs_v2.battle_core.provider_identity import SkillProviderRef
from sgs_v2.battle_core.state_application import StateCandidate
from sgs_v2.battle_core.state_runtime_params import EmptyStateRuntimeParams
from sgs_v2.battle_core.state_definition import StateDefinition
from sgs_v2.battle_core.skill_definition import ApplyStateSkillEffectSpec
from sgs_v2.battle_core.stage10_state_params import ContinuousDamageStateParams
from sgs_v2.battle_core.stage11_state_params import Stage11TimedFlagParams
from sgs_v2.battle_core.rule_hooks import RoundStartHook


def context(install=True):
    units={f'{team}{i}':UnitRuntime(f'{team}{i}',f'{team}{i}',team,6000,6000,210,120,100-i,
        intelligence=180,troop_type=TroopType.SHIELD,lineup_position=position)
        for team in ('R','L') for i,position in enumerate(LineupPosition)}
    c=BattleContext('independent-transfer-audit',units,EventBus(),RandomSystem(521),max_rounds=4)
    c.current_phase='PRE_BATTLE'
    c.metadata['attacker_team_id']='R'
    s=BattleSystems()
    register_official_state_definitions(c.states)
    rt=create_yan_xing_zhen_runtime('R1',slot=SkillSlot.LEARNED_2)
    c.skill_runtimes.register(rt)
    if install:
        assert admit_and_install_formation_skill(c,s,rt).status.value=='SUCCESS'
    return c,s,SkillProviderRef(rt.owner_id,rt.skill_slot,rt.definition.skill_id)


def test_whole_battle_dot_transfer_replay_is_deterministic():
    histories=[]
    for _ in range(2):
        c,s,ref=context(False)
        s.state_lifecycle_system.apply(c,state_id='burn',owner_id='R2',source_id='L2',
            runtime_params=ContinuousDamageStateParams(),duration_rounds=2)
        result=BattleEngine(c,s).run()
        histories.append((result.final_troops,c.metadata.get('round_team_transfer_history',[])))
    assert histories[0]==histories[1]
    assert histories[0][1]


def test_provider_command_suppression_moves_to_new_holder_and_expires():
    c,s,ref=context()
    for owner in ('R2','L2'):
        sid='audit-command-'+owner
        c.states.register_definition(StateDefinition(sid,sid))
        c.skill_runtimes.register(SkillRuntime(SkillDefinition(sid,sid,1,SkillTargetMode.SELF,
            (ApplyStateSkillEffectSpec(sid),),skill_type=SkillType.COMMAND),owner,SkillSlot.INHERENT))
    source=s.state_application_coordinator.apply_candidate(c,StateCandidate('false_report','R2',EmptyStateRuntimeParams(),source_id='L1')).instance
    oldref=SkillProviderRef('R2',SkillSlot.INHERENT,'audit-command-R2')
    newref=SkillProviderRef('L2',SkillSlot.INHERENT,'audit-command-L2')
    assert not s.provider_validity_policy.evaluate_provider(c,oldref).valid
    c.current_phase='ROUND_START'
    c.current_round=1
    result=StateTransferSupport(s).transfer(c,source,'L2',ref)
    assert result['status']=='TRANSFERRED'
    assert s.provider_validity_policy.evaluate_provider(c,oldref).valid
    assert not s.provider_validity_policy.evaluate_provider(c,newref).valid
    # Production expiry coordinates physical removal and dependency settlement.
    # Calling the low-level physical writer alone intentionally omits the latter.
    BattleEngine(c,s)._settle_phase_expiry(round_no=1,phase='ROUND_END')
    assert s.provider_validity_policy.evaluate_provider(c,newref).valid


def test_normal_nonstacking_application_does_not_gain_transfer_override():
    c,s,ref=context()
    s.state_lifecycle_system.apply(c,state_id='weakness',owner_id='L2',runtime_params=Stage11TimedFlagParams())
    with pytest.raises(ValueError,match='already exists'):
        s.state_lifecycle_system.apply(c,state_id='weakness',owner_id='L2',runtime_params=Stage11TimedFlagParams())
    assert not c.metadata.get('_state_transfer_in_progress',0)


def test_replaying_original_source_after_success_cannot_duplicate_effect_or_rng():
    c,s,ref=context()
    source=s.state_lifecycle_system.apply(c,state_id='healing_ban',owner_id='R2')
    c.current_phase='ROUND_START'
    c.current_round=1
    support=StateTransferSupport(s)
    assert support.transfer(c,source,'L2',ref)['status']=='TRANSFERRED'
    before=tuple(c.states.find())
    rng=c.random._rng.getstate()
    assert support.transfer(c,source,'L2',ref)['status']=='SOURCE_NOT_RESIDENT'
    assert tuple(c.states.find())==before and c.random._rng.getstate()==rng


def test_original_attribute_scaling_is_still_deferred_at_runtime():
    c,s,ref=context()
    c.units['R1'].defense=900
    c.current_phase='ROUND_START'
    c.current_round=1
    decisions=iter((False,False,True))
    c.random.chance=lambda probability: next(decisions)
    s.rule_hook_system.process(c,RoundStartHook(1))
    row=c.metadata['round_team_transfer_history'][0]
    assert row['probability']==.35 and row['attribute_amount']==10
    assert row['theft']['total']==30


def test_full_engine_false_report_transfer_releases_binding_after_round_end():
    c,s,ref=context(False)
    c.max_rounds=1
    for owner in ('R2','L2'):
        sid='full-command-'+owner
        c.states.register_definition(StateDefinition(sid,sid))
        c.skill_runtimes.register(SkillRuntime(SkillDefinition(sid,sid,1,SkillTargetMode.SELF,
            (ApplyStateSkillEffectSpec(sid),),skill_type=SkillType.COMMAND),owner,SkillSlot.INHERENT))
    source=s.state_application_coordinator.apply_candidate(c,StateCandidate('false_report','R2',
        EmptyStateRuntimeParams(),source_id='L1')).instance
    c.random.chance=lambda probability: True
    c.random.sample=lambda candidates,k:[c.units['L2'] if candidates[0].team_id=='L' else c.units['R0']]
    BattleEngine(c,s).run()
    transfers=c.metadata['round_team_transfer_history'][0]['transfers']
    assert any(row.get('state_id')=='false_report' and row['status']=='TRANSFERRED' for row in transfers)
    assert not c.states.find(state_id='false_report')
    for owner in ('R2','L2'):
        provider=SkillProviderRef(owner,SkillSlot.INHERENT,'full-command-'+owner)
        assert s.provider_validity_policy.evaluate_provider(c,provider).valid
