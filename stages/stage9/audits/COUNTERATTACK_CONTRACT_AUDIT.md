# COUNTERATTACK Contract Audit

> Project: 三国志战略版战斗模拟器 V2  
> Scope: Stage 9 Frozen Contract Independent Review — `690085 COUNTERATTACK / 反击`  
> Audit Date: 2026-09-13  
> Final Verdict: **PASS WITH DOC SYNC**

---

## 1. Repository Baseline

本轮重新读取两个仓库远端 `main`，未沿用聊天记录中的旧缓存。

```text
battle repo:
lxy2005051020-commits/sgs-v2-battle-system
exact main HEAD = 3a1f559e232e67e19671dc60521c80f3ca95597c
audit(stage9): verify distribution frozen contract

state research repo:
lxy2005051020-commits/sgs-state-mechanics-research
exact main HEAD = 9d86e54c407913ff020bafacf8196085780b99c6
```

本轮继承并读取此前八轮独立审计：

```text
CONFUSION_CONTRACT_AUDIT.md
TAUNT_CONTRACT_AUDIT.md
GUARD_CONTRACT_AUDIT.md
COMBO_CONTRACT_AUDIT.md
CLEAVE_CONTRACT_AUDIT.md
CHAIN_LINK_CONTRACT_AUDIT.md
DAMAGE_SHARE_CONTRACT_AUDIT.md
DISTRIBUTION_CONTRACT_AUDIT.md
```

当前 OPEN_FINDING_LEDGER 至少保持：

```text
CFS9-B01

CBS9-B01
CBS9-B02
CBS9-B03
CBS9-M01
CBS9-M02
CBS9-M03

CLVS9-B01
CLVS9-B02
CLVS9-B03
CLVS9-B04
CLVS9-M01

CHNS9-B01

SHS9-B01
SHS9-B02
SHS9-M01

DSTS9-B01
DSTS9-B02
DSTS9-M01
```

以及各轮 audit 中仍 OPEN 的 DOC_DRIFT / HARDENING。Counter 本轮只允许 SUPPORT / CONTRADICT / NARROW，不直接修改其他机制 P0。

---

## 2. Authoritative Freeze Source

COUNTERATTACK 当前 sole P0：

```text
stages/stage9/research/core_arbitration_v2/
STAGE9_COUNTERATTACK_MECHANICS_FREEZE_RECORD.md

status = FROZEN
current blob SHA = 5db49f4a9fa7088d9d980b50e75194a994119cc9
current line count = 814
original freeze commit = 4418f9f19719fb7d5938f73f58528c1e22c2019b
freeze Stage 9 counterattack mechanics
latest current-path commit = 83a7a44374399efed01dacc1e869b724089201c4
chore: organize stage artifacts into dedicated stage folders
```

随后存在：

```text
1f959938cf08a96e8facd064172f750f0380afa3
mark Stage 9 counterattack mechanics frozen

93247862243227b0d7712c218b2c6c187e124795
link frozen counterattack research contract

0cd4a08e78a0ca85c674fa5435a6b9c9e60a415a
sync frozen counterattack rules into Stage 9 core arbitration
```

状态研究仓：

```text
states/functional/minimum_usable/690085_COUNTERATTACK.md
Stage = MINIMUM_USABLE
```

并不存在：

```text
states/functional/counterattack/MECHANISM_CONTRACT.md
```

因此：

```text
battle Freeze Record = SOLE P0
state repo minimum_usable = lower-authority skeleton
```

---

## 3. State Kernel Audit

冻结 kernel：

```text
COUNTERATTACK
= Reaction State
triggered by ON_NORMAL_ATTACK_RECEIVED
```

正式分类：

```yaml
TriggerFamily: NORMAL_ATTACK_RECEIVED
DamageFamily: WEAPON_EFFECT_DAMAGE
NormalAttackIdentity: false
Container: MULTI_INSTANCE_LIST
```

COUNTERATTACK 不是：

```text
damage reflection
incoming damage percentage feedback
extra normal attack
generic on-damage reaction
```

反击伤害数值与 incoming NormalAttack damage 数值不构成基数关系。P0 的 14,756 对样本相关系数接近 0，并包含 incoming loss = 0 但 Counter positive damage 的直接反例。

Result: **PASS**。

---

## 4. Trigger Identity Audit

正式门禁：

```text
Incoming event has NormalAttack identity
AND defender is FINAL_ACTUAL_ATTACK_RECIPIENT
AND defender has operational CounterState at trigger window
AND defender survives pre-counter boundary
```

### 4.1 ALLOWED trigger sources

```text
standard NormalAttack                    ALLOWED
Combo #2 NormalAttack                    ALLOWED
Duel NormalAttack                        ALLOWED
Guard redirected NormalAttack            ALLOWED
Taunt selected NormalAttack               ALLOWED
Confusion selected NormalAttack           ALLOWED
```

其中 Guard 后 Counter holder 必须是：

```text
FINAL_ACTUAL_ATTACK_RECIPIENT
```

例：

```text
A attacks B
B guarded by C
→ originalTarget = B
→ actualTarget = C
→ read C.counterStates
→ never read B.counterStates for this hit
```

### 4.2 BLOCKED trigger sources

```text
Cleave                                   BLOCKED
Assault                                  BLOCKED
Chain TRUE_FEEDBACK                      BLOCKED
DamageShare derived loss                 BLOCKED
Distribution participant direct loss     BLOCKED
Counter damage                           BLOCKED
Periodic damage                          BLOCKED
ActiveSkill damage                       BLOCKED
```

核心原因是 event identity，而不是：

```text
Weapon damage?
Damage > 0?
Troop loss > 0?
```

因此 incoming NormalAttack 的实际扣兵为 0 仍可以形成 Counter window，只要该 NormalAttack DamageEvent 合法完成且 defender 存活。

Result: **PASS**。

---

## 5. NormalAttack Lifecycle Position Audit

当前兼容且唯一的相对顺序：

```text
NormalAttack main damage
→ defender death check
→ FirstAid / immediate allowed target reaction
→ Cleave
→ associated Chain
→ CounterBatch
→ if original attacker alive: Assault
→ if original attacker alive: Combo checkpoint / next-hit dispatch
```

CHAIN/CLEAVE 特例：

```text
without Cleave:
main-target Chain INLINE
→ CounterBatch

with Cleave:
main-target Chain qualification deferred
→ Cleave secondary #1
   → Cleave Chain INLINE
→ Cleave secondary #2 ...
→ Cleave complete
→ deferred main-target Chain
→ CounterBatch
```

因此 Counter P0 与当前 CLEAVE / CHAIN 审计后的生命周期位置一致。

COMBO P0 旧 §5 把 Assault 放在 Counter 前属于 `CBS9-B02`，不反向降低 Counter P0。

Result: **PASS**。

---

## 6. Damage Pipeline Audit

CounterDamage：

```text
IndependentWeaponDamageResolution(
  source = counterOwner,
  target = originalAttacker,
  sourceSkill = counterState.sourceSkill,
  skillRate = counterState.damageRate,
  runtimeContext = live
)
```

不是：

```text
incomingDamage × counterRatio
```

状态实例只绑定：

```text
source identity
source skill
damageRate
lifecycle metadata
```

每个 Ci execution 动态读取：

```text
owner current troops / attributes / modifiers
target current troops / defense / modifiers
target Evasion / Resistance
current Share / Distribution / Chain world state
```

禁止在 Apply 时 snapshot STR、troops、target defense 或 runtime modifiers。

### 6.1 Counter Damage Pipeline Matrix

| Stage / mechanism | Counter |
|---|---|
| Weapon base formula | ALLOWED |
| Damage modifier | ALLOWED |
| Crit | ALLOWED |
| Weakness | ALLOWED |
| Evasion | ALLOWED |
| Resistance | ALLOWED |
| DamageShare | ALLOWED |
| Distribution | ALLOWED — family/P0 inheritance |
| FirstAid | ALLOWED |
| Chain | ALLOWED |
| Lifesteal | ALLOWED |
| StrategyRecovery | BLOCKED |
| Counter | BLOCKED |
| Cleave | BLOCKED |
| Assault | BLOCKED |
| Combo | NOT APPLICABLE as Counter damage itself; outer attacker Combo branch resumes only after CounterBatch and only if attacker alive |

Counter 自身不引入新的 integerization 规则；基础兵刃公式与其已有 numeric semantics 直接继承 Stage8 / Frozen Weapon formula，因此不新增 Counter-specific rounding blocker。

Result: **PASS**。

---

## 7. Counter-Kill / COMBO Conflict Audit

这是本轮最高优先级。

### 7.1 Counter P0 Q05

P0 冻结：

```text
Counter kills original attacker
→ pending attacker-owned Assault CANCEL
→ pending Combo next-hit dispatch CANCEL
→ remaining attacker-owned Action ABORT
```

全库：

```text
Counter-kill original attacker = 341
post-death Assault = 0
post-death Combo #2 = 0
```

P0 进一步说明其中包含明确携带 Assault、以及明确具有 Combo 状态并在首击后被 Counter 反杀的样本。

### 7.2 COMBO Q45 controlled context

COMBO 研究 Q45 精确控制的上下文就是：

```text
attacker performs NormalAttack #1
→ defender Counter damage
→ attacker troops reach 0
→ cfg163 / death cleanup
→ inspect cfg230 and #2
```

结果：

```text
eligible cases = 11
cfg230 after death = 0
Combo #2 = 0
failures = 0
```

因此这 11/11 不是与 Counter Q05 无关的另一类死亡样本，而是同一关键上下文的独立证据。

### 7.3 Later COMBO P0 did not supply opposite raw evidence

本轮未发现 COMBO freeze commit 新增以下直接 raw evidence：

```text
Counter kills attacker
AND dead attacker emits cfg230
AND dead attacker executes Combo #2
```

所以不能仅因 COMBO P0 更新较晚就覆盖 Counter Q05。

正式裁决：

```text
COUNTER Q05 remains better-supported P0 behavior.
CBS9-B01 = SUPPORTED.
most likely repair owner = COMBO.
```

更精确地说，需要 narrow-repair 的是：

```text
COMBO universal ACTOR_DEATH_DURING_OWN_OPEN_ACTION exception
```

不能覆盖：

```text
Counter-kill death family
battle-termination death family
```

Counter P0 不需要因该冲突自身 REOPEN。

---

## 8. Multi-Source State Model Audit

正式模型：

```text
List<CounterState>
```

不是 single slot。

冻结：

```text
different sources coexist = true
replace = false
stronger wins = false
execute all = true
```

P0 记录：

```text
multi-source executions = 198
```

已观察组合：

```text
后发制人 → 还击
后发制人 → 三里而还
气凌三军 → 三里而还
```

Same-source：

```text
SameSource_Reapply = REFRESH
DuplicateSameSourceStack = false
```

全库有 128 次 `反击效果已刷新`。

刷新持续时间与 source-defined runtime metadata；damageRate/source metadata 的具体重新采样规则属于 source-skill responsibility，不要求 Counter core 猜统一生成公式。

Result: **PASS**。

---

## 9. CounterBatch Snapshot Audit

CounterBatch 必须是双阶段模型。

### Phase 1 — trigger-time admission snapshot

```text
ON_NORMAL_ATTACK_RECEIVED
→ gather all CounterStates operational NOW
→ deterministic order
→ freeze batch plan
```

锁定：

```text
instance identity
source identity
sourceSkill
damageRate/source-bound metadata
batch order
```

冻结：

```text
EligibilityEvaluation = TRIGGER_TIME
QueuedCounterSilentRemoval = false
```

因此 instance 一旦进入 batch，之后因：

```text
False Report appears
source skill becomes suppressed
state expires
state is physically removed/replaced
```

都不得重新跑 `state.isOperational()` 来撤销已经取得的 batch admission。

这只是 admission lock，不等于把 entity liveness、target liveness、battle state 一并 snapshot。

Result: **PASS**。

---

## 10. CounterBatch Live Execution Audit

Phase 2 每个 Ci 独立执行：

```text
Ci Execute
→ read live world
→ if target alive: standard independent weapon damage
→ Ci downstream reactions inline
→ world may mutate
→ Ci+1 reads updated world
```

所以：

```text
batch snapshot != combat context snapshot
```

允许：

```text
C1
→ target FirstAid
→ C1 Chain
→ C1 Lifesteal
→ state/troop/world mutation
→ C2
```

禁止：

```text
C1
C2
then process all callbacks
```

CounterBatch 是 ordered reaction batch with nested inline callbacks，不是简单 FIFO log list。

### 10.1 Owner death is a global execution gate, not admission re-check

P0 §10.4 冻结 holder death 遵循 global hard termination/state cleanup；R5 又冻结“动作/反应执行主体自身阵亡”对其尚未开始的后续自有执行分支进行 hard stop。

因此本轮将边界解释为：

```text
suppression/removal after admission
→ DOES NOT revoke queued Counter admission

Counter owner entity death before queued Ci begins
→ global source-liveness / death gate wins
→ that not-yet-started owner-owned Ci cannot begin
```

这不是重新检查 CounterState operationality，而是执行主体已死亡后的全局运行许可。

为避免实现者把两者混成同一个 `if (!isOperational) skip`，记录 `CTS9-H01`。

---

## 11. Multi-Counter Death Boundary Audit

Q07 冻结：

```text
CounterBatch = [C1, C2, ...]
C1 kills original attacker
→ death event
→ C2 CounterExecute STILL FIRES
→ target troops already 0
→ C2 committed troop loss = 0
→ remaining admitted siblings continue
```

关键样本：4，方向一致。

这证明：

```text
death != cancel every queued sibling reaction
```

同时必须与 Q05 并存：

```text
already-enqueued sibling Counter = CONTINUE
original dead attacker's future Assault/Combo = CANCEL
```

核心区别不是单纯 alive/dead，而是：

```text
execution right already granted inside current ReactionBatch
vs
future branch not yet granted execution right
```

### 11.1 zero-loss microstep permission

P0 recommended runtime 对 target already dead 的 sibling 明确走：

```text
emit CounterExecute
→ commitAttributedZeroCounterLoss
→ optional death confirmation
→ continue
```

并且跳过：

```text
resolveWeaponDamage(...)
```

因此 target already dead 时：

```text
CounterExecute fact          YES
attributed zero-loss commit  YES
new full DamageRequest       NO
Evasion                      NO
Resistance                   NO
DamageShare                  NO
Distribution                 NO
FirstAid                     NO
Chain                        NO
Lifesteal                    NO
```

这不是“对尸体再跑一遍完整伤害管线”。

Result: **PASS**。

---

## 12. Holder Death / Suppression Audit

### 12.1 suppression after batch creation

```text
queued at trigger time
→ later False Report / source suppression
→ queued Ci remains admitted
```

未来新的 NormalAttack trigger window 才会重新读取 operational state；已创建 batch 不受 retroactive suppression 影响。

### 12.2 physical state removal after batch creation

同理：

```text
queued instance identity already captured
→ later expiry/physical state removal
→ does not silently delete queued Ci
```

但 source-bound metadata 使用已锁定的 queued metadata；runtime combat context 仍 live。

### 12.3 Counter owner death during batch

若 C1 downstream 使 Counter owner 自身死亡：

```text
owner death
→ global death execution gate
→ not-yet-started owner-owned sibling C2 cannot begin
```

这与 target death after C1 不同：target death 不杀死 reaction owner；owner death 则移除未来执行主体。

该边界由 Counter P0 holder-death clause + R5 actor-self-death rule 可以唯一收敛，不构成 BLOCKER；但 P0 的 recommended pseudocode 未显式写出 owner-liveness gate，故保留 `CTS9-H01` 作为 runtime hardening。

### 12.4 holder death wording

不能实现为：

```text
if holder dead: cancel everything globally
```

必须拆成：

```text
future trigger eligibility = NO
physical state cleanup = YES
already completed Ci = preserved fact
not-yet-started owner-owned Ci = blocked by owner death
outer original attacker future branch = governed by attacker liveness / Q05
battle finalization = governed by R5
```

Result: **PASS WITH HARDENING**。

---

## 13. Attribution / Recovery Audit

正常 Counter attribution：

```yaml
physicalAttacker: COUNTER_OWNER
physicalSkill: COUNTER_SOURCE_SKILL
victim: ORIGINAL_NORMAL_ATTACKER
creditOwner: COUNTER_OWNER
DamageType: WEAPON
SourceType: COUNTER
NormalAttackIdentity: false
```

Recovery：

```text
Lifesteal = ALLOWED
StrategyRecovery = BLOCKED
```

若 Share / Distribution 参与：

```text
recovery base follows normal target's post-partition DamageEvent amount Dtarget
```

participant/share-recipient direct troop loss 不作为新的 ordinary DamageEvent，不额外产生 Counter owner's recovery trigger。

Counter → Chain：

```text
Counter damage
→ target normal DamageEvent survives
→ target Chain INLINE
→ return to current CounterBatch
```

若 Counter damage 直接杀死 trigger node：

```text
Chain CANCELLED
```

并受 `CHNS9-B01` 的 integerization blocker 影响；Counter 不重复创建数值 blocker。

Counter → Share：

```text
ALLOWED
```

Share target-death pending sharer 语义仍受 `SHS9-B02`，Counter 不替 Share 决定。

Counter → Distribution：

```text
ALLOWED
Evidence = FAMILY/P0 INHERITANCE
```

不得夸大为 Counter 专题大量直接观察。

Distribution participant commander death / transaction termination 继续受 `DSTS9-B02`，Counter 不替它关闭。

Result: **PASS**。

---

## 14. Cross-Mechanism Consistency

| Cross Item | Verdict | Notes |
|---|---|---|
| COUNTER × CONFUSION | CONSISTENT | Confusion only changes NormalAttack intended target; Counter reads final actual recipient. Counter-kill subcase does not reach Combo #2 target selection. |
| COUNTER × TAUNT | CONSISTENT | Taunt selects intended NormalAttack target; Guard may later redirect; Counter binds final actual recipient. |
| COUNTER × GUARD | CONSISTENT | Counter holder = FINAL_ACTUAL_ATTACK_RECIPIENT. |
| COUNTER × COMBO | CONFLICT | Q05/Q45 vs COMBO universal own-open-action death exception; repair owner most likely COMBO. Normal nonlethal order remains consistent: CounterBatch before Combo checkpoint. |
| COUNTER × CLEAVE | CONSISTENT | Cleave before Counter; Counter damage cannot recursively Cleave. CLEAVE's own open blockers remain external. |
| COUNTER × CHAIN | CONSISTENT | Counter may trigger Chain; Chain settles inline inside Ci; CHNS9-B01 remains external. |
| COUNTER × DAMAGE_SHARE | CONSISTENT | Counter ordinary weapon DamageEvent may enter Share; SHS9-B01/B02 remain external. |
| COUNTER × DISTRIBUTION | CONSISTENT | Allowed by Distribution family contract; DSTS9-B01/B02 remain external. |

### 14.1 Recursion Matrix

| Edge | Verdict |
|---|---|
| Counter → Counter | BLOCKED |
| Counter → Cleave | BLOCKED |
| Counter → Assault | BLOCKED |
| Counter → Combo | NOT APPLICABLE as direct recursion; outer attacker branch resumes only after batch if alive |
| Counter → Chain | ALLOWED |
| Counter → Share | ALLOWED |
| Counter → Distribution | ALLOWED |
| Counter → FirstAid | ALLOWED |
| Counter → Lifesteal | ALLOWED |
| Counter → StrategyRecovery | BLOCKED |

---

## 15. Stage8 Compatibility

Counter damage应作为：

```text
standard WEAPON effect DamageRequest
```

进入 Stage8 Frozen damage pipeline，然后由 Stage9 extension seams 承接：

```text
Share / Distribution
Chain
FirstAid / recovery / reactions
```

不得：

```text
复制兵刃基础公式
绕过 Stage8
手写 target troops -= x
```

当前没有证据表明 Stage8 需要为 Counter 正式 reopen。

```text
FORMAL STAGE8 REOPEN = NO
```

Stage9 runtime 需要能表达 ReactionBatch，但本轮冻结语义，不绑定具体类名。

---

## 16. Documentation Drift

### CTS9-D01 — state index still marks Counter as MINIMUM_USABLE

`sgs-state-mechanics-research/STATE_MECHANICS_INDEX.md` 当前仍：

```text
690085 COUNTERATTACK = MINIMUM_USABLE
```

而 battle repo sole P0 已：

```text
FROZEN
```

这是明确 DOC_DRIFT。

### CTS9-D02 — state minimum skeleton remains accuracy-deferred

`states/functional/minimum_usable/690085_COUNTERATTACK.md` 仍把 Damage Formula / Multi-source / Precise Ordering / Complex Interactions 标为 unresolved。作为历史 skeleton 可以保留，但需要在导航层明确 superseded by battle Freeze Record，否则读者容易把低权威 skeleton 当当前状态。

### CTS9-D03 — state root death baseline is stale for Counter/Combo conflict

state repo root README 仍用无条件：

```text
TARGET_DEATH
→ ABORT_REMAINING_ACTION
```

而 index 又采用 COMBO universal own-open-action exception。当前 Counter Q05 + COMBO Q45 证明至少 Counter-kill family 必须重新分层。该全局文档需在后续 consolidation/re-freeze 阶段统一，不在本 audit commit 修改。

---

## 17. Impact on Existing OPEN Findings

### CBS9-B01

```text
SUPPORT STRONGLY
```

Counter Q05 的 341 例与 COMBO Q45 11/11 同上下文 hard-cancel 一致。

推荐：

```text
CBS9-B01 most likely repair owner = COMBO
```

Counter P0 不需要为了兼容一个证据较弱的后生 generalization 而反向改写。

### CFS9-B01

Counter-kill 子场景应从 CONFUSION blocker scope 中移除：

```text
confused actor
→ NormalAttack #1
→ Counter kills actor
→ no Combo #2
→ no #2 Target Selection
→ no question of dead CONFUSION operationality in this subcase
```

因此：

```text
CFS9-B01 = NARROW RECOMMENDED
```

剩余 scope 只保留：

```text
non-Counter actor-death families
where dead actor is independently proven to reach a later target-selection point
```

如果 COMBO narrow re-freeze 最终证明没有任何 death family 允许 dead actor #2，则 CFS9-B01 可能进一步缩小甚至消失；本轮不直接关闭。

### CBS9-B02

```text
SUPPORT
```

Counter exact lifecycle order继续支持：

```text
Counter before Assault before Combo
```

### CBS9-B03

R5 与 Counter death model 均支持 battle termination 不应让 dead attacker 获得新 future branch；保持 OPEN，待 COMBO repair。

### CHNS9-B01 / SHS9-B01 / SHS9-B02 / SHS9-M01 / DSTS9-B01 / DSTS9-B02 / DSTS9-M01

Counter 不关闭这些外部 finding，只确认自己的 DamageEvent 按对应 P0 seam 交给各机制。

---

## 18. Findings

### BLOCKER

```text
NONE
```

### MAJOR

```text
NONE
```

### MINOR

```text
NONE
```

### DOC_DRIFT

```text
CTS9-D01
State index still reports 690085 as MINIMUM_USABLE although battle sole P0 is FROZEN.

CTS9-D02
minimum_usable Counter skeleton remains accuracy-deferred and lacks explicit superseded navigation.

CTS9-D03
state root/index death baselines remain mutually stale around Counter-kill vs COMBO own-open-action death.
```

### HARDENING

```text
CTS9-H01
Runtime must distinguish trigger-time CounterState admission lock from execution-time entity liveness.
Suppression/removal after admission does not revoke queued Ci; Counter-owner death before Ci begins does.

CTS9-H02
Add an explicit regression for commander original attacker killed by C1 with C2 already queued:
C2 remains in current CounterBatch, emits zero-loss execution, then victory finalization occurs after current admitted reaction batch semantics.
Direct four-sample Q07 set is not documented as commander-controlled, but P0 Q07 is unqualified and R5 places victory finalization outside current reaction completion.

CTS9-H03
Zero-loss sibling path must not call the full weapon DamageRequest pipeline against an already-dead target; emit CounterExecute + attributed zero loss only.
```

Finding counts：

```text
BLOCKER = 0
MAJOR = 0
MINOR = 0
DOC_DRIFT = 3
HARDENING = 3
```

---

## 19. Final Verdict

# PASS WITH DOC SYNC

COUNTERATTACK 自身 P0 的核心运行合同足以实现，并且本轮没有发现需要 reopen Counter P0 的新 blocker/major。

关键结论：

```text
1. Counter trigger identity = ON_NORMAL_ATTACK_RECEIVED, not generic damage.
2. Counter holder = FINAL_ACTUAL_ATTACK_RECIPIENT.
3. Counter lifecycle = after FirstAid/Cleave/Chain, before Assault/Combo.
4. Counter damage = independent live standard WEAPON effect damage.
5. Counter → Chain / Share / Distribution / FirstAid / Lifesteal = ALLOWED.
6. Counter → Counter / Cleave / Assault = BLOCKED by event identity.
7. Counter container = multi-instance list; same-source = refresh.
8. trigger-time batch admission is snapshotted; execution-time world is live.
9. C1 kills original attacker → queued sibling C2 continues as zero-loss execution.
10. original attacker death → its not-yet-started Assault / Combo future branches cancel.
11. commander original attacker death does not retroactively erase already-admitted current CounterBatch; victory finalization is outside current admitted reaction completion.
12. Counter owner death before sibling begins is different: source entity death removes future execution permission even though CounterState admission had been locked.
13. post-admission suppression / state removal does not cancel queued Ci.
14. Q05 vs COMBO is a real direct conflict; evidence favors Counter Q05.
15. CBS9-B01 repair owner = COMBO.
16. CFS9-B01 should remove the Counter-kill subcase and retain only independently proven non-Counter dead-actor later-selection families.
17. Exact global Counter comparator remains DEFERRED_NON_BLOCKING: current contract provides deterministic source-registration/source-slot default, observed pairwise constraints, and R6 supports skill-slot ordering. Official universal comparator fidelity remains deferred but does not prevent deterministic simulator implementation.
18. Universal Dispel remains DEFERRED_NON_BLOCKING with source-specific dispellability default.
19. Stage8 formal reopen = NO.
```

最重要的死亡模型必须以“执行权所有权”表达，而不能只写：

```text
if dead: return
```

正式概念：

```text
Already-enqueued Counter sibling
= execution right already granted inside current ReactionBatch
= target death alone does not revoke it

Original attacker's Assault / Combo
= future branch whose execution right has not yet been granted
= attacker death prevents branch creation / dispatch
```

因此：

```text
queued != future
reaction-batch ownership != entity-global queue
admission snapshot != world-state snapshot
```

九个单机制独立合同审计至此正式完成：

```text
CONFUSION
TAUNT
GUARD
COMBO
CLEAVE
CHAIN_LINK
DAMAGE_SHARE
DISTRIBUTION
COUNTERATTACK
```

下一阶段不再创建第十个单机制审计，正式进入：

```text
OPEN Finding Consolidation
→ Narrow Re-freeze Plan
→ Contract Repair
→ Cross-Mechanism Final Audit
```
