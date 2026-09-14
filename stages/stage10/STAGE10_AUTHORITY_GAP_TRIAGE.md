# Stage10 Authority Gap Triage

> Work package: `Stage10 Design Repair R1-A / Authority Gap Triage`
>
> Purpose: distinguish gameplay-authority gaps from architecture/design gaps before the first Stage10 design repair.
>
> This document does **not** modify `STAGE10.md`, reopen Stage7/8/9 gameplay semantics, implement production code, or authorize Stage10 Design Freeze.

---

## 0. Metadata

```text
battle repo:
lxy2005051020-commits/sgs-v2-battle-system

battle branch:
stage10-persistent-state-research

battle HEAD read before triage:
81cd99a2c76d698d1e472545a16d4d7dab2b5b15

battle base tree:
9ba94c50bec7278f447024e9f4feaa665f0776b7

STAGE10.md blob:
b833f0c0a02ca8f45d9b2f560af0aad9599d041a

STAGE10_DESIGN_AUDIT.md blob:
9e8e73d0cc296e8cdb8799ffaabfbcc34a9204d3

gameplay repo:
lxy2005051020-commits/sgs-state-mechanics-research

gameplay branch:
main

gameplay HEAD:
61f2be7e87e6bfab1433657ee7f766ae0c53da9d

triage date:
2026-09-15
```

The historical SHAs in the task were treated only as locators. Both repositories were reread at their current refs before classification. The Battle branch still pointed to `81cd99a...` and Gameplay `main` still pointed to `61f2be7...` at triage start.

### Sources reread

Battle Stage10:

```text
stages/stage10/STAGE10.md
stages/stage10/STAGE10_RESEARCH_MATRIX.md
stages/stage10/STAGE10_RUNTIME_MAPPING.md
stages/stage10/STAGE10_OPEN_QUESTIONS.md
stages/stage10/STAGE10_DESIGN_AUDIT.md
stages/stage10/README.md
```

Frozen runtime/design authority rechecked:

```text
Stage7 design + final freeze/audit
Stage8 design freeze + implementation freeze record
Stage9 typed runtime / partition / finalization contracts
current production runtime owners and composition root
```

Gameplay authority rechecked:

```text
690072 BURN
690073 FLOOD
690074 POISON
690075 ROUT
690076 SANDSTORM
690077 REBELLION
690078 FIRST_AID
690079 RECUPERATION

methodology/CONTINUOUS_DAMAGE_FAMILY_BASELINE.md
FIRST_AID MECHANISM_CONTRACT + post-freeze audit + battle evidence
RECUPERATION MECHANISM_CONTRACT + battle evidence
Damage Share frozen contract
Distribution Stage9 freeze authority
global death hard-termination baseline
application-time snapshot / refresh rules
source-skill deactivation rules
```

---

## 1. Executive Verdict

```text
Total BLOCKER reviewed: 7
Total MAJOR reviewed:   6

ARCHITECTURE_ONLY:             11
AUTHORITY_ALREADY_SUFFICIENT:   1
TRUE_GAMEPLAY_AUTHORITY_GAP:    0
MIXED:                          1

Is broad Stage10 mechanism re-research required?
NO

Is targeted battle-report research required?
YES

Number of targeted research questions:
2
```

The only research admission is the RNG-consumption subpart of `S10-B07`.

No continuous-damage state, FIRST_AID as a whole, RECUPERATION as a whole, death semantics, refresh semantics, Stage9 partition semantics, or Stage7/8/9 ownership contract is reopened.

The two admitted questions are deliberately microscopic:

```text
S10-TR-01
When final recovery probability is exactly 1.0, is a probability RNG draw consumed?

S10-TR-02
When a recovery opportunity is reached but current recoverable gap is zero,
is a probability RNG draw consumed before the missing-troop cap yields zero recovery?
```

Everything else goes directly to Stage10 Design Repair.

---

## 2. Finding Classification Matrix

| Finding ID | Severity | Problem | Classification | Existing Authority | New Battle Research? | Next Action |
|---|---|---|---|---|---|---|
| `S10-B01` | BLOCKER | owner death must abort remaining state resolution, but Stage7 pre-collects and executes the full Hook Effect tuple | `ARCHITECTURE_ONLY` | Gameplay death baseline uniquely requires `TARGET_DEATH -> CLEAR_ALL_STATES -> ABORT_REMAINING_STATE_RESOLUTION`; current Stage7 runtime freezes execute-all Hook batch | NO | formal narrow Stage7 compatibility reopen; define abortable Hook batch/result semantics without changing TriggerSystem purity |
| `S10-B02` | BLOCKER | Stage10 materially changes Stage8 participant validation / calculation basis / formula-stage / trace contracts without formal authority | `ARCHITECTURE_ONLY` | Stage8 freeze/reopen rules are explicit; Stage10 gameplay snapshot facts are already frozen | NO | create explicit Stage8 compatibility reopen/addendum before Stage10 freeze |
| `S10-B03` | BLOCKER | `FROZEN_APPLICATION` does not uniquely own application-time FormulaPolicy/BaseFormula/coefficient/Modifier/Crit production | `ARCHITECTURE_ONLY` | Continuous family and per-state contracts already freeze what is application-locked vs tick-dynamic; REBELLION already freezes route and defense-stat bypass boundary | NO | freeze one application-time producer matrix and one Stage8-owned frozen-basis seam; eliminate double-apply/dead-field ambiguity |
| `S10-B04` | BLOCKER | PRE_BATTLE `current_round=0` makes finite N-round lifecycle lose one eligible opportunity | `ARCHITECTURE_ONLY` | Frozen contracts say first tick is next valid target action start and N rounds provide at most N eligible opportunities; PRE_BATTLE states are not supposed to expire before R1 | NO | repair lifecycle anchor/first-eligible representation for pre-battle applications |
| `S10-B05` | BLOCKER | no unique typed defeat cleanup owner/checkpoint across standard damage, Share, Distribution, Cleave, Chain, Counter | `ARCHITECTURE_ONLY` | Global death baseline is already unique and mandatory; runtime currently has multiple destructive paths that can publish death without synchronous state cleanup | NO | add one authoritative defeat-cleanup integration contract owned through StateLifecycleSystem and wire every destructive path |
| `S10-B06` | BLOCKER | no battle-authoritative `(owner_id, skill_slot) -> SkillRuntime` lookup for frozen source-skill active gate | `ARCHITECTURE_ONLY` | FIRST_AID/RECUPERATION deactivation semantics are already frozen; `SkillRuntime.enabled` exists but BattleContext/BattleSystems lacks authoritative lookup | NO | add typed battle-local SkillRuntime registry/query seam; do not re-research false-report/morale-shake gameplay |
| `S10-B07` | BLOCKER | Stage10 mandates exact RNG consumption for every active recovery opportunity, including `p=1.0` and zero recoverable gap | `MIXED` | active/inactive gate, fatal-target gate, healing-ban recovery-stage gate and per-event probability opportunity are frozen; exact PRNG draw consumption for `p=1.0` and zero-gap opportunity is not uniquely frozen | YES, targeted only | D1 remove unsupported blanket RNG mandate from repaired design; D2 research only `S10-TR-01` and `S10-TR-02` |
| `S10-M01` | MAJOR | retained physical state instance ID can become ambiguous across refresh-overwrite generations | `ARCHITECTURE_ONLY` | gameplay freezes one effective instance + full provenance/context overwrite, not physical ID reuse | NO | choose new physical ID or add immutable application-generation identity; preserve historical Effect provenance |
| `S10-M02` | MAJOR | `DamagePipelineTrace` frozen-lane representation is left as two legal alternatives | `ARCHITECTURE_ONLY` | Stage8 trace is a typed observable contract with `EXECUTED/NOT_EVALUATED`; no gameplay fact depends on the representation choice | NO | Stage8 reopen must choose one trace representation and regression-gate LIVE_RUNTIME |
| `S10-M03` | MAJOR | Stage7 synthetic periodic params and new official Stage10 params have no migration boundary | `ARCHITECTURE_ONLY` | official Stage10 state semantics are frozen; synthetic Stage7 path was infrastructure-only / evidence-gated | NO | freeze synthetic route as test/compatibility-only or remove its production authority; one official params path |
| `S10-M04` | MAJOR | `RecoveryOpportunityEffect` / result hierarchy / aborted tail / AFTER_DAMAGE carrier not closed | `ARCHITECTURE_ONLY` | probability/recovery behavior is separately governed by frozen authority; this finding concerns typed runtime ownership and API closure | NO | close Effect union, executor dispatch/result, Hook result and direct aftermath service contracts |
| `S10-M05` | MAJOR | `EXTERNAL_LIFECYCLE` can mean physical external removal or per-opportunity dynamic active query | `AUTHORITY_ALREADY_SUFFICIENT` | RECUPERATION contract assigns command-aura source-death removal to the external command-aura lifecycle owner; it does not authorize a hidden second active-query semantics | NO | repair STAGE10 design wording: `EXTERNAL_LIFECYCLE` means external lifecycle/removal ownership; keep temporary source-skill active gate as a distinct contract |
| `S10-M06` | MAJOR | standard/Cleave AFTER_DAMAGE integration uses separate callback shapes and different current Share ordering | `ARCHITECTURE_ONLY` | Stage9 freezes standard target damage facts, DirectTroopLoss non-reentry, admitted-work drain and Cleave permissions; FIRST_AID freezes one opportunity per eligible target damage event | NO | freeze one shared `DamageAftermathPort`/service for standard + Cleave and preserve Stage9 local-drain/finalization semantics |

### Classification totals

```text
7 BLOCKER:
A = 6
B = 0
C = 0
D = 1

6 MAJOR:
A = 5
B = 1
C = 0
D = 0

TOTAL:
ARCHITECTURE_ONLY             = 11
AUTHORITY_ALREADY_SUFFICIENT = 1
TRUE_GAMEPLAY_AUTHORITY_GAP  = 0
MIXED                         = 1
```

There is no whole audit finding that is purely `TRUE_GAMEPLAY_AUTHORITY_GAP`. The genuine research debt is narrower than `S10-B07` itself, so `S10-B07` must remain `MIXED` rather than being mislabeled wholesale as gameplay research.

---

## 3. Existing Authority Closures

### 3.1 `S10-M05` · Command-aura RECUPERATION external lifecycle

**Finding**

`EXTERNAL_LIFECYCLE` is ambiguous in the Stage10 draft.

**Authority source**

```text
sgs-state-mechanics-research/
states/persistent/recuperation/MECHANISM_CONTRACT.md

Stage10 extraction:
stages/stage10/STAGE10_RESEARCH_MATRIX.md
stages/stage10/STAGE10_OPEN_QUESTIONS.md
```

**Frozen fact**

```text
active-sourced RECUPERATION source death
→ existing state persists

command-aura RECUPERATION source death
→ associated RECUPERATION removal is owned by external command-aura lifecycle

source-skill temporary inactivity
→ separate active-gate behavior
→ missed opportunity lost
→ clock continues
```

**Why sufficient**

The two candidate meanings are not equally legal. Current authority already separates:

```text
lifecycle/removal ownership
from
temporary source-skill operational gating
```

Therefore `EXTERNAL_LIFECYCLE` must not be interpreted as an implicit per-opportunity active query.

**Required Stage10 design change**

Freeze `EXTERNAL_LIFECYCLE` as external physical lifecycle/removal ownership, and keep `PersistentSourceSkillGate` as a separate mechanism only where the source-skill deactivation contract requires it.

No battle-report research is admitted.

---

### 3.2 `S10-B07` resolved subparts · healing ban, inactive gate, fatal target

`S10-B07` is mixed, but several of its candidate ambiguities are already closed.

**Authority source**

```text
states/persistent/first_aid/MECHANISM_CONTRACT.md
states/persistent/first_aid/POST_FREEZE_CORRECTIVE_AUDIT.md
states/persistent/first_aid/BATTLE_REPORT_EVIDENCE.md
states/persistent/recuperation/MECHANISM_CONTRACT.md
states/persistent/recuperation/BATTLE_REPORT_EVIDENCE.md
```

**Frozen facts**

```text
source skill temporarily inactive
→ opportunity suppressed
→ no probability check

FIRST_AID fatal target
→ no recovery / no resurrection

HEALING_BAN
→ does not remove FIRST_AID / RECUPERATION state
→ opportunity/effect still reaches recovery resolution
→ final recovery is blocked/reduced there
```

FIRST_AID battle evidence explicitly records a successful emergency-aid opportunity followed by healing-ban reduction to zero. RECUPERATION evidence likewise records normal effect execution followed by healing-ban reduction.

Therefore Q3 from the task is **closed**:

```text
chance/opportunity processing is not skipped merely because HEALING_BAN is present;
HEALING_BAN is a recovery-resolution gate.
```

The only remaining uncertainty is whether a guaranteed probability itself consumes an RNG draw. That is `S10-TR-01`, not a healing-ban ordering question.

---

### 3.3 Q4 · dead historical source versus dynamic WEAKNESS

**Authority source**

```text
methodology/CONTINUOUS_DAMAGE_FAMILY_BASELINE.md
690072-690077 per-state MECHANISM_CONTRACT.md
project global death hard-termination baseline
```

**Frozen facts**

```text
continuous damage source death
→ existing target-owned DOT persists

Source_Weakness
→ DYNAMIC_CHECK_AT_TRIGGER
→ not application snapshot

any unit death as state owner
→ CLEAR_ALL_STATES on that dead owner
```

**Closure**

The persistent DOT keeps historical source attribution, but WEAKNESS is not a historical application snapshot. If the historical source has died, its own target-owned status set has been cleared by the global death baseline. A later DOT tick therefore cannot invent a snapshotted historical WEAKNESS fact.

This is uniquely derivable from existing authority. No targeted research is admitted.

Required design wording:

```text
historical source identity may remain valid for provenance;
dynamic source-state gates read only currently existing runtime state;
no historical weakness snapshot is created.
```

---

### 3.4 Q5 · Share / Distribution DirectTroopLoss and FIRST_AID

**Authority source**

```text
states/functional/damage_share/MECHANISM_CONTRACT.md
stages/stage9/research/core_arbitration_v2/STAGE9_DISTRIBUTION_MECHANICS_FREEZE_RECORD.md
stages/stage9/hardening/STAGE9_TYPED_RUNTIME_CONTRACTS.md
```

**Frozen fact**

Share sharer loss and Distribution participant loss are `Attributed Direct Troop Loss`, not a second normal DamageEvent. The frozen contracts explicitly forbid re-entry into:

```text
Defense
Evasion / Resistance
FIRST_AID
Counter
Chain
Share / Distribution recursion
generic Hurt callback
base formula
```

The original target remains a normal damage recipient and may trigger FIRST_AID from its authoritative target settlement.

**Closure**

Q5 is not a simulator-only inference. Current Gameplay/Stage9 authority itself explicitly says partition-derived direct troop loss does **not** trigger FIRST_AID.

No research is admitted.

---

### 3.5 Q6 · Share / Distribution relative ordering versus FIRST_AID

The exact hidden internal implementation order does not need to be rediscovered to repair Stage10.

Frozen Stage9 facts already separate:

```text
planned partition amounts
normal target settlement
AttributedDirectTroopLoss
victory latch
admitted local-work drain
finalization
```

and FIRST_AID is eligible only from the normal target damage event, not from derived DirectTroopLoss.

For Share, target settlement is already committed before sharer direct loss. For Distribution, participant direct losses are a distinct transaction-local operation and the target settlement remains the single FIRST_AID-eligible damage fact.

The Stage10 repair requirement is therefore architectural:

```text
one shared standard/Cleave aftermath port
+ one authoritative target-settled fact
+ completion-local FIRST_AID work
+ Stage9 admitted-work/finalization preservation
```

Stage10 may freeze an engineering checkpoint that preserves these observable facts without claiming an unsupported universal hidden server callback order.

No new battle-report research is admitted for `S10-M06`.

---

## 4. Architecture-Only Repairs

### 4.1 Stage7 Compatibility Reopen

Applies to:

```text
S10-B01
S10-M04
```

Repair requirements:

```text
- formally reopen only Hook batch completion semantics required by death hard termination
- preserve TriggerSystem as pure collector
- allow abort/skipped-tail representation after owner death
- update HookResolutionResult so it no longer falsely implies every pre-collected Effect executed
- do not turn EventBus into rule control flow
```

No gameplay question is open.

### 4.2 Stage8 Compatibility Reopen

Applies to:

```text
S10-B02
S10-B03
S10-M02
```

Repair requirements:

```text
- explicit Stage8 reopen authority
- one typed LIVE_RUNTIME / FROZEN_APPLICATION contract
- application-time producer table for FormulaPolicy/BaseFormula/coefficient/Modifier/Crit
- REBELLION defense-policy consumption at the actual formula-producing checkpoint
- no modifier/crit double application
- one frozen trace representation
- exact LIVE_RUNTIME golden compatibility including RNG consumption
```

The gameplay snapshot split is already frozen. This is pipeline ownership design.

### 4.3 Stage9 Orchestration

Applies to:

```text
S10-M06
```

Repair requirements:

```text
- one typed DamageAftermathPort/service used by standard and Cleave damage
- authoritative input = settled target damage fact / ActualTargetTroopLoss
- partition DirectTroopLoss remains FIRST_AID-ineligible
- completion-local aftermath must respect victory latch and finalization drain
- no duplicate Cleave-only FIRST_AID engine
```

### 4.4 Lifecycle

Applies to:

```text
S10-B04
S10-M01
```

Repair requirements:

```text
- PRE_BATTLE application cannot anchor first eligible round at nonexistent round 0
- N-round state receives the frozen number of future eligible action-start opportunities
- refresh before/after action recomputes the correct opportunity window
- choose physical replacement ID or add immutable application-generation identity
- define logical-active versus physical-presence query semantics so an expired-but-not-yet-removed instance cannot leak to external observers
```

### 4.5 Death Cleanup

Applies to:

```text
S10-B05
S10-B01
```

Repair requirements:

```text
- StateLifecycleSystem remains physical state mutation owner
- one typed defeat-cleanup integration point
- clear dead owner's states immediately
- reject later state application to dead owner
- abort remaining owner-state resolution
- wire standard settlement, Share/Distribution direct loss, Cleave, Chain feedback and Counter paths
- define ordering relative to UNIT_DEFEATED publication and Stage9 finalization observation
```

### 4.6 Recovery Runtime

Architecture portion of:

```text
S10-B07
S10-M04
S10-M06
```

Repair requirements already supported without new research:

```text
- inactive source-skill gate before any probability opportunity
- fatal target cannot recover
- healing ban remains RecoverySystem-time prevention
- probability for 0 < p < 1 uses BattleContext.random only
- do not freeze p=1 or zero-gap draw behavior until S10-TR-01/02 close
```

### 4.7 Composition / Dependency

Applies to:

```text
S10-B06
S10-M06
```

Repair requirements:

```text
- battle-authoritative SkillRuntime registry/lookup by owner + slot
- no duplicate external-control store
- BattleSystems wires one shared aftermath service rather than separate semantic callbacks
```

### 4.8 Provenance

Applies to:

```text
S10-M01
S10-M04
```

Repair requirements:

```text
- immutable application-generation provenance if physical slot ID is retained
- recovery opportunity/result types preserve state/source/skill/slot lineage as required
- historical Effect attribution must never silently resolve to refreshed provenance
```

### 4.9 Legacy Migration

Applies to:

```text
S10-M03
```

Repair requirements:

```text
- define status of PeriodicDamageStateParams / PeriodicRecoveryStateParams
- synthetic Stage7 capability tests may remain, but they cannot be a second official Stage10 runtime route
- official eight-state definitions must map to one authoritative Stage10 params family
```

---

## 5. True Gameplay Authority Gaps

There are no whole findings classified `TRUE_GAMEPLAY_AUTHORITY_GAP`.

There are exactly two admitted gameplay subquestions under mixed finding `S10-B07`.

### S10-TR-01

**Affected states**

```text
690078 FIRST_AID
690079 RECUPERATION
```

**Exact gameplay question**

When the final trigger probability presented to the official runtime is exactly `100%`, does the official runtime still consume one probability RNG draw?

**Known facts**

```text
- FIRST_AID is per eligible damage-event probability opportunity.
- RECUPERATION has source-defined probability behavior, including guaranteed sources.
- 100% sources show successful execution with no failure log.
- temporary source-skill inactivity suppresses the opportunity and therefore consumes no probability check.
- simulator RNG owner must remain BattleContext.random.
- current simulator RandomSystem.chance(1.0) does consume one random() draw.
```

**Unknown fact**

Whether the official runtime consumes a PRNG draw for a logically guaranteed `p=1.0` opportunity.

**Competing hypotheses**

```text
A. DRAW_AT_1_0
   chance/roll path is still entered; one RNG value is consumed.

B. SHORT_CIRCUIT_1_0
   guaranteed probability is resolved deterministically; no RNG value is consumed.
```

**Observable difference**

The current recovery result is identical, but every later stochastic operation in the battle can consume a different RNG value. Deterministic replay diverges.

**Required evidence**

A differential sample capable of revealing RNG-sequence position, not merely `success at 100%`:

```text
- reproducible/replay-controlled battle or raw trace with known shared random stream, and
- a guaranteed FIRST_AID/RECUPERATION opportunity followed by an observable stochastic event, and
- matched control where the guaranteed opportunity is absent while all earlier stochastic admissions are identical.
```

If ordinary battle reports do not expose enough information to distinguish PRNG position, aggregate success/failure counts are insufficient and must not be treated as proof.

**Minimum battle-report sample shape**

```text
paired or replay-equivalent traces
+ one guaranteed recovery opportunity
+ one downstream RNG-sensitive discriminator
+ no intervening unmatched RNG consumer
```

**Blocking Stage10 design?** `YES` for exact deterministic RNG replay semantics; `NO` for unrelated lifecycle/damage architecture repairs.

---

### S10-TR-02

**Affected states**

```text
690079 RECUPERATION
690078 FIRST_AID only where a legitimate eligible AFTER_DAMAGE opportunity can reach zero recoverable gap
```

**Exact gameplay question**

When a recovery opportunity has otherwise been reached but the target currently has no missing troops, does the official runtime still execute the probability draw before the missing-troop cap yields zero recovery?

**Known facts**

```text
- RECUPERATION battle evidence includes normal cfg_96 execution with zero actual recovery at full/no-gap conditions.
- missing-troop cap is dynamic at recovery resolution.
- FIRST_AID/RECUPERATION healing-ban cases prove healing prevention does not simply delete the state/opportunity.
- current authority does not state an RNG-consumption rule for zero recoverable gap.
```

**Unknown fact**

Whether `missing troops == 0` is checked before probability RNG admission or only after chance success when RecoverySystem/TroopSystem caps recovery.

**Competing hypotheses**

```text
A. ROLL_THEN_CAP
   opportunity rolls probability; successful recovery resolves to 0 because missing-troop cap is 0.

B. ZERO_GAP_SHORT_CIRCUIT
   zero recoverable gap makes the probability opportunity ineligible; no RNG draw.

C. other authority-backed sequencing discovered by evidence.
```

**Observable difference**

Immediate troops may remain identical, but downstream deterministic RNG sequence differs. If a visible success/failure protocol marker is emitted at zero gap, event/log output may also differ.

**Required evidence**

Prefer a non-guaranteed RECUPERATION source at full troops so probability-path presence can be distinguished. Pair it with a later observable RNG-sensitive event under replay-equivalent conditions. For FIRST_AID, first prove that an authority-valid eligible damage event can actually reach the opportunity with zero recoverable gap; do not manufacture an unreachable synthetic case and call it official evidence.

**Minimum battle-report sample shape**

```text
RECUPERATION:
- target at max troops at TARGET_ACTION_START
- active non-guaranteed source
- opportunity window definitely reached
- downstream RNG discriminator

FIRST_AID, only if reachable:
- eligible AFTER_DAMAGE_EVENT under frozen contract
- target has zero recoverable gap at opportunity checkpoint
- downstream RNG discriminator
```

**Blocking Stage10 design?** `YES` for exact RNG-admission ordering; `NO` for other R1 architecture repairs.

---

## 6. Research Admission Gate Applied

| Candidate | Authority unique? | Changes gameplay / replay? | Derivable from Stage7/8/9? | Pure API/owner issue? | Admit research? |
|---|---:|---:|---:|---:|---:|
| `p=1.0` RNG draw | NO | YES, replay RNG | NO | NO | YES |
| zero recoverable gap RNG draw | NO | YES, replay RNG | NO | NO | YES |
| HEALING_BAN vs chance order | YES | n/a | n/a | NO | NO |
| dead historical source WEAKNESS | YES | n/a | n/a | NO | NO |
| Share DirectTroopLoss -> FIRST_AID | YES | n/a | n/a | NO | NO |
| Distribution DirectTroopLoss -> FIRST_AID | YES | n/a | n/a | NO | NO |
| Share/Distribution aftermath port ordering | sufficient observable contract | potentially, but Stage9 local drain preserves it | YES | YES, orchestration | NO |
| Stage7 death abort | YES | YES | gameplay side already frozen | YES, compatibility | NO |
| PRE_BATTLE lifecycle off-by-one | YES | YES | gameplay side already frozen | YES | NO |
| Stage8 frozen basis producer | gameplay boundary YES | YES | requires explicit reopen design | YES | NO |
| SkillRuntime registry | YES | YES | runtime fact missing | YES | NO |
| trace representation | n/a | typed trace only | n/a | YES | NO |
| refresh application ID | n/a | provenance trace/replay integrity | n/a | YES | NO |

---

## 7. R1-A Verdict

```text
BROAD STAGE10 MECHANISM RE-RESEARCH = NOT AUTHORIZED

TARGETED RESEARCH = AUTHORIZED ONLY FOR:
S10-TR-01
S10-TR-02

STAGE10 DESIGN REPAIR = REQUIRED
STAGE10.md MODIFICATION IN THIS WORK PACKAGE = FORBIDDEN / NOT PERFORMED
PRODUCTION IMPLEMENTATION = NOT AUTHORIZED
STAGE10 DESIGN FREEZE = NOT AUTHORIZED
```

The next design-repair round must not reopen already frozen mechanism questions merely because the current architecture cannot represent them cleanly. Architecture pays its own debts; gameplay research is not a laundering service for design ambiguity.
