# 三国志战略版战斗模拟器 V2 · Stage 4 官方 BattleState 规则接入与代表状态验证

> Stage 3 已冻结并通过 CI。Stage 4 的任务不是一次性实现全部 40 个官方状态，而是把官方状态目录接入项目，并用少量代表状态验证 BattleState 能真正改变不同 BattleSystem 的规则。
>
> 本阶段必须以 `research/official_state_catalog_v1/` 中的官方接口资料为状态语义基线。不得用攻略、记忆或战法名称覆盖官方接口原文。

---

# 1. Stage 4 的目标

Stage 4 完成后，项目应达到：

```text
官方 40 状态静态目录
        ↓
StateDefinition
        ↓
StateLifecycleSystem
        ↓
StateRegistry
        ↓
BattleSystem 查询状态并解释规则
        │
        ├─ ActionOrderSystem
        │     ├─ 先攻
        │     └─ 遇袭
        ├─ ActionSystem
        │     └─ 震慑
        ├─ NormalAttackSystem
        │     └─ 缴械
        └─ DamageSystem
              └─ 虚弱
```

核心验证命题：

> State 只表示持续存在的战斗事实；具体 BattleSystem 决定该事实如何影响规则。

---

# 2. 本阶段明确不做什么

Stage 4 **不实现全部 40 个状态效果**。

除第一批 5 个代表状态外，其余状态只建立官方目录和未来系统映射，不提前实现。

本阶段不要新增：

```text
ActiveSkillSystem
CommandSkillSystem
PassiveSkillSystem
Effect
SkillRuntime
具体战法
完整持续伤害系统
完整恢复系统
完整命中/规避系统
完整状态免疫/覆盖/刷新系统
```

不要为了实现某个状态提前把 Stage 5/6/7 一起塞进来。

---

# 3. Stage 3 不能被破坏

Stage 3 当前核心基础设施继续保持：

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

禁止重新设计 Stage 3 生命周期。

继续保持：

```text
StateRegistry = 存储与查询
StateLifecycleSystem = 状态写入 / 删除 / 过期入口
BattleSystem = 解释具体状态规则
BattleEngine = 通用流程，不认识具体状态名
```

不得在 `StateLifecycleSystem` 中出现：

```python
if state_id == "disarm":
    ...
```

不得在 `BattleEngine` 中出现：

```python
if context.states.has(...):
    ...
```

具体状态由对应 BattleSystem 查询。

---

# 4. Stage 4 的官方资料基线

正式依据：

```text
research/official_state_catalog_v1/
├─ official_state_catalog_v1.xlsx
├─ OFFICIAL_STATE_CATALOG_V1.md
└─ official_state_rules_v1.csv
```

历史研究资料：

```text
research/state_catalog_v1/
```

只作为历史参考，不再作为 Stage 4 的主要状态全集依据。

当前官方接口结论：

```text
官方战斗词条：46
非具体状态分类/机制词条：6
具体 BattleState 候选：40
```

6 个非具体状态词条：

```text
功能性状态
功能状态
控制状态
战斗属性
会心伤害
奇谋伤害
```

40 个具体状态官方分类数量：

```text
持续性状态：8
功能性状态：17
控制状态：11
其他：4
总计：40
```

---

# 5. Stage 4A：建立官方静态状态目录

建议新增：

```text
sgs_v2/battle_core/official_state_catalog.py
```

不要把官方 Hint ID、分类和原文硬塞进 Stage 3 的 `StateDefinition`。

建议新建纯静态元数据：

```python
class OfficialStateCategory(str, Enum):
    CONTINUOUS = "CONTINUOUS"
    FUNCTIONAL = "FUNCTIONAL"
    CONTROL = "CONTROL"
    OTHER = "OTHER"


class OfficialStateId(str, Enum):
    ...
```

以及：

```python
@dataclass(frozen=True, slots=True)
class OfficialStateEntry:
    state_id: OfficialStateId
    name: str
    hint_id: int
    category: OfficialStateCategory
    official_text: str
```

然后：

```python
OFFICIAL_STATE_CATALOG: tuple[OfficialStateEntry, ...] = (...)
```

目录必须有 40 项。

---

# 6. 推荐稳定 state_id

本项目 V1 建议固定：

```text
burn                    灼烧
flood                   水攻
poison                  中毒
rout                    溃逃
sandstorm               沙暴
rebellion               叛逃
first_aid               急救
recuperation            休整

combo                   连击
evasion                 规避
barrier                 抵御
cleave                  群攻
counterattack           反击
damage_split            分摊
damage_share            分担
insight                 洞察
first_strike            先攻
ambush                  遇袭
sure_hit                必中
defense_pierce          破阵
weapon_lifesteal        倒戈
strategy_lifesteal      攻心
chain_link              铁索连环
guard                   援护
vigilance               警戒

silence                 计穷
disarm                  缴械
confusion               混乱
weakness                虚弱
healing_ban             禁疗
taunt                   嘲讽
false_report            伪报
provoke                 挑拨
equipment_disable       破坏
capture                 捕获
stun                    震慑

critical                会心
strategy_critical       奇谋
damage_reduction_pierce 看破
intimidation            威慑
```

这些是项目工程标识，不替代官方中文名称和 Hint ID。

---

# 7. 官方目录与 StateDefinition 的边界

提供一个显式注册函数，例如：

```python
def register_official_state_definitions(
    registry: StateRegistry,
) -> None:
    ...
```

它可以把官方目录转换为最小 `StateDefinition`：

```python
StateDefinition(
    state_id=entry.state_id.value,
    name=entry.name,
    tags=frozenset({entry.category.value}),
)
```

不要让 `BattleContext.__post_init__` 偷偷依赖某个具体状态效果。

Stage 4 测试可以显式：

```python
register_official_state_definitions(context.states)
```

未来 BattleFactory/配置层再统一处理默认注册。

---

# 8. Stage 4A 验收测试

至少新增：

```text
tests/test_official_state_catalog.py
```

必须验证：

```text
总数 = 40
持续性 = 8
功能性 = 17
控制 = 11
其他 = 4

state_id 唯一
Hint ID 唯一
中文状态名唯一
40 个 Hint ID 与官方目录资料一致

先攻 = 690090
遇袭 = 690091
缴械 = 690102
虚弱 = 690104
震慑 = 690111
```

还要验证 6 个非具体状态词条不进入 `OFFICIAL_STATE_CATALOG`。

---

# 9. Stage 4B：第一批只实现 5 个代表状态

固定第一批：

```text
先攻 first_strike
遇袭 ambush
缴械 disarm
震慑 stun
虚弱 weakness
```

它们分别验证：

```text
ActionOrderSystem
NormalAttackSystem
ActionSystem
DamageSystem
```

这 5 个成功后才能认为 Stage 3 的 BattleState 基础设施被真实规则验证。

---

# 10. 先攻 / 遇袭 → ActionOrderSystem

官方原文：

```text
先攻：
让武将在回合内优先行动，多名武将同时拥有先攻状态时则根据速度高低决定行动顺序。

遇袭：
让武将在回合内延后行动，多名武将同时拥有先攻状态时则根据速度高低决定行动顺序。
```

遇袭第二句官方原文写“先攻”，疑似官方文本笔误；Stage 4 不擅自改官方原文，但工程实现只采用已明确部分：

```text
先攻 → 提前层
普通 → 中间层
遇袭 → 延后层
```

ActionOrderSystem 推荐优先级：

```text
FIRST_STRIKE = 1
NORMAL       = 0
AMBUSH       = -1
```

排序：

```text
priority tier 降序
        ↓
effective speed 降序
        ↓
同 tier + 同速度
        ↓
RandomSystem.shuffle()
```

必须保持：

```text
没有真正并列
→ 不消耗 RNG
```

---

# 11. 先攻 + 遇袭同时存在

当前官方资料没有给出同一武将同时拥有：

```text
先攻 + 遇袭
```

时的最终关系。

Stage 4 禁止自行猜测：

```text
互相抵消
先攻覆盖
遇袭覆盖
```

当前实现必须显式识别此组合并报告“未解析状态交互”，不得静默选择其中一个。

可以使用项目级异常，例如：

```python
class UnresolvedStateInteractionError(RuntimeError):
    ...
```

测试必须覆盖该行为。

---

# 12. 缴械 → NormalAttackSystem

官方原文：

```text
控制状态，无法发动普通攻击
```

所以规则只属于：

```text
NormalAttackSystem
```

`NormalAttackSystem.execute()` 必须在任何目标选择之前检查：

```python
context.states.has(
    owner_id=actor.unit_id,
    state_id=OfficialStateId.DISARM.value,
)
```

若缴械：

```text
不选目标
不消耗 TargetSystem RNG
不进入 DamageSystem
不消耗伤害公式 RNG
不调用 TroopSystem
```

并发布：

```text
ACTION_BLOCKED
```

建议 payload：

```python
{
    "action_type": "NORMAL_ATTACK",
    "reason_state_id": "disarm",
}
```

---

# 13. 震慑 → ActionSystem

官方原文：

```text
控制状态，无法行动
```

它比缴械高一层。

`ActionSystem.execute()` 在调用任何具体行动前检查：

```text
stun
```

存在时：

```text
整个行动停止
NormalAttackSystem 不被调用
```

并发布：

```text
ACTION_BLOCKED
```

建议：

```python
{
    "action_type": "ALL",
    "reason_state_id": "stun",
}
```

BattleEngine 仍然只调用 `ActionSystem.execute()`，不能自己判断震慑。

---

# 14. 虚弱 → DamageSystem

官方原文：

```text
控制状态，无法造成伤害
```

虚弱不等于：

```text
无法行动
无法普攻
无法发动战法
```

因此：

```text
行动照常
目标选择照常
DamageRequest 照常产生
```

但进入 `DamageSystem.calculate()` 后：

```text
source 存在 weakness
        ↓
本次伤害被阻止
        ↓
final_damage = 0
```

必须在基础伤害公式之前检查虚弱。

原因：

```text
虚弱已明确阻止伤害
→ 不需要计算基础伤害
→ 不应消耗伤害公式随机数
```

---

# 15. DamageResult 支持“伤害被阻止”

当前 Stage 2 的：

```python
final_damage = max(1, int(scaled_damage))
```

不能表达官方“无法造成伤害”。

Stage 4 应让 `DamageResult` 正式支持合法 0 伤害。

推荐新增兼容字段：

```python
prevented: bool = False
prevented_by_state_id: str | None = None
```

虚弱结果：

```text
base_damage = 0
scaled_damage = 0
final_damage = 0
prevented = True
prevented_by_state_id = "weakness"
```

不要使用：

```python
coefficient = 0
```

来伪装虚弱。

普通非阻止伤害仍保留现有基础伤害低伤规则。

---

# 16. DAMAGE_PREVENTED 与 TroopSystem

建议 EventType 增加：

```text
ACTION_BLOCKED
DAMAGE_PREVENTED
```

当 `DamageResult.prevented`：

```text
不调用 TroopSystem.apply_damage()
不发布 DAMAGE_DEALT
发布 DAMAGE_PREVENTED
```

普通攻击事实是否仍发布 `NORMAL_ATTACK` 可以保留，因为“发动了普通攻击但无法造成伤害”与“缴械导致根本无法发动普通攻击”是不同事实。

推荐事件顺序：

```text
虚弱：
NORMAL_ATTACK
→ DAMAGE_PREVENTED

缴械：
ACTION_BLOCKED
```

---

# 17. Stage 4 的 RNG 验收

必须增加 RNG 消耗测试：

```text
缴械
→ 不消耗目标 RNG
→ 不消耗伤害 RNG

震慑
→ 不进入 NormalAttackSystem
→ 不消耗目标/伤害 RNG

虚弱
→ 可以正常经过目标选择
→ 但 DamageSystem 不消耗基础伤害 RNG

行动顺序：
不同 tier → 不消耗裁决 RNG
同 tier 不同速度 → 不消耗裁决 RNG
同 tier 同速度 → 才使用 RandomSystem
```

不能直接调用 Python `random`。

---

# 18. Stage 4C：代表状态组合测试

至少测试：

```text
先攻 vs 普通
普通 vs 遇袭
先攻 vs 遇袭
多个先攻按速度
多个遇袭按速度
同 tier 同速度固定 seed 可复现

缴械单位不能普攻
震慑单位不能行动
震慑 + 缴械时由 ActionSystem 的震慑先阻止整次行动
虚弱单位仍可执行普通攻击，但最终伤害为 0

先攻 + 遇袭同单位
→ 明确报未解析交互
```

不要测试官方资料没有支持的“抵消规则”。

---

# 19. Stage 4D：其余 35 状态只做未来系统映射

不实现，但必须记录未来主要依赖。

建议按以下方向标记：

```text
持续伤害/周期恢复
→ DEFER_EFFECT_TRIGGER / PERIODIC_EFFECT

连击
→ DEFER_ACTION_REPEAT

规避 / 必中
→ DEFER_HIT_RESOLUTION

抵御
→ DEFER_DAMAGE_PREVENTION

群攻 / 反击
→ DEFER_TRIGGER_SYSTEM

分摊 / 分担 / 铁索连环 / 援护
→ DEFER_DAMAGE_REDIRECT / TARGET_REDIRECT

洞察
→ DEFER_STATE_APPLICATION_POLICY

破阵 / 警戒 / 会心 / 奇谋 / 看破
→ DEFER_DAMAGE_MODIFIER

倒戈 / 攻心 / 急救 / 休整 / 禁疗
→ DEFER_RECOVERY_SYSTEM

计穷 / 伪报 / 挑拨 / 威慑
→ DEFER_SKILL_SYSTEM

混乱 / 嘲讽
→ DEFER_TARGET_RESOLUTION

破坏
→ DEFER_EQUIPMENT_SYSTEM

捕获
→ DEFER_COMPOSITE_CONTROL

其余
→ 明确标记对应未来系统，不允许留成“以后再说”
```

可以把该映射写入：

```text
research/official_state_catalog_v1/STATE_SYSTEM_MAPPING_V1.md
```

或者等价文档。

---

# 20. 代码中不要散落中文状态名或裸字符串

生产规则代码优先使用：

```python
OfficialStateId.DISARM.value
OfficialStateId.STUN.value
OfficialStateId.WEAKNESS.value
```

而不是：

```python
"缴械"
"震慑"
"weakness"
```

到处散落。

中文名称用于官方目录、事件展示或 BattleReport。

---

# 21. Stage 4 架构红线

禁止：

```python
if skill.name == "...":
```

禁止：

```python
unit.can_attack = False
unit.is_stunned = True
unit.has_first_strike = True
```

禁止把 40 个状态变成 40 个 `UnitRuntime` bool。

禁止 StateLifecycleSystem 直接执行：

```text
扣兵
恢复
选目标
禁行动
伤害修正
```

禁止 BattleEngine 判断具体状态。

禁止具体状态绕过：

```text
TargetSystem
AttributeSystem
DamageSystem
TroopSystem
VictorySystem
RandomSystem
```

---

# 22. 推荐实现顺序

```text
Step 1
阅读 STAGE3.md + 官方状态资料

Step 2
实现 OfficialStateCategory / OfficialStateId / OfficialStateEntry

Step 3
建立 40 状态静态目录 + 注册函数

Step 4
官方目录测试

Step 5
EventType 增加 ACTION_BLOCKED / DAMAGE_PREVENTED

Step 6
ActionOrderSystem 接入先攻 / 遇袭

Step 7
NormalAttackSystem 接入缴械

Step 8
ActionSystem 接入震慑

Step 9
DamageResult / DamageSystem 接入虚弱与 0 伤害

Step 10
代表状态单元测试

Step 11
RNG 消耗测试

Step 12
其余 35 状态未来系统映射文档

Step 13
完整 pytest -q

Step 14
python demo.py

Step 15
确认 GitHub Actions 成功
```

---

# 23. Stage 4 封版验收标准

只有全部满足才封版：

```text
✅ 官方 40 状态静态目录建立
✅ 8 / 17 / 11 / 4 分类计数正确
✅ 40 个 state_id 唯一
✅ 40 个 Hint ID 唯一
✅ 官方原文未被擅自改写

✅ 先攻 → ActionOrderSystem
✅ 遇袭 → ActionOrderSystem
✅ 缴械 → NormalAttackSystem
✅ 震慑 → ActionSystem
✅ 虚弱 → DamageSystem

✅ 虚弱允许 final_damage = 0
✅ 被阻止行为不消耗无意义 RNG
✅ 先攻+遇袭未知组合不猜测

✅ ACTION_BLOCKED
✅ DAMAGE_PREVENTED

✅ BattleEngine 不认识具体状态
✅ StateLifecycleSystem 不执行具体状态效果
✅ UnitRuntime 不增加具体状态 bool
✅ 无具体战法逻辑
✅ 其余 35 状态有未来系统映射

✅ Stage 1/2/3 回归全部通过
✅ pytest -q 全绿
✅ demo.py 正常
✅ GitHub Actions success
```

---

# 24. Stage 4 完成定义

Stage 4 完成时，我们应该能证明：

```text
官方状态全集已经有静态基线；
BattleState 不只是“能存、能过期”，
而是真的能通过不同 BattleSystem 改变规则；

同时没有为了实现 5 个状态，
提前把后续 Skill / Effect / Trigger / Recovery 等系统硬塞进来。
```

完成后再进入 Stage 5：Effect。
