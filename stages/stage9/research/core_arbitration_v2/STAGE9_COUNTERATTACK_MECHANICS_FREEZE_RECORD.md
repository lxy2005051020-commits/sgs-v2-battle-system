# Stage 9 反击 / COUNTERATTACK 核心机制冻结记录

Status ID: `690085`  
Official Name: `反击`  
English Name: `COUNTERATTACK`  
Status: `FROZEN`

Freeze Date: `2026-09-12`

本文件为 `sgs-v2-battle-system` 中 `690085 COUNTERATTACK / 反击` 的正式实现依据。

本轮冻结建立在反击专题全量扫描与微步切片之上，主要数据包括：

```text
反击专题战报：4,017 场
反击执行事件：15,060 次
普通攻击受击伤害 ↔ 反击伤害匹配对：14,756 组
双向具备反击能力战报：70 场
反击命中另一反击武将：197 次
Counter → Counter：0 次
多来源反击同一普攻连续执行：198 次
反击反杀原攻击者：341 例
多反击中 C1 致死后 C2 继续执行的关键样本：4 例
```

除本文明确标记为 `DEFERRED_NON_BLOCKING` 的两项外，690085 已无实现阻塞问题。

---

## 1. Classification

```yaml
Category: FUNCTIONAL_STATE
Family: REACTION_STATE
TriggerFamily: NORMAL_ATTACK_RECEIVED
DamageFamily: WEAPON_EFFECT_DAMAGE
NormalAttackIdentity: false
Container: MULTI_INSTANCE_LIST
Status: FROZEN
```

核心定义：

> 反击是在单位成为一次合法普通攻击的实际承受者后，于该普通攻击自己的派生结算完成、且受击者仍存活时触发的反应批次。每个已入队反击实例随后独立执行一次标准兵刃效果伤害结算，但反击本身不具有普通攻击身份。

---

## 2. Trigger Eligibility — Q01 FROZEN

反击触发门禁不是“受到兵刃伤害”，而是：

```text
ON_NORMAL_ATTACK_RECEIVED
```

正式触发条件：

```text
IncomingEvent has NormalAttack identity
AND defender is FINAL_ACTUAL_ATTACK_RECIPIENT
AND defender CounterState is operational at trigger window
AND defender survives required pre-counter boundary
```

### 2.1 允许触发

```text
标准普通攻击
连击产生的第 2 次普通攻击
援护 / 嘲讽改变目标后的实际普通攻击承受者
决斗中的交替普通攻击
```

每一次独立普通攻击实例都独立获得一次反击触发窗口：

```yaml
Counter_Trigger_Granularity: PER_NORMAL_ATTACK_INSTANCE
```

### 2.2 不允许触发

以下事件不具有 `NormalAttack` 身份，因此不满足反击触发门禁：

```text
主动战法伤害
突击战法伤害
被动 / 指挥额外伤害
群攻副目标伤害
铁索连环伤害
分担派生扣兵
分摊派生扣兵
持续伤害
反击伤害
```

### 2.3 Counter → Counter

全量检索中：

```text
双方具备反击能力战报：70
反击命中另一反击武将：197
Counter → Counter：0
```

正式冻结：

```text
COUNTER_DAMAGE.isNormalAttack = false
Counter → Counter = BLOCKED
```

禁止通过额外“防死循环补丁”实现；正确原因是反击伤害没有普通攻击事件身份。

---

## 3. Normal Attack Lifecycle Position — Q02 FROZEN

反击位于普通攻击生命周期中、突击与连击下一击之前。

### 3.1 基本时序

```text
Normal Attack Declared
→ normal damage calculation / modifiers
→ Normal Attack Damage Commit
→ defender death check
→ defender immediate post-hit reaction (e.g. FirstAid)
→ normal-attack-derived Cleave branch
→ associated Chain resolution
→ COUNTER BATCH
→ counter damage + each counter's allowed downstream reactions
→ if original attacker alive: Assault
→ if original attacker alive: Combo next-hit dispatch
```

### 3.2 死亡门禁

```text
Normal Attack Damage Commit
→ defender currentTroops <= 0
→ no Counter batch
```

普攻直接致死样本中，反击全部熔断。

### 3.3 FirstAid / Cleave / Chain / Assault / Combo 相对顺序

冻结：

```yaml
Defender_FirstAid: BEFORE_COUNTER
Cleave: BEFORE_COUNTER
NormalAttack_Derived_Chain: BEFORE_COUNTER
Assault: AFTER_COUNTER
Combo_Next_NormalAttack: AFTER_COUNTER
```

Chain 保持已冻结的 Inline / Deferred 特例：

```text
无 Cleave：main-target Chain INLINE → Counter
有 Cleave：
  defer main-target Chain
  → Cleave target(s)
  → Cleave-target Chain INLINE
  → Cleave complete
  → deferred main-target Chain
  → Counter
```

### 3.4 关键行为反证

【当锋摧决】样本确认：

```text
Counter executes
→ original attacker later launches Assault
→ False Report is applied
→ Counter becomes temporarily suppressed only after current Counter already executed
```

因此 `Counter BEFORE Assault` 为直接行为证据，而非单纯日志相邻推断。

---

## 4. Damage Basis — Q03 FROZEN

反击伤害不是从触发它的普通攻击伤害派生。

否定模型：

```text
CounterDamage = TriggeringNormalAttackDamage × Ratio
```

全量 14,756 组匹配对的皮尔逊相关系数：

```text
rho(NA_Damage, Counter_Damage) = -0.0165
```

并存在大量直接反例：

```text
Incoming normal attack actual loss = 0
→ Counter can still deal positive damage

Incoming normal attack loss ≈ 900
→ Counter can deal only single-digit damage
```

正式模型：

```text
CounterDamage
= IndependentWeaponDamageResolution(
    source = counterOwner,
    target = originalAttacker,
    sourceSkill = counterState.sourceSkill,
    skillRate = counterState.damageRate,
    runtimeContext = current live context
  )
```

冻结：

```yaml
DamageType: WEAPON
CalculationMode: INDEPENDENT_WEAPON_DAMAGE_RESOLUTION
TriggerDamageAsNumericBase: false
ExactWeaponFormula: INHERITS_BATTLE_SYSTEM_WEAPON_FORMULA
```

本合同不重新反演兵刃基础伤害公式内部的武力、统率、兵力函数和精确取整位置。

---

## 5. Counter Damage Pipeline Permission — Q04 FROZEN

反击具有：

```text
Standard Weapon Effect Damage identity
```

但不具有：

```text
NormalAttack identity
```

### 5.1 允许

直接战报支持：

```yaml
WeaponDamageIncreaseReduction: ALLOWED
Crit: ALLOWED
Weakness: APPLIES
Evasion: ALLOWED
Resistance: ALLOWED
DamageShare: ALLOWED
FirstAid: ALLOWED
Chain: ALLOWED
Lifesteal: ALLOWED
StandardWeaponDamageHitResponses: ENTERS
```

已观察到的目标受击响应包括：

```text
急救
刚烈不屈
绝地反击等受到兵刃伤害后的合法响应
```

未知特殊回调默认继承标准兵刃伤害管线，除非后续反例明确覆盖。

### 5.2 禁止

由于反击不是普通攻击：

```yaml
Assault: BLOCKED
Cleave: BLOCKED
Counter: BLOCKED
StrategyLifesteal: BLOCKED
```

### 5.3 Distribution

`Counter → Distribution` 当前没有在本反击专题中单独建立高强度直接样本，但依据已冻结 DISTRIBUTION 合同：分摊接受正常合法 DamageEvent 在终伤后进入分流阶段。

因此模拟器采用：

```yaml
Counter_to_Distribution: ALLOWED
Evidence: INHERITED_FROM_DISTRIBUTION_DAMAGE_EVENT_CONTRACT
Implementation_Blocking: false
```

不得把该条描述成“本反击专题已直接观察大量 Counter → Distribution 样本”。

---

## 6. Attribution / Lifesteal / Event Identity

常规反击：

```yaml
physicalAttacker: COUNTER_OWNER
physicalSkill: COUNTER_SOURCE_SKILL
victim: ORIGINAL_NORMAL_ATTACKER
creditOwner: COUNTER_OWNER
DamageType: WEAPON
SourceType: COUNTER
NormalAttackIdentity: false
```

反击者的倒戈可基于其实际造成的兵刃伤害正常恢复；攻心不适用于兵刃型反击。

---

## 7. Counter Kill Interrupt — Q05 FROZEN

当某次反击使原攻击者兵力归 0：

```text
Counter Damage Commit
→ original attacker death check
→ original attacker dead
→ pending attacker-owned Assault CANCEL
→ pending Combo next-hit dispatch CANCEL
→ remaining attacker-owned action window ABORT
```

全库反击反杀原攻击者样本：

```text
341 例
死后继续突击：0
死后继续连击第二击：0
```

明确携带突击且被反杀样本、以及明确存在连击状态且首击被反杀样本，同样全部中断。

死亡与状态清理本身引用全局死亡合同，不在本文件重复定义另一套死亡物理规则。

---

## 8. Multi-source Counter State Model — Q06 FROZEN

### 8.1 必须使用多实例容器

```text
counterStates: List<CounterState>
```

禁止：

```text
counterState: CounterState?
```

全库已观察到 198 次同一单位在一次普通攻击后连续执行多个不同来源反击。

已观察组合包括：

```text
后发制人 → 还击
后发制人 → 三里而还
气凌三军 → 三里而还
```

冻结：

```yaml
DifferentSources:
  Coexist: true
  Replace: false
  StrongerWins: false
  ExecuteAll: true
```

### 8.2 同源重施加

全库记录到 128 次 `反击效果已刷新`。

冻结：

```yaml
SameSource_Reapply: REFRESH
DuplicateSameSourceStack: false
```

同源实例刷新其持续时间 / 来源定义的运行元数据，不追加第二份相同来源实例。

### 8.3 多来源执行顺序

已确认执行顺序具有确定性，且已观察 pairwise order 稳定：

```text
后发制人 before 三里而还
气凌三军 before 三里而还
后发制人 before 还击
```

但当前证据不足以宣称已完整反演官方所有来源之间的全局 comparator。

冻结边界：

```yaml
ExecutionOrder_Deterministic: true
ExactGlobalComparator: DEFERRED_NON_BLOCKING
ImplementationDefault: stable source registration / source-slot priority consistent with observed pairwise order
```

---

## 9. Counter State Runtime Values — Q06 FROZEN

状态实例绑定：

```text
source identity
source skill
source damageRate
lifecycle metadata
```

每次反击执行时动态读取：

```text
counter owner current troops
counter owner current attributes
counter owner current damage modifiers
target current troops
target current defense
target current damage reduction
target current Evasion / Resistance
```

因此：

```yaml
DamageRate: SOURCE_BOUND
RuntimeCombatContext: LIVE_AT_COUNTER_EXECUTION
```

不得在反击状态施加时快照武力、统率、兵力、增减伤等运行时战斗属性。

---

## 10. Duration / Suppression / Removal — Q06 FROZEN

### 10.1 Duration

反击固定持续时间由持有者自己的 `ACTION_START` 管理。

全库 427 次“反击效果已消失”均锚定于持有者自身行动开始窗口。

```yaml
DurationOwner: HOLDER
DurationTick: HOLDER_ACTION_START
```

工程模型建议显式区分：

```text
FIXED_DURATION
PERMANENT
SOURCE_BOUND
```

不要把领域语义依赖在 `remainingTurns = -1` 之类魔法数字上。

### 10.2 False Report / Source Suppression

全库记录到 166 次“反击暂时失效”。

冻结：

```text
state exists
!=
state operational
```

```yaml
FalseReport:
  PhysicalRemoval: false
  OperationalSuppression: true
  RestoreAfterSuppressionEnds: true
```

建议统一通过：

```text
counterState.isOperational(context)
```

判断来源技能当前是否可运行，而非把伪报硬编码为 CounterState 内部专属布尔字段。

### 10.3 Cleanse / Dispel

净化不移除作为正向功能效果的反击。

对于统一 `Dispel` 语义，当前全库没有足够直接样本证明所有来源的 690085 都共享绝对 `dispellable=false`。

因此：

```yaml
Cleanse_RemovesCounter: false
Universal_Dispel_Rule: DEFERRED_NON_BLOCKING
ImplementationDefault: FOLLOW_SOURCE_EFFECT_DISPELLABILITY
```

不得把“未观察到被驱散”写成“所有 Counter 一定不可驱散”。

### 10.4 Holder death

反击持有者死亡遵循全局死亡硬终止与状态清理规则。

---

## 11. Multi-Counter Death Boundary — Q07 FROZEN

多反击不是：

```text
C1 kills attacker
→ cancel C2
```

真实外部行为：

```text
NormalAttack received
→ Counter batch has [C1, C2, ...]
→ C1 Execute
→ C1 kills original attacker
→ death event
→ C2 Execute event STILL FIRES
→ target already has 0 troops
→ C2 committed troop loss = 0
→ death confirmation can appear again
→ continue remaining already-enqueued sibling counters
```

全库捕获 4 个关键样本，均表现一致。

冻结：

```yaml
TargetDeathAfterCounterBatchCreation:
  CancelRemainingCounterExecuteEvents: false
  AlreadyQueuedCounterActualTroopLossIfTargetDead: 0
```

同时：

```text
already-enqueued sibling Counter reactions can continue
!=
original attacker can continue its own Assault / Combo
```

后者仍按 Q05 立即中止。

---

## 12. Batch Snapshot vs Live Evaluation — Q08 FROZEN

反击采用严格双阶段架构。

### Phase 1 — Trigger-Time Batch Plan Snapshot

在 `ON_NORMAL_ATTACK_RECEIVED` 触发窗口：

```text
counterBatch = all CounterStates operational NOW
```

一旦进入 batch，实例执行资格锁定：

```yaml
EligibilityEvaluation: TRIGGER_TIME
QueuedCounterSilentRemoval: false
```

Batch 锁定：

```text
Counter instance identity
source identity / source skill
damageRate / source-bound metadata
batch execution order
```

### Phase 2 — Execution-Time Live World Evaluation

每个 `Ci` 独立成为一个微步：

```text
Ci Execute
→ read live world state
→ resolve independent weapon damage if target alive
→ resolve Ci downstream callbacks
→ world may change
→ Ci+1 Execute using updated world
```

每个 Ci 执行时动态读取：

```text
owner current troops / attributes / modifiers
target current troops / defense / reduction
target current Evasion / Resistance
```

反击批次不是不可插入的原子宏；不同 Counter 之间允许插入当前 Counter 产生的即时下游反应，例如急救、铁索等。

关键实证中：

```text
C1
→ target dies
→ counter owner FirstAid heals
→ owner troops changes
→ C2 still executes
```

因此不得快照 owner troops / attributes 作为整个 CounterBatch 的统一伤害上下文。

---

## 13. Unified Runtime Contract

推荐领域结构：

```text
CounterState {
  owner
  source
  sourceSkill
  damageRate
  lifecycleType
  remainingTurns optional
}

GeneralEntity {
  counterStates: List<CounterState>
}
```

推荐运行合同：

```text
onNormalAttackReceived(defender, attacker, event):

    if !event.hasNormalAttackIdentity:
        return

    if defender.currentTroops <= 0:
        return

    counterBatch = defender.counterStates
        .filter(state => state.isOperationalAtTriggerWindow())
        .sort(stableCounterOrder)
        .toList()

    for counter in counterBatch:

        emit CounterExecute(counter)

        if attacker.currentTroops <= 0:
            commitAttributedZeroCounterLoss(
                source = defender,
                target = attacker,
                skill = counter.sourceSkill
            )
            emit deathConfirmationIfRequired(attacker)
            continue

        resolveWeaponDamage(
            source = defender,
            target = attacker,
            sourceType = COUNTER,
            skill = counter.sourceSkill,
            skillRate = counter.damageRate,
            normalAttackIdentity = false,
            runtimeContext = LIVE
        )

        # each counter resolves its own allowed downstream callbacks
        # do not re-check batch admission eligibility here

    if attacker.currentTroops <= 0:
        cancelPendingAssault(attacker)
        cancelPendingComboNextHit(attacker)
        abortRemainingAttackerOwnedAction(attacker)
        return

    continueToAssaultAndComboLifecycle()
```

注意：该伪代码是模拟器外部行为合同，不宣称官方客户端使用相同函数、字段或内部调用栈。

---

## 14. Required Regression Tests

最低必须覆盖：

```text
T01 normal attack triggers Counter
T02 combo second normal attack independently triggers Counter
T03 duel normal attack triggers Counter
T04 Cleave damage does not trigger Counter
T05 Assault damage does not trigger Counter
T06 Counter damage does not trigger Counter
T07 incoming normal attack with actual loss 0 can still trigger Counter
T08 lethal normal attack on Counter owner blocks Counter

T09 Counter uses independent weapon damage formula
T10 Counter damage is not incoming damage × ratio
T11 Counter can Crit
T12 Counter owner Weakness can yield 0 damage
T13 Counter target can Evasion
T14 Counter target can Resistance and consume resistance
T15 Counter can enter DamageShare
T16 Counter can trigger Chain
T17 Counter can trigger FirstAid on victim
T18 Counter can trigger Lifesteal on source
T19 Counter cannot trigger Assault
T20 Counter cannot trigger Cleave

T21 Counter executes before original attacker's Assault
T22 Counter executes before Combo next-hit dispatch
T23 Counter kills attacker -> pending Assault cancelled
T24 Counter kills attacker -> pending Combo next hit cancelled

T25 two different Counter sources coexist
T26 same-source Counter reapplies as refresh, not duplicate stack
T27 one normal attack can enqueue multiple Counter instances
T28 observed pairwise Counter order is deterministic

T29 C1 kills original attacker -> C2 CounterExecute still emitted
T30 C1 kills original attacker -> C2 actual troop loss = 0
T31 C1 downstream reaction can occur before C2
T32 C2 reads updated owner troops / runtime context

T33 holder ACTION_START ticks finite Counter duration
T34 False Report suppresses Counter without physical deletion
T35 suppression end restores still-valid Counter state
T36 holder death clears Counter states under global death contract
```

---

## 15. Frozen vs Deferred Boundary

### FROZEN

```text
NormalAttack-only trigger identity
PER-NORMAL-ATTACK-INSTANCE trigger granularity
actual redirected attack recipient ownership
Counter timing before Assault / Combo
independent weapon damage formula
standard weapon effect damage pipeline
Crit / Weakness / Evasion / Resistance
DamageShare / Chain / FirstAid / Lifesteal
Counter → Counter blocked
Counter → Assault blocked
Counter → Cleave blocked
multi-source coexistence
same-source refresh
multi-instance Counter batch
holder ACTION_START duration
False Report operational suppression
Counter kill aborts attacker-owned later action branches
queued sibling Counter survives target death as 0-loss execution
trigger-time eligibility snapshot + execution-time live world evaluation
```

### DEFERRED_NON_BLOCKING

```text
1. exact universal comparator across every possible Counter source
2. universal Dispel semantics across every possible Counter source
```

这两项不得阻止 690085 实现与封版；后续若出现直接反例，仅重开对应条款。

---

## 16. Freeze Gate

```yaml
Status: FROZEN
BLOCKER: 0
MAJOR: 0
Implementation_Blocking_Unresolved: 0

Deferred_NonBlocking:
  - Exact_Global_MultiCounter_Comparator
  - Universal_Dispel_Semantics
```

最终实现原则：

> `COUNTERATTACK` 不是“受到兵刃伤害就反弹”的数值效果，而是绑定于普通攻击受击节点的多实例 Reaction Batch。Batch 的入队资格在触发时锁定；每个反击实例随后作为独立标准兵刃效果伤害微步运行，并在执行时读取实时世界状态。反击不是普通攻击，因此不会派生突击、群攻或再次反击；已入队 sibling Counter 不因目标中途死亡而撤销，但原攻击者自身尚未执行的突击、连击等后续主动分支会因死亡立即终止。
