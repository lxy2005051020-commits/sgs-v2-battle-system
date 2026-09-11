# R4 跨机制递归许可矩阵与有效分母审计报告 (v2 - Cleave/Share Sync)

> **研究基线 Commit**: `de80a4ec30fb3bf50220a719011478116bd34e5b` (main)  
> **数据文件**: `evidence/r7_recursion_denominators.json`, `evidence/r7_recursion_matrix_data.json`, `evidence/raw_slices/EM-11_*`, `evidence/raw_slices/EM-22_*`  
> **群攻机制冻结记录**: `STAGE9_CLEAVE_MECHANICS_FREEZE_RECORD.md`  
> **核心任务**: 为递归禁止断言计算有效机会（Eligible Opportunities）分母，并同步纳入后续直接确认的群攻 / 分担机制边界。

---

## 一、 自递归机制的有效机会分母与定性

历史审计原则仍然成立：仅凭“战报未观察到”不能把机制写成 BLOCKED；若无有效分母，应标记 NOT OBSERVED。  
但当某项机制后来通过独立游戏机制确认被直接确定时，可以从“统计未观察”升级为“项目机制已确认”。这两类证据来源必须区分。

| 自递归对 (Self-Recursion) | 历史统计状态 | 当前状态 | 当前说明 |
| :--- | :--- | :--- | :--- |
| **Counter → Counter** | 有效机会分母存在，历史统计 0 触发 | **PENDING FINAL EXTRACTOR AUDIT** | 方向支持 BLOCKED，但最终冻结仍受状态生命周期提取器语义审计约束。 |
| **Cleave → Cleave** | 历史分母为 0，曾标记 NOT OBSERVED | **BLOCKED — FROZEN** | 已直接确认：群攻派生伤害不会再次触发新的群攻。不得再保留为“仅工程防御不变量”。 |
| **Chain → Chain** | 历史有效机会分母较大，0 触发 | **PENDING FINAL EXTRACTOR AUDIT** | 方向支持 BLOCKED，但最终冻结仍受 Chain 状态 / execution 语义审计约束。 |
| **Share Damage → Share** | 历史分母为 0，曾标记 NOT OBSERVED | **BLOCKED — FROZEN** | 已直接确认：分担兵力扣除属于被动数值结算，不会再次触发分担。 |
| **Combo2 → Combo3** | 全量连击样本中未观察第三击 | **BLOCKED** | 当前研究强支持连击仅额外产生第二次普通攻击，不递归出第三击。 |

---

## 二、 群攻 / 分担直接确认后的递归边界

### 1. Cleave 派生伤害

已经冻结：

```text
Cleave → Cleave = BLOCKED
Cleave → Counter = BLOCKED
Cleave → Share = ALLOWED
Cleave → FirstAid = ALLOWED
```

群攻属于派生伤害，可以进入规避、抵御、分担与允许的伤后恢复流程，但 **不具备再次传播攻击型 Reaction 的资格**。

### 2. Share Damage

分担者被扣除的兵力属于：

```text
Passive Numeric Settlement
```

而不是：

```text
New Hit Event
New Damage Reaction Source
```

因此已经冻结：

```text
Share Damage → Share = BLOCKED
Share Damage → FirstAid = BLOCKED
Share Damage → Counter = BLOCKED
Share Damage → 刚烈不屈等受击响应 = BLOCKED
```

这条规则从机制层直接切断 Share 的递归响应链。

---

## 三、 跨机制派生矩阵

| 触发源 (Source) | 承接机制 (Target) | 当前判定 | 说明 |
| :--- | :--- | :---: | :--- |
| **Cleave (群攻)** | Share (分担) | **ALLOWED — FROZEN** | 群攻可以进入分担。 |
| **Cleave (群攻)** | FirstAid (急救) | **ALLOWED — FROZEN** | 群攻实际承伤可以触发急救。 |
| **Cleave (群攻)** | Counter (反击) | **BLOCKED — FROZEN** | 群攻副目标不会因群攻触发反击。 |
| **Cleave (群攻)** | Cleave (群攻) | **BLOCKED — FROZEN** | 群攻不会递归触发群攻。 |
| **Share Damage** | Share | **BLOCKED — FROZEN** | 被动数值结算，不再开启分担。 |
| **Share Damage** | FirstAid | **BLOCKED — FROZEN** | 被动数值结算，不产生受击急救响应。 |
| **Share Damage** | Counter | **BLOCKED — FROZEN** | 被动数值结算，不产生反击响应。 |
| **Counter (反击)** | FirstAid | ALLOWED（既有研究） | 被反击方受伤可触发急救。 |
| **Counter (反击)** | Chain | ALLOWED（既有研究） | 谋略反击可进入连环反馈。 |
| **Chain (连环)** | Share / FirstAid / Counter | **待独立复核** | 不允许从 Cleave 冻结矩阵自动类推 Chain。 |

---

## 四、 模拟器工程防御规范

当前至少需要明确区分三类运行时语义：

```text
1. Full Attack / Full Hit
2. Derived Damage（例如 Cleave）
3. Passive Numeric Settlement（例如 Share Damage）
```

其中：

```text
Derived Damage
→ 可以拥有部分防护 / 分担 / 恢复回调
→ 但可通过 provenance / recursion permission 禁止攻击型递归

Passive Numeric Settlement
→ 直接执行数值扣除
→ 不重新打开受击 Reaction 链
```

因此不建议仅靠一个笼统的 `ReactionDepth <= 1` 解决所有递归问题。更准确的做法是让来源类型与递归许可矩阵共同裁决。

---

## 五、 当前冻结状态

已经从待研究项中移除：

- `Cleave → Cleave`；
- `Cleave → Counter`；
- `Cleave → Share`；
- `Cleave → FirstAid`；
- `Share Damage → Share`；
- `Share Damage → FirstAid / Counter / 受击响应`。

Counter / Chain 自递归仍需等待提取器最后一轮语义正确性复核后再决定是否进入正式 FROZEN。
