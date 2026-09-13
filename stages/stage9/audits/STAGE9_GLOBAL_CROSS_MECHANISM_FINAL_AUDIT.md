# Stage9 Global Cross-Mechanism Final Audit

## 1. Repository Baseline

Audit type: `READ-ONLY DESIGN AUDIT`.

Audit-start and pre-commit baselines were independently re-read from remote `main` and remained unchanged during the audit:

```text
battle:
lxy2005051020-commits/sgs-v2-battle-system
6941e9cd1ee1568dcf645a4a493752add7e5813c
docs(stage9): close documentation drift package

state:
lxy2005051020-commits/sgs-state-mechanics-research
033a0314a101b17222d7cefa79dbf178b8eaca9f
docs(stage9): sync mechanism status and authority navigation
```

No battle-report research was started. No production code, tests, Frozen mechanism semantics, README/Index, or `STAGE9.md` were changed by this audit.

## 2. Audit Scope

The audit was executed horizontally rather than mechanism-by-mechanism:

```text
Target
→ Lifecycle
→ Damage
→ Reaction
→ Death
→ Finalization
→ Runtime Contract
→ Regression
```

Mandatory inputs read and cross-checked:

- `STAGE9_AUTHORITY_MAP.md`;
- RF-P01..RF-P07;
- RF-C01 hardening ledger, typed contracts, 42 invariants, 45 regression contracts, hardening report;
- RF-C02 documentation ledger/report;
- Core Arbitration, Execution Right, Finalization P0;
- nine current mechanism P0/Freeze Records;
- current README/Index/Evidence Matrix/superseded navigation surfaces;
- existing RF-P06 archived evidence only where needed to classify one audit finding.

This is a specification-completeness audit, not production-test execution.

## 3. Authority Hierarchy

Current authority follows `STAGE9_AUTHORITY_MAP.md`. Repair/audit records are provenance unless explicitly named as an authority bridge. RF-C01 owns runtime representation, not gameplay semantics.

### STAGE9_GLOBAL_AUTHORITY_MATRIX

| Domain | Authoritative file / owner | Consumers | Competing current authority? | Verdict |
|---|---|---|---:|---|
| Target selection | Core Arbitration + CONFUSION/TAUNT P0 | NormalAttack, Combo #2 | 0 | CONSISTENT |
| Guard redirect | GUARD P0 | NormalAttack, Counter, Cleave, Assault | 0 | CONSISTENT |
| NormalAttack lifecycle | Core Arbitration / NormalAttack Orchestrator | all NormalAttack observers | 0 | CONSISTENT |
| Execution right | `STAGE9_EXECUTION_RIGHT_AND_DEATH_SCOPE_CONTRACT.md` | mechanism local transactions | 0 | CONSISTENT |
| Finalization | `STAGE9_BATTLE_FINALIZATION_BARRIER_CONTRACT.md` | all mechanisms | 0 | CONSISTENT |
| Integerization | mechanism P0 + RF-P01/RF-P06 re-freeze | RF-C01 regression vectors | 0 | CONSISTENT, one notation MINOR |
| Derived damage | CLEAVE P0 / CHAIN P0 | Hit/settlement policy | 0 | CONSISTENT |
| Direct troop loss | DAMAGE_SHARE / DISTRIBUTION P0 | typed `AttributedDirectTroopLoss` | 0 | CONSISTENT |
| Reaction admission | mechanism P0 + Execution Right + Finalization | Counter/Cleave/Chain/partition callbacks | 0 | CONSISTENT |
| State lifecycle | each mechanism P0 | ActionStart maintenance / target/runtime reads | 0 | CONSISTENT |
| Runtime typed contracts | RF-C01 typed contract | Stage9 implementation | 0 | REPRESENTATION ONLY |
| Runtime invariants | RF-C01 invariants | Stage9 tests/assertions | 0 | REPRESENTATION ONLY |
| Regression contracts | RF-C01 regression spec | Stage9 build tests | 0 | TEST SPEC ONLY |
| Documentation navigation | RF-C02 Authority Map + README/Index | readers/tooling | 0 semantic | one DOC_ONLY stale banner found in COMBO body |
| Historical evidence | R1-R8 / independent audits / old minimum_usable | provenance only | N/A | HISTORICAL/SUPERSEDED |

Authority domains audited: **15**.  
Current competing P0 owners: **0**.  
Authority-duplication conflicts: **0**.

## 4. Mechanism Status Matrix

| ID | Mechanism | P0 status | Runtime status | Open blocker | Research debt |
|---:|---|---|---|---:|---|
| 690103 | CONFUSION | FROZEN | READY | 0 | none blocking |
| 690106 | TAUNT | FROZEN | READY | 0 | none blocking |
| 690098 | GUARD | FROZEN | READY | 0 | none blocking |
| 690081 | COMBO | FROZEN | READY | 0 | none blocking |
| 690084 | CLEAVE | FROZEN | READY | 0 | none blocking |
| 690097 | CHAIN_LINK | FROZEN | READY | 0 | none blocking |
| 690087 | DAMAGE_SHARE | FROZEN | READY | 0 | none blocking |
| 690086 | DISTRIBUTION | RUNTIME_READY_WITH_RESEARCH_DEBT | deterministic | 0 | `DSTS9-B02` |
| 690085 | COUNTERATTACK | FROZEN | deterministic | 0 | non-blocking official comparator/dispel fidelity notes, no runtime ambiguity |

`DSTS9-B02` remains intentionally dual-status:

```text
EMPIRICAL: OPEN / UNOBSERVED
RUNTIME: CLOSED BY PROJECT_RUNTIME_DEFAULT
DESIGN: NOT BLOCKING
RESEARCH DEBT: YES
NOT EMPIRICALLY PROVEN
```

## 5. Global Lifecycle

Single master owner: **Stage9 Core Arbitration / NormalAttack Orchestrator**.

Audited master order:

```text
NormalAttack permission
→ fresh target resolution
→ Confusion / Taunt arbitration
→ Guard
→ Target Lock
→ main damage
→ defender death fact
→ immediate hit reactions
→ Cleave / Chain semantics
→ CounterBatch
→ Assault
→ Combo Checkpoint
```

Chain special order is consistent across Core, Chain, Counter and RF-C01:

```text
WITHOUT Cleave:
main-target Chain INLINE
→ CounterBatch

WITH Cleave:
main-target Chain deferred
→ Cleave secondary #1 → Chain INLINE
→ Cleave secondary #2 → Chain INLINE
→ current Cleave effect completion
→ deferred main-target Chain
→ CounterBatch
```

No mechanism P0 currently owns a contradictory second master lifecycle.

Verdict: **CONSISTENT**.

## 6. Target Arbitration

Audited target pipeline:

```text
Alive Pool
→ camp constraint
→ Confusion
→ Taunt
→ IntendedAttackTarget
→ Guard exactly once
→ PostRedirectActualTarget
→ DamageRecipient(s) at concrete settlement
```

Positive checks:

- Confusion shadows the Taunt selector only; Taunt lifecycle is not deleted/suppressed by that fact.
- Guard is single-pass and non-recursive.
- Combo #2 creates a fresh NormalAttack target-resolution context.
- Share/Distribution inspect the final actual DamageEvent target.
- Counter holder is the final actual NormalAttack receiver.
- Cleave topology anchors on the post-Guard actual target.

RF-C01 types:

```text
SelectedTarget
IntendedAttackTarget
PostRedirectActualTarget
DamageRecipient
```

introduce no new target-selection behavior. `SelectedTarget` is representation/provenance; behavior-driving pre-Guard identity remains `IntendedAttackTarget`, and downstream attack-bound behavior uses `PostRedirectActualTarget`. No overwrite-style single mutable `target` authority remains.

Verdict: **CONSISTENT**.

## 7. Combo

Audited entry and grant order:

```text
ActionStart maintenance
→ expiry/removal
→ suppression state settles
→ effective Combo read
→ Action-local grant
→ provenance lock
```

Audited checkpoint:

```text
authoritative #1 lifecycle complete
→ Combo Checkpoint
→ atomic consume
→ cfg230
→ can_normal_attack()
→ future-work admission gate
→ fresh target resolution
→ possible NormalAttack #2
```

Ceilings are unique and consistent:

```text
cfg230 <= 1 / Action
#2 <= 1 / Action
#3 impossible
```

Death/finalization:

- actor death before future Combo admission: no #2 and no cfg230 from the dead-actor path;
- #1 satisfies VictoryCondition: #2 is never admitted;
- victory latch does **not** imply cfg230 must be absent; RF-P04 observed post-latch cfg230 in a subset while #2 remained 0.

Verdict: **CONSISTENT**.

## 8. Cleave

Damage kernel:

```text
CleaveBase = ActualTargetTroopLoss
CleaveDamage = FLOOR(ActualTargetTroopLoss × CleaveRatio)
```

Identity/permission:

```text
Cleave != NormalAttack
no base formula rerun
no Crit reroll
no generic target modifier rerun
Counter blocked
recursive Cleave blocked
Evasion / Resistance / Share or Distribution / FirstAid / Chain allowed by local policy
```

State/queue:

```text
SOURCE_BOUND_EFFECT_LIST
same-source REFRESH
multi-source COEXIST
SKILL_SLOT_ORDER
effect-major execution
secondary GLOBAL_SLOT_ASCENDING
JIT secondary liveness
```

Finalization:

- main target death may still allow the current Cleave operation to start under frozen evidence;
- secondary commander death drains the current admitted CleaveEffect's remaining locally legal secondaries;
- a later independent CleaveEffect not yet admitted after victory latch is blocked;
- attacker death remains a local liveness cancellation for later not-yet-executed Cleave work.

Current P0/runtime semantics are consistent. One RF-P06 **supporting-evidence example** is malformed; see Finding `FA-M01`.

Verdict: **SEMANTICS CONSISTENT; SUPPORTING RECORD MINOR**.

## 9. Chain

Frozen kernel:

```text
TRUE_FEEDBACK
base = TriggerNodeResolvedDamage
integerization = FLOOR
```

Traversal:

```text
one-pass
slot order deterministic
JIT live eligibility
later unvisited eligible slot may join
visited/passed slot never revisited
```

Deferred main-target work:

```text
snapshot: trigger amount / trigger identity / parent provenance
live-read at execution: source/trigger liveness, current Chain state, current owner, ratio/effect metadata, candidate state
```

Finalization:

```text
commander death mid traversal
→ victory latch
→ admitted ChainTraversal drains remaining eligible slots
→ no unrelated future work
→ finalization after traversal boundary
```

Verdict: **CONSISTENT**.

## 10. Damage Share

Math:

```text
Dsharer = ROUND_HALF_UP(Dtotal × R)
Dtarget = Dtotal - Dsharer
```

Commit:

```text
TARGET FIRST
→ target death check
→ if target survives: sharer direct troop-loss commit
→ if target dies: TARGET_DEATH_INTERRUPT; pending sharer work discarded
```

Sharer loss is `AttributedDirectTroopLoss`, not a DamageEvent. It cannot trigger Defense/Evasion/Resistance/FirstAid/Counter/Chain/Share/Distribution/generic hurt callbacks.

Battle/state P0 semantics are synchronized.

Verdict: **CONSISTENT**.

## 11. Distribution

Math:

```text
Dtarget = ROUND_HALF_UP(Dtotal × (1-R))
Dtransfer = Dtotal - Dtarget
Dparticipant = ROUND_HALF_UP(Dtransfer / N)
```

At each DamageInstance, a plan is built from the live participant set. Once the transaction plan is admitted:

```text
participant identities fixed
N fixed
Dtarget / Dtransfer / Dparticipant fixed
participants commit first in slot order
target commits last
```

A planned participant becoming invalid means `SKIP`, not recomputation or replacement. Ordinary participant death does not abort later planned work.

`DSTS9-B02`:

```text
commander participant lethal empirical sample = 0
empirical status = OPEN / UNOBSERVED
runtime = drain admitted fixed plan under PROJECT_RUNTIME_DEFAULT
finalization follows transaction boundary
```

No runtime TODO/undefined branch remains.

Verdict: **CONSISTENT WITH EXPLICIT RESEARCH DEBT**.

## 12. Counter

Trigger and identity:

```text
trigger = ON_NORMAL_ATTACK_RECEIVED
holder = final actual NormalAttack receiver
Counter = independent Weapon DamageEvent
Counter != NormalAttack
```

Batch semantics:

```text
trigger-time admission snapshot
execution-time world live
post-admission state suppression/removal/expiry does not revoke entry
owner death before entry begins cancels via local liveness gate
target death from earlier sibling does not revoke later admitted sibling
```

Dead-target sibling path:

```text
CounterExecute
→ attributed zero troop loss
→ complete entry
```

It does not run the full Stage8 Weapon DamageRequest against a dead target.

Counter's exact official universal source comparator and universal dispel fidelity remain non-blocking research/fidelity notes; the project runtime has deterministic defaults and no reachable undefined branch.

Verdict: **CONSISTENT**.

## 13. Recursion Matrix

### STAGE9_GLOBAL_RECURSION_MATRIX

| From | To | Rule | Authority |
|---|---|---|---|
| Cleave | Cleave | BLOCK | CLEAVE P0 / INV-17 |
| Cleave | Counter | BLOCK | CLEAVE + COUNTER identity |
| Cleave | Chain | ALLOW | CLEAVE P0 |
| Cleave | Share | ALLOW | CLEAVE + SHARE P0 |
| Cleave | Distribution | ALLOW | CLEAVE + DISTRIBUTION P0 |
| Cleave | FirstAid | ALLOW | CLEAVE P0 |
| Counter | Counter | BLOCK | COUNTER P0 |
| Counter | Cleave | BLOCK | no NormalAttack identity |
| Counter | Assault | BLOCK | no NormalAttack identity |
| Counter | Chain | ALLOW | COUNTER P0 |
| Counter | Share | ALLOW | COUNTER + SHARE P0 |
| Counter | Distribution | ALLOW | COUNTER + DISTRIBUTION P0 |
| Counter | FirstAid | ALLOW | COUNTER P0 |
| Chain | Chain | BLOCK | CHAIN restricted TRUE_FEEDBACK |
| Chain | Counter | BLOCK | CHAIN restricted TRUE_FEEDBACK |
| Chain | Share | BLOCK | CHAIN restricted TRUE_FEEDBACK |
| Chain | Distribution | BLOCK | CHAIN restricted TRUE_FEEDBACK |
| Chain | FirstAid | BLOCK | CHAIN restricted TRUE_FEEDBACK |
| Share DirectLoss | all hit callbacks | BLOCK | SHARE + typed DirectTroopLoss |
| Distribution DirectLoss | all hit callbacks | BLOCK | DISTRIBUTION + typed DirectTroopLoss |

Runtime-reachable `UNSPECIFIED` cells in required matrix: **0**.

## 14. Damage Layer Matrix

| Layer | Meaning | May be reused as another layer? | Verdict |
|---|---|---:|---|
| `Dtotal` | normal formula result before partition | NO | distinct |
| `Dtarget` | theoretical quota assigned to actual DamageEvent target after partition | NO | distinct |
| `ActualCommittedTroopLoss` / `ActualTargetTroopLoss` | troop-clamped committed target loss | NO | distinct |
| `CreditedDamage` | attribution/statistics layer | NO | distinct |
| `DerivedCalculatedDamage` | calculated Cleave/Chain derived value before target clamp/settlement | NO | distinct |
| `AttributedDirectTroopLoss` | non-DamageEvent troop mutation for Share/Distribution recipients | NO | distinct |

RF-C01 typed contracts do not use `final_damage`, `real_damage`, or a mutable generic `damage` field as multi-layer semantic authority.

Damage-layer semantic conflicts: **0**.

## 15. Integerization Matrix

### STAGE9_INTEGERIZATION_MATRIX

| Call site | Rule | Explicit regression |
|---|---|---|
| CHAIN | FLOOR | REG-INT-01 |
| CLEAVE | FLOOR | REG-INT-05 |
| SHARE `Dsharer` | ROUND_HALF_UP | REG-INT-02 |
| DISTRIBUTION `Dtarget` | ROUND_HALF_UP | REG-INT-03 |
| DISTRIBUTION `Dparticipant` | ROUND_HALF_UP | REG-INT-04 |

Regression vectors contain explicit integers and do not use host-language `round()` as an oracle.

Current authoritative integerization conflicts: **0**.

Non-blocking notation finding: Core Arbitration §6 still uses generic `round(...)` shorthand and generic Cleave multiplication in a current shared summary even though the owning mechanism P0s are precise. See `FA-M02`.

## 16. Execution Right Matrix

| Work | Admission point | Death after admission | Local gate | Future branch? |
|---|---|---|---|---|
| Damage microstep | current DamageInstance commit | current committed microstep is not rolled back | target clamp/current settlement legality | NO |
| Counter sibling | CounterBatch creation | target death does not revoke sibling | counter-owner alive; dead target uses zero-loss terminal | NO |
| Cleave secondary | current CleaveEffect secondary plan | secondary commander death does not erase current effect plan | attacker/secondary local liveness; dead secondary SKIP | later independent CleaveEffect = YES |
| Chain slot | ChainTraversal admission | commander death does not erase traversal | JIT alive/linked; deferred source/state live-read | NO |
| Share pending sharer | target-first transaction after target survives gate | lethal target interrupts before sharer commit | target survived + sharer locally valid/alive | NO |
| Distribution participant | DistributionTransactionPlan creation | ordinary/commander death follows fixed-plan local rule | per-step participant eligibility; invalid = SKIP | NO |
| Assault | branch boundary after CounterBatch | actor/victory death before admission cancels | actor live + future-work admission | YES |
| Combo #2 | Combo Checkpoint future-branch boundary | actor death/victory before admission blocks #2 | grant/consume + can_normal_attack + admission + fresh target | YES |

Global rules remain:

```text
death != universal abort
admitted != unconditional execution
```

Execution-right conflicts: **0**.

## 17. Finalization State Machine

Unique runtime state machine:

```text
RUNNING
→ VICTORY_LATCHED
→ DRAINING_ADMITTED_WORK
→ FINALIZED
```

with implementation substeps such as commander collateral processing/barrier crossing contained under the finalization owner.

Strict identities:

```text
UnitDeathFact
!= VictoryConditionLatched
!= BattleFinalized
```

After victory latch, future admission is uniformly blocked for:

```text
next Action
future Assault
Combo #2
new CounterBatch
new ChainTraversal
unadmitted next CleaveEffect
```

Already-admitted current work drains/cancels only by its local contract.

Low-level mechanisms have no authority to set a generic `battle.finished = true`.

Finalization conflicts: **0**.

## 18. Typed Runtime Contracts

| Typed contract | P0 fidelity | New gameplay rule? | Conflict |
|---|---|---:|---:|
| `TargetResolutionResult` | faithful target identity + one-pass Guard | NO | 0 |
| `ComboActionGrant` | faithful physical/operational/grant split | NO | 0 |
| `DerivedDamageRequest` | faithful Cleave derived identity/base/permissions | NO | 0 |
| `AttributedDirectTroopLoss` | faithful Share/Distribution non-hit identity | NO | 0 |
| `CounterBatchEntry` | faithful admission/live execution split | NO | 0 |
| `DistributionTransactionPlan` | faithful fixed-plan semantics | NO | 0 |
| `ChainDeferredWork` | faithful snapshot/live split | NO | 0 |
| `BattleTerminationState` | faithful finalization state machine | NO | 0 |

Typed-runtime contract conflicts: **0**.  
Missing necessary runtime identity fields found: **0**.

## 19. Runtime Invariants

All 42 RF-C01 invariants were individually traced back to current P0/repair authority.

| IDs | Classification |
|---|---|
| INV-01 | SUPPORTED |
| INV-02 | SUPPORTED |
| INV-03 | SUPPORTED |
| INV-04 | SUPPORTED |
| INV-05 | SUPPORTED |
| INV-06 | SUPPORTED |
| INV-07 | SUPPORTED |
| INV-08 | SUPPORTED |
| INV-09 | SUPPORTED |
| INV-10 | SUPPORTED |
| INV-11 | SUPPORTED |
| INV-12 | SUPPORTED |
| INV-13 | SUPPORTED |
| INV-14 | SUPPORTED |
| INV-15 | SUPPORTED |
| INV-16 | SUPPORTED |
| INV-17 | SUPPORTED |
| INV-18 | SUPPORTED |
| INV-19 | SUPPORTED |
| INV-20 | SUPPORTED |
| INV-21 | SUPPORTED |
| INV-22 | SUPPORTED |
| INV-23 | SUPPORTED |
| INV-24 | SUPPORTED |
| INV-25 | SUPPORTED |
| INV-26 | SUPPORTED |
| INV-27 | SUPPORTED |
| INV-28 | SUPPORTED |
| INV-29 | SUPPORTED |
| INV-30 | SUPPORTED |
| INV-31 | SUPPORTED |
| INV-32 | SUPPORTED |
| INV-33 | SUPPORTED |
| INV-34 | SUPPORTED |
| INV-35 | SUPPORTED |
| INV-36 | SUPPORTED |
| INV-37 | SUPPORTED |
| INV-38 | SUPPORTED |
| INV-39 | SUPPORTED |
| INV-40 | SUPPORTED |
| INV-41 | SUPPORTED |
| INV-42 | SUPPORTED |

Totals:

```text
SUPPORTED = 42
DUPLICATED_BUT_CONSISTENT = 0
CONFLICT = 0
UNDER-SPECIFIED = 0
```

## 20. Regression Coverage

All 45 RF-C01 regression contracts were content-audited against current P0, not merely title-counted.

```text
Target         7  → REG-TGT-01..07
Combo          5  → REG-CMB-01..05
Cleave         5  → REG-CLV-01..05
Chain          4  → REG-CHN-01..04
Share          4  → REG-SHR-01..04
Distribution   4  → REG-DST-01..04
Counter        5  → REG-CTR-01..05
Finalization   6  → FINAL_01..06
Integerization 5  → REG-INT-01..05
TOTAL         45
```

Classification:

```text
TRACEABLE TO CURRENT P0 = 45
REGRESSION CONFLICT      = 0
MISSING MANDATORY COVERAGE = 0
```

### P0_RULE → REGRESSION_ID coverage map

| P0 rule | Regression coverage |
|---|---|
| Confusion > Taunt > Guard | REG-TGT-01, REG-TGT-02, REG-TGT-03, REG-TGT-04 |
| Combo fresh #2 | REG-TGT-05, REG-TGT-06, REG-CMB-04 |
| Combo battle-end block | FINAL_03 |
| Cleave actual-loss base | REG-CLV-01, REG-INT-05 |
| Cleave commander-secondary drain | FINAL_04 |
| Chain deferred live read | REG-CHN-01 |
| Share lethal interrupt | REG-SHR-02, FINAL_05 |
| Distribution fixed plan | REG-DST-01, REG-DST-02 |
| Distribution commander engineering default | REG-DST-03, FINAL_06 |
| Counter queued sibling | REG-CTR-03, FINAL_02 |
| Counter owner-death gate | REG-CTR-02 |
| Counter zero-loss path | REG-CTR-04 |
| Victory latch / Finalization barrier | FINAL_01..06, INV-39..41 |

No production tests were executed or required by this audit.

## 21. Stage8 Boundary

Audited boundary:

```text
Stage8 = FROZEN
Formal Stage8 Reopen = NO
```

Stage9 only wraps/coordinates/derives/redirects/partitions/schedules/finalizes around Stage8 seams.

No current Stage9 contract modifies:

```text
Stage8 base damage formulas
DamageFormulaPolicy
Stage8 modifier ownership
Stage8 DamageResult contract
```

Counter legitimately calls the existing independent Stage8 weapon-damage resolution for a live target; Cleave/Chain do not rerun the base formula.

Stage8 boundary violations: **0**.

## 22. Documentation Consistency

RF-C02 current navigation was re-checked through Stage9 README, Authority Map, Evidence Matrix, state Index, DOC_DRIFT ledger, and superseded minimum_usable entry points.

Positive result:

```text
README current status conflict = 0
Index current status conflict = 0
Evidence Matrix current status conflict = 0
Authority Map conflict = 0
minimum_usable current-authority leakage = 0
DSTS9-B02 collapsed to empirical CLOSED = 0
```

One status-presentation issue remains inside the authoritative COMBO body: §9 still contains the historical RF-P02-era banner `STATUS: OPEN — CBS9-B03`, while §26 later correctly re-freezes `CBS9-B03 = CLOSED` via RF-P04. Behavior is unique; presentation is stale. See `FA-D01`.

Documentation current semantic conflict count: **0**.  
Documentation status-presentation finding count: **1**.

## 23. Cross-Repo Consistency

Audited dual-repo authority/mirror relationships:

- COMBO: state repo sole P0 owner; battle repo carries repair/navigation reference, no competing mirror.
- CLEAVE: state P0 current owner; battle Freeze Record is supporting and behaviorally compatible.
- DAMAGE_SHARE: state P0 and battle Freeze Record are semantically synchronized.
- GUARD: state P0 and battle compatibility contract are behaviorally consistent.
- CONFUSION: state P0 is the mechanism authority; battle shared arbitration consumes it without redefining lifecycle.

Cross-repo semantic conflicts: **0**.

Header/provenance/legacy terminology differences do not alter behavior.

## 24. Research Debt

Formal Stage9 research-debt finding:

### `DSTS9-B02`

```text
EMPIRICAL: OPEN / UNOBSERVED
RUNTIME: CLOSED BY PROJECT_RUNTIME_DEFAULT
DESIGN: NOT BLOCKING
RESEARCH DEBT: YES
NOT EMPIRICALLY PROVEN
```

This is not a BLOCKER because the runtime policy is deterministic and the empirical gap is explicitly labeled.

COUNTER also retains non-blocking fidelity notes for the exact official universal multi-source comparator and universal dispel behavior. They do not create runtime ambiguity and are not counted as additional open Stage9 architecture findings.

Formal `RESEARCH_DEBT` finding count: **1**.

## 25. Findings

### `FA-M01` — MINOR — RF-P06 decisive Cleave example is numerically/evidentially inconsistent

Location:

```text
stages/stage9/repairs/RF_P06_CLEAVE_DAMAGE_LAYER_AND_RECOVERY_BASIS_REFREEZE.md
§6 Decisive Proof 2
```

The text states, for `战报_1105099_pid1100193.json`:

```text
Dtarget = 475
CleaveRatio = 62%
475 × 0.62 = 294.5
observed Cleave = 295
floor(294.5) → 295
```

That is mathematically incompatible with `FLOOR` (`floor(294.5)=294`). More importantly, the already-archived `CLEAVE_DAMAGE_LAYER_EVIDENCE.json` entry for the same battle and `Dtarget=475` records `obs_cleave=251`, inferred ratio about `0.5284`, and `pred_dtarget=294`, not the quoted 295 example.

Why non-blocking:

- current CLEAVE P0 is explicit `FLOOR(ActualTargetTroopLoss × CleaveRatio)`;
- RF-P06 §4/§9, RF-P07, state CLEAVE P0, RF-C01 INV-15, REG-CLV-01 and REG-INT-05 all agree;
- multiple valid archived FLOOR vectors remain.

Required pre-Stage9 fix: remove or replace this malformed proof example with an already-valid archived sample. Do not change the frozen rule.

### `FA-M02` — MINOR — Core Arbitration uses under-specific integerization/Cleave shorthand

Locations:

```text
STAGE9_CORE_ARBITRATION_RULES_V2.md §6.1 / §6.2
  round(...)

STAGE9_CORE_ARBITRATION_RULES_V2.md §6.5 / §8.1
  MainAttackFinalDamage × CleaveRatio
```

The mechanism owners are precise (`ROUND_HALF_UP` for Share/Distribution, `FLOOR(ActualTargetTroopLoss × ratio)` for Cleave), so runtime is uniquely decidable and there is no P0 direct contradiction. However, the shared current Core summary remains implementation-facing and can be misread as host-language `round()` or as omitting Cleave FLOOR/actual-loss mapping.

Required pre-Stage9 fix: semantic-preserving normalization only. Replace generic shorthand with explicit call-site rules, or mark these lines as non-authoritative summaries with direct mechanism-P0 references. No gameplay semantic change.

### `FA-D01` — DOC_ONLY — COMBO §9 retains stale RF-P02-era open-status banner

Location:

```text
states/functional/combo/MECHANISM_CONTRACT.md §9
STATUS: OPEN — CBS9-B03
```

The same current P0 later correctly states in §26:

```text
CBS9-B03 = CLOSED (Frozen via RF-P04)
```

Therefore behavior is not ambiguous, but current-facing status presentation is stale.

Required pre-Stage9 fix: mark §9 banner `HISTORICAL / SUPERSEDED BY §26 RF-P04` or update it to closed while retaining provenance.

No BLOCKER or MAJOR finding was found.

## 26. Final Gate

Fresh final-audit counts:

```text
BLOCKER = 0
MAJOR = 0
MINOR = 2
DOC_ONLY = 1
RESEARCH_DEBT = 1

P0_CONFLICT = 0
RUNTIME_AMBIGUITY = 0
REACHABLE_UNSPECIFIED_BRANCH = 0
AUTHORITY_DUPLICATION_CONFLICT = 0

RF-C01_INVARIANT_CONFLICT = 0
RF-C01_INVARIANT_UNDER_SPECIFIED = 0
RF-C01_REGRESSION_CONFLICT = 0
RF-C01_MISSING_MANDATORY_COVERAGE = 0

STAGE8_REOPEN = NO
```

Base PASS safety gate is satisfied for runtime determinism:

```text
BLOCKER = 0
MAJOR = 0
P0 direct conflict = 0
Runtime ambiguity = 0
Reachable unspecified branch = 0
Authority duplication conflict = 0
Invariant conflict = 0
Regression conflict = 0
Stage8 reopen = NO
```

However the recommended stricter authoring gate is not yet satisfied because one of the two MINOR findings (`FA-M02`) is implementation-facing semantic notation, and `FA-M01` is a misleading supporting repair example.

## 27. Final Verdict

```text
FINAL VERDICT = PASS WITH PRE-STAGE9 FIXES

STAGE9 SPEC AUTHORING ADMISSION = NOT READY
REASON = resolve FA-M01, FA-M02, FA-D01 first; then perform a narrow delta audit
```

No `STAGE9.md` was created.

Recommended next action is a narrow semantic-preserving pre-Stage9 cleanup package. It must not reopen Stage8 or change the frozen gameplay rules. After those three non-blocking fixes are applied, re-run only the affected documentation/authority/integerization delta checks; if no new finding appears, Stage9 implementation specification authoring can be admitted.
