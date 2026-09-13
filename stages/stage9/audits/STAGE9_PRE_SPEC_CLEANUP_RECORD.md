# Stage9 Pre-Spec Cleanup Record

> Date: 2026-09-13  
> Scope: `FA-M01`, `FA-M02`, `FA-D01` only  
> Cleanup type: semantic-preserving documentation cleanup  
> New mechanism research: NO  
> Battle-report corpus rescan: NO  
> Production code change: NO  
> Test code change: NO  
> `STAGE9.md` created: NO

---

## Baseline

### Battle repository

```text
Repository: lxy2005051020-commits/sgs-v2-battle-system
pre-cleanup remote main:
1212de3aa2f4b25c4e89a66433d35307b28849c6
```

### State-mechanics repository

```text
Repository: lxy2005051020-commits/sgs-state-mechanics-research
pre-cleanup remote main:
033a0314a101b17222d7cefa79dbf178b8eaca9f

state cleanup commit:
15ed915435f328a6ecd8f488d98b5b9e13c913b5
docs(combo): close stale CBS9-B03 status banner
```

The historical Global Final Audit body is intentionally unchanged. Its original `PASS WITH PRE-STAGE9 FIXES` verdict remains the truthful record of the audit at that time.

---

## FA-M01 — RF-P06 malformed supporting example

### Original finding

`stages/stage9/repairs/RF_P06_CLEAVE_DAMAGE_LAYER_AND_RECOVERY_BASIS_REFREEZE.md` §6 contained a malformed second supporting example for `战报_1105099_pid1100193.json`:

```text
Dtarget = 475
CleaveRatio = 62%
475 × 0.62 = 294.5
observed Cleave = 295
floor(294.5) → 295
```

This was internally invalid because `FLOOR(294.5) = 294`, and the archived evidence for that battle did not match the prose's ratio / observed value pair.

### Exact cleanup

The malformed non-authoritative example was removed from the current-facing proof section and replaced only with an already archived valid sample from `CLEAVE_DAMAGE_LAYER_EVIDENCE.json`:

```text
battle id = 战报_2235624_pid2306204.json
ActualTargetTroopLoss = 635
CleaveRatio = 54%
exact product = 342.90
FLOOR(342.90) = 342
observed Cleave = 342
```

No historical evidence JSON was edited, no new battle report was scanned, and no new Cleave inference was performed.

### Semantic outcome

Before cleanup:

```text
Frozen rule = CleaveBase is ActualTargetTroopLoss
Frozen integerization = FLOOR
Supporting prose contained one malformed non-authoritative example
```

After cleanup:

```text
Frozen rule = CleaveBase is ActualTargetTroopLoss
Frozen integerization = FLOOR
Supporting prose now uses an archived exact-match example
```

```text
Gameplay semantic change = NO
```

---

## FA-M02 — Core Arbitration shorthand normalization

### Original finding

`stages/stage9/research/core_arbitration_v2/STAGE9_CORE_ARBITRATION_RULES_V2.md` used summary shorthand that was less explicit than the mechanism-owned P0 rules:

```text
Dsharer = round(Dtotal × R)
Dtarget = round(Dtotal × (1 - R))
Dparticipant = round(Dtransfer / N)
CleaveDerivedDamage = MainAttackFinalDamage × CleaveRatio
ChainCalculatedDamage = TriggerNodeResolvedDamage × CurrentChainRatio
```

This was a current-summary precision defect, not a runtime ambiguity or a P0 conflict.

### Exact cleanup

The Core summary is now call-site explicit:

```text
Dsharer = ROUND_HALF_UP(Dtotal × ShareRatio)
Dtarget = Dtotal - Dsharer
```

```text
Dtarget = ROUND_HALF_UP(Dtotal × (1 - DistributionRatio))
Dtransfer = Dtotal - Dtarget
Dparticipant = ROUND_HALF_UP(Dtransfer / N)
```

```text
CleaveDerivedCalculatedDamage
= FLOOR(
    ActualTargetTroopLoss
    × CleaveRatio
  )
```

```text
ChainCalculatedDamage
= FLOOR(
    TriggerNodeResolvedDamage
    × CurrentChainRatio
  )
```

The Cleave and Chain pipeline summaries were normalized to the same explicit integerization operators and base names.

Each numeric subsection now identifies the owning mechanism freeze record. Core remains the orchestration / summary consumer and does not become the semantic owner of Share, Distribution, Cleave, or Chain mathematics.

### Semantic outcome

Before cleanup:

```text
Mechanism P0 rules = already frozen and unambiguous
Core summary = shorthand / less explicit
```

After cleanup:

```text
Mechanism P0 rules = unchanged
Core summary = explicit mirror / reference of mechanism-owned rules
```

```text
Gameplay semantic change = NO
Core ownership change = NO
```

---

## FA-D01 — COMBO stale CBS9-B03 banner

### Original finding

State repository current P0 `states/functional/combo/MECHANISM_CONTRACT.md` had presentation drift:

```text
§9:  STATUS: OPEN — CBS9-B03
§26: CBS9-B03 = CLOSED (Frozen via RF-P04)
```

### Exact cleanup

§9 now preserves RF-P02 provenance while making current status explicit:

```text
HISTORICAL STATUS NOTE
CBS9-B03 was OPEN at RF-P02 time.
Superseded by RF-P04.
Current status: CLOSED.
See §26.
```

§26 and the underlying RF-P04 finalization semantics were not modified.

### Semantic outcome

Before cleanup:

```text
Current semantic status = CLOSED via RF-P04
Presentation = stale OPEN banner in §9
```

After cleanup:

```text
Current semantic status = CLOSED via RF-P04
Presentation = historical OPEN provenance + current CLOSED status
```

```text
Gameplay semantic change = NO
Historical provenance preserved = YES
```

---

## Scope Integrity Check

```text
FA-M01 touched only supporting repair prose / archived-example presentation.
FA-M02 touched only Core summary numeric explicitness / authority references.
FA-D01 touched only COMBO status presentation.

Frozen gameplay semantics modified = NO
Integerization conclusion modified = NO
Cleave damage layer modified = NO
NormalAttack lifecycle modified = NO
Finalization semantics modified = NO
Runtime contracts modified = NO
42 invariants modified = NO
45 regression contracts modified = NO
Production code modified = NO
Test code modified = NO
Global Final Audit report body modified = NO
STAGE9.md created = NO

P0 semantic change count = 0
```
