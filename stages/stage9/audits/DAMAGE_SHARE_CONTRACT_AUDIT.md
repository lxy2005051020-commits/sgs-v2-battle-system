# DAMAGE_SHARE Contract Audit

> Project: 三国志战略版战斗模拟器 V2  
> Scope: Stage 9 Frozen Contract Independent Review — `690087 DAMAGE_SHARE / 分担`  
> Audit Type: P0 cross-repository consistency + runtime contract closure audit  
> Audit Date: 2026-09-13  
> Final Verdict: **REOPEN REQUIRED**  
> Reopen Scope: **NARROW REOPEN — rounding tie rule + TARGET_DEATH_INTERRUPT evidence/wording only; Stage8 does not require formal reopen**

---

## 1. Repository Baseline

本轮重新读取远端 `main`，不沿用上一轮会话中的旧基线。

### 1.1 Battle repository

```text
Repository:
lxy2005051020-commits/sgs-v2-battle-system

Branch:
main

Exact main HEAD:
ccc90227c514aacf5f1e65a5009040be185d527c

HEAD commit:
audit(stage9): verify chain-link frozen contract
```

该 HEAD 与上一轮 CHAIN audit commit 相同，但本轮已经重新读取远端确认。

### 1.2 State research repository

```text
Repository:
lxy2005051020-commits/sgs-state-mechanics-research

Branch:
main

Exact main HEAD:
9d86e54c407913ff020bafacf8196085780b99c6

HEAD commit:
Refine README scope and authority notes
```

### 1.3 Inherited independent-audit findings

本轮完整继承此前六轮审计的 OPEN findings，不擅自关闭：

```text
CFS9-B01
CBS9-B01
CBS9-B02
CBS9-B03
CLVS9-B01
CLVS9-B02
CLVS9-B03
CLVS9-B04
CHNS9-B01
```

以及此前各 audit 中仍 OPEN 的 MAJOR / DOC_DRIFT / HARDENING 项。

若 DAMAGE_SHARE 为这些 finding 提供新约束，本文件只记录：

```text
IMPACT ON EXISTING FINDING
```

真正关闭仍要求对应机制执行 narrow re-freeze。

---

## 2. Dual P0 Authority Audit

DAMAGE_SHARE 当前存在两份 P0-class authority。

### 2.1 Battle-repo P0

```text
Path:
stages/stage9/research/core_arbitration_v2/
STAGE9_DAMAGE_SHARE_MECHANICS_FREEZE_RECORD.md

Status:
FROZEN

Current blob SHA:
012ba3a4b68f5e44fb1f6381a1ebddd2d48209f3

Line count:
965

Latest path commit:
83a7a406f59c38df8d48098f347b6816ff283870
refactor(paths): migrate completed stage artifacts under stages/

Original freeze commit:
f0ac9fc73299b283061708dfff9468fc6d62df04
freeze Stage 9 damage share mechanics
```

### 2.2 State-research P0

```text
Path:
states/functional/damage_share/MECHANISM_CONTRACT.md

Status:
FROZEN

Current blob SHA:
802d56d8114ce270106bbc935d835306f8a0c098

Line count:
965

Latest contract commit / freeze commit:
5b9e7dacd87da694226739549b31cf2ef5a14025
freeze 690087 damage share mechanism contract
```

### 2.3 Byte identity

```text
BYTE-IDENTICAL = NO
```

两文件 blob SHA 不同，文件大小亦不同，因此不能判 byte-identical。

差异集中在：

- 文档标题；
- 仓库角色说明；
- battle repo 的“同步自独立状态机制研究仓库”实现侧 provenance 文字。

未发现这些差异改变 runtime contract。

### 2.4 P0 semantic identity verdict

```text
SEMANTICALLY IDENTICAL = YES
MAIN SUPERSET OF STATE CONTRACT = NO, runtime semantics not broader
STATE CONTRACT SUPERSET OF MAIN = NO
DIVERGED P0 CONTRACTS = NO
```

正式判定：

# **SEMANTICALLY IDENTICAL**

两份 P0 不是同一个 blob，但核心条款、算法、顺序、生命周期、归因、统计和实现边界保持一致。

因此：

```text
P0 CROSS-REPO BLOCKER = NONE
```

---

## 3. Cross-Repo Contract Diff

按本轮要求逐 clause 核对：

| Clause | Battle P0 | State P0 | Verdict |
|---|---|---|---|
| Classification | post-formula partition / redirection family | same | SAME |
| State Model | owner=protected target, linked sharer | same | SAME |
| Ratio Snapshot | apply/refresh snapshot, runtime no recompute | same | SAME |
| Unique Slot | one effective Share per target | same | SAME |
| Reapplication | same-source refresh+replace; cross-source replace | same | SAME |
| Eligibility | reached Share stage, not cancelled/cost/share-derived | same | SAME |
| Zero vs Cancelled | legal zero executes; cancelled does not | same | SAME |
| Pipeline Position | after normal formula / before troop commit | same | SAME |
| Guard | inspect final actual target | same | SAME |
| Partition Math | round share portion, target exact remainder | same | SAME |
| Rounding | both say `round()`; neither defines `.5` tie mode | same unresolved text | SAME BUT INCOMPLETE |
| Commit Order | target first | same | SAME |
| Death Interrupt | target death discards pending sharer portion | same | SAME ASSERTION |
| Overflow | sharer overflow discarded | same | SAME |
| Derived Loss Identity | Attributed Direct Troop Loss, not DamageEvent | same | SAME |
| Post-Share DamageEvent | target event amount = Dtarget | same | SAME |
| Live Validation | per Damage Instance JIT | same | SAME |
| AOE | serial targets; no skill-level Share snapshot | same | SAME |
| Distribution Precedence | Share > Distribution | same | SAME |
| Lifecycle | exists != operational; fixed/source/condition-bound | same | SAME |
| Duration | protected-target ACTION_START ownership | same | SAME |
| Removal | expiry/death/replacement/functional invalidation distinctions | same | SAME |
| Attribution | physical source preserved | same | SAME |
| Cross-camp Credit | physical source != credit owner | same | SAME |
| Statistics | actual committed troop loss | same | SAME |
| Wounded | actual sharer committed loss is base | same | SAME |
| Implementation Contract | pre-commit partition, no recursive DamageSystem | same | SAME |

结论：双 P0 的问题不是“两个仓库讲了两套东西”，而是**两边同步保留了同样的两个未封口点：精确 round 规则，以及 target-death interrupt 的证据闭环**。

---

## 4. State Kernel Audit

### 4.1 Classification

DAMAGE_SHARE 的可实现分类为：

```text
Family = DAMAGE_PARTITION
State Owner = protected target
Linked Entity = sharer
```

P0 标题层使用：

```text
DAMAGE_REDIRECTION / DAMAGE_PARTITION
```

其中 `DAMAGE_REDIRECTION` 可作为描述性父标签；真正决定 Stage9 runtime 的 family 是 `DAMAGE_PARTITION`。

必须保持：

```text
DAMAGE_SHARE
!= DamageReductionModifier
!= second normal DamageEvent
!= transfer after troop loss
```

### 4.2 Dtotal

正式定义：

```text
Dtotal
= normal DamageEvent 已经完成其正常理论伤害 pipeline 后，
  在 DAMAGE_SHARE 介入之前的 pre-partition final damage
```

也即：

```text
normal formula / modifier finalization
→ Dtotal
→ DamagePartition
```

Dtotal 不是 target 实际已扣兵量，也不是 `ActualTargetTroopLoss`。

---

## 5. Eligibility / Pipeline Audit

### 5.1 Precise Stage8 mapping

Share P0 用概念顺序写：

```text
Target Selection
→ Guard / Target Redirect
→ FINAL_ACTUAL_DAMAGE_TARGET
→ Evasion / Resistance
→ normal Formula
→ Dtotal
→ DAMAGE_SHARE
```

映射到 Stage8 正式 topology 时，应更精确表达为：

```text
Target / Guard ownership outside Stage8 damage formula
↓
DamagePreventionSystem / HitResolutionSystem
    - cancellation / prevention gate
    - Evasion / Resistance-like prevention semantics belong here
↓
DamageFormulaPolicySystem
↓
Frozen Base Formula
↓
coefficient
↓
DamageModifierSystem
↓
finalization
↓
DamageResult.final_damage = Dtotal
↓
Stage9 DamagePartition extension
↓
Troop mutation
```

因此“Evasion / Resistance 在 normal formula 前”应理解为：

```text
它们属于 upstream Prevention / Hit Resolution，
不是 DAMAGE_SHARE 自己的 formula modifier。
```

Stage8 当时对具体 official Evasion / Resistance production binding 的 Evidence Gate 状态，不影响本轮 Share 的 ownership mapping。

### 5.2 Allowed DamageEvent families

合并最新 P0 × P0 后，以下合法 normal DamageEvent 可到达 Share：

```text
NormalAttack                  ALLOWED
Combo #2 NormalAttack         ALLOWED
ActiveSkill                   ALLOWED
Assault                       ALLOWED
Passive                       ALLOWED
Command                       ALLOWED
Periodic damage               ALLOWED
Cleave                        ALLOWED
Counter                       ALLOWED
Friendly fire / Confusion     ALLOWED
legal zero DamageEvent        ALLOWED
```

### 5.3 Blocked families / operation types

```text
Chain TRUE_FEEDBACK                 BLOCKED
Distribution participant direct loss BLOCKED
Share derived loss                  BLOCKED
self-cost / sacrifice               BLOCKED
evasion-cancelled event             BLOCKED
resistance-absorbed event           BLOCKED
```

核心门禁：

```text
Eligible =
    DamageEventReachedShareStage
    AND NOT DamageEventCancelled
    AND NOT SelfSacrificeCost
    AND NOT ShareDerivedLoss
```

不得把“兵力减少”本身当成 Share eligibility。

### 5.4 Legal zero vs cancelled

冻结语义完整且一致：

```text
Dtotal = 0
→ event remains legal
→ Share execution allowed
→ Dsharer_theoretical = 0
→ Dtarget = 0
```

而：

```text
event.cancelled == true
→ no Share
```

必须区分：

```text
Weakness / legal zero      = value 0, event alive
Evasion cancel             = event cancelled upstream
Resistance absorption      = event absorbed / stopped upstream
```

禁止：

```text
if damage <= 0: skip
```

---

## 6. Partition Math / Rounding Audit

### 6.1 Frozen algebra

P0 当前一致冻结：

```text
R = ratioSnapshot

Dsharer_theoretical = round(Dtotal × R)
Dtarget             = Dtotal - Dsharer_theoretical
```

守恒因此由“目标取整数余量”保证：

```text
Dsharer_theoretical + Dtarget = Dtotal
```

正确顺序：

```text
round share portion once
→ target takes exact remainder
```

禁止：

```text
round(Dtotal × R)
+
round(Dtotal × (1-R))
```

因为这会引入双边独立取整并可能破坏守恒。

### 6.2 Exact `round()` audit

本轮没有找到 Stage8 或公共 numeric policy 对以下边界作出 P0 定义：

```text
x.5
```

Stage8 numeric freeze 只定义：

- finite validation；
- bool / NaN / inf 拒绝；
- domain validation；

并未冻结：

```text
banker's rounding
ROUND_HALF_UP
ROUND_HALF_AWAY_FROM_ZERO
floor
ceil
truncate
int(x + 0.5)
```

Share P0 虽要求 regression `T02 .5 rounding boundary`，但没有给 T02 的**期望答案**。

例如：

```text
Dtotal × R = 100.5
```

当前合同不能唯一决定：

```text
100
or
101
```

因此：

```text
SHS9-B01 = OPEN
```

注意：这与 `CHNS9-B01` 属于同一“Stage9 derivative integerization 未定义”问题族，但不能自动假设 Share 与 Chain 必须采用同一种规则。

### 6.3 Distribution impact

Distribution P0 同样写有多个 `round()`：

```text
Dtarget = round(Dtotal × (1-R))
Dparticipant = round(Dtransfer / N)
```

因此 Share 的 round blocker 是下一轮 DISTRIBUTION 审计的重要前置输入，但本轮不替 Distribution 提前裁决其精确取整政策。

---

## 7. Commit Order / Death Interrupt Audit

### 7.1 Target-first commit

P0 一致冻结：

```text
1. compute partition
2. commit Dtarget to target
3. target death check
4. if target survives, commit Dsharer_theoretical to sharer
```

结论：

```text
DAMAGE_SHARE != atomic simultaneous split
```

非致死战报抽取结构也与此顺序一致：目标扣兵先出现，随后才出现 sharer 的分担执行与扣兵。

因此：

```text
TARGET-FIRST COMMIT = SUPPORTED / INTERNALLY CONSISTENT
```

### 7.2 TARGET_DEATH_INTERRUPT assertion

P0 当前断言：

```text
target receives Dtarget
→ target dies
→ discard pending Dsharer
→ sharer takes nothing
```

但本轮重新审计证据链后，**该结论尚未达到本轮要求的 controlled direct evidence gate**。

关键事实：

`r6_fendan_math_data.json`：

```text
total        = 11381
normal_count = 11381
lethal_count = 0
lethal_samples = []
```

其提取脚本只有在同时找到：

```text
main target loss
+
sharer execution/loss
```

时才把记录加入 `fendan_cases`。

因此一个“target 死亡后根本没有 sharer commit”的事件天然无法进入该数学数据集，不能由 `lethal_count = 0` 反向证明 interrupt。

另一个 `research_r6_death_during_fendan.py` 仅执行：

```text
fen_dan-tagged report
+ death event
+ previous 10 events contain “分担”
```

然后保存死亡前邻域。

它没有控制：

```text
Dsharer_theoretical > 0
sharer identity
sharer alive at commit point
sharer.currentTroops > 0
source requirements valid
no replacement / suppression / expiration
no other skip reason
post-death events contain no delayed share commit
```

现有样本确实出现：

```text
cfg123 target Share reduction
→ target loss to 0
→ target death
```

这是**有方向性的 Grade-B historical evidence**，但当前仓库中没有一个 controlled sample 同时证明：

```text
Dsharer_theoretical > 0
AND target dies from Dtarget
AND sharer alive
AND sharer has enough troops
AND no other gate blocks
AND ActualSharerTroopLoss = 0
```

而 `STAGE9_EVIDENCE_MATRIX_V2.md` 自己仍把 EM-19 标成：

```text
历史 B，未冻结
Remaining Unknowns = Share death atomic boundary
```

R3 也明确写：旧版致死分担观察仍属于 Share/Death 专题，不从 Cleave/Chain 结论外推。

因此当前 P0 中：

```text
“这遵循项目全局死亡硬终止原则”
```

不能作为充分依据。COMBO / CHAIN 已经证明死亡终止具有 operation-specific atomic boundary，不存在可无条件套用的 universal hard-death shortcut。

结论：

```text
TARGET_DEATH_INTERRUPT = PLAUSIBLE / P0 ASSERTED
DIRECT CONTROLLED EVIDENCE = INSUFFICIENT
SHS9-B02 = OPEN
```

### 7.3 Required narrow re-freeze evidence

关闭 `SHS9-B02` 至少需要一条可复核样本满足：

```text
Share active and operational
Dsharer_theoretical > 0
Target current troops <= Dtarget
Target dies from Dtarget
Sharer alive
Sharer troops > 0
No suppression / expiration / replacement / invalid source
Observe after target death through end of relevant DamageEvent
ActualSharerTroopLoss = 0
```

若真实证据无法获得，也可以显式把这一条降为 simulator policy，但不得继续标成“已被直接战报冻结”。

---

## 8. Sharer Loss Identity Audit

### 8.1 Formal operation identity

分担者份额属于：

```text
Attributed Direct Troop Loss
```

不是：

```text
Normal DamageEvent
```

因此不得把 Dsharer 递归送回普通 `DamageSystem`。

### 8.2 Sharer-side blocked pipeline

分担者不重新执行：

```text
Defense
Damage Reduction
Evasion
Resistance
FirstAid
Counter
Chain
Share
Distribution
ordinary hurt callbacks
```

也不产生新的 Cleave / Lifesteal / StrategyRecovery trigger node。

### 8.3 Still-real effects

但 `ActualSharerTroopLoss` 仍然是实际战斗事实：

```text
troop mutation
sharer death
wounded generation
battle statistics
kill attribution
victim identity
```

因此：

```text
Runtime event identity
!=
statistics / provenance identity
```

这并不矛盾。

### 8.4 Overflow

```text
ActualSharerTroopLoss
= min(Dsharer_theoretical, sharer.currentTroops)

Overflow
= Dsharer_theoretical - ActualSharerTroopLoss
```

Overflow 必须：

```text
discard
not return to target
not transfer to third unit
not repartition
not trigger Share
not trigger Distribution
not count in damage statistics
not generate wounded
```

这一部分 P0 闭环完整。

---

## 9. Lifecycle / Reapplication Audit

### 9.1 Unique slot

```text
one protected target
→ one effective DAMAGE_SHARE instance
```

明确不是：

```text
First-In Wins
multi-instance
stronger-wins
```

### 9.2 Reapplication

```text
same source   = REFRESH_AND_REPLACE
cross source  = REPLACE
old Share instance returns later = NO
```

新实例替换：

```text
sharer
sourceUnit
sourceSkill
ratioSnapshot
duration / lifecycle context
```

### 9.3 Ratio snapshot

```text
successful Apply / Refresh
→ calculate R from source-skill context
→ ratioSnapshot = R
```

之后：

```text
runtime attribute changes
→ do not recompute existing R
```

刷新重新采样。

具体：

```text
attributes → R
```

属于 SOURCE-SKILL RESPONSIBILITY，Share system 不负责猜测。

### 9.4 Sharer live validation

每个 Damage Instance JIT：

```text
state exists
state operational
sharer exists
sharer alive
sharer troops > 0
source requirements valid
```

所以：

```text
Hit1 kills sharer → Hit2 no Share
AOE Target1 kills common sharer → later Target2 no Share
```

不存在 skill-level Share snapshot。

### 9.5 Multi-target serial resolution

Share 只冻结：

```text
whatever deterministic targetQueue outer layer provides
→ resolve target serially
→ JIT Share check for each target
```

具体 AOE targetQueue 排序由 source skill / target system 所有，不是 Share blocker。

### 9.6 Sharer death and zombie instance

Sharer death：

```text
state.isOperational() = false immediately
```

物理 instance 可以暂时留在 protected target 身上直到后续清理窗口。

若此时新 Share 成功施加：

```text
new Share REPLACE existing slot
```

所以 zombie instance 不会永久阻塞新 Share，也不会在新实例结束后复活。

### 9.7 Control on sharer

```text
Stun / Silence / Disarm / Weakness / Confusion
```

只影响 sharer 的行动能力，不等同于 sharer dead / source invalid。

因此既有 Share 继续 operational，符合 passive partition identity。

### 9.8 Source suppression

P0 已通过 `lifecycleType` 区分：

```text
SOURCE_BOUND
→ source suppressed
→ instance may exist
→ operational=false
→ source recovers
→ operational=true
```

和：

```text
already independently applied active-style Share
→ source later suppressed
→ existing instance not automatically removed merely for that reason
```

语义足够实现。

### 9.9 Duration

固定时长 Share：

```text
duration owner = protected target
clock = protected target ACTION_START
```

```text
applied before target same-round ActionStart
→ same-round ActionStart consumes one

applied after target already acted
→ next ActionStart is first tick
```

无 apply-round exemption。

### 9.10 Cleanse / Dispel

```text
Purify = no
Cleanse = no
Dispel = no
```

并且：

```text
source suppression != dispel
functional invalidation != physical removal
```

这一部分两仓一致。

### 9.11 Protected-target death overreach

Share P0 仍包含：

```text
TARGET_DEATH
→ CLEAR_ALL_STATES
→ ABORT_REMAINING_STATE_RESOLUTION
→ ABORT_REMAINING_ACTION
→ REJECT_FUTURE_STATE_APPLICATION
```

其中必须拆分：

```text
A. Share operational status
B. Share physical state removal
C. current Share transaction
D. current DamageEvent
E. outer Action
F. future scheduling
```

Share 自己有权冻结的安全部分是：

```text
protected target dead
→ this target's Share no longer operational
→ its own Share instance may be cleared by death cleanup
→ current Share transaction cannot continue as though target were alive
```

但 Share **无权**凭自己的合同重新冻结：

```text
universal ABORT_REMAINING_ACTION
```

因为 COMBO 已经存在 own-open-action death exception，CHAIN 也证明 atomic block completion 具有机制级例外。

因此该段应在 narrow re-freeze 中改成 ownership-scoped wording。

```text
SHS9-M01 = OPEN
```

这不是对 `TARGET_DEATH_INTERRUPT` 的替代证明；二者必须分开处理。

---

## 10. Attribution / Credit Audit

### 10.1 Normal same-camp Share

Sharer direct troop loss 的物理 provenance：

```text
physicalAttacker = original attacker
physicalSkill    = original skill / normal attack
victim           = sharer
```

若 sharer 因此死亡：

```text
physical kill source = original attack source
```

同时实际 committed loss 进入对应战斗 damage statistics。

### 10.2 Cross-camp reverse Share

P0 对【闭月】类反向分担已经明确拆开：

```text
physicalAttacker
physicalSkill
victim
creditOwner
```

例：

```text
A attacks Diaochan
B (same camp as A) shares for Diaochan
```

可出现：

```text
physicalAttacker = A
physicalSkill = A's original skill
victim = B
creditOwner = DAMAGE_SHARE_EFFECT_OWNER
```

因此：

```text
physical source != combat credit owner
```

并不矛盾。

战后伤害收益、对应 kill/merit credit 按 `creditOwner`，而日志/物理因果仍保留原攻击 provenance。

### 10.3 attacker == sharer

明确允许：

```text
attacker == sharer
```

这不是 self-sacrifice cost。

即使攻击者自己的攻击最终让自己承担 Share loss：

```text
physical provenance = attacker's original attack
credit owner may be rerouted to Share effect owner
```

该边界 P0 已唯一冻结。

---

## 11. Statistics / Wounded Audit

必须保持以下字段分离：

```text
Dtotal
Dtarget
Dsharer_theoretical
ActualTargetTroopLoss
ActualSharerTroopLoss
```

### 11.1 Statistics

战后统计基准：

```text
ActualCommittedTroopLoss
```

正常正向 Share：

```text
DamageStat
+= ActualTargetTroopLoss
 + ActualSharerTroopLoss
```

禁止无条件：

```text
stat += Dtotal
```

因为：

- target overkill 只记实际扣兵；
- target-death interrupt 若成立，pending uncommitted share 不计；
- sharer overflow 不计。

### 11.2 Immediate recovery

P0 明确：

```text
Lifesteal / StrategyRecovery immediate recovery base
= target normal DamageEvent amount Dtarget
```

```text
Dsharer direct troop loss
→ does not feed attacker Lifesteal / StrategyRecovery
```

### 11.3 Wounded

虽然 sharer loss 不是 DamageEvent，但：

```text
WoundedGenerationBase = ActualSharerTroopLoss
```

具体伤兵比例与内部取整仍 OUT OF SHARE CONTRACT。

---

## 12. Share vs Distribution Audit

### 12.1 Priority

两份 Share P0 与 Distribution P0 一致：

```text
DAMAGE_SHARE > DISTRIBUTION
```

施加层：

```text
existing Share + incoming Distribution
→ Distribution invalid / rejected

existing Distribution + incoming Share
→ Share succeeds
→ Distribution replaced
```

### 12.2 Runtime exclusivity

正式 runtime 要求：

```text
same target + same Damage Instance
→ choose at most one effective partition policy
```

因此 Stage9 不得实现：

```text
run Share
then run Distribution
```

正确架构应接近：

```text
DamagePartitionResolver
→ resolve effective partition policy
→ SHARE or DISTRIBUTION or NONE
```

### 12.3 Replacement semantics

两 P0 都使用：

```text
replace / 覆盖 / 替换
```

因此 runtime 上旧 Distribution 不得在 Share 到期后自动“复活”；否则不再是 replacement，而是 suppression。

至于内部是否立刻删除对象、标 terminal-replaced、或保留只读历史记录，只要旧 instance 永远不能重新 operational，属于实现细节。

为防止实现误读，建议下一轮 Distribution narrow audit 显式写出：

```text
REPLACE != SUPPRESS
replaced instance never resumes
```

记录为 hardening，不构成本轮 Share blocker。

---

## 13. Death / Battle Termination Audit

### 13.1 Target death vs battle termination

即使未来 `TARGET_DEATH_INTERRUPT` 被直接证据确认，也只证明：

```text
target death
→ stop Share micro-transaction
→ discard pending sharer portion
```

它不能自动推出：

```text
battle immediately finalizes
outer action immediately aborts
all reaction stack disappears
```

这些属于 R5 / Action / Victory / specific atomic-block ownership。

### 13.2 Sharer dies during Share commit

当：

```text
sharer.currentTroops < Dsharer_theoretical
```

则：

```text
ActualSharerTroopLoss = sharer.currentTroops
sharer dies
Overflow discarded
```

Sharer death不能反向取消已经完成的 target commit，也不能把 target normal DamageEvent 改写成 cancelled。

因此：

```text
current Share transaction
→ completes at sharer commit/death bookkeeping
```

之后 outer DamageEvent 的合法 callback / reaction 是否继续，应由其自己的 event-family 与 Victory/termination policy 决定。

### 13.3 Commander sharer death

P0 只足够冻结：

```text
sharer is commander
+ Share commit kills sharer
→ commander death fact is real
→ battle victory condition may become satisfied
```

但当前项目对：

```text
Victory condition becomes true
vs
current atomic block / target callback completion
```

仍存在前序 OPEN blockers。

因此本轮不新造重复 blocker；记录为：

```text
INHERITED GLOBAL TERMINATION DEPENDENCY
```

受以下 OPEN finding 影响：

```text
CBS9-B03
CLVS9-B04
CFS9-B01 scope issue
```

Share 实现不得简单编码：

```text
if sharer commander dead: return-from-all-battle-processing
```

除非对应全局/机制级 re-freeze 已明确当前 atomic boundary。

---

## 14. Cross-Mechanism Consistency

### 14.1 Cross-mechanism matrix

| Cross Item | Verdict | Runtime contract |
|---|---|---|
| SHARE × CONFUSION | CONSISTENT | CONFUSION 改 target selection；Share 只读最终 actual target |
| SHARE × TAUNT | CONSISTENT | TAUNT 先决定 NormalAttack intended target；Share 在 actual damage target 上工作 |
| SHARE × GUARD | CONSISTENT | Guard redirect first；Share never reads original intended target |
| SHARE × COMBO | CONSISTENT | #1/#2 are independent NormalAttack; each JIT checks Share |
| SHARE × CLEAVE | CONSISTENT | Cleave DamageEvent → Share ALLOWED；CLVS9-B01 remains upstream |
| SHARE × CHAIN_LINK | CONSISTENT | target Dtarget may trigger Chain；sharer loss cannot；Chain feedback cannot Share |
| SHARE × COUNTERATTACK | CONSISTENT | Counter DamageEvent → Share ALLOWED；sharer loss → Counter blocked |
| SHARE × DISTRIBUTION | CONSISTENT | Share > Distribution; effective partition policies mutually exclusive |

### 14.2 CONFUSION / TAUNT / GUARD ordering

```text
CONFUSION / TAUNT
→ intended target selection
↓
GUARD
→ final actual target
↓
SHARE
→ inspect final actual target only
```

Share never reads original intended target.

### 14.3 COMBO

Combo #1 / #2：

```text
independent NormalAttackInstance
→ independently resolve final target
→ independently live-check Share
```

如果第一击的 Share commit 杀死 sharer：

```text
#2 Share check sees sharer dead
→ no Share
```

但 Combo 自身 death / Victory blockers 继续 OPEN，Share 不负责解决。

### 14.4 CLEAVE

```text
Cleave secondary DamageEvent
→ Evasion / Resistance gate
→ Cleave Dtotal
→ Share
→ Dtarget / Dsharer
```

`CLVS9-B01 MainAttackFinalDamage` 决定“主普攻生成多少 Cleave”，是 Share 之前的 Cleave input blocker，不重复计成 Share blocker。

### 14.5 CHAIN

最新关系：

```text
normal target Dtarget
→ may trigger Chain

sharer Dsharer direct troop loss
→ Chain BLOCKED

Chain TRUE_FEEDBACK
→ Share BLOCKED
```

Share P0 的：

```text
TakeDamageEvent.damage = Dtarget
```

与 CHAIN audit 的：

```text
TriggerNodeResolvedDamage = post-partition Dtarget
```

一致。

### 14.6 Counter

```text
Counter DamageEvent
→ Share ALLOWED
```

对于普通攻击父事件：

```text
main target receives normal Dtarget
→ main target Counter remains possible if ON_NORMAL_ATTACK_RECEIVED rules permit
```

而：

```text
sharer receives Dsharer direct troop loss
→ no Counter
```

不会形成：

```text
Counter → Share → Counter
```

### 14.7 FirstAid

必须区分两个 recipient：

```text
target Dtarget normal DamageEvent
→ FirstAid possible if event-family permits

sharer Dsharer direct troop loss
→ FirstAid BLOCKED
```

### 14.8 Recursion matrix

| Share-derived operation | Verdict |
|---|---|
| Share loss → Share | BLOCKED |
| Share loss → Distribution | BLOCKED |
| Share loss → Chain | BLOCKED |
| Share loss → Counter | BLOCKED |
| Share loss → FirstAid | BLOCKED |
| Share loss → Cleave | BLOCKED / N/A |
| Share loss → Lifesteal | BLOCKED |
| Share loss → StrategyRecovery | BLOCKED |
| Share loss → ordinary hurt callback | BLOCKED |

这里所有 BLOCKED 都只描述：

```text
sharer Dsharer direct troop loss
```

不能误伤：

```text
target Dtarget normal DamageEvent
```

的正常 callback eligibility。

---

## 15. Stage8 Compatibility

### 15.1 Frozen ownership

Stage8 正式冻结：

```text
DamageSystem.calculate
= unique theoretical damage entry

DamageResolutionSystem
= theoretical result → troop mutation / battle fact coordinator

TroopSystem
= troop mutation boundary
```

并明确把：

```text
damage split/share
```

留给 Stage9，而不是 Stage8。

### 15.2 Current implementation topology

当前 `DamageResolutionSystem.apply_result()` 对未 prevented DamageResult 直接：

```text
target = context.get_unit(damage.target_id)
↓
TroopSystem.apply_damage(target, damage.final_damage)
```

即当前代码没有暴露现成的 public Share seam。

### 15.3 Required extension point

Share 不能在 troop commit 之后实现成“再从 target 搬兵给 sharer”。

必须插入：

```text
DamageResult.final_damage / Dtotal
↓
Stage9 DamagePartition policy
↓
assigned target loss
↓
TroopSystem target commit
↓
optional sharer direct troop-loss commit
```

最合理分类：

```text
C. COMPATIBLE POST-FORMULA PARTITION EXTENSION
```

也可工程化为：

```text
B. Stage9-aware wrapper/extension at DamageResolution coordinator boundary
```

前提是仍保持唯一 theoretical-result → troop-mutation coordinator，不绕开 TroopSystem 的唯一 mutation ownership。

### 15.4 Formal reopen verdict

```text
Stage8 FORMAL REOPEN = NOT REQUIRED
```

理由：

1. Stage8 明确把 damage split/share 留给 later stage；
2. Share 不改变 Stage8 frozen base formula / modifier / prevention semantics；
3. Share 读取 final theoretical damage，正好位于 `DamageResult` 与 troop mutation 之间；
4. 需要的是 Stage9 extension seam，而不是重定义 Stage8 已冻结结果。

但 Stage9 施工时必须保证：

```text
partition before troop commit
```

否则就会违反 Share P0。

---

## 16. Documentation Drift

### SHS9-D01 — Evidence Matrix Share status is stale

`STAGE9_EVIDENCE_MATRIX_V2.md` 当前同时存在：

```text
EM-15 Share 数学
→ 尚未作为本轮 Share Core Frozen

EM-19 致死分担截断
→ 历史 B，未冻结

Current Research Status:
Share Core Mechanics = NEXT RESEARCH TARGET
```

而两份最新 P0 都已经标：

```text
Status = FROZEN
```

这属于明确 documentation drift。

注意：EM-19 的“未冻结”恰好也暴露出 `SHS9-B02` 的证据链没有被后续 artifact 正式补强。

### SHS9-D02 — State-research root README still presents unconditional global Target Death

state repo `README.md` 仍直接写：

```text
TARGET_DEATH
→ CLEAR_ALL_STATES
→ ABORT_REMAINING_STATE_RESOLUTION
→ ABORT_REMAINING_ACTION
→ REJECT_FUTURE_STATE_APPLICATION
```

而同仓 `STATE_MECHANICS_INDEX.md` 已经加入 Combo own-open-action death exception。

因此 root README 的 global baseline 已过宽，容易继续污染 Share/Distribution 的生命周期文字。

### Index status

`STATE_MECHANICS_INDEX.md` 当前已正确把：

```text
690087 DAMAGE_SHARE
→ ✅ FROZEN
```

所以 DAMAGE_SHARE 自身索引状态不是 drift。

---

## 17. Findings

### BLOCKER

#### SHS9-B01 — `round(Dtotal × R)` exact integerization is undefined

**Status:** OPEN

两 P0 都写 `round()`，但项目没有冻结 `.5` tie-breaking 规则。Stage8 numeric validation 不是 rounding policy。

影响：

```text
Dsharer_theoretical
Dtarget
post-share Chain trigger base
recovery base Dtarget
statistics / wounded in edge cases
```

关闭条件：

```text
freeze explicit integerization rule
+
provide .5 regression expectations
```

不得用具体编程语言 built-in `round()` 的默认行为代替合同。

#### SHS9-B02 — TARGET_DEATH_INTERRUPT lacks controlled direct evidence

**Status:** OPEN

P0 已断言 target death discards pending sharer portion，但当前可复现 artifact 没有满足本轮要求的 controlled sample。

现有：

```text
historical Grade-B direction
+ death-near-share neighborhood scan
+ obsolete blanket hard-death rationale
```

不足以唯一证明 Share-specific micro-transaction interrupt。

关闭条件：

```text
controlled lethal target sample
or explicit downgraded simulator-policy decision
```

### MAJOR

#### SHS9-M01 — Protected-target death clause over-owns outer Action termination

**Status:** OPEN

Share P0 的生命周期段把 protected-target death 直接写成 unconditional `ABORT_REMAINING_ACTION`，与当前 operation-specific death model 不兼容。

修复应只冻结 Share 自己拥有的：

```text
instance operational/removal
Share transaction stop
```

outer Action / Victory / future reaction 交给对应机制合同。

### MINOR

#### SHS9-N01 — Cross-family replacement should explicitly forbid resurrection

**Status:** OPEN / NON-BLOCKING

`Share replaces Distribution` 的 runtime 语义已经足以要求两者不并行，但下一轮 Distribution 文档应显式写：

```text
REPLACE != SUPPRESS
replaced Distribution never resumes after Share expires
```

以免实现把 replace 做成 temporary suppression。

### DOC_DRIFT

#### SHS9-D01 — `STAGE9_EVIDENCE_MATRIX_V2.md` still says Share is next research / death boundary unfrozen

**Status:** OPEN

应在对应 re-freeze 后同步，而不是本轮修改。

#### SHS9-D02 — state repo root README still states unconditional global death hard-stop

**Status:** OPEN

同仓 index 已经有 Combo exception，root README 应后续同步为 scoped death model。

### HARDENING

#### SHS9-H01 — Introduce one effective `DamagePartitionResolver`

建议：

```text
Dtotal
→ choose SHARE / DISTRIBUTION / NONE
→ execute exactly one partition policy
```

防止 Share 与 Distribution 被串行执行。

#### SHS9-H02 — Use typed direct-troop-loss provenance

建议把：

```text
Attributed Direct Troop Loss
```

建成与 normal DamageEvent 不同的 typed operation，并至少保留：

```text
physicalAttacker
physicalSkill
creditOwner
victim
parentDamageEventId / provenance
```

防止 recursive DamageSystem re-entry 与 attribution 混淆。

### Finding counts

```text
BLOCKER   = 2
MAJOR     = 1
MINOR     = 1
DOC_DRIFT = 2
HARDENING = 2
TOTAL     = 8
```

---

## 18. Impact on Existing Findings

### CFS9-B01

```text
STATUS = OPEN
```

IMPACT ON EXISTING FINDING：Share P0 仍复用了过宽的 unconditional hard-death wording，进一步证明死亡规则必须按 operation / atomic boundary 分层，不能使用 universal `death → abort action`。

本轮不关闭 CFS9-B01。

### CBS9-B01 / CBS9-B02 / CBS9-B03

```text
STATUS = OPEN
```

Share 不解决 Combo 自身：

- own-open-action death continuation；
- reaction ordering ownership；
- Victory/no-target ordering。

Share 只提供“每个 NormalAttack DamageEvent 独立 JIT 检查 Share”的约束。

### CLVS9-B01 / B02 / B03 / B04

```text
STATUS = OPEN
```

`CLVS9-B01 MainAttackFinalDamage` 影响 Cleave 先生成多少 secondary damage；随后 secondary DamageEvent 可以进入 Share。它是上游 Cleave blocker，不是 Share blocker。

其余 Cleave state lifecycle / secondary target / death pending 边界同样不由 Share 关闭。

### CLVS9-M01

```text
STATUS = OPEN
```

IMPACT ON EXISTING FINDING：Share P0 提供明确方向：

```text
any normal DamageEvent after Share partition
→ Lifesteal / StrategyRecovery base reads Dtarget only
→ Dsharer excluded
```

因此 Cleave→Share 情况的恢复基数应遵循 post-share `Dtarget`。但仍须在 Cleave narrow re-freeze 中正式关闭 CLVS9-M01。

### CHNS9-B01

```text
STATUS = OPEN
```

Share 新发现 `SHS9-B01` 与其同属 integerization-contract 缺口，但：

```text
Share round rule
!= automatically Chain round rule
```

不能用本轮自动关闭 CHNS9-B01。

---

## 19. Final Verdict

# **REOPEN REQUIRED**

范围严格限定为：

```text
NARROW REOPEN
```

当前 DAMAGE_SHARE 的大部分 runtime contract 已经闭环：

```text
P0 cross-repo semantics          CONSISTENT
state model                      COMPLETE
unique slot / reapplication      COMPLETE
ratio snapshot                   COMPLETE
eligibility                      COMPLETE
legal-zero vs cancelled          COMPLETE
final actual target ownership    COMPLETE
Dtotal position                  COMPLETE
target-first commit              COMPLETE
sharer overflow                  COMPLETE
sharer direct-loss identity      COMPLETE
recursion boundary               COMPLETE
Chain / Cleave / Counter mapping COMPLETE
Distribution precedence          COMPLETE
live validation                  COMPLETE
multi-target serial check        COMPLETE
control / source suppression     COMPLETE
duration ownership               COMPLETE
cleanse / dispel                 COMPLETE
cross-camp attribution / credit  COMPLETE
statistics / wounded             COMPLETE
Stage8 compatibility             COMPLETE — no formal reopen
```

仍不能宣布 `PASS — CONTRACT READY` 的原因只有两个 implementation-blocking 核心点：

```text
1. SHS9-B01
   round(Dtotal × R) 的 `.5` 精确规则未定义

2. SHS9-B02
   target dies → pending sharer loss cancelled
   仍缺本轮要求的 controlled direct evidence
```

另有一个必须在同次 narrow re-freeze 修正文义边界的 MAJOR：

```text
SHS9-M01
Protected-target death clause must not own universal outer Action abort
```

### Canonical runtime contract that is already safe to retain

```text
normal DamageEvent
→ upstream cancellation / hit resolution
→ normal formula / modifiers
→ Dtotal
→ select effective partition policy
→ DAMAGE_SHARE live-check final actual target
→ Dsharer_theoretical = ROUND_POLICY(Dtotal × R)   # exact policy OPEN
→ Dtarget = Dtotal - Dsharer_theoretical
→ commit target Dtarget first
→ target death check
→ TARGET_DEATH_INTERRUPT                           # evidence OPEN
→ if allowed, commit attributed direct troop loss to sharer
→ discard sharer overflow
→ target normal DamageEvent semantics use Dtarget
→ sharer direct loss does not re-enter normal DamageEvent pipeline
```

### Next mechanism

```text
NEXT INDEPENDENT MECHANISM AUDIT = 690086 DISTRIBUTION / 分摊
```

Distribution 审计应直接继承本轮的两个前置警报：

```text
- do not assume `round()` has a project-global meaning
- do not inherit unconditional global hard-death wording without operation-specific proof
```
