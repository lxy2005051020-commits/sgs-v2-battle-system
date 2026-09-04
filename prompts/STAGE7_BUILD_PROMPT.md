# Stage 7 Build Prompt — Trigger / Rule Hook / Recovery

你现在要继续维护我的项目：

# 三国志战略版战斗模拟器 V2

GitHub 仓库：

`lxy2005051020-commits/sgs-v2-battle-system`

目标：完成 **Stage 7 Trigger / Rule Hook / Recovery** 的正式施工。

---

# 一、开始前必须重新读取最新仓库

不要根据旧聊天记录猜测当前代码，不要只看 README，也不要把本 Prompt 当成比仓库更高的事实来源。

开始施工前必须重新读取：

```text
main 最新 HEAD
PROJECT_STATUS.md
STAGE7.md
STAGE6_FINAL_AUDIT.md
STAGE6.md
PROJECT_ROADMAP.md
```

以及当前实际生产代码，至少包括：

```text
sgs_v2/battle_core/engine.py
sgs_v2/battle_core/battle_systems.py
sgs_v2/battle_core/context.py
sgs_v2/battle_core/events.py
sgs_v2/battle_core/effects.py
sgs_v2/battle_core/effect_result.py
sgs_v2/battle_core/effect_executor.py
sgs_v2/battle_core/damage_system.py
sgs_v2/battle_core/damage_resolution_system.py
sgs_v2/battle_core/troop_system.py
sgs_v2/battle_core/state_definition.py
sgs_v2/battle_core/state_instance.py
sgs_v2/battle_core/state_registry.py
sgs_v2/battle_core/state_lifecycle_system.py
sgs_v2/battle_core/state_runtime_params.py
sgs_v2/battle_core/official_state_catalog.py
sgs_v2/battle_core/skill_definition.py
sgs_v2/battle_core/skill_runtime.py
sgs_v2/battle_core/skill_resolver.py
sgs_v2/battle_core/__init__.py
```

并检查：

```text
tests/
.github/workflows/
demo.py
```

若最新 `main` 与本 Prompt 生成时相比已有变化，以最新生产代码、测试、Actions、`PROJECT_STATUS.md` 和 `STAGE7.md` 为准。

---

# 二、权威顺序

发生冲突时按以下优先级处理：

```text
1. 当前生产代码
2. 当前测试
3. GitHub Actions
4. PROJECT_STATUS.md
5. STAGE7.md
6. Stage 6 FINAL AUDIT / Stage 6 frozen spec
7. PROJECT_ROADMAP.md
8. 本 Prompt
9. 旧聊天记录
```

对于 Stage 7 的设计边界：

```text
STAGE7.md
```

是唯一正式施工规范。

本 Prompt 的用途是把 `STAGE7.md` 转换为可执行施工任务，不允许自行重新设计 Stage 7。

---

# 三、施工分支

不要直接在 `main` 上开发 Stage 7 生产代码。

从施工开始时的最新 `main` 创建独立分支，建议：

```text
stage7-trigger-recovery
```

施工完成后先在该分支完成：

```text
pytest -q
python demo.py
GitHub Actions
独立实现审计
```

在最终审计通过前不要合并 `main`，不要标记 Stage 7 FROZEN。

---

# 四、Stage 7 已通过设计审计

Stage 7 已完成三轮设计审计。

第三轮收口审计结论：

```text
BLOCKER   = 0
MAJOR     = 0
MINOR     = 1
HARDENING = 2

VERDICT = READY FOR STAGE 7 BUILD
```

第三轮剩余项不阻止施工，但本次施工必须直接吸收：

```text
1. 显式定义：
   RuleHook = RoundStartHook | UnitActionStartHook

2. UnitActionStartHook 在 RuleHookSystem 边界除 actor existence 外，
   还应防御性验证 actor 在 hook 入口仍为 alive；
   production Engine 本身仍需保持死亡 actor 不进入 UNIT_ACTION_START。

3. HookResolutionResult.effect_results：
   - canonicalize 为 tuple
   - 验证每个成员都是合法 EffectExecutionResult variant
```

不要为这三项另起一套架构。

---

# 五、Stage 7 核心目标

Stage 7 要冻结的第一条主链：

```text
Battle Flow
↓
Explicit RuleHook
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

第二条主链：

```text
RecoverEffect
↓
EffectExecutor
↓
RecoverySystem
↓
TroopSystem.restore
```

第三条来源链：

```text
StateInstance
↓
source_skill_id
source_state_id + source_state_instance_id
↓
Effect
↓
Request
↓
Result
↓
BattleEvent payload
```

必须保持单向依赖、强类型、确定性和可审计性。

---

# 六、绝对红线

禁止出现：

```text
EventBus subscribe → 自动执行状态规则
StateInstance.execute()
StateRuntimeParams.execute()
TriggerSystem 直接扣兵
TriggerSystem 直接恢复兵力
TriggerSystem 直接写 StateRegistry
TriggerSystem 调用 DamageSystem / DamageResolutionSystem
TriggerSystem 调用 EffectExecutor
TriggerSystem import random
RecoverySystem 直接 target.troops += ...
RecoverySystem 调用 TriggerSystem
RecoverySystem 调用 EffectExecutor
RecoverySystem 调用 VictorySystem
RuleHookSystem 认识具体 state_id
RuleHookSystem 依赖 VictorySystem
BattleEngine 认识 burn / poison / recuperation 等状态名
BattleEngine 判断 DamageEffect / RecoverEffect 类型
SkillRuntime 监听 EventBus
SkillRuntime 执行 Effect
SkillResolver 直接执行 Effect
具体 skill_id / skill.name 特判进入核心
第二套伤害计算路径
第二套兵力写入口
第二套状态写入口
Python random 绕过 RandomSystem
```

EventBus 必须继续是：

```text
已经发生事实的记录 / 分发器
```

而不是规则引擎。

---

# 七、第一步必须先建立 Stage 7 Evidence Matrix

在实现任何官方周期状态的 production mapping 前，先创建：

```text
research/stage7_evidence_matrix/STAGE7_EVIDENCE_MATRIX.md
```

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

硬 Gate：

若仍存在会改变**单实例基础行为**的关键 UNKNOWN，例如：

```text
trigger node 无法确定
damage type 无法确定
基础公式 / coefficient 语义无法确定
source attribution 无法确定
恢复 amount 的工程来源无法确定
```

则必须：

```text
implementation verdict = DEFER
```

不得根据经验猜一个规则，然后声称官方状态已实现。

以下未知项若本阶段明确不解决，可以保留 DEFER，不必阻止 synthetic 基础设施施工：

```text
同名 stacking
refresh
最高值覆盖
同源 / 异源竞争
```

但必须明确：

```text
多实例 deterministic execution
≠ 官方 stacking 规则
```

目前允许直接进入 Stage 7 policy 的状态：

```text
healing_ban
```

以下状态只有 Evidence Matrix 为 `PASS_STAGE7` 后才能加入 production Trigger mapping：

```text
burn
flood
poison
rout
sandstorm
recuperation
```

如果证据不够，就 DEFER，并使用 synthetic StateDefinition / StateInstance 完成 RuleHook / Trigger / Recovery 基础设施测试。

---

# 八、明确 DEFER，禁止偷做

Stage 7 不正式实现：

```text
rebellion
first_aid
weapon_lifesteal
strategy_lifesteal
```

原因：

```text
rebellion
→ 需要 Stage 8 正式 Damage Modifier / ignore-defense pipeline

first_aid
weapon_lifesteal
strategy_lifesteal
→ 需要 AFTER_DAMAGE reaction / queue
```

同时禁止提前实现：

```text
AFTER_DAMAGE recursive reaction queue
HitResolution
Damage Modifier Pipeline
反击
群攻
连击
Damage Redirect / Split / Share
援护
StateApplicationPolicy
控制免疫完整政策
完整 Skill disable policy
装备运行态
BattleReport / Replay
API / 批量模拟 / 性能优化
```

---

# 九、RuleHook 强类型合同

新增不可变强类型：

```text
RoundStartHook
UnitActionStartHook
```

正式类型别名必须显式定义：

```python
RuleHook = RoundStartHook | UnitActionStartHook
```

不要建立：

```text
任意 payload dict
几十个无消费者的 timing enum
万能 Hook base class + dict
```

最小字段：

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

`RuleHookSystem.process(context, hook)` 边界必须验证：

```text
hook.round_no == context.current_round
```

对于 `UnitActionStartHook` 还必须验证：

```text
hook.actor_id in context.units
actor 在 hook 入口仍为 alive
```

若不合法：明确失败，不得静默当成“无 Effect”。

---

# 十、TriggerSystem

正式职责：

```text
输入：BattleContext + typed RuleHook
输出：tuple[Effect, ...]
```

TriggerSystem 可以读取：

```text
StateRegistry
StateInstance.runtime_params
StateInstance.source_id
StateInstance.source_skill_id
StateInstance.state_id
StateInstance.instance_id
```

只负责根据 hook 产生 ordered Effects。

不得执行任何 Effect。

确定性顺序：

```text
同一 hook 匹配多个 StateInstance
→ instance_id 升序

单一 StateInstance 产生多个 Effect
→ 明确 declaration / handler 顺序
```

Stage 7 第一版周期触发不额外做概率裁决。

未来若需要概率，只能使用：

```text
context.random / RandomSystem
```

---

# 十一、RuleHookSystem

职责严格限定为：

```text
验证 RuleHook
↓
TriggerSystem.collect
↓
ordered Effects
↓
逐个 EffectExecutor.execute
↓
HookResolutionResult
```

不得负责：

```text
Victory
具体状态识别
伤害公式
恢复政策
RNG
```

构造依赖必须是最小依赖：

```text
TriggerSystem
EffectExecutor
```

不得注入整个 `BattleSystems`。

---

# 十二、HookResolutionResult

正式实现：

```python
@dataclass(frozen=True, slots=True)
class HookResolutionResult:
    hook: RuleHook
    effect_results: tuple[EffectExecutionResult, ...]
```

要求：

```text
无 Effect 时返回 effect_results=()
绝不返回 None
canonicalize effect_results 为 tuple
验证每个成员属于合法 EffectExecutionResult variant
结果数量与 TriggerSystem.collect 的 Effect 数量一致
顺序严格一一对应
```

不要重复保存：

```text
effects
```

因为 EffectExecutionResult 已携带其 Effect。

不要保存：

```text
BattleResult
VictoryResult
terminal flag
```

---

# 十三、Hook atomic batch

Stage 7 v1 正式采用：

```text
一个 RuleHook
→ collect 一次 Effect tuple
→ 全部 Effect 按顺序执行
→ RuleHookSystem 返回
→ BattleEngine 再调用 VictorySystem.check
```

即使较早 Effect 已击杀主将，同一 hook batch 中后续 Effects 仍继续执行。

这是：

```text
D = ENGINEERING DECISION
```

不是官方结算时序声明。

RuleHookSystem 不得为此引入 VictorySystem。

---

# 十四、BattleEngine 接入

## ROUND_START

冻结流程：

```text
enter ROUND_START
↓
StateLifecycleSystem.expire_at(ROUND_START)
↓
ROUND_STARTED
↓
RuleHookSystem.process(RoundStartHook)
↓
VictorySystem.check
↓
terminal → BATTLE_END
否则 → ACTION_ORDER
```

因此到期状态不会再在该 ROUND_START 触发。

## UNIT_ACTION_START

冻结流程：

```text
order 中 actor 若进入时已死亡
→ continue

否则：
enter UNIT_ACTION_START
↓
UNIT_ACTION_STARTED
↓
RuleHookSystem.process(UnitActionStartHook)
↓
VictorySystem.check
↓
如果无 terminal 且 actor 仍 alive
    → UNIT_ACTION
    → ActionSystem.execute
    → VictorySystem.check
否则
    → 跳过 ActionSystem
↓
UNIT_ACTION_END
↓
UNIT_ACTION_ENDED
↓
若 terminal
    → BATTLE_END
```

必须保持：

```text
hook 击杀副将
→ 跳过 ActionSystem
→ 仍有 UNIT_ACTION_ENDED

hook 击杀主将
→ 跳过 ActionSystem
→ UNIT_ACTION_ENDED
→ BATTLE_ENDED
```

`UNIT_ACTION_ENDED` 表示行动生命周期闭合，不代表成功进行了普通攻击。

BattleEngine 不得出现具体状态 / Effect 类型判断。

---

# 十五、State provenance

Stage 7 必须给周期状态产生的 Effect 增加完整来源：

```text
source_skill_id
source_state_id
source_state_instance_id
```

`source_state_id` 和 `source_state_instance_id` 必须满足：

```text
both None
或
both non-None
```

禁止：

```text
state_id / None
None / instance_id
```

该不变量至少覆盖：

```text
DamageEffect
DamageRequest
DamageResult
RecoverEffect
RecoveryRequest
RecoveryResult（经 request）
```

状态触发：

```text
source_state_id = state.state_id
source_state_instance_id = state.instance_id
```

非状态来源：

```text
None / None
```

---

# 十六、Damage 链只能做 provenance 扩展

允许对：

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

必须向后兼容现有 Stage 1～6 调用方。

禁止借 Stage 7 修改：

```text
基础兵刃伤害公式
基础谋略伤害公式
DamageType 语义
weakness 阻止逻辑
伤害随机逻辑
```

DamageEffect 仍然必须：

```text
EffectExecutor
→ DamageResolutionSystem
→ DamageSystem + TroopSystem
```

不得出现第二套伤害路径。

---

# 十七、Stage 7 StateRuntimeParams

新增：

```text
PeriodicDamageStateParams
PeriodicRecoveryStateParams
```

## PeriodicDamageStateParams

字段：

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
finite
>= 0
规范化为 float
```

## PeriodicRecoveryStateParams

字段：

```text
amount: int
```

要求：

```text
frozen dataclass
slots
必须是 int
bool reject
>= 0
```

不要建立：

```text
dict[str, Any] runtime payload
callable handler
state.execute
```

若官方周期状态通过 Evidence Matrix，则只更新对应 `StateDefinition.runtime_params_type`，不要把所有 40 个状态改成 generic params。

---

# 十八、RecoverEffect 加固

当前 RecoverEffect 从 Stage 5 的 DEFERRED 路径正式进入真实执行，所以施工前必须强化合同。

正式字段：

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
target_id 非空、非纯空白
所有 optional ID 提供时非空、非纯空白
source_state_id / source_state_instance_id 必须成对
amount 必须 int
bool reject
amount >= 0
```

RecoverEffect 必须保持纯数据、不可变、无副作用。

---

# 十九、RecoveryRequest

正式字段：

```text
source_id: str | None
target_id: str
amount: int
source_skill_id: str | None
source_state_id: str | None
source_state_instance_id: str | None
```

验证与 RecoverEffect 一致。

---

# 二十、RecoveryPreventionReason / RecoveryResult

新增强类型枚举：

```text
RecoveryPreventionReason.HEALING_BAN
RecoveryPreventionReason.TARGET_DEFEATED
```

禁止任意字符串 reason。

RecoveryResult 使用联合类型：

```text
RecoveryResolvedResult
RecoveryPreventedResult

RecoveryResult = RecoveryResolvedResult | RecoveryPreventedResult
```

## RecoveryResolvedResult

至少：

```text
request: RecoveryRequest
troop_change: TroopChangeResult
```

## RecoveryPreventedResult

至少：

```text
request: RecoveryRequest
reason: RecoveryPreventionReason
reason_state_id: str | None
```

严格不变量：

```text
reason == HEALING_BAN
→ reason_state_id == OfficialStateId.HEALING_BAN.value

reason == TARGET_DEFEATED
→ reason_state_id is None
```

被阻止时不得伪造 TroopChangeResult。

---

# 二十一、RecoverySystem

职责：

```text
解析目标
恢复政策裁决
死亡目标阻止
healing_ban 判定
调用 TroopSystem.restore
发布恢复事实
返回 RecoveryResult
```

正式裁决优先级：

```text
1. target_id 无法解析
   → 明确失败，不返回 PREVENTED

2. target defeated
   → TARGET_DEFEATED
   → RECOVERY_PREVENTED
   → 不调用 restore

3. target 有 healing_ban
   → HEALING_BAN
   → RECOVERY_PREVENTED
   → 不调用 restore

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
```

RecoverySystem 不负责 Victory，不实现复活。

---

# 二十二、TroopSystem.restore 类型加固

TroopSystem 继续是唯一实际兵力写入口。

`restore()` 增加防御性验证：

```text
requested_recovery 必须是 int
bool reject
>= 0
```

但禁止 TroopSystem 判断：

```text
healing_ban
source state
skill type
复活
```

这些是 RecoverySystem 的政策。

---

# 二十三、恢复事实事件

新增：

```text
RECOVERY_PREVENTED
TROOPS_RECOVERED
```

## RECOVERY_PREVENTED payload 至少：

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

`reason` 使用 `RecoveryPreventionReason.value`。

## TROOPS_RECOVERED payload 至少：

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

满兵时：

```text
RecoveryResolvedResult(actual_change=0)
```

合法，但：

```text
actual_change == 0
→ 不发布 TROOPS_RECOVERED
```

EventBus 只记录实际发生的事实。

---

# 二十四、EffectExecutor 正式接入 RecoverySystem

Stage 5/6 历史：

```text
RecoverEffect
→ DeferredEffectResult
→ RECOVERY_SYSTEM_NOT_AVAILABLE
```

Stage 7 完成后：

```text
RecoverEffect
→ RecoveryRequest
→ RecoverySystem.resolve
→ RecoveryResult
→ RecoverEffectResult
```

`RecoverEffectResult.status`：

```text
EffectExecutionStatus.RESOLVED
```

即使 RecoveryResult 是 PREVENTED，也仍属于 Effect 已被规则正常解析，不是 DEFERRED，也不是异常。

施工完成后：

```text
RECOVERY_SYSTEM_NOT_AVAILABLE
```

不再是 RecoverEffect 的正常 production 返回路径。

---

# 二十五、官方状态接入

## healing_ban

Stage 7 正式接入：

```text
RecoverySystem policy
```

不要放进 TroopSystem。

## 周期状态

只有 Evidence Matrix `PASS_STAGE7` 才能接：

```text
burn
flood
poison
rout
sandstorm
recuperation
```

若通过：

```text
ROUND_START
或
UNIT_ACTION_START
```

具体映射必须严格服从 Evidence Matrix，不可根据状态名字猜 timing / damage type / coefficient。

真实状态参数来自：

```text
StateInstance.runtime_params
```

不能把伤害率、恢复量、持续回合写成状态固定常量。

---

# 二十六、推荐文件

可新增：

```text
sgs_v2/battle_core/rule_hooks.py
sgs_v2/battle_core/trigger_system.py
sgs_v2/battle_core/rule_hook_system.py
sgs_v2/battle_core/recovery_system.py
sgs_v2/battle_core/stage7_state_params.py
```

必要时修改：

```text
sgs_v2/battle_core/effects.py
sgs_v2/battle_core/effect_result.py
sgs_v2/battle_core/effect_executor.py
sgs_v2/battle_core/events.py
sgs_v2/battle_core/damage_system.py
sgs_v2/battle_core/damage_resolution_system.py
sgs_v2/battle_core/troop_system.py
sgs_v2/battle_core/official_state_catalog.py
sgs_v2/battle_core/battle_systems.py
sgs_v2/battle_core/engine.py
sgs_v2/battle_core/__init__.py
```

研究交付：

```text
research/stage7_evidence_matrix/STAGE7_EVIDENCE_MATRIX.md
```

不得为了 Stage 7 重构无关模块。

---

# 二十七、BattleSystems 组合要求

保持最小依赖：

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

不得：

```text
TriggerSystem(BattleSystems)
RecoverySystem(BattleSystems)
RuleHookSystem(BattleSystems)
```

避免万能依赖和循环。

---

# 二十八、测试要求

至少新增或等价覆盖：

```text
tests/test_recovery_system.py
tests/test_trigger_system.py
tests/test_rule_hook_system.py
tests/test_stage7_engine_hooks.py
tests/test_stage7_provenance.py
tests/test_stage7_state_params.py
tests/test_stage7_architecture.py
```

并覆盖 Evidence Matrix gate。

## RecoverySystem

必须测试：

```text
正常恢复走 TroopSystem.restore
恢复不超过 max_troops
TARGET_DEFEATED 阻止
healing_ban 阻止
被阻止时不调用 restore
裁决 precedence
dead + healing_ban → TARGET_DEFEATED
full + healing_ban → HEALING_BAN
full + no ban → Resolved(0)
Resolved(0) 不发布 TROOPS_RECOVERED
RECOVERY_PREVENTED payload
TROOPS_RECOVERED payload
provenance 完整
死亡单位不复活
RecoverySystem 不直接写 troops
```

## 类型反例

必须测试：

```text
RecoverEffect.amount=True reject
RecoverEffect.amount=1.5 reject
RecoverEffect.amount<0 reject
RecoveryRequest 同类反例
TroopSystem.restore(True) reject
TroopSystem.restore(1.5) reject
非法 RecoveryPreventionReason reject
TARGET_DEFEATED + reason_state_id 非 None reject
HEALING_BAN + reason_state_id 缺失/错误 reject
```

## RuleHook / TriggerSystem

必须测试：

```text
RuleHook union alias
RoundStartHook typed
UnitActionStartHook typed
round_no < 1 reject
bool round_no reject
actor_id 空/空白 reject
round mismatch reject
actor 不存在 reject
actor dead at hook entry reject
无关 hook → no Effects
只读取有效 StateInstance
instance_id 确定排序
TriggerSystem 只产生 Effects
不执行 Effects
不修改 troops
不写 StateRegistry
不 import random
```

## HookResolutionResult

必须测试：

```text
无 Effect → effect_results=()
不返回 None
一个 Effect → 一个 result
多个 Effect → 数量与顺序严格对应
保存 typed hook
canonicalize tuple
非法 result member reject
不保存 Victory / terminal
```

## provenance

必须端到端测试：

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

并测试：

```text
None / None valid
state_id / instance_id valid
state_id / None reject
None / instance_id reject
```

## Hook atomic batch

构造 synthetic：

```text
Effect 1 = lethal DamageEffect
Effect 2 = another legal Effect
```

验证：

```text
Effect 1 执行
Effect 2 仍执行
顺序一致
RuleHookSystem 不调用 VictorySystem
batch 后 Engine 才检查 Victory
HookResolutionResult 顺序一致
```

## Engine lifecycle

必须验证：

```text
ROUND_START expire 先于 Hook
ROUND_STARTED 后调用 RoundStartHook
ROUND_START hook 后检查 Victory

UNIT_ACTION_STARTED 后调用 UnitActionStartHook
hook 杀 actor 后不调用 ActionSystem
hook 杀副将仍 UNIT_ACTION_ENDED
hook 杀主将仍 UNIT_ACTION_ENDED → BATTLE_ENDED
hook 未杀 actor 保持原流程
```

---

# 二十九、Architecture Tests

优先 AST / import inspection，不要靠扫描注释字符串制造脆弱测试。

至少验证：

```text
TriggerSystem
- no Python random
- no TroopSystem
- no DamageSystem
- no DamageResolutionSystem
- no StateLifecycleSystem write
- no EffectExecutor

RecoverySystem
- no direct UnitRuntime.troops assignment
- only TroopSystem for troop mutation
- no TriggerSystem
- no EffectExecutor
- no VictorySystem

RuleHookSystem
- no VictorySystem
- no OfficialStateId / specific state strings
- only coordinates TriggerSystem + EffectExecutor

BattleEngine
- no OfficialStateId / specific state branches
- no DamageEffect / RecoverEffect type branches

EventBus
- no production rule subscriptions

DamageSystem Stage 7 diff
- provenance only
- no formula semantic change
```

---

# 三十、Stage 1～6 全回归

必须保证所有现有测试继续通过。

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

对 Stage 5/6 数据合同增加字段必须使用向后兼容默认值，不得逼迫旧调用方无意义修改。

---

# 三十一、完成验证

施工完成后必须运行并记录：

```text
pytest -q
python demo.py
```

并确认 GitHub Actions 对**施工分支 exact HEAD**：

```text
status = completed
conclusion = success
```

报告实际测试数量，不要预设它一定是多少。

如果测试或 CI 失败，先修复，不得用“主要功能完成”替代验证。

---

# 三十二、施工完成后的报告格式

完成后给出：

```text
1.施工分支名称
2.施工分支 exact HEAD SHA
3.相对 main 的 ahead / behind
4.新增生产文件
5.修改生产文件
6.新增/修改测试
7.Evidence Matrix 路径与 PASS_STAGE7 / DEFER 结论
8.实际接入的官方状态列表
9.明确 DEFER 的状态列表
10.RuleHook / TriggerSystem 实际结构
11.RecoverySystem 实际结构
12.provenance 全链说明
13.Engine hook 生命周期说明
14.pytest 结果
15.demo 结果
16.GitHub Actions exact HEAD 结果
17.是否存在已知 BLOCKER / MAJOR 风险
18.是否建议进入 Stage 7 independent implementation audit
```

---

# 三十三、禁止提前封版

施工完成、测试全绿、CI success 只代表：

```text
STAGE 7 IMPLEMENTATION CANDIDATE READY FOR AUDIT
```

不代表：

```text
STAGE 7 FROZEN
```

下一步必须是：

```text
独立 Stage 7 实现审计
↓
修复（如需要）
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

在此之前不要修改 `PROJECT_STATUS.md` 为 FROZEN，也不要开始 Stage 8。

---

# 三十四、最终施工原则

不要追求“本阶段实现多少个状态”。

Stage 7 真正成功的标准是：

```text
RuleHook 明确
TriggerSystem 只产 Effects
EffectExecutor 仍是统一 Effect 路由
RecoverySystem 成为统一恢复政策入口
TroopSystem 仍是唯一兵力写入口
DamageSystem 仍是统一理论伤害入口
StateLifecycleSystem 仍是统一状态写入口
EventBus 仍然只记录事实
来源 provenance 不丢失
行为顺序可确定、可测试
未知官方规则明确 DEFER
```

按 `STAGE7.md` 完整施工，不擅自扩展 Stage 8 / Stage 9，不为方便建立第二套路径。