# 飞熊军：用户指定最终伤害加法模型

更新：2026-10-12。分支：stage14/fei-xiong-jun。远端main基线：60ad790c83211c6e1597e63278eb85e79bc6a0b8。

状态：**USER_SPECIFIED_FINAL_ADDITIVE_MODEL / LOCAL_RUNTIME_INTEGRATED / NOT_GAMEPLAY_FROZEN**。

用户指定实际恢复口径、两个目标共享快照、伤害期间产生的治疗计入下一次，并纠正“治疗量/10是直接加在最终的伤害中”。本规则覆盖此前的缺失公式报错方案，也覆盖对话中曾提出但未实现的“提高伤害率”解释。

## 用户模型

以H表示上次触发后、此次触发前我军全体累计造成的实际恢复兵力：

```text
普通谋略伤害率 = 64%（保持不变）
每目标最终加成 = H / 10
每目标理论最终伤害 = floor(普通64%伤害的最终整数结果 + H / 10)
```

H=1000时两个目标各加100，合计额外200；不是两人平分100，也不是提高伤害率。追加位于普通增伤、减伤、奇谋等计算之后，分担/分配及实际扣兵之前；伤兵、吸血、反应、死亡和终结仍由原owner处理。

一次触发两个目标共享H。成功产生目标批次后，在第一段伤害执行前保存并消耗累计边界，期间新增恢复进入下一次累计。概率失败不消耗累计。

代码注释、模型常量及快照事件均使用标记：
**FEIXIONG_USER_ACTUAL_RECOVERY_FINAL_ADDITION_V1**。这是用户指定模型，不是客户端实证冻结。

## 组件树

```text
TroopSkillConfig(20247, CAVALRY -> FEI_XIONG_JUN)
  PRE_BATTLE -> resolve_recovery_definition
    FIXED_ALL_TEAM -> ReceivedRecoveryBonusParams(16% / 董卓主将20%)
  supplemental -> TEAM_COMMANDER
    ApplyStateSkillEffectSpec(runtime_action_start_recovery_damage)
      probability=.60 / STRATEGY / coefficient=.64 / target_count=2
      recovery_damage_ratio=1/10 / 用户模型标记

AccumulatedRecoveryRuleHookSystem(UnitActionStartHook)
  原有行动开始Hook批次完成后
  -> ActionStartRecoveryDamageSupport
  -> 状态/提供者/主将执行权/终结门控与同回合防重复
  -> project_settled_team_recovery（已结算恢复事实）
  -> SkillResolver（一次概率与规范目标选择）
  -> 消耗H对应的事件边界，发布用户模型快照
  -> 两个规范DamageEffect（final_additive_damage为相同H/10）
  -> EffectExecutor / AdditiveDamageSystem最终加法接口
  -> 原DamageInstanceCoordinator / 分担分配 / 扣兵 / 派生恢复
```

提供者为携带者，伤害执行者与智力读取者为主将，不在主将身上伪造技能槽位。治疗增益按接收者生效，董卓必须是主将才能取20%。

累计只读取TROOPS_RECOVERED.actual_recovery，按治疗提供者所属队伍归集；不重复统计RECOVERY_RESOLVED汇总，不读取名义治疗或请求值。溢出与禁疗未实际恢复的部分不计入。伤害期间真实吸血也进入下一次。无来源恢复不强行归入本队。

## 工程默认与仍开放的玩法边界

- 触发位于普通UnitActionStartHook批次之后、行动开始寿命结算之前；同一主将同一回合最多尝试一次。更细游戏顺序仍OPEN。
- 复用StateEffectivenessPolicy、ProviderValidityPolicy、CurrentActorPermissionPolicy与最终化门控；提供者或主将死亡时不触发。提供者在两段伤害之间失效的游戏细节仍OPEN。
- 不绕过规避、抵御、虚弱与全额警戒拦截。成功选出目标后即消耗累计，即使伤害被防止；该重置边界仍需战报确认。
- 治疗增益状态遵循已有持久修饰语义；修改SkillRuntime.enabled不等于删除已经施加的状态。死亡/威慑下治疗增益的生命周期仍OPEN。
- 敌军不足2人保留公共目标系统的显式insufficient candidates边界，未自定单目标行为，也不消耗累计。
- H/10小数按最终整数伤害向下取整，无另设上限。取整细节为工程约定。
- 20247与各等级参数待客户端原始资源核对；目前只声明满级参数。

## 来源边界

[官方攻略](https://bbs.4399.cn/thread-view-tid-42385703)和[公开战法描述汇编](https://sanzhan.slgsim.com/zh-hans/tactics/)仅用于公开描述参考。H/10最终加法、实际恢复口径与快照规则的直接依据为用户2026-10-12指令，不从攻略推算。尚未完成5份原始飞熊军战报验证，工程测试不是游戏机制证明。

## 文件与验证

战法模块：sgs_v2/battle_core/troop_skills/fei_xiong_jun.py。
通用新增：action_start_recovery_damage.py。
复用并扩展additive_damage.py、effects.py；保留received_recovery_modifier.py。
组合与声明：battle_systems.py、state_modifiers.py、troop_admission.py、enums.py、__init__.py。
测试：tests/test_stage14_troop_fei_xiong_jun.py、tests/test_action_start_recovery_damage.py。

没有改动冻结的BattleEngine、DamageSystem、RecoverySystem、RuleHookSystem、TriggerSystem等owner。以通用RuleHookSystem子类组合新状态，在现有AdditiveDamageSystem增加opt-in最终加法请求与结果；原modifier trace保留普通伤害计算，追加层以独立结果字段及快照事件记录。新组件不硬编码战法名或编号。

触发参数为不可变状态声明。实际累计边界和同回合尝试计数存于BattleContext.metadata内的类型化RecoveryDamageCursor，以状态instance_id和generation共同隔离；不直接修改StateRegistry，也不修改生命周期对官方状态参数维护的冻结授权。伤害效果由现有SkillResolver产生，本组件仅用dataclasses.replace附加最终增量与执行者归因，不新增伤害生产入口。

实际注册仍为TROOP_SKILL_REGISTRY，无另建自动发现路径。清洁进程核对20247的CONFIG/factory/SKILL。

可重放验证：scripts/verify_fei_xiong_jun.py --output stages/stage14/feixiong_evidence/verification.json。
当前结果位于feixiong_evidence/；原报错方案输出保存在history/known_recovery_slice_92842f1/，不作为当前状态。

专项51项验证治疗、最终加法、快照、真实吸血、期间恢复、失败保留、免疫/虚弱、奇谋、门控、目标不足、跨战斗游标隔离等；加上原有31项架构检查，共82项通过。全套2192项通过，Stage13-D1冻结owner哈希检查与11项独立对抗检查PASS，标准demo与清洁进程注册检查PASS。详细输出见当前验证记录。

当前为本地独立分支，未合入main，未完成远端CI。
