from __future__ import annotations

import ast
import inspect
from pathlib import Path

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
    ExactRatio,
    LineupPosition,
    LoadedSkillRef,
    PeriodicDamageStateParams,
    RandomSystem,
    ROUND_START_TRIGGER_TAG,
    RoundStartHook,
    SkillDefinition,
    SkillRuntime,
    SkillSlot,
    SkillTargetMode,
    DamageSkillEffectSpec,
    SourceType,
    StateDefinition,
    StateInstance,
    TargetSystem,
    TriggerSystem,
    UnitRuntime,
    register_official_state_definitions,
)
from sgs_v2.battle_core.damage_instance_coordinator import PartitionExecutionStatus
from sgs_v2.battle_core.damage_partition_system import (
    DamagePartitionCoordinator,
    DamagePartitionKind,
    DamageShareTransactionPlan,
    DistributionTransactionPlan,
)
from sgs_v2.battle_core.direct_troop_loss_system import (
    DirectTroopLossRequest,
    DirectTroopLossResolver,
)
from sgs_v2.battle_core.execution_right_system import BattleTerminationState
from sgs_v2.battle_core.official_state_catalog import OfficialStateId
from sgs_v2.battle_core.operation_identity import OperationLineage
from sgs_v2.battle_core.stage9_state_params import (
    DamageShareStateParams,
    DistributionStateParams,
)


def _unit(
    unit_id: str,
    team_id: str,
    position: LineupPosition,
    *,
    troops: int = 1000,
) -> UnitRuntime:
    return UnitRuntime(
        unit_id,
        unit_id.upper(),
        team_id,
        1000,
        troops,
        300,
        100,
        100,
        lineup_position=position,
    )


def make_context(
    *,
    a_troops: tuple[int, ...] = (1000,),
    b_troops: tuple[int, ...] = (1000, 1000, 1000),
) -> BattleContext:
    positions = (
        LineupPosition.COMMANDER,
        LineupPosition.DEPUTY_1,
        LineupPosition.DEPUTY_2,
    )
    units: dict[str, UnitRuntime] = {}
    for index, troops in enumerate(a_troops, start=1):
        units[f"a{index}"] = _unit(
            f"a{index}", "A", positions[index - 1], troops=troops
        )
    for index, troops in enumerate(b_troops, start=1):
        units[f"b{index}"] = _unit(
            f"b{index}", "B", positions[index - 1], troops=troops
        )
    context = BattleContext(
        battle_id="stage9-phase95",
        units=units,
        event_bus=EventBus(),
        random=RandomSystem(95),
    )
    context.current_round = 1
    context.current_phase = "UNIT_ACTION"
    register_official_state_definitions(context.states)
    return context


def lineage() -> OperationLineage:
    return OperationLineage(
        root_action_id=None,
        parent_normal_attack_id=None,
        parent_damage_instance_id=None,
        source_type=SourceType.ACTIVE_SKILL,
        physical_attacker="a1",
        physical_skill="skill-95",
        credit_owner="a1",
    )


def request(target_id: str) -> DamageRequest:
    return DamageRequest(
        source_id="a1",
        target_id=target_id,
        damage_type=DamageType.WEAPON,
        source_type=DamageSourceType.SKILL,
        coefficient=1.0,
        source_skill_id="skill-95",
    )


def install_damage_result(
    monkeypatch: pytest.MonkeyPatch,
    systems: BattleSystems,
    *,
    final_damage: int,
    prevented: bool = False,
) -> list[DamageRequest]:
    calls: list[DamageRequest] = []

    def fake_calculate(context: BattleContext, req: DamageRequest) -> DamageResult:
        calls.append(req)
        return DamageResult(
            source_id=req.source_id,
            target_id=req.target_id,
            damage_type=req.damage_type,
            source_type=req.source_type,
            coefficient=req.coefficient,
            base_damage=float(final_damage),
            scaled_damage=float(final_damage),
            final_damage=final_damage,
            source_skill_id=req.source_skill_id,
            prevented=prevented,
            prevented_by_state_id="barrier" if prevented else None,
            source_state_id=req.source_state_id,
            source_state_instance_id=req.source_state_instance_id,
        )

    monkeypatch.setattr(systems.damage_system, "calculate", fake_calculate)
    return calls


def apply_share(
    context: BattleContext,
    systems: BattleSystems,
    *,
    target_id: str,
    sharer_id: str,
    ratio: ExactRatio,
) -> None:
    systems.state_lifecycle_system.apply(
        context,
        state_id=OfficialStateId.DAMAGE_SHARE.value,
        owner_id=target_id,
        source_id="a1",
        source_skill_id="share-skill",
        runtime_params=DamageShareStateParams(
            sharer_id=sharer_id,
            ratio=ratio,
        ),
    )


def apply_distribution(
    context: BattleContext,
    systems: BattleSystems,
    *,
    target_id: str,
    ratio: ExactRatio,
) -> None:
    systems.state_lifecycle_system.apply(
        context,
        state_id=OfficialStateId.DAMAGE_SPLIT.value,
        owner_id=target_id,
        source_id="a1",
        source_skill_id="distribution-skill",
        runtime_params=DistributionStateParams(ratio=ratio),
    )


def event_types(context: BattleContext) -> list[EventType]:
    return [event.event_type for event in context.event_bus.history]


# ---------------------------------------------------------------------------
# Share / exactly-one partition / integerization
# ---------------------------------------------------------------------------


def test_reg_int_02_and_reg_shr_01_share_target_first(monkeypatch: pytest.MonkeyPatch) -> None:
    context = make_context()
    systems = BattleSystems()
    apply_share(
        context,
        systems,
        target_id="b1",
        sharer_id="b2",
        ratio=ExactRatio(15, 100),
    )
    calls = install_damage_result(monkeypatch, systems, final_damage=470)

    before_target = context.get_unit("b1").troops
    before_sharer = context.get_unit("b2").troops
    result = systems.damage_instance_coordinator.execute_partitioned_damage_instance(
        context,
        request("b1"),
        lineage(),
    )

    assert len(calls) == 1
    assert isinstance(result.partition_plan, DamageShareTransactionPlan)
    assert result.partition_plan.dsharer_theoretical == 71
    assert result.partition_plan.dtarget == 399
    assert result.partition_plan.dtarget + result.partition_plan.dsharer_theoretical == 470
    assert result.resolution.damage.final_damage == 470
    assert result.resolution.assigned_target_damage == 399
    assert result.resolution.actual_target_troop_loss == 399
    assert context.get_unit("b1").troops == before_target - 399
    assert context.get_unit("b2").troops == before_sharer - 71
    assert len(result.direct_losses) == 1
    assert result.direct_losses[0].actual_loss == 71
    damage_index = event_types(context).index(EventType.DAMAGE_DEALT)
    direct_index = event_types(context).index(EventType.DIRECT_TROOP_LOSS)
    assert damage_index < direct_index


def test_reg_shr_02_and_fin_01_lethal_commander_discards_sharer_then_finalizes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = make_context(b_troops=(300, 1000, 1000))
    systems = BattleSystems()
    apply_share(
        context,
        systems,
        target_id="b1",
        sharer_id="b2",
        ratio=ExactRatio(15, 100),
    )
    install_damage_result(monkeypatch, systems, final_damage=470)
    before_sharer = context.get_unit("b2").troops

    result = systems.damage_instance_coordinator.execute_partitioned_damage_instance(
        context,
        request("b1"),
        lineage(),
    )

    assert result.partition_status is PartitionExecutionStatus.TARGET_DEATH_INTERRUPT
    assert result.resolution.target_defeated is True
    assert result.direct_losses == ()
    assert context.get_unit("b2").troops == before_sharer
    assert EventType.DIRECT_TROOP_LOSS not in event_types(context)
    assert systems.finalization_coordinator.termination_state is BattleTerminationState.FINALIZED
    assert systems.finalization_coordinator.active_damage_instance_ids == ()


def test_zero_amount_share_remains_real_share_transaction_and_direct_loss_fact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = make_context()
    systems = BattleSystems()
    apply_share(
        context,
        systems,
        target_id="b1",
        sharer_id="b2",
        ratio=ExactRatio(0, 1),
    )
    install_damage_result(monkeypatch, systems, final_damage=0)

    result = systems.damage_instance_coordinator.execute_partitioned_damage_instance(
        context,
        request("b1"),
        lineage(),
    )

    assert isinstance(result.partition_plan, DamageShareTransactionPlan)
    assert result.partition_plan.dsharer_theoretical == 0
    assert result.partition_plan.dtarget == 0
    assert len(result.direct_losses) == 1
    assert result.direct_losses[0].theoretical_loss == 0
    assert result.direct_losses[0].actual_loss == 0
    assert EventType.DIRECT_TROOP_LOSS in event_types(context)


def test_p95_ptn_01_corrupted_fixture_with_both_states_selects_share_only() -> None:
    context = make_context()
    systems = BattleSystems()
    apply_distribution(
        context,
        systems,
        target_id="b1",
        ratio=ExactRatio(1, 2),
    )
    share = StateInstance(
        instance_id=context.states.next_instance_id(),
        state_id=OfficialStateId.DAMAGE_SHARE.value,
        owner_id="b1",
        source_id="a1",
        source_skill_id="share-skill",
        applied_round=context.current_round,
        applied_phase=context.current_phase,
        runtime_params=DamageShareStateParams(
            sharer_id="b2",
            ratio=ExactRatio(1, 4),
        ),
    )
    context.states.add(share)
    damage_instance_id = context.id_allocator.allocate_damage_instance_id()
    damage = DamageResult(
        source_id="a1",
        target_id="b1",
        damage_type=DamageType.WEAPON,
        source_type=DamageSourceType.SKILL,
        coefficient=1.0,
        base_damage=100.0,
        scaled_damage=100.0,
        final_damage=100,
        source_skill_id="skill-95",
    )

    plan = systems.damage_partition_coordinator.plan(
        context, damage_instance_id, damage
    )

    assert isinstance(plan, DamageShareTransactionPlan)
    assert plan.kind is DamagePartitionKind.SHARE


def test_reg_shr_04_share_replaces_distribution_and_old_distribution_never_resurrects() -> None:
    context = make_context()
    systems = BattleSystems()
    apply_distribution(context, systems, target_id="b1", ratio=ExactRatio(1, 2))
    assert context.states.has(
        owner_id="b1", state_id=OfficialStateId.DAMAGE_SPLIT.value
    )

    apply_share(
        context,
        systems,
        target_id="b1",
        sharer_id="b2",
        ratio=ExactRatio(1, 4),
    )
    shares = context.states.find(
        owner_id="b1", state_id=OfficialStateId.DAMAGE_SHARE.value
    )
    assert len(shares) == 1
    assert not context.states.has(
        owner_id="b1", state_id=OfficialStateId.DAMAGE_SPLIT.value
    )

    systems.state_lifecycle_system.remove(context, shares[0].instance_id)
    assert not context.states.has(
        owner_id="b1", state_id=OfficialStateId.DAMAGE_SHARE.value
    )
    assert not context.states.has(
        owner_id="b1", state_id=OfficialStateId.DAMAGE_SPLIT.value
    )


def test_incoming_distribution_is_rejected_while_share_exists() -> None:
    context = make_context()
    systems = BattleSystems()
    apply_share(
        context,
        systems,
        target_id="b1",
        sharer_id="b2",
        ratio=ExactRatio(1, 4),
    )

    with pytest.raises(ValueError, match="DAMAGE_SHARE > DISTRIBUTION"):
        apply_distribution(context, systems, target_id="b1", ratio=ExactRatio(1, 2))

    assert context.states.has(
        owner_id="b1", state_id=OfficialStateId.DAMAGE_SHARE.value
    )
    assert not context.states.has(
        owner_id="b1", state_id=OfficialStateId.DAMAGE_SPLIT.value
    )


def test_p95_ptn_06_share_is_freshly_rechecked_for_each_damage_instance() -> None:
    context = make_context()
    systems = BattleSystems()
    apply_share(
        context,
        systems,
        target_id="b1",
        sharer_id="b2",
        ratio=ExactRatio(1, 4),
    )
    damage = DamageResult(
        source_id="a1",
        target_id="b1",
        damage_type=DamageType.WEAPON,
        source_type=DamageSourceType.SKILL,
        coefficient=1.0,
        base_damage=100.0,
        scaled_damage=100.0,
        final_damage=100,
        source_skill_id="skill-95",
    )
    first = systems.damage_partition_coordinator.plan(
        context, context.id_allocator.allocate_damage_instance_id(), damage
    )
    assert isinstance(first, DamageShareTransactionPlan)

    systems.troop_system.apply_damage(context.get_unit("b2"), context.get_unit("b2").troops)
    second = systems.damage_partition_coordinator.plan(
        context, context.id_allocator.allocate_damage_instance_id(), damage
    )
    assert second.kind is DamagePartitionKind.NONE


# ---------------------------------------------------------------------------
# Distribution fixed plan / integerization / finalization drain
# ---------------------------------------------------------------------------


def test_reg_int_03_distribution_target_round_half_up() -> None:
    context = make_context(b_troops=(1000,))
    systems = BattleSystems()
    apply_distribution(context, systems, target_id="b1", ratio=ExactRatio(1, 2))
    damage = DamageResult(
        source_id="a1",
        target_id="b1",
        damage_type=DamageType.WEAPON,
        source_type=DamageSourceType.SKILL,
        coefficient=1.0,
        base_damage=251.0,
        scaled_damage=251.0,
        final_damage=251,
        source_skill_id="skill-95",
    )

    plan = systems.damage_partition_coordinator.plan(
        context, context.id_allocator.allocate_damage_instance_id(), damage
    )

    assert isinstance(plan, DistributionTransactionPlan)
    assert plan.n == 0
    # Frozen N==0 rule keeps all damage on target; integer vector itself requires N>0.
    assert plan.dtarget == 251
    assert plan.dtransfer == 0

    context2 = make_context(b_troops=(1000, 1000))
    systems2 = BattleSystems()
    apply_distribution(context2, systems2, target_id="b1", ratio=ExactRatio(1, 2))
    plan2 = systems2.damage_partition_coordinator.plan(
        context2, context2.id_allocator.allocate_damage_instance_id(), damage
    )
    assert plan2.dtarget == 126
    assert plan2.dtransfer == 125


def test_reg_int_04_distribution_participant_round_half_up() -> None:
    context = make_context()
    systems = BattleSystems()
    apply_distribution(context, systems, target_id="b1", ratio=ExactRatio(1, 2))
    damage = DamageResult(
        source_id="a1",
        target_id="b1",
        damage_type=DamageType.WEAPON,
        source_type=DamageSourceType.SKILL,
        coefficient=1.0,
        base_damage=706.0,
        scaled_damage=706.0,
        final_damage=706,
        source_skill_id="skill-95",
    )

    plan = systems.damage_partition_coordinator.plan(
        context, context.id_allocator.allocate_damage_instance_id(), damage
    )

    assert isinstance(plan, DistributionTransactionPlan)
    assert plan.participant_ids == ("b2", "b3")
    assert plan.n == 2
    assert plan.dtarget == 353
    assert plan.dtransfer == 353
    assert plan.dparticipant == 177
    assert plan.dtarget + plan.n * plan.dparticipant == 707  # no remainder repair


def test_p95_ptn_04_distribution_n_zero_keeps_full_dtotal_on_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = make_context(b_troops=(1000,))
    systems = BattleSystems()
    apply_distribution(context, systems, target_id="b1", ratio=ExactRatio(1, 2))
    install_damage_result(monkeypatch, systems, final_damage=251)

    result = systems.damage_instance_coordinator.execute_partitioned_damage_instance(
        context,
        request("b1"),
        lineage(),
    )

    assert isinstance(result.partition_plan, DistributionTransactionPlan)
    assert result.partition_plan.n == 0
    assert result.partition_plan.dtarget == 251
    assert result.direct_losses == ()
    assert result.resolution.assigned_target_damage == 251
    assert result.resolution.actual_target_troop_loss == 251


def test_reg_dst_01_invalid_planned_participant_is_skipped_without_recompute(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = make_context()
    systems = BattleSystems()
    apply_distribution(context, systems, target_id="b1", ratio=ExactRatio(1, 2))
    install_damage_result(monkeypatch, systems, final_damage=706)
    original_resolve = systems.direct_troop_loss_resolver.resolve
    calls = 0

    def wrapped_resolve(ctx: BattleContext, direct_request: DirectTroopLossRequest):
        nonlocal calls
        calls += 1
        result = original_resolve(ctx, direct_request)
        if calls == 1:
            b3 = ctx.get_unit("b3")
            systems.troop_system.apply_damage(b3, b3.troops)
        return result

    monkeypatch.setattr(systems.direct_troop_loss_resolver, "resolve", wrapped_resolve)

    result = systems.damage_instance_coordinator.execute_partitioned_damage_instance(
        context,
        request("b1"),
        lineage(),
    )

    plan = result.partition_plan
    assert isinstance(plan, DistributionTransactionPlan)
    assert plan.participant_ids == ("b2", "b3")
    assert plan.n == 2
    assert plan.dtarget == 353
    assert plan.dparticipant == 177
    assert [loss.victim for loss in result.direct_losses] == ["b2"]
    assert result.resolution.assigned_target_damage == 353


def test_reg_dst_02_ordinary_participant_death_does_not_abort_later_plan_or_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = make_context(b_troops=(1000, 100, 1000))
    systems = BattleSystems()
    apply_distribution(context, systems, target_id="b1", ratio=ExactRatio(1, 2))
    install_damage_result(monkeypatch, systems, final_damage=706)

    result = systems.damage_instance_coordinator.execute_partitioned_damage_instance(
        context,
        request("b1"),
        lineage(),
    )

    assert [loss.victim for loss in result.direct_losses] == ["b2", "b3"]
    assert result.direct_losses[0].actual_loss == 100
    assert context.get_unit("b2").troops == 0
    assert result.direct_losses[1].actual_loss == 177
    assert result.resolution.assigned_target_damage == 353
    facts = [
        event
        for event in context.event_bus.history
        if event.event_type in (EventType.DIRECT_TROOP_LOSS, EventType.DAMAGE_DEALT)
    ]
    assert [event.target_id for event in facts] == ["b2", "b3", "b1"]


def test_reg_dst_03_and_fin_02_commander_participant_death_drains_then_finalizes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = make_context(b_troops=(100, 1000, 1000))
    systems = BattleSystems()
    apply_distribution(context, systems, target_id="b2", ratio=ExactRatio(1, 2))
    install_damage_result(monkeypatch, systems, final_damage=706)
    observed_states: list[BattleTerminationState] = []
    target_settle_states: list[BattleTerminationState] = []

    original_observe = systems.finalization_coordinator.observe_damage_instance_death
    original_settle = systems.damage_resolution_system.settle

    def wrapped_observe(ctx: BattleContext, damage_instance_id):
        original_observe(ctx, damage_instance_id)
        observed_states.append(systems.finalization_coordinator.termination_state)

    def wrapped_settle(context: BattleContext, req, permit):
        target_settle_states.append(systems.finalization_coordinator.termination_state)
        return original_settle(context, req, permit)

    monkeypatch.setattr(
        systems.finalization_coordinator,
        "observe_damage_instance_death",
        wrapped_observe,
    )
    monkeypatch.setattr(systems.damage_resolution_system, "settle", wrapped_settle)

    result = systems.damage_instance_coordinator.execute_partitioned_damage_instance(
        context,
        request("b2"),
        lineage(),
    )

    plan = result.partition_plan
    assert isinstance(plan, DistributionTransactionPlan)
    assert plan.participant_ids == ("b1", "b3")
    assert [loss.victim for loss in result.direct_losses] == ["b1", "b3"]
    assert observed_states[0] is BattleTerminationState.DRAINING_ADMITTED_WORK
    assert target_settle_states[-1] is BattleTerminationState.DRAINING_ADMITTED_WORK
    assert result.resolution.assigned_target_damage == 353
    assert systems.finalization_coordinator.termination_state is BattleTerminationState.FINALIZED
    assert systems.finalization_coordinator.active_damage_instance_ids == ()


# ---------------------------------------------------------------------------
# Upstream prevention and direct troop loss contract
# ---------------------------------------------------------------------------


def test_p95_ptn_03_prevented_damage_never_partitions_or_commits_direct_loss(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = make_context()
    systems = BattleSystems()
    apply_share(
        context,
        systems,
        target_id="b1",
        sharer_id="b2",
        ratio=ExactRatio(1, 2),
    )
    install_damage_result(monkeypatch, systems, final_damage=0, prevented=True)

    result = systems.damage_instance_coordinator.execute_partitioned_damage_instance(
        context,
        request("b1"),
        lineage(),
    )

    assert result.partition_plan is None
    assert result.direct_losses == ()
    assert result.resolution.actual_target_troop_loss == 0
    assert EventType.DAMAGE_PREVENTED in event_types(context)
    assert EventType.DIRECT_TROOP_LOSS not in event_types(context)


def test_p95_dtl_01_02_03_04_07_clamp_overflow_zero_and_lineage() -> None:
    context = make_context(b_troops=(1000, 50, 1000))
    systems = BattleSystems()
    parent_id = context.id_allocator.allocate_damage_instance_id()
    tx_id = context.id_allocator.allocate_partition_transaction_id()
    direct_lineage = OperationLineage(
        root_action_id=None,
        parent_normal_attack_id=None,
        parent_damage_instance_id=parent_id,
        source_type=SourceType.SHARE_DIRECT_LOSS,
        physical_attacker="a1",
        physical_skill="skill-95",
        credit_owner="a1",
    )
    direct_request = DirectTroopLossRequest(
        partition_transaction_id=tx_id,
        parent_damage_instance_id=parent_id,
        source_type=SourceType.SHARE_DIRECT_LOSS,
        physical_attacker="a1",
        physical_skill="skill-95",
        victim="b2",
        credit_owner="a1",
        theoretical_loss=71,
        lineage=direct_lineage,
    )

    first = systems.direct_troop_loss_resolver.resolve(context, direct_request)
    assert first.loss.theoretical_loss == 71
    assert first.loss.actual_loss == 50
    assert first.troops_before == 50
    assert first.troops_after == 0
    assert first.death_edge is True
    assert first.loss.parent_damage_instance_id == parent_id
    assert first.loss.lineage.parent_damage_instance_id == parent_id
    assert first.loss.physical_attacker == "a1"
    assert first.loss.physical_skill == "skill-95"
    assert first.loss.credit_owner == "a1"
    assert first.loss.direct_loss_id != parent_id

    zero_request = DirectTroopLossRequest(
        partition_transaction_id=tx_id,
        parent_damage_instance_id=parent_id,
        source_type=SourceType.SHARE_DIRECT_LOSS,
        physical_attacker="a1",
        physical_skill="skill-95",
        victim="b2",
        credit_owner="a1",
        theoretical_loss=0,
        lineage=direct_lineage,
    )
    second = systems.direct_troop_loss_resolver.resolve(context, zero_request)
    assert second.loss.actual_loss == 0
    assert second.death_edge is False
    assert second.loss.direct_loss_id != first.loss.direct_loss_id
    defeat_events = [
        event for event in context.event_bus.history if event.event_type is EventType.UNIT_DEFEATED
    ]
    assert len(defeat_events) == 1


def test_p95_dtl_05_06_and_reg_shr_03_dst_04_direct_loss_has_no_damage_pipeline_dependency() -> None:
    source = inspect.getsource(DirectTroopLossResolver)
    for forbidden in (
        "DamageSystem",
        "DamageResolutionSystem",
        ".calculate(",
        ".settle(",
        ".resolve(",
        "HitResolution",
        "DAMAGE_DEALT",
    ):
        assert forbidden not in source
    assert "TroopSystem" in source
    assert ".apply_damage(" in source
    assert "DIRECT_TROOP_LOSS" in source


def test_partition_coordinator_is_read_only_planner() -> None:
    source = inspect.getsource(DamagePartitionCoordinator)
    for forbidden in (
        ".apply_damage(",
        ".settle(",
        "DamageSystem.calculate",
        "finalize",
        "context.ended",
    ):
        assert forbidden not in source


# ---------------------------------------------------------------------------
# Production provenance coverage, before EffectExecutor cutover
# ---------------------------------------------------------------------------


def _skill_definition() -> SkillDefinition:
    return SkillDefinition(
        skill_id="skill-provenance",
        name="Skill Provenance",
        activation_rate=1.0,
        target_mode=SkillTargetMode.SINGLE_RANDOM_ENEMY,
        effect_specs=(DamageSkillEffectSpec(DamageType.WEAPON, coefficient=1.25),),
    )


def test_p95_src_01_skill_resolver_real_path_emits_active_skill_source_ref() -> None:
    context = make_context(b_troops=(1000,))
    runtime = SkillRuntime(
        definition=_skill_definition(),
        owner_id="a1",
        skill_slot=SkillSlot.LEARNED_1,
    )

    result = BattleSystems().skill_resolver.resolve(context, runtime)
    effect = result.effects[0]

    assert effect.source_ref is not None
    assert effect.source_ref.stage9_source_type is SourceType.ACTIVE_SKILL
    assert effect.source_ref.source_unit_id == "a1"
    assert effect.source_ref.source_skill_id == "skill-provenance"
    assert effect.source_ref.source_skill_slot is SkillSlot.LEARNED_1


def test_p95_src_02_loaded_skill_slot_survives_runtime_and_resolver() -> None:
    context = make_context(b_troops=(1000,))
    loaded = LoadedSkillRef(
        owner_id="a1",
        definition=_skill_definition(),
        skill_slot=SkillSlot.LEARNED_2,
    )
    runtime = SkillRuntime.from_loaded(loaded)

    effect = BattleSystems().skill_resolver.resolve(context, runtime).effects[0]

    assert effect.source_ref is not None
    assert effect.source_ref.source_skill_slot is SkillSlot.LEARNED_2


def test_p95_src_03_04_periodic_trigger_preserves_source_and_state_provenance() -> None:
    context = make_context()
    context.states.register_definition(
        StateDefinition(
            state_id="periodic-95",
            name="periodic-95",
            tags=frozenset({ROUND_START_TRIGGER_TAG}),
            runtime_params_type=PeriodicDamageStateParams,
        )
    )
    systems = BattleSystems()
    state = systems.state_lifecycle_system.apply(
        context,
        state_id="periodic-95",
        owner_id="b1",
        source_id="a1",
        source_skill_id="dot-skill",
        source_skill_slot=SkillSlot.INHERENT,
        runtime_params=PeriodicDamageStateParams(DamageType.WEAPON, 1.0),
    )

    effect = TriggerSystem().collect(context, RoundStartHook(1))[0]

    assert effect.source_ref is not None
    assert effect.source_ref.stage9_source_type is SourceType.PERIODIC_DAMAGE
    assert effect.source_ref.source_unit_id == "a1"
    assert effect.source_ref.source_skill_id == "dot-skill"
    assert effect.source_ref.source_skill_slot is SkillSlot.INHERENT
    assert effect.source_state_id == "periodic-95"
    assert effect.source_state_instance_id == state.instance_id


def test_phase95_production_damage_effect_constructor_scan_is_fully_classified() -> None:
    root = Path(__file__).resolve().parents[1] / "sgs_v2" / "battle_core"
    constructors: list[tuple[str, int, set[str]]] = []
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = None
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr
            if name != "DamageEffect":
                continue
            constructors.append(
                (
                    path.name,
                    node.lineno,
                    {keyword.arg for keyword in node.keywords if keyword.arg is not None},
                )
            )

    assert [(name, line) for name, line, _ in constructors] == [
        ("skill_resolver.py", next(line for name, line, _ in constructors if name == "skill_resolver.py")),
        ("trigger_system.py", next(line for name, line, _ in constructors if name == "trigger_system.py")),
    ]
    assert len(constructors) == 2
    assert all("source_ref" in keywords for _, _, keywords in constructors)


def test_no_low_level_phase95_system_owns_legacy_finalization_side_effects() -> None:
    from sgs_v2.battle_core import damage_instance_coordinator as dic_module
    from sgs_v2.battle_core import direct_troop_loss_system as dtl_module
    from sgs_v2.battle_core import damage_partition_system as partition_module

    for module in (dic_module, dtl_module, partition_module):
        source = inspect.getsource(module)
        assert "context.ended" not in source
        assert "BATTLE_ENDED" not in source
