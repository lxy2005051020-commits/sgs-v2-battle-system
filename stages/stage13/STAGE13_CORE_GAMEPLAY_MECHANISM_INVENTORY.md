# Stage13 Core Gameplay Mechanism Inventory Audit

> Audit: STAGE13_CORE_GAMEPLAY_MECHANISM_INVENTORY_AUDIT
>
> Date: 2026-09-28
>
> Battle baseline: 5ebe6d121d5bc55351b5e907bacf168ec38ce1b7
>
> Research baseline: 12cc30505f3ae8b1f823fb9d0dde0e4fe70704c3
>
> Scope: inventory / classification / governance only. No new gameplay implementation.

## 1. Verdict

~~~text
Repository Lock                         PASS
Stage12 Frozen Baseline                 VERIFIED
Stage13 Replan Authority                VERIFIED
Current Production Architecture Scan   COMPLETE
Gameplay Owner Inventory                COMPLETE
Core Mechanism Domain Inventory         COMPLETE
Test Coverage Inventory                 COMPLETE
Research Authority Inventory            COMPLETE
Known Gaps Classified                   COMPLETE
Research / Runtime Governance Split     COMPLETE
Stage12 Hidden Reopen                   NONE
Skill-System Leakage                    NONE
Dependency Order                        KNOWN

STAGE13_ENTRY_GATE                      PASS
Stage13 Readiness                       READY
Stage13 Active                          YES

CORE_GAMEPLAY_MECHANISM_INVENTORY       COMPLETE
CORE_GAMEPLAY_ENGINE                    NOT YET FROZEN
Skill Runtime Readiness                 NOT YET READY
~~~

Entry Gate PASS activates Stage13 work. It does not close any gap, freeze the architecture, or authorize Skill Runtime implementation.

## 2. Frozen baseline

The audit preserves the following Stage12 exit state:

~~~text
Stage11 Runtime                         FROZEN
Stage12 Research                        7 / 7 FROZEN
Stage12 Gameplay                        7 / 7
Stage12 Runtime Frozen To Contract      7 / 7
STAGE12_RUNTIME_FREEZE                  PASS
FINAL_40_STATE_RUNTIME_AUDIT            PASS
GOVERNANCE_SYNC                         PASS
Stage12 Runtime                         FROZEN
Stage12 Complete                        YES

Official States                         40
Runtime FROZEN TO CONTRACT              40 / 40
Research FROZEN                         39 / 40
Strict Complete                         39 / 40

690086 DISTRIBUTION / DSTS9-B02         OPEN / UNOBSERVED
~~~

The latest recorded merged-main validation before the Stage13 replan is 1667 passed / demo PASS. The Stage13 replan commit is documentation-only and does not alter gameplay.

## 3. Inventory method

Production owners, public contracts, tests and research authorities were inspected from the two locked repository heads. Candidate domains from the Stage13 replan were treated as inventory seeds, not presumed gaps.

Classification is exactly one of:

- ALREADY_IMPLEMENTED
- PARTIAL
- MISSING
- RESEARCH_REQUIRED
- RUNTIME_GOVERNANCE_REQUIRED
- UNSUPPORTED
- NOT_NEEDED

A mechanism is ALREADY_IMPLEMENTED only when a production owner, observable semantics, canonical architecture, tests, and a legal future consumption path all exist.

## 4. Canonical mechanism inventory

| ID | Mechanism | Domain | Current Owner | Production / Test Evidence | Authority | Classification | Skill Blocking | Required Next Action |
|---|---|---|---|---|---|---|---|---|
| CGM-001 | Battle phase backbone | Timing | BattleEngine / BattlePhase | PRE_BATTLE, ROUND_START, ACTION_ORDER, UNIT_ACTION_START, UNIT_ACTION, UNIT_ACTION_END, ROUND_END, BATTLE_END; Stage7/9 engine tests | Stage1-10 frozen runtime | PARTIAL | YES | Define typed core timing/opportunity surface without turning EventBus into authority |
| CGM-002 | Gameplay hook / opportunity surface | Trigger | RuleHookSystem / TriggerSystem | Formal RuleHook only RoundStartHook and UnitActionStartHook; damage aftermath recovery uses a separate port | Stage7/10 frozen runtime | PARTIAL | YES | Generalize typed opportunities for core committed facts required by future Skill Runtime |
| CGM-003 | Public committed fact stream | Event | EventBus / EventType | Explicit fact-only contract; zero-subscriber combat tests | Stage9 architecture audit | ALREADY_IMPLEMENTED | NO | Preserve facts-only boundary |
| CGM-004 | Primary action ordering | Action order | ActionOrderSystem | priority tier + final speed + attacker/defender + lineup tie; no shuffle RNG; round snapshot | 690090 / 690091 frozen contracts + Stage11 Amendment 001 | ALREADY_IMPLEMENTED | NO | Regression only |
| CGM-005 | Action progress and holder action-start clock | Action | ActionProgressTracker / StateLifecycleSystem | acted/action-start tracking and holder-action lifetime settlement | Stage10/11 frozen runtime | ALREADY_IMPLEMENTED | NO | Regression only |
| CGM-006 | Natural action permission | Action | ActionSystem + CurrentActorPermissionPolicy | typed allow/deny/unsupported path before natural action | Stage11/12 runtime | ALREADY_IMPLEMENTED | NO | Regression only |
| CGM-007 | Normal attack orchestration | Normal attack | NormalAttackSystem | canonical target resolution, target lock, damage-instance routing, combo integration | Stage9 frozen runtime | ALREADY_IMPLEMENTED | NO | Regression only |
| CGM-008 | Target operation identity / query freshness | Target | TargetOperation / TargetOperationProducer | NEW_QUERY, INHERIT_RESOLVED, DERIVE_FROM_RESOLVED, LOCK_RESOLVED; typed provenance | Stage12 Shared Foundation | ALREADY_IMPLEMENTED | NO | Reuse as Skill Runtime substrate |
| CGM-009 | Generic target selector vocabulary | Target | TargetSystem + SkillResolver | random, deterministic-by-candidate-order, explicit; SINGLE / CHOOSE_N / FIXED_ALL | Stage12 Shared Foundation | PARTIAL | YES | Add typed reusable ranking/selecting primitives only when core semantics require them; do not encode concrete skills |
| CGM-010 | Damage request / instance / settlement identity | Damage | DamageSystem / DamageInstanceCoordinator / DamageResolutionSystem / OperationIdAllocator | typed DamageRequest, DamageInstanceId, permits, lineage, settlement | Stage8-10 frozen runtime | ALREADY_IMPLEMENTED | NO | Reuse |
| CGM-011 | Damage source-family extensibility | Damage | DamageSourceType / SourceType + DamageInstanceCoordinator | normal, skill, continuous, counter plus frozen derived paths; production DamageEffect execution-right classification is finite | Stage9-11 runtime | PARTIAL | YES | Define extension seam without weakening existing family guards |
| CGM-012 | Damage modifier pipeline | Modifier / Damage | DamageModifierSystem | typed phases CRITICAL, OUTGOING, INCOMING, SINGLE_HIT; deterministic phase order | Stage8/11 frozen runtime | ALREADY_IMPLEMENTED | NO | Regression only |
| CGM-013 | Damage partition / share / distribution | Damage | DamagePartitionCoordinator | typed Share and Distribution plans; conservation tests | Stage9/11 frozen runtime | ALREADY_IMPLEMENTED | NO | Preserve 690086 research debt and project-default provenance |
| CGM-014 | Damage aftermath committed fact | Damage / Trigger | DamageAftermathSystem / DamageAftermathPort | standard, DOT, counter, assault, cleave checkpoint | Stage10 frozen runtime | ALREADY_IMPLEMENTED | NO | Reuse as one opportunity source |
| CGM-015 | Recovery settlement | Recovery | RecoverySystem + TroopSystem | modifier second CEIL, healing block, capacity, equipment contribution path | Stage10/11 frozen runtime | ALREADY_IMPLEMENTED | NO | Regression only |
| CGM-016 | Generic recovery opportunity model | Recovery / Trigger | RecoveryOpportunitySystem | FIRST_AID_AFTER_DAMAGE and RECUPERATION_ACTION_START only | Stage10 frozen runtime | PARTIAL | YES | Separate generic opportunity admission from the two existing state families |
| CGM-017 | Damage-derived attacker recovery | Recovery | Stage11AttackerRecoverySystem + RecoverySystem | Share assigned-damage basis, per-source first CEIL, shared second CEIL | Stage11 freeze | ALREADY_IMPLEMENTED | NO | Regression only |
| CGM-018 | Final battle attribute reads | Attribute | AttributeSystem | attack, defense, intelligence, speed; callers already route through owner | Stage2/4/8/11 runtime | PARTIAL | YES | Promote a typed battle-attribute vocabulary and source model |
| CGM-019 | Attribute modifier composition | Attribute / Modifier | AttributeSystem + AttributeModifierProvider + equipment contributions | opaque state modifier provider plus additive equipment contributions; no common flat/percent/source stacking contract | Existing runtime only | PARTIAL | YES | Design typed contribution model with provenance and deterministic phase/order rules |
| CGM-020 | Attribute snapshot / JIT policy | Attribute / Execution right | StateGenerationSnapshot + ExecutionRightSpec provide adjacent pieces | no generic attribute-value read policy per operation/hit | No complete authority | MISSING | YES | Add explicit read-mode primitive; future skill contracts select modes rather than hardcoding universal JIT/snapshot |
| CGM-021 | Sole RNG service | RNG | BattleContext.random / RandomSystem | only canonical production PRNG service; Stage12 audit guards direct random use | Stage12 RNG governance | ALREADY_IMPLEMENTED | NO | Preserve sole-owner rule |
| CGM-022 | RNG decision topology / replay trace | RNG / Replay | domain owners + RandomSystem | many frozen zero-draw/draw rules exist, but no generic decision-operation trace contract across future core primitives | Stage12 RNG governance partially covers current domains | RUNTIME_GOVERNANCE_REQUIRED | YES | Govern API-level decision trace and draw/no-draw contracts before new random primitives |
| CGM-023 | Core Effect primitive set | Effect | EffectExecutor | DamageEffect, ApplyStateEffect, RemoveStateEffect, RecoverEffect | Stage5-10 runtime | PARTIAL | YES | Add only core missing effect families, notably typed attribute modification if architecture requires it |
| CGM-024 | Multi-effect composition and ordering | Effect / Operation | SkillResolver ordered effect tuple + RuleHookSystem ordered intents | order exists locally; no generic operation-level sequence/abort/atomicity contract | Existing runtime only | PARTIAL | YES | Define composition semantics and failure boundary |
| CGM-025 | Delayed / repeated / scheduled work | Work lifecycle | state-specific periodic triggers and Sabotage scheduling | no generic delayed/repeated work owner | State-specific frozen authorities only | MISSING | YES | Introduce minimal typed pending-work owner with explicit execution-right/lifetime semantics |
| CGM-026 | Cross-domain modifier model | Modifier | DamageModifierSystem / RecoverySystem / AttributeSystem | strong domain-local owners, no shared typed metadata for activation/target/duration/effect-value modifiers | Existing domain authorities | PARTIAL | YES | Define shared modifier provenance/lifetime shell without centralizing domain math |
| CGM-027 | State lifetime | Lifecycle | StateLifetimeSpec / StateLifecycleSystem | round calendar, explicit phase expiry, holder action windows, persistent generation windows | Stage10/12 frozen runtime | ALREADY_IMPLEMENTED | NO | Reuse |
| CGM-028 | Generic Effect / Modifier lifetime | Lifecycle | none | state lifetime cannot own arbitrary pending effects/modifiers | No authority | MISSING | YES | Add reusable lifetime/expiry contract outside StateInstance |
| CGM-029 | Usage / charge / frequency / cooldown | Lifecycle / Frequency | narrow action/opportunity counters only | no canonical generic owner for N uses, once-per-round, once-per-target, cooldown | No authority | MISSING | YES | Design minimal UsageBudget/Frequency primitive or equivalent |
| CGM-030 | State / Provider dependency graph | Dependency | DependencyEvaluationSupport | StateNode, ProviderNode, atomic replacement, cycle detection, typed evaluation | Stage12 Shared Foundation | ALREADY_IMPLEMENTED | NO | Reuse; do not invent extra node kinds without a work requirement |
| CGM-031 | Pending-work validity dependencies | Dependency / Work | ExecutionRightSpec + specialized grants/ports | no generic work node carrying actor/provider/target/equipment/state validity across delay | Partial authorities | PARTIAL | YES | Integrate pending work with ExecutionRight rather than turning attribution into dependency |
| CGM-032 | Holder defeat cleanup | Death | DefeatCleanupPort + StateLifecycleSystem + VictorySystem | synchronous alive→defeated state cleanup and termination barriers | Stage10/11 frozen runtime | ALREADY_IMPLEMENTED | NO | Regression only |
| CGM-033 | Source defeat vs pending/scheduled work | Death / Work | mechanism-specific source_dependent rules + ProviderValidity | no universal rule, deliberately; no generic pending-work continuation/cancel contract | Frozen mechanism-specific authorities | PARTIAL | YES | Define work-level policy modes; preserve mechanism-specific frozen rules |
| CGM-034 | Unit / team canonical facts | Unit / Team | UnitRuntime + BattleContext | identity, team, ally/enemy, lineup, troops/max, alive | Stage1-3 runtime | ALREADY_IMPLEMENTED | NO | Reuse |
| CGM-035 | Operation identity / lineage | Identity | OperationIdAllocator + OperationLineage | typed Action, NA, target, damage, partition/reaction IDs; no generic SkillOperation/Effect/Recovery work identity | Stage9 runtime | PARTIAL | YES | Extend minimally for generic core work lineage |
| CGM-036 | Snapshot / JIT execution-right dimensions | Execution right | ExecutionRightSpec / ExecutionRightSupport | actor, provider, target, equipment, state effectiveness modes exist; attribute/effect-value/work-lifetime dimensions absent | Stage12 Shared Foundation | PARTIAL | YES | Extend dimensions only where new pending work requires them |
| CGM-037 | Exact state removal and lifecycle removal | Removal | StateRemovalPolicy / StateRemovalCoordinator | ordinary/specialized/scripted/infrastructure removal operations with unsupported boundaries | Stage12 Shared Foundation | ALREADY_IMPLEMENTED | NO | Reuse |
| CGM-038 | Generic cleanse / dispel / category removal | Removal | StateRemovalPolicy adapters | no universal positive/negative/buff/debuff category selector contract | Current frozen states only | PARTIAL | YES | Build typed category-removal primitive only from actual gameplay categories |
| CGM-039 | Global buff/debuff taxonomy | Taxonomy | none required | UI-style positive/negative taxonomy is not needed to run current frozen contracts | None required | NOT_NEEDED | NO | Do not invent gameplay semantics from UI labels |
| CGM-040 | Equipment contribution effectiveness | Equipment | EquipmentContributionRegistry / EquipmentEffectivenessPolicy | provider identity, contribution identity, suppression/effectiveness, attribute/damage/recovery/trigger seams | Stage12 frozen runtime | ALREADY_IMPLEMENTED | NO | Reuse; concrete equipment catalog is outside this inventory |
| CGM-041 | Provider validity / skill permission interoperability | Provider / Skill metadata | ProviderValidityPolicy / SkillPermissionPolicy / SkillOperationAdmissionCoordinator | pre-RNG admission, suppression, typed provider refs | Stage12 frozen runtime | ALREADY_IMPLEMENTED | NO | Reuse; not a declaration that full Skill Runtime exists |
| CGM-042 | Preparation minimal interoperability | Preparation | PreparationStateOwner / PreparationInterruptionPort | PREPARING storage/interruption only; explicitly no full preparation execution | Stage12 frozen runtime | ALREADY_IMPLEMENTED | NO | Keep minimal; full Preparation Runtime remains Stage14+ |
| CGM-043 | Deterministic replay verification | Replay | current seeded RNG + golden/integration tests | deterministic pieces exist but no Stage13 whole-battle replay audit over operation/RNG/target/damage/recovery/state/final result | Existing tests only | PARTIAL | YES | Build explicit replay trace + duplicate-run audit for Stage13-F |
| CGM-044 | Battle finalization and termination barriers | Finalization | BattleFinalizationCoordinator / VictorySystem / BattleEngine | typed termination generation, permits, barriers, victory projection | Stage9 frozen runtime | ALREADY_IMPLEMENTED | NO | Regression only |
| CGM-045 | 690221 See-Through family applicability: ACTIVE_SKILL | Research boundary | Stage11StateRuntime guard | frozen contract explicitly marks ACTIVE_SKILL unobserved / unsupported | 690221 frozen contract | RESEARCH_REQUIRED | YES | Focused model-separating research before claiming broad Active Skill readiness |
| CGM-046 | 690221 See-Through family applicability: DOT / DELAYED | Research boundary | Stage11StateRuntime guard | frozen contract explicitly marks DOT/DELAYED unobserved / unsupported | 690221 frozen contract | RESEARCH_REQUIRED | YES | Focused model-separating research or explicit Stage13 non-blocking boundary decision |
| CGM-047 | Existing bounded Stage12 micro-slices | Boundary | existing policy guards | Provocation/Capture/FalseReport/Sabotage bounded paths remain explicit unsupported boundaries | Stage12 contracts/default ledger | UNSUPPORTED | NO | Preserve until a concrete required consumer triggers reopen |
| CGM-048 | Politics / Charisma as battle attributes | Attribute | none | no current battle-core consumer identified | No gameplay need established | NOT_NEEDED | NO | Do not add unused attributes merely for data completeness |

## 5. Inventory totals

~~~text
ALREADY_IMPLEMENTED              22
PARTIAL                          16
MISSING                           4
RESEARCH_REQUIRED                 2
RUNTIME_GOVERNANCE_REQUIRED       1
UNSUPPORTED                       1
NOT_NEEDED                        2
TOTAL                            48
~~~

The table contains exactly 48 mechanism rows. These counts are checked by the Stage13 inventory audit test; prose totals are not a second source of truth.

## 6. High-level finding

The engine is not missing its entire combat foundation. The mature owners are concentrated in:

- state lifecycle / effectiveness / removal;
- provider and equipment effectiveness;
- natural action and normal attack;
- damage request/instance/settlement;
- recovery settlement;
- target operation identity and freshness;
- dependency graph and transaction atomicity;
- battle finalization;
- sole RNG service.

The implementation-required gaps are mainly generalization gaps that become visible only when moving from frozen state mechanics to large-scale Skill Runtime:

1. timing/opportunity breadth;
2. typed attribute modification and read timing;
3. generic effect/modifier composition;
4. delayed/repeated pending work;
5. usage/frequency/lifetime outside StateInstance;
6. work identity and execution-right continuity;
7. deterministic RNG/replay observability;
8. a small number of explicit empirical damage-family boundaries.

This means Stage13 should extend existing owners and compose them. A CoreGameplayGodObject is neither necessary nor allowed.

## 7. Stage13-A exit

~~~text
mechanism universe sufficiently enumerated      YES
owner inventory complete                         YES
all known gaps classified                        YES
research/governance gaps separated               YES
hidden Stage12 reopen                            NO
Skill System implementation leakage              NO
dependency order known                           YES

STAGE13_ENTRY_GATE                               PASS
Stage13 Active                                   YES
~~~

## 8. Unique NEXT

~~~text
NEXT =
STAGE13_B_GAP_CLASSIFICATION_AND_CLOSURE_PLANNING
~~~

Stage13-B must turn the implementation-required rows into closure batches, open focused research only for CGM-045/046, and prepare Runtime Governance questions for CGM-022 and the deterministic choices implied by the PARTIAL/MISSING work primitives. No gameplay implementation is authorized by this document.
