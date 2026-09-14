# Stage 10 · Persistent State Runtime Integration

> Status: `ARCHITECTURE DESIGN DRAFT / DESIGN AUDIT REQUIRED`
>
> Production implementation: `NOT AUTHORIZED`
>
> Battle design baseline: battle `main` `6824fbd36e8188274b80da5815cdca2abf7e4b5b`
>
> Research branch baseline before Stage10 design: `4057ec88e1fdfb2fec5db4cc1977cc0942aa51d3`
>
> Gameplay authority: `lxy2005051020-commits/sgs-state-mechanics-research@61f2be7e87e6bfab1433657ee7f766ae0c53da9d`

---

# 0. Authority and admission

Stage10 consumes already frozen mechanism contracts. Runtime incompatibility is an architecture problem, not permission to rewrite gameplay research.

Authority priority:

```text
1. current frozen per-state MECHANISM_CONTRACT.md
2. current frozen family methodology contracts
3. STAGE10_RESEARCH_MATRIX.md
4. STAGE10_RUNTIME_MAPPING.md
5. STAGE10_OPEN_QUESTIONS.md
6. this STAGE10.md
7. implementation convenience
```

Current state:

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

# 1. Goals

Stage10 must provide one auditable runtime binding for the eight persistent states while preserving Stage7/8/9 ownership boundaries.

Required outcome:

```text
one persistent-state storage truth
one state mutation owner
one action-start trigger family
one continuous-damage family
one action-start recovery family
one after-damage recovery trigger path
application-time frozen potency/context
source-death-safe persistent attribution
same-name refresh-and-overwrite
owner-relative finite duration
central runtime RNG
central RecoverySystem / TroopSystem mutation
Stage9 operation identity / partition / finalization preserved
```

Stage10 freezes state topology and runtime contracts. It does not pretend every source skill's microscopic numeric formula is already known.

---

# 2. Non-goals

Stage10 does not:

```text
invent exact DOT nonlinear constants
invent exact treatment nonlinear constants
reverse-engineer PRNG internals
implement full EVASION / BARRIER official mechanics
implement full CRITICAL / STRATEGY_CRITICAL official mechanics
invent universal positive dispel
implement FALSE_REPORT or morale-shake gameplay
own command-aura lifecycle
implement Elephant Soldiers FLOOD delay
implement external observer skills
create a second damage engine
create a second state registry
replace Stage9 finalization / FutureAdmission
turn EventBus into a rule engine
```

External systems may later feed typed facts into Stage10 seams without reopening the persistent-state topology.

---

# 3. Runtime ownership map

| Concern | Authoritative owner after Stage10 |
|---|---|
| Physical state storage | `BattleContext.states / StateRegistry` |
| State apply / refresh / remove / expire | `StateLifecycleSystem` |
| Per-battle action-start fact | `BattleContext.action_progress / ActionProgressTracker` |
| Action-start trigger collection | Stage7 `TriggerSystem` |
| Action-start execution | Stage7 `RuleHookSystem` + `EffectExecutor` |
| Recovery opportunity RNG / amount resolution | new `RecoveryOpportunitySystem` |
| After-damage trigger coordination | new `AfterDamageHookSystem` |
| Runtime RNG | `BattleContext.random` |
| Recovery prevention / final recovery policy | `RecoverySystem` |
| Troop mutation | `TroopSystem` |
| Standard theoretical damage | `DamageSystem.calculate()` |
| Periodic damage operation identity | Stage9 `DamageInstanceCoordinator` |
| Partition / share / distribution | Stage9 orchestration |
| Chain / admitted secondary work | Stage9 callback/admission owners |
| Battle termination / drain | `BattleFinalizationCoordinator` |

No additional physical owner is authorized.

---

# 4. P0 blocker closure

## S10-B01 · Snapshot-backed continuous damage

Decision:

```text
Add an explicit FROZEN_APPLICATION calculation basis
inside the existing DamageSystem.calculate() entry.
```

An effective continuous state carries immutable `FrozenContinuousDamageBasis` created at application/refresh. Tick-time damage never reconstructs potency from current source runtime.

This requires the limited Stage8 compatibility reopen in section 5.

## S10-B02 · Source-dead persistent damage

Decision:

```text
FROZEN_APPLICATION periodic damage validates historical source identity,
not current source combat eligibility.
```

Target must be alive. The original source must remain identifiable for credit, but source troops may already be zero.

This exception is authorized only when all are true:

```text
DamageSourceType.CONTINUOUS
SourceType.PERIODIC_DAMAGE
source_state_id present
source_state_instance_id present
valid FrozenContinuousDamageBasis present
```

Ordinary live damage keeps the existing alive-source requirement.

## S10-B03 · FIRST_AID exact checkpoint

Decision:

```text
AFTER_DAMAGE is synchronous DamageInstance-local aftermath work.
```

It runs after authoritative target settlement exists and before normal resolved-damage callback fanout / DamageInstance completion.

It is not a new global future branch.

## S10-B04 · Owner-relative expiration

Decision:

```text
finite persistent lifecycle = PersistentLifecycleWindow
anchored by BattleContext.action_progress.
```

No universal ROUND_END conversion is allowed.

---

# 5. Explicit Stage8 limited compatibility reopen

## 5.1 Why the reopen is necessary

Current Stage8 standard path assumes:

```text
DamageSystem.calculate() = unique theoretical-damage entry
source = current UnitRuntime
source must be alive
```

Stage10 authority requires:

```text
application/refresh potency context is locked
runtime source changes do not recalculate old instance
source death does not cancel old instance
```

The current live-only input contract cannot represent those facts. A narrow explicit reopen is therefore required.

## 5.2 Allowed changes

```text
1. typed DamageCalculationBasis on DamageRequest
2. typed FrozenContinuousDamageBasis input
3. basis-aware participant validation
4. basis-aware DamagePipelineTrace
5. FROZEN_APPLICATION reuse after tick-dynamic prevention/hit gates
6. strict preservation of DamageResult and Stage9 settlement meanings
```

## 5.3 Forbidden changes

```text
base formula mathematical rewrite
F(N) rewrite
morale formula rewrite
weapon/strategy RNG-range rewrite
low-damage-floor rewrite
ordinary modifier arithmetic reinterpretation
prevention order change
hit order change
Dtotal / Dtarget / ActualTargetTroopLoss meaning change
DamageResolutionSystem ownership change
TroopSystem ownership change
```

## 5.4 Backward-compatibility hard gate

Every existing request without an explicit frozen basis remains:

```text
calculation_basis = LIVE_RUNTIME
```

For all such requests, seeded behavior must remain equivalent in:

```text
DamageResult
DamagePipelineTrace
RNG consumption
exceptions
settlement events
Stage9 operation identity
```

---

# 6. DamageCalculationBasis

Stage10 freezes:

```text
DamageCalculationBasis
- LIVE_RUNTIME
- FROZEN_APPLICATION
```

Conceptual `DamageRequest` extension:

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
→ existing source/target validation unchanged

FROZEN_APPLICATION
→ source_type == CONTINUOUS
→ state provenance pair present
→ frozen_application_basis present
→ basis damage_type matches request damage_type
```

`FROZEN_APPLICATION` is not a generic dead-unit execution permission.

---

# 7. FrozenContinuousDamageBasis

`FrozenContinuousDamageBasis` is the immutable application/refresh potency contract for one effective continuous-damage instance.

Conceptual shape:

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

Mandatory invariants:

```text
nominal_damage is int, bool rejected, >= 0
no UnitRuntime object stored
no mutable StateInstance stored
no callable stored
no dict[str, Any] snapshot
all fields immutable / typed
```

`nominal_damage` means:

```text
application/refresh-time nominal theoretical damage
with application-locked potency context already resolved,
before tick-time dynamic weakness/evasion/barrier gates.
```

It is not Dtarget and not ActualTargetTroopLoss.

## 7.1 Formula-research boundary

The exact producer of `nominal_damage` belongs to source-skill/effect formula authority.

Stage10 only requires:

```text
successful application/refresh of official continuous state
→ valid FrozenContinuousDamageBasis supplied
→ same basis remains authoritative until refresh/removal
```

Synthetic potency producers may test Stage10 topology. A concrete source skill becomes numerically official only when its potency producer is evidence-backed.

## 7.2 REBELLION

REBELLION basis additionally freezes:

```text
route = WEAPON or STRATEGY at application/refresh
DefensePolicy = IGNORE_RELEVANT_TARGET_DEFENSE
```

Runtime ATK/INT changes never reroute the old instance. Refresh may create a different route/basis.

---

# 8. FROZEN_APPLICATION DamageSystem semantics

Prepared periodic lane:

```text
validate historical provenance + live target
↓
collect tick-dynamic prevention/hit rules only
↓
DamagePreventionSystem
↓
HitResolutionSystem
↓
validate/reuse FrozenContinuousDamageBasis
↓
final theoretical damage = basis.nominal_damage
↓
DamageResult
```

Current ordinary source/target damage modifiers must not be collected and applied a second time.

Dynamic at tick:

```text
source weakness
future official evasion
future official barrier
owner alive
battle/finalization eligibility
```

Locked in basis:

```text
potency
applicable ordinary modifier context
applicable crit context
REBELLION route / defense policy
```

## 8.1 Trace truthfulness

`DamagePipelineTrace` must identify:

```text
LIVE_RUNTIME
vs
FROZEN_APPLICATION
```

It may not pretend frozen application data was freshly recalculated from live runtime.

One representation detail is intentionally left for independent design audit:

```text
A. add REUSED_FROZEN_INPUT to StageEvaluationStatus
or
B. preserve the current status enum and add explicit frozen-stage trace fields
```

This choice is trace-only and may not affect gameplay.

---

# 9. Historical source provenance

Existing persistent damage retains:

```text
source_id
source_skill_id
source_skill_slot
source_state_id
source_state_instance_id
```

Persistent tick validation distinguishes:

```text
historical source identity exists
from
source currently has execution right
```

For valid `FROZEN_APPLICATION` periodic damage:

```text
source identity exists       REQUIRED
source alive                 NOT REQUIRED
source can act               NOT REQUIRED
source weakness at tick      DYNAMIC gate
```

No standard attack/skill inherits this exception.

---

# 10. Stage10 StateRuntimeParams

Official Stage10 params replace the previous synthetic/minimal DEFER representation.

Conceptual types:

```text
ContinuousDamageStateParams
FirstAidStateParams
RecuperationStateParams
```

## 10.1 PersistentLifecycleWindow

```python
@dataclass(frozen=True, slots=True)
class PersistentLifecycleWindow:
    first_eligible_round: int
    last_eligible_round: int | None
    duration_kind: FINITE_ROUNDS | UNTIL_BATTLE_END | EXTERNAL_SOURCE_LIFECYCLE
```

For finite N:

```text
last_eligible_round = first_eligible_round + N - 1
```

There is no per-state `last_processed_round`. Same-round duplicate suppression is an action-progress fact owned by `ActionProgressTracker`, not a TriggerSystem mutation.

## 10.2 ContinuousDamageStateParams

```text
frozen_basis: FrozenContinuousDamageBasis
lifecycle: PersistentLifecycleWindow
active_gate: PersistentSourceSkillGate
```

## 10.3 FirstAidStateParams

```text
probability: float in [0,1]
recovery_model: TREATMENT_AMOUNT | TRIGGER_DAMAGE_RATIO
frozen_recovery_context: FrozenRecoveryApplicationContext
lifecycle: PersistentLifecycleWindow
active_gate: PersistentSourceSkillGate
```

## 10.4 RecuperationStateParams

```text
probability: float in [0,1]
recovery_model: TREATMENT_AMOUNT
frozen_recovery_context: FrozenRecoveryApplicationContext
lifecycle: PersistentLifecycleWindow
active_gate: PersistentSourceSkillGate
```

Probability `1.0` represents guaranteed RECUPERATION sources. The official model may not collapse all sources into guaranteed recovery.

---

# 11. ActionProgressTracker

## 11.1 Ownership

Stage10 introduces one battle-local typed fact:

```text
BattleContext.action_progress: ActionProgressTracker
```

This is execution progress, not state storage.

## 11.2 API

Conceptual API:

```text
mark_action_start(round_no, actor_id)
action_start_count(round_no, actor_id) -> int
has_started_this_round(round_no, actor_id) -> bool
last_started_round(actor_id) -> int | None
```

BattleEngine calls `mark_action_start` immediately before `UNIT_ACTION_STARTED` publication / `UnitActionStartHook` processing.

StateLifecycleSystem reads the tracker while applying/refreshing persistent states.

TriggerSystem reads `action_start_count` to enforce the family rule:

```text
max one persistent action-start opportunity per owner per combat round
```

No EventBus history is used.

---

# 12. Lifecycle derivation

For an incoming finite N-round state at combat round R:

```text
if owner has NOT reached action start in R:
    first_eligible_round = R
else:
    first_eligible_round = R + 1

last_eligible_round = first_eligible_round + N - 1
```

This derivation is rerun on refresh.

Examples:

```text
2-round state applied before owner acts in round 3
→ eligible rounds 3,4
→ no opportunity round 5

2-round state applied after owner acts in round 3
→ eligible rounds 4,5
→ no opportunity round 6
```

No catch-up exists at round end.

---

# 13. UnitActionStart lifecycle algorithm

Production order for actor A at round R:

```text
1. BattleEngine marks A action start in context.action_progress
2. StateLifecycleSystem expires A's finite persistent states where R > last_eligible_round
3. BattleEngine publishes observation facts
4. RuleHookSystem processes UnitActionStartHook
5. TriggerSystem considers persistent state only if action_start_count(R,A) == 1
6. TriggerSystem collects immutable Effects / RecoveryOpportunityEffects
7. EffectExecutor executes them in stable order
```

TriggerSystem remains mutation-free.

## 13.1 Finite expiry

```text
R > last_eligible_round
→ expire before effect collection
```

At `R == last_eligible_round`, the final opportunity may occur.

The state may remain physically present until the next owner action-start expiry check; the contract requires no N+1 opportunity, not a guessed universal round-end removal.

## 13.2 Additional action starts in same round

If a future official mechanism reaches a second `UnitActionStartHook` for the same owner in the same combat round:

```text
action_start_count > 1
→ Stage10 persistent states produce no second opportunity
```

This closes the family max-one-per-round contract without hardcoding “the engine can never have a second action start.”

---

# 14. Same-name refresh-and-overwrite

All eight target states allow one effective same-name instance per owner.

Stage10 adds an atomic `StateLifecycleSystem` persistent refresh operation.

Conceptually:

```text
apply_or_refresh_persistent(...)
```

No existing same-name instance:

```text
create StateInstance
publish STATE_APPLIED
```

Existing same-name instance:

```text
replace source/source skill/source slot/runtime params/application context/lifecycle atomically
retain physical instance_id
publish STATE_REFRESHED
```

## 14.1 Identity decision

Refresh retains `StateInstance.instance_id`.

This is an engineering identity choice because the gameplay contract freezes one continuing effective same-name slot and does not require a remove gap.

Retained instance ID does **not** preserve old potency/provenance. All effective fields are replaced.

## 14.2 Event contract

Add:

```text
EventType.STATE_REFRESHED
```

Payload includes at least:

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

This refresh policy is Stage10-state-specific and is not a universal stacking law.

---

# 15. Same-node deterministic order

Research does not freeze universal DOT-vs-RECUPERATION family priority.

Stage10 therefore freezes an engineering runtime default:

```text
matching physical StateInstances are processed by stable instance_id order
```

Label:

```text
RUNTIME DETERMINISM DEFAULT
NOT OFFICIAL FAMILY PRIORITY
```

Refresh retaining instance ID prevents refresh from accidentally changing this engineering order.

---

# 16. Periodic damage production

Eligible continuous state produces `DamageEffect` with:

```text
source_id                = effective state source
source_skill_id          = effective source skill
source_state_id          = state id
source_state_instance_id = physical instance id
damage_type              = frozen basis route
source_type              = DamageSourceType.CONTINUOUS
source_ref.stage9_source_type = SourceType.PERIODIC_DAMAGE
calculation_basis        = FROZEN_APPLICATION
frozen_application_basis = params.frozen_basis
```

Then:

```text
EffectExecutor
→ DamageInstanceCoordinator
→ DamageSystem.calculate(FROZEN_APPLICATION)
→ Stage9 partition / settlement
→ Stage9 aftermath/finalization
```

DirectTroopLoss is forbidden for these six DOT states.

---

# 17. RecoveryOpportunityEffect

Stage10 official FIRST_AID and RECUPERATION use a pure-data recovery opportunity instead of consuming RNG in TriggerSystem.

Conceptual type:

```python
@dataclass(frozen=True, slots=True)
class RecoveryOpportunityEffect:
    source_id: str | None
    target_id: str
    probability: float
    frozen_recovery_context: FrozenRecoveryApplicationContext
    active_gate: PersistentSourceSkillGate
    triggering_actual_damage: int | None
    source_skill_id: str | None
    source_skill_slot: SkillSlot | None
    source_state_id: str
    source_state_instance_id: str
    trigger_damage_instance_id: DamageInstanceId | None
    trigger_lineage: OperationLineage | None
```

This is an intent. It has no side effects and consumes no RNG by construction.

For RECUPERATION:

```text
triggering_actual_damage = None
trigger_damage_instance_id = None
trigger_lineage = None
```

For FIRST_AID damage-ratio model:

```text
triggering_actual_damage = AfterDamageHook.actual_target_troop_loss
```

---

# 18. RecoveryOpportunitySystem

`RecoveryOpportunitySystem` is the unique owner of Stage10 persistent recovery probability consumption and nominal recovery resolution.

It depends on:

```text
RecoverySystem
skill effectiveness query seam
```

It does not depend on DamageInstanceCoordinator.

Execution order:

```text
1. validate RecoveryOpportunityEffect
2. verify target currently alive
3. evaluate PersistentSourceSkillGate
4. inactive -> NO_TRIGGER, consume no RNG
5. context.random.chance(probability) exactly once
6. chance failure -> NO_TRIGGER
7. resolve nominal amount from FrozenRecoveryApplicationContext
8. create RecoveryRequest with full provenance
9. RecoverySystem applies target-death/healing-ban policy
10. TroopSystem.restore applies missing-troop cap
```

Healing ban is intentionally after successful trigger chance because the frozen recovery contracts place it at recovery resolution rather than probability eligibility.

`RecoveryOpportunitySystem` returns a typed result distinguishing at least:

```text
INACTIVE
CHANCE_FAILED
RECOVERY_RESOLVED
RECOVERY_PREVENTED
```

No state mutation occurs here.

---

# 19. RECUPERATION flow

At the owner's first eligible action start in a combat round:

```text
lifecycle eligibility
↓
TriggerSystem creates RecoveryOpportunityEffect
↓
EffectExecutor routes it to RecoveryOpportunitySystem
↓
active gate
↓
probability roll, including probability=1.0 sources
↓
nominal recovery
↓
RecoverySystem
↓
healing ban / target alive
↓
TroopSystem.restore cap
```

Temporary inactive source-skill window:

```text
no RNG
no recovery
finite lifecycle window unchanged
opportunity is lost
no catch-up
```

Stun/disarm/silence/weakness/confusion do not inherently suppress an already reached RECUPERATION action-start opportunity.

---

# 20. AfterDamageHook

Stage10 adds immutable typed damage aftermath facts:

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

The implementation may refine field names, but not omit these semantic facts.

No EventBus history reconstruction is allowed.

---

# 21. FIRST_AID eligibility before opportunity creation

For one `AfterDamageHook`:

```text
1. locate effective FIRST_AID on target
2. none -> stop
3. prevented -> stop
4. actual_target_troop_loss <= 0 -> stop
5. target_defeated -> stop
6. target currently dead -> stop
7. create exactly one RecoveryOpportunityEffect for that FIRST_AID instance
```

No RNG occurs during this collection.

Consequences:

```text
prevented damage -> no RNG
zero actual loss -> no RNG
fatal damage -> no RNG and no resurrection
one eligible DamageInstance -> at most one FIRST_AID opportunity
multiple hits represented by multiple DamageInstances -> independent opportunities
no combat-round cap
```

Source-skill active gating and RNG happen later in `RecoveryOpportunitySystem`.

---

# 22. FIRST_AID exact checkpoint

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
AfterDamageHookSystem
↓
FIRST_AID RecoveryOpportunityEffect(s)
↓
RecoveryOpportunitySystem
↓
existing resolved-damage callback fanout (Chain etc.)
↓
complete current DamageInstance
```

Share:

```text
target settlement
→ FIRST_AID target aftermath
→ share direct troop loss
```

Distribution:

```text
distribution direct losses
→ target settlement
→ FIRST_AID target aftermath
```

Partition direct troop losses are not silently reclassified as standard damage events and do not automatically trigger FIRST_AID.

Cleave derived damage:

```text
derived target settlement
→ same AfterDamageHookSystem
→ same RecoveryOpportunitySystem
→ existing damage callback fanout
```

The existing evidence-gated `cleave_first_aid` seam must bind to the same Stage10 service rather than becoming a parallel FIRST_AID engine.

---

# 23. AfterDamageHookSystem and acyclic dependency

Naive wiring is forbidden:

```text
DamageInstanceCoordinator
→ RuleHookSystem
→ EffectExecutor
→ DamageInstanceCoordinator
```

Stage10 instead freezes:

```text
Damage aftermath callback point
        ↓
AfterDamageHookSystem
        ↓
TriggerSystem AFTER_DAMAGE collection
        ↓
RecoveryOpportunityEffect(s) ONLY
        ↓
RecoveryOpportunitySystem
        ↓
RecoverySystem
```

`AfterDamageHookSystem` does not depend on `EffectExecutor`.

`TriggerSystem` remains side-effect-free and consumes no RNG.

For AFTER_DAMAGE collection, any produced `DamageEffect`, state mutation effect, or unsupported effect is a programmer/design error.

---

# 24. FIRST_AID recovery models

Stage10 freezes:

```text
TREATMENT_AMOUNT
TRIGGER_DAMAGE_RATIO
```

For `TREATMENT_AMOUNT`:

```text
nominal amount comes from FrozenRecoveryApplicationContext
```

For `TRIGGER_DAMAGE_RATIO`:

```text
basis = AfterDamageHook.actual_target_troop_loss
ratio = application-time frozen ratio
nominal recovery = evidence-backed integerization of basis × ratio
```

Stage10 explicitly rejects Dtotal or assigned target damage as a substitute for the frozen “当次受击扣减伤害量” input.

Exact source-skill ratio mapping / rounding remains source formula authority.

---

# 25. FrozenRecoveryApplicationContext

Conceptual typed snapshot:

```python
@dataclass(frozen=True, slots=True)
class FrozenRecoveryApplicationContext:
    potency_model: RecoveryPotencyModel
    nominal_amount: int | None
    trigger_damage_ratio: ExactRatio | None
    locked_modifier_context: FrozenRecoveryModifierContext
    potency_origin: PersistentPotencyOrigin
```

Legal combinations:

```text
TREATMENT_AMOUNT
→ nominal_amount present
→ trigger_damage_ratio absent

TRIGGER_DAMAGE_RATIO
→ trigger_damage_ratio present
→ dynamic trigger amount supplied by AfterDamageHook
```

No mutable UnitRuntime and no untyped snapshot dict is stored.

---

# 26. Recovery provenance extension

`RecoveryRequest` and relevant effect/result surfaces receive backward-compatible optional provenance extensions after existing constructor fields.

Required facts:

```text
source_skill_slot
trigger_damage_instance_id
trigger_lineage or equivalent immutable operation reference
```

RECUPERATION leaves trigger-damage fields None.

FIRST_AID binds them from `AfterDamageHook`.

RecoverySystem preserves/publishes provenance but does not reinterpret Stage9 operation identity.

---

# 27. PersistentSourceSkillGate

Typed values:

```text
ALWAYS_ACTIVE
QUERY_SKILL_RUNTIME
EXTERNAL_LIFECYCLE
```

For `QUERY_SKILL_RUNTIME`, the state keeps:

```text
source_id
source_skill_id
source_skill_slot
```

and queries one authoritative runtime effectiveness owner.

Current `SkillRuntime.enabled` is the natural existing fact to reuse if a battle-authoritative lookup exists.

Persistent-state params must not copy FALSE_REPORT / morale-shake truth into a second store.

If implementation discovery finds no authoritative `(owner, slot) -> SkillRuntime` lookup, Stage10 records an implementation blocker and may add a typed registry/lookup owner. It may not invent the external disable mechanics.

---

# 28. Official state definition binding

```text
BURN         -> ContinuousDamageStateParams + RULE_HOOK:UNIT_ACTION_START
FLOOD        -> ContinuousDamageStateParams + RULE_HOOK:UNIT_ACTION_START
POISON       -> ContinuousDamageStateParams + RULE_HOOK:UNIT_ACTION_START
ROUT         -> ContinuousDamageStateParams + RULE_HOOK:UNIT_ACTION_START
SANDSTORM    -> ContinuousDamageStateParams + RULE_HOOK:UNIT_ACTION_START
REBELLION    -> ContinuousDamageStateParams + RULE_HOOK:UNIT_ACTION_START
RECUPERATION -> RecuperationStateParams     + RULE_HOOK:UNIT_ACTION_START
FIRST_AID    -> FirstAidStateParams         + RULE_HOOK:AFTER_DAMAGE
```

Tags are runtime selectors, not gameplay evidence.

---

# 29. Evidence Gate promotion

Stage10 must explicitly update evidence matrices.

Minimum promotions:

```text
Stage7 action-start official binding:
BURN / FLOOD / POISON / ROUT / SANDSTORM / REBELLION / RECUPERATION

Stage10 reactive binding:
FIRST_AID via typed AFTER_DAMAGE + RecoveryOpportunitySystem

Stage8:
REBELLION defense-ignore specific policy
FROZEN_APPLICATION continuous-damage compatibility lane
```

Still DEFER unless independently frozen:

```text
EVASION official binding
BARRIER official binding
CRITICAL official binding
STRATEGY_CRITICAL official binding
DAMAGE_REDUCTION_PIERCE official binding
universal positive dispel
```

Synthetic capability tests do not promote official evidence rows.

---

# 30. Death contracts

## Owner death

Global behavior remains:

```text
owner death
→ clear attached states
→ abort remaining owner-state resolution
→ reject future state application to dead owner
```

Stage10 must use one authoritative death-cleanup integration point, not eight EventBus subscribers.

## Source death

No generic sourced-state deletion:

```text
continuous damage existing instance -> persists
FIRST_AID existing instance          -> persists
active-sourced RECUPERATION          -> persists
command-aura RECUPERATION            -> external owner may remove it
```

---

# 31. Finalization boundary

## Periodic damage

A new periodic DamageInstance may only be created while the surrounding action-start work is legally executing under the existing battle lifecycle.

No Stage10 subsystem admits damage after Stage9 finalization denies new work.

## FIRST_AID local drain

FIRST_AID is local aftermath of an already-admitted damage operation.

It does not create a new target, damage operation, action, or future branch.

Fatal target damage is filtered before recovery opportunity creation, so FIRST_AID cannot resurrect a defeated target or undo that target's victory edge.

If another partition participant death has already latched victory while the current DamageInstance is still draining, a nonfatal target's already-local FIRST_AID aftermath may complete before that DamageInstance closes. This is completion of admitted work, not new future admission.

---

# 32. External dependencies preserved as external

```text
Evasion / Barrier
Critical / Strategy Critical
positive dispel
command-aura source death
FALSE_REPORT / morale-shake skill deactivation
Elephant Soldiers FLOOD delay
external state observers
cleanse target-selection policy
```

Stage10 exposes typed seams only.

---

# 33. Required dependency graph

```text
BattleEngine
  -> BattleContext.action_progress
  -> StateLifecycleSystem action-start expiry
  -> RuleHookSystem

RuleHookSystem
  -> TriggerSystem
  -> EffectExecutor

EffectExecutor
  -> DamageInstanceCoordinator
  -> StateLifecycleSystem
  -> RecoveryOpportunitySystem
  -> RecoverySystem

DamageInstanceCoordinator
  -> DamageSystem
  -> Stage9 partition/finalization
  -> damage aftermath callback point

Damage aftermath callback point
  -> AfterDamageHookSystem
  -> existing Stage9 damage callbacks

AfterDamageHookSystem
  -> TriggerSystem
  -> RecoveryOpportunitySystem

RecoveryOpportunitySystem
  -> RecoverySystem
  -> authoritative skill-effectiveness query

RecoverySystem
  -> TroopSystem
```

Forbidden:

```text
AfterDamageHookSystem -> EffectExecutor
RecoveryOpportunitySystem -> DamageInstanceCoordinator
EventBus -> gameplay trigger execution
```

Runtime dependency-cycle count remains zero.

---

# 34. Required invariants

```text
S10-I01 one physical StateRegistry
S10-I02 one StateLifecycleSystem mutation owner
S10-I03 one effective same-name Stage10 state per owner
S10-I04 refresh replaces all effective provenance/potency/lifecycle fields
S10-I05 refresh retains physical instance_id and emits STATE_REFRESHED
S10-I06 no fake remove/apply gap on refresh
S10-I07 application-before-owner-action may trigger same round
S10-I08 application-after-owner-action cannot catch up same round
S10-I09 finite N-round state cannot produce N+1 opportunity
S10-I10 second owner action-start in same round cannot duplicate persistent opportunity
S10-I11 inactive finite recovery opportunity is lost without duration extension
S10-I12 TriggerSystem performs no state mutation and consumes no RNG
S10-I13 DOT tick never recalculates potency from live source UnitRuntime
S10-I14 source death does not invalidate existing DOT
S10-I15 live standard damage still requires alive source
S10-I16 periodic damage retains Stage9 PERIODIC_DAMAGE identity
S10-I17 periodic damage never uses DirectTroopLoss shortcut
S10-I18 REBELLION route fixed until refresh
S10-I19 REBELLION basis carries IGNORE_RELEVANT_TARGET_DEFENSE
S10-I20 FIRST_AID one eligible damage settlement = one recovery opportunity
S10-I21 FIRST_AID has no combat-round cap
S10-I22 prevented/zero/fatal damage produces no FIRST_AID opportunity/RNG
S10-I23 FIRST_AID damage-ratio basis = ActualTargetTroopLoss
S10-I24 RECUPERATION probability is source-defined, including guaranteed 1.0
S10-I25 inactive FIRST_AID/RECUPERATION opportunity consumes no RNG
S10-I26 healing ban remains RecoverySystem-owned after successful chance
S10-I27 missing-troop cap remains TroopSystem-owned
S10-I28 EventBus never drives persistent gameplay
S10-I29 AfterDamageHookSystem cannot execute damage/state mutation
S10-I30 runtime dependency graph remains acyclic
S10-I31 source-skill disable truth not copied into state params
S10-I32 owner death hard-terminates attached persistent state execution
S10-I33 standard Stage1-9 behavior unchanged outside explicit Stage8 reopen
```

---

# 35. Mandatory regression scenarios

```text
1. 1-round DOT applied before owner acts -> same-round tick only
2. 1-round DOT applied after owner acts -> next-round tick only
3. 2-round DOT exact two opportunities
4. second action-start same owner/same round -> no second DOT/RECUPERATION opportunity
5. same-source refresh before owner action
6. cross-source refresh after owner action
7. refresh replaces provenance
8. refresh replaces frozen potency
9. refresh may reroute REBELLION
10. source dies after applying DOT -> later tick still resolves
11. source attributes change after apply -> old DOT unchanged
12. source ordinary modifiers change -> old DOT unchanged
13. weakness dynamically blocks tick without deleting state
14. stun/disarm/silence do not suppress eligible action-start persistent trigger
15. owner death clears state and prevents later trigger
16. purify removal prevents later negative-state tick
17. RECUPERATION same-round first opportunity
18. RECUPERATION after-action deferred first opportunity
19. RECUPERATION probability failure
20. RECUPERATION guaranteed probability=1.0
21. RECUPERATION inactive window -> no RNG / no recovery / no extension
22. FIRST_AID normal attack damage
23. FIRST_AID skill damage
24. FIRST_AID periodic damage
25. two multi-hit DamageInstances -> two independent FIRST_AID opportunities
26. FIRST_AID prevented hit -> no opportunity/RNG
27. FIRST_AID fatal hit -> no opportunity/RNG/resurrection
28. FIRST_AID damage-ratio reads actual troop loss, not Dtotal/Dtarget
29. FIRST_AID under healing ban -> chance can succeed, RecoverySystem prevents recovery
30. share target FIRST_AID before sharer direct loss
31. distribution direct losses do not automatically trigger FIRST_AID
32. Cleave uses same Stage10 FIRST_AID aftermath service
33. battle-latched admitted DamageInstance may drain local nonfatal FIRST_AID
34. ordinary live DamageRequest remains Stage9-baseline equivalent
35. ordinary dead-source standard attack/skill remains rejected
36. no EventBus control-flow subscription
37. no runtime dependency cycle
```

DEFER interactions use synthetic providers without claiming official integration.

---

# 36. Implementation phases

## Phase 10.1 · Typed contracts

```text
DamageCalculationBasis
FrozenContinuousDamageBasis
FrozenRecoveryApplicationContext
PersistentLifecycleWindow
PersistentSourceSkillGate
Stage10 StateRuntimeParams
RecoveryOpportunityEffect
RecoveryOpportunityResult
AfterDamageHook
recovery provenance extension
STATE_REFRESHED
```

## Phase 10.2 · Action progress and lifecycle

```text
BattleContext.action_progress
ActionProgressTracker
BattleEngine explicit mark_action_start
StateLifecycleSystem persistent apply/refresh
owner-relative action-start expiry
same-round duplicate suppression
```

## Phase 10.3 · Stage8 limited reopen

```text
FROZEN_APPLICATION validation
basis-aware participant validation
prepared periodic lane
truthful trace representation
full LIVE_RUNTIME regression gate
```

## Phase 10.4 · Continuous damage family

```text
BURN
FLOOD
POISON
ROUT
SANDSTORM
REBELLION
```

## Phase 10.5 · Recovery opportunity runtime + RECUPERATION

```text
RecoveryOpportunitySystem
skill-effectiveness query seam
RECUPERATION action-start probability/recovery
finite and battle-long lifecycle
```

## Phase 10.6 · AFTER_DAMAGE + FIRST_AID

```text
AfterDamageHookSystem
standard damage aftermath integration
Cleave derived integration
FIRST_AID eligibility
full recovery provenance
```

## Phase 10.7 · death / cleanse / external seam hardening

```text
owner-death cleanup integration
purify/remove compatibility
external source-lifecycle seam
DEFER guards
```

## Phase 10.8 · independent implementation audit / final freeze

```text
full pytest twice
demo
exact-head CI
artifact provenance
architecture invariant audit
mechanism-contract audit
Stage8 limited-reopen regression audit
Stage10 Final Audit
```

---

# 37. Likely implementation surfaces

```text
sgs_v2/battle_core/context.py
sgs_v2/battle_core/rule_hooks.py
sgs_v2/battle_core/trigger_system.py
sgs_v2/battle_core/recovery_system.py
sgs_v2/battle_core/effects.py
sgs_v2/battle_core/effect_result.py
sgs_v2/battle_core/effect_executor.py
sgs_v2/battle_core/state_lifecycle_system.py
sgs_v2/battle_core/official_state_catalog.py
sgs_v2/battle_core/damage_system.py
sgs_v2/battle_core/damage_pipeline_trace.py
sgs_v2/battle_core/damage_instance_coordinator.py
sgs_v2/battle_core/cleave_derived_damage_system.py
sgs_v2/battle_core/battle_systems.py
sgs_v2/battle_core/engine.py
new stage10_state_params.py
new persistent_damage_basis.py or equivalent
new action_progress_tracker.py
new recovery_opportunity_system.py
new after_damage_hook_system.py
```

Extra production files require explicit justification. This list is not permission for broad refactoring.

---

# 38. Forbidden shortcuts

```text
claim synthetic PeriodicDamageStateParams already equals official DOT
recalculate DOT from live source every tick
delete existing DOT when source dies
temporarily revive source
copy DamageSystem into PersistentDamageSystem
write troops directly for DOT
route DOT through DirectTroopLoss
read EventBus history for FIRST_AID
subscribe DAMAGE_DEALT to execute gameplay
consume probability in TriggerSystem
make FIRST_AID one-per-round
make all RECUPERATION guaranteed
use Dtotal/Dtarget for FIRST_AID damage-ratio basis
heal after fatal damage
pause finite duration while source skill inactive
convert owner-relative duration to universal ROUND_END
allow multiple effective same-name Stage10 instances
fake refresh as STATE_REMOVED + STATE_APPLIED
store application context as dict[str, Any]
store mutable UnitRuntime in state params
import Python random in persistent state logic
add FutureBranchKind for synchronous FIRST_AID
wire AfterDamageHookSystem through EffectExecutor
copy external disable truth into persistent state params
silently activate EVASION/BARRIER/CRITICAL official bindings
claim instance_id deterministic order is official priority
```

---

# 39. Design audit hard gates

`STAGE10_DESIGN_AUDIT.md` must reject the design unless it proves:

```text
A. S10-B01..B04 each have one implementable answer
B. S10-M01..M06 each have one implementable answer
C. Stage8 limited reopen is explicit and regression-testable
D. LIVE_RUNTIME damage remains frozen
E. FROZEN_APPLICATION cannot authorize arbitrary dead-source standard damage
F. owner-relative lifecycle handles application/refresh before and after owner action
G. same-round duplicate prevention does not require TriggerSystem mutation
H. RECUPERATION probability is represented
I. FIRST_AID checkpoint uses authoritative settlement facts
J. TriggerSystem remains RNG-free
K. AFTER_DAMAGE architecture is acyclic
L. recovery provenance remains backward compatible
M. external dependencies remain external
N. formula research debt is not converted into guessed constants
O. no duplicate state/troop owner exists
P. Stage9 operation/finalization semantics remain intact
```

Failure of any gate means:

```text
DESIGN AUDIT = FAIL
BUILD PROMPT = BLOCKED
```

---

# 40. Architecture decision record

```text
S10-B01 snapshot-backed ingress
= FROZEN_APPLICATION basis inside existing DamageSystem.calculate

S10-B02 source-dead execution
= historical source identity accepted only for valid periodic frozen-basis request

S10-B03 FIRST_AID checkpoint
= synchronous target-settlement aftermath inside owning DamageInstance

S10-B04 owner-relative expiry
= BattleContext.action_progress + PersistentLifecycleWindow

S10-M01 same-name replacement
= StateLifecycleSystem atomic refresh, physical instance_id retained

S10-M02 RNG
= RecoveryOpportunitySystem owns chance after eligibility/active gates

S10-M03 recovery provenance
= backward-compatible request/effect/result provenance extension

S10-M04 source-skill inactive gate
= typed authoritative skill-runtime query seam

S10-M05 snapshot schema
= immutable typed damage/recovery application contexts

S10-M06 state binding / evidence
= explicit params + hook tags + evidence-matrix promotion
```

---

# 41. Remaining representation-only review item

One non-gameplay representation choice is deliberately left to independent design audit:

```text
How DamagePipelineTrace represents FROZEN_APPLICATION stage reuse
without falsely claiming a fresh live formula/modifier calculation.
```

Allowed families:

```text
A. typed REUSED_FROZEN_INPUT status
B. separate typed frozen-basis trace fields while preserving current status enum
```

The design audit must select one before design freeze.

No P0 or P1 gameplay/runtime ownership decision remains intentionally open.

---

# 42. Design verdict

```text
Mechanism research              = COMPLETE
Runtime mapping                 = COMPLETE
P0 architecture decisions       = CLOSED IN DESIGN
P1 architecture decisions       = CLOSED IN DESIGN
Stage8 conflict                 = EXPLICIT LIMITED REOPEN REQUIRED
Stage9 conflict                 = NO REOPEN; local aftermath extension only
TriggerSystem purity            = PRESERVED
Recovery probability ownership  = RecoveryOpportunitySystem
Formula constants               = OUT OF STAGE10 CORE SCOPE
External dependency semantics   = PRESERVED AS EXTERNAL
Production implementation       = NOT AUTHORIZED

NEXT REQUIRED STEP:
STAGE10_DESIGN_AUDIT.md
```

Only an independent design audit may promote this specification to `DESIGN FROZEN` and authorize `STAGE10_BUILD_PROMPT.md`.
