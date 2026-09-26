# Stage12 State Lifecycle Transaction Design

Date: 2026-09-27  
Round: `STAGE12_SF_ROUND4_STATE_LIFECYCLE_TRANSACTION_DESIGN`  
Status: **DESIGN FROZEN FOR DQ-SF-01 / 22 / 24; DQ-SF-25 ARCHITECTURE CLOSED WITH CONTRACT BOUNDARIES; SHARED FOUNDATION NOT YET FROZEN**  
Gameplay implementation in this round: **NONE**

## 1. Repository and authority lock

Round 4 is designed against:

- Battle main: `91e9cbd05642344e2f6b03979b64bc1ee9cabf7e`
- Research main: `e18ae56a4db5662b87458dfa8fdff25dcdd8053b`
- Research remains read-only in this round.

Inherited owners are not reopened:

- `StateRegistry` = physical storage only.
- `StateLifecycleSystem` = sole physical state writer.
- `StateEffectivenessPolicy` = canonical current authority of a resident state.
- `ProviderValidityPolicy` = canonical current Provider validity.
- `EffectivenessTransitionCoordinator` = non-authoritative transition/dependency coordinator.
- `BattleContext.random` / RandomSystem = RNG authority.

The Round 4 invariant is:

```text
DECISION FIRST
MUTATION SECOND
ONE PHYSICAL COMMIT
```

A rejected candidate/removal request never reaches a compensating "apply then delete", "refresh then roll back", or "remove then reapply" path.

## 2. Canonical lifecycle topology

The canonical incoming-state path is:

```text
source operation
→ source-side candidate generation / source RNG where defined
→ StateCandidate validation
→ StateAdmissionPolicy
→ StateConflictPolicy
→ prepare StateApplicationTransaction
→ validate dependency topology and commit preconditions
→ consume only transaction-authorized RNG
→ freeze final transaction
→ StateLifecycleSystem physical commit
→ re-evaluate affected effectiveness/provider closure
→ synchronous domain transition ports
→ observable committed facts
```

Admission is before same-state conflict whenever the contract requires it. In particular, effective Insight rejects a protected incoming candidate before any same-state refresh/replace logic is allowed to inspect or modify an old resident instance.

## 3. StateCandidate

A candidate is not a resident state and owns no physical identity.

Minimum semantic shape:

```text
StateCandidate
    state_id
    owner_id
    source_ref / source attribution
    runtime_params_candidate
    lifetime_spec
    strength_or_priority_key?      # only when a contract actually requires comparison
    provider_dependency?          # only when explicitly contract-authorized
    application_provenance
```

Rules:

- No `instance_id` exists before physical commit.
- No `application_generation_id` exists before physical commit.
- `EffectSourceRef` remains attribution, not an inferred live dependency.
- `ProviderDependency` remains explicit.
- Candidate schema does not pre-encode every hypothetical future state feature.
- Malformed schema/unknown state IDs are preflight validation errors, not immunity decisions.

## 4. DQ-SF-01 — State Admission

### Canonical owner

`StateAdmissionPolicy` is the single pure decision owner for:

> May this already-generated incoming StateCandidate enter the state-conflict/application pipeline for this target now?

Equivalent API:

```text
evaluate_candidate(context, candidate) -> AdmissionDecision
```

Minimum decision statuses:

```text
ALLOW
REJECT_IMMUNITY
REJECT_SPECIAL_PROTECTION
REJECT_INVALID_TARGET
```

Minimum diagnostic fields:

```text
status
reason_rule_id
reason_state_instance_id?
reason_provider_ref?
```

The decision must not contain a mutation callback.

### Admission boundary

Admission owns target-side admission blockers such as:

- effective Insight rejecting incoming protected controls;
- FalseReport special-protection checks that are actually frozen;
- Intimidation special immunity boundaries;
- Sabotage special admission protections;
- Capture's explicit Insight bypass.

Admission does **not** own:

- equal/stronger same-state conflict;
- refresh/replace behavior;
- physical Registry writes;
- expiry;
- cleanse eligibility;
- target-operation policy for Provocation;
- source-side candidate-generation probability.

### Source RNG boundary

Source-side control generation is complete before target admission.

```text
probabilistic source child
→ consume its normal source-generation RNG
→ candidate exists
→ StateAdmissionPolicy
```

A deterministic source child introduces no synthetic RNG merely because the target has Insight.

Admission itself does not refund, replay, skip, or manufacture source-generation RNG.

### Rejection invariants

A rejected candidate:

- creates no resident instance;
- allocates no application generation;
- does not modify any old instance;
- does not change any old timer;
- does not replace runtime parameters;
- does not select an Intimidation binding;
- does not emit an applied-then-removed pair;
- does not abort legal sibling effects of a composite parent skill.

## 5. State conflict / reapplication policy

`StateConflictPolicy` is the pure decision owner after admission.

Equivalent API:

```text
evaluate_conflict(context, candidate, resident_matches)
    -> StateConflictDecision
```

Minimum dispositions:

```text
CREATE
REFRESH
REPLACE
REJECT_CONFLICT
UNSUPPORTED_BOUNDARY
```

There is no universal rule equivalent to:

```text
if same_state:
    refresh
```

Each state adapter must inherit a frozen contract rule or explicitly preserve a bounded unknown.

`UNSUPPORTED_BOUNDARY` is not a guessed gameplay answer. It stops the transaction before mutation and surfaces the contract debt explicitly.

## 6. DQ-SF-22 — StateApplicationTransaction

### Transaction representation

`StateApplicationTransaction` is an immutable prepared commit plan, not a second writer.

It contains only facts needed for one commit, including as applicable:

```text
disposition
candidate
expected_existing_instance_id?
expected_existing_generation_id?
new_generation_policy
final_runtime_params
final_lifetime_spec
final_provider_binding?
transition_dependency_delta
```

A non-writing `StateApplicationCoordinator` orchestrates policy calls and preparation. Only `StateLifecycleSystem` may commit the transaction to `StateRegistry`.

### Generation semantics

Frozen Shared Foundation semantics:

| Disposition | physical instance_id | application_generation_id | Meaning |
|---|---|---|---|
| CREATE | new | new | new resident physical state |
| REFRESH | same | **new** | one physical instance receives a new application generation |
| REPLACE | new | new | old physical instance terminates; a new physical instance begins |
| REJECT_* | unchanged old state | none allocated for candidate | no physical admission |

This matches the existing Lifecycle refresh architecture: refresh preserves the physical `instance_id` and advances `current_generation_id`.

The generation id is allocated only on a committed create/refresh/replace path. A rejected candidate does not consume a generation.

### Refresh atomicity

Refresh must be prepared while the old generation remains fully authoritative.

For Intimidation:

```text
old instance + old binding + old lifetime remain authoritative
→ admission succeeds
→ conflict resolves REFRESH
→ validate topology / eligible-provider input / non-RNG preconditions
→ perform one authorized provider-selection operation
→ freeze new binding + new lifetime + NEW generation request
→ one Lifecycle REFRESH commit
→ transition closure sees old-generation → new-generation change
```

If preparation fails before commit:

- old instance remains resident;
- old generation remains current;
- old timer remains unchanged;
- old binding remains authoritative;
- no released-old-binding half-state exists.

The new selection may equal the old Provider and is still a real refresh selection.

### Resume is not refresh

A resident suppressed state becoming effective again is an effectiveness transition only.

It does not:

- call refresh;
- allocate a new generation;
- reset lifetime;
- reroll Intimidation binding;
- replay missed behavior.

### Application result

Minimum typed result:

```text
APPLIED
REFRESHED
REPLACED
REJECTED_ADMISSION
REJECTED_CONFLICT
UNSUPPORTED_BOUNDARY
```

Committed results may carry the resulting `instance_id` and `application_generation_id`. Rejections carry decision diagnostics but no fake physical result.

### Failure and commit boundary

All fallible checks capable of rejecting a transaction must happen before physical commit:

- candidate structural validation;
- admission;
- conflict;
- dependency-cycle validation;
- binding input validation;
- expected existing instance/generation preconditions.

Authorized RNG is consumed only after all deterministic rejection checks are complete and immediately before final plan freeze/commit. No later gameplay-policy validation may reject the already-authorized transaction.

A post-commit transition callback is an invariant/implementation failure if it throws; it is not handled by removing/reapplying the state. Transition ports must therefore be prevalidated and designed as deterministic, synchronous consumers.

## 7. Legacy StateLifecycleSystem compatibility

Existing Stage1-11 call sites are not migrated in this design round.

Future implementation rules:

- the current public `StateLifecycleSystem.apply()` / `refresh()` compatibility behavior remains available;
- legacy conflict paths that raise `ValueError` retain that failure surface until their callers are deliberately migrated;
- Stage12 ingress uses the typed candidate/policy/transaction path;
- the new internal Lifecycle commit seam must not force old callers to reinterpret a typed rejection as success;
- no duplicate physical writer is introduced.

This round changes no gameplay code.

## 8. DQ-SF-24 — Lifecycle Clock

### Canonical clock owner

`StateLifecycleSystem` owns physical state lifetime progression. It may delegate calculation helpers, but no effectiveness/admission/removal policy advances time.

### Clock-domain taxonomy

The runtime must distinguish at least:

| Domain | Meaning | Canonical owner |
|---|---|---|
| ROUND / CALENDAR LIFETIME | state exists through defined round envelope | StateLifecycleSystem |
| HOLDER ACTION-WINDOW LIFETIME | state lifetime advances relative to holder action lifecycle | StateLifecycleSystem |
| EXPLICIT PHASE EXPIRY | existing expires_round / expires_phase style anchor | StateLifecycleSystem |
| NATURAL-ACTION BLOCK COUNTER | count of actually blocked qualifying opportunities, e.g. STUN | gameplay/domain counter via Lifecycle mutation seam |
| CONSUMABLE USE COUNTER | count decremented only when the effect is actually consumed | owning gameplay domain via Lifecycle mutation seam |
| PROVIDER-LOCAL COUNTER | Provider's own lifetime/charges | Provider owner, not generic state clock |
| SOURCE-SKILL COUNTER | source skill's own usage/lifetime | source skill owner, not generic state clock |

Physical lifetime and behavioral opportunity consumption are not synonyms.

### Stage10 persistence hazard

Stage12 state durations must **not** be represented merely by passing legacy `duration_rounds` / `lifecycle_window` into today's `StateLifecycleSystem.apply()`, because current `_is_stage10_persistent_state` treats the presence of either field as Stage10 persistence.

Future implementation must introduce explicit Stage12 lifetime metadata, equivalent to a typed `StateLifetimeSpec`, and route it through Lifecycle without entering the Stage10 persistent-state detector merely because a duration exists.

### Suppression does not pause physical lifetime

Shared invariant:

```text
SUPPRESSED != PAUSED
```

Unless a future contract explicitly freezes an exception:

- Insight-suppressed controls keep physical lifetime progression.
- FalseReport provider-dependent effects keep their own lifetime progression.
- Intimidation may expire while ineffective.
- Sabotage may expire while its effect is suppressed.
- Capture-dependent effects keep their own independent lifetimes.

### STUN discriminator

STUN `remaining_blocks` is behavioral opportunity consumption.

When STUN is suppressed by Insight:

- suppression does not globally pause unrelated physical time;
- an opportunity that STUN does not actually block does not consume a STUN block;
- therefore "clock continues" does not mean decrementing `remaining_blocks` while ineffective.

### Intimidation suspended expiry

If Intimidation expires while ineffective:

```text
Lifecycle removes Intimidation
→ its binding terminates with that state generation
→ its Provider suppression cause is absent
→ later source/provider recovery cannot resurrect the removed Intimidation
```

### FalseReport holder-relative timeline

Representative required model:

```text
FalseReport admitted
→ verified Provider suppressed
→ holder-relative lifetime progresses
→ FalseReport expires
→ same still-live Provider resumes future eligibility
→ missed triggers are not replayed
```

## 9. Same-envelope expiry / resume ordering

Research freezes the observable requirement that due expiry/suppression-source removal settle before later behavior depending on the resulting privilege, but does not prove hidden micro-order when both the suppressed state and suppressor are due in the same envelope.

Runtime therefore adopts RD-SF-003:

```text
at one lifecycle settlement envelope:
1. snapshot all states due for physical expiry/removal at that envelope;
2. commit the complete due-removal set in deterministic instance_id order;
3. only then recompute the affected effectiveness/provider closure;
4. invoke resume/suppression transition ports;
5. publish/consume later gameplay behavior.
```

A state already in the due-removal snapshot cannot transiently resume merely because its suppressor is also removed in that same envelope.

This is `PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN`.

## 10. DQ-SF-25 — Removal / Cleanse architecture

### Physical removal versus eligibility

`StateLifecycleSystem.remove()` is the physical removal primitive.

It does not decide whether a cleanse/removal operation is allowed to select a state.

`StateRemovalPolicy` is the pure canonical owner of:

> May removal operation X remove resident StateInstance Y under the relevant contract?

Equivalent API:

```text
evaluate_removal(context, operation, state_instance)
    -> RemovalDecision
```

Minimum policy result:

```text
ALLOW
REJECT_CONTRACT_PROTECTED
REJECT_INVALID_OPERATION
UNSUPPORTED_BOUNDARY
```

Diagnostics include a stable `reason_rule_id` and operation category.

### Removal operation classes

Eligibility-governed gameplay removal:

- `ORDINARY_CLEANSE`
- `SPECIALIZED_CLEANSE`
- `SCRIPTED_GAMEPLAY_REMOVE`

Lifecycle infrastructure, not ordinary cleanse selection:

- `NATURAL_EXPIRY`
- `OWNER_DEFEAT_CLEANUP`
- `BATTLE_TEARDOWN`

`SOURCE_LIFECYCLE_END` is only available when an explicit contract dependency owns that removal. Source death is never promoted to a universal state-deletion rule.

Natural expiry, owner defeat cleanup and battle teardown do not query ordinary cleanse resistance.

### State-specific removal boundaries

- CAPTURE: ordinary cleanse is rejected; same resident instance/timer remains. Source death does not remove established Capture.
- INTIMIDATION: tested generic negative-cleanse category is rejected; specialized removal remains `UNSUPPORTED_BOUNDARY`; no universal "uncleanseable" boolean.
- FALSE_REPORT: tested cleanse operations are allowed; unseen cleanse/removal classes remain evidence-scoped, not automatically allowed.
- SABOTAGE: observed cleanse/removal path is allowed only within the proven class; unobserved removal classes remain bounded.
- PROVOCATION: source death does not remove the resident state.
- INSIGHT / EXHAUSTION: removal follows their concrete contract/source lifecycle; no new universal cleanse claim is invented here.

Therefore DQ-SF-25's **architecture** closes, while mechanism-specific bounded classes remain explicitly open.

## 11. Removal transaction topology

Gameplay removal path:

```text
RemovalRequest
→ validate resident target
→ StateRemovalPolicy
→ if reject/unsupported: no mutation
→ snapshot affected decisions
→ validate dependency topology / commit preconditions
→ StateLifecycleSystem.remove(...)
→ recompute affected closure
→ synchronous transition ports
→ observable committed facts
```

Rejection preserves the exact resident instance, generation, timer and binding.

After a committed removal, downstream consequences are owned by effectiveness/provider/domain policies. RemovalPolicy itself does not "resume Confusion", "enable Provider", replay skill activation, replay damage/healing, or restore RNG.

## 12. Seven-state lifecycle mapping

| State | Admission | Conflict / refresh | Clock | Removal / cleanup |
|---|---|---|---|---|
| INSIGHT | ordinary candidate admission; its effective instance blocks protected incoming controls | PD-INS-002: any PRESENT canonical Insight rejects incoming Insight; no refresh/replace/backup, including while suppressed | source-defined holder lifecycle; suppression never pauses | normal Lifecycle removal/expiry; dependent protected controls re-evaluate; holder defeat is infrastructure cleanup |
| EXHAUSTION | effective Insight rejects incoming Exhaustion | no universal reapply rule invented; unsupported overlap remains explicit unless its source contract supplies one | physical lifetime continues while suppressed | evidence/source-lifecycle scoped; no skill-permission logic is implemented here |
| FALSE_REPORT | ordinary Insight does not reject; tested special protections may | equal-strength same/different-source incoming rejected, no refresh; stronger/weaker = unsupported bounded boundary | holder-relative action lifecycle | tested cleanse allowed; untested classes bounded; source death does not remove |
| PROVOCATION | effective Insight rejects incoming Provocation | same/different-source reapply/multisource = unsupported bounded boundary | own resident lifetime continues even if Source becomes inadmissible | Source death does not remove; later ordinary expiry/removal is physical Lifecycle work |
| INTIMIDATION | special protection checked before Provider selection; ordinary Insight does not reject | supported successful reapplication = REFRESH; same instance + new generation + newly selected binding; resume is not refresh; unsupported multisource stays bounded | observed 1-round source scope; lifetime continues while ineffective | tested generic cleanse rejected; specialized removal unsupported; expiry terminates state + binding |
| SABOTAGE | effective Insight / tested special protection can reject before conflict | observed equal-or-stronger conflict rejects incoming; no duplicate suppression; stronger different-source replacement remains bounded | physical lifetime continues under suppression | natural expiry and observed cleanse class supported; other removal classes bounded |
| CAPTURE | effective Insight does not reject verified Capture | state-core reapply/multisource Q70-Q74 unsupported; source skill owns its alternate branch | verified 20228 source supplies 2-round lifecycle; not universalized to every future source | ordinary cleanse rejected; source death does not end established Capture |

## 13. Composite-skill boundary

Admission rejects only the affected StateCandidate.

For a parent skill with independent children:

```text
damage child commits legally
protected-control child reaches admission
→ rejected by Insight
other legal siblings continue
```

`StateAdmissionPolicy` never returns "cancel parent skill".

## 14. Observable facts boundary

Round 4 does not preempt DQ-SF-13.

Existing canonical committed facts remain sufficient for architecture design:

- applied;
- refreshed;
- removed;
- expired.

Typed application/removal results distinguish admission rejection, conflict rejection and unsupported boundaries internally. Whether those become new public `EventType` values is deferred to DQ-SF-13.

EventBus records committed facts and never controls the transaction.

## 15. Required discriminator tests

Admission:

```text
insight_rejects_incoming_protected_control
rejected_candidate_never_becomes_resident
rejected_candidate_preserves_existing_state_exactly
source_rng_consumed_before_insight_admission_when_required
deterministic_control_adds_no_rng
rejected_child_does_not_abort_sibling_effect
```

Conflict / refresh:

```text
insight_reapply_rejected_no_refresh
suppressed_insight_reapply_rejected_PD_INS_002
false_report_equal_reapply_no_refresh
refresh_transaction_is_atomic
intimidation_refresh_changes_binding_only_on_commit
intimidation_resume_preserves_binding_and_timer
```

Clock:

```text
suppressed_control_clock_continues
suppressed_control_expires_and_never_resumes
stun_suppression_does_not_consume_behavior_block
intimidation_can_expire_while_suppressed
false_report_expiry_restores_provider_future_only
same_envelope_due_state_does_not_transiently_resume
```

Removal:

```text
capture_rejects_ordinary_cleanse
intimidation_generic_removal_boundary
source_death_does_not_remove_capture
holder_defeat_cleanup_not_synthetic_expiry_cascade
remove_insight_resumes_live_control
remove_false_report_propagates_provider_resume
```

Failure / compatibility:

```text
cycle_validation_failure_commits_nothing
refresh_failure_preserves_old_instance
refresh_failure_preserves_old_binding
rejected_removal_preserves_instance_and_timer
legacy_apply_failure_adapter_preserved
```

These are design obligations, not newly implemented tests in Round 4.

## 16. Stage9 / Stage11 impact

No Stage9 or Stage11 gameplay rule is changed.

Stage11 Reopen Required = **NO**.

Important compatibility facts:

- Stage11 STUN's `remaining_blocks` remains a behavioral-opportunity counter, not a generic lifetime timer.
- Stage11 existing ValueError conflict callers remain compatible.
- Stage10 persistent-state detection is not reused as the generic Stage12 clock.
- Round 3's Stage9/11 effectiveness migration remains future implementation work.

## 17. Runtime defaults

Round 4 adds exactly one Shared Foundation Runtime Default:

```text
RD-SF-003
Same-envelope lifecycle settlement ordering
PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN
```

No default is added for:

- Provocation multi-source/reapplication;
- Capture state-core reapplication;
- Intimidation specialized removal or source death;
- FalseReport stronger/weaker replacement;
- Sabotage stronger different-source replacement;
- unknown cleanse classes.

Unknown behavior is not improved by giving it a confident enum value.

## 18. DQ verdicts

```text
DQ-SF-01 = CLOSED_BY_SHARED_FOUNDATION_DESIGN
DQ-SF-22 = CLOSED_BY_SHARED_FOUNDATION_DESIGN
DQ-SF-24 = CLOSED_BY_SHARED_FOUNDATION_DESIGN
DQ-SF-25 = CONTRACT_DEPENDENT_WITH_ARCHITECTURE_CLOSED
```

The DQ-SF-25 status means the shared removal architecture is frozen while named contract-specific removal classes remain bounded/unsupported.

## 19. Round 4 exit gate

```text
STAGE12_SF_ROUND4_STATE_LIFECYCLE_TRANSACTION_DESIGN = PASS

StateRegistry remains storage-only = YES
StateLifecycleSystem remains sole physical writer = YES
StateEffectivenessPolicy unchanged as canonical effective truth = YES
ProviderValidityPolicy unchanged as canonical Provider truth = YES

admission before contract-relevant conflict = YES
refresh atomicity designed = YES
resume != refresh = YES
suppression does not pause physical lifetime = YES
cleanse eligibility != physical removal primitive = YES
source death != automatic state removal = YES

Gameplay implementation = NONE
Stage11 Reopen Required = NO
Stage12 Runtime Frozen = 0 / 7
Stage13 Active = NO
Shared Foundation Design Freeze = NOT YET
```

## 20. Next

Next design round:

```text
DQ-SF-06
DQ-SF-07
DQ-SF-21
```

Theme:

**Skill Permission + Preparation Interruption + Existing JIT Provider Gate Migration**

Round 4 does not start Stage13/14/15 gameplay.
