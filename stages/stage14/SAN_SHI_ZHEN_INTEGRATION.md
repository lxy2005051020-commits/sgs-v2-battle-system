# 三势阵接入记录

状态：`IMPLEMENTED_USER_SPECIFIED_MODEL / NOT_GAMEPLAY_FROZEN`，2026-10-13。工作树
`D:\模拟系统\stage14-san-shi-zhen`，分支 `stage14/san-shi-zhen`。
基于本次实时 fetch 的 Battle origin/main `74817c59325bcaf7fafd5fc67f40621174ec9d65`。
原工作树验证为历史快照；本次统一发布见[阵法同步记录](FORMATION_COMPLETED_SYNC.md)。本地验证不代表远端CI。

## 描述与规则来源

正式 ID `22012`、类型 `FORMATION`，客户端静态 `arm_limit={}`，沿用五种基础兵种准入。
满级静态描述：

> 我军三名武将阵营均不相同，且我方主将自带战法为主动战法或突击战法时，战斗前5回合，主将提高16%自带主动、突击战法发动几率，每回合行动前，使损失兵力较多的副将受到伤害降低30%，另一名副将造成伤害提高25%，持续到战斗结束。

[静态十级原始行](san_shi_evidence/static_levels.csv)保留每一级原文；
[来源清单](san_shi_evidence/source_manifest.json)保留源路径、SHA256、完整配置。
实现全部十级，三项数值逐行读取，不对显示百分数插值，也无属性缩放。

用户明确确认：**损失兵力相同时选择副将1；旧效果清除**。
因此平局时副将1减伤、副将2增伤；每次有效重新分配先移除同一来源的旧增减伤，
再施加新的两路状态。其他战法或携带者的贡献不受影响。每个携带者每回合只执行一次，
重复 hook 不重复施加。

主将发动率加成只匹配 `SkillSlot.INHERENT` 和实际自带战法类型，
不增加学习战法或副将的发动率。沿用公共发动率加算与 `[0,1]` 封顶。
第6回合 `ROUND_START` 清除发动率加成；副将分配继续至战斗结束。

`UnitRuntime.faction` 是可选关键字字段，不等于战斗的 `team_id`。
三势阵阵容必须提供三个明确的阵营值（如 `魏/蜀/吴/群`，同一阵营请保持同一编码）。
未知阵营明确拒绝，不从名称推断。已知阵营重复或主将没有主动/突击自带战法时，
阵法合法装备但不安装效果。关闭的自带战法仍保持其装备类型条件；运行资格由正式技能准入负责。

## 显式模型边界

以下为可检查的本地模型假设，**不表示用户确认或客户端实证冻结**：

- “每回合行动前”按**阵法携带者**的 `UnitActionStartHook` 执行，
  在普通行动前状态批次（含持续伤害和恢复）结算后、正式行动之前比较兵力。
- “损失兵力”按阵法安装时记录的入场兵力减当前兵力，即净损失；
  不是最低当前兵力、最大兵力差、伤兵池或累计受伤次数。治疗可以改变下一次比较结果。
- 描述中的前5回合限制仅作用于主将发动率加成，副将分配继续至战斗结束。
- 安装时要求完整存活三人阵容；后续缺少一名存活副将时清除旧分配并跳过，
  记录 `MISSING_LIVING_DEPUTY_PAIR`，不自行给唯一副将补齐双效果。

携带者阵亡即清理其全部效果，沿用当前 main 用户批准的阵法 V1 合同，
不是本次新增的客户端实证结论。清除驱动状态后旧伤害修饰立即失效，且不再产生新分配。

## 组件树与文件

```text
FormationSkillConfig / FORMATION_SKILL_REGISTRY
  PRE_BATTLE / 100% / 无准备回合
  同队唯一阵法、兵种与 SkillSlot 准入
  san_shi_zhen.py: install_san_shi_zhen
    明确阵营、完整阵容、主将 INHERENT 的 ACTIVE/ASSAULT 条件
    ApplyStateEffect(runtime_activation_rate_bonus)
      ActivationRateBonusParams(actual_type, level_bonus, skill_slot=INHERENT)
      第6回合 ROUND_START 到期
    ApplyStateEffect(runtime_action_start_role_split)
      RoleSplitParams(两名副将入场兵力, level_reduction, level_increase)
  UnitActionStartHook(携带者) / 每回合一次
    RoleSplitRuleHookSystem → 原 PoolRuleHookSystem 普通状态批次
    ActionStartRoleSplitSupport
      StateEffectivenessPolicy 检查有效 driver/provider
      PriorityTargetSystem.most_lost_troop_deputies
      RemoveStateEffect(本来源旧伤害修饰)
      ApplyStateEffect(runtime_damage_rate_modifier)
        第一目标 incoming_rate=-reduction
        另一目标 outgoing_rate=+increase
      EffectExecutor → StateLifecycleSystem → ProviderNode
DamageRateModifierProvider → 正式 DamageModifierSystem → 正式 DamageSystem
```

新通用组件 `action_start_role_split.py`（driver、每回合分配、hook 适配）与
`damage_rate_modifier.py`（带可选驱动前置条件的正负伤害贡献），
均不判断战法名称或 ID。扩展公共 `ActivationRateBonusParams` 的可选槽位过滤与
同源维度冲突处理；默认 `None` 保持旧的全部同类型槽位加成。
`priority_target_system.py`新增副将净损失排序；`unit.py`新增阵营字段及可检查快照。
`battle_systems.py`组合上述 opt-in provider/hook；`formation_admission.py`、
`__init__.py`接入唯一 canonical 工厂和公共 API。

未修改冻结伤害、治疗、状态生命周期、EffectExecutor、TriggerSystem、
RuleHookSystem、TargetSystem、TroopSystem、随机源或 BattleEngine。
伤害修饰的前置状态检查通过公共 effectiveness adapter 完成，
避免被移除驱动产生悬空 `StateNode` 引用。

## 使用

```python
from sgs_v2.battle_core import create_san_shi_zhen_runtime, SkillSlot

# 阵容的 UnitRuntime 显式提供 faction；主将真实自带战法注册于 INHERENT。
context.skill_runtimes.register(create_san_shi_zhen_runtime(
    "provider_id", slot=SkillSlot.LEARNED_1, level=10,
))
# 正式 BattleEngine.run() 自动进行战前安装和行动前分配。
```

观察结果保存在 `context.metadata['san_shi_admissions']` 和
`context.metadata['action_start_role_split_history']`，包括等级、条件、来源槽位、
每回合损失兵力、两个目标和缺员标记。状态施加/移除沿用正式事件日志。

## 验证

- 三势阵专项 **47 PASS**，包括全部等级对原始行校验、两种自带类型、真实
  SkillResolver 概率消费、槽位过滤与旧组件兼容、两类伤害正式管线、平局、
  换人先清旧效果、治疗后净损失、保护其他来源、缺员、驱动移除、重复执行、
  关闭 runtime、三种携带位置、阵亡清理、五种兵种和正式6回合引擎种子复现。
- [全量回归](san_shi_evidence/full_regression.txt)：**2314 passed**。
- [Stage13-D1审计](san_shi_evidence/stage13_d1_audit.json)：全部冻结 Owner
  哈希一致，独立对抗测试 **11 PASS**，verdict=`PASS`。
- [青州兵审计](san_shi_evidence/qingzhou_audit.json)：`PASS`，含原有 Demo smoke。
- 独立新进程导入 `FORMATION_SKILL_REGISTRY['22012']`，唯一 canonical 定义与 `SKILL`一致。

这些结果验证当前模型实现，不补足上述客户端机制证据。
