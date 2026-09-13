# Stage 9 v2 内部结论一致性审计表 (Post Cleave / Chain Freeze Sync)

> **历史审计基线 Commit**: `de80a4ec30fb3bf50220a719011478116bd34e5b`  
> **后续冻结记录**: `STAGE9_CLEAVE_MECHANICS_FREEZE_RECORD.md`, `STAGE9_CHAIN_MECHANICS_FREEZE_RECORD.md`  
> **当前原则**: 历史统计审计用于证据溯源；若其机制解释与后续逐项直接冻结规则冲突，以最新冻结记录、R3/R4 与 Stage 9 总规为当前唯一事实基线。

---

## 一、 当前一致性总表

| 主题 | 历史状态 | 后续冻结后的统一结论 | 当前状态 |
|---|---|---|---|
| confusion vs taunt | 历史提取器支持混乱压制嘲讽 | 保持历史结论，但最终证据强度仍受提取器语义终审约束 | PENDING AUDIT QUALITY |
| guard vs taunt | 援护可重定向嘲讽后的实际承伤者 | 无本轮冲突 | CONSISTENT |
| cleave vs counter timing | 群攻先于普通反击 | 保持；群攻副目标 Chain 可在各自群攻伤害后 Inline | CONSISTENT + EXTENDED |
| counter vs assault | 普通反击先于突击 | 无本轮冲突 | CONSISTENT |
| commander death | 当前原子动作与未来反应分层处理 | Chain 目标循环的局部死亡规则已单独冻结 | CONSISTENT + EXTENDED |
| Counter→Counter | 历史样本方向支持 BLOCKED | 不升级为 Frozen，继续等提取器语义终审 | PENDING |
| Cleave→Cleave | 历史曾因分母 0 写 NOT OBSERVED | 已直接确认 `BLOCKED — FROZEN` | **RESOLVED** |
| Chain→Chain | 历史统计支持 BLOCKED | 已直接确认 `BLOCKED — FROZEN`，不再依赖旧分母证明实现语义 | **RESOLVED** |
| Share→Share | 历史曾因分母 0 写 NOT OBSERVED | 已直接确认 Share passive settlement 不会再触发 Share | **RESOLVED** |
| Cleave Pipeline | 旧版写 fixed base + target modifier re-entry | **废弃旧模型**。Cleave 可规避、可抵御、可分担，但不重新吃副目标伤害增减 | **FIXED** |
| Chain Pipeline | 旧版写 fixed base + target modifier / Barrier / Evasion re-entry | **废弃旧模型**。Chain 为 TRUE_FEEDBACK，不可规避、不可抵御、不吃目标侧增减伤、不可分担 | **FIXED** |
| Chain FirstAid | 旧统计曾将 Chain→FirstAid 视为允许 | 已直接确认 `BLOCKED — FROZEN` | **FIXED** |
| Chain Counter | 历史统计方向支持不触发 | 已直接确认 `BLOCKED — FROZEN` | **RESOLVED** |
| Cleave→Chain | 历史存在相关样本但旧总规未冻结 | 已直接确认 `ALLOWED — FROZEN`；群攻副目标受伤后可立即 Inline Chain | **RESOLVED** |
| Counter→Chain | 历史支持 | 已直接确认 `ALLOWED — FROZEN`，反击伤害后 Inline | **RESOLVED** |
| Share→Chain | 旧矩阵未明确冻结 | 已直接确认 `BLOCKED — FROZEN` | **RESOLVED** |
| Chain 多来源 | 旧版未完整裁决 | 单实例；后发覆盖；owner/ratio 使用执行时当前有效状态；持续时间刷新 2 回合 | **RESOLVED** |
| Chain owner death | 旧版未完整裁决 | 施加者死亡不清除状态；伤害/击杀仍归该 owner；死者自身治疗收益丢弃 | **RESOLVED** |
| Chain duration / cleanse | 旧版未完整裁决 | ACTION_START 扣减；到期先于持续伤害；震慑照常 tick；净化即时移除 | **RESOLVED** |
| combo retarget | 历史统计支持重索敌 | 重索敌强结论保留；严格 transition matrix 仍需最终统计封口 | PENDING STAT CLOSURE |
| stronger control overwrite | 未证实 | 仍 UNKNOWN / 待研究 | PENDING |

---

## 二、 Cleave 当前唯一统一模型

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

```text
Cleave → FirstAid = ALLOWED
Cleave → Share = ALLOWED
Cleave → Chain = ALLOWED
Cleave → Counter = BLOCKED
Cleave → Cleave = BLOCKED
```

群攻继承源攻击 DamageType；兵刃 / 谋略分别进入对应恢复类判定。

---

## 三、 Chain 当前唯一统一模型

```text
TriggerNodeResolvedDamage
→ × trigger-node current ChainRatio
→ TRUE_FEEDBACK
→ no Evasion
→ no Barrier
→ no target-side damage modifier
→ no Share
→ no second Crit
→ applied troop-loss settlement
→ no hit-response callbacks
```

```text
Chain → FirstAid = BLOCKED
Chain → Counter = BLOCKED
Chain → Chain = BLOCKED
Chain → Share = BLOCKED
Chain → Lifesteal = BLOCKED
Chain → StrategyRecovery = BLOCKED
Chain → 刚烈不屈等受击响应 = BLOCKED
```

可触发 Chain：

```text
Normal Attack / Skill / Periodic / Cleave / Counter damage
```

不可触发 Chain：

```text
Chain TRUE_FEEDBACK
Share Passive Numeric Settlement
```

---

## 四、 Chain 时序统一模型

默认：

```text
Damage Instance
→ Chain INLINE
→ continue
```

普通攻击主目标 + 群攻特例：

```text
Main target damage
→ defer main-target Chain
→ resolve all Cleave targets and each target's Inline Chain
→ Cleave complete
→ execute main-target Deferred Chain
```

Deferred Chain：

```text
fixed: triggerDamage
JIT at execution: source alive + activeChainEffect exists
execution-time dynamic: owner / ratio / effect metadata
```

死亡或状态失效：Cancel。状态被覆盖：使用当前新 owner / ratio。

---

## 五、 Chain 传播与状态生命周期统一模型

传播：

```text
same camp only
slot 0 → slot 1 → slot 2
JIT revalidation per target
broadcast full ratio to each eligible target
one target death does not stop remaining targets
```

状态：

```text
single active Chain instance per unit
same-source reapply → refresh to 2 turns
different-source reapply → later effect overwrites owner/ratio and refreshes to 2 turns
owner death → state remains
cleanse → immediate removal
reapply after cleanse → brand-new instance
duration tick → target ACTION_START
1→0 expiry → before periodic damage
stun → does not prevent duration tick
```

---

## 六、 一致性审计结论

本轮同步后，以下旧版互斥断言已从当前主文档体系中废弃：

```text
Cleave target modifier re-entry
Chain Evasion / Barrier / target modifier re-entry
Chain → Share ALLOWED
Chain → FirstAid ALLOWED
Cleave→Cleave merely NOT OBSERVED
Share→Share merely NOT OBSERVED
```

当前主基线已经统一为：

```text
Cleave Core Mechanics = FROZEN
Chain Core Mechanics = FROZEN
Share Core Mechanics = NEXT RESEARCH TARGET
```

尚未解决的问题必须继续标记为 PENDING / UNKNOWN，不得因为 Cleave / Chain 已冻结而顺带宣布整个 Stage 9 完成。
