from __future__ import annotations

from dataclasses import FrozenInstanceError
import pytest

from sgs_v2.battle_core.effects import DamageEffect, EffectSourceRef
from sgs_v2.battle_core.enums import DamageSourceType, DamageType
from sgs_v2.battle_core.execution_right_system import (
    BattleTerminationState,
    DamageSettlementPermit,
    FinalizationProjectionPermit,
    FutureAdmissionPermit,
    FutureBranchKind,
    LegacyFinalizationBarrier,
    PermitStatus,
)
from sgs_v2.battle_core.operation_identity import (
    ActionId,
    ChainTraversalId,
    CleaveEffectId,
    CounterBatchEntryId,
    DamageInstanceId,
    DirectTroopLossId,
    FinalizationId,
    NormalAttackInstanceId,
    OperationIdAllocator,
    OperationLineage,
    PartitionTransactionId,
    ReactionBatchId,
    SourceType,
    TargetResolutionId,
)
from sgs_v2.battle_core.reaction_permission_policy import ReactionPermissionPolicy
from sgs_v2.battle_core.skill_definition import DamageSkillEffectSpec, SkillDefinition, SkillTargetMode
from sgs_v2.battle_core.skill_runtime import LoadedSkillRef, LoadedSkillSet, SkillSlot
from sgs_v2.battle_core.stage9_integerization import (
    ExactRatio,
    exact_ratio_from_legacy_config_float,
    floor_product_int_ratio,
    round_half_up_divide_int,
    round_half_up_product_int_ratio,
)
from sgs_v2.battle_core.stage9_state_params import (
    ChainStateParams,
    CleaveStateParams,
    ComboStateParams,
    CounterStateParams,
    DamageShareStateParams,
    DistributionStateParams,
    GuardStateParams,
    TauntStateParams,
)
from sgs_v2.battle_core.stage9_trace import Stage9DiagnosticTraceSink, Stage9TraceEntry


class TestOperationIdentityAndAllocator:
    def test_allocator_produces_monotonic_unique_ids(self) -> None:
        allocator = OperationIdAllocator()

        act1 = allocator.allocate_action_id()
        act2 = allocator.allocate_action_id()
        assert act1 != act2
        assert act1.value == "act_1"
        assert act2.value == "act_2"

        na1 = allocator.allocate_normal_attack_id()
        na2 = allocator.allocate_normal_attack_id()
        assert na1 != na2
        assert na1.value == "na_1"

        tr1 = allocator.allocate_target_resolution_id()
        assert tr1.value == "tr_1"

        dmg1 = allocator.allocate_damage_instance_id()
        assert dmg1.value == "dmg_1"

        ptx1 = allocator.allocate_partition_transaction_id()
        assert ptx1.value == "ptx_1"

        rxn1 = allocator.allocate_reaction_batch_id()
        assert rxn1.value == "rxn_1"

        cbe1 = allocator.allocate_counter_batch_entry_id()
        assert cbe1.value == "cbe_1"

        clv1 = allocator.allocate_cleave_effect_id()
        assert clv1.value == "clv_1"

        chn1 = allocator.allocate_chain_traversal_id()
        assert chn1.value == "chn_1"

        dtl1 = allocator.allocate_direct_troop_loss_id()
        assert dtl1.value == "dtl_1"

        fin1 = allocator.allocate_finalization_id()
        assert fin1.value == "fin_1"

        prm1 = allocator.allocate_permit_id()
        assert prm1 == "prm_1"

    def test_typed_identity_non_interchangeability(self) -> None:
        raw_val = "op_1"
        act = ActionId(raw_val)
        na = NormalAttackInstanceId(raw_val)
        tr = TargetResolutionId(raw_val)
        dmg = DamageInstanceId(raw_val)
        ptx = PartitionTransactionId(raw_val)
        rxn = ReactionBatchId(raw_val)
        cbe = CounterBatchEntryId(raw_val)
        clv = CleaveEffectId(raw_val)
        chn = ChainTraversalId(raw_val)
        dtl = DirectTroopLossId(raw_val)
        fin = FinalizationId(raw_val)

        # None of different types are equal even with identical underlying string
        id_list = [act, na, tr, dmg, ptx, rxn, cbe, clv, chn, dtl, fin]
        for i in range(len(id_list)):
            for j in range(len(id_list)):
                if i == j:
                    assert id_list[i] == id_list[j]
                else:
                    assert id_list[i] != id_list[j]

    def test_identity_immutability(self) -> None:
        act = ActionId("act_1")
        with pytest.raises(FrozenInstanceError):
            act.value = "act_2"  # type: ignore[misc]

    def test_empty_or_invalid_id_value_rejected(self) -> None:
        with pytest.raises(TypeError):
            ActionId(123)  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            ActionId("")
        with pytest.raises(ValueError):
            ActionId("   ")


class TestOperationLineage:
    def test_valid_operation_lineage(self) -> None:
        act = ActionId("act_1")
        na = NormalAttackInstanceId("na_1")
        dmg = DamageInstanceId("dmg_1")

        lineage = OperationLineage(
            root_action_id=act,
            parent_normal_attack_id=na,
            parent_damage_instance_id=dmg,
            source_type=SourceType.NORMAL_ATTACK,
            physical_attacker="attacker_1",
            physical_skill=None,
            credit_owner="attacker_1",
        )
        assert lineage.root_action_id == act
        assert lineage.parent_normal_attack_id == na
        assert lineage.parent_damage_instance_id == dmg
        assert lineage.source_type == SourceType.NORMAL_ATTACK
        assert lineage.physical_attacker == "attacker_1"

    def test_lineage_validation_rejections(self) -> None:
        act = ActionId("act_1")
        # Invalid source_type
        with pytest.raises(TypeError):
            OperationLineage(
                root_action_id=act,
                parent_normal_attack_id=None,
                parent_damage_instance_id=None,
                source_type="NORMAL_ATTACK",  # type: ignore[arg-type]
            )
        # Invalid ID type (raw string instead of ActionId)
        with pytest.raises(TypeError):
            OperationLineage(
                root_action_id="act_1",  # type: ignore[arg-type]
                parent_normal_attack_id=None,
                parent_damage_instance_id=None,
                source_type=SourceType.NORMAL_ATTACK,
            )
        # Empty whitespace attacker
        with pytest.raises(ValueError):
            OperationLineage(
                root_action_id=act,
                parent_normal_attack_id=None,
                parent_damage_instance_id=None,
                source_type=SourceType.NORMAL_ATTACK,
                physical_attacker="   ",
            )

    def test_lineage_immutability(self) -> None:
        lineage = OperationLineage(
            root_action_id=ActionId("act_1"),
            parent_normal_attack_id=None,
            parent_damage_instance_id=None,
            source_type=SourceType.NORMAL_ATTACK,
        )
        with pytest.raises(FrozenInstanceError):
            lineage.physical_attacker = "new_attacker"  # type: ignore[misc]


class TestSourceTypeAndEffectSourceRef:
    def test_source_type_domain(self) -> None:
        expected = {
            "NORMAL_ATTACK",
            "ACTIVE_SKILL",
            "ASSAULT",
            "PERIODIC_DAMAGE",
            "CLEAVE",
            "COUNTER",
            "CHAIN_TRUE_FEEDBACK",
            "SHARE_DIRECT_LOSS",
            "DISTRIBUTION_DIRECT_LOSS",
        }
        assert {item.value for item in SourceType} == expected

    def test_effect_source_ref_validation(self) -> None:
        ref = EffectSourceRef(
            stage9_source_type=SourceType.ACTIVE_SKILL,
            source_unit_id="unit_1",
            source_skill_id="skill_fire",
            source_skill_slot=SkillSlot.LEARNED_1,
        )
        assert ref.stage9_source_type == SourceType.ACTIVE_SKILL
        assert ref.source_unit_id == "unit_1"
        assert ref.source_skill_id == "skill_fire"
        assert ref.source_skill_slot == SkillSlot.LEARNED_1

        # ACTIVE_SKILL requires source_unit_id and source_skill_id
        with pytest.raises(ValueError):
            EffectSourceRef(
                stage9_source_type=SourceType.ACTIVE_SKILL,
                source_unit_id=None,
                source_skill_id="skill_fire",
            )
        with pytest.raises(ValueError):
            EffectSourceRef(
                stage9_source_type=SourceType.ACTIVE_SKILL,
                source_unit_id="unit_1",
                source_skill_id=None,
            )

        # System / non-skill source can have None skill
        sys_ref = EffectSourceRef(
            stage9_source_type=SourceType.NORMAL_ATTACK,
            source_unit_id="unit_1",
        )
        assert sys_ref.source_skill_id is None
        assert sys_ref.source_skill_slot is None

    def test_effect_source_ref_distinct_from_lineage(self) -> None:
        ref = EffectSourceRef(
            stage9_source_type=SourceType.ACTIVE_SKILL,
            source_unit_id="unit_1",
            source_skill_id="skill_1",
            source_skill_slot=SkillSlot.INHERENT,
        )
        lineage = OperationLineage(
            root_action_id=ActionId("act_1"),
            parent_normal_attack_id=None,
            parent_damage_instance_id=None,
            source_type=SourceType.ACTIVE_SKILL,
            physical_attacker="unit_1",
            physical_skill="skill_1",
        )
        assert ref != lineage
        assert type(ref) is not type(lineage)


class TestSkillSlotDomain:
    def test_skill_slot_exact_domain(self) -> None:
        assert SkillSlot.INHERENT == 0
        assert SkillSlot.LEARNED_1 == 1
        assert SkillSlot.LEARNED_2 == 2
        assert {item.value for item in SkillSlot} == {0, 1, 2}

    def test_loaded_skill_ref_and_set_validation(self) -> None:
        def_1 = SkillDefinition(
            skill_id="s1",
            name="Skill 1",
            activation_rate=1.0,
            target_mode=SkillTargetMode.SINGLE_RANDOM_ENEMY,
            effect_specs=(DamageSkillEffectSpec(DamageType.WEAPON),),
        )
        def_2 = SkillDefinition(
            skill_id="s2",
            name="Skill 2",
            activation_rate=1.0,
            target_mode=SkillTargetMode.SINGLE_RANDOM_ENEMY,
            effect_specs=(DamageSkillEffectSpec(DamageType.STRATEGY),),
        )

        ref1 = LoadedSkillRef(owner_id="u1", definition=def_1, skill_slot=SkillSlot.INHERENT)
        ref2 = LoadedSkillRef(owner_id="u1", definition=def_2, skill_slot=SkillSlot.LEARNED_1)

        skill_set = LoadedSkillSet(owner_id="u1", loaded=(ref1, ref2))
        assert len(skill_set.loaded) == 2

        # Duplicate slot rejection
        ref2_dup = LoadedSkillRef(owner_id="u1", definition=def_2, skill_slot=SkillSlot.INHERENT)
        with pytest.raises(ValueError, match="Duplicate SkillSlot"):
            LoadedSkillSet(owner_id="u1", loaded=(ref1, ref2_dup))

        # Owner mismatch rejection
        ref_other_owner = LoadedSkillRef(owner_id="u2", definition=def_2, skill_slot=SkillSlot.LEARNED_1)
        with pytest.raises(ValueError, match="does not match"):
            LoadedSkillSet(owner_id="u1", loaded=(ref1, ref_other_owner))


class TestExactRatioAndIntegerization:
    def test_exact_ratio_canonicalization_gcd(self) -> None:
        r1 = ExactRatio(54, 100)
        assert r1.numerator == 27
        assert r1.denominator == 50

        r2 = ExactRatio(540, 1000)
        assert r2.numerator == 27
        assert r2.denominator == 50

    def test_exact_ratio_sign_normalization(self) -> None:
        r1 = ExactRatio(-54, -100)
        assert r1.numerator == 27
        assert r1.denominator == 50

        r2 = ExactRatio(54, -100)
        assert r2.numerator == -27
        assert r2.denominator == 50

        r3 = ExactRatio(-54, 100)
        assert r3.numerator == -27
        assert r3.denominator == 50

    def test_exact_ratio_zero_canonicalization(self) -> None:
        r1 = ExactRatio(0, 7)
        assert r1.numerator == 0
        assert r1.denominator == 1

        r2 = ExactRatio(0, -99)
        assert r2.numerator == 0
        assert r2.denominator == 1

    def test_exact_ratio_positive_denominator_and_zero_division(self) -> None:
        r = ExactRatio(10, 2)
        assert r.denominator > 0

        with pytest.raises(ZeroDivisionError):
            ExactRatio(1, 0)

    def test_exact_ratio_no_generic_from_float(self) -> None:
        assert not hasattr(ExactRatio, "from_float")

    def test_exact_ratio_from_text(self) -> None:
        assert ExactRatio.from_text("0.54") == ExactRatio(27, 50)
        assert ExactRatio.from_text("54%") == ExactRatio(27, 50)
        assert ExactRatio.from_text("28.28%") == ExactRatio(707, 2500)
        assert ExactRatio.from_text("27/50") == ExactRatio(27, 50)

    def test_exact_ratio_from_legacy_config_float(self) -> None:
        r = exact_ratio_from_legacy_config_float(0.54)
        assert r == ExactRatio(27, 50)

    def test_exact_ratio_immutability(self) -> None:
        r = ExactRatio(27, 50)
        with pytest.raises(FrozenInstanceError):
            r.numerator = 1  # type: ignore[misc]


class TestArchitectureNoGameplayComparators:
    """Architecture Guarantee: Operation IDs and permit IDs never act as gameplay comparators."""

    def test_ids_cannot_be_compared_with_relational_operators(self) -> None:
        alloc = OperationIdAllocator()

        act1 = alloc.allocate_action_id()
        act2 = alloc.allocate_action_id()
        with pytest.raises(TypeError, match="does not support comparison operator"):
            _ = act1 < act2

        na1 = alloc.allocate_normal_attack_id()
        na2 = alloc.allocate_normal_attack_id()
        with pytest.raises(TypeError, match="does not support comparison operator"):
            _ = na1 < na2

        dmg1 = alloc.allocate_damage_instance_id()
        dmg2 = alloc.allocate_damage_instance_id()
        with pytest.raises(TypeError, match="does not support comparison operator"):
            _ = dmg1 < dmg2

        ptx1 = alloc.allocate_partition_transaction_id()
        ptx2 = alloc.allocate_partition_transaction_id()
        with pytest.raises(TypeError, match="does not support comparison operator"):
            _ = ptx1 < ptx2

        rxn1 = alloc.allocate_reaction_batch_id()
        rxn2 = alloc.allocate_reaction_batch_id()
        with pytest.raises(TypeError, match="does not support comparison operator"):
            _ = rxn1 < rxn2

        cbe1 = alloc.allocate_counter_batch_entry_id()
        cbe2 = alloc.allocate_counter_batch_entry_id()
        with pytest.raises(TypeError, match="does not support comparison operator"):
            _ = cbe1 < cbe2

        clv1 = alloc.allocate_cleave_effect_id()
        clv2 = alloc.allocate_cleave_effect_id()
        with pytest.raises(TypeError, match="does not support comparison operator"):
            _ = clv1 < clv2

        chn1 = alloc.allocate_chain_traversal_id()
        chn2 = alloc.allocate_chain_traversal_id()
        with pytest.raises(TypeError, match="does not support comparison operator"):
            _ = chn1 < chn2

        dtl1 = alloc.allocate_direct_troop_loss_id()
        dtl2 = alloc.allocate_direct_troop_loss_id()
        with pytest.raises(TypeError, match="does not support comparison operator"):
            _ = dtl1 < dtl2

        tr1 = alloc.allocate_target_resolution_id()
        tr2 = alloc.allocate_target_resolution_id()
        with pytest.raises(TypeError, match="does not support comparison operator"):
            _ = tr1 < tr2

        fin1 = alloc.allocate_finalization_id()
        fin2 = alloc.allocate_finalization_id()
        with pytest.raises(TypeError, match="does not support comparison operator"):
            _ = fin1 < fin2

    def test_permits_and_lineage_cannot_be_compared(self) -> None:
        p1 = FutureAdmissionPermit("p1", FutureBranchKind.NEXT_ACTION, "scope1", 0)
        p2 = FutureAdmissionPermit("p2", FutureBranchKind.NEXT_ACTION, "scope1", 0)
        with pytest.raises(TypeError, match="does not support comparison operator"):
            _ = p1 < p2

        ds1 = DamageSettlementPermit("p1", DamageInstanceId("dmg_1"))
        ds2 = DamageSettlementPermit("p2", DamageInstanceId("dmg_2"))
        with pytest.raises(TypeError, match="does not support comparison operator"):
            _ = ds1 < ds2

        fp1 = FinalizationProjectionPermit("p1", FinalizationId("fin_1"))
        fp2 = FinalizationProjectionPermit("p2", FinalizationId("fin_2"))
        with pytest.raises(TypeError, match="does not support comparison operator"):
            _ = fp1 < fp2

        l1 = OperationLineage(None, None, None, SourceType.NORMAL_ATTACK)
        l2 = OperationLineage(None, None, None, SourceType.NORMAL_ATTACK)
        with pytest.raises(TypeError, match="does not support comparison operator"):
            _ = l1 < l2


class TestPermitAndCapabilityTypes:
    def test_future_branch_kind_exact_six(self) -> None:
        expected = {
            "NEXT_ACTION",
            "ASSAULT",
            "COMBO_SECOND_NORMAL_ATTACK",
            "COUNTER_BATCH",
            "CHAIN_TRAVERSAL",
            "CLEAVE_EFFECT",
        }
        assert {item.value for item in FutureBranchKind} == expected

    def test_battle_termination_state_exact_four(self) -> None:
        expected = {
            "RUNNING",
            "VICTORY_LATCHED",
            "DRAINING_ADMITTED_WORK",
            "FINALIZED",
        }
        assert {item.value for item in BattleTerminationState} == expected

    def test_legacy_finalization_barrier_exact_six(self) -> None:
        expected = {
            "INITIAL_SETTLED",
            "ROUND_START_HOOKS_SETTLED",
            "UNIT_ACTION_START_HOOKS_SETTLED",
            "ACTION_SETTLED",
            "ROUND_END_SETTLED",
            "MAX_ROUND_SETTLED",
        }
        assert {item.value for item in LegacyFinalizationBarrier} == expected

    def test_permit_validation(self) -> None:
        permit = FutureAdmissionPermit(
            permit_id="prm_1",
            branch_kind=FutureBranchKind.NEXT_ACTION,
            parent_scope_identity="engine_1",
            termination_generation=0,
        )
        assert permit.permit_id == "prm_1"

        with pytest.raises(ValueError):
            FutureAdmissionPermit("", FutureBranchKind.NEXT_ACTION, "scope", 0)

        with pytest.raises(TypeError):
            FutureAdmissionPermit("prm_1", "NEXT_ACTION", "scope", 0)  # type: ignore[arg-type]

        with pytest.raises(ValueError):
            FutureAdmissionPermit("prm_1", FutureBranchKind.NEXT_ACTION, "scope", -1)


class TestReactionPermissionPolicy:
    """Mapped to INV-13, INV-17, INV-19, INV-20, INV-42."""

    def test_normal_attack_permissions(self) -> None:
        st = SourceType.NORMAL_ATTACK
        assert ReactionPermissionPolicy.has_normal_attack_identity(st) is True
        assert ReactionPermissionPolicy.is_direct_troop_loss(st) is False
        assert ReactionPermissionPolicy.can_trigger_cleave(st) is True
        assert ReactionPermissionPolicy.can_trigger_counter(st) is True
        assert ReactionPermissionPolicy.can_trigger_chain(st) is True
        assert ReactionPermissionPolicy.can_enter_partition(st) is True
        assert ReactionPermissionPolicy.can_trigger_recovery(st) is True

    def test_cleave_permissions_blocked_recursive_and_counter(self) -> None:
        # INV-13: Cleave has no NormalAttack identity
        # INV-17: Cleave permissions are identity-driven (Counter and recursive Cleave blocked)
        st = SourceType.CLEAVE
        assert ReactionPermissionPolicy.has_normal_attack_identity(st) is False
        assert ReactionPermissionPolicy.can_trigger_cleave(st) is False
        assert ReactionPermissionPolicy.can_trigger_counter(st) is False
        assert ReactionPermissionPolicy.can_trigger_chain(st) is True
        assert ReactionPermissionPolicy.can_enter_partition(st) is True

    def test_counter_permissions_blocked_counter_and_cleave(self) -> None:
        st = SourceType.COUNTER
        assert ReactionPermissionPolicy.has_normal_attack_identity(st) is False
        assert ReactionPermissionPolicy.can_trigger_counter(st) is False
        assert ReactionPermissionPolicy.can_trigger_cleave(st) is False
        assert ReactionPermissionPolicy.can_trigger_chain(st) is True

    def test_direct_troop_loss_permissions_strictly_blocked(self) -> None:
        # INV-19 / INV-20: Direct troop loss never enters HitResolution / callbacks
        for st in (SourceType.SHARE_DIRECT_LOSS, SourceType.DISTRIBUTION_DIRECT_LOSS):
            assert ReactionPermissionPolicy.is_direct_troop_loss(st) is True
            assert ReactionPermissionPolicy.has_normal_attack_identity(st) is False
            assert ReactionPermissionPolicy.can_trigger_cleave(st) is False
            assert ReactionPermissionPolicy.can_trigger_counter(st) is False
            assert ReactionPermissionPolicy.can_trigger_chain(st) is False
            assert ReactionPermissionPolicy.can_enter_partition(st) is False
            assert ReactionPermissionPolicy.can_trigger_recovery(st) is False
            assert ReactionPermissionPolicy.can_trigger_evasion(st) is False
            assert ReactionPermissionPolicy.can_trigger_resistance(st) is False


class TestStage9DiagnosticTraceSink:
    def test_trace_sink_boundedness(self) -> None:
        sink = Stage9DiagnosticTraceSink(max_capacity=5)
        for i in range(10):
            sink.record("CATEGORY_TEST", f"op_{i}", value=i)

        assert sink.count == 5
        entries = sink.get_entries()
        assert len(entries) == 5
        # The oldest 5 entries (0..4) were dropped; remaining are 5..9
        assert entries[0].payload["value"] == 5
        assert entries[-1].payload["value"] == 9

    def test_trace_sink_filtering(self) -> None:
        sink = Stage9DiagnosticTraceSink(max_capacity=100)
        sink.record("ADMISSION", "op_1")
        sink.record("FINALIZATION", "op_2")
        sink.record("ADMISSION", "op_3")

        adm = sink.filter_by_category("ADMISSION")
        assert len(adm) == 2
        assert [e.operation_id for e in adm] == ["op_1", "op_3"]


class TestStage9StateParams:
    def test_state_params_types_and_invariants(self) -> None:
        cleave_p = CleaveStateParams(ratio=ExactRatio(27, 50))
        assert cleave_p.ratio == ExactRatio(27, 50)

        chain_p = ChainStateParams(ratio=ExactRatio(1, 5))
        assert chain_p.ratio == ExactRatio(1, 5)

        share_p = DamageShareStateParams(sharer_id="u2", ratio=ExactRatio(3, 20))
        assert share_p.sharer_id == "u2"
        assert share_p.ratio == ExactRatio(3, 20)

        dist_p = DistributionStateParams(ratio=ExactRatio(1, 2))
        assert dist_p.ratio == ExactRatio(1, 2)

        taunt_p = TauntStateParams(taunt_target_id="u3")
        assert taunt_p.taunt_target_id == "u3"

        guard_p = GuardStateParams(guarded_unit_id="u4")
        assert guard_p.guarded_unit_id == "u4"

        ctr_p = CounterStateParams(damage_rate=ExactRatio(1, 1))
        assert ctr_p.damage_rate == ExactRatio(1, 1)

        combo_p = ComboStateParams()
        assert isinstance(combo_p, ComboStateParams)

        # Negative ratio rejected
        with pytest.raises(ValueError):
            CleaveStateParams(ratio=ExactRatio(-1, 2))
        with pytest.raises(ValueError):
            ChainStateParams(ratio=ExactRatio(-1, 2))
        with pytest.raises(ValueError):
            DamageShareStateParams(sharer_id="u2", ratio=ExactRatio(-1, 2))
        with pytest.raises(ValueError):
            DistributionStateParams(ratio=ExactRatio(-1, 2))
        with pytest.raises(ValueError):
            CounterStateParams(damage_rate=ExactRatio(-1, 2))
