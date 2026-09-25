from __future__ import annotations

import pytest

from sgs_v2.battle_core import (
    BattleContext,
    BattlePhase,
    BattleSystems,
    DamageRequest,
    DamageSourceType,
    DamageType,
    EventBus,
    EventType,
    LineupPosition,
    OfficialStateId,
    RandomSystem,
    FirstAidStateParams,
    RecuperationStateParams,
    RecoveryModelKind,
    RecoveryPotencyContext,
    UnitActionStartHook,
    UnitRuntime,
    register_official_state_definitions,
)
from sgs_v2.battle_core.operation_identity import OperationLineage, SourceType
from sgs_v2.battle_core.stage9_integerization import ExactRatio
from sgs_v2.battle_core.stage9_state_params import DamageShareStateParams, DistributionStateParams
from sgs_v2.battle_core.stage11_state_params import (
    AlertStateParams,
    CriticalStateParams,
    EvasionStateParams,
    LifeStealStateParams,
    ResistanceStateParams,
    Stage11TimedFlagParams,
)


def make_context() -> tuple[BattleContext, BattleSystems]:
    ctx = BattleContext(
        "stage11-cross-matrix",
        {
            "a1": UnitRuntime("a1", "A1", "A", 10000, 5000, 200, 100, 100,
                              lineup_position=LineupPosition.COMMANDER, intelligence=200),
            "b1": UnitRuntime("b1", "B1", "B", 10000, 5000, 150, 100, 90,
                              lineup_position=LineupPosition.COMMANDER, intelligence=150),
            "b2": UnitRuntime("b2", "B2", "B", 10000, 5000, 150, 100, 80,
                              lineup_position=LineupPosition.DEPUTY_1, intelligence=150),
        },
        EventBus(),
        RandomSystem(20260925),
    )
    register_official_state_definitions(ctx.states)
    return ctx, BattleSystems()


def apply(ctx, systems, state_id, owner, params=None, source="a1"):
    return systems.state_lifecycle_system.apply(
        ctx,
        state_id=state_id.value if isinstance(state_id, OfficialStateId) else state_id,
        owner_id=owner,
        source_id=source,
        source_skill_id="stage11-cross",
        runtime_params=params,
    )


def fixed_base(monkeypatch, systems, *, weapon=100, strategy=100):
    monkeypatch.setattr(
        systems.damage_system,
        "_calculate_weapon_base_damage",
        lambda *args, **kwargs: weapon,
    )
    monkeypatch.setattr(
        systems.damage_system,
        "_calculate_strategy_base_damage",
        lambda *args, **kwargs: strategy,
    )


def request(damage_type=DamageType.WEAPON):
    return DamageRequest(
        "a1", "b1", damage_type, DamageSourceType.SKILL, 1.0,
        source_skill_id="stage11-cross",
    )


def execute_parent(ctx, systems, damage_type=DamageType.WEAPON):
    lineage = OperationLineage(
        ctx.id_allocator.allocate_action_id(),
        None,
        None,
        SourceType.ACTIVE_SKILL,
        "a1",
        "stage11-cross",
        "a1",
    )
    return systems.damage_instance_coordinator.execute_partitioned_damage_instance(
        ctx, request(damage_type), lineage
    )


def test_evasion_and_resistance_are_bypassed_by_sure_hit_but_resistance_consumes(monkeypatch):
    ctx, systems = make_context()
    fixed_base(monkeypatch, systems)
    apply(ctx, systems, OfficialStateId.EVASION, "b1", EvasionStateParams(probability=1.0), source="b1")
    barrier = apply(ctx, systems, OfficialStateId.BARRIER, "b1", ResistanceStateParams(remaining_uses=1), source="b1")
    apply(ctx, systems, OfficialStateId.SURE_HIT, "a1", Stage11TimedFlagParams())

    result = systems.damage_system.calculate(ctx, request())

    assert result.prevented is False
    assert result.final_damage == 100
    assert barrier.instance_id not in ctx.states


def test_resistance_prevents_before_alert_so_alert_is_not_consumed(monkeypatch):
    ctx, systems = make_context()
    fixed_base(monkeypatch, systems)
    apply(ctx, systems, OfficialStateId.BARRIER, "b1", ResistanceStateParams(remaining_uses=1), source="b1")
    alert = apply(ctx, systems, OfficialStateId.VIGILANCE, "b1",
                  AlertStateParams(remaining_uses=1, reduction_rate=ExactRatio(1, 2), threshold=10), source="b1")

    result = systems.damage_system.calculate(ctx, request())

    assert result.prevented is True
    assert result.final_damage == 0
    assert ctx.states.get(alert.instance_id) is not None


@pytest.mark.parametrize(
    ("damage_type", "critical_state"),
    [
        (DamageType.WEAPON, OfficialStateId.CRITICAL),
        (DamageType.STRATEGY, OfficialStateId.STRATEGY_CRITICAL),
    ],
)
def test_break_and_matching_critical_compose_without_reordering(monkeypatch, damage_type, critical_state):
    ctx, systems = make_context()
    fixed_base(monkeypatch, systems)
    apply(ctx, systems, OfficialStateId.DEFENSE_PIERCE, "a1", Stage11TimedFlagParams())
    apply(ctx, systems, critical_state, "a1", CriticalStateParams(chance=1.0, bonus=1.0))

    result = systems.damage_system.calculate(ctx, request(damage_type))

    assert result.critical_triggered is True
    assert result.final_damage == 200


def test_critical_happens_before_alert_threshold_and_reduction(monkeypatch):
    ctx, systems = make_context()
    fixed_base(monkeypatch, systems)
    apply(ctx, systems, OfficialStateId.CRITICAL, "a1", CriticalStateParams(chance=1.0, bonus=1.0))
    alert = apply(ctx, systems, OfficialStateId.VIGILANCE, "b1",
                  AlertStateParams(remaining_uses=1, reduction_rate=ExactRatio(1, 2), threshold=150), source="b1")

    result = systems.damage_system.calculate(ctx, request())

    assert result.critical_triggered is True
    assert result.alert_consumed_instance_id == alert.instance_id
    assert result.final_damage == 100


def test_weakness_zero_short_circuits_alert_consumption_after_formula(monkeypatch):
    ctx, systems = make_context()
    fixed_base(monkeypatch, systems)
    apply(ctx, systems, OfficialStateId.WEAKNESS, "a1", Stage11TimedFlagParams(), source="b1")
    alert = apply(ctx, systems, OfficialStateId.VIGILANCE, "b1",
                  AlertStateParams(remaining_uses=1, reduction_rate=ExactRatio(1, 2), threshold=1), source="b1")

    result = systems.damage_system.calculate(ctx, request())

    assert result.base_damage == 100
    assert result.final_damage == 0
    assert result.zeroed_by_state_id == OfficialStateId.WEAKNESS.value
    assert result.alert_consumed_instance_id is None
    assert ctx.states.get(alert.instance_id) is not None


def test_critical_actual_damage_is_the_lifesteal_basis(monkeypatch):
    ctx, systems = make_context()
    fixed_base(monkeypatch, systems)
    ctx.units["a1"].troops = 4000
    apply(ctx, systems, OfficialStateId.CRITICAL, "a1", CriticalStateParams(chance=1.0, bonus=1.0))
    apply(ctx, systems, OfficialStateId.WEAPON_LIFESTEAL, "a1", LifeStealStateParams(ExactRatio(1, 10)))

    execution = execute_parent(ctx, systems)

    assert execution.resolution.actual_target_troop_loss == 200
    recovery = [e for e in ctx.event_bus.history if e.event_type is EventType.TROOPS_RECOVERED]
    assert len(recovery) == 1
    assert recovery[0].payload["requested_recovery"] == 20


def test_weakness_share_and_lifesteal_stay_zero_without_second_trigger(monkeypatch):
    ctx, systems = make_context()
    fixed_base(monkeypatch, systems)
    ctx.units["a1"].troops = 4000
    apply(ctx, systems, OfficialStateId.WEAKNESS, "a1", Stage11TimedFlagParams(), source="b1")
    apply(ctx, systems, OfficialStateId.WEAPON_LIFESTEAL, "a1", LifeStealStateParams(ExactRatio(1, 10)))
    apply(ctx, systems, OfficialStateId.DAMAGE_SHARE, "b1",
          DamageShareStateParams("b2", ExactRatio(1, 2)), source="b2")

    execution = execute_parent(ctx, systems)

    assert execution.damage_result.final_damage == 0
    assert execution.partition_plan.attacker_recovery_basis == 0
    assert execution.resolution.actual_target_troop_loss == 0
    assert sum(loss.actual_loss for loss in execution.direct_losses) == 0
    assert not [e for e in ctx.event_bus.history if e.event_type is EventType.TROOPS_RECOVERED]
    assert ctx.units["a1"].troops == 4000


def test_healing_block_intercepts_strategy_lifesteal(monkeypatch):
    ctx, systems = make_context()
    fixed_base(monkeypatch, systems)
    ctx.units["a1"].troops = 4000
    apply(ctx, systems, OfficialStateId.STRATEGY_LIFESTEAL, "a1", LifeStealStateParams(ExactRatio(1, 10)))
    apply(ctx, systems, OfficialStateId.HEALING_BAN, "a1", Stage11TimedFlagParams(), source="b1")

    execution = execute_parent(ctx, systems, DamageType.STRATEGY)

    assert execution.resolution.actual_target_troop_loss == 100
    prevented = [e for e in ctx.event_bus.history if e.event_type is EventType.RECOVERY_PREVENTED]
    assert len(prevented) == 1
    assert prevented[0].payload["requested_recovery"] == 10
    assert ctx.units["a1"].troops == 4000


def test_stun_does_not_suppress_persistent_damage_tick():
    ctx, systems = make_context()
    ctx.current_round = 1
    ctx.current_phase = BattlePhase.ROUND_START.value
    apply(ctx, systems, OfficialStateId.STUN, "b1", source="a1")
    burn = systems.state_lifecycle_system.apply(
        ctx,
        state_id=OfficialStateId.BURN.value,
        owner_id="b1",
        source_id="a1",
        duration_rounds=1,
    )
    assert burn is not None
    before = ctx.units["b1"].troops
    ctx.current_phase = BattlePhase.UNIT_ACTION_START.value
    ctx.action_progress.set_current_acting_unit("b1")
    ctx.action_progress.mark_action_start("b1", 1)

    systems.rule_hook_system.process(ctx, UnitActionStartHook(round_no=1, actor_id="b1"))

    assert ctx.units["b1"].troops < before


def test_continuous_damage_freezes_critical_and_break_context_at_application():
    ctx, systems = make_context()
    ctx.current_round = 1
    ctx.current_phase = BattlePhase.ROUND_START.value
    crit = apply(ctx, systems, OfficialStateId.STRATEGY_CRITICAL, "a1", CriticalStateParams(chance=1.0, bonus=1.0))
    brk = apply(ctx, systems, OfficialStateId.DEFENSE_PIERCE, "a1", Stage11TimedFlagParams())
    burn = systems.state_lifecycle_system.apply(
        ctx,
        state_id=OfficialStateId.BURN.value,
        owner_id="b1",
        source_id="a1",
        duration_rounds=1,
    )
    basis = burn.runtime_params.frozen_damage_basis
    assert basis.locked_crit_context.triggered is True
    assert basis.formula_policy_result.formula_context.defense_policy.value == "IGNORE_RELEVANT_TARGET_DEFENSE"

    systems.state_lifecycle_system.remove(ctx, crit.instance_id)
    systems.state_lifecycle_system.remove(ctx, brk.instance_id)
    ctx.current_phase = BattlePhase.UNIT_ACTION_START.value
    ctx.action_progress.set_current_acting_unit("b1")
    ctx.action_progress.mark_action_start("b1", 1)
    result = systems.rule_hook_system.process(ctx, UnitActionStartHook(round_no=1, actor_id="b1"))

    damage = result.intent_results[0].resolution.damage
    assert damage.critical_triggered is True
    assert damage.calculation_basis.value == "FROZEN_APPLICATION"



def test_weakness_resolved_zero_still_triggers_first_aid(monkeypatch):
    ctx, systems = make_context()
    ctx.current_round = 1
    fixed_base(monkeypatch, systems)
    ctx.units["b1"].troops = 4000
    apply(ctx, systems, OfficialStateId.WEAKNESS, "a1", Stage11TimedFlagParams(), source="b1")
    systems.state_lifecycle_system.apply(
        ctx,
        state_id=OfficialStateId.FIRST_AID.value,
        owner_id="b1",
        source_id="b1",
        duration_rounds=2,
        runtime_params=FirstAidStateParams(
            probability=1.0,
            recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT,
            recovery_potency_context=RecoveryPotencyContext(treatment_amount=50),
        ),
    )

    execution = execute_parent(ctx, systems)

    assert execution.damage_result.final_damage == 0
    assert execution.damage_result.zeroed_by_state_id == OfficialStateId.WEAKNESS.value
    recovery = [e for e in ctx.event_bus.history if e.event_type is EventType.TROOPS_RECOVERED]
    assert len(recovery) == 1
    assert recovery[0].payload["actual_recovery"] == 50
    assert ctx.units["b1"].troops == 4050


def test_healing_block_intercepts_first_aid_request(monkeypatch):
    ctx, systems = make_context()
    ctx.current_round = 1
    fixed_base(monkeypatch, systems)
    ctx.units["b1"].troops = 4000
    systems.state_lifecycle_system.apply(
        ctx,
        state_id=OfficialStateId.FIRST_AID.value,
        owner_id="b1",
        source_id="b1",
        duration_rounds=2,
        runtime_params=FirstAidStateParams(
            probability=1.0,
            recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT,
            recovery_potency_context=RecoveryPotencyContext(treatment_amount=50),
        ),
    )
    apply(ctx, systems, OfficialStateId.HEALING_BAN, "b1", Stage11TimedFlagParams(), source="a1")

    execution = execute_parent(ctx, systems)

    assert execution.resolution.actual_target_troop_loss == 100
    prevented = [e for e in ctx.event_bus.history if e.event_type is EventType.RECOVERY_PREVENTED]
    assert len(prevented) == 1
    assert prevented[0].payload["requested_recovery"] == 50
    assert ctx.units["b1"].troops == 3900


def test_stun_does_not_suppress_recuperation_hot():
    ctx, systems = make_context()
    ctx.current_round = 1
    ctx.units["b1"].troops = 4000
    apply(ctx, systems, OfficialStateId.STUN, "b1", source="a1")
    systems.state_lifecycle_system.apply(
        ctx,
        state_id=OfficialStateId.RECUPERATION.value,
        owner_id="b1",
        source_id="b1",
        source_skill_id="recuperation",
        duration_rounds=2,
        runtime_params=RecuperationStateParams(
            probability=1.0,
            recovery_potency_context=RecoveryPotencyContext(treatment_amount=60),
        ),
    )
    ctx.current_phase = BattlePhase.UNIT_ACTION_START.value
    ctx.action_progress.set_current_acting_unit("b1")
    ctx.action_progress.mark_action_start("b1", 1)

    result = systems.rule_hook_system.process(ctx, UnitActionStartHook(round_no=1, actor_id="b1"))

    assert result.batch_status == "COMPLETED"
    recovered = [e for e in ctx.event_bus.history if e.event_type is EventType.TROOPS_RECOVERED]
    assert len(recovered) == 1
    assert recovered[0].payload["actual_recovery"] == 60
    assert ctx.units["b1"].troops == 4060


def test_share_partitions_post_alert_damage(monkeypatch):
    ctx, systems = make_context()
    fixed_base(monkeypatch, systems, weapon=200)
    alert = apply(
        ctx, systems, OfficialStateId.VIGILANCE, "b1",
        AlertStateParams(remaining_uses=1, reduction_rate=ExactRatio(1, 2), threshold=100),
        source="b1",
    )
    apply(ctx, systems, OfficialStateId.DAMAGE_SHARE, "b1",
          DamageShareStateParams("b2", ExactRatio(1, 2)), source="b2")

    execution = execute_parent(ctx, systems)

    assert execution.damage_result.alert_consumed_instance_id == alert.instance_id
    assert execution.damage_result.final_damage == 100
    assert execution.partition_plan.dtotal == 100
    assert execution.partition_plan.primary_assigned_damage == 50
    assert execution.partition_plan.shared_assigned_damage == 50
    assert execution.resolution.actual_target_troop_loss == 50
    assert execution.direct_losses[0].actual_loss == 50


def test_distribution_lifesteal_keeps_explicit_target_only_runtime_default(monkeypatch):
    ctx, systems = make_context()
    fixed_base(monkeypatch, systems, weapon=100)
    ctx.units["a1"].troops = 4000
    apply(ctx, systems, OfficialStateId.WEAPON_LIFESTEAL, "a1", LifeStealStateParams(ExactRatio(1, 10)))
    apply(ctx, systems, OfficialStateId.DAMAGE_SPLIT, "b1", DistributionStateParams(ExactRatio(1, 2)), source="b1")

    execution = execute_parent(ctx, systems)

    assert execution.partition_plan.dtotal == 100
    assert execution.partition_plan.dtarget == 50
    assert execution.resolution.actual_target_troop_loss == 50
    assert sum(loss.actual_loss for loss in execution.direct_losses) == 50
    recovery = [e for e in ctx.event_bus.history if e.event_type is EventType.TROOPS_RECOVERED]
    assert len(recovery) == 1
    assert recovery[0].payload["requested_recovery"] == 5
    assert ctx.units["a1"].troops == 4005
