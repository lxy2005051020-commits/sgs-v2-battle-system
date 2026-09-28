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
Residual known state research family             1
  - 690221 family applicability
Runtime-governance workstreams                    5
Stage1-12 wholesale reopen required               0
Skill Runtime implementation started              NO
~~~

The two 690221 inventory rows remain one focused residual-state research family with two discriminating lanes: ACTIVE_SKILL and DOT / DELAYED. A post-inventory route review additionally opened three foundational empirical families because the original inventory treated runnable settlement behavior too generously as evidence of formula-level closure.

## 2. Gap ledger

| Gap ID | Inventory | Gap | Current State | Gap Type | Blocking | Dependencies | Required Closure |
|---|---|---|---|---|:---:|---|---|
| G13-001 | CGM-001/002 | Core timing / gameplay opportunity breadth | coarse BattlePhase + two RuleHook types + specialized aftermath path | PARTIAL | YES | existing engine/finalization barriers | typed opportunity model + architecture audit + tests |
| G13-002 | CGM-009 | Reusable target selector vocabulary | relation/cardinality/query identity strong; selector semantics only random / input-order deterministic / explicit | PARTIAL | YES | TargetOperation, AttributeSystem | typed ranking selectors or explicit unsupported contracts; no concrete-skill selectors |
| G13-003 | CGM-011 | Damage family extension seam | strong DamageInstance core; finite source/work classification | PARTIAL | YES | OperationLineage, ExecutionRight | typed extension seam preserving existing family guards |
| G13-004 | CGM-016 | Recovery opportunity extensibility | only FirstAid and Recuperation are canonical opportunities | PARTIAL | YES | opportunity model, RecoverySystem | generic opportunity descriptor/admission path without moving settlement ownership |
| G13-005 | CGM-018/019 | Attribute source + modifier model | four live battle attributes, opaque state modifier provider, additive equipment seam | PARTIAL | YES | Provider/Equipment effectiveness | typed attribute key/contribution/provenance/stacking architecture |
| G13-006 | CGM-020 | Attribute read-mode policy | no generic per-work snapshot/JIT attribute read descriptor | MISSING | YES | operation identity, attribute model | snapshot/JIT primitive + tests; mode chosen by authority at consumer level |
| G13-007 | CGM-022 | RNG decision trace / replay topology governance | sole PRNG exists, current-domain zero/draw contracts exist | RUNTIME_GOVERNANCE_REQUIRED | YES | RandomSystem, operation identity | formal API-level draw-operation trace/default policy; no new PRNG owner |
| G13-008 | CGM-023 | Missing core Effect primitives | executor supports Damage/ApplyState/RemoveState/Recover only | PARTIAL | YES | attribute model, execution right | minimal new core effects required by generic engine, beginning with typed attribute modification if selected by design |
| G13-009 | CGM-024 | Multi-effect composition semantics | local ordered tuples/batches exist; no generic operation sequence failure/abort contract | PARTIAL | YES | Effect model, operation identity | ordered composition contract + abort/continue/atomic group semantics |
| G13-010 | CGM-025 | Delayed / repeated / scheduled work | periodic and Sabotage paths are mechanism-specific | MISSING | YES | timing/opportunity, work identity, lifetime | minimal PendingWork owner; typed scheduling and execution-right carry |
| G13-011 | CGM-026 | Cross-domain modifier shell | damage/recovery/attribute owners are separate but metadata/lifetime shell is not reusable | PARTIAL | YES | attribute/effect/lifetime | typed provenance/scope/lifetime shell; math remains domain-owned |
| G13-012 | CGM-028 | Generic non-state lifetime | StateLifetime cannot own arbitrary effects/modifiers/pending work | MISSING | YES | work identity | reusable lifetime spec for core work with explicit clock domain |
| G13-013 | CGM-029 | Usage / charge / frequency | only narrow mechanism-local counters exist | MISSING | YES | work identity, lifetime | canonical budget/frequency primitive or equivalent typed owner |
| G13-014 | CGM-031/033 | Pending-work validity under defeat / provider / target change | specialized grants and source-dependent states exist; no generic work contract | PARTIAL | YES | ExecutionRight, DefeatCleanupPort, ProviderValidity | work-level continuation/cancellation policy modes; preserve mechanism-specific rules |
| G13-015 | CGM-035 | Generic operation/work lineage | many typed IDs exist but no generic skill/effect/recovery work identity | PARTIAL | YES | OperationIdAllocator | minimal stable IDs/lineage, not a universal UUID abstraction |
| G13-016 | CGM-036 | ExecutionRight coverage for new core work | actor/provider/target/equipment/state dimensions exist | PARTIAL | YES | G13-015, attribute model | extend only dimensions demanded by delayed/composite work |
| G13-017 | CGM-038 | Generic cleanse/dispel/category removal | exact removal strong; category semantics are bounded/adapters only | PARTIAL | YES | StateRemovalPolicy, actual state taxonomy | typed category-removal query after authority review; never infer from UI labels |
| G13-018 | CGM-043 | Whole-battle deterministic replay audit | seeded RNG and golden traces exist but no Stage13 replay gate | PARTIAL | YES | G13-007, all other core work | trace schema + repeated same-input/same-seed audit across operations/RNG/targets/damage/recovery/states/result |
| G13-019 | CGM-045/046 | 690221 See-Through active / DOT family applicability | explicit UNSUPPORTED_UNKNOWN | RESEARCH_REQUIRED | YES | existing 690221 authority | focused evidence campaign + amendment/freeze audit OR explicit Stage13 non-blocking unsupported-boundary verdict |
| G13-020 | Post-inventory foundation audit | Wounded-troop / recoverable-capacity mechanics | Runtime clamps recovery to missing troops; independent wounded-pool truth is not empirically established | RESEARCH_REQUIRED | YES | damage settlement, RecoverySystem, TroopSystem | focused battle-report research establishing equivalence, independent pool, family-specific rule, or explicit unobservable boundary |
| G13-021 | Post-inventory foundation audit | Damage increase / reduction aggregation mathematics | typed modifier phases exist, but universal stacking/order/cap/rounding semantics are not fully empirically frozen | RESEARCH_REQUIRED | YES | DamageModifierSystem, critical families, morale/troop-restraint layers | controlled multi-modifier research + quantitative model discrimination + foundation freeze |
| G13-022 | Post-inventory foundation audit | General recovery / treatment formula mechanics | trigger/lifecycle are mature, while treatment-rate/attribute conversion remains FORMULA_RESEARCH_OUT_OF_SCOPE in key contracts | RESEARCH_REQUIRED | YES | G13-020, RecoverySystem, FirstAid/Recuperation authorities | formula-family research + modifier/rounding/snapshot discrimination + foundation freeze |

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
DSTS9-B02 = OPEN / UNOBSERVED
Runtime      = FROZEN TO CONTRACT by explicit project default
Research     = NOT FROZEN
Strict       = INCOMPLETE
~~~

Stage13 infrastructure may touch the same shared owners but must not convert this debt into empirical closure.

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
  G13-019 690221 focused research
  audit 690086 / 690099 / all other residual state debt
  reopen only exact unresolved clauses

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
