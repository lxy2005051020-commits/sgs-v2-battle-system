from __future__ import annotations

import inspect

import pytest

from sgs_v2.battle_core import (
    BattleContext,
    BattlePhase,
    BattleSystems,
    EmptyStateRuntimeParams,
    EquipmentAttributeContribution,
    EquipmentContributionDependency,
    EquipmentContributionKind,
    EquipmentContributionRef,
    EquipmentEffectivenessStatus,
    EquipmentProviderRef,
    EventBus,
    LineupPosition,
    OfficialStateId,
    ProviderDependency,
    ProviderNode,
    ProviderValidityStatus,
    RandomSystem,
    RemovalOperation,
    StateApplicationResultStatus,
    StateCandidate,
    StateEffectivenessStatus,
    StateLifetimeSpec,
    StateNode,
    StateRemovalResultStatus,
    UnitRuntime,
    register_official_state_definitions,
)
from sgs_v2.battle_core import sabotage_integration as sabotage_module
from sgs_v2.battle_core.damage_modifier_system import DamageModifierSystem
from sgs_v2.battle_core.damage_modifiers import (
    DamageModifierContribution,
    DamageModifierKind,
    DamageModifierOperation,
    DamageModifierPhase,
)
from sgs_v2.battle_core.damage_rule_models import RuleContributionSource
from sgs_v2.battle_core.damage_rule_provider import DamageRuleCollection
from sgs_v2.battle_core.damage_system import DamageRequest
from sgs_v2.battle_core.enums import DamageSourceType, DamageType
from sgs_v2.battle_core.equipment_effectiveness import (
    EquipmentTriggerGateStatus,
)
from sgs_v2.battle_core.execution_right_runtime import (
    ExecutionRightEvaluationStatus,
    ExecutionRightMode,
    ExecutionRightRequest,
    ExecutionRightSpec,
)
from sgs_v2.battle_core.false_report_integration import (
    FALSE_REPORT_EQUIPMENT_SUPPRESSION_RULE_ID,
)
from sgs_v2.battle_core.recovery_system import (
    RecoveryModifierContribution,
    RecoveryModifierPolicy,
    RecoveryRequest,
)
from sgs_v2.battle_core.sabotage_integration import (
    SABOTAGE_EQUAL_REAPPLICATION_RULE_ID,
    SABOTAGE_GANGYI_ADMISSION_RULE_ID,
    SABOTAGE_PROVIDER_SUPPRESSION_RULE_ID,
    SABOTAGE_STRENGTH_BOUNDARY_RULE_ID,
)
from sgs_v2.battle_core.stage9_integerization import ExactRatio


class CountingRandomSystem(RandomSystem):
    def __init__(self, seed: int = 690109) -> None:
        super().__init__(seed)
        self.chance_calls = 0
        self.choice_calls = 0
        self.sample_calls = 0

    def chance(self, probability: float) -> bool:
        self.chance_calls += 1
        return super().chance(probability)

    def choice(self, values):  # type: ignore[no-untyped-def]
        self.choice_calls += 1
        return super().choice(values)

    def sample(self, values, k):  # type: ignore[no-untyped-def]
        self.sample_calls += 1
        return super().sample(values, k)


def make_context(rng: RandomSystem | None = None) -> BattleContext:
    context = BattleContext(
        battle_id="stage12-690109",
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
        random=rng or RandomSystem(690109),
    )
    register_official_state_definitions(context.states)
    context.current_round = 1
    context.current_phase = BattlePhase.UNIT_ACTION.value
    return context


def candidate(
    state_id: str = OfficialStateId.EQUIPMENT_DISABLE.value,
    *,
    owner: str = "a",
    source: str = "b",
    lifetime: StateLifetimeSpec | None = None,
    strength: float | None = None,
    dependencies: tuple[ProviderDependency, ...] = (),
) -> StateCandidate:
    return StateCandidate(
        state_id=state_id,
        owner_id=owner,
        source_id=source,
        source_skill_id=f"source-{state_id}",
        runtime_params_candidate=EmptyStateRuntimeParams(),
        lifetime_spec=lifetime,
        strength=strength,
        provider_dependencies=dependencies,
        application_provenance="stage12-690109-runtime-test",
    )


def apply_state(
    systems: BattleSystems,
    context: BattleContext,
    state_id: str = OfficialStateId.EQUIPMENT_DISABLE.value,
    **kwargs,
):
    return systems.state_application_coordinator.apply_candidate(
        context,
        candidate(state_id, **kwargs),
    )


def apply_sabotage(systems: BattleSystems, context: BattleContext, **kwargs):
    return apply_state(
        systems,
        context,
        OfficialStateId.EQUIPMENT_DISABLE.value,
        **kwargs,
    )


def remove_state(
    systems: BattleSystems,
    context: BattleContext,
    instance_id: str,
    operation: RemovalOperation = RemovalOperation.ORDINARY_CLEANSE,
):
    return systems.state_removal_coordinator.remove(
        context,
        operation=operation,
        instance_id=instance_id,
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


def register_equipment(
    systems: BattleSystems,
    *,
    owner: str = "a",
    provider_key: str = "weapon:test",
    kind: EquipmentContributionKind = EquipmentContributionKind.LIVE_EFFECT,
    contribution_key: str | None = None,
    payload: object | None = None,
    enabled: bool = True,
):
    provider_ref = EquipmentProviderRef(owner, provider_key)
    if systems.equipment_contribution_registry.resolve_provider(None, provider_ref) is None:
        systems.equipment_contribution_registry.register_provider(
            provider_ref,
            enabled=enabled,
            payload=payload,
        )
    contribution_ref = EquipmentContributionRef(
        provider_ref,
        contribution_key or f"{provider_key}:{kind.value}",
        kind,
    )
    systems.equipment_contribution_registry.register_contribution(
        contribution_ref,
    )
    return provider_ref, contribution_ref


def assert_effective(systems: BattleSystems, context: BattleContext, ref) -> None:
    assert systems.equipment_effectiveness_policy.evaluate_contribution(
        context, ref
    ).status is EquipmentEffectivenessStatus.EFFECTIVE


def assert_suppressed(systems: BattleSystems, context: BattleContext, ref) -> None:
    decision = systems.equipment_effectiveness_policy.evaluate_contribution(
        context, ref
    )
    assert decision.status is EquipmentEffectivenessStatus.SUPPRESSED
    assert any(
        cause.rule_id == SABOTAGE_PROVIDER_SUPPRESSION_RULE_ID
        for cause in decision.suppression_causes
    )


def test_application_effective_truth_and_zero_policy_rng() -> None:
    rng = CountingRandomSystem()
    context, systems = make_context(rng), BattleSystems()
    _, ref = register_equipment(systems)

    baseline = RandomSystem(690109)
    result = apply_sabotage(systems, context)

    assert result.status is StateApplicationResultStatus.APPLIED
    assert result.instance is not None
    assert systems.state_effectiveness_policy.evaluate_state(
        context, result.instance
    ).effective
    assert_suppressed(systems, context, ref)
    assert (rng.chance_calls, rng.choice_calls, rng.sample_calls) == (0, 0, 0)
    assert rng.random() == baseline.random()


@pytest.mark.parametrize(
    "provider_key",
    [
        "weapon:slot",
        "armor:slot",
        "mount:slot",
        "treasure:slot",
    ],
)
def test_all_four_equipment_slots_are_in_sabotage_scope(provider_key: str) -> None:
    context, systems = make_context(), BattleSystems()
    provider_ref, ref = register_equipment(
        systems,
        provider_key=provider_key,
        kind=EquipmentContributionKind.ATTRIBUTE,
    )
    before_record = systems.equipment_contribution_registry.resolve_provider(
        context, provider_ref
    )

    apply_sabotage(systems, context)

    during_record = systems.equipment_contribution_registry.resolve_provider(
        context, provider_ref
    )
    assert before_record is during_record
    assert before_record is not None and before_record.enabled is True
    assert_suppressed(systems, context, ref)


@pytest.mark.parametrize("kind", list(EquipmentContributionKind))
def test_every_frozen_contribution_taxonomy_kind_uses_same_provider_gate(
    kind: EquipmentContributionKind,
) -> None:
    context, systems = make_context(), BattleSystems()
    _, ref = register_equipment(
        systems,
        provider_key=f"provider:{kind.value}",
        kind=kind,
    )
    apply_sabotage(systems, context)
    assert_suppressed(systems, context, ref)


def test_equipment_object_identity_and_payload_are_retained_across_restore() -> None:
    context, systems = make_context(), BattleSystems()
    physical_equipment = object()
    provider_ref, ref = register_equipment(
        systems,
        payload=physical_equipment,
        kind=EquipmentContributionKind.ATTRIBUTE,
    )
    before = systems.equipment_contribution_registry.resolve_provider(
        context, provider_ref
    )
    sabotage = apply_sabotage(systems, context).instance
    assert sabotage is not None
    during = systems.equipment_contribution_registry.resolve_provider(
        context, provider_ref
    )

    removed = remove_state(systems, context, sabotage.instance_id)

    after = systems.equipment_contribution_registry.resolve_provider(
        context, provider_ref
    )
    assert removed.status is StateRemovalResultStatus.REMOVED
    assert before is during is after
    assert after is not None and after.payload is physical_equipment
    assert after.enabled is True
    assert_effective(systems, context, ref)


def test_attribute_consumer_suppresses_resumes_and_has_no_drift() -> None:
    context, systems = make_context(), BattleSystems()
    _, ref = register_equipment(
        systems,
        kind=EquipmentContributionKind.ATTRIBUTE,
    )

    def equipment_attributes(_context, unit, attribute):  # type: ignore[no-untyped-def]
        if unit.unit_id != "a" or attribute != "attack":
            return ()
        return (EquipmentAttributeContribution(ref, "attack", 25.0),)

    systems.attribute_system.register_equipment_contribution_provider(
        equipment_attributes
    )

    assert systems.attribute_system.get_attack(context, context.get_unit("a")) == 325.0
    sabotage = apply_sabotage(systems, context).instance
    assert sabotage is not None
    assert systems.attribute_system.get_attack(context, context.get_unit("a")) == 300.0

    insight = apply_state(
        systems, context, OfficialStateId.INSIGHT.value, owner="a", source="b"
    ).instance
    assert insight is not None
    assert systems.state_effectiveness_policy.evaluate_state(
        context, sabotage
    ).status is StateEffectivenessStatus.SUPPRESSED
    assert systems.attribute_system.get_attack(context, context.get_unit("a")) == 325.0

    remove_state(
        systems,
        context,
        insight.instance_id,
        RemovalOperation.NATURAL_EXPIRY,
    )
    assert systems.attribute_system.get_attack(context, context.get_unit("a")) == 300.0

    remove_state(systems, context, sabotage.instance_id)
    assert systems.attribute_system.get_attack(context, context.get_unit("a")) == 325.0
    assert context.get_unit("a").attack == 300


def _damage_rules(ref: EquipmentContributionRef, *, probability: float = 1.0):
    contribution = DamageModifierContribution(
        phase=DamageModifierPhase.OUTGOING,
        kind=DamageModifierKind.OUTGOING_INCREASE,
        operation=DamageModifierOperation.MULTIPLY_FACTOR,
        operand=1.5,
        source=RuleContributionSource(
            owner_id="a",
            applied_by_unit_id="a",
            source_skill_id=None,
            source_state_id=None,
            source_state_instance_id=None,
            origin_key="equipment:test-damage",
        ),
        order_key="equipment:test-damage",
        probability=probability,
        equipment_contribution_ref=ref,
    )
    return DamageRuleCollection(modifier_contributions=(contribution,))


def _damage_request() -> DamageRequest:
    return DamageRequest(
        source_id="a",
        target_id="b",
        damage_type=DamageType.WEAPON,
        source_type=DamageSourceType.NORMAL_ATTACK,
    )


def test_damage_modifier_consumer_is_future_only_and_resolved_fact_stays_fixed() -> None:
    context, systems = make_context(), BattleSystems()
    _, ref = register_equipment(
        systems,
        kind=EquipmentContributionKind.DAMAGE_MODIFIER,
    )
    modifier = DamageModifierSystem(systems.equipment_effectiveness_policy)
    rules = _damage_rules(ref)

    before = modifier.resolve(context, _damage_request(), rules, 100.0)
    sabotage = apply_sabotage(systems, context).instance
    assert sabotage is not None
    during = modifier.resolve(context, _damage_request(), rules, 100.0)
    remove_state(systems, context, sabotage.instance_id)
    after = modifier.resolve(context, _damage_request(), rules, 100.0)

    assert before.output_damage == 150.0
    assert during.output_damage == 100.0
    assert after.output_damage == 150.0
    assert before.output_damage == 150.0


def test_suppressed_damage_modifier_short_circuits_before_modifier_rng() -> None:
    rng = CountingRandomSystem()
    context, systems = make_context(rng), BattleSystems()
    _, ref = register_equipment(
        systems,
        kind=EquipmentContributionKind.DAMAGE_MODIFIER,
    )
    apply_sabotage(systems, context)

    DamageModifierSystem(systems.equipment_effectiveness_policy).resolve(
        context,
        _damage_request(),
        _damage_rules(ref, probability=0.5),
        100.0,
    )

    assert rng.chance_calls == 0


def test_recovery_modifier_consumer_suppresses_and_resumes_without_replay() -> None:
    provider_ref = EquipmentProviderRef("a", "treasure:prayer")
    ref = EquipmentContributionRef(
        provider_ref,
        "treasure:prayer:recovery",
        EquipmentContributionKind.RECOVERY_MODIFIER,
    )

    def modifier_provider(_context, _request):  # type: ignore[no-untyped-def]
        return RecoveryModifierContribution(
            ExactRatio(3, 2),
            equipment_contribution_ref=ref,
        )

    systems = BattleSystems(recovery_modifier_provider=modifier_provider)
    context = make_context()
    systems.equipment_contribution_registry.register_provider(provider_ref)
    systems.equipment_contribution_registry.register_contribution(ref)
    request = RecoveryRequest(
        source_id="a",
        target_id="a",
        amount=100,
        modifier_policy=RecoveryModifierPolicy.APPLY,
    )

    context.get_unit("a").troops = 500
    before = systems.recovery_system.resolve(context, request)
    context.get_unit("a").troops = 500

    sabotage = apply_sabotage(systems, context).instance
    assert sabotage is not None
    during = systems.recovery_system.resolve(context, request)
    context.get_unit("a").troops = 500

    remove_state(systems, context, sabotage.instance_id)
    after = systems.recovery_system.resolve(context, request)

    assert before.modified_recovery == 150
    assert during.modified_recovery == 100
    assert after.modified_recovery == 150
    assert before.modified_recovery == 150


def test_deterministic_trigger_consumer_skips_missed_window_without_replay() -> None:
    context, systems = make_context(), BattleSystems()
    _, ref = register_equipment(
        systems,
        kind=EquipmentContributionKind.TRIGGER,
    )
    dependency = EquipmentContributionDependency(ref, "test-trigger")
    fired: list[str] = []

    if systems.trigger_system.evaluate_equipment_dependency(
        context, dependency
    ).status is EquipmentTriggerGateStatus.ALLOW:
        fired.append("A")

    sabotage = apply_sabotage(systems, context).instance
    assert sabotage is not None
    if systems.trigger_system.evaluate_equipment_dependency(
        context, dependency
    ).status is EquipmentTriggerGateStatus.ALLOW:
        fired.append("B")

    remove_state(systems, context, sabotage.instance_id)
    if systems.trigger_system.evaluate_equipment_dependency(
        context, dependency
    ).status is EquipmentTriggerGateStatus.ALLOW:
        fired.append("C")

    assert fired == ["A", "C"]


def test_scheduled_execution_right_rechecks_at_execution_and_does_not_replay() -> None:
    context, systems = make_context(), BattleSystems()
    _, ref = register_equipment(
        systems,
        kind=EquipmentContributionKind.SCHEDULED_TRIGGER,
    )
    dependency = EquipmentContributionDependency(ref, "scheduled-opportunity")
    spec = ExecutionRightSpec(
        equipment_contribution=ExecutionRightMode.RECHECK_AT_EXECUTION,
    )
    request = ExecutionRightRequest(
        equipment_dependency=dependency,
    )
    executed: list[str] = []

    if systems.execution_right_support.evaluate(context, spec, request).allowed:
        executed.append("window-1")

    sabotage = apply_sabotage(systems, context).instance
    assert sabotage is not None
    denied = systems.execution_right_support.evaluate(context, spec, request)
    assert denied.status is ExecutionRightEvaluationStatus.DENY_EQUIPMENT

    remove_state(systems, context, sabotage.instance_id)
    if systems.execution_right_support.evaluate(context, spec, request).allowed:
        executed.append("window-3")

    assert executed == ["window-1", "window-3"]


def test_local_existing_live_effect_resumes_same_instance_generation() -> None:
    context, systems = make_context(), BattleSystems()
    provider_ref, _ = register_equipment(
        systems,
        kind=EquipmentContributionKind.LIVE_EFFECT,
    )
    effect = apply_state(
        systems,
        context,
        OfficialStateId.PROVOKE.value,
        owner="a",
        source="a",
        dependencies=(ProviderDependency(provider_ref, "explicit-equipment-owner"),),
    ).instance
    assert effect is not None
    generation = effect.current_generation_id

    sabotage = apply_sabotage(systems, context).instance
    assert sabotage is not None
    assert systems.state_effectiveness_policy.evaluate_state(
        context, effect
    ).status is StateEffectivenessStatus.SUPPRESSED

    remove_state(systems, context, sabotage.instance_id)
    resident = context.states.get(effect.instance_id)
    assert resident is effect
    assert resident.current_generation_id == generation
    assert systems.state_effectiveness_policy.evaluate_state(
        context, resident
    ).effective


def test_remote_effect_follows_equipment_owner_not_effect_holder() -> None:
    context, systems = make_context(), BattleSystems()
    provider_ref, _ = register_equipment(
        systems,
        owner="a",
        provider_key="weapon:remote",
        kind=EquipmentContributionKind.LIVE_EFFECT,
    )
    remote = apply_state(
        systems,
        context,
        OfficialStateId.PROVOKE.value,
        owner="b",
        source="a",
        dependencies=(ProviderDependency(provider_ref, "remote-equipment-owner"),),
    ).instance
    assert remote is not None

    holder_sabotage = apply_sabotage(
        systems, context, owner="b", source="c"
    ).instance
    assert holder_sabotage is not None
    assert systems.state_effectiveness_policy.evaluate_state(
        context, remote
    ).effective
    remove_state(systems, context, holder_sabotage.instance_id)

    owner_sabotage = apply_sabotage(
        systems, context, owner="a", source="c"
    ).instance
    assert owner_sabotage is not None
    assert systems.state_effectiveness_policy.evaluate_state(
        context, remote
    ).status is StateEffectivenessStatus.SUPPRESSED

    remove_state(systems, context, owner_sabotage.instance_id)
    assert systems.state_effectiveness_policy.evaluate_state(
        context, remote
    ).effective


def test_attribution_alone_does_not_create_equipment_dependency() -> None:
    context, systems = make_context(), BattleSystems()
    register_equipment(
        systems,
        owner="a",
        provider_key="weapon:attribution-only",
        kind=EquipmentContributionKind.LIVE_EFFECT,
    )
    attributed = apply_state(
        systems,
        context,
        OfficialStateId.PROVOKE.value,
        owner="b",
        source="a",
    ).instance
    assert attributed is not None
    assert systems.dependency_evaluation_support.prerequisites(
        StateNode(attributed.instance_id)
    ) == ()

    apply_sabotage(systems, context, owner="a", source="c")

    assert systems.state_effectiveness_policy.evaluate_state(
        context, attributed
    ).effective


def test_insight_rejects_incoming_sabotage_before_residency_or_equipment_change() -> None:
    context, systems = make_context(), BattleSystems()
    _, ref = register_equipment(
        systems,
        kind=EquipmentContributionKind.ATTRIBUTE,
    )
    insight = apply_state(
        systems, context, OfficialStateId.INSIGHT.value, owner="a"
    )
    assert insight.status is StateApplicationResultStatus.APPLIED

    result = apply_sabotage(systems, context)

    assert result.status is StateApplicationResultStatus.REJECTED_ADMISSION
    assert context.states.find(
        owner_id="a",
        state_id=OfficialStateId.EQUIPMENT_DISABLE.value,
    ) == ()
    assert_effective(systems, context, ref)


def test_later_insight_suppresses_resident_sabotage_then_same_instance_resumes() -> None:
    context, systems = make_context(), BattleSystems()
    provider_ref, ref = register_equipment(
        systems,
        kind=EquipmentContributionKind.ATTRIBUTE,
    )
    sabotage = apply_sabotage(systems, context).instance
    assert sabotage is not None
    generation = sabotage.current_generation_id
    assert_suppressed(systems, context, ref)

    insight = apply_state(
        systems, context, OfficialStateId.INSIGHT.value, owner="a"
    ).instance
    assert insight is not None
    assert systems.state_effectiveness_policy.evaluate_state(
        context, sabotage
    ).status is StateEffectivenessStatus.SUPPRESSED
    assert systems.provider_validity_policy.evaluate_provider(
        context, provider_ref
    ).status is ProviderValidityStatus.VALID
    assert_effective(systems, context, ref)

    remove_state(
        systems,
        context,
        insight.instance_id,
        RemovalOperation.NATURAL_EXPIRY,
    )

    resident = context.states.get(sabotage.instance_id)
    assert resident is sabotage
    assert resident.current_generation_id == generation
    assert systems.state_effectiveness_policy.evaluate_state(
        context, resident
    ).effective
    assert_suppressed(systems, context, ref)


def test_suppressed_sabotage_can_expire_without_later_ghost_resume() -> None:
    context, systems = make_context(), BattleSystems()
    _, ref = register_equipment(
        systems,
        kind=EquipmentContributionKind.ATTRIBUTE,
    )
    sabotage = apply_sabotage(
        systems,
        context,
        lifetime=StateLifetimeSpec.round_calendar(expires_round=2),
    ).instance
    assert sabotage is not None
    insight = apply_state(
        systems,
        context,
        OfficialStateId.INSIGHT.value,
        owner="a",
        lifetime=StateLifetimeSpec.round_calendar(expires_round=3),
    ).instance
    assert insight is not None
    assert_effective(systems, context, ref)

    context.current_round = 2
    context.current_phase = BattlePhase.ROUND_END.value
    removed = settle_due(
        systems,
        context,
        round_no=2,
        phase=BattlePhase.ROUND_END.value,
    )
    assert [item.instance_id for item in removed] == [sabotage.instance_id]
    assert not context.states.has_instance(sabotage.instance_id)

    remove_state(
        systems,
        context,
        insight.instance_id,
        RemovalOperation.NATURAL_EXPIRY,
    )
    assert_effective(systems, context, ref)


def test_same_envelope_insight_and_sabotage_expiry_has_no_transient_resuppression() -> None:
    context, systems = make_context(), BattleSystems()
    provider_ref, ref = register_equipment(
        systems,
        kind=EquipmentContributionKind.ATTRIBUTE,
    )
    lifetime = StateLifetimeSpec.round_calendar(expires_round=2)
    sabotage = apply_sabotage(systems, context, lifetime=lifetime).instance
    assert sabotage is not None
    insight = apply_state(
        systems,
        context,
        OfficialStateId.INSIGHT.value,
        owner="a",
        lifetime=lifetime,
    ).instance
    assert insight is not None
    assert_effective(systems, context, ref)

    transitions = []
    systems.effectiveness_transition_coordinator.register_provider_transition_port(
        lambda _context, transition: transitions.append(transition)
    )
    transitions.clear()

    context.current_round = 2
    context.current_phase = BattlePhase.ROUND_END.value
    removed = settle_due(
        systems,
        context,
        round_no=2,
        phase=BattlePhase.ROUND_END.value,
    )

    assert {item.instance_id for item in removed} == {
        sabotage.instance_id,
        insight.instance_id,
    }
    assert systems.provider_validity_policy.evaluate_provider(
        context, provider_ref
    ).status is ProviderValidityStatus.VALID
    assert_effective(systems, context, ref)
    assert transitions == []


def test_effective_gangyi_rejects_incoming_sabotage() -> None:
    context, systems = make_context(), BattleSystems()
    _, gangyi_ref = register_equipment(
        systems,
        provider_key="刚毅",
        kind=EquipmentContributionKind.LIVE_EFFECT,
        contribution_key="刚毅",
    )
    assert_effective(systems, context, gangyi_ref)

    result = apply_sabotage(systems, context)

    assert result.status is StateApplicationResultStatus.REJECTED_ADMISSION
    assert result.reason_rule_id == SABOTAGE_GANGYI_ADMISSION_RULE_ID
    assert context.states.find(
        owner_id="a",
        state_id=OfficialStateId.EQUIPMENT_DISABLE.value,
    ) == ()


def test_false_report_suppressed_gangyi_does_not_block_sabotage() -> None:
    context, systems = make_context(), BattleSystems()
    register_equipment(
        systems,
        provider_key="刚毅",
        kind=EquipmentContributionKind.LIVE_EFFECT,
        contribution_key="刚毅",
    )
    false_report = apply_state(
        systems,
        context,
        OfficialStateId.FALSE_REPORT.value,
        owner="a",
        source="b",
    )
    assert false_report.status is StateApplicationResultStatus.APPLIED

    result = apply_sabotage(systems, context)

    assert result.status is StateApplicationResultStatus.APPLIED


def test_equal_reapplication_rejected_without_refresh_or_generation_change() -> None:
    context, systems = make_context(), BattleSystems()
    register_equipment(systems)
    first = apply_sabotage(
        systems,
        context,
        lifetime=StateLifetimeSpec.round_calendar(expires_round=3),
    ).instance
    assert first is not None
    generation = first.current_generation_id
    lifecycle = first.lifecycle_window

    second = apply_sabotage(
        systems,
        context,
        owner="a",
        source="c",
    )

    assert second.status is StateApplicationResultStatus.REJECTED_CONFLICT
    assert second.reason_rule_id == SABOTAGE_EQUAL_REAPPLICATION_RULE_ID
    resident = context.states.get(first.instance_id)
    assert resident.current_generation_id == generation
    assert resident.lifecycle_window == lifecycle


def test_numeric_stronger_weaker_dimension_is_explicitly_unsupported() -> None:
    context, systems = make_context(), BattleSystems()
    result = apply_sabotage(systems, context, strength=2.0)
    assert result.status is StateApplicationResultStatus.UNSUPPORTED_BOUNDARY
    assert result.reason_rule_id == SABOTAGE_STRENGTH_BOUNDARY_RULE_ID


def test_natural_expiry_and_observed_cleanse_restore_future_effectiveness() -> None:
    for operation in (
        RemovalOperation.NATURAL_EXPIRY,
        RemovalOperation.ORDINARY_CLEANSE,
    ):
        context, systems = make_context(), BattleSystems()
        _, ref = register_equipment(
            systems,
            kind=EquipmentContributionKind.ATTRIBUTE,
        )
        sabotage = apply_sabotage(systems, context).instance
        assert sabotage is not None
        assert_suppressed(systems, context, ref)

        removed = remove_state(
            systems,
            context,
            sabotage.instance_id,
            operation,
        )

        assert removed.status is StateRemovalResultStatus.REMOVED
        assert_effective(systems, context, ref)


@pytest.mark.parametrize(
    "operation",
    [
        RemovalOperation.SPECIALIZED_CLEANSE,
        RemovalOperation.SCRIPTED_GAMEPLAY_REMOVE,
    ],
)
def test_unobserved_gameplay_removal_classes_remain_unsupported(
    operation: RemovalOperation,
) -> None:
    context, systems = make_context(), BattleSystems()
    _, ref = register_equipment(systems)
    sabotage = apply_sabotage(systems, context).instance
    assert sabotage is not None

    result = remove_state(systems, context, sabotage.instance_id, operation)

    assert result.status is StateRemovalResultStatus.UNSUPPORTED_BOUNDARY
    assert context.states.has_instance(sabotage.instance_id)
    assert_suppressed(systems, context, ref)


def test_false_report_and_sabotage_causes_compose_sabotage_removed_first() -> None:
    context, systems = make_context(), BattleSystems()
    _, ref = register_equipment(
        systems,
        provider_key="踩踏",
        contribution_key="踩踏",
        kind=EquipmentContributionKind.TRIGGER,
    )
    false_report = apply_state(
        systems,
        context,
        OfficialStateId.FALSE_REPORT.value,
        owner="a",
    ).instance
    assert false_report is not None
    sabotage = apply_sabotage(systems, context).instance
    assert sabotage is not None

    decision = systems.equipment_effectiveness_policy.evaluate_contribution(
        context, ref
    )
    assert decision.status is EquipmentEffectivenessStatus.SUPPRESSED
    assert any(
        cause.rule_id == SABOTAGE_PROVIDER_SUPPRESSION_RULE_ID
        for cause in decision.suppression_causes
    )
    assert any(
        cause.rule_id == FALSE_REPORT_EQUIPMENT_SUPPRESSION_RULE_ID
        for cause in decision.suppression_causes
    )

    remove_state(systems, context, sabotage.instance_id)
    still = systems.equipment_effectiveness_policy.evaluate_contribution(
        context, ref
    )
    assert still.status is EquipmentEffectivenessStatus.SUPPRESSED
    assert any(
        cause.rule_id == FALSE_REPORT_EQUIPMENT_SUPPRESSION_RULE_ID
        for cause in still.suppression_causes
    )

    remove_state(systems, context, false_report.instance_id)
    assert_effective(systems, context, ref)


def test_false_report_and_sabotage_causes_compose_false_report_removed_first() -> None:
    context, systems = make_context(), BattleSystems()
    _, ref = register_equipment(
        systems,
        provider_key="踩踏",
        contribution_key="踩踏",
        kind=EquipmentContributionKind.TRIGGER,
    )
    false_report = apply_state(
        systems,
        context,
        OfficialStateId.FALSE_REPORT.value,
        owner="a",
    ).instance
    assert false_report is not None
    sabotage = apply_sabotage(systems, context).instance
    assert sabotage is not None

    remove_state(systems, context, false_report.instance_id)
    assert_suppressed(systems, context, ref)
    remove_state(systems, context, sabotage.instance_id)
    assert_effective(systems, context, ref)


@pytest.mark.parametrize(
    "kind",
    [
        EquipmentContributionKind.ATTRIBUTE,
        EquipmentContributionKind.DAMAGE_MODIFIER,
        EquipmentContributionKind.RECOVERY_MODIFIER,
    ],
)
def test_false_report_alone_does_not_gain_sabotage_ordinary_equipment_scope(
    kind: EquipmentContributionKind,
) -> None:
    context, systems = make_context(), BattleSystems()
    _, ref = register_equipment(
        systems,
        provider_key=f"ordinary:{kind.value}",
        kind=kind,
    )
    apply_state(
        systems,
        context,
        OfficialStateId.FALSE_REPORT.value,
        owner="a",
    )
    assert_effective(systems, context, ref)


def test_dynamic_equipment_created_after_sabotage_is_not_silently_generalized() -> None:
    context, systems = make_context(), BattleSystems()
    sabotage = apply_sabotage(systems, context).instance
    assert sabotage is not None

    _, ref = register_equipment(
        systems,
        provider_key="dynamic:post-sabotage",
        kind=EquipmentContributionKind.ATTRIBUTE,
    )
    decision = systems.equipment_effectiveness_policy.evaluate_contribution(
        context, ref
    )

    assert decision.status is EquipmentEffectivenessStatus.UNSUPPORTED_BOUNDARY


def test_equipment_effectiveness_queries_publish_no_public_event() -> None:
    context, systems = make_context(), BattleSystems()
    _, ref = register_equipment(systems)
    apply_sabotage(systems, context)
    before = tuple(context.event_bus.history)

    systems.equipment_effectiveness_policy.evaluate_contribution(context, ref)

    assert tuple(context.event_bus.history) == before


def test_sabotage_does_not_mutate_baseline_enabled_or_provider_identity() -> None:
    context, systems = make_context(), BattleSystems()
    provider_ref, ref = register_equipment(systems)
    before = systems.equipment_contribution_registry.resolve_provider(
        context, provider_ref
    )
    apply_sabotage(systems, context)
    after = systems.equipment_contribution_registry.resolve_provider(
        context, provider_ref
    )

    assert before is after
    assert after is not None and after.enabled is True
    assert ref.provider_ref is provider_ref


def test_static_architecture_guards() -> None:
    source = inspect.getsource(sabotage_module)
    assert "import random" not in source
    assert "context.random" not in source
    assert ".enabled =" not in source
    assert "unequip(" not in source
    assert "clear_slot" not in source
    assert "EventBus" not in source
    assert "DamageSystem" not in source
    assert "RecoverySystem" not in source
    assert "TriggerSystem" not in source
    assert "OfficialStateId.CAPTURE" not in source
    assert "690110" not in source

    from sgs_v2.battle_core import damage_modifier_system
    from sgs_v2.battle_core import recovery_system
    from sgs_v2.battle_core import trigger_system

    for module in (
        damage_modifier_system,
        recovery_system,
        trigger_system,
    ):
        consumer_source = inspect.getsource(module)
        assert "EQUIPMENT_DISABLE" not in consumer_source
        assert "690109" not in consumer_source


def test_provider_dependency_graph_is_explicit_and_owner_local() -> None:
    context, systems = make_context(), BattleSystems()
    provider_ref, _ = register_equipment(
        systems,
        owner="a",
        provider_key="armor:graph",
    )
    sabotage = apply_sabotage(systems, context, owner="a").instance
    assert sabotage is not None

    assert systems.dependency_evaluation_support.prerequisites(
        ProviderNode(provider_ref)
    ) == (StateNode(sabotage.instance_id),)

    unrelated_provider, unrelated_ref = register_equipment(
        systems,
        owner="b",
        provider_key="armor:other-owner",
    )
    assert systems.dependency_evaluation_support.prerequisites(
        ProviderNode(unrelated_provider)
    ) == ()
    assert_effective(systems, context, unrelated_ref)
