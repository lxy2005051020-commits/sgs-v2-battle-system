# Stage 7 → Stage 10 Compatibility Addendum

> Project: 三国志战略版战斗模拟器 V2  
> Scope: Stage10 persistent-state death hard-boundary compatibility  
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

That rule was valid as a Stage7 engineering default before the persistent-state family authority existed.

---

## 2. Conflict discovered by Stage10

The frozen continuous-state family authority now supplies a stronger gameplay boundary:

```text
TARGET_DEATH
→ CLEAR_ALL_STATES
→ ABORT_REMAINING_STATE_RESOLUTION
→ ABORT_REMAINING_ACTION
→ REJECT_FUTURE_STATE_APPLICATION
```

Consequently this sequence is no longer compatible:

```text
Effect A from owner-state resolution
→ owner reaches 0 troops
→ Effect B from the same owner-state resolution still executes
```

The Stage7 deterministic ordering rule is retained, but target defeat becomes a hard execution boundary.

---

## 3. Reopened surface

Only the following Stage7 clauses are reopened for Stage10 compatibility:

```text
1. per-Effect execution-right validation inside RuleHookSystem/EffectExecutor orchestration
2. owner-defeat abort semantics for the remaining state-resolution tail
3. HookResolutionResult representation of an aborted tail
4. synchronous cooperation with the Stage10 authoritative defeat-cleanup port
```

The following Stage7 surfaces remain frozen and are **not** reopened:

```text
TriggerSystem purity
TriggerSystem one-shot collection
EventBus = observation only
StateLifecycleSystem = unique state-mutation owner
EffectExecutor = typed Effect router
RecoverySystem ownership
TroopSystem = unique troop mutation owner
BattleEngine ignorance of concrete state ids
rule-hook deterministic ordering
state provenance pairing
```

---

## 4. New compatibility rule

### 4.1 Deterministic pre-collection remains

`TriggerSystem.collect()` still runs once per hook and produces one immutable ordered tuple.

A defeat does **not** cause a second collection pass and does not reorder surviving work.

```text
Stage7 Hook batch remains deterministic
BUT
target defeat is a hard execution boundary
```

### 4.2 Execution right is revalidated before every Effect

`EffectExecutor` must not assume that execution rights observed when the tuple was collected are still valid when an Effect reaches the head of the queue.

Before dispatching each Effect, orchestration obtains a typed decision from `ExecutionRightSystem` (or an equivalent typed port):

```text
EffectExecutionRightDecision
- ALLOWED
- OWNER_DEFEATED
- TARGET_DEFEATED
- BATTLE_FINALIZED
- other already-frozen explicit denial reason when applicable
```

For Stage10 persistent-state Effects, the execution subject is the immutable state-application generation owner carried by the generated Effect snapshot. The check must never JIT-read a refreshed `StateInstance` merely to recover provenance.

`EffectExecutor` may perform the final per-effect validation, but **RuleHookSystem owns whether the remaining state-resolution tail is aborted**.

### 4.3 Authoritative defeat signal

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

`UNIT_DEFEATED`, `STATE_REMOVED`, and related EventBus facts are observation products only. No subscriber may perform the cleanup or abort the hook.

---

## 5. Batch-abort ownership

`RuleHookSystem` owns the hook-level decision:

```text
if a just-completed Effect causes the hook actor / state-resolution owner to be defeated:
    batch state = ABORTED_BY_TARGET_DEFEAT
    do not execute remaining STATE_RESOLUTION Effects for that owner
```

For the current Stage7 `UNIT_ACTION_START` periodic-state path, all collected periodic Effects belong to the actor's state-resolution domain, so owner defeat aborts the remaining tail.

Future hooks that mix unrelated non-state domains must not treat this addendum as a universal "cancel every arbitrary Effect after any death" rule. Each Effect still receives its own execution-right validation; only the owner-scoped state-resolution tail is covered by this compatibility reopen.

The subsequent normal action is separately denied because the defeated actor has no action execution right.

---

## 6. HookResolutionResult compatibility extension

Stage7's result keeps one observable outcome per originally collected Effect so deterministic auditing remains possible.

The result union is extended with a typed aborted variant equivalent to:

```text
EffectAbortedResult
- effect: Effect
- status: ABORTED
- reason: TARGET_DEFEATED
```

`HookResolutionResult` is correspondingly extended with typed batch metadata equivalent to:

```text
HookResolutionResult
- hook
- effect_results: tuple[EffectExecutionResult | EffectAbortedResult, ...]
- batch_status: COMPLETED | ABORTED_BY_TARGET_DEFEAT
- aborting_effect_index: int | None
```

Required invariants:

```text
len(effect_results)
== len(TriggerSystem.collect(...) output)

results before abort index
→ ordinary executed results

aborting Effect
→ ordinary executed result that caused/observed the death edge

remaining owner-state Effects
→ EffectAbortedResult(reason=TARGET_DEFEATED)
→ EffectExecutor is NOT called for those Effects
```

This preserves the original Stage7 cardinality/audit property without pretending skipped work executed.

---

## 7. Already-generated remaining Effects

Effects generated before the defeat remain immutable historical intent objects.

After the hard boundary:

```text
they are NOT mutated
they are NOT rebound to another state generation
they are NOT retried
they are NOT executed
they are represented only by typed aborted outcomes
```

The tuple is discarded when the hook result scope ends.

---

## 8. StateLifecycleSystem cooperation

StateLifecycleSystem remains the sole physical state mutation owner.

Stage10 may add a typed method equivalent to:

```text
clear_owner_on_defeat(context, owner_id, defeat_ref)
→ DefeatStateCleanupResult
```

but that method must remain inside `StateLifecycleSystem`; the defeat port coordinates it and does not remove registry entries directly.

The clear operation must:

```text
- identify every physically attached state for owner_id
- remove them in deterministic instance_id order
- publish observation facts after each physical mutation
- reject no state merely because it belongs to an older Stage
```

No individual persistent-state resolver may duplicate death cleanup.

---

## 9. State-removal event semantics on defeat

Natural expiry and defeat cleanup are distinct facts.

Stage10 compatibility freezes:

```text
natural lifecycle expiry
→ STATE_EXPIRED

defeat cleanup
→ STATE_REMOVED with typed removal_reason = OWNER_DEFEATED
```

An equivalent dedicated `STATE_CLEARED_ON_DEFEAT` event is acceptable only if the independent re-audit explicitly approves a repository-wide event migration. R1-C chooses the backward-compatible `STATE_REMOVED + removal_reason` model.

Ordering is deterministic by `instance_id` and the events remain observation-only.

---

## 10. Unaffected Stage7 behavior

This addendum does **not** authorize changes to:

```text
Recovery precedence
healing-ban semantics
ROUND_START hook timing
UNIT_ACTION_START fact publication
existing Effect type routing other than the typed abort extension
VictorySystem ownership
EventBus control-flow policy
```

It also does not make Stage10 production states executable. Evidence-Gate promotion remains a separate Stage10 design/build obligation.

---

## 11. Regression obligation

Future implementation must prove at minimum:

```text
1. owner-state Effect A defeats owner
   → owner states cleared synchronously
   → remaining owner-state Effect B is ABORTED, not executed

2. same hook without death
   → exact Stage7 ordering and result cardinality preserved

3. unrelated non-state Effect domain
   → not silently cancelled merely because this addendum exists

4. EventBus observer removal/subscription changes
   → cannot alter gameplay cleanup or abort behavior

5. natural expiry
   → STATE_EXPIRED remains distinct from OWNER_DEFEATED removal
```

---

## 12. Compatibility verdict

```text
Stage7 original freeze                       = STILL AUTHORITATIVE
Stage7 execute-all owner-state tail rule     = REOPENED ONLY FOR TARGET-DEFEAT BOUNDARY
TriggerSystem purity                         = UNCHANGED
EventBus observation-only                    = UNCHANGED
State mutation owner                         = UNCHANGED
Production implementation                    = NOT AUTHORIZED
Independent Stage10 re-audit                 = REQUIRED
```
