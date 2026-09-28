import pytest
from evidence.lib.unit_identity import UnitRegistry
from evidence.lib.target_pool import TargetPoolManager
from evidence.lib.state_tracker import StateTracker

def test_counter_to_counter_eligibility():
    lineup = {
        'my': [{'name': '关羽', 'pos': 1}],
        'enemy': [{'name': '夏侯惇', 'pos': 1}]
    }
    reg = UnitRegistry("f1", lineup)
    st = StateTracker(reg)
    pool = TargetPoolManager(reg)
    guanyu = reg.units['my'][0]
    xiahoudun = reg.units['enemy'][0]

    st._record_apply('COUNTER', guanyu, guanyu, '后发制人', 5)
    assert st.is_state_active(guanyu, 'COUNTER', 10) is True
    assert pool.is_alive(guanyu) is True

    pool.mark_dead(guanyu)
    st.record_death(guanyu, 12)
    assert pool.is_alive(guanyu) is False
    assert st.is_state_active(guanyu, 'COUNTER', 13) is False
