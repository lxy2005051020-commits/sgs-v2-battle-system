# 三国志战略版战斗模拟器 V2 · Stage 2 BattleSystem

Stage 2 已完成无战法战斗所需的 BattleSystem 基础架构，并冻结统一的目标、属性、伤害、兵力、胜负与随机边界。本阶段不实现状态、Effect、具体战法、会心或增减伤系统。

## 当前架构

```text
BattleEngine
    ↓
BattleSystems
    ├─ ActionOrderSystem
    │      ↓
    │  AttributeSystem
    │
    ├─ ActionSystem
    │      ↓
    │  NormalAttackSystem
    │      ├─ TargetSystem
    │      ├─ DamageSystem
    │      │      ├─ WeaponBaseDamageFormula
    │      │      └─ StrategyBaseDamageFormula
    │      └─ TroopSystem
    │
    └─ VictorySystem
```

共享基础设施：

```text
BattleContext
RandomSystem
EventBus
```

## 系统职责边界

- `BattleEngine` 只推进战斗阶段、回合、行动节点和事件，并调用各 BattleSystem；不包含伤害公式、目标选择或主将阵亡的具体规则。
- `ActionOrderSystem` 通过 `AttributeSystem` 获取最终 `speed`。只有同速组需要随机裁决，随机统一由 `BattleContext.random` 提供。
- `AttributeSystem` 是最终属性的统一读取入口，当前覆盖 `attack`、`defense`、`intelligence`、`speed`。Stage 2 中最终值等于基础值，具体系统不得自行修改最终属性。
- `TargetSystem` 统一处理目标筛选与随机目标。若只有一个合法目标，或指定数量会选中全部候选，则不消耗随机数；全选时按主将、第一副将、第二副将顺序结算。
- `DamageSystem` 的唯一正式入口是 `DamageSystem.calculate(context, request)`。它只计算理论伤害，不修改兵力，也不做击杀封顶。
- `TroopSystem` 是唯一允许修改 `troops` 的系统；`apply_damage()` 负责实际扣兵与击杀封顶，`restore()` 为后续恢复类效果保留统一入口。
- `NormalAttackSystem` 负责“选目标 → 构造 `DamageRequest` → `DamageSystem.calculate()` → `TroopSystem.apply_damage()` → 发布事件”。普通攻击不存在第二套伤害公式。
- `VictorySystem` 负责主将阵亡、全军无法战斗、最大回合和战平。主将兵力归零后战斗立即结束，即使副将仍存活。

## DamageSystem 正式链路

```text
NormalAttack / Future Effect
        ↓
DamageRequest
        ↓
DamageSystem.calculate()
        ↓
DamageType.WEAPON
        └─ WeaponBaseDamageFormula

DamageType.STRATEGY
        └─ StrategyBaseDamageFormula
        ↓
base_damage
        ↓
× DamageRequest.coefficient
        ↓
scaled_damage
        ↓
final_damage
        ↓
TroopSystem.apply_damage()
```

`WeaponBaseDamageFormula` 和 `StrategyBaseDamageFormula` 只负责 100% 基础伤害。`coefficient` 在基础公式之后处理。未来的增伤、减伤、会心、奇谋、状态和战法类型不得塞入基础伤害公式。

## 基础伤害

- `DamageType.WEAPON` 使用 `WeaponBaseDamageFormula`，属性对抗为武力 `attack` vs 统率 `defense`。
- `DamageType.STRATEGY` 使用 `StrategyBaseDamageFormula`，属性对抗为智力 `intelligence` vs 智力 `intelligence`。
- 两类基础伤害共享当前仓库实现中的完整 `F(N)` 查表、等级缩放、兵种克制层、士气层、随机层和低伤下限。
- 所有随机行为必须通过 `BattleContext.random / RandomSystem`。
- `DamageResult.final_damage` 是理论伤害。例如目标只剩 100 兵而理论伤害为 800，`final_damage` 仍为 800；实际损失 100 由 `TroopSystem` 负责。

兵刃公式的逆向候选说明见 `NORMAL_ATTACK_FORMULA_V1.md`；谋略实现边界见 `STRATEGY_DAMAGE_FORMULA_V1.md`。这些文档描述的是仓库当前采用的候选模型，不是官方公开公式，也不是服务器源码。

## 阵容规则

`BattleContext` 强制每队 1～3 名武将，并满足：

```text
1 人：主将
2 人：主将 + 第一副将
3 人：主将 + 第一副将 + 第二副将
```

每队必须恰好一个主将，位置不得重复且必须连续。正式查询入口包括：

```python
context.commander_of(team_id)
context.unit_at_position(team_id, position)
```

## 可复现性

战斗内禁止具体系统直接调用 Python 全局随机函数。相同配置与相同 seed 必须得到相同结果：

```text
same configuration + same seed = same result
```

## 运行与验证

```bash
pip install -e .
pytest -q
python demo.py
```

GitHub Actions 在 `push` 和 `pull_request` 上执行测试，并额外运行 Demo 作为 smoke test。

## Stage 2 冻结范围

Stage 2 到此只负责稳定 BattleSystem 基础边界，不提前加入：

```text
StateDefinition / StateInstance / StateRegistry / StateLifecycleSystem
缴械 / 技穷 / 震慑 / 先攻
增伤 / 减伤 / 会心 / 奇谋
Effect / SkillRuntime
```

这些能力在后续阶段建立，不应反向污染 Stage 2 的基础接口。
