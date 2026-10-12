"""Real action-start timing, snapshots, final-addition lane and lifecycle guards."""
from dataclasses import replace
import pytest

from tests.test_stage14_troop_batch01 import setup
from sgs_v2.battle_core import (
    BattlePhase, DamageType, EventType, TroopType, TroopAdmissionStatus,
    admit_and_install_troop_skill, create_fei_xiong_jun_runtime, StateCandidate,
)
from sgs_v2.battle_core.action_start_recovery_damage import (
    ACTION_START_RECOVERY_DAMAGE_STATE_ID, project_settled_team_recovery,
    ActionStartRecoveryDamageParams,
)
from sgs_v2.battle_core.additive_damage import FinalAdditiveDamageRequest, FinalAdditiveDamageResult
from sgs_v2.battle_core.enums import DamageSourceType
from sgs_v2.battle_core.recovery_system import RecoveryRequest, RecoveryModifierPolicy
from sgs_v2.battle_core.rule_hooks import UnitActionStartHook
from sgs_v2.battle_core.state_modifiers import INCOMING_DAMAGE_REDUCTION_STATE_ID, IncomingDamageReductionParams


def fixture(*, holder='a2', success=True):
    c, s, _ = setup(create_fei_xiong_jun_runtime, TroopType.CAVALRY)
    for u in c.units.values():
        u.intelligence = 200
    rt = create_fei_xiong_jun_runtime(holder)
    assert admit_and_install_troop_skill(c, s, rt).status is TroopAdmissionStatus.SUCCESS
    for u in c.units.values():
        u.troops, u.wounded_troops = 5000, 5000
    c.random.chance = lambda p: c.random.probabilities.append(p) or success
    c.current_round, c.current_phase = 1, BattlePhase.UNIT_ACTION_START.value
    return c, s, rt


def recover(c, s, amount=100, source='a2', target='a3', apply=True):
    return s.recovery_system.resolve(c, RecoveryRequest(source, target, amount,
        modifier_policy=RecoveryModifierPolicy.APPLY if apply else RecoveryModifierPolicy.NONE))


def action(c, s, actor='a1', round_no=1):
    c.current_round, c.current_phase = round_no, BattlePhase.UNIT_ACTION_START.value
    return s.rule_hook_system.process(c, UnitActionStartHook(round_no, actor))


def snapshots(c):
    return [e for e in c.event_bus.history if e.payload.get('event_kind') == 'ACCUMULATED_RECOVERY_SNAPSHOT']


def damages(c):
    return [e for e in c.event_bus.history if e.event_type is EventType.DAMAGE_DEALT
            and e.payload.get('source_skill_id') == '20247']


def test_actual_recovery_not_nominal_target_count_provider_and_performer():
    c, s, rt = fixture()
    assert recover(c, s).actual_recovery == 116
    result = action(c, s)
    assert c.random.probabilities == [.6]
    snap = snapshots(c)[0]
    assert snap.actor_id == 'a1' and snap.payload['provider_id'] == rt.owner_id == 'a2'
    assert snap.payload['actual_recovery_snapshot'] == 116
    assert snap.payload['final_additive_damage_per_target'] == 11.6
    assert len(snap.payload['target_ids']) == 2 and len(set(snap.payload['target_ids'])) == 2
    assert len(damages(c)) == 2
    for r in result.effect_results:
        damage = r.resolution.damage
        assert isinstance(damage, FinalAdditiveDamageResult)
        assert damage.coefficient == .64 and damage.final_additive_damage == 11.6
        assert damage.final_damage == int(damage.unaugmented_final_damage + 11.6)
        assert damage.source_id == 'a1'


def test_only_commander_action_rolls_once_per_round_and_failure_keeps_accumulation():
    c, s, _ = fixture(success=False)
    recover(c, s, 100, apply=False)
    action(c, s, 'a2')
    action(c, s, 'a3')
    assert not c.random.probabilities
    action(c, s)
    action(c, s)
    assert c.random.probabilities == [.6] and not snapshots(c)
    recover(c, s, 50, apply=False)
    c.random.chance = lambda p: c.random.probabilities.append(p) or True
    action(c, s, round_no=2)
    assert snapshots(c)[0].payload['actual_recovery_snapshot'] == 150
    assert len(damages(c)) == 2


def test_one_shared_snapshot_and_damage_during_recovery_is_next_batch():
    c, s, _ = fixture()
    recover(c, s, 1000, apply=False)
    execute = s.effect_executor.execute
    count = [0]
    def execute_and_recover(context, effect):
        result = execute(context, effect)
        count[0] += 1
        if count[0] == 1:
            recover(c, s, 200, apply=False)
        return result
    s.effect_executor.execute = execute_and_recover
    first = action(c, s)
    assert [r.effect.final_additive_damage for r in first.effect_results] == [100, 100]
    s.effect_executor.execute = execute
    action(c, s, round_no=2)
    assert [e.payload['actual_recovery_snapshot'] for e in snapshots(c)] == [1000, 200]
    action(c, s, round_no=3)
    assert snapshots(c)[-1].payload['actual_recovery_snapshot'] == 0


def test_overheal_counts_only_actual_and_enemy_team_healing_is_excluded():
    c, s, _ = fixture()
    c.units['a3'].troops, c.units['a3'].wounded_troops = 9995, 5
    assert recover(c, s, 1000).actual_recovery == 5
    recover(c, s, 400, source='b1', target='b2', apply=False)
    action(c, s)
    assert snapshots(c)[0].payload['actual_recovery_snapshot'] == 5


@pytest.mark.parametrize('boundary', ['disabled', 'provider_death', 'actor_death', 'suppressed'])
def test_lifecycle_gate_has_no_roll_no_consumption(boundary):
    c, s, rt = fixture()
    recover(c, s, 100, apply=False)
    if boundary == 'disabled':
        rt.enabled = False
    elif boundary == 'provider_death':
        c.units[rt.owner_id].troops = 0
    elif boundary == 'actor_death':
        # Engine skips dead actors. Direct support must also be defensive.
        c.units['a1'].troops = 0
    else:
        from sgs_v2.battle_core.state_effectiveness import StateEffectivenessContribution, SuppressionCause, LocalRuleCauseRef
        s.state_effectiveness_policy.register_rule_adapter(lambda c, state, session:
            StateEffectivenessContribution(suppression_causes=(SuppressionCause('test', LocalRuleCauseRef('gate')),)))
    if boundary == 'actor_death':
        from sgs_v2.battle_core.action_start_recovery_damage import ActionStartRecoveryDamageSupport
        ActionStartRecoveryDamageSupport(s).execute(c, UnitActionStartHook(1, 'a1'))
    else:
        action(c, s)
    assert not c.random.probabilities and not damages(c)
    state = c.states.find(state_id=ACTION_START_RECOVERY_DAMAGE_STATE_ID)[0]
    assert project_settled_team_recovery(c, team_id='a', after_sequence=state.runtime_params.after_sequence).actual_recovery == 100


def test_separate_final_addition_is_not_scaled_by_incoming_reduction():
    c, s, _ = fixture()
    for uid in ('b1', 'b2', 'b3'):
        s.state_application_coordinator.apply_candidate(c, StateCandidate(
            INCOMING_DAMAGE_REDUCTION_STATE_ID, uid, IncomingDamageReductionParams(DamageType.STRATEGY, .5)))
    recover(c, s, 1000, apply=False)
    result = action(c, s)
    for r in result.effect_results:
        d = r.resolution.damage
        assert d.final_damage - d.unaugmented_final_damage == 100
        assert d.pipeline_trace.modifier_result.output_damage < d.scaled_damage
        assert d.coefficient == .64


@pytest.mark.parametrize('value', [-1, True, float('nan'), float('inf')])
def test_final_addition_validation(value):
    with pytest.raises((TypeError, ValueError)):
        FinalAdditiveDamageRequest('a1', 'b1', DamageType.STRATEGY, DamageSourceType.SKILL,
                                  final_additive_damage=value)


def test_final_addition_does_not_leak_to_next_ordinary_request():
    c, s, _ = fixture()
    c.random.randint = lambda a, b: a
    request = FinalAdditiveDamageRequest('a1', 'b1', DamageType.STRATEGY, DamageSourceType.SKILL,
        coefficient=.64, final_additive_damage=100)
    augmented = s.damage_system.calculate(c, request)
    ordinary = s.damage_system.calculate(c, replace(request, final_additive_damage=0))
    assert augmented.final_damage == ordinary.final_damage + 100
    assert not isinstance(ordinary, FinalAdditiveDamageResult)


@pytest.mark.parametrize('boundary', ['weakness', 'evasion', 'barrier'])
def test_prevention_never_restores_bonus_damage(boundary):
    from sgs_v2.battle_core import OfficialStateId
    from sgs_v2.battle_core.stage11_state_params import EvasionStateParams, ResistanceStateParams
    c, s, _ = fixture()
    if boundary == 'weakness':
        s.state_lifecycle_system.apply(c, state_id=OfficialStateId.WEAKNESS.value, owner_id='a1', source_id='b1')
    else:
        for uid in ('b1', 'b2', 'b3'):
            s.state_lifecycle_system.apply(c,
                state_id=(OfficialStateId.EVASION if boundary == 'evasion' else OfficialStateId.BARRIER).value,
                owner_id=uid, source_id=uid,
                runtime_params=EvasionStateParams() if boundary == 'evasion' else ResistanceStateParams())
    recover(c, s, 1000, apply=False)
    result = action(c, s)
    assert all(r.resolution.damage.final_damage == 0 for r in result.effect_results)
    assert all(c.units[uid].troops == 5000 for uid in ('b1', 'b2', 'b3'))
    assert snapshots(c)[0].payload['actual_recovery_snapshot'] == 1000


def test_critical_does_not_multiply_final_addition():
    from sgs_v2.battle_core import OfficialStateId
    from sgs_v2.battle_core.stage11_state_params import CriticalStateParams
    c, s, _ = fixture()
    s.state_lifecycle_system.apply(c, state_id=OfficialStateId.STRATEGY_CRITICAL.value,
        owner_id='a1', source_id='a1', runtime_params=CriticalStateParams(chance=1, bonus=1))
    recover(c, s, 1000, apply=False)
    result = action(c, s)
    for r in result.effect_results:
        d = r.resolution.damage
        assert d.critical_triggered and d.final_damage - d.unaugmented_final_damage == 100


def test_real_damage_lifesteal_is_next_snapshot_not_second_target_bonus():
    from sgs_v2.battle_core import OfficialStateId
    from sgs_v2.battle_core.stage11_state_params import LifeStealStateParams
    from sgs_v2.battle_core.stage9_integerization import ExactRatio
    c, s, _ = fixture()
    s.state_lifecycle_system.apply(c, state_id=OfficialStateId.STRATEGY_LIFESTEAL.value,
        owner_id='a1', source_id='a1', runtime_params=LifeStealStateParams(ExactRatio(1, 2)))
    recover(c, s, 1000, apply=False)
    first = action(c, s)
    assert [r.effect.final_additive_damage for r in first.effect_results] == [100, 100]
    after = project_settled_team_recovery(c, team_id='a', after_sequence=snapshots(c)[0].payload['through_sequence'])
    assert after.actual_recovery > 0
    action(c, s, round_no=2)
    assert snapshots(c)[1].payload['actual_recovery_snapshot'] == after.actual_recovery


def test_current_actor_permission_denial_preserves_pool_without_rng():
    from sgs_v2.battle_core.execution_right_runtime import CurrentActorPermissionDecision, CurrentActorPermissionStatus
    c, s, _ = fixture()
    recover(c, s, 100, apply=False)
    s.current_actor_permission_policy.register_rule_adapter(lambda c, req:
        CurrentActorPermissionDecision(req, CurrentActorPermissionStatus.DENY, ('test',)))
    action(c, s)
    assert not c.random.probabilities and not snapshots(c)


def test_target_shortage_preserves_existing_explicit_boundary_without_consumption():
    c, s, _ = fixture()
    recover(c, s, 100, apply=False)
    c.units['b2'].troops = c.units['b3'].troops = 0
    state = c.states.find(state_id=ACTION_START_RECOVERY_DAMAGE_STATE_ID)[0]
    with pytest.raises((ValueError, NotImplementedError), match='insufficient'):
        action(c, s)
    assert c.states.get(state.instance_id).runtime_params == state.runtime_params


def test_runtime_cursor_is_battle_scoped_and_never_mutates_physical_state():
    from sgs_v2.battle_core.action_start_recovery_damage import recovery_damage_cursor
    c, s, _ = fixture()
    state = c.states.find(state_id=ACTION_START_RECOVERY_DAMAGE_STATE_ID)[0]
    recover(c, s, 100, apply=False)
    action(c, s)
    assert c.states.get(state.instance_id) == state
    assert recovery_damage_cursor(c, state).last_attempt_round == 1
    other, other_s, _ = fixture()
    other_state = other.states.find(state_id=ACTION_START_RECOVERY_DAMAGE_STATE_ID)[0]
    assert other_state.instance_id == state.instance_id
    assert recovery_damage_cursor(other, other_state).last_attempt_round == 0
    recover(other, other_s, 300, apply=False)
    action(other, other_s)
    assert snapshots(other)[0].payload['actual_recovery_snapshot'] == 300
