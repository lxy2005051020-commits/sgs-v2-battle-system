from __future__ import annotations

import inspect

import pytest

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
    SkillOperationKind,
    SkillPermissionRequest,
    SkillPermissionStatus,
    SkillResolutionStatus,
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
from sgs_v2.battle_core import battle_systems as battle_systems_module
from sgs_v2.battle_core import preparation_state as preparation_state_module
from sgs_v2.battle_core import state_application as state_application_module
from sgs_v2.battle_core.preparation_interruption import (
    NoopPreparationInterruptionPort,
    PreparationInterruptionRequest,
    PreparationInterruptionResult,
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


class CountingRandomSystem(RandomSystem):
    def __init__(self, seed: int = 690101) -> None:
        super().__init__(seed)
        self.chance_calls = 0
        self.sample_calls = 0

    def chance(self, probability: float) -> bool:
        self.chance_calls += 1
        return True

    def sample(self, values, k):  # type: ignore[no-untyped-def]
        self.sample_calls += 1
        return super().sample(values, k)


class RecordingPort:
    def __init__(self, owner: PreparationStateOwner | None = None) -> None:
        self.owner = owner
        self.requests: list[PreparationInterruptionRequest] = []

    def interrupt(self, context, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        if self.owner is not None:
            return self.owner.interrupt(context, request)
        return PreparationInterruptionResult(
            request=request,
            status=PreparationInterruptionStatus.NOT_PREPARING,
        )


class RaisingPort:
    def __init__(self) -> None:
        self.calls = 0

    def interrupt(self, context, request):  # type: ignore[no-untyped-def]
        self.calls += 1
        raise RuntimeError("audit synthetic post-commit interruption failure")


def make_context(random_system: RandomSystem | None = None) -> BattleContext:
    context = BattleContext(
        battle_id="stage12-690101-runtime-freeze-audit",
        units={
            "a": UnitRuntime(
                "a", "A", "A", 1000, 1000, 300, 100, 100,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "b": UnitRuntime(
                "b", "B", "B", 1000, 1000, 100, 100, 90,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "c": UnitRuntime(
                "c", "C", "B", 1000, 1000, 100, 100, 80,
                lineup_position=LineupPosition.DEPUTY_1,
            ),
        },
        event_bus=EventBus(),
        random=random_system or RandomSystem(690101),
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
        application_provenance="stage12-690101-runtime-freeze-audit",
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


def active_runtime(
    *,
    skill_id: str = "audit.active",
    enabled: bool = True,
) -> SkillRuntime:
    return SkillRuntime(
        definition=SkillDefinition(
            skill_id=skill_id,
            name=skill_id,
            activation_rate=1.0,
            target_mode=SkillTargetMode.SINGLE_RANDOM_ENEMY,
            effect_specs=(DamageSkillEffectSpec(DamageType.WEAPON),),
            skill_type=SkillType.ACTIVE,
            preparation_mode=PreparationMode.NONE,
        ),
        owner_id="a",
        skill_slot=SkillSlot.INHERENT,
        enabled=enabled,
    )


def begin_preparing(
    systems: BattleSystems,
    context: BattleContext,
    *,
    owner: PreparationStateOwner | None = None,
    operation_id: str = "audit-op-1",
) -> SkillProviderRef:
    runtime = SkillRuntime(
        definition=SkillDefinition(
            skill_id="audit.preparing.active",
            name="audit.preparing.active",
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
    context.skill_runtimes.register(runtime)
    ref = SkillProviderRef("a", SkillSlot.INHERENT, runtime.definition.skill_id)
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
    (owner or systems.preparation_state_owner).begin_preparing(
        holder_id="a",
        provider_ref=ref,
        admitted_operation_id=operation_id,
    )
    return ref


def second_exhaustion_suppressor(context, instance, _session):
    if instance.state_id != OfficialStateId.SILENCE.value:
        return StateEffectivenessContribution()
    if not context.metadata.get("audit_second_suppressor", False):
        return StateEffectivenessContribution()
    return StateEffectivenessContribution(
        suppression_causes=(
            SuppressionCause(
                "AUDIT_SECOND_EXHAUSTION_SUPPRESSOR",
                LocalRuleCauseRef(instance.instance_id),
            ),
        )
    )


def settle_due(
    systems: BattleSystems,
    context: BattleContext,
    *,
    round_no: int,
    phase: str,
) -> None:
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


def test_production_preparation_port_is_concrete() -> None:
    systems = BattleSystems()

    assert systems.preparation_interruption_port is systems.preparation_state_owner
    assert not isinstance(
        systems.preparation_interruption_port,
        NoopPreparationInterruptionPort,
    )


def test_preparation_owner_has_no_progression_api() -> None:
    public_callables = {
        name
        for name, value in inspect.getmembers(PreparationStateOwner)
        if callable(value) and not name.startswith("_")
    }
    assert public_callables == {
        "begin_preparing",
        "clear_preparing",
        "get_preparing",
        "interrupt",
        "is_preparing",
    }

    source = inspect.getsource(preparation_state_module)
    for forbidden in (
        "def advance_round",
        "def progress_preparation",
        "def execute_prepared",
        "def select_target",
        "PreparationScheduler",
        "PreparationTurnMachine",
        "PreparationProgressEngine",
        "PreparationQueue",
        "PreparationRoundResolver",
        "ActiveSkillPreparationRuntime",
        "Stage15Runtime",
        "SkillPermissionPolicy",
        "ProviderValidityPolicy",
        "context.random",
        "import random",
    ):
        assert forbidden not in source


def test_effective_create_interrupts_exactly_once() -> None:
    context = make_context()
    owner = PreparationStateOwner()
    port = RecordingPort(owner)
    systems = BattleSystems(preparation_interruption_port=port)
    begin_preparing(systems, context, owner=owner)

    result = apply_state(systems, context, OfficialStateId.SILENCE.value)

    assert result.status is StateApplicationResultStatus.APPLIED
    assert len(port.requests) == 1
    assert port.requests[0].scope is PreparationInterruptionScope.HOLDER_ACTIVE
    assert not owner.is_preparing("a")


def test_initial_suppressed_create_does_not_interrupt() -> None:
    context = make_context()
    port = RecordingPort()
    systems = BattleSystems(preparation_interruption_port=port)
    systems.state_effectiveness_policy.register_rule_adapter(
        second_exhaustion_suppressor
    )
    context.metadata["audit_second_suppressor"] = True

    result = apply_state(systems, context, OfficialStateId.SILENCE.value)

    assert result.status is StateApplicationResultStatus.APPLIED
    assert result.instance is not None
    assert not systems.state_effectiveness_policy.evaluate_state(
        context, result.instance
    ).effective
    assert port.requests == []


def test_failed_application_does_not_interrupt() -> None:
    context = make_context()
    port = RecordingPort()
    systems = BattleSystems(preparation_interruption_port=port)
    assert apply_state(
        systems, context, OfficialStateId.INSIGHT.value
    ).status is StateApplicationResultStatus.APPLIED
    port.requests.clear()

    rejected = apply_state(systems, context, OfficialStateId.SILENCE.value)

    assert rejected.status is StateApplicationResultStatus.REJECTED_ADMISSION
    assert port.requests == []


def test_failed_conflict_does_not_interrupt() -> None:
    context = make_context()
    port = RecordingPort()
    systems = BattleSystems(preparation_interruption_port=port)
    first = apply_state(systems, context, OfficialStateId.SILENCE.value)
    assert first.status is StateApplicationResultStatus.APPLIED
    port.requests.clear()

    second = apply_state(systems, context, OfficialStateId.SILENCE.value)

    assert second.status is StateApplicationResultStatus.UNSUPPORTED_BOUNDARY
    assert port.requests == []


def test_resume_interrupts_exactly_once_and_preserves_identity() -> None:
    context = make_context()
    owner = PreparationStateOwner()
    port = RecordingPort(owner)
    systems = BattleSystems(preparation_interruption_port=port)
    exhaustion = apply_state(
        systems, context, OfficialStateId.SILENCE.value
    ).instance
    insight = apply_state(
        systems, context, OfficialStateId.INSIGHT.value
    ).instance
    assert exhaustion is not None and insight is not None
    original_instance_id = exhaustion.instance_id
    original_generation = exhaustion.current_generation_id
    original_lifetime = exhaustion.lifetime_spec
    port.requests.clear()
    begin_preparing(systems, context, owner=owner)

    systems.state_removal_coordinator.remove(
        context,
        operation=RemovalOperation.NATURAL_EXPIRY,
        instance_id=insight.instance_id,
    )

    assert len(port.requests) == 1
    assert not owner.is_preparing("a")
    resident = context.states.get(original_instance_id)
    assert resident.instance_id == original_instance_id
    assert resident.current_generation_id == original_generation
    assert resident.lifetime_spec == original_lifetime


def test_remove_one_of_multiple_causes_does_not_interrupt() -> None:
    context = make_context()
    owner = PreparationStateOwner()
    port = RecordingPort(owner)
    systems = BattleSystems(preparation_interruption_port=port)
    systems.state_effectiveness_policy.register_rule_adapter(
        second_exhaustion_suppressor
    )
    exhaustion = apply_state(
        systems, context, OfficialStateId.SILENCE.value
    ).instance
    assert exhaustion is not None

    context.metadata["audit_second_suppressor"] = True
    insight = apply_state(
        systems, context, OfficialStateId.INSIGHT.value
    ).instance
    assert insight is not None
    port.requests.clear()
    begin_preparing(systems, context, owner=owner)

    systems.state_removal_coordinator.remove(
        context,
        operation=RemovalOperation.NATURAL_EXPIRY,
        instance_id=insight.instance_id,
    )

    assert owner.is_preparing("a")
    assert port.requests == []

    root = (StateNode(exhaustion.instance_id),)
    before = systems.effectiveness_transition_coordinator.capture(context, root)
    context.metadata["audit_second_suppressor"] = False
    systems.effectiveness_transition_coordinator.settle(context, before, root)

    assert len(port.requests) == 1
    assert not owner.is_preparing("a")


def test_same_envelope_expiry_does_not_interrupt() -> None:
    context = make_context()
    owner = PreparationStateOwner()
    port = RecordingPort(owner)
    systems = BattleSystems(preparation_interruption_port=port)
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
    port.requests.clear()
    begin_preparing(systems, context, owner=owner)

    settle_due(
        systems,
        context,
        round_no=2,
        phase=BattlePhase.ROUND_END.value,
    )

    assert port.requests == []
    assert owner.is_preparing("a")
    assert not context.states.has_instance(exhaustion.instance_id)
    assert not context.states.has_instance(insight.instance_id)


def test_insight_rejected_exhaustion_does_not_interrupt() -> None:
    context = make_context()
    owner = PreparationStateOwner()
    port = RecordingPort(owner)
    systems = BattleSystems(preparation_interruption_port=port)
    begin_preparing(systems, context, owner=owner)
    assert apply_state(
        systems, context, OfficialStateId.INSIGHT.value
    ).status is StateApplicationResultStatus.APPLIED
    port.requests.clear()

    result = apply_state(systems, context, OfficialStateId.SILENCE.value)

    assert result.status is StateApplicationResultStatus.REJECTED_ADMISSION
    assert port.requests == []
    assert owner.is_preparing("a")


def test_continuation_not_preparing_is_not_interrupted() -> None:
    context = make_context()
    systems = BattleSystems()
    item = active_runtime()
    context.skill_runtimes.register(item)
    ref = SkillProviderRef("a", SkillSlot.INHERENT, item.definition.skill_id)

    decision = systems.skill_permission_policy.evaluate(
        context,
        SkillPermissionRequest(
            actor_id="a",
            provider_ref=ref,
            skill_type=SkillType.ACTIVE,
            preparation_mode=PreparationMode.NONE,
            operation_kind=SkillOperationKind.CONTINUATION,
        ),
    )
    assert decision.status is SkillPermissionStatus.CONTINUATION_NOT_REEVALUATED

    apply_state(systems, context, OfficialStateId.SILENCE.value)

    after = systems.skill_permission_policy.evaluate(
        context,
        SkillPermissionRequest(
            actor_id="a",
            provider_ref=ref,
            skill_type=SkillType.ACTIVE,
            preparation_mode=PreparationMode.NONE,
            operation_kind=SkillOperationKind.CONTINUATION,
        ),
    )
    assert after.status is SkillPermissionStatus.CONTINUATION_NOT_REEVALUATED
    assert not systems.preparation_state_owner.is_preparing("a")


def test_provider_invalid_precedes_exhaustion_permission() -> None:
    context = make_context()
    systems = BattleSystems()
    item = active_runtime(enabled=False)
    context.skill_runtimes.register(item)
    apply_state(systems, context, OfficialStateId.SILENCE.value)

    decision = systems.skill_operation_admission_coordinator.evaluate(
        context,
        SkillOperationAdmissionRequest(
            actor_id="a",
            provider_ref=SkillProviderRef(
                "a", SkillSlot.INHERENT, item.definition.skill_id
            ),
            skill_type=SkillType.ACTIVE,
            preparation_mode=PreparationMode.NONE,
        ),
    )

    assert decision.status is SkillOperationAdmissionStatus.DENY_PROVIDER_INVALID
    assert decision.permission_decision is None


def test_active_deny_zero_rng() -> None:
    rng = CountingRandomSystem()
    context = make_context(rng)
    systems = BattleSystems()
    item = active_runtime()
    context.skill_runtimes.register(item)
    apply_state(systems, context, OfficialStateId.SILENCE.value)

    result = systems.skill_resolver.resolve(context, item)

    assert result.status is SkillResolutionStatus.DISABLED
    assert rng.chance_calls == 0
    assert rng.sample_calls == 0


def test_post_commit_callback_failure_does_not_rollback_registry() -> None:
    context = make_context()
    port = RaisingPort()
    systems = BattleSystems(preparation_interruption_port=port)

    with pytest.raises(
        RuntimeError,
        match="audit synthetic post-commit interruption failure",
    ):
        apply_state(systems, context, OfficialStateId.SILENCE.value)

    assert port.calls == 1
    residents = context.states.find(
        owner_id="a",
        state_id=OfficialStateId.SILENCE.value,
    )
    assert len(residents) == 1
    assert systems.state_effectiveness_policy.evaluate_state(
        context, residents[0]
    ).effective


def test_query_paths_emit_no_events_and_architecture_has_no_stage15_leakage() -> None:
    context = make_context()
    systems = BattleSystems()
    begin_preparing(systems, context)
    before = context.event_bus.history

    systems.preparation_state_owner.get_preparing("a")
    systems.preparation_state_owner.is_preparing("a")
    systems.skill_permission_policy.evaluate(
        context,
        SkillPermissionRequest(
            actor_id="a",
            provider_ref=SkillProviderRef(
                "a", SkillSlot.INHERENT, "audit.preparing.active"
            ),
            skill_type=SkillType.ACTIVE,
            preparation_mode=PreparationMode.REQUIRED,
        ),
    )
    assert context.event_bus.history == before

    battle_systems_source = inspect.getsource(battle_systems_module)
    application_source = inspect.getsource(state_application_module)
    assert "NoopPreparationInterruptionPort()" not in battle_systems_source
    assert "CommittedEffectiveStateActivation" in application_source
    assert "EXHAUSTION" not in application_source
    assert "SILENCE" not in application_source
