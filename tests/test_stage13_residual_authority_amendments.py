from __future__ import annotations

from sgs_v2.battle_core.damage_partition_system import (
    DistributionRuntimeAuthority,
    DistributionTransactionPlan,
)
from sgs_v2.battle_core.stage11_state_runtime import (
    SeeThroughEligibility,
    Stage11DamageFamily,
    Stage11StateRuntime,
)


def test_690221_active_skill_and_periodic_damage_are_applicable() -> None:
    assert (
        Stage11StateRuntime.see_through_eligibility(Stage11DamageFamily.ACTIVE_SKILL)
        is SeeThroughEligibility.SUPPORTED_APPLICABLE
    )
    assert (
        Stage11StateRuntime.see_through_eligibility(Stage11DamageFamily.PERIODIC_DAMAGE)
        is SeeThroughEligibility.SUPPORTED_APPLICABLE
    )


def test_690099_alert_threshold_is_six_percent_of_max_carry_and_inclusive() -> None:
    assert Stage11StateRuntime.alert_threshold(10_000) == 600.0
    assert Stage11StateRuntime.alert_threshold_satisfied(599.0, 10_000) is False
    assert Stage11StateRuntime.alert_threshold_satisfied(600.0, 10_000) is True
    assert Stage11StateRuntime.alert_threshold_satisfied(601.0, 10_000) is True
    assert Stage11StateRuntime.alert_threshold(8_000) == 480.0
    assert Stage11StateRuntime.alert_threshold_satisfied(480.0, 8_000) is True


def test_690086_distribution_transaction_authority_is_frozen_p0() -> None:
    field = DistributionTransactionPlan.__dataclass_fields__["runtime_authority"]
    assert field.default is DistributionRuntimeAuthority.FROZEN_P0
