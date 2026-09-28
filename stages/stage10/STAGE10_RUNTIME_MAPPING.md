# Stage10 · Persistent State Runtime Integration · Runtime Mapping R1-C

> Status: `RUNTIME MAPPING REPAIRED FOR DRAFT V2`  
> Production implementation: `NOT AUTHORIZED`

This document maps the repaired Stage10 contracts onto the current Stage7 / Stage8 / Stage9 runtime. Normative design is `STAGE10.md`; compatibility reopen details are in the Stage7 and Stage8 addenda.

---

## 1. Current frozen owners retained

| Concern | Existing owner | Stage10 V2 rule |
|---|---|---|
| battle state storage | `BattleContext.states / StateRegistry` | no duplicate state store |
| state mutation | `StateLifecycleSystem` | apply/refresh/remove/expire/defeat-clear remain here |
| trigger collection | `TriggerSystem` | pure typed intent collection only |
| hook orchestration | `RuleHookSystem` | deterministic routing + owner-state defeat abort |
| theoretical normal damage | Stage8 `DamageSystem` | remains unique owner; receives limited frozen-input lane |
| formula policy | `DamageFormulaPolicySystem` | REBELLION reuses typed ignore-defense policy |
| standard destructive settlement | `DamageResolutionSystem` | target troop mutation coordination + defeat checkpoint |
| DamageInstance orchestration | `DamageInstanceCoordinator` | remains standard target/partition coordinator |
| partition | `DamagePartitionCoordinator` | Share/Distribution arithmetic unchanged |
| direct partition loss | `DirectTroopLossResolver` | remains DirectTroopLoss; gains common defeat checkpoint |
| recovery policy | `RecoverySystem` | target/healing-ban/recovery-result owner unchanged |
| troop mutation | `TroopSystem` | unique actual troop mutation/cap owner |
| victory/finalization | `BattleFinalizationCoordinator` | admitted work vs future admission unchanged |
| RNG | `BattleContext.random` | only battle RNG source |
| events | `EventBus` | facts only, never gameplay control flow |

---

## 2. New Stage10 typed owners

```text
ActionProgressTracker
SkillRuntimeRegistry
ContinuousDamageBasisProducer
DefeatCleanupPort
DamageAftermathSystem / DamageAftermathPort
RecoveryOpportunitySystem
StateApplicationGenerationId / StateGenerationSnapshot contracts
```

None of these is allowed to duplicate an existing mutation owner.

---

## 3. Stage7 mapping

Current Stage7 path:

```text
UnitActionStartHook
→ TriggerSystem.collect
→ RuleHookSystem
→ EffectExecutor
```

Stage10 keeps that seam for:

```text
BURN
FLOOD
POISON
ROUT
SANDSTORM
REBELLION
RECUPERATION
```

Two limited extensions are required.

### 3.1 Death hard boundary

Current code executes the collected Effect tuple with no per-effect owner-death abort. Stage10 compatibility addendum changes only that boundary:

```text
owner-state Effect causes owner death
→ DefeatCleanupPort clears owner states synchronously
→ ExecutionRightSystem denies remaining owner-state execution
→ RuleHookSystem marks tail aborted
```

Trigger collection remains one-shot/deterministic.

### 3.2 RecoveryOpportunity as sibling intent

R1-C does not force probability-bearing recovery into a generic `RecoverEffect` before probability resolution.

```text
TriggerSystem
→ RuleIntent batch
   - ordinary Effect
   - RecoveryOpportunity

RuleHookSystem
→ EffectExecutor for Effect
→ RecoveryOpportunitySystem for RecoveryOpportunity
```

TriggerSystem consumes no RNG.

---

## 4. Stage8 mapping

Current LIVE path is verified from production code as:

```text
participant validation
→ rule provider
→ prevention
→ hit resolution
→ formula policy
→ Weapon/Strategy base formula
→ coefficient
→ modifier system
→ finalization
→ DamageResult + DamagePipelineTrace
```

The base formula currently reads live source/target facts and consumes formula RNG. Probabilistic modifier contributions may consume RNG in `DamageModifierSystem`.

### 4.1 LIVE_RUNTIME

No Stage10 change is permitted:

```text
source exists and is alive
current source/target facts
current provider collection
current formula RNG
current modifier probability behavior
current trace semantics
```

Exact golden regression is mandatory.

### 4.2 FROZEN_APPLICATION

The new lane is restricted to authoritative periodic continuous damage.

Application/refresh producer captures:

```text
historical source provenance
application generation
route
source-side formula facts
formula-policy result
coefficient/potency input
application-resolved ordinary modifier plan
application-resolved crit context when authorized
```

Tick consumer:

```text
validates historical roster source identity
DOES NOT require source alive
validates target alive
runs dynamic Prevention
runs dynamic Hit Resolution
reuses frozen FormulaPolicy result
runs same base-formula arithmetic with frozen source facts + current target formula facts
uses existing base-formula tick RNG
uses frozen coefficient
applies frozen modifier plan without rediscovery/reroll
finalizes one DamageResult
```

This replaces Draft V1's `nominal_damage` shortcut.

### 4.3 Trace

Chosen representation:

```text
DamagePipelineTrace.frozen_application_trace
```

Tick-time stages that did not execute remain truthfully `NOT_EVALUATED`; the typed frozen trace records the reused application-generation inputs/results.

---

## 5. REBELLION mapping

Application/refresh:

```text
route = WEAPON or STRATEGY
route locked
formula policy = IGNORE_RELEVANT_TARGET_DEFENSE
matching modifier/crit context locked
```

Tick:

```text
same locked route
same formula-policy result
Stage8 base formula actually consumes ignore-defense policy
```

No true-damage/direct-loss bypass is created.

---

## 6. Persistent lifecycle mapping

Current generic Stage7 expiry is not sufficient for owner-relative Stage10 windows.

Stage10 maps lifecycle through:

```text
BattleContext.action_progress: ActionProgressTracker
+
PersistentLifecycleWindow
```

Time domain:

```text
PRE_BATTLE
ROUND 1
ROUND 2
...
```

Rules:

```text
PRE_BATTLE + N=1 → first=1 last=1
PRE_BATTLE + N=2 → first=1 last=2
round R before owner ActionStart → first=R
round R after owner ActionStart  → first=R+1
last = first + N - 1
```

Physical expiry occurs at completion of the owner's last eligible `UNIT_ACTION_START` resolution window, not at some later owner action.

Therefore expired persistent states are absent from all gameplay queries immediately after that window.

---

## 7. Refresh mapping

Current `StateRegistry` may hold multiple instances, so official Stage10 same-name uniqueness must be enforced in `StateLifecycleSystem`.

R1-C model:

```text
one physical StateInstance container
+
new StateApplicationGenerationId on every successful apply/refresh
```

Refresh atomically replaces:

```text
source unit
source skill
source slot
runtime params
frozen damage/recovery basis
lifecycle window
generation id
```

Generated work carries `StateGenerationSnapshot`, so refresh cannot alter already-created intent.

---

## 8. Death cleanup mapping

Current production code has several destructive paths:

```text
DamageResolutionSystem
DirectTroopLossResolver
CleaveDerivedDamageResolver
ChainSystem restricted feedback
```

and each can observe a death edge independently.

Stage10 requires one synchronous port:

```text
DefeatCleanupPort
```

Every destructive owner calls it on alive→dead before returning control to later aftermath/reaction work.

The port delegates physical state deletion to `StateLifecycleSystem.clear_owner_on_defeat` and does not use EventBus subscribers.

Required death-capable routes:

```text
standard target settlement
PERIODIC_DAMAGE
Counter
Share direct loss
Distribution direct loss
Cleave target/direct partition loss
Chain restricted feedback
future troop-loss resolvers
```

Source death and owner death remain distinct: cleanup affects states attached to the defeated owner, not all states historically sourced by that unit.

---

## 9. SkillRuntime mapping

Current `SkillRuntime` already has:

```text
owner_id
skill_slot
enabled
```

but current BattleContext lacks an authoritative owner/slot lookup.

Stage10 adds:

```text
SkillRuntimeRegistry
key = (owner_id, SkillSlot)
```

Registration occurs before PRE_BATTLE state application.

Lookup validates expected `skill_id` against the stored runtime definition.

Source death does not remove the registry entry and does not implicitly set `enabled=false`.

Gate mapping:

```text
ALWAYS_ACTIVE
→ no dynamic skill lookup

QUERY_SKILL_RUNTIME
→ read only current explicit skill enabled/disabled fact

EXTERNAL_LIFECYCLE
→ external owner removes state through StateLifecycleSystem
→ no dynamic callback query
```

---

## 10. FIRST_AID DamageAftermath mapping

Current Stage9 facts already separate:

```text
Dtotal
assigned target damage
ActualTargetTroopLoss
target defeated
SourceType / lineage
```

but Draft V1's `prevented + actual_loss` pair is not expressive enough.

Stage10 adds typed `DamageAftermathFact` with at least:

```text
resolved-hit topology
no-hit evasion/miss topology
weakness-zero cause
barrier-zero cause
assigned target damage
actual target loss
target defeated
lineage/source family
```

FIRST_AID exact eligibility:

```text
effective FIRST_AID generation
+
source-skill gate operational
+
relevant source/event family
+
resolved-hit topology
+
target survived
→ opportunity
```

No `ActualTargetTroopLoss > 0` requirement exists.

---

## 11. Stage9 standard settlement mapping

### 11.1 NoPartition

```text
DamageSystem
→ target settlement
→ defeat cleanup if fatal
→ Stage9 death observation if fatal
→ DamageAftermathPort
→ local FIRST_AID recovery when eligible
→ existing resolved-damage callbacks
→ reaction admission
→ complete DamageInstance
```

### 11.2 Share

```text
target settlement Dtarget
→ cleanup/death check
→ if target dies: discard pending sharer loss, no FIRST_AID
→ if target survives: target DamageAftermathPort / FIRST_AID
→ Share DirectTroopLoss to sharer
→ sharer cleanup/death observation if required
→ existing target resolved-damage callbacks
→ complete
```

Share direct loss itself never creates FIRST_AID.

### 11.3 Distribution

Current Stage9 participant-first plan remains:

```text
participant DirectTroopLoss commits
→ cleanup/death observations
→ target settlement Dtarget
→ cleanup/death observation
→ target DamageAftermathPort
→ existing callbacks
→ complete current admitted DamageInstance
```

If a participant death latches victory before target settlement, the already-admitted Distribution transaction and its target-local aftermath still drain. New future branches remain blocked.

---

## 12. Cleave mapping

Current code has a separate `cleave_first_aid` callback. Stage10 removes that production seam.

Repaired mapping:

```text
Cleave derived hit/partition logic
→ target settlement
→ DefeatCleanupPort
→ shared DamageAftermathPort
→ FIRST_AID when permitted
→ Share direct loss after surviving target aftermath when applicable
→ attacker recovery contract
→ existing damage callbacks
```

Distribution participant direct losses remain before Cleave target settlement according to Stage9 partition contract.

Cleave still does not re-enter standard base formula/modifier/crit stages.

---

## 13. Chain / Counter mapping

Counter standard damage already flows through `DamageInstanceCoordinator`, so it reaches the shared aftermath port through the standard route.

`CHAIN_TRUE_FEEDBACK` is a restricted Stage9 settlement identity. Stage10 may classify it through the common aftermath fact model for consistency/audit, but Stage9 permission remains:

```text
FIRST_AID = NOT PERMITTED
```

Stage10 does not widen restricted Chain feedback merely for code uniformity.

---

## 14. Recovery mapping

`RecoveryOpportunitySystem` is the only Stage10 opportunity executor.

It owns:

```text
opportunity validation
skill-active gate
simulator probability draw
frozen potency resolution
RecoveryRequest creation
RecoverySystem call
```

`RecoverySystem` still owns:

```text
target defeated permission
healing ban
recovery result semantics
```

`TroopSystem` still owns actual restore/cap.

Full troops do not short-circuit opportunity admission.

---

## 15. Simulator RNG mapping

Official hidden draw consumption is unknown.

R1-C simulator policy:

```text
one context.random.chance(probability)
per admitted RecoveryOpportunity
including p=0 / p=1 and zero recoverable gap
```

This is `ENGINEERING DETERMINISM`, not a Gameplay Authority rule.

---

## 16. Composition / cycle boundary

Safe dependency chain:

```text
DamageInstanceCoordinator
→ DamageAftermathSystem
→ TriggerSystem
→ RecoveryOpportunitySystem
→ RecoverySystem
→ TroopSystem
```

There is no edge from aftermath back through EffectExecutor to DamageInstanceCoordinator.

AfterDamage Trigger collection is restricted to `RecoveryOpportunity` intent.

The existing Stage9 one-time typed `DamageResolutionSystem.bind_coordinator()` permit-validation binding is retained; Stage10 adds no new service locator or lambda cycle.

---

## 17. Migration boundary

```text
PeriodicDamageStateParams
→ TEST-ONLY LEGACY SYNTHETIC after Stage10 build

PeriodicRecoveryStateParams
→ TEST-ONLY LEGACY SYNTHETIC after Stage10 build

cleave_first_aid
→ DELETE FROM PRODUCTION COMPOSITION
```

Official Stage10 state definitions use new typed persistent params/generation snapshots only.

---

## 18. Mapping verdict

```text
Stage7 death conflict              = explicit compatibility reopen
Stage8 live-source incompatibility = explicit frozen-input compatibility lane
PRE_BATTLE lifecycle gap           = closed
physical expiry ambiguity          = closed
fatal cleanup ownership            = closed
SkillRuntime lookup gap            = closed
FIRST_AID zero-loss mapping        = corrected
full-troop opportunity mapping     = corrected
RNG hidden-authority ambiguity     = isolated as engineering policy
Cleave aftermath duplication       = closed by shared port
constructor/runtime dependency DAG = explicitly bounded

Production code change in R1-C = NONE
Next gate                      = Independent Design Re-Audit Round 2
```
