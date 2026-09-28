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
    SkillRuntime,
    SkillTargetMode,
    SkillType,
    StateApplicationResultStatus,
    StateCandidate,
    StateLifetimeSpec,
    TauntStateParams,
    UnitRuntime,
    register_official_state_definitions,
)
from sgs_v2.battle_core.dependency_evaluation import StateNode
from sgs_v2.battle_core.damage_system import DamageRequest
from sgs_v2.battle_core.enums import DamageSourceType, DamageType
from sgs_v2.battle_core import insight_integration as insight_module
from sgs_v2.battle_core.insight_integration import (
    INSIGHT_EXPLICIT_NON_PROTECTED_STATE_IDS,
    INSIGHT_PROTECTED_STATE_IDS,
)
from sgs_v2.battle_core.recovery_system import (
    RecoveryPreventedResult,
    RecoveryRequest,
    RecoveryResolvedResult,
)
from sgs_v2.battle_core.skill_runtime import SkillSlot
from sgs_v2.battle_core.stage11_state_params import (
    DisarmStateParams,
    Stage11TimedFlagParams,
    StunStateParams,
)
from sgs_v2.battle_core.state_effectiveness import (
    LocalRuleCauseRef,
    StateEffectivenessContribution,
    StateEffectivenessStatus,
    SuppressionCause,
)


PROTECTED_IDS = (
    OfficialStateId.SILENCE.value,
    OfficialStateId.DISARM.value,
    OfficialStateId.CONFUSION.value,
    OfficialStateId.WEAKNESS.value,
    OfficialStateId.HEALING_BAN.value,
    OfficialStateId.TAUNT.value,
    OfficialStateId.PROVOKE.value,
    OfficialStateId.EQUIPMENT_DISABLE.value,
    OfficialStateId.STUN.value,
)

NON_PROTECTED_IDS = (
    OfficialStateId.FALSE_REPORT.value,
    OfficialStateId.INTIMIDATION.value,
    OfficialStateId.CAPTURE.value,
)


def make_context(seed: int = 690089) -> BattleContext:
    context = BattleContext(
        battle_id=f"stage12-insight-{seed}",
        units={
            "a0": UnitRuntime(
                "a0", "A0", "A", 1000, 1000, 100, 100, 100,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "a1": UnitRuntime(
                "a1", "A1", "A", 1000, 1000, 100, 100, 95,
                lineup_position=LineupPosition.DEPUTY_1,
            ),
            "b0": UnitRuntime(
                "b0", "B0", "B", 1000, 1000, 100, 100, 90,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "b1": UnitRuntime(
                "b1", "B1", "B", 1000, 1000, 100, 100, 85,
                lineup_position=LineupPosition.DEPUTY_1,
            ),
        },
        event_bus=EventBus(),
        random=RandomSystem(seed),
    )
    register_official_state_definitions(context.states)
    context.current_round = 1
    context.current_phase = BattlePhase.ACTION_ORDER.value
    return context


def register_intimidation_provider(context: BattleContext) -> None:
    context.skill_runtimes.register(
        SkillRuntime(
            definition=SkillDefinition(
                skill_id="insight-negative-intimidation-provider",
                name="insight-negative-intimidation-provider",
                activation_rate=1.0,
                target_mode=SkillTargetMode.SINGLE_RANDOM_ENEMY,
                effect_specs=(DamageSkillEffectSpec(DamageType.WEAPON),),
                skill_type=SkillType.ACTIVE,
                preparation_mode=PreparationMode.NONE,
            ),
            owner_id="a0",
            skill_slot=SkillSlot.INHERENT,
            enabled=True,
        )
    )


def runtime_params(state_id: str):
    if state_id == OfficialStateId.DISARM.value:
        return DisarmStateParams(block_probability=1.0)
    if state_id in {
        OfficialStateId.WEAKNESS.value,
        OfficialStateId.HEALING_BAN.value,
    }:
        return Stage11TimedFlagParams()
    if state_id == OfficialStateId.STUN.value:
        return StunStateParams(remaining_blocks=2)
    if state_id == OfficialStateId.TAUNT.value:
        return TauntStateParams(taunt_target_id="b0")
    return EmptyStateRuntimeParams()


def candidate(
    state_id: str,
    *,
    owner_id: str = "a0",
    lifetime_spec: StateLifetimeSpec | None = None,
):
    return StateCandidate(
        state_id=state_id,
        owner_id=owner_id,
        source_id="b0",
        source_skill_id=f"source-{state_id}",
        source_skill_slot=SkillSlot.LEARNED_1,
        runtime_params_candidate=runtime_params(state_id),
        lifetime_spec=lifetime_spec,
        application_provenance="stage12-690089-contract-test",
    )


def apply(systems: BattleSystems, context: BattleContext, state_id: str, **kwargs):
    return systems.state_application_coordinator.apply_candidate(
        context,
        candidate(state_id, **kwargs),
    )


def event_count(context: BattleContext, event_type: EventType) -> int:
    return sum(1 for event in context.event_bus.history if event.event_type is event_type)


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


def test_protected_set_is_exact_and_negative_exclusions_are_explicit() -> None:
    assert INSIGHT_PROTECTED_STATE_IDS == frozenset(PROTECTED_IDS)
    assert INSIGHT_EXPLICIT_NON_PROTECTED_STATE_IDS == frozenset(NON_PROTECTED_IDS)
    assert INSIGHT_PROTECTED_STATE_IDS.isdisjoint(
        INSIGHT_EXPLICIT_NON_PROTECTED_STATE_IDS
    )


def test_insight_application_and_effective_truth_consume_zero_rng() -> None:
    context = make_context(seed=11)
    systems = BattleSystems()
    control = RandomSystem(11)

    result = apply(systems, context, OfficialStateId.INSIGHT.value)

    assert result.status is StateApplicationResultStatus.APPLIED
    assert result.instance is not None
    assert systems.state_effectiveness_policy.has_effective(
        context, "a0", OfficialStateId.INSIGHT.value
    )
    assert context.random.random() == control.random()


@pytest.mark.parametrize("protected_id", PROTECTED_IDS)
def test_incoming_protected_candidate_rejected_before_mutation(
    protected_id: str,
) -> None:
    context = make_context()
    systems = BattleSystems()
    apply(systems, context, OfficialStateId.INSIGHT.value)
    generation_before = context.generation_allocator._generation_seq

    result = apply(systems, context, protected_id)

    assert result.status is StateApplicationResultStatus.REJECTED_ADMISSION
    assert not context.states.has(owner_id="a0", state_id=protected_id)
    assert context.generation_allocator._generation_seq == generation_before
    assert event_count(context, EventType.STATE_APPLIED) == 1
    assert event_count(context, EventType.STATE_REMOVED) == 0


@pytest.mark.parametrize("state_id", NON_PROTECTED_IDS)
def test_negative_exclusions_are_not_rejected_by_ordinary_insight(
    state_id: str,
) -> None:
    context = make_context()
    systems = BattleSystems()
    apply(systems, context, OfficialStateId.INSIGHT.value)
    if state_id == OfficialStateId.INTIMIDATION.value:
        register_intimidation_provider(context)

    result = apply(systems, context, state_id)

    assert result.status is StateApplicationResultStatus.APPLIED
    assert context.states.has(owner_id="a0", state_id=state_id)
    instance = result.instance
    assert instance is not None
    assert systems.state_effectiveness_policy.evaluate_state(
        context, instance
    ).effective


def test_pd_ins_001_source_rng_consumes_before_rejection() -> None:
    context = make_context(seed=17)
    systems = BattleSystems()
    apply(systems, context, OfficialStateId.INSIGHT.value)
    control = RandomSystem(17)

    assert context.random.chance(0.75) == control.chance(0.75)
    result = apply(systems, context, OfficialStateId.CONFUSION.value)

    assert result.status is StateApplicationResultStatus.REJECTED_ADMISSION
    assert context.random.random() == control.random()


def test_pd_ins_001_deterministic_source_gets_no_synthetic_rng() -> None:
    context = make_context(seed=19)
    systems = BattleSystems()
    apply(systems, context, OfficialStateId.INSIGHT.value)
    control = RandomSystem(19)

    result = apply(systems, context, OfficialStateId.STUN.value)

    assert result.status is StateApplicationResultStatus.REJECTED_ADMISSION
    assert context.random.random() == control.random()


def test_pd_ins_002_present_insight_rejects_reapplication_without_refresh() -> None:
    context = make_context()
    systems = BattleSystems()
    first = apply(
        systems,
        context,
        OfficialStateId.INSIGHT.value,
        lifetime_spec=StateLifetimeSpec.round_calendar(expires_round=3),
    )
    assert first.instance is not None
    old = first.instance
    old_generation = old.current_generation_id
    old_lifetime = old.lifetime_spec
    generation_before = context.generation_allocator._generation_seq

    second = apply(
        systems,
        context,
        OfficialStateId.INSIGHT.value,
        lifetime_spec=StateLifetimeSpec.round_calendar(expires_round=9),
    )

    assert second.status is StateApplicationResultStatus.REJECTED_CONFLICT
    current = context.states.get(old.instance_id)
    assert current.current_generation_id == old_generation
    assert current.lifetime_spec == old_lifetime
    assert context.generation_allocator._generation_seq == generation_before
    assert event_count(context, EventType.STATE_REFRESHED) == 0


@pytest.mark.parametrize("protected_id", PROTECTED_IDS)
def test_resident_protected_state_is_suppressed_without_removal(
    protected_id: str,
) -> None:
    context = make_context()
    systems = BattleSystems()
    protected = apply(systems, context, protected_id).instance
    assert protected is not None
    generation = protected.current_generation_id

    apply(systems, context, OfficialStateId.INSIGHT.value)

    current = context.states.get(protected.instance_id)
    decision = systems.state_effectiveness_policy.evaluate_state(context, current)
    assert decision.status is StateEffectivenessStatus.SUPPRESSED
    assert current.current_generation_id == generation
    assert event_count(context, EventType.STATE_REMOVED) == 0


def test_suppression_resume_preserves_instance_generation_lifetime_and_events() -> None:
    context = make_context()
    systems = BattleSystems()
    protected = apply(
        systems,
        context,
        OfficialStateId.CONFUSION.value,
        lifetime_spec=StateLifetimeSpec.round_calendar(expires_round=4),
    ).instance
    insight = apply(
        systems,
        context,
        OfficialStateId.INSIGHT.value,
        lifetime_spec=StateLifetimeSpec.round_calendar(expires_round=2),
    ).instance
    assert protected is not None and insight is not None
    protected_generation = protected.current_generation_id
    protected_lifetime = protected.lifetime_spec

    assert event_count(context, EventType.STATE_SUPPRESSED) == 1
    for _ in range(5):
        assert systems.state_effectiveness_policy.evaluate_state(
            context, protected
        ).status is StateEffectivenessStatus.SUPPRESSED
    assert event_count(context, EventType.STATE_SUPPRESSED) == 1

    systems.state_removal_coordinator.remove(
        context,
        operation=RemovalOperation.NATURAL_EXPIRY,
        instance_id=insight.instance_id,
    )

    current = context.states.get(protected.instance_id)
    assert systems.state_effectiveness_policy.evaluate_state(
        context, current
    ).effective
    assert current.current_generation_id == protected_generation
    assert current.lifetime_spec == protected_lifetime
    assert event_count(context, EventType.STATE_RESUMED) == 1
    assert event_count(context, EventType.STATE_REFRESHED) == 0


def test_protected_state_expiring_while_suppressed_never_resumes() -> None:
    context = make_context()
    systems = BattleSystems()
    protected = apply(
        systems,
        context,
        OfficialStateId.CONFUSION.value,
        lifetime_spec=StateLifetimeSpec.round_calendar(expires_round=1),
    ).instance
    insight = apply(
        systems,
        context,
        OfficialStateId.INSIGHT.value,
        lifetime_spec=StateLifetimeSpec.round_calendar(expires_round=2),
    ).instance
    assert protected is not None and insight is not None
    resume_before = event_count(context, EventType.STATE_RESUMED)

    settle_due(
        systems,
        context,
        round_no=1,
        phase=BattlePhase.ROUND_END.value,
    )
    assert not context.states.has_instance(protected.instance_id)

    settle_due(
        systems,
        context,
        round_no=2,
        phase=BattlePhase.ROUND_END.value,
    )
    assert event_count(context, EventType.STATE_RESUMED) == resume_before


def test_same_envelope_insight_and_protected_expiry_has_no_transient_resume() -> None:
    context = make_context()
    systems = BattleSystems()
    protected = apply(
        systems,
        context,
        OfficialStateId.CONFUSION.value,
        lifetime_spec=StateLifetimeSpec.round_calendar(expires_round=2),
    ).instance
    insight = apply(
        systems,
        context,
        OfficialStateId.INSIGHT.value,
        lifetime_spec=StateLifetimeSpec.round_calendar(expires_round=2),
    ).instance
    assert protected is not None and insight is not None
    resume_before = event_count(context, EventType.STATE_RESUMED)

    removed = settle_due(
        systems,
        context,
        round_no=2,
        phase=BattlePhase.ROUND_END.value,
    )

    assert {item.instance_id for item in removed} == {
        protected.instance_id,
        insight.instance_id,
    }
    assert event_count(context, EventType.STATE_RESUMED) == resume_before


def test_stage9_confusion_authority_migrates_to_effective_truth() -> None:
    context = make_context(seed=1)
    systems = BattleSystems()
    confusion = apply(systems, context, OfficialStateId.CONFUSION.value).instance
    insight = apply(systems, context, OfficialStateId.INSIGHT.value).instance
    assert confusion is not None and insight is not None

    assert systems.stage9_state_runtime.get_operational_confusion(
        context, "a0"
    ) is None
    first = systems.target_resolution_system.resolve(
        context,
        "a0",
        normal_attack_id=context.id_allocator.allocate_normal_attack_id(),
    )
    assert first is not None
    assert first.intended_attack_target in {"b0", "b1"}

    systems.state_removal_coordinator.remove(
        context,
        operation=RemovalOperation.NATURAL_EXPIRY,
        instance_id=insight.instance_id,
    )
    assert systems.stage9_state_runtime.get_operational_confusion(
        context, "a0"
    ) == confusion


def test_confusion_and_taunt_are_both_suppressed_in_stage9_arbitration() -> None:
    context = make_context()
    systems = BattleSystems()
    confusion = apply(systems, context, OfficialStateId.CONFUSION.value).instance
    taunt = apply(systems, context, OfficialStateId.TAUNT.value).instance
    apply(systems, context, OfficialStateId.INSIGHT.value)
    assert confusion is not None and taunt is not None

    assert systems.stage9_state_runtime.get_operational_confusion(
        context, "a0"
    ) is None
    assert systems.stage9_state_runtime.get_operational_taunt(
        context, "a0"
    ) is None
    assert context.states.has_instance(confusion.instance_id)
    assert context.states.has_instance(taunt.instance_id)


def test_stage11_disarm_stun_weakness_healing_block_consume_effective_truth() -> None:
    context = make_context()
    systems = BattleSystems()
    disarm = apply(systems, context, OfficialStateId.DISARM.value).instance
    stun = apply(systems, context, OfficialStateId.STUN.value).instance
    weakness = apply(systems, context, OfficialStateId.WEAKNESS.value).instance
    healing = apply(systems, context, OfficialStateId.HEALING_BAN.value).instance
    assert all(item is not None for item in (disarm, stun, weakness, healing))

    apply(systems, context, OfficialStateId.INSIGHT.value)

    assert systems.stage11_state_runtime.disarm_blocks(context, "a0") is False
    assert systems.stage11_state_runtime.weakness_active(context, "a0") is False
    assert systems.stage11_state_runtime.healing_block_active(context, "a0") is False
    before = context.states.get(stun.instance_id).runtime_params.remaining_blocks
    assert systems.stage11_state_runtime.consume_stun_natural_action(
        context, "a0"
    ) is False
    after = context.states.get(stun.instance_id).runtime_params.remaining_blocks
    assert after == before


def test_dependency_binding_is_explicit_and_removed_with_insight() -> None:
    context = make_context()
    systems = BattleSystems()
    protected = apply(systems, context, OfficialStateId.CONFUSION.value).instance
    insight = apply(systems, context, OfficialStateId.INSIGHT.value).instance
    assert protected is not None and insight is not None

    assert systems.dependency_evaluation_support.prerequisites(
        StateNode(protected.instance_id)
    ) == (StateNode(insight.instance_id),)

    systems.state_removal_coordinator.remove(
        context,
        operation=RemovalOperation.NATURAL_EXPIRY,
        instance_id=insight.instance_id,
    )
    assert systems.dependency_evaluation_support.prerequisites(
        StateNode(protected.instance_id)
    ) == ()



def _synthetic_insight_suppressor(_context, instance, _session):
    if instance.state_id != OfficialStateId.INSIGHT.value:
        return StateEffectivenessContribution()
    return StateEffectivenessContribution(
        suppression_causes=(
            SuppressionCause(
                "TEST_SUPPRESS_INSIGHT",
                LocalRuleCauseRef("synthetic-insight-suppressor"),
            ),
        )
    )


def test_pd_ins_002_suppressed_present_insight_still_rejects_reapplication() -> None:
    context = make_context(seed=23)
    systems = BattleSystems()
    systems.state_effectiveness_policy.register_rule_adapter(
        _synthetic_insight_suppressor
    )
    first = apply(systems, context, OfficialStateId.INSIGHT.value)
    assert first.instance is not None
    assert systems.state_effectiveness_policy.evaluate_state(
        context, first.instance
    ).status is StateEffectivenessStatus.SUPPRESSED
    generation_before = context.generation_allocator._generation_seq
    control = RandomSystem(23)

    second = apply(systems, context, OfficialStateId.INSIGHT.value)

    assert second.status is StateApplicationResultStatus.REJECTED_CONFLICT
    assert context.generation_allocator._generation_seq == generation_before
    assert context.random.random() == control.random()
    assert context.states.get(first.instance.instance_id).current_generation_id == (
        first.instance.current_generation_id
    )


def test_suppressed_insight_does_not_protect_incoming_control() -> None:
    context = make_context()
    systems = BattleSystems()
    systems.state_effectiveness_policy.register_rule_adapter(
        _synthetic_insight_suppressor
    )
    insight = apply(systems, context, OfficialStateId.INSIGHT.value).instance
    assert insight is not None
    assert systems.state_effectiveness_policy.evaluate_state(
        context, insight
    ).status is StateEffectivenessStatus.SUPPRESSED

    result = apply(systems, context, OfficialStateId.CONFUSION.value)

    assert result.status is StateApplicationResultStatus.APPLIED
    assert result.instance is not None
    assert systems.state_effectiveness_policy.evaluate_state(
        context, result.instance
    ).effective
    assert systems.dependency_evaluation_support.prerequisites(
        StateNode(result.instance.instance_id)
    ) == (StateNode(insight.instance_id),)


def test_insight_rejects_same_protected_state_before_conflict_refresh() -> None:
    context = make_context()
    systems = BattleSystems()
    original = apply(
        systems,
        context,
        OfficialStateId.CONFUSION.value,
        lifetime_spec=StateLifetimeSpec.round_calendar(expires_round=4),
    ).instance
    assert original is not None
    original_generation = original.current_generation_id
    original_lifetime = original.lifetime_spec
    apply(systems, context, OfficialStateId.INSIGHT.value)
    generation_before = context.generation_allocator._generation_seq

    result = apply(
        systems,
        context,
        OfficialStateId.CONFUSION.value,
        lifetime_spec=StateLifetimeSpec.round_calendar(expires_round=9),
    )

    assert result.status is StateApplicationResultStatus.REJECTED_ADMISSION
    current = context.states.get(original.instance_id)
    assert current.current_generation_id == original_generation
    assert current.lifetime_spec == original_lifetime
    assert context.generation_allocator._generation_seq == generation_before
    assert event_count(context, EventType.STATE_REFRESHED) == 0


def test_multiple_suppression_causes_compose_and_insight_removal_does_not_false_resume() -> None:
    context = make_context()
    systems = BattleSystems()
    protected = apply(
        systems, context, OfficialStateId.CONFUSION.value
    ).instance
    assert protected is not None

    def local_control_suppressor(_context, instance, _session):
        if instance.instance_id != protected.instance_id:
            return StateEffectivenessContribution()
        return StateEffectivenessContribution(
            suppression_causes=(
                SuppressionCause(
                    "TEST_SECONDARY_CONTROL_SUPPRESSOR",
                    LocalRuleCauseRef("synthetic-control-suppressor"),
                ),
            )
        )

    systems.state_effectiveness_policy.register_rule_adapter(
        local_control_suppressor
    )
    assert systems.state_effectiveness_policy.evaluate_state(
        context, protected
    ).status is StateEffectivenessStatus.SUPPRESSED
    resume_before = event_count(context, EventType.STATE_RESUMED)

    insight = apply(
        systems, context, OfficialStateId.INSIGHT.value
    ).instance
    assert insight is not None
    decision = systems.state_effectiveness_policy.evaluate_state(
        context, protected
    )
    assert decision.status is StateEffectivenessStatus.SUPPRESSED
    assert {cause.rule_id for cause in decision.suppression_causes} == {
        "TEST_SECONDARY_CONTROL_SUPPRESSOR",
        "690089_INSIGHT_RESIDENT_CONTROL_SUPPRESSION",
    }

    systems.state_removal_coordinator.remove(
        context,
        operation=RemovalOperation.NATURAL_EXPIRY,
        instance_id=insight.instance_id,
    )
    after = systems.state_effectiveness_policy.evaluate_state(
        context, protected
    )
    assert after.status is StateEffectivenessStatus.SUPPRESSED
    assert {cause.rule_id for cause in after.suppression_causes} == {
        "TEST_SECONDARY_CONTROL_SUPPRESSOR",
    }
    assert event_count(context, EventType.STATE_RESUMED) == resume_before


def test_weakness_damage_pipeline_reads_effective_truth_under_insight() -> None:
    context = make_context(seed=29)
    systems = BattleSystems()
    weakness = apply(
        systems, context, OfficialStateId.WEAKNESS.value
    ).instance
    insight = apply(
        systems, context, OfficialStateId.INSIGHT.value
    ).instance
    assert weakness is not None and insight is not None

    request = DamageRequest(
        source_id="a0",
        target_id="b0",
        damage_type=DamageType.WEAPON,
        source_type=DamageSourceType.SKILL,
        coefficient=1.0,
    )
    while_suppressed = systems.damage_system.calculate(context, request)
    assert while_suppressed.final_damage > 0

    systems.state_removal_coordinator.remove(
        context,
        operation=RemovalOperation.NATURAL_EXPIRY,
        instance_id=insight.instance_id,
    )
    resumed = systems.damage_system.calculate(context, request)
    assert resumed.final_damage == 0


def test_healing_ban_recovery_pipeline_reads_effective_truth_under_insight() -> None:
    context = make_context()
    systems = BattleSystems()
    context.get_unit("a0").troops = 500
    healing_ban = apply(
        systems, context, OfficialStateId.HEALING_BAN.value
    ).instance
    insight = apply(
        systems, context, OfficialStateId.INSIGHT.value
    ).instance
    assert healing_ban is not None and insight is not None

    allowed = systems.recovery_system.resolve(
        context,
        RecoveryRequest(source_id="a1", target_id="a0", amount=100),
    )
    assert isinstance(allowed, RecoveryResolvedResult)
    assert allowed.actual_recovery == 100

    systems.state_removal_coordinator.remove(
        context,
        operation=RemovalOperation.NATURAL_EXPIRY,
        instance_id=insight.instance_id,
    )
    blocked = systems.recovery_system.resolve(
        context,
        RecoveryRequest(source_id="a1", target_id="a0", amount=100),
    )
    assert isinstance(blocked, RecoveryPreventedResult)
    assert blocked.reason_state_id == OfficialStateId.HEALING_BAN.value


def test_insight_static_architecture_guards() -> None:
    source = inspect.getsource(insight_module)
    battle_systems_source = inspect.getsource(BattleSystems.__post_init__)

    assert "event_bus.publish" not in source
    assert "StateLifecycleSystem.remove" not in source
    assert ".refresh(" not in source
    assert "random." not in source
    assert "Stage12InsightRuntime" not in source
    assert "all_negative_states" not in source
    assert "all_control_states" not in source
    assert "all_debuffs" not in source
    assert battle_systems_source.count("StateEffectivenessPolicy(") == 1
