# 三国志战略版战斗模拟器 V2 · Stage 5 Effect 实施指南

> Stage 4 已完成最终封版审计并进入 `FROZEN`。Stage 5 的目标不是实现真实战法，而是在不破坏 Stage 2/3/4 边界的前提下建立通用 Effect 表达与执行链，并为未来状态运行参数建立类型安全合同。

---

# 1. Stage 5 目标

Stage 5 建立：

```text
Effect
    ↓
EffectExecutor
    ↓
BattleSystem
```

并正式解决两个结构问题：

```text
1. 上层规则如何表达“希望发生什么”，而不直接操作底层系统。
2. StateInstance 如何携带不可变、类型安全、可审计的运行参数，而不是万能 dict。
```

Stage 5 第一批正式支持：

```text
DamageEffect
ApplyStateEffect
RemoveStateEffect
RecoverEffect（仅定义意图，执行暂缓）
```

同时抽取共享：

```text
DamageResolutionSystem
```

避免普通攻击和 DamageEffect 各自复制一套：

```text
DamageSystem
→ TroopSystem
→ DAMAGE_PREVENTED / DAMAGE_DEALT
→ UNIT_DEFEATED
```

---

# 2. Stage 5 明确不做什么

本阶段不实现：

```text
SkillDefinition
SkillRuntime
真实战法
TriggerSystem
RecoverySystem
持续伤害触发
急救 / 休整 / 禁疗 / 倒戈 / 攻心
Modifier Pipeline
Hit Resolution
状态叠加 / 刷新统一政策
真实状态参数全集
```

Stage 5 也不让 `BattleEngine` 主动执行 Effect。

未来 SkillRuntime / TriggerSystem 负责产生 Effect；Stage 5 只证明 Effect 可以通过统一执行器安全调用已有 BattleSystem。

---

# 3. 不可破坏的冻结边界

必须继续保持：

```text
TargetSystem
= 目标选择入口

AttributeSystem
= 最终属性入口

DamageSystem
= 理论伤害计算入口

TroopSystem
= 唯一兵力修改入口

VictorySystem
= 胜负判定入口

RandomSystem
= 唯一战斗 RNG

StateLifecycleSystem
= 状态正式写入口

StateRegistry
= 状态存储与查询中心

BattleEngine
= 通用流程推进器

EventBus
= 事实记录器，不是规则引擎
```

禁止 EffectExecutor 直接：

```python
target.troops -= damage
context.states.add(...)
context.states.remove(...)
import random
```

禁止具体战法名称进入 Effect / BattleSystem。

---

# 4. Effect 的设计原则

Effect 是“规则意图”，不是行为对象。

Effect 应满足：

```text
不可变
只保存执行所需数据
不持有 BattleContext
不持有 BattleSystem
不执行副作用
不选择目标
不调用 RNG
```

推荐使用：

```python
@dataclass(frozen=True, slots=True)
```

EffectExecutor 只负责类型路由：

```text
DamageEffect
→ DamageResolutionSystem

ApplyStateEffect
→ StateLifecycleSystem.apply

RemoveStateEffect
→ StateLifecycleSystem.remove

RecoverEffect
→ DEFERRED
```

不要让 EffectExecutor 逐渐变成另一个 BattleEngine。

---

# 5. DamageEffect

DamageEffect 至少表达：

```text
source_id
target_id
damage_type
source_type
coefficient
source_skill_id
```

执行链固定为：

```text
DamageEffect
    ↓
EffectExecutor
    ↓
DamageResolutionSystem
    ↓
DamageSystem.calculate
    ↓
DamageResult
    ↓
TroopSystem / DAMAGE_PREVENTED
```

EffectExecutor 不直接调用 `TroopSystem`。

---

# 6. 为什么必须抽取 DamageResolutionSystem

Stage 4 当前普通攻击内部已经协调：

```text
DamageSystem.calculate()
        ↓
DamageResult
        ↓
prevented ?
├─ yes → DAMAGE_PREVENTED
└─ no
   ↓
TroopSystem.apply_damage()
   ↓
DAMAGE_DEALT
   ↓
必要时 UNIT_DEFEATED
```

如果 DamageEffect 再复制同一逻辑，将产生两套伤害落地路径。

Stage 5 必须改为：

```text
NormalAttackSystem ─┐
                    ├→ DamageResolutionSystem
EffectExecutor ─────┘
                         ↓
                    DamageSystem
                         ↓
                    TroopSystem
                         ↓
                      EventBus
```

职责：

```text
DamageSystem
= 只计算理论 DamageResult

DamageResolutionSystem
= 协调理论伤害、实际扣兵与伤害事实事件

NormalAttackSystem
= 普攻门控、目标选择、NORMAL_ATTACK 事实

EffectExecutor
= Effect 类型路由
```

`NORMAL_ATTACK` 仍由 NormalAttackSystem 发布，不属于 DamageResolutionSystem。

---

# 7. DamageResolutionSystem 事件规则

若 `DamageResult.prevented`：

```text
不调用 TroopSystem.apply_damage
发布 DAMAGE_PREVENTED
```

否则：

```text
TroopSystem.apply_damage
→ DAMAGE_DEALT
→ 若目标死亡，发布 UNIT_DEFEATED
```

必须保持 Stage 4 虚弱语义：

```text
NORMAL_ATTACK
→ DAMAGE_PREVENTED
```

并保持正常攻击：

```text
NORMAL_ATTACK
→ DAMAGE_DEALT
→ 可选 UNIT_DEFEATED
```

---

# 8. ApplyStateEffect

ApplyStateEffect 表达：

```text
state_id
owner_id
source_id
source_skill_id
expires_round
expires_phase
runtime_params
```

执行必须走：

```text
EffectExecutor
→ StateLifecycleSystem.apply
→ StateRegistry
→ STATE_APPLIED
```

EffectExecutor 不得直接写 Registry。

---

# 9. RemoveStateEffect

第一版只使用明确的：

```text
instance_id
```

执行：

```text
EffectExecutor
→ StateLifecycleSystem.remove
→ STATE_REMOVED
```

Stage 5 不新增“按 state_id 批量移除”“驱散全部控制”等尚未研究的策略。

---

# 10. RecoverEffect 为什么暂缓执行

当前虽然存在：

```python
TroopSystem.restore()
```

但后续恢复规则需要统一处理：

```text
禁疗
急救
休整
倒戈
攻心
恢复修正
恢复事实事件
```

这些属于未来 RecoverySystem。

因此 Stage 5 可以定义 `RecoverEffect` 意图合同，但 EffectExecutor 必须返回：

```text
DEFERRED
```

且：

```text
不修改兵力
不直接调用 TroopSystem.restore
```

这样可以证明 Effect 模型可扩展，同时不提前绕过未来 RecoverySystem。

---

# 11. 状态运行参数合同

Stage 3 的 StateInstance 已正确保存：

```text
owner
source
source_skill
time
expiration
```

但未来状态还需要参数，例如：

```text
概率
倍率
比例
次数
层数
伤害系数
恢复系数
关联目标
共享组
```

Stage 5 禁止直接加入：

```python
payload: dict[str, Any]
```

作为 StateInstance 的万能参数容器。

正式合同：

```text
StateRuntimeParams
= 不可变参数类型的基类

EmptyStateRuntimeParams
= 无参数状态默认参数

未来每种参数结构
= 定义独立 frozen dataclass 子类
```

例如未来可以出现：

```python
@dataclass(frozen=True, slots=True)
class SomeStateParams(StateRuntimeParams):
    coefficient: float
    charges: int
```

但 Stage 5 不提前猜测 35 个未实现状态的完整参数表。

---

# 12. StateDefinition 参数 schema

`StateDefinition` 增加静态 schema：

```text
runtime_params_type
```

默认：

```text
EmptyStateRuntimeParams
```

含义：

> 这种状态实例允许携带哪一种参数结构。

这属于静态数据合同，不是行为逻辑。

StateLifecycleSystem.apply 必须验证：

```text
runtime_params
isinstance(..., definition.runtime_params_type)
```

不匹配时拒绝施加。

因此：

```text
StateDefinition
= 定义参数结构

StateInstance
= 保存本次实际参数值

BattleSystem
= 未来解释这些参数如何影响规则
```

State 仍然不执行行为。

---

# 13. StateInstance 参数要求

StateInstance 新增：

```text
runtime_params: StateRuntimeParams
```

要求：

```text
不可变
类型明确
不包含行为
可序列化为审计事件
```

Stage 3 已有调用必须保持兼容：

```text
未显式传 runtime_params
→ EmptyStateRuntimeParams()
```

但当 Definition 明确要求自定义参数类型时：

```text
未提供参数
→ 拒绝施加
```

---

# 14. 状态事件中的运行参数

STATE_APPLIED / STATE_REMOVED / STATE_EXPIRED 的事件 payload 应继续包含生命周期字段，并新增可审计表示：

```text
runtime_params_type
runtime_params
```

这里的 dict 只是 EventBus 的序列化事实，不是状态运行时合同，因此不违反禁止万能 payload 的规则。

同样输入下必须保持事件内容可复现。

---

# 15. EffectResult

Effect 执行结果必须类型安全，不使用一个塞满可空字段的万能结果对象。

建议：

```text
DamageEffectResult
ApplyStateEffectResult
RemoveStateEffectResult
DeferredEffectResult
```

统一类型别名：

```text
EffectExecutionResult
```

DamageEffectResult 包含共享 `DamageResolutionResult`。

RecoverEffect 返回 DeferredEffectResult，并明确原因：

```text
RECOVERY_SYSTEM_NOT_AVAILABLE
```

---

# 16. BattleSystems 接入

Stage 5 后 BattleSystems 应新增：

```text
DamageResolutionSystem
EffectExecutor
```

推荐构造依赖：

```text
DamageSystem
+ TroopSystem
→ DamageResolutionSystem

DamageResolutionSystem
+ StateLifecycleSystem
→ EffectExecutor

TargetSystem
+ DamageResolutionSystem
→ NormalAttackSystem
```

这样普通攻击与 Effect 共用同一伤害落地通道。

---

# 17. BattleEngine 边界

Stage 5 不修改 BattleEngine 的流程职责。

BattleEngine 不应出现：

```text
EffectExecutor.execute(...)
DamageEffect
ApplyStateEffect
RemoveStateEffect
RecoverEffect
```

原因：当前还没有 SkillRuntime / TriggerSystem 决定 Effect 在什么时机产生。

Stage 5 的集成测试直接调用 EffectExecutor 即可。

---

# 18. RNG 边界

Effect / EffectExecutor 不得直接使用 RNG。

DamageEffect 的基础伤害随机仍然：

```text
DamageSystem
→ WeaponBaseDamageFormula / StrategyBaseDamageFormula
→ context.random
```

ApplyStateEffect 第一版也不做概率判定。

未来“35% 概率施加状态”属于 Skill / Trigger / Rule 层，不属于 StateLifecycleSystem 或 ApplyStateEffect 本身。

---

# 19. Stage 5 测试要求

至少新增：

```text
tests/test_state_runtime_params.py
tests/test_damage_resolution_system.py
tests/test_effect_executor.py
```

必须覆盖：

## State Runtime Params

```text
默认 EmptyStateRuntimeParams 兼容旧状态
自定义 frozen params 可以保存到 StateInstance
Definition schema 与 runtime params 匹配时可施加
类型不匹配时拒绝
未提供必需自定义 params 时拒绝
状态事件记录 params type + values
多实例仍可携带不同参数并共存
```

## DamageResolutionSystem

```text
普通伤害实际通过 TroopSystem 扣兵
虚弱伤害仍为 0 且不调用 TroopSystem
DAMAGE_DEALT / DAMAGE_PREVENTED 正确
击杀仍发布 UNIT_DEFEATED
DamageSystem.calculate 单独调用仍不修改 troops
```

## EffectExecutor

```text
DamageEffect 走共享 DamageResolutionSystem
ApplyStateEffect 走 StateLifecycleSystem
RemoveStateEffect 走 StateLifecycleSystem
RecoverEffect 返回 DEFERRED 且不修改 troops
EffectExecutor 不直接消费 RNG
Effect 对象不可变
BattleEngine 不认识具体 Effect 类型
```

还必须验证普通攻击迁移后 Stage 4 事件顺序与行为不变。

---

# 20. 推荐文件

新增：

```text
sgs_v2/battle_core/effects.py
sgs_v2/battle_core/effect_result.py
sgs_v2/battle_core/effect_executor.py
sgs_v2/battle_core/state_runtime_params.py
sgs_v2/battle_core/damage_resolution_system.py
```

修改：

```text
state_definition.py
state_instance.py
state_lifecycle_system.py
normal_attack_system.py
battle_systems.py
__init__.py
```

以及相关 Stage 3 / Stage 4 测试期望。

---

# 21. Stage 5 架构红线

禁止：

```text
Effect 修改 UnitRuntime
Effect 修改 StateRegistry
Effect 直接调用 BattleSystem
EffectExecutor 自己计算伤害公式
EffectExecutor 自己修改 troops
EffectExecutor 自己选择目标
EffectExecutor 直接调用 Python random
RecoverEffect 绕过未来 RecoverySystem
StateRuntimeParams 使用 dict[str, Any] 作为正式合同
StateRuntimeParams 内包含 callable / 行为对象
BattleEngine 认识具体 Effect
```

---

# 22. 推荐实施顺序

```text
Step 1
写并审计 STAGE5.md

Step 2
StateRuntimeParams 基础合同

Step 3
StateDefinition / StateInstance / StateLifecycleSystem 接入参数 schema

Step 4
参数合同测试

Step 5
抽取 DamageResolutionSystem

Step 6
NormalAttackSystem 迁移到共享伤害落地通道

Step 7
共享伤害结算回归测试

Step 8
定义 Effect / EffectResult

Step 9
实现 EffectExecutor

Step 10
EffectExecutor 测试

Step 11
BattleSystems / __init__ 接入

Step 12
完整 Stage 1/2/3/4 回归

Step 13
pytest -q

Step 14
python demo.py

Step 15
GitHub Actions

Step 16
Stage 5 最终审计
```

---

# 23. Stage 5 完成标准

Stage 5 功能施工完成必须满足：

```text
✅ Stage 4 仍保持 FROZEN 边界
✅ StateRuntimeParams 类型安全且不可变
✅ StateDefinition 定义参数 schema
✅ StateInstance 保存实际参数
✅ StateLifecycleSystem 验证参数类型
✅ 状态事件可审计参数

✅ DamageResolutionSystem 成为共享伤害落地协调层
✅ NormalAttackSystem 不再复制扣兵/伤害结果事件逻辑
✅ DamageEffect 与普通攻击共用伤害落地通道

✅ ApplyStateEffect 只经 StateLifecycleSystem
✅ RemoveStateEffect 只经 StateLifecycleSystem
✅ RecoverEffect 明确 DEFERRED，不绕过 RecoverySystem

✅ Effect 不执行行为
✅ EffectExecutor 只负责路由
✅ BattleEngine 不认识具体 Effect
✅ RandomSystem 仍是唯一 RNG
✅ TroopSystem 仍是唯一兵力写入口
✅ EventBus 仍只记录事实

✅ Stage 1/2/3/4 回归全部通过
✅ pytest -q 全绿
✅ demo.py 正常
✅ GitHub Actions success
```

---

# 24. Stage 5 完成后的架构

```text
Future SkillRuntime / TriggerSystem
            ↓
          Effect
            ↓
      EffectExecutor
       /          \
      ↓            ↓
DamageResolution  StateLifecycleSystem
      ↓                 ↓
DamageSystem         StateRegistry
      ↓
TroopSystem

Shared:
BattleContext
RandomSystem
EventBus
```

Stage 5 完成时我们应该能证明：

> 上层规则已经可以用纯数据 Effect 表达伤害和状态变化，而不侵入底层 BattleSystem；状态实例也已经拥有可扩展但不失控的运行参数合同。

完成 Stage 5 后，下一阶段才进入 SkillDefinition / SkillRuntime。