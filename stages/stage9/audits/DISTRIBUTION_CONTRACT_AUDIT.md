# DISTRIBUTION Contract Audit

> Project: 三国志战略版战斗模拟器 V2  
> Scope: Stage 9 Frozen Contract Independent Review — `690086 DISTRIBUTION / 分摊`  
> Audit Type: P0 authority + inherited-rule + partition topology + death boundary + Stage8 compatibility audit  
> Audit Date: 2026-09-13  
> Final Verdict: **REOPEN REQUIRED**  
> Reopen Scope: **NARROW REOPEN — Distribution integerization tie semantics + commander-participant death/finalization boundary + protected-target death wording only; Stage8 does not require formal reopen**

---

## 1. Repository Baseline

本轮重新读取两个仓库远端 `main`，不沿用旧会话缓存。

### 1.1 Battle repository

```text
Repository:
lxy2005051020-commits/sgs-v2-battle-system

Branch:
main

Exact audit baseline HEAD:
66681c58b02be8baaecc17b0783ec3d5f6775385

HEAD commit:
audit(stage9): verify damage-share frozen contract
```

### 1.2 State research repository

```text
Repository:
lxy2005051020-commits/sgs-state-mechanics-research

Branch:
main

Exact audit baseline HEAD:
9d86e54c407913ff020bafacf8196085780b99c6

HEAD commit:
docs(index): mark combo frozen and scope death baseline
```

### 1.3 Inherited OPEN findings

本轮继承此前七轮独立审计中仍 OPEN 的 finding，不擅自关闭：

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

SHS9-B01
SHS9-B02
SHS9-M01
```

以及对应 audit 中仍 OPEN 的其他 MAJOR / DOC_DRIFT / HARDENING 项。

若 DISTRIBUTION 对旧 finding 提供约束，只记录 `IMPACT ON EXISTING FINDING`；本审计不替其他机制执行 re-freeze。

---

## 2. Authoritative Freeze Source

### 2.1 Battle-repo P0

```text
Path:
stages/stage9/research/core_arbitration_v2/
STAGE9_DISTRIBUTION_MECHANICS_FREEZE_RECORD.md

Status:
FROZEN

Current blob SHA:
c1df3fe35a80bd9ee22024b88e156cc75c92f60b

Current line count:
695

Original freeze commit:
f3996e1b63fee0387eaa62f33006125cb7e15f9c
freeze Stage 9 distribution mechanics

Original path:
research/stage9_core_arbitration_v2/
STAGE9_DISTRIBUTION_MECHANICS_FREEZE_RECORD.md

Latest path/migration commit:
83a7a44374399efed01dacc1e869b724089201c4
chore: organize stage artifacts into dedicated stage folders
```

原始 freeze commit 以 `+1,695` 新增该文件；迁移后 current blob SHA 与原始 blob SHA 相同，因此本次路径迁移没有改变 P0 内容字节。

### 2.2 State-research authority

状态研究仓当前仍只有：

```text
README.md
STATE_MECHANICS_INDEX.md
states/functional/minimum_usable/690086_DISTRIBUTION.md
```

其中 `690086_DISTRIBUTION.md` 明确写为：

```text
Stage = MINIMUM_USABLE
Exact Split Ratio = UNRESOLVED_FOR_ACCURACY_PHASE
Eligibility = UNRESOLVED_FOR_ACCURACY_PHASE
Multi-source / Reapplication = UNRESOLVED_FOR_ACCURACY_PHASE
Precise Ordering = UNRESOLVED_FOR_ACCURACY_PHASE
Complex Interactions = UNRESOLVED_FOR_ACCURACY_PHASE
```

并明确“不构成正式冻结合同”。

当前不存在：

```text
states/functional/distribution/MECHANISM_CONTRACT.md
```

因此本轮权威关系为：

```text
battle repo Freeze Record = SOLE P0
state repo = LOWER-AUTHORITY SKELETON / INDEX ONLY
```

不存在 dual-P0 semantic consistency blocker。

---

## 3. Inherited DAMAGE_SHARE Rules Audit

DISTRIBUTION 的继承原则只能用于外围 DamageEvent 管线；数学、参与者拓扑、Commit 顺序与死亡边界必须以 Distribution P0 自己的条款为准。

| Rule | Audit Classification | Distribution verdict |
|---|---|---|
| DamageEvent eligibility | SAFE TO INHERIT | 仅 reached partition stage 且未被上游 cancel/absorb 的正常 DamageEvent 进入 |
| legal zero | SAFE TO INHERIT | `Dtotal = 0` 仍是合法事件值，不等于 cancelled |
| Evasion cancellation | SAFE TO INHERIT | Evasion 在 partition 前取消事件 |
| Resistance absorption | SAFE TO INHERIT | Resistance 在 partition 前吸收/终止事件 |
| Guard actualTarget | SAFE TO INHERIT | participant topology 锚定 `FINAL_ACTUAL_DAMAGE_TARGET` |
| post-formula partition position | SAFE TO INHERIT | `Dtotal` 已完成普通公式，partition 位于 troop commit 前 |
| Ratio snapshot | SAFE TO INHERIT | successful Apply/Refresh 时快照；现有 ratio 不随运行时属性变化重算 |
| live validation | SAFE TO INHERIT | 每个 Damage Instance 重新读取当前 Distribution 与当前世界状态 |
| derived loss identity | SAFE TO INHERIT | participant loss = Attributed Direct Troop Loss，不是 DamageEvent |
| statistics | SAFE TO INHERIT | 只统计实际 committed troop loss |
| wounded | SAFE TO INHERIT | participant wounded base = actual participant loss；ratio/rounding 属伤兵合同 |
| source suppression | SAFE TO INHERIT | 跟随 source effect operational semantics，不等于物理删除 |
| cleanse / dispel | SAFE TO INHERIT | Normal Purify/Dispel 不移除 Distribution；证据等级是 family-inherited，不冒充 Distribution direct report proof |
| duration owner / tick | SAFE TO INHERIT | protected target 自身 ACTION_START / Turn Start 管理固定 duration |
| death outer-action wording | INHERITED BUT CURRENTLY OPEN | `ABORT_REMAINING_ACTION` 过度拥有外层动作终止，见 DSTS9-M01 |
| Share target-death interrupt | OVERRIDDEN BY DISTRIBUTION | Distribution 是 participants-first；不能继承 `TARGET_DEATH_INTERRUPT` |
| strict theoretical conservation | OVERRIDDEN BY DISTRIBUTION | Distribution double-rounding 明确允许整数级非守恒 |
| single sharer topology | NOT APPLICABLE | Distribution = MULTI_RECIPIENT |
| target-first commit | OVERRIDDEN BY DISTRIBUTION | Distribution = PARTICIPANTS_FIRST_COMMIT |
| Share cross-camp credit rerouting | NOT APPLICABLE | Distribution 常规 attribution 保持 original attacker；无 Share 的闭月特殊 rerouting |
| Share `round()` resolution | INHERITED BUT CURRENTLY OPEN | `SHS9-B01` 没有提供可继承答案；Distribution 自己有两个 round site，见 DSTS9-B01 |

关键裁决：

```text
SHS9-B01 does NOT solve Distribution rounding.
SHS9-B02 does NOT become a universal death law.
SHS9-M01 does NOT authorize Distribution to own outer Action termination.
```

---

## 4. State Kernel Audit

正式运行内核：

```text
normal DamageEvent
→ normal formula completes
→ Dtotal
→ resolve FINAL_ACTUAL_DAMAGE_TARGET
→ read Distribution state
→ build current participant plan
→ calculate Dtarget / Dtransfer / Dparticipant
→ deterministic participant Slot ASC micro-commits
→ original target Dtarget normal commit
```

分类保持：

```yaml
Family: DAMAGE_PARTITION
Participant_Topology: MULTI_RECIPIENT
State_Owner: PROTECTED_TARGET
Commit_Topology: PARTICIPANTS_FIRST_COMMIT
```

明确不是：

```text
ordinary damage reduction
multiple DAMAGE_SHARE instances
secondary AOE attack
participant DamageEvent fan-out
```

实现上应视为 ordered micro-commit transaction，而不是把全部 participant loss 合成一个不可观察的 giant atomic mutation。每个 participant commit 后仍允许 troop mutation、death fact、commander-death condition、statistics、wounded、kill attribution 发生；只是普通 hurt callbacks 被身份规则阻断。

---

## 5. Partition Math Audit

当 `N > 0`：

```text
Dtotal
= partition 前正常 DamageEvent 的理论最终伤害

Dtarget
= round(Dtotal × (1 - R))
= 原目标最后正常 commit 使用的理论分配量

Dtransfer
= Dtotal - Dtarget
= 被移出原目标的理论转移池

Dparticipant
= round(Dtransfer / N)
= 本 transaction 中每一个 planned participant 共用的理论分配量
```

所有 participant 使用同一个 `Dparticipant`。

禁止：

```text
lastParticipant += remainder
target += remainder
recompute a balancing remainder after commits
```

因此：

```text
Dtarget + N × Dparticipant
```

**不要求**等于：

```text
Dtotal
```

这与 DAMAGE_SHARE 的 `Dtarget = Dtotal - Dsharer` 严格理论守恒完全不同。

当 `N == 0`：

```text
Dtarget = Dtotal
no effective participant distribution
```

Distribution state 本身不因此被删除，不消费 ratio，不改变 duration；下一笔 Damage Instance 仍重新判断。N=0 时是否打印专门 execution announcement 属日志表现层，P0 未冻结为战斗结果语义，不构成本轮 blocker。

---

## 6. Double-Rounding Audit

Distribution 有两个独立整数化调用点：

```text
RoundTarget:
round(Dtotal × (1 - R))

RoundParticipant:
round(Dtransfer / N)
```

### 6.1 Exact rule status

当前项目没有统一 P0 冻结：

```text
x.5 → ?
```

也没有证据证明这里应直接采用 Python / Java / C# / JS 任一语言 builtin。

因此当前精确规则是：

```text
RoundTarget exact tie rule = UNDEFINED
RoundParticipant exact tie rule = UNDEFINED
```

本审计将其记录为**一个** blocker，而不是人为拆成两个：两处在同一个 P0 中使用同一个未定义的 `round()` 记号，当前没有任何证据证明它们应采用不同 integerization policy。narrow re-freeze 应建立一个明确的 `DistributionIntegerizationPolicy`，或者明确证明两个调用点不同后再拆分。现在先把“缺少统一精确定义”作为一个合同缺口最准确。

Result: **DSTS9-B01**。

### 6.2 Boundary examples

| Case | Rule | Dtarget | Dtransfer | Dparticipant | `Dtarget + N×Dparticipant` |
|---|---|---:|---:|---:|---:|
| `Dtotal=201, R=50%, N=2` | half-up | 101 | 100 | 50 | 201 |
| same | half-even | 100 | 101 | 50 | 200 |
| `Dtotal=203, R=50%, N=2` | half-up | 102 | 101 | 51 | 204 |
| same | half-even | 102 | 101 | 50 | 202 |
| `Dtotal=201, R=50%, N=1` | half-up | 101 | 100 | 100 | 201 |
| same | half-even | 100 | 101 | 101 | 201 |
| `Dtotal=200, R=49.75%, N=2` | half-up | 101 | 99 | 50 | 201 |
| same | half-even | 100 | 100 | 50 | 200 |

所以 double rounding 的后果不是“日志差 1 点”这么温柔：它可改变 participant / target 是否死亡、主将是否死亡、后续 participant eligibility、后续 Damage Instance 的世界状态与终战时机。

### 6.3 Conservation verdict

```text
STRICT CONSERVATION = NO
```

非守恒是合同的一部分，不是 bug。实现不得在第二次 round 后自行做 remainder repair。

---

## 7. Participant Set / N Timing Audit

这是本轮重点，但 P0 已足以唯一收敛，不形成 blocker。

### 7.1 Two dynamic layers must be separated

跨 Damage Instance：

```text
PER DAMAGE INSTANCE dynamic
```

同一 Distribution transaction 内：

```text
participant identities are planned once
N is fixed once
Dparticipant is fixed once
slot commit performs JIT eligibility recheck
```

依据不是猜测，而是 P0 自身的组合约束：

1. §4 先定义 `N = current legal participant count`，再计算一个统一 `Dparticipant`；
2. §4 明确“所有承担者独立使用同一个 Dparticipant”；
3. §6 要求 slot ASC commit，并“跳过当前不合法单位”；
4. §17 implementation contract 明确先 `resolveCurrentParticipants(...).sortBy(slot ASC)`，再以 `participants.count` 计算一次 `Dparticipant`，随后才进入 `for participant in participants`；
5. §18 的动态回归测试描述的是“队友死亡后**下一击**重新计算 participants”，不是同一 transaction 每步重算。

正式解释：

```text
Damage Instance reaches Distribution
↓
build participant identity list from current legal world state
↓
N = list.count
↓
compute Dtarget / Dtransfer / Dparticipant once
↓
commit list in Slot ASC
    each slot JIT rechecks current alive/legal state
↓
target commit
```

因此：

```text
mid-transaction newly eligible unit → NOT ADDED
planned participant becomes invalid before own slot → SKIP
skip → NO N recompute
skip → NO Dparticipant recompute
skip → NO redistribution
```

下一笔独立 Damage Instance 才重新建 participant list / N / amounts。

Result: **NO BLOCKER**。

### 7.2 Hardening note

实现必须把“per-Damage-instance dynamic”与“within-transaction recompute”拆开，否则一句 `for teammate in current_allies` 很容易在循环中偷偷读取变化后的集合并重算分母。

Result: **DSTS9-H01**。

---

## 8. Participant Commit Order Audit

candidate selection 与 commit order 是两个概念。

候选身份：

```text
same camp as FINAL_ACTUAL_DAMAGE_TARGET
alive at transaction planning
not actualTarget
not isolated / not source-excluded
```

planned identities 排序：

```text
Slot 0 commander
→ Slot 1 deputy
→ Slot 2 deputy
```

然后按该顺序 micro-commit；`actualTarget` 和轮到时当前失效的 planned identity 被跳过。

无 RNG，不按当前兵力、不按速度、不按添加状态时间排序。

正式 commit topology：

```text
calculate once
→ participant slot 0
→ participant slot 1
→ participant slot 2
→ target Dtarget
```

这正是：

```text
DISTRIBUTION = PARTICIPANTS_FIRST_COMMIT
```

不得被 DAMAGE_SHARE family abstraction 改写成 target-first。

---

## 9. Participant Death / Overflow Audit

### 9.1 Overflow

每个 participant：

```text
ActualParticipantTroopLoss
= min(Dparticipant, participant.currentTroops)
```

理论 overflow：

```text
DISCARD
```

明确：

```text
NO redistribution
NO target return
NO transfer to later participant
NO Share recursion
NO Distribution recursion
NO statistics for overflow
NO wounded for overflow
```

### 9.2 Ordinary participant death

P0 §7.1 直接冻结：较早 participant 因本次 direct loss 死亡后，当前 commit 完成，后续普通 participant 继续，原 target 最后继续。

因此对于 deputy / non-battle-ending participant death：

```text
CONTINUE = FROZEN
```

### 9.3 Commander participant death

本轮专门搜索了当前 repository evidence mapping。`CLAIM_EVIDENCE_INDEX.csv` 有 EM-21 commander-death、EM-19 Share target-death 等映射，但没有 Distribution commander-participant death 的 controlled sample；Distribution Freeze Record §7.1 也没有提供一个“participant #1 = commander and dies”的直接样本编号。

R5 只证明两类一般模型都真实存在：

```text
action executor dies → immediate hard stop
multi-target / Chain target commander dies → current atomic loop completes, then finalization
```

它没有把 Distribution ordered micro-commit transaction 分类进其中任一类。

因此不能仅凭 §7.1 的普通 `participant death does not abort` 文义，自动推导：

```text
commander participant dies
→ later participant definitely commits
→ original target definitely commits
→ only then battle finalizes
```

也不能反向自动推导立即终战。

这会直接改变兵损与胜负前世界状态，属于 implementation-blocking。

Result: **DSTS9-B02**。

---

## 10. Target Commit Audit

所有 participant micro-commits 完成后：

```text
ActualTargetTroopLoss
= min(Dtarget, target.currentTroops)
```

原 target 才进入正常受伤后续语义。

因此：

```text
TakeDamageEvent.damage = Dtarget
```

目标正常 callback 使用 `Dtarget` 作为本 DamageEvent 的 post-partition 正常值：

```text
FirstAid → allowed if the parent DamageEvent normally permits it
Counter window → allowed if parent identity is NormalAttack and other gates pass
Chain → target-side normal post-partition Dtarget may be trigger base if eligible
ordinary hurt callbacks → target-side normal semantics
```

participant direct loss 不进入这些 callback。

### 10.1 Target death is last

因为 target commit 在 participant phase 之后：

```text
participant losses already committed
→ target commit
→ target dies
```

已提交 participant losses **不得回滚**。

Distribution 不存在 Share 的：

```text
target dies first
→ cancel pending participant loss
```

结构，因为 target 根本不是 first commit。

因此 `SHS9-B02` 不可继承，也不被 Distribution 反向证明或关闭。

---

## 11. Derived Loss Identity Audit

每个 participant 接收：

```text
Attributed Direct Troop Loss
```

不是：

```text
DamageEvent
```

所以 participant side 不重新进入：

```text
Defense
DamageModifier
Evasion
Resistance
FirstAid
Counter
Chain
DAMAGE_SHARE
DISTRIBUTION
Cleave
ordinary OnTakeDamage / OnHurt
Lifesteal trigger path
StrategyRecovery trigger path
```

但 direct troop loss 仍必须产生其本职事实：

```text
troop mutation
death fact
commander-death condition
wounded processing
statistics
kill attribution
```

死亡事实与 hurt callback 必须分离；“不是 DamageEvent”不等于“不会死”。

### 11.1 Recursion matrix

| Distribution participant loss → | Verdict | Reason |
|---|---|---|
| Distribution | BLOCKED | direct troop loss, not DamageEvent |
| Damage Share | BLOCKED | same |
| Chain | BLOCKED | same |
| Counter | BLOCKED | same |
| FirstAid | BLOCKED | same |
| Cleave | BLOCKED | same |
| Lifesteal | BLOCKED | participant loss is not the attacker's normal DamageEvent value |
| StrategyRecovery | BLOCKED | same |
| ordinary hurt callback | BLOCKED | same |

---

## 12. Lifecycle / Reapplication Audit

### 12.1 Same source

Known natural source is 【义心昭烈】。

```text
same-source reapplication = REFRESH
one effective instance
```

成功 refresh：

```text
duration/current instance refreshed
ratio snapshot recalculated or replaced according to source effect rule
runtime attribute changes do not mutate the already stored ratio
```

source skill 如何计算 `R` 属 source-skill responsibility，不属于 Distribution kernel。

### 12.2 Cross source

当前没有第二种自然 Distribution 来源可做真实 cross-source observation。

P0 已正确标注：

```yaml
CrossSource_Behavior: REPLACE
Evidence: INHERITED_FROM_DAMAGE_SHARE_FAMILY_CONTRACT
Empirical_Observability: CURRENTLY_UNAVAILABLE
Implementation_Blocking: false
```

审计结论：

```text
ENGINEERING DEFAULT = ACCEPTABLE
OFFICIAL BATTLE-REPORT CONFIRMED = NO
BLOCKER = NO
```

未来出现第二自然来源时应重新验证，但当前不制造假 blocker。

### 12.3 Duration / operational lifecycle

固定 duration 继承 Share family：

```text
owner = protected target
tick = protected target ACTION_START / Turn Start
expire before later periodic damage / normal action resolution
```

apply-round 的相对时序也继承：若本回合在 target Turn Start 前施加，本回合该 Turn Start 可消耗一次；若之后施加，则下一次 target Turn Start 才首次消耗。

`state.exists != state.isOperational()` 保持成立。普通控制不应把被动 partition 错当作“必须主动行动才能工作”；若引擎进入 protected-target ACTION_START，duration tick 由该 lifecycle window 所有，而非由“最终是否成功执行主动动作”所有。

source-bound / condition-bound instance 是否 operational 继续由 source effect 语义决定；False Report 等 source suppression 不等于普通 Dispel。

生命周期对当前已知来源足以实现，唯一明显越权位于 protected-target death outer-action wording，见 DSTS9-M01。

---

## 13. Share Precedence Audit

冻结优先级：

```text
DAMAGE_SHARE > DISTRIBUTION
```

Apply-time：

```text
Existing Share + Incoming Distribution
→ Distribution rejected / ineffective

Existing Distribution + Incoming Share
→ Share succeeds
→ Distribution replaced
```

这里：

```text
REPLACE != SUPPRESS
```

Share 结束后旧 Distribution 不自动复活。

Damage-time defensive resolver 仍应：

```text
Share
> Distribution
> None
```

但只选择一个 partition policy，不能 Share 后再 Distribution 顺序执行。

---

## 14. Attribution / Statistics / Wounded Audit

### 14.1 Attribution

常规 participant direct loss：

```yaml
physicalAttacker: ORIGINAL_ATTACKER
physicalSkill: ORIGINAL_SKILL_OR_NORMAL_ATTACK
victim: CURRENT_PARTICIPANT
creditOwner: ORIGINAL_ATTACKER
```

即使 Confusion / friendly-fire 导致原始攻击拓扑异常，也保持原始 attack provenance；Distribution 没有证据授权复制 DAMAGE_SHARE 的 cross-camp special credit rerouting。

### 14.2 Statistics

统计读取实际 commit：

```text
sum(ActualParticipantTroopLoss)
+
ActualTargetTroopLoss
```

不读取：

```text
Dtransfer theoretical pool
uncommitted Dparticipant
participant overflow
rounding remainder
```

因为 double rounding 允许理论总分配与 `Dtotal` 有整数差，所以统计层不得“修正回 Dtotal”。

### 14.3 Wounded

participant：

```text
WoundedGenerationBase = ActualParticipantTroopLoss
```

target：

```text
normal target wounded base = ActualTargetTroopLoss
```

具体 wounded ratio / integerization / dead-vs-wounded conversion 不属于 Distribution contract。

### 14.4 Recovery basis

Distribution 本地身份规则给出唯一可接受的 partition-side解释：

```text
participant direct loss
→ not a DamageEvent
→ not a Lifesteal / StrategyRecovery input

target normal DamageEvent
→ post-partition value = Dtarget
```

因此在 Distribution 自身边界内，attacker recovery 不应把 participant actual losses聚合进正常 `damage` 值。

但 690094/690095 recovery consumer 的跨机制最终合同仍由其自身阶段负责；`CLVS9-M01` 继续保持 OPEN，本轮不重复创建一个同义 Distribution MAJOR，也不宣称 Distribution 已替恢复系统完成 freeze。

---

## 15. Death / Battle Termination Audit

Distribution P0 当前生命周期段写：

```text
TARGET_DEATH
→ CLEAR_ALL_STATES
→ ABORT_REMAINING_STATE_RESOLUTION
→ ABORT_REMAINING_ACTION
→ REJECT_FUTURE_STATE_APPLICATION
```

这里把多个不同 ownership 粒度压成一条 universal death rule，和 R5 的 operation-specific 9-layer model 不兼容。

必须拆开：

```text
Distribution state operationality
physical state removal
current Distribution transaction
current DamageEvent
current Reaction
outer Action
future scheduling
battle victory finalization
```

对 Distribution 自身可以冻结：

```text
target commits last
participant commits before target remain committed
target death does not rollback participant loss
state on dead target becomes non-operational / is cleared by death lifecycle
future applications to dead target are rejected by target legality
```

但 Distribution P0 不应拥有“任何 target death 都必然 ABORT_REMAINING_ACTION”的宇宙级判断。

Result: **DSTS9-M01**。

### 15.1 Commander Death Matrix

| Scenario | Distribution behavior |
|---|---|
| earlier participant deputy dies | current commit completes; later planned participant continues; target eventually commits |
| earlier participant commander dies | **OPEN — DSTS9-B02**; transaction-vs-victory finalization precedence lacks Distribution-specific controlled evidence |
| later participant deputy dies | its commit completes; target continues |
| target deputy dies | all participant commits already permanent; target last commit kills deputy; no rollback |
| target commander dies | all participant commits already permanent; target last commit may establish victory; no rollback; outer Action/finalization follows scoped death model, not Distribution universal wording |
| victory condition becomes true during participant phase | only materially unresolved case is commander participant death; **OPEN — DSTS9-B02** |
| finalization occurs before target commit? | ordinary participant death: NO; commander participant death: **UNRESOLVED** |

---

## 16. Cross-Mechanism Consistency

| Cross Item | Verdict | Audit note |
|---|---|---|
| DISTRIBUTION × CONFUSION | CONSISTENT | Confusion changes attack provenance/targeting upstream; Distribution participants are same-camp to final actualTarget; CFS9-B01 remains open independently |
| DISTRIBUTION × TAUNT | CONSISTENT | Taunt affects NormalAttack intended target upstream; Distribution acts after final actualTarget is known |
| DISTRIBUTION × GUARD | CONSISTENT | Guard redirect happens first; participant camp/topology anchors redirected actualTarget |
| DISTRIBUTION × COMBO | CONSISTENT | each inner NormalAttack DamageEvent re-evaluates Distribution independently; CBS9-B* remain open |
| DISTRIBUTION × CLEAVE | CONSISTENT | Cleave secondary DamageEvent may enter Distribution; participant direct loss cannot trigger Cleave; CLVS9-B01 remains upstream |
| DISTRIBUTION × CHAIN | CONSISTENT | participant direct loss → Chain BLOCKED; original target post-partition `Dtarget` may be Chain trigger base if eligible; CHNS9-B01 remains independent numeric blocker |
| DISTRIBUTION × COUNTER | CONSISTENT | NormalAttack target `Dtarget` may open Counter; Counter DamageEvent itself may enter Distribution; participant direct loss → Counter BLOCKED; Counter→Counter remains blocked |
| DISTRIBUTION × DAMAGE_SHARE | CONSISTENT | mutually exclusive partition family with `Share > Distribution`; Share blockers remain open and are not inherited as answers |

### 16.1 Impact on existing findings

```text
CFS9-B01:
No new direct evidence. Remains OPEN.

CBS9-B01/B02/B03:
No new direct evidence. Remain OPEN.

CLVS9-B01/B02/B03/B04:
No new direct evidence. Remain OPEN.
Distribution confirms Cleave secondary can enter partition but does not fix Cleave base/target/lifecycle/death blockers.

CHNS9-B01:
No closure. Distribution has its own integerization gap; this strengthens the need for explicit per-mechanism numeric policy instead of language builtin assumptions.

SHS9-B01:
No closure. Distribution creates independent DSTS9-B01 in the same Stage9 numeric-policy problem family.

SHS9-B02:
Not inherited. Distribution target-last topology is structurally different and does not prove or disprove Share target-first pending-sharer cancellation.

SHS9-M01:
No closure. Distribution repeats analogous over-broad target-death wording and therefore gets its own scoped DSTS9-M01.
```

没有任何此前 OPEN blocker 因本轮 Distribution 新证据被正式关闭。

---

## 17. Stage8 Compatibility

Stage8 frozen ownership remains:

```text
DamageRequest
→ DamageSystem calculation / modifiers / finalization
→ DamageResult(final theoretical damage)
→ DamageResolutionSystem
→ TroopSystem mutation
```

Distribution 的兼容扩展 seam 可以放在：

```text
DamageResult.final_damage
→ Stage9 DamagePartition selection
→ Distribution participant settlement plan
→ ordered attributed troop-loss micro-commits
→ original target normal commit
```

Stage9 partition extension 至少需要表达：

```text
partition kind
participant identity plan
fixed participant assigned amount
fixed target assigned damage
provenance
commit order
JIT participant eligibility gate
```

禁止：

```text
Stage8 target troop commit first
→ later patch participant transfers
```

因为那会直接把 participants-first 改成 target-first。

只要 Stage9 在 `DamageResult.final_damage → coordinated troop commits` 之间扩展 resolution，不改变 Stage8 base formula / modifier ownership：

```text
FORMAL STAGE8 REOPEN = NO
```

本轮没有发现 DSTS9-B candidate 6。

---

## 18. Documentation Drift

### DSTS9-D01 — state research repo still exposes 690086 only as MINIMUM_USABLE

State repo index/skeleton 仍把 690086 标为 `MINIMUM_USABLE`，并继续把 ratio / eligibility / ordering 等列为 unresolved；battle repo 已有 695 行正式 FROZEN P0。

这不是 dual-P0 conflict，因为 state file 自己明确“不构成正式冻结合同”；但跨仓导航状态已经滞后。

Result: **DSTS9-D01**。

### DSTS9-D02 — STAGE9_EVIDENCE_MATRIX_V2 is not post-Distribution-freeze synchronized

Evidence Matrix 标题称 `Post Freeze Sync`，但：

- header 的“后续冻结记录”只列 Cleave / Chain；
- Share math 仍写“尚未作为本轮 Share Core Frozen”；
- 当前研究状态仍写 `Share Core Mechanics = NEXT RESEARCH TARGET`；
- 没有 Distribution 当前 P0 的专门 row / current status entry。

该文件已被 README 明确降级为历史统计证据矩阵、Freeze Record 优先，因此不会覆盖 P0，也不形成 implementation blocker；但文档名与“Post Freeze Sync”表述已经落后于实际冻结历史。

Result: **DSTS9-D02**。

### 18.1 R3 / R4 / R5 / R6 authority note

R3/R4/R5/R6 是历史专题/总则型 authority。当前 README 已明确：Share/Distribution/Counter 的最终机制以对应 Freeze Record 为准。因此这些文件未逐条复制 Distribution 新合同不自动算 P0 divergence。

其中 R5 的 death model 对 commander participant death 只能提供两种可能模式，不能替 Distribution 做 micro-transaction classification；这正是 DSTS9-B02 的原因，而不是 R5 本身的 doc drift。

---

## 19. Findings

### BLOCKER

#### DSTS9-B01 — Distribution exact integerization policy is undefined at both round sites

**Status:** OPEN

```text
RoundTarget(x.5) = ?
RoundParticipant(x.5) = ?
```

当前没有项目级统一 numeric rule，也没有 Distribution direct evidence 给出 tie semantics。两处 round 共同记录为一个缺失的 Distribution integerization policy blocker。

**Required closure:** narrow re-freeze exact tie behavior for both call sites; explicitly state whether they share one policy. Do not delegate semantics to programming-language builtin.

---

#### DSTS9-B02 — commander participant death continuation / battle-finalization boundary is not proven

**Status:** OPEN

普通 participant death continuation 已冻结；但 repository evidence mapping 没有 controlled Distribution case：

```text
participant #1 = commander
participant #1 theoretical loss > current troops
participant #1 dies
participant #2 remains eligible
target remains alive
```

R5 同时存在 immediate-abort 与 atomic-loop-delayed-finalization 两种真实模式，无法唯一分类 Distribution ordered micro-commit transaction。

**Required closure:** direct battle-report sample, stronger Distribution-specific P0 evidence, or explicitly downgraded simulator-policy decision establishing whether later participants and original target still commit after commander participant death.

---

### MAJOR

#### DSTS9-M01 — protected-target death clause over-owns outer Action termination

**Status:** OPEN

Distribution P0 把 target death 直接扩张为 unconditional `ABORT_REMAINING_ACTION`。该 wording 与 R5 operation-specific termination model、现有 Combo/Chain death exceptions 不兼容。

Distribution 只能拥有自己的 state/transaction semantics；outer Action / Reaction / battle finalization 必须由更高层 death scheduler 决定。

已提交 participant losses 在 target-last death 后不得 rollback，这一点不受该 wording 缺口影响。

---

### MINOR

```text
NONE
```

---

### DOC_DRIFT

```text
DSTS9-D01
state repo 690086 remains MINIMUM_USABLE / skeleton-only despite battle P0 FROZEN

DSTS9-D02
STAGE9_EVIDENCE_MATRIX_V2 remains pre-Share/Distribution-freeze in several status rows despite Post Freeze Sync title
```

---

### HARDENING

#### DSTS9-H01 — encode fixed transaction plan + JIT slot gate as separate invariants

**Status:** NON-BLOCKING

P0 已足以解析 N timing，但实现/测试应显式区分：

```text
plan identities once
N once
Dparticipant once
JIT gate per planned identity
no newly eligible join
no recompute after skip
next Damage Instance rebuilds plan
```

这是防止代码层误读 `DAMAGE_TIME_DYNAMIC` 的 hardening，不需要 re-freeze。

---

### Finding count

```text
BLOCKER: 2
MAJOR: 1
MINOR: 0
DOC_DRIFT: 2
HARDENING: 1
TOTAL NEW FINDINGS: 6
```

---

## 20. Final Verdict

# REOPEN REQUIRED

更精确地说：

```text
NARROW REOPEN REQUIRED
```

需要重新封口的核心范围仅为：

```text
1. DistributionIntegerizationPolicy
   - RoundTarget exact x.5 rule
   - RoundParticipant exact x.5 rule

2. Commander participant death
   - does current Distribution transaction finish?
   - do later participant commits execute?
   - does original target Dtarget commit execute?
   - when does commander-death battle finalization occur?

3. Protected-target death wording
   - scope state removal / current transaction / DamageEvent / Reaction / outer Action / finalization separately
```

已经足够稳定、无需重开的 Distribution kernel：

```text
Dtotal = post-formula normal DamageEvent value
Dtarget = round(Dtotal × (1 - R))
Dtransfer = Dtotal - Dtarget
Dparticipant = round(Dtransfer / N)

participant topology = same camp as FINAL_ACTUAL_DAMAGE_TARGET
participant identity plan = per Damage Instance
N = fixed once per Distribution transaction
participant eligibility = JIT recheck per planned slot
newly eligible mid-transaction unit = does not join
invalid planned participant = skip without recompute/redistribution

commit order = participant Slot ASC → target
ordinary participant death = does not abort remaining Distribution
participant overflow = discard
participant loss identity = Attributed Direct Troop Loss
participant hurt/partition/reaction recursion = blocked
target commit = normal DamageEvent with Dtarget
participant losses already committed before target death = never rollback

DAMAGE_SHARE > DISTRIBUTION
Share and Distribution never sequentially partition one Damage Instance
```

Stage8 conclusion：

```text
FORMAL STAGE8 REOPEN = NO
```

Distribution 可以通过 Stage9 partition/resolution extension seam 插入 `DamageResult.final_damage` 与 troop commits 之间，不需要修改 Stage8 基础公式或 modifier ownership。

### Relation to Share findings

```text
SHS9-B01
= same broad Stage9 numeric-policy problem family
!= answer to Distribution
→ DSTS9-B01 independently required

SHS9-B02
= Share target-first death-interrupt evidence gap
!= Distribution participant-first rule
→ not inherited, not closed

SHS9-M01
= Share outer-action over-ownership wording
Distribution has analogous wording problem
→ DSTS9-M01 independently recorded
```

### Prior audits impact

本轮没有直接证据足以关闭：

```text
CFS9-B01
CBS9-B*
CLVS9-B*
CHNS9-B01
SHS9-B01
SHS9-B02
SHS9-M01
```

DISTRIBUTION 唯一新增的结构性启示，是再次证明“死亡终止”和“取整”都必须按机制/operation scope 冻结，不能靠一句 universal rule 或一个语言 builtin 糊过去。

### Next mechanism

```text
COUNTERATTACK
```
