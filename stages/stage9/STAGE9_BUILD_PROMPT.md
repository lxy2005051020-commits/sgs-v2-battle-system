# Stage9 Build Prompt

> Project: 三国志战略版战斗模拟器 V2  
> Repository: `lxy2005051020-commits/sgs-v2-battle-system`  
> Target branch: `main`  
> Authoring baseline (battle): `e7e08ff4c4371fc96f58c54b21cd25265665c0f4`  
> Frozen state-authority baseline: `15ed915435f328a6ecd8f488d98b5b9e13c913b5`  
> Stage9 Design Frozen: **YES**  
> Design Freeze Verified: **YES**  
> Build Prompt Authored: **YES**  
> Build Prompt Audited: **NO**  
> Production Implementation Authorized: **NO**

```text
STATUS:
DRAFT — BUILD PROMPT AUDIT REQUIRED

Stage9 Design Frozen = YES
Design Freeze Verified = YES

Build Prompt Authored = YES
Build Prompt Audited = NO

Production Implementation Authorized = NO

Next Step:
Stage9 Build Prompt Audit
```

This file is an implementation execution contract translated from the frozen `STAGE9.md`. It is **not** a new design document, does not create gameplay rules, and MUST NOT be executed until a later Stage9 Build Prompt Audit explicitly authorizes production implementation.

---

# 1. Executor Role and Non-Negotiable Scope

When this prompt is later authorized, the implementation executor must build Stage9 strictly as eight independently-green phases:

```text
9.1
→ tests green
→ exit gate PASS
→ commit
→ remote main verification

9.2
→ tests green
→ exit gate PASS
→ commit
→ remote main verification

...

9.8
→ tests green
→ exit gate PASS
→ commit
→ remote main verification
```

Forbidden strategy:

```text
Big Bang implementation
wire all production paths first
add tests at the end
create placeholder/TODO services used by production
implement later-phase semantic owners early
silently reinterpret gameplay to make tests pass
```

Stage9 may only:

```text
wrap
coordinate
redirect
partition
derive
schedule
settle assigned target amounts
finalize
```

Stage9 may not reopen Stage8 gameplay semantics.

Permanent Stage8 boundary:

```text
DamageResult.final_damage = Dtotal
DamageSettlementRequest.assigned_target_damage = Dtarget
DamageResolutionResult.actual_target_troop_loss = ActualTargetTroopLoss
```

These three layers must never be collapsed or aliased.

---

# 2. Mandatory Pre-Flight Gate

Before touching production code or tests, perform all of the following against the live remote repositories.

## 2.1 Re-read remote heads

Read:

```text
lxy2005051020-commits/sgs-v2-battle-system main
lxy2005051020-commits/sgs-state-mechanics-research main
```

Do not trust a pasted report, local checkout, cached SHA, or this document alone.

Frozen authority identity that must still be present in ancestry/history:

```text
Frozen audited design commit:
394d32e40b6584db9814f46dfbf44a2d5e753893

Round3 approval commit:
524438ef97f8170fd81d026f82f7ecf6ae828a90

Design Freeze commit:
3bc2e2d0b2dffed4b718ae903abb835fa495f278

Design Freeze Audit commit:
e7e08ff4c4371fc96f58c54b21cd25265665c0f4

Frozen audited STAGE9.md blob:
8972452d68d6c71e45563a9a2ec5d70826978c9b

State authority baseline:
15ed915435f328a6ecd8f488d98b5b9e13c913b5
```

The future implementation baseline may legitimately be a descendant because Build Prompt authoring/audit commits occur after the freeze verification. Therefore do **not** require `main == e7e08ff4...` at implementation time. Instead verify that every intervening commit is authorized Stage9 documentation/audit movement and that no unreviewed production/test/Stage8/P0 semantic drift occurred.

## 2.2 Read authority files completely

At minimum re-read:

```text
stages/stage9/STAGE9.md
stages/stage9/STAGE9_DESIGN_FREEZE.md
stages/stage9/audits/STAGE9_DESIGN_FREEZE_AUDIT.md
stages/stage9/audits/STAGE9_DESIGN_AUDIT_ROUND3.md
stages/stage9/audits/STAGE9_DESIGN_REPAIR_ROUND2.md
stages/stage9/hardening/STAGE9_TYPED_RUNTIME_CONTRACTS.md
stages/stage9/hardening/STAGE9_RUNTIME_INVARIANTS.md
stages/stage9/hardening/STAGE9_REGRESSION_CONTRACTS.md
stages/stage9/docsync/STAGE9_AUTHORITY_MAP.md
```

Also read the current production files and tests actually touched by the target phase. README files are navigation only.

## 2.3 Verify implementation authorization

Do not start Phase 9.1 unless a later formal Build Prompt Audit states all of the following:

```text
Stage9 Build Prompt Audit = PASS
Build Prompt Audited = YES
Production Implementation Authorized = YES
```

If that authorization is absent:

```text
STOP IMPLEMENTATION
REPORT: BUILD PROMPT AUDIT / AUTHORIZATION REQUIRED
```

## 2.4 Verify no semantic drift

If any current authority conflicts with frozen `STAGE9.md` on gameplay semantics:

```text
STOP IMPLEMENTATION
REPORT: STAGE9 DESIGN REOPEN REQUIRED
```

Do not select whichever rule seems more convenient.

## 2.5 Preserve authority priority

Gameplay semantics:

```text
1. current mechanism/shared P0 contracts
2. RF-P01..RF-P07 re-freeze records
3. STAGE9_CORE_ARBITRATION_RULES_V2
4. RF-C01 typed contracts / invariants / regressions
```

Implementation design authority:

```text
frozen STAGE9.md
```

Freeze record:

```text
STAGE9_DESIGN_FREEZE.md
```

The freeze record records the frozen design. It does not invent new gameplay semantics.

---

# 3. Frozen Cross-Mechanism Contracts

The implementation must preserve these identities without reinterpretation.

## 3.1 Target pipeline

```text
Alive/legal pool
→ camp filter
→ Confusion selector arbitration
→ Taunt selector arbitration
→ default selector
→ intended_attack_target frozen
→ Guard exactly once
→ post_redirect_actual_target frozen
```

Combo #2:

```text
same ActionId
new NormalAttackInstanceId
new TargetResolutionResult
new Guard pass
```

## 3.2 NormalAttack master

```text
NormalAttackSystem
= unique NormalAttack lifecycle master
```

It owns ordering/component orchestration/result assembly only. It does not own target algorithms, partition math, state mutation, Cleave/Chain/Counter internals, finalization semantic state, or Stage8 formulas.

## 3.3 Future admission

Exactly six global future branches exist:

```text
NEXT_ACTION
ASSAULT
COMBO_SECOND_NORMAL_ATTACK
COUNTER_BATCH
CHAIN_TRAVERSAL
CLEAVE_EFFECT
```

Required order:

```text
FutureAdmissionGate
→ one-shot FutureAdmissionPermit
→ validate/consume permit
→ branch identity allocation/admission
```

Already-admitted local work does not re-query the global gate.

## 3.4 Finalization

```text
VictorySystem = pure evaluator
BattleFinalizationCoordinator = semantic termination owner
BattleEngine = legacy compatibility projector
```

Termination state:

```text
RUNNING
→ VICTORY_LATCHED
→ DRAINING_ADMITTED_WORK
→ FINALIZED
```

Legacy barriers:

```text
INITIAL_SETTLED
ROUND_START_HOOKS_SETTLED
UNIT_ACTION_START_HOOKS_SETTLED
ACTION_SETTLED
ROUND_END_SETTLED
MAX_ROUND_SETTLED
```

`ACTION_SETTLED` observable order:

```text
ActionSystem.execute
→ semantic victory evaluate/latch
→ UNIT_ACTION_ENDED
→ permit-backed final compatibility projection
```

`BATTLE_END` / `BATTLE_ENDED` must not move before `UNIT_ACTION_ENDED` on this path.

## 3.5 Provenance

```text
EffectSourceRef = pre-operation provenance
OperationLineage = runtime operation ancestry
```

Unique conversion point:

```text
EffectSourceRef + runtime parent scope
→ DamageInstanceCoordinator
→ OperationLineage
```

Never infer Stage9 `SourceType` backward from Stage8 `DamageSourceType`.

## 3.6 SkillSlot

```text
INHERENT  = 0
LEARNED_1 = 1
LEARNED_2 = 2
```

Slot is holder-specific runtime provenance, never a static `SkillDefinition` property.

## 3.7 Integerization

```text
CHAIN                  = FLOOR
CLEAVE                 = FLOOR
DAMAGE_SHARE           = ROUND_HALF_UP
DISTRIBUTION target    = ROUND_HALF_UP
DISTRIBUTION participant = ROUND_HALF_UP
```

No generic `ExactRatio.from_float()` and no host-language `round()` as oracle.

## 3.8 DSTS9-B02 status

Preserve exactly:

```text
EMPIRICAL: OPEN / UNOBSERVED
RUNTIME: CLOSED BY PROJECT_RUNTIME_DEFAULT
DESIGN: NOT BLOCKING
RESEARCH DEBT: YES
```

The commander-participant Distribution drain behavior is an engineering runtime default, not empirically proven official behavior.

---

# 4. Exact Frozen Production File Plan

Pure code-organization-equivalent adjustments are allowed only if semantic ownership, dependency direction, public contracts, and phase boundaries stay unchanged. Otherwise stop for Design Reopen.

## 4.1 Planned NEW production files — 16

```text
sgs_v2/battle_core/operation_identity.py
sgs_v2/battle_core/stage9_trace.py
sgs_v2/battle_core/stage9_integerization.py
sgs_v2/battle_core/stage9_state_params.py
sgs_v2/battle_core/stage9_state_runtime.py
sgs_v2/battle_core/target_resolution_system.py
sgs_v2/battle_core/reaction_permission_policy.py
sgs_v2/battle_core/execution_right_system.py
sgs_v2/battle_core/damage_instance_coordinator.py
sgs_v2/battle_core/damage_partition_system.py
sgs_v2/battle_core/direct_troop_loss_system.py
sgs_v2/battle_core/cleave_derived_damage_system.py
sgs_v2/battle_core/cleave_system.py
sgs_v2/battle_core/chain_system.py
sgs_v2/battle_core/counter_system.py
sgs_v2/battle_core/battle_finalization_coordinator.py
```

## 4.2 Planned MODIFY production files — 17

```text
sgs_v2/battle_core/context.py
sgs_v2/battle_core/battle_systems.py
sgs_v2/battle_core/engine.py
sgs_v2/battle_core/action_system.py
sgs_v2/battle_core/normal_attack_system.py
sgs_v2/battle_core/damage_resolution_system.py
sgs_v2/battle_core/effect_executor.py
sgs_v2/battle_core/effect_result.py
sgs_v2/battle_core/skill_runtime.py
sgs_v2/battle_core/skill_resolver.py
sgs_v2/battle_core/effects.py
sgs_v2/battle_core/state_instance.py
sgs_v2/battle_core/state_lifecycle_system.py
sgs_v2/battle_core/official_state_catalog.py
sgs_v2/battle_core/events.py
sgs_v2/battle_core/trigger_system.py
sgs_v2/battle_core/__init__.py
```

## 4.3 KEEP/CALL by default

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

## 4.4 Stage8 gameplay semantics — DO NOT TOUCH

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

---

# 5. Universal Per-Phase Workflow

For every phase `9.x`, use this exact control loop.

## 5.1 Start gate

1. Re-read remote `main`.
2. Confirm it equals the previously verified phase commit, or explain and validate authorized drift before continuing.
3. Read the phase-relevant production/test files from the remote state.
4. Confirm there is no forward dependency on a later phase.
5. Confirm no production call points to a placeholder/stub/TODO Stage9 service.

## 5.2 Build only the current phase

Implement only the files/contracts needed for the current phase. Do not pre-wire later mechanism services “for convenience”.

## 5.3 Test before commit

Required before phase exit:

```text
all pre-existing tests green
all current-phase new tests green
all current-phase mapped regression contracts green
all current-phase mapped invariant assertions green
all current-phase architecture tests green where applicable
Stage8 frozen tests green
```

## 5.4 Diff audit before commit

Inspect exact changed files and reject:

```text
unexpected Stage8 semantic edits
unexpected P0/historical audit edits
production stubs/TODOs
unplanned future-phase production wiring
EventBus control-flow ownership
BattleContext service-locator growth
operation IDs used as gameplay comparators
reverse DamageSourceType -> SourceType inference
```

## 5.5 Commit and remote verify

Each phase gets its own implementation commit. After pushing:

```text
re-read remote main
verify exact commit SHA
verify commit message
verify changed-file set
verify parent is the previously accepted phase/baseline commit
verify report claims against repository contents
```

Do not begin the next phase until this verification passes.

Recommended commit naming:

```text
feat(stage9): implement phase 9.1 identity foundations
feat(stage9): implement phase 9.2 finalization transition
feat(stage9): implement phase 9.3 target and source-slot ingress
feat(stage9): implement phase 9.4 settlement core
feat(stage9): implement phase 9.5 partition damage cutover
feat(stage9): implement phase 9.6 normal attack orchestration
feat(stage9): implement phase 9.7 cleave chain counter
feat(stage9): complete phase 9.8 integration
```

---

# 6. Phase 9.1 — Identity / Provenance / Exact Numeric / Permit Types

## Scope

Create the non-destructive foundational types only:

```text
operation identities + OperationIdAllocator
SourceType
OperationLineage
EffectSourceRef
SkillSlot
ExactRatio + exact integerization helpers
Stage9 state parameter types
Stage9 trace contract
permit/capability value types/interfaces required by later phases
```

No production damage/finalization reroute.

## Expected file focus

```text
NEW:
operation_identity.py
stage9_trace.py
stage9_integerization.py
stage9_state_params.py
reaction_permission_policy.py
execution_right_system.py   # type/capability foundations only

MODIFY as needed:
effects.py
skill_runtime.py
__init__.py
```

Do not make production future-branch factories depend on incomplete later-phase systems.

## Required tests

```text
operation ID uniqueness/immutability/lineage validation
SourceType validation
SkillSlot legal domain {0,1,2}
EffectSourceRef validation
ExactRatio canonicalization
no generic from_float
REG-INT-01..05
operation/permit IDs not gameplay ordering keys
```

## Exit gate

```text
SkillSlot domain frozen
ExactRatio canonicalization frozen
no generic from_float
EffectSourceRef frozen
SourceType producer contract representable
permit primitives typed
no production damage/finalization reroute
existing tests green
phase tests green
```

Then commit and remote verify. Stop before Phase 9.2.

---

# 7. Phase 9.2 — Execution Right + Legacy-Compatible Finalization

## Scope

Activate only the real finalization/execution-right base infrastructure:

```text
BattleFinalizationCoordinator
BattleTerminationState/record
LegacyFinalizationBarrier
FinalizationResult
FinalizationProjectionPermit
FutureAdmissionGate base capability
LegacyActionDispatchAdapter for NEXT_ACTION
```

At this phase:

```text
Stage9 admitted-operation set = EMPTY
ActionScope count = 0
DamageInstance count = 0
ReactionBatch count = 0
stub operation scopes = FORBIDDEN
```

## Expected file focus

```text
NEW:
battle_finalization_coordinator.py
execution_right_system.py

MODIFY:
context.py
battle_systems.py
engine.py
events.py
__init__.py
```

`victory_system.py` remains the pure evaluator and should be called, not redesigned.

## Required compatibility tests

Exercise all six real legacy barriers:

```text
INITIAL_SETTLED
ROUND_START_HOOKS_SETTLED
UNIT_ACTION_START_HOOKS_SETTLED
ACTION_SETTLED
ROUND_END_SETTLED
MAX_ROUND_SETTLED
```

For applicable paths assert:

```text
legacy result unchanged
observable event order unchanged
BATTLE_END exactly once
BATTLE_ENDED exactly once
VictorySystem not re-evaluated during projection
FinalizationResult deep immutable
projection permit claim once / consume once
next-Action FutureAdmissionPermit reuse rejected
```

Special assertion:

```text
ActionSystem.execute
→ ACTION_SETTLED semantic observation/latch
→ UNIT_ACTION_ENDED
→ projection
```

## Exit gate

```text
legacy barrier map = 6/6
terminal checkpoints migrated 1:1
Coordinator is unique semantic finalization owner
Engine is permit-backed compatibility projector only
legacy outcomes/events unchanged
FinalizationResult deep immutable
projection exactly once
no fake operation scopes
existing tests green
phase tests green
```

Then commit and remote verify. Stop before Phase 9.3.

---

# 8. Phase 9.3 — Target Resolution + Holder Source-Slot Ingress

## Scope

Implement:

```text
LoadedSkillRef / LoadedSkillSet / SkillRuntime.from_loaded
source_skill_slot provenance propagation
same-source reapply slot mismatch guard
SkillResolver ACTIVE_SKILL EffectSourceRef producer
StateInstance.source_skill_slot
StateLifecycleSystem supplied provenance handling
TargetResolutionSystem
Confusion > Taunt > default selector
Guard exactly once
immutable intended/actual target identities
Stage9StateRuntime read/maintenance adapter
```

No production `EffectExecutor -> DamageInstanceCoordinator` cutover yet.

## Expected file focus

```text
NEW:
stage9_state_runtime.py
target_resolution_system.py

MODIFY:
skill_runtime.py
skill_resolver.py
effects.py
state_instance.py
state_lifecycle_system.py
official_state_catalog.py
battle_systems.py
__init__.py
```

## Required tests

```text
REG-TGT-01..04
holder-specific slot ingress
duplicate same-holder same-slot rejection
no slot inference from skill_id
source_ref propagation
StateInstance source slot persistence
same-source reapply mismatch rejection
TargetResolution immutability
Guard one-pass
```

## Exit gate

```text
holder-specific skill-slot ingress real
source slot immutable through apply/reapply path
periodic source metadata available on StateInstance
TargetResolution immutable/single-pass
no production DamageEffect cutover
existing tests green
phase tests green
```

Then commit and remote verify. Stop before Phase 9.4.

---

# 9. Phase 9.4 — Typed Settlement + Isolated DamageInstance

## Scope

Implement the isolated standard DamageInstance core without routing production `EffectExecutor` through it yet.

Required settlement model:

```text
DamageSystem.calculate
→ DamageResult.final_damage = Dtotal
→ DamageSettlementRequest.assigned_target_damage = Dtarget
→ DamageSettlementPermit
→ DamageResolutionSystem.settle
→ actual_target_troop_loss
```

Legacy APIs remain compatible:

```text
DamageResolutionSystem.resolve = historical LEGACY_COMPAT full settlement
apply_result = legacy full-settlement wrapper only
```

Do not add optional `assigned_amount` to `apply_result`.

## Expected file focus

```text
NEW:
damage_instance_coordinator.py

MODIFY:
damage_resolution_system.py
battle_systems.py
events.py
__init__.py
```

## Required tests

```text
Dtotal != Dtarget != ActualTargetTroopLoss fixture
DAMAGE_DEALT.requested_damage == Dtarget
legacy resolve/apply_result compatibility
one DamageSettlementPermit per DamageInstance
permit consumed before troop mutation
permit replay rejected with no second mutation/event
identity/lineage mismatch rejected
prevented result causes zero troop mutation
finalization observation fixture
```

## Exit gate

```text
isolated DamageInstance fixture end-to-end green
typed settlement green
settlement replay structurally blocked
Dtotal/Dtarget/ActualLoss distinct
legacy settlement semantics unchanged
EffectExecutor still not production-rerouted
Stage8 calculation semantics unchanged
```

Then commit and remote verify. Stop before Phase 9.5.

---

# 10. Phase 9.5 — Partition + DirectTroopLoss + EffectExecutor Production Cutover

## Scope

Implement real partition/direct-loss infrastructure first; only then cut production `DamageEffect` routing over at the end of the phase.

Implement:

```text
exactly-one partition plan: NONE | SHARE | DISTRIBUTION
Share target-first transaction
Distribution immutable fixed plan
AttributedDirectTroopLoss
DirectTroopLossResolver
active-skill SourceType producer wiring
periodic SourceType producer wiring in TriggerSystem
EffectExecutor consumes authoritative EffectSourceRef
DamageEffectResult narrow compatibility surface
```

Direct troop loss must not re-enter the normal hit pipeline.

## Expected file focus

```text
NEW:
damage_partition_system.py
direct_troop_loss_system.py

MODIFY:
effect_executor.py
effect_result.py
trigger_system.py
skill_resolver.py
effects.py
battle_systems.py
events.py
__init__.py
```

## Cutover gate before changing production route

```text
production DamageEffect source identity coverage = 100%
unclassified production DamageEffect = 0
SkillResolver emits ACTIVE_SKILL directly
TriggerSystem emits PERIODIC_DAMAGE directly
EffectExecutor performs no reverse DamageSourceType inference
all attribution preserved
partition/direct loss real
finalization/execution-right real
one-shot settlement real
```

If any production-reachable DamageEffect lacks authoritative `EffectSourceRef`, do not cut over.

## Required regressions

```text
REG-SHR-01..04
REG-DST-01..04
```

Also assert producer identity through real `SkillResolver` and `TriggerSystem` construction paths.

## DSTS9-B02 rule

For REG-DST-03 and related runtime:

```text
PROJECT_RUNTIME_DEFAULT
NOT EMPIRICALLY PROVEN
commander participant death during admitted fixed transaction
→ drain existing planned local transaction
→ finalization after transaction barrier
```

Do not relabel this as official fidelity.

## Exit gate

```text
production DamageEffect cannot bypass provenance
production DamageEffect cannot bypass partition
production DamageEffect cannot bypass finalization observation
production DamageEffect cannot bypass one-shot settlement
unclassified DamageEffect = 0
legacy historical direct APIs remain compatible
existing tests green
phase tests green
```

Then commit and remote verify. Stop before Phase 9.6.

---

# 11. Phase 9.6 — NormalAttack Master + Combo + Assault Admission

## Scope

Convert the existing `NormalAttackSystem` into the unique thin Stage9 master and add real Action/NormalAttack identities and branch admission.

Implement:

```text
ActionId
ActionScope admission using NEXT_ACTION permit
NormalAttackInstanceId
fresh TargetResolution per NormalAttack
ComboActionGrant
Combo checkpoint one-shot consume
cfg230-equivalent fact once
Combo #2 FutureAdmissionPermit before NA #2 identity allocation
AssaultDispatchPort admission seam only
real ActionScope replaces Phase 9.2 legacy action dispatch adapter
```

Do not invent Assault gameplay semantics.

## Expected file focus

```text
MODIFY:
action_system.py
normal_attack_system.py
engine.py
battle_systems.py
events.py
__init__.py
```

Use already-completed target/damage/finalization services. Do not embed Cleave/Chain/Counter algorithms.

## Required regressions

```text
REG-TGT-05..07
REG-CMB-01..05
```

Also assert:

```text
one Action <= 2 physical NormalAttacks
checkpoint <= 1 per Action
consume/cfg230 <= 1 per Action
#2 fresh target + fresh Guard
no future identity allocation before permit consume
no recursive Combo checkpoint
Action/Assault/Combo branch factories have no permit bypass
```

## Exit gate

```text
NormalAttackSystem is unique master
Action and NA identities distinct
Combo #2 is fresh NA instance
future branch gate precedes identity allocation
Assault remains seam only
existing tests green
phase tests green
```

Then commit and remote verify. Stop before Phase 9.7.

---

# 12. Phase 9.7 — Cleave + Chain + Counter

## Scope

Implement the remaining mechanism services only after real Action/NormalAttack/DamageInstance/finalization infrastructure exists.

Implement:

```text
CleaveDerivedDamageResolver
Cleave effect-major ordering
Cleave secondary fixed plan + JIT liveness
Cleave actual-target-troop-loss basis
Chain deferred trigger snapshot/live split
Chain monotonic one-pass slot cursor
CHAIN_TRUE_FEEDBACK restricted settlement
Counter trigger-time immutable batch
Counter execution-time owner/target liveness gates
Counter dead-target explicit zero-loss terminal
shared DamageCallbackAdmissionPoint
permit-required CLEAVE_EFFECT / CHAIN_TRAVERSAL / COUNTER_BATCH factories
```

Positive live-target Counter uses the standard DamageInstance path with legitimate Stage8 `DamageSourceType.COUNTER`. Cleave and Chain TRUE_FEEDBACK must not fake Stage8 standard requests.

## Expected file focus

```text
NEW:
cleave_derived_damage_system.py
cleave_system.py
chain_system.py
counter_system.py

MODIFY:
normal_attack_system.py
battle_systems.py
events.py
official_state_catalog.py
__init__.py
```

## Required regressions

```text
REG-CLV-01..05
REG-CHN-01..04
REG-CTR-01..05
```

Also assert:

```text
Cleave source ordering by authoritative source_skill_slot where required
no skill_id or OperationId fallback for required slot order
Cleave derived path does not re-enter Stage8 base formula/modifier/Crit
Chain passed slot never revisited
ChainSystem cannot self-admit
Counter admitted sibling survives earlier sibling victory latch
Counter dead target bypasses full weapon pipeline
already-admitted local work never re-gates globally
```

## Exit gate

```text
all six future branch families structurally permit-gated
all Cleave/Chain/Counter P0 regressions green
local admitted work uses local gates only
no recursive permission leak
existing tests green
phase tests green
```

Then commit and remote verify. Stop before Phase 9.8.

---

# 13. Phase 9.8 — Full Integration / Regression / Architecture Closure

No new gameplay semantics or new production switch is allowed here. This phase is integration and verification only.

Run and close:

```text
FINAL_01_CHAIN_COMMANDER_DEATH
FINAL_02_COUNTER_SIBLING
FINAL_03_COMBO_BATTLE_END
FINAL_04_CLEAVE_COMMANDER_SECONDARY
FINAL_05_SHARE_COMMANDER_TARGET
FINAL_06_DISTRIBUTION_COMMANDER_PARTICIPANT
```

Also run:

```text
all existing Stage1-8 tests
all Stage9 phase tests
45/45 gameplay regression contracts
42/42 runtime invariant assertions
12/12 architecture tests
golden trace / operation identity diagnostics
CI/demo compatibility where present
```

Final exit gate:

```text
42/42 invariants enforced
45/45 gameplay regressions green
12/12 architecture tests green
unclassified production DamageEffect = 0
dependency cycles = 0
forward production dependencies = 0
Stage8 semantic reopen = 0
production stubs/TODO Stage9 services = 0
```

Only after this gate may the implementation phase be reported complete. This still does not perform Stage9 Final Freeze; a separate Implementation Audit / Repair / Re-Audit / Final Freeze lifecycle follows.

---

# 14. Runtime Invariant Mapping — 42 / 42

The implementation must preserve the complete RF-C01 invariant texts in `STAGE9_RUNTIME_INVARIANTS.md`. This table assigns their primary implementation/test phase; it does not rewrite their semantics.

| Invariant | Primary phase | Required proof seam |
|---|---:|---|
| INV-01 | 9.3 | immutable selected/intended/actual/damage-recipient identities |
| INV-02 | 9.3 | selector arbitration before Guard |
| INV-03 | 9.3 | one Guard pass per NormalAttack |
| INV-04 | 9.6 | downstream NA-bound mechanics consume actual target |
| INV-05 | 9.4 | concrete DamageEvent/settlement owns recipient |
| INV-06 | 9.6 | Combo #2 fresh NA + target resolution |
| INV-07 | 9.6 | physical Combo state / operational state / Action grant separated |
| INV-08 | 9.6 | ACTION_START maintenance before grant |
| INV-09 | 9.6 | REMOVE revokes; ordinary SUPPRESS does not revoke current grant |
| INV-10 | 9.6 | checkpoint <= 1 per Action |
| INV-11 | 9.6 | consume/cfg230 <= 1 per Action |
| INV-12 | 9.6 | physical NormalAttack <= 2 per Action |
| INV-13 | 9.7 | Cleave source identity, no NormalAttack identity |
| INV-14 | 9.7 | Cleave basis = ActualTargetTroopLoss |
| INV-15 | 9.1 + 9.7 | exact FLOOR helper/vector used by Cleave |
| INV-16 | 9.7 | no Cleave upstream formula/modifier/Crit re-entry |
| INV-17 | 9.1 + 9.7 | centralized typed reaction permission policy |
| INV-18 | 9.3 + 9.7 | authoritative skill-slot/effect-major source ordering and fixed/JIT secondary plan; no comparator invention |
| INV-19 | 9.5 | AttributedDirectTroopLoss distinct from DamageEvent |
| INV-20 | 9.5 | direct loss bypasses HitResolution and hit callbacks |
| INV-21 | 9.1 + 9.5 | explicit direct-loss/source provenance |
| INV-22 | 9.5 | exactly one SHARE/DISTRIBUTION/NONE partition |
| INV-23 | 9.5 | cross-family replacement does not resurrect |
| INV-24 | 9.5 | Share commits target first |
| INV-25 | 9.5 | lethal Share target discards pending sharer work |
| INV-26 | 9.4 + 9.5 | theoretical/assigned/actual/credit facts remain distinct |
| INV-27 | 9.5 | Distribution participant tuple and N immutable |
| INV-28 | 9.5 | Distribution calculated amounts immutable |
| INV-29 | 9.5 | invalid planned participant = skip only |
| INV-30 | 9.5 | no newly eligible participant append/replan |
| INV-31 | 9.5 | DSTS9-B02 runtime default labeled non-empirical |
| INV-32 | 9.7 | Chain deferred snapshot contains only immutable trigger facts |
| INV-33 | 9.7 | Chain execution live-reads current world fields |
| INV-34 | 9.7 | monotonic one-pass Chain slot cursor |
| INV-35 | 9.7 | Chain TRUE_FEEDBACK restricted settlement |
| INV-36 | 9.7 | CounterBatch membership immutable after admission |
| INV-37 | 9.7 | Counter admission distinct from owner liveness gate |
| INV-38 | 9.7 | dead-target admitted Counter explicit zero terminal |
| INV-39 | 9.2 + 9.8 | UnitDeathFact / victory latch / finalized separated |
| INV-40 | 9.2 + 9.6 + 9.7 | victory latch blocks new future branches, not admitted local work |
| INV-41 | 9.2 | finalization has one semantic owner |
| INV-42 | 9.1 + 9.5 + 9.7 | typed SourceType/lineage/permission authority; no string/call-stack/battle.finished inference |

Final Phase 9.8 must re-run all 42 as one closure gate.

---

# 15. Gameplay Regression Mapping — 45 / 45

| Contract family | Contract IDs | Primary phase |
|---|---|---:|
| Target (7) | REG-TGT-01, 02, 03, 04 | 9.3 |
| Target (7) | REG-TGT-05, 06, 07 | 9.6 |
| Combo (5) | REG-CMB-01..05 | 9.6 |
| Cleave (5) | REG-CLV-01..05 | 9.7 |
| Chain (4) | REG-CHN-01..04 | 9.7 |
| Share (4) | REG-SHR-01..04 | 9.5 |
| Distribution (4) | REG-DST-01..04 | 9.5 |
| Counter (5) | REG-CTR-01..05 | 9.7 |
| Finalization (6) | FINAL_01..FINAL_06 | 9.8 |
| Integerization (5) | REG-INT-01..05 | 9.1, re-run 9.8 |

Count gate:

```text
Target          7
Combo           5
Cleave          5
Chain           4
Share           4
Distribution    4
Counter         5
Finalization    6
Integerization  5
-----------------
Total          45
```

No contract may be silently merged away because another test happens to cover similar behavior.

---

# 16. Architecture Test Mapping — 12 / 12

| # | Architecture guarantee | Primary phase | Required assertion |
|---:|---|---:|---|
| 1 | Stage8 semantic/import inversion blocked | 9.4/9.8 | Stage8 calculation modules do not import Stage9 mechanism services; Stage8 meaning unchanged |
| 2 | FutureAdmissionGate no bypass | 9.6/9.7/9.8 | every global future branch construction surface requires gate-issued permit |
| 3 | Finalization semantic writer single | 9.2/9.8 | only coordinator mutates termination/finalization semantic state |
| 4 | Finalization projection exactly once | 9.2/9.8 | repeated claim/consume cannot emit second BATTLE_END/BATTLE_ENDED |
| 5 | Operation IDs never gameplay comparator | 9.1/9.8 | static/source check forbids operation IDs in gameplay ordering |
| 6 | StateRegistry sole state storage | 9.3/9.8 | no second physical state container |
| 7 | StateLifecycleSystem sole state mutation | 9.3/9.8 | no direct physical state mutation outside lifecycle owner |
| 8 | EventBus facts-only | 9.2/9.8 | no subscriber required for orchestration/finalization |
| 9 | BattleSystems composition root | 9.2 onward/9.8 | no service self-construction/global singleton/BattleContext service locator |
| 10 | Damage settlement one-shot | 9.4/9.8 | replayed Stage9 request/permit has no second troop/event side effect |
| 11 | EffectExecutor Stage9 SourceType producer coverage | 9.5/9.8 | active/periodic producers explicit; no reverse enum inference |
| 12 | source_skill_slot ingress + immutability | 9.3/9.8 | typed domain, loadout producer, duplicate-slot rejection, reapply mismatch rejection |

Phase 9.8 must report:

```text
Architecture tests = 12/12 GREEN
```

---

# 17. STOP CONDITIONS — DESIGN REOPEN REQUIRED

If any condition below is encountered, do not invent a local solution.

```text
P0 vs frozen STAGE9 semantic conflict
missing authority for reachable runtime path
Stage8 semantic reopen required
new future branch not in frozen six-branch permit set
unclassified production DamageEffect at required cutover
need new integerization rule
need different Target pipeline
need different finalization barrier
need different SourceType semantics
DSTS9-B02 runtime default insufficient
42-invariant obligation cannot be implemented without semantic change
45-regression contract conflicts with frozen design
architecture guarantee requires ownership/dependency change
phase dependency must be reordered
public contract must change in a gameplay-affecting way
new state storage or mutation owner appears necessary
EventBus control flow appears necessary
```

Required response:

```text
STOP IMPLEMENTATION

REPORT:
STAGE9 DESIGN REOPEN REQUIRED

Include:
- exact remote SHA
- exact conflicting file/authority
- exact reachable runtime path
- why current frozen design is insufficient
- whether issue is gameplay semantic, architecture ownership, or missing authority
- no speculative repair committed
```

A pure code-organization adjustment does **not** require Design Reopen only when all remain unchanged:

```text
semantic ownership
dependency direction
public semantic contracts
phase boundaries
Stage8 boundary
```

---

# 18. Required Phase Report Format

After each implementation phase, report only repository-verified facts.

```text
Phase: 9.x
Remote main before: <sha>
Remote main after:  <sha>
Commit:             <sha + message>
Parent:             <sha>

Changed production files:
<exact list>

Changed test files:
<exact list>

Existing tests: PASS/FAIL
Phase tests:    PASS/FAIL
Mapped regressions: <x/x PASS>
Mapped invariants:  <x/x PASS>
Mapped architecture tests: <x/x PASS>
Stage8 reopen: NO/YES
Forward dependency: 0/<count>
Production stub/TODO dependency: 0/<count>

Gameplay semantic changes: 0/<details>
Engineering defaults added: 0/<details>
Empirical claims added: 0/<details>

Exit Gate: PASS/FAIL
Next permitted step: <phase or STOP>
```

A report that says PASS while the remote repository disagrees is FAIL. Remote content wins, because apparently files remain stubbornly more authoritative than optimism.

---

# 19. Final Implementation Acceptance Obligation

Stage9 production implementation is complete only when the future implementation audit can verify all of the following from the repository and test results:

```text
42 / 42 runtime invariants
45 / 45 gameplay regression contracts
12 / 12 architecture tests

Stage8 semantic reopen = 0
P0 semantic conflict = 0
unclassified production DamageEffect = 0
future-admission bypass = 0
settlement replay path = 0
finalization duplicate projection = 0
state storage duplication = 0
state mutation ownership duplication = 0
dependency cycles = 0
forward production dependencies = 0
```

After Phase 9.8 the lifecycle is:

```text
Implementation Audit
→ Repair / Re-Audit if required
→ Stage9 Final Freeze
```

Do not perform Stage9 Final Freeze as part of Phase 9.8 itself.

---

# 20. Current Lifecycle Boundary

This file is currently only authored, not audited.

```text
DO NOT EXECUTE THIS BUILD PROMPT YET.
DO NOT MODIFY PRODUCTION.
DO NOT MODIFY TESTS.
DO NOT START PHASE 9.1.
```

Next permitted project action:

```text
Stage9 Build Prompt Audit
```
