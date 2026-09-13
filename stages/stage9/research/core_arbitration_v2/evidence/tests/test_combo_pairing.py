import pytest
from evidence.lib.unit_identity import UnitRegistry
from evidence.lib.target_pool import TargetPoolManager
from evidence.lib.state_tracker import StateTracker
from evidence.lib.action_segmenter import ActionSegmenter
from evidence.lib.evidence_utils import verify_combo_invariants

def test_combo_pairing_and_invariants():
    lineup = {
        'my': [{'name': '太史慈', 'pos': 1}],
        'enemy': [{'name': '曹操', 'pos': 1}]
    }
    reg = UnitRegistry("f1", lineup)
    pool = TargetPoolManager(reg)
    st = StateTracker(reg)
    segmenter = ActionSegmenter(reg, pool, st)

    events = [
        {'cfg_id': 723, 'clean_desc': '[太史慈] 行动回合', 'full_desc': "<font color='#75b3ed'>[太史慈]</font> 行动回合"},
        {'cfg_id': 9, 'clean_desc': '[太史慈]对[曹操]发动普通攻击', 'full_desc': "<font color='#75b3ed'>[太史慈]</font>对<font color='#ec616b'>[曹操]</font>发动普通攻击"},
        {'cfg_id': 28, 'clean_desc': '[曹操]损失了兵力100', 'full_desc': ''},
        {'cfg_id': 230, 'clean_desc': '[太史慈]执行来自【神射】的「连击」效果', 'full_desc': ''},
        {'cfg_id': 9, 'clean_desc': '[太史慈]对[曹操]发动普通攻击', 'full_desc': "<font color='#75b3ed'>[太史慈]</font>对<font color='#ec616b'>[曹操]</font>发动普通攻击"},
        {'cfg_id': 28, 'clean_desc': '[曹操]损失了兵力100', 'full_desc': ''},
        {'cfg_id': 733, 'clean_desc': '', 'full_desc': ''}
    ]

    attacks, combos = segmenter.segment_turns_and_actions(events)
    assert len(combos) == 1
    c = combos[0]
    assert c.candidate_count == 1
    assert c.condition == 'NORMAL'
    assert c.target1_status == 'SURVIVED'
    assert c.same_target is True

    inv_res = verify_combo_invariants(combos)
    assert inv_res['inv01_candidate1_same']['pass_rate'] == 1.0
    assert inv_res['inv06_combo_actor_match']['pass_rate'] == 1.0
