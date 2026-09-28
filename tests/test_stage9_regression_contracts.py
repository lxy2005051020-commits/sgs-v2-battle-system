from __future__ import annotations

import pytest

from sgs_v2.battle_core.stage9_integerization import (
    ExactRatio,
    floor_product_int_ratio,
    round_half_up_divide_int,
    round_half_up_product_int_ratio,
)


class TestStage9RegressionContractsIntegerization:
    """Executable regression vectors from STAGE9_REGRESSION_CONTRACTS.md (Section I).

    These are frozen exact vectors, not language built-in round() results.
    """

    def test_reg_int_01_chain_uses_floor(self) -> None:
        """REG-INT-01 — Chain uses FLOOR.

        Given TriggerNodeResolvedDamage=396, ChainRatio=28.28%.
        When Chain value is integerized.
        Then 396×0.2828=111.9888 → 111.
        """
        trigger_damage = 396
        chain_ratio = ExactRatio.from_text("28.28%")
        assert chain_ratio == ExactRatio(707, 2500)

        result = floor_product_int_ratio(trigger_damage, chain_ratio)
        assert result == 111

    def test_reg_int_02_share_uses_round_half_up(self) -> None:
        """REG-INT-02 — Share uses ROUND_HALF_UP.

        Given Dtotal=470, R=15%.
        When Share partitions.
        Then 470×0.15=70.5 → Dsharer_theoretical=71, Dtarget=399.
        """
        d_total = 470
        share_ratio = ExactRatio.from_text("15%")
        assert share_ratio == ExactRatio(3, 20)

        d_sharer_theoretical = round_half_up_product_int_ratio(d_total, share_ratio)
        assert d_sharer_theoretical == 71

        d_target = d_total - d_sharer_theoretical
        assert d_target == 399

    def test_reg_int_03_distribution_target_uses_round_half_up(self) -> None:
        """REG-INT-03 — Distribution target uses ROUND_HALF_UP.

        Given Dtotal=251, R=50%.
        When Distribution computes target share.
        Then 251×0.5=125.5 → Dtarget=126, Dtransfer=125.
        """
        d_total = 251
        dist_ratio = ExactRatio.from_text("50%")
        assert dist_ratio == ExactRatio(1, 2)

        # In Distribution: Dtarget = round_half_up(Dtotal * (1 - ratio))
        # When ratio = 50%, 1 - ratio = 50%
        one_minus_ratio = ExactRatio(1, 2)
        d_target = round_half_up_product_int_ratio(d_total, one_minus_ratio)
        assert d_target == 126

        d_transfer = d_total - d_target
        assert d_transfer == 125

    def test_reg_int_04_distribution_participant_uses_round_half_up(self) -> None:
        """REG-INT-04 — Distribution participant uses ROUND_HALF_UP.

        Given Dtransfer=353, N=2.
        When participant amount is computed.
        Then 353/2=176.5 → Dparticipant=177 for each planned participant; no last-participant remainder repair is added.
        """
        d_transfer = 353
        n = 2

        d_participant = round_half_up_divide_int(d_transfer, n)
        assert d_participant == 177

    def test_reg_int_05_cleave_uses_floor(self) -> None:
        """REG-INT-05 — Cleave uses FLOOR.

        Given ActualTargetTroopLoss=55, CleaveRatio=54%.
        When Cleave derives calculated damage.
        Then 55×0.54=29.7 → 29.
        """
        actual_loss = 55
        cleave_ratio = ExactRatio.from_text("54%")
        assert cleave_ratio == ExactRatio(27, 50)

        derived_calculated = floor_product_int_ratio(actual_loss, cleave_ratio)
        assert derived_calculated == 29


class TestStage9RegressionContractsTargetArbitration:
    """Executable regression vectors from STAGE9_REGRESSION_CONTRACTS.md (Section A: Target Arbitration).

    REG-TGT-01..04 are active Phase 9.3 contracts.
    REG-TGT-05..07 are reserved for Phase 9.6 / 9.7.
    """

    def test_reg_tgt_01_confusion_shadows_taunt_selector(self) -> None:
        """REG-TGT-01 — Confusion shadows Taunt selector."""
        from test_stage9_phase_9_3_target_resolution import (
            TestTargetResolutionArbitration,
        )
        TestTargetResolutionArbitration().test_reg_tgt_01_confusion_shadows_taunt_selector()

    def test_reg_tgt_02_taunt_lifecycle_continues_while_selector_is_shadowed(self) -> None:
        """REG-TGT-02 — Taunt lifecycle continues while selector is shadowed."""
        from test_stage9_phase_9_3_target_resolution import (
            TestTargetResolutionArbitration,
        )
        TestTargetResolutionArbitration().test_reg_tgt_02_taunt_lifecycle_continues_while_selector_is_shadowed()

    def test_reg_tgt_03_guard_occurs_after_selector(self) -> None:
        """REG-TGT-03 — Guard occurs after selector."""
        from test_stage9_phase_9_3_target_resolution import (
            TestTargetResolutionArbitration,
        )
        TestTargetResolutionArbitration().test_reg_tgt_03_guard_occurs_after_selector()

    def test_reg_tgt_04_guard_is_single_pass(self) -> None:
        """REG-TGT-04 — Guard is single-pass."""
        from test_stage9_phase_9_3_target_resolution import (
            TestTargetResolutionArbitration,
        )
        TestTargetResolutionArbitration().test_reg_tgt_04_guard_is_single_pass()

