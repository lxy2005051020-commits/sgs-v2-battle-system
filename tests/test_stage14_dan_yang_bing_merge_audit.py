"""Additional adversarial merge audit using canonical production seams."""
import pytest

from tests.test_stage14_troop_dan_yang_bing import installed, round_start, fixed_damage
from sgs_v2.battle_core.effects import DamageEffect, EffectSourceRef
from sgs_v2.battle_core.operation_identity import SourceType
from sgs_v2.battle_core.enums import DamageType, DamageSourceType
from sgs_v2.battle_core.events import EventType
from sgs_v2.battle_core.temporary_damage_pool import pool_balance, TEMPORARY_DAMAGE_POOL_STATE_ID


def charged():
    c, s, rt, state = installed()
    round_start(c, s, 1)
    fixed_damage(c, s, 1000)
    round_start(c, s, 2)
    return c, s, rt, state


def test_canonical_effect_executor_and_aftermath_use_absorbed_actual_loss():
    c, s, _, state = charged()
    before = c.units['a3'].troops
    result = s.effect_executor.execute(c,
        DamageEffect('b1', 'a3', DamageType.STRATEGY, DamageSourceType.SKILL,
            source_skill_id='audit', source_ref=EffectSourceRef(SourceType.ACTIVE_SKILL, 'b1', 'audit')))
    events = c.event_bus.history
    absorption = [e for e in events if e.event_type is EventType.TEMPORARY_POOL_UPDATED
                  and e.payload['operation'] == 'ABSORB'][-1]
    damage = [e for e in events if e.event_type is EventType.DAMAGE_DEALT][-1]
    assigned = absorption.payload['assigned_target_damage']
    absorbed = absorption.payload['absorbed']
    assert absorbed == assigned * 36 // 100
    assert damage.payload['damage'] == before - c.units['a3'].troops == assigned - absorbed
    assert pool_balance(c, state).amount == 1000 - absorbed
    assert result is not None
    assert result.resolution.actual_target_troop_loss == assigned - absorbed
    assert result.damage_instance_id is not None


@pytest.mark.parametrize('family', ['share', 'distribution'])
def test_partition_target_absorption_does_not_intercept_direct_participant_losses(family):
    from tests.test_stage14_troop_qing_zhou_bing import state as apply_state
    from sgs_v2.battle_core import OfficialStateId
    from sgs_v2.battle_core.stage9_state_params import DamageShareStateParams, DistributionStateParams
    from sgs_v2.battle_core.stage9_integerization import ExactRatio
    c, s, _, pool = charged()
    if family == 'share':
        apply_state(c, s, OfficialStateId.DAMAGE_SHARE, 'a2', DamageShareStateParams('a3', ExactRatio(1, 2)))
    else:
        apply_state(c, s, OfficialStateId.DAMAGE_SPLIT, 'a2', DistributionStateParams(ExactRatio(1, 2)))
    before = sum(c.units[uid].troops for uid in ('a1', 'a2', 'a3'))
    result = s.effect_executor.execute(c, DamageEffect('b1', 'a2', DamageType.STRATEGY,
        DamageSourceType.SKILL, source_skill_id='audit',
        source_ref=EffectSourceRef(SourceType.ACTIVE_SKILL, 'b1', 'audit')))
    assert result.direct_losses
    absorbed = result.resolution.assigned_target_damage * 36 // 100
    assert result.resolution.actual_target_troop_loss == result.resolution.assigned_target_damage - absorbed
    total_actual = before - sum(c.units[uid].troops for uid in ('a1', 'a2', 'a3'))
    assert total_actual == result.resolution.actual_target_troop_loss + sum(x.actual_loss for x in result.direct_losses)
    assert pool_balance(c, pool).amount == 1000 - absorbed


def test_carrying_deputy_death_retains_living_team_pool_and_attribute():
    c, s, rt, state = charged()
    fixed_damage(c, s, 10000, source='b1', target=rt.owner_id)
    assert not c.units[rt.owner_id].is_alive
    assert c.states.find(owner_id='a1', state_id=TEMPORARY_DAMAGE_POOL_STATE_ID)
    assert s.attribute_system.get_defense(c, c.units['a3']) == 156
    assert fixed_damage(c, s, 100, source='b1', target='a3', kind=DamageType.STRATEGY).actual_target_troop_loss == 64
    assert pool_balance(c, state).amount == 964


def test_pool_state_removal_stops_absorption_and_generation():
    c, s, _, state = charged()
    s.state_lifecycle_system.remove(c, state.instance_id, reason='AUDIT')
    assert fixed_damage(c, s, 100, source='b1', target='a3', kind=DamageType.STRATEGY).actual_target_troop_loss == 100
    old = pool_balance(c, state)
    fixed_damage(c, s, 100)
    round_start(c, s, 3)
    assert pool_balance(c, state) == old


def test_pool_event_ledger_conserves_generation_decay_and_consumption():
    c, s, _, state = charged()
    for number in range(2, 5):
        fixed_damage(c, s, 333, source='b1', target='a3', kind=DamageType.STRATEGY)
        fixed_damage(c, s, 123, source='a3', target='b2')
        round_start(c, s, number + 1)
    balance = 0
    for event in c.event_bus.history:
        if event.event_type is not EventType.TEMPORARY_POOL_UPDATED:
            continue
        p = event.payload
        assert p['pool_before'] == balance
        if p['operation'] == 'ROUND_UPDATE':
            balance += p['generated'] - p['decayed']
        else:
            balance -= p['absorbed']
        assert balance == p['pool_after'] >= 0
    assert balance == pool_balance(c, state).amount


@pytest.mark.parametrize('amount,absorbed', [(25, 9), (1, 0), (50, 18)])
def test_absorption_decimal_floor_boundary(amount, absorbed):
    c, s, _, state = charged()
    result = fixed_damage(c, s, amount, source='b1', target='a3', kind=DamageType.STRATEGY)
    assert result.actual_target_troop_loss == amount - absorbed
    assert pool_balance(c, state).amount == 1000 - absorbed
