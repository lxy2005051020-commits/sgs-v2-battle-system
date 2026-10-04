from __future__ import annotations

import pytest

from sgs_v2.battle_core import (
    BattleContext,
    BattleSystems,
    DamageModifierContribution,
    DamageModifierKind,
    DamageModifierOperation,
    DamageModifierPhase,
    DamageRequest,
    DamageSourceType,
    DamageType,
    EventBus,
    LineupPosition,
    RandomSystem,
    TroopSystem,
    UnitRuntime,
)
from sgs_v2.battle_core.damage_modifier_system import DamageModifierSystem
from sgs_v2.battle_core.damage_rule_models import RuleContributionSource
from sgs_v2.battle_core.damage_rule_provider import DamageRuleCollection


def _unit(
    unit_id: str,
    team_id: str,
    *,
    troops: int = 1000,
    wounded_troops: int | None = None,
    advancement_stars: int = 0,
    military_books_active: bool = False,
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
        intelligence=250,
        lineup_position=LineupPosition.COMMANDER,
        wounded_troops=wounded_troops,
        advancement_stars=advancement_stars,
        military_books_active=military_books_active,
    )


def _context(*, source=None, target=None) -> BattleContext:
    source = source or _unit("a", "A")
    target = target or _unit("b", "B")
    return BattleContext(
        battle_id="stage13-foundation",
        units={"a": source, "b": target},
        event_bus=EventBus(),
        random=RandomSystem(7),
    )


def _request() -> DamageRequest:
    return DamageRequest(
        source_id="a",
        target_id="b",
        damage_type=DamageType.WEAPON,
        source_type=DamageSourceType.SKILL,
    )


def _source(owner_id: str, key: str) -> RuleContributionSource:
    return RuleContributionSource(
        owner_id=owner_id,
        applied_by_unit_id=owner_id,
        source_skill_id=key,
        source_state_id=None,
        source_state_instance_id=None,
        origin_key=key,
    )


def _modifier(
    *,
    phase: DamageModifierPhase,
    kind: DamageModifierKind,
    operand: float,
    owner_id: str,
    key: str,
) -> DamageModifierContribution:
    return DamageModifierContribution(
        phase=phase,
        kind=kind,
        operation=DamageModifierOperation.MULTIPLY_FACTOR,
        operand=operand,
        source=_source(owner_id, key),
        order_key=key,
    )


def test_wounded_generation_is_event_local_floor_not_aggregate_floor() -> None:
    unit = _unit("a", "A", wounded_troops=0)
    troops = TroopSystem()

    first = troops.apply_damage(unit, 78)
    second = troops.apply_damage(unit, 78)

    assert first.wounded_generated == 70
    assert second.wounded_generated == 70
    assert unit.wounded_troops == 140
    assert unit.wounded_troops != (156 * 90) // 100


def test_recovery_is_clamped_by_wounded_pool_and_consumes_it_one_for_one() -> None:
    unit = _unit("a", "A", wounded_troops=0)
    troops = TroopSystem()
    troops.apply_damage(unit, 500)

    result = troops.restore(unit, 999)

    assert result.actual_change == 450
    assert result.wounded_consumed == 450
    assert unit.troops == 950
    assert unit.wounded_troops == 0


def test_wounded_pool_decays_ten_percent_at_round_transition() -> None:
    unit = _unit("a", "A", troops=800, wounded_troops=123)
    troops = TroopSystem()

    assert troops.decay_wounded(unit) == 110
    assert unit.wounded_troops == 110


def test_defeat_clears_wounded_pool_runtime_default() -> None:
    unit = _unit("a", "A", troops=100, wounded_troops=50)
    troops = TroopSystem()

    result = troops.apply_damage(unit, 999)

    assert result.actual_change == 100
    assert unit.troops == 0
    assert unit.wounded_troops == 0


def test_outgoing_increase_and_reduction_use_algebraic_same_side_pool() -> None:
    context = _context()
    rules = DamageRuleCollection(
        modifier_contributions=(
            _modifier(
                phase=DamageModifierPhase.OUTGOING,
                kind=DamageModifierKind.OUTGOING_INCREASE,
                operand=1.20,
                owner_id="a",
                key="oi",
            ),
            _modifier(
                phase=DamageModifierPhase.OUTGOING,
                kind=DamageModifierKind.OUTGOING_REDUCTION,
                operand=0.90,
                owner_id="a",
                key="od",
            ),
        )
    )

    result = DamageModifierSystem().resolve_phases(
        context,
        _request(),
        rules,
        1000.0,
        phases=frozenset({DamageModifierPhase.OUTGOING}),
    )

    assert result.output_damage == pytest.approx(1100.0)
    assert result.output_damage != pytest.approx(1080.0)


def test_incoming_pool_is_algebraic_and_pierce_only_scales_reduction_part() -> None:
    context = _context()
    rules = DamageRuleCollection(
        modifier_contributions=(
            _modifier(
                phase=DamageModifierPhase.INCOMING,
                kind=DamageModifierKind.INCOMING_INCREASE,
                operand=1.20,
                owner_id="b",
                key="ii",
            ),
            _modifier(
                phase=DamageModifierPhase.INCOMING,
                kind=DamageModifierKind.INCOMING_REDUCTION,
                operand=0.80,
                owner_id="b",
                key="id",
            ),
        )
    )

    result = DamageModifierSystem().resolve_phases(
        context,
        _request(),
        rules,
        1000.0,
        phases=frozenset({DamageModifierPhase.INCOMING}),
        pierce_rate=0.50,
    )

    # +20% vulnerability - (20% reduction * 50% remaining) = +10% net.
    assert result.output_damage == pytest.approx(1100.0)


def test_same_side_modifier_pool_has_absolute_minus_ninety_percent_floor() -> None:
    context = _context()
    rules = DamageRuleCollection(
        modifier_contributions=(
            _modifier(
                phase=DamageModifierPhase.INCOMING,
                kind=DamageModifierKind.INCOMING_REDUCTION,
                operand=0.20,
                owner_id="b",
                key="id1",
            ),
            _modifier(
                phase=DamageModifierPhase.INCOMING,
                kind=DamageModifierKind.INCOMING_REDUCTION,
                operand=0.20,
                owner_id="b",
                key="id2",
            ),
        )
    )

    result = DamageModifierSystem().resolve_phases(
        context,
        _request(),
        rules,
        1000.0,
        phases=frozenset({DamageModifierPhase.INCOMING}),
    )

    assert result.output_damage == pytest.approx(100.0)


def test_advancement_is_independent_outgoing_and_incoming_multiplier() -> None:
    base_context = _context()
    advanced_context = _context(
        source=_unit(
            "a",
            "A",
            advancement_stars=5,
            military_books_active=True,
        ),
        target=_unit(
            "b",
            "B",
            advancement_stars=5,
            military_books_active=True,
        ),
    )
    base_systems = BattleSystems(
        weapon_random_percent_range=(90, 90),
        weapon_low_damage_floor_range=(5, 5),
    )
    advanced_systems = BattleSystems(
        weapon_random_percent_range=(90, 90),
        weapon_low_damage_floor_range=(5, 5),
    )

    base = base_systems.damage_system.calculate(base_context, _request())
    advanced = advanced_systems.damage_system.calculate(advanced_context, _request())

    assert advanced.final_damage == int(base.scaled_damage * 1.10 * 0.90)
