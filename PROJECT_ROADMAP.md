# 三国志战略版战斗模拟器 V2 · 项目现状与长期路线图

> 本文是项目级路线图，不替代各阶段的 `STAGE*.md` 施工指南。
>
> 当前状态快照基于 `main` 提交 `be171664ac85fcdf8d3077fb01a1ed285a8b9e7b`（2026-09-04）。后续阶段编号与内容属于规划，必须在进入对应阶段前重新研究、写正式施工文档并审计，不能把本路线图当成不可修改的实现细节。

---

# 1. 项目最终目标

本项目要构建的不是“几个战法能跑”的脚本，而是一套可持续扩展、可复现、可审计的《三国志战略版》战斗模拟系统。

长期目标架构：

```text
Game / Skill Data
        ↓
SkillDefinition
        ↓
SkillRuntime
        ↓
Effect
        ↓
EffectExecutor / Rule Hooks
        ↓
BattleSystem
        │
        ├─ TargetSystem
        ├─ AttributeSystem
        ├─ ActionOrderSystem
        ├─ ActionSystem
        ├─ DamageSystem
        ├─ RecoverySystem
        ├─ TroopSystem
        ├─ VictorySystem
        └─ Future Rule Systems
        ↓
BattleState / Modifier Runtime
        ↓
BattleEngine
        ↓
EventBus
        ↓
BattleReport / Replay / Validation
```

项目长期坚持的核心原则：

> **具体战法不直接执行战斗底层机制。战法只表达“希望发生什么”；BattleSystem 决定“具体如何发生”。**

因此后续任何阶段都不应出现：

```python
if skill.name == "某个具体战法":
    ...
```

也不应让具体战法直接：

```text
修改 troops
修改最终属性
直接写 StateRegistry
自己选目标
自己调用 Python random
```

---

# 2. 当前项目已经做到什么程度

## 2.1 当前总体状态

```text
基础运行模型            ✅ 已建立
Stage 2 BattleSystem    ✅ 已封版
Stage 3 BattleState     ✅ 基础设施已完成并稳定
Stage 4 官方状态接入     ✅ 功能施工完成
Stage 4 最终封版审计     ⏳ 下一步
Stage 5+                ⏳ 尚未开始
```

当前 `main` 最新代码已经通过：

```text
pytest -q
→ 80 passed

python demo.py
→ success

GitHub Actions
→ success
```

因此项目已经从“基础战斗循环”进入了“可以开始搭建技能与效果表达层”的位置，但 Stage 4 在进入 Stage 5 前仍应完成一次正式封版审计。

---

# 3. 已完成基础架构

## 3.1 BattleEngine / BattleContext

当前已经具备完整基础战斗推进能力：

```text
PRE_BATTLE
ROUND_START
ACTION_ORDER
UNIT_ACTION_START
UNIT_ACTION
UNIT_ACTION_END
ROUND_END
BATTLE_END
```

`BattleEngine` 只负责：

```text
推进阶段
推进回合
调用 BattleSystem
调用状态生命周期节点
检查胜负
发布流程事实
```

它不应该，也目前没有承担具体状态和具体战法规则。

---

## 3.2 Stage 2：BattleSystem 基础层

Stage 2 已建立并冻结：

```text
ActionOrderSystem
ActionSystem
NormalAttackSystem
TargetSystem
AttributeSystem
DamageSystem
TroopSystem
VictorySystem
RandomSystem
EventBus
```

以及伤害请求模型：

```text
DamageRequest
DamageResult
DamageType
DamageSourceType
```

基础兵刃与谋略伤害已经统一接入：

```text
DamageRequest
    ↓
DamageSystem.calculate()
    ↓
WeaponBaseDamageFormula
或
StrategyBaseDamageFormula
    ↓
coefficient
    ↓
final_damage
    ↓
TroopSystem
```

Stage 2 已冻结的重要边界：

```text
TargetSystem    = 目标选择入口
AttributeSystem = 最终属性入口
DamageSystem    = 理论伤害入口
TroopSystem     = 唯一兵力修改入口
VictorySystem   = 胜负判定入口
RandomSystem    = 唯一战斗 RNG 入口
BattleEngine    = 通用流程推进器
```

阵容已经支持每队 1～3 名武将，并正式区分：

```text
主将
第一副将
第二副将
```

主将兵力归零会立即结束战斗，即使副将仍然存活。

---

# 4. Stage 3：BattleState 基础设施

Stage 3 已完成：

```text
StateDefinition
StateInstance
StateRegistry
StateLifecycleSystem
BattleContext.states
```

以及结构化状态事件：

```text
STATE_APPLIED
STATE_REMOVED
STATE_EXPIRED
```

当前 State 层解决的是：

```text
状态是什么
状态属于谁
状态由谁施加
来自哪个战法
何时施加
何时过期
是否仍然存在
```

Stage 3 的关键架构原则已经确立：

```text
State = 持续存在的战斗事实
BattleSystem = 解释该事实意味着什么
```

因此不会给 `UnitRuntime` 增加：

```python
is_stunned
is_disarmed
has_first_strike
```

之类的具体状态 bool。

状态实例编号也保持确定性，不使用 UUID 或随机数。

---

# 5. Stage 4：官方状态目录与代表状态验证

## 5.1 官方状态全集基线

当前官方研究资料已经确认：

```text
46 个官方战斗词条
-
6 个分类 / 机制词条
=
40 个具体 BattleState
```

40 个状态官方一级分类：

```text
持续性状态：8
功能性状态：17
控制状态：11
其他：4
总计：40
```

项目已建立：

```text
OfficialStateCategory
OfficialStateId
OfficialStateEntry
OFFICIAL_STATE_CATALOG
register_official_state_definitions()
```

官方中文名称、Hint ID、分类和官方原文与工程 `state_id` 分离保存。

官方研究基线位于：

```text
research/official_state_catalog_v1/
```

其中官方接口原文与项目补充确认规则保持分层，不互相伪装。

---

## 5.2 Stage 4 已实现的 5 个代表状态

当前已经真正接入 BattleSystem 的状态只有 5 个：

```text
first_strike / 先攻
ambush        / 遇袭
disarm        / 缴械
stun          / 震慑
weakness      / 虚弱
```

它们用于验证不同 BattleSystem 能根据 StateRegistry 改变规则：

```text
先攻 / 遇袭
→ ActionOrderSystem

缴械
→ NormalAttackSystem

震慑
→ ActionSystem

虚弱
→ DamageSystem
```

这证明 Stage 3 的状态基础设施已经不仅仅“能存状态”，而是真的可以影响战斗规则。

---

## 5.3 先攻 / 遇袭当前规则

当前工程规则：

```text
先攻 = +1
普通 = 0
遇袭 = -1
```

同一武将同时拥有：

```text
先攻 + 遇袭
```

按项目补充确认规则：

```text
+1 + (-1) = 0
```

因此进入普通行动层，再按有效速度排序。

只有：

```text
相同 priority tier
+
相同 effective speed
```

才由 `RandomSystem.shuffle()` 裁决顺序。

该组合规则记录在：

```text
PROJECT_STATE_INTERACTIONS_V1.md
```

它是项目补充确认规则，不反向改写官方 Hint 原文。

---

## 5.4 Stage 4 其他已完成能力

已增加：

```text
ACTION_BLOCKED
DAMAGE_PREVENTED
```

虚弱已经让 `DamageResult` 正式支持“明确被阻止时合法 0 伤害”：

```text
base_damage = 0
scaled_damage = 0
final_damage = 0
prevented = True
```

同时保留普通非阻止伤害的原有最低伤害语义。

缴械、震慑、虚弱也已经分别验证了无意义 RNG 不被消耗。

---

# 6. 当前还没有实现什么

必须明确：

> **现在并没有实现全部 40 个状态。**

Stage 4 只实现 5 个代表状态。

剩余 35 个已经全部写入：

```text
research/official_state_catalog_v1/STATE_SYSTEM_MAPPING_V1.md
```

并分配了未来系统归属。

当前也尚未正式建立：

```text
Effect
EffectExecutor
SkillDefinition
SkillRuntime
完整 SkillSystem
TriggerSystem / RuleHookSystem
RecoverySystem
HitResolution
完整 Damage Modifier Pipeline
状态参数运行时模型
完整装备系统
BattleReport
Replay
真实战法目录与运行时
```

这些正是后续阶段要解决的内容。

---

# 7. 现在立刻应该做什么

## 下一步：Stage 4 最终封版审计

在写 Stage 5 代码之前，先完成 Stage 4 最终审计。

审计重点：

```text
40 状态目录完整性
40 条官方原文不可漂移
先攻 + 遇袭归零规则
5 个代表状态系统边界
RNG 消耗
ACTION_BLOCKED / DAMAGE_PREVENTED
BattleEngine 红线
StateLifecycleSystem 红线
UnitRuntime 无具体状态 bool
其余 35 状态映射完整性
pytest / demo / GitHub Actions
```

如果审计只发现加固项：

```text
审计
→ 修复 / 加固
→ 再审计
→ Stage 4 FROZEN
```

如果发现 MAJOR / BLOCKER，则 Stage 4 不应直接进入 Stage 5。

---

# 8. 后续阶段统一工作方法

从现在开始，每个阶段都建议严格执行：

```text
研究资料
    ↓
确定证据边界
    ↓
写 STAGEX.md
    ↓
设计审计
    ↓
编码实现
    ↓
pytest + demo
    ↓
GitHub Actions
    ↓
最终审计
    ↓
修复
    ↓
再次审计
    ↓
FROZEN
```

不要跳过“设计”和“封版审计”直接连续堆功能。

---

# 9. Stage 5 规划：Effect 与状态运行参数合同

> Stage 5 是下一阶段的首要规划，但在 Stage 4 封版前不要开始编码。

## 9.1 目标

建立：

```text
Effect
    ↓
EffectExecutor
    ↓
BattleSystem
```

让上层只表达“希望发生什么”。

第一批候选 Effect：

```text
DamageEffect
ApplyStateEffect
RemoveStateEffect
RecoverEffect
```

后续再扩展：

```text
ModifyAttributeEffect
ModifyDamageEffect
```

是否在 Stage 5 第一批加入，需要在 `stages/stage5/STAGE5.md` 中重新审计，不应仅凭路线图直接实现。

## 9.2 Stage 5 的关键难点：状态运行参数

当前 `StateInstance` 主要保存生命周期与来源信息，并没有完整表达：

```text
概率
倍率
百分比
次数
层数
伤害系数
恢复系数
关联目标
共享组
```

但真实状态会需要这些参数，例如：

```text
规避 → 概率
群攻 → 伤害比例
反击 → 伤害系数
倒戈 / 攻心 → 恢复比例
铁索连环 → 反馈比例
看破 → 穿透比例
会心 / 奇谋 → 概率
持续伤害 → 系数 + 触发时机 + 来源信息
```

因此 Stage 5 必须先设计**类型安全、不可变、可审计的状态运行参数合同**。

原则：

```text
State 仍然只是事实
参数可以随 StateInstance 存在
行为不能塞进 State 对象
```

不要未经设计就简单加入：

```python
payload: dict[str, Any]
```

作为万能逃生门。

---

# 10. Stage 6 规划：SkillDefinition / SkillRuntime 基础链

Stage 6 建议完成：

```text
SkillDefinition
      ↓
SkillRuntime
      ↓
Skill activation / resolution
      ↓
Effect
```

目标不是立刻录入成百上千战法，而是证明：

> 一个战法运行时只产生 Effect，不直接操作 BattleSystem 内部。

本阶段需要确定：

```text
战法静态定义
战法等级参数
携带者
来源
是否有效
运行时状态
发动 / 触发入口
Effect 生成
```

具体战法类型和触发语义必须以项目后续官方 / 客户端研究数据为准，不应在路线图中提前凭记忆冻结。

Stage 6 至少需要一个“测试用技能定义”证明完整链路，但不应通过具体战法名称硬编码规则。

---

# 11. Stage 7 规划：Trigger / Timing / Recovery / 持续效果

Stage 7 建议建立统一规则触发节点，而不是让 `EventBus` 变成规则引擎。

推荐方向：

```text
BattleEngine / BattleSystem
        ↓
明确 Rule Hook
        ↓
TriggerSystem
        ↓
产生 Effect
        ↓
EffectExecutor
```

可能需要的规则节点：

```text
ROUND_START
ROUND_END
BEFORE_ACTION
AFTER_ACTION
BEFORE_DAMAGE
AFTER_DAMAGE
AFTER_NORMAL_ATTACK
BEFORE_RECOVERY
AFTER_RECOVERY
```

最终节点名称以 Stage 7 设计为准。

EventBus 继续只记录已经发生的事实，不反向决定规则。

## Stage 7 预计实现状态

持续伤害 / 周期触发：

```text
灼烧
水攻
中毒
溃逃
沙暴
叛逃
```

恢复类：

```text
急救
休整
禁疗
倒戈
攻心
```

因此需要建立：

```text
RecoverySystem
```

RecoverySystem 负责恢复政策和状态规则，最终仍由 `TroopSystem.restore()` 修改实际兵力。

---

# 12. Stage 8 规划：通用 Modifier、命中与伤害裁决链

实际战法不仅有“特殊状态”，还大量涉及：

```text
属性提高 / 降低
造成伤害提高 / 降低
受到伤害提高 / 降低
概率裁决
防御穿透
伤害免疫
```

因此 Stage 8 建议建立正式、可排序的 Modifier Pipeline，而不是不断往 `DamageSystem` 增加独立 `if`。

需要研究并冻结的层次包括：

```text
Attribute Modifier
Hit Resolution
Damage Prevention
Defense / Intelligence Ignore
Damage Increase / Reduction
Critical / Strategy Critical
Damage Reduction Pierce
Final Damage
```

具体顺序必须由研究和实测决定，路线图不提前声称官方结算顺序。

## Stage 8 预计实现状态

```text
规避
抵御
必中
破阵
警戒
会心
奇谋
看破
```

其中必须重点研究状态覆盖关系，例如：

```text
必中
→ 无视规避及抵御
```

这些关系不能靠调用顺序碰巧得到正确答案，应写成明确裁决政策。

---

# 13. Stage 9 规划：目标重定向、追加行动与反应式机制

Stage 9 解决“一个行为会产生更多行为”的问题。

需要防止：

```text
递归触发失控
反击套反击
伤害传播无限循环
追加行动错误重复
多目标顺序不确定
```

建议建立明确的：

```text
Action Repeat Policy
Reaction / Trigger Queue
Target Redirect
Damage Redirect / Split
Recursion Guard
Deterministic Resolution Order
```

## Stage 9 预计实现状态

```text
连击
群攻
反击
分摊
分担
铁索连环
援护
混乱
嘲讽
```

这些状态会重点扩展：

```text
ActionSystem
NormalAttackSystem
TargetSystem
DamageSystem
TriggerSystem
```

但仍不能让状态对象自己执行行为。

---

# 14. Stage 10 规划：状态施加政策、高级控制、技能失效与装备

这一阶段处理依赖 SkillRuntime 或其他子系统的复杂状态。

## Stage 10 预计实现状态

```text
洞察
计穷
伪报
挑拨
破坏
捕获
威慑
```

关键能力包括：

```text
StateApplicationPolicy
Control Immunity
Skill Enable / Disable Policy
Skill Target Forcing
Equipment Runtime
Composite Control
```

典型交互：

```text
洞察
→ 免疫控制状态

伪报
→ 无视洞察
→ 使指挥 / 被动战法失效

捕获
→ 禁行动
→ 禁造成伤害
→ 禁疗
→ 技能失效
→ 友方不可选中
```

这些属于跨系统规则，必须在完整基础设施存在后处理，不适合提前塞进 Stage 4。

---

# 15. 35 个未实现状态的长期落点

按当前规划：

```text
Stage 7：11 个
灼烧、水攻、中毒、溃逃、沙暴、叛逃、急救、休整、禁疗、倒戈、攻心

Stage 8：8 个
规避、抵御、必中、破阵、警戒、会心、奇谋、看破

Stage 9：9 个
连击、群攻、反击、分摊、分担、铁索连环、援护、混乱、嘲讽

Stage 10：7 个
洞察、计穷、伪报、挑拨、破坏、捕获、威慑
```

总计：

```text
11 + 8 + 9 + 7 = 35
```

这只是当前工程分组计划。

进入对应阶段前，如果研究发现某个状态依赖其他基础设施，应调整阶段归属，而不是为了满足路线图编号强行实现。

---

# 16. Stage 11 规划：真实战法目录与数据驱动运行

当：

```text
Effect
SkillRuntime
Trigger
State
Modifier
Target
Damage
Recovery
```

都足够稳定后，才适合大规模接入真实战法。

Stage 11 的目标：

```text
官方 / 客户端研究数据
        ↓
SkillDefinition Catalog
        ↓
Level Parameter Data
        ↓
SkillRuntime
        ↓
Effects
```

要求：

```text
战法数据与引擎代码分离
具体战法不写进核心 BattleSystem
同类战法复用 Effect / Trigger / State 机制
未知参数保留证据等级
```

建议先选少量代表战法覆盖不同机制，再逐步扩展，不进行“几百个战法一次性全部录入”的冒险活动。

---

# 17. Stage 12 规划：BattleReport / Replay / 可解释性

EventBus 当前已经保存结构化事实。

后续应正式建立：

```text
BattleReport
BattleReplay
Debug Trace
```

目标是让一次战斗不仅给出输赢，还能解释：

```text
为什么谁先行动
哪个状态阻止了什么
一次伤害如何得到最终值
哪个 Effect 来自哪个战法
状态何时加入 / 过期
哪个随机裁决发生过
为什么主将死亡后结束
```

同一 seed 的战斗应能够稳定重放和审计。

---

# 18. Stage 13 规划：准确性验证与规则校准

当机制基本齐全后，需要从“架构正确”转向“游戏规则准确”。

建立：

```text
Golden Battle Cases
Regression Fixtures
Research Evidence Matrix
Formula Calibration
State Interaction Matrix
Skill Interaction Matrix
```

每个高价值规则应尽量有：

```text
官方原文
或
可重复实测
或
明确标记的逆向候选模型
```

不得把候选模型写成“官方公式”。

对未来客户端版本变化，应版本化研究数据，而不是静默覆盖旧证据。

---

# 19. Stage 14 规划：模拟器产品化

引擎规则稳定后再做外层能力：

```text
BattleConfig / BattleFactory
Data Loader
CLI
API
批量模拟
统计结果
性能优化
并行模拟
缓存
场景导入 / 导出
```

最终可支持：

```text
单场可解释模拟
固定 seed 重放
大量 Monte Carlo 模拟
阵容 / 战法方案比较
战报分析
规则验证
```

UI 如果需要，应建立在稳定 API / Report 层之上，而不是直接耦合 BattleSystem。

---

# 20. 长期架构红线

无论做到哪个阶段，以下原则不能为了赶进度而牺牲。

## 20.1 战法不得侵入底层

```text
Skill
→ Effect
→ BattleSystem
```

不是：

```text
Skill
→ 直接扣兵 / 改属性 / 改目标
```

## 20.2 EventBus 不是规则引擎

```text
BattleSystem / TriggerSystem
→ 决定规则

EventBus
→ 记录事实
```

## 20.3 RandomSystem 仍是唯一 RNG

```text
same configuration + same seed
= same result
```

## 20.4 State 不执行行为

```text
State = fact + runtime parameters
BattleSystem = behavior
```

## 20.5 TroopSystem 仍是兵力写入口

无论是：

```text
伤害
治疗
急救
休整
倒戈
攻心
```

最终实际兵力修改都必须汇入统一入口。

## 20.6 未知规则不猜

如果官方资料 / 实测没有给出：

```text
顺序
覆盖
叠加
刷新
优先级
```

必须显式记录未解析项，直到取得证据或项目方明确补充规则。

---

# 21. 项目当前成熟度判断

现在的项目还不是“完整三战模拟器”，但已经完成了最危险的一部分基础工作：

```text
战斗流程边界
目标边界
属性边界
伤害边界
兵力边界
胜负边界
随机边界
状态生命周期边界
状态影响 BattleSystem 的验证
```

因此当前阶段可以概括为：

> **底层战斗内核已经成型，状态系统已经打通，下一大里程碑是建立 Effect / SkillRuntime，使真实战法可以在不破坏底层架构的前提下进入模拟器。**

如果把完整项目粗略分成：

```text
A. 战斗内核
B. 状态 / Effect / 技能规则
C. 全量机制与真实战法
D. 战报、验证与产品化
```

那么目前大致处于：

```text
A：基本完成
B：状态基础已完成，Effect / SkillRuntime 尚未开始
C：大部分尚未开始
D：基础 EventBus 已有，正式 Report / Validation 尚未开始
```

不建议用一个虚假的单一百分比描述整个项目，因为“80 个测试”并不等于“80% 的游戏规则”。当前最有价值的事实是：**核心架构已经稳定到可以承载后续复杂规则。**

---

# 22. 最近三个明确里程碑

从当前状态开始，优先级固定为：

```text
里程碑 1
Stage 4 最终审计
→ 修复 / 加固
→ Stage 4 FROZEN

里程碑 2
研究并编写 stages/stage5/STAGE5.md
→ Effect
→ 状态运行参数合同
→ EffectExecutor

里程碑 3
Stage 6 SkillDefinition / SkillRuntime
→ 打通 Skill → Effect → BattleSystem
```

只有这三个里程碑稳定后，才开始批量实现剩余 35 状态和真实战法。

---

# 23. 文档维护规则

本文件是项目级总路线图。

以后每完成一个 Stage：

1. 更新“当前项目已经做到什么程度”。
2. 把该 Stage 标记为 `FROZEN` 或记录未解决问题。
3. 更新最新测试 / CI 基线。
4. 如果后续研究改变阶段划分，更新路线图并说明原因。
5. 不修改历史官方研究原文来配合当前代码。

详细施工规则仍以对应：

```text
stages/stage3/STAGE3.md
stages/stage4/STAGE4.md
未来 stages/stage5/STAGE5.md
未来 stages/stage6/STAGE6.md
...
```

为准。

---

# 24. 当前结论

当前项目不是要继续扩充 Stage 4 状态数量。

正确路线是：

```text
Stage 4 最终封版审计
        ↓
Stage 4 FROZEN
        ↓
Stage 5 Effect + 状态运行参数
        ↓
Stage 6 SkillDefinition / SkillRuntime
        ↓
Stage 7 Trigger / Recovery / 持续状态
        ↓
Stage 8 Modifier / Hit / Damage States
        ↓
Stage 9 Redirect / Reaction / Action States
        ↓
Stage 10 Advanced Control / Skill Disable / Equipment
        ↓
Stage 11 Real Skill Catalog
        ↓
Stage 12 BattleReport / Replay
        ↓
Stage 13 Accuracy Validation
        ↓
Stage 14 Productization
```

这条路线的目的不是让阶段编号看起来整齐，而是保证每一类复杂规则都有自己的基础设施，避免最终把所有游戏机制都堆进 `DamageSystem`、`BattleEngine` 或具体战法文件里。