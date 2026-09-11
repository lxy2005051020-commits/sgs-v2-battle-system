# R3 群攻与铁索连环伤害基数与 Pipeline 研究报告 (v2 - Repaired)

> **研究基线 Commit**: `de80a4ec30fb3bf50220a719011478116bd34e5b` (main)  
> **数据文件**: `evidence/r3_cleave_damage_data.json`, `evidence/r4_chain_damage_data.json`, `evidence/r6_death_near_fendan.json`  
> **核心任务**: 控制变量切片厘清派生伤害基数，规范管线重入模型（HR-01），厘清致死分担观察事实（HR-02）。

---

## 一、 群攻（Cleave）真实伤害机制与矛盾裁决

### 1. 全库多副目标群攻事件统计
在 1,303 份战报中提取出 **2,258 个包含 2 个副目标的群攻事件**：
- **副目标承受完全相同伤害**: **1,938 个 (85.8%)**
- **副目标承受不同伤害**: **320 个 (14.2%)**

### 2. 差异案例（320 例）的逐帧切片归因
对 320 个差异样本进行排查，**无一例参与副目标防御公式计算**：
1. **残血兵力截断 (HP Clipping)**: 副目标当前剩余兵力少于应受群攻伤害，直接扣至 0 阵亡。
2. **副目标带有分担 (Damage Share)**: 副目标触发分担减免（如严阵以待），部分伤害被队友分流。
3. **主行动期间攻击者增益变动**: 攻击者在击中前序目标后触发特定增益（如攻其不备）。
4. **副目标自身具有增减伤差异**: 副目标身上的受到伤害降低/增加状态。

### 3. 管线模型定论 (HR-01 / Grade B — STRONG)
- **事实定性**: 战报表现**最符合 fixed derived base + target-side modifier re-entry 模型**。
  $$D_{\text{cleave\_base}} = D_{\text{main\_final}} \times \text{CleaveRatio}$$
- **重入规则**: 派生基数直接作为输入，跳过副目标基础攻防公式（Base Pipeline），但进入副目标侧的命中判定（规避/抵御）与修饰管线（Modifier Pipeline）。
- **工程实现说明**: 模拟器可在 Stage 9 侧通过 `DerivedDamagePipelineAdapter` 承接此派生输入，无需断言“官方底层也是此种 Adapter 架构”。

---

## 二、 铁索连环（Iron Chain）真实伤害基数与 Pipeline

### 1. 全库多目标连环反馈统计
在 1,522 份战报中提取出 **11,104 个多副目标铁索连环反馈事件**：
- **副目标承受完全相同伤害**: **10,817 个 (97.4%)**
- **副目标承受不同伤害**: **287 个 (2.6%)**（全部为残血致死截断或多段技能分段反馈）。

### 2. 管线模型定论 (HR-01 / Grade B — STRONG)
- 铁索连环反馈数值基数等于：
  $$D_{\text{chain\_feedback\_base}} = D_{\text{trigger\_damage}} \times \text{ChainRatio}$$
- **副目标智力与防御不重新参与基础攻防差值计算**。
- **副目标独立应用自身的抵御（Barrier）、规避（Evasion）与全局受伤害降低 Buff**。

---

## 三、 致死过量与分担表现 (HR-02 / Grade B — STRONG)

排查 154 例主目标在受击瞬间兵力扣至 0 的分担战报样本（`evidence/r6_death_near_fendan.json`，见切片 `raw_slices/EM-19_战报_1008108_pid1003335_ev130_150.json`）：

### 1. 观察事实 (OBSERVED FACT)
在全部 154 例样本中，当主目标受到致死伤害阵亡时，战报中**未观察到分担转嫁日志（分担者兵力扣除为 0）**。

### 2. 机制推论 (INFERRED MECHANISM)
此现象最符合“主目标致死短路了正在处于队列中的分担结算”这一模型。
分担仅在主目标存活且伤害进入正常承受阶段时生效；致死攻击使得动作流在主目标处直接宣告死亡并阻断分担动作。
