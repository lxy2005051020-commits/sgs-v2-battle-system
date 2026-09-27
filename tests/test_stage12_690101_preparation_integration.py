from __future__ import annotations

import inspect

from sgs_v2.battle_core import (
    BattleContext,
    BattlePhase,
    BattleSystems,
    DamageSkillEffectSpec,
    DamageType,
    EmptyStateRuntimeParams,
    EventBus,
    LineupPosition,
    OfficialStateId,
    PreparationMode,
    RandomSystem,
    RemovalOperation,
    SkillDefinition,
    SkillOperationAdmissionRequest,
    SkillOperationAdmissionStatus,
    SkillRuntime,
    SkillSlot,
    SkillTargetMode,
    SkillType,
    StateApplicationResultStatus,
    StateCandidate,
    StateLifetimeSpec,
    StateNode,
    UnitRuntime,
    register_official_state_definitions,
)
from sgs_v2.battle_core.preparation_interruption import (
    NoopPreparationInterruptionPort,
    PreparationInterruptionRequest,
    PreparationInterruptionScope,
    PreparationInterruptionStatus,
)
from sgs_v2.battle_core.preparation_state import PreparationStateOwner
from sgs_v2.battle_core.provider_identity import SkillProviderRef
from sgs_v2.battle_core.state_effectiveness import (
    LocalRuleCauseRef,
    StateEffectivenessContribution,
    SuppressionCause,
)
from sgs_v2.battle_core import battle_systems as battle_systems_module
from sgs_v2.battle_core import preparation_state as preparation_state_module
from sgs_v2.battle_core import state_application as state_application_module


class RecordingOwnerPort:
    def __init__(self, owner: PreparationStateOwner) -> None:
        self.owner = owner
        self.requests: list[PreparationInterruptionRequest] = []

    def interrupt(self, context, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        return self.owner.interrupt(context, request)


def make_context() -> BattleContext:
    context = BattleContext(
        battle_id="stage12-690101-preparation",
        units={
            "a": UnitRuntime(
                "a", "A", "A", 1000, 1000, 300, 100, 100,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "b": UnitRuntime(
                "b", "B", "B", 1000, 1000, 100, 100, 90,
                lineup_position=LineupPosition.COMMANDER,
            ),
        },
        event_bus=EventBus(),
        random=RandomSystem(690101),
    )
    register_official_state_definitions(context.states)
    context.current_round = 1
    context.current_phase = BattlePhase.UNIT_ACTION.value
    return context


def state_candidate(
    state_id: str,
    *,
    lifetime_spec: StateLifetimeSpec | None = None,
) -> StateCandidate:
    return StateCandidate(
        state_id=state_id,
        owner_id="a",
        source_id="b",
        source_skill_id=f"source-{state_id}",
        source_skill_slot=SkillSlot.LEARNED_1,
        runtime_params_candidate=EmptyStateRuntimeParams(),
        lifetime_spec=lifetime_spec,
        application_provenance="stage12-690101-preparation-test",
    )


def apply_state(
    systems: BattleSystems,
    context: BattleContext,
    state_id: str,
    *,
    lifetime_spec: StateLifetimeSpec | None = None,
):
    return systems.state_application_coordinator.apply_candidate(
        context,
        state_candidate(state_id, lifetime_spec=lifetime_spec),
    )


def active_runtime(skill_id: str = "preparing.active") -> SkillRuntime:
    return SkillRuntime(
        definition=SkillDefinition(
            skill_id=skill_id,
            name=skill_id,
            activation_rate=1.0,
            target_mode=SkillTargetMode.SINGLE_RANDOM_ENEMY,
            effect_specs=(DamageSkillEffectSpec(DamageType.WEAPON),),
            skill_type=SkillType.ACTIVE,
            preparation_mode=PreparationMode.REQUIRED,
        ),
        owner_id="a",
        skill_slot=SkillSlot.INHERENT,
        enabled=True,
    )


def begin_admitted_preparation(
    systems: BattleSystems,
    context: BattleContext,
    *,
    owner: PreparationStateOwner | None = None,
    skill_id: str = "preparing.active",
    operation_id: str = "skillop-1",
):
    item = active_runtime(skill_id)
    context.skill_runtimes.register(item)
    ref = SkillProviderRef("a", SkillSlot.INHERENT, skill_id)
    decision = systems.skill_operation_admission_coordinator.evaluate(
        context,
        SkillOperationAdmissionRequest(
            actor_id="a",
            provider_ref=ref,
            skill_type=SkillType.ACTIVE,
            preparation_mode=PreparationMode.REQUIRED,
        ),
    )
    assert decision.status is SkillOperationAdmissionStatus.ALLOW
    target_owner = owner or systems.preparation_state_owner
    record = target_owner.begin_preparing(
        holder_id="a",
        provider_ref=ref,
        admitted_operation_id=operation_id,
    )
    return ref, record


def settle_due(
    systems: BattleSystems,
    context: BattleContext,
    *,
    round_no: int,
    phase: str,
):
    due = systems.state_lifecycle_system.due_at(
        context,
        round_no=round_no,
        phase=phase,
    )
    roots = tuple(StateNode(item.instance_id) for item in due)
    before = systems.effectiveness_transition_coordinator.capture(context, roots)
    removed = systems.state_lifecycle_system.expire_at(
        context,
        round_no=round_no,
        phase=phase,
    )
    systems.effectiveness_transition_coordinator.complete_removed_nodes(
        context,
        before,
        tuple(StateNode(item.instance_id) for item in removed),
    )
    return removed


def second_exhaustion_suppressor(context, instance, _session):
    if instance.state_id != OfficialStateId.SILENCE.value:
        return StateEffectivenessContribution()
    if not context.metadata.get("second_exhaustion_suppressor", False):
        return StateEffectivenessContribution()
    return StateEffectivenessContribution(
        suppression_causes=(
            SuppressionCause(
                "TEST_SECOND_EXHAUSTION_SUPPRESSOR",
                LocalRuleCauseRef(instance.instance_id),
            ),
        )
    )


def test_begin_preparing_records_admitted_identity() -> None:
    context = make_context()
    systems = BattleSystems()

    ref, record = begin_admitted_preparation(systems, context)

    assert record.holder_id == "a"
    assert record.provider_ref == ref
    assert record.skill_id == ref.skill_id
    assert record.admitted_operation_id == "skillop-1"
    assert systems.preparation_state_owner.get_preparing("a") == (record,)


def test_interruption_clears_preparing_and_second_interrupt_is_not_preparing() -> None:
    context = make_context()
    systems = BattleSystems()
    begin_admitted_preparation(systems, context)
    request = PreparationInterruptionRequest(
        scope=PreparationInterruptionScope.HOLDER_ACTIVE,
        holder_id="a",
        cause_key="test",
    )

    first = systems.preparation_state_owner.interrupt(context, request)
    second = systems.preparation_state_owner.interrupt(context, request)

    assert first.status is PreparationInterruptionStatus.INTERRUPTED
    assert second.status is PreparationInterruptionStatus.NOT_PREPARING
    assert not systems.preparation_state_owner.is_preparing("a")


def test_provider_scope_matches_exact_provider_only() -> None:
    context = make_context()
    owner = PreparationStateOwner()
    first = SkillProviderRef("a", SkillSlot.INHERENT, "active.one")
    second = SkillProviderRef("a", SkillSlot.LEARNED_1, "active.two")
    owner.begin_preparing(
        holder_id="a", provider_ref=first, admitted_operation_id="op-1"
    )
    owner.begin_preparing(
        holder_id="a", provider_ref=second, admitted_operation_id="op-2"
    )

    result = owner.interrupt(
        context,
        PreparationInterruptionRequest(
            scope=PreparationInterruptionScope.PROVIDER,
            holder_id="a",
            provider_ref=first,
            cause_key="provider-test",
        ),
    )

    assert result.status is PreparationInterruptionStatus.INTERRUPTED
    assert result.interrupted_provider_refs == (first,)
    remaining = owner.get_preparing("a")
    assert len(remaining) == 1
    assert remaining[0].provider_ref == second


def test_provider_scope_does_not_interrupt_other_provider() -> None:
    context = make_context()
    owner = PreparationStateOwner()
    resident = SkillProviderRef("a", SkillSlot.INHERENT, "active.one")
    requested = SkillProviderRef("a", SkillSlot.LEARNED_1, "active.two")
    owner.begin_preparing(
        holder_id="a", provider_ref=resident, admitted_operation_id="op-1"
    )

    result = owner.interrupt(
        context,
        PreparationInterruptionRequest(
            scope=PreparationInterruptionScope.PROVIDER,
            holder_id="a",
            provider_ref=requested,
            cause_key="provider-test",
        ),
    )

    assert result.status is PreparationInterruptionStatus.PROVIDER_NOT_MATCHED
    assert owner.is_preparing("a")


def test_preparation_owner_queries_emit_no_events_and_use_zero_rng() -> None:
    context = make_context()
    systems = BattleSystems()
    begin_admitted_preparation(systems, context)
    before = context.event_bus.history

    assert systems.preparation_state_owner.is_preparing("a")
    assert systems.preparation_state_owner.get_preparing("a")
    assert context.event_bus.history == before

    source = inspect.getsource(preparation_state_module)
    assert "import random" not in source
    assert "context.random" not in source


def test_production_battle_systems_uses_concrete_owner_not_noop() -> None:
    systems = BattleSystems()

    assert systems.preparation_interruption_port is systems.preparation_state_owner
    assert not isinstance(
        systems.preparation_interruption_port,
        NoopPreparationInterruptionPort,
    )


def test_effective_exhaustion_create_interrupts_existing_preparation_once() -> None:
    context = make_context()
    owner = PreparationStateOwner()
    port = RecordingOwnerPort(owner)
    systems = BattleSystems(preparation_interruption_port=port)
    begin_admitted_preparation(systems, context, owner=owner)

    result = apply_state(systems, context, OfficialStateId.SILENCE.value)

    assert result.status is StateApplicationResultStatus.APPLIED
    assert not owner.is_preparing("a")
    assert len(port.requests) == 1
    assert port.requests[0].scope is PreparationInterruptionScope.HOLDER_ACTIVE


def test_initially_suppressed_exhaustion_create_does_not_interrupt() -> None:
    context = make_context()
    systems = BattleSystems()
    systems.state_effectiveness_policy.register_rule_adapter(
        second_exhaustion_suppressor
    )
    begin_admitted_preparation(systems, context)
    context.metadata["second_exhaustion_suppressor"] = True

    result = apply_state(systems, context, OfficialStateId.SILENCE.value)

    assert result.status is StateApplicationResultStatus.APPLIED
    assert result.instance is not None
    assert not systems.state_effectiveness_policy.evaluate_state(
        context, result.instance
    ).effective
    assert systems.preparation_state_owner.is_preparing("a")


def test_insight_rejected_exhaustion_does_not_interrupt() -> None:
    context = make_context()
    systems = BattleSystems()
    begin_admitted_preparation(systems, context)
    assert apply_state(
        systems, context, OfficialStateId.INSIGHT.value
    ).status is StateApplicationResultStatus.APPLIED

    result = apply_state(systems, context, OfficialStateId.SILENCE.value)

    assert result.status is StateApplicationResultStatus.REJECTED_ADMISSION
    assert systems.preparation_state_owner.is_preparing("a")


def test_exhaustion_resume_interrupts_preparation_once() -> None:
    context = make_context()
    owner = PreparationStateOwner()
    port = RecordingOwnerPort(owner)
    systems = BattleSystems(preparation_interruption_port=port)
    exhaustion = apply_state(
        systems, context, OfficialStateId.SILENCE.value
    ).instance
    insight = apply_state(
        systems, context, OfficialStateId.INSIGHT.value
    ).instance
    assert exhaustion is not None and insight is not None
    begin_admitted_preparation(systems, context, owner=owner)

    systems.state_removal_coordinator.remove(
        context,
        operation=RemovalOperation.NATURAL_EXPIRY,
        instance_id=insight.instance_id,
    )

    assert not owner.is_preparing("a")
    assert len(port.requests) == 1


def test_remove_one_suppressor_no_interrupt_then_last_suppressor_interrupts_once() -> None:
    context = make_context()
    owner = PreparationStateOwner()
    port = RecordingOwnerPort(owner)
    systems = BattleSystems(preparation_interruption_port=port)
    systems.state_effectiveness_policy.register_rule_adapter(
        second_exhaustion_suppressor
    )
    exhaustion = apply_state(
        systems, context, OfficialStateId.SILENCE.value
    ).instance
    assert exhaustion is not None

    context.metadata["second_exhaustion_suppressor"] = True
    insight = apply_state(
        systems, context, OfficialStateId.INSIGHT.value
    ).instance
    assert insight is not None
    assert not systems.state_effectiveness_policy.evaluate_state(
        context, exhaustion
    ).effective
    begin_admitted_preparation(systems, context, owner=owner)

    systems.state_removal_coordinator.remove(
        context,
        operation=RemovalOperation.NATURAL_EXPIRY,
        instance_id=insight.instance_id,
    )
    assert owner.is_preparing("a")
    assert port.requests == []

    root = (StateNode(exhaustion.instance_id),)
    before = systems.effectiveness_transition_coordinator.capture(context, root)
    context.metadata["second_exhaustion_suppressor"] = False
    systems.effectiveness_transition_coordinator.settle(context, before, root)

    assert not owner.is_preparing("a")
    assert len(port.requests) == 1


def test_same_envelope_insight_exhaustion_expiry_has_no_ghost_interrupt() -> None:
    context = make_context()
    systems = BattleSystems()
    lifetime = StateLifetimeSpec.round_calendar(expires_round=2)
    exhaustion = apply_state(
        systems,
        context,
        OfficialStateId.SILENCE.value,
        lifetime_spec=lifetime,
    ).instance
    insight = apply_state(
        systems,
        context,
        OfficialStateId.INSIGHT.value,
        lifetime_spec=lifetime,
    ).instance
    assert exhaustion is not None and insight is not None
    begin_admitted_preparation(systems, context)

    settle_due(
        systems,
        context,
        round_no=2,
        phase=BattlePhase.ROUND_END.value,
    )

    assert systems.preparation_state_owner.is_preparing("a")
    assert not context.states.has_instance(exhaustion.instance_id)
    assert not context.states.has_instance(insight.instance_id)


def test_static_architecture_keeps_stage15_inactive_and_activation_seam_generic() -> None:
    preparation_source = inspect.getsource(preparation_state_module)
    battle_systems_source = inspect.getsource(battle_systems_module)
    application_source = inspect.getsource(state_application_module)

    for forbidden in (
        "PreparationScheduler",
        "PreparationTurnMachine",
        "PreparationProgressEngine",
        "PreparationQueue",
        "PreparationRoundResolver",
        "ActiveSkillPreparationRuntime",
        "Stage15Runtime",
    ):
        assert forbidden not in preparation_source
        assert forbidden not in battle_systems_source

    assert "SkillPermissionPolicy" not in preparation_source
    assert "ProviderValidityPolicy" not in preparation_source
    assert "TargetSystem" not in preparation_source
    assert "advance_round" not in preparation_source
    assert "NoopPreparationInterruptionPort()" not in battle_systems_source

    assert "CommittedEffectiveStateActivation" in application_source
    assert "EXHAUSTION" not in application_source
    assert "SILENCE" not in application_source
