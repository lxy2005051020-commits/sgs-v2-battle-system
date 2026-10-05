# Stage14 第一批：白马义从 + 虎豹骑

状态：`BASELINE_IMPLEMENTED / LOCAL_VALIDATION_PASS`。未合并主线。

## 范围和证据

本批次按用户 2026-10-05 指定，仅接入白马义从（20075）与虎豹骑（20098）。
用户随后明确：属性缩放“暂时不考虑，用空白占位”。两份战法模块的
`COMMANDER_SCALING = None` 表示未实现，不能解释成零系数或已验证的基础公式。

实现基线：Battle `766eeaac16e227c9eee250e452403020f16e11ea`，已包含西凉铁骑。
Research 权威：2026-10-05 fetch 后的 `origin/main`（完整 SHA 见来源快照）。

依据：

- Research `Stage14_Troop_Skill_Research/00_Governance/TROOP_SKILL_CATALOG.md` 中的
  20075、20098 条目。这是目录证据；原条目的独立合同状态仍为 OPEN。
- Research `TROOP_SKILL_IDENTITY_AND_PROVIDER_LIFECYCLE_CONTRACT.md`：
  复用 PRE_BATTLE 进阶、基础兵种克制、前向属性可见性、持有者来源及失效生命周期。
- 本地客户端文本 CSV `D:\三国志战略版战斗模拟系统\战法\战法类型_8_兵种.csv`：
  保存实际读取的等级文本、记录键和 SHA-256 至 `batch01/source_snapshot.json`。
  本地提取文本不是对现行官方客户端版本的独立验证。
- 旧模拟器仅用于寻找资料，不作为游戏机制或冻结公式权威。

## 本次实现的基础效果（满级）

| 项目 | 白马义从 | 虎豹骑 |
|---|---|---|
| 基础兵种 / 特殊身份 | BOW / BAI_MA_YI_CONG | CAVALRY / HU_BAO_QI |
| 安装时点 | PRE_BATTLE | PRE_BATTLE |
| 目标 | FIXED_ALL_TEAM，含持有者 | FIXED_ALL_TEAM，含持有者 |
| Effect Tree | 先攻 + ACTIVE 发动率修饰 | attack 属性修饰 + ASSAULT 发动率修饰 |
| 效果数值 | 先攻；主动发动率 +10 个百分点 | 武力 +40；突击发动率 +10 个百分点 |
| 自然到期 | 两项均于 R3 ROUND_START 到期 | 发动率于 R4 ROUND_START 到期；武力至战斗结束 |
| 安装随机 / 准备回合 | 无 / 无 | 无 / 无 |
| 属性缩放 | 空白占位，USER_DEFERRED | 空白占位，USER_DEFERRED |

白马的地图行军速度 +50% 属战略地图层，本项目战斗引擎没有行军域；不将其误写为
战斗 `speed` 属性提升。

公孙瓒文本的“生效时间改为前4回合”是否同时延长先攻与发动率，在当前材料中没有
独立裁决。本次 `COMMANDER_DURATION = None`，仍采用基础两回合分支，明确保留为
待确认，不能据此声称公孙瓒统领分支已完整支持。曹纯缩放同样不支持。

## 接缝和组件复用

复用：`process_pre_battle_troop_skills`、`TroopSkillConfig`、
`admit_and_install_troop_skill`、`SkillDefinition`、`ApplyStateSkillEffectSpec`、
`SkillResolver`、`FIXED_ALL_TEAM`、`StateApplicationCoordinator`、
`StateLifecycleSystem`、`StateEffectivenessPolicy`、`SkillProviderRef`、
`StateNode -> ProviderNode`、`Stage11TimedFlagParams`、`ActionOrderSystem` 和唯一 RNG。

通用扩展：

- `state_modifiers.py` 提供 `AttributeBonusParams`、`ActivationRateBonusParams` 和
  `StateModifierSupport`。两个内部状态 ID 是 Runtime 表达，不冒充官方状态编号。
- `AttributeSystem.register_modifier_provider` 保留已有修饰符和装备接口，增加组合入口。
- `SkillResolver.activation_rate_provider` 在准入和候选预检后、唯一发动率判定前读取
  实时有效值；不改写不可变 `SkillDefinition.activation_rate`，不消耗额外 RNG。
- 内部贡献采用加法，概率最终限制在 [0,1]；按来源和维度区分贡献，同源重复不叠加。
  这是本批次通用组件的模型策略，不能泛化为所有官方发动率修饰的已冻结叠加规则。
- 准入按 canonical ID 构造定义，拒绝不同特殊兵种身份冲突及已占用来源槽位，
  防止虎豹与西凉同时挂载或将增益错误绑定到其他战法。

项目实际注册方式为 `TROOP_SKILL_REGISTRY` 配置及生产 Runtime 工厂，没有
`register_skill` / 自动发现 API。本批次沿用实际注册方式，两战法各自一个独立模块，
不添加第二套技能注册框架。

没有修改 Engine 调度、伤害公式、普通攻击、执行权或状态物理写入所有者。
发动率修饰覆盖现有 `SkillResolver.resolve` 入口；本批次没有新增主动/突击战法自动
施放调度器，不把发动率修饰测试宣称为所有战法的端到端调度闭环。

## 生命周期验收

| 验收项 | 测试范围 |
|---|---|
| 队伍效果与克制身份 | 3 名友军、无敌军增益、基础兵种保持、真实先攻排序 |
| 发动率实际消费 | ACTIVE / ASSAULT 类型隔离、单次 RNG、定义原值保持 |
| 时间窗口 | R1–R2 / R1–R3，精确 ROUND_START 到期，虎豹武力不随发动率到期 |
| 来源失效 | 威慑抑制与恢复、压制中时钟继续、过期后无补偿；伪报不封 TROOP |
| 来源死亡 | 已安装存活友军效果保留自身时钟；虎豹已挂载属性仍可读取 |
| 准入 | 兵种不符、混编、禁用、非法阶段、重复、不同特殊兵种冲突、槽位冲突 |
| 通用修饰 | 已有属性 provider 共存、多源相加、同源重复拒绝、有限数值验证 |
| 引擎 | 自动 PRE_BATTLE 安装、战斗结束清理；两个战法均覆盖 |
| 占位 | 缩放和白马统领时长使用 None，不填假公式 |

## 发布边界

基础 Runtime 本地实现与游戏机制合同冻结是不同状态。
本批次没有将两个 OPEN 条目自动改成 FROZEN，没有发布 Research 合同，也没有
执行主线合并。按 Stage14 既有门禁，正式进入 main 前仍需独立机制合同收口、
Runtime 审阅及 PR CI。用户已延期的统领缩放应在发布范围中明确标为未实现。

验证记录见 `batch01/VALIDATION.md`；本次不声称已完成独立第三方审计或远端 CI。
