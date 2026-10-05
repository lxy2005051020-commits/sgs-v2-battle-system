# Stage14 第二批：无当飞军 + 陷阵营

状态：`BASELINE_FROZEN / MERGED_MAIN / CI_PASS`。

> Post-merge note：PR #47 已合并至 `main`，merge SHA `b5dbd2db52a70834b7b9eeb9bce1b3816f837e06`，merged-main CI `37314103287 / SUCCESS`。Research bounded baseline 已由 `MC-STAGE14-TROOP-BATCH01-04-BASELINE-01` 冻结；下文原始门禁描述保留为分支开发时的历史记录。

## 范围与来源

用户 2026-10-05 指定接入无当飞军（20100）和陷阵营（20096），明确提供无当伤害率
公式，并指定陷阵营高顺统领暂时空白占位。实现范围为满级基础分支及王平目标扩展。

实现基于第一批提交 `7cf0620478e540d5859802b8d8c270112f813dea`；该提交位于
`stage14-troop-batch-01`，截至本批创建时尚未合并 main，见 GitHub PR #46。
本批分支 `stage14-troop-batch-02` 依赖第一批的状态属性修饰，不重复实现属性计算系统。

来源快照 `batch02/source_snapshot.json` 保存：

- Research 当前 `origin/main` 的完整 SHA；其战法目录 20100 / 20096 条目仍为 OPEN。
- 本地 `D:\三国志战略版战斗模拟系统\战法\战法类型_8_兵种.csv` 的 SHA-256，
  两个战法各 10 个等级的完整原记录及 `full_id` 记录键。满级原文对应 2010010 / 2009610。
- 用户公式原图 `batch02/user_rate_formula.png` 及 SHA-256，公式权威为用户本次指令。

本地提取文本不是现行官方客户端版本的独立验证，旧模拟器不作为公式权威。
特殊兵种身份、前向属性可见性、来源生命周期继承 Research 的
`MC-STAGE14-TROOP-FOUNDATION-01`；持续伤害、急救、治疗计算继承已有正式执行接口。

## 无当飞军

```text
SkillType.TROOP / BOW -> WU_DANG_FEI_JUN
PRE_BATTLE -> FIXED_ALL_TEAM -> defense +22, speed +22
R1 ROUND_START -> one-shot Skill application
    默认：CHOOSE_N_RANDOM_ENEMIES (2)
    王平为 LineupPosition.COMMANDER：FIXED_ALL_ENEMIES
    -> POISON -> target action-start ticks R1, R2, R3
```

无准备回合；战法安装不作随机发动判定。默认两目标的随机选择由现有 TargetSystem / 
SkillTargetPolicy 完成，王平全体分支不随机挑选。王平仅为副将不触发全体分支。

用户指定公式：

```text
Rate(I_A) = 0.80 * (1 + max(0, I_A - 350) / 1500)
```

`I_A` 在本批解释为战法携带者通过 `AttributeSystem.get_intelligence` 读取的当前最终
智力，在 R1 开始施加中毒时读取。携带者、队伍主将与中毒目标不是同一个概念。
例如 I_A<=350 时为 80%，I_A=500 为 88%，I_A=650 为 96%，I_A=1850 为 160%。
该值是伤害系数，不是概率；不限制到 100%，不作中间取整。

中毒应用时使用 `ContinuousDamageBasisProducer.capture` 冻结完整伤害基础；后续
由已有持续伤害管线结算，仍遵循正式伤害整数化。施加后改变来源智力/兵力不会重算
既有中毒快照。副将携带者死亡后的既有中毒保留自身时钟；队伍终结仍由最终结算器负责。

### 实现边界

- 首回合安装选择 R1 ROUND_START 的现有 PendingWork 检查点（回合开始 hook 完成后、
  行动排序前），不伪装成 PRE_BATTLE 中毒应用。客户端内部与其他首回合效果的更细
  顺序仍需战法独立证据。
- 采用“实时应用时读取”的 I_A 口径；用户公式本身没有额外指定更早的数值快照时点。
- 默认两目标不足两个合法敌军时，保持现有 TargetPolicy 的 fail-closed 边界并显式报错；
  不自行把 CHOOSE_N 改成 min(N, alive_count)。王平全体目标不受此两目标门槛限制。
- 本批明确为中毒挂接来源依赖并启用 QUERY_SKILL_RUNTIME 门控：暂时来源失效时
  跳过 tick、时钟继续，恢复后无补偿。该选择沿用共享压制生命周期模型，尚未提供
  无当中毒被威慑后的战法独立战报裁决。保留为审阅问题，不能把合成测试当作游戏实证。
- 启动前缺少来源智力时在身份/状态 mutation 前拒绝；R1 执行时来源死亡或失效则
  一次性开场工作取消，不在后续回合补施中毒。

## 陷阵营

```text
SkillType.TROOP / SHIELD -> XIAN_ZHEN_YING
PRE_BATTLE -> FIXED_ALL_TEAM
    -> attack +22, defense +22 (整场)
    -> FIRST_AID (前三回合)
       after settled damage -> probability 0.40
       -> RecoveryOpportunitySystem -> TreatmentFormulaSystem -> RecoverySystem
```

基础治疗率 0.60，智力与兵力使用 PRE_BATTLE 携带者的当前最终智力/当前兵力快照。
`RecoveryPotencyContext` 交给已有 `TreatmentFormulaSystem`；战法模块不复制 FB1、
修饰池、取整、伤兵限制或禁疗逻辑。

急救于 R4 ROUND_START 到期；属性增益不随急救一同到期。急救失败仅消耗既有概率
检定，不治疗；来源暂时失效不作 RNG 检定，恢复后仍按原窗口执行。已挂载的存活
友军急救继续使用应用时来源快照，来源死亡不会被替换成受疗者属性。

`GAO_SHUN_COMMANDER_ENHANCEMENT = None` 是用户要求的空白占位；高顺主将当前
仍按基础 40% 概率、60% 治疗率执行，没有填入零系数或猜测统率公式。

## 复用与扩展

复用：第一批的 `StateModifierSupport` / `AttributeBonusParams`，以及
`TroopSkillConfig`、兵种准入、`ApplyStateSkillEffectSpec`、`SkillResolver`、
TargetPolicy、`ContinuousDamageBasisProducer`、`ContinuousDamageStateParams`、
`PersistentLifecycleWindow`、`FirstAidStateParams`、`RecoveryPotencyContext`、
PendingWork、状态物理生命周期、ProviderValidity、伤害/治疗正式所有者。

新增或扩展的通用接缝：

- `ScheduledSkillSupport`：一次性定时技能应用桥。PendingWork 只保存来源身份和
  调度数据，执行时委托现有 resolver / effect executor。开场定义在战法模块声明，
  没有在 Engine 中写入无当 ID 或数值。
- `TroopSkillConfig.opening_definition_resolver`：可复用的开场定义声明入口。
- `ApplyStateSkillEffectSpec.continuous_damage_coefficient`：将战法系数交给已有
  连续伤害基础捕获器；`SkillResolver` 使用正式 producer 捕获，生命周期仍拥有
  实际安装 generation / instance。历史来源次级引用不填尚未创建的身份，不留假 ID。
- `StateEffectivenessTriggerAdapter`：组合冻结的 TriggerSystem，只过滤明确启用
  来源门控的 DOT 意图，查询正式 StateEffectivenessPolicy。已有 always-active
  持续伤害与急救收集逻辑保持既有行为。

两个战法各有独立模块及 `SKILL`，沿用实际 `TROOP_SKILL_REGISTRY`，不另建自动发现
框架。没有更改 frozen owner 清单或审计脚本；所有被冻结文件的哈希检查通过。

本批没有扩展核心伤害/治疗公式、终结裁决或 PendingWork 的调度权限。

## 验证与发布

详见 `batch02/VALIDATION.md`。全量和专测验证的是上述 Runtime 及用户指定代数公式，
不替代真实战报留出验证、独立机制合同收口或第三方 Runtime 审阅。

本批可以作为依赖第一批的草稿 PR 审阅；独立合同未冻结时不进入 main。
