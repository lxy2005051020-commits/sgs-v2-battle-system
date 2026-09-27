# Stage12 Shared Foundation Composition and Final Test Architecture

> Round: STAGE12_SF_ROUND10_COMPOSITION_WIRING_FINAL_TEST_ARCHITECTURE  
> Date: 2026-09-27  
> Battle baseline: 12b1cd6835f138d790859c72caa7fd3f8d75b0ef  
> Research baseline: e18ae56a4db5662b87458dfa8fdff25dcdd8053b  
> Scope: design / docs only  
> Gameplay implementation: NONE  
> Stage12 Runtime Frozen: 0 / 7  
> Stage13 / Stage14 / Stage15 Active: NO  
> Shared Foundation Design Freeze: NOT YET; DQ-SF-26 independent audit remains mandatory.

## 1. Round 10 verdict

DQ-SF-17 = CLOSED_BY_SHARED_FOUNDATION_DESIGN.

DQ-SF-18 = CLOSED_BY_SHARED_FOUNDATION_DESIGN.

The design now fixes one canonical production dependency graph, explicit construction ownership, explicit consumer injection, explicit legacy migration rules, and a four-layer final test architecture. There are no owner or test-mapping TBDs for frozen claims. Remaining unknowns are named contract boundaries, not unfinished architecture.

## 2. Context resources versus composition root

BattleContext remains the per-battle owner of foundational runtime resources that already exist:

- StateRegistry at context.states;
- SkillRuntimeRegistry at context.skill_runtimes;
- RandomSystem at context.random;
- EventBus at context.event_bus;
- StateGenerationAllocator at context.generation_allocator;
- operation/action progress identity already carried by BattleContext.

BattleSystems remains the production composition root for systems, policies, coordinators, ports and adapters.

This distinction is deliberate. BattleSystems MUST NOT create a second StateRegistry, SkillRuntimeRegistry, EventBus or RandomSystem merely to make Stage12 look centralized. Policies receive BattleContext at query/decision time and therefore observe the same per-battle resources.

For one production battle assembly there is one canonical Shared Foundation object graph. Consumers may be many; canonical policy instances may not be duplicated per consumer.

## 3. Canonical Shared Foundation graph

Conceptual production graph:

~~~
BattleEngine
├─ BattleContext
│  ├─ StateRegistry
│  ├─ SkillRuntimeRegistry
│  ├─ RandomSystem
│  ├─ EventBus
│  └─ StateGenerationAllocator
│
└─ BattleSystems
   ├─ StateLifecycleSystem
   ├─ EquipmentContributionRegistry / read-only adapter
   ├─ DependencyEvaluationSupport
   │
   ├─ StateEffectivenessPolicy
   ├─ ProviderValidityPolicy
   ├─ StateAdmissionPolicy
   ├─ StateConflictPolicy
   ├─ StateRemovalPolicy
   ├─ SkillPermissionPolicy
   ├─ SkillTargetPolicy
   ├─ EquipmentEffectivenessPolicy
   │
   ├─ StateApplicationCoordinator
   ├─ EffectivenessTransitionCoordinator
   ├─ SkillOperationAdmissionCoordinator
   ├─ PreparationInterruptionPort
   │
   ├─ Stage9StateRuntime
   ├─ Stage11StateRuntime
   ├─ ActionSystem
   ├─ NormalAttackSystem
   ├─ SkillResolver
   ├─ TargetSystem
   ├─ TargetResolutionSystem
   ├─ DamageSystem / DamageInstanceCoordinator / DamageResolutionSystem
   ├─ RecoverySystem / RecoveryOpportunitySystem
   ├─ TriggerSystem
   └─ existing Stage1-11 systems
~~~

DependencyEvaluationSupport is infrastructure, not a gameplay owner. It owns the evaluation-session mechanics frozen in Round 3: consumer-to-prerequisite graph traversal, deterministic node keys, memoization, visiting stack, reverse-dependency closure and DependencyCycleError diagnostics. It does not decide whether a state or Provider is effective.

StateEffectivenessPolicy and ProviderValidityPolicy are the typed node evaluators registered into that support exactly once by BattleSystems. The support is not a general service locator and exposes no arbitrary name-to-service lookup.

## 4. Construction order

BattleSystems future Stage12 construction order is frozen as:

1. reuse or construct existing domain primitives such as StateLifecycleSystem, AttributeSystem, TargetSystem and TroopSystem;
2. construct exactly one EquipmentContributionRegistry/read-only adapter;
3. construct exactly one DependencyEvaluationSupport;
4. construct exactly one StateEffectivenessPolicy and ProviderValidityPolicy against the same dependency support;
5. bind those two typed evaluators into DependencyEvaluationSupport exactly once;
6. construct StateAdmissionPolicy, StateConflictPolicy, StateRemovalPolicy, SkillPermissionPolicy, SkillTargetPolicy and EquipmentEffectivenessPolicy;
7. construct PreparationInterruptionPort implementation/placeholder according to the Stage15 boundary;
8. construct EffectivenessTransitionCoordinator, StateApplicationCoordinator and SkillOperationAdmissionCoordinator;
9. construct Stage9StateRuntime and Stage11StateRuntime with the canonical StateEffectivenessPolicy;
10. construct domain consumers with the exact policies/coordinators they require;
11. expose the assembled graph only through typed BattleSystems attributes.

Forbidden production construction pattern:

~~~
consumer(...)
    internally creates StateEffectivenessPolicy(...)
~~~

Also forbidden for any constructor participating in the canonical production graph:

~~~
state_effectiveness_policy or StateEffectivenessPolicy(...)
provider_validity_policy or ProviderValidityPolicy(...)
equipment_policy or EquipmentEffectivenessPolicy(...)
~~~

## 5. Dependency direction and cycle handling

The dependency direction remains:

~~~
domain consumer
→ typed policy/coordinator
→ typed prerequisite or DependencyEvaluationSupport
→ canonical context resource / canonical domain primitive
~~~

StateEffectivenessPolicy and ProviderValidityPolicy may recursively depend on state/provider prerequisite nodes, but they do not construct each other. Cross-node evaluation always enters the shared DependencyEvaluationSupport session. That is the single place owning memoization and cycle detection.

A cycle raises DependencyCycleError with the explicit cycle path. There is no fixed-point iteration, last-writer rule, default allow, default deny or recursive fall-through.

No EventBus callback may resolve a policy dependency. Events are downstream facts, never an authority backchannel.

## 6. State lifecycle and transaction wiring

Application path:

~~~
incoming candidate
→ source-generation RNG if the source contract owns one
→ StateAdmissionPolicy.evaluate_candidate
→ StateConflictPolicy
→ StateApplicationCoordinator validates complete transaction
→ dependency-topology validation
→ StateLifecycleSystem commit
→ EffectivenessTransitionCoordinator recomputes affected closure
→ synchronous domain transition ports
→ committed public facts
~~~

StateLifecycleSystem remains the only physical writer. It does not call StateApplicationCoordinator, so there is no Lifecycle ↔ Coordinator recursion.

Gameplay removal path:

~~~
RemovalRequest
→ StateRemovalPolicy.evaluate_removal
→ snapshot affected decisions
→ dependency-topology validation
→ StateLifecycleSystem.remove
→ EffectivenessTransitionCoordinator recompute
→ synchronous transition ports
→ committed public facts
~~~

Natural expiry, owner-defeat cleanup and battle teardown remain infrastructure and do not pretend to be ordinary cleanse selection.

## 7. Stage9 and Stage11 wiring

Stage9StateRuntime constructor gains the canonical StateEffectivenessPolicy as a required production dependency.

Future method delegation:

- has_operational_insight → StateEffectivenessPolicy.has_effective;
- get_operational_confusion → resident read plus shared effective decision;
- get_taunt_suppressors → shared effective Insight truth, never raw resident Insight;
- get_taunt_lifecycle_state → Stage9 compatibility facade over shared decision;
- is_taunt_operational → shared effectiveness first, then Stage9-specific target/source arbitration.

TargetResolutionSystem continues to receive Stage9StateRuntime. Normal Attack remains outside SkillTargetPolicy.

Stage11StateRuntime constructor gains the same StateEffectivenessPolicy instance. Its instances method remains a resident/order helper. is_effective, effective_instances and has_effective become delegates/derivations of the shared policy. Stage11 hit, critical, reduction, resistance, alert and recovery calculations remain Stage11 domain logic.

Required identity test: Stage9StateRuntime and Stage11StateRuntime reference the same StateEffectivenessPolicy object that other Shared Foundation consumers use.

## 8. Provider and Skill wiring

ProviderValidityPolicy reads Skill Provider identity through BattleContext.skill_runtimes and Equipment Provider identity through the canonical EquipmentContributionRegistry/adapter. It consumes shared effectiveness decisions through DependencyEvaluationSupport.

Skill admission path:

~~~
SkillResolver receives SkillRuntime / operation request
→ SkillOperationAdmissionCoordinator
   → resolve SkillProviderRef
   → ProviderValidityPolicy.evaluate_provider
   → SkillPermissionPolicy.evaluate_operation
→ only if admitted: activation RNG
→ TargetOperation producer
→ SkillTargetPolicy
→ TargetSystem selector / target RNG
→ Effect construction
~~~

SkillResolver must stop treating runtime.enabled as complete Provider truth.

RecoveryOpportunitySystem Gate 4 must construct/resolve SkillProviderRef with explicit slot-is-not-None semantics, include expected skill_id, and delegate current validity to ProviderValidityPolicy before its Gate 5 RNG draw. SkillSlot value 0 is legal and cannot be lost through truthiness.

## 9. Target wiring

Skill path:

~~~
Skill operation
→ TargetOperation producer
→ raw candidate enumeration by TargetSystem
→ SkillTargetPolicy eligibility/constraint
→ TargetSystem selector
→ selected target set
~~~

Normal Attack path:

~~~
NormalAttackSystem
→ TargetResolutionSystem
→ Stage9 Taunt / Confusion arbitration
→ TargetSystem primitives
~~~

The two paths remain visibly separate. Provocation never becomes a Normal Attack redirect rule, and Taunt never becomes a generic SkillTargetPolicy rule.

## 10. Equipment wiring

One EquipmentContributionRegistry/read-only adapter is constructed by BattleSystems.

One EquipmentEffectivenessPolicy is constructed by BattleSystems and consumes:

- EquipmentContributionRegistry;
- ProviderValidityPolicy;
- StateEffectivenessPolicy/DependencyEvaluationSupport for contract-authorized causes.

Consumers share that same EquipmentEffectivenessPolicy:

- AttributeSystem modifier adapter checks ATTRIBUTE contribution effectiveness at query time;
- DamageRuleProvider checks DAMAGE_MODIFIER before returning the contribution;
- RecoveryModifierProvider checks RECOVERY_MODIFIER before aggregate ratio/second CEIL;
- equipment trigger adapter checks TRIGGER/SCHEDULED_TRIGGER at opportunity/due time;
- explicit LIVE_EFFECT dependencies query the policy at use time.

No consumer may hard-code if Sabotage or if FalseReport as its own equipment truth.

## 11. Action, Damage, Recovery and Trigger seams

ActionSystem is the final natural-action owner. Capture natural-action denial is evaluated after action-start maintenance and before any STUN-block consumption or NormalAttack creation. Therefore a Capture denial does not consume a STUN block.

Damage keeps its existing stack. Capture does not become a DamageSystem god branch. The future exact seam is the owning work admission/execution path around DamageInstanceCoordinator.execute_standard_damage_instance / execute_damage_effect and the typed damage request/work descriptor. Current actor plus work category determines whether a new actor-driven damage operation is blocked, while attached Active-origin DOT and contract-approved proxy cases retain their distinct identity.

RecoverySystem preserves:

~~~
base amount
→ modifier
→ second CEIL
→ prevention
   → HealingBlock
   → Capture
→ capacity / troop restore
~~~

Capture is an additional prevention cause in RecoverySystem's prevention phase. StateEffectivenessPolicy never computes recovery amount.

TriggerSystem keeps trigger collection ownership. Only opportunities with a Provider/equipment dependency query ProviderValidityPolicy or EquipmentEffectivenessPolicy. There is no universal query-everything tax on every trigger.

## 12. PreparationInterruptionPort before Stage15

Stage15 remains inactive.

Production composition before a concrete preparation runtime exists may use only an explicit unavailable/no-preparation compatibility implementation whose invariant is that no PREPARING work can exist in this runtime. It must never silently pretend that interruption was implemented.

Tests may inject FakePreparationInterruptionPort.

If real PREPARING work can exist, an affected Stage12 state cannot claim full Runtime Freeze until a concrete owner implements the port. A silent Noop that accepts interruption and does nothing is forbidden as completion evidence.

## 13. ExecutionRightSpec wiring

ExecutionRightSpec remains per-work metadata, not a global manager.

Construction/storage:

- SkillOperationAdmissionCoordinator creates the Skill work spec at admission and stores it on the Skill operation descriptor;
- ActionSystem/ActionScope owns natural-action work identity;
- Damage work carries execution-right dimensions on the damage operation/descriptor owned by DamageInstanceCoordinator;
- RecoveryOpportunitySystem carries the relevant Provider/JIT dimension on the opportunity/descriptor;
- target operations carry their own query/admission granularity.

Evaluation:

- SNAPSHOT_AT_ADMISSION dimensions are frozen by the owner at admission;
- RECHECK_AT_EXECUTION dimensions are evaluated JIT by the owning domain using canonical policies;
- NOT_APPLICABLE is explicit;
- UNSUPPORTED_BOUNDARY rejects/halts the unsupported path rather than guessing.

No GlobalExecutionRightManager is introduced.

## 14. RNG wiring

BattleContext.random remains the sole RNG service.

No Shared Foundation policy, coordinator, transition coordinator, equipment registry or ExecutionRight evaluation creates another PRNG.

Actual draws remain with domain decision owners:

- source mechanism generation;
- Skill activation;
- TargetSystem selector;
- Intimidation binding selector;
- RecoveryOpportunitySystem Gate 5;
- trigger/equipment trigger owner where contract-authorized.

Denied paths consume no downstream-owned RNG. Resume consumes no Intimidation binding RNG. Refresh authorizes a new binding selection.

Static audit must use AST/import/call analysis to find direct random module use or duplicate RandomSystem construction in gameplay code, not a brittle raw-string ban.

## 15. Event wiring

BattleContext.event_bus is the sole event bus for a battle.

Policies and pure queries publish nothing. Domain owners publish committed facts only after the canonical decision/commit. EffectivenessTransitionCoordinator may surface typed transition facts to the owning publisher/port, but it does not mutate gameplay through EventBus listeners.

Forbidden authority inversion:

~~~
policy decision
→ EventBus
→ handler performs required state/domain mutation
~~~

Existing ACTION_BLOCKED, DAMAGE_PREVENTED and RECOVERY_PREVENTED remain owned by their domains. State application/suppression/resume facts follow the Round 9 vocabulary only after the corresponding commit/transition.

## 16. Legacy constructor migration

Production rule:

- new Shared Foundation dependencies are required constructor parameters on production consumers;
- BattleSystems supplies them;
- no canonical-owner fallback construction exists.

Compatibility rule:

- isolated unit tests may use an explicit factory fixture such as build_stage12_test_graph;
- legacy test construction may use a clearly named NON_PRODUCTION compatibility adapter during migration;
- such a factory constructs a complete coherent graph once and injects it, rather than creating per-consumer policies.

Existing unrelated pre-Stage12 defaults such as old formula helpers are not automatically outlawed. The ban is specifically against constructing a second canonical Shared Foundation truth.

Static tests must prove the BattleSystems production path contains no fallback Shared Foundation owner construction.

## 17. Four-layer final test architecture

Layer 1: Shared Foundation unit and composition tests.

- tests/test_stage12_state_admission.py
- tests/test_stage12_state_lifecycle_transaction.py
- tests/test_stage12_state_effectiveness.py
- tests/test_stage12_provider_validity.py
- tests/test_stage12_skill_permission.py
- tests/test_stage12_target_policy.py
- tests/test_stage12_equipment_effectiveness.py
- tests/test_stage12_execution_rights.py
- tests/test_stage12_rng_governance.py
- tests/test_stage12_event_governance.py
- tests/test_stage12_wiring.py
- tests/test_stage12_architecture_static.py

Layer 2: seven state contract suites.

- tests/test_stage12_690089_insight.py
- tests/test_stage12_690101_exhaustion.py
- tests/test_stage12_690107_false_report.py
- tests/test_stage12_690108_provocation.py
- tests/test_stage12_690222_intimidation.py
- tests/test_stage12_690109_sabotage.py
- tests/test_stage12_690110_capture.py

Mandatory numerical floors remain exactly those already frozen:

- FALSE_REPORT >= 30;
- PROVOCATION >= 25;
- INTIMIDATION >= 21.

No invented numeric floor is created for the other four states; they must cover every contract obligation.

Layer 3: cross-state and Stage11 regression.

- tests/test_stage12_cross_state.py
- tests/test_stage12_stage11_regressions.py

Layer 4: whole-system acceptance.

- full pytest suite;
- demo;
- deterministic replay checks;
- static architecture audit;
- PR/commit CI.

## 18. Mandatory cross-state matrix

Stage12 minimum:

- Insight × Exhaustion
- Insight × FalseReport
- Insight × Provocation
- Insight × Intimidation
- Insight × Sabotage
- Insight × Capture
- Exhaustion × Provocation
- Exhaustion × FalseReport
- Exhaustion × Intimidation
- Exhaustion × Capture
- FalseReport × Intimidation
- FalseReport × Capture
- FalseReport × Sabotage
- Provocation × Confusion
- Provocation × Taunt
- Provocation × Capture
- Intimidation × Capture
- Sabotage × Capture
- FalseReport-source × Provocation dependency discriminator

Stage11/legacy minimum:

- STUN × CAPTURE
- WEAKNESS × CAPTURE
- HEALING_BLOCK × CAPTURE
- CONFUSION × PROVOCATION
- TAUNT × PROVOCATION
- DISARM × INSIGHT
- STUN × INSIGHT
- Damage Pipeline × CAPTURE
- Recovery Pipeline × CAPTURE
- INSIGHT × CONFUSION authority-migration discriminator

## 19. No-regression definition

For a legacy battle that contains no Stage12 state and does not opt into new Stage12 metadata:

- battle outcome must be unchanged;
- event sequence/order must be unchanged;
- RNG consumption trace must be unchanged;
- canonical owner count must not increase per consumer;
- Provider/source provenance must be unchanged;
- Stage9/10/11 frozen semantics remain unchanged.

Passing pytest alone is not sufficient evidence for this invariant.

## 20. Contract-to-test traceability rule

Every frozen claim must resolve to:

~~~
Contract Rule
→ Canonical Owner
→ Method / Seam
→ Positive Test
→ Negative Test
→ Discriminator Test
→ Evidence Class
→ Default ID or NONE
→ Design Status
~~~

Allowed Evidence Class values:

- RESEARCH_CONFIRMED
- OBSERVED
- INFERRED_BOUNDED
- PROJECT_DEFAULT
- UNSUPPORTED_BOUNDARY
- SOURCE_SKILL_SCOPE

UNSUPPORTED_BOUNDARY receives an executable negative/explicit-failure test. It is not left without a test merely because the gameplay answer is unknown.

## 21. Static architecture audit

Required semantic scans:

- one canonical StateEffectivenessPolicy instance per production BattleSystems graph;
- one canonical ProviderValidityPolicy instance;
- one canonical SkillPermissionPolicy instance;
- one canonical SkillTargetPolicy instance;
- one canonical EquipmentEffectivenessPolicy instance;
- no Shared Foundation policy self-construction fallback;
- no direct StateRegistry mutation outside StateLifecycleSystem-authorized storage seams;
- no direct random module gameplay use and no duplicate RandomSystem construction;
- no EventBus permission ownership;
- no duplicated Stage12 state-id decision ladder across consumers;
- no source_skill_slot truthiness gate;
- no Provider attribution-to-dependency inference;
- no Stage13/14/15 gameplay implementation leakage;
- no unledgered PROJECT_RUNTIME_DEFAULT.

AST/class-call analysis is preferred over raw substring bans.

## 22. Wiring identity tests

Mandatory tests include:

- battle_systems_uses_single_state_effectiveness_policy
- battle_systems_uses_single_provider_validity_policy
- stage9_stage11_share_same_effective_truth
- skill_and_recovery_share_same_provider_validity
- equipment_consumers_share_same_equipment_policy
- dependency_support_is_shared_and_cycle_safe
- event_bus_is_shared_but_not_authority
- production_path_has_no_shared_policy_fallback
- explicit_test_factory_builds_one_coherent_graph

## 23. Remaining boundaries, not TBDs

The following remain explicit evidence/integration boundaries:

- Intimidation exact selection weights: DEFERRED;
- Intimidation empty eligible pool: UNSUPPORTED_BOUNDARY;
- Provocation insufficient candidates BU-P09: UNSUPPORTED_BOUNDARY;
- Provocation multi-source/reapplication BU-P06: UNSUPPORTED_BOUNDARY;
- Sabotage broader queued/in-flight JIT B-SAB-07: UNSUPPORTED_BOUNDARY;
- Capture Q16 / Q44 / Q45 and other named contract-bounded work cases: UNSUPPORTED_BOUNDARY where already ledgered;
- concrete preparation owner: integration dependency while Stage15 is inactive.

None of these is an owner TBD. None authorizes a silent allow/deny/default.

## 24. Risk register

| Risk | Round 10 mitigation |
|---|---|
| duplicate canonical owner | BattleSystems constructs one graph; identity tests |
| legacy fallback owner | strict production injection; explicit non-production factory only |
| policy cycle | shared DependencyEvaluationSupport + DependencyCycleError |
| RNG drift | context.random only; denied-path zero-draw tests; replay trace |
| event duplication | post-commit publication + idempotence tests |
| default laundering | ledger-ID audit; no new Round 10 default |
| provider / holder confusion | ProviderRef identity and holder permission remain separate |
| resident / effective confusion | StateRegistry residency and StateEffectivenessPolicy authority separate |
| suppression / removal confusion | policy decision vs Lifecycle physical mutation separate |
| resume / reinitialize confusion | same live instance/binding; future-only behavior |
| Stage13+ leakage | static scope audit |
| bounded unknown silently allowed | explicit UNSUPPORTED_BOUNDARY tests |
| Noop preparation false completeness | unavailable-port invariant + Runtime Freeze gate |

## 25. Round 10 exit gate

~~~
DQ-SF-17 = CLOSED_BY_SHARED_FOUNDATION_DESIGN
DQ-SF-18 = CLOSED_BY_SHARED_FOUNDATION_DESIGN

Shared Foundation owner graph = COMPLETE
duplicate canonical owner = 0 by design
owner TBD = 0
test mapping TBD for frozen claims = 0 by design
BattleSystems wiring design = COMPLETE
legacy migration design = COMPLETE

Stage11 Reopen Required = NO
Gameplay Implementation = NONE
Stage12 Runtime Frozen = 0 / 7
Stage13 / Stage14 / Stage15 Active = NO

Shared Foundation Design Freeze = NOT YET
NEXT = DQ-SF-26 Independent Design Audit
~~~

## Round 11 independent-audit amendment

`AUDIT-DRIVEN CORRECTION`

The independent audit preserves the Round 10 composition graph and adds two governance/coverage clarifications:

1. EXHAUSTION denied-ACTIVE zero activation/target RNG is governed by RD-SF-004 because the Research contract leaves blocked-attempt hidden RNG unobservable.
2. The semantic slot-0 static audit covers both RecoveryOpportunitySystem's liveness gate and TriggerSystem's provenance fallback. TriggerSystem must preserve `source_skill_slot == 0` using explicit `is not None` precedence; this does not turn provenance into a live Provider dependency.

No canonical owner, construction order, fallback rule, Stage13+ boundary, or gameplay implementation changes.
