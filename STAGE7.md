# 三国志战略版战斗模拟器 V2 · Stage 7 Trigger / Rule Hook / Recovery 实施规范

> 本文是 Stage 7 的正式规划与未来施工边界。它建立在当前 `main` 的 Stage 6 FROZEN 基线上。
> 本文不是施工结果，也不是 FINAL AUDIT。任何 Stage 7 生产代码施工前，都必须再次读取最新 `main` 并完成独立设计审计。

---

# 0. 当前基线

Stage 7 规划时重新确认的 `main` HEAD：

```text
15bde039fd4521a36f76224731e82cceb9846c19
```

对应提交：

```text
docs: mark Stage 6 frozen
```

当前正式状态：

```text
Stage 1 基础运行模型       回归稳定
Stage 2 BattleSystem      FROZEN
Stage 3 BattleState       稳定
Stage 4 官方状态接入       FROZEN
Stage 5 Effect            FROZEN
Stage 6 Skill Runtime     FROZEN
Stage 7                   规划阶段
```

Stage 6 已具备：

```text
SkillDefinition
→ SkillRuntime
→ SkillResolver
→ ordered Effect(s)
→ EffectExecutor
→ BattleSystem
```

且 `STAGE6_FINAL_AUDIT.md` 已完成独立最终审计，Stage 6 实现与审计均已进入 `main`，对应 main CI 成功。

如果 Stage 7 实际施工时 `main` 已变化，施工者必须重新确认 Stage 6 冻结边界仍成立，以新的 HEAD 作为实际施工基线。

---

# 1. Stage 7 为什么现在需要做

Stage 1～6 已经解决：

```text
战斗流程
基础 BattleSystem
状态存储与生命周期
官方状态静态目录
Effect 意图与统一执行
Skill 静态定义 / 运行实例 / 显式解析
```

但目前仍缺少两个关键能力：

```text
1. 战斗流程中的明确规则触发节点。
2. 正式恢复兵力结算系统。
```

因此当前还无法正确表达：

```text
每回合触发
武将行动时触发
周期伤害
周期恢复
禁疗
未来的伤害后恢复 / 反应式机制
```

Stage 7 的核心架构缺口是：

```text
BattleEngine / BattleSystem
        ↓
explicit Rule Hook
        ↓
TriggerSystem
        ↓
ordered Effect(s)
        ↓
EffectExecutor
        ↓
BattleSystem
```

同时补上：

```text
RecoverEffect
→ RecoverySystem
→ TroopSystem.restore
```

---

# 2. Stage 7 最高架构原则

Stage 7 必须保持：

```text
EventBus
= 已发生事实的记录 / 分发器
≠ 规则引擎

RuleHook
= 战斗规则层主动发出的明确规则节点

TriggerSystem
= 读取当前 BattleState / hook context
  并产生 ordered Effects

RuleHookSystem
= 触发协调层：TriggerSystem → EffectExecutor

EffectExecutor
= Effect 类型路由

RecoverySystem
= 恢复规则与恢复阻止政策

TroopSystem
= 唯一兵力写入口
```

禁止：

```text
EventBus subscribe → 自动执行状态规则
StateInstance.execute()
StateRuntimeParams.execute()
TriggerSystem 直接扣兵
TriggerSystem 直接恢复兵力
TriggerSystem 直接写 StateRegistry
TriggerSystem 自己计算基础伤害公式
TriggerSystem import random
RecoverySystem 直接 target.troops += ...
```

---

# 3. Stage 7 依赖的冻结能力

必须复用：

```text
BattleEngine
BattleContext
BattleSystems
StateRegistry
StateLifecycleSystem
StateRuntimeParams
Effect
EffectExecutor
DamageResolutionSystem
DamageSystem
TroopSystem
RandomSystem
EventBus
```

以及 Stage 6：

```text
SkillDefinition
SkillRuntime
SkillResolver
```

不得以 Stage 7 为理由重新设计 SkillRuntime 或把具体战法逻辑塞进 TriggerSystem。

---

# 4. 证据等级

Stage 7 的所有真实规则继续按：

```text
A = 当前官方接口 / 官方文本
B = 项目方明确确认
C = 用户提供战法数据、战报、逆向或测试证据
D = 工程设计决定
E = UNKNOWN / NEEDS_RESEARCH
```

权威优先级：

```text
当前官方接口证据
> 项目已确认规则
> 高质量战法 / 战报研究
> 工程设计决定
> 推测
```

禁止把 D 写成官方规则。

---

# 5. 当前 Stage 7 相关证据

当前官方状态目录明确：

```text
burn / 灼烧
= 每回合持续造成伤害

flood / 水攻
poison / 中毒
rout / 溃逃
sandstorm / 沙暴
= 拥有该状态的武将行动时受到伤害

rebellion / 叛逃
= 每回合受到伤害，且无视防御

first_aid / 急救
= 受到伤害时恢复兵力

recuperation / 休整
= 每回合恢复一次兵力

weapon_lifesteal / 倒戈
= 造成兵刃伤害时按伤害量恢复自身

strategy_lifesteal / 攻心
= 造成谋略伤害时按伤害量恢复自身

healing_ban / 禁疗
= 无法恢复兵力
```

`research/state_catalog_v1/STATE_CATALOG_V1.md` 还提供了战法描述 / 战报级研究：

```text
灼烧 / 水攻 / 中毒 / 沙暴
→ 高证据持续伤害

倒戈
→ 兵刃伤害后恢复

攻心
→ 谋略伤害后恢复

禁疗
→ 恢复兵力结算阶段阻止
```

但以下规则仍不能凭当前资料完整冻结：

```text
持续状态同名多实例的覆盖 / 刷新 / 最高来源政策
持续伤害精确 tick 相对事件顺序
持续伤害是否快照来源属性
来源死亡后持续状态的计算方式
休整精确发生在回合哪个节点
急救具体恢复公式
倒戈 / 攻心使用 requested damage 还是 actual damage
禁疗对所有吸血 / 急救交互的完整事件顺序
叛逃“无视防御”的正式 Damage Pipeline 位置
```

以上必须标记 NEEDS_RESEARCH，而不是用经验补齐。

---

# 6. Stage 7 正式范围

Stage 7 第一版正式建设：

```text
RuleHook 数据合同
TriggerSystem
RuleHookSystem
RecoveryRequest / RecoveryResult
RecoverySystem
RecoverEffect → RecoverySystem 正式接入
恢复事实事件
周期 Damage / Recovery StateRuntimeParams
ROUND_START / UNIT_ACTION_START 最小显式 hook
确定性 trigger ordering
Stage 7 synthetic trigger tests
官方状态证据门槛与可接入子集
```

Stage 7 不要求一次解决所有后续反应式机制。

---

# 7. RuleHook 最小模型

Stage 7 不建立几十个空 timing enum。

第一版只建立当前有消费者的节点：

```text
ROUND_START
UNIT_ACTION_START
```

推荐使用不可变强类型 hook：

```text
RoundStartHook
UnitActionStartHook
```

而不是：

```python
hook_payload: dict[str, Any]
```

概念：

```text
RoundStartHook
- round_no

UnitActionStartHook
- round_no
- actor_id
```

未来：

```text
AFTER_DAMAGE
AFTER_NORMAL_ATTACK
BEFORE_RECOVERY
AFTER_RECOVERY
```

只有出现合法消费者时再加入。

---

# 8. 为什么 Stage 7 第一版不直接加入 AFTER_DAMAGE Hook

`first_aid / 急救`、`weapon_lifesteal / 倒戈`、`strategy_lifesteal / 攻心` 都属于：

```text
一次 Damage Resolution
→ 产生新的 Recovery 行为
```

这已经进入“一个行为产生更多行为”的 reaction chain。

当前普通攻击伤害路径和 DamageEffect 路径都复用 `DamageResolutionSystem`，但 `EffectExecutor` 又依赖 `DamageResolutionSystem`。

如果为了赶 Stage 7 直接让：

```text
DamageResolutionSystem
→ TriggerSystem
→ EffectExecutor
→ DamageResolutionSystem
```

会形成明显循环依赖，并提前引入递归触发风险。

因此 Stage 7 v1：

```text
建立 RecoverySystem
建立周期 hook
但不把 AFTER_DAMAGE 反应链硬塞进 DamageResolutionSystem。
```

`急救 / 倒戈 / 攻心` 正式行为继续 DEFER，建议与 Stage 9 Reaction / Queue 一并研究接入。

这属于基于当前架构的阶段边界调整，不代表这些状态永远不属于 RecoverySystem。

---

# 9. TriggerSystem 精确职责

`TriggerSystem`：

```text
输入：BattleContext + typed RuleHook
输出：tuple[Effect, ...]
```

它可以：

```text
读取 StateRegistry
读取 StateInstance.runtime_params
读取 StateInstance.source_id / source_skill_id
根据 hook 判断哪些 state instance 应产生 Effect
按确定顺序构造 Effect
```

它不得：

```text
EffectExecutor.execute
DamageSystem.calculate
DamageResolutionSystem.resolve
TroopSystem.apply_damage
TroopSystem.restore
StateLifecycleSystem.apply/remove
StateRegistry.add/remove
EventBus 反向驱动规则
Python random
```

TriggerSystem 只回答：

> 当前这个规则节点应该产生哪些 Effect？

---

# 10. RuleHookSystem 精确职责

为了避免 BattleEngine 自己识别具体状态 / Effect，新增最小协调层：

```text
RuleHookSystem
```

职责：

```text
RuleHook
↓
TriggerSystem.collect(...)
↓
ordered Effect(s)
↓
EffectExecutor.execute(...)
↓
返回 typed hook resolution result
```

`BattleEngine` 只调用：

```text
rule_hook_system.process(context, hook)
```

BattleEngine 不认识：

```text
burn
poison
recuperation
RecoverEffect
DamageEffect
```

---

# 11. Rule Hook 的 Engine 接入点

Stage 7 推荐工程顺序：

## ROUND_START

```text
enter ROUND_START
↓
StateLifecycleSystem.expire_at(ROUND_START)
↓
ROUND_STARTED fact
↓
RuleHookSystem.process(RoundStartHook)
↓
VictorySystem.check
↓
ACTION_ORDER
```

工程理由：

```text
已经在 ROUND_START 到期的状态不会再触发本回合效果；
周期伤害可以在行动排序前结束战斗。
```

这是 D = 工程设计决定，不冒充官方所有状态的精确结算时序。

## UNIT_ACTION_START

```text
enter UNIT_ACTION_START
↓
UNIT_ACTION_STARTED fact
↓
RuleHookSystem.process(UnitActionStartHook(actor_id))
↓
VictorySystem.check
↓
若 actor 已死亡则不进入 ActionSystem
↓
否则进入 UNIT_ACTION
```

如果 hook 使副将死亡但战斗未结束：

```text
该 actor 本次不再执行 ActionSystem
```

这保持现有“死亡单位不能行动”的工程不变量。

连续伤害与 stun / disarm 等状态的精确交互顺序仍应作为单独研究项，不因为这个 hook 顺序宣称已证明官方规则。

---

# 12. Trigger 确定性顺序

Stage 7 必须冻结工程确定性：

```text
同一 hook 中匹配多个 StateInstance
→ 按 instance_id 升序处理

单一 StateInstance 产生多个 Effect
→ 按 handler / declaration 明确顺序

RuleHookSystem
→ 严格按 TriggerSystem 返回 tuple 顺序执行
```

这是 D = 工程确定性合同。

真实游戏中同名持续状态的覆盖 / 刷新 / 强度择优不是由这个顺序解决，仍需未来 StateApplicationPolicy / 研究证据。

---

# 13. 周期伤害参数合同

Stage 5 已经建立 `StateRuntimeParams`。

Stage 7 可以正式增加：

```text
PeriodicDamageStateParams
```

推荐最小字段：

```text
damage_type: DamageType
coefficient: float
```

要求：

```text
frozen dataclass
slots
coefficient finite
coefficient >= 0
bool reject
```

来源与归属继续使用 StateInstance 已有：

```text
source_id
source_skill_id
owner_id
```

不得复制到万能 payload。

TriggerSystem 产生：

```text
DamageEffect(
    source_id=state.source_id,
    target_id=state.owner_id,
    damage_type=params.damage_type,
    source_type=CONTINUOUS,
    coefficient=params.coefficient,
    source_skill_id=state.source_skill_id,
)
```

如果正式周期伤害状态缺少合法 source_id：

```text
必须明确失败或被数据校验拒绝，不能静默改成 owner 自伤来源。
```

---

# 14. 周期恢复参数合同

增加：

```text
PeriodicRecoveryStateParams
```

Stage 7 第一版推荐字段：

```text
amount: int
```

要求：

```text
amount >= 0
bool reject
frozen dataclass
slots
```

这只是 Stage 7 Effect / Recovery 基础合同。

它不宣称真实休整最终恢复公式就是固定 amount；真实来源战法如何得到 amount / coefficient，仍由未来战法数据与恢复公式研究决定。

---

# 15. RecoverySystem

Stage 7 建立正式：

```text
RecoveryRequest
RecoveryResult
RecoverySystem
```

职责：

```text
RecoverySystem
= 恢复规则裁决
+ 禁疗判定
+ 调用 TroopSystem.restore
+ 发布恢复结果事实
```

`TroopSystem` 继续：

```text
唯一实际兵力写入口
```

禁止：

```python
target.troops += amount
```

出现在 RecoverySystem 或 TriggerSystem。

---

# 16. RecoveryRequest

推荐表达：

```text
source_id
 target_id
 amount
 source_skill_id
 source_state_id
```

字段必须类型明确。

`source_state_id` 用于周期恢复 / 未来吸血恢复的审计来源，不承载行为。

---

# 17. RecoveryResult

结果至少要能区分：

```text
RESOLVED
PREVENTED
```

并保留：

```text
requested amount
actual troop change
remaining troops
prevented reason / state
source / target
```

不要建立塞满几十个 Optional 字段的万能 Result。

可以使用独立结果类型或严格不变量的单一 dataclass；施工前设计审计必须选择并冻结其中一个方案。

---

# 18. Healing Ban / 禁疗

当前官方语义明确：

```text
healing_ban
= 无法恢复兵力
```

Stage 7 可以正式由 RecoverySystem 解释：

```text
RecoveryRequest
↓
RecoverySystem
↓
context.states.has(target_id, healing_ban)
↓
PREVENTED
↓
不调用 TroopSystem.restore
```

禁止把禁疗逻辑塞进：

```text
TroopSystem.restore
```

因为 TroopSystem 只负责兵力写入，不负责状态政策。

---

# 19. 恢复事件

Stage 7 推荐增加事实事件：

```text
RECOVERY_PREVENTED
TROOPS_RECOVERED
```

语义：

```text
RECOVERY_PREVENTED
= 一次恢复请求已被正式规则阻止

TROOPS_RECOVERED
= 一次恢复请求已经实际修改兵力（actual_change 可为明确值）
```

payload 至少包含：

```text
source_id
source_skill_id
source_state_id
requested_recovery
actual_recovery
remaining_troops
reason_state_id（prevented 时）
```

EventBus 仍只记录事实。

---

# 20. RecoverEffect 正式接入

Stage 5 / 6：

```text
RecoverEffect
→ DeferredEffectResult
→ RECOVERY_SYSTEM_NOT_AVAILABLE
```

Stage 7 建立 RecoverySystem 后改为：

```text
RecoverEffect
↓
EffectExecutor
↓
RecoverySystem.resolve
↓
TroopSystem.restore / RECOVERY_PREVENTED
```

需要新增正式 typed：

```text
RecoverEffectResult
```

并从 `EffectExecutionResult` 联合类型纳入。

完成后：

```text
RECOVERY_SYSTEM_NOT_AVAILABLE
```

不再是 RecoverEffect 的正常返回路径。

必须保留 Stage 5 历史测试意图，但更新为 Stage 7 新合同。

---

# 21. 官方持续状态接入策略

Stage 7 不允许“看到状态名就全部 hardcode”。

正式接入前必须建立一个 Stage 7 evidence matrix，至少记录：

```text
state_id
trigger node evidence
runtime params
source attribution
known stacking behavior
known refresh behavior
known formula / damage type
unknowns
implementation verdict
```

候选状态：

| state | Stage 7 candidate | 当前判断 |
|---|---|---|
| burn / 灼烧 | YES, evidence gate | 有持续伤害高证据，但精确 tick / stacking 仍需记录 |
| flood / 水攻 | YES, evidence gate | 官方明确 owner action 时伤害 |
| poison / 中毒 | YES, evidence gate | 官方明确 owner action 时伤害 |
| rout / 溃逃 | YES, evidence gate | 官方明确 owner action 时伤害；damage type 需由 params 提供 |
| sandstorm / 沙暴 | YES, evidence gate | 官方明确 owner action 时伤害 |
| recuperation / 休整 | YES, evidence gate | 官方明确每回合恢复；精确 round node 需工程冻结 |
| healing_ban / 禁疗 | YES | RecoverySystem policy 证据足够 |

真实状态接入时仍不把“伤害率、恢复量、持续回合、目标数量”写成状态固定常量；这些来自来源技能 / StateRuntimeParams。

---

# 22. Stage 7 明确 DEFER 的 4 个候选

## rebellion / 叛逃

官方明确：

```text
造成伤害
+
无视防御
```

当前 DamageSystem 只有 WEAPON / STRATEGY 正常基础公式，没有正式：

```text
ignore defense
```

裁决合同。

如果 Stage 7 为叛逃单独增加：

```text
if state == rebellion:
    bypass defense
```

会提前破坏 Stage 8 Modifier / Damage Pipeline。

因此：

```text
rebellion
→ DEFER TO STAGE 8 damage pipeline research
```

## first_aid / 急救

属于：

```text
AFTER_DAMAGE reaction
```

当前不在 Stage 7 v1 建立递归 reaction queue。

因此：

```text
first_aid
→ DEFER TO reaction-capable stage
```

## weapon_lifesteal / 倒戈

需要：

```text
实际兵刃伤害结果
→ AFTER_DAMAGE
→ RecoveryEffect
```

还需要确认恢复基数是 requested / actual damage 等细节。

因此 DEFER。

## strategy_lifesteal / 攻心

同上，针对谋略伤害，DEFER。

---

# 23. 对旧 Roadmap 的阶段数量调整

旧 `PROJECT_ROADMAP.md` 把 Stage 7 候选粗略列为 11 个状态。

当前 Stage 7 正式研究认为：

```text
Stage 7 v1 核心
= Trigger / Rule Hook / Recovery 基础设施

可接入官方状态候选
= burn / flood / poison / rout / sandstorm / recuperation / healing_ban

明确不在 Stage 7 v1 强行实现
= rebellion / first_aid / weapon_lifesteal / strategy_lifesteal
```

这是进入 Stage 7 前重新研究后的正式细化。

不为此重写 `PROJECT_ROADMAP.md` 的历史状态快照；当前阶段施工以 `STAGE7.md` 为准。

---

# 24. State Definition 参数 schema

Stage 7 若正式启用参数化官方状态，必须更新对应 `StateDefinition.runtime_params_type`。

例如：

```text
周期伤害状态
→ PeriodicDamageStateParams

recuperation
→ PeriodicRecoveryStateParams

healing_ban
→ EmptyStateRuntimeParams
```

禁止：

```text
所有 40 状态统一改成 generic params
```

只修改 Stage 7 已有正式消费者的状态。

---

# 25. 多状态 / 多实例问题

StateRegistry 当前允许多实例共存。

Stage 7 只冻结：

```text
TriggerSystem 对当前实际 StateInstance 集合进行确定性处理
```

不声称已经解决：

```text
同名状态覆盖
刷新
最大值取代
同源 / 异源叠加
```

这些属于未来 StateApplicationPolicy / 实测研究。

Stage 7 测试可验证多实例执行顺序稳定，但不得把该测试描述成官方 stacking 规则证明。

---

# 26. RandomSystem 边界

Stage 7 周期触发本身第一版不额外做概率裁决。

如果未来状态参数包含概率：

```text
必须由正式 TriggerSystem 通过 context.random / RandomSystem
```

不得：

```python
import random
```

当前第一版不为了“以后可能需要”提前加入 probability 字段。

DamageEffect 的基础伤害随机仍由：

```text
DamageSystem
→ 现有公式
→ RandomSystem
```

产生。

---

# 27. BattleEngine 边界

Stage 7 允许 BattleEngine 新增：

```text
显式 RuleHookSystem 调用
```

但不允许：

```python
if context.states.has(..., "burn"):
if state_id == "poison":
if isinstance(effect, RecoverEffect):
```

Engine 只认识：

```text
流程阶段
RuleHook 类型
VictorySystem
```

不认识具体状态。

---

# 28. EventBus 边界

严格禁止：

```text
EventBus.subscribe(DAMAGE_DEALT, trigger_state_rules)
```

作为正式规则执行路径。

订阅者可以用于：

```text
测试观察
战报
调试
未来 replay
```

但不能反向改变战斗规则。

---

# 29. SkillRuntime 边界

Stage 7 不修改 Stage 6 核心命题：

```text
SkillResolver
→ Effects only
```

SkillRuntime 不负责：

```text
触发周期状态
恢复
监听事件
执行 Effect
```

未来真实技能只负责产生包含 runtime params 的 ApplyStateEffect / RecoverEffect 等意图。

---

# 30. 推荐生产文件

新增候选：

```text
sgs_v2/battle_core/rule_hooks.py
sgs_v2/battle_core/trigger_system.py
sgs_v2/battle_core/rule_hook_system.py
sgs_v2/battle_core/recovery_system.py
sgs_v2/battle_core/stage7_state_params.py
```

必要修改：

```text
sgs_v2/battle_core/effects.py
sgs_v2/battle_core/effect_result.py
sgs_v2/battle_core/effect_executor.py
sgs_v2/battle_core/events.py
sgs_v2/battle_core/official_state_catalog.py
sgs_v2/battle_core/battle_systems.py
sgs_v2/battle_core/engine.py
sgs_v2/battle_core/__init__.py
```

不得为了 Stage 7 无关目标重构：

```text
DamageSystem
TargetSystem
SkillResolver
ActionOrderSystem
```

---

# 31. BattleSystems 推荐组合

建议：

```text
TroopSystem
    ↓
RecoverySystem

DamageResolutionSystem
StateLifecycleSystem
RecoverySystem
    ↓
EffectExecutor

TriggerSystem
EffectExecutor
    ↓
RuleHookSystem
```

同时保持：

```text
TargetSystem
→ NormalAttackSystem
→ existing flow

TargetSystem
→ SkillResolver
```

不得出现：

```text
TriggerSystem(BattleSystems)
RuleHookSystem(BattleSystems)
```

万能依赖。

---

# 32. Recovery 与 Victory

周期 DamageEffect 可能击杀武将。

因此 RuleHook 执行后必须由已有：

```text
VictorySystem
```

重新检查战斗结果。

RecoverySystem 不自行判断胜负。

Stage 7 不实现复活。

对已死亡单位的恢复：

```text
默认工程规则：不得通过普通 RecoverySystem 复活。
```

该行为必须写测试，并标记为 D = 工程决定；未来如游戏存在正式复活机制，建立独立机制，不把它偷偷塞进 RecoverySystem。

---

# 33. Stage 7 测试要求

至少新增：

```text
tests/test_recovery_system.py
tests/test_trigger_system.py
tests/test_rule_hook_system.py
tests/test_stage7_engine_hooks.py
tests/test_stage7_architecture.py
```

以及必要的 Stage 7 state params / integration tests。

---

# 34. RecoverySystem 测试

必须覆盖：

```text
正常恢复通过 TroopSystem.restore
不得超过 max_troops
healing_ban 阻止恢复
被阻止时不调用 TroopSystem.restore
RECOVERY_PREVENTED payload
TROOPS_RECOVERED payload
source_skill_id / source_state_id 保留
死亡单位不会通过普通恢复复活
RecoverySystem 不直接写 troops
```

---

# 35. RecoverEffect 测试

Stage 5 旧语义：

```text
RecoverEffect → DEFERRED
```

Stage 7 必须更新为：

```text
RecoverEffect
→ EffectExecutor
→ RecoverySystem
→ typed RecoverEffectResult
```

必须验证：

```text
EffectExecutor 不直接修改 troops
RecoverEffect 本身无副作用
```

---

# 36. TriggerSystem 测试

至少覆盖：

```text
typed RoundStartHook
 typed UnitActionStartHook
不相关 hook 不产生 Effect
只读取当前有效 StateInstance
按 instance_id 确定顺序
周期伤害产生 DamageEffect(CONTINUOUS)
周期恢复产生 RecoverEffect
source / source_skill 追踪正确
TriggerSystem 不执行 Effect
TriggerSystem 不修改 troops
TriggerSystem 不写 StateRegistry
TriggerSystem 不 import random
```

---

# 37. Engine Hook 集成测试

必须覆盖：

```text
ROUND_START 生命周期到期先于 Stage 7 hook
ROUND_START hook 后进行 Victory check
UNIT_ACTION_STARTED fact 后触发 UnitActionStartHook
hook 击杀 actor 后 actor 不再执行 ActionSystem
hook 击杀主将可立即结束战斗
hook 产生的 recovery / damage 事件顺序确定
BattleEngine 不出现具体 state_id 判断
```

对于尚未研究的真实状态交互：

```text
不要写测试假装官方规则已确定。
```

---

# 38. Architecture Tests

静态架构测试必须尽量使用 AST / import inspection，而不是粗暴注释字符串匹配。

验证：

```text
TriggerSystem
- no Python random import
- no TroopSystem
- no DamageSystem
- no DamageResolutionSystem
- no StateLifecycleSystem write
- no EffectExecutor

RecoverySystem
- no direct UnitRuntime.troops assignment
- only TroopSystem is troop mutation dependency

BattleEngine
- no OfficialStateId / specific state string branches

EventBus
- no rule-specific handler registration added by production composition
```

---

# 39. Stage 1～6 全回归

Stage 7 必须保持：

```text
Stage 1
Stage 2
Stage 3
Stage 4
Stage 5
Stage 6
```

全部既有测试通过。

特别保护：

```text
先攻 / 遇袭
缴械
震慑
虚弱
DamageResolutionSystem
EffectExecutor
StateRuntimeParams
SkillDefinition
SkillRuntime
SkillResolver
RNG non-consumption
```

---

# 40. Stage 7 OUT OF SCOPE

第一版明确不做：

```text
真实战法目录 / 批量真实战法
完整 SkillCategory timing

AFTER_DAMAGE reaction queue
急救正式触发
倒戈正式触发
攻心正式触发

叛逃无视防御
HitResolution
Damage Modifier Pipeline

反击
群攻
连击
Damage Redirect / Split / Share
援护

StateApplicationPolicy
洞察控制免疫完整政策

计穷 / 伪报 / 威慑完整 Skill disable policy
装备运行态

BattleReport / Replay
API / 批量模拟 / 性能优化
```

---

# 41. Stage 7 必须回答的 20 个问题

正式施工前设计审计必须逐项确认：

```text
1. 为什么 Stage 7 现在需要 Rule Hook？
2. 为什么不能用 EventBus 当 TriggerSystem？
3. RuleHook 与 BattleEvent 的区别是什么？
4. Stage 7 第一版需要哪些 hook，为什么只需要这些？
5. TriggerSystem 的输入 / 输出是什么？
6. TriggerSystem 为什么不能执行 Effect？
7. RuleHookSystem 的精确协调职责是什么？
8. 周期伤害参数存在哪里？
9. 周期恢复参数存在哪里？
10. source / source_skill 如何保留？
11. Trigger 顺序如何确定？
12. RecoverEffect 如何正式接入 RecoverySystem？
13. 禁疗由谁阻止？
14. 实际恢复兵力由谁写？
15. 恢复事实由谁发布？
16. Hook 造成死亡后何时检查 Victory？
17. 哪些官方状态证据足够接入？
18. 哪些规则仍 NEEDS_RESEARCH？
19. 为什么叛逃 / 急救 / 倒戈 / 攻心本阶段 DEFER？
20. 如何证明没有第二套伤害 / 恢复 / 状态 / RNG 路径？
```

---

# 42. Stage 7 验收条件

只有以下全部成立，Stage 7 才可进入最终审计：

```text
[ ] RuleHook 强类型合同建立
[ ] TriggerSystem 建立且只产生 Effect
[ ] RuleHookSystem 建立且职责单一
[ ] RecoverySystem 建立
[ ] RecoverEffect 正式接入 RecoverySystem
[ ] TroopSystem 仍为唯一兵力写入口
[ ] healing_ban 正确阻止恢复
[ ] 周期 Damage / Recovery params 类型安全
[ ] ROUND_START hook 接入
[ ] UNIT_ACTION_START hook 接入
[ ] hook effect ordering 确定
[ ] hook 后 Victory check 正确
[ ] BattleEngine 无具体状态判断
[ ] EventBus 仍只记录事实
[ ] TriggerSystem 不使用 Python random
[ ] DamageEffect 仍走 DamageResolutionSystem
[ ] State 写仍走 StateLifecycleSystem
[ ] Stage 6 Skill → Effect 边界未破坏
[ ] 未提前加入 reaction queue / damage modifier
[ ] 官方状态接入均有 evidence matrix
[ ] UNKNOWN 项没有被伪装成官方规则
[ ] Stage 1～6 全回归
[ ] pytest -q success
[ ] python demo.py success
[ ] GitHub Actions success
[ ] 独立最终审计 BLOCKER = 0
[ ] 独立最终审计 MAJOR = 0
```

---

# 43. Stage 7 封版流程

```text
STAGE7.md
↓
独立设计审计
↓
必要修订 STAGE7.md
↓
prompts/STAGE7_BUILD_PROMPT.md
↓
Stage 7 施工分支
↓
pytest + demo + CI
↓
独立实现审计
↓
修复
↓
再次审计
↓
STAGE7_FINAL_AUDIT.md
↓
merge main
↓
main exact HEAD CI success
↓
Stage 7 FROZEN
```

不得因为规划文档或施工分支 CI 通过就提前标记 FROZEN。

---

# 44. Stage 7 最终目标

Stage 7 成功不是“状态数量突然暴涨”。

真正要冻结的是：

```text
Battle Flow
↓
Explicit Rule Hook
↓
TriggerSystem
↓
Effect
↓
EffectExecutor
↓
BattleSystem
```

以及：

```text
RecoverEffect
↓
RecoverySystem
↓
TroopSystem
```

只要这两条路径保持单向、可测试、可审计，后续 Stage 8 Damage Modifier、Stage 9 Reaction / Redirect 和真实技能接入才不会靠 EventBus 回调、状态对象 execute() 或散落 if 分支勉强拼起来。
