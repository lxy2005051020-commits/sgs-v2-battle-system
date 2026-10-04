from __future__ import annotations

import pytest

from sgs_v2.battle_core import (
    BattleContext,
    BattleSystems,
    EventBus,
    ExactRatio,
    LineupPosition,
    RandomSystem,
    RecoveryModelKind,
    RecoveryOpportunity,
    RecoveryOpportunityKind,
    RecoveryPotencyContext,
    RuleIntentExecutionDescriptor,
    RuleIntentKind,
    TreatmentFormulaSystem,
    TreatmentModifierSnapshot,
    UnitRuntime,
)


def _identity_troop_table() -> dict[int, int]:
    return {n: n for n in range(1, 10001)}


def _unit(
    unit_id: str,
    team_id: str,
    *,
    troops: int,
    wounded_troops: int,
    intelligence: float = 100.0,
) -> UnitRuntime:
    return UnitRuntime(
        unit_id=unit_id,
        name=unit_id,
        team_id=team_id,
        max_troops=1000,
        troops=troops,
        attack=300,
        defense=200,
        speed=100,
        intelligence=intelligence,
        lineup_position=LineupPosition.COMMANDER,
        wounded_troops=wounded_troops,
    )


def test_treatment_formula_uses_same_side_sum_cross_side_multiply_and_red_pool() -> None:
    formula = TreatmentFormulaSystem(troop_function_table=_identity_troop_table())
    modifiers = TreatmentModifierSnapshot(
        source_side_deltas=(
            ExactRatio(1, 5),   # +20%
            ExactRatio(-1, 10), # -10% -> source pool = 1.10
        ),
        target_side_deltas=(
            ExactRatio(3, 10),  # +30%
            ExactRatio(-1, 5),  # -20% -> target pool = 1.10
        ),
        red_pool_multiplier=ExactRatio(21, 20),  # independent 1.05 pool
    )

    result = formula.calculate(
        rate=ExactRatio(1, 2),
        source_troops=1000,
        source_attribute=100,
        modifiers=modifiers,
    )

    # CEIL(0.5 * (1000 + 100) * 1.10 * 1.10 * 1.05)
    assert result.nominal_recovery == 699


def test_treatment_formula_integerization_is_ceiling() -> None:
    formula = TreatmentFormulaSystem(troop_function_table=_identity_troop_table())

    result = formula.calculate(
        rate=ExactRatio(1, 3),
        source_troops=100,
        source_attribute=1,
    )

    assert result.nominal_recovery == 34


def test_persistent_treatment_replays_application_time_formula_snapshot() -> None:
    table = _identity_troop_table()
    systems = BattleSystems(weapon_troop_function_table=table)
    source = _unit(
        "source",
        "A",
        troops=1000,
        wounded_troops=0,
        intelligence=100.0,
    )
    target = _unit(
        "target",
        "B",
        troops=100,
        wounded_troops=900,
        intelligence=50.0,
    )
    context = BattleContext(
        battle_id="stage13-b3-snapshot",
        units={"source": source, "target": target},
        event_bus=EventBus(),
        random=RandomSystem(7),
    )

    potency = RecoveryPotencyContext(
        base_rate=0.5,
        source_troops_at_application=1000,
        source_attribute_at_application=100.0,
    )
    opportunity = RecoveryOpportunity(
        opportunity_kind=RecoveryOpportunityKind.RECUPERATION_ACTION_START,
        execution_descriptor=RuleIntentExecutionDescriptor(
            intent_kind=RuleIntentKind.RECOVERY_OPPORTUNITY,
            intent_owner_id="target",
            state_owner_id="target",
            target_id="target",
        ),
        probability=1.0,
        recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT,
        recovery_potency_context=potency,
        aftermath_fact=None,
    )

    # Mutable live source facts change after application. The tick must not re-read them.
    source.troops = 1
    source.intelligence = 999.0

    resolved = systems.recovery_opportunity_system.execute(context, opportunity)

    assert resolved.executed is True
    assert resolved.resolution is not None
    assert resolved.resolution.actual_recovery == 550
    assert target.troops == 650
    assert target.wounded_troops == 350


def test_formula_lane_requires_complete_application_time_snapshot() -> None:
    systems = BattleSystems(weapon_troop_function_table=_identity_troop_table())
    target = _unit(
        "target",
        "B",
        troops=100,
        wounded_troops=900,
    )
    enemy = _unit(
        "enemy",
        "B",
        troops=1000,
        wounded_troops=0,
    )
    context = BattleContext(
        battle_id="stage13-b3-incomplete-snapshot",
        units={"target": target, "enemy": enemy},
        event_bus=EventBus(),
        random=RandomSystem(7),
    )
    opportunity = RecoveryOpportunity(
        opportunity_kind=RecoveryOpportunityKind.RECUPERATION_ACTION_START,
        execution_descriptor=RuleIntentExecutionDescriptor(
            intent_kind=RuleIntentKind.RECOVERY_OPPORTUNITY,
            intent_owner_id="target",
            target_id="target",
        ),
        probability=1.0,
        recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT,
        recovery_potency_context=RecoveryPotencyContext(
            base_rate=0.5,
            source_attribute_at_application=100.0,
        ),
        aftermath_fact=None,
    )

    with pytest.raises(ValueError, match="application-time source_troops"):
        systems.recovery_opportunity_system.execute(context, opportunity)



def test_special_pre_resolved_recovery_does_not_enter_ordinary_treatment_formula() -> None:
    systems = BattleSystems(weapon_troop_function_table=_identity_troop_table())
    source = _unit(
        "source",
        "A",
        troops=1000,
        wounded_troops=0,
        intelligence=999.0,
    )
    target = _unit(
        "target",
        "A",
        troops=100,
        wounded_troops=900,
        intelligence=50.0,
    )
    context = BattleContext(
        battle_id="stage13-b3-special-recovery-isolation",
        units={"source": source, "target": target},
        event_bus=EventBus(),
        random=RandomSystem(7),
    )

    # Special recovery families provide an already-resolved amount through their
    # dedicated owner. No FB1 source-troop/attribute snapshot is required or read.
    opportunity = RecoveryOpportunity(
        opportunity_kind=RecoveryOpportunityKind.RECUPERATION_ACTION_START,
        execution_descriptor=RuleIntentExecutionDescriptor(
            intent_kind=RuleIntentKind.RECOVERY_OPPORTUNITY,
            intent_owner_id="target",
            target_id="target",
        ),
        probability=1.0,
        recovery_model_kind=RecoveryModelKind.TREATMENT_AMOUNT,
        recovery_potency_context=RecoveryPotencyContext(
            treatment_amount=321,
        ),
        aftermath_fact=None,
    )

    resolved = systems.recovery_opportunity_system.execute(context, opportunity)

    assert resolved.executed is True
    assert resolved.resolution is not None
    assert resolved.resolution.actual_recovery == 321
    assert target.troops == 421
