# 三国志战略版战斗模拟器 V2 · Stage 8 Damage Rule / Hit Resolution / Modifier Pipeline 实施规范

> 本文是 Stage 8 的第一版正式规划草案，用于后续独立设计审计与修订。
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
Stage 8                   规划 / 待独立设计审计
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
输入：BattleContext + DamageRequest
输出：DamagePermissionResult
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

Stage 8 完成后，不应继续在 `DamageSystem` 内保留第二套 weakness hardcode。

---

# 11. HitResolutionSystem

Stage 8 新增：

```text
HitResolutionSystem
```

它只回答：

> 已经允许产生伤害的 DamageRequest，是否成功通过本次命中 / 回避 / 抵御裁决？

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

`HitAllowedResult` 可以保存最小 bypass 信息，例如：

```text
sure_hit_applied: bool
```

如果需要精确追踪被必中绕过的状态实例，应使用强类型 tuple，不得使用万能 dict。

---

# 12. 命中层与伤害阻止层必须分开

以下不是同一语义：

```text
weakness → 攻击者不能造成伤害
evasion  → 本次伤害被回避
barrier  → 本次伤害被免疫 / 抵御
```

因此：

```text
DamagePreventionSystem
≠ HitResolutionSystem
```

`DamageResult.prevented == True` 可以作为兼容的统一最终表现，但 Stage 8 trace 必须能区分原因。

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

但 production mapping 前仍需 Matrix 明确适用 `DamageSourceType`、连续伤害、多实例和未来特殊免疫边界。

Stage 8 禁止把“必中”实现成无视一切 DamagePrevention。

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

这个顺序不自动声明官方所有组合关系已经确认。

如果 barrier 消耗、evasion 非线性叠加、barrier + evasion 资源消耗等 UNKNOWN 会改变真实结果，则对应官方状态 DEFER。

---

# 15. DamageFormulaPolicySystem

Stage 8 新增：

```text
DamageFormulaPolicySystem
```

职责是根据 `BattleContext`、`DamageRequest` 和状态事实决定基础伤害公式使用什么防御属性政策。

第一版建议：

```text
DamageDefensePolicy.NORMAL
DamageDefensePolicy.IGNORE_RELEVANT_TARGET_DEFENSE
```

语义：

```text
WEAPON + IGNORE_RELEVANT_TARGET_DEFENSE
→ 目标 defense 对本次基础伤害公式贡献视为 0

STRATEGY + IGNORE_RELEVANT_TARGET_DEFENSE
→ 目标 intelligence 的防御贡献视为 0
```

它不得直接计算基础伤害、修改 UnitRuntime 属性或永久修改 AttributeSystem。

---

# 16. defense_pierce / 破阵

官方静态目录：

```text
破阵 = 造成伤害时无视目标统率及智力
```

Stage 8 正式实现时应进入 `DamageFormulaPolicySystem`，而不是伪装成最终伤害倍率。

必须保证：

```text
WEAPON → 只改变目标防御输入
STRATEGY → 只改变目标智力防御输入
source 自身 attack / intelligence 正常
兵种克制正常
士气正常
基础伤害随机正常
F(N) 查表正常
```

---

# 17. rebellion / 叛逃在 Stage 8 的位置

Stage 7 已明确：

```text
rebellion = 周期伤害 + 无视防御
```

Stage 8 只负责提供本次 `DamageRequest` 可采用 ignore-defense policy 的基础设施。

如果 `damage_type`、`coefficient` / 基础伤害基准、trigger 精确时机、source attribution、来源死亡后规则仍未知，则：

```text
rebellion = DEFER
```

不得因为已有 ignore-defense 基础设施就顺手猜完其余机制。

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

允许的最小改动仅限为 `DamageDefensePolicy` 增加受控的目标防御属性输入政策。

NORMAL policy 下必须保证 Stage 2～7 所有既有基础伤害 golden cases 不漂移。

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

Stage 8 Modifier Pipeline 从 `scaled_damage` 开始处理，不把 Stage 5/6 已冻结的 coefficient 语义混进 modifier list。

---

# 20. DamageModifierSystem

Stage 8 新增：

```text
DamageModifierSystem
```

负责读取合法 modifier 来源、构造 typed contribution、按明确 phase / 顺序处理、记录 applied trace 并返回修改后的理论伤害。

它不得扣兵、发布 Victory、执行 Effect、写 StateRegistry 或修改 UnitRuntime。

输出建议：

```text
DamageModificationResult
- input_damage: float
- output_damage: float
- applied_modifiers: tuple[AppliedDamageModifier, ...]
```

---

# 21. Damage Modifier 必须强类型

禁止万能 dict modifier。

建议使用：

```text
DamageModifierContribution
AppliedDamageModifier
DamageModifierPhase
DamageModifierKind
```

贡献来源必须可追踪：

```text
source_id
source_skill_id
source_state_id
source_state_instance_id
```

Stage 7 provenance pairing 不变量继续成立。

---

# 22. Stage 8 v1 Modifier Phase

第一版建议建立最小 phase：

```text
CRITICAL
OUTGOING
INCOMING
SINGLE_HIT
FINAL
```

概念：

```text
CRITICAL   → 会心 / 奇谋
OUTGOING   → 造成伤害提高 / 降低
INCOMING   → 受到伤害提高 / 降低
SINGLE_HIT → 警戒等单次伤害专用修正
FINAL      → 未来确有消费者时的最终修正
```

不得提前造大量空 phase。

---

# 23. Modifier Phase 顺序的证据边界

Stage 8 可以冻结一个模拟器工程顺序：

```text
scaled_damage
→ CRITICAL
→ OUTGOING
→ INCOMING
→ SINGLE_HIT
→ FINAL
→ finalization
```

该顺序属于 D = ENGINEERING DECISION。真实状态如果正确结果依赖某两个 phase 的精确先后而证据不足，该状态 DEFER。

---

# 24. 同 phase 的确定性顺序

Stage 8 v1 冻结工程确定性：

```text
同一 phase 多个 StateInstance
→ source_state_instance_id 升序

单个 StateInstance 多 contribution
→ declaration order

非 State 来源
→ 显式 deterministic order key
```

确定性执行顺序不等于官方 stacking 规则。

---

# 25. 会心 / 奇谋基础设施

官方文本：

```text
会心 = 有概率造成双倍兵刃伤害
奇谋 = 有概率造成双倍谋略伤害
```

Stage 8 基础设施应支持：

```text
WEAPON → critical candidate
STRATEGY → strategy_critical candidate
```

错误 DamageType 不参与对应 critical roll，也不消耗无意义 RNG。

概率参数必须强类型、finite、范围 `[0, 1]`，bool reject。

双倍语义为 multiplier 2.0，但与其他 modifier 的官方精确顺序仍需 Evidence Matrix。

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

这是 D = ENGINEERING DECISION，不声明与客户端内部 RNG stream 完全一致。

必须保持：

```text
probability == 0 → 不消耗 RNG
probability == 1 → 不消耗 RNG
0 < probability < 1 → context.random / RandomSystem
```

---

# 27. 造成伤害 / 受到伤害 Modifier

最小概念：

```text
OUTGOING = source 侧修改
INCOMING = target 侧修改
```

基础设施必须能表达造成伤害提高 / 降低、受到伤害提高 / 降低。

加算、乘算、上限、下限等真实 stacking 规则如果没有证据，不得写成官方规则。

---

# 28. 看破 / Damage Reduction Pierce

官方文本：

```text
看破 = 造成伤害时无视目标一定比例的受到伤害降低效果
```

看破不是普通最终增伤，应作用于可识别的 `INCOMING_REDUCTION` contribution。

如果多个 reduction 的聚合方式、pierce rate 叠加、逐个还是聚合后穿透、rounding 等未知，则真实 `damage_reduction_pierce` 状态 DEFER。

---

# 29. 警戒 / Vigilance

官方文本：

```text
警戒 = 可减少单次受到的伤害
```

基础设施上应进入 `SINGLE_HIT` 一类专门 phase。

但减伤数值来源、固定值 / 百分比、次数 / 层数消耗、被抵御时是否消耗、多实例与看破交互等 UNKNOWN 未解决时：

```text
vigilance = DEFER
```

---

# 30. Finalization

非 prevented 的 Damage Pipeline 最终默认继续保护 Stage 2 语义：

```text
modified_damage
↓
int(modified_damage)
↓
max(1, ...)
↓
final_damage
```

合法 0 伤害继续只来自明确裁决：

```text
DamagePreventedResult
HitPreventedResult
```

若未来证据证明普通减伤可以得到非 prevented 的 0，必须显式扩展 finalization policy。

---

# 31. DamageResult 向后兼容

Stage 7 已冻结 positional compatibility。Stage 8 新字段只能追加，不能插入旧字段中间。

建议追加：

```text
pipeline_trace: DamagePipelineTrace | None = None
```

不建议把大量 Stage 8 字段平铺到 `DamageResult`。

---

# 32. DamagePipelineTrace

建议建立不可变 typed trace：

```text
DamagePipelineTrace
```

至少能审计：

```text
prevention result
hit result
formula defense policy
modifier result
```

要求 frozen dataclass + slots，不得包含可变 list / dict 作为运行时合同。

EventBus 需要序列化时再转换成普通 payload。

旧调用方可 `pipeline_trace=None`，正式 `DamageSystem.calculate()` Stage 8 路径必须产生完整 trace。

---

# 33. DamageResult prevented 兼容映射

Stage 8 继续支持：

```text
prevented: bool
prevented_by_state_id: str | None
```

DamagePreventionSystem 或 HitResolutionSystem prevented 都映射为 `prevented=True`，正常 hit 为 False。

真正的 typed 原因进入 `pipeline_trace`。

---

# 34. EventBus 事实扩展

EventBus 不参与规则计算。

`DAMAGE_PREVENTED` 可兼容追加：

```text
prevention_family
prevention_reason
reason_state_instance_id
```

`DAMAGE_DEALT` 可追加：

```text
formula_defense_policy
modifier_trace summary
critical_applied / multiplier（如正式发生）
```

Event payload 是事实表示，不是运行时规则对象。

---

# 35. State provenance

Stage 8 新的 modifier / prevention / hit trace 必须能够追踪参与裁决的具体 StateInstance。

例如：

```text
evasion instance
barrier instance
critical instance
damage reduction instance
damage reduction pierce instance
```

禁止只保存 `critical=True` 而丢失来源。

---

# 36. Stage 8 runtime params 原则

只有真实 production consumer 通过 Evidence Gate 后，才升级对应 `StateDefinition.runtime_params_type`。

候选可包括：

```text
ProbabilityStateParams
DamageRateStateParams
DamageReductionPierceStateParams
```

名字可在设计审计中调整。

硬要求：StateRuntimeParams subclass、explicit frozen dataclass、slots、强类型校验、bool 不伪装数字、finite、范围明确。

禁止 `payload: dict[str, Any]` 作为万能参数。

---

# 37. 官方状态初始 Evidence Gate

| state | Stage 8 机制归属 | 第一版规划判断 |
|---|---|---|
| `weakness` / 虚弱 | DamagePreventionSystem | 已有生产行为，兼容迁移 |
| `evasion` / 规避 | HitResolutionSystem | EVIDENCE GATE |
| `barrier` / 抵御 | HitResolutionSystem | EVIDENCE GATE |
| `sure_hit` / 必中 | HitResolutionSystem bypass | EVIDENCE GATE |
| `defense_pierce` / 破阵 | DamageFormulaPolicySystem | EVIDENCE GATE |
| `vigilance` / 警戒 | SINGLE_HIT modifier | EVIDENCE GATE |
| `critical` / 会心 | CRITICAL modifier | EVIDENCE GATE |
| `strategy_critical` / 奇谋 | CRITICAL modifier | EVIDENCE GATE |
| `damage_reduction_pierce` / 看破 | INCOMING_REDUCTION transform | EVIDENCE GATE |
| `rebellion` / 叛逃 | periodic damage + formula policy | EVIDENCE GATE |

Stage 8 基础设施施工不要求新状态全部 PASS。

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

如果 UNKNOWN 会改变单实例或核心交互的真实行为，例如 barrier 消耗、evasion 概率合并、critical 概率来源、vigilance 减伤类型、看破算法、破阵适用伤害类型、必中适用 DamageSourceType，则对应真实状态 DEFER。

基础设施仍可用 synthetic case 验收。

---

# 40. 多实例与 stacking

必须区分：

```text
deterministic processing order
```

和：

```text
official stacking behavior
```

前者必须实现，后者未知时不得靠 instance_id 逐个运算冒充解决。

尤其官方文本已明确规避几率为非线性叠加，若聚合公式没有证据，真实 evasion 多实例不能声称完整实现。

---

# 41. RNG 边界

Stage 8 所有新增概率裁决必须经过 `context.random` / `RandomSystem`。

必须验证无意义 RNG 不消耗：

```text
weakness prevented → 不 roll hit / base / critical
sure_hit bypass evasion → 不 roll evasion
barrier 确定阻止 → 不算 base / critical
错误 DamageType critical → 不 roll
probability 0 / 1 → 不调用 RandomSystem.chance
```

NORMAL baseline 没有 Stage 8 新规则时，基础公式 RNG sequence 必须与 Stage 7 相同。

---

# 42. DamageSourceType 过滤

当前：

```text
NORMAL_ATTACK
SKILL
CONTINUOUS
COUNTER
```

Stage 8 状态不得默认对所有来源一视同仁。production handler 必须根据 Evidence Matrix 显式声明适用 `DamageSourceType`。

---

# 43. DamageType 过滤

当前：

```text
WEAPON
STRATEGY
```

必须显式过滤：

```text
critical → WEAPON only
strategy_critical → STRATEGY only
```

`defense_pierce` 对两种 DamageType 分别作用于对应防御输入。

未来新增 DamageType 时不得通过 `else` 静默当作已有类型。

---

# 44. BattleSystems 组合

Stage 8 推荐：

```text
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

`BattleSystems.__post_init__()` 负责 canonical wiring。

禁止各 Stage 8 系统依赖整个 `BattleSystems` 万能对象，只注入真实需要的最小依赖。

---

# 45. 依赖方向

建议：

```text
DamagePreventionSystem → BattleContext / StateRegistry
HitResolutionSystem → BattleContext / RandomSystem
DamageFormulaPolicySystem → BattleContext / StateRegistry
DamageModifierSystem → BattleContext / StateRegistry / RandomSystem
DamageSystem → above systems + AttributeSystem + Frozen Formula
DamageResolutionSystem → DamageSystem + TroopSystem
```

不得反向：

```text
ModifierSystem → DamageResolutionSystem
HitResolutionSystem → EffectExecutor
DamageSystem → RuleHookSystem
```

Reaction Queue 留给 Stage 9。

---

# 46. Effect / Skill 边界

Stage 8 不修改：

```text
SkillResolver → Effect only
```

DamageEffect 仍只表达 source、target、damage type、source type、coefficient、provenance。

不建议往 DamageEffect 堆 `is_critical`、`ignore_defense`、`ignore_evasion` 等 bool。若未来一次性技能政策确有需要，应单独设计 typed contract。

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

这些继续属于 Stage 9。

Stage 7 的周期 DamageEffect 自动经过新的统一 Damage Pipeline，不建立持续伤害专用第二套 pipeline。

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

也不做 silence、insight、false_report、capture 等高级 Skill Policy。

---

# 49. 推荐生产文件

新增候选：

```text
sgs_v2/battle_core/damage_prevention_system.py
sgs_v2/battle_core/hit_resolution_system.py
sgs_v2/battle_core/damage_formula_policy_system.py
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

没有 PASS 的官方状态仍保留静态目录，但不得配置 production runtime params / handler。

---

# 50. DamageResult compatibility 测试

必须保护 Stage 7 positional constructor：

```text
旧 positional 构造仍有效
旧 keyword 构造仍有效
新增 trace 字段在末尾
手动构造 trace=None 合法
DamageSystem.calculate() 正式路径产生 typed trace
```

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
```

并验证 PreventionSystem 不修改 troops、不写 StateRegistry、不发布 Victory、不 import random。

---

# 52. HitResolutionSystem synthetic 测试

即使真实状态 DEFER，也使用 synthetic state 验证：

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

synthetic barrier 不等于官方 barrier 已实现。

---

# 53. Formula Policy 测试

必须覆盖：

```text
NORMAL weapon / strategy → 与 Stage 7 完全相同
IGNORE_RELEVANT_TARGET_DEFENSE + WEAPON → 忽略 target defense contribution
IGNORE_RELEVANT_TARGET_DEFENSE + STRATEGY → 忽略 target intelligence defense contribution
```

source 属性、troops、level、morale、troop counter 和 RNG 其余部分必须保持正常。

---

# 54. Modifier Pipeline synthetic 测试

至少使用 synthetic modifier 覆盖：

```text
单一 CRITICAL
单一 OUTGOING
单一 INCOMING
单一 SINGLE_HIT
多 phase 固定顺序
同 phase instance_id 固定顺序
trace before / after 正确
provenance 正确
```

DamageModifierSystem 只修改理论伤害，不写 troops / StateRegistry，不执行 Effect。

---

# 55. Critical 测试

若 critical 基础设施进入 Stage 8：

```text
WEAPON + critical candidate → 正确 roll
STRATEGY + critical state → 不 roll
STRATEGY + strategy_critical → 正确 roll
WEAPON + strategy_critical → 不 roll
```

概率 0 / 1 不消耗 RNG，中间概率走 RandomSystem.chance。若真实状态未 PASS，则只使用 synthetic params。

---

# 56. Damage Reduction Pierce synthetic 测试

至少证明：

```text
INCOMING_REDUCTION 可识别
pierce 只作用于 reduction
不作用于 damage taken increase
不作用于 critical
不作用于 formula defense
```

若 Stage 8 最终决定不实现 pierce 算法本体，也必须冻结可插入点并明确 DEFER 原因。

---

# 57. Finalization 测试

必须覆盖：

```text
正常 positive modified damage → int → min 1
modified damage in (0,1) → final_damage = 1
explicit prevented → final_damage = 0
prevented 不被 min 1 恢复为 1
```

保护 `requested_damage` 兼容语义。

---

# 58. DamageResolutionSystem 集成测试

必须证明只有一个实际扣兵入口：

```text
DamageRequest
→ Stage 8 DamageSystem
→ DamageResult
→ TroopSystem.apply_damage
```

覆盖 prevented / hit prevented / normal damage / kill cap / DAMAGE_PREVENTED / DAMAGE_DEALT / UNIT_DEFEATED，并保持 VictorySystem 职责不漂移。

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

保留 state_id、instance_id、source_skill_id、source_id（如适用），并覆盖多实例。

---

# 60. RNG non-consumption 集成测试

建议新增：

```text
tests/test_stage8_rng_consumption.py
```

锁定 weakness、sure_hit bypass、barrier prevent、evasion 0/1、wrong DamageType critical、critical 0/1，以及无 Stage 8 规则时与 Stage 7 相同的基础 RNG sequence。

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

weakness 迁移只是内部架构升级，不允许改变 Stage 4 对外行为。

---

# 62. Architecture Tests

建议新增：

```text
tests/test_stage8_architecture.py
```

至少检查：

```text
BattleEngine 无 Stage 8 具体 state_id
EffectExecutor 无 evasion / barrier / critical 分支
DamageResolutionSystem 不识别具体官方状态
TroopSystem 不识别 Stage 8 状态
Stage 8 systems 不依赖 BattleSystems 万能对象
新增系统不 import Python random
StateRuntimeParams 无 execute()
EventBus 不作为规则引擎
```

可以使用 AST / source inspection 锁定关键红线。

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

Stage 8 trace 只是未来可解释性的必要事实，不等于 BattleReport 已实现。

---

# 64. Stage 8 必须回答的设计问题

独立设计审计至少逐项回答：

```text
1. DamageSystem 为什么仍是理论伤害唯一入口？
2. Prevention 与 Hit Resolution 为什么必须分开？
3. weakness 如何迁移而不改变 Stage 4 行为？
4. sure_hit 精确绕过哪些规则？
5. sure_hit 是否错误绕过 weakness？
6. evasion / barrier 的 UNKNOWN 是否足以阻止 production mapping？
7. Hit Resolution 何时消耗 RNG？
8. 为什么 hit prevented 后不计算 base damage？
9. Formula Policy 为什么不能直接修改 UnitRuntime？
10. defense_pierce 如何不重写基础公式数学结构？
11. NORMAL policy 如何证明完全回归？
12. coefficient 为什么保持在 modifier 之前？
13. DamageModifierPhase 是否足够且不过度设计？
14. phase 顺序哪些是证据、哪些只是 D？
15. 同 phase 多实例如何保证工程确定性？
16. deterministic order 为什么不等于 stacking？
17. critical / strategy critical 如何做 DamageType 过滤？
18. critical RNG 在哪里发生？
19. probability 0 / 1 为什么不消耗 RNG？
20. OUTGOING / INCOMING 如何区分？
21. 看破如何只穿透受到伤害降低？
22. vigilance 为什么使用 SINGLE_HIT？
23. final_damage min 1 如何保护？
24. prevented 0 如何避免被 min 1 覆盖？
25. DamageResult positional compatibility 如何保护？
26. pipeline trace 的正式 schema 是什么？
27. modifier provenance 如何追踪 instance_id？
28. Stage 8 Evidence Matrix 存在哪里？
29. 哪些状态 PASS / DEFER，依据是什么？
30. rebellion 为什么不能因有 ignore-defense 自动 PASS？
31. Stage 7 periodic DamageEffect 如何自动进入 Stage 8 pipeline？
32. 为什么 Stage 8 不建立 Reaction Queue？
33. 为什么 Stage 8 不处理 Target Redirect？
34. 如何证明没有第二套 Damage / RNG / Troop mutation 路径？
35. 如何证明基础伤害公式没有漂移？
```

---

# 65. Stage 8 验收条件

只有以下全部成立，Stage 8 才可进入最终实现审计：

```text
[ ] DamagePreventionSystem 建立
[ ] weakness 行为兼容迁移
[ ] DamageSystem 不再重复 hardcode weakness
[ ] typed DamagePreventionReason / DamagePermissionResult 建立

[ ] HitResolutionSystem / typed HitResolutionResult 建立
[ ] synthetic evasion / barrier / sure_hit 测试通过
[ ] hit prevented 后不进入基础伤害公式
[ ] sure_hit bypass 不消耗无意义 evasion RNG
[ ] sure_hit 不错误绕过 weakness

[ ] DamageFormulaPolicySystem / DamageDefensePolicy 建立
[ ] NORMAL policy 完全回归
[ ] IGNORE_RELEVANT_TARGET_DEFENSE synthetic 测试通过
[ ] 基础兵刃 / 谋略公式数学结构未重写

[ ] coefficient 既有语义未改变
[ ] DamageModifierSystem / typed contribution / phase 建立
[ ] deterministic modifier ordering / trace / provenance 完整

[ ] critical 基础设施若进入 scope，则 DamageType / RNG policy 完整测试
[ ] damage reduction pierce 插入点明确
[ ] vigilance SINGLE_HIT 插入点明确
[ ] 非明确 prevented 继续 min 1
[ ] prevented 继续合法 final_damage = 0

[ ] DamageResult positional compatibility 保持
[ ] Stage 8 新字段只追加
[ ] DamagePipelineTrace 强类型
[ ] DAMAGE_PREVENTED / DAMAGE_DEALT 事件保持兼容

[ ] BattleSystems canonical wiring 完成
[ ] TroopSystem 仍为唯一兵力写入口
[ ] DamageResolutionSystem 仍为理论伤害到扣兵唯一协调层
[ ] RandomSystem / context.random 仍为唯一战斗 RNG
[ ] EventBus 仍只记录事实
[ ] BattleEngine / EffectExecutor 无具体 Stage 8 状态规则

[ ] STAGE8_EVIDENCE_MATRIX.md 存在
[ ] 所有真实 production mapping 均 PASS_STAGE8
[ ] DEFER 状态没有 production handler
[ ] UNKNOWN 没有伪装成官方结论
[ ] research repo 引用包含 commit SHA + path

[ ] Stage 1～7 全回归
[ ] pytest -q success
[ ] python demo.py success
[ ] GitHub Actions success
[ ] 独立最终审计 BLOCKER = 0
[ ] 独立最终审计 MAJOR = 0
```

---

# 66. Stage 8 设计与封版流程

```text
STAGE8.md v1
↓
第一轮独立设计审计
↓
修订 STAGE8.md
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

不得因为第一版文档看起来完整就跳过设计审计。

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
状态可以影响伤害，但状态对象不执行伤害；
Modifier 可以改变理论伤害，但 Modifier 不写兵力；
Hit Resolution 可以阻止一次伤害，但不创建第二套 Damage path；
无视防御可以改变公式输入政策，但不篡改 UnitRuntime 属性；
所有概率都经过 RandomSystem；
所有真实官方行为都经过 Evidence Gate。
```

只要这一层冻结，Stage 9 才能安全进入 Reaction Queue、Target Redirect、追加行动、反击、群攻、分摊 / 分担、援护、混乱 / 嘲讽，而不是让这些机制继续从 DamageSystem、EventBus 和各种状态 if 的缝隙里长出来。
