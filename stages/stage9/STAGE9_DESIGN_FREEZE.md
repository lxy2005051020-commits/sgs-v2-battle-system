# Stage 9 Design Freeze Record

> Project: 三国志战略版战斗模拟器 V2
>
> Repository: `lxy2005051020-commits/sgs-v2-battle-system`
>
> Scope: Stage9 Cross-Mechanism Runtime Orchestration
>
> Status: `DESIGN FROZEN — PENDING FREEZE AUDIT`

---

# 1. Freeze basis

This record freezes the implementation specification that passed Stage9 Design Audit Round 3. It is a **design freeze record**, not the later implementation-final freeze record.

Frozen identities:

```text
Round3 audited design commit:
394d32e40b6584db9814f46dfbf44a2d5e753893
design(stage9): repair round2 architecture findings

Round3 audited STAGE9.md blob:
8972452d68d6c71e45563a9a2ec5d70826978c9b

Round3 approval commit:
524438ef97f8170fd81d026f82f7ecf6ae828a90
audit(stage9): complete design audit round 3

State authority baseline:
15ed915435f328a6ecd8f488d98b5b9e13c913b5
docs(combo): close stale CBS9-B03 status banner
```

Freeze admission:

```text
Round3 Verdict = PASS
Design Freeze Admission = ELIGIBLE
Design Freeze Admission after this transition = CONSUMED
```

The reviewed design body is the `STAGE9.md` body at the audited blob above. This freeze commit may change only status/current-admission/freeze-reference metadata around that body.

---

# 2. Design Freeze Gate

Round3 independently verified:

```text
BLOCKER = 0
MAJOR = 0
MINOR = 0
DOC_ONLY = 0

P0 semantic conflict = 0
Stage8 reopen = 0

Dependency cycle = 0
Forward production dependency = 0

Unowned runtime facts = 0
Unspecified reachable paths = 0

Unenforced invariants = 0
Untestable regressions = 0
Blocked architecture tests = 0
Independently-green phase failures = 0
```

Additional verified counts:

```text
legacy finalization barriers = 6/6
production DamageEffect producers = 2
classified DamageEffect producers = 2
unclassified DamageEffect producers = 0
future permit-required branches = 6/6
gate bypass paths = 0
Stage9 destructive settlement replay paths = 0
```

Design-freeze admission gate:

```text
Runtime invariants = 42 / 42 enforced/design-enforceable
Gameplay regression contracts = 45 / 45 mapped/testable
Architecture tests = 12 / 12 READY
```

These are design-readiness statements. They do not claim Stage9 production code or tests are already implemented.

---

# 3. Frozen runtime topology

The following Stage9 implementation contracts are frozen:

```text
NormalAttack orchestration
TargetResolution
DamageInstance coordination
Damage settlement
Damage partition
DirectTroopLoss
Cleave
Chain
Counter
Execution Right
Battle Finalization
```

Normative service topology remains the topology in the reviewed `STAGE9.md`:

```text
BattleEngine
  -> BattleFinalizationCoordinator
  -> ActionSystem
       -> NormalAttackSystem
            -> TargetResolutionSystem
            -> DamageInstanceCoordinator
            -> CleaveSystem
            -> ChainSystem
            -> CounterSystem
            -> AssaultDispatchPort
            -> Combo checkpoint

BattleSystems = service composition root
BattleContext = battle data + OperationIdAllocator + small termination record only
EventBus = observable facts only
```

No implementation phase may silently introduce a second lifecycle owner, second state store, global service locator, or event-driven orchestration owner.

---

# 4. Frozen runtime identity

The following operation identities are frozen as distinct typed runtime identities:

```text
ActionId
NormalAttackInstanceId
TargetResolutionId [TRACE_ONLY SUPPORTING ID]
DamageInstanceId
ReactionBatchId
CounterBatchEntryId
PartitionTransactionId
CleaveEffectId
ChainTraversalId
DirectTroopLossId
```

All operation/permit IDs are runtime identity or trace correlation only. They are never gameplay priority or comparator keys.

---

# 5. Frozen target contract

Target resolution order is frozen:

```text
Confusion
→ Taunt
→ intended_attack_target
→ Guard once
→ post_redirect_actual_target
```

There is exactly one selector arbitration before the intended target is frozen and exactly one Guard pass after it.

Combo #2 is frozen as:

```text
fresh NormalAttackInstance
+
fresh target resolution
+
fresh Guard resolution
```

No Combo #2 path may inherit the first NormalAttack target or Guard result.

---

# 6. Frozen NormalAttack master ownership

```text
NormalAttackSystem
=
NormalAttack lifecycle master orchestrator
```

It owns:

```text
ordering
component calls
NormalAttack-local result assembly
assigned future-branch admission call sites
```

It does not own:

```text
target algorithm
partition math
state mutation
Cleave algorithm
Chain algorithm
Counter internals
finalization state
Stage8 damage formulas
```

---

# 7. Frozen Stage8 boundary

```text
Stage8 = FROZEN
Formal Stage8 Reopen = NO
```

Permanent Stage8 fact:

```text
DamageResult.final_damage = Dtotal
```

Stage9 may add the typed assigned-target settlement field:

```text
DamageSettlementRequest.assigned_target_damage = Dtarget
```

Stage9 must not rewrite `DamageResult.final_damage` to the partitioned amount or otherwise reinterpret Stage8 theoretical-damage semantics.

---

# 8. Frozen settlement contract

The three semantic layers remain distinct:

```text
Dtotal
=
DamageResult.final_damage

Dtarget
=
DamageSettlementRequest.assigned_target_damage

ActualTargetTroopLoss
=
DamageResolutionResult.actual_target_troop_loss
```

They may not be aliased or collapsed during implementation.

Settlement API responsibilities are frozen:

```text
DamageSystem.calculate
= Stage8 theoretical calculation

DamageResolutionSystem.resolve
= legacy calculate + full settlement

DamageResolutionSystem.settle
= assigned-target settlement primitive

DamageInstanceCoordinator
= Stage9 orchestration
```

`DamageResolutionSystem.resolve` remains a legacy compatibility operation and does not become the Stage9 partition coordinator.

---

# 9. Frozen DamageSettlementPermit

Stage9 destructive target settlement is one-shot:

```text
one DamageInstanceId
→ one DamageSettlementPermit
→ validate + consume before troop mutation
```

Duplicate/reused/mismatched settlement is a domain/programmer error and must fail before troop/event side effects.

Forbidden replay guard:

```text
EventBus history inspection
```

No battle-long unbounded consumed-DamageInstance history is added to `BattleContext`.

---

# 10. Frozen effect provenance

`EffectSourceRef` is the canonical pre-operation provenance value and carries:

```text
Stage9 SourceType
source unit
source skill
source skill slot
```

It is distinct from:

```text
OperationLineage
= runtime execution ancestry
```

The unique conversion point remains:

```text
EffectSourceRef + runtime parent scope
→ DamageInstanceCoordinator
→ OperationLineage
```

Source-type ownership is frozen:

```text
DamageSourceType
= Stage8 formula classification

SourceType
= Stage9 provenance / permission identity
```

Forbidden:

```text
DamageSourceType → SourceType reverse inference
```

---

# 11. Frozen production DamageEffect producer set

Current production producers are frozen for the Phase 9.5 cutover plan:

```text
SkillResolver._build_effect
→ SourceType.ACTIVE_SKILL

TriggerSystem._effects_for_state
→ SourceType.PERIODIC_DAMAGE
```

`EffectExecutor` is a consumer/router and does not invent Stage9 provenance.

Phase 9.5 production cutover may occur only when:

```text
unclassified production DamageEffect producer = 0
```

---

# 12. Frozen SkillSlot / LoadedSkill design

```python
class SkillSlot(IntEnum):
    INHERENT  = 0
    LEARNED_1 = 1
    LEARNED_2 = 2
```

Frozen domain:

```text
internal indexing = 0-based
legal values = {0, 1, 2}
```

Holder-specific provenance is frozen through:

```text
LoadedSkillRef
LoadedSkillSet
SkillRuntime.from_loaded(...)
```

Slot belongs to holder-specific runtime provenance and does not belong to `SkillDefinition`.

For same-source refresh/reapply:

```text
incoming source_skill_slot == existing source_skill_slot
→ refresh may proceed according to mechanism P0

incoming source_skill_slot != existing source_skill_slot
→ domain error
→ no silent overwrite
```

Production-loaded duplicate same-holder same-slot skills are invalid at the loading boundary.

---

# 13. Frozen FutureAdmission contract

Global future branches are frozen as:

```text
NEXT_ACTION
ASSAULT
COMBO_SECOND_NORMAL_ATTACK
COUNTER_BATCH
CHAIN_TRAVERSAL
CLEAVE_EFFECT
```

Required construction order:

```text
FutureAdmissionGate
→ one-shot FutureAdmissionPermit
→ validate/consume permit
→ operation identity allocation / admission
```

Forbidden:

```text
construct/allocate operation first
→ ask gate later
```

Exactly-one authoritative caller remains defined for each branch by the reviewed `STAGE9.md`.

Already-admitted work does not re-query the global gate:

```text
Counter sibling
Chain slot
current Cleave secondary
Share pending local step
Distribution planned participant
```

Those use only their local execution/liveness rule.

---

# 14. Frozen finalization ownership

Ownership is frozen:

```text
VictorySystem
= pure evaluator

BattleFinalizationCoordinator
= semantic termination owner

BattleEngine
= legacy finalized-result compatibility projector
```

The coordinator is the unique owner of termination state, victory latch, drain state, finalization result, and projection-permit issuance/validation. Engine projects only after a valid permit; it does not re-evaluate victory.

---

# 15. Frozen legacy finalization barriers

The six existing macro barriers remain exactly:

```text
INITIAL_SETTLED
ROUND_START_HOOKS_SETTLED
UNIT_ACTION_START_HOOKS_SETTLED
ACTION_SETTLED
ROUND_END_SETTLED
MAX_ROUND_SETTLED
```

They preserve current BattleEngine observable timing.

`ACTION_SETTLED` special ordering is frozen:

```text
ActionSystem.execute
→ semantic victory evaluate/latch
→ UNIT_ACTION_ENDED
→ legacy final projection
```

`BATTLE_END` / `BATTLE_ENDED` must not move before `UNIT_ACTION_ENDED` on this path.

---

# 16. Frozen FinalizationResult / projection capability

Deep-immutable result schema is frozen:

```text
finalization_id
winner_team_id
reason
rounds_completed
final_troops_snapshot
```

Snapshot requirements:

```text
immutable tuple
stable unit identity ordering
no mutable BattleResult.final_troops reference
```

`FinalizationProjectionPermit` contract is frozen:

```text
FinalizationResult create once
projection claim once
permit consume once
```

It protects exactly-once compatibility side effects:

```text
context.ended
context.result
BATTLE_END
BATTLE_ENDED
```

---

# 17. Frozen ExactRatio / integerization

`ExactRatio` canonicalization is frozen:

```text
denominator > 0
gcd reduced
sign normalized to numerator
zero canonical = 0/1
```

Stage9 core has:

```text
NO generic ExactRatio.from_float()
```

Frozen integerization:

```text
CHAIN
→ FLOOR

CLEAVE
→ FLOOR

SHARE
→ ROUND_HALF_UP

DISTRIBUTION target
→ ROUND_HALF_UP

DISTRIBUTION participant
→ ROUND_HALF_UP
```

Host-language `round()` is not the Stage9 oracle.

---

# 18. Frozen Cleave design

At minimum the following are frozen:

```text
base = ActualTargetTroopLoss
Cleave-specific derived damage resolver
effect-major execution
GLOBAL_SLOT_ASCENDING secondary order
JIT target validity
current CleaveEffect = admission unit
```

Cleave is not a NormalAttack and does not re-enter the Stage8 base-formula/modifier/Crit pipeline.

A later independent CleaveEffect is a future branch and requires a new admission permit; secondaries inside the current admitted effect are local work.

---

# 19. Frozen Chain design

At minimum the following are frozen:

```text
TRUE_FEEDBACK
FLOOR
one-pass
monotonic ascending slot cursor
passed slot never revisited
deferred snapshot/live split
```

New ChainTraversal admission is owned by the shared `DamageCallbackAdmissionPoint`; `ChainSystem` cannot self-admit.

---

# 20. Frozen Counter design

At minimum the following are frozen:

```text
trigger-time batch admission snapshot
execution-time live world
owner-death local gate
dead-target zero-loss terminal path
```

An already-admitted sibling is not removed merely because a previous sibling killed the target. The dead-target path is explicit zero-loss terminal behavior and does not fake a full Stage8 damage request.

---

# 21. Frozen DirectTroopLoss design

```text
AttributedDirectTroopLoss
!= DamageEvent
```

It must not re-enter:

```text
Hit
Defense
Evasion
Resistance
FirstAid
Counter
Chain
Share
Distribution
generic Hurt callback
base damage formula
```

Its permitted consequences remain troop mutation/clamp, attribution/stat facts, death fact, and finalization observation as specified by the reviewed design.

---

# 22. Frozen permission / admission / local-gate separation

The following three layers remain separate:

```text
ReactionPermissionPolicy
= reaction family allowed for this source identity?

FutureAdmissionGate
= new future branch globally admissible now?

Local execution gate
= already-admitted work executable now?
```

They must not be collapsed into a generic `battle.finished`/reaction-depth boolean.

---

# 23. Frozen composition root / context / EventBus boundaries

```text
BattleSystems
= service composition root
```

Forbidden:

```text
global singleton
service self-construction
BattleContext as service locator
```

Allowed new `BattleContext` cross-mechanism infrastructure remains limited to:

```text
OperationIdAllocator
small termination record/read state
```

Forbidden in `BattleContext`:

```text
all systems
permit managers
mechanism queues
policies
trace service
generic Stage9 runtime bag
battle-long consumed permit histories
```

`EventBus` remains:

```text
observable facts
```

and must not become lifecycle orchestration, admission, state mutation, or finalization owner.

---

# 24. Frozen implementation phase plan

The implementation plan is frozen as:

```text
9.1
Identity / provenance / Exact Numeric / permit types

9.2
Execution Right + legacy-compatible Finalization

9.3
Target Resolution + holder source-slot ingress

9.4
Typed Settlement + isolated DamageInstance

9.5
Partition + DirectTroopLoss + EffectExecutor production cutover

9.6
NormalAttack + Combo + Assault seam

9.7
Cleave + Chain + Counter

9.8
Full Integration / regressions / architecture tests
```

Every phase must satisfy before exit:

```text
existing tests green
phase tests green
no production stub/TODO service
no forward production dependency
```

Forbidden implementation strategy:

```text
wire production now
→ fill semantic owner/service in a later phase
```

---

# 25. Frozen test gate

Design-time test obligations are frozen:

```text
Runtime invariants
= 42 / 42 enforced/design-enforceable

Gameplay regression contracts
= 45 / 45 mapped/testable

Architecture tests
= 12 / 12 READY
```

The Stage9 implementation must make these green; this design freeze does not claim they are already production test results.

---

# 26. Frozen file-plan snapshot

Round3 independently verified:

```text
NEW production files = 16
MODIFY production files = 17
missing = 0
unnecessary = 0
```

Planned NEW:

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

Planned MODIFY:

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

File path/split is not itself gameplay semantics. A purely implementation-local organization refactor does not require Design Reopen only when all remain unchanged:

```text
same ownership
same dependency direction
same contracts
same phase boundaries
same public semantics
```

Otherwise it is a Design Reopen.

---

# 27. DSTS9-B02 research-debt isolation

The freeze preserves exactly:

```text
EMPIRICAL: OPEN / UNOBSERVED
RUNTIME: CLOSED BY PROJECT_RUNTIME_DEFAULT
DESIGN: NOT BLOCKING
RESEARCH DEBT: YES
```

The runtime default exists only in Distribution local continuation policy for an already-admitted fixed transaction.

It is not empirically proven official behavior and must not be promoted into a generic finalization, admission, settlement, or operation-identity rule.

---

# 28. Change-control policy after Design Freeze

## 28.1 Changes that do NOT require Design Reopen

Only non-semantic changes such as:

```text
private helper naming
import layout
pure code organization
equivalent internal refactor
test fixture naming
non-semantic comments/docs typo
```

are implementation-local, and only if they preserve every frozen design contract.

## 28.2 Changes that REQUIRE Design Reopen

Any change to any of the following requires formal Design Reopen:

```text
gameplay-facing behavior
semantic owner
target identity
operation lifecycle
settlement layers
reaction ordering
admission boundary
finalization owner/barrier
SourceType provenance
SkillSlot domain/order
integerization
permission matrix
phase dependency
Stage8 boundary
public runtime contract
42 invariants
45 regressions
```

Required workflow:

```text
DESIGN REOPEN
→ explicit reason
→ design change
→ targeted audit
→ re-freeze
```

Implementation must never “fix it while here” by silently changing the frozen specification.

---

# 29. P0 change policy

If future state-mechanics research changes a current P0 consumed by Stage9:

```text
P0 change
→ impact analysis
→ Stage9 Design Reopen if affected
```

Stage9 implementation is not allowed to adapt itself around a changed P0 without that impact/reopen decision.

---

# 30. Lifecycle separation

This record freezes the implementation specification only:

```text
STAGE9_DESIGN_FREEZE.md
= design/specification freeze record
```

It is intentionally distinct from the future:

```text
STAGE9_FREEZE_RECORD.md
= final production implementation freeze record
```

The latter must not be created until Stage9 production implementation and its final independent audit have completed.

---

# 31. Freeze decision

Current Stage9 state after this status transition:

```text
STATUS = DESIGN FROZEN — FREEZE AUDIT REQUIRED

Stage9 Design Frozen = YES
Stage9 Final Implementation Frozen = NO

Design Audit Round 3 = PASS
Design Freeze Admission = ELIGIBLE / CONSUMED

Implementation specification = FROZEN
Implementation Design Ready = YES

Build Prompt Admission = PENDING FREEZE AUDIT
Build Prompt Authoring = PENDING FREEZE AUDIT
Production Implementation = NOT STARTED
```

No Build Prompt is authorized by this record.

No production implementation is authorized by this record.

The next allowed workflow step is exactly:

```text
Stage9 Design Freeze Audit
```

The Freeze Audit must verify that this freeze commit is a status/record/navigation transition only and that the Round3-audited semantic design body remains unchanged.

Expected Freeze Audit self-check input:

```text
semantic design-body changes = 0
P0 changes = 0
Stage8 changes = 0
production changes = 0
test changes = 0
state repo changes = 0
```

Final Design Freeze verdict for this transition:

```text
STAGE9 DESIGN FROZEN — FREEZE AUDIT REQUIRED
```
