# STAGE 9 — Cross-Mechanism Runtime Orchestration

> STATUS: **DRAFT — DESIGN AUDIT REQUIRED**  
> Authoring baseline (battle): `4745d061345181aaf12c454ada9890d7b69c5598`  
> Round1 repair baseline (battle): `05512d198c9016410ca14be2e40eb0c913cd1b77`  
> Authority baseline (state): `15ed915435f328a6ecd8f488d98b5b9e13c913b5`  
> Authoring date: 2026-09-13  
> Round1 repair date: 2026-09-13  
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
STAGE9.md derived from RF-C01

Regression Semantic Authority
=
RF-C01 regression contracts + current P0
```

`STAGE9.md` does not redefine gameplay. It may only consume, organize, map, and implement frozen rules.

Authority priority:

```text
1. newest formal mechanism/shared P0
2. RF-P01..RF-P07 re-freeze records
3. STAGE9_CORE_ARBITRATION_RULES_V2
4. RF-C01 runtime contracts / invariants / regressions
5. STAGE9_AUTHORITY_MAP
6. historical audit/research only as provenance
```

If a gameplay-affecting design cannot be uniquely derived from the authority set, implementation stops at:

```text
SPEC BLOCKED BY AUTHORITY GAP
```

No implementation convenience may silently become a gameplay rule.

### 0.2 Current admission state

```text
Round1 design audit       = COMPLETE / FAIL — REPAIR REQUIRED
Round1 design repair      = COMPLETE IN THIS SPEC REVISION
Round2 design audit       = NOT EXECUTED
Stage9 FROZEN             = NO
Ready for implementation  = NO
STATUS                    = DRAFT — DESIGN AUDIT REQUIRED
```

`DSTS9-B02` remains deliberately dual-status:

```text
EMPIRICAL: OPEN / UNOBSERVED
RUNTIME: CLOSED BY PROJECT_RUNTIME_DEFAULT
DESIGN: NOT BLOCKING
RESEARCH DEBT: YES
```

This document never relabels that project runtime default as empirically proven official behavior.

### 0.3 Stage8 boundary

```text
Stage8 = FROZEN
Formal Stage8 Reopen = NO
```

Stage9 wraps, coordinates, redirects, partitions, derives, schedules, settles assigned target amounts, and finalizes around frozen Stage8 seams. It does not replace or reinterpret Stage8 formulas.

---

## 1. Goals

Stage9 turns frozen cross-mechanism semantics into an implementable runtime architecture with:

- one explicit NormalAttack lifecycle owner;
- strong operation identity and source provenance;
- deterministic ordering with project defaults clearly labeled;
- a typed `Dtotal -> Dtarget -> ActualTargetTroopLoss` settlement chain;
- one global future-admission seam per future branch;
- one semantic finalization owner;
- an acyclic dependency graph;
- independently green implementation phases;
- test seams for all 42 invariants and 45 mandatory regressions.

The design must make these questions answerable from types and call sites:

```text
Which Action / NormalAttack / DamageInstance owns this work?
Which target identity applies at this phase?
Is work not admitted, admitted, executing, locally cancelled, or completed?
Which exact damage layer is being consumed?
Which callbacks are legal for this source identity?
Has victory only latched, or is the battle FINALIZED?
```

Engineering rule:

```text
explicit orchestration > implicit event ordering
strong identity > booleans
single semantic owner > duplicate convenience owners
local typed policy > string inspection
exact numeric input > binary-float rounding accidents
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

Assault remains only an ordered/admitted dispatch seam because current production has no Assault runtime. Stage9 does not invent Assault gameplay semantics.

No global `enable_stage9=true` flag is introduced. Incremental implementation uses the composition root and real, completed phase-local services only. Production code must never route into a Stage9 placeholder/stub/TODO coordinator.

---

## 3. Frozen Inputs

Mandatory inputs remain:

- `stages/stage9/docsync/STAGE9_AUTHORITY_MAP.md`
- `stages/stage9/audits/STAGE9_GLOBAL_CROSS_MECHANISM_FINAL_AUDIT.md`
- `stages/stage9/audits/STAGE9_PRE_SPEC_DELTA_AUDIT.md`
- `stages/stage9/audits/STAGE9_DESIGN_AUDIT_ROUND1.md`
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
- current `sgs_v2/battle_core/` and `tests/` layout at the Round1 repair baseline.

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

`DAMAGE_SPLIT` is a production compatibility name only. Stage9 canonical terminology is **DISTRIBUTION**.

---

## 4. Stage8 Boundary and Damage Settlement Contract

### 4.1 Frozen Stage8 calculation pipeline

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
```

Frozen rules:

1. `DamageSystem.calculate()` remains the only standard Stage8 theoretical-damage entry.
2. `DamageResult.final_damage` **ALWAYS means the Stage8 final theoretical integer**. In Stage9 partition-eligible standard damage this is `Dtotal`.
3. `DamageResult.requested_damage` remains the existing compatibility alias of `final_damage`; it must never be redefined to mean `Dtarget`.
4. Stage9 never mutates or clones a `DamageResult` merely to overwrite `final_damage` with a partitioned amount.
5. Stage8 formula classes, prevention semantics, formula policy, modifier ownership, `DamagePipelineTrace`, and frozen base formulas are **DO NOT TOUCH**.
6. Stage9 exact-ratio helpers apply only at Stage9 P0 integerization call sites; the Stage8 float formula pipeline is not converted wholesale.

### 4.2 Unique settlement request — `DamageSettlementRequest`

Assigned target settlement is represented by a typed command, never an optional positional amount on `apply_result()`.

```python
DamageSettlementRequest(
    damage_result: DamageResult,                  # immutable Stage8 result; final_damage == Dtotal
    assigned_target_damage: int,                 # Dtarget submitted to TroopSystem
    damage_instance_id: DamageInstanceId | None, # required for STAGE9 origin
    lineage: OperationLineage | None,             # required for STAGE9 origin
    origin: SettlementOrigin,                    # STAGE9 | LEGACY_COMPAT
)
```

Validation:

```text
origin == STAGE9
→ damage_instance_id != None
→ lineage != None

origin == LEGACY_COMPAT
→ damage_instance_id == None
→ lineage == None
→ assigned_target_damage == damage_result.final_damage

assigned_target_damage >= 0
```

A Stage9 standard path may never use `LEGACY_COMPAT` to evade operation identity.

### 4.3 Unique settlement result — Model A

**Model A is frozen.** Existing `DamageResolutionResult` is upgraded into the one settlement-result type. No long-lived parallel `Stage9DamageSettlementResult` exists.

```python
DamageResolutionResult(
    damage: DamageResult,                 # Stage8 theoretical result
    assigned_target_damage: int,          # Dtarget
    actual_target_troop_loss: int,        # clamp result
    target_troops_before: int,
    target_troops_after: int,
    target_defeated: bool,
    credited_damage: int,                 # explicit attribution layer
    troop_change: TroopChangeResult | None,
    damage_instance_id: DamageInstanceId | None,
    lineage: OperationLineage | None,
)
```

Compatibility/read-only projections may include:

```text
dtotal           = damage.final_damage
requested_damage = assigned_target_damage
defeated          = target_defeated
```

Existing `damage`, `troop_change`, and `target_defeated` callers remain source-compatible where practical. No compatibility property may collapse `Dtotal`, `Dtarget`, and actual loss.

For ordinary positive standard target settlement:

```text
credited_damage = actual_target_troop_loss
```

unless a currently frozen mechanism P0 defines a different attribution fact on a separate typed path. Share/Distribution direct loss keeps its own attribution type and does not reuse this field as a hit.

A prevented Stage8 result never mutates troops: its settlement/result surface records zero actual target loss and produces no `DAMAGE_DEALT`; existing `DAMAGE_PREVENTED` semantics remain observation-only.

### 4.4 Settlement API

Legacy convenience path:

```python
DamageResolutionSystem.resolve(context, request: DamageRequest)
```

means:

```text
DamageSystem.calculate(request)
→ DamageSettlementRequest(
     damage_result=result,
     assigned_target_damage=result.final_damage,
     origin=LEGACY_COMPAT,
  )
→ settle(...)
```

Therefore Stage1-8 compatibility preserves:

```text
Dtotal == Dtarget
DAMAGE_DEALT.requested_damage == DamageResult.final_damage
```

Stage9 standard path:

```text
DamageSystem.calculate()
→ immutable DamageResult(final_damage=Dtotal)
→ exactly-one partition plan
→ Dtarget
→ DamageSettlementRequest(origin=STAGE9, assigned_target_damage=Dtarget, ids/lineage present)
→ DamageResolutionSystem.settle(...)
→ DamageResolutionResult
```

`apply_result(context, damage)` may remain only as a legacy full-settlement wrapper. It may not gain an optional `assigned_amount` argument.

### 4.5 `DAMAGE_DEALT` event meaning

For `DAMAGE_DEALT`:

```text
payload.requested_damage
=
actual requested settlement amount submitted to TroopSystem
=
DamageResolutionResult.assigned_target_damage
=
Dtarget on Stage9 partitioned paths
```

It is not `Dtotal` on partitioned paths.

Consumers needing `Dtotal` read `DamageResolutionResult.damage.final_damage`; consumers needing actual committed troop change read `actual_target_troop_loss`.

`DAMAGE_PREVENTED` is not a troop-settlement fact and does not redefine this `DAMAGE_DEALT.requested_damage` contract.

### 4.6 DAMAGE_FACT ownership matrix

| Semantic layer | Typed owner | Authoritative field | Consumer examples |
|---|---|---|---|
| `Dtotal` | `DamageResult` | `final_damage` | partition planning, theoretical trace |
| `Dtarget` | `DamageSettlementRequest` | `assigned_target_damage` | TroopSystem settlement |
| `ActualTargetTroopLoss` | `DamageResolutionResult` | `actual_target_troop_loss` | Cleave basis, recovery/stat, death edge |
| `CreditedDamage` | `DamageResolutionResult` / direct attribution type | explicit `credited_damage` / direct-loss credit field | statistics/recovery attribution where permitted |
| `UnitDeathFact` | concrete settlement/direct-loss edge | explicit typed fact | finalization + trace |

```text
NO FIELD ALIASING ACROSS SEMANTIC LAYERS.
```

This is Stage9 settlement plumbing around a frozen Stage8 result, not a Stage8 gameplay semantic reopen.

---

## 5. Existing Architecture Baseline

Current production facts:

- `BattleEngine` owns round/action phase progression and currently owns terminal compatibility side effects through `_finish()`.
- `BattleSystems` is the composition root.
- `ActionSystem` currently performs alive/STUN gate then calls `NormalAttackSystem`.
- `NormalAttackSystem` currently owns physical normal attack permission/target/settlement.
- `TargetSystem` is the common target/RNG query seam.
- `DamageSystem` owns the frozen Stage8 theoretical pipeline.
- `DamageResolutionSystem` owns current settlement and damage/death fact publication.
- `TroopSystem` is the sole troop mutation boundary.
- `VictorySystem` is already a pure world-state evaluator returning `BattleResult`.
- `EventBus` explicitly documents facts-only semantics.
- `StateLifecycleSystem` is the sole formal state apply/remove/expire writer.
- `StateRegistry` is the sole state container.
- `TriggerSystem` produces ordered Effects and does not execute side effects.
- `EffectExecutor` currently routes `DamageEffect` directly to `DamageResolutionSystem.resolve()`.
- `SkillRuntime` currently has owner+definition but no slot; Round1 repair assigns the ingress below.
- `RandomSystem` remains the unique battle RNG.

### 5.1 EXISTING_ARCHITECTURE_IMPACT_MATRIX

| Existing component | Stage9 action | Why |
|---|---|---|
| `BattleEngine` | MODIFY narrowly | outer loop + future-action gate + finalized-result projection |
| `BattleContext` | MODIFY narrowly | operation-id allocator + small termination record only |
| `BattleSystems` | MODIFY | compose/inject Stage9 services |
| `ActionOrderSystem` | KEEP | existing ordering seam |
| `ActionSystem` | MODIFY | ActionId, ActionStart maintenance/grant |
| `NormalAttackSystem` | MODIFY / MASTER OWNER | orchestration-first master only |
| `TargetSystem` | KEEP / CALL | candidate/random primitives only |
| `AttributeSystem` | KEEP / CALL | live combat stats source |
| `DamageSystem` | KEEP / DO NOT TOUCH semantics | frozen Stage8 calculation owner |
| `DamageResolutionSystem` | MODIFY settlement seam only | typed assigned-target settlement |
| `TroopSystem` | KEEP / CALL | sole troop mutation primitive |
| `VictorySystem` | **KEEP / CALL** | already pure; no Round1 repair edit required |
| `RandomSystem` | KEEP | sole RNG |
| `EventBus` | KEEP semantics / observation additions only | never control flow |
| `StateLifecycleSystem` | MODIFY provenance ingress only | store supplied source slot; mutation ownership unchanged |
| `StateInstance` | MODIFY provenance metadata only | store optional source slot |
| `StateRegistry` | KEEP | sole state container |
| `SkillRuntime` | MODIFY provenance | authoritative loaded-skill slot carrier |
| `SkillResolver` | MODIFY provenance propagation | pass runtime slot to Effects |
| `effects.py` | MODIFY provenance carrier | Damage/ApplyState Effects carry source slot |
| `effect_result.py` | MODIFY | stable Stage9 DamageEffect result shape |
| `EffectExecutor` | MODIFY narrowly | DamageEffect routes through completed DamageInstance path |
| Stage8 formula/resolver internals | DO NOT TOUCH | frozen authority boundary |

No BattleEngine 2.0 and no second state runtime are introduced.

---

## 6. Design Principles and Deterministic Defaults

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
11. engineering defaults are never mislabeled as official order
```

Additional rules:

- EventBus fact publication never substitutes for coordinator calls.
- No core ordering depends on subscriber registration, dict/hash iteration, or object address.
- Operation IDs are **NEVER gameplay ordering keys**.
- Invalid identity/provenance, illegal recursive dispatch, double admission/consume, missing required source slot, and conflicting duplicate finalization are programmer/domain errors.
- P0-defined dead/invalid planned member is a typed local skip/cancel, not an exception.

### 6.1 Comparator labels

| Comparator | Runtime rule | Authority label |
|---|---|---|
| battle/unit slot | lineup order, then stable `unit_id` only if a tie still exists | `PROJECT_DETERMINISTIC_DEFAULT` for `unit_id`; **NOT EMPIRICALLY PROVEN / NOT OFFICIAL ORDER** |
| Cleave source effects | authoritative `source_skill_slot` ascending | P0-derived; missing required slot = domain error |
| Cleave secondary targets | `GLOBAL_SLOT_ASCENDING` | P0-derived |
| Chain traversal | stable global slot ascending, monotonic cursor | P0-derived |
| Counter fallback where universal comparator remains open | stable mechanism-local source/instance fallback | `PROJECT_DETERMINISTIC_DEFAULT`; **NOT EMPIRICALLY PROVEN / NOT OFFICIAL ORDER** |

Stable state-instance identity may be used only as a deterministic fallback where P0 explicitly leaves fidelity open. Operation IDs never resolve gameplay ties.

---

## 7. Global Runtime Topology

```text
BattleEngine
  ├─ BattleFinalizationCoordinator
  │    ├─ VictorySystem (pure evaluator)
  │    ├─ termination state/record
  │    └─ ExecutionRightSystem / FutureAdmissionGate read of termination state
  │
  └─ ActionSystem
       ├─ Stage9StateRuntime / maintenance
       ├─ ActionId + ComboActionGrant
       └─ NormalAttackSystem  ← UNIQUE NORMAL-ATTACK MASTER
            ├─ TargetResolutionSystem
            ├─ DamageInstanceCoordinator
            │    ├─ DamageSystem.calculate (Stage8)
            │    ├─ DamagePartitionCoordinator
            │    ├─ DamageResolutionSystem.settle
            │    ├─ DirectTroopLossResolver
            │    └─ DamageCallbackAdmissionPoint for new Chain traversal
            ├─ CleaveSystem
            │    └─ CleaveDerivedDamageResolver
            │         └─ same DamageCallbackAdmissionPoint after eligible derived settlement
            ├─ ChainSystem
            ├─ CounterSystem
            │    └─ DamageInstanceCoordinator for positive live-target Counter damage
            ├─ AssaultDispatchPort
            └─ Combo checkpoint

BattleSystems = composition root for every service above.
BattleContext = battle data + ID allocator + small termination record, NOT a service locator.
```

### 7.1 NormalAttack sequence

```python
execute_normal_attack(action_scope, actor, *, combo_checkpoint_allowed):
    require(action_scope is admitted)
    if not can_normal_attack(actor):
        return blocked_result

    na = new_normal_attack_instance(action_scope)
    target = target_resolution.resolve(na, actor)  # selector -> Guard once -> lock
    if target is None:
        return no_target_result

    main = damage_instances.resolve_standard(
        lineage=na.lineage,
        source_type=NORMAL_ATTACK,
        target=target.post_redirect_actual_target,
    )

    resolve_already_admitted_local_post_hit_work(main)
    admit_next_cleave_effect_if_any(main)
    admit_counter_batch_if_triggered(na, target.post_redirect_actual_target)
    admit_assault_if_registered(action_scope, na)

    if combo_checkpoint_allowed:
        combo.try_run_checkpoint(action_scope, na)

    return normal_attack_result
```

New Chain traversal admission is owned by the shared damage-callback admission point when a resolved damage fact is Chain-eligible; NormalAttack does not duplicate that gate.

`NormalAttack #2` calls the same master with `combo_checkpoint_allowed=False`.

### 7.2 Standard DamageInstance sequence

```text
allocate DamageInstanceId + lineage
→ construct legitimate Stage8 DamageRequest
→ DamageSystem.calculate
→ freeze Dtotal = DamageResult.final_damage
→ exactly one partition plan: NONE / SHARE / DISTRIBUTION
→ obtain Dtarget
→ typed DamageSettlementRequest(Dtarget)
→ target settlement + direct-loss transaction steps
→ explicit ActualTargetTroopLoss / CreditedDamage / UnitDeathFact(s)
→ permitted already-admitted local callbacks
→ submit Chain-eligible resolved-damage fact to the one DamageCallbackAdmissionPoint
→ notify finalization coordinator of death/barrier facts
→ complete DamageInstance barrier
```

No partition rewrites the Stage8 result.

### 7.3 Finalization sequence

```text
UnitDeathFact or macro victory evaluation point
→ VictorySystem.check / resolve_max_rounds
→ BattleFinalizationCoordinator.evaluate_and_latch(...)
→ RUNNING -> VICTORY_LATCHED / DRAINING_ADMITTED_WORK
→ FutureAdmissionGate rejects new global FutureBranches
→ admitted local operations obey their P0 drain/cancel rules
→ notify_operation_completed(...)
→ try_finalize(...)
→ FINALIZED + immutable FinalizationResult
→ BattleEngine._apply_finalized_battle_result(FinalizationResult)
→ context.ended/context.result + BATTLE_END + BATTLE_ENDED compatibility projection
```

`VICTORY_LATCHED != FINALIZED` is structural.

---

## 8. Operation Identity & Provenance

### 8.1 Strong identities

All IDs are immutable typed values allocated by one per-battle `OperationIdAllocator` using deterministic monotonic sequences. IDs are runtime/trace identity, never gameplay priority.

| ID | Generator | Lifetime | Parent | Status |
|---|---|---|---|---|
| `ActionId` | ActionSystem | one unit Action | root | required |
| `NormalAttackInstanceId` | NormalAttackSystem | one physical NA | ActionId | required |
| `TargetResolutionId` | TargetResolutionSystem | one target resolve | NormalAttackId | **TRACE_ONLY SUPPORTING ID** |
| `DamageInstanceId` | damage/derived owner | one damage event | NA/parent damage | required |
| `PartitionTransactionId` | partition coordinator | one transaction | DamageInstanceId | required |
| `ReactionBatchId` | CounterSystem | one admitted batch | NormalAttackId | required |
| `CounterBatchEntryId` | CounterSystem | one batch entry | ReactionBatchId | required |
| `CleaveEffectId` | CleaveSystem | one effect execution | NormalAttackId | required |
| `ChainTraversalId` | ChainSystem | one traversal | DamageInstanceId | required |
| `DirectTroopLossId` | DirectTroopLossResolver | one direct commit | PartitionTransactionId | required |

`TargetResolutionId` is retained only because it improves #1/#2 target trace correlation:

```text
not a gameplay prerequisite
not a gameplay ordering key
removable later without gameplay semantic change
```

### 8.2 Source identity vs Stage8 damage source

`SourceType` is Stage9 orchestration/provenance/permission identity. `DamageSourceType` is Stage8 formula-source classification.

| `SourceType` | Stage8 mapping | Rule |
|---|---|---|
| `NORMAL_ATTACK` | `DamageSourceType.NORMAL_ATTACK` | legitimate standard request |
| `ACTIVE_SKILL` | `DamageSourceType.SKILL` | legitimate standard request |
| `PERIODIC_DAMAGE` | `DamageSourceType.CONTINUOUS` | legitimate standard request |
| `COUNTER` | `DamageSourceType.COUNTER` | legitimate positive Counter request |
| `ASSAULT` | none until authoritative Assault damage path exists | no invented mapping |
| `CLEAVE` | **NO fake mapping** | Cleave-specific derived route |
| `CHAIN_TRUE_FEEDBACK` | **NO fake mapping** | restricted feedback route |
| `SHARE_DIRECT_LOSS` | **NO fake mapping** | direct troop loss |
| `DISTRIBUTION_DIRECT_LOSS` | **NO fake mapping** | direct troop loss |

Only legitimate Stage8 `DamageRequest` construction performs the one-way mapping.

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

Mechanism-local data stays in mechanism-local types.

---

## 9. Target Resolution

### 9.1 Immutable result

Round1 repair removes redundant `selected_target`.

```python
TargetResolutionResult(
    resolution_id: TargetResolutionId,  # TRACE_ONLY SUPPORTING ID
    normal_attack_id: NormalAttackInstanceId,
    intended_attack_target: str,
    post_redirect_actual_target: str,
    redirect_source: str | None,
    redirect_reason: RedirectReason,    # NONE | GUARD
)
```

There is exactly one selector pass before `intended_attack_target` is frozen. No extra RNG call exists merely to populate a DTO.

### 9.2 Pipeline

```text
TargetResolutionSystem
  1. build live legal pool through TargetSystem
  2. ConfusionSelectorPolicy
  3. else TauntSelectorPolicy
  4. else default selector through TargetSystem/RandomSystem
  5. freeze IntendedAttackTarget
  6. GuardRedirectResolver exactly once
  7. freeze PostRedirectActualTarget
  8. return immutable result
```

Rules remain:

- Confusion shadows Taunt only for current selector arbitration; it does not delete/suppress Taunt.
- Guard never recursively redirects the guarder.
- Share/Distribution use the concrete DamageEvent recipient after redirect.
- Counter holder and Cleave anchor use `post_redirect_actual_target`.
- Cleave secondaries do not rerun selector/Confusion/Taunt/Guard.
- Combo #2 allocates a fresh NormalAttack instance and fresh target-resolution pass.

---

## 10. NormalAttack Orchestration

### 10.1 Unique master

Existing `NormalAttackSystem` is the unique NormalAttack master because it already owns the production physical-attack entry.

It may own only:

```text
normal-attack permission
NormalAttackInstanceId
calling TargetResolutionSystem
calling main DamageInstanceCoordinator
relative ordering of component calls
future-branch admission call sites assigned to the NA lifecycle
CounterBatch trigger-window placement
Assault-window placement
Combo checkpoint reachability
completion barrier
collecting typed results
```

It is explicitly forbidden to own:

```text
target-selection algorithms
Share/Distribution partition math
state storage mutation
Cleave algorithm
Chain traversal algorithm
CounterBatch internals
finalization writes
Stage8 damage formulas
```

### 10.2 Action relationship

`ActionSystem` owns `ActionId`, ActionStart maintenance/grant, and Action-level cancellation. `NormalAttackSystem` owns each NormalAttack instance. Combo #1/#2 therefore share one `ActionId` but never share target/damage identities.

### 10.3 Assault seam

`AssaultDispatchPort` remains an ordering/admission port only. No Assault producer is registered by default. No gameplay semantics are invented.

---

## 11. Combo

`ComboStateInstance` is a typed view over physical state 690081, not a second state store.

```python
ComboActionGrant(
    action_id,
    granting_instance_id,
    source_unit,
    source_skill,
    state=VALID | REVOKED_BY_PHYSICAL_REMOVE | CONSUMED,
)
```

```text
ACTION_START maintenance
→ effective Combo read
→ grant if operational
→ physical REMOVE before consume revokes grant
→ ordinary SUPPRESS after valid grant does not revoke current Action grant
→ checkpoint atomic consume once
→ Action end disposes Action-local scope
```

Checkpoint:

```text
local actor/action gate permits reaching checkpoint
→ checkpoint REACHED once
→ validate grant
→ atomic consume once
→ cfg230-equivalent fact
→ standard can_normal_attack gate
→ FutureAdmissionGate at Combo #2 caller edge
→ allocate fresh NormalAttack #2 only if admitted
→ fresh target/Guard
→ same NormalAttackSystem, combo_checkpoint_allowed=False
```

After victory latch, P0 may still allow an already-admitted consumed checkpoint/cfg230 fact, but `NormalAttack #2` allocation is a future branch and is blocked.

---

## 12. Damage Partition

### 12.1 Arbitration

`DamagePartitionCoordinator` performs only:

```text
DamageInstance + actual DamageEvent target + Dtotal
→ exactly one effective plan
  NONE | SHARE | DISTRIBUTION
```

Share > Distribution precedence follows frozen P0. Share and Distribution keep separate transaction logic.

### 12.2 Semantic damage layers

| Semantic layer | Carrier |
|---|---|
| `Dtotal` | `DamageResult.final_damage` |
| `Dtarget` | partition plan and then `DamageSettlementRequest.assigned_target_damage` |
| `ActualTargetTroopLoss` | `DamageResolutionResult.actual_target_troop_loss` |
| `CreditedDamage` | explicit settlement/direct attribution field |
| `DerivedCalculatedDamage` | Cleave-specific derived result before clamp |
| `AttributedDirectTroopLoss` | separate non-DamageEvent direct-loss result |

### 12.3 Share

```text
DsharerTheoretical = ROUND_HALF_UP(Dtotal × ShareRatio)
Dtarget = Dtotal - DsharerTheoretical

settle target Dtarget
→ if target died: TARGET_DEATH_INTERRUPT; discard pending sharer work
→ else commit sharer AttributedDirectTroopLoss
```

Theoretical and actual sharer loss remain separate; overflow is discarded.

### 12.4 Distribution

Immutable plan freezes:

```text
participant tuple
N
Dtotal
ratio
Dtarget = ROUND_HALF_UP(Dtotal × (1-ratio))
Dtransfer = Dtotal - Dtarget
Dparticipant = ROUND_HALF_UP(Dtransfer / N)
```

Execution may JIT skip an invalid planned participant, but never recompute `N`, `Dtarget`, `Dparticipant`, participants, or remainder.

`DSTS9-B02` remains a Distribution-local policy:

```text
PROJECT_RUNTIME_DEFAULT
NOT EMPIRICALLY PROVEN
commander participant death during admitted fixed transaction
→ continue local planned work
→ finalization after transaction barrier
```

---

## 13. Attributed Direct Troop Loss

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
validate provenance
→ TroopSystem.apply_damage
→ clamp actual loss
→ attributed direct-loss fact
→ UnitDeathFact on alive→dead edge
→ explicit attribution/stat seam
→ finalization observation/barrier notification
```

It never calls DamageSystem/HitResolution/base formulas/Counter/Chain/Share/Distribution/FirstAid/generic Hurt callbacks.

---

## 14. Cleave

### 14.1 State and ordering

Cleave state remains in `StateRegistry`; `Stage9StateRuntime` returns typed views. Cleave source ordering uses authoritative `StateInstance.source_skill_slot`.

For a skill-sourced Cleave state where P0 requires skill-slot order:

```text
source_skill_slot is required
None = domain error
skill_id ordering fallback = FORBIDDEN
```

### 14.2 Cleave-specific derived boundary

Round1 removes speculative generic `DerivedDamageSystem<T>`. The owner is:

```text
CleaveDerivedDamageResolver
```

```python
CleaveDerivedDamageRequest(
    damage_instance_id,
    cleave_effect_id,
    lineage,
    source_type=CLEAVE,
    damage_type=inherited_weapon_or_strategy,
    base_fact=ACTUAL_TARGET_TROOP_LOSS,
    base_amount,
    ratio: ExactRatio,
    secondary_target,
    permission_policy,
)
```

Calculation:

```text
CleaveDerivedCalculatedDamage
= FLOOR(ActualTargetTroopLoss × CleaveRatio)
```

No Stage8 base formula, coefficient recomputation, generic modifier rerun, Crit reroll, selector, Guard, Combo, or Counter identity is entered.

If the resolved Cleave-derived damage is Chain-eligible under P0, the resolver submits the resolved fact to the **same** `DamageCallbackAdmissionPoint`; it does not construct a traversal or call the global future gate independently.

Chain is not forced through the Cleave-derived abstraction; Chain keeps its own restricted feedback route.

### 14.3 Effect queue

```text
CleaveEffect A: secondary 1 → secondary 2
then CleaveEffect B: secondary 1 → secondary 2
```

Each admitted effect freezes its secondary identity plan. Each secondary is local work inside the already-admitted effect and does not re-query the global FutureAdmissionGate. JIT liveness still applies. The next independent CleaveEffect has its own global admission check.

---

## 15. Chain

`ChainSystem` owns a one-pass `ChainTraversal`.

### 15.1 Monotonic slot cursor

```text
fixed global slot order
cursor begins before first slot
for each slot in ascending order:
    cursor advances to that slot exactly once
    live-read current eligibility at that moment
    if eligible: execute once
    if ineligible: pass once
once cursor passes a slot: never inspect that slot again
later higher slot may become eligible before cursor reaches it and may join
cursor never rewinds
```

Forbidden:

```text
while exists unvisited eligible identity:
    rescan all slots
```

because an already-passed slot must never re-enter.

### 15.2 Deferred work

Snapshot only trigger facts (`parent_damage_instance_id`, trigger node, trigger damage, provenance). Execution-time state/owner/ratio/candidate eligibility remains live-read where P0 requires it.

`CHAIN_TRUE_FEEDBACK` is not a Stage8 `DamageRequest`; it has its own restricted settlement and permission set.

---

## 16. Counter

Counter remains three layers:

```text
trigger-time eligible-state snapshot
→ immutable CounterBatch entries
→ execution-time owner/target liveness gates
```

Positive live-target Counter creates a legitimate Stage8 weapon request mapped to `DamageSourceType.COUNTER` and uses the Stage9 standard `DamageInstanceCoordinator` path.

Dead-target admitted sibling uses an explicit Counter terminal result:

```text
CounterExecute fact
→ attributed zero troop loss
→ complete entry
```

No fake Stage8 DamageResult or base-formula call is created.

Ordering:

- if current Counter P0 supplies authoritative slot metadata, use it;
- where universal comparator fidelity remains open and an eligible source has no slot, use the isolated Counter `PROJECT_DETERMINISTIC_DEFAULT` fallback;
- the fallback is **NOT EMPIRICALLY PROVEN / NOT OFFICIAL ORDER**;
- never substitute `skill_id` sorting for skill-slot sorting.

---

## 17. Execution Right / Future Admission

### 17.1 Semantic states

```text
NOT_ADMITTED
ADMITTED_PENDING
EXECUTING
COMPLETED
CANCELLED_BY_LOCAL_GATE
CANCELLED_BEFORE_ADMISSION
```

### 17.2 FUTURE_ADMISSION_CALLER_MATRIX

Every global future branch has **EXACTLY ONE authoritative gate caller**.

| Future branch | Exactly-one authoritative caller | Gate point |
|---|---|---|
| next Action | `BattleEngine` | immediately before dispatching the next Action lifecycle after macro checks |
| Assault | `NormalAttackSystem` master | immediately before `AssaultDispatchPort.dispatch` |
| Combo #2 | Combo checkpoint owned from NormalAttack lifecycle | after consume/local attack permission, before allocating NormalAttack #2 |
| new CounterBatch | `NormalAttackSystem` post-hit reaction admission point | before constructing/admitting a new CounterBatch snapshot |
| new ChainTraversal | shared `DamageCallbackAdmissionPoint` | resolved standard/derived damage producer submits a fact; this point alone calls the global gate and returns an admitted traversal token |
| next unadmitted CleaveEffect | `CleaveSystem` effect-loop boundary | before creating/freezing the next independent CleaveEffect plan |

`DamageCallbackAdmissionPoint` is a narrow execution-right admission seam (implemented with the execution-right/Chain admission contracts, not a second gameplay system). `DamageInstanceCoordinator` and `CleaveDerivedDamageResolver` may submit eligible resolved-damage facts to it; neither independently calls the Chain future gate. `ChainSystem` requires an admitted traversal token and cannot self-admit.

### 17.3 Already-admitted work does not re-query the future gate

Examples:

```text
Counter sibling already in admitted batch
next slot inside an admitted ChainTraversal
next secondary inside current admitted CleaveEffect
next planned Distribution participant
pending Share sharer step inside admitted Share transaction
current DamageInstance local callback already admitted by its operation contract
```

These use local liveness/P0 rules only. Re-running the global gate inside them would violate RF-P03/RF-P04 drain semantics.

### 17.4 No-bypass enforcement

```text
one injectable FutureAdmissionGate service
→ only assigned caller owners possess the branch-specific global admission capability
→ Chain traversal constructor requires an admitted token from DamageCallbackAdmissionPoint
→ local steps receive operation-local scope, not a second global admission decision
→ architecture tests assert future-branch constructors/allocators are dominated by their assigned gate
→ tests reject direct allocation after VICTORY_LATCHED
```

`context.ended` is never a semantic future-work gate. It becomes true only after finalized compatibility projection.

---

## 18. Battle Finalization

### 18.1 Ownership split

`VictorySystem` remains a pure evaluator. No Stage9 core edit is required for its gameplay behavior.

`BattleFinalizationCoordinator` is the **unique semantic owner** of:

```text
BattleTerminationState
victory latch identity/result
RUNNING -> VICTORY_LATCHED
VICTORY_LATCHED -> DRAINING_ADMITTED_WORK
DRAINING_ADMITTED_WORK -> FINALIZED
final operation-drain barrier
termination-state fact consumed by future-admission policy
```

`BattleEngine` remains outer loop and the **unique legacy terminal projection owner**, but only after receiving an immutable finalized result.

### 18.2 Writer matrix

| Field/effect | Unique writer | Rule |
|---|---|---|
| termination state | `BattleFinalizationCoordinator` | only coordinator transitions it |
| victory latch / finalized result | `BattleFinalizationCoordinator` | semantic decision owner |
| `context.ended` | `BattleEngine` finalized-result projection | written only when coordinator is `FINALIZED` |
| `context.result` | `BattleEngine` finalized-result projection | copied from immutable finalized result |
| `BATTLE_END` phase | `BattleEngine` finalized-result projection | compatibility projection only |
| `BATTLE_ENDED` event | `BattleEngine` finalized-result projection | exactly once |

Coordinator decides; Engine projects. They do not co-own finalization.

### 18.3 `_finish()` compatibility treatment

Preferred replacement:

```python
BattleEngine._apply_finalized_battle_result(finalization_result)
```

Precondition:

```text
finalization_result.state == FINALIZED
coordinator termination read-view == FINALIZED
```

It may only:

```text
context.ended = True
context.result = finalization_result.battle_result
enter BATTLE_END
publish BATTLE_ENDED once
return battle_result
```

It may not evaluate victory, latch victory, decide drain completion, or decide whether finalization is allowed.

If `_finish` is temporarily retained for source compatibility, its contract must be mechanically equivalent and accept only coordinator-produced finalized input.

### 18.4 Dependency direction

```text
BattleEngine
→ BattleFinalizationCoordinator
→ VictorySystem

NEVER:
BattleFinalizationCoordinator
→ BattleEngine._finish / _apply_finalized_battle_result
```

The coordinator returns `FinalizationResult | None`; Engine consumes it.

### 18.5 Coordinator API

Names may vary mechanically, semantics may not:

```python
observe_death_fact(...)
evaluate_and_latch(...)
can_admit_future_work(...)
notify_operation_completed(...)
try_finalize(...) -> FinalizationResult | None
```

Macro max-round handling remains:

```text
BattleEngine reaches existing max-round boundary
→ coordinator evaluates supplied `VictorySystem.resolve_max_rounds` result
→ latch/drain/finalize
→ Engine projects finalized result
```

### 18.6 Existing Engine/Stage7 ordering compatibility

Migrating semantic finalization must preserve current externally observable macro ordering unless a frozen P0 explicitly overrides it:

```text
RoundStart hook processing completes before its existing victory barrier
Action execution completes before UNIT_ACTION_END compatibility publication
UNIT_ACTION_ENDED remains published before terminal BATTLE_END projection for the current action path
BATTLE_END / BATTLE_ENDED are emitted only after coordinator FINALIZED
max-round result rules remain VictorySystem-owned
```

Coordinator observation may latch victory earlier inside admitted work, but Engine terminal projection does not jump ahead of the existing macro compatibility publication point. This preserves Stage7 hook/action event ordering while allowing Stage9 local drain semantics.

### 18.7 Finalization test seam

Tests read typed fields/results, never log strings:

```text
termination_state
victory_latched / latched_result
finalized / finalized_result
operation barrier state
legacy BATTLE_END phase/event publication
```

Repeated observation of the same fact is idempotent; conflicting duplicate finalization is a domain error; `BATTLE_ENDED` is emitted exactly once.

---

## 19. Recursion / Permission Policy

`ReactionPermissionPolicy` is a centralized typed table over `SourceType`, NormalAttack identity, and lineage.

| From | Cleave | Counter | Chain | Share | Distribution | FirstAid / Recovery |
|---|---:|---:|---:|---:|---:|---:|
| NORMAL_ATTACK | ALLOW by trigger P0 | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW where P0 permits |
| CLEAVE | BLOCK | BLOCK | ALLOW | ALLOW | ALLOW | ALLOW by Cleave P0 |
| COUNTER | BLOCK | BLOCK | ALLOW | ALLOW | ALLOW | ALLOW by Counter P0 |
| CHAIN_TRUE_FEEDBACK | BLOCK/N/A | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK |
| SHARE_DIRECT_LOSS | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK |
| DISTRIBUTION_DIRECT_LOSS | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK |

NormalAttack-only selector/Guard/Assault/Combo paths require NormalAttack identity.

---

## 20. Exact Numeric Representation

### 20.1 `ExactRatio`

Stage9 freezes a rational representation:

```python
ExactRatio(
    numerator: int,
    denominator: int,  # > 0, normalized/reduced
)
```

It represents finite decimal ratio/config input exactly. Stage9 integerization uses integer/rational math, not binary float multiplication.

### 20.2 Ingress boundary

Preferred:

```text
raw textual decimal config
→ Decimal(raw_text) for validation/parsing
→ exact numerator/denominator
→ ExactRatio
```

If an existing surface exposes only `float`, compatibility conversion is exactly:

```python
Decimal(str(value))
```

then converted to `ExactRatio`.

Forbidden:

```python
Decimal(value)
Fraction(value)
float multiplication then floor/round
Python round()
```

This boundary does not change Stage8 `DamageRequest.coefficient`, Stage8 formula types, or Stage8 result semantics.

### 20.3 Integerization API

```python
floor_product_int_ratio(base: int, ratio: ExactRatio) -> int
round_half_up_product_int_ratio(base: int, ratio: ExactRatio) -> int
round_half_up_divide_int(numerator: int, denominator: int) -> int
```

For nonnegative gameplay quantities these can be exact integer arithmetic. Ratio range restrictions belong to mechanism P0/call sites.

| Call site | Rule |
|---|---|
| Chain | `FLOOR` |
| Cleave | `FLOOR` |
| Share `Dsharer` | `ROUND_HALF_UP` |
| Distribution `Dtarget` | `ROUND_HALF_UP` |
| Distribution participant | `ROUND_HALF_UP` |

RF-C01 vectors remain the executable oracle.

---

## 21. State Runtime Integration and `source_skill_slot`

### 21.1 No second state runtime

```text
BattleContext.states : StateRegistry
StateLifecycleSystem : only physical state mutation writer
Stage9StateRuntime   : typed read/maintenance adapter only
```

### 21.2 Authoritative slot producer

`SkillDefinition` does not own slot because a static definition may be equipped in different positions.

The authoritative producer/carrier boundary is the holder-specific **loaded `SkillRuntime` entry**:

```python
SkillRuntime(
    definition,
    owner_id,
    skill_slot: int | None,
    enabled=True,
)
```

The production call site that constructs the loaded runtime and already knows the equipped position must supply `skill_slot`; `SkillRuntime` validates/stores it. Downstream systems never infer slot from `skill_id`.

Semantic source triple:

```text
source_unit_id
source_skill_id
source_skill_slot
```

Implementation may wrap the triple in `SourceSkillRef` or retain validated explicit fields; producer and propagation semantics are frozen.

### 21.3 Propagation chain

```text
loaded SkillRuntime(skill_slot known when applicable)
→ SkillResolver
→ DamageEffect / ApplyStateEffect source provenance
→ EffectExecutor
→ StateLifecycleSystem.apply(... source_skill_slot=...)
→ StateInstance.source_skill_slot
→ Stage9StateRuntime typed view
→ Cleave / Counter ordering
```

`DamageEffect` may carry slot for Stage9 lineage/provenance, but `DamageRequest` remains a Stage8 formula request and gains no slot field solely for orchestration.

### 21.4 No-slot handling

Legitimate non-skill or unknown-slot sources use:

```text
source_skill_slot = None
```

Examples: system-applied, external command/system source, compatibility fixture.

Rules:

- never auto-fill `0`, `999`, hash, or `skill_id` order;
- P0-required skill-slot ordering (notably skill-sourced Cleave ordering) + `None` -> domain error before ordering/execution;
- Counter areas whose universal comparator remains intentionally open may use isolated `PROJECT_DETERMINISTIC_DEFAULT` fallback;
- mechanisms not depending on slot accept `None`.

### 21.5 INV-18 enforcement

```text
TYPE:
source_skill_slot exists explicitly as Optional[int] throughout apply provenance.

RUNTIME:
Stage9StateRuntime / mechanism adapter rejects missing slot whenever applicable P0 requires it.

ARCHITECTURE:
StateRegistry never guesses slot; StateLifecycleSystem stores supplied provenance only.
```

---

## 22. Recovery / Trigger Integration

Stage9 does not redesign Stage7 Trigger/Recovery.

- `TriggerSystem` stays fact-to-Effect collector.
- `RecoverySystem` stays recovery execution owner.
- `TroopSystem.restore` stays write boundary.
- EventBus remains observation-only.
- Stage9 decides source eligibility and exact damage-fact layer; Recovery logic is not duplicated.

Damage-event basis:

```text
NormalAttack standard damage: existing eligible recovery hooks
Counter positive standard DamageEvent: permitted hooks under Counter P0
Cleave derived DamageEvent: permitted hooks under Cleave P0
Chain TRUE_FEEDBACK: blocked where Chain P0 blocks
Share/Distribution direct loss: never recovery damage basis
Counter dead-target zero terminal: no damage basis
```

Recovery/stat attribution consumes the exact actual/credited field required by P0, never infers from `Dtotal` or `Dtarget` by name coincidence.

---

## 23. Trace & Observability

### 23.1 Lifecycle

`Stage9OperationTrace` is battle-scoped observation only.

Production default:

```text
lightweight
configurable
bounded by a finite record budget
battle lifetime only
overflow deterministic: drop-oldest bounded ring + dropped-count metadata
not persisted into gameplay state
not serialized as authoritative battle state
never read for gameplay decisions
```

Tests:

```text
full-detail sink enabled for fixture lifetime
may retain all records needed by the test
deterministic typed records + IDs
```

A no-op sink may exist for disabled diagnostics, but gameplay must be identical under no-op/bounded/full sinks.

### 23.2 Trace records

Trace may observe:

```text
Action admission/completion/cancel
NormalAttack creation/completion
TargetResolution
DamageInstance calculation + Dtotal
Settlement Dtarget + actual loss + credited damage
Partition plan/steps
Cleave calculation/effect/secondary
CounterBatch admission/entries
ChainTraversal cursor/slots
FutureAdmission decisions
victory latch/drain/finalization
```

### 23.3 EventBus rule

```text
Event = observation / notification
Coordinator call = authoritative control flow
```

No Stage9 finalization/reaction sequencing depends on subscriber order.

---

## 24. Runtime Invariants — Round1 Re-coverage

All 42 RF-C01 invariants remain mapped.

| Invariant | Primary enforcement |
|---|---|
| INV-01 | TYPE: immutable intended/actual target fields |
| INV-02 | STRUCTURAL: selector pipeline before Guard |
| INV-03 | RUNTIME ASSERTION: one Guard pass / NA |
| INV-04 | TYPE: downstream actual-target contracts |
| INV-05 | TYPE: recipient belongs to concrete settlement |
| INV-06 | STRUCTURAL: fresh #2 instance/resolution |
| INV-07 | TYPE: physical/operational/grant types separate |
| INV-08 | STRUCTURAL: ActionStart maintenance sequencing |
| INV-09 | RUNTIME ASSERTION: grant transition |
| INV-10 | RUNTIME ASSERTION: checkpoint ceiling |
| INV-11 | RUNTIME ASSERTION: atomic consume ceiling |
| INV-12 | RUNTIME ASSERTION: <=2 physical NormalAttacks |
| INV-13 | TYPE: Cleave source/identity |
| INV-14 | STRUCTURAL: actual target troop loss is Cleave input |
| INV-15 | RUNTIME ASSERTION: exact FLOOR helper/vector |
| INV-16 | STRUCTURAL: CleaveDerivedDamageResolver has no Stage8 base-formula edge |
| INV-17 | TYPE: centralized permission policy |
| INV-18 | **TYPE + RUNTIME: authoritative source-slot chain; required missing slot rejected** |
| INV-19 | TYPE: direct loss distinct from DamageEvent |
| INV-20 | STRUCTURAL: direct loss bypasses HitResolution |
| INV-21 | TYPE: explicit provenance fields/value object |
| INV-22 | RUNTIME ASSERTION: exactly-one partition |
| INV-23 | STRUCTURAL: lifecycle replacement adapter |
| INV-24 | STRUCTURAL: Share target-first |
| INV-25 | STRUCTURAL: lethal target local interrupt |
| INV-26 | TYPE: Dtotal/Dtarget/actual/credit fields distinct |
| INV-27 | TYPE: frozen participants/N |
| INV-28 | TYPE: frozen calculated fields |
| INV-29 | STRUCTURAL: skip-only fixed plan |
| INV-30 | STRUCTURAL: no participant append/replan |
| INV-31 | STRUCTURAL: labeled Distribution local default |
| INV-32 | TYPE: deferred trigger snapshot schema |
| INV-33 | STRUCTURAL: execution-time live state lookup |
| INV-34 | RUNTIME ASSERTION: monotonic Chain cursor |
| INV-35 | STRUCTURAL: restricted Chain settlement |
| INV-36 | TYPE: immutable CounterBatch entries |
| INV-37 | STRUCTURAL: global admission vs local liveness separated |
| INV-38 | TYPE: explicit Counter zero terminal |
| INV-39 | TYPE: death fact/latch/finalized separation |
| INV-40 | **STRUCTURAL: caller matrix + branch-specific gate capability + no-bypass architecture test** |
| INV-41 | **STRUCTURAL: coordinator alone mutates termination state; Engine only projects finalized result** |
| INV-42 | STRUCTURAL: SourceType + lineage + permission mapping |

Recomputed primary categories:

```text
STRUCTURAL        = 18
TYPE-ENFORCED     = 16
RUNTIME ASSERTION = 8
TEST-ONLY         = 0
UNENFORCED        = 0
TOTAL             = 42
```

Architecture tests supplement structural enforcement; no invariant relies on test-only enforcement.

---

## 25. Regression Mapping and Testability

Mandatory gameplay contract count remains exactly **45**. Round1 repair adds seams, not gameplay IDs.

| Regression ID | Planned test | Core assertion |
|---|---|---|
| REG-TGT-01 | `test_stage9_target_resolution.py` | Confusion selector wins only current selection |
| REG-TGT-02 | same | Taunt lifecycle remains while shadowed |
| REG-TGT-03 | same | intended=B, actual=C under Guard |
| REG-TGT-04 | same | exactly one redirect |
| REG-TGT-05 | same | Combo #2 fresh NA + trace-only target-resolution ID |
| REG-TGT-06 | same | #2 reruns Guard |
| REG-TGT-07 | same | pre-Guard intended target may be Cleave secondary |
| REG-CMB-01 | `test_stage9_combo.py` | maintenance before grant |
| REG-CMB-02 | same | physical remove revokes grant |
| REG-CMB-03 | same | suppress after grant retains current grant |
| REG-CMB-04 | same | consume once/no refund/<=2 attacks |
| REG-CMB-05 | same | death/victory blocks future Assault/#2 allocation |
| REG-CLV-01 | `test_stage9_cleave.py` | actual target loss base; 55×54%=29 FLOOR |
| REG-CLV-02 | same | no base-formula/modifier/Crit re-entry |
| REG-CLV-03 | same | permission matrix exact |
| REG-CLV-04 | same | effect-major + JIT skip + source-slot order |
| REG-CLV-05 | same | post-Guard actual target is Cleave anchor |
| REG-CHN-01 | `test_stage9_chain.py` | trigger snapshot + live ratio |
| REG-CHN-02 | same | monotonic one-pass; later higher slot may join |
| REG-CHN-03 | same | admitted traversal drains after commander-death latch |
| REG-CHN-04 | same | restricted feedback only |
| REG-SHR-01 | `test_stage9_partition.py` | target settlement first, then sharer direct loss |
| REG-SHR-02 | same | lethal target discards pending sharer |
| REG-SHR-03 | same | direct loss is not a hit |
| REG-SHR-04 | same | Share precedence; one partition |
| REG-DST-01 | same | invalid planned participant SKIP/no recompute |
| REG-DST-02 | same | fixed plan continues ordinary participant death |
| REG-DST-03 | same | commander participant labeled project default drain |
| REG-DST-04 | same | participant direct loss is not DamageEvent |
| REG-CTR-01 | `test_stage9_counter.py` | admitted entry retained after state removal |
| REG-CTR-02 | same | dead owner cancels only local entry |
| REG-CTR-03 | same | admitted sibling zero terminal after target death, then finalize |
| REG-CTR-04 | same | dead-target sibling never enters Stage8 formula |
| REG-CTR-05 | same | Counter victory blocks future Assault/Combo branches |
| FINAL_01_CHAIN_COMMANDER_DEATH | `test_stage9_finalization.py` | latch→admitted traversal drain→finalize |
| FINAL_02_COUNTER_SIBLING | same | admitted Counter sibling drains after latch |
| FINAL_03_COMBO_BATTLE_END | same | no NormalAttack #2 allocation after victory latch |
| FINAL_04_CLEAVE_COMMANDER_SECONDARY | same | current effect local drain; next effect blocked |
| FINAL_05_SHARE_COMMANDER_TARGET | same | Share target-death interrupt then finalize |
| FINAL_06_DISTRIBUTION_COMMANDER_PARTICIPANT | same | runtime-default admitted transaction drain |
| REG-INT-01 | `test_stage9_integerization.py` | 396×28.28% FLOOR=111 |
| REG-INT-02 | same | 470×15% HALF_UP=71; target=399 |
| REG-INT-03 | same | 251×50% target HALF_UP=126 |
| REG-INT-04 | same | 353/2 participant HALF_UP=177, no repair |
| REG-INT-05 | same | 55×54% FLOOR=29 |

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
Untestable      = 0
Unmapped        = 0
Semantic Conflict = 0
```

### 25.1 Required settlement/fact seam tests — not new gameplay IDs

A supporting fixture must realize:

```text
Dtotal != Dtarget != ActualTargetTroopLoss
```

and prove separately:

1. partition test reads `Dtotal` from `DamageResult.final_damage` and `Dtarget` from settlement request/result;
2. Cleave base test reads only `actual_target_troop_loss`;
3. recovery/stat attribution test reads the explicit actual/credited field required by its seam;
4. event payload test proves `DAMAGE_DEALT.requested_damage == Dtarget` while Dtotal remains on `DamageResult`.

These are seam/architecture assertions inside planned Stage9 groups, not extra gameplay regression IDs.

### 25.2 Finalization observation seam

`FINAL_01..06` assert typed:

```text
termination_state
victory_latched
finalized
operation-drain completion
BATTLE_END / BATTLE_ENDED compatibility publication
```

No finalization regression may depend on string-log parsing.

---

## 26. Source File Plan — Recomputed After Round1 Repair

All paths are under the flat `sgs_v2/battle_core/` package unless stated otherwise.

### 26.1 Planned NEW production files — 16

| File | Responsibility |
|---|---|
| `operation_identity.py` | typed IDs, allocator, SourceType, lineage |
| `stage9_trace.py` | bounded production/full-test observation sink |
| `stage9_integerization.py` | `ExactRatio` + exact FLOOR/HALF_UP helpers |
| `stage9_state_params.py` | mechanism typed runtime params |
| `stage9_state_runtime.py` | typed StateRegistry adapter + ordering validation |
| `target_resolution_system.py` | selector + Guard single-pass immutable result |
| `reaction_permission_policy.py` | centralized recursion/callback permissions |
| `execution_right_system.py` | FutureAdmissionGate, admitted tokens, operation barriers, DamageCallbackAdmissionPoint contract |
| `damage_instance_coordinator.py` | standard Stage8 damage orchestration/fact boundary |
| `damage_partition_system.py` | exactly-one partition + Share/Distribution plans |
| `direct_troop_loss_system.py` | attributed direct-loss settlement |
| `cleave_derived_damage_system.py` | Cleave-specific derived calculation/settlement seam |
| `cleave_system.py` | source-bound effects/secondary plans/admission |
| `chain_system.py` | monotonic traversal/deferred/restricted feedback |
| `counter_system.py` | CounterBatch/entries/live gates/zero terminal |
| `battle_finalization_coordinator.py` | unique termination/latch/drain/finalize owner |

```text
Planned NEW = 16
```

### 26.2 Planned MODIFY production files — 16

| File | Planned change | Constraint |
|---|---|---|
| `context.py` | OperationIdAllocator + small termination record | no services/queues/policies/trace/mechanism state |
| `battle_systems.py` | compose/inject Stage9 systems | composition root only |
| `engine.py` | future Action gate + finalized-result projection | no mechanism algorithms/termination decision |
| `action_system.py` | ActionId, ActionStart maintenance/grant | no direct registry mutation |
| `normal_attack_system.py` | thin master orchestration | no local mechanism algorithms/finalization writes |
| `damage_resolution_system.py` | typed settlement request, upgraded result, `settle()` | `DamageResult.final_damage` untouched |
| `effect_executor.py` | route DamageEffect through completed DamageInstance path | no Trigger semantic change |
| `effect_result.py` | upgrade `DamageEffectResult` narrow stable result | no coordinator internals exposed |
| `skill_runtime.py` | authoritative optional `skill_slot` carrier | slot belongs to holder runtime |
| `skill_resolver.py` | propagate source slot into Effects | no slot inference |
| `effects.py` | carry source slot on Damage/ApplyState Effects | `DamageRequest` Stage8 shape unchanged |
| `state_instance.py` | store `source_skill_slot: int | None` | provenance only |
| `state_lifecycle_system.py` | accept/store/publish supplied source slot | generic lifecycle does not guess slot |
| `official_state_catalog.py` | bind Stage9 typed runtime params where required | IDs/text unchanged |
| `events.py` | Stage9 observation facts where needed | EventBus never controls flow |
| `__init__.py` | intentional public exports only | minimize surface |

```text
Planned MODIFY = 16
```

### 26.3 KEEP / CALL — not modified by default

```text
victory_system.py          # already pure evaluator
state_registry.py          # sole state store
skill_definition.py        # static definition; no slot ownership
target_system.py           # target primitives
troop_system.py            # sole troop mutation primitive
attribute_system.py        # live attributes
random_system.py           # sole RNG
recovery_system.py         # Stage7 recovery semantics
trigger_system.py          # Stage7 trigger semantics
rule_hook_system.py        # explicit hook route
```

### 26.4 DO NOT TOUCH Stage8 gameplay semantics

```text
damage_system.py calculation semantics
damage_prevention_system.py
hit_resolution_system.py semantics
damage_formula_policy_system.py
damage_modifier_system.py
weapon_damage_formula.py
strategy_damage_formula.py
damage_pipeline_trace.py meaning
DamageResult.final_damage meaning
```

If a frozen owner must materially change gameplay semantics, implementation stops for a formal authority/reopen decision.

### 26.5 `DamageEffectResult` compatibility

`effect_result.py` is explicitly in the plan.

Upgrade existing `DamageEffectResult`, do not return a giant coordinator aggregate:

```python
DamageEffectResult(
    effect: DamageEffect,
    damage_instance_id: DamageInstanceId,
    settlement_result: DamageResolutionResult,
)
```

A read-only compatibility property:

```text
resolution -> settlement_result
```

may preserve existing callers/tests. Partition plan, reaction queue, mutable coordinator state, and finalization internals are not exposed.

Dependency direction:

```text
EffectExecutor → DamageInstanceCoordinator
NEVER DamageInstanceCoordinator → EffectExecutor
```

### 26.6 Future test groups

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

This repair round creates none of them.

---

## 27. Existing System Impact Matrix

| Existing component | KEEP / MODIFY | Integration contract |
|---|---|---|
| BattleEngine | MODIFY | outer loop; unique finalized projection; no semantic finalization decision |
| BattleContext | MODIFY | ID allocator + small termination record only |
| BattleSystems | MODIFY | single composition root |
| ActionSystem | MODIFY | Action scope/maintenance |
| NormalAttackSystem | MODIFY | unique thin NormalAttack master |
| TargetSystem | KEEP | candidate/RNG primitives only |
| DamageSystem | KEEP | frozen Stage8 theoretical owner |
| DamageResolutionSystem | MODIFY | typed backward-compatible settlement seam |
| TroopSystem | KEEP | sole troop mutation writer |
| VictorySystem | **KEEP / CALL** | pure evaluator already correct |
| EventBus | KEEP semantics | observation only |
| StateRegistry | KEEP | one store |
| StateLifecycleSystem | MODIFY provenance only | one physical writer |
| SkillRuntime/Resolver/Effects | MODIFY provenance | authoritative source-slot chain |
| Trigger/Recovery | KEEP | no semantic redesign |
| EffectExecutor/effect_result | MODIFY | standard DamageEffect uses narrow Stage9 path/result |
| RandomSystem | KEEP | sole RNG |
| AttributeSystem | KEEP | live combat stats |

---

## 28. Implementation Phases — Reordered After Round1 Repair

### 28.0 Universal phase green gate

Every phase independently satisfies:

```text
all existing tests green
new phase tests green
no production call points to placeholder/stub/TODO Stage9 service
no production path depends on a later-phase semantic owner
Stage8 frozen semantics still green
```

Temporary production stub latch/coordinator is forbidden.

### Phase 9.1 — Identity / Provenance Types / Exact Numeric Utilities

**Goal:** foundational value types only.  
**Creates:** operation identities, `SourceType`, lineage, trace contracts, `ExactRatio`, integerization helpers, Stage9 state params.  
**Prepares:** loaded `SkillRuntime.skill_slot` contract; no Stage9 mechanism production route yet.  
**Required tests:** ID/lineage validation, numeric ingress, REG-INT-01..05.  
**Exit:** exact numeric boundary and provenance types complete.  
**Forbidden:** production damage/finalization reroute.

### Phase 9.2 — Execution Right + Finalization Infrastructure

**Goal:** install real semantic termination owner before Stage9 production damage depends on it.  
**Creates:** `ExecutionRightSystem`, `BattleFinalizationCoordinator`, termination record/result/admitted-token contracts.  
**Modifies:** `context.py`, `battle_systems.py`, `engine.py`; `VictorySystem` remains KEEP/CALL.  
**Tasks:** migrate Engine terminal decision to coordinator, keep Engine finalized projection, install next-Action gate, preserve current engine/hook terminal ordering.  
**Required tests:** current victory/engine tests + state/projection/idempotency tests.  
**Exit:** one termination writer, one compatibility projection writer, no coordinator→Engine edge.  
**Forbidden:** mechanism-local drain inventions.

### Phase 9.3 — Target Arbitration + State Provenance Ingress

**Goal:** complete source-slot chain and immutable target resolution.  
**Modifies:** `skill_runtime.py`, `skill_resolver.py`, `effects.py`, `state_lifecycle_system.py`, `state_instance.py`, catalog/composition surfaces.  
**Creates:** `Stage9StateRuntime`, target-resolution system.  
**Tasks:** runtime slot producer, Effect propagation, StateInstance metadata, required-slot validation, Confusion/Taunt/default selector, Guard once, remove `selectedTarget`.  
**Required tests:** REG-TGT-01..04 + provenance/no-slot tests.  
**Exit:** no forbidden slot inference; target result immutable.  
**Forbidden:** partition/reaction production routing.

### Phase 9.4 — Settlement Seam + Isolated DamageInstance Core

**Goal:** complete B1 typed settlement and build DamageInstance core against real finalization infrastructure.  
**Modifies:** `damage_resolution_system.py`; creates isolated coordinator.  
**Tasks:** Model A upgrade, typed request, legacy mapping, `DAMAGE_DEALT.requested_damage=Dtarget`, explicit death/credit facts.  
**Important:** `EffectExecutor` remains on legacy route until Phase 9.5 completes partition/direct-loss dependencies. The coordinator is tested directly; no production caller points to an incomplete coordinator.  
**Required tests:** legacy compatibility + `Dtotal != Dtarget != actual` seam + finalization notifications.  
**Exit:** unique settlement contract; old Stage1-8 behavior preserved.  
**Forbidden:** Stage8 calculation semantic change.

### Phase 9.5 — Partition + DirectTroopLoss + Production Damage Route

**Goal:** complete standard Stage9 damage path before routing production DamageEffect through it.  
**Creates:** partition/direct-loss systems.  
**Modifies at phase end:** `effect_executor.py`, `effect_result.py`, composition.  
**Tasks:** Share/Distribution plans, target-first/skip-only behavior, direct loss, narrow DamageEffect result, death/finalization/barrier notifications.  
**Production switch:** only after all 9.5 dependencies are real/green, route `EffectExecutor -> DamageInstanceCoordinator`.  
**Required tests:** REG-SHR-01..04, REG-DST-01..04, EffectExecutor compatibility tests.  
**Exit:** production DamageEffect cannot bypass partition/finalization seam.

### Phase 9.6 — NormalAttack Master + Combo

**Goal:** make existing NormalAttackSystem the thin lifecycle master and add Action-local Combo.  
**Tasks:** ActionId/NA IDs, fresh #2 target pass, Combo grant/checkpoint, Assault admission, caller ownership for Combo #2 and Assault.  
**Required tests:** REG-TGT-05..07, REG-CMB-01..05, existing normal-attack tests.  
**Exit:** one Action <=2 attacks; no recursive checkpoint; future branches gate once.  
**Forbidden:** embed Cleave/Chain/Counter algorithms.

### Phase 9.7 — Cleave + Chain + Counter

**Goal:** add real local mechanism services and remaining future-admission edges.  
**Creates:** Cleave-derived, Cleave, Chain, Counter, permission completion; wires shared DamageCallbackAdmissionPoint.  
**Tasks:** actual-loss Cleave basis, effect-major sequencing, monotonic Chain cursor, Counter batch/zero terminal, next-Cleave/new-Chain/new-CounterBatch gate ownership.  
**Required tests:** REG-CLV-01..05, REG-CHN-01..04, REG-CTR-01..05.  
**Exit:** all future-admission families covered; local admitted work never re-gates globally.

### Phase 9.8 — Full Integration / 45 Regressions

**Goal:** close all 42 invariants and 45 contracts on fully composed runtime.  
**Tasks:** FINAL_01..06, golden trace, architecture no-bypass/no-cycle tests, all existing tests, CI/demo compatibility.  
**Exit:** 42/42 enforced, 45/45 green, no dependency cycles, no Stage8 reopen.  
**Forbidden:** new gameplay research/semantic expansion.

### 28.1 PHASE_DEPENDENCY_GRAPH

```text
9.1 identity / provenance types / exact numeric
  ↓
9.2 real execution-right + finalization infrastructure
  ↓
9.3 target arbitration + source-slot/state ingress
  ↓
9.4 typed settlement seam + isolated DamageInstance core
  ↓
9.5 partition + direct loss + EffectExecutor production reroute
  ↓
9.6 NormalAttack master + Combo/Assault branch admission
  ↓
9.7 Cleave + Chain + Counter + remaining admission edges
  ↓
9.8 full integration / 42 invariants / 45 regressions
```

```text
Dependency cycles               = 0
Forward production dependencies = 0
```

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

The default remains isolated inside Distribution’s local transaction policy.

### 29.2 Counter fidelity

```text
exact official universal comparator fidelity = DEFERRED_NON_BLOCKING
universal dispel fidelity                    = DEFERRED_NON_BLOCKING
```

Project fallback ordering remains deterministic and clearly non-official.

---

## 30. Dependency / Boundary Acceptance Gate

### 30.1 Authoritative call/dependency edges

The following edges are authoritative. Arrows mean **consumer calls/depends on provider**:

```text
BattleEngine → ActionSystem
BattleEngine → BattleFinalizationCoordinator
BattleFinalizationCoordinator → VictorySystem
BattleFinalizationCoordinator → BattleTerminationRecord

ActionSystem → Stage9StateRuntime
ActionSystem → NormalAttackSystem

NormalAttackSystem → TargetResolutionSystem
NormalAttackSystem → DamageInstanceCoordinator
NormalAttackSystem → CleaveSystem
NormalAttackSystem → CounterSystem
NormalAttackSystem → FutureAdmissionGate (only its assigned Assault/CounterBatch/Combo branch edges)

EffectExecutor → DamageInstanceCoordinator
CounterSystem → DamageInstanceCoordinator

DamageInstanceCoordinator → DamageSystem
DamageInstanceCoordinator → DamagePartitionCoordinator
DamageInstanceCoordinator → DamageResolutionSystem
DamageInstanceCoordinator → DirectTroopLossResolver
DamageInstanceCoordinator → DamageCallbackAdmissionPoint
DamageInstanceCoordinator → finalization observation/barrier port

CleaveSystem → CleaveDerivedDamageResolver
CleaveSystem → FutureAdmissionGate (next independent CleaveEffect only)
CleaveDerivedDamageResolver → DamagePartitionCoordinator / settlement primitive as P0 permits
CleaveDerivedDamageResolver → DamageCallbackAdmissionPoint

DamageCallbackAdmissionPoint → FutureAdmissionGate
ChainSystem ← admitted ChainTraversal token from DamageCallbackAdmissionPoint
ChainSystem → restricted Chain settlement primitive

BattleSystems → constructs/injects every service above
```

Forbidden reverse/shortcut edges:

```text
BattleFinalizationCoordinator -X-> BattleEngine
local mechanism system        -X-> NormalAttackSystem to advance lifecycle
DamageInstanceCoordinator     -X-> EffectExecutor
ChainSystem                   -X-> self-admit a new traversal
StateRegistry                 -X-> infer source_skill_slot
EventBus subscriber           -X-> become Stage9 orchestration owner
```

This edge set has no required static dependency cycle. Ports/protocols may be used where needed to keep finalization observation and admitted-token flow acyclic.

### 30.2 BattleContext anti-service-locator boundary

Allowed new per-battle fields:

```text
OperationIdAllocator
small BattleTerminationRecord/read state
```

Forbidden in `BattleContext`:

```text
BattleSystems
mechanism systems
queues
policies
trace service
mechanism mutable runtime bags
```

Those remain owned/composed by `BattleSystems` or operation-local scopes.

### 30.3 Round1 repair final gate

```text
BLOCKER remaining               = 0
MAJOR remaining                 = 0
MINOR remaining                 = 0
DOC_ONLY remaining              = 0

Unowned runtime facts           = 0
Unspecified reachable paths     = 0
Unenforced invariants           = 0
Dependency cycles               = 0
Forward production dependency   = 0
Untestable mandatory regression = 0

P0 semantic change              = 0
new gameplay rule               = 0
Stage8 semantic reopen          = 0
planned NEW production files    = 16
planned MODIFY production files = 16
42 invariants                   = 42/42 enforced
45 regressions                  = 45/45 testable/mapped
```

The five Round1 previously unspecified path families are closed:

1. `Dtarget -> typed settlement -> event/result fact meanings`;
2. `EffectExecutor -> DamageInstanceCoordinator -> narrow DamageEffectResult`;
3. `source_skill_slot` producer -> Effect -> lifecycle -> StateInstance -> adapter/order;
4. finalization semantic state -> Engine compatibility projection/publication;
5. every global future branch -> exactly-one FutureAdmissionGate caller edge.

### 30.4 Current document status

```text
STAGE9.md
STATUS: DRAFT — DESIGN AUDIT REQUIRED

Stage9 FROZEN = NO
Ready for implementation = NO
Round2 Design Audit = REQUIRED
```

Round1 repair does not authorize implementation or Build Prompt creation.

Next permitted step:

```text
Stage9 Design Audit Round 2
```

Do not create `STAGE9_BUILD_PROMPT.md`, do not begin production implementation, and do not declare Stage9 FROZEN before Round2 independently verifies this repaired design.
