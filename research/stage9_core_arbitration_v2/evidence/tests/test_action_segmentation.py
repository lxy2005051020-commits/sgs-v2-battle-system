import pytest
from evidence.lib.unit_identity import UnitRegistry
from evidence.lib.target_pool import TargetPoolManager
from evidence.lib.state_tracker import StateTracker
from evidence.lib.action_segmenter import ActionSegmenter

def test_action_segmentation_turns():
    lineup = {
        'my': [{'name': '关羽', 'pos': 1}],
        'enemy': [{'name': '曹操', 'pos': 1}]
    }
    reg = UnitRegistry("f1", lineup)
    pool = TargetPoolManager(reg)
    st = StateTracker(reg)
    segmenter = ActionSegmenter(reg, pool, st)

    events = [
        {'cfg_id': 723, 'clean_desc': '[关羽] 行动回合', 'full_desc': "<font color='#75b3ed'>[关羽]</font> 行动回合"},
        {'cfg_id': 9, 'clean_desc': '[关羽]对[曹操]发动普通攻击', 'full_desc': "<font color='#75b3ed'>[关羽]</font>对<font color='#ec616b'>[曹操]</font>发动普通攻击"},
        {'cfg_id': 28, 'clean_desc': '[曹操]损失了兵力100', 'full_desc': ''},
        {'cfg_id': 733, 'clean_desc': '', 'full_desc': ''}
    ]

    attacks, combos = segmenter.segment_turns_and_actions(events)
    assert len(attacks) == 1
    assert attacks[0].actor.display_name == '关羽'
    assert attacks[0].intended_target.display_name == '曹操'
    assert attacks[0].resolved_target.display_name == '曹操'
    assert attacks[0].is_guard_redirected is False
