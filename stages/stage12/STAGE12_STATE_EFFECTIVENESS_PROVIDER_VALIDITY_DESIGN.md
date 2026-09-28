# Stage12 State Effectiveness / Provider Validity / Dependency Cycle Design

Date: 2026-09-27  
Round: `STAGE12_SF_ROUND3_EFFECTIVENESS_PROVIDER_VALIDITY_DESIGN`  
Status: **DESIGN FROZEN FOR DQ-SF-02 / 03 / 08 / 20; SHARED FOUNDATION NOT YET FROZEN**  
Gameplay implementation in this round: **NONE**

## 1. Repository and authority boundary

Round 3 starts from:

- Battle main: `6ea6bc1ec7f920fa7d634e597a5b0f3ad524b140`
- Research main: `e18ae56a4db5662b87458dfa8fdff25dcdd8053b`
- Round 2 authority migration and Provider identity design are inherited without re-litigation.
- StateRegistry remains storage only.
- StateLifecycleSystem remains the sole physical state mutation / expiry / removal owner.
- EffectSourceRef remains provenance, not a live dependency.

The goal of this document is one canonical effective truth that is composable, resumable and cycle-safe.

## 2. Canonical owners

### StateEffectivenessPolicy

`StateEffectivenessPolicy` is the single canonical owner of the question:

> Given a physically resident StateInstance, does that instance currently own the gameplay authority granted by its contract?

Equivalent API:

```text
evaluate_state(context, state_instance) -> StateEffectivenessDecision
has_effective(context, owner_id, state_id) -> bool
effective_instances(context, owner_id, state_id) -> tuple[StateInstance, ...]
```

The convenience queries MUST derive from `evaluate_state`; they may not create another truth.

### ProviderValidityPolicy

`ProviderValidityPolicy` is the single canonical owner of:

> Given a stable ProviderRef, is that provider currently eligible to produce, maintain or participate in contract-authorized behavior?

Equivalent API:

```text
evaluate_provider(context, provider_ref) -> ProviderValidityDecision
```

Provider identity resolution remains owned by the relevant registry/resolver. Validity consumes identity facts; it does not redefine identity.

### EffectivenessTransitionCoordinator

A small shared transition coordinator is necessary, but it is **not** a policy owner.

It may:

- compute an affected reverse-dependency closure;
- compare pre/post decisions during one transition wave;
- order dependent re-evaluation;
- surface typed internal transition facts;
- synchronously call domain-owned transition ports such as future preparation interruption.

It MUST NOT own:

- StateRegistry;
- StateLifecycleSystem;
- ActionSystem;
- DamageSystem;
- RecoverySystem;
- TargetSystem;
- RNG;
- Provider identity;
- EventBus permission decisions.

EventBus may publish a result only after the owning policy/domain has decided it.

## 3. Resident / Effective / Suppressed / Removed

The four words name different facts:

```text
Resident
= physical StateInstance exists in StateRegistry.

Effective
= the resident instance currently owns its contract-defined gameplay authority.

Suppressed
= the instance is Resident, but one or more reversible external suppression causes currently deny that authority.

Removed
= no physical StateInstance exists in StateRegistry.
```

Invariants:

```text
Resident != Effective
Suppressed != Removed
Removed is not a StateEffectivenessDecision status.
```

A removed/non-resident instance is outside query semantics. Query by a missing instance id must fail explicitly at the residency boundary rather than returning a fake `REMOVED` decision.

## 4. StateEffectivenessDecision

Minimum serializable decision:

```text
StateEffectivenessStatus:
    EFFECTIVE
    SUPPRESSED
    INACTIVE

StateEffectivenessDecision:
    state_instance_id
    application_generation_id
    status
    suppression_causes: tuple[SuppressionCause, ...]
    inactivity_causes: tuple[InactivityCause, ...]
```

Rules:

- EFFECTIVE: no blocker exists.
- SUPPRESSED: at least one reversible external suppression cause exists and no non-suppression inactivity blocker exists.
- INACTIVE: a state-local/domain blocker exists, for example an explicitly modeled source-inadmissible or depleted-use condition. Suppression causes may also be reported diagnostically.
- `effective == (status == EFFECTIVE)`.
- Provocation source admissibility is not renamed “Insight-style suppression”. Shared state-level source-liveness blockers can be typed as inactivity; fine-grained target-operation admissibility remains DQ-SF-09.
- Stage11 remaining-use and source-dependent checks become local rule adapters feeding this policy, rather than remaining a second effective truth.

No decision object contains a Python function, pointer, closure or mutable list.

## 5. SuppressionCause identity and composition

Suppression is semantically a set of independent causes.

Minimum cause identity is a stable value-object union such as:

```text
StateCauseRef(
    state_instance_id,
    application_generation_id,
)

ProviderCauseRef(
    provider_ref,
)

LocalRuleCauseRef(
    subject_key,
)

SuppressionCause(
    rule_id,
    source_ref,   # one of the stable refs above
)
```

Why state id alone is forbidden:

- two StateInstances with the same state_id can be distinct sources;
- refresh may preserve physical instance_id while changing application generation;
- generation provenance must remain attributable even when net effective status does not change.

Cause ordering has no gameplay meaning. Implementations may deterministically sort stable serialized keys, but composition semantics are set semantics.

Removing one cause resumes authority only if **all** other blockers are gone.

## 6. Derived suppression, not mutable target flags

Canonical suppression composition is query-time derived.

Do **not** store a universal mutable list like:

```text
state.suppressors.append(...)
provider.enabled = False
```

The canonical model is:

```text
baseline fact
+ current resident/effective suppressor states
+ explicit bindings/dependencies
→ derived current decision
```

Materialized facts are allowed only when they are actual gameplay facts, for example Intimidation's selected `ProviderRef` binding. That binding is not itself a mutable list of current suppressors.

This avoids the classic bug:

```text
A suppresses P
B suppresses P
A ends
incorrectly set P.enabled = True
```

## 7. State lifetime is independent from effectiveness

Global invariant:

```text
suppression does not pause lifecycle
```

unless a future mechanism contract explicitly freezes such a pause.

Therefore:

- Insight suppressing Confusion does not pause Confusion duration.
- FalseReport/Capture/Intimidation suspension does not reset dependent effect lifetime.
- A suppressed state that expires is removed by StateLifecycleSystem.
- Removing the suppressor later cannot resurrect the removed instance.
- Resume means future eligibility only. It never replays missed triggers, reruns past activation, restores consumed RNG, rolls back settled damage/recovery, or restarts an expired timer.

Lifecycle clock owner remains distinct from effectiveness owner.

## 8. ProviderValidityDecision

Minimum public Provider validity states:

```text
VALID
SUPPRESSED
BASELINE_DISABLED
MISSING
IDENTITY_MISMATCH
```

Minimum serializable result:

```text
ProviderValidityDecision:
    provider_ref
    status
    suppression_causes: tuple[SuppressionCause, ...]
```

Evaluation order:

1. resolve ProviderRef identity;
2. if absent → MISSING;
3. if stable expected identity no longer matches → IDENTITY_MISMATCH;
4. if the physical/runtime baseline is disabled → BASELINE_DISABLED;
5. derive all currently effective suppression causes;
6. one or more causes → SUPPRESSED;
7. otherwise → VALID.

`SkillRuntime.enabled` is baseline configuration only. Transient Stage12 suppression MUST NOT mutate it.

Owner defeat is not a universal identity or validity failure. Source/owner liveness affects a state/provider only through an explicit contract dependency.

EquipmentProviderRef remains part of typed ProviderRef, but DQ-SF-11 still owns the equipment-specific baseline/effectiveness adapter. Round 3 does not invent an equipment subsystem.

## 9. Explicit ProviderDependency

Attribution is not dependency.

A state/effect that must remain live only while a Provider is currently valid records an explicit value object such as:

```text
ProviderDependency(
    provider_ref,
    rule_id,
)
```

No consumer may infer this from `source_id`, `source_skill_id`, `source_skill_slot` or EffectSourceRef alone.

For an explicit live dependency:

- Provider VALID → dependency satisfied.
- Provider SUPPRESSED → dependent state/effect becomes temporarily ineffective according to its contract.
- BASELINE_DISABLED / MISSING / IDENTITY_MISMATCH are typed non-valid outcomes; the dependent state does not silently rebind.
- Physical state residency remains independent unless its own lifecycle says otherwise.

This preserves Provider / Holder / Source separation.

## 10. Insight protected-control model

Protected-control suppression is generic by taxonomy, not a state-id ladder in each consumer.

Required behavior:

```text
Confusion resident
Insight effective
→ Confusion resident + suppressed

Insight ceases first
→ same Confusion instance resumes if still resident/alive

Confusion expires first
→ Lifecycle removes Confusion
→ later Insight removal does not resurrect it
```

The same protected-control suppression framework covers the frozen protected taxonomy, including Taunt, Disarm, Stun, Exhaustion, Weakness, Healing Ban, Provocation and Sabotage where the Insight contract says so.

Protection always asks for **effective Insight**, never resident Insight.

Therefore:

```text
FalseReport
→ Insight Provider SUPPRESSED
→ Insight resident but ineffective
→ controls whose only blocker was that Insight resume
```

When the Provider later returns VALID:

```text
same Insight instance becomes effective
→ protection returns
→ still-live protected controls become suppressed again
```

No state is reapplied and no timer is reset.

## 11. Provider suppression models

### FalseReport

For a Provider owned by the FalseReport holder:

- effective FalseReport contributes a suppression cause to verified PASSIVE and COMMAND Skill Providers;
- unrelated Provider categories are not generalized;
- tested equipment-special behavior remains routed through DQ-SF-11;
- Provider removal/expiry of FalseReport removes only that cause;
- still-live dependent effects resume future behavior only.

### Intimidation

Intimidation stores one stable selected `ProviderRef`.

If Intimidation is effective, it contributes a suppression cause only to that bound Provider.

If Intimidation becomes ineffective:

- the binding is preserved;
- the selected Provider loses this cause;
- no reroll occurs.

If the same Intimidation becomes effective again:

- the same binding contributes suppression again;
- no reroll/reapplication occurs.

Refresh transaction and RNG ownership remain DQ-SF-22 / DQ-SF-12.

### Capture

Effective Capture contributes suppression causes to the verified PASSIVE / COMMAND Provider categories.

It does not delete skills, unload SkillRuntime, or rewrite Provider identity.

Capture removal removes only its own cause. If FalseReport or another independent cause still exists, the Provider remains SUPPRESSED.

Source death of an already established Capture does not remove it under the frozen Capture contract.

## 12. Provider / Holder separation

Example:

```text
Provider A owns effect E
E resides on Holder B
```

If E has explicit ProviderDependency(A):

```text
A SUPPRESSED
→ E becomes ineffective according to E's dependency rule
```

This does not imply:

- B's unrelated Providers are suppressed;
- a FalseReport resident on B suppresses remote Provider A;
- every effect attributed to A has a live dependency on A.

Only explicit ownership/dependency edges propagate.

## 13. Dependency graph

Runtime evaluation uses an explicit directed graph.

Node types:

```text
StateNode(instance_id)
ProviderNode(provider_ref)
```

Edge direction is **consumer → prerequisite**:

```text
Insight StateNode → its explicit ProviderNode
Confusion StateNode → effective Insight StateNode(s)
Provider P → effective FalseReport/Capture/Intimidation StateNode(s) that can suppress P
```

The reverse index is used for propagation:

```text
prerequisite changed
→ find dependents
→ re-evaluate affected closure
```

Each evaluation session owns:

- memoized node decisions;
- a visiting stack/set;
- deterministic node keys for diagnostics.

Duplicate edges are deduplicated semantically.

## 14. Cycle policy — DQ-SF-20

Cycles are unsupported, not auto-solved.

Forbidden behavior:

```text
iterate until stable
last writer wins
default allow
default deny
ordinary recursion until RecursionError
```

Required behavior:

```text
if evaluation encounters an already-visiting node:
    raise DependencyCycleError(cycle_path)
```

No boolean gameplay truth is returned for that cycle.

Any transition that adds or changes explicit dependency topology must validate the affected graph before committing the dependency-changing transition. DQ-SF-22 will own the eventual atomic transaction integration.

If a migrated/preloaded battle already contains a cycle, bootstrap/evaluation fails explicitly rather than silently choosing semantics.

Because no gameplay fallback is chosen, Round 3 adds no Runtime Default Ledger entry for cycle outcome.

## 15. Transition versus query

Query-time decisions remain canonical, but query alone is insufficient for immediate consequences.

Examples requiring transition awareness:

- Exhaustion becomes effective while a preparation is in progress;
- Intimidation becomes effective and its bound Provider must be interrupted/suspended;
- Insight becomes effective and existing protected controls lose authority;
- Insight becomes ineffective and still-live protected controls regain authority.

The transition coordinator therefore compares decision snapshots across a mutation/transition wave.

It may create internal facts equivalent to:

```text
StateEffectiveChanged(old, new)
ProviderValidityChanged(old, new)
```

These are internal coordination facts, not newly frozen EventType values.

DQ-SF-13 still owns whether public/observable `STATE_SUPPRESSED`, `STATE_RESUMED`, `PROVIDER_SUPPRESSED`, or `PROVIDER_RESUMED` events are needed.

Repeated identical queries emit nothing.

## 16. Stage9 migration

Stage9 keeps domain-specific arbitration. It stops owning shared effective truth.

Method-level plan:

- `has_operational_insight` → delegate to `StateEffectivenessPolicy.has_effective(... INSIGHT)`.
- `get_operational_confusion` → read resident Confusion, return only an EFFECTIVE shared decision.
- `get_taunt_suppressors` → stop using `Registry.has(INSIGHT)`; consume shared suppression/effective Insight truth.
- `get_taunt_lifecycle_state` → map shared decision to Stage9's local TAUNT ACTIVE/SUPPRESSED representation as a compatibility façade.
- `is_taunt_operational` → shared effectiveness first, then retain Stage9-specific target/source alive arbitration.
- Guard, damage-share, distribution, chain, counter, target identity and other Stage9-specific arbitration remain Stage9-owned.

Round 2's narrow Insight × Confusion authority supersession remains the only historical rule migration required here.

## 17. Stage11 migration

Stage11 keeps damage/hit/recovery/domain arbitration. It stops computing a second canonical effectiveness truth.

Method-level plan:

- `Stage11StateRuntime.instances` remains a resident read/order helper.
- `is_effective` becomes a thin delegate to `StateEffectivenessPolicy.evaluate_state`.
- `effective_instances` and `has_effective` derive only from the shared policy.
- current `runtime_params.is_suppressed` compatibility, `source_dependent`, remaining-use and remaining-block checks migrate into typed local rule adapters consumed by StateEffectivenessPolicy.
- Stage11's resolve-hit, critical, reduction, resistance, alert and other domain calculations keep their current ownership and merely consume shared state decisions.

No Stage11 frozen gameplay rule is contradicted by this design. Stage11 Reopen Required = NO.

## 18. Seven-state contract mapping

| State | Resident model | Effective dependency | Provider dependency | Suppression / authority target |
|---|---|---|---|---|
| INSIGHT | StateInstance until Lifecycle removal | protected by its own blockers; may become ineffective through explicit provider dependency | explicit only | protected-control states |
| EXHAUSTION | StateInstance | Insight may suppress existing Exhaustion | none inferred from provenance | future ACTIVE admission; preparation interruption is transition consumer |
| FALSE_REPORT | StateInstance | ordinary Insight does not suppress it | none inferred globally | verified PASSIVE/COMMAND Providers; tested equipment via DQ-SF-11 |
| PROVOCATION | StateInstance survives source inadmissibility | state-level source liveness may produce INACTIVE; operation-level admissibility stays DQ-SF-09 | none inferred globally | eligible skill target operations |
| INTIMIDATION | StateInstance + stable selected ProviderRef binding | if state becomes ineffective, its cause stops but binding persists | any liveness dependency must be explicit | exactly the selected ProviderRef |
| SABOTAGE | protected StateInstance | existing Sabotage may be suppressed by effective Insight | equipment dependencies explicit | tested equipment contributions/effects via DQ-SF-11 |
| CAPTURE | StateInstance; established lifecycle survives source death | ordinary Insight does not suppress Capture | none inferred from source survival | verified PASSIVE/COMMAND Providers; other composite domains remain DQ-SF-19 |

## 19. Tests required before implementation can be called complete

State effectiveness:

- resident_effective
- resident_suppressed
- removed_not_queryable
- insight_suppresses_existing_confusion
- insight_removal_resumes_live_confusion
- expired_confusion_not_resurrected
- suppressed_insight_does_not_protect_controls
- insight_resumes_then_protection_returns
- two_suppression_reasons_remove_a_still_suppressed
- two_suppression_reasons_remove_b_last_resumes

Provider validity:

- provider_exists_and_valid
- provider_baseline_disabled
- provider_suppressed
- provider_missing
- provider_identity_mismatch
- provider_a_suppressed_holder_b_effect_inactive
- provider_b_unrelated_remains_valid
- false_report_suppresses_passive_command_provider
- intimidation_only_selected_provider_suppressed
- capture_suppresses_verified_provider_categories

Dependency propagation:

- FalseReport → Insight Provider suppressed → Insight ineffective → Confusion resumes.
- FalseReport ends → same Provider valid → same Insight effective → same live Confusion suppressed again.
- No reapply, no new generation, no timer reset, no missed-trigger replay.

Cycle:

- simple acyclic dependency;
- nested dependency;
- duplicate dependency;
- cycle detected;
- cycle never recurses indefinitely;
- cycle path/outcome explicit;
- dependency-topology change rejected before commit when it would introduce a cycle.

## 20. Runtime defaults

New defaults added in Round 3: **NONE**.

Cycle semantics are an unsupported boundary, not a guessed gameplay default.

Cause-set serialization order has no gameplay authority.

Source death remains explicit-contract-only dependency behavior.

## 21. DQ verdicts

```text
DQ-SF-02 = CLOSED_BY_SHARED_FOUNDATION_DESIGN
DQ-SF-03 = CLOSED_BY_SHARED_FOUNDATION_DESIGN
DQ-SF-08 = CLOSED_BY_SHARED_FOUNDATION_DESIGN
DQ-SF-20 = CLOSED_BY_SHARED_FOUNDATION_DESIGN
```

No gameplay implementation was added.

No Stage11 reopen is required.

```text
STAGE12_SF_ROUND3_EFFECTIVENESS_PROVIDER_VALIDITY_DESIGN = PASS
Shared Foundation Design Freeze = NOT YET
Stage12 Runtime Frozen = 0 / 7
Stage13 Active = NO
```

## 22. Next design round

```text
DQ-SF-01
DQ-SF-22
DQ-SF-24
DQ-SF-25
```

Next topic:

**State Admission + Refresh Transaction + Lifecycle Clock + Removal/Cleanse Design**

That round must connect incoming state → admission → conflict → apply → refresh → suppression → expiry → removal without changing the owner decisions frozen here.
