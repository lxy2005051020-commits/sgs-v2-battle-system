# COMBO Contract Audit

> Audit target: `690081 COMBO / 连击`  
> Audit date: 2026-09-13  
> Audit type: Stage 9 Frozen Contract Independent Review  
> Final verdict: **REOPEN REQUIRED**  
> Reopen scope: **NARROW REOPEN ONLY** — do not discard the confirmed COMBO kernel.

---

## 1. Repository Baseline

This review re-read both repository `main` refs immediately before writing this audit.

```text
battle repo:
lxy2005051020-commits/sgs-v2-battle-system
exact main HEAD = 2884db6411900ca4775f8cd84c6eed3724ebc2f3
audit(stage9): verify guard frozen contract

state research repo:
lxy2005051020-commits/sgs-state-mechanics-research
exact main HEAD = 9d86e54c407913ff020bafacf8196085780b99c6
docs(index): mark combo frozen and scope death baseline
```

Inherited independent audits were read before this review:

```text
stages/stage9/audits/CONFUSION_CONTRACT_AUDIT.md
stages/stage9/audits/TAUNT_CONTRACT_AUDIT.md
stages/stage9/audits/GUARD_CONTRACT_AUDIT.md
```

Inherited cross-contract finding remains:

```text
CFS9-B01 = OPEN
```

This COMBO audit does **not** treat that inherited finding as proof. It re-audits the death boundary from the COMBO side below.

---

## 2. Authoritative Freeze Source

Current COMBO P0 source:

```text
sgs-state-mechanics-research
states/functional/combo/MECHANISM_CONTRACT.md
blob = 2cc1f658a223a334e386a0251dcc45205047b547
```

Freeze commit:

```text
10226e9afa627eadfc447cb8b0ee5613a15eadc5
docs(combo): freeze 690081 combo mechanism contract
```

The freeze commit added the P0 contract itself. The current repository evidence package still contains the earlier `QUESTION_RESULTS_INDEX.md`, `CROSS_QUESTION_CONSISTENCY_AUDIT.md`, `COUNTEREXAMPLE_AUDIT.md`, and `questions/` research layer. Those lower-priority files are not allowed to normatively override P0, but their direct battle slices remain valid evidence when deciding whether a later P0 assertion was over-generalized.

Authority order used in this review:

```text
P0 latest MECHANISM_CONTRACT / FREEZE_RECORD
P1 FREEZE_AUDIT / FINAL_CONSISTENCY_AUDIT
P2 STAGE9_CORE_ARBITRATION_RULES_V2
P3 R1-R8
P4 STAGE9_EVIDENCE_MATRIX_V2
P5 README / INDEX
P6 MINIMUM_USABLE
P7 historical inference
```

Important rule applied throughout: **P0 vs P0 is not resolved by commit recency alone.** Same-context direct contradiction must be reconciled by event boundary and evidence.

---

## 3. Superseded / Stale Sources

The following COMBO research artifacts are lower than the current P0 as normative contracts:

```text
states/functional/combo/QUESTION_RESULTS_INDEX.md
states/functional/combo/CROSS_QUESTION_CONSISTENCY_AUDIT.md
states/functional/combo/COUNTEREXAMPLE_AUDIT.md
states/functional/combo/questions/Q01.md ... Q51.md
```

They are nevertheless highly relevant as **evidence provenance**. In particular:

- `Q45.md` directly studies `NORMAL_ATTACK #1 -> Counter damage -> attacker death -> pending Combo` and observes hard cancellation.
- `Q46.md` directly studies `#1 kills commander / battle finishes -> pending Combo` and observes hard cancellation.
- `Q10.md` / `Q41.md` state that physical mid-action removal of Combo cancels an unstarted extra attack.

No new raw counter-kill slice or new battle-corpus artifact was added by the COMBO freeze commit that explains why those same contexts should now produce the opposite result.

Battle-repo Stage9 README/Evidence documents are also stale relative to the state-research COMBO freeze; this is documentation drift, not proof that COMBO was never frozen.

---

## 4. State Kernel Audit

### 4.1 Kernel

**PASS.** The stable COMBO kernel is implementation-ready:

```text
COMBO
=
within one already-started owner Action,
after NORMAL_ATTACK #1 and its synchronous downstream work complete,
at most one additional complete standard NORMAL_ATTACK #2 may be dispatched.
```

`#2` is a **new NormalAttack instance**, not:

```text
extra damage
same DamagePacket twice
double-hit animation
recursive additional attack
third/fourth hit stacking
```

Therefore `#2` must re-enter standard normal-attack behavior, including permission, live target resolution, Guard, damage, Cleave, Chain, Counter, Assault and other legitimate observers according to their own P0 contracts.

### 4.2 Two-attack ceiling

**PASS.** The following are correctly distinct invariants:

```text
cfg230 per owner Action <= 1
physical standard normal attacks per owner Action <= 2
```

`NORMAL_ATTACK #2` must never open another COMBO checkpoint. Multiple source skills cannot create #3/#4 because `690081` is a single slot and the Action has one atomic COMBO consumption opportunity.

### 4.3 Single slot / reapply

**PASS.** Current P0 consistently freezes:

```text
StatusSlot[690081] = max one instance
First Active Combo Wins
later Apply -> cfg23 REJECT
no refresh
no overwrite
no longer-duration replacement
no stacking
```

A rejected source must not overwrite source provenance.

### 4.4 Temporary vs permanent

**PASS with implementation caveats audited in §7.**

Temporary COMBO is duration-managed on holder Action timeline and can be dispelled as frozen. Permanent passive COMBO is a real status instance, occupies the same slot, is not ordinary duration-consumed, can be operationally suppressed by False Report, and resumes after suppression. It must not be implemented as an unrelated permanent boolean.

---

## 5. Lifecycle Audit

### 5.1 Correct ownership boundary

The COMBO-owned lifecycle fact that survives audit is:

```text
NORMAL_ATTACK #1 complete
+ every synchronous downstream item belonging to #1 settled
=> only then Combo Checkpoint
```

The COMBO contract should **not** own the detailed internal ordering of Cleave / Chain / Counter / Assault inside one NormalAttack instance.

### 5.2 Current §5 over-freezes the inner NormalAttack order

Current COMBO P0 §5 labels the following as `FROZEN` and calls it the complete order:

```text
NORMAL_ATTACK #1
-> normal damage
-> Assault
-> Assault damage
-> hit reactions
-> Counter / reflect
-> passive follow-up
-> heal
-> ...
-> Event Stack EMPTY
-> Combo Checkpoint
```

That is not merely a harmless non-exhaustive diagram. It explicitly places **Assault before Counter**.

Current Counterattack P0, Core Arbitration V2, and R1 converge on:

```text
Main Damage
-> immediate allowed reactions
-> Cleave
-> Chain inline/deferred completion
-> CounterBatch
-> if attacker alive: Assault
-> if attacker alive: Combo next-hit dispatch
```

R1 pairwise evidence records true normal-attack Counter before Assault at `96:0` after removing three misclassified `OnDamageTaken` callbacks, Counter before Combo `54:0`, and Assault before Combo `162:0`.

Because the ordering changes battle results when Counter kills the attacker, current COMBO §5 cannot remain an independent exact-sequence P0.

Result: **CBS9-B02**.

---

## 6. Trigger / Combo Checkpoint Audit

### 6.1 Checkpoint placement

**PASS**, after narrowing lifecycle ownership as above:

```text
#1 synchronous resolution fully complete
-> Combo Checkpoint
```

Cleave / Chain / Counter / Assault belonging to #1 must settle according to their own P0 lifecycle before the checkpoint.

### 6.2 Atomic consumption

**PASS.** Current P0 correctly distinguishes:

```text
Combo Triggered != Second Attack Executed
```

Frozen operational order:

```text
Combo Checkpoint
-> eligible && !consumed
-> atomically set combo_consumed = true
-> cfg230
-> can_normal_attack()
-> fresh target resolution
-> cfg9 #2 only if all gates pass
```

Thus a post-`cfg230` Disarm, Stun or no-target failure cannot roll back the consume and cannot cause retry.

### 6.3 Derived damage cannot create a checkpoint

**PASS.** Cleave, Chain, Share and Distribution settlements are not new owner NormalAttack instances. They cannot independently create a COMBO checkpoint.

---

## 7. Action-local Eligibility Audit

### 7.1 Entry and midway acquisition

**PASS conceptually.** The engineering tuple:

```text
combo_eligible
combo_source_skill
combo_consumed
```

is a valid project model, not an alleged official schema.

Supported semantics:

- effective COMBO at Action entry can seed eligibility;
- successful new COMBO during #1 or its reaction chain can move `false -> true` and be used in the current Action;
- successful checkpoint consumes atomically;
- Action end destroys the Action-local latch;
- next Action re-evaluates live operational state.

### 7.2 REMOVE vs SUPPRESS is not fully represented

Current P0 explicitly freezes:

```text
REMOVE != SUPPRESS
```

and freezes that False Report suppression after eligibility acquisition does not retroactively cancel the current Action. That is coherent.

However the minimal latch and recommended pseudocode have no transition for **physical mid-action removal**. Earlier direct COMBO research (`Q10`, `Q41`) says a real dispel between #1 and the checkpoint removes `690081` and cancels the unstarted extra attack. If Stage9 implements a pure once-true-never-false latch, physical REMOVE will incorrectly survive.

Required narrow clarification:

```text
SUPPRESS after eligibility acquisition
-> does not retroactively revoke current Action eligibility

PHYSICAL REMOVE before Combo Checkpoint
-> contract must explicitly decide whether eligibility is revoked
```

Current direct research supports revocation on REMOVE, but current P0 does not state the transition in its runtime model.

Result: **CBS9-M02**.

### 7.3 Action Start expiration ordering risk

P0 §13 states that holder `ACTION_START` is the duration-maintenance anchor and an exhausted temporary COMBO is removed before later action logic.

But recommended §21 pseudocode does:

```text
get_effective_combo_status_at_action_entry()
-> latch combo_eligible
-> process_action_start_status_maintenance()
```

This can pre-latch a temporary COMBO whose remaining duration should be removed at this very `ACTION_START`.

The external duration semantics are sufficiently clear; the recommended implementation order is not.

Required engineering order should be equivalent to:

```text
ACTION_START
-> lifecycle expiry / restoration maintenance
-> evaluate effective Combo for this Action
-> create or update Action-local eligibility
```

unless a re-freeze explicitly proves another order.

Result: **CBS9-M01**.

---

## 8. Target / RNG Audit

### 8.1 Fresh target resolution

**PASS.** The observable rule is:

```text
#2 does not inherit #1 target
#2 rebuilds the current legal target set
#2 resolves target against live world state
```

This is compatible with Confusion JIT, Taunt JIT, Guard live re-check, target death, and other between-hit changes.

### 8.2 `independent uniform random` is over-frozen

Current COMBO P0 §4 additionally states that, absent forcing rules, #2 performs an `independent uniform random` target choice.

R7 explicitly repaired this overclaim. Its stratified data shows that fresh reselection is observable, but observed same-target rates are not compatible with a proved uniform i.i.d. official selector. R7 therefore freezes official PRNG algorithm / call count as unknown and only recommends project-deterministic re-entry into the standard target selector.

The COMBO P0 freeze commit does not add new target-RNG evidence sufficient to supersede that limitation.

Required narrowing:

```text
FROZEN: fresh live target resolution through the standard TargetSystem
NOT FROZEN as official fact: exact uniform i.i.d. probability / PRNG consumption count
```

The simulator may still define deterministic RandomSystem behavior as an engineering policy, but must not present it as proven official internals.

Result: **CBS9-M03**.

---

## 9. NormalAttack Lifecycle Ownership Audit

| Node | Owning P0 / authority | May COMBO redefine inner ordering? | Audit result |
|---|---|---|---|
| Main Damage | standard NormalAttack + Stage8 frozen damage pipeline | NO | COMBO only dispatches a standard NormalAttack |
| Cleave | `STAGE9_CLEAVE_MECHANICS_FREEZE_RECORD.md` | NO | Cleave ordering/recursion owned by Cleave P0 |
| Chain | `STAGE9_CHAIN_MECHANICS_FREEZE_RECORD.md` | NO | Inline/deferred Chain ownership remains with Chain P0 |
| Counter | `STAGE9_COUNTERATTACK_MECHANICS_FREEZE_RECORD.md` | NO | CounterBatch must finish before Assault/Combo as frozen |
| Assault | Core Arbitration V2 + Counter P0 relative-order constraints | NO | executes after Counter when original attacker survives |
| Combo Checkpoint | COMBO P0 | YES, only its own checkpoint boundary | after entire #1 synchronous lifecycle; does not own inner reaction order |

There are currently two P0s freezing different inner sequences. This is not safely implementable until COMBO §5 is narrowed to checkpoint ownership.

---

## 10. Reaction / Recursion Audit

### 10.1 Operation identity

Required Stage9 identity model:

```text
Root Action
├─ NormalAttack #1
│  └─ downstream reactions
└─ Combo-created NormalAttack #2
   └─ downstream reactions
```

`#2` is a normal attack and therefore opens a fresh per-NormalAttack window for Guard, Cleave, Chain, Counter and Assault as applicable.

### 10.2 No Combo recursion

**PASS.** `#2` cannot create #3. The semantic guard is Action-local `combo_consumed` (or equivalent), not a global recursion-depth hack.

### 10.3 Cleave

**CONSISTENT.** Both #1 and #2 may independently produce Cleave because both are NormalAttack instances. Cleave itself is derived damage, not a NormalAttack, and therefore cannot create a COMBO checkpoint.

### 10.4 Chain

**CONSISTENT.** #1's inline/deferred Chain work must fully settle before the Combo checkpoint. #2 gets an independent complete Chain interaction. Chain feedback does not create a COMBO checkpoint.

### 10.5 Counter normal case

**CONSISTENT.** #1 creates one `ON_NORMAL_ATTACK_RECEIVED` / CounterBatch window; #2, if actually executed, creates a fresh independent window. #2 cannot inherit #1's CounterBatch.

---

## 11. Death / Termination Audit

### 11.1 Death Interaction Matrix

| Death Scenario | Current COMBO P0 | Other P0 / direct evidence | Result |
|---|---|---|---|
| actor dies from Counter during #1 | current Action continues; cfg230 and #2 may execute | Counter P0 Q05: pending Assault/Combo cancel, owner action abort; 341 counter-kills. COMBO Q45: 11/11 hard cancel. R5/R1 also hard-abort attacker-owned future work | **DIRECT CONFLICT — CBS9-B01** |
| actor dies from other reaction during #1 | §18 generalizes continuation to any own-open-action death | R5 text generalizes actor-self-death hard stop, but its direct sample family is primarily Counter; current COMBO freeze does not provide controlled per-death-family comparison | **UNRESOLVED / death-family narrowing required** |
| #1 target dies, battle continues | fresh target resolution at #2 | standard target liveness + R7 fresh reselection | **CONSISTENT** |
| all legal enemies die | cfg230 -> no target -> cfg733 -> Victory | COMBO Q46 37/37: battle termination cancels pending Combo; R5: commander-death future Assault/Combo cancel | **DIRECT CONFLICT — CBS9-B03** |
| Guard protector dies between hits | #2 must live-read Guard | GUARD P0: each NormalAttack independently resolves Guard | **CONSISTENT** |
| Taunt source dies between hits | #2 live JIT target selection | TAUNT P0: dead source fails source-liveness check; stale instance may remain but cannot force dead source | **CONSISTENT** |
| Confused actor dies | §19 says existing states remain readable and current Action can continue | CONFUSION P0 uses holder-death hard termination / state clear baseline | **CONFLICT — inherited CFS9-B01 remains OPEN** |
| #2 target dies | finish #2's permitted synchronous work; no further Combo checkpoint | reaction P0s + Action end boundary | **CONSISTENT, subject to global Victory rules** |
| commander dies during derived Chain | COMBO §9 tends to defer final Victory until owner Action closes | Chain P0 permits current Chain atomic traversal to complete; R5 cancels later owner-driven work after battle-terminating commander death | **current atomic block may finish; later Combo dispatch is not proven and conflicts with R5/Q46** |

### 11.2 Existing state presence vs operationality

COMBO §19 proves at most its own intended model that an existing `StatusSlot` may remain readable after its proposed death exception. It does **not** independently prove that every other state, especially CONFUSION, remains operational after holder death.

Therefore:

```text
StatusSlot physically present
!=
CONFUSION operational for dead-holder target selection
```

COMBO evidence cannot close `CFS9-B01`.

---

## 12. Counterattack Conflict Audit

This is the highest-priority result of the review.

### 12.1 Are the two P0s describing the same event context?

**YES.** This is not a death-family mismatch.

Counter P0 Q05 freezes:

```text
NormalAttack #1
-> Counter damage
-> original attacker dies
-> pending Assault CANCEL
-> pending Combo next-hit dispatch CANCEL
-> remaining attacker-owned action window ABORT
```

COMBO P0 §18 freezes the opposite universal rule:

```text
NormalAttack #1
-> reaction chain kills actor
-> actor dead
-> current Action continues
-> Combo Checkpoint
-> cfg230
-> NORMAL_ATTACK #2 can execute and deal damage
```

Older COMBO direct research `Q45.md` removes any ambiguity about context. It specifically filters first-hit downstream **Counter** with attacker death and finds:

```text
eligible = 11
hard-cancel = 11
counterexamples = 0
cfg230 after counter-kill = 0
#2 after counter-kill = 0
```

Representative COMBO research slice:

```text
战报_1008108_pid1003335.json, Group 5
#1 cfg9
-> defender Counter
-> attacker damage
-> attacker troops = 0
-> cfg163
-> death/abort boundary
-> cfg733
-> no cfg230
-> no #2 cfg9
```

Counter P0 independently expands the same condition to:

```text
341 counter-kill samples
dead attacker continues Assault = 0
dead attacker continues Combo #2 = 0
```

R1/R5 provide further independent support (`113` attacker counter-kill hard-stop samples in their historical extraction).

### 12.2 Disposition

This is both a **P0 direct contradiction** and an evidence-direction case of **ONE P0 OVER-GENERALIZED**.

The current repository does not contain a same-context direct sample showing:

```text
Counter kills original attacker
AND
same dead attacker later executes Combo #2
```

The COMBO freeze commit added the P0 text but no new raw counter-kill evidence artifact that supersedes Q45 / Counter Q05.

Therefore the evidence-backed narrow repair direction is:

```text
reopen COMBO death clauses
narrow ACTOR_DEATH_DURING_OWN_OPEN_ACTION by death context
explicitly exclude Counter-kill unless new direct evidence proves otherwise
preserve Counter P0 Q05 pending-action abort until contradicted by stronger same-context evidence
```

Affected COMBO P0 areas include at least §16.3 death clause, §18, §19, death-related acceptance cases, forbidden models, and any state-index global death exception that inherits the universal wording.

Result: **CBS9-B01**.

---

## 13. Provenance Audit

### 13.1 Source lock

**PASS.** Once Action eligibility is acquired from Source A, later rejected Source B must not change `cfg230` source provenance.

A mid-action successful new COMBO acquisition may set the Action source when eligibility transitions `false -> true`. Once eligibility is already held for the Action, rejected applications cannot replace that source.

### 13.2 Event provenance

R8 correctly treats `root_action_id`, `parent_event_id`, `derivation_kind`, etc. as project engineering fields rather than official log fields.

Recommended semantic shape:

```text
same Root Action
#1 = NormalAttackInstance A
#2 = NormalAttackInstance B created by COMBO checkpoint
```

#2 has a new NormalAttack identity and new per-attack reaction windows, while `combo_consumed` remains owner-Action local.

Global `reaction_depth` must not substitute for COMBO semantics.

---

## 14. Cross-Mechanism Consistency

| Cross Item | Verdict |
|---|---|
| COMBO × CONFUSION — living actor / JIT #2 target resolution | CONSISTENT |
| COMBO × CONFUSION — dead actor own-open-action | CONFLICT |
| COMBO × TAUNT | CONSISTENT |
| COMBO × GUARD | CONSISTENT |
| COMBO × CLEAVE | CONSISTENT |
| COMBO × CHAIN_LINK | CONSISTENT |
| COMBO × COUNTERATTACK — attacker survives CounterBatch | CONSISTENT |
| COMBO × COUNTERATTACK — Counter kills original attacker | CONFLICT |
| COMBO × DAMAGE_SHARE | CONSISTENT |
| COMBO × DISTRIBUTION | CONSISTENT |

### 14.1 CONFUSION

Living actor behavior is coherent: #2 is a new NormalAttack and must run a fresh JIT selector. The dead-actor case is unresolved because COMBO's universal death continuation conflicts with CONFUSION holder-death hard termination and COMBO provides no Confusion-specific proof of operationality after death.

`CFS9-B01 disposition recommendation`: **KEEP OPEN**, but narrow it after COMBO death re-freeze. Counter-kill evidence now strongly indicates that at least the Counter death family should not be used to justify a dead holder continuing into Confusion target selection. Any surviving non-Counter death exception needs its own direct controlled evidence and a Confusion-operationality test.

### 14.2 TAUNT

Each hit independently resolves live Taunt state/source liveness. Apply/expire/suppress/resume/source-death changes between hits are read at #2. No new TAUNT-specific blocker was found. Dead-actor behavior inherits the unresolved COMBO death model rather than creating a new TAUNT contradiction.

### 14.3 GUARD

Each hit independently performs:

```text
Target Selection
-> originalTarget
-> Guard Check
-> actualTarget
-> Target Lock
```

#2 cannot inherit #1 originalTarget, actualTarget or Guard result. Protector death/expiry between hits is live-read. Consistent.

### 14.4 CLEAVE

#1 and #2 may each independently Cleave. Cleave is derived damage and cannot create another Combo checkpoint. Consistent.

### 14.5 CHAIN

All #1 Chain inline/deferred work blocks the Combo checkpoint until settled. #2 has its own complete Chain interaction. Consistent once COMBO relinquishes ownership of inner NormalAttack reaction ordering.

### 14.6 COUNTER

Surviving-attacker case is coherent. Counter-kill case is the primary P0 conflict and requires reopen.

### 14.7 SHARE / DISTRIBUTION

Both mechanisms are Damage-Instance internal partition/settlement behavior. #2 enters them through its own standard damage instance and live actual target. Participant loss cannot create a new Combo checkpoint. Consistent.

---

## 15. Stage8 Compatibility

**FORMAL STAGE8 REOPEN REQUIRED = NO.**

Stage8 remains frozen with:

```text
DamageRequest
-> frozen hit/damage pipeline
-> DamageResult
-> DamageResolutionSystem
-> TroopSystem mutation
```

COMBO belongs to Stage9 action/reaction orchestration. Its correct implementation should create `NORMAL_ATTACK #2` and let the normal attack system construct the usual `DamageRequest`.

COMBO must not:

```text
copy base damage formulas
copy NormalAttack damage code
bypass DamageResolutionSystem
change Stage8 frozen ordering
```

The current COMBO blockers are Stage9 orchestration/death/termination contract defects, not Stage8 freeze-breaking defects.

---

## 16. Documentation Drift

### D01 — battle repo lacks current COMBO P0 mirror

Current battle-repo tree contains no equivalent current COMBO P0 mirror under Stage9, while the state-research repository has the frozen `states/functional/combo/MECHANISM_CONTRACT.md`.

Classification: **CROSS-REPO SYNC GAP / DOC_DRIFT**, not evidence that COMBO was never frozen.

### D02 — battle Stage9 overview is stale

`stages/stage9/research/core_arbitration_v2/README.md` still lists:

```text
COMBO core mechanics research = pending
Next Core Research Target = CONFUSION
```

and the evidence matrix remains a pre-COMBO-freeze historical matrix. `stages/stage9/README.md` also has no COMBO mirror/navigation entry.

These are documentation-sync defects only. They must not be used to downgrade the state-research P0, but they should be synced after repair/re-freeze.

### D03 — state-research top-level death wording is internally stale

State-research README material still contains broad target-death hard-termination language while the state index was updated to advertise the new COMBO own-open-action death exception. Since the exception itself is now blocked by same-context Counter evidence, documentation should not be globally harmonized until the narrow death re-freeze is complete.

---

## 17. Findings

### CBS9-B01 — BLOCKER — COMBO own-open-action death continuation contradicts Counter Q05 in the same Counter-kill context

**Severity:** BLOCKER  
**Scope:** COMBO §16.3 death clause, §18, §19, death acceptance cases / forbidden models, propagated death exception wording.

Evidence direction:

```text
Counter P0: 341 counter-kills -> 0 dead-attacker Combo #2
COMBO Q45: 11/11 counter-kills -> hard cancel, 0 cfg230 / 0 #2
R1/R5: 113 historical attacker counter-kill hard stops
current COMBO P0: says dead actor may still cfg230 + execute #2
```

Required action: narrow re-open and death-family re-freeze. Do not reopen the entire COMBO kernel.

### CBS9-B02 — BLOCKER — COMBO §5 freezes an inner NormalAttack order that conflicts with Counter/Cleave/Chain lifecycle P0 ownership

**Severity:** BLOCKER

Current COMBO §5 places Assault before Counter. Current Counter P0/Core Arbitration place Counter before Assault and Combo, with direct outcome impact when Counter kills the attacker.

Required action: COMBO must own only `Combo Checkpoint after full #1 synchronous completion`; inner Cleave/Chain/Counter/Assault order must be delegated to their owning P0s.

### CBS9-B03 — BLOCKER — Victory/no-target ordering contradicts Q46 and R5 battle-termination evidence

**Severity:** BLOCKER

Current COMBO §8.2/§9 freezes:

```text
#1 kills all legal enemies
-> cfg230
-> no target
-> cfg733
-> Victory
```

Direct COMBO Q46 finds 37/37 battle-ending #1 samples where battle termination short-circuits pending Combo, and R5 freezes commander-death future Assault/Combo cancellation.

Required action: separate:

```text
ordinary no-legal-target while battle remains open
vs
commander death / global battle finish / all-enemy elimination
```

and re-freeze exact Victory timing from direct slices.

### CBS9-M01 — MAJOR — recommended ActionStart pseudocode latches before expiry maintenance

**Severity:** MAJOR

The current pseudocode can capture a temporary COMBO that should expire at the current cfg175. Reorder lifecycle maintenance before effective-state latching, or explicitly prove an equivalent safe invariant.

### CBS9-M02 — MAJOR — Action-local latch lacks physical REMOVE invalidation semantics

**Severity:** MAJOR

P0 correctly distinguishes REMOVE from SUPPRESS but the latch model only states non-rollback for suppression/death/control. Direct Q10/Q41 evidence says mid-action physical dispel cancels pending extra attack. Add an explicit REMOVE transition; do not implement `combo_eligible` as irrevocable after acquisition for every cause.

### CBS9-M03 — MAJOR — P0 over-freezes exact independent uniform targeting

**Severity:** MAJOR

Fresh live reselection is supported. Exact official uniform i.i.d. selection / PRNG consumption is not established and conflicts with R7's repaired evidence interpretation. Narrow to standard live target resolution and keep project RandomSystem determinism separate from official-mechanism claims.

### CBS9-D01 — DOC_DRIFT — no current COMBO P0 mirror in battle repo

**Severity:** DOC_DRIFT

Sync only after COMBO repair/re-freeze.

### CBS9-D02 — DOC_DRIFT — battle Stage9 README / Core README / Evidence Matrix still describe COMBO as pending or omit it

**Severity:** DOC_DRIFT

Do not repair in this audit commit.

### CBS9-D03 — DOC_DRIFT — state README/index death-baseline wording is not mutually synchronized

**Severity:** DOC_DRIFT

Wait for death re-freeze before syncing.

### CBS9-H01 — HARDENING — death checks must be context-aware; generic `if actor.is_dead: return` is also insufficient

**Severity:** HARDENING

The fix is not to replace COMBO §18 with another universal one-line rule. Stage9 needs an explicit death/termination decision owned by the event context:

```text
Counter-kill owner abort
current atomic derived loop completion where frozen
battle-finalization barrier where frozen
future owner scheduling cancellation
```

Only after re-freeze should `can_normal_attack()` / Action orchestration encode any surviving own-open-action death exception.

### Finding counts

```text
BLOCKER   = 3
MAJOR     = 3
MINOR     = 0
DOC_DRIFT = 3
HARDENING = 1
TOTAL     = 10
```

---

## 18. Final Verdict

# REOPEN REQUIRED

This is a **NARROW REOPEN**, not a rejection of COMBO as a whole.

The following core pieces are sufficiently stable to preserve:

```text
690081 single-slot First-In-Wins state kernel
#2 = new complete standard NormalAttack instance
max physical normal attacks per Action = 2
cfg230 per Action <= 1
Combo checkpoint after #1 synchronous completion
atomic consume before second-attack gate
cfg230 != cfg9 #2
fresh live target resolution
source provenance lock
second-hit independent Taunt / Guard / Cleave / Chain / Counter / Assault windows
Share / Distribution remain DamageInstance internals
Stage8 remains closed/FROZEN
```

Narrow re-freeze must resolve before implementation:

```text
1. Counter-kill death context vs COMBO §18/§19
2. COMBO §5 lifecycle ownership and Counter-before-Assault ordering
3. Victory / battle-finish vs ordinary no-target boundary
4. ActionStart maintenance-before-latch implementation order
5. physical REMOVE vs SUPPRESS latch transitions
6. target reselection observable semantics vs unproven official uniform PRNG claims
```

`CFS9-B01` must remain **OPEN**. This review adds evidence that weakens the universal COMBO death-continuation premise, but it does not independently prove that a dead CONFUSION holder remains operational. Actual closure still requires narrow re-freeze of the affected P0 contracts.

Formal Stage8 reopen required: **NO**.

Next independent mechanism after COMBO: **CLEAVE**.
