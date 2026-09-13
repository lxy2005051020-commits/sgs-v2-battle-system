# Stage9 Design Repair Round 1

> Repair type: IMPLEMENTATION-SPEC REPAIR  
> Target: `stages/stage9/STAGE9.md`  
> Battle repair baseline: `05512d198c9016410ca14be2e40eb0c913cd1b77`  
> State authority baseline: `15ed915435f328a6ecd8f488d98b5b9e13c913b5`  
> State repository mode: **READ ONLY**  
> Repair date: 2026-09-13

## Baseline

Both remote `main` branches were re-read before repair and immediately before commit construction.

```text
battle:
05512d198c9016410ca14be2e40eb0c913cd1b77
audit(stage9): complete design audit round 1

state:
15ed915435f328a6ecd8f488d98b5b9e13c913b5
docs(combo): close stale CBS9-B03 status banner
```

The state authority repository remained read-only. No current P0 conflict requiring a state-side edit was found.

Round1 dependencies were rechecked against current production, including:

```text
DamageResolutionSystem / DamageResolutionResult
DamageEffectResult / EffectExecutor
BattleEngine / BattleContext / BattleSystems / VictorySystem
StateInstance / StateRegistry / StateLifecycleSystem
SkillRuntime / SkillResolver / SkillDefinition / effects.py / effect_result.py
NormalAttackSystem / ActionSystem / TroopSystem / EventBus
DamageSystem / DamageResult
```

## Round1 Findings

Audit input:

```text
BLOCKER = 3
MAJOR = 4
MINOR = 6
DOC_ONLY = 0

Unowned runtime facts          = 1
Unspecified reachable paths    = 5
Unenforced invariants          = 3
Dependency cycles              = 0
Forward production dependency  = 1
```

Repair order was preserved:

```text
P1 BLOCKER: B1 Settlement -> B2 Finalization -> B3 Phase dependency
P2 MAJOR: M1 source slot -> M2 exact numeric -> M3 future admission -> M4 EffectExecutor result
P3 MINOR: N1..N6 cleanup
```

No production code, tests, Stage8 files, P0 authority, battle-report research, or Build Prompt were changed.

## B1 Settlement Repair

### Final model

Round1 freezes **Model A**:

```text
DamageResolutionResult
=
existing result type upgraded into the single settlement result
```

No permanent parallel `Stage9DamageSettlementResult` is introduced.

New typed command:

```python
DamageSettlementRequest(
    damage_result: DamageResult,
    assigned_target_damage: int,
    damage_instance_id: DamageInstanceId | None,
    lineage: OperationLineage | None,
    origin: STAGE9 | LEGACY_COMPAT,
)
```

Rules:

```text
DamageResult.final_damage ALWAYS = Dtotal
assigned_target_damage           = Dtarget
DamageResolutionResult.actual_target_troop_loss = actual clamp loss
DamageResolutionResult.credited_damage          = explicit attribution layer
```

For `STAGE9` origin, DamageInstanceId + lineage are mandatory. For `LEGACY_COMPAT`, they are absent and `assigned_target_damage == damage_result.final_damage` is mandatory.

For ordinary standard target settlement:

```text
credited_damage = actual_target_troop_loss
```

while direct-loss paths retain separate explicit attribution.

### Legacy compatibility

```text
DamageResolutionSystem.resolve(request)
→ calculate
→ typed LEGACY_COMPAT settlement request
→ settle full final_damage
```

Thus legacy Stage1-8 callers keep:

```text
Dtotal == Dtarget
requested settlement == DamageResult.final_damage
```

`apply_result(context, damage)` may remain only as a compatibility wrapper for full settlement. It does not gain an optional/positional assigned amount.

### Event semantics

For `DAMAGE_DEALT`:

```text
requested_damage
=
actual requested amount submitted to TroopSystem
=
Dtarget on Stage9 partitioned paths
```

Consumers needing Dtotal read `DamageResult.final_damage`; consumers needing actual committed loss read `actual_target_troop_loss`.

### Fact matrix

| Layer | Typed owner | Field |
|---|---|---|
| Dtotal | `DamageResult` | `final_damage` |
| Dtarget | `DamageSettlementRequest` | `assigned_target_damage` |
| ActualTargetTroopLoss | `DamageResolutionResult` | `actual_target_troop_loss` |
| CreditedDamage | settlement/direct attribution result | explicit credit field |
| UnitDeathFact | concrete settlement/direct-loss edge | explicit fact |

Result: no semantic-layer field aliasing remains.

## B2 Finalization Ownership Repair

Current production reality is preserved:

```text
VictorySystem = already pure evaluator
BattleEngine._finish() = current terminal side-effect owner
```

Repaired ownership:

```text
BattleFinalizationCoordinator
=
unique termination-state / victory-latch / drain / FINALIZED semantic owner

BattleEngine
=
outer loop + finalized-result compatibility projection owner

VictorySystem
=
pure condition evaluator, KEEP / CALL
```

Unique writers:

| Concern | Writer |
|---|---|
| termination state | `BattleFinalizationCoordinator` |
| victory latch/finalized result | `BattleFinalizationCoordinator` |
| `context.ended` | BattleEngine finalized projection |
| `context.result` | BattleEngine finalized projection |
| `BATTLE_END` phase | BattleEngine finalized projection |
| `BATTLE_ENDED` | BattleEngine finalized projection |

Current `_finish(BattleResult)` is no longer allowed to decide termination. Preferred replacement:

```text
_apply_finalized_battle_result(FinalizationResult)
```

with precondition `termination_state == FINALIZED`.

Dependency direction:

```text
BattleEngine → BattleFinalizationCoordinator → VictorySystem
```

Forbidden:

```text
BattleFinalizationCoordinator → BattleEngine._finish()
```

Existing macro event ordering remains compatible: current RoundStart/action hook barriers remain, `UNIT_ACTION_ENDED` remains before terminal projection on the current action path, and `BATTLE_END/BATTLE_ENDED` occur only after coordinator `FINALIZED`.

## B3 Phase Dependency Repair

Old 9.4 production reroute before 9.7 finalization infrastructure is removed.

New phase order:

```text
9.1 Identity / provenance types / exact numeric utilities
  ↓
9.2 Execution Right + real Finalization infrastructure
  ↓
9.3 Target arbitration + state/source-slot ingress
  ↓
9.4 Typed settlement seam + isolated DamageInstance core
  ↓
9.5 Partition + DirectTroopLoss + EffectExecutor production reroute
  ↓
9.6 NormalAttack orchestration + Combo
  ↓
9.7 Cleave + Chain + Counter
  ↓
9.8 Full integration / 45 regressions
```

Key rule:

```text
foundation before production routing
```

Phase 9.4 builds/tests DamageInstance directly but does not reroute production EffectExecutor. Production reroute occurs only at 9.5 exit, after settlement, partition, direct loss, execution right, and finalization are real services.

Universal phase exit gate:

```text
existing tests green
new phase tests green
no production call points to placeholder/stub/TODO Stage9 service
no production semantic dependency on later phase
```

Recomputed:

```text
phase dependency cycles = 0
forward production dependencies = 0
```

## M1 Source Skill Slot Ingress

### Authoritative producer

`SkillDefinition` remains static and does not own slot.

The authoritative producer/carrier boundary is the holder-specific loaded runtime:

```text
SkillRuntime.skill_slot
```

The production call site constructing the loaded `SkillRuntime` and already knowing equipped position supplies it. No downstream system derives slot from skill id.

### Propagation

```text
SkillRuntime
→ SkillResolver
→ DamageEffect / ApplyStateEffect
→ EffectExecutor
→ StateLifecycleSystem.apply
→ StateInstance.source_skill_slot
→ Stage9StateRuntime
→ Cleave / Counter ordering
```

### No-slot policy

```text
system/external/compat source -> source_skill_slot=None
```

Never use `0`, `999`, hash, or `skill_id` order as a fake slot.

- P0-required skill-slot ordering + missing slot -> domain error.
- Counter comparator areas intentionally left open by P0 may use an isolated `PROJECT_DETERMINISTIC_DEFAULT` fallback.
- Non-slot-dependent mechanisms accept `None`.

This closes INV-18 with explicit type + runtime validation.

## M2 Exact Numeric Representation

Stage9 freezes:

```text
ExactRatio = normalized exact rational (numerator:int, denominator:int>0)
```

Preferred ingress:

```text
raw textual decimal -> Decimal(raw_text) -> exact rational -> ExactRatio
```

Legacy float-only ingress:

```python
Decimal(str(value))
```

Forbidden:

```text
Decimal(float)
Fraction(float)
float multiplication followed by rounding
Python round()
```

Required APIs:

```python
floor_product_int_ratio(base, ratio)
round_half_up_product_int_ratio(base, ratio)
round_half_up_divide_int(numerator, denominator)
```

Scope is Stage9 integerization call sites only. Stage8 float pipeline remains frozen.

## M3 Future Admission Caller Matrix

Exactly one authoritative global-gate caller is frozen for each future branch:

| Future branch | Authoritative caller |
|---|---|
| next Action | `BattleEngine` action dispatch boundary |
| Assault | `NormalAttackSystem` before Assault dispatch |
| Combo #2 | Combo checkpoint before NormalAttack #2 allocation |
| new CounterBatch | NormalAttack post-hit reaction admission point |
| new ChainTraversal | shared `DamageCallbackAdmissionPoint` |
| next unadmitted CleaveEffect | `CleaveSystem` effect-loop boundary |

For Chain, standard `DamageInstanceCoordinator` and `CleaveDerivedDamageResolver` only submit eligible resolved-damage facts to the shared `DamageCallbackAdmissionPoint`; that admission point alone calls the global gate and returns an admitted traversal token. `ChainSystem` cannot self-admit.

Already-admitted local work does not re-query the global gate:

```text
Counter sibling
next slot in admitted Chain traversal
next secondary in current Cleave effect
next planned Distribution participant
Share local pending step
```

No-bypass enforcement is structural: single gate service, branch-specific callers/tokens, local scopes for admitted work, plus architecture assertions around future-branch constructors/allocators.

Remaining future-gate bypass paths: **0**.

## M4 EffectExecutor Result Compatibility

`effect_result.py` is explicitly added to the modified-file plan.

Existing `DamageEffectResult` is upgraded instead of exposing a coordinator aggregate:

```python
DamageEffectResult(
    effect,
    damage_instance_id,
    settlement_result: DamageResolutionResult,
)
```

A read-only compatibility projection `resolution -> settlement_result` may preserve existing callers.

Not exposed:

```text
partition plan
reaction queue
mutable coordinator internals
finalization internals
```

Dependency direction:

```text
EffectExecutor → DamageInstanceCoordinator
not reverse
```

## Minor Cleanup

### N1 selectedTarget

Removed. `intended_attack_target` is the one selector output before Guard. No extra RNG/selection occurs.

### N2 comparator defaults

Authority-silent fallbacks are explicitly labeled:

```text
PROJECT_DETERMINISTIC_DEFAULT
NOT EMPIRICALLY PROVEN
NOT OFFICIAL ORDER
```

Operation IDs are never gameplay ordering keys.

### N3 TargetResolutionId

Retained only as:

```text
TRACE_ONLY SUPPORTING ID
```

It is not a gameplay prerequisite or ordering key.

### N4 DerivedDamage abstraction

Generic `DerivedDamageSystem<T>` is removed. It becomes:

```text
CleaveDerivedDamageResolver
cleave_derived_damage_system.py
```

Chain remains on its own restricted feedback path.

### N5 VictorySystem

```text
VictorySystem = KEEP / CALL
```

No default modification is planned because it is already pure.

### N6 trace lifecycle

```text
production: lightweight / configurable / bounded / battle-scoped
overflow: deterministic drop-oldest ring + dropped-count metadata
tests: full-detail sink
not persisted into gameplay state
not authoritative serialization
never queried for gameplay decisions
```

## Invariant Re-coverage

Previously unenforced:

```text
INV-18
INV-40
INV-41
```

After repair:

```text
INV-18 = TYPE + RUNTIME VALIDATION
INV-40 = STRUCTURAL caller matrix + branch capability/token + architecture no-bypass assertions
INV-41 = STRUCTURAL single termination writer + Engine finalized projection only
```

Recomputed primary categories:

```text
STRUCTURAL        = 18
TYPE-ENFORCED     = 16
RUNTIME ASSERTION = 8
TEST-ONLY         = 0
UNENFORCED        = 0
TOTAL             = 42
```

## Regression Testability Re-check

Mandatory gameplay IDs remain:

```text
45/45 mapped
45/45 testable
new gameplay regression IDs = 0
```

A required supporting fixture must realize:

```text
Dtotal != Dtarget != ActualTargetTroopLoss
```

and prove:

```text
partition reads Dtotal/Dtarget from correct layers
Cleave reads ActualTargetTroopLoss
recovery/stat reads explicit actual/credited layer
DAMAGE_DEALT.requested_damage == Dtarget
```

Finalization tests observe typed:

```text
termination_state
victory_latched
finalized
legacy BATTLE_END/BATTLE_ENDED publication
```

No log-string parsing is required.

Chain wording is frozen as a monotonic ascending slot cursor: once a slot is passed, it is never inspected again; a later higher slot may still become live-eligible before the cursor reaches it.

## File Plan Recalculation

### Planned NEW — 16

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

`DamageCallbackAdmissionPoint` is part of the execution-right/admitted-token contract; it does not require an additional production file.

### Planned MODIFY — 16

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
__init__.py
```

### KEEP / CALL

At minimum:

```text
victory_system.py
state_registry.py
skill_definition.py
target_system.py
troop_system.py
attribute_system.py
random_system.py
recovery_system.py
trigger_system.py
rule_hook_system.py
```

### DO NOT TOUCH Stage8 semantics

Stage8 formula/prevention/hit/modifier/pipeline-trace meanings and `DamageResult.final_damage` semantics remain frozen.

## Dependency Re-check

Authoritative critical directions:

```text
BattleEngine → BattleFinalizationCoordinator → VictorySystem
not reverse

NormalAttackSystem → local mechanism systems
not local mechanisms → NormalAttackSystem lifecycle

EffectExecutor → DamageInstanceCoordinator
not coordinator → executor

CounterSystem → DamageInstanceCoordinator
DamageInstanceCoordinator → settlement/partition/direct-loss/finalization ports
standard + Cleave-derived damage producers → shared DamageCallbackAdmissionPoint
DamageCallbackAdmissionPoint → FutureAdmissionGate
ChainSystem requires admitted token and cannot self-admit
```

`BattleSystems` remains composition root. `BattleContext` may contain only operation ID allocator and a small termination record as new cross-mechanism infrastructure; systems, queues, policies, trace service, and mechanism state are forbidden there.

```text
Dependency cycles = 0
```

## Stage8 Boundary

```text
DamageResult.final_damage = frozen Dtotal
DamageSystem.calculate semantics = unchanged
Damage formula/modifier/prevention/hit ownership = unchanged
Stage9 typed settlement = extension around frozen result
```

```text
Stage8 semantic reopen = 0
```

## Semantic Drift Check

```text
P0 semantic change = 0
new gameplay rule = 0
Stage8 semantic reopen = 0
```

Engineering-only decisions are explicitly labeled `PROJECT_DETERMINISTIC_DEFAULT` where P0 is silent.

## Remaining Findings

After rechecking the repaired implementation spec against all Round1 findings:

```text
BLOCKER = 0
MAJOR = 0
MINOR = 0
DOC_ONLY = 0

Unowned runtime facts           = 0
Unspecified reachable paths     = 0
Unenforced invariants           = 0
Dependency cycles               = 0
Forward production dependency   = 0
Untestable mandatory regression = 0
```

This is a repair verdict only. It is **not** a Round2 audit result.

## Changed Files

This repair commit contains only:

```text
stages/stage9/STAGE9.md
stages/stage9/audits/STAGE9_DESIGN_REPAIR_ROUND1.md
stages/stage9/README.md   # minimal navigation/status sync only
```

No production file, test file, Stage8 file, or state-authority repository file is changed.

`STAGE9_AUTHORING_REPORT.md` remains untouched because it is a historical authoring-time record; old phase/file counts are superseded by this repair record and current `STAGE9.md` rather than rewritten retroactively.

## Commit

Planned commit message:

```text
design(stage9): repair round1 architecture findings
```

The commit SHA is intentionally not self-embedded in this file because a commit cannot contain its own final hash without changing that hash. The authoritative SHA is the remote `main` commit containing this record and is reported by post-commit verification.

## Verdict

# ROUND1 DESIGN REPAIR COMPLETE — ROUND2 AUDIT REQUIRED

This means only:

```text
Round1 findings have a unique implementation-spec repair
Stage9 remains DRAFT — DESIGN AUDIT REQUIRED
Stage9 FROZEN = NO
Ready for implementation = NO
```

It does **not** mean PASS/FROZEN/READY FOR IMPLEMENTATION.

Next step:

```text
Stage9 Design Audit Round 2
```
