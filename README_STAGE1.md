# 三战战法 V2 · 阶段 2：基础 BattleSystem

本目录完成了无战法战斗从阶段 1 临时规则到正式 BattleSystem 的迁移。

```text
BattleEngine
  └─ BattleSystems
       ├─ ActionOrderSystem ── AttributeSystem
       ├─ ActionSystem ── NormalAttackSystem
       │                   ├─ TargetSystem
       │                   ├─ DamageSystem ── AttributeSystem
       │                   └─ TroopSystem
       └─ VictorySystem

共享：BattleContext、RandomSystem、EventBus
```

## 设计边界

- `BattleEngine` 只推进阶段、回合和事件节点；不含目标、伤害、属性或胜负公式。
- `AttributeSystem` 是最终 `attack / defense / speed` 的唯一读取入口。当前结果等于基础值，并预留了阶段 4 `AttributeModifierState` 的修正接口。
- `TargetSystem` 统一处理敌我、存活过滤、随机单目标和指定数量随机目标；随机均来自 `RandomSystem`。
- `DamageSystem` 只返回 `DamageResult`，不改兵力。
- `TroopSystem` 是唯一执行兵力增减的系统，并包含后续治疗使用的 `restore` 入口。
- `NormalAttackSystem` 组织“选目标 → 计算伤害 → 变更兵力 → Event”。
- `ActionSystem` 当前只调度普攻；阶段 4 的震慑等整次行动阻断将在此接入。
- `VictorySystem` 负责主将阵亡、全军无法战斗、最大回合和战平；战前双方均无存活单位时立即判为平局。

`BattleContext` 强制 `context.units` 的 key 与 `UnitRuntime.unit_id` 相等，保证后续
State、Effect、SkillRuntime 和 Event 的单位 ID 可安全关联。行动顺序按最终速度分组，
仅同速组调用 `RandomSystem.shuffle`；异速单位不消耗随机流。

临时 `Stage1NoSkillRules` 及 `stage1_rules.py` 已删除。

## 使用

```python
BattleEngine(
    context=context,
    systems=BattleSystems(damage_scale=1.0),
).run()
```

`damage_scale` 只保留阶段 1 占位伤害公式的可配置倍率，尚不代表游戏真实伤害公式。

## 验证

```bash
pytest -q
python demo.py
```

测试覆盖无战法完整战斗、事件顺序、相同 seed 的可复现性、阵亡单位跳过行动，以及各阶段 2 系统的职责边界。

阶段 3 才引入 `StateDefinition`、`StateInstance`、`StateRegistry` 与 `StateLifecycleSystem`；阶段 4 再接入先攻、缴械、计穷、震慑、属性 Modifier 和减伤。
