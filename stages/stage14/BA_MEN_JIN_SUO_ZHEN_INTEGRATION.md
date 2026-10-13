# 八门金锁阵接入记录

状态：`IMPLEMENTED_LOCAL_CANDIDATE`。分支 `stage14/ba-men-jin-suo-zhen`，基于远端 main `74817c59325bcaf7fafd5fc67f40621174ec9d65`。尚未发布 PR 或合并 main。

## 来源与公式

正式 ID `20025`，类型 `FORMATION`，全部五种基础兵种适用。[官方战法页](https://sgz.ejoy.com/m/station/detail-350659307657771017-367353729220884488)描述为前三回合降低敌军群体两人造成的伤害，并给己方主将先攻。

Lv1～10 基础降伤率为 **15%、16.6%、18.2%、19.8%、21.4%、23%、24.7%、26.4%、28.1%、30%**，直接来自本机 named static export，不做插值。[10 级来源行](ba_men_evidence/static_levels.csv)、[路径及 SHA-256](ba_men_evidence/source_manifest.json)已保留。

用户提供的[截图](ba_men_evidence/user_scaling_formula.png)指定：

```text
rate = base_rate * (1 + 0.272 * (INT - 100) / 100)
```

用户在本次接入明确确认：使用**发动时携带者智力快照**。通过 `AttributeSystem.get_intelligence` 读取，包含当时已生效的属性修正；后续变化不重算。满级 INT=50/100/200/300/400 时，降伤为 25.92%/30%/38.16%/46.32%/54.48%。计算过程中不按显示精度取整。

公式标记 `USER_SPECIFIED_FORMULA / NOT_CLIENT_EMPIRICALLY_FROZEN`；智力时点标记 `USER_CONFIRMED_APPLICATION_SNAPSHOT`，不能将实现和测试当成客户端公式实证。

## 组件树

```text
FormationSkillConfig / FORMATION_SKILL_REGISTRY
  PRE_BATTLE / 100% / 无准备回合
  同队唯一阵法、兵种与 provider slot 准入
  install_ba_men_jin_suo_zhen
    AttributeSystem 发动智力快照 → 用户公式
    SkillResolver(CHOOSE_N_RANDOM_ENEMIES, min(2, living enemies))
      ApplyStateSkillEffectSpec(runtime_outgoing_damage_reduction, rate)
    SkillResolver(TEAM_COMMANDER)
      ApplyStateSkillEffectSpec(first_strike, Stage11TimedFlagParams)
    EffectExecutor → StateLifecycleSystem
    StateNode → ProviderNode(SkillProviderRef)
```

所有目标由公共选择器决定，八门不自行抽随机数，选定后不逐回合重选。两分支均在第 4 回合 `ROUND_START` 到期。先攻由既有 `ActionOrderSystem` 消费。

新通用组件 `outgoing_damage_reduction.py` 声明状态、typed `OutgoingDamageReductionParams` 及 `OutgoingDamageReductionProvider`，为状态持有者追加 `OUTGOING_REDUCTION`，适用于兵刃和谋略。同侧加算、跨侧乘算、降伤下限均由既有 `DamageModifierSystem` 处理。未修改冻结伤害、生命周期、EffectExecutor、随机数 Owner。

沿用 main 的用户批准阵法 V1 合同：携带者阵亡立即清理其施加在敌军和己方主将上的效果，保留其他来源。这不是客户端机制实证结论。

准入 factory 给出满级 canonical 身份；installer 从已注册的原始 loaded runtime 读取真实等级，并验证完整定义等于对应等级模板。默认满级，支持全部 10 级。记录 `context.metadata['ba_men_snapshots']`：等级、基础率、发动智力、生效率及两个分支的目标 ID。

## 使用

```python
from sgs_v2.battle_core import create_ba_men_jin_suo_zhen_runtime, SkillSlot

context.skill_runtimes.register(create_ba_men_jin_suo_zhen_runtime(
    "provider_id", slot=SkillSlot.LEARNED_1, level=10,
))
# 正常 BattleEngine.run() 在 PRE_BATTLE 自动接入。
```

与已有生产上下文一致，需先注册 official state catalog；缺少先攻 schema 时在目标选择 RNG 和状态施加前报错。极端智力使公式结果超出 `[0, 1]` 时明确报错，未发明额外封顶或负值规则。

## 验证

- 八门专项 **50 PASS**；[全量回归记录](ba_men_evidence/full_regression.txt) **2317 PASS**。
- 原有 Demo smoke PASS；独立新进程 canonical registry `20025` PASS。
- [Stage13-D1](ba_men_evidence/stage13_d1_audit.json)：冻结 Owner hash 不变，11 条对抗测试 PASS。
- [青州兵独立审计](ba_men_evidence/qingzhou_audit.json)：PASS。
- 生产 `DamageSystem.calculate` 验证来源与 OUTGOING modifier trace、两类伤害及阵亡清理；生产 `BattleEngine` 验证一次施加、第 4 回合真实到期。
- 同侧锋矢增减伤叠加、智力快照、全部等级与兵种、目标不足两人、同队阵法冲突、关闭 runtime 和重复安装均有行为测试。
- 等级常量逐行对照保留的静态 CSV；真实战斗行动顺序验证前三回合主将先攻、第 4 回合恢复速度排序。

跨战法净化、震慑等更细的客户端交互未因此获得实证冻结。本记录仅验收本地分支；远端 CI、PR 发布与 main 合并尚未执行。
