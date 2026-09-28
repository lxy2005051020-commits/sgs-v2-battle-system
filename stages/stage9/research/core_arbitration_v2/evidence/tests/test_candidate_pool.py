import pytest
from evidence.lib.unit_identity import UnitRegistry
from evidence.lib.target_pool import TargetPoolManager
from evidence.lib.state_tracker import StateTracker

def test_candidate_pool_resolution():
    lineup = {
        'my': [{'name': '关羽', 'pos': 1}, {'name': '张飞', 'pos': 2}],
        'enemy': [{'name': '曹操', 'pos': 1}, {'name': '许褚', 'pos': 2}, {'name': '夏侯惇', 'pos': 3}]
    }
    reg = UnitRegistry("f1", lineup)
    pool = TargetPoolManager(reg)
    st = StateTracker(reg)
    guanyu = reg.units['my'][0]
    caocao = reg.units['enemy'][0]
    xuchu = reg.units['enemy'][1]
    xiahoudun = reg.units['enemy'][2]

    res = pool.resolve_candidate_pool(guanyu, 10, st)
    assert res.is_known is True
    assert res.candidate_count == 3
    assert res.forced_target_reason is None

    pool.mark_dead(caocao)
    res2 = pool.resolve_candidate_pool(guanyu, 25, st)
    assert res2.candidate_count == 2

    st._record_apply('CONFUSION', guanyu, None, '暴戾无仁', 30)
    res_conf = pool.resolve_candidate_pool(guanyu, 35, st)
    assert res_conf.forced_target_reason == 'CONFUSION'
    assert res_conf.candidate_count == 3

    st._record_expire('CONFUSION', guanyu, 40)
    st._record_apply('TAUNT', guanyu, xuchu, '唇枪舌战', 45)
    res_taunt = pool.resolve_candidate_pool(guanyu, 50, st)
    assert res_taunt.forced_target_reason == 'TAUNT'
    assert res_taunt.candidate_count == 1
    assert res_taunt.candidates[0].same_unit(xuchu)
