# Stage 9 Open Finding Consolidation

> Project: 三国志战略版战斗模拟器 V2  
> Scope: Stage 9 Contract Closure — OPEN Finding Consolidation + Narrow Re-freeze Plan  
> Status: `CONSOLIDATION COMPLETE / CONTRACT REPAIR NOT STARTED`  
> Boundary: 本文件只做汇总、去重、owner 判定、证据缺口判定、依赖排序与 narrow re-freeze 规划；不修改任何现有 Frozen P0。

---

## 1. Repository Baseline

本轮开始时重新读取两个远端 `main` exact HEAD：

```text
battle repository
lxy2005051020-commits/sgs-v2-battle-system
main = f8cb7c59de4ce51492915abc84247f677815ea6e
message = audit(stage9): verify counterattack frozen contract

state research repository
lxy2005051020-commits/sgs-state-mechanics-research
main = 9d86e54c407913ff020bafacf8196085780b99c6
message = docs(index): mark combo frozen and scope death baseline
```

提交前再次校验 battle `main` 仍为上述 SHA，目标文件此前不存在，因此本提交没有覆盖并发工作。

---

## 2. Nine-Audit Completion Status

九份独立 Frozen Contract Audit 均已从正文重新读取，不依赖聊天摘要。

| Mechanism | Audit Verdict | Blockers | Majors | Re-freeze Needed | Frozen Stable Core | Narrow Open Scope |
|---|---:|---:|---:|---|---|---|
| CONFUSION | REOPEN REQUIRED | 1 | 0 | YES, narrow only | selector legality、JIT target pool、TAUNT/GUARD target ownership | death intersection only；`CFS9-B01` 已被 Counter evidence 压窄 |
| TAUNT | PASS WITH DOC SYNC | 0 | 0 | NO P0 reopen | full TAUNT P0、selector override、lifecycle、per-hit JIT | docs + regression hardening |
| GUARD | PASS; DOC/HARDENING ONLY | 0 | 0 | NO P0 reopen | cover check、actualTarget lock、lifecycle | docs + typed target identity hardening |
| COMBO | REOPEN REQUIRED | 3 | 3 | YES | two-hit kernel、action-local latch concept、fresh target-resolution checkpoint | death-family scope、master lifecycle ownership、finalization、REMOVE/SUPPRESS、RNG wording |
| CLEAVE | REOPEN REQUIRED | 4 | 1 | YES | derived-damage identity、ratio relation、permission matrix | damage layer、state lifecycle、secondary queue、death/finalization、recovery basis |
| CHAIN_LINK | NARROW REOPEN REQUIRED | 1 | 0 | YES, numeric only | TRUE_FEEDBACK、traversal、owner/ratio binding、JIT、death traversal | integerization |
| DAMAGE_SHARE | REOPEN REQUIRED | 2 | 1 | YES | topology、target-first partition、post-partition Dtarget、attribution | integerization、lethal-target interrupt、outer death wording |
| DISTRIBUTION | REOPEN REQUIRED | 2 | 1 | YES | dynamic participants、participants-first、ordinary participant-death continuation | integerization、commander participant、outer death wording |
| COUNTERATTACK | PASS WITH DOC SYNC | 0 | 0 | NO P0 reopen | trigger identity、CounterBatch admission/execution、target-death siblings | docs + hardening |

Raw OPEN findings：

```text
BLOCKER   = 13
MAJOR     = 6
MINOR     = 1
DOC_DRIFT = 29
HARDENING = 11
TOTAL     = 60
```

真正影响 Stage9 P0 / architecture 的 `BLOCKER + MAJOR = 19`。`finding count != root-cause count`。

---

## 3. Master Open Finding Ledger

分类：

```text
A = TRUE P0 CONTRADICTION
B = P0 OVER-GENERALIZATION
C = MISSING P0 SEMANTIC
D = IMPLEMENTATION CONTRACT HARDENING
E = DOCUMENTATION DRIFT
```

`A+B` 表示过度泛化已经造成同上下文 P0 对撞；`A→NARROWED` 表示保留历史 finding ID，但最新高优先级证据已经消灭其中一个子场景。

| Finding ID | Mechanism | Severity | Current Status | Class | Symptom | Root Cause Candidate | P0 Owner | Other Affected P0 | Evidence State | Research Needed | Contract Edit Needed | Architecture Impact | Dependency | Repair Package | Closure Proof |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CFS9-B01 | CONFUSION | BLOCKER | NARROWED | A→NARROWED | universal target-death abort vs COMBO death exception；Counter-kill 已证明不会到 #2 | execution-right/death scope | COMBO/shared owner first；CONFUSION only if residual target-selection case survives | COMBO/Core | conflicting | CONDITIONAL | CONDITIONAL | HIGH | RF-P03 | RF-P03 | Counter-kill removed；only non-Counter death + independently proven fresh target selection may remain |
| CFS9-D01 | CONFUSION | DOC_DRIFT | DOC_ONLY | E | Core README still marks CONFUSION/COMBO pending | docs drift | DOC | none | sufficient | NO | NO | LOW | P0 re-freezes | RF-C02 | README synced |
| CFS9-D02 | CONFUSION | DOC_DRIFT | DOC_ONLY | E | Evidence Matrix still historical | docs drift | DOC | none | sufficient | NO | NO | LOW | P0 re-freezes | RF-C02 | matrix synced |
| CFS9-D03 | CONFUSION | DOC_DRIFT | DOC_ONLY | E | state root README death/research baseline stale | docs drift | DOC | death owner | sufficient | NO | NO | LOW | RF-P03/P04 | RF-C02 | README scoped death wording |
| CFS9-D04 | CONFUSION | DOC_DRIFT | DOC_ONLY | E | battle repo lacks current COMBO mirror/navigation | docs drift | DOC | COMBO | sufficient | NO | NO | LOW | COMBO re-freeze | RF-C02 | mirror/navigation synced |
| TAS9-D01 | TAUNT | DOC_DRIFT | DOC_ONLY | E | state index still MINIMUM_USABLE | docs drift | DOC | none | sufficient | NO | NO | LOW | final re-freeze | RF-C02 | index synced |
| TAS9-D02 | TAUNT | DOC_DRIFT | DOC_ONLY | E | Core README current-state/death wording stale | docs drift | DOC | CONFUSION/COMBO | sufficient | NO | NO | LOW | RF-P03/P04 | RF-C02 | README synced |
| TAS9-D03 | TAUNT | DOC_DRIFT | DOC_ONLY | E | Evidence Matrix historical rather than current status | docs drift | DOC | none | sufficient | NO | NO | LOW | final re-freeze | RF-C02 | matrix synced |
| TAS9-D04 | TAUNT | DOC_DRIFT | DOC_ONLY | E | lower-authority death docs unsynchronized | docs drift | DOC | COMBO/Counter | sufficient | NO | NO | LOW | RF-P03/P04 | RF-C02 | death docs synced |
| TAS9-H01 | TAUNT | HARDENING | OPEN | D | missing open-action-death TAUNT regression | runtime hardening | tests/runtime | execution owner | sufficient | NO | NO | LOW | RF-P03 | RF-C01 | regression added without TAUNT-specific death rule |
| GDS9-D01 | GUARD | DOC_DRIFT | DOC_ONLY | E | Core README stale | docs drift | DOC | none | sufficient | NO | NO | LOW | RF-P03/P04 | RF-C02 | synced |
| GDS9-D02 | GUARD | DOC_DRIFT | DOC_ONLY | E | Evidence Matrix stale | docs drift | DOC | none | sufficient | NO | NO | LOW | final re-freeze | RF-C02 | synced |
| GDS9-D03 | GUARD | DOC_DRIFT | DOC_ONLY | E | state root README stale | docs drift | DOC | death owner | sufficient | NO | NO | LOW | RF-P03/P04 | RF-C02 | synced |
| GDS9-D04 | GUARD | DOC_DRIFT | DOC_ONLY | E | R2 self-guard terminology ambiguous/historical | docs drift | DOC | target arbitration | sufficient | NO | NO | LOW | none | RF-C02 | terminology normalized |
| GDS9-H01 | GUARD | HARDENING | OPEN | D | enforce atomic Target Resolution + typed target identities | runtime hardening | Core/runtime | CONFUSION/TAUNT | sufficient | NO | NO | MEDIUM | stable target core | RF-C01 | typed target invariants tested |
| CBS9-B01 | COMBO | BLOCKER | OPEN | A+B | own-open-action ANY-death continuation contradicts Counter Q05 | death over-generalization | COMBO | Counter/Core | conflicting | YES only for residual reachable non-Counter families | YES | HIGH | RF-P02→P03 | RF-P03 | Counter-kill PROVEN ABORT；all families explicitly classified |
| CBS9-B02 | COMBO | BLOCKER | OPEN | A | COMBO §5 owns inner lifecycle and puts Assault before Counter | duplicated lifecycle ownership | Core owns master；COMBO owns checkpoint | Counter/Cleave/Chain | sufficient | NO | YES | HIGH | none | RF-P02 | COMBO delegates inner order；Counter before Assault/Combo |
| CBS9-B03 | COMBO | BLOCKER | OPEN | A | victory/no-target ordering conflicts Q46/R5 | finalization boundary | shared Finalization + COMBO consumer | R5/Core | conflicting | NO for known Q46；YES for shared barrier completion | YES | HIGH | RF-P03/P05/P04 | RF-P04 | battle-open no-target separated from VictoryConditionSatisfied |
| CBS9-M01 | COMBO | MAJOR | OPEN | D | ActionStart latch before expiry maintenance | latch ordering | COMBO | lifecycle | sufficient | NO | YES | MEDIUM | none | RF-P02 | maintenance before latch |
| CBS9-M02 | COMBO | MAJOR | OPEN | D | latch lacks physical REMOVE invalidation | exists/operational/granted distinction | COMBO | execution owner | sufficient | NO | YES | HIGH | none | RF-P02 | REMOVE cancels；SUPPRESS not physical removal |
| CBS9-M03 | COMBO | MAJOR | OPEN | B | exact uniform iid/PRNG over-frozen | targeting over-generalization | COMBO wording | R7/RandomSystem | sufficient | NO | YES | MEDIUM | none | RF-P02 | only fresh live target resolution frozen |
| CBS9-D01 | COMBO | DOC_DRIFT | DOC_ONLY | E | no battle-repo COMBO P0 mirror | docs drift | DOC | COMBO | sufficient | NO | NO | LOW | COMBO re-freeze | RF-C02 | mirror synced |
| CBS9-D02 | COMBO | DOC_DRIFT | DOC_ONLY | E | Stage9/Core README/Evidence Matrix pending/omit COMBO | docs drift | DOC | none | sufficient | NO | NO | LOW | COMBO re-freeze | RF-C02 | nav synced |
| CBS9-D03 | COMBO | DOC_DRIFT | DOC_ONLY | E | state README/index death baseline unsynchronized | docs drift | DOC | death owner | sufficient | NO | NO | LOW | RF-P03/P04 | RF-C02 | synced |
| CBS9-H01 | COMBO | HARDENING | OPEN | D | generic `if actor.dead:return` also wrong | operation-scope hardening | shared execution runtime | Counter/Chain/partitions | sufficient | NO | NO | MEDIUM | RF-P03 | RF-C01 | runtime uses scope/admission rights |
| CLVS9-B01 | CLEAVE | BLOCKER | OPEN | C | MainAttackFinalDamage ambiguous: Dtotal/Dtarget/actual/credited | missing damage-layer semantic | CLEAVE | Share/Distribution | missing | YES | YES | HIGH | RF-P06 | RF-P06 | controlled partition/overkill slices identify one layer |
| CLVS9-B02 | CLEAVE | BLOCKER | OPEN | C | full state lifecycle/multi-source P0 missing | missing state-container semantic | CLEAVE | R6 historical only | missing | YES | YES | HIGH | none | RF-P07 | apply/reapply/duration/source/multi-source unique |
| CLVS9-B03 | CLEAVE | BLOCKER | OPEN | C | secondary target set/count/order/JIT not P0-frozen | missing target-queue semantic | CLEAVE | Core target orchestration | missing | YES | YES | HIGH | none | RF-P07 | ordered queue + revalidation uniquely specified |
| CLVS9-B04 | CLEAVE | BLOCKER | OPEN | C | pending Cleave across death/finalization not frozen | missing death/finalization semantic | CLEAVE + shared Finalization | R5/execution | missing | YES | YES | HIGH | RF-P03/P06/P07/P05 | RF-P04 | controlled death slices define admitted completion/finalization |
| CLVS9-M01 | CLEAVE | MAJOR | OPEN | C | recovery basis after Cleave→Distribution outside frozen recovery P0 | missing consumer layer semantic | recovery 690094/690095 | Share/Distribution | missing | CONDITIONAL | YES | MEDIUM | CLVS9-B01 | RF-P06 | recovery uses explicit post-partition fact |
| CLVS9-D01 | CLEAVE | DOC_DRIFT | DOC_ONLY | E | Barrier term should normalize to 690083 RESISTANCE | docs drift | DOC | RESISTANCE | sufficient | NO | NO | LOW | none | RF-C02 | normalized |
| CLVS9-D02 | CLEAVE | DOC_DRIFT | DOC_ONLY | E | Evidence Matrix stale | docs drift | DOC | none | sufficient | NO | NO | LOW | final re-freeze | RF-C02 | synced |
| CLVS9-D03 | CLEAVE | DOC_DRIFT | DOC_ONLY | E | minimum-usable doc superseded by core P0 | docs drift | DOC | CLEAVE | sufficient | NO | NO | LOW | CLEAVE re-freeze | RF-C02 | superseded nav clear |
| CLVS9-D04 | CLEAVE | DOC_DRIFT | DOC_ONLY | E | state root README stale | docs drift | DOC | death owner | sufficient | NO | NO | LOW | RF-P03/P04 | RF-C02 | synced |
| CLVS9-H01 | CLEAVE | HARDENING | OPEN | D | typed DerivedDamage identity/provenance/permission policy | runtime hardening | Stage9 derived runtime | Chain/R8 | sufficient | NO | NO | MEDIUM | RF-P06 | RF-C01 | typed permission tests |
| CHNS9-B01 | CHAIN_LINK | BLOCKER | OPEN | C | Chain ratio multiplication integerization undefined | missing numeric semantic | CHAIN or proven shared policy | Share/Distribution | missing | YES | YES | MEDIUM | RF-P01 | RF-P01 | direct x.5 evidence + explicit rule |
| CHNS9-D01 | CHAIN_LINK | DOC_DRIFT | DOC_ONLY | E | minimum skeleton still marks frozen fields unresolved | docs drift | DOC | Chain | sufficient | NO | NO | LOW | Chain re-freeze | RF-C02 | nav synced |
| CHNS9-D02 | CHAIN_LINK | DOC_DRIFT | DOC_ONLY | E | R4 missing Distribution participant loss→Chain BLOCKED | docs drift | DOC | Distribution | sufficient | NO | NO | LOW | none | RF-C02 | R4 synced |
| CHNS9-D03 | CHAIN_LINK | DOC_DRIFT | DOC_ONLY | E | Evidence Matrix footer stale | docs drift | DOC | Share/Counter | sufficient | NO | NO | LOW | final re-freeze | RF-C02 | footer synced |
| CHNS9-H01 | CHAIN_LINK | HARDENING | OPEN | D | typed one-pass slot traversal + restricted settlement | runtime hardening | Chain runtime | derived runtime | sufficient | NO | NO | MEDIUM | RF-P01 numeric expectation | RF-C01 | traversal/settlement regressions |
| SHS9-B01 | DAMAGE_SHARE | BLOCKER | OPEN | C | `round(Dtotal×R)` .5 tie undefined | missing numeric semantic | Share or proven shared policy | Distribution/Chain | missing | YES | YES | MEDIUM | RF-P01 | RF-P01 | direct x.5 rule + regressions |
| SHS9-B02 | DAMAGE_SHARE | BLOCKER | OPEN | C | TARGET_DEATH_INTERRUPT lacks controlled direct evidence；extractor biased | missing partition-death semantic | Share | execution/finalization | missing | YES | YES | HIGH | RF-P03；avoid tie samples or consume P01 | RF-P05 | lethal target controlled sample decides pending sharer |
| SHS9-M01 | DAMAGE_SHARE | MAJOR | OPEN | B | protected-target death clause over-owns outer Action | death over-generalization | Share branch only；outer shared | R5/Core | sufficient | NO | YES | HIGH | RF-P03 | RF-P03 | contract stops at transaction scope |
| SHS9-N01 | DAMAGE_SHARE | MINOR | OPEN | D | replacement should forbid resurrection of replaced Distribution | hardening | Share/Distribution wording | Distribution | sufficient | NO | YES | LOW | none | RF-C01 | replace is terminal for old effective instance |
| SHS9-D01 | DAMAGE_SHARE | DOC_DRIFT | DOC_ONLY | E | Evidence Matrix still says Share next research / death unfrozen | docs drift | DOC | Share | sufficient | NO | NO | LOW | Share re-freeze | RF-C02 | synced |
| SHS9-D02 | DAMAGE_SHARE | DOC_DRIFT | DOC_ONLY | E | state root README unconditional death hard-stop | docs drift | DOC | execution owner | sufficient | NO | NO | LOW | RF-P03/P04 | RF-C02 | scoped wording |
| SHS9-H01 | DAMAGE_SHARE | HARDENING | OPEN | D | one effective DamagePartitionResolver | runtime hardening | partition runtime | Distribution | sufficient | NO | NO | MEDIUM | RF-P05 | RF-C01 | exactly one partition policy |
| SHS9-H02 | DAMAGE_SHARE | HARDENING | OPEN | D | typed attributed direct-troop-loss provenance | runtime hardening | provenance runtime | R8/Distribution | sufficient | NO | NO | MEDIUM | none | RF-C01 | attacker/skill/victim/credit distinct |
| DSTS9-B01 | DISTRIBUTION | BLOCKER | OPEN | C | both round sites have undefined x.5 and shared/separate policy unknown | missing numeric semantic | Distribution or proven shared policy | Share/Chain | missing | YES | YES | MEDIUM | RF-P01 | RF-P01 | both call sites frozen explicitly |
| DSTS9-B02 | DISTRIBUTION | BLOCKER | OPEN | C | commander participant #1 death continuation/finalization unproven | missing transaction/finalization semantic | Distribution commits + shared Finalization | R5/Core | missing | YES | YES | HIGH | RF-P03；P04 consumes | RF-P05 | controlled commander participant sample |
| DSTS9-M01 | DISTRIBUTION | MAJOR | OPEN | B | protected-target death over-owns outer Action | death over-generalization | Distribution branch only；outer shared | R5/Core | sufficient | NO | YES | HIGH | RF-P03 | RF-P03 | outer termination delegated |
| DSTS9-D01 | DISTRIBUTION | DOC_DRIFT | DOC_ONLY | E | state repo still MINIMUM_USABLE/skeleton | docs drift | DOC | Distribution | sufficient | NO | NO | LOW | Distribution re-freeze | RF-C02 | synced |
| DSTS9-D02 | DISTRIBUTION | DOC_DRIFT | DOC_ONLY | E | Evidence Matrix not post-freeze synchronized | docs drift | DOC | Distribution | sufficient | NO | NO | LOW | Distribution re-freeze | RF-C02 | synced |
| DSTS9-H01 | DISTRIBUTION | HARDENING | OPEN | D | fixed transaction plan and JIT slot gate must be separate | runtime hardening | Distribution runtime | partition | sufficient | NO | NO | MEDIUM | RF-P05 | RF-C01 | no mid-transaction N recompute |
| CTS9-D01 | COUNTERATTACK | DOC_DRIFT | DOC_ONLY | E | state index still MINIMUM_USABLE | docs drift | DOC | Counter | sufficient | NO | NO | LOW | final re-freeze | RF-C02 | synced |
| CTS9-D02 | COUNTERATTACK | DOC_DRIFT | DOC_ONLY | E | minimum skeleton accuracy-deferred without superseded nav | docs drift | DOC | Counter | sufficient | NO | NO | LOW | none | RF-C02 | points to authoritative P0 |
| CTS9-D03 | COUNTERATTACK | DOC_DRIFT | DOC_ONLY | E | state death baseline stale around Counter-kill vs COMBO | docs drift | DOC | COMBO/execution | sufficient | NO | NO | LOW | RF-P03/P04 | RF-C02 | synced |
| CTS9-H01 | COUNTERATTACK | HARDENING | OPEN | D | trigger-time admission != execution-time owner liveness | runtime hardening | Counter/shared execution | COMBO | sufficient | NO | NO | MEDIUM | RF-P03 | RF-C01 | owner-death regression distinct from target-death continuation |
| CTS9-H02 | COUNTERATTACK | HARDENING | OPEN | D | commander attacker killed by C1 with C2 queued regression | finalization hardening | Counter tests/shared finalization | R5 | sufficient model；commander-controlled Q07 sample absent | NO | NO | MEDIUM | RF-P04 | RF-C01 | admitted C2 zero-loss then finalization, or contradiction reopened |
| CTS9-H03 | COUNTERATTACK | HARDENING | OPEN | D | zero-loss sibling must not run full weapon pipeline on dead target | runtime hardening | Counter runtime | Damage pipeline | sufficient | NO | NO | LOW | none | RF-C01 | CounterExecute + attributed zero-loss path tested |

---

## 4. Finding Classification

```text
A / A+B / A→NARROWED
- CFS9-B01
- CBS9-B01
- CBS9-B02
- CBS9-B03

B
- CBS9-M03
- SHS9-M01
- DSTS9-M01

C
- CLVS9-B01
- CLVS9-B02
- CLVS9-B03
- CLVS9-B04
- CLVS9-M01
- CHNS9-B01
- SHS9-B01
- SHS9-B02
- DSTS9-B01
- DSTS9-B02

D
- CBS9-M01
- CBS9-M02
- SHS9-N01
- all 11 HARDENING findings

E
- all 29 DOC_DRIFT findings
```

DOC_DRIFT 不进入 P0 blocker 队列；HARDENING 不自动升级为研究；多个 `round()` 只先共享研究问题，不能先验共享答案。

---

## 5. Root-Cause Deduplication

| Root Cause | Primary Findings | Mechanisms | Evidence Needed | Primary Package | Priority |
|---|---|---|---|---|---|
| Integerization semantics | CHNS9-B01, SHS9-B01, DSTS9-B01 | Chain, Share, Distribution | direct `.5` boundaries | RF-P01 | P0 |
| NormalAttack lifecycle / COMBO ownership | CBS9-B02, CBS9-M01, CBS9-M02, CBS9-M03 | Combo + Orchestrator | existing P0 sufficient | RF-P02 | P0 |
| Execution-right / operation-scoped death | CFS9-B01, CBS9-B01, SHS9-M01, DSTS9-M01 | Confusion, Combo, Share, Distribution | Counter sufficient；residual death families conditional | RF-P03 | P0 |
| Battle-finalization barrier | CBS9-B03, CLVS9-B04；consumes DSTS9-B02/CTS9-H02 | Combo, Cleave, Distribution, Counter | controlled commander/death boundaries | RF-P04 | P0 |
| Ordered partition-transaction death | SHS9-B02, DSTS9-B02 | Share, Distribution | two distinct controlled scenarios | RF-P05 | P0 |
| Cleave damage layer / recovery | CLVS9-B01, CLVS9-M01 | Cleave + recovery | partition/overkill slices | RF-P06 | P0/P1 |
| Cleave state + secondary targets | CLVS9-B02, CLVS9-B03 | Cleave | Cleave-specific evidence | RF-P07 | P0 |
| Implementation hardening | SHS9-N01 + 11 H | cross-mechanism | no battle research | RF-C01 | P2 |
| Documentation drift | 29 D | docs | no game research | RF-C02 | P3 |

```text
Deduplicated root-cause package count = 9
```

### Target Arbitration Ready

```text
TARGET ARBITRATION ROOT PACKAGE = READY

CONFUSION → selector legality
TAUNT     → intended-target override
GUARD     → post-selection actual target redirect

pre_redirect_target
post_redirect_attack_target
damage_recipient(s)
```

Death blockers elsewhere不重开 Target Arbitration。

---

## 6. Integerization Root Package

```text
CHNS9-B01:
ChainCalculatedDamage = TriggerNodeResolvedDamage × Ratio
→ integerization undefined

SHS9-B01:
Dsharer = round(Dtotal × R)
→ .5 tie undefined

DSTS9-B01:
Dtarget = round(Dtotal × (1-R))
Dparticipant = round(Dtransfer / N)
→ both .5 ties undefined
```

Stage8 only freezes numeric validation boundaries, not tie-breaking or a global integerization algorithm.

```text
Unified research question = YES
Unified numeric answer     = NOT YET PROVEN
Shared Integerization P0   = CONDITIONAL, NOT YET AUTHORIZED
```

Required evidence：exact `x.5`, adjacent below/above `.5`, low values, and one-point lethal boundaries where possible. `100.5` must actually be observed as `100` or `101`; non-tie samples cannot freeze a tie rule.

Cleave ratio multiplication has no standalone rounding finding. It is an explicit sub-check under `CLVS9-B01 / RF-P06`, not silently merged into RF-P01 before its damage base is known.

---

## 7. Execution Ownership / Death Root Package

Conceptual scopes：

```text
CURRENT_MICROSTEP
CURRENT_DAMAGE_INSTANCE
CURRENT_PARTITION_TRANSACTION
CURRENT_REACTION
ALREADY_ADMITTED_REACTION_BATCH
CURRENT_NORMAL_ATTACK_INSTANCE
CURRENT_ACTION
NOT_YET_DISPATCHED_FUTURE_BRANCH
BATTLE_FINALIZATION
```

Counter anchor：

```text
CounterBatch = [C1, C2]
C1 kills attacker
C2 already admitted → still executes, troop loss = 0
Assault not started → cancelled
Combo #2 not dispatched → cancelled
```

Thus：

```text
already-admitted reaction right
!=
not-yet-created future owner branch
```

Lifecycle dimensions must remain independent：

```text
physical state exists
state operational
action-local eligibility already granted
reaction-batch admission already granted
entity alive
future scheduling eligibility
```

### COMBO death-family matrix

| Death Family | Current Status | Disposition |
|---|---|---|
| Counter-kill | PROVEN ABORT | Counter Q05/Q07；future Assault/Combo cancelled |
| Reflect / recoil | UNRESOLVED | no same-context direct P0 evidence |
| Self-cost | NOT APPLICABLE unless reachable；otherwise UNRESOLVED | do not invent reachability |
| Periodic / delayed | UNRESOLVED | research only if reachable before checkpoint |
| Reaction damage | Counter = PROVEN ABORT；other reactions UNRESOLVED | split by identity |
| Other passive damage | UNRESOLVED | no universal inference |
| Commander collateral | UNRESOLVED / finalization-owned | death != finalization |

No non-Counter family is `PROVEN CONTINUE` merely because old COMBO said ANY death.

### CFS9-B01 disposition tree

```text
repair COMBO death-family scope
↓
non-Counter death family
AND dead actor independently proven to reach fresh #2 Target Selection?

NO → CLOSE CFS9-B01 without changing CONFUSION operational semantics
YES → research only that exact family × target-selection intersection
```

Counter-kill is no longer a live CFS9-B01 subcase.

---

## 8. Battle Finalization Root Package

Must distinguish：

```text
UnitDeathFact
VictoryConditionSatisfied
CommanderDeathDetected
CurrentOperationCompletion
FutureBranchCancellation
BattleFinalization
```

Anchors：

```text
CHAIN commander death mid traversal
→ finish current traversal
→ finalization later

COUNTER target death after batch admission
→ admitted siblings continue
→ future attacker branch cancels
→ finalization outside current admitted reaction
```

Unresolved：Distribution commander participant；Cleave pending work across death.

Recommendation：future small shared `STAGE9_BATTLE_FINALIZATION_CONTRACT.md` (or equivalent) owns victory detection/finalization barrier/commander collateral ordering only, without copying mechanism traversals.

---

## 9. Damage-Layer / Cleave Root Package

| Term | Meaning |
|---|---|
| `Dtotal` | normal theoretical final amount before Share/Distribution partition |
| `Dtarget` | post-partition target assigned amount before troop clamp |
| `DerivedCalculatedDamage` | provenance-specific theoretical derived amount before troop clamp |
| `AssignedDamage` | amount assigned to one recipient before troop clamp |
| `ActualCommittedTroopLoss` | actual troop mutation |
| `CreditedDamage` | amount attributed to credit owner according to mechanism P0 |
| `MainAttackFinalDamage` | UNRESOLVED Cleave term；CLVS9-B01 |

Numeric matrix：

| Site | Formula | Integerization | Finding |
|---|---|---|---|
| Chain | `TriggerNodeResolvedDamage × Ratio` | undefined | CHNS9-B01 |
| Share Dsharer | `round(Dtotal × R)` | `.5` undefined | SHS9-B01 |
| Distribution Dtarget | `round(Dtotal × (1-R))` | `.5` undefined | DSTS9-B01 |
| Distribution Dparticipant | `round(Dtransfer/N)` | `.5` undefined；shared policy not assumed | DSTS9-B01 |
| Cleave | `MainAttackFinalDamage × CleaveRatio` | not explicitly frozen | CLVS9-B01 sub-check |

`CLVS9-B01` must discriminate `Dtotal / Dtarget / ActualCommittedTroopLoss / CreditedDamage` using Share, Distribution, overkill and no-partition controls.

`CLVS9-M01` is likely contract integration after B01 because Share/Distribution already separate post-partition target DamageEvent from participant direct loss. Only run recovery-specific research if 690094/690095 remain ambiguous after layer mapping.

---

## 10. State Lifecycle / Container Root Package

Cleave is the only audited mechanism with blocker-level state-container incompleteness. TAUNT/GUARD/COMBO/CHAIN/SHARE/DISTRIBUTION/COUNTER already freeze their relevant container/lifecycle models.

```text
global FunctionalStateContainerContract = NOT JUSTIFIED NOW
```

Repair `CLVS9-B02` in Cleave P0. Do not create a global project because one mechanism is incomplete.

---

## 11. Mechanism-Specific Remaining Gaps

```text
CONFUSION
- narrowed death intersection only

COMBO
- death-family scope
- lifecycle master ownership
- finalization/no-target distinction
- maintenance-before-latch
- REMOVE vs SUPPRESS vs granted eligibility
- exact-uniform PRNG overclaim

CLEAVE
- MainAttackFinalDamage layer
- state lifecycle/multi-source
- secondary target queue/order/revalidation
- pending work across death/finalization
- recovery basis after layer map
- integerization sub-check after base known

CHAIN
- integerization only

SHARE
- integerization
- lethal target → pending sharer?
- outer Action wording

DISTRIBUTION
- two integerization sites
- commander participant death/finalization
- outer Action wording

TAUNT/GUARD/COUNTER
- no P0 reopen；hardening/docs only
```

---

## 12. Documentation Drift Package

```text
RF-C02 DOC_SYNC_PACKAGE

CFS9-D01..D04
TAS9-D01..D04
GDS9-D01..D04
CBS9-D01..D03
CLVS9-D01..D04
CHNS9-D01..D03
SHS9-D01..D02
DSTS9-D01..D02
CTS9-D01..D03
```

Always：`P0 re-freeze → hardening → docs sync LAST`。

---

## 13. P0 Ownership Map

| Semantic | Primary Owner | Mechanism responsibility |
|---|---|---|
| Target selector legality | Core + CONFUSION | selector branch only |
| intended target override | TAUNT | override eligibility |
| actual-target redirect | GUARD | cover check/actualTarget lock |
| NormalAttack master lifecycle | Core Arbitration / Orchestrator | mechanisms own insertion/checkpoint only |
| Counter insertion/batch | Counter P0 | trigger/admission/execution |
| Combo checkpoint/latch | Combo P0 | #2 admission, not #1 inner order |
| Cleave branch | Cleave P0 | state/secondary/derived semantics |
| Chain traversal | Chain P0 | traversal/JIT/TRUE_FEEDBACK |
| Share partition | Share P0 | target-first transaction |
| Distribution partition | Distribution P0 | participants-first transaction |
| execution rights | proposed shared Execution Ownership P0 | admitted scopes/future scheduling |
| battle finalization | proposed shared Finalization P0 | victory/finalization barrier |
| integerization | shared only if evidence proves common policy | otherwise mechanism-local |

---

## 14. Dependency Graph

```text
RF-P02 LIFECYCLE OWNERSHIP
    ↓
RF-P03 EXECUTION_RIGHT/DEATH
    ├──────────────┐
    ↓              ↓
RF-P05 PARTITION_TRANSACTION_DEATH
                   │
RF-P06 CLEAVE_DAMAGE_LAYER
    ↓              │
RF-P07 CLEAVE_STATE/TARGET
    └──────┬───────┘
           ↓
RF-P04 BATTLE_FINALIZATION
           ↓
RF-C01 HARDENING
           ↓
RF-C02 DOC_SYNC
```

RF-P01 INTEGERIZATION is an early parallel evidence track and feeds exact regression expectations. Lethal/commander samples may be collected before it finishes if chosen away from ambiguous `.5` boundaries.

---

## 15. Narrow Re-freeze Packages

### RF-P01 — STAGE9_INTEGERIZATION_POLICY

```text
Level: A
Priority: P0
Affected: CHNS9-B01, SHS9-B01, DSTS9-B01
Primary owner: mechanism-local unless common policy proven
Need new extractor: YES
```

Required slices：Chain x.5；Share Dsharer x.5；Distribution Dtarget x.5；Distribution Dparticipant x.5；adjacent non-ties；lethal one-point boundaries where possible.

Expected evidence：report/event span, mechanism, call-site, inputs, theoretical value, fractional part, observed integer, confounders, candidate policies eliminated.

Allowed future edits：relevant numeric P0/evidence/regression spec；shared Integerization P0 only after common behavior is proven. Forbidden：Stage8/unrelated P0/production before re-freeze/docs in semantic commit.

Closure：every call-site has explicit executable integer rule；no programming-language built-in is semantic authority.

---

### RF-P02 — NORMAL_ATTACK_LIFECYCLE_AND_COMBO_CONTRACT_REPAIR

```text
Level: B
Priority: P0
Affected: CBS9-B02, CBS9-M01, CBS9-M02, CBS9-M03
Need new extractor: NO
```

Existing Counter/Core/R1/Q10/Q41/R7 evidence is sufficient.

```text
Core owns:
main damage → Cleave/Chain → CounterBatch → Assault → Combo checkpoint

COMBO owns:
ActionStart maintenance/latch
physical REMOVE invalidation
checkpoint admission
fresh #2 target resolution
```

Remove exact uniform-iid/PRNG claim. Regression：Counter before Assault/Combo；maintenance before latch；REMOVE vs SUPPRESS；fresh target resolution.

This is the **first actual Frozen Contract repair package** after consolidation.

---

### RF-P03 — EXECUTION_RIGHT_AND_DEATH_SCOPE

```text
Level: A
Priority: P0
Affected: CFS9-B01, CBS9-B01, SHS9-M01, DSTS9-M01
Need new extractor: CONDITIONAL YES
Depends on: RF-P02
```

Do not re-research Counter-kill. Research only reachable non-Counter families still necessary after deleting the universal rule. Every family must become exactly `PROVEN CONTINUE / PROVEN ABORT / UNRESOLVED / NOT APPLICABLE`.

Allowed future edits：COMBO P0；Share/Distribution outer death wording；optional small shared Execution Ownership P0；CONFUSION only if residual fresh-selection case survives. Counter Q05/Q07 and Target Arbitration are forbidden to weaken.

Closure：no unqualified `ANY death` or `TARGET_DEATH → ABORT_REMAINING_ACTION` across unrelated scopes.

---

### RF-P04 — BATTLE_FINALIZATION_BARRIER

```text
Level: A
Priority: P0
Primary: CBS9-B03, CLVS9-B04
Secondary inputs: DSTS9-B02, CTS9-H02, Chain commander-death anchor
Need new extractor: YES for unresolved predicates
Depends on: RF-P03, P05, P06, P07
Blocks: Stage9 design admission
```

Decision matrix per operation：death fact；victory satisfied；current completion boundary；admitted siblings；future cancellation；commander collateral；finalization timing.

Allowed future edits：small shared Finalization P0 + narrow COMBO/CLEAVE/DISTRIBUTION consumer clauses. Stage8 and unrelated math remain forbidden.

---

### RF-P05 — PARTITION_TRANSACTION_DEATH

```text
Level: A
Priority: P0
Affected: SHS9-B02, DSTS9-B02
Need new extractor: YES, two separate predicates
Depends on: RF-P03
Blocks: RF-P04
```

Share predicate：state operational；`Dsharer>0`；Dtarget lethal；sharer alive；source valid；no replacement/suppression confounder；inspect to DamageEvent end. The old extractor requiring both target and sharer loss is biased and cannot prove cancellation.

Distribution predicate：participant #1 is commander；#1 dies；later participant exists；target exists；observe later participant, target, commander collateral and finalization. Do not infer from Chain.

Shared abstraction may describe ordered transaction rights, not one universal death outcome.

---

### RF-P06 — CLEAVE_DAMAGE_LAYER_AND_RECOVERY_BASIS

```text
Level: A
Priority: P0 for B01；P1 for M01
Affected: CLVS9-B01, CLVS9-M01
Need new extractor: YES for B01；CONDITIONAL for M01
```

Controlled cases：partitioned main hit；unpartitioned control；overkill；actual/credited amounts；recovery callback if needed. Decision candidates：`Dtotal / Dtarget / ActualCommittedTroopLoss / CreditedDamage`.

Closure：`MainAttackFinalDamage` maps to one formal layer；recovery consumers use explicit facts.

---

### RF-P07 — CLEAVE_STATE_AND_SECONDARY_TARGET_COMPLETION

```text
Level: A
Priority: P0
Affected: CLVS9-B02, CLVS9-B03
Need new extractor: YES, Cleave-specific
```

Required：same-source reapply；cross-source coexist/replace；duration；source death/suppression；multiple sources；secondary count/order；earlier-secondary world changes；live/dead revalidation.

Do not create global FunctionalStateContainerContract unless another mechanism independently needs it.

---

### RF-C01 — IMPLEMENTATION_HARDENING

```text
Level: C
Priority: P2
Affected:
SHS9-N01
TAS9-H01
GDS9-H01
CBS9-H01
CLVS9-H01
CHNS9-H01
SHS9-H01
SHS9-H02
DSTS9-H01
CTS9-H01
CTS9-H02
CTS9-H03
```

No new game research. Translate frozen semantics into typed runtime invariants/tests only after P0 re-freeze.

### RF-C02 — DOC_SYNC_PACKAGE

```text
Level: C
Priority: P3
Affected: all 29 DOC_DRIFT findings
```

No game research. Run last.

---

## 16. Recommended Repair Order

```text
1 RF-P02 contract-only lifecycle ownership
2 RF-P01 numeric boundary research/re-freeze
3 RF-P03 execution-right/death scope
4 RF-P06 Cleave damage layer
5 RF-P07 Cleave state + secondary queue
6 RF-P05 partition death research
7 RF-P04 finalization barrier
8 RF-C01 hardening
9 RF-C02 docs sync
```

RF-P01 evidence extraction may start in parallel immediately. First actual Frozen Contract edit remains RF-P02.

---

## 17. Required Research Tasks

```text
RF-P01
- Chain x.5
- Share x.5
- Distribution Dtarget x.5
- Distribution Dparticipant x.5
- Cleave numeric sub-check after base layer

RF-P03
- only reachable non-Counter COMBO death families still required by design

RF-P04
- Cleave death/finalization boundaries
- finalization synthesis using Distribution commander result

RF-P05
- Share lethal protected target before sharer commit
- Distribution commander participant #1 death

RF-P06
- Cleave MainAttackFinalDamage layer

RF-P07
- Cleave lifecycle/multi-source
- Cleave secondary queue/order/revalidation
```

No generic archaeology pass. Full-corpus scan is allowed only to locate a rare explicit predicate.

---

## 18. Contract-Only Repair Tasks

No new game research needed：

```text
CBS9-B02 → remove COMBO ownership of inner lifecycle
CBS9-M01 → maintenance before latch
CBS9-M02 → REMOVE invalidates pending latch；SUPPRESS distinct
CBS9-M03 → remove uniform-iid/PRNG overclaim
CBS9-B01 Counter-kill subcase → COMBO owner, direct evidence sufficient
CFS9-B01 Counter-kill narrowing → no #2 / no fresh target selection
SHS9-M01 → Share owns transaction branch, not whole Action
DSTS9-M01 → Distribution owns transaction branch, not whole Action
CBS9-B03 known Q46 branch → victory-satisfied path cannot create pending Combo
```

`CLVS9-M01` likely becomes contract-only after CLVS9-B01 unless recovery contracts remain ambiguous.

---

## 19. Regression / Closure Requirements

### Death Semantics Matrix

| Scenario | Current operation continues? | Already-admitted siblings continue? | Future owner branch? | State cleanup relation | Victory/finalization | Authority | Finding |
|---|---|---|---|---|---|---|---|
| attacker dies from Counter | current Counter completes | admitted Counter siblings YES | Assault/Combo NO | cleanup separate from admission | commander finalization after admitted boundary | Counter Q05/Q07 + R5 | CBS9-B01/CFS9-B01 |
| Counter target dies, sibling queued | C1 completes | YES；later Ci zero-loss | target future NO | target death does not revoke batch | after admitted reaction | Q07 | CTS9-H02 |
| Counter owner dies before queued sibling | cause completes | not-yet-started owner-owned Ci NO | NO | owner liveness execution gate | operation-specific | holder-death + R5 | CTS9-H01 |
| Chain deputy dies | current target completes | remaining traversal YES | deputy future NO | normal cleanup | no commander finalization | Chain P0 | stable |
| Chain commander dies | current target completes | remaining traversal YES | unrelated future NO | death now/finalization later | traversal then finalization | Chain + R5 | RF-P04 anchor |
| Share protected target dies | target commit completes | pending sharer UNRESOLVED | outer delegated | cleanup cannot prove pending commit | commander depends transaction answer | Share audit | SHS9-B02 |
| Distribution non-commander participant dies | commit completes | later participants YES | target YES | next DamageEvent re-evaluates | no commander victory | Distribution P0 | stable |
| Distribution commander participant dies | commit completes | UNRESOLVED | target UNRESOLVED | separate from admission | UNRESOLVED | Distribution audit | DSTS9-B02 |
| Cleave attacker dies during derived chain | UNRESOLVED | UNRESOLVED | pending admitted Cleave unknown | operation-specific | commander unresolved | Cleave audit | CLVS9-B04 |
| Combo actor dies from non-Counter reaction | family-specific UNRESOLVED | n/a | #2 family-specific | remove/suppress orthogonal | commander delegated | Combo audit | CBS9-B01 |
| commander dies while scope open | operation-specific | proven YES for Chain/admitted Counter；unknown elsewhere | future not-created branch cancelled when owner dead | death != finalization | shared barrier | R5/P0 | RF-P04 |

Numeric tests must record theoretical value + observed integer；“uses round” is not an oracle.

Damage-layer tests/runtime must expose equivalent concepts：`Dtotal / Dtarget / DerivedCalculatedDamage / AssignedDamage / ActualCommittedTroopLoss / CreditedDamage`。

---

## 20. Stage8 Compatibility

Stage8 freeze/design records were rechecked. Stage8 freezes numeric validation, not Stage9 integerization. Stage9 needs target orchestration, reaction admission, partition seam, derived provenance/permission, restricted settlement, and finalization coordination through Stage9-compatible extension seams.

```text
FORMAL STAGE8 REOPEN REQUIRED = NO
STAGE8 = FROZEN
```

No current finding requires changing Stage8 pipeline topology, base formula, provider/binding architecture or Stage8 ownership.

---

## 21. Design Admission Gate

```text
CURRENT STAGE9 DESIGN ADMISSION = BLOCKED
```

Architecture-affecting blockers remain in integerization, execution/death ownership, partition death, finalization and Cleave completeness.

Stable core already usable：Target Arbitration；Core-owned NormalAttack master lifecycle；Counter batch semantics；Chain TRUE_FEEDBACK/traversal；Share target-first topology except lethal interrupt；Distribution participants-first topology except commander participant；Cleave derived identity/permission matrix except base/state/secondary/death.

Forbidden to pre-encode：implicit built-in round；universal death abort；universal death continuation；commander death == `battle.finished`；queued reaction == all post-death behavior continues；Share lethal cancellation；Distribution commander continuation；Cleave damage layer/state/target queue/death semantics.

---

## 22. Final Re-freeze Plan

Shared-contract recommendation：

```text
YES:
small STAGE9_EXECUTION_OWNERSHIP_CONTRACT
→ admission rights / scope completion / future scheduling

YES:
separate STAGE9_BATTLE_FINALIZATION_CONTRACT
→ victory detection / finalization barrier / commander collateral

CONDITIONAL:
STAGE9_INTEGERIZATION_CONTRACT
→ only if direct evidence proves common policy

NO:
STAGE9_EVERYTHING_CONTRACT

NO FOR NOW:
global FunctionalStateContainerContract
→ blocker-level incompleteness is Cleave-specific
```

Root Package Map：

```text
RF-P01  STAGE9_INTEGERIZATION_POLICY
RF-P02  NORMAL_ATTACK_LIFECYCLE_AND_COMBO_CONTRACT_REPAIR
RF-P03  EXECUTION_RIGHT_AND_DEATH_SCOPE
RF-P04  BATTLE_FINALIZATION_BARRIER
RF-P05  PARTITION_TRANSACTION_DEATH
RF-P06  CLEAVE_DAMAGE_LAYER_AND_RECOVERY_BASIS
RF-P07  CLEAVE_STATE_AND_SECONDARY_TARGET_COMPLETION
RF-C01  IMPLEMENTATION_HARDENING
RF-C02  DOC_SYNC_PACKAGE
```

Narrow Re-freeze Order：

```text
1 RF-P02
2 RF-P01
3 RF-P03
4 RF-P06
5 RF-P07
6 RF-P05
7 RF-P04
8 RF-C01
9 RF-C02
```

RF-P01 evidence extraction may run from the beginning. The first package that should actually edit a Frozen Contract is RF-P02.

This consolidation document is the only artifact added in this round. Do not start modifying any Frozen Contract until the next explicitly scoped repair package.