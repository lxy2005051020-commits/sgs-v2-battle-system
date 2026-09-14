# Stage 10 · Persistent State Runtime Integration

> Status: `ARCHITECTURE DESIGN DRAFT / DESIGN AUDIT REQUIRED`
>
> Production implementation: `NOT AUTHORIZED`
>
> Battle design baseline: `stage10-persistent-state-research` from battle `main` `6824fbd36e8188274b80da5815cdca2abf7e4b5b`
>
> Research branch baseline before this document: `4057ec88e1fdfb2fec5db4cc1977cc0942aa51d3`
>
> Gameplay authority repository: `lxy2005051020-commits/sgs-state-mechanics-research`
>
> Gameplay authority main at authoring: `61f2be7e87e6bfab1433657ee7f766ae0c53da9d`

---

# 0. Authority and admission state

Stage10 consumes already frozen mechanism contracts. It does not reopen gameplay research merely because the current runtime cannot yet represent those contracts.

Authority priority:

```text
1. current frozen per-state MECHANISM_CONTRACT.md
2. current frozen family methodology contracts
3. STAGE10_RESEARCH_MATRIX.md
4. STAGE10_RUNTIME_MAPPING.md
5. STAGE10_OPEN_QUESTIONS.md
6. this STAGE10.md architecture design
7. implementation convenience
```

If this design contradicts current gameplay authority, gameplay authority wins and Stage10 design must be repaired before implementation.

Current admission state:

```text
Mechanism research extraction = COMPLETE
Runtime mapping research       = COMPLETE
Architecture design            = THIS DOCUMENT
Independent design audit       = REQUIRED
Build Prompt                    = NOT AUTHORIZED
Production implementation      = NOT AUTHORIZED
```

Target states:

```text
690072 BURN / 灼烧
690073 FLOOD / 水攻
690074 POISON / 中毒
690075 ROUT / 溃逃
690076 SANDSTORM / 沙暴
690077 REBELLION / 叛逃
690078 FIRST_AID / 急救
690079 RECUPERATION / 休整
```

---

# 1. Stage10 goals

Stage10 must convert the eight frozen state contracts into one coherent production runtime binding while preserving the frozen ownership model established by Stage7, Stage8 and Stage9.

The target architecture must provide:

```text
one persistent-state storage truth
one state mutation owner
one action-start trigger family
one continuous-damage runtime family
one action-start recovery family
one after-damage recovery trigger path
application-time frozen potency/context
source-death-safe persistent attribution
same-name refresh-and-overwrite
owner-relative duration semantics
Stage9 operation identity for periodic damage
central RecoverySystem / TroopSystem mutation
central runtime RNG
explicit external-dependency seams
```

Completion means the eight official state definitions have an auditable runtime contract. It does not mean every source skill has already obtained exact microscopic numeric formula research.

---

# 2. Non-goals

Stage10 does **not**:

```text
invent exact DOT nonlinear constants
invent exact treatment nonlinear constants
reverse-engineer the PRNG algorithm
implement EVASION / BARRIER full official state mechanics
implement CRITICAL / STRATEGY_CRITICAL full official state mechanics
implement universal positive dispel
implement FALSE_REPORT / morale-shake source systems
implement command-aura lifecycle as a persistent-state-owned system
implement Elephant Soldiers FLOOD delay
implement skills that merely observe BURN/FLOOD/POISON/etc.
create a second damage engine
create a second state registry
replace Stage9 finalization / FutureAdmission
turn EventBus into a rule engine
```

Numeric formula research may later supply authoritative application-time potency inputs without reopening the Stage10 lifecycle topology.

---

# 3. Frozen ownership map

| Concern | Authoritative owner after Stage10 |
|---|---|
| Physical state storage | `BattleContext.states / StateRegistry` |
| State apply / refresh / remove / expire | `StateLifecycleSystem` |
| Action progress fact | new `ActionProgressTracker` |
| Action-start trigger collection | Stage7 `TriggerSystem` |
| Action-start effect execution | Stage7 `RuleHookSystem` + `EffectExecutor` |
| After-damage trigger collection | Stage7 `TriggerSystem` |
| After-damage recovery execution | new `AfterDamageHookSystem` + `RecoverySystem` |
| Runtime RNG | `BattleContext.random` |
| Recovery policy | `RecoverySystem` |
| Troop mutation | `TroopSystem` |
| Standard theoretical damage | `DamageSystem.calculate()` |
| Periodic damage operation identity | Stage9 `DamageInstanceCoordinator` |
| Partition / share / distribution | Stage9 orchestration |
| Chain / admitted secondary work | Stage9 callback/admission owners |
| Battle termination / drain | `BattleFinalizationCoordinator` |

No other module may become a second physical owner of these facts.

---

# 4. Stage10 blocker closure summary

This design closes the four P0 blockers as follows.

## S10-B01 · Snapshot-backed continuous-damage ingress

Decision:

```text
Introduce a typed FROZEN_APPLICATION calculation basis
inside the existing DamageSystem.calculate() entry.
```

The persistent state carries an immutable `FrozenContinuousDamageBasis` created at application/refresh. Tick-time damage does not reconstruct potency from current source runtime.

A narrowly scoped Stage8 compatibility reopen is therefore REQUIRED and explicitly authorized by this design. See section 5.

## S10-B02 · Source-dead persistent damage

Decision:

```text
FROZEN_APPLICATION periodic damage validates historical source identity,
not current source combat eligibility.
```

The target must still exist and be alive. The original source unit must still be identifiable for provenance, but `source.troops <= 0` does not invalidate an already-existing persistent state tick.

This exception is legal only when all of the following are true:

```text
DamageSourceType.CONTINUOUS
+
SourceType.PERIODIC_DAMAGE
+
valid source_state_id
+
valid source_state_instance_id
+
valid FrozenContinuousDamageBasis
```

Standard/live damage retains the existing alive-source requirement.

## S10-B03 · FIRST_AID exact AFTER_DAMAGE checkpoint

Decision:

```text
AFTER_DAMAGE is a synchronous DamageInstance-local aftermath microstep.
```

It occurs after authoritative target settlement is known, before normal resolved-damage callback fanout and before the DamageInstance is completed.

It does not create a new global future branch and therefore does not add a `FutureBranchKind`.

## S10-B04 · Owner-relative action-start expiration

Decision:

```text
finite persistent lifecycle = typed PersistentLifecycleWindow
anchored by owner action progress, not ROUND_END conversion.
```

The runtime tracks whether the owner already reached action start in the current combat round and derives first/last eligible rounds accordingly.

---

# 5. Explicit Stage8 limited compatibility reopen

## 5.1 Why reopen is required

Current Stage8 freezes:

```text
DamageSystem.calculate()
= unique theoretical damage entry

standard source participant
= existing + alive

formula inputs
= current UnitRuntime
```

The frozen Stage10 mechanism authority requires:

```text
application/refresh potency context is locked
runtime source changes do not recalculate old instance
source death does not cancel old instance
```

These contracts cannot both be satisfied by the current live-source-only path.

Therefore Stage10 explicitly authorizes a **limited Stage8 compatibility reopen**.

This is not a formula reopen.

## 5.2 Reopen scope

Allowed Stage8 changes:

```text
1. add typed calculation-basis discrimination to DamageRequest
2. add typed FrozenContinuousDamageBasis input
3. make participant validation basis-aware
4. make DamagePipelineTrace identify LIVE_RUNTIME vs FROZEN_APPLICATION
5. allow FROZEN_APPLICATION to reuse frozen application potency after dynamic prevention/hit gates
6. preserve existing DamageResult / Stage9 settlement contracts
```

Forbidden Stage8 changes:

```text
base formula mathematical rewrite
F(N) rewrite
morale formula rewrite
weapon/strategy random range rewrite
low-damage-floor rewrite
modifier arithmetic reinterpretation
prevention order change
hit order change
Dtotal/Dtarget/ActualTargetTroopLoss meaning change
DamageResolutionSystem settlement ownership change
TroopSystem ownership change
```

## 5.3 Backward compatibility hard gate

For every existing request that does not explicitly provide a frozen application basis:

```text
calculation_basis = LIVE_RUNTIME
```

The following must remain byte-for-byte / value-for-value equivalent for deterministic seeded tests:

```text
DamageResult
DamagePipelineTrace
RNG consumption
exceptions
EventBus facts after settlement
Stage9 operation identity
```

A Stage10 implementation that changes ordinary live damage in order to support DOT fails the design.

---

# 6. Damage calculation basis contract

Stage10 freezes two explicit calculation basis modes.

```text
DamageCalculationBasis
- LIVE_RUNTIME
- FROZEN_APPLICATION
```

Conceptual request shape:

```python
DamageRequest(
    source_id,
    target_id,
    damage_type,
    source_type,
    coefficient=1.0,
    source_skill_id=None,
    source_state_id=None,
    source_state_instance_id=None,
    calculation_basis=DamageCalculationBasis.LIVE_RUNTIME,
    frozen_application_basis=None,
)
```

Validation:

```text
LIVE_RUNTIME
→ frozen_application_basis is None
→ existing participant validation unchanged

FROZEN_APPLICATION
→ source_type == CONTINUOUS
→ source_state_id != None
→ source_state_instance_id != None
→ frozen_application_basis != None
→ frozen basis damage_type matches request.damage_type
```

No caller may use `FROZEN_APPLICATION` as a general way to make dead units attack.

---

# 7. FrozenContinuousDamageBasis

## 7.1 Purpose

`FrozenContinuousDamageBasis` represents the already-resolved application/refresh potency of one effective continuous-damage state instance.

It is a typed **input contract**, not an executable mini-engine.

The Stage10 state runtime does not infer the exact microscopic source-skill formula from live UnitRuntime at tick time.

## 7.2 Minimum semantic fields

Conceptual contract:

```python
@dataclass(frozen=True, slots=True)
class FrozenContinuousDamageBasis:
    damage_type: DamageType
    nominal_damage: int
    defense_policy: DamageDefensePolicy
    locked_modifier_context: FrozenDamageModifierContext
    locked_crit_context: FrozenCritContext | None
    potency_origin: PersistentPotencyOrigin
```

Required invariants:

```text
nominal_damage is int
bool rejected
nominal_damage >= 0
all values immutable
no UnitRuntime object stored
no mutable StateInstance stored
no callable stored
no untyped dict snapshot
```

`nominal_damage` means:

```text
application/refresh-time nominal theoretical damage
with the contractually locked potency context already resolved,
before tick-time dynamic weakness/evasion/barrier gates.
```

It is not:

```text
Dtarget
after-partition damage
actual troop loss
direct troop loss
```

## 7.3 Formula research boundary

The exact producer of `nominal_damage` belongs to the source skill/effect formula layer.

Stage10 freezes only:

```text
once the source effect successfully applies/refreshes a persistent damage state,
it must provide a valid FrozenContinuousDamageBasis;
that basis is authoritative for later ticks until refresh/removal.
```

Synthetic and fixture producers may be used to validate Stage10 topology. Individual production source skills are admitted only when they can provide evidence-backed potency input.

This preserves the existing project decision that microscopic constants are formula research rather than state-lifecycle research.

## 7.4 REBELLION

REBELLION basis additionally requires:

```text
route fixed at application/refresh
DamageType = WEAPON or STRATEGY
DefensePolicy = IGNORE_RELEVANT_TARGET_DEFENSE
```

Runtime ATK/INT changes never reroute an existing basis.

A refresh creates a new basis and may choose a different route.

---

# 8. FROZEN_APPLICATION DamageSystem semantics

For `FROZEN_APPLICATION`:

```text
validate historical provenance + live target
↓
collect only tick-dynamic prevention/hit rules
↓
DamagePreventionSystem
↓
HitResolutionSystem
↓
validate/reuse FrozenContinuousDamageBasis
↓
final theoretical damage = frozen basis nominal_damage
↓
DamageResult
```

The live formula and current ordinary modifier calculation are not rerun.

This is intentional because those semantics are already represented by the application basis.

The implementation must not accidentally collect current ordinary source/target modifier contributions and apply them a second time.

## 8.1 Dynamic tick gates

The prepared lane remains dynamic for:

```text
source weakness
future official evasion
future official barrier
owner alive
battle/finalization admission
```

These are not part of the application basis.

## 8.2 Pipeline trace

Stage10 must not lie in traces.

`DamagePipelineTrace` gains a basis field conceptually:

```text
calculation_basis = LIVE_RUNTIME | FROZEN_APPLICATION
```

For FROZEN_APPLICATION the trace must clearly show that live formula/modifier computation was not rerun.

The design audit may choose either:

```text
A. extend StageEvaluationStatus with a typed REUSED_FROZEN_INPUT value
or
B. add separate prepared-basis trace fields while preserving the current two-value status enum
```

but it may not label a skipped live computation as an ordinary fresh live execution without provenance.

This is the only intentionally unresolved representation choice allowed in this document; the design audit must select one before `STAGE10_DESIGN_FREEZE.md`.

---

# 9. Historical source provenance and source death

For a valid persistent damage instance:

```text
source_id
source_skill_id
source_skill_slot
source_state_id
source_state_instance_id
```

remain authoritative credit facts even after the source unit dies.

`FROZEN_APPLICATION` validation therefore distinguishes:

```text
historical source identity exists
from
source currently has execution right
```

Persistent tick rule:

```text
source exists in battle identity graph     REQUIRED
source alive                               NOT REQUIRED
source currently able to take an action    NOT REQUIRED
source weakness at tick                    DYNAMIC gate
```

No generic standard attack/skill request inherits this exception.

---

# 10. Persistent StateRuntimeParams model

Stage10 replaces synthetic Stage7 official-state DEFER usage with typed official params.

Conceptual types:

```text
ContinuousDamageStateParams
FirstAidStateParams
RecuperationStateParams
```

The exact module name may be `stage10_state_params.py`.

## 10.1 Shared lifecycle type

```python
@dataclass(frozen=True, slots=True)
class PersistentLifecycleWindow:
    first_eligible_round: int
    last_eligible_round: int | None
    last_processed_round: int | None
    duration_kind: FINITE_ROUNDS | UNTIL_BATTLE_END | EXTERNAL_SOURCE_LIFECYCLE
```

For finite N-round instances:

```text
last_eligible_round = first_eligible_round + N - 1
```

For battle-long or externally owned lifecycle:

```text
last_eligible_round = None
```

`last_processed_round` prevents a second same-state opportunity for the same owner in one combat round.

## 10.2 ContinuousDamageStateParams

Minimum semantics:

```text
frozen_basis: FrozenContinuousDamageBasis
lifecycle: PersistentLifecycleWindow
active_gate: PersistentSourceSkillGate
```

`active_gate` is normally ALWAYS_ACTIVE for active-skill-applied continuous damage unless a specific contract says otherwise.

## 10.3 FirstAidStateParams

Minimum semantics:

```text
probability: float [0,1]
recovery_model: TREATMENT_AMOUNT | TRIGGER_DAMAGE_RATIO
frozen_recovery_context: FrozenRecoveryApplicationContext
lifecycle: PersistentLifecycleWindow
active_gate: PersistentSourceSkillGate
```

For damage-ratio model:

```text
triggering ActualTargetTroopLoss
```

is read dynamically from `AfterDamageHook`.

## 10.4 RecuperationStateParams

Minimum semantics:

```text
recovery_model
frozen_recovery_context
lifecycle
active_gate
```

No generic flat `amount` field is sufficient as the official model.

---

# 11. ActionProgressTracker

## 11.1 Purpose

State application must know whether the target already reached action start in the current combat round.

`context.current_phase` alone cannot answer this because multiple units pass through the same global phase value.

EventBus history is not an allowed control-flow database.

Therefore Stage10 introduces one typed battle-local fact owner:

```text
ActionProgressTracker
```

## 11.2 Contract

Conceptual API:

```text
mark_action_start(round_no, actor_id)
has_started_this_round(round_no, actor_id) -> bool
last_started_round(actor_id) -> int | None
```

Rules:

```text
BattleEngine marks action start exactly once before processing UnitActionStartHook.
TriggerSystem may read the tracker.
StateLifecycleSystem may read the tracker while applying/refreshing a persistent state.
No state-specific behavior lives inside the tracker.
No EventBus inspection is used.
```

The tracker is an execution fact, not a second StateRegistry.

---

# 12. Persistent lifecycle window derivation

For an incoming finite state with duration N at combat round R:

```text
if owner has NOT reached action start in R:
    first_eligible_round = R
else:
    first_eligible_round = R + 1

last_eligible_round = first_eligible_round + N - 1
last_processed_round = None
```

This rule applies on both first application and refresh.

Examples:

```text
2-round DOT applied before owner acts in round 3
→ eligible rounds 3,4
→ expires at owner action start round 5 before a tick

2-round DOT applied after owner acts in round 3
→ eligible rounds 4,5
→ expires at owner action start round 6 before a tick
```

There is no round-end catch-up.

---

# 13. UnitActionStart persistent-state lifecycle algorithm

At `UnitActionStartHook(round_no=R, actor_id=A)` the persistent-state trigger path processes A's matching persistent states deterministically.

For each state instance:

```text
1. owner alive check
2. lifecycle expiration check
3. same-round duplicate opportunity check
4. mark this round as processed when an opportunity belongs to this round
5. source-skill active gate
6. state-specific trigger eligibility
7. produce DamageEffect or RecoverEffect
```

## 13.1 Expiration rule

For finite state:

```text
if R > last_eligible_round:
    remove/expire before producing an effect
```

For `R == last_eligible_round`:

```text
one final opportunity may occur
state is not required to disappear until the next owner action-start expiration check
```

This matches the frozen observable rule that no N+1 opportunity occurs.

## 13.2 Temporary inactive opportunity

If the state belongs to an inactive command/passive/troop source at an otherwise eligible action start:

```text
mark R processed
produce no trigger effect
no RNG where the contract says execution itself is suppressed
do not extend last_eligible_round
no catch-up later
```

---

# 14. Same-name refresh-and-overwrite transaction

All eight Stage10 states freeze one effective same-name instance per owner.

Stage10 chooses an explicit **atomic refresh** operation owned by `StateLifecycleSystem`.

Conceptual API:

```text
apply_or_refresh_persistent(...)
```

If no existing same-name instance exists:

```text
create new StateInstance
publish STATE_APPLIED
```

If one exists:

```text
atomically replace source/source skill/source slot/runtime params/application context/lifecycle
preserve one physical registry record
publish STATE_REFRESHED
```

## 14.1 Instance identity decision

Stage10 freezes:

```text
refresh RETAINS the physical StateInstance.instance_id
```

Reason:

```text
refresh is one continuing same-name effective state slot on the owner,
not a remove event followed by an observable gap;
keeping identity avoids fake STATE_REMOVED + STATE_APPLIED semantics.
```

All gameplay-relevant content of the effective instance is replaced.

The retained physical instance ID does **not** mean old potency/provenance survives.

## 14.2 New event

Add:

```text
EventType.STATE_REFRESHED
```

Payload includes at minimum:

```text
instance_id
state_id
owner_id
old source provenance
new source provenance
new lifecycle window
new runtime params type
```

EventBus remains observation-only.

## 14.3 Generic scope boundary

This refresh law applies only to the eight Stage10 states admitted by explicit state IDs / typed definitions.

It is not a global stacking law for all official states.

---

# 15. Trigger ordering at the same action-start node

Research does not freeze a universal “DOT before RECUPERATION” family priority.

Stage10 therefore freezes an engineering determinism rule:

```text
matching StateInstances are processed by stable physical instance_id order
```

This is labeled:

```text
RUNTIME DETERMINISM DEFAULT
NOT OFFICIAL FAMILY PRIORITY
```

Refresh retaining physical instance ID also means refresh does not accidentally move the state to another same-node ordering position.

If later evidence proves an official cross-state priority, this ordering rule may be reopened without changing the basic trigger topology.

---

# 16. Periodic damage effect production

A continuous state tick produces a standard `DamageEffect` with:

```text
source_id                = state source
source_skill_id          = state source skill
source_state_id          = state id
source_state_instance_id = physical state instance id
damage_type               = frozen basis damage type
source_type               = DamageSourceType.CONTINUOUS
source_ref.stage9_source_type = SourceType.PERIODIC_DAMAGE
frozen_application_basis  = params.frozen_basis
```

It then enters:

```text
EffectExecutor
→ DamageInstanceCoordinator
→ DamageSystem.calculate(FROZEN_APPLICATION)
→ Stage9 partition / settlement
→ finalization barrier
```

No direct troop loss route is authorized.

---

# 17. FIRST_AID typed AfterDamageHook

Stage10 adds:

```python
@dataclass(frozen=True, slots=True)
class AfterDamageHook:
    round_no: int
    damage_instance_id: DamageInstanceId
    lineage: OperationLineage
    source_id: str | None
    target_id: str
    damage_type: DamageType
    source_type: SourceType
    assigned_target_damage: int
    actual_target_troop_loss: int
    prevented: bool
    target_defeated: bool
    source_state_id: str | None
    source_state_instance_id: str | None
```

The exact field names may be refined during implementation, but the semantic facts above are mandatory.

The hook is immutable and may not query EventBus history to reconstruct missing facts.

---

# 18. AFTER_DAMAGE exact checkpoint

For standard Stage9 damage:

```text
Stage8 theoretical calculation
↓
Stage9 partition planning
↓
standard target settlement
↓
DamageResolutionResult exists
↓
construct AfterDamageHook
↓
FIRST_AID synchronous aftermath processing
↓
resolved-damage callback fanout (Chain etc.)
↓
finish current DamageInstance
```

For Share:

```text
target settlement
→ FIRST_AID on target if eligible
→ share direct troop loss
```

For Distribution:

```text
distribution direct losses
→ target settlement
→ FIRST_AID on target if eligible
```

Partition direct losses are not reclassified as standard damage events and do not automatically create FIRST_AID opportunities.

For Cleave derived damage:

```text
derived target troop settlement
→ typed AfterDamageHook using the derived DamageInstance fact
→ FIRST_AID
→ existing damage callback fanout
```

The existing Stage9 evidence-gated `cleave_first_aid` seam is replaced/bound by the same Stage10 aftermath service rather than becoming a second FIRST_AID implementation.

---

# 19. Why AFTER_DAMAGE is synchronous local work

FIRST_AID recovery:

```text
does not create damage
does not choose a new combat target
does not schedule another action
does not create a global branch
does not require work after the owning DamageInstance closes
```

Therefore Stage10 classifies it as:

```text
DamageInstance-local synchronous aftermath microstep
```

It is **not** a new `FutureBranchKind`.

If a future mechanism requires delayed/replayable work outside this scope, that future mechanism must go through FutureAdmission separately.

---

# 20. Acyclic AfterDamage architecture

Stage7 originally deferred AFTER_DAMAGE because naive wiring would create:

```text
DamageInstanceCoordinator
→ RuleHookSystem
→ EffectExecutor
→ DamageInstanceCoordinator
```

Stage10 explicitly forbids this cycle.

Instead:

```text
Damage aftermath callback point
        ↓
AfterDamageHookSystem
        ↓
TriggerSystem.collect(context, AfterDamageHook)
        ↓
RecoverEffect(s) ONLY
        ↓
RecoverySystem
        ↓
TroopSystem.restore
```

`AfterDamageHookSystem` does **not** depend on `EffectExecutor`.

It validates that every effect returned for `AfterDamageHook` is a `RecoverEffect`. A `DamageEffect`, `ApplyStateEffect`, `RemoveStateEffect`, or unknown Effect at this hook is a programmer/design error in Stage10.

This preserves:

```text
TriggerSystem = pure trigger rule collector
RecoverySystem = recovery policy owner
DamageInstanceCoordinator = damage owner
runtime dependency graph = acyclic
```

---

# 21. FIRST_AID eligibility and RNG order

For one `AfterDamageHook`, FIRST_AID processing order is frozen:

```text
1. locate effective FIRST_AID state on target
2. if none -> stop
3. if hook.prevented -> stop
4. if actual_target_troop_loss <= 0 -> stop
5. if target_defeated -> stop
6. verify target is currently alive -> otherwise stop
7. evaluate source-skill active gate
8. if inactive -> stop
9. consume exactly one context.random.chance(probability)
10. failure -> stop
11. compute nominal recovery from frozen recovery context
12. construct RecoverEffect with state + damage provenance
13. RecoverySystem applies dynamic healing-ban / target-alive policy
14. TroopSystem.restore applies current missing-troop cap
```

Important consequences:

```text
fatal damage consumes NO FIRST_AID RNG
prevented damage consumes NO FIRST_AID RNG
zero actual troop loss consumes NO FIRST_AID RNG
inactive source-skill window consumes NO FIRST_AID RNG
healing ban is checked by RecoverySystem AFTER successful trigger chance
```

The last point preserves the frozen separation between trigger probability and recovery prevention.

No combat-round cap exists.

---

# 22. FIRST_AID recovery amount models

Stage10 freezes two model kinds:

```text
TREATMENT_AMOUNT
TRIGGER_DAMAGE_RATIO
```

For `TREATMENT_AMOUNT`:

```text
nominal amount is determined from FrozenRecoveryApplicationContext
```

For `TRIGGER_DAMAGE_RATIO`:

```text
basis = AfterDamageHook.actual_target_troop_loss
ratio = application-time frozen ratio
nominal recovery = evidence-backed integerization of basis × ratio
```

The exact source-skill ratio formula/rounding is supplied by the source skill formula authority.

Stage10 does not substitute `assigned_target_damage` or `Dtotal` for the frozen “当次受击扣减伤害量” contract.

---

# 23. RECUPERATION action-start flow

At an eligible owner action start:

```text
lifecycle opportunity check
↓
mark current round processed
↓
source-skill active gate
↓
if inactive: lose opportunity, no catch-up
↓
resolve nominal recovery from FrozenRecoveryApplicationContext
↓
RecoverEffect
↓
RecoverySystem
↓
healing-ban / target-alive gate
↓
TroopSystem.restore missing-troop cap
```

Stun/disarm/silence/weakness/confusion do not inherently suppress the RECUPERATION trigger once the owner reached its action-start node.

---

# 24. FrozenRecoveryApplicationContext

Stage10 requires a typed recovery application snapshot.

Conceptual contract:

```python
@dataclass(frozen=True, slots=True)
class FrozenRecoveryApplicationContext:
    potency_model: RecoveryPotencyModel
    nominal_amount: int | None
    trigger_damage_ratio: ExactRatio | None
    locked_modifier_context: FrozenRecoveryModifierContext
    potency_origin: PersistentPotencyOrigin
```

Validation enforces legal combinations:

```text
TREATMENT_AMOUNT
→ nominal_amount present
→ trigger_damage_ratio absent

TRIGGER_DAMAGE_RATIO
→ trigger_damage_ratio present
→ nominal_amount absent or only used as source-specific typed parameter when explicitly authorized
```

No mutable UnitRuntime or untyped dict snapshot is stored.

---

# 25. Recovery provenance extension

`RecoverEffect` and `RecoveryRequest` receive backward-compatible optional provenance extensions after existing constructor fields.

Required facts:

```text
source_skill_slot
trigger_damage_instance_id
trigger_lineage / equivalent immutable operation reference
```

For RECUPERATION:

```text
trigger_damage_instance_id = None
trigger_lineage = None
```

For FIRST_AID:

```text
trigger_damage_instance_id = AfterDamageHook.damage_instance_id
trigger lineage = AfterDamageHook.lineage
```

RecoverySystem does not use these facts to decide arithmetic except where a future explicit contract says so. It preserves/publishes them for audit and report provenance.

Existing Stage7 callers that omit the new optional fields retain old behavior.

---

# 26. PersistentSourceSkillGate

FIRST_AID and RECUPERATION sometimes remain physically present while the source skill is temporarily ineffective.

Stage10 freezes a typed gate abstraction:

```text
PersistentSourceSkillGate
- ALWAYS_ACTIVE
- QUERY_SKILL_RUNTIME
- EXTERNAL_LIFECYCLE
```

For `QUERY_SKILL_RUNTIME`, the state retains:

```text
source_id
source_skill_id
source_skill_slot
```

and queries one authoritative skill-runtime effectiveness service.

## 26.1 Existing SkillRuntime fact

Current `SkillRuntime` already has:

```text
enabled: bool
```

Stage10 may reuse/extend the authoritative runtime that owns this flag.

It must not duplicate FALSE_REPORT / morale-shake truth inside persistent-state params.

## 26.2 Missing authoritative runtime case

If implementation discovery proves there is no battle-authoritative lookup from `(source_id, skill_slot)` to current SkillRuntime effectiveness, construction stops and records an implementation blocker.

The implementation may add a typed skill-runtime registry/lookup owner, but may not invent the external disable gameplay itself.

---

# 27. Official state definition bindings

Stage10 promotes the eight target state definitions from `EmptyStateRuntimeParams` to explicit typed params.

Binding:

```text
BURN        -> ContinuousDamageStateParams + RULE_HOOK:UNIT_ACTION_START
FLOOD       -> ContinuousDamageStateParams + RULE_HOOK:UNIT_ACTION_START
POISON      -> ContinuousDamageStateParams + RULE_HOOK:UNIT_ACTION_START
ROUT        -> ContinuousDamageStateParams + RULE_HOOK:UNIT_ACTION_START
SANDSTORM   -> ContinuousDamageStateParams + RULE_HOOK:UNIT_ACTION_START
REBELLION   -> ContinuousDamageStateParams + RULE_HOOK:UNIT_ACTION_START
RECUPERATION-> RecuperationStateParams     + RULE_HOOK:UNIT_ACTION_START
FIRST_AID   -> FirstAidStateParams         + RULE_HOOK:AFTER_DAMAGE
```

The tag names are runtime selectors, not gameplay authority.

State IDs remain the canonical existing identifiers from `OfficialStateId`.

---

# 28. Evidence Gate promotion

Stage10 must update evidence matrices explicitly.

At minimum:

```text
Stage7
burn / flood / poison / rout / sandstorm / rebellion / recuperation
→ promoted for official action-start trigger binding

first_aid
→ promoted only for Stage10 typed AFTER_DAMAGE + Recovery path

Stage8
rebellion defense-ignore
→ promoted from DEFER for the specific frozen formula-policy meaning

continuous damage prepared-basis mode
→ Stage10 evidence-backed architecture extension
```

The following remain DEFER unless separately frozen:

```text
EVASION official binding
BARRIER official binding
CRITICAL official binding
STRATEGY_CRITICAL official binding
DAMAGE_REDUCTION_PIERCE official binding
universal positive dispel
```

Synthetic capability tests do not change those verdicts.

---

# 29. Death contracts

## 29.1 State owner death

Global hard termination remains:

```text
owner death
→ clear attached states
→ abort remaining owner-state resolution
→ reject future state application to dead owner
```

Stage10 must identify one authoritative death-cleanup integration point.

It must not add eight independent UNIT_DEFEATED EventBus subscribers.

## 29.2 Source death

No generic sourced-state deletion is allowed.

```text
continuous damage existing instance -> persists
FIRST_AID existing instance          -> persists
active-sourced RECUPERATION          -> persists
command-aura RECUPERATION            -> external lifecycle may remove it
```

---

# 30. Finalization and victory boundary

## 30.1 Periodic damage admission

A new periodic tick is produced from an already-admitted `UnitActionStartHook` while the battle is RUNNING.

The resulting DamageInstance uses existing Stage9 admission and finalization rules.

If the battle has already latched/finalized before a new action-start hook can legally run, no new persistent damage is created.

## 30.2 FIRST_AID during DamageInstance drain

FIRST_AID is part of the already-admitted DamageInstance's local aftermath.

Therefore it may finish while the coordinator is draining that same already-admitted DamageInstance.

Fatal target damage suppresses FIRST_AID before RNG, so FIRST_AID cannot resurrect a defeated target and cannot invalidate a victory caused by that target death.

If a different partition participant death already latched victory earlier in the same admitted DamageInstance, a nonfatal target's local FIRST_AID may still complete before the DamageInstance closes. This is classified as drain of already-admitted local work, not admission of new future work.

---

# 31. Dynamic external interactions

Stage10 preserves explicit seams for:

```text
Evasion / Barrier
Critical / Strategy Critical
positive dispel
command aura source death
FALSE_REPORT / morale-shake source skill deactivation
Elephant Soldiers FLOOD delay
external observers of persistent state identity
cleanse target-selection policy
```

Persistent state runtime may query or receive typed facts from these owners when they exist.

It must not silently absorb their full gameplay semantics.

---

# 32. Required dependency graph

Target dependency direction:

```text
BattleEngine
  -> ActionProgressTracker
  -> RuleHookSystem

RuleHookSystem
  -> TriggerSystem
  -> EffectExecutor

EffectExecutor
  -> DamageInstanceCoordinator
  -> StateLifecycleSystem
  -> RecoverySystem

DamageInstanceCoordinator
  -> DamageSystem
  -> Stage9 partition/finalization
  -> Damage aftermath callback point

Damage aftermath callback point
  -> AfterDamageHookSystem
  -> existing Stage9 damage callbacks

AfterDamageHookSystem
  -> TriggerSystem
  -> RecoverySystem

RecoverySystem
  -> TroopSystem
```

Forbidden dependency:

```text
AfterDamageHookSystem -> EffectExecutor
```

because that closes a cycle back into `DamageInstanceCoordinator`.

Runtime dependency-cycle count must remain zero.

---

# 33. Required invariants

Stage10 implementation must prove at least the following invariants.

```text
S10-I01 one physical StateRegistry
S10-I02 one StateLifecycleSystem mutation owner
S10-I03 one effective same-name Stage10 state per owner
S10-I04 refresh replaces all effective provenance/potency/lifecycle fields
S10-I05 refresh retains physical instance_id and emits STATE_REFRESHED only
S10-I06 no fake remove/apply gap on refresh
S10-I07 application-before-owner-action may trigger same round
S10-I08 application-after-owner-action cannot catch up same round
S10-I09 finite N-round state cannot produce N+1 opportunity
S10-I10 same state cannot produce second action-start opportunity in same combat round
S10-I11 inactive opportunity is lost without duration extension
S10-I12 DOT tick never recalculates potency from live source UnitRuntime
S10-I13 source death does not invalidate existing DOT
S10-I14 live standard damage still requires alive source
S10-I15 periodic damage retains Stage9 PERIODIC_DAMAGE identity
S10-I16 periodic damage never uses DirectTroopLoss as a shortcut
S10-I17 REBELLION route remains fixed until refresh
S10-I18 REBELLION frozen basis carries IGNORE_RELEVANT_TARGET_DEFENSE
S10-I19 FIRST_AID one eligible damage settlement = one chance opportunity
S10-I20 FIRST_AID has no combat-round cap
S10-I21 prevented/zero/fatal damage consumes no FIRST_AID RNG
S10-I22 FIRST_AID uses ActualTargetTroopLoss for damage-ratio model
S10-I23 healing ban remains RecoverySystem-owned
S10-I24 missing-troop clamp remains TroopSystem-owned
S10-I25 EventBus never drives FIRST_AID rule execution
S10-I26 AfterDamageHookSystem cannot emit/execute damage
S10-I27 runtime dependency graph remains acyclic
S10-I28 source-skill disable truth is not copied into a second store
S10-I29 owner death hard-terminates attached persistent state execution
S10-I30 standard Stage1-9 regression semantics remain unchanged outside explicit Stage8 reopen scope
```

---

# 34. Mandatory regression scenarios

Design audit and later build prompt must require tests for at least:

```text
1. 1-round DOT applied before target acts -> same-round one tick, no next-round tick
2. 1-round DOT applied after target acts -> next-round one tick only
3. 2-round DOT exact two opportunities
4. same-source refresh before owner action
5. cross-source refresh after owner action
6. refresh replaces source provenance
7. refresh replaces frozen potency
8. refresh may reroute REBELLION
9. source dies after applying DOT -> later tick still resolves
10. source attribute changes after apply -> old DOT unchanged
11. source modifier changes after apply -> old DOT unchanged
12. dynamic weakness blocks one tick without deleting state
13. stun/disarm/silence do not suppress eligible action-start tick
14. owner death clears state and prevents later tick
15. purify removal prevents future tick
16. RECUPERATION same-round first opportunity
17. RECUPERATION after-action deferred first opportunity
18. RECUPERATION inactive window loses opportunity, duration not extended
19. FIRST_AID normal attack damage opportunity
20. FIRST_AID skill damage opportunity
21. FIRST_AID periodic damage opportunity
22. FIRST_AID two multi-hit DamageInstances -> two chance opportunities
23. FIRST_AID prevented hit -> no RNG
24. FIRST_AID fatal hit -> no RNG / no resurrection
25. FIRST_AID damage-ratio reads actual troop loss, not Dtotal
26. FIRST_AID under healing ban -> chance may succeed, RecoverySystem prevents recovery
27. share target settlement FIRST_AID occurs before sharer direct loss
28. distribution direct losses do not automatically trigger FIRST_AID
29. Cleave uses same Stage10 FIRST_AID aftermath service
30. battle-latched admitted DamageInstance may drain local nonfatal FIRST_AID
31. ordinary live DamageRequest result unchanged from Stage9 baseline
32. ordinary dead source standard attack/skill remains rejected
33. no EventBus subscription controls persistent gameplay
34. no runtime dependency cycle
```

External DEFER mechanics use synthetic rule providers where needed; tests must not relabel them as officially integrated.

---

# 35. Implementation phases

Stage10 production work, once design audit passes, should be split so each phase can be independently audited.

## Phase 10.1 · Typed contracts only

```text
DamageCalculationBasis
FrozenContinuousDamageBasis
FrozenRecoveryApplicationContext
PersistentLifecycleWindow
PersistentSourceSkillGate
Stage10 StateRuntimeParams
AfterDamageHook
recovery provenance fields
STATE_REFRESHED event type
```

No production official binding yet.

## Phase 10.2 · Action progress + lifecycle

```text
ActionProgressTracker
BattleEngine explicit mark_action_start
StateLifecycleSystem persistent apply/refresh
owner-relative finite lifecycle maintenance
same-round duplicate prevention
```

## Phase 10.3 · Stage8 limited reopen

```text
FROZEN_APPLICATION request validation
basis-aware participant validation
prepared periodic damage lane
trace representation
strict live-path regression gate
```

No Stage9 or state official activation until this phase passes its own audit.

## Phase 10.4 · Continuous damage family

```text
BURN
FLOOD
POISON
ROUT
SANDSTORM
REBELLION
```

Bind official definitions and periodic damage Stage9 ingress.

## Phase 10.5 · RECUPERATION

```text
action-start recovery
source-skill active gate
finite and battle-long lifecycle
```

## Phase 10.6 · AFTER_DAMAGE + FIRST_AID

```text
AfterDamageHookSystem
standard damage callback integration
Cleave derived damage integration
RNG order
recovery provenance
```

## Phase 10.7 · death / cleanse / external seams hardening

```text
owner-death cleanup integration
purify/remove compatibility
external source-lifecycle seam
DEFER interaction guards
```

## Phase 10.8 · independent implementation audit + final freeze

```text
full pytest twice
full demo
exact-head CI
artifact provenance
architecture invariant audit
mechanism-contract audit
Stage8 limited-reopen regression audit
Stage10 Final Audit
```

---

# 36. Files expected to change during implementation

Likely production surfaces:

```text
sgs_v2/battle_core/rule_hooks.py
sgs_v2/battle_core/trigger_system.py
sgs_v2/battle_core/recovery_system.py
sgs_v2/battle_core/effects.py
sgs_v2/battle_core/effect_result.py
sgs_v2/battle_core/state_lifecycle_system.py
sgs_v2/battle_core/state_instance.py (only if typed lifecycle placement requires it)
sgs_v2/battle_core/official_state_catalog.py
sgs_v2/battle_core/damage_system.py
sgs_v2/battle_core/damage_pipeline_trace.py
sgs_v2/battle_core/damage_instance_coordinator.py
sgs_v2/battle_core/cleave_derived_damage_system.py
sgs_v2/battle_core/battle_systems.py
sgs_v2/battle_core/engine.py
new stage10_state_params.py
new persistent_damage_basis.py or equivalent typed module
new action_progress_tracker.py
new after_damage_hook_system.py
```

This list is not permission for gratuitous rewrites. Any additional production file touched must be justified by a concrete frozen contract or required dependency seam.

---

# 37. Forbidden shortcuts

The Build Prompt must explicitly reject all of the following:

```text
“PeriodicDamageStateParams already works, so official DOT is complete”
recalculate DOT from current source stats every tick
delete sourced DOT when source dies
temporarily revive dead source to satisfy DamageSystem
copy DamageSystem into PersistentDamageSystem
write troops directly for DOT
route DOT through DirectTroopLossSystem
read EventBus history to trigger FIRST_AID
subscribe to DAMAGE_DEALT to execute FIRST_AID
make FIRST_AID one-per-round
use Dtotal for damage-ratio FIRST_AID
heal after fatal damage
pause finite duration while source skill is inactive
convert owner-relative duration to a universal ROUND_END timer
allow multiple effective same-name Stage10 instances
use remove+apply event pair to fake refresh
store application snapshot as dict[str, Any]
store mutable UnitRuntime inside state params
import Python random in state logic
add a FutureBranchKind merely for synchronous FIRST_AID
wire AfterDamageHookSystem through EffectExecutor and recreate a runtime cycle
silently activate EVASION/BARRIER/CRITICAL official bindings
claim engineering instance_id ordering is official state priority
```

---

# 38. Design audit hard gates

`STAGE10_DESIGN_AUDIT.md` must reject this design if any of the following is not proven:

```text
A. all S10-B01..B04 have one unambiguous architecture answer
B. all S10-M01..M06 have one unambiguous architecture answer
C. Stage8 limited reopen scope is explicit and regression-testable
D. standard LIVE_RUNTIME damage behavior remains frozen
E. FROZEN_APPLICATION cannot be abused by arbitrary dead-source standard damage
F. owner-relative lifecycle handles before/after-action application and refresh
G. FIRST_AID checkpoint uses authoritative settlement facts
H. FIRST_AID has no EventBus control-flow dependency
I. AfterDamage architecture is acyclic
J. recovery provenance remains backward compatible
K. external dependency items remain external
L. formula research debt is not silently converted into guessed constants
M. no duplicated state storage or troop mutation owner
N. Stage9 operation identity/finalization semantics remain intact
```

If any gate fails:

```text
DESIGN AUDIT = FAIL
BUILD PROMPT = BLOCKED
```

---

# 39. Open representation item intentionally deferred to design audit

Exactly one internal representation choice remains open for independent review:

```text
How DamagePipelineTrace represents a FROZEN_APPLICATION formula/modifier reuse
without falsely claiming a fresh live computation.
```

Allowed resolution families:

```text
A. extend StageEvaluationStatus with REUSED_FROZEN_INPUT
B. preserve status enum and add typed calculation-basis / frozen-stage trace fields
```

The choice must not change gameplay semantics.

No other P0/P1 item remains intentionally open in this specification.

---

# 40. Architecture decision record

Final Stage10 design decisions:

```text
S10-B01 snapshot-backed ingress
= FROZEN_APPLICATION basis in existing DamageSystem.calculate

S10-B02 source-dead execution
= historical source provenance accepted only for valid periodic frozen-basis request

S10-B03 FIRST_AID checkpoint
= synchronous target-settlement aftermath inside owning DamageInstance

S10-B04 owner-relative expiry
= ActionProgressTracker + PersistentLifecycleWindow

S10-M01 same-name replacement
= StateLifecycleSystem atomic refresh, physical instance_id retained

S10-M02 RNG
= eligibility/death/inactive gates first, then exactly one context.random chance

S10-M03 recovery provenance
= backward-compatible RecoverEffect/RecoveryRequest extension

S10-M04 source skill inactive gate
= typed authoritative skill-runtime query seam, no copied truth

S10-M05 snapshot schema
= immutable typed damage/recovery application contexts, no dict/UnitRuntime capture

S10-M06 state binding / evidence
= explicit official params + hook tags + evidence-matrix promotion
```

---

# 41. Stage10 design verdict

```text
Mechanism research              = COMPLETE
Runtime mapping                 = COMPLETE
P0 architecture decisions       = CLOSED IN DESIGN
P1 architecture decisions       = CLOSED IN DESIGN
Stage8 conflict                 = EXPLICIT LIMITED REOPEN REQUIRED
Stage9 conflict                 = NO REOPEN; additive local aftermath seam only
Formula constants               = OUT OF STAGE10 CORE SCOPE
External dependency semantics   = PRESERVED AS EXTERNAL
Production implementation       = NOT AUTHORIZED

NEXT REQUIRED STEP:
STAGE10_DESIGN_AUDIT.md
```

Only an independent design audit may promote this document to `DESIGN FROZEN` and authorize creation of `STAGE10_BUILD_PROMPT.md`.
