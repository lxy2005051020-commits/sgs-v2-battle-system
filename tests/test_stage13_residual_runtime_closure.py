from __future__ import annotations

import pytest

from sgs_v2.battle_core import (
    BattleContext,
    BattleSystems,
    DamageRequest,
    DamageSourceType,
    DamageType,
    EventBus,
    ExactRatio,
    LineupPosition,
    OfficialStateId,
    RandomSystem,
    RecoveryModelKind,
    RecoveryOpportunity,
    RecoveryOpportunityKind,
    RecoveryPotencyContext,
    RuleIntentExecutionDescriptor,
    RuleIntentKind,
    UnitRuntime,
    register_official_state_definitions,
)
from sgs_v2.battle_core.damage_partition_system import (
    DistributionRuntimeAuthority,
    DistributionTransactionPlan,
)
from sgs_v2.battle_core.operation_identity import (
    DamageInstanceId,
    OperationLineage,
    PartitionTransactionId,
    SourceType,
)
from sgs_v2.battle_core.stage9_state_params import DistributionStateParams
from sgs_v2.battle_core.stage11_state_params import (
    AlertStateParams,
    DamageReductionPierceStateParams,
)
from sgs_v2.battle_core.stage11_state_runtime import Stage11DamageFamily


def _unit(
    unit_id: str,
    team_id: str,
    *,
    troops: int = 1000,
    max_troops: int = 1000,
    lineup_position: LineupPosition = LineupPosition.COMMANDER,
    wounded_troops: int | None = None,
) -> UnitRuntime:
    return UnitRuntime(
        unit_id=unit_id,
        name=unit_id,
        team_id=team_id,
        max_troops=max_troops,
        troops=troops,
        attack=800,
        defense=100,
        speed=100,
        intelligence=300,
        lineup_position=lineup_position,
        wounded_troops=wounded_troops,
    )


def _context(units: dict[str, UnitRuntime], seed: int = 7) -> BattleContext:
    context = BattleContext(
        battle_id="stage13-residual-runtime-closure",
        units=units,
        event_bus=EventBus(),
        random=RandomSystem(seed),
    )
    register_official_state_definitions(context.states)
    return context


def test_see_through_applies_to_active_skill_and_periodic_damage() -> None:
    systems = BattleSystems()
    context = _context(
        {
            "a": _unit("a", "A"),
            "b": _unit("b", "B"),
        }
    )
    systems.state_lifecycle_system.apply(
        context,
        state_id=OfficialStateId.DAMAGE_REDUCTION_PIERCE.value,
        owner_id="a",
        source_id="a",
        runtime_params=DamageReductionPierceStateParams(rate=0.5),
    )

    assert systems.stage11_state_runtime.see_through_rate(
        context, "a", Stage11DamageFamily.ACTIVE_SKILL
    ) == pytest.approx(0.5)
    assert systems.stage11_state_runtime.see_through_rate(
        context, "a", Stage11DamageFamily.PERIODIC_DAMAGE
    ) == pytest.approx(0.5)


def test_alert_threshold_is_max_carry_six_percent_and_equality_triggers() -> None:
    systems = BattleSystems()
    context = _context(
        {
            "a": _unit("a", "A"),
            "b": _unit("b", "B", troops=10000, max_troops=10000),
        }
    )
    instance = systems.state_lifecycle_system.apply(
        context,
        state_id=OfficialStateId.VIGILANCE.value,
        owner_id="b",
        source_id="b",
        runtime_params=AlertStateParams(
            remaining_uses=2,
            reduction_rate=ExactRatio(1, 2),
            # Deliberately contradictory legacy value: runtime must ignore it.
            threshold=9999,
        ),
    )

    below = systems.stage11_state_runtime.adjust_alert(
        context,
        target_id="b",
        candidate_damage=599.0,
    )
    assert below.output_damage == pytest.approx(599.0)
    assert below.consumed_instance_id is None
    assert context.states.get(instance.instance_id).runtime_params.remaining_uses == 2

    equal = systems.stage11_state_runtime.adjust_alert(
        context,
        target_id="b",
        candidate_damage=600.0,
    )
    assert equal.output_damage == pytest.approx(300.0)
    assert equal.consumed_instance_id == instance.instance_id
    assert context.states.get(instance.instance_id).runtime_params.remaining_uses == 1


def test_alert_threshold_scales_with_non_10000_max_carry() -> None:
    systems = BattleSystems()
    context = _context(
        {
            "a": _unit("a", "A"),
            "b": _unit("b", "B", troops=5000, max_troops=5000),
        }
    )
    systems.state_lifecycle_system.apply(
        context,
        state_id=OfficialStateId.VIGILANCE.value,
        owner_id="b",
        source_id="b",
        runtime_params=AlertStateParams(
            remaining_uses=1,
            reduction_rate=ExactRatio(1, 2),
            threshold=600,
        ),
    )

    result = systems.stage11_state_runtime.adjust_alert(
        context,
        target_id="b",
        candidate_damage=300.0,
    )
    assert result.output_damage == pytest.approx(150.0)
    assert result.consumed_instance_id is not None


def test_distribution_default_authority_is_frozen_p0() -> None:
    plan = DistributionTransactionPlan(
        partition_transaction_id=PartitionTransactionId("part_1"),
        parent_damage_instance_id=DamageInstanceId("dmg_1"),
        target_id="target",
        participant_ids=("commander", "deputy"),
        participant_count=2,
        dtotal=100,
        ratio=ExactRatio(1, 2),
        dtarget=50,
        dtransfer=50,
        dparticipant=25,
    )
    assert plan.runtime_authority is DistributionRuntimeAuthority.FROZEN_P0


def test_commander_participant_death_does_not_abort_distribution_transaction() -> None:
    systems = BattleSystems(
        weapon_random_percent_range=(90, 90),
        weapon_low_damage_floor_range=(5, 5),
    )
    context = _context(
        {
            "attacker": _unit("attacker", "A", troops=1000),
            "commander": _unit(
                "commander",
                "B",
                troops=1,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "target": _unit(
                "target",
                "B",
                troops=1000,
                lineup_position=LineupPosition.DEPUTY_1,
            ),
            "deputy": _unit(
                "deputy",
                "B",
                troops=1000,
                lineup_position=LineupPosition.DEPUTY_2,
            ),
        }
    )
    systems.state_lifecycle_system.apply(
        context,
        state_id=OfficialStateId.DAMAGE_SPLIT.value,
        owner_id="target",
        source_id="target",
        runtime_params=DistributionStateParams(ratio=ExactRatio(1, 2)),
    )

    before_deputy = context.get_unit("deputy").troops
    before_target = context.get_unit("target").troops
    request = DamageRequest(
        source_id="attacker",
        target_id="target",
        damage_type=DamageType.WEAPON,
        source_type=DamageSourceType.SKILL,
        coefficient=1.0,
    )
    lineage = OperationLineage(
        root_action_id=None,
        parent_normal_attack_id=None,
        parent_damage_instance_id=None,
        source_type=SourceType.ACTIVE_SKILL,
        physical_attacker="attacker",
        physical_skill="distribution-test",
        credit_owner="attacker",
    )

    execution = systems.damage_instance_coordinator.execute_partitioned_damage_instance(
        context,
        request,
        lineage,
    )

    assert context.get_unit("commander").troops == 0
    # The commander death latched victory, but the already-admitted distribution
    # still drained the later participant and the original target.
    assert context.get_unit("deputy").troops < before_deputy
    assert context.get_unit("target").troops < before_target
    assert len(execution.direct_losses) == 2
    assert isinstance(execution.partition_plan, DistributionTransactionPlan)
    assert execution.partition_plan.runtime_authority is DistributionRuntimeAuthority.FROZEN_P0


def test_special_resolved_recovery_bypasses_ordinary_treatment_formula() -> None:
    systems = BattleSystems()
    context = _context(
        {
            "source": _unit("source", "A"),
            "target": _unit(
                "target",
                "A",
                troops=500,
                max_troops=1000,
                wounded_troops=500,
                lineup_position=LineupPosition.DEPUTY_1,
            ),
        }
    )
    opportunity = RecoveryOpportunity(
        opportunity_kind=RecoveryOpportunityKind.RECUPERATION_ACTION_START,
        execution_descriptor=RuleIntentExecutionDescriptor(
            intent_kind=RuleIntentKind.RECOVERY_OPPORTUNITY,
            intent_owner_id="target",
            target_id="target",
        ),
        probability=1.0,
        recovery_model_kind=RecoveryModelKind.RESOLVED_SPECIAL_AMOUNT,
        # base_rate is intentionally unusable as an ordinary treatment snapshot.
        # The special-family lane must ignore it and consume only treatment_amount.
        recovery_potency_context=RecoveryPotencyContext(
            base_rate=99.0,
            treatment_amount=123,
        ),
        aftermath_fact=None,
    )

    result = systems.recovery_opportunity_system.execute(context, opportunity)

    assert result.executed is True
    assert result.resolution is not None
    assert result.resolution.request.amount == 123
    assert result.resolution.actual_recovery == 123
    assert context.get_unit("target").troops == 623
