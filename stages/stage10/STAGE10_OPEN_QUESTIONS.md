# Stage10 · Persistent State Runtime Integration · Question Closure Ledger

> Status: `DESIGN FROZEN / ALL BLOCKERS & AUDIT FINDINGS CLOSED`  
> Design Freeze Record: `STAGE10_DESIGN_FREEZE.md`  
> Final Audit: `PASS / DESIGN FREEZE ELIGIBLE`  
> Open Design Blockers: `0`  
> Open Freeze-Blocking Questions: `0`  
> Normative architecture: `STAGE10.md` (FROZEN)

This file was originally the Stage10 open-question list. It serves as a closure ledger so historical design blockers are not accidentally re-opened by an implementation author.

---

## 1. Core design questions closed by R1-C

| Historical item | R1-C answer | Status |
|---|---|---|
| S10-B01 snapshot-backed continuous damage ingress | Stage8 `FROZEN_APPLICATION` uses typed frozen application-generation inputs, not final nominal damage | `CLOSED / REPAIR CLAIMED` |
| S10-B02 source-dead persistent damage | historical source roster identity + authorized periodic frozen lane; source-alive validation skipped only there | `CLOSED / REPAIR CLAIMED` |
| S10-B03 FIRST_AID checkpoint | one shared synchronous `DamageAftermathPort` after target settlement/defeat cleanup and before later callbacks | `CLOSED / REPAIR CLAIMED` |
| S10-B04 owner-relative lifecycle | explicit PRE_BATTLE domain + `ActionProgressTracker` + first/last eligible combat rounds | `CLOSED / REPAIR CLAIMED` |
| S10-M01 same-name replacement | retain physical instance id; allocate new immutable application generation on every apply/refresh | `CLOSED / REPAIR CLAIMED` |
| S10-M02 FIRST_AID RNG ownership | `RecoveryOpportunitySystem`; simulator one-draw policy per admitted opportunity | `CLOSED / REPAIR CLAIMED` |
| S10-M03 recovery provenance | generation snapshot + source unit/skill/slot + aftermath lineage outside RecoverySystem core | `CLOSED / REPAIR CLAIMED` |
| S10-M04 temporary skill inactive gate | `SkillRuntimeRegistry` lookup; QUERY mode reads only explicit skill enabled/disabled fact | `CLOSED / REPAIR CLAIMED` |
| S10-M05 snapshot schema | typed damage/recovery basis, no UnitRuntime/callback/untyped dict | `CLOSED / REPAIR CLAIMED` |
| S10-M06 official state tags / promotion boundary | Stage10 definitions use new typed params; unrelated Stage8 DEFER bindings remain deferred | `CLOSED FOR DESIGN / BUILD MUST IMPLEMENT GATE` |

---

## 1.1 Design questions closed by R2-B

| Finding | R2-B answer | Status |
|---|---|---|
| S10-R2-B01 Stage9 Cleave vs FIRST_AID | Stage9 Addendum created; preserved frozen ordering: target settlement -> share direct loss -> aftermath -> recovery -> callbacks | `CLOSED / REPAIR CLAIMED` |
| S10-R2-B02 ASSAULT recovery permission | Formally authorized in Stage9 Addendum and ReactionPermissionPolicy | `CLOSED / REPAIR CLAIMED` |
| S10-R2-M01 Authority Sync | Targeted research formally promoted to Authority `main` @ `a9a05cef` | `PROMOTED & PASS` |
| S10-R2-M02 ExecutionRight ownership | Split into Decision Owner (ExecutionRightSystem), Dispatch Owner (RuleHookSystem), Router (EffectExecutor) | `CLOSED / REPAIR CLAIMED` |
| S10-R2-M03 PersistentSourceSkillGate | Normative family mapping table added; EXTERNAL_LIFECYCLE unified | `CLOSED / REPAIR CLAIMED` |
| S10-R2-M04 Generation ID propagation | End-to-end propagation matrix added across all DTOs and events | `CLOSED / REPAIR CLAIMED` |
| S10-R2-M05 Battle-end state cleanup | StateLifecycleSystem.clear_all_on_battle_end formally defined | `CLOSED / REPAIR CLAIMED` |

---

## 1.2 Design questions closed by R3-B

| Finding | R3-B answer | Status |
|---|---|---|
| S10-R3-B01 Target Defeat vs Owner Defeat scope | Disentangled `REJECT_CURRENT(TARGET_DEFEATED)` (only rejects current intent, living owner continues) and `ABORT_OWNER_STATE_REMAINDER(OWNER_DEFEATED)` (cancels remaining dead owner intents, other units continue). Formalized Timeline A/B/C/D. | `CLOSED / REPAIR CLAIMED` |
| S10-R3-M01 Recuperation Gate 2 DamageAftermathFact requirement | Introduced `RecoveryOpportunityKind` (`FIRST_AID_AFTER_DAMAGE` vs `RECUPERATION_ACTION_START`). Gate 2 is REQUIRED for FIRST_AID, NOT_APPLICABLE for RECUPERATION. RECUPERATION admitted at UNIT_ACTION_START with aftermath_fact=None. | `CLOSED / REPAIR CLAIMED` |
| S10-R3-M02 ExecutionRightSystem evaluate_rule_intent typed interface | Defined typed `RuleIntentExecutionDescriptor` dataclass carried by `RuleIntent`, consumed by `evaluate_rule_intent(descriptor, context) -> ExecutionRightDecision`. Zero duck typing. | `CLOSED / REPAIR CLAIMED` |
| S10-R3-N01 RandomSystem.chance native one-draw invariant ($p=0, p=1$) | Confirmed native `sgs_v2` implementation draws exactly one float for all $p \in [0.0, 1.0]$. Documented NO Stage 2 reopen and zero RandomSystem changes. | `CLOSED / REPAIR CLAIMED` |


---

## 2. Targeted-research closures supplied to R1-C

These are no longer architecture blockers:

```text
FIRST_AID eligibility
≠ ActualTargetTroopLoss > 0

WEAKNESS_ZERO
→ resolved damage-event topology exists
→ ActualTargetTroopLoss = 0
→ FIRST_AID opportunity YES

BARRIER_ZERO
→ resolved damage-event topology exists
→ ActualTargetTroopLoss = 0
→ FIRST_AID opportunity YES

EVASION / MISS
→ no resolved-hit damage event
→ FIRST_AID opportunity NO
```

Full-troop recovery is also closed:

```text
recoverable_gap == 0
!=
no opportunity
```

Official hidden recovery PRNG consumption remains:

```text
UNKNOWN / UNOBSERVABLE
```

Stage10 therefore owns only a simulator determinism policy, not a claimed official PRNG fact.

---

## 3. External dependencies that remain intentionally open

### 3.1 Evasion / Barrier official bindings

Stage10 consumes typed aftermath/hit topology when available but does not promote the complete official Evasion/Barrier production implementations.

```text
Status = EXTERNAL / NON-BLOCKING
```

### 3.2 Physical / Strategy Critical official bindings

Stage10 freezes how an authorized crit context would be captured at application time, but it does not promote complete official CRITICAL / STRATEGY_CRITICAL bindings.

```text
Status = EXTERNAL / NON-BLOCKING
```

### 3.3 Positive dispel

Universal positive-dispel policy is not invented here.

```text
Status = EXTERNAL / NON-BLOCKING
```

### 3.4 Command-aura source death

When an external command-aura lifecycle owns removal, Stage10 uses `EXTERNAL_LIFECYCLE` to mean:

```text
external owner physically removes/replaces the state through StateLifecycleSystem
```

It is not a dynamic per-opportunity callback.

### 3.5 FLOOD external observers / delay

External skills may observe FLOOD identity later; Stage10 only preserves typed identity/queryability.

### 3.6 Cleanse skill selection

Stage10 provides state removal ownership, not universal cleanse target-selection policy.

---

## 4. Non-blocking research debt

The following remain explicitly outside Stage10 architecture freeze:

```text
universal same-node ordering among unrelated persistent families
microscopic source-skill formula constants not already authoritative
future mechanisms that create additional action-start nodes
unrelated positive-dispel selection semantics
```

No implementation may fill these gaps with an undocumented “reasonable default” and then call it official behavior.

---

## 5. Questions explicitly forbidden from re-opening without new contradictory authority

```text
Q: Does ordinary source attr/modifier/crit context of an existing continuous state update dynamically?
A: NO. It is application/refresh locked.

Q: Does source death generically cancel existing continuous damage?
A: NO.

Q: Can owner death leave attached persistent states active?
A: NO.

Q: Can same-name Stage10 states coexist as multiple effective instances?
A: NO.

Q: Is REBELLION DirectTroopLoss / true damage?
A: NO.

Q: Does REBELLION reroute after application because ATK/INT changed?
A: NO.

Q: Is FIRST_AID once per round?
A: NO. One opportunity per eligible damage aftermath.

Q: Does ActualTargetTroopLoss == 0 automatically deny FIRST_AID?
A: NO.

Q: Does full troop automatically deny a recovery opportunity?
A: NO.

Q: Is official probability RNG consumption at 100% or zero gap known?
A: NO. Official behavior is UNKNOWN / UNOBSERVABLE.

Q: Can Stage10 use Python random directly?
A: NO. Runtime RNG remains context.random.
```

---

## 6. Current admission gate

The design freeze-gate audit has completed with verdict PASS:

```text
Stage10 Architecture Design: FROZEN
Freeze Record: STAGE10_DESIGN_FREEZE.md
Final Audit: STAGE10_FINAL_DESIGN_FREEZE_GATE_AUDIT.md (PASS)

DESIGN BLOCKERS           = 0
OPEN FREEZE QUESTIONS     = 0
DESIGN FROZEN             = YES
BUILD PROMPT AUTHORIZED   = YES
PRODUCTION IMPLEMENTATION = NOT YET STARTED
NEXT STEP                 = Stage10 Build Prompt Preparation
```

