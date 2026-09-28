# Stage12 Runtime Owner Matrix

> Status: **FROZEN OWNER DESIGN / IMPLEMENTATION COMPLETE / 7 OF 7 RUNTIME FREEZES VALID / FINAL COMPLETION AUDIT CANDIDATE**nonical constraint: one responsibility may not have two competing canonical owners.

| Responsibility | Current Owner | Stage12 Owner Decision | States | Change |
|---|---|---|---|---|
| State physical storage | StateRegistry | StateRegistry | all 7 | REUSE |
| State lifecycle mutation | StateLifecycleSystem | StateLifecycleSystem | all 7 | REUSE / EXTEND |
| State physical lifetime clock | mixed Stage10/11 mechanisms | `StateLifecycleSystem` with explicit clock domains / typed Stage12 lifetime metadata | all 7 | DESIGN FIXED / FUTURE EXTEND |
| Resident/effective interpretation | Stage9/Stage11 local readers | `StateEffectivenessPolicy` | all resident states requiring current authority | NEW CANONICAL SHARED OWNER; Stage9/11 DELEGATE |
| State admission / immunity | Stage11-specific application policy only | `StateAdmissionPolicy` pure decision owner, invoked before state conflict | INSIGHT + protected/special boundaries | NEW CANONICAL SHARED OWNER |
| State conflict / reapplication | mixed rules inside Lifecycle/application modules | `StateConflictPolicy` pure per-contract decision owner | all 7 | NEW CANONICAL SHARED OWNER |
| State application transaction orchestration | implicit inside Lifecycle.apply | `StateApplicationCoordinator` prepares immutable transaction; `StateLifecycleSystem` alone commits | all 7 | NEW NON-WRITING COORDINATOR |
| State removal / cleanse eligibility | no shared canonical owner | `StateRemovalPolicy` pure gameplay-removal eligibility owner; Lifecycle keeps physical remove primitive | all 7 | NEW CANONICAL SHARED OWNER |
| Natural action admission | ActionSystem | ActionSystem | CAPTURE | EXTEND |
| Normal attack permission | NormalAttackSystem | NormalAttackSystem | EXHAUSTION negative discriminator; Capture action interaction | REUSE |
| Skill identity / slots | SkillRuntime + SkillRuntimeRegistry | same registry + frozen SkillProviderRef(owner_id, slot, skill_id) identity | EXHAUSTION, FALSE_REPORT, INTIMIDATION, CAPTURE | REUSE / DESIGN FIXED |
| Skill category recognition | insufficient general taxonomy | SkillDefinition metadata: SkillType ACTIVE/ASSAULT/PASSIVE/COMMAND/TROOP/FORMATION/TALENT + PreparationMode NONE/REQUIRED; TALENT is a 690107 negative discriminator and is not implicitly eligible for Intimidation | EXHAUSTION, FALSE_REPORT, INTIMIDATION, CAPTURE | DESIGN FIXED / FUTURE SCHEMA |
| Skill permission | none canonical | SkillPermissionPolicy, holder-level permission only | EXHAUSTION | NEW CANONICAL MINIMAL OWNER; DESIGN FIXED |
| Skill operation admission composition | SkillResolver local enabled gate | SkillOperationAdmissionCoordinator composes ProviderValidityPolicy + SkillPermissionPolicy before observable activation/RNG | EXHAUSTION + all skill Providers | NEW THIN COORDINATOR; DESIGN FIXED |
| Preparation interruption request | none | PreparationInterruptionPort implemented later by the true preparation owner | EXHAUSTION, INTIMIDATION | NEW MINIMAL PORT; DESIGN FIXED / IMPLEMENTATION DEPENDENCY |
| Skill Provider validity | none canonical | `ProviderValidityPolicy` after ProviderRef identity resolution | FALSE_REPORT, INTIMIDATION, CAPTURE; explicit provider-dependent effects | NEW CANONICAL SHARED OWNER |
| Skill target operation / eligibility / constraints | SkillResolver + TargetSystem | producer creates `TargetOperation`; `TargetSystem` supplies raw candidates/RNG primitives; `SkillTargetPolicy` owns operation-local eligibility and constraints | PROVOCATION, CAPTURE | NEW CANONICAL POLICY SEAM; DESIGN FIXED / NOT IMPLEMENTED |
| Normal Attack target arbitration | TargetResolutionSystem | TargetResolutionSystem | TAUNT/CONFUSION regression, Provocation non-domain | REUSE |
| Damage permission / actor execution right | DamageSystem / existing prevention seams | Damage domain admission/execution-right seam, using typed work category + current actor metadata | CAPTURE | EXTEND; DESIGN FIXED |
| Recovery | RecoverySystem | RecoverySystem | CAPTURE | EXTEND |
| Equipment contribution effectiveness | no canonical production owner | EquipmentEffectivenessPolicy after EquipmentProviderRef/ContributionRef resolution and generic ProviderValidityPolicy | SABOTAGE; tested FalseReport equipment scope; verified Capture equipment-attribute scope | NEW CANONICAL MINIMAL OWNER; DESIGN FIXED |
| Trigger collection | TriggerSystem | TriggerSystem querying provider/equipment policy | FALSE_REPORT, SABOTAGE, CAPTURE | EXTEND |
| RNG | BattleContext.random / RandomSystem | same | PROVOCATION, INTIMIDATION, any randomized application/selection | REUSE |
| Event facts | domain owner → EventBus | same | all 7 | REUSE |
| Composition / wiring | BattleSystems | BattleSystems | shared foundation | EXTEND WIRING |

## Owner rules

1. `StateRegistry` remains storage. It must not become the policy engine.
2. `StateLifecycleSystem` remains the sole physical state mutation owner.
3. Existing Stage11 owners are not duplicated merely because Stage12 also needs a similar question.
4. A new Stage12 owner is allowed only where the Entry Audit identifies a genuine gap.
5. Skill Permission and Provider Validity are distinct semantic questions even if the final design composes them in one small policy object.
6. Target policy must keep Normal Attack arbitration separate from skill target operations.
7. Equipment suppression means effectiveness query, not physical unequip/delete/recreate.
8. EventBus records facts and never decides permission.
9. All randomized decisions consume `BattleContext.random`, with explicit consume/no-consume tests.

## Design-open items

The following remain open after Round 4:

- DQ-SF-06 CLOSED in Round 5: SkillPermissionPolicy + pre-RNG SkillOperationAdmissionCoordinator;
- DQ-SF-07 CLOSED in Round 5: PreparationInterruptionPort + synchronous transition timing; concrete preparation owner remains an integration dependency;
- DQ-SF-09 / 10 CLOSED in Round 6: TargetOperation + explicit producer-declared query boundary + SkillTargetPolicy;
- DQ-SF-11 CLOSED in Round 7: EquipmentContributionRef + EquipmentEffectivenessPolicy + domain filter/JIT seams;
- DQ-SF-12 CLOSED in Round 9: sole RNG service + per-domain random-decision ownership + zero-RNG policy matrix + rejection/refresh/resume/replay rules;
- DQ-SF-13 CLOSED in Round 9: query/event split + domain event ownership + post-decision/commit publication + idempotence;
- DQ-SF-17 CLOSED in Round 10: BattleSystems canonical composition root, shared policy identity, strict production injection and legacy compatibility migration;
- DQ-SF-19 CLOSED in Round 8: Capture composite owner matrix + action/damage/recovery/provider/target/equipment boundaries;
- DQ-SF-21 CLOSED_BY_SHARED_FOUNDATION_DESIGN in Round 5: RecoveryOpportunitySystem Gate 4 migration contract frozen; implementation remains pending;
- DQ-SF-23 ARCHITECTURE CLOSED / CONTRACT_DEPENDENT in Round 8: per-dimension ExecutionRightSpec; Q16/Q44/Q45/B-SAB-07 remain bounded;
- DQ-SF-26 independent Shared Foundation design audit.

Admission, effectiveness, Provider validity, lifecycle transaction, clock and removal-policy owner names are no longer open architecture questions.

These remaining items are architecture decisions, not new Research questions unless a named contract boundary is explicitly reopened.

## SF-0 owner qualification — 2026-09-27

Historical Round-10 note: at that checkpoint this matrix remained DESIGN INPUT. Current owner implementation is COMPLETE and is revalidated by the final audit amendment below.
The [current capability inventory and gap ledger](STAGE12_SHARED_FOUNDATION_ARCHITECTURE_RECONNAISSANCE.md)
adds omitted owners: Stage9StateRuntime (Taunt/Insight effective read),
RecoveryOpportunitySystem (existing JIT source-skill gate), AttributeSystem and modifier-provider
seams. Stage11ApplicationPolicy is a module of conflict/ingress functions, not a general immunity class.
Shared effectiveness must migrate/delegate existing Stage9 and Stage11 readers, not duplicate them.
AR-SF-01 legacy Confusion semantics requires authority disposition first.
The [28-question ledger](STAGE12_SHARED_FOUNDATION_DESIGN_QUESTION_LEDGER.md) precedes method-level owner freeze.


## SF Round 2 owner decisions — 2026-09-27

Authority records:
- STAGE12_INSIGHT_CONFUSION_AUTHORITY_MIGRATION.md
- STAGE12_SKILLTYPE_PROVIDER_IDENTITY_DESIGN.md
- STAGE12_RUNTIME_DEFAULT_LEDGER.md

Fixed for downstream Shared Foundation design:

1. SkillDefinition owns static SkillType and PreparationMode metadata.
2. PREPARATION_ACTIVE is represented as ACTIVE + PreparationMode.REQUIRED, not as an independent SkillType.
3. NORMAL_ATTACK remains an operation owned by NormalAttackSystem and is not a SkillType.
4. Equipment specials are a separate ProviderCategory and are not coerced into SkillType.
5. SkillRuntimeRegistry owns loaded skill identity resolution and deterministic enumeration.
6. SkillProviderRef identity is (owner_id, SkillSlot, skill_id); slot 0 is fully valid.
7. EffectSourceRef remains attribution and cannot implicitly create a live Provider dependency.
8. Provider current validity remains a separate DQ-SF-08 owner; disabled/suppressed does not mean identity missing.
9. Intimidation binding will store ProviderRef rather than Python object identity.
10. RecoveryOpportunitySystem's slot-0 JIT gate and TriggerSystem's slot-0 provenance merge are both formal migration obligations. The former is Provider-validity/liveness gating; the latter is provenance identity only. Neither is repaired in this design-only round.

No gameplay implementation is authorized by these owner decisions.


## SF Round 3 owner decisions — 2026-09-27

Authority record:
- STAGE12_STATE_EFFECTIVENESS_PROVIDER_VALIDITY_DESIGN.md

Canonical owner split:

| Responsibility | Canonical owner | Non-owner collaborators |
|---|---|---|
| physical state residency | StateRegistry | policies may read only |
| physical state mutation / expiry | StateLifecycleSystem | transition coordinator observes before/after decisions |
| current state gameplay authority | StateEffectivenessPolicy | Stage9StateRuntime / Stage11StateRuntime delegate |
| Provider identity resolution | SkillRuntimeRegistry and future typed equipment resolver | ProviderValidityPolicy consumes resolved identity facts |
| current Provider validity | ProviderValidityPolicy | state policy may depend on its decision |
| dependency propagation / transition awareness | EffectivenessTransitionCoordinator | policies remain the decision owners |
| domain arbitration | existing Stage9/11/12 domain systems | consume effective/valid decisions |
| observable event publication | deciding domain owner → EventBus | coordinator may surface internal transition facts but EventBus never decides |

Owner invariants:

- StateEffectivenessPolicy and ProviderValidityPolicy remain separate because StateInstance identity and ProviderRef identity are different domains.
- EffectivenessTransitionCoordinator is deliberately not a God object. It owns neither Registry/Lifecycle nor Action/Damage/Recovery/Target/RNG.
- Shared policies never mutate `SkillRuntime.enabled` or state runtime params to represent transient suppression.
- Explicit Intimidation ProviderRef binding remains state-owned gameplay data; it is not a mutable suppression ledger.
- Equipment Provider identity can enter ProviderRef, but DQ-SF-11 still owns the equipment-effectiveness semantics and adapter.

No gameplay implementation is authorized by these owner decisions.

## SF Round 4 owner decisions — 2026-09-27

Authority record:
- STAGE12_STATE_LIFECYCLE_TRANSACTION_DESIGN.md

Canonical Round 4 split:

| Responsibility | Canonical owner | Non-owner collaborators |
|---|---|---|
| incoming state admission | StateAdmissionPolicy | source operation creates candidate first; conflict policy runs only after ALLOW |
| same-state / reapplication conflict | StateConflictPolicy | per-state contract adapters; Lifecycle does not invent generic stacking |
| application transaction preparation | StateApplicationCoordinator | pure policies, Provider selection/binding preparation, transition coordinator |
| physical create/refresh/replace/remove | StateLifecycleSystem | Registry remains storage only |
| physical state lifetime clock | StateLifecycleSystem | domain-specific helpers/counters remain separate |
| gameplay removal eligibility | StateRemovalPolicy | cleanse/source operation supplies typed RemovalOperation |
| effectiveness after commit | StateEffectivenessPolicy | EffectivenessTransitionCoordinator re-evaluates affected closure |
| Provider validity after commit | ProviderValidityPolicy | same transition closure |
| same-envelope project ordering | RD-SF-003 | Lifecycle snapshots due removals before transition recomputation |

Round 4 invariants:

- decision first, mutation second;
- a rejected admission/removal request changes nothing physical;
- REFRESH = same physical instance + new application generation;
- REPLACE = old physical instance terminates + new physical instance begins;
- resume is not refresh;
- suppression does not pause physical lifetime;
- Stage12 clock metadata must not accidentally opt into Stage10 persistence;
- ordinary cleanse policy is distinct from expiry/defeat/teardown infrastructure;
- no global source-death cleanup rule exists.

No gameplay implementation is authorized by these owner decisions.


## SF Round 5 owner closure

| Responsibility | Canonical owner | Non-owner collaborators | Frozen boundary |
|---|---|---|---|
| holder-level skill permission | SkillPermissionPolicy | StateEffectivenessPolicy supplies effective Exhaustion fact | no Provider validity, RNG, targeting or execution |
| new skill operation admission composition | SkillOperationAdmissionCoordinator | ProviderValidityPolicy + SkillPermissionPolicy | pure/pre-RNG decision seam only |
| Provider current validity | ProviderValidityPolicy | SkillRuntimeRegistry resolves identity | unchanged from Round 3 |
| preparation progress/storage | future Stage15 preparation owner | PreparationInterruptionPort exposes only interruption command | Stage12 never stores progress |
| preparation interruption transition dispatch | EffectivenessTransitionCoordinator | StateEffectivenessPolicy / ProviderValidityPolicy transition facts + PreparationInterruptionPort | synchronous, non-authoritative |
| recovery JIT source gate | RecoveryOpportunitySystem remains opportunity owner; validity delegated to ProviderValidityPolicy | typed SkillProviderRef construction | rejection before probability RNG |

Owner invariants:

- SkillPermissionPolicy and ProviderValidityPolicy remain separate truth domains.
- SkillOperationAdmissionCoordinator may aggregate blockers, but it may not invent a second permission/validity truth.
- Provider resume means only future behavior may become eligible; it never auto-activates a skill or resumes old preparation.
- EventBus records committed/decided facts and does not decide interruption.


## SF Round 6 owner closure — target operations

Authority record:
- STAGE12_TARGET_OPERATION_POLICY_DESIGN.md

| Responsibility | Canonical owner | Non-owner collaborators | Frozen boundary |
|---|---|---|---|
| declare a fresh independent Skill target query | skill/effect operation producer | SkillResolver is the current migration site | producer must explicitly declare NEW_QUERY; policy never guesses from call count |
| fresh target-operation identity | future typed TargetOperationId allocated by the battle operation-ID facility | producer owns allocation timing | value identity only; no pointer identity and no priority ordering |
| raw team/candidate primitives | TargetSystem | producer supplies operation relation/context | physical allies/enemies remain unfiltered primitives |
| operation-local target eligibility and Stage12 constraints | SkillTargetPolicy | StateEffectivenessPolicy supplies effective-state facts; TargetSystem supplies raw candidates | zero RNG; no state lifecycle, Provider validity or Normal Attack authority |
| random/deterministic target selection | existing selector / TargetSystem primitives | consumes TargetPolicyDecision | selector remains sole target-sampling RNG owner |
| Normal Attack target arbitration | TargetResolutionSystem | TargetSystem + Stage9StateRuntime | unchanged Confusion > Taunt > default > Guard domain |
| Capture friendly exclusion | SkillTargetPolicy eligibility phase | Capture effectiveness fact | verified ALLY SINGLE / CHOOSE_N only; no global targetable flag |
| Provocation forcing/inclusion | SkillTargetPolicy constraint phase | operation-local Source admissibility | enemy Skill operations only; cardinality preserved; no illegal Source forcing |

Owner invariants:

- candidate construction, eligibility, policy constraints and selector are distinct responsibilities;
- TargetSystem.allies() / enemies() keep physical membership semantics;
- SkillTargetPolicy never calls RNG and never returns a random target merely because a constraint exists;
- Confusion pre-emption is represented by domain/arbitration authority, not a numeric priority integer;
- Taunt remains Normal Attack authority and is not folded into a universal ForceTargetPolicy;
- TargetResolutionSystem is not reused as the Skill target-operation owner;
- Capture recovery denial remains RecoverySystem-owned.


## SF Round 7 owner closure — equipment effectiveness

Authority record:
- STAGE12_EQUIPMENT_EFFECTIVENESS_DESIGN.md

| Responsibility | Canonical owner | Non-owner collaborators | Frozen boundary |
|---|---|---|---|
| equipment Provider stable identity | EquipmentProviderRef / minimal contribution registry adapter | ProviderValidityPolicy consumes resolution | owner_id + stable provider_key; never pointer identity |
| concrete contribution identity | EquipmentContributionRef | domain adapter supplies contribution_key/kind | stable value identity; Equipment != Skill |
| generic equipment Provider validity | ProviderValidityPolicy | equipment baseline resolver | existing Provider validity status space |
| final concrete contribution effectiveness | EquipmentEffectivenessPolicy | ProviderValidityPolicy + StateEffectivenessPolicy + scoped rule adapters | one final truth; unsupported evidence stays explicit |
| contribution enumeration | minimal read-only EquipmentContributionRegistry/adapter | domain consumer asks only its kind | no inventory/slot/loadout mutation system |
| static attribute calculation | AttributeSystem + AttributeModifierProvider | EquipmentEffectivenessPolicy only filters | no base-stat mutation |
| equipment damage modifier order/math | DamageRuleProvider / Damage pipeline | equipment adapter filters per request | phase/order_key unchanged |
| equipment recovery modifier order/math | RecoveryModifierProvider + RecoverySystem | adapter filters before ratio | RecoverySystem retains second CEIL |
| deterministic equipment trigger execution | trigger/opportunity owner | EquipmentEffectivenessPolicy JIT gate | suppressed window skipped/no replay |
| tested scheduled due window | scheduler/trigger owner | EquipmentEffectivenessPolicy due-time gate | broader queued micro-order remains DQ-SF-23 |
| remote live-effect authority | effect/state owner | explicit EquipmentContributionDependency | Holder != Equipment Owner; attribution != dependency |
| suppression cause composition | EquipmentEffectivenessPolicy | effective SABOTAGE / scoped FALSE_REPORT / scoped CAPTURE facts | causes are a set |
| equipment RNG | existing domain RNG owner | policy/registry | Equipment policy and registry consume zero RNG |

Owner invariants:
- EquipmentEffectivenessPolicy is a policy, never an equipment god object.
- ProviderValidityPolicy and EquipmentEffectivenessPolicy are one ordered decision path, not caller-selectable truths.
- Equipment suppression is contribution ineligibility, never unequip/delete/reinstall.
- Domain owners retain calculation, ordering, CEIL, scheduling and trigger RNG.
- FalseReport/Capture bounded categories surface as unsupported rather than being generalized.
- Public transition events are governed by the Round 9 Event Model; domain owners publish post-decision/commit facts and pure queries emit none.

## SF Round 8 owner closure — Capture composite + work execution rights

Authority record:
- STAGE12_CAPTURE_COMPOSITE_EXECUTION_DESIGN.md

### Capture composite owner matrix

| Capture effect | Canonical owner | Capture supplies | Frozen boundary |
|---|---|---|---|
| Natural Action denied | ActionSystem | effective-CAPTURE rule fact | upstream of NormalAttack; no target/RNG; CAPTURE denial does not consume STUN |
| Normal Attack attempt | ActionSystem -> NormalAttackSystem boundary | none beyond Action denial | no global Capture filter in NormalAttackSystem |
| New Skill admission | existing ProviderValidity + SkillPermission composition where contract applies | provider/holder state facts only | no Capture-owned skill engine |
| PASSIVE / COMMAND Provider suppression | ProviderValidityPolicy | effective-CAPTURE suppression cause | no physical provider deletion; resume future-only |
| New actor-driven damage | Damage domain admission/execution-right seam | current-actor CAPTURE denial fact | no Weakness reuse; no universal source_id gate |
| Counter damage | CounterSystem owns admitted batch; Damage domain owns local damage permission | current counter actor CAPTURE fact | batch semantics preserved; no counter damage; public damage-denial fact follows Round 9 Damage-domain event ownership |
| Existing Active-origin DOT | existing attached/persistent effect owner + Damage domain | no Capture actor denial for admitted continuation | explicit ProviderDependency, if any, remains independently live |
| Received recovery | RecoverySystem | CAPTURE prevention cause | after modifier/second CEIL, before troop restore/capacity; target selection remains separate |
| Friendly SINGLE / CHOOSE_N eligibility | SkillTargetPolicy | CAPTURE target-ineligibility fact | ALL_ALLIES and locked/delayed remain bounded |
| Equipment attribute contribution | EquipmentEffectivenessPolicy | CAPTURE equipment suppression cause | Q63 reactive/damage remains unsupported boundary |
| Physical CAPTURE lifetime | StateLifecycleSystem | state metadata only | source death does not auto-remove |

### Shared execution-right ownership

| Responsibility | Canonical owner | Round 8 decision |
|---|---|---|
| future branch admission while battle is RUNNING | existing FutureAdmissionGate | REUSE unchanged; not a Capture/state-permission engine |
| RuleIntent execution liveness | existing ExecutionRightSystem | REUSE / future typed extension only; preserve admitted persistent work and current-only rejection invariants |
| domain operation identity | existing domain IDs and owners | REUSE; no UniversalWorkId |
| execution-right stability metadata | ExecutionRightSpec carried by owning work | NEW SHARED DESIGN VALUE / NOT A GAMEPLAY OWNER |
| ACTOR_PERMISSION final decision | Action/Damage/etc. owner that owns the operation | domain-owned |
| PROVIDER_VALIDITY final decision | ProviderValidityPolicy | existing canonical owner |
| TARGET_ELIGIBILITY final decision | SkillTargetPolicy when the work contract requests recheck | existing canonical owner; LOCKED != NEW_QUERY |
| EQUIPMENT_CONTRIBUTION final decision | EquipmentEffectivenessPolicy | existing canonical owner |
| STATE_EFFECTIVENESS final decision | StateEffectivenessPolicy | existing canonical owner |
| public event publication | deciding domain owner -> EventBus | Round 9 event governance CLOSED; query != event and publication follows the canonical decision/commit |

Owner invariants:

- Capture never becomes a central executor.
- ExecutionRightSpec is metadata, not a universal is_valid boolean and not an RNG consumer.
- Per-dimension modes can differ on the same work item.
- UNSUPPORTED_BOUNDARY must surface rather than silently ALLOW/DENY.
- A JIT failure skips the current execution only; no automatic requeue/replay.
- Current actor, origin Provider, historical source, effect holder, damage source and damage target are distinct roles.


## SF Round 9 owner closure — RNG / Event / Runtime Default governance

Authority record:
- STAGE12_RNG_EVENT_DEFAULT_GOVERNANCE.md

### RNG service and decision ownership

| Responsibility | Canonical owner | Non-owner collaborators | Frozen Round 9 boundary |
|---|---|---|---|
| PRNG service | BattleContext.random / RandomSystem | every randomized domain consumer | sole random service; no direct random module use by gameplay owners |
| source state/effect proc | originating source/effect-generation owner | StateAdmissionPolicy consumes only the resulting candidate | source proc draw, if any, occurs before Insight admission |
| state admission / effectiveness / conflict | StateAdmissionPolicy / StateEffectivenessPolicy / StateConflictPolicy | application coordinator | zero RNG |
| skill Provider validity | ProviderValidityPolicy | SkillOperationAdmissionCoordinator | zero RNG; non-VALID rejects before activation RNG |
| holder Skill permission | SkillPermissionPolicy | SkillOperationAdmissionCoordinator | zero RNG; denial rejects before activation RNG |
| Skill activation probability | Skill activation owner / SkillResolver-equivalent | admission coordinator authorizes attempt | draw only after final admission ALLOW |
| target policy | SkillTargetPolicy | TargetSystem provides candidates | zero RNG |
| target sampling | TargetSystem / selector | consumes TargetPolicyDecision | sole target-sampling RNG owner |
| Intimidation binding | mechanism-specific binding selector | StateApplicationCoordinator carries prepared binding transaction | random selection only after admitted initial/refresh path; coordinator itself remains zero-RNG except explicit delegated selection result |
| RecoveryOpportunity probability | RecoveryOpportunitySystem | ProviderValidityPolicy JIT gate | Provider validity before recovery probability RNG |
| equipment trigger RNG | trigger/opportunity owner | EquipmentEffectivenessPolicy JIT gate | contribution validity before downstream trigger RNG |
| execution-right evaluation | owning domain + ExecutionRightSpec | canonical policy owners per dimension | evaluation zero RNG; DENY skips downstream work RNG |
| replay trace | test instrumentation around RandomSystem seam | domain tests | assert owner/path/API decision order; no new production RNG owner |

### Zero-RNG owner set

These owners never consume RNG as a consequence of being queried:

- StateAdmissionPolicy
- StateEffectivenessPolicy
- StateConflictPolicy
- ProviderValidityPolicy
- SkillPermissionPolicy
- SkillOperationAdmissionCoordinator
- SkillTargetPolicy
- EquipmentEffectivenessPolicy
- StateRemovalPolicy
- EffectivenessTransitionCoordinator
- ExecutionRightSpec evaluation

StateApplicationCoordinator remains transaction preparation/orchestration, not a hidden RNG policy.
The only Intimidation randomness is an explicit binding-selection operation authorized by an admitted initial/refresh path.

### Event ownership matrix

| Observable fact | Canonical deciding/publishing owner | Policy/helper role | Round 9 design |
|---|---|---|---|
| STATE_APPLIED / STATE_REFRESHED / STATE_REMOVED / STATE_EXPIRED | StateLifecycleSystem after physical commit | policies decide eligibility/conflict only | reuse current event ownership |
| state application rejection | final state application orchestrator | admission/conflict policy supplies typed reason | future STATE_APPLICATION_REJECTED with ADMISSION/CONFLICT discriminator |
| state becomes suppressed/resumed | committed dependency/effectiveness transition path | StateEffectivenessPolicy supplies truth; coordinator detects transition | future STATE_SUPPRESSED / STATE_RESUMED only for contract-observable transitions |
| Provider validity changed | internal EffectivenessTransitionCoordinator fact | ProviderValidityPolicy supplies truth | internal by default; no generic public Provider event required |
| blocked Skill attempt | Skill operation admission/execution owner | Provider/permission policies supply blockers | future SKILL_OPERATION_BLOCKED only for an actual attempt |
| preparation interrupted | true preparation owner after successful interruption | PreparationInterruptionPort is boundary | future PREPARATION_INTERRUPTED; NOT_PREPARING emits none |
| natural action blocked | ActionSystem | Capture/STUN facts consumed by Action owner | reuse ACTION_BLOCKED; state handler never duplicates it |
| damage denied | Damage domain | Capture execution-right fact consumed by Damage owner | reuse DAMAGE_PREVENTED; distinct from Weakness legal-zero |
| recovery prevented | RecoverySystem | internal prevention cause set may include HealingBlock/Capture | one RECOVERY_PREVENTED public fact; compatibility primary reason |
| target constraint evaluated | none | SkillTargetPolicy pure query | no event |
| actual target-set change, if future report surface requires it | target-operation resolution owner | policy supplies constraint | not required as a new EventType in Round 9 |
| EventBus dispatch/history | EventBus | receives already-decided fact | never permission/ordering authority |

### Event ordering invariants

- query != event;
- successful mutation publishes after canonical commit;
- dependency recomputation and internal transition dispatch precede public transition facts;
- rejected/failed transactions never emit committed-state events;
- repeated query emits nothing;
- same effective/valid state with no transition emits nothing;
- EventBus listeners do not decide gameplay.

### Default ownership

Runtime Default authority stays in STAGE12_RUNTIME_DEFAULT_LEDGER.md.

Battle-owned defaults remain RD-SF-001 / RD-SF-002 / RD-SF-003.
Research-owned PD-INS-001 / PD-INS-002 remain inherited approved project defaults with their original provenance.
Round 9 adds no new default and creates no new gameplay owner.

Owner invariants after Round 9:

- RandomSystem is the sole RNG service, but it is not a gameplay-decision owner.
- Policy queries are deterministic and side-effect free with respect to RNG and EventBus.
- EventBus is the sole event dispatch/history service, but it is not a gameplay-decision owner.
- Domain systems publish only facts they canonically own.
- PROJECT_RUNTIME_DEFAULT is governance metadata, not a substitute policy engine.


## SF Round 10 owner closure — construction / injection / rights

Authority: STAGE12_SHARED_FOUNDATION_COMPOSITION_AND_TEST_ARCHITECTURE.md

| Responsibility | Canonical owner | Constructed / owned by | Main consumers | Mutation rights | RNG rights | Event rights |
|---|---|---|---|---|---|---|
| state storage | StateRegistry | BattleContext.states | Lifecycle + read-only policies through context | storage only through authorized Lifecycle seams | NONE | NONE |
| skill identity storage | SkillRuntimeRegistry | BattleContext.skill_runtimes | ProviderValidityPolicy / RecoveryOpportunitySystem | registry loading only | NONE | NONE |
| RNG service | RandomSystem | BattleContext.random | domain random decision owners | RNG state only | SOLE SERVICE | NONE |
| event bus | EventBus | BattleContext.event_bus | committed domain publishers | event history/subscriptions only | NONE | facts only; never permission |
| state physical mutation / clock | StateLifecycleSystem | BattleSystems | application/removal/lifecycle orchestration | SOLE STATE WRITER | NONE | committed lifecycle facts |
| dependency session | DependencyEvaluationSupport | BattleSystems | StateEffectivenessPolicy + ProviderValidityPolicy + transition coordinator | memo/visiting/reverse-index only | NONE | NONE |
| state current authority | StateEffectivenessPolicy | BattleSystems | Stage9/11 + dependent policies/adapters | NONE | NONE | NONE on query |
| Provider validity | ProviderValidityPolicy | BattleSystems | Skill admission, Recovery Gate 4, dependent triggers/effects | NONE | NONE | NONE on query |
| state admission | StateAdmissionPolicy | BattleSystems | StateApplicationCoordinator | NONE | NONE | rejection only after final decision |
| state conflict/reapply | StateConflictPolicy | BattleSystems | StateApplicationCoordinator | NONE | NONE | NONE on query |
| state removal eligibility | StateRemovalPolicy | BattleSystems | removal orchestration | NONE | NONE | NONE on query |
| equipment contribution identity | EquipmentContributionRegistry / adapter | BattleSystems | ProviderValidityPolicy + EquipmentEffectivenessPolicy | no inventory mutation | NONE | NONE |
| equipment current contribution authority | EquipmentEffectivenessPolicy | BattleSystems | Attribute/Damage/Recovery/Trigger/live-effect adapters | NONE | NONE | NONE on query |
| holder skill permission | SkillPermissionPolicy | BattleSystems | SkillOperationAdmissionCoordinator | NONE | NONE | domain block fact after denial |
| Skill target policy | SkillTargetPolicy | BattleSystems | SkillResolver target-operation path | NONE | NONE | post-resolution domain fact only |
| application orchestration | StateApplicationCoordinator | BattleSystems | state application callers | prepares only; Lifecycle commits | NONE | post-commit coordination |
| effectiveness propagation | EffectivenessTransitionCoordinator | BattleSystems | application/removal/lifecycle orchestration | NONE | NONE | typed transition facts only after commit |
| Skill admission composition | SkillOperationAdmissionCoordinator | BattleSystems | SkillResolver | NONE | NONE before admission | domain-owned admission fact |
| preparation interruption | PreparationInterruptionPort | BattleSystems | EffectivenessTransitionCoordinator | concrete Stage15 owner later | NONE | no EventBus authority |
| natural action | ActionSystem | BattleSystems | BattleEngine | action-domain state only | existing domain draws | ACTION_BLOCKED |
| damage | Damage stack | BattleSystems | Effects / NormalAttack / reactions | damage settlement only | existing domain draws | DAMAGE facts |
| recovery | RecoverySystem | BattleSystems | recovery opportunity / effects | troop restore through TroopSystem | NONE | RECOVERY facts |
| recovery opportunity | RecoveryOpportunitySystem | BattleSystems | aftermath / hooks | opportunity execution | Gate 5 draw | governed domain facts |
| trigger collection | TriggerSystem | BattleSystems | hooks / aftermath | collects intents only | explicit trigger-owned draws only | no permission authority |

Production invariant: one StateEffectivenessPolicy, one ProviderValidityPolicy, one SkillPermissionPolicy, one SkillTargetPolicy and one EquipmentEffectivenessPolicy per BattleSystems graph. Isolated tests may build a complete fixture graph, but production consumers may not self-create these owners.

DQ-SF-17 = CLOSED_BY_SHARED_FOUNDATION_DESIGN. DQ-SF-26 remains pending.

## STAGE12_FINAL_AUDIT_CANDIDATE_OWNER_MATRIX — 2026-09-28

Final static audit confirms one production definition for each canonical Shared Foundation owner and one BattleSystems composition root registering all seven integrations. No shadow StateEffectivenessPolicy, ProviderValidityPolicy, SkillTargetPolicy, EquipmentEffectivenessPolicy, recovery owner, lifecycle writer, or local RNG owner was found.
