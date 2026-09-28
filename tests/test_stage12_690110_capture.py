from __future__ import annotations

import inspect

import pytest

from sgs_v2.battle_core import (
    BattleContext,
    BattleEngine,
    BattlePhase,
    BattleSystems,
    DamageDeniedEffectResult,
    DamageEffect,
    DamageExecutionWork,
    DamageSkillEffectSpec,
    DamageSourceType,
    DamageType,
    DamageWorkKind,
    EmptyStateRuntimeParams,
    EquipmentAttributeContribution,
    EquipmentContributionKind,
    EquipmentContributionRef,
    EquipmentEffectivenessStatus,
    EquipmentProviderRef,
    EventBus,
    EventType,
    ExecutionRightEvaluationStatus,
    ExecutionRightMode,
    ExecutionRightRequest,
    ExecutionRightSpec,
    FutureBranchKind,
    LineupPosition,
    OfficialStateId,
    ProviderDependency,
    ProviderValidityStatus,
    RandomSystem,
    RecoveryPreventionReason,
    RecoveryPreventedResult,
    RecoveryRequest,
    RecoveryResolvedResult,
    RemovalOperation,
    SkillDefinition,
    SkillProviderRef,
    SkillResolutionStatus,
    SkillRuntime,
    SkillSlot,
    SkillTargetMode,
    SkillType,
    SourceType,
    StateApplicationResultStatus,
    StateCandidate,
    StateEffectivenessStatus,
    StateLifetimeSpec,
    StateNode,
    StateRemovalResultStatus,
    TargetCardinality,
    TargetEligibilityContext,
    TargetOperationDomain,
    TargetOperationProducer,
    TargetPolicyBoundary,
    TargetPurpose,
    TargetQueryMode,
    TargetRelation,
    TargetSelectionProvenance,
    TargetSelectionResult,
    TargetSelectorKind,
    UnitRuntime,
    register_official_state_definitions,
)
from sgs_v2.battle_core import capture_integration as capture_module
from sgs_v2.battle_core.capture_integration import (
    CAPTURE_ACTOR_PERMISSION_RULE_ID,
    CAPTURE_EQUIPMENT_ATTRIBUTE_RULE_ID,
    CAPTURE_PROVIDER_SUPPRESSION_RULE_ID,
    CAPTURE_RECOVERY_PREVENTION_RULE_ID,
    CAPTURE_REAPPLICATION_BOUNDARY_RULE_ID,
)
from sgs_v2.battle_core.chain_system import ResolvedDamageFact
from sgs_v2.battle_core.execution_right_system import admit_action_scope
from sgs_v2.battle_core.operation_identity import OperationLineage
from sgs_v2.battle_core.stage11_state_params import (
    Stage11TimedFlagParams,
    StunStateParams,
)
from sgs_v2.battle_core.stage9_state_params import CounterStateParams


class CountingRandomSystem(RandomSystem):
    def __init__(self, seed: int = 690110, chance_result: bool | None = None) -> None:
        super().__init__(seed)
        self.chance_result = chance_result
        self.chance_calls = 0
        self.choice_calls = 0
        self.sample_calls = 0

    def chance(self, probability: float) -> bool:
        self.chance_calls += 1
        if self.chance_result is not None:
            return self.chance_result
        return super().chance(probability)

    def choice(self, values):  # type: ignore[no-untyped-def]
        self.choice_calls += 1
        return super().choice(values)

    def sample(self, values, k):  # type: ignore[no-untyped-def]
        self.sample_calls += 1
        return super().sample(values, k)


def make_context(rng: RandomSystem | None = None, *, max_rounds: int = 8) -> BattleContext:
    context = BattleContext(
        battle_id="stage12-690110",
        units={
            "a": UnitRuntime(
                "a", "A", "A", 10000, 5000, 300, 120, 120,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "x": UnitRuntime(
                "x", "X", "A", 10000, 5000, 140, 100, 110,
                lineup_position=LineupPosition.DEPUTY_1,
            ),
            "y": UnitRuntime(
                "y", "Y", "A", 10000, 5000, 130, 100, 100,
                lineup_position=LineupPosition.DEPUTY_2,
            ),
            "b": UnitRuntime(
                "b", "B", "B", 10000, 5000, 210, 110, 90,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "c": UnitRuntime(
                "c", "C", "B", 10000, 5000, 120, 100, 80,
                lineup_position=LineupPosition.DEPUTY_1,
            ),
            "d": UnitRuntime(
                "d", "D", "B", 10000, 5000, 110, 100, 70,
                lineup_position=LineupPosition.DEPUTY_2,
            ),
        },
        event_bus=EventBus(),
        random=rng or RandomSystem(690110),
        max_rounds=max_rounds,
    )
    register_official_state_definitions(context.states)
    context.current_round = 1
    context.current_phase = BattlePhase.UNIT_ACTION.value
    return context


def candidate(
    state_id: str,
    *,
    owner: str = "a",
    source: str | None = "b",
    lifetime: StateLifetimeSpec | None = None,
    runtime_params=None,
    dependencies: tuple[ProviderDependency, ...] = (),
    source_skill_id: str | None = None,
    source_skill_slot: SkillSlot | None = None,
) -> StateCandidate:
    return StateCandidate(
        state_id=state_id,
        owner_id=owner,
        source_id=source,
        source_skill_id=source_skill_id or f"source-{state_id}",
        source_skill_slot=source_skill_slot,
        runtime_params_candidate=(
            EmptyStateRuntimeParams()
            if runtime_params is None
            else runtime_params
        ),
        lifetime_spec=lifetime,
        provider_dependencies=dependencies,
        application_provenance="stage12-690110-runtime-test",
    )


def apply_state(
    systems: BattleSystems,
    context: BattleContext,
    state_id: str,
    **kwargs,
):
    return systems.state_application_coordinator.apply_candidate(
        context,
        candidate(state_id, **kwargs),
    )


def apply_capture(
    systems: BattleSystems,
    context: BattleContext,
    **kwargs,
):
    return apply_state(
        systems,
        context,
        OfficialStateId.CAPTURE.value,
        **kwargs,
    )


def expire_holder_action_window(
    systems: BattleSystems,
    context: BattleContext,
    owner_id: str,
):
    due = systems.state_lifecycle_system.due_at_action_start(context, owner_id)
    roots = tuple(StateNode(item.instance_id) for item in due)
    before = systems.effectiveness_transition_coordinator.capture(context, roots)
    removed = systems.state_lifecycle_system.settle_action_start_lifetimes(
        context,
        owner_id,
    )
    systems.effectiveness_transition_coordinator.complete_removed_nodes(
        context,
        before,
        tuple(StateNode(item.instance_id) for item in removed),
    )
    return removed


def natural_action(
    systems: BattleSystems,
    context: BattleContext,
    actor_id: str = "a",
):
    permit = systems.future_admission_gate.request_admission(
        FutureBranchKind.NEXT_ACTION,
        f"capture-action-{actor_id}",
    )
    assert permit is not None
    scope = admit_action_scope(
        context,
        systems.future_admission_gate,
        permit,
        context.get_unit(actor_id),
        f"capture-action-{actor_id}",
    )
    try:
        return systems.action_system.execute(
            context,
            context.get_unit(actor_id),
            action_scope=scope,
        )
    finally:
        systems.finalization_coordinator.complete_action_scope(context, scope)


def skill_runtime(
    *,
    owner: str = "a",
    slot: SkillSlot = SkillSlot.INHERENT,
    skill_id: str = "capture-fixture-skill",
    skill_type: SkillType = SkillType.ACTIVE,
    target_mode: SkillTargetMode = SkillTargetMode.SINGLE_RANDOM_ENEMY,
    target_count: int | None = None,
    activation_rate: float = 1.0,
) -> SkillRuntime:
    return SkillRuntime(
        definition=SkillDefinition(
            skill_id=skill_id,
            name=skill_id,
            activation_rate=activation_rate,
            target_mode=target_mode,
            target_count=target_count,
            effect_specs=(DamageSkillEffectSpec(DamageType.WEAPON),),
            skill_type=skill_type,
        ),
        owner_id=owner,
        skill_slot=slot,
    )


def register_runtime(context: BattleContext, **kwargs) -> SkillRuntime:
    item = skill_runtime(**kwargs)
    context.skill_runtimes.register(item)
    return item


def provider_ref(item: SkillRuntime) -> SkillProviderRef:
    assert item.skill_slot is not None
    return SkillProviderRef(
        item.owner_id,
        item.skill_slot,
        item.definition.skill_id,
    )


def active_damage_effect(
    *,
    source: str = "a",
    target: str = "b",
    skill_id: str = "active-damage",
) -> DamageEffect:
    return DamageEffect(
        source,
        target,
        DamageType.WEAPON,
        DamageSourceType.SKILL,
        source_skill_id=skill_id,
        source_ref=capture_source_ref(
            SourceType.ACTIVE_SKILL,
            source,
            skill_id,
        ),
    )


def periodic_damage_effect(
    *,
    source: str = "a",
    target: str = "b",
    skill_id: str = "active-damage",
) -> DamageEffect:
    return DamageEffect(
        source,
        target,
        DamageType.WEAPON,
        DamageSourceType.CONTINUOUS,
        source_skill_id=skill_id,
        source_state_id="burn",
        source_state_instance_id="burn-fixture",
        source_ref=capture_source_ref(
            SourceType.PERIODIC_DAMAGE,
            source,
            skill_id,
        ),
    )


def capture_source_ref(
    source_type: SourceType,
    source_id: str,
    skill_id: str,
):
    from sgs_v2.battle_core import EffectSourceRef

    return EffectSourceRef(
        source_type,
        source_id,
        skill_id,
        SkillSlot.INHERENT,
    )


def main_normal_attack_fact(
    context: BattleContext,
    *,
    target: str = "b",
    attacker: str = "a",
) -> ResolvedDamageFact:
    return ResolvedDamageFact(
        context.id_allocator.allocate_damage_instance_id(),
        target,
        OperationLineage(
            context.id_allocator.allocate_action_id(),
            context.id_allocator.allocate_normal_attack_id(),
            None,
            SourceType.NORMAL_ATTACK,
            attacker,
            None,
            attacker,
        ),
        DamageType.WEAPON,
        100,
        100,
    )


def create_counter_batch(
    systems: BattleSystems,
    context: BattleContext,
    *,
    owner: str = "b",
    attacker: str = "a",
):
    systems.state_lifecycle_system.apply(
        context,
        state_id="counterattack",
        owner_id=owner,
        runtime_params=CounterStateParams(),
        source_id=owner,
        source_skill_id="counter-fixture",
        source_skill_slot=SkillSlot.INHERENT,
    )
    fact = main_normal_attack_fact(
        context,
        target=owner,
        attacker=attacker,
    )
    permit = systems.future_admission_gate.request_admission(
        FutureBranchKind.COUNTER_BATCH,
        str(fact.lineage.parent_normal_attack_id),
    )
    assert permit is not None
    return systems.counter_system.create_batch(context, fact, permit=permit)


def register_equipment_attribute(
    systems: BattleSystems,
    *,
    owner: str = "a",
    key: str = "weapon:capture-attr",
    amount: float = 50.0,
):
    provider = EquipmentProviderRef(owner, key)
    systems.equipment_contribution_registry.register_provider(provider)
    ref = EquipmentContributionRef(
        provider,
        f"{key}:attack",
        EquipmentContributionKind.ATTRIBUTE,
    )
    systems.equipment_contribution_registry.register_contribution(ref)
    contribution = EquipmentAttributeContribution(ref, "attack", amount)

    def provider_fn(_context, unit, attribute):
        if unit.unit_id == owner and attribute == "attack":
            return (contribution,)
        return ()

    systems.attribute_system.register_equipment_contribution_provider(provider_fn)
    return provider, ref


def test_capture_application_effective_truth_and_zero_adapter_rng() -> None:
    rng = CountingRandomSystem()
    context, systems = make_context(rng), BattleSystems()

    result = apply_capture(systems, context)

    assert result.status is StateApplicationResultStatus.APPLIED
    assert result.instance is not None
    assert systems.state_effectiveness_policy.evaluate_state(
        context,
        result.instance,
    ).status is StateEffectivenessStatus.EFFECTIVE
    assert (rng.chance_calls, rng.choice_calls, rng.sample_calls) == (0, 0, 0)


def test_insight_does_not_reject_capture() -> None:
    context, systems = make_context(), BattleSystems()
    apply_state(systems, context, OfficialStateId.INSIGHT.value, owner="a")

    result = apply_capture(systems, context, owner="a")

    assert result.status is StateApplicationResultStatus.APPLIED
    assert result.instance is not None
    assert systems.state_effectiveness_policy.evaluate_state(
        context, result.instance
    ).effective


def test_ordinary_cleanse_rejected_and_capture_remains() -> None:
    context, systems = make_context(), BattleSystems()
    capture = apply_capture(systems, context).instance
    assert capture is not None

    result = systems.state_removal_coordinator.remove(
        context,
        operation=RemovalOperation.ORDINARY_CLEANSE,
        instance_id=capture.instance_id,
    )

    assert result.status is StateRemovalResultStatus.REJECTED
    assert context.states.has_instance(capture.instance_id)


def test_specialized_and_scripted_capture_removal_stay_bounded() -> None:
    context, systems = make_context(), BattleSystems()
    capture = apply_capture(systems, context).instance
    assert capture is not None

    for operation in (
        RemovalOperation.SPECIALIZED_CLEANSE,
        RemovalOperation.SCRIPTED_GAMEPLAY_REMOVE,
    ):
        result = systems.state_removal_coordinator.remove(
            context,
            operation=operation,
            instance_id=capture.instance_id,
        )
        assert result.status is StateRemovalResultStatus.UNSUPPORTED_BOUNDARY
        assert context.states.has_instance(capture.instance_id)


def test_source_death_does_not_remove_established_capture() -> None:
    context, systems = make_context(), BattleSystems()
    capture = apply_capture(systems, context, owner="a", source="b").instance
    assert capture is not None

    context.get_unit("b").troops = 0
    systems.defeat_cleanup_port.commit_defeat(context, "b")

    assert context.states.has_instance(capture.instance_id)
    assert systems.state_effectiveness_policy.evaluate_state(
        context, capture
    ).effective


def test_capture_reapplication_is_explicit_unsupported_boundary() -> None:
    context, systems = make_context(), BattleSystems()
    first = apply_capture(systems, context, owner="a").instance
    assert first is not None

    second = apply_capture(systems, context, owner="a", source="c")

    assert second.status is StateApplicationResultStatus.UNSUPPORTED_BOUNDARY
    assert second.reason_rule_id == CAPTURE_REAPPLICATION_BOUNDARY_RULE_ID
    assert context.states.has_instance(first.instance_id)


def test_capture_natural_expiry_restores_future_only() -> None:
    context, systems = make_context(), BattleSystems()
    capture = apply_capture(
        systems,
        context,
        lifetime=StateLifetimeSpec.holder_action_window(1),
    ).instance
    assert capture is not None

    removed = expire_holder_action_window(systems, context, "a")

    assert tuple(item.instance_id for item in removed) == (capture.instance_id,)
    assert not context.states.has_instance(capture.instance_id)


def test_captured_holder_natural_action_denied_before_normal_attack_and_rng() -> None:
    rng = CountingRandomSystem()
    context, systems = make_context(rng), BattleSystems()
    apply_capture(systems, context, owner="a")

    before = len(
        [e for e in context.event_bus.history if e.event_type is EventType.NORMAL_ATTACK]
    )
    result = natural_action(systems, context, "a")

    assert result is None
    assert len(
        [e for e in context.event_bus.history if e.event_type is EventType.NORMAL_ATTACK]
    ) == before
    assert (rng.choice_calls, rng.sample_calls) == (0, 0)
    blocked = [
        e for e in context.event_bus.history
        if e.event_type is EventType.ACTION_BLOCKED and e.actor_id == "a"
    ]
    assert blocked
    assert CAPTURE_ACTOR_PERMISSION_RULE_ID in blocked[-1].payload["blocker_keys"]


def test_capture_plus_stun_does_not_consume_stun_counter() -> None:
    context, systems = make_context(), BattleSystems()
    stun = apply_state(
        systems,
        context,
        OfficialStateId.STUN.value,
        owner="a",
        runtime_params=StunStateParams(remaining_blocks=1),
    ).instance
    assert stun is not None
    apply_capture(systems, context, owner="a")

    assert natural_action(systems, context, "a") is None

    current = context.states.get(stun.instance_id)
    assert isinstance(current.runtime_params, StunStateParams)
    assert current.runtime_params.remaining_blocks == 1


def test_battle_engine_production_consumer_never_starts_captured_action() -> None:
    rng = CountingRandomSystem()
    context = BattleContext(
        battle_id="capture-engine",
        units={
            "a": UnitRuntime(
                "a", "A", "A", 10000, 5000, 300, 120, 120,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "b": UnitRuntime(
                "b", "B", "B", 10000, 5000, 200, 100, 90,
                lineup_position=LineupPosition.COMMANDER,
            ),
        },
        event_bus=EventBus(),
        random=rng,
        max_rounds=1,
    )
    register_official_state_definitions(context.states)
    systems = BattleSystems()
    apply_capture(systems, context, owner="a", source="b")

    BattleEngine(context, systems).run()

    assert not any(
        e.event_type is EventType.NORMAL_ATTACK and e.actor_id == "a"
        for e in context.event_bus.history
    )


def test_new_actor_driven_damage_is_denied_before_damage_instance() -> None:
    context, systems = make_context(), BattleSystems()
    apply_capture(systems, context, owner="a")
    before_troops = context.get_unit("b").troops
    before_seq = context.id_allocator._damage_instance_seq

    result = systems.effect_executor.execute(
        context,
        active_damage_effect(source="a", target="b"),
    )

    assert isinstance(result, DamageDeniedEffectResult)
    assert result.execution_right.status is ExecutionRightEvaluationStatus.DENY_ACTOR
    assert context.get_unit("b").troops == before_troops
    assert context.id_allocator._damage_instance_seq == before_seq


def test_capture_damage_denial_preempts_weakness_zero_damage_path(monkeypatch) -> None:
    context, systems = make_context(), BattleSystems()
    apply_capture(systems, context, owner="a")
    apply_state(
        systems,
        context,
        OfficialStateId.WEAKNESS.value,
        owner="a",
        runtime_params=Stage11TimedFlagParams(),
    )

    def forbidden(*_args, **_kwargs):
        pytest.fail("Capture-denied damage reached DamageSystem.calculate")

    monkeypatch.setattr(systems.damage_system, "calculate", forbidden)

    result = systems.effect_executor.execute(
        context,
        active_damage_effect(source="a", target="b"),
    )
    assert isinstance(result, DamageDeniedEffectResult)


def test_counter_opportunity_exists_but_counter_damage_is_denied(monkeypatch) -> None:
    context, systems = make_context(), BattleSystems()
    batch = create_counter_batch(systems, context, owner="b", attacker="a")
    assert batch.entries
    apply_capture(systems, context, owner="b", source="a")
    before = context.get_unit("a").troops

    def forbidden(*_args, **_kwargs):
        pytest.fail("Capture-denied counter entered DamageSystem.calculate")

    monkeypatch.setattr(systems.damage_system, "calculate", forbidden)

    result = systems.counter_system.execute(context, batch)

    assert len(result) == len(batch.entries)
    assert all(item.executed for item in result)
    assert all(item.actual_troop_loss == 0 for item in result)
    assert all(item.damage_execution is None for item in result)
    assert context.get_unit("a").troops == before
    assert any(
        e.event_type is EventType.COUNTER_EXECUTE and e.actor_id == "b"
        for e in context.event_bus.history
    )


def test_attached_active_origin_dot_continues_after_capture() -> None:
    context, systems = make_context(), BattleSystems()
    apply_capture(systems, context, owner="a")
    before = context.get_unit("b").troops

    result = systems.effect_executor.execute(
        context,
        periodic_damage_effect(source="a", target="b"),
    )

    assert not isinstance(result, DamageDeniedEffectResult)
    assert result.resolution.actual_target_troop_loss > 0
    assert context.get_unit("b").troops < before


def test_historical_captured_source_does_not_block_free_proxy_actor() -> None:
    context, systems = make_context(), BattleSystems()
    apply_capture(systems, context, owner="a")
    work = DamageExecutionWork(
        DamageWorkKind.FREE_PROXY_DAMAGE,
        ExecutionRightSpec(
            actor_permission=ExecutionRightMode.RECHECK_AT_EXECUTION,
        ),
        ExecutionRightRequest(
            current_actor_id="b",
            actor_operation_kind=DamageWorkKind.FREE_PROXY_DAMAGE.value,
            historical_source_id="a",
            damage_source_id="a",
        ),
    )

    evaluation = systems.damage_instance_coordinator.evaluate_execution_right(
        context,
        work,
    )

    assert evaluation.status is ExecutionRightEvaluationStatus.ALLOW


def test_already_created_damage_request_boundary_is_not_guessed() -> None:
    context, systems = make_context(), BattleSystems()
    work = DamageExecutionWork(
        DamageWorkKind.ALREADY_CREATED_DAMAGE_REQUEST,
        ExecutionRightSpec(
            actor_permission=ExecutionRightMode.UNSUPPORTED_BOUNDARY,
        ),
        ExecutionRightRequest(
            current_actor_id="a",
            actor_operation_kind=DamageWorkKind.ALREADY_CREATED_DAMAGE_REQUEST.value,
        ),
    )

    evaluation = systems.damage_instance_coordinator.evaluate_execution_right(
        context,
        work,
    )

    assert evaluation.status is ExecutionRightEvaluationStatus.UNSUPPORTED_BOUNDARY


@pytest.mark.parametrize(
    "skill_type, expected",
    [
        (SkillType.PASSIVE, ProviderValidityStatus.SUPPRESSED),
        (SkillType.COMMAND, ProviderValidityStatus.SUPPRESSED),
        (SkillType.ACTIVE, ProviderValidityStatus.VALID),
        (SkillType.ASSAULT, ProviderValidityStatus.VALID),
        (SkillType.TROOP, ProviderValidityStatus.VALID),
        (SkillType.FORMATION, ProviderValidityStatus.VALID),
        (SkillType.TALENT, ProviderValidityStatus.VALID),
    ],
)
def test_capture_provider_scope_is_passive_command_only(skill_type, expected) -> None:
    context = make_context()
    item = register_runtime(context, skill_type=skill_type)
    systems = BattleSystems()
    apply_capture(systems, context, owner="a")

    decision = systems.provider_validity_policy.evaluate_provider(
        context,
        provider_ref(item),
    )

    assert decision.status is expected


def test_capture_provider_suppression_keeps_runtime_identity_and_enabled_flag() -> None:
    context = make_context()
    item = register_runtime(context, skill_type=SkillType.PASSIVE)
    systems = BattleSystems()
    ref = provider_ref(item)
    before = context.skill_runtimes.resolve_provider(ref).runtime

    apply_capture(systems, context, owner="a")

    after = context.skill_runtimes.resolve_provider(ref).runtime
    decision = systems.provider_validity_policy.evaluate_provider(context, ref)
    assert before is item is after
    assert item.enabled is True
    assert decision.status is ProviderValidityStatus.SUPPRESSED
    assert any(
        cause.rule_id == CAPTURE_PROVIDER_SUPPRESSION_RULE_ID
        for cause in decision.suppression_causes
    )


def test_detached_passive_origin_state_is_not_inferred_as_dependency() -> None:
    context = make_context()
    passive = register_runtime(
        context,
        skill_type=SkillType.PASSIVE,
        skill_id="passive-origin",
    )
    systems = BattleSystems()
    apply_capture(systems, context, owner="a")

    detached = apply_state(
        systems,
        context,
        OfficialStateId.PROVOKE.value,
        owner="c",
        source="a",
        source_skill_id=passive.definition.skill_id,
        source_skill_slot=SkillSlot.INHERENT,
    ).instance
    assert detached is not None

    assert systems.dependency_evaluation_support.prerequisites(
        StateNode(detached.instance_id)
    ) == ()
    assert systems.state_effectiveness_policy.evaluate_state(
        context,
        detached,
    ).effective


def test_explicit_provider_dependency_propagates_capture_and_restores() -> None:
    context = make_context()
    passive = register_runtime(
        context,
        skill_type=SkillType.PASSIVE,
        skill_id="passive-origin",
    )
    systems = BattleSystems()
    capture = apply_capture(
        systems,
        context,
        owner="a",
        lifetime=StateLifetimeSpec.holder_action_window(1),
    ).instance
    assert capture is not None

    dependent = apply_state(
        systems,
        context,
        OfficialStateId.PROVOKE.value,
        owner="c",
        source="a",
        dependencies=(ProviderDependency(provider_ref(passive), "PAIR"),),
    ).instance
    assert dependent is not None
    assert systems.state_effectiveness_policy.evaluate_state(
        context,
        dependent,
    ).status is StateEffectivenessStatus.SUPPRESSED

    expire_holder_action_window(systems, context, "a")

    assert systems.state_effectiveness_policy.evaluate_state(
        context,
        dependent,
    ).effective


def test_capture_and_false_report_provider_causes_compose_without_early_restore() -> None:
    context = make_context()
    passive = register_runtime(
        context,
        skill_type=SkillType.PASSIVE,
        skill_id="shared-passive",
    )
    systems = BattleSystems()
    apply_state(systems, context, OfficialStateId.FALSE_REPORT.value, owner="a")
    apply_capture(
        systems,
        context,
        owner="a",
        lifetime=StateLifetimeSpec.holder_action_window(1),
    )

    during = systems.provider_validity_policy.evaluate_provider(
        context,
        provider_ref(passive),
    )
    assert during.status is ProviderValidityStatus.SUPPRESSED
    assert len(during.suppression_causes) >= 2

    expire_holder_action_window(systems, context, "a")

    after = systems.provider_validity_policy.evaluate_provider(
        context,
        provider_ref(passive),
    )
    assert after.status is ProviderValidityStatus.SUPPRESSED
    assert all(
        cause.rule_id != CAPTURE_PROVIDER_SUPPRESSION_RULE_ID
        for cause in after.suppression_causes
    )


def test_provider_resume_is_future_only_no_missed_rng_replay() -> None:
    rng = CountingRandomSystem(chance_result=True)
    context = make_context(rng)
    passive = register_runtime(
        context,
        skill_type=SkillType.PASSIVE,
        activation_rate=0.5,
        skill_id="future-passive",
    )
    systems = BattleSystems()
    apply_capture(
        systems,
        context,
        owner="a",
        lifetime=StateLifetimeSpec.holder_action_window(1),
    )

    blocked = systems.skill_resolver.resolve(context, passive)
    assert blocked.status is SkillResolutionStatus.DISABLED
    assert rng.chance_calls == 0

    expire_holder_action_window(systems, context, "a")
    assert rng.chance_calls == 0

    systems.skill_resolver.resolve(context, passive)
    assert rng.chance_calls == 1


def test_received_recovery_resolves_to_zero_through_recovery_system() -> None:
    context, systems = make_context(), BattleSystems()
    context.get_unit("a").troops = 4000
    apply_capture(systems, context, owner="a")

    result = systems.recovery_system.resolve(
        context,
        RecoveryRequest("b", "a", 500),
    )

    assert isinstance(result, RecoveryPreventedResult)
    assert result.reason is RecoveryPreventionReason.FOUNDATION_POLICY
    assert result.reason_key == CAPTURE_RECOVERY_PREVENTION_RULE_ID
    assert context.get_unit("a").troops == 4000


def test_capture_and_healing_block_keep_independent_reasons() -> None:
    context, systems = make_context(), BattleSystems()
    context.get_unit("a").troops = 4000
    apply_capture(systems, context, owner="a")
    apply_state(
        systems,
        context,
        OfficialStateId.HEALING_BAN.value,
        owner="a",
        runtime_params=Stage11TimedFlagParams(),
    )

    result = systems.recovery_system.resolve(
        context,
        RecoveryRequest("b", "a", 500),
    )

    assert isinstance(result, RecoveryPreventedResult)
    assert result.reason is RecoveryPreventionReason.HEALING_BAN
    assert CAPTURE_RECOVERY_PREVENTION_RULE_ID in result.internal_reason_keys
    assert "HEALING_BAN" in result.internal_reason_keys
    assert context.get_unit("a").troops == 4000


def test_zeroed_recovery_is_not_replayed_after_capture_ends() -> None:
    context, systems = make_context(), BattleSystems()
    context.get_unit("a").troops = 4000
    apply_capture(
        systems,
        context,
        owner="a",
        lifetime=StateLifetimeSpec.holder_action_window(1),
    )

    first = systems.recovery_system.resolve(
        context,
        RecoveryRequest("b", "a", 500),
    )
    assert isinstance(first, RecoveryPreventedResult)
    expire_holder_action_window(systems, context, "a")
    assert context.get_unit("a").troops == 4000

    second = systems.recovery_system.resolve(
        context,
        RecoveryRequest("b", "a", 500),
    )
    assert isinstance(second, RecoveryResolvedResult)
    assert second.actual_recovery == 500
    assert context.get_unit("a").troops == 4500


def test_self_target_remains_eligible_under_capture() -> None:
    context = make_context()
    item = register_runtime(
        context,
        owner="a",
        target_mode=SkillTargetMode.SELF,
        skill_id="self-target",
    )
    systems = BattleSystems()
    apply_capture(systems, context, owner="a")

    result = systems.skill_resolver.resolve(context, item)

    assert result.status is SkillResolutionStatus.RESOLVED
    assert result.target_ids == ("a",)


def test_friendly_single_excludes_capture_before_random_selector() -> None:
    rng = CountingRandomSystem()
    context = make_context(rng)
    item = register_runtime(
        context,
        owner="a",
        target_mode=SkillTargetMode.SINGLE_RANDOM_ALLY,
        skill_id="friendly-single",
    )
    systems = BattleSystems()
    apply_capture(systems, context, owner="x", source="b")

    result = systems.skill_resolver.resolve(context, item)

    assert result.status is SkillResolutionStatus.RESOLVED
    assert result.target_ids == ("y",)
    assert rng.sample_calls == 0


def test_friendly_choose_n_excludes_capture_before_selector_rng() -> None:
    rng = CountingRandomSystem()
    context = make_context(rng)
    item = register_runtime(
        context,
        owner="a",
        target_mode=SkillTargetMode.CHOOSE_N_RANDOM_ALLIES,
        target_count=1,
        skill_id="friendly-choose-n",
    )
    systems = BattleSystems()
    apply_capture(systems, context, owner="x", source="b")

    result = systems.skill_resolver.resolve(context, item)

    assert result.status is SkillResolutionStatus.RESOLVED
    assert result.target_ids == ("y",)
    assert rng.sample_calls == 0


def test_friendly_choose_n_insufficient_pool_stays_explicit_boundary() -> None:
    rng = CountingRandomSystem()
    context = make_context(rng)
    item = register_runtime(
        context,
        owner="a",
        target_mode=SkillTargetMode.CHOOSE_N_RANDOM_ALLIES,
        target_count=2,
        skill_id="friendly-choose-two",
    )
    systems = BattleSystems()
    apply_capture(systems, context, owner="x", source="b")

    with pytest.raises(ValueError, match="insufficient candidates"):
        systems.skill_resolver.resolve(context, item)

    assert rng.sample_calls == 0


def test_all_allies_targeting_remains_bounded() -> None:
    context = make_context()
    item = register_runtime(
        context,
        owner="a",
        target_mode=SkillTargetMode.FIXED_ALL_ALLIES,
        skill_id="all-allies",
    )
    systems = BattleSystems()
    apply_capture(systems, context, owner="x", source="b")

    with pytest.raises(ValueError, match="unsupported Skill target-policy boundary"):
        systems.skill_resolver.resolve(context, item)


def test_enemy_targeting_is_not_changed_by_capture_target_rule() -> None:
    context = make_context()
    item = register_runtime(
        context,
        owner="b",
        target_mode=SkillTargetMode.SINGLE_DETERMINISTIC_ENEMY,
        skill_id="enemy-target",
    )
    systems = BattleSystems()
    apply_capture(systems, context, owner="a", source="b")

    result = systems.skill_resolver.resolve(context, item)

    assert result.status is SkillResolutionStatus.RESOLVED
    assert result.target_ids == ("a",)


def test_locked_target_continuation_is_not_requeried() -> None:
    context, systems = make_context(), BattleSystems()
    apply_capture(systems, context, owner="x", source="b")
    previous = TargetSelectionResult(
        operation_id=context.id_allocator.allocate_target_operation_id(),
        target_ids=("x",),
        provenance=TargetSelectionProvenance.FRESH_SELECTED,
    )

    locked = TargetOperationProducer.continue_from(
        previous,
        TargetQueryMode.LOCK_RESOLVED,
    )

    assert locked.target_ids == ("x",)
    assert locked.operation_id == previous.operation_id
    assert locked.provenance is TargetSelectionProvenance.LOCKED


def test_delayed_inherited_target_continuation_is_not_requeried() -> None:
    context, systems = make_context(), BattleSystems()
    apply_capture(systems, context, owner="x", source="b")
    previous = TargetSelectionResult(
        operation_id=context.id_allocator.allocate_target_operation_id(),
        target_ids=("x",),
        provenance=TargetSelectionProvenance.FRESH_SELECTED,
    )

    inherited = TargetOperationProducer.continue_from(
        previous,
        TargetQueryMode.INHERIT_RESOLVED,
    )

    assert inherited.target_ids == ("x",)
    assert inherited.operation_id == previous.operation_id
    assert inherited.provenance is TargetSelectionProvenance.INHERITED


def test_equipment_attribute_is_removed_from_real_attribute_gather_and_resumes() -> None:
    context, systems = make_context(), BattleSystems()
    provider, ref = register_equipment_attribute(systems, owner="a", amount=50)
    base = context.get_unit("a").attack
    assert systems.attribute_system.get_attack(context, context.get_unit("a")) == base + 50

    apply_capture(
        systems,
        context,
        owner="a",
        lifetime=StateLifetimeSpec.holder_action_window(1),
    )

    decision = systems.equipment_effectiveness_policy.evaluate_contribution(
        context, ref
    )
    assert decision.status is EquipmentEffectivenessStatus.SUPPRESSED
    assert any(
        cause.rule_id == CAPTURE_EQUIPMENT_ATTRIBUTE_RULE_ID
        for cause in decision.suppression_causes
    )
    assert systems.attribute_system.get_attack(context, context.get_unit("a")) == base
    assert systems.equipment_contribution_registry.resolve_provider(
        context, provider
    ) is not None

    expire_holder_action_window(systems, context, "a")

    assert systems.attribute_system.get_attack(context, context.get_unit("a")) == base + 50


@pytest.mark.parametrize(
    "kind",
    [
        EquipmentContributionKind.DAMAGE_MODIFIER,
        EquipmentContributionKind.RECOVERY_MODIFIER,
        EquipmentContributionKind.TRIGGER,
        EquipmentContributionKind.SCHEDULED_TRIGGER,
        EquipmentContributionKind.LIVE_EFFECT,
    ],
)
def test_unverified_equipment_categories_remain_bounded(kind) -> None:
    context, systems = make_context(), BattleSystems()
    provider = EquipmentProviderRef("a", f"equipment:{kind.value}")
    systems.equipment_contribution_registry.register_provider(provider)
    ref = EquipmentContributionRef(provider, f"contribution:{kind.value}", kind)
    systems.equipment_contribution_registry.register_contribution(ref)
    apply_capture(systems, context, owner="a")

    decision = systems.equipment_effectiveness_policy.evaluate_contribution(
        context,
        ref,
    )

    assert decision.status is EquipmentEffectivenessStatus.UNSUPPORTED_BOUNDARY


def test_capture_and_sabotage_equipment_causes_do_not_restore_early() -> None:
    context, systems = make_context(), BattleSystems()
    _, ref = register_equipment_attribute(systems, owner="a", amount=50)
    apply_state(
        systems,
        context,
        OfficialStateId.EQUIPMENT_DISABLE.value,
        owner="a",
    )
    apply_capture(
        systems,
        context,
        owner="a",
        lifetime=StateLifetimeSpec.holder_action_window(1),
    )

    during = systems.equipment_effectiveness_policy.evaluate_contribution(
        context, ref
    )
    assert during.status is EquipmentEffectivenessStatus.SUPPRESSED
    assert len(during.suppression_causes) >= 2

    expire_holder_action_window(systems, context, "a")

    after = systems.equipment_effectiveness_policy.evaluate_contribution(
        context, ref
    )
    assert after.status is EquipmentEffectivenessStatus.SUPPRESSED
    assert all(
        cause.rule_id != CAPTURE_EQUIPMENT_ATTRIBUTE_RULE_ID
        for cause in after.suppression_causes
    )


def test_capture_adapters_publish_no_direct_capture_events() -> None:
    source = inspect.getsource(capture_module)
    assert "event_bus.publish" not in source
    assert "random." not in source
    assert ".chance(" not in source
    assert ".choice(" not in source
    assert ".sample(" not in source


def test_capture_is_not_a_god_object_or_old_state_alias() -> None:
    source = inspect.getsource(capture_module)
    assert "class CaptureRuntime" not in source
    assert "class CaptureManager" not in source
    assert "class CaptureEngine" not in source
    assert "Capture = STUN" not in source
    assert "Capture = WEAKNESS" not in source
    assert "runtime.enabled =" not in source
    assert "unregister" not in source


def test_capture_bounded_target_modes_are_not_fresh_queries() -> None:
    source = inspect.getsource(capture_module)
    assert "TargetQueryMode" not in source
    assert "LOCK_RESOLVED" not in source
    assert "INHERIT_RESOLVED" not in source
