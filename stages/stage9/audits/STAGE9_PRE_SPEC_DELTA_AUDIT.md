# Stage9 Pre-Spec Delta Audit

> Date: 2026-09-13  
> Audit type: NARROW DELTA AUDIT  
> Scope: `FA-M01`, `FA-M02`, `FA-D01` and their direct authority edges only  
> Full Global Final Audit rerun: NO  
> Battle-report corpus scan: NO  
> 42-invariant full rescan: NO  
> 45-regression full rescan: NO  
> Recursion Matrix full rescan: NO  
> Nine-mechanism P0 rescan: NO  
> `DSTS9-B02` research: NOT REOPENED  
> `STAGE9.md` created: NO

---

## Baseline

### Battle repository pre-cleanup

```text
Repository: lxy2005051020-commits/sgs-v2-battle-system
remote main:
1212de3aa2f4b25c4e89a66433d35307b28849c6
audit(stage9): complete global cross-mechanism final audit
```

### State-mechanics repository pre-cleanup

```text
Repository: lxy2005051020-commits/sgs-state-mechanics-research
remote main:
033a0314a101b17222d7cefa79dbf178b8eaca9f
docs(stage9): sync mechanism status and authority navigation
```

The historical `STAGE9_GLOBAL_CROSS_MECHANISM_FINAL_AUDIT.md` body is intentionally unchanged. Its `PASS WITH PRE-STAGE9 FIXES` verdict remains a historical audit result, not a current post-cleanup verdict.

---

## Cleanup Commits

```text
Battle cleanup:
b4c6e7d5c18f342831c887a0ac50465be24b6748
cleanup(stage9): resolve pre-spec final-audit findings

State cleanup:
15ed915435f328a6ecd8f488d98b5b9e13c913b5
docs(combo): close stale CBS9-B03 status banner
```

Battle cleanup scope:

```text
MODIFIED  stages/stage9/repairs/RF_P06_CLEAVE_DAMAGE_LAYER_AND_RECOVERY_BASIS_REFREEZE.md
MODIFIED  stages/stage9/research/core_arbitration_v2/STAGE9_CORE_ARBITRATION_RULES_V2.md
ADDED     stages/stage9/audits/STAGE9_PRE_SPEC_CLEANUP_RECORD.md
```

State cleanup scope:

```text
MODIFIED  states/functional/combo/MECHANISM_CONTRACT.md
```

---

## FA-M01 Delta Check

### Delta under review

RF-P06 §6 malformed supporting example was removed and replaced by an already archived valid sample:

```text
battle id = 战报_2235624_pid2306204.json
ActualTargetTroopLoss = 635
CleaveRatio = 54%
exact product = 342.90
FLOOR(342.90) = 342
observed Cleave = 342
```

No new report scan or mechanism inference was performed.

### Direct authority edges checked

1. `STAGE9_CLEAVE_MECHANICS_FREEZE_RECORD.md`

```text
Cleave base = ActualTargetTroopLoss
CleaveDerivedCalculatedDamage = floor(ActualTargetTroopLoss × CleaveRatio)
```

2. `STAGE9_RUNTIME_INVARIANTS.md` — only direct invariant edge inspected:

```text
INV-14: Cleave base fact is ActualTargetTroopLoss
INV-15: Cleave integerization is FLOOR
```

3. `STAGE9_REGRESSION_CONTRACTS.md` — only direct regression edges inspected:

```text
REG-CLV-01:
ActualTargetTroopLoss=55, ratio=54%
→ floor(55×0.54)=29

REG-INT-05:
ActualTargetTroopLoss=55, ratio=54%
→ 55×0.54=29.7 → 29
```

4. RF-P06 repaired text now agrees with the above authority set.

### Malformed-proof search

Current battle `main` searches for the malformed current-facing proof returned no matches for:

```text
475 × 0.62
294.5
floor(294.5)
observed Cleave = 295
战报_1105099_pid1100193
```

The archived evidence JSON was not edited.

### Verdict

```text
FA-M01 = CLOSED
Cleave base agreement = YES
Cleave FLOOR agreement = YES
Gameplay semantic change = NO
```

---

## FA-M02 Delta Check

### Delta under review

Core Arbitration numeric summary was made call-site explicit without changing mechanism ownership.

### Direct authority edges checked

#### Share

Core now states:

```text
Dsharer = ROUND_HALF_UP(Dtotal × ShareRatio)
Dtarget = Dtotal - Dsharer
```

Share P0 states the same rule with `round_half_up` and target-as-remainder semantics.

#### Distribution

Core now states:

```text
Dtarget = ROUND_HALF_UP(Dtotal × (1 - DistributionRatio))
Dtransfer = Dtotal - Dtarget
Dparticipant = ROUND_HALF_UP(Dtransfer / N)
```

Distribution P0 states the same two `ROUND_HALF_UP` call sites.

#### Cleave

Core now states:

```text
CleaveDerivedCalculatedDamage
= FLOOR(
    ActualTargetTroopLoss
    × CleaveRatio
  )
```

Cleave P0 and RF-P06 state the same base and integerization rule.

#### Chain

Core now states:

```text
ChainCalculatedDamage
= FLOOR(
    TriggerNodeResolvedDamage
    × CurrentChainRatio
  )
```

Chain P0 states `FLOOR(TriggerNodeResolvedDamage × ChainRatio)`.

#### Integerization Matrix / RF-P01

RF-P01 explicitly freezes call-site-specific integerization:

```text
CHAIN = FLOOR
SHARE = ROUND_HALF_UP
DISTRIBUTION_TARGET = ROUND_HALF_UP
DISTRIBUTION_PARTICIPANT = ROUND_HALF_UP
```

It also explicitly rejects a monolithic global rounding assumption.

### Ownership check

Core §6 now explicitly identifies itself as an orchestration / summary consumer and names the owning mechanism Freeze Record for Share, Distribution, Cleave, and Chain.

```text
Core semantic ownership expansion = NO
Mechanism P0 ownership retained = YES
```

### Current-facing shorthand search

Repository search was requested for:

```text
round(
MainAttackFinalDamage
final damage
finalDamage
```

The connector code-search surface returned zero indexed results for these terms after cleanup. Because repository indexing/search can be conservative, the decisive current-authority check was also performed directly against the current Core file content:

```text
Core current content: generic `round(` = 0
Core current content: `MainAttackFinalDamage` = 0
```

Relevant historical/mechanism documents may preserve old terminology or before/after examples as provenance. This audit does not rewrite historical records. The admission requirement applies to current Stage9 authority surfaces, where the ambiguous shorthand is now absent.

### Verdict

```text
FA-M02 = CLOSED
generic Stage9 current-authority integerization ambiguity = 0
ambiguous Cleave base shorthand in current Core = 0
ownership conflict introduced = 0
Gameplay semantic change = NO
```

---

## FA-D01 Delta Check

### Delta under review

COMBO §9 stale banner was changed from a current-looking OPEN status to a provenance-preserving historical note:

```text
HISTORICAL STATUS NOTE
CBS9-B03 was OPEN at RF-P02 time.
Superseded by RF-P04.
Current status: CLOSED.
See §26.
```

### Direct authority edges checked

1. COMBO §9 now records historical OPEN provenance and current CLOSED status.
2. COMBO §26 remains:

```text
CBS9-B03 = CLOSED (Frozen via RF-P04)
```

3. `RF_P04_BATTLE_FINALIZATION_BARRIER_REFREEZE.md` states:

```text
CBS9-B03 = CLOSED
```

and freezes the NormalAttack #1 battle-ending barrier behavior.

4. `STAGE9_AUTHORITY_MAP.md` continues to classify COMBO as:

```text
Current status = FROZEN
Runtime ready = YES
P0 = state states/functional/combo/MECHANISM_CONTRACT.md
```

### Provenance check

The RF-P02-era prose below §9 remains preserved as historical context; only the stale current-looking status banner was normalized.

### Verdict

```text
FA-D01 = CLOSED
CBS9-B03 current status = CLOSED
historical provenance preserved = YES
Gameplay semantic change = NO
```

---

## P0 Semantic Change Check

The cleanup delta modifies no mechanism P0 gameplay rule, no runtime contract, no production code, and no test code.

Final cleanup-delta file scope is limited to:

```text
Battle:
- RF_P06_CLEAVE_DAMAGE_LAYER_AND_RECOVERY_BASIS_REFREEZE.md
- STAGE9_CORE_ARBITRATION_RULES_V2.md
- STAGE9_PRE_SPEC_CLEANUP_RECORD.md
- STAGE9_PRE_SPEC_DELTA_AUDIT.md (this report)

State:
- states/functional/combo/MECHANISM_CONTRACT.md (§9 presentation only)
```

```text
P0 semantic change count = 0
Runtime semantic change count = 0
Production code change count = 0
Test code change count = 0
```

---

## Stage8 Boundary

No Stage8 formula ownership, Damage Pipeline contract, or Stage8 Frozen semantic was modified or reopened.

```text
Stage8 = FROZEN
Stage8 reopen = NO
```

---

## Remaining Findings

```text
FA-M01 = CLOSED
FA-M02 = CLOSED
FA-D01 = CLOSED

Remaining blocking findings = 0
Remaining pre-spec findings = 0
```

Research debt remains intentionally unchanged:

```text
DSTS9-B02 = empirical OPEN / UNOBSERVED
Runtime = deterministic explicit project default
Admission impact = NON-BLOCKING
Remaining research debt = DSTS9-B02 only
```

---

## Final Gate

```text
FA-M01 = CLOSED
FA-M02 = CLOSED
FA-D01 = CLOSED

new BLOCKER = 0
new MAJOR = 0
new MINOR = 0
new DOC_ONLY = 0

P0 semantic change = 0
Runtime ambiguity = 0
P0 conflict = 0
Stage8 reopen = NO

Research debt = DSTS9-B02 only (non-blocking)
```

No new reachable unspecified runtime branch was introduced by this documentation-only delta.

---

## Verdict

```text
DELTA VERDICT = PASS

STAGE9 SPEC AUTHORING ADMISSION = READY

Remaining blocking findings = 0
Remaining pre-spec findings = 0
Remaining research debt = DSTS9-B02 only

NEXT STEP:
Stage9 implementation specification authoring
```

`STAGE9.md` is intentionally not created by this cleanup/audit round.
