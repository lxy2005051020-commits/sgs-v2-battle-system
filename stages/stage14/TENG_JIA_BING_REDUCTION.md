# 藤甲兵：满级统率减伤与藤甲兵效果

2026-10-05，原独立分支 `stage14-teng-jia-bing`；父提交 `53b268e`。

状态：`BASELINE_FROZEN / MERGED_MAIN / CI_PASS`。

> Post-merge note：PR #49 已合并至 `main`，merge SHA `8d3f19eaae7e69b9f8f7e7422182d7870acb7be5`，merged-main CI `37314342610 / SUCCESS`，最终全量 `1951 passed`。藤甲兵 bounded baseline 已由 `MC-STAGE14-TROOP-BATCH01-04-BASELINE-01` 冻结；特殊净化/免疫分类等扩展问题继续 OPEN。

## 用户确认的规则

- 准备回合锁定兵刃减伤 `R = 0.24 * (1 + (战内统率 - 100) / 350)`。
- 100统率24%；450统率48%。原式计算，不采用截断的展开系数。
- 受到灼烧时施加独立的“藤甲兵效果”；它不属于灼烧，只按灼烧伤害方式计算。
- 伤害倍率300%；与原灼烧同时存在；属性来源为原灼烧施加者的兵力和智力。
- 客户端满级2009510文字给出：战法20095、盾兵、全体友军，兀突骨统领倍率250%。
- 图中13组战报及回归统计未在本次独立复现。

## 实现

减伤：`TroopSkillConfig -> PRE_BATTLE -> AttributeSystem.get_defense(holder)`
读取携带者当时最终统率，锁定快照，全队挂载独立受伤减免状态。
`IncomingDamageReductionProvider -> DamageModifierSystem.INCOMING_REDUCTION`
处理兵刃减伤，谋略伤害不变；原伤害管线处理加减伤池、看破和下限。

追加效果：全隊挂载 `ApplicationDamageReactionParams(trigger_state_id=burn)`。
`ReactingStateLifecycleSystem` 覆盖真实 EffectExecutor 的旧状态施加入口，
`ReactingStateApplicationCoordinator` 覆盖正式 StateCandidate 入口。
两者组合既有 lifecycle/coordinator，通过同步内部方法接入，不监听 EventBus，
不修改冻结的 StateLifecycleSystem、StateApplicationCoordinator、TriggerSystem 源码。

当原灼烧成功施加或刷新时，通过既有 lifecycle 挂载/刷新
`runtime_troop_damage_effect`，显示名“藤甲兵效果”。继承
`ContinuousDamageStateParams` 的持续伤害能力和原施加者冻结兵力/智力快照，
倍率替换为3.0或2.5；原灼烧本身不改变。
现有 TriggerSystem 在单位行动开始结算，DamageSystem 按冻结持续伤害管线计算。
特殊状态ID独立，不匹配灼烧触发条件，因此无递归。
来源死亡后沿用历史快照。伤害事件保持原施加者和原技能来源，并以独立
source_state_id 区分“藤甲兵效果”；parent_state_instance_id保留触发来源关联。
兀突骨必须是阵容主将，副将不改变倍率。

## 实现假设与范围

- 减伤属性取携带者统率，沿用现有兵种持有者来源映射。
- 用户已确认关联持续：持续窗口与原灼烧同步，原灼烧被净化后关联效果立即消失。
- 同队普通灼烧刷新时特殊效果刷新，保持一个特殊效果，未实现额外多层叠加。
- 特殊效果独立于burn ID，但通过parent_state_instance_id与原灼烧关联；成功净化/显式移除/到期移除原灼烧会连带移除它。
  它是否应被某类特殊净化、免疫识别，未获得独立规则，未扩展官方净化分类。
- 应通过支持的 SkillResolver/EffectExecutor 与正式 StateCandidate 入口施加。
  若直接提供没有冻结伤害依据的灼烧，反应适配器拒绝该输入。
- 使用默认 BattleSystems 生命周期适配器；自定义注入的裸 StateLifecycleSystem
  不自动具备旧施加入口的反应回调。
- 非支持范围的R>1准入前拒绝；没有自行发明公式上限。

## 验证

藤甲兵专测：46 passed。全量：1951 passed in 8.44s。
覆盖：减伤锚点、统率前向可见性与锁定、三名友军、所有伤害来源的兵刃/谋略区分、
威慑抑制与恢复、来源死亡、非法准入/槽位/重复安装、原有规则提供者兼容、
普通与兀突骨追加倍率、原灼烧共存、独立显示名、原施加者冻结属性和兵力、
来源死亡后真实结算、同回合不重复结算、不递归、非灼烧不触发、刷新不叠加、
原有生命周期到期移除、成功净化联动、拒绝净化保留、其他武将不受影响、刷新后联动、过期代际请求不误删、父状态移除事件观察不到孤立的关联效果。
测试不是图片战报的独立复现，也不构成远程CI或正式冻结。