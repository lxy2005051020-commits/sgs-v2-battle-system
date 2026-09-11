# R3 群攻与铁索连环伤害基数与 Pipeline 研究报告 (v2 - Cleave/Chain Frozen Sync)

> **研究基线 Commit**: `de80a4ec30fb3bf50220a719011478116bd34e5b` (main)  
> **群攻机制冻结记录**: `STAGE9_CLEAVE_MECHANICS_FREEZE_RECORD.md`  
> **铁索机制冻结记录**: `STAGE9_CHAIN_MECHANICS_FREEZE_RECORD.md`  
> **数据文件**: `evidence/r3_cleave_damage_data.json`, `evidence/r4_chain_damage_data.json`, `evidence/r6_death_near_fendan.json`  
> **核心任务**: 统一派生伤害基数与 Pipeline 边界，并以逐项确认后的冻结记录覆盖与其冲突的旧统计推论。

---

## 一、 群攻（Cleave）真实伤害机制与最终裁决

### 1. 历史全库统计
在 1,303 份战报中提取出 **2,258 个包含 2 个副目标的群攻事件**：
- **副目标承受完全相同伤害**: **1,938 个 (85.8%)**
- **副目标承受不同伤害**: **320 个 (14.2%)**

旧版研究曾将部分差异解释为“副目标自身增减伤 Modifier 再入”。该解释已经被后续逐项机制确认推翻，**不得继续作为群攻实现依据**。

### 2. 群攻伤害基数（已冻结）
群攻以触发群攻的主攻击 **最终结算伤害** 为派生基数：

```text
CleaveDerivedDamage = MainAttackFinalDamage × CleaveRatio
```

明确结论：
1. 副目标 **不重新执行基础攻防伤害公式**；
2. 群攻使用主攻击最终结算出的伤害值进行比例派生；
3. 群攻派生伤害继承原攻击 `DamageType`。

### 3. 群攻 Pipeline 重入边界（已冻结）

- 可以被规避；
- 可以被抵御，成功后消耗 1 次抵御；
- 不重新受到副目标自身伤害增减效果影响；
- 可以被分担；
- 可以触发急救；
- 不能触发反击；
- 不能再次触发群攻；
- 兵刃型群攻可按规则触发倒戈；谋略型群攻可按规则触发攻心。

```text
MainAttackFinalDamage
→ × CleaveRatio
→ CleaveDerivedDamage
→ Evasion
→ Barrier
→ Share（若存在）
→ Troop Loss
→ Allowed post-damage recovery callbacks
```

---

## 二、 铁索连环（Iron Chain）真实伤害机制与最终裁决

### 1. 历史统计与冻结优先级

历史全库研究在 1,522 份战报中提取出 11,104 个多目标铁索反馈事件。历史统计曾对 Barrier / Evasion / Modifier / Share / FirstAid 等边界作出类推或统计性解释。

本轮已对铁索逐项完成机制确认。**若历史统计解释与 `STAGE9_CHAIN_MECHANICS_FREEZE_RECORD.md` 冲突，以冻结记录为准。**

### 2. 铁索伤害基数（已冻结）

铁索使用传播源节点本次已经结算的受伤数值作为输入，再乘传播源节点**执行时当前有效铁索状态**的比例：

```text
ChainCalculatedDamage
= TriggerNodeResolvedDamage × CurrentChainRatio
```

铁索反馈目标不重新执行基础攻防公式。

若本次合法伤害结算值为 0，铁索仍会执行，但所有反馈值为 0。

若传播源节点在本次伤害后死亡，则本次铁索取消。

### 3. 铁索伤害类型（已冻结）

铁索反馈不继承兵刃 / 谋略类型，而是独立的：

```text
TRUE_FEEDBACK / 真实伤害反馈
```

原始伤害若已发生暴击，暴击结果已经包含在传播基数中；铁索反馈自身**不再次暴击**。

### 4. 铁索 Pipeline 边界（已冻结）

铁索反馈：

```text
不可规避
不可抵御
不吃传播目标自身伤害增减
不可分担
不再次暴击
不触发急救
不触发反击
不再次触发铁索
不触发倒戈
不触发攻心
不触发刚烈不屈等受击响应
```

因此铁索事实链为：

```text
TriggerNodeResolvedDamage
→ × CurrentChainRatio
→ TRUE_FEEDBACK
→ restricted direct troop-loss settlement
→ no Evasion / Barrier / target modifier / Share
→ no hit-response callback chain
```

### 5. 可触发铁索的伤害事件（已冻结）

```text
普通攻击伤害 → ALLOWED
战法伤害 → ALLOWED
持续性伤害 → ALLOWED
群攻伤害 → ALLOWED
反击伤害 → ALLOWED
```

明确阻断：

```text
Chain TRUE_FEEDBACK → Chain = BLOCKED
Share passive numeric settlement → Chain = BLOCKED
```

铁索触发粒度为 `PER DAMAGE INSTANCE`。多段伤害每一段都独立触发。

### 6. 铁索时序（已冻结）

默认：

```text
Damage Instance
→ damage settlement
→ source alive/state recheck
→ Chain INLINE
→ continue
```

普通多段伤害、反击伤害、群攻副目标伤害均在本段伤害后立即 Inline Chain。

唯一已确认特殊规则：普通攻击主目标若本次攻击存在群攻，则主目标 Chain 延迟到所有群攻及群攻副目标 Inline Chain 完成后执行。

```text
Main normal-attack damage
→ defer main-target Chain
→ Cleave target 1 → Inline Chain
→ Cleave target 2 → Inline Chain
→ Cleave complete
→ execute main-target Deferred Chain
```

### 7. Deferred Chain（已冻结）

Deferred Chain 触发时保存：

```text
triggerDamage
```

真正执行时重新检查并读取：

```text
source alive
current activeChainEffect exists
current owner
current ratio
current effect metadata
```

源节点死亡或铁索已失效 / 被净化：直接 Cancel。

若铁索在等待期间被新来源覆盖，则使用**新状态 owner / ratio**，但伤害基数仍使用原先保存的 `triggerDamage`。

### 8. 传播目标、顺序与 JIT（已冻结）

传播只面向：

```text
同阵营
+ 当前存活
+ 当前铁索有效
+ 非传播源自身
```

每个合法目标都独立获得完整比例，不做均分。

固定结算顺序：

```text
槽位 0（主将）
→ 槽位 1（副将 1）
→ 槽位 2（副将 2）
```

轮到每个目标时执行 JIT revalidation。某个传播目标死亡只结束该目标结算，不中止其余目标。

### 9. owner / ratio / 击杀归属（已冻结）

传播使用**触发节点自身当前 activeChainEffect**：

```text
ChainRatio = triggerNode.activeChainEffect.ratio
ChainDamageOwner = triggerNode.activeChainEffect.owner
ChainKillOwner = triggerNode.activeChainEffect.owner
```

接收目标自身铁索的 owner / ratio 不参与本次收到的反馈计算。

### 10. 多来源覆盖与状态生命周期（已冻结）

同一目标铁索为单实例状态：

```text
同一来源再次施加 → 刷新 / 覆盖，重置 2 回合
不同来源再次施加 → 后发覆盖先发，owner / ratio / 参数改为后发者，重置 2 回合
```

每次受伤仍只触发 1 次铁索，不因多来源堆叠而多次传播。

施加者死亡不会清除目标身上的铁索；状态继续倒计时、正常传播，伤害与击杀仍归原施加者。但施加者已死亡时，其本人应获得的后续治疗等收益跳过。

铁索持续时间在目标自身 `[单位]开始行动` 时扣减。`1 → 0` 时先到期移除，再结算灼烧 / 中毒 / 溃逃等 ACTION_START 持续伤害。震慑不会跳过铁索倒计时。

铁索可被净化 / 驱散负面立即移除；净化后重新施加视为全新实例。

### 11. 兵力截断与统计（已冻结）

```text
AppliedTroopLoss = min(ChainCalculatedDamage, CurrentTroops)
```

伤害统计按实际兵力损失计入 Chain owner；若反馈击杀目标，击杀也归 Chain owner。

---

## 三、 分担（Share）作为被动数值结算的边界

群攻可以触发分担，但分担者被扣除的分担兵力已经确认属于 **被动数值结算**，不是新的完整受击事件。

因此：

```text
Share Damage → FirstAid = BLOCKED
Share Damage → Counter = BLOCKED
Share Damage → 刚烈不屈等受击响应 = BLOCKED
Share Damage → Share = BLOCKED
Share Damage → Chain = BLOCKED
```

---

## 四、 历史致死过量与分担观察 (HR-02)

旧版提取器曾排查主目标致死时的分担战报样本，并观察到致死情况下未发生分担转嫁。该问题仍属于 Share / Death 专题，当前**不从 Cleave / Chain 冻结记录外推新的 Share 致死规则**。

---

## 五、 Stage 8 / Stage 9 架构含义

群攻与铁索虽然都属于“由已有伤害结果派生出的后续数值”，但许可矩阵明显不同：

```text
Cleave
→ fixed derived damage
→ Evasion / Barrier
→ Share
→ Troop Loss
→ selected callbacks

Chain
→ resolved trigger damage × current ChainRatio
→ TRUE_FEEDBACK
→ restricted direct troop-loss settlement
→ no Evasion / Barrier / Modifier / Share / hit callbacks
```

Stage 9 因此不能只有一个“所有 Derived Damage 共用的统一重入 Pipeline”。运行时至少需要表达：

```text
DerivedDamageKind / provenance
+ permission matrix
+ timing policy (INLINE / DEFERRED)
+ attribution owner
```

具体接口在 Stage 9 设计阶段评估；**当前不构成 Stage 8 Formal Reopen**。

---

## 六、 当前冻结状态

```text
CLEAVE CORE MECHANICS FROZEN
CHAIN CORE MECHANICS FROZEN
```

群攻与铁索的核心伤害基数、Pipeline、防护边界、递归、触发、时序与状态生命周期已从待研究列表移除。
