# Stage 10 · Persistent State Runtime Integration · Architecture Design Draft V4

> Repair: `Stage10 Design Repair R3-B / Final Contract Closure`  
> Status: `ARCHITECTURE DESIGN DRAFT V4`  
> Independent design audit: `FINAL INDEPENDENT FREEZE-GATE AUDIT REQUIRED`  
> Production implementation: `NOT AUTHORIZED`  
> Design freeze: `NOT AUTHORIZED`

---

# 0. R3-B input baseline

R3-B was authored from the real repository state following the Stage10 Independent Design Re-Audit Round 3 (`STAGE10_DESIGN_REAUDIT_R3.md`):

```text
Battle repo:
lxy2005051020-commits/sgs-v2-battle-system
branch: stage10-persistent-state-research
input HEAD: 4fb5b966b37648b3572e92451b9ad51aecce70bf (docs(stage10): add independent design re-audit round 3)
preceding HEAD: dfe9008ab74269c3239c214b65d25d626127884a (docs(stage10): repair round-2 architecture findings)

STAGE10.md Draft V3 input blob:
1519189a744a0a7c4b31f8e834a08b4df39496ad

STAGE10_DESIGN_REAUDIT_R3.md blob:
3d49cf575dec6596d76733a277283d32d3b1b6f7

STAGE7_STAGE10_COMPATIBILITY_ADDENDUM.md blob:
64cdb7d86c8bda5b9123b49afcb924db7e1fd485

STAGE8_STAGE10_COMPATIBILITY_ADDENDUM.md blob:
4c1e22eda97bdc0ef74ab6175a28672845771ddc

STAGE9_STAGE10_COMPATIBILITY_ADDENDUM.md blob:
737b058cefd08a1d0a08526436098a3455a8168f

Gameplay Authority repo:
lxy2005051020-commits/sgs-state-mechanics-research
branch: main
canonical authoritative HEAD: a9a05ceffa2a9489cdc1e0a000a4c27bac81a5fe
```

## 0.1 Authority synchronization status: PASS

Following Stage10 R2-A3 local provenance recovery and R2-A4 formal promotion, Gameplay Authority `main` at HEAD `a9a05ceffa2a9489cdc1e0a000a4c27bac81a5fe` contains:

```text
1. commit 4661f4ffa1074045ce17d9158499dc03a8dfbec3:
   - stage10/TARGETED_RESEARCH_S10_TR_01.md
   - stage10/TARGETED_RESEARCH_S10_TR_02.md
   - stage10/TARGETED_RESEARCH_S10_TR_03.md
   - stage10/research_tools/replay_inspector.py
   - stage10/research_tools/battle_log_analyzer.py
   - stage10/research_tools/state_matrix_generator.py
   - stage10/evidence/raw_logs/...
   - stage10/evidence/parsed_tables/...

2. commit 0b9e172a4d3ce3b29025347b086738c0253e56ac:
   - states/persistent/first_aid/MECHANISM_CONTRACT.md (zero-loss, full-troop, and trigger eligibility alignment)

3. commit a9a05ceffa2a9489cdc1e0a000a4c27bac81a5fe:
   - PROMOTION_STAGE10_R2_A4.md (formal promotion record)
```

Authority synchronization is therefore complete (`Authority Sync = PASS`). The dual-evidence divergence noted in Draft V2 is fully resolved. Draft V3 binds directly to canonical Gameplay Authority HEAD `a9a05ceffa2a9489cdc1e0a000a4c27bac81a5fe`.

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

## 4.1 System Responsibilities, Boundaries & Typed Interface (S10-R2-M02, S10-R3-M02)

To eliminate ownership ambiguity between decision, dispatch, and execution, and to prevent reflection or duck-typing over heterogeneous intents, responsibilities are partitioned strictly:

```text
1. Decision Owner: ExecutionRightSystem
   - Authoritative decision maker for intent/effect admissibility.
   - Evaluates evaluate_rule_intent(descriptor, context).
   - Validates live unit status, suppression, and defeat state using typed descriptor.
   - Performs ZERO troop mutations, ZERO state mutations, ZERO dispatch, ZERO control-flow events.
   - Returns typed ExecutionRightDecision with explicit reason and scope.

2. Dispatch Owner: RuleHookSystem
   - Manages hook registration, batch iteration, and loop control.
   - Dispatches each collected intent to ExecutionRightSystem via intent.execution_descriptor prior to execution.
   - Enforces abort scope actions (e.g. discarding only current intent on REJECT_CURRENT, discarding remaining intents for the defeated owner on ABORT_OWNER_STATE_REMAINDER, or halting the hook batch on ABORT_HOOK).
   - Performs NO independent gameplay permission or alive checks.

3. Execution Router: EffectExecutor
   - Pure execution worker.
   - Executes already-admitted Effect objects through domain handlers (DamageInstanceCoordinator, StateLifecycleSystem, RecoverySystem).
   - Performs NO secondary gameplay permission, suppression, or defeat arbitration.

4. Cleanup Port: DefeatCleanupPort
   - Coordinates synchronous state cleanup upon unit defeat across all death paths.

5. State Owner: StateLifecycleSystem
   - Owns physical container creation, refresh, and removal.

6. Observation: EventBus
   - Strictly observational; no gameplay control flow or side-effects.
```

### 4.1.1 Typed Descriptor Specification (S10-R3-M02)

Every `RuleIntent` (`Effect` and `RecoveryOpportunity`) must immutably carry an explicit typed descriptor populated at creation time by `TriggerSystem` (or factory):

```python
@dataclass(frozen=True, slots=True)
class RuleIntentExecutionDescriptor:
    intent_kind: RuleIntentKind           # EFFECT | RECOVERY_OPPORTUNITY
    intent_owner_id: str                  # Hook actor / submitter of the intent batch
    state_owner_id: str | None            # Unit to which state is physically attached (if state-driven)
    target_id: str | None                 # Primary target unit id (or None for untargeted effects)
    source_ref: DamageSourceRef | None    # Historical / live source ref
    state_instance_id: str | None         # Physical state instance id (if state-driven)
    state_generation_id: StateApplicationGenerationId | None # Immutable generation id
    execution_domain: str                 # "STATE_RESOLUTION", "ACTION", "AFTERMATH", etc.
```

**Disambiguation of Actor, Owner, and Target**:
- `intent_owner_id`: The unit acting or initiating the hook batch (e.g. hook actor).
- `state_owner_id`: The physical bearer of the persistent state (i.e. `state.owner_id`). When this unit dies, all remaining state-resolution intents for this state terminate. For persistent state resolution at `UNIT_ACTION_START`, `state_owner_id == intent_owner_id`.
- `target_id`: The recipient/victim of the effect (e.g. the unit being damaged or healed). For multi-target effects, each resolved `RuleIntent` carries its specific single `target_id`.
- Untargeted intents (e.g. field aura or global state update) set `target_id = None`.

**Normative Method Signature**:
```python
ExecutionRightSystem.evaluate_rule_intent(
    descriptor: RuleIntentExecutionDescriptor,
    context: BattleContext,
) -> ExecutionRightDecision
```

`ExecutionRightSystem` reads only typed fields from `RuleIntentExecutionDescriptor` and `BattleContext`. It is strictly forbidden from using `hasattr`, `isinstance`, or reflection to probe heterogeneous intent objects.

## 4.2 Orthogonal ExecutionRight Decisions & Decision Matrix (S10-R3-B01)

To strictly prevent conflation between **Target Defeat** and **State Owner Defeat**, the decision model is partitioned orthogonally into distinct typed outcomes:

```python
class ExecutionRightDecisionKind(str, Enum):
    ALLOW = "ALLOW"
    REJECT_CURRENT = "REJECT_CURRENT"
    ABORT_OWNER_STATE_REMAINDER = "ABORT_OWNER_STATE_REMAINDER"
    ABORT_HOOK = "ABORT_HOOK"

class ExecutionRightReason(str, Enum):
    TARGET_DEFEATED = "TARGET_DEFEATED"
    OWNER_DEFEATED = "OWNER_DEFEATED"
    STATE_NOT_FOUND = "STATE_NOT_FOUND"
    SUPPRESSED = "SUPPRESSED"
    BATTLE_FINALIZED = "BATTLE_FINALIZED"
    INVALID_TARGET = "INVALID_TARGET"
```

```text
ALLOW
→ Intent is admitted and forwarded to EffectExecutor or RecoveryOpportunitySystem. Batch continues normally.

REJECT_CURRENT(reason = TARGET_DEFEATED | SUPPRESSED | ...)
→ ONLY the current intent is rejected.
→ Reason TARGET_DEFEATED means descriptor.target_id is dead (target.is_alive == False).
→ This rejection is strictly local to the dead target.
→ Subsequent unrelated intents in the batch (including intents by the same owner targeting other living units) CONTINUE evaluation!

ABORT_OWNER_STATE_REMAINDER(reason = OWNER_DEFEATED)
→ The state-resolution owner is defeated (descriptor.state_owner_id is dead).
→ Current intent is aborted.
→ All remaining intents in the current batch belonging to the same state_owner_id are discarded.
→ Intents belonging to other living owners in the same batch CONTINUE evaluation!

ABORT_HOOK(reason = BATTLE_FINALIZED | ...)
→ Critical execution boundary violation. Entire hook batch terminates immediately.
```

### 4.2.1 Normative Decision Matrix (S10-R3-B01)

| Condition | Decision Kind | Reason | Action Taken by RuleHookSystem |
|---|---|---|---|
| Target alive (`is_alive == True`), state owner alive | `ALLOW` | `None` | Forward intent to executor; batch continues |
| Target defeated (`is_alive == False`), state owner alive | `REJECT_CURRENT` | `TARGET_DEFEATED` | Record rejected result for current intent; **continue batch for subsequent intents** |
| State owner defeated (`is_alive == False`) | `ABORT_OWNER_STATE_REMAINDER` | `OWNER_DEFEATED` | Record abort for current intent; **discard all remaining intents with same `state_owner_id`**; continue other owners |
| Physical state not found / expired | `REJECT_CURRENT` | `STATE_NOT_FOUND` | Record rejected result for current intent; subsequent intents evaluated individually |
| Action suppressed by control state (Stun/Amnesia) | `REJECT_CURRENT` | `SUPPRESSED` | Record rejected result for current intent; opportunity window consumed; clock continues |
| Battle finalized / victory latched | `ABORT_HOOK` | `BATTLE_FINALIZED` | Admitted work drains per Stage9 Addendum; halt all remaining batch execution |

## 4.3 Normative Timelines: Target Death vs Owner Death (S10-R3-B01)

### 4.3.1 Target Death Timeline (A / B / C / D Sequence)

Consider a hook producing multiple effects across units:
- **Intent A**: State owner $P_1$, target $P_2$. Deals damage to $P_2$ (reduces $P_2$ troops to 0).
- **Intent B**: State owner $P_1$, target $P_2$. Secondary effect on $P_2$.
- **Intent C**: State owner $P_1$, target $P_3$. Independent effect on living unit $P_3$.
- **Intent D**: State owner $P_4$, target $P_3$. Independent effect from different living owner $P_4$ on living unit $P_3$.

```text
1. Intent A evaluation:
   - RuleHookSystem requests evaluation from ExecutionRightSystem.
   - P1 alive, P2 alive → ExecutionRightSystem returns ALLOW.
   - RuleHookSystem forwards Intent A to EffectExecutor.
   - Damage settlement resolves; P2 troops reach 0 (P2 defeated).
   - Synchronous call to DefeatCleanupPort.commit_defeat(P2):
     * StateLifecycleSystem cleanses P2 states with reason OWNER_DEFEATED.
     * P2 is latched dead in UnitRegistry / BattleContext.

2. Intent B evaluation:
   - RuleHookSystem requests evaluation for Intent B (state_owner_id = P1, target_id = P2).
   - ExecutionRightSystem checks target P2: P2 is dead (target.is_alive == False).
   - State owner P1 is alive.
   - ExecutionRightSystem returns REJECT_CURRENT(reason = TARGET_DEFEATED).
   - RuleHookSystem records AbortedRuleIntentResult(reason = TARGET_DEFEATED) for Intent B.
   - Intent B is NEVER dispatched to EffectExecutor.
   - CRITICAL: P1's remaining intents are NOT aborted because P1 is alive!

3. Intent C evaluation:
   - RuleHookSystem requests evaluation for Intent C (state_owner_id = P1, target_id = P3).
   - State owner P1 is alive. Target P3 is alive.
   - ExecutionRightSystem returns ALLOW.
   - RuleHookSystem forwards Intent C to EffectExecutor.
   - Intent C executes normally!

4. Intent D evaluation:
   - RuleHookSystem requests evaluation for Intent D (state_owner_id = P4, target_id = P3).
   - State owner P4 is alive. Target P3 is alive.
   - ExecutionRightSystem returns ALLOW.
   - RuleHookSystem forwards Intent D to EffectExecutor.
   - Intent D executes normally!
```

**Deterministic Observable Behavior**: $A \text{ executes} \to B \text{ rejected (TARGET\_DEFEATED)} \to C \text{ executes} \to D \text{ executes}$.

### 4.3.2 Owner Death Timeline

Consider a hook where an intent causes the state-resolution owner to die:
- **Intent A**: State owner $P_1$, target $P_1$ (e.g. self-inflicted DOT tick reducing $P_1$ troops to 0).
- **Intent B**: State owner $P_1$, target $P_2$. Secondary effect belonging to $P_1$'s state.
- **Intent D**: State owner $P_4$, target $P_3$. Independent effect belonging to living owner $P_4$.

```text
1. Intent A evaluation:
   - P1 is alive → ExecutionRightSystem returns ALLOW.
   - Intent A resolves; P1 troops reach 0 (P1 defeated).
   - Synchronous call to DefeatCleanupPort.commit_defeat(P1):
     * StateLifecycleSystem cleanses P1 attached states with reason OWNER_DEFEATED.
     * P1 is latched dead in UnitRegistry / BattleContext.

2. Intent B evaluation:
   - RuleHookSystem requests evaluation for Intent B (state_owner_id = P1, target_id = P2).
   - ExecutionRightSystem detects state_owner_id P1 is dead.
   - ExecutionRightSystem returns ABORT_OWNER_STATE_REMAINDER(reason = OWNER_DEFEATED).
   - RuleHookSystem records AbortedRuleIntentResult(reason = OWNER_DEFEATED) for Intent B.
   - RuleHookSystem discards all remaining intents in batch where state_owner_id == P1.

3. Intent D evaluation:
   - RuleHookSystem evaluates Intent D (state_owner_id = P4, target_id = P3).
   - State owner P4 is alive. Target P3 is alive.
   - Intent D does NOT belong to defeated owner P1.
   - ExecutionRightSystem returns ALLOW.
   - RuleHookSystem forwards Intent D to EffectExecutor.
   - Intent D executes normally!
```

**Deterministic Observable Behavior**: $A \text{ executes (P1 dies)} \to B \text{ aborted (OWNER\_DEFEATED)} \to \text{remaining P1 discarded} \to D \text{ executes}$.

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

## 8.1 Battle-end Persistent State Teardown Semantics (S10-R2-M05)

Stage10 strictly distinguishes **Gameplay Expiration** from **Battle Teardown**:

```text
1. Gameplay Expiration:
   - Triggered when a state naturally reaches the end of its duration window (round == last_eligible_round).
   - Occurs at the completion of UNIT_ACTION_START.
   - Emits STATE_EXPIRED event.
   - Or triggered upon unit defeat via DefeatCleanupPort (emits STATE_REMOVED with reason OWNER_DEFEATED).

2. Battle Teardown (clear_all_on_battle_end):
   - Triggered ONLY upon battle completion/finalization.
   - Unique Owner: StateLifecycleSystem.clear_all_on_battle_end(context).
   - Execution Timing: Executes strictly AFTER victory is latched and all already-admitted work (including final local aftermath) is drained, immediately before returning the final BattleResult.
   - Target Scope: Cleanses all remaining persistent and temporary state instances across ALL units (both surviving winners and losers).
   - Observation: Emits observation-only non-gameplay event STATE_CLEARED_ON_BATTLE_END.
   - Guarantees zero state leakage into subsequent simulations or context reuse.
```

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

## 9.1 Exact Execution Ordering at UNIT_ACTION_START (S10-R2-N01)

To prevent nondeterministic interleaving between state decay, tracking, and trigger collection, the exact sequence of operations at the start of each unit action is frozen:

```text
1. Set Acting Unit:
   ActionProgressTracker.set_current_acting_unit(owner_id)

2. Increment Action Index & Mark Round Consumption:
   ActionProgressTracker.mark_action_start(owner_id, current_round)

3. Publish Action Start Observation:
   EventBus.publish(UNIT_ACTION_START, payload={unit_id: owner_id, round: current_round})

4. Evaluate Action-Start Triggers & Persistent Opportunities:
   TriggerSystem collects registered triggers for UNIT_ACTION_START.
   Persistent opportunities (e.g. RECUPERATION, DOT ticks) are collected into an immutable batch.

5. Execute Hook / Intent Batch:
   RuleHookSystem dispatches batch through ExecutionRightSystem -> EffectExecutor.

6. Synchronous Physical Expiration Check:
   For each state on owner:
     if current_round >= state.last_eligible_round:
       StateLifecycleSystem.expire_state(state, reason="DURATION_EXPIRED")

7. Hand off to Action Phase:
   Engine proceeds to regular action execution (Command / Active skills, Normal Attack).
```

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

## 12.1 Normative Mapping per State Family and Source Class (S10-R2-M03)

| State Family | Source Skill Class | Gate Mode | Operational Semantics |
|---|---|---|---|
| Periodic DOT (`BURN`, `FLOOD`, `POISON`, `ROUT`, `SANDSTORM`, `REBELLION`) | Active / Command / Passive | `ALWAYS_ACTIVE` | Never queries source skill runtime; source unit death or silence does not suppress DOT damage ticks. |
| `FIRST_AID` | Passive / Command | `QUERY_SKILL_RUNTIME` | Queries `SkillRuntime.enabled`. Temporary deactivation (e.g. 伪报 / 军心动摇) suppresses recovery opportunity; clock continues. |
| `FIRST_AID` | Active | `ALWAYS_ACTIVE` | Active skill buffs once applied run to duration completion; subsequent silence does not suppress opportunity. |
| `RECUPERATION` | Passive / Command | `QUERY_SKILL_RUNTIME` | Queries `SkillRuntime.enabled`. Temporary deactivation suppresses opportunity; clock continues. |
| `RECUPERATION` | Active | `ALWAYS_ACTIVE` | Buff runs to duration completion; cannot be silenced mid-duration. |
| External Aura (Field / Aura) | External Provider | `EXTERNAL_LIFECYCLE` | External system manages physical attachment and lifetime; if state physically attached, admitted. No dynamic per-opportunity callback. |

## 12.2 ALWAYS_ACTIVE

The already-created persistent generation never dynamically queries source skill runtime.

Source death has no generic effect.

## 12.3 QUERY_SKILL_RUNTIME

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

## 12.4 EXTERNAL_LIFECYCLE

Stage10 freezes exactly one meaning for `EXTERNAL_LIFECYCLE`:

```text
external authoritative owner physically removes/replaces the persistent state through StateLifecycleSystem
```

It does **not** mean a per-opportunity `is_external_active()` callback.

While the state physically exists on the target container, Stage10 does not add a second dynamic gate for EXTERNAL_LIFECYCLE.

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

## 13.2 StateApplicationGenerationId End-to-End Propagation Matrix (S10-R2-M04)

Every DTO, request, result, trace, and observation event in the persistent pipeline must carry `StateApplicationGenerationId` end-to-end:

| Pipeline Entity | Field Name | Type | Provenance Guarantee |
|---|---|---|---|
| `StateInstance` | `current_generation_id` | `StateApplicationGenerationId` | Allocated on initial apply or same-name refresh |
| `StateGenerationSnapshot` | `application_generation_id` | `StateApplicationGenerationId` | Captured immutably at opportunity collection time |
| `DamageRequest` | `source_generation_id` | `StateApplicationGenerationId \| None` | Attached when damage originates from persistent state |
| `DamageResult` | `source_generation_id` | `StateApplicationGenerationId \| None` | Preserved from request through Stage8/Stage9 pipeline |
| `RecoveryRequest` | `source_generation_id` | `StateApplicationGenerationId \| None` | Attached when recovery originates from persistent state |
| `RecoveryResult` | `source_generation_id` | `StateApplicationGenerationId \| None` | Preserved from recovery request through RecoverySystem |
| `DamageAftermathFact` | `source_state_generation` | `StateApplicationGenerationId \| None` | Links aftermath fact to triggering DOT / attack state |
| `DamagePipelineTrace` | `source_generation_id` | `StateApplicationGenerationId \| None` | Embedded in execution trace for deterministic audit |
| `STATE_APPLIED` event | `application_generation_id` | `StateApplicationGenerationId` | Authoritative generation identity of applied state |
| `STATE_REFRESHED` event | `old/new_generation_id` | `StateApplicationGenerationId` | Provenance transition audit |
| `STATE_EXPIRED` event | `application_generation_id` | `StateApplicationGenerationId` | Exact expiring generation identity |
| `STATE_REMOVED` event | `application_generation_id` | `StateApplicationGenerationId` | Exact removed generation identity |
| `DAMAGE_RESOLVED` event | `source_generation_id` | `StateApplicationGenerationId \| None` | Observation link to originating state generation |
| `RECOVERY_RESOLVED` event| `source_generation_id` | `StateApplicationGenerationId \| None` | Observation link to originating state generation |

## 13.3 Snapshot vs JIT Query Separation (S10-R2-M04)

To prevent runtime race conditions and generation leakage, Stage10 strictly partitions snapshot values from JIT queries:

```text
1. Snapshot at Generation Creation (Immutable):
   - Potency & Rates: recovery chance, treatment rate, ratio, base damage rate.
   - Source Attributes: strength, intellect at application time (for frozen formula).
   - Formula Policy: FROZEN_APPLICATION vs LIVE_RUNTIME.
   - Locked Decisions: crit roll locked, modifier plan locked.
   - Lifecycle Window: first_eligible_round, last_eligible_round.

2. JIT Queries at Opportunity Execution (Dynamic):
   - Source Skill Gate: SkillRuntime.enabled (queried only when mode == QUERY_SKILL_RUNTIME).
   - Target Survival: target.is_alive() and defeat status.
   - Target Missing Troops: target.troops < target.max_troops (for recovery amount clamping).
   - Dynamic Suppression: healing ban (CANNOT_BE_HEALED / 禁疗), dynamic damage barriers/reductions.
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
2. that generation is within its lifecycle window
3. source-skill gate for that generation is operational (PersistentSourceSkillGate)
4. DamageAftermathFact represents an authorized source/event family per ReactionPermissionPolicy.can_trigger_recovery(source_type) == True (includes NORMAL_ATTACK, ACTIVE_SKILL, PERIODIC_DAMAGE, CLEAVE, COUNTER, and ASSAULT)
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
ASSAULT hit   → YES (Pursuit_Counterattack authorized)
```

Share / Distribution `AttributedDirectTroopLoss` does not become FIRST_AID-eligible merely because it can kill a unit.

Stage9 `CHAIN_TRUE_FEEDBACK` remains restricted by its frozen reaction-permission contract. It may pass through the shared aftermath topology for explicit classification/audit, but the source-type permission result is `FIRST_AID NOT PERMITTED`; Stage10 does not silently widen Chain feedback into a normal DamageEvent.

`ReactionPermissionPolicy.can_trigger_recovery(source_type)` is the SINGLE AUTHORITATIVE PERMISSION OWNER for damage aftermath recovery eligibility.

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

## 18.0 Native RandomSystem Implementation Invariant (S10-R3-N01)

The existing production implementation in `sgs_v2/battle_core/random_system.py`:

```python
def chance(self, probability: float) -> bool:
    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability must be in [0.0, 1.0]")
    return self.random() < probability
```

already evaluates `self.random() < probability` unconditionally, with zero short-circuit shortcuts for `probability == 0.0` or `probability == 1.0`. Thus, every call to `chance()` consumes exactly one underlying float from `self._rng`.

Therefore, Stage10's engineering determinism policy requires:
- **NO Stage2 / RandomSystem compatibility reopen.**
- **NO production modifications to RandomSystem.**

Official hidden PRNG behavior remains classified as `UNKNOWN / UNOBSERVABLE` per Gameplay Authority; the one-draw invariant is strictly a **Simulator Engineering Determinism Policy**.

## 18.1 Normalized Pre-RNG Admission Gate Sequence (S10-R2-N02, S10-R3-M01)

To ensure trace and failure-reason determinism across the codebase, admission before consuming an RNG draw is partitioned strictly by `RecoveryOpportunityKind`:

```text
1. Target Validity & Alive Gate (Shared):
   - Target unit exists and target.is_alive() == True.
   - If dead or None: reject opportunity (TARGET_DEFEATED / INVALID_TARGET); NO RNG call.

2. Hit Topology & Reaction Permission Gate (Kind-Specific):
   - For FIRST_AID_AFTER_DAMAGE:
       * DamageAftermathFact.hit_topology == DamageHitTopology.RESOLVED_HIT.
       * ReactionPermissionPolicy.can_trigger_recovery(source_type) == True.
       * If not resolved hit (e.g. EVASION) or source ineligible (e.g. CHAIN_TRUE_FEEDBACK): reject; NO RNG call.
   - For RECUPERATION_ACTION_START:
       * NOT_APPLICABLE (Gate 2 is skipped entirely; RECUPERATION is an action-start opportunity with no damage event).

3. Opportunity Lifecycle Window Gate (Shared):
   - current_combat_round >= state.first_eligible_round and current_combat_round <= state.last_eligible_round.
   - If outside lifecycle window: reject; NO RNG call.

4. Source Skill Enablement Gate (Shared):
   - PersistentSourceSkillGate evaluates source skill status.
   - If mode == QUERY_SKILL_RUNTIME and SkillRuntime.enabled == False: suppress opportunity; NO RNG call. Clock continues.

5. ADMITTED -> Exactly One RNG Draw (Shared Engine Tail):
   - All pre-conditions satisfied.
   - Opportunity becomes ADMITTED.
   - Consume exactly one context.random.chance(probability) call.
   - (recoverable_gap == 0 does NOT suppress this draw; full troops proceed to draw).
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

# 22. RecoveryOpportunitySystem ownership (S10-R3-M01)

`RecoveryOpportunitySystem` is the single, unified recovery opportunity engine for both after-damage reactions (`FIRST_AID`) and turn-based action-start recovery (`RECUPERATION`). To eliminate damage-event dependencies on non-damage opportunities, the system operates on typed opportunity kinds.

### 22.1 RecoveryOpportunityKind Specification

```python
class RecoveryOpportunityKind(str, Enum):
    FIRST_AID_AFTER_DAMAGE = "FIRST_AID_AFTER_DAMAGE"
    RECUPERATION_ACTION_START = "RECUPERATION_ACTION_START"
```

Every `RecoveryOpportunity` object immutably carries `opportunity_kind: RecoveryOpportunityKind`.

### 22.2 Admission Gate Matrix (S10-R3-M01)

| Gate | FIRST_AID_AFTER_DAMAGE | RECUPERATION_ACTION_START | Failure Action |
|---|---|---|---|
| **1. Target Validity & Alive Gate** | **REQUIRED** (`target.is_alive == True`) | **REQUIRED** (`target.is_alive == True`) | Reject with `TARGET_DEFEATED` or `INVALID_TARGET`; zero RNG draws |
| **2. Hit Topology & Reaction Permission** | **REQUIRED** (`RESOLVED_HIT` + `can_trigger_recovery(source_type) == True`) | **NOT_APPLICABLE** (Skipped entirely) | If FIRST_AID fails: reject with `INELIGIBLE_HIT_OR_SOURCE`; zero RNG draws |
| **3. Opportunity Lifecycle Window Gate** | **REQUIRED** (`first_eligible <= round <= last_eligible`) | **REQUIRED** (`first_eligible <= round <= last_eligible`) | Reject with `LIFECYCLE_WINDOW_EXPIRED`; zero RNG draws |
| **4. Source Skill Enablement Gate** | **REQUIRED** (`PersistentSourceSkillGate`) | **REQUIRED** (`PersistentSourceSkillGate`) | If disabled: suppress with `SKILL_TEMPORARILY_DISABLED`; clock continues; zero RNG draws |
| **5. Simulator RNG Probability Draw** | **REQUIRED** (`context.random.chance(prob)`) | **REQUIRED** (`context.random.chance(prob)`) | If roll fails: return `OpportunityFailed(PROBABILITY_FAILED)` |
| Full Troops (`recoverable_gap == 0`) | **NOT A GATE** (proceeds to draw) | **NOT A GATE** (proceeds to draw) | Continues to nominal calculation and RecoverySystem |
| Zero Loss (`ActualTargetTroopLoss == 0`) | **NOT A REJECTION** (proceeds if resolved hit) | **NOT_APPLICABLE** | Treatment model may recover >0; ratio model nominal 0 |

### 22.3 Normalized Admission Sequence before RNG Draw

```text
1. Target Validity & Alive Gate (Shared):
   - Validate target unit exists and target.is_alive() == True.
   - If dead or None: abort opportunity with TARGET_DEFEATED / INVALID_TARGET; NO RNG draw.

2. Hit Topology & Reaction Permission Gate (Kind-Specific):
   - For FIRST_AID_AFTER_DAMAGE:
       * Validate DamageAftermathFact exists and DamageAftermathFact.hit_topology == DamageHitTopology.RESOLVED_HIT.
       * Validate ReactionPermissionPolicy.can_trigger_recovery(source_type) == True.
       * If not resolved hit (e.g. EVASION) or source ineligible (e.g. CHAIN_TRUE_FEEDBACK): abort opportunity; NO RNG draw.
   - For RECUPERATION_ACTION_START:
       * NOT_APPLICABLE: Gate 2 is skipped completely. RECUPERATION never queries ReactionPermissionPolicy and never requires DamageAftermathFact.

3. Opportunity Lifecycle Window Gate (Shared):
   - Validate current combat round is within [first_eligible_round, last_eligible_round].
   - If outside window: abort opportunity; NO RNG draw.

4. Source Skill Enablement Gate (Shared):
   - Query PersistentSourceSkillGate.
   - When mode == QUERY_SKILL_RUNTIME: query SkillRuntimeRegistry.lookup(owner_id, slot).enabled.
   - If disabled: suppress opportunity (SKILL_TEMPORARILY_DISABLED); NO RNG draw. Clock continues.

5. Simulator RNG Probability Draw (Shared Engine Tail):
   - Opportunity becomes ADMITTED.
   - Consume exactly one context.random.chance(probability) call.
   - (recoverable_gap == 0 does NOT suppress this draw; full troops proceed to draw).
   - If roll fails: return OpportunityFailed(PROBABILITY_FAILED).

6. Potency Calculation & RecoveryRequest (Shared Engine Tail):
   - Resolve frozen recovery potency from generation snapshot.
   - For damage-ratio model: read typed ActualTargetTroopLoss from aftermath snapshot.
   - Create RecoveryRequest carrying source_generation_id.
   - Call RecoverySystem.
   - Return RecoveryOpportunityResult.
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

## 24.2 Share (Reconciled per Stage9 Addendum)

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
     commit Share AttributedDirectTroopLoss to sharer
     → DefeatCleanupPort if sharer dies
     → victory/finalization death observation for sharer
     → target DamageAftermathPort (invoked at reconciled Stage9 checkpoint after partition commit)
        → local FIRST_AID opportunity/recovery if target alive
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

## 24.4 Cleave (Reconciled per Stage9 Addendum S10-R2-B01)

The existing parallel `cleave_first_aid` callback is removed in Stage10 build.

Cleave uses:

```text
Cleave derived hit topology
→ partition plan
→ Distribution participant direct losses first when applicable
→ Cleave target troop settlement
→ DefeatCleanupPort if defeated
→ target death observation
→ if target defeated:
     discard pending sharer direct loss
     no FIRST_AID
     complete Cleave
→ else:
     commit Share DirectTroopLoss to sharer (if SharePlan exists)
     → DefeatCleanupPort if sharer dies
     → victory/finalization death observation for sharer
     → shared DamageAftermathPort (checkpoint reconciled per Stage9 Addendum §4.1)
        → FIRST_AID local recovery if permitted and target alive
     → existing attacker-recovery contract (倒戈/吸血, if can_trigger_recovery)
     → existing resolved-damage callbacks / deferred Chain timing
→ complete admitted Cleave local damage
```

This preserves the Stage9 frozen execution order per `STAGE9_STAGE10_COMPATIBILITY_ADDENDUM.md`, confirming that `DamageAftermathPort` is a shared port invoked at each settlement path's respective frozen checkpoint rather than an unauthorized runtime reordering.

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

# 31. Dependency graph V3

Normative dependency direction:

```text
BattleContext
├─ UnitRuntime roster
├─ StateRegistry
├─ SkillRuntimeRegistry
├─ ActionProgressTracker
├─ RandomSystem
└─ OperationIdAllocator

ReactionPermissionPolicy (static / policy authority)

AttributeSystem
TroopSystem
StateLifecycleSystem
ExecutionRightSystem (decision owner: evaluate_rule_intent, dead/suppression checks)
SkillRuntimeRegistry/Lookup
        ↓
DefeatCleanupPort (synchronous defeat checkpoint)
        ├─ StateLifecycleSystem
        └─ ExecutionRightSystem

RecoverySystem
        └─ TroopSystem

RecoveryOpportunitySystem
        ├─ SkillRuntimeRegistry/Lookup
        ├─ PersistentSourceSkillGate
        ├─ ReactionPermissionPolicy
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
        ├─ ReactionPermissionPolicy
        └─ RecoveryOpportunitySystem

DamageInstanceCoordinator
        ├─ DamageSystem
        ├─ DamageResolutionSystem
        ├─ DamagePartitionCoordinator
        ├─ DirectTroopLossResolver
        ├─ ReactionPermissionPolicy
        ├─ DamageAftermathPort
        └─ BattleFinalizationCoordinator

CleaveDerivedDamageResolver
        ├─ TroopSystem
        ├─ DefeatCleanupPort
        ├─ DamagePartitionCoordinator
        ├─ DirectTroopLossResolver
        ├─ HitResolutionSystem
        ├─ ReactionPermissionPolicy
        ├─ DamageAftermathPort
        └─ BattleFinalizationCoordinator

ChainSystem
        ├─ TroopSystem
        ├─ DefeatCleanupPort
        ├─ ReactionPermissionPolicy
        └─ BattleFinalizationCoordinator

EffectExecutor (pure execution router)
        ├─ DamageInstanceCoordinator
        ├─ StateLifecycleSystem
        └─ RecoverySystem

RuleHookSystem (dispatch owner & batch loop controller)
        ├─ TriggerSystem
        ├─ ExecutionRightSystem (pre-dispatch decision check)
        ├─ EffectExecutor
        └─ RecoveryOpportunitySystem

BattleFinalizationCoordinator
        └─ StateLifecycleSystem.clear_all_on_battle_end (post-victory teardown)

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
| CLEAVE derived damage | YES | YES per frozen Cleave recovery permission at reconciled Stage9 checkpoint |
| ASSAULT pursuit/normal damage | YES | YES if resolved-hit + survived (Pursuit_Counterattack authorized) |
| CHAIN_TRUE_FEEDBACK | restricted classification fact | NO; Stage9 restricted feedback permission remains frozen |
| SHARE_DIRECT_LOSS | no DamageEvent aftermath | NO |
| DISTRIBUTION_DIRECT_LOSS | no DamageEvent aftermath | NO |

`ReactionPermissionPolicy.can_trigger_recovery(source_type)` is the SINGLE AUTHORITATIVE RUNTIME PERMISSION OWNER. No individual system may hardcode its own permission list.

---

# 34. Mandatory regression plan V4

No tests are written in R3-B, but the implementation build/audit must include at least:

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

BATTLE TEARDOWN (S10-R2-M05)
- battle finalization drains all admitted aftermath work
- StateLifecycleSystem.clear_all_on_battle_end executes after victory latched
- all states across all units (both winners and losers) are cleansed
- STATE_CLEARED_ON_BATTLE_END emitted; zero state leakage between battles

GENERATION PROVENANCE & DTO PROPAGATION (S10-R2-M04)
- refresh generation 3 → 4
- pending generation-3 Effect executes with generation-3 snapshot
- STATE_REFRESHED reports old/new generation
- source_generation_id propagated end-to-end through DamageRequest, DamageResult,
  RecoveryRequest, RecoveryResult, DamageAftermathFact, DamagePipelineTrace,
  and observation events (DAMAGE_RESOLVED, RECOVERY_RESOLVED)

FIRST_AID AFTERMATH
- weakness-zero → opportunity YES
- barrier-zero → opportunity YES
- evasion/miss → opportunity NO
- positive nonfatal loss → opportunity YES
- fatal loss → cleanup then opportunity NO
- zero-loss + existing missing troops + treatment model → may recover >0
- zero-loss + ratio model → opportunity exists, nominal ratio amount 0
- zero-loss + full troops → opportunity executes; successful recovery resolves actual 0
- ASSAULT pursuit/counterattack hit → opportunity YES (S10-R2-B02)
- DamageAftermathFact REQUIRED for admission (S10-R3-M01)

RECUPERATION (S10-R3-M01)
- admitted at UNIT_ACTION_START with DamageAftermathFact = None (Gate 2 NOT_APPLICABLE)
- full troops → opportunity not skipped
- source-skill inactive → opportunity suppressed without pausing finite lifecycle

RNG & ADMISSION GATES (S10-R2-N02, S10-R3-N01)
- normalized gate order: target alive -> hit topology & permission -> lifecycle window -> source skill gate -> RNG draw
- probability == 1.0 → exactly one simulator probability draw per admitted opportunity (native RandomSystem.chance)
- probability == 0.0 → exactly one simulator probability draw per admitted opportunity (native RandomSystem.chance)
- zero RNG calls if target dead or skill disabled before RNG gate
- recoverable_gap == 0 → does not suppress admitted opportunity draw
- ineligible aftermath → zero recovery probability draws
- zero Stage 2 reopen / zero RandomSystem code modification (S10-R3-N01)

DEATH & EXECUTION RIGHT (S10-R2-M02, S10-R3-B01, S10-R3-M02)
- ExecutionRightSystem.evaluate_rule_intent consumes typed RuleIntentExecutionDescriptor (zero duck-typing)
- Target Death (Timeline A/B/C/D):
  * P1 targets Unit 2 (dies in A) -> B evaluated with target dead -> REJECT_CURRENT(TARGET_DEFEATED)
  * P1 (Unit 1, still alive) targets Unit 3 in C -> ALLOW -> executes!
  * P2 targets Unit 4 in D -> ALLOW -> executes!
- Owner Death (Timeline A/B/C/D):
  * P1 owner (Unit 1) dies in A -> B evaluated with owner dead -> ABORT_OWNER_STATE_REMAINDER(OWNER_DEFEATED)
  * All remaining intents belonging to Unit 1 in the hook batch are discarded
  * P2 (Unit 2, alive) targets Unit 3 in D -> ALLOW -> executes!
- unrelated unit intents in same hook batch are NOT discarded when another unit dies
- DefeatCleanupPort invoked synchronously once on troop reduction to 0 across all death paths

STAGE8
- LIVE_RUNTIME exact golden regression unchanged
- FROZEN_APPLICATION does not read current source formula facts
- FROZEN_APPLICATION does not rediscover current ordinary modifiers
- FROZEN_APPLICATION locked modifier/crit decisions do not reroll
- base-formula tick RNG follows existing Stage8 formula path
- REBELLION locked route + ignore-defense policy consumed
- source-dead historical periodic source accepted only on authorized frozen lane
- trace never marks skipped stage EXECUTED

STAGE9 / AFTERMATH (S10-R2-B01, S10-R2-B02)
- NoPartition target aftermath before callbacks
- Share: target settlement -> sharer direct loss -> target aftermath (reconciled checkpoint)
- Distribution: participant direct loss drains before target settlement
- victory latched during admitted Distribution still allows current target local FIRST_AID aftermath
- Share/Distribution DirectTroopLoss never triggers FIRST_AID
- Cleave: target settlement -> sharer direct loss -> DamageAftermathPort(target) -> attacker recovery -> callbacks
- no `cleave_first_aid` production path remains
- Chain restricted feedback remains FIRST_AID-ineligible
- ASSAULT source type permitted for FIRST_AID aftermath recovery
```

Hardening also requires:

```text
property tests for lifecycle windows
conformance suite for all death-capable troop-loss paths
S10-R2-H01: exactly-once defeat-cleanup conformance spy across every destructive route (standard, direct loss, Cleave, Chain, Counter)
S10-R2-H02: frozen-lane instrumentation proving zero current-source formula/provider live recalculation
RNG spy/golden sequence tests
static dependency/import/constructor DAG tests
no EventBus gameplay subscribers
LIVE_RUNTIME exact golden suite
```

---

# 35. Finding Closure Matrix

`REPAIR CLAIMED` means the authoring pass supplied an explicit design answer. It does **not** mean the independent re-audit has accepted it.

### Round 1 Findings (Preserved from Draft V2)

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

### Round 2 Findings (Preserved from Draft V3)

| Audit Finding | Severity | R2-B Repair / Resolution | Status |
|---|---|---|---|
| S10-R2-B01 Stage9 Cleave vs FIRST_AID ordering conflict | BLOCKER | Formal `STAGE9_STAGE10_COMPATIBILITY_ADDENDUM.md` created; preserved Stage9 frozen ordering (`Cleave target settlement -> Share direct loss -> DamageAftermathPort(target) -> attacker recovery -> callbacks`) | `REPAIR CLAIMED` |
| S10-R2-B02 `SourceType.ASSAULT` FIRST_AID recovery permission conflict | BLOCKER | Formally authorized in Stage9 Addendum and `ReactionPermissionPolicy.can_trigger_recovery`; aligned with Authority `Pursuit_Counterattack: ELIGIBLE` | `REPAIR CLAIMED` |
| S10-R2-M01 Gameplay Authority pinned commit missing targeted research | MAJOR | Formally promoted in R2-A4 to Gameplay Authority `main` @ `a9a05ceffa2a9489cdc1e0a000a4c27bac81a5fe`; `Authority Sync = PASS` | `PROMOTED & SYNC PASS` |
| S10-R2-M02 ExecutionRight unique owner ambiguity | MAJOR | Partitioned into Decision Owner (`ExecutionRightSystem`), Dispatch Owner (`RuleHookSystem`), and Router (`EffectExecutor`); typed abort scopes (`ALLOW`, `REJECT_CURRENT`, `ABORT_OWNER_STATE_REMAINDER`, `ABORT_HOOK`); explicit Effect A/B/C timeline | `REPAIR CLAIMED` |
| S10-R2-M03 `PersistentSourceSkillGate` mapping underdefined | MAJOR | Added normative mapping table per family + source class; single definition of `EXTERNAL_LIFECYCLE` (external physical lifetime management) | `REPAIR CLAIMED` |
| S10-R2-M04 `StateApplicationGenerationId` propagation matrix absent | MAJOR | Added end-to-end propagation matrix across all DTOs/requests/results/events; explicit separation between snapshot values and JIT queries | `REPAIR CLAIMED` |
| S10-R2-M05 Battle-end persistent state cleanup underdefined | MAJOR | Added `StateLifecycleSystem.clear_all_on_battle_end(context)` teardown contract distinct from gameplay expiration | `REPAIR CLAIMED` |
| S10-R2-N01 `ActionProgressTracker` exact order in `UNIT_ACTION_START` | MINOR | Exact sequence frozen: set acting unit -> mark action start -> publish observation -> trigger/hook evaluation -> expiry | `REPAIR CLAIMED` |
| S10-R2-N02 Recovery pre-RNG admission gate sequence inconsistent | MINOR | Normalized exact sequence across §18 and §22: target alive -> hit topology & permission -> lifecycle window -> source skill gate -> RNG draw | `REPAIR CLAIMED` |
| S10-R2-N03 Regression contract omits critical invariants | MINOR | Added ASSAULT, battle teardown, generation propagation, and mixed-hook tests to §34 | `REPAIR CLAIMED` |
| S10-R2-H01 Exactly-once defeat-cleanup conformance spy | HARDENING | Added conformance spy requirement across every destructive route to §34 | `ACCEPTED FOR BUILD` |
| S10-R2-H02 Frozen-lane zero live formula read instrumentation | HARDENING | Added frozen-lane instrumentation test requirement to §34 | `ACCEPTED FOR BUILD` |

### Round 3 Findings (Repaired in Draft V4)

| Audit Finding | Severity | R3-B Repair / Resolution | Status |
|---|---|---|---|
| S10-R3-B01 Target Defeat vs Owner Defeat conflated in ExecutionRight abort scope | BLOCKER | Split into `REJECT_CURRENT(reason=TARGET_DEFEATED)` (only cancels the intent targeting dead unit; does not cancel other intents of living owner) and `ABORT_OWNER_STATE_REMAINDER(reason=OWNER_DEFEATED)` (cancels all remaining intents of dead owner, but unrelated units proceed). Formalized Decision Matrix and exact A/B/C/D timeline in §4.2, §4.3, §4.4. | `REPAIR CLAIMED` |
| S10-R3-M01 RecoveryOpportunitySystem Gate 2 incorrectly requires DamageAftermathFact for RECUPERATION | MAJOR | Introduced `RecoveryOpportunityKind` enum (`FIRST_AID_AFTER_DAMAGE` vs `RECUPERATION_ACTION_START`). In §18.1 and §22, defined Gate 2 as REQUIRED for FIRST_AID but NOT_APPLICABLE for RECUPERATION. RECUPERATION is admitted at `UNIT_ACTION_START` with `aftermath_fact=None`. | `REPAIR CLAIMED` |
| S10-R3-M02 ExecutionRightSystem.evaluate_rule_intent typed interface and descriptor underdefined | MAJOR | Defined explicit `RuleIntentExecutionDescriptor` dataclass in §4.1, carried directly by `RuleIntent`, constructed by `TriggerSystem`. Standardized signature `ExecutionRightSystem.evaluate_rule_intent(descriptor, context) -> ExecutionRightDecision`. Zero duck-typing or attribute probing. | `REPAIR CLAIMED` |
| S10-R3-N01 RandomSystem.chance native one-draw invariant ($p=0, p=1$) insufficiently documented | MINOR | Documented in §18.0 that native `sgs_v2` implementation (`self.random() < probability`) draws exactly one float for all $p \in [0.0, 1.0]$ without shortcutting. Formally confirmed NO Stage 2 reopen and zero `RandomSystem` code modification. | `REPAIR CLAIMED` |

Summary:

```text
Round 1 findings: 7 BLOCKER, 6 MAJOR, 4 MINOR, 5 HARDENING (retained repaired)
Round 2 findings: 2 BLOCKER, 5 MAJOR, 3 MINOR, 2 HARDENING (retained repaired/promoted)
Round 3 findings: 1 BLOCKER, 2 MAJOR, 1 MINOR, 0 HARDENING (all repaired)

Independent acceptance = PENDING FINAL INDEPENDENT FREEZE-GATE AUDIT
```

---

# 36. Author self-audit scenarios

R3-B author self-audit requires two independent implementers reading this Draft V4 to produce the same observable contract for:

```text
PRE_BATTLE N=1
source dies before DOT tick
target dies mid-hook (Effect A/B/C)
owner dies mid-hook (Effect A/B/C)
same-name refresh before pending effect executes
weakness-zero FIRST_AID
barrier-zero FIRST_AID
evasion FIRST_AID
ASSAULT FIRST_AID
full-troop FIRST_AID
full-troop RECUPERATION
probability=100%
probability=0%
Share
Distribution
Cleave
battle-end teardown
victory latched during current DamageInstance
```

Author conclusion:

```text
Scenario A: Target Defeat mid-batch
→ Effect A kills Target 1.
→ Effect B (also targeting Target 1 from living Owner 1) evaluates evaluate_rule_intent:
  Target 1 is dead -> returns REJECT_CURRENT(TARGET_DEFEATED). Effect B is skipped.
→ Effect C (targeting living Target 2 from Owner 1) evaluates evaluate_rule_intent:
  Owner 1 alive, Target 2 alive -> returns ALLOW. Effect C executes normally!
→ Effect D (from living Owner 2) evaluates evaluate_rule_intent:
  returns ALLOW. Effect D executes normally!

Scenario B: Owner Defeat mid-batch
→ Effect A kills Owner 1.
→ Effect B (from dead Owner 1) evaluates evaluate_rule_intent:
  Owner 1 is dead -> returns ABORT_OWNER_STATE_REMAINDER(OWNER_DEFEATED).
→ RuleHookSystem discards all remaining intents belonging to Owner 1 in this batch.
→ Effect D (from living Owner 2) evaluates evaluate_rule_intent:
  Owner 2 is alive, Target alive -> returns ALLOW. Effect D executes normally!

Scenario C: Recuperation vs First Aid Gate 2 Admission
→ RECUPERATION at UNIT_ACTION_START:
  Opportunity kind is RECUPERATION_ACTION_START. Gate 2 is NOT_APPLICABLE.
  admitted with aftermath_fact = None; evaluates lifecycle window, skill gate, then draws RNG.
→ FIRST_AID at DAMAGE_RESOLVED:
  Opportunity kind is FIRST_AID_AFTER_DAMAGE. Gate 2 is REQUIRED.
  Checks DamageAftermathFact (is_hit, non-evaded, allowed source type); rejects if absent/invalid.

PRE_BATTLE N=1
→ Round1 exactly one opportunity, then physical expiry at end of ActionStart window

source dies before DOT tick
→ state persists; frozen source basis executes; dead source live validation not required

refresh before pending effect executes
→ pending effect remains bound to old generation snapshot

weakness-zero
→ FIRST_AID YES

barrier-zero
→ FIRST_AID YES

evasion/miss
→ FIRST_AID NO

ASSAULT hit
→ FIRST_AID YES (authorized in ReactionPermissionPolicy per Authority contract)

full-troop FIRST_AID / RECUPERATION
→ opportunity not skipped; simulator probability policy still applies; successful RecoverySystem resolution may actual=0

probability=100% / probability=0%
→ exactly one simulator RNG chance draw per admitted opportunity via native RandomSystem.chance; zero Stage 2 reopen; ENGINEERING ONLY

Share
→ target settlement → if target alive: commit sharer direct loss → target DamageAftermathPort (reconciled checkpoint)

Distribution
→ participant direct losses → target settlement → cleanup → local target aftermath; admitted drain survives victory latch

Cleave
→ Cleave target settlement → if target alive: commit sharer direct loss → shared DamageAftermathPort (reconciled Stage9 checkpoint) → attacker recovery → callbacks

battle-end teardown
→ StateLifecycleSystem.clear_all_on_battle_end cleans all states across all units; emits STATE_CLEARED_ON_BATTLE_END

victory latched during current DamageInstance
→ no new global branch, but already-admitted local target aftermath drains if target survived
```

No remaining item above is intentionally delegated to “implementation decides”.

---

# 37. R3-B completion claim

```text
1. 1 Round 3 BLOCKER explicit repair (S10-R3-B01)   YES
2. 2 Round 3 MAJOR explicit repair (S10-R3-M01/M02)  YES
3. 1 Round 3 MINOR explicit repair (S10-R3-N01)      YES
4. Target vs Owner Defeat scope cleanly separated    YES
5. Normative A/B/C/D execution timelines documented YES
6. RuleIntentExecutionDescriptor strongly typed      YES
7. RecoveryOpportunityKind & Gate 2 bifurcation      YES
8. Native RandomSystem.chance one-draw confirmed     YES
9. Zero Stage 2 reopen / zero core code modified     YES
10. Stage7/8/9 compatibility addenda preserved       YES
11. Gameplay Authority sync PASS (a9a05cef)          YES
12. Production code modified by R3-B                 NO
13. Test code modified by R3-B                       NO
14. Document remains DESIGN DRAFT                    YES
```

Final authoring status:

```text
R3-B ARCHITECTURE REPAIR COMPLETE
STATUS: ARCHITECTURE DESIGN DRAFT V4
READY FOR FINAL INDEPENDENT DESIGN FREEZE-GATE AUDIT

DESIGN PASS                  = NOT CLAIMED
DESIGN FROZEN                = NO
PRODUCTION IMPLEMENTATION    = NOT AUTHORIZED
NEXT STEP                    = Final Stage10 Independent Design Freeze-Gate Audit
```

