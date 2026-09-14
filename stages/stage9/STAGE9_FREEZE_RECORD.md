# Stage9 Freeze Record

## Purpose

`STAGE9_DESIGN_FREEZE.md` is the pre-implementation design freeze. This file is the post-implementation/runtime final freeze authority for **Stage 9 · Cross-Mechanism Runtime Orchestration**.

## Frozen implementation identity

Final frozen implementation source:

`7380682164cf4a71256e23207bd031171c3e6231`

Parent:

`57ff7bbc6df6f85010add43d8fcc9567d3a0f95b`

FF9-B01 repair changed only:

- `tests/test_stage9_phase_9_5_infrastructure.py`
- `stages/stage9/implementation/STAGE9_PREFREEZE_VERIFICATION_REPAIR_REPORT.md`

Production diff: `0`.

Build Prompt blob: `835206ba39ce64c42a822a7138afeee307e0a492`.

Frozen State Authority:

- Repository: `lxy2005051020-commits/sgs-state-mechanics-research`
- branch: `main`
- commit: `15ed915435f328a6ecd8f488d98b5b9e13c913b5`

## Stage8 permanent boundary

```text
Stage8 = FROZEN
Formal Stage8 Reopen = NO
```

Stage9 does not change:

- weapon base formula
- strategy base formula
- DamagePrevention semantics
- HitResolution semantics
- DamageModifier semantics
- DamageFormulaPolicy ownership

Permanent non-alias fields:

```text
DamageResult.final_damage
= Dtotal

DamageSettlementRequest.assigned_target_damage
= Dtarget

DamageResolutionResult.actual_target_troop_loss
= ActualTargetTroopLoss
```

## Target pipeline

```text
Alive/legal pool
→ camp
→ Confusion
→ Taunt
→ default selector
→ intended target
→ Guard exactly once
→ actual target
```

Combo #2:

```text
same ActionId
new NormalAttackInstanceId
new TargetResolutionResult
fresh Guard
```

## Operation identities

Frozen identities:

- ActionId
- NormalAttackInstanceId
- TargetResolutionId
- DamageInstanceId
- PartitionTransactionId
- DirectTroopLossId
- CleaveEffectId
- ChainTraversalId
- ReactionBatchId
- CounterBatchEntryId

Principle:

```text
operation identity != gameplay priority
```

Operation IDs may be used only for identity, provenance, lookup, trace, and equality. They must not be used as a gameplay sorting comparator.

## Provenance

```text
EffectSourceRef = pre-operation provenance
OperationLineage = runtime ancestry
```

Never infer Stage9 `SourceType` backward from Stage8 `DamageSourceType`.

SkillSlot:

```text
INHERENT = 0
LEARNED_1 = 1
LEARNED_2 = 2
```

SkillSlot comes from the holder runtime loadout, not a static `SkillDefinition` field.

## FutureBranch admission

The only FutureBranch families are:

```text
NEXT_ACTION
ASSAULT
COMBO_SECOND_NORMAL_ATTACK
COUNTER_BATCH
CHAIN_TRAVERSAL
CLEAVE_EFFECT
```

Unified admission:

```text
FutureAdmissionGate
→ one-shot authentic permit
→ exact consume
→ only then operation identity allocation
→ admission
```

Victory latch blocks **new** future work. It does **not** discard already-admitted local work.

## Finalization

Unique semantic owner:

`BattleFinalizationCoordinator`

`BattleEngine` is the legacy compatibility projector.

Lifecycle:

```text
RUNNING
→ VICTORY_LATCHED
→ DRAINING_ADMITTED_WORK
→ FINALIZED
```

Finalization barriers:

- INITIAL_SETTLED
- ROUND_START_HOOKS_SETTLED
- UNIT_ACTION_START_HOOKS_SETTLED
- ACTION_SETTLED
- ROUND_END_SETTLED
- MAX_ROUND_SETTLED

## Partition semantics

Exactly one of:

```text
NONE
SHARE
DISTRIBUTION
```

Priority:

`SHARE > DISTRIBUTION`

Share is target-first. For a lethal target:

```text
TARGET_DEATH_INTERRUPT
→ pending sharer loss discarded
```

Distribution uses fixed participant tuple, fixed N, fixed Dtarget, fixed Dtransfer, and fixed Dparticipant. Invalid participant = SKIP. No replacement, no replan, no repartition.

## Integerization

```text
CHAIN: FLOOR
CLEAVE: FLOOR
DAMAGE_SHARE: ROUND_HALF_UP
DISTRIBUTION target: ROUND_HALF_UP
DISTRIBUTION participant: ROUND_HALF_UP
```

Exact vectors:

```text
396 × 28.28% = 111
470 × 15% → Dsharer = 71, Dtarget = 399
251 × 50% → Dtarget = 126, Dtransfer = 125
353 / 2 = 177
55 × 54% = 29
```

## Frozen mechanisms

```text
690103 CONFUSION       RUNTIME FROZEN
690106 TAUNT           RUNTIME FROZEN
690098 GUARD           RUNTIME FROZEN
690081 COMBO           RUNTIME FROZEN
690084 CLEAVE          RUNTIME FROZEN
690097 CHAIN_LINK      RUNTIME FROZEN
690087 DAMAGE_SHARE    RUNTIME FROZEN
690085 COUNTERATTACK   RUNTIME FROZEN
```

Distribution:

```text
690086 DISTRIBUTION
RUNTIME: FROZEN
PROJECT_RUNTIME_DEFAULT: FROZEN
EMPIRICAL: OPEN / UNOBSERVED
RESEARCH DEBT: YES
```

## Cleave frozen semantics

- source ordering: `SkillSlot`
- execution ordering: effect-major
- secondary plan: fixed identity plan
- secondary order: `GLOBAL_SLOT_ASCENDING`
- secondary eligibility: JIT live-read
- derived damage basis: parent main-hit `ActualTargetTroopLoss`
- integerization: `FLOOR`
- main target death does not cancel current `CleaveEffect` admission
- later independent Cleave after victory latch is BLOCKED

### Cleave recovery correction

Cleave derived damage basis is the parent main-hit `ActualTargetTroopLoss`.

For Cleave secondary + Share, attacker Lifesteal / StrategyRecovery basis is the secondary post-share `Dtarget`, **not** secondary `ActualTargetTroopLoss` and **not** `Dsharer`.

This is a frozen runtime contract.

## Chain frozen semantics

Snapshot:

```text
triggerDamage
immutable trigger identity/provenance
```

Execution live-read:

- current Chain state
- current owner
- current ratio
- candidate eligibility

Traversal uses a monotonic global-slot cursor. A passed slot is never revisited. A later unvisited slot may become eligible before the cursor arrives.

`TRUE_FEEDBACK` is restricted settlement, not a standard `DamageRequest`, and cannot recursively trigger Chain.

## Counter frozen semantics

Three layers:

```text
trigger-time state eligibility snapshot
→ immutable CounterBatch
→ execution-time owner/target liveness
```

Dead owner: local execution cancellation.

Dead target with an already-admitted entry:

```text
CounterExecute
→ explicit zero-loss terminal
```

It must not enter the full weapon pipeline.

Callbacks:

```text
Counter → Counter BLOCKED
Counter → Cleave BLOCKED
Counter → Chain according to typed policy
```

## Combo frozen semantics

```text
ACTION_START maintenance before grant
REMOVE revokes unconsumed grant
SUPPRESS after grant does not revoke current grant
checkpoint <= 1 / Action
grant consume <= 1 / Action
cfg230 <= 1 / Action
physical NormalAttack <= 2 / Action
```

## Capability authenticity

```text
same value != same capability
```

This covers:

- FutureAdmissionPermit
- DamageSettlementPermit
- FinalizationProjectionPermit
- ActionScope

Cross-context rule:

```text
same textual ID != same authority
```

Foreign context is rejected before mutation.

## FF9-B01 closure

```text
FF9-B01 = CLOSED
```

Root cause: `Path.glob` filesystem enumeration order was incorrectly treated as a stable test contract.

Repair: order-independent assertion only.

Frozen semantic coverage after repair:

```text
DamageEffect constructors = exactly 2
producer file set = { skill_resolver.py, trigger_system.py }
source_ref coverage = 100%
```

- Gameplay change: NO
- Production change: NO
- Architecture semantic change: NO

## Approved-source evidence

Approved frozen source: `7380682164cf4a71256e23207bd031171c3e6231`.

Fresh local verification on the exact approved-source artifact snapshot:

```text
pytest run 1: 753 / 753 PASS
pytest run 2: 753 / 753 PASS
demo: PASS
```

CI:

```text
run_id: 34834698631
head_sha: 7380682164cf4a71256e23207bd031171c3e6231
conclusion: success
```

Artifact:

```text
id: 10343920202
name: stage8-independent-audit-7380682164cf4a71256e23207bd031171c3e6231
legacy label: YES
digest: sha256:77449ee0eb87bb0f0722659ca5409a7663a30e2d3fe2bb2787a835953eb881fd
AUDIT_SOURCE_SHA: 7380682164cf4a71256e23207bd031171c3e6231
```

The artifact name is a LEGACY / NON-SEMANTIC LABEL.

## Freeze verdict

```text
Stage9 Design Freeze: PASS
Build Prompt Audit: PASS
Phase 9.1..9.8: COMPLETE
Independent Implementation Audit: COMPLETE
Implementation Final Re-Audit Round 2: PASS
FF9-B01: CLOSED
Pre-Freeze Verification Repair Re-Audit: PASS
42 / 42 invariants: PASS
45 / 45 gameplay regressions: PASS
12 / 12 architecture guarantees: PASS
6 / 6 finalization: PASS
5 / 5 integerization: PASS
6 / 6 FutureBranch: PASS
Stage8 reopen: NO
P0 conflict: 0
DSTS9-B02 research debt: PRESERVED
STAGE 9: FROZEN
```

## Formal reopen policy

Stage9 frozen runtime semantics must not be changed by convenience patches.

Any future discovery of a gameplay contradiction, P0 conflict, target semantics defect, finalization ownership defect, provenance defect, integerization defect, or public frozen runtime contract defect requires:

```text
FORMAL STAGE9 REOPEN
```

A later stage must not silently alter these frozen contracts.
