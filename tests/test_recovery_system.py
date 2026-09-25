from __future__ import annotations

import pytest

from sgs_v2.battle_core import (
    BattleContext,
    EventBus,
    EventType,
    LineupPosition,
    OfficialStateId,
    RandomSystem,
    RecoverEffect,
    RecoveryModifierPolicy,
    RecoveryPreventionReason,
    RecoveryPreventedResult,
    RecoveryRequest,
    RecoveryResolvedResult,
    RecoverySystem,
    StateLifecycleSystem,
    TroopChangeResult,
    TroopSystem,
    UnitRuntime,
    register_official_state_definitions,
)
from sgs_v2.battle_core.stage9_integerization import ExactRatio


def make_context() -> BattleContext:
    context = BattleContext(
        battle_id="stage7-recovery",
        units={
            "a1": UnitRuntime(
                "a1", "A1", "A", 1000, 1000, 100, 100, 100,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "b1": UnitRuntime(
                "b1", "B1", "B", 1000, 400, 100, 100, 90,
                lineup_position=LineupPosition.COMMANDER,
            ),
        },
        event_bus=EventBus(),
        random=RandomSystem(7),
    )
    context.current_round = 1
    context.current_phase = "UNIT_ACTION_START"
    register_official_state_definitions(context.states)
    return context


def apply_healing_ban(context: BattleContext) -> None:
    StateLifecycleSystem().apply(
        context,
        state_id=OfficialStateId.HEALING_BAN.value,
        owner_id="b1",
        source_id="a1",
        source_skill_id="ban-skill",
    )


def test_normal_recovery_uses_troop_system_restore_and_clamps_to_max() -> None:
    context = make_context()
    result = RecoverySystem(TroopSystem()).resolve(
        context,
        RecoveryRequest(
            source_id="a1",
            target_id="b1",
            amount=900,
            source_skill_id="heal-skill",
        ),
    )

    assert isinstance(result, RecoveryResolvedResult)
    assert result.troop_change.requested_change == 900
    assert result.troop_change.actual_change == 600
    assert result.troop_change.remaining_troops == 1000
    assert context.get_unit("b1").troops == 1000
    event = context.event_bus.history[-1]
    assert event.event_type is EventType.TROOPS_RECOVERED
    assert event.payload["requested_recovery"] == 900
    assert event.payload["actual_recovery"] == 600
    assert event.payload["remaining_troops"] == 1000


def test_target_defeated_precedes_healing_ban_and_never_restores() -> None:
    context = make_context()
    apply_healing_ban(context)
    context.get_unit("b1").troops = 0

    class SpyTroops:
        def __init__(self) -> None:
            self.calls = 0

        def restore(self, target, requested_recovery):
            self.calls += 1
            raise AssertionError("restore must not be called")

    spy = SpyTroops()
    result = RecoverySystem(spy).resolve(  # type: ignore[arg-type]
        context,
        RecoveryRequest(source_id="a1", target_id="b1", amount=100),
    )

    assert isinstance(result, RecoveryPreventedResult)
    assert result.reason is RecoveryPreventionReason.TARGET_DEFEATED
    assert result.reason_state_id is None
    assert spy.calls == 0
    assert context.get_unit("b1").troops == 0
    assert context.event_bus.history[-1].event_type is EventType.RECOVERY_PREVENTED


def test_full_target_with_healing_ban_is_prevented_before_restore() -> None:
    context = make_context()
    context.get_unit("b1").troops = 1000
    apply_healing_ban(context)

    result = RecoverySystem(TroopSystem()).resolve(
        context,
        RecoveryRequest(source_id="a1", target_id="b1", amount=100),
    )

    assert isinstance(result, RecoveryPreventedResult)
    assert result.reason is RecoveryPreventionReason.HEALING_BAN
    assert result.reason_state_id == OfficialStateId.HEALING_BAN.value
    assert context.get_unit("b1").troops == 1000


def test_full_target_without_ban_resolves_zero_and_emits_no_recovery_fact() -> None:
    context = make_context()
    context.get_unit("b1").troops = 1000
    before = len(context.event_bus.history)

    result = RecoverySystem(TroopSystem()).resolve(
        context,
        RecoveryRequest(source_id="a1", target_id="b1", amount=100),
    )

    assert isinstance(result, RecoveryResolvedResult)
    assert result.troop_change.actual_change == 0
    assert len(context.event_bus.history) == before
    assert not any(
        event.event_type is EventType.TROOPS_RECOVERED
        for event in context.event_bus.history
    )


def test_unknown_target_is_an_explicit_failure_not_prevented_result() -> None:
    context = make_context()
    before = len(context.event_bus.history)
    with pytest.raises(KeyError, match="unknown unit_id"):
        RecoverySystem(TroopSystem()).resolve(
            context,
            RecoveryRequest(source_id="a1", target_id="missing", amount=10),
        )
    assert len(context.event_bus.history) == before


def test_recovery_events_preserve_full_provenance() -> None:
    context = make_context()
    request = RecoveryRequest(
        source_id="a1",
        target_id="b1",
        amount=50,
        source_skill_id="skill-7",
        source_state_id="synthetic-heal",
        source_state_instance_id="state-000123",
    )
    RecoverySystem(TroopSystem()).resolve(context, request)
    payload = context.event_bus.history[-1].payload
    assert payload["source_id"] == "a1"
    assert payload["source_skill_id"] == "skill-7"
    assert payload["source_state_id"] == "synthetic-heal"
    assert payload["source_state_instance_id"] == "state-000123"

    context.get_unit("b1").troops = 300
    apply_healing_ban(context)
    RecoverySystem(TroopSystem()).resolve(context, request)
    payload = context.event_bus.history[-1].payload
    assert payload["source_skill_id"] == "skill-7"
    assert payload["source_state_id"] == "synthetic-heal"
    assert payload["source_state_instance_id"] == "state-000123"
    assert payload["reason"] == RecoveryPreventionReason.HEALING_BAN.value


@pytest.mark.parametrize("amount", [True, 1.5, -1])
def test_recover_effect_rejects_invalid_amount(amount) -> None:
    with pytest.raises((TypeError, ValueError)):
        RecoverEffect(source_id=None, target_id="b1", amount=amount)  # type: ignore[arg-type]


@pytest.mark.parametrize("amount", [True, 1.5, -1])
def test_recovery_request_rejects_invalid_amount(amount) -> None:
    with pytest.raises((TypeError, ValueError)):
        RecoveryRequest(source_id=None, target_id="b1", amount=amount)  # type: ignore[arg-type]


@pytest.mark.parametrize("amount", [True, 1.5])
def test_troop_restore_rejects_non_integer_recovery(amount) -> None:
    context = make_context()
    with pytest.raises(TypeError):
        TroopSystem().restore(context.get_unit("b1"), amount)  # type: ignore[arg-type]


def test_recovery_prevention_reason_and_reason_state_invariants() -> None:
    request = RecoveryRequest(source_id=None, target_id="b1", amount=1)
    with pytest.raises(TypeError):
        RecoveryPreventedResult(
            request=request,
            reason="HEALING_BAN",  # type: ignore[arg-type]
            reason_state_id=OfficialStateId.HEALING_BAN.value,
        )
    with pytest.raises(ValueError):
        RecoveryPreventedResult(
            request=request,
            reason=RecoveryPreventionReason.TARGET_DEFEATED,
            reason_state_id=OfficialStateId.HEALING_BAN.value,
        )
    with pytest.raises(ValueError):
        RecoveryPreventedResult(
            request=request,
            reason=RecoveryPreventionReason.HEALING_BAN,
            reason_state_id=None,
        )
    with pytest.raises(ValueError):
        RecoveryPreventedResult(
            request=request,
            reason=RecoveryPreventionReason.HEALING_BAN,
            reason_state_id="wrong",
        )


def test_prevented_recovery_does_not_fabricate_troop_change() -> None:
    context = make_context()
    context.get_unit("b1").troops = 0
    result = RecoverySystem(TroopSystem()).resolve(
        context,
        RecoveryRequest(source_id=None, target_id="b1", amount=100),
    )
    assert isinstance(result, RecoveryPreventedResult)
    assert not hasattr(result, "troop_change")



def test_recovery_modifier_owner_applies_exact_second_ceil() -> None:
    context = make_context()
    system = RecoverySystem(
        TroopSystem(),
        recovery_modifier_provider=lambda _context, _request: ExactRatio(11, 10),
    )

    result = system.resolve(
        context,
        RecoveryRequest(
            source_id="a1",
            target_id="b1",
            amount=11,
            modifier_policy=RecoveryModifierPolicy.APPLY,
        ),
    )

    assert isinstance(result, RecoveryResolvedResult)
    assert result.request.base_amount == 11
    assert result.modified_recovery == 13
    assert result.troop_change.requested_change == 13
    assert result.actual_recovery == 13
    event = context.event_bus.history[-1]
    assert event.payload["base_recovery"] == 11
    assert event.payload["modified_recovery"] == 13
    assert event.payload["requested_recovery"] == 13


def test_recovery_modifier_policy_none_preserves_generic_recovery_and_skips_provider() -> None:
    context = make_context()
    calls = 0

    def provider(_context, _request):
        nonlocal calls
        calls += 1
        return ExactRatio(99, 10)

    result = RecoverySystem(
        TroopSystem(),
        recovery_modifier_provider=provider,
    ).resolve(
        context,
        RecoveryRequest(source_id="a1", target_id="b1", amount=11),
    )

    assert isinstance(result, RecoveryResolvedResult)
    assert result.modified_recovery == 11
    assert result.actual_recovery == 11
    assert calls == 0


def test_zero_recovery_request_does_not_invoke_modifier_provider() -> None:
    context = make_context()
    calls = 0

    def provider(_context, _request):
        nonlocal calls
        calls += 1
        return ExactRatio(11, 10)

    result = RecoverySystem(
        TroopSystem(),
        recovery_modifier_provider=provider,
    ).resolve(
        context,
        RecoveryRequest(
            source_id="a1",
            target_id="b1",
            amount=0,
            modifier_policy=RecoveryModifierPolicy.APPLY,
        ),
    )

    assert isinstance(result, RecoveryResolvedResult)
    assert result.modified_recovery == 0
    assert result.actual_recovery == 0
    assert calls == 0
