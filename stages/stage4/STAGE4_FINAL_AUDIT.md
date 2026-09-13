# 三国志战略版战斗模拟器 V2 · Stage 4 最终封版审计

> 本文记录 Stage 4 的最终独立封版审计结果。它不是新的施工规范；Stage 4 的功能边界仍以 `STAGE4.md`、`stages/stage3/STAGE3.md` 与 `research/official_state_catalog_v1/` 为准。
>
> 审计起点：`main` 提交 `5124e4978ec7241b5d89f97630ac5342ac48932e`（2026-09-04）。
>
> 结论：**未发现 BLOCKER 或 MAJOR。Stage 4 达到封版条件。本文所在提交的 GitHub Actions 全部成功后，Stage 4 状态正式为 `FROZEN`。**

---

# 1. 审计范围

本次最终审计重新检查：

```text
PROJECT_ROADMAP.md
stages/stage3/STAGE3.md
STAGE4.md
research/README.md

research/official_state_catalog_v1/
├─ OFFICIAL_STATE_CATALOG_V1.md
├─ official_state_rules_v1.csv
├─ STATE_SYSTEM_MAPPING_V1.md
└─ PROJECT_STATE_INTERACTIONS_V1.md

sgs_v2/battle_core/
├─ __init__.py
├─ context.py
├─ engine.py
├─ events.py
├─ unit.py
├─ enums.py
├─ battle_systems.py
├─ action_order_system.py
├─ action_system.py
├─ normal_attack_system.py
├─ damage_system.py
├─ target_system.py
├─ troop_system.py
├─ attribute_system.py
├─ random_system.py
├─ state_definition.py
├─ state_instance.py
├─ state_registry.py
├─ state_lifecycle_system.py
└─ official_state_catalog.py

完整 tests/
.github/workflows/tests.yml
当前 GitHub Actions 状态与日志
```

---

# 2. 审计等级

本项目 Stage 4 最终审计使用：

```text
BLOCKER
= 不修复不得封版，也不得进入 Stage 5。

MAJOR
= 会破坏 Stage 3/4 核心语义、BattleSystem 边界、RNG、状态目录或代表状态行为。

MINOR
= 不影响当前功能正确性，但应记录或整理的文档/维护项。
```

最终结果：

```text
BLOCKER: 0
MAJOR:   0
MINOR:   1
```

唯一 MINOR 为：

```text
PROJECT_ROADMAP.md 的状态快照仍写着“Stage 4 最终封版审计待进行”。
```

这是状态文档滞后，不是代码缺陷。本文作为本次最终审计与冻结记录，封版后路线图应在下一次维护时同步为 Stage 4 FROZEN。

---

# 3. 官方 40 状态目录审计

确认：

```text
官方战斗词条：46
非具体状态分类/机制词条：6
具体 BattleState：40
```

分类计数：

```text
持续性状态：8
功能性状态：17
控制状态：11
其他：4
总计：40
```

并确认：

```text
40 个 state_id 唯一
40 个 Hint ID 唯一
40 个中文状态名唯一
6 个非具体状态词条未进入 OFFICIAL_STATE_CATALOG
官方中文原文未被项目补充规则反向改写
```

代表状态 Hint ID：

```text
first_strike / 先攻 = 690090
ambush / 遇袭        = 690091
disarm / 缴械        = 690102
weakness / 虚弱      = 690104
stun / 震慑          = 690111
```

审计结论：

```text
PASS
```

---

# 4. 先攻 / 遇袭审计

当前 `ActionOrderSystem` 规则：

```text
先攻 = +1
普通 = 0
遇袭 = -1
```

同一武将同时拥有：

```text
先攻 + 遇袭
= +1 + (-1)
= 0
```

因此回到普通行动层，再按有效速度排序。

只有：

```text
相同 priority tier
+
相同 effective speed
```

才调用：

```text
RandomSystem.shuffle()
```

该组合语义与 `PROJECT_STATE_INTERACTIONS_V1.md` 一致，并且保持为项目补充确认规则，不伪装成官方 Hint 原文。

审计结论：

```text
PASS
```

---

# 5. 缴械审计

规则归属：

```text
NormalAttackSystem
```

缴械检查发生在：

```text
目标选择
DamageSystem
TroopSystem
```

之前。

缴械时确认：

```text
不选目标
不消耗目标 RNG
不进入 DamageSystem
不消耗伤害公式 RNG
不调用 TroopSystem
发布 ACTION_BLOCKED
```

没有把缴械变成 `UnitRuntime.can_attack = False` 一类持久 bool。

审计结论：

```text
PASS
```

---

# 6. 震慑审计

规则归属：

```text
ActionSystem
```

震慑存在时：

```text
整个行动停止
NormalAttackSystem 不被调用
发布 ACTION_BLOCKED
```

同时存在：

```text
stun + disarm
```

时，由更高层的 `ActionSystem` 震慑先阻止整个行动。

确认：

```text
不选目标
不消耗目标 RNG
不消耗伤害 RNG
不调用 TroopSystem
```

审计结论：

```text
PASS
```

---

# 7. 虚弱审计

规则归属：

```text
DamageSystem
```

虚弱不阻止行动，也不阻止目标选择；它只阻止造成伤害。

当前 `DamageSystem.calculate()` 在基础伤害公式之前检查虚弱。

结果为：

```text
base_damage = 0
scaled_damage = 0
final_damage = 0
prevented = True
prevented_by_state_id = weakness
```

确认：

```text
不运行兵刃/谋略基础伤害公式
不消耗公式 RNG
不调用 TroopSystem.apply_damage()
发布 DAMAGE_PREVENTED
不发布 DAMAGE_DEALT
```

虚弱不是通过 `coefficient = 0` 伪装实现。

审计结论：

```text
PASS
```

---

# 8. ACTION_BLOCKED / DAMAGE_PREVENTED 审计

确认：

```text
缴械
→ ACTION_BLOCKED(action_type=NORMAL_ATTACK)

震慑
→ ACTION_BLOCKED(action_type=ALL)

虚弱
→ NORMAL_ATTACK
→ DAMAGE_PREVENTED
```

`EventBus` 只记录已经发生的事实，不参与规则决策。

审计结论：

```text
PASS
```

---

# 9. Stage 3 架构回归审计

确认继续保持：

```text
StateDefinition
StateInstance
StateRegistry
StateLifecycleSystem
BattleContext.states
STATE_APPLIED
STATE_REMOVED
STATE_EXPIRED
```

并确认：

```text
StateRegistry = 存储与查询
StateLifecycleSystem = 状态加入 / 删除 / 到期的正式写入口
BattleSystem = 解释具体状态规则
BattleEngine = 通用流程推进
```

`StateLifecycleSystem` 没有：

```text
扣兵
恢复
选目标
执行伤害
解释缴械/震慑/虚弱等具体状态
```

`StateRegistry` 继续允许：

```text
同 owner + 同 state_id 的多个 StateInstance 共存
```

`StateInstance` 继续使用确定性 `instance_id` 与明确绝对过期锚点：

```text
expires_round
expires_phase
```

审计结论：

```text
PASS
```

---

# 10. BattleEngine / UnitRuntime 红线审计

确认 `BattleEngine` 不认识：

```text
first_strike
ambush
disarm
stun
weakness
```

只调用通用 BattleSystem 与状态生命周期节点。

确认 `UnitRuntime` 没有增加：

```text
can_attack
is_stunned
is_disarmed
has_first_strike
has_ambush
is_weak
```

一类具体状态 bool。

审计结论：

```text
PASS
```

---

# 11. DamageSystem / TroopSystem 边界审计

确认：

```text
DamageSystem
= 只计算理论伤害

TroopSystem
= 实际兵力修改入口
```

基础兵刃和谋略伤害继续保持：

```text
DamageRequest
→ DamageSystem.calculate()
→ DamageResult
```

兵力变化只有之后通过：

```text
TroopSystem.apply_damage()
```

发生。

Stage 4 没有把边界改成：

```text
DamageSystem.calculate_and_apply()
```

审计结论：

```text
PASS
```

---

# 12. RandomSystem 审计

确认：

```text
RandomSystem
```

仍为唯一战斗 RNG 入口。

Stage 4 测试明确覆盖：

```text
缴械不消耗目标/伤害 RNG
震慑不消耗目标/伤害 RNG
虚弱可正常目标选择，但不消耗伤害公式 RNG
不同 priority tier 不消耗 shuffle RNG
同 tier 不同速度不消耗 shuffle RNG
同 tier 同速度才使用 shuffle
```

没有发现生产规则代码自行调用 Python 全局随机数的 Stage 4 倒退。

审计结论：

```text
PASS
```

---

# 13. 其余 35 状态边界审计

确认 Stage 4 没有提前实现其余 35 状态。

它们全部在：

```text
research/official_state_catalog_v1/STATE_SYSTEM_MAPPING_V1.md
```

具有未来系统映射。

分组完整性：

```text
持续性未实现：8
功能性未实现：15
控制未实现：8
其他未实现：4

8 + 15 + 8 + 4 = 35
```

没有为了 Stage 4 提前塞入：

```text
Effect
SkillRuntime
TriggerSystem
RecoverySystem
HitResolution
完整 Damage Modifier Pipeline
装备系统
```

审计结论：

```text
PASS
```

---

# 14. 具体战法逻辑审计

没有发现生产代码通过：

```python
if skill.name == "...":
```

分发具体战法规则。

Stage 4 仍然只验证通用状态与 BattleSystem 的边界。

审计结论：

```text
PASS
```

---

# 15. 测试与 CI 基线

审计起点提交：

```text
5124e4978ec7241b5d89f97630ac5342ac48932e
```

对应 GitHub Actions 实际日志：

```text
pytest -q
→ 80 passed

python demo.py
→ success

GitHub Actions
→ success
```

工作流会在本文提交后重新执行：

```text
pytest -q
python demo.py
```

只有本文所在提交的 GitHub Actions 最终为 `success`，本文件中的 `FROZEN` 状态才正式生效。

---

# 16. 最终审计结论

最终严重级别：

```text
BLOCKER: 0
MAJOR:   0
MINOR:   1（路线图状态快照滞后，仅文档状态项）
```

代码修复：

```text
无需代码修复。
```

原因：

```text
没有发现会破坏 Stage 4 功能、Stage 3 架构、RNG、状态目录、事件或 BattleSystem 边界的问题。
```

因此不进行为了制造“修复 commit”而修改正确代码的仪式性活动。修不存在的 bug 通常是制造真实 bug 的高效方式。

---

# 17. Stage 4 FROZEN 条件

以下条件已经满足：

```text
✅ 官方 40 状态静态目录
✅ 8 / 17 / 11 / 4 分类正确
✅ 官方原文与工程补充规则分层

✅ 先攻
✅ 遇袭
✅ 先攻 + 遇袭 = 0
✅ 缴械
✅ 震慑
✅ 虚弱

✅ ACTION_BLOCKED
✅ DAMAGE_PREVENTED

✅ RNG 边界
✅ BattleEngine 红线
✅ StateLifecycleSystem 红线
✅ UnitRuntime 无具体状态 bool

✅ Stage 1/2/3 回归基线
✅ pytest 起点基线 80 passed
✅ demo 起点基线 success
✅ 起点 GitHub Actions success

✅ 最终独立源码审计无 BLOCKER / MAJOR
```

最后一个动态条件：

```text
本文所在提交的 GitHub Actions = success
```

满足后：

# Stage 4 = FROZEN

---

# 18. FROZEN 后的变更规则

Stage 4 `FROZEN` 后，不再把后续功能塞回 Stage 4。

如果未来发现 Stage 4 缺陷：

```text
明确记录缺陷
→ 判断是否需要解冻
→ 最小修复
→ Stage 1/2/3/4 全回归
→ 新一轮审计
→ 重新 FROZEN
```

不得静默改变：

```text
40 状态 V1 官方研究原文
先攻 + 遇袭项目补充规则
Stage 3 生命周期边界
DamageSystem / TroopSystem 边界
RandomSystem 唯一 RNG 边界
```

---

# 19. 下一步

Stage 4 正式 FROZEN 后，才允许进入：

```text
Stage 5
Effect + EffectExecutor + State Runtime Parameter Contract
```

Stage 5 必须重新读取当时最新 `main`，先建立正式 `stages/stage5/STAGE5.md`，不得根据本次审计时的旧 SHA 猜测仓库状态。
