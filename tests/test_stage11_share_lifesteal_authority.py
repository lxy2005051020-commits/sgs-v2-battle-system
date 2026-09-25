from __future__ import annotations

import pytest

from sgs_v2.battle_core import (
    BattleContext,
    BattleSystems,
    DamageRequest,
    DamageResult,
    DamageSourceType,
    DamageType,
    EventBus,
    EventType,
    LineupPosition,
    OfficialStateId,
    RandomSystem,
    UnitRuntime,
    register_official_state_definitions,
)
from sgs_v2.battle_core.operation_identity import OperationLineage, SourceType
from sgs_v2.battle_core.recovery_system import RecoveryRequest
from sgs_v2.battle_core.stage9_integerization import ExactRatio
from sgs_v2.battle_core.stage9_state_params import DamageShareStateParams
from sgs_v2.battle_core.stage11_state_params import LifeStealStateParams


def make_context() -> BattleContext:
    units = {}
    for side in ("a", "b"):
        for n, pos in enumerate(LineupPosition):
            uid = f"{side}{n}"
            units[uid] = UnitRuntime(
                uid,
                uid,
                side,
                10000,
                5000,
                200,
                150,
                100,
                lineup_position=pos,
                intelligence=180,
            )
    ctx = BattleContext(
        "stage11-share-lifesteal-authority",
        units,
        EventBus(),
        RandomSystem(20260925),
    )
    register_official_state_definitions(ctx.states)
    return ctx


def apply_share(ctx: BattleContext, systems: BattleSystems, *, target: str, sharer: str) -> None:
    systems.state_lifecycle_system.apply(
        ctx,
        state_id=OfficialStateId.DAMAGE_SHARE.value,
        owner_id=target,
        source_id=sharer,
        source_skill_id="share-source",
        runtime_params=DamageShareStateParams(sharer, ExactRatio(15, 100)),
    )


def apply_lifesteal(
    ctx: BattleContext,
    systems: BattleSystems,
    *,
    damage_type: DamageType,
) -> None:
    state_id = (
        OfficialStateId.WEAPON_LIFESTEAL
        if damage_type is DamageType.WEAPON
        else OfficialStateId.STRATEGY_LIFESTEAL
    )
    systems.state_lifecycle_system.apply(
        ctx,
        state_id=state_id.value,
        owner_id="a0",
        source_id="a0",
        source_skill_id="lifesteal-source",
        runtime_params=LifeStealStateParams(ExactRatio(1, 10)),
    )


def execute_fixed_share(
    monkeypatch: pytest.MonkeyPatch,
    ctx: BattleContext,
    systems: BattleSystems,
    *,
    target: str,
    damage_type: DamageType = DamageType.WEAPON,
    amount: int = 314,
):
    def calculate(_ctx, request):
        return DamageResult(
            request.source_id,
            request.target_id,
            request.damage_type,
            request.source_type,
            request.coefficient,
            amount,
            amount,
            amount,
            source_skill_id=request.source_skill_id,
        )

    monkeypatch.setattr(systems.damage_system, "calculate", calculate)
    request = DamageRequest(
        source_id="a0",
        target_id=target,
        damage_type=damage_type,
        source_type=DamageSourceType.SKILL,
        coefficient=1.0,
        source_skill_id="fixed-damage",
    )
    lineage = OperationLineage(
        root_action_id=ctx.id_allocator.allocate_action_id(),
        parent_normal_attack_id=None,
        parent_damage_instance_id=None,
        source_type=SourceType.ACTIVE_SKILL,
        physical_attacker="a0",
        physical_skill="fixed-damage",
        credit_owner="a0",
    )
    return systems.damage_instance_coordinator.execute_partitioned_damage_instance(
        ctx,
        request,
        lineage,
    )


def recovery_events(ctx: BattleContext):
    return [
        event for event in ctx.event_bus.history
        if event.event_type is EventType.TROOPS_RECOVERED
    ]


def prevented_recovery_events(ctx: BattleContext):
    return [
        event for event in ctx.event_bus.history
        if event.event_type is EventType.RECOVERY_PREVENTED
    ]


def test_share_nonlethal_recovery_basis_is_partition_assignment_sum(monkeypatch) -> None:
    ctx, systems = make_context(), BattleSystems()
    ctx.units["a0"].troops = 4000
    apply_share(ctx, systems, target="b2", sharer="b1")
    apply_lifesteal(ctx, systems, damage_type=DamageType.WEAPON)

    execution = execute_fixed_share(monkeypatch, ctx, systems, target="b2")

    plan = execution.partition_plan
    assert plan.primary_assigned_damage == 267
    assert plan.shared_assigned_damage == 47
    assert plan.attacker_recovery_basis == 314
    assert execution.resolution.actual_target_troop_loss == 267
    assert sum(loss.actual_loss for loss in execution.direct_losses) == 47

    events = recovery_events(ctx)
    assert len(events) == 1
    assert events[0].payload["requested_recovery"] == 32
    assert events[0].payload["actual_recovery"] == 32
    assert ctx.units["a0"].troops == 4032


def test_share_target_death_interrupt_does_not_shrink_recovery_basis(monkeypatch) -> None:
    ctx, systems = make_context(), BattleSystems()
    ctx.units["a0"].troops = 4000
    ctx.units["b2"].troops = 55
    apply_share(ctx, systems, target="b2", sharer="b1")
    apply_lifesteal(ctx, systems, damage_type=DamageType.WEAPON)

    execution = execute_fixed_share(monkeypatch, ctx, systems, target="b2")

    plan = execution.partition_plan
    assert plan.primary_assigned_damage == 267
    assert plan.shared_assigned_damage == 47
    assert plan.attacker_recovery_basis == 314
    assert execution.resolution.actual_target_troop_loss == 55
    assert execution.direct_losses == ()
    assert ctx.units["b1"].troops == 5000

    events = recovery_events(ctx)
    assert len(events) == 1
    assert events[0].payload["requested_recovery"] == 32


def test_share_both_capacities_below_assignment_keeps_basis_and_target_death_cancels_sharer(monkeypatch) -> None:
    ctx, systems = make_context(), BattleSystems()
    ctx.units["a0"].troops = 4000
    ctx.units["b2"].troops = 55
    ctx.units["b1"].troops = 10
    apply_share(ctx, systems, target="b2", sharer="b1")
    apply_lifesteal(ctx, systems, damage_type=DamageType.WEAPON)

    execution = execute_fixed_share(monkeypatch, ctx, systems, target="b2")

    plan = execution.partition_plan
    assert plan.primary_assigned_damage == 267
    assert plan.shared_assigned_damage == 47
    assert plan.attacker_recovery_basis == 314
    assert execution.resolution.actual_target_troop_loss == 55
    # Frozen target-first death interrupt cancels the pending sharer settlement,
    # even though the sharer also lacks capacity for its 47 assigned damage.
    assert execution.direct_losses == ()
    assert ctx.units["b1"].troops == 10
    events = recovery_events(ctx)
    assert len(events) == 1
    assert events[0].payload["requested_recovery"] == 32


def test_share_receiver_overkill_uses_shared_assignment_not_actual_loss(monkeypatch) -> None:
    ctx, systems = make_context(), BattleSystems()
    ctx.units["a0"].troops = 4000
    ctx.units["b1"].troops = 10
    apply_share(ctx, systems, target="b2", sharer="b1")
    apply_lifesteal(ctx, systems, damage_type=DamageType.WEAPON)

    execution = execute_fixed_share(monkeypatch, ctx, systems, target="b2")

    plan = execution.partition_plan
    assert plan.shared_assigned_damage == 47
    assert len(execution.direct_losses) == 1
    assert execution.direct_losses[0].actual_loss == 10
    assert plan.attacker_recovery_basis == 314

    events = recovery_events(ctx)
    assert len(events) == 1
    assert events[0].payload["requested_recovery"] == 32


def test_share_recovery_capacity_caps_actual_recovery_not_basis(monkeypatch) -> None:
    ctx, systems = make_context(), BattleSystems()
    ctx.units["a0"].troops = 9990
    apply_share(ctx, systems, target="b2", sharer="b1")
    apply_lifesteal(ctx, systems, damage_type=DamageType.WEAPON)

    execution = execute_fixed_share(monkeypatch, ctx, systems, target="b2")

    assert execution.partition_plan.attacker_recovery_basis == 314
    event, = recovery_events(ctx)
    assert event.payload["requested_recovery"] == 32
    assert event.payload["actual_recovery"] == 10
    assert ctx.units["a0"].troops == 10000


def test_healing_block_intercepts_positive_share_recovery_request(monkeypatch) -> None:
    ctx, systems = make_context(), BattleSystems()
    ctx.units["a0"].troops = 4000
    apply_share(ctx, systems, target="b2", sharer="b1")
    apply_lifesteal(ctx, systems, damage_type=DamageType.WEAPON)
    systems.state_lifecycle_system.apply(
        ctx,
        state_id=OfficialStateId.HEALING_BAN.value,
        owner_id="a0",
        source_id="b0",
        source_skill_id="healing-ban-source",
    )

    execution = execute_fixed_share(monkeypatch, ctx, systems, target="b2")

    assert execution.partition_plan.attacker_recovery_basis == 314
    assert recovery_events(ctx) == []
    event, = prevented_recovery_events(ctx)
    assert event.payload["requested_recovery"] == 32
    assert event.payload["reason_state_id"] == OfficialStateId.HEALING_BAN.value
    assert ctx.units["a0"].troops == 4000


def test_strategy_lifesteal_mirrors_assigned_share_basis(monkeypatch) -> None:
    ctx, systems = make_context(), BattleSystems()
    ctx.units["a0"].troops = 4000
    ctx.units["b1"].troops = 10
    apply_share(ctx, systems, target="b2", sharer="b1")
    apply_lifesteal(ctx, systems, damage_type=DamageType.STRATEGY)

    execution = execute_fixed_share(
        monkeypatch,
        ctx,
        systems,
        target="b2",
        damage_type=DamageType.STRATEGY,
    )

    assert execution.partition_plan.attacker_recovery_basis == 314
    event, = recovery_events(ctx)
    assert event.payload["source_state_id"] == OfficialStateId.STRATEGY_LIFESTEAL.value
    assert event.payload["requested_recovery"] == 32


def test_share_creates_one_lifesteal_opportunity_not_one_per_direct_loss(monkeypatch) -> None:
    ctx, systems = make_context(), BattleSystems()
    ctx.units["a0"].troops = 4000
    apply_share(ctx, systems, target="b2", sharer="b1")
    apply_lifesteal(ctx, systems, damage_type=DamageType.WEAPON)

    execution = execute_fixed_share(monkeypatch, ctx, systems, target="b2")

    assert len(execution.direct_losses) == 1
    assert len(recovery_events(ctx)) == 1


def test_recovery_modifier_owner_uses_second_stage_ceil() -> None:
    ctx, systems = make_context(), BattleSystems()
    ctx.units["a0"].troops = 4000

    # Demonstrates the required difference:
    # ceil(5 * 1/2) = 3, then ceil(3 * 3/2) = 5.
    # One combined ceil(5 * 1/2 * 3/2) would be only 4.
    base_recovery = (5 + 2 - 1) // 2
    assert base_recovery == 3

    result = systems.recovery_system.resolve(
        ctx,
        RecoveryRequest(
            source_id="a0",
            target_id="a0",
            amount=base_recovery,
            healing_modifier=ExactRatio(3, 2),
        ),
    )

    assert result.request.amount == 5
    assert result.actual_recovery == 5
    assert ctx.units["a0"].troops == 4005
