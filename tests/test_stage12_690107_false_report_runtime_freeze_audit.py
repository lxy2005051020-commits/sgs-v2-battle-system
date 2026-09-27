from __future__ import annotations

import inspect

from sgs_v2.battle_core import (
    BattleContext,
    BattlePhase,
    BattleSystems,
    DamageSkillEffectSpec,
    DamageType,
    EmptyStateRuntimeParams,
    EquipmentContributionKind,
    EquipmentContributionRef,
    EquipmentEffectivenessStatus,
    EquipmentProviderRef,
    EventBus,
    LineupPosition,
    OfficialStateId,
    PreparationMode,
    ProviderDependency,
    ProviderNode,
    ProviderValidityStatus,
    RandomSystem,
    SkillDefinition,
    SkillOperationAdmissionRequest,
    SkillOperationAdmissionStatus,
    SkillOperationKind,
    SkillProviderRef,
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
from sgs_v2.battle_core import false_report_integration as fr_module
from sgs_v2.battle_core.state_effectiveness import StateEffectivenessStatus
from sgs_v2.battle_core.stage11_state_params import DisarmStateParams, StunStateParams
from sgs_v2.battle_core.state_removal import RemovalOperation


class CountingRandomSystem(RandomSystem):
    def __init__(self, seed: int = 690107) -> None:
        super().__init__(seed)
        self.chance_calls = 0
        self.sample_calls = 0

    def chance(self, probability: float) -> bool:
        self.chance_calls += 1
        return True

    def sample(self, values, k):  # type: ignore[no-untyped-def]
        self.sample_calls += 1
        return super().sample(values, k)


def make_context(random_system: RandomSystem | None = None) -> BattleContext:
    context = BattleContext(
        battle_id="stage12-690107-freeze-audit",
        units={
            "a": UnitRuntime(
                "a", "A", "A", 1000, 1000, 300, 100, 100,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "d": UnitRuntime(
                "d", "D", "A", 1000, 1000, 100, 100, 95,
                lineup_position=LineupPosition.DEPUTY_1,
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
        random=random_system or RandomSystem(690107),
    )
    register_official_state_definitions(context.states)
    context.current_round = 1
    context.current_phase = BattlePhase.UNIT_ACTION.value
    return context


def runtime(
    *,
    owner: str = "a",
    slot: SkillSlot = SkillSlot.INHERENT,
    skill_id: str = "fr-audit-provider",
    skill_type: SkillType = SkillType.PASSIVE,
    preparation: PreparationMode = PreparationMode.NONE,
    rate: float = 1.0,
) -> SkillRuntime:
    return SkillRuntime(
        definition=SkillDefinition(
            skill_id=skill_id,
            name=skill_id,
            activation_rate=rate,
            target_mode=SkillTargetMode.SINGLE_RANDOM_ENEMY,
            effect_specs=(DamageSkillEffectSpec(DamageType.WEAPON),),
            skill_type=skill_type,
            preparation_mode=preparation,
        ),
        owner_id=owner,
        skill_slot=slot,
        enabled=True,
    )


def register_runtime(context: BattleContext, **kwargs) -> SkillRuntime:
    item = runtime(**kwargs)
    context.skill_runtimes.register(item)
    return item


def provider_ref(item: SkillRuntime) -> SkillProviderRef:
    assert item.skill_slot is not None
    return SkillProviderRef(item.owner_id, item.skill_slot, item.definition.skill_id)


def params_for(state_id: str):
    if state_id == OfficialStateId.DISARM.value:
        return DisarmStateParams(block_probability=0.5)
    if state_id == OfficialStateId.STUN.value:
        return StunStateParams(remaining_blocks=2)
    return EmptyStateRuntimeParams()


def candidate(
    state_id: str,
    *,
    owner: str = "a",
    source: str = "b",
    lifetime: StateLifetimeSpec | None = None,
    dependencies=(),
) -> StateCandidate:
    return StateCandidate(
        state_id=state_id,
        owner_id=owner,
        source_id=source,
        source_skill_id=f"source-{state_id}",
        source_skill_slot=SkillSlot.LEARNED_1,
        runtime_params_candidate=params_for(state_id),
        lifetime_spec=lifetime,
        provider_dependencies=tuple(dependencies),
        application_provenance="stage12-690107-runtime-freeze-audit",
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


def apply_fr(
    systems: BattleSystems,
    context: BattleContext,
    *,
    owner: str = "a",
    source: str = "b",
    lifetime: StateLifetimeSpec | None = None,
):
    return apply_state(
        systems,
        context,
        OfficialStateId.FALSE_REPORT.value,
        owner=owner,
        source=source,
        lifetime=lifetime,
    )


def remove_fr(systems: BattleSystems, context: BattleContext, instance_id: str) -> None:
    result = systems.state_removal_coordinator.remove(
        context,
        operation=RemovalOperation.ORDINARY_CLEANSE,
        instance_id=instance_id,
    )
    assert result.removed_instance is not None


def admit(
    systems: BattleSystems,
    context: BattleContext,
    item: SkillRuntime,
    *,
    operation_kind: SkillOperationKind = SkillOperationKind.NEW_ADMISSION,
):
    return systems.skill_operation_admission_coordinator.evaluate(
        context,
        SkillOperationAdmissionRequest(
            actor_id=item.owner_id,
            provider_ref=provider_ref(item),
            skill_type=item.definition.skill_type,
            preparation_mode=item.definition.preparation_mode,
            operation_kind=operation_kind,
        ),
    )


def test_active_execution_under_false_report() -> None:
    context = make_context()
    item = register_runtime(context, skill_type=SkillType.ACTIVE)
    systems = BattleSystems()
    apply_fr(systems, context)

    result = systems.skill_resolver.resolve(context, item)

    assert result.status is SkillResolutionStatus.RESOLVED
    assert result.effects


def test_preparation_active_start_and_complete_under_false_report() -> None:
    context = make_context()
    item = register_runtime(
        context,
        skill_type=SkillType.ACTIVE,
        preparation=PreparationMode.REQUIRED,
    )
    systems = BattleSystems()
    apply_fr(systems, context)

    assert admit(systems, context, item).status is SkillOperationAdmissionStatus.ALLOW
    assert (
        admit(
            systems,
            context,
            item,
            operation_kind=SkillOperationKind.CONTINUATION,
        ).status
        is SkillOperationAdmissionStatus.ALLOW
    )


def test_assault_execution_under_false_report() -> None:
    context = make_context()
    item = register_runtime(context, skill_type=SkillType.ASSAULT)
    systems = BattleSystems()
    apply_fr(systems, context)

    result = systems.skill_resolver.resolve(context, item)

    assert result.status is SkillResolutionStatus.RESOLVED


def test_talent_intact_under_false_report() -> None:
    context = make_context()
    item = register_runtime(context, skill_type=SkillType.TALENT)
    systems = BattleSystems()
    apply_fr(systems, context)

    assert (
        systems.provider_validity_policy.evaluate_provider(context, provider_ref(item)).status
        is ProviderValidityStatus.VALID
    )
    assert systems.skill_resolver.resolve(context, item).status is SkillResolutionStatus.RESOLVED


def test_command_ally_cascade_and_passive_enemy_cascade() -> None:
    context = make_context()
    command = register_runtime(context, skill_type=SkillType.COMMAND)
    passive = register_runtime(
        context,
        slot=SkillSlot.LEARNED_1,
        skill_id="passive-enemy-provider",
        skill_type=SkillType.PASSIVE,
    )
    systems = BattleSystems()
    fr = apply_fr(systems, context).instance
    assert fr is not None

    ally_effect = apply_state(
        systems,
        context,
        OfficialStateId.PROVOKE.value,
        owner="d",
        source="a",
        dependencies=(ProviderDependency(provider_ref(command), "FR_ALLY"),),
    ).instance
    enemy_effect = apply_state(
        systems,
        context,
        OfficialStateId.CONFUSION.value,
        owner="b",
        source="a",
        dependencies=(ProviderDependency(provider_ref(passive), "FR_ENEMY"),),
    ).instance
    assert ally_effect is not None and enemy_effect is not None

    assert (
        systems.state_effectiveness_policy.evaluate_state(context, ally_effect).status
        is StateEffectivenessStatus.SUPPRESSED
    )
    assert (
        systems.state_effectiveness_policy.evaluate_state(context, enemy_effect).status
        is StateEffectivenessStatus.SUPPRESSED
    )

    remove_fr(systems, context, fr.instance_id)
    assert systems.state_effectiveness_policy.evaluate_state(context, ally_effect).effective
    assert systems.state_effectiveness_policy.evaluate_state(context, enemy_effect).effective


def test_holder_false_report_does_not_break_external_provider_effect() -> None:
    context = make_context()
    external = register_runtime(
        context,
        owner="b",
        skill_id="external-command",
        skill_type=SkillType.COMMAND,
    )
    systems = BattleSystems()
    effect = apply_state(
        systems,
        context,
        OfficialStateId.PROVOKE.value,
        owner="a",
        source="b",
        dependencies=(ProviderDependency(provider_ref(external), "EXTERNAL"),),
    ).instance
    assert effect is not None

    apply_fr(systems, context, owner="a", source="c")

    assert (
        systems.provider_validity_policy.evaluate_provider(context, provider_ref(external)).status
        is ProviderValidityStatus.VALID
    )
    assert systems.state_effectiveness_policy.evaluate_state(context, effect).effective


def test_gangyi_failure_two_stage_reaches_apply_then_suppresses_special() -> None:
    context = make_context()
    systems = BattleSystems()
    equipment_provider = EquipmentProviderRef("a", "刚毅")
    systems.equipment_contribution_registry.register_provider(equipment_provider)
    contribution = EquipmentContributionRef(
        equipment_provider,
        "刚毅",
        EquipmentContributionKind.LIVE_EFFECT,
    )
    systems.equipment_contribution_registry.register_contribution(contribution)

    systems.state_admission_policy.register_rule_adapter(lambda _ctx, _candidate: None)
    result = apply_fr(systems, context)

    assert result.status is StateApplicationResultStatus.APPLIED
    assert (
        systems.equipment_effectiveness_policy.evaluate_contribution(
            context, contribution
        ).status
        is EquipmentEffectivenessStatus.SUPPRESSED
    )


def test_missed_provider_opportunity_is_not_replayed_on_resume() -> None:
    rng = CountingRandomSystem()
    context = make_context(rng)
    item = register_runtime(context, skill_type=SkillType.PASSIVE, rate=1.0)
    systems = BattleSystems()
    fr = apply_fr(systems, context).instance
    assert fr is not None

    missed = systems.skill_resolver.resolve(context, item)
    assert missed.status is SkillResolutionStatus.DISABLED
    assert rng.sample_calls == 0

    damage_events_before = sum(
        event.event_type.value == "DAMAGE_DEALT" for event in context.event_bus.history
    )
    remove_fr(systems, context, fr.instance_id)
    assert rng.sample_calls == 0
    assert sum(
        event.event_type.value == "DAMAGE_DEALT" for event in context.event_bus.history
    ) == damage_events_before

    future = systems.skill_resolver.resolve(context, item)
    assert future.status is SkillResolutionStatus.RESOLVED
    assert rng.sample_calls == 1


def test_resolved_damage_is_not_rolled_back_by_later_false_report() -> None:
    context = make_context()
    item = register_runtime(context, skill_type=SkillType.PASSIVE, rate=1.0)
    systems = BattleSystems()

    resolved = systems.skill_resolver.resolve(context, item)
    assert resolved.status is SkillResolutionStatus.RESOLVED
    target_id = resolved.target_ids[0]
    before = context.get_unit(target_id).troops
    for effect in resolved.effects:
        systems.effect_executor.execute(context, effect)
    after_damage = context.get_unit(target_id).troops
    assert after_damage < before

    apply_fr(systems, context)

    assert context.get_unit(target_id).troops == after_damage


def test_false_report_and_stun_are_independent() -> None:
    context = make_context()
    systems = BattleSystems()
    apply_fr(systems, context)
    stun = apply_state(systems, context, OfficialStateId.STUN.value).instance
    assert stun is not None

    before = context.states.get(stun.instance_id).runtime_params.remaining_blocks
    assert systems.stage11_state_runtime.consume_stun_natural_action(context, "a") is True
    after = context.states.get(stun.instance_id).runtime_params.remaining_blocks
    assert after == before - 1


def test_false_report_and_disarm_are_independent() -> None:
    rng = CountingRandomSystem()
    context = make_context(rng)
    systems = BattleSystems()
    apply_fr(systems, context)
    disarm = apply_state(systems, context, OfficialStateId.DISARM.value).instance
    assert disarm is not None

    assert systems.stage11_state_runtime.disarm_blocks(context, "a") is True
    assert rng.chance_calls == 1


def test_false_report_and_confusion_targeting_are_independent() -> None:
    context_with_fr = make_context(RandomSystem(8801))
    systems_with_fr = BattleSystems()
    confusion_with_fr = apply_state(
        systems_with_fr,
        context_with_fr,
        OfficialStateId.CONFUSION.value,
    ).instance
    assert confusion_with_fr is not None
    apply_fr(systems_with_fr, context_with_fr)

    context_control = make_context(RandomSystem(8801))
    systems_control = BattleSystems()
    confusion_control = apply_state(
        systems_control,
        context_control,
        OfficialStateId.CONFUSION.value,
    ).instance
    assert confusion_control is not None

    with_fr = systems_with_fr.target_resolution_system.resolve(
        context_with_fr,
        "a",
        normal_attack_id=context_with_fr.id_allocator.allocate_normal_attack_id(),
    )
    control = systems_control.target_resolution_system.resolve(
        context_control,
        "a",
        normal_attack_id=context_control.id_allocator.allocate_normal_attack_id(),
    )

    assert systems_with_fr.stage9_state_runtime.get_operational_confusion(
        context_with_fr, "a"
    ) is not None
    assert with_fr is not None and control is not None
    assert with_fr.intended_attack_target == control.intended_attack_target


def test_holder_action_duration_representative_timeline() -> None:
    context = make_context()
    item = register_runtime(context, skill_type=SkillType.COMMAND)
    systems = BattleSystems()
    fr = apply_fr(
        systems,
        context,
        lifetime=StateLifetimeSpec.holder_action_window(2),
    ).instance
    assert fr is not None

    assert (
        systems.provider_validity_policy.evaluate_provider(context, provider_ref(item)).status
        is ProviderValidityStatus.SUPPRESSED
    )

    due1 = systems.state_lifecycle_system.due_at_action_start(context, "a")
    assert fr.instance_id not in {item.instance_id for item in due1}
    removed1 = systems.state_lifecycle_system.settle_action_start_lifetimes(context, "a")
    assert removed1 == []
    assert context.states.has_instance(fr.instance_id)
    assert (
        systems.provider_validity_policy.evaluate_provider(context, provider_ref(item)).status
        is ProviderValidityStatus.SUPPRESSED
    )

    due2 = systems.state_lifecycle_system.due_at_action_start(context, "a")
    assert fr.instance_id in {item.instance_id for item in due2}
    before = systems.effectiveness_transition_coordinator.capture(
        context,
        tuple(StateNode(item.instance_id) for item in due2),
    )
    removed2 = systems.state_lifecycle_system.settle_action_start_lifetimes(context, "a")
    systems.effectiveness_transition_coordinator.complete_removed_nodes(
        context,
        before,
        tuple(StateNode(item.instance_id) for item in removed2),
    )

    assert not context.states.has_instance(fr.instance_id)
    assert (
        systems.provider_validity_policy.evaluate_provider(context, provider_ref(item)).status
        is ProviderValidityStatus.VALID
    )


def test_false_report_runtime_freeze_static_owner_guards() -> None:
    source = inspect.getsource(fr_module)
    assert "SkillType.TALENT" not in source
    assert "SkillType.PASSIVE" in source and "SkillType.COMMAND" in source
    assert ".enabled =" not in source
    assert "context.random" not in source and "import random" not in source
    assert "StateLifecycleSystem.remove" not in source
    assert "EffectSourceRef" not in source
    assert "ActionSystem" not in source and "NormalAttackSystem" not in source
