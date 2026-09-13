# Stage 9 核心底层裁决证据矩阵 (Evidence Matrix v2 - Post Freeze Sync)

> **研究基线 Commit**: `de80a4ec30fb3bf50220a719011478116bd34e5b` (main)  
> **数据基线**: 全盘扫描 32,660 份战报（全量事件逾 1,400 万条）  
> **后续冻结记录**: `STAGE9_CLEAVE_MECHANICS_FREEZE_RECORD.md`, `STAGE9_CHAIN_MECHANICS_FREEZE_RECORD.md`  
> **重要说明**: 本矩阵最初用于记录历史战报统计证据。后续 Cleave / Chain / Share Damage 的若干边界已经通过项目逐项机制确认正式冻结。若历史统计模型与冻结记录冲突，**以冻结记录和 `STAGE9_CORE_ARBITRATION_RULES_V2.md` 为当前唯一实现基线**。历史样本数仅保留用于证据溯源，不能覆盖后续已冻结规则。

---

## 置信度 / 状态口径

- `A / B / C`: 历史战报统计证据强度。
- `FROZEN — DIRECT`: 后续逐项机制确认后的项目冻结事实，不再依赖旧提取器模型来决定实现语义。
- `PENDING`: 仍受提取器最终语义审计或额外机制确认约束。

---

## 当前证据矩阵

| ID | Mechanism | 当前统一 Claim | Evidence / Source | Cases / Denominator | Current Status | Remaining Unknowns |
|---|---|---|---|---:|---|---|
| EM-01 | 目标裁决顺序 | 混乱压制嘲讽锁定，进入无差别目标选择 | `r11_confusion_taunt_data.json` | 1,351 | 历史 A；仍受提取器最终审计约束 | 精确权重分布 |
| EM-02 | 援护 vs 嘲讽 | 援护可在嘲讽目标决议后重定向实际承伤者 | 历史战报样本 | 89 | 历史 A | 无 |
| EM-03 | 自援护 | 混乱攻击友军时可出现攻击者==援护者的自攻 | 历史样本 | 25 | 历史 A | 无 |
| EM-04 | 目标解耦 | `intended_target` / `resolved_target` / `damage_recipient` 必须解耦 | 多类战报 | 3,250 | 历史 A | 无 |
| EM-05 | 群攻基准点 | 群攻围绕实际承伤动作目标派生至其他合法副目标 | 群攻战报 | 18 | 历史 B | 样本有限 |
| EM-06 | 反击承伤者 | 反击由实际受击者触发 | 历史样本 | 96 | 历史 A | 无 |
| EM-07 | 突击受体 | 突击及控制作用于实际受击动作目标 | 历史样本 | 74 | 历史 A | 无 |
| EM-08 | 普攻反应时序 | 群攻先于普通反击，反击先于突击，突击先于连击检查点 | `r1_lifecycle_data.json` | 182 | 历史 B | Chain 特殊 Inline / Deferred 已由 Chain Freeze 补充 |
| EM-09 | 急救时点 | 普通可触发急救的伤害在扣兵后进入急救回调 | 历史样本 | 4,654 | 历史 A | 不适用于 Chain / Share passive settlement |
| EM-10 | 零伤反应 | 普攻 0 伤仍可能继续产生其动作级后续机制 | `r1_edge_cases.json` | 281 | 历史 A | Chain 0 伤规则已单独冻结 |
| EM-11 | Counter→Counter | 历史样本支持 BLOCKED | `r7_recursion_denominators.json` | 0 / 90 | **PENDING FINAL EXTRACTOR AUDIT** | 状态生命周期语义提取 |
| EM-12 | Cleave→Cleave | 群攻派生伤害不会再次触发群攻 | `STAGE9_CLEAVE_MECHANICS_FREEZE_RECORD.md` | direct confirmation | **FROZEN — DIRECT** | 无 |
| EM-13 | Chain→Chain | TRUE_FEEDBACK 不会再次触发 Chain | `STAGE9_CHAIN_MECHANICS_FREEZE_RECORD.md`; 历史统计亦为 0 触发 | historical 0 / 23,620 | **FROZEN — DIRECT** | 无 |
| EM-14 | Share→Share | Share passive settlement 不再次触发 Share | Cleave/Share direct confirmation | direct confirmation | **FROZEN — DIRECT** | Share 上游数学仍待研究 |
| EM-15 | Share 数学 | 历史统计支持 SPLIT / 守恒模型 | `r6_fendan_math_data.json` | 11,381 | 历史 A；**尚未作为本轮 Share Core Frozen** | ShareBase、致死边界、取整 |
| EM-16 | Chain 反馈数学 | `TriggerNodeResolvedDamage × CurrentChainRatio`，对每个合法同阵营目标独立广播完整比例 | `STAGE9_CHAIN_MECHANICS_FREEZE_RECORD.md`; `r4_chain_damage_data.json` | 10,817+ history | **FROZEN — DIRECT** | 无核心未知 |
| EM-17 | Cleave Pipeline | `MainAttackFinalDamage × ratio`；可 Evasion / Barrier / Share；**不重新吃副目标伤害增减** | `STAGE9_CLEAVE_MECHANICS_FREEZE_RECORD.md` | direct confirmation | **FROZEN — DIRECT** | Stage 9 工程接口 |
| EM-18 | Chain Pipeline | TRUE_FEEDBACK；**不可 Evasion / Barrier / target modifier / Share**；不触发 FirstAid / Counter / Chain / 倒戈 / 攻心 / 刚烈等响应 | `STAGE9_CHAIN_MECHANICS_FREEZE_RECORD.md` | direct confirmation | **FROZEN — DIRECT** | Stage 9 工程接口 |
| EM-19 | 致死分担截断 | 历史样本中主目标致死时未观察到分担转嫁 | `r6_death_near_fendan.json` | 154 | 历史 B，**未冻结** | Share death atomic boundary |
| EM-20 | 反击致死短路 | 攻击者反击中阵亡后续突击 / 连击短路 | 历史样本 | 113 | 历史 A | 无 |
| EM-21 | 主将阵亡终战 | 当前原子动作与未来反应需分层裁决 | 历史样本 | 890 | 历史 A | 极端边界 |
| EM-22 | Chain 传播目标死亡 | 当前目标死亡不阻止同一次 Chain 继续处理其他合法目标 | `STAGE9_CHAIN_MECHANICS_FREEZE_RECORD.md`; 历史 chain-death samples | direct + historical 5 | **FROZEN — DIRECT** for Chain target-loop rule | 战斗全局终战仍由 R5 处理 |
| EM-23 | 多控制冲突 | 重复同类控制多数 cfg23 拒绝；强覆盖弱仍未证实 | 历史样本 | 1,550 | 历史 B | stronger replacement |
| EM-24 | 多反击触发 | 历史少量样本支持多反击按顺序独立触发 | 历史样本 | 8 | 历史 C | 执行顺序需继续确认 |
| EM-25 | Combo 重索敌 | 第二击重新执行目标决议；严格 transition matrix 仍需统计封口 | 历史分层数据 | 34,639 | B+ / strong | strict iid/uniform proof |
| EM-26 | 混乱即时判定 | 混乱按动作前即时状态参与目标决议 | 历史样本 | 320 | 历史 A | 无 |

---

## Cleave / Chain 后冻结覆盖声明

以下旧版断言已经正式废弃，不得再作为实现依据：

```text
旧：Cleave → target-side damage modifier re-entry
新：Cleave 不重新受到副目标自身伤害增减影响

旧：Chain → target-side modifier / Barrier / Evasion re-entry
新：Chain TRUE_FEEDBACK 不可规避、不可抵御、不吃目标侧增减伤

旧：Chain → Share / FirstAid 可以触发
新：Chain → Share / FirstAid = BLOCKED

旧：Cleave→Cleave / Share→Share 仅 NOT OBSERVED
新：两者均已通过后续直接机制确认升级为 BLOCKED — FROZEN
```

---

## 当前研究状态

```text
Cleave Core Mechanics = FROZEN
Chain Core Mechanics = FROZEN
Share Core Mechanics = NEXT RESEARCH TARGET
Counter self-recursion = PENDING FINAL EXTRACTOR AUDIT
```

历史评级统计不再用于宣称整个 Stage 9 已冻结；Stage 9 仍按专题逐个封闭。
