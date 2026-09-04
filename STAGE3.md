# 三国志战略版战斗模拟器 V2 · Stage 3 BattleState 实施指南

> 本文是 Stage 3 的正式施工指南。
>
> 目标不是立刻实现“缴械、技穷、震慑、先攻”等具体状态，而是先建立一套稳定、可查询、可过期、可复现、可被各 BattleSystem 使用的通用 BattleState 基础框架。
>
> Stage 2 已封版。Stage 3 不得反向破坏 Stage 2 已确定的目标、属性、伤害、兵力、胜负和随机边界。

---

# 1. Stage 3 的目标

Stage 3 要完成以下基础能力：

```text
StateDefinition
      ↓
StateInstance
      ↓
StateRegistry
      ↓
StateLifecycleSystem
      ↓
BattleContext
      ↓
BattleEngine / BattleSystem 查询和驱动
      ↓
EventBus 记录状态事实
```

完成后，系统必须能够回答：

```text
这种状态是什么？
某个单位当前有哪些状态？
某个状态是谁施加的？
它来自哪个战法？
它什么时候加入？
它什么时候过期？
它现在是否仍然存在？
状态加入、移除、过期是否有结构化事件？
同样输入下状态实例编号和生命周期是否可复现？
```

Stage 3 的最终成果是“状态基础设施可用”，不是“具体状态效果已经实现”。

---

# 2. Stage 3 明确不做什么

本阶段不要实现：

```text
DisarmState / 缴械
SilenceState / 技穷
StunState / 震慑
FirstStrikeState / 先攻
AttributeModifierState
DamageReductionState
会心
奇谋
ActiveSkillSystem
Effect
SkillRuntime
具体战法
```

也不要在 Stage 3 中提前写：

```python
if state.state_id == "disarm":
    ...
```

或者：

```python
unit.can_attack = False
unit.is_stunned = True
unit.has_first_strike = True
```

Stage 3 只建立“状态存在、状态查询、状态生命周期”基础能力。

具体状态如何影响 BattleSystem，属于 Stage 4。

---

# 3. Stage 2 不能被破坏的架构边界

Stage 3 开发期间必须继续保持：

```text
TargetSystem
= 唯一目标选择入口

AttributeSystem
= 最终属性统一读取入口

DamageSystem
= 理论伤害统一计算入口

TroopSystem
= 唯一兵力修改入口

VictorySystem
= 胜负判定入口

RandomSystem
= 唯一随机源

BattleEngine
= 只负责流程推进和系统调用
```

禁止为了状态功能写出：

```python
target.troops -= damage
```

```python
target.attack += 30
```

```python
if skill.name == "...":
```

```python
import random
```

状态系统必须建立在 Stage 2 之上，而不是绕开 Stage 2。

---

# 4. 核心设计原则

整个 Stage 3 必须遵循：

> State 只表达“一个持续存在的战斗事实”。
>
> BattleSystem 决定“这个事实会怎样影响战斗机制”。

例如未来的缴械：

```text
StateRegistry 中存在 disarm
        ↓
NormalAttackSystem 查询
        ↓
决定本次不能执行普通攻击
```

而不是：

```text
缴械状态被施加
        ↓
直接修改 unit.can_attack
```

同理，未来先攻应该由 ActionOrderSystem 查询状态，震慑应该由 ActionSystem 查询状态，属性状态应该由 AttributeSystem 查询状态。

State 自身不应该直接执行这些系统规则。

---

# 5. Stage 3 推荐新增文件

建议新增：

```text
sgs_v2/battle_core/state_definition.py
sgs_v2/battle_core/state_instance.py
sgs_v2/battle_core/state_registry.py
sgs_v2/battle_core/state_lifecycle_system.py
```

并修改：

```text
sgs_v2/battle_core/context.py
sgs_v2/battle_core/battle_systems.py
sgs_v2/battle_core/engine.py
sgs_v2/battle_core/events.py
sgs_v2/battle_core/__init__.py
```

建议新增测试：

```text
tests/test_state_registry.py
tests/test_state_lifecycle.py
tests/test_stage3_integration.py
```

不要把所有状态代码塞进一个 `states.py` 巨型文件。

---

# 6. StateDefinition 应该是什么

`StateDefinition` 表示一种状态的静态定义。

它回答：

> “这种状态是什么？”

建议第一版保持最小化：

```python
@dataclass(frozen=True, slots=True)
class StateDefinition:
    state_id: str
    name: str
```

必要时可以增加不包含行为的静态标签，例如：

```python
tags: frozenset[str] = frozenset()
```

但 Stage 3 不要把具体系统逻辑写进去。

错误示例：

```python
StateDefinition(
    state_id="disarm",
    affected_system="NormalAttackSystem",
    disable_normal_attack=True,
)
```

Stage 3 不允许这样做。

`StateDefinition` 不应该保存：

```text
owner_id
source_id
当前剩余回合
施加回合
过期回合
source_skill_id
```

这些属于 StateInstance。

---

# 7. StateInstance 应该是什么

`StateInstance` 表示“一场具体战斗中真实存在的一次状态实例”。

建议第一版字段：

```python
@dataclass(frozen=True, slots=True)
class StateInstance:
    instance_id: str
    state_id: str

    owner_id: str
    source_id: str | None
    source_skill_id: str | None

    applied_round: int
    applied_phase: str

    expires_round: int | None = None
    expires_phase: str | None = None
```

字段语义：

```text
instance_id
= 本次状态实例的唯一 ID

state_id
= 对应 StateDefinition.state_id

owner_id
= 当前状态挂在哪个单位身上

source_id
= 谁造成了这个状态

source_skill_id
= 如果状态来自战法，记录来源战法 ID

applied_round
= 状态加入时所在回合

applied_phase
= 状态加入时所在阶段

expires_round / expires_phase
= 明确的绝对过期锚点
```

`source_id` 允许为 `None`，用于未来可能存在的全局规则或无单位来源状态。

`source_skill_id` 也允许为 `None`。

---

# 8. 生命周期必须使用“绝对过期锚点”

Stage 3 不建议使用：

```python
remaining_rounds -= 1
```

原因是这种模型很容易产生：

```text
施加当回合算不算？
ROUND_START 减还是 ROUND_END 减？
先减再生效还是先生效再减？
不同状态是不是会各自拥有一套计时规则？
```

Stage 3 应使用：

```text
expires_round
+
expires_phase
```

作为绝对过期锚点。

例如：

```python
expires_round=4
expires_phase="ROUND_START"
```

含义必须固定为：

> 状态一直保持有效，直到战斗进入第 4 回合 ROUND_START 生命周期节点；在该回合正式执行 ROUND_START 逻辑之前，由 StateLifecycleSystem 将其移除。

再例如：

```python
expires_round=3
expires_phase="ROUND_END"
```

含义：

> 状态保持有效直到第 3 回合结束；ROUND_END 的常规事实完成后，由 StateLifecycleSystem 处理过期。

---

# 9. Stage 3 不负责解释“持续 N 回合”

这一点非常重要。

Stage 3 只提供：

```text
明确的 applied 时间
明确的 expires 时间
```

但不要在 Stage 3 中擅自把游戏文本：

```text
“持续 2 回合”
```

固定解释成某一种过期算法。

原因是：

```text
主动战法中途施加
指挥效果战前施加
回合开始施加
回合结束施加
自身行动后施加
```

可能存在不同游戏语义。

Stage 4 / Effect / Skill 层在游戏规则被验证后，负责把：

```text
持续 N 回合
```

翻译成明确的：

```text
expires_round + expires_phase
```

这样 StateLifecycleSystem 本身就不用认识具体战法文案。

---

# 10. expires_round / expires_phase 的约束

建议定义：

```text
两个都为 None
→ 永久状态，直到显式移除

两个都存在
→ 有明确过期锚点

只存在其中一个
→ 非法
```

创建 StateInstance 时应验证。

还应验证：

```text
expires_round >= applied_round
```

Stage 3 第一版只建议正式支持：

```text
ROUND_START
ROUND_END
```

作为自动过期节点。

不要一开始就允许：

```text
UNIT_ACTION_START
UNIT_ACTION_END
```

因为这些阶段一回合中会重复多次，并且还涉及“哪个单位的行动”这一额外维度。

需要“持续若干次自身行动”之类规则时，再在后续阶段扩展生命周期模型，不要现在假装已经解决。

---

# 11. StateRegistry 的职责

`StateRegistry` 是一场战斗中的状态存储与查询中心。

它只负责：

```text
保存 StateDefinition
保存 StateInstance
根据条件查询
删除实例
生成稳定实例编号所需的内部序号
```

它不负责：

```text
决定某状态能不能叠加
决定状态效果
决定什么时候施加
决定什么时候刷新
发布战斗事件
修改 UnitRuntime
```

这些属于其他层。

---

# 12. StateRegistry 推荐 API

第一版建议至少提供：

```python
registry.register_definition(definition)

registry.get_definition(state_id)

registry.add(instance)

registry.get(instance_id)

registry.remove(instance_id)

registry.has(
    owner_id=...,
    state_id=...,
)

registry.find(
    owner_id=None,
    state_id=None,
    source_id=None,
)

registry.states_of(owner_id)
```

其中：

```text
has()
= 返回 bool

find()
= 返回满足条件的状态实例列表

states_of()
= 返回某单位当前全部状态实例
```

返回结果必须是副本或不可变结果，不能让调用方拿到内部容器然后绕过 Registry 修改。

---

# 13. StateRegistry 必须保证确定性

项目已有核心原则：

```text
same configuration + same seed = same result
```

因此状态实例不能直接使用随机 UUID：

```python
uuid.uuid4()
```

也不能依赖 Python 全局随机数生成 ID。

推荐由 StateRegistry 维护单调递增序号：

```text
state-000001
state-000002
state-000003
```

或者等价的确定性 instance_id。

这样：

```text
相同战斗流程
→ 相同状态应用顺序
→ 相同 instance_id
→ 相同 EventBus 记录
```

状态查询结果也要保持稳定顺序。

推荐按：

```text
注册/应用 sequence
```

排序，而不是依赖任意 set 顺序。

---

# 14. StateDefinition 的注册规则

同一个 `state_id` 只能注册一次。

例如：

```python
StateDefinition("test_state", "测试状态")
```

注册后，再注册另一个相同 `state_id` 的定义应报错。

不要 silently overwrite。

因为如果 Definition 被悄悄替换，运行中的 StateInstance 就会指向含义不稳定的定义。

---

# 15. StateLifecycleSystem 的职责

`StateLifecycleSystem` 是状态生命周期唯一正式写入口。

推荐职责：

```text
申请状态
验证 owner/source
生成 instance_id
构造 StateInstance
写入 StateRegistry
发布 STATE_APPLIED

显式移除状态
从 StateRegistry 删除
发布 STATE_REMOVED

处理生命周期节点
找到到期状态
删除
发布 STATE_EXPIRED
```

生产代码中应尽量避免直接：

```python
context.states.add(...)
context.states.remove(...)
```

正式流程应走：

```text
StateLifecycleSystem
        ↓
StateRegistry
```

Registry 是存储层，LifecycleSystem 是状态变更入口。

---

# 16. StateLifecycleSystem 推荐 API

建议第一版提供：

```python
apply(
    context,
    *,
    state_id: str,
    owner_id: str,
    source_id: str | None = None,
    source_skill_id: str | None = None,
    expires_round: int | None = None,
    expires_phase: str | None = None,
) -> StateInstance
```

显式移除：

```python
remove(
    context,
    instance_id: str,
) -> StateInstance
```

生命周期处理：

```python
expire_at(
    context,
    *,
    round_no: int,
    phase: str,
) -> list[StateInstance]
```

`apply()` 必须验证：

```text
state_id 已注册
owner_id 存在
source_id 如果不为 None，则必须存在
expires_round / expires_phase 合法
```

---

# 17. Stage 3 不定义叠加 / 刷新规则

第一版 Registry 应允许：

```text
同一 owner
同一 state_id
存在多个不同 instance_id
```

不要在 Stage 3 擅自决定：

```text
同类状态是否覆盖
是否刷新持续时间
是否叠加层数
不同来源是否共存
```

这些是具体状态规则。

Stage 4 在实现真实状态时，再决定：

```text
STACK
REPLACE
REFRESH
UNIQUE_PER_SOURCE
UNIQUE_PER_OWNER
```

如果 Stage 3 现在就强行做统一规则，很可能以后发现缴械、属性增减、持续伤害根本不是同一种叠加语义。

---

# 18. BattleContext 接入方式

`StateRegistry` 属于“一场战斗的运行态”，应该放进 BattleContext。

推荐：

```python
@dataclass(slots=True)
class BattleContext:
    ...
    states: StateRegistry = field(default_factory=StateRegistry)
```

最终 BattleContext 类似：

```text
BattleContext
├─ units
├─ event_bus
├─ random
├─ states
├─ current_round
├─ current_phase
├─ ended
└─ result
```

不要把状态存储在：

```text
NormalAttackSystem
ActionSystem
DamageSystem
```

也不要直接把几十个状态 bool 塞进 UnitRuntime。

---

# 19. BattleSystems 接入方式

`BattleSystems` 中加入：

```python
state_lifecycle_system: StateLifecycleSystem
```

它和其他 BattleSystem 一样由 BattleSystems 统一组合。

推荐最终结构：

```text
BattleSystems
├─ AttributeSystem
├─ TargetSystem
├─ TroopSystem
├─ VictorySystem
├─ StateLifecycleSystem
├─ ActionOrderSystem
├─ DamageSystem
├─ NormalAttackSystem
└─ ActionSystem
```

Stage 3 暂时不要求其他系统真正查询具体状态。

---

# 20. BattleEngine 应如何接入生命周期

BattleEngine 仍然不能认识：

```text
disarm
stun
first_strike
silence
```

BattleEngine 只能在通用生命周期节点调用：

```python
state_lifecycle_system.expire_at(...)
```

推荐第一版只接入两个明确节点：

## ROUND_START

建议顺序：

```text
进入 ROUND_START phase
        ↓
StateLifecycleSystem.expire_at(ROUND_START)
        ↓
发布 ROUND_STARTED
        ↓
其他回合开始逻辑
```

这样标记为“第 N 回合 ROUND_START 过期”的状态，在本回合正式开始前就已经不存在。

## ROUND_END

建议顺序：

```text
进入 ROUND_END phase
        ↓
发布 ROUND_ENDED
        ↓
StateLifecycleSystem.expire_at(ROUND_END)
        ↓
继续胜负检查 / 下一回合
```

这样标记为“第 N 回合 ROUND_END 过期”的状态在第 N 回合结束前保持有效。

无论采用何种具体代码布局，测试必须固定事件与过期顺序，不能靠口头约定。

---

# 21. EventBus 新增状态事件

建议加入：

```text
STATE_APPLIED
STATE_REMOVED
STATE_EXPIRED
```

Stage 3 不需要 `STATE_REFRESHED`，因为本阶段不定义刷新规则。

未来 Stage 4 确定刷新语义后再增加。

---

# 22. STATE_APPLIED 事件建议字段

建议 payload 至少包含：

```text
instance_id
state_id
owner_id
source_id
source_skill_id
applied_round
applied_phase
expires_round
expires_phase
```

`actor_id` 可以使用 source_id。

`target_id` 可以使用 owner_id。

如果 source_id 为 None，actor_id 也允许为 None。

---

# 23. STATE_REMOVED 与 STATE_EXPIRED

显式移除：

```text
STATE_REMOVED
```

自然到期：

```text
STATE_EXPIRED
```

不要把两者混成一个模糊事件。

两种事件至少应记录：

```text
instance_id
state_id
owner_id
source_id
```

EventBus 只记录事实。

不要让事件监听器承担：

```text
真正删除状态
真正恢复普攻
真正修改属性
```

这些都不属于 EventBus。

---

# 24. Stage 3 测试状态

Stage 3 不要用缴械或震慑作为基础框架验收对象。

建议测试中定义：

```python
StateDefinition(
    state_id="test_state",
    name="测试状态",
)
```

这个状态没有任何游戏效果。

用它只验证：

```text
Definition 注册
        ↓
Instance 创建
        ↓
Registry 查询
        ↓
生命周期持续
        ↓
到期
        ↓
自动移除
        ↓
EventBus 事件正确
```

如果一个没有游戏效果的测试状态都能完成完整生命周期，就说明状态框架本身是成立的。

---

# 25. test_state_registry.py 应覆盖什么

至少覆盖：

```text
StateDefinition 可以注册

重复 state_id 被拒绝

StateInstance 可以加入 Registry

可以通过 instance_id 查询

可以通过 owner_id 查询

可以通过 state_id 查询

可以通过 source_id 查询

has(owner_id, state_id) 正常工作

remove(instance_id) 正常工作

删除未知 instance_id 的行为明确

同类状态的多个实例可以共存

查询结果顺序稳定
```

---

# 26. test_state_lifecycle.py 应覆盖什么

至少覆盖：

```text
apply() 会验证 owner_id

apply() 会验证 source_id

apply() 会验证 StateDefinition 已注册

状态实例 ID 是确定性的

永久状态不会自动过期

ROUND_START 过期正常

ROUND_END 过期正常

过期状态从 Registry 删除

显式 remove 正常

STATE_APPLIED 正确发出

STATE_REMOVED 正确发出

STATE_EXPIRED 正确发出
```

---

# 27. test_stage3_integration.py 应覆盖什么

至少覆盖：

```text
BattleContext 默认拥有 StateRegistry

BattleSystems 拥有 StateLifecycleSystem

BattleEngine 在 ROUND_START 调用生命周期处理

BattleEngine 在 ROUND_END 调用生命周期处理

同样战斗流程下 instance_id 一致

同样配置 + seed 下 EventBus 状态事件一致

状态系统不会修改 troops

状态系统不会修改 attack / defense / intelligence / speed

BattleEngine 不包含具体 state_id 判断
```

---

# 28. 必须增加的静态架构检查

测试中可以增加简单源码检查，确保生产代码没有出现明显倒退。

例如检查：

```text
BattleEngine 不出现：
"disarm"
"stun"
"silence"
"first_strike"
```

以及：

```text
state_lifecycle_system.py
不直接修改 target.troops
```

不要把静态字符串检查当成全部架构测试，但可以作为低成本防线。

---

# 29. Stage 3 与 RandomSystem 的关系

StateRegistry instance_id 不需要随机数。

StateLifecycleSystem 也不应该为了生成实例编号消耗 RandomSystem。

原因：

```text
状态 ID 是基础设施编号
不是战斗随机事件
```

只有真正的游戏规则需要随机时，才允许消耗 RandomSystem。

例如未来“35%概率施加震慑”中的 35% 判定属于 Effect / Skill 层，而不是 StateLifecycleSystem。

---

# 30. StateRegistry 不应该主动修改 BattleContext.units

Registry 只保存状态实例引用信息，例如：

```text
owner_id="b1"
```

它不应该保存一个可变 UnitRuntime 引用然后私下操作。

需要单位对象时：

```python
context.get_unit(owner_id)
```

由真正负责该规则的 BattleSystem 获取。

这样可以避免状态存储层和战斗单位运行态过度耦合。

---

# 31. 为什么不把状态直接挂成 UnitRuntime 字段

不要变成：

```python
unit.is_disarmed
unit.is_silenced
unit.is_stunned
unit.has_first_strike
unit.damage_reduction
unit.attack_bonus
```

因为随着战法增加，UnitRuntime 会不断膨胀。

更重要的是，这种设计无法优雅表达：

```text
两个不同来源的同类状态
不同持续时间
来源战法
多实例
状态生命周期
状态事件
未来的驱散或刷新
```

所以 UnitRuntime 继续只负责单位运行态基础数据。

持续规则统一进入 StateRegistry。

---

# 32. 为什么 StateRegistry 不应该决定具体效果

错误架构：

```python
if state_id == "disarm":
    owner.can_attack = False
elif state_id == "stun":
    owner.can_act = False
```

这种代码最终会把所有战斗规则堆进 Registry。

正确方向：

```text
StateRegistry
只回答：
“这个状态存在吗？”

BattleSystem
回答：
“如果存在，会怎样影响当前机制？”
```

Stage 4 中：

```text
NormalAttackSystem
→ 查询 Disarm

ActionSystem
→ 查询 Stun

ActionOrderSystem
→ 查询 FirstStrike

AttributeSystem
→ 查询 AttributeModifier

DamageSystem
→ 查询 DamageReduction
```

这才是 V2 的核心解耦方向。

---

# 33. Stage 3 推荐实施顺序

不要四个文件一起乱写。

推荐严格按以下顺序：

```text
Step 1
StateDefinition
        ↓
Step 2
StateInstance
        ↓
Step 3
StateRegistry
        ↓
Step 4
StateRegistry 单元测试
        ↓
Step 5
BattleContext 接入 StateRegistry
        ↓
Step 6
StateLifecycleSystem
        ↓
Step 7
EventBus 状态事件
        ↓
Step 8
StateLifecycle 单元测试
        ↓
Step 9
BattleSystems 接入 StateLifecycleSystem
        ↓
Step 10
BattleEngine 接入 ROUND_START / ROUND_END 生命周期节点
        ↓
Step 11
Stage 3 集成测试
        ↓
Step 12
完整 pytest + demo
```

每完成一步先保持测试通过，再进入下一步。

---

# 34. 推荐第一批提交拆分

为了方便审计，建议不要一个 commit 塞完全部 Stage 3。

可以拆成：

```text
feat: add battle state definitions and instances

feat: add deterministic state registry

test: cover state registry behavior

feat: add state lifecycle system

feat: publish state lifecycle events

feat: integrate state registry into battle context

feat: integrate state lifecycle into battle flow

test: cover stage3 state lifecycle integration

docs: document stage3 battle state framework
```

这样如果某一步出现问题，定位会容易很多。

---

# 35. Stage 3 最终目标架构

Stage 3 完成后，建议形成：

```text
BattleEngine
      ↓
BattleSystems
      │
      ├─ StateLifecycleSystem
      │          ↓
      │     StateRegistry
      │          ↓
      │     StateInstance
      │          ↓
      │     StateDefinition
      │
      ├─ ActionOrderSystem
      ├─ ActionSystem
      ├─ NormalAttackSystem
      ├─ TargetSystem
      ├─ AttributeSystem
      ├─ DamageSystem
      ├─ TroopSystem
      └─ VictorySystem

Shared:
BattleContext
RandomSystem
EventBus
```

其中：

```text
BattleContext.states
→ 当前战斗状态存储

StateLifecycleSystem
→ 状态加入 / 删除 / 到期

EventBus
→ 记录状态事实

其他 BattleSystem
→ Stage 4 开始查询真实状态规则
```

---

# 36. Stage 3 完成后的代码形态示例

测试代码可以类似：

```python
definition = StateDefinition(
    state_id="test_state",
    name="测试状态",
)

context.states.register_definition(definition)

instance = systems.state_lifecycle_system.apply(
    context,
    state_id="test_state",
    owner_id="b1",
    source_id="a1",
    expires_round=3,
    expires_phase="ROUND_START",
)

assert context.states.has(
    owner_id="b1",
    state_id="test_state",
)
```

当战斗进入：

```text
Round 3 / ROUND_START
```

之后：

```python
assert not context.states.has(
    owner_id="b1",
    state_id="test_state",
)
```

同时 EventBus 中应能看到：

```text
STATE_APPLIED
STATE_EXPIRED
```

这就是 Stage 3 的核心验收场景。

---

# 37. Stage 3 封版验收标准

以下项目必须全部通过，Stage 3 才能封版。

## 数据模型

```text
✅ StateDefinition 存在且只保存静态定义

✅ StateInstance 存在且记录 owner/source/source_skill/time

✅ 有明确 expires_round / expires_phase

✅ 无 remaining_rounds 到处分散递减
```

## Registry

```text
✅ StateRegistry 是当前战斗唯一状态存储中心

✅ 支持 definition 注册

✅ 支持 instance 添加 / 删除 / 查询

✅ 支持 owner/state/source 查询

✅ 同类状态多实例可共存

✅ 查询顺序确定

✅ instance_id 确定性生成
```

## Lifecycle

```text
✅ StateLifecycleSystem 是正式状态变更入口

✅ apply 正常

✅ remove 正常

✅ ROUND_START 自动过期正常

✅ ROUND_END 自动过期正常

✅ 永久状态不会自动过期
```

## BattleContext / BattleEngine

```text
✅ BattleContext 拥有 states

✅ BattleSystems 拥有 StateLifecycleSystem

✅ BattleEngine 只调用通用生命周期接口

✅ BattleEngine 不认识任何具体状态名称
```

## EventBus

```text
✅ STATE_APPLIED

✅ STATE_REMOVED

✅ STATE_EXPIRED

✅ EventBus 只记录事实，不执行规则
```

## 架构边界

```text
✅ 状态系统不直接修改 troops

✅ 状态系统不直接修改 attack / defense / intelligence / speed

✅ UnitRuntime 不增加大量具体状态 bool

✅ RandomSystem 不被用于生成状态实例 ID

✅ 不出现 if skill.name == ...

✅ 不实现具体状态效果
```

## 测试

```text
✅ pytest -q 全部通过

✅ 现有 Stage 2 测试全部继续通过

✅ demo.py 继续正常运行

✅ GitHub Actions 通过
```

---

# 38. Stage 3 完成后不要立刻写具体战法

Stage 3 封版后进入 Stage 4。

Stage 4 用少量真实状态验证不同系统接口：

```text
FirstStrikeState
→ ActionOrderSystem

DisarmState
→ NormalAttackSystem

SilenceState
→ ActiveSkillSystem

StunState
→ ActionSystem

AttributeModifierState
→ AttributeSystem

DamageReductionState
→ DamageSystem
```

这些状态的作用不是为了堆内容，而是验证：

> BattleState 是否真的能通过不同 BattleSystem 改变规则，而无需让具体战法进入底层系统。

Stage 4 验证通过之后，才进入 Effect 和 SkillRuntime 的进一步建设。

---

# 39. Stage 3 最终完成定义

Stage 3 真正完成时，应该达到：

```text
我们已经拥有一个通用状态容器，
但还没有把任何具体游戏状态硬编码进底层。

状态有定义。
状态有实例。
状态有来源。
状态有持有者。
状态有确定性的生命周期。
状态可以统一查询。
状态加入和离开都有事件。
BattleEngine 只负责通用生命周期节点。
BattleSystem 未来可以各自查询状态并解释规则。
```

如果完成 Stage 3 后仍然可以在完全不知道“缴械、震慑、先攻是什么”的情况下运行全部状态框架测试，那么这一阶段的架构就基本做对了。

---

# 40. Stage 3 开发时的最终红线

任何 Stage 3 实现如果开始出现下面这些代码，应立即停止并重新检查设计：

```python
if state.state_id == "disarm":
```

```python
if skill.name == "...":
```

```python
unit.can_attack = False
```

```python
unit.is_stunned = True
```

```python
unit.attack += modifier
```

```python
unit.troops -= damage
```

```python
uuid.uuid4()
```

```python
import random
```

Stage 3 的任务不是实现更多游戏内容。

Stage 3 的任务是：

# 建立一个足够干净、确定、可扩展的 BattleState 基础框架，让后面的每一种状态都不需要重新发明生命周期和存储机制。
