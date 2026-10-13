# 形一阵接入记录

2026-10-13；分支 `stage14/xing-yi-zhen`；实时 fetch 的 origin/main 基线
`c4724e7abef1f7e99eca65c9e09c4074fb43dd92`。满级实现通过独立分支发布；未合入 main。
状态：`IMPLEMENTED_STATIC_DESCRIPTION_AND_USER_CONFIRMED_CURVE / NOT_GAMEPLAY_FROZEN`。

## 原文与范围

客户端静态 ID `22039`，类型 `FORMATION`，`arm_limit={}`。
保留[十级原始行](xing_yi_evidence/static_levels.csv)与
[源路径、SHA256及完整配置](xing_yi_evidence/source_manifest.json)。来源为2026-08-08导出快照，
不宣称核对了当前客户端版本。本次只实现 Lv10，不推测低等级回合取整。

满级原文：我军三名武将自带战法类型相同时，战斗中，自身最高属性提高60点，
友军群体（2人）造成及受到伤害降低30%，此效果每回合降低10%，该效果结束后，
每回合使其造成伤害提高16%，受到伤害提高1%，可叠加。

用户本次明确确认下表曲线。同来源以百分点加算，不做逐层乘法。
并列最高属性按**武力→智力→统率→速度**优先级，仅选一项提高60；此规则由用户确认，
不将其标为客户端实证冻结。属性选择始终先比较数值，优先级仅用于数值并列。

| 回合 | 两名队友造成伤害修正 | 两名队友受到伤害修正 |
|---|---|---|
| 1 | -30% | -30% |
| 2 | -20% | -20% |
| 3 | -10% | -10% |
| 4 | +16% | +1% |
| 5 | +32% | +2% |
| 6 | +48% | +3% |
| 7 | +64% | +4% |
| 8 | +80% | +5% |

之后继续逐回合叠加，不另设未经确认的上限。修正进入现有 OUTGOING/INCOMING 伤害池，
仍由公共伤害系统负责各池叠加、取整、克制、暴击与伤亡。
携带者在武力、统率、智力、速度中最高一项提高60；两名队友始终排除携带者，
不由主副将身份推断。三人的类型判断只使用 INHERENT 槽。

## 组件树

```text
FormationSkillConfig / FORMATION_SKILL_REGISTRY
  PRE_BATTLE / 100% / 无准备回合
  同队唯一阵法、基础兵种、provider SkillSlot 准入
  install_xing_yi_zhen
    完整存活三人编队 / 三人的 INHERENT 类型一致
    AttributeSystem: 读取携带者四项有效属性
    ApplyStateEffect(ATTRIBUTE_BONUS_STATE_ID, AttributeBonusParams(highest, 60))
    两名队友 ApplyStateEffect(DAMAGE_RATE_STATE_ID, RoundDamageRateParams)
    StateNode -> ProviderNode 依赖
  DamageRateModifierProvider.collect
    StateEffectivenessPolicy -> 当前回合曲线 -> 现有伤害池
```

复用准入、准备阶段调度、目标查询、属性读写、EffectExecutor、状态生命周期、依赖图、
有效性与伤害贡献系统。唯一新增公共能力 `RoundDamageRateParams` 支持任意开场回合数组
及随后逐回合加算双向修正；原 `DamageRateParams` 保持原有行为。
新增战法模块 `xing_yi_zhen.py`，通过现有 `register_formation_skill_config` 注册，
公开入口 `create_xing_yi_zhen_runtime(owner_id, slot=SkillSlot.LEARNED_1)`。
不消费 RNG、不修改冻结核心 owner，也不新增每回合状态堆积。

## 保留边界

- 最高属性读取时点未获用户确认：当前为**发动安装时有效属性快照**的暂定模型，
  选择后不因后续属性变化重新选择；缺失属性直接报错，不填零。
- 三人自带类型已知但不相同时合法携带但无效果；任一自带战法缺失时直接报错。
  判断装备类型不取决于自带战法 enabled 状态，不从学习槽推断。
- 沿用现有阵法 V1 携带者阵亡清理与提供者有效性策略，不宣称证实客户端死亡/净化细节。
- 准备阶段 round=0 使用首回合修正值，进入战斗后按 current_round 读取。
  该机制不代表证实了更细的回合起始微事件顺序。
- 低等级、当前版本变更、原始战报逐事件对照保持 OPEN。

## 验证

专项覆盖真实伤害管线双向曲线、兵刃/谋略、携带者三位置、五基础兵种、
有效最高属性快照、全部11种并列组合的优先级与单项增益、缺失报错、类型不符、调度与幂等、阵亡清理、移除状态、RNG不变、
实际 BattleEngine 自动安装与公共曲线校验。
Stage13-D1冻结核心哈希和11项对抗审计见
[冻结审计](xing_yi_evidence/frozen_owner_audit.json)。本地验证不代表远端 CI 或玩法实证冻结。

本次结果（含用户确认的并列属性优先级）：形一阵专项 **62 passed**；相关阵法与同步专项 **170 passed**；
全量 **2512 passed**（49.67秒）；21个冻结核心文件哈希一致，11项D1对抗审计PASS。
新进程registry恰含6项、22039唯一注册且解析为本模块SKILL。
保存[专项输出](xing_yi_evidence/focused_tests.txt)、[全量输出](xing_yi_evidence/full_regression.txt)、
[注册验证](xing_yi_evidence/registry_check.txt)。
