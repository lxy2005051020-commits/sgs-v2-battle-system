# Stage9 Typed Runtime Contracts

Package: `RF-C01 — IMPLEMENTATION_HARDENING`

Status: `FROZEN DESIGN CONTRACT / NO PRODUCTION CLASS CREATED IN RF-C01`

This document translates already-frozen Stage9 P0 semantics into implementation-facing typed contracts. It does not create new game rules, does not reopen Stage8, and does not require these exact class names. Equivalent types are allowed only when they preserve every identity, state, and ownership boundary below.

## 1. Design rule

Stage9 must prefer:

```text
typed source identity
+ operation identity
+ explicit state enum
+ lineage
```

over:

```text
boolean soup
+ mutable generic target fields
+ call-stack inference
+ scattered battle.finished checks
```

Stage8 stays FROZEN. Stage9-specific identity is added through Stage9 wrappers/coordinators and extension seams, not by stuffing Stage8 `DamageRequest` with mechanism-specific flags.

---

## 2. Strong operation identities

Conceptual value types:

```text
ActionId
NormalAttackInstanceId
DamageInstanceId
ReactionBatchId
PartitionTransactionId
CleaveEffectId
ChainTraversalId
DirectTroopLossId
TargetResolutionId
CounterBatchEntryId
```

Required properties:

```text
- immutable after creation
- unique within one BattleContext
- equality by identity, not display name
- serializable in test fixtures / traces
- never inferred from skill-name strings
```

A death fact, admission decision, or recursion decision must be attributable to the operation that owns it.

---

## 3. Source identity and lineage

### 3.1 SourceType

At minimum the runtime must distinguish equivalent typed values for:

```text
NORMAL_ATTACK
ACTIVE_SKILL
ASSAULT
PERIODIC_DAMAGE
CLEAVE
COUNTER
CHAIN_TRUE_FEEDBACK
SHARE_DIRECT_LOSS
DISTRIBUTION_DIRECT_LOSS
```

`DamageType` and `SourceType` are orthogonal. Example:

```text
sourceType = CLEAVE
damageType = WEAPON | STRATEGY
```

### 3.2 OperationLineage

Conceptual schema:

```text
OperationLineage {
  rootActionId: ActionId?
  parentNormalAttackId: NormalAttackInstanceId?
  parentDamageInstanceId: DamageInstanceId?
  sourceType: SourceType
  physicalAttacker: UnitId?
  physicalSkill: SkillId?
  creditOwner: UnitId?
}
```

Only fields with real semantic meaning are populated. No fake `DamageType`, attacker, or skill is invented merely to satisfy a generic interface.

Minimum provenance preserved wherever applicable:

```text
rootActionId
parentNormalAttackId
parentDamageInstanceId
sourceType
physicalAttacker
physicalSkill
creditOwner
```

Derived work must never recover its parent by parsing a skill name or log string.

---

## 4. Typed target identity

At minimum distinguish:

```text
SelectedTarget
IntendedAttackTarget       // pre_redirect_target
PostRedirectActualTarget   // final attack receiver after Guard
DamageRecipient            // recipient of a concrete DamageEvent/settlement
```

These are semantic types even if all ultimately wrap `UnitId`.

### 4.1 TargetResolutionResult

Conceptual schema:

```text
TargetResolutionResult {
  resolutionId: TargetResolutionId
  normalAttackId: NormalAttackInstanceId
  selectedTarget: SelectedTarget
  intendedAttackTarget: IntendedAttackTarget
  postRedirectActualTarget: PostRedirectActualTarget
  redirectSource: UnitId?
  redirectReason: NONE | GUARD
}
```

Frozen ordering:

```text
NormalAttack permission
→ fresh selector arbitration
   CONFUSION > TAUNT > default selector
→ intendedAttackTarget / pre_redirect_target
→ exactly one Guard pass
→ postRedirectActualTarget
→ Target Lock
```

Forbidden implementation:

```text
targetId = selected
... later ...
targetId = taunted
... later ...
targetId = guarder
```

A generic field must not silently change meaning across phases.

Downstream attack-bound mechanics consume `postRedirectActualTarget`, including:

```text
normal hit recipient
Counter holder
single-target Assault inheritance
Cleave main-target anchor
Share / Distribution state lookup for the resulting DamageEvent
```

A `DamageEvent` owns its own `damageRecipient`; it does not mutate the earlier target-resolution identities.

Each Combo #2 is a new `NormalAttackInstanceId` and receives a new `TargetResolutionResult`.

---

## 5. Combo runtime state

A single `combo_active: bool` is forbidden as the complete model.

### 5.1 ComboStateInstance

Represents the physical status instance:

```text
ComboStateInstance {
  instanceId
  holder
  sourceUnit
  sourceSkill
  ratioOrEffectMetadata
  durationMetadata
  lifecycleState
}
```

It answers whether the physical state exists and what owns it. It does not by itself answer whether the state is operational at this instant or whether an Action already owns a granted opportunity.

### 5.2 ComboActionGrant

Represents current-Action permission already granted from a specific instance:

```text
ComboActionGrant {
  actionId: ActionId
  grantingInstanceId
  sourceUnit
  sourceSkill
  provenanceLocked: true
  state: VALID | REVOKED_BY_PHYSICAL_REMOVE | CONSUMED
}
```

Frozen transitions:

```text
ACTION_START maintenance / expiry
→ read effective Combo
→ create grant if operational

physical REMOVE of granting instance before consume
→ VALID → REVOKED_BY_PHYSICAL_REMOVE

ordinary SUPPRESS after valid grant
→ does not revoke this Action grant

consume at checkpoint
→ VALID → CONSUMED
```

### 5.3 ComboCheckpointState

```text
ComboCheckpointState {
  actionId: ActionId
  state: NOT_REACHED | REACHED | CONSUMED | BLOCKED
}
```

The checkpoint state is not the physical state and not the grant.

### 5.4 Consume contract

Per `ActionId`:

```text
cfg230 emission count <= 1
Combo opportunity consumed <= 1
physical NormalAttack count <= 2
```

Frozen execution shape:

```text
valid grant
→ Combo Checkpoint
→ atomic consume
→ cfg230
→ can_normal_attack()
→ can_admit_new_work(COMBO_SECOND_NORMAL_ATTACK)
→ fresh target resolution
→ optional NormalAttack #2
```

No retry/refund occurs after atomic consume when a later gate blocks #2.

---

## 6. Cleave derived damage

Cleave must not be represented as another complete standard `DamageRequest`.

### 6.1 DerivedDamageRequest

Conceptual Cleave specialization:

```text
DerivedDamageRequest<CLEAVE> {
  damageInstanceId: DamageInstanceId
  cleaveEffectId: CleaveEffectId
  lineage: OperationLineage
  sourceType: CLEAVE
  damageType: inherited WEAPON | STRATEGY
  baseFact: ACTUAL_TARGET_TROOP_LOSS
  baseAmount: ActualTargetTroopLoss
  ratio: CleaveRatio
  integerization: FLOOR
  secondaryTarget: UnitId
  normalAttackIdentity: false
  permissionPolicy: CleaveDerivedPermissionPolicy
}
```

Frozen arithmetic:

```text
CleaveDerivedCalculatedDamage
= floor(ActualTargetTroopLoss × CleaveRatio)
```

### 6.2 Forbidden re-entry

Cleave secondary processing must not re-enter:

```text
base weapon formula
base strategy formula
secondary target generic damage-modifier recalculation
Crit reroll
NormalAttack-only target selection
Guard
Combo checkpoint
Counter trigger by NormalAttack identity
recursive Cleave
```

### 6.3 Allowed downstream gates

According to Frozen P0, Cleave secondary damage may enter:

```text
Evasion
Resistance
DamagePartitionResolver (Share or Distribution)
FirstAid
Chain
eligible recovery semantics
Troop settlement
```

Permissions derive from typed source/event identity, not skill-name strings or a `reaction_depth` boolean.

### 6.4 Cleave effect queue identity

Multiple effects are distinct `CleaveEffectId` values and execute:

```text
SKILL_SLOT_ORDER
+
EFFECT_MAJOR_ORDER
```

Within an admitted effect, secondaries follow `GLOBAL_SLOT_ASCENDING` with JIT liveness revalidation. A dead planned secondary is skipped; a passed slot is not revisited.

---

## 7. Attributed Direct Troop Loss

Share sharer loss and Distribution participant loss are not normal DamageEvents.

### 7.1 AttributedDirectTroopLoss

Conceptual schema:

```text
AttributedDirectTroopLoss {
  directLossId: DirectTroopLossId
  partitionTransactionId: PartitionTransactionId
  parentDamageInstanceId: DamageInstanceId
  sourceType: SHARE_DIRECT_LOSS | DISTRIBUTION_DIRECT_LOSS
  physicalAttacker: UnitId?
  physicalSkill: SkillId?
  victim: UnitId
  creditOwner: UnitId?
  theoreticalLoss: Integer
  actualLoss: Integer
  lineage: OperationLineage
}
```

`DamageType` is intentionally absent unless a future authoritative P0 explicitly assigns one.

### 7.2 Allowed effects

This operation may perform only Frozen direct-loss consequences:

```text
troop mutation
actual-loss clamp
death fact
wounded/statistics attribution
kill attribution
```

### 7.3 Forbidden Hit Pipeline re-entry

It must not re-enter:

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
base weapon/strategy formula
```

This is an identity rule, not a collection of ad hoc booleans on `DamageRequest`.

---

## 8. Damage partition arbitration

### 8.1 DamagePartitionResolver

For one eligible DamageEvent and final actual damage target:

```text
Dtotal
→ resolve exactly one effective policy:
   SHARE | DISTRIBUTION | NONE
→ execute exactly that policy
```

Share and Distribution may never serially partition the same `Dtotal`.

Cross-family replacement is terminal replacement, not suppression:

```text
Share replaces Distribution
→ replaced Distribution does not resume when Share later disappears
```

### 8.2 DamageShareTransactionPlan

```text
DamageShareTransactionPlan {
  transactionId: PartitionTransactionId
  parentDamageInstanceId: DamageInstanceId
  target
  sharer
  Dtotal
  ratio
  DsharerTheoretical = round_half_up(Dtotal × ratio)
  Dtarget = Dtotal - DsharerTheoretical
  targetCommitState: PLANNED | COMMITTED
  sharerCommitState: PLANNED | COMMITTED | DISCARDED_TARGET_DEATH
}
```

Commit order:

```text
commit target Dtarget
→ target death check
→ if target died: TARGET_DEATH_INTERRUPT, discard pending sharer work
→ else commit sharer attributed direct troop loss
```

Theoretical and actual loss are recorded separately.

### 8.3 DistributionTransactionPlan

```text
DistributionTransactionPlan {
  transactionId: PartitionTransactionId
  parentDamageInstanceId: DamageInstanceId
  target
  participantIds: immutable ordered tuple<UnitId>
  N: immutable Integer
  Dtotal
  ratio
  Dtarget = round_half_up(Dtotal × (1-ratio))
  Dtransfer = Dtotal - Dtarget
  Dparticipant = round_half_up(Dtransfer / N) when N > 0
  participantCommitStates
  targetCommitState
  runtimeAuthority: FROZEN_P0 | PROJECT_RUNTIME_DEFAULT
}
```

Planning occurs once at transaction start.

During execution:

```text
planned participant becomes invalid
→ SKIP its step
→ do not change participantIds
→ do not change N
→ do not change Dparticipant
→ do not redistribute

new unit becomes eligible mid-transaction
→ do not add it
```

Commander participant death follows RF-P04's explicit:

```text
PROJECT_RUNTIME_DEFAULT (NOT EMPIRICALLY PROVEN GAME RULE)
```

The already-admitted local Distribution transaction drains its planned local work before handing off to the finalization barrier.

---

## 9. Deferred Chain work

A Deferred Chain must not snapshot the whole combat world.

### 9.1 ChainDeferredWork

```text
ChainDeferredWork {
  traversalId: ChainTraversalId
  immutableTriggerSnapshot: {
    parentDamageInstanceId
    triggerNodeIdentity
    triggerDamage
    triggerProvenance
  }
  liveExecutionLookup: {
    triggerNodeIdentity
    chainStateSlotKey
    candidateSideKey
  }
  visitedSlots: Set<BattleSlot>
}
```

### 9.2 Snapshot fields

Fixed at qualification:

```text
triggerDamage
triggerNodeIdentity
parent/source provenance identity
```

### 9.3 Live-read fields

At execution:

```text
trigger node/source alive
current Chain state existence
current Chain owner
current ratio
current effect metadata
current candidate alive state
current candidate linked state
```

Therefore a Deferred Chain may keep the old `triggerDamage` but use a newly current owner/ratio if the Chain state changed before execution, exactly as Frozen P0 requires.

### 9.4 Traversal identity

The current traversal is one-pass by slot:

```text
slot visited → never revisit in this traversal
later unvisited slot linked before its turn → may join if currently eligible
```

`CHAIN_TRUE_FEEDBACK` uses restricted settlement and cannot recurse into Chain/Share/Distribution/Counter/FirstAid/Guard or normal HitResolution.

---

## 10. Counter admission and liveness

### 10.1 CounterBatchEntry

```text
CounterBatchEntry {
  entryId: CounterBatchEntryId
  reactionBatchId: ReactionBatchId
  counterInstanceIdentity
  owner
  source
  sourceSkill
  damageRate
  batchOrder
  admitted: true
}
```

Trigger-time admission freezes the entry identity, source-bound metadata, and order.

After admission:

```text
Counter state suppression/removal/expiry
→ does not revoke the admitted entry
```

### 10.2 Execution-time local gate

Immediately before a queued entry begins, live-read:

```text
owner currentTroops / liveness
target currentTroops / liveness
live combat stats and modifiers when normal Counter damage is allowed
```

If Counter owner died before its entry begins:

```text
entry fails local execution gate
→ no execution
```

This is not a re-check of CounterState operationality.

### 10.3 Dead-target Counter zero-loss terminal path

If an already-admitted sibling reaches execution after its target has died:

```text
CounterZeroLossTerminalPath {
  emit CounterExecute fact
  emit attributed zero troop loss
  do not call full weapon DamageRequest / DamageSystem
  do not run Evasion / Resistance / Share / Distribution / Chain / FirstAid
  complete entry
}
```

Zero is explicit terminal semantics, not an accidental result of the full damage pipeline.

---

## 11. Battle termination state

The following are distinct facts/states:

```text
UnitDeathFact
VictoryConditionSatisfied / VictoryConditionLatched
BattleFinalized
```

### 11.1 BattleTerminationState

Conceptual enum:

```text
RUNNING
VICTORY_LATCHED
DRAINING_ADMITTED_WORK
FINALIZED
```

Interpretation:

```text
RUNNING
→ new work may be admitted subject to mechanism gates

VICTORY_LATCHED
→ victory condition fixed
→ FutureBranch admission forbidden
→ already-admitted current operation still follows its local drain rule

DRAINING_ADMITTED_WORK
→ explicit state while local admitted operation/batch/transaction drains

FINALIZED
→ no new action, work, reaction, or settlement admission
```

Only the finalization owner may write `FINALIZED`.

### 11.2 Future admission gate

Conceptual API:

```text
can_admit_new_work(workKind, operationContext, battleTerminationState) -> bool
```

After victory latch it blocks at least:

```text
next Action
Assault not yet admitted
Combo #2 not yet admitted
new CounterBatch
new ChainTraversal
unadmitted next CleaveEffect
```

It does not retroactively erase currently admitted work such as:

```text
current Chain traversal remaining slots
already-admitted Counter sibling
current admitted CleaveEffect planned secondaries
admitted Distribution transaction under its local rule
```

A scattered mechanism-local `if battle.finished: return` is forbidden because it collapses admission, liveness, and finalization into one boolean and breaks these distinctions.

---

## 12. Recursion guard contract

Recursion and callback eligibility must be decided using:

```text
SourceType
NormalAttackIdentity
OperationLineage
permission policy
```

Examples:

```text
Cleave → Counter            BLOCKED
Cleave → Cleave             BLOCKED
Counter → Counter           BLOCKED
Chain → Chain               BLOCKED
Share direct loss → hit callbacks BLOCKED
Distribution direct loss → hit callbacks BLOCKED
```

Forbidden substitute:

```text
if already_in_counter_function
if reaction_depth > N
if skill_name == "..."
```

Call-stack booleans may exist for debugging but cannot be the semantic authority.

---

## 13. Stage8 compatibility

RF-C01 creates no production class and modifies no Stage1-8 runtime behavior.

Stage9 build must integrate through compatible seams around:

```text
Target Resolution before Stage8 damage calculation
post-formula DamagePartition before Troop commit
Stage9 derived/restricted settlement wrappers
ReactionBatch orchestration
Battle finalization coordinator
```

Do not reopen Stage8 merely to attach Stage9-specific booleans to its core `DamageRequest`.

```text
Stage8 = FROZEN
Formal Stage8 Reopen = NO
```
