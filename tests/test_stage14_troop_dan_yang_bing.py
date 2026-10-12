from dataclasses import replace

import pytest

from tests.test_stage14_troop_batch01 import setup
from sgs_v2.battle_core import (BattleEngine, BattlePhase, EventType, TroopType,
    TroopAdmissionStatus, admit_and_install_troop_skill, create_dan_yang_bing_runtime)
from sgs_v2.battle_core.damage_system import DamageRequest
from sgs_v2.battle_core.enums import DamageType, DamageSourceType
from sgs_v2.battle_core.rule_hooks import RoundStartHook
from sgs_v2.battle_core.temporary_damage_pool import (TemporaryDamagePoolParams,
    TEMPORARY_DAMAGE_POOL_STATE_ID, pool_balance)
from sgs_v2.battle_core.troop_admission import TROOP_SKILL_REGISTRY
from sgs_v2.battle_core.troop_skills.dan_yang_bing import CONFIG, SKILL


def installed(commander="a1", holder="a2"):
    c, s, _ = setup(create_dan_yang_bing_runtime, TroopType.SHIELD)
    for unit in c.units.values():
        unit.intelligence = 120
    c.units["a1"].name = commander
    rt = create_dan_yang_bing_runtime(holder)
    assert admit_and_install_troop_skill(c, s, rt).status is TroopAdmissionStatus.SUCCESS
    state = c.states.find(owner_id="a1", state_id=TEMPORARY_DAMAGE_POOL_STATE_ID)[0]
    return c, s, rt, state


def round_start(c, s, number):
    c.current_round, c.current_phase = number, BattlePhase.ROUND_START.value
    s.rule_hook_system.process(c, RoundStartHook(number))


def fixed_damage(c, s, amount, *, source="a3", target="b1", kind=DamageType.WEAPON):
    # Real damage calculation for topology; exact input to real destructive seam.
    calculated = s.damage_system.calculate(c, DamageRequest(source, target, kind, DamageSourceType.SKILL))
    return s.damage_resolution_system.apply_result(c, replace(calculated, final_damage=amount))


def test_registry_conversion_and_team_command_bonus():
    c, s, rt, state = installed()
    assert TROOP_SKILL_REGISTRY[SKILL.skill_id] is CONFIG
    assert len(TROOP_SKILL_REGISTRY) == 15
    for uid in ("a1", "a2", "a3"):
        assert c.units[uid].special_troop_id.value == "DAN_YANG_BING"
        assert c.units[uid].troop_type is TroopType.SHIELD
        assert s.attribute_system.get_defense(c, c.units[uid]) == 156
    assert s.attribute_system.get_defense(c, c.units["b1"]) == 120
    assert state.source_id == rt.owner_id and state.source_skill_slot == rt.skill_slot
    assert len(c.states.find(owner_id="a2", state_id=TEMPORARY_DAMAGE_POOL_STATE_ID)) == 0
    assert admit_and_install_troop_skill(c, s, rt).status is TroopAdmissionStatus.REJECTED_ALREADY_INSTALLED


@pytest.mark.parametrize("commander,holder,ratio", [("a1", "a2", .36), ("陶谦", "a2", .40), ("a1", "a1", .36)])
def test_bonus_uses_commander(commander, holder, ratio):
    c, s, rt, state = installed(commander, holder)
    c.units["a2"].name = "陶谦"
    assert state.runtime_params.absorb_ratio == ratio


def test_previous_round_actual_loss_generation_decay_stack_and_idempotent_hook():
    c, s, _, state = installed()
    round_start(c, s, 1)
    assert pool_balance(c, state).amount == 0
    fixed_damage(c, s, 100)
    fixed_damage(c, s, 20, source="a2", target="b2")
    fixed_damage(c, s, 900, kind=DamageType.STRATEGY)
    fixed_damage(c, s, 900, source="b1", target="a3")
    round_start(c, s, 2)
    assert pool_balance(c, state).amount == 120
    round_start(c, s, 2)
    assert pool_balance(c, state).amount == 120
    fixed_damage(c, s, 200)
    round_start(c, s, 3)
    assert pool_balance(c, state).amount == 308
    round_start(c, s, 4)
    assert pool_balance(c, state).amount == 277


@pytest.mark.parametrize("commander,expected", [("a1", 64), ("陶谦", 60)])
def test_shared_pool_absorbs_each_teammate_strategy_only(commander, expected):
    c, s, _, state = installed(commander)
    round_start(c, s, 1)
    fixed_damage(c, s, 200)
    round_start(c, s, 2)
    for target in ("a2", "a3"):
        result = fixed_damage(c, s, 100, source="b1", target=target, kind=DamageType.STRATEGY)
        assert result.actual_target_troop_loss == expected
        assert result.damage.final_damage == result.assigned_target_damage == 100
        assert result.troop_change.wounded_generated == expected * 90 // 100
    balance = pool_balance(c, state).amount
    fixed_damage(c, s, 100, source="b1", target="a3")
    assert pool_balance(c, state).amount == balance


def test_pool_exhaustion_prevention_and_calculation_does_not_consume():
    c, s, _, state = installed()
    round_start(c, s, 1)
    fixed_damage(c, s, 10)
    round_start(c, s, 2)
    req = DamageRequest("b1", "a3", DamageType.STRATEGY, DamageSourceType.SKILL)
    calculated = s.damage_system.calculate(c, req)
    assert pool_balance(c, state).amount == 10
    s.damage_resolution_system.apply_result(c, replace(calculated, prevented=True, final_damage=0))
    assert pool_balance(c, state).amount == 10
    result = fixed_damage(c, s, 100, source="b1", target="a3", kind=DamageType.STRATEGY)
    assert result.actual_target_troop_loss == 90
    assert pool_balance(c, state).amount == 0
    assert fixed_damage(c, s, 100, source="b1", target="a3", kind=DamageType.STRATEGY).actual_target_troop_loss == 100


def test_direct_troop_loss_does_not_consume_pool_and_actual_capacity_limits_generation():
    c, s, _, state = installed()
    round_start(c, s, 1)
    c.units["b1"].troops = 9
    fixed_damage(c, s, 100)
    round_start(c, s, 2)
    assert pool_balance(c, state).amount == 9
    s.troop_system.apply_damage(c.units["a3"], 20)
    assert pool_balance(c, state).amount == 9


def test_full_engine_admission_and_round_generation():
    c, s, rt = setup(create_dan_yang_bing_runtime, TroopType.SHIELD)
    c.skill_runtimes.register(rt)
    result = BattleEngine(c, s).run()
    assert result is not None and c.ended
    updates = [e for e in c.event_bus.history if e.event_type is EventType.TEMPORARY_POOL_UPDATED]
    assert updates[0].payload["generated"] == 0
    assert any(e.payload["generated"] > 0 for e in updates[1:])
    assert not c.states.find(owner_id="a1", state_id=TEMPORARY_DAMAGE_POOL_STATE_ID)


@pytest.mark.parametrize("key,value", [("absorb_ratio", -1), ("absorb_ratio", 2),
    ("decay_ratio", float("nan")), ("generation_ratio", True), ("generated_damage_type", "WEAPON")])
def test_generic_parameter_validation(key, value):
    values = {"absorb_ratio": .36, key: value}
    with pytest.raises((ValueError, TypeError)):
        TemporaryDamagePoolParams(**values)


def test_suppression_preserves_pool_decay_and_resumption():
    from sgs_v2.battle_core.state_effectiveness import (
        StateEffectivenessContribution, SuppressionCause, LocalRuleCauseRef)
    c, s, _, state = installed()
    round_start(c, s, 1)
    fixed_damage(c, s, 100)
    round_start(c, s, 2)
    suppressed = [True]
    def gate(context, instance, session):
        if suppressed[0] and instance.state_id == TEMPORARY_DAMAGE_POOL_STATE_ID:
            return StateEffectivenessContribution(suppression_causes=(
                SuppressionCause("test_gate", LocalRuleCauseRef("test")),))
        return StateEffectivenessContribution()
    s.state_effectiveness_policy.register_rule_adapter(gate)
    assert fixed_damage(c, s, 100, source="b1", target="a3", kind=DamageType.STRATEGY).actual_target_troop_loss == 100
    fixed_damage(c, s, 100)
    round_start(c, s, 3)
    assert pool_balance(c, state).amount == 90
    suppressed[0] = False
    assert fixed_damage(c, s, 100, source="b1", target="a3", kind=DamageType.STRATEGY).actual_target_troop_loss == 64
    assert pool_balance(c, state).amount == 54


def test_production_permit_consumes_pool_once_replay_has_no_mutation():
    from sgs_v2.battle_core.operation_identity import OperationLineage, SourceType
    from sgs_v2.battle_core.damage_resolution_system import DamageSettlementRequest, SettlementOrigin
    c, s, _, state = installed()
    round_start(c, s, 1)
    fixed_damage(c, s, 100)
    round_start(c, s, 2)
    lineage = OperationLineage(None, None, None, SourceType.ACTIVE_SKILL,
        physical_attacker="b1", physical_skill="test", credit_owner="b1")
    coordinator = s.damage_instance_coordinator
    damage_id = coordinator.begin_damage_instance(c, lineage)
    calculated = s.damage_system.calculate(c,
        DamageRequest("b1", "a3", DamageType.STRATEGY, DamageSourceType.SKILL))
    request = DamageSettlementRequest(replace(calculated, final_damage=100), 100,
        damage_id, lineage, SettlementOrigin.STAGE9)
    permit = coordinator.issue_settlement_permit(damage_id, lineage, c)
    result = s.damage_resolution_system.settle(c, request, permit)
    assert result.actual_target_troop_loss == 64 and pool_balance(c, state).amount == 64
    before = (c.units["a3"].troops, pool_balance(c, state), len(c.event_bus.history))
    with pytest.raises(ValueError):
        s.damage_resolution_system.settle(c, request, permit)
    assert (c.units["a3"].troops, pool_balance(c, state), len(c.event_bus.history)) == before
    coordinator.close_damage_instance(damage_id, c)


def test_invalid_troop_admission_is_atomic():
    c, s, rt = setup(create_dan_yang_bing_runtime, TroopType.CAVALRY)
    assert admit_and_install_troop_skill(c, s, rt).status is TroopAdmissionStatus.REJECTED_INVALID_TROOP
    assert not c.metadata and not c.states.find(state_id=TEMPORARY_DAMAGE_POOL_STATE_ID)
    assert all(u.special_troop_id is None for u in c.units.values())
