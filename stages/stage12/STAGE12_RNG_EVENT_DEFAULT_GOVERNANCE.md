# Stage12 RNG / Event / Runtime Default Governance

Date: 2026-09-27
Round: STAGE12_SF_ROUND9_RNG_EVENT_DEFAULT_GOVERNANCE
Status: DESIGN FROZEN FOR DQ-SF-12 AND DQ-SF-13; DQ-SF-14 ARCHITECTURE CLOSED / CONTRACT DEPENDENT
Gameplay implementation in this round: NONE

## 1. Repository and authority lock

Round 9 starts from:

- Battle main: c12bc800d6c520edd41b10525118a1ce90e9b5c6
- Research main: e18ae56a4db5662b87458dfa8fdff25dcdd8053b
- Round 8 CI: 36296755216 / success
- pytest baseline: 913 passed
- demo smoke: PASS
- independent audit snapshot: PASS

Research remains read-only. This round changes design/governance documentation only.

## 2. Governing invariants

The Shared Foundation freezes three independent rules.

~~~text
RNG
Only the domain owner of a real random decision may consume BattleContext.random.

EVENT
EventBus records facts after the owning decision/commit; it never decides gameplay.

DEFAULT
A PROJECT_RUNTIME_DEFAULT exists only when Runtime must choose deterministic behavior
and Research cannot determine that behavior.
~~~

Unknown does not imply Default.

~~~text
Runtime can reject/defer unsupported path
-> UNSUPPORTED_BOUNDARY

Runtime must choose deterministic behavior now
-> PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN
~~~

## 3. Current runtime audit anchors

The existing runtime already supplies the correct service-level authorities:

- sgs_v2/battle_core/random_system.py defines RandomSystem as the battle's sole random service.
- Runtime consumers use context.random.
- TargetSystem owns target-sampling primitives.
- SkillResolver owns the current activation probability draw.
- EventBus explicitly records/distributes already-happened facts and does not decide outcomes.
- StateLifecycleSystem publishes STATE_APPLIED / STATE_REFRESHED / STATE_REMOVED only after physical mutation.
- ActionSystem owns ACTION_BLOCKED.
- Damage resolution owns DAMAGE_PREVENTED.
- RecoverySystem owns RECOVERY_PREVENTED.

The current EventType vocabulary has no generic state-suppressed/resumed, Provider-suppressed/resumed,
state-application-rejected, skill-operation-blocked, preparation-interrupted, or target-forced event.

Round 9 freezes future ownership and vocabulary requirements. It does not add those EventTypes now.

## 4. DQ-SF-12 verdict

~~~text
DQ-SF-12
= CLOSED_BY_SHARED_FOUNDATION_DESIGN
~~~

The random service, random-decision owners, zero-RNG policies, decision points, rejection paths,
refresh/resume distinction, deterministic replay rule, and bounded RNG unknowns are now architecturally closed.

## 5. Final RNG Ownership Matrix

| Operation | RNG owner | Decision point | Rejected / bypassed path |
|---|---|---|---|
| source state/effect application probability | originating source/effect-generation owner | before candidate admission when the source contract defines a proc roll | no candidate when source roll fails; Insight does not move this draw |
| Insight-protected incoming control | original source-generation owner only | normal source RNG, then candidate, then StateAdmissionPolicy | Insight rejection adds zero RNG and never skips source RNG required by PD-INS-001 |
| Skill activation probability | Skill activation owner / SkillResolver-equivalent | only after ProviderValidity + SkillPermission + operation admission ALLOW | invalid Provider or denied permission consumes zero activation RNG |
| Skill target random selection | TargetSystem / selector | after SkillTargetPolicy returns legal candidates/constraints | denied operation consumes zero target RNG |
| Provocation SINGLE | TargetSystem / selector, but deterministic when Source is the sole required result | after policy constraint | forced legal singleton consumes zero target RNG |
| Provocation CHOOSE_N | TargetSystem / selector when implemented | after policy constraint | exact reserve-vs-replace micro-order remains bounded/deferred |
| Intimidation initial Provider binding | Intimidation binding-selection owner | only after successful state admission and eligible Provider pool construction | admission rejection consumes zero binding RNG |
| Intimidation refresh binding | same binding-selection owner | after successful REFRESH authorization, before refresh transaction commit | failed/rejected refresh consumes zero new binding RNG |
| Intimidation resume | none | effectiveness transition only | zero binding RNG; retained binding is reused |
| Provider-dependent RecoveryOpportunity probability | existing RecoveryOpportunity owner | ProviderValidity JIT ALLOW first, then recovery probability | every non-VALID Provider result consumes zero recovery probability RNG |
| equipment trigger probability | trigger/opportunity owner | after EquipmentEffectiveness JIT ALLOW | suppressed/invalid contribution consumes zero downstream trigger RNG |
| reaction/counter randomness, if a specific reaction owns any | that reaction domain owner | after its own admission/execution-right gate | Shared Foundation adds no synthetic reaction RNG |
| ExecutionRightSpec evaluation | none | JIT policy evaluation | DENY consumes zero work-owned downstream RNG unless a source contract explicitly freezes source-RNG-before-rejection |

RandomSystem is a service. Gameplay owners authorize a draw; they do not become alternative PRNG services.

## 6. Zero-RNG Policy Matrix

The following are pure decision/query layers and consume zero RNG:

| Owner | RNG contract |
|---|---|
| StateAdmissionPolicy | 0 RNG |
| StateEffectivenessPolicy | 0 RNG |
| StateConflictPolicy | 0 RNG |
| ProviderValidityPolicy | 0 RNG |
| SkillPermissionPolicy | 0 RNG |
| SkillOperationAdmissionCoordinator | 0 RNG |
| SkillTargetPolicy | 0 RNG |
| EquipmentEffectivenessPolicy | 0 RNG |
| StateRemovalPolicy | 0 RNG |
| EffectivenessTransitionCoordinator | 0 RNG |
| ExecutionRightSpec evaluation | 0 RNG |

StateApplicationCoordinator is also RNG-free as a generic transaction coordinator.
A mechanism-specific Intimidation binding selector is an explicit delegated random decision, not a hidden policy query.

## 7. Method-level RNG order

### 7.1 State application and Insight

~~~text
originating effect source
-> normal source proc RNG, iff source defines one
-> candidate exists
-> StateAdmissionPolicy.evaluate_candidate
-> conflict policy only after admission ALLOW
-> transaction preparation / commit
~~~

PD-INS-001 is preserved exactly in substance:

- probabilistic source control keeps its normal source draw before Insight rejection;
- deterministic source control adds no synthetic draw;
- Insight admission itself is zero RNG.

### 7.2 Skill activation

~~~text
resolve ProviderRef
-> ProviderValidityPolicy
-> SkillPermissionPolicy
-> SkillOperationAdmissionCoordinator final ALLOW
-> activation probability owner may draw
-> target operation / selector as applicable
~~~

No activation draw is consumed for MISSING, IDENTITY_MISMATCH, BASELINE_DISABLED, SUPPRESSED,
or holder-permission denial.

### 7.3 Target selection

~~~text
fresh TargetOperation
-> raw candidates
-> SkillTargetPolicy eligibility/constraints
-> selector
-> immutable target result
~~~

SkillTargetPolicy never samples. TargetSystem.random_enemy and random_units remain the random-selection primitive owners.

A legal forced singleton and an all-candidates selection are deterministic and require no meaningless draw.

### 7.4 Intimidation binding

~~~text
incoming Intimidation candidate
-> admission/protection
-> conflict/refresh authorization
-> eligible Provider pool
-> binding selection
-> transaction commit
~~~

Initial application and successful refresh authorize a real selection operation.
A refresh reroll remains a reroll even if it selects the same Provider value.
Resume is not Refresh and consumes zero binding RNG.

The contract proves random selection of exactly one eligible Provider but does not prove uniform 1/N weighting.

### 7.5 Recovery and equipment

Provider-dependent RecoveryOpportunity:

~~~text
ProviderValidity JIT
-> if VALID: existing recovery probability owner may draw
-> otherwise: reject, zero recovery RNG
~~~

Equipment trigger opportunity:

~~~text
EquipmentEffectiveness JIT
-> if EFFECTIVE: trigger owner may perform its own frozen random decision
-> otherwise: skip, zero downstream trigger RNG, no replay
~~~

## 8. Provocation CHOOSE_N boundary

The contract freezes the observable result topology:

- preserve requested cardinality when the supported candidate case exists;
- include admissible Source exactly once.

It does not distinguish:

~~~text
reserve Source -> sample N-1
vs
sample N -> replace one if Source absent
~~~

Those topologies can alter the RNG stream. Round 9 therefore does not choose one.

Round 9 classification at the design-freeze checkpoint:

~~~text
BU-P02 / exact CHOOSE_N RNG micro-order
= NOT CURRENTLY IMPLEMENTED / DEFERRED
= NOT A NEW RUNTIME DEFAULT IN ROUND 9
~~~

The later 690108 integration gate made deferral impossible. BU-P02 is now governed by **RD-SF-005** in the Runtime Default Ledger:

~~~text
reserve required Source first
-> remove Source from remaining random population
-> TargetSystem fills N-1 remaining slots
-> no post-selector replacement
~~~

RD-SF-005 is `PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN`; it does not change the bounded Research conclusion.

## 9. Intimidation weighting and empty-pool boundaries

~~~text
selection weighting
= NOT CURRENTLY IMPLEMENTED / DEFERRED
uniform 1/N is forbidden as a research claim

empty eligible pool
= UNSUPPORTED_BOUNDARY
until contract/default authority supplies a deterministic gameplay answer
~~~

RD-SF-002 defines deterministic Provider enumeration only. It does not define selection weighting.

## 10. Deterministic replay contract

For Stage12 randomized paths:

~~~text
same seed
+ same input
+ same admission decisions
+ same supported execution path
-> same ordered RandomSystem API decisions
-> same result
~~~

Governance is defined at the RandomSystem API decision-operation level.
It does not claim CPython random.Random's hidden internal bit-consumption as original-game behavior.

Future tests may instrument a trace/fake around the existing RandomSystem seam to assert owner/path and call sequence.
Production RandomSystem must not be redesigned merely for test convenience.

## 11. Remaining RNG boundaries

The following remain explicit rather than guessed:

- Provocation CHOOSE_N exact sampling micro-order.
- Provocation insufficient-candidate policy.
- Provocation simultaneous multi-source precedence.
- Intimidation exact selection weights.
- Intimidation empty eligible pool.
- any mechanism-specific queued/JIT boundary already marked UNSUPPORTED_BOUNDARY.

These do not block DQ-SF-12 architecture closure.

## 12. DQ-SF-13 verdict

~~~text
DQ-SF-13
= CLOSED_BY_SHARED_FOUNDATION_DESIGN
~~~

Event ownership, query/event separation, public-vs-internal transitions, transaction ordering,
idempotence, multiple-reason handling, and EventBus non-authority are now fixed.

## 13. Query is not Event

Pure repeated queries publish nothing:

- StateAdmissionPolicy evaluation before a final application outcome;
- StateEffectivenessPolicy.evaluate;
- ProviderValidityPolicy.evaluate;
- SkillPermissionPolicy.evaluate;
- SkillTargetPolicy.evaluate;
- EquipmentEffectivenessPolicy.evaluate_contribution;
- StateRemovalPolicy evaluation;
- ExecutionRightSpec evaluation.

A query may discover a fact used by an owner. The query itself is not the observable transition.

## 14. Internal transition vs public event model

Internal coordination facts may include:

~~~text
StateEffectiveChanged(old, new)
ProviderValidityChanged(old, new)
dependency closure changed
preparation interruption requested
~~~

They are not automatically EventBus events.

Public events require an actual observable fact and an owning domain decision.

### 14.1 State effectiveness transition

Existing lifecycle events cannot truthfully express PRESENT_BUT_SUPPRESSED.

Future Stage12 event vocabulary therefore requires:

~~~text
STATE_SUPPRESSED
STATE_RESUMED
~~~

for contract-observable state transitions such as Insight cfg204/cfg205 semantics.

Publishing rules:

- publish only after committed state/dependency changes and recomputation;
- publish once per real effective-state transition;
- SUPPRESSED -> SUPPRESSED emits nothing;
- RESUMED requires the physical state still exists and becomes effective;
- query repetition emits nothing.

EffectivenessTransitionCoordinator may coordinate the transition, but it does not own the underlying effectiveness truth.

### 14.2 Provider transition

ProviderValidityChanged is internal by default.

No generic public PROVIDER_SUPPRESSED / PROVIDER_RESUMED event is required merely for debugging.
A Provider transition becomes publicly observable through the actual dependent domain fact when the contract requires one.

A later contract may add a Provider-level public fact, but it must not be created merely because a query returned a new value.

## 15. State application rejection

Round 9 chooses one future public rejection fact with a typed stage, not two unrelated EventTypes:

~~~text
STATE_APPLICATION_REJECTED
rejection_stage = ADMISSION | CONFLICT
reason = typed reason
candidate provenance = preserved
~~~

Examples:

- effective Insight rejects incoming protected control -> ADMISSION;
- incoming Insight rejected by resident singleton/conflict rule -> CONFLICT.

The final application orchestrator publishes the rejection only after the rejection is canonical.
StateAdmissionPolicy and StateConflictPolicy themselves publish nothing.

No rejected candidate emits STATE_APPLIED / STATE_REFRESHED / STATE_REMOVED.

## 16. Skill and preparation facts

An actual new Skill operation that reaches admission and is denied may publish a future:

~~~text
SKILL_OPERATION_BLOCKED
~~~

owned by the Skill operation admission/execution domain.

No Active attempt means no block event. Holder state alone does not emit a per-round block event.

An actual PREPARING -> interrupted transition may publish future:

~~~text
PREPARATION_INTERRUPTED
~~~

owned by the true preparation domain after the transition succeeds.

NOT_PREPARING produces no interruption event.

## 17. Action event ownership

ACTION_BLOCKED remains ActionSystem-owned.

CAPTURE supplies an action-denial fact; ActionSystem makes the canonical action decision and publishes the event.
A Capture state handler must not publish ACTION_BLOCKED independently.

CAPTURE denial occurs before NormalAttack creation, so no downstream target RNG or NormalAttack event is fabricated.

## 18. Damage event ownership

DAMAGE_PREVENTED remains Damage-domain-owned for denied damage work such as CAPTURE actor-permission denial.

WEAKNESS is different: it permits legal damage work whose amount is zero under its own frozen damage rule.
It must not be collapsed into a generic DAMAGE_ZERO event with CAPTURE.

The public event follows the canonical Damage-domain decision.

## 19. Recovery event ownership and multiple causes

RECOVERY_PREVENTED remains RecoverySystem-owned.

Internal prevention topology may retain a cause set, for example:

~~~text
{HEALING_BAN, CAPTURE}
~~~

The current public compatibility surface is one RECOVERY_PREVENTED event with one primary reason.
Round 9 freezes this compatibility rule:

1. TARGET_DEFEATED keeps its existing earlier terminal meaning.
2. If HEALING_BAN and CAPTURE both prevent the same supported recovery, public primary reason remains HEALING_BAN.
3. CAPTURE-only prevention uses CAPTURE as the future primary reason.
4. Internal cause membership may retain all applicable causes.
5. Exactly one public RECOVERY_PREVENTED fact is emitted for one prevented recovery.

This is an event-representation compatibility choice, not a PROJECT_RUNTIME_DEFAULT, because it does not choose gameplay outcome.

## 20. Target event model

SkillTargetPolicy evaluation never emits an event.

Round 9 does not require a generic TARGET_FORCED EventType.

If a later report surface requires target-constraint observability, the target-operation resolution owner may publish only when the final resolved target set is observably changed by the constraint.

Therefore:

- Provocation FIXED_ALL no-op does not fabricate a forced-target change;
- Source already present in a valid CHOOSE_N result does not fabricate a second force event;
- repeated target-policy queries emit nothing.

## 21. Transaction and event ordering

For successful mutation:

~~~text
canonical decision
-> physical commit
-> dependency recompute
-> internal transition ports
-> public observable facts
~~~

For a rejected application with no commit:

~~~text
canonical rejection decision
-> optional/public rejection fact
~~~

For precondition, cycle, binding-validation, or transaction-validation failure:

- no STATE_APPLIED;
- no STATE_REFRESHED;
- no false Provider/state transition event;
- a rejection/failure fact is allowed only if the final domain contract explicitly defines that failed attempt as observable.

Gameplay ordering owns event ordering, never the reverse.
EventBus listeners may react to facts but may not become permission authorities.

## 22. Event idempotence

Required invariants:

- repeated query -> zero events;
- same decision without transition -> zero transition events;
- SUPPRESSED -> SUPPRESSED -> zero new STATE_SUPPRESSED;
- RESUMED -> RESUMED -> zero new STATE_RESUMED;
- failed transaction -> zero committed-state events;
- one domain outcome -> one canonical public outcome fact, unless a frozen contract explicitly requires more.

## 23. DQ-SF-14 verdict

~~~text
DQ-SF-14
= CONTRACT_DEPENDENT_WITH_ARCHITECTURE_CLOSED
~~~

Architecture is closed because every currently known unknown has a governance category.
Gameplay truth is not invented merely to make the ledger look complete.

## 24. Runtime Default finalization

Battle-owned Runtime Defaults remain:

~~~text
RD-SF-001
Legacy SkillDefinition classification compatibility

RD-SF-002
Loaded Skill Provider deterministic enumeration order

RD-SF-003
Same-envelope lifecycle settlement ordering
~~~

Round 9 adds:

~~~text
NEW RUNTIME DEFAULTS = NONE
~~~

Research-owned approved project defaults are inherited, not relabeled as empirical facts:

~~~text
PD-INS-001
Insight source RNG parity

PD-INS-002
Insight resident-singleton / no-refresh-no-replace reapplication saturation
~~~

They keep their original provenance.

## 25. Unknown candidate classification

| Candidate | Governance category | Round 9 disposition |
|---|---|---|
| Insight stronger replacement | INHERITED PROJECT DEFAULT | PD-INS-002 governs reject/no replace while canonical Insight is present |
| Intimidation selection weights | NOT CURRENTLY IMPLEMENTED / DEFERRED | do not assume uniform 1/N |
| Intimidation empty eligible pool | UNSUPPORTED_BOUNDARY | no invented success/failure semantics |
| Provocation CHOOSE_N RNG micro-order | NOT CURRENTLY IMPLEMENTED / DEFERRED | BU-P02 preserved; future implementation choice must be ledgered if required |
| Provocation insufficient candidates | UNSUPPORTED_BOUNDARY | legacy helper truncation is not promoted to contract truth |
| Provocation multi-source precedence | UNSUPPORTED_BOUNDARY | no latest/earliest/random-source rule invented |
| FalseReport stronger/weaker | UNSUPPORTED_BOUNDARY | B-U01 preserved |
| Sabotage stronger/multi-source | UNSUPPORTED_BOUNDARY | B-SAB-02 preserved |
| Sabotage queued/JIT | UNSUPPORTED_BOUNDARY | B-SAB-07 preserved outside tested scheduled due-window |
| Capture Q16 already-created DamageRequest | UNSUPPORTED_BOUNDARY | actor-permission micro-slice not guessed |
| Capture Q42 ALL_ALLIES | UNSUPPORTED_BOUNDARY | verified friendly SINGLE/CHOOSE_N not generalized |
| Capture Q44 delayed friendly work | UNSUPPORTED_BOUNDARY | per-dimension JIT mode not guessed |
| Capture Q45 already-locked friendly target | UNSUPPORTED_BOUNDARY | LOCKED never silently becomes NEW_QUERY |
| Capture multi-source/reapplication Q70-Q74 | UNSUPPORTED_BOUNDARY | no state-core stack/refresh invention |
| Capture Q63 reactive/damage equipment | UNSUPPORTED_BOUNDARY | verified ATTRIBUTE scope not generalized |

## 26. Default provenance and reopen triggers

Every Battle Runtime Default entry must keep:

- ID;
- Mechanism;
- Question;
- Research Status;
- Why Runtime Must Decide;
- Chosen Runtime Default;
- Evidence Classification;
- Scope;
- Reopen Trigger;
- Tests.

PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN labels may not be removed.

Reopen triggers include:

- new direct model-separating evidence;
- audited cross-contract amendment;
- new official rule/authority;
- Runtime implementation proving a default is unnecessary;
- a higher-authority architecture that changes the deterministic requirement.

Research files remain read-only. Battle defaults never rewrite a Mechanism Contract into pretending the project choice was observed.

## 27. Required future RNG tests

At minimum:

~~~text
insight_rejection_preserves_source_control_rng_parity
deterministic_control_under_insight_adds_no_rng
provider_invalid_skill_consumes_no_activation_rng
skill_permission_denied_consumes_no_activation_rng
forced_single_provocation_adds_no_target_rng
intimidation_rejected_before_binding_consumes_no_binding_rng
intimidation_refresh_consumes_one_authorized_binding_selection
intimidation_resume_consumes_zero_binding_rng
provider_invalid_recovery_consumes_zero_recovery_rng
execution_right_denial_consumes_no_downstream_rng
suppressed_equipment_trigger_consumes_no_downstream_rng
same_seed_same_stage12_rng_trace
~~~

"one authorized binding selection" means one binding-selection operation at the RandomSystem seam,
not a claim about hidden PRNG bit draws.

## 28. Required future event tests

At minimum:

~~~text
repeated_effectiveness_query_emits_no_event
state_suppressed_transition_emits_once_if_public
state_resume_transition_emits_once_if_public
provider_query_emits_no_event
provider_internal_transition_does_not_invent_public_event
admission_reject_event_distinct_from_conflict_reject_by_payload
no_active_attempt_no_exhaustion_block_event
not_preparing_no_interruption_event
failed_transaction_emits_no_applied_or_refreshed_event
capture_action_block_event_owned_by_action_system
capture_damage_prevention_event_owned_by_damage_domain
capture_healing_block_recovery_emits_one_prevented_event
provocation_noop_constraint_does_not_emit_false_forced_target_event
~~~

## 29. Static architecture checks

Future static/audit checks must verify:

~~~text
no direct random module use outside RandomSystem infrastructure
policy queries do not consume BattleContext.random
EventBus handlers do not become permission authorities
all PROJECT_RUNTIME_DEFAULT behavior is ledgered
no Runtime Default provenance labels are silently removed
no Stage13/14/15 gameplay is introduced by Stage12 foundation work
~~~

## 30. Risk register for this governance round

| Risk | Failure mode | Required mitigation |
|---|---|---|
| RNG drift | a rejection path accidentally adds/skips a draw and changes all later seeded outcomes | owner-level draw matrix + zero-RNG policy tests + replay trace |
| Event duplication / phantom fact | queries or pre-commit branches publish facts that never happened | post-decision/commit ownership + transition idempotence tests |
| Default laundering | a project choice loses its provenance and is later cited as researched game truth | mandatory labels, ledger references, provenance audit |
| Hidden second authority | EventBus listener or policy helper starts deciding gameplay | architecture/static scan + composition audit |
| Bounded-unknown leakage | implementation silently picks an unsupported Provocation/Intimidation/Capture/Sabotage behavior | explicit UNSUPPORTED_BOUNDARY / DEFERRED classification and freeze-gate checks |

## 31. Round 9 exit state

~~~text
DQ-SF-12 = CLOSED_BY_SHARED_FOUNDATION_DESIGN
DQ-SF-13 = CLOSED_BY_SHARED_FOUNDATION_DESIGN
DQ-SF-14 = CONTRACT_DEPENDENT_WITH_ARCHITECTURE_CLOSED

BattleContext.random / RandomSystem = sole RNG service
Policy queries = 0 RNG unless an explicit mechanism-specific random owner is delegated
Resume paths = no synthetic RNG
EventBus = fact recorder / dispatcher only
Repeated query = no event
Failed transaction = no false committed event
Runtime Default Ledger = complete for currently required deterministic choices
New Runtime Defaults = NONE
Research = untouched
Stage11 Reopen Required = NO
Gameplay Implementation = NONE
Stage12 Runtime Frozen = 0 / 7
Stage13/14/15 Active = NO
~~~

## 32. Next

Round 10 may now address:

~~~text
DQ-SF-17
Composition Wiring

DQ-SF-18
Final Test Architecture
~~~

After those close, DQ-SF-26 receives the independent Shared Foundation design audit.

## Round 11 Independent Audit Governance Amendment

`AUDIT-DRIVEN CORRECTION — SF-AUD-11-001`

The Round 9 Skill activation topology remains unchanged:

```text
ProviderValidity
→ SkillPermission
→ operation admission
→ activation RNG
→ target operation / target RNG
```

The independent audit corrects its **governance provenance**, not its behavior. Because 690101 EXHAUSTION explicitly leaves blocked-attempt activation RNG unobservable and requires an explicit project choice, the zero-activation-RNG / zero-target-RNG denied-ACTIVE path is now governed by **RD-SF-004** and labeled `PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN`.

Current Battle-owned Runtime Defaults at the Round 11 checkpoint:

```text
RD-SF-001
RD-SF-002
RD-SF-003
RD-SF-004
```

Round 9's historical statement `NEW RUNTIME DEFAULTS = NONE` remains true for Round 9 itself. BU-P02 governance later adds RD-SF-005.

No RNG owner changes. `BattleContext.random / RandomSystem` remains the sole RNG service.


## BU-P02 Runtime Governance Amendment — RD-SF-005

`IMPLEMENTATION_BLOCKER-690108-001` made the previously deferred BU-P02 selection topology mandatory for deterministic implementation. The owner architecture does not reopen.

Current disposition:

```text
DQ-SF-12 architecture = CLOSED
BU-P02 empirical micro-order = BOUNDED UNKNOWN
BU-P02 Runtime implementation choice = RESOLVED_BY_RD-SF-005
```

### Frozen project topology

For a supported fresh RANDOM `CHOOSE_N(N)` operation with one admissible required Provocation Source:

```text
SkillTargetPolicy
  -> required_target_ids=(Source,)
  -> 0 RNG

SkillResolver required-target topology
  -> reserve Source
  -> remaining_slots = N - 1
  -> remaining_population = eligible - Source

TargetSystem.random_units(
    remaining_population,
    count=remaining_slots
)
  -> sole target RNG owner
```

No post-selector replacement is permitted by this default.

### RandomSystem API topology

Within the supported sufficient-candidate scope:

```text
remaining_slots == 0
-> 0 RandomSystem.sample calls

len(remaining_population) == remaining_slots
-> 0 RandomSystem.sample calls
-> deterministic all-candidate order

0 < remaining_slots < len(remaining_population)
-> exactly 1 RandomSystem.sample(population, remaining_slots) call
```

The `remaining_population < remaining_slots` case is **not** normalized here. BU-P09 remains `UNSUPPORTED_BOUNDARY`; legacy TargetSystem truncation is still not promoted into the 690108 contract.

### Scope guard

RD-SF-005 applies to:

```text
NEW_QUERY
+ TargetCardinality.CHOOSE_N
+ TargetSelectorKind.RANDOM
+ admissible required Provocation Source
+ supported sufficient-candidate case
```

It does not reselect:

```text
INHERIT_RESOLVED
DERIVE_FROM_RESOLVED
LOCK_RESOLVED
```

DETERMINISTIC uses the generic required-slot architecture without acquiring an RNG rule from RD-SF-005. EXPLICIT remains outside this BU-P02 random micro-order decision.

### Provenance

```text
PROJECT_RUNTIME_DEFAULT
NOT_EMPIRICALLY_FROZEN
```

This amendment does not claim to discover the original game's hidden target-selection micro-order. It freezes the simulator's replay contract only.

Current Battle-owned Runtime Defaults:

```text
RD-SF-001
RD-SF-002
RD-SF-003
RD-SF-004
RD-SF-005
```
