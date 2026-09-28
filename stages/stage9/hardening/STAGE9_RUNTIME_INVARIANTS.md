# Stage9 Runtime Invariants

Package: `RF-C01 — IMPLEMENTATION_HARDENING`

Status: `FROZEN IMPLEMENTATION GUARDRAILS / TEST-ONLY ASSERTION SPEC`

These invariants encode already-frozen Stage9 semantics. They are not new game rules. Production code may use equivalent representations, but Stage9 build tests and diagnostic assertions must be able to prove the same properties.

## Target Identity

### INV-01 — Target identities are immutable semantic values
A resolved `SelectedTarget`, `IntendedAttackTarget`, `PostRedirectActualTarget`, and `DamageRecipient` must never be represented by one field whose meaning changes by overwrite.

### INV-02 — Selector arbitration precedes Guard
For a NormalAttack instance, Confusion/Taunt/default selector arbitration completes before Guard. Confusion shadows Taunt only at the selector layer.

### INV-03 — Guard is single-pass
Each `NormalAttackInstanceId` executes at most one Guard check. The resulting actual target is never recursively Guard-resolved again.

### INV-04 — Downstream attack-bound nodes consume actual target
After target lock, Counter holder, single-target Assault inheritance, Cleave main-target anchor, and the normal hit target use `PostRedirectActualTarget`, never the pre-redirect intended target.

### INV-05 — Damage recipient is owned by the concrete DamageEvent/settlement
A later partition or derived operation may have a different `DamageRecipient` without mutating the NormalAttack target-resolution record.

### INV-06 — Combo #2 has a fresh target-resolution identity
NormalAttack #2 creates a new `NormalAttackInstanceId` and `TargetResolutionResult`; it cannot inherit #1 target or Guard result.

## Combo Runtime State

### INV-07 — Physical state, operational state, and Action grant are distinct
No single boolean may simultaneously mean “Combo instance exists”, “Combo is operational now”, and “this Action already owns a Combo opportunity”.

### INV-08 — ACTION_START maintenance precedes grant
Expiry/removal/suppression state visible at ACTION_START must settle before the current Action evaluates an effective Combo and creates a grant.

### INV-09 — REMOVE and SUPPRESS have different grant effects
Physical removal of the granting instance before consume revokes the pending unconsumed grant. Ordinary suppression after a valid grant does not retroactively revoke that Action-local grant.

### INV-10 — Combo checkpoint count per Action is at most one
A given `ActionId` may reach the Combo checkpoint at most once.

### INV-11 — cfg230 / consume count per Action is at most one
A given `ActionId` may consume the Combo opportunity and emit cfg230 at most once, even if #2 later fails another gate.

### INV-12 — Physical NormalAttack count per Action is at most two
No Combo path may produce a third or later standard NormalAttack inside the same Action.

## Cleave Derived Damage

### INV-13 — Cleave has no NormalAttack identity
Every Cleave secondary derived event has `sourceType=CLEAVE` and `normalAttackIdentity=false`.

### INV-14 — Cleave base fact is ActualTargetTroopLoss
The parent normal hit value consumed by Cleave is exactly the parent actual target's clamped committed troop loss, not pre-partition `Dtotal`, unclamped `Dtarget`, or credited/statistical damage.

### INV-15 — Cleave integerization is FLOOR
`CleaveDerivedCalculatedDamage = floor(ActualTargetTroopLoss × CleaveRatio)` using deterministic arithmetic.

### INV-16 — Cleave cannot re-enter upstream formula/modifier/Crit stages
A Cleave secondary may not execute base weapon/strategy formula, generic secondary target damage-modifier recalculation, or Crit reroll.

### INV-17 — Cleave permissions are identity-driven
Cleave callback permissions are decided by typed event/source policy, not skill-name strings or reaction-depth inference. Counter and recursive Cleave are blocked; Evasion, Resistance, partition, FirstAid, Chain, and eligible recovery remain available according to Frozen P0.

### INV-18 — Cleave admitted-effect queue preserves frozen ordering
Cleave effects use skill-slot / effect-major ordering; planned secondaries use global slot ascending order with JIT liveness revalidation. A dead planned secondary is skipped, not replaced or reordered.

## Direct Troop Loss / Partition Identity

### INV-19 — AttributedDirectTroopLoss is not a DamageEvent
Share sharer loss and Distribution participant loss have their own typed operation identity and cannot masquerade as a normal hit.

### INV-20 — Direct troop loss never enters HitResolution
Attributed direct loss cannot trigger Defense, DamageReduction, Evasion, Resistance, FirstAid, Counter, Chain, Share, Distribution, generic Hurt callbacks, or base damage formulas.

### INV-21 — Direct troop loss preserves explicit provenance
Where semantically defined, the runtime records physical attacker, physical skill, victim, credit owner, source type, parent DamageInstance, theoretical loss, and actual committed loss separately.

### INV-22 — Exactly one partition policy executes per DamageEvent
`DamagePartitionResolver` selects exactly one of SHARE, DISTRIBUTION, or NONE. Share and Distribution can never serially partition the same `Dtotal`.

### INV-23 — Cross-family replacement cannot resurrect
A Distribution instance replaced by Share is terminally displaced for that instance; removal/expiry of the replacing Share cannot reactivate the replaced Distribution.

## Damage Share

### INV-24 — Share commits target first
For an admitted Share transaction, `Dtarget` commits before any sharer loss.

### INV-25 — Lethal Share target discards pending sharer work
If target commit reaches zero troops, `TARGET_DEATH_INTERRUPT` discards the pending theoretical sharer loss; the sharer commits zero from that transaction.

### INV-26 — Share theoretical and actual losses remain distinct
`Dsharer_theoretical` and the sharer's clamped `actualLoss` are separate facts; overflow is discarded and is not returned to the target or repartitioned.

## Distribution Fixed Plan

### INV-27 — Distribution participant identities and N are immutable after planning
Once `DistributionTransactionPlan` is created, its ordered participant identity tuple and `N` cannot change.

### INV-28 — Distribution calculated amounts are immutable after planning
`Dtarget`, `Dtransfer`, and `Dparticipant` are calculated once and cannot be recomputed because the world changes during the transaction.

### INV-29 — Invalid planned participant means SKIP only
A planned participant that becomes invalid before its step is skipped. The runtime performs no repartition, redistribution, remainder repair, or denominator change.

### INV-30 — Newly eligible participant cannot join an admitted transaction
A unit becoming eligible after plan creation must wait for a later independent DamageInstance; it cannot enter the current plan.

### INV-31 — Commander participant death uses the labeled engineering default
When a commander participant dies during an admitted Distribution transaction, the runtime drains the existing local transaction plan before finalization under `PROJECT_RUNTIME_DEFAULT`; the implementation must not present this as empirically proven official behavior.

## Chain Snapshot / Live Split

### INV-32 — Deferred Chain snapshots only immutable trigger facts
At qualification, `triggerDamage`, trigger-node identity, parent DamageInstance identity, and trigger provenance are fixed. The runtime must not snapshot the entire Chain/combat context.

### INV-33 — Deferred Chain live-reads execution fields
At execution it re-reads trigger-node/source liveness, current Chain state, current owner, current ratio/effect metadata, and current candidate alive/linked state.

### INV-34 — Chain traversal is one-pass by slot
Each battle slot is visited at most once per `ChainTraversalId`. A later unvisited slot linked before its turn may join; a passed slot is never revisited.

### INV-35 — Chain TRUE_FEEDBACK uses restricted settlement
Chain feedback does not re-enter standard formula/HitResolution and cannot trigger Chain, Share, Distribution, Counter, FirstAid, Guard, or other forbidden normal-hit callbacks.

## Counter Admission / Execution

### INV-36 — CounterBatch membership is immutable after admission
Once trigger-time admission creates the ordered `CounterBatchEntry` list, state suppression/removal/expiry cannot remove an already-admitted entry from that batch.

### INV-37 — Counter admission and owner liveness are separate gates
Post-admission state suppression/removal does not revoke entry admission; owner death before an entry begins fails a separate execution-time local liveness gate.

### INV-38 — Dead-target admitted Counter uses explicit zero-loss terminal path
An admitted sibling whose target is already dead emits Counter execution identity and attributed zero loss without invoking the full weapon DamageRequest pipeline or Evasion/Resistance/Share/Distribution/Chain/FirstAid.

## Victory / Finalization

### INV-39 — UnitDeathFact, VictoryLatched, and BattleFinalized are distinct
A unit reaching zero troops cannot directly set the battle to finalized. Victory satisfaction/latch and finalization are separate state transitions.

### INV-40 — Victory latch blocks FutureBranch admission, not admitted local work
After `VICTORY_LATCHED`, no new next Action, unadmitted Assault, Combo #2, CounterBatch, ChainTraversal, or later unadmitted CleaveEffect may enter. Current admitted work follows its frozen local drain/cancel rule.

### INV-41 — Finalization has one owner
Only the battle finalization coordinator/owner may transition `BattleTerminationState` to `FINALIZED`; mechanism code cannot set a generic `battle.finished` as a side effect of observing death.

## Operation Identity / Recursion

### INV-42 — Typed identity and lineage are semantic authority
Admission, recursion, and callback permissions must derive from `SourceType`, `NormalAttackIdentity`, operation IDs/lineage, and explicit permission policy. Call-stack booleans, skill-name tests, and scattered `if battle.finished` checks are not semantic authority.

---

## Test-only assertion map

During Stage9 build, diagnostic/test fixtures should expose enough trace data to assert at least:

```text
ActionId / NormalAttackInstanceId / DamageInstanceId
ReactionBatchId / PartitionTransactionId
CleaveEffectId / ChainTraversalId
TargetResolutionResult
SourceType / NormalAttackIdentity / OperationLineage
BattleTerminationState transitions
admission decision vs local-liveness decision
```

Assertions should fail at the first invariant violation rather than allowing a later troop-total mismatch to be the only symptom. Humans are remarkably good at debugging the wrong layer for six hours when an ID was overwritten twelve calls earlier, so the trace contract exists for a reason.

```text
Runtime Invariant Count = 42
P0 semantic expansion = 0
Stage8 reopen = NO
```
