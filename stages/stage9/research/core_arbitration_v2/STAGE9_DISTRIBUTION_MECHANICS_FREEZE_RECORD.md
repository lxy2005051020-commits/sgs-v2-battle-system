# Stage 9 分摊 / DISTRIBUTION 核心机制冻结记录

Status ID: `690086`  
Official Name: `分摊`  
English Name: `DISTRIBUTION`  
Status: `FROZEN`

Freeze Date: `2026-09-12`

本文件为 `sgs-v2-battle-system` 中 `690086 DISTRIBUTION / 分摊` 的正式实现依据。

当前研究原则：

```text
DISTRIBUTION
inherits DAMAGE_SHARE common pipeline rules
EXCEPT where battle-report evidence proves a distribution-specific rule
```

因此，分摊与分担共享外围 DamageEvent 准入、上游取消、援护后的 ActualTarget、终伤后介入、派生扣兵非二次 DamageEvent、实时校验、实际扣兵统计/伤兵等通用原则；但**分摊自己的数学拆分、参与者拓扑和 Commit 顺序与分担不同，必须单独实现**。

---

## 1. Classification

```yaml
Category: FUNCTIONAL_STATE
Family: DAMAGE_PARTITION
State_Owner: PROTECTED_TARGET
Participant_Topology: MULTI_RECIPIENT
Effective_Instance_Limit_Per_Target: 1
DamageShare_Precedence: DAMAGE_SHARE > DISTRIBUTION
Status: FROZEN
```

核心定义：

> 分摊是在正常伤害公式已经得到 `Dtotal` 后，先确定原目标保留份额，再把被转移部分按当前合法承担者数量拆成相同理论份额，并按固定顺序依次提交承担者扣兵，最后才提交原目标扣兵。

分摊不是普通 `DamageReductionModifier`，也不是“多个分担者版的 DAMAGE_SHARE”简单复制。

---

## 2. Shared Family Rules Inherited From DAMAGE_SHARE

除本合同明确覆盖的差异外，分摊继承 `690087 DAMAGE_SHARE` 已冻结的以下通用规则：

```text
TARGET_SELECTION
→ GUARD / TARGET_REDIRECTION
→ FINAL_ACTUAL_DAMAGE_TARGET
→ EVASION / RESISTANCE upstream cancellation
→ normal damage formula
→ Dtotal (legal value may be 0)
→ DAMAGE_PARTITION stage
```

并继承：

- 规避成功：DamageEvent 在分摊前取消，不进入分摊；
- 抵御生效：DamageEvent 在分摊前被吸收/终止，不进入分摊；
- 虚弱等导致合法 `Dtotal = 0`：事件仍可进入分摊阶段；
- 分摊读取援护后的 `FINAL_ACTUAL_DAMAGE_TARGET`；
- 分摊不加入普通增伤/减伤百分比池；
- 分摊派生承担者损失不是第二个正常 DamageEvent；
- 承担者不重新计算自身统率/智力、防御、普通减伤；
- 承担者不再触发自身规避、抵御、急救、反击等正常受击链；
- 分摊派生损失不得再次递归进入分担/分摊；
- 每个 Damage Instance 实时重新校验当前状态与参与者；
- 实际成功扣除的兵力进入战后实际伤害统计与伤兵处理；
- 理论溢出、未提交损失不进入统计与伤兵基数。

本合同若与 `STAGE9_DAMAGE_SHARE_MECHANICS_FREEZE_RECORD.md` 的通用规则冲突，以本合同对 DISTRIBUTION 的明确差异条款为准。

---

## 3. Ratio Snapshot

分摊比例 `R` 采用与分担相同的状态实例快照原则：

```yaml
Ratio_Policy: SNAPSHOT_AT_SUCCESSFUL_APPLICATION_OR_REFRESH
Runtime_Attribute_Changes: DO_NOT_RECALCULATE_EXISTING_RATIO
Refresh: RECALCULATE_OR_REPLACE_BY_SOURCE_EFFECT_RULE
Exact_Source_Formula: DEFINED_BY_SOURCE_SKILL
```

本合同不冻结【义心昭烈】如何从自身战法参数得到 `R` 的来源战法内部公式，只冻结分摊系统拿到 `R` 之后如何结算。

---

## 4. Mathematical Partition Algorithm

### 4.1 Normal damage formula first

分摊介入前，必须先完成正常伤害公式：

```text
Defense / Damage Modifiers / Troop / Crit / other normal formula stages
↓
Dtotal
↓
DISTRIBUTION
```

不得把分摊比例 `R` 直接塞进普通减伤池。

### 4.2 Target retained loss first

当当前合法承担者数量 `N > 0` 时：

```text
Dtarget = round_half_up(Dtotal × (1 - R))
Dtransfer = Dtotal - Dtarget
```

这里的 `Dtarget` 是原目标理论承担量，`Dtransfer` 是被转移出去的理论总量。

### 4.3 Equal independent participant share

设：

```text
N = current legal participant count
```

则每一个承担者获得**相同理论份额**：

```text
Dparticipant = round_half_up(Dtransfer / N)
```

所有承担者独立使用同一个 `Dparticipant`。

已确认：

```text
NO_LAST_PARTICIPANT_REMAINDER_RULE
NO_ASYMMETRIC_REMAINDER_ASSIGNMENT
```

因此不得实现为：

```text
前 N-1 人固定份额
最后 1 人吃掉全部余数
```

### 4.4 Second-rounding consequence

由于 `Dtarget` 与 `Dparticipant` 分别存在整数取整步骤，分摊不要求理论提交量严格满足：

```text
Dtarget + N × Dparticipant == Dtotal
```

出现整数级取整偏差属于算法结果，不得为了“强行守恒”再把余数补到最后一个承担者。

### 4.5 取整与 .5 边界裁决（DSTS9-B01 冻结）

分摊机制中的两处取整均严格执行 **`ROUND_HALF_UP`**（向正无穷四舍五入 / half ties round upward）：
1. **原目标保留份额 `Dtarget`**：
   - 经 12 例 $R = 50.00\%$ 精确 .5 边界真实战报验证（如 $251 \times 0.5 = 125.5 \to 126, 407 \times 0.5 = 203.5 \to 204$）：**100% 进位至 $K+1$**；
   - 小于 0.5 正常舍去（如 $622.386 \to 622$），大于 0.5 正常进位（如 $348.894 \to 349$）。
2. **承担者分配份额 `Dparticipant`**：
   - 经 34 例 $N = 2$ 精确 .5 边界真实战报验证：
     - 偶数基数 $K$ 遇 $.5$（$N=17$，如 $353 / 2 = 176.5 \to 177, 165 / 2 = 82.5 \to 83$）：**100% 进位至 $K+1$**；
     - 奇数基数 $K$ 遇 $.5$（$N=17$，如 $147 / 2 = 73.5 \to 74, 183 / 2 = 91.5 \to 92$）：**100% 进位至 $K+1$**；
     - 彻底排除银行家舍入 `ROUND_HALF_EVEN` 以及向下取整 `FLOOR`。

此项冻结正式关闭 Finding `DSTS9-B01`。

---

## 5. Dynamic Participant Set

参与者集合在**每一笔 Damage Instance 的分摊执行时动态读取**，不是状态施加时快照。

正式定义：

```text
participants = current team members satisfying:
    same camp as actualTarget
    AND alive now
    AND not actualTarget
    AND not isolated / excluded by source-legal participation rule
```

核心性质：

```yaml
Participant_Evaluation: DAMAGE_TIME_DYNAMIC
Apply_Time_Participant_Snapshot: false
Alive_Check: JIT
Exclude_Actual_Target: true
Camp: SAME_CAMP
```

### 5.1 Death immediately changes N

已确认存在同一既存分摊实例跨队友死亡继续执行的战报链：

```text
施加时：Target + AllyA + AllyB 全部存活
↓
AllyB 后续死亡
↓
状态未重新施加 / 未刷新
↓
Target 再次受击
↓
participants 动态变为 [AllyA]
N = 1
```

因此不得在分摊状态实例中保存一个长期不变的 participant list。

### 5.2 No legal participant

若伤害执行时：

```text
N == 0
```

则不存在可转移对象：

```text
Dtarget = Dtotal
no effective participant distribution
```

不得凭空消除 `R` 对应的伤害。

---

## 6. Participant Resolution Order

多个承担者不是同时原子提交。

承担者按固定槽位升序依次执行：

```text
Slot 0 / 主将
→ Slot 1 / 副将1
→ Slot 2 / 副将2
```

结算时跳过 `actualTarget` 和当前不合法单位。

正式顺序：

```text
1. DISTRIBUTION execution announced
2. Participant Slot ASC commits
3. target reduction/explanation log
4. Original Target commits Dtarget
```

因此：

```text
DISTRIBUTION = PARTICIPANTS_FIRST_COMMIT
```

这一点与 `DAMAGE_SHARE = TARGET_FIRST_COMMIT` 明确不同。

---

## 7. Participant Death / Overflow

每个承担者独立执行兵力截断：

```text
ActualParticipantTroopLoss
    = min(Dparticipant, participant.currentTroops)
```

若理论承担量超过当前兵力：

```text
Overflow = Dparticipant - ActualParticipantTroopLoss
```

`Overflow` 直接丢弃：

- 不重新均摊给其他承担者；
- 不返还给原目标；
- 不延迟到后续单位；
- 不再次进入分担/分摊；
- 不计入实际伤害统计；
- 不进入伤兵生成基数。

### 7.1 Participant death does not abort the distribution

若较早槽位承担者因本次分摊扣兵死亡：

```text
该承担者死亡
→ 当前承担者 commit 完成
→ 后续承担者继续
→ 原目标最后继续 commit
```

分摊不存在“某承担者死亡导致整个分摊流程中断”的规则。

这与分担中“原目标先死会中断 pending sharer loss”的 target-first 结构不同。

---

## 8. Original Target Commit

完成所有当前合法承担者的提交后：

```text
ActualTargetTroopLoss
    = min(Dtarget, target.currentTroops)
```

然后执行原目标正常受伤后续语义。

因此分摊的关键 Commit 图为：

```text
calculate Dtarget / Dtransfer / Dparticipant
↓
Participant 1 commit
↓
Participant 2 commit
↓
...
↓
Original Target commit
```

---

## 9. Nature of Participant Loss

承担者收到的是：

```text
Attributed Direct Troop Loss
```

不是第二个正常 DamageEvent。

因此承担者侧不重新执行：

- 防御属性；
- 普通伤害增减；
- 规避；
- 抵御；
- 警戒等普通受击减伤；
- 急救；
- 反击；
- 普通 OnTakeDamage / OnHurt 回调；
- 再次分担；
- 再次分摊。

实际扣兵仍保留原攻击来源与统计归因元数据。

---

## 10. Attribution / Statistics / Kill Credit

常规分摊承担者的物理伤害来源继续穿透原始攻击：

```yaml
physicalAttacker: ORIGINAL_ATTACKER
physicalSkill: ORIGINAL_SKILL_OR_NORMAL_ATTACK
victim: CURRENT_PARTICIPANT
creditOwner: ORIGINAL_ATTACKER
```

因此：

- 承担者日志仍可显示原攻击者及原技能；
- 承担者实际扣兵计入原攻击者对应 `normal_damage / skill_damage`；
- 承担者因分摊死亡时，Killer 归原始攻击者；
- 不视为承担者自残或友军自伤。

统计口径继续使用：

```text
ActualCommittedTroopLoss
```

理论份额、overflow、未执行份额均不计。

---

## 11. Wounded Generation

承担者的实际 Direct Troop Loss 进入正常伤兵处理链。

冻结：

```text
WoundedGenerationBase = ActualParticipantTroopLoss
```

因此：

- 残兵截断只以实际扣掉的兵力为伤兵基数；
- overflow 不生成伤兵；
- 理论分摊量不直接生成伤兵。

本合同不冻结伤兵系统内部具体比例、取整、死淘公式。

---

## 12. Reapplication / Instance Lifecycle

### 12.1 Single effective instance

```yaml
Effective_Instance_Limit_Per_Target: 1
```

同一目标不会同时保留两个独立有效分摊实例并行结算。

### 12.2 Same-source reapplication

当前真实游戏中的分摊来源以【义心昭烈】为已知来源。

同源再次生效：

```text
SameSource = REFRESH
```

表现为刷新现有分摊持续时间 / 当前实例，而不是叠加第二实例。

### 12.3 Cross-source behavior

当前研究资料中没有可自然观察的第二种独立 DISTRIBUTION 来源，因此跨来源行为**无法通过现有真实战报直接验证**。

模拟器采用：

```yaml
CrossSource_Behavior: REPLACE
Evidence: INHERITED_FROM_DAMAGE_SHARE_FAMILY_CONTRACT
Empirical_Observability: CURRENTLY_UNAVAILABLE
Implementation_Blocking: false
```

即如果未来出现新的分摊来源，后成功生效的分摊实例替换旧实例。

这是一条**家族继承的非阻塞实现规则**，不得标记成“已由跨来源真实战报直接证明”。

---

## 13. DAMAGE_SHARE vs DISTRIBUTION

两者具有严格非对称优先级：

```text
DAMAGE_SHARE > DISTRIBUTION
```

### Existing DAMAGE_SHARE + Incoming DISTRIBUTION

```text
已有分担
→ 新分摊无效 / 被拒绝
```

### Existing DISTRIBUTION + Incoming DAMAGE_SHARE

```text
已有分摊
→ 新分担成功
→ 分担覆盖分摊
```

两者不会同时参与同一目标同一 Damage Instance 的伤害拆分。

---

## 14. Duration / Operational Lifecycle

除本合同没有另外证明差异的部分，分摊生命周期沿用 DAMAGE_SHARE 家族基线：

```text
state.exists
!=
state.isOperational()
```

固定持续回合实例由状态持有者自身的行动开始窗口管理 duration。

状态持有者死亡遵循全局死亡硬终止：

```text
TARGET_DEATH
→ CLEAR_ALL_STATES
→ ABORT_REMAINING_STATE_RESOLUTION
→ ABORT_REMAINING_ACTION
→ REJECT_FUTURE_STATE_APPLICATION
```

承担者死亡只会在下一次 Damage-Time participant evaluation 时被动态排除，不要求旧状态实例整体失效。

---

## 15. Cleanse / Dispel / Source Suppression

按照当前“除已证明差异外继承 DAMAGE_SHARE”的冻结原则：

```yaml
Normal_Purify: DOES_NOT_REMOVE_DISTRIBUTION
Normal_Dispel: DOES_NOT_REMOVE_DISTRIBUTION
Source_Suppression: FOLLOW_SOURCE_EFFECT_SEMANTICS
```

如果未来发现 DISTRIBUTION 对净化/驱散存在独立战报反例，应重新打开本条，而不是修改核心数学与 Commit 模型。

---

## 16. Zero Damage / Upstream Cancellation

继续继承 DAMAGE_SHARE 家族的事件语义：

```text
DamageValue == 0
!=
DamageEvent.cancelled
```

因此：

```text
Weakness / legal zero Dtotal
→ Distribution stage may still execute with zero values
```

而：

```text
Evasion successful
Resistance successful
→ DamageEvent cancelled / absorbed upstream
→ no Distribution
```

不得用：

```text
if damage <= 0: return
```

代替正式 Event Cancellation 判断。

---

## 17. Implementation Contract

推荐实现时明确区分：

```yaml
preDistributionFinalDamage: Dtotal
targetAssignedDamage: Dtarget
transferPool: Dtransfer
participantAssignedDamage: Dparticipant
actualParticipantTroopLoss: per participant
actualTargetTroopLoss: final target commit
```

推荐伪代码：

```text
resolveDistribution(event, actualTarget):
    state = actualTarget.distributionState

    if state == null:
        return normal damage

    if event.cancelled:
        return no distribution

    if !state.isOperational():
        return normal damage

    participants = resolveCurrentParticipants(actualTarget)
        .filter(sameCamp)
        .filter(alive)
        .filter(not actualTarget)
        .filter(not isolated / source-legal)
        .sortBy(slot ASC)

    if participants.isEmpty():
        commit normal target Dtotal
        return

    Dtotal = event.preDistributionFinalDamage
    R = state.ratioSnapshot

    Dtarget = round_half_up(Dtotal * (1 - R))
    Dtransfer = Dtotal - Dtarget
    Dparticipant = round_half_up(Dtransfer / participants.count)

    for participant in participants:
        actualLoss = min(Dparticipant, participant.currentTroops)
        commitAttributedDirectTroopLoss(
            victim = participant,
            amount = actualLoss,
            physicalAttacker = event.attacker,
            physicalSkill = event.skill,
            creditOwner = event.attacker
        )
        # participant death does not abort remaining loop
        # overflow is discarded

    commit original target Dtarget last
```

注意：以上为模拟器外部行为实现合同，不宣称官方源码使用相同函数或字段名。

---

## 18. Required Regression Tests

最低必须覆盖：

```text
T01 two participants receive equal assigned share
T02 one participant alive -> N=1 and receives full transfer pool after rounding
T03 N=0 -> target takes full Dtotal
T04 target-first mathematical calculation uses round_half_up(Dtotal × (1-R))
T05 participant share uses round_half_up(Dtransfer / N)
T06 no last-participant remainder assignment
T07 participant Slot ASC commit order
T08 participant dies during commit -> later participant still executes
T09 participant overflow discarded
T10 participant overflow not returned to target
T11 participant overflow not redistributed
T12 target commits after all participants
T13 teammate dies after application -> next hit recalculates participants dynamically
T14 no apply-time participant snapshot
T15 same-source reapplication refreshes one instance
T16 existing DAMAGE_SHARE rejects incoming DISTRIBUTION
T17 incoming DAMAGE_SHARE replaces existing DISTRIBUTION
T18 guard redirects first -> Distribution checks final ActualTarget
T19 weakness legal Dtotal=0 can execute zero distribution
T20 evasion blocks Distribution upstream
T21 resistance blocks Distribution upstream
T22 participant loss does not re-enter normal DamageSystem
T23 actual participant loss enters statistics
T24 actual participant loss enters wounded processing
```

---

## 19. Frozen / Deferred Boundary

### FROZEN

本合同冻结：

- 分摊作为 Damage Partition 家族成员；
- 正常伤害公式完成后读取 `Dtotal`；
- 原目标理论份额的计算顺序与取整（DSTS9-B01：ROUND_HALF_UP）；
- 转移池 `Dtransfer`；
- 当前承担者数量 `N`；
- 每个承担者相同独立理论份额与取整（DSTS9-B01：ROUND_HALF_UP）；
- 不使用最后一人吃余数；
- Damage-Time 动态参与者集合；
- same-camp / alive / exclude actualTarget；
- participant Slot ASC 顺序；
- participants-first / target-last Commit；
- 承担者死亡不中断后续分摊；
- 残兵截断与 overflow 丢弃；
- attribution / statistics / wounded 基于实际 commit；
- same-source refresh；
- DAMAGE_SHARE > DISTRIBUTION；
- 继承 DAMAGE_SHARE 的通用外围 DamageEvent 规则。

### INHERITED_NON_BLOCKING

```text
CrossSource DISTRIBUTION → REPLACE
```

当前真实游戏资料缺少第二独立分摊来源，采用 DAMAGE_SHARE 家族一致的单实例替换规则。

### DEFERRED / OUT OF SCOPE

本合同不冻结：

- 【义心昭烈】内部具体比例公式；
- 普通基础兵刃/谋略伤害公式；
- 伤兵系统自身精确比例、取整和回合死淘；
- 官方源码内部类名、函数名、字段名；
- 尚未研究状态与分摊之间可能存在的未来特殊例外。

---

## 20. Freeze Gate

```yaml
BLOCKER: 0
MAJOR: 0
Implementation_Blocking_Unresolved: 0
CrossSource_Unobservable: NON_BLOCKING
Status: FROZEN
```

当前合同已经足以作为战斗模拟器 `690086 DISTRIBUTION` 的正式实现依据。
