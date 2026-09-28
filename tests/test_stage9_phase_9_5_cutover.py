from __future__ import annotations

import inspect

import pytest

from sgs_v2.battle_core import (
    BattleContext,
    BattleSystems,
    BattleTerminationState,
    DamageEffect,
    DamageEffectResult,
    DamageResult,
    DamageShareStateParams,
    DamageSourceType,
    DamageType,
    EffectSourceRef,
    EventBus,
    ExactRatio,
    LineupPosition,
    PeriodicDamageStateParams,
    RandomSystem,
    ROUND_START_TRIGGER_TAG,
    RoundStartHook,
    SourceType,
    StateDefinition,
    UnitRuntime,
    register_official_state_definitions,
)
from sgs_v2.battle_core.damage_partition_system import (
    DamagePartitionKind,
    DamageShareTransactionPlan,
)
from sgs_v2.battle_core.effect_executor import EffectExecutor
from sgs_v2.battle_core.official_state_catalog import OfficialStateId


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


def make_context(*, target_troops: int = 1000, with_sharer: bool = False) -> BattleContext:
    units = {
        "a1": _unit("a1", "A", LineupPosition.COMMANDER),
        "b1": _unit("b1", "B", LineupPosition.COMMANDER, troops=target_troops),
    }
    if with_sharer:
        units["b2"] = _unit("b2", "B", LineupPosition.DEPUTY_1)
    context = BattleContext(
        battle_id="stage9-phase95-cutover",
        units=units,
        event_bus=EventBus(),
        random=RandomSystem(951),
    )
    context.current_round = 1
    context.current_phase = "UNIT_ACTION"
    register_official_state_definitions(context.states)
    return context


def active_effect(*, target_id: str = "b1") -> DamageEffect:
    return DamageEffect(
        source_id="a1",
        target_id=target_id,
        damage_type=DamageType.WEAPON,
        source_type=DamageSourceType.SKILL,
        coefficient=1.0,
        source_skill_id="skill-95",
        source_ref=EffectSourceRef(
            stage9_source_type=SourceType.ACTIVE_SKILL,
            source_unit_id="a1",
            source_skill_id="skill-95",
        ),
    )


def install_damage_result(
    monkeypatch: pytest.MonkeyPatch,
    systems: BattleSystems,
    *,
    final_damage: int,
) -> None:
    def fake_calculate(context: BattleContext, request) -> DamageResult:
        return DamageResult(
            source_id=request.source_id,
            target_id=request.target_id,
            damage_type=request.damage_type,
            source_type=request.source_type,
            coefficient=request.coefficient,
            base_damage=float(final_damage),
            scaled_damage=float(final_damage),
            final_damage=final_damage,
            source_skill_id=request.source_skill_id,
            source_state_id=request.source_state_id,
            source_state_instance_id=request.source_state_instance_id,
        )

    monkeypatch.setattr(systems.damage_system, "calculate", fake_calculate)


def forbid_legacy_resolve(monkeypatch: pytest.MonkeyPatch, systems: BattleSystems) -> None:
    def fail_legacy(*args, **kwargs):
        raise AssertionError("production DamageEffect reached legacy resolve()")

    monkeypatch.setattr(systems.damage_resolution_system, "resolve", fail_legacy)


def test_p95_src_05_missing_source_ref_is_rejected_without_reverse_inference(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = make_context()
    systems = BattleSystems()
    forbid_legacy_resolve(monkeypatch, systems)
    before = context.get_unit("b1").troops
    effect = DamageEffect(
        source_id="a1",
        target_id="b1",
        damage_type=DamageType.WEAPON,
        source_type=DamageSourceType.SKILL,
        source_skill_id="skill-95",
    )

    with pytest.raises(ValueError, match="EffectSourceRef"):
        systems.effect_executor.execute(context, effect)

    assert context.get_unit("b1").troops == before


def test_p95_src_06_stage8_scalar_classification_conflict_is_domain_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = make_context()
    systems = BattleSystems()
    forbid_legacy_resolve(monkeypatch, systems)
    effect = DamageEffect(
        source_id="a1",
        target_id="b1",
        damage_type=DamageType.WEAPON,
        source_type=DamageSourceType.CONTINUOUS,
        source_skill_id="skill-95",
        source_ref=EffectSourceRef(
            stage9_source_type=SourceType.ACTIVE_SKILL,
            source_unit_id="a1",
            source_skill_id="skill-95",
        ),
    )

    with pytest.raises(ValueError, match="conflicts with authoritative Stage9"):
        systems.effect_executor.execute(context, effect)


def test_none_path_uses_one_shot_stage9_settlement_and_never_legacy_resolve(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = make_context()
    systems = BattleSystems()
    forbid_legacy_resolve(monkeypatch, systems)
    install_damage_result(monkeypatch, systems, final_damage=123)
    original_settle = systems.damage_resolution_system.settle
    settle_count = 0

    def counted_settle(ctx, request, permit):
        nonlocal settle_count
        settle_count += 1
        return original_settle(ctx, request, permit)

    monkeypatch.setattr(systems.damage_resolution_system, "settle", counted_settle)

    result = systems.effect_executor.execute(context, active_effect())

    assert isinstance(result, DamageEffectResult)
    assert result.damage_instance_id is not None
    assert result.partition_plan is not None
    assert result.partition_plan.kind is DamagePartitionKind.NONE
    assert result.resolution.damage.final_damage == 123
    assert result.resolution.assigned_target_damage == 123
    assert result.resolution.actual_target_troop_loss == 123
    assert settle_count == 1


def test_production_share_preserves_dtotal_and_commits_direct_loss(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = make_context(with_sharer=True)
    systems = BattleSystems()
    systems.state_lifecycle_system.apply(
        context,
        state_id=OfficialStateId.DAMAGE_SHARE.value,
        owner_id="b1",
        source_id="a1",
        source_skill_id="share-skill",
        runtime_params=DamageShareStateParams(
            sharer_id="b2",
            ratio=ExactRatio(15, 100),
        ),
    )
    forbid_legacy_resolve(monkeypatch, systems)
    install_damage_result(monkeypatch, systems, final_damage=470)

    result = systems.effect_executor.execute(context, active_effect())

    assert isinstance(result.partition_plan, DamageShareTransactionPlan)
    assert result.resolution.damage.final_damage == 470
    assert result.resolution.assigned_target_damage == 399
    assert result.resolution.actual_target_troop_loss == 399
    assert len(result.direct_losses) == 1
    assert result.direct_losses[0].theoretical_loss == 71
    assert result.direct_losses[0].actual_loss == 71


def test_periodic_trigger_damage_effect_uses_same_production_cutover(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = make_context()
    systems = BattleSystems()
    context.states.register_definition(
        StateDefinition(
            state_id="periodic-cutover",
            name="periodic-cutover",
            tags=frozenset({ROUND_START_TRIGGER_TAG}),
            runtime_params_type=PeriodicDamageStateParams,
        )
    )
    state = systems.state_lifecycle_system.apply(
        context,
        state_id="periodic-cutover",
        owner_id="b1",
        source_id="a1",
        source_skill_id="dot-skill",
        runtime_params=PeriodicDamageStateParams(DamageType.WEAPON, 1.0),
    )
    effect = systems.trigger_system.collect(context, RoundStartHook(1))[0]
    forbid_legacy_resolve(monkeypatch, systems)
    install_damage_result(monkeypatch, systems, final_damage=88)

    result = systems.effect_executor.execute(context, effect)

    assert isinstance(result, DamageEffectResult)
    assert effect.source_ref is not None
    assert effect.source_ref.stage9_source_type is SourceType.PERIODIC_DAMAGE
    assert effect.source_state_id == state.state_id
    assert effect.source_state_instance_id == state.instance_id
    assert result.damage_instance_id is not None
    assert result.resolution.assigned_target_damage == 88


def test_production_damage_effect_observes_real_finalization_barrier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = make_context(target_troops=100)
    systems = BattleSystems()
    forbid_legacy_resolve(monkeypatch, systems)
    install_damage_result(monkeypatch, systems, final_damage=200)

    result = systems.effect_executor.execute(context, active_effect())

    assert result.resolution.target_defeated is True
    assert systems.finalization_coordinator.active_damage_instance_ids == ()
    assert systems.finalization_coordinator.termination_state is BattleTerminationState.FINALIZED


def test_effect_executor_has_no_reverse_source_inference_or_legacy_damage_router() -> None:
    source = inspect.getsource(EffectExecutor)
    assert "DamageSourceType" not in source
    assert "_damage_resolution" not in source
    assert ".resolve(\n                context,\n                effect.to_request()" not in source
    assert "execute_damage_effect(context, effect)" in source
