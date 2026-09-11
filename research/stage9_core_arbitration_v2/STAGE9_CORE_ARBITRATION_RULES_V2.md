# Stage 9 核心底层裁决全景总规 (v2 - Repaired)

> **项目**: 三国志战略版战斗模拟器 V2  
> **研究基线 Commit**: `de80a4ec30fb3bf50220a719011478116bd34e5b` (main)  
> **数据基线**: 全盘扫描 32,660 份战报（逾 1,400 万条原始事件流）  
> **状态**: `REPAIRED — CLEAVE / CHAIN CORE MECHANICS FROZEN`  
> **群攻机制冻结记录**: `STAGE9_CLEAVE_MECHANICS_FREEZE_RECORD.md`  
> **铁索机制冻结记录**: `STAGE9_CHAIN_MECHANICS_FREEZE_RECORD.md`  
> **最高原则**: 
> 1. 反例优先、控制变量优先、直接证据优先；
> 2. 严禁将 NOT OBSERVED 写成 BLOCKED；
> 3. 严禁把工程设计表述为官方内部实证；
> 4. 严禁把统计模型兼容断言为官方机制证明；
> 5. 跨文档同一机制只能存在单一一致结论；
> 6. 后续逐项直接确认的 Frozen 机制结论若与旧统计推论冲突，以最新冻结记录为准。

---

## 核心裁决原则全览 (12 个问题域统一裁决)

### 1. 目标选择与重定向总顺序 (R2)
- **流水线**: 存活池 → 阵营过滤 → 混乱判定 (JIT 即时) → 嘲讽/锁定检查 (若未混乱) → 意图目标 → 援护拦截 → 受击承伤者。
- 混乱压制嘲讽、援护重定向、自援护等仍维持既有研究结论；最终证据评级仍受 Stage 9 提取器最后语义审计约束。

### 2. 目标身份三级解耦 (R2)
必须解耦：
1. `pre_redirect_target`：攻击意图目标；
2. `post_redirect_attack_target`：实际动作受体；
3. `damage_recipient(s)`：最终兵力实际扣除实体。

群攻以 `post_redirect_attack_target` 为中心向其余合法副目标派生。

### 3. 普通攻击完整生命周期 (R1 + Cleave/Chain Freeze)
普通攻击生命周期仍以既有时序为骨架，但铁索加入明确的 Inline / Deferred 规则：

```text
Main normal-attack damage
→ if main target has Chain and Cleave exists: defer main-target Chain
→ resolve Cleave target 1
   → Cleave damage
   → target Chain INLINE if eligible
→ resolve Cleave target 2
   → Cleave damage
   → target Chain INLINE if eligible
→ Cleave complete
→ execute main-target Deferred Chain if still eligible
→ continue later reactions / assault / combo lifecycle
```

默认所有其他合法 Damage Instance 的 Chain 都在该段伤害后立即 Inline 执行。

### 4. 反应队列 / 时序架构 (R1 + Chain Freeze)
- 采用**阶段优先级 + 局域 Inline 回调 + 少量显式 Deferred 资格**。
- Chain 默认 `PER-DAMAGE INLINE`。
- 普通攻击主目标在存在群攻时是目前已确认的 Chain Deferred 特例。
- Deferred Chain 不是固化伤害事件，而是待执行资格；执行时重新检查源节点存活与当前 Chain 状态。
- Deferred Chain 固定触发伤害值，但 owner / ratio / effect metadata 在执行时读取当前有效 Chain 状态。

### 5. 跨机制递归许可矩阵 (R4 + Frozen Records)

已冻结：

```text
Cleave → Cleave = BLOCKED
Cleave → Counter = BLOCKED
Cleave → Share = ALLOWED
Cleave → FirstAid = ALLOWED
Cleave → Chain = ALLOWED

Counter → Chain = ALLOWED

Chain → Chain = BLOCKED
Chain → Share = BLOCKED
Chain → FirstAid = BLOCKED
Chain → Counter = BLOCKED
Chain → Crit = BLOCKED
Chain → Lifesteal = BLOCKED
Chain → StrategyRecovery = BLOCKED
Chain → 刚烈不屈等受击响应 = BLOCKED

Share Damage → Share = BLOCKED
Share Damage → FirstAid = BLOCKED
Share Damage → Counter = BLOCKED
Share Damage → Chain = BLOCKED
Share Damage → 刚烈不屈等受击响应 = BLOCKED
```

Counter → Counter 仍保留为最终提取器语义复核项，不因 Chain 已冻结而自动升级。

### 6. 派生伤害数学语义 (R3)

#### 6.1 SPLIT / Share
分担属于被动数值结算支路。其完整基数 / 致死边界仍属于下一阶段 Share 专题。

#### 6.2 TRANSFER / Guard
援护属于动作级重定向，继续维持既有研究框架。

#### 6.3 COPY / Cleave — FROZEN

```text
CleaveDerivedDamage = MainAttackFinalDamage × CleaveRatio
```

群攻继承原攻击 DamageType，并使用自身许可矩阵。

#### 6.4 TRUE_FEEDBACK / Chain — FROZEN

```text
ChainCalculatedDamage = TriggerNodeResolvedDamage × CurrentChainRatio
```

Chain 为独立 `TRUE_FEEDBACK` 类型，不继承原始兵刃 / 谋略 DamageType。

每个合法同阵营传播目标都独立获得完整比例，不做均分。

### 7. 理论 / 计算伤害 vs 实际兵力损失

群攻：使用主攻击最终结算伤害作为派生基数。

铁索：

```text
ChainCalculatedDamage = TriggerNodeResolvedDamage × CurrentChainRatio
AppliedTroopLoss = min(ChainCalculatedDamage, CurrentTroops)
CreditedDamage = AppliedTroopLoss
```

Chain overkill 不计入伤害统计；击杀归 Chain effect owner。

Share 的完整基数与死亡截断继续单独研究，禁止从旧统计直接冻结。

### 8. 派生伤害 Pipeline (R3 + Frozen Records)

#### 8.1 Cleave — FROZEN

```text
MainAttackFinalDamage
→ × CleaveRatio
→ CleaveDerivedDamage
→ Evasion
→ Barrier
→ no target-side damage modifier re-entry
→ Share if present
→ Troop Loss
→ allowed recovery callbacks
```

群攻：
- 可规避；
- 可抵御并消耗一次抵御；
- 不重新吃副目标自身伤害增减；
- 可分担；
- 可急救；
- 兵刃型可按规则倒戈，谋略型可按规则攻心；
- 不反击、不群攻自递归。

#### 8.2 Chain — FROZEN

```text
TriggerNodeResolvedDamage
→ × CurrentChainRatio
→ TRUE_FEEDBACK
→ no Evasion
→ no Barrier
→ no target-side damage modifier
→ no Share
→ no Crit reroll
→ restricted troop-loss settlement
→ no hit-response callback chain
```

Chain 不触发急救、反击、倒戈、攻心、刚烈等响应，也不再次触发 Chain。

#### 8.3 Share Passive Settlement

```text
Share Damage
→ passive troop-number settlement
→ no new FirstAid / Counter / Chain / Share / hit-response chain
```

### 9. 战报因果溯源结构 (R8)
继续区分：
1. `LOG FACT`：原始平铺战报；
2. `RECONSTRUCTED MODEL`：从日志重建动作 / 反应边界；
3. `ENGINEERING MODEL`：模拟器内部 `root_action_id`、reaction provenance、timing policy 等实现字段。

不得把工程字段宣称为官方内部调用栈事实。

### 10. 死亡与终战边界 (R5 + Chain Freeze)

Chain 已确认：

```text
Trigger node dies from triggering damage
→ Chain does not start

Deferred Chain source dies before execution
→ Cancel

One feedback target dies
→ only that target settlement ends
→ remaining legal targets continue
```

传播目标按槽位顺序继续结算，不因前一个目标死亡而整体中止。

其余 Battle Victory / commander death / skill-loop 等总终战规则仍维持既有 R5 研究状态。

### 11. 多来源冲突与状态生命周期 (R6 + Chain Freeze)

#### 11.1 Chain 单实例覆盖 — FROZEN

同一目标铁索不可多份并存：

```text
same owner reapply
→ refresh / overwrite
→ duration reset to 2

other owner reapply
→ later state overwrites earlier state
→ owner / ratio / metadata become later state
→ duration reset to 2
```

每次合法伤害仍只产生一次 Chain。

Chain feedback 的 owner / ratio 来自**触发节点当前 activeChainEffect**，接收目标自己的 Chain owner / ratio 不影响本次收到的反馈。

#### 11.2 Chain owner death — FROZEN

施加者死亡不会清除已施加的 Chain：
- 状态继续倒计时；
- 传播伤害不衰减；
- 伤害 / 击杀仍归原施加者；
- 已死亡施加者本人应获得的治疗等收益跳过。

#### 11.3 Chain duration / cleanse — FROZEN

- 持续时间在目标自身 `[单位]开始行动` 节点扣减；
- `1 → 0` 时先移除，再结算持续伤害；
- 震慑不阻止 duration tick；
- 净化 / 驱散负面可在当前微步立即移除 Chain；
- 净化后重新施加是全新实例。

控制状态更强覆盖、更广泛多来源同类 Reaction 顺序仍按各自专题处理。

### 12. 确定性与 RNG (R7 + Chain Freeze)

Chain 多目标传播**不使用 RNG**，按固定槽位：

```text
slot 0 → slot 1 → slot 2
```

每个目标轮到时执行 JIT revalidation：

```text
same camp
alive
chain active
not trigger node itself
```

连击第二击重新索敌与严格 transition matrix 的统计封口仍属于 R7 独立问题。

---

## Chain 触发资格汇总

可以触发：

```text
Normal Attack Damage
Skill Damage
Periodic Damage
Cleave Damage
Counter Damage
```

明确不能触发：

```text
Chain TRUE_FEEDBACK
Share Passive Numeric Settlement
```

0 伤害的合法伤害结算仍会执行 Chain，只是反馈伤害为 0。

---

## 与 Stage 8 Frozen Contract 边界评估

1. **Counter**: 仍可作为新的攻击/伤害动作走既有 Stage 8 能力边界。
2. **Cleave**: 固定派生值，跳过 Base Formula，使用 Cleave 专属许可矩阵。
3. **Chain**: `TRUE_FEEDBACK`，跳过 Base Formula，并且进一步跳过 Evasion / Barrier / Modifier / Share / hit callback 层，使用受限直接数值结算。
4. **Share**: 分担者支路目前已确定是 Passive Numeric Settlement，但其上游 ShareBase 等核心数学仍待下一专题冻结。
5. **结论**: Stage 9 设计需要能够表达不同派生类型的 provenance、permission matrix、timing policy 与 attribution owner。当前事实**不构成 Stage 8 Formal Reopen**。

---

## 当前冻结状态

```text
Stage 8 = FROZEN
Cleave Core Mechanics = FROZEN
Chain Core Mechanics = FROZEN
Share Core Mechanics = NEXT RESEARCH TARGET
```
