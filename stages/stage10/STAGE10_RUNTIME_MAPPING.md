# Stage10 · Persistent State Runtime Integration · Runtime Mapping

> Status: `RESEARCH COMPLETE / ARCHITECTURE MAPPING COMPLETE`
>
> Production implementation: `NOT AUTHORIZED`

## 1. Mapping objective

This document maps the eight frozen persistent-state contracts onto the current Stage7 / Stage8 / Stage9 runtime without silently changing those frozen contracts.

The core rule is:

```text
reuse frozen owners where semantics already fit
+
add only explicit backward-compatible extension seams where a legitimate Stage10 consumer now exists
+
STOP when current runtime semantics would produce an officially wrong result
```

## 2. Current runtime owners

| Concern | Frozen owner | Stage10 rule |
|---|---|---|
| State physical storage | `BattleContext.states / StateRegistry` | no duplicate store |
| State mutation | `StateLifecycleSystem` | all apply/refresh/remove/expire changes remain here |
| Explicit lifecycle hook | Stage7 `RuleHookSystem / TriggerSystem` | extend only with typed consumers; EventBus remains observation-only |
| Recovery rule gate | `RecoverySystem` | keep target-death/healing-ban gate here |
| Troop mutation | `TroopSystem` | no direct troop write |
| Theoretical standard damage | Stage8 `DamageSystem` | do not bypass with ad-hoc troop loss for DOT |
| Defense-ignore formula policy | Stage8 `DamageFormulaPolicySystem` | reuse for REBELLION |
| Runtime RNG | `BattleContext.random / RandomSystem` | FIRST_AID probability consumes only this source |
| Damage operation identity | Stage9 `DamageInstanceCoordinator` | periodic damage remains authoritative `SourceType.PERIODIC_DAMAGE` |
| Partition / share / split | Stage9 damage orchestration | periodic damage enters normal Stage9 damage transaction unless authority explicitly says otherwise |
| Finalization / victory barrier | Stage9 finalization owner | Stage10 reactions may not bypass finalization/admission policy |

## 3. Stage7 mapping

### 3.1 Existing compatible seam: UNIT_ACTION_START

Current Stage7 already has:

```text
UnitActionStartHook
→ TriggerSystem.collect
→ ordered Effect(s)
→ RuleHookSystem
→ EffectExecutor
```

This is the correct high-level trigger seam for:

```text
BURN
FLOOD
POISON
ROUT
SANDSTORM
REBELLION
RECUPERATION
```

No new per-state battle loop is permitted.

### 3.2 Required Stage7 extension: AFTER_DAMAGE

FIRST_AID is not a periodic action-start state. Its contract requires:

```text
one eligible settled damage event
→ one independent probability check
→ optional recovery
```

Stage7 design explicitly deferred `AFTER_DAMAGE` until a legitimate consumer existed. Stage10 now provides that consumer.

Required design direction:

```text
AfterDamageHook (typed)
```

must carry enough immutable facts to evaluate FIRST_AID without reading EventBus history. At minimum the design must decide how to expose:

```text
damage_instance_id / lineage when Stage9-originated
source and target identity
damage type / source family
Stage8 prevented flag
assigned target damage
actual target troop loss
target defeated state
source state provenance for periodic damage
```

The hook must be emitted by explicit orchestration after destructive target settlement has produced the authoritative damage-resolution result. It must **not** be implemented as:

```text
EventBus DAMAGE_DEALT subscriber
→ TriggerSystem
```

because Stage7 freezes EventBus as fact publication, not rule control flow.

### 3.3 TriggerSystem cannot own formula work

Stage7 remains pure trigger intent generation. It may read frozen state runtime parameters and typed hook data, perform the state-specific probability check through `context.random` only if design explicitly assigns RNG ownership there, then produce typed Effects.

It may not:

```text
recalculate base damage formulas
mutate troops
mutate state registry
publish gameplay facts as control flow
```

## 4. StateRuntimeParams mapping

Current Stage7 params are intentionally synthetic/minimal:

```text
PeriodicDamageStateParams
- damage_type
- coefficient

PeriodicRecoveryStateParams
- amount
```

They are insufficient as the official Stage10 runtime contract.

Stage10 design needs official typed runtime params that preserve application-time frozen context. Conceptually:

```text
ContinuousDamageStateParams
- resolved route / DamageType
- source-side application snapshot needed for potency
- source troops/attribute snapshot inputs required by the frozen mechanism contract
- locked ordinary modifier context
- locked crit-family context
- source skill potency parameters
- state-specific flags (e.g. REBELLION defense policy)
- lifecycle metadata required for eligible tick counting
- temporary-active gate metadata where applicable

FirstAidStateParams
- probability snapshot
- recovery model kind
- locked source attribute context
- locked treatment rate OR damage-ratio parameters
- locked recovery modifier context
- source-skill lifecycle category / active gate reference

RecuperationStateParams
- recovery potency model
- locked source attributes
- locked recovery modifiers
- finite-vs-battle-long lifecycle model
- source-skill lifecycle category / active gate reference
```

These names are design placeholders, not yet frozen class names.

Critical invariant:

```text
StateRuntimeParams store mechanism inputs / frozen context
≠ executable mini-engine
```

## 5. StateLifecycleSystem mapping

### 5.1 Reapplication

Current `StateRegistry` permits multiple instances. Therefore Stage10 same-name uniqueness must be enforced by `StateLifecycleSystem`, not by relying on registry accident.

Required behavior for the eight states:

```text
incoming same-name persistent state on same owner
→ identify current effective same-name instance
→ terminally replace it under StateLifecycleSystem ownership
→ new instance receives new source/source skill/source slot
→ new runtime snapshot
→ duration reset from incoming source contract
```

Do not generalize this into a universal stacking rule for all 40 official states.

### 5.2 Expiration gap

Current generic state expiration accepts only:

```text
ROUND_START
ROUND_END
```

The Stage10 contracts require owner-relative action-start lifecycle semantics.

Therefore Stage10 needs an explicit lifecycle extension that can guarantee:

```text
eligible action-start opportunity count
+
no N+1 tick
+
application-before-action same-round eligibility
+
application-after-action no catch-up
```

A fake conversion from all contracts to global `ROUND_START` expiry is forbidden because it changes observable same-round behavior.

### 5.3 Death cleanup

Owner death must hard-terminate all attached persistent state execution.

The runtime design must verify one authoritative cleanup point rather than adding eight source-specific death listeners.

Source death must **not** invoke generic sourced-state deletion.

## 6. Stage8 mapping

### 6.1 What can be reused directly

The following Stage8 seams are already structurally correct for Stage10:

```text
DamagePreventionSystem
HitResolutionSystem
DamageFormulaPolicySystem
DamageModifierSystem
DamagePipelineTrace
DamageResult
```

REBELLION can reuse the already frozen formula policy:

```text
DamageDefensePolicy.IGNORE_RELEVANT_TARGET_DEFENSE
```

This is preferable to a special “true damage” route because the mechanism contract still allows applicable percentage damage modifiers.

### 6.2 Critical incompatibility: live-source formula path

Current `DamageSystem.calculate()` validates that:

```text
source exists
source.troops > 0
```

and then calculates base damage from the **current** source/target runtime through the frozen base formula.

That is not equivalent to Stage10 continuous-damage authority, which freezes:

```text
potency/application context at state application or refresh
source death does not cancel existing state
runtime source attribute changes do not recalculate existing potency
```

Therefore this current path is **not an authorized official DOT implementation**:

```text
PeriodicDamageStateParams(coefficient)
→ DamageEffect
→ DamageSystem.calculate(current live source)
```

It would incorrectly:

```text
1. reject a valid persistent tick after the original source dies
2. recalculate damage from runtime source state instead of application snapshot
3. risk re-reading runtime modifiers that the contract locks at application
```

This is the primary Stage10 architecture design issue.

### 6.3 Required design seam: snapshot-backed continuous damage

Stage10 design must introduce one explicit Stage8-compatible input model for continuous damage that preserves all four requirements simultaneously:

```text
A. Stage8 prevention / hit / formula-policy / modifier semantics remain observable
B. base formula topology is not duplicated or silently rewritten
C. application-time potency context is authoritative
D. dead historical source may still receive provenance credit without pretending to be an alive attacker
```

Acceptable solution families to evaluate in Stage10 design include:

```text
1. typed formula-input snapshot consumed by the existing DamageSystem pipeline
2. typed precomputed continuous-damage baseline that enters the Stage8 pipeline at an explicitly frozen seam
3. another single-pipeline design proven equivalent by independent audit
```

Not acceptable:

```text
clone DamageSystem into PersistentDamageSystem
write target.troops directly
route official DOT through DirectTroopLossSystem
temporarily resurrect source unit
mutate source attributes back to snapshot values
skip Stage8 to avoid source-death validation
```

Whether option 1 or 2 is selected is a Stage10 **design decision**, not a research question.

### 6.4 Dynamic gates vs locked context

Stage10 must keep this boundary explicit:

```text
LOCKED AT APPLICATION
- source potency inputs
- ordinary modifier context specified by contract
- route/crit family context

DYNAMIC AT TICK
- owner alive
- weakness prevention
- evasion / barrier when officially integrated
- battle finalization eligibility
```

A single generic “snapshot everything” flag is too coarse and would freeze things that are contractually dynamic.

## 7. Stage9 mapping

### 7.1 Periodic damage ingress

Current production already recognizes:

```text
SourceType.PERIODIC_DAMAGE
↔ DamageSourceType.CONTINUOUS
```

and requires state provenance IDs on production periodic `DamageEffect`.

This is the correct operation identity for the six DOT states and must be retained.

Required provenance:

```text
source unit
source skill
source skill slot when applicable
source state id
source state instance id
SourceType.PERIODIC_DAMAGE
DamageInstanceId generated by Stage9 coordinator
```

### 7.2 Share / distribution / chain / finalization

A Stage10 periodic damage tick is still a real damage operation. Unless a frozen state contract explicitly excludes a Stage9 cross-mechanism family, it must enter the same orchestration seams rather than manually applying troops.

Research classification:

```text
Damage Share / Distribution
→ runtime orchestration responsibility, not persistent-state-owned arithmetic

Chain / other admitted secondary work
→ Stage9 policy owns eligibility and future work

Battle finalization
→ Stage10 may not create new work after Stage9 has denied admission / finalized battle
```

Stage10 does not reinterpret Stage9’s six existing `FutureBranchKind` values. If FIRST_AID recovery is synchronous completion-local work rather than a new global future branch, design must explicitly prove that it can complete inside the current DamageInstance/finalization boundary. If it requires new future work after settlement, Stage10 must explicitly audit whether a new future-admission branch kind is required.

This is a design item, not permission to bypass `FutureAdmissionGate`.

### 7.3 FIRST_AID placement

FIRST_AID must observe the authoritative damage settlement result because damage-ratio recovery sources need the actual triggering damage input and fatal damage must hard-stop recovery.

Proposed design checkpoint to audit:

```text
Stage8 calculate Dtotal
→ Stage9 partition / assigned target amount
→ TroopSystem settlement
→ authoritative DamageResolutionResult
→ fatal-target check
→ typed AFTER_DAMAGE hook
→ FIRST_AID chance / optional RecoverEffect
→ RecoverySystem
→ continue Stage9 reaction/finalization boundary
```

The final Stage10 design must prove exact placement relative to:

```text
partition direct losses
counter/cleave/chain child work
victory latch
finalization drain
```

No placement is frozen merely by this research document.

## 8. Recovery mapping

### 8.1 Existing RecoverySystem is the correct terminal gate

Current RecoverySystem already correctly centralizes:

```text
target defeated prevention
healing-ban prevention
TroopSystem.restore
recovery event publication
```

`TroopSystem.restore` correctly clamps recovery to current missing troops.

Therefore Stage10 should **not** rewrite recovery mutation.

### 8.2 What must happen before RecoverySystem

Stage10 must resolve the nominal recovery amount before constructing the final recovery request:

```text
FIRST_AID probability
FIRST_AID model selection
triggering actual-damage ratio when applicable
RECUPERATION application snapshot potency
source-skill temporary-active gate
locked recovery modifiers
```

Then:

```text
nominal amount
→ RecoverEffect / RecoveryRequest
→ RecoverySystem dynamic target-death + healing-ban gate
→ TroopSystem.restore cap
```

Current `RecoverEffect` / `RecoveryRequest` provenance is less complete than Stage10’s desired provenance because it does not carry `source_skill_slot`, typed operation lineage, or source-ref identity. Stage10 design must decide whether recovery becomes an operation-identified effect or whether state provenance is sufficient and operation lineage remains attached to the surrounding hook result.

## 9. RNG mapping

FIRST_AID consumes one independent probability check per eligible damage event.

RNG owner remains:

```text
BattleContext.random
```

No Stage10 state may:

```text
import random
instantiate its own RNG
derive probability from instance_id hash
consume RNG for ineligible or already-fatal events
```

Design must freeze the exact “eligibility checks before RNG” order so deterministic replay does not drift.

## 10. External dependencies that must remain external

The following are interactions, not ownership transfers into persistent-state runtime:

```text
positive dispel
negative cleanse skill targeting logic
command aura source-death lifecycle
source skill temporary deactivation (伪报 / 军心动摇)
Elephant Soldiers Flood-delay behavior
skills that observe Burn/Flood/Poison/etc as predicates
critical/evasion/barrier official state application mechanics
```

Stage10 may expose typed seams for them, but must not silently implement their entire source systems.

## 11. Architecture verdict

### Reuse without reopen

```text
StateRegistry                         YES
StateLifecycleSystem ownership       YES
Stage7 UnitActionStart hook path      YES
RecoverySystem / TroopSystem          YES
Stage8 defense-ignore policy          YES
Stage9 PERIODIC_DAMAGE identity       YES
Stage9 partition/finalization owners  YES
RandomSystem                          YES
```

### Backward-compatible extension required

```text
Stage7 typed AFTER_DAMAGE hook                    REQUIRED
persistent official StateRuntimeParams            REQUIRED
same-name refresh arbitration for Stage10 family  REQUIRED
action-start lifecycle/expiry semantics           REQUIRED
recovery provenance / context extension           REQUIRED
source-skill inactive gate seam                    REQUIRED
```

### Explicit design decision required before build

```text
snapshot-backed continuous-damage pipeline seam   P0
source-dead persistent-damage execution model     P0
FIRST_AID exact Stage9 settlement/finalization placement P0
```

### Forbidden shortcut

```text
“existing synthetic PeriodicDamageStateParams already runs, therefore official DOT is integrated”
```

That statement is false under the frozen mechanism contracts.

## 12. Mapping verdict

```text
Stage7 mapping    = COMPLETE, extensions identified
Stage8 mapping    = COMPLETE, one central P0 design incompatibility identified
Stage9 mapping    = COMPLETE, FIRST_AID placement requires design freeze
Lifecycle mapping = COMPLETE, action-start expiry extension identified
Recovery mapping  = COMPLETE
RNG mapping       = COMPLETE
Provenance mapping= COMPLETE, recovery extension required

RUNTIME MAPPING RESEARCH = COMPLETE
PRODUCTION BUILD          = BLOCKED UNTIL STAGE10 DESIGN DECISIONS CLOSE
```
