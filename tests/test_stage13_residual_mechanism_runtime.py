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


def test_see_through_applies_to_active_skill_and_periodic_damage() -> None:
    assert (
        Stage11StateRuntime.see_through_eligibility(
            Stage11DamageFamily.ACTIVE_SKILL
        )
        is SeeThroughEligibility.SUPPORTED_APPLICABLE
    )
    assert (
        Stage11StateRuntime.see_through_eligibility(
            Stage11DamageFamily.PERIODIC_DAMAGE
        )
        is SeeThroughEligibility.SUPPORTED_APPLICABLE
    )


def test_alert_threshold_is_six_percent_of_max_carry_and_equality_is_eligible() -> None:
    threshold = Stage11StateRuntime.alert_threshold(10_000)
    assert threshold == 600.0
    assert 599 < threshold
    assert 600 >= threshold

    nonstandard = Stage11StateRuntime.alert_threshold(8_500)
    assert nonstandard == 510.0


def test_distribution_plan_authority_is_frozen_p0() -> None:
    field = DistributionTransactionPlan.__dataclass_fields__["runtime_authority"]
    assert field.default is DistributionRuntimeAuthority.FROZEN_P0
