# 三国志战略版战斗模拟器 V2 · Stage 5 最终封版审计

> 本文记录 Stage 5 的最终独立审计与封版结论。Stage 5 的施工边界仍以 `STAGE5.md` 为准；Stage 4 已冻结规则继续以 `STAGE4.md`、`STAGE4_FINAL_AUDIT.md` 和官方状态研究目录为准。

审计基线：

```text
Stage 4 FROZEN 基线：e4afe4d2b23645a3843f4943716caa0c3e424624
Stage 5 最终施工分支：stage5-effect
最终审计前分支头：33f0885fe8201955b12cd6cee00facc20984fe26
```

结论：

```text
BLOCKER: 0
MAJOR:   0（已发现的 1 个文档 MAJOR 已修复）
MINOR:   0 个未解决封版项
```

本文所在提交进入 `main` 且 GitHub Actions 成功后，Stage 5 正式标记为 `FROZEN`。

---

# 1. 审计范围

重新检查：

```text
STAGE5.md
prompts/STAGE5_BUILD_PROMPT.md

sgs_v2/battle_core/
├─ state_runtime_params.py
├─ state_definition.py
├─ state_instance.py
├─ state_lifecycle_system.py
├─ damage_resolution_system.py
├─ effects.py
├─ effect_result.py
├─ effect_executor.py
├─ normal_attack_system.py
├─ battle_systems.py
└─ __init__.py

Stage 1/2/3/4 全部既有测试
Stage 5 新增测试
PROJECT_ROADMAP.md 差异完整性
GitHub Actions / demo.py
```

---

# 2. StateRuntimeParams 审计

Stage 5 已建立：

```text
StateRuntimeParams
EmptyStateRuntimeParams
StateDefinition.runtime_params_type
StateInstance.runtime_params
```

结论：

```text
✅ runtime params 不是 dict[str, Any] 运行时逃生门
✅ 正式参数 schema 必须是 StateRuntimeParams 子类
✅ schema 必须显式声明为 frozen dataclass
✅ StateDefinition 在定义阶段验证 schema
✅ StateInstance 保存不可变参数实例
✅ StateLifecycleSystem.apply 验证实例类型与 Definition schema 一致
✅ 无参数旧状态默认使用 EmptyStateRuntimeParams
✅ 参数化状态缺少必需 params 时被拒绝
✅ 同一状态多个实例仍可携带不同参数并共存
✅ STATE_APPLIED / REMOVED / EXPIRED 可记录参数类型和值
```

事件中的 `runtime_params` dict 只是 EventBus 的审计序列化，不是运行时参数合同。

---

# 3. State 责任边界

重新确认：

```text
StateDefinition
= 静态定义 + 参数 schema

StateInstance
= 战斗事实 + 来源 + 生命周期 + 实际参数

StateLifecycleSystem
= apply / remove / expire

BattleSystem
= 解释状态事实的行为语义
```

未发现：

```text
StateRuntimeParams 执行行为
StateLifecycleSystem 扣兵
StateLifecycleSystem 选目标
StateLifecycleSystem 计算伤害
StateLifecycleSystem 直接执行 Effect
```

Stage 3 架构边界保持成立。

---

# 4. DamageResolutionSystem 审计

Stage 5 已抽出共享：

```text
DamageResolutionSystem
```

职责：

```text
DamageSystem.calculate
        ↓
DamageResult
        ↓
prevented ?
├─ yes → DAMAGE_PREVENTED
└─ no
   ↓
TroopSystem.apply_damage
   ↓
DAMAGE_DEALT
   ↓
必要时 UNIT_DEFEATED
```

结论：

```text
✅ DamageSystem 仍然只计算理论伤害
✅ TroopSystem 仍是实际兵力写入口
✅ DAMAGE_PREVENTED 统一由共享协调层发布
✅ DAMAGE_DEALT 统一由共享协调层发布
✅ UNIT_DEFEATED 统一由共享协调层发布
✅ 被阻止伤害不调用 TroopSystem
✅ 已死亡目标不会被重复发布新的 UNIT_DEFEATED
```

---

# 5. NormalAttackSystem 迁移审计

Stage 4 冻结语义要求：

```text
缴械
→ ACTION_BLOCKED

虚弱普攻
→ NORMAL_ATTACK
→ DAMAGE_PREVENTED

正常普攻
→ NORMAL_ATTACK
→ DAMAGE_DEALT
→ 可选 UNIT_DEFEATED
```

迁移后：

```text
NormalAttackSystem
= 缴械门控 + 选目标 + NORMAL_ATTACK 事实

DamageResolutionSystem
= 伤害落地与 DAMAGE_* / UNIT_DEFEATED
```

测试确认 Stage 4 事件顺序未漂移。

结论：

```text
✅ 缴械仍在目标选择前阻止
✅ 震慑仍由 ActionSystem 更高层阻止
✅ 虚弱仍在基础伤害公式前阻止
✅ NORMAL_ATTACK 仍先于 DAMAGE_PREVENTED / DAMAGE_DEALT
✅ NormalAttackSystem 不再自己调用 TroopSystem.apply_damage
✅ NormalAttackSystem 不再拥有 DAMAGE_* / UNIT_DEFEATED 发布逻辑
```

---

# 6. Effect 模型审计

已建立不可变：

```text
DamageEffect
ApplyStateEffect
RemoveStateEffect
RecoverEffect
```

Effect 只保存意图数据，不持有 BattleContext / BattleSystem。

结论：

```text
✅ Effect frozen + slots
✅ Effect 不直接修改 UnitRuntime
✅ Effect 不直接写 StateRegistry
✅ Effect 不直接消费 RNG
✅ Effect 不执行伤害或恢复
```

`DamageEffect.to_request()` 只是无副作用的数据转换，不执行战斗规则。

---

# 7. EffectExecutor 审计

当前路由：

```text
DamageEffect
→ DamageResolutionSystem

ApplyStateEffect
→ StateLifecycleSystem.apply

RemoveStateEffect
→ StateLifecycleSystem.remove

RecoverEffect
→ DeferredEffectResult
```

结论：

```text
✅ EffectExecutor 不计算伤害公式
✅ EffectExecutor 不直接修改 troops
✅ EffectExecutor 不直接写 context.states
✅ EffectExecutor 不选择目标
✅ EffectExecutor 不调用 random
✅ Apply / Remove State 仍通过 StateLifecycleSystem
✅ DamageEffect 与普通攻击共用 DamageResolutionSystem
```

---

# 8. RecoverEffect 审计

Stage 5 明确不建立 RecoverySystem。

当前：

```text
RecoverEffect
→ DEFERRED
→ reason = RECOVERY_SYSTEM_NOT_AVAILABLE
```

并验证：

```text
✅ 不调用 TroopSystem.restore
✅ 不改变兵力
✅ 不提前实现禁疗 / 急救 / 休整 / 倒戈 / 攻心
```

因此没有为了“Effect 看起来完整”而建立错误的第二套恢复路径。

---

# 9. EffectResult 审计

已建立类型化结果：

```text
DamageEffectResult
ApplyStateEffectResult
RemoveStateEffectResult
DeferredEffectResult
```

不是一个塞满可空字段的万能 Result。

状态字段：

```text
RESOLVED
DEFERRED
```

已经加固为 `init=False` 固定值，调用方不能构造矛盾结果，例如：

```text
DeferredEffectResult(status=RESOLVED)
```

---

# 10. BattleSystems / BattleEngine 审计

BattleSystems 新增组合：

```text
DamageResolutionSystem
EffectExecutor
```

构造关系：

```text
DamageSystem + TroopSystem
→ DamageResolutionSystem

DamageResolutionSystem + StateLifecycleSystem
→ EffectExecutor

TargetSystem + DamageResolutionSystem
→ NormalAttackSystem
```

BattleEngine 未接入具体 Effect 执行。

结论：

```text
✅ BattleEngine 不认识 DamageEffect
✅ BattleEngine 不认识 ApplyStateEffect
✅ BattleEngine 不认识 RemoveStateEffect
✅ BattleEngine 不认识 RecoverEffect
✅ BattleEngine 不认识 EffectExecutor
```

这符合 Stage 5 尚无 SkillRuntime / TriggerSystem 的边界。

---

# 11. RNG 审计

静态架构测试继续验证：

```text
除 random_system.py 外
battle_core/*.py
不得 import random
```

EffectExecutor 源码也不持有 `context.random` 调用。

结论：

```text
✅ RandomSystem 仍为唯一战斗 RNG 封装
✅ DamageEffect 的伤害随机仍由 DamageSystem / 公式层产生
✅ ApplyStateEffect 不擅自做概率判定
```

---

# 12. Stage 4 FROZEN 回归

Stage 5 没有修改：

```text
官方 40 状态目录
官方 Hint ID
官方原文
先攻 / 遇袭工程交互规则
ActionOrderSystem
ActionSystem
DamageSystem 中虚弱规则
OfficialStateId
```

普通攻击仅进行了职责抽取，并通过专门事件顺序回归测试。

因此 Stage 4 规则语义保持冻结。

---

# 13. 施工过程中发现并修复的问题

## 13.1 第一轮 CI 测试问题

第一轮 Stage 5 CI：

```text
101 passed
2 failed
1 warning
```

两个失败均来自新测试自身：

```text
1. 非击杀样例目标兵力设置过低，实际被击杀，导致最后事件是 UNIT_DEFEATED。
2. 静态源码测试错误匹配了注释里的 DAMAGE_DEALT 字符串。
```

另有 pytest fixture 类命名告警。

修复后全部通过。

## 13.2 参数合同加固

审计发现：

```text
普通 StateRuntimeParams 子类如果未显式 @dataclass，
可能仅继承父类 dataclass 元信息。
```

已修复为：

```text
参数 schema 必须在类自身显式拥有 __dataclass_params__
且 frozen=True
```

## 13.3 EffectResult 状态加固

审计发现结果 status 默认值原本仍可由构造参数覆盖。

已改为：

```text
field(..., init=False)
```

确保结果类型与状态不可矛盾。

## 13.4 PROJECT_ROADMAP.md 文档回归

施工中曾错误地为了更新阶段状态而重写长期路线图，造成：

```text
PROJECT_ROADMAP.md
819 行历史/规划内容被误删
```

严重级别：

```text
MAJOR（文档完整性）
```

已在施工分支中精确恢复到 Stage 4 封版 blob，最终差异中 `PROJECT_ROADMAP.md` 已不存在任何修改。

长期阶段状态以后使用 `PROJECT_STATUS.md` 单独维护，避免再次通过整文件重写破坏路线图。

---

# 14. 最终差异审计

Stage 4 FROZEN 基线到 Stage 5 最终施工头的差异只包含：

```text
STAGE5.md
prompts/STAGE5_BUILD_PROMPT.md
Stage 5 核心模块
必要的 Stage 3/4 接入修改
Stage 5 测试
```

`PROJECT_ROADMAP.md` 已恢复，无意外删除。

未发现：

```text
真实战法
SkillRuntime
TriggerSystem
RecoverySystem
新的具体官方状态效果
BattleEngine 具体 Effect 判断
直接 Python random
第二个兵力写入口
第二个状态写入口
```

---

# 15. 最终自动验证

最终施工分支提交 `33f0885fe8201955b12cd6cee00facc20984fe26` 的 GitHub Actions 实际结果：

```text
pytest -q
→ 105 passed in 0.40s

python demo.py
→ success

GitHub Actions
→ success
```

Stage 4 封版时为 80 tests，因此 Stage 5 新增并通过 25 个测试。

---

# 16. FROZEN 条件

Stage 5 当前满足：

```text
✅ Effect 数据模型
✅ EffectExecutor
✅ DamageResolutionSystem
✅ StateRuntimeParams
✅ 类型化 EffectResult
✅ RecoverEffect 明确 DEFERRED
✅ Stage 4 回归
✅ 105 tests 全绿
✅ demo.py success
✅ 施工分支 GitHub Actions success
✅ 最终差异审计无未解决 BLOCKER / MAJOR
```

最后一步：

```text
本文所在提交进入 main
→ main GitHub Actions success
→ Stage 5 FROZEN
```

---

# 17. 下一阶段边界

Stage 5 FROZEN 后进入 Stage 6：

```text
SkillDefinition
→ SkillRuntime
→ Effect
→ EffectExecutor
```

Stage 6 的目标是证明战法运行时只产生 Effect，不直接侵入 BattleSystem。

在 Stage 6 之前仍不要批量接入真实战法，也不要把 EventBus 改成规则引擎。