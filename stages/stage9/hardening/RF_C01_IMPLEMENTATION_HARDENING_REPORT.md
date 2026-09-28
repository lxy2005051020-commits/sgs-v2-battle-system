# RF-C01 Implementation Hardening Report

Package: `RF-C01 — IMPLEMENTATION_HARDENING`

Final Verdict: **RF-C01 CLOSED**

This package performs the first engineering-contract hardening after the Stage9 architecture-level P0 repair packages. It does not research new mechanics, rescan battle reports, change Frozen semantic outcomes, implement Stage9 production features, or execute RF-C02 documentation/navigation cleanup.

---

## Repository Baseline

### Battle repository

```text
Repository: lxy2005051020-commits/sgs-v2-battle-system
Branch: main
RF-C01 write baseline exact remote main:
41ad2ac05c2a4b81bc4d2b0af1cadc6cd2508407

Baseline commit:
repair(stage9): freeze battle finalization barrier contract

Baseline tree:
fcd5db81c47b19b737c48018b0fc4d25ae817149

Actual parent of 41ad2ac...:
77693176288d2a5ce54e87b6e1fb46e9b09d2d42
```

### State-mechanics research repository

```text
Repository: lxy2005051020-commits/sgs-state-mechanics-research
Branch: main
RF-C01 read baseline exact remote main:
566dceec9780102c0f2774f77feacece0963e6af

Baseline commit:
docs(finalization): freeze combo and cleave battle finalization barriers
```

The state repository is read-only in RF-C01.

### RF-P04 metadata drift check

The prior reported value:

```text
77693170795b...
```

does not match the real battle commit graph. The actual parent of `41ad2ac...` is:

```text
77693176288d2a5ce54e87b6e1fb46e9b09d2d42
```

The tracked file:

```text
stages/stage9/repairs/RF_P04_BATTLE_FINALIZATION_BARRIER_REFREEZE.md
```

was searched for the bad SHA and for the `776931` parent string. The erroneous `77693170795b...` value is **not present in the tracked RF-P04 repair file**, and repository search found no tracked occurrence requiring correction.

Disposition:

```text
DOC/METADATA DRIFT CONFIRMED IN PRIOR REPORTING
TRACKED RF-P04 FILE CORRECTION REQUIRED = NO
SEPARATE METADATA COMMIT = NO
RF-P04 SEMANTIC CONTRACT MODIFIED = NO
```

---

## P0 Read Set

RF-C01 did not infer finding meanings from IDs. The original independent audits were re-read for the exact finding text:

```text
TAUNT_CONTRACT_AUDIT.md
GUARD_CONTRACT_AUDIT.md
COMBO_CONTRACT_AUDIT.md
CLEAVE_CONTRACT_AUDIT.md
CHAIN_LINK_CONTRACT_AUDIT.md
DAMAGE_SHARE_CONTRACT_AUDIT.md
DISTRIBUTION_CONTRACT_AUDIT.md
COUNTERATTACK_CONTRACT_AUDIT.md
STAGE9_OPEN_FINDING_CONSOLIDATION.md
```

The repaired Frozen authority was then re-read from:

```text
RF_P01_STAGE9_INTEGERIZATION_REFREEZE.md
RF_P02_NORMAL_ATTACK_LIFECYCLE_AND_COMBO_REFREEZE.md
RF_P03_EXECUTION_RIGHT_AND_DEATH_SCOPE_REFREEZE.md
RF_P04_BATTLE_FINALIZATION_BARRIER_REFREEZE.md
RF_P05_PARTITION_TRANSACTION_DEATH_REFREEZE.md
RF_P06_CLEAVE_DAMAGE_LAYER_AND_RECOVERY_BASIS_REFREEZE.md
RF_P07_CLEAVE_STATE_AND_SECONDARY_TARGET_REFREEZE.md
```

Later repair packages supersede an earlier audit expectation only where the repair package explicitly re-froze that boundary. Historical finding IDs are retained.

---

## Finding Ledger

Full ledger: `RF_C01_HARDENING_LEDGER.md`.

| Finding | Final disposition | Closure authority |
|---|---|---|
| `SHS9-N01` | `CLOSED BY RUNTIME CONTRACT` | DamagePartition replacement state + no-resurrection invariant |
| `TAS9-H01` | `CLOSED BY RUNTIME CONTRACT` | RF-P03 reachable-death re-freeze + regression preventing dead actor #2 target pass |
| `GDS9-H01` | `CLOSED BY RUNTIME CONTRACT` | typed TargetResolutionResult + one-pass Guard |
| `CBS9-H01` | `CLOSED BY RUNTIME CONTRACT` | RF-P02/RF-P03/RF-P04 + scoped admission/liveness/finalization model |
| `CLVS9-H01` | `CLOSED BY RUNTIME CONTRACT` | typed DerivedDamageRequest + permission policy |
| `CHNS9-H01` | `CLOSED BY RUNTIME CONTRACT` | typed one-pass traversal + snapshot/live split + restricted settlement |
| `SHS9-H01` | `CLOSED BY RUNTIME CONTRACT` | one effective DamagePartitionResolver |
| `SHS9-H02` | `CLOSED BY RUNTIME CONTRACT` | typed AttributedDirectTroopLoss |
| `DSTS9-H01` | `CLOSED BY RUNTIME CONTRACT` | immutable DistributionTransactionPlan |
| `CTS9-H01` | `CLOSED BY RUNTIME CONTRACT` | immutable trigger-time admission + execution-time owner liveness |
| `CTS9-H02` | `CLOSED BY RUNTIME CONTRACT` | RF-P04 + CounterBatch/finalization regression |
| `CTS9-H03` | `CLOSED BY RUNTIME CONTRACT` | explicit Counter zero-loss terminal path |

```text
RF-C01 finding total = 12
OPEN after RF-C01     = 0
```

---

## Target Identity

Final typed model:

```text
SelectedTarget
IntendedAttackTarget       // pre_redirect_target
PostRedirectActualTarget   // after Guard
DamageRecipient            // per DamageEvent/settlement
```

`TargetResolutionResult` owns the first three identities and redirect provenance. A concrete DamageEvent/settlement owns `DamageRecipient`.

Frozen ordering:

```text
NormalAttack permission
→ CONFUSION / TAUNT / default selector arbitration
→ IntendedAttackTarget
→ exactly one Guard pass
→ PostRedirectActualTarget
→ Target Lock
```

Downstream target-bound nodes consume the post-Guard actual target. A single mutable `targetId` whose meaning changes by overwrite is forbidden.

---

## Combo Runtime State

Final runtime model separates:

```text
ComboStateInstance
→ physical instance / source / metadata / duration

ComboActionGrant
→ current Action permission already granted
→ provenance locked
→ VALID / REVOKED_BY_PHYSICAL_REMOVE / CONSUMED

ComboCheckpointState
→ NOT_REACHED / REACHED / CONSUMED / BLOCKED
```

Required Action invariants:

```text
cfg230 <= 1
Combo opportunity consumed <= 1
physical NormalAttack count <= 2
```

RF-P03 supersedes the historical dead-actor continuation expectation: a dead actor during #1 does not reach #2 fresh target resolution in the frozen reachable execution model.

---

## Derived Damage

Cleave uses a typed `DerivedDamageRequest<CLEAVE>` or equivalent with at least:

```text
sourceType = CLEAVE
damageType = inherited
baseFact = ActualTargetTroopLoss
baseAmount = ActualTargetTroopLoss
ratio = CleaveRatio
integerization = FLOOR
normalAttackIdentity = false
root/parent operation lineage
secondaryTarget
permissionPolicy
```

Forbidden re-entry:

```text
base weapon formula
base strategy formula
secondary target generic damage-modifier recalculation
Crit reroll
Counter via NormalAttack identity
recursive Cleave
```

Allowed downstream according to Frozen P0:

```text
Evasion
Resistance
Share / Distribution partition
FirstAid
Chain
eligible Recovery
```

---

## Direct Troop Loss

Share sharer loss and Distribution participant loss are represented as typed `AttributedDirectTroopLoss`, not DamageEvent.

Minimum fields:

```text
physicalAttacker
physicalSkill
victim
creditOwner
sourceType
parentDamageInstanceId / lineage
theoreticalLoss
actualLoss
```

No `DamageType` is fabricated where P0 does not define one.

Allowed:

```text
troop mutation
death fact
wounded/statistics/kill attribution
```

Forbidden normal Hit Pipeline re-entry:

```text
Defense
DamageReduction
Evasion
Resistance
FirstAid
Counter
Chain
Share
Distribution
generic Hurt callback
base damage formula
```

---

## Chain Snapshot/Live

`ChainDeferredWork` is partitioned into:

```text
immutableTriggerSnapshot
- parent DamageInstance identity
- trigger node identity
- triggerDamage
- trigger provenance

liveExecutionLookup
- trigger/source liveness
- current Chain state
- current owner
- current ratio/effect metadata
- current candidate alive/linked state
```

Frozen distinction:

```text
triggerDamage fixed
but owner / ratio / Chain state / source liveness / candidate eligibility are live-read
```

A one-pass `ChainTraversalId` plus visited-slot set prevents revisits while still allowing a later unvisited slot that becomes linked before its turn to participate.

---

## Distribution Plan

`DistributionTransactionPlan` freezes at transaction planning time:

```text
participant identities
ordered participant tuple
N
Dtarget
Dtransfer
Dparticipant
```

Later world changes may only cause a planned step to `SKIP`; they cannot:

```text
change N
change Dparticipant
repartition
redistribute
add a newly eligible participant
```

Commander participant death remains:

```text
Empirical status = UNOBSERVED / OPEN as research fact
Runtime status   = CLOSED BY PROJECT_RUNTIME_DEFAULT
```

The code/spec must label this `PROJECT_RUNTIME_DEFAULT (NOT EMPIRICALLY PROVEN GAME RULE)`.

---

## Counter Admission/Liveness

Final split:

```text
Trigger-time admission lock
→ freeze CounterBatchEntry identity/source/sourceSkill/damageRate/order

Execution-time local liveness
→ read owner alive / target alive / live combat context
```

After admission:

```text
state suppression/removal/expiry
→ does NOT revoke admitted entry

owner death before entry begins
→ entry fails local execution gate
```

These are different decisions and may not be collapsed into `if counter_state.exists` or `if was_queued`.

---

## Dead-target Counter zero-loss path

An already-admitted sibling Counter whose target is already dead uses an explicit terminal path:

```text
emit CounterExecute
→ attributed zero troop loss
→ complete entry
```

It must not call the full weapon DamageRequest pipeline and therefore must not run:

```text
weapon base formula
Evasion
Resistance
Share
Distribution
Chain
FirstAid
```

Zero is an explicit result, not an accidental downstream clamp.

---

## Finalization Runtime State

Distinct concepts:

```text
UnitDeathFact
VictoryConditionSatisfied / VictoryConditionLatched
BattleFinalized
```

Final typed state:

```text
BattleTerminationState:
  RUNNING
  VICTORY_LATCHED
  DRAINING_ADMITTED_WORK
  FINALIZED
```

Only the finalization owner may write `FINALIZED`.

---

## Future Admission Gate

A common `can_admit_new_work(...)` contract or equivalent must distinguish:

```text
Current Admitted Operation
vs
FutureBranch
```

After victory latch, deny at least:

```text
next Action
unadmitted Assault
Combo #2
new CounterBatch
new ChainTraversal
unadmitted next CleaveEffect
```

Already-admitted work drains or cancels according to its local Frozen rule. Therefore scattered mechanism-local:

```text
if battle.finished: return
```

is forbidden as semantic authority.

---

## Operation Identity

RF-C01 freezes design-level strong identities for at least:

```text
ActionId
NormalAttackInstanceId
DamageInstanceId
ReactionBatchId
PartitionTransactionId
CleaveEffectId
ChainTraversalId
```

Additional supporting IDs are allowed, such as `TargetResolutionId`, `DirectTroopLossId`, and `CounterBatchEntryId`.

---

## Provenance

Minimum common lineage fields where semantically defined:

```text
rootActionId
parentNormalAttackId
parentDamageInstanceId
sourceType
physicalAttacker
physicalSkill
creditOwner
```

Only semantically real fields are populated. Derived events may not guess parents from strings.

---

## Recursion Guards

Semantic permission derives from:

```text
SourceType
NormalAttackIdentity
OperationLineage
explicit permission policy
```

Examples:

```text
Cleave → Counter = BLOCKED
Cleave → Cleave = BLOCKED
Counter → Counter = BLOCKED
Chain → Chain = BLOCKED
Share direct loss → hit callbacks = BLOCKED
Distribution direct loss → hit callbacks = BLOCKED
```

Forbidden authority patterns:

```text
skill-name string switches
if already_in_counter_function
reaction-depth-only recursion guards
scattered battle.finished checks
```

---

## Runtime Invariants

`STAGE9_RUNTIME_INVARIANTS.md` freezes:

```text
Runtime Invariant Count = 42
Runtime invariant ambiguity = 0
```

Major groups:

```text
Target Identity
Combo Runtime State
Cleave Derived Damage
Direct Troop Loss / Partition Identity
Damage Share
Distribution Fixed Plan
Chain Snapshot / Live
Counter Admission / Execution
Victory / Finalization
Operation Identity / Recursion
```

---

## Regression Contracts

`STAGE9_REGRESSION_CONTRACTS.md` freezes:

```text
Regression Contract Count = 45
```

Coverage:

```text
Target Arbitration = 7
Combo              = 5
Cleave             = 5
Chain              = 4
Share              = 4
Distribution       = 4
Counter            = 5
Finalization       = 6
Integerization     = 5
```

Mandatory RF-P04 cases are present verbatim by ID:

```text
FINAL_01_CHAIN_COMMANDER_DEATH
FINAL_02_COUNTER_SIBLING
FINAL_03_COMBO_BATTLE_END
FINAL_04_CLEAVE_COMMANDER_SECONDARY
FINAL_05_SHARE_COMMANDER_TARGET
FINAL_06_DISTRIBUTION_COMMANDER_PARTICIPANT
```

The final Distribution case is explicitly marked `PROJECT_RUNTIME_DEFAULT`.

Integerization expectations are explicit numeric vectors and do not use host-language built-in `round()` as oracle.

---

## Stage8 Compatibility

```text
Stage8 = FROZEN
Formal Stage8 Reopen = NO
Stage1-8 production behavior changed = NO
```

Stage9 build should use wrappers/coordinators/extension seams rather than adding a row of Stage9 mechanism booleans to Stage8 `DamageRequest`.

---

## Remaining Findings

```text
RF-C01 scoped finding count = 12
CLOSED BY RUNTIME CONTRACT  = 12
REMAINS OPEN                = 0
P0 CONFLICT DISCOVERED      = 0
Runtime invariant ambiguity = 0
Typed contract ambiguity    = 0
```

Research truth for `DSTS9-B02` remains explicitly dual-status and is not falsified:

```text
Empirical = UNOBSERVED / OPEN
Runtime = CLOSED BY ENGINEERING DEFAULT
```

That does not constitute an RF-C01 runtime ambiguity.

---

## Changed Files

RF-C01 changes battle repository documentation only:

```text
stages/stage9/hardening/RF_C01_HARDENING_LEDGER.md
stages/stage9/hardening/STAGE9_TYPED_RUNTIME_CONTRACTS.md
stages/stage9/hardening/STAGE9_RUNTIME_INVARIANTS.md
stages/stage9/hardening/STAGE9_REGRESSION_CONTRACTS.md
stages/stage9/hardening/RF_C01_IMPLEMENTATION_HARDENING_REPORT.md
```

Not changed:

```text
production source code
production tests
Stage8 contracts
state-mechanics research repository
README
STATE_MECHANICS_INDEX
Evidence Matrix
minimum-usable navigation
```

The last four are RF-C02 scope and are deliberately untouched.

---

## Commit

Intended atomic commit message:

```text
hardening(stage9): freeze runtime invariants and regression contracts
```

The exact Git commit SHA is intentionally not self-embedded in this file because a Git commit cannot contain its own final hash without changing that hash. The final execution report and repository history identify the exact commit object containing this report.

No separate metadata-only correction commit is required because the incorrect RF-P04 parent SHA is absent from the tracked RF-P04 file.

---

## Final Verdict

```text
HARDENING finding OPEN       = 0
Runtime invariant ambiguity  = 0
Typed contract ambiguity     = 0
P0 conflict introduced       = 0
Stage8 reopen                = NO
Production code changed      = NO
RF-C02 executed              = NO

RF-C01 CLOSED
```

Next package after this closure is:

```text
RF-C02
```

RF-C02 is **not** executed by this package.
