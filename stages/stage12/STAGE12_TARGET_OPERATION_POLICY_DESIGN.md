# Stage12 Target Operation / Target Policy Design

Date: 2026-09-27  
Round: SF Round 6  
Status: **DESIGN FROZEN FOUNDATION / NO GAMEPLAY IMPLEMENTATION**  
Primary gates: **DQ-SF-09 / DQ-SF-10**

## 1. Verdict

~~~text
DQ-SF-09 = CLOSED_BY_SHARED_FOUNDATION_DESIGN
DQ-SF-10 = CLOSED_BY_SHARED_FOUNDATION_DESIGN

SkillTargetPolicy = canonical Skill target-operation policy owner
TargetSystem = raw candidate + selector/RNG primitive owner
TargetResolutionSystem = unchanged Normal Attack arbitration owner

Stage11 Reopen Required = NO
Gameplay Implementation = NONE
Stage12 Runtime Frozen = 0 / 7
Stage13 / Stage14 / Stage15 Active = NO
~~~

This document freezes representation and owner boundaries needed by later Stage12 Runtime work. It does not add a production target mode, state effect, selector, event or runtime branch.

## 2. Audited existing Runtime

Current production Runtime is intentionally smaller than the Stage12 design.

SkillDefinition.SkillTargetMode currently exposes only:

~~~text
SINGLE_RANDOM_ENEMY
~~~

SkillResolver.resolve currently:

~~~text
runtime.enabled gate
→ build enemy candidates
→ activation probability
→ TargetSystem.random_units(count=1)
→ build Effects
~~~

TargetSystem already owns raw relationship and selector primitives:

~~~text
allies
enemies
random_enemy
random_allies
random_units
~~~

Its current random_units helper consumes zero RNG when every candidate is selected.

TargetResolutionSystem is a separate Stage9 Normal Attack authority:

~~~text
legal pool
→ Confusion
→ else Taunt
→ else default selector
→ freeze intended target
→ Guard redirect exactly once
→ final Normal Attack target
~~~

Round 6 preserves all of those production owners and changes none of their code.

## 3. Core model

A Skill target decision is represented as a fresh target-producing operation with explicit semantics.

Minimum frozen dimensions:

~~~text
TargetOperation
- operation_id
- relation
- cardinality
- selector_kind
- eligibility_context
- producer / admitted-skill identity reference
~~~

Target result and continuation provenance are separate from the operation request itself.

This prevents one overloaded enum such as RANDOM_ENEMY from silently carrying relation, count, freshness, policy and provenance at once.

## 4. Relation

Round 6 freezes:

~~~text
ENEMY
ALLY
SELF
~~~

ANY is deliberately not introduced.

Current Stage12 contracts do not require a general mixed-side Skill relation, while Stage9 Confusion already owns its Normal Attack mixed-side candidate construction. A future Skill contract may add another relation only with an explicit contract discriminator.

## 5. Cardinality

Round 6 freezes:

~~~text
SINGLE
CHOOSE_N
FIXED_ALL
~~~

Rules:

- SINGLE has exact cardinality 1 when a legal target exists.
- CHOOSE_N carries an explicit requested positive integer N.
- FIXED_ALL means every currently eligible target in the operation scope.
- a sentinel target_count such as 999 must never represent FIXED_ALL.

CHOOSE_N and FIXED_ALL remain different because Provocation constrains them differently.

## 6. Selector boundary

Minimum selector kinds:

~~~text
RANDOM
DETERMINISTIC
EXPLICIT
~~~

Selector semantics answer how an allowed target set is selected.

They do not answer Provocation, Capture, Confusion, target inheritance, Provider validity or Skill admission.

Random sampling remains owned by the selector / TargetSystem primitives and ultimately by BattleContext.random.

## 7. Eligibility context

Every TargetOperation carries operation-local eligibility context sufficient to answer legal-target questions that raw team membership cannot answer.

The context must preserve at least:

~~~text
operation domain = SKILL
relation / side requirement
contract-specific legal-target predicate or fixed-context restrictions
purpose boundary for hostile / friendly-support / recovery / self
~~~

This is not a universe-scale taxonomy. A fixed Duel-style context can reject an external Provocation Source without changing TargetSystem's physical team membership.

## 8. TargetOperationId

A fresh independent target query receives a typed value identity:

~~~text
TargetOperationId
~~~

Required properties:

- immutable value identity;
- deterministic allocation within a battle;
- equality by value, never Python object identity;
- non-orderable for gameplay priority;
- distinct from TargetResolutionId.

The existing TargetResolutionId is a Stage9 Normal Attack trace/supporting identity and must not be repurposed as Skill target-operation semantic identity.

The future implementation may extend the existing operation-ID allocator pattern, but Round 6 adds no production type.

## 9. Who creates a new operation

The skill/effect operation producer owns the declaration.

Equivalent request boundary:

~~~text
NEW_QUERY
INHERIT_RESOLVED
DERIVE_FROM_RESOLVED
LOCK_RESOLVED
~~~

Only NEW_QUERY allocates a new TargetOperationId, constructs a TargetOperation, enters SkillTargetPolicy and may cause Provocation to be evaluated for that query.

SkillTargetPolicy never infers freshness from call count, stack depth, hit index, object identity or the mere existence of a new Effect object.

## 10. DQ-SF-10 query definition

A new target query is a producer-declared new independent candidate-selection request whose answer is not inherited, derived or locked from an already resolved target operation.

~~~text
fresh independent candidate-selection request
→ NEW_QUERY
→ new TargetOperationId
→ policy may re-evaluate

reuse already-resolved target
→ INHERIT_RESOLVED / DERIVE_FROM_RESOLVED / LOCK_RESOLVED
→ no new TargetOperation
→ no automatic policy recheck
~~~

This closes DQ-SF-10 without asking policy code to guess intent.

## 11. TargetSelectionResult and provenance

Equivalent result shape:

~~~text
TargetSelectionResult
- operation_id
- target_ids
- provenance
~~~

Minimum provenance:

~~~text
FRESH_SELECTED
INHERITED
DERIVED
LOCKED
~~~

Provenance explains where a resolved target came from. It is not itself permission to create a fresh query.

A child effect can carry the original operation identity plus INHERITED or DERIVED provenance without allocating another operation.

## 12. Multi-hit

Target selected once and then hit repeatedly is one TargetOperation when the Skill contract does not explicitly request reacquisition.

Provocation is not rerun per hit. Multiple damage/effect instances are not evidence of multiple target queries.

## 13. Multi-query

If the producer explicitly declares query 1 and query 2 as two independent acquisitions, each is NEW_QUERY and receives a distinct TargetOperationId.

Provocation may be evaluated independently for each operation.

## 14. Inherited / Derived / Locked

Inherited:
a child effect reuses an already resolved target. No new query and no automatic Provocation recheck.

Derived:
an adjacent/linked/secondary target computed from an already-resolved target is a continuation by default. Only an explicit independent candidate selection creates NEW_QUERY.

Locked:
a resolved target can be stored for later work. Locked reuse retains the original operation identity/provenance and does not automatically rerun Provocation or Capture target eligibility.

Capture delayed/already-locked semantics remain DQ-SF-23 plus Capture Q44/Q45.

## 15. SkillTargetPolicy owner

Canonical owner:

~~~text
SkillTargetPolicy
~~~

Equivalent API:

~~~text
evaluate(
    context,
    operation: TargetOperation,
    raw_candidates,
) -> TargetPolicyDecision
~~~

It answers: given this already-admitted fresh Skill target operation and its raw candidates, what operation-local eligibility exclusions and target-set constraints apply?

It does not own Provider identity/validity, holder Skill permission, State lifecycle, Normal Attack targeting, RNG service, random sampling or public events.

## 16. TargetPolicyDecision

The decision is constraint-oriented, not random-target-oriented.

Equivalent minimum semantics:

~~~text
TargetPolicyDecision
- eligible_candidate_ids
- required_target_ids
- excluded_target_ids
- preserve_cardinality
- boundary / unsupported marker when a contract edge remains bounded
~~~

Examples:

~~~text
Provocation CHOOSE_N
→ required_target_ids = {Source}
→ preserve requested N

Capture verified friendly operation
→ excluded_target_ids += {captured holders}
~~~

The policy must not produce a random final target merely because it owns a constraint.

## 17. Canonical Skill target subpipeline

Round 6 freezes:

~~~text
Provider identity resolution
→ ProviderValidityPolicy
→ SkillPermissionPolicy
→ Skill operation admitted
→ producer declares NEW_QUERY
→ allocate TargetOperationId
→ TargetSystem builds raw candidates
→ operation-local legality / Capture eligibility
→ arbitration-authority discriminator
→ Provocation constraint when eligible
→ selector executes
→ TargetSelectionResult
→ child effects inherit / derive / lock as declared
~~~

The exact placement of activation-probability RNG relative to pure candidate construction is still DQ-SF-12.

Hard boundary:

~~~text
skill admission denied
→ no TargetOperation
→ no target-selection RNG
~~~

## 18. Candidate construction versus eligibility

TargetSystem.allies() and TargetSystem.enemies() remain physical/raw relationship primitives.

They must not silently encode Stage12 state restrictions.

~~~text
raw team candidates
!=
operation-local eligible candidates
~~~

Capture eligibility filtering and Provocation Source admissibility happen in the Skill target-operation layer.

## 19. Capture friendly eligibility

Verified Capture scope:

~~~text
ALLY + SINGLE
ALLY + CHOOSE_N
~~~

For those fresh selection operations, a captured holder is excluded from eligible candidates.

Capture does not mean unit.targetable = False and does not remove that unit from raw TargetSystem.allies().

### Friendly SINGLE

If no legal target remains after Capture exclusion:

~~~text
NO_LEGAL_TARGET
~~~

The future SkillResolver adapter may map that to existing NO_VALID_TARGET. No automatic self fallback is introduced.

### Friendly CHOOSE_N

Captured holders are excluded before selection while requested-cardinality semantics remain explicit.

If fewer than N eligible targets remain, exact behavior remains bounded.

Current TargetSystem.random_units() uses min(count, len(candidates)); Round 6 explicitly does not promote that legacy helper behavior into the Stage12 CHOOSE_N contract.

### FIXED_ALL / ALL_ALLIES

Capture Q42 remains bounded. Verified single/multi exclusion is not generalized to every ALL_ALLIES effect.

### Enemy and self boundaries

Capture does not remove enemy targetability.

Capture recovery denial is not target eligibility. A self-recovery target may remain resolved while RecoverySystem independently enforces received-recovery-zero semantics.

~~~text
Target Eligibility
!=
Recovery Permission
~~~

## 20. Provocation domain

Provocation applies only to an eligible fresh enemy-directed Skill TargetOperation when the state currently has gameplay authority and the Provocation Source is admissible for this operation.

Provocation never creates a target opportunity for an operation that has no fresh target query.

### SINGLE

For ENEMY + SINGLE with admissible Source:

~~~text
required target = Source
exact cardinality = 1
final target = Source
~~~

SkillTargetPolicy itself consumes zero RNG. A forced SINGLE does not justify a random draw merely to overwrite it.

### CHOOSE_N

~~~text
requested N stays N
Source must appear exactly once
remaining slots are owned by the original selector
~~~

The policy must never collapse CHOOSE_N to [Source].

Exact random micro-order is intentionally unresolved:

~~~text
reserve Source then sample N-1
vs
sample N then replace one slot
~~~

Those algorithms may consume RNG differently. DQ-SF-12 / BU-P02 retains that question.

### FIXED_ALL

~~~text
final = all eligible enemies
~~~

Provocation does not collapse the set. If Source is already in the eligible all-set, no structural change is needed. If Source is illegal, policy must not insert it.

## 21. Source admissibility and duplicates

A Provocation Source must be legal under the current operation relation and eligibility context.

If Source is inadmissible, Provocation contributes no forcing constraint to this operation and normal operation semantics continue. This does not physically remove the Provocation State.

Operation-local inadmissibility must not be written back into StateEffectivenessPolicy as if all target operations shared one candidate scope.

Stage12 SINGLE/CHOOSE_N target IDs are unique unless a future contract explicitly introduces duplicate-target semantics. Source-already-selected therefore does not create a duplicate or policy-side RNG draw.

## 22. Multiple Provocation Sources

Simultaneous multi-source/reapplication precedence remains bounded.

Round 6 does not choose latest-wins, lowest-id-wins, random-source or registration-order precedence.

If implementation later cannot avoid this overlap, the Runtime Default process must own the decision.

## 23. Confusion / Taunt / Guard boundary

Normal Attack never enters SkillTargetPolicy.

Its existing owner remains TargetResolutionSystem with:

~~~text
Confusion
→ else Taunt
→ else default
→ Guard
~~~

For any future Skill operation whose contract explicitly says Confusion controls the target decision, Confusion arbitration authority pre-empts Provocation; Provocation must not force again afterwards.

This is a domain/arbitration discriminator, not a generic numeric priority.

Taunt remains Normal Attack forced-target authority. Guard remains post-selector Normal Attack redirect. No universal ForceTargetPolicy is introduced.

## 24. Exhaustion / Provider-invalid boundary

Round 5 admission is upstream.

~~~text
effective Exhaustion denies new ACTIVE admission
→ no Skill operation admitted
→ no TargetOperation
→ no Provocation target opportunity
~~~

Likewise:

~~~text
ProviderValidity != VALID
→ no Skill operation admitted
→ no TargetOperation
→ no target-selection RNG
~~~

## 25. Cross-state phase ordering

Round 6 uses domain phases instead of a generic priority number:

~~~text
1. admitted operation / relation legality
2. raw candidate construction
3. operation-local eligibility exclusions
4. arbitration-authority discriminator
5. state-specific target constraints such as Provocation
6. selector
7. immutable target result
~~~

Provocation can require only a Source that survives legality/eligibility. It cannot bypass Capture or another legality rule.

In currently verified scopes, Capture friendly exclusion and Provocation enemy forcing normally occupy different relation domains.

## 26. RNG ownership

~~~text
SkillTargetPolicy.evaluate = 0 RNG
~~~

Target sampling remains selector-owned and all eventual random sampling remains BattleContext.random-owned.

Consequences:

- no policy-side random replacement slot;
- no arbitrary extra draw because Provocation exists;
- forced SINGLE may resolve deterministically;
- FIXED_ALL adds no policy RNG;
- CHOOSE_N exact random stream remains DQ-SF-12.

## 27. No-target opportunity

If no fresh target query exists, Provocation cannot manufacture one.

Inherited, derived and locked continuations remain continuations.

A FIXED_ALL operation can still be a TargetOperation if its producer explicitly creates one. Freshness is about operation semantics, not whether RNG is used.

## 28. SkillResolver migration seam

Future migration can preserve SkillResolutionResult externally while replacing the internal single-enum targeting seam:

~~~text
current:
SkillTargetMode
→ _candidate_units
→ _select_targets

future:
admitted Skill operation
→ TargetOperation producer
→ TargetSystem raw candidates
→ SkillTargetPolicy
→ selector
→ TargetSelectionResult
→ existing Effect construction
~~~

No production signature changes in Round 6.

## 29. Bounded edges preserved

Round 6 leaves these outside closed gameplay semantics:

- Provocation CHOOSE_N RNG micro-order;
- Provocation insufficient-candidate micro-policy;
- simultaneous multi-source/reapplication precedence;
- rare unobserved Source-invalidity variants beyond legal-target rule;
- Capture ALL_ALLIES;
- Capture delayed/already-locked friendly work;
- Capture state-level reapplication/multi-source;
- public target-forced event vocabulary;
- final composition wiring.

Architecture can represent these boundaries without inventing their answers.

## 30. Runtime defaults

~~~text
New Runtime Defaults = NONE
~~~

RD-SF-001 / RD-SF-002 / RD-SF-003 remain the full Shared Foundation Runtime Default set.

## 31. Planned tests

Provocation:

~~~text
provocation_single_forces_source
provocation_choose_n_includes_source_and_preserves_n
provocation_fixed_all_preserves_all
source_already_selected_no_duplicate
friendly_operation_not_redirected
self_operation_not_redirected
normal_attack_not_redirected
confusion_preempts_provocation
exhaustion_blocked_skill_creates_no_target_operation
provider_invalid_skill_creates_no_target_operation
policy_cannot_force_illegal_source
~~~

Query granularity:

~~~text
inherited_target_not_rechecked
derived_target_not_rechecked_without_explicit_new_query
independent_second_query_rechecks_provocation
multi_hit_same_target_one_operation
multi_query_creates_distinct_operation_ids
target_operation_producer_must_explicitly_mark_new_query
~~~

Capture:

~~~text
captured_holder_excluded_from_friendly_single
captured_holder_excluded_from_verified_friendly_choose_n
capture_does_not_remove_enemy_targetability
capture_does_not_mutate_global_allies_query
self_recovery_not_reimplemented_as_target_exclusion
all_allies_boundary_remains_explicit
locked_delayed_friendly_target_remains_DQ_SF_23_boundary
~~~

Architecture/RNG:

~~~text
target_policy_consumes_zero_rng
selector_remains_rng_owner
normal_attack_target_resolution_unchanged_without_stage12_skill_operation
target_operation_producer_must_explicitly_mark_new_query
policy_cannot_force_illegal_source
~~~

These are design obligations only. No executable tests are added in Round 6.

## 32. Closure audit

DQ-SF-09 closure requirements satisfied:

- TargetOperation model;
- relation;
- cardinality;
- selector boundary;
- provenance/result shape;
- SkillTargetPolicy owner;
- Provocation SINGLE;
- Provocation CHOOSE_N target-set semantics;
- Provocation FIXED_ALL;
- Capture verified friendly eligibility.

DQ-SF-10 closure requirements satisfied:

- new query definition;
- inherited;
- derived;
- locked;
- independent re-query;
- multi-hit;
- multi-query;
- producer ownership.

## 33. Round 6 exit

~~~text
DQ-SF-09 = CLOSED_BY_SHARED_FOUNDATION_DESIGN
DQ-SF-10 = CLOSED_BY_SHARED_FOUNDATION_DESIGN

SkillTargetPolicy canonical owner = FROZEN
TargetOperation model = FROZEN
Normal Attack owner = UNCHANGED

Provocation SINGLE = force admissible Source
Provocation CHOOSE_N = preserve N + include Source once
Provocation FIXED_ALL = preserve all eligible targets

Inherited / Derived / Locked != NEW_QUERY
Independent NEW_QUERY may re-evaluate Provocation

Capture friendly eligibility = verified SINGLE / CHOOSE_N only
Capture global untargetable flag = FORBIDDEN
TargetPolicy RNG = 0

Stage11 Reopen Required = NO
Gameplay Implementation = NONE
Stage12 Runtime Frozen = 0 / 7
Stage13 / Stage14 / Stage15 Active = NO
~~~

Shared Foundation Design Freeze remains **NOT YET**.

NEXT:

~~~text
DQ-SF-11
Equipment Effectiveness / Sabotage /
Equipment-linked FalseReport & Capture Boundary Design
~~~
