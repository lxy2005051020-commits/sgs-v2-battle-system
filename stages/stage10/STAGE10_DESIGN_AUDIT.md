# Stage10 Independent Design Audit

## 0. Audit Metadata

- Battle repository: `lxy2005051020-commits/sgs-v2-battle-system`
- Audited branch: `stage10-persistent-state-research`
- Audited PR: `#6`
- Audited battle HEAD: `04ff2120dda77080fff9989787dcd5e28a40f192`
- Audited `stages/stage10/STAGE10.md` blob SHA: `b833f0c0a02ca8f45d9b2f560af0aad9599d041a`
- Gameplay authority repository: `lxy2005051020-commits/sgs-state-mechanics-research`
- Gameplay authority branch: `main`
- Gameplay authority HEAD: `61f2be7e87e6bfab1433657ee7f766ae0c53da9d`
- Audit date: `2026-09-14`
- Auditor role: `Independent / adversarial architecture reviewer`
- Production code modified by this audit: `NO`
- Tests modified by this audit: `NO`
- Gameplay authority modified by this audit: `NO`

This audit treats the current Stage10 design as potentially wrong until it survives adversarial review. A green Stage1-9 regression suite is not considered evidence that Stage10 architecture is correct, because Stage10 production behavior has not yet been implemented.

---

## 1. Executive Verdict

```text
BLOCKER   = 7
MAJOR     = 6
MINOR     = 4
HARDENING = 5

VERDICT = FAIL / DESIGN REPAIR REQUIRED
DESIGN FREEZE ELIGIBLE = NO
STAGE10 IMPLEMENTATION AUTHORIZED = NO
```

The current design is not uniquely implementable without changing observable behavior. Several findings are direct frozen-authority conflicts rather than stylistic disagreements:

1. Stage7 freezes an execute-all Hook atomic batch, while the gameplay authority freezes immediate death hard termination and abort of remaining state resolution.
2. Stage10 materially changes the frozen Stage8 participant-validation / pipeline-trace / formula-policy boundary, but no formal Stage8 reopen/addendum authority exists.
3. `FROZEN_APPLICATION` injects a pre-resolved `nominal_damage` after dynamic gates while leaving the producer outside Stage10, so FormulaPolicy / BaseFormula / coefficient / modifier ownership is not uniquely defined.
4. The finite lifecycle formula fails for PRE_BATTLE / round-0 applications.
5. Death cleanup is stated as an invariant but is not assigned to one concrete runtime port/checkpoint across every destructive troop-loss path.
6. `QUERY_SKILL_RUNTIME` depends on a battle-authoritative runtime lookup that the current composition does not provide.
7. Stage10 mandates RNG consumption for guaranteed recovery and implicitly for full-troop opportunities without gameplay authority proving those RNG semantics.

Repair is required before a second Design Audit.

---

## 2. Authority Review

### 2.1 Battle architecture authority read

The audit read the Stage10 design set and the frozen Stage7/8/9 authority relevant to this integration, including:

```text
stages/stage10/STAGE10.md
stages/stage10/STAGE10_RESEARCH_MATRIX.md
stages/stage10/STAGE10_RUNTIME_MAPPING.md
stages/stage10/STAGE10_OPEN_QUESTIONS.md
stages/stage10/README.md

stages/stage7/STAGE7.md
stages/stage7/STAGE7_FINAL_AUDIT.md

stages/stage8/STAGE8.md
stages/stage8/STAGE8_DESIGN_FREEZE.md
stages/stage8/STAGE8_FREEZE_RECORD.md

stages/stage9/STAGE9.md
stages/stage9/hardening/STAGE9_TYPED_RUNTIME_CONTRACTS.md
stages/stage9/hardening/STAGE9_RUNTIME_INVARIANTS.md
stages/stage9/hardening/STAGE9_REGRESSION_CONTRACTS.md
```

The runtime implementation was checked against the design, including the Damage pipeline, State lifecycle/registry, Trigger/Hook/Effect path, Recovery path, Stage9 partition/finalization path, Cleave/Chain/Counter, SkillRuntime, BattleSystems composition root, Engine, operation identity, and event contracts.

### 2.2 Gameplay authority read

The current gameplay-authority `main` at `61f2be7e87e6bfab1433657ee7f766ae0c53da9d` was used, not a prompt-pinned historical assumption.

The audit read the family baselines and all eight Stage10 mechanism contracts:

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

Relevant frozen gameplay rules include:

```text
continuous damage:
- TARGET_ACTION_START
- at most one opportunity per owner per combat round
- N combat rounds => at most N eligible opportunities
- application/refresh potency context is locked
- source weakness / target evasion / target barrier are trigger-time gates
- source death does not cancel an existing DOT
- same-name reapplication refreshes/overwrites the one effective instance

all target-owned persistent states:
TARGET_DEATH
→ CLEAR_ALL_STATES
→ ABORT_REMAINING_STATE_RESOLUTION
→ ABORT_REMAINING_ACTION
→ REJECT_FUTURE_STATE_APPLICATION

FIRST_AID:
- per eligible damage event
- ActualTargetTroopLoss is the dynamic triggering-damage fact for ratio models
- fatal damage cannot resurrect
- no combat-round cap

RECUPERATION / source-skill deactivation:
- inactive runtime opportunity is suppressed
- no probability check while inactive
- duration clock continues
- missed opportunity is lost without catch-up
```

When Stage10 wording conflicts with this gameplay authority, gameplay authority wins.

---

## 3. Frozen Boundary Review

### Stage7

Stage7 freezes the following Hook atomic-batch rule:

```text
one RuleHook
→ collect one ordered Effect tuple
→ execute every Effect in tuple order
→ only after the batch completes does the Engine perform victory observation

Even if an earlier Effect kills a commander,
RuleHookSystem does not interrupt the remaining Effect tuple.
```

The current `RuleHookSystem` implements exactly that pre-collection / execute-all behavior. Stage10's death-hard-termination requirement therefore cannot be implemented merely by adding another invariant. It changes a frozen Stage7 observable contract and requires a formal, narrow compatibility reopen/addendum.

### Stage8

Stage8 freezes:

```text
DamageSystem.calculate()
= unique theoretical-damage entry

DamageRequest
→ participant validation
→ rule collection
→ Prevention
→ Hit
→ FormulaPolicy
→ frozen BaseFormula
→ coefficient
→ Modifier
→ finalization
→ DamageResult + DamagePipelineTrace
```

Stage10 changes participant validation for historical dead sources, introduces a second calculation basis, changes how FormulaPolicy/BaseFormula/modifier information is represented, and requires new trace semantics. These are material Stage8 contracts named by the Stage8 reopen rule. A Stage10-local declaration that the reopen is “limited” does not itself create Stage8 authority.

### Stage9

Stage9's typed damage-fact split remains sound and must remain unchanged:

```text
Dtotal                  = DamageResult.final_damage
Dtarget                 = DamageSettlementRequest.assigned_target_damage
ActualTargetTroopLoss   = committed target troop reduction
```

Stage10 correctly selects `ActualTargetTroopLoss` for FIRST_AID damage-ratio models and correctly avoids reclassifying Share/Distribution direct troop loss as a normal damage event. The current `DamageInstanceCoordinator` already has a target-settlement callback seam whose standard-path timing can support the intended FIRST_AID checkpoint.

However, death cleanup and Cleave integration are not yet uniquely mapped to one shared port, and this blocks an unambiguous Stage10 implementation.

---

## 4. P0 Blocker Review

### S10-B01 — Death hard termination versus Stage7 atomic Hook batch

**Result: BLOCKED.**

The gameplay authority requires immediate abort of remaining owner-state resolution after target death. Stage7 freezes the opposite behavior for an already-collected Hook batch. Stage10 does not formally reopen Stage7 or update `HookResolutionResult`, whose frozen contract assumes one execution result per collected Effect.

A legal Stage10 implementation cannot simultaneously satisfy both authorities without an explicit compatibility repair.

### S10-B02 — Stage8 limited compatibility reopen

**Result: BLOCKED.**

A real Stage8 reopen is required. The minimum reopen touches:

```text
participant validation
DamageRequest basis contract
frozen theoretical-input representation
FormulaPolicy/BaseFormula/modifier stage semantics
DamagePipelineTrace semantics
REBELLION defense-policy ingress
```

A dedicated Stage8 compatibility addendum/reopen authority is required before Stage10 Design Freeze.

### S10-B03 — `FROZEN_APPLICATION` theoretical damage ownership

**Result: BLOCKED.**

Current Stage10 semantics are:

```text
application/refresh producer somewhere outside Stage10
→ supplies FrozenContinuousDamageBasis.nominal_damage

tick:
Prevention(dynamic subset)
→ Hit(dynamic subset)
→ final_damage = nominal_damage
```

This is not merely “reusing the Stage8 pipeline.” It is value injection after live Prevention/Hit while FormulaPolicy/BaseFormula/coefficient/Modifier are not executed at tick time.

The design does not uniquely specify who produced `nominal_damage`, using which Stage8 stages, which RNG, which defense policy, and which modifier ordering. `defense_policy` and locked modifier/crit fields also remain stored beside a value said to have already resolved them, creating a double-apply versus dead-field ambiguity.

REBELLION makes the defect concrete: `IGNORE_RELEVANT_TARGET_DEFENSE` matters at formula evaluation time. If `nominal_damage` is already final before the tick, the policy must have been consumed earlier by an explicitly named authority. Merely storing it in the basis does not cause it to affect damage.

### S10-B04 — PRE_BATTLE finite lifecycle off-by-one

**Result: BLOCKED.**

The current derivation says for application at combat round `R`:

```text
owner has not started action in R
→ first_eligible_round = R
last_eligible_round = first + N - 1
```

At PRE_BATTLE, `context.current_round == 0`.

Literal results:

| Duration | Derived first | Derived last | First real action-start | Observable opportunities |
|---:|---:|---:|---:|---|
| N=1 | 0 | 0 | R1 | none; expires at R1 before trigger |
| N=2 | 0 | 1 | R1 | R1 only |
| N=3 | 0 | 2 | R1 | R1, R2 only |

This is an off-by-one failure for command/passive/troop states applied before combat-round 1.

### S10-B05 — Death cleanup has no unique runtime checkpoint

**Result: BLOCKED.**

Current destructive paths include:

```text
standard target settlement
Share direct troop loss
Distribution direct troop loss
Cleave derived settlement/direct loss
Chain true feedback
Counter through standard DamageInstance
```

Current runtime paths can publish `UNIT_DEFEATED` without synchronously clearing states. `StateLifecycleSystem` does not yet expose a canonical defeat-cleanup seam, and its state-application path does not by itself reject every dead-owner application.

Stage10 states “one authoritative death-cleanup integration point” but does not freeze its type, owner, call sites, or ordering relative to `UNIT_DEFEATED`, FIRST_AID, resolved callbacks, and finalization.

### S10-B06 — Missing battle-authoritative SkillRuntime lookup

**Result: BLOCKED.**

`SkillRuntime.enabled` exists, but the current `BattleContext` / `BattleSystems` composition has no battle-authoritative:

```text
(owner_id, skill_slot) -> SkillRuntime
```

registry/lookup.

Stage10 itself says this absence is an implementation blocker. The source-skill deactivation gameplay authority is already frozen, so this cannot be postponed as a mere implementation convenience.

### S10-B07 — Recovery RNG semantics exceed authority

**Result: BLOCKED.**

Stage10 mandates:

```text
context.random.chance(probability) exactly once
```

for every active opportunity and explicitly includes `probability == 1.0`. Current `RandomSystem.chance(1.0)` consumes one RNG value.

The RECUPERATION authority freezes probability behavior, inactivity suppression, recovery cap, and healing prevention, but the reviewed authority does not uniquely establish whether:

```text
guaranteed probability 1.0 consumes a PRNG draw
full-troop target with zero recoverable gap still consumes the probability draw
```

Those choices alter the subsequent deterministic RNG sequence and therefore observable replay behavior. They require gameplay-authority closure rather than an engineering guess.

---

## 5. P1 Design Item Review

### S10-M01 — Same-name refresh identity / provenance

One effective instance is frozen gameplay. Retaining one physical `instance_id` is only an engineering choice.

If the ID is retained while source, source skill, potency, and application context are replaced, the ID becomes a slot identity rather than a unique application identity. An immutable Effect created immediately before a refresh can legitimately carry the old snapshot while its `source_state_instance_id` now resolves in the registry to new provenance.

Stage10 needs a separate immutable application generation / application identity if physical slot identity is retained.

### S10-M02 — Trace representation

Stage10 explicitly leaves two implementations open:

```text
A. add REUSED_FROZEN_INPUT to StageEvaluationStatus
B. keep the enum and add new frozen-stage trace fields
```

`DamagePipelineTrace` is an observable typed result. Two implementers can therefore produce different trace contracts while both claiming compliance. Freeze must choose one representation.

### S10-M03 — Stage7 synthetic periodic path migration

The current production `TriggerSystem` still understands:

```text
PeriodicDamageStateParams
PeriodicRecoveryStateParams
```

while the eight official Stage10 states still use `EmptyStateRuntimeParams` in the current catalog mapping.

Stage10 says the official params “replace” the synthetic representation but does not say whether the Stage7 params become test-only, compatibility-only, or remain a second production route. The migration boundary must be explicit.

### S10-M04 — RecoveryOpportunity result hierarchy is not fully closed

The current `Effect` / `EffectExecutionResult` / `HookResolutionResult` hierarchy does not contain a recovery-opportunity variant. Stage10 defines conceptual types and statuses but does not fully freeze:

```text
Effect union membership
EffectExecutor dispatch result type
RuleHookSystem result carrier
aborted/skipped-tail representation after death
AFTER_DAMAGE direct-service result carrier
```

The type boundary must be closed before implementation.

### S10-M05 — `EXTERNAL_LIFECYCLE` has two possible meanings

It is not uniquely stated whether `EXTERNAL_LIFECYCLE` means:

```text
external owner physically removes/updates the state
```

or:

```text
every recovery opportunity dynamically queries an external active flag
```

For command-aura RECUPERATION, the gameplay contract already points to an external aura lifecycle owner. Stage10 should freeze `EXTERNAL_LIFECYCLE` as a lifecycle/removal ownership rule, not a second hidden active-gate query.

### S10-M06 — Shared standard/Cleave AfterDamage port is underspecified

The standard coordinator has a target-settled callback seam. Cleave currently has a separate optional `cleave_first_aid` callback, and its current Share ordering invokes the callback after Share direct loss.

Stage10 wants:

```text
target settlement
→ FIRST_AID
→ Share direct troop loss
```

for both standard and Cleave paths. A concrete shared `DamageAftermathPort`/service contract and constructor wiring must be frozen so Cleave cannot retain a parallel semantic engine.

---

## 6. Stage8 Limited Reopen Audit

### 6.1 Exact stage matrix required

The existing live path is unambiguous:

| Stage | LIVE_RUNTIME |
|---|---|
| participant validation | live source + live target |
| rule collection | live |
| Prevention | executed |
| Hit | executed |
| FormulaPolicy | executed |
| BaseFormula | executed, including formula RNG |
| coefficient | executed |
| Modifier | executed |
| final integer | executed |

The proposed frozen lane currently implies:

| Stage | FROZEN_APPLICATION draft |
|---|---|
| participant validation | historical source identity + live target |
| rule collection | dynamic gate subset only |
| Prevention | executed dynamically |
| Hit | executed dynamically |
| FormulaPolicy | not executed at tick; supposed to be represented by frozen input |
| BaseFormula | not executed at tick |
| coefficient | not executed at tick |
| Modifier | not executed at tick |
| final integer | `basis.nominal_damage` |

What is missing is the authoritative **application-time** producer table showing exactly which of FormulaPolicy/BaseFormula/coefficient/Modifier/Crit were executed or snapshotted, and where their RNG was consumed.

### 6.2 Modifier double-apply / omission risk

`nominal_damage` is defined as already including application-locked potency context, while the basis also stores `locked_modifier_context` and `locked_crit_context`. Without a producer contract:

```text
implementation A may pre-apply modifiers into nominal_damage
implementation B may apply the stored contexts later
implementation C may accidentally do both
```

All three can be made to fit the current prose.

### 6.3 Trace truthfulness

Current `StageEvaluationStatus` has only:

```text
EXECUTED
NOT_EVALUATED
```

and its validator couples `EXECUTED` to a typed result. A frozen reuse is semantically neither a fresh execution nor simply “not evaluated” if the trace is meant to explain how the final value was obtained. The Stage8 addendum must freeze the representation.

### 6.4 LIVE_RUNTIME compatibility

The design correctly requires exact backward equivalence in:

```text
RNG consumption
exceptions
DamageResult
DamagePipelineTrace
settlement events
operation identity
```

This should become a golden regression gate against the pre-reopen baseline. It is not itself a blocker once the reopen is formally authorized.

---

## 7. Lifecycle / Refresh Audit

### 7.1 Finite duration timelines

For a state applied in round 3 before the owner reaches action start:

| N | Eligible opportunities | Expiry check removes before |
|---:|---|---|
| 1 | R3 | R4 trigger |
| 2 | R3, R4 | R5 trigger |
| 3 | R3, R4, R5 | R6 trigger |

For application after the owner already reached action start in round 3:

| N | Eligible opportunities | Expiry check removes before |
|---:|---|---|
| 1 | R4 | R5 trigger |
| 2 | R4, R5 | R6 trigger |
| 3 | R4, R5, R6 | R7 trigger |

Those ordinary-round cases are consistent with the gameplay authority.

### 7.2 Required edge behavior

```text
refresh before owner action
→ recompute first eligibility at current round

refresh after owner action
→ first eligibility becomes next round

stun
→ BattleEngine still reaches UNIT_ACTION_START hook before ActionSystem blocks action
→ persistent opportunity remains eligible

second UnitActionStart in same combat round
→ action_start_count > 1
→ no second persistent opportunity

purify
→ physical removal is immediate
→ no later opportunity

owner death
→ physical state removal must be immediate
→ must not wait for next owner action-start expiry

battle finalization before natural expiry
→ no new gameplay work may be created
```

### 7.3 Logical expiry versus physical presence

The draft intentionally allows a finite state to remain physically present until the next owner action-start cleanup. This is safe only if **every** external state observer, refresh candidate selector, cleanse selector, and predicate check uses logical eligibility rather than raw registry presence.

Current `StateRegistry.has/find/states_of` are physical-presence queries. Stage10 does not define a universal logical-active filter. This creates a future compatibility risk: an already logically expired state can remain externally observable and can be refreshed or tested by another mechanism before the next owner action start.

This issue is currently covered by the mandatory repair of lifecycle ownership and should be explicitly resolved in the repaired design. A round-boundary removal is not automatically required, but “physically present but globally ineligible” needs one authoritative query model.

### 7.4 Refresh identity

Gameplay authority freezes one effective current instance and full overwrite of effective provenance/context. It does **not** require retained physical ID. If the physical ID is retained, add a separate application-generation identity to preserve historical attribution and immutable-effect provenance.

---

## 8. Recovery / RNG Audit

Frozen responsibility split should remain:

```text
TriggerSystem
= collect opportunity intent only

RecoveryOpportunitySystem
= active gate + probability + nominal opportunity amount

RecoverySystem
= target/recovery permission, including healing prevention

TroopSystem
= troop mutation + missing-troop cap
```

The layering is sound and acyclic.

The unresolved point is RNG admission. The repaired design must provide an authority-backed matrix for:

| Case | RNG draw? |
|---|---|
| source skill inactive | NO, frozen authority |
| prevented/fatal FIRST_AID damage | NO, frozen authority |
| probability in `(0,1)` and eligible | YES |
| probability exactly `1.0` | authority required |
| target already at full troops | authority required |
| healing ban present | current authority supports resolution-stage prevention, therefore chance may occur first |

No implementation should infer PRNG consumption from a numerical shortcut such as “1.0 always succeeds anyway.” Replay sequence is observable behavior.

---

## 9. AFTER_DAMAGE / FIRST_AID Audit

### 9.1 Damage-fact basis

The draft correctly uses:

```text
FIRST_AID ratio basis = ActualTargetTroopLoss
```

and rejects `Dtotal` or `Dtarget` as substitutes.

### 9.2 Standard checkpoint

The intended standard checkpoint is compatible with the current Stage9 coordinator:

```text
calculate Dtotal
→ partition plan
→ direct participant losses as required by partition kind
→ target settlement (Dtarget -> ActualTargetTroopLoss)
→ synchronous target AFTER_DAMAGE / FIRST_AID
→ remaining local partition step if Share
→ resolved-damage callbacks
→ DamageInstance complete
→ finalization may close after admitted work drains
```

### 9.3 Share

Required:

```text
target settlement
→ target FIRST_AID
→ Share direct troop loss
```

Share direct loss is not itself a standard damage event and does not trigger FIRST_AID.

### 9.4 Distribution

Required:

```text
participant direct losses
→ possible victory latch
→ target settlement
→ nonfatal target FIRST_AID may complete as local admitted work
```

This is compatible with Stage9's “victory latch, then drain current admitted DamageInstance” model.

### 9.5 Fatal damage

Fatal target settlement must result in:

```text
state cleanup
→ no FIRST_AID lookup/opportunity
→ no RNG
→ no resurrection
```

The exact cleanup checkpoint must therefore be fixed by the death-cleanup repair. Merely checking `target_defeated` after settlement avoids resurrection but does not satisfy the global immediate state-clear contract.

### 9.6 Cleave

Cleave must use the same aftermath service. The current legacy seam is not sufficient because its present Share ordering is later than the Stage10 checkpoint. The repaired design must move Cleave's shared aftermath call to the same semantic point as standard target settlement.

### 9.7 Multi-hit

The gameplay authority says each hit gets an independent opportunity. The architecture is correct only when the source skill/runtime represents each hit as a distinct eligible `DamageInstance`. Stage10 must not assume that prose alone makes all future multi-hit producers comply; this belongs in source-skill integration regressions.

---

## 10. Death Cleanup Audit

A single architecture owner is mandatory.

Recommended minimum repair contract:

```text
StateLifecycleSystem.clear_for_defeat(context, owner_id, defeat_context)
```

or an equivalent typed port owned by the state-lifecycle subsystem.

Every destructive owner must call the same port on a real alive->dead edge:

```text
DamageResolutionSystem target settlement
DirectTroopLossResolver (Share / Distribution)
Cleave target settlement
Cleave direct-loss substeps
Chain true feedback
Counter via standard DamageInstance
any future destructive troop-loss owner
```

The repaired contract must freeze the order among:

```text
TroopSystem mutation
state cleanup
STATE_REMOVED/defeat-removal facts
UNIT_DEFEATED fact
AfterDamage/FIRST_AID
victory latch observation
resolved callbacks
```

It must also freeze deterministic ordering of multiple removed states and reject state application to a dead target before registry mutation/event publication.

Already-generated but not yet executed owner-state effects must not survive owner death. This is the same conflict captured by S10-A-B01.

---

## 11. Dependency / Composition Audit

### 11.1 Constructor dependency graph that can remain acyclic

Acyclic construction is possible with explicit ports:

```text
TroopSystem
  ↑
RecoverySystem
  ↑
RecoveryOpportunitySystem ← SkillRuntimeLookup

TriggerSystem
  ↑
AfterDamageHookSystem → RecoveryOpportunitySystem

DamageSystem
  ↓
DamageResolutionSystem
  ↓
DamageInstanceCoordinator → DamageAftermathPort(AfterDamageHookSystem)

CleaveDerivedDamageResolver → same DamageAftermathPort

EffectExecutor
  → DamageInstanceCoordinator
  → StateLifecycleSystem
  → RecoveryOpportunitySystem
  → RecoverySystem

RuleHookSystem
  → one TriggerSystem instance
  → EffectExecutor
```

No `AfterDamageHookSystem -> EffectExecutor` edge is required. No `RecoveryOpportunitySystem -> DamageInstanceCoordinator` edge is required.

### 11.2 Runtime callback dependencies

```text
DamageInstanceCoordinator
→ target-settlement callback
→ AfterDamageHookSystem
→ TriggerSystem AFTER_DAMAGE collection
→ RecoveryOpportunitySystem
→ RecoverySystem
```

This callback must be constrained to recovery opportunities only; it cannot create damage/state-mutation effects.

### 11.3 Type-import dependencies

Use stage-neutral protocols/typed facts for:

```text
DamageAftermathPort
SkillRuntimeLookup
RecoveryOpportunityResult
```

so the composition root does not need circular concrete imports.

### 11.4 Composition blockers

The graph itself is feasible. The current design is blocked because two required nodes are not fully defined:

```text
battle-authoritative SkillRuntimeLookup
shared DamageAftermathPort used by standard + Cleave
```

A service locator, global mutable registry, deferred `None` binding, or lambda capturing an unconstructed service is not required and should not be introduced as a workaround.

---

## 12. Evidence Gate Audit

The Stage10 draft correctly keeps the following official integrations deferred unless separately frozen:

```text
EVASION
BARRIER
CRITICAL
STRATEGY_CRITICAL
DAMAGE_REDUCTION_PIERCE
universal positive dispel
```

Synthetic providers may test the architecture but must not create official production bindings.

The eight target states have gameplay authority sufficient for their Stage10 topology, subject to the blockers above.

`REBELLION` has frozen authority for application-time route selection and ignoring relevant target defense. The defect is not missing gameplay evidence; it is the current architectural failure to state where that defense policy is actually consumed when `nominal_damage` is produced.

---

## 13. Findings

### BLOCKER

#### S10-A-B01
- **Severity:** BLOCKER
- **Location:** Stage7 Hook atomic-batch contract; `rule_hook_system.py`; Stage10 death invariants
- **Problem:** Stage7 requires executing the full pre-collected Effect tuple even after an earlier Effect kills the owner, while gameplay authority requires immediate abort of remaining state resolution.
- **Why it matters:** Both cannot be true in the same observable combat.
- **Observable failure scenario:** Two persistent effects are collected at one owner action start. The first DOT kills the owner; the second DOT/recovery still executes under the frozen Stage7 contract.
- **Required repair:** Formal Stage7 compatibility reopen/addendum; freeze post-effect owner-death abort semantics and revise `HookResolutionResult` so an aborted tail is representable.
- **Gameplay research required:** NO.

#### S10-A-B02
- **Severity:** BLOCKER
- **Location:** Stage8 freeze records; Stage10 sections 5-8
- **Problem:** Stage10 materially changes frozen Stage8 contracts without a formal Stage8 reopen authority.
- **Why it matters:** A later-stage document cannot silently override a frozen earlier-stage architecture.
- **Observable failure scenario:** One implementer changes trace enum and participant validation in Stage8; another treats Stage8 as immutable and wraps around it. Both claim Stage10 compliance.
- **Required repair:** Create and approve a narrow Stage8 compatibility addendum defining the exact reopened contracts and unchanged contracts.
- **Gameplay research required:** NO.

#### S10-A-B03
- **Severity:** BLOCKER
- **Location:** `FrozenContinuousDamageBasis`, `FROZEN_APPLICATION`, `damage_system.py`, Stage8 pipeline
- **Problem:** The producer and mathematical stage ownership of `nominal_damage` are not uniquely defined; stored defense/modifier/crit contexts may be already consumed, consumed later, or accidentally consumed twice.
- **Why it matters:** Two implementations can produce different damage, RNG consumption, and trace while both conform to the prose.
- **Observable failure scenario:** REBELLION basis stores `IGNORE_RELEVANT_TARGET_DEFENSE`, but the precomputed nominal value was produced without passing that policy through the base formula. The tick later returns nominal unchanged, so REBELLION incorrectly uses defense.
- **Required repair:** Freeze one application-time theoretical-damage producer and an exact per-stage EXECUTE/REUSE/NOT-APPLICABLE table; ensure REBELLION policy is consumed there; remove redundant/dead basis fields or prove their role.
- **Gameplay research required:** NO for architecture; source-specific exact formulas remain separately evidence-gated.

#### S10-A-B04
- **Severity:** BLOCKER
- **Location:** Stage10 lifecycle derivation sections 11-13
- **Problem:** PRE_BATTLE `R=0` produces an invalid first/last window.
- **Why it matters:** N-round prebattle states lose one or all legal opportunities.
- **Observable failure scenario:** 1-round state applied at PRE_BATTLE derives last=0 and expires at the first R1 action start without triggering.
- **Required repair:** Define PRE_BATTLE/application-round domain explicitly; prebattle application must map to the first legal combat round, with N=1/2/3 regressions.
- **Gameplay research required:** NO.

#### S10-A-B05
- **Severity:** BLOCKER
- **Location:** `state_lifecycle_system.py`, `damage_resolution_system.py`, `direct_troop_loss_system.py`, `cleave_derived_damage_system.py`, `chain_system.py`
- **Problem:** No single typed defeat-cleanup owner/checkpoint is frozen across all destructive paths.
- **Why it matters:** Dead units can retain observable states or permit already-collected state work to execute.
- **Observable failure scenario:** Distribution direct loss kills a participant; `UNIT_DEFEATED` is published but attached states remain in the registry until unrelated later lifecycle work.
- **Required repair:** Freeze one StateLifecycle defeat-cleanup port, exact call sites, and ordering relative to death event / aftermath / finalization; reject future state applications to dead targets.
- **Gameplay research required:** NO.

#### S10-A-B06
- **Severity:** BLOCKER
- **Location:** Stage10 `PersistentSourceSkillGate`; `skill_runtime.py`; `context.py`; `battle_systems.py`
- **Problem:** `QUERY_SKILL_RUNTIME` depends on a battle-authoritative `(owner, slot) -> SkillRuntime` lookup that does not exist in the current composition.
- **Why it matters:** Official inactive-state suppression cannot be implemented without either duplicating truth or inventing a service locator.
- **Observable failure scenario:** FIRST_AID sourced from a temporarily disabled command skill has no authoritative runtime object to query, so one implementation still rolls RNG and another suppresses it.
- **Required repair:** Freeze and compose one typed battle-local SkillRuntime registry/lookup owner; define key uniqueness, missing-key failure, source-death behavior, and skill-id cross-check.
- **Gameplay research required:** NO.

#### S10-A-B07
- **Severity:** BLOCKER
- **Location:** Stage10 `RecoveryOpportunitySystem` / RECUPERATION flow; `random_system.py`
- **Problem:** Stage10 mandates PRNG consumption for `probability=1.0` and does not provide an authority-backed full-troop RNG rule.
- **Why it matters:** RNG consumption changes all later seeded outcomes.
- **Observable failure scenario:** A full-troop unit receives guaranteed RECUPERATION. One implementation consumes one random draw before the zero cap; another skips the meaningless roll. Later random damage differs.
- **Required repair:** Research/freeze the guaranteed and full-troop PRNG-consumption rules; encode the result in the opportunity contract.
- **Gameplay research required:** YES.

### MAJOR

#### S10-A-M01
- **Severity:** MAJOR
- **Location:** same-name refresh / source-state provenance
- **Problem:** retained physical `instance_id` spans multiple application generations.
- **Why it matters:** historical Effect provenance can become ambiguous after refresh.
- **Observable failure scenario:** an immutable old Effect and the refreshed registry state share one ID but refer to different source/potency data.
- **Required repair:** add immutable application generation/application ID, or separate physical-slot ID from semantic application ID; effects must carry copied immutable params, not JIT-read refreshed params.
- **Gameplay research required:** NO.

#### S10-A-M02
- **Severity:** MAJOR
- **Location:** Stage10 trace section; `damage_pipeline_trace.py`
- **Problem:** trace representation is explicitly left to implementation choice.
- **Why it matters:** trace is an observable typed contract and the two proposed forms are not identical.
- **Observable failure scenario:** one implementation adds `REUSED_FROZEN_INPUT`; another emits `NOT_EVALUATED` plus side fields.
- **Required repair:** choose one representation in the Stage8 addendum.
- **Gameplay research required:** NO.

#### S10-A-M03
- **Severity:** MAJOR
- **Location:** `stage7_state_params.py`, `trigger_system.py`, official state catalog
- **Problem:** old synthetic periodic params can coexist with new official Stage10 params without a frozen migration boundary.
- **Why it matters:** duplicate production paths and inconsistent behavior are possible.
- **Observable failure scenario:** a definition tagged for action-start still uses `PeriodicDamageStateParams` and enters the live Stage8 damage path while official DOT uses the frozen path.
- **Required repair:** mark legacy params test-only/compat-only or remove their production binding; official eight states must have exactly one Stage10 path.
- **Gameplay research required:** NO.

#### S10-A-M04
- **Severity:** MAJOR
- **Location:** Effect / EffectExecutor / HookResolutionResult contracts
- **Problem:** recovery-opportunity type/result integration is not completely specified.
- **Why it matters:** two implementations can extend the effect/result hierarchy differently and disagree on Hook result cardinality after death-abort.
- **Observable failure scenario:** RECUPERATION returns a nested RecoveryOpportunityResult in one implementation and a generic recovery execution result in another.
- **Required repair:** freeze Effect union membership, executor result type, Hook result representation, and direct AFTER_DAMAGE result shape.
- **Gameplay research required:** NO.

#### S10-A-M05
- **Severity:** MAJOR
- **Location:** `PersistentSourceSkillGate.EXTERNAL_LIFECYCLE`
- **Problem:** the enum value can mean external physical removal or per-opportunity dynamic querying.
- **Why it matters:** command-aura source-death behavior can differ across implementations.
- **Observable failure scenario:** one implementation removes RECUPERATION when the aura owner dies; another leaves the state and merely asks an active flag every action start.
- **Required repair:** freeze `EXTERNAL_LIFECYCLE` as external lifecycle/removal ownership, or split it into distinct typed concepts.
- **Gameplay research required:** NO.

#### S10-A-M06
- **Severity:** MAJOR
- **Location:** standard DamageInstance aftermath and `CleaveDerivedDamageResolver`
- **Problem:** the design says “same service” but does not freeze one concrete shared port/adaptor; current Cleave Share order is different.
- **Why it matters:** FIRST_AID timing can diverge between standard and Cleave damage.
- **Observable failure scenario:** standard Share triggers FIRST_AID before sharer loss, while Cleave invokes its legacy callback after sharer loss.
- **Required repair:** freeze one shared `DamageAftermathPort` and require both standard and Cleave to call it immediately after target settlement at the same semantic checkpoint.
- **Gameplay research required:** NO.

### MINOR

#### S10-A-N01
- **Severity:** MINOR
- **Problem:** “historical source identity exists” is not typed precisely.
- **Required repair:** define it as an existing battle roster identity (`source_id in context.units`) without alive/execution-right requirements, or freeze another explicit definition.
- **Gameplay research required:** NO.

#### S10-A-N02
- **Severity:** MINOR
- **Problem:** defeat cleanup event semantics are not frozen.
- **Required repair:** define whether cleanup emits `STATE_REMOVED` with an `OWNER_DEFEATED` reason, never mislabels defeat cleanup as natural `STATE_EXPIRED`, and define deterministic order.
- **Gameplay research required:** NO.

#### S10-A-N03
- **Severity:** MINOR
- **Problem:** nested numeric validation ownership for probability/snapshot contexts is not fully enumerated.
- **Required repair:** constructor-level finite/domain validation for probability, nominal amounts, ExactRatio, modifier/crit snapshot values; reject bool/NaN/inf before RNG or side effects.
- **Gameplay research required:** NO.

#### S10-A-N04
- **Severity:** MINOR
- **Problem:** `STATE_REFRESHED` payload is specified only as “at least” a loose set of fields.
- **Required repair:** freeze a stable minimum audit schema, including old/new semantic application identity if S10-A-M01 is repaired that way.
- **Gameplay research required:** NO.

### HARDENING

#### S10-A-H01
Property-test lifecycle windows across PRE_BATTLE, before/after owner action, N=1/2/3, refresh, stun, second action start, purify, and owner death.

#### S10-A-H02
Create a death-path conformance suite covering standard settlement, Share, Distribution, Cleave, Chain, and Counter; assert no attached state remains executable after a death edge.

#### S10-A-H03
Use an RNG spy/golden sequence for inactive gate, p=1, full troops, healing ban, prevented damage, zero loss, and fatal damage.

#### S10-A-H04
Add static dependency/composition tests enforcing forbidden edges, one TriggerSystem singleton, one RecoverySystem, and no EventBus gameplay subscription.

#### S10-A-H05
Pin LIVE_RUNTIME golden regressions against the pre-Stage8-reopen baseline for DamageResult, PipelineTrace, RNG consumption, exceptions, and settlement events.

---

## 14. Mandatory Repair Set

The next design revision must complete all of the following before re-audit:

1. **Formal Stage7 compatibility reopen/addendum** for death-abort of persistent Hook batches, including `HookResolutionResult` tail semantics.
2. **Formal Stage8 compatibility addendum/reopen** with an exact stage matrix for `FROZEN_APPLICATION`, participant validation, trace, and REBELLION formula-policy consumption.
3. **Freeze the one application-time theoretical-damage producer** for `FrozenContinuousDamageBasis`; remove all ambiguity around FormulaPolicy/BaseFormula/coefficient/Modifier/Crit and RNG ownership.
4. **Repair lifecycle round-domain semantics**, especially PRE_BATTLE / round 0, and explicitly define logical-active versus physical-presence behavior after nominal expiry.
5. **Freeze one defeat-cleanup port and ordering** across every destructive troop-loss path, including state-application rejection to dead owners.
6. **Add one battle-authoritative SkillRuntime lookup owner** and its composition contract.
7. **Research and freeze recovery RNG admission** for `probability=1.0` and full-troop opportunities.
8. **Separate physical slot identity from application provenance** if same-name refresh continues to retain `instance_id`.
9. **Close the RecoveryOpportunity Effect/result type hierarchy** and shared standard/Cleave aftermath port.
10. **Close legacy Stage7 synthetic periodic migration** so exactly one production path exists for each official Stage10 state.
11. **Define `EXTERNAL_LIFECYCLE` uniquely** and keep external aura ownership external.
12. **Keep Evidence Gate DEFER items deferred**; do not activate Evasion/Barrier/Crit/StrategyCrit/ReductionPierce/positive dispel merely to satisfy Stage10 plumbing.

No production implementation should start before a repaired `STAGE10.md` receives a new independent design audit with `BLOCKER=0` and `MAJOR=0`.

---

## 15. Validation Results

### 15.1 Repository / CI validation

The audited branch head is:

```text
04ff2120dda77080fff9989787dcd5e28a40f192
```

Current PR #6 workflow associated with that head:

```text
workflow name = tests
run number    = 339
run id        = 34862678620
job id        = 104038634071
conclusion    = success
Python        = 3.11.16
```

Workflow log result:

```text
pytest -q
753 passed in 2.82s

python demo.py > /dev/null
success
```

Important provenance detail: the PR workflow checked out GitHub's PR merge ref:

```text
8311b5b3ec86763666b4c02a1b60458a3ff4c687
= merge of audited head 04ff2120... into base 6824fbd3...
```

Therefore this is a successful **PR merge-snapshot baseline validation**, not an independently executed naked branch-HEAD run.

### 15.2 Local exact-head execution

```text
local exact-head pytest = NOT EXECUTED
local exact-head demo   = NOT EXECUTED
```

Reason: the audit environment did not have a local checkout and did not provide direct network cloning; repository inspection and validation evidence were obtained through the connected GitHub source. No local result is fabricated.

### 15.3 Interpretation

The green baseline shows the Stage10 documentation branch has not visibly broken the existing Stage1-9 test/demo baseline. It does not validate Stage10 design correctness, because the Stage10 production architecture is not implemented.

---

## 16. Two-Implementer Test

Question: if two independent implementers read only the current `STAGE10.md`, are they forced to produce the same observable behavior?

| Topic | Unique today? | Finding |
|---|---|---|
| FROZEN_APPLICATION pipeline | NO | S10-A-B02/B03 |
| DOT tick dynamic gates | PARTIAL | gate set is clear; skill-runtime owner is not |
| source-dead DOT | PARTIAL | persistence is clear; validation/skill-gate ownership needs closure |
| same-name refresh effective fields | YES | gameplay overwrite is clear |
| state application identity | NO | S10-A-M01 |
| finite N-round normal-round timing | YES | before/after action cases are clear |
| PRE_BATTLE finite timing | NO | S10-A-B04 |
| physical expiration visibility | NO | logical vs physical active query is not globally closed |
| RECUPERATION p in (0,1) RNG | YES | active eligible case is clear |
| RECUPERATION p=1 RNG authority | NO | S10-A-B07 |
| full-troop recovery RNG | NO | S10-A-B07 |
| FIRST_AID ratio basis | YES | ActualTargetTroopLoss |
| healing-ban order | YES | after successful chance / RecoverySystem |
| standard AfterDamage checkpoint | YES | Stage9 target-settlement callback can map it |
| Cleave AfterDamage checkpoint | NO | S10-A-M06 |
| Share/Distribution direct-loss eligibility | YES | direct loss is not FIRST_AID damage event |
| fatal target damage | PARTIAL | no resurrection is clear; cleanup owner/order is not |
| death cleanup | NO | S10-A-B01/B05 |
| source skill active gate | NO | S10-A-B06/M05 |
| trace representation | NO | S10-A-M02 |

The mandatory Design Freeze test therefore fails.

---

## 17. Final Verdict

```text
BLOCKER   = 7
MAJOR     = 6
MINOR     = 4
HARDENING = 5

VERDICT = FAIL / DESIGN REPAIR REQUIRED
```

Stage10 is **not** Design Freeze eligible.

This audit does not authorize:

```text
STAGE10_DESIGN_FREEZE.md
STAGE10_BUILD_PROMPT.md
production implementation
PR merge
```

The correct next step is a design-repair round that closes the Mandatory Repair Set, followed by a fresh independent audit.
