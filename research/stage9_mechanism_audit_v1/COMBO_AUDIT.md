# Stage 9 Mechanism Audit v1 — COMBO / 连击

```text
Mechanism: combo / 连击 / 690081
Audit mode: independent, counterexample-first, evidence-first
Production code touched: NO
Stage 8 Damage Pipeline touched: NO
Verdict: FAIL — MORE RESEARCH REQUIRED
Blocking findings: 2
Audit date: 2026-09-13
```

> 本报告只审计 `combo / 连击`。它不设计 Stage 9 类名，不修改生产实现，也不因为已有文件写了 `FROZEN` 就自动继承其结论。
>
> 本轮区分四类陈述：**直接观察事实（OBSERVED）**、**统计推断（STATISTICAL）**、**间接推断（INFERRED）**、**工程抽象（ENGINEERING）**。只有证据能够支撑的层级才进入裁决。

---

# 1. Scope

本审计回答以下问题：

- 连击究竟产生什么事件；
- 第二击是否为完整标准普通攻击；
- 第二击是否重新进行目标决议；
- Combo Checkpoint 位于哪里；
- 第二击是否重新读取当前状态；
- 第二击能否触发普通攻击的下游观察者；
- 单次 Action 是否最多只有一份连击追加机会；
- 第一击后缴械、震慑、死亡、主将阵亡、无目标、战斗结束分别如何处理；
- 哪些 RNG 结论可冻结，哪些只能保留为未知；
- 现有绝对化表述是否真正得到全称证据支持。

本审计不研究连击具体来源战法的数值概率，也不借助当前模拟器行为反推游戏规则。

---

# 2. Research Baseline

## 2.1 Battle repository

审计开始时读取：

```text
repository: lxy2005051020-commits/sgs-v2-battle-system
main: current latest baseline
Stage 8: FROZEN
Stage 9: NOT STARTED / READY FOR DESIGN
```

`stage9-redirect-reaction` 分支存在，但与当前 `main` 已明显分叉：

```text
ahead_by  = 3
behind_by = 46
```

其 `STAGE9_PREPARATION.md` / `STAGE9_EVIDENCE_MATRIX.md` 仍固定在旧 battle HEAD `660fefe...` 与旧 state-research baseline `7f134568...`，因此只能作为历史 pre-design 资料，不能覆盖当前研究。

## 2.2 Research source priority

当前 `research/README.md` 明确规定：

```text
official_state_catalog_v1
>
stage9_core_arbitration_v2   CURRENT NORMATIVE BASELINE
>
stage9_core_arbitration_v1   historical reference
>
legacy state_catalog_v1
```

因此本审计不会把 v1 的绝对化结论直接当作当前规范。

## 2.3 Independent state-mechanics repository

同时读取：

```text
repository: lxy2005051020-commits/sgs-state-mechanics-research
latest combo status: FROZEN
latest combo freeze commit: 10226e9afa627eadfc447cb8b0ee5613a15eadc5
latest index/scope commit: 9d86e54c407913ff020bafacf8196085780b99c6
```

当前正式 combo 文件为：

```text
states/functional/combo/MECHANISM_CONTRACT.md
```

但其结论仍必须接受本轮独立反例审计。

---

# 3. Claimed Mechanics

当前最新 Combo Contract 的主要主张可归纳为：

1. 连击追加的是新的、完整的标准 `NORMAL_ATTACK`，不是附加伤害段；
2. 单次 Action 最多追加 1 次普攻，总物理普攻次数上限为 2；
3. 第二击不继承第一击目标，而重新进行目标决议；
4. 第一击所有同步派生结算结束后才进入 Combo Checkpoint；
5. `cfg 230` 表示追加机会已调度，但不保证第二个 `cfg 9` 一定产生；
6. 击间遭缴械 / 震慑时可以出现 `cfg 230 → cfg 46/44 → 无 cfg 9 #2`；
7. 第二击重新进入标准普通攻击观察者链，包括目标规则、伤害、突击、受击反应等；
8. 连击机会一旦调度不重试；
9. 第二击不会再次连击形成第三击；
10. 最新 state-research Contract 进一步主张：**当前行动者即使在第一击反应链中死亡，当前 Action 仍继续，甚至仍可打出第二击**；
11. 最新 Contract 还主张：第一击消灭全部合法敌军后仍会先输出 `cfg 230`，随后因无目标而没有第二个 `cfg 9`，再到 Action End 与胜负宣告。

第 10、11 项与现存其他高优先级研究发生直接冲突，是本次审计的核心。

---

# 4. Evidence Reviewed

本轮实际交叉核对的主要证据包括：

```text
battle repo:
- PROJECT_STATUS.md
- PROJECT_ROADMAP.md
- research/README.md
- research/stage9_core_arbitration_v1/README.md
- research/stage9_core_arbitration_v1/STAGE9_CORE_ARBITRATION_RULES.md
- research/stage9_core_arbitration_v1/RESEARCH_Q1_Q2_Q11_TARGET_RESOLUTION.md
- research/stage9_core_arbitration_v1/RESEARCH_Q3_Q4_Q10_ATTACK_LIFECYCLE.md
- research/stage9_core_arbitration_v1/RESEARCH_Q5_Q6_Q7_Q8_DAMAGE_DERIVATION.md
- research/stage9_core_arbitration_v1/RESEARCH_Q9_Q12_PROVENANCE_AND_RNG.md
- research/stage9_core_arbitration_v2/README.md
- research/stage9_core_arbitration_v2/R1_ATTACK_LIFECYCLE_AND_REACTION_ORDER.md
- research/stage9_core_arbitration_v2/R5_DEATH_TERMINATION_MATRIX.md
- research/stage9_core_arbitration_v2/R7_RNG_AND_DETERMINISM.md
- stages/stage9/STAGE9_PREPARATION.md @ stage9-redirect-reaction
- stages/stage9/STAGE9_EVIDENCE_MATRIX.md @ stage9-redirect-reaction

state-mechanics repo:
- states/functional/combo/MECHANISM_CONTRACT.md
- states/functional/combo/COUNTEREXAMPLE_AUDIT.md
- states/functional/combo/CROSS_QUESTION_CONSISTENCY_AUDIT.md
- states/functional/combo/RESEARCH_EVIDENCE_INDEX.md
- states/functional/combo/questions/Q36.md
- states/functional/combo/questions/Q37.md
- states/functional/combo/questions/Q46.md
- STATE_MECHANICS_INDEX.md latest death-scope amendment
```

重要的可复现性限制：battle repo v2 自己声明为 `PARTIALLY REPRODUCIBLE FROM REPOSITORY`，完整复现仍依赖原始战报数据库。因此本轮可以审计 GitHub 中保存的证据、统计、原始切片和相互一致性，但不能伪装成已经重新跑过用户本地整库。

---

# 5. Trigger Audit

## 5.1 连击触发主体

**结论：持有有效连击资格的当前行动者。**

支持来源：官方定义“每回合可额外进行一次普通攻击”以及大量 `cfg 230 → cfg 9` 行动内样本。

评级：**A — STRONGLY CONFIRMED**（外部语义）。

## 5.2 Combo Checkpoint 的前置事件

可观察事实支持：

```text
第一击标准普通攻击
→ 其群攻 / 反击 / 突击等已观察后置链
→ cfg 230
→ 第二击
```

v2 R1 的成对共现统计给出：

```text
Counter before Combo: 54 : 0   Grade A
Assault before Combo: 162 : 0  Grade A
```

因此“已观察到的 Counter / Assault 位于 Combo 之前”可冻结。

但“**内部 Event Stack 一定已经完全 EMPTY**”不是战报直接字段，而是对日志拓扑的实现解释。它应标为：

```text
Observable ordering = CONFIRMED
Hidden stack emptiness = INFERRED / ENGINEERING MODEL
```

评级：外部顺序 **A**；内部栈模型 **C**。

## 5.3 第一击根本未执行时

旧 combo 专项研究 Q06/Q07 以及行动前缴械样本支持：第一击普通攻击步骤未成立时，不会凭空调度连击第二击。

评级：**B — CONFIRMED**。

---

# 6. Lifecycle Audit

## 6.1 来源死亡

Q36 检出 14 个合格样本，来源武将死亡后，已经挂在其他持有者身上的连击仍按持有者自己的行动时钟运行。

可冻结外部语义：

```text
source death
≠ remove already-applied combo on another living holder
```

评级：**B**。

## 6.2 行动中途新获得连击

已有孙权等案例支持第一击后成功获得连击，当前 Action 的后续 Combo Checkpoint 可以读取到新状态并追加第二击。

这证明不能把本 Action 的“攻击次数”在 Action Start 静态锁死。

评级：**B**。

## 6.3 临时状态生命周期

现有问题集对 `cfg 175` 处的持续时间维护、行动前 / 行动后获得 1 回合连击均有直接案例。

对于 Stage 9 公共动作模型而言，可以采用的冻结外部语义是：

```text
Combo effectiveness is evaluated on the holder's action timeline,
not consumed as a one-shot charge merely because one extra attack occurred.
```

评级：**B**。

## 6.4 “Action-local latch”

最新 Contract 使用：

```text
combo_eligible
combo_source_skill
combo_consumed
```

解释行动中取得资格、来源锁存与只消费一次。

这些字段名及 latch 结构是**工程抽象**，不是官方内部可观察事实。

允许冻结的是对应外部不变量，不允许把字段布局写成“官方机制”。

评级：外部行为 **B**；具体 latch **ENGINEERING ONLY**。

---

# 7. Target Audit

## 7.1 第二击是否重新进行目标决议

v2 R7 对 5,252 组连续普攻切片重新分层后，确认第二击存在大量目标切换，因此：

```text
Attack #2 does not hard-inherit Attack #1 target.
Attack #2 re-enters target resolution using the then-current battlefield state.
```

这是 Stage 9 真正需要的公共语义。

评级：**B — CONFIRMED**。

## 7.2 “独立均匀随机”是否成立

**不成立，至少当前证据不能支持。**

v2 R7 已主动修正 v1 的旧说法：

```text
3 normal candidates, target #1 survived:
observed same target = 48.75%
independent-uniform expectation = 33.33%

2 normal candidates:
observed same target = 64.11%
independent-uniform expectation = 50.00%
```

因此最新 Combo Contract 中“再次独立均匀随机选择目标”的绝对表述与 battle repo 当前 v2 RNG 报告冲突。

裁决：

```text
fresh target resolution       = B CONFIRMED
uniform i.i.d. target draw    = F CONTRADICTED AS A FROZEN CLAIM
exact official target weights = UNKNOWN
```

这不是 Combo 架构 blocker，只要 Stage 9 让第二击调用标准 Target Resolution，而不是在 Combo 模块自带一个均匀随机器。

## 7.3 candidate / intended / resolved

第二击应重新经历标准普通攻击的目标层级：

```text
candidate set
→ forced/intended target policy
→ intended target
→ guard redirect if applicable
→ resolved/final event target
```

“第二击重跑标准目标流程”有支持；但 Combo 本身不应该冻结混乱、嘲讽、援护的全部内部优先级，那些属于各机制及 Cross-State Audit。

评级：**B**（调用标准目标语义），交叉优先级另行 evidence-gated。

---

# 8. Ordering Audit

当前可安全冻结的 Combo 相对顺序：

```text
NormalAttack #1 main resolution
→ observed inline callbacks / Cleave / Counter / Assault according to their own rules
→ Combo Checkpoint
→ cfg 230 if eligible
→ second-attack permission/target gates
→ cfg 9 #2 if executable
→ NormalAttack #2 full observable lifecycle
→ Action End
```

其中：

- `Counter → Combo`：A；
- `Assault → Combo`：A；
- `Cleave → Combo`：由标准攻击生命周期与现有共现支持，至少 B；
- “所有可能同步事件的隐藏队列绝对为空”：仅推断，不可升格为服务器内部事实。

---

# 9. Damage Pipeline Audit

Combo 自身**不产生一种新的伤害公式**。如果第二击确属新的标准普通攻击，则其伤害部分应按标准普通攻击进入既有 Stage 8 Damage Pipeline。

逐项裁决如下：

| Pipeline item | Combo #2 audit |
|---|---|
| 基础兵刃公式 | 随标准 NormalAttack 重新计算，B |
| 攻击属性 | 读取第二击当时实时属性，B |
| 防御属性 | 按第二击当前目标读取，B |
| damage coefficient | 使用标准普攻合同，不存在 Combo 专用倍率，B |
| 增伤 / 减伤 | 作为标准攻击重新评估，B |
| 会心 | 不应继承第一击结果，按标准攻击事件独立处理，B |
| 规避 | 第二击可独立面对标准 hit/evasion 规则，B |
| 抵御 | 第二击可独立面对标准 resistance 规则，B |
| 虚弱 / 其他状态修正 | 读取第二击发动时实时状态，B |
| 兵力裁切 | 走标准 TroopSystem / Stage 8 apply 边界，B |
| 受伤回调 | 第二击造成的实际伤害可按标准事件触发，B |

证据含义需要谨慎：这里的 B 不是说每一个 Stage 8 内部函数名都在原始战报里可见，而是“第二击是标准 NormalAttack”这一事件身份与多个下游观察者实证共同支持**没有 Combo 专用简化伤害管线**。

---

# 10. Derived Event Audit

第二击的最佳语义分类是：

```text
NEW STANDARD NORMAL_ATTACK
```

不是：

```text
× extra damage segment
× copied damage
× direct troop loss
× special weapon effect damage
```

与 Counterattack 的事件身份必须严格区分。当前 v2 Counterattack Freeze 已明确 Counter 是 `WEAPON EFFECT DAMAGE, not NormalAttack`；Combo #2 则是新 NormalAttack。

评级：**A/B 边界，采用 B — CONFIRMED 作为保守审计评级**。

---

# 11. Recursion Audit

## 11.1 Combo → Combo

官方文本本身是“额外进行一次普通攻击”，且大量战报未观察到单 Action 出现第二次连击本体调度。最新 Contract 统计：

```text
17,764 场连击战报
single Action cfg230 >= 2 : 0
```

旧反例审计还对 243,037 个行动窗口排查了表面 >2 普攻，并将候选异常还原为同名实体、镜像与援护双日志。

因此可冻结**可观察行为上限**：

```text
one ordinary Action receives at most one Combo-generated extra NormalAttack
```

评级：**A**（可观察语义）。

但以下说法不得冒充直接证据：

```text
“官方内部一定存在 ActionAttackLimit = 2 字段”
```

该字段是工程推断。

## 11.2 第二击触发其他观察者

因为第二击是标准 NormalAttack，可以重新进入普通攻击观察者族。已有资料直接支持至少：

- Assault：两击都能独立触发，B/A；
- Guard：第二击是新普攻，需重新经历 redirect，B；
- Taunt：当前 v2 Taunt Freeze 明确 Combo 每击新建 NormalAttackInstance 并 JIT 重评 Taunt，A（Taunt 侧证据）；
- Counter：第二击作为新收到的普通攻击实例可重新触发，B；
- Cleave：第二击普通攻击可再次产生该击自己的 Cleave，B；
- Evasion / Resistance / FirstAid：跟随标准普攻 / 标准伤害事件，不继承第一击结果，B。

Combo 的“禁止递归”只禁止 **Combo 自己再追加第三次普通攻击**，不能误写成“第二击不触发普通攻击观察者”。

---

# 12. Death / Termination Audit

这是本次 FAIL 的核心。

## 12.1 攻击者在第一击反应链中死亡

存在两组互相排斥的正式资料。

### Evidence Set A — hard stop

battle repo 当前 normative v2：

```text
R1_ATTACK_LIFECYCLE_AND_REACTION_ORDER.md
- 113 例反击致死攻击者
- pending Assault / Combo 全部 IMMEDIATE ABORT
- Grade A

R5_DEATH_TERMINATION_MATRIX.md
- actor itself dies -> IMMEDIATE HARD STOP
- Counter killing original attacker cancels pending Combo
- Grade A
```

state-research 的旧专项证据也一致：

```text
Q37: 218 eligible holder-death cases, 0 failures
Q41/Q45 representative case 1008108...
→ holder death stops later action / no cfg230
```

### Evidence Set B — continue current Action

2026-09-13 最新 state-research Combo Contract 与随后 index amendment 改成：

```text
ACTOR_DEATH_DURING_OWN_OPEN_ACTION
→ MARK_DEAD
→ retain existing status slots
→ current Action continues
→ cfg230 may still occur
→ second NormalAttack may still execute
→ Action closes at cfg733
```

这是**规则级反转**。

问题在于：当前 GitHub Combo 目录没有与该反转同等级公开的专项重新检索报告、分母、失败数与明确原始事件切片。Contract 只笼统列出 `2494090.json` 为“永久连击 / 死亡边界相关证据”，不足以独立推翻前述 113 / 218 例统计与 main v2 Grade A 裁决。

### Audit verdict

```text
BF-COMBO-01 = BLOCKING
```

当前无法安全冻结：

```text
actor death after hit #1
→ abort Combo?
OR
→ preserve current Action and execute Combo #2?
```

这会直接决定 Stage 9 queue cancellation、actor-liveness gate、状态清理时机和 action ownership，属于架构 blocker。

## 12.2 第一击击杀敌方主将 / 战斗结束

同样存在正面冲突。

旧 combo Q46：

```text
5,000 scanned
37 eligible
0 failures
first hit kills enemy commander
→ battle FINISHED
→ cfg733
→ no cfg230 / no second attack
```

battle repo v2 R5 也把普通攻击击杀敌方主将后的后续 Assault / Combo 标为取消，Grade A。

但最新 Combo Contract 改写为：

```text
first hit eliminates all legal enemies
→ Combo Checkpoint
→ cfg230
→ no target
→ no cfg9 #2
→ cfg733
→ victory declaration
```

这里还混合了两个不应自动等价的条件：

```text
A. killed enemy commander
B. no legal targets remain
```

三战存在主将死亡即终战语义，因此“仍有副将存活但主将死亡”与“全体都死了”必须单独检索。

### Audit verdict

```text
BF-COMBO-02 = BLOCKING
```

在重新提供边界战报前，不得冻结 `battle_end` 与 `Combo Checkpoint` 的优先级。

## 12.3 主目标死亡但战斗未结束

如果第一击只击杀一个普通目标而战斗仍继续，已有“第二击转火其他存活目标”案例支持重新索敌。

评级：**B**。

---

# 13. RNG Audit

本轮明确撤销以下旧式绝对结论：

```text
× Combo #2 必定消耗 exactly 1 PRNG draw
× 只有 1 个候选目标时官方内部一定不推进 PRNG
× 第二击目标完全 i.i.d. uniform
```

战报只能冻结：

```text
1. 第二击会重新进入目标决议；
2. 第二击不固定继承第一击目标；
3. 嘲讽等强制规则可以使可观察目标确定；
4. 官方内部 PRNG 算法、种子推进与调用次数 UNKNOWN。
```

模拟器工程当然可以在唯一合法目标时不消耗 `RandomSystem`，但这是项目确定性设计，不得伪装成已证明的服务器内部实现。

评级：

```text
fresh target resolution: B
exact RNG consumption: D / UNKNOWN
uniform i.i.d.: F as frozen claim
```

---

# 14. Cross-State Interactions

当前 Combo 审计允许进入 Stage 9 设计的交叉语义只有：

```text
Combo #2
= new NormalAttackInstance
= therefore re-evaluate live normal-attack target / permission / observer rules
```

具体状态交叉仍以各自审计为准：

| Interaction | Combo-side verdict |
|---|---|
| Combo × Taunt | 每击 JIT 重评，Taunt v2 Freeze 有直接支持，A |
| Combo × Guard | 第二击为新普攻，需重新经历 Guard redirect，B |
| Combo × Confusion | 应重新进入当击 target selector；具体 candidate semantics 等待 Confusion 独立审计，C |
| Combo × Disarm | 击间可阻止第二击实际执行；`cfg230` 与 gate 的精确先后有直接案例，B |
| Combo × Stun | 同上，B |
| Combo × Counter | 第二击可再次被 Counter 观察；但第一击 Counter 杀死攻击者后的 Combo 是否存在被 BF-COMBO-01 阻塞 |
| Combo × Cleave | 每个标准普通攻击实例可有自己的 Cleave，B |
| Combo × FirstAid | 第二击伤害按标准伤害事件触发受击回调，B |

---

# 15. Counterexample Search

本轮不是为了“证明 FROZEN 文件没问题”，而是主动寻找能破坏它的条件。

已经确认的反例 / 冲突攻击结果：

1. **攻击“第二击独立均匀随机”**：v2 R7 的分层统计直接破坏 i.i.d. uniform 冻结结论；
2. **攻击“行动者死亡仍继续第二击”**：main v2 的 113 个反击致死样本与旧 combo 218 个 holder-death 样本构成相反证据；
3. **攻击“首击终战后仍先 cfg230”**：旧 Q46 37 个 eligible / 0 failures 与 main v2 R5 均给出相反行为；
4. **攻击“>2 次普攻”**：旧全库候选异常已被同名实体 / 镜像 / 援护双日志解释，未找到真实第三击；
5. **攻击“第二击继承第一击目标”**：大量不同目标样本证伪固定继承模型；
6. **攻击“第二击只是追加伤害”**：第二击具有独立 cfg9、独立目标和独立 Assault/observer 行为，不符合追加伤害模型。

---

# 16. Absolutist Claim Audit

对当前资料中常见绝对词逐项降级：

| 原表述 | 审计后表述 |
|---|---|
| “百分之百属于新的完整普通攻击” | 大量事件与观察者行为支持，保守评级 B，不声称穷尽所有未来规则 |
| “单 Action 绝不出现第三击” | 当前大规模样本 + 官方语义强支持，可冻结可观察上限 A；内部防重字段未知 |
| “第二击独立均匀随机” | **撤销，F**；只能冻结“重新目标决议” |
| “候选集 1 一定不推进 PRNG” | 官方内部不可观察，降为 UNKNOWN / engineering choice |
| “Event Stack 必定为空后才 cfg230” | 冻结可观察 ordering；隐藏栈状态仅推断 |
| “cfg230 阶段原子消费” | 可冻结“cfg230 后失败不补偿重试”的行为；内部原子变量写入属于 engineering abstraction |
| “攻击者死后当前 Action 必定继续” | **BLOCKED BY CONFLICT** |
| “攻击者死后必定立即中止” | **同样不能直接冻结**，直到冲突复核完成 |
| “主将首杀后必定取消 Combo” | 当前旧证据强，但被最新 Contract 反向改写，暂列 blocker |
| “首杀后必定先 cfg230 再判无目标” | 同上，暂列 blocker |

---

# 17. Confidence Matrix

| Claim | Evidence type | Grade | Audit status |
|---|---|---:|---|
| Combo produces one extra standard NormalAttack | direct + official + cross-observer | A/B | CONFIRMED |
| Max one Combo-generated extra attack per ordinary Action | official + large negative search | A | CONFIRMED |
| Attack #2 re-enters target resolution | direct/statistical | B | CONFIRMED |
| Attack #2 fixed-inherits target #1 | counterexamples | F | CONTRADICTED |
| Attack #2 uses uniform i.i.d. target draw | stratified stats conflict | F | CONTRADICTED AS FROZEN CLAIM |
| Exact official PRNG draw count | not observable | D | UNKNOWN |
| Counter / Assault complete before Combo checkpoint | pairwise direct stats | A | CONFIRMED |
| Hidden event stack is literally empty | inferred | C | PROVISIONAL MODEL |
| cfg230 does not guarantee cfg9 #2 | direct boundary cases | B | CONFIRMED |
| Inter-hit Disarm/Stun can block #2 | direct | B | CONFIRMED |
| Source death removes existing holder Combo | direct counterexample | F | CONTRADICTED |
| Holder/actor death during own Action aborts Combo | conflicting corpora/specs | C/F conflict | BLOCKED |
| Holder/actor death during own Action still executes Combo | latest spec but contradicted by prior evidence | C/F conflict | BLOCKED |
| Enemy commander death cancels Combo | older direct stats + v2 | B/A but conflicting latest spec | BLOCKED |
| Enemy commander death still permits cfg230/no-target path | latest spec, insufficient public re-proof | C | BLOCKED |
| Attack #2 can independently trigger Assault | direct | A/B | CONFIRMED |
| Attack #2 can re-enter standard observers | event identity + examples | B | CONFIRMED |

---

# 18. Blocking Findings

## BF-COMBO-01 — Actor death semantics are internally contradictory

**Architecture impact:** critical.

需要冻结的最小问题：

```text
If the attacking actor dies after NormalAttack #1 has started/completed
but before Combo Checkpoint:

A. Does the current Action hard-abort before cfg230?
B. Can cfg230 still emit?
C. Can cfg9 #2 still execute while actor is already cfg163 dead?
D. Are existing states retained until cfg733 or cleared at death?
```

### Required battle-report search

必须重新检索全部：

```text
actor had effective Combo eligibility
+
actor starts own Action
+
NormalAttack #1 occurs
+
actor reaches cfg163 before Combo checkpoint
```

并输出：

```text
total eligible denominator
cfg230 after death count
cfg9 #2 after death count
hard-abort count
all anomaly slices
```

至少对最新 Contract 暗示的 `2494090.json` 给出带实体身份的完整事件切片，并与旧代表 `1008108...` 做正反对照。

## BF-COMBO-02 — Commander death / battle termination priority is unresolved

**Architecture impact:** critical.

必须分离三个条件，不得再混写：

```text
A. first hit kills a non-commander target, battle continues
B. first hit kills enemy commander while deputies remain
C. first hit removes the last legal enemy unit
```

逐类统计：

```text
cfg163 commander death
cfg209 morale-loss timing
cfg157 victory timing
cfg230 presence/absence
cfg9 #2 presence/absence
cfg733 position
```

在这一问题关闭前，Stage 9 不能冻结：

```text
battle termination gate
vs
Combo checkpoint
```

的优先级。

---

# 19. Non-Blocking Findings

## NF-COMBO-01 — Uniform-random wording must be removed

Stage 9 Combo 只应要求：

```text
second attack invokes standard target resolution again
```

不得要求 Combo 自身进行均匀随机抽样，也不得冻结官方 PRNG draw count。

## NF-COMBO-02 — “atomic consume” should be separated into observable and engineering layers

可冻结：

```text
cfg230 has been emitted
+
second attack later fails permission/target gate
→ no compensating retry in the same Action
```

不可假装直接观察到：

```text
combo_consumed = true
```

这个字段只属于推荐工程模型。

## NF-COMBO-03 — Legacy Stage9 pre-design branch is stale

`stage9-redirect-reaction` 的 evidence matrix 仍固定在旧 state-research baseline，并且落后 main 46 commits。后续 Stage 9 正式设计不能继续引用它作为最新证据门禁，必须在所有单机制审计完成后统一重建。

## NF-COMBO-04 — Cross-repository status drift

battle repo 当前 v2 README 仍把：

```text
690103 CONFUSION
then
690081 COMBO
```

列为后续研究目标，而 state-mechanics repo 已将两者先后推进到 FROZEN。说明两个仓库的研究状态尚未同步，Stage 9 evidence gate 必须显式 pin 到 commit，而不能只写“latest research”。

---

# 20. Final Verdict

```text
VERDICT = FAIL — MORE RESEARCH REQUIRED

Core Combo identity               = CONFIRMED
Second standard NormalAttack      = CONFIRMED
Fresh target resolution           = CONFIRMED
Single-extra-attack cap           = STRONGLY CONFIRMED
Standard observer re-entry        = CONFIRMED
Exact PRNG consumption            = UNKNOWN / DO NOT FREEZE
Uniform i.i.d. targeting          = CONTRADICTED AS A FROZEN CLAIM
Actor-death continuation/abort    = BLOCKING CONFLICT
Commander-death termination       = BLOCKING CONFLICT
```

Combo **暂时不能晋升为 `PASS_STAGE9`**。

失败原因不是主体机制模糊，而是两个架构关键死亡边界存在相反的“已冻结”结论。继续带着这个矛盾设计 Stage 9，会迫使 Reaction Queue 在最底层同时满足“死亡立即清队列”和“死亡者仍可继续第二击”两套互斥规则。人类通常把这种情况叫“以后再修”，然后以后就会变成考古现场。

## Minimum research required to unblock

只需要优先完成两个定向复核，不必重做全部 51 问：

```text
MR-COMBO-01
Re-audit actor-death-during-own-open-action with entity-safe parsing.

MR-COMBO-02
Re-audit commander-death vs last-target-eliminated as separate termination classes.
```

两项均关闭后，再更新本文件 verdict。只有当 Blocking Finding = 0 且核心机制至少维持 B，Combo 才可进入：

```text
AUDITED
→ CONFIRMED
→ READY FOR STAGE9 DESIGN
→ PASS_STAGE9 candidate
```
