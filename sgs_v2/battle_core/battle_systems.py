from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from .action_order_system import ActionOrderSystem
from .action_system import ActionSystem
from .attribute_system import AttributeSystem
from .battle_finalization_coordinator import BattleFinalizationCoordinator
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

    action_order_system: ActionOrderSystem = field(init=False)
    damage_system: DamageSystem = field(init=False)
    damage_resolution_system: DamageResolutionSystem = field(init=False)
    damage_instance_coordinator: DamageInstanceCoordinator = field(init=False)
    damage_partition_coordinator: DamagePartitionCoordinator = field(init=False)
    direct_troop_loss_resolver: DirectTroopLossResolver = field(init=False)
    normal_attack_system: NormalAttackSystem = field(init=False)
    action_system: ActionSystem = field(init=False)
    recovery_system: RecoverySystem = field(init=False)
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

    def __post_init__(self) -> None:
        self.action_order_system = ActionOrderSystem(self.attribute_system)
        self.damage_system = DamageSystem(
            self.attribute_system,
            weapon_troop_function_table=self.weapon_troop_function_table,
            weapon_random_percent_range=self.weapon_random_percent_range,
            weapon_low_damage_floor_range=self.weapon_low_damage_floor_range,
            strategy_troop_function_table=self.strategy_troop_function_table,
            strategy_random_percent_range=self.strategy_random_percent_range,
            strategy_low_damage_floor_range=self.strategy_low_damage_floor_range,
        )
        self.damage_resolution_system = DamageResolutionSystem(
            self.damage_system,
            self.troop_system,
        )
        self.stage9_state_runtime = Stage9StateRuntime(
            state_lifecycle_system=self.state_lifecycle_system,
        )
        self.damage_partition_coordinator = DamagePartitionCoordinator(
            self.stage9_state_runtime,
        )
        self.direct_troop_loss_resolver = DirectTroopLossResolver(
            self.troop_system,
        )
        self.finalization_coordinator = BattleFinalizationCoordinator(
            victory_system=self.victory_system,
        )
        self.damage_instance_coordinator = DamageInstanceCoordinator(
            self.damage_system,
            self.damage_resolution_system,
            partition_coordinator=self.damage_partition_coordinator,
            direct_troop_loss_resolver=self.direct_troop_loss_resolver,
            finalization_coordinator=self.finalization_coordinator,
        )
        self.future_admission_gate = FutureAdmissionGate(
            coordinator=self.finalization_coordinator,
        )
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
        self.recovery_system = RecoverySystem(self.troop_system)
        self.effect_executor = EffectExecutor(
            self.damage_instance_coordinator,
            self.state_lifecycle_system,
            self.recovery_system,
        )
        self.skill_resolver = SkillResolver(self.target_system)
        self.trigger_system = TriggerSystem()
        self.rule_hook_system = RuleHookSystem(
            self.trigger_system,
            self.effect_executor,
        )
