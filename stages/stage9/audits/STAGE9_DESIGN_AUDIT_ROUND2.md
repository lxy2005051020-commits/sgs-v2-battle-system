# Stage9 Design Audit Round 2

> Audit type: READ-ONLY REPAIRED-DESIGN AUDIT  
> Audit object: `stages/stage9/STAGE9.md`  
> Battle baseline: `928cd1d070435d95e9b969192d6ded67609386c3`  
> State-authority baseline: `15ed915435f328a6ecd8f488d98b5b9e13c913b5`  
> Locked `STAGE9.md` blob: `f28a6274741db23b5c8f0b9a13300d4185a6cf4c`  
> Status remains: `DRAFT — DESIGN AUDIT REQUIRED`; `Stage9 FROZEN = NO`; `Ready for implementation = NO`

## 1. Repository Baseline

Both remote `main` branches were re-read before the audit.

| Repository | SHA | Head |
|---|---|---|
| `lxy2005051020-commits/sgs-v2-battle-system` | `928cd1d070435d95e9b969192d6ded67609386c3` | `design(stage9): repair round1 architecture findings` |
| `lxy2005051020-commits/sgs-state-mechanics-research` | `15ed915435f328a6ecd8f488d98b5b9e13c913b5` | `docs(combo): close stale CBS9-B03 status banner` |

No baseline drift existed at audit start. `STAGE9.md` was locked read-only at blob `f28a6274741db23b5c8f0b9a13300d4185a6cf4c`.

## 2. Audit Scope

Round 2 independently audited the repaired `STAGE9.md` body rather than accepting the Round1 repair report as proof. The audit re-read the Round1 audit/repair records, authority map, typed runtime contracts, 42 runtime invariants, 45 regression contracts, pre-spec delta audit, relevant shared P0 finalization/execution contracts, and current production interfaces.

Production reality checks included `DamageSystem`, `DamageResolutionSystem`, `DamageResult`, `DamageResolutionResult`, `EffectExecutor`, `DamageEffectResult`, `effects.py`, `effect_result.py`, `BattleEngine`, `BattleContext`, `BattleSystems`, `VictorySystem`, `ActionSystem`, `NormalAttackSystem`, `SkillRuntime`, `SkillResolver`, `SkillDefinition`, `StateInstance`, `StateLifecycleSystem`, `StateRegistry`, `TroopSystem`, `EventBus`, `RecoverySystem`, `TriggerSystem`, `RuleHookSystem`, `official_state_catalog.py`, `state_runtime_params.py`, and representative existing tests.

This round performs no design repair, gameplay research, P0 modification, Stage8 modification, production/test modification, state-repository modification, implementation, Build Prompt authoring, or Stage9 freeze.

## 3. Round1 Repair Verification

### Round1 Finding Closure Matrix

| Finding | Round1 severity | Repair intent | Round2 verification | Status |
|---|---|---|---|---|
| F-01 Settlement fact/API ownership | BLOCKER | Model A typed settlement request/result + legacy mapping | Dtotal/Dtarget/actual/credit semantics are now unique; legacy route is representable | CLOSED |
| F-02 Finalization ownership | BLOCKER | Coordinator semantic owner + Engine projection | Semantic owner split is now conceptually unique, but finalized-result immutability/projection exactly-once enforcement remains incomplete | PARTIALLY CLOSED |
| F-03 Phase forward dependency | BLOCKER | move real execution/finalization before damage cutover | Old 9.4→9.7 forward dependency is removed; dependency graph itself is now acyclic and forward-free | CLOSED |
| F-04 `source_skill_slot` ingress | MAJOR | `SkillRuntime.skill_slot` -> Effect -> StateInstance | Carrier chain exists, but concrete producer, index convention, refresh/reapply provenance, and same-slot collision semantics are not frozen | PARTIALLY CLOSED |
| F-05 Exact integerization ingress | MAJOR | `ExactRatio` + exact conversion boundary | Exact Stage9 representation is implementable; no current Stage9 ratio config is forced through existing float state params | CLOSED |
| F-06 FutureAdmissionGate caller ownership | MAJOR | exactly-one caller matrix + admitted tokens | Caller matrix is complete, but structural no-bypass tokens/factories are explicit only for Chain; other global branches remain convention-enforced | PARTIALLY CLOSED |
| F-07 EffectExecutor result compatibility | MAJOR | narrow `DamageEffectResult` + `resolution` projection | Existing `.resolution` consumers can remain source-compatible without coordinator-result nesting | CLOSED |
| F-08 selected/intended target ambiguity | MINOR | remove `selectedTarget` | one selector output before Guard; no extra RNG field | CLOSED |
| F-09 engineering fallback labels | MINOR | explicit project-default labels | labeling is explicit and OperationId is forbidden as gameplay ordering | CLOSED |
| F-10 `TargetResolutionId` over-design | MINOR | trace-only label | explicitly trace-only/supporting | CLOSED |
| F-11 generic DerivedDamage abstraction | MINOR | Cleave-specific resolver | generic abstraction removed | CLOSED |
| F-12 unnecessary VictorySystem edit | MINOR | KEEP/CALL | current pure evaluator preserved | CLOSED |
| F-13 trace lifecycle | MINOR | bounded battle-scoped observation | lifecycle/overflow/non-authority behavior is now explicit | CLOSED |

Round1 closure summary:

```text
BLOCKER findings: 2 CLOSED, 1 PARTIALLY CLOSED
MAJOR findings:   2 CLOSED, 2 PARTIALLY CLOSED
MINOR findings:   6 CLOSED
```

The old defects were mostly repaired. Round2 nevertheless found new repair-interaction defects that prevent freeze admission.

## 4. Settlement Contract

### Semantic layer verdict

The repaired model cleanly separates:

```text
Dtotal                 = DamageResult.final_damage
Dtarget                = DamageSettlementRequest.assigned_target_damage
ActualTargetTroopLoss  = DamageResolutionResult.actual_target_troop_loss
CreditedDamage         = DamageResolutionResult.credited_damage / direct attribution fact
```

`DamageResult.final_damage` remains permanently Stage8 `Dtotal`; no Stage9 partition rewrites it.

### Settlement API Matrix

| API | Calculates? | Settles? | Supports partition? | Legacy? | Authoritative use |
|---|---:|---:|---:|---:|---|
| `DamageSystem.calculate` | YES | NO | NO | YES | sole Stage8 theoretical calculation |
| `DamageResolutionSystem.resolve` | YES | YES | NO | YES | legacy calculate + full `Dtotal` settlement only |
| `DamageResolutionSystem.settle` | NO | YES | YES | YES through typed origin | one assigned-target settlement primitive |
| `DamageResolutionSystem.apply_result` | NO | YES | NO | YES | optional full-settlement compatibility wrapper only |
| `DamageInstanceCoordinator` | ORCHESTRATES | ORCHESTRATES | YES | NO | authoritative Stage9 standard DamageInstance path |

Current production `resolve()` already performs one calculate followed by one troop mutation; `apply_result()` does not recalculate. The repaired compatibility mapping therefore does not inherently duplicate `calculate`, `DAMAGE_DEALT`, or troop mutation.

### Round2 settlement defect

The request/result meanings are unique, but `DamageSettlementRequest` has no frozen one-shot/duplicate-settlement contract. Reusing the same Stage9 settlement request can, from the current design alone, call `settle()` twice and mutate troops/publish facts twice. `damage_instance_id` exists and could support duplicate rejection, but Round2 does not infer an unwritten policy.

This is **R2-M04** below.

## 5. EffectExecutor Compatibility

Current production callers expect `DamageEffectResult.resolution: DamageResolutionResult`. The repaired shape:

```text
DamageEffectResult
  -> settlement_result: DamageResolutionResult
  -> resolution (read-only compatibility projection)
```

is sufficient for current tests/callers that read `resolution.damage`, `resolution.troop_change`, and defeat facts. It does not expose partition plans, reaction queues, finalization internals, or a multi-layer coordinator aggregate.

Result nesting remains bounded:

```text
DamageEffectResult
  -> DamageResolutionResult
      -> DamageResult
```

No five-layer result Russian doll is required.

**EffectExecutor result verdict: PASS.**

A separate Phase 9.5 source-identity ingress blocker exists and is not a result-shape defect.

## 6. Finalization Ownership

The repaired semantic ownership is correct at the conceptual level:

```text
BattleFinalizationCoordinator = semantic termination/latch/drain/finalize owner
VictorySystem                 = pure evaluator
BattleEngine                  = finalized-result compatibility projector
```

The design also correctly forbids Engine from re-calling `VictorySystem` after the coordinator has produced the finalized result.

### FinalizationResult completeness

The document requires:

```text
finalization_result.state == FINALIZED
finalization_result.battle_result
```

and current `BattleResult` contains winner/draw identity (`winner_team_id`), reason, rounds, and final troop snapshot. Semantically this is enough information for projection without a second victory calculation.

However, a concrete frozen `FinalizationResult` schema is never declared. More importantly, current `BattleResult` is a frozen dataclass containing a mutable `dict[str, int] final_troops`; wrapping it does not automatically produce the “immutable FinalizationResult” promised by the design.

### Exactly-once projection gap

Coordinator-side repeated `try_finalize()` is specified as idempotent, but Engine-side `_apply_finalized_battle_result(...)` has no explicit one-shot projection token/flag/result-identity contract. The document states `BATTLE_END` and `BATTLE_ENDED` must happen exactly once but does not structurally prevent the same finalized result from being projected twice.

This is **R2-M03** below. Semantic finalization ownership is unique; final result immutability/projection idempotency is not freeze-complete.

## 7. Execution Right / Admission

The three conceptual layers are correctly separated:

```text
ReactionPermissionPolicy = source/lineage permits reaction family?
FutureAdmissionGate       = global termination state permits new future work?
Local execution gate      = already-admitted work is locally executable now?
```

### Admission / Completion Matrix

| Work | Admission caller | Admission token? | Local gate | Completion notification | Victory-latch behavior |
|---|---|---|---|---|---|
| Action | `BattleEngine` | action scope implied, concrete gate token not frozen | actor/action validity | Action barrier | new Action blocked |
| Assault | `NormalAttackSystem` | no concrete branch token frozen | owner/local dispatch validity | dispatch terminal | new Assault blocked |
| Combo #2 | Combo checkpoint | no concrete branch token frozen | `can_normal_attack` / owner validity | NA #2 barrier | allocation blocked after latch |
| CounterBatch | `NormalAttackSystem` | no concrete batch-admission token frozen | entry-local owner/target gates | batch completion | new batch blocked |
| Counter sibling | admitted batch | immutable batch entry identity | owner liveness; dead target explicit zero path | entry/batch terminal | drains locally |
| ChainTraversal | `DamageCallbackAdmissionPoint` | **YES: admitted traversal token explicit** | trigger/current Chain/live owner rules | traversal completion | new traversal blocked; admitted traversal drains |
| Chain slot | admitted traversal scope | local traversal scope | monotonic cursor + live eligibility | slot terminal | no global re-gate |
| CleaveEffect | `CleaveSystem` next-effect boundary | no concrete effect-admission token frozen | effect/local source validity | effect terminal | next independent effect blocked |
| Cleave secondary | admitted effect plan | local effect scope | JIT target liveness | secondary/effect terminal | local drain |
| Share transaction | parent DamageInstance partition path | partition-local transaction identity | target-first local interrupt | transaction terminal | admitted micro-transaction follows local rule |
| Distribution transaction | parent DamageInstance partition path | immutable plan identity | participant JIT SKIP | transaction terminal | admitted fixed plan drains |

The caller matrix is good, and admitted local work is correctly forbidden from re-querying the global gate. But structural no-bypass enforcement is asymmetric: Chain explicitly requires an admitted token, while Action/Assault/Combo #2/CounterBatch/CleaveEffect are primarily protected by assigned-caller prose plus architecture tests.

That is insufficient to call INV-40 structurally closed in a Python codebase where constructors/factories remain otherwise callable. This is **R2-M02**.

## 8. Phase Buildability

### Phase-by-phase simulation

| Phase | Inputs already exist? | Production switch? | Independently green as written? | Round2 result |
|---|---:|---:|---:|---|
| 9.1 Identity/provenance/exact numeric | mostly | NO | NO | slot domain/index convention and generic float escape hatch need closure |
| 9.2 Execution Right + Finalization | current Engine/Victory exist | YES: terminal decision migration | **NO** | legacy macro barrier -> coordinator transition is unspecified |
| 9.3 Target + source-slot ingress | target/lifecycle seams exist | provenance path | NO | concrete slot producer/reapply semantics incomplete |
| 9.4 Settlement + isolated DamageInstance | depends on real 9.2 | NO EffectExecutor cutover | NO until upstream + settlement one-shot closed | direct fixture seam itself is sound |
| 9.5 Partition + direct loss + EffectExecutor cutover | depends on 9.1-9.4 | **YES** | **NO** | Stage9 `SourceType` ingress for existing DamageEffect paths missing |
| 9.6 NormalAttack + Combo | depends on prior phases | YES | NO | blocked upstream; admission token hardening incomplete |
| 9.7 Cleave + Chain + Counter | depends on prior phases | YES | NO | blocked upstream; Cleave slot identity/reapply ambiguity remains |
| 9.8 Integration | all above | full | NO | 3 invariants remain unenforced |

### Phase 9.2 compatibility blocker

Current Engine victory barriers occur after initial state, RoundStart hooks, UnitActionStart hooks, Action execution, RoundEnd, and max-round resolution. Phase 9.2 says “migrate Engine terminal decision to coordinator” and “preserve current engine/hook terminal ordering”, but it never freezes how those current synchronous legacy barriers become coordinator operation-completion/barrier signals before Stage9 Action/Reaction scopes exist.

No `legacy operation scope adapter`, synthetic barrier contract, or equivalent transition API is defined. Round2 therefore cannot prove that 9.2 is independently green without inventing behavior during implementation.

This is **R2-B01**.

### Phase 9.4 isolation

The isolated coordinator test strategy is sound: direct coordinator fixture/integration tests can exercise the settlement seam while `EffectExecutor` remains legacy. No production caller must point at an incomplete coordinator in 9.4.

### Phase 9.5 production cutover blocker

Stage9 permissions/lineage use `SourceType` (`ACTIVE_SKILL`, `PERIODIC_DAMAGE`, etc.), while current `DamageEffect` contains only Stage8 `DamageSourceType`. The repaired design explicitly states that Stage9 `SourceType -> DamageSourceType` is a one-way mapping performed when constructing legitimate Stage8 requests.

Yet Phase 9.5 switches every production `DamageEffect` into `DamageInstanceCoordinator` without defining where authoritative Stage9 `SourceType` comes from. Current active-skill DamageEffects carry `DamageSourceType.SKILL`; current periodic TriggerSystem DamageEffects carry `DamageSourceType.CONTINUOUS`; `TriggerSystem` is listed KEEP.

Reverse-inferring Stage9 permission identity from Stage8 formula classification would contradict the design's own ownership boundary. Adding a new source identity to Effects would require an explicit producer chain, including periodic/triggered effects.

This mandatory production path is unspecified. This is **R2-B02**.

### Dependency verdict

The old forward dependency is genuinely gone:

```text
Dependency cycles = 0
Forward production dependencies = 0
```

The failure is instead two missing transition/ingress contracts inside phases that are claimed independently green.

## 9. Source Skill Slot Provenance

The repaired propagation chain is directionally correct:

```text
SkillRuntime
-> SkillResolver
-> DamageEffect / ApplyStateEffect
-> EffectExecutor
-> StateLifecycleSystem
-> StateInstance.source_skill_slot
-> Stage9StateRuntime
-> Cleave / Counter ordering
```

But Round2 finds four unresolved engineering facts:

1. current `UnitRuntime` has no equipped-skill collection and current production has no identified loaded-runtime builder that “already knows equipped position”; the spec names a conceptual producer but not a concrete production construction surface;
2. `skill_slot` is only `int | None`; 0-based vs 1-based and valid range are not frozen;
3. `StateInstance` being frozen prevents in-place mutation, but refresh/reapply behavior is not specified: same-source refresh must not silently change source-slot provenance;
4. same-slot Cleave tie behavior is therefore not uniquely closed if duplicate/same-source instances can coexist; OperationId is correctly forbidden, but no second tie-break/default is frozen for that reachable shape.

**Verdict: PARTIAL / MAJOR.** This is **R2-M01** and keeps INV-18 from being fully enforceable.

`DamageEffect.source_skill_slot` also lacks a named downstream consumer distinct from ApplyState provenance. If it remains merely optional provenance, a narrow source-reference value object would be cleaner than unrelated field spread. This ergonomic issue is recorded as **R2-N02** rather than a gameplay defect.

## 10. Exact Numeric Representation

`ExactRatio(numerator, denominator)` with normalized/reduced positive denominator is implementable and Stage8 floats remain properly isolated.

Current production review found no existing Stage9 Cleave/Chain/Share/Distribution ratio config loader that forces those ratios through float. `official_state_catalog.py` currently stores IDs/text only; `StateRuntimeParams` is an extensible frozen typed base; current periodic `coefficient: float` belongs to the frozen Stage8 damage coefficient path, not Stage9 exact partition/reaction ratio arithmetic.

Therefore the intended safest ingress is available:

```text
Stage9 typed config/runtime params
-> exact textual/Decimal parse
-> ExactRatio immediately
```

The design's generic fallback `Decimal(str(float))` is not tied to a named current Stage9 ratio surface. If used on a previously computed float, it preserves the float's decimalized artifact rather than recovering original exact source intent. It should not become a generic primary ingress.

Canonicalization says normalized/reduced and denominator > 0, which implies gcd reduction in ordinary implementations, but unique zero representation (`0/1`) is not stated explicitly.

**Verdict: PASS WITH MINOR CONTRACT TIGHTENING.** This is **R2-N01**.

## 11. NormalAttack Orchestration

The repaired responsibility budget is adequate.

`NormalAttackSystem` owns lifecycle/orchestration, IDs, component order, assigned branch-admission call sites, and result assembly; it explicitly does not own target algorithms, partition math, state mutation, Cleave/Chain/Counter algorithms, finalization state, or Stage8 formulas.

No requirement forces it to import mechanism-internal implementation details rather than injected service interfaces.

**God-object risk: CONTROLLED / LOW if the documented boundaries are enforced.**

## 12. Partition / DirectLoss

The partition plan preserves one resolver result (`NONE | SHARE | DISTRIBUTION`) per DamageInstance. Share target-first and Distribution fixed-plan behavior remain distinct; no generic mechanism-switch executor is required.

`DirectTroopLossResolver` correctly bypasses `DamageSystem`, HitResolution, Counter, Chain, Share, Distribution, FirstAid, and generic Hurt callbacks. It may produce attribution and `UnitDeathFact`, then notify finalization directly through typed coordinator calls.

Most importantly:

```text
AttributedDirectTroopLoss
-X-> DamageCallbackAdmissionPoint
```

so Share/Distribution direct loss cannot accidentally create Chain traversal.

**Verdict: PASS.**

## 13. Cleave

Current-effect admission semantics are explicit:

- current admitted `CleaveEffect` freezes secondary identities;
- secondaries are local work and do not re-query global admission;
- victory latch during the current effect does not cancel locally legal remaining secondaries;
- next independent CleaveEffect is a future branch and must pass the gate.

Derived damage correctly uses `ActualTargetTroopLoss` and exact FLOOR, with no Stage8 base-formula/modifier/Crit re-entry.

The remaining weakness is source-slot provenance/tie closure from §9, not Cleave's admission semantics.

**Admission verdict: PASS. Ordering provenance verdict: PARTIAL via R2-M01.**

## 14. Chain

The monotonic ascending slot cursor directly implements live expansion without rescanning:

```text
passed slot -> never revisited
not-yet-reached later slot -> live-read when cursor reaches it
```

The shared `DamageCallbackAdmissionPoint` remains narrow: it owns new ChainTraversal admission only, while ChainSystem owns traversal execution. DirectTroopLoss cannot enter it.

**Verdict: PASS.**

## 15. Counter

The design does not turn `source_skill_slot` into an unauthorized universal Counter comparator. Where P0 has authoritative slot metadata it can be used; where comparator fidelity remains open, the isolated mechanism-local deterministic fallback remains explicitly non-official.

Admission snapshot and execution-time owner/target gates remain separate. Dead-target sibling uses explicit zero-loss terminal behavior without fake Stage8 damage.

**Verdict: PASS.**

## 16. State Runtime Integration

`StateRegistry` remains the sole physical state container and `StateLifecycleSystem` remains the formal mutation writer. `Stage9StateRuntime` is a typed read/maintenance adapter, not a second state store.

The architecture boundary is sound, but the source-slot reapply/refresh provenance gap in §9 must be closed before design freeze.

## 17. Event / Trace Boundaries

Current `EventBus` explicitly represents observation/history and the repaired design says coordinator direct calls, not event subscribers, own Stage9 control flow.

Current production inspection found no runtime subscriber that relies on `DAMAGE_DEALT.requested_damage == DamageResult.final_damage`; existing tests primarily inspect event type/history. Therefore changing the event payload meaning to actual submitted settlement amount (`Dtarget`) on partitioned Stage9 paths does not break a known production control-flow consumer.

`Stage9OperationTrace` is separately battle-scoped, bounded/configurable, non-authoritative, and never read for gameplay decisions.

**Verdict: PASS.**

## 18. Operation Identity

Typed operation IDs and `OperationLineage` remain runtime identity/trace authority, never gameplay priority. `TargetResolutionId` is explicitly supporting trace only.

Architecture tests must continue to reject operation IDs appearing in sorting/comparator logic.

**Verdict: PASS.**

## 19. Error / Idempotency Model

The repaired error taxonomy is mostly clear:

```text
Programmer/domain invariant violation:
- duplicate operation identity
- illegal recursive dispatch
- double Combo consume
- missing P0-required source slot
- conflicting finalization

Expected combat invalidation:
- dead secondary
- dead Counter owner
- invalid planned Distribution participant
- target-specific local skip/cancel

Compatibility path:
- deterministic legacy wrapper, not warning-driven behavior
```

Two idempotency gaps remain:

1. **Settlement replay**: no frozen duplicate-rejection/one-shot contract for the same Stage9 settlement request (`R2-M04`).
2. **Engine finalization projection replay**: exact-once publication is asserted but the one-shot projection mechanism is not frozen (`R2-M03`).

Combo atomic consume, immutable partition plan, CounterBatch admission, Chain traversal admission, and coordinator victory/finalization observation are otherwise explicitly guarded.

## 20. File Plan

### Recomputed NEW files

The 16 planned NEW files are individually justified by distinct responsibilities. No required merge candidate rises to MAJOR severity; `reaction_permission_policy.py`, `execution_right_system.py`, and `battle_finalization_coordinator.py` answer different questions (permission vs admission vs termination).

```text
Planned NEW in spec = 16
Clearly unjustified NEW = 0
```

However the source-slot producer remains an unnamed production surface, so `NEW=16` cannot yet be treated as final/frozen if closure requires a dedicated loaded-skill holder/builder.

### Recomputed MODIFY files

The spec lists 16 MODIFY files. Round2 identifies one concrete missing candidate:

```text
trigger_system.py
```

If Stage9 `SourceType` is made explicit on `DamageEffect` so Phase 9.5 does not reverse-infer permission identity from `DamageSourceType`, periodic DamageEffects must receive `PERIODIC_DAMAGE` at their producer. Current `TriggerSystem` creates those effects and is currently listed KEEP.

Additionally, the actual holder-specific loaded `SkillRuntime` construction surface is not identified; its eventual file ownership is unresolved.

```text
Planned MODIFY in spec = 16
Minimum recomputed MODIFY candidates = 17
Concrete missing MODIFY candidate = trigger_system.py
Unresolved producer surface = loaded SkillRuntime construction/skill-slot owner
Unjustified planned MODIFY = 0
```

The exact final count must not be frozen until R2-B02/R2-M01 close.

## 21. Dependency / Composition Root

`BattleSystems` remains the proper composition root. `BattleContext` is restricted to battle data, `OperationIdAllocator`, and a small termination record/read state; systems, policies, queues, trace services, partition services, and mechanism runtime bags remain outside Context.

No required static dependency cycle is present.

```text
Dependency cycles = 0
BattleContext service-locator expansion = 0
```

## 22. 42 Invariant Recheck

Round2 independently rechecked all 42 invariants against the repaired architecture.

| INV | Round2 | Reason |
|---:|---|---|
| 01 | ENFORCED | immutable target identity fields |
| 02 | ENFORCED | selector structurally precedes Guard |
| 03 | ENFORCED | one Guard pass/NA assertion |
| 04 | ENFORCED | downstream actual-target contract |
| 05 | ENFORCED | concrete settlement owns recipient |
| 06 | ENFORCED | fresh #2 identity/result |
| 07 | ENFORCED | physical/operational/grant types split |
| 08 | ENFORCED | ActionStart maintenance before grant |
| 09 | ENFORCED | remove vs suppress transition |
| 10 | ENFORCED | checkpoint ceiling |
| 11 | ENFORCED | atomic consume ceiling |
| 12 | ENFORCED | <=2 physical NAs/Action |
| 13 | ENFORCED | Cleave typed source/identity |
| 14 | ENFORCED | actual target troop loss basis |
| 15 | ENFORCED | exact FLOOR helper/vector |
| 16 | ENFORCED | Cleave derived route has no Stage8 base formula edge |
| 17 | ENFORCED | typed permission policy |
| 18 | **UNENFORCED** | slot producer/indexing/reapply/same-slot closure incomplete |
| 19 | ENFORCED | direct loss distinct type |
| 20 | ENFORCED | direct loss bypasses HitResolution/callbacks |
| 21 | ENFORCED | explicit direct-loss provenance |
| 22 | ENFORCED | exactly-one partition plan |
| 23 | ENFORCED | replacement non-resurrection boundary |
| 24 | ENFORCED | Share target-first |
| 25 | ENFORCED | lethal target local interrupt |
| 26 | ENFORCED | damage layers remain typed/distinct |
| 27 | ENFORCED | Distribution participants/N immutable |
| 28 | ENFORCED | calculated amounts immutable |
| 29 | ENFORCED | invalid participant SKIP-only |
| 30 | ENFORCED | no late participant join |
| 31 | ENFORCED | DSTS9-B02 local labeled default |
| 32 | ENFORCED | Chain snapshot schema narrow |
| 33 | ENFORCED | execution fields live-read |
| 34 | ENFORCED | monotonic one-pass cursor |
| 35 | ENFORCED | restricted Chain settlement |
| 36 | ENFORCED | CounterBatch immutable admission snapshot |
| 37 | ENFORCED | admission vs owner-liveness gate split |
| 38 | ENFORCED | explicit Counter dead-target zero terminal |
| 39 | ENFORCED | death/latch/finalized states split |
| 40 | **UNENFORCED** | no-bypass structural token/factory protection incomplete outside Chain |
| 41 | ENFORCED | coordinator alone owns termination-state transition; Engine is projection-only by contract |
| 42 | **UNENFORCED** | production DamageEffect cutover lacks authoritative Stage9 `SourceType` ingress |

Recomputed:

```text
STRUCTURAL / TYPE / RUNTIME enforced total = 39
UNENFORCED                                  = 3
TOTAL                                       = 42
```

The repaired document's claimed `42/42 enforced` is therefore not independently sustained.

## 23. 45 Regression Testability

All 45 gameplay regressions still have clear Given/When/Then expected behavior and fixture seams. None requires log-string parsing.

The new defects block architecture/phase admission, but they do not make the frozen gameplay expectations unknowable. A test can still explicitly construct slot fixtures, source identities, or finalization states once the missing architecture contracts are supplied.

```text
Mandatory gameplay regressions = 45
Testable                       = 45
Untestable                     = 0
Unmapped                       = 0
```

The supporting settlement fixture `Dtotal != Dtarget != ActualTargetTroopLoss` remains directly testable after the settlement one-shot contract is added.

## 24. Architecture-Test Mapping

Round2 requires at least the following architecture tests in implementation. These are separate from the 45 gameplay IDs.

| Architecture guarantee | Planned architecture test | Current design testability |
|---|---|---|
| no Stage8 semantic/import inversion | dependency/import test: Stage8 calculation types never import Stage9 mechanism services | READY |
| FutureAdmissionGate no bypass | every global branch allocator/factory requires gate-issued capability/token | **BLOCKED: R2-M02** |
| finalization single semantic writer | only coordinator mutates termination state; Engine never evaluates victory after finalized result | READY |
| Engine final projection exactly once | repeated projection attempt cannot emit second BATTLE_END/BATTLE_ENDED or rewrite result | **BLOCKED: R2-M03** |
| OperationId never gameplay ordering | static/source test forbids operation IDs in gameplay comparators/sort keys | READY |
| StateRegistry sole storage | source/architecture test forbids second physical state container | READY |
| StateLifecycleSystem sole mutation | source test forbids direct `states.add/remove` outside lifecycle owner | READY |
| EventBus facts-only | no subscriber callback is required for Stage9 orchestration/finalization | READY |
| BattleSystems composition root | construction graph test + BattleContext anti-service-locator assertion | READY |
| settlement one-shot | same Stage9 settlement identity cannot mutate troops/publish twice | **BLOCKED: R2-M04** |
| EffectExecutor Stage9 source identity | active/periodic DamageEffect enters coordinator with explicit Stage9 SourceType; no reverse inference | **BLOCKED: R2-B02** |
| source-skill-slot ingress/immutability | loaded slot convention, propagation, refresh/reapply invariance, no inference | **BLOCKED: R2-M01** |

```text
Required architecture tests mapped = 12
READY                           = 7
BLOCKED BY DESIGN               = 5
```

## 25. Stage8 Boundary

Round2 found no Stage8 semantic reopen.

```text
DamageResult.final_damage = Dtotal permanently
DamageResult.requested_damage compatibility alias = Dtotal
Stage8 formula/modifier/prevention/hit semantics unchanged
Stage9 settlement/partition remains an outer orchestration layer
Stage8 semantic reopen = 0
```

The missing Stage9 `SourceType` ingress must be solved without mutating Stage8 `DamageSourceType` semantics.

## 26. Research Debt Isolation

`DSTS9-B02` remains isolated to Distribution local continuation policy:

```text
Empirical = OPEN / UNOBSERVED
Runtime = PROJECT_RUNTIME_DEFAULT
Admission impact = NON-BLOCKING
```

No finalization/coordinator rule branches on the finding ID or on “distribution commander died” as a global special case. Finalization only needs admitted-operation completion/victory-latch facts.

**Research debt isolation verdict: PASS.**

## 27. Findings

### BLOCKER

**R2-B01 — Phase 9.2 has no frozen legacy finalization compatibility bridge.**  
The design migrates Engine semantic terminal decisions before Stage9 operation scopes exist, but does not define how current RoundStart/UnitActionStart/Action/RoundEnd/max-round barriers become coordinator completion/finalization signals. Phase 9.2 cannot be proven independently green without inventing a transition policy during implementation.

**R2-B02 — Phase 9.5 production `DamageEffect` cutover lacks authoritative Stage9 `SourceType` ingress.**  
Current Effects carry Stage8 `DamageSourceType`; Stage9 permission/lineage requires `SourceType`. The design forbids treating Stage8 formula classification as the semantic owner, yet does not add a Stage9 source identity producer for active/periodic/triggered DamageEffects before routing them into `DamageInstanceCoordinator`. This is a mandatory production path with undefined identity.

### MAJOR

**R2-M01 — `source_skill_slot` remains incomplete as a production provenance contract.**  
Carrier/storage propagation is specified, but the concrete loaded-runtime producer is not identified, index convention is not frozen, refresh/reapply source-slot immutability is unspecified, and same-slot Cleave ordering can therefore lack a deterministic non-OperationId tie rule.

**R2-M02 — FutureAdmissionGate no-bypass enforcement is not structural for all branch families.**  
The caller matrix is complete, but only Chain explicitly requires a gate-issued admitted token. Action/Assault/Combo #2/CounterBatch/CleaveEffect still rely on caller discipline plus architecture tests rather than a constructor/factory/capability boundary.

**R2-M03 — Finalization result/projection idempotency is under-specified.**  
`FinalizationResult` has no explicit frozen schema/immutable snapshot contract, current nested `BattleResult.final_troops` is mutable, and Engine's finalized projection has no frozen one-shot guard even though BATTLE_END/BATTLE_ENDED are required exactly once.

**R2-M04 — Stage9 settlement has no duplicate-consumption guard.**  
The same typed `DamageSettlementRequest`/DamageInstance settlement identity can be submitted to `settle()` repeatedly under the written API. The design must classify duplicate settlement as a programmer/domain error or otherwise enforce one-shot settlement before claiming idempotent damage plumbing.

### MINOR

**R2-N01 — ExactRatio canonical/ingress wording is slightly too permissive.**  
State unique zero (`0/1`) explicitly and do not let the generic `Decimal(str(float))` compatibility branch become an unnamed primary Stage9 ratio ingress when no current exact-ratio source requires it.

**R2-N02 — `DamageEffect.source_skill_slot` has no named current consumer.**  
ApplyState provenance clearly requires the slot; DamageEffect carries it only as broad provenance while `DamageRequest` and current lineage do not. Keep the field only with an explicit consumer/source-ref contract, otherwise avoid field spread.

### DOC_ONLY

None.

## 28. Final Gate

Recomputed Round2 gate:

```text
BLOCKER = 2
MAJOR   = 4
MINOR   = 2
DOC_ONLY = 0

P0 semantic conflict             = 0
Stage8 reopen                    = 0
Dependency cycle                 = 0
Forward production dependency    = 0
Unowned runtime facts            = 2
Unspecified reachable paths      = 5
Unenforced invariants            = 3
Untestable mandatory regressions = 0
```

Unowned runtime facts:

1. authoritative Stage9 `SourceType` for production DamageEffect cutover;
2. concrete producer/domain convention for `source_skill_slot`.

Primary unspecified reachable path families:

1. legacy macro barrier -> coordinator completion/finalization transition in Phase 9.2;
2. active/periodic/triggered DamageEffect -> Stage9 source identity in Phase 9.5;
3. source-slot refresh/reapply/same-slot provenance path;
4. duplicate settlement submission;
5. duplicate finalized-result projection.

Design Freeze admission criteria are not met.

```text
DESIGN FREEZE ADMISSION = NOT ELIGIBLE
```

## 29. Verdict

```text
VERDICT = FAIL — DESIGN REPAIR REQUIRED

Stage9 FROZEN = NO
Ready for implementation = NO
STATUS = DRAFT — DESIGN AUDIT REQUIRED

NEXT STEP:
Stage9 Design Repair Round 2
```

Round2 does not prescribe gameplay changes and does not reopen P0. The next repair should be narrow and limited to the Round2 findings above. No automatic Round3 is authorized by this audit; whether a later delta audit or Round3 is necessary depends on the repair scope.