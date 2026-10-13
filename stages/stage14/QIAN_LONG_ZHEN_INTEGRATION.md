# 潜龙阵接入记录

2026-10-13；独立分支 `stage14/qian-long-zhen`；GitHub API核对main基线
`0e8a9ed223e918bc7872e67e88d2102e08cdab2c`。
状态：`IMPLEMENTED_STATIC_DESCRIPTION_AND_USER_CONFIRMED_SNAPSHOT / NOT_GAMEPLAY_FROZEN`。

客户端静态ID `22040`，阵法，`arm_limit={}`；十级原文、完整配置和源文件SHA256保存在
[原始行](qian_long_evidence/static_levels.csv)、[来源清单](qian_long_evidence/source_manifest.json)。
来源为2026-08-08静态快照，不宣称验证了当前客户端版本。

## 行为与数值

我军三名武将阵营各不相同时，主将四维提升、造成伤害降低15%；副将造成伤害提高、
受到伤害降低，且可触发其战法的主将效果。若主将任意已装备战法拥有主将效果，
主将失去该效果，四维改用较低比例。所有已装备槽位参与存在性判断，包括disabled战法。
三人同阵营或仅两个阵营时合法携带但无效果；缺失阵营或完整存活编队直接报错。

| 等级 | 常规主将四维提升 / 副将增伤减伤 | 主将拥有主将效果时四维提升 |
|---|---|---|
| 1 | 7.5% | 2.5% |
| 2 | 8.3% | 2.8% |
| 3 | 9.2% | 3.1% |
| 4 | 10% | 3.3% |
| 5 | 10.8% | 3.6% |
| 6 | 11.7% | 3.9% |
| 7 | 12.5% | 4.2% |
| 8 | 13.3% | 4.4% |
| 9 | 14.2% | 4.7% |
| 10 | 15% | 5% |

用户确认：补齐通用主将效果接口；四维按发动时有效属性快照乘百分比产生固定增量。
当前快照在潜龙阵任何状态安装之前读取，包括主将资格切换之前；若开场被动已经提供
属性主将效果，该效果进入发动时快照，资格切换后旧效果停用，但固定增量不重新计算。
不取整、不插值；后续增益不改变潜龙阵增量。此微时序是明确工程模型，未作战报实证冻结。

## 组件树

```text
FormationSkillConfig / FORMATION_SKILL_REGISTRY[22040]
  PRE_BATTLE / 100% / 无准备回合 / 同队唯一阵法
  完整存活编队 + 三个明确且不同的faction
  主将全部已装备SkillDefinition.commander_effect_specs存在性
  AttributeSystem: 四维有效值快照
  ApplyStateEffect
    三人 CommanderEffectRoleParams: 主将False / 两副将True
    主将四项 AttributeBonusParams: snapshot * rate
    主将 DamageRateParams: OUT -15%
    副将 DamageRateParams: OUT +rate / IN -rate
  StateNode -> ProviderNode
  既有状态有效性、生命周期、伤害池、阵亡清理
```

公开入口：`create_qian_long_zhen_runtime(owner_id, level=10, slot=SkillSlot.LEARNED_1)`。
携带者可为三个位置任意一人；效果目标始终按真实主副将确定。
既有canonical registry是实际注册路径，本仓库没有`register_skill`或类别自动扫描器，
沿用现有单战法模块位置和`register_formation_skill_config`，不另造注册系统。

## 通用主将效果接口

- `SkillDefinition.commander_effect_specs`显式声明主将专属分支；默认空，旧定义行为不变。
  不用战法名称、静态描述字符串或战法ID猜测主将效果。
- `CommanderEffectPolicy.enabled(context, actor_id)`查询该武将的主将效果资格。
  默认真实主将拥有资格；有效`CommanderEffectRoleParams`可覆盖资格。
  物理`lineup_position`、目标选择、武将身份和provider槽位保持权威。
- 普通效果和专属分支共用一次准入、发动概率与目标选择，失败时两者都不执行。
  ACTIVE/ASSAULT专属伤害或恢复仅在资格有效时产生。
- 持续主将状态可预先安装为休眠状态，公共有效性adapter按**来源武将**资格决定效果，
  接受效果的单位无须是主将。这样PASSIVE早于FORMATION时无需重新发动或重复安装被动。
  普通与专属分支必须使用不同state_id，保证source/skill/slot/state身份可区分。
- 开场PASSIVE/COMMAND专属分支必须是持续状态；瞬时开场专属伤害/恢复需要新的时序合同，
  构造时直接拒绝，不静默执行。两个分支目前使用同一目标意图；独立目标/概率需要独立组件合同。
- 尚无带真实客户端主将分支的普通武将战法在此仓库注册；本次用显式测试战法验证通用接口。
  以后接入各具体武将战法时必须声明真实专属效果，不会仅凭资格标记自动补出未实现的效果。

新增公共能力：资格状态、查询policy及状态有效性adapter；扩展SkillDefinition的声明字段、
SkillResolver的可选policy与效果树组合；BattleSystems负责依赖注入。
复用TargetPrioritySkillResolver、EffectExecutor、AttributeSystem、DamageRateModifierProvider、
StateEffectivenessPolicy及所有既有冻结owner。

## 验证与保留边界

专项见[测试记录](qian_long_evidence/focused_tests.txt)，包含十级静态值逐项核对、
15%/5%分支、携带者三位置、五基础兵种、兵刃/谋略真实伤害管线、学习槽/disabled存在性、
属性快照保留、共享RNG和目标、开场状态资格切换、来源与接收者分离、移除资格、
阵亡清理、双方潜龙阵隔离、失败前无状态及RNG变化、引擎自动安装。
[架构检查](qian_long_evidence/architecture_tests.txt)、
[冻结审计](qian_long_evidence/frozen_owner_audit.json)、
[全量回归](qian_long_evidence/full_regression.txt)。

原始战报逐事件对照、当前客户端变化、净化规则和资格切换的公开状态事件微时序保持OPEN。
沿用阵法V1提供者阵亡移除；移除后资格恢复默认真实编队角色。
安装后仅改变formation runtime.enabled不会自动撤回持续状态，仍由已有生命周期owner管理。
通用接口完成和工程测试通过不等于所有武将主将效果已实现或玩法已冻结。

本地验证：潜龙阵及公共接口81项通过；含阵法同步专项83项通过；
架构及静态定义专项52项通过；全量 **2598 passed**；demo通过；
21个冻结核心文件哈希一致、D1对抗11项通过，青州兵审计通过。
新进程registry含7项，22040唯一解析为本模块SKILL。远端状态以PR与Actions为准。
