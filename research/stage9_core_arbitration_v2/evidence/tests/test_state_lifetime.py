import pytest
from evidence.lib.unit_identity import BattleUnitRef, UnitRegistry
from evidence.lib.state_tracker import StateTracker

def test_inv04_active_state_end():
    lineup = {
        'my': [{'name': '关羽', 'pos': 1}],
        'enemy': [{'name': '曹操', 'pos': 1}]
    }
    reg = UnitRegistry("file1", lineup)
    tracker = StateTracker(reg)
    guanyu = reg.units['my'][0]
    caocao = reg.units['enemy'][0]

    tracker._record_apply('TAUNT', guanyu, caocao, '守而必固', 10)
    assert tracker.is_state_active(guanyu, 'TAUNT', 5) is False
    assert tracker.is_state_active(guanyu, 'TAUNT', 10) is True
    assert tracker.is_state_active(guanyu, 'TAUNT', 15) is True

    tracker._record_expire('TAUNT', guanyu, 20)
    assert tracker.is_state_active(guanyu, 'TAUNT', 15) is True
    assert tracker.is_state_active(guanyu, 'TAUNT', 20) is False
    assert tracker.is_state_active(guanyu, 'TAUNT', 25) is False

def test_death_cleanup_state():
    lineup = {
        'my': [{'name': '关羽', 'pos': 1}],
        'enemy': [{'name': '曹操', 'pos': 1}]
    }
    reg = UnitRegistry("file1", lineup)
    tracker = StateTracker(reg)
    guanyu = reg.units['my'][0]
    caocao = reg.units['enemy'][0]

    tracker._record_apply('TAUNT', guanyu, caocao, '唇枪舌战', 10)
    assert tracker.is_state_active(guanyu, 'TAUNT', 12) is True

    tracker.record_death(caocao, 15)
    assert tracker.is_state_active(guanyu, 'TAUNT', 16) is False
