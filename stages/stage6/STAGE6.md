# 三国志战略版战斗模拟器 V2 · Stage 6 SkillDefinition / SkillRuntime / Skill Resolution 实施规范

> 本文是 Stage 6 的正式施工规范。它建立在 GitHub `main` 当前真实状态之上，不依赖旧聊天、旧 Prompt 或历史 SHA 推断项目现状。
>
> 本文只规定 Stage 6 的施工边界、数据合同、依赖方向、测试与封版条件。本文不是施工结果，也不是 FINAL AUDIT。

---

# 0. 当前基线与前置条件

本次 Stage 6 规划重新读取的 `main` 最新 HEAD：

```text
0ae9459731f1d7aa8b011406b39985b0a9a52150
```

对应提交：

```text
docs: add canonical project stage status
```

当前 `main` 上：

```text
PROJECT_STATUS.md
stages/stage5/STAGE5_FINAL_AUDIT.md
```

已经进入同一提交，且该 HEAD 对应的 GitHub Actions：

```text
workflow: tests
status: completed
conclusion: success

Run tests              → success
Run demo smoke test    → success
```

`PROJECT_STATUS.md` 明确规定 Stage 5 的最后冻结条件是：

```text
stages/stage5/STAGE5_FINAL_AUDIT.md 与 PROJECT_STATUS.md 所在提交进入 main
+
该 main 提交 GitHub Actions success
```

该条件现在已经满足。

因此本规范的正式前提是：

```text
Stage 5 = FROZEN
```

如果未来实际施工 Stage 6 时 `main` 已经变化，施工者必须再次重新读取最新 `main`，确认 Stage 5 冻结边界未被破坏，再以新的 HEAD 为实际施工基线。

---

# 1. 为什么现在需要 Stage 6

Stage 1～5 已经建立：

```text
BattleContext
BattleEngine
BattleSystems

TargetSystem
AttributeSystem
ActionOrderSystem
ActionSystem
NormalAttackSystem
DamageSystem
DamageResolutionSystem
TroopSystem
VictorySystem
RandomSystem
EventBus

StateDefinition
StateInstance
StateRegistry
StateLifecycleSystem
StateRuntimeParams

DamageEffect
ApplyStateEffect
RemoveStateEffect
RecoverEffect
EffectExecutor
```

Stage 5 已经证明：

```text
上层规则
→ Effect
→ EffectExecutor
→ BattleSystem
```

可以安全表达伤害和状态变化，而且不会绕过统一伤害、兵力、状态与 RNG 边界。

当前仍然缺少的是 Effect 之前的一层：

```text
“一个战法是什么”
“一个携带者在本场战斗中的该战法实例是什么”
“什么时候进行一次明确的战法解析尝试”
“怎样把一次战法解析转换成 Effect”
```

因此 Stage 6 解决的架构缺口是：

```text
SkillDefinition
        ↓
SkillRuntime
        ↓
Skill Resolution
        ↓
Effect
        ↓
EffectExecutor
        ↓
BattleSystem
```

Stage 6 的成功标准不是“已经能跑大量真实战法”，而是证明：

> Skill 层只决定“希望发生什么”，底层 BattleSystem 仍决定“具体如何发生”。

---

# 2. Stage 6 的最高架构原则

Stage 6 必须保持：

```text
SkillDefinition
= 静态战法数据

SkillRuntime
= 某携带者在当前战斗中的战法运行事实

SkillResolver
= 一次显式技能解析的规则协调层

Effect
= 不可变规则意图

EffectExecutor
= Effect 类型路由

BattleSystem
= 实际战斗规则执行
```

禁止出现：

```text
SkillDefinition.execute()
SkillRuntime.apply_damage()
SkillRuntime.apply_state()
SkillRuntime.choose_random_target()
SkillRuntime.execute_effect()
SkillRuntime.resolve_and_execute()
```

禁止：

```text
Skill → DamageSystem
Skill → DamageResolutionSystem
Skill → TroopSystem
Skill → StateRegistry
Skill → StateLifecycleSystem
Skill → Python random
```

Stage 6 的依赖方向必须以单向为主：

```text
SkillDefinition
      ↓
SkillRuntime
      ↓
SkillResolver
   ┌──┴──────────────┐
   ↓                 ↓
TargetSystem   BattleContext.random
                     ↓
                 RandomSystem
   └────────┬────────┘
            ↓
       ordered Effect(s)
            ↓
       [调用方边界]
            ↓
      EffectExecutor
       /          \
      ↓            ↓
DamageResolution  StateLifecycleSystem
      ↓                  ↓
DamageSystem         StateRegistry
      ↓
TroopSystem
```

Stage 6 不允许出现：

```text
BattleSystems
→ SkillResolver
→ BattleSystems
```

也不允许：

```text
SkillRuntime
→ EffectExecutor
→ BattleSystems
→ SkillRuntime
```

---

# 3. Stage 6 依赖的 Stage 1～5 FROZEN 能力

Stage 6 直接依赖：

```text
BattleContext
= 当前战斗上下文与每场战斗唯一 RandomSystem

TargetSystem
= 目标查询与随机选择统一入口

RandomSystem
= 唯一战斗 RNG 来源

Effect
= 不可变意图数据

EffectExecutor
= Effect 执行路由

DamageResolutionSystem
= 统一伤害落地协调层

StateLifecycleSystem
= 状态正式写入口
```

必须保持不变的旧边界：

```text
DamageSystem
= 只计算理论伤害

TroopSystem
= 唯一兵力修改入口

StateRegistry
= 状态存储与查询中心

StateLifecycleSystem
= 状态正式加入 / 删除 / 到期入口

BattleEngine
= 通用流程推进器

EventBus
= 已发生事实的记录 / 分发器，不是规则引擎

RandomSystem
= 唯一战斗 RNG 封装
```

Stage 6 不得以“技能需要”为理由重新设计以上系统。

---

# 4. 证据等级

Stage 6 所有规则必须按以下等级理解：

```text
A = 官方接口 / 官方文本
B = 项目方明确确认
C = 实测 / 逆向研究
D = 工程设计决定
E = UNKNOWN / NEEDS_RESEARCH
```

本阶段尤其要防止把 D 伪装成 A。

当前可以确认：

```text
[A]
官方状态文本已经明确出现“主动战法”“指挥战法”“被动战法”等概念，
但这些文本不足以证明所有战法分类的完整生命周期、触发时机和优先级。

[B]
项目已经明确要求：Skill 只产生 Effect，不直接操作底层 BattleSystem。

[B]
项目已经明确要求：RandomSystem 是唯一 RNG，TargetSystem 是目标规则统一入口。

[D]
Stage 6 synthetic skill 的 Effect 按 effect_specs 声明顺序产生。

[D]
Stage 6 对 0% / 100% 发动率不消费“发动判定 RNG”。

[D]
Stage 6 在没有合法目标时不进行发动率 RNG。

[E]
真实游戏中“目标存在性检查、发动率判定、目标随机选择”的官方精确先后顺序。

[E]
主动 / 突击 / 指挥 / 被动 / 阵法 / 兵种的完整生命周期和自动发动时点。

[E]
计穷 / 伪报 / 威慑等真实技能失效政策及其优先级。
```

---

# 5. Stage 6 正式范围

Stage 6 只建立以下最小能力：

```text
SkillDefinition
SkillRuntime
SkillResolver
SkillResolutionResult

最小 SkillTargetMode
最小 typed SkillEffectSpec

activation_rate 工程合同
Skill → ordered Effects 合同

BattleSystems 中的 SkillResolver 组合
synthetic / test-only skills
```

Stage 6 通过直接集成测试验证：

```text
SkillDefinition
↓
SkillRuntime
↓
SkillResolver
↓
Effect(s)
↓
EffectExecutor
↓
已有 BattleSystem
```

本阶段不要求 BattleEngine 自动运行任何技能。

---

# 6. Stage 6 明确 OUT OF SCOPE

以下能力全部不属于 Stage 6：

```text
真实战法目录
批量真实战法录入
官方战法参数全集

TriggerSystem
RuleHookSystem
完整 Timing System

RecoverySystem
持续伤害运行机制

完整 HitResolution
完整 Damage Modifier Pipeline

反击
群攻
连击
伤害重定向
分摊
分担
援护

完整 StateApplicationPolicy
洞察
控制免疫

完整 Skill disable policy
伪报
计穷
威慑

EquipmentRuntime

BattleReport
Replay

API
批量模拟
性能优化
```

也不实现其余 35 个尚未接入行为的官方状态。

Stage 6 可以复用当前已经实现的：

```text
先攻
遇袭
缴械
震慑
虚弱
```

其中 Stage 6 只需要用 `缴械` 验证：

```text
Skill
→ ApplyStateEffect
→ EffectExecutor
→ StateLifecycleSystem
```

不得借此顺手实现：

```text
计穷
伪报
威慑
```

---

# 7. SkillDefinition 精确职责

## 7.1 定义

`SkillDefinition` 表达：

```text
战法静态身份
静态发动率
静态目标需求
静态 Effect 生成规格
```

它不表达：

```text
当前是否失效
当前发动了几次
当前触发了几次
当前剩余次数
当前冷却
当前临时增减发动率
当前目标
当前 BattleContext
当前 BattleSystems
```

推荐：

```python
@dataclass(frozen=True, slots=True)
class SkillDefinition:
    skill_id: str
    name: str
    activation_rate: float
    target_mode: SkillTargetMode
    effect_specs: tuple[SkillEffectSpec, ...]
```

这是 Stage 6 推荐的最小字段集合。

## 7.2 字段审计

### `skill_id`

```text
Stage 6 是否需要：是
谁读取：SkillRuntime / SkillResolver / Effect.source_skill_id
静态还是运行态：静态
理由：建立稳定身份，并把 source_skill_id 传递到已有 Effect / DamageRequest / StateInstance 链。
```

### `name`

```text
Stage 6 是否需要：是
谁读取：调试、测试、未来展示
静态还是运行态：静态
理由：Definition 至少需要可读名称。
```

不同时建立：

```text
name
+
display_name
```

因为 Stage 6 没有两个不同消费者需要这两个字段。

### `activation_rate`

```text
Stage 6 是否需要：是
谁读取：SkillResolver
静态还是运行态：静态
理由：Stage 6 正式验证发动率 + RandomSystem + seed 确定性。
```

范围：

```text
0.0 <= activation_rate <= 1.0
```

### `target_mode`

```text
Stage 6 是否需要：是
谁读取：SkillResolver
静态还是运行态：静态
理由：Skill 不得直接选 Unit，Resolver 必须把目标意图交给 TargetSystem。
```

### `effect_specs`

```text
Stage 6 是否需要：是
谁读取：SkillResolver
静态还是运行态：静态
理由：核心代码不能按 skill_id / skill name 写具体技能分支，
      必须按通用 typed effect specification 生成已有 Effect。
```

约束：

```text
使用 tuple
至少 1 项
保持声明顺序
```

## 7.3 Stage 6 不加入的字段

以下字段全部 DEFER：

```text
category / skill_type
level
level_parameter_table
metadata
priority
timing
trigger_type
cooldown
charges
runtime_payload
custom_handler
callable
```

原因不是这些字段永远不需要，而是 Stage 6 当前没有合法消费者，或者其规则证据不足。

特别禁止：

```python
metadata: dict[str, Any]
params: dict[str, Any]
handler: Callable[..., ...]
```

作为绕过类型合同的逃生门。

---

# 8. SkillEffectSpec 最小合同

Stage 6 需要把“具体测试技能”与“通用解析器”分离。

因此不能写：

```python
if definition.skill_id == "synthetic.weapon_damage":
    ...
```

也不能写：

```python
if definition.name == "某战法":
    ...
```

推荐在 `skill_definition.py` 中建立最小 typed specification：

```python
@dataclass(frozen=True, slots=True)
class DamageSkillEffectSpec:
    damage_type: DamageType
    coefficient: float = 1.0


@dataclass(frozen=True, slots=True)
class ApplyStateSkillEffectSpec:
    state_id: str


SkillEffectSpec = DamageSkillEffectSpec | ApplyStateSkillEffectSpec
```

Stage 6 的 Resolver 只认识：

```text
DamageSkillEffectSpec
ApplyStateSkillEffectSpec
```

并将它们转换为：

```text
DamageEffect
ApplyStateEffect
```

它不认识任何真实战法名称或 ID。

## 8.1 为什么 Stage 6 不建立 RecoverSkillEffectSpec

`RecoverEffect` 当前仍然：

```text
DEFERRED
→ RECOVERY_SYSTEM_NOT_AVAILABLE
```

恢复并不是验证 Stage 6 Skill → Effect 链所必需。

因此 Stage 6 不需要为了“规格看起来齐全”加入恢复型 skill spec。

Stage 6 仍必须回归验证：

```text
RecoverEffect
→ DEFERRED
```

但 synthetic skills 不使用恢复效果。

## 8.2 为什么不建立通用脚本 / callable

禁止：

```text
SkillEffectSpec.execute()
SkillEffectSpec.build_effects(context)
callable effect factory
Python lambda skill handler
```

原因：这会把“具体战法行为”重新塞回数据对象，最终绕过核心边界。

---

# 9. SkillRuntime 精确职责

## 9.1 Stage 6 推荐模型

推荐：

```python
@dataclass(slots=True)
class SkillRuntime:
    definition: SkillDefinition
    owner_id: str
    enabled: bool = True
```

Stage 6 中：

```text
一个携带者的一项技能绑定
→ 一个 SkillRuntime
```

同一个 `SkillDefinition` 可以被多个 owner 使用，但每个 owner 的 runtime 必须是独立对象。

## 9.2 SkillRuntime 什么时候创建

Stage 6 当前没有 BattleFactory / SkillLoadout / SkillCatalog 装载层。

因此正式施工约定：

```text
真实项目未来：战斗初始化 / 队伍技能装载阶段创建
Stage 6 测试：测试夹具显式创建
```

Stage 6 不为了存放 SkillRuntime 而立即增加：

```text
BattleContext.skills
UnitRuntime.skills
SkillRegistry
```

这些容器需要真实装载、触发与技能槽语义后再设计。

## 9.3 `definition`

表示该运行实例绑定的静态定义。

它不是复制一份静态字段。

禁止：

```text
runtime.skill_id
runtime.name
runtime.activation_rate
```

再次独立保存并产生双重真相源。

## 9.4 `owner_id`

表示该战法属于哪个当前战斗单位。

Resolver 通过：

```text
context.get_unit(owner_id)
```

解析 owner。

Stage 6 不再额外增加：

```text
caster_id
source_id
```

因为当前 synthetic skill 中：

```text
owner = caster = Effect source
```

未来如果真实规则证明技能来源与当前施法者可能分离，再新增明确类型合同。

## 9.5 `enabled`

Stage 6 允许存在一个最小运行状态：

```text
enabled: bool
```

意义仅为：

> 当前这一个 SkillRuntime 是否允许进入一次 Stage 6 resolution attempt。

这不是完整 Skill Disable Policy。

Stage 6 不实现：

```text
计穷如何禁主动
伪报如何禁指挥 / 被动
威慑如何选一个战法失效
技能失效优先级
免疫 / 覆盖 / 恢复
```

`enabled` 的存在只是为了建立：

```text
runtime fact
≠
static definition
```

并验证：

```text
enabled = False
→ 不进行 activation RNG
→ 不进行 target RNG
→ 不产生 Effect
```

Stage 10 再建立真正的 Skill Enable / Disable Policy。

## 9.6 Stage 6 不加入的运行字段

全部 DEFER：

```text
activation_count
trigger_count
charges
cooldown
temporary_activation_modifier
temporary_target_modifier
runtime_level
runtime_params
runtime_data
metadata
```

特别禁止：

```python
runtime_data: dict[str, Any]
```

如果未来确实需要运行参数，必须建立新的强类型合同，而不是万能 mutable dict。

---

# 10. 关键设计一：SkillRuntime.resolve vs SkillResolver

## 方案 A：SkillRuntime 自己 resolve

概念：

```text
SkillRuntime.resolve(context, ...)
→ Effects
```

### 优点

```text
API 表面简单
调用层少
小型 demo 容易理解
```

### 缺点

```text
SkillRuntime 同时承担“保存事实”和“规则协调”
容易逐渐持有 TargetSystem / RandomSystem / BattleContext
未来 disabled / trigger / timing / target / condition 会继续堆进 runtime
测试 runtime 独立性困难
```

### 对 Stage 7 的影响

```text
TriggerSystem 最终需要调用一个越来越胖的 SkillRuntime
规则边界模糊
```

### 对 Stage 10 的影响

```text
Skill disable policy 很容易侵入 runtime.resolve 内部并变成大量状态判断
```

### 测试复杂度

```text
较低起步，较高长期
```

### 迁移成本

```text
未来拆 Resolver 成本较高
```

---

## 方案 B：独立 SkillResolver

概念：

```text
SkillDefinition
+
SkillRuntime
+
BattleContext
        ↓
SkillResolver
        ↓
SkillResolutionResult + ordered Effects
```

### 优点

```text
Definition = 静态数据
Runtime = 运行事实
Resolver = 规则协调
职责清晰
便于独立测试 RNG、目标和 Effect 生成
Stage 7 TriggerSystem 可以自然调用 Resolver
Stage 10 Skill disable policy 可以在明确政策层控制 runtime enabled / eligibility
```

### 缺点

```text
比 Runtime.resolve 多一个类型
需要明确依赖注入
```

### 对 Stage 7 的影响

```text
TriggerSystem 未来只负责“何时请求一次 resolution”
Resolver 继续负责“一次 resolution 如何解析”
兼容性好
```

### 对 Stage 10 的影响

```text
Skill disable policy 可以保持在独立政策 / trigger eligibility 层，
不需要把 SkillRuntime 变成状态规则引擎
```

### 测试复杂度

```text
略高于方案 A，但边界测试更直接
```

### 迁移成本

```text
低
```

## 推荐

```text
推荐方案 B：SkillResolver
```

Stage 6 不建立宽泛的“大 SkillSystem”。

原因：

```text
SkillSystem
```

这个名字容易让一个类同时承担：

```text
技能存储
触发
发动率
目标
Effect 生成
Effect 执行
事件
禁用政策
```

Stage 6 当前只需要“一次技能解析器”，因此 `SkillResolver` 的职责更精确。

---

# 11. SkillResolutionResult

Stage 6 推荐建立类型化解析结果。

建议放在：

```text
skill_resolver.py
```

而不是为了类型数量再单独创建 `skill_result.py`。

推荐：

```python
class SkillResolutionStatus(str, Enum):
    DISABLED = "DISABLED"
    NO_VALID_TARGET = "NO_VALID_TARGET"
    ACTIVATION_FAILED = "ACTIVATION_FAILED"
    RESOLVED = "RESOLVED"
```

以及不可变结果：

```python
@dataclass(frozen=True, slots=True)
class SkillResolutionResult:
    skill_id: str
    owner_id: str
    status: SkillResolutionStatus
    target_ids: tuple[str, ...]
    effects: tuple[Effect, ...]
```

要求：

```text
DISABLED
→ target_ids = ()
→ effects = ()

NO_VALID_TARGET
→ target_ids = ()
→ effects = ()

ACTIVATION_FAILED
→ target_ids = ()
→ effects = ()

RESOLVED
→ target_ids 非空（Stage 6 当前模式）
→ effects 非空
```

不要建立一个塞满：

```text
activated?
failed_reason?
rng_value?
target?
damage?
state?
```

的大型可空字段 Result。

Stage 6 不要求记录原始 RNG 浮点值。

---

# 12. 关键设计二：Skill Resolution 是否直接执行 EffectExecutor

## 方案 A：Resolver 只返回 Effects

```text
SkillResolver.resolve(...)
→ SkillResolutionResult.effects

调用方
→ EffectExecutor.execute(...)
```

### 优点

```text
Skill = 意图生成
EffectExecutor = 行为路由
边界最清楚
Resolver 不依赖底层 BattleSystem
Stage 7 TriggerSystem 可自由决定 Effects 的队列 / 执行时点
测试可以证明“resolve 后战场尚未改变”
```

### 缺点

```text
调用方需要显式多一步执行
```

### Stage 7 影响

```text
最佳
TriggerSystem 可把 resolution 与 execution 分层组合
```

### 测试复杂度

```text
低，并且可以直接验证无副作用
```

### 迁移成本

```text
低
```

---

## 方案 B：SkillSystem / Resolver 内部执行 EffectExecutor

```text
resolve
→ Effects
→ EffectExecutor
→ BattleSystem
```

### 优点

```text
调用接口短
一次调用即可看到战场变化
```

### 缺点

```text
解析和执行混合
Resolver 直接依赖 EffectExecutor
EffectExecutor 又依赖 DamageResolution / StateLifecycle
技能层开始知道底层执行链
未来 Trigger queue / reaction / replay / 延迟执行难以插入
```

### Stage 7 影响

```text
较差
TriggerSystem 很难只拿到意图而不立即产生副作用
```

### 测试复杂度

```text
较高，解析测试和执行测试耦合
```

### 迁移成本

```text
中到高
```

## 推荐

```text
推荐方案 A
```

正式边界：

```text
SkillResolver
= 产生 Effect

EffectExecutor
= 执行 Effect
```

`SkillResolver` 的构造函数中禁止出现：

```text
EffectExecutor
DamageSystem
DamageResolutionSystem
TroopSystem
StateLifecycleSystem
StateRegistry
```

---

# 13. 关键设计三：Skill target specification 最小模型

## 方案 A：预组合最小 TargetMode

Stage 6 只定义当前确实需要的：

```python
class SkillTargetMode(str, Enum):
    SINGLE_RANDOM_ENEMY = "SINGLE_RANDOM_ENEMY"
```

Resolver 将该 intent 映射为：

```text
TargetSystem.enemies(...)
→ 只查询合法候选，不消费 RNG

activation 成功后
→ TargetSystem.random_units(..., count=1)
```

### 优点

```text
最小
Stage 6 synthetic skills 足够
不会提前冻结复杂目标 DSL
TargetSystem 继续是唯一目标规则入口
当前 TargetSystem 已经足够，不要求新增 SkillTargetSystem
```

### 缺点

```text
以后增加己方、多目标、主将、最低兵力等需求时要扩展 enum / spec
```

### Stage 7 影响

```text
低风险
```

### 测试复杂度

```text
低
```

### 迁移成本

```text
低到中，可按真实需求扩展
```

---

## 方案 B：通用组合式 TargetQuery DSL

例如提前定义：

```text
relation
alive_only
include_self
count
selection_mode
position_filter
attribute_filter
priority
fallback
```

### 优点

```text
表面上通用
未来很多目标规则可能能表达
```

### 缺点

```text
当前没有真实规则证据支撑字段全集
容易把未知游戏规则冻结成错误 DSL
TargetSystem 和 SkillDefinition 之间形成过度抽象
测试矩阵迅速膨胀
```

### Stage 7 影响

```text
未知，可能反而限制真实 Trigger / target forcing 需求
```

### 测试复杂度

```text
高
```

### 迁移成本

```text
一旦字段语义错误，迁移成本高
```

## 推荐

```text
推荐方案 A：最小预组合 TargetMode
```

Stage 6 不建立 `SkillTargetSystem`。

Stage 6 也不扩展 TargetSystem，除非施工时发现当前公开方法无法满足：

```text
查询存活敌方候选
+
成功后随机选 1 个
```

按当前 `main`，已有：

```text
enemies()
random_units()
```

已经足够。

---

# 14. 关键设计四：技能分类现在做到什么深度

## 方案 A：现在加入 SkillCategory，仅作为标签

可能枚举：

```text
ACTIVE
ASSAULT
COMMAND
PASSIVE
FORMATION
TROOP
```

### 优点

```text
静态模型看起来更接近未来真实数据
Stage 10 伪报 / 计穷最终需要分类
```

### 缺点

```text
Stage 6 当前没有消费者
官方状态文本只证明部分类别概念存在，不证明完整分类全集和生命周期
容易出现“有字段但没有任何 runtime 语义”的半成品合同
```

### Stage 7 影响

```text
可能诱导 TriggerSystem 直接按未经研究的类别写时序
```

### 测试复杂度

```text
低，但测试只是形式验证，没有规则价值
```

### 迁移成本

```text
如果分类名 / 范围研究后不同，需要迁移数据
```

---

## 方案 B：Stage 6 完全 DEFER 分类字段

### 优点

```text
所有 Definition 字段都有真实 Stage 6 消费者
不伪装已经理解所有类别生命周期
避免 BattleEngine / Resolver 出现 category 分支
```

### 缺点

```text
未来真实目录接入时需要新增字段
```

### Stage 7 影响

```text
迫使 Stage 7 先研究 Timing / Trigger，再设计真正需要的 category 合同
```

### 测试复杂度

```text
最低
```

### 迁移成本

```text
低，新增字段优于修正错误字段
```

## 推荐

```text
推荐方案 B：Stage 6 不建立 SkillCategory / SkillType
```

需要明确区分：

```text
“真实游戏存在战法类别”
≠
“Stage 6 已经有足够证据冻结完整类别合同”
```

技能分类在 Stage 7 / Stage 10 / Stage 11 根据真实研究重新进入设计。

---

# 15. 关键设计五：BattleEngine 是否在 Stage 6 自动运行技能

## 方案 A：Stage 6 就接入 BattleEngine

可能做法：

```text
UNIT_ACTION
→ 先尝试主动技能
→ 再普通攻击
```

或：

```text
ROUND_START
→ 指挥 / 被动 / 阵法
```

### 优点

```text
demo 看起来更像真实战斗
```

### 缺点

```text
当前没有 Trigger / Timing 合同
会被迫猜主动、突击、指挥、被动、阵法、兵种的时点
BattleEngine 会开始认识技能类型或具体技能阶段
直接侵占 Stage 7 范围
```

### Stage 7 影响

```text
极差
Stage 7 需要拆掉 Stage 6 的临时时序
```

### 测试复杂度

```text
高
```

### 迁移成本

```text
高
```

---

## 方案 B：Stage 6 不接自动 timing，只做直接集成测试

```text
测试显式调用：
SkillResolver.resolve(...)
        ↓
拿到 ordered Effects
        ↓
逐个 EffectExecutor.execute(...)
```

### 优点

```text
只验证 Stage 6 真正需要证明的架构链
BattleEngine 保持冻结职责
不猜 timing
Stage 7 可以从干净接口开始设计 Trigger
```

### 缺点

```text
Stage 6 demo 不会自动展示技能发动
```

### Stage 7 影响

```text
最佳
```

### 测试复杂度

```text
低
```

### 迁移成本

```text
低
```

## 推荐

```text
推荐方案 B
```

Stage 6 禁止在 `BattleEngine` 中出现：

```python
if skill.type == ...
if skill.category == ...
if skill.skill_id == ...
```

Stage 6 也不让 Engine 调用：

```text
SkillResolver.resolve()
```

自动技能 timing 统一 DEFER TO STAGE 7。

---

# 16. SkillResolver 精确职责

`SkillResolver` 只负责“一次显式 resolution attempt”。

推荐依赖：

```text
TargetSystem
```

运行时通过：

```text
BattleContext.random
```

使用当前战斗的 `RandomSystem`。

它不依赖：

```text
EffectExecutor
DamageSystem
DamageResolutionSystem
TroopSystem
StateLifecycleSystem
StateRegistry
BattleSystems
EventBus 规则订阅
```

Stage 6 推荐解析步骤：

```text
1. 检查 SkillRuntime.enabled
2. 解析 owner 是否存在
3. 通过 TargetSystem 查询合法候选，不随机选择
4. 若无合法候选，返回 NO_VALID_TARGET
5. 处理 activation_rate
6. 若发动失败，返回 ACTIVATION_FAILED
7. 发动成功后，通过 TargetSystem 进行必要目标随机选择
8. 按 effect_specs 声明顺序生成 Effect
9. 返回 SkillResolutionResult
```

注意：

```text
Resolver 返回时
→ troops 不得改变
→ StateRegistry 不得改变
→ DAMAGE_* / STATE_* 事实不得因为 Resolver 本身被发布
```

真正战场变化只能发生在调用方随后执行：

```text
EffectExecutor.execute(...)
```

---

# 17. 发动率合同

## 17.1 静态数据与裁决职责

```text
SkillDefinition.activation_rate
= 静态发动概率

SkillResolver
= 判断本次 resolution attempt 是否发动成功

RandomSystem
= 唯一真正 RNG 来源
```

以下系统不得判断技能发动率：

```text
Effect
EffectExecutor
StateLifecycleSystem
DamageSystem
DamageResolutionSystem
TroopSystem
```

## 17.2 Stage 6 RNG 消耗节点

正式工程合同：

### `enabled = False`

```text
返回 DISABLED
不查询随机目标
不消费 activation RNG
不消费 target RNG
```

### 没有合法目标

```text
返回 NO_VALID_TARGET
不消费 activation RNG
不消费 target RNG
```

这是 Stage 6 的 D 级工程决定。

真实游戏是否存在“先发动、后发现无目标”的特殊技能：

```text
NEEDS_RESEARCH
```

### `activation_rate = 0.0`

```text
返回 ACTIVATION_FAILED
不调用 RandomSystem.chance()
```

### `activation_rate = 1.0`

```text
视为发动成功
不调用 RandomSystem.chance()
```

### `0.0 < activation_rate < 1.0`

```text
恰好调用一次：
context.random.chance(activation_rate)
```

### 发动失败

```text
不进行随机目标选择
```

### 发动成功

```text
需要随机选目标时
→ 只通过 TargetSystem
```

TargetSystem 当前已经保证：

```text
候选只有 1 个
→ 不消费 target RNG

选择数量等于全部候选
→ 不消费 target RNG
```

Stage 6 必须继续保持这一确定性语义。

## 17.3 为什么 0% / 100% 要特殊处理

当前 `RandomSystem.chance()` 对任意合法概率都会调用 `random()`。

因此 Stage 6 Resolver 若直接：

```python
context.random.chance(0.0)
context.random.chance(1.0)
```

会无意义地改变后续 RNG 序列。

Stage 6 明确选择：

```text
0% / 100%
→ 不消费 activation RNG
```

这是工程确定性合同 D，不冒充官方客户端内部实现事实。

## 17.4 同 seed 可复现

相同：

```text
seed
BattleContext 初始事实
SkillDefinition
SkillRuntime
resolution 调用顺序
```

必须得到相同：

```text
activation decision
target_ids
Effects 顺序和内容
```

---

# 18. “发动条件不满足”如何处理

Stage 6 当前正式存在的前置条件只有：

```text
runtime.enabled
合法目标存在
```

其他真实战法条件，例如：

```text
特定回合
受到攻击后
普攻后
兵力阈值
主将 / 副将身份
状态存在性
次数限制
技能类型失效
```

全部 DEFER。

这些条件未来由 Stage 7 Trigger / Timing 或 Stage 10 Skill Policy 进入设计。

在没有研究证据前，Stage 6 不冻结它们与发动率 RNG 的相对顺序。

---

# 19. 技能目标解析合同

Stage 6 的 SkillDefinition 只保存：

```text
Target Intent
```

SkillRuntime 不保存当前目标。

SkillRuntime 也不自己：

```text
context.random.choice(...)
context.random.sample(...)
```

正确链路：

```text
SkillDefinition.target_mode
        ↓
SkillResolver
        ↓
TargetSystem
        ↓
UnitRuntime candidate / selected target
```

当前 Stage 6 只支持：

```text
SINGLE_RANDOM_ENEMY
```

未知目标规则全部 DEFER：

```text
随机友军
包含自己 / 排除自己
全体敌军
随机 N 人
主将优先
副将优先
兵力最低
属性最高 / 最低
无差别目标
强制目标
挑拨
嘲讽
混乱
```

不得为了“将来可能需要”一次做出通用目标 DSL。

---

# 20. Effect 生成合同

Stage 6 的核心 API 语义必须成立：

```text
Skill Resolution
→ tuple[Effect, ...]
```

具体方法名可以在施工时采用：

```text
SkillResolver.resolve(...)
```

但概念不可改变。

## 20.1 DamageSkillEffectSpec

转换：

```text
DamageSkillEffectSpec
        ↓
DamageEffect(
    source_id = runtime.owner_id,
    target_id = selected target,
    damage_type = spec.damage_type,
    source_type = DamageSourceType.SKILL,
    coefficient = spec.coefficient,
    source_skill_id = definition.skill_id,
)
```

之后由调用方：

```text
EffectExecutor
→ DamageResolutionSystem
→ DamageSystem
→ TroopSystem
```

Skill 层不得直接引用后三者。

## 20.2 ApplyStateSkillEffectSpec

转换：

```text
ApplyStateSkillEffectSpec
        ↓
ApplyStateEffect(
    state_id = spec.state_id,
    owner_id = selected target,
    source_id = runtime.owner_id,
    source_skill_id = definition.skill_id,
)
```

之后由调用方：

```text
EffectExecutor
→ StateLifecycleSystem.apply
→ StateRegistry
```

Skill 层不得直接写状态。

---

# 21. 多个 Effect 的确定顺序

Stage 6 正式工程合同：

```text
SkillDefinition.effect_specs
= tuple

SkillResolver 生成 Effects
= 严格按 effect_specs declaration order
```

例如 synthetic 组合技能：

```text
DamageSkillEffectSpec
ApplyStateSkillEffectSpec
```

必须生成：

```text
DamageEffect
ApplyStateEffect
```

调用方逐个执行时：

```text
先伤害
后施加状态
```

这只是：

```text
Stage 6 synthetic skill 的 D 级工程确定性合同
```

不得写成：

> 所有官方真实战法的多个效果必然按文本声明顺序结算。

真实战法内部多段效果的官方顺序：

```text
NEEDS_RESEARCH
```

---

# 22. Skill 与 EffectExecutor 的边界

Stage 6 必须能通过测试证明：

```text
result = SkillResolver.resolve(...)
```

之后：

```text
目标 troops 未改变
StateRegistry 未改变
```

只有：

```text
for effect in result.effects:
    systems.effect_executor.execute(context, effect)
```

之后才允许产生真实战场副作用。

这条测试比单纯字符串搜索更重要，因为它直接证明：

```text
Skill resolution
≠
Effect execution
```

---

# 23. EventBus 边界

Stage 6 推荐：

```text
不新增 SKILL_ACTIVATED
不新增 SKILL_RESOLVED
```

原因：

```text
Stage 6 没有正式自动 timing
真实技能 activation / trigger 语义尚未研究
技能失效政策尚未建立
“activated”和“resolved”的精确事件时点仍会受 Stage 7 Trigger 设计影响
```

Stage 6 使用：

```text
SkillResolutionResult
```

作为解析层的可测试返回值即可。

已有：

```text
DAMAGE_DEALT
DAMAGE_PREVENTED
STATE_APPLIED
STATE_REMOVED
```

继续由已有底层系统发布。

Stage 6 不复制这些事件。

未来如果 Stage 7 确实需要：

```text
SKILL_ACTIVATED
SKILL_RESOLVED
```

必须重新回答：

```text
它记录的已经发生事实是什么？
谁发布？
在 RNG 前还是后？
在选目标前还是后？
是否包含 source_skill_id？
是否包含 target_ids？
失败是否发事件？
```

EventBus 仍不得订阅 `UNIT_ACTION` 后自行决定技能发动。

---

# 24. BattleEngine 边界

Stage 6 不修改 BattleEngine 的技能流程职责。

BattleEngine 继续只负责：

```text
阶段推进
回合推进
ActionSystem 调用
状态自然到期节点
胜负检查
流程事实事件
```

禁止：

```text
BattleEngine → SkillResolver
BattleEngine → EffectExecutor for skills
BattleEngine 根据 SkillCategory 分支
BattleEngine 根据 skill_id / name 分支
```

Stage 6 的完整技能链只在直接集成测试中显式验证。

自动 timing：

```text
DEFER TO STAGE 7
```

---

# 25. BattleSystems 是否接入 SkillResolver

推荐：

```text
是
```

原因：

```text
BattleSystems 当前已经是 BattleSystem / 规则组件的组合根
SkillResolver 需要共享已有 TargetSystem
把 Resolver 放入组合根可避免各调用方各自临时构造不同 TargetSystem
```

推荐新增：

```text
skill_resolver: SkillResolver = field(init=False)
```

构造：

```text
TargetSystem
→ SkillResolver
```

禁止：

```text
BattleSystems
→ SkillResolver(BattleSystems)
```

也禁止把：

```text
EffectExecutor
```

注入 `SkillResolver`。

推荐构造关系最终为：

```text
TargetSystem
→ SkillResolver

DamageSystem + TroopSystem
→ DamageResolutionSystem

DamageResolutionSystem + StateLifecycleSystem
→ EffectExecutor
```

技能解析与 Effect 执行在组合根中并列存在，但不互相持有。

---

# 26. RecoverEffect 边界

Stage 6 不建立 RecoverySystem。

因此必须继续保持：

```text
RecoverEffect
→ EffectExecutor
→ DeferredEffectResult
→ RECOVERY_SYSTEM_NOT_AVAILABLE
```

Stage 6 禁止：

```text
SkillResolver → TroopSystem.restore
SkillRuntime → TroopSystem.restore
```

Stage 6 synthetic skills 不需要恢复效果。

完整回归必须确认 Stage 5 的 RecoverEffect DEFER 语义未漂移。

---

# 27. 第一批 synthetic skills

这些技能只存在于：

```text
tests / test fixture
```

它们不是：

```text
官方真实战法
官方战法数据
未来正式 Skill Catalog
```

核心生产代码不得认识这些 skill_id 或 name。

## 27.1 Synthetic Weapon Damage

测试 ID 示例：

```text
synthetic.weapon_damage
```

定义：

```text
activation_rate = 1.0
target_mode = SINGLE_RANDOM_ENEMY

effect_specs:
1. DamageSkillEffectSpec(
     damage_type = WEAPON,
     coefficient = 测试固定值
   )
```

验证：

```text
SkillDefinition
→ SkillRuntime
→ SkillResolver
→ DamageEffect
→ EffectExecutor
→ DamageResolutionSystem
```

## 27.2 Synthetic Disarm

测试 ID 示例：

```text
synthetic.disarm
```

定义：

```text
activation_rate = 1.0
target_mode = SINGLE_RANDOM_ENEMY

effect_specs:
1. ApplyStateSkillEffectSpec(state_id = disarm)
```

验证：

```text
Skill
→ ApplyStateEffect
→ EffectExecutor
→ StateLifecycleSystem
```

## 27.3 Synthetic Damage And Disarm

测试 ID 示例：

```text
synthetic.damage_and_disarm
```

定义：

```text
effect_specs:
1. DamageSkillEffectSpec(...)
2. ApplyStateSkillEffectSpec(disarm)
```

验证：

```text
one Skill resolution
→ multiple Effects
→ declaration order preserved
```

## 27.4 Synthetic Probabilistic Skill

Stage 6 已经把：

```text
activation_rate
```

作为正式 SkillDefinition 字段。

因此必须有代表测试验证它的 runtime 语义。

建议增加：

```text
synthetic.probabilistic_damage
```

例如测试固定：

```text
activation_rate = 0.35
```

用途：

```text
same seed
→ same activation decisions

failed activation
→ no target RNG
→ no Effect

successful activation
→ deterministic target / Effects under same seed
```

---

# 28. 推荐文件结构

Stage 6 施工建议只新增三个生产文件：

```text
sgs_v2/battle_core/
├─ skill_definition.py
├─ skill_runtime.py
└─ skill_resolver.py
```

## `skill_definition.py`

建议包含：

```text
SkillTargetMode
DamageSkillEffectSpec
ApplyStateSkillEffectSpec
SkillEffectSpec
SkillDefinition
```

这样避免为了几个很小的静态类型建立：

```text
skill_type.py
skill_target_spec.py
skill_effect_spec.py
```

一堆只有十几行的抽象文件。

## `skill_runtime.py`

只包含：

```text
SkillRuntime
```

## `skill_resolver.py`

建议包含：

```text
SkillResolutionStatus
SkillResolutionResult
SkillResolver
```

Stage 6 不需要单独：

```text
skill_result.py
skill_system.py
skill_registry.py
skill_catalog.py
```

## 预计修改

```text
sgs_v2/battle_core/battle_systems.py
sgs_v2/battle_core/__init__.py
```

原则上不需要修改：

```text
engine.py
context.py
unit.py
events.py
target_system.py
random_system.py
effects.py
effect_executor.py
damage_system.py
damage_resolution_system.py
state_lifecycle_system.py
```

如果施工时确实需要修改这些 FROZEN 文件，必须明确说明：

```text
为什么现有接口不足
为什么是 Stage 6 必需最小变更
如何保证旧测试语义不漂移
```

---

# 29. 测试设计

建议新增：

```text
tests/test_skill_definition.py
tests/test_skill_runtime.py
tests/test_skill_resolver.py
tests/test_stage6_integration.py
tests/test_stage6_architecture.py
```

具体文件名可调整，但测试维度不得减少。

---

# 30. SkillDefinition 测试

至少覆盖：

```text
SkillDefinition 是 frozen dataclass
slots=True
skill_id 非空
name 非空
activation_rate 必须在 [0.0, 1.0]
effect_specs 非空
传入的 effect_specs 最终为 tuple

Definition 不持有 BattleContext
Definition 不持有 BattleSystems
Definition 不持有 EffectExecutor
Definition 不持有 callable handler
Definition 没有 metadata/runtime_data 万能 dict
```

还必须证明：

```text
两个 synthetic skills
可以只通过不同 Definition data
让同一个 Resolver 产生不同 Effects
```

而不是靠 skill_id 分支。

---

# 31. SkillRuntime 测试

至少覆盖：

```text
绑定 SkillDefinition
绑定 owner_id
默认 enabled = True
不同 owner 的 runtime 实例互相独立
同一个 Definition 可以被多个 Runtime 共享
修改一个 runtime.enabled 不影响另一个
```

结构测试必须确认没有：

```text
runtime_data: dict
metadata: dict
BattleContext 字段
BattleSystems 字段
TargetSystem 字段
EffectExecutor 字段
```

---

# 32. SkillResolver 单元测试

必须覆盖：

```text
100% skill
→ 不消费 activation RNG
→ 可以 RESOLVED

0% skill
→ 不消费 activation RNG
→ ACTIVATION_FAILED

0% skill
→ 不进行随机目标选择

0 < rate < 1
→ 恰好一次 activation chance

runtime.enabled = False
→ DISABLED
→ 不消费 activation RNG
→ 不消费 target RNG

没有合法目标
→ NO_VALID_TARGET
→ 不消费 activation RNG
→ 不消费 target RNG

activation failed
→ target_ids = ()
→ effects = ()

activation succeeded
→ target 只经 TargetSystem
→ effects 只由 typed specs 产生
```

RNG 消耗测试不要只比较“最终结果相同”。

推荐使用：

```text
可计数 RandomSystem test double
```

或者其他明确可观察调用次数的测试方法，分别记录：

```text
chance calls
choice/sample calls
```

但测试替身本身不得改变生产 RandomSystem 合同。

---

# 33. Skill → Damage 集成测试

流程：

```text
1. 创建 synthetic weapon damage Definition
2. 创建 SkillRuntime
3. SkillResolver.resolve()
4. 断言返回 DamageEffect
5. 在执行 Effect 前记录 target troops
6. 断言 target troops 尚未变化
7. EffectExecutor.execute(DamageEffect)
8. 断言 troops 下降
9. 断言走 DamageResolutionSystem 现有结果与事件链
```

必须证明：

```text
Skill 层没有直接调用 DamageSystem
Skill 层没有直接调用 DamageResolutionSystem
Skill 层没有直接调用 TroopSystem
```

最终链：

```text
Skill
→ DamageEffect
→ EffectExecutor
→ DamageResolutionSystem
→ DamageSystem
→ TroopSystem
```

---

# 34. Skill → State 集成测试

流程：

```text
1. 注册当前官方状态目录
2. 创建 synthetic disarm Definition
3. 创建 Runtime
4. SkillResolver.resolve()
5. 断言返回 ApplyStateEffect(disarm)
6. 执行 Effect 前断言 Registry 中没有 disarm
7. EffectExecutor.execute(ApplyStateEffect)
8. 断言 StateLifecycleSystem 成功施加 disarm
9. 断言 STATE_APPLIED 正确
```

必须证明：

```text
Skill 层不写 StateRegistry
Skill 层不调用 StateLifecycleSystem
```

最终链：

```text
Skill
→ ApplyStateEffect
→ EffectExecutor
→ StateLifecycleSystem
→ StateRegistry
```

---

# 35. Multi-effect 顺序测试

synthetic combination skill：

```text
DamageSkillEffectSpec
ApplyStateSkillEffectSpec(disarm)
```

必须断言 Resolver 返回：

```text
(
    DamageEffect,
    ApplyStateEffect,
)
```

调用方按 tuple 顺序执行后，应观察：

```text
DAMAGE_DEALT / DAMAGE_PREVENTED
在相应 STATE_APPLIED 之前
```

前提是本测试的 DamageEffect 实际进入相应伤害事件路径。

该事件顺序只验证 synthetic declaration order，不宣称真实战法通用顺序。

---

# 36. 架构静态测试

Stage 6 必须新增明确架构防回归测试。

## 36.1 禁止直接 Python random

继续验证：

```text
sgs_v2/battle_core/*.py
除 random_system.py 外
不得 import random
不得 from random import ...
```

Stage 6 新增 skill modules 也必须满足。

## 36.2 Skill modules 禁止导入底层执行系统

至少禁止：

```text
troop_system
damage_system
damage_resolution_system
state_registry
state_lifecycle_system
effect_executor
battle_systems
```

其中 `skill_resolver.py` 可以导入：

```text
context
target_system
effects
enums
skill_definition
skill_runtime
```

## 36.3 禁止直接写运行数据

架构测试应考虑检测：

```text
*.troops =
*.troops +=
*.troops -=
context.states.add(...)
context.states.remove(...)
```

## 36.4 优先 AST / import 级检测

Stage 5 曾发生过：

```text
静态源码测试把注释中的字符串当成真实违规调用
```

Stage 6 不应只写：

```python
assert "DamageSystem" not in source_text
```

这种容易误报的全文字符串扫描。

推荐：

```text
AST Import / ImportFrom 节点检查
AST Call / Attribute 节点检查
+
行为集成测试
```

如果必须用 `inspect.getsource()`：

```text
只检查明确类 / 函数范围
只匹配实际调用形态
不要把注释和文档字符串当成违规证据
```

---

# 37. BattleEngine 架构测试

继续确认 `BattleEngine` 不认识：

```text
SkillDefinition
SkillRuntime
SkillResolver
SkillTargetMode
DamageSkillEffectSpec
ApplyStateSkillEffectSpec
任何 synthetic skill ID / name
```

更重要的是行为上确认：

```text
BattleEngine.run()
```

不会因为 Stage 6 增加 resolver 而自动执行 synthetic skill。

---

# 38. Stage 1～5 回归要求

Stage 6 必须保持完整旧测试通过。

特别验证：

```text
普通攻击
DamageResolutionSystem
EffectExecutor
StateLifecycleSystem
StateRuntimeParams
先攻
遇袭
缴械
震慑
虚弱
RecoverEffect DEFERRED
```

必须继续保持：

```text
缴械
→ ACTION_BLOCKED

震慑
→ ACTION_BLOCKED

虚弱普通攻击
→ NORMAL_ATTACK
→ DAMAGE_PREVENTED

正常 DamageEffect
→ EffectExecutor
→ DamageResolutionSystem

RecoverEffect
→ DEFERRED
→ RECOVERY_SYSTEM_NOT_AVAILABLE
```

Stage 6 不允许为了新技能测试修改这些旧语义。

---

# 39. Stage 6 的 20 个必答问题

## 1. 为什么现在需要 Stage 6？

因为 Stage 5 已经建立 Effect 执行链，但还没有正式的“战法静态定义 + 战斗运行实例 + 一次技能解析”层。

## 2. Stage 6 解决哪个架构缺口？

解决：

```text
Game / Skill Data
→ SkillDefinition
→ SkillRuntime
→ Skill Resolution
→ Effect
```

中 Effect 之前的缺口。

## 3. 依赖哪些 Stage 1～5 FROZEN 能力？

主要依赖：

```text
BattleContext
TargetSystem
RandomSystem
Effect
EffectExecutor
DamageResolutionSystem
StateLifecycleSystem
```

## 4. 哪些旧系统不得破坏？

```text
BattleEngine
EventBus
TargetSystem
DamageSystem
DamageResolutionSystem
TroopSystem
StateRegistry
StateLifecycleSystem
RandomSystem
ActionSystem
NormalAttackSystem
ActionOrderSystem
```

## 5. SkillDefinition 的精确职责是什么？

不可变静态数据：身份、名称、发动率、最小目标 intent、typed effect specs。

## 6. SkillRuntime 的精确职责是什么？

保存某携带者当前战斗中的技能绑定与最小运行事实：Definition、owner、enabled。

## 7. 是否需要 SkillSystem / SkillResolver？

需要独立 `SkillResolver`；不建立大而全的 `SkillSystem`。

## 8. Skill 类型是否现在进入？

不进入。Stage 6 没有真实消费者，分类完整语义证据不足，DEFER。

## 9. 发动率保存在哪里？

`SkillDefinition.activation_rate`。

## 10. 发动率由谁裁决？

`SkillResolver`。

## 11. RNG 在哪里消费？

真正随机只能通过 `BattleContext.random -> RandomSystem`；目标随机只能通过 `TargetSystem`。

## 12. 技能目标由谁解析？

SkillDefinition 表达 intent，SkillResolver 协调，TargetSystem 执行候选查询和随机目标选择。

## 13. Skill 如何产生 Effect？

Resolver 按 typed `SkillEffectSpec` 转换成已有 `Effect`，不按具体 skill_id/name 分支。

## 14. 多个 Effect 如何保持确定顺序？

`effect_specs` 使用 tuple，Resolver 严格保留 declaration order。

## 15. Skill 与 EffectExecutor 的边界是什么？

SkillResolver 只返回 Effects；调用方随后显式调用 EffectExecutor。

## 16. Skill 与 EventBus 的边界是什么？

Stage 6 SkillResolver 不使用 EventBus 作为规则引擎，也不新增技能事件；底层 Effect 执行继续发布已有事实。

## 17. Skill 与 BattleEngine 的边界是什么？

Stage 6 BattleEngine 不自动运行技能，不认识技能分类和具体技能。

## 18. 哪些能力 DEFER 到 Stage 7+？

Trigger、Timing、Recovery、周期效果、Modifier、Reaction、Skill Disable、真实技能目录等全部延后。

## 19. 用哪些 synthetic skills 验证架构？

```text
synthetic.weapon_damage
synthetic.disarm
synthetic.damage_and_disarm
synthetic.probabilistic_damage
```

均为 TEST ONLY。

## 20. 如何证明没有出现 Skill → BattleSystem 第二套路径？

组合证明：

```text
1. AST/import 架构测试禁止 skill modules 导入底层执行系统；
2. Resolver 行为测试证明 resolve 后 troops / states 尚未变化；
3. 只有 EffectExecutor 执行后才发生 troops / states 变化；
4. Stage 1～5 旧边界测试继续全绿。
```

---

# 40. 已知事实

基于当前 `main`，以下是已确认项目事实：

```text
1. Stage 5 FROZEN 条件已经满足。

2. Effect 已经是不可变意图数据。

3. EffectExecutor 已经统一路由：
   DamageEffect → DamageResolutionSystem
   ApplyStateEffect → StateLifecycleSystem
   RemoveStateEffect → StateLifecycleSystem
   RecoverEffect → DEFERRED

4. DamageSourceType 已经包含 SKILL。

5. DamageEffect / DamageRequest / DamageResult 已经有 source_skill_id。

6. StateInstance / ApplyStateEffect 已经有 source_skill_id。

7. TargetSystem 已经有敌我查询和随机选择能力。

8. TargetSystem 已经具备“无必要时不消费目标 RNG”的工程语义。

9. RandomSystem.chance() 是合法概率入口，但 0% / 100% 调用仍会消费 RNG，
   因此 Stage 6 Resolver 必须在边界概率上短路。

10. BattleEngine 当前没有 Effect / Skill 具体逻辑。

11. EventBus 当前只记录 / 分发已发生事实。

12. BattleContext 当前没有技能注册表。

13. UnitRuntime 当前没有 skills 字段。

14. ActionSystem 当前只处理震慑门控后进入普通攻击，
    没有成熟的主动 / 突击 / 指挥 / 被动 timing 基础设施。
```

---

# 41. UNKNOWN / NEEDS_RESEARCH

以下问题 Stage 6 不猜：

```text
1. 真实完整 SkillCategory / SkillType 枚举。

2. 主动 / 突击 / 指挥 / 被动 / 阵法 / 兵种的完整生命周期。

3. 每类战法精确触发 / 发动 timing。

4. 真实游戏中“先检查合法目标还是先 roll 发动率”的精确顺序。

5. 真实游戏客户端对 0% / 100% 是否内部消耗随机序列。

6. 无合法目标时，某些特殊技能是否仍被视为“发动”。

7. owner 死亡 / 濒死 / 行动结束后的技能 eligibility。

8. 真实技能多目标选择顺序。

9. 真实技能多 Effect 的官方结算顺序。

10. 战法等级及参数表的正式数据结构。

11. activation count / trigger count / charges / cooldown 的真实语义。

12. 技能失效政策：计穷、伪报、威慑以及组合优先级。

13. SKILL_ACTIVATED / SKILL_RESOLVED 的最终事件语义与精确时点。

14. 真实战法 Catalog 数据来源和装载格式。
```

任何一个 E 级问题都不得通过 synthetic 测试结果反向“证明”为官方规则。

---

# 42. 风险清单

## 风险 1：SkillResolver 变成第二个 BattleEngine

控制：

```text
只处理一次显式 resolution attempt
不处理回合推进
不处理 trigger queue
不执行 Effect
```

## 风险 2：SkillRuntime 变成万能状态袋

控制：

```text
Stage 6 只允许 definition / owner_id / enabled
禁止 runtime_data / metadata 万能 dict
```

## 风险 3：EffectSpec 变成脚本语言

控制：

```text
只建立 Stage 6 真正需要的两个 typed spec
禁止 callable / execute / handler
```

## 风险 4：过早冻结技能分类

控制：

```text
Stage 6 不加入 SkillCategory
```

## 风险 5：过早冻结官方 target / RNG 顺序

控制：

```text
把 Stage 6 顺序明确标记为 D 工程合同
把真实游戏顺序标记 E NEEDS_RESEARCH
```

## 风险 6：BattleEngine timing 膨胀

控制：

```text
Stage 6 不自动运行技能
```

## 风险 7：EventBus 变成规则引擎

控制：

```text
Stage 6 不通过 EventBus 订阅触发技能
```

## 风险 8：架构测试误报注释

控制：

```text
优先 AST/import 级检查
+
行为测试
```

## 风险 9：BattleSystems 循环依赖

控制：

```text
SkillResolver 只注入 TargetSystem
不注入 BattleSystems / EffectExecutor
```

## 风险 10：为了“真实感”录入真实战法

控制：

```text
Stage 6 只允许 synthetic/test definitions
```

---

# 43. 推荐施工顺序

正式施工 Stage 6 时按以下顺序：

```text
Step 1
重新读取当时 main 最新 HEAD
确认 Stage 5 FROZEN 边界和 CI 仍成立

Step 2
建立 skill_definition.py
- SkillTargetMode
- typed SkillEffectSpec
- SkillDefinition

Step 3
建立 SkillDefinition tests

Step 4
建立 skill_runtime.py
- SkillRuntime

Step 5
建立 SkillRuntime tests

Step 6
建立 skill_resolver.py
- SkillResolutionStatus
- SkillResolutionResult
- SkillResolver

Step 7
完成 activation / target / RNG 单元测试

Step 8
建立 synthetic damage / disarm / combination / probabilistic definitions
仅放 tests / fixtures

Step 9
完成 Skill → Effect 无副作用测试

Step 10
完成 Skill → Effect → EffectExecutor → BattleSystem 集成测试

Step 11
BattleSystems 接入 SkillResolver

Step 12
__init__.py 暴露 Stage 6 公共类型

Step 13
新增 Stage 6 AST/import 架构测试

Step 14
完整 Stage 1～5 回归

Step 15
pytest -q

Step 16
python demo.py

Step 17
GitHub Actions

Step 18
独立 Stage 6 最终审计

Step 19
修复 BLOCKER / MAJOR

Step 20
再次审计
```

---

# 44. Stage 6 正式验收标准

只有以下全部满足，Stage 6 功能施工才可认为完成：

```text
✅ SkillDefinition 静态不可变合同建立

✅ SkillDefinition 只包含 Stage 6 有真实消费者的字段

✅ SkillRuntime 战斗运行合同建立

✅ SkillRuntime 不使用万能 mutable dict

✅ 一个携带者的一项技能绑定可拥有独立 SkillRuntime

✅ SkillResolver 独立于 SkillRuntime

✅ Skill resolution 产生 Effect，而不执行 Effect

✅ synthetic damage skill
   → DamageEffect
   → EffectExecutor
   → DamageResolutionSystem

✅ synthetic state skill
   → ApplyStateEffect
   → EffectExecutor
   → StateLifecycleSystem

✅ synthetic multi-effect skill
   → ordered Effects

✅ synthetic probabilistic skill
   → activation_rate
   → RandomSystem determinism

✅ disabled runtime
   → 不消费无意义 RNG

✅ 无合法目标
   → 不消费 activation / target RNG

✅ 0% / 100% activation
   → 不消费 activation RNG

✅ same seed
   → same activation decisions
   → same target decisions
   → same Effects

✅ Skill 层不直接修改 troops

✅ Skill 层不直接写 StateRegistry

✅ Skill 层不直接调用 DamageSystem

✅ Skill 层不直接调用 DamageResolutionSystem

✅ Skill 层不直接调用 StateLifecycleSystem

✅ Skill 层不直接调用 EffectExecutor

✅ 所有随机经过 RandomSystem

✅ 目标随机只经过 TargetSystem

✅ BattleEngine 没有具体技能判断

✅ BattleEngine Stage 6 不自动运行技能

✅ EventBus 没变成规则引擎

✅ Stage 6 不新增未经定义的技能事实事件

✅ RecoverEffect 仍 DEFERRED
   → RECOVERY_SYSTEM_NOT_AVAILABLE

✅ 无真实战法硬编码

✅ 无真实 skill_id / name 分支

✅ 无 SkillCategory lifecycle 猜测

✅ 无 Stage 7+ 范围膨胀

✅ Stage 1～5 回归通过

✅ pytest 全绿

✅ demo success

✅ GitHub Actions success

✅ 最终独立审计无 BLOCKER / MAJOR
```

---

# 45. Stage 6 FROZEN 规则

`STAGE6.md` 写完不等于 Stage 6 FROZEN。

正确流程：

```text
Stage 6 规划完成
↓
STAGE6.md
↓
STAGE6_BUILD_PROMPT.md
↓
施工
↓
pytest
↓
demo
↓
GitHub Actions
↓
独立 Stage 6 最终审计
↓
修复
↓
再次审计
↓
最终审计文件进入 main
↓
main CI success
↓
Stage 6 FROZEN
```

在真实生产代码、真实测试和真实 CI 都存在之前，禁止创建：

```text
STAGE6_FINAL_AUDIT.md
```

---

# 46. Stage 6 完成后的预期架构

```text
Game / Skill Data
        ↓
SkillDefinition
        ↓
SkillRuntime
        ↓
SkillResolver
  ┌─────┴──────────┐
  ↓                ↓
TargetSystem   RandomSystem
  └─────┬──────────┘
        ↓
ordered Effect(s)
        ↓
[future Trigger / caller orchestration]
        ↓
EffectExecutor
   /           \
  ↓             ↓
DamageResolution  StateLifecycleSystem
  ↓                   ↓
DamageSystem       StateRegistry
  ↓
TroopSystem
```

BattleEngine 仍然：

```text
通用流程推进器
```

EventBus 仍然：

```text
事实记录器
```

Stage 6 最终必须能够通过代码和测试共同证明：

> Skill 只表达和产生“希望发生什么”；真正的战斗副作用仍由 EffectExecutor 之后的 BattleSystem 决定。

这条合同冻结后，Stage 7 Trigger / Timing / Recovery 才有可靠接入点。
