# 箕形阵（20178）满级模型接入

基线：2026-10-13 实时获取的 Battle origin/main `74817c5`。隔离工作树
`D:\模拟系统\stage14-ji-xing-zhen`，分支 `stage14/ji-xing-zhen`。

用户公式：`减伤率 = 40% + 16/150 × (武力 - 100)`。
按百分数点解释斜率，内部使用 `0.40 + 0.16/150 * (strength - 100)`。
武力100/250/400对应40%/56%/72%。不做展示精度舍入；结果超出[0,1]拒绝，
不推断单战法上限。公式状态为 `USER_SPECIFIED_FORMULA / NOT_CLIENT_EMPIRICALLY_FROZEN`。

来源：`ji_xing_evidence/static_levels.csv`保留客户端静态导出10个等级原始行；
`manifest.json`保存原文件路径、SHA256、完整20178配置、用户公式。
本轮仅实现Lv10；不推导其他等级的属性斜率。

效果树：FORMATION准入 → PRE_BATTLE安装（100%，无准备）→
敌军主将造成兵刃与谋略伤害降低 → 我军随机副将受到兵刃伤害降低20% →
保留另一名副将，受到谋略伤害降低20%。三路状态均在第4回合ROUND_START过期。
客户端配置arm_limit为空，沿用所有基础兵种的准入。

武力通过AttributeSystem.get_attack读取携带者的有效属性。
读取时点暂采用阵法安装快照：`PROVISIONAL_INSTALLATION_TIME_PROVIDER_ATTACK`；
这是可检查的模型假设，尚无用户裁决或战报验证。之后武力改变不会追溯修改快照。
需要一名存活敌军主将和两名存活我军副将；缺员阵容提前拒绝并保留为OPEN，
不自行推断缺员时分配方式。

复用FormationSkillConfig/阵法调度、TargetSystem、ApplyStateEffect/EffectExecutor、
IncomingDamageReductionParams/Provider、StateLifecycle、ProviderNode/StateNode、
DefeatCleanupPort与正式DamageModifierSystem。
新增通用OutgoingDamageReductionParams/Provider，仅把有效来源状态映射为
OUTGOING_REDUCTION贡献；同池叠加、地板、穿透由原伤害系统负责。
没有修改冻结伤害、治疗或生命周期owner。

调用：`create_ji_xing_zhen_runtime(owner_id, slot=SkillSlot.LEARNED_1)`，
注册进`context.skill_runtimes`后由正式BattleEngine自动准入安装。
此仓库的实际注册接口是FormationSkillConfig；没有另建技能自动发现体系。

验证：箕形阵专项22项与锋矢阵/F0回归合计65项通过。
覆盖百分数点、有效属性快照、目标和来源、互斥伤害类型、正式伤害管线、
回合1至3/回合4到期、阵亡跨队清理、重复安装、种子复现、缺员拒绝和完整引擎入口。
全量回归：2289 passed（49.68s）。D1冻结owner哈希全部一致，独立对抗测试
11 passed；报告为`ji_xing_evidence/d1_audit.json`，verdict=PASS。
已通过新进程导入核对20178唯一注册及工厂定义一致性。
交付为本地分支，未推送、未合并，不表示远端CI已通过。
