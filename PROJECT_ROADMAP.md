# 三国志战略版战斗模拟器 V2 · 项目现状与长期路线图

> 本文是项目级路线图，不替代各阶段的 `STAGE*.md` 施工指南。
>
> 当前状态快照基于 2026-09-04 的 Stage 4 最终封版提交 `e4afe4d2b23645a3843f4943716caa0c3e424624`；Stage 5 当前在独立施工分支进行。后续阶段编号与内容属于规划，必须在进入对应阶段前重新研究、写正式施工文档并审计，不能把本路线图当成不可修改的实现细节。

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
Stage 4 官方状态接入     ✅ FROZEN
Stage 4 最终封版审计     ✅ 完成
Stage 5 Effect          🚧 施工中
Stage 6+                ⏳ 尚未开始
```

Stage 4 封版基线：

```text
pytest -q
→ 80 passed

python demo.py
→ success

GitHub Actions
→ success
```

Stage 4 最终审计见：

```text
STAGE4_FINAL_AUDIT.md
```

Stage 5 正式施工指南：

```text
STAGE5.md
```

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

Stage 3 的核心原则继续冻结：

```text
State = 持续存在的战斗事实
BattleSystem = 解释该事实意味着什么
```

---

# 5. Stage 4：官方状态目录与代表状态验证

Stage 4 已正式 `FROZEN`。

官方静态基线：

```text
40 个具体 BattleState
持续性状态 8
功能性状态 17
控制状态 11
其他 4
```

已实现代表状态：

```text
first_strike / 先攻
ambush / 遇袭
disarm / 缴械
stun / 震慑
weakness / 虚弱
```

其余 35 个状态继续按：

```text
research/official_state_catalog_v1/STATE_SYSTEM_MAPPING_V1.md
```

延后到对应基础设施成熟后实现。

Stage 5 不得为了 Effect 方便改写这些已冻结状态语义。

---

# 6. Stage 5：Effect 与状态运行参数合同

Stage 5 当前施工目标：

```text
Effect
    ↓
EffectExecutor
    ↓
BattleSystem
```

第一批 Effect：

```text
DamageEffect
ApplyStateEffect
RemoveStateEffect
RecoverEffect（仅合同，执行 DEFERRED）
```

同时建立：

```text
StateRuntimeParams
EmptyStateRuntimeParams
StateDefinition.runtime_params_type
StateInstance.runtime_params
```

以及共享伤害协调层：

```text
DamageResolutionSystem
```

目标结构：

```text
NormalAttackSystem ─┐
                    ├→ DamageResolutionSystem
EffectExecutor ─────┘
                         ↓
                    DamageSystem
                         ↓
                    TroopSystem
```

RecoverEffect 当前不得直接调用 `TroopSystem.restore()`；正式恢复执行等待未来 `RecoverySystem`。

详细边界以 `STAGE5.md` 为准。

---

# 7. 当前还没有实现什么

仍未正式建立：

```text
SkillDefinition
SkillRuntime
完整 SkillSystem
TriggerSystem / RuleHookSystem
RecoverySystem
HitResolution
完整 Damage Modifier Pipeline
完整装备系统
BattleReport
Replay
真实战法目录与运行时
```

这些不得被 Stage 5 偷偷提前实现。

---

# 8. 后续阶段统一工作方法

每个阶段继续执行：

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

---

# 9. Stage 6 规划：SkillDefinition / SkillRuntime 基础链

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

进入 Stage 6 前必须先完成 Stage 5 最终审计与封版。

---

# 10. Stage 7 规划：Trigger / Timing / Recovery / 持续效果

Stage 7 建议建立：

```text
TriggerSystem
RecoverySystem
周期 / 行动节点 Effect 触发
```

预计处理持续伤害和恢复类状态，包括：

```text
灼烧
水攻
中毒
溃逃
沙暴
叛逃
急救
休整
禁疗
倒戈
攻心
```

---

# 11. Stage 8 规划：Modifier、命中与伤害裁决链

预计处理：

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

具体结算顺序仍需对应阶段研究后冻结。

---

# 12. Stage 9 规划：重定向、追加行动与反应式机制

预计处理：

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

需要明确递归保护与确定性结算顺序。

---

# 13. Stage 10 规划：高级控制、技能失效与装备

预计处理：

```text
洞察
计穷
伪报
挑拨
破坏
捕获
威慑
```

需要完整 SkillRuntime / Equipment Runtime 等基础设施。

---

# 14. 长期架构红线

```text
Skill → Effect → BattleSystem
EventBus 只记录事实
RandomSystem 是唯一 RNG
State = fact + runtime params
TroopSystem 是唯一兵力写入口
未知规则不猜
```

任何后续阶段都不得为了赶进度破坏这些边界。
