"""User-specified actual recovery / 10 final addition, through real owners."""
import pytest

from tests.test_stage14_troop_batch01 import setup
from sgs_v2.battle_core import (
    BattleEngine, BattleSystems, EventType, ProviderNode, SkillRuntime, SkillSlot, StateNode,
    TroopType, TroopAdmissionStatus, admit_and_install_troop_skill,
    create_fei_xiong_jun_runtime,
)
from sgs_v2.battle_core.provider_identity import SkillProviderRef
from sgs_v2.battle_core.received_recovery_modifier import (
    RECEIVED_RECOVERY_BONUS_STATE_ID, ReceivedRecoveryBonusParams, ReceivedRecoveryModifierProvider,
)
from sgs_v2.battle_core.recovery_system import (
    RecoveryRequest, RecoveryModifierPolicy, RecoveryModifierContribution,
)
from sgs_v2.battle_core.stage9_integerization import ExactRatio
from sgs_v2.battle_core.state_modifiers import register_modifier_state_definitions
from sgs_v2.battle_core.troop_skills.fei_xiong_jun import (
    CONFIG, SKILL, resolve_recovery_definition, FEI_XIONG_ACTUAL_RECOVERY_DAMAGE_RATIO,
)


def preview(*, commander='a1', holder='a2', systems=None):
    """Isolated effect execution, explicitly not production troop admission."""
    c, s, _ = setup(create_fei_xiong_jun_runtime, TroopType.CAVALRY, systems=systems)
    c.units['a1'].name = commander
    rt = create_fei_xiong_jun_runtime(holder)
    c.skill_runtimes.register(rt)
    register_modifier_state_definitions(c.states)
    definition = resolve_recovery_definition(c, s, c.units[holder])
    effective = SkillRuntime(definition, holder, rt.skill_slot)
    resolution = s.skill_resolver.resolve(c, effective)
    ref = SkillProviderRef(holder, rt.skill_slot, SKILL.skill_id)
    for effect in resolution.effects:
        result = s.effect_executor.execute(c, effect)
        if result.state_instance is not None:
            s.dependency_evaluation_support.add_dependency(StateNode(result.state_instance.instance_id), ProviderNode(ref))
    for u in c.units.values():
        u.troops, u.wounded_troops = 5000, 5000
    return c, s, rt


def heal(c, s, *, target='a3', source='a1', amount=100, policy=RecoveryModifierPolicy.APPLY):
    return s.recovery_system.resolve(c, RecoveryRequest(source, target, amount, modifier_policy=policy))


@pytest.mark.parametrize('commander,holder,expected', [
    ('a1', 'a2', 116), ('董卓', 'a2', 120), ('a1', 'a1', 116),
])
def test_known_full_level_received_recovery_team_and_commander(commander, holder, expected):
    c, s, rt = preview(commander=commander, holder=holder)
    for uid in ('a1', 'a2', 'a3'):
        result = heal(c, s, target=uid)
        assert result.actual_recovery == expected
        assert c.units[uid].troops == 5000 + expected
        state = c.states.find(owner_id=uid, state_id=RECEIVED_RECOVERY_BONUS_STATE_ID)[0]
        assert state.source_id == holder and state.source_skill_slot == rt.skill_slot
        assert state.expires_round is None
    assert heal(c, s, target='b1').actual_recovery == 100
    assert not c.random.probabilities


def test_dong_zhuo_holder_is_not_commander_bonus():
    c, s, rt = preview()
    c.units[rt.owner_id].name = '董卓'
    assert heal(c, s).actual_recovery == 116


def test_received_bonus_follows_target_not_healer():
    c, s, _ = preview()
    assert heal(c, s, source='b1').actual_recovery == 116
    assert heal(c, s, target='b1', source='a3').actual_recovery == 100


@pytest.mark.parametrize('amount,expected', [(0, 0), (1, 2), (7, 9), (25, 29)])
def test_exact_ratio_second_ceil(amount, expected):
    c, s, _ = preview()
    assert heal(c, s, amount=amount).actual_recovery == expected


def test_explicit_modifier_bypass_and_capacity_stay_recovery_owner():
    c, s, _ = preview()
    assert heal(c, s, policy=RecoveryModifierPolicy.NONE).actual_recovery == 100
    c.units['a3'].troops, c.units['a3'].wounded_troops = 9990, 10
    result = heal(c, s)
    assert result.modified_recovery == 116 and result.actual_recovery == 10


def test_baseline_runtime_toggle_does_not_remove_an_installed_persistent_modifier():
    c, s, rt = preview()
    rt.enabled = False
    # Same persistent-state semantics as existing typed attribute modifiers.
    assert heal(c, s).actual_recovery == 116
    rt.enabled = True
    assert heal(c, s).actual_recovery == 116


def test_existing_final_modifier_ratio_is_preserved_and_bonus_adds_once():
    c, s, _ = preview(systems=BattleSystems(recovery_modifier_provider=lambda c, r: ExactRatio(6, 5)))
    assert heal(c, s).actual_recovery == 136
    assert heal(c, s, target='b1').actual_recovery == 120


def test_no_state_preserves_equipment_contribution_identity():
    c, s, _ = setup(create_fei_xiong_jun_runtime, TroopType.CAVALRY)
    base = RecoveryModifierContribution(ExactRatio(6, 5))
    provider = ReceivedRecoveryModifierProvider(s.state_effectiveness_policy, lambda c, r: base)
    assert provider(c, RecoveryRequest('a1', 'b1', 100)) is base


def test_equipment_gate_is_independent_of_received_bonus():
    from sgs_v2.battle_core.provider_identity import EquipmentProviderRef
    from sgs_v2.battle_core.equipment_effectiveness import EquipmentContributionRef, EquipmentContributionKind
    ref = EquipmentContributionRef(EquipmentProviderRef('a3', 'prayer'), 'recovery',
                                  EquipmentContributionKind.RECOVERY_MODIFIER)
    systems = BattleSystems(recovery_modifier_provider=lambda c, r:
                            RecoveryModifierContribution(ExactRatio(6, 5), ref))
    c, s, _ = preview(systems=systems)
    # Missing equipment is ineffective, but must leave the independent +16%.
    assert heal(c, s).actual_recovery == 116
    s.equipment_contribution_registry.register_provider(ref.provider_ref)
    s.equipment_contribution_registry.register_contribution(ref)
    assert heal(c, s).actual_recovery == 136


def test_equipment_owned_modifier_with_no_policy_raises_even_with_state_bonus():
    from sgs_v2.battle_core.provider_identity import EquipmentProviderRef
    from sgs_v2.battle_core.equipment_effectiveness import EquipmentContributionRef, EquipmentContributionKind
    c, s, _ = preview()
    ref = EquipmentContributionRef(EquipmentProviderRef('a3', 'prayer'), 'recovery',
                                  EquipmentContributionKind.RECOVERY_MODIFIER)
    provider = ReceivedRecoveryModifierProvider(s.state_effectiveness_policy,
        lambda c, r: RecoveryModifierContribution(ExactRatio(6, 5), ref))
    with pytest.raises(RuntimeError, match='no effectiveness policy'):
        provider(c, RecoveryRequest('a1', 'a3', 100))


def test_state_effectiveness_gate_suppresses_without_changing_physical_state():
    from sgs_v2.battle_core.state_effectiveness import (
        StateEffectivenessContribution, SuppressionCause, LocalRuleCauseRef,
    )
    c, s, _ = preview()
    suppressed = [True]
    def gate(context, instance, session):
        if suppressed[0] and instance.state_id == RECEIVED_RECOVERY_BONUS_STATE_ID:
            return StateEffectivenessContribution(suppression_causes=(
                SuppressionCause('test_gate', LocalRuleCauseRef('test')),))
        return StateEffectivenessContribution()
    s.state_effectiveness_policy.register_rule_adapter(gate)
    assert heal(c, s).actual_recovery == 100
    assert len(c.states.find(state_id=RECEIVED_RECOVERY_BONUS_STATE_ID)) == 3
    suppressed[0] = False
    assert heal(c, s).actual_recovery == 116


def test_duplicate_source_is_rejected_distinct_source_adds_and_removal_clears():
    from sgs_v2.battle_core import StateCandidate
    from sgs_v2.battle_core.state_application import StateApplicationResultStatus
    c, s, rt = preview()
    duplicate = StateCandidate(RECEIVED_RECOVERY_BONUS_STATE_ID, 'a3',
        ReceivedRecoveryBonusParams(ExactRatio(16, 100)), rt.owner_id, '20247', rt.skill_slot)
    assert s.state_application_coordinator.apply_candidate(c, duplicate).status is StateApplicationResultStatus.REJECTED_CONFLICT
    extra = StateCandidate(RECEIVED_RECOVERY_BONUS_STATE_ID, 'a3',
        ReceivedRecoveryBonusParams(ExactRatio(1, 10)), 'a1', 'generic_bonus', SkillSlot.LEARNED_2)
    s.state_application_coordinator.apply_candidate(c, extra)
    assert heal(c, s).actual_recovery == 126
    for state in tuple(c.states.find(owner_id='a3', state_id=RECEIVED_RECOVERY_BONUS_STATE_ID)):
        s.state_lifecycle_system.remove(c, state.instance_id)
    assert heal(c, s).actual_recovery == 100


def test_healing_ban_remains_authoritative_after_modifier():
    from sgs_v2.battle_core import StateCandidate, OfficialStateId
    from sgs_v2.battle_core.stage11_state_params import Stage11TimedFlagParams
    c, s, _ = preview()
    s.state_application_coordinator.apply_candidate(c, StateCandidate(
        OfficialStateId.HEALING_BAN.value, 'a3', Stage11TimedFlagParams()))
    result = heal(c, s)
    assert result.reason.value == 'HEALING_BAN' and c.units['a3'].troops == 5000


def test_missing_commander_cannot_assume_default_recovery_bonus():
    c, s, rt = setup(create_fei_xiong_jun_runtime, TroopType.CAVALRY)
    del c.units['a1']
    with pytest.raises(ValueError, match='commander'):
        resolve_recovery_definition(c, s, c.units['a2'])


@pytest.mark.parametrize('rate,error', [(True, TypeError), (.16, TypeError), (ExactRatio(-1, 10), ValueError)])
def test_generic_bonus_validation(rate, error):
    with pytest.raises(error):
        ReceivedRecoveryBonusParams(rate)


def test_registry_is_real_project_registry_and_model_is_user_specified():
    from sgs_v2.battle_core.troop_admission import TROOP_SKILL_REGISTRY
    assert TROOP_SKILL_REGISTRY['20247'] is CONFIG
    assert CONFIG.definition_factory() == SKILL
    assert CONFIG.required_troop_type is TroopType.CAVALRY
    assert FEI_XIONG_ACTUAL_RECOVERY_DAMAGE_RATIO == ExactRatio(1, 10)


def test_default_admission_installs_conversion_recovery_and_commander_trigger():
    from sgs_v2.battle_core.action_start_recovery_damage import ACTION_START_RECOVERY_DAMAGE_STATE_ID
    c, s, rt = setup(create_fei_xiong_jun_runtime, TroopType.CAVALRY)
    assert admit_and_install_troop_skill(c, s, rt).status is TroopAdmissionStatus.SUCCESS
    assert all(c.units[uid].special_troop_id.value == 'FEI_XIONG_JUN' for uid in ('a1', 'a2', 'a3'))
    assert len(c.states.find(state_id=RECEIVED_RECOVERY_BONUS_STATE_ID)) == 3
    states = c.states.find(state_id=ACTION_START_RECOVERY_DAMAGE_STATE_ID)
    assert len(states) == 1 and states[0].owner_id == 'a1'
    assert not c.random.probabilities


def test_engine_registered_runtime_runs_and_emits_user_model_marker():
    c, s, rt = setup(create_fei_xiong_jun_runtime, TroopType.CAVALRY)
    for u in c.units.values():
        u.intelligence = 200
    c.skill_runtimes.register(rt)
    result = BattleEngine(c, s).run()
    assert c.ended and c.result is result
    snapshots = [e for e in c.event_bus.history if e.payload.get('event_kind') == 'ACCUMULATED_RECOVERY_SNAPSHOT']
    assert snapshots and all('USER' in e.payload['basis_model_key'] for e in snapshots)
    assert all(e.actor_id == 'a1' and e.payload['coefficient'] == .64 for e in snapshots)


@pytest.mark.parametrize('failure,expected', [
    ('disabled', TroopAdmissionStatus.REJECTED_BASELINE_DISABLED),
    ('wrong_troop', TroopAdmissionStatus.REJECTED_INVALID_TROOP),
    ('mixed', TroopAdmissionStatus.REJECTED_TEAM_INVARIANT_VIOLATION),
    ('no_slot', TroopAdmissionStatus.REJECTED_PROVIDER_SLOT_CONFLICT),
])
def test_shared_preflight_still_owns_invalid_loadouts(failure, expected):
    c, s, rt = setup(create_fei_xiong_jun_runtime, TroopType.CAVALRY)
    if failure == 'disabled':
        rt.enabled = False
    elif failure == 'wrong_troop':
        c.units['a1'].troop_type = TroopType.SPEAR
    elif failure == 'mixed':
        c.units['a3'].troop_type = TroopType.SPEAR
    else:
        rt.skill_slot = None
    assert admit_and_install_troop_skill(c, s, rt).status is expected
    assert all(u.special_troop_id is None for u in c.units.values())
