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
    EventType,
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
from sgs_v2.battle_core import exhaustion_integration as exhaustion_module
from sgs_v2.battle_core.exhaustion_integration import (
    EXHAUSTION_PERMISSION_RULE_ID,
    EXHAUSTION_PREPARATION_INTERRUPTION_RULE_ID,
)
from sgs_v2.battle_core.preparation_interruption import (
    PreparationInterruptionRequest,
    PreparationInterruptionResult,
    PreparationInterruptionScope,
    PreparationInterruptionStatus,
)
from sgs_v2.battle_core.provider_identity import SkillProviderRef
from sgs_v2.battle_core.state_effectiveness import (
    LocalRuleCauseRef,
    StateEffectivenessContribution,
    SuppressionCause,
)


class CountingRandomSystem(RandomSystem):
    def __init__(self, seed: int = 690101, *, chance_result: bool | None = None) -> None:
        super().__init__(seed)
        self.chance_result = chance_result
        self.chance_calls = 0
        self.sample_calls = 0

    def chance(self, probability: float) -> bool:
        self.chance_calls += 1
        if self.chance_result is not None:
            return self.chance_result
        return super().chance(probability)

    def sample(self, values, k):  # type: ignore[no-untyped-def]
        self.sample_calls += 1
        return super().sample(values, k)


class FakePreparationInterruptionPort:
    def __init__(self, preparing: tuple[SkillProviderRef, ...] = ()) -> None:
        self.preparing = list(preparing)
        self.requests: list[PreparationInterruptionRequest] = []

    def interrupt(self, context, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        if request.scope is not PreparationInterruptionScope.HOLDER_ACTIVE:
            return PreparationInterruptionResult(
                request,
                PreparationInterruptionStatus.UNSUPPORTED,
            )
        matched = [
            item for item in self.preparing
            if item.owner_id == request.holder_id
        ]
        if not matched:
            return PreparationInterruptionResult(
                request,
                PreparationInterruptionStatus.NOT_PREPARING,
            )
        for item in matched:
            self.preparing.remove(item)
        return PreparationInterruptionResult(
            request,
            PreparationInterruptionStatus.INTERRUPTED,
            tuple(matched),
        )


def make_context(
    random_system: RandomSystem | None = None,
    *,
    second_enemy: bool = True,
) -> BattleContext:
    units = {
        "a": UnitRuntime(
            "a", "A", "A", 1000, 1000, 300, 100, 100,
            lineup_position=LineupPosition.COMMANDER,
        ),
        "b": UnitRuntime(
            "b", "B", "B", 1000, 1000, 100, 100, 90,
            lineup_position=LineupPosition.COMMANDER,
        ),
    }
    if second_enemy:
        units["c"] = UnitRuntime(
            "c", "C", "B", 1000, 1000, 100, 100, 80,
            lineup_position=LineupPosition.DEPUTY_1,
        )
    context = BattleContext(
        battle_id="stage12-690101",
        units=units,
        event_bus=EventBus(),
        random=random_system or RandomSystem(690101),
    )
    register_official_state_definitions(context.states)
    context.current_round = 1
    context.current_phase = BattlePhase.UNIT_ACTION.value
    return context


def candidate(
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
        application_provenance="stage12-690101-runtime-test",
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
        candidate(state_id, lifetime_spec=lifetime_spec),
    )


def definition(
    *,
    skill_id: str = "synthetic.exhaustion",
    rate: float = 0.5,
    skill_type: SkillType = SkillType.ACTIVE,
    preparation_mode: PreparationMode = PreparationMode.NONE,
) -> SkillDefinition:
    return SkillDefinition(
        skill_id=skill_id,
        name=skill_id,
        activation_rate=rate,
        target_mode=SkillTargetMode.SINGLE_RANDOM_ENEMY,
        effect_specs=(DamageSkillEffectSpec(DamageType.WEAPON),),
        skill_type=skill_type,
        preparation_mode=preparation_mode,
    )


def runtime(
    *,
    skill_id: str = "synthetic.exhaustion",
    rate: float = 0.5,
    skill_type: SkillType = SkillType.ACTIVE,
    preparation_mode: PreparationMode = PreparationMode.NONE,
    enabled: bool = True,
) -> SkillRuntime:
    return SkillRuntime(
        definition=definition(
            skill_id=skill_id,
            rate=rate,
            skill_type=skill_type,
            preparation_mode=preparation_mode,
        ),
        owner_id="a",
        skill_slot=SkillSlot.INHERENT,
        enabled=enabled,
    )


def permission_request(
    *,
    skill_type: SkillType = SkillType.ACTIVE,
    preparation_mode: PreparationMode = PreparationMode.NONE,
    operation_kind: SkillOperationKind = SkillOperationKind.NEW_ADMISSION,
) -> SkillPermissionRequest:
    return SkillPermissionRequest(
        actor_id="a",
        provider_ref=SkillProviderRef("a", SkillSlot.INHERENT, "synthetic.exhaustion"),
        skill_type=skill_type,
        preparation_mode=preparation_mode,
        operation_kind=operation_kind,
    )


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


def test_exhaustion_application_and_effective_truth() -> None:
    context = make_context()
    systems = BattleSystems()

    result = apply_state(systems, context, OfficialStateId.SILENCE.value)

    assert result.status is StateApplicationResultStatus.APPLIED
    assert result.instance is not None
    assert systems.state_effectiveness_policy.has_effective(
        context, "a", OfficialStateId.SILENCE.value
    )


def test_exhaustion_state_application_uses_zero_rng() -> None:
    rng = CountingRandomSystem(seed=11)
    context = make_context(rng)
    systems = BattleSystems()

    apply_state(systems, context, OfficialStateId.SILENCE.value)

    assert rng.chance_calls == 0
    assert rng.sample_calls == 0


def test_active_skill_permission_denied() -> None:
    context = make_context()
    systems = BattleSystems()
    apply_state(systems, context, OfficialStateId.SILENCE.value)

    decision = systems.skill_permission_policy.evaluate(
        context,
        permission_request(),
    )

    assert decision.status is SkillPermissionStatus.DENY_STATE_PERMISSION
    assert decision.blocker_keys == (EXHAUSTION_PERMISSION_RULE_ID,)


def test_legacy_active_skill_denied() -> None:
    context = make_context()
    systems = BattleSystems()
    apply_state(systems, context, OfficialStateId.SILENCE.value)
    item = SkillDefinition(
        "legacy.exhaustion",
        "Legacy Exhaustion",
        1.0,
        SkillTargetMode.SINGLE_RANDOM_ENEMY,
        (DamageSkillEffectSpec(DamageType.WEAPON),),
    )

    decision = systems.skill_permission_policy.evaluate(
        context,
        SkillPermissionRequest(
            actor_id="a",
            provider_ref=SkillProviderRef("a", SkillSlot.INHERENT, item.skill_id),
            skill_type=item.skill_type,
            preparation_mode=item.preparation_mode,
        ),
    )

    assert item.skill_type is SkillType.ACTIVE
    assert item.preparation_mode is PreparationMode.NONE
    assert decision.status is SkillPermissionStatus.DENY_STATE_PERMISSION


@pytest.mark.parametrize(
    "preparation_mode",
    [PreparationMode.NONE, PreparationMode.REQUIRED],
)
def test_active_denial_is_not_merely_a_preparation_block(
    preparation_mode: PreparationMode,
) -> None:
    context = make_context()
    systems = BattleSystems()
    apply_state(systems, context, OfficialStateId.SILENCE.value)

    decision = systems.skill_permission_policy.evaluate(
        context,
        permission_request(preparation_mode=preparation_mode),
    )

    assert decision.status is SkillPermissionStatus.DENY_STATE_PERMISSION


@pytest.mark.parametrize(
    "skill_type",
    [
        SkillType.ASSAULT,
        SkillType.PASSIVE,
        SkillType.COMMAND,
        SkillType.TROOP,
        SkillType.FORMATION,
    ],
)
def test_non_active_skill_types_are_not_denied(skill_type: SkillType) -> None:
    context = make_context()
    systems = BattleSystems()
    apply_state(systems, context, OfficialStateId.SILENCE.value)

    decision = systems.skill_permission_policy.evaluate(
        context,
        permission_request(skill_type=skill_type),
    )

    assert decision.status is SkillPermissionStatus.ALLOW


def test_already_admitted_continuation_is_not_reevaluated() -> None:
    context = make_context()
    systems = BattleSystems()
    apply_state(systems, context, OfficialStateId.SILENCE.value)

    decision = systems.skill_permission_policy.evaluate(
        context,
        permission_request(operation_kind=SkillOperationKind.CONTINUATION),
    )

    assert decision.status is SkillPermissionStatus.CONTINUATION_NOT_REEVALUATED
    assert decision.allowed


def test_exhaustion_does_not_toggle_skill_runtime_enabled() -> None:
    context = make_context()
    systems = BattleSystems()
    item = runtime(enabled=True)
    context.skill_runtimes.register(item)
    apply_state(systems, context, OfficialStateId.SILENCE.value)

    systems.skill_permission_policy.evaluate(context, permission_request())

    assert item.enabled is True


def test_exhaustion_denial_consumes_zero_activation_and_target_rng() -> None:
    rng = CountingRandomSystem(chance_result=True)
    context = make_context(rng)
    systems = BattleSystems()
    item = runtime(rate=0.5)
    context.skill_runtimes.register(item)
    apply_state(systems, context, OfficialStateId.SILENCE.value)

    result = systems.skill_resolver.resolve(context, item)

    assert result.status is SkillResolutionStatus.DISABLED
    assert rng.chance_calls == 0
    assert rng.sample_calls == 0


def test_exhaustion_denial_creates_no_target_operation() -> None:
    context = make_context()
    systems = BattleSystems()
    item = runtime(rate=1.0)
    context.skill_runtimes.register(item)
    apply_state(systems, context, OfficialStateId.SILENCE.value)

    result = systems.skill_resolver.resolve(context, item)

    assert result.status is SkillResolutionStatus.DISABLED
    assert str(context.id_allocator.allocate_target_operation_id()) == "top_1"


def test_provider_invalid_wins_before_exhaustion_permission() -> None:
    context = make_context()
    systems = BattleSystems()
    item = runtime(enabled=False)
    context.skill_runtimes.register(item)
    apply_state(systems, context, OfficialStateId.SILENCE.value)

    decision = systems.skill_operation_admission_coordinator.evaluate(
        context,
        SkillOperationAdmissionRequest(
            actor_id="a",
            provider_ref=SkillProviderRef(
                "a",
                SkillSlot.INHERENT,
                item.definition.skill_id,
            ),
            skill_type=SkillType.ACTIVE,
            preparation_mode=PreparationMode.NONE,
        ),
    )

    assert decision.status is SkillOperationAdmissionStatus.DENY_PROVIDER_INVALID
    assert decision.permission_decision is None


def test_natural_action_and_normal_attack_are_not_denied_by_exhaustion() -> None:
    context = make_context(second_enemy=False)
    systems = BattleSystems()
    apply_state(systems, context, OfficialStateId.SILENCE.value)

    result = systems.action_system.execute(context, context.get_unit("a"))

    assert result is not None
    assert any(
        event.event_type is EventType.NORMAL_ATTACK
        and event.actor_id == "a"
        for event in context.event_bus.history
    )


def test_effective_insight_rejects_incoming_exhaustion() -> None:
    context = make_context()
    systems = BattleSystems()
    assert apply_state(
        systems, context, OfficialStateId.INSIGHT.value
    ).status is StateApplicationResultStatus.APPLIED

    result = apply_state(systems, context, OfficialStateId.SILENCE.value)

    assert result.status is StateApplicationResultStatus.REJECTED_ADMISSION
    assert not context.states.has(
        owner_id="a",
        state_id=OfficialStateId.SILENCE.value,
    )


def test_resident_exhaustion_suppressed_by_insight_allows_active() -> None:
    rng = CountingRandomSystem(chance_result=True)
    context = make_context(rng)
    systems = BattleSystems()
    item = runtime(rate=0.5)
    context.skill_runtimes.register(item)
    exhaustion = apply_state(
        systems, context, OfficialStateId.SILENCE.value
    ).instance
    assert exhaustion is not None
    apply_state(systems, context, OfficialStateId.INSIGHT.value)

    assert not systems.state_effectiveness_policy.evaluate_state(
        context, exhaustion
    ).effective
    result = systems.skill_resolver.resolve(context, item)

    assert result.status is SkillResolutionStatus.RESOLVED
    assert rng.chance_calls == 1


def test_insight_expiry_resumes_exhaustion_denial() -> None:
    context = make_context()
    systems = BattleSystems()
    exhaustion = apply_state(
        systems, context, OfficialStateId.SILENCE.value
    ).instance
    insight = apply_state(
        systems, context, OfficialStateId.INSIGHT.value
    ).instance
    assert exhaustion is not None and insight is not None

    systems.state_removal_coordinator.remove(
        context,
        operation=RemovalOperation.NATURAL_EXPIRY,
        instance_id=insight.instance_id,
    )

    assert systems.state_effectiveness_policy.evaluate_state(
        context, exhaustion
    ).effective
    assert systems.skill_permission_policy.evaluate(
        context, permission_request()
    ).status is SkillPermissionStatus.DENY_STATE_PERMISSION


def test_exhaustion_expiry_while_suppressed_never_resumes() -> None:
    context = make_context()
    systems = BattleSystems()
    exhaustion = apply_state(
        systems, context, OfficialStateId.SILENCE.value
    ).instance
    insight = apply_state(
        systems, context, OfficialStateId.INSIGHT.value
    ).instance
    assert exhaustion is not None and insight is not None

    systems.state_removal_coordinator.remove(
        context,
        operation=RemovalOperation.NATURAL_EXPIRY,
        instance_id=exhaustion.instance_id,
    )
    systems.state_removal_coordinator.remove(
        context,
        operation=RemovalOperation.NATURAL_EXPIRY,
        instance_id=insight.instance_id,
    )

    assert not context.states.has(
        owner_id="a",
        state_id=OfficialStateId.SILENCE.value,
    )
    assert systems.skill_permission_policy.evaluate(
        context, permission_request()
    ).status is SkillPermissionStatus.ALLOW


def test_same_envelope_insight_and_exhaustion_expiry_has_no_ghost_denial() -> None:
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

    settle_due(
        systems,
        context,
        round_no=2,
        phase=BattlePhase.ROUND_END.value,
    )

    assert not context.states.has(
        owner_id="a",
        state_id=OfficialStateId.SILENCE.value,
    )
    assert systems.skill_permission_policy.evaluate(
        context, permission_request()
    ).status is SkillPermissionStatus.ALLOW


def test_resident_exhaustion_resume_drives_preparation_interruption_port() -> None:
    ref = SkillProviderRef("a", SkillSlot.INHERENT, "preparing.active")
    port = FakePreparationInterruptionPort()
    context = make_context()
    systems = BattleSystems(preparation_interruption_port=port)
    exhaustion = apply_state(
        systems, context, OfficialStateId.SILENCE.value
    ).instance
    insight = apply_state(
        systems, context, OfficialStateId.INSIGHT.value
    ).instance
    assert exhaustion is not None and insight is not None
    # The initial effective CREATE lawfully issued one interruption request,
    # but no preparation existed yet. This test isolates the later resume path.
    assert len(port.requests) == 1
    port.requests.clear()
    port.preparing.append(ref)

    systems.state_removal_coordinator.remove(
        context,
        operation=RemovalOperation.NATURAL_EXPIRY,
        instance_id=insight.instance_id,
    )

    assert len(port.requests) == 1
    request = port.requests[0]
    assert request.scope is PreparationInterruptionScope.HOLDER_ACTIVE
    assert request.holder_id == "a"
    assert request.cause_key == EXHAUSTION_PREPARATION_INTERRUPTION_RULE_ID
    assert port.preparing == []



def test_exhaustion_natural_expiry_removes_permission_denial() -> None:
    context = make_context()
    systems = BattleSystems()
    exhaustion = apply_state(
        systems,
        context,
        OfficialStateId.SILENCE.value,
        lifetime_spec=StateLifetimeSpec.round_calendar(expires_round=2),
    ).instance
    assert exhaustion is not None
    assert systems.skill_permission_policy.evaluate(
        context, permission_request()
    ).status is SkillPermissionStatus.DENY_STATE_PERMISSION

    settle_due(
        systems,
        context,
        round_no=2,
        phase=BattlePhase.ROUND_END.value,
    )

    assert not context.states.has_instance(exhaustion.instance_id)
    assert systems.skill_permission_policy.evaluate(
        context, permission_request()
    ).status is SkillPermissionStatus.ALLOW


def test_suppression_resume_preserves_instance_generation_and_lifetime() -> None:
    context = make_context()
    systems = BattleSystems()
    lifetime = StateLifetimeSpec.round_calendar(expires_round=4)
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
    ).instance
    assert exhaustion is not None and insight is not None
    generation = exhaustion.current_generation_id
    instance_id = exhaustion.instance_id

    systems.state_removal_coordinator.remove(
        context,
        operation=RemovalOperation.NATURAL_EXPIRY,
        instance_id=insight.instance_id,
    )

    current = context.states.get(instance_id)
    assert current.instance_id == instance_id
    assert current.current_generation_id == generation
    assert current.lifetime_spec == lifetime


def _second_exhaustion_suppressor(context, instance, _session):
    blocked = set(context.metadata.get("second_exhaustion_suppressor", ()))
    if instance.instance_id not in blocked:
        return StateEffectivenessContribution()
    return StateEffectivenessContribution(
        suppression_causes=(
            SuppressionCause(
                "TEST_SECOND_EXHAUSTION_SUPPRESSOR",
                LocalRuleCauseRef(instance.instance_id),
            ),
        )
    )


def test_removing_insight_does_not_false_resume_with_second_suppressor() -> None:
    ref = SkillProviderRef("a", SkillSlot.INHERENT, "preparing.active")
    port = FakePreparationInterruptionPort()
    context = make_context()
    systems = BattleSystems(preparation_interruption_port=port)
    systems.state_effectiveness_policy.register_rule_adapter(
        _second_exhaustion_suppressor
    )
    exhaustion = apply_state(
        systems, context, OfficialStateId.SILENCE.value
    ).instance
    assert exhaustion is not None
    context.metadata["second_exhaustion_suppressor"] = (exhaustion.instance_id,)
    insight = apply_state(
        systems, context, OfficialStateId.INSIGHT.value
    ).instance
    assert insight is not None
    assert not systems.state_effectiveness_policy.evaluate_state(
        context, exhaustion
    ).effective
    # Initial CREATE was effective before the synthetic second suppressor was
    # installed, so isolate this test from that already-completed command.
    port.requests.clear()
    port.preparing.append(ref)

    systems.state_removal_coordinator.remove(
        context,
        operation=RemovalOperation.NATURAL_EXPIRY,
        instance_id=insight.instance_id,
    )

    assert not systems.state_effectiveness_policy.evaluate_state(
        context, exhaustion
    ).effective
    assert port.requests == []
    assert systems.skill_permission_policy.evaluate(
        context, permission_request()
    ).status is SkillPermissionStatus.ALLOW


def test_permission_query_emits_no_event() -> None:
    context = make_context()
    systems = BattleSystems()
    apply_state(systems, context, OfficialStateId.SILENCE.value)
    before = context.event_bus.history

    systems.skill_permission_policy.evaluate(context, permission_request())

    assert context.event_bus.history == before

def test_exhaustion_reapplication_remains_explicit_unsupported_boundary() -> None:
    context = make_context()
    systems = BattleSystems()
    assert apply_state(
        systems, context, OfficialStateId.SILENCE.value
    ).status is StateApplicationResultStatus.APPLIED

    second = apply_state(systems, context, OfficialStateId.SILENCE.value)

    assert second.status is StateApplicationResultStatus.UNSUPPORTED_BOUNDARY


def test_exhaustion_integration_static_architecture_guards() -> None:
    source = inspect.getsource(exhaustion_module)

    assert "enabled =" not in source
    assert "context.random" not in source
    assert "TargetSystem" not in source
    assert "ActionSystem" not in source
    assert "EventBus" not in source
