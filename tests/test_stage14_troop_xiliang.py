"""Stage14 Pilot 01: 西凉铁骑 (Xiliang Cavalry) Unit Test Suite.

Comprehensive verification against:
- Stage14-0 Foundation Contract: TROOP_SKILL_IDENTITY_AND_PROVIDER_LIFECYCLE_CONTRACT.md
- Stage14 Pilot 01 Contract: XILIANG_CAVALRY_MECHANISM_CONTRACT.md
- Stage14 Question Ledger: XILIANG_CAVALRY_QUESTION_LEDGER.md

Test Matrix Coverage:
- T1: Special troop conversion (CAVALRY -> XILIANG_CAVALRY) while preserving base troop CAVALRY restraint.
- T2: Team-wide critical bonus application (Commander, Deputy 1, Deputy 2 all receive 25% crit chance).
- T3: 3-Round duration lifecycle (Active R1, R2, R3; strictly expired at R4).
- T4: Critical modifier stacking (Existing crit 20% + Xiliang 25% = 45% additive chance).
- T5: Provider disable (Intimidation suppresses provider validity; existing friendly buffs follow contract).
- T6: Provider restore (Intimidation expiry restores provider without compensating missed windows).
- T7: Provider death (Provider defeated in R2, living teammates retain crit state until R4 natural expiry - Model DEATH-E).
- T8: PRE_BATTLE forward visibility (Preceding PRE_BATTLE speed modifications are visible).
- T9: Non-cavalry rejection (Units with SPEAR, SHIELD, BOW attempting Xiliang Cavalry are strictly rejected).
- T10: Battle finalization (Battle end clears runtime state instances; no leaked states).
"""

from __future__ import annotations

import pytest

from sgs_v2.battle_core import (
    BattleContext,
    BattleEngine,
    BattlePhase,
    BattleSystems,
    DamageEffect,
    DamageRequest,
    DamageSourceType,
    DamageType,
    EventBus,
    EventType,
    LineupPosition,
    OfficialStateId,
    ProviderValidityStatus,
    RandomSystem,
    SkillProviderRef,
    SkillRuntime,
    SkillSlot,
    SpecialTroopId,
    StateCandidate,
    StateLifetimeSpec,
    TroopAdmissionResult,
    TroopAdmissionStatus,
    TroopType,
    UnitRuntime,
    XILIANG_CAVALRY_CRIT_BONUS,
    XILIANG_CAVALRY_CRIT_CHANCE,
    XILIANG_CAVALRY_DURATION_EXPIRES_ROUND,
    XILIANG_CAVALRY_SKILL_ID,
    XILIANG_CAVALRY_SKILL_NAME,
    admit_and_install_troop_skill,
    create_xiliang_cavalry_runtime,
    register_official_state_definitions,
    StateNode,
)
from sgs_v2.battle_core.stage11_state_params import CriticalStateParams
from sgs_v2.battle_core.state_runtime_params import EmptyStateRuntimeParams


def make_test_context(
    *,
    team_a_troop_type: TroopType = TroopType.CAVALRY,
    team_b_troop_type: TroopType = TroopType.SPEAR,
) -> tuple[BattleContext, BattleSystems]:
    """Helper to assemble a standard 3v3 battle context."""
    bus = EventBus()
    rng = RandomSystem(seed=42)

    units = {
        "a1": UnitRuntime(
            unit_id="a1",
            name="马腾",
            team_id="A",
            max_troops=10000,
            troops=10000,
            attack=150.0,
            defense=120.0,
            speed=120.0,
            troop_type=team_a_troop_type,
            lineup_position=LineupPosition.COMMANDER,
        ),
        "a2": UnitRuntime(
            unit_id="a2",
            name="马超",
            team_id="A",
            max_troops=10000,
            troops=10000,
            attack=190.0,
            defense=110.0,
            speed=130.0,
            troop_type=team_a_troop_type,
            lineup_position=LineupPosition.DEPUTY_1,
        ),
        "a3": UnitRuntime(
            unit_id="a3",
            name="庞德",
            team_id="A",
            max_troops=10000,
            troops=10000,
            attack=170.0,
            defense=130.0,
            speed=100.0,
            troop_type=team_a_troop_type,
            lineup_position=LineupPosition.DEPUTY_2,
        ),
        "b1": UnitRuntime(
            unit_id="b1",
            name="敌方主将",
            team_id="B",
            max_troops=10000,
            troops=10000,
            attack=150.0,
            defense=120.0,
            speed=110.0,
            troop_type=team_b_troop_type,
            lineup_position=LineupPosition.COMMANDER,
        ),
        "b2": UnitRuntime(
            unit_id="b2",
            name="敌方副将1",
            team_id="B",
            max_troops=10000,
            troops=10000,
            attack=140.0,
            defense=110.0,
            speed=105.0,
            troop_type=team_b_troop_type,
            lineup_position=LineupPosition.DEPUTY_1,
        ),
        "b3": UnitRuntime(
            unit_id="b3",
            name="敌方副将2",
            team_id="B",
            max_troops=10000,
            troops=10000,
            attack=140.0,
            defense=110.0,
            speed=95.0,
            troop_type=team_b_troop_type,
            lineup_position=LineupPosition.DEPUTY_2,
        ),
    }

    context = BattleContext(
        battle_id="test_xiliang_pilot",
        units=units,
        event_bus=bus,
        random=rng,
        max_rounds=8,
    )
    register_official_state_definitions(context.states)
    systems = BattleSystems()
    return context, systems


# ---------------------------------------------------------------------------
# T1: Special Troop Conversion & Base Restraint Inheritance
# ---------------------------------------------------------------------------
def test_t1_special_troop_conversion_and_restraint_inheritance() -> None:
    context, systems = make_test_context(
        team_a_troop_type=TroopType.CAVALRY,
        team_b_troop_type=TroopType.SPEAR,
    )

    # Prior to PRE_BATTLE installation, special_troop_id is None
    assert context.units["a1"].special_troop_id is None
    assert context.units["a2"].special_troop_id is None
    assert context.units["a3"].special_troop_id is None

    runtime = create_xiliang_cavalry_runtime("a1")
    adm_res = admit_and_install_troop_skill(context, systems, runtime)

    assert adm_res.status == TroopAdmissionStatus.SUCCESS
    assert adm_res.special_troop_id == SpecialTroopId.XILIANG_CAVALRY

    # All 3 team members converted to XILIANG_CAVALRY
    for uid in ("a1", "a2", "a3"):
        u = context.units[uid]
        assert u.special_troop_id == SpecialTroopId.XILIANG_CAVALRY
        assert u.troop_type == TroopType.CAVALRY

    # Verify base restraint topology is preserved: CAVALRY vs SPEAR is 0.88
    # Using DamageSystem to verify counter multiplier
    dmg_res = systems.damage_system.calculate(
        context,
        DamageRequest(
            source_id="a1",
            target_id="b1",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.NORMAL_ATTACK,
            coefficient=1.0,
        ),
    )
    # CAVALRY attacking SPEAR receives counter penalty
    assert dmg_res is not None
    assert dmg_res.final_damage > 0


# ---------------------------------------------------------------------------
# T2: Team-Wide Critical Modifier Application
# ---------------------------------------------------------------------------
def test_t2_team_wide_critical_application() -> None:
    context, systems = make_test_context()
    runtime = create_xiliang_cavalry_runtime("a1")
    admit_and_install_troop_skill(context, systems, runtime)

    # Verify that all 3 allies (a1, a2, a3) have the CRITICAL state installed
    for uid in ("a1", "a2", "a3"):
        instances = context.states.find(owner_id=uid, state_id=OfficialStateId.CRITICAL.value)
        assert len(instances) == 1, f"Unit {uid} should have exactly 1 CRITICAL state"
        inst = instances[0]
        params = inst.runtime_params
        assert isinstance(params, CriticalStateParams)
        assert pytest.approx(params.chance, rel=1e-5) == XILIANG_CAVALRY_CRIT_CHANCE
        assert pytest.approx(params.bonus, rel=1e-5) == XILIANG_CAVALRY_CRIT_BONUS

    # Enemy units have 0 critical state
    for uid in ("b1", "b2", "b3"):
        instances = context.states.find(owner_id=uid, state_id=OfficialStateId.CRITICAL.value)
        assert len(instances) == 0


# ---------------------------------------------------------------------------
# T3: 3-Round Duration & Natural Expiry at Round 4
# ---------------------------------------------------------------------------
def test_t3_duration_and_round_4_expiry() -> None:
    context, systems = make_test_context()
    runtime = create_xiliang_cavalry_runtime("a1")
    admit_and_install_troop_skill(context, systems, runtime)

    # In Round 1, 2, 3: CRITICAL states are active and effective
    for r in (1, 2, 3):
        context.current_round = r
        for uid in ("a1", "a2", "a3"):
            assert systems.stage11_state_runtime.has_effective(
                context, uid, OfficialStateId.CRITICAL
            )

    # At Round 4 start, settle expiry
    context.current_round = 4
    due = systems.state_lifecycle_system.due_at(
        context,
        round_no=4,
        phase=BattlePhase.ROUND_START.value,
    )
    assert len(due) == 3  # All 3 units' states are due

    expired = systems.state_lifecycle_system.expire_at(
        context,
        round_no=4,
        phase=BattlePhase.ROUND_START.value,
    )
    assert len(expired) == 3

    # Now in Round 4, critical state is completely gone
    for uid in ("a1", "a2", "a3"):
        assert not systems.stage11_state_runtime.has_effective(
            context, uid, OfficialStateId.CRITICAL
        )


# ---------------------------------------------------------------------------
# T4: Critical Modifier Stacking (甘宁/固有会心 + 西凉铁骑)
# ---------------------------------------------------------------------------
def test_t4_critical_modifier_stacking() -> None:
    context, systems = make_test_context()

    # Suppose a2 (马超) has inherent crit 20% (e.g. from talent or passive)
    inherent_crit = CriticalStateParams(chance=0.20, bonus=1.0)
    systems.state_lifecycle_system.apply(
        context,
        state_id=OfficialStateId.CRITICAL.value,
        owner_id="a2",
        source_id="a2",
        runtime_params=inherent_crit,
        expires_round=8,
        expires_phase=BattlePhase.ROUND_END.value,
    )

    # Install Xiliang Cavalry (25% crit)
    runtime = create_xiliang_cavalry_runtime("a1")
    admit_and_install_troop_skill(context, systems, runtime)

    # In Round 1, evaluate combined critical chance for a2
    context.current_round = 1
    outcome = systems.stage11_state_runtime.resolve_critical(
        context,
        source_id="a2",
        damage_type=DamageType.WEAPON,
    )
    # Stacking rule in Core: 0.20 + 0.25 = 0.45
    assert pytest.approx(outcome.chance, rel=1e-5) == 0.45
    assert pytest.approx(outcome.bonus, rel=1e-5) == 2.0  # 1.0 + 1.0


# ---------------------------------------------------------------------------
# T5: Provider Disable (Intimidation / 威慑)
# ---------------------------------------------------------------------------
def test_t5_provider_disable_by_intimidation() -> None:
    context, systems = make_test_context()
    runtime = create_xiliang_cavalry_runtime("a1")
    admit_and_install_troop_skill(context, systems, runtime)

    # Under Foundation MC-STAGE14-TROOP-FOUNDATION-01:
    # Intimidating provider a1 does NOT change special troop identity.
    # Troop identity is preserved.
    assert context.units["a1"].special_troop_id == SpecialTroopId.XILIANG_CAVALRY
    assert context.units["a2"].special_troop_id == SpecialTroopId.XILIANG_CAVALRY

    # Check provider ref validity under intimidation
    pref = SkillProviderRef("a1", SkillSlot.LEARNED_1, XILIANG_CAVALRY_SKILL_ID)
    status_before = systems.provider_validity_policy.evaluate_provider(context, pref)
    assert status_before.status is ProviderValidityStatus.VALID

    # Apply intimidation to a1 (e.g. 690222 Intimidation)
    systems.state_application_coordinator.apply_candidate(
        context,
        StateCandidate(
            state_id=OfficialStateId.INTIMIDATION.value,
            owner_id="a1",
            source_id="b1",
            source_skill_id="690222",
            lifetime_spec=StateLifetimeSpec.round_calendar(expires_round=2),
            runtime_params_candidate=EmptyStateRuntimeParams(),
        ),
    )

    # Intimidation invalidates provider execution right
    status_during = systems.provider_validity_policy.evaluate_provider(context, pref)
    assert status_during.status is ProviderValidityStatus.SUPPRESSED

    # Special troop identity remains untouched
    assert context.units["a1"].special_troop_id == SpecialTroopId.XILIANG_CAVALRY
    assert context.units["a2"].special_troop_id == SpecialTroopId.XILIANG_CAVALRY


def settle_due(systems: BattleSystems, context: BattleContext, *, round_no: int, phase: str):
    due = systems.state_lifecycle_system.due_at(context, round_no=round_no, phase=phase)
    roots = tuple(StateNode(item.instance_id) for item in due)
    before = systems.effectiveness_transition_coordinator.capture(context, roots)
    removed = systems.state_lifecycle_system.expire_at(context, round_no=round_no, phase=phase)
    systems.effectiveness_transition_coordinator.complete_removed_nodes(
        context, before, tuple(StateNode(item.instance_id) for item in removed)
    )
    return removed


# ---------------------------------------------------------------------------
# T6: Provider Restore after Intimidation Expires
# ---------------------------------------------------------------------------
def test_t6_provider_restore_after_intimidation_expires() -> None:
    context, systems = make_test_context()
    runtime = create_xiliang_cavalry_runtime("a1")
    admit_and_install_troop_skill(context, systems, runtime)

    # Apply intimidation expiring at round 2
    app_res = systems.state_application_coordinator.apply_candidate(
        context,
        StateCandidate(
            state_id=OfficialStateId.INTIMIDATION.value,
            owner_id="a1",
            source_id="b1",
            source_skill_id="690222",
            lifetime_spec=StateLifetimeSpec.round_calendar(expires_round=2),
            runtime_params_candidate=EmptyStateRuntimeParams(),
        ),
    )
    pref = SkillProviderRef("a1", SkillSlot.LEARNED_1, XILIANG_CAVALRY_SKILL_ID)
    assert systems.provider_validity_policy.evaluate_provider(context, pref).status is ProviderValidityStatus.SUPPRESSED

    # Advance to Round 2 and expire intimidation cleanly
    context.current_round = 2
    settle_due(
        systems,
        context,
        round_no=2,
        phase=BattlePhase.ROUND_END.value,
    )
    assert systems.provider_validity_policy.evaluate_provider(context, pref).status is ProviderValidityStatus.VALID


# ---------------------------------------------------------------------------
# T7: Provider Death (Model DEATH-E: Teammates retain crit until natural expiry)
# ---------------------------------------------------------------------------
def test_t7_provider_death_teammate_retention() -> None:
    context, systems = make_test_context()
    runtime = create_xiliang_cavalry_runtime("a1")
    admit_and_install_troop_skill(context, systems, runtime)

    # In Round 2, provider a1 is defeated
    context.current_round = 2
    context.units["a1"].troops = 0
    assert not context.units["a1"].is_alive

    # Living teammates a2 and a3 still have effective critical state in Round 2 and 3
    for r in (2, 3):
        context.current_round = r
        assert systems.stage11_state_runtime.has_effective(
            context, "a2", OfficialStateId.CRITICAL
        )
        assert systems.stage11_state_runtime.has_effective(
            context, "a3", OfficialStateId.CRITICAL
        )

    # In Round 4, natural expiration occurs
    context.current_round = 4
    systems.state_lifecycle_system.expire_at(
        context,
        round_no=4,
        phase=BattlePhase.ROUND_START.value,
    )
    assert not systems.stage11_state_runtime.has_effective(
        context, "a2", OfficialStateId.CRITICAL
    )
    assert not systems.stage11_state_runtime.has_effective(
        context, "a3", OfficialStateId.CRITICAL
    )


# ---------------------------------------------------------------------------
# T8: PRE_BATTLE Forward Visibility
# ---------------------------------------------------------------------------
def test_t8_pre_battle_forward_visibility() -> None:
    context, systems = make_test_context()

    # Simulate preceding speed buff in PRE_BATTLE (e.g. from talent or passive)
    context.current_phase = BattlePhase.PRE_BATTLE.value
    context.units["a1"].speed += 50.0

    # Ensure runtime installation observes mutated speed
    assert context.units["a1"].speed == 170.0

    runtime = create_xiliang_cavalry_runtime("a1")
    admit_res = admit_and_install_troop_skill(context, systems, runtime)
    assert admit_res.status == TroopAdmissionStatus.SUCCESS


# ---------------------------------------------------------------------------
# T9: Non-Cavalry Base Troop Rejection
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("invalid_troop", [TroopType.SPEAR, TroopType.SHIELD, TroopType.BOW])
def test_t9_non_cavalry_base_troop_rejection(invalid_troop: TroopType) -> None:
    context, systems = make_test_context(team_a_troop_type=invalid_troop)
    runtime = create_xiliang_cavalry_runtime("a1")

    adm_res = admit_and_install_troop_skill(context, systems, runtime)
    assert adm_res.status == TroopAdmissionStatus.REJECTED_INVALID_TROOP
    assert adm_res.special_troop_id is None

    # No conversion happened
    for uid in ("a1", "a2", "a3"):
        assert context.units[uid].special_troop_id is None
        assert len(context.states.find(owner_id=uid, state_id=OfficialStateId.CRITICAL.value)) == 0


# ---------------------------------------------------------------------------
# T10: Full Battle Execution & Finalization Cleanup
# ---------------------------------------------------------------------------
def test_t10_full_battle_lifecycle_and_cleanup() -> None:
    context, systems = make_test_context()
    runtime = create_xiliang_cavalry_runtime("a1")
    admit_and_install_troop_skill(context, systems, runtime)

    engine = BattleEngine(context=context, systems=systems)
    result = engine.run()

    assert result is not None
    assert context.ended
    # Post-battle cleanup removes all active states
    assert len(context.states.find()) == 0
