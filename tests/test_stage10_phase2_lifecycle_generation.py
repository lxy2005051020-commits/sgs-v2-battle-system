from __future__ import annotations

import pytest
from sgs_v2.battle_core.action_progress_tracker import ActionProgressTracker
from sgs_v2.battle_core.context import BattleContext
from sgs_v2.battle_core.defeat_cleanup_port import (
    DefeatCleanupPort,
    DefeatCleanupResult,
    DefeatRemovalReason,
)
from sgs_v2.battle_core.enums import BattlePhase, DamageType, LineupPosition
from sgs_v2.battle_core.events import EventBus, EventType
from sgs_v2.battle_core.official_state_catalog import (
    OfficialStateId,
    register_official_state_definitions,
)
from sgs_v2.battle_core.random_system import RandomSystem
from sgs_v2.battle_core.skill_definition import (
    DamageSkillEffectSpec,
    SkillDefinition,
    SkillTargetMode,
)
from sgs_v2.battle_core.skill_runtime import SkillRuntime, SkillSlot
from sgs_v2.battle_core.stage10_state_params import (
    ContinuousDamageStateParams,
    FirstAidStateParams,
    FrozenContinuousDamageBasis,
    RecoveryModelKind,
    RecoveryPotencyContext,
    RecuperationStateParams,
)
from sgs_v2.battle_core.state_generation import (
    PersistentLifecycleWindow,
    StateApplicationGenerationId,
    StateGenerationAllocator,
    StateGenerationSnapshot,
)
from sgs_v2.battle_core.state_instance import StateInstance
from sgs_v2.battle_core.state_lifecycle_system import StateLifecycleSystem
from sgs_v2.battle_core.unit import UnitRuntime


def make_test_unit(unit_id: str, team_id: str, position: LineupPosition, speed: int = 100) -> UnitRuntime:
    return UnitRuntime(
        unit_id=unit_id,
        name=f"Unit_{unit_id}",
        team_id=team_id,
        lineup_position=position,
        troops=10000,
        max_troops=10000,
        attack=100,
        defense=100,
        intelligence=100,
        speed=speed,
    )


def make_test_context() -> BattleContext:
    units = {
        "u1": make_test_unit("u1", "t1", LineupPosition.COMMANDER, speed=120),
        "u2": make_test_unit("u2", "t1", LineupPosition.DEPUTY_1, speed=100),
        "u3": make_test_unit("u3", "t2", LineupPosition.COMMANDER, speed=110),
        "u4": make_test_unit("u4", "t2", LineupPosition.DEPUTY_1, speed=90),
    }
    context = BattleContext(
        battle_id="test_lifecycle_battle",
        units=units,
        event_bus=EventBus(),
        random=RandomSystem(seed=42),
    )
    register_official_state_definitions(context.states)
    return context


class TestPreBattleLifecycleWindows:
    @pytest.mark.parametrize("duration,expected_last", [(1, 1), (2, 2), (3, 3), (4, 4)])
    def test_pre_battle_duration_calculation(self, duration: int, expected_last: int) -> None:
        lifecycle = StateLifecycleSystem()
        context = make_test_context()
        context.current_phase = BattlePhase.PRE_BATTLE.value
        context.current_round = 0

        window = lifecycle.calculate_lifecycle_window(
            context,
            owner_id="u3",
            duration_rounds=duration,
        )

        assert window.application_phase == BattlePhase.PRE_BATTLE.value
        assert window.application_round == 0
        assert window.first_eligible_round == 1
        assert window.last_eligible_round == expected_last
        assert window.max_opportunities_per_owner_round == 1
        assert window.is_round_eligible(1) is True
        if duration > 1:
            assert window.is_round_eligible(duration) is True
        assert window.is_round_eligible(duration + 1) is False

    def test_pre_battle_does_not_consume_opportunity(self) -> None:
        lifecycle = StateLifecycleSystem()
        context = make_test_context()
        context.current_phase = BattlePhase.PRE_BATTLE.value
        context.current_round = 0

        inst = lifecycle.apply(
            context,
            state_id=OfficialStateId.BURN.value,
            owner_id="u3",
            source_id="u1",
            duration_rounds=1,
        )

        assert inst.lifecycle_window is not None
        assert inst.lifecycle_window.first_eligible_round == 1
        assert inst.lifecycle_window.last_eligible_round == 1

        # In PRE_BATTLE, owner has not acted
        assert context.action_progress.has_acted_in_round("u3", 0) is False
        assert context.action_progress.has_acted_in_round("u3", 1) is False

        # Transition to Round 1 ActionStart
        context.current_round = 1
        context.current_phase = BattlePhase.UNIT_ACTION_START.value
        context.action_progress.set_current_acting_unit("u3")
        context.action_progress.mark_action_start("u3", 1)

        # Round 1 ActionStart is eligible!
        assert lifecycle.is_generation_eligible_at_action_start(context, inst) is True

        # Post ActionStart expiry
        expired = lifecycle.expire_eligible_states(context, "u3")
        assert len(expired) == 1
        assert expired[0].instance_id == inst.instance_id
        assert inst.instance_id not in context.states


class TestCombatRoundLifecycleWindows:
    def test_applied_before_owner_acts_same_round_eligible(self) -> None:
        lifecycle = StateLifecycleSystem()
        context = make_test_context()
        context.current_round = 2
        context.current_phase = BattlePhase.ROUND_START.value

        # u3 has not acted in Round 2
        assert context.action_progress.has_acted_in_round("u3", 2) is False

        inst = lifecycle.apply(
            context,
            state_id=OfficialStateId.POISON.value,
            owner_id="u3",
            source_id="u1",
            duration_rounds=2,
        )

        assert inst.lifecycle_window is not None
        assert inst.lifecycle_window.first_eligible_round == 2
        assert inst.lifecycle_window.last_eligible_round == 3

        # Enter u3 ActionStart in Round 2
        context.current_phase = BattlePhase.UNIT_ACTION_START.value
        context.action_progress.set_current_acting_unit("u3")
        context.action_progress.mark_action_start("u3", 2)

        # Round 2 is eligible
        assert lifecycle.is_generation_eligible_at_action_start(context, inst) is True

        # Post ActionStart R2: should NOT expire yet (last is 3)
        expired_r2 = lifecycle.expire_eligible_states(context, "u3")
        assert len(expired_r2) == 0
        assert inst.instance_id in context.states

    def test_applied_after_owner_acts_deferred_to_next_round(self) -> None:
        lifecycle = StateLifecycleSystem()
        context = make_test_context()
        context.current_round = 2
        context.current_phase = BattlePhase.UNIT_ACTION.value

        # u3 already acted in Round 2
        context.action_progress.mark_action_start("u3", 2)
        assert context.action_progress.has_acted_in_round("u3", 2) is True

        # Now apply state to u3 (e.g. from an attack by u1)
        inst = lifecycle.apply(
            context,
            state_id=OfficialStateId.ROUT.value,
            owner_id="u3",
            source_id="u1",
            duration_rounds=2,
        )

        assert inst.lifecycle_window is not None
        assert inst.lifecycle_window.first_eligible_round == 3
        assert inst.lifecycle_window.last_eligible_round == 4
        # Round 2 is NOT eligible (no catch-up!)
        assert inst.lifecycle_window.is_round_eligible(2) is False
        assert inst.lifecycle_window.is_round_eligible(3) is True


class TestActionProgressTrackerInvariants:
    def test_single_action_start_opportunity_per_owner_per_round(self) -> None:
        tracker = ActionProgressTracker()
        assert tracker.has_consumed_action_start("u1", 1) is False

        # First mark
        first_mark = tracker.mark_action_start("u1", 1)
        assert first_mark is True
        assert tracker.has_consumed_action_start("u1", 1) is True
        assert tracker.is_action_start_opportunity_eligible("u1", 1) is True

        # Second mark (e.g. extra action in same round)
        second_mark = tracker.mark_action_start("u1", 1)
        assert second_mark is False
        # Invariant: persistent opportunity is NO LONGER eligible
        assert tracker.is_action_start_opportunity_eligible("u1", 1) is False

    def test_second_action_start_lifecycle_ineligibility(self) -> None:
        lifecycle = StateLifecycleSystem()
        context = make_test_context()
        context.current_round = 1
        context.current_phase = BattlePhase.PRE_BATTLE.value

        inst = lifecycle.apply(
            context,
            state_id=OfficialStateId.RECUPERATION.value,
            owner_id="u1",
            duration_rounds=2,
        )

        # First ActionStart
        context.current_phase = BattlePhase.UNIT_ACTION_START.value
        context.action_progress.set_current_acting_unit("u1")
        context.action_progress.mark_action_start("u1", 1)
        assert lifecycle.is_generation_eligible_at_action_start(context, inst) is True

        # Second ActionStart in same round
        context.action_progress.mark_action_start("u1", 1)
        assert lifecycle.is_generation_eligible_at_action_start(context, inst) is False


class TestRefreshAndGenerations:
    def test_initial_application_allocates_generation_and_retains_different_id(self) -> None:
        lifecycle = StateLifecycleSystem()
        context = make_test_context()
        context.current_round = 1
        context.current_phase = BattlePhase.ROUND_START.value

        inst = lifecycle.apply(
            context,
            state_id=OfficialStateId.BURN.value,
            owner_id="u2",
            source_id="u1",
            duration_rounds=2,
        )

        assert inst.instance_id.startswith("state-")
        assert isinstance(inst.current_generation_id, StateApplicationGenerationId)
        # Invariant: physical instance_id != generation_id
        assert inst.instance_id != str(inst.current_generation_id)
        assert inst.lifecycle_window is not None
        assert inst.lifecycle_window.first_eligible_round == 1
        assert inst.lifecycle_window.last_eligible_round == 2

    def test_refresh_retains_physical_instance_and_allocates_new_generation(self) -> None:
        lifecycle = StateLifecycleSystem()
        context = make_test_context()
        context.current_round = 1
        context.current_phase = BattlePhase.ROUND_START.value

        inst1 = lifecycle.apply(
            context,
            state_id=OfficialStateId.BURN.value,
            owner_id="u2",
            source_id="u1",
            duration_rounds=2,
        )
        original_inst_id = inst1.instance_id
        g1_id = inst1.current_generation_id

        # Same state applied again on same owner -> triggers refresh
        inst2 = lifecycle.apply(
            context,
            state_id=OfficialStateId.BURN.value,
            owner_id="u2",
            source_id="u3",
            duration_rounds=3,
        )

        # Invariant: physical instance ID retained
        assert inst2.instance_id == original_inst_id
        # Invariant: exactly 1 effective BURN state on u2
        matching = context.states.find(owner_id="u2", state_id=OfficialStateId.BURN.value)
        assert len(matching) == 1
        assert matching[0].instance_id == original_inst_id

        # Invariant: new generation ID allocated
        assert inst2.current_generation_id != g1_id
        assert isinstance(inst2.current_generation_id, StateApplicationGenerationId)

        # Invariant: provenance replaced
        assert inst2.source_id == "u3"
        assert inst2.lifecycle_window is not None
        assert inst2.lifecycle_window.first_eligible_round == 1
        assert inst2.lifecycle_window.last_eligible_round == 3

    def test_refresh_observation_event_payload(self) -> None:
        lifecycle = StateLifecycleSystem()
        context = make_test_context()
        context.current_round = 1
        context.current_phase = BattlePhase.ROUND_START.value

        inst1 = lifecycle.apply(
            context,
            state_id=OfficialStateId.POISON.value,
            owner_id="u2",
            source_id="u1",
            duration_rounds=1,
        )
        g1_id = inst1.current_generation_id

        inst2 = lifecycle.refresh(
            context,
            instance_id=inst1.instance_id,
            source_id="u4",
            duration_rounds=2,
        )

        # Verify STATE_REFRESHED event
        refresh_events = [e for e in context.event_bus.history if e.event_type == EventType.STATE_REFRESHED]
        assert len(refresh_events) == 1
        ev = refresh_events[0]
        assert ev.payload["physical_instance_id"] == inst1.instance_id
        assert ev.payload["state_id"] == OfficialStateId.POISON.value
        assert ev.payload["owner_id"] == "u2"
        assert ev.payload["old_application_generation_id"] == str(g1_id)
        assert ev.payload["new_application_generation_id"] == str(inst2.current_generation_id)
        assert ev.payload["old_source_id"] == "u1"
        assert ev.payload["new_source_id"] == "u4"
        assert ev.payload["old_last_eligible_round"] == 1
        assert ev.payload["new_last_eligible_round"] == 2

    def test_old_snapshot_immutability_on_refresh(self) -> None:
        lifecycle = StateLifecycleSystem()
        context = make_test_context()
        context.current_round = 1
        context.current_phase = BattlePhase.ROUND_START.value

        basis = FrozenContinuousDamageBasis(
            application_generation_id=StateApplicationGenerationId("temp_placeholder"),
            source_unit_id="u1",
            damage_type=DamageType.STRATEGY,
            coefficient=1.5,
        )
        params = ContinuousDamageStateParams(frozen_damage_basis=basis)

        inst1 = lifecycle.apply(
            context,
            state_id=OfficialStateId.BURN.value,
            owner_id="u2",
            source_id="u1",
            duration_rounds=2,
            runtime_params=params,
        )
        g1_id = inst1.current_generation_id
        snapshot_g1 = inst1.create_generation_snapshot()

        assert snapshot_g1.application_generation_id == g1_id
        assert snapshot_g1.source_id == "u1"
        assert snapshot_g1.frozen_damage_basis is not None
        assert snapshot_g1.frozen_damage_basis.application_generation_id == g1_id

        # Refresh to G2
        inst2 = lifecycle.refresh(
            context,
            instance_id=inst1.instance_id,
            source_id="u3",
            duration_rounds=3,
        )
        g2_id = inst2.current_generation_id
        assert g2_id != g1_id

        # Invariant: snapshot_g1 is 100% immutable and preserves G1 facts
        assert snapshot_g1.application_generation_id == g1_id
        assert snapshot_g1.source_id == "u1"
        assert snapshot_g1.lifecycle_window.last_eligible_round == 2
        assert snapshot_g1.frozen_damage_basis.application_generation_id == g1_id


class TestStateCoexistenceAndUniqueness:
    def test_one_effective_slot_per_owner_for_same_state(self) -> None:
        lifecycle = StateLifecycleSystem()
        context = make_test_context()
        context.current_round = 1
        context.current_phase = BattlePhase.ROUND_START.value

        # Apply BURN 3 times from different sources
        inst_a = lifecycle.apply(context, state_id=OfficialStateId.BURN.value, owner_id="u2", source_id="u1", duration_rounds=2)
        inst_b = lifecycle.apply(context, state_id=OfficialStateId.BURN.value, owner_id="u2", source_id="u3", duration_rounds=2)
        inst_c = lifecycle.apply(context, state_id=OfficialStateId.BURN.value, owner_id="u2", source_id="u4", duration_rounds=2)

        # All 3 refreshes maintain the exact same physical instance
        assert inst_a.instance_id == inst_b.instance_id == inst_c.instance_id
        matching = context.states.find(owner_id="u2", state_id=OfficialStateId.BURN.value)
        assert len(matching) == 1

    def test_different_persistent_states_coexist(self) -> None:
        lifecycle = StateLifecycleSystem()
        context = make_test_context()
        context.current_round = 1
        context.current_phase = BattlePhase.ROUND_START.value

        inst_burn = lifecycle.apply(context, state_id=OfficialStateId.BURN.value, owner_id="u2", source_id="u1", duration_rounds=2)
        inst_poison = lifecycle.apply(context, state_id=OfficialStateId.POISON.value, owner_id="u2", source_id="u1", duration_rounds=2)
        inst_aid = lifecycle.apply(
            context,
            state_id=OfficialStateId.FIRST_AID.value,
            owner_id="u2",
            source_id="u3",
            duration_rounds=2,
            runtime_params=FirstAidStateParams(probability=0.8, recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT),
        )

        assert inst_burn.instance_id != inst_poison.instance_id != inst_aid.instance_id
        all_u2_states = context.states.find(owner_id="u2")
        assert len(all_u2_states) == 3


class TestStaleExpirationProtection:
    def test_stale_g1_cleanup_does_not_delete_refreshed_g2(self) -> None:
        lifecycle = StateLifecycleSystem()
        context = make_test_context()
        context.current_round = 1
        context.current_phase = BattlePhase.ROUND_START.value

        inst1 = lifecycle.apply(
            context,
            state_id=OfficialStateId.FLOOD.value,
            owner_id="u2",
            source_id="u1",
            duration_rounds=1,
        )
        g1_id = inst1.current_generation_id
        inst_id = inst1.instance_id

        # At Round 1 ActionStart checkpoint, suppose an effect refreshes same state to G2
        inst2 = lifecycle.refresh(
            context,
            instance_id=inst_id,
            source_id="u3",
            duration_rounds=2,
        )
        g2_id = inst2.current_generation_id
        assert g2_id != g1_id

        # Now an old scheduled G1 expiration check executes:
        result = lifecycle.expire_if_current_generation(context, inst_id, generation_id=g1_id)
        assert result is None  # Protected! Did not remove!

        # State G2 remains active in registry!
        assert inst_id in context.states
        surviving = context.states.get(inst_id)
        assert surviving.current_generation_id == g2_id


class TestOwnerDeathAndSourceDeath:
    def test_owner_death_removes_all_attached_states(self) -> None:
        lifecycle = StateLifecycleSystem()
        context = make_test_context()
        context.current_round = 1
        context.current_phase = BattlePhase.ROUND_START.value

        inst1 = lifecycle.apply(context, state_id=OfficialStateId.BURN.value, owner_id="u2", source_id="u1", duration_rounds=2)
        inst2 = lifecycle.apply(context, state_id=OfficialStateId.POISON.value, owner_id="u2", source_id="u3", duration_rounds=2)

        # Other unit state
        inst3 = lifecycle.apply(context, state_id=OfficialStateId.ROUT.value, owner_id="u3", source_id="u2", duration_rounds=2)

        removed = lifecycle.clear_owner_on_defeat(context, "u2")
        assert len(removed) == 2
        removed_ids = {r.instance_id for r in removed}
        assert removed_ids == {inst1.instance_id, inst2.instance_id}

        # u2 has no states left
        assert len(context.states.find(owner_id="u2")) == 0
        # u3 still has their state intact!
        assert inst3.instance_id in context.states

        # Events emitted with OWNER_DEFEATED
        removed_events = [e for e in context.event_bus.history if e.event_type == EventType.STATE_REMOVED]
        assert len(removed_events) == 2
        for ev in removed_events:
            assert ev.payload["removal_reason"] == DefeatRemovalReason.OWNER_DEFEATED.value

    def test_source_death_does_not_remove_target_states(self) -> None:
        lifecycle = StateLifecycleSystem()
        context = make_test_context()
        context.current_round = 1
        context.current_phase = BattlePhase.ROUND_START.value

        # Source u1 applies state to target u3
        inst = lifecycle.apply(context, state_id=OfficialStateId.BURN.value, owner_id="u3", source_id="u1", duration_rounds=2)

        # Source u1 dies and is cleaned up
        lifecycle.clear_owner_on_defeat(context, "u1")

        # Target u3 persistent state STILL EXISTS!
        assert inst.instance_id in context.states
        assert context.states.get(inst.instance_id).source_id == "u1"

    def test_source_death_does_not_remove_skill_runtimes(self) -> None:
        context = make_test_context()
        def_skill = SkillDefinition(
            skill_id="skill_fire",
            name="Fire",
            activation_rate=1.0,
            target_mode=SkillTargetMode.SINGLE_RANDOM_ENEMY,
            effect_specs=(DamageSkillEffectSpec(DamageType.WEAPON, 1.0),),
        )
        sk = SkillRuntime(definition=def_skill, owner_id="u1", skill_slot=SkillSlot.INHERENT, enabled=True)
        context.skill_runtimes.register(sk)

        lifecycle = StateLifecycleSystem()
        # u1 dies
        lifecycle.clear_owner_on_defeat(context, "u1")

        # SkillRuntime remains registered!
        lookup = context.skill_runtimes.lookup("u1", SkillSlot.INHERENT)
        assert lookup is not None
        assert lookup.definition.skill_id == "skill_fire"


class TestDefeatCleanupPort:
    def test_commit_defeat_cleanses_states_and_returns_typed_result(self) -> None:
        lifecycle = StateLifecycleSystem()
        context = make_test_context()
        context.current_round = 3
        context.current_phase = BattlePhase.UNIT_ACTION.value

        lifecycle.apply(context, state_id=OfficialStateId.BURN.value, owner_id="u2", source_id="u1", duration_rounds=2)
        lifecycle.apply(context, state_id=OfficialStateId.POISON.value, owner_id="u2", source_id="u3", duration_rounds=2)

        port = DefeatCleanupPort(lifecycle)
        res = port.commit_defeat(context, defeated_unit_id="u2", defeat_source_ref="normal_attack_123")

        assert isinstance(res, DefeatCleanupResult)
        assert res.defeated_unit_id == "u2"
        assert res.defeat_source_ref == "normal_attack_123"
        assert len(res.removed_states) == 2
        assert res.round_no == 3
        assert res.phase == BattlePhase.UNIT_ACTION.value
        assert len(context.states.find(owner_id="u2")) == 0