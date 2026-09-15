# Stage10 Build Prompt
# Frozen Architecture → Implementation Execution Plan

> Target Project: 三国志战略版战斗模拟器 V2  
> Target Repository: `lxy2005051020-commits/sgs-v2-battle-system`  
> Target Branch: `stage10-persistent-state-research`  
> Governance Authority: Stage10 Design Freeze (`stages/stage10/STAGE10_DESIGN_FREEZE.md`)  
> Authority Repository: `lxy2005051020-commits/sgs-state-mechanics-research` @ `a9a05ceffa2a9489cdc1e0a000a4c27bac81a5fe`  
> Document Type: Formal Implementation Build Prompt & Phase Execution Plan  
> Status: `BUILD PROMPT AUTHORIZED / PRODUCTION IMPLEMENTATION READY FOR NEXT ROUND`  
> Directive to Builder: **DESIGN IS NOT A SUGGESTION. EXECUTE FROZEN ARCHITECTURE WITHOUT DRIFT.**  

---

## 0. Frozen Input Metadata & Baseline Verification

The builder must strictly verify the baseline repository state before beginning implementation:

```text
Freeze Commit:                    e4e5974f328f592411c34e02d38c358b7d19dd25
Implementation Base HEAD:         e4e5974f328f592411c34e02d38c358b7d19dd25
Battle Repository:                lxy2005051020-commits/sgs-v2-battle-system
Battle Branch:                    stage10-persistent-state-research
Gameplay Authority Repository:    lxy2005051020-commits/sgs-state-mechanics-research
Gameplay Authority Branch:        main
Gameplay Authority HEAD:          a9a05ceffa2a9489cdc1e0a000a4c27bac81a5fe
Baseline Test Suite:              pytest -q → 753 passed
Baseline Demo:                    python demo.py → PASS
Working Tree:                     CLEAN (Zero uncommitted changes)
```

### 0.1 Immutable Audited Blob Integrity Ledger

The following exact Git blob SHAs were verified during freeze audit and are permanently locked. Any deviation indicates contract drift:

| Document / Contract | Repository Relative Path | Required Blob SHA | Status |
|---|---|---|---|
| **Stage10 Architecture Design (Audited)** | `stages/stage10/STAGE10.md` | `b87dc4c40abe13373e25cf4028ea27a08b413076` | FROZEN |
| **Stage10 Architecture Design (Post-Freeze)** | `stages/stage10/STAGE10.md` | `50fe8c151968b74c4292cf14a84aa25382610c21` | FROZEN (Metadata only) |
| **Stage7 Compatibility Addendum** | `stages/stage7/STAGE7_STAGE10_COMPATIBILITY_ADDENDUM.md` | `64cdb7d86c8bda5b9123b49afcb924db7e1fd485` | FROZEN |
| **Stage8 Compatibility Addendum** | `stages/stage8/STAGE8_STAGE10_COMPATIBILITY_ADDENDUM.md` | `4c1e22eda97bdc0ef74ab6175a28672845771ddc` | FROZEN |
| **Stage9 Compatibility Addendum** | `stages/stage9/STAGE9_STAGE10_COMPATIBILITY_ADDENDUM.md` | `737b058cefd08a1d0a08526436098a3455a8168f` | FROZEN |
| **Final Freeze-Gate Audit** | `stages/stage10/STAGE10_FINAL_DESIGN_FREEZE_GATE_AUDIT.md` | `e32bef16453bc24ae7117e1e7d89ef8c95d4f0ad` | FROZEN |
| **Recovery RNG Edge Research** | Authority: `stage10/RECOVERY_RNG_EDGE_RESEARCH.md` | `d669659243db6d2060166121d92265ff507598e0` | PINNED |
| **First Aid Zero-Loss Research** | Authority: `stage10/FIRST_AID_ZERO_LOSS_ELIGIBILITY_RESEARCH.md` | `11a36e5e60f875f3c820a5d1d81541ea2dabd24a` | PINNED |
| **Targeted Research Promotion** | Authority: `stage10/STAGE10_TARGETED_RESEARCH_AUTHORITY_PROMOTION.md` | `99cb60ce3324fb547af35ef1e0490b603ad20eb0` | PINNED |
| **First Aid Mechanism Contract** | Authority: `states/persistent/first_aid/MECHANISM_CONTRACT.md` | `2dc32ea70941660a0ac580601febfdd538822d36` | PINNED |

---

## 1. Mission

The mission of the Stage10 implementation engineer is to translate the frozen Stage10 architecture into production-grade Python code within `sgs_v2` and build an exhaustive verification test suite in `tests`.

**Primary Goal**:
Integrate full persistent state runtime execution for exactly the eight authorized persistent states:
1. `690072 BURN` (灼烧) - Continuous elemental damage
2. `690073 FLOOD` (水攻) - Continuous elemental damage
3. `690074 POISON` (中毒) - Continuous elemental damage
4. `690075 ROUT` (溃逃) - Continuous physical damage
5. `690076 SANDSTORM` (沙暴) - Continuous elemental damage
6. `690077 REBELLION` (叛逃) - Continuous true/direct damage (defense-bypass)
7. `690078 FIRST_AID` (急救) - After-damage reaction recovery
8. `690079 RECUPERATION` (休整) - Action-start periodic recovery

**Strict Boundary**:
- Do **NOT** invent architectural patterns or alter existing Stage7/8/9 frozen contracts.
- Do **NOT** implement deferred features (full evasion, full barrier, universal dispel, unresearched crits, Stage 11+).
- Preserve all 753 existing tests with 100% green pass rate at every phase gate.

---

## 2. Authority Precedence Stack

In the event of any apparent conflict, discrepancy, or ambiguity encountered during coding, the following precedence stack is absolute:

```text
       Gameplay Authority (sgs-state-mechanics-research @ a9a05cef)
                           ↓
          Original Frozen Stage Contracts (Stage 7 / 8 / 9)
                           ↓
        Explicit Stage10 Compatibility Addenda (Stage 7 / 8 / 9)
                           ↓
             Stage10 Frozen Architecture Design (STAGE10.md)
                           ↓
                   Production Implementation
```

**Rule of Conflict**:
If production implementation code conflicts with any upper layer, **the implementation code is wrong**. The developer is strictly prohibited from "re-interpreting" or silently updating documentation.

---

## 3. Non-Negotiable Frozen Architectural Contracts

The builder must implement the following 27 frozen contracts exactly as designed:

1. **Persistent Lifecycle Model**: PRE_BATTLE domain separation; combat round indexing starts at 1. Finite duration $N \ge 1$ gives $[R, R+N-1]$ if applied before ActionStart, $[R+1, R+N]$ if after ActionStart. Suppressed opportunity still consumes the round window; no catch-up.
2. **ActionProgressTracker Contract**: `mark_action_start(owner_id, round)` tracks ActionStart timing. Exactly one persistent ActionStart opportunity per owner per round. Stun/amnesia suppresses execution but window is consumed.
3. **Physical Expiration Semantics**: Synchronous check at action window completion (`current_round >= state.last_eligible_round`). State removed deterministically.
4. **StateApplicationGenerationId**: Strong immutable identity allocated on initial application and on every refresh. Container physical `instance_id` is retained on refresh; generation snapshot is renewed.
5. **Snapshot vs JIT Separation**: Potency, formula policy, locked modifiers/crits, attributes locked in `StateGenerationSnapshot`. Target survival, healing ban, missing troops, and skill gate are queried JIT at execution time.
6. **ExecutionRight Sibling Decision Model**:
   - `RuleIntent` is the common base for `Effect` and `RecoveryOpportunity`.
   - `RuleIntentExecutionDescriptor` carries typed context without duck typing or attribute probing.
   - Decisions: `ALLOW`, `REJECT_CURRENT` (target dead; batch continues for other targets), `ABORT_OWNER_STATE_REMAINDER` (owner dead; remaining intents for that owner discarded; other owners continue), `ABORT_HOOK` (battle finalized; halt batch).
7. **RuleHookSystem Dispatch Ownership**: RuleHookSystem iterates intents, queries `ExecutionRightSystem.evaluate_rule_intent(descriptor, context)`, enforces abort scopes, and delegates execution to pure routers.
8. **EffectExecutor Pure Routing**: Pure router for `Effect` variants. Zero permission logic, zero defeat arbitration.
9. **Authoritative DefeatCleanupPort**: Single synchronous port `commit_defeat(context, unit_id, defeat_source_ref)` invoked once on alive $\to$ defeated edge across all destructive routes (standard damage, DOT, counter, cleave, share direct loss, distribution direct loss, chain feedback). Removes states deterministically via `StateLifecycleSystem.clear_owner_on_defeat`.
10. **Battle Finalization & Teardown**: Admitted work drains upon `VICTORY_LATCHED`. Once finalized, `StateLifecycleSystem.clear_all_on_battle_end(context)` cleans all states across all units (winners and losers). Emits `STATE_CLEARED_ON_BATTLE_END`. Zero state leakage between battles.
11. **SkillRuntime Registry**: Battle-scoped authoritative registry on `BattleContext.skill_runtimes` keyed by `(owner_id, SkillSlot)`. Source death does NOT remove runtime or disable skill.
12. **PersistentSourceSkillGate**: Typed gate checking `ALWAYS_ACTIVE`, `QUERY_SKILL_RUNTIME` (`lookup.enabled`), or `EXTERNAL_LIFECYCLE`.
13. **FROZEN_APPLICATION Damage Lane**: Replays locked application-time formula inputs, frozen attributes, locked modifiers, and locked crit through Stage8 `DamageSystem`. Base formula tick RNG follows Stage8 formulas. Participant validation permits dead historical sources on this authorized lane.
14. **REBELLION Continuous Damage**: Route chosen at application/refresh based on ATK vs INT; route and ignore-defense policy locked in generation snapshot. Settled through `DamageDefensePolicy.IGNORE_DEFENSE`, NOT DirectTroopLoss.
15. **Source-Dead Continuous Damage**: When source dies, state persists on living target. Executes on schedule using historical snapshot.
16. **RecoveryOpportunity Hierarchy & Engine**: Unified `RecoveryOpportunitySystem` executing both `FIRST_AID_AFTER_DAMAGE` and `RECUPERATION_ACTION_START`.
17. **RecoveryOpportunityKind**: Strongly-typed enum discriminating aftermath reaction from turn-based recovery.
18. **Bifurcated Gate 2 Admission**:
    - `FIRST_AID_AFTER_DAMAGE`: Gate 2 is **REQUIRED** (`DamageAftermathFact` present, `RESOLVED_HIT`, `ReactionPermissionPolicy.can_trigger_recovery(source_type) == True`).
    - `RECUPERATION_ACTION_START`: Gate 2 is **NOT_APPLICABLE** (`aftermath_fact=None`; `ReactionPermissionPolicy` is never queried).
19. **FIRST_AID Zero-Loss Eligibility**: Weakness-zero and barrier-zero resolved hits on living targets are eligible for FIRST_AID. Evasion/miss is ineligible. Fatal hits are ineligible. ActualTargetTroopLoss is NOT a gate.
20. **Full-Troop Recovery Semantics**: If target has full troops (`recoverable_gap == 0`), recovery opportunity is NOT skipped. RNG draw is executed; `RecoverySystem` resolves actual recovery to 0.
21. **Simulator Recovery RNG Determinism Policy**: Exactly one `RandomSystem.chance(probability)` draw per admitted opportunity. Probability 0.0 draws once (evaluates `False`). Probability 1.0 draws once (evaluates `True`). Native `RandomSystem.chance` implementation unmodified.
22. **Stage9 DamageAftermathPort**: Unified aftermath intake mounted at reconciled frozen checkpoints across all Stage9 pipelines:
    - *NoPartition*: target settlement $\to$ target aftermath (if alive) $\to$ callbacks.
    - *Share*: target settlement $\to$ sharer direct loss $\to$ target aftermath (if alive) $\to$ callbacks.
    - *Distribution*: participant direct loss drain $\to$ target settlement $\to$ target aftermath (if alive) $\to$ callbacks.
    - *Cleave*: target settlement $\to$ sharer direct loss $\to$ target aftermath (FIRST_AID) $\to$ attacker recovery $\to$ callbacks.
    - *Counter*: target settlement $\to$ target aftermath (if alive) $\to$ callbacks.
    - *Chain*: restricted settlement $\to$ aftermath strictly INELIGIBLE.
23. **DirectTroopLoss Inviolability**: `SHARE_DIRECT_LOSS` and `DISTRIBUTION_DIRECT_LOSS` never generate `DamageAftermathFact` and never trigger FIRST_AID.
24. **ReactionPermissionPolicy Authority**: `ReactionPermissionPolicy.can_trigger_recovery` is the sole arbiter of recovery eligibility. `SourceType.ASSAULT` is added to the authorized list.
25. **End-to-End Generation Provenance**: `StateApplicationGenerationId` propagates through `StateInstance`, `StateGenerationSnapshot`, `RuleIntent`, `DamageRequest`, `DamageResult`, `RecoveryRequest`, `RecoveryResult`, `DamageAftermathFact`, `DamagePipelineTrace`, and all observation events.
26. **Acyclic Static Architecture**: Composition root and system interactions adhere strictly to a directed acyclic graph (DAG). No global singletons, service locators, or untyped dependency bags.
27. **Hardening Obligations (S10-FG-H01 & S10-FG-H02)**: Precondition validation on descriptors; strict isolation of RECUPERATION from aftermath facts.

---

## 4. Current Runtime Baseline

The production code structure in `sgs_v2` and tests in `tests` as of freeze commit `e4e5974`:

```text
sgs_v2/
└── battle_core/
    ├── __init__.py                     # Public API exports
    ├── context.py                      # BattleContext, BattleResult
    ├── battle_systems.py               # Composition root (wiring BattleSystems)
    ├── unit.py                         # UnitRuntime
    ├── state_instance.py               # StateInstance
    ├── state_registry.py               # StateRegistry
    ├── state_lifecycle_system.py       # StateLifecycleSystem
    ├── official_state_catalog.py       # OfficialStateId, OFFICIAL_STATE_CATALOG
    ├── state_runtime_params.py         # StateRuntimeParams base
    ├── stage7_state_params.py          # Legacy synthetic stage7 params
    ├── stage8_state_params.py          # Legacy stage8 modifier params
    ├── stage9_state_params.py          # Functional state params (Cleave, Share, etc.)
    ├── trigger_system.py               # TriggerSystem (rule hook collection)
    ├── rule_hooks.py                   # RuleHook, UnitActionStartHook, RoundStartHook
    ├── rule_hook_system.py             # RuleHookSystem (hook dispatch)
    ├── effects.py                      # DamageEffect, ApplyStateEffect, RecoverEffect, etc.
    ├── effect_executor.py              # EffectExecutor (typed effect routing)
    ├── effect_result.py                # EffectExecutionResult hierarchy
    ├── execution_right_system.py       # FutureAdmissionGate, ActionScope, Permits
    ├── damage_system.py                # DamageSystem, DamageRequest, DamageResult
    ├── damage_rule_models.py           # DamageRule models and contributions
    ├── damage_resolution_system.py     # DamageResolutionSystem (destructive settlement)
    ├── damage_instance_coordinator.py  # DamageInstanceCoordinator (Stage9 coordinator)
    ├── damage_partition_system.py     # DamagePartitionCoordinator (Share/Distribution)
    ├── direct_troop_loss_system.py     # DirectTroopLossResolver
    ├── cleave_derived_damage_system.py # CleaveDerivedDamageResolver
    ├── counter_system.py               # CounterSystem
    ├── chain_system.py                 # ChainSystem
    ├── normal_attack_system.py         # NormalAttackSystem
    ├── action_system.py                # ActionSystem
    ├── recovery_system.py              # RecoverySystem, RecoveryRequest, RecoveryResult
    ├── troop_system.py                 # TroopSystem (troop mutation)
    ├── random_system.py                # RandomSystem (chance, uniform, etc.)
    ├── battle_finalization_coordinator.py # BattleFinalizationCoordinator
    ├── operation_identity.py           # ActionId, DamageInstanceId, SourceType, Lineage
    ├── events.py                       # EventBus, EventType
    └── damage_pipeline_trace.py        # DamagePipelineTrace
```

---

## 5. Expected File Map

The implementation must create, modify, or strictly leave untouched the following files:

### 5.1 New Production Files to Create (`CREATE`)

| File Path | Primary Responsibilities | Frozen Architecture Clause | Implementation Phase |
|---|---|---|---|
| `sgs_v2/battle_core/state_generation.py` | `StateApplicationGenerationId`, `StateGenerationSnapshot`, `StateGenerationAllocator`, `PersistentLifecycleWindow` | `STAGE10.md §7, §13` | Phase 1 |
| `sgs_v2/battle_core/stage10_state_params.py` | `ContinuousDamageStateParams`, `FirstAidStateParams`, `RecuperationStateParams`, `FrozenContinuousDamageBasis`, `RecoveryPotencyContext`, `RecoveryModelKind` | `STAGE10.md §29` | Phase 1 |
| `sgs_v2/battle_core/action_progress_tracker.py` | `ActionProgressTracker` (ActionStart tracking per owner/round) | `STAGE10.md §9` | Phase 2 |
| `sgs_v2/battle_core/skill_runtime_registry.py` | `SkillRuntimeRegistry`, `PersistentSourceSkillGate`, `PersistentSourceSkillGateMode` | `STAGE10.md §11, §12` | Phase 1 |
| `sgs_v2/battle_core/rule_intent.py` | `RuleIntentKind`, `RuleIntentExecutionDescriptor`, `RecoveryOpportunity`, `RecoveryOpportunityKind`, `RecoveryOpportunityResult`, `AbortedRuleIntentResult`, `RuleIntentResult`, `RuleIntent` union | `STAGE10.md §4.1, §20` | Phase 1 & 3 |
| `sgs_v2/battle_core/defeat_cleanup_port.py` | `DefeatCleanupPort`, `DefeatCleanupResult`, `DefeatRemovalReason` | `STAGE10.md §10` | Phase 2 |
| `sgs_v2/battle_core/recovery_opportunity_system.py` | `RecoveryOpportunitySystem`, admission gates 1-5, chance draw, RecoveryRequest dispatch | `STAGE10.md §18, §22` | Phase 5 |
| `sgs_v2/battle_core/damage_aftermath_port.py` | `DamageAftermathPort`, `DamageAftermathFact`, `DamageHitTopology` | `STAGE10.md §15, §23` | Phase 6 |

### 5.2 Existing Production Files to Modify (`MODIFY`)

| File Path | Required Changes | Frozen Architecture Clause | Implementation Phase |
|---|---|---|---|
| `sgs_v2/battle_core/context.py` | Add `skill_runtimes: SkillRuntimeRegistry` and `action_progress: ActionProgressTracker` to `BattleContext`. | `STAGE10.md §9, §11` | Phase 1 & 2 |
| `sgs_v2/battle_core/state_instance.py` | Add `current_generation_id`, lifecycle window access, and generation snapshot creation helper. | `STAGE10.md §13` | Phase 1 |
| `sgs_v2/battle_core/state_lifecycle_system.py` | PRE_BATTLE domain separation, generation allocation, refresh-and-overwrite transaction, physical expiration check at window close, `clear_owner_on_defeat`, and `clear_all_on_battle_end(context)`. | `STAGE10.md §7, §8, §10, §14` | Phase 2 & 7 |
| `sgs_v2/battle_core/execution_right_system.py` | Add `evaluate_rule_intent(descriptor, context) -> ExecutionRightDecision`, `ExecutionRightDecisionKind` (`ALLOW`, `REJECT_CURRENT`, `ABORT_OWNER_STATE_REMAINDER`, `ABORT_HOOK`), `ExecutionRightReason` (`TARGET_DEFEATED`, `OWNER_DEFEATED`, etc.). Strictly read typed descriptor (no duck-typing). | `STAGE10.md §4.1, §4.2` | Phase 3 |
| `sgs_v2/battle_core/rule_hook_system.py` | Support `RuleIntent` batch iteration; invoke `evaluate_rule_intent` with precondition validation (H01); enforce `REJECT_CURRENT` (batch continues), `ABORT_OWNER_STATE_REMAINDER` (owner tail discarded), and `ABORT_HOOK`; route admitted intents to `EffectExecutor` or `RecoveryOpportunitySystem`; construct `HookResolutionResult`. | `STAGE10.md §4.1, §4.2, §20` | Phase 3 |
| `sgs_v2/battle_core/trigger_system.py` | Update `collect` to emit `RuleIntent`s carrying `RuleIntentExecutionDescriptor`; add `collect_after_damage` for `FIRST_AID_AFTER_DAMAGE` opportunities. | `STAGE10.md §4.1, §20, §21` | Phase 3 & 6 |
| `sgs_v2/battle_core/effects.py` | Ensure `Effect` variants carry or associate with `RuleIntentExecutionDescriptor`; maintain backward compatibility. | `STAGE10.md §4.1, §20` | Phase 1 & 3 |
| `sgs_v2/battle_core/effect_result.py` | Add sibling result representations (`AbortedRuleIntentResult`, `RecoveryOpportunityResult`) for `HookResolutionResult`. | `STAGE10.md §20` | Phase 3 |
| `sgs_v2/battle_core/damage_system.py` | Add `calculation_basis` (`LIVE_RUNTIME` vs `FROZEN_APPLICATION`), `frozen_basis: FrozenContinuousDamageBasis | None`, and `source_generation_id: StateApplicationGenerationId | None` to `DamageRequest` and `DamageResult`; bypass live source validation on authorized frozen lane; replay frozen inputs; preserve LIVE path unmodified. | `STAGE8_ADDENDUM §3`, `STAGE10.md §5` | Phase 4 |
| `sgs_v2/battle_core/damage_resolution_system.py` | Synchronously call `DefeatCleanupPort.commit_defeat` on alive $\to$ defeated edge; propagate `source_generation_id` through results and events. | `STAGE10.md §10, §13.2` | Phase 6 |
| `sgs_v2/battle_core/direct_troop_loss_system.py` | Synchronously call `DefeatCleanupPort.commit_defeat` on alive $\to$ defeated edge (for Share and Distribution). | `STAGE10.md §10` | Phase 6 |
| `sgs_v2/battle_core/reaction_permission_policy.py` | Add `SourceType.ASSAULT` to `can_trigger_recovery`. Maintain strict blocking for `CHAIN_TRUE_FEEDBACK`, `SHARE_DIRECT_LOSS`, and `DISTRIBUTION_DIRECT_LOSS`. | `STAGE9_ADDENDUM §4.3`, `STAGE10.md §33` | Phase 6 |
| `sgs_v2/battle_core/recovery_system.py` | Add `source_generation_id` to `RecoveryRequest`, `RecoveryResolvedResult`, and `RecoveryPreventedResult`. | `STAGE10.md §13.2` | Phase 5 |
| `sgs_v2/battle_core/damage_instance_coordinator.py` | Mount `DamageAftermathPort.commit_aftermath` at reconciled checkpoints (NoPartition, Share after direct loss, Distribution after target settlement); integrate `DefeatCleanupPort`. | `STAGE9_ADDENDUM §4.2`, `STAGE10.md §24` | Phase 6 |
| `sgs_v2/battle_core/cleave_derived_damage_system.py` | Mount `DamageAftermathPort.commit_aftermath` for Cleave FIRST_AID; remove obsolete `cleave_first_aid` callback injection; invoke `DefeatCleanupPort`. | `STAGE9_ADDENDUM §4.1`, `STAGE10.md §24.4` | Phase 6 |
| `sgs_v2/battle_core/counter_system.py` | Invoke `DamageAftermathPort` on counter settlement; invoke `DefeatCleanupPort`. | `STAGE9_ADDENDUM §4.2`, `STAGE10.md §24` | Phase 6 |
| `sgs_v2/battle_core/battle_systems.py` | Wire Composition Root V2: inject `DefeatCleanupPort`, `RecoveryOpportunitySystem`, `DamageAftermathPort`, `ActionProgressTracker`, `SkillRuntimeRegistry`. | `STAGE10.md §32` | Phase 6 |
| `sgs_v2/battle_core/events.py` | Add `STATE_CLEARED_ON_BATTLE_END`; ensure `source_generation_id` is supported across `STATE_APPLIED`, `STATE_REFRESHED`, `STATE_EXPIRED`, `STATE_REMOVED`, `DAMAGE_RESOLVED`, `RECOVERY_RESOLVED`. | `STAGE10.md §8, §13.2` | Phase 7 |
| `sgs_v2/battle_core/damage_pipeline_trace.py` | Support `source_generation_id` and frozen continuous damage basis representation in execution trace. | `STAGE10.md §6, §13.2` | Phase 4 |
| `sgs_v2/battle_core/official_state_catalog.py` | Map the 8 official continuous states to official Stage10 params. | `STAGE10.md §5, §29` | Phase 4 & 5 |
| `sgs_v2/battle_core/__init__.py` | Re-export new public Stage10 classes and enums. | Contract export | Phase 8 |

### 5.3 Strictly Forbidden to Modify (`DO NOT TOUCH`)

| File Path | Invariant Rationale |
|---|---|
| `sgs_v2/battle_core/random_system.py` | **Zero Stage 2 reopen**. Native `random.chance(p)` already provides deterministic one-draw semantic ($p=0 \to \text{draw}, p=1 \to \text{draw}$). Zero code modification allowed. |
| `sgs_v2/battle_core/weapon_damage_formula.py` | Mathematical formulas and low-floor RNG are strictly frozen Stage8 contracts. |
| `sgs_v2/battle_core/strategy_damage_formula.py` | Mathematical formulas and low-floor RNG are strictly frozen Stage8 contracts. |
| `sgs_v2/battle_core/damage_partition_system.py` | Share and Distribution mathematical partitioning is strictly frozen Stage9 contract. |
| `sgs_v2/battle_core/chain_system.py` | Restricted feedback settlement is strictly frozen Stage9 contract (zero recovery permission). |
| `sgs_v2/battle_core/action_order_system.py` | Speed-based ordering and tie-breaking remain frozen. |
| `sgs_v2/battle_core/victory_system.py` | Win/loss condition predicates remain frozen. |
| `sgs_v2/battle_core/stage7_state_params.py` | Retained untouched for test-only legacy synthetic backward compatibility. |
| `sgs_v2/battle_core/stage8_state_params.py` | Retained untouched for test-only legacy synthetic backward compatibility. |
| `sgs_v2/battle_core/stage9_state_params.py` | Retained untouched for Stage9 functional state compatibility. |

---

## 6. Production Ownership Map

To prevent architectural overlap or dual authority, each responsibility has exactly one owner:

| Responsibility | Authoritative Production Owner | Prohibited Collaborators / Antipatterns |
|---|---|---|
| **State Lifecycle & Physical Containers** | `StateLifecycleSystem` | No direct dictionary mutations on `context.states`; no state creation in TriggerSystem |
| **Generation Identity Allocation** | `StateGenerationAllocator` | No ad-hoc string formatting or local counters |
| **Action Start Progress Tracking** | `ActionProgressTracker` | No engine ad-hoc flags; no tracking inside NormalAttackSystem |
| **Execution Right Decision** | `ExecutionRightSystem` | Zero duck-typing; zero troop mutations; zero state removals |
| **Intent Hook Dispatch & Abort Scopes** | `RuleHookSystem` | No independent gameplay alive checks; must call `evaluate_rule_intent` |
| **Typed Effect Execution** | `EffectExecutor` | Pure router; zero gameplay permission logic; zero defeat arbitration |
| **Authoritative Defeat Cleanup** | `DefeatCleanupPort` | No EventBus listener handling cleanup; exactly once per death edge |
| **Recovery Admission & Probability** | `RecoveryOpportunitySystem` | Single engine; no split `FirstAidSystem` vs `RecuperationSystem`; zero RNG in TriggerSystem |
| **Recovery Troop Mutation & Healing Ban** | `RecoverySystem` & `TroopSystem` | `RecoveryOpportunitySystem` does not directly mutate troops or clamp max hp |
| **Continuous Theoretical Damage** | `DamageSystem` | No second damage formula; FROZEN_APPLICATION must route through `DamageSystem` |
| **Reaction Recovery Permission** | `ReactionPermissionPolicy.can_trigger_recovery` | Sole permission arbiter; no secondary white-lists in Cleave or Coordinator |
| **Damage Aftermath Ingress** | `DamageAftermathPort` | Shared port called across NoPartition, Share, Distribution, Cleave, Counter |
| **Battle Teardown Cleanup** | `StateLifecycleSystem.clear_all_on_battle_end` | Finalization triggers; lifecycle executes; EventBus purely observes |
| **Skill Runtime Lookup** | `SkillRuntimeRegistry` on `BattleContext` | Keyed by `(owner_id, SkillSlot)`; source death does NOT remove or disable |

---

## 7. Phase 0 — Baseline & Freeze Integrity Gate

**Goal**: Establish verified baseline state before modifying any production or test code.

**Prerequisites**:
- Working tree clean.
- HEAD matches Freeze Commit `e4e5974f328f592411c34e02d38c358b7d19dd25`.
- Gameplay Authority matches `a9a05ceffa2a9489cdc1e0a000a4c27bac81a5fe`.

**Execution Steps**:
1. Run Git plumbing integrity check:
   ```powershell
   git status
   git rev-parse HEAD
   git ls-tree HEAD stages/stage10/STAGE10.md stages/stage7/STAGE7_STAGE10_COMPATIBILITY_ADDENDUM.md stages/stage8/STAGE8_STAGE10_COMPATIBILITY_ADDENDUM.md stages/stage9/STAGE9_STAGE10_COMPATIBILITY_ADDENDUM.md stages/stage10/STAGE10_FINAL_DESIGN_FREEZE_GATE_AUDIT.md
   ```
2. Verify existing test suite baseline:
   ```powershell
   python -m pytest -q
   # Must report exactly: 753 passed
   ```
3. Verify demo baseline:
   ```powershell
   python demo.py
   # Must complete cleanly to battle end
   ```

**Phase 0 Exit Gate**:
- Git status clean.
- All blob hashes match ledger §0.1.
- 753/753 tests pass.
- Demo passes.

---

## 8. Phase 1 — Core Typed State Runtime Foundation

**Goal**: Implement the foundational immutable data structures, generation identifiers, parameter classes, and registry contracts without modifying gameplay execution.

**Production Files to Create**:
- `sgs_v2/battle_core/state_generation.py`:
  - `StateApplicationGenerationId` (frozen dataclass/string wrapper)
  - `StateGenerationSnapshot` (frozen dataclass capturing application-time facts)
  - `StateGenerationAllocator` (deterministic sequence generator)
  - `PersistentLifecycleWindow` (application_phase, application_round, first_eligible_round, last_eligible_round)
- `sgs_v2/battle_core/stage10_state_params.py`:
  - `ContinuousDamageStateParams`
  - `FirstAidStateParams`
  - `RecuperationStateParams`
  - `FrozenContinuousDamageBasis`
  - `RecoveryPotencyContext`
  - `RecoveryModelKind` (`TREATMENT_AMOUNT`, `TRIGGER_DAMAGE_RATIO`)
- `sgs_v2/battle_core/skill_runtime_registry.py`:
  - `SkillRuntimeRegistry` (`lookup(owner_id, slot, expected_skill_id)`)
  - `PersistentSourceSkillGate` & `PersistentSourceSkillGateMode` (`ALWAYS_ACTIVE`, `QUERY_SKILL_RUNTIME`, `EXTERNAL_LIFECYCLE`)
- `sgs_v2/battle_core/rule_intent.py`:
  - `RuleIntentKind` (`EFFECT`, `RECOVERY_OPPORTUNITY`)
  - `RuleIntentExecutionDescriptor` (frozen dataclass, §4.1.1)

**Production Files to Modify**:
- `sgs_v2/battle_core/state_instance.py`: Add `current_generation_id` field (defaulting to a valid generation or allocated on creation).
- `sgs_v2/battle_core/context.py`: Add `skill_runtimes: SkillRuntimeRegistry = field(default_factory=SkillRuntimeRegistry)`.

**Tests to Create**:
- `tests/test_stage10_phase1_primitives.py`:
  - Verify deterministic allocation of `StateApplicationGenerationId`.
  - Verify immutability and numeric validation of all Stage10 params.
  - Verify `SkillRuntimeRegistry` registration, duplicate slot rejection, and lookup validation.
  - Verify `RuleIntentExecutionDescriptor` field validation.

**Phase 1 Exit Gate**:
- All 753 baseline tests pass unchanged.
- All Phase 1 primitive tests pass.
- Zero gameplay control-flow changes introduced.

---

## 9. Phase 2 — Lifecycle, Generation & ActionProgressTracker

**Goal**: Implement persistent state lifecycle window arithmetic, same-name refresh generation transitions, ActionProgressTracker, and defeat cleanup boundary.

**Production Files to Create**:
- `sgs_v2/battle_core/action_progress_tracker.py`:
  - `ActionProgressTracker`: `mark_action_start(owner_id, round)`, `has_acted_in_round(owner_id, round)`, `current_acting_unit`.
- `sgs_v2/battle_core/defeat_cleanup_port.py`:
  - `DefeatCleanupPort`: `commit_defeat(context, defeated_unit_id, defeat_source_ref) -> DefeatCleanupResult`.

**Production Files to Modify**:
- `sgs_v2/battle_core/context.py`: Add `action_progress: ActionProgressTracker = field(default_factory=ActionProgressTracker)`.
- `sgs_v2/battle_core/state_lifecycle_system.py`:
  - Implement PRE_BATTLE window calculation (`first=1, last=N`).
  - Implement mid-combat window calculation based on `action_progress.has_acted_in_round`.
  - Implement same-name refresh transaction (retain `instance_id`, allocate new generation, update window).
  - Implement `expire_eligible_states(context, owner_id)` at action window close.
  - Implement `clear_owner_on_defeat(context, owner_id)`.

**Tests to Create**:
- `tests/test_stage10_phase2_lifecycle_generation.py`:
  - PRE_BATTLE N=1 $\to$ Round 1 eligible, expires at end of Round 1 ActionStart.
  - PRE_BATTLE N=2 $\to$ Round 1 & Round 2 eligible.
  - Applied in Round R before ActionStart $\to$ $[R, R+N-1]$.
  - Applied in Round R after ActionStart $\to$ $[R+1, R+N]$.
  - Refresh before ActionStart $\to$ new generation eligible in R.
  - Refresh after ActionStart $\to$ new generation starts in R+1.
  - ActionProgressTracker: second ActionStart call in same combat round rejected/idempotent.
  - Stunned owner still marks ActionStart consumed.
  - Owner defeat cleanses all states synchronously in deterministic order.
  - Source defeat leaves target's persistent states intact.

**Phase 2 Exit Gate**:
- 753 baseline tests pass.
- Phase 1 & 2 tests pass.
- Lifecycle property matrix fully verified.

---

## 10. Phase 3 — RuleIntent & ExecutionRight Integration

**Goal**: Integrate the sibling `RuleIntent` model into `RuleHookSystem` and `ExecutionRightSystem`, strictly implementing Hardening H01 and the orthogonal Target Defeat vs Owner Defeat scopes.

**Production Files to Modify**:
- `sgs_v2/battle_core/rule_intent.py`:
  - Formalize `ExecutionRightDecision`, `ExecutionRightDecisionKind` (`ALLOW`, `REJECT_CURRENT`, `ABORT_OWNER_STATE_REMAINDER`, `ABORT_HOOK`), `ExecutionRightReason`.
  - Sibling intent hierarchy: `RuleIntent = Effect | RecoveryOpportunity`.
- `sgs_v2/battle_core/execution_right_system.py`:
  - Implement `evaluate_rule_intent(descriptor: RuleIntentExecutionDescriptor, context: BattleContext) -> ExecutionRightDecision`.
  - Strictly read typed descriptor: check target alive (`is_alive`), check owner alive (`is_alive`), check state existence, check suppression.
  - ZERO duck-typing (no `hasattr`, `getattr`, or reflection).
- `sgs_v2/battle_core/rule_hook_system.py`:
  - **H01 Precondition Validation**: Debug assertion verifying `intent.execution_descriptor is not None` and `intent_owner_id` is populated.
  - Implement loop over collected `RuleIntent`s:
    - Call `evaluate_rule_intent`.
    - If `ALLOW`: dispatch to executor.
    - If `REJECT_CURRENT(TARGET_DEFEATED)`: record aborted result; **continue batch for other intents**.
    - If `ABORT_OWNER_STATE_REMAINDER(OWNER_DEFEATED)`: record abort; **discard remaining intents with same `state_owner_id`**; continue other owners.
    - If `ABORT_HOOK`: halt batch immediately.
  - Produce `HookResolutionResult` containing typed results.
- `sgs_v2/battle_core/trigger_system.py`:
  - Attach `RuleIntentExecutionDescriptor` to every emitted intent.
- `sgs_v2/battle_core/effect_result.py`:
  - Add `AbortedRuleIntentResult` and `RecoveryOpportunityResult`.

**Tests to Create**:
- `tests/test_stage10_phase3_rule_intent_execution_right.py`:
  - **S10-FG-H01 Verification**: Test verifying debug assertion fails if descriptor is None; test verifying `ExecutionRightSystem` reads only descriptor fields with zero duck typing.
  - **Target Defeat Timeline (A/B/C/D)**:
    - Intent A defeats Target 1.
    - Intent B (targeting dead Target 1 from living Owner 1) $\to$ `REJECT_CURRENT(TARGET_DEFEATED)`.
    - Intent C (targeting living Target 2 from living Owner 1) $\to$ `ALLOW` $\to$ executes!
    - Intent D (from living Owner 2) $\to$ `ALLOW` $\to$ executes!
  - **Owner Defeat Timeline (A/B/C/D)**:
    - Intent A defeats Owner 1.
    - Intent B (from dead Owner 1) $\to$ `ABORT_OWNER_STATE_REMAINDER(OWNER_DEFEATED)`.
    - Remaining intents from Owner 1 discarded.
    - Intent D (from living Owner 2) $\to$ `ALLOW` $\to$ executes!

**Phase 3 Exit Gate**:
- 753 baseline tests pass.
- Hardening S10-FG-H01 verified.
- Target Defeat and Owner Defeat scopes cleanly separated in automated tests.

---

## 11. Phase 4 — Persistent Continuous Damage & FROZEN_APPLICATION Lane

**Goal**: Implement the 6 continuous damage states (`BURN`, `FLOOD`, `POISON`, `ROUT`, `SANDSTORM`, `REBELLION`) routing through Stage8 `DamageSystem` using the `FROZEN_APPLICATION` calculation lane.

**Production Files to Modify**:
- `sgs_v2/battle_core/damage_system.py`:
  - Add `CalculationBasis` enum (`LIVE_RUNTIME`, `FROZEN_APPLICATION`).
  - Extend `DamageRequest` with `calculation_basis`, `frozen_basis: FrozenContinuousDamageBasis | None`, and `source_generation_id`.
  - On `FROZEN_APPLICATION` lane:
    - Bypass live source alive/troops validation (permit historical source with 0 troops).
    - Read locked attributes, locked formula policy, locked modifiers, and locked crit from `frozen_basis`.
    - Execute base formula tick RNG using existing Stage8 formulas.
    - Read dynamic target facts at tick time.
  - Preserve `LIVE_RUNTIME` pipeline identical to Stage8.
- `sgs_v2/battle_core/damage_pipeline_trace.py`:
  - Embed `source_generation_id` and frozen calculation trace.
- `sgs_v2/battle_core/official_state_catalog.py`:
  - Bind `BURN`, `FLOOD`, `POISON`, `ROUT`, `SANDSTORM`, `REBELLION` to `ContinuousDamageStateParams`.

**Tests to Create**:
- `tests/test_stage10_phase4_continuous_damage_frozen_lane.py`:
  - **S10-R2-H02 Frozen Lane Spy**: Instrument source unit; verify zero calls to `source.troops`, `source.attributes`, or source modifier providers during DOT tick.
  - **Source-Dead Execution**: Source unit killed in Round 1; target continues to suffer DOT damage in Round 2; historical provenance intact.
  - **REBELLION Route Locking**: Route (weapon vs strategy) chosen at application time based on ATK vs INT; route locked in snapshot; applies `DamageDefensePolicy.IGNORE_DEFENSE`.
  - **LIVE_RUNTIME Regression**: Verify standard attacks produce identical results to Stage8 golden baselines.

**Phase 4 Exit Gate**:
- 753 baseline tests pass.
- All Phase 4 tests pass.
- Frozen-lane zero-live-read spy test green.

---

## 12. Phase 5 — RecoveryOpportunitySystem (FIRST_AID & RECUPERATION)

**Goal**: Implement the unified `RecoveryOpportunitySystem` executing `FIRST_AID_AFTER_DAMAGE` and `RECUPERATION_ACTION_START`, strictly implementing Hardening H02, zero-loss eligibility, full-troop recovery, and deterministic native RNG draws.

**Production Files to Create**:
- `sgs_v2/battle_core/recovery_opportunity_system.py`:
  - Unified engine evaluating Gates 1 through 5:
    - Gate 1: Target alive check.
    - Gate 2 (Bifurcated):
      * `FIRST_AID_AFTER_DAMAGE`: Requires `DamageAftermathFact.hit_topology == RESOLVED_HIT` and `ReactionPermissionPolicy.can_trigger_recovery(source_type) == True`.
      * `RECUPERATION_ACTION_START`: Skipped completely (`DamageAftermathFact` must be None; `ReactionPermissionPolicy` never queried).
    - Gate 3: Lifecycle window check (`first_eligible <= round <= last_eligible`).
    - Gate 4: Source skill gate (`SkillRuntime.enabled`).
    - Gate 5: Simulator probability draw via `context.random.chance(probability)`.
  - Calculation and dispatch:
    - Treatment amount model vs trigger damage ratio model.
    - Full troops (`recoverable_gap == 0`) does NOT suppress draw; passes to `RecoverySystem` which resolves actual recovery = 0.
    - Dispatch to `RecoverySystem.recover`.

**Production Files to Modify**:
- `sgs_v2/battle_core/recovery_system.py`: Propagate `source_generation_id`.
- `sgs_v2/battle_core/official_state_catalog.py`: Bind `FIRST_AID` and `RECUPERATION`.

**Tests to Create**:
- `tests/test_stage10_phase5_recovery_opportunity_system.py`:
  - **S10-FG-H02 RECUPERATION Isolation**: Test verifying `RECUPERATION_ACTION_START` operates with `aftermath_fact=None` and never queries `ReactionPermissionPolicy`; test asserting invariant violation if dummy aftermath fact is passed.
  - **FIRST_AID Zero-Loss Eligibility**:
    - Weakness-zero resolved hit $\to$ opportunity admitted.
    - Barrier-zero resolved hit $\to$ opportunity admitted.
    - Evasion/miss $\to$ opportunity rejected (zero RNG draws).
    - Fatal damage $\to$ target defeated; opportunity rejected (zero RNG draws).
  - **Full-Troop Recovery**: Target at max HP; opportunity admitted; draws RNG; recovery resolves actual = 0.
  - **RNG Determinism ($p=0, p=1$)**:
    - $p=0.0 \to$ exactly one RNG draw, evaluates False.
    - $p=1.0 \to$ exactly one RNG draw, evaluates True.
    - Dead target or disabled skill before RNG gate $\to$ zero RNG draws.

**Phase 5 Exit Gate**:
- 753 baseline tests pass.
- Hardening S10-FG-H02 verified.
- All admission gate and zero-loss edge tests pass.

---

## 13. Phase 6 — Shared DamageAftermathPort & Stage9 Reconciled Routes

**Goal**: Implement `DamageAftermathPort` and mount it across all Stage9 settlement routes at their exact, frozen checkpoints; update `ReactionPermissionPolicy` for ASSAULT; enforce exactly-once `DefeatCleanupPort` across all death paths.

**Production Files to Create**:
- `sgs_v2/battle_core/damage_aftermath_port.py`:
  - `DamageAftermathPort`: `commit_aftermath(context, aftermath_fact: DamageAftermathFact) -> AftermathResult`.
  - Collects after-damage opportunities via `TriggerSystem.collect_after_damage`.
  - Dispatches to `RecoveryOpportunitySystem`.

**Production Files to Modify**:
- `sgs_v2/battle_core/reaction_permission_policy.py`:
  - Add `SourceType.ASSAULT` to `can_trigger_recovery`.
- `sgs_v2/battle_core/damage_instance_coordinator.py`:
  - In `NoPartitionPlan`: target settlement $\to$ defeat cleanup if dead $\to$ `commit_aftermath` if alive $\to$ finish.
  - In `DamageShareTransactionPlan`: target settlement $\to$ if target dead: TARGET_DEATH_INTERRUPT; if target alive: commit sharer direct loss (cleanup sharer if dead) $\to$ `commit_aftermath(target)` $\to$ finish.
  - In `DistributionTransactionPlan`: drain participant direct loss (cleanup if dead) $\to$ target settlement (cleanup if dead) $\to$ `commit_aftermath(target)` if alive $\to$ finish.
- `sgs_v2/battle_core/cleave_derived_damage_system.py`:
  - Cleave target settlement $\to$ if alive: commit share direct loss $\to$ `DamageAftermathPort(target)` (FIRST_AID) $\to$ attacker recovery $\to$ callbacks.
- `sgs_v2/battle_core/counter_system.py`:
  - Counter target settlement $\to$ `DamageAftermathPort` $\to$ callbacks.
- `sgs_v2/battle_core/damage_resolution_system.py` & `direct_troop_loss_system.py`:
  - Synchronously invoke `DefeatCleanupPort.commit_defeat` on death edge.
- `sgs_v2/battle_core/battle_systems.py`:
  - Wire Composition Root V2.

**Tests to Create**:
- `tests/test_stage10_phase6_damage_aftermath_stage9.py`:
  - **S10-R2-H01 Defeat Cleanup Conformance Spy**: Verify `commit_defeat` is called exactly once across: standard damage, DOT, Counter, Cleave target, Cleave share, Distribution direct loss, Chain feedback.
  - **Stage9 Cleave vs FIRST_AID Ordering**: Verify exact sequence: Cleave target settlement $\to$ Sharer direct loss $\to$ Target FIRST_AID aftermath $\to$ Attacker recovery.
  - **ASSAULT Recovery Permission**: Verify `SourceType.ASSAULT` hit triggers FIRST_AID.
  - **DirectTroopLoss Inviolability**: Verify `SHARE_DIRECT_LOSS` and `DISTRIBUTION_DIRECT_LOSS` never trigger FIRST_AID.
  - **Chain Feedback Recovery Blocked**: Verify `CHAIN_TRUE_FEEDBACK` never triggers FIRST_AID.

**Phase 6 Exit Gate**:
- 753 baseline tests pass.
- S10-R2-H01 defeat cleanup conformance spy passes across all paths.
- Stage9 compatibility addenda verified 100%.

---

## 14. Phase 7 — Battle Teardown, Provenance & Observation Events

**Goal**: Implement `clear_all_on_battle_end` post-victory teardown, end-to-end generation provenance propagation, and observation event payload consistency.

**Production Files to Modify**:
- `sgs_v2/battle_core/state_lifecycle_system.py`:
  - Implement `clear_all_on_battle_end(context)`: iterates all units, removes all states (finite, UNTIL_BATTLE_END, EXTERNAL_LIFECYCLE) in deterministic order, publishes `STATE_CLEARED_ON_BATTLE_END`.
- `sgs_v2/battle_core/battle_finalization_coordinator.py` & `engine.py`:
  - Call `StateLifecycleSystem.clear_all_on_battle_end` after victory is latched and admitted work has drained.
- `sgs_v2/battle_core/events.py`:
  - Ensure `application_generation_id` / `source_generation_id` are included in payloads for `STATE_APPLIED`, `STATE_REFRESHED`, `STATE_EXPIRED`, `STATE_REMOVED`, `DAMAGE_RESOLVED`, `RECOVERY_RESOLVED`.

**Tests to Create**:
- `tests/test_stage10_phase7_teardown_provenance.py`:
  - **Battle Teardown**: Battle ends; verify `context.states` is completely empty across both teams; zero state leakage; `STATE_CLEARED_ON_BATTLE_END` emitted.
  - **Generation Provenance Propagation**:
    - State refreshes from Generation 1 to Generation 2 while an intent from Generation 1 is pending.
    - Pending Generation 1 intent executes: carries G1 potency, G1 formula basis, G1 provenance.
    - Dynamic target checks (survival, healing ban) evaluate current state.
  - **EventBus Observation Purity**: Verify no gameplay listeners exist on EventBus.

**Phase 7 Exit Gate**:
- 753 baseline tests pass.
- Teardown cleanses 100% of states.
- Generation propagation matrix fully verified.

---

## 15. Phase 8 — Full Conformance Suite & Final Audit

**Goal**: Execute the complete Frozen Regression Plan V4 and the Two-Implementer Conformance Suite, verifying zero design drift and complete backward compatibility.

**Tests to Create**:
- `tests/test_stage10_phase8_two_implementer_conformance.py`:
  - Encode all 14 Two-Implementer scenarios from `STAGE10.md §36`:
    1. PRE_BATTLE N=1
    2. Source dies before DOT tick
    3. Target dies mid-hook (Effect A/B/C)
    4. Owner dies mid-hook (Effect A/B/C)
    5. Same-name refresh before pending effect executes
    6. Weakness-zero FIRST_AID
    7. Barrier-zero FIRST_AID
    8. Evasion FIRST_AID
    9. ASSAULT FIRST_AID
    10. Full-troop FIRST_AID & RECUPERATION
    11. Probability 100% & 0% native one-draw
    12. Share direct loss non-trigger
    13. Cleave + Share + FIRST_AID ordering
    14. Battle-end teardown
- `tests/test_stage10_hardening_audit.py`:
  - Consolidate all hardening checks: S10-FG-H01, S10-FG-H02, S10-R2-H01, S10-R2-H02.

**Verification Steps**:
```powershell
python -m pytest -q
# Must pass all 753 baseline tests + all new Stage10 tests
python demo.py
# Must run cleanly
```

**Phase 8 Exit Gate**:
- 100% test pass rate across baseline + Stage10 suite.
- Zero blob drift in frozen documentation.
- Ready for formal independent implementation audit.

---

## 16. Mandatory Test Mapping Matrix

Every frozen regression obligation from `STAGE10.md §34` is explicitly mapped to a target test file:

| Frozen Regression Obligation | Category | Target Test File | Specific Required Scenario |
|---|---|---|---|
| PRE_BATTLE N=1 & N=2 | `LIFECYCLE` | `tests/test_stage10_phase2_lifecycle_generation.py` | Round 1 exactly 1 opportunity; physical expiry at action window close |
| Mid-combat Apply Before/After ActionStart | `LIFECYCLE` | `tests/test_stage10_phase2_lifecycle_generation.py` | Before ActionStart $\to [R, R+N-1]$; After ActionStart $\to [R+1, R+N]$ |
| Refresh Before/After ActionStart | `LIFECYCLE` | `tests/test_stage10_phase2_lifecycle_generation.py` | Generation transition; window recalibration |
| ActionProgressTracker Invariant | `LIFECYCLE` | `tests/test_stage10_phase2_lifecycle_generation.py` | Max 1 ActionStart opportunity per owner per round; stunned owner consumed |
| Target Defeat mid-batch (A/B/C/D) | `DEATH` | `tests/test_stage10_phase3_rule_intent_execution_right.py` | `REJECT_CURRENT(TARGET_DEFEATED)` only drops target; other living targets execute |
| Owner Defeat mid-batch (A/B/C/D) | `DEATH` | `tests/test_stage10_phase3_rule_intent_execution_right.py` | `ABORT_OWNER_STATE_REMAINDER(OWNER_DEFEATED)` drops owner tail; other owners execute |
| S10-FG-H01 Zero Duck-Typing | `HARDENING` | `tests/test_stage10_phase3_rule_intent_execution_right.py` | Reads only `RuleIntentExecutionDescriptor`; assertion validates precondition |
| FROZEN_APPLICATION Zero Live Read | `STAGE8` | `tests/test_stage10_phase4_continuous_damage_frozen_lane.py` | Instrumentation spy proves zero source attribute/troops reads during tick |
| Source-Dead DOT Tick | `STAGE8` | `tests/test_stage10_phase4_continuous_damage_frozen_lane.py` | Source killed in R1; DOT executes in R2 with G1 historical provenance |
| REBELLION Route & Defense Bypass | `STAGE8` | `tests/test_stage10_phase4_continuous_damage_frozen_lane.py` | Route locked in snapshot; applies `IGNORE_DEFENSE`; not DirectTroopLoss |
| S10-FG-H02 RECUPERATION Isolation | `HARDENING` | `tests/test_stage10_phase5_recovery_opportunity_system.py` | `aftermath_fact=None`; `ReactionPermissionPolicy` never queried |
| FIRST_AID Zero-Loss Eligibility | `FIRST_AID` | `tests/test_stage10_phase5_recovery_opportunity_system.py` | Weakness-zero & barrier-zero eligible; evasion & fatal ineligible |
| Full-Troop Recovery | `RECOVERY` | `tests/test_stage10_phase5_recovery_opportunity_system.py` | `recoverable_gap == 0` does not suppress RNG; resolves actual recovery = 0 |
| Recovery RNG One-Draw Determinism | `RNG` | `tests/test_stage10_phase5_recovery_opportunity_system.py` | $p=0.0 \to 1$ draw; $p=1.0 \to 1$ draw; zero RNG calls if dead before gate |
| S10-R2-H01 Defeat Cleanup Conformance Spy | `HARDENING` | `tests/test_stage10_phase6_damage_aftermath_stage9.py` | Exactly-once `commit_defeat` across standard, DOT, counter, cleave, share, distribution |
| Stage9 Cleave vs FIRST_AID Ordering | `STAGE9` | `tests/test_stage10_phase6_damage_aftermath_stage9.py` | Target settlement $\to$ Sharer direct loss $\to$ Target FIRST_AID $\to$ Attacker recovery |
| ASSAULT FIRST_AID Authorization | `STAGE9` | `tests/test_stage10_phase6_damage_aftermath_stage9.py` | `SourceType.ASSAULT` hit triggers FIRST_AID opportunity |
| DirectTroopLoss Inviolability | `STAGE9` | `tests/test_stage10_phase6_damage_aftermath_stage9.py` | `SHARE_DIRECT_LOSS` and `DISTRIBUTION_DIRECT_LOSS` never trigger FIRST_AID |
| Battle Teardown Cleansing | `TEARDOWN` | `tests/test_stage10_phase7_teardown_provenance.py` | All states cleansed on battle end; `STATE_CLEARED_ON_BATTLE_END` emitted |
| Refresh G1/G2 Provenance | `PROVENANCE` | `tests/test_stage10_phase7_teardown_provenance.py` | Pending G1 intent executes with G1 snapshot; dynamic target facts are current |
| Two-Implementer 14 Scenarios | `CONFORMANCE` | `tests/test_stage10_phase8_two_implementer_conformance.py` | All 14 normative author self-audit scenarios encode identical observable behavior |

---

## 17. Hardening Obligations Specification

The four formal hardening obligations must be encoded as explicit, automated regression tests:

### 17.1 S10-FG-H01: Execution Descriptor Precondition Validation
- **Requirement**: `RuleHookSystem` debug assertions must verify `intent.execution_descriptor is not None` and `intent.execution_descriptor.intent_owner_id` is populated before calling `evaluate_rule_intent`.
- **Test**: An automated test must verify that `ExecutionRightSystem` reads only typed fields from `RuleIntentExecutionDescriptor` and raises an assertion or type error if an arbitrary un-descriptored object is submitted. Duck-typing (`getattr`, `hasattr`) is strictly forbidden.

### 17.2 S10-FG-H02: RECUPERATION Aftermath-Fact Isolation
- **Requirement**: `RecoveryOpportunitySystem` executing `RECUPERATION_ACTION_START` must operate with `DamageAftermathFact = None` and never query `ReactionPermissionPolicy`.
- **Test**: An automated test must verify that passing an explicit dummy `DamageAftermathFact` to an action-start opportunity raises an invariant violation or is strictly ignored, proving total decoupling from the damage pipeline.

### 17.3 S10-R2-H01: Exactly-Once Defeat Cleanup Conformance Spy
- **Requirement**: `DefeatCleanupPort.commit_defeat` must be called exactly once per alive $\to$ defeated transition.
- **Test**: An instrumented test spy must verify that every destructive route (standard damage, DOT, Counter, Cleave target, Cleave share, Distribution direct loss, Chain restricted feedback) invokes `DefeatCleanupPort.commit_defeat` exactly once when a unit's troops reach 0.

### 17.4 S10-R2-H02: Frozen Lane Zero-Live-Read Spy
- **Requirement**: On the `FROZEN_APPLICATION` lane, `DamageSystem` must never query live source attributes, source troops, or source modifier providers at tick time.
- **Test**: Instrument the source unit; verify that executing a periodic damage tick on a living target performs zero reads of `source.troops`, `source.attributes`, or source modifiers.

---

## 18. Forbidden Duplicate Truths Ledger

The implementation build must strictly observe these architectural boundaries:

```text
[NO-DUPLICATE-01] No second ASSAULT allow-list:
                  ReactionPermissionPolicy.can_trigger_recovery is the sole authority.

[NO-DUPLICATE-02] No second death permission logic:
                  ExecutionRightSystem is the sole decision maker for death during hook batches.

[NO-DUPLICATE-03] No second damage formula:
                  DOT damage must route through DamageSystem via FROZEN_APPLICATION lane.

[NO-DUPLICATE-04] No second recovery RNG engine:
                  RecoveryOpportunitySystem is the single engine for FIRST_AID and RECUPERATION.

[NO-DUPLICATE-05] No duplicate lifecycle countdown:
                  StateLifecycleSystem exclusively owns physical expiration at action window close.

[NO-DUPLICATE-06] No duplicated generation allocator:
                  StateApplicationGenerationId is allocated solely via StateGenerationAllocator.

[NO-DUPLICATE-07] No EventBus gameplay control flow:
                  EventBus is strictly observational. Event handlers must NEVER alter gameplay state.

[NO-DUPLICATE-08] No DirectTroopLoss promotion:
                  SHARE_DIRECT_LOSS and DISTRIBUTION_DIRECT_LOSS never enter DamageAftermathPort.

[NO-DUPLICATE-09] No duck-typing in ExecutionRightSystem:
                  Only read typed RuleIntentExecutionDescriptor.
```

---

## 19. Design Reopen Stop Conditions

If any of the following conditions occur during code construction, the implementer must **STOP WORK IMMEDIATELY** and emit `DESIGN REOPEN REQUIRED`:

1. **Unspecified Behavior**: An edge case is discovered that is not specified in `STAGE10.md` or the Compatibility Addenda.
2. **Contract Conflict**: Two frozen documents conflict on observable behavior, ordering, or formula inputs.
3. **Authority Conflict**: Official Gameplay Authority (`sgs-state-mechanics-research`) contradicts the frozen design.
4. **Architectural Impasse**: The production runtime cannot support a frozen contract without altering the frozen DAG or Stage 7/8/9 architecture.
5. **Gameplay Choice Required**: The implementer finds themselves forced to choose between multiple plausible gameplay behaviors.

**Prohibition**:
The implementer must **never** make a subjective gameplay decision. An unauthorized decision constitutes a critical breach of the frozen baseline.

---

## 20. Commit Strategy

To ensure full auditability, the implementation must be committed phase by phase:

```text
Commit 1: feat(stage10): add core typed runtime primitives and generation contracts (Phase 1)
Commit 2: feat(stage10): implement lifecycle arithmetic, generation tracking, and ActionProgressTracker (Phase 2)
Commit 3: feat(stage10): integrate rule intent sibling hierarchy and execution right system (Phase 3)
Commit 4: feat(stage10): integrate persistent continuous damage and FROZEN_APPLICATION lane (Phase 4)
Commit 5: feat(stage10): implement unified recovery opportunity runtime for FIRST_AID and RECUPERATION (Phase 5)
Commit 6: feat(stage10): integrate damage aftermath port and reconcile Stage9 settlement routes (Phase 6)
Commit 7: feat(stage10): implement battle teardown and end-to-end generation provenance (Phase 7)
Commit 8: test(stage10): complete frozen conformance suite and two-implementer scenarios (Phase 8)
```

---

## 21. Final Implementation Acceptance Gate

Stage10 production implementation is officially complete **only** when all of the following criteria are satisfied:

```text
[ ] Baseline tests remain 100% green (753/753 passed)
[ ] All Stage10 unit and integration tests pass
[ ] All 14 Two-Implementer scenarios pass deterministically
[ ] Hardening obligations S10-FG-H01 and S10-FG-H02 pass
[ ] Conformance spies S10-R2-H01 and S10-R2-H02 pass
[ ] Zero blob drift in STAGE10.md or Stage 7/8/9 Addenda
[ ] Zero drift in pinned Gameplay Authority blobs
[ ] Zero unauthorized Stage 7/8/9 semantic changes
[ ] Zero unresolved gameplay TODOs or TBD choices
[ ] python demo.py runs cleanly to completion
[ ] Full independent implementation audit completed and passed
```

Production code implementation is authorized to begin in the subsequent round using this specification.
