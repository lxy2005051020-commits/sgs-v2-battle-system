# STAGE 9 — Cross-Mechanism Runtime Orchestration

> STATUS: **DRAFT — DESIGN AUDIT REQUIRED**  
> Authoring baseline (battle): `4745d061345181aaf12c454ada9890d7b69c5598`  
> Authority baseline (state): `15ed915435f328a6ecd8f488d98b5b9e13c913b5`  
> Authoring date: 2026-09-13  
> This document is **Implementation Design Authority**, not gameplay research and not implementation approval.

---

## 0. Status / Authority

### 0.1 Authority boundary

```text
Gameplay Semantic Authority
=
mechanism P0 / shared Stage9 P0

Implementation Design Authority
=
STAGE9.md

Runtime Representation Authority
=
STAGE9.md
  derived from RF-C01

Regression Semantic Authority
=
RF-C01 regression contracts
+ current P0
```

`STAGE9.md` does not redefine gameplay. It may only **consume / organize / map / implement** frozen rules.

Authority priority:

```text
1. newest formal mechanism/shared P0
2. RF-P01..RF-P07 re-freeze records
3. STAGE9_CORE_ARBITRATION_RULES_V2
4. RF-C01 runtime contracts / invariants / regressions
5. STAGE9_AUTHORITY_MAP
6. historical audit/research only as provenance
```

If a gameplay-affecting design cannot be uniquely derived from the authority set, the implementation section must stop at:

```text
SPEC BLOCKED BY AUTHORITY GAP
```

No implementation convenience may silently become a game rule.

### 0.2 Authoring admission

Current gate consumed by this document:

```text
DELTA VERDICT = PASS
STAGE9 SPEC AUTHORING ADMISSION = READY
Remaining blocking findings = 0
Remaining pre-spec findings = 0
P0 semantic change = 0
Runtime ambiguity = 0
P0 conflict = 0
Stage8 reopen = NO
```

`DSTS9-B02` remains deliberately dual-status:

```text
EMPIRICAL: OPEN / UNOBSERVED
RUNTIME: CLOSED BY PROJECT_RUNTIME_DEFAULT
DESIGN: NOT BLOCKING
RESEARCH DEBT: YES
```

This document never upgrades it back into a blocker and never relabels the runtime default as empirically proven official behavior.

### 0.3 Stage 8 boundary

```text
Stage8 = FROZEN
Formal Stage8 Reopen = NO
```

Stage9 wraps, coordinates, redirects, partitions, derives, schedules and finalizes around Stage8 seams. It does not replace Stage8.

---

## 1. Goals

Stage9 turns frozen cross-mechanism semantics into an implementable runtime architecture with one explicit control-flow owner, strong operation identity, deterministic ordering, local admission barriers, testable provenance, and an explicit battle-finalization barrier.

The design must make the following questions answerable from types and call sites rather than from call-stack folklore:

- Which Action / NormalAttack / DamageInstance owns this work?
- Which target identity is being used at this phase?
- Is the work admitted, executing, cancelled locally, or not yet admitted?
- Is a troop change a normal DamageEvent, a derived damage event, a restricted feedback, or attributed direct troop loss?
- Which callbacks are legal for this source identity?
- Has victory merely latched, or is the battle finalized?

Engineering design rule:

```text
explicit orchestration > implicit event ordering
strong identity > booleans
local typed policy > string inspection
```

---

## 2. Non-Goals

Stage9 does **not** implement or research:

```text
new skill scripting language
new AI target strategy
new base damage formulas
Stage8 modifier/formula ownership changes
complete logging rewrite
visual battle replay
all remaining status mechanics
exact official Counter universal comparator fidelity
exact universal dispel fidelity
DSTS9-B02 empirical closure
new official PRNG assumptions
```

Assault is represented only as an ordered/admitted dispatch seam because the current production tree has no Assault runtime. Stage9 does not invent Assault gameplay semantics.

No global `enable_stage9=true` feature flag is introduced. Incremental implementation uses composition-root registration and isolated fixtures.

---

## 3. Frozen Inputs

Mandatory authoring inputs:

- `stages/stage9/docsync/STAGE9_AUTHORITY_MAP.md`
- `stages/stage9/audits/STAGE9_GLOBAL_CROSS_MECHANISM_FINAL_AUDIT.md`
- `stages/stage9/audits/STAGE9_PRE_SPEC_DELTA_AUDIT.md`
- `stages/stage9/hardening/STAGE9_TYPED_RUNTIME_CONTRACTS.md`
- `stages/stage9/hardening/STAGE9_RUNTIME_INVARIANTS.md`
- `stages/stage9/hardening/STAGE9_REGRESSION_CONTRACTS.md`
- `stages/stage9/repairs/RF_P01_STAGE9_INTEGERIZATION_REFREEZE.md` ... `RF_P07_CLEAVE_STATE_AND_SECONDARY_TARGET_REFREEZE.md`
- `stages/stage9/research/core_arbitration_v2/STAGE9_CORE_ARBITRATION_RULES_V2.md`
- `STAGE9_EXECUTION_RIGHT_AND_DEATH_SCOPE_CONTRACT.md`
- `STAGE9_BATTLE_FINALIZATION_BARRIER_CONTRACT.md`
- current mechanism P0 / Freeze Records identified by `STAGE9_AUTHORITY_MAP.md`
- `stages/stage8/STAGE8.md`
- `stages/stage8/STAGE8_DESIGN_FREEZE.md`
- `stages/stage8/STAGE8_FREEZE_RECORD.md`
- current `sgs_v2/battle_core/` and `tests/` layout at the authoring baseline.

Mechanism state IDs consumed by Stage9:

| hint id | canonical | current production identifier |
|---:|---|---|
| 690081 | COMBO | `OfficialStateId.COMBO` |
| 690084 | CLEAVE | `OfficialStateId.CLEAVE` |
| 690085 | COUNTERATTACK | `OfficialStateId.COUNTERATTACK` |
| 690086 | DISTRIBUTION | compatibility identifier `OfficialStateId.DAMAGE_SPLIT` |
| 690087 | DAMAGE_SHARE | `OfficialStateId.DAMAGE_SHARE` |
| 690097 | CHAIN_LINK | `OfficialStateId.CHAIN_LINK` |
| 690098 | GUARD | `OfficialStateId.GUARD` |
| 690103 | CONFUSION | `OfficialStateId.CONFUSION` |
| 690106 | TAUNT | `OfficialStateId.TAUNT` |

`DAMAGE_SPLIT` is a production compatibility name only. Current Stage9 canonical terminology is **DISTRIBUTION**.

---

## 4. Stage8 Boundary

Frozen Stage8 pipeline remains:

```text
DamageRequest
→ participant validation
→ StateDamageRuleProvider / adapter
→ DamageRuleCollection
→ DamagePreventionSystem
→ HitResolutionSystem
→ DamageFormulaPolicySystem
→ Frozen Base Formula
→ coefficient
→ DamageModifierSystem
→ finalization
→ DamageResult + DamagePipelineTrace
→ DamageResolutionSystem
→ TroopSystem
```

Stage9 rules:

1. `DamageSystem.calculate()` remains the only standard Stage8 theoretical-damage entry.
2. Stage9 never adds Cleave/Chain/Share/Distribution flags to `DamageRequest` merely to smuggle non-Stage8 semantics through the pipeline.
3. Standard main/skill/Counter damage may produce a legitimate `DamageRequest`; `AttributedDirectTroopLoss` never does.
4. `DamageResult.final_damage` keeps its Stage8 meaning. Stage9 treats it as pre-partition `Dtotal` for partition-eligible standard DamageEvents and never mutates it into `Dtarget`.
5. A future narrow `DamageResolutionSystem` settlement overload may accept an explicitly assigned target amount while preserving the original `DamageResult`; existing `apply_result()` remains behavior-compatible as `assigned = final_damage`.
6. Stage8 formula classes, prevention semantics, formula policy, modifier ownership, `DamagePipelineTrace`, and frozen base formulas are **DO NOT TOUCH** for Stage9 semantics.
7. Cleave is a typed derived path. Chain TRUE_FEEDBACK and Share/Distribution direct loss are restricted paths. None reruns the Stage8 base formula.

This is an engineering extension around a frozen seam, not a Stage8 semantic reopen.

---

## 5. Existing Architecture Baseline

Current production facts relevant to Stage9:

- `BattleEngine` owns round/action phase progression and currently checks `VictorySystem` at coarse barriers.
- `BattleSystems` is the explicit composition root.
- `ActionSystem` currently performs actor/Stun gate then calls `NormalAttackSystem`.
- `NormalAttackSystem` already owns normal-attack permission, target selection, standard weapon `DamageRequest`, NORMAL_ATTACK fact ordering, and settlement.
- `TargetSystem` is the common target/RNG query seam.
- `DamageSystem` owns the frozen Stage8 theoretical pipeline.
- `DamageResolutionSystem` owns Stage8 `DamageResult` settlement and current damage/death facts.
- `TroopSystem` is the sole troop mutation boundary.
- `VictorySystem` is currently a pure world-state evaluator returning `BattleResult`.
- `EventBus` explicitly documents facts-only semantics.
- `StateLifecycleSystem` is the sole formal apply/remove/expire write entry.
- `StateRegistry` stores instances and deterministic query data, though current lookup is linear.
- `TriggerSystem` produces ordered Effects and does not execute side effects.
- `RecoverySystem` delegates troop writes to `TroopSystem`.
- `EffectExecutor` currently routes every `DamageEffect` directly to `DamageResolutionSystem.resolve()`.
- `RandomSystem` is the unique battle RNG.
- `UnitRuntime` has lineup position but no skill-slot identity; source-bound Stage9 state metadata must therefore carry authoritative apply-time source skill slot when P0 ordering requires it.

### 5.1 EXISTING_ARCHITECTURE_IMPACT_MATRIX

| Existing component | Stage9 action | Why |
|---|---|---|
| `BattleEngine` | MODIFY narrowly | delegate victory latch/finalization barriers; preserve phase loop |
| `BattleContext` | MODIFY narrowly | hold stable per-battle operation-id allocator + termination record only |
| `BattleSystems` | MODIFY | wire new Stage9 coordinators/policies; remains composition root |
| `ActionOrderSystem` | KEEP | existing deterministic ordering/RNG seam is sufficient |
| `ActionSystem` | MODIFY | allocate `ActionId`, ACTION_START Stage9 maintenance/grant, call master NormalAttack |
| `NormalAttackSystem` | MODIFY / MASTER OWNER | existing owner becomes orchestration-first master; delegates mechanism-local work |
| `TargetSystem` | KEEP / CALL | low-level candidate/random seam; no Guard/Combo lifecycle ownership |
| `AttributeSystem` | KEEP / CALL | live combat stat source for standard Counter damage |
| `DamageSystem` | KEEP / DO NOT TOUCH semantics | frozen Stage8 calculation owner |
| `DamageResolutionSystem` | MODIFY only at settlement seam | preserve Stage8 behavior; allow explicit assigned-target settlement without changing `DamageResult` |
| `TroopSystem` | KEEP / CALL | sole troop mutation boundary |
| `VictorySystem` | MODIFY narrowly | expose pure victory evaluation used by finalization coordinator; keep compatibility behavior |
| `RandomSystem` | KEEP | unique RNG |
| `EventBus` | KEEP semantics | observation only; additional facts allowed, never authoritative control flow |
| `StateLifecycleSystem` | KEEP / CALL | Stage9 maintenance delegates physical writes here |
| `StateRegistry` | KEEP storage; adapter above it | no second state runtime |
| `TriggerSystem` | KEEP | existing typed hook/effect collector |
| `RecoverySystem` | KEEP | existing recovery execution seam |
| `EffectExecutor` | MODIFY narrowly | standard DamageEffect routes through Stage9 DamageInstance coordinator so partition/finalization cannot be bypassed |
| Stage8 formula/resolver internals | DO NOT TOUCH | frozen authority boundary |

No BattleEngine 2.0 is introduced.

---

## 6. Design Principles

Stage9 freezes these engineering principles:

```text
1. orchestration over mutation
2. typed identity over booleans
3. explicit operation scope
4. immutable admission plan where P0 requires snapshot
5. live-read only where P0 requires live state
6. semantic owner remains mechanism P0
7. Stage8 receives only legitimate DamageRequest
8. DirectTroopLoss bypasses DamagePipeline
9. no low-level battle finalization
10. deterministic runtime for every reachable path
```

Additional rules:

- EventBus fact publication never substitutes for coordinator calls.
- No core ordering depends on subscriber registration order.
- No ordering depends on dict/hash iteration or object address.
- State adapters may know official state identity; mechanism-independent low-level systems must not dispatch on skill names.
- Invalid identity/provenance, illegal recursive dispatch, double admission/consume, and duplicate finalization are programmer/domain errors, not silent skips.
- JIT dead-target/member invalidation explicitly defined by P0 is a safe skip, not an exception.
- Performance target is indexed/current-state lookup, not repeated `states × units × history` scans per DamageEvent.

### 6.1 Deterministic comparators

Central reusable comparators:

```text
unit slot order      = team + LineupPosition(COMMANDER, DEPUTY_1, DEPUTY_2) + unit_id tie breaker
skill slot order     = authoritative source_skill_slot ascending
reaction batch order = mechanism P0 comparator, then stable instance identity tie breaker only where authority permits
Cleave effect order  = source_skill_slot ascending
Cleave target order  = GLOBAL_SLOT_ASCENDING
Chain traversal      = battle slot ascending / P0 one-pass order
```

No comparator invents an official universal Counter order where the P0 intentionally leaves only a deterministic project default/fidelity note.

---

## 7. Global Runtime Topology

```text
BattleEngine
  │
  ├─ ActionSystem
  │    ├─ Stage9StateRuntime / maintenance
  │    ├─ ActionId + ComboActionGrant
  │    └─ NormalAttackSystem  ← UNIQUE NORMAL-ATTACK MASTER
  │         ├─ TargetResolutionSystem
  │         │    ├─ ConfusionSelectorPolicy
  │         │    ├─ TauntSelectorPolicy
  │         │    ├─ TargetSystem
  │         │    └─ GuardRedirectResolver
  │         ├─ DamageInstanceCoordinator
  │         │    ├─ DamageSystem.calculate (Stage8 standard damage only)
  │         │    ├─ DamagePartitionCoordinator
  │         │    ├─ DamageResolutionSystem target settlement
  │         │    └─ DirectTroopLossResolver
  │         ├─ CleaveSystem
  │         │    └─ DerivedDamageSystem<CLEAVE>
  │         ├─ ChainSystem / ChainTraversal
  │         ├─ CounterSystem / CounterBatch
  │         ├─ Assault dispatch port
  │         └─ Combo checkpoint
  │
  └─ BattleFinalizationCoordinator
       ├─ VictorySystem (pure condition evaluation)
       ├─ FutureAdmissionGate / ExecutionRight
       └─ BattleTerminationState

Cross-cutting:
OperationIdentity / OperationLineage
ReactionPermissionPolicy
Stage9OperationTrace (observation only)
StateRegistry + StateLifecycleSystem (single existing state runtime)
RandomSystem (single existing RNG)
```

### 7.1 Global NormalAttack sequence

```python
execute_normal_attack(action_scope, actor, *, combo_checkpoint_allowed):
    require(action_scope is admitted)
    if not can_normal_attack(actor):
        return blocked_result

    na = new_normal_attack_instance(action_scope)
    target = target_resolution.resolve(na, actor)  # selector → Guard once → lock
    if target is None:
        return no_target_result

    main = damage_instances.resolve_standard(
        lineage=na.lineage,
        source_type=NORMAL_ATTACK,
        target=target.post_redirect_actual_target,
    )

    admit_and_resolve_immediate_post_hit_work(main)

    if cleave_window_qualified(main):
        resolve_cleave_effects_and_inline_secondary_chain(main)
        resolve_deferred_main_target_chain_if_eligible(main)
    else:
        resolve_main_target_chain_inline_if_eligible(main)

    resolve_counter_batch_if_admitted(na, target.post_redirect_actual_target)

    if future_admission.can_admit(ASSAULT, action_scope) and actor.is_alive:
        assault_dispatch_port.dispatch(action_scope, na)

    if combo_checkpoint_allowed:
        combo.try_run_checkpoint(action_scope, na)

    return normal_attack_result
```

`NormalAttack #2` calls the same master with `combo_checkpoint_allowed=False`.

### 7.2 Standard DamageInstance sequence

```text
allocate DamageInstanceId + lineage
→ construct legitimate Stage8 DamageRequest
→ DamageSystem.calculate
→ freeze Dtotal = DamageResult.final_damage
→ resolve exactly one partition plan: NONE / SHARE / DISTRIBUTION
→ execute target/direct-loss transaction using typed plan
→ produce ActualTargetTroopLoss / direct-loss facts / UnitDeathFact(s)
→ admit only source-permitted local callbacks
→ notify finalization owner of death/victory facts
→ complete DamageInstance barrier
```

No partition rewrites the Stage8 `DamageResult`.

### 7.3 Finalization sequence

```text
UnitDeathFact
→ VictorySystem.evaluate
→ VictoryConditionSatisfied
→ BattleFinalizationCoordinator latch
→ reject FutureBranch admission
→ current admitted operation follows its P0 local drain/cancel rule
→ operation barrier reached
→ commander collateral / other shared terminal work if authoritative
→ FINALIZATION_BARRIER
→ BattleFinalized
```

`VICTORY_LATCHED != FINALIZED` is structural, not a logging convention.

---

## 8. Operation Identity & Provenance

### 8.1 Strong identities

All IDs are immutable typed values allocated by one per-`BattleContext` `OperationIdAllocator` using deterministic monotonic sequences. They are not inferred from event sequence, skill name or Python object identity.

| ID | Generator | Lifetime | Parent | Persisted? |
|---|---|---|---|---|
| `ActionId` | ActionSystem | one unit Action | root | trace/test only |
| `NormalAttackInstanceId` | NormalAttackSystem | one physical standard NA | ActionId | trace/test only |
| `TargetResolutionId` | TargetResolutionSystem | one NA target resolve | NormalAttackId | trace/test only |
| `DamageInstanceId` | Damage/Derived coordinator | one concrete damage event | NA/parent damage | trace/test only |
| `PartitionTransactionId` | DamagePartitionCoordinator | one partition transaction | DamageInstanceId | trace/test only |
| `ReactionBatchId` | CounterSystem | one admitted reaction batch | NormalAttackId | trace/test only |
| `CounterBatchEntryId` | CounterSystem | one batch entry | ReactionBatchId | trace/test only |
| `CleaveEffectId` | CleaveSystem | one source-bound effect execution | NormalAttackId | trace/test only |
| `ChainTraversalId` | ChainSystem | one traversal | DamageInstanceId | trace/test only |
| `DirectTroopLossId` | DirectTroopLossResolver | one direct loss commit | PartitionTransactionId | trace/test only |

IDs are serializable strings in trace fixtures but not written into gameplay state unless an authoritative state contract requires a reference.

### 8.2 Source identity

Stage9 defines a separate typed `SourceType` for orchestration/permission/provenance:

```text
NORMAL_ATTACK
ACTIVE_SKILL
ASSAULT
PERIODIC_DAMAGE
CLEAVE
COUNTER
CHAIN_TRUE_FEEDBACK
SHARE_DIRECT_LOSS
DISTRIBUTION_DIRECT_LOSS
```

`SourceType` is not `DamageType`. A Cleave may inherit `WEAPON | STRATEGY` while remaining `sourceType=CLEAVE`.

For legitimate standard Stage8 damage, Stage9 maps to existing `DamageSourceType` without expanding Stage8 semantics. For non-Stage8 operations there is no fake `DamageRequest` mapping.

### 8.3 OperationLineage

```python
OperationLineage(
    root_action_id: ActionId | None,
    parent_normal_attack_id: NormalAttackInstanceId | None,
    parent_damage_instance_id: DamageInstanceId | None,
    source_type: SourceType,
    physical_attacker: str | None,
    physical_skill: str | None,
    credit_owner: str | None,
)
```

This is intentionally small. Mechanism-local data stays in mechanism-local types.

### 8.4 Type dependency graph

```text
OperationId types + SourceType
        ↓
OperationLineage
        ↓
ActionScope / NormalAttackInstance
        ↓
TargetResolutionResult     DamageInstanceContext
        ↓                         ↓
CleaveEffect / ChainTraversal   PartitionPlan
CounterBatch                   DirectTroopLoss
        \                         /
         → ExecutionRight / OperationBarrier
                    ↓
          BattleFinalizationCoordinator
```

No `Stage9Context` containing every queue/state/mechanism is permitted.

---

## 9. Target Resolution

### 9.1 Immutable result

```python
TargetResolutionResult(
    resolution_id: TargetResolutionId,
    normal_attack_id: NormalAttackInstanceId,
    selected_target: str,
    intended_attack_target: str,
    post_redirect_actual_target: str,
    redirect_source: str | None,
    redirect_reason: RedirectReason,  # NONE | GUARD
)
```

All fields are immutable semantic identities. A generic mutable `target_id` that changes meaning is forbidden.

### 9.2 Pipeline and responsibility

```text
TargetResolutionSystem
  1. build live legal pool through TargetSystem
  2. ConfusionSelectorPolicy
  3. else TauntSelectorPolicy
  4. else default selector through TargetSystem/RandomSystem
  5. freeze IntendedAttackTarget
  6. GuardRedirectResolver exactly once
  7. freeze PostRedirectActualTarget
  8. return TargetResolutionResult
```

Rules:

- Confusion shadows Taunt only at selector arbitration; it does not physically delete/suppress Taunt.
- Guard never recursively redirects the guarder.
- Share/Distribution query the concrete DamageEvent recipient after redirect.
- Counter holder and Cleave anchor use `post_redirect_actual_target`.
- Cleave secondaries do **not** rerun selector/Confusion/Taunt/Guard.
- Combo #2 allocates a fresh `NormalAttackInstanceId`, `TargetResolutionId`, selector pass and Guard pass. It keeps the same `ActionId/rootActionId` and locked Combo grant provenance.

Authority: Core Arbitration + CONFUSION / TAUNT / GUARD P0 + RF-C01 Target contracts.

---

## 10. NormalAttack Orchestration

### 10.1 Chosen master owner

**Existing `NormalAttackSystem` is extended into the unique master NormalAttack orchestrator.**

Reason: it already owns the production normal-attack entry and `ActionSystem` already depends on it. Creating a parallel `NormalAttackOrchestrator` would produce two lifecycle owners or force a compatibility facade with no engineering gain.

`NormalAttackSystem` becomes orchestration-first and delegates local work. It does not absorb mechanism algorithms.

### 10.2 Ownership

Master owns:

```text
normal-attack permission
NormalAttackInstanceId
TargetResolution
main DamageInstance dispatch
relative phase ordering
local-child admission points
CounterBatch window
Assault window ordering
Combo checkpoint reachability
completion barrier
```

Local mechanisms return typed facts/results. They may not advance the master lifecycle:

```text
ComboSystem cannot run main hit / Counter / Cleave
CounterSystem cannot dispatch next Combo
CleaveSystem cannot end Action
ChainSystem cannot finalize battle
```

### 10.3 Action relationship

`ActionSystem` owns `ActionId`, ActionStart maintenance/grant and Action-level cancellation. `NormalAttackSystem` owns each NormalAttack instance. This allows Combo #1/#2 to share one `ActionId` without sharing target/damage identities.

### 10.4 Assault seam

Current production has no Assault runtime. Stage9 defines a narrow `AssaultDispatchPort` contract only for ordering/admission. Default composition has no registered Assault producer. This is a system registration boundary, not a global gameplay boolean.

---

## 11. Combo

### 11.1 Runtime model

`ComboStateInstance` is a typed view over the physical `StateInstance` (690081), not a second state object store.

`ComboActionGrant`:

```python
ComboActionGrant(
    action_id,
    granting_instance_id,
    source_unit,
    source_skill,
    state=VALID | REVOKED_BY_PHYSICAL_REMOVE | CONSUMED,
)
```

`ComboCheckpointState`:

```text
NOT_REACHED | REACHED | CONSUMED | BLOCKED
```

Lifecycle:

```text
ACTION_START maintenance
→ effective Combo read
→ grant created if operational
→ physical REMOVE of granting instance before consume = revoke
→ ordinary SUPPRESS after valid grant = does not revoke this Action grant
→ checkpoint atomic consume = CONSUMED
→ Action end = dispose grant/checkpoint scope
```

### 11.2 Checkpoint seam

Conceptual API:

```python
try_run_combo_checkpoint(action_scope, first_normal_attack_result)
```

Required behavior:

```text
actor/action local gate permits reaching checkpoint
→ mark checkpoint REACHED exactly once
→ validate grant
→ atomic consume exactly once
→ emit cfg230-equivalent Combo execution fact
→ standard can_normal_attack() gate
→ can_admit_new_work(COMBO_SECOND_NORMAL_ATTACK)
→ allocate fresh NormalAttack #2 only if admitted
→ fresh target resolution / Guard
→ call same NormalAttackSystem with combo_checkpoint_allowed=False
```

Important authority nuance: a victory-latched path may still have a consumed checkpoint/cfg230 fact where P0 allows it, but **must never allocate or dispatch NormalAttack #2**. Actor death before checkpoint reach cancels the future branch and produces no dead-actor Combo consume path.

No consume refund/retry exists after atomic consume. Per Action:

```text
checkpoint reached <= 1
cfg230 / consume <= 1
physical NormalAttack <= 2
```

---

## 12. Damage Partition

### 12.1 Unified arbitration, separate transactions

`DamagePartitionCoordinator` unifies only qualification and typed result selection:

```text
DamageInstance + final actual DamageEvent target + Dtotal
→ exactly one effective plan
   NONE | SHARE | DISTRIBUTION
```

Share and Distribution transaction algorithms remain separate. No Stage9 engineering decision invents precedence; replacement/precedence follows current P0.

A `DamageInstanceId` can create at most one `PartitionTransactionId`.

### 12.2 Semantic damage layers

| Semantic layer | Stage9 / production mapping |
|---|---|
| `Dtotal` | standard path: immutable `DamageResult.final_damage` before partition; derived path: typed calculated input before partition |
| `Dtarget` | partition-plan field only; never overwrites `DamageResult.final_damage` |
| `ActualTargetTroopLoss` | target `TroopChangeResult.actual_change` at commit |
| `CreditedDamage` | attribution/statistics fact based on actual committed loss under P0 |
| `DerivedCalculatedDamage` | typed Cleave/Chain calculated amount before target clamp/settlement |
| `AttributedDirectTroopLoss` | non-DamageEvent direct-loss operation for Share/Distribution recipients |

### 12.3 DamageShareTransactionPlan

```python
DamageShareTransactionPlan(
    transaction_id,
    parent_damage_instance_id,
    target,
    sharer,
    dtotal,
    share_ratio,
    dsharer_theoretical,
    dtarget,
)
```

Arithmetic and commit:

```text
DsharerTheoretical = ROUND_HALF_UP(Dtotal × ShareRatio)
Dtarget = Dtotal - DsharerTheoretical

commit target Dtarget
→ target death check
→ if target died: TARGET_DEATH_INTERRUPT; pending sharer work discarded
→ else: commit sharer AttributedDirectTroopLoss
```

Theoretical vs actual sharer loss remains separate. Overflow is discarded.

### 12.4 DistributionTransactionPlan

```python
DistributionTransactionPlan(
    transaction_id,
    parent_damage_instance_id,
    target,
    participant_ids: tuple[str, ...],
    n,
    dtotal,
    ratio,
    dtarget,
    dtransfer,
    dparticipant,
    runtime_authority,
)
```

Plan creation is immutable:

```text
Dtarget = ROUND_HALF_UP(Dtotal × (1-ratio))
Dtransfer = Dtotal - Dtarget
Dparticipant = ROUND_HALF_UP(Dtransfer / N), N > 0
```

Execution follows Distribution P0 ordering. If a planned participant becomes invalid: `SKIP` only. Never change participant tuple, N, Dtarget or Dparticipant; never add a newly eligible participant; never repair remainder.

`DSTS9-B02` is implemented as a replaceable **Distribution local transaction policy**:

```text
PROJECT_RUNTIME_DEFAULT
NOT EMPIRICALLY PROVEN
commander participant death
→ admitted fixed transaction continues local planned work
→ finalization at transaction barrier
```

Replacing future evidence changes this local policy, not the global finalization architecture.

---

## 13. Attributed Direct Troop Loss

Formal type:

```python
AttributedDirectTroopLoss(
    direct_loss_id: DirectTroopLossId,
    partition_transaction_id: PartitionTransactionId,
    parent_damage_instance_id: DamageInstanceId,
    source_type: SHARE_DIRECT_LOSS | DISTRIBUTION_DIRECT_LOSS,
    physical_attacker: str | None,
    physical_skill: str | None,
    victim: str,
    credit_owner: str | None,
    theoretical_loss: int,
    actual_loss: int,
    lineage: OperationLineage,
)
```

`DirectTroopLossResolver`:

```text
validate typed provenance
→ call TroopSystem.apply_damage
→ clamp actual loss
→ create attributed loss fact
→ create UnitDeathFact if transition alive→dead
→ update attribution/statistics seam
```

It does **not** call:

```text
DamageSystem / DamageRequest
HitResolution
Defense / Reduction
Evasion / Resistance
FirstAid
Counter / Chain / Share / Distribution
base formulas
generic Hurt callbacks
```

This is the formal bypass path required by P0. EventBus may observe the result; subscriber callbacks cannot convert it back into a hit.

---

## 14. Cleave

### 14.1 State container

Cleave 690084 remains in the existing `StateRegistry`. `Stage9StateRuntime.cleave_effects(holder)` returns typed views of source-bound state instances.

Required metadata for a source-bound Cleave instance is carried in typed `StateRuntimeParams`, including authoritative apply-time `cleave_ratio` and `source_skill_slot` when the source contract requires slot ordering.

Container behavior references CLEAVE P0, not duplicated rules:

```text
SOURCE_BOUND_EFFECT_LIST
same-source REFRESH
cross-source COEXIST
SKILL_SLOT_ORDER
permanent / temporary duration
suppression
source death semantics
holder death semantics
```

Physical apply/remove/expiry still goes through `StateLifecycleSystem`.

### 14.2 Derived request

```python
DerivedDamageRequestCleave(
    damage_instance_id,
    cleave_effect_id,
    lineage,
    source_type=CLEAVE,
    damage_type=inherited_weapon_or_strategy,
    base_fact=ACTUAL_TARGET_TROOP_LOSS,
    base_amount,
    ratio,
    integerization=FLOOR,
    secondary_target,
    normal_attack_identity=False,
    permission_policy,
)
```

Calculation:

```text
CleaveDerivedCalculatedDamage
= FLOOR(ActualTargetTroopLoss × CleaveRatio)
```

No `WeaponBaseDamageFormula` / `StrategyBaseDamageFormula`, coefficient recomputation, target generic damage-modifier rerun, Crit reroll, selector, Guard, Combo or Counter identity is entered.

### 14.3 Derived downstream seam

`DerivedDamageSystem` owns Cleave's typed restricted path. It does not fabricate a Stage8 `DamageRequest`.

The policy supports P0-allowed downstream gates:

```text
Evasion / Resistance
one effective Share or Distribution partition
FirstAid
Chain
eligible recovery
Troop settlement
```

“ALLOW” means Stage9 must not structurally block an authoritative existing/future binding. It does **not** authorize Stage9 to invent deferred Evasion/Resistance mechanics currently outside their own evidence gate.

### 14.4 Queue and admission

Effect order:

```text
CleaveEffect A: secondary 1 → secondary 2
then
CleaveEffect B: secondary 1 → secondary 2
```

Each effect creates an immutable `secondary_identity_plan` ordered by `GLOBAL_SLOT_ASCENDING`. Each step revalidates JIT alive/legal state. No replacement and no revisit.

No secondary reruns Confusion/Taunt/Guard.

Admission grain is **one CleaveEffect**. Once admitted, the current effect follows its local P0 drain/gate behavior. After victory latch, a later independent effect not yet admitted is blocked. Attacker/holder liveness gates remain mechanism-local and may cancel work where CLEAVE P0 explicitly requires it.

Cleave anchor is `PostRedirectActualTarget`; a pre-Guard intended target may be an ordinary secondary if otherwise eligible.

---

## 15. Chain

### 15.1 ChainTraversal

`ChainSystem` owns one-pass traversal identified by `ChainTraversalId` and a `visited_slots` set keyed by stable battle slot, not Unit object address.

```text
slot visited → never revisit in traversal
later unvisited slot becomes linked before its turn → may join if live eligible
passed slot → never re-enter
```

### 15.2 ChainDeferredWork

```python
ChainDeferredWork(
    traversal_id,
    immutable_trigger_snapshot={
        parent_damage_instance_id,
        trigger_node_identity,
        trigger_damage,
        trigger_provenance,
    },
    live_execution_lookup={
        trigger_node_identity,
        chain_state_slot_key,
        candidate_side_key,
    },
    visited_slots,
)
```

Snapshot only:

```text
trigger damage
trigger node
parent/source provenance
```

Live execution read:

```text
trigger/source alive
current Chain state existence
current owner
current ratio/effect metadata
candidate alive
candidate linked
```

Main-target Chain is inline when no Cleave. When Cleave exists it is deferred while Cleave secondaries may trigger Chain inline, then main-target Deferred Chain executes if still locally eligible.

### 15.3 Restricted feedback

`CHAIN_TRUE_FEEDBACK` is not a standard Stage8 DamageRequest and does not inherit `DamageType`. Its restricted settlement blocks Chain recursion, Share, Distribution, Counter, FirstAid, Guard, Crit and recovery paths forbidden by P0.

Integerization is `FLOOR(TriggerNodeResolvedDamage × CurrentChainRatio)`.

---

## 16. Counter

### 16.1 CounterBatch admission

```python
CounterBatch(
    reaction_batch_id,
    parent_normal_attack_id,
    target_original_attacker,
    entries: tuple[CounterBatchEntry, ...],
)
```

Each entry:

```python
CounterBatchEntry(
    entry_id,
    reaction_batch_id,
    counter_instance_identity,
    owner,
    source,
    source_skill,
    damage_rate,
    batch_order,
)
```

At the trigger window, eligible Counter states and deterministic order are snapshotted. State suppression/removal/expiry after admission does not revoke an admitted entry.

### 16.2 Execution-time gates

Immediately before each entry:

```text
read owner alive?
read target alive?
read live combat stats/modifiers for standard Counter damage
```

- owner dead → `CANCELLED_BY_LOCAL_GATE`, no execution.
- target alive → create a legitimate independent Stage8 weapon `DamageRequest` with existing `DamageSourceType.COUNTER`, then use the Stage9 DamageInstance/partition/finalization path.
- target already dead → explicit terminal path:

```text
CounterExecute fact
→ attributed zero troop loss / zero terminal result
→ complete entry
```

The dead-target path never invokes Stage8 base formula, Evasion, Resistance, partition, Chain or FirstAid.

Counter is not NormalAttack identity, so Counter→Counter, Cleave and Assault are blocked even though Counter's positive-damage path is standard weapon damage.

Exact official universal Counter comparator/dispel fidelity is `DEFERRED_NON_BLOCKING`; project ordering remains deterministic and isolated behind the Counter comparator.

---

## 17. Execution Right

### 17.1 Semantic states

The architecture expresses:

```text
NOT_ADMITTED
ADMITTED_PENDING
EXECUTING
COMPLETED
CANCELLED_BY_LOCAL_GATE
CANCELLED_BEFORE_ADMISSION
```

These may be represented by typed local scopes/results rather than one giant mutable global enum.

### 17.2 FutureAdmissionGate

Conceptual API:

```python
can_admit_new_work(work_kind, operation_context, termination_state) -> bool
```

After `VICTORY_LATCHED`, block FutureBranches including:

```text
next Action
unadmitted Assault
NormalAttack #2
new CounterBatch
new unrelated ChainTraversal
next independent CleaveEffect not yet admitted
```

It does not retroactively erase work already admitted by the P0-defined trigger/admission point.

No mechanism may use scattered:

```python
if context.ended:
    return
```

as its semantic gate. `context.ended` is terminal compatibility state only after `FINALIZED`.

### 17.3 Operation barrier matrix

| Operation | Admission point | Completion boundary | Local gate | Finalization interaction |
|---|---|---|---|---|
| `DamageInstance` | dispatch accepted with valid lineage | target/direct settlement + permitted local callbacks complete | participant legality / typed permission | death fact may latch victory; instance completes current boundary |
| `ShareTransaction` | partition plan created | target commit + survive/sharer commit OR target-death interrupt | sharer live before direct commit | local interrupt owns only transaction; then barrier notification |
| `DistributionTransaction` | fixed plan created | planned participant/target steps drained | each participant JIT validity; invalid=SKIP | admitted plan drains under P0 / DSTS9 default |
| `ChainTraversal` | Chain trigger admitted | one-pass traversal boundary | source/current state/candidate live reads | admitted traversal drains after victory latch |
| `CounterBatch` | trigger snapshot complete | all entries completed/cancelled locally | owner liveness; dead target zero terminal | admitted siblings remain; finalize after batch |
| `CleaveEffect` | effect admitted and secondary plan fixed | current effect plan traversed | attacker/secondary liveness per P0 | current effect local rule; next unadmitted effect blocked after latch |
| `NormalAttackInstance` | normal attack dispatch admitted | all authoritative pre-completion synchronous work done | actor/target permission | future Assault/Combo admission may be blocked |
| `Action` | ActionOrder entry passes action-start gate | Action end barrier | actor action permission | no new Action after latch |

---

## 18. Battle Finalization

### 18.1 Unique owner

New `BattleFinalizationCoordinator` is the only writer of the global termination state and the only component permitted to transition to `FINALIZED`.

`VictorySystem` remains the pure evaluator of current victory conditions / max-round result. It does not finalize the battle by itself.

### 18.2 State

```text
RUNNING
→ VICTORY_LATCHED
→ DRAINING_ADMITTED_WORK
→ FINALIZED
```

A small `BattleTerminationRecord` is stored per `BattleContext` because it is truly cross-mechanism battle state. It contains only the termination enum, latched result/condition provenance, and idempotency metadata; it is not a generic Stage9 context bag.

Read access is available to admission policies. Write access belongs only to `BattleFinalizationCoordinator`.

### 18.3 Fact separation

```text
Troop mutation/death detector
→ UnitDeathFact

VictorySystem
→ VictoryConditionSatisfied

BattleFinalizationCoordinator
→ Victory latch / drain state / BattleFinalized
```

These are never collapsed into one boolean.

`BattleEngine._finish` becomes an outer compatibility/phase publication step invoked only after the coordinator reports `FINALIZED`; no damage/reaction subsystem calls it.

### 18.4 Idempotency

- repeated observation of the same death fact cannot create a second latch;
- `FINALIZED → FINALIZED` is rejected or no-op only when the same finalization identity/result is supplied; conflicting duplicate write is a domain error;
- only one `BATTLE_ENDED` terminal fact is emitted.

---

## 19. Recursion / Permission Policy

`ReactionPermissionPolicy` is a centralized typed table over `SourceType`, `NormalAttackIdentity` and `OperationLineage`. Mechanism code asks the policy; it does not scatter `if source == ...` branches.

Minimum matrix:

| From | Cleave | Counter | Chain | Share | Distribution | FirstAid / Recovery |
|---|---:|---:|---:|---:|---:|---:|
| NORMAL_ATTACK | ALLOW by trigger P0 | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW where existing recovery P0 permits |
| CLEAVE | BLOCK | BLOCK | ALLOW | ALLOW | ALLOW | ALLOW by Cleave P0 |
| COUNTER | BLOCK | BLOCK | ALLOW | ALLOW | ALLOW | ALLOW by Counter P0 |
| CHAIN_TRUE_FEEDBACK | N/A/BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK |
| SHARE_DIRECT_LOSS | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK |
| DISTRIBUTION_DIRECT_LOSS | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK |

NormalAttack-only target selection, Guard, Assault and Combo are available only to `NormalAttackIdentity=true`; derived/reaction damage cannot reopen them.

Illegal recursive dispatch that contradicts this table is a domain error in tests/debug builds and a hard blocked result in production policy, with a trace record. It is not silently reinterpreted as another source type.

---

## 20. Integerization

Stage9 introduces pure explicit numeric helpers, for example:

```python
floor_damage(exact_value) -> int
round_half_up_damage(exact_value) -> int
```

Implementation must use deterministic decimal/rational semantics appropriate to authoritative inputs and must not delegate gameplay semantics to Python `round()` or environment-dependent default rounding.

Call-site matrix:

| Call site | Rule |
|---|---|
| Chain | `FLOOR` |
| Cleave | `FLOOR` |
| Share `Dsharer` | `ROUND_HALF_UP` |
| Distribution `Dtarget` | `ROUND_HALF_UP` |
| Distribution participant | `ROUND_HALF_UP` |

Regression vectors in RF-C01 are the executable oracle.

---

## 21. State Runtime Integration

### 21.1 No second state runtime

Stage9 state truth remains:

```text
BattleContext.states : StateRegistry
StateLifecycleSystem : only physical apply/remove/expiry writer
```

`Stage9StateRuntime` is a typed read/maintenance adapter, not a second store.

Responsibilities:

- resolve Stage9 `StateInstance` into mechanism-specific typed views;
- deterministic source-bound ordering;
- compute operationality/suppression using current P0;
- perform ACTION_START maintenance by calling `StateLifecycleSystem.remove/apply` as required;
- create Action-local Combo grants outside physical state storage;
- expose indexed lookup hooks so implementation does not repeatedly scan all battle history.

### 21.2 Typed runtime params

New `stage9_state_params.py` carries only data required by P0, such as:

```text
Cleave: ratio, source_skill_slot, duration metadata where required
Counter: damage rate, source_skill_slot/order metadata where authoritative
Distribution: ratio + source binding metadata
DamageShare: ratio + sharer/source binding metadata
Chain: ratio + owner/source metadata
Guard/Taunt/Confusion/Combo: only parameters actually required by their P0
```

`source_id`, `source_skill_id`, apply/expiry anchors remain existing `StateInstance` fields where already modeled. Do not duplicate them gratuitously.

### 21.3 Lifecycle

Apply/reapply/duration/suppression/source death/holder death semantics are referenced from each mechanism P0. STAGE9.md does not rewrite those contracts.

---

## 22. Recovery / Trigger Integration

Stage9 does not redesign Stage7 Trigger/Recovery.

- `TriggerSystem` stays a fact-to-Effect collector at typed hooks.
- `RecoverySystem` stays recovery execution owner and `TroopSystem.restore` remains the write boundary.
- EventBus facts may be observed by report/trace code; core Stage9 sequencing never depends on subscriber order.

Damage-event eligibility:

```text
NormalAttack standard damage: existing eligible recovery hooks by P0
Counter positive standard DamageEvent: Lifesteal / StrategyRecovery / FirstAid where Counter P0 allows
Cleave derived DamageEvent: eligible recovery / FirstAid where Cleave P0 allows
Chain TRUE_FEEDBACK: blocked where Chain P0 blocks
Share/Distribution AttributedDirectTroopLoss: NEVER recovery damage basis
Counter dead-target zero terminal: no damage basis
```

`CreditedDamage` and recovery basis use the precise mechanism P0 layer, not a generic `final_damage` alias.

---

## 23. Trace & Observability

### 23.1 Stage9OperationTrace

New test/diagnostic trace records typed immutable observations:

```text
Action admitted/completed/cancelled
NormalAttackInstance created/completed
TargetResolution result
DamageInstance created/calculated/settled
Partition selected/transaction steps
Derived damage calculation
CounterBatch admission/entry result
ChainTraversal slots
CleaveEffect admission/secondary result
FutureAdmission decision
Victory latch
Finalization
```

Minimum IDs in records:

```text
ActionId
NormalAttackInstanceId
TargetResolutionId
DamageInstanceId
PartitionTransactionId
ReactionBatchId / CounterBatchEntryId
CleaveEffectId
ChainTraversalId
DirectTroopLossId
```

Trace is **observability only**. Runtime code may write to a `Stage9TraceSink`; it may never query previous trace contents to make gameplay decisions.

### 23.2 EventBus rule

```text
Event = observation / notification
Coordinator call = authoritative control flow
```

New facts such as victory latch/direct loss may be published for reporting, but the coordinator must already have made the decision.

### 23.3 Error policy

| Fault | Handling |
|---|---|
| invalid operation identity / wrong parent | domain error / assertion |
| missing required provenance | constructor/domain error |
| illegal recursive dispatch | permission denial + diagnostic assertion/test failure |
| double Guard resolution | domain error |
| double Combo checkpoint/consume | domain error |
| duplicate partition plan for one DamageInstance | domain error |
| duplicate CounterBatch admission | domain error |
| conflicting duplicate finalization | domain error |
| P0-defined dead/invalid planned member | safe typed SKIP/cancel result |

---

## 24. Runtime Invariants

All 42 RF-C01 invariants are mapped. “Structural” means the type/control-flow shape prevents the invalid state; “runtime” means an explicit guard/assertion is required; “test” means a regression/golden trace proves behavior.

| Invariant | Enforcement |
|---|---|
| INV-01 | structural: frozen typed target fields; test |
| INV-02 | structural TargetResolution pipeline; test |
| INV-03 | runtime one Guard pass per `NormalAttackInstanceId`; test |
| INV-04 | structural downstream APIs accept actual target identity; test |
| INV-05 | structural per-DamageInstance recipient; test |
| INV-06 | allocator + fresh TargetResolution for #2; test |
| INV-07 | separate StateInstance / grant / checkpoint types |
| INV-08 | ActionSystem ordering structural; test |
| INV-09 | grant transition runtime guard; test |
| INV-10 | checkpoint idempotency runtime assertion; test |
| INV-11 | atomic consume idempotency assertion; test |
| INV-12 | `combo_checkpoint_allowed=False` on #2 + test |
| INV-13 | derived Cleave type fixes `normalAttackIdentity=false` |
| INV-14 | constructor requires `ActualTargetTroopLoss`; test |
| INV-15 | explicit `floor_damage`; unit test |
| INV-16 | DerivedDamageSystem has no base-formula/modifier call edge; architecture test |
| INV-17 | ReactionPermissionPolicy; test |
| INV-18 | immutable effect/secondary plans + comparators + JIT test |
| INV-19 | separate `AttributedDirectTroopLoss` type |
| INV-20 | DirectTroopLossResolver has no DamageSystem/HitResolution dependency; architecture test |
| INV-21 | required provenance constructor fields + trace test |
| INV-22 | partition enum/result exactly one; runtime assertion + test |
| INV-23 | state replacement lifecycle P0 adapter; test |
| INV-24 | Share transaction method order structural; test |
| INV-25 | target-death terminal enum; test |
| INV-26 | separate theoretical/actual fields; test |
| INV-27 | frozen tuple + N in Distribution plan; test |
| INV-28 | frozen calculated fields; test |
| INV-29 | typed participant `SKIP`; test |
| INV-30 | plan has no add/replan operation; test |
| INV-31 | `runtime_authority=PROJECT_RUNTIME_DEFAULT`; regression + trace label |
| INV-32 | ChainDeferredWork snapshot schema restricts fields; test |
| INV-33 | live lookup performed at execute; test |
| INV-34 | visited-slot set + deterministic loop; test |
| INV-35 | `CHAIN_TRUE_FEEDBACK` permission set; architecture/test |
| INV-36 | CounterBatch entries frozen tuple; test |
| INV-37 | separate admission and owner-liveness result; test |
| INV-38 | explicit zero-loss terminal result; architecture/test |
| INV-39 | separate UnitDeathFact / latch / finalized types/state; test |
| INV-40 | FutureAdmissionGate + local operation barrier matrix; test |
| INV-41 | only BattleFinalizationCoordinator writes FINALIZED; architecture/test |
| INV-42 | SourceType + lineage + IDs + centralized permission; architecture/test |

```text
Mapped = 42
Unmapped = 0
Contradiction = 0
```

---

## 25. Regression Mapping

Future Stage9 tests use minimal deterministic fixtures first; battle-report compatibility fixtures may be added as a higher-level validation layer but are not the only oracle.

Test layers:

```text
unit        → integerization, plan construction, permission, IDs
integration → target/NormalAttack/partition/reaction/finalization
trace       → cross-operation ordering/admission/finalization identity
```

| Regression ID | Planned test | Fixture needed | Core assertion |
|---|---|---|---|
| REG-TGT-01 | `test_stage9_target_resolution.py` | Confusion + Taunt actor | Confusion selector wins only current selection |
| REG-TGT-02 | same | shadowed Taunt across attacks | Taunt lifecycle remains |
| REG-TGT-03 | same | B guarded by C | intended=B, actual=C |
| REG-TGT-04 | same | B→C guard, C→D guard | exactly one redirect |
| REG-TGT-05 | same | Combo #2 changed legality | fresh NA/target IDs |
| REG-TGT-06 | same | Guard changes between hits | #2 reruns Guard |
| REG-TGT-07 | same | B intended, C guard | B may be Cleave secondary |
| REG-CMB-01 | `test_stage9_combo.py` | expiring Combo at ActionStart | no grant after maintenance |
| REG-CMB-02 | same | remove granting instance | grant revoked before consume |
| REG-CMB-03 | same | suppress after grant | current grant retained |
| REG-CMB-04 | same | consume then #2 gate fail | no refund / cfg230 once / <=2 attacks |
| REG-CMB-05 | same | attacker dies in #1 downstream | no future Assault/#2/cfg230 path |
| REG-CLV-01 | `test_stage9_cleave.py` | target 55, ratio 54% | base 55, result 29 |
| REG-CLV-02 | same | derived request with formula spies | no base/modifier/Crit re-entry |
| REG-CLV-03 | same | permission spies | allow/block matrix exact |
| REG-CLV-04 | same | effects A/B + later dead secondary | effect-major + JIT skip |
| REG-CLV-05 | same | Guard B→C | Cleave anchor C |
| REG-CHN-01 | `test_stage9_chain.py` | old 20%, new live 30%, trigger 500 | snapshot trigger + live ratio |
| REG-CHN-02 | same | dynamic later slot link | one-pass, later unvisited may join |
| REG-CHN-03 | same | commander death mid traversal | current traversal drains before finalization |
| REG-CHN-04 | same | feedback permission spies | restricted settlement only |
| REG-SHR-01 | `test_stage9_partition.py` | nonlethal Share | target first then sharer direct loss |
| REG-SHR-02 | same | lethal target | pending sharer discarded |
| REG-SHR-03 | same | callback spies on sharer loss | direct loss is not hit |
| REG-SHR-04 | same | Distribution replaced by Share | one partition; no resurrection |
| REG-DST-01 | same | plan `[P1,P2]`, P2 invalid | SKIP, no recompute |
| REG-DST-02 | same | ordinary participant dies | fixed plan continues |
| REG-DST-03 | same | commander participant dies | labeled project default drains plan |
| REG-DST-04 | same | participant direct loss | not a DamageEvent |
| REG-CTR-01 | `test_stage9_counter.py` | admitted entry then state removed | entry retained |
| REG-CTR-02 | same | owner dies before entry | local cancel only |
| REG-CTR-03 | same | C1 kills commander, C2 admitted | C2 zero terminal then finalize |
| REG-CTR-04 | same | target dead before sibling | no Stage8 weapon pipeline |
| REG-CTR-05 | same | Counter kills original actor | future Assault/Combo cancelled |
| FINAL_01_CHAIN_COMMANDER_DEATH | `test_stage9_finalization.py` | Chain traversal commander kill | latch→drain traversal→finalize |
| FINAL_02_COUNTER_SIBLING | same | admitted C1/C2 | sibling drains after latch |
| FINAL_03_COMBO_BATTLE_END | same | #1 victory | no #2 allocation/target resolution |
| FINAL_04_CLEAVE_COMMANDER_SECONDARY | same | current effect secondary commander kill | current effect local drain; next effect blocked |
| FINAL_05_SHARE_COMMANDER_TARGET | same | lethal commander target Share | local death interrupt then finalize |
| FINAL_06_DISTRIBUTION_COMMANDER_PARTICIPANT | same | commander participant | runtime-default transaction drain |
| REG-INT-01 | `test_stage9_integerization.py` | 396 × 28.28% | FLOOR = 111 |
| REG-INT-02 | same | 470 × 15% | HALF_UP=71; target=399 |
| REG-INT-03 | same | 251 × 50% | target HALF_UP=126 |
| REG-INT-04 | same | 353 / 2 | participant HALF_UP=177, no repair |
| REG-INT-05 | same | 55 × 54% | Cleave FLOOR=29 |

Additional `tests/test_stage9_golden_trace.py` will prove cross-mechanism operation identity/order without replacing the 45 semantic contracts.

```text
Target          = 7/7
Combo           = 5/5
Cleave          = 5/5
Chain           = 4/4
Share           = 4/4
Distribution    = 4/4
Counter         = 5/5
Finalization    = 6/6
Integerization  = 5/5
TOTAL           = 45/45
Unmapped        = 0
Semantic Conflict = 0
```

---

## 26. Source File Plan

All paths use the real flat `sgs_v2/battle_core/` package layout.

### 26.1 NEW production files

| File | Responsibility | Authority/dependencies | Primary future tests |
|---|---|---|---|
| `operation_identity.py` | typed IDs, allocator, SourceType, lineage | RF-C01 | identity/trace |
| `stage9_trace.py` | observation-only trace sink/records | RF-C01 | golden trace |
| `stage9_integerization.py` | FLOOR / ROUND_HALF_UP helpers | RF-P01 + mechanism P0 | integerization |
| `stage9_state_params.py` | typed state runtime metadata | mechanism P0 | state/Combo/Cleave/Counter |
| `stage9_state_runtime.py` | typed StateRegistry adapter + ActionStart maintenance | mechanism P0 + Stage3/4 lifecycle | state integration |
| `target_resolution_system.py` | selector policies + single Guard pass + immutable result | Core + Confusion/Taunt/Guard P0 | target |
| `reaction_permission_policy.py` | centralized recursion/callback matrix | Core + RF-C01 | permission |
| `execution_right_system.py` | work kinds, admission decisions, operation barriers | RF-P03/RF-P04 | finalization |
| `damage_instance_coordinator.py` | standard Stage8 damage → partition → settlement orchestration | Stage8 + RF-C01 | partition/integration |
| `damage_partition_system.py` | exactly-one resolver + Share/Distribution plans | Share/Distribution P0 | partition |
| `direct_troop_loss_system.py` | attributed direct-loss settlement | Share/Distribution P0 | partition |
| `derived_damage_system.py` | typed Cleave derived path / derived settlement interfaces | CLEAVE P0/RF-P06 | Cleave |
| `cleave_system.py` | source-bound effects, queue, secondary plans/admission | CLEAVE P0/RF-P07/RF-P04 | Cleave |
| `chain_system.py` | traversal/deferred work/restricted feedback | CHAIN P0 | Chain |
| `counter_system.py` | CounterBatch/entries/live gates/zero terminal | COUNTER P0 | Counter |
| `battle_finalization_coordinator.py` | termination state owner, latch/drain/finalize | RF-P04 | finalization |

Planned new production files: **16**.

### 26.2 MODIFY production files

| File | Planned change | Semantic constraint |
|---|---|---|
| `context.py` | add typed per-battle ID allocator + small termination record | no giant Stage9Context |
| `battle_systems.py` | compose/inject Stage9 systems | composition only |
| `engine.py` | use finalization coordinator at macro barriers | no mechanism logic in engine |
| `action_system.py` | ActionId, ActionStart maintenance/grant, master dispatch | preserve Stun/action ownership |
| `normal_attack_system.py` | become master orchestration owner, delegate local work | no mechanism algorithm duplication |
| `damage_resolution_system.py` | narrow assigned-target settlement seam preserving original DamageResult | no Stage8 calculation change |
| `effect_executor.py` | route standard DamageEffect through DamageInstanceCoordinator | no Trigger semantics change |
| `victory_system.py` | pure condition evaluation API + compatibility wrapper | finalization ownership moves to coordinator, victory rules unchanged |
| `official_state_catalog.py` | bind Stage9 typed runtime param types where required | IDs/text unchanged |
| `events.py` | add Stage9 observation facts if needed | EventBus never controls flow |
| `__init__.py` | export intentionally public Stage9 types only | minimize public surface |

Planned modified production files: **11**.

Existing control-flow classes planned for modification: **8** (`BattleContext`, `BattleSystems`, `BattleEngine`, `ActionSystem`, `NormalAttackSystem`, `DamageResolutionSystem`, `EffectExecutor`, `VictorySystem`).

### 26.3 DO NOT TOUCH Stage8 semantics

```text
damage_system.py formula semantics
damage_prevention_system.py
hit_resolution_system.py semantics
damage_formula_policy_system.py
damage_modifier_system.py
weapon_damage_formula.py
strategy_damage_formula.py
damage_pipeline_trace.py meaning
random_system.py PRNG contract
attribute_system.py final-attribute ownership
recovery_system.py recovery semantics
trigger_system.py trigger semantics
```

If implementation discovers that one of these semantic owners must materially change, Stage9 implementation stops and requests a formal authority/reopen decision rather than silently editing it.

### 26.4 Future test files

Planned Stage9 test groups:

```text
tests/test_stage9_operation_identity.py
tests/test_stage9_target_resolution.py
tests/test_stage9_combo.py
tests/test_stage9_partition.py
tests/test_stage9_cleave.py
tests/test_stage9_chain.py
tests/test_stage9_counter.py
tests/test_stage9_finalization.py
tests/test_stage9_integerization.py
tests/test_stage9_golden_trace.py
```

This authoring round creates none of them.

---

## 27. Existing System Impact Matrix

| Existing component | KEEP / MODIFY | Integration contract |
|---|---|---|
| BattleEngine | MODIFY | outer phase loop retained; no direct low-level death finalization |
| BattleContext | MODIFY | only stable cross-mechanism ID/termination infrastructure |
| BattleSystems | MODIFY | single composition root |
| ActionSystem | MODIFY | Action scope owner; does not own reaction internals |
| NormalAttackSystem | MODIFY | unique NormalAttack master owner |
| TargetSystem | KEEP | target candidate/RNG primitives only |
| DamageSystem | KEEP | Stage8 theoretical pipeline owner |
| DamageResolutionSystem | MODIFY | backward-compatible settlement seam only |
| TroopSystem | KEEP | only troop mutation writer |
| VictorySystem | MODIFY | condition evaluator, not finalization writer |
| EventBus | KEEP | observation only |
| State system | KEEP + adapter | StateRegistry/StateLifecycle remain single truth/write path |
| Trigger system | KEEP | no anonymous subscriber-based Stage9 master flow |
| Recovery system | KEEP | Stage7 recovery owner; Stage9 controls event eligibility only |
| EffectExecutor | MODIFY | standard DamageEffect cannot bypass Stage9 partition/finalization seam |
| RandomSystem | KEEP | sole RNG |
| AttributeSystem | KEEP | live combat stats source |

Minimal-intrusion test: no design requires edits to twenty Stage8 formula entrances. The main integration is composition + orchestration around existing boundaries.

---

## 28. Implementation Phases

Every phase must end with a green build, all pre-Stage9 tests green, and the phase's new regression subset green. No Big Bang merge is permitted.

### Phase 9.1 — Foundation / Identity / Provenance

**Goal:** strong IDs, lineage, SourceType, trace sink, integerization, state params.  
**Files:** new identity/trace/integerization/state-param files; narrow `context.py`/exports.  
**New Types:** all operation IDs, allocator, `OperationLineage`, `SourceType`, numeric helpers.  
**Modified Systems:** BattleContext only for stable per-battle infra.  
**Dependencies:** RF-C01, RF-P01.  
**Tasks:** implement constructors/validation/serialization; trace must be write-only from gameplay perspective.  
**Required Tests:** identity uniqueness, lineage validation, five integerization vectors.  
**Exit Gate:** deterministic IDs; REG-INT-01..05 pass; old tests green.  
**Forbidden Scope:** target/mechanism behavior.

### Phase 9.2 — State Adapter + Target Arbitration + Guard

**Goal:** typed Stage9 state views and immutable target-resolution pipeline.  
**Files:** state runtime/params, target resolution, catalog binding, BattleSystems wiring.  
**New Types:** `TargetResolutionResult`, redirect reason, selector policies.  
**Modified Systems:** catalog/composition only; `TargetSystem` remains unchanged.  
**Dependencies:** 9.1, Confusion/Taunt/Guard P0.  
**Tasks:** selector precedence, Guard once, deterministic result/trace, ActionStart maintenance primitives.  
**Required Tests:** REG-TGT-01..04 plus state adapter tests.  
**Exit Gate:** immutable identity and Guard single-pass proven.  
**Forbidden Scope:** Combo/Cleave/partition.

### Phase 9.3 — NormalAttack Master + Combo

**Goal:** make existing NormalAttackSystem the single orchestration owner and add Action-local Combo model.  
**Files:** ActionSystem, NormalAttackSystem, state runtime, execution-right initial seam.  
**New Types:** `ActionScope`, `NormalAttackInstance`, Combo grant/checkpoint.  
**Modified Systems:** ActionSystem / NormalAttackSystem.  
**Dependencies:** 9.1-9.2.  
**Tasks:** #1 lifecycle shell, fresh #2, no recursive checkpoint, Assault dispatch port ordering.  
**Required Tests:** REG-TGT-05..07, REG-CMB-01..05.  
**Exit Gate:** one Action has <=2 attacks; fresh target/Guard #2; old normal-attack tests green.  
**Forbidden Scope:** mechanism math not yet implemented.

### Phase 9.4 — DamageInstance / Partition / DirectTroopLoss

**Goal:** one standard DamageInstance path with exactly-one partition and typed direct loss.  
**Files:** damage coordinator, partition, direct loss; narrow DamageResolutionSystem/EffectExecutor wiring.  
**New Types:** partition plans/results, direct-loss type, damage execution result.  
**Modified Systems:** DamageResolutionSystem / EffectExecutor / BattleSystems.  
**Dependencies:** 9.1 identity; Stage8 frozen seam.  
**Tasks:** preserve `DamageResult`; Share target-first; Distribution fixed plan; provenance.  
**Required Tests:** REG-SHR-01..04, REG-DST-01..04 except finalization-specific full barrier may use stub latch.  
**Exit Gate:** one partition only; direct loss cannot enter hit pipeline; old Stage8 tests green.  
**Forbidden Scope:** alter Stage8 formula/modifier semantics.

### Phase 9.5 — Cleave + Chain

**Goal:** derived Cleave path and Chain traversal/deferred split.  
**Files:** derived damage, Cleave, Chain, permission policy.  
**New Types:** Cleave effect/plan/request, ChainTraversal/DeferredWork.  
**Modified Systems:** NormalAttack orchestration wiring only.  
**Dependencies:** 9.2 target identity, 9.4 partition, 9.1 numeric/lineage.  
**Tasks:** ActualTargetTroopLoss base; effect-major; JIT; Chain inline/deferred; restricted feedback.  
**Required Tests:** REG-CLV-01..05, REG-CHN-01..04.  
**Exit Gate:** no formula re-entry; one-pass traversal; permission matrix enforced.  
**Forbidden Scope:** implement deferred Evasion/Resistance gameplay without authority.

### Phase 9.6 — CounterBatch

**Goal:** trigger-time admission snapshot + execution-time local gates + zero terminal.  
**Files:** counter system, permission policy, NormalAttack wiring.  
**New Types:** CounterBatch/Entry/terminal result.  
**Modified Systems:** composition/NormalAttack only.  
**Dependencies:** 9.3 NA identity, 9.4 standard damage path, 9.5 permission framework.  
**Tasks:** final-actual-target holder, immutable batch, live stats, target-dead zero path.  
**Required Tests:** REG-CTR-01..05.  
**Exit Gate:** admitted siblings stable; no dead-target Stage8 request.  
**Forbidden Scope:** claim exact official universal comparator fidelity.

### Phase 9.7 — Execution Right + Finalization

**Goal:** explicit victory latch/drain/finalization and remove scattered battle-end control from mechanism paths.  
**Files:** execution right, finalization coordinator; BattleEngine/VictorySystem/context/events wiring.  
**New Types:** termination state/record, UnitDeathFact, admission decisions, barriers.  
**Modified Systems:** Engine / VictorySystem / Action/NormalAttack integration.  
**Dependencies:** 9.3-9.6 operation barriers exist.  
**Tasks:** latch once; future admission gate; DSTS9 local policy; terminal publication.  
**Required Tests:** FINAL_01..06 plus golden state-transition traces.  
**Exit Gate:** only finalization coordinator writes FINALIZED; all finalization regressions pass; pre-Stage9 victory tests green.  
**Forbidden Scope:** empirical research for DSTS9-B02.

### Phase 9.8 — Full Regression / Integration

**Goal:** close all 42 invariants and 45 contracts against full composed runtime.  
**Files:** Stage9 test groups only unless defects require authority-consistent fixes.  
**New Types:** none by default.  
**Modified Systems:** only defect fixes within frozen design.  
**Dependencies:** 9.1-9.7.  
**Tasks:** unit + integration + golden trace, battle-report compatibility fixtures as supplemental checks, performance sanity.  
**Required Tests:** 45/45 contracts, invariant architecture tests, all existing tests, demo/CI.  
**Exit Gate:** existing tests all green; new Stage9 suite green; invariant mapped/verified 42/42; regression 45/45.  
**Forbidden Scope:** new mechanism research or semantic expansion.

---

## 29. Research Debt

### 29.1 DSTS9-B02

```text
RESEARCH_DEBT
NON_BLOCKING
RUNTIME DEFAULT INSTALLED

Empirical: OPEN / UNOBSERVED
Runtime: CLOSED BY PROJECT_RUNTIME_DEFAULT
```

Implementation isolates this in the Distribution local transaction policy:

```text
commander participant death during admitted fixed plan
→ continue locally planned transaction
→ finalization at transaction barrier
```

Future evidence may replace that local policy and its regression expectation without rewriting `BattleFinalizationCoordinator`, operation identities, partition planning, or Stage8.

### 29.2 Counter fidelity

```text
exact official universal comparator fidelity = DEFERRED_NON_BLOCKING
universal dispel fidelity                    = DEFERRED_NON_BLOCKING
```

Neither is a Stage9 spec blocker because current reachable runtime remains deterministic.

---

## 30. Acceptance Gate

### 30.1 Authoring self-audit

```text
Authority Trace Audit       = PASS
Stage8 Boundary Audit       = PASS
42 Invariant Coverage Audit = PASS (42/42)
45 Regression Mapping Audit = PASS (45/45)
File Plan Completeness      = PASS
Dependency Cycle Audit      = PASS
P0 Semantic Drift Audit     = PASS (0)
```

Dependency direction intentionally remains:

```text
identity/state/policy
→ target/damage local services
→ mechanism local systems
→ NormalAttack master
→ Action / Engine
→ Finalization owner
```

Mechanism-local systems do not import the master to advance its lifecycle. Finalization does not import mechanism implementations; it consumes operation/admission facts.

### 30.2 Authoring gate

```text
Stage8 reopen                    = NO
P0 semantic drift                = 0
unmapped invariants              = 0
unmapped regressions             = 0
production changes this round    = 0
test changes this round          = 0
DSTS9-B02 blocker                = NO
```

### 30.3 Public surface

Intended Stage10+ stable/public concepts are deliberately small:

```text
ActionId / NormalAttackInstanceId / DamageInstanceId
OperationLineage / SourceType
TargetResolutionResult
BattleTerminationState read view
Future admission query/port where later stages need ordered dispatch
```

Mechanism queue internals, mutable transaction states, grant/checkpoint implementation classes, trace storage internals and local policy helpers remain Stage9-internal unless a later design explicitly promotes them.

### 30.4 Current document status

```text
STAGE9.md
STATUS: DRAFT — DESIGN AUDIT REQUIRED

NOT FROZEN
NOT READY FOR IMPLEMENTATION
```

Next permitted step:

```text
Stage9 Design Audit Round 1
```

Do not create `STAGE9_BUILD_PROMPT.md` and do not begin production implementation before the design audit/freeze workflow authorizes it.
