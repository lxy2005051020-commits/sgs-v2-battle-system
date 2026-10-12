# 丹阳兵接入说明

日期：2026-10-12。分支：`stage14/dan-yang-bing`。
基线：GitHub main `f189c84`（飞熊军 PR #62 合并后）。
状态：**RUNTIME_INTEGRATED / USER_CONFIRMED_GENERATION_RATIO / GAMEPLAY_DETAILS_OPEN**。
此分支兵种注册表共15项；尚未合并main。

## 参数和口径

- 本地旧战法模块记录base_id 20245、满级全体统率+36、抵挡36%，陶谦统领40%，每回合衰减10%。客户端ID仍待原始资源核对。
- 用户在本次对话明确确认：丹阳兵生成量为上一回合我军全体造成的兵刃伤害的1.0倍。
- 暂按全队共享一个兵池，状态挂在主将、提供者绑定实际携带者及战法槽位。陶谦加成判断主将姓名，不判断携带者姓名。
- “造成伤害”暂取`DAMAGE_DEALT.payload.damage`实际扣兵口径；普攻及兵刃战法均计入，敌方、谋略伤害、直接扣兵不计入。理论伤害与超出目标剩余兵力的部分不计入。
- 暂定回合开始先对已有兵池衰减10%，再加上一回合生成量。首回合池为0；同回合Hook重复执行不重复生成或衰减。
- 生成、衰减及抵挡取整数向下取整，以十进制有理数计算，避免浮点临界值误差。
- 抵挡发生在分担/分配确定目标伤害后、实际扣兵前：`抵挡=min(池量,floor(分配伤害*抵挡比例))`。不足时消耗剩余池量；仅剩余伤害产生实际扣兵、伤兵、归因及后续反应。
- 未命中、被防止或0伤害不消耗；直接扣兵绕开该机制。伤害预览/计算不消耗兵池；正式结算许可消费成功后才扣池，同一许可重放无副作用。
- 状态失效期间暂停生成和抵挡，已有池继续按回合衰减；恢复有效后使用剩余池。状态移除/战斗终结由原生命周期处理，元数据保留已结束战斗账本供检查，不能继续生效。

全队共享、实际扣兵口径、衰减与生成顺序、取整、与分担/分配的相对层级属于明确实现选择，仍需原始战报验证，不声明玩法冻结。

## 组件树与改动

```text
TroopSkillConfig(20245, SHIELD -> DAN_YANG_BING)
  PRE_BATTLE / FIXED_ALL_TEAM
    ApplyStateSkillEffectSpec -> AttributeBonusParams(defense, 36)
  supplemental / TEAM_COMMANDER
    ApplyStateSkillEffectSpec -> TemporaryDamagePoolParams(.36 / 陶谦.40)

PoolRuleHookSystem(RoundStartHook)
  -> TemporaryDamagePoolSupport.round_start
  -> 原有普通Hook及飞熊军行动开始处理

PoolDamageResolutionSystem
  -> 原有DamageResolutionSystem校验并消费许可
  -> _PoolTroopSettlement -> TemporaryDamagePoolSupport.absorb
  -> 原有TroopSystem.apply_damage(剩余伤害)
  -> 原有伤害事实 / 死亡 / aftermath / 反应与终结
```

战法单独位于`troop_skills/dan_yang_bing.py`，沿当前项目的显式`TROOP_SKILL_REGISTRY/CONFIG`接入；当前项目没有旧技能库的`register_skill`或模块自动发现API，因此沿用生产注册方式，不引入另一套注册器。

新增通用组件`temporary_damage_pool.py`及内部状态参数；新增`TEMPORARY_POOL_UPDATED`事实事件记录生成、衰减、消耗及源伤害事件序号。原`engine.py`、`damage_system.py`、`damage_resolution_system.py`、`troop_system.py`、分担/分配及伤害许可owner均未修改；仅在组合根选用继承适配器。

## 验证

- 丹阳兵专项：18 passed，覆盖准入原子性、身份、属性、提供者槽位、陶谦主将、上一回合口径、叠加、衰减、防重复、全队共享抵挡、耗尽、防止、实际兵力上限、直接扣兵、状态抑制恢复、正式许可及重放、完整BattleEngine。
- 全量：2210 passed。
- 原demo.py：PASS；全新进程生产注册表解析：PASS，20245解析到CONFIG且工厂等于SKILL，无重复注册。
- Stage13 D1冻结owner哈希及对抗测试结果保存在`dan_yang_bing_d1_audit.json`。
- 上述是运行时回归，不代替原始战报实证或远端CI。
