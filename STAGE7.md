# 三国志战略版战斗模拟器 V2 · Stage 7 Trigger / Rule Hook / Recovery 实施规范

> 本文是 Stage 7 的正式规划与未来施工边界。它建立在当前 `main` 的 Stage 6 FROZEN 基线上。
> 本文不是施工结果，也不是 FINAL AUDIT。任何 Stage 7 生产代码施工前，都必须再次读取最新 `main` 并完成独立设计审计。
>
> 本版已经吸收第一轮 Stage 7 独立设计审计发现的 4 个 MAJOR、2 个 MINOR、2 个 HARDENING，以及第二轮设计复审发现的 2 个 MAJOR、1 个 MINOR、2 个 HARDENING。第二轮重点修复：Recovery prevention reason、Recovery precedence、HookResolutionResult、State provenance 配对不变量、UnitActionStartHook actor existence、Evidence Matrix 固定交付位置。

---

# 0. 当前基线

Stage 7 初始规划基线：

```text
15bde039fd4521a36f76224731e82cceb9846c19
docs: mark Stage 6 frozen
```

第一轮 Stage 7 独立设计审计基线：

```text
e9a5f118e887ddada6401c1590738cac87791f1a
docs: mark Stage 7 planning ready
```

第一轮修订后的第二轮设计复审基线：

```text
a8f8d5651445c880560f21fa028785acb7d1d714
docs: mark Stage 7 plan revised for re-audit
```

该基线验证：

```text
pytest -q
→ 151 passed

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
Stage 7                   第二轮规划修订 / 待第三轮快速复审
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

Stage 7 实际施工时如果 `main` 已变化，施工者必须重新确认 Stage 6 冻结边界仍成立，并以新的 HEAD 作为实际施工基线。

---

# 1. Stage 7 为什么现在需要做

Stage 1～6 已解决：

```text
战斗流程
基础 BattleSystem
状态存储与生命周期
官方状态静态目录
Effect 意图与统一执行
Skill 静态定义 / 运行实例 / 显式解析
```

当前仍缺少：

```text
1. 战斗流程中的明确规则触发节点。
2. 正式恢复兵力结算系统。
```

因此尚不能正确表达：

```text
每回合触发
武将行动时触发
周期伤害
周期恢复
禁疗
未来的伤害后恢复 / 反应式机制
```

Stage 7 要冻结的核心链路：

```text
BattleEngine / BattleSystem
        ↓
explicit Rule Hook
        ↓
TriggerSystem
        ↓
ordered Effect(s)
        ↓
RuleHookSystem
        ↓
EffectExecutor
        ↓
BattleSystem
```

以及：

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
= 恢复规则裁决与阻止政策

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
RuleHookSystem 认识具体 state_id
RuleHookSystem 依赖 VictorySystem
BattleEngine 认识具体 Effect 类型
BattleEngine 认识具体 state_id
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

Stage 7 允许对 Stage 5/6 数据合同做**向后兼容、仅为 Stage 7 正式消费者服务的最小扩展**，但不得改变已冻结的核心业务语义。

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

`research/state_catalog_v1/STATE_CATALOG_V1.md` 还提供战法描述 / 战报级研究：

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

以下规则仍不能凭当前资料完整冻结：

```text
持续状态同名多实例的覆盖 / 刷新 / 最高来源政策
持续伤害精确 tick 相对官方事件顺序
持续伤害是否快照来源属性
来源死亡后持续状态的计算方式
休整官方精确发生节点
急救具体恢复公式
倒戈 / 攻心使用 requested damage 还是 actual damage
禁疗对所有吸血 / 急救交互的完整事件顺序
叛逃“无视防御”的正式 Damage Pipeline 位置
```

以上必须标记 NEEDS_RESEARCH，不得用经验补齐。

---

# 6. Stage 7 正式范围

Stage 7 第一版正式建设：

```text
RuleHook 强类型数据合同
TriggerSystem
RuleHookSystem
HookResolutionResult
RecoveryRequest / RecoveryResult
RecoveryPreventionReason
RecoverySystem
RecoverEffect → RecoverySystem 正式接入
恢复事实事件
周期 Damage / Recovery StateRuntimeParams
ROUND_START / UNIT_ACTION_START 最小显式 hook
确定性 trigger ordering
Hook 原子批次执行合同
State provenance 全链追踪
Stage 7 synthetic trigger tests
官方状态 evidence matrix 与 PASS / DEFER gate
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

使用不可变强类型 hook：

```text
RoundStartHook
UnitActionStartHook
```

禁止：

```python
hook_payload: dict[str, Any]
```

正式最小合同：

```text
RoundStartHook
- round_no: int

UnitActionStartHook
- round_no: int
- actor_id: str
```

运行时验证：

```text
round_no 必须是 int
bool reject
round_no >= 1
actor_id 必须是非空、非纯空白 str
```

`RuleHookSystem.process(context, hook)` 必须验证：

```text
hook.round_no == context.current_round
```

对 `UnitActionStartHook` 还必须验证：

```text
hook.actor_id in context.units
```

若 round 不一致或 actor 不存在：

```text
明确失败
不得静默视为“无触发效果”
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

这已经进入 reaction chain。

当前普通攻击伤害路径和 DamageEffect 路径都复用 `DamageResolutionSystem`，但 `EffectExecutor` 又依赖 `DamageResolutionSystem`。

如果直接让：

```text
DamageResolutionSystem
→ TriggerSystem
→ EffectExecutor
→ DamageResolutionSystem
```

会形成循环依赖，并提前引入递归触发风险。

因此 Stage 7 v1：

```text
建立 RecoverySystem
建立周期 hook
但不把 AFTER_DAMAGE 反应链硬塞进 DamageResolutionSystem
```

`急救 / 倒戈 / 攻心` 正式行为继续 DEFER，建议与 Stage 9 Reaction / Queue 一并研究接入。

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
读取 StateInstance.source_id
读取 StateInstance.source_skill_id
读取 StateInstance.state_id
读取 StateInstance.instance_id
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

`RuleHookSystem` 是最小协调层。

职责：

```text
RuleHook
↓
输入一致性验证
↓
TriggerSystem.collect(...)
↓
ordered Effect(s)
↓
EffectExecutor.execute(...)
↓
返回 HookResolutionResult
```

`RuleHookSystem` 不负责：

```text
Victory 判定
状态识别
伤害计算
恢复政策
RNG
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

# 11. HookResolutionResult 正式合同

第二轮设计复审要求冻结这个边界，不能只写“返回 typed result”然后让施工者自由发挥。

正式定义：

```text
@dataclass(frozen=True, slots=True)
HookResolutionResult:
    hook: RuleHook
    effect_results: tuple[EffectExecutionResult, ...]
```

语义：

```text
hook
= 本次已经处理的 typed RuleHook

effect_results
= EffectExecutor 按 TriggerSystem 返回 Effect tuple 的原始顺序产生的执行结果
```

不再重复保存：

```text
effects: tuple[Effect, ...]
```

因为每个 `EffectExecutionResult` 已携带对应 Effect。

无匹配 Effect 时仍返回：

```text
HookResolutionResult(
    hook=hook,
    effect_results=(),
)
```

禁止：

```text
无 Effect → return None
```

`HookResolutionResult` 不保存：

```text
VictoryResult
BattleResult
terminal flag
```

Victory 继续由 BattleEngine 在 hook atomic batch 完成后检查。

必须保证：

```text
len(effect_results)
== TriggerSystem.collect(...) 返回 Effect 数量
```

且顺序一一对应。

---

# 12. Rule Hook 的 Engine 接入点与行动生命周期

Stage 7 冻结以下 D = ENGINEERING DECISION。

## 12.1 ROUND_START

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
若 terminal → BATTLE_END
否则 → ACTION_ORDER
```

工程理由：

```text
已经在 ROUND_START 到期的状态不会再触发本回合效果；
周期伤害可以在行动排序前结束战斗。
```

这不是官方所有状态精确结算时序的声明。

## 12.2 UNIT_ACTION_START

正式流程：

```text
enter UNIT_ACTION_START
↓
UNIT_ACTION_STARTED fact
↓
RuleHookSystem.process(UnitActionStartHook(actor_id))
↓
VictorySystem.check
↓
如果 result is None 且 actor.is_alive
    → enter UNIT_ACTION
    → ActionSystem.execute
    → VictorySystem.check
否则
    → 跳过 UNIT_ACTION / ActionSystem
↓
enter UNIT_ACTION_END
↓
UNIT_ACTION_ENDED fact
↓
如果 result != None
    → BATTLE_END
否则
    → 下一个 actor
```

注意这里的 `result` 指 `VictorySystem.check()` 的结果，不是 `HookResolutionResult`。

因此：

```text
hook 击杀副将
→ 跳过该 actor 的 ActionSystem
→ 仍发布 UNIT_ACTION_ENDED

hook 击杀主将并形成 terminal result
→ 跳过该 actor 的 ActionSystem
→ 仍进入 UNIT_ACTION_END
→ 发布 UNIT_ACTION_ENDED
→ 再进入 BATTLE_END
```

这里继承当前 Engine 已有语义：

> 行动生命周期开始后，即使本次行动中形成终局，也先闭合 `UNIT_ACTION_END / UNIT_ACTION_ENDED`，再结束战斗。

`UNIT_ACTION_ENDED` 表示本次 action lifecycle 已结束，不代表 actor 一定成功执行过普通攻击。

连续伤害与 stun / disarm 等状态的官方精确交互顺序仍需单独研究。

---

# 13. Trigger 确定性顺序与 Hook 原子批次合同

Stage 7 必须冻结工程确定性：

```text
同一 hook 中匹配多个 StateInstance
→ 按 instance_id 升序处理

单一 StateInstance 产生多个 Effect
→ 按 handler / declaration 明确顺序

RuleHookSystem
→ 严格按 TriggerSystem 返回 tuple 顺序执行
```

## 13.1 Hook atomic batch policy

Stage 7 v1 采用：

```text
一个 RuleHook
→ collect 一次 ordered Effect tuple
→ tuple 内全部 Effect 按顺序执行
→ batch 完成后
→ BattleEngine 调用 VictorySystem.check
```

即：

```text
同一个 Hook batch 中
即使较早 Effect 已击杀主将
也不在 RuleHookSystem 内中断后续 Effect
```

这是：

```text
D = ENGINEERING DECISION
```

理由：

```text
RuleHookSystem 保持只协调 TriggerSystem + EffectExecutor；
不反向依赖 VictorySystem；
不在 Stage 7 提前建立可递归 / 可中断 Reaction Queue。
```

该规则必须写明确测试。

如果未来官方证据证明某类规则需要 effect-level terminal short-circuit，则在正式 queue / resolution policy 中扩展，不靠临时 `if battle ended` 分支破坏 Stage 7 合同。

---

# 14. State provenance 全链合同

Stage 7 第一次正式引入“StateInstance 触发新的 Effect”。

必须冻结以下可选 provenance：

```text
source_state_id: str | None
source_state_instance_id: str | None
```

语义：

```text
source_state_id
= 触发该 Effect 的状态种类

source_state_instance_id
= 触发该 Effect 的具体 StateInstance
```

二者只记录来源，不承载行为。

## 14.1 配对不变量

第二轮设计复审正式冻结：

```text
source_state_id
和
source_state_instance_id
```

必须：

```text
both None
或
both non-None
```

禁止构造：

```text
source_state_id="burn"
source_state_instance_id=None
```

或：

```text
source_state_id=None
source_state_instance_id="state-001"
```

这个配对不变量至少适用于：

```text
DamageEffect
DamageRequest
DamageResult
RecoverEffect
RecoveryRequest
RecoveryResult（通过 request 继承）
```

对于由状态触发的周期 Effect：

```text
source_state_id
= state.state_id

source_state_instance_id
= state.instance_id
```

对于非状态来源 Effect：

```text
source_state_id = None
source_state_instance_id = None
```

Stage 7 至少要求以下链路保留 provenance：

```text
StateInstance
→ TriggerSystem
→ DamageEffect / RecoverEffect
→ DamageRequest / RecoveryRequest
→ DamageResult / RecoveryResult
→ 对应事实 Event payload
```

`source_skill_id` 继续保留原始施加该状态的技能来源。

## 14.2 对 Damage 链的最小扩展

Stage 7 允许对：

```text
DamageEffect
DamageRequest
DamageResult
DamageResolutionSystem event payload
```

增加：

```text
source_state_id
source_state_instance_id
```

仅做 provenance 元数据透传。

禁止借此修改：

```text
基础兵刃公式
基础谋略公式
DamageType 语义
weakness 既有阻止逻辑
伤害随机逻辑
```

这不是 Stage 8 Damage Pipeline。

---

# 15. 周期伤害参数合同

新增：

```text
PeriodicDamageStateParams
```

最小字段：

```text
damage_type: DamageType
coefficient: float
```

要求：

```text
frozen dataclass
slots
damage_type 必须是 DamageType
coefficient 必须是 int / float
bool reject
coefficient finite
coefficient >= 0
最终规范化为 float
```

来源与归属继续使用 StateInstance：

```text
source_id
source_skill_id
state_id
instance_id
owner_id
```

不得复制到万能 payload。

TriggerSystem 产生概念：

```text
DamageEffect(
    source_id=state.source_id,
    target_id=state.owner_id,
    damage_type=params.damage_type,
    source_type=CONTINUOUS,
    coefficient=params.coefficient,
    source_skill_id=state.source_skill_id,
    source_state_id=state.state_id,
    source_state_instance_id=state.instance_id,
)
```

如果正式周期伤害状态缺少合法 `source_id`：

```text
必须明确失败或被数据校验拒绝
不能静默改成 owner 自伤来源
```

---

# 16. 周期恢复参数合同

增加：

```text
PeriodicRecoveryStateParams
```

Stage 7 第一版字段：

```text
amount: int
```

正式要求：

```text
必须是 int
bool reject
amount >= 0
frozen dataclass
slots
```

这只是 Stage 7 Effect / Recovery 基础合同。

它不宣称真实休整最终恢复公式就是固定 amount；真实来源战法如何得到 amount / coefficient，仍由未来战法数据与恢复公式研究决定。

---

# 17. RecoverEffect 激活前的类型安全修订

Stage 5 / 6 的 `RecoverEffect` 只处于 DEFERRED 路径。Stage 7 将正式执行恢复，所以必须先同步加固。

正式合同：

```text
source_id: str | None
target_id: str
amount: int
source_skill_id: str | None
source_state_id: str | None
source_state_instance_id: str | None
```

验证：

```text
target_id 必须非空、非纯空白
source_id 提供时必须非空、非纯空白
source_skill_id 提供时必须非空、非纯空白
source_state_id 提供时必须非空、非纯空白
source_state_instance_id 提供时必须非空、非纯空白
source_state_id / source_state_instance_id 必须成对出现
amount 必须是 int
bool reject
amount >= 0
```

`RecoverEffect` 本身仍然：

```text
无副作用
不调用 RecoverySystem
不调用 TroopSystem
```

---

# 18. RecoveryRequest

正式表达：

```text
source_id: str | None
target_id: str
amount: int
source_skill_id: str | None
source_state_id: str | None
source_state_instance_id: str | None
```

验证必须与 RecoverEffect 一致：

```text
amount 必须是 int
bool reject
amount >= 0
ID 字段提供时不得为空或纯空白
source_state_id / source_state_instance_id 必须成对出现
```

`source_state_id` / `source_state_instance_id` 用于周期恢复与未来反应式恢复的审计来源，不承载行为。

---

# 19. Recovery prevention 正式合同

第二轮设计复审发现：仅有 `reason_state_id` 无法表示“死亡目标不能普通恢复”。因此 Stage 7 正式建立：

```text
RecoveryPreventionReason
```

最小枚举：

```text
HEALING_BAN
TARGET_DEFEATED
```

不得使用任意字符串 reason。

---

# 20. RecoveryResult 正式冻结方案

Stage 7 使用独立结果类型组成联合类型：

```text
RecoveryResolvedResult
RecoveryPreventedResult

RecoveryResult
= RecoveryResolvedResult | RecoveryPreventedResult
```

## 20.1 RecoveryResolvedResult

至少保存：

```text
request: RecoveryRequest
troop_change: TroopChangeResult
```

因此可得到：

```text
requested amount
actual recovery
remaining troops
全部 source provenance
```

## 20.2 RecoveryPreventedResult

正式保存：

```text
request: RecoveryRequest
reason: RecoveryPreventionReason
reason_state_id: str | None
```

不得伪造 `TroopChangeResult`。

严格不变量：

```text
reason == HEALING_BAN
→ reason_state_id 必须等于 healing_ban 的正式 state_id

reason == TARGET_DEFEATED
→ reason_state_id 必须为 None
```

禁止：

```text
reason == TARGET_DEFEATED
reason_state_id="target_is_dead"
```

死亡是 UnitRuntime / battle fact，不是假状态。

被阻止时：

```text
不调用 TroopSystem.restore
```

## 20.3 EffectExecutionStatus 语义

`RecoveryPreventedResult` 表示：

```text
RecoverEffect 已被正式规则成功解析
只是恢复结果被规则阻止
```

因此：

```text
Recovery PREVENTED
≠ EffectExecutionStatus.DEFERRED
≠ Effect 执行失败
```

正式：

```text
RecoverEffectResult
- effect: RecoverEffect
- resolution: RecoveryResult
- status = EffectExecutionStatus.RESOLVED
```

这与现有 DamageEffectResult / DamageResult.prevented 的分层保持一致。

---

# 21. RecoverySystem

Stage 7 建立正式：

```text
RecoverySystem
```

职责：

```text
RecoveryRequest 输入验证
目标存在性检查
恢复规则裁决
死亡目标阻止
禁疗判定
调用 TroopSystem.restore
发布恢复结果事实
返回 RecoveryResult
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

RecoverySystem 不负责：

```text
Victory
复活
Trigger
Skill
Effect routing
```

---

# 22. RecoverySystem 裁决优先级

Stage 7 冻结以下 D = ENGINEERING DECISION：

```text
1. target_id 必须能从 BattleContext 解析到目标
   → 不存在时明确失败，不返回 PREVENTED

2. target 已死亡
   → RecoveryPreventedResult(
        reason=TARGET_DEFEATED,
        reason_state_id=None,
      )
   → 发布 RECOVERY_PREVENTED
   → 不调用 TroopSystem.restore

3. target 存在 healing_ban
   → RecoveryPreventedResult(
        reason=HEALING_BAN,
        reason_state_id=healing_ban,
      )
   → 发布 RECOVERY_PREVENTED
   → 不调用 TroopSystem.restore

4. 否则
   → TroopSystem.restore
   → RecoveryResolvedResult
```

因此：

```text
dead + healing_ban
→ TARGET_DEFEATED

alive + healing_ban + full troops
→ HEALING_BAN

alive + no healing_ban + full troops
→ RESOLVED(actual=0)
→ 不发布 TROOPS_RECOVERED
```

这个顺序只冻结 Stage 7 工程确定性，不冒充未来所有恢复机制的官方优先级。

---

# 23. TroopSystem.restore 防御性合同

Stage 7 不把禁疗等恢复政策塞进 `TroopSystem.restore()`。

但由于 `restore()` 是最终兵力写入口，可以增加输入层防御性验证：

```text
requested_recovery 必须是 int
bool reject
requested_recovery >= 0
```

这只是兵力写入类型安全，不属于恢复政策。

禁止 TroopSystem 判断：

```text
healing_ban
source state
skill type
复活规则
```

---

# 24. Healing Ban / 禁疗

当前官方语义明确：

```text
healing_ban
= 无法恢复兵力
```

Stage 7 正式由 RecoverySystem 解释：

```text
RecoveryRequest
↓
RecoverySystem
↓
context.states.has(target_id, healing_ban)
↓
RecoveryPreventedResult(
    reason=HEALING_BAN,
    reason_state_id="healing_ban",
)
↓
RECOVERY_PREVENTED fact
↓
不调用 TroopSystem.restore
```

禁止把禁疗逻辑塞进 TroopSystem。

---

# 25. 恢复事件与 0 实际恢复语义

Stage 7 增加事实事件：

```text
RECOVERY_PREVENTED
TROOPS_RECOVERED
```

## 25.1 RECOVERY_PREVENTED

语义：

```text
一次恢复请求已被正式规则阻止
```

至少包含：

```text
source_id
source_skill_id
source_state_id
source_state_instance_id
target_id
requested_recovery
reason
reason_state_id
```

其中：

```text
reason = RecoveryPreventionReason.value
```

`reason_state_id` 仅在该阻止原因确实来自状态时存在。

## 25.2 TROOPS_RECOVERED

语义：

```text
一次恢复请求已经实际增加目标兵力
```

至少包含：

```text
source_id
source_skill_id
source_state_id
source_state_instance_id
target_id
requested_recovery
actual_recovery
remaining_troops
```

## 25.3 满兵 / actual_recovery == 0

Stage 7 冻结：

```text
RecoverySystem 可以返回 RecoveryResolvedResult
且 troop_change.actual_change == 0
```

但：

```text
actual_change == 0
→ 不发布 TROOPS_RECOVERED
```

理由：

```text
EventBus 记录已经发生的事实；
0 实际恢复没有发生兵力增加。
```

这是 D = ENGINEERING DECISION。

---

# 26. RecoverEffect 正式接入

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
构造 / 转换 RecoveryRequest
↓
RecoverySystem.resolve
↓
RecoveryResolvedResult / RecoveryPreventedResult
↓
RecoverEffectResult
```

完成后：

```text
RECOVERY_SYSTEM_NOT_AVAILABLE
```

不再是 RecoverEffect 的正常返回路径。

必须保留 Stage 5 历史测试意图，但更新为 Stage 7 新合同。

---

# 27. 官方持续状态 Evidence Matrix 与硬 Gate

Stage 7 不允许“看到状态名就全部 hardcode”。

正式 Evidence Matrix 固定交付位置：

```text
research/stage7_evidence_matrix/STAGE7_EVIDENCE_MATRIX.md
```

这份文件是 Stage 7 正式审计输入，不能只存在于聊天、临时笔记或施工者记忆里。

至少记录：

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

`implementation verdict` 只能是：

```text
PASS_STAGE7
DEFER
```

## 27.1 硬 Gate

如果仍存在会改变**单实例基础行为**的关键 UNKNOWN，例如：

```text
trigger node 无法确定
damage type 无法确定
基础公式 / coefficient 语义无法确定
source attribution 无法确定
恢复 amount 的工程来源无法确定
```

则：

```text
implementation verdict = DEFER
```

不得：

```text
UNKNOWN
+ 自行猜一个规则
+ 宣布官方状态已实现
```

以下未知项如果 Stage 7 明确不声称解决，则可以继续 DEFER 而不必阻止基础设施和 synthetic 单实例测试：

```text
同名 stacking
refresh
最高值覆盖
同源 / 异源竞争
```

但测试与文档必须明确：

```text
多实例 deterministic execution
≠ 官方 stacking 规则
```

当前候选状态：

| state | Stage 7 candidate | 当前判断 |
|---|---|---|
| burn / 灼烧 | evidence gate | 有持续伤害证据；只有 matrix PASS 后接入 |
| flood / 水攻 | evidence gate | 官方明确 owner action 时伤害；其余关键项需 matrix |
| poison / 中毒 | evidence gate | 官方明确 owner action 时伤害；其余关键项需 matrix |
| rout / 溃逃 | evidence gate | owner action 时伤害；damage type 等需 matrix |
| sandstorm / 沙暴 | evidence gate | owner action 时伤害；其余关键项需 matrix |
| recuperation / 休整 | evidence gate | 每回合恢复；工程 hook 与 amount 来源需 matrix |
| healing_ban / 禁疗 | PASS_STAGE7 | RecoverySystem policy 证据足够 |

Stage 7 **基础设施施工不以全部周期官方状态必须 PASS 为前提**。

如果某个周期状态 Evidence Matrix 不能 PASS：

```text
该状态 DEFER
但 RuleHook / Trigger / Recovery 基础设施仍可施工与验收
```

周期状态若证据不足，使用 synthetic StateDefinition / StateInstance 验证基础设施，不得拿真实状态名称填补未知规则。

---

# 28. Stage 7 明确 DEFER 的 4 个候选

## rebellion / 叛逃

官方明确：

```text
造成伤害
+
无视防御
```

当前 DamageSystem 没有正式 ignore-defense / modifier pipeline。

如果 Stage 7 单独增加：

```text
if state == rebellion:
    bypass defense
```

会提前破坏 Stage 8 Damage Pipeline。

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

因此 DEFER。

## weapon_lifesteal / 倒戈

需要：

```text
实际兵刃伤害结果
→ AFTER_DAMAGE
→ RecoverEffect
```

还需要确认恢复基数是 requested / actual damage。

因此 DEFER。

## strategy_lifesteal / 攻心

同上，针对谋略伤害，DEFER。

---

# 29. 对旧 Roadmap 的阶段数量调整

旧 `PROJECT_ROADMAP.md` 把 Stage 7 候选粗略列为 11 个状态。

当前 Stage 7 正式研究细化为：

```text
Stage 7 v1 核心
= Trigger / Rule Hook / Recovery 基础设施

可进入 evidence gate 的官方状态
= burn / flood / poison / rout / sandstorm / recuperation

Recovery policy 可直接进入 Stage 7
= healing_ban

明确不在 Stage 7 v1 强行实现
= rebellion / first_aid / weapon_lifesteal / strategy_lifesteal
```

不为此重写 `PROJECT_ROADMAP.md` 的历史状态快照；当前阶段施工以 `STAGE7.md` 为准。

---

# 30. State Definition 参数 schema

Stage 7 若正式启用参数化官方状态，必须更新对应 `StateDefinition.runtime_params_type`。

例如：

```text
通过 evidence gate 的周期伤害状态
→ PeriodicDamageStateParams

recuperation（仅在 evidence gate PASS 后）
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

# 31. 多状态 / 多实例问题

StateRegistry 当前允许多实例共存。

Stage 7 只冻结：

```text
TriggerSystem 对当前实际 StateInstance 集合进行确定性处理
State provenance 能精确追踪到 instance_id
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

# 32. RandomSystem 边界

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

DamageEffect 的基础伤害随机仍由现有 DamageSystem / formula / RandomSystem 路径产生。

---

# 33. BattleEngine 边界

Stage 7 允许 BattleEngine 新增：

```text
显式 RuleHookSystem 调用
Victory check 的新流程位置
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
RuleHookSystem
VictorySystem
```

不认识具体状态或 Effect 类型。

---

# 34. EventBus 边界

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

Stage 7 新增 provenance 只允许进入事实 payload，不改变 EventBus 职责。

---

# 35. SkillRuntime 边界

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

# 36. 推荐生产文件

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
sgs_v2/battle_core/damage_system.py                 # provenance 透传，不改公式
sgs_v2/battle_core/damage_resolution_system.py      # provenance event payload
sgs_v2/battle_core/troop_system.py                  # restore 输入类型加固
sgs_v2/battle_core/official_state_catalog.py
sgs_v2/battle_core/battle_systems.py
sgs_v2/battle_core/engine.py
sgs_v2/battle_core/__init__.py
```

文档 / 研究交付：

```text
research/stage7_evidence_matrix/STAGE7_EVIDENCE_MATRIX.md
```

不得为了 Stage 7 无关目标重构：

```text
基础伤害公式
TargetSystem
SkillResolver
ActionOrderSystem
NormalAttackSystem 既有语义
```

`DamageSystem` 的 Stage 7 修改只允许：

```text
source_state provenance 元数据透传
```

不得改伤害计算规则。

---

# 37. BattleSystems 推荐组合

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
RecoverySystem(BattleSystems)
```

万能依赖。

`RuleHookSystem` 不注入 `VictorySystem`；Victory 继续由 Engine 在 Hook atomic batch 完成后检查。

---

# 38. Recovery 与 Victory

周期 DamageEffect 可能击杀武将。

Stage 7 v1 冻结：

```text
RuleHookSystem 完整执行当前 hook atomic batch
↓
返回 HookResolutionResult
↓
BattleEngine 调用 VictorySystem.check
```

RecoverySystem 不自行判断胜负。

Stage 7 不实现复活。

对已死亡单位的恢复：

```text
RecoveryPreventedResult(
    reason=TARGET_DEFEATED,
    reason_state_id=None,
)
```

未来如游戏存在正式复活机制，建立独立机制，不把它偷偷塞进 RecoverySystem。

---

# 39. Stage 7 测试要求

至少新增：

```text
tests/test_recovery_system.py
tests/test_trigger_system.py
tests/test_rule_hook_system.py
tests/test_stage7_engine_hooks.py
tests/test_stage7_provenance.py
tests/test_stage7_state_params.py
tests/test_stage7_architecture.py
```

以及 Evidence Matrix review / integration tests。

---

# 40. RecoverySystem 测试

必须覆盖：

```text
正常恢复通过 TroopSystem.restore
不得超过 max_troops
healing_ban 阻止恢复
TARGET_DEFEATED 阻止恢复
被阻止时不调用 TroopSystem.restore
RECOVERY_PREVENTED payload
TROOPS_RECOVERED payload
source_skill_id 保留
source_state_id 保留
source_state_instance_id 保留
死亡单位不会通过普通恢复复活
RecoverySystem 不直接写 troops
满兵恢复返回 Resolved(actual=0)
满兵恢复不发布 TROOPS_RECOVERED
```

必须验证 precedence：

```text
dead + healing_ban
→ TARGET_DEFEATED

alive + healing_ban + full troops
→ HEALING_BAN

alive + no healing_ban + full troops
→ RESOLVED(actual=0)
```

反例：

```text
RecoverEffect.amount = True → reject
RecoverEffect.amount = 1.5 → reject
RecoverEffect.amount < 0 → reject
RecoveryRequest.amount = True → reject
RecoveryRequest.amount = 1.5 → reject
RecoveryRequest.amount < 0 → reject
TroopSystem.restore(True) → reject
TroopSystem.restore(1.5) → reject
非法 RecoveryPreventionReason → reject
TARGET_DEFEATED + reason_state_id 非 None → reject
HEALING_BAN + reason_state_id 缺失 → reject
```

---

# 41. RecoverEffect 测试

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
Recovery PREVENTED 仍返回 EffectExecutionStatus.RESOLVED
provenance 完整传入 RecoveryRequest / Result / Event
```

---

# 42. TriggerSystem / RuleHook 测试

至少覆盖：

```text
typed RoundStartHook
typed UnitActionStartHook
round_no < 1 reject
bool round_no reject
空 / 纯空白 actor_id reject
hook.round_no != context.current_round reject
UnitActionStartHook actor_id 不存在于 context.units → reject
不相关 hook 不产生 Effect
只读取当前有效 StateInstance
按 instance_id 确定顺序
周期伤害产生 DamageEffect(CONTINUOUS)
周期恢复产生 RecoverEffect
source_id 追踪正确
source_skill_id 追踪正确
source_state_id 追踪正确
source_state_instance_id 追踪正确
TriggerSystem 不执行 Effect
TriggerSystem 不修改 troops
TriggerSystem 不写 StateRegistry
TriggerSystem 不 import random
```

---

# 43. HookResolutionResult 测试

必须覆盖：

```text
无 Effect
→ HookResolutionResult(effect_results=())
→ 不返回 None

一个 Effect
→ 一个 EffectExecutionResult

多个 Effect
→ effect_results 数量一致
→ 顺序严格一致

HookResolutionResult 保存原始 typed hook
HookResolutionResult 不保存 VictoryResult / terminal flag
```

---

# 44. Provenance 集成测试

必须分别证明：

```text
StateInstance
→ DamageEffect
→ DamageRequest
→ DamageResult
→ DAMAGE_DEALT / DAMAGE_PREVENTED
```

以及：

```text
StateInstance
→ RecoverEffect
→ RecoveryRequest
→ RecoveryResult
→ TROOPS_RECOVERED / RECOVERY_PREVENTED
```

全过程保留：

```text
source_skill_id
source_state_id
source_state_instance_id
```

还必须验证 provenance pairing：

```text
None / None → valid
state_id / instance_id → valid
state_id / None → reject
None / instance_id → reject
```

不得只验证 Effect 层然后假定后续仍存在。

---

# 45. Hook atomic batch 测试

必须构造 synthetic hook：

```text
Effect 1
→ lethal DamageEffect

Effect 2
→ 另一合法 Effect
```

验证：

```text
Effect 1 执行
Effect 2 仍执行
Effect 执行顺序与 tuple 顺序一致
RuleHookSystem 内不调用 VictorySystem
batch 完成后才由 Engine Victory check
HookResolutionResult.effect_results 顺序一致
```

该测试只证明 Stage 7 工程 atomic batch contract，不冒充官方持续状态 terminal 顺序。

---

# 46. Engine Hook 生命周期集成测试

必须覆盖：

```text
ROUND_START 生命周期到期先于 Stage 7 hook
ROUND_STARTED fact 后进入 RoundStartHook
ROUND_START hook batch 后进行 Victory check

UNIT_ACTION_STARTED fact 后进入 UnitActionStartHook
hook 击杀 actor 后 actor 不进入 ActionSystem
hook 击杀副将后仍发布 UNIT_ACTION_ENDED
hook 击杀主将后仍发布 UNIT_ACTION_ENDED，再 BATTLE_ENDED
hook 未击杀 actor 时保持既有 UNIT_ACTION 流程
hook 产生的 recovery / damage 事件顺序确定
BattleEngine 不出现具体 state_id / Effect 类型判断
```

事件顺序至少验证：

```text
UNIT_ACTION_STARTED
→ hook effect facts
→ UNIT_ACTION_ENDED
```

若形成终局：

```text
UNIT_ACTION_STARTED
→ hook effect facts
→ UNIT_ACTION_ENDED
→ BATTLE_ENDED
```

对于尚未研究的真实状态交互：

```text
不要写测试假装官方规则已确定
```

---

# 47. Architecture Tests

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
- no TriggerSystem
- no EffectExecutor
- no VictorySystem

RuleHookSystem
- no VictorySystem
- no OfficialStateId / specific state string
- only coordinates TriggerSystem + EffectExecutor

BattleEngine
- no OfficialStateId / specific state string branches
- no DamageEffect / RecoverEffect type branches

EventBus
- no rule-specific handler registration added by production composition

DamageSystem Stage 7 diff
- provenance only
- no formula semantic change
```

---

# 48. Evidence Matrix Review Gate

正式文件：

```text
research/stage7_evidence_matrix/STAGE7_EVIDENCE_MATRIX.md
```

任何官方周期状态进入生产映射前，审计资料必须确认：

```text
implementation verdict = PASS_STAGE7
```

如果：

```text
implementation verdict = DEFER
```

则生产 TriggerSystem 不得为该 state_id 增加正式行为分支。

`healing_ban` 可作为 RecoverySystem policy 的正式 Stage 7 状态。

周期状态若证据不足，使用 synthetic StateDefinition / StateInstance 验证基础设施，不得拿真实状态名称填补未知规则。

---

# 49. Stage 1～6 全回归

Stage 7 必须保持 Stage 1～6 全部既有测试通过。

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

对 `DamageRequest / DamageResult / DamageEffect` 的 provenance 扩展必须向后兼容，不得破坏 Stage 1～6 既有调用方。

---

# 50. Stage 7 OUT OF SCOPE

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

Stage 7 provenance 字段不是 BattleReport/Replay 实现，只是为未来可审计性保留必要来源事实。

---

# 51. Stage 7 必须回答的 31 个问题

正式施工前第三轮快速复审必须逐项确认：

```text
1. 为什么 Stage 7 现在需要 Rule Hook？
2. 为什么不能用 EventBus 当 TriggerSystem？
3. RuleHook 与 BattleEvent 的区别是什么？
4. Stage 7 第一版需要哪些 hook，为什么只需要这些？
5. RuleHook 如何验证 round / actor 输入一致性？
6. UnitActionStartHook 为什么必须验证 actor 存在？
7. TriggerSystem 的输入 / 输出是什么？
8. TriggerSystem 为什么不能执行 Effect？
9. RuleHookSystem 的精确协调职责是什么？
10. HookResolutionResult 的正式 schema 是什么？
11. 为什么 RuleHookSystem 不依赖 VictorySystem？
12. Hook atomic batch 的 terminal policy 是什么？
13. 周期伤害参数存在哪里？
14. 周期恢复参数存在哪里？
15. source / source_skill / source_state / instance provenance 如何保留？
16. 为什么 source_state_id / source_state_instance_id 必须成对出现？
17. Trigger 顺序如何确定？
18. RecoverEffect 如何正式接入 RecoverySystem？
19. RecoverEffect / RecoveryRequest 的 amount 如何保证类型安全？
20. RecoveryResult 为什么采用 resolved / prevented 两个类型？
21. RecoveryPreventionReason 为什么需要强类型？
22. TARGET_DEFEATED 与 HEALING_BAN 的优先级是什么？
23. 实际恢复兵力由谁写？
24. actual_recovery == 0 时事件语义是什么？
25. Hook 击杀 actor 后 UNIT_ACTION lifecycle 如何闭合？
26. Hook batch 后何时检查 Victory？
27. Evidence Matrix 固定存放在哪里？
28. 哪些官方状态 evidence matrix 足够接入？
29. 哪些规则仍 NEEDS_RESEARCH？
30. 为什么叛逃 / 急救 / 倒戈 / 攻心本阶段 DEFER？
31. 如何证明没有第二套伤害 / 恢复 / 状态 / RNG 路径？
```

---

# 52. Stage 7 验收条件

只有以下全部成立，Stage 7 才可进入最终审计：

```text
[ ] RuleHook 强类型合同建立
[ ] Hook 与 BattleContext round 一致性验证建立
[ ] UnitActionStartHook actor existence 验证建立
[ ] TriggerSystem 建立且只产生 Effect
[ ] RuleHookSystem 建立且职责单一
[ ] HookResolutionResult 建立
[ ] 无 Effect 时 HookResolutionResult.effect_results == ()
[ ] RuleHookSystem 不依赖 VictorySystem
[ ] Hook atomic batch policy 实现并测试
[ ] RecoverySystem 建立
[ ] RecoveryPreventionReason 建立
[ ] Recovery prevention precedence 实现并测试
[ ] RecoverEffect 正式接入 RecoverySystem
[ ] RecoverEffect / RecoveryRequest amount 强类型
[ ] RecoveryResolvedResult / RecoveryPreventedResult 建立
[ ] RecoveryPreventedResult reason / reason_state_id 不变量成立
[ ] RecoverEffectResult 正确包装 RecoveryResult
[ ] TroopSystem 仍为唯一兵力写入口
[ ] TroopSystem.restore 输入类型防御建立
[ ] healing_ban 正确阻止恢复
[ ] TARGET_DEFEATED 正确阻止恢复
[ ] actual_recovery == 0 不发布 TROOPS_RECOVERED
[ ] 周期 Damage / Recovery params 类型安全
[ ] source_skill_id 全链保留
[ ] source_state_id 全链保留
[ ] source_state_instance_id 全链保留
[ ] source_state provenance 配对不变量成立
[ ] Damage provenance 仅元数据透传，不改公式
[ ] ROUND_START hook 接入
[ ] UNIT_ACTION_START hook 接入
[ ] hook effect ordering 确定
[ ] hook 杀死 actor 后 lifecycle 正确闭合
[ ] hook batch 后 Victory check 正确
[ ] BattleEngine 无具体状态 / Effect 判断
[ ] EventBus 仍只记录事实
[ ] TriggerSystem 不使用 Python random
[ ] DamageEffect 仍走 DamageResolutionSystem
[ ] State 写仍走 StateLifecycleSystem
[ ] Stage 6 Skill → Effect 边界未破坏
[ ] 未提前加入 reaction queue / damage modifier
[ ] STAGE7_EVIDENCE_MATRIX.md 存在
[ ] 官方状态接入均有 evidence matrix
[ ] evidence matrix 使用 PASS_STAGE7 / DEFER gate
[ ] UNKNOWN 项没有被伪装成官方规则
[ ] Stage 1～6 全回归
[ ] pytest -q success
[ ] python demo.py success
[ ] GitHub Actions success
[ ] 独立最终审计 BLOCKER = 0
[ ] 独立最终审计 MAJOR = 0
```

---

# 53. Stage 7 封版流程

```text
STAGE7.md
↓
第一轮独立设计审计
↓
第一次修订 STAGE7.md
↓
第二轮独立设计复审
↓
第二次修订 STAGE7.md
↓
第三轮快速设计复审
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

# 54. Stage 7 最终目标

Stage 7 成功不是“状态数量突然暴涨”。

真正要冻结的是：

```text
Battle Flow
↓
Explicit Rule Hook
↓
TriggerSystem
↓
ordered Effect(s)
↓
RuleHookSystem
↓
HookResolutionResult
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
RecoveryResolvedResult / RecoveryPreventedResult
↓
TroopSystem
```

同时冻结：

```text
StateInstance
↓
source_skill_id
source_state_id + source_state_instance_id
↓
Effect / Request / Result / Event
```

以及恢复阻止的确定性：

```text
TARGET_DEFEATED
→ HEALING_BAN
→ restore
```

只要这些路径保持单向、类型安全、来源可追踪、确定可测试，后续 Stage 8 Damage Modifier、Stage 9 Reaction / Redirect 和真实技能接入才不需要靠 EventBus 回调、状态对象 execute()、丢失来源的事件或散落 if 分支勉强拼起来。
