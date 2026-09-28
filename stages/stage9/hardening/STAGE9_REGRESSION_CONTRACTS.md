# Stage9 Regression Contracts

Package: `RF-C01 — IMPLEMENTATION_HARDENING`

Status: `FROZEN TEST SPECIFICATION / NO TEST CODE ADDED IN RF-C01`

All cases use explicit Given / When / Then semantics. Expected numeric values are contractual vectors, not language built-in `round()` results.

## A. Target Arbitration — 7 contracts

### REG-TGT-01 — Confusion shadows Taunt selector
**Given** an actor has operational Confusion and an otherwise operational Taunt.  
**When** a new NormalAttack performs selector arbitration.  
**Then** the Confusion selector decides the intended/pre-redirect target; Taunt is shadowed for that selection only and is not removed or suppressed by that fact.

### REG-TGT-02 — Taunt lifecycle continues while selector is shadowed
**Given** Taunt physically exists and remains lifecycle-valid while Confusion controls the current target selection.  
**When** Confusion later ceases before a future NormalAttack.  
**Then** the future NormalAttack may read the still-existing Taunt according to Taunt's own operational/source-liveness rules; no synthetic Taunt refresh/removal occurred merely because Confusion previously shadowed it.

### REG-TGT-03 — Guard occurs after selector
**Given** selector arbitration chooses B as intended target and B is validly guarded by C.  
**When** target resolution completes.  
**Then** `intendedAttackTarget=B`, exactly one Guard pass runs, `postRedirectActualTarget=C`, and B retains selection provenance only.

### REG-TGT-04 — Guard is single-pass
**Given** B is guarded by C and C is itself guarded by D.  
**When** A attacks B.  
**Then** the attack resolves B→C and stops; C is not recursively redirected to D.

### REG-TGT-05 — Combo #2 uses fresh target resolution
**Given** Combo #1 completed and #2 is legally admitted while target legality changed between hits.  
**When** NormalAttack #2 begins.  
**Then** #2 creates a new `NormalAttackInstanceId` and target-resolution context and does not inherit #1's selected/intended/actual target.

### REG-TGT-06 — Guard reruns for Combo #2
**Given** #1 had a Guard result and Guard state/liveness changes before #2.  
**When** #2 resolves its target.  
**Then** #2 performs a new single Guard check against the live world and does not reuse #1's Guard result.

### REG-TGT-07 — Guard original target may become Cleave secondary
**Given** A selects B, C guards B, so C becomes actualTarget; B remains alive on C's side and otherwise qualifies as a Cleave secondary.  
**When** Cleave plans secondaries around C.  
**Then** B may be included in the secondary queue; being the pre-Guard intended target grants no Cleave immunity.

## B. Combo — 5 contracts

### REG-CMB-01 — ACTION_START maintenance before grant
**Given** a temporary Combo instance expires at the current ACTION_START.  
**When** the Action begins.  
**Then** lifecycle maintenance physically removes it before effective Combo evaluation and no `ComboActionGrant` is created.

### REG-CMB-02 — Physical REMOVE revokes an unconsumed grant
**Given** a valid Action-local grant exists from Combo instance X and the checkpoint has not consumed it.  
**When** X is physically removed.  
**Then** the grant becomes `REVOKED_BY_PHYSICAL_REMOVE`; no cfg230 may later be emitted from X for that Action.

### REG-CMB-03 — Ordinary SUPPRESS after grant does not revoke current grant
**Given** a valid grant was created while Combo was operational.  
**When** the physical instance becomes ordinarily suppressed before the checkpoint but is not removed.  
**Then** the current Action grant remains valid; the next Action re-evaluates operational state independently.

### REG-CMB-04 — Atomic consume ceiling
**Given** an Action has a valid Combo grant.  
**When** the checkpoint consumes it and a later #2 admission/target gate fails.  
**Then** consume is not refunded: cfg230 count <= 1, consume count <= 1, and total physical NormalAttack count for the Action <= 2.

### REG-CMB-05 — Actor death cancels future owner branches
**Given** the original attacker dies during NormalAttack #1 before Assault/Combo future branches are admitted.  
**When** the parent lifecycle reaches the branch boundary.  
**Then** future Assault and Combo #2 are not admitted, cfg230 is not emitted, and no #2 Confusion/Taunt/Guard target-resolution pass occurs. This is the post-RF-P03 regression authority for historical `TAS9-H01`.

## C. Cleave — 5 contracts

### REG-CLV-01 — Cleave base uses actual committed main-target troop loss
**Given** the main target has 55 troops remaining and the normal hit's assigned damage exceeds 55; Cleave ratio is 54%.  
**When** Cleave derives its value.  
**Then** base fact is `ActualTargetTroopLoss=55` and derived calculated damage is `floor(55×0.54)=29`.

### REG-CLV-02 — Cleave does not re-enter upstream damage formula
**Given** a valid Cleave secondary request whose parent main hit already resolved offense/defense/modifiers/Crit.  
**When** the secondary is processed.  
**Then** it does not execute weapon/strategy base formula, target generic damage-modifier recalculation, or Crit reroll.

### REG-CLV-03 — Cleave permission policy
**Given** a Cleave secondary derived event.  
**When** downstream callbacks are evaluated.  
**Then** Evasion, Resistance, one effective Share/Distribution partition, FirstAid, Chain, and eligible recovery are available according to their P0 rules; Counter and recursive Cleave are blocked; Guard/Taunt/Combo are not reopened.

### REG-CLV-04 — Effect-major queue and JIT secondary skip
**Given** two Cleave effects A then B by skill-slot order, with planned secondaries in global-slot ascending order, and an earlier downstream result kills a later planned secondary before its step.  
**When** the queue drains.  
**Then** all admitted A steps are processed before B begins; the dead planned secondary is skipped at JIT liveness check; no reordering, replacement target, or revisit occurs.

### REG-CLV-05 — Post-Guard anchor controls Cleave topology
**Given** Guard redirects a normal attack from B to C.  
**When** the main hit commits and Cleave is admitted.  
**Then** C is the Cleave anchor and B is treated only as an ordinary potential secondary under the frozen candidate rules.

## D. Chain — 4 contracts

### REG-CHN-01 — Deferred snapshot/live split
**Given** trigger node B qualifies Deferred Chain at `triggerDamage=500` under old owner A / ratio 20%, then before execution the old Chain is replaced by current owner D / ratio 30%, with B still alive and chained.  
**When** Deferred Chain executes.  
**Then** `triggerDamage` remains 500, while current owner/ratio/effect metadata are live-read; calculation uses the current 30% state and current attribution. If B or current Chain state is gone, the work cancels locally.

### REG-CHN-02 — One-pass slot traversal
**Given** a Chain traversal visits slot 0, then a previously unlinked later slot 2 becomes linked before slot 2 is visited, while an already-passed slot changes again.  
**When** traversal continues.  
**Then** slot 2 may join if currently eligible; a passed slot is never revisited; every slot executes at most once per `ChainTraversalId`.

### REG-CHN-03 — Propagated commander death does not abort current broadcast
**Given** an admitted Chain traversal has remaining eligible later slots and one propagated step kills the enemy commander.  
**When** the death/victory condition is recorded.  
**Then** victory latches but the current Chain traversal drains its remaining eligible slots before BattleFinalized.

### REG-CHN-04 — TRUE_FEEDBACK restricted settlement
**Given** a Chain feedback value is produced.  
**When** it settles.  
**Then** it uses restricted attributed troop-loss semantics and does not enter normal formula/HitResolution, Share, Distribution, Counter, FirstAid, Guard, or recursive Chain.

## E. Damage Share — 4 contracts

### REG-SHR-01 — Target survives, sharer commits
**Given** Share plan has positive `Dtarget` and `Dsharer_theoretical` and target survives the target-first commit.  
**When** the transaction executes.  
**Then** target commits first, death check passes, and sharer receives its attributed direct troop loss with actual clamp/stat attribution.

### REG-SHR-02 — Lethal target interrupts pending sharer
**Given** Share plan has positive pending sharer loss and `Dtarget` is lethal to target.  
**When** target-first commit reaches zero troops.  
**Then** `TARGET_DEATH_INTERRUPT` fires and pending sharer work is discarded; sharer actual loss from this transaction is 0.

### REG-SHR-03 — Share direct loss is not a hit
**Given** a non-lethal Share transaction proceeds to sharer loss.  
**When** the sharer loses troops.  
**Then** the operation is `AttributedDirectTroopLoss` with physical attacker/skill/victim/credit owner/provenance and theoretical vs actual amount; it does not trigger Defense, Evasion, Resistance, FirstAid, Counter, Chain, Share, Distribution, or generic Hurt callbacks.

### REG-SHR-04 — Partition exclusivity and no replacement resurrection
**Given** a target has Distribution and a later Share application replaces it according to Frozen precedence/replacement semantics.  
**When** an eligible DamageEvent reaches partition and later the Share disappears.  
**Then** only one partition policy executes for the DamageEvent, and the displaced Distribution instance does not resurrect merely because Share expired/was removed.

## F. Distribution — 4 contracts

### REG-DST-01 — Fixed plan, invalid participant SKIP
**Given** a Distribution transaction plans participants `[P1,P2]`, fixes `N=2`, `Dtarget`, and one `Dparticipant`, then P2 becomes invalid before its step.  
**When** the transaction reaches P2.  
**Then** P2 is skipped; N, Dtarget, and Dparticipant are unchanged; no repartition, redistribution, remainder repair, or replacement participant occurs.

### REG-DST-02 — Ordinary participant death does not abort plan
**Given** an admitted Distribution plan has later participant/target work and an ordinary non-commander participant dies during its commit.  
**When** the transaction continues.  
**Then** remaining planned eligible steps and original target commit continue according to the fixed plan.

### REG-DST-03 — Commander participant death uses project runtime default
**Given** a commander is a planned Distribution participant and dies during an admitted transaction with later planned local work.  
**When** victory condition latches.  
**Then** under `PROJECT_RUNTIME_DEFAULT (NOT EMPIRICALLY PROVEN GAME RULE)` the admitted transaction drains its planned local steps before the Finalization Barrier; no N/amount recomputation occurs.

### REG-DST-04 — Distribution participant loss is not a hit
**Given** a planned participant receives its assigned Distribution loss.  
**When** troop loss commits.  
**Then** it is typed `AttributedDirectTroopLoss`, records theoretical and actual loss/provenance, and cannot re-enter normal HitResolution or hit callbacks.

## G. Counter — 5 contracts

### REG-CTR-01 — Post-admission suppression/removal does not revoke entry
**Given** CounterBatch entry C1 was admitted at the trigger window.  
**When** its CounterState later becomes suppressed, expires, or is removed before C1 begins, while owner remains alive.  
**Then** C1 remains an admitted batch entry; state operationality is not re-run as an admission test.

### REG-CTR-02 — Counter owner death fails local execution gate
**Given** C1 is already admitted but its Counter owner dies before C1 begins.  
**When** C1 reaches the head of the batch.  
**Then** it fails the execution-time owner-liveness gate and does not execute, without rewriting the historical admission list.

### REG-CTR-03 — C1 commander kill retains admitted sibling
**Given** original attacker is commander and `CounterBatch=[C1,C2]` is already admitted.  
**When** C1 kills the original attacker and latches victory.  
**Then** C2 remains in the batch, runs the explicit zero-loss terminal path against the dead target, the batch drains, and only then may the Finalization Barrier finalize battle.

### REG-CTR-04 — Dead-target sibling bypasses full weapon pipeline
**Given** an admitted Counter sibling begins after its target already has zero troops.  
**When** it executes.  
**Then** emit CounterExecute + attributed zero troop loss only; do not invoke weapon base formula, Evasion, Resistance, Share, Distribution, Chain, or FirstAid.

### REG-CTR-05 — Counter kill cancels original attacker's future branches
**Given** Counter damage kills the original attacker during NormalAttack #1 before that attacker's Assault/Combo branches are admitted.  
**When** parent lifecycle reaches those branch points.  
**Then** those future owner branches are cancelled while already-admitted reaction work remains governed by its own local rules.

## H. Finalization Barrier — 6 mandatory contracts

### FINAL_01_CHAIN_COMMANDER_DEATH
**Given** current admitted ChainTraversal has remaining eligible slots.  
**When** one feedback step kills enemy commander.  
**Then** transition through victory latch/draining state, complete current Chain traversal, then Finalize; do not admit unrelated future work.

### FINAL_02_COUNTER_SIBLING
**Given** `CounterBatch=[C1,C2]` was admitted and C1 kills commander original attacker.  
**When** victory latches.  
**Then** C2 remains admitted, executes zero-loss terminal semantics, batch drains, then BattleFinalized.

### FINAL_03_COMBO_BATTLE_END
**Given** NormalAttack #1 satisfies battle victory condition before Combo #2 admission.  
**When** lifecycle reaches Combo future-branch boundary.  
**Then** victory latch blocks #2 admission; no new target resolution/#2 is created; battle finalizes after already-admitted local work is drained.

### FINAL_04_CLEAVE_COMMANDER_SECONDARY
**Given** current `CleaveEffect` has an admitted ordered secondary plan and one secondary step kills enemy commander while later secondaries in that same effect remain planned.  
**When** victory latches.  
**Then** current admitted effect drains its remaining locally legal planned secondaries; an unadmitted later independent CleaveEffect is a FutureBranch and is not admitted; finalization follows local drain.

### FINAL_05_SHARE_COMMANDER_TARGET
**Given** a Share target is commander and target-first `Dtarget` commit is lethal while sharer work is pending.  
**When** commander dies.  
**Then** Share's local `TARGET_DEATH_INTERRUPT` discards pending sharer loss; victory latches; finalization occurs after the Share micro-transaction reaches its local terminal state.

### FINAL_06_DISTRIBUTION_COMMANDER_PARTICIPANT
**Given** commander is a planned Distribution participant and dies before later planned transaction steps.  
**When** victory latches.  
**Then** apply `PROJECT_RUNTIME_DEFAULT (NOT EMPIRICALLY PROVEN GAME RULE)`: drain the already-admitted fixed plan without repartition, then cross the Finalization Barrier.

## I. Integerization — 5 explicit vectors

### REG-INT-01 — Chain uses FLOOR
**Given** `TriggerNodeResolvedDamage=396`, `ChainRatio=28.28%`.  
**When** Chain value is integerized.  
**Then** `396×0.2828=111.9888 → 111`.

### REG-INT-02 — Share uses ROUND_HALF_UP
**Given** `Dtotal=470`, `R=15%`.  
**When** Share partitions.  
**Then** `470×0.15=70.5 → Dsharer_theoretical=71`, `Dtarget=399`.

### REG-INT-03 — Distribution target uses ROUND_HALF_UP
**Given** `Dtotal=251`, `R=50%`.  
**When** Distribution computes target share.  
**Then** `251×0.5=125.5 → Dtarget=126`, `Dtransfer=125`.

### REG-INT-04 — Distribution participant uses ROUND_HALF_UP
**Given** `Dtransfer=353`, `N=2`.  
**When** participant amount is computed.  
**Then** `353/2=176.5 → Dparticipant=177` for each planned participant; no last-participant remainder repair is added.

### REG-INT-05 — Cleave uses FLOOR
**Given** `ActualTargetTroopLoss=55`, `CleaveRatio=54%`.  
**When** Cleave derives calculated damage.  
**Then** `55×0.54=29.7 → 29`.

---

## Regression gate

```text
Target Arbitration contracts = 7
Combo contracts              = 5
Cleave contracts             = 5
Chain contracts              = 4
Share contracts              = 4
Distribution contracts       = 4
Counter contracts            = 5
Finalization contracts       = 6
Integerization contracts     = 5
--------------------------------
TOTAL                         = 45
```

No contract uses the host language's built-in `round()` as its oracle. Stage9 build may implement helpers, but expected vectors above are the authority.
