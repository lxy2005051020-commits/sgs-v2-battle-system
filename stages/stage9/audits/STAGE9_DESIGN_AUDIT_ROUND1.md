# Stage9 Design Audit Round 1

> Audit type: READ-ONLY IMPLEMENTATION DESIGN AUDIT  
> Audit object: `stages/stage9/STAGE9.md`  
> Baseline battle `main`: `90577778c9789632765a8be2ffea0d03e76d288e`  
> Baseline state-authority `main`: `15ed915435f328a6ecd8f488d98b5b9e13c913b5`  
> `STAGE9.md` baseline blob: `f8ee7850697dc87827d88af88a1aa4d6322de13a`  
> Status remains: `DRAFT — DESIGN AUDIT REQUIRED`; `Stage9 FROZEN = NO`; `Ready for implementation = NO`

## 1. Repository Baseline

Both remote `main` branches were re-read before the audit and again immediately before report commit.

| Repository | Baseline SHA | Baseline head |
|---|---|---|
| `lxy2005051020-commits/sgs-v2-battle-system` | `90577778c9789632765a8be2ffea0d03e76d288e` | `design(stage9): author implementation specification` |
| `lxy2005051020-commits/sgs-state-mechanics-research` | `15ed915435f328a6ecd8f488d98b5b9e13c913b5` | `docs(combo): close stale CBS9-B03 status banner` |

No baseline drift occurred during the read-only audit. The audited `STAGE9.md` blob is `f8ee7850697dc87827d88af88a1aa4d6322de13a`.

## 2. Audit Scope

This round audited implementation feasibility, ownership, existing-code compatibility, dependency direction, Stage8 seam safety, identity/provenance completeness, control-flow executability, incremental buildability, testability, and P0 fidelity.

This round did **not** re-open gameplay research, modify P0, modify `STAGE9.md`, modify production code/tests/Stage8, modify the state authority repository, freeze Stage9, or implement any repair.

Primary reality checks were made against current production code, especially:

- `BattleEngine`, `BattleContext`, `BattleSystems`
- `ActionSystem`, `NormalAttackSystem`, `TargetSystem`
- `DamageSystem`, `DamageResolutionSystem`, `TroopSystem`
- `VictorySystem`, `EventBus`, `RandomSystem`
- `StateRegistry`, `StateLifecycleSystem`, `StateInstance`
- `TriggerSystem`, `RuleHookSystem`, `RecoverySystem`, `EffectExecutor`
- `SkillRuntime`, `SkillResolver`, `SkillDefinition`, `effects.py`, `effect_result.py`

Existing tests for normal attack, damage resolution, EffectExecutor, Stage7 engine hooks, State runtime, Trigger/Recovery, BattleSystems, and all Stage8 damage-pipeline suites were also checked.

## 3. Authority Fidelity

### AUTHORITY_FIDELITY_MATRIX

| Design concern | Classification | Audit result |
|---|---|---|
| Confusion/Taunt/default target selector precedence | P0-DERIVED | Matches current P0 |
| Guard after intended target, single pass | P0-DERIVED | Matches current P0 |
| Combo #2 fresh NormalAttack + target resolution | P0-DERIVED | Matches current P0 |
| Counter admission snapshot vs execution liveness | P0-DERIVED | Matches current P0 |
| Share > Distribution precedence | P0-DERIVED | Matches current P0 |
| Share target-first lethal interrupt | P0-DERIVED | Matches current P0 |
| Distribution fixed `N` / fixed plan | P0-DERIVED | Matches current P0 |
| Cleave `ActualTargetTroopLoss` basis | P0-DERIVED | Matches current P0 |
| Cleave current-effect drain vs next effect admission | P0-DERIVED | Matches RF-P04 |
| Chain one-pass live expansion | P0-DERIVED | Matches current P0 if implemented as a monotonic slot cursor |
| Future-branch blocking after victory latch | P0-DERIVED | Matches RF-P03/RF-P04 |
| `SourceType`, typed lineage, operation IDs | RF-C01 REPRESENTATION | Representation only; must not become gameplay authority beyond frozen permissions |
| Deterministic unit comparator fallback | ENGINEERING-ONLY | Allowed only as a labeled deterministic project default where P0 is silent |
| Counter stable source/slot tie-break | ENGINEERING-ONLY | Current Counter P0 explicitly leaves exact universal comparator non-blocking; must not be called official |
| `unit_id` as final tie-break | ENGINEERING-ONLY | Acceptable only as deterministic stability fallback; never evidence of official order |
| Operation IDs used as gameplay tie-break | UNAUTHORIZED SEMANTIC | **Forbidden; none is authorized** |
| New target eligibility, callback eligibility, removal rules | UNAUTHORIZED SEMANTIC | No such semantic expansion found in the authored design |

**P0 semantic conflict count: 0.**  
**Unauthorized semantic found in current STAGE9 design: 0**, provided engineering tie-breakers remain explicitly labeled as project defaults and operation IDs never drive gameplay priority.

## 4. Existing Architecture Reality Check

Key source-level facts:

1. `DamageSystem` is already the Stage8 theoretical pipeline owner and does not mutate troops.
2. `DamageResolutionSystem.apply_result()` currently treats `DamageResult.final_damage` as the amount requested from `TroopSystem` and publishes that same value as `DAMAGE_DEALT.requested_damage`.
3. `TroopSystem` mutates troops but does not publish generic hit/hurt/death callbacks itself.
4. `VictorySystem` is **already a pure evaluator**. It does not finalize the battle.
5. `BattleEngine._finish()` is the current terminal side-effect owner: it writes `context.ended`, writes `context.result`, enters `BATTLE_END`, and publishes `BATTLE_ENDED`.
6. `EffectExecutor` is the standard `DamageEffect` route, but current `DamageEffectResult.resolution` is statically shaped as `DamageResolutionResult`.
7. `RuleHookSystem` routes hook-produced effects through `TriggerSystem -> EffectExecutor`.
8. Current skill/state application provenance contains `source_skill_id` but not `source_skill_slot`.
9. `StateRegistry` remains the sole state container and `StateLifecycleSystem` is the formal mutation path.
10. Existing Stage8 request/config coefficients are `float`, while Stage9 integerization requires exact deterministic decimal/rational semantics.

### EXISTING_CODE_COMPATIBILITY_MATRIX

| Existing component | Current reality | Planned Stage9 use | Verdict |
|---|---|---|---|
| `BattleEngine` | Macro loop + terminal side effects | Macro loop; finalization migrated | **BLOCKER: terminal ownership split not unique** |
| `BattleContext` | Battle facts + current terminal compatibility fields | Add ID allocator + small termination record | ACCEPTABLE with strict anti-service-locator boundary |
| `BattleSystems` | Composition root | Compose/inject Stage9 services | ACCEPTABLE |
| `ActionSystem` | Alive/STUN gate + normal attack dispatch | Action scope + maintenance orchestration | ACCEPTABLE; no direct registry mutation |
| `NormalAttackSystem` | Compact physical attack execution | Master orchestration | ACCEPTABLE only as thin coordinator |
| `DamageResolutionSystem` | `final_damage` drives settlement/event request | Assigned-target settlement seam | **BLOCKER: fact meanings/API are not unique** |
| `EffectExecutor` | `DamageEffect -> DamageResolutionSystem` | `DamageEffect -> DamageInstanceCoordinator` | **MAJOR: result type/file plan incomplete** |
| `effect_result.py` | `DamageEffectResult.resolution: DamageResolutionResult` | Not listed for modification | **MAJOR / missing planned modification** |
| `VictorySystem` | Already pure evaluator | “make pure” + compatibility wrapper | Existing edit is not justified by current source |
| `TroopSystem` | Mutation only, no callbacks | Shared primitive for normal/direct loss | ACCEPTABLE |
| `StateRegistry` / Lifecycle | Sole storage/write path | Keep + typed adapter | ACCEPTABLE |
| `SkillRuntime` / `SkillResolver` / effects | No slot provenance | Must somehow provide `source_skill_slot` | **MAJOR: producer/ingress missing** |
| `EventBus` | Fact bus/history | Observation only | ACCEPTABLE in inspected production paths |
| `RecoverySystem` | Recovery owner | Consume permitted damage facts only | ACCEPTABLE; Stage9 must not duplicate recovery |
| `RandomSystem` | Sole RNG | Remains sole RNG | ACCEPTABLE |

## 5. Responsibility Ownership

### RESPONSIBILITY_OWNERSHIP_MATRIX

| Component | Current responsibility | Planned Stage9 responsibility | Ownership overlap? | Verdict |
|---|---|---|---|---|
| `BattleEngine` | Phase/action loop + terminal projection/publication | Outer loop + macro barriers | Yes, with finalization coordinator unless repaired | BLOCKER |
| `ActionSystem` | Action gate + normal attack dispatch | Action scope, maintenance orchestration, one master dispatch | No if lifecycle mutation remains delegated | PASS |
| `NormalAttackSystem` | Target + physical attack execution | Master NormalAttack orchestration | Risk of growth, but local algorithms delegated | PASS WITH GUARDRAIL |
| `TargetResolutionSystem` | New | Sole target arbitration + single Guard pass | No | PASS |
| `DamageInstanceCoordinator` | New | Standard DamageInstance orchestration and damage-fact boundary | No if it does not own formula/partition algorithms | PASS |
| `DamagePartitionCoordinator` | New | Qualify/select exactly one typed resolver/plan | No | PASS |
| `CleaveSystem` | New | Cleave effects/queue/secondary admission | No | PASS |
| `ChainSystem` | New | Chain traversal/live revalidation/restricted feedback | No | PASS |
| `CounterSystem` | New | CounterBatch admission/entries/local execution gates | No | PASS |
| `FutureAdmissionGate` / `ExecutionRightSystem` | New | Global future-branch admission only | Potentially bypassed because caller edges are underspecified | MAJOR |
| `BattleFinalizationCoordinator` | New | Victory latch/drain/finalization semantic owner | Overlaps current Engine terminal projection | BLOCKER |
| `VictorySystem` | Pure evaluator | Pure evaluator | No | KEEP |
| `EffectExecutor` | Typed effect dispatch | Adapter into Stage9 standard damage route | No mechanism ownership | PASS |

Target condition “multiple final owners for same decision = 0” is **not yet met** because `BattleEngine._finish()` and the new finalization coordinator lack a uniquely specified compatibility split.

## 6. NormalAttack Master Design

**Verdict: ACCEPTABLE WITH ARCHITECTURAL GUARDRAILS; not itself a blocker.**

The current `NormalAttackSystem` already owns physical normal-attack execution. Extending it into the master lifecycle coordinator is feasible if it remains orchestration-only:

- owns the NormalAttack lifecycle sequence;
- requests target resolution;
- delegates standard damage to `DamageInstanceCoordinator`;
- delegates Cleave/Chain/Counter to their own systems;
- requests global future admission from `ExecutionRightSystem`;
- never mutates state storage directly;
- never computes Share/Distribution/Cleave/Chain/Counter algorithms;
- never writes finalization state.

A separate top-level coordinator is not required **if these boundaries hold**. If implementation places target algorithms, partition math, state mutation, reaction queue internals, and finalization inside `NormalAttackSystem`, it becomes a God Object and violates this design verdict.

## 7. Target Resolution

**Verdict: gameplay shape is sound; one minor DTO ambiguity remains.**

`intendedAttackTarget` and `postRedirectActualTarget` are necessary and sufficient for Confusion/Taunt/Guard, Combo #2 freshness, Cleave anchor, and Counter holder.

`selectedTarget` is not given a distinct downstream semantic consumer in the design. Unless it is explicitly defined as diagnostic selector output distinct from the P0 `intendedAttackTarget`, it is redundant and risks an implementer performing an extra default-selection/RNG action merely to populate it.

No additional “selector provenance” field is required by current P0/tests beyond existing redirect/source/reason + trace facts. Do not add one speculatively.

## 8. Damage / Settlement Seam

**Verdict: BLOCKER.**

Current Stage8 settlement reality:

```text
DamageResult.final_damage
    -> DamageResolutionSystem.apply_result()
    -> TroopSystem.apply_damage(requested_damage=final_damage)
    -> DAMAGE_DEALT.requested_damage = final_damage
```

Stage9 requires:

```text
DamageResult.final_damage = Dtotal
partition produces Dtarget
TroopSystem settles Dtarget
actual committed loss = clamp(Dtarget, current troops)
```

The authored “narrow overload accepting assigned target amount while preserving original DamageResult” does not uniquely define:

- the typed carrier of `Dtarget`;
- what `DamageResolutionResult` means after assigned settlement;
- what `DAMAGE_DEALT.requested_damage` means: `Dtotal` or `Dtarget`;
- how consumers obtain `Dtotal`, `Dtarget`, and actual loss without overloading one field;
- how legacy callers preserve their current public behavior;
- how `DamageEffectResult` represents the Stage9 execution result.

A silent wrong-layer read here corrupts Cleave basis, recovery/stat attribution, trace, and death/finalization facts. Stage8 formula semantics do **not** need to reopen, but the settlement boundary must be redesigned before implementation.

### STAGE8_SEAM_MATRIX

| Seam | Frozen Stage8 meaning | Stage9 need | Round1 verdict |
|---|---|---|---|
| `DamageRequest` | Formula request; float coefficient today | Standard theoretical calculation input | KEEP |
| `DamageResult.final_damage` | Final theoretical integer and legacy settlement request | Must remain `Dtotal` | KEEP; never redefine |
| `DamageResult.requested_damage` compat property | Alias of `final_damage` | Cannot become `Dtarget` | KEEP |
| `DamageResolutionSystem.resolve()` | Calculate + settle same amount | Legacy path | Preserve compatibility |
| `DamageResolutionSystem.apply_result()` | Settle `final_damage` | Needs assigned target amount | BLOCKER until typed semantics fixed |
| `DAMAGE_DEALT.requested_damage` | Current requested settlement amount | Must have one unambiguous Stage9 meaning | BLOCKER |
| `DamageResolutionResult` | DamageResult + troop change + defeated | Needs assigned settlement facts | Incomplete |
| Stage8 formulas/modifiers/prevention/hit | Frozen gameplay semantics | No semantic change | NO REOPEN |
| Stage8 tests | Protect calculation and current settlement behavior | Need extra Stage9 compatibility tests around assigned amount | Existing suite is necessary but not sufficient |

**Stage8 reopen findings: 0.** The problem is seam specification, not formula authority.

### DAMAGE_FACT_OWNERSHIP_MATRIX

| Fact | Owner | Producer | Consumer | Verdict |
|---|---|---|---|---|
| `Dtotal` | `DamageInstanceCoordinator` after Stage8 calculation | immutable `DamageResult.final_damage` | partition, derived bases, trace | Clear |
| `Dtarget` | mechanism-specific typed partition plan | Share/Distribution/NONE resolver | assigned-target settlement | **Carrier/settlement contract missing** |
| `ActualTargetTroopLoss` | target settlement result | `TroopSystem` clamp through settlement seam | Cleave, Chain, recovery/stat, death | Clear after seam repair |
| `DamageResult` | `DamageSystem` | Stage8 calculation | coordinator/trace/legacy | Clear; immutable |
| `UnitDeathFact` | concrete settlement/direct-loss edge | target settlement or direct-loss resolver | finalization + trace | Clear conceptually; idempotency must be structural |
| `CreditedDamage` | concrete settlement result | standard settlement/direct-loss attribution | recovery/stat/observation | Must remain distinct from Dtotal/Dtarget |

`DamageResult.final_damage` must never simultaneously mean `Dtotal` to one consumer, `Dtarget` to another, and actual loss to a third.

## 9. Partition / DirectTroopLoss

### Partition abstraction verdict

**PASS.** The common abstraction is appropriately narrow **as authored**: qualification -> select exactly one of `SHARE / DISTRIBUTION / NONE` -> return a typed mechanism-specific plan. Share and Distribution should retain distinct execution logic. A generic `execute_partition(plan)` full of mechanism switches would be a regression from this design.

Partition selection authority is present: current P0 freezes `DamageShare > Distribution`; Stage9 does not invent a new priority.

### DirectTroopLoss verdict

**PASS.** Current `TroopSystem` has no generic hit/hurt callback publication. Therefore `DirectTroopLossResolver -> TroopSystem` can safely bypass HitResolution/FirstAid/Counter/Chain/Share/Distribution, provided the resolver itself owns:

- theoretical vs actual loss;
- physical attacker / skill / victim / credit provenance;
- alive->dead edge detection;
- `UnitDeathFact`;
- notification to the finalization service through the repaired owner boundary.

No second troop mutation writer is justified.

## 10. Cleave / Chain

### Cleave

Gameplay architecture matches P0: `ActualTargetTroopLoss` basis, effect-major sequencing, JIT secondary liveness, current admitted `CleaveEffect` drains while a later independent effect remains a future branch.

`DerivedDamageSystem<CLEAVE>` is a **MINOR speculative abstraction**. Chain TRUE_FEEDBACK explicitly uses a different restricted path, and no second derived-damage family currently consumes the generic. Prefer a Cleave-specific derived boundary or keep the generic so narrow that it cannot acquire cross-mechanism permission semantics.

### Chain

The live-expansion design is executable **only if “passed” is operationally defined as a monotonic slot cursor having advanced beyond that battle slot**. A repeated “scan unvisited identities until stable” implementation would be wrong because a newly changed already-passed slot must not re-enter.

Recommended implementation interpretation inside the frozen design:

```text
fixed global slot order
cursor advances monotonically
at each not-yet-passed slot: live-read current eligibility
eligible -> execute once
ineligible -> pass once
never rewind cursor
```

This is architecture clarification, not new gameplay semantics.

## 11. Counter

**Verdict: core Counter architecture is sound; source-slot provenance is a MAJOR integration gap.**

The three required layers are correctly separated:

1. trigger-time eligible-state snapshot;
2. immutable batch-entry admission;
3. execution-time owner-liveness / dead-target local terminal.

The dead-target zero-loss terminal is explicitly modelable without fabricating a Stage8 `DamageResult`: it should return a typed Counter terminal result with Counter execution identity + attributed zero troop loss.

The unresolved issue is ordering metadata. Current state/skill application paths cannot supply the planned apply-time `source_skill_slot`. Until that ingress is specified, multi-source Cleave and Counter comparator data cannot be built without guessing.

## 12. Execution Right / Finalization

### Execution Right

The conceptual separation is correct:

```text
global FutureAdmissionGate != local execution-time liveness gate
```

Dead Counter owner, dead planned Cleave secondary, and invalid Distribution participant are local gates, not global finalization decisions.

However, the design lists the future branches without assigning every concrete caller edge. A “central gate” is not centralized merely because the class name contains the word centralized.

Expected unique caller ownership must be frozen for:

| Future branch | Expected caller/owner |
|---|---|
| next Action | `BattleEngine` macro loop via `ExecutionRightSystem` |
| Assault | NormalAttack lifecycle branch dispatcher |
| Combo #2 | NormalAttack Combo checkpoint |
| new CounterBatch | Counter trigger/admission window |
| new ChainTraversal | Chain admission/dispatcher |
| next independent CleaveEffect | Cleave effect queue/lifecycle owner |

The current spec does not make these call edges sufficiently executable, so this is a **MAJOR** finding.

### Finalization / Victory compatibility verdict

**BLOCKER.**

`VictorySystem` is already pure. The compatibility problem is not making it pure; it is moving terminal ownership out of `BattleEngine._finish()` without creating two final owners.

Required compatibility plan must uniquely state:

| Concern | Required repaired contract |
|---|---|
| Existing victory rule behavior | Preserve `VictorySystem.check()` / max-round semantics |
| New evaluator API | May alias/rename, but no semantic change required |
| Legacy evaluator API | Keep current callers/tests working during migration |
| Termination record | Only `BattleFinalizationCoordinator` mutates latch/drain/finalized semantic state |
| `context.ended` / `context.result` | Assign exactly one compatibility projection owner |
| `BATTLE_END` phase | Assign exactly one transition owner |
| `BATTLE_ENDED` | Publish exactly once, with existing ordering guarantees |
| Engine relation | Engine calls/consumes coordinator; coordinator must not call back into Engine |
| Stage7 compatibility | Lethal round/action hook ordering remains intact |

Until the projection/publication split is explicit, “one finalization owner” is not actually true.

## 13. State Runtime Integration

### STATE_RUNTIME_FIT_MATRIX

| Need | Current runtime fit | Required Stage9 shape | Verdict |
|---|---|---|---|
| Combo physical state | StateRegistry supports it | typed adapter view | FIT |
| Combo remove/suppress/grant distinction | lifecycle + Action-local grant can model it | no second registry | FIT |
| Cleave multi-source instances | registry instances are source-bound | typed params + deterministic query | FIT |
| Counter source entries | source-bound state instance can carry params | typed params | FIT |
| duration/expiry/remove | Lifecycle owns it | reuse | FIT |
| ActionStart maintenance | existing lifecycle has phase maintenance APIs | Action orchestrates, Lifecycle mutates | FIT |
| `source_skill_id` | already present | reuse | FIT |
| `source_skill_slot` storage | can live in typed runtime params | safe extension | FIT |
| `source_skill_slot` producer | absent from Unit/SkillRuntime/SkillResolver/effects/lifecycle ingress | must be defined | **MAJOR** |
| external/temp source without slot | not defined | explicit sentinel/optional policy required | **MAJOR part of same finding** |
| slot fallback comparator authority | not uniquely defined in implementation spec | must be labeled engineering default where P0 is silent | **MAJOR part of same finding** |
| lookup performance | registry scan is linear | Stage9 query adapter/index may cache views, but registry stays sole storage | ACCEPTABLE |

`ActionSystem` must orchestrate ActionStart maintenance but must not mutate `StateRegistry` directly.

## 14. EventBus / Trigger / Recovery Integration

In inspected production paths, EventBus is a fact/observation bus; no authoritative gameplay decision was found to be owned by an EventBus subscriber. `RuleHookSystem` explicitly executes `TriggerSystem -> EffectExecutor`, not “publish and hope a subscriber advances combat”.

Verdict:

- EventBus remains observation-only for Stage9;
- Trigger semantics remain in `TriggerSystem`;
- Recovery remains in `RecoverySystem`;
- Stage9 permission policy controls whether an eligible damage fact reaches recovery/callback semantics, not how Recovery calculates;
- no mechanism should use EventBus as an anonymous orchestration master.

A future architecture test should reject authoritative Stage9 side effects hidden in event subscribers.

## 15. Operation Identity / Provenance

### OPERATION_ID_MATRIX

| ID | Runtime identity need | Trace/test need | Verdict |
|---|---|---|---|
| `ActionId` | Action grant/checkpoint scope | yes | NECESSARY |
| `NormalAttackInstanceId` | #1/#2 lifecycle distinction | yes | NECESSARY |
| `TargetResolutionId` | no independent gameplay lifecycle | trace only | MINOR / OVER-DESIGNED supporting ID |
| `DamageInstanceId` | parentage/partition/callback scope | yes | NECESSARY |
| `ReactionBatchId` | reaction admission batch scope | yes | NECESSARY |
| `CounterBatchEntryId` | stable admitted sibling identity | yes | NECESSARY |
| `PartitionTransactionId` | local transaction/drain boundary | yes | NECESSARY |
| `CleaveEffectId` | current-effect admission/finalization grain | yes | NECESSARY |
| `ChainTraversalId` | one-pass traversal boundary | yes | NECESSARY |
| `DirectTroopLossId` | multiple attributed loss entries | yes | NECESSARY |

**Missing required operation IDs: 0.**  
**Over-designed/supporting IDs: 1 (`TargetResolutionId`).**

One deterministic monotonic allocator per `BattleContext` is compatible with current battle lifecycle. IDs are diagnostic/runtime identity only:

```text
ID values participate in gameplay ordering = NO
```

Battle restart via a new context naturally resets the allocator. If battle serialization/replay is later introduced, allocator state would need serialization, but that is not a Stage9 gameplay requirement.

### SourceType vs DamageSourceType

| Concern | `SourceType` | `DamageSourceType` |
|---|---|---|
| gameplay damage formula | NO | YES |
| Stage8 request | NO | YES |
| recursion/callback policy | YES | NO |
| provenance/lineage | YES | limited existing source category |
| derived/direct path | YES | should not be forced into a fake Stage8 source |
| standard boundary mapping | one-way orchestration mapping | formula input |

The split is acceptable if mapping is narrow and one-way:

```text
NORMAL_ATTACK -> DamageSourceType.NORMAL_ATTACK
ACTIVE_SKILL -> SKILL
PERIODIC_DAMAGE -> CONTINUOUS
COUNTER -> COUNTER
```

Do not invent an Assault mapping until Assault runtime exists. Do not let `SourceType` and `DamageSourceType` become two competing formula truths.

### OperationLineage completeness

The planned lineage is sufficient when combined with local operation IDs:

- Cleave: Action -> NormalAttack -> parent DamageInstance -> CleaveEffect/derived settlement.
- Chain: parent DamageInstance -> ChainTraversal -> next-node attributed feedback.
- Counter: NormalAttack -> ReactionBatch -> CounterBatchEntry -> Counter DamageInstance.
- Direct loss: DamageInstance -> PartitionTransaction -> DirectTroopLoss.

No call-stack inspection or skill-name lookup should be required.

## 16. Integerization

**Verdict: MAJOR design incompleteness.**

The helper rules are semantically correct:

- `floor_damage`
- `round_half_up_damage`
- no Python built-in `round()`
- deterministic decimal/rational semantics

But current production config/request coefficients are `float`. The spec does not freeze the conversion boundary:

```text
float -> Decimal?
float -> Fraction?
Decimal(str(value))?
exact integer ratio / basis points?
```

This matters because a binary float such as an intended decimal ratio can fall microscopically below a boundary before FLOOR or HALF_UP.

Stage9 must define exact accepted numeric representation at the Stage9 ratio/config boundary without reopening Stage8 formula semantics. Integerization research cannot be allowed to lose to IEEE-754 at the final plumbing layer.

## 17. Invariant Enforcement

All 42 invariant IDs were independently checked for enforceability, not merely mention count.

### INVARIANT_ENFORCEMENT_MATRIX

| INV | Primary enforcement | Round1 assessment |
|---|---|---|
| 01 | TYPE-ENFORCED | immutable target fields |
| 02 | STRUCTURAL | selector pipeline before Guard |
| 03 | RUNTIME ASSERTION | one Guard pass / NA |
| 04 | TYPE-ENFORCED | downstream actual-target contracts |
| 05 | TYPE-ENFORCED | recipient belongs to concrete settlement |
| 06 | STRUCTURAL | fresh #2 instance/resolution |
| 07 | TYPE-ENFORCED | physical/operational/grant types separated |
| 08 | STRUCTURAL | ActionStart maintenance sequencing |
| 09 | RUNTIME ASSERTION | remove vs suppress grant transition |
| 10 | RUNTIME ASSERTION | checkpoint ceiling |
| 11 | RUNTIME ASSERTION | atomic consume/cfg230 ceiling |
| 12 | RUNTIME ASSERTION | <=2 physical NormalAttacks |
| 13 | TYPE-ENFORCED | Cleave source/identity |
| 14 | STRUCTURAL | actual committed loss is Cleave input |
| 15 | RUNTIME ASSERTION | FLOOR helper/vector; numeric representation still MAJOR |
| 16 | STRUCTURAL | derived route bypasses upstream formula |
| 17 | TYPE-ENFORCED | centralized permission policy |
| 18 | **UNENFORCED** | `source_skill_slot` ingress/ordering data not defined |
| 19 | TYPE-ENFORCED | direct loss distinct from DamageEvent |
| 20 | STRUCTURAL | direct-loss route bypasses HitResolution |
| 21 | TYPE-ENFORCED | explicit provenance DTO |
| 22 | RUNTIME ASSERTION | exactly-one partition resolver |
| 23 | STRUCTURAL | lifecycle replacement semantics |
| 24 | STRUCTURAL | Share target-first executor |
| 25 | STRUCTURAL | lethal target local interrupt |
| 26 | TYPE-ENFORCED | theoretical vs actual fields |
| 27 | TYPE-ENFORCED | frozen ordered participants/N |
| 28 | TYPE-ENFORCED | frozen planned amounts |
| 29 | STRUCTURAL | fixed plan + skip-only loop |
| 30 | STRUCTURAL | no participant append after admission |
| 31 | STRUCTURAL | labeled Distribution local policy |
| 32 | TYPE-ENFORCED | immutable deferred trigger facts only |
| 33 | STRUCTURAL | execution-time state adapter reads |
| 34 | RUNTIME ASSERTION | monotonic cursor / once-per-slot |
| 35 | STRUCTURAL | restricted Chain settlement route |
| 36 | TYPE-ENFORCED | immutable CounterBatch entries |
| 37 | STRUCTURAL | admission gate separate from owner-liveness gate |
| 38 | TYPE-ENFORCED | explicit zero terminal result/bypass |
| 39 | TYPE-ENFORCED | termination state machine types |
| 40 | **UNENFORCED** | complete FutureAdmissionGate caller coverage not assigned |
| 41 | **UNENFORCED** | coordinator vs Engine final projection ownership ambiguous |
| 42 | STRUCTURAL | typed lineage + centralized permission route; architecture tests still required |

Recomputed totals:

```text
STRUCTURAL        = 16
TYPE-ENFORCED     = 15
RUNTIME ASSERTION = 8
TEST-ONLY         = 0
UNENFORCED        = 3
TOTAL             = 42
```

`UNENFORCED != 0`, therefore the Round1 PASS gate cannot be satisfied.

## 18. Regression Testability

The 45 mandatory regressions were independently checked for fixture constructability, required hook/seam, and observable output. The planned Stage9 trace seam is sufficient to observe admission vs execution gates, batch snapshots, operation IDs, and termination-state transitions **if** its production/test policy is repaired as noted below.

### REGRESSION_TESTABILITY_MATRIX

| Contract | Planned observation seam | Testable? | Design blocker affecting implementation |
|---|---|---:|---|
| REG-TGT-01 | TargetResolutionResult/trace | YES | none |
| REG-TGT-02 | State adapter + target trace | YES | none |
| REG-TGT-03 | intended/actual target fields | YES | none |
| REG-TGT-04 | Guard pass trace | YES | none |
| REG-TGT-05 | NA/TargetResolution IDs | YES | none |
| REG-TGT-06 | Guard trace #2 | YES | none |
| REG-TGT-07 | Cleave plan trace | YES | none |
| REG-CMB-01 | Action grant trace | YES | none |
| REG-CMB-02 | grant transition trace | YES | none |
| REG-CMB-03 | grant transition trace | YES | none |
| REG-CMB-04 | consume/cfg230/NA IDs | YES | none |
| REG-CMB-05 | admission decision trace | YES | F-06 caller coverage |
| REG-CLV-01 | settlement actual loss + Cleave result | YES | F-01 settlement seam |
| REG-CLV-02 | derived-route architecture hook | YES | none |
| REG-CLV-03 | permission decision trace | YES | none |
| REG-CLV-04 | Cleave effect/secondary trace | YES | F-04 source slot |
| REG-CLV-05 | target + Cleave anchor trace | YES | none |
| REG-CHN-01 | deferred snapshot + live execution trace | YES | none |
| REG-CHN-02 | traversal slot trace | YES | none |
| REG-CHN-03 | traversal + termination trace | YES | F-02/F-03 |
| REG-CHN-04 | restricted-settlement trace | YES | none |
| REG-SHR-01 | partition + settlement/direct-loss results | YES | F-01 |
| REG-SHR-02 | target commit + interrupt trace | YES | F-01 |
| REG-SHR-03 | DirectTroopLoss result/permission trace | YES | none |
| REG-SHR-04 | resolver selection + state lifecycle | YES | none |
| REG-DST-01 | immutable plan + step trace | YES | none |
| REG-DST-02 | plan step/death trace | YES | none |
| REG-DST-03 | plan + termination trace | YES | F-02/F-03 |
| REG-DST-04 | DirectTroopLoss result | YES | none |
| REG-CTR-01 | admitted batch snapshot | YES | F-04 source slot only for ordering fixtures |
| REG-CTR-02 | entry + local gate trace | YES | none |
| REG-CTR-03 | batch + zero terminal + termination trace | YES | F-02/F-03 |
| REG-CTR-04 | explicit zero terminal result | YES | none |
| REG-CTR-05 | admission decisions | YES | F-06 caller coverage |
| FINAL_01 | termination transitions + traversal barrier | YES | F-02/F-03 |
| FINAL_02 | termination transitions + Counter barrier | YES | F-02/F-03 |
| FINAL_03 | admission decision + termination trace | YES | F-02/F-03/F-06 |
| FINAL_04 | CleaveEffect admission + termination trace | YES | F-02/F-03 |
| FINAL_05 | Share local terminal + termination trace | YES | F-01/F-02 |
| FINAL_06 | Distribution plan + termination trace | YES | F-02/F-03 |
| REG-INT-01 | integer helper output | YES | F-05 representation boundary |
| REG-INT-02 | integer helper output | YES | F-05 |
| REG-INT-03 | integer helper output | YES | F-05 |
| REG-INT-04 | integer helper output | YES | F-05 |
| REG-INT-05 | integer helper output | YES | F-05 |

Recomputed:

```text
mandatory regressions = 45
testable by planned observable seams = 45
missing observation seam = 0
conflicting regression contracts = 0
untestable mandatory regression = 0
```

This does **not** mean implementation can start: several testable contracts are blocked by unresolved design ownership/API findings.

## 19. File Plan

### FILE_PLAN_AUDIT_MATRIX — new production files

The authored list independently recomputes to **16** new production files.

| New file | Classification | Audit note |
|---|---|---|
| `operation_identity.py` | NECESSARY | IDs/lineage/source type |
| `stage9_trace.py` | NECESSARY | mandatory admission/barrier observability |
| `stage9_integerization.py` | NECESSARY | P0 integerization boundary |
| `stage9_state_params.py` | NECESSARY | typed state metadata |
| `stage9_state_runtime.py` | NECESSARY | adapter over sole registry |
| `target_resolution_system.py` | NECESSARY | target arbitration owner |
| `reaction_permission_policy.py` | NECESSARY | recursion/callback authority |
| `execution_right_system.py` | NECESSARY | global future admission |
| `damage_instance_coordinator.py` | NECESSARY | standard DamageInstance owner |
| `damage_partition_system.py` | NECESSARY | exactly-one resolver/typed plans |
| `direct_troop_loss_system.py` | NECESSARY | non-hit attributed loss |
| `derived_damage_system.py` | MERGE_CANDIDATE | only Cleave consumer today |
| `cleave_system.py` | NECESSARY | Cleave effect/queue |
| `chain_system.py` | NECESSARY | Chain traversal |
| `counter_system.py` | NECESSARY | CounterBatch |
| `battle_finalization_coordinator.py` | NECESSARY | termination owner after repair |

Result: **15 NECESSARY + 1 MERGE_CANDIDATE = 16**.

### FILE_PLAN_AUDIT_MATRIX — modified production files

The authored list independently recomputes to **11** modified production files.

| Planned modified file | Classification | Audit note |
|---|---|---|
| `context.py` | NECESSARY | allocator + small termination record |
| `battle_systems.py` | NECESSARY | composition root |
| `engine.py` | NECESSARY | migrate macro finalization integration |
| `action_system.py` | NECESSARY | Action scope/maintenance dispatch |
| `normal_attack_system.py` | NECESSARY | master orchestration |
| `damage_resolution_system.py` | NECESSARY | settlement seam |
| `effect_executor.py` | NECESSARY | standard DamageEffect routing |
| `victory_system.py` | UNJUSTIFIED AS WRITTEN | already pure; avoid needless core edit |
| `official_state_catalog.py` | NECESSARY | typed runtime bindings |
| `events.py` | NECESSARY | Stage9 observation facts if needed |
| `__init__.py` | NECESSARY | intentional exports |

**Definitely missing planned modified file:** `effect_result.py`. Its `DamageEffectResult.resolution` currently names `DamageResolutionResult`, which conflicts with the planned `DamageInstanceCoordinator` result shape.

**Missing logical provenance ingress:** the plan does not name the existing skill/effect files that must produce `source_skill_slot`. At minimum the design must choose a source-slot owner in the current skill runtime model and propagate it through the current apply path. Likely affected seams include `skill_runtime.py`, `skill_resolver.py`, and/or `effects.py`; the exact file set cannot be truthfully recomputed until the design chooses the ownership model.

Recomputed core-control edits:

```text
author-listed control-flow core edits = 8
justified among those = 7
unjustified among those = 1 (`VictorySystem`, already pure)
```

The report does not invent a fake revised total for source-slot ingress; that uncertainty is itself a MAJOR design finding.

## 20. Dependency Graph

### DEPENDENCY_GRAPH

Required acyclic direction after repair:

```text
BattleContext primitives / IDs / StateRegistry
        ↓
typed state adapter / target policy / permission policy / execution-right policy
        ↓
Stage8 DamageSystem + narrow settlement primitive
        ↓
partition plans / direct-loss resolver
        ↓
DamageInstanceCoordinator
        ↓
Cleave / Chain / Counter mechanism services
        ↓
NormalAttackSystem (master orchestration)
        ↓
ActionSystem
        ↓
BattleEngine

VictorySystem (pure evaluator)
        ↓
BattleFinalizationCoordinator / termination record
        ↑
death/victory facts from settlement + admitted-operation barriers
```

Critical direction rules:

- Finalization coordinator must **not** call `BattleEngine`.
- Local mechanism systems must **not** call back into NormalAttack/Action/Engine to advance lifecycle.
- `DamageInstanceCoordinator` may notify a finalization port/service, but that service may not depend on the coordinator implementation.
- State adapter reads registry; lifecycle mutates registry. Mechanism systems do not own a parallel state store.
- All systems are composed/injected by `BattleSystems`; no method-level `new SystemB()` and no singleton.

**Known required dependency cycle count: 0.**  
There is a **cycle hazard** only if the repair makes the finalization coordinator invoke `BattleEngine._finish()` directly; that direction is explicitly rejected by this audit.

### PLANNED_DEPENDENCY_INJECTION_MATRIX

| Consumer | Injected dependency | Composition owner |
|---|---|---|
| TargetResolution | Target primitives + Stage9StateRuntime | `BattleSystems` |
| DamagePartition | Stage9StateRuntime + integerization/policies | `BattleSystems` |
| DirectTroopLoss | `TroopSystem` + provenance/finalization port | `BattleSystems` |
| DamageInstanceCoordinator | `DamageSystem`, settlement seam, partition, permission, finalization port | `BattleSystems` |
| Cleave | state runtime, derived-damage boundary, execution gate | `BattleSystems` |
| Chain | state runtime, restricted settlement, execution gate | `BattleSystems` |
| Counter | state runtime, DamageInstanceCoordinator, permission, execution gate | `BattleSystems` |
| NormalAttack | target, damage, Cleave, Chain, Counter, execution gate, Combo adapter/Assault port | `BattleSystems` |
| FinalizationCoordinator | Victory evaluator + termination record/barrier policy | `BattleSystems` |
| Engine | ActionSystem + FinalizationCoordinator | `BattleSystems` |

## 21. Implementation Phases

### PHASE_DEPENDENCY_GRAPH

Authored dependency intent:

```text
9.1 identity/numeric/state metadata
  ↓
9.2 state adapter + target/Guard
  ↓
9.3 NormalAttack master + Combo
  ↓
9.4 DamageInstance + partition + direct loss
  ↓
9.5 Cleave + Chain
  ↓
9.6 Counter
  ↓
9.7 Execution Right + Finalization
  ↓
9.8 integration
```

The graph is textually acyclic, but **not independently buildable as written**.

| Phase | Can another AI implement without semantic/ownership guess? | Round1 verdict |
|---|---:|---|
| 9.1 | NO | exact numeric representation boundary is missing |
| 9.2 | NO | source-slot metadata ingress required by state adapter is not owned; target `selectedTarget` ambiguity is minor |
| 9.3 | PARTIAL | master model is clear, but full future-admission caller contract is not |
| 9.4 | NO | settlement seam is non-unique; production path requires finalization notification but real owner arrives in 9.7 |
| 9.5 | NO | depends on 9.4 seam and execution/finalization admission semantics |
| 9.6 | NO | depends on source-slot ordering + 9.4 + future-admission semantics |
| 9.7 | NO | Engine/coordinator terminal compatibility ownership is non-unique |
| 9.8 | NO | integration cannot close three unenforced invariants until design repair |

### BLOCKER: forward semantic dependency

Phase 9.4 installs production `EffectExecutor -> DamageInstanceCoordinator`, while the coordinator’s own standard flow includes notifying the finalization owner and completing an operation barrier. The real Execution Right / Finalization owner is deferred to 9.7. A “stub latch” in tests does not make the **production** 9.4 intermediate state architecturally complete.

Repair must either:

1. introduce the minimal real termination/admission/finalization service before the production DamageInstance reroute, then migrate Engine publication later; or
2. delay the production reroute until that real service exists.

No repair is executed in this audit.

## 22. Stage8 Boundary

Stage8 frozen formula/modifier/prevention/hit semantics do not need to change.

Round1 result:

```text
Stage8 semantic edits required = 0
Stage8 reopen required = 0
Stage8 seam specification defect = 1 BLOCKER (settlement semantics)
```

The repair must preserve the existing legacy calculation/settlement path while adding a Stage9 typed assigned-target settlement path around it.

## 23. Research-Debt Isolation

`DSTS9-B02` remains isolated to Distribution’s local continuation policy. It must not become a generic `BattleFinalizationCoordinator` rule. Finalization consumes the transaction’s admitted/terminal status; it does not know why Distribution continues locally.

Counter exact universal comparator/dispel fidelity remains isolated to Counter ordering/state policy. Generic ReactionBatch architecture must not bake in an alleged official order.

No new research debt is created by this audit.

## 24. Findings

### BLOCKER

**F-01 — Damage settlement fact/API ownership is non-unique.**  
`DamageResult.final_damage=Dtotal` must be preserved while actual target settlement uses `Dtarget`, but the spec does not define the typed settlement request/result, event payload meaning, or legacy mapping. This can silently make consumers read the wrong damage layer.

**F-02 — Finalization ownership is non-unique between coordinator and current Engine compatibility projection.**  
Current `BattleEngine._finish()` owns `context.ended`, result, phase transition, and `BATTLE_ENDED`; Stage9 also declares a sole finalization coordinator. The exact split is not specified.

**F-03 — Phase 9.4 has a forward production dependency on 9.7 finalization/execution-right infrastructure.**  
A test stub latch is insufficient for an independently green production phase.

### MAJOR

**F-04 — `source_skill_slot` has a storage design but no authoritative producer/ingress path.**  
Current Unit/SkillRuntime/SkillResolver/effect/state-apply contracts provide only `source_skill_id`. External/no-slot sources and fallback comparator authority are also unspecified.

**F-05 — Exact integerization input representation/conversion boundary is unspecified while current coefficients are floats.**  
The helper rule is correct, but callers can still feed binary-float artifacts.

**F-06 — FutureAdmissionGate is conceptually centralized but concrete caller ownership is incomplete.**  
Every future branch must pass exactly one global admission seam; local liveness gates must remain separate.

**F-07 — EffectExecutor rerouting is incompatible with the current `DamageEffectResult` type/file plan.**  
`effect_result.py` is not planned for modification although `DamageEffectResult.resolution` currently names `DamageResolutionResult` and 9.4 introduces a Stage9 damage-execution result.

### MINOR

**F-08 — `selectedTarget` vs `intendedAttackTarget` is not semantically distinguished.**  
Remove/alias/document the diagnostic role so no extra RNG/selection occurs.

**F-09 — Engineering tie-breakers need stronger “project default, not official order” labeling.**  
Especially `unit_id` and stable source/instance fallbacks.

**F-10 — `TargetResolutionId` is supporting/trace-only over-design.**  
Not harmful, but there is no independent gameplay lifecycle requiring it.

**F-11 — Generic `DerivedDamageSystem<T>` is speculative with Cleave as its only current consumer.**  
Keep Cleave-specific or extremely narrow.

**F-12 — Planned `VictorySystem` core edit is unnecessary against current source.**  
It is already a pure evaluator.

**F-13 — Stage9 trace production lifecycle is underspecified.**  
Freeze whether production default is no-op/bounded/debug-only, battle lifetime/retention, and serialization behavior. Trace must never affect gameplay.

### DOC_ONLY

None.

## 25. Final Gate

Recomputed from current remote `main` and current design:

```text
BLOCKER = 3
MAJOR = 4
MINOR = 6
DOC_ONLY = 0

P0 semantic conflict = 0
Stage8 reopen = 0
Unowned runtime fact = 1
Dependency cycle = 0
Unspecified reachable path = 5
Untestable mandatory regression = 0
Unenforced invariant = 3

planned new production files = 16
planned modified production files = 11
planned core-control edits = 8 listed / 7 justified
42 invariant mappings = 42 checked / 3 unenforced
45 regression mappings = 45 checked / 45 testable
```

The five unspecified reachable path families are:

1. `Dtarget -> assigned settlement -> event/result fact meanings`;
2. `EffectExecutor -> DamageInstanceCoordinator -> EffectExecutionResult` carrier;
3. `source_skill_slot` producer -> state application;
4. finalization semantic state -> Engine compatibility projection/publication;
5. each future branch -> centralized FutureAdmissionGate caller edge.

### ROUND1_REPAIR_PLAN

Priority order only; **not executed in this round**:

1. Repair the Damage settlement contract first: freeze distinct `Dtotal`, assigned `Dtarget`, actual loss, event payload meaning, result type, and legacy API mapping.
2. Repair finalization compatibility ownership: one semantic writer, one compatibility/publication projection contract, no coordinator -> Engine callback.
3. Reorder phases so real minimal execution-right/finalization infrastructure exists before production damage rerouting/mechanism integration.
4. Define `source_skill_slot` owner, apply-time ingress, no-slot representation, and comparator fallback authority.
5. Freeze Stage9 exact-number representation/conversion boundary.
6. Assign every FutureAdmissionGate caller edge and add no-bypass architecture assertions.
7. Repair EffectExecutor result compatibility/file plan, including `effect_result.py`.
8. Clean the six MINOR items without changing P0.

## 26. Verdict

# FAIL — DESIGN REPAIR REQUIRED

Reason: the design is semantically aligned with current P0 and does not require reopening Stage8, but it is **not yet uniquely implementable** at the settlement seam, finalization compatibility boundary, or phase-9.4 intermediate state. Four additional MAJOR implementation-design gaps remain.

Therefore:

```text
STAGE9 FROZEN = NO
Ready for implementation = NO
STATUS = DRAFT — DESIGN AUDIT REQUIRED
```

Correct next step:

```text
Stage9 Design Repair Round 1
```

Do not start Round 2 until the BLOCKER/MAJOR findings above are repaired and re-audited.
