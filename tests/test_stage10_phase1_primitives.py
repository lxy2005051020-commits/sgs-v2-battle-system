from __future__ import annotations

from dataclasses import FrozenInstanceError
import pytest

from sgs_v2.battle_core.action_progress_tracker import ActionProgressTracker
from sgs_v2.battle_core.context import BattleContext
from sgs_v2.battle_core.effects import DamageEffect, EffectSourceRef
from sgs_v2.battle_core.enums import DamageSourceType, DamageType, LineupPosition
from sgs_v2.battle_core.events import EventBus
from sgs_v2.battle_core.official_state_catalog import (
    OfficialStateId,
    STAGE10_PERSISTENT_STATE_IDS,
    get_stage10_persistent_params_type,
)
from sgs_v2.battle_core.operation_identity import SourceType
from sgs_v2.battle_core.random_system import RandomSystem
from sgs_v2.battle_core.rule_intent import (
    AbortedRuleIntentResult,
    ExecutionRightDecisionKind,
    ExecutionRightReason,
    RecoveryOpportunity,
    RecoveryOpportunityKind,
    RecoveryOpportunityResult,
    RuleIntentExecutionDescriptor,
    RuleIntentKind,
)
from sgs_v2.battle_core.skill_definition import (
    DamageSkillEffectSpec,
    SkillDefinition,
    SkillTargetMode,
)
from sgs_v2.battle_core.skill_runtime import SkillRuntime, SkillSlot
from sgs_v2.battle_core.skill_runtime_registry import (
    PersistentSourceSkillGate,
    PersistentSourceSkillGateMode,
    SkillRuntimeRegistry,
)
from sgs_v2.battle_core.stage10_state_params import (
    ContinuousDamageStateParams,
    FirstAidStateParams,
    FrozenContinuousDamageBasis,
    RecuperationStateParams,
    RecoveryModelKind,
    RecoveryPotencyContext,
)
from sgs_v2.battle_core.state_generation import (
    PersistentLifecycleWindow,
    StateApplicationGenerationId,
    StateGenerationAllocator,
    StateGenerationSnapshot,
)
from sgs_v2.battle_core.state_instance import StateInstance
from sgs_v2.battle_core.state_runtime_params import (
    validate_state_runtime_params,
    validate_state_runtime_params_type,
)
from sgs_v2.battle_core.unit import UnitRuntime


def _make_dummy_context() -> BattleContext:
    u1 = UnitRuntime(
        unit_id="u1",
        name="Unit 1",
        team_id="team_a",
        max_troops=10000,
        troops=10000,
        attack=100.0,
        defense=100.0,
        speed=100.0,
        lineup_position=LineupPosition.COMMANDER,
    )
    u2 = UnitRuntime(
        unit_id="u2",
        name="Unit 2",
        team_id="team_b",
        max_troops=10000,
        troops=10000,
        attack=100.0,
        defense=100.0,
        speed=100.0,
        lineup_position=LineupPosition.COMMANDER,
    )
    return BattleContext(
        battle_id="b_test",
        units={"u1": u1, "u2": u2},
        event_bus=EventBus(),
        random=RandomSystem(42),
    )


class TestStateApplicationGenerationId:
    def test_identity_and_semantic_domain(self) -> None:
        gen1 = StateApplicationGenerationId("gen_1")
        gen2 = StateApplicationGenerationId("gen_2")
        gen1_dup = StateApplicationGenerationId("gen_1")

        assert str(gen1) == "gen_1"
        assert gen1 == gen1_dup
        assert gen1 != gen2
        assert hash(gen1) == hash(gen1_dup)

        # Semantic domain isolation: instance_id string != StateApplicationGenerationId
        assert "gen_1" != gen1
        assert type(gen1) is StateApplicationGenerationId

    def test_ordering_forbidden(self) -> None:
        g1 = StateApplicationGenerationId("gen_1")
        g2 = StateApplicationGenerationId("gen_2")

        with pytest.raises(TypeError, match="does not support comparison operator"):
            _ = g1 < g2
        with pytest.raises(TypeError, match="does not support comparison operator"):
            _ = g1 <= g2
        with pytest.raises(TypeError, match="does not support comparison operator"):
            _ = g1 > g2
        with pytest.raises(TypeError, match="does not support comparison operator"):
            _ = g1 >= g2

    def test_empty_or_invalid_value_rejected(self) -> None:
        with pytest.raises(TypeError, match="must be a str"):
            StateApplicationGenerationId(123)  # type: ignore[arg-type]
        with pytest.raises(ValueError, match="cannot be empty or whitespace"):
            StateApplicationGenerationId("")
        with pytest.raises(ValueError, match="cannot be empty or whitespace"):
            StateApplicationGenerationId("   ")

    def test_state_generation_allocator_deterministic_sequence(self) -> None:
        allocator = StateGenerationAllocator()
        g1 = allocator.allocate()
        g2 = allocator.allocate()
        g3 = allocator.allocate(prefix="s10_gen")

        assert g1 == StateApplicationGenerationId("gen_1")
        assert g2 == StateApplicationGenerationId("gen_2")
        assert g3 == StateApplicationGenerationId("s10_gen_3")
        assert g1 != g2
        assert g2 != g3


class TestPersistentLifecycleWindow:
    def test_valid_lifecycle_window(self) -> None:
        window = PersistentLifecycleWindow(
            application_phase="UNIT_ACTION_START",
            application_round=1,
            first_eligible_round=1,
            last_eligible_round=2,
            max_opportunities_per_owner_round=1,
        )
        assert window.is_round_eligible(1) is True
        assert window.is_round_eligible(2) is True
        assert window.is_round_eligible(3) is False
        assert window.is_expired(2) is True
        assert window.is_expired(1) is False

    def test_invalid_lifecycle_window_rejected(self) -> None:
        with pytest.raises(ValueError, match="cannot be empty"):
            PersistentLifecycleWindow("", 1, 1, 2)
        with pytest.raises(ValueError, match="application_round must be >= 0"):
            PersistentLifecycleWindow("ACTION", -1, 1, 2)
        with pytest.raises(ValueError, match="first_eligible_round must be >= 1"):
            PersistentLifecycleWindow("ACTION", 1, 0, 2)
        with pytest.raises(ValueError, match="last_eligible_round must be >= first_eligible_round"):
            PersistentLifecycleWindow("ACTION", 1, 3, 2)
        with pytest.raises(ValueError, match="max_opportunities_per_owner_round must be exactly 1"):
            PersistentLifecycleWindow("ACTION", 1, 1, 2, max_opportunities_per_owner_round=2)


class TestStateGenerationSnapshot:
    def test_snapshot_immutability(self) -> None:
        gen_id = StateApplicationGenerationId("gen_test_1")
        window = PersistentLifecycleWindow("UNIT_ACTION_START", 1, 1, 2)
        snapshot = StateGenerationSnapshot(
            physical_instance_id="inst_101",
            application_generation_id=gen_id,
            state_id="burn",
            owner_id="u1",
            source_id="u2",
            source_skill_id="skill_fire",
            source_skill_slot=SkillSlot.INHERENT,
            lifecycle_window=window,
        )

        assert snapshot.physical_instance_id == "inst_101"
        assert snapshot.application_generation_id == gen_id
        assert snapshot.state_id == "burn"
        assert snapshot.owner_id == "u1"
        assert snapshot.source_id == "u2"

        with pytest.raises(FrozenInstanceError):
            snapshot.state_id = "poison"  # type: ignore[misc]

    def test_snapshot_validation(self) -> None:
        with pytest.raises(ValueError, match="physical_instance_id cannot be empty"):
            StateGenerationSnapshot("", StateApplicationGenerationId("g1"), "burn", "u1")
        with pytest.raises(TypeError, match="must be a StateApplicationGenerationId"):
            StateGenerationSnapshot("inst_1", "g1", "burn", "u1")  # type: ignore[arg-type]


class TestSkillRuntimeRegistry:
    def _make_runtime(self, owner_id: str, slot: SkillSlot, skill_id: str = "sk_1") -> SkillRuntime:
        definition = SkillDefinition(
            skill_id=skill_id,
            name=f"Skill {skill_id}",
            activation_rate=1.0,
            target_mode=SkillTargetMode.SINGLE_RANDOM_ENEMY,
            effect_specs=(DamageSkillEffectSpec(DamageType.WEAPON, 1.0),),
        )
        return SkillRuntime(definition=definition, owner_id=owner_id, skill_slot=slot, enabled=True)

    def test_register_lookup_and_isolation(self) -> None:
        registry = SkillRuntimeRegistry()
        rt1 = self._make_runtime("u1", SkillSlot.INHERENT, "sk_inh")
        rt2 = self._make_runtime("u1", SkillSlot.LEARNED_1, "sk_l1")
        rt3 = self._make_runtime("u2", SkillSlot.INHERENT, "sk_inh")

        registry.register(rt1)
        registry.register(rt2)
        registry.register(rt3)

        assert len(registry) == 3
        assert registry.contains("u1", SkillSlot.INHERENT) is True
        assert registry.contains("u1", SkillSlot.LEARNED_2) is False

        looked_up = registry.lookup("u1", SkillSlot.INHERENT, expected_skill_id="sk_inh")
        assert looked_up is rt1
        assert registry.lookup("u1", SkillSlot.LEARNED_1) is rt2
        assert registry.lookup("u2", SkillSlot.INHERENT) is rt3

    def test_duplicate_slot_rejected(self) -> None:
        registry = SkillRuntimeRegistry()
        rt1 = self._make_runtime("u1", SkillSlot.INHERENT, "sk_1")
        rt2 = self._make_runtime("u1", SkillSlot.INHERENT, "sk_2")

        registry.register(rt1)
        with pytest.raises(ValueError, match="Duplicate SkillRuntime registration"):
            registry.register(rt2)

    def test_lookup_missing_raises_key_error(self) -> None:
        registry = SkillRuntimeRegistry()
        with pytest.raises(KeyError, match="No SkillRuntime registered for owner 'u1'"):
            registry.lookup("u1", SkillSlot.INHERENT)

    def test_expected_skill_id_mismatch_raises_value_error(self) -> None:
        registry = SkillRuntimeRegistry()
        rt1 = self._make_runtime("u1", SkillSlot.INHERENT, "actual_skill")
        registry.register(rt1)

        with pytest.raises(ValueError, match="SkillRuntime skill_id mismatch"):
            registry.lookup("u1", SkillSlot.INHERENT, expected_skill_id="expected_other_skill")

    def test_dead_owner_does_not_delete_or_disable_entry(self) -> None:
        ctx = _make_dummy_context()
        unit = ctx.get_unit("u1")
        rt = self._make_runtime("u1", SkillSlot.INHERENT, "sk_persist")
        ctx.skill_runtimes.register(rt)

        # Kill the unit
        unit.troops = 0
        assert unit.is_alive is False

        # Verify registry entry persists authoritatively and enabled flag is untouched
        looked_up = ctx.skill_runtimes.lookup("u1", SkillSlot.INHERENT, "sk_persist")
        assert looked_up is rt
        assert looked_up.enabled is True


class TestActionProgressTracker:
    def test_progress_tracking_and_idempotency(self) -> None:
        tracker = ActionProgressTracker()
        assert tracker.has_consumed_action_start("u1", 1) is False
        assert tracker.has_acted_in_round("u1", 1) is False

        # First mark in Round 1 succeeds
        res1 = tracker.mark_action_start("u1", 1)
        assert res1 is True
        assert tracker.has_consumed_action_start("u1", 1) is True
        assert tracker.has_acted_in_round("u1", 1) is True

        # Duplicate mark in same round returns False (idempotent)
        res2 = tracker.mark_action_start("u1", 1)
        assert res2 is False

        # Round 2 is NOT consumed
        assert tracker.has_consumed_action_start("u1", 2) is False

        # Different unit is independent
        assert tracker.has_consumed_action_start("u2", 1) is False
        assert tracker.mark_action_start("u2", 1) is True

    def test_current_acting_unit(self) -> None:
        tracker = ActionProgressTracker()
        assert tracker.current_acting_unit is None

        tracker.set_current_acting_unit("u1")
        assert tracker.current_acting_unit == "u1"

        tracker.set_current_acting_unit(None)
        assert tracker.current_acting_unit is None


class TestPersistentSourceSkillGate:
    def test_modes_and_factory_constructors(self) -> None:
        g1 = PersistentSourceSkillGate.always_active()
        g2 = PersistentSourceSkillGate.query_skill_runtime()
        g3 = PersistentSourceSkillGate.external_lifecycle()

        assert g1.mode == PersistentSourceSkillGateMode.ALWAYS_ACTIVE
        assert g2.mode == PersistentSourceSkillGateMode.QUERY_SKILL_RUNTIME
        assert g3.mode == PersistentSourceSkillGateMode.EXTERNAL_LIFECYCLE

        # Immutability
        with pytest.raises(FrozenInstanceError):
            g1.mode = PersistentSourceSkillGateMode.QUERY_SKILL_RUNTIME  # type: ignore[misc]


class TestStage10StateParams:
    def test_continuous_damage_params_validations_and_schema(self) -> None:
        validate_state_runtime_params_type(ContinuousDamageStateParams)

        gen_id = StateApplicationGenerationId("gen_dot_1")
        basis = FrozenContinuousDamageBasis(
            application_generation_id=gen_id,
            source_unit_id="u1",
            damage_type=DamageType.STRATEGY,
            coefficient=1.2,
        )
        params = ContinuousDamageStateParams(
            application_generation_id=gen_id,
            frozen_damage_basis=basis,
        )
        validate_state_runtime_params(params)
        assert params.application_generation_id == gen_id
        assert params.source_skill_gate.mode == PersistentSourceSkillGateMode.ALWAYS_ACTIVE

    def test_first_aid_params_validations(self) -> None:
        validate_state_runtime_params_type(FirstAidStateParams)

        potency = RecoveryPotencyContext(base_rate=0.5, ratio=0.35, source_intellect=220)
        params = FirstAidStateParams(
            probability=0.7,
            recovery_model_kind=RecoveryModelKind.TRIGGER_DAMAGE_RATIO,
            recovery_potency_context=potency,
        )
        validate_state_runtime_params(params)
        assert params.probability == 0.7
        assert params.recovery_model_kind == RecoveryModelKind.TRIGGER_DAMAGE_RATIO
        assert params.source_skill_gate.mode == PersistentSourceSkillGateMode.QUERY_SKILL_RUNTIME

        # Invalid probability
        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            FirstAidStateParams(probability=1.5, recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT)
        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            FirstAidStateParams(probability=-0.1, recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT)

    def test_recuperation_params_validations(self) -> None:
        validate_state_runtime_params_type(RecuperationStateParams)

        params = RecuperationStateParams(probability=1.0)
        validate_state_runtime_params(params)
        assert params.probability == 1.0
        assert params.source_skill_gate.mode == PersistentSourceSkillGateMode.QUERY_SKILL_RUNTIME

        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            RecuperationStateParams(probability=2.0)


class TestRuleIntentAndDescriptor:
    def test_recovery_opportunity_kinds_frozen(self) -> None:
        assert set(RecoveryOpportunityKind) == {
            RecoveryOpportunityKind.FIRST_AID_AFTER_DAMAGE,
            RecoveryOpportunityKind.RECUPERATION_ACTION_START,
        }

    def test_descriptor_immutability_and_h01_precondition(self) -> None:
        gen_id = StateApplicationGenerationId("gen_desc_1")
        source_ref = EffectSourceRef(
            stage9_source_type=SourceType.ACTIVE_SKILL,
            source_unit_id="u1",
            source_skill_id="sk_1",
        )

        desc = RuleIntentExecutionDescriptor(
            intent_kind=RuleIntentKind.EFFECT,
            intent_owner_id="u1",
            state_owner_id="u2",
            target_id="u2",
            source_ref=source_ref,
            state_instance_id="inst_1",
            state_generation_id=gen_id,
            execution_domain="STATE_RESOLUTION",
        )

        assert desc.intent_kind == RuleIntentKind.EFFECT
        assert desc.intent_owner_id == "u1"
        assert desc.state_owner_id == "u2"
        assert desc.intent_owner_id != desc.state_owner_id
        assert desc.target_id == "u2"
        assert desc.state_generation_id == gen_id

        with pytest.raises(FrozenInstanceError):
            desc.intent_owner_id = "u3"  # type: ignore[misc]

        # S10-FG-H01 Precondition Validation: intent_owner_id cannot be missing/empty
        with pytest.raises(ValueError, match="intent_owner_id cannot be empty or whitespace"):
            RuleIntentExecutionDescriptor(
                intent_kind=RuleIntentKind.EFFECT,
                intent_owner_id="",
            )
        with pytest.raises(ValueError, match="intent_owner_id cannot be empty or whitespace"):
            RuleIntentExecutionDescriptor(
                intent_kind=RuleIntentKind.EFFECT,
                intent_owner_id="   ",
            )

    def test_recovery_opportunity_structure(self) -> None:
        desc = RuleIntentExecutionDescriptor(
            intent_kind=RuleIntentKind.RECOVERY_OPPORTUNITY,
            intent_owner_id="u1",
            target_id="u1",
        )
        opp = RecoveryOpportunity(
            opportunity_kind=RecoveryOpportunityKind.FIRST_AID_AFTER_DAMAGE,
            execution_descriptor=desc,
            probability=0.5,
            recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT,
        )

        assert opp.opportunity_kind == RecoveryOpportunityKind.FIRST_AID_AFTER_DAMAGE
        assert opp.execution_descriptor is desc
        assert opp.probability == 0.5

        # Sibling result representations
        res = RecoveryOpportunityResult(opportunity=opp, executed=False, reason="PROBABILITY_FAILED")
        assert res.executed is False

        aborted = AbortedRuleIntentResult(
            descriptor=desc,
            decision_kind=ExecutionRightDecisionKind.REJECT_CURRENT,
            reason=ExecutionRightReason.TARGET_DEFEATED,
        )
        assert aborted.decision_kind == ExecutionRightDecisionKind.REJECT_CURRENT


class TestStateInstanceGenerationIntegration:
    def test_default_generation_id_allocation(self) -> None:
        inst = StateInstance(
            instance_id="inst_burn_1",
            state_id="burn",
            owner_id="u1",
            source_id="u2",
            source_skill_id="sk_fire",
            applied_round=1,
            applied_phase="UNIT_ACTION_START",
        )
        # Defaults to valid StateApplicationGenerationId without breaking legacy callers
        assert isinstance(inst.current_generation_id, StateApplicationGenerationId)
        assert str(inst.current_generation_id) == "gen_inst_burn_1"

    def test_explicit_generation_id(self) -> None:
        custom_gen = StateApplicationGenerationId("gen_custom_99")
        inst = StateInstance(
            instance_id="inst_burn_2",
            state_id="burn",
            owner_id="u1",
            source_id="u2",
            source_skill_id="sk_fire",
            applied_round=1,
            applied_phase="UNIT_ACTION_START",
            current_generation_id=custom_gen,
        )
        assert inst.current_generation_id == custom_gen

    def test_create_generation_snapshot(self) -> None:
        custom_gen = StateApplicationGenerationId("gen_custom_100")
        window = PersistentLifecycleWindow("UNIT_ACTION_START", 1, 1, 3)
        inst = StateInstance(
            instance_id="inst_burn_3",
            state_id="burn",
            owner_id="u1",
            source_id="u2",
            source_skill_id="sk_fire",
            applied_round=1,
            applied_phase="UNIT_ACTION_START",
            current_generation_id=custom_gen,
            lifecycle_window=window,
        )
        snapshot = inst.create_generation_snapshot()
        assert snapshot.physical_instance_id == "inst_burn_3"
        assert snapshot.application_generation_id == custom_gen
        assert snapshot.state_id == "burn"
        assert snapshot.lifecycle_window == window


class TestEffectExecutionDescriptorIntegration:
    def test_damage_effect_with_and_without_descriptor(self) -> None:
        eff1 = DamageEffect(
            source_id="u1",
            target_id="u2",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.SKILL,
        )
        assert eff1.execution_descriptor is None

        desc = RuleIntentExecutionDescriptor(
            intent_kind=RuleIntentKind.EFFECT,
            intent_owner_id="u1",
            target_id="u2",
        )
        eff2 = DamageEffect(
            source_id="u1",
            target_id="u2",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.SKILL,
            execution_descriptor=desc,
        )
        assert eff2.execution_descriptor is desc


class TestOfficialStateCatalogStage10Bindings:
    def test_stage10_persistent_state_ids_frozen(self) -> None:
        expected_ids = {
            OfficialStateId.BURN,
            OfficialStateId.FLOOD,
            OfficialStateId.POISON,
            OfficialStateId.ROUT,
            OfficialStateId.SANDSTORM,
            OfficialStateId.REBELLION,
            OfficialStateId.FIRST_AID,
            OfficialStateId.RECUPERATION,
        }
        assert STAGE10_PERSISTENT_STATE_IDS == expected_ids

    def test_stage10_persistent_params_mapping(self) -> None:
        assert get_stage10_persistent_params_type(OfficialStateId.BURN) is ContinuousDamageStateParams
        assert get_stage10_persistent_params_type("burn") is ContinuousDamageStateParams
        assert get_stage10_persistent_params_type(OfficialStateId.REBELLION) is ContinuousDamageStateParams
        assert get_stage10_persistent_params_type(OfficialStateId.FIRST_AID) is FirstAidStateParams
        assert get_stage10_persistent_params_type(OfficialStateId.RECUPERATION) is RecuperationStateParams

        with pytest.raises(KeyError):
            get_stage10_persistent_params_type(OfficialStateId.CLEAVE)
