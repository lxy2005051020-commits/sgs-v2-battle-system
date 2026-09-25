from __future__ import annotations

from types import SimpleNamespace

from sgs_v2.battle_core import (
    BattleContext,
    BattleSystems,
    DamageType,
    EventBus,
    LineupPosition,
    OfficialStateId,
    RandomSystem,
    UnitRuntime,
    register_official_state_definitions,
)
from sgs_v2.battle_core.damage_partition_system import DamageShareTransactionPlan
from sgs_v2.battle_core.operation_identity import (
    DamageInstanceId,
    OperationLineage,
    PartitionTransactionId,
    SourceType,
)
from sgs_v2.battle_core.recovery_system import RecoveryPreventedResult, RecoveryResolvedResult
from sgs_v2.battle_core.stage9_integerization import ExactRatio
from sgs_v2.battle_core.stage11_state_params import LifeStealStateParams


def _unit(
    unit_id: str,
    team: str,
    troops: int = 1000,
    lineup_position: LineupPosition = LineupPosition.COMMANDER,
) -> UnitRuntime:
    return UnitRuntime(
        unit_id=unit_id,
        name=unit_id,
        team_id=team,
        max_troops=1000,
        troops=troops,
        attack=100,
        defense=100,
        intelligence=100,
        speed=100,
        lineup_position=lineup_position,
    )


def _context(attacker_troops: int = 500) -> tuple[BattleContext, BattleSystems]:
    context = BattleContext(
        battle_id="stage11-share-lifesteal-resolution",
        units={
            "a": _unit("a", "A", attacker_troops),
            "b": _unit("b", "B", 1000),
            "c": _unit("c", "B", 1000, LineupPosition.DEPUTY_1),
        },
        event_bus=EventBus(),
        random=RandomSystem(20260926),
    )
    register_official_state_definitions(context.states)
    return context, BattleSystems()


def _lifesteal(
    context: BattleContext,
    systems: BattleSystems,
    state_id: OfficialStateId,
    ratio: ExactRatio = ExactRatio(1, 10),
) -> None:
    systems.state_lifecycle_system.apply(
        context,
        state_id=state_id.value,
        owner_id="a",
        source_id="a",
        source_skill_id=f"{state_id.value}-source",
        runtime_params=LifeStealStateParams(ratio=ratio),
    )


def _share_plan(dtotal: int = 100, dtarget: int = 60) -> DamageShareTransactionPlan:
    return DamageShareTransactionPlan(
        partition_transaction_id=PartitionTransactionId("part_1"),
        parent_damage_instance_id=DamageInstanceId("dmg_1"),
        target_id="b",
        sharer_id="c",
        dtotal=dtotal,
        ratio=ExactRatio(dtotal - dtarget, dtotal),
        dsharer_theoretical=dtotal - dtarget,
        dtarget=dtarget,
    )


def _lineage() -> OperationLineage:
    return OperationLineage(
        root_action_id=None,
        parent_normal_attack_id=None,
        parent_damage_instance_id=None,
        source_type=SourceType.ACTIVE_SKILL,
        physical_attacker="a",
        physical_skill="skill",
        credit_owner="a",
    )


def _resolve(
    systems: BattleSystems,
    context: BattleContext,
    *,
    damage_type: DamageType = DamageType.WEAPON,
    actual_primary: int,
    actual_shared: int | None,
    dtotal: int = 100,
    dtarget: int = 60,
):
    direct_losses = (
        ()
        if actual_shared is None
        else (SimpleNamespace(actual_loss=actual_shared),)
    )
    return systems.stage11_attacker_recovery_system.resolve_parent_damage(
        context,
        lineage=_lineage(),
        damage_result=SimpleNamespace(target_id="b", damage_type=damage_type),
        resolution=SimpleNamespace(actual_target_troop_loss=actual_primary),
        partition_plan=_share_plan(dtotal=dtotal, dtarget=dtarget),
        direct_losses=direct_losses,
    )


def test_share_normal_nonlethal_uses_assigned_partition_sum_and_single_trigger() -> None:
    context, systems = _context()
    _lifesteal(context, systems, OfficialStateId.WEAPON_LIFESTEAL)

    resolved = _resolve(systems, context, actual_primary=60, actual_shared=40)

    assert resolved.basis == 100
    assert len(resolved.results) == 1
    result = resolved.results[0]
    assert isinstance(result, RecoveryResolvedResult)
    assert result.request.amount == 10
    assert result.actual_recovery == 10


def test_share_target_death_interrupt_does_not_shrink_recovery_basis() -> None:
    context, systems = _context()
    _lifesteal(context, systems, OfficialStateId.WEAPON_LIFESTEAL)

    resolved = _resolve(systems, context, actual_primary=20, actual_shared=None)

    assert resolved.basis == 100
    result = resolved.results[0]
    assert isinstance(result, RecoveryResolvedResult)
    assert result.request.amount == 10


def test_share_receiver_and_both_side_overkill_do_not_shrink_recovery_basis() -> None:
    context, systems = _context()
    _lifesteal(context, systems, OfficialStateId.WEAPON_LIFESTEAL)

    receiver_overkill = _resolve(
        systems, context, actual_primary=60, actual_shared=5
    )
    assert receiver_overkill.basis == 100

    context.get_unit("a").troops = 500
    both_overkill = _resolve(
        systems, context, actual_primary=10, actual_shared=5
    )
    assert both_overkill.basis == 100


def test_share_lifesteal_ceil_and_recovery_capacity_are_separate_owners() -> None:
    context, systems = _context(attacker_troops=997)
    _lifesteal(context, systems, OfficialStateId.WEAPON_LIFESTEAL)

    resolved = _resolve(
        systems,
        context,
        actual_primary=61,
        actual_shared=40,
        dtotal=101,
        dtarget=61,
    )

    assert resolved.basis == 101
    result = resolved.results[0]
    assert isinstance(result, RecoveryResolvedResult)
    assert result.request.amount == 11  # CEIL(101 * 10%)
    assert result.actual_recovery == 3  # capacity owner caps only the commit


def test_healing_block_intercepts_positive_request_without_zeroing_basis() -> None:
    context, systems = _context()
    _lifesteal(context, systems, OfficialStateId.WEAPON_LIFESTEAL)
    systems.state_lifecycle_system.apply(
        context,
        state_id=OfficialStateId.HEALING_BAN.value,
        owner_id="a",
        source_id="b",
    )

    before = context.get_unit("a").troops
    resolved = _resolve(systems, context, actual_primary=60, actual_shared=40)

    assert resolved.basis == 100
    result = resolved.results[0]
    assert isinstance(result, RecoveryPreventedResult)
    assert result.request.amount == 10
    assert result.reason_state_id == OfficialStateId.HEALING_BAN.value
    assert context.get_unit("a").troops == before


def test_strategy_lifesteal_mirrors_assigned_share_basis_by_damage_lane() -> None:
    context, systems = _context()
    _lifesteal(context, systems, OfficialStateId.WEAPON_LIFESTEAL)
    _lifesteal(context, systems, OfficialStateId.STRATEGY_LIFESTEAL)

    resolved = _resolve(
        systems,
        context,
        damage_type=DamageType.STRATEGY,
        actual_primary=60,
        actual_shared=5,
    )

    assert resolved.basis == 100
    assert len(resolved.results) == 1
    result = resolved.results[0]
    assert isinstance(result, RecoveryResolvedResult)
    assert result.request.source_state_id == OfficialStateId.STRATEGY_LIFESTEAL.value
    assert result.request.amount == 10
