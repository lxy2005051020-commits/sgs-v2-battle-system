# Confusion / 混乱 Mechanism Contract

Status ID: `690103`  
Official Name: `混乱`  
English Name: `CONFUSION`  
Status: `FROZEN`

Freeze Date: `2026-09-13`

本合同用于三国志战略版战斗模拟器中的 `690103 CONFUSION / 混乱` 状态实现。

合同冻结的是经过当前逐问题研究、战报扫描与项目所有者确认后稳定成立的**状态层外部行为规则**。文中的 `TargetSelector`、`SidePredicate`、`ActionWindow`、`active_states`、`originalTarget`、`actualTarget` 等名称均为本项目的规范实现术语，不宣称复原官方源码中的真实类名或字段名。

本合同严格遵守：

```text
研究状态如何运行
而不是研究具体战法如何制造状态
```

---

# 1. Classification

```yaml
Category: CONTROL_STATE
Family: TARGET_SELECTION_MODIFIER
State_Owner: TARGET / HOLDER
Runtime_Form: TARGET_HOSTED_STANDALONE_STATE
Core_Function: SIDE_CONSTRAINT_SUPPRESSOR
Effective_Instance_Limit: 1
Stackable: false
Refreshable: false
Replaceable: false
Extendable: false
Duration_Based: true
Source_Alive_Dependent: false
Cleanse_Removal: IMMEDIATE
Evaluation_Mode: JIT
Evaluation_Granularity: EACH_ACTUAL_TARGET_SELECTION
```

核心定义：

> 混乱不是“随机目标覆盖器”，也不是重新构造一套特殊目标算法。混乱只在一次真实目标选择发生时，删除该 TargetSelector 原本的敌我阵营约束；其余合法性谓词、目标数量、身份条件、关系锚点、排序规则与采样规则全部保持原样。

形式化表达：

```text
Original Selector
=
Candidate Universe
+ Side Predicate
+ Other Predicates
+ Selection Strategy
+ Target Count

Under CONFUSION
=
Candidate Universe
+ [REMOVE Side Predicate]
+ Other Predicates unchanged
+ Selection Strategy unchanged
+ Target Count unchanged
```

---

# 2. L1 — STATE KERNEL

## 2.1 Only Side Constraint Is Suppressed

当状态持有者执行一个需要真实目标选择的行动时：

```text
if actor.has(CONFUSION):
    suppress selector.side_constraint
else:
    execute selector normally
```

混乱删除的只有：

```text
Side == ENEMY
Side == ALLY
```

混乱不会删除或修改：

```text
Alive Constraint
Self Include / Exclude Constraint
Target Count
Identity Predicate
Attribute Predicate
Relationship Anchor
Ordering Rule
Random Sampling Rule
Skill-specific Predicate
```

因此：

```text
CONFUSION
!= TargetPoolRebuilder
!= RandomTargetOverride
!= IgnoreAllTargetRules
```

---

## 2.2 Self Eligibility Is Preserved

混乱不会自动允许自选，也不会自动禁止自选。

```text
原 Selector 排除 Self
→ 混乱后仍排除 Self

原 Selector 允许 Self
→ 混乱后仍按原规则允许 Self
```

普通攻击与标准单体攻击原本排除自身时，混乱不会让持有者攻击自己。

---

## 2.3 Enemy / Ally Targeting Becomes Any-Side Targeting Only At Side Layer

例如原选择器：

```text
ENEMY + RANDOM_SINGLE + EXCLUDE_SELF
```

混乱后：

```text
ANY_SIDE + RANDOM_SINGLE + EXCLUDE_SELF
```

原本的友军治疗选择器：

```text
ALLY + other predicates
```

混乱后同样只删除 `ALLY` 阵营限制，因此敌军可以成为合法治疗目标，只要仍满足其他原始规则。

---

## 2.4 Identity Predicate Is Preserved

例如：

```text
敌军主将
=
Side == ENEMY
+ IsCommander == true
```

混乱后：

```text
IsCommander == true
```

因此双方主将可进入候选池，但副将仍然不合法。

已核验的【暗潮涌动】混乱样本中：

```text
N = 49
命中主将 = 49
命中副将 = 0
```

---

## 2.5 Relationship Anchor Is Not A Side Predicate

必须区分：

```text
“我军主将”作为普通 side + identity selector
```

与：

```text
“自身主将” / source.team.commander
```

这类固定关系锚点。

若效果语义绑定的是施法者自身队伍中的固定实体关系，例如：

```text
source.team.commander
```

则它不是一个等待混乱修改的普通阵营筛选器。

因此混乱不会把固定“自身主将”锚点改成敌军主将。

---

## 2.6 Selection Strategy Is Preserved

冻结总则：

```text
CONFUSION MODIFIES CANDIDATE LEGALITY,
NOT SELECTION STRATEGY.
```

混乱不会把原本的：

```text
Random
Sampling Without Replacement
ArgMin
ArgMax
Sorting
Identity Filter
```

改造成另一种选人算法。

---

## 2.7 Random Single Target — Flat Uniform Selection

对于原本采用等权随机单体抽取的 Selector，混乱后：

```text
1. 删除 Side Predicate
2. 生成扩大的完整合法候选池
3. 在完整候选池内执行一次原有等权随机抽取
```

不存在：

```text
先随机 ALLY / ENEMY
→ 再在该阵营内部随机单位
```

若合法候选池中有：

```text
N_ally 个友军
N_enemy 个敌军
```

则对任意合法目标：

```text
P(Target_i) = 1 / (N_ally + N_enemy)
```

实证关键矩阵：

```text
1 友 + 3 敌：104 次，友军命中 26 次 = 25.00%
```

与扁平候选池 `1/4` 完全一致，并否定“先敌我 50/50”的模型。

---

## 2.8 Random Multi-Target — Sampling Without Replacement

对于原本随机选择多个不同目标的 Selector，混乱后：

```text
1. 删除 Side Predicate
2. 保留完整合法候选池
3. 保留原 Target Count
4. 执行原有无放回抽样
```

冻结规则：

```yaml
Duplicate_Target_In_Same_Selection: FORBIDDEN
Sampling: WITHOUT_REPLACEMENT
Side_Quota: NONE
Minimum_Enemy_Count: NONE
Minimum_Ally_Count: NONE
```

因此允许出现：

```text
2 目标战法 → 2 友 0 敌
```

且真实战报中已经观测到该组合。

满员 `2 友 + 3 敌` 候选池中，抽取 `k` 个目标时，敌我数量分布服从原无放回抽样对应的组合分布；混乱不追加阵营配额。

---

## 2.9 Ordered / Extreme-Value Targeting Is Preserved

若原 Selector 为：

```text
Side Filter
→ Other Filters
→ ArgMin / ArgMax / Sorting
→ Target
```

混乱后为：

```text
[Side Filter removed]
→ Other Filters unchanged
→ same ArgMin / ArgMax / Sorting
→ Target
```

例如：

```text
敌军统率最低
```

混乱后变为：

```text
全场其他条件合法单位中统率最低
```

而不是变成随机选择。

同理，原本对友军执行 `ArgMax(损兵)` 的治疗选择器，混乱后会在扩大后的合法池中继续执行同一个 `ArgMax`。

精确 tie-break 规则属于基础 TargetSelector 本身；混乱只继承，不重新定义。

---

# 3. L2 — STATE INSTANCE LIFECYCLE

## 3.1 Successful Application Activates Immediately

一旦混乱施加成功：

```text
Create CONFUSION instance
→ add to target state container
→ immediately visible to later JIT target selections
```

不存在“等到下一回合才开始生效”的延迟激活。

同一行动窗口中，如果混乱在前序步骤刚刚成功施加，后续尚未发生的 Target Selection 立即受影响。

---

## 3.2 Insight / Control Immunity Gate Blocks Instance Creation

当一个混乱施加请求已经到达状态施加阶段，而目标当前具有对该控制状态生效的洞察免疫时：

```text
Target Selection 已经完成
前置伤害 / 其他已在前序节点结算的效果不被回滚
↓
CONFUSION Application Attempt
↓
Immunity Gate
↓
REJECT
```

外部行为：

```yaml
CONFUSION_Instance_Created: false
Added_To_Active_States: false
Apply_Then_Remove: false
Immunity_Consumed_By_This_Block: false
```

典型日志：

```text
执行来自【...】的「洞察」效果
由于「洞察」的效果，「混乱」对其无效
```

洞察不会让目标从战法 TargetSelector 中自动消失，也不会自动免除同一战法已经结算的前置伤害。

---

## 3.3 Single Instance + Hard Rejection On Reapplication

同一目标同时最多只有一个有效/尚未物理删除的混乱实例。

```yaml
Effective_Instance_Limit: 1
Multiple_Instances: false
Refresh: false
Overwrite: false
Extend: false
Max_Duration_Merge: false
Source_Replacement: false
```

当目标状态容器中已经存在混乱实例时，新的混乱施加请求：

```text
→ HARD REJECT
→ new instance discarded
→ existing instance unchanged
```

典型日志：

```text
[目标]身上已存在同等或更强的「混乱」效果
```

新施加不会：

```text
刷新持续时间
延长持续时间
按更长持续时间重置
替换来源
替换来源战法
建立第二实例
```

---

## 3.4 remainingTurns == 0 Does Not Mean Instance Removed

混乱的“计时值为 0”与“实例已经物理删除”是两个不同事实。

```text
remainingTurns == 0
!= state instance absent
```

如果旧混乱已经在上一行动窗口结束时消耗到 `0`，但持有者下一次 `Owner Action Start` 尚未来临，则旧实例仍然存在于状态容器中。

因此此时新的混乱施加仍然被旧实例硬拦截。

禁止实现：

```text
if existing.remainingTurns > 0:
    reject()
```

应按实例存在性判断：

```text
if existingInstance != null:
    reject()
```

---

## 3.5 Duration Is Owner Action Window Based

混乱持续时间的消费单位是：

```text
OWNER ACTION WINDOW
```

不是：

```text
GLOBAL ROUND
SUCCESSFUL ATTACK
SUCCESSFUL SKILL CAST
SUCCESSFUL ACTION BODY
```

冻结模型：

```text
OWNER_ACTION_START
↓
if remainingTurns <= 0:
    remove CONFUSION
    本次行动窗口不受该混乱影响
else:
    CONFUSION remains active for this action window
↓
OWNER_ACTION_WINDOW_END
↓
remainingTurns -= 1
```

---

## 3.6 Application Before / After Owner Acts

若收到 `CONFUSION(N=1)`：

### 在持有者本轮行动前施加

```text
本轮 Owner Action Window：受混乱影响
Window End：1 → 0
下一次 Owner Action Start：自然到期删除
```

实际控制行动窗口数：`1`。

### 在持有者本轮已经行动后施加

```text
本轮不再出现 Owner Action Window，因此不消费
下一轮 Owner Action Window：受混乱影响
Window End：1 → 0
再下一次 Owner Action Start：自然到期删除
```

实际控制行动窗口数仍为：`1`。

因此战报中的大回合跨度差异不能被误写成全局 Round 计时。

---

## 3.7 Unable To Act Still Consumes Duration

如果混乱持有者进入自己的 Action Window，但因其他控制原因无法完成正常战法/普通攻击流程：

```text
Owner Action Window still exists
→ confusion duration still consumes 1
```

因此：

```text
CONFUSION_DURATION_CONSUMPTION
= ACTION_WINDOW_CONSUMPTION
!= SUCCESSFUL_ACTION_CONSUMPTION
```

无法正常行动不会冻结混乱剩余持续时间。

---

## 3.8 Natural Expiration Is Checked At Owner Action Start

自然到期的物理删除节点为：

```text
Owner Action Start
→ remainingTurns <= 0
→ emit disappear event
→ remove CONFUSION instance
→ only then continue action logic
```

因此到期行动窗口内：

```text
CONFUSION 不再执行
Target Selection 恢复正常
```

---

## 3.9 Cleanse / Purge Removes Immediately

成功净化混乱时：

```text
Purge resolves
→ immediately remove CONFUSION instance
→ immediately emit disappear event
→ later target selections see CONFUSION == false
```

冻结规则：

```yaml
Removal_Mode: IMMEDIATE_HARD_REMOVAL
Lazy_Expire: false
Wait_For_Action_Start: false
Wait_For_Action_End: false
```

这与自然到期不同：

```text
Natural Expiration
→ deferred to Owner Action Start expiration gate

Purge Removal
→ immediate at purge resolution node
```

自净化样本已确认：同一 Action Window 中，前一个战法清除混乱后，后续战法与普通攻击立即恢复正常选敌。

---

## 3.10 Source Death Does Not Remove Or Disable Existing Confusion

混乱是：

```text
TARGET-HOSTED STANDALONE STATE
```

来源武将死亡后：

```yaml
Remove_Existing_Confusion: false
Disable_Existing_Confusion: false
Modify_Remaining_Turns: false
Modify_Source_Attribution: false
```

目标后续仍然正常执行该混乱，直到自然到期、被合法净化或目标死亡。

因此：

```text
Source Reference
= provenance / attribution
!= runtime alive dependency
```

来源死亡后日志仍可以保留原来源战法归因。

---

## 3.11 Target Death Uses Global Hard Termination

目标自身死亡时遵守项目全局基线：

```text
TARGET_DEATH
→ CLEAR_ALL_STATES
→ ABORT_REMAINING_STATE_RESOLUTION
→ ABORT_REMAINING_ACTION
→ REJECT_FUTURE_STATE_APPLICATION
```

因此死亡目标上的混乱实例被清空，后续不再参与结算。

---

# 4. L3 — BATTLE EVENT / JIT EVALUATION

## 4.1 Only Actual Target Selection Is The Evaluation Trigger

混乱的运行时检查节点不是：

```text
Turn Start
Action Start Snapshot
Skill Start
Skill Preparation Start
SkillContext Creation
```

而是：

```text
EACH ACTUAL TARGET SELECTION
```

冻结规则：

```yaml
Evaluation_Mode: JIT
Reads: actor.current_active_states
Snapshot: NONE
```

---

## 4.2 State Changes Before A Later Selection Are Immediately Visible

同一 Action Window 内允许：

```text
CONFUSION false → true
```

若随后才发生新的 Target Selection，则该选择立即受混乱影响。

同样：

```text
CONFUSION true → false
```

若混乱在后续 Target Selection 之前被净化，则该选择立即恢复正常阵营约束。

---

## 4.3 Already Selected Targets Are Not Retroactively Rewritten

一次目标已经选定后，之后才获得或失去混乱：

```text
不会追溯修改已经完成的 Target Selection
```

混乱只影响后续真正发生的新选择。

---

## 4.4 Confusion Does Not Create Extra Target Selections

冻结原则：

```text
No new TargetSelector call
→ CONFUSION does nothing
```

混乱不会仅因为状态存在就强迫一个已经绑定目标的效果重新选人。

---

## 4.5 Parent / Attack Target Inheritance Does Not Re-select

若一个后续效果的目标语义是直接继承父事件已经锁定的攻击目标，例如：

```text
TargetBindingMode = ATTACK_TARGET
```

则：

```text
target = parentAttack.actualTarget
```

此时：

```text
不调用新的 TargetSelector
不再次执行 CONFUSION
不重新随机目标
```

战报扫描中，混乱普通攻击后触发“对普通攻击目标/对目标”的单体突击效果：

```text
N = 67
后续目标 == 普攻目标：67 / 67
后续独立混乱执行日志：0
```

反之，如果后续效果自身明确定义一个新的独立 Selector，则该新 Selector 正常执行混乱 JIT。

该规则只冻结混乱对“是否存在新 Target Selection”的响应，不扩展定义具体战法本身的全部目标机制。

---

## 4.6 Prepared Skills Do Not Snapshot Confusion

准备型战法开始准备时：

```text
只建立准备 / channeling 状态
不选择目标
不锁定候选池
不快照 CONFUSION
```

正式发动结算时：

```text
TargetSelector.resolve(...)
→ JIT read current CONFUSION
```

已核验跨回合动态翻转样本：

```text
准备时无混乱 → 正式发动时有混乱：N=84
准备时有混乱 → 正式发动时混乱已解除：N=65
```

结果跟随**正式目标选择时的当前状态**，而不是准备时状态。

因此：

```text
CONFUSION NEVER SNAPSHOTS AT SKILL PREPARATION
```

---

# 5. L4 — INTERACTION / TARGET PIPELINE

本节只冻结已经研究确认的**混乱一侧运行规则**，不把其他状态顺带提升为完整机制合同。

## 5.1 Confusion vs Taunt

普通攻击目标选择阶段：

```text
if CONFUSION active:
    resolve original selector with Side Predicate suppressed
    skip TAUNT forced-target branch
else if TAUNT active:
    execute taunt forced-target logic
```

冻结关系：

```text
CONFUSION > TAUNT
```

已核验混乱与嘲讽重叠样本：

```text
N = 1,318
CONFUSION branch executed = 1,318
TAUNT branch executed = 0
```

该短路不取决于两状态施加先后顺序。

---

## 5.2 Confusion vs Provocation

需要进行技能目标选择时：

```text
if CONFUSION active:
    suppress Side Predicate
    execute original selector
    skip PROVOCATION forced-target branch
else if PROVOCATION active:
    execute provocation forced-target logic
```

冻结关系：

```text
CONFUSION > PROVOCATION
```

---

## 5.3 Confusion vs Pursuit

普通攻击目标选择阶段，混乱存在时：

```text
CONFUSION target-selection branch
→ PURSUIT target-lock branch not entered
→ PURSUIT success/failure probability check not executed
```

冻结关系：

```text
CONFUSION > PURSUIT
```

已核验重叠普通攻击样本中：

```text
Confused attacks = 41
Pursuit success logs = 0
Pursuit failure logs = 0
```

混乱消失后，Pursuit 分支恢复正常执行。

---

## 5.4 Confusion Does Not Dominate Later Post-Selection Redirection

禁止从以上三条外推：

```text
CONFUSION > EVERY TARGET MECHANIC
```

当前已经确认普通攻击目标管线至少需要区分：

```text
1. Target Selection Precedence
   CONFUSION
   ↓ if absent
   TAUNT
   ↓ if absent
   PURSUIT
   ↓
   NORMAL SELECTION

2. originalTarget determined

3. Post-selection Target Resolution
   GUARD / COVER
   ↓
   actualTarget

4. Target Lock
```

因此混乱负责决定 `originalTarget` 时，后续属于不同阶段的目标重定向仍可把它解析成另一个 `actualTarget`。

这是阶段边界，不是“混乱失效”。

---

# 6. Runtime Reference Algorithm

以下为规范实现骨架，表达冻结行为，不要求项目源码逐字采用同名类和字段。

```python
def resolve_targets(actor, selector, battle):
    candidates = selector.build_base_candidates(actor, battle)

    candidates = selector.apply_non_side_predicates(
        actor=actor,
        candidates=candidates,
        battle=battle,
    )

    if not actor.has_status(CONFUSION):
        candidates = selector.apply_side_predicate(
            actor=actor,
            candidates=candidates,
            battle=battle,
        )

    return selector.selection_strategy.select(
        candidates=candidates,
        count=selector.target_count,
        battle=battle,
    )
```

真实实现允许先后组织过滤器，但必须满足外部等价不变量：

```text
CONFUSION removes only the Side Predicate.
All other selector semantics remain unchanged.
```

JIT 入口：

```python
def on_actual_target_selection(actor, selector, battle):
    # must read current state container here
    confused_now = actor.has_status(CONFUSION)
    return selector.resolve(actor, battle, suppress_side=confused_now)
```

重复施加：

```python
def try_apply_confusion(target, new_instance, battle):
    if target.is_immune_to_control(CONFUSION):
        emit_confusion_immune(target)
        return False

    if target.get_status(CONFUSION) is not None:
        emit_same_or_stronger_exists(target, CONFUSION)
        return False

    target.active_states.add(new_instance)
    emit_confusion_applied(target)
    return True
```

生命周期：

```python
def on_owner_action_start(owner):
    confusion = owner.get_status(CONFUSION)
    if confusion is not None and confusion.remaining_turns <= 0:
        owner.remove_status(CONFUSION)
        emit_confusion_disappeared(owner)


def on_owner_action_window_end(owner):
    confusion = owner.get_status(CONFUSION)
    if confusion is not None:
        confusion.remaining_turns -= 1
```

净化：

```python
def purge_confusion(target):
    confusion = target.get_status(CONFUSION)
    if confusion is None:
        return False

    target.remove_status_instance(confusion)
    emit_confusion_disappeared(target)
    return True
```

---

# 7. Strong Invariants

实现必须满足以下不变量：

```text
I-01  同一目标同时最多存在一个 CONFUSION 实例。
I-02  只要旧实例尚未物理删除，新 CONFUSION 一律硬拒绝。
I-03  remainingTurns == 0 不等于实例已删除。
I-04  成功施加后立即对后续 Target Selection 可见。
I-05  成功净化后立即对后续 Target Selection 不可见。
I-06  来源死亡不删除、不禁用已存在 CONFUSION。
I-07  目标死亡执行全局状态硬清空。
I-08  每次真实 Target Selection 都 JIT 读取当前 CONFUSION。
I-09  混乱只删除 Side Predicate。
I-10  混乱不修改其他谓词、Target Count 或 Selection Strategy。
I-11  混乱不创造额外 Target Selection。
I-12  已锁定/继承的目标不会仅因混乱重新选取。
I-13  自然到期发生在 Owner Action Start expiration gate。
I-14  Action Window 即使因控制无法正常行动，仍消费持续时间。
I-15  准备阶段不快照混乱；正式选目标时才判定。
```

---

# 8. Question Registry Closure

| Question | Frozen Result |
|---|---|
| Q01 Target legality | 仅删除 Side Constraint；其他目标约束全部保留 |
| Q02 Evaluation timing | 每次真实 Target Selection JIT 判定；无快照 |
| Q03 × Taunt | CONFUSION 短路 Taunt forced-target branch |
| Q04 × Provocation | CONFUSION 短路 Provocation forced-target branch |
| Q05 × Pursuit | CONFUSION 短路 Pursuit target-lock / roll branch |
| Q06 Duration lifecycle | Owner Action Window 计时；Action Start 到期门；Window End 消耗 |
| Q07 Reapplication | 单实例；存在即 Hard Reject；不刷新/覆盖/延长 |
| Q08 Unable to act | 仍消费该 Owner Action Window 的持续时间 |
| Q09 Source death | 来源死亡不影响已存在混乱 |
| Q10 Purge timing | 成功净化立即物理删除；后续 JIT 立即恢复正常 |
| Q11 Insight gate | 状态施加准入门直接拒绝，不创建混乱实例 |
| Q12 Inherited target | 无新 Target Selection 则不重新执行混乱 |
| Q13 Random single | 扁平合法池一次等权抽取；无敌我两阶段随机 |
| Q14 Random multi | 原无放回抽样；无敌我配额；无重复目标 |
| Q15 Ordered/extreme selector | 删除阵营谓词后继续原排序/极值/身份规则 |
| Q16 Prepared skill | 准备时不锁定；正式目标选择时 JIT 判定 |

全部核心问题已关闭。

---

# 9. Evidence Boundary

本合同的核心结论来自：

```text
U  — 项目所有者明确确认的游戏规则
BR — 当前重新扫描、统计和逐例核验的战报行为证据
GB — 已冻结的项目全局基线（例如 TARGET_DEATH）
```

本合同不把以下内容升级为混乱规则：

```text
具体来源战法为什么施加混乱
具体来源战法的发动概率
具体来源战法提供多少基础持续回合
其他控制状态是否拥有同样的重施策略
其他控制状态是否同样不依赖来源存活
基础 TargetSelector 的 RNG seed / random stream 实现
基础 TargetSelector 在属性完全相等时的 tie-break 细节
```

其中 RNG 流与 tie-break 属于基础目标选择器本体；混乱的冻结要求只是“完全继承原 Selector 行为”，因此不构成混乱机制的实现阻塞项。

---

# 10. Freeze Decision

```text
BLOCKER = 0
MAJOR = 0
IMPLEMENTATION-BLOCKING UNRESOLVED = 0
```

因此：

```text
690103 CONFUSION / 混乱
MECHANISM STATUS = FROZEN
```

后续只有在出现能够直接反驳本合同外部行为的新增高质量证据时，才允许重新打开本合同。
