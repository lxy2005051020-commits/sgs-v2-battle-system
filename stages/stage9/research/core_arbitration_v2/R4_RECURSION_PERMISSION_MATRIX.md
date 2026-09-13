# R4 跨机制递归许可矩阵与有效分母审计报告 (v2 - Cleave/Chain/Share Sync)

> **研究基线 Commit**: `de80a4ec30fb3bf50220a719011478116bd34e5b` (main)  
> **群攻机制冻结记录**: `STAGE9_CLEAVE_MECHANICS_FREEZE_RECORD.md`  
> **铁索机制冻结记录**: `STAGE9_CHAIN_MECHANICS_FREEZE_RECORD.md`  
> **核心任务**: 区分历史统计证据与后续逐项机制确认，并维护当前唯一递归 / 跨机制许可矩阵。

---

## 一、 自递归当前状态

历史审计原则仍成立：仅凭“战报未观察到”不能自动写成 BLOCKED。  
但后续通过独立机制确认已经直接确定的项目，可以升级为正式 Frozen 规则。

| 自递归对 | 当前状态 | 当前说明 |
|---|---|---|
| **Counter → Counter** | `PENDING FINAL EXTRACTOR AUDIT` | 历史统计方向支持 BLOCKED，但仍受最终提取器语义审计约束。 |
| **Cleave → Cleave** | **`BLOCKED — FROZEN`** | 群攻派生伤害不会再次触发新的群攻。 |
| **Chain → Chain** | **`BLOCKED — FROZEN`** | 铁索真实反馈不会再次触发铁索。该结论现已由直接机制确认，不再依赖旧提取器分母。 |
| **Share Damage → Share** | **`BLOCKED — FROZEN`** | 分担扣兵属于被动数值结算，不重新触发分担。 |
| **Combo2 → Combo3** | `BLOCKED` | 当前研究强支持连击仅额外产生第二次普通攻击。 |

---

## 二、 群攻（Cleave）许可矩阵

```text
Cleave → Share = ALLOWED
Cleave → FirstAid = ALLOWED
Cleave → Chain = ALLOWED
Cleave → Counter = BLOCKED
Cleave → Cleave = BLOCKED
```

群攻派生伤害可以进入分担、急救，并且群攻副目标受到合法伤害后可以立即 Inline 触发其自己的 Chain。

群攻不具备 Counter / Cleave 攻击型递归传播资格。

---

## 三、 铁索（Chain）许可矩阵

### 3.1 可以触发 Chain 的来源

```text
Normal Attack Damage → Chain = ALLOWED
Skill Damage → Chain = ALLOWED
Periodic Damage → Chain = ALLOWED
Cleave Damage → Chain = ALLOWED
Counter Damage → Chain = ALLOWED
```

只要是合法伤害结算、传播源节点在结算后仍存活且当前铁索有效，即可触发。

### 3.2 不能触发 Chain 的来源

```text
Chain TRUE_FEEDBACK → Chain = BLOCKED
Share Passive Numeric Settlement → Chain = BLOCKED
```

### 3.3 Chain 反馈不能承接的机制

```text
Chain → Evasion = BLOCKED
Chain → Barrier = BLOCKED
Chain → Target-side Damage Modifier = BLOCKED
Chain → Share = BLOCKED
Chain → Crit = BLOCKED
Chain → FirstAid = BLOCKED
Chain → Counter = BLOCKED
Chain → Chain = BLOCKED
Chain → Lifesteal = BLOCKED
Chain → StrategyRecovery = BLOCKED
Chain → 刚烈不屈等受击响应 = BLOCKED
```

铁索真实反馈属于受限派生数值结算，不重新打开完整 Hit / Damage Reaction 链。

---

## 四、 Share Damage 许可矩阵

分担者被扣除的兵力属于：

```text
Passive Numeric Settlement
```

不是：

```text
New Hit Event
New Damage Reaction Source
```

因此：

```text
Share Damage → Share = BLOCKED
Share Damage → FirstAid = BLOCKED
Share Damage → Counter = BLOCKED
Share Damage → Chain = BLOCKED
Share Damage → 刚烈不屈等受击响应 = BLOCKED
```

---

## 五、 当前跨机制总矩阵

| 触发源 | 承接机制 | 当前判定 | 说明 |
|---|---|---:|---|
| **Cleave** | Share | **ALLOWED — FROZEN** | 群攻可被分担。 |
| **Cleave** | FirstAid | **ALLOWED — FROZEN** | 群攻实际承伤可触发急救。 |
| **Cleave** | Chain | **ALLOWED — FROZEN** | 群攻副目标每个独立伤害段可触发自己的 Chain。 |
| **Cleave** | Counter | **BLOCKED — FROZEN** | 群攻副目标不会因群攻触发反击。 |
| **Cleave** | Cleave | **BLOCKED — FROZEN** | 群攻不递归群攻。 |
| **Counter** | Chain | **ALLOWED — FROZEN** | 反击伤害后立即 Inline Chain。 |
| **Chain** | Share | **BLOCKED — FROZEN** | TRUE_FEEDBACK 不可分担。 |
| **Chain** | FirstAid | **BLOCKED — FROZEN** | TRUE_FEEDBACK 不触发急救。 |
| **Chain** | Counter | **BLOCKED — FROZEN** | TRUE_FEEDBACK 不触发反击。 |
| **Chain** | Chain | **BLOCKED — FROZEN** | TRUE_FEEDBACK 不递归铁索。 |
| **Share Damage** | Share | **BLOCKED — FROZEN** | 被动数值结算。 |
| **Share Damage** | FirstAid | **BLOCKED — FROZEN** | 被动数值结算。 |
| **Share Damage** | Counter | **BLOCKED — FROZEN** | 被动数值结算。 |
| **Share Damage** | Chain | **BLOCKED — FROZEN** | 被动数值结算不属于合法 Chain 触发伤害。 |

---

## 六、 递归与时序不能只靠 ReactionDepth

当前至少需要区分：

```text
1. Full Attack / Full Hit
2. Cleave Derived Damage
3. Chain TRUE_FEEDBACK
4. Share Passive Numeric Settlement
```

并通过：

```text
provenance / damage kind
+ permission matrix
+ timing policy
```

共同裁决。

单独使用 `ReactionDepth <= 1` 无法准确表达以下已经确认的合法链：

```text
Cleave → Chain = ALLOWED
Counter → Chain = ALLOWED
```

同时也无法准确表达：

```text
Chain → Chain = BLOCKED
Share → Chain = BLOCKED
```

---

## 七、 铁索特殊时序约束

默认：

```text
Damage Instance → Chain INLINE
```

普通攻击主目标存在群攻时：

```text
Main target damage
→ defer main-target Chain
→ resolve all Cleave targets and their Inline Chains
→ execute main-target Deferred Chain
```

Deferred Chain 执行时重新检查传播源存活和当前铁索状态，并动态读取当前 owner / ratio；触发伤害基数仍使用产生该 Deferred Chain 时保存的 damage value。

---

## 八、 当前冻结状态

已经从待研究项中移除：

- `Cleave → Cleave / Counter / Share / FirstAid / Chain`；
- `Chain → Chain / Share / FirstAid / Counter / Crit / Lifesteal / StrategyRecovery / 受击响应`；
- `Counter → Chain`；
- `Share Damage → Share / FirstAid / Counter / Chain / 受击响应`。

仍未冻结的递归重点主要剩余：

```text
Counter → Counter（最终提取器语义复核）
```
