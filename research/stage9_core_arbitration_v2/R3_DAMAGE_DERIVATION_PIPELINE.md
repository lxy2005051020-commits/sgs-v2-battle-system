# R3 群攻与铁索连环伤害基数与 Pipeline 研究报告 (v2 - Cleave Frozen Sync)

> **研究基线 Commit**: `de80a4ec30fb3bf50220a719011478116bd34e5b` (main)  
> **群攻机制同步记录**: `STAGE9_CLEAVE_MECHANICS_FREEZE_RECORD.md`  
> **数据文件**: `evidence/r3_cleave_damage_data.json`, `evidence/r4_chain_damage_data.json`, `evidence/r6_death_near_fendan.json`  
> **核心任务**: 控制变量切片厘清派生伤害基数，规范管线重入模型（HR-01），厘清致死分担观察事实（HR-02）。

---

## 一、 群攻（Cleave）真实伤害机制与最终裁决

### 1. 历史全库统计
在 1,303 份战报中提取出 **2,258 个包含 2 个副目标的群攻事件**：
- **副目标承受完全相同伤害**: **1,938 个 (85.8%)**
- **副目标承受不同伤害**: **320 个 (14.2%)**

旧版研究曾将部分差异解释为“副目标自身增减伤 Modifier 再入”。该解释已经被后续逐项机制确认推翻，**不得继续作为群攻实现依据**。

### 2. 群攻伤害基数（已冻结）
群攻以触发群攻的主攻击 **最终结算伤害** 为派生基数：

$$D_{\text{cleave}} = D_{\text{main-final}} \times \text{CleaveRatio}$$

明确结论：
1. 副目标 **不重新执行基础攻防伤害公式**；
2. 群攻使用主攻击最终结算出的伤害值进行比例派生；
3. 群攻派生伤害继承原攻击 `DamageType`。

### 3. 群攻 Pipeline 重入边界（已冻结）
已经逐项确认：

- 群攻 **可以被规避（Evasion）**；
- 群攻 **可以被抵御（Barrier）**；
- 抵御成功后该次群攻伤害归零，并 **消耗 1 次抵御次数**；
- 群攻 **不重新受到副目标自身伤害增减效果影响**；
- 群攻 **可以被分担（Share）**；
- 群攻实际造成伤害后 **可以触发急救（FirstAid）**；
- 群攻 **不能触发反击（Counter）**；
- 群攻 **不能再次触发群攻（Cleave→Cleave）**；
- 兵刃型群攻可按规则触发倒戈；谋略型群攻可按规则触发攻心。

因此当前群攻机制事实链为：

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

而不是：

```text
CleaveDerivedDamage
→ Base Formula Again
→ Target Damage Increase/Reduction Again
```

### 4. 群攻后续响应许可（已冻结）

```text
Cleave → Share = ALLOWED
Cleave → FirstAid = ALLOWED
Cleave → Counter = BLOCKED
Cleave → Cleave = BLOCKED
```

群攻属于派生伤害：允许进入部分防护、分担与伤后恢复层，但 **不具备再次传播攻击型 Reaction 的资格**。

### 5. DamageType 与倒戈 / 攻心
群攻继承触发它的主攻击伤害类型：

```text
Weapon-type source attack
→ Weapon-type Cleave
→ 可按规则触发倒戈

Strategy-type converted normal attack
→ Strategy-type Cleave
→ 可按规则触发攻心
```

因此运行时群攻派生对象至少需要保留：

```text
damage_type
source
source_action
cleave_ratio
derived_damage
```

---

## 二、 铁索连环（Iron Chain）真实伤害基数与 Pipeline

### 1. 全库多目标连环反馈统计
在 1,522 份战报中提取出 **11,104 个多副目标铁索连环反馈事件**：
- **副目标承受完全相同伤害**: **10,817 个 (97.4%)**
- **副目标承受不同伤害**: **287 个 (2.6%)**（历史分析主要归因为残血致死截断或多段技能分段反馈）。

### 2. 当前研究结论
铁索连环反馈数值基数表现为：

$$D_{\text{chain-feedback-base}} = D_{\text{trigger-damage}} \times \text{ChainRatio}$$

副目标智力与防御不重新参与基础攻防差值计算。

> 注意：本轮只冻结了 **Cleave** 的完整 Pipeline 边界。铁索连环是否与群攻完全共享相同的 Evasion / Barrier / Modifier / Share / Callback 许可矩阵，仍应由铁索专题单独确认，禁止因群攻结论而自动类推。

---

## 三、 分担（Share）作为被动数值结算的边界

群攻可以触发分担，但分担者被扣除的分担兵力已经确认属于 **被动数值结算**，不是新的完整受击事件。

因此：

```text
Share Damage → FirstAid = BLOCKED
Share Damage → Counter = BLOCKED
Share Damage → 刚烈不屈等受击响应 = BLOCKED
Share Damage → Share = BLOCKED
```

这意味着分担支路在扣除分担者兵力后终止，不再递归打开新的受击 Reaction 链。

---

## 四、 历史致死过量与分担观察 (HR-02)

旧版提取器曾排查 154 例主目标在受击瞬间兵力扣至 0 的分担战报样本（`evidence/r6_death_near_fendan.json`）：

### 1. 观察事实
在这些样本中，当主目标受到致死伤害阵亡时，未观察到分担转嫁日志。

### 2. 当前处理
由于 Stage 9 提取器仍在做最终语义正确性审计，这一历史统计 **不得自动提升为新的 Frozen 规则**。致死场景下 Share 的精确 atomic boundary，应继续归入 Share / Death 专题，而不是从群攻冻结记录中外推。

---

## 五、 Stage 8 / Stage 9 架构含义

群攻不是新的普通攻击，也不应重新运行完整的 Stage 8 Base Formula + Modifier Pipeline。

Stage 9 需要表达：

```text
已有 MainAttackFinalDamage
→ 构造带 provenance / damage_type 的 Derived Damage
→ 执行允许的 Evasion / Barrier
→ Share
→ Troop mutation
→ 允许的 post-damage recovery callback
→ 禁止 Counter / Cleave 递归传播
```

这支持在 Stage 9 设计阶段评估一个明确的 **Derived Damage extension/interface**。该结论 **不构成 Stage 8 Formal Reopen**。

---

## 六、 群攻冻结状态

群攻以下核心机制不再列为待研究项：

- 主伤害基数；
- 是否重跑副目标基础公式；
- 规避；
- 抵御与次数消耗；
- 副目标伤害增减 Modifier；
- 分担；
- 急救；
- 反击；
- 群攻自递归；
- DamageType；
- 倒戈 / 攻心条件；
- 群攻触发分担后的 Share Damage 响应边界。

**状态：`CLEAVE CORE MECHANICS FROZEN`。**
