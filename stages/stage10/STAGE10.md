# Stage 10 · Persistent State Runtime Integration · Architecture Design Draft V2

> Repair: `Stage10 Design Repair R1-C / Architecture Contract Repair`  
> Status: `ARCHITECTURE DESIGN DRAFT V2`  
> Independent design audit: `REQUIRED`  
> Production implementation: `NOT AUTHORIZED`  
> Design freeze: `NOT AUTHORIZED`

---

# 0. R1-C input baseline

R1-C was authored from the real branch state, not from historical SHA values in an earlier prompt.

```text
Battle repo:
lxy2005051020-commits/sgs-v2-battle-system
branch: stage10-persistent-state-research
input HEAD: 2be2cfdd789ef9e035306fbb4c5fb40bf994a341

STAGE10.md blob:
b833f0c0a02ca8f45d9b2f560af0aad9599d041a

STAGE10_DESIGN_AUDIT.md blob:
9e8e73d0cc296e8cdb8799ffaabfbcc34a9204d3

STAGE10_AUTHORITY_GAP_TRIAGE.md blob:
860160964e07cccbb9eabb50bd86c42750fefbae

STAGE10_TARGETED_RESEARCH_QUESTIONS.md blob:
cddaa78bb0cbdc1db0e94f740edfee2ccc065c75

Gameplay Authority repo:
lxy2005051020-commits/sgs-state-mechanics-research
branch: main
input HEAD: 61f2be7e87e6bfab1433657ee7f766ae0c53da9d
```

R1-C also reread the current Stage7 / Stage8 / Stage9 frozen contracts and the current production runtime before choosing compatibility seams.

## 0.1 Authority synchronization note

At Gameplay Authority HEAD `61f2be7e...`, the repository tree does **not** yet contain the task-referenced files:

```text
stage10/RECOVERY_RNG_EDGE_RESEARCH.md
stage10/FIRST_AID_ZERO_LOSS_ELIGIBILITY_RESEARCH.md
```

and the current `states/persistent/first_aid/MECHANISM_CONTRACT.md` blob still predates the zero-loss eligibility correction.

R1-C therefore distinguishes two evidence sources instead of pretending the missing files exist:

```text
A. repository-pinned Gameplay Authority
   → HEAD 61f2be7e...

B. project-owner supplied targeted-research closure for R1-C
   → zero-loss FIRST_AID eligibility facts
   → full-troop recovery opportunity facts
   → official recovery PRNG-consumption = UNKNOWN / UNOBSERVABLE
```

The supplied closure is treated as authoritative project input for this repair, but **Gameplay Authority repository contents are not modified by R1-C**. Independent re-audit must keep this repository-sync fact visible.

---

# 1. Architecture objective

Stage10 integrates these eight persistent states without creating eight independent loops:

```text
690072 BURN
690073 FLOOD
690074 POISON
690075 ROUT
690076 SANDSTORM
690077 REBELLION
690078 FIRST_AID
690079 RECUPERATION
```

The repaired architecture must provide:

```text
one persistent lifecycle owner
one generation/provenance model
one continuous-damage Stage8 lane
one recovery-opportunity owner
one shared damage-aftermath port
one defeat-cleanup checkpoint
one battle-authoritative skill-runtime lookup
one deterministic composition DAG
```

while preserving:

```text
TriggerSystem purity
TroopSystem unique mutation
RecoverySystem recovery-policy ownership
DamageSystem theoretical-damage ownership
Stage9 DamageInstance / partition / finalization ownership
EventBus observation-only semantics
Evidence Gate discipline
```

---

# 2. Authority classification model

R1-C no longer uses bare `F / P / D` labels without definition.

| Classification | Meaning |
|---|---|
| `GAMEPLAY FROZEN` | Observable behavior fixed by pinned Gameplay Authority or explicit project-owner targeted-research closure. |
| `OFFICIAL UNKNOWN` | Official implementation behavior cannot be observed/reliably established. |
| `ENGINEERING DETERMINISM` | Simulator chooses one replay-stable rule because official hidden behavior is unknown. Must not be exported as gameplay authority. |
| `ARCHITECTURE REQUIRED` | Structural rule needed to make frozen gameplay implementable by one unambiguous runtime. |
| `COMPATIBILITY REOPEN` | Narrow change to a previously frozen Stage contract, documented by addendum. |
| `EXTERNAL / DEFERRED` | Existing or future mechanism owner remains outside Stage10. |

## 2.1 Gameplay vs engineering decision matrix

| Decision | Classification |
|---|---|
| FIRST_AID zero-loss resolved hit eligible | `GAMEPLAY FROZEN` |
| Evasion / miss creates no FIRST_AID opportunity | `GAMEPLAY FROZEN` |
| Barrier-zero creates FIRST_AID opportunity | `GAMEPLAY FROZEN` |
| Weakness-zero creates FIRST_AID opportunity | `GAMEPLAY FROZEN` |
| Full-troop recovery opportunity is not skipped | `GAMEPLAY FROZEN` |
| Source death does not generically cancel existing persistent state | `GAMEPLAY FROZEN` |
| Owner death clears states and aborts remaining state resolution | `GAMEPLAY FROZEN` |
| 100% probability consumes official RNG draw | `OFFICIAL UNKNOWN` |
| Zero recoverable gap consumes official RNG draw | `OFFICIAL UNKNOWN` |
| Simulator recovery probability draw policy | `ENGINEERING DETERMINISM` |
| Retain physical StateInstance id on refresh | `ENGINEERING` |
| New application-generation identity on every apply/refresh | `ARCHITECTURE REQUIRED` |
| Separate typed frozen trace field | `ENGINEERING` |
| Stage7 target-death hard boundary | `GAMEPLAY FROZEN + COMPATIBILITY REOPEN` |
| Stage8 FROZEN_APPLICATION lane | `ARCHITECTURE REQUIRED + COMPATIBILITY REOPEN` |

---

# 3. Frozen family facts preserved

## 3.1 Continuous damage

```text
Trigger                         = TARGET_ACTION_START
reachable max frequency         = 1 effective opportunity / owner / combat round
same-name effective instances   = 1
same-source reapply             = REFRESH_AND_OVERWRITE
cross-source reapply            = REFRESH_AND_OVERWRITE
application potency/context     = LOCKED_AT_APPLICATION
refresh                         = rebuild from refresh-time application context
source death                    = existing state persists
owner death                     = hard termination
BURN/FLOOD/POISON/SANDSTORM     = STRATEGY
ROUT                            = WEAPON
REBELLION                       = WEAPON or STRATEGY, route locked at application
REBELLION                       = IGNORE_RELEVANT_TARGET_DEFENSE
REBELLION                       != DirectTroopLoss / true-damage third family
weakness/evasion/barrier        = tick-time topology, not application snapshot
```

## 3.2 Recovery family

```text
FIRST_AID    = per eligible damage aftermath
RECUPERATION = owner TARGET_ACTION_START
same-name effective instances = 1
reapply = REFRESH_AND_OVERWRITE
recovery potency context = LOCKED_AT_APPLICATION
owner death = hard termination
healing ban = dynamic RecoverySystem gate
actual recovery cap = dynamic TroopSystem cap
```

Opportunity eligibility and recovery amount are separate contracts.

---

# 4. R1 · Stage7 target-death compatibility reopen

Normative addendum:

```text
stages/stage7/STAGE7_STAGE10_COMPATIBILITY_ADDENDUM.md
```

Stage7's deterministic pre-collection remains:

```text
Hook
→ collect one ordered immutable intent/effect batch
→ execute in deterministic order
```

The execute-all-tail rule is narrowed:

```text
target / owner defeat
→ synchronous defeat cleanup
→ execution right revoked/denied
→ remaining owner-state resolution is aborted
```

## 4.1 Ownership

```text
StateLifecycleSystem
→ owns physical state clear

DefeatCleanupPort
→ owns synchronous defeat checkpoint coordination

ExecutionRightSystem
→ owns typed execution-right decision

RuleHookSystem
→ owns hook-tail abort decision

EffectExecutor
→ validates execution right before dispatching each Effect

EventBus
→ observation only
```

Already-generated tail Effects are immutable historical intent. They are not rebound, retried, or executed after the hard boundary; they receive typed aborted outcomes.

Non-state Effect domains are not silently cancelled merely because a different unit died. Each Effect/domain uses its own execution-right rule. The Stage10 hard batch abort applies to the defeated owner's remaining state-resolution domain.

---

# 5. R2/R3 · Stage8 limited compatibility reopen

Normative addendum:

```text
stages/stage8/STAGE8_STAGE10_COMPATIBILITY_ADDENDUM.md
```

R1-C chooses:

```text
FROZEN_APPLICATION
= frozen application-generation INPUTS
≠ precomputed complete final nominal damage
```

The lane exists only for authorized Stage10 periodic continuous damage.

## 5.1 V2 basis

Conceptual contract:

```text
FrozenContinuousDamageBasis
- application_generation_id
- historical_source: HistoricalDamageSourceRef
- damage_type
- source_formula_facts: FrozenSourceFormulaFacts
- formula_policy_result
- coefficient / locked potency input
- locked_modifier_plan
- locked_crit_context | None
- formula_producer_provenance
```

Forbidden content:

```text
UnitRuntime
mutable StateInstance
callback/callable
untyped dict
service locator
```

The source-side formula facts capture the application-time source inputs required by the current Stage8 formula family without copying a UnitRuntime. Current target base-formula facts remain tick-time inputs unless a future authority explicitly freezes them.

## 5.2 Stage8 per-layer matrix

Legend:

```text
LIVE | FROZEN INPUT | REUSED RESULT | SKIPPED | DYNAMIC | NOT APPLICABLE
```

| Stage8 Layer | LIVE_RUNTIME | FROZEN_APPLICATION | Owner |
|---|---|---|---|
| participant validation | LIVE | DYNAMIC | DamageSystem |
| source historical identity | LIVE | FROZEN INPUT | typed historical source ref |
| target alive validation | LIVE | DYNAMIC | DamageSystem |
| Prevention | LIVE | DYNAMIC | DamagePreventionSystem |
| Hit Resolution | LIVE | DYNAMIC | HitResolutionSystem |
| Damage Formula Policy | LIVE | REUSED RESULT | frozen application producer + DamageSystem consumer |
| Base Formula | LIVE | DYNAMIC | existing Weapon/Strategy formula arithmetic with frozen source facts and current target facts |
| coefficient | LIVE | FROZEN INPUT | basis |
| locked potency input | NOT APPLICABLE | FROZEN INPUT | basis |
| ordinary modifier | LIVE | FROZEN INPUT | application-resolved ordered modifier plan |
| weakness | LIVE | DYNAMIC | current Stage8 prevention topology |
| crit | LIVE | FROZEN INPUT | only if an authorized crit contribution exists |
| RNG | LIVE | DYNAMIC | base-formula RNG remains tick-time; locked modifier/crit participation is not rerolled |
| defense policy | LIVE | REUSED RESULT | application-time FormulaPolicy result |
| final theoretical result | LIVE | DYNAMIC | DamageSystem |
| DamageResult | LIVE | DYNAMIC | DamageSystem |
| PipelineTrace | LIVE | DYNAMIC | truthful current trace + typed frozen-application trace |

No layer is left to implementation discretion.

## 5.3 Source-dead execution

`LIVE_RUNTIME` remains unchanged and rejects a dead source.

`FROZEN_APPLICATION` validates:

```text
historical source exists in battle roster
+
authorized PERIODIC_DAMAGE identity
+
matching state/generation provenance
+
live target exists
+
live target has troops > 0
```

It does not require `historical_source.troops > 0`.

The exception cannot be used by ordinary damage.

## 5.4 REBELLION

```text
application/refresh:
route locked
source formula facts locked
ordinary modifier/crit context locked
formula policy resolved = IGNORE_RELEVANT_TARGET_DEFENSE

at tick:
route reused
formula policy reused by actual Stage8 base formula
opposite family not rediscovered
current source attributes do not participate
```

---

# 6. DamagePipelineTrace closure

R1-C chooses one representation:

```text
separate typed frozen_application_trace
```

It does **not** add a fake `EXECUTED` status for a stage skipped at tick time.

Conceptually:

```text
DamagePipelineTrace
- existing prevention/hit/formula-policy/modifier status/result
- calculation_basis
- frozen_application_trace | None
```

`LIVE_RUNTIME` keeps the existing Stage8 trace exactly.

`FROZEN_APPLICATION` records dynamic prevention/hit honestly; tick-time FormulaPolicy/Modifier fields remain `NOT_EVALUATED` when their application-time result/plan is reused, while `frozen_application_trace` records the generation and reused/frozen inputs.

---

# 7. R4 · Persistent lifecycle time domain

Stage10 freezes three distinct time domains:

```text
PRE_BATTLE
COMBAT_ROUND(1)
COMBAT_ROUND(2)
...
```

`PRE_BATTLE` is not combat round zero for opportunity arithmetic.

## 7.1 Lifecycle record

Finite persistent states carry immutable generation lifecycle metadata:

```text
PersistentLifecycleWindow
- application_phase
- application_round
- first_eligible_round
- last_eligible_round
- max_opportunities_per_owner_round = 1
```

For a finite duration `N >= 1`:

```text
PRE_BATTLE application:
first_eligible_round = 1
last_eligible_round  = N

application in combat round R before owner reaches ActionStart:
first_eligible_round = R
last_eligible_round  = R + N - 1

application in combat round R after owner has reached ActionStart:
first_eligible_round = R + 1
last_eligible_round  = R + N
```

## 7.2 Required timelines

### PRE_BATTLE N=1

```text
PRE_BATTLE apply
→ first=1, last=1
→ Round1 owner ActionStart: exactly one eligible opportunity
→ end of that ActionStart resolution window: physical expiry
```

### PRE_BATTLE N=2

```text
PRE_BATTLE apply
→ first=1, last=2
→ Round1 opportunity
→ Round2 opportunity
→ end Round2 ActionStart window: physical expiry
```

### Apply before owner action in R

```text
ActionProgressTracker says owner has not reached ActionStart in R
→ R is first eligible round
```

### Apply after owner action in R

```text
ActionProgressTracker says owner already reached ActionStart in R
→ R+1 is first eligible round
→ no catch-up
```

### Refresh before action

```text
new generation
→ new source/provenance/potency
→ first eligible = R
→ lifecycle window rebuilt from R
```

### Refresh after action

```text
new generation
→ first eligible = R+1
→ no replay of R
```

Temporary source-skill inactivity suppresses the opportunity but does not pause the lifecycle clock and does not create catch-up work.

---

# 8. R5 · Physical expiration semantics

R1-C rejects deferred physical garbage collection.

Chosen model:

```text
physical expiration occurs synchronously at completion of the owner's last eligible ActionStart resolution window
```

Detailed order:

```text
owner reaches ActionStart
→ ActionProgressTracker.mark_action_start
→ lifecycle admission determines current generation eligibility
→ TriggerSystem collects current window intents
→ hook/opportunity resolution executes or is explicitly suppressed
→ if current round == last_eligible_round and state still exists
   StateLifecycleSystem physically expires it now
→ control leaves UNIT_ACTION_START
```

Consequences:

```text
predicate query after the window          → cannot see expired state
cleanse target selection after the window → cannot select expired state
same-name reapply after the window        → applies fresh state, not refresh of ghost
state count                               → excludes expired state
positive/negative state query             → excludes expired state
observer                                  → receives STATE_EXPIRED at physical expiry
```

There is no externally observable stale interval by design.

Owner death may physically remove the state earlier through defeat cleanup.

---

# 9. ActionProgressTracker contract

Stage10 adds battle-scoped:

```text
BattleContext.action_progress: ActionProgressTracker
```

The tracker records:

```text
owner reached UNIT_ACTION_START timing in combat round R
```

It does **not** mean:

```text
owner successfully executed a normal action
owner performed a normal attack
owner was not stunned
```

`mark_action_start(owner_id, R)` occurs when the engine reaches the action-start lifecycle node, before Stage10 action-start opportunity collection.

Therefore stun/control may suppress later action behavior without changing the fact that the owner consumed that round's persistent action-start timing.

Stage10 action-start persistent opportunity invariant:

```text
max 1 per owner per combat round
```

A second synthetic/duplicate action-start call in the same combat round cannot create a second Stage10 persistent opportunity.

---

# 10. R6 · Authoritative defeat cleanup

Stage10 introduces one synchronous typed port:

```text
DefeatCleanupPort
```

Equivalent conceptual API:

```text
commit_defeat(context, defeated_unit_id, defeat_source_ref)
→ DefeatCleanupResult
```

It is called only on the alive → defeated edge after troop mutation.

## 10.1 Ownership

```text
TroopSystem
→ actual troop mutation only

destructive settlement owner
→ detects alive→dead edge
→ calls DefeatCleanupPort synchronously

DefeatCleanupPort
→ coordinates hard defeat boundary
→ calls StateLifecycleSystem.clear_owner_on_defeat
→ returns typed cleanup fact

StateLifecycleSystem
→ physically removes states

ExecutionRightSystem
→ subsequent state/action execution queries deny the defeated owner
```

No EventBus subscriber and no individual state resolver owns cleanup.

## 10.2 All destructive paths

The port is mandatory for every troop-loss path capable of producing death:

```text
standard DamageResolutionSystem target settlement
PERIODIC_DAMAGE standard settlement
Counter standard settlement
Share attributed direct loss
Distribution attributed direct loss
Cleave target settlement
Cleave partition direct loss
Chain restricted feedback settlement
any later Stage9 troop-loss resolver
```

Share / Distribution DirectTroopLoss remains DirectTroopLoss; using the defeat port does not upgrade it into a DamageEvent.

## 10.3 Exact death ordering

For a destructive settlement:

```text
TroopSystem mutation
→ compute death edge
→ publish the settlement's existing damage/direct-loss observation fact
→ if death edge:
     DefeatCleanupPort.commit_defeat
       → clear attached states deterministically
       → execution right becomes unavailable
     → publish existing UNIT_DEFEATED observation fact
→ return typed settlement result
→ current coordinator observes death for victory/finalization
→ DamageAftermathPort receives fact if this operation has an aftermath topology
→ reactions / admitted local drain continue only where their frozen contracts permit
```

The EventBus facts do not drive any step above.

Fatal target damage creates no FIRST_AID recovery because the aftermath fact is marked defeated after cleanup.

## 10.4 Defeat-removal event semantics

Chosen representation:

```text
natural expiry
→ STATE_EXPIRED

defeat cleanup
→ STATE_REMOVED
   removal_reason = OWNER_DEFEATED
```

States are removed in deterministic `instance_id` order. A dedicated new EventBus gameplay controller is forbidden.

---

# 11. R7 · Battle-authoritative SkillRuntime registry

Stage10 adds a battle-scoped authoritative registry:

```text
BattleContext.skill_runtimes: SkillRuntimeRegistry
```

`BattleSystems` composes consumers of this registry but does not keep a second skill-runtime truth.

## 11.1 Key and registration

Primary key:

```text
(owner_id, SkillSlot)
```

`skill_id` is **not** part of the key because Stage6 already freezes one loaded skill per owner slot. It is an invariant validated against the located runtime.

Registration occurs during battle setup after validated `LoadedSkillSet` construction and before PRE_BATTLE rule/state application.

Duplicate `(owner_id, slot)` registration is an error.

## 11.2 Lookup semantics

```text
lookup(owner_id, slot, expected_skill_id)
→ SkillRuntime
```

Validation:

```text
owner/slot must exist
runtime.definition.skill_id must equal expected_skill_id
```

Source death:

```text
does NOT remove SkillRuntime entry
does NOT automatically set SkillRuntime.enabled = false
```

`SkillRuntime.enabled` remains available for explicit temporary skill active/inactive control.

Therefore:

```text
source dead
!=
temporary skill disabled
```

---

# 12. PersistentSourceSkillGate closure

Exactly three modes remain:

```text
ALWAYS_ACTIVE
QUERY_SKILL_RUNTIME
EXTERNAL_LIFECYCLE
```

## 12.1 ALWAYS_ACTIVE

The already-created persistent generation never dynamically queries source skill runtime.

Source death has no generic effect.

## 12.2 QUERY_SKILL_RUNTIME

Each opportunity queries only the registered source skill's explicit temporary active/inactive fact:

```text
SkillRuntime.enabled
```

It must **not** implicitly query:

```text
source alive
source can act
source action permission
```

unless a future Gameplay Authority explicitly requires those facts.

## 12.3 EXTERNAL_LIFECYCLE

R1-C chooses one meaning:

```text
external authoritative owner physically removes/replaces the persistent state through StateLifecycleSystem
```

It does **not** mean a per-opportunity `is_external_active()` callback.

While the state physically exists, Stage10 does not add a second dynamic gate for EXTERNAL_LIFECYCLE.

---

# 13. R8 · Physical state identity vs application generation

Stage10 distinguishes:

```text
StateInstance.instance_id
= physical container identity

StateApplicationGenerationId
= immutable identity of one successful application/refresh generation
```

R1-C chooses to retain the physical `instance_id` on same-name refresh as an engineering decision, but every successful application or refresh allocates a **new generation id**.

## 13.1 Generation snapshot

A generated Effect/opportunity carries an immutable snapshot equivalent to:

```text
StateGenerationSnapshot
- physical_instance_id
- application_generation_id
- state_id
- owner_id
- source_id
- source_skill_id
- source_skill_slot
- runtime_params snapshot
- lifecycle window snapshot
- damage/recovery basis snapshot
```

No generated work may JIT-read a later generation's `StateInstance.runtime_params`.

Required behavior:

```text
generation 3 produces Effect E
→ physical instance refreshes to generation 4
→ E executes later
→ E still uses generation 3 snapshot
```

Refresh updates together:

```text
application generation
source provenance
source skill provenance
potency snapshot
damage/recovery basis
first eligible round
last eligible round
```

---

# 14. STATE_REFRESHED semantics

Refresh is a StateLifecycleSystem mutation, not EventBus control flow.

Chosen observation fact:

```text
STATE_REFRESHED
```

Minimum typed payload:

```text
physical_instance_id
state_id
owner_id
old_application_generation_id
new_application_generation_id
old_source_id
new_source_id
old_source_skill_id
new_source_skill_id
old_source_skill_slot
new_source_skill_slot
old_first_eligible_round
new_first_eligible_round
old_last_eligible_round
new_last_eligible_round
old_runtime_params_type
new_runtime_params_type
```

The physical mutation is complete before the event is published. Subscribers cannot perform refresh mutation.

---

# 15. R9 · Shared typed DamageAftermath contract

Stage10 introduces one shared port:

```text
DamageAftermathPort
```

All relevant target damage settlements produce one typed aftermath fact through this port. The port is not an EventBus subscriber.

## 15.1 DamageAftermathFact

Conceptual schema:

```text
DamageAftermathFact
- damage_instance_id
- target_id
- lineage / SourceType
- damage_type
- assigned_target_damage
- actual_target_troop_loss
- target_troops_after
- target_defeated
- hit_topology: DamageHitTopology
- zero_loss_cause: DamageZeroLossCause | None
- source_state_generation | None
```

`DamageHitTopology` must distinguish at least:

```text
RESOLVED_HIT
NO_RESOLVED_HIT_EVASION_OR_MISS
```

`DamageZeroLossCause` must distinguish at least:

```text
WEAKNESS_ZERO
BARRIER_ZERO
SETTLED_ZERO
```

A single `prevented: bool` is explicitly insufficient.

The fact factory derives these fields from typed Stage8 trace/result + Stage9 settlement result, not from EventBus history.

## 15.2 Required topology examples

```text
WEAKNESS_ZERO
→ resolved damage-event topology exists
→ actual_target_troop_loss = 0
→ FIRST_AID opportunity eligibility = YES

BARRIER_ZERO
→ resolved damage-event topology exists
→ actual_target_troop_loss = 0
→ FIRST_AID opportunity eligibility = YES

EVASION / MISS
→ no resolved-hit damage event
→ actual_target_troop_loss = 0
→ FIRST_AID opportunity eligibility = NO

positive nonfatal settlement
→ resolved hit
→ FIRST_AID opportunity eligibility = YES

fatal settlement
→ resolved hit
→ target_defeated = true
→ FIRST_AID opportunity eligibility = NO
```

This topology does not promote official EVASION/BARRIER state bindings; it only defines how those typed outcomes are consumed if/when an authorized binding produces them.

---

# 16. FIRST_AID eligibility V2

Exact predicate:

```text
FIRST_AID opportunity exists iff:

1. an effective FIRST_AID generation is attached to target
2. that generation is within its lifecycle
3. source-skill gate for that generation is operational
4. DamageAftermathFact represents a relevant source/event family
5. hit_topology == RESOLVED_HIT
6. target_defeated == false
7. target remains alive after settlement/defeat cleanup
```

Explicitly **not** required:

```text
ActualTargetTroopLoss > 0
recoverable_gap > 0
```

Therefore:

```text
weakness-zero → YES
barrier-zero  → YES
evasion       → NO
```

Share / Distribution `AttributedDirectTroopLoss` does not become FIRST_AID-eligible merely because it can kill a unit.

Stage9 `CHAIN_TRUE_FEEDBACK` remains restricted by its frozen reaction-permission contract. It may pass through the shared aftermath topology for explicit classification/audit, but the source-type permission result is `FIRST_AID NOT PERMITTED`; Stage10 does not silently widen Chain feedback into a normal DamageEvent.

---

# 17. Eligibility and potency are separate

## 17.1 TREATMENT_AMOUNT model

```text
resolved zero-loss hit
+
existing missing troops > 0
→ opportunity exists
→ probability may succeed
→ frozen treatment potency may recover > 0
```

The triggering loss amount is not the potency basis.

## 17.2 TRIGGER_DAMAGE_RATIO model

Dynamic potency input:

```text
ActualTargetTroopLoss
```

Therefore:

```text
resolved zero-loss hit
→ opportunity still exists
→ ratio nominal amount = 0
```

A zero nominal amount does not erase the opportunity.

---

# 18. R10 · Recovery RNG engineering determinism policy

Official hidden PRNG consumption is classified:

```text
probability == 1.0 official draw consumption = UNKNOWN / UNOBSERVABLE
recoverable_gap == 0 official draw consumption = UNKNOWN / UNOBSERVABLE
```

R1-C freezes a simulator-only policy:

```text
Every ADMITTED RecoveryOpportunity consumes exactly one
context.random.chance(probability) call,
including probability 0.0 and 1.0,
and regardless of current recoverable_gap.
```

The call happens only after:

```text
state/generation exists
opportunity timing is valid
source-skill active gate passes where applicable
target survives / remains alive
damage topology is eligible for FIRST_AID
```

`recoverable_gap` is **not** an eligibility gate.

Chosen rationale:

```text
stable replay
uniform opportunity semantics
future probability-modifier compatibility
minimal hidden short-circuit branches
auditability through one RNG call per admitted opportunity
```

Classification:

```text
ENGINEERING DETERMINISM
NOT OFFICIAL GAMEPLAY AUTHORITY
```

This policy must never be written back into Gameplay Authority as an observed game fact.

---

# 19. Full-troop recovery semantics

Forbidden:

```text
if target.troops == target.max_troops:
    return before opportunity
```

Required pipeline:

```text
opportunity admitted
→ simulator probability policy
→ if chance succeeds: resolve nominal amount
→ RecoveryRequest
→ RecoverySystem dynamic target/healing-ban policy
→ TroopSystem.restore cap
→ RecoveryResolvedResult(actual=0) when full
```

Stage7's existing `RecoveryResolvedResult(actual=0)` remains the terminal representation for an allowed full-troop recovery request.

---

# 20. R11 · RecoveryOpportunity type hierarchy

R1-C chooses **Model B: sibling typed rule intent**, not `RecoveryOpportunityEffect extends Effect`.

```text
RuleIntent
├─ ordinary Effect
└─ RecoveryOpportunity
```

Conceptually:

```text
TriggerIntentBatch
- ordered_intents: tuple[Effect | RecoveryOpportunity, ...]
```

`TriggerSystem` remains a pure collector and may only construct immutable intent.

For ordinary action-start hooks:

```text
RuleHookSystem
→ TriggerSystem.collect
→ ordered intents
→ Effect intents           → EffectExecutor
→ RecoveryOpportunity      → RecoveryOpportunitySystem
```

For damage aftermath:

```text
DamageAftermathSystem
→ TriggerSystem.collect_after_damage
→ RecoveryOpportunity only
→ RecoveryOpportunitySystem
```

The AfterDamage collector contract rejects ordinary DamageEffect/StateMutation intent. This prevents:

```text
DamageInstanceCoordinator
→ DamageAftermathSystem
→ EffectExecutor
→ DamageInstanceCoordinator
```

and therefore avoids a constructor/runtime recursion cycle.

`HookResolutionResult` must gain a typed ordered outcome union equivalent to:

```text
RuleIntentResult
= EffectExecutionResult
| RecoveryOpportunityResult
| AbortedRuleIntentResult
```

with one outcome per collected intent.

Stage7's original `effect_results` view may remain as a compatibility projection, but it is no longer the complete Stage10 hook result truth.

---

# 21. TriggerSystem purity remains frozen

TriggerSystem may:

```text
read StateRegistry
read immutable generation snapshots
read ActionProgressTracker
read typed RuleHook / DamageAftermathFact
construct typed intent
order intent deterministically
```

It must not:

```text
consume RNG
mutate troops
mutate states
call DamageSystem
call RecoverySystem
call RecoveryOpportunitySystem
publish EventBus facts as control flow
```

---

# 22. RecoveryOpportunitySystem ownership

Unique responsibilities:

```text
validate RecoveryOpportunity type/provenance/generation snapshot
validate target still alive
query PersistentSourceSkillGate when mode == QUERY_SKILL_RUNTIME
consume exactly one simulator probability draw for admitted opportunity
resolve frozen recovery potency
for damage-ratio model, read typed ActualTargetTroopLoss from aftermath snapshot
create RecoveryRequest
call RecoverySystem
return RecoveryOpportunityResult
```

It must not:

```text
mutate StateInstance
deal damage
own EventBus control flow
clamp troops directly
change lifecycle duration
query source alive as a hidden skill gate
```

`RecoverySystem` continues to own:

```text
recovery permission
TARGET_DEFEATED prevention
healing-ban handling
RecoveryRequest/Result semantics
TroopSystem.restore coordination
```

`TroopSystem` continues to own actual troop increase and cap.

---

# 23. R12 · Shared DamageAftermathPort

One production implementation only:

```text
DamageAftermathSystem implements DamageAftermathPort
```

The following routes must use it or an explicit restricted classification call:

```text
standard DamageInstance target settlement
PERIODIC_DAMAGE
multi-hit DamageInstances, one call per DamageInstance
Counter standard DamageInstance
Cleave derived target settlement
Chain restricted feedback classification
```

Forbidden:

```text
standard_first_aid callback
cleave_first_aid callback
periodic_first_aid callback
parallel hand-written eligibility checks
```

`BattleSystems.cleave_first_aid` is a migration target and must not survive as a Stage10 production path.

---

# 24. Standard DamageInstance exact Stage10 ordering

Stage10 inserts synchronous local aftermath work inside the already-admitted current DamageInstance. It is **not** a new `FutureBranchKind`.

## 24.1 NoPartition

```text
DamageSystem.calculate
→ Stage9 NoPartition plan
→ target DamageResolutionSystem settlement
→ DefeatCleanupPort if target defeated
→ Stage9 death observation / victory latch if defeated
→ DamageAftermathPort
   → fatal/no-hit/source-policy gate
   → FIRST_AID RecoveryOpportunity(s) if eligible
   → RecoveryOpportunitySystem
   → RecoverySystem
→ existing resolved-damage callbacks
→ reaction admission/handling under existing FutureAdmissionGate
→ complete current DamageInstance
→ finalization drain/barrier
```

Fatal target path reaches the aftermath port as `target_defeated=true` and creates no recovery opportunity.

## 24.2 Share

Frozen Stage9 partition arithmetic remains target-first.

Stage10 sequence:

```text
target settlement with Dtarget
→ DefeatCleanupPort if target defeated
→ target death observation
→ if target defeated:
     discard pending sharer loss
     no FIRST_AID
     finish current DamageInstance
→ else:
     target DamageAftermathPort
     → local FIRST_AID opportunity/recovery
     → commit Share AttributedDirectTroopLoss to sharer
     → DefeatCleanupPort if sharer dies
     → victory/finalization death observation for sharer
     → existing resolved-damage callbacks for the original target hit
→ complete current DamageInstance
```

Share direct loss never creates FIRST_AID.

## 24.3 Distribution

Stage9 already freezes participant-direct-loss drain before target settlement.

Stage10 sequence:

```text
immutable Distribution plan
→ participant direct-loss commits in frozen order
   → DefeatCleanupPort on each death edge
   → finalization may latch victory
→ target settlement with Dtarget
→ DefeatCleanupPort if target defeated
→ target death observation
→ DamageAftermathPort for target settlement
   → if target survives and source/event eligible, local FIRST_AID executes
→ existing resolved-damage callbacks attempt their normal admission
→ complete current DamageInstance
```

If victory was latched by an earlier Distribution participant death:

```text
current Distribution transaction was already admitted
+
current target settlement is already admitted local work
+
FIRST_AID aftermath is a completion-local component of that admitted target settlement
→ it still drains
```

However new global future branches requested afterward remain denied by `FutureAdmissionGate`.

## 24.4 Cleave

The existing parallel `cleave_first_aid` callback is removed in Stage10 build.

Cleave uses:

```text
Cleave derived hit topology
→ partition plan
→ Distribution participant direct losses first when applicable
→ Cleave target troop settlement
→ DefeatCleanupPort if defeated
→ shared DamageAftermathPort
→ FIRST_AID local recovery if permitted
→ Share direct loss after surviving target aftermath when applicable
→ existing attacker-recovery contract
→ existing resolved-damage callbacks / deferred Chain timing
→ complete admitted Cleave local damage
```

This intentionally closes the Stage9 implementation asymmetry where Cleave's Share direct loss previously occurred before its dedicated FIRST_AID callback.

Cleave remains derived damage and does not re-enter the standard Stage8 base formula/modifier pipeline.

---

# 25. Victory latch and local aftermath

Distinguish:

```text
VICTORY_LATCHED
!=
FINALIZED
```

A FIRST_AID opportunity belonging to the current admitted target settlement is local drain, not global future admission.

Therefore:

```text
victory latched before current target aftermath
+
target survived
+
current DamageInstance/derived local damage already admitted
→ local aftermath may complete
```

But FIRST_AID never resurrects a defeated target because defeat cleanup and fatal classification happen first.

---

# 26. Source death vs owner death

## OWNER DEATH

```text
DefeatCleanupPort
→ clear attached states
→ deny future state opportunities
→ abort remaining owner-state resolution
→ deny later state application to dead owner
```

## SOURCE DEATH

```text
does not generically remove already-applied persistent state
does not invalidate historical source provenance
does not remove SkillRuntimeRegistry identity
does not automatically disable SkillRuntime.enabled
```

Continuous damage uses the historical source ref + frozen application basis.

The only source-death removals are those already assigned to explicit external lifecycle owners, such as an authorized command-aura lifecycle.

---

# 27. Same-name refresh transaction

For the eight Stage10 families:

```text
incoming same-name state on same owner
→ StateLifecycleSystem finds current effective physical instance
→ allocate new StateApplicationGenerationId
→ atomically replace source/provenance/runtime/lifecycle generation fields
→ retain physical instance_id (R1-C engineering choice)
→ publish STATE_REFRESHED observation
```

The registry must never expose an intermediate state where old and new generations are both effective.

---

# 28. Old synthetic Stage7 params migration boundary

Stage10 build must not maintain parallel official production paths.

| Old type/path | Stage10 replacement | Final status after Stage10 build |
|---|---|---|
| `PeriodicDamageStateParams` | `ContinuousDamageStateParams` + `FrozenContinuousDamageBasis` | `TEST-ONLY LEGACY SYNTHETIC`; forbidden on official Stage10 definitions |
| `PeriodicRecoveryStateParams` | `RecuperationStateParams` + `RecoveryOpportunity` | `TEST-ONLY LEGACY SYNTHETIC`; forbidden on official Stage10 definitions |
| Stage7 direct periodic `DamageEffect(coefficient)` official mapping | generation-snapshot periodic intent carrying frozen basis | `DEPRECATED FOR OFFICIAL STATES` |
| fixed-amount Stage7 periodic RecoverEffect official mapping | recovery opportunity + frozen recovery potency | `DEPRECATED FOR OFFICIAL STATES` |
| `BattleSystems.cleave_first_aid` callback | shared `DamageAftermathPort` | `DELETE FROM PRODUCTION COMPOSITION` |

Synthetic Stage7 regressions may keep the old params to protect historical infrastructure behavior, but official state definitions may not reference them.

---

# 29. Official Stage10 runtime params

Minimum typed families:

```text
ContinuousDamageStateParams
- application_generation_id
- lifecycle_window
- frozen_damage_basis
- source_skill_gate

FirstAidStateParams
- application_generation_id
- lifecycle metadata
- probability
- recovery_model_kind: TREATMENT_AMOUNT | TRIGGER_DAMAGE_RATIO
- frozen recovery potency context
- source_skill_gate

RecuperationStateParams
- application_generation_id
- lifecycle_window / battle-long lifecycle kind
- probability
- frozen recovery potency context
- source_skill_gate
```

Every nested object is frozen/typed/validated. No executable callbacks live inside params.

---

# 30. Evidence Gate boundary

Stage10 does not use persistent-state work to silently promote unrelated official mechanisms.

Still not authorized by Stage10 alone:

```text
EVASION official production binding
BARRIER official production binding
CRITICAL official production binding
STRATEGY_CRITICAL official production binding
DAMAGE_REDUCTION_PIERCE official production binding
positive dispel universal behavior
```

S10 targeted research may use evasion/barrier topology to define FIRST_AID aftermath behavior without authorizing their complete state implementation.

---

# 31. Dependency graph V2

Normative dependency direction:

```text
BattleContext
├─ UnitRuntime roster
├─ StateRegistry
├─ SkillRuntimeRegistry
├─ ActionProgressTracker
├─ RandomSystem
└─ OperationIdAllocator

AttributeSystem
TroopSystem
StateLifecycleSystem
ExecutionRightSystem
SkillRuntimeRegistry/Lookup
        ↓
DefeatCleanupPort
        ├─ StateLifecycleSystem
        └─ ExecutionRightSystem

RecoverySystem
        └─ TroopSystem

RecoveryOpportunitySystem
        ├─ SkillRuntimeRegistry/Lookup
        └─ RecoverySystem

ContinuousDamageBasisProducer
        ├─ Attribute / Stage8 rule-provider inputs
        └─ Stage8 typed formula/modifier policy components

DamageSystem
        ├─ AttributeSystem
        ├─ Stage8 rule provider
        ├─ Prevention
        ├─ HitResolution
        ├─ FormulaPolicy
        └─ ModifierSystem

DamageResolutionSystem
        ├─ DamageSystem
        ├─ TroopSystem
        └─ DefeatCleanupPort

DirectTroopLossResolver
        ├─ TroopSystem
        └─ DefeatCleanupPort

TriggerSystem
        └─ reads BattleContext typed facts only

DamageAftermathSystem / Port
        ├─ TriggerSystem
        └─ RecoveryOpportunitySystem

DamageInstanceCoordinator
        ├─ DamageSystem
        ├─ DamageResolutionSystem
        ├─ DamagePartitionCoordinator
        ├─ DirectTroopLossResolver
        ├─ DamageAftermathPort
        └─ BattleFinalizationCoordinator

CleaveDerivedDamageResolver
        ├─ TroopSystem
        ├─ DefeatCleanupPort
        ├─ DamagePartitionCoordinator
        ├─ DirectTroopLossResolver
        ├─ HitResolutionSystem
        ├─ DamageAftermathPort
        └─ BattleFinalizationCoordinator

ChainSystem
        ├─ TroopSystem
        ├─ DefeatCleanupPort
        └─ BattleFinalizationCoordinator

EffectExecutor
        ├─ DamageInstanceCoordinator
        ├─ StateLifecycleSystem
        └─ RecoverySystem

RuleHookSystem
        ├─ TriggerSystem
        ├─ EffectExecutor
        ├─ RecoveryOpportunitySystem
        └─ ExecutionRightSystem

BattleEngine
        └─ BattleSystems composition root
```

## 31.1 Cycle analysis

Constructor dependency:

```text
DamageInstanceCoordinator
→ DamageAftermathSystem
→ RecoveryOpportunitySystem
→ RecoverySystem
→ TroopSystem
```

There is no edge back to EffectExecutor or DamageInstanceCoordinator.

Runtime callback dependency:

```text
DamageAftermathSystem
→ TriggerSystem.collect_after_damage
→ RecoveryOpportunitySystem
```

The AfterDamage collector is type-restricted from returning ordinary DamageEffect, so it cannot re-enter DamageInstanceCoordinator.

Type/import dependency:

Shared DTOs (`DamageAftermathFact`, `RecoveryOpportunity`, generation IDs) must live in neutral contract modules. They may not import service implementations.

The existing Stage9 one-time `DamageResolutionSystem.bind_coordinator(...)` permit-validation binding is retained as a previously frozen typed late-binding seam. Stage10 adds no second service locator, callback lambda cycle, or post-construction mutation trick.

---

# 32. BattleSystems composition root V2

Plausible construction order:

```text
1. battle-scoped registries / typed context stores
   - StateRegistry
   - SkillRuntimeRegistry
   - ActionProgressTracker

2. low-level pure/mutation systems
   - AttributeSystem
   - TroopSystem
   - StateLifecycleSystem
   - ExecutionRightSystem

3. defeat cleanup
   - DefeatCleanupPort(StateLifecycleSystem, ExecutionRightSystem)

4. recovery
   - RecoverySystem(TroopSystem)
   - RecoveryOpportunitySystem(RecoverySystem, skill-runtime lookup)

5. Stage8 calculation components
   - rule provider
   - Prevention / Hit / FormulaPolicy / Modifier
   - ContinuousDamageBasisProducer
   - DamageSystem

6. destructive Stage9 systems
   - DamageResolutionSystem(DamageSystem, TroopSystem, DefeatCleanupPort)
   - DirectTroopLossResolver(TroopSystem, DefeatCleanupPort)
   - partition/finalization/future-admission systems

7. TriggerSystem

8. DamageAftermathSystem(TriggerSystem, RecoveryOpportunitySystem)

9. DamageInstanceCoordinator(..., DamageAftermathPort, finalization)
   - perform the existing one-time typed coordinator permit binding

10. Cleave / Chain / Counter systems
    - all receive DefeatCleanupPort / DamageAftermathPort as required

11. EffectExecutor

12. RuleHookSystem

13. Action / NormalAttack systems

14. BattleEngine
```

Forbidden:

```text
global singleton
service locator
untyped dependency dict
circular lambda capture
new arbitrary post-construction backpatch
```

---

# 33. FIRST_AID / aftermath source-family permissions

Shared aftermath topology does not erase Stage9 source identity.

| SourceType / route | Aftermath fact | FIRST_AID permission |
|---|---|---|
| standard normal/skill DamageInstance | YES | YES if resolved-hit + survived |
| PERIODIC_DAMAGE | YES | YES if resolved-hit + survived |
| multi-hit | one fact per DamageInstance | YES independently per eligible hit |
| COUNTER standard damage | YES | YES if existing Stage9 permission allows standard damage callbacks |
| CLEAVE derived damage | YES | YES per frozen Cleave recovery permission |
| CHAIN_TRUE_FEEDBACK | restricted classification fact | NO; Stage9 restricted feedback permission remains frozen |
| SHARE_DIRECT_LOSS | no DamageEvent aftermath | NO |
| DISTRIBUTION_DIRECT_LOSS | no DamageEvent aftermath | NO |

---

# 34. Mandatory regression plan V2

No tests are written in R1-C, but the next build/audit must include at least:

```text
LIFECYCLE
- PRE_BATTLE N=1 → Round1 exactly one opportunity
- PRE_BATTLE N=2 → Round1 + Round2 exactly
- apply before owner ActionStart in R → R eligible
- apply after owner ActionStart in R → first R+1
- refresh before action → new generation R eligible
- refresh after action → new generation starts R+1
- last eligible window complete → physical state absent immediately afterward
- suppressed opportunity → clock continues, no catch-up

GENERATION
- refresh generation 3 → 4
- pending generation-3 Effect executes with generation-3 snapshot
- STATE_REFRESHED reports old/new generation

FIRST_AID AFTERMATH
- weakness-zero → opportunity YES
- barrier-zero → opportunity YES
- evasion/miss → opportunity NO
- positive nonfatal loss → opportunity YES
- fatal loss → cleanup then opportunity NO
- zero-loss + existing missing troops + treatment model → may recover >0
- zero-loss + ratio model → opportunity exists, nominal ratio amount 0
- zero-loss + full troops → opportunity executes; successful recovery resolves actual 0

RECUPERATION
- full troops → opportunity not skipped
- source-skill inactive → opportunity suppressed without pausing finite lifecycle

RNG
- probability == 1.0 → exactly one simulator probability draw per admitted opportunity
- probability == 0.0 → exactly one simulator probability draw per admitted opportunity
- recoverable_gap == 0 → does not suppress admitted opportunity draw
- ineligible aftermath → zero recovery probability draws

DEATH
- owner dies during hook batch → cleanup synchronously; remaining owner-state intents aborted
- future state application to dead owner rejected
- source dies before DOT tick → existing target state survives and later tick executes
- Chain/direct/Cleave death paths all call one defeat cleanup port

STAGE8
- LIVE_RUNTIME exact golden regression unchanged
- FROZEN_APPLICATION does not read current source formula facts
- FROZEN_APPLICATION does not rediscover current ordinary modifiers
- FROZEN_APPLICATION locked modifier/crit decisions do not reroll
- base-formula tick RNG follows existing Stage8 formula path
- REBELLION locked route + ignore-defense policy consumed
- source-dead historical periodic source accepted only on authorized frozen lane
- trace never marks skipped stage EXECUTED

STAGE9 / AFTERMATH
- NoPartition target aftermath before callbacks
- Share target aftermath before sharer DirectTroopLoss
- Distribution participant direct loss drains before target settlement
- victory latched during admitted Distribution still allows current target local FIRST_AID aftermath
- Share/Distribution DirectTroopLoss never triggers FIRST_AID
- Cleave uses same DamageAftermathPort as standard damage
- no `cleave_first_aid` production path remains
- Chain restricted feedback remains FIRST_AID-ineligible
```

Hardening also requires:

```text
property tests for lifecycle windows
conformance suite for all death-capable troop-loss paths
RNG spy/golden sequence tests
static dependency/import/constructor DAG tests
no EventBus gameplay subscribers
LIVE_RUNTIME exact golden suite
```

---

# 35. Finding Closure Matrix

`REPAIR CLAIMED` means the authoring pass supplied an explicit design answer. It does **not** mean the independent re-audit has accepted it.

| Audit Finding | Severity | R1-C repair | Status |
|---|---|---|---|
| S10-A-B01 Stage7 execute-all vs death hard termination | BLOCKER | Stage7 compatibility addendum; typed abort tail; execution-right recheck | `REPAIR CLAIMED` |
| S10-A-B02 Stage8 reopen only declared informally | BLOCKER | formal Stage8 compatibility addendum | `REPAIR CLAIMED` |
| S10-A-B03 FROZEN_APPLICATION producer/math ownership ambiguous | BLOCKER | frozen-input model + unique per-layer matrix | `REPAIR CLAIMED` |
| S10-A-B04 PRE_BATTLE off-by-one | BLOCKER | separate PRE_BATTLE domain; first=1 | `REPAIR CLAIMED` |
| S10-A-B05 no authoritative defeat cleanup checkpoint | BLOCKER | one DefeatCleanupPort across all death paths | `REPAIR CLAIMED` |
| S10-A-B06 SkillRuntime lookup not authoritative | BLOCKER | BattleContext SkillRuntimeRegistry keyed owner+slot | `REPAIR CLAIMED` |
| S10-A-B07 hidden recovery RNG semantics exceed authority | BLOCKER | official UNKNOWN isolated; simulator one-draw policy labeled engineering | `REPAIR CLAIMED` |
| S10-A-M01 refresh provenance spans generations | MAJOR | StateApplicationGenerationId + immutable generation snapshot | `REPAIR CLAIMED` |
| S10-A-M02 DamagePipelineTrace choice deferred | MAJOR | separate typed frozen_application_trace selected | `REPAIR CLAIMED` |
| S10-A-M03 old synthetic params migration absent | MAJOR | explicit TEST-ONLY migration table | `REPAIR CLAIMED` |
| S10-A-M04 RecoveryOpportunity hierarchy incomplete | MAJOR | Model B sibling RuleIntent + unique RecoveryOpportunitySystem | `REPAIR CLAIMED` |
| S10-A-M05 EXTERNAL_LIFECYCLE ambiguous | MAJOR | external physical removal ownership only | `REPAIR CLAIMED` |
| S10-A-M06 standard/Cleave aftermath divergent | MAJOR | one DamageAftermathPort; parallel Cleave callback removed | `REPAIR CLAIMED` |
| S10-A-N01 historical source identity underdefined | MINOR | HistoricalDamageSourceRef + roster identity / no alive requirement | `REPAIR CLAIMED` |
| S10-A-N02 defeat cleanup event semantics | MINOR | STATE_REMOVED + OWNER_DEFEATED reason; deterministic order | `REPAIR CLAIMED` |
| S10-A-N03 nested numeric validation ownership | MINOR | nested value types validate numbers; outer validates cross-fields | `REPAIR CLAIMED` |
| S10-A-N04 STATE_REFRESHED payload underspecified | MINOR | old/new generation + provenance/lifecycle typed payload | `REPAIR CLAIMED` |
| S10-A-H01 lifecycle property tests | HARDENING | mandatory regression plan | `ACCEPTED FOR BUILD` |
| S10-A-H02 death-path conformance suite | HARDENING | mandatory regression plan | `ACCEPTED FOR BUILD` |
| S10-A-H03 RNG spy/golden | HARDENING | mandatory regression plan | `ACCEPTED FOR BUILD` |
| S10-A-H04 dependency/static architecture tests | HARDENING | explicit DAG + forbidden edges | `ACCEPTED FOR BUILD` |
| S10-A-H05 LIVE_RUNTIME golden | HARDENING | exact backward-regression obligation | `ACCEPTED FOR BUILD` |

Summary:

```text
BLOCKER repaired claim = 7 / 7
MAJOR repaired claim   = 6 / 6
MINOR addressed        = 4 / 4
HARDENING accepted     = 5 / 5

Independent acceptance = NOT YET PERFORMED
```

---

# 36. Author self-audit scenarios

R1-C author self-audit requires two independent implementers reading this Draft V2 to produce the same observable contract for:

```text
PRE_BATTLE N=1
source dies before DOT tick
target dies mid-hook
same-name refresh before pending effect executes
weakness-zero FIRST_AID
barrier-zero FIRST_AID
evasion FIRST_AID
full-troop FIRST_AID
full-troop RECUPERATION
probability=100%
Share
Distribution
Cleave
victory latched during current DamageInstance
```

Author conclusion:

```text
PRE_BATTLE N=1
→ Round1 exactly one opportunity, then physical expiry at end of ActionStart window

source dies before DOT tick
→ state persists; frozen source basis executes; dead source live validation not required

target dies mid-hook
→ synchronous cleanup; remaining owner-state intents aborted

refresh before pending effect executes
→ pending effect remains bound to old generation snapshot

weakness-zero
→ FIRST_AID YES

barrier-zero
→ FIRST_AID YES

evasion/miss
→ FIRST_AID NO

full-troop FIRST_AID / RECUPERATION
→ opportunity not skipped; simulator probability policy still applies; successful RecoverySystem resolution may actual=0

probability=100%
→ exactly one simulator RNG chance draw per admitted opportunity; ENGINEERING ONLY

Share
→ target settlement → cleanup if fatal → target aftermath if alive → sharer direct loss

Distribution
→ participant direct losses → target settlement → cleanup → local target aftermath; admitted drain survives victory latch

Cleave
→ shared DamageAftermathPort; no parallel first-aid callback

victory latched during current DamageInstance
→ no new global branch, but already-admitted local target aftermath drains if target survived
```

No remaining item above is intentionally delegated to “implementation decides”.

---

# 37. R1-C completion claim

```text
1. 7 BLOCKER explicit repair                      YES
2. 6 MAJOR explicit repair                        YES
3. Stage7 compatibility reopen documented         YES
4. Stage8 compatibility reopen documented         YES
5. FROZEN_APPLICATION pipeline unique              YES
6. PRE_BATTLE lifecycle fixed                      YES
7. physical expiration semantics unique            YES
8. defeat cleanup unique owner/checkpoint          YES
9. SkillRuntime lookup authority defined           YES
10. refresh generation provenance defined          YES
11. FIRST_AID zero-loss eligibility corrected      YES
12. evasion/barrier distinction represented        YES
13. full-troop opportunity not skipped             YES
14. hidden PRNG uncertainty isolated               YES
15. RecoveryOpportunity hierarchy closed           YES
16. shared DamageAftermathPort defined              YES
17. dependency graph analyzed as acyclic            YES
18. BattleSystems construction order plausible      YES
19. production code changed by R1-C                NO
20. document remains DESIGN DRAFT                  YES
```

Final authoring status:

```text
R1-C REPAIR COMPLETE
READY FOR INDEPENDENT DESIGN RE-AUDIT

DESIGN PASS                  = NOT CLAIMED
DESIGN FROZEN                = NO
PRODUCTION IMPLEMENTATION    = NOT AUTHORIZED
NEXT STEP                    = Stage10 Independent Design Re-Audit Round 2
```
