import pytest
from evidence.lib.unit_identity import BattleUnitRef, UnitRegistry

def test_unit_ref_properties():
    u1 = BattleUnitRef("file1", "my", 0, 1, "关羽", 1001, 10000)
    u2 = BattleUnitRef("file1", "my", 0, 1, "关羽", 1001, 10000)
    u3 = BattleUnitRef("file1", "enemy", 0, 1, "关羽", 1001, 10000)
    u4 = BattleUnitRef("file1", "my", 1, 2, "张飞", 1002, 10000)

    assert u1.canonical_id == "my_0_关羽"
    assert u1.same_unit(u2)
    assert not u1.same_unit(u3)
    assert not u1.same_unit(u4)
    assert u1.same_camp(u4)
    assert u1.opposing_camp(u3)

def test_inv03_camp_disjoint():
    lineup = {
        'my': [{'name': '关羽', 'pos': 1}, {'name': '张飞', 'pos': 2}],
        'enemy': [{'name': '曹操', 'pos': 1}]
    }
    reg = UnitRegistry("file1", lineup)
    my_units = reg.units['my']
    enemy_units = reg.units['enemy']

    for m in my_units:
        assert m.camp == 'my'
        for e in enemy_units:
            assert e.camp == 'enemy'
            assert not m.same_camp(e)
            assert m.opposing_camp(e)

def test_resolve_from_event_color():
    lineup = {
        'my': [{'name': '勇城卫', 'pos': 1}],
        'enemy': [{'name': '勇城卫', 'pos': 1}]
    }
    reg = UnitRegistry("file1", lineup)

    u_my, unam_my = reg.resolve_from_event_text("[勇城卫]", "<font color='#75b3ed'>[勇城卫]</font>")
    assert u_my.camp == 'my'
    assert unam_my is True

    u_en, unam_en = reg.resolve_from_event_text("[勇城卫]", "<font color='#ec616b'>[勇城卫]</font>")
    assert u_en.camp == 'enemy'
    assert unam_en is True
