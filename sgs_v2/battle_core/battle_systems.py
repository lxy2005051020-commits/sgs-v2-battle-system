from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from .action_order_system import ActionOrderSystem
from .action_system import ActionSystem
from .attribute_system import AttributeSystem
from .battle_finalization_coordinator import BattleFinalizationCoordinator
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
from .damage_partition_system import DamagePartitionCoordinator
from .damage_resolution_system import DamageResolutionSystem
from .damage_system import DamageSystem
from .direct_troop_loss_system import DirectTroopLossResolver
from .effect_executor import EffectExecutor
from .execution_right_system import (
    AssaultDispatchPort,
    FutureAdmissionGate,
    LegacyActionDispatchAdapter,
)
from .normal_attack_system import NormalAttackSystem
from .recovery_opportunity_system import RecoveryOpportunitySystem
from .recovery_system import RecoverySystem
from .rule_hook_system import RuleHookSystem
from .skill_resolver import SkillResolver
from .stage9_state_runtime import Stage9StateRuntime
from .state_lifecycle_system import StateLifecycleSystem
from .target_resolution_system import TargetResolutionSystem
from .target_system import TargetSystem
from .trigger_system import TriggerSystem
from .troop_system import TroopSystem
from .victory_system import VictorySystem


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

    state_lifecycle_system: StateLifecycleSystem = field(default_factory=StateLifecycleSystem)
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

    action_order_system: ActionOrderSystem = field(init=False)
    damage_system: DamageSystem = field(init=False)
    damage_resolution_system: DamageResolutionSystem = field(init=False)
    damage_instance_coordinator: DamageInstanceCoordinator = field(init=False)
    damage_partition_coordinator: DamagePartitionCoordinator = field(init=False)
    direct_troop_loss_resolver: DirectTroopLossResolver = field(init=False)
    normal_attack_system: NormalAttackSystem = field(init=False)
    action_system: ActionSystem = field(init=False)
    recovery_system: RecoverySystem = field(init=False)
    recovery_opportunity_system: RecoveryOpportunitySystem = field(init=False)
    damage_aftermath_system: DamageAftermathSystem = field(init=False)
    effect_executor: EffectExecutor = field(init=False)
    skill_resolver: SkillResolver = field(init=False)
    trigger_system: TriggerSystem = field(init=False)
    rule_hook_system: RuleHookSystem = field(init=False)
    finalization_coordinator: BattleFinalizationCoordinator = field(init=False)
    future_admission_gate: FutureAdmissionGate = field(init=False)
    legacy_action_dispatch_adapter: LegacyActionDispatchAdapter = field(init=False)
    assault_dispatch_port: AssaultDispatchPort = field(init=False)
    stage9_state_runtime: Stage9StateRuntime = field(init=False)
    target_resolution_system: TargetResolutionSystem = field(init=False)
    chain_system: ChainSystem = field(init=False)
    damage_callbacks: DamageCallbackAdmissionPoint = field(init=False)
    cleave_derived_damage_resolver: CleaveDerivedDamageResolver = field(init=False)
    cleave_system: CleaveSystem = field(init=False)
    counter_system: CounterSystem = field(init=False)
    continuous_damage_basis_producer: ContinuousDamageBasisProducer = field(init=False)

    def __post_init__(self) -> None:
        self.action_order_system = ActionOrderSystem(self.attribute_system)
        self.recovery_system = RecoverySystem(self.troop_system)
        self.recovery_opportunity_system = RecoveryOpportunitySystem(self.recovery_system)

        if self.defeat_cleanup_port is None:
            self.defeat_cleanup_port = DefeatCleanupPort(self.state_lifecycle_system)

        self.damage_system = DamageSystem(
            self.attribute_system,
            weapon_troop_function_table=self.weapon_troop_function_table,
            weapon_random_percent_range=self.weapon_random_percent_range,
            weapon_low_damage_floor_range=self.weapon_low_damage_floor_range,
            strategy_troop_function_table=self.strategy_troop_function_table,
            strategy_random_percent_range=self.strategy_random_percent_range,
            strategy_low_damage_floor_range=self.strategy_low_damage_floor_range,
            rule_provider=self.damage_rule_provider,
        )
        self.damage_resolution_system = DamageResolutionSystem(
            self.damage_system,
            self.troop_system,
            defeat_cleanup_port=self.defeat_cleanup_port,
        )
        self.stage9_state_runtime = Stage9StateRuntime(
            state_lifecycle_system=self.state_lifecycle_system,
            counter_operationality=self.counter_operationality,
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
        )
        self.future_admission_gate = FutureAdmissionGate(
            coordinator=self.finalization_coordinator,
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
        )
        self.state_lifecycle_system._basis_producer = self.continuous_damage_basis_producer
        self.trigger_system = TriggerSystem(self.state_lifecycle_system)

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
            attacker_recovery=self.cleave_attacker_recovery,
            consume_hit_prevention=self.cleave_hit_consumption,
            damage_aftermath_port=self.damage_aftermath_port,
            defeat_cleanup_port=self.defeat_cleanup_port,
        )
        self.cleave_system = CleaveSystem(self.stage9_state_runtime, self.future_admission_gate, self.cleave_derived_damage_resolver)
        self.counter_system = CounterSystem(self.stage9_state_runtime, self.future_admission_gate, self.damage_instance_coordinator)
        self.assault_dispatch_port = AssaultDispatchPort(
            gate=self.future_admission_gate,
        )
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
        )
        self.action_system = ActionSystem(
            normal_attack_system=self.normal_attack_system,
            stage9_state_runtime=self.stage9_state_runtime,
            state_lifecycle_system=self.state_lifecycle_system,
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
        self.skill_resolver = SkillResolver(self.target_system)
        self.rule_hook_system = RuleHookSystem(
            self.trigger_system,
            self.effect_executor,
        )
        self.rule_hook_system.recovery_opportunity_system = self.recovery_opportunity_system
        self.rule_hook_system.recovery_opportunity_handler = (
            self.recovery_opportunity_system.evaluate_and_resolve
        )
