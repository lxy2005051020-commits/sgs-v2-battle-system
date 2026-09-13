# 690103 CONFUSION / 混乱 — Freeze Audit

Audit Date: `2026-09-13`  
Target Contract: [`MECHANISM_CONTRACT.md`](MECHANISM_CONTRACT.md)  
Audit Result: `PASS / FROZEN`

---

# 1. Audit Goal

本审计只检查：

```text
690103 CONFUSION / 混乱
```

是否已经达到项目冻结门槛：

```text
BLOCKER = 0
MAJOR = 0
Implementation-blocking unresolved = 0
```

不借本次审计扩展研究其他控制状态，也不把来源战法自身规则混入状态合同。

---

# 2. Scope Audit

依据项目 `STATE_MECHANISM_SCOPE_BOUNDARY`，混乱合同应只覆盖：

```text
L1 STATE_KERNEL
L2 STATE_INSTANCE_LIFECYCLE
L3 BATTLE_EVENT
L4 INTERACTION
```

审计结果：`PASS`。

合同没有把以下来源战法层内容冻结成状态规则：

```text
具体战法发动概率
具体战法为什么命中某目标
具体战法为什么给 N 回合混乱
具体战法自己的公式与触发条件
```

战法名称只用于行为样本归因与 TargetSelector 类型验证。

---

# 3. Question Closure Audit

| Q | Research Item | Audit Status |
|---|---|---|
| Q01 | 混乱究竟修改哪些目标合法性条件 | ✅ CLOSED |
| Q02 | 混乱在什么时点检查 | ✅ CLOSED |
| Q03 | 混乱 × 嘲讽 | ✅ CLOSED |
| Q04 | 混乱 × 挑拨 | ✅ CLOSED |
| Q05 | 混乱 × 穷追 | ✅ CLOSED |
| Q06 | 持续时间 / 生命周期 | ✅ CLOSED |
| Q07 | 重复施加 | ✅ CLOSED |
| Q08 | 无法正常行动时是否消费持续时间 | ✅ CLOSED |
| Q09 | 来源死亡 | ✅ CLOSED |
| Q10 | 净化移除时机 | ✅ CLOSED |
| Q11 | 洞察免疫门 | ✅ CLOSED |
| Q12 | 已有父目标是否重新选取 | ✅ CLOSED |
| Q13 | 随机单目标分布 | ✅ CLOSED |
| Q14 | 随机多目标分布 | ✅ CLOSED |
| Q15 | 排序 / 极值 / 身份 Selector | ✅ CLOSED |
| Q16 | 准备战法的混乱判定时点 | ✅ CLOSED |

结论：

```text
Open Core Research Questions = 0
```

---

# 4. L1 STATE_KERNEL Audit

## 4.1 Core Definition

合同将混乱定义为：

```text
TargetSelector Side-Constraint Suppressor
```

而不是：

```text
RandomTargetOverride
IgnoreAllTargetRules
TargetPoolRebuilder
```

审计结果：`PASS`。

## 4.2 Exact Mutation Boundary

合同明确：

```text
REMOVE:
  Side Predicate only

PRESERVE:
  Alive
  Self Include / Exclude
  Target Count
  Identity Predicate
  Attribute Predicate
  Relationship Anchor
  Ordering
  Sampling
  Skill-specific predicates
```

与 Q01、Q13、Q14、Q15 的研究结论一致。

审计结果：`PASS`。

## 4.3 Random Single Consistency

冻结模型：

```text
Expanded Legal Candidate Pool
→ one flat uniform selection
```

关键样本：

```text
1 ally + 3 enemies
N = 104
Friendly hit = 26 = 25.00%
```

符合 `1/4` 扁平池模型，排除阵营先行 50/50 模型。

审计结果：`PASS`。

## 4.4 Random Multi Consistency

冻结模型：

```text
Expanded Legal Candidate Pool
→ Sampling Without Replacement
→ no camp quota
```

真实存在：

```text
2-target selector → 2 allies + 0 enemies
```

且单次目标互异。

审计结果：`PASS`。

## 4.5 Ordered / Extreme Selector Consistency

冻结模型：

```text
Remove Side Predicate
→ preserve ArgMin / ArgMax / Sorting / Identity Filter
```

与【暗潮涌动】、【避实击虚】、【刮骨疗毒】类样本一致。

审计结果：`PASS`。

---

# 5. L2 STATE_INSTANCE_LIFECYCLE Audit

## 5.1 Application

已确认：

```text
Successful Application
→ instance created
→ immediately active
```

与同一 Action Window 后续 Target Selection 立即受影响的样本一致。

审计结果：`PASS`。

## 5.2 Immunity Gate

已确认洞察类控制免疫在：

```text
Status Application Gate
```

直接拒绝混乱实例创建。

不会回滚已经发生的目标选择与前置伤害。

审计结果：`PASS`。

## 5.3 Reapplication

已确认：

```text
Single Instance
+ Existing Instance → Hard Reject
```

不存在：

```text
Refresh
Overwrite
Extend
Max-duration merge
Multiple instances
```

审计结果：`PASS`。

## 5.4 Zero Remaining vs Physical Existence

临界样本确认：

```text
remainingTurns == 0
but instance not yet removed
→ new CONFUSION still rejected
→ next Owner Action Start removes old instance
```

因此合同明确按“实例存在性”而不是 `remainingTurns > 0` 判断重施。

审计结果：`PASS`。

## 5.5 Duration Consumption

已确认：

```text
Duration Unit = Owner Action Window
```

并且：

```text
无法正常行动
!= 冻结混乱持续时间
```

只要自身 Action Window 被推进，本窗口仍消费持续时间。

审计结果：`PASS`。

## 5.6 Natural Expiration

冻结：

```text
Owner Action Start
→ remainingTurns <= 0
→ remove before action logic
```

这与战报中的“开始行动 → 混乱消失 → 后续正常行动”顺序一致。

审计结果：`PASS`。

## 5.7 Purge

冻结：

```text
Purge resolution
→ immediate physical remove
→ later same-window selectors immediately see no confusion
```

21 例 Self-Purge 样本中，净化后同一 Action Window 再次执行混乱为 0。

审计结果：`PASS`。

## 5.8 Source Death

冻结：

```text
Source dies
→ existing CONFUSION remains active
```

并保留来源归因信息。

审计结果：`PASS`。

## 5.9 Target Death

合同引用项目全局硬终止基线：

```text
TARGET_DEATH
→ CLEAR_ALL_STATES
→ ABORT_REMAINING_STATE_RESOLUTION
→ ABORT_REMAINING_ACTION
→ REJECT_FUTURE_STATE_APPLICATION
```

不存在与混乱局部生命周期冲突。

审计结果：`PASS`。

---

# 6. L3 BATTLE_EVENT Audit

## 6.1 JIT Timing

冻结：

```text
Evaluation Trigger = EACH ACTUAL TARGET SELECTION
```

不是：

```text
Turn Start Snapshot
Action Start Snapshot
Skill Start Snapshot
Preparation Start Snapshot
```

审计结果：`PASS`。

## 6.2 Apply / Purge Dynamic Visibility

Q02、Q10 构成双向一致闭环：

```text
false → true
successful apply
→ next selection immediately sees confusion

true → false
successful purge
→ next selection immediately sees no confusion
```

不存在 Action Window 级缓存模型。

审计结果：`PASS`。

## 6.3 Already-Selected Target

合同明确：

```text
Confusion does not retroactively rewrite completed Target Selection.
```

因此状态变化只影响后续新选择。

审计结果：`PASS`。

## 6.4 No Artificial Reselection

Q12 确认：

```text
If effect inherits parent actualTarget
→ no new TargetSelector
→ no new confusion execution
```

67 / 67 单体“对目标”型后续效果继承普通攻击目标。

合同同时保留：

```text
若效果本身创建新的独立 Selector
→ CONFUSION 正常 JIT
```

两者无矛盾。

审计结果：`PASS`。

## 6.5 Prepared Skill

Q16 确认：

```text
Prepare Start → no target lock / no confusion snapshot
Resolve → JIT current confusion
```

动态翻转样本：

```text
无混乱准备 → 有混乱发动：N=84
有混乱准备 → 解混后发动：N=65
```

与 Q02 完全一致。

审计结果：`PASS`。

---

# 7. L4 INTERACTION Audit

本节只审计混乱自身的相对阶段，不替其他状态建立完整合同。

## 7.1 Taunt

冻结：

```text
CONFUSION > TAUNT
```

1,318 个重叠样本中：

```text
Confusion branch = 1,318
Taunt branch = 0
```

施加先后顺序不改变结果。

审计结果：`PASS`。

## 7.2 Provocation

冻结：

```text
CONFUSION > PROVOCATION
```

混乱存在时，挑拨 forced-target branch 不执行。

审计结果：`PASS`。

## 7.3 Pursuit

冻结：

```text
CONFUSION > PURSUIT
```

混乱普通攻击样本中，Pursuit success/failure roll 均未进入；混乱消失后该分支恢复。

审计结果：`PASS`。

## 7.4 Guard / Cover Phase Boundary

已冻结援护合同规定：

```text
Target Selection → originalTarget
Target Resolution / Cover → actualTarget
Target Lock
```

因此：

```text
CONFUSION can determine originalTarget
GUARD can later redirect actualTarget
```

这与 Q03-Q05 不冲突，因为它们发生在 Target Selection Precedence；援护属于后续 Target Resolution。

审计结果：`PASS`。

重要限制：

```text
不得外推为 CONFUSION > EVERY TARGET MECHANIC
```

合同已明确写入该边界。

---

# 8. Cross-Question Consistency Audit

## 8.1 Q01 + Q13 + Q14 + Q15

四题统一为：

```text
Confusion changes Candidate Legality only
→ Side Predicate removed
→ Selection Strategy preserved
```

无冲突。

Result: `PASS`。

## 8.2 Q02 + Q10 + Q16

三题统一为：

```text
Current State Container
→ read JIT at actual Target Selection
```

Apply、Purge、Prepared Skill 均符合这一模型。

Result: `PASS`。

## 8.3 Q06 + Q07

二题共同要求区分：

```text
remainingTurns == 0
```

与：

```text
instance physically absent
```

合同已明确区分，因此没有“0 回合状态可以被刷新”的实现漏洞。

Result: `PASS`。

## 8.4 Q09 + Provenance

来源死亡：

```text
不影响运行
```

但：

```text
source / sourceSkill provenance retained
```

两者语义不冲突。

Result: `PASS`。

## 8.5 Q03–Q05 + Guard

统一目标管线：

```text
Target Selection Precedence
→ originalTarget
→ Post-selection Target Resolution
→ actualTarget
```

混乱短路前置 forced-target / lock 分支，但不阻断后置援护重定向。

Result: `PASS`。

---

# 9. Implementation Audit

实现至少需要以下能力：

```text
1. Actor current-state JIT query
2. Selector side predicate suppression
3. Preserve-all-other-selector-semantics path
4. Single-instance confusion slot / lookup
5. Hard reject reapplication
6. Owner Action Start expiration gate
7. Owner Action Window End duration consumption
8. Immediate purge removal
9. Source provenance independent from source alive
10. Parent-target inheritance without forced reselection
```

上述能力均可直接从现有冻结规则确定，不存在必须等待更多状态研究才能实现的混乱内部语义。

Result: `PASS`。

---

# 10. Non-Blocking Boundaries

以下未在混乱合同中定义，但不构成混乱机制冻结阻塞：

```text
A. 基础 TargetSelector 的 RNG seed / random stream 消耗细节
B. ArgMin / ArgMax 完全相等时基础 Selector 的 tie-break 规则
C. 具体来源战法提供的基础持续回合数
D. 具体来源战法自身发动概率与目标数量
E. 其他控制状态是否继承相同 reapplication / source-death 模型
```

原因：

```text
A/B = Base TargetSelector responsibility; CONFUSION inherits it unchanged
C/D = Source skill layer; out of state-mechanism scope
E   = Other state research; cannot be generalized from CONFUSION
```

因此：

```text
Implementation-blocking unresolved = 0
```

---

# 11. Severity Result

```yaml
BLOCKER: 0
MAJOR: 0
MINOR: 0
NON_BLOCKING_BOUNDARY: 5
IMPLEMENTATION_BLOCKING_UNRESOLVED: 0
```

---

# 12. Freeze Gate

项目冻结门槛：

```text
BLOCKER = 0
MAJOR = 0
Implementation-blocking unresolved = 0
```

本次结果：

```text
0 / 0 / 0
```

最终裁决：

```text
690103 CONFUSION / 混乱
✅ FREEZE GATE PASSED
✅ MECHANISM CONTRACT FROZEN
```

重新打开条件：

```text
只有出现能够直接反驳当前冻结外部行为的新增高质量战报证据，
或发现合同内部存在新的实现级矛盾，才重新进入研究阶段。
```
