# Stage 9 铁索连环（Chain）机制冻结记录

> **项目**: 三国志战略版战斗模拟器 V2  
> **状态**: `CHAIN CORE MECHANICS FROZEN`  
> **用途**: 记录 Stage 9 铁索连环机制逐项确认后的单一事实基线。后续实现、审计与研究文档不得继续沿用与本文件冲突的旧推论。  
> **说明**: 本文件记录当前项目已逐项确认的游戏机制规则；它不等同于官方内部代码结构，也不用于反推官方调用栈。

---

## 1. 触发基数与反馈数学语义

铁索以**传播源节点本次已经结算的受伤数值**作为输入，再乘传播源节点当前有效铁索状态的比例：

```text
TriggerNodeResolvedDamage
→ × TriggerNode.activeChainEffect.ratio
→ ChainCalculatedDamage
```

即：

```text
ChainCalculatedDamage = TriggerNodeResolvedDamage × ChainRatio
```

例：

```text
B 本次受到 500
B 当前铁索比例 = 50%

→ 对每个合法传播目标：500 × 50% = 250
```

铁索反馈目标不重新执行基础攻防伤害公式。

### 1.1 0 伤害仍可执行铁索

铁索触发不要求 `resolvedDamage > 0`。只要该次属于合法伤害结算、传播源节点仍存活且铁索仍有效，就会执行铁索；若本次结算伤害为 0，则传播结果也全部为 0：

```text
resolvedDamage = 0
→ 0 × ChainRatio = 0
→ Chain 仍执行，但反馈伤害全为 0
```

### 1.2 致死源伤害不传导

若传播源节点在本次原始伤害结算后已经死亡，则本次铁索不再执行：

```text
Source Damage
→ Trigger Node dies
→ Chain = CANCELLED
```

因此铁索真正开始传播时，传播源节点必须仍然存活。

---

## 2. 铁索反馈是独立的真实伤害反馈类型

铁索反馈**不继承原始伤害的兵刃 / 谋略 DamageType**，而是独立的：

```text
TRUE_FEEDBACK / 真实伤害反馈
```

原始攻击如果已经发生暴击，暴击后的受伤数值会自然进入 `TriggerNodeResolvedDamage`；但铁索反馈本身**不会再次进行暴击判定**。

```text
原伤害暴击后使 B 受到 1000
ChainRatio = 50%
→ ChainCalculatedDamage = 500
→ 这 500 不会再次暴击
```

### 2.1 反馈数值计算与取整策略（CHNS9-B01 冻结）

铁索连环计算伤害公式：

```text
ChainCalculatedDamage = floor(TriggerNodeResolvedDamage × ChainRatio)
```

取整规则经 1,657 条真实战报边界样本验证（100.0% 吻合，0 矛盾）：
- 采用 **`FLOOR`**（向下取整 / 向零截断 `math.floor`）；
- **不采用**四舍五入（`ROUND_HALF_UP` 存在 808 例反例，`CEIL` 存在 1,656 例反例）；
- 例：`396 × 28.28% = 111.9888 → 111`（若四舍五入为 112 判伪）；`753 × 28.28% = 212.9484 → 212`；`265 × 22.58% = 59.837 → 59`。

此项冻结正式关闭 Finding `CHNS9-B01`。

---

## 3. 铁索反馈的防护、修正与后续响应边界

铁索反馈属于高度受限的派生数值结算。已经确认：

| 机制 | 是否作用于 Chain | 冻结结论 |
|---|---:|---|
| 规避 / Evasion | 否 | `BLOCKED` |
| 抵御 / Barrier | 否 | `BLOCKED` |
| 传播目标自身伤害增减 | 否 | `BLOCKED` |
| 分担 / Share | 否 | `BLOCKED` |
| 再次暴击 | 否 | `BLOCKED` |
| 急救 / FirstAid | 否 | `BLOCKED` |
| 反击 / Counter | 否 | `BLOCKED` |
| 再次铁索 / Chain→Chain | 否 | `BLOCKED` |
| 倒戈 | 否 | `BLOCKED` |
| 攻心 | 否 | `BLOCKED` |
| 刚烈不屈等受击响应 | 否 | `BLOCKED` |

因此铁索反馈不能被实现成“重新发起一次普通攻击 / 完整 Hit”。

当前事实链：

```text
TriggerNodeResolvedDamage
→ × current ChainRatio
→ TRUE_FEEDBACK
→ no Evasion
→ no Barrier
→ no target-side damage modifier
→ no Share
→ no Crit reroll
→ Troop Loss
→ no hit-response callback chain
```

---

## 4. 传播触发资格

### 4.1 正常伤害事件可触发

只要目标进入一次合法伤害结算、结算后仍存活、铁索状态仍有效，就可以触发铁索。已经确认包括：

```text
普通攻击伤害 → Chain ALLOWED
战法伤害 → Chain ALLOWED
持续性伤害（灼烧/中毒/溃逃等） → Chain ALLOWED
群攻伤害 → Chain ALLOWED
反击伤害 → Chain ALLOWED
```

### 4.2 明确例外

以下不属于可再次触发铁索的正常伤害事件：

```text
Chain TRUE_FEEDBACK → Chain = BLOCKED
Share passive numeric settlement → Chain = BLOCKED
```

也就是说，铁索监听的不是“兵力数字变化”，而是具备合法伤害事件资格的伤害结算。

---

## 5. 每个独立伤害段都独立触发

铁索触发粒度为：

```text
PER DAMAGE INSTANCE
```

多段战法：

```text
Hit1
→ Chain1 inline
→ Hit2
→ Chain2 inline
→ Hit3
→ Chain3 inline
```

铁索不是“每个 Skill / Action 最多触发一次”。禁止按 `skill_id` 对铁索触发做整次动作级去重。

---

## 6. 默认执行时序：PER-DAMAGE INLINE

默认规则：

```text
Damage Instance
→ 该段伤害完成
→ 检查传播源仍存活、铁索仍有效
→ 立即执行 Chain
→ Chain 全部结算完成
→ 才继续后续流程
```

已经确认：

```text
普通多段伤害 → 每段后立即 Chain
反击伤害 → Chain INLINE
群攻副目标受伤 → Chain INLINE
```

### 6.1 普通攻击主目标 + 群攻：特殊 Deferred Chain

普通攻击主目标的铁索存在一个已确认的特殊时序：

```text
主目标受到普通攻击伤害
→ 产生主目标 Chain 待执行资格
→ 先结算群攻副目标 1
   → 若其触发 Chain，则立即 Inline 完成
→ 再结算群攻副目标 2
   → 若其触发 Chain，则立即 Inline 完成
→ 群攻全部结束
→ 再执行主目标 Deferred Chain
```

因此：

```text
CleaveTarget Chain = INLINE
NormalAttack MainTarget Chain = DEFERRED UNTIL CLEAVE COMPLETE
```

---

## 7. Deferred Chain 的 JIT 重校验与参数绑定

Deferred Chain 不是已经固化的完整伤害事件，而是“待执行资格”。

### 7.1 执行时必须重新检查

执行时必须重新检查：

```text
source.alive == true
AND
source.activeChainEffect != null
```

任一失败：

```text
→ Discard / Cancel
→ 不产生任何传播伤害
```

因此：

```text
延迟期间传播源死亡 → Cancel
延迟期间铁索被净化 / 到期 / 失效 → Cancel
```

### 7.2 触发伤害基数固定，铁索参数动态读取

Deferred Chain 在触发时保存原始伤害基数，但 owner / ratio 等铁索参数在真正执行时读取当前有效状态：

```text
触发时：
B 受到 500
旧铁索 owner = 庞统, ratio = 20%
→ save triggerDamage = 500

执行前：
新铁索覆盖旧铁索
owner = 后发施加者, ratio = 30%

执行时：
500 × 30% = 150
伤害 / 击杀归当前新 owner
```

因此 Deferred Chain 的语义是：

```text
固定：triggerDamage
动态：activeChainEffect existence / owner / ratio / current metadata
```

---

## 8. 传播目标池

铁索只向**传播源节点同阵营**的合法铁索单位传播。

传播目标必须在轮到自己结算时同时满足：

```text
1. 与传播源节点同阵营
2. 当前存活
3. 当前铁索状态有效
4. 不是传播源节点自身
```

敌对阵营即使也处于铁索状态，也不会进入本次传播目标池。

### 8.1 多目标为广播，不是分摊

每个合法目标都独立获得完整比例：

```text
B 本次受到 500
B ChainRatio = 50%
C、D、E 都是合法目标

C = 250
D = 250
E = 250
```

不是将 250 在目标之间再次均分。

### 8.2 固定槽位顺序

同阵营多目标按固定槽位顺序结算：

```text
主将（槽位 0）
→ 副将 1（槽位 1）
→ 副将 2（槽位 2）
```

不使用 RNG。

### 8.3 JIT Revalidation

传播目标池不是不可变快照。轮到每个目标时重新检查当前资格：

```text
传播开始时 D 合法
→ 先结算 C
→ 期间 D 的铁索状态被移除
→ 轮到 D 时重新检查失败
→ D 跳过
```

因此多目标传播采用：

```text
slot-order iteration + JIT target revalidation
```

### 8.4 某个传播目标死亡不终止其他目标

如果 C 在自己的反馈伤害中死亡：

```text
C death
→ only C settlement ends
→ D / E 仍继续按槽位顺序结算
```

目标死亡不会降低其他目标的反馈值，也不会终止整次广播。

---

## 9. 铁索 owner、ratio 与伤害归属

铁索反馈使用**触发这次传播的源节点自身 activeChainEffect**。

例如：

```text
B 身上的铁索由庞统施加，ratio = 20%
C 身上的铁索由其他武将施加，ratio = 30%

B 受到 500 并触发 Chain
→ 传播到 C 的伤害 = 500 × 20% = 100
→ Chain Damage Owner = 庞统
```

C 自己的 owner / ratio 只在 C 将来作为传播源节点时生效。

### 9.1 伤害与击杀归属

```text
chain_effect_owner = 传播源节点当前铁索施加者
chain_damage_owner = chain_effect_owner
chain_kill_owner = chain_effect_owner
```

原始伤害来源者只提供触发伤害数值，不拥有后续铁索反馈伤害。

---

## 10. 多来源覆盖：单实例、刷新、后发覆盖

同一武将身上的铁索为**单实例状态**，不会叠加成多份独立 Chain。

### 10.1 同一施加者重复施加

```text
同一施加者再次施加
→ 刷新 / 覆盖
→ 持续时间重置为 2 回合
→ 每次受伤仍只触发 1 次 Chain
```

### 10.2 不同施加者重复施加

```text
不同武将后发施加
→ 后发状态覆盖先发状态
→ owner / ratio / 状态参数更新为后发者
→ 持续时间刷新为 2 回合
→ 每次受伤仍只触发 1 次 Chain
```

覆盖后，后续反馈伤害与击杀全部归后发施加者。

---

## 11. 施加者死亡后的状态与收益

铁索状态挂在受状态单位身上。施加者死亡不会自动清除已经存在的铁索：

```text
庞统施加铁索给张飞
→ 庞统死亡
→ 张飞身上的铁索继续正常存在与倒计时
→ 张飞后续合法受伤仍正常触发 Chain
→ 反馈伤害不衰减
→ 伤害 / 击杀统计仍归庞统
```

但需要让已死亡施加者本人获得的后续收益会被跳过，例如战法自带治疗：

```text
Chain Damage 仍成立
→ 庞统统计照常
→ 庞统已死亡
→ [庞统]恢复兵力 XX = 跳过 / 丢弃
```

因此必须区分：

```text
state_valid
effect_owner_alive
owner_can_receive_followup_benefit
```

---

## 12. 状态持续时间与 ACTION_START

铁索持续 2 回合，持续时间在**被施加铁索单位自身的 `[单位]开始行动` 节点**扣减与到期结算：

```text
[张飞]开始行动
→ Chain duration--
→ 若 1 → 0，则立即到期并移除
```

不是全局 RoundEnd 统一扣减。

### 12.1 到期优先于持续伤害

同一个 ACTION_START 节点：

```text
[张飞]开始行动
→ 铁索 1 → 0
→ 铁索立即失效移除
→ 再结算灼烧 / 中毒 / 溃逃等持续伤害
→ 此次持续伤害不能触发已到期铁索
```

即至少存在：

```text
Chain expiry/tick
BEFORE
periodic damage settlement
```

### 12.2 震慑不阻止持续时间扣减

即使单位因震慑无法实际行动，ACTION_START 生命周期仍发生：

```text
轮到张飞
→ [张飞]开始行动
→ Chain duration 正常 -1 / 到期处理
→ 其他 ACTION_START 状态处理
→ 因震慑跳过实际行动
```

因此“无法行动”不等于跳过铁索倒计时。

---

## 13. 净化 / 驱散

铁索属于可被净化 / 驱散的负面状态。

```text
Cleanse / Dispel Debuff succeeds
→ Chain immediately removed in the same micro-step
```

无需等待回合结束。

如果存在 Deferred Chain：

```text
Deferred Chain pending
→ source Chain 被净化
→ 执行时 activeChainEffect == null
→ Cancel / Discard
```

净化后再次施加铁索，视为一个全新的实例：

```text
new duration = 2
new owner = 本次施加者
new ratio = 本次效果参数
```

不继承旧状态的 duration / owner / ratio。

---

## 14. 兵力截断、统计与击杀

铁索计算伤害仍受当前剩余兵力上限截断：

```text
appliedTroopLoss = min(ChainCalculatedDamage, CurrentTroops)
```

例如：

```text
ChainCalculatedDamage = 250
目标当前兵力 = 100
→ 实际损失 100
→ 目标死亡
```

伤害统计按**实际兵力损失**计入铁索 owner：

```text
calculatedDamage = 250
appliedTroopLoss = 100
creditedDamage = 100
killOwner = chain_effect_owner
```

不会把 overkill 的虚空数值计入伤害统计。

---

## 15. 与群攻 / 反击 / 分担的跨机制矩阵

已确认：

```text
Cleave → Chain = ALLOWED
Counter → Chain = ALLOWED
Share Damage → Chain = BLOCKED
Chain → Chain = BLOCKED
Chain → Share = BLOCKED
Chain → FirstAid = BLOCKED
Chain → Counter = BLOCKED
```

其中群攻可使多个副目标分别独立触发自己的 Chain；每一个合法 Damage Instance 都是独立触发机会。

---

## 16. Stage 9 / Stage 8 架构含义

铁索不应复用群攻的完整派生防护链。

群攻：

```text
Derived Damage
→ Evasion / Barrier
→ Share
→ Troop Loss
→ selective callbacks
```

铁索：

```text
Resolved Trigger Damage
→ × current ChainRatio
→ TRUE_FEEDBACK
→ direct restricted troop-loss settlement
→ no Evasion / Barrier / Modifier / Share / hit callbacks
```

Stage 9 因此需要能够表达不同 `DerivedDamageKind` / provenance 对应的**不同许可矩阵**，而不是用一个统一的 Derived Damage Pipeline 把所有派生伤害硬塞成相同流程。

该机制冻结记录不构成 Stage 8 Formal Reopen；具体接口仍应在 Stage 9 设计阶段评估。

---

## 17. 冻结声明

以下铁索核心问题不再列为 Stage 9 待研究项：

- 触发伤害基数与比例；
- 反馈数值取整策略：`floor(TriggerNodeResolvedDamage * ChainRatio)`（CHNS9-B01）；
- 0 伤害触发；
- 源节点致死截断；
- TRUE_FEEDBACK 类型；
- 规避 / 抵御 / 目标侧增减伤 / 分担；
- 暴击、急救、反击、倒戈、攻心、刚烈等响应；
- Chain 自递归；
- 正常伤害、持续伤害、群攻、反击对 Chain 的触发资格；
- Share Damage 对 Chain 的阻断；
- 每段伤害独立触发；
- 默认 Inline 与普通攻击主目标的特殊 Deferred 时序；
- Deferred Chain 的执行时 JIT 重校验与参数绑定；
- 同阵营传播、槽位顺序、广播模型、JIT 目标复核；
- 多来源覆盖、owner / ratio 归属；
- 施加者死亡后的状态存续与治疗丢弃；
- ACTION_START 倒计时、到期优先级与震慑边界；
- 净化、重新施加；
- overkill 截断、伤害统计与击杀归属。

**最终状态：`CHAIN CORE MECHANICS FROZEN`。**
