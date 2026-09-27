# Stage12 Capture Composite Execution / Admitted-Queued-JIT Boundary Design

Date: 2026-09-27
Round: STAGE12_SF_ROUND8_CAPTURE_COMPOSITE_EXECUTION_DESIGN
Status: DESIGN FROZEN FOR DQ-SF-19; DQ-SF-23 ARCHITECTURE CLOSED / CONTRACT DEPENDENT
Gameplay implementation in this round: NONE

## 1. Repository and authority lock

Round 8 starts from:

- Battle main: d5ed78e0eb3e9e391e8521d48d9379f1401140d5
- Research main: e18ae56a4db5662b87458dfa8fdff25dcdd8053b
- Round 7 CI: 36296049746 / success
- pytest baseline: 913 passed
- demo smoke: PASS
- independent audit snapshot upload: PASS
- 690110 CAPTURE: Research FROZEN / Contract v1.0-frozen

Research remains read-only in this round.

This round is design/docs only. It implements no CAPTURE gameplay and changes no Action/Damage/Recovery/Provider/Target/Equipment runtime code.

## 2. Scope

This round closes two architecture questions:

~~~text
DQ-SF-19
Capture Composite Owner Matrix

DQ-SF-23
new / admitted / queued / attached / locked / execution-time JIT boundary
~~~

It does not close the following gameplay evidence boundaries:

~~~text
Capture Q16  already-created DamageRequest
Capture Q23  detached passive-created state
Capture Q34  Emergency Aid discriminator
Capture Q42  ALL_ALLIES targeting
Capture Q44  delayed friendly work
Capture Q45  already-locked friendly target
Capture Q63  equipment reactive/damage special
Capture Q70-Q74 reapplication / multisource
Capture Q78  holder-death cleanup internals
Sabotage B-SAB-07 collected / queued / JIT micro-order
hidden universal damage guard = NON-CLAIM
~~~

## 3. Canonical invariant

CAPTURE is a Composite State.

It is not:

~~~text
CaptureRuntime.do_everything()
~~~

CAPTURE provides state-derived rule facts. The canonical domain owner makes the final decision.

~~~text
Capture State
    |
    +-> ActionSystem
    +-> Damage domain admission/execution seam
    +-> ProviderValidityPolicy
    +-> RecoverySystem
    +-> SkillTargetPolicy
    +-> EquipmentEffectivenessPolicy
    +-> StateLifecycleSystem for physical lifetime only
~~~

There is no Capture God Object.

## 4. Existing runtime architecture audit

### 4.1 FutureAdmissionGate

Current FutureAdmissionGate is the Stage9 authority for future branches while BattleTerminationState is RUNNING.

It governs typed permits for:

~~~text
NEXT_ACTION
ASSAULT
COMBO_SECOND_NORMAL_ATTACK
COUNTER_BATCH
CHAIN_TRAVERSAL
CLEAVE_EFFECT
~~~

It does not currently answer current actor CAPTURE permission.

Decision:

~~~text
REUSE AS-IS FOR FUTURE BRANCH ADMISSION
DO NOT TURN IT INTO A CAPTURE / STATE PERMISSION ENGINE
~~~

### 4.2 ExecutionRightSystem

Current ExecutionRightSystem evaluates typed RuleIntentExecutionDescriptor liveness. Important frozen behavior already includes:

- battle-finalized abort;
- state-owner defeat scope;
- physical state-instance existence;
- STUN is explicitly not a generic RuleIntent suppressor;
- Stage10 persistent DOT/HoT and already-admitted hooks remain reachable;
- target defeat is current-only rejection, never an automatic owner-tail abort.

Decision:

~~~text
PRESERVE THESE INVARIANTS
EXTEND ONLY AS SHARED MECHANICAL EXECUTION-RIGHT INFRASTRUCTURE IF NEEDED
DO NOT MAKE IT THE OWNER OF ACTION / DAMAGE / RECOVERY / TARGET / EQUIPMENT TRUTH
~~~

### 4.3 ActionSystem

Current ActionSystem performs ACTION_START maintenance, then consumes STUN at the natural-action block seam, then enters NormalAttackSystem.

CAPTURE therefore belongs at natural-action admission before NormalAttack creation.

The existing one-step STUN consumption call cannot simply be preceded by another arbitrary if statement. Round 8 freezes a two-phase architecture described below.

### 4.4 Damage stack

Current DamageRequest contains source_id and provenance fields, but it does not provide a universal current-actor field.

OperationLineage separately exposes:

~~~text
physical_attacker
physical_skill
credit_owner
source_type
~~~

Therefore:

~~~text
source_id != universal current actor
historical provider != universal current actor
credit owner != universal current actor
~~~

Stage12 integration needs typed work metadata and must not infer CAPTURE actor permission from source_id alone.

### 4.5 CounterSystem

Current CounterSystem:

1. admits a CounterBatch;
2. preserves batch/entry identity;
3. checks current entry owner liveness;
4. creates local Counter DamageRequest;
5. executes through DamageInstanceCoordinator.

This matches the frozen Stage9 admitted-reaction model.

CAPTURE must not retroactively delete the admitted CounterBatch.

### 4.6 RecoverySystem

Current RecoverySystem ordering is:

~~~text
target alive
-> recovery modifier
-> second CEIL
-> HealingBlock prevention
-> troop restore / recovery capacity
~~~

CAPTURE must join the prevention topology without moving existing modifier/CEIL or restore/capacity ownership.

## 5. DQ-SF-19 verdict

~~~text
DQ-SF-19
= CLOSED_BY_SHARED_FOUNDATION_DESIGN
~~~

Architecture closure means the composite owner split and runtime seams are frozen. It does not mean CAPTURE is implemented.

## 6. Capture Composite Owner Matrix

| Capture effect | Canonical owner | Frozen design |
|---|---|---|
| Natural Action denied | ActionSystem | pure CAPTURE action-eligibility check before consumable STUN blocking |
| Normal Attack attempt | ActionSystem -> NormalAttackSystem | no NormalAttack operation if natural action denied |
| New Skill admission | existing SkillOperationAdmissionCoordinator where contract applies | no independent Capture skill engine |
| PASSIVE / COMMAND Provider suppression | ProviderValidityPolicy | effective CAPTURE contributes Provider suppression cause |
| New actor-driven damage | Damage domain admission/execution seam | current actor + typed work category decide CAPTURE denial |
| Counter damage | CounterSystem batch + Damage domain local damage permission | batch retained; no counter damage |
| Existing Active-origin DOT | existing attached/persistent owner + Damage domain | admitted continuation; CAPTURE actor gate does not reclassify it |
| Received recovery | RecoverySystem | CAPTURE prevention cause after modifier/second CEIL |
| Friendly SINGLE / CHOOSE_N target exclusion | SkillTargetPolicy | verified fresh-query scope only |
| Equipment attribute suppression | EquipmentEffectivenessPolicy | verified ATTRIBUTE scope only |
| Physical CAPTURE lifetime/removal | StateLifecycleSystem | source death does not auto-remove |

## 7. Natural Action boundary

CAPTURE contract:

~~~text
effective CAPTURE
-> Natural Action denied
~~~

The denied Natural Action is upstream of:

~~~text
NormalAttackSystem
TargetResolutionSystem
Normal Attack target RNG
Normal Attack Damage
~~~

Therefore ActionSystem is the only required natural-action integration owner.

No global CAPTURE check is added to NormalAttackSystem.

## 8. CAPTURE + STUN composition

CAPTURE and STUN can both explain why a unit does not act, but they are not the same mechanic.

Required two-phase action block architecture:

~~~text
Phase A: non-consuming action eligibility
    - death / battle-level prerequisites
    - CAPTURE natural-action denial
    - other future non-consuming eligibility blockers

if denied:
    -> no consumable action-block counter is spent
    -> no NormalAttack operation

Phase B: consumable behavioral blocker
    - STUN remaining block consumption
    - other explicitly consumable blockers

if blocked:
    -> consume only the blocker that actually owns this blocked opportunity
~~~

Thus:

~~~text
CAPTURE + STUN
-> action denied by CAPTURE eligibility
-> STUN remaining_blocks unchanged
~~~

This is not first-if-wins. It is a frozen ownership topology based on whether the opportunity reaches the consumable blocker seam.

Public multi-reason event presentation remains DQ-SF-13.

## 9. Normal Attack consequence

If CAPTURE denies the Natural Action:

~~~text
no NormalAttackInstance
no NormalAttack target resolution
no NormalAttack target RNG
no NormalAttack damage
~~~

This is consequence of upstream Action denial, not a second CAPTURE rule inside NormalAttackSystem.

## 10. Actor / Provider / Source role model

Round 8 freezes these roles as distinct:

~~~text
Current Actor
Origin Provider
Historical Source
Effect Holder
Damage Source
Damage Target
Credit Owner
~~~

A runtime object may have the same unit in several roles, but identity equality is data, not architecture.

No single source_id field may stand in for all roles.

## 11. Minimal work execution metadata

No UniversalWorkId is introduced.

Each domain keeps its existing identity.

Shared execution-right metadata may be represented by an equivalent structure:

~~~text
WorkExecutionDescriptor:
    operation_identity        # domain-specific ID
    work_category
    current_actor_id?         # only when ACTOR_PERMISSION applies
    origin_provider_ref?
    historical_source_id?
    effect_holder_id?
    target_provenance?
    execution_right_spec
~~~

This is metadata carried by the owning operation. It is not a new gameplay owner.

## 12. Damage work taxonomy

Minimum Round 8 taxonomy:

~~~text
NEW_ACTOR_DRIVEN_DAMAGE
COUNTER_DAMAGE
ATTACHED_EXISTING_DOT
FREE_PROXY_DAMAGE
ALREADY_CREATED_DAMAGE_REQUEST
OTHER_BOUNDED
~~~

This is not a full future damage taxonomy. It exists only to prevent CAPTURE from collapsing distinct contracts into source_id-based suppression.

## 13. New actor-driven damage

Verified rule:

~~~text
current actor is CAPTURED
+
work category = NEW_ACTOR_DRIVEN_DAMAGE
-> damage opportunity denied
~~~

The denial belongs to the Damage domain admission/execution-right seam.

It must occur before damage-owned calculation/RNG/observable settlement for that denied work.

Do not calculate ordinary damage and then merely overwrite the final amount to zero.

## 14. CAPTURE denial is not WEAKNESS

WEAKNESS Stage11 semantics are legal damage work whose output becomes zero in the damage pipeline.

CAPTURE new actor-driven semantics are denial of the damage opportunity.

Therefore:

~~~text
CAPTURE != WEAKNESS
~~~

Shared result shapes may be reused internally, but CAPTURE must not call the Weakness gameplay rule.

## 15. Counter boundary

Frozen observable contract:

~~~text
captured counter actor
-> no counter damage
~~~

Round 8 preserves:

~~~text
admitted CounterBatch identity
entry ordering
Stage9 admitted-entry invariant
current entry-owner liveness checks
~~~

CAPTURE does not retroactively cancel the batch.

The local damage opportunity for a Counter entry carries:

~~~text
work_category = COUNTER_DAMAGE
current_actor_id = entry.owner_id
ACTOR_PERMISSION = RECHECK_AT_EXECUTION
~~~

If the actor is currently captured, the Damage domain denies the local damage opportunity.

Whether COUNTER_EXECUTE remains a public event before this denial is DQ-SF-13. Round 8 does not manufacture an event answer.

## 16. Counter vs attached DOT discriminator

Two frozen facts coexist:

~~~text
captured actor Counter
-> no damage

previously attached Active-origin DOT
-> continues
~~~

Therefore this model is forbidden:

~~~text
if source_id has CAPTURE:
    block all outgoing damage
~~~

## 17. Attached Active-origin DOT

An already attached Active-origin DOT is admitted persistent continuation.

For the CAPTURE actor-permission dimension:

~~~text
ACTOR_PERMISSION = NOT_APPLICABLE
~~~

The tick is not a new action by the original Provider merely because the historical source/provenance points to that unit.

If the attached effect explicitly declares a live ProviderDependency, that independent dimension still follows ProviderValidityPolicy. Round 8 does not delete legitimate dependencies.

## 18. Free proxy actor boundary

Required discriminator:

~~~text
A historically originated a mechanism
A is now CAPTURED
B is the free current proxy actor
B legally executes damage
-> B is not blocked merely because provenance points to A
~~~

The actor gate checks B.

A remains origin Provider / historical provenance as applicable.

## 19. Q16 already-created DamageRequest

Capture Q16 remains bounded.

A DamageRequest may exist before a DamageInstance is admitted.

Round 8 refuses to guess whether CAPTURE applies at that micro-slice.

Required representation:

~~~text
work_category = ALREADY_CREATED_DAMAGE_REQUEST
ACTOR_PERMISSION = UNSUPPORTED_BOUNDARY
~~~

Runtime integration may not silently choose SNAPSHOT or JIT for Q16 without later authority or a lawful PROJECT_RUNTIME_DEFAULT.

## 20. Recovery composite

CAPTURE received recovery:

~~~text
Recovery reaches captured holder
-> final recovered troops = 0
~~~

RecoverySystem remains owner.

Frozen architecture:

~~~text
base recovery
-> modifier composition
-> second CEIL
-> prevention phase
      HealingBlock cause?
      CAPTURE cause?
-> if prevented: zero / no troop restore
-> otherwise Recovery Capacity / troop restore
~~~

No target policy shortcut is permitted.

## 21. CAPTURE + HealingBlock

Both can apply to the same recovery.

Internal topology must be able to retain multiple causes:

~~~text
HEALING_BLOCK
CAPTURE
~~~

Final recovery remains zero.

Round 8 does not choose the final public dominant reason/event payload. That is DQ-SF-13.

A future minimal RecoveryPreventionDecision may carry a cause set while preserving compatibility with the current single-reason RecoveryPreventedResult adapter.

## 22. Provider composite

Verified PASSIVE / COMMAND provider suppression remains entirely ProviderValidityPolicy-owned.

CAPTURE only contributes a typed suppression cause.

It does not:

- delete the Provider;
- delete historical effects;
- pause physical state lifetime by default;
- replay missed triggers after resume.

Source death does not end established CAPTURE and therefore is not a universal Provider/execution gate.

## 23. Equipment composite

Verified CAPTURE equipment ATTRIBUTE suppression remains EquipmentEffectivenessPolicy-owned.

Capture Q63 equipment reactive/damage special remains:

~~~text
UNSUPPORTED_BOUNDARY
~~~

Round 8 does not generalize CAPTURE into SABOTAGE-lite.

## 24. Target composite

Verified fresh friendly target operations:

~~~text
ALLY SINGLE
ALLY CHOOSE_N
-> captured holder excluded
~~~

SkillTargetPolicy remains owner.

Capture Q42 ALL_ALLIES remains bounded.

Self recovery may still reach the captured holder and then be zeroed by RecoverySystem.

## 25. DQ-SF-23 work lifecycle model

Round 8 freezes this minimum vocabulary:

~~~text
NEW
ADMITTED
QUEUED
ATTACHED
EXECUTING
SETTLED
~~~

TARGET_LOCKED is orthogonal provenance, not an exclusive lifecycle state.

Examples:

~~~text
ADMITTED + QUEUED + TARGET_LOCKED
ADMITTED + ATTACHED
ADMITTED + EXECUTING
~~~

This avoids pretending every domain follows one linear queue structure.

## 26. Admission identity

Admission creates or binds a stable domain identity.

Examples already available in the runtime include:

~~~text
ActionId
NormalAttackInstanceId
DamageInstanceId
ReactionBatchId / CounterBatchEntryId
TargetOperationId
StateApplicationGenerationId
RecoveryOpportunity identity / owning state generation
~~~

Round 8 adds no UniversalWorkId.

Queued/attached work retains the original domain identity required for replay safety and provenance.

## 27. ExecutionRightSpec

Each work category carries per-dimension stability metadata.

Modes:

~~~text
SNAPSHOT_AT_ADMISSION
RECHECK_AT_EXECUTION
NOT_APPLICABLE
UNSUPPORTED_BOUNDARY
~~~

Dimensions:

~~~text
ACTOR_PERMISSION
PROVIDER_VALIDITY
TARGET_ELIGIBILITY
EQUIPMENT_CONTRIBUTION
STATE_EFFECTIVENESS
~~~

No single recheck_on_execute boolean is lawful.

## 28. Snapshot vs JIT anchors

### Already-admitted Active under later EXHAUSTION

Skill permission:

~~~text
SNAPSHOT_AT_ADMISSION
~~~

Later EXHAUSTION does not rollback the admitted Active chain.

Other dimensions may still JIT when their own contract explicitly requires it.

### Provider-dependent RecoveryOpportunity

Provider validity:

~~~text
RECHECK_AT_EXECUTION
~~~

The Provider check occurs before recovery probability RNG.

### Attached Active DOT under CAPTURE

CAPTURE actor permission:

~~~text
NOT_APPLICABLE
~~~

The attached tick continues.

### New actor-driven damage

Actor permission:

~~~text
RECHECK_AT_EXECUTION
~~~

Captured current actor is denied.

### Scheduled equipment due window

Equipment contribution:

~~~text
RECHECK_AT_EXECUTION
~~~

for the already frozen Round 7 due-window scope.

## 29. No universal JIT

Forbidden:

~~~text
on every execution:
    rerun every policy
~~~

This would break:

- admitted Active stability;
- attached DOT continuation;
- locked target provenance;
- RNG/event topology.

## 30. No universal snapshot

Also forbidden:

~~~text
once admitted:
    never recheck anything
~~~

This would break known JIT cases such as Provider-dependent RecoveryOpportunity and tested equipment scheduled due-window execution.

## 31. Q44 delayed friendly work

Capture Q44 remains bounded.

A delayed item must carry explicit per-dimension modes for:

~~~text
ACTOR_PERMISSION
PROVIDER_VALIDITY
TARGET_ELIGIBILITY
~~~

where applicable.

Unknown dimensions are UNSUPPORTED_BOUNDARY, not guessed.

## 32. Q45 already-locked friendly target

Capture Q45 remains bounded.

The work retains:

~~~text
LOCKED target provenance
original target identity
target recheck mode
~~~

If a future contract freezes no target recheck, the target is retained without re-entering SkillTargetPolicy.

If a future contract freezes execution-time eligibility recheck, the same locked target may be checked without silently allocating a new TargetOperationId or target-selection RNG.

LOCKED never silently becomes NEW_QUERY.

## 33. Sabotage B-SAB-07 connection

Round 7 already freezes the tested scheduled due-window JIT result.

Broader:

~~~text
collected
queued
state changes
execute later
~~~

micro-order remains B-SAB-07 / DQ-SF-23 bounded.

Representation:

~~~text
EQUIPMENT_CONTRIBUTION = UNSUPPORTED_BOUNDARY
~~~

outside the tested due-window anchor.

## 34. JIT failure result

When a dimension declared RECHECK_AT_EXECUTION fails:

~~~text
SKIP / DENY current execution opportunity
~~~

Default shared behavior is not:

~~~text
requeue
replay on resume
backfill missed window
~~~

A mechanism must explicitly authorize such behavior to get it.

## 35. RNG boundary

ExecutionRightSpec and pure execution-right evaluation consume zero RNG.

Known order:

~~~text
Provider-dependent RecoveryOpportunity
-> ProviderValidity JIT
-> if valid, recovery probability RNG
~~~

For CAPTURE actor-driven damage, denial must precede any RNG owned by the denied damage work.

Final RNG ownership/signature/ordering governance remains DQ-SF-12.

## 36. Event boundary

The deciding domain owner owns the fact.

EventBus records facts later.

Forbidden topology:

~~~text
Capture handler publishes event
-> DamageSystem listens
-> event decides permission
~~~

Public event vocabulary, reason priority and multi-reason serialization remain DQ-SF-13.

## 37. Restoration

When CAPTURE ends, future lawful opportunities resume through their domain owners:

~~~text
future Natural Action
future actor-driven damage
PASSIVE / COMMAND Provider validity
future received recovery
fresh friendly targeting
verified equipment attributes
~~~

No replay:

~~~text
no missed action replay
no missed counter replay
no missed recovery replay
no missed trigger replay
~~~

## 38. Source death and holder death

Established CAPTURE survives source death.

Therefore:

~~~text
origin source alive?
~~~

cannot be a universal future-execution condition.

Capture Q78 holder-death cleanup internals remain bounded. Physical battle lifecycle/teardown owners remain authoritative.

## 39. Runtime defaults

New Runtime Defaults added in Round 8:

~~~text
NONE
~~~

Reason:

- Q16 can remain UNSUPPORTED_BOUNDARY.
- Q44 can remain UNSUPPORTED_BOUNDARY.
- Q45 can remain UNSUPPORTED_BOUNDARY.
- B-SAB-07 can remain UNSUPPORTED_BOUNDARY.

Design can proceed without inventing gameplay behavior.

RD-SF-001, RD-SF-002 and RD-SF-003 remain the complete Shared Foundation Runtime Default set.

## 40. Planned tests

Capture Action:

~~~text
capture_blocks_natural_action
capture_block_does_not_consume_stun_block
capture_removal_allows_future_action_no_replay
~~~

Damage:

~~~text
capture_blocks_new_actor_driven_damage
capture_blocks_counter_damage
capture_does_not_block_existing_active_dot
free_proxy_damage_not_blocked_by_historical_captured_origin
weakness_and_capture_remain_distinct_damage_semantics
~~~

Execution rights:

~~~text
already_admitted_active_permission_not_rechecked_by_exhaustion
execution_right_dimensions_can_mix_snapshot_and_jit
provider_jit_failure_does_not_requeue
bounded_damage_request_policy_is_explicit
bounded_locked_target_policy_is_explicit
no_universal_jit_recheck
no_universal_snapshot
~~~

Architecture:

~~~text
capture_has_no_universal_runtime_owner
domain_owners_remain_canonical
execution_right_spec_is_rng_free
event_bus_does_not_decide_execution_right
source_id_not_equal_current_actor
future_admission_gate_is_not_capture_permission_owner
~~~

These are design obligations only. No executable tests are added in Round 8.

## 41. DQ-SF-23 verdict

~~~text
DQ-SF-23
= CONTRACT_DEPENDENT_WITH_ARCHITECTURE_CLOSED
~~~

Architecture is closed because the system can represent every known snapshot/JIT combination and can explicitly refuse unknown combinations.

Gameplay micro-boundaries remain bounded where Research remains bounded.

## 42. Round 8 exit gate

~~~text
DQ-SF-19 = CLOSED_BY_SHARED_FOUNDATION_DESIGN
DQ-SF-23 = CONTRACT_DEPENDENT_WITH_ARCHITECTURE_CLOSED

Capture composite owner matrix = FROZEN
No Capture God Object = FROZEN

new work != admitted work = FROZEN
admitted work != universally immutable = FROZEN
JIT recheck is per-dimension = FROZEN

DOT continuation = EXPLAINED
Counter denial = EXPLAINED
Free proxy actor boundary = MODELED

Q16 = BOUNDED / PRESERVED
Q44 = BOUNDED / PRESERVED
Q45 = BOUNDED / PRESERVED
B-SAB-07 = BOUNDED / PRESERVED

Stage11 Reopen Required = NO
Gameplay Implementation = NONE
Stage12 Runtime Frozen = 0 / 7
Stage13 Active = NO
Stage14 Active = NO
Stage15 Active = NO
~~~

Shared Foundation Design Freeze remains NOT YET.

## 43. Next

Next governance round:

~~~text
DQ-SF-12 RNG Governance
DQ-SF-13 Event Model
DQ-SF-14 Runtime Default finalization
~~~

After that:

~~~text
DQ-SF-17 Composition Wiring
DQ-SF-18 Final Test Architecture
DQ-SF-26 Independent Design Audit
~~~
