# Stage 9 核心底层裁决全景总规 (v2 - Repaired)

> **项目**: 三国志战略版战斗模拟器 V2  
> **研究基线 Commit**: `de80a4ec30fb3bf50220a719011478116bd34e5b` (main)  
> **数据基线**: 全盘扫描 32,660 份战报（逾 1,400 万条原始事件流）  
> **状态**: `REPAIRED — CLEAVE / CHAIN / SHARE / DISTRIBUTION / COUNTERATTACK CORE MECHANICS FROZEN`  
> **群攻机制冻结记录**: `STAGE9_CLEAVE_MECHANICS_FREEZE_RECORD.md`  
> **铁索机制冻结记录**: `STAGE9_CHAIN_MECHANICS_FREEZE_RECORD.md`  
> **分担机制冻结记录**: `STAGE9_DAMAGE_SHARE_MECHANICS_FREEZE_RECORD.md`  
> **分摊机制冻结记录**: `STAGE9_DISTRIBUTION_MECHANICS_FREEZE_RECORD.md`  
> **反击机制冻结记录**: `STAGE9_COUNTERATTACK_MECHANICS_FREEZE_RECORD.md`  
> **最高原则**: 
> 1. 反例优先、控制变量优先、直接证据优先；
> 2. 严禁将 NOT OBSERVED 写成 BLOCKED；
> 3. 严禁把工程设计表述为官方内部实证；
> 4. 严禁把统计模型兼容断言为官方机制证明；
> 5. 跨文档同一机制只能存在单一一致结论；
> 6. 后续逐项直接确认的 Frozen 机制结论若与旧统计推论冲突，以最新冻结记录为准。

---

## 核心裁决原则全览 (12 个问题域统一裁决)

### 1. 目标选择与重定向总顺序 (R2)
- **流水线**: 存活池 → 阵营过滤 → 混乱判定 (JIT 即时) → 嘲讽/锁定检查 (若未混乱) → 意图目标 → 援护拦截 → 受击承伤者。
- 混乱压制嘲讽、援护重定向、自援护等仍维持既有研究结论；最终证据评级仍受 Stage 9 提取器最后语义审计约束。
- Share / Distribution 均只检查援护等重定向后的 `FINAL_ACTUAL_DAMAGE_TARGET`，不得回头读取原始意图目标的状态。
- Counter 只由最终实际承受普通攻击的实体进入 `ON_NORMAL_ATTACK_RECEIVED` 触发窗口；援护 / 嘲讽改变实际受击者后，由新的实际承受者检查自身反击列表。

### 2. 目标身份三级解耦 (R2)
必须解耦：
1. `pre_redirect_target`：攻击意图目标；
2. `post_redirect_attack_target`：实际动作受体；
3. `damage_recipient(s)`：最终兵力实际扣除实体。

群攻以 `post_redirect_attack_target` 为中心向其余合法副目标派生。

Share / Distribution 会在正常伤害公式完成后进一步把一个 Damage Instance 的最终兵力承担实体扩展为多个 `damage_recipient(s)`。

Counter 则在实际普通攻击承受者存活时，以原攻击者作为新的 Counter damage target 创建独立兵刃效果伤害。

### 3. 普通攻击完整生命周期 (R1 + Frozen Records)
普通攻击生命周期在 Chain / Counter 冻结后正式收敛为：

```text
Main normal-attack damage
→ defender death check
→ defender immediate post-hit reactions such as FirstAid
→ if main target has Chain and Cleave exists: defer main-target Chain
→ resolve Cleave target 1
   → Cleave damage
   → target Chain INLINE if eligible
→ resolve Cleave target 2
   → Cleave damage
   → target Chain INLINE if eligible
→ Cleave complete
→ execute main-target Deferred Chain if still eligible
→ build and consume CounterBatch if defender eligible
→ if original attacker alive: Assault
→ if original attacker alive: Combo next-hit dispatch
```

无 Cleave 时，主目标合法 Chain 在主伤害后 INLINE，并先于 Counter。

Share / Distribution 属于单个 Damage Instance 内部的伤害分流阶段，不是新的攻击动作。

Counter 以 `PER-NORMAL-ATTACK-INSTANCE` 为粒度；连击第二击是新的 NormalAttack Instance，因此拥有独立的新 Counter 触发窗口。

### 4. 反应队列 / 时序架构 (R1 + Frozen Records)
- 采用**阶段优先级 + 局域 Inline 回调 + 少量显式 Deferred 资格 + Counter Reaction Batch**。
- Chain 默认 `PER-DAMAGE INLINE`。
- 普通攻击主目标在存在群攻时是目前已确认的 Chain Deferred 特例。
- Deferred Chain 不是固化伤害事件，而是待执行资格；执行时重新检查源节点存活与当前 Chain 状态。
- Deferred Chain 固定触发伤害值，但 owner / ratio / effect metadata 在执行时读取当前有效 Chain 状态。
- Share / Distribution 均按 `PER-DAMAGE INSTANCE` 实时校验，不在技能开始时整体快照可用承担关系。
- Counter 在 `ON_NORMAL_ATTACK_RECEIVED` 时一次性快照当前 operational CounterStates 形成 `CounterBatch`；入队资格锁定，但每个 Counter microstep 在执行时读取实时世界状态。
- CounterBatch 不是原子宏；C1 的急救、铁索等即时下游反应可以在 C2 之前改变世界状态。

### 5. 跨机制递归许可矩阵 (R4 + Frozen Records)

已冻结：

```text
Cleave → Cleave = BLOCKED
Cleave → Counter = BLOCKED
Cleave → Share = ALLOWED
Cleave → FirstAid = ALLOWED
Cleave → Chain = ALLOWED

Counter → Counter = BLOCKED
Counter → Assault = BLOCKED
Counter → Cleave = BLOCKED
Counter → Chain = ALLOWED
Counter → FirstAid = ALLOWED
Counter → Lifesteal = ALLOWED
Counter → Crit = ALLOWED
Counter → Evasion = ALLOWED
Counter → Resistance = ALLOWED
Counter → Share = ALLOWED
Counter → Distribution = ALLOWED (inherited from Distribution DamageEvent contract)

Chain → Chain = BLOCKED
Chain → Share = BLOCKED
Chain → Distribution = BLOCKED
Chain → FirstAid = BLOCKED
Chain → Counter = BLOCKED
Chain → Crit = BLOCKED
Chain → Lifesteal = BLOCKED
Chain → StrategyRecovery = BLOCKED
Chain → 刚烈不屈等受击响应 = BLOCKED

Share derived loss → Share = BLOCKED
Share derived loss → Distribution = BLOCKED
Share derived loss → FirstAid = BLOCKED
Share derived loss → Counter = BLOCKED
Share derived loss → Chain = BLOCKED
Share derived loss → 刚烈不屈等受击响应 = BLOCKED

Distribution participant derived loss → Share = BLOCKED
Distribution participant derived loss → Distribution = BLOCKED
Distribution participant derived loss → FirstAid = BLOCKED
Distribution participant derived loss → Counter = BLOCKED
Distribution participant derived loss → Chain = BLOCKED
Distribution participant derived loss → 普通受击响应 = BLOCKED
```

`Counter → Counter` 已由反击专题直接冻结为 BLOCKED：反击伤害属于标准兵刃效果伤害，但没有 NormalAttack identity，因此不满足 Counter 的触发门禁。

### 6. 派生伤害 / 分流数学语义 (R3 + Frozen Records)

#### 6.1 SPLIT / DAMAGE_SHARE — FROZEN

```text
Dsharer = round(Dtotal × R)
Dtarget = Dtotal - Dsharer
```

关键性质：

```text
single sharer
share portion calculated first
target takes remainder
target-first commit
```

理论拆分满足：

```text
Dtarget + Dsharer == Dtotal
```

#### 6.2 DISTRIBUTION — FROZEN

```text
participants = current legal same-camp alive non-target units
N = participants.count
```

若 `N == 0`：

```text
Dtarget = Dtotal
no effective distribution
```

若 `N > 0`：

```text
Dtarget = round(Dtotal × (1 - R))
Dtransfer = Dtotal - Dtarget
Dparticipant = round(Dtransfer / N)
```

每个承担者使用相同 `Dparticipant`，不使用最后一人吃余数规则。由于第二次独立取整，不要求：

```text
Dtarget + N × Dparticipant == Dtotal
```

#### 6.3 COUNTERATTACK — FROZEN

反击不是触发普通攻击伤害的比例派生：

```text
CounterDamage != TriggeringNormalAttackDamage × CounterRatio
```

而是：

```text
CounterDamage
= IndependentWeaponDamageResolution(
    source = CounterOwner,
    target = OriginalNormalAttacker,
    sourceSkill = CounterSourceSkill,
    skillRate = CounterState.damageRate,
    runtimeContext = LIVE
  )
```

反击专题 14,756 组普通攻击伤害 ↔ 反击伤害匹配对的皮尔逊相关系数为 `-0.0165`，并存在普通攻击实际损失为 0 但反击仍造成正伤害等直接反例。

#### 6.4 TRANSFER / Guard
援护属于动作级重定向，继续维持既有研究框架。

#### 6.5 COPY / Cleave — FROZEN

```text
CleaveDerivedDamage = MainAttackFinalDamage × CleaveRatio
```

群攻继承原攻击 DamageType，并使用自身许可矩阵。

#### 6.6 TRUE_FEEDBACK / Chain — FROZEN

```text
ChainCalculatedDamage = TriggerNodeResolvedDamage × CurrentChainRatio
```

Chain 为独立 `TRUE_FEEDBACK` 类型，不继承原始兵刃 / 谋略 DamageType。

每个合法同阵营传播目标都独立获得完整比例，不做均分。

### 7. 理论 / 计算伤害 vs 实际兵力损失

群攻：使用主攻击最终结算伤害作为派生基数。

铁索：

```text
ChainCalculatedDamage = TriggerNodeResolvedDamage × CurrentChainRatio
AppliedTroopLoss = min(ChainCalculatedDamage, CurrentTroops)
CreditedDamage = AppliedTroopLoss
```

分担：

```text
ActualTargetTroopLoss = min(Dtarget, target.currentTroops)
ActualSharerTroopLoss = min(Dsharer, sharer.currentTroops)
```

若 target 在 target-first commit 后死亡，则 pending `Dsharer` 整笔丢弃。

分摊：

```text
ActualParticipantTroopLoss = min(Dparticipant, participant.currentTroops)
ActualTargetTroopLoss = min(Dtarget, target.currentTroops)
```

承担者 overflow 直接丢弃，不返还目标、不重新分配给其他承担者。

反击：目标存活时按独立兵刃伤害管线提交实际兵力损失；若某个已入队 sibling Counter 轮到执行时原攻击者已死亡，则该 Counter Execute 事件仍存在，但实际提交兵力损失固定为 0。

所有冻结机制的战后伤害统计均以**实际成功提交的兵力损失**为基础，而不是理论 overkill / overflow / 未提交份额。

### 8. 派生伤害 / 分流 Pipeline (R3 + Frozen Records)

#### 8.1 Cleave — FROZEN

```text
MainAttackFinalDamage
→ × CleaveRatio
→ CleaveDerivedDamage
→ Evasion
→ Barrier
→ no target-side damage modifier re-entry
→ Share if present
→ Troop Loss
→ allowed recovery callbacks
```

群攻：
- 可规避；
- 可抵御并消耗一次抵御；
- 不重新吃副目标自身伤害增减；
- 可分担；
- 可急救；
- 兵刃型可按规则倒戈，谋略型可按规则攻心；
- 不反击、不群攻自递归。

#### 8.2 Chain — FROZEN

```text
TriggerNodeResolvedDamage
→ × CurrentChainRatio
→ TRUE_FEEDBACK
→ no Evasion
→ no Barrier
→ no target-side damage modifier
→ no Share / Distribution
→ no Crit reroll
→ restricted troop-loss settlement
→ no hit-response callback chain
```

Chain 不触发急救、反击、倒戈、攻心、刚烈等响应，也不再次触发 Chain。

#### 8.3 DAMAGE_SHARE — FROZEN

```text
TARGET_SELECTION
→ GUARD / REDIRECT
→ FINAL_ACTUAL_DAMAGE_TARGET
→ EVASION / RESISTANCE upstream gate
→ normal damage formula
→ Dtotal
→ Share partition
→ target commits Dtarget
→ target death check
→ if target alive: sharer commits attributed direct troop loss
```

合法 `Dtotal = 0` 不等于事件取消；虚弱 0 伤害仍可执行 0 值分担。

#### 8.4 DISTRIBUTION — FROZEN

```text
TARGET_SELECTION
→ GUARD / REDIRECT
→ FINAL_ACTUAL_DAMAGE_TARGET
→ EVASION / RESISTANCE upstream gate
→ normal damage formula
→ Dtotal
→ Damage-Time participant set evaluation
→ calculate Dtarget / Dtransfer / Dparticipant
→ participants Slot ASC commit
→ original target commits Dtarget last
```

某个承担者死亡不会中断后续承担者或目标提交。

#### 8.5 COUNTERATTACK — FROZEN

```text
NormalAttack damage committed
→ defender survives
→ defender immediate post-hit reaction
→ Cleave / relevant Chain branches complete
→ snapshot operational CounterStates into CounterBatch
→ for each queued Counter:
     emit CounterExecute
     if original attacker already dead:
         commit attributed 0 troop loss
         continue sibling Counter batch
     else:
         resolve independent WEAPON effect damage using LIVE context
         resolve allowed Counter downstream reactions
→ after CounterBatch:
     if original attacker dead:
         cancel pending Assault / Combo / later attacker-owned action
     else:
         continue Assault / Combo lifecycle
```

反击本身不具有 NormalAttack identity，因此不会派生突击、群攻或再次反击。

### 9. 战报因果溯源结构 (R8)
继续区分：
1. `LOG FACT`：原始平铺战报；
2. `RECONSTRUCTED MODEL`：从日志重建动作 / 反应边界；
3. `ENGINEERING MODEL`：模拟器内部 `root_action_id`、reaction provenance、timing policy、CounterBatch 等实现字段。

不得把工程字段宣称为官方内部调用栈事实。

Share / Distribution 的承担者损失必须保留：

```text
physicalAttacker
physicalSkill
victim
creditOwner
```

正常同阵营分流下 `creditOwner = original attacker`；Share 的跨阵营反向分担特例按其冻结记录可发生 credit rerouting。

Counter 归因：

```text
physicalAttacker = counter owner
physicalSkill = counter source skill
victim = original normal attacker
creditOwner = counter owner
sourceType = COUNTER
DamageType = WEAPON
NormalAttackIdentity = false
```

### 10. 死亡与终战边界 (R5 + Frozen Records)

Chain 已确认：

```text
Trigger node dies from triggering damage
→ Chain does not start

Deferred Chain source dies before execution
→ Cancel

One feedback target dies
→ only that target settlement ends
→ remaining legal targets continue
```

Share 已确认：

```text
calculate Dtarget / Dsharer
→ target commit first
→ if target dies:
     discard pending Dsharer
     stop Share branch
```

Distribution 已确认：

```text
participants commit first by Slot ASC
→ participant death only ends that participant settlement
→ later participants continue
→ original target commits last
```

承担者死亡后，下一笔 Damage Instance 的 Distribution participant set 会在 Damage-Time 动态重算。

Counter 已确认：

```text
Normal attack kills Counter holder
→ no CounterBatch

C1 Counter kills original attacker
→ already-enqueued sibling C2/C3 CounterExecute events are NOT cancelled
→ dead target receives 0 actual troop loss from later queued Counters
→ after CounterBatch, pending original-attacker Assault / Combo are cancelled
→ remaining attacker-owned action aborts
```

因此死亡不会机械清空“当前已经入队的所有 sibling reaction”，但会使死亡实体未来尚未执行的 owner-driven action branch 失效。

其余 Battle Victory / commander death / skill-loop 等总终战规则仍维持既有 R5 研究状态。

### 11. 多来源冲突与状态生命周期 (R6 + Frozen Records)

#### 11.1 Chain 单实例覆盖 — FROZEN

同一目标铁索不可多份并存：

```text
same owner reapply
→ refresh / overwrite
→ duration reset to 2

other owner reapply
→ later state overwrites earlier state
→ owner / ratio / metadata become later state
→ duration reset to 2
```

每次合法伤害仍只产生一次 Chain。

#### 11.2 DAMAGE_SHARE 单实例与优先级 — FROZEN

```text
Effective_Instance_Limit = 1
same source reapply = REFRESH_AND_REPLACE
cross source reapply = REPLACE
```

并冻结：

```text
DAMAGE_SHARE > DISTRIBUTION
```

即已有 Share 时 incoming Distribution 无效；已有 Distribution 时 incoming Share 成功并替换 Distribution。

#### 11.3 DISTRIBUTION 单实例 — FROZEN / inherited non-blocking edge

```text
Effective_Instance_Limit = 1
same source reapply = REFRESH
```

当前真实资料中没有可自然观察的第二独立 Distribution 来源，因此：

```text
cross source reapply = REPLACE
```

属于从 DAMAGE_SHARE 家族继承的非阻塞实现规则，不能宣称已被真实跨来源战报直接证明。

#### 11.4 COUNTERATTACK 多实例 — FROZEN

Counter 与 Share / Distribution 不同，必须使用多实例列表：

```text
counterStates: List<CounterState>
```

冻结：

```text
different Counter sources coexist
all operational sources can enter one CounterBatch
same-source reapply = REFRESH, not duplicate stack
```

已观察到同一次普通攻击连续执行多个不同来源 Counter 共 198 次。

Counter finite duration 由持有者自身 `ACTION_START` tick；False Report 可使来源相关 Counter `state.exists == true` 但 `state.isOperational() == false`，压制结束后仍有效的状态恢复运行。

Counter 净化不作为负面状态清除；统一 Dispel 语义尚无足够直接证据，按来源效果 dispellability 处理，属于非阻塞 deferred 项。

#### 11.5 Duration / operational distinction

Share / Distribution / Counter 都必须能够表达：

```text
state.exists
!=
state.isOperational()
```

Share / Distribution 固定持续回合状态由 protected target 自身 ACTION_START 管理 duration；Counter 固定持续回合状态由 Counter holder 自身 ACTION_START 管理。

Share 的 sharer 死亡会即时使后续 Share operational check 失败；Distribution 的 participant 死亡在下一次 Damage-Time participant evaluation 中动态排除；CounterBatch 入队后则不因目标中途死亡撤销已入队 sibling Counter。

### 12. 确定性与 RNG (R7 + Frozen Records)

Chain 多目标传播**不使用 RNG**，按固定槽位：

```text
slot 0 → slot 1 → slot 2
```

Distribution 多承担者提交同样采用：

```text
slot 0 → slot 1 → slot 2
```

跳过 original target 与当前不合法承担者。

每一笔 Damage Instance 的 Distribution participant set 都是 JIT 动态读取。

Counter 多来源执行顺序已确认具有确定性，并存在稳定 pairwise ordering；但尚未完整反演所有可能 Counter 来源之间的官方全局 comparator。模拟器应采用与已观察 pairwise order 一致的稳定 source registration / source-slot priority；该 comparator 细节属于 `DEFERRED_NON_BLOCKING`。

连击第二击重新索敌与严格 transition matrix 的统计封口仍属于 R7 独立问题。

---

## Chain 触发资格汇总

可以触发：

```text
Normal Attack Damage
Skill Damage
Periodic Damage
Cleave Damage
Counter Damage
```

明确不能触发：

```text
Chain TRUE_FEEDBACK
Share Passive Numeric Settlement
Distribution Participant Passive Numeric Settlement
```

0 伤害的合法伤害结算仍会执行 Chain，只是反馈伤害为 0。

---

## Counter 核心运行摘要

```text
Trigger:
ON_NORMAL_ATTACK_RECEIVED only
PER-NORMAL-ATTACK-INSTANCE

Identity:
WEAPON EFFECT DAMAGE
NOT NormalAttack

Batch:
trigger-time eligibility snapshot
execution-time live world evaluation
multiple different sources can coexist
same source refreshes

Timing:
after normal-attack-derived Cleave / Chain
before Assault
before Combo next hit

Death:
normal attack kills holder -> no Counter
C1 kills attacker -> queued C2 still executes with 0 loss
attacker dead after batch -> pending Assault / Combo cancelled

Blocked:
Counter → Counter
Counter → Assault
Counter → Cleave

Allowed:
Crit / Weakness / Evasion / Resistance
Share / Distribution
FirstAid / Chain / Lifesteal
standard weapon-damage hit responses
```

---

## Share / Distribution 家族关键差异

```text
DAMAGE_SHARE
- topology: one linked sharer
- calculation: Dsharer first, target takes remainder
- commit: target first, sharer second
- target death: interrupts pending sharer commit

DISTRIBUTION
- topology: dynamic multi-participant set
- calculation: Dtarget first, transfer pool then equal participant share
- commit: participants Slot ASC first, target last
- participant death: does not abort later commits
```

两者共同点：

```text
post-normal-formula partition
not ordinary DamageReductionModifier
derived participant loss is not second normal DamageEvent
actual committed troop loss drives statistics / wounded processing
```

---

## 与 Stage 8 Frozen Contract 边界评估

1. **Counter**: 独立标准兵刃效果伤害；使用已有 Weapon Damage Formula，但自身不具有 NormalAttack identity；以多实例 Reaction Batch 表达时序与来源。
2. **Cleave**: 固定派生值，跳过 Base Formula，使用 Cleave 专属许可矩阵。
3. **Chain**: `TRUE_FEEDBACK`，跳过 Base Formula，并且进一步跳过 Evasion / Barrier / Modifier / Share / Distribution / hit callback 层，使用受限直接数值结算。
4. **Share**: post-formula single-sharer partition；target-first commit；派生承担者损失为 attributed direct troop loss。
5. **Distribution**: post-formula dynamic multi-participant partition；participants-first commit；派生承担者损失为 attributed direct troop loss。
6. **结论**: Stage 9 设计需要能够表达不同派生类型的 provenance、permission matrix、timing policy、partition topology、reaction batch 与 attribution owner。当前事实**不构成 Stage 8 Formal Reopen**。

---

## 当前冻结状态

```text
Stage 8 = FROZEN
Cleave Core Mechanics = FROZEN
Chain Core Mechanics = FROZEN
Share Core Mechanics = FROZEN
Distribution Core Mechanics = FROZEN
Counterattack Core Mechanics = FROZEN
Next Functional State Research Target = TBD
```
