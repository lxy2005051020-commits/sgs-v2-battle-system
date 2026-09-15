from .context import BattleContext, BattleResult
from .engine import BattleEngine
from .enums import (
    BattlePhase,
    BattleEndReason,
    DamageSourceType,
    DamageType,
    LineupPosition,
    TroopType,
)
from .events import BattleEvent, EventBus, EventType
from .random_system import RandomSystem
from .unit import UnitRuntime
from .action_order_system import ActionOrderSystem
from .action_system import ActionSystem
from .attribute_system import AttributeSystem, AttributeModifierProvider
from .battle_systems import BattleSystems
from .damage_formula_context import DamageDefensePolicy, DamageFormulaContext
from .damage_formula_policy_system import (
    DamageFormulaPolicyResult,
    DamageFormulaPolicySystem,
)
from .damage_modifiers import (
    AppliedDamageModifier,
    DamageModifierContribution,
    DamageModifierKind,
    DamageModifierOperation,
    DamageModifierPhase,
    DamageModifierResult,
)
from .damage_modifier_system import DamageModifierSystem
from .damage_pipeline_trace import DamagePipelineTrace, StageEvaluationStatus
from .damage_prevention_system import (
    DamageAllowedResult,
    DamagePermissionResult,
    DamagePreventedResult,
    DamagePreventionReason,
    DamagePreventionSystem,
)
from .damage_instance_coordinator import (
    DamageInstanceCoordinator,
    DamageInstanceExecution,
    PartitionExecutionStatus,
)
from .damage_partition_system import (
    DamagePartitionCoordinator,
    DamagePartitionKind,
    DamagePartitionPlan,
    DamageShareTransactionPlan,
    DistributionRuntimeAuthority,
    DistributionTransactionPlan,
    NoPartitionPlan,
)
from .direct_troop_loss_system import (
    AttributedDirectTroopLoss,
    DirectTroopLossRequest,
    DirectTroopLossResolution,
    DirectTroopLossResolver,
)
from .damage_resolution_system import (
    DamageResolutionResult,
    DamageResolutionSystem,
    DamageSettlementRequest,
    SettlementOrigin,
)
from .damage_rule_models import (
    DamageFormulaPolicyContribution,
    DamagePreventionContribution,
    DamagePreventionRuleKind,
    DamageRuleFamily,
    HitPreventionCategory,
    HitRuleContribution,
    HitRuleKind,
    RuleContributionSource,
)
from .damage_rule_provider import (
    DamageRuleCollection,
    DamageRuleProvider,
    StateDamageRuleProvider,
    StateRuleAdapter,
    StateRuleBinding,
)
from .damage_state_rule_bindings import (
    DEFAULT_STAGE8_STATE_RULE_BINDINGS,
    default_stage8_official_binding_state_ids,
)
from .damage_system import (
    DamageRequest,
    DamageResult,
    DamageSystem,
    InvalidDamageParticipantError,
)
from .effect_executor import EffectExecutor
from .effect_result import (
    ApplyStateEffectResult,
    DamageEffectResult,
    DeferredEffectResult,
    EffectExecutionResult,
    EffectExecutionStatus,
    RecoverEffectResult,
    RemoveStateEffectResult,
)
from .effects import (
    ApplyStateEffect,
    DamageEffect,
    Effect,
    EffectSourceRef,
    RecoverEffect,
    RemoveStateEffect,
)
from .battle_finalization_coordinator import (
    BattleFinalizationCoordinator,
    BattleTerminationRecord,
    FinalizationResult,
)
from .execution_right_system import (
    BattleTerminationState,
    DamageSettlementPermit,
    FinalizationProjectionPermit,
    FutureAdmissionGate,
    FutureAdmissionPermit,
    FutureBranchKind,
    LegacyActionDispatchAdapter,
    LegacyFinalizationBarrier,
    PermitStatus,
)
from .hit_resolution_system import (
    HitAllowedResult,
    HitPreventedResult,
    HitPreventionReason,
    HitResolutionResult,
    HitResolutionSystem,
)
from .normal_attack_system import NormalAttackResult, NormalAttackSystem
from .stage9_state_runtime import (
    Stage9StateRuntime,
    SuppressionReason,
    TauntLifecycleState,
)
from .target_resolution_system import (
    RedirectReason,
    TargetResolutionResult,
    TargetResolutionSystem,
)
from .official_state_catalog import (
    OFFICIAL_STATE_CATALOG,
    OfficialStateCategory,
    OfficialStateEntry,
    OfficialStateId,
    register_official_state_definitions,
)
from .operation_identity import (
    ActionId,
    ChainTraversalId,
    CleaveEffectId,
    CounterBatchEntryId,
    DamageInstanceId,
    DirectTroopLossId,
    FinalizationId,
    NormalAttackInstanceId,
    OperationIdAllocator,
    OperationLineage,
    PartitionTransactionId,
    ReactionBatchId,
    SourceType,
    TargetResolutionId,
)
from .reaction_permission_policy import ReactionPermissionPolicy
from .recovery_system import (
    RecoveryPreventionReason,
    RecoveryPreventedResult,
    RecoveryRequest,
    RecoveryResolvedResult,
    RecoveryResult,
    RecoverySystem,
)
from .rule_hooks import RoundStartHook, RuleHook, UnitActionStartHook
from .rule_hook_system import HookResolutionResult, RuleHookSystem
from .skill_definition import (
    ApplyStateSkillEffectSpec,
    DamageSkillEffectSpec,
    SkillDefinition,
    SkillEffectSpec,
    SkillTargetMode,
)
from .skill_resolver import (
    SkillResolutionResult,
    SkillResolutionStatus,
    SkillResolver,
)
from .skill_runtime import (
    LoadedSkillRef,
    LoadedSkillSet,
    SkillRuntime,
    SkillSlot,
)
from .stage7_state_params import (
    PeriodicDamageStateParams,
    PeriodicRecoveryStateParams,
)
from .stage8_state_params import (
    Stage8ModifierParams,
    Stage8PierceParams,
    Stage8ProbabilityParams,
)
from .stage9_integerization import (
    ExactRatio,
    exact_ratio_from_legacy_config_float,
    floor_product_int_ratio,
    round_half_up_divide_int,
    round_half_up_product_int_ratio,
)
from .stage9_state_params import (
    ChainStateParams,
    CleaveStateParams,
    ComboStateParams,
    CounterStateParams,
    DamageShareStateParams,
    DistributionStateParams,
    GuardStateParams,
    TauntStateParams,
)
from .stage9_trace import Stage9DiagnosticTraceSink, Stage9TraceEntry
from .state_definition import StateDefinition
from .state_instance import StateInstance
from .state_lifecycle_system import StateLifecycleSystem
from .state_registry import StateRegistry
from .state_runtime_params import (
    EmptyStateRuntimeParams,
    StateRuntimeParams,
)
from .strategy_damage_formula import StrategyBaseDamageFormula
from .target_system import TargetSystem
from .trigger_system import (
    ROUND_START_TRIGGER_TAG,
    UNIT_ACTION_START_TRIGGER_TAG,
    TriggerSystem,
)
from .troop_system import TroopChangeResult, TroopSystem
from .victory_system import VictorySystem
from .weapon_damage_formula import WeaponBaseDamageFormula
from .state_generation import (
    StateApplicationGenerationId,
    PersistentLifecycleWindow,
    StateGenerationAllocator,
    StateGenerationSnapshot,
)
from .stage10_state_params import (
    RecoveryModelKind,
    RecoveryPotencyContext,
    FrozenContinuousDamageBasis,
    ContinuousDamageStateParams,
    FirstAidStateParams,
    RecuperationStateParams,
)
from .skill_runtime_registry import (
    PersistentSourceSkillGateMode,
    PersistentSourceSkillGate,
    SkillRuntimeRegistry,
)
from .action_progress_tracker import ActionProgressTracker
from .rule_intent import (
    RuleIntentKind,
    RecoveryOpportunityKind,
    ExecutionRightDecisionKind,
    ExecutionRightReason,
    ExecutionRightDecision,
    RuleIntentExecutionDescriptor,
    RecoveryOpportunity,
    RecoveryOpportunityResult,
    AbortedRuleIntentResult,
    RuleIntent,
    RuleIntentResult,
)
from .execution_right_system import ExecutionRightSystem
from .defeat_cleanup_port import (
    DefeatCleanupPort,
    DefeatCleanupResult,
    DefeatRemovalReason,
)

__all__ = [
    "BattleContext",
    "BattleResult",
    "BattleEngine",
    "BattlePhase",
    "BattleEndReason",
    "DamageSourceType",
    "DamageType",
    "LineupPosition",
    "TroopType",
    "BattleEvent",
    "EventBus",
    "EventType",
    "RandomSystem",
    "UnitRuntime",
    "ActionOrderSystem",
    "ActionSystem",
    "AttributeSystem",
    "AttributeModifierProvider",
    "BattleSystems",
    "DamageDefensePolicy",
    "DamageFormulaContext",
    "DamageFormulaPolicyResult",
    "DamageFormulaPolicySystem",
    "AppliedDamageModifier",
    "DamageModifierContribution",
    "DamageModifierKind",
    "DamageModifierOperation",
    "DamageModifierPhase",
    "DamageModifierResult",
    "DamageModifierSystem",
    "DamagePipelineTrace",
    "StageEvaluationStatus",
    "DamageAllowedResult",
    "DamagePermissionResult",
    "DamagePreventedResult",
    "DamagePreventionReason",
    "DamagePreventionSystem",
    "DamageInstanceCoordinator",
    "DamageInstanceExecution",
    "PartitionExecutionStatus",
    "DamagePartitionCoordinator",
    "DamagePartitionKind",
    "DamagePartitionPlan",
    "NoPartitionPlan",
    "DamageShareTransactionPlan",
    "DistributionTransactionPlan",
    "DistributionRuntimeAuthority",
    "AttributedDirectTroopLoss",
    "DirectTroopLossRequest",
    "DirectTroopLossResolution",
    "DirectTroopLossResolver",
    "DamageResolutionResult",
    "DamageResolutionSystem",
    "DamageSettlementRequest",
    "SettlementOrigin",
    "DamageRuleFamily",
    "RuleContributionSource",
    "DamagePreventionRuleKind",
    "DamagePreventionContribution",
    "HitPreventionCategory",
    "HitRuleKind",
    "HitRuleContribution",
    "DamageFormulaPolicyContribution",
    "DamageRuleCollection",
    "DamageRuleProvider",
    "StateRuleAdapter",
    "StateRuleBinding",
    "StateDamageRuleProvider",
    "DEFAULT_STAGE8_STATE_RULE_BINDINGS",
    "default_stage8_official_binding_state_ids",
    "DamageRequest",
    "DamageResult",
    "DamageSystem",
    "InvalidDamageParticipantError",
    "EffectExecutor",
    "EffectExecutionStatus",
    "EffectExecutionResult",
    "DamageEffectResult",
    "ApplyStateEffectResult",
    "RemoveStateEffectResult",
    "RecoverEffectResult",
    "DeferredEffectResult",
    "Effect",
    "DamageEffect",
    "ApplyStateEffect",
    "RemoveStateEffect",
    "RecoverEffect",
    "EffectSourceRef",
    "HitAllowedResult",
    "HitPreventedResult",
    "HitPreventionReason",
    "HitResolutionResult",
    "HitResolutionSystem",
    "NormalAttackResult",
    "NormalAttackSystem",
    "OFFICIAL_STATE_CATALOG",
    "OfficialStateCategory",
    "OfficialStateEntry",
    "OfficialStateId",
    "register_official_state_definitions",
    "RecoveryRequest",
    "RecoveryPreventionReason",
    "RecoveryResolvedResult",
    "RecoveryPreventedResult",
    "RecoveryResult",
    "RecoverySystem",
    "RoundStartHook",
    "UnitActionStartHook",
    "RuleHook",
    "HookResolutionResult",
    "RuleHookSystem",
    "ApplyStateSkillEffectSpec",
    "DamageSkillEffectSpec",
    "SkillDefinition",
    "SkillEffectSpec",
    "SkillTargetMode",
    "SkillResolutionResult",
    "SkillResolutionStatus",
    "SkillResolver",
    "SkillRuntime",
    "SkillSlot",
    "LoadedSkillRef",
    "LoadedSkillSet",
    "PeriodicDamageStateParams",
    "PeriodicRecoveryStateParams",
    "Stage8ProbabilityParams",
    "Stage8ModifierParams",
    "Stage8PierceParams",
    "StateDefinition",
    "StateInstance",
    "StateLifecycleSystem",
    "StateRegistry",
    "StateRuntimeParams",
    "EmptyStateRuntimeParams",
    "StrategyBaseDamageFormula",
    "TargetSystem",
    "ROUND_START_TRIGGER_TAG",
    "UNIT_ACTION_START_TRIGGER_TAG",
    "TriggerSystem",
    "TroopChangeResult",
    "TroopSystem",
    "VictorySystem",
    "WeaponBaseDamageFormula",
    # Stage9 Phase 9.1 Foundational Contracts
    "ActionId",
    "NormalAttackInstanceId",
    "TargetResolutionId",
    "DamageInstanceId",
    "PartitionTransactionId",
    "ReactionBatchId",
    "CounterBatchEntryId",
    "CleaveEffectId",
    "ChainTraversalId",
    "DirectTroopLossId",
    "FinalizationId",
    "SourceType",
    "OperationLineage",
    "OperationIdAllocator",
    "ExactRatio",
    "exact_ratio_from_legacy_config_float",
    "floor_product_int_ratio",
    "round_half_up_product_int_ratio",
    "round_half_up_divide_int",
    "CleaveStateParams",
    "ChainStateParams",
    "DamageShareStateParams",
    "DistributionStateParams",
    "TauntStateParams",
    "GuardStateParams",
    "CounterStateParams",
    "ComboStateParams",
    "ReactionPermissionPolicy",
    "FutureBranchKind",
    "BattleTerminationState",
    "LegacyFinalizationBarrier",
    "PermitStatus",
    "FutureAdmissionPermit",
    "DamageSettlementPermit",
    "FinalizationProjectionPermit",
    "Stage9TraceEntry",
    "Stage9DiagnosticTraceSink",
    # Stage9 Phase 9.2 Finalization & Future Admission
    "BattleFinalizationCoordinator",
    "BattleTerminationRecord",
    "FinalizationResult",
    "FutureAdmissionGate",
    "LegacyActionDispatchAdapter",
    # Stage9 Phase 9.3 Target Resolution & State Runtime
    "Stage9StateRuntime",
    "TargetResolutionSystem",
    "TargetResolutionResult",
    "RedirectReason",
    "TauntLifecycleState",
    "SuppressionReason",
    # Stage9 Phase 9.5 Partition / Direct Troop Loss
    "DamagePartitionCoordinator",
    "DamagePartitionKind",
    "DamagePartitionPlan",
    "NoPartitionPlan",
    "DamageShareTransactionPlan",
    "DistributionTransactionPlan",
    "DistributionRuntimeAuthority",
    "AttributedDirectTroopLoss",
    "DirectTroopLossRequest",
    "DirectTroopLossResolution",
    "DirectTroopLossResolver",
    "DamageInstanceExecution",
    "PartitionExecutionStatus",
    # Stage10 Phase 1 Primitives
    "StateApplicationGenerationId",
    "PersistentLifecycleWindow",
    "StateGenerationAllocator",
    "StateGenerationSnapshot",
    "RecoveryModelKind",
    "RecoveryPotencyContext",
    "FrozenContinuousDamageBasis",
    "ContinuousDamageStateParams",
    "FirstAidStateParams",
    "RecuperationStateParams",
    "PersistentSourceSkillGateMode",
    "PersistentSourceSkillGate",
    "SkillRuntimeRegistry",
    "ActionProgressTracker",
    "RuleIntentKind",
    "RecoveryOpportunityKind",
    "ExecutionRightDecisionKind",
    "ExecutionRightReason",
    "ExecutionRightDecision",
    "ExecutionRightSystem",
    "RuleIntentExecutionDescriptor",
    "RecoveryOpportunity",
    "RecoveryOpportunityResult",
    "AbortedRuleIntentResult",
    "RuleIntent",
    "RuleIntentResult",
    "DefeatCleanupPort",
    "DefeatCleanupResult",
    "DefeatRemovalReason",
]
