# Stage9 Design Audit Round 3

> Audit type: **FINAL REPAIRED-DESIGN VERIFICATION**  
> Audit date: 2026-09-13  
> Battle baseline audited: `394d32e40b6584db9814f46dfbf44a2d5e753893`  
> State authority baseline: `15ed915435f328a6ecd8f488d98b5b9e13c913b5`  
> `STAGE9.md` baseline blob: `8972452d68d6c71e45563a9a2ec5d70826978c9b`  
> Audit mode: **READ-ONLY DESIGN AUDIT — NO REPAIR / NO IMPLEMENTATION / NO FREEZE**

---

## 1. Repository Baseline

Remote `main` was re-read before audit and again immediately before this report was created.

```text
battle main = 394d32e40b6584db9814f46dfbf44a2d5e753893
design(stage9): repair round2 architecture findings

state main  = 15ed915435f328a6ecd8f488d98b5b9e13c913b5
docs(combo): close stale CBS9-B03 status banner
```

No pre-audit remote drift was observed.

The repaired `stages/stage9/STAGE9.md` was locked as a read-only audit input at blob:

```text
8972452d68d6c71e45563a9a2ec5d70826978c9b
```

Its admission status at audit start remained:

```text
STATUS                   = DRAFT — DESIGN AUDIT REQUIRED
Stage9 FROZEN            = NO
Ready for implementation = NO
Round3 design audit      = REQUIRED / NOT EXECUTED
```

This Round3 does not modify that file or execute Design Freeze.

---

## 2. Audit Scope

Round3 fully re-read the required Stage9 design chain:

```text
stages/stage9/STAGE9.md
stages/stage9/audits/STAGE9_DESIGN_AUDIT_ROUND1.md
stages/stage9/audits/STAGE9_DESIGN_REPAIR_ROUND1.md
stages/stage9/audits/STAGE9_DESIGN_AUDIT_ROUND2.md
stages/stage9/audits/STAGE9_DESIGN_REPAIR_ROUND2.md
stages/stage9/docsync/STAGE9_AUTHORITY_MAP.md
stages/stage9/hardening/STAGE9_TYPED_RUNTIME_CONTRACTS.md
stages/stage9/hardening/STAGE9_RUNTIME_INVARIANTS.md
stages/stage9/hardening/STAGE9_REGRESSION_CONTRACTS.md
stages/stage9/audits/STAGE9_GLOBAL_CROSS_MECHANISM_FINAL_AUDIT.md
stages/stage9/audits/STAGE9_PRE_SPEC_DELTA_AUDIT.md
```

Round3 also re-read the current production implementation surfaces required by the prompt, including:

```text
BattleEngine / BattleContext / BattleSystems / VictorySystem
DamageSystem / DamageResolutionSystem / DamageResult / DamageResolutionResult
EffectExecutor / DamageEffectResult / effects.py / effect_result.py
SkillRuntime / SkillResolver / SkillDefinition
TriggerSystem / RuleHookSystem
StateInstance / StateLifecycleSystem / StateRegistry
ActionSystem / NormalAttackSystem / TroopSystem / EventBus
```

Additional production surfaces used to validate the exact-numeric and file-plan boundaries were re-read where needed (`enums.py`, `stage7_state_params.py`, `state_runtime_params.py`, `official_state_catalog.py`, `__init__.py`).

GitHub code-search indexing was incomplete for `DamageEffect`, so the producer count was **not** accepted from an empty search result. It was independently reconstructed from the full `sgs_v2/battle_core` production file inventory plus every effect-producing/routing surface. This avoids mistaking an index failure for architectural evidence.

Round3 deliberately did **not**:

```text
repair STAGE9.md
modify Round2 repair record
modify gameplay P0
modify production code
modify tests
modify Stage8
modify state repo
create a Build Prompt
implement Stage9
execute Stage9 Design Freeze
```

---

## 3. Round2 Repair Closure Matrix

| Finding | Repair design | Round3 independent verification | Status |
|---|---|---|---|
| R2-B01 | six typed legacy finalization barriers + Phase 9.2 compatibility bridge + ACTION_SETTLED delayed projection | current `BattleEngine.run()` has exactly the six claimed checkpoints; repaired mapping is 1:1; Phase 9.2 requires no future operation stubs and preserves action-end observable order | **CLOSED** |
| R2-B02 | authoritative `EffectSourceRef`; active skill producer = `ACTIVE_SKILL`; periodic producer = `PERIODIC_DAMAGE`; no reverse enum inference | current production has exactly two reachable `DamageEffect` constructors: `SkillResolver._build_effect` and `TriggerSystem._effects_for_state`; `EffectExecutor` is only a consumer; NormalAttack is separate | **CLOSED** |
| R2-M01 | typed 0-based `SkillSlot`; holder-specific `LoadedSkillRef/LoadedSkillSet`; duplicate-slot rejection; refresh provenance guard | current runtime gap is exactly where repair says it is; holder runtime is the correct narrow ingress; no UnitRuntime loadout is required; same-source slot mutation is explicitly a domain error | **CLOSED** |
| R2-M02 | one-shot `FutureAdmissionPermit`; permit-required future branch factories; caller matrix; no-bypass architecture test | all six global future branches gate before identity allocation/admission; already-admitted siblings/steps are explicitly exempt from re-gating | **CLOSED** |
| R2-M03 | deep-immutable `FinalizationResult`; one-shot projection claim/consume; Engine compatibility projection only | schema contains all Engine projection facts; snapshot is deep immutable; projection consumes permit before any compatibility side effect; no second VictorySystem evaluation | **CLOSED** |
| R2-M04 | one `DamageSettlementPermit` per Stage9 DamageInstance; consume before troop mutation | destructive settlement has a structural replay guard; duplicate settlement fails before troop/event side effects; legacy resolve remains independent | **CLOSED** |
| R2-N01 | canonical `ExactRatio`; no generic `from_float`; named compatibility-only float adapter if ever proven necessary | positive denominator, gcd reduction, numerator sign, `0/1` zero all frozen; no current Stage9 exact-ratio source is forced through computed float | **CLOSED** |
| R2-N02 | shared `EffectSourceRef`; clear distinction from `OperationLineage` | pre-operation provenance and runtime ancestry have separate owners; unique conversion occurs at `DamageInstanceCoordinator` admission | **CLOSED** |

```text
Round2 findings checked = 8
CLOSED                  = 8
PARTIALLY CLOSED        = 0
REOPENED                = 0
```

---

## 4. Legacy Finalization Bridge

### 4.1 Current production checkpoint re-scan

Round3 independently re-read `BattleEngine.run()` and confirmed six, and only six, current terminal evaluation checkpoints.

| Barrier | Current production fact | Repaired adapter fit | Verified |
|---|---|---|---|
| `INITIAL_SETTLED` | `VictorySystem.check` after PRE_BATTLE / BATTLE_STARTED before round 1 | observe initial barrier | YES |
| `ROUND_START_HOOKS_SETTLED` | check after ROUND_START expiry/event/hook processing | observe round-start-hooks barrier | YES |
| `UNIT_ACTION_START_HOOKS_SETTLED` | check after UNIT_ACTION_STARTED + UnitActionStartHook before action | observe unit-action-start-hooks barrier | YES |
| `ACTION_SETTLED` | check immediately after `ActionSystem.execute` | semantic observe/latch here; projection delayed | YES |
| `ROUND_END_SETTLED` | check after ROUND_ENDED + round-end expiry | observe round-end barrier | YES |
| `MAX_ROUND_SETTLED` | `VictorySystem.resolve_max_rounds` after loop | observe max-round barrier | YES |

```text
legacy barriers verified = 6/6
unmapped terminal checks  = 0
```

### 4.2 ACTION_SETTLED ordering

Current code fact is:

```text
ActionSystem.execute
→ VictorySystem.check
→ enter UNIT_ACTION_END
→ publish UNIT_ACTION_ENDED
→ _finish / legacy projection
```

The repaired design preserves that observable order as:

```text
ActionSystem.execute
→ ACTION_SETTLED
→ coordinator evaluate/latch/finalize semantically
→ enter UNIT_ACTION_END
→ publish UNIT_ACTION_ENDED
→ claim/consume finalized projection
→ context/result/BATTLE_END/BATTLE_ENDED projection
```

Projection is therefore **not** moved before `UNIT_ACTION_ENDED`.

```text
ACTION_SETTLED ordering verdict = PASS
```

### 4.3 Phase 9.2 independent-green check

The repaired Phase 9.2 explicitly defines:

```text
real BattleFinalizationCoordinator
real six-barrier adapter
real FutureAdmissionGate base capability
Stage9 admitted-operation set = EMPTY
ActionScope count              = 0
DamageInstance count           = 0
ReactionBatch count            = 0
stub operation scopes          = FORBIDDEN
```

Therefore victory at any legacy barrier can immediately reach `FINALIZED` when no Stage9 operation has yet been introduced, then be projected at the same compatibility point as current Engine behavior.

No implementer needs to invent an unstated legacy bridge and no later-phase `ActionScope`, `DamageInstance`, or `ReactionBatch` stub is required.

```text
R2-B01 verdict                 = CLOSED
Phase 9.2 independently green = YES
```

---

## 5. SourceType / EffectSourceRef

### 5.1 Production `DamageEffect` producers

Round3 re-established the current production producer inventory from source:

| Producer | Current Stage8 source | Required Stage9 source | Round3 result |
|---|---|---|---|
| `SkillResolver._build_effect` | `DamageSourceType.SKILL` | `EffectSourceRef.stage9_source_type = ACTIVE_SKILL` | classified |
| `TriggerSystem._effects_for_state` | `DamageSourceType.CONTINUOUS` | `EffectSourceRef.stage9_source_type = PERIODIC_DAMAGE` | classified |

Current non-producers were rechecked:

```text
EffectExecutor     = consumer/router only
RuleHookSystem     = TriggerSystem -> EffectExecutor routing only
NormalAttackSystem = does not construct DamageEffect
```

```text
production DamageEffect producers = 2
classified                         = 2
unclassified                       = 0
```

### 5.2 No reverse inference

The repaired design makes Stage9 provenance authoritative at the semantic producer. It explicitly forbids:

```text
DamageSourceType.SKILL      -> infer ACTIVE_SKILL
DamageSourceType.CONTINUOUS -> infer PERIODIC_DAMAGE
DamageSourceType.COUNTER    -> infer runtime ancestry/permission
```

`EffectExecutor` therefore consumes `EffectSourceRef`; it does not manufacture Stage9 identity from the older Stage8 enum.

### 5.3 NormalAttack ingress

Current `NormalAttackSystem` directly builds a Stage8 `DamageRequest` and does not use `DamageEffect`. The repaired design correctly leaves that architecture intact:

```text
NormalAttackSystem / DamageInstanceCoordinator
→ SourceType.NORMAL_ATTACK
→ one-way mapping to DamageSourceType.NORMAL_ATTACK
```

No fake `DamageEffect` wrapper is required.

### 5.4 `EffectSourceRef` vs `OperationLineage`

The repaired ownership split is implementable and non-overlapping:

```text
EffectSourceRef
= effect creation/application provenance
= may exist before Stage9 operation IDs

OperationLineage
= runtime operation ancestry
= Stage9 operation identities + current operation SourceType
```

Unique conversion point:

```text
EffectSourceRef + runtime parent scope
→ DamageInstanceCoordinator
→ OperationLineage
```

No second conversion owner is specified.

```text
R2-B02 verdict                 = CLOSED
EffectSourceRef verdict        = PASS
OperationLineage conversion    = UNIQUE / PASS
INV-42 source-identity closure = ENFORCED
```

---

## 6. SkillSlot / State Provenance

### 6.1 Typed domain

The repaired design freezes:

```python
class SkillSlot(IntEnum):
    INHERENT  = 0
    LEARNED_1 = 1
    LEARNED_2 = 2
```

```text
indexing     = 0-based
legal domain = {0,1,2}
```

This is compatible with the current project because slot is holder/loadout provenance, not a `SkillDefinition` property. `SkillDefinition` remains static.

### 6.2 Holder-specific producer

The current code has `SkillRuntime(definition, owner_id, enabled)` and no UnitRuntime loadout collection. The repaired design adds the narrow missing producer in `skill_runtime.py`:

```text
LoadedSkillRef(owner_id, definition, skill_slot)
LoadedSkillSet(owner_id, loaded)
SkillRuntime.from_loaded(...)
```

`LoadedSkillSet` enforces:

```text
same owner
legal typed slot
no duplicate slot for one holder
```

Therefore:

```text
same holder + same slot + two distinct loaded skills
→ rejected as domain error
```

A new loadout container on `UnitRuntime` is not required.

### 6.3 State refresh provenance

For a mechanism-defined same-source refresh/reapply:

```text
incoming source_skill_slot == existing source_skill_slot
→ refresh may proceed

incoming source_skill_slot != existing source_skill_slot
→ DOMAIN ERROR
→ no silent provenance overwrite
```

For a P0-required slot comparator, a missing required slot is also a domain error. `None` remains legal only for explicitly non-equipped/system/external/legacy-fixture paths that do not enter a slot-required mechanism.

### 6.4 INV-18

INV-18 is now enforceable through the complete chain:

```text
typed SkillSlot
+ holder-specific producer
+ duplicate-slot rejection
+ EffectSourceRef / StateInstance propagation
+ refresh immutability
+ required-slot missing rejection
+ Cleave effect-major / slot ordering seam
```

```text
R2-M01 verdict            = CLOSED
SkillSlot type/domain     = PASS
holder-specific producer  = PASS
refresh provenance        = PASS
INV-18                    = ENFORCED
```

---

## 7. Future Admission Capability

### 7.1 Global future branches

All six global future branches have an exactly-one gate caller and a permit-consuming construction boundary.

| Future branch | Gate before identity/admission? | Permit-required consumer | Round3 |
|---|---:|---|---|
| `NEXT_ACTION` | YES | legacy dispatch adapter in 9.2, real `ActionScope` factory in 9.6 | PASS |
| `ASSAULT` | YES | `AssaultDispatchPort` | PASS |
| `COMBO_SECOND_NORMAL_ATTACK` | YES | NormalAttack #2 allocation factory | PASS |
| `COUNTER_BATCH` | YES | `CounterSystem.create_batch` | PASS |
| `CHAIN_TRAVERSAL` | YES | `ChainSystem.create_traversal` | PASS |
| `CLEAVE_EFFECT` | YES | `CleaveSystem.create_effect` | PASS |

Required order is always:

```text
FutureAdmissionGate
→ gate-issued FutureAdmissionPermit
→ validate/consume permit
→ only then allocate branch identity / admit work
```

The design explicitly forbids construct-first-ask-later flows.

### 7.2 Structural no-bypass

The Python implementation need not pretend it has language-level sealed constructors, but the design requires all of the practical structural controls requested by Round2:

```text
internal construction/factory boundary
required permit argument
gate-issued permit validation
branch/parent/generation match
one-shot consumption
architecture test scanning all future branch factories
```

Normal production construction therefore cannot “legitimately” bypass the gate.

```text
permit-required global branches = 6/6
gate bypass paths                = 0
```

### 7.3 Already-admitted work

The design correctly does **not** re-query the global gate for:

```text
Counter sibling already in an admitted batch
next slot in an admitted ChainTraversal
next secondary in the current admitted CleaveEffect
pending Share sharer step
planned Distribution participant
other local work already admitted by its operation contract
```

Those use only mechanism-local liveness/P0 execution gates.

```text
R2-M02 verdict = CLOSED
INV-40         = ENFORCED
```

---

## 8. Finalization Result / Projection

### 8.1 `FinalizationResult` sufficiency

The schema contains every fact needed for legacy Engine projection without another victory evaluation:

```text
finalization_id
winner_team_id
reason
rounds_completed
final_troops_snapshot
```

Engine can build a fresh legacy `BattleResult` directly from this value.

### 8.2 Deep immutability

The current legacy `BattleResult` outer dataclass is frozen but its `final_troops` dict is mutable. The repair does not reuse that reference.

It freezes:

```text
final_troops_snapshot: tuple[tuple[str,int], ...]
```

with a deep copy at finalization and a fresh compatibility dict only during Engine projection.

```text
deep immutability verdict = PASS
```

### 8.3 Projection capability

`FinalizationProjectionPermit` is specified as one-shot:

```text
FinalizationResult creation = once
permit issuance             = once
claim                        = once
second claim                 = None
consume                      = once
second consume               = domain/programmer error
```

Engine must consume the permit **before**:

```text
context.ended
context.result
BATTLE_END
BATTLE_ENDED
```

The projection function may not call `VictorySystem`, decide drain completion, issue permits, or create a new finalization result.

### 8.4 Semantic single writer

```text
BattleFinalizationCoordinator
= termination state / latch / FINALIZED / FinalizationResult / projection permit owner

BattleEngine
= permit-backed compatibility projector only
```

This closes the former split-brain risk while preserving the current outer-loop architecture.

```text
R2-M03 verdict                   = CLOSED
FinalizationResult               = PASS
projection permit                = PASS
BATTLE_ENDED exactly-once design = PASS
INV-41                           = ENFORCED
```

---

## 9. Settlement Replay Guard

The Stage9 destructive target settlement path has exactly one permit per `DamageInstanceId`:

```text
issuer   = DamageInstanceCoordinator
consumer = DamageResolutionSystem.settle
```

Required order:

```text
validate request + permit identity
→ atomically consume permit
→ only then TroopSystem.apply_damage
→ then DAMAGE_DEALT / UNIT_DEFEATED facts
```

A second settlement attempt therefore fails before all destructive/observable side effects:

```text
second settle
→ domain/programmer error
→ troop mutation 0
→ DAMAGE_DEALT 0
→ UNIT_DEFEATED 0
→ second settlement result 0
```

Replay protection is structural permit state, not EventBus history.

The historical API remains isolated:

```text
DamageResolutionSystem.resolve(context, DamageRequest)
→ fresh LEGACY_COMPAT operation each call
→ no DamageInstanceId requirement
```

No Stage1-8 caller is retroactively forced into Stage9 identity.

```text
R2-M04 verdict                   = CLOSED
DamageSettlementPermit           = PASS
Stage9 replay-capable paths       = 0
permitted duplicate settlement   = 0
legacy resolve isolation         = PASS
```

---

## 10. Exact Numeric Representation

`ExactRatio` is canonical by contract:

```text
denominator > 0
gcd(|numerator|, denominator) = 1
sign stored in numerator
zero canonical form = 0/1
```

There is no generic:

```text
ExactRatio.from_float(...)
```

Preferred ingress is exact textual/Decimal/integer-percent/basis-point/numerator-denominator data. If a future proven legacy float-only configuration boundary exists, only a named compatibility adapter is allowed, using `Decimal(str(value))` on a **raw loaded scalar**, never a computed float.

Round3 production re-scan found current float coefficients in Stage7/8 damage configuration (`PeriodicDamageStateParams.coefficient`, skill coefficients), but these remain inside the frozen Stage7/8 formula path and are **not** Stage9 exact-ratio inputs. The official state catalog itself does not currently store the Stage9 mechanism ratios.

```text
R2-N01 verdict              = CLOSED
ExactRatio canonicalization = PASS
generic from_float          = ABSENT BY DESIGN
Stage9 computed-float ingress contamination = 0
```

---

## 11. Phase 9.1–9.8 Buildability

Round3 simulated each phase against both the repaired spec and current production seams.

| Phase | Dependencies already available at phase start? | Production switch | Compatibility bridge | Test seam sufficient? | Independently green? |
|---|---:|---|---|---:|---:|
| 9.1 Identity / provenance / exact numeric / permit types | YES, Stage8 frozen baseline | none | Stage1-8 untouched; legacy runtime slot may be None outside slot-required paths | YES | **YES** |
| 9.2 Execution right + legacy finalization | YES, 9.1 types only | six-barrier coordinator + next-Action permit adapter | 6/6 legacy barriers; ACTION projection after UNIT_ACTION_ENDED; fresh BattleResult projection | YES | **YES** |
| 9.3 Target + holder source/slot ingress | YES, real 9.2 infra | holder load path + provenance propagation | legacy/test SkillRuntime still legal outside required slot semantics | YES | **YES** |
| 9.4 Settlement + isolated DamageInstance | YES, 9.3 provenance + 9.2 finalization | no EffectExecutor cutover | legacy resolve/apply full settlement remains | YES | **YES** |
| 9.5 Partition/direct loss + DamageEffect cutover | YES, 9.4 settlement + 9.3 source refs + 9.2 finalization | EffectExecutor -> DamageInstanceCoordinator only at phase end | narrow DamageEffectResult compatibility; legacy direct APIs retained | YES | **YES** |
| 9.6 NormalAttack master + Combo/Assault | YES, complete 9.5 route | thin NormalAttack master + real ActionScope | same Stage8 damage semantics/events; NEXT_ACTION permit contract retained | YES | **YES** |
| 9.7 Cleave/Chain/Counter | YES, real Action/NA scopes + prior infra | mechanism services/factories | already-admitted work remains local and is not globally re-gated | YES | **YES** |
| 9.8 Integration closure | YES, all services real | none | all pre-Stage9 tests/semantics remain required | YES | **YES** |

```text
phase independently-green failures = 0
forward production dependencies     = 0
```

### Phase 9.5 cutover verdict

Before the production reroute, the design requires all of the following to be real:

```text
all production DamageEffect source refs classified
SkillResolver ACTIVE_SKILL ingress
TriggerSystem PERIODIC_DAMAGE ingress
partition path
DirectTroopLoss path
one-shot target settlement
finalization/execution-right infrastructure
EffectSourceRef -> OperationLineage conversion
```

All prerequisites are owned by phases 9.1–9.4 or the Phase 9.5 pre-cutover tasks. No missing later-phase dependency is required.

```text
Phase 9.5 cutover verdict = PASS / BUILDABLE
```

---

## 12. NormalAttack Ownership

The repaired design keeps `NormalAttackSystem` intentionally narrow.

It owns:

```text
normal-attack lifecycle ordering
NormalAttackInstanceId
component orchestration
NA-local result assembly
assigned future-branch admission call sites
```

It explicitly does **not** own:

```text
target-selection algorithm
Guard algorithm internals
partition math
state storage mutation
Cleave internals
Chain internals
Counter internals
Stage8 formula semantics
finalization state
```

This is compatible with the current production entry point and does not create a God Object.

```text
NormalAttack ownership verdict = PASS
```

---

## 13. Partition / DirectTroopLoss

The damage layers remain typed and non-aliased:

```text
Dtotal                  = DamageResult.final_damage
Dtarget                 = DamageSettlementRequest.assigned_target_damage
ActualTargetTroopLoss   = DamageResolutionResult.actual_target_troop_loss
AttributedDirectTroopLoss = separate direct-loss operation/result
```

Exactly one partition policy applies to a standard DamageEvent:

```text
NONE | SHARE | DISTRIBUTION
```

Share/Distribution direct loss is not a normal DamageEvent and does not enter:

```text
DamageSystem
HitResolution
base formula
Counter
Chain
Share/Distribution recursion
FirstAid/generic Hurt callbacks
```

Critically, `DirectTroopLossResolver` does **not** send direct loss into `DamageCallbackAdmissionPoint`. Thus:

```text
Share/Distribution direct loss
-X-> Chain admission
```

The shared damage-callback admission seam is reserved for damage facts that are P0-eligible for that callback family.

```text
partition/direct-loss verdict = PASS
```

---

## 14. Cleave / Chain / Counter

### Cleave

```text
base fact        = ActualTargetTroopLoss
integerization   = exact FLOOR
normal-attack ID = false
secondary plan   = admitted-effect local work
new effect       = FutureAdmissionPermit required
```

Cleave does not rerun the Stage8 base formula/modifier/Crit pipeline.

### Chain

```text
new traversal    = shared DamageCallbackAdmissionPoint -> FutureAdmissionPermit
cursor            = monotonic fixed global slot order
trigger snapshot  = immutable trigger facts only
execution fields  = live-read where P0 requires
TRUE_FEEDBACK     = restricted settlement, not Stage8 DamageRequest
```

`ChainSystem` cannot self-admit a traversal.

### Counter

```text
CounterBatch membership = immutable after admission
owner liveness          = separate local execution gate
positive live target    = legitimate standard DamageInstance path
dead-target sibling     = explicit zero-loss terminal, no fake Stage8 pipeline
new CounterBatch        = FutureAdmissionPermit required
```

All three mechanisms consume prior infrastructure and introduce no new global orchestration owner.

```text
Cleave / Chain / Counter verdict = PASS
```

---

## 15. Permission / Admission / Local Gate

The repaired design preserves three distinct layers:

```text
ReactionPermissionPolicy
→ is this reaction family semantically allowed for this source identity?

FutureAdmissionGate
→ may a NEW global future branch be admitted now?

Local execution gate
→ may already-admitted work execute now under its mechanism liveness/P0 rule?
```

No layer is merged with another.

Examples confirm the distinction:

```text
Counter sibling: already admitted -> local owner/target gate only
Chain next slot: already admitted -> local traversal liveness only
Cleave current secondary: already admitted -> local JIT liveness only
new Chain traversal: permission may allow family, but FutureAdmissionGate still controls admission
```

```text
three-layer separation verdict = PASS
```

---

## 16. Invariant Recheck

Round3 rechecked all 42 RF-C01 invariants against the repaired API/ownership surfaces rather than accepting the Round2 repair summary as authority.

| Invariant | Round3 enforcement seam | Verdict |
|---|---|---|
| INV-01 | immutable intended/actual target fields | ENFORCED |
| INV-02 | selector pipeline structurally before Guard | ENFORCED |
| INV-03 | per-NA single Guard pass assertion | ENFORCED |
| INV-04 | downstream contracts consume actual target | ENFORCED |
| INV-05 | concrete settlement owns damage recipient | ENFORCED |
| INV-06 | Combo #2 allocates fresh NA/target resolution | ENFORCED |
| INV-07 | physical/operational/grant types separated | ENFORCED |
| INV-08 | ActionStart maintenance before grant | ENFORCED |
| INV-09 | explicit grant transition distinguishes remove/suppress | ENFORCED |
| INV-10 | checkpoint ceiling per Action | ENFORCED |
| INV-11 | atomic consume/cfg230 ceiling | ENFORCED |
| INV-12 | physical NA count <= 2 | ENFORCED |
| INV-13 | Cleave typed source and no NA identity | ENFORCED |
| INV-14 | Cleave input is ActualTargetTroopLoss | ENFORCED |
| INV-15 | exact FLOOR helper/vector | ENFORCED |
| INV-16 | Cleave resolver has no upstream formula/modifier/Crit edge | ENFORCED |
| INV-17 | typed centralized reaction permission policy | ENFORCED |
| INV-18 | typed SkillSlot + holder load producer + immutable provenance + required-slot rejection | **ENFORCED** |
| INV-19 | direct loss is distinct typed operation | ENFORCED |
| INV-20 | direct loss bypasses HitResolution/callback path | ENFORCED |
| INV-21 | explicit direct-loss provenance | ENFORCED |
| INV-22 | exactly-one partition assertion | ENFORCED |
| INV-23 | replacement lifecycle cannot resurrect displaced instance | ENFORCED |
| INV-24 | Share target-first structure | ENFORCED |
| INV-25 | lethal target local interrupt discards pending sharer | ENFORCED |
| INV-26 | theoretical/assigned/actual/credit facts typed separately | ENFORCED |
| INV-27 | frozen Distribution participants/N | ENFORCED |
| INV-28 | frozen Distribution calculated amounts | ENFORCED |
| INV-29 | invalid planned participant = skip only | ENFORCED |
| INV-30 | no post-plan participant append/replan | ENFORCED |
| INV-31 | DSTS9-B02 isolated labeled Distribution local default | ENFORCED |
| INV-32 | typed deferred Chain trigger snapshot | ENFORCED |
| INV-33 | execution-time Chain live lookup | ENFORCED |
| INV-34 | monotonic one-pass Chain cursor | ENFORCED |
| INV-35 | restricted Chain feedback settlement | ENFORCED |
| INV-36 | immutable CounterBatch entries | ENFORCED |
| INV-37 | global admission and local liveness gates separate | ENFORCED |
| INV-38 | explicit Counter dead-target zero terminal | ENFORCED |
| INV-39 | UnitDeathFact / VictoryLatched / Finalized separated | ENFORCED |
| INV-40 | single gate + one-shot permit + permit-required factories + no-bypass test | **ENFORCED** |
| INV-41 | coordinator unique semantic finalization owner; Engine projection only | **ENFORCED** |
| INV-42 | authoritative EffectSourceRef producers + no reverse inference + lineage mapping | **ENFORCED** |

```text
TOTAL      = 42
ENFORCED   = 42
UNENFORCED = 0
```

This is a **design-enforceability** verdict. It does not claim Stage9 production code or tests already exist.

---

## 17. Regression Testability

The 45 frozen gameplay regression contracts were rechecked for reachable test seams after the Round2 repairs.

| Group | Contracts | Testable | Blocking gap |
|---|---:|---:|---:|
| Target arbitration | 7 | 7 | 0 |
| Combo | 5 | 5 | 0 |
| Cleave | 5 | 5 | 0 |
| Chain | 4 | 4 | 0 |
| Share | 4 | 4 | 0 |
| Distribution | 4 | 4 | 0 |
| Counter | 5 | 5 | 0 |
| Finalization | 6 | 6 | 0 |
| Integerization | 5 | 5 | 0 |
| **TOTAL** | **45** | **45** | **0** |

The repaired APIs expose the previously missing seams needed to test:

```text
source skill slot / immutable provenance
FutureAdmission gate/no-bypass
finalization latch/drain/projection exactly once
settlement replay rejection
SourceType producer identity
Dtotal != Dtarget != ActualTargetTroopLoss
```

```text
mapped      = 45
 testable   = 45
unmapped    = 0
untestable  = 0
conflicting = 0
```

---

## 18. Architecture Test Matrix

| Architecture guarantee | Planned test | Ready? |
|---|---|---:|
| no Stage8 semantic/import inversion | assert Stage8 calculation modules do not import Stage9 mechanism services | **READY** |
| FutureAdmission no bypass | inspect every global future-branch factory/adapter; construction requires a valid gate-issued permit | **READY** |
| finalization single semantic writer | only coordinator may mutate termination/finalization semantic state | **READY** |
| Engine projection exactly once | repeated claim/consume cannot produce second BATTLE_END/BATTLE_ENDED | **READY** |
| OperationId never gameplay ordering | static/source test forbids operation/permit IDs in gameplay comparators | **READY** |
| StateRegistry sole storage | no second physical state container | **READY** |
| StateLifecycleSystem sole mutation | no direct state add/remove outside lifecycle owner | **READY** |
| EventBus facts-only | no subscriber is required for Stage9 orchestration/finalization/admission | **READY** |
| BattleSystems composition root | all services constructed/injected there; BattleContext is not a service locator | **READY** |
| settlement one-shot | second Stage9 settle with same request/permit fails before troop/event effects | **READY** |
| EffectExecutor Stage9 SourceType | actual SkillResolver/TriggerSystem producers supply source refs; no reverse enum mapping | **READY** |
| source_skill_slot ingress / immutability | typed slot domain, holder producer, duplicate-slot rejection, refresh mismatch rejection | **READY** |

```text
Architecture tests READY   = 12
Architecture tests BLOCKED = 0
```

The five architecture guarantees that were blocked in Round2 are now independently testable:

```text
FutureAdmission no bypass                       READY
Engine final projection exactly once             READY
Settlement one shot                              READY
EffectExecutor authoritative Stage9 SourceType   READY
source_skill_slot ingress / immutability         READY
```

---

## 19. File Plan

Round3 recomputed the file plan from current source ownership and the repaired dependency graph rather than inheriting the repair counts.

### 19.1 NEW production files — 16

```text
operation_identity.py
stage9_trace.py
stage9_integerization.py
stage9_state_params.py
stage9_state_runtime.py
target_resolution_system.py
reaction_permission_policy.py
execution_right_system.py
damage_instance_coordinator.py
damage_partition_system.py
direct_troop_loss_system.py
cleave_derived_damage_system.py
cleave_system.py
chain_system.py
counter_system.py
battle_finalization_coordinator.py
```

Each file has a distinct semantic owner; no required owner is missing and no listed file exists solely to hide a small type that belongs naturally in an existing module.

### 19.2 MODIFY production files — 17

```text
context.py
battle_systems.py
engine.py
action_system.py
normal_attack_system.py
damage_resolution_system.py
effect_executor.py
effect_result.py
skill_runtime.py
skill_resolver.py
effects.py
state_instance.py
state_lifecycle_system.py
official_state_catalog.py
events.py
trigger_system.py
__init__.py
```

`trigger_system.py` is correctly **MODIFY**, not KEEP, because it is the authoritative periodic `PERIODIC_DAMAGE` `EffectSourceRef` producer.

### 19.3 KEEP / CALL

```text
victory_system.py
state_registry.py
skill_definition.py
target_system.py
troop_system.py
attribute_system.py
random_system.py
recovery_system.py
rule_hook_system.py
unit.py
```

`rule_hook_system.py` remains KEEP because it routes effects and does not construct provenance.

### 19.4 DO NOT TOUCH Stage8 semantics

```text
damage_system.py calculation semantics
damage_prevention_system.py
hit_resolution_system.py semantics
damage_formula_policy_system.py
damage_modifier_system.py
weapon_damage_formula.py
strategy_damage_formula.py
damage_pipeline_trace.py meaning
DamageResult.final_damage meaning
```

```text
planned NEW       = 16
planned MODIFY    = 17
missing files     = 0
unnecessary files = 0
```

---

## 20. Dependency / Composition Root

The repaired dependency graph remains acyclic in the required direction.

Key direction checks:

```text
BattleEngine -> BattleFinalizationCoordinator -> VictorySystem
EffectExecutor -> DamageInstanceCoordinator
DamageInstanceCoordinator -X-> EffectExecutor
DamageCallbackAdmissionPoint -> FutureAdmissionGate
ChainSystem -X-> self-admit traversal
BattleFinalizationCoordinator -X-> BattleEngine
```

`BattleSystems` remains the one service composition root. There is no global singleton and no mechanism service self-constructs its dependency graph.

`BattleContext` additions remain bounded to:

```text
OperationIdAllocator
small termination record/read state
```

It must not hold:

```text
BattleSystems
mechanism systems
policies
permit managers
trace service
mechanism queues/runtime bags
battle-long consumed permit histories
```

`EventBus` remains facts-only. No admission, orchestration, mutation, or finalization correctness depends on subscriber order.

```text
dependency cycles               = 0
forward production dependencies = 0
composition root verdict        = PASS
BattleContext boundary          = PASS
EventBus boundary               = PASS
```

---

## 21. Stage8 Boundary

Round3 confirms the repaired design does not reopen Stage8.

Permanent contract:

```text
DamageResult.final_damage = Dtotal
```

Stage9 only adds:

```text
typed settlement request carrying Dtarget
partition planning
derived/direct troop-loss paths
operation orchestration
finalization/admission capability guards
```

It does not alter:

```text
base formulas
HitResolution semantics
DamagePrevention semantics
modifier ownership
DamagePipelineTrace semantics
Stage8 DamageRequest formula identity
```

`DamageResolutionSystem` is modified only at the settlement seam; `DamageSystem.calculate()` remains the theoretical-damage owner.

```text
P0 semantic conflicts = 0
Stage8 reopen          = 0
Stage8 boundary        = PASS
```

---

## 22. Research Debt Isolation

`DSTS9-B02` remains:

```text
EMPIRICAL: OPEN / UNOBSERVED
RUNTIME: CLOSED BY PROJECT_RUNTIME_DEFAULT
DESIGN: NOT BLOCKING
RESEARCH DEBT: YES
```

Round3 confirms that the default appears only in Distribution's local continuation policy for an already-admitted fixed transaction.

It does **not** leak into:

```text
BattleFinalizationCoordinator
FutureAdmissionGate
DamageSettlementPermit
FinalizationProjectionPermit
generic operation identity/lineage
standard settlement
```

No research debt was promoted into a generic runtime rule.

```text
research debt isolation verdict = PASS
```

---

## 23. Findings

Round3 found no remaining or newly introduced implementation-semantic defect.

```text
BLOCKER = 0
MAJOR   = 0
MINOR   = 0
DOC_ONLY= 0
```

No finding is being suppressed as “style”. Conversely, no class-name/file-layout preference is being manufactured into a finding merely to keep the audit alive.

---

## 24. Final Gate

```text
BLOCKER = 0
MAJOR   = 0
MINOR   = 0
DOC_ONLY= 0

P0 semantic conflict = 0
Stage8 reopen        = 0

dependency cycle              = 0
forward production dependency = 0

unowned runtime facts       = 0
unspecified reachable paths = 0

unenforced invariants   = 0
untestable regressions  = 0
blocked architecture tests = 0
phase independently-green failures = 0

legacy barriers verified       = 6/6
production DamageEffect producers = 2
unclassified producer             = 0
future permit-required branches   = 6/6
gate bypass paths                 = 0
Stage9 settlement replay paths    = 0

42 invariants enforced/design-enforceable = 42/42
45 regressions mapped/testable             = 45/45
architecture tests READY                   = 12/12
architecture tests BLOCKED                 = 0

planned NEW production files    = 16
planned MODIFY production files = 17
missing files                   = 0
unnecessary files               = 0
```

All pure-PASS admission conditions are satisfied.

---

## 25. Verdict

# PASS

```text
DESIGN FREEZE ADMISSION = ELIGIBLE
```

This report does **not** execute Design Freeze.

It does **not** change `STAGE9.md` from:

```text
STATUS                   = DRAFT — DESIGN AUDIT REQUIRED
Stage9 FROZEN            = NO
Ready for implementation = NO
```

The next permitted step is exactly:

# Stage9 Design Freeze

No production implementation, Build Prompt authoring, or Stage9 freeze declaration is authorized by any action inside this Round3 audit itself.
