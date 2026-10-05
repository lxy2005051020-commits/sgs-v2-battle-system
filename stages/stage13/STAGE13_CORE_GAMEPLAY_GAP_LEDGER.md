# Stage13 Core Gameplay Gap Ledger

> Status: CURRENT GAP LEDGER / Stage13-A inventory preserved + foundational research amendment
>
> Source inventory: STAGE13_CORE_GAMEPLAY_MECHANISM_INVENTORY.md
>
> This ledger records implementation-required core gaps. It does not authorize gameplay implementation.

## 1. Gate summary

~~~text
Inventory rows                                  48
Inventory-derived implementation gap families   18
Post-inventory foundational research families    3
  - wounded-troop / recoverable capacity
  - damage increase / reduction mechanics
  - recovery / treatment formula mechanics
Residual known state research family             0
  - 690221 ACTIVE_SKILL and DOT/DELAYED applicability CLOSED
Runtime-governance workstreams                    5
Stage1-12 wholesale reopen required               0
Skill Runtime implementation started              NO
~~~

The two 690221 inventory rows remain one focused residual-state research family with two discriminating lanes: ACTIVE_SKILL and DOT / DELAYED. A post-inventory route review additionally opened three foundational empirical families because the original inventory treated runnable settlement behavior too generously as evidence of formula-level closure.

## 2. Gap ledger

| Gap ID | Inventory | Gap | Current State | Gap Type | Blocking | Dependencies | Required Closure |
|---|---|---|---|---|:---:|---|---|
| G13-001 | CGM-001/002 | Core timing / gameplay opportunity breadth | BattlePhase, RuleHookSystem, TriggerSystem, DamageAftermathSystem, PendingWorkTimingPoint | CLOSED_BY_EXISTING_OWNER | NO | existing engine/finalization barriers | CLOSED: canonical timing checkpoints established; future skill hooks extend typed seams |
| G13-002 | CGM-009 | Reusable target selector vocabulary | TargetSystem, TargetOperation, SkillTargetPolicy, SkillResolver | CLOSED_BY_EXISTING_OWNER | NO | TargetOperation, AttributeSystem | CLOSED: random/deterministic/fixed/explicit operable; concrete ranking belongs to skill contracts |
| G13-003 | CGM-011 | Damage family extension seam | DamageInstanceCoordinator, DamageResolutionSystem, SourceType | CLOSED_FOR_EXIT | NO | OperationLineage, ExecutionRight | CLOSED: typed SourceType routes through unified coordinator; no second damage pipeline |
| G13-004 | CGM-016 | Recovery opportunity extensibility | RecoveryOpportunitySystem, RecoverySystem, TreatmentFormulaSystem | CLOSED_BY_EXISTING_OWNER | NO | opportunity model, RecoverySystem | CLOSED: typed opportunity admission and settlement unified; special recovery uses dedicated lane |
| G13-005 | CGM-018/019 | Attribute source + modifier model | AttributeSystem, AttributeModifierProvider, EquipmentContributionRegistry | CLOSED_BY_EXISTING_OWNER | NO | Provider/Equipment effectiveness | CLOSED: single canonical reader with explicit provider hooks and equipment contributions |
| G13-006 | CGM-020 | Attribute read-mode policy | PendingWorkReadPolicy, RecoveryPotencyContext, DamageSystem | CLOSED_BY_EXISTING_IMPLEMENTATION | NO | operation identity, attribute model | CLOSED: snapshot at creation/application vs live read at execution supported and audited |
| G13-007 | CGM-022 | RNG decision trace / replay topology governance | RandomSystem, BattleContext.random | CLOSED_BY_EXISTING_IMPLEMENTATION | NO | RandomSystem, operation identity | CLOSED: sole PRNG owner; 0 external random; zero-draw fast paths verified |
| G13-008 | CGM-023 | Missing core Effect primitives | EffectExecutor, DamageEffect, ApplyStateEffect, RemoveStateEffect, RecoverEffect | CLOSED_BY_EXISTING_OWNER | NO | attribute model, execution right | CLOSED: EffectExecutor routes typed Effect subclasses; new effects extend as skills require |
| G13-009 | CGM-024 | Multi-effect composition semantics | SkillDefinition.effect_specs, SkillResolver, EffectExecutor | EXPLICIT_FUTURE_BOUNDARY | NO | Effect model, operation identity | CLOSED: ordered execution with fail-closed exception; rollback/atomic groups deferred to skill contract |
| G13-010 | CGM-025 | Delayed / repeated / scheduled work | PendingWork unique owner; one-shot schedules; REPEAT_N_TIMES RESERVED | CLOSED_BY_EXISTING_IMPLEMENTATION | NO | timing/opportunity, work identity, lifetime | CLOSED: D1 foundation frozen; ONE_SHOT/UNTIL_EXECUTED/UNTIL_ROUND audited; repeat reserved |
| G13-011 | CGM-026 | Cross-domain modifier shell | DamageModifierSystem, TreatmentFormulaSystem, AttributeSystem | CLOSED_BY_EXISTING_OWNER | NO | attribute/effect/lifetime | CLOSED: domain-separated math avoids God Object; no universal shell required |
| G13-012 | CGM-028 | Generic non-state lifetime | WorkLifetimeSpec, StateLifetimeSpec | CLOSED_BY_EXISTING_IMPLEMENTATION | NO | work identity | CLOSED: WorkLifetimeSpec and StateLifetimeSpec handle all discrete clock lifetimes |
| G13-013 | CGM-029 | Usage / charge / frequency | future Skill Contract / ActionProgressTracker | NON_BLOCKING_FUTURE_SKILL_CAPABILITY | NO | work identity, lifetime | CLOSED: no frozen Stage 1-13 core dependency; governed per concrete Stage14+ skill contract |
| G13-014 | CGM-031/033 | Pending-work validity under defeat / provider / target change | PendingWorkValidityPolicy, ExecutionRightSupport, DefeatCleanupPort | CLOSED_BY_EXISTING_IMPLEMENTATION | NO | ExecutionRight, DefeatCleanupPort, ProviderValidity | CLOSED: source/target/provider validity modes implemented and audited in D1 |
| G13-015 | CGM-035 | Generic operation/work lineage | OperationIdAllocator, OperationLineage | CLOSED_BY_EXISTING_IMPLEMENTATION | NO | OperationIdAllocator | CLOSED: monotonic non-orderable IDs across all work types; parent lineage preserved |
| G13-016 | CGM-036 | ExecutionRight coverage for new core work | ExecutionRightSystem, ExecutionRightSupport | CLOSED_BY_EXISTING_IMPLEMENTATION | NO | G13-015, attribute model | CLOSED: admission snapshot vs live execution recheck fully supported and tested |
| G13-017 | CGM-038 | Generic cleanse/dispel/category removal | StateRemovalPolicy, StateRemovalCoordinator, RemovalOperation | EXPLICIT_UNSUPPORTED_BOUNDARY | NO | StateRemovalPolicy, actual state taxonomy | CLOSED: exact removal strong; broad cleanse unsupported until official state taxonomy |
| G13-018 | CGM-043 | Whole-battle deterministic replay audit | test_stage13_whole_battle_replay_audit.py, RandomSystem | CLOSED_BY_EXISTING_IMPLEMENTATION | NO | G13-007, all other core work | CLOSED: Case A 25/25 runs identical, Case B seed divergence, Case C zero-RNG fast paths PASS |
| G13-019 | CGM-045/046 | 690221 See-Through active / DOT family applicability | ACTIVE_SKILL and DOT/DELAYED authorized and integrated; merged-main residual runtime audit PASS | IMPLEMENTED_AUDITED | NO | 690221 mechanism contract; Stage13 residual runtime integration | CLOSED |
| G13-020 | Post-inventory foundation audit | Wounded-troop / recoverable-capacity mechanics | B1 research FROZEN; explicit wounded pool integrated and audited | IMPLEMENTED_AUDITED | NO | damage settlement, RecoverySystem, TroopSystem | CLOSED for current integrated slice |
| G13-021 | Post-inventory foundation audit | Damage increase / reduction aggregation mathematics | B2/B2.5 closed slice integrated and audited: same-side algebraic pools, cross-side multiplication, -90% floor, independent advancement multipliers | IMPLEMENTED_AUDITED | NO | DamageModifierSystem, critical families, morale/troop-restraint layers | CLOSED for current integrated slice |
| G13-022 | Post-inventory foundation audit | General recovery / treatment formula mechanics | ordinary treatment core integrated and merged-main audited: Rate(F(N)+Attr), coefficient 1, same-side algebraic pools, cross-side multiplication, independent red pool, CEIL, application-time persistent snapshot | IMPLEMENTED_AUDITED | NO | G13-020, RecoverySystem, FirstAid/Recuperation authorities | CLOSED for ordinary-treatment core; special recovery families remain separately bounded |

## 3. Non-gaps that must not be reopened

The following are mature enough to be reused as frozen substrate:

- EventBus fact ownership;
- primary action tier/speed/tie/snapshot;
- natural action permission;
- normal attack orchestration;
- TargetOperation identity/query modes;
- DamageRequest / DamageInstance / settlement identity;
- current damage modifier pipeline;
- Share / Distribution partition runtime;
- damage aftermath commitment;
- RecoverySystem settlement;
- Stage11 attacker recovery;
- sole RandomSystem service;
- StateLifetime / StateLifecycle;
- State/Provider dependency graph;
- holder defeat cleanup;
- Unit/Team facts;
- exact state removal;
- equipment effectiveness;
- provider validity / skill permission metadata;
- minimal preparation interoperability;
- battle finalization.

A later architecture may extend these owners. It may not silently replace them.

## 4. Explicit preserved debt / unsupported boundaries

### 690086 Distribution

~~~text
DSTS9-B02 = CLOSED
Commander participant death = continue current DistributionTransaction
Remaining participants       = continue
Original target Dtarget      = continue
Battle finalization          = after DistributionTransaction completes
Research Debt                = NO
Runtime Authority             = FROZEN_P0
~~~

The historical absence of a lethal commander-participant corpus sample remains provenance only; it is no longer an open mechanism boundary.

### Stage12 bounded micro-slices

The existing Runtime Default Ledger keeps Provocation, Capture, FalseReport and Sabotage bounded slices explicit. They remain unsupported unless a concrete Stage13 core primitive requires them. A generic primitive is not permission to guess a state-specific rule.

## 5. Dependency order

The research-first route amendment supersedes the original direct BATCH A-F execution order.

~~~text
RESEARCH GATE B1
  G13-020 wounded-troop / recoverable-capacity mechanics

RESEARCH GATE B2
  G13-021 damage increase / reduction mechanics

RESEARCH GATE B3
  G13-022 recovery / treatment formula mechanics

STAGE13-C
  G13-019 690221 applicability — CLOSED
  690086 DSTS9-B02 — CLOSED
  690099 6% threshold/equality boundary — CLOSED
  audit only remaining exact unresolved micro-clauses

STAGE13-D — consolidated planning / governance
  G13-007 RNG trace governance
  G13-015 operation/work lineage
  G13-005 attribute source/modifier model
  G13-006 attribute snapshot/JIT policy
  G13-002 selector vocabulary
  G13-001 timing/opportunity breadth
  G13-004 recovery opportunity extensibility
  G13-008 core Effect primitives
  G13-009 multi-effect composition
  G13-011 modifier shell
  G13-012 generic lifetime
  G13-013 usage/frequency
  G13-010 delayed/repeated work
  G13-016 ExecutionRight extension
  G13-014 pending-work validity
  G13-017 category removal
  G13-003 damage extension seam
  G13-018 replay plan

STAGE13-E/F/G
  architecture
  implementation
  deterministic replay / independent completion audit
~~~

B1 is first because B3 recovery interpretation depends on knowing what capacity is actually recoverable. B2 is independent enough to prepare in parallel, but all three foundational research gates must close before Stage13-C is declared complete.

## 6. Stage13-D planning requirement

Stage13-D must produce a closure plan for every gap with:

- exact authority source;
- owner to reuse/extend;
- whether a Runtime Default is required;
- whether focused empirical research is required;
- discriminating tests;
- dependency predecessor;
- freeze/audit artifact.

No row may move directly from this ledger to implementation merely because its desired API seems obvious.

## Stage13-D1 closure boundary — 2026-10-04

D1 PendingWork foundation is FROZEN / MAIN CI PASS; latest-main publication
gate is recorded in STAGE13_D1_PENDING_WORK_FREEZE_AUDIT.md. G13-010/012/014/015/016
now have a concrete one-shot reusable foundation. Broad ledger blocking flags remain
conservative for the Stage13 exit audit rather than implying all lifetime/modifier/operation
consumers are implemented. REPEAT_N_TIMES is a typed reserved seam with an explicit
NotImplementedError, not a hidden implemented capability.

| Remaining workstream | Existing gap coverage | Deferred boundary |
|---|---|---|
| D2 | G13-013 | UsageBudget/frequency/cooldown/charge; no new counters in D1 |
| D3 | G13-009 and composition-related Effect/target/opportunity consumers | ordered multi-effect semantics; no concrete skills |
| D4 | G13-005/006/011 and associated domain extension consumers | attribute snapshot/JIT and modifier provenance; D1 only carries declared data |
| D5 | G13-007 | RNG trace/replay topology; RandomSystem remains sole PRNG |
| G | G13-018 and final inventory reconciliation | whole-battle deterministic replay/engine exit audit |

No Stage1-12 mechanism or B1/B2/B2.5/B3/residual formula has been reopened.
