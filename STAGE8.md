# 三国志战略版战斗模拟器 V2 · Stage 8 Damage Rule / Hit Resolution / Modifier Pipeline 实施规范

> 本文是 Stage 8 的第二版修订规划草案，已吸收第一轮独立设计审计意见，用于第二轮独立设计复审；当前仍不是 DESIGN FROZEN。
>
> Stage 8 建立在 Stage 7 已经 FROZEN 的 `main` 基线上。本文不是施工结果，也不是 FINAL AUDIT，更不是允许直接绕过设计审计开始编码的施工 Prompt。
>
> Stage 8 的核心目标不是“再实现一批状态”，而是冻结一条可组合、可追踪、可测试的命中 / 伤害裁决管线，使后续规避、抵御、必中、破阵、会心、奇谋、警戒、看破以及叛逃的“无视防御”不需要继续向 `DamageSystem` 堆叠零散 `if`。
>
> 任何真实官方状态进入 production mapping 前，必须经过 Stage 8 Evidence Gate。基础设施可以先用 synthetic state / synthetic modifier 验证，UNKNOWN 不得用工程猜测伪装成官方规则。

---

# 0. 当前基线

Stage 8 第一版规划基线：

```text
8f51a9ebd06038ec163e858164bc26e8a7637ed2
docs(stage7): record frozen status
```

Stage 7 正式实现与最终审计进入 `main` 的 merge commit：

```text
199585c25b7db46d5c008fab46ab21fb7957ebb0
Stage 7: Trigger/Recovery final merge
```

Stage 7 最终独立审计：

```text
BLOCKER   = 0
MAJOR     = 0
MINOR     = 0
HARDENING = 1 accepted
```

Stage 7 main exact-head 验证：

```text
pytest -q
→ 234 passed

python demo.py
→ success

GitHub Actions
→ success
```

当前正式状态：

```text
Stage 1 基础运行模型       回归稳定
Stage 2 BattleSystem      FROZEN
Stage 3 BattleState       稳定
Stage 4 官方状态接入       FROZEN
Stage 5 Effect            FROZEN
Stage 6 Skill Runtime     FROZEN
Stage 7 Trigger/Recovery  FROZEN
Stage 8                   设计修订 v2 / 待第二轮独立设计复审
```

Stage 7 已冻结的关键链路：

```text
RuleHook
→ TriggerSystem
→ ordered Effect(s)
→ RuleHookSystem
→ EffectExecutor
→ BattleSystem
```

以及：

```text
RecoverEffect
→ RecoverySystem
→ TroopSystem.restore
```

Stage 8 不得借机重写这些冻结边界。

## 0.1 Stage 8 v1 与第一轮独立设计审计记录

Stage 8 v1 设计提交：

```text
98b23726ab1d28e4c378e998314a4abe1a39e5b7
docs(stage8): add initial damage pipeline design draft
```

第一轮独立设计审计结论：

```text
BLOCKER   = 0
MAJOR     = 7
MINOR     = 6
HARDENING = 4

VERDICT
= REVISE BEFORE DESIGN FREEZE
```

本 v2 必须关闭的核心问题：

```text
M-01  StateInstance → typed rule contribution discovery / mapping contract
M-02  DamageFormulaPolicy → frozen base formula 的唯一 typed 输入接口
M-03  DamageModifierContribution 的 operation / kind 模型
M-04  runtime RNG / StateRegistry 唯一来源 + DamageSystem 构造兼容
M-05  damage source 与 modifier/state provenance 术语分离
M-06  Stage 8 calculation systems 的 EventBus 发布禁令
M-07  Stage 8 Evidence Matrix 正式 artifact 落地
```

本 v2 同时吸收以下设计硬化：

```text
PipelineTrace short-circuit 语义
多 contributor trace 预留
删除无正式消费者的 FINAL modifier phase
finite / NaN / inf / bool 数值边界
死亡 / 0 兵力 DamageRequest 前置条件
architecture test 与 behavior test 分工
最小 probability helper
```

本轮修订只冻结“怎样安全实现”的工程合同；凡是仍缺官方 / 战报 / 实测证据的真实状态行为，继续 `DEFER`，不得借设计修订偷偷升级为官方结论。

---

# 1. Stage 8 为什么现在需要做

当前 `DamageSystem.calculate()` 已经能够完成：

```text
DamageRequest
→ 兵刃 / 谋略基础伤害
→ coefficient
→ final_damage
```

并且 Stage 4 已经用 `weakness / 虚弱` 证明状态可以阻止伤害。

但当前体系仍缺少正式、可组合的：

```text
伤害前阻止规则
命中 / 回避裁决
抵御 / 免疫裁决
必中覆盖关系
无视统率 / 智力
会心 / 奇谋
造成伤害提高 / 降低
受到伤害提高 / 降低
单次伤害减免
受到伤害降低穿透
伤害修正执行顺序
伤害修正来源追踪
伤害修正审计 trace
```

如果继续直接在 `DamageSystem` 增加：

```python
if evasion:
    ...
if barrier:
    ...
if sure_hit:
    ...
if defense_pierce:
    ...
if critical:
    ...
if vigilance:
    ...
```

最终会形成状态名驱动的单体巨型函数。

Stage 8 要解决的不是某一个状态，而是：

> **一次 DamageRequest 在真正扣兵之前，究竟要经过哪些明确、单向、可审计的规则层。**

---

# 2. Stage 8 核心目标

Stage 8 v1 要冻结以下主链：

```text
DamageRequest
    ↓
DamagePreventionSystem
    ↓
HitResolutionSystem
    ↓
DamageFormulaPolicySystem
    ↓
Frozen Base Damage Formula
    ↓
coefficient scaling
    ↓
DamageModifierSystem
    ↓
finalization
    ↓
DamageResult
    ↓
DamageResolutionSystem
    ↓
TroopSystem.apply_damage
```

核心要求：

```text
DamageSystem.calculate()
= 理论伤害唯一入口

DamageResolutionSystem
= 理论伤害 → 实际扣兵 → 事实事件 的唯一协调层

TroopSystem
= 唯一实际兵力写入口

RandomSystem / BattleContext.random
= 唯一战斗 RNG

State
= 战斗事实与参数
≠ 可执行行为对象
```

Stage 8 成功的标志不是“8 个状态全部点亮”，而是：

```text
Prevention
Hit
Formula Policy
Modifier
Finalization
```

五个职责已经有清晰边界，并且任何正式状态必须通过 Evidence Gate 才能挂载。

---

# 3. Stage 8 最高架构原则

必须保持：

```text
BattleEngine
= 流程推进器
≠ Damage Rule Engine

EventBus
= 已发生事实记录 / 分发
≠ 伤害规则触发器

DamageSystem
= 理论伤害管线协调入口

DamagePreventionSystem
= “本次伤害是否允许继续”裁决

HitResolutionSystem
= 命中 / 回避 / 抵御 / 必中覆盖裁决

DamageFormulaPolicySystem
= 基础公式输入政策，例如是否忽略目标防御属性

DamageModifierSystem
= 基础伤害与 coefficient 之后的伤害修正

DamageResolutionSystem
= 理论结果 → 实际兵力变化 → Event

TroopSystem
= 唯一兵力修改入口
```

严格禁止：

```text
BattleEngine 判断具体 Stage 8 state_id
EffectExecutor 判断 evasion / critical / vigilance
EventBus.subscribe(...) 反向执行伤害规则
StateInstance.execute()
StateRuntimeParams.execute()
HitResolutionSystem 直接扣兵
DamageModifierSystem 直接扣兵
DamageModifierSystem 发布胜负
DamagePreventionSystem import random
DamageModifierSystem import random
任何新系统直接调用 Python random
任何具体战法名称进入 BattleSystem 核心判断
建立第二套 DamageRequest / Troop mutation 路径
```

---

# 4. Stage 8 证据体系

继续沿用：

```text
A = 当前官方接口 / 官方文本
B = 项目方明确确认
C = 战报、实测、逆向、可重复测试证据
D = 工程设计决定
E = UNKNOWN / NEEDS_RESEARCH
```

权威优先级：

```text
官方接口 / 官方文本
> 项目已确认规则
> 高质量战报与机制研究
> 工程设计决定
> 推测
```

D 可以冻结模拟器工程行为，但不得写成官方规则。

---

# 5. Stage 8 与状态机制研究仓库的关系

真实状态机制研究优先进入独立仓库：

```text
lxy2005051020-commits/sgs-state-mechanics-research
```

Stage 8 production mapping 的正式 Evidence Matrix 固定存放：

```text
research/stage8_evidence_matrix/STAGE8_EVIDENCE_MATRIX.md
```

Matrix 中引用外部研究时必须记录：

```text
research repository
commit SHA
file path
evidence level
conclusion
remaining unknowns
```

禁止只写：

```text
“之前聊过”
“印象里是这样”
“游戏一般都是这样”
```

人类记忆已经给软件工程制造过足够多的惊喜，不需要再拿它当数据库。

---

# 6. Stage 8 正式范围

Stage 8 v1 正式建设：

```text
DamagePreventionSystem
DamagePreventionReason
typed prevention result

HitResolutionSystem
typed HitResolutionResult
命中 / 回避 / 抵御 / 必中基础设施

DamageFormulaPolicySystem
DamageDefensePolicy
无视目标相关防御属性的受控公式输入路径

DamageModifierSystem
typed DamageModifier contribution
typed modifier phase
deterministic modifier ordering
modifier execution trace

critical / strategy critical 基础设施
incoming / outgoing damage modifier 基础设施
damage reduction pierce 基础设施

DamageResult Stage 8 trace 扩展
Stage 8 event payload 扩展
BattleSystems 正式组合

weakness 既有行为迁移到正式 prevention 层
基础伤害公式回归保护
Stage 8 Evidence Matrix
Stage 8 synthetic tests
```

候选官方状态：

```text
evasion / 规避
barrier / 抵御
sure_hit / 必中
defense_pierce / 破阵
vigilance / 警戒
critical / 会心
strategy_critical / 奇谋
damage_reduction_pierce / 看破
```

Stage 7 已明确转交 Stage 8 的候选：

```text
rebellion / 叛逃
```

但“候选”不等于“必须实现”。

---

# 7. Stage 8 不把完整 Attribute Modifier 大系统强塞进 v1

当前 `AttributeSystem` 已经是最终属性读取入口，并保留：

```text
AttributeModifierProvider
```

Stage 8 v1 冻结：

```text
伤害公式正常读取属性
→ 继续经过 AttributeSystem
```

Stage 8 只为：

```text
ignore relevant target defense / intelligence
```

建立**伤害查询上下文中的公式政策**。

本阶段不要求一次完成：

```text
所有属性提高 / 降低
所有属性百分比叠加
所有属性临时层数
所有属性覆盖 / 取最高
```

如果独立设计审计证明通用 `AttributeModifierSystem` 是 Stage 8 必要前置，可以在审计修订版加入；否则不为“路线图里出现过 Attribute Modifier”而无消费者地制造一套过度抽象。

无论是否新增正式 AttributeModifierSystem，都必须保持：

```text
AttributeSystem
= 最终属性读取唯一入口
```

---

# 8. DamageSystem 的 Stage 8 职责

Stage 8 后 `DamageSystem.calculate(context, request)` 继续是统一理论伤害入口。

它负责协调：

```text
1. source / target 解析
2. DamagePreventionSystem
3. HitResolutionSystem
4. DamageFormulaPolicySystem
5. 基础伤害公式
6. coefficient scaling
7. DamageModifierSystem
8. finalization
9. DamageResult
```

它不得负责：

```text
实际扣兵
Victory
Reaction Queue
After Damage Trigger
恢复
目标重定向
状态施加 / 消耗
```

特别是：

```text
DamageSystem
≠ Stage 9 Reaction System
```

## 8.1 DamageRequest 参与者前置条件

项目已确认的战斗生命周期规则：

```text
武将死亡后：
→ 其自身状态清空
→ 后续不再参与战斗结算
```

因此 Stage 8 把以下内容冻结为 Damage Pipeline 的 API 前置条件，而不是某个“伤害被阻止”状态：

```text
source 必须存在且 troops > 0
target 必须存在且 troops > 0
```

canonical runtime 应在更上游保证不会为已死亡参与者生成新的 `DamageRequest`。

如果测试、调试或外部调用绕过 canonical runtime，直接向 `DamageSystem.calculate()` 传入已死亡 source / target，则 Stage 8 v1 规定：

```text
在 DamagePrevention / Hit / Formula / Modifier 之前拒绝该非法请求
→ 抛出明确的 domain-level InvalidDamageParticipantError（或等价专用异常）
→ 不消耗 RNG
→ 不进入基础伤害公式
→ 不产生 DAMAGE_PREVENTED / DAMAGE_DEALT
→ 不发生 troop mutation
```

原因：

```text
“参与者已死亡”
≠ weakness / barrier / evasion 等战斗裁决
```

不得为了方便把 dead participant 伪装成 `prevented=True`，否则 EventBus 会记录一场实际上不应发生的伤害裁决。

`0 troops` 在本项目中视为已死亡参与者，因此也走同一非法调用合同。

Stage 8 不在这里重新研究某个具体持续状态“来源死亡后是否还能留下独立效果”；真实状态若存在这种特殊机制，必须先由机制研究提供证据并显式扩展生命周期合同。在当前项目已确认规则下，不允许死者继续作为新的 DamageRequest source 参与结算。

## 8.2 Rule Contribution Discovery / Mapping 正式合同

Stage 8 不允许把：

```text
if state_id == evasion
if state_id == critical
if state_id == defense_pierce
```

从 `DamageSystem` 搬到四个新 System 后就宣布架构完成。那只是把同一片 if 森林分盆栽种。

Stage 8 v2 冻结一个最小、只服务 Damage Pipeline 的规则发现层：

```text
StateInstance
↓
StateDamageRuleProvider
↓
DamageRuleCollection
↓
family-specific typed contributions
↓
DamagePreventionSystem / HitResolutionSystem /
DamageFormulaPolicySystem / DamageModifierSystem
```

正式类型概念：

```text
DamageRuleFamily
- PREVENTION
- HIT
- FORMULA_POLICY
- MODIFIER

DamageRuleCollection
- prevention_contributions
- hit_contributions
- formula_policy_contributions
- modifier_contributions
```

`DamageRuleCollection` 是一次 `DamageSystem.calculate()` 内的只读快照：

```text
只读
不消耗 RNG
不修改 StateRegistry
不修改 troops
不发布 Event
```

默认实现 `StateDamageRuleProvider`：

```text
1. 仅通过 context.states 读取 source / target 当前 StateInstance
2. 按 instance_id 形成确定性输入顺序
3. 使用不可变 StateRuleBinding 表把 state_id 映射到一个或多个 family adapter
4. adapter 根据 typed StateRuntimeParams 构造 typed contribution
5. core resolver 只看 typed contribution，不识别 OfficialStateId
```

`StateRuleBinding` / adapter 可以知道具体官方 `state_id`；但是具体 ID 只能集中在独立 binding / adapter 层，例如：

```text
sgs_v2/battle_core/damage_state_rule_bindings.py
```

禁止出现在：

```text
DamagePreventionSystem core resolver
HitResolutionSystem core resolver
DamageFormulaPolicySystem core resolver
DamageModifierSystem core resolver
```

synthetic state 必须通过同一 binding/provider 接口进入，而不是测试专用后门。

允许一个 `StateInstance` 产生多个 contribution，但必须：

```text
family 明确
声明顺序明确
provenance 相同且可追踪
```

若未来出现非 State 来源的伤害规则，允许实现额外 `DamageRuleProvider`，但必须拥有稳定的 `provider_key / order_key`，且不得把 EventBus、BattleSystems 或任意回调系统变成万能 Rule Engine。

### 8.2.1 RuleContributionSource

Stage 8 v2 统一使用独立来源对象，不再用含义模糊的 `source_id` 表示 modifier 来源：

```text
RuleContributionSource
- owner_id: str | None
- applied_by_unit_id: str | None
- source_skill_id: str | None
- source_state_id: str | None
- source_state_instance_id: str | None
- origin_key: str
```

从 `StateInstance` 映射时：

```text
owner_id                 = StateInstance.owner_id
applied_by_unit_id       = StateInstance.source_id
source_skill_id          = StateInstance.source_skill_id
source_state_id          = StateInstance.state_id
source_state_instance_id = StateInstance.instance_id
```

其中：

```text
DamageRequest.source_id
= 本次伤害的攻击 / 伤害来源单位

RuleContributionSource.owner_id
= 当前拥有该规则/状态的单位

RuleContributionSource.applied_by_unit_id
= 当初施加该状态的单位
```

三者必须严格区分。

对于非 State contribution：

```text
source_state_id = None
source_state_instance_id = None
```

两者继续满足 Stage 7 的成对不变量；`origin_key` 必须提供确定性审计身份。

---

# 9. DamagePreventionSystem

Stage 8 新增：

```text
DamagePreventionSystem
```

它回答：

> 在进行命中裁决和基础公式 RNG 之前，本次伤害是否已经因为确定性规则而不能继续？

Stage 8 v1 至少迁移：

```text
weakness / 虚弱
```

正式要求：

```text
输入：
BattleContext
DamageRequest

输出：
DamagePermissionResult
```

建议使用联合类型：

```text
DamageAllowedResult
DamagePreventedResult

DamagePermissionResult
= DamageAllowedResult | DamagePreventedResult
```

`DamagePreventedResult` 至少保存：

```text
reason: DamagePreventionReason
reason_state_id: str | None
reason_state_instance_id: str | None
```

Stage 8 第一版：

```text
DamagePreventionReason.WEAKNESS
```

未来可扩展，但不得预先塞几十个无人使用的 enum。

---

# 10. weakness / 虚弱迁移合同

当前 Stage 4 行为：

```text
source 拥有 weakness
→ base_damage = 0
→ scaled_damage = 0
→ final_damage = 0
→ prevented = True
→ 不进入正常基础伤害公式
```

Stage 8 允许迁移代码位置，但不允许改变行为。

迁移后：

```text
DamageSystem
↓
DamagePreventionSystem
↓
weakness matched
↓
DamagePreventedResult
↓
DamageSystem 构造兼容 DamageResult
```

必须保持：

```text
不消耗基础伤害 RNG
不调用 TroopSystem
DAMAGE_PREVENTED 事实仍成立
final_damage == 0
prevented == True
prevented_by_state_id == "weakness"
```

Stage 8 完成后，不应继续在 `DamageSystem` 内保留第二套：

```python
if context.states.has(... weakness ...):
```

否则只是把旧 `if` 复制了一份，属于架构失败，不属于“兼容”。

---

# 11. HitResolutionSystem

Stage 8 新增：

```text
HitResolutionSystem
```

它只回答：

> 已经允许产生伤害的 DamageRequest，是否成功通过本次命中 / 回避 / 抵御裁决？

输入：

```text
BattleContext
DamageRequest
```

输出建议：

```text
HitAllowedResult
HitPreventedResult

HitResolutionResult
= HitAllowedResult | HitPreventedResult
```

`HitPreventedResult` 至少保存：

```text
reason: HitPreventionReason
reason_state_id: str
reason_state_instance_id: str
```

候选枚举：

```text
EVASION
BARRIER
```

`HitAllowedResult` 可以保存用于审计的最小 bypass 信息，例如：

```text
sure_hit_applied: bool
```

如果需要精确追踪被必中绕过的状态实例，应使用强类型 tuple，不得使用万能 dict。

---

# 12. 命中层与伤害阻止层必须分开

以下不是同一语义：

```text
weakness
→ 攻击者根本不能造成伤害

evasion
→ 本次伤害被回避

barrier
→ 本次伤害被免疫 / 抵御
```

因此：

```text
DamagePreventionSystem
≠ HitResolutionSystem
```

`DamageResult.prevented == True` 可以作为兼容的统一最终表现，但 Stage 8 trace 必须能区分原因。

否则未来 BattleReport 只能告诉我们：

```text
“伤害是 0”
```

却解释不了：

```text
为什么是 0
```

那种日志的调试价值与天气预报里的“今天有天气”差不多。

---

# 13. sure_hit / 必中的裁决边界

官方静态目录当前文本：

```text
必中
= 发动战法及普通攻击命中目标时无视规避及抵御
```

Stage 8 基础设施必须支持：

```text
sure_hit
→ bypass evasion
→ bypass barrier
```

但正式 production mapping 前仍需 Matrix 明确：

```text
适用 DamageSourceType
对连续伤害是否生效
多实例是否有额外语义
与未来特殊免疫的边界
```

Stage 8 禁止把“必中”实现成：

```text
所有 DamageRequest 永远不能被任何机制阻止
```

因为官方文本只明确：

```text
规避
抵御
```

未来其他 `DamagePreventionReason` 不得被必中顺便抹掉。

---

# 14. Hit Resolution 的确定性工程顺序

Stage 8 v1 建议冻结以下 D = ENGINEERING DECISION：

```text
DamagePreventionSystem
↓
sure_hit bypass policy
↓
deterministic barrier-like prevention
↓
probabilistic evasion
↓
HIT
```

重要限制：

```text
这个顺序不是自动声明官方所有组合关系已经确认。
```

任何真实状态只有在 Evidence Matrix 证明其交互与该政策兼容后才能 PASS。

尤其：

```text
barrier 是否消耗次数
evasion 非线性叠加
barrier + evasion 同时存在时的官方资源消耗
```

如果未知会改变真实结果或状态消耗：

```text
DEFER
```

---

# 15. DamageFormulaPolicySystem

Stage 8 新增：

```text
DamageFormulaPolicySystem
```

职责：

```text
根据当前 DamageRuleCollection + BattleContext + DamageRequest
决定 frozen base formula 对“目标防御属性贡献”采用什么 typed policy
```

第一版强类型：

```text
DamageDefensePolicy.NORMAL
DamageDefensePolicy.IGNORE_RELEVANT_TARGET_DEFENSE
```

语义：

```text
WEAPON
+ IGNORE_RELEVANT_TARGET_DEFENSE
→ 目标统率 / defense 对本次基础伤害公式贡献视为 0

STRATEGY
+ IGNORE_RELEVANT_TARGET_DEFENSE
→ 目标 intelligence 对本次基础伤害公式的防御贡献视为 0
```

它不得：

```text
直接计算基础伤害
直接修改 UnitRuntime.defense
直接修改 UnitRuntime.intelligence
永久修改 AttributeSystem
复制一套 ignore-defense 公式
```

## 15.1 DamageFormulaContext 是唯一公式政策输入

Stage 8 v2 冻结：

```text
@dataclass(frozen=True, slots=True)
DamageFormulaContext:
    defense_policy: DamageDefensePolicy = NORMAL
```

`DamageFormulaPolicySystem` 输出必须能规范化为一个 `DamageFormulaContext`；`DamageSystem` 只通过这个 typed context 把 policy 传给基础公式。

为了保护 Stage 2～7 的直接公式调用与 positional compatibility，基础公式签名只允许做**向后兼容的 keyword-only 扩展**：

```text
WeaponBaseDamageFormula.calculate(
    context,
    source,
    target,
    *,
    formula_context: DamageFormulaContext | None = None,
)

StrategyBaseDamageFormula.calculate(
    context,
    source,
    target,
    *,
    formula_context: DamageFormulaContext | None = None,
)
```

兼容合同：

```text
旧调用 calculate(context, source, target)
→ formula_context=None
→ 规范化为 DamageDefensePolicy.NORMAL
→ 必须与 Stage 7 exact-equivalent
```

Stage 8 canonical `DamageSystem` 路径则必须显式传入 policy system 返回的 context，不能靠隐藏全局状态。

禁止扩展成：

```text
ignore_defense: bool
ignore_intelligence: bool
ignore_xxx: bool
```

这种会迅速繁殖的布尔参数集合。

## 15.2 Frozen Formula 内唯一允许的 policy 分支

基础公式内部只允许在**读取 target defensive contribution 的位置**使用 policy：

```text
NORMAL
→ 继续通过 AttributeSystem 读取原目标 defense / intelligence

IGNORE_RELEVANT_TARGET_DEFENSE
→ 本次局部 target defensive contribution = 0
```

随后：

```text
F(N)
source 属性
source/target level
兵种克制
士气
基础随机
low damage floor
```

全部继续走同一份既有数学实现。

禁止：

```text
calculate_ignore_defense()
第二套公式 class
临时改 AttributeSystem provider
临时改 UnitRuntime 属性再恢复
```

NORMAL 路径必须以 differential / golden test 锁定结果与 RNG 消耗位置完全不漂移。

---

# 16. defense_pierce / 破阵

官方静态目录：

```text
破阵
= 造成伤害时无视目标统率及智力
```

Stage 8 正式实现时应进入：

```text
DamageFormulaPolicySystem
```

而不是：

```text
if defense_pierce:
    final_damage *= 1.XX
```

因为“无视防御属性”不是普通最终伤害倍率。

必须证明：

```text
WEAPON
→ 只改变目标防御输入

STRATEGY
→ 只改变目标智力防御输入

source 自身 attack / intelligence 继续正常读取
兵种克制继续正常
士气继续正常
基础伤害随机继续正常
F(N) 查表继续正常
```

---

# 17. rebellion / 叛逃在 Stage 8 的位置

Stage 7 已明确：

```text
rebellion
= 周期伤害
+ 无视防御
```

但 Stage 7 没有正式 Damage Formula Policy，因此 DEFER。

Stage 8 只负责提供：

```text
“这一次 DamageRequest 可以使用 IGNORE_RELEVANT_TARGET_DEFENSE”
```

并不自动说明 `rebellion` 可以立即 PASS。

如果仍未知：

```text
damage_type
coefficient / 基础伤害基准
trigger 精确时机
source attribution
来源死亡后的规则
```

则：

```text
rebellion = DEFER
```

不得因为 Stage 8 已经有 ignore-defense 基础设施，就顺手猜完其余规则。

---

# 18. 基础伤害公式冻结边界

Stage 8 不重新研究、修改：

```text
WeaponBaseDamageFormula 的 F(N) 查表
兵刃基础公式数学结构
StrategyBaseDamageFormula 数学结构
兵种克制既有倍率
士气既有倍率
基础随机区间
low damage floor
```

允许的最小改动仅限：

```text
为 DamageDefensePolicy 增加受控的“目标防御属性输入政策”
```

NORMAL policy 下必须保证：

```text
Stage 2～7 所有既有基础伤害 golden cases
逐项不漂移
```

建议建立 exact regression：

```text
同 seed
同 unit
同 troops
同 coefficient
NORMAL policy

Stage 8 前后：
base_damage 相同
scaled_damage 相同
final_damage 相同
RNG 消耗相同
```

---

# 19. coefficient 的正式位置

Stage 8 继续冻结：

```text
base_damage
↓
coefficient
↓
scaled_damage
```

即：

```text
scaled_damage = base_damage * request.coefficient
```

Stage 8 Modifier Pipeline 从：

```text
scaled_damage
```

开始处理。

不得把 `coefficient` 偷偷混入通用 modifier list，否则 Stage 5/6 已冻结的 `DamageEffect.coefficient` 语义会变得不可审计。

---

# 20. DamageModifierSystem

Stage 8 新增：

```text
DamageModifierSystem
```

它负责：

```text
读取当前合法 modifier 来源
构造 typed modifier contribution
按明确 phase / 顺序处理
记录 applied trace
返回修改后的浮点伤害
```

它不得：

```text
TroopSystem.apply_damage
发布 Victory
直接执行 Effect
写 StateRegistry
修改 UnitRuntime
```

输入建议：

```text
BattleContext
DamageRequest
base_damage
scaled_damage
DamageFormulaPolicyResult
```

输出建议：

```text
DamageModificationResult
```

至少包含：

```text
input_damage: float
output_damage: float
applied_modifiers: tuple[AppliedDamageModifier, ...]
```

---

# 21. Damage Modifier 必须强类型

禁止：

```python
modifier = {
    "type": "whatever",
    "value": ...
}
```

Stage 8 v2 冻结最小 schema：

```text
DamageModifierContribution
- phase: DamageModifierPhase
- kind: DamageModifierKind
- operation: DamageModifierOperation
- operand: float
- source: RuleContributionSource
- order_key: str

AppliedDamageModifier
- contribution
- input_damage
- output_damage
- original_operand
- effective_operand
```

`operand` 与所有中间 / 输出数值必须：

```text
finite
bool rejected as number
满足 operation / kind 自身范围约束
```

Stage 8 v1 只需要正式实现一个基础 operation：

```text
DamageModifierOperation.MULTIPLY_FACTOR
```

未来如果真实证据要求：

```text
ADD_FLAT
CAP_MAX
FLOOR_MIN
```

可以新增 operation enum + executor branch，而不需要推翻 Contribution 总体 schema。没有真实消费者前不预建这些 operation。

`DamageModifierKind` v1 至少区分：

```text
CRITICAL_MULTIPLIER
OUTGOING_INCREASE
OUTGOING_REDUCTION
INCOMING_INCREASE
INCOMING_REDUCTION
SINGLE_HIT_ADJUSTMENT
```

注意：

```text
kind
= 规则语义分类

operation
= 对数值执行什么操作
```

二者不是同一概念。

例如 synthetic 测试可以让：

```text
INCOMING_REDUCTION
+ MULTIPLY_FACTOR
+ operand = 0.80
```

表示一个明确的工程测试输入；但不得因此宣布官方“20% 减伤一定这样叠加”。官方 stacking 仍由 Evidence Matrix 决定。

贡献来源统一使用：

```text
RuleContributionSource
```

不得再把 modifier/state 来源字段叫成与 `DamageRequest.source_id` 相同语义的裸 `source_id`。

---

# 22. Stage 8 v1 Modifier Phase

第二版只冻结有明确 Stage 8 消费者 / 插入需求的 phase：

```text
CRITICAL
OUTGOING
INCOMING
SINGLE_HIT
```

概念：

```text
CRITICAL
→ 会心 / 奇谋一类本次伤害倍率

OUTGOING
→ 造成伤害提高 / 降低

INCOMING
→ 受到伤害提高 / 降低

SINGLE_HIT
→ 警戒等“仅针对本次单次伤害”的修正插入点
```

v1 **删除 `FINAL` phase**。

原因：

```text
当前没有正式消费者
提前创建只会制造一个语义空洞的万能兜底层
```

未来有真实规则必须位于所有现有 modifier 之后时，再通过新证据与设计审计新增 phase。

---

# 23. Modifier Phase 顺序的证据边界

Stage 8 冻结模拟器工程顺序：

```text
scaled_damage
→ CRITICAL
→ OUTGOING
→ INCOMING
→ SINGLE_HIT
→ finalization
```

该顺序属于：

```text
D = ENGINEERING DECISION
```

除非 Matrix 有官方 / 实测证据，否则不得写成：

```text
“游戏官方结算顺序就是这样”
```

真实状态如果其正确结果依赖某两个 phase 的精确先后，而当前证据不足：

```text
该状态 DEFER
```

为了让未来发现官方顺序不同时可以替换，phase resolver 必须：

```text
通过明确 phase sequence 驱动
不得把 phase 顺序散落硬编码到各状态 adapter
不得让 adapter 直接调用下一 phase
```

---

# 24. 同 phase 的确定性顺序

Stage 8 v1 冻结工程确定性：

```text
State 来源 contribution
→ source_state_instance_id 升序
→ 同一 StateInstance 内按 adapter declaration order

非 State 来源
→ provider_key / order_key 明确排序
```

禁止依赖：

```text
set 顺序
dict 偶然插入顺序
对象内存地址
Python hash
```

确定性执行顺序：

```text
≠ 官方 stacking 规则
```

因此：

```text
“按 instance_id 稳定执行”
```

只能证明模拟器 deterministic，不能替代 Evidence Matrix 对真实多实例 stacking 的研究。

---

# 25. 会心 / 奇谋基础设施

官方文本：

```text
critical / 会心
= 有概率造成双倍兵刃伤害

strategy_critical / 奇谋
= 有概率造成双倍谋略伤害
```

Stage 8 基础设施应支持：

```text
WEAPON
→ critical candidate

STRATEGY
→ strategy_critical candidate
```

并且：

```text
错误伤害类型
→ 不参与对应 critical roll
→ 不消耗无意义 RNG
```

如果正式接入，runtime params 至少需要明确：

```text
probability
```

建议复用强类型概率参数，而不是万能 payload。

概率必须：

```text
int / float
bool reject
finite
0.0 <= probability <= 1.0
最终规范化为 float
```

双倍语义：

```text
multiplier = 2.0
```

但其与其他 modifier 的官方精确顺序仍需 Evidence Matrix。

---

# 26. Critical RNG 的工程位置

Stage 8 v1 建议冻结：

```text
DamagePrevention
↓
Hit Resolution RNG（若需要）
↓
Base Damage Formula RNG
↓
Critical / Modifier RNG（若需要）
```

理由：

```text
被阻止 / 未命中的伤害不应该再计算基础伤害；
只有真正进入 damage modification 的请求才做 critical 裁决。
```

这是 D = ENGINEERING DECISION，不声明与客户端内部 RNG stream 完全一致。

必须保持：

```text
probability == 0
→ 不消耗 RNG

probability == 1
→ 不消耗 RNG

0 < probability < 1
→ 通过 context.random / RandomSystem
```

---

# 27. 造成伤害 / 受到伤害 Modifier

Stage 8 建立基础设施，但不要求一次接入所有真实战法。

最小概念：

```text
OUTGOING
= source 侧对本次伤害的修改

INCOMING
= target 侧对本次伤害的修改
```

必须能够表达：

```text
造成伤害提高
造成伤害降低
受到伤害提高
受到伤害降低
```

但实际 stacking 语义，例如：

```text
多个 +20% 是加算还是乘算
多种减伤如何叠加
增伤和减伤先后
上限 / 下限
```

如果没有证据：

```text
不准写成官方规则
```

synthetic modifier 可以使用明确工程操作验证 pipeline。

---

# 28. 看破 / Damage Reduction Pierce

官方文本：

```text
看破
= 造成伤害时无视目标一定比例的受到伤害降低效果
```

因此看破不是普通：

```text
final_damage *= 1.XX
```

而且它也不能与 `defense_pierce` 混为一谈。

Stage 8 v2 冻结：

```text
INCOMING_REDUCTION
```

必须是 `DamageModifierKind` 中类型可识别的 contribution category。

DamageModifierSystem 的内部处理顺序概念为：

```text
collect typed modifier contributions
↓
识别 INCOMING_REDUCTION contributions
↓
如存在合法 reduction-pierce transform，则计算 effective_operand
↓
按 phase / deterministic order 应用 effective contributions
↓
AppliedDamageModifier 同时记录 original_operand / effective_operand
```

pierce transform 只能接触：

```text
DamageModifierKind.INCOMING_REDUCTION
```

禁止影响：

```text
INCOMING_INCREASE
OUTGOING modifier
CRITICAL
Formula defense policy
```

Stage 8 可以提供一个纯计算的 reduction-transform 插入合同，例如概念上的：

```text
DamageReductionTransform
```

但 v2 **不冻结任何官方 pierce 数学公式**。

如果以下未知：

```text
多个 reduction 先聚合还是逐个处理
pierce rate 如何叠加
pierce 对每个 reduction 还是对 aggregate 生效
rounding
上下限
```

则：

```text
damage_reduction_pierce 官方状态 = DEFER
```

synthetic tests 可以使用明确给定的 transform 输入 / 输出验证“只穿透 reduction，不误伤其他 kind”，但 synthetic 算法不得进入官方 Evidence Matrix 的 PASS 结论。

---

# 29. 警戒 / Vigilance

官方文本：

```text
警戒
= 可减少单次受到的伤害
```

这说明它应位于：

```text
SINGLE_HIT
```

一类专门 phase，而不是混成永久 Attribute Modifier。

但正式生产实现前必须研究：

```text
减伤数值来源
固定值 / 百分比
是否消耗层数 / 次数
什么时候消耗
被 0 伤害 / 被抵御时是否消耗
多警戒实例如何处理
与看破是否交互
```

任何会改变单次基础行为的 UNKNOWN 未解决：

```text
vigilance = DEFER
```

Stage 8 的 `DamageModifierSystem` 只负责计算本次理论伤害，明确禁止：

```text
减少 vigilance 次数
移除 vigilance StateInstance
写 StateRegistry
触发额外 Effect
```

如果真实警戒需要 charge / consumption，这一“消费动作”必须由后续经过设计审计的状态消费/反应机制承接；在该合同存在前，官方 vigilance 继续 DEFER。

---

# 30. Finalization

非 prevented 的 Damage Pipeline 最终：

```text
modified_damage: float
↓
int(modified_damage)
↓
max(1, ...)
↓
final_damage
```

Stage 8 v1 默认继续保护 Stage 2 既有语义：

```text
非明确 prevented 的合法伤害
→ final_damage >= 1
```

合法 0 伤害继续只来自明确裁决：

```text
DamagePreventedResult
HitPreventedResult
```

如果未来证据证明某种减伤可以在非“免疫 / 回避”语义下把伤害降为 0，则必须显式扩展 finalization policy，不得偷偷删掉 `max(1, ...)`。

---

# 31. DamageResult 向后兼容

Stage 7 最终审计已经专门修复 `DamageResult` positional compatibility。

当前必须保护既有字段顺序，尤其已有 positional tail：

```text
source_skill_id
prevented
prevented_by_state_id
source_state_id
source_state_instance_id
```

Stage 8 新字段：

```text
只能追加
不得插入旧字段中间
```

建议追加：

```text
pipeline_trace: DamagePipelineTrace | None = None
```

或等价的单一强类型 trace。

不建议把几十个 Stage 8 字段直接平铺到 `DamageResult`。

---

# 32. DamagePipelineTrace

Stage 8 建立不可变 typed trace：

```text
DamagePipelineTrace
```

至少包含：

```text
prevention_result: DamagePermissionResult
hit_result: HitResolutionResult | None
formula_policy_result: DamageFormulaPolicyResult | None
modifier_result: DamageModificationResult | None
```

要求：

```text
frozen dataclass
slots
不得包含可变 list / dict 作为运行时合同
```

## 32.1 short-circuit 语义

Stage 8 v2 明确：

```text
pipeline_trace is None
```

只表示：

```text
legacy / manual DamageResult 没有 Stage 8 trace
```

而正式 `DamageSystem.calculate()` 返回的 `DamageResult`：

```text
pipeline_trace 必须非 None
```

一旦存在 `DamagePipelineTrace`，某个 stage 字段为 `None` 的唯一含义是：

```text
NOT_EVALUATED because an earlier stage short-circuited
```

例如：

```text
weakness prevented
→ prevention_result = PREVENTED
→ hit_result = None
→ formula_policy_result = None
→ modifier_result = None

barrier/evasion prevented
→ prevention_result = ALLOWED
→ hit_result = PREVENTED
→ formula_policy_result = None
→ modifier_result = None

normal hit
→ 四个已执行阶段均有 typed result
```

禁止为了让 trace “看起来完整”而伪造：

```text
identity hit
NORMAL formula policy
empty modifier result
```

去冒充没有实际执行的阶段。

## 32.2 多 contributor trace

`HitPreventedResult` / 聚合概率类结果不得永久限制为“只有一个 reason state”。

v2 推荐：

```text
contributors: tuple[RuleContributionSource, ...]
decisive_source: RuleContributionSource | None
```

对于确定性单实例 barrier：

```text
contributors = (that_source,)
decisive_source = that_source
```

对于未来可能确认的非线性多实例 evasion：

```text
contributors
```

可以保留所有参与聚合的实例；`decisive_source` 是否存在由实际算法决定。

EventBus 需要序列化时再把 trace 转换成普通 payload，不能让 event payload 反向成为 runtime rule contract。

---

# 33. DamageResult prevented 兼容映射

Stage 8 必须继续支持旧字段：

```text
prevented: bool
prevented_by_state_id: str | None
```

正式映射：

```text
DamagePreventionSystem prevented
→ prevented = True

HitResolutionSystem prevented
→ prevented = True

正常 hit + damage
→ prevented = False
```

`prevented_by_state_id`：

```text
如果阻止来自具体 StateInstance
→ 对应 state_id

如果未来阻止来自非状态规则
→ None
```

真正的 typed 原因放在：

```text
pipeline_trace
```

---

# 34. EventBus 事实扩展与发布所有权

Stage 8 不允许 EventBus 参与规则计算。

更严格地冻结：

```text
DamageRuleProvider / StateDamageRuleProvider
DamagePreventionSystem
HitResolutionSystem
DamageFormulaPolicySystem
DamageModifierSystem
DamageSystem.calculate()

= 全部不得 publish battle fact
= 全部不得持有 EventBus 作为规则依赖
```

唯一发布所有权继续属于：

```text
DamageResolutionSystem.apply_result()
```

它根据已经完成的 `DamageResult` 发布：

```text
DAMAGE_PREVENTED
DAMAGE_DEALT
UNIT_DEFEATED（按既有合同）
```

这必须保护 Stage 4 已冻结的普通攻击事实顺序：

```text
NORMAL_ATTACK
→ DAMAGE_PREVENTED
```

或：

```text
NORMAL_ATTACK
→ DAMAGE_DEALT
```

绝不能因为 HitResolution 在 `DamageSystem.calculate()` 内提前 publish，变成：

```text
DAMAGE_PREVENTED
→ NORMAL_ATTACK
```

Stage 8 如需更细审计信息，只允许：

```text
calculation systems 写入 DamagePipelineTrace
↓
DamageResolutionSystem 在 apply_result 时序列化 trace summary 到 event payload
```

`DAMAGE_PREVENTED` 可在保持旧 payload 的前提下追加：

```text
prevention_family
prevention_reason
reason_state_instance_id
contributors summary
```

`DAMAGE_DEALT` 可追加：

```text
formula_defense_policy
modifier_trace summary
critical_applied（若真实发生）
```

事件 payload 是事实表示，不是运行时规则对象。

---

# 35. State / Modifier provenance

Stage 7 已冻结 `StateInstance` 的：

```text
owner_id
source_id
source_skill_id
instance_id
state_id
```

Stage 8 不再把这些来源与 `DamageRequest.source_id` 混用。

正式语义：

```text
DamageRequest.source_id
= 本次 DamageRequest 的伤害来源单位

RuleContributionSource.owner_id
= 当前拥有该 State / rule 的单位

RuleContributionSource.applied_by_unit_id
= 施加该 State 的单位，对应 StateInstance.source_id

RuleContributionSource.source_skill_id
= 对应 StateInstance.source_skill_id

RuleContributionSource.source_state_id
= 对应 StateInstance.state_id

RuleContributionSource.source_state_instance_id
= 对应 StateInstance.instance_id
```

例：

```text
A 对 B 造成伤害
C 曾给 B 施加一个减伤状态
```

必须能够同时恢复：

```text
damage source = A
modifier owner = B
modifier applied_by = C
```

任何 trace / event serializer 都不得把三者压缩回一个含义模糊的 `source_id`。

多实例时还必须能够回答：

> 哪些具体 StateInstance 参与了本次裁决，哪一个（如果存在）是最终 decisive instance？

禁止只记录：

```text
"critical": True
```

却完全丢失贡献来源。

---

# 36. Stage 8 runtime params 原则

只有真实 production consumer 已经通过 Evidence Gate 后，才为对应官方状态升级：

```text
StateDefinition.runtime_params_type
```

候选：

```text
ProbabilityStateParams
DamageRateStateParams
DamageReductionPierceStateParams
```

但第一版规划不强制这些名字。

硬要求：

```text
StateRuntimeParams subclass
explicit frozen dataclass
slots
强类型校验
bool 不得伪装成数字
finite
范围明确
```

禁止：

```python
payload: dict[str, Any]
```

作为 Stage 8 状态万能参数。

## 36.1 Stage 8 数值 domain 合同

所有 Stage 8 新增 probability / rate / modifier operand 必须：

```text
bool 明确拒绝
NaN 明确拒绝
+inf / -inf 明确拒绝
范围由具体 typed params / operation 显式验证
```

同时 Stage 8 对既有 damage coefficient 增加 contract hardening：

```text
DamageRequest.coefficient
DamageEffect.coefficient

必须 finite
必须 >= 0
bool 不得作为 0 / 1 偷渡
```

该 hardening 只能改变“此前未定义的非法输入”，所有合法有限 coefficient 的 Stage 5/6 行为必须完全不漂移。

`DamageModifierSystem` 输出给 finalization 的 `modified_damage` 必须：

```text
finite
>= 0
```

非有限或违反 operation 约束的 contribution 必须在 finalization 前失败，不能让 `int(NaN)`、`int(inf)` 或负数偶然决定战斗规则。

---

# 37. 官方状态初始 Evidence Gate

Stage 8 v2 不再用模糊的 “EVIDENCE GATE” 占位作为施工 scope 开关；正式 artifact：

```text
research/stage8_evidence_matrix/STAGE8_EVIDENCE_MATRIX.md
```

必须存在并给出唯一 verdict。

当前 v2 的安全初始 verdict：

| state | Stage 8 机制归属 | v2 verdict |
|---|---|---|
| `weakness` / 虚弱 | DamagePreventionSystem | `PASS_STAGE8`，仅限既有冻结行为的架构迁移 |
| `evasion` / 规避 | HitResolutionSystem | `DEFER` |
| `barrier` / 抵御 | HitResolutionSystem | `DEFER` |
| `sure_hit` / 必中 | HitResolutionSystem bypass policy | `DEFER` production mapping |
| `defense_pierce` / 破阵 | DamageFormulaPolicySystem | `DEFER` |
| `vigilance` / 警戒 | SINGLE_HIT modifier | `DEFER` |
| `critical` / 会心 | CRITICAL modifier | `DEFER` real mapping |
| `strategy_critical` / 奇谋 | CRITICAL modifier | `DEFER` real mapping |
| `damage_reduction_pierce` / 看破 | INCOMING_REDUCTION transform | `DEFER` |
| `rebellion` / 叛逃 | periodic damage + formula policy | `DEFER` |

这意味着 Stage 8 可以施工：

```text
generic infrastructure
synthetic contributions
weakness compatibility migration
```

但不能仅凭本设计把其余官方状态接入 production handler。

未来某一行从 `DEFER` 升级到 `PASS_STAGE8` 时，必须同时满足 Matrix 中对应证据字段与测试合同，且引用固定 commit SHA + path。

---

# 38. Stage 8 Evidence Matrix 字段

正式文件：

```text
research/stage8_evidence_matrix/STAGE8_EVIDENCE_MATRIX.md
```

每个候选至少记录：

```text
state_id
official text
research source
research commit SHA / file path
rule family
applicable DamageType
applicable DamageSourceType
runtime params schema
probability semantics
stacking semantics
consumption semantics
prevention / hit semantics
formula policy
modifier phase
cross-state precedence
rounding evidence
RNG evidence
source provenance
known unknowns
implementation verdict
```

`implementation verdict` 只能：

```text
PASS_STAGE8
DEFER
```

---

# 39. Stage 8 Hard Gate

如果 UNKNOWN 会改变单实例或核心交互的真实行为，例如：

```text
是否会消耗 barrier
evasion 概率如何合并
critical 概率来源无法确定
vigilance 减伤类型无法确定
damage reduction pierce 算法无法确定
defense_pierce 对何类伤害生效无法确定
sure_hit 对某类 DamageSourceType 是否生效无法确定
```

则：

```text
DEFER
```

如果 UNKNOWN 只涉及 Stage 8 明确不声称解决的未来机制，例如：

```text
未来 BattleReport UI
API 输出格式
性能优化
```

则不阻止基础设施 FROZEN。

---

# 40. 多实例与 stacking

Stage 8 必须区分：

```text
deterministic processing order
```

和：

```text
official stacking behavior
```

前者必须实现。

后者如果未知：

```text
不得靠“按 instance_id 一个个乘”假装解决。
```

尤其 `evasion` 官方文本已经明确：

```text
规避几率为非线性叠加
```

因此如果 nonlinear aggregation 公式没有证据：

```text
真实 evasion 多实例 production mapping 不得声称完整实现
```

Evidence Matrix 必须明确这是否足以让整个状态 DEFER。

---

# 41. RNG 边界

Stage 8 所有新增概率裁决必须：

```text
context.random
或
RandomSystem
```

不得：

```python
import random
random.random()
```

新增 RNG 至少包括候选：

```text
evasion
critical
strategy_critical
```

必须验证无意义 RNG 不消耗：

```text
weakness prevented
→ 不 roll hit
→ 不算 base formula
→ 不 roll critical

sure_hit bypass evasion
→ 不 roll evasion

barrier 确定阻止
→ 不算 base formula
→ 不 roll critical

错误 DamageType 的 critical state
→ 不 roll critical

probability 0 / 1
→ 不调用 RandomSystem.chance
```

## 41.1 最小 probability helper

为了让 evasion / critical / strategy critical 使用一致的 RNG 消耗合同，Stage 8 可以建立一个纯 helper，而不是新 System：

```text
resolve_probability(context, probability)
```

固定行为：

```text
p == 0
→ False
→ 不调用 context.random

p == 1
→ True
→ 不调用 context.random

0 < p < 1
→ context.random.chance(p)
```

输入必须先通过 finite / bool / [0,1] 验证。

该 helper 不保存 RNG 对象；battle-local RNG 永远来自当前调用的：

```text
context.random
```

---

# 42. DamageSourceType 过滤

当前：

```text
NORMAL_ATTACK
SKILL
CONTINUOUS
COUNTER
```

Stage 8 状态不能默认对所有来源一视同仁。

例如官方必中明确：

```text
发动战法及普通攻击
```

因此 production handler 必须根据 Evidence Matrix 显式声明：

```text
允许哪些 DamageSourceType
```

禁止：

```text
“为了方便，所有 DamageRequest 都生效”
```

除非证据确实如此。

---

# 43. DamageType 过滤

当前：

```text
WEAPON
STRATEGY
```

Stage 8 必须显式过滤：

```text
critical
→ WEAPON only

strategy_critical
→ STRATEGY only
```

`defense_pierce`：

```text
WEAPON
→ ignore target defense

STRATEGY
→ ignore target intelligence defense contribution
```

未来新增其他 DamageType 时不得通过 `else` 静默当作某一种已知伤害。

---

# 44. BattleSystems 组合与 DamageSystem 构造兼容

Stage 8 canonical 关系：

```text
DamageRuleProvider
DamagePreventionSystem
HitResolutionSystem
DamageFormulaPolicySystem
DamageModifierSystem
        ↓
DamageSystem
        ↓
DamageResolutionSystem
        ↓
TroopSystem
```

`BattleSystems.__post_init__()` 继续是 canonical wiring root。

禁止：

```text
DamagePreventionSystem(BattleSystems)
HitResolutionSystem(BattleSystems)
DamageModifierSystem(BattleSystems)
```

这种万能依赖。

## 44.1 `DamageSystem` 公开构造兼容

Stage 8 必须保护 Stage 2～7 已存在的 `DamageSystem(...)` 直接构造方式。

新 collaborators 不得插进旧 positional 参数中间。

建议把新增依赖封装为一个 typed `DamageRuleServices`（名称可等价调整），并仅通过 keyword-only 参数进入：

```text
DamageSystem(
    <existing positional / keyword args unchanged>,
    *,
    rule_services: DamageRuleServices | None = None,
)
```

关键语义必须写死：

```text
rule_services is None
→ 构造行为等价的 default Stage 8 services
→ 包含正式 Damage Pipeline
→ 包含 weakness compatibility binding
→ 绝不表示“跳过 Stage 8”
```

`BattleSystems` 可以显式创建并传入同一 default services；旧代码手动构造 `DamageSystem` 时则自动得到**同语义**默认服务。

必须证明：

```text
canonical BattleSystems construction
== manual legacy DamageSystem construction
```

在同一 context / request / seed 下具有相同 pipeline、相同 weakness 行为、相同 RNG 消耗。

禁止形成：

```text
BattleSystems → 完整 Stage8
manual DamageSystem → silently legacy-only
```

的双语义世界。

---

# 45. 依赖方向与 battle-local runtime truth

Stage 8 v2 冻结两条 runtime truth：

```text
runtime StateRegistry
= context.states only

runtime RNG
= context.random only
```

Stage 8 任一 constructor 都不得保存第二套 battle-local：

```text
RandomSystem
StateRegistry
```

否则会出现：

```text
context.random != self._random
context.states != self._states
```

这种无法审计的双真相。

建议依赖：

```text
StateDamageRuleProvider
→ BattleContext（读取 context.states）

DamagePreventionSystem
→ typed prevention contributions

HitResolutionSystem
→ typed hit contributions
→ BattleContext（仅概率时读取 context.random）

DamageFormulaPolicySystem
→ typed formula-policy contributions

DamageModifierSystem
→ typed modifier contributions
→ BattleContext（仅概率 modifier 时读取 context.random）

DamageSystem
→ DamageRuleServices / provider + above resolvers
→ AttributeSystem
→ Frozen Formula

DamageResolutionSystem
→ DamageSystem
→ TroopSystem
```

不得反向：

```text
ModifierSystem → DamageResolutionSystem
HitResolutionSystem → EffectExecutor
DamageSystem → RuleHookSystem
Stage8 calculation system → EventBus publisher
Stage8 system → BattleSystems mega-dependency
```

Stage 9 Reaction Queue 以后另建。

---

# 46. Effect / Skill 边界

Stage 8 不修改 Stage 5 / 6 核心命题：

```text
SkillResolver
→ Effect only
```

DamageEffect 仍然只表达：

```text
source
target
damage type
source type
coefficient
provenance
```

Stage 8 不建议在 `DamageEffect` 上堆：

```text
is_critical
ignore_defense
ignore_evasion
ignore_barrier
damage_reduction_pierce
```

因为这些通常是 BattleState / Battle Rule 决定的运行规则，不应该由上层 Effect 预先算完。

如果某个未来技能本身的一次性效果确实需要显式 policy，再单独设计 typed contract，不使用 bool 大礼包。

---

# 47. Trigger / Recovery 边界

Stage 8 不扩展：

```text
AFTER_DAMAGE
Reaction Queue
first_aid
weapon_lifesteal
strategy_lifesteal
```

这些继续属于 Stage 9 Reaction / Queue。

Stage 8 可以让 Stage 7 的周期 DamageEffect 自动经过新的 Damage Pipeline。

也就是说：

```text
synthetic periodic DamageEffect
→ DamageResolutionSystem
→ Stage 8 DamageSystem
→ Prevention / Hit / Formula / Modifier
```

不建立“持续伤害专用第二套 pipeline”。

---

# 48. Target / Action 边界

Stage 8 不做：

```text
taunt
guard
confusion
target redirect
target force
combo
additional action
counterattack queue
cleave
```

这些继续 Stage 9。

也不做：

```text
silence
insight
false_report
capture
skill disable policy
```

这些继续后续高级控制阶段。

---

# 49. 推荐生产文件

新增候选：

```text
sgs_v2/battle_core/damage_rule_provider.py
sgs_v2/battle_core/damage_state_rule_bindings.py
sgs_v2/battle_core/damage_prevention_system.py
sgs_v2/battle_core/hit_resolution_system.py
sgs_v2/battle_core/damage_formula_policy_system.py
sgs_v2/battle_core/damage_formula_context.py
sgs_v2/battle_core/damage_modifier_system.py
sgs_v2/battle_core/damage_modifiers.py
sgs_v2/battle_core/stage8_state_params.py
```

必要修改候选：

```text
sgs_v2/battle_core/damage_system.py
sgs_v2/battle_core/damage_resolution_system.py
sgs_v2/battle_core/weapon_damage_formula.py
sgs_v2/battle_core/strategy_damage_formula.py
sgs_v2/battle_core/battle_systems.py
sgs_v2/battle_core/official_state_catalog.py
sgs_v2/battle_core/events.py
sgs_v2/battle_core/__init__.py
```

文档 / 研究：

```text
research/stage8_evidence_matrix/STAGE8_EVIDENCE_MATRIX.md
```

如果某官方状态没有 PASS：

```text
official_state_catalog.py
```

可以仍保留其静态目录，但不得为它配置新的 production runtime params / handler。

---

# 50. DamageResult compatibility 测试

必须保护 Stage 7 的 positional constructor。

至少测试：

```text
旧 positional 构造仍有效
旧 keyword 构造仍有效
新增 trace 字段在末尾
手动构造 trace=None 合法
DamageSystem.calculate() 正式路径产生 typed trace
legacy DamageResult.pipeline_trace=None 合法
canonical Stage8 DamageResult.pipeline_trace 必须非 None
short-circuit stage 使用 None = NOT_EVALUATED
```

Stage 8 不得重演一次“改 dataclass 字段顺序把旧调用方悄悄炸掉”的古典喜剧。

---

# 51. DamagePreventionSystem 测试

必须覆盖：

```text
无 prevention → allowed
weakness → prevented
多个 weakness instance → deterministic reason instance
weakness 不消耗 RNG
weakness 不进入 HitResolution
weakness 不进入 base formula
weakness 不进入 critical
weakness 不调用 TroopSystem
DamageSystem 不再保留重复 weakness hardcode
weakness 通过正式 StateRuleBinding / provider 产生 contribution
core DamagePreventionSystem 不识别 OfficialStateId.WEAKNESS
```

还必须验证：

```text
DamagePreventionSystem
不修改 troops
不写 StateRegistry
不发布 Victory
不 import random
```

---

# 52. HitResolutionSystem synthetic 测试

即使真实状态暂时 DEFER，也必须使用 synthetic state 验证基础设施：

```text
无 hit rule → HIT
deterministic barrier → prevented
evasion probability 0 → HIT without RNG
evasion probability 1 → prevented without RNG
0 < evasion < 1 → context.random
sure_hit → bypass evasion
sure_hit → bypass barrier
sure_hit bypass 时不消耗 evasion RNG
hit prevented 后不进入 base formula
hit prevented 后不进入 critical
```

如果真实 barrier consumption 证据不足：

```text
synthetic barrier
≠ 官方 barrier 已实现
```

还必须覆盖多 contributor trace：

```text
单 contributor deterministic barrier
→ contributors 与 decisive_source 正确

多 synthetic evasion contributor
→ trace 能保留全部 contributors
```

---

# 53. Formula Policy 测试

必须覆盖：

```text
NORMAL weapon
→ 与 Stage 7 完全相同

NORMAL strategy
→ 与 Stage 7 完全相同

IGNORE_RELEVANT_TARGET_DEFENSE + WEAPON
→ 目标 defense contribution 被忽略
→ source attack 正常
→ troops / level / morale / troop counter 正常

IGNORE_RELEVANT_TARGET_DEFENSE + STRATEGY
→ target intelligence defense contribution 被忽略
→ source intelligence 正常
```

必须检查：

```text
基础公式 RNG 次数不因 NORMAL policy 改变
旧三参数 calculate(context, source, target) 与显式 NORMAL context exact-equivalent
IGNORE policy 只改变 target defensive contribution，不改变其他公式输入
不存在第二套 ignore-defense formula
```

---

# 54. Modifier Pipeline synthetic 测试

至少建立不依赖真实 state_id 的 synthetic modifier cases：

```text
单一 CRITICAL modifier
单一 OUTGOING modifier
单一 INCOMING modifier
单一 SINGLE_HIT modifier
多 phase 固定顺序
同 phase instance_id 固定顺序
trace before / after value 正确
provenance 正确
DamageModifierKind / DamageModifierOperation 区分正确
INCOMING_REDUCTION 与 INCOMING_INCREASE 类型可区分
unsupported operation 明确拒绝
```

必须证明：

```text
DamageModifierSystem
只修改理论伤害数值
不写 troops
不写 StateRegistry
不执行 Effect
```

---

# 55. Critical 测试

如果 critical 基础设施进入 Stage 8：

```text
WEAPON + critical candidate
→ 正确 roll

STRATEGY + critical state
→ 不 roll

STRATEGY + strategy_critical candidate
→ 正确 roll

WEAPON + strategy_critical state
→ 不 roll
```

概率：

```text
0 → 不触发、不 RNG
1 → 必触发、不 RNG
(0,1) → RandomSystem.chance
```

若 production state 尚未 PASS：

```text
使用 synthetic critical params
```

---

# 56. Damage Reduction Pierce synthetic 测试

即使真实 `damage_reduction_pierce` 尚未 PASS，基础设施应证明：

```text
INCOMING_REDUCTION 可被识别
pierce 只作用于 reduction
不作用于 damage taken increase
不作用于 critical
不作用于 formula defense
original_operand / effective_operand trace 正确
```

如果 Stage 8 第一版最终审计决定不实现 pierce 算法本体，也至少必须冻结可插入点并在文档明确 DEFER 原因。

---

# 57. Finalization 测试

必须覆盖：

```text
正常 positive modified damage
→ int
→ min 1

modified damage in (0,1)
→ final_damage = 1

explicit prevented
→ final_damage = 0

prevented
→ 不通过 min 1 强行变回 1

NaN / inf modified damage
→ finalization 前拒绝

negative modified damage
→ 违反 Stage8 modifier output contract，finalization 前拒绝
```

还必须保护现有：

```text
requested_damage property
```

兼容语义。

---

# 58. DamageResolutionSystem 集成测试

必须证明：

```text
DamageRequest
→ Stage 8 DamageSystem
→ DamageResult
→ TroopSystem.apply_damage
```

只有一个实际扣兵入口。

测试：

```text
prevented → troop_change is None
hit prevented → troop_change is None
normal damage → apply_damage once
actual damage capped by target troops
DAMAGE_PREVENTED payload 正确
DAMAGE_DEALT payload 正确
UNIT_DEFEATED 行为不漂移
Stage8 calculation systems 不提前 publish EventBus
NORMAL_ATTACK → DAMAGE_PREVENTED / DAMAGE_DEALT 顺序不漂移
```

Stage 8 不改变 VictorySystem 责任。

---

# 59. Provenance 集成测试

至少证明：

```text
StateInstance
→ prevention / hit / modifier contribution
→ DamagePipelineTrace
→ DamageResult
→ Event payload
```

保留：

```text
state_id
instance_id
source_skill_id（如适用）
owner_id
applied_by_unit_id（如适用）
```

必须专门覆盖：

```text
A damages B
C-applied state on B reduces damage

DamageResult.source_id = A
RuleContributionSource.owner_id = B
RuleContributionSource.applied_by_unit_id = C
```

必须覆盖多实例，不能只测一个状态然后假设 trace 永远没问题。

---

# 60. RNG non-consumption 集成测试

建议单独建立：

```text
tests/test_stage8_rng_consumption.py
```

至少锁定：

```text
weakness
sure_hit bypass
barrier prevent
evasion 0
evasion 1
wrong damage type critical
critical 0
critical 1
```

以及 NORMAL baseline：

```text
没有 Stage 8 新规则时
→ Base Formula RNG sequence 与 Stage 7 相同

canonical BattleSystems construction
与 manual DamageSystem construction
→ RNG position 相同
```

## 60.1 Damage participant / numeric contract tests

必须覆盖：

```text
dead source
→ InvalidDamageParticipantError
→ 0 RNG / 0 Event / 0 troop mutation

dead target
→ same

0 troops source / target
→ same

DamageRequest.coefficient = NaN / inf / bool / negative
→ reject

DamageEffect.coefficient = NaN / inf / bool / negative
→ reject

modifier operand = NaN / inf / bool
→ reject
```

这些是非法输入 contract tests，不得混成 `DAMAGE_PREVENTED` 行为测试。

---

# 61. Stage 1～7 全回归

Stage 8 必须保护：

```text
先攻 / 遇袭
缴械
震慑
虚弱最终行为
禁疗
RecoverySystem
RuleHookSystem
TriggerSystem
EffectExecutor
SkillDefinition
SkillRuntime
SkillResolver
State provenance
DamageResult positional compatibility
NormalAttackSystem
基础兵刃公式
基础谋略公式
RNG non-consumption
```

特别是：

```text
weakness 迁移
```

属于内部架构升级，不允许改变 Stage 4 的公开行为。

---

# 62. Architecture Tests 与 Behavior Tests 分工

建议新增：

```text
tests/test_stage8_architecture.py
```

AST / source inspection 只保护适合静态检查的红线：

```text
BattleEngine 无 Stage 8 具体 state_id
EffectExecutor 无 evasion / barrier / critical 分支
DamageResolutionSystem 不识别具体官方状态
TroopSystem 不识别 Stage 8 状态
core DamagePreventionSystem 不识别具体 OfficialStateId
core HitResolutionSystem 不识别具体 OfficialStateId
core DamageFormulaPolicySystem 不识别具体 OfficialStateId
core DamageModifierSystem 不识别具体 OfficialStateId
具体 state_id mapping 只允许集中在 binding / adapter 层
新增系统不 import Python random
Stage8 systems 不保存第二套 RandomSystem / StateRegistry
Stage8 calculation systems 不依赖 EventBus publisher
StateRuntimeParams 无 execute()
无直接 troops assignment
无 Stage8 → DamageResolutionSystem / EffectExecutor 反向依赖
```

以下内容必须使用 behavior tests，而不是脆弱字符串搜索：

```text
DamageSystem 唯一实际 pipeline
NORMAL formula exact equivalence
RNG consumption position
event ordering
prevented no troop mutation
manual/canonical construction equivalence
RuleContributionSource provenance
PipelineTrace short-circuit
DEFER official state 没有 production consumer
```

禁止用“文件里没出现某个字符串”来证明复杂运行行为正确。

---

# 63. Stage 8 OUT OF SCOPE

第一版明确不做：

```text
真实战法大规模目录

Reaction Queue
AFTER_DAMAGE
first_aid
weapon_lifesteal
strategy_lifesteal

combo
cleave
counterattack
damage_split
damage_share
chain_link
guard

taunt
confusion
target redirect

StateApplicationPolicy
完整同名状态覆盖 / refresh / max policy

insight
silence
false_report
provoke
capture
intimidation
完整 skill disable policy

完整装备系统

BattleReport
Replay
API
批量模拟
性能优化
```

Stage 8 trace 只是为未来可解释性保留必要事实，不等于 BattleReport 已实现。

---

# 64. Stage 8 必须回答的设计问题

独立设计审计至少逐项回答：

```text
1. DamageSystem 为什么仍然是理论伤害唯一入口？
2. Prevention 与 Hit Resolution 为什么必须分开？
3. weakness 如何迁移而不改变 Stage 4 行为？
4. sure_hit 精确绕过哪些规则？
5. sure_hit 是否错误绕过了 weakness？
6. evasion / barrier 的官方 UNKNOWN 是否足以阻止 production mapping？
7. Hit Resolution 何时消耗 RNG？
8. 为什么 hit prevented 后不计算 base damage？
9. DamageFormulaPolicy 为什么不能直接修改 UnitRuntime 属性？
10. defense_pierce 如何在不修改基础公式数学结构的情况下实现？
11. NORMAL formula policy 如何证明完全回归？
12. coefficient 为什么必须保持在 modifier pipeline 之前？
13. DamageModifierPhase 是否足够且没有过度设计？
14. phase 顺序哪些是官方证据，哪些只是 D？
15. 同 phase 多实例如何保证工程确定性？
16. deterministic order 为什么不等于 stacking 规则？
17. critical / strategy critical 如何做 DamageType 过滤？
18. critical RNG 在哪里发生？
19. probability 0 / 1 为什么不应消耗 RNG？
20. OUTGOING / INCOMING modifier 如何区分？
21. 看破如何只穿透“受到伤害降低”？
22. vigilance 为什么应该有 SINGLE_HIT phase？
23. final_damage 的 min 1 语义如何保护？
24. prevented 0 伤害如何避免被 min 1 覆盖？
25. DamageResult positional compatibility 如何保护？
26. pipeline trace 的正式 schema 是什么？
27. modifier provenance 如何追踪到 instance_id？
28. Stage 8 Evidence Matrix 固定存放在哪里？
29. 哪些官方状态 PASS，哪些 DEFER，依据是什么？
30. rebellion 为什么不能只因为有 ignore-defense 就自动 PASS？
31. Stage 7 periodic DamageEffect 如何自动进入 Stage 8 pipeline？
32. 为什么 Stage 8 不建立 Reaction Queue？
33. 为什么 Stage 8 不处理 Target Redirect？
34. 如何证明没有第二套 Damage / RNG / Troop mutation 路径？
35. 如何证明基础伤害公式没有漂移？
```

第一轮审计后，第二轮设计复审还必须明确回答：

```text
36. StateInstance 通过哪个唯一 provider / binding contract 变成 typed contribution？
37. core resolver 是否完全不知道具体 OfficialStateId？
38. synthetic state 是否走同一 provider / binding 路径？
39. Formula Policy 是否只通过 DamageFormulaContext 进入 frozen formula？
40. 旧三参数 formula calculate 是否 exact-equivalent NORMAL？
41. Modifier kind 与 operation 是否在类型上分离？
42. INCOMING_REDUCTION 是否可被 pierce 精确识别而不误伤 increase / critical / formula？
43. 为什么 v1 不再保留 FINAL phase？
44. runtime StateRegistry 是否只有 context.states？
45. runtime RNG 是否只有 context.random？
46. manual DamageSystem 与 BattleSystems canonical construction 是否行为等价？
47. Damage source / rule owner / state applier 是否可同时追踪？
48. 哪些对象明确禁止 publish EventBus？
49. PipelineTrace 的 None 是 legacy missing 还是 stage NOT_EVALUATED，是否无歧义？
50. dead / 0 troops DamageRequest 是否在 RNG 前明确拒绝？
51. NaN / inf / bool 是否可能进入 coefficient / modifier pipeline？
52. Evidence Matrix 是否已经真实存在，而不是只在 STAGE8.md 里提到？
```

---

# 65. Stage 8 验收条件

只有以下全部成立，Stage 8 才可进入最终实现审计：

```text
[ ] DamageRuleProvider / StateDamageRuleProvider 正式合同建立
[ ] DamageRuleCollection 只读、无 RNG、无 mutation、无 Event
[ ] official state_id 仅集中在 binding / adapter 层
[ ] core prevention / hit / formula-policy / modifier resolver 不识别具体 OfficialStateId
[ ] synthetic state 走与 official binding 相同的 discovery contract
[ ] RuleContributionSource 明确区分 owner / applied_by / damage source
[ ] dead source / dead target / 0 troops precondition 已冻结并测试
[ ] invalid participant 不产生 DAMAGE_PREVENTED / DAMAGE_DEALT

[ ] DamagePreventionSystem 建立
[ ] weakness 行为完成兼容迁移
[ ] DamageSystem 不再重复 hardcode weakness
[ ] typed DamagePreventionReason 建立
[ ] typed DamagePermissionResult 建立

[ ] HitResolutionSystem 建立
[ ] typed HitResolutionResult 建立
[ ] synthetic evasion / barrier / sure_hit 基础设施测试通过
[ ] hit prevented 后不进入基础伤害公式
[ ] sure_hit bypass 不消耗无意义 evasion RNG
[ ] sure_hit 不错误绕过 weakness

[ ] DamageFormulaPolicySystem 建立
[ ] DamageDefensePolicy 建立
[ ] DamageFormulaContext 建立
[ ] base formula 只做 keyword-only policy 扩展
[ ] 旧三参数 formula 调用 exact-equivalent NORMAL
[ ] NORMAL policy 完全回归
[ ] IGNORE_RELEVANT_TARGET_DEFENSE synthetic 测试通过
[ ] 基础兵刃公式数学结构未被重写
[ ] 基础谋略公式数学结构未被重写

[ ] coefficient 既有语义未改变
[ ] DamageModifierSystem 建立
[ ] typed modifier contribution 建立
[ ] DamageModifierKind / DamageModifierOperation 明确分离
[ ] v1 仅实现有消费者的 operation；未知 operation 不预建
[ ] FINAL phase 已从 v1 删除
[ ] DamageModifierPhase 建立
[ ] deterministic modifier ordering 建立
[ ] modifier trace 建立
[ ] modifier provenance 完整

[ ] critical 基础设施若进入 scope，则 DamageType / RNG policy 完整测试
[ ] damage reduction pierce 插入点明确
[ ] vigilance SINGLE_HIT 插入点明确
[ ] 非明确 prevented 继续保持 min 1
[ ] prevented 继续合法 final_damage = 0

[ ] DamageResult positional compatibility 保持
[ ] Stage 8 新字段只追加
[ ] DamagePipelineTrace 强类型
[ ] canonical DamageSystem trace 必须非 None
[ ] short-circuit stage None = NOT_EVALUATED
[ ] hit trace 支持 contributors + decisive_source
[ ] DAMAGE_PREVENTED 事件保持兼容
[ ] DAMAGE_DEALT 事件保持兼容

[ ] BattleSystems canonical wiring 完成
[ ] manual DamageSystem construction 与 canonical construction 语义等价
[ ] context.states 是唯一 runtime StateRegistry
[ ] context.random 是唯一 runtime RNG
[ ] TroopSystem 仍为唯一兵力写入口
[ ] DamageResolutionSystem 仍为理论伤害到实际扣兵唯一协调层
[ ] RandomSystem / context.random 仍为唯一战斗 RNG
[ ] EventBus 仍只记录事实
[ ] Stage8 calculation systems 全部禁止 publish battle facts
[ ] DamageResolutionSystem.apply_result 继续拥有 DAMAGE_PREVENTED / DAMAGE_DEALT 发布权
[ ] NORMAL_ATTACK event order 不漂移
[ ] BattleEngine 无具体 Stage 8 state_id
[ ] EffectExecutor 无具体 Stage 8 状态规则

[ ] STAGE8_EVIDENCE_MATRIX.md 存在
[ ] 所有真实 Stage 8 production mapping 均为 PASS_STAGE8
[ ] DEFER 状态没有 production handler
[ ] UNKNOWN 没有被写成官方结论
[ ] research repo 引用包含 commit SHA + path（仅在实际引用外部研究时）
[ ] 当前 Matrix 中 weakness 为兼容迁移 PASS；其余未有充分证据者保持 DEFER

[ ] coefficient / modifier finite 数值边界测试通过
[ ] dead / zero-troop precondition 测试通过
[ ] architecture tests 与 behavior tests 职责分离

[ ] Stage 1～7 全回归
[ ] pytest -q success
[ ] python demo.py success
[ ] GitHub Actions success
[ ] 独立最终审计 BLOCKER = 0
[ ] 独立最终审计 MAJOR = 0
```

---

# 66. Stage 8 设计与封版流程

建议严格执行：

```text
STAGE8.md v1
↓
第一轮独立设计审计
↓
STAGE8.md v2 修订（当前）
↓
第二轮独立设计复审
↓
必要时第三轮快速复审
↓
STAGE8.md DESIGN FROZEN
↓
prompts/STAGE8_BUILD_PROMPT.md
↓
Stage 8 施工分支
↓
pytest + demo + CI
↓
独立实现审计
↓
修复
↓
再次审计
↓
STAGE8_FINAL_AUDIT.md
↓
merge main
↓
main exact HEAD CI success
↓
Stage 8 FROZEN
```

不得因为：

```text
“第一版文档看起来很完整”
```

就跳过设计审计。

---

# 67. Stage 8 最终目标

Stage 8 真正要冻结的是：

```text
DamageRequest
↓
DamagePreventionSystem
↓
HitResolutionSystem
↓
DamageFormulaPolicySystem
↓
Frozen Base Formula
↓
coefficient
↓
DamageModifierSystem
↓
finalization
↓
DamageResult + DamagePipelineTrace
↓
DamageResolutionSystem
↓
TroopSystem
```

以及：

```text
StateInstance
↓
StateDamageRuleProvider / binding adapter
↓
typed rule contribution
↓
deterministic resolution
↓
typed trace
↓
Event fact
```

最终应做到：

```text
状态可以影响伤害
但状态对象不执行伤害；

Modifier 可以改变理论伤害
但 Modifier 不写兵力；

Hit Resolution 可以阻止一次伤害
但不创建第二套 Damage path；

无视防御可以改变公式输入政策
但不篡改 UnitRuntime 属性；

所有概率都经过 RandomSystem；

所有真实官方行为都经过 Evidence Gate。
```

只要这一层冻结，Stage 9 才能安全进入：

```text
Reaction Queue
Target Redirect
追加行动
反击
群攻
分摊 / 分担
援护
混乱 / 嘲讽
```

而不是让这些机制继续从 `DamageSystem`、`EventBus` 和各种状态 `if` 的缝隙里长出来。
