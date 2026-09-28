# RF-P06 Cleave Damage Layer and Recovery Basis Research Report

## 1. Executive Summary

本报告为 Stage 9 Contract Closure 中 **`RF-P06 — CLEAVE_DAMAGE_LAYER_AND_RECOVERY_BASIS`** 的专项实证研究成果。

核心研究对象为：
- **`CLVS9-B01`**：`MainAttackFinalDamage` 精确伤害层映射（`Dtotal` vs `Dtarget` vs `ActualTargetTroopLoss` vs `CreditedDamage`）及群攻取整规则。

- **`CLVS9-M01`**：群攻与分担（Share）/分摊（Distribution）交互后，倒戈（Lifesteal）/攻心（StrategyRecovery）恢复基数冻结。


### 核心实证结论

1. **`MainAttackFinalDamage` 唯一映射**：
   - 当主攻击受到分担（Share）时，群攻派生基数严格采用原目标的实际分担后结算伤害 **`Dtarget`**，绝对排除未经分担的理论总伤害 **`Dtotal`**（`Dtotal` 产生超 20% 偏差，被 100% 反驳并淘汰）。
   - 当主攻击发生残兵过量击杀（Overkill，即 `target.currentTroops < Dtarget`）时，群攻派生基数严格截断为原目标的实际扣兵量 **`ActualTargetTroopLoss`**（`min(Dtarget, target.currentTroops)`），绝不使用超额的未截断理论值。
   - 因此，**`MainAttackFinalDamage = ActualTargetTroopLoss`**（在非 Overkill 场景下恒等于 `Dtarget`）。

2. **群攻乘法取整规则（Integerization Rule）**：
   - 实证证明群攻计算公式为：`CleaveDerivedDamage = floor(ActualTargetTroopLoss * CleaveRatio)`。
   - 取整算法采用 **`FLOOR`**，与 CHAIN 取整规则保持一致，彻底排除 `CEIL` 与 `ROUND_HALF_UP`。

3. **恢复基数（Recovery Basis, `CLVS9-M01`）**：
   - 群攻命中每一名副目标时，均独立发出合法 `DamageEvent`，其恢复判定为 **`PER-SECONDARY DAMAGE EVENT`**。
   - 当副目标受到分担（Share）时，攻击方恢复基数仅读取该副目标的实际结算伤害 `Dtarget`，分担者的被动扣血 `Dsharer` 不计入恢复基数（继承 Share P0 规范）。
   - 当副目标受到分摊（Distribution）时，群攻模块仅向世界提供标准 `DamageEvent`（`Dtarget`），分摊承担者的扣兵是否被计入倒戈/攻心交由 `690094`/`690095` 状态合同统一仲裁，群攻不自行决定。


## 2. Candidate Elimination Matrix


| Candidate Base Layer | Definition | Share Partition Prediction vs Reality | Overkill Prediction vs Reality | Contradictions | Verdict |

|---|---|---|---|---:|---|

| **`Dtotal`** | 伤害分担/分摊前的原始理论普通攻击伤害 | 预测值显著高于实测（如 369 vs 314） | 无法解释残兵时溅射变小 | 100% 冲突 | **REJECTED** |

| **`Dtarget`** | 经 Share/Distribution 分割后赋予主目标的理论分配量 | 理论预测与战报完全一致 | 在非 Overkill 场景下 100% 吻合；Overkill 场景需进一步截断 | 0 | **SUPPORTED (NORMAL)** |

| **`ActualTargetTroopLoss`** | 主目标兵力截断后的实际扣除兵力 (`min(Dtarget, currentTroops)`) | 100% 完全吻合 | 100% 完全吻合（如 55 兵残血派生 29 伤害） | 0 | **SUPPORTED (DEFINITIVE)** |

| **`CreditedDamage`** | 战后统计归因伤害层 | 数值与 ActualTargetTroopLoss 等价，但属于战后统计属性并非运行时事件层 | 不适用运行时结算 | 0 | **OBSERVATIONALLY_EQUIVALENT (STATISTICAL)** |


## 3. Empirical Data Overview


- 总扫描战报数量: **33728**

- 提取有效群攻行为总数: **4276**

- 主攻击受分担（SHARE）样本数: **109**

- 主攻击受分摊（DISTRIBUTION）样本数: **0**

- 主目标过量击杀（OVERKILL）样本数: **178**

- 基线普通对照（CONTROL）样本数: **3989**

- 群攻派生倒戈/攻心恢复样本数: **193**


## 4. Key Representative Battle Cases


### 4.1 分担（SHARE）关键区分样本：`Dtotal` vs `Dtarget`

以 `战报_2235624_pid2306204.json` 为例：

- 攻击方：马超，战法：【槊血纵横】（群攻系数 54%）

- 主目标：郭汜，受【严阵以待】分担 15.00%

- 主目标战报损失兵力：`582`（`Dtarget = 582`）

- 分担者纪灵损失兵力：`103`（`Dsharer = 103`）

- 理论总伤害：`Dtotal = 582 + 103 = 685`

- 群攻溅射纪灵实测伤害：**`314`**

  - 若基数为 `Dtotal`：`685 × 54% = 369.9` -> 预测 `369`（与实测 **314** 严重冲突，淘汰！）

  - 若基数为 `Dtarget`：`floor(582 × 54%) = floor(314.28) = 314`（与实测 **314** 完全精准契合！）


### 4.2 残兵过量击杀（OVERKILL）关键区分样本：`Dtarget` vs `ActualTargetTroopLoss`

以 `战报_2235624_pid2306204.json` 事件 376-381 为例：

- 攻击方：马超，战法：【槊血纵横】（群攻系数 54%）

- 主目标：纪灵，受击前仅剩 **55** 兵力（`currentTroops = 55`）

- 正常普通攻击理论伤害预期：600~800

- 纪灵实际扣除兵力：`ActualTargetTroopLoss = 55`，兵力归 0 阵亡

- 群攻溅射副目标李傕实测伤害：**`29`**

  - 若基数为未截断的理论伤害：`600 × 54% = 324`（完全荒谬）

  - 若基数为实际兵力损失：`floor(55 × 54%) = floor(29.7) = 29`（与实测 **29** 精准吻合！）

