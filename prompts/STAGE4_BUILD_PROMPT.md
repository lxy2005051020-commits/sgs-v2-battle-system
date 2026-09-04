你现在要继续维护我的项目：

# 三国志战略版战斗模拟器 V2

GitHub 仓库：

`lxy2005051020-commits/sgs-v2-battle-system`

目标分支：

`main`

当前任务：

# 按仓库中的 `STAGE4.md` 完整搭建 Stage 4

请不要根据旧聊天记录猜仓库状态。开始前必须直接读取当前 `main` 的最新代码和以下资料：

```text
STAGE3.md
STAGE4.md

research/official_state_catalog_v1/OFFICIAL_STATE_CATALOG_V1.md
research/official_state_catalog_v1/official_state_rules_v1.csv
research/official_state_catalog_v1/official_state_catalog_v1.xlsx

sgs_v2/battle_core/state_definition.py
sgs_v2/battle_core/state_instance.py
sgs_v2/battle_core/state_registry.py
sgs_v2/battle_core/state_lifecycle_system.py
sgs_v2/battle_core/context.py
sgs_v2/battle_core/battle_systems.py
sgs_v2/battle_core/engine.py
sgs_v2/battle_core/events.py
sgs_v2/battle_core/action_order_system.py
sgs_v2/battle_core/action_system.py
sgs_v2/battle_core/normal_attack_system.py
sgs_v2/battle_core/damage_system.py
sgs_v2/battle_core/target_system.py
sgs_v2/battle_core/random_system.py
sgs_v2/battle_core/troop_system.py
sgs_v2/battle_core/__init__.py

tests/
```

如果实际仓库结构与文档有差异，以当前代码为准，但不能静默改变 `STAGE4.md` 已确定的架构目标。

---

# 一、任务原则

Stage 3 已冻结。

Stage 4 不是实现全部 40 个官方状态。

Stage 4 的目标是：

```text
1. 建立完整官方 40 状态静态目录
2. 用 5 个代表状态验证 BattleState 真正接入 BattleSystem
3. 为其余 35 状态建立未来系统映射
4. 保持 Stage 1/2/3 全部回归通过
```

第一批固定状态：

```text
先攻 first_strike
遇袭 ambush
缴械 disarm
震慑 stun
虚弱 weakness
```

不得擅自更换第一批状态。

---

# 二、官方资料必须作为唯一状态语义基线

当前官方接口已确认：

```text
46 个官方战斗词条
-
6 个分类/机制词条
=
40 个具体战斗特殊状态
```

40 状态分类：

```text
持续性状态 8
功能性状态 17
控制状态 11
其他 4
```

不要用攻略或记忆覆盖官方原文。

特别注意：

```text
遇袭 690091
```

官方原文第二句出现“多名武将同时拥有先攻状态”，疑似官方笔误。

必须保留原文，工程实现只采用明确证据：

```text
遇袭 = 回合内延后行动
```

不要自己修正文案后宣称是官方规则。

---

# 三、先建立 OfficialStateCatalog

按照 `STAGE4.md` 新增官方静态目录。

建议：

```text
official_state_catalog.py
```

至少包含：

```text
OfficialStateCategory
OfficialStateId
OfficialStateEntry
OFFICIAL_STATE_CATALOG
register_official_state_definitions()
```

必须完整录入 40 项：

```text
中文状态名
Hint ID
官方分类
官方接口原文
稳定 state_id
```

不得修改 Stage 3 的 StateDefinition 让它变成具体规则容器。

---

# 四、必须通过的目录测试

新增测试并确认：

```text
总数 40
持续性 8
功能性 17
控制 11
其他 4

state_id 唯一
Hint ID 唯一
中文状态名唯一

first_strike = 先攻 = 690090
ambush = 遇袭 = 690091
disarm = 缴械 = 690102
weakness = 虚弱 = 690104
stun = 震慑 = 690111
```

6 个分类/机制词条不能进入具体状态目录：

```text
功能性状态
功能状态
控制状态
战斗属性
会心伤害
奇谋伤害
```

---

# 五、实现先攻和遇袭

只修改 `ActionOrderSystem` 的行动排序规则。

优先级：

```text
先攻
↓
普通
↓
遇袭
```

每个优先级内部：

```text
最终速度高 → 先行动
```

只有：

```text
同优先级
+
同速度
```

才允许使用 `RandomSystem.shuffle()`。

不得因为状态排序额外消耗无意义 RNG。

---

# 六、先攻 + 遇袭同时存在

官方接口原文没有直接给出两者同时存在时的组合说明。

项目已补充确认规则：

```text
先攻 = +1
普通 = 0
遇袭 = -1

先攻 + 遇袭
= +1 + (-1)
= 0
= 普通行动层
```

因此不得再抛出未解析交互异常。

同一单位同时拥有先攻和遇袭时：

```text
priority = NORMAL
```

随后与其他普通层单位一起按有效速度排序；仅普通层同速时才允许使用 `RandomSystem.shuffle()`。

注意：这条是项目补充确认规则，不得反向改写官方接口原文。

测试必须覆盖。

---

# 七、实现缴械

官方：

```text
控制状态，无法发动普通攻击
```

规则属于：

```text
NormalAttackSystem
```

必须在 TargetSystem 之前判断。

缴械时：

```text
不选目标
不计算伤害
不扣兵
不消耗目标 RNG
不消耗伤害 RNG
```

发布：

```text
ACTION_BLOCKED
```

payload 至少有：

```text
action_type=NORMAL_ATTACK
reason_state_id=disarm
```

不要在 BattleEngine 判断缴械。

---

# 八、实现震慑

官方：

```text
控制状态，无法行动
```

规则属于：

```text
ActionSystem
```

必须在进入具体行动前判断。

震慑时：

```text
NormalAttackSystem 不执行
```

发布：

```text
ACTION_BLOCKED
```

建议：

```text
action_type=ALL
reason_state_id=stun
```

不要在 BattleEngine 判断震慑。

---

# 九、实现虚弱

官方：

```text
控制状态，无法造成伤害
```

虚弱不阻止行动，也不阻止普通攻击本身。

流程：

```text
行动
→ 普攻
→ 选目标
→ DamageRequest
→ DamageSystem
→ 发现 source 有 weakness
→ 本次伤害被阻止
→ final_damage = 0
```

必须在基础伤害公式前阻止。

因此虚弱伤害不能消耗基础伤害公式 RNG。

---

# 十、正式支持 0 伤害

当前 DamageSystem 如果仍有：

```python
max(1, ...)
```

不要简单全局删除低伤下限。

正确做法是：

```text
正常伤害
→ 保持现有低伤规则

明确被状态阻止
→ DamageResult.final_damage = 0
```

建议给 DamageResult 增加兼容字段：

```text
prevented
prevented_by_state_id
```

虚弱：

```text
base_damage=0
scaled_damage=0
final_damage=0
prevented=True
prevented_by_state_id=weakness
```

不要用 `coefficient=0` 冒充虚弱。

---

# 十一、增加 DAMAGE_PREVENTED

EventType 至少增加：

```text
ACTION_BLOCKED
DAMAGE_PREVENTED
```

虚弱的普通攻击建议事件语义：

```text
NORMAL_ATTACK
→ DAMAGE_PREVENTED
```

且：

```text
不调用 TroopSystem.apply_damage
不发布 DAMAGE_DEALT
```

缴械/震慑则只记录相应 `ACTION_BLOCKED`，因为行为根本没有执行。

---

# 十二、保持所有 Stage 2/3 架构边界

继续保持：

```text
TargetSystem = 选目标入口
AttributeSystem = 最终属性入口
DamageSystem = 理论伤害入口
TroopSystem = 兵力修改入口
VictorySystem = 胜负入口
RandomSystem = 唯一随机入口
StateLifecycleSystem = 状态写入/删除/过期入口
StateRegistry = 状态存储查询
BattleEngine = 通用流程
```

禁止：

```python
target.troops -= ...
unit.can_attack = False
unit.is_stunned = True
if skill.name == ...
import random
uuid.uuid4()
```

不要把 40 个状态做成 UnitRuntime 的 40 个 bool。

---

# 十三、其余 35 状态不要实现

按照 `STAGE4.md` 建立未来系统映射文档，例如：

```text
research/official_state_catalog_v1/STATE_SYSTEM_MAPPING_V1.md
```

每个未实现状态至少标记：

```text
状态名
state_id
未来主要系统
延期原因
```

不要留成含糊的“以后处理”。

---

# 十四、必须补的测试

至少覆盖：

```text
官方状态目录完整性

先攻 > 普通 > 遇袭
多个先攻按速度
多个遇袭按速度
同 tier 同速度固定 seed 可复现
无并列不消耗 RNG
先攻+遇袭同单位相互抵消并按普通层处理

缴械阻止普通攻击
缴械不消耗目标/伤害 RNG

震慑阻止整个行动
震慑不进入 NormalAttackSystem

虚弱仍可普通攻击
虚弱最终伤害 0
虚弱不调用 TroopSystem
虚弱不消耗伤害公式 RNG

ACTION_BLOCKED
DAMAGE_PREVENTED

BattleEngine 不出现具体状态判断
StateLifecycleSystem 不出现具体状态效果
```

---

# 十五、完整回归

修改完成后必须实际运行：

```bash
pytest -q
python demo.py
```

然后检查 GitHub Actions。

不要只读测试然后宣称通过。

---

# 十六、不要修改官方研究资料

以下目录是证据基线：

```text
research/official_state_catalog_v1/
```

如果发现代码需求和资料冲突：

```text
停止猜测
记录冲突
按官方资料保守实现
```

不要为了让代码方便而改官方原文。

---

# 十七、完成后进行 Stage 4 审计

最终报告必须列出：

```text
1. 修改文件
2. 新增架构
3. 40 状态目录统计
4. 5 个代表状态分别接入哪个 BattleSystem
5. RNG 消耗验证
6. 0 伤害语义
7. 新增事件
8. 其余 35 状态延期映射
9. pytest 实际结果
10. demo 结果
11. GitHub Actions 结果
12. 是否满足 STAGE4.md 全部封版条件
```

如果任一封版条件未满足，不得宣布 Stage 4 完成。

现在请先读取当前仓库最新代码与 `STAGE4.md`，然后按实施顺序直接开始修改。
