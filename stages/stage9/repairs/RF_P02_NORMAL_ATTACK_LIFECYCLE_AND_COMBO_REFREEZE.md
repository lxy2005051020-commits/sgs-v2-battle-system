# RF-P02 Repair Record

## NORMAL_ATTACK_LIFECYCLE_AND_COMBO_CONTRACT_REPAIR

```text
Package: RF-P02
Level: B
Priority: P0
Execution Type: CONTRACT-ONLY REPAIR
Need New Extractor: NO
Repair Date: 2026-09-13
Final Verdict: RF-P02 CLOSED
Overall COMBO Status: NARROW REOPEN REMAINS
```

---

## 1. Repository Baseline

Repair start exact `main` refs were re-read immediately before modification.

### Battle repository

```text
Repository:
lxy2005051020-commits/sgs-v2-battle-system

repair-before exact main HEAD:
49aeea81f22ba94cc791eea75f9501b78b484c29

audit(stage9): consolidate open contract findings

repair-before parent:
f8cb7c59de4ce51492915abc84247f677815ea6e

repair-before tree:
26fc81b3622c88acaa908374a27b21ff60d931f2
```

### State-mechanics research repository

```text
Repository:
lxy2005051020-commits/sgs-state-mechanics-research

repair-before exact main HEAD:
9d86e54c407913ff020bafacf8196085780b99c6

docs(index): mark combo frozen and scope death baseline

repair-before parent:
aa556486580548d41768d4dd6c0dc00f4dc3e5f7

repair-before tree:
7b0e34ce9fe7f158fad432eee307021c5aac4eb2
```

No pre-existing `stages/stage9/repairs/` convention was present in the battle repository. This directory is therefore introduced only for the narrow re-freeze package record requested by the Stage9 consolidation plan.

---

## 2. Affected Findings

RF-P02 is strictly limited to:

```text
CBS9-B02
CBS9-M01
CBS9-M02
CBS9-M03
```

Disposition after repair:

```text
CBS9-B02 = CLOSED
CBS9-M01 = CLOSED
CBS9-M02 = CLOSED
CBS9-M03 = CLOSED
```

Explicitly not closed here:

```text
CBS9-B01 = OPEN → RF-P03
CBS9-B03 = OPEN → RF-P04
CFS9-B01 = OPEN / NARROWED → RF-P03
```

All Cleave / Chain / Share / Distribution open findings remain untouched.

---

## 3. Authoritative Source of Truth

The sole authoritative COMBO P0 remains in the state-mechanics research repository:

```text
sgs-state-mechanics-research/
states/functional/combo/MECHANISM_CONTRACT.md
```

RF-P02 authoritative repair commit:

```text
96719f98d11cd5ad60cd3eda568bda8d2e0e790d
docs(combo): re-freeze lifecycle ownership contract
```

Repaired COMBO P0 blob:

```text
5237dd1d4ec4f89023c4543e146bdf09c71d5702
```

The battle repository does **not** create a second competing COMBO P0 mirror in RF-P02. The cross-repository mirror/navigation drift is `CBS9-D01` and belongs to `RF-C02`.

This record is the battle-repository authoritative reference to the repaired state-repository P0 until RF-C02 performs documentation synchronization.

---

## 4. Authority Used

RF-P02 used existing evidence only. No new battle-report scan or extractor was run.

Authority order:

```text
P0 Formal Contract / Freeze Record
>
P1 Freeze Audit
>
Stage9 Core Arbitration V2
>
R1-R8
>
Evidence Matrix
>
README / INDEX
```

Read and reconciled sources include:

```text
stages/stage9/audits/STAGE9_OPEN_FINDING_CONSOLIDATION.md
stages/stage9/audits/COMBO_CONTRACT_AUDIT.md
stages/stage9/audits/COUNTERATTACK_CONTRACT_AUDIT.md
stages/stage9/audits/CLEAVE_CONTRACT_AUDIT.md
stages/stage9/audits/CHAIN_LINK_CONTRACT_AUDIT.md

stages/stage9/research/core_arbitration_v2/STAGE9_CORE_ARBITRATION_RULES_V2.md
stages/stage9/research/core_arbitration_v2/R1_ATTACK_LIFECYCLE_AND_REACTION_ORDER.md
stages/stage9/research/core_arbitration_v2/R7_RNG_AND_DETERMINISM.md
stages/stage9/research/core_arbitration_v2/STAGE9_COUNTERATTACK_MECHANICS_FREEZE_RECORD.md
stages/stage9/research/core_arbitration_v2/STAGE9_CLEAVE_MECHANICS_FREEZE_RECORD.md
stages/stage9/research/core_arbitration_v2/STAGE9_CHAIN_MECHANICS_FREEZE_RECORD.md

sgs-state-mechanics-research/states/functional/combo/MECHANISM_CONTRACT.md
```

---

## 5. Problem

RF-P02 repaired four contract defects without changing production behavior code.

### CBS9-B02

The old COMBO P0 duplicated the full `NORMAL_ATTACK #1` inner lifecycle and froze an incompatible order:

```text
Assault
→ Counter
→ Combo
```

while Core Arbitration and Counter P0 already converged on:

```text
CounterBatch
→ Assault
→ Combo
```

The problem was not merely one bad arrow. Multiple P0 documents were claiming ownership of the same global ordering.

### CBS9-M01

The old recommended COMBO pseudocode did:

```text
read effective Combo
→ latch eligibility
→ ACTION_START lifecycle maintenance
```

which could grant a Combo that should expire at that same `ACTION_START`.

### CBS9-M02

The old latch model did not cleanly separate:

```text
physical state existence
operational state
already-granted Action-local eligibility
```

and omitted the explicit physical-REMOVE invalidation transition supported by existing Combo direct research.

### CBS9-M03

The old COMBO P0 over-froze:

```text
independent uniform random targeting
```

as an official rule even though R7 only supports fresh live reselection and explicitly leaves exact official PRNG internals unknown.

---

## 6. RF_P02_BEFORE_AFTER_MATRIX

| Topic | Before RF-P02 | After RF-P02 |
|---|---|---|
| NormalAttack master lifecycle owner | COMBO §5 duplicated a complete inner sequence while Core/Counter/Cleave/Chain also owned parts of it | **Stage9 Core Arbitration / NormalAttack Orchestrator** owns the master lifecycle; mechanism P0s own insertion/admission/local semantics only |
| Counter vs Assault order | COMBO P0 could be read as Assault → Counter | **CounterBatch → Assault → Combo Checkpoint** on the non-terminated path |
| Combo Checkpoint ownership | COMBO owned both parent inner lifecycle and checkpoint | COMBO owns only checkpoint-after-authoritative-parent-resolution plus its own grant/consume/#2 admission semantics |
| ACTION_START maintenance | recommended pseudocode latched before maintenance | maintenance/expiry/removal/suppression state settles **before** effective Combo read and grant |
| eligibility latch | single broad boolean model | physical existence, operational state, and Action-local grant are separate concepts |
| physical REMOVE | no explicit pending-grant invalidation in runtime model | before grant: cannot grant; after grant but before consume: removed granting instance invalidates its pending unconsumed grant |
| SUPPRESS | conceptually distinct from REMOVE but incompletely modeled | suppressed at entry: no grant; suppression after a valid grant does not retroactively revoke that current-Action grant |
| already-granted eligibility | easily conflated with “#2 definitely executes” | valid grant only owns a pending opportunity; checkpoint/consume/can_normal_attack/fresh target resolution still decide actual #2 dispatch |
| #2 target resolution | “independent uniformly random” | **fresh live standard NormalAttack Target Resolution**; no inherited #1 target or Guard result |
| official PRNG claim | uniform i.i.d. language could be read as official implementation fact | exact official uniformity, PRNG algorithm, seed advancement and call count are **UNKNOWN / NOT FROZEN**; simulator uses project RandomSystem when randomness is required |

---

## 7. Repaired NormalAttack Ownership Contract

The master lifecycle already present in `STAGE9_CORE_ARBITRATION_RULES_V2.md` remains the global ordering source. RF-P02 does not rewrite that file because its existing master order is already compatible with Counter/Cleave/Chain P0 and the repair is accomplished by removing COMBO's competing ownership claim.

Ownership after RF-P02:

```text
Stage9 Core Arbitration / NormalAttack Orchestrator
→ master NormalAttack lifecycle owner

CONFUSION / TAUNT
→ selector arbitration semantics

GUARD
→ redirect semantics

CLEAVE
→ Cleave admission / derived-damage local semantics

CHAIN
→ Chain qualification / inline-deferred local semantics

COUNTERATTACK
→ CounterBatch admission / execution local semantics

ASSAULT
→ Assault insertion / local semantics

COMBO
→ Action-local grant + Combo Checkpoint + atomic consume + #2 admission
```

Master shape relevant to RF-P02:

```text
NormalAttack permission
↓
fresh target resolution
↓
CONFUSION / TAUNT selector arbitration
↓
GUARD redirect
↓
Target Lock
↓
main NormalAttack damage
↓
defender death check
↓
immediate allowed hit reactions such as FirstAid
↓
Cleave phase if present
    ↓
    each Cleave target
    ↓
    Cleave damage
    ↓
    eligible target Chain INLINE
↓
main-target Deferred Chain if applicable
↓
CounterBatch
↓
if the authoritative lifecycle still permits the attacker branch:
    Assault
↓
if the authoritative lifecycle still permits Combo branch creation:
    Combo Checkpoint
```

No Cleave case:

```text
main-target Chain INLINE
→ CounterBatch
```

RF-P02 does not create a universal death rule around the two conditional branches above. Their death-family semantics remain RF-P03 scope.

---

## 8. Combo Checkpoint Ownership

COMBO now owns only this parent boundary:

```text
NORMAL_ATTACK #1
→ resolve under authoritative Stage9 NormalAttack lifecycle
→ complete all synchronous work that the master lifecycle places before Combo Checkpoint
→ Combo Checkpoint
```

COMBO does not own or replicate the exact inner order of:

```text
FirstAid
Cleave
Chain
Counter
Assault
```

This closes `CBS9-B02` without weakening the stronger owning P0s.

---

## 9. ACTION_START / Latch Semantics

RF-P02 freezes the COMBO entry read order as:

```text
cfg175 ACTION_START
1. lifecycle maintenance / expiration
2. physical removals caused by maintenance
3. operational suppression / restoration state visible at entry
4. read currently effective Combo
5. grant Action-local eligibility if effective
6. lock source provenance
7. continue Action
```

Therefore:

```text
Combo expires at this ACTION_START
→ physically removed before Combo read
→ no grant for this Action
```

This closes `CBS9-M01`.

---

## 10. REMOVE / SUPPRESS / Granted Eligibility

RF-P02 requires three separate state dimensions at minimum:

```text
physical instance exists
operational now
action-local grant exists
```

### Physical REMOVE

Before grant:

```text
REMOVE
→ no physical instance
→ cannot grant
```

After grant but before atomic consume:

```text
Grant from instance X
→ physical REMOVE X
→ pending grant from X invalidated
→ no cfg230 from X
```

This direction is supported by existing Combo direct research `Q10` / `Q41`; no new battle-report extraction was required.

### SUPPRESS

Before grant:

```text
physical exists + operational false
→ no grant
```

After grant:

```text
GRANTED
→ later ordinary SUPPRESS
→ current Action grant not retroactively revoked
```

Next Action re-evaluates the live operational state after that Action's lifecycle maintenance.

### Granted eligibility

A valid grant means only:

```text
this Action owns a pending Combo opportunity
```

It does not guarantee #2. The actual path remains:

```text
valid grant
→ Combo Checkpoint
→ atomic consume
→ cfg230
→ can_normal_attack()
→ fresh live target resolution
→ possible cfg9 #2
```

This closes `CBS9-M02`.

---

## 11. Target / RNG Scope

RF-P02 keeps the observable target contract:

```text
#2 = fresh NormalAttackInstance
#2 performs fresh live Target Resolution
#2 does not inherit #1 resolved target
#2 does not inherit #1 Guard result
#2 reads current target legality at dispatch time
```

The following claims were removed as official facts:

```text
official target selection is proven uniform
official #1/#2 selection is proven i.i.d.
official target selection consumes exactly one PRNG call
official PRNG seed/state advancement is known
official PRNG algorithm is known
```

Project implementation remains deterministic by using the existing `TargetSystem / RandomSystem` contract whenever target resolution actually requires randomness.

This closes `CBS9-M03`.

---

## 12. Atomic Combo Consumption — Unchanged Stable Core

RF-P02 does not change:

```text
Combo Checkpoint
→ valid grant && !consumed
→ atomic consume
→ cfg230
→ can_normal_attack()
→ fresh target resolution
→ optional cfg9 #2
```

After `cfg230`, a Disarm / Stun / no-target failure does not refund or retry the opportunity.

---

## 13. Stable Core Preserved

The following remain unchanged:

```text
COMBO = independent second standard NormalAttack
maximum physical NormalAttack count per Action = 2
Combo Checkpoint at most once per eligible Action
cfg230 per Action <= 1
#2 is a fresh NormalAttackInstance
#2 reruns target selection
#2 reruns Guard
#2 can independently trigger Cleave / Counter / Chain / Assault
Cleave does not create Combo Checkpoint
Counter does not create Combo Checkpoint
single Combo status slot
same-slot First-In-Wins
source provenance lock
atomic Combo opportunity consumption
```

Stage8 remains `FROZEN`; RF-P02 changes no Stage8 contract, production code, formula or test implementation.

---

## 14. Cross-Contract Verification

### COMBO × COUNTER

```text
Counter P0 master-relative constraint:
CounterBatch before Assault before Combo

RF-P02 COMBO:
delegates parent lifecycle to Core
→ CONSISTENT
```

Counter-kill death semantics remain `CBS9-B01 / RF-P03`; RF-P02 does not claim full death-family closure.

### COMBO × CLEAVE

```text
#1 and #2 are each standard NormalAttack instances
→ each may independently enter Cleave if eligible
Cleave itself is derived damage
→ no Combo Checkpoint
```

RF-P02 does not change Cleave's open `CLVS9-*` findings.

### COMBO × CHAIN

```text
#1 Chain work completes at the positions owned by Chain/Core
→ Combo waits until parent pre-checkpoint lifecycle completes
#2 gets its own independent Chain interaction
Chain feedback itself does not create Combo Checkpoint
```

RF-P02 does not change `CHNS9-B01`.

### COMBO × TAUNT

```text
#2 re-enters fresh live Target Resolution
→ current Taunt selector state is re-read
→ no inherited #1 target
```

No new conflict introduced.

### COMBO × GUARD

```text
#2 re-enters standard NormalAttack Target Resolution
→ Guard is re-evaluated live
→ #1 originalTarget / actualTarget / Guard result are not inherited
```

No new conflict introduced.

---

## 15. Remaining Open Findings

RF-P02 deliberately leaves:

```text
CBS9-B01 = OPEN
COMBO death-family execution-right semantics
→ RF-P03

CBS9-B03 = OPEN
Victory / no-target / Battle Finalization barrier
→ RF-P04

CFS9-B01 = OPEN / NARROWED
Counter-kill subcase is no longer a viable dead-actor later-selection path,
but residual non-Counter death families still require RF-P03 classification.
```

Therefore:

```text
RF-P02 = CLOSED
COMBO FULLY RE-FROZEN = NO
COMBO NARROW REOPEN REMAINS = YES
```

---

## 16. Regression Requirements — TEST SPEC ONLY

No production test code is changed in RF-P02. Future implementation tests must cover at least:

```text
1. expired Combo at ACTION_START
   → no eligibility grant

2. active operational Combo after maintenance
   → eligibility granted

3. SUPPRESS before Action entry read
   → no eligibility

4. eligibility granted
   → later SUPPRESS does not retroactively revoke current Action

5. physical REMOVE before eligibility acquisition
   → no eligibility

6. granted instance physically removed before Combo Checkpoint
   → pending grant invalidated
   → no cfg230 from removed instance

7. NormalAttack #1 authoritative path
   → CounterBatch
   → Assault
   → Combo Checkpoint
   where later nodes are not cancelled by their owning termination rules

8. #2
   → fresh target resolution

9. #2
   → no inherited Guard result

10. cfg230
    → #2 blocked
    → opportunity still consumed
    → no retry

11. no #3
```

These are `TEST SPEC ONLY` in RF-P02.

---

## 17. Changed Files

### State research repository

```text
MODIFIED
states/functional/combo/MECHANISM_CONTRACT.md
```

Purpose:

```text
formal RF-P02 re-freeze of authoritative COMBO P0
```

### Battle repository

```text
ADDED
stages/stage9/repairs/RF_P02_NORMAL_ATTACK_LIFECYCLE_AND_COMBO_REFREEZE.md
```

`STAGE9_CORE_ARBITRATION_RULES_V2.md` was intentionally **not modified** because its existing §3 master lifecycle already has the correct Core-owned ordering:

```text
Cleave / Chain
→ CounterBatch
→ Assault
→ Combo
```

The defect was the competing exact sequence in COMBO P0, not the Core ordering itself. Avoiding a no-op Core rewrite keeps this package narrow and prevents accidental edits to damage/death/share/distribution semantics.

Not modified:

```text
production code
tests
Stage8
CONFUSION P0
TAUNT P0
GUARD P0
CLEAVE P0
CHAIN P0
SHARE P0
DISTRIBUTION P0
COUNTER P0
README
STATE_MECHANICS_INDEX
STAGE9_EVIDENCE_MATRIX_V2
STAGE9.md
```

---

## 18. Commits

State research re-freeze commit:

```text
96719f98d11cd5ad60cd3eda568bda8d2e0e790d
docs(combo): re-freeze lifecycle ownership contract
parent = 9d86e54c407913ff020bafacf8196085780b99c6
```

Battle repair record is committed by the commit containing this file; its exact SHA is verified from remote `main` after write and reported in the final RF-P02 verification output. A commit cannot truthfully embed its own future SHA without manufacturing a second bookkeeping commit, so no self-referential hash is invented here. Humans have already invented enough cyclic dependencies.

---

## 19. Finding Closure

### CBS9-B02 — CLOSED

Closure condition satisfied:

```text
COMBO no longer owns NORMAL_ATTACK #1 inner lifecycle.
Core Arbitration / NormalAttack Orchestrator owns master order.
CounterBatch before Assault before Combo Checkpoint.
```

### CBS9-M01 — CLOSED

Closure condition satisfied:

```text
ACTION_START maintenance / expiry / physical removal
occurs before effective Combo read and grant.
```

### CBS9-M02 — CLOSED

Closure condition satisfied:

```text
physical existence
operational status
action-local granted eligibility
```

are separate concepts, with explicit physical-REMOVE invalidation and non-retroactive SUPPRESS semantics.

### CBS9-M03 — CLOSED

Closure condition satisfied:

```text
fresh live target resolution remains FROZEN.
exact official uniform iid / PRNG implementation claims are removed.
```

---

## 20. Final Verdict

# RF-P02 CLOSED

No new evidence gap was found. Existing P0 / Audit / R1 / R7 / Combo direct research was sufficient, exactly as the consolidation predicted.

Final ownership model:

```text
Core Arbitration / NormalAttack Orchestrator
→ owns NormalAttack master lifecycle

Counter P0
→ owns CounterBatch semantics

Assault mechanism
→ owns Assault local insertion behavior

COMBO P0
→ owns Combo grant / source lock / checkpoint / atomic consume / #2 admission
```

Final relative order relevant to this package:

```text
CounterBatch
→ Assault
→ Combo Checkpoint
```

Open after RF-P02:

```text
CBS9-B01 = OPEN
CBS9-B03 = OPEN
CFS9-B01 = OPEN / NARROWED
```

```text
Stage8 = FROZEN
Formal Stage8 Reopen = NO
```

Per `STAGE9_OPEN_FINDING_CONSOLIDATION.md`, the next repair package after RF-P02 is:

```text
RF-P01 — numeric boundary research / re-freeze
```

RF-P01 is **not executed** by this package.
