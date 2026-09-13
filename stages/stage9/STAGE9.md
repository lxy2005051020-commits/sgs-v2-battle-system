# STAGE 9 — Cross-Mechanism Runtime Orchestration

> STATUS: **DESIGN FROZEN — FREEZE AUDIT REQUIRED**  
> Authoring baseline (battle): `4745d061345181aaf12c454ada9890d7b69c5598`  
> Round1 repair baseline (battle): `05512d198c9016410ca14be2e40eb0c913cd1b77`  
> Round2 audit baseline (battle): `fbeca591fd9d5df014035a5aa643f15bb5389c68`  
> Authority baseline (state): `15ed915435f328a6ecd8f488d98b5b9e13c913b5`  
> Authoring date: 2026-09-13  
> Round1 repair date: 2026-09-13  
> Round2 design repair date: 2026-09-13  
> Round3 design audit: `PASS`  
> Design freeze reviewed commit: `394d32e40b6584db9814f46dfbf44a2d5e753893`  
> Design freeze reviewed `STAGE9.md` blob: `8972452d68d6c71e45563a9a2ec5d70826978c9b`  
> Design freeze approving audit commit: `524438ef97f8170fd81d026f82f7ecf6ae828a90`  
> Design freeze date: 2026-09-13  
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
Round1 design audit                = COMPLETE / FAIL — REPAIR REQUIRED
Round1 design repair               = COMPLETE
Round2 design audit                = COMPLETE / FAIL — REPAIR REQUIRED
Round2 design repair               = COMPLETE IN THIS SPEC REVISION
Round3 design audit                = COMPLETE / PASS
Stage9 Design Frozen               = YES
Stage9 Final Implementation Frozen = NO
Design Freeze Admission            = ELIGIBLE / CONSUMED
Implementation specification       = FROZEN
Implementation Design Ready        = YES
Build Prompt Admission             = PENDING FREEZE AUDIT
Build Prompt Authoring             = PENDING FREEZE AUDIT
Production Implementation          = NOT STARTED
STATUS                             = DESIGN FROZEN — FREEZE AUDIT REQUIRED
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

### 0.4 Round2 repair scope

This revision repairs only:

```text
R2-B01  Phase 9.2 legacy finalization compatibility bridge
R2-B02  authoritative Stage9 SourceType ingress for production DamageEffect
R2-M01  SkillSlot domain / concrete producer / reapply provenance
R2-M02  FutureAdmission structural no-bypass capability
R2-M03  deep-immutable FinalizationResult + exactly-once projection
R2-M04  Stage9 settlement replay guard
R2-N01  ExactRatio canonicalization / float ingress tightening
R2-N02  Effect provenance ergonomics
```

Repair constraints:

```text
P0 semantic change = 0
new gameplay rule = 0
Stage8 reopen = NO
state authority changes = 0
battle-report research = 0
production implementation = 0
```

---

## 1. Goals

Stage9 turns frozen cross-mechanism semantics into an implementable runtime architecture with:

- one explicit NormalAttack lifecycle owner;
- strong operation identity and source provenance;
- deterministic ordering with project defaults clearly labeled;
- a typed `Dtotal -> Dtarget -> ActualTargetTroopLoss` settlement chain;
- one global future-admission seam per future branch;
- one semantic finalization owner;
- structural one-shot capabilities where duplicate execution would be destructive;
- an acyclic dependency graph;
- independently green implementation phases;
- test seams for all 42 invariants and 45 mandatory regressions.

The design must make these questions answerable from types and call sites:

```text
Which Action / NormalAttack / DamageInstance owns this work?
Which target identity applies at this phase?
Is work not admitted, admitted, executing, locally cancelled, or completed?
Which exact damage layer is being consumed?
Which semantic source created this effect?
Which skill slot is authoritative when P0 requires slot order?
Which callbacks are legal for this source identity?
Has victory only latched, or is the battle FINALIZED?
Has settlement/future admission/final projection already consumed its one-shot right?
```

Engineering rule:

```text
explicit orchestration > implicit event ordering
strong identity > booleans
single semantic owner > duplicate convenience owners
capability-required destructive transitions > caller discipline
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
- `stages/stage9/audits/STAGE9_DESIGN_REPAIR_ROUND1.md`
- `stages/stage9/audits/STAGE9_DESIGN_AUDIT_ROUND2.md`
- `stages/stage9/audits/STAGE9_DESIGN_REPAIR_ROUND2.md`
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
- current `sgs_v2/battle_core/` and `tests/` layout at the Round2 audit baseline.

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

### 4.4 Stage9 one-shot settlement capability — `DamageSettlementPermit`

Stage9 settlement is destructive and therefore capability-gated.

```python
DamageSettlementPermit(
    permit_id: opaque runtime identity,
    damage_instance_id: DamageInstanceId,
)
```

Contract:

```text
issuer                     = DamageInstanceCoordinator
issued per DamageInstance  = at most one
consumer                   = DamageResolutionSystem.settle
lifetime                   = one DamageInstance settlement micro-scope
ordering role              = NONE
serialization/gameplay     = NONE
```

Stage9 API:

```python
DamageResolutionSystem.settle(
    context,
    request: DamageSettlementRequest,
    permit: DamageSettlementPermit,
) -> DamageResolutionResult
```

Before any `TroopSystem.apply_damage` call, settlement must atomically validate and consume the permit:

```text
request.origin == STAGE9
permit.damage_instance_id == request.damage_instance_id
permit is issued and unconsumed
→ consume permit atomically
→ only then perform troop mutation / events
```

Failure modes:

```text
reused permit
unknown permit
lineage / damage_instance_id mismatch
missing permit on STAGE9 request
```

are programmer/domain errors and produce:

```text
no troop mutation
no DAMAGE_DEALT
no UNIT_DEFEATED
no second settlement result
```

Replay protection is runtime structural state, not EventBus history inspection.

Permit state is operation-local. After settlement/completion the coordinator may release the consumed permit record. `BattleContext` must **not** accumulate a battle-long unbounded set of consumed DamageInstance IDs.

### 4.5 Legacy settlement compatibility

Legacy convenience path remains:

```python
DamageResolutionSystem.resolve(context, request: DamageRequest)
```

meaning:

```text
DamageSystem.calculate(request)
→ stack-local LEGACY_COMPAT DamageSettlementRequest(
     assigned_target_damage=result.final_damage,
     damage_instance_id=None,
     lineage=None,
  )
→ legacy full settlement
```

Each call to legacy `resolve()` is a new legacy operation. The Stage9 `DamageInstanceId` replay guard does **not** reinterpret or reject historical repeated legacy API calls.

`apply_result(context, damage)` may remain only as a legacy full-settlement wrapper. It may not gain an optional `assigned_amount` argument.

### 4.6 `DAMAGE_DEALT` event meaning

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

### 4.7 DAMAGE_FACT ownership matrix

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

Current production facts at Round2 audit baseline:

- `BattleEngine` owns round/action phase progression and currently has six terminal checkpoints plus compatibility side effects in `_finish()`.
- `BattleSystems` is the composition root.
- `ActionSystem` currently performs alive/STUN gate then calls `NormalAttackSystem`.
- `NormalAttackSystem` currently owns physical normal attack permission/target/settlement.
- `TargetSystem` is the common target/RNG query seam.
- `DamageSystem` owns the frozen Stage8 theoretical pipeline.
- `DamageResolutionSystem` owns current settlement and damage/death fact publication; current APIs are replayable by construction.
- `TroopSystem` is the sole troop mutation boundary and performs a mutation every time it is called.
- `VictorySystem` is already a pure world-state evaluator returning `BattleResult`.
- `BattleResult` is frozen as a dataclass but contains mutable `dict[str, int] final_troops`.
- `EventBus` explicitly documents facts-only semantics.
- `StateLifecycleSystem` is the sole formal state apply/remove/expire writer.
- `StateInstance` is frozen but currently stores only `source_id` + `source_skill_id`; it has no source slot.
- `StateRegistry` is the sole state container.
- `SkillRuntime` currently contains only `definition`, `owner_id`, and `enabled`; `UnitRuntime` has no skill loadout field.
- `SkillResolver` is the production constructor of active-skill `DamageEffect` and `ApplyStateEffect`.
- `TriggerSystem` is the production constructor of periodic/continuous `DamageEffect` from `StateInstance`.
- `RuleHookSystem` only routes `TriggerSystem.collect()` results to `EffectExecutor`; it does not construct effects.
- `EffectExecutor` currently routes `DamageEffect` directly to `DamageResolutionSystem.resolve()`.
- `RandomSystem` remains the unique battle RNG.

### 5.1 EXISTING_ARCHITECTURE_IMPACT_MATRIX

| Existing component | Stage9 action | Why |
|---|---|---|
| `BattleEngine` | MODIFY narrowly | legacy barrier bridge + future-action gate + finalized-result projection |
| `BattleContext` | MODIFY narrowly | operation-id allocator + small termination record only |
| `BattleSystems` | MODIFY | compose/inject Stage9 services |
| `ActionOrderSystem` | KEEP | existing ordering seam |
| `ActionSystem` | MODIFY | ActionId, ActionStart maintenance/grant |
| `NormalAttackSystem` | MODIFY / MASTER OWNER | orchestration-first master only |
| `TargetSystem` | KEEP / CALL | candidate/random primitives only |
| `AttributeSystem` | KEEP / CALL | live combat stats source |
| `DamageSystem` | KEEP / DO NOT TOUCH semantics | frozen Stage8 calculation owner |
| `DamageResolutionSystem` | MODIFY settlement seam only | typed settlement + one-shot consume |
| `TroopSystem` | KEEP / CALL | sole troop mutation primitive |
| `VictorySystem` | **KEEP / CALL** | already pure; no Stage9 gameplay edit required |
| `RandomSystem` | KEEP | sole RNG |
| `EventBus` | KEEP semantics / observation additions only | never control flow |
| `StateLifecycleSystem` | MODIFY provenance ingress only | store supplied source slot; mutation ownership unchanged |
| `StateInstance` | MODIFY provenance metadata only | store optional source slot |
| `StateRegistry` | KEEP | sole state container |
| `SkillRuntime` | MODIFY provenance | typed slot + holder-specific loading surface |
| `SkillResolver` | MODIFY provenance propagation | create authoritative `EffectSourceRef` |
| `effects.py` | MODIFY provenance carrier | own `EffectSourceRef`; Effects consume it |
| `effect_result.py` | MODIFY | stable Stage9 DamageEffect result shape |
| `EffectExecutor` | MODIFY narrowly | consume provenance and route completed DamageInstance path |
| `TriggerSystem` | **MODIFY provenance only** | periodic `DamageEffect` must create `PERIODIC_DAMAGE` source ref |
| `RuleHookSystem` | KEEP / CALL | routing only; no provenance invention |
| Stage8 formula/resolver internals | DO NOT TOUCH | frozen authority boundary |

No BattleEngine 2.0 and no second state runtime are introduced.

---

## 6. Design Principles, Error Taxonomy, and Engineering Capabilities

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
12. destructive/replay-sensitive runtime edges require one-shot capabilities
```

Additional rules:

- EventBus fact publication never substitutes for coordinator calls.
- No core ordering depends on subscriber registration, dict/hash iteration, or object address.
- Operation IDs and permit IDs are **NEVER gameplay ordering keys**.
- `FutureAdmissionPermit`, `DamageSettlementPermit`, and `FinalizationProjectionPermit` are engineering safety mechanisms only. They never change target selection, comparator order, damage, or P0 semantics.

### 6.1 Domain / programmer errors

Fail fast:

```text
missing required SkillSlot at a P0-required slot-order boundary
same-source refresh with mismatched source skill slot
reused DamageSettlementPermit
settlement permit / DamageInstance identity mismatch
reused FutureAdmissionPermit
future permit branch-kind or parent mismatch
double FinalizationProjectionPermit consumption
EffectExecutor missing authoritative Stage9 SourceType after the Phase 9.5 cutover
illegal recursive dispatch
duplicate/conflicting finalization identity
```

### 6.2 Expected battle-local invalidation

Typed safe skip/cancel, not programmer error:

```text
dead Cleave secondary
dead Counter owner
dead Counter target on already-admitted sibling (zero terminal per P0)
invalid Distribution planned participant
other P0-defined local liveness failure
```

### 6.3 Comparator labels

| Comparator | Runtime rule | Authority label |
|---|---|---|
| battle/unit slot | lineup order, then stable `unit_id` only if a tie still exists | `PROJECT_DETERMINISTIC_DEFAULT` for `unit_id`; **NOT EMPIRICALLY PROVEN / NOT OFFICIAL ORDER** |
| Cleave source effects | authoritative `source_skill_slot` ascending | P0-derived; missing required slot = domain error |
| Cleave secondary targets | `GLOBAL_SLOT_ASCENDING` | P0-derived |
| Chain traversal | stable global slot ascending, monotonic cursor | P0-derived |
| Counter fallback where universal comparator remains open | stable mechanism-local source/instance fallback | `PROJECT_DETERMINISTIC_DEFAULT`; **NOT EMPIRICALLY PROVEN / NOT OFFICIAL ORDER** |

Stable state-instance identity may be used only as a deterministic fallback where P0 explicitly leaves fidelity open. Operation IDs/permit IDs never resolve gameplay ties.

---

## 7. Global Runtime Topology

```text
BattleEngine
  ├─ BattleFinalizationCoordinator
  │    ├─ VictorySystem (pure evaluator)
  │    ├─ LegacyFinalizationBarrier adapter ingress
  │    ├─ FinalizationResult / FinalizationProjectionPermit
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
            │    ├─ DamageSettlementPermit issuer
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
    target = target_resolution.resolve(na, actor)
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
→ create typed DamageSettlementRequest(Dtarget)
→ issue exactly one DamageSettlementPermit for this DamageInstanceId
→ atomically consume permit before target troop mutation
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
UnitDeathFact or legacy macro observation barrier
→ BattleFinalizationCoordinator invokes/consumes VictorySystem pure evaluation
→ RUNNING -> VICTORY_LATCHED
→ FutureAdmissionGate rejects new global FutureBranches
→ if admitted Stage9 work exists: DRAINING_ADMITTED_WORK
→ admitted local operations obey P0 drain/cancel rules
→ operation completion facts drain
→ FINALIZED once + deep-immutable FinalizationResult once
→ coordinator issues FinalizationProjectionPermit once
→ BattleEngine consumes permit
→ context.ended/context.result + BATTLE_END + BATTLE_ENDED compatibility projection once
```

`VICTORY_LATCHED != FINALIZED` is structural.

---

## 8. Operation Identity & Provenance

### 8.1 Strong identities

All operation IDs are immutable typed values allocated by one per-battle `OperationIdAllocator` using deterministic monotonic sequences. IDs are runtime/trace identity, never gameplay priority.

| ID | Generator | Lifetime | Parent | Status |
|---|---|---|---|---|
| `ActionId` | ActionSystem | one unit Action | root | required |
| `NormalAttackInstanceId` | NormalAttackSystem | one physical NA | ActionId | required |
| `TargetResolutionId` | TargetResolutionSystem | one target resolve | NormalAttackId | TRACE_ONLY SUPPORTING ID |
| `DamageInstanceId` | damage/derived owner | one damage event | NA/parent damage | required |
| `PartitionTransactionId` | partition coordinator | one transaction | DamageInstanceId | required |
| `ReactionBatchId` | CounterSystem | one admitted batch | NormalAttackId | required |
| `CounterBatchEntryId` | CounterSystem | one batch entry | ReactionBatchId | required |
| `CleaveEffectId` | CleaveSystem | one effect execution | NormalAttackId | required |
| `ChainTraversalId` | ChainSystem | one traversal | DamageInstanceId | required |
| `DirectTroopLossId` | DirectTroopLossResolver | one direct commit | PartitionTransactionId | required |

`TargetResolutionId` is retained only for trace correlation and is not a gameplay prerequisite or ordering key.

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

Forbidden reverse inference:

```text
DamageSourceType.SKILL       -X-> infer SourceType.ACTIVE_SKILL
DamageSourceType.CONTINUOUS  -X-> infer SourceType.PERIODIC_DAMAGE
DamageSourceType.COUNTER     -X-> infer runtime parent/permission identity
```

Stage8 classification never becomes Stage9 provenance authority.

### 8.3 `EffectSourceRef` — creation/application provenance

`effects.py` owns the narrow provenance value to avoid scattering correlated fields across each Effect:

```python
EffectSourceRef(
    stage9_source_type: SourceType,
    source_unit_id: str | None,
    source_skill_id: str | None,
    source_skill_slot: SkillSlot | None,
)
```

Rules:

```text
ACTIVE_SKILL production-loaded path
→ source_unit_id required
→ source_skill_id required
→ source_skill_slot supplied from holder-specific LoadedSkillRef

PERIODIC_DAMAGE from a skill-sourced StateInstance
→ stage9_source_type = PERIODIC_DAMAGE
→ preserve original source_unit_id/source_skill_id/source_skill_slot

system/external/non-skill source
→ source_skill_id/source_skill_slot may be None
```

Existing state-instance identity metadata (`source_state_id`, `source_state_instance_id`) stays on the damage/effect fact where it is already semantically required; it is not duplicated as a second authority inside `EffectSourceRef`.

`DamageEffect` and `ApplyStateEffect` use one `source_ref` as the Stage9 provenance authority. During compatibility migration, existing scalar fields may be retained only as read-only projections/adapters and must never disagree with `source_ref`.

### 8.4 `EffectSourceRef` vs `OperationLineage`

```text
EffectSourceRef
=
effect creation/application provenance
can exist before Stage9 operation IDs exist

OperationLineage
=
runtime execution ancestry
contains Stage9 operation identities and current operation SourceType
```

At DamageInstance admission:

```text
EffectSourceRef + runtime parent scope
→ DamageInstanceCoordinator constructs OperationLineage
```

The two types are deliberately not merged into one universal bag.

### 8.5 `OperationLineage`

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

`source_type` describes current operation permission identity. `physical_skill` and `credit_owner` retain original attribution where required. Periodic damage therefore has:

```text
lineage.source_type = PERIODIC_DAMAGE
physical_attacker / physical_skill / credit_owner = original attribution as applicable
```

### 8.6 DAMAGE_EFFECT_SOURCE_INGRESS_MATRIX

Round2 production scan of `sgs_v2/battle_core` finds two production constructors of `DamageEffect`:

| Producer | Semantic origin | Stage8 `DamageSourceType` | authoritative Stage9 `SourceType` producer | Slot source |
|---|---|---|---|---|
| `SkillResolver._build_effect` | active skill `DamageSkillEffectSpec` | `SKILL` | `SkillResolver` creates `EffectSourceRef(ACTIVE_SKILL, ...)` from the executing `SkillRuntime` | `LoadedSkillRef.skill_slot` carried by runtime; legacy fixture may be `None` but slot-required mechanisms reject it |
| `TriggerSystem._effects_for_state` | periodic/continuous damage from `StateInstance` | `CONTINUOUS` | `TriggerSystem` creates `EffectSourceRef(PERIODIC_DAMAGE, ...)` | preserved `StateInstance.source_skill_slot` |

Non-producers:

```text
EffectExecutor     = consumer/router only
RuleHookSystem     = TriggerSystem -> EffectExecutor route only
NormalAttackSystem = directly constructs a Stage8 DamageRequest today; it does not construct DamageEffect
```

NormalAttack Stage9 ingress is therefore separately authoritative at the NormalAttack/DamageInstance boundary:

```text
NormalAttackSystem / DamageInstanceCoordinator
→ SourceType.NORMAL_ATTACK
→ one-way Stage8 mapping to DamageSourceType.NORMAL_ATTACK
```

Phase 9.5 cutover gate:

```text
every production-reachable DamageEffect has EffectSourceRef
active skill producer emits ACTIVE_SKILL directly
periodic producer emits PERIODIC_DAMAGE directly
EffectExecutor never reverses DamageSourceType
all source refs preserve attribution
unclassified production DamageEffect = 0
```

---

## 9. Target Resolution

### 9.1 Immutable result

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

It is explicitly forbidden to own target algorithms, partition math, state storage mutation, Cleave/Chain/Counter internals, finalization writes, or Stage8 formulas.

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
→ FutureAdmissionGate.try_admit(COMBO_SECOND_NORMAL_ATTACK)
→ receive/consume FutureAdmissionPermit before allocating NormalAttack #2
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

Cleave state remains in `StateRegistry`; `Stage9StateRuntime` returns typed views. Cleave source ordering uses authoritative `StateInstance.source_skill_slot: SkillSlot | None`.

For a skill-sourced Cleave state where P0 requires skill-slot order:

```text
source_skill_slot is required
None = domain error
skill_id ordering fallback = FORBIDDEN
OperationId ordering fallback = FORBIDDEN
```

Production loadout invariants make two distinct active skill sources from the same holder and same `SkillSlot` unreachable. If a corrupted/legacy fixture violates that invariant, it is a domain error rather than a gameplay comparator invention.

### 14.2 Cleave-specific derived boundary

The owner is:

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

### 14.3 Effect queue

```text
CleaveEffect A: secondary 1 → secondary 2
then CleaveEffect B: secondary 1 → secondary 2
```

Each independent CleaveEffect is admitted only after a `FutureAdmissionPermit` is issued and consumed. Each admitted effect freezes its secondary identity plan. Each secondary is local work inside that admitted effect and does not re-query the global gate. JIT liveness still applies.

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

### 15.2 Deferred work

Snapshot only trigger facts (`parent_damage_instance_id`, trigger node, trigger damage, provenance). Execution-time state/owner/ratio/candidate eligibility remains live-read where P0 requires it.

A new traversal can be constructed only from a consumed `FutureAdmissionPermit(branch_kind=CHAIN_TRAVERSAL)` issued by the one `DamageCallbackAdmissionPoint`. `ChainSystem` cannot self-admit.

`CHAIN_TRUE_FEEDBACK` is not a Stage8 `DamageRequest`; it has its own restricted settlement and permission set.

---

## 16. Counter

Counter remains three layers:

```text
trigger-time eligible-state snapshot
→ immutable CounterBatch entries
→ execution-time owner/target liveness gates
```

A new `CounterBatch` can be constructed only after `FutureAdmissionGate` issues a `COUNTER_BATCH` permit and the Counter factory consumes it.

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
- never substitute `skill_id` or OperationId sorting for P0-required skill-slot sorting.

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

### 17.2 One gate, typed branch kind

```python
FutureBranchKind = (
    NEXT_ACTION
    | ASSAULT
    | COMBO_SECOND_NORMAL_ATTACK
    | COUNTER_BATCH
    | CHAIN_TRAVERSAL
    | CLEAVE_EFFECT
)
```

`FutureAdmissionGate` is the single global admission authority.

### 17.3 `FutureAdmissionPermit`

Gate approval returns a one-shot capability:

```python
FutureAdmissionPermit(
    permit_id: opaque runtime identity,
    branch_kind: FutureBranchKind,
    parent_scope_identity: typed parent identity,
    termination_generation: int,
)
```

Rules:

```text
Gate evaluates current termination/admission state
→ if allowed, issues one permit
→ permit is immediately consumed by the assigned branch factory/dispatch adapter
→ only after successful consume may future operation identity be allocated/admitted
```

Forbidden:

```text
new CounterBatch()
then ask gate

allocate NormalAttack #2 ID
then ask gate

construct ChainTraversal
then ask gate
```

The permit is not a gameplay object and never participates in ordering. It is not copied or stored long-term. Issued/consumed records are micro-scope state and may be discarded once the branch has been admitted; no battle-long unbounded permit history is required.

Permit validation includes:

```text
issued by this gate
not already consumed
branch_kind matches factory
parent_scope_identity matches caller/factory
termination generation has not invalidated the admission before consume
```

Mismatch/reuse is a domain error.

### 17.4 FUTURE_ADMISSION_CALLER_MATRIX

Every global future branch has **EXACTLY ONE authoritative gate caller** and a permit-required construction surface.

| Future branch | Exactly-one authoritative caller | Gate point | Permit consumer |
|---|---|---|---|
| next Action | `BattleEngine` | immediately before dispatching next Action lifecycle | Phase 9.2 legacy dispatch adapter; Phase 9.6 real `ActionScope` factory |
| Assault | `NormalAttackSystem` master | before dispatch | `AssaultDispatchPort` |
| Combo #2 | Combo checkpoint | after consume/local attack permission, before allocating NA #2 | `NormalAttackSystem` NA factory |
| new CounterBatch | `NormalAttackSystem` post-hit reaction admission point | before batch snapshot/allocation | `CounterSystem` batch factory |
| new ChainTraversal | shared `DamageCallbackAdmissionPoint` | after eligible resolved damage fact | `ChainSystem` traversal factory |
| next unadmitted CleaveEffect | `CleaveSystem` effect-loop boundary | before independent effect plan/ID | `CleaveSystem` effect factory |

### 17.5 Required construction APIs

Public production constructors/factories for future branches must require a permit argument. Conceptual signatures:

```python
LegacyActionDispatchAdapter.dispatch(..., permit: FutureAdmissionPermit)   # Phase 9.2
ActionScope.admit(..., permit: FutureAdmissionPermit)                     # Phase 9.6
AssaultDispatchPort.dispatch(..., permit: FutureAdmissionPermit)
NormalAttackSystem.allocate_combo_attack(..., permit: FutureAdmissionPermit)
CounterSystem.create_batch(..., permit: FutureAdmissionPermit)
ChainSystem.create_traversal(..., permit: FutureAdmissionPermit)
CleaveSystem.create_effect(..., permit: FutureAdmissionPermit)
```

No permit means the future branch cannot be constructed/admitted through production API.

### 17.6 Already-admitted work does not re-query global admission

Examples:

```text
Counter sibling already in admitted batch
next slot inside admitted ChainTraversal
next secondary inside current admitted CleaveEffect
next planned Distribution participant
pending Share sharer step inside admitted Share transaction
current DamageInstance local callback already admitted by its operation contract
```

These use local liveness/P0 rules only.

### 17.7 INV-40 structural closure

INV-40 is enforced jointly by:

```text
single FutureAdmissionGate
+ typed FutureAdmissionPermit
+ permit-required future-branch factories/dispatch adapter
+ assigned caller matrix
+ no-bypass architecture test
```

`context.ended` is never a semantic future-work gate. It becomes true only after finalized compatibility projection.

---

## 18. Battle Finalization

### 18.1 Ownership split

`VictorySystem` remains a pure evaluator. No Stage9 gameplay edit is required for its behavior.

`BattleFinalizationCoordinator` is the **unique semantic owner** of:

```text
BattleTerminationState
victory latch identity/result
RUNNING -> VICTORY_LATCHED
VICTORY_LATCHED -> DRAINING_ADMITTED_WORK
DRAINING_ADMITTED_WORK -> FINALIZED
FinalizationResult creation
FinalizationProjectionPermit issuance/consume validation
final operation-drain barrier
termination-state fact consumed by FutureAdmissionGate
```

`BattleEngine` remains outer loop and compatibility projection consumer only.

### 18.2 Current legacy terminal checkpoints

Round2 code scan finds exactly six current production terminal checkpoints in `BattleEngine.run()`.

#### LEGACY_FINALIZATION_BARRIER_MATRIX

| Existing barrier | Current production location | Current evaluation timing | Phase 9.2 adapter | Ordering preserved? |
|---|---|---|---|---|
| `INITIAL_SETTLED` | after PRE_BATTLE `PHASE_ENTERED` + `BATTLE_STARTED` | `VictorySystem.check` before entering round 1 | `coordinator.observe_legacy_barrier(context, INITIAL_SETTLED)` | YES |
| `ROUND_START_HOOKS_SETTLED` | after ROUND_START expiry + `ROUND_STARTED` + `RoundStartHook` processing | `VictorySystem.check` after hook completes | observe same barrier; coordinator calls pure `check` | YES |
| `UNIT_ACTION_START_HOOKS_SETTLED` | after `UNIT_ACTION_STARTED` + `UnitActionStartHook` | `VictorySystem.check` before Action execution | observe same barrier; coordinator calls pure `check` | YES |
| `ACTION_SETTLED` | immediately after `ActionSystem.execute` | `VictorySystem.check` before entering/publishing UNIT_ACTION_END | observe same barrier and latch/finalize semantically; **Engine projection claim is delayed until after existing `UNIT_ACTION_ENDED` publication** | YES |
| `ROUND_END_SETTLED` | after `ROUND_ENDED` + ROUND_END state expiry | `VictorySystem.check` | observe same barrier; coordinator calls pure `check` | YES |
| `MAX_ROUND_SETTLED` | after the final round loop completes | `VictorySystem.resolve_max_rounds` | observe max-round barrier; coordinator invokes max-round evaluator once | YES |

```text
mapped current terminal checkpoints = 6/6
hook-after barriers included         = YES
max-round barrier included           = YES
unmapped terminal checkpoint         = 0
```

### 18.3 `LegacyFinalizationBarrier` contract

```python
class LegacyFinalizationBarrier(Enum):
    INITIAL_SETTLED = ...
    ROUND_START_HOOKS_SETTLED = ...
    UNIT_ACTION_START_HOOKS_SETTLED = ...
    ACTION_SETTLED = ...
    ROUND_END_SETTLED = ...
    MAX_ROUND_SETTLED = ...
```

It means only:

> the current legacy synchronous work for this macro checkpoint has completely settled, so finalization may safely observe world state now.

It is **not** a gameplay event and does not:

```text
evaluate mechanism rules
set context.ended
set context.result
enter BATTLE_END
publish BATTLE_ENDED
```

It is a typed adapter signal into the one semantic finalization owner.

### 18.4 Phase 9.2 compatibility API

Normative shape:

```python
BattleFinalizationCoordinator.observe_legacy_barrier(
    context: BattleContext,
    barrier: LegacyFinalizationBarrier,
) -> None

BattleFinalizationCoordinator.claim_finalized_projection(
) -> tuple[FinalizationProjectionPermit, FinalizationResult] | None

BattleFinalizationCoordinator.consume_projection_permit(
    permit: FinalizationProjectionPermit,
) -> None
```

Barrier evaluation:

```text
INITIAL / ROUND_START / UNIT_ACTION_START / ACTION / ROUND_END
→ VictorySystem.check(context)

MAX_ROUND_SETTLED
→ VictorySystem.resolve_max_rounds(context)
```

Coordinator then:

```text
no victory
→ remain RUNNING

victory
→ latch once
→ if admitted Stage9 work exists: DRAINING_ADMITTED_WORK
→ else FINALIZED once and create FinalizationResult once
```

### 18.5 Phase 9.2 compatibility bridge

Phase 9.2 has:

```text
real BattleFinalizationCoordinator
real LegacyFinalizationBarrier signals
real FutureAdmissionGate base capability
Stage9 admitted-operation set = EMPTY
ActionScope count = 0
DamageInstance scope count = 0
ReactionBatch scope count = 0
stub operation scopes = FORBIDDEN
```

Therefore:

```text
BattleEngine reaches existing legacy barrier
→ coordinator.observe_legacy_barrier(...)
→ coordinator invokes VictorySystem pure evaluator
→ no victory: Engine continues exactly as before
→ victory: latch -> FINALIZED immediately because admitted-operation set is empty
→ deep-immutable FinalizationResult created once
→ Engine claims one projection permit at the existing compatibility projection point
→ Engine consumes permit
→ Engine performs legacy result/event projection once
```

For `ACTION_SETTLED`, semantic finalization may already be ready immediately after the existing check point, but Engine must preserve the historical observable order:

```text
ActionSystem.execute
→ ACTION_SETTLED observation
→ enter UNIT_ACTION_END
→ publish UNIT_ACTION_ENDED
→ claim/consume finalized projection
→ enter BATTLE_END
→ publish BATTLE_ENDED
```

Thus evaluation timing and externally visible event ordering are both preserved.

**Phase 9.2 independently green verdict:** YES. Stage1-8 termination behavior requires no fake Action/Damage/Reaction scope.

### 18.6 Post-9.6/9.7 operation relationship

Once real operation scopes exist, legacy macro barriers remain finalization opportunities, but are not “force finalize” instructions.

```text
victory observed
→ VICTORY_LATCHED
→ FutureAdmissionGate blocks new global future branches
→ if previously admitted work remains:
     DRAINING_ADMITTED_WORK
→ local P0 drain/cancel rules execute
→ operation completion facts drain
→ FINALIZED only when admitted-work barrier is clear
```

The legacy adapter never becomes a second semantic owner.

### 18.7 Deep-immutable `FinalizationResult`

The current legacy `BattleResult.final_troops` is mutable despite the frozen outer dataclass. Stage9 therefore does not embed a `BattleResult` reference.

```python
FinalizationResult(
    finalization_id: FinalizationId,
    winner_team_id: str | None,
    reason: BattleEndReason,
    rounds_completed: int,
    final_troops_snapshot: tuple[tuple[str, int], ...],
)
```

Rules:

```text
frozen dataclass / immutable value
final_troops_snapshot deep-copied from live units at finalization
canonical tuple sorted by stable unit_id for snapshot serialization only
sorting is NOT gameplay winner/order logic
no mutable dict/list/reference reachable from result
```

Legacy projection is data-only:

```python
BattleResult(
    winner_team_id=result.winner_team_id,
    reason=result.reason,
    rounds_completed=result.rounds_completed,
    final_troops=dict(result.final_troops_snapshot),  # fresh compatibility dict
)
```

Projection never calls `VictorySystem` again.

### 18.8 `FinalizationProjectionPermit` exactly once

```python
FinalizationProjectionPermit(
    permit_id: opaque battle-lifetime identity,
    finalization_id: FinalizationId,
)
```

Coordinator rules:

```text
FinalizationResult creation = once
projection permit claim     = once
permit consume              = once
second claim                = None
second consume              = domain/programmer error
```

Engine:

```python
claim = coordinator.claim_finalized_projection()
if claim is not None:
    permit, result = claim
    coordinator.consume_projection_permit(permit)  # before any compatibility side effect
    return self._apply_finalized_battle_result(result)
```

`_apply_finalized_battle_result` may only:

```text
construct fresh legacy BattleResult from immutable snapshot
context.ended = True
context.result = legacy result
enter BATTLE_END
publish BATTLE_ENDED
return legacy result
```

It may not evaluate victory, decide drain completion, issue permits, or create a second finalized result.

Exactly-once guarantee:

```text
multiple death facts / operation completion facts / legacy barriers
may call try_finalize repeatedly
BUT
FinalizationResult creation = once
FinalizationProjectionPermit issuance = once
BATTLE_END transition = once
BATTLE_ENDED publication = once
```

Permit lifetime is one battle and one projection only.

### 18.9 Writer matrix

| Field/effect | Unique writer | Rule |
|---|---|---|
| termination state | `BattleFinalizationCoordinator` | only coordinator transitions it |
| victory latch | `BattleFinalizationCoordinator` | semantic decision owner |
| `FinalizationResult` | `BattleFinalizationCoordinator` | created once |
| projection capability | `BattleFinalizationCoordinator` | issued/validated once |
| `context.ended` | `BattleEngine` permit-backed projection | only after permit consume |
| `context.result` | `BattleEngine` permit-backed projection | fresh legacy projection |
| `BATTLE_END` phase | `BattleEngine` permit-backed projection | exactly once |
| `BATTLE_ENDED` event | `BattleEngine` permit-backed projection | exactly once |

Coordinator decides; Engine projects. They do not co-own semantic finalization.

### 18.10 Dependency direction

```text
BattleEngine
→ BattleFinalizationCoordinator
→ VictorySystem

NEVER:
BattleFinalizationCoordinator
→ BattleEngine._finish / _apply_finalized_battle_result
```

---

## 19. Recursion / Permission Policy

`ReactionPermissionPolicy` is a centralized typed table over `SourceType`, NormalAttack identity, and lineage.

| From | Cleave | Counter | Chain | Share | Distribution | FirstAid / Recovery |
|---|---:|---:|---:|---:|---:|---:|
| NORMAL_ATTACK | ALLOW by trigger P0 | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW where P0 permits |
| ACTIVE_SKILL / PERIODIC_DAMAGE | only where current P0 permits | only where current P0 permits | only where current P0 permits | by P0 | by P0 | by P0 |
| CLEAVE | BLOCK | BLOCK | ALLOW | ALLOW | ALLOW | ALLOW by Cleave P0 |
| COUNTER | BLOCK | BLOCK | ALLOW | ALLOW | ALLOW | ALLOW by Counter P0 |
| CHAIN_TRUE_FEEDBACK | BLOCK/N/A | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK |
| SHARE_DIRECT_LOSS | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK |
| DISTRIBUTION_DIRECT_LOSS | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK |

This table does not invent new active-skill/periodic reactions. Any cell not already frozen by P0 remains denied/deferred according to existing permission authority; Stage9 source identity merely makes the decision explicit.

NormalAttack-only selector/Guard/Assault/Combo paths require NormalAttack identity.

---

## 20. Exact Numeric Representation

### 20.1 Canonical `ExactRatio`

Stage9 freezes a rational representation:

```python
ExactRatio(
    numerator: int,
    denominator: int,
)
```

Canonicalization is mandatory:

```text
denominator > 0
gcd(|numerator|, denominator) reduced to 1
sign normalized to numerator
zero canonical form = 0 / 1
```

Examples:

```text
54/100   -> 27/50
27/50    -> 27/50
540/1000 -> 27/50
0/7      -> 0/1
-54/-100 -> 27/50
54/-100  -> -27/50
```

Mechanism call sites still enforce any P0-specific nonnegative/range constraints.

### 20.2 Preferred ingress

Preferred Stage9 ingress, in order:

```text
raw textual decimal
Decimal
integer percent / basis points
exact numerator + denominator
```

These convert directly to canonical `ExactRatio` without a binary-float arithmetic step.

### 20.3 No generic float constructor

Stage9 core does **not** expose:

```python
ExactRatio.from_float(...)
```

Current Round2 production scan identifies no Stage9 exact-ratio source that is forced to originate as a legacy float-only scalar, so no float adapter is required for Phase 9.1.

If a future named legacy compatibility boundary is proven to expose only a raw loaded float, the only permitted adapter shape is explicit and non-generic:

```python
exact_ratio_from_legacy_config_float(raw_loaded_value: float) -> ExactRatio
```

with all constraints:

```text
raw loaded scalar only
never a computed float
Decimal(str(value))
clearly documented as compatibility-only
cannot recover precision lost before this boundary
```

Forbidden:

```text
Decimal(value)
Fraction(value) from float
generic ExactRatio.from_float
computed float -> adapter
float multiplication then floor/round
Python round()
```

### 20.4 Integerization API

```python
floor_product_int_ratio(base: int, ratio: ExactRatio) -> int
round_half_up_product_int_ratio(base: int, ratio: ExactRatio) -> int
round_half_up_divide_int(numerator: int, denominator: int) -> int
```

For nonnegative gameplay quantities these use exact integer arithmetic.

| Call site | Rule |
|---|---|
| Chain | `FLOOR` |
| Cleave | `FLOOR` |
| Share `Dsharer` | `ROUND_HALF_UP` |
| Distribution `Dtarget` | `ROUND_HALF_UP` |
| Distribution participant | `ROUND_HALF_UP` |

RF-C01 vectors remain the executable oracle.

---

## 21. State Runtime Integration / `SkillSlot`

### 21.1 No second state runtime

```text
BattleContext.states : StateRegistry
StateLifecycleSystem : only physical state mutation writer
Stage9StateRuntime   : typed read/maintenance adapter only
```

### 21.2 Typed `SkillSlot` domain

The internal equipped-slot domain is explicit and 0-based:

```python
class SkillSlot(IntEnum):
    INHERENT  = 0
    LEARNED_1 = 1
    LEARNED_2 = 2
```

```text
internal indexing = 0-based
legal values       = {0, 1, 2}
```

No raw arbitrary `int` is accepted by Stage9 slot-dependent contracts.

`SkillDefinition` remains static and **does not own slot**.

### 21.3 Current production gap and concrete holder-specific ingress

Round2 code inspection confirms:

```text
SkillRuntime current fields = definition, owner_id, enabled
UnitRuntime has no skill/loadout collection
no existing holder-specific production loadout object exists
```

Therefore Phase 9.3 adds the minimal holder-specific loading surface in `skill_runtime.py`, not a new gameplay system:

```python
LoadedSkillRef(
    owner_id: str,
    definition: SkillDefinition,
    skill_slot: SkillSlot,
)

LoadedSkillSet(
    owner_id: str,
    loaded: tuple[LoadedSkillRef, ...],
)
```

`LoadedSkillSet` validates:

```text
all refs belong to same owner
skill_slot values are legal typed SkillSlot values
no duplicate slot for one holder
```

and is the authoritative production construction surface for holder-equipped Stage9 skill runtimes:

```python
SkillRuntime.from_loaded(ref: LoadedSkillRef, *, enabled: bool = True)
```

`SkillRuntime` stores `skill_slot: SkillSlot | None` as provenance. `None` remains available only for legitimate non-equipped/system/external/legacy-fixture cases; downstream P0-required slot boundaries reject it.

This is a representation/validation contract, not a gameplay ordering invention.

### 21.4 Same-slot collision policy

For production-loaded skills:

```text
same holder + same SkillSlot + two distinct LoadedSkillRef
= structurally invalid loadout
= domain error at LoadedSkillSet construction
```

Thus two distinct active skill sources from one holder with the same equipped slot are unreachable in the legal production loadout model. Architecture tests enforce this invariant.

No OperationId or `skill_id` comparator is introduced to paper over an invalid loadout.

### 21.5 Provenance propagation

```text
LoadedSkillRef / LoadedSkillSet
→ SkillRuntime.skill_slot
→ SkillResolver builds EffectSourceRef
→ DamageEffect / ApplyStateEffect
→ EffectExecutor / StateLifecycleSystem.apply
→ StateInstance.source_skill_slot
→ TriggerSystem preserves slot for periodic EffectSourceRef
→ Stage9StateRuntime typed view
→ Cleave / Counter ordering where P0 requires
```

`DamageRequest` remains a Stage8 formula request and gains no slot field solely for orchestration.

### 21.6 StateInstance provenance

`StateInstance` stores only durable source metadata needed by later mechanisms:

```text
source_id: str | None
source_skill_id: str | None
source_skill_slot: SkillSlot | None
```

It does **not** store transient operation IDs such as `ActionId` or `DamageInstanceId` unless a future P0 explicitly requires such persistence.

### 21.7 Refresh / reapply slot semantics

Generic lifecycle does not invent a universal stacking/refresh gameplay rule. Where a frozen mechanism chooses **same-source refresh/reapply** of an existing physical instance, Stage9 freezes the provenance guard:

```text
same-source identity key
=
(owner_id, state_id, source_id, source_skill_id)
```

If refresh targets that existing source identity:

```text
incoming source_skill_slot == existing source_skill_slot
→ mechanism-specific refresh may proceed

incoming source_skill_slot != existing source_skill_slot
→ DOMAIN ERROR
→ provenance is never silently overwritten
```

If a P0 mechanism legitimately creates a separate stack/instance instead of refreshing, each new frozen `StateInstance` keeps its own immutable source provenance.

### 21.8 `None` policy

`SkillSlot | None` is valid for:

```text
system source
external/non-skill source
legacy fixture not entering a P0 slot-order mechanism
```

P0-required `SKILL_SLOT_ORDER` receiving `None` is a domain error unless that mechanism's P0 explicitly defines an alternate comparator.

### 21.9 INV-18 structural closure

INV-18 is enforced by:

```text
typed SkillSlot legal domain
+ authoritative holder-specific LoadedSkillRef/LoadedSkillSet producer
+ propagation through EffectSourceRef and StateInstance
+ immutable refresh/reapply provenance guard
+ runtime rejection of missing slot at P0-required comparator
+ duplicate same-holder same-slot loadout rejection
```

---

## 22. Recovery / Trigger Integration

Stage9 does not redesign Stage7 trigger/recovery gameplay semantics.

- `TriggerSystem` remains fact-to-Effect collector, but is **MODIFIED for provenance production only**.
- `RuleHookSystem` remains an unchanged routing layer.
- `RecoverySystem` remains recovery execution owner.
- `TroopSystem.restore` remains write boundary.
- EventBus remains observation-only.

Periodic damage path after Phase 9.3/9.5 provenance wiring:

```text
StateInstance(original source_id/source_skill_id/source_skill_slot)
→ TriggerSystem creates EffectSourceRef(
     stage9_source_type=PERIODIC_DAMAGE,
     original source metadata...
   )
→ DamageEffect still carries Stage8 DamageSourceType.CONTINUOUS independently
→ EffectExecutor consumes source_ref
→ DamageInstanceCoordinator builds runtime OperationLineage
```

No reverse enum inference is permitted.

Damage-event basis remains:

```text
NormalAttack standard damage: existing eligible recovery hooks
Counter positive standard DamageEvent: permitted hooks under Counter P0
Cleave derived DamageEvent: permitted hooks under Cleave P0
Chain TRUE_FEEDBACK: blocked where Chain P0 blocks
Share/Distribution direct loss: never recovery damage basis
Counter dead-target zero terminal: no damage basis
```

---

## 23. Trace & Observability

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

Tests may use a full-detail sink for fixture lifetime.

Trace may observe Action admission/completion/cancel, NormalAttack creation/completion, TargetResolution, DamageInstance/Dtotal/Dtarget/actual loss, partition steps, derived effects, CounterBatch, Chain cursor, future admission, and finalization transitions.

```text
Event = observation / notification
Coordinator call = authoritative control flow
```

No Stage9 sequencing depends on subscriber order.

---

## 24. Runtime Invariants — Round2 Re-coverage

All 42 RF-C01 invariants remain mapped. Round2 identified exactly three unenforced invariants: **INV-18, INV-40, INV-42**. This repair closes all three without gameplay semantic change.

| Invariant | Primary enforcement after Round2 repair |
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
| INV-18 | **STRUCTURAL + TYPE + RUNTIME: SkillSlot domain + LoadedSkill ingress + immutable reapply provenance + required missing-slot rejection** |
| INV-19 | TYPE: direct loss distinct from DamageEvent |
| INV-20 | STRUCTURAL: direct loss bypasses HitResolution |
| INV-21 | TYPE: explicit provenance value object |
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
| INV-40 | **STRUCTURAL: single gate + FutureAdmissionPermit + permit-required factories + no-bypass test** |
| INV-41 | **STRUCTURAL: coordinator unique termination/final result/projection-permit owner; Engine permit consumer only** |
| INV-42 | **STRUCTURAL + TYPE: EffectSourceRef authoritative SourceType producers + no reverse DamageSourceType inference + lineage/permission mapping** |

```text
TOTAL      = 42
ENFORCED   = 42
UNENFORCED = 0
TEST-ONLY  = 0
```

Supporting one-shot settlement/finalization architecture contracts strengthen existing invariants; they do not create new gameplay invariants or semantic IDs.

---

## 25. Regression Mapping and Architecture Test Readiness

### 25.1 Mandatory gameplay regressions

Mandatory gameplay contract count remains exactly **45** and all remain testable. Round2 repairs add structural seams, not gameplay IDs.

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

A supporting settlement fixture must still realize:

```text
Dtotal != Dtarget != ActualTargetTroopLoss
```

and assert each layer separately.

### 25.2 Required architecture tests — 12/12 READY

| Architecture guarantee | Planned test seam | Status after repair |
|---|---|---|
| no Stage8 semantic/import inversion | Stage8 calculation types never import Stage9 mechanism services | READY |
| FutureAdmissionGate no bypass | every global future branch factory/adapter requires gate-issued permit | **READY** |
| finalization single semantic writer | only coordinator mutates termination/finalization semantic state | READY |
| Engine final projection exactly once | repeated claim/consume cannot emit second BATTLE_END/BATTLE_ENDED | **READY** |
| OperationId never gameplay ordering | static/source test forbids operation IDs in gameplay comparators | READY |
| StateRegistry sole storage | no second physical state container | READY |
| StateLifecycleSystem sole mutation | no direct state add/remove outside lifecycle owner | READY |
| EventBus facts-only | no subscriber required for Stage9 orchestration/finalization | READY |
| BattleSystems composition root | construction graph + BattleContext anti-service-locator | READY |
| settlement one-shot | same Stage9 request/permit mutates troops/publishes once; replay rejected | **READY** |
| EffectExecutor Stage9 source identity | active/periodic source refs explicit; no reverse enum mapping | **READY** |
| source-skill-slot ingress/immutability | typed domain, LoadedSkill producer, duplicate-slot rejection, reapply mismatch rejection | **READY** |

```text
Architecture tests mapped = 12
READY                     = 12
BLOCKED                   = 0
```

### 25.3 Required source-type producer assertions

```text
active skill DamageEffect
→ EffectSourceRef.stage9_source_type == ACTIVE_SKILL
→ DamageEffect Stage8 classification remains DamageSourceType.SKILL

periodic state damage
→ EffectSourceRef.stage9_source_type == PERIODIC_DAMAGE
→ DamageEffect Stage8 classification remains DamageSourceType.CONTINUOUS
```

Tests must construct these through the actual semantic producers (`SkillResolver`, `TriggerSystem`) and must not pass by reverse enum mapping in `EffectExecutor`.

### 25.4 Required Phase 9.2 finalization compatibility assertions

At minimum, using the actual six current barriers:

```text
initial victory
round-start hook victory
unit-action-start hook victory
action-end victory
round-end victory
max-round ending
```

For each applicable path:

```text
legacy result unchanged
observable event ordering unchanged
BATTLE_END transition exactly once
BATTLE_ENDED event exactly once
VictorySystem not re-evaluated during legacy projection
```

### 25.5 Required settlement one-shot assertion

```text
settle Stage9 request + permit once
→ troop loss once
→ DAMAGE_DEALT once

settle same request/permit again
→ domain/programmer error
→ no second troop mutation
→ no second event
```

---

## 26. Source File Plan — Recomputed After Round2 Repair

All production paths are under flat `sgs_v2/battle_core/`.

### 26.1 Planned NEW production files — 16

| File | Responsibility |
|---|---|
| `operation_identity.py` | typed IDs, allocator, SourceType, lineage |
| `stage9_trace.py` | bounded production/full-test observation sink |
| `stage9_integerization.py` | canonical `ExactRatio` + exact FLOOR/HALF_UP helpers |
| `stage9_state_params.py` | mechanism typed runtime params |
| `stage9_state_runtime.py` | typed StateRegistry adapter + ordering validation |
| `target_resolution_system.py` | selector + Guard single-pass immutable result |
| `reaction_permission_policy.py` | centralized recursion/callback permissions |
| `execution_right_system.py` | FutureAdmissionGate + FutureAdmissionPermit + operation barriers + DamageCallbackAdmissionPoint |
| `damage_instance_coordinator.py` | standard Stage8 damage orchestration/fact boundary + settlement permit issuance |
| `damage_partition_system.py` | exactly-one partition + Share/Distribution plans |
| `direct_troop_loss_system.py` | attributed direct-loss settlement |
| `cleave_derived_damage_system.py` | Cleave-specific derived calculation/settlement seam |
| `cleave_system.py` | source-bound effects/secondary plans/admission |
| `chain_system.py` | monotonic traversal/deferred/restricted feedback |
| `counter_system.py` | CounterBatch/entries/live gates/zero terminal |
| `battle_finalization_coordinator.py` | LegacyFinalizationBarrier + FinalizationResult + FinalizationProjectionPermit + termination ownership |

```text
Planned NEW = 16
```

No extra file is created just for a small provenance/permit dataclass:

```text
EffectSourceRef             -> effects.py
SkillSlot/LoadedSkillRef    -> skill_runtime.py
FutureAdmissionPermit       -> execution_right_system.py
DamageSettlementPermit      -> damage settlement/coordinator ownership; no standalone module
FinalizationProjectionPermit-> battle_finalization_coordinator.py
```

### 26.2 Planned MODIFY production files — 17

| File | Planned change | Constraint |
|---|---|---|
| `context.py` | OperationIdAllocator + small termination record | no services/queues/policies/trace/mechanism state |
| `battle_systems.py` | compose/inject Stage9 systems | composition root only |
| `engine.py` | six legacy barrier adapters + next-Action admission + permit-backed final projection | no mechanism algorithms/termination decision |
| `action_system.py` | ActionId, ActionStart maintenance/grant | no direct registry mutation |
| `normal_attack_system.py` | thin master orchestration | no local mechanism algorithms/finalization writes |
| `damage_resolution_system.py` | typed request/result, `settle()`, one-shot permit validation/consume | `DamageResult.final_damage` untouched |
| `effect_executor.py` | consume EffectSourceRef; route DamageEffect through completed DamageInstance path | never infer SourceType from DamageSourceType |
| `effect_result.py` | narrow stable Stage9 DamageEffect result | no coordinator internals exposed |
| `skill_runtime.py` | `SkillSlot`, `LoadedSkillRef/Set`, optional runtime slot, production loading API | slot belongs to holder runtime |
| `skill_resolver.py` | build authoritative ACTIVE_SKILL EffectSourceRef | no slot/source inference |
| `effects.py` | own `EffectSourceRef`; Effects use canonical source ref | `DamageRequest` Stage8 shape unchanged |
| `state_instance.py` | store `source_skill_slot: SkillSlot | None` | durable provenance only |
| `state_lifecycle_system.py` | accept/store/publish supplied source slot; reapply provenance guard at adapter seam | generic lifecycle does not guess slot |
| `official_state_catalog.py` | bind Stage9 typed runtime params where required | IDs/text unchanged |
| `events.py` | Stage9 observation facts where needed | EventBus never controls flow |
| `trigger_system.py` | **periodic EffectSourceRef producer** | Stage7 trigger timing/selection semantics unchanged |
| `__init__.py` | intentional public exports only | minimize surface |

```text
Planned MODIFY = 17
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
rule_hook_system.py        # explicit Trigger -> EffectExecutor route; not an Effect producer
unit.py                    # no skill-loadout ownership introduced here
```

`rule_hook_system.py` was explicitly rechecked and remains KEEP because it constructs no `DamageEffect`/`ApplyStateEffect` and does not own source provenance.

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

### 26.5 `DamageEffectResult` compatibility

Upgrade existing `DamageEffectResult`, do not expose coordinator internals:

```python
DamageEffectResult(
    effect: DamageEffect,
    damage_instance_id: DamageInstanceId,
    settlement_result: DamageResolutionResult,
)
```

A read-only `resolution -> settlement_result` compatibility property may preserve old callers/tests.

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

This design repair creates none of them.

---

## 27. Existing System Impact Matrix

| Existing component | KEEP / MODIFY | Integration contract |
|---|---|---|
| BattleEngine | MODIFY | six legacy barriers; future Action gate; permit-backed projection |
| BattleContext | MODIFY | ID allocator + small termination record only |
| BattleSystems | MODIFY | single composition root |
| ActionSystem | MODIFY | Action scope/maintenance |
| NormalAttackSystem | MODIFY | unique thin NormalAttack master |
| TargetSystem | KEEP | candidate/RNG primitives only |
| DamageSystem | KEEP | frozen Stage8 theoretical owner |
| DamageResolutionSystem | MODIFY | typed backward-compatible settlement + one-shot Stage9 permit |
| TroopSystem | KEEP | sole troop mutation writer |
| VictorySystem | KEEP / CALL | pure evaluator already correct |
| EventBus | KEEP semantics | observation only |
| StateRegistry | KEEP | one store |
| StateLifecycleSystem | MODIFY provenance only | one physical writer |
| SkillRuntime/Resolver/Effects | MODIFY provenance | authoritative source/slot chain |
| TriggerSystem | MODIFY provenance only | periodic source identity producer |
| RuleHookSystem / Recovery | KEEP | no semantic redesign |
| EffectExecutor/effect_result | MODIFY | standard DamageEffect uses narrow Stage9 path/result |
| RandomSystem | KEEP | sole RNG |
| AttributeSystem | KEEP | live combat stats |

---

## 28. Implementation Phases — Round2 Revalidated

### 28.0 Universal phase green gate

Every phase independently satisfies:

```text
all existing tests green
new phase tests green
no production call points to placeholder/stub/TODO Stage9 service
no production path depends on a later-phase semantic owner
Stage8 frozen semantics still green
```

Temporary production stub coordinators/scopes are forbidden.

### Phase 9.1 — Identity / Provenance / Exact Numeric / Capability Types

**Prerequisites:** Stage8 frozen; Round3 later verifies this design before implementation.  
**New production switch:** none.  
**Creates/types:** operation identities, `SourceType`, `OperationLineage`, `SkillSlot`, `EffectSourceRef`, canonical `ExactRatio`, integerization helpers, Stage9 state params, typed permit primitives/interfaces (`FutureAdmissionPermit`, settlement/finalization permit contracts) without destructive production rerouting.  
**Compatibility bridge:** existing Stage1-8 runtime remains untouched; legacy `SkillRuntime` fixtures may carry `skill_slot=None`.  
**Required tests:** ID/lineage validation, SkillSlot legal domain, ExactRatio canonical vectors, REG-INT-01..05, EffectSourceRef validation.  
**Exit gate:**

```text
SkillSlot domain frozen
ExactRatio canonicalization frozen
no generic from_float
EffectSourceRef frozen
SourceType producer matrix complete
settlement/finalization/future-admission permit primitives typed
```

**Independent green:** YES.  
**Forbidden:** production damage/finalization reroute.

### Phase 9.2 — Execution Right + Legacy Finalization Transition

**Prerequisites:** Phase 9.1 types.  
**New production switch:** `BattleFinalizationCoordinator` becomes the sole semantic finalization owner at the six mapped legacy barriers; `FutureAdmissionGate` becomes the next-Action admission owner through a permit-consuming `LegacyActionDispatchAdapter`. No Stage9 operation scopes are required.  
**Compatibility bridge:** six `LegacyFinalizationBarrier` adapters preserve the exact current evaluation points; action-path projection remains after `UNIT_ACTION_ENDED`; Engine consumes `FinalizationProjectionPermit` and builds fresh legacy `BattleResult`.  
**Admitted Stage9 operation set:** empty.  
**Required tests:** existing engine/victory tests plus all six legacy barriers, deep immutable snapshot, claim/consume one-shot, `BATTLE_ENDED` exactly once, next-Action gate permit reuse rejection.  
**Exit gate:**

```text
Legacy finalization barrier map = 6/6
current Engine terminal checkpoints migrated 1:1
Coordinator semantic owner active
legacy outcomes/events unchanged
FinalizationResult deep immutable
projection permit exactly once
no fake Action/Damage/Reaction scope
```

**Independent green:** **YES**.  
**Forbidden:** mechanism-local drain inventions.

### Phase 9.3 — Target Arbitration + Holder-Specific Source/Slot Ingress

**Prerequisites:** 9.2 real finalization/execution-right infrastructure.  
**New production switch:** holder-equipped Stage9 skill registration uses `LoadedSkillRef/LoadedSkillSet -> SkillRuntime.from_loaded`; `SkillResolver` and state apply paths create/propagate `EffectSourceRef`.  
**Compatibility bridge:** direct legacy/test `SkillRuntime(..., skill_slot=None)` remains usable where no P0 slot-order rule is entered; generic lifecycle keeps old mutation ownership.  
**Tasks:** typed slot producer, duplicate-slot rejection, effect propagation, `StateInstance.source_skill_slot`, same-source refresh mismatch guard, Confusion/Taunt/default selector, Guard once, immutable target result.  
**Required tests:** REG-TGT-01..04 + slot domain/duplicate/reapply/source-ref propagation tests.  
**Exit gate:**

```text
concrete holder-specific skill slot ingress exists
no slot inference from skill_id
ApplyState source provenance immutable
periodic source metadata is available on StateInstance
TargetResolution immutable/single-pass
INV-18 structurally closed
```

**Independent green:** YES.  
**Forbidden:** production DamageEffect cutover to incomplete DamageInstance path.

### Phase 9.4 — Settlement Seam + Isolated DamageInstance Core

**Prerequisites:** 9.3 source/provenance types and real 9.2 finalization infrastructure.  
**New production switch:** none from `EffectExecutor`; DamageInstance coordinator is fixture-callable only.  
**Compatibility bridge:** legacy `DamageResolutionSystem.resolve/apply_result` remain full-settlement `LEGACY_COMPAT` paths with historical call semantics.  
**Tasks:** Model A result, typed request, `DAMAGE_DEALT.requested_damage=Dtarget`, explicit death/credit facts, exactly-one `DamageSettlementPermit`, identity match, atomic consume before troop write.  
**Required tests:** legacy compatibility + `Dtotal != Dtarget != actual` + one-shot replay rejection + finalization observation fixture.  
**Exit gate:**

```text
isolated DamageInstance fixture works end-to-end
typed settlement works
settlement one-shot works
Dtotal/Dtarget/ActualLoss remain distinct
legacy resolve semantics unchanged
```

**Independent green:** YES.  
**Forbidden:** Stage8 calculation semantic change; EffectExecutor production reroute.

### Phase 9.5 — Partition + DirectTroopLoss + Authoritative Production DamageEffect Cutover

**Prerequisites:** 9.4 isolated one-shot settlement; 9.3 source refs; real 9.2 finalization.  
**New production switch:** only at phase end, `EffectExecutor -> DamageInstanceCoordinator` for production `DamageEffect`.  
**Compatibility bridge:** narrow `DamageEffectResult` compatibility projection; legacy direct APIs remain available to historical callers not routed through Stage9.  
**Tasks:** Share/Distribution plans, direct loss, finalization/barrier notifications, active/periodic SourceType wiring, `TriggerSystem` periodic producer update, EffectExecutor source-ref consumption.  
**Required tests:** REG-SHR-01..04, REG-DST-01..04, EffectExecutor compatibility, active/periodic producer assertions, unclassified-source scan.  
**Cutover gate before reroute:**

```text
production DamageEffect source identity coverage = 100%
unclassified production DamageEffect = 0
no reverse inference from DamageSourceType
TriggerSystem periodic SourceType ingress = real
all attribution preserved
partition/direct loss = real
finalization/execution right = real
settlement one-shot = real
```

**Exit gate:** production DamageEffect cannot bypass provenance/partition/finalization/one-shot settlement seams.  
**Independent green:** **YES**.  
**Forbidden:** source provenance invention inside EffectExecutor.

### Phase 9.6 — NormalAttack Master + Combo / Assault Admission

**Prerequisites:** complete 9.5 production damage route.  
**New production switch:** existing `NormalAttackSystem` becomes the thin Stage9 lifecycle master; real `ActionScope` replaces Phase 9.2 legacy action dispatch adapter.  
**Compatibility bridge:** same NormalAttack events/order and same Stage8 damage semantics; Phase 9.2 `NEXT_ACTION` permit contract is retained, only consumer becomes real ActionScope factory.  
**Tasks:** ActionId/NA IDs, fresh #2 target pass, Combo grant/checkpoint, Assault admission, permit-required Combo #2/Assault/Action branch factories.  
**Required tests:** REG-TGT-05..07, REG-CMB-01..05, existing normal-attack tests, FutureAdmission no-bypass for Action/Assault/Combo.  
**Exit gate:** one Action <=2 attacks; no recursive checkpoint; future branches gate before identity allocation.  
**Independent green:** YES.  
**Forbidden:** embed Cleave/Chain/Counter algorithms.

### Phase 9.7 — Cleave + Chain + Counter

**Prerequisites:** 9.6 real NA/Action scopes + all prior provenance/settlement/finalization seams.  
**New production switch:** real Cleave/Chain/Counter services and their future-branch factories.  
**Compatibility bridge:** no global re-gating of already-admitted local work; all mechanism P0 drain/cancel behavior remains local.  
**Tasks:** actual-loss Cleave basis, effect-major sequencing, monotonic Chain cursor, Counter batch/zero terminal, permit-required next-Cleave/new-Chain/new-CounterBatch creation, shared DamageCallbackAdmissionPoint.  
**Required tests:** REG-CLV-01..05, REG-CHN-01..04, REG-CTR-01..05, no-bypass tests for all three branch families.  
**Exit gate:** all future-admission branch families are structurally permit-gated; local admitted work never re-gates globally.  
**Independent green:** YES.

### Phase 9.8 — Full Integration / 45 Regressions / Architecture Closure

**Prerequisites:** 9.7 all mechanism services real.  
**New production switch:** none; integration/verification only.  
**Compatibility bridge:** all Stage1-8 tests remain green; no Stage8 semantic or event-contract reopen.  
**Tasks:** FINAL_01..06, golden trace, all 12 architecture tests, all existing tests, CI/demo compatibility.  
**Exit gate:**

```text
42/42 invariants enforced
45/45 gameplay regressions green
12/12 architecture tests green
unclassified DamageEffect = 0
dependency cycles = 0
forward production dependencies = 0
Stage8 reopen = 0
```

**Independent green:** YES.  
**Forbidden:** new gameplay research/semantic expansion.

### 28.1 PHASE_DEPENDENCY_GRAPH

```text
9.1 identity / provenance / exact numeric / capability types
  ↓
9.2 execution-right + six-barrier legacy finalization transition
  ↓
9.3 target arbitration + holder source-slot/state provenance ingress
  ↓
9.4 typed one-shot settlement + isolated DamageInstance core
  ↓
9.5 partition + direct loss + authoritative EffectExecutor cutover
  ↓
9.6 NormalAttack master + Action/Combo/Assault permit integration
  ↓
9.7 Cleave + Chain + Counter + remaining permit-required branch factories
  ↓
9.8 full integration / 42 invariants / 45 regressions / 12 architecture tests
```

```text
Dependency cycles               = 0
Forward production dependencies = 0
Phase 9.2 independent failure   = 0
Phase 9.5 independent failure   = 0
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

Neither `LegacyFinalizationBarrier`, `FinalizationResult`, nor any permit contains a `DSTS9-B02` or commander-Distribution special case.

### 29.2 Counter fidelity

```text
exact official universal comparator fidelity = DEFERRED_NON_BLOCKING
universal dispel fidelity                    = DEFERRED_NON_BLOCKING
```

Project fallback ordering remains deterministic and clearly non-official.

---

## 30. Dependency / Boundary Acceptance Gate

### 30.1 Authoritative call/dependency edges

Arrows mean consumer calls/depends on provider:

```text
BattleEngine → BattleFinalizationCoordinator
BattleEngine → FutureAdmissionGate (NEXT_ACTION only)
BattleEngine → ActionSystem
BattleFinalizationCoordinator → VictorySystem
BattleFinalizationCoordinator → BattleTerminationRecord

ActionSystem → Stage9StateRuntime
ActionSystem → NormalAttackSystem

SkillResolver → EffectSourceRef
TriggerSystem → EffectSourceRef
RuleHookSystem → TriggerSystem
RuleHookSystem → EffectExecutor

NormalAttackSystem → TargetResolutionSystem
NormalAttackSystem → DamageInstanceCoordinator
NormalAttackSystem → CleaveSystem
NormalAttackSystem → CounterSystem
NormalAttackSystem → FutureAdmissionGate (assigned Assault/CounterBatch/Combo edges)

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
CleaveDerivedDamageResolver → DamageCallbackAdmissionPoint

DamageCallbackAdmissionPoint → FutureAdmissionGate
ChainSystem ← consumed FutureAdmissionPermit from DamageCallbackAdmissionPoint
ChainSystem → restricted Chain settlement primitive

BattleSystems → constructs/injects every service above
```

Forbidden reverse/shortcut edges:

```text
BattleFinalizationCoordinator -X-> BattleEngine
LegacyFinalizationBarrier     -X-> set context.ended / publish BATTLE_ENDED
EffectExecutor                -X-> infer SourceType from DamageSourceType
StateRegistry                 -X-> infer source_skill_slot
local mechanism system        -X-> NormalAttackSystem to advance lifecycle
DamageInstanceCoordinator     -X-> EffectExecutor
ChainSystem                   -X-> self-admit a new traversal
future branch factory         -X-> construct without FutureAdmissionPermit
EventBus subscriber           -X-> become Stage9 orchestration owner
```

This edge set has no required static dependency cycle.

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
battle-long consumed permit-ID sets
```

### 30.3 Round2 findings closure

| Finding | Closure |
|---|---|
| R2-B01 | six-entry `LEGACY_FINALIZATION_BARRIER_MATRIX`; Phase 9.2 bridge; action projection ordering; no stub operation scopes |
| R2-B02 | `EffectSourceRef`; `SkillResolver=ACTIVE_SKILL`; `TriggerSystem=PERIODIC_DAMAGE`; no reverse inference; 100% cutover gate |
| R2-M01 | typed 0-based `SkillSlot`; `LoadedSkillRef/Set`; duplicate-slot rejection; reapply slot immutability; required-slot error |
| R2-M02 | `FutureAdmissionPermit`; permit-required branch construction; caller matrix; no-bypass architecture test |
| R2-M03 | deep-immutable `FinalizationResult`; one-shot projection claim/consume; fresh legacy `BattleResult` projection |
| R2-M04 | one-shot `DamageSettlementPermit`; atomic consume before troop mutation; legacy API preserved |
| R2-N01 | reduced/sign-normalized/positive-denominator ratio; zero `0/1`; no generic float constructor |
| R2-N02 | shared `EffectSourceRef`; explicit distinction from runtime `OperationLineage` |

### 30.4 Round2 repair final gate

```text
BLOCKER remaining               = 0
MAJOR remaining                 = 0
MINOR remaining                 = 0
DOC_ONLY remaining              = 0

P0 semantic conflict            = 0
P0 semantic change              = 0
new gameplay rule               = 0
Stage8 semantic reopen          = 0

Unowned runtime facts           = 0
Unspecified reachable paths     = 0
Unenforced invariants           = 0
Untestable mandatory regression = 0

Architecture tests READY        = 12/12
Architecture tests BLOCKED      = 0

mapped legacy barriers          = 6/6
unclassified production DamageEffect = 0 by required Phase 9.5 gate

Dependency cycles               = 0
Forward production dependency   = 0
Phase independently-green failure = 0

planned NEW production files    = 16
planned MODIFY production files = 17
42 invariants                   = 42/42 enforced
45 regressions                  = 45/45 testable/mapped
```

### 30.5 Current document status

```text
STAGE9.md
STATUS: DESIGN FROZEN — FREEZE AUDIT REQUIRED

Stage9 Design Frozen = YES
Stage9 Final Implementation Frozen = NO
Round3 Design Audit = PASS
Design Freeze Admission = ELIGIBLE / CONSUMED
Implementation specification = FROZEN
Implementation Design Ready = YES
Build Prompt Authoring = PENDING FREEZE AUDIT
Production Implementation = NOT STARTED
```

Design Freeze does not authorize implementation or Build Prompt creation. It records the status transition of the Round3-approved implementation specification without changing its semantic design body.

Next permitted step:

```text
Stage9 Design Freeze Audit
```

Do not create `STAGE9_BUILD_PROMPT.md` and do not begin production implementation before the separate Freeze Audit verifies this freeze commit.
