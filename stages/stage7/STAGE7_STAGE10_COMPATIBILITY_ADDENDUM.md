# Stage 7 → Stage 10 Compatibility Addendum

> Project: 三国志战略版战斗模拟器 V2  
> Scope: Stage10 persistent-state compatibility  
> Status: `LIMITED COMPATIBILITY REOPEN / DESIGN ADDENDUM`  
> Production implementation: `NOT AUTHORIZED BY THIS DOCUMENT`
>
> Original Stage7 freeze remains authoritative except for the explicitly reopened clauses below.

---

## 1. Original contract

Stage7 froze the following hook topology:

```text
RuleHook
→ TriggerSystem.collect()
→ one deterministic ordered Effect tuple
→ RuleHookSystem
→ EffectExecutor
→ HookResolutionResult
```

and the original atomic-batch engineering rule was:

```text
collect once
→ execute every collected Effect in order
→ only after the complete tuple
→ BattleEngine checks Victory
```

Therefore an earlier Effect could defeat the hook actor while later Effects from the same owner-state batch still executed.

Stage7 also used ordinary `Effect` as the only hook intent family because Stage7 periodic recovery could already be represented by a concrete `RecoverEffect`.

Both rules were valid Stage7 engineering defaults before Stage10 supplied persistent-state death authority and probability-bearing recovery opportunities.

---

## 2. Conflicts discovered by Stage10

### 2.1 Target defeat hard boundary

Frozen persistent-state authority requires:

```text
TARGET_DEATH
→ CLEAR_ALL_STATES
→ ABORT_REMAINING_STATE_RESOLUTION
→ ABORT_REMAINING_ACTION
→ REJECT_FUTURE_STATE_APPLICATION
```

Consequently this sequence is incompatible:

```text
Effect A from owner-state resolution
→ owner reaches 0 troops
→ Effect B from the same owner-state resolution still executes
```

### 2.2 Probability-bearing recovery intent

Stage10 recovery opportunity semantics require:

```text
TriggerSystem
→ identify opportunity
→ NO RNG inside TriggerSystem
→ probability owned by RecoveryOpportunitySystem
→ only successful opportunity reaches RecoverySystem
```

Therefore Stage10 cannot force every recovery opportunity to become a `RecoverEffect` at collection time without either consuming RNG inside TriggerSystem or creating a fake recovery request before chance resolution.

---

## 3. Reopened surface

Only the following Stage7 surfaces are reopened for Stage10 compatibility:

```text
1. per-intent execution-right validation inside hook orchestration
2. owner-defeat abort semantics for the remaining state-resolution tail
3. HookResolutionResult representation of an aborted tail
4. synchronous cooperation with the Stage10 authoritative defeat-cleanup port
5. hook intent/result type closure so RecoveryOpportunity can be a sibling typed intent
```

The following Stage7 surfaces remain frozen and are **not** reopened:

```text
TriggerSystem purity
TriggerSystem one-shot collection
EventBus = observation only
StateLifecycleSystem = unique state-mutation owner
EffectExecutor = ordinary typed Effect router
RecoverySystem ownership
TroopSystem = unique troop mutation owner
BattleEngine ignorance of concrete state ids
rule-hook deterministic ordering
state provenance pairing
```

---

## 4. New deterministic hook compatibility rule

### 4.1 One pre-collection pass remains

`TriggerSystem.collect()` still runs once per hook and produces one immutable deterministically ordered batch.

Stage10 generalizes the batch element type from only `Effect` to a typed rule intent union:

```text
RuleIntent
= Effect
| RecoveryOpportunity
```

Equivalent concrete type names are allowed, but untyped dictionaries or callback objects are not.

A defeat does **not** cause a second collection pass and does not reorder surviving work.

```text
Stage7 Hook batch remains deterministic
BUT
target defeat is a hard execution boundary
```

### 4.2 Routing owner is explicit

`RuleHookSystem` owns ordered dispatch:

```text
Effect
→ EffectExecutor

RecoveryOpportunity
→ RecoveryOpportunitySystem
```

`EffectExecutor` remains an ordinary Effect router and does not absorb recovery probability policy.

`TriggerSystem` must not call either executor.

### 4.3 Execution right is revalidated before every intent

Before dispatching each intent, orchestration obtains a typed decision from `ExecutionRightSystem` or an equivalent typed port:

```text
RuleIntentExecutionRightDecision
- ALLOWED
- OWNER_DEFEATED
- TARGET_DEFEATED
- BATTLE_FINALIZED
- other already-frozen explicit denial reason when applicable
```

For Stage10 persistent-state intent, the execution subject is the immutable state-application-generation snapshot carried by the generated intent. The check must never JIT-read a refreshed `StateInstance` merely to recover old provenance.

`RuleHookSystem` owns whether the remaining owner-state resolution tail is aborted.

---

## 5. Authoritative defeat signal

The hard boundary is driven by the synchronous typed defeat transition owned by Stage10's authoritative defeat-cleanup port, not by EventBus subscription.

Conceptually:

```text
TroopSystem mutation
→ death edge detected by destructive settlement owner
→ DefeatCleanupPort.commit_defeat(...)
→ StateLifecycleSystem.clear_owner_on_defeat(...)
→ ExecutionRightSystem observes/derives OWNER_DEFEATED
→ control returns synchronously to current resolver
```

`UNIT_DEFEATED`, `STATE_REMOVED`, and related EventBus facts are observation products only. No subscriber may perform cleanup or abort the hook.

---

## 6. Batch-abort ownership

`RuleHookSystem` owns the hook-level decision:

```text
if a just-completed intent causes the hook actor / state-resolution owner to be defeated:
    batch state = ABORTED_BY_TARGET_DEFEAT
    do not execute remaining STATE_RESOLUTION intents for that owner
```

For the Stage10 `UNIT_ACTION_START` persistent-state path, all owner-state intents for that actor share the same hard owner-death boundary.

Future hooks that mix unrelated non-state domains must not treat this addendum as a universal "cancel every arbitrary intent after any death" rule. Each intent still receives its own execution-right validation; only the defeated owner's state-resolution tail is covered by this compatibility reopen.

The subsequent normal action is separately denied because the defeated actor has no action execution right.

---

## 7. HookResolutionResult compatibility extension

Stage7's auditability property remains: one observable outcome per originally collected intent.

The result union becomes conceptually:

```text
RuleIntentResult
= EffectExecutionResult
| RecoveryOpportunityResult
| AbortedRuleIntentResult
```

with an aborted variant equivalent to:

```text
AbortedRuleIntentResult
- intent: RuleIntent
- status: ABORTED
- reason: TARGET_DEFEATED
```

`HookResolutionResult` carries:

```text
HookResolutionResult
- hook
- intent_results: tuple[RuleIntentResult, ...]
- batch_status: COMPLETED | ABORTED_BY_TARGET_DEFEAT
- aborting_intent_index: int | None
```

Backward compatibility may expose the old Stage7 `effect_results` as a projection containing only ordinary Effect outcomes, but it is not the complete Stage10 result truth.

Required invariant:

```text
len(intent_results)
== len(TriggerSystem.collect(...) output)
```

and after an abort:

```text
completed prefix
→ ordinary typed results

aborting intent
→ ordinary result that caused/observed the death edge

remaining owner-state intents
→ AbortedRuleIntentResult(reason=TARGET_DEFEATED)
→ no executor called for those intents
```

---

## 8. Already-generated remaining intents

Intents generated before defeat remain immutable historical intent objects.

After the hard boundary:

```text
they are NOT mutated
they are NOT rebound to another state generation
they are NOT retried
they are NOT executed
they are represented only by typed aborted outcomes
```

The batch is discarded when the hook result scope ends.

---

## 9. StateLifecycleSystem cooperation

StateLifecycleSystem remains the sole physical state mutation owner.

Stage10 may add a typed method equivalent to:

```text
clear_owner_on_defeat(context, owner_id, defeat_ref)
→ DefeatStateCleanupResult
```

but that method remains inside `StateLifecycleSystem`; the defeat port coordinates it and does not remove registry entries directly.

The clear operation must:

```text
- identify every physically attached state for owner_id
- remove them in deterministic instance_id order
- publish observation facts after each physical mutation
- reject no state merely because it belongs to an older Stage
```

No individual persistent-state resolver may duplicate death cleanup.

---

## 10. State-removal event semantics on defeat

Natural expiry and defeat cleanup are distinct facts.

Stage10 compatibility chooses:

```text
natural lifecycle expiry
→ STATE_EXPIRED

defeat cleanup
→ STATE_REMOVED with typed removal_reason = OWNER_DEFEATED
```

A dedicated alternative event would require its own later repository-wide audit. R1-C does not add one.

Ordering is deterministic by `instance_id` and events remain observation-only.

---

## 11. AFTER_DAMAGE boundary

Stage10 does not turn EventBus into a new Stage7 rule-hook driver.

For FIRST_AID, the authoritative Stage9 settlement owner calls a shared typed `DamageAftermathPort`. That port may use a dedicated pure TriggerSystem collection method for `RecoveryOpportunity`, but it does **not** route through EventBus and it may not return ordinary damage/state-mutation Effects.

This preserves the Stage7 principle:

```text
TriggerSystem = pure intent collection
EventBus      = facts only
```

while avoiding a runtime dependency cycle back into `DamageInstanceCoordinator`.

---

## 12. Unaffected Stage7 behavior

This addendum does **not** authorize changes to:

```text
Recovery precedence
healing-ban semantics
ROUND_START hook timing
UNIT_ACTION_START fact publication
ordinary Effect type routing
VictorySystem ownership
EventBus control-flow policy
```

It also does not make Stage10 production states executable. Evidence-Gate promotion remains a separate Stage10 build obligation.

---

## 13. Regression obligation

Future implementation must prove at minimum:

```text
1. owner-state intent A defeats owner
   → owner states cleared synchronously
   → remaining owner-state intent B is ABORTED, not executed

2. same hook without death
   → deterministic Stage7 ordering preserved

3. RecoveryOpportunity
   → TriggerSystem consumes no RNG
   → RuleHookSystem routes it once to RecoveryOpportunitySystem

4. unrelated non-state intent domain
   → not silently cancelled merely because this addendum exists

5. EventBus observer changes
   → cannot alter gameplay cleanup or abort behavior

6. natural expiry
   → STATE_EXPIRED remains distinct from OWNER_DEFEATED removal
```

---

## 14. Compatibility verdict

```text
Stage7 original freeze                        = STILL AUTHORITATIVE
execute-all owner-state tail after defeat     = REOPENED ONLY FOR TARGET-DEFEAT BOUNDARY
hook intent union                             = LIMITED EXTENSION FOR RECOVERY OPPORTUNITY
TriggerSystem purity                          = UNCHANGED
EventBus observation-only                     = UNCHANGED
State mutation owner                          = UNCHANGED
EffectExecutor ordinary-Effect ownership      = UNCHANGED
Production implementation                     = NOT AUTHORIZED
Independent Stage10 re-audit                  = REQUIRED
```
