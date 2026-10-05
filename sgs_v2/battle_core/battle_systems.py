from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from .action_order_system import ActionOrderSystem
from .action_system import ActionSystem
from .attribute_system import AttributeSystem
from .state_modifiers import StateModifierSupport, modifier_conflict_rule, IncomingDamageReductionProvider
from .state_application_reaction import ReactingStateApplicationCoordinator, ReactingStateLifecycleSystem
from .scheduled_skill import ScheduledSkillSupport
from .normal_attack_followup import NormalAttackFollowupPort, ProbabilisticComboRuntime
from .state_effectiveness_trigger import StateEffectivenessTriggerAdapter
from .troop_admission import resolve_opening_troop_definition
from .battle_finalization_coordinator import BattleFinalizationCoordinator
from .dependency_evaluation import DependencyEvaluationSupport
from .chain_system import ChainSystem, DamageCallbackAdmissionPoint
from .cleave_system import CleaveSystem
from .cleave_derived_damage_system import CleaveDerivedDamageResolver
from .continuous_damage_basis_producer import ContinuousDamageBasisProducer
from .counter_system import CounterSystem
from .damage_aftermath_port import DamageAftermathPort, DamageAftermathSystem
from .defeat_cleanup_port import DefeatCleanupPort
from .hit_resolution_system import HitResolutionSystem
from .damage_rule_provider import StateDamageRuleProvider
from .damage_instance_coordinator import DamageInstanceCoordinator
from .damage_modifier_system import DamageModifierSystem
from .damage_partition_system import DamagePartitionCoordinator
from .damage_resolution_system import DamageResolutionSystem
from .damage_system import DamageSystem
from .direct_troop_loss_system import DirectTroopLossResolver
from .effect_executor import EffectExecutor
from .equipment_effectiveness import (
    EquipmentContributionRegistry,
    EquipmentEffectivenessPolicy,
)
from .execution_right_runtime import (
    CurrentActorPermissionPolicy,
    DamageExecutionRightPort,
    ExecutionRightSupport,
    ExecutionTargetEligibilityPolicy,
    RecoveryExecutionPreventionPolicy,
)
from .execution_right_system import (
    AssaultDispatchPort,
    FutureAdmissionGate,
    LegacyActionDispatchAdapter,
)
from .normal_attack_system import NormalAttackSystem
from .recovery_opportunity_system import RecoveryOpportunitySystem
from .recovery_system import RecoveryModifierProvider, RecoverySystem
from .provider_validity import ProviderValidityPolicy
from .preparation_interruption import PreparationInterruptionPort
from .preparation_state import PreparationStateOwner
from .skill_operation_admission import SkillOperationAdmissionCoordinator
from .skill_permission import SkillPermissionPolicy
from .skill_target_policy import SkillTargetPolicy
from .state_effectiveness import StateEffectivenessPolicy
from .state_application import (
    StateAdmissionPolicy,
    StateApplicationCoordinator,
    StateConflictPolicy,
)
from .state_removal import StateRemovalCoordinator, StateRemovalPolicy
from .effectiveness_transition import EffectivenessTransitionCoordinator
from .effectiveness_transition_events import StateEffectivenessEventAdapter
from .insight_integration import register_insight_integration
from .exhaustion_integration import register_exhaustion_integration
from .false_report_integration import register_false_report_integration
from .intimidation_integration import register_intimidation_integration
from .sabotage_integration import register_sabotage_integration
from .provocation_integration import register_provocation_integration
from .capture_integration import register_capture_integration
from .rule_hook_system import RuleHookSystem
from .skill_resolver import SkillResolver
from .stage9_state_runtime import Stage9StateRuntime
from .stage11_state_runtime import (
    Stage11StateRuntime,
    stage11_legacy_effectiveness_adapter,
)
from .stage11_attacker_recovery import Stage11AttackerRecoverySystem
from .state_lifecycle_system import StateLifecycleSystem
from .target_resolution_system import TargetResolutionSystem
from .target_system import TargetSystem
from .trigger_system import TriggerSystem
from .troop_system import TroopSystem
from .treatment_formula import TreatmentFormulaSystem
from .victory_system import VictorySystem
from .pending_work import PendingWorkSystem


@dataclass(slots=True)
class BattleSystems:
    """BattleSystem 组合根，供 BattleEngine 与显式规则层使用。"""

    attribute_system: AttributeSystem = field(default_factory=AttributeSystem)
    target_system: TargetSystem = field(default_factory=TargetSystem)
    troop_system: TroopSystem = field(default_factory=TroopSystem)
    victory_system: VictorySystem = field(default_factory=VictorySystem)

    weapon_troop_function_table: Mapping[int, int] | None = None
    weapon_random_percent_range: tuple[int, int] = (86, 94)
    weapon_low_damage_floor_range: tuple[int, int] = (5, 15)

    strategy_troop_function_table: Mapping[int, int] | None = None
    strategy_random_percent_range: tuple[int, int] = (86, 94)
    strategy_low_damage_floor_range: tuple[int, int] = (5, 15)

    state_lifecycle_system: StateLifecycleSystem = field(default_factory=ReactingStateLifecycleSystem)
    # Effect owners supply evidence-backed policies. Official Stage8 DEFER states
    # are not silently activated by the Stage9 orchestration layer.
    cleave_hit_rules: object | None = None
    cleave_hit_consumption: object | None = None
    cleave_first_aid: object | None = None
    cleave_attacker_recovery: object | None = None
    counter_operationality: object | None = None
    damage_rule_provider: object | None = None
    defeat_cleanup_port: DefeatCleanupPort | None = None
    damage_aftermath_port: DamageAftermathPort | None = None
    recovery_modifier_provider: RecoveryModifierProvider | None = None
    preparation_interruption_port: PreparationInterruptionPort | None = None

    action_order_system: ActionOrderSystem = field(init=False)
    damage_system: DamageSystem = field(init=False)
    damage_resolution_system: DamageResolutionSystem = field(init=False)
    damage_instance_coordinator: DamageInstanceCoordinator = field(init=False)
    damage_partition_coordinator: DamagePartitionCoordinator = field(init=False)
    direct_troop_loss_resolver: DirectTroopLossResolver = field(init=False)
    normal_attack_system: NormalAttackSystem = field(init=False)
    action_system: ActionSystem = field(init=False)
    recovery_system: RecoverySystem = field(init=False)
    treatment_formula_system: TreatmentFormulaSystem = field(init=False)
    recovery_opportunity_system: RecoveryOpportunitySystem = field(init=False)
    damage_aftermath_system: DamageAftermathSystem = field(init=False)
    effect_executor: EffectExecutor = field(init=False)
    skill_resolver: SkillResolver = field(init=False)
    trigger_system: TriggerSystem = field(init=False)
    rule_hook_system: RuleHookSystem = field(init=False)
    finalization_coordinator: BattleFinalizationCoordinator = field(init=False)
    future_admission_gate: FutureAdmissionGate = field(init=False)
    pending_work_system: PendingWorkSystem = field(init=False)
    legacy_action_dispatch_adapter: LegacyActionDispatchAdapter = field(init=False)
    assault_dispatch_port: AssaultDispatchPort = field(init=False)
    stage9_state_runtime: Stage9StateRuntime = field(init=False)
    stage11_state_runtime: Stage11StateRuntime = field(init=False)
    stage11_attacker_recovery_system: Stage11AttackerRecoverySystem = field(init=False)
    target_resolution_system: TargetResolutionSystem = field(init=False)
    chain_system: ChainSystem = field(init=False)
    damage_callbacks: DamageCallbackAdmissionPoint = field(init=False)
    cleave_derived_damage_resolver: CleaveDerivedDamageResolver = field(init=False)
    cleave_system: CleaveSystem = field(init=False)
    counter_system: CounterSystem = field(init=False)
    continuous_damage_basis_producer: ContinuousDamageBasisProducer = field(init=False)
    dependency_evaluation_support: DependencyEvaluationSupport = field(init=False)
    state_effectiveness_policy: StateEffectivenessPolicy = field(init=False)
    provider_validity_policy: ProviderValidityPolicy = field(init=False)
    equipment_contribution_registry: EquipmentContributionRegistry = field(init=False)
    equipment_effectiveness_policy: EquipmentEffectivenessPolicy = field(init=False)
    current_actor_permission_policy: CurrentActorPermissionPolicy = field(init=False)
    execution_target_eligibility_policy: ExecutionTargetEligibilityPolicy = field(init=False)
    recovery_execution_prevention_policy: RecoveryExecutionPreventionPolicy = field(init=False)
    execution_right_support: ExecutionRightSupport = field(init=False)
    damage_execution_right_port: DamageExecutionRightPort = field(init=False)
    state_effectiveness_event_adapter: StateEffectivenessEventAdapter = field(init=False)
    skill_permission_policy: SkillPermissionPolicy = field(init=False)
    skill_operation_admission_coordinator: SkillOperationAdmissionCoordinator = field(init=False)
    skill_target_policy: SkillTargetPolicy = field(init=False)
    state_admission_policy: StateAdmissionPolicy = field(init=False)
    state_conflict_policy: StateConflictPolicy = field(init=False)
    state_removal_policy: StateRemovalPolicy = field(init=False)
    effectiveness_transition_coordinator: EffectivenessTransitionCoordinator = field(init=False)
    state_application_coordinator: StateApplicationCoordinator = field(init=False)
    state_removal_coordinator: StateRemovalCoordinator = field(init=False)
    preparation_state_owner: PreparationStateOwner = field(init=False)
    state_modifier_support: StateModifierSupport = field(init=False)
    scheduled_skill_support: ScheduledSkillSupport = field(init=False)

    def __post_init__(self) -> None:
        self.dependency_evaluation_support = DependencyEvaluationSupport()
        self.equipment_contribution_registry = EquipmentContributionRegistry()
        self.state_effectiveness_policy = StateEffectivenessPolicy(
            self.dependency_evaluation_support
        )
        self.state_effectiveness_policy.register_rule_adapter(
            stage11_legacy_effectiveness_adapter
        )
        self.state_modifier_support = StateModifierSupport(self.state_effectiveness_policy)
        self.attribute_system.register_modifier_provider(self.state_modifier_support)
        self.provider_validity_policy = ProviderValidityPolicy(
            self.dependency_evaluation_support,
            equipment_resolver=self.equipment_contribution_registry.resolve_provider,
        )
        self.equipment_effectiveness_policy = EquipmentEffectivenessPolicy(
            self.equipment_contribution_registry,
            self.provider_validity_policy,
        )
        self.attribute_system.bind_equipment_effectiveness_policy(
            self.equipment_effectiveness_policy
        )
        self.current_actor_permission_policy = CurrentActorPermissionPolicy()
        self.execution_target_eligibility_policy = ExecutionTargetEligibilityPolicy()
        self.recovery_execution_prevention_policy = RecoveryExecutionPreventionPolicy()
        self.execution_right_support = ExecutionRightSupport(
            actor_policy=self.current_actor_permission_policy,
            provider_policy=self.provider_validity_policy,
            target_policy=self.execution_target_eligibility_policy,
            equipment_policy=self.equipment_effectiveness_policy,
            state_policy=self.state_effectiveness_policy,
        )
        self.damage_execution_right_port = DamageExecutionRightPort(
            self.execution_right_support
        )
        self.skill_permission_policy = SkillPermissionPolicy()
        self.skill_operation_admission_coordinator = SkillOperationAdmissionCoordinator(
            self.provider_validity_policy,
            self.skill_permission_policy,
        )
        self.skill_target_policy = SkillTargetPolicy()
        self.preparation_state_owner = PreparationStateOwner()
        if self.preparation_interruption_port is None:
            # Production now has a concrete minimal PREPARING owner. This is
            # interruption storage only, not the Stage15 preparation scheduler.
            self.preparation_interruption_port = self.preparation_state_owner
        self.dependency_evaluation_support.bind_evaluators(
            state_evaluator=self.state_effectiveness_policy.evaluate_node,
            provider_evaluator=self.provider_validity_policy.evaluate_node,
        )
        self.state_admission_policy = StateAdmissionPolicy()
        self.state_conflict_policy = StateConflictPolicy()
        self.state_conflict_policy.register_rule_adapter(modifier_conflict_rule)
        self.state_removal_policy = StateRemovalPolicy()
        self.effectiveness_transition_coordinator = EffectivenessTransitionCoordinator(
            dependencies=self.dependency_evaluation_support,
            state_policy=self.state_effectiveness_policy,
            provider_policy=self.provider_validity_policy,
        )
        self.state_effectiveness_event_adapter = StateEffectivenessEventAdapter()
        self.effectiveness_transition_coordinator.register_state_public_fact_port(
            self.state_effectiveness_event_adapter
        )
        self.state_application_coordinator = ReactingStateApplicationCoordinator(
            admission_policy=self.state_admission_policy,
            conflict_policy=self.state_conflict_policy,
            lifecycle=self.state_lifecycle_system,
            dependencies=self.dependency_evaluation_support,
            transition_coordinator=self.effectiveness_transition_coordinator,
            state_effectiveness_policy=self.state_effectiveness_policy,
        )
        if isinstance(self.state_lifecycle_system, ReactingStateLifecycleSystem):
            self.state_lifecycle_system.reaction_port = self.state_application_coordinator.react
            self.state_lifecycle_system.association_transition_coordinator = self.effectiveness_transition_coordinator
        self.state_removal_coordinator = StateRemovalCoordinator(
            policy=self.state_removal_policy,
            lifecycle=self.state_lifecycle_system,
            transition_coordinator=self.effectiveness_transition_coordinator,
        )
        register_insight_integration(
            state_admission_policy=self.state_admission_policy,
            state_conflict_policy=self.state_conflict_policy,
            state_effectiveness_policy=self.state_effectiveness_policy,
            state_application_coordinator=self.state_application_coordinator,
        )
        register_exhaustion_integration(
            state_effectiveness_policy=self.state_effectiveness_policy,
            skill_permission_policy=self.skill_permission_policy,
            effectiveness_transition_coordinator=self.effectiveness_transition_coordinator,
            preparation_interruption_port=self.preparation_interruption_port,
            state_application_coordinator=self.state_application_coordinator,
        )

        register_false_report_integration(
            state_admission_policy=self.state_admission_policy,
            state_conflict_policy=self.state_conflict_policy,
            state_effectiveness_policy=self.state_effectiveness_policy,
            provider_validity_policy=self.provider_validity_policy,
            equipment_effectiveness_policy=self.equipment_effectiveness_policy,
            state_application_coordinator=self.state_application_coordinator,
            state_removal_policy=self.state_removal_policy,
        )
        register_intimidation_integration(
            state_admission_policy=self.state_admission_policy,
            state_conflict_policy=self.state_conflict_policy,
            state_effectiveness_policy=self.state_effectiveness_policy,
            provider_validity_policy=self.provider_validity_policy,
            state_application_coordinator=self.state_application_coordinator,
            state_removal_policy=self.state_removal_policy,
            effectiveness_transition_coordinator=self.effectiveness_transition_coordinator,
            preparation_interruption_port=self.preparation_interruption_port,
            equipment_contribution_registry=self.equipment_contribution_registry,
            equipment_effectiveness_policy=self.equipment_effectiveness_policy,
            dependencies=self.dependency_evaluation_support,
        )
        register_sabotage_integration(
            state_admission_policy=self.state_admission_policy,
            state_conflict_policy=self.state_conflict_policy,
            state_effectiveness_policy=self.state_effectiveness_policy,
            provider_validity_policy=self.provider_validity_policy,
            equipment_contribution_registry=self.equipment_contribution_registry,
            equipment_effectiveness_policy=self.equipment_effectiveness_policy,
            state_application_coordinator=self.state_application_coordinator,
            state_removal_policy=self.state_removal_policy,
            dependencies=self.dependency_evaluation_support,
        )
        register_provocation_integration(
            state_conflict_policy=self.state_conflict_policy,
            state_effectiveness_policy=self.state_effectiveness_policy,
            skill_target_policy=self.skill_target_policy,
        )
        register_capture_integration(
            state_conflict_policy=self.state_conflict_policy,
            state_effectiveness_policy=self.state_effectiveness_policy,
            provider_validity_policy=self.provider_validity_policy,
            current_actor_permission_policy=self.current_actor_permission_policy,
            recovery_execution_prevention_policy=self.recovery_execution_prevention_policy,
            skill_target_policy=self.skill_target_policy,
            equipment_effectiveness_policy=self.equipment_effectiveness_policy,
            state_application_coordinator=self.state_application_coordinator,
            state_removal_policy=self.state_removal_policy,
        )

        self.stage11_state_runtime = Stage11StateRuntime(
            self.state_lifecycle_system,
            self.state_effectiveness_policy,
        )
        self.action_order_system = ActionOrderSystem(
            self.attribute_system, self.stage11_state_runtime
        )
        self.recovery_system = RecoverySystem(
            self.troop_system,
            self.stage11_state_runtime,
            recovery_modifier_provider=self.recovery_modifier_provider,
            equipment_effectiveness_policy=self.equipment_effectiveness_policy,
            execution_prevention_policy=self.recovery_execution_prevention_policy,
        )
        self.treatment_formula_system = TreatmentFormulaSystem(
            troop_function_table=self.weapon_troop_function_table,
        )
        self.recovery_opportunity_system = RecoveryOpportunitySystem(
            self.recovery_system,
            provider_validity_policy=self.provider_validity_policy,
            treatment_formula_system=self.treatment_formula_system,
        )
        self.stage11_attacker_recovery_system = Stage11AttackerRecoverySystem(
            self.recovery_system,
            self.stage11_state_runtime,
        )

        if self.defeat_cleanup_port is None:
            self.defeat_cleanup_port = DefeatCleanupPort(
                self.state_lifecycle_system,
                transition_coordinator=self.effectiveness_transition_coordinator,
            )

        self.damage_rule_provider = IncomingDamageReductionProvider(
            self.state_effectiveness_policy, self.damage_rule_provider)
        self.damage_system = DamageSystem(
            self.attribute_system,
            weapon_troop_function_table=self.weapon_troop_function_table,
            weapon_random_percent_range=self.weapon_random_percent_range,
            weapon_low_damage_floor_range=self.weapon_low_damage_floor_range,
            strategy_troop_function_table=self.strategy_troop_function_table,
            strategy_random_percent_range=self.strategy_random_percent_range,
            strategy_low_damage_floor_range=self.strategy_low_damage_floor_range,
            rule_provider=self.damage_rule_provider,
            modifier_system=DamageModifierSystem(self.equipment_effectiveness_policy),
            stage11_state_runtime=self.stage11_state_runtime,
        )
        self.damage_resolution_system = DamageResolutionSystem(
            self.damage_system,
            self.troop_system,
            defeat_cleanup_port=self.defeat_cleanup_port,
        )
        self.stage9_state_runtime = Stage9StateRuntime(
            state_lifecycle_system=self.state_lifecycle_system,
            counter_operationality=self.counter_operationality,
            state_effectiveness_policy=self.state_effectiveness_policy,
        )
        self.damage_partition_coordinator = DamagePartitionCoordinator(
            self.stage9_state_runtime,
        )
        self.direct_troop_loss_resolver = DirectTroopLossResolver(
            self.troop_system,
            defeat_cleanup_port=self.defeat_cleanup_port,
        )
        self.finalization_coordinator = BattleFinalizationCoordinator(
            victory_system=self.victory_system,
            state_lifecycle_system=self.state_lifecycle_system,
            effectiveness_transition_coordinator=self.effectiveness_transition_coordinator,
        )
        self.future_admission_gate = FutureAdmissionGate(
            coordinator=self.finalization_coordinator,
        )
        self.pending_work_system = PendingWorkSystem(
            self.execution_right_support, self.future_admission_gate,
        )
        self.chain_system = ChainSystem(
            self.stage9_state_runtime,
            self.future_admission_gate,
            self.troop_system,
            defeat_cleanup_port=self.defeat_cleanup_port,
        )
        self.damage_callbacks = DamageCallbackAdmissionPoint(
            self.future_admission_gate,
            self.chain_system,
            self.stage9_state_runtime,
        )

        self.continuous_damage_basis_producer = ContinuousDamageBasisProducer(
            self.attribute_system,
            rule_provider=self.damage_rule_provider,
            stage11_state_runtime=self.stage11_state_runtime,
        )
        self.state_lifecycle_system._basis_producer = self.continuous_damage_basis_producer
        self.trigger_system = StateEffectivenessTriggerAdapter(
            self.state_lifecycle_system,
            self.equipment_effectiveness_policy,
            self.state_effectiveness_policy,
        )

        self.damage_aftermath_system = DamageAftermathSystem(
            self.trigger_system,
            self.recovery_opportunity_system,
        )
        if self.damage_aftermath_port is None:
            self.damage_aftermath_port = self.damage_aftermath_system

        self.damage_instance_coordinator = DamageInstanceCoordinator(
            self.damage_system,
            self.damage_resolution_system,
            partition_coordinator=self.damage_partition_coordinator,
            direct_troop_loss_resolver=self.direct_troop_loss_resolver,
            finalization_coordinator=self.finalization_coordinator,
            resolved_damage_callback=self.damage_callbacks.accept,
            damage_aftermath_port=self.damage_aftermath_port,
            defeat_cleanup_port=self.defeat_cleanup_port,
            attacker_recovery_system=self.stage11_attacker_recovery_system,
            execution_right_port=self.damage_execution_right_port,
        )
        self.cleave_derived_damage_resolver = CleaveDerivedDamageResolver(
            troops=self.troop_system,
            partition=self.damage_partition_coordinator,
            direct_loss=self.direct_troop_loss_resolver,
            finalization=self.finalization_coordinator,
            hit_resolution=HitResolutionSystem(),
            hit_rules=self.cleave_hit_rules or StateDamageRuleProvider(()),
            damage_callbacks=self.damage_callbacks,
            first_aid=self.cleave_first_aid,
            attacker_recovery=(
                self.cleave_attacker_recovery
                or self.stage11_attacker_recovery_system.resolve_cleave
            ),
            consume_hit_prevention=self.cleave_hit_consumption,
            damage_aftermath_port=self.damage_aftermath_port,
            defeat_cleanup_port=self.defeat_cleanup_port,
            stage11_state_runtime=self.stage11_state_runtime,
        )
        self.cleave_system = CleaveSystem(self.stage9_state_runtime, self.future_admission_gate, self.cleave_derived_damage_resolver)
        self.counter_system = CounterSystem(self.stage9_state_runtime, self.future_admission_gate, self.damage_instance_coordinator)
        self.assault_dispatch_port = NormalAttackFollowupPort(
            self.future_admission_gate,
            lambda context, runtime, **kwargs: self.skill_resolver.resolve(context, runtime, **kwargs),
            lambda context, effect: self.effect_executor.execute(context, effect),
            self.state_effectiveness_policy)
        self.target_resolution_system = TargetResolutionSystem(
            self.target_system,
            self.stage9_state_runtime,
        )
        self.normal_attack_system = NormalAttackSystem(
            target_system=self.target_system,
            damage_resolution_system=self.damage_resolution_system,
            target_resolution_system=self.target_resolution_system,
            damage_instance_coordinator=self.damage_instance_coordinator,
            future_admission_gate=self.future_admission_gate,
            finalization_coordinator=self.finalization_coordinator,
            assault_dispatch_port=self.assault_dispatch_port,
            state_runtime=self.stage9_state_runtime,
            cleave_system=self.cleave_system,
            chain_system=self.chain_system,
            counter_system=self.counter_system,
            damage_callbacks=self.damage_callbacks,
            stage11_state_runtime=self.stage11_state_runtime,
        )
        self.action_system = ActionSystem(
            normal_attack_system=self.normal_attack_system,
            stage9_state_runtime=ProbabilisticComboRuntime(self.state_lifecycle_system,
                state_effectiveness_policy=self.state_effectiveness_policy),
            state_lifecycle_system=self.state_lifecycle_system,
            stage11_state_runtime=self.stage11_state_runtime,
            current_actor_permission_policy=self.current_actor_permission_policy,
        )
        self.legacy_action_dispatch_adapter = LegacyActionDispatchAdapter(
            action_system=lambda: self.action_system,
            gate=self.future_admission_gate,
        )
        self.effect_executor = EffectExecutor(
            self.damage_instance_coordinator,
            self.state_lifecycle_system,
            self.recovery_system,
        )
        self.skill_resolver = SkillResolver(
            self.target_system,
            admission_coordinator=self.skill_operation_admission_coordinator,
            target_policy=self.skill_target_policy,
            activation_rate_provider=self.state_modifier_support.activation_rate,
            continuous_damage_basis_producer=self.continuous_damage_basis_producer,
        )
        self.scheduled_skill_support = ScheduledSkillSupport(
            self.pending_work_system, self.skill_resolver, self.effect_executor,
            self.dependency_evaluation_support,
            lambda context, skill_id, owner_id: resolve_opening_troop_definition(context, self, skill_id, owner_id),
        )
        self.rule_hook_system = RuleHookSystem(
            self.trigger_system,
            self.effect_executor,
        )
        self.rule_hook_system.recovery_opportunity_system = self.recovery_opportunity_system
        self.rule_hook_system.recovery_opportunity_handler = (
            self.recovery_opportunity_system.evaluate_and_resolve
        )
