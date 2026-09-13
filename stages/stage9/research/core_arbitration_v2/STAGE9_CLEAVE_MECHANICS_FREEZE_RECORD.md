# Stage 9 群攻（Cleave）机制冻结记录

> **项目**: 三国志战略版战斗模拟器 V2  
> **状态**: `CORE MECHANISM FROZEN`  
> **用途**: 记录 Stage 9 群攻机制逐项确认后的单一事实基线，后续实现与审计不得继续沿用与本文件冲突的旧推论。  
> **说明**: 本文件记录的是当前项目已经人工确认的游戏机制规则；它不等同于“官方底层实现结构”，也不用于反推官方内部调用栈。

---

## 1. 群攻伤害基数与伤害层映射（RF-P06 冻结 / CLVS9-B01 关闭）

群攻以触发该群攻的主攻击 **实际扣除兵力（ActualTargetTroopLoss）** 为派生基数，再乘群攻比例并向下取整（FLOOR）：

```text
ActualTargetTroopLoss = min(Dtarget, mainTarget.currentTroops)
CleaveDerivedCalculatedDamage = floor(ActualTargetTroopLoss × CleaveRatio)
```

即：

```text
MainAttackFinalDamage ≡ ActualTargetTroopLoss
```

### 1.1 伤害分层与候选排除

根据 RF-P06 专项实证研究（33,728 场战报全量扫描，109 场分担样本，178 场过量击杀样本）：

1. **排除 `Dtotal`**：当主攻击受到伤害分担（DAMAGE_SHARE）或分摊（DISTRIBUTION）时，群攻派生基数严格采用原目标分担后的理论分配量 `Dtarget`，绝不采用未经分割的理论总伤害 `Dtotal`（`Dtotal` 预测值与实战存在重大偏差，已被 100% 证伪淘汰）。
2. **排除未截断的理论分配量（Overkill 裁决）**：当主目标剩余兵力不足（`Dtarget > mainTarget.currentTroops`，如 1000 伤害打 100 残兵）时，群攻派生基数严格截断为主目标的实际扣除兵力（100），绝不基于未截断的理论分配量（1000）派生伤害。
3. **排除 `CreditedDamage` 运行时概念**：`CreditedDamage` 属于战后统计归因层，运行时派生伤害直接锚定于提交阶段的实际扣兵层 `ActualTargetTroopLoss`。

### 1.2 取整规则（Integerization Policy）

群攻乘法取整采用 **`FLOOR`**：

```text
CleaveDerivedCalculatedDamage = floor(ActualTargetTroopLoss × CleaveRatio)
```

与 CHAIN 机制保持一致，彻底排除 `ROUND_HALF_UP`、`ROUND_HALF_EVEN` 及 `CEIL`。

群攻副目标 **不重新执行基础攻防伤害公式**。

---

## 2. 群攻派生伤害的防护与修正边界

已经确认：

1. **可以被规避（Evasion）**；
2. **可以被抵御（Barrier）**；
3. 抵御成功后该次群攻伤害归零，并正常 **消耗 1 次抵御次数**；
4. **不重新受到副目标自身伤害增减效果影响**；
5. **可以被分担（Share）**。

因此群攻不是“直接无条件扣兵”，但也不是一次完整重新进入普通伤害 Modifier Pipeline 的新攻击。

当前群攻派生链按机制事实表达为：

```text
MainAttackFinalDamage
→ CleaveRatio
→ CleaveDerivedDamage
→ Evasion
→ Barrier
→ Share（若存在）
→ Troop Loss
→ Allowed post-damage recovery callbacks
```

明确禁止把它实现为：

```text
CleaveDerivedDamage
→ Base Damage Formula Again
→ Target Damage Increase/Reduction Again
```

---

## 3. 后续响应许可矩阵

| 后续机制 | 群攻伤害是否可触发 | 冻结结论 |
|---|---:|---|
| 急救 / FirstAid | 是 | `ALLOWED` |
| 分担 / Share | 是 | `ALLOWED` |
| 反击 / Counter | 否 | `BLOCKED` |
| 再次群攻 / Cleave→Cleave | 否 | `BLOCKED` |
| 倒戈 | 条件允许 | 兵刃型群攻伤害可触发 |
| 攻心 | 条件允许 | 谋略型群攻伤害可触发 |

由此可得：

```text
Cleave → Counter = BLOCKED
Cleave → Cleave = BLOCKED
Cleave → Share = ALLOWED
Cleave → FirstAid = ALLOWED
```

群攻属于“派生伤害”，能够进入部分防护、分担与伤后恢复流程，但 **不具备再次传播攻击型 Reaction 的资格**。

### 3.1 恢复触发模型与恢复基数（RF-P06 冻结 / CLVS9-M01 关闭）

1. **触发粒度**：群攻对多名副目标造成伤害时，每命中一个副目标均独立产生一次 `DamageEvent`。倒戈/攻心的判定与结算为 **`PER-SECONDARY DAMAGE EVENT`**，各副目标分别独立判定并恢复兵力，不合并为单笔总伤害恢复。
2. **分担（Share）恢复基数**：当群攻副目标具有分担状态时，攻击方倒戈/攻心恢复基数严格只读取该副目标的实际结算伤害 `Dtarget`，分担者承担的被动兵损 `Dsharer` 不计入恢复基数（继承 DAMAGE_SHARE P0 规则）。
3. **分摊（Distribution）恢复基数**：群攻副目标受到分摊时，群攻模块仅对外发射标准 `DamageEvent`（带有副目标 `Dtarget` 与物理归因）。分摊承担者的被动扣兵是否被计入倒戈/攻心，属于 `690094 LIFE_STEAL` / `690095 STRATEGY_LIFE_STEAL` 状态自身合同的仲裁边界，群攻模块不越权私自包含承担者兵损。

---

## 4. DamageType 继承

群攻派生伤害继承触发它的主攻击伤害类型。

```text
Weapon-type source attack
→ Weapon-type Cleave
→ 可按规则触发倒戈

Strategy-type converted normal attack
→ Strategy-type Cleave
→ 可按规则触发攻心
```

因此群攻运行时至少需要保留：

```text
damage_type
source
source_action
cleave_ratio
derived_damage
```

不能只保存一个裸伤害数值。

---

## 5. 与分担（Share）的边界

群攻本身可以触发分担，但 **分担者被扣除的分担兵力属于被动数值结算**，不是新的完整受击事件。

已经确认：

```text
Share Damage → FirstAid = BLOCKED
Share Damage → Counter = BLOCKED
Share Damage → 刚烈不屈等受击响应 = BLOCKED
Share Damage → Share = BLOCKED
```

因此不要把群攻后的分担支路继续递归成新的受击 Reaction 链。

---

## 6. Stage 9 / Stage 8 架构含义

群攻的最小语义不是“重新发起一次普通攻击”，而是：

```text
已有主攻击最终结算伤害
→ 生成带 DamageType / Source Provenance 的派生伤害
→ 重新进行允许的防护层（规避、抵御）
→ 允许分担
→ 扣兵
→ 允许特定伤后恢复类回调
→ 禁止 Counter / Cleave 递归传播
```

这进一步说明 Stage 9 需要一个 **Derived Damage** 入口，而不是把群攻伪装成新的普通攻击。

是否需要对 Stage 8 增加正式扩展接口，应在 Stage 9 设计阶段单独评估；本机制冻结记录 **不构成 Stage 8 Formal Reopen**。

---

## 7. 冻结声明

以下群攻核心问题不再列为 Stage 9 待研究项：

- 群攻伤害基数与伤害层映射（`MainAttackFinalDamage ≡ ActualTargetTroopLoss`，`CLVS9-B01 = CLOSED`）；
- 群攻乘法取整规则（`FLOOR`，`CLVS9-B01 = CLOSED`）；
- 群攻派生倒戈/攻心恢复基数与分担/分摊边界（`PER-SECONDARY DAMAGE EVENT`，`CLVS9-M01 = CLOSED`）；
- 是否重新跑副目标基础伤害公式（否，`BLOCKED`）；
- 是否可规避（是，`ALLOWED`）；
- 是否可抵御及抵御次数消耗（是，`ALLOWED`，消耗 1 次抵御）；
- 是否重新吃副目标自身伤害增减修正（否，`BLOCKED`）；
- 是否可分担（是，`ALLOWED`）；
- 是否触发急救（是，`ALLOWED`）；
- 是否触发反击（否，`BLOCKED`）；
- 是否递归触发群攻（否，`BLOCKED`）；
- 倒戈 / 攻心与 DamageType 的关系（继承 DamageType 并在允许条件下触发）；
- 群攻触发分担后，Share Damage 是否继续触发受击响应（被动扣损，不触发受击 Reaction）。

以下问题明确保持 OPEN，留待后续专用 Package 解决：
- `CLVS9-B02`：690084 完整状态生命周期、重施加、多来源共存与倍率绑定（属于 RF-P07）；
- `CLVS9-B03`：副目标候选池、数量、稳定排序队列与 JIT 存活重校验（属于 RF-P07）；
- `CLVS9-B04`：主目标死亡、攻击者死亡、副将/主将阵亡终战边界（属于 RF-P04）。

**最终状态：`CLEAVE CORE MECHANICS FROZEN (RF-P06 RE-FROZEN)`。**  
（注：本文件不重命名为 FULL CONTRACT FROZEN，完整状态合同等待 RF-P07。）
