# Stage 9 分担 / DAMAGE_SHARE 核心机制冻结记录

Status ID: `690087`  
Official Name: `分担`  
English Name: `DAMAGE_SHARE`  
Status: `FROZEN`

Freeze Date: `2026-09-11`

本文件为 `sgs-v2-battle-system` 中 `690087 DAMAGE_SHARE / 分担` 的正式实现依据，同步自独立状态机制研究仓库的冻结结论。冻结的是经战报研究稳定确认的**外部行为合同**，不宣称复原官方源码内部类名、函数名或数据结构。

---

## 1. Classification

```yaml
Category: FUNCTIONAL_STATE
Family: DAMAGE_REDIRECTION / DAMAGE_PARTITION
State_Owner: PROTECTED_TARGET
Linked_Entity: SHARER
Effective_Instance_Limit_Per_Target: 1
Self_Share: FORBIDDEN
Cleanseable: false
Dispellable: false
```

核心定义：

> 分担不是普通减伤，而是在一笔伤害已经完成正常终伤计算后，将该终伤按比例拆分为“原目标份额”和“分担者份额”的独立分流机制。

因此：

```text
DamageReductionModifier != DamageShareOperator
```

战报中的“本次攻击受到的伤害减少了 R%”只是对拆分结果的展示性描述，不应把 `R` 加入普通减伤百分比池。

---

## 2. State Model

一个有效分担实例至少需要表达：

```yaml
DamageShareState:
  owner: protectedTarget
  sharer: linkedSharer
  sourceUnit: sourceUnit
  sourceSkill: sourceSkill
  ratioSnapshot: R
  lifecycleType: FIXED_DURATION | SOURCE_BOUND | CONDITION_BOUND
  remainingTurns: OPTIONAL
```

强不变量：

```text
protectedTarget.id != sharer.id
```

允许：

```text
attacker == sharer
```

例如【闭月】可以让攻击者本人替貂蝉分担；禁止的是“受保护目标同时也是自己的分担者”。

---

## 3. Ratio Snapshot

```yaml
Ratio_Policy: SNAPSHOT_AT_SUCCESSFUL_APPLICATION_OR_REFRESH
Runtime_Attribute_Changes: DO_NOT_RECALCULATE_EXISTING_RATIO
Refresh: RECALCULATE_AND_REPLACE_RATIO
Exact_Source_Formula: DEFINED_BY_SOURCE_SKILL
System_Level_Clamp: NOT_REQUIRED_BY_CURRENT_CONTRACT
```

成功施加或刷新分担时计算比例 `R`，并把该值固化在当前状态实例中。

```text
Apply / Refresh
→ read current source-specific attributes/context
→ calculate R
→ ratioSnapshot = R
```

后续持续期间属性变化不追溯修改已有 `ratioSnapshot`；再次成功刷新时重新采样。

本合同不冻结各具体来源战法如何从属性计算 `R`，该公式属于来源战法实现。

---

## 4. Unique Slot / Reapplication

`DAMAGE_SHARE` 是单实例唯一槽状态。

```yaml
Multiple_Active_Sharers_On_One_Target: false
Same_Source_Reapplication: REFRESH_AND_REPLACE
Cross_Source_Reapplication: REPLACE
Old_Instance_Returns_After_Replacement_Expires: false
```

不存在：

```text
多个分担者同时分一笔伤害
多个 R 加法叠加
多个 R 乘法复合
```

成功的新分担实例会成为唯一有效实例，并替换旧实例的：

- `sharer`
- `sourceUnit`
- `sourceSkill`
- `ratioSnapshot`
- duration / lifecycle context

同源刷新会重置持续时间并重新计算比例，而不是在旧持续时间上累加。

---

## 5. Eligibility

旧规则“`FinalDamage > 0` 才能触发分担”已被战报反例推翻。

正式准入规则：

```text
Eligible =
    DamageEventReachedShareStage
    AND NOT DamageEventCancelled
    AND NOT IsSelfSacrificeCost
    AND NOT IsShareDerivedTroopLoss
```

已确认可进入分担的伤害包括：

- 普通攻击，包括连击/追加普通攻击；
- 主动、突击、被动、指挥等产生的直接兵刃/谋略伤害；
- 灼烧、中毒、溃逃、沙暴、水攻、叛逃等持续伤害；
- 群攻 / Splash；
- 反击；
- 特殊兵种/延迟类有效伤害；
- 混乱、误伤等友军伤害；
- 合法但最终数值为 `0` 的 DamageEvent，例如虚弱导致 `Dtotal = 0`。

明确不属于可再次分担的对象：

- 分担派生的 `Dsharer`；
- 纯自损/献祭/成本型兵力扣除；
- 已在上游被规避、抵御等机制取消/吸收的 DamageEvent。

---

## 6. Upstream Cancellation: Zero Damage != Cancelled Event

必须区分：

```text
DamageValue == 0
```

与：

```text
DamageEvent.cancelled == true
```

两者语义完全不同。

### 6.1 Weakness / 虚弱

```text
合法 DamageEvent
→ 数值修正为 Dtotal = 0
→ DamageEvent 继续流转
→ 分担仍完整执行
→ Dtarget = 0
→ Dsharer = 0
```

零值分担仍属于成功执行，可以出现“执行分担”及“损失兵力0”的日志。

### 6.2 Evasion / 规避

```text
规避成功
→ DamageEvent 在分担之前取消
→ 不进入 DAMAGE_SHARE
```

### 6.3 Resistance / 抵御

```text
抵御生效
→ DamageEvent 在分担之前被吸收/终止
→ 不进入 DAMAGE_SHARE
```

因此模拟器不得使用：

```text
if (damage <= 0) return;
```

作为 DamageEvent 的通用短路条件。

---

## 7. Pipeline Position

当前冻结的关键顺序：

```text
TARGET_SELECTION
↓
GUARD / TARGET_REDIRECTION
↓
ACTUAL_TARGET 确定
↓
EVASION / RESISTANCE 等前置取消层
↓
正常伤害公式
  - 防御属性
  - 增伤/减伤
  - 兵种
  - 暴击/奇谋
  - 其他正常 Formula Modifier
↓
得到 Dtotal（允许为 0）
↓
DAMAGE_SHARE
↓
TARGET TROOP LOSS COMMIT
↓
TARGET DEATH CHECK
↓
若目标仍存活：SHARER TROOP LOSS COMMIT
```

分担不参与普通伤害公式，也不会让分担者再跑一遍自身防御/减伤计算。

---

## 8. Guard / 援护 Interaction

分担读取的是**援护后的最终实际受击者**，而不是最初被攻击选中的目标。

```text
OriginalTarget = A
B 援护 A
↓
ActualTarget = B
↓
后续仅检查 B 的防御、减伤、分担状态
```

规则：

```text
DAMAGE_SHARE_TARGET = FINAL_ACTUAL_DAMAGE_TARGET
```

因此：

- A 有分担、B 无分担：援护后不触发 A 的分担；
- A 无分担、B 有分担：援护后正常触发 B 的分担。

---

## 9. Partition Algorithm / 取整与守恒（SHS9-B01 冻结）

对于已确定的终伤：

```text
Dtotal
```

读取当前实例：

```text
R = ratioSnapshot
```

理论拆分算法：

```text
Dsharer_theoretical = round_half_up(Dtotal * R)
Dtarget             = Dtotal - Dsharer_theoretical
```

关键规则：

```text
先计算分担份额并采用 ROUND_HALF_UP 取整
→ 原目标取剩余值：Dtarget = Dtotal - Dsharer_theoretical
```

因此理论分配严格满足：

```text
Dtarget + Dsharer_theoretical == Dtotal
```

不得对两边分别独立取整。

### 9.1 取整与 .5 边界裁决（SHS9-B01）

分担份额取整必须严格执行 **`ROUND_HALF_UP`**（向正无穷四舍五入 / half ties round upward）：
- 经 98 例精确 .5 边界真实战报验证（【严阵以待】$R = 15.00\% = 3/20$）：
  - 偶数基数 $K$ 遇 $.5$（$N=47$，如 $70.5 \to 71, 106.5 \to 107, 82.5 \to 83, 64.5 \to 65$）：**100% 进位至 $K+1$**；
  - 奇数基数 $K$ 遇 $.5$（$N=39$，如 $37.5 \to 38, 1.5 \to 2, 61.5 \to 62, 115.5 \to 116$）：**100% 进位至 $K+1$**；
  - 彻底排除银行家舍入 `ROUND_HALF_EVEN`（偶数向偶数舍入假说）以及向下取整 `FLOOR`；
  - 非边界小数部分 $< 0.5$ 正常舍去（如 $70.35 \to 70$），排除 `CEIL`。
- 原目标永远取整数余量：$D_{\text{target}} = D_{\text{total}} - D_{\text{sharer\_theoretical}}$。

此项冻结正式关闭 Finding `SHS9-B01`。

---

## 10. Zero-Amount Share

`Dsharer_theoretical == 0` 不代表分担未触发。

```yaml
ShareTriggered: true
ShareExecuted: true
ActualSharerTroopLoss: 0
```

允许完整执行：

```text
Dsharer_theoretical = 0
Dtarget = Dtotal
```

并允许分担者侧产生“执行分担 / 损失兵力0”的事件表现。

因此不得写：

```text
if (Dsharer <= 0) skipShare;
```

---

## 11. Target Commit First / Death Interrupt

分担不是“两边同时原子扣兵”。

冻结顺序：

```text
1. 先完成理论拆分
2. 原目标提交 Dtarget
3. 检查原目标是否死亡
4. 仅当原目标仍存活时，才提交 Dsharer_theoretical 给分担者
```

若原目标因 `Dtarget` 当场死亡：

```text
TARGET_DEATH_INTERRUPT
→ 丢弃尚未提交的 Dsharer_theoretical
→ 分担者本次不扣兵
```

即使前面已经计算出分担份额，该份额也不会再执行。

这遵循项目全局死亡硬终止原则，同时明确了分担内部的 commit 顺序。

---

## 12. Sharer Troop-Loss Commit / Overflow

当原目标存活并进入分担者提交阶段：

```text
ActualSharerTroopLoss
    = min(Dsharer_theoretical, sharer.currentTroops)
```

若分担者兵力不足：

```text
Overflow
    = Dsharer_theoretical - ActualSharerTroopLoss
```

`Overflow` 直接丢弃：

- 不返还给原目标；
- 不传递给第三人；
- 不再次触发分担；
- 不再次触发分摊；
- 不计入实际伤害统计；
- 不进入伤兵生成基数。

因此实际兵力损失可以小于理论 `Dtotal`。

---

## 13. Nature of Sharer Loss

`Dsharer` 的正式定义：

```text
Attributed Direct Troop Loss
```

它不是第二个正常 DamageEvent，也不是“复制攻击”。

分担者侧不会重新执行：

- 自身统率/智力防御计算；
- 自身普通减伤；
- 规避；
- 抵御；
- 警戒等普通受击减免；
- 急救；
- 常规 OnTakeDamage / OnHurt 被动；
- 反击类受击触发；
- 再次分担 / 分摊。

因此实现上不得把 `Dsharer` 递归送回普通 `DamageSystem`。

但该兵力损失保留来源/归因元数据，并进入兵力扣除后的统计与伤兵处理。

---

## 14. Original Target Post-Share Damage Event

原目标后续的正常“受到伤害”语义读取的是：

```text
Dtarget
```

而不是分担前的 `Dtotal`。

因此：

```text
TakeDamageEvent.damage = Dtarget
```

并据此处理：

- 原目标的受伤布尔判定；
- 原目标受击被动；
- 原目标反击；
- 原目标急救/按受伤量计算机制；
- 原目标自身伤兵生成。

攻击方的倒戈/攻心等按实际造成伤害量计算的恢复，同样只读取原目标实际 DamageEvent 的 `Dtarget`，不读取 `Dsharer`。

---

## 15. Live Validation / No Skill-Level Snapshot

分担有效性不是在一个战法开始时整体快照。

每一笔独立 Damage Instance 都重新检查当前状态：

```text
state exists
AND state operational
AND sharer exists
AND sharer alive
AND sharer.currentTroops > 0
AND source requirements currently valid
```

因此：

- Hit 1 的分担把 sharer 打死，Hit 2 立即失去分担；
- 同一 AOE 中 Target 1 的分担把共同 sharer 打死，稍后结算的 Target 2 立即失去分担；
- 不需要等当前战法、当前行动或当前回合结束。

正式原则：

```text
DAMAGE_SHARE_HAS_NO_SKILL_LEVEL_SNAPSHOT
```

---

## 16. Multi-Target / AOE Resolution

多目标伤害按目标逐个串行结算，而不是对所有目标同时冻结分担关系。

```text
for target in targetQueue:
    resolveDamage(target)
```

每个目标在自己的 Damage Instance 中重新做 `DAMAGE_SHARE_CHECK`。

因此共同分担者在较早目标的分担过程中死亡，会即时影响同一战法尚未结算的后续目标。

本合同冻结“串行逐目标重新校验”，但**不冻结具体 AOE targetQueue 的目标排序规则**；目标排序属于对应战法/目标系统研究范围。

---

## 17. Damage Share vs Distribution / 分担与分摊

`DAMAGE_SHARE` 对 `DISTRIBUTION` 具有严格非对称优先级：

```text
DAMAGE_SHARE > DISTRIBUTION
```

### Existing SHARE + Incoming DISTRIBUTION

```text
目标已有分担
→ 新分摊施加失败 / 无效
```

战报可出现：

```text
由于「分担」的效果，「分摊」对其无效
```

### Existing DISTRIBUTION + Incoming SHARE

```text
目标已有分摊
→ 新分担成功施加
→ 分担覆盖/替换分摊
```

两者不会在同一目标上同时参与同一笔伤害结算。

---

## 18. Lifecycle

分担必须区分：

```text
state.exists
```

与：

```text
state.isOperational()
```

### 18.1 Protected Target Death（SHS9-M01 冻结闭环）

状态持有者死亡时，分担机制仅拥有自身事务内部行为，不越权拥有整个外层 Action：

```text
TARGET_DEATH (Protected Target)
→ commit target assigned loss (Dtarget)
→ emit TargetDeathFact
→ apply Share-local transaction rule (discard pending Dsharer; see Section 11 & SHS9-B02)
→ complete Share transaction
→ delegate outer Action / reaction / finalization decisions to authoritative owner
```

规则定义：
1. **Transaction-Scope Ownership**：分担 P0 仅拥有本分担微事务的切分、目标扣兵、死亡感知与待扣除份额决策；
2. **委托外层调度**：分担 P0 不直接硬编码 `ABORT_REMAINING_ACTION`。外部 Action、反应栈（ReactionStack）或战斗终结由 Stage 9 全局调度器（Core Orchestrator / RF-P04 终战合同）裁决；
3. 若同一来源分别保护多个目标，一个目标死亡不会删除其他目标自己的分担实例。

此项冻结正式关闭 Finding `SHS9-M01`。

### 18.2 Sharer Death

分担者死亡：

```text
state.isOperational() = false immediately
```

后续任何 Damage Instance 立即不再分担。

但保护目标身上的状态实例/展示可能暂时残留，直至其自身后续清理窗口才出现“分担效果已消失”。

因此 sharer 死亡首先属于**功能失效**，不要求状态实例在同一瞬间物理删除。

### 18.3 Normal Control On Sharer

震慑、计穷、缴械、虚弱、混乱等普通控制不会因为分担者“不能行动”而停止已存在分担。

分担是被动兵力分流，不要求 sharer 主动行动。

### 18.4 Source Suppression / 伪报

若当前分担依赖仍需持续有效的被动/指挥来源，而来源被伪报压制：

```text
state may still exist
state.isOperational() = false
```

来源恢复有效后，既有 source-bound 分担可以重新恢复 operational。

对已经独立施加完成、无需持续来源维持的主动类实例，不应因为来源后来被伪报而自动删除。

---

## 19. Duration Ownership / Tick Subject

固定持续回合的分担，其 duration owner 是：

```text
protected target / state owner
```

不是施法者，也不是分担者。

基本模型：

```text
remainTurns = N

on protectedTarget Turn Start:
    remainTurns -= 1
    if expired:
        remove state before subsequent damage/action resolution
```

因此速度/行动顺序会影响跨自然回合的实际覆盖长度：

- 本回合在目标行动前施加：目标本回合后续 Turn Start 会消耗一次；
- 本回合在目标行动后施加：首次消耗等到下一回合目标 Turn Start。

自然到期发生在保护目标自己的 Turn Start 清理窗口，早于该目标随后触发的持续伤害/正常行动。

并非所有分担都有 `remainingTurns`：

```yaml
FIXED_DURATION: uses remainingTurns
SOURCE_BOUND: no fixed turn counter required
CONDITION_BOUND: no fixed turn counter required
```

---

## 20. Cleanse / Dispel / Removal

```yaml
Purify: DOES_NOT_REMOVE
Cleanse: DOES_NOT_REMOVE
Dispel: DOES_NOT_REMOVE
```

分担不属于通用净化可移除的负面状态，也不属于可被普通驱散移除的常规增益。

必须区分：

```text
REMOVE STATE
```

和：

```text
SOURCE SUPPRESSION / FUNCTIONAL INVALIDATION
```

伪报属于后者，不属于驱散。

当前冻结的主要状态终止/替换路径：

- 自然到期；
- 状态持有者死亡；
- 新分担成功替换旧分担；
- 来源/分担者条件失败导致 operational=false（可与物理状态残留并存）。

---

## 21. Attribution / Positive Same-Camp Share

常规同阵营正向分担中，分担者实际扣掉的兵力仍继承原始伤害的物理来源：

```yaml
physicalAttacker: ORIGINAL_ATTACKER
physicalSkill: ORIGINAL_SKILL_OR_NORMAL_ATTACK
victim: SHARER
```

若分担者因此死亡：

- 死亡者是 `sharer`；
- 击杀来源归原攻击者；
- 原技能来源保留；
- 主将因分担死亡可正常触发对应战斗终局；
- 要求特定 Victim 的击杀后机制按真实死亡者判断。

因此 `Dsharer` 不是无来源自损。

---

## 22. Cross-Camp Reverse Share / 闭月 Credit Rerouting

跨阵营反向分担必须区分：

```text
physical source
```

和：

```text
combat credit owner
```

例如【闭月】：

```text
敌军 A 攻击貂蝉
敌军 B 为貂蝉分担
```

分担者日志仍可表现为：

```text
B 由于 A 的原技能伤害而损失兵力
```

但战后收益归属发生重定向：

```yaml
physicalAttacker: A
physicalSkill: A's original skill
victim: B
creditOwner: DAMAGE_SHARE_EFFECT_OWNER  # 闭月拥有者貂蝉
```

因此：

- A 不把这部分己方损失计入自己的对敌伤害统计；
- 该反向分担造成的有效兵力损失计入闭月效果拥有者；
- 对应击杀/战功收益同样归 credit owner；
- 即使 `attacker == sharer`，仍允许物理日志表现为自己技能导致自己损失兵力，而收益归闭月拥有者。

实现上应避免仅使用一个含义含混的 `source` 字段同时承担日志来源与战果归属。

建议至少区分：

```text
physicalAttacker
physicalSkill
creditOwner
victim
```

---

## 23. Runtime Damage vs Post-Battle Statistics

必须区分运行时 DamageEvent 数值与战后统计。

### Runtime

攻击者的倒戈/攻心等即时伤害量读取：

```text
Dtarget
```

`Dsharer` 不参与这些即时 DamageEvent-based 计算。

### Statistics

战后 `normal_damage / skill_damage` 统计锚定于：

```text
ActualCommittedTroopLoss
```

正常正向分担中：

```text
DamageStat
+= ActualTargetTroopLoss
 + ActualSharerTroopLoss
```

而不是无条件记录理论 `Dtotal`。

所以：

- 原目标残血 overkill：只记实际扣掉的兵力；
- 原目标死亡中断导致 `Dsharer` 未提交：未提交部分不计；
- 分担者残血导致 overflow：只记 `ActualSharerTroopLoss`；
- 无截断正常情况下，由于实际两份之和等于 `Dtotal`，统计才“看起来等于 Dtotal”。

跨阵营反向分担按第 22 节的 `creditOwner` 规则归属。

---

## 24. Wounded Generation / 伤兵

分担者的 Direct Troop Loss 虽然不是正常 `TakeDamageEvent`，但实际成功扣除的兵力会进入正常伤兵处理链。

冻结规则：

```text
WoundedGenerationBase = ActualSharerTroopLoss
```

因此：

- 分担者残血截断：只以实际扣掉的部分作为伤兵基数；
- 原目标死亡中断、分担未提交：分担者新增伤兵为 0；
- `Dsharer = 0`：新增伤兵为 0；
- 理论 overflow 不产生伤兵。

本合同**不冻结**具体伤兵比例、取整方式、回合死淘率等伤兵系统内部公式；这些属于独立伤兵机制研究。

---

## 25. Damage Reduction Interaction

普通减伤与分担为两个独立阶段：

```text
Normal Damage Formula / DamageReductionModifier
→ Dtotal
→ DamageShareOperator
```

例如普通减伤已经把伤害压低后，分担再从该结果中按 `R` 拆分。

不得实现为：

```text
ordinaryReduction + shareRatio
```

同一个减伤百分比桶。

分担也不属于被普通减伤上限直接裁剪的同类 Modifier；它只读取已经完成公式处理的 `Dtotal`。

---

## 26. Implementation Contract

推荐把伤害过程中的关键值明确区分，禁止一个 `damage` 字段承担全部语义：

```yaml
preShareFinalDamage: Dtotal
sharedAssignedDamage: Dsharer_theoretical
targetAssignedDamage: Dtarget
actualTargetTroopLoss: ActualTargetTroopLoss
actualSharerTroopLoss: ActualSharerTroopLoss
```

推荐分担解析结构：

```text
resolveDamageShare(event, actualTarget):
    state = actualTarget.damageShareState

    if state does not exist:
        return no-share

    if event.cancelled:
        return no-share

    if !state.isOperational():
        return no-share

    sharer = resolve(state.sharer)

    if sharer == null
       or !sharer.alive
       or sharer.troops <= 0
       or sharer.id == actualTarget.id:
        return no-share

    Dtotal = event.preShareFinalDamage
    Dsharer = round_half_up(Dtotal * state.ratioSnapshot)
    Dtarget = Dtotal - Dsharer

    commit target assigned loss first

    if target died:
        discard pending Dsharer
        return

    commit attributed direct troop loss to sharer
```

注意：这是模拟器实现合同，不宣称官方源码使用相同函数或字段名。

---

## 27. Required Regression Tests

最低必须覆盖：

```text
T01 normal damage + share
T02 .5 rounding boundary
T03 Dsharer = 0 but share still executes
T04 weakness -> Dtotal = 0 -> share still executes
T05 evasion -> event cancelled -> no share
T06 resistance -> event negated -> no share
T07 guard redirects target -> check redirected target's share
T08 sharer dies on Hit1 -> Hit2 no share
T09 AOE Target1 kills common sharer -> later target no share
T10 target dies from Dtarget -> pending Dsharer discarded
T11 sharer low troops -> overflow discarded
T12 runtime lifesteal reads Dtarget only
T13 post-battle stat uses actual committed troop loss
T14 same-source refresh resets duration and ratio snapshot
T15 new share replaces old share
T16 existing SHARE rejects incoming DISTRIBUTION
T17 existing DISTRIBUTION is replaced by incoming SHARE
T18 sharer normal control does not disable share
T19 source-bound share suppressed by false report and later operational again
T20 cleanse/dispel do not remove share
T21 self-share application rejected
T22 positive same-camp share kill attribution
T23 cross-camp reverse share credit rerouting
T24 shared actual troop loss enters wounded processing
```

---

## 28. Frozen / Deferred Boundary

### FROZEN

本合同冻结：

- 分担的状态模型；
- 唯一槽 / 刷新 / 替换；
- apply-time ratio snapshot；
- DamageEvent 准入与取消区别；
- 与援护、规避、抵御、分摊、普通减伤的关键顺序；
- 终伤后拆分公式与取整（SHS9-B01：ROUND_HALF_UP）；
- target-first commit；
- target death interrupt；
- sharer overflow；
- 多段 / 多目标逐实例实时校验；
- 生命周期与 Turn Start duration ownership；
- 不可净化 / 不可驱散；
- 正向/反向分担的物理来源与收益归属；
- 运行时伤害量与战后统计口径；
- 伤兵生成基数；
- self-share 禁止；
- 保护目标阵亡仅拥有分担微事务语义，外层 Action/终战委托全局调度（SHS9-M01）。

### OUT OF SCOPE / DEFERRED

本合同不冻结：

- 各来源战法的具体 `R` 数学公式；
- 致死原目标对分担者未提交份额的精确保留/取消（SHS9-B02，留待 RF-P05）；
- 普通基础兵刃/谋略伤害公式；
- AOE targetQueue 的具体目标排序规则；
- 伤兵系统自己的精确生成比例、取整和回合死淘公式；
- 官方源码内部类名、函数名、字段名；
- 与尚未研究状态之间的未知特殊交互。

---

## 29. Freeze Gate

```yaml
BLOCKER: 0
MAJOR: 0
Implementation_Blocking_Unresolved: 0
Status: FROZEN
```

当前合同已经足以作为战斗模拟器 `690087 DAMAGE_SHARE` 的正式实现依据。
