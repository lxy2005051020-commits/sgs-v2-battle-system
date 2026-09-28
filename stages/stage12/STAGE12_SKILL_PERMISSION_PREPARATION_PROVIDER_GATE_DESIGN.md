# Stage12 Skill Permission / Preparation Interruption / Provider Gate Design

Date: 2026-09-27  
Round: STAGE12_SF_ROUND5_SKILL_PERMISSION_PREPARATION_PROVIDER_GATE_DESIGN  
Status: **DESIGN FROZEN FOR DQ-SF-06 / DQ-SF-07 / DQ-SF-21; SHARED FOUNDATION NOT YET FROZEN**  
Gameplay implementation in this round: **NONE**

## 1. Repository lock and authority

Round 5 is audited against:

- Battle main: 77d527e4e48287bd5981d55239d5e569a9294ef6
- Research main: e18ae56a4db5662b87458dfa8fdff25dcdd8053b
- Exhaustion contract blob: c6c0a7d55b455b853b56eba6572a1a66279c8cc0
- Intimidation contract blob: 3e5eaaf4c5ac09eef3cb5c5810c68f5b01f997a1

Inherited owners are not reopened:

- StateRegistry = physical storage only.
- StateLifecycleSystem = sole physical writer and physical lifetime owner.
- StateEffectivenessPolicy = canonical resident-state gameplay-authority owner.
- ProviderValidityPolicy = canonical ProviderRef current-validity owner.
- EffectivenessTransitionCoordinator = non-authoritative synchronous transition coordinator.
- SkillProviderRef identity = owner_id + SkillSlot + skill_id.
- SkillSlot.INHERENT == 0 is a legitimate Provider key.
- SkillType and PreparationMode remain the Round 2 taxonomy.
- EffectSourceRef is attribution, not a liveness dependency.

Round 5 does not implement Stage13, Stage14 or Stage15 behavior.

## 2. Code audit findings

The current Battle runtime exposes three different things that must not be conflated.

### 2.1 SkillResolver

SkillResolver.resolve currently performs:

~~~text
runtime.enabled
-> candidate construction
-> activation probability RNG
-> target selection RNG
-> effect construction
~~~

The direct runtime.enabled check is a baseline availability check, but it is not sufficient as the future current-validity truth because transient Provider suppression must be owned by ProviderValidityPolicy.

Round 5 freezes an insertion seam only. It does not rewrite SkillResolver.

### 2.2 RecoveryOpportunitySystem

RecoveryOpportunitySystem.evaluate_and_resolve Gate 4 currently:

- uses PersistentSourceSkillGateMode.QUERY_SKILL_RUNTIME;
- reads opportunity.execution_descriptor.source_ref;
- tests source_skill_slot by truthiness;
- calls SkillRuntimeRegistry.get;
- rejects only when an existing SkillRuntime has enabled == False;
- performs this gate before the recovery probability RNG.

This produces three architecture defects for Stage12:

1. SkillSlot.INHERENT == 0 bypasses the lookup because 0 is falsey.
2. a missing runtime currently falls through rather than producing an explicit MISSING decision.
3. the lookup does not validate expected source_skill_id, so slot reuse can silently validate the wrong Provider.

The pre-RNG placement itself is correct and must be preserved.

### 2.3 Runtime-wide source-slot scan

Production runtime scan found:

- RecoveryOpportunitySystem is the concrete current JIT liveness consumer that reads SkillRuntime.enabled.
- SkillResolver reads SkillRuntime.enabled for direct skill resolution.
- Stage10 FirstAidStateParams and RecuperationStateParams declare QUERY_SKILL_RUNTIME as the source-gate mode.
- ContinuousDamageBasisProducer, EffectExecutor, StateInstance, StateGeneration and StateLifecycleSystem transport source_skill_slot as identity/provenance. They are not automatically Provider liveness consumers.
- TriggerSystem contains a separate source_skill_slot truthiness fallback in frozen-damage attribution. That is a Provider identity/provenance hygiene hazard, not evidence that periodic damage should gain a new live Provider dependency.

Therefore Round 5 forbids a mechanical global replacement of every enabled or source_skill_slot occurrence.

## 3. DQ-SF-06 verdict

DQ-SF-06 = **CLOSED_BY_SHARED_FOUNDATION_DESIGN**.

Canonical holder-level owner:

~~~text
SkillPermissionPolicy
~~~

It answers only:

> Given a real attempt to create a new Skill operation for this holder and SkillType, is holder-level state permission currently allowing that admission?

It does not answer:

- whether a specific ProviderRef is valid;
- whether the Provider exists;
- whether activation RNG succeeds;
- which target is selected;
- whether already-admitted work continues;
- whether an Effect child executes.

## 4. SkillPermissionPolicy API

Equivalent frozen interface:

~~~text
evaluate_skill_permission(
    context,
    actor_id,
    skill_type,
    operation_boundary,
) -> SkillPermissionDecision
~~~

Minimum decision semantics:

~~~text
ALLOW
DENY_STATE_PERMISSION
CONTINUATION_NOT_REEVALUATED
~~~

The decision should retain typed blocker facts when denied.

Operation boundary distinguishes:

~~~text
NEW_ADMISSION
CONTINUATION
~~~

CONTINUATION exists to prevent accidental re-admission, not to create a second permission check. Correct callers should normally bypass new-admission policy for child effects belonging to an already admitted Skill operation.

SkillPermissionPolicy consumes no RNG and mutates no state.

## 5. SkillOperationAdmissionCoordinator

A thin composition seam is justified:

~~~text
SkillOperationAdmissionCoordinator
~~~

It is not a new gameplay-policy owner.

Equivalent input:

~~~text
evaluate_admission(
    context,
    actor_id,
    provider_ref,
    skill_type,
    preparation_mode,
    operation_boundary,
) -> SkillOperationAdmissionDecision
~~~

Canonical topology:

~~~text
Provider identity resolution
-> ProviderValidityPolicy
-> SkillPermissionPolicy
-> composed admission decision
-> observable activation / owned RNG
~~~

The coordinator may evaluate both pure policies and retain all blockers so that evaluation order cannot alter the final ALLOW/DENY truth.

Internal blockers include at least:

~~~text
DENY_PROVIDER_INVALID
DENY_STATE_PERMISSION
~~~

ProviderValidityDecision remains the source of the detailed Provider status:

~~~text
VALID
SUPPRESSED
BASELINE_DISABLED
MISSING
IDENTITY_MISMATCH
~~~

If multiple blockers exist, blocker presentation order is diagnostic only. Round 5 does not freeze public event priority; DQ-SF-13 still owns event vocabulary.

## 6. Exhaustion mapping

When Exhaustion is EFFECTIVE:

| Operation | SkillPermission result |
|---|---|
| new ACTIVE admission | DENY_STATE_PERMISSION |
| ACTIVE with PreparationMode.REQUIRED | DENY_STATE_PERMISSION |
| ACTIVE whose preparation is skipped/reduced to zero | DENY_STATE_PERMISSION |
| standard ASSAULT | not denied merely by Exhaustion |
| PASSIVE / COMMAND | no Exhaustion activation denial |
| Normal Attack | outside SkillPermissionPolicy |

Exhaustion is not STUN and not CAPTURE.

No ActionSystem-wide cannot_act flag is introduced.

The policy is queried only when a real admission attempt exists. A holder with no Active candidate produces no synthetic blocked-skill operation merely because Exhaustion is resident.

## 7. Already-admitted work boundary

Frozen contract:

~~~text
new admission != continuation of already admitted work
~~~

If an Active Skill has already crossed its observable admission/activation boundary and Exhaustion becomes effective later:

- the admitted operation is not rolled back;
- already-resolving child effects do not become new Skill admissions merely because they are separate Effect objects;
- future genuinely independent Active admissions are denied;
- independent PREPARING work is interrupted through DQ-SF-07.

Broader queued/in-flight edge cases remain DQ-SF-23. Round 5 does not invent them.

## 8. Provider validity composition

Skill Permission and Provider Validity remain separate.

Example A:

~~~text
holder has effective Exhaustion
Provider is VALID
ACTIVE new admission
=> denied by holder permission
~~~

Example B:

~~~text
holder has no Exhaustion
selected Assault Provider is SUPPRESSED by Intimidation
=> Provider cannot produce future Provider-owned behavior
=> no need to pretend the holder lost Assault permission globally
~~~

Example C:

~~~text
selected Provider becomes VALID again
holder still has effective Exhaustion
=> future ACTIVE admission remains denied
~~~

Provider resume never auto-activates a skill.

## 9. DQ-SF-07 verdict

DQ-SF-07 = **CLOSED_BY_SHARED_FOUNDATION_DESIGN**.

Stage12 does not own PREPARING state.

The future concrete preparation owner may be introduced by Stage15. Stage12 depends only on:

~~~text
PreparationInterruptionPort
~~~

This is a command protocol, not storage and not a scheduler.

## 10. PreparationInterruptionPort

Equivalent frozen shape:

~~~text
interrupt(
    context,
    PreparationInterruptionRequest
) -> PreparationInterruptionResult
~~~

Request scope:

~~~text
HOLDER_ACTIVE
PROVIDER
~~~

HOLDER_ACTIVE includes:

- holder_id;
- reason/cause identity;
- semantic requirement: interrupt every currently PREPARING Active Skill owned by that holder.

PROVIDER includes:

- exact SkillProviderRef;
- reason/cause identity;
- semantic requirement: interrupt only preparation belonging to that Provider.

Minimum result semantics:

~~~text
INTERRUPTED
NOT_PREPARING
PROVIDER_NOT_MATCHED
~~~

A batch result may retain interrupted ProviderRefs/counts. Exact serialization is not gameplay semantics.

## 11. Exhaustion preparation transition

Trigger is not physical STATE_APPLIED.

Trigger is:

~~~text
Exhaustion old effectiveness != EFFECTIVE
and new effectiveness == EFFECTIVE
~~~

Examples include:

- newly committed Exhaustion becomes effective;
- resident Exhaustion was suppressed by Insight, then Insight ends and the same Exhaustion instance becomes effective.

Transition ordering:

~~~text
state transaction commits
-> StateEffectivenessPolicy recomputes
-> EffectivenessTransitionCoordinator detects transition into EFFECTIVE
-> PreparationInterruptionPort HOLDER_ACTIVE request executes synchronously
-> later gameplay may continue
~~~

There is no legal window where Exhaustion is already effective but an old preparation advances one more step.

If Exhaustion is resident but SUPPRESSED, Active permission remains available and no interruption request is produced.

## 12. Intimidation preparation transition

Intimidation owns a stable selected ProviderRef binding.

For preparation interruption, the relevant effective fact is the selected Provider transition:

~~~text
selected SkillProviderRef
VALID -> SUPPRESSED
with Intimidation among the effective suppression causes
~~~

If the selected Provider is ACTIVE + PreparationMode.REQUIRED and currently preparing:

~~~text
PreparationInterruptionPort PROVIDER request
=> only selected Provider interrupted
~~~

Unselected Providers remain untouched.

If another independent cause already keeps the selected Provider SUPPRESSED, removing Intimidation does not create a false VALID transition, false preparation restart or false activation.

## 13. No preparation resume

An interruption destroys continuation rights for that old preparation instance.

Later:

~~~text
Exhaustion ends
or
Intimidation/source suppression ends
or
selected Provider becomes VALID
~~~

means only:

~~~text
a future new admission may be attempted
~~~

It never means:

- restore previous preparation progress;
- resume the old preparation object;
- automatically activate the skill.

A later attempt must create a new preparation through the future preparation owner.

## 14. Stage15 compatibility and adapters

Tests may inject:

~~~text
FakePreparationInterruptionPort
~~~

The fake must record request scope, cause, ProviderRef and result so transition tests can distinguish no preparation from successful interruption.

Round 5 does not adopt a silent production Noop as proof of behavior.

Before a concrete preparation owner exists, production composition may use an explicit no-preparation placeholder only under the invariant that the runtime cannot contain PREPARING work. Any Stage12 state whose frozen contract requires mid-preparation interruption may not be declared fully Runtime Frozen on the strength of that placeholder.

This is an integration dependency, not a gameplay default.

## 15. DQ-SF-21 verdict

DQ-SF-21 = **CLOSED_BY_SHARED_FOUNDATION_DESIGN**.

Design closure does not mean the slot-0 bug is repaired.

The first concrete migration target is RecoveryOpportunitySystem.evaluate_and_resolve Gate 4.

## 16. RecoveryOpportunitySystem method-level migration

Current Gate 4 semantics:

~~~text
QUERY_SKILL_RUNTIME
-> optional Registry.get
-> only existing enabled == False rejects
-> probability RNG
~~~

Future semantics:

~~~text
QUERY_SKILL_RUNTIME
-> require/construct explicit SkillProviderRef(
       owner_id = source_ref.source_unit_id,
       skill_slot = source_ref.source_skill_slot,
       skill_id = source_ref.source_skill_id
   )
-> ProviderValidityPolicy.evaluate_provider
-> if decision != VALID: reject opportunity
-> only VALID reaches probability RNG
~~~

Slot test is explicitly:

~~~text
source_skill_slot is not None
~~~

never truthiness.

SkillSlot values 0, 1 and 2 traverse the same identity/validity path.

Expected skill_id is mandatory for this Provider-dependent gate. Slot reuse by a different skill produces IDENTITY_MISMATCH rather than silently accepting the new Provider.

For an explicitly QUERY_SKILL_RUNTIME / Provider-dependent opportunity:

- MISSING rejects before RNG;
- IDENTITY_MISMATCH rejects before RNG;
- BASELINE_DISABLED rejects before RNG;
- SUPPRESSED rejects before RNG;
- VALID preserves the existing probability/RNG behavior.

The externally surfaced RecoveryOpportunityResult reason may remain compatibility-shaped until DQ-SF-13 freezes public vocabulary, but the internal ProviderValidityDecision must not be lost.

## 17. SkillResolver future migration seam

SkillResolver currently treats runtime.enabled as the complete first gate.

Future admission wiring must change that conceptually to:

~~~text
runtime / ProviderRef identity
-> SkillOperationAdmissionCoordinator
-> only admitted work enters candidate construction / activation RNG / target selection
~~~

ProviderValidityPolicy may use baseline runtime.enabled as one input producing BASELINE_DISABLED.

SkillResolver must not independently invent transient suppression by mutating enabled.

Round 5 does not implement this seam and does not build the Stage14 full activation loop.

## 18. Provider gate migration inventory

| Site | Current behavior | Classification | Round 5 decision |
|---|---|---|---|
| RecoveryOpportunitySystem.evaluate_and_resolve Gate 4 | direct QUERY_SKILL_RUNTIME + enabled check | MUST MIGRATE IN STAGE12 FOUNDATION | construct SkillProviderRef, delegate to ProviderValidityPolicy before recovery RNG |
| SkillResolver.resolve | direct runtime.enabled before activation RNG | ADMISSION SEAM / FUTURE FOUNDATION WIRING | baseline disabled remains an input, but composed ProviderValidity + SkillPermission becomes canonical gate |
| FirstAidStateParams.source_skill_gate | defaults QUERY_SKILL_RUNTIME | DECLARATION CAN REMAIN | execution semantics migrate in RecoveryOpportunitySystem |
| RecuperationStateParams.source_skill_gate | defaults QUERY_SKILL_RUNTIME | DECLARATION CAN REMAIN | execution semantics migrate in RecoveryOpportunitySystem |
| ContinuousDamageBasisProducer / EffectExecutor | copies source_skill_slot | ATTRIBUTION / IDENTITY ONLY | no liveness dependency inferred |
| StateInstance / StateGeneration / StateLifecycleSystem | stores/copies source_skill_slot | STORAGE / PROVENANCE ONLY | no mechanical migration |
| TriggerSystem frozen damage source_skill_slot fallback | uses truthiness fallback | IDENTITY/PROVENANCE HAZARD | record for later explicit fix; do not convert periodic damage into Provider-dependent work |
| CounterSystem source slot | attribution/order data | NOT PROVIDER-DEPENDENT BY ITSELF | no migration merely because a slot exists |

## 19. JIT recheck rule

ProviderValidityPolicy is rechecked at execution time only for behavior that explicitly owns a ProviderDependency or equivalent gate declaration.

Examples:

- recovery opportunity explicitly marked QUERY_SKILL_RUNTIME;
- future provider-owned trigger opportunity;
- future provider-owned scheduled action;
- ongoing provider-dependent effect whose contract declares live Provider dependence.

Not every Effect with source_skill_id or EffectSourceRef becomes provider-dependent.

Already admitted Skill work is not retroactively rolled back simply because the originating Provider later becomes invalid, unless a separate contract explicitly defines that behavior.

## 20. RNG boundary

SkillPermissionPolicy:

~~~text
0 RNG
~~~

ProviderValidityPolicy:

~~~text
0 RNG
~~~

PreparationInterruptionPort:

~~~text
0 RNG
~~~

SkillOperationAdmissionCoordinator:

~~~text
0 RNG
~~~

Owned RNG begins only after admission, for the relevant owner such as:

- Active activation probability;
- target randomization;
- Intimidation binding selection/refresh reroll;
- recovery opportunity probability.

Provider gate rejection in RecoveryOpportunitySystem therefore consumes zero recovery probability RNG.

## 21. Composition examples

### Provider VALID + Exhaustion EFFECTIVE

~~~text
ProviderValidity = VALID
SkillPermission = DENY_STATE_PERMISSION
=> admission denied
~~~

### Provider SUPPRESSED + no Exhaustion

~~~text
ProviderValidity = SUPPRESSED
SkillPermission = ALLOW
=> admission denied
~~~

### Provider SUPPRESSED + Exhaustion EFFECTIVE

~~~text
ProviderValidity = SUPPRESSED
SkillPermission = DENY_STATE_PERMISSION
=> admission denied
=> both internal blockers retained
=> evaluation order cannot change gameplay truth
~~~

### Intimidation removed but Capture suppression remains

~~~text
Provider suppression causes before = {INTIMIDATION, CAPTURE}
remove INTIMIDATION
causes after = {CAPTURE}
Provider stays SUPPRESSED
=> no false preparation resume
=> no auto-activation
~~~

## 22. Runtime defaults

New PROJECT_RUNTIME_DEFAULT entries in Round 5:

~~~text
NONE
~~~

Diagnostic blocker ordering has no gameplay authority.

Non-VALID Provider rejection for explicitly Provider-dependent JIT work is canonical policy semantics, not a guessed default.

No silent no-op preparation implementation is accepted as contract completion.

## 23. Planned tests

Skill Permission:

- exhaustion_denies_active
- exhaustion_allows_normal_attack
- exhaustion_does_not_deny_standard_assault
- exhaustion_does_not_disable_passive_command
- suppressed_exhaustion_allows_active
- exhaustion_resume_denies_future_active
- already_admitted_active_not_rolled_back
- skip_preparation_does_not_bypass_exhaustion
- no_active_attempt_emits_no_block

Preparation:

- effective_exhaustion_interrupts_all_current_active_preparations_for_holder
- selected_intimidation_interrupts_only_selected_provider
- unselected_provider_preparation_untouched
- suppressed_exhaustion_does_not_interrupt
- exhaustion_becomes_effective_after_insight_ends_interrupts_immediately
- interrupted_preparation_does_not_resume
- provider_resume_does_not_resume_preparation
- not_preparing_is_noop
- provider_not_matched_is_distinct
- transition_interruption_precedes_later_gameplay

JIT Provider gate:

- slot_zero_provider_is_gated
- slot_one_provider_is_gated
- slot_two_provider_is_gated
- expected_skill_id_mismatch_rejected
- missing_provider_rejected
- baseline_disabled_rejected
- provider_suppressed_rejected
- provider_gate_rejection_consumes_no_recovery_rng
- provider_valid_path_preserves_existing_rng_behavior

Composition:

- provider_valid_but_exhaustion_blocks_active
- provider_suppressed_without_exhaustion_blocks_selected_skill
- remove_intimidation_but_capture_remains_provider_suppressed
- final_suppression_removed_provider_valid_but_exhaustion_still_blocks_active
- provider_resume_never_auto_activates_skill

## 24. Closure gates

DQ-SF-06 closure requirements are satisfied:

- canonical owner: SkillPermissionPolicy;
- typed decision;
- exact pre-activation/pre-RNG admission seam;
- new admission vs continuation boundary;
- Exhaustion mapping;
- ProviderValidity composition;
- Normal Attack/Assault boundaries;
- zero RNG authority.

DQ-SF-07 closure requirements are satisfied:

- preparation ownership remains future Stage15;
- minimal interruption protocol frozen;
- holder-wide and Provider-specific scope frozen;
- synchronous transition timing frozen;
- old preparation never resumes;
- fake/test behavior defined;
- production placeholder cannot claim contract completion.

DQ-SF-21 closure requirements are satisfied:

- slot 0 semantics frozen;
- expected skill validation frozen;
- missing/mismatch behavior frozen;
- ProviderValidityPolicy migration frozen;
- rejection-before-RNG boundary frozen;
- method-level RecoveryOpportunitySystem mapping frozen;
- migration inventory separates liveness gates from attribution.

## 25. Round 5 verdict

~~~text
DQ-SF-06 = CLOSED_BY_SHARED_FOUNDATION_DESIGN
DQ-SF-07 = CLOSED_BY_SHARED_FOUNDATION_DESIGN
DQ-SF-21 = CLOSED_BY_SHARED_FOUNDATION_DESIGN

SkillPermissionPolicy = canonical holder-level skill permission owner
ProviderValidityPolicy = unchanged canonical Provider validity owner
SkillOperationAdmissionCoordinator = thin composition seam only
PreparationInterruptionPort = minimal Stage12-facing contract

Exhaustion != global action block
Intimidation != holder-level Active block
Provider resume != skill activation
Preparation interruption != Stage15 implementation
SkillSlot.INHERENT == 0 = valid Provider key
JIT Provider rejection = before owned RNG

Stage11 Reopen Required = NO
Gameplay implementation = NONE
Stage12 Runtime Frozen = 0 / 7
Stage13 / Stage14 / Stage15 Active = NO
~~~

Shared Foundation Design Freeze remains NOT PASSED.

NEXT:

~~~text
DQ-SF-09 / DQ-SF-10
Skill Target Operation / Provocation / Capture Target Eligibility Design
~~~
