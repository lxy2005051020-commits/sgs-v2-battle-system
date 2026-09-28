# Guard / Cover Mechanism Contract

Status ID: `690098`  
Official Name: `援护`  
English Name: `GUARD / COVER`  
Status: `FROZEN`

Freeze Date: `2026-09-12`

本合同用于三国志战略版战斗模拟器中的 `690098 GUARD / 援护` 状态实现。合同冻结的是已经通过当前战报研究与逐问题裁决稳定确认的**外部行为规则**；文中的 `NormalAttackEvent`、`AttackChainContext`、`CoverBuff`、`CoverSlot`、`actualTarget` 等名称是本项目为实现与审计建立的规范术语，不宣称复原官方源码中的真实类名、字段名或函数名。

---

## 1. Classification

```yaml
Category: FUNCTIONAL_STATE
Family: NORMAL_ATTACK_TARGET_REDIRECTION
State_Owner: PROTECTED_TARGET / HOLDER
Linked_Entity: PROTECTOR
Trigger_Event: NORMAL_ATTACK_ONLY
Target_Redirection: SINGLE_PASS_NON_RECURSIVE
Effective_Instance_Limit_Per_Holder: 1
Protector_To_Holder_Cardinality: ONE_TO_MANY
Self_Guard: FORBIDDEN
Refreshable: false
Replaceable: false
Dispellable: false
Cleanseable: false
Charge_Based: false
Duration_Based: true
```

核心定义：

> 援护不是伤害转移、不是承伤末端代扣、也不是受击后被动响应；它是 `NormalAttackEvent` 的目标解析阶段中的一次性目标重定向。援护成功后，援助者直接成为该次普通攻击链的 `actualTarget`，并作为整条攻击链的真实目标被后续节点继承。

形式化表达：

```text
Target Selection
→ originalTarget
→ Cover Check
→ actualTarget
→ Target Lock
→ 后续普通攻击链
```

---

## 2. Core State Model

一个援护实例至少需要表达：

```yaml
CoverBuff:
  holder: protectedTarget
  protector: linkedProtector        # immutable
  sourceUnit: sourceUnit            # immutable provenance
  sourceSkill: sourceSkill          # immutable provenance
  applyRound: battleRoundIndex
  remainingDuration: integer
  isDisabled: boolean
```

强不变量：

```text
holder != null
protector != null
holder.id != protector.id
protector/sourceUnit/sourceSkill 在实例生命周期内不可变
同一 holder 同时最多存在 1 个 CoverBuff 实例
```

允许：

```text
同一 protector 同时保护多个 holder
protector 自己同时被第三人援护
attacker == protector
attacker == actualTarget
source == target（后续反制状态节点中允许）
```

---

## 3. Event-Type Contract

援护触发严格遵守事件类型契约：

```text
触发 Cover Check ⇔ EventType == NORMAL_ATTACK
```

### 3.1 必然进入援护判定的普通攻击

只要底层动作属于新的普通攻击事件，无论来源为何，都进入援护目标解析：

- 正常行动中的普通攻击；
- 连击产生的第二次普通攻击；
- 决斗等机制中创建的普通攻击；
- 嘲讽、锁定等强制选敌后发起的普通攻击；
- 混乱导致的友军误伤普通攻击；
- 其他未来来源，只要其事件契约最终是 `NORMAL_ATTACK`。

### 3.2 绝不进入援护判定的事件

以下均不是新的普通攻击事件，因此不得独立触发援护：

- 主动战法直接兵刃/谋略伤害；
- 突击战法自身的派生伤害节点；
- 反击伤害；
- 持续伤害；
- 普攻链内其他非 `NORMAL_ATTACK` 的派生伤害；
- 任何仅在表现或文本上“像砍了一刀”、但事件类型不是普通攻击的技能伤害。

已核验的援护执行记录中，真实援护执行前置均为普通攻击事件；非普攻事件触发援护的记录为 0。

实现禁止：

```text
if damage.isPhysical:
    resolveCover()
```

正确入口必须是事件类型级判断，而不是伤害类型、动画或技能类别推断。

---

## 4. Exact Pipeline Position

援护严格属于 `NormalAttackEvent` 的 **Target Resolution Phase**，并且发生在目标正式锁定、所有目标类事件、防御判定和伤害计算之前。

冻结时序：

```text
NormalAttackEvent
│
├─ 1. Target Selection
│      └─ originalTarget
│
├─ 2. Target Resolution
│      └─ Cover Check
│          └─ actualTarget
│
├─ 3. Target Lock
│
├─ 4. Target / Attack Event Dispatch
│
├─ 5. Defense Resolution
│      ├─ Evasion / 规避
│      ├─ Resistance / 抵御
│      ├─ Damage Reduction / 受击前减伤
│      └─ Defense Attributes / 统率、智力等
│
├─ 6. Damage Resolution
│
└─ 7. Derived Attack Pipeline
       ├─ 突击
       ├─ 普攻附加效果
       ├─ 群攻 / Splash
       ├─ 受击反制
       └─ 其他已排队派生节点
```

援护绝对不是：

```text
ON_NORMAL_ATTACK_RECEIVED
→ CoverBuff listener
→ 事后把伤害搬给 protector
```

模拟器应把它实现为普通攻击目标解析的一部分。

---

## 5. originalTarget vs actualTarget

### 5.1 originalTarget

`originalTarget` 只表示：

> 本次普通攻击在寻敌阶段最初选择了谁。

援护成功后，它降级为 Selection Provenance / 溯源字段。

### 5.2 actualTarget

援护成功后：

```text
actualTarget = protector
```

并成为该次普通攻击链唯一的运行时主目标。

后续所有与目标有关的正常逻辑统一读取 `actualTarget`，包括：

- 规避；
- 抵御；
- 受击前减伤；
- 统率、智力等防御属性；
- 目标当前兵力；
- 目标是否主将；
- 目标是否具有某状态；
- 突击/追击/普攻特效的目标；
- 受击类事件与反制；
- 群攻主目标锚点。

例如：

```text
originalTarget = 敌军主将 B
protector = 副将 C
→ actualTarget = C
```

后续“若目标为主将”的条件必须检查 C；若 C 不是主将，则条件为 False。

---

## 6. originalTarget Zero-Awareness Rule

Cover Check 发生在所有“成为攻击目标 / 被普通攻击 / 受击”事件派发之前。

因此援护成功后，`originalTarget`：

```text
不会收到 Targeted 事件
不会收到 ON_NORMAL_ATTACK_RECEIVED
不会收到 ON_DAMAGED
不会触发受击监听器
不会读取其防御侧属性
不会消耗其规避/抵御
不会参与该次攻击链的目标条件判断
```

当前核验的 1,801 次真实援护执行记录中，援护执行后原目标在当前攻击链后续节点出现目标/受击日志的记录为 `0 / 1,801`。

---

## 7. Cover Check Algorithm

每次新的普通攻击事件只对 `originalTarget` 执行一次非递归援护解析：

```text
resolveCover(originalTarget):
    cover = originalTarget.coverSlot.instance

    if cover == null:
        return originalTarget

    if cover.isDisabled:
        return originalTarget

    if !cover.protector.is_alive():
        return originalTarget

    return cover.protector
```

关键约束：

```text
Single-Pass
Non-Recursive
No Chain Guard
```

如果：

```text
B 由 C 援护
C 又由 D 援护
```

A 普攻 B 时结果仍然是：

```text
B → C → STOP
```

绝不会继续变成 `B → C → D`。

当前全库核验中，同一次普通攻击发生两次及以上链式援护的记录为 0。

---

## 8. Attack-Chain Target Lock

援护一旦成功：

```text
AttackChainContext.actualTarget = protector
```

该值在本次普通攻击链内固定，不重新援护、不重新寻敌、不回弹到 `originalTarget`。

后续以主目标为基准的节点直接继承：

- 普通攻击主体伤害；
- 普攻附加效果；
- 突击节点；
- 追击/追加类派生节点；
- 受击反制；
- 目标身份/属性/状态条件；
- 群攻的主目标锚点。

派生节点绝对不会再次执行援护判定。

---

## 9. Combo / Multiple Normal Attacks

连击产生的第二次普通攻击是一个全新的普通攻击事件：

```text
NormalAttackEvent #1
→ Target Selection #1
→ Cover Check #1
→ AttackChainContext #1
→ 完整结算
→ Context #1 销毁

NormalAttackEvent #2
→ Target Selection #2
→ Cover Check #2
→ AttackChainContext #2
```

因此第二次普通攻击：

- 重新寻敌；
- 原目标可以与第一次不同；
- 重新读取最新援护状态；
- 重新执行完整 Cover Check；
- 不继承第一次普通攻击的 `actualTarget`。

---

## 10. Duration-Based, Not Charge-Based

援护是持续时间型 Buff，不存在触发次数或层数消耗。

```text
Cover Trigger
!= consume()
!= decrementCharge()
!= removeStatus()
```

只要援护实例仍有效：

- 同一回合被多名敌人连续普攻，可以每次援护；
- 连击第二次普攻可以再次援护；
- 决斗中每一个独立普通攻击事件可以分别援护；
- 援护触发本身不会缩短 Duration。

---

## 11. Holder-Owned Lifecycle

援护实例挂载在被保护者 `holder` 身上，其生命周期由 Holder 自身行动轮次管理，与 Protector 的行动轮次无关。

```text
holder.OnActionStart
→ CoverBuff lifecycle tick
```

```text
protector.OnActionStart
→ 不推进该 CoverBuff Duration
```

### 11.1 Apply-Round Exemption

施加回合内，Holder 即使随后触发 `OnActionStart`，也不扣减本次新援护的 Duration。

正确规则是：

```text
if currentRound == cover.applyRound:
    skip duration tick
else:
    remainingDuration -= 1
```

而不是“无条件跳过施加后的第一次 OnActionStart”。

因此如果 Holder 在施加前已经完成本回合行动，下一战斗轮次的 `OnActionStart` 仍会正常扣减。

### 11.2 Expiration Boundary

当进入可扣减轮次且：

```text
remainingDuration: 1 → 0
```

则必须在 Holder 的 `OnActionStart` 节点立即物理删除援护，且早于本次行动中的战法发动和普通攻击。

```text
开始行动
→ Duration Tick
→ remainingDuration == 0
→ remove CoverBuff
→ 后续战法/普攻
```

该 Buff 不覆盖这次行动周期。

---

## 12. Physical Removal Rule

援护一旦成功创建，战斗中不存在主动驱散、净化、破盾式消耗或其他中途 `RemoveBuff` 机制。

冻结规则：

```text
唯一正常物理删除入口：
Holder.OnActionStart
→ Duration 到期
→ remove CoverBuff
```

已核验的 1,132 次“援护效果已消失”物理注销记录中，`1,132 / 1,132` 均发生在 Holder 自身 `OnActionStart` 的到期节点；中途技能驱散、净化、Protector 死亡或承伤导致提前删除的记录为 0。

战斗结束时状态容器整体销毁属于 Battle Runtime 清理，不属于战斗中援护机制的主动删除规则。

---

## 13. Unique Slot / First-In Wins

援护是纯二元功能状态，不存在“更强的援护”概念。

```yaml
Strength_Tier: NONE
Stacking: FORBIDDEN
Refresh: FORBIDDEN
Replacement: FORBIDDEN
First_In_Wins: true
```

只要 Holder 身上已有任意尚未物理删除的 CoverBuff：

```text
new ApplyCover(holder)
→ CONFLICT
→ 新实例施加失败
```

后续施加不会：

- 刷新 Duration；
- 替换 Protector；
- 替换 Source；
- 延长持续时间；
- 覆盖旧实例。

战报提示“已存在同等或更强的「援护」效果”属于通用冲突文案，不能据此推导援护存在强弱等级。

当前全库未发现“援护效果已刷新”记录。

---

## 14. Zombie Buff / Slot Occupancy

`CoverSlot` 的占用只取决于 CoverBuff 实例是否仍存在，而不取决于它当前是否可以实际挡刀。

因此以下实例仍然占槽：

```text
cover.protector 已死亡
cover.isDisabled == true
```

它们属于本项目定义的 Zombie CoverBuff：

```text
实例存在
→ 继续占用唯一援护槽
→ 继续走 Holder 生命周期
→ Cover Check 时被跳过
```

在旧实例物理删除之前，任何新援护都因槽位冲突施加失败。

当旧实例到期 `remove()` 的同一瞬间：

```text
CoverSlot = EMPTY
```

不存在“本回合曾经有过援护”的冷却或残留锁。已核验到同一回合旧援护行动初消失后、稍后成功重新挂载新援护的案例。

---

## 15. Protector Liveness

Cover Check 对 Protector 的核心动态强校验是：

```text
protector.is_alive()
```

如果 Protector 已经死亡：

```text
CoverBuff 不删除
CoverSlot 仍占用
Duration 继续正常流逝
Cover Check 返回 originalTarget
```

死亡瞬间不会遍历其他 Holder 并删除其援护实例。

注意与全局死亡清理规则的关系：

> Protector 阵亡会清理 Protector 自身持有的状态，但挂在其他 Holder 状态容器中的 CoverBuff 是独立实例，仅保存对 Protector 的不可变引用，因此不会被 Protector 死亡级联物理删除。

---

## 16. Control States and Runtime Eligibility

已成功施加的援护，不要求 Protector 具备行动能力。

以下状态不会因为 Protector 当前不能正常行动而直接阻止已有援护挡刀：

- 震慑；
- 缴械；
- 计穷；
- 混乱；
- 虚弱；
- 其他一般行动限制。

只要 Protector 存活且 CoverBuff 未被特殊失效标记，援护仍可执行。

### 16.1 伪报

对已经成功派生并挂载到友军身上的 CoverBuff：

```text
Protector 后续被伪报
→ 不追溯撤销已创建 CoverBuff
→ 不直接令既有 CoverBuff 物理删除
```

因此不得实现通用规则：

```text
sourceSkill disabled
→ remove all derived CoverBuffs
```

---

## 17. 军心动摇 / Cascading Suppression

军心动摇是已确认的特殊失效通道。

其语义不是 Cover Check 临时检查某个控制状态，而是：

```text
Protector 进入军心动摇
→ 源装备特技【援助】被压制
→ 依赖链传播
→ 由该源特技派生的 CoverBuff.isDisabled = true
```

`isDisabled` 只是 Effect Suppression Mask：

```text
功能响应被屏蔽
生命周期时钟不暂停
```

因此：

```text
isDisabled == true
→ Cover Check 直接跳过
→ remainingDuration 仍按 Holder.OnActionStart 正常推进
→ 到期仍正常物理删除
```

军心动摇不存在后续解除/恢复阶段，因此本合同不定义由其产生的 CoverBuff Reactivation 机制。

---

## 18. Apply-Time Architecture

援护施加必须区分两个层次：

```text
Source Ability Guard
!=
CoverBuff Apply Guard
```

### 18.1 Source Ability Guard

源战法/特技先按自身规则决定能否成功发动。

例如主动战法【千里驰援】：

- Protector 必须存活；
- 震慑会阻止行动；
- 计穷会阻止主动战法发动；
- 缴械不阻止主动战法；
- 虚弱不阻止纯增益类主动战法发动；
- 伪报不等于封禁主动战法；
- 混乱可能改变选敌，但不当然禁止施法动作；
- 仍需通过该战法自身发动概率等来源规则。

装备特技【援助】按其准备阶段触发逻辑执行。

这些属于源能力准入，不能硬编码进通用 `CoverBuff` 构造器。

### 18.2 CoverBuff Apply Guard

一旦已经进入通用援护挂载阶段，至少需要满足：

```text
protector != null
protector.is_alive() == true
holder != null
holder.is_alive() == true
protector.id != holder.id
protector 与 holder 属于合法友军关系
holder 当前没有既存 CoverBuff 实例
```

推荐伪代码：

```text
ApplyCover(protector, holder, source):
    if protector == null or !protector.is_alive():
        return INVALID_SOURCE

    if holder == null or !holder.is_alive():
        return INVALID_TARGET

    if protector.id == holder.id:
        return SELF_GUARD_FORBIDDEN

    if !isAlly(protector, holder):
        return INVALID_RELATION

    if holder.coverSlot.instance != null:
        return CONFLICT

    holder.coverSlot.instance = new CoverBuff(...)
    return SUCCESS
```

---

## 19. Holder Death Apply Guard

系统不会向已经死亡的 Holder 创建援护实例。

存在双重守卫：

```text
TargetSelector
→ “友军全体”等候选池过滤死亡单位
```

以及：

```text
add_buff / can_receive_buff
→ 再次检查 holder.is_alive()
→ 死亡则拒绝创建实例
```

因此死亡 Holder：

```text
不创建 CoverBuff
不占 CoverSlot
不产生成功施加日志
```

---

## 20. Multi-Target Application

同一个源效果向多个友军施加援护时，按 Holder 独立遍历结算，不是整体原子事务。

```text
for holder in selectedTargets:
    ApplyCover(protector, holder)
```

例如：

```text
B 已有援护
C 槽位为空
```

同一源效果尝试援护 B、C：

```text
B → CONFLICT
C → SUCCESS
```

B 的失败不会中断 C 的施加。

---

## 21. One Protector Can Protect Multiple Holders

数据关系为：

```text
Protector 1 → N CoverBuffs
Holder    1 → max 1 CoverBuff
```

例如：

```text
Protector A
├─ CoverBuff #1 → Holder B
└─ CoverBuff #2 → Holder C
```

两个 Holder 上的实例：

- 独立创建；
- 独立占槽；
- 独立保存 Duration；
- 独立随各自 Holder 的 `OnActionStart` 推进；
- 生命周期互不干扰。

---

## 22. Self-Guard Is Forbidden

援护目标选择严格排除 Protector 本人。

```text
protector.id != holder.id
```

当前核验的援护施加与执行记录中未出现 `protector == holder`。

注意：该不变量不等价于 `attacker != protector`。在混乱环境下，Protector 完全可能成为本次普通攻击的攻击者。

---

## 23. Confusion / Friendly-Fire Normal Attack

援护不检查攻击者与 Holder 是否敌对。

触发条件只看：

```text
EventType == NORMAL_ATTACK
AND Holder has CoverBuff
AND CoverBuff runtime guards pass
```

因此混乱导致友军普攻受援者时，援护照常触发。

极端但合法的结果：

```text
C 援护 B
C 因混乱普通攻击 B
→ originalTarget = B
→ Cover Check
→ actualTarget = C
```

于是：

```text
attacker == actualTarget == C
```

系统不会因攻击者和目标是同一实体而做特殊短路。

---

## 24. Self-Attack Role Semantics

当 `attacker == actualTarget` 时，仍按标准普通攻击角色模型执行。

同一个实体分别作为：

```text
AttackerRole(C)
TargetRole(C)
```

攻击侧读取 C 的攻击属性、攻击增益与攻击条件；防御侧同时读取 C 的统率、规避、抵御、减伤及受击状态。

不得因为对象引用相同而提前返回。

---

## 25. Self-Attack Event Dispatch and Reactions

即使 `attacker == actualTarget`：

```text
ON_NORMAL_ATTACK_RECEIVED(owner=C)
ON_DAMAGED(owner=C)
```

等受击事件仍按规则派发。

若受击反制的目标规则为：

```text
ReactionTarget = ctx.attacker
```

此时反制目标也会得到 C 自己。

后续若反制状态节点尝试：

```text
ApplyStatus(source=C, target=C)
```

状态系统不得仅因 `source == target` 拒绝；应由目标侧正常的 `can_receive_status()` 规则决定，例如存活、洞察/免控、状态互斥等。

---

## 26. Forced Target Selection

嘲讽、锁定目标、指定普攻对象等机制只负责覆盖寻敌算法并确定 `originalTarget`。

冻结顺序：

```text
Forced Target Selection
→ originalTarget
→ Cover Check
→ actualTarget
```

不存在任何已确认的“强制选敌可以穿透援护”特权。

因此：

```text
强制攻击 B
B 被 C 援护
→ actualTarget = C
```

---

## 27. Splash / 群攻 Interaction

援护成功后，群攻主目标锚点是 `actualTarget`，不是 `originalTarget`。

例如：

```text
A 原本普攻 B
C 援护 B
→ actualTarget = C
```

群攻定义为“对主目标以外的其他有效敌军造成伤害”，因此副目标补集按：

```text
SplashTargets = CurrentValidEnemies - {actualTarget}
```

若敌方为 B、C、D：

```text
C → 承受直接普通攻击
B → 可作为群攻副目标承受溅射
D → 可作为群攻副目标承受溅射
C → 不重复承受自己的群攻副伤害
```

### 27.1 Just-In-Time Evaluation

群攻副目标集合不在攻击链创建时提前快照。

正确模型：

```text
轮到 Splash Node 真正执行
→ 读取当时最新战场存活/有效状态
→ 以 context.actualTarget 为排除锚点
→ 即时生成 SplashTargets
```

因此：

```text
actualTarget = AttackChain-level fixed binding
SplashTargets = Node-level late binding / JIT
```

---

## 28. actualTarget Death Mid-Chain

如果 Protector 成为 `actualTarget` 后在攻击链中途死亡：

```text
actualTarget 仍然保持该 Protector
```

绝不会：

- 回弹到 `originalTarget`；
- 重新执行 Cover Check；
- 重新寻敌；
- 因此把后续主目标节点改回原目标。

### 28.1 Damage Nodes

针对已死亡 `actualTarget` 的后续单体伤害不再产生有效兵力扣减，按节点自身死亡守卫处理。

### 28.2 Status Nodes

后续尝试向死亡 `actualTarget` 施加状态时，命中死亡守卫并拒绝挂载；可产生“已经死亡，无法获得某效果”类日志。

### 28.3 Counter / Reaction Nodes

死亡目标自身的受击反制立即停止，不再继续触发。

### 28.4 Independent Target Nodes

若派生战法的后续段拥有**独立目标规则**，例如额外指定敌军主将，则该节点继续按自己的目标解析执行，不因 `actualTarget` 死亡而自动取消。

---

## 29. No Premature Attack-Chain Abort

`AttackChainContext` 的生命周期独立于 `actualTarget` 的生命周期。

```text
actualTarget 死亡
!=
abort entire AttackChainContext
```

攻击链中已生成、排队的后续节点仍按顺序完整遍历；每个节点自行执行自己的：

- `target.is_alive()`；
- `can_receive_status()`；
- 独立目标解析；
- 其他节点级合法性守卫。

推荐架构原则：

```text
Chain-level:
  负责顺序与上下文

Node-level:
  负责合法性与实际效果
```

严禁：

```text
if !context.actualTarget.is_alive():
    break
```

作为普通攻击链的全局终止条件。

---

## 30. Interaction with Damage Share / Distribution

援护与后续伤害重分配的职责边界冻结为：

```text
Target Selection
→ Cover Redirection
→ actualTarget 锁定
→ Defense Resolution
→ Damage Redistribution
→ Final Troop Loss
```

因此援护成功后：

```text
Initial Damaged Entity = actualTarget
```

`originalTarget` 的分担/分摊关系完全旁路；后续伤害重分配系统只读取 `actualTarget` 自己的相关关系。

本合同只冻结**援护位于分担/分摊之前**这一交互顺序；分担/分摊内部如何派发事件、扣兵和处理死亡，由各自机制合同负责，不属于援护合同范围。

---

## 31. Immutable Provenance

CoverBuff 创建成功后，以下引用在整个生命周期内严格不可变：

```text
protector
sourceUnit
sourceSkill
```

不存在：

- 中途换绑援助者；
- 援护权移交；
- 用后来施加失败的援护覆盖 Source；
- 动态替补；
- 原实例内部刷新为新 Protector。

当前核验的 438 个经历多次承伤的完整援护生命周期中，同一实例援助者动态漂移记录为 0。

---

## 32. Source Ability Guard vs Runtime Guard

必须严格分离三层职责：

```text
1. Source Ability Phase
   → 源技能能否发动

2. CoverBuff Apply Phase
   → 能否创建并占用 Holder 的唯一援护槽

3. Cover Runtime / Trigger Phase
   → 本次普通攻击是否能真正重定向
```

禁止把源技能条件硬编码进通用 Cover Check，也禁止把运行期 Protector 状态错误回溯成 Apply 期状态删除。

---

## 33. Recommended Simulator Contract

推荐核心数据结构：

```text
CoverBuff
├─ holder
├─ protector            // readonly
├─ sourceUnit           // readonly
├─ sourceSkill          // readonly
├─ applyRound
├─ remainingDuration
└─ isDisabled
```

推荐普通攻击入口：

```text
NormalAttackSystem.resolveTarget(attacker):
    originalTarget = targetSelector.select(attacker)
    actualTarget = coverSystem.resolve(originalTarget)

    return TargetResolution(
        originalTarget = originalTarget,
        actualTarget = actualTarget
    )
```

随后：

```text
AttackChainContext.actualTarget = TargetResolution.actualTarget
```

从 `Target Lock` 开始，正常攻击业务统一读取 `actualTarget`。

---

## 34. MUST Rules

模拟器实现必须满足：

1. `NORMAL_ATTACK` 是援护判定的唯一事件入口；
2. Cover Check 必须发生在目标锁定与所有受击/防御事件之前；
3. 援护成功后必须令 Protector 成为整条当前攻击链的 `actualTarget`；
4. 同一普通攻击只允许一次、非递归重定向；
5. 派生节点必须继承已锁定 `actualTarget`，除非节点本身定义独立目标规则；
6. 连击等新的普通攻击事件必须重新寻敌、重新 Cover Check；
7. 防御侧属性、状态、目标身份条件必须读取 `actualTarget`；
8. Holder 同时最多只能存在一个 CoverBuff；
9. 既存实例无论正常、disabled 或 Protector 已死，都必须继续占槽直到物理删除；
10. 援护触发不得消费层数或次数；
11. Duration 必须由 Holder 的 `OnActionStart` 管理；
12. 施加回合内 Holder 的行动开始不得消耗新援护 Duration；
13. Duration 到 0 时必须在 Holder 行动逻辑前立即删除；
14. Protector 死亡不得级联删除挂在其他 Holder 身上的 CoverBuff；
15. `isDisabled` 不得暂停生命周期；
16. `protector/sourceUnit/sourceSkill` 必须视为实例级不可变引用；
17. 强制选敌只允许决定 `originalTarget`，不得绕过 Cover Check；
18. 群攻副目标必须以 `actualTarget` 为排除锚点并在群攻节点执行时即时计算；
19. `actualTarget` 中途死亡不得导致攻击链全局提前终止；
20. 援护必须先于分担/分摊等伤害重分配机制解析。

---

## 35. MUST NOT Rules

模拟器实现禁止：

1. 把援护实现成 Damage Transfer；
2. 在 `ON_NORMAL_ATTACK_RECEIVED` 后再修改目标；
3. 对突击、反击、持续伤害等非普通攻击事件独立调用 Cover Check；
4. 对新的 `actualTarget` 递归执行第二次援护；
5. 派生节点重新检查援护；
6. 援护成功后继续用 `originalTarget` 做防御、状态、身份条件判断；
7. 因 Protector 被震慑、缴械、计穷、混乱、虚弱而自动删除已有 CoverBuff；
8. 因 Protector 死亡而删除其他 Holder 上的 CoverBuff；
9. 允许 disabled / zombie CoverBuff 释放槽位；
10. 刷新、覆盖或替换已有援护实例；
11. 允许 `protector == holder`；
12. 因 `attacker == actualTarget` 而跳过攻击或受击事件；
13. 提前快照群攻副目标列表；
14. 因 `actualTarget` 死亡直接 `break` 整条攻击链；
15. 将源技能的施法准入条件全部塞进通用 CoverBuff 构造器或 Cover Check。

---

## 36. Frozen Edge Cases

| Edge Case | Frozen Result |
|---|---|
| 连击第二次普攻 | 新 `NormalAttackEvent`，重新寻敌与援护 |
| 决斗普攻 | 属于普通攻击事件则正常援护 |
| 反击 | 不援护 |
| 突击战法伤害 | 不独立援护，只继承当前链 `actualTarget` |
| 强制选敌 / 嘲讽 / 锁定 | 只决定 `originalTarget`，仍可被援护 |
| 混乱友军普攻 | 正常援护，不检查敌我关系 |
| Protector 普攻自己保护的 Holder | 可被援护重定向回 Protector，形成自我普攻 |
| 自我普攻后的受击反制 | 正常触发，可把反制目标指回自己 |
| `source == target` 的反制状态 | 不因同实体自动拒绝，由状态系统目标守卫决定 |
| 多个援护来源竞争同一 Holder | First-In Wins，后续施加失败 |
| Protector 同时保护两名友军 | 允许，各 Holder 独立实例 |
| Protector 死亡 | 已有 Buff 留存并占槽，运行期不再重定向 |
| 军心动摇 | 派生 Buff `isDisabled=true`，Duration 继续流逝 |
| 伪报 | 不追溯删除已挂载 CoverBuff |
| 援护到期 | Holder.OnActionStart 立即物理删除 |
| 到期后同回合再次施加 | 允许，删除瞬间槽位立即 EMPTY |
| Protector 中途死亡成为 `actualTarget` | 不回弹原目标；节点级守卫继续遍历 |
| 群攻 | 主目标锚点为 `actualTarget`，副目标 JIT 计算 |

---

## 37. Evidence Summary

本次冻结使用的问题驱动研究结论与战报大盘核验。已明确记录的统计证据包括：

```text
真实援护执行记录：1,801
→ 普通攻击前置：1,801 / 1,801
→ 非普攻触发援护：0

援护物理注销记录：1,132
→ Holder.OnActionStart 到期注销：1,132 / 1,132
→ 中途驱散/净化/死亡提前删除：0

完整多次承伤援护生命周期：438
→ 同一 CoverBuff Protector 动态漂移：0

链式援护（同一普通攻击 >= 2 次重定向）：0
自我援护 protector == holder：0
援护效果刷新：0
```

统计样本用于支撑外部行为合同，不应被解释为官方源码结构证明。

---

## 38. Freeze Decision

```yaml
Mechanism_Status: FROZEN
Core_Target_Redirection: CONFIRMED
Trigger_Event_Contract: CONFIRMED
AttackChain_Target_Lock: CONFIRMED
Lifecycle: CONFIRMED
Slot_Exclusion: CONFIRMED
Protector_Death_Behavior: CONFIRMED
Suppression_Behavior: CONFIRMED
Forced_Target_Interaction: CONFIRMED
Splash_Interaction: CONFIRMED
Confusion_Self_Attack_Edge: CONFIRMED
Implementation_Blocking_Unresolved: 0
```

最终冻结定义：

> `690098 援护 / GUARD` 是一种挂载在被保护者 Holder 身上的、单槽位、不可刷新、不可覆盖、不可主动驱散的持续型功能状态。它仅在新的 `NormalAttackEvent` 的目标解析阶段执行一次非递归 Cover Check；成功时将不可变 Protector 引用解析为该次攻击链的 `actualTarget`，并在目标锁定后使后续正常目标语义全部与 `originalTarget` 脱钩。援护实例的生命周期由 Holder 自身 `OnActionStart` 推进；Protector 死亡或特殊失效只改变运行资格，不会提前删除实例或释放槽位。
