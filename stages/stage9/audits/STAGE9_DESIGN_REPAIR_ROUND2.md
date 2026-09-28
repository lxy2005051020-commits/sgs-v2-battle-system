# Stage9 Design Repair Round 2

> Repair baseline (battle): `fbeca591fd9d5df014035a5aa643f15bb5389c68`  
> State authority baseline: `15ed915435f328a6ecd8f488d98b5b9e13c913b5`  
> Date: 2026-09-13  
> Scope: **IMPLEMENTATION SPEC DESIGN REPAIR ONLY**  
> Production code/tests/Stage8/state authority changes: **FORBIDDEN**

---

## 1. Baseline

Before repair, both remote `main` heads were re-read and verified:

```text
battle:
fbeca591fd9d5df014035a5aa643f15bb5389c68
audit(stage9): complete design audit round 2

state:
15ed915435f328a6ecd8f488d98b5b9e13c913b5
docs(combo): close stale CBS9-B03 status banner
```

The state repository was treated as read-only throughout this repair.

Files fully re-read before design changes:

```text
stages/stage9/STAGE9.md
stages/stage9/audits/STAGE9_DESIGN_AUDIT_ROUND1.md
stages/stage9/audits/STAGE9_DESIGN_REPAIR_ROUND1.md
stages/stage9/audits/STAGE9_DESIGN_AUDIT_ROUND2.md
```

Relevant production surfaces re-read included:

```text
BattleEngine / BattleContext / BattleSystems / VictorySystem
DamageSystem / DamageResolutionSystem / DamageResult / DamageResolutionResult
EffectExecutor / DamageEffectResult / effects.py / effect_result.py
SkillRuntime / SkillResolver / SkillDefinition
TriggerSystem / RuleHookSystem
StateInstance / StateLifecycleSystem / StateRegistry
ActionSystem / NormalAttackSystem / TroopSystem / EventBus
UnitRuntime
```

No gameplay research or battle-report research was performed.

---

## 2. Round2 Findings

Round2 input findings were taken only from `STAGE9_DESIGN_AUDIT_ROUND2.md`:

```text
BLOCKER
R2-B01
R2-B02

MAJOR
R2-M01
R2-M02
R2-M03
R2-M04

MINOR
R2-N01
R2-N02
```

Pre-repair gate:

```text
BLOCKER = 2
MAJOR = 4
MINOR = 2
DOC_ONLY = 0

P0 conflict = 0
Stage8 reopen = NO

Unenforced invariants = 3
INV-18
INV-40
INV-42

Architecture tests = 7 READY / 5 BLOCKED
```

The repair order was preserved: B01 -> B02 -> M01/N02 -> M02 -> M03 -> M04 -> N01 -> phase revalidation.

---

## 3. R2-B01 Legacy Finalization Bridge

### 3.1 Production call-site scan

Current `BattleEngine.run()` has exactly six terminal evaluation checkpoints:

1. initial `VictorySystem.check` after `BATTLE_STARTED`;
2. `VictorySystem.check` after RoundStart expiry/event/hook processing;
3. `VictorySystem.check` after UnitActionStart event/hook processing;
4. `VictorySystem.check` immediately after `ActionSystem.execute` and before `UNIT_ACTION_END` publication;
5. `VictorySystem.check` after `ROUND_ENDED` and RoundEnd expiry;
6. `VictorySystem.resolve_max_rounds` after the final round loop.

No current hook-after or max-round checkpoint is omitted.

### 3.2 LEGACY_FINALIZATION_BARRIER_MATRIX

| Existing barrier | Current location | Current evaluation timing | Phase 9.2 adapter | Ordering preserved? |
|---|---|---|---|---|
| `INITIAL_SETTLED` | after PRE_BATTLE + `BATTLE_STARTED` | before round 1 | coordinator observes barrier and calls `VictorySystem.check` | YES |
| `ROUND_START_HOOKS_SETTLED` | after RoundStart expiry/event/hook | after hook completion | same timing through coordinator | YES |
| `UNIT_ACTION_START_HOOKS_SETTLED` | after UnitActionStart event/hook | before Action execution | same timing through coordinator | YES |
| `ACTION_SETTLED` | after `ActionSystem.execute` | before UNIT_ACTION_END | coordinator observes/latches at same point; Engine projection remains after `UNIT_ACTION_ENDED` | YES |
| `ROUND_END_SETTLED` | after `ROUND_ENDED` + expiry | existing round-end check | same timing through coordinator | YES |
| `MAX_ROUND_SETTLED` | after max-round loop | `resolve_max_rounds` | coordinator invokes max-round evaluator once | YES |

```text
mapped terminal checkpoints = 6/6
unmapped = 0
```

### 3.3 Legacy barrier contract

`LegacyFinalizationBarrier` is a typed engineering signal meaning:

> legacy synchronous work for this macro checkpoint has settled and finalization may safely observe world state.

It is not an EventBus gameplay fact and cannot:

```text
set context.ended
set context.result
enter BATTLE_END
publish BATTLE_ENDED
own gameplay victory rules
```

### 3.4 Phase 9.2 compatibility path

```text
BattleEngine reaches existing barrier
→ BattleFinalizationCoordinator.observe_legacy_barrier
→ VictorySystem pure evaluation
→ no victory: continue
→ victory: latch
→ Phase 9.2 admitted Stage9 operation set is empty
→ FINALIZED immediately
→ deep-immutable FinalizationResult created once
→ Engine claims one FinalizationProjectionPermit
→ Engine consumes permit
→ Engine performs legacy compatibility projection once
```

For `ACTION_SETTLED`, evaluation remains before UnitActionEnd exactly as production does today, while projection remains after `UNIT_ACTION_ENDED`, preserving observable event order.

Phase 9.2 requires **zero** ActionScope/DamageInstance/ReactionBatch stubs.

```text
Phase 9.2 independently green = YES
Stage1-8 termination behavior preserved = YES
```

After later Stage9 scopes exist, legacy macro barriers remain finalization opportunities, but a latched victory with admitted work enters `DRAINING_ADMITTED_WORK` until the real operation barrier clears.

---

## 4. R2-B02 Stage9 SourceType Ingress

### 4.1 Separation retained

```text
DamageSourceType = Stage8 formula classification
SourceType       = Stage9 provenance / permission identity
```

Reverse inference is forbidden.

### 4.2 Production DamageEffect producer scan

The production package has two authoritative `DamageEffect` construction sites:

| Producer | Semantic origin | Stage8 classification | Stage9 source producer | Slot source |
|---|---|---|---|---|
| `SkillResolver._build_effect` | active skill | `DamageSourceType.SKILL` | `SourceType.ACTIVE_SKILL` created by resolver | loaded runtime / `LoadedSkillRef.skill_slot` |
| `TriggerSystem._effects_for_state` | periodic state damage | `DamageSourceType.CONTINUOUS` | `SourceType.PERIODIC_DAMAGE` created by trigger system | preserved `StateInstance.source_skill_slot` |

`RuleHookSystem` is not a producer; it only routes TriggerSystem effects to EffectExecutor.

`NormalAttackSystem` currently constructs `DamageRequest` directly, not `DamageEffect`; its Stage9 source identity is produced at the NormalAttack/DamageInstance ingress as `SourceType.NORMAL_ATTACK`.

### 4.3 Phase 9.5 cutover gate

Before `EffectExecutor -> DamageInstanceCoordinator` becomes a production route:

```text
every production DamageEffect has authoritative EffectSourceRef
active skill producer emits ACTIVE_SKILL directly
periodic producer emits PERIODIC_DAMAGE directly
no reverse DamageSourceType mapping exists
all source refs preserve attribution
EffectExecutor invents no provenance
TriggerSystem periodic ingress is implemented
unclassified production DamageEffect = 0
```

---

## 5. R2-M01 SkillSlot Contract

### 5.1 Typed domain

```python
class SkillSlot(IntEnum):
    INHERENT  = 0
    LEARNED_1 = 1
    LEARNED_2 = 2
```

```text
index convention = 0-based
legal domain = {0,1,2}
```

`SkillDefinition` remains static and slot-free.

### 5.2 Concrete holder-specific producer

Production inspection confirmed:

```text
SkillRuntime currently = definition + owner_id + enabled
UnitRuntime has no skill/loadout collection
existing holder-specific loadout object = NONE
```

Therefore the minimal Phase 9.3 construction surface is placed in `skill_runtime.py`:

```python
LoadedSkillRef(owner_id, definition, skill_slot: SkillSlot)
LoadedSkillSet(owner_id, loaded: tuple[LoadedSkillRef, ...])
SkillRuntime.from_loaded(ref, enabled=True)
```

`LoadedSkillSet` rejects duplicate slots for one holder. This makes two distinct production-loaded skills for one holder at the same `SkillSlot` structurally invalid.

### 5.3 None policy

`SkillRuntime.skill_slot: SkillSlot | None` permits system/external/non-equipped/legacy-fixture provenance.

Any P0-required slot-order mechanism receiving `None` fails fast unless its P0 explicitly defines an alternate comparator.

### 5.4 Refresh/reapply provenance

For a mechanism whose P0 refreshes an existing same-source state:

```text
same-source key = owner_id + state_id + source_id + source_skill_id
```

The incoming slot must equal the frozen existing slot. A mismatch is a domain error; the existing slot is never silently overwritten.

A mechanism that legitimately creates another instance instead of refreshing keeps separate immutable instance provenance.

### 5.5 StateInstance persistence

Persist only durable source metadata:

```text
source_id
source_skill_id
source_skill_slot
```

Do not persist transient ActionId/DamageInstanceId solely for convenience.

---

## 6. R2-M02 Future Admission Capabilities

### 6.1 FutureAdmissionPermit

```python
FutureAdmissionPermit(
    permit_id,
    branch_kind,
    parent_scope_identity,
    termination_generation,
)
```

It is one-shot, engineering-only, never a gameplay ordering key, and is consumed immediately at branch construction/admission.

### 6.2 Permit-required global future branches

```text
NEXT_ACTION
ASSAULT
COMBO_SECOND_NORMAL_ATTACK
COUNTER_BATCH
CHAIN_TRAVERSAL
CLEAVE_EFFECT
```

No production branch may allocate its future operation identity before permit approval/consume.

### 6.3 Caller matrix

```text
next Action   -> BattleEngine
Assault       -> NormalAttackSystem
Combo #2      -> Combo checkpoint
CounterBatch  -> NormalAttack post-hit admission point
ChainTraversal-> DamageCallbackAdmissionPoint
CleaveEffect  -> Cleave effect-loop boundary
```

### 6.4 Already-admitted work

No new global permit is required for:

```text
Counter sibling
next slot in current Chain traversal
secondary in current Cleave effect
pending Share sharer local step
planned Distribution participant
```

These are covered by the parent admitted scope and only run local execution/liveness gates.

### 6.5 INV-40 closure

```text
single FutureAdmissionGate
+ one-shot typed permit
+ permit-required constructors/factories
+ caller matrix
+ architecture no-bypass test
```

Gate bypass count after design repair: `0`.

---

## 7. R2-M03 Finalization Result / Projection

### 7.1 Deep-immutable FinalizationResult

The current legacy `BattleResult` cannot be embedded directly because `final_troops` is a mutable dict.

Frozen Stage9 result:

```python
FinalizationResult(
    finalization_id,
    winner_team_id,
    reason,
    rounds_completed,
    final_troops_snapshot: tuple[tuple[str, int], ...],
)
```

Snapshot policy:

```text
deep copy live troop values
canonical tuple sorted by stable unit_id for snapshot serialization only
no mutable reference reachable from FinalizationResult
```

Legacy `BattleResult` is reconstructed as a fresh data projection. Projection never calls VictorySystem again.

### 7.2 FinalizationProjectionPermit

Coordinator is the only issuer/validator:

```text
FinalizationResult creation = once
projection permit claim = once
projection permit consume = once
second claim = None
second consume = domain error
```

Engine consumes the permit before writing:

```text
context.ended
context.result
BATTLE_END phase
BATTLE_ENDED event
```

Thus those compatibility side effects happen exactly once even when multiple death/barrier/completion facts all call finalization attempts.

### 7.3 INV-41 strengthening

INV-41 was already considered structurally covered in Round2, but this repair strengthens the mechanism:

```text
Coordinator = termination writer + final result creator + projection permit issuer
Engine      = permit consumer + compatibility projector only
```

No coordinator -> Engine call edge is introduced.

---

## 8. R2-M04 Settlement Replay Guard

### 8.1 DamageSettlementPermit

One permit is issued per Stage9 `DamageInstanceId` by `DamageInstanceCoordinator`.

`DamageResolutionSystem.settle` validates and atomically consumes it **before** calling `TroopSystem.apply_damage`.

Required identity check:

```text
permit.damage_instance_id == request.damage_instance_id
```

Replay/mismatch is a domain/programmer error.

### 8.2 Replay outcome

```text
first settlement
→ troop mutation once
→ DAMAGE_DEALT once
→ possible UNIT_DEFEATED once

same permit/request again
→ rejected
→ no troop mutation
→ no second event
```

EventBus history is never used as the replay guard.

### 8.3 Legacy compatibility

Legacy `resolve()` remains a distinct historical API. Every call is a new `LEGACY_COMPAT` operation and is not subjected to Stage9 DamageInstance replay identity.

### 8.4 Permit lifecycle

Consumed permit state is operation-local and releasable after DamageInstance settlement/completion. No unbounded battle-long consumed-ID set is added to BattleContext.

---

## 9. ExactRatio Tightening

Canonicalization:

```text
denominator > 0
gcd reduced
sign normalized to numerator
zero canonical = 0/1
```

Examples:

```text
54/100   -> 27/50
27/50    -> 27/50
540/1000 -> 27/50
0/100    -> 0/1
```

Stage9 core exposes no generic `ExactRatio.from_float()`.

Preferred ingress:

```text
raw text
Decimal
integer percent/basis points
exact numerator/denominator
```

Current design/code scan found no Stage9 ratio that is forced to originate through a float-only compatibility surface, so no float adapter is required now.

If a future named legacy raw-float boundary is proven, only a specifically named compatibility adapter may use `Decimal(str(value))`; computed floats are forbidden and prior precision loss cannot be recovered.

---

## 10. EffectSourceRef

Canonical narrow value in `effects.py`:

```python
EffectSourceRef(
    stage9_source_type: SourceType,
    source_unit_id: str | None,
    source_skill_id: str | None,
    source_skill_slot: SkillSlot | None,
)
```

This removes four correlated source facts from being independently invented at each Effect call site.

`EffectSourceRef` and `OperationLineage` are intentionally distinct:

```text
EffectSourceRef = creation/application provenance, valid before Stage9 operation IDs
OperationLineage = execution ancestry, created when runtime operation scope exists
```

DamageInstanceCoordinator combines source ref with current parent scope to build lineage.

---

## 11. Phase Plan Revalidation

| Phase | Prerequisites | New production switch | Compatibility bridge | Key exit gate | Independently green? |
|---|---|---|---|---|---|
| 9.1 | Stage8 frozen | none | Stage1-8 untouched | SkillSlot/ExactRatio/EffectSourceRef/permit types/source matrix frozen | YES |
| 9.2 | 9.1 | coordinator owns six legacy finalization barriers; next-Action gate via legacy permit adapter | no Stage9 operation scopes; legacy events/results unchanged | 6/6 barriers, deep immutable result, one-shot projection | **YES** |
| 9.3 | 9.2 | holder-specific LoadedSkill ingress + source/slot propagation + target resolution | legacy no-slot fixture allowed outside required slot mechanisms | INV-18 closed; target result immutable | YES |
| 9.4 | 9.3 | isolated DamageInstance only | legacy resolve/apply_result preserved | one-shot settlement + Dtotal/Dtarget/actual | YES |
| 9.5 | 9.4 | EffectExecutor production cutover after full source/partition gate | narrow result compatibility | source coverage 100%, unclassified=0, Trigger periodic ingress real | **YES** |
| 9.6 | 9.5 | real Action/NA master + Combo/Assault permit consumers | Phase 9.2 NEXT_ACTION permit contract retained | Action/Assault/Combo no bypass | YES |
| 9.7 | 9.6 | Cleave/Chain/Counter + remaining permit consumers | admitted local work stays local | all branch families structurally gated | YES |
| 9.8 | 9.7 | none | all historical tests stay green | 42/42 + 45/45 + 12/12 | YES |

No phase requires a production call into a later-phase stub/TODO owner.

---

## 12. Invariant Re-coverage

Round2 exact unenforced set:

```text
INV-18
INV-40
INV-42
```

Closure:

```text
INV-18
→ typed SkillSlot
→ concrete LoadedSkillRef/LoadedSkillSet producer
→ immutable reapply slot guard
→ P0-required missing-slot rejection
→ duplicate same-holder same-slot loadout rejection

INV-40
→ single FutureAdmissionGate
→ FutureAdmissionPermit
→ permit-required future branch factories
→ no-bypass architecture test

INV-42
→ EffectSourceRef
→ authoritative ACTIVE_SKILL/PERIODIC_DAMAGE producers
→ no reverse DamageSourceType inference
→ runtime OperationLineage / permission mapping
```

Final invariant gate:

```text
42 total
42 enforced
0 unenforced
0 test-only
```

---

## 13. Architecture Test Readiness

Round2 had `7 READY / 5 BLOCKED`.

The five previously blocked tests are now design-ready:

| Previously blocked test | Repair |
|---|---|
| FutureAdmission no bypass | permit-required factories + one gate |
| Engine projection exactly once | FinalizationProjectionPermit claim/consume |
| Settlement one shot | DamageSettlementPermit atomic pre-mutation consume |
| EffectExecutor Stage9 SourceType | EffectSourceRef + producer matrix + no reverse inference |
| source_skill_slot ingress/immutability | typed SkillSlot + LoadedSkill producer + reapply guard |

Final readiness:

```text
Architecture tests READY   = 12/12
Architecture tests BLOCKED = 0
```

---

## 14. File Plan Recalculation

### 14.1 Planned NEW production files

Still `16`.

Small types are colocated with their responsibility owners rather than creating extra one-class modules:

```text
EffectSourceRef -> effects.py
SkillSlot / LoadedSkillRef / LoadedSkillSet -> skill_runtime.py
FutureAdmissionPermit -> execution_right_system.py
DamageSettlementPermit -> settlement/coordinator ownership
FinalizationProjectionPermit -> battle_finalization_coordinator.py
```

### 14.2 Planned MODIFY production files

Round1 plan: `16`.

Round2 repair adds the proven missing producer file:

```text
trigger_system.py = MODIFY
```

Recomputed:

```text
planned MODIFY = 17
```

`rule_hook_system.py` stays `KEEP / CALL` because it constructs no Effect and owns no provenance.

`unit.py` stays KEEP; the minimal holder-specific skill loading surface is owned by `skill_runtime.py`, avoiding an unrelated UnitRuntime loadout redesign.

```text
missing planned production files = 0
unnecessary planned production files = 0
```

---

## 15. Dependency Recheck

Required directions remain acyclic:

```text
BattleEngine -> BattleFinalizationCoordinator -> VictorySystem
BattleEngine -> FutureAdmissionGate / ActionSystem
SkillResolver -> EffectSourceRef
TriggerSystem -> EffectSourceRef
RuleHookSystem -> TriggerSystem -> EffectExecutor
EffectExecutor -> DamageInstanceCoordinator
DamageInstanceCoordinator -> DamageSystem / partition / settlement / direct loss / finalization port
DamageCallbackAdmissionPoint -> FutureAdmissionGate -> Chain permit
```

Forbidden directions include:

```text
Coordinator -> BattleEngine
EffectExecutor -> reverse-infer Stage9 SourceType
DamageInstanceCoordinator -> EffectExecutor
ChainSystem -> self-admit
branch factory -> bypass gate
EventBus subscriber -> orchestration owner
```

```text
dependency cycles = 0
forward production dependencies = 0
```

---

## 16. Stage8 Boundary

No Stage8 gameplay semantic is reopened.

Unchanged meanings include:

```text
DamageRequest
DamageSourceType
DamageResult.final_damage
DamagePipelineTrace
prevention/hit/formula/modifier ownership
base weapon/strategy formulas
```

Stage9 SourceType is additional orchestration provenance and never reinterprets Stage8 classification.

```text
Stage8 reopen = NO
```

---

## 17. Semantic Drift

```text
P0 semantic conflict = 0
P0 semantic change = 0
new gameplay rule = 0
```

The three permit types are explicitly engineering safety mechanisms, not official gameplay concepts.

The new legacy barrier names model existing Engine checkpoints; they do not create new victory moments.

The typed SkillSlot domain models the already-required equipped-position identity; it does not move ordering authority into runtime IDs.

`DSTS9-B02` remains isolated to Distribution local continuation policy and is absent from finalization/permit contracts.

---

## 18. Remaining Findings

Post-repair design gate:

```text
BLOCKER = 0
MAJOR = 0
MINOR = 0
DOC_ONLY = 0

P0 conflict = 0
Stage8 reopen = 0

Unowned runtime facts = 0
Unspecified reachable paths = 0
Unenforced invariants = 0

Architecture tests = 12/12 READY
BLOCKED = 0

Dependency cycles = 0
Forward dependencies = 0
Phase independently-green failures = 0
```

This is a repair verdict only. It is **not** an independent Round3 audit result.

---

## 19. Changed Files

This repair is intentionally documentation-only:

```text
MODIFY  stages/stage9/STAGE9.md
ADD     stages/stage9/audits/STAGE9_DESIGN_REPAIR_ROUND2.md
MODIFY  stages/stage9/README.md
```

Expected repository diff outside those paths:

```text
production diff = 0
tests diff = 0
Stage8 diff = 0
state repository diff = 0
```

---

## 20. Verdict

```text
ROUND2 DESIGN REPAIR COMPLETE — ROUND3 AUDIT REQUIRED
```

`STAGE9.md` remains:

```text
DRAFT — DESIGN AUDIT REQUIRED
Stage9 FROZEN = NO
Ready for implementation = NO
```

No Build Prompt and no Stage9 implementation are admitted by this repair.

```text
NEXT STEP:
Stage9 Design Audit Round 3
```

Round3 must be an independent final repaired-design verification. Only a pure PASS can admit a later, separate Stage9 Design Freeze step.
