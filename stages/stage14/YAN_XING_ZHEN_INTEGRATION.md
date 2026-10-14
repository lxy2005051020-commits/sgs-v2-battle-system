# 雁行阵接入记录

2026-10-14；独立分支 `stage14/yan-xing-zhen`；远端main基线
`4357a6b0a46f379945193c0e203a1373dd1c6e03`（本次通过OpenSSL后端fetch核对）。
状态：`USER_APPROVED_BASE_VALUE_MODEL / ATTRIBUTE_SCALING_DEFERRED / BOUNDED_TRANSFER / NOT_GAMEPLAY_FROZEN`。
本记录为独立分支实现，不表示已合入main或通过远端CI。

## 用户裁决与来源

用户明确选择“暂时按基础概率和基础偷取量运行”，并批准：每回合开始执行；
实时最低统率并列按主将→副将1→副将2；负面状态按种类抽取1–2种；效果本回合结束过期。
携带者统率对三分支概率及偷取量的缩放继续留空，未应用、未拟合、未冻结。

客户端静态ID `20862`，阵法，`arm_limit={}`；适用五种基础兵种。
来源为2026-08-08静态快照：[十级原始行与HTML](yan_xing_evidence/static_levels.csv)、
[原始配置与源文件SHA256](yan_xing_evidence/source_manifest.json)。这不是当前客户端机制实证。

| 等级 | 三分支各自基础概率 | 每名敌军基础偷取统率 |
|---|---|---|
| 1 | 17.5% | 5 |
| 2 | 19.4% | 5.6 |
| 3 | 21.4% | 6.1 |
| 4 | 23.3% | 6.7 |
| 5 | 25.3% | 7.2 |
| 6 | 27.2% | 7.8 |
| 7 | 29.2% | 8.3 |
| 8 | 31.1% | 8.9 |
| 9 | 33.1% | 9.4 |
| 10 | 35% | 10 |

## 正式入口与组件树

```python
from sgs_v2.battle_core import create_yan_xing_zhen_runtime, SkillSlot
runtime = create_yan_xing_zhen_runtime("holder", level=10, slot=SkillSlot.LEARNED_1)
```

```text
FORMATION_SKILL_REGISTRY[20862] / create_yan_xing_zhen_definition / SKILL
  PRE_BATTLE / 100%安装 / 无准备回合 / 每队唯一阵法
  FormationSkillConfig.validator -> canonical定义与完整存活三人编队
  ApplyStateEffect -> RoundTeamTransferParams(probability, attribute_amount)
  StateNode -> ProviderNode（携带者 / ID / 槽位）
  RoundStartHook -> RoundTeamTransferSupport（有效driver每回合仅一次）
    三次独立chance，先判定三分支，再消耗选人随机数
    分支1：随机敌军 + 随机友军 -> 静态受到伤害降低效果转移
    分支2：友军群体 -> 随机抽1–2种负面状态 -> 同一随机敌军
    分支3：实时最低统率友军 + 存活敌军全体 -> 加法属性修饰
  StateTransferSupport -> StateCandidate / StateApplicationCoordinator
    目标免疫/冲突拒绝时保留原状态
    scoped removal permit -> StateRemovalCoordinator -> 既有Lifecycle
  既有属性、伤害、生命周期、EffectExecutor、到期与阵亡清理owner
```

新增公共组件 `RoundTeamTransferSupport`、`StateTransferSupport`及其强类型参数和hook适配器；
扩展已有 `PriorityTargetSystem.lowest_attribute_units`，按实时属性及编队顺序排序；
为既有阵法准入配置补充可选纯校验器，复用于全局开场预检和单阵法安装。
沿用仓库canonical注册方式，无另一套自动扫描器、注册表或Engine特殊分支。

统率偷取每名存活且通过目标准入的敌军减去基础量，选中的友军增加这些量之和。
满级3名敌军时分别-10，受益者+30；不会只加10，也不按携带者统率再放缩。
不改基础属性，不加额外取整或下限。当前回合结束全部还原。

## 转移支持与明确边界

已支持：`IncomingDamageReductionParams`（保留伤害类型）；静态 `DamageRateParams`；
`FengShiZhenModifierParams`中对应符号的减益或减伤维度（转入通用伤害修饰）；
普通负面属性加法修饰、静态造成伤害降低；Empty/TimedFlag/Disarm/Stun普通控制参数。
混合伤害修饰只移动对应维度，剩余维度保留原来源、原期限和原依赖。

原实例ID、generation、原来源武将/战法/槽位与新实例/目标均在转移记录中保留；
新的转移效果以雁行阵携带者为provider。driver及转移效果在provider不可用时失效，
携带者阵亡走既有清理。只迁移当前有效状态；无效果可转移时不创建状态。

以下尚未实装，命中对应schema时明确 `NotImplementedError`，不会伪造拷贝：

- 持续伤害及其冻结来源、伤害快照、关联子状态；
- 嘲讽、挑拨、捕获、铁索连环、伪报、威慑等带专用关联或contract参数的转移；
- 武锋阵按同次战法选人绑定的实时减伤；形一阵等回合动态曲线的转移；
- 未在以上清单中的特殊参数、bounded叠层属性。
- 有下游状态依赖原实例的转移：关联重绑定规则尚未确认，施加新状态前明确报错。

合并前审计补充：动态曲线按当前回合实际符号分类；没有减伤或减益时不进入相应转移。
通用转移入口拒绝不含对应维度的状态，不会删除无关增益。详见
[合并前审计及独立对抗测试](YAN_XING_ZHEN_MERGE_AUDIT.md)。

状态抽样中的种类目前按canonical `state_id`分组；选中种类的友军有效实例按编队顺序依次处理。
1或2种等概率，在可选种类不足时截取；该抽样规则属于暂定工程模型。
同种类多个来源转入同一目标时，继续服从既有冲突政策；拒绝或
`UNSUPPORTED_BOUNDARY`明确记入history，原状态保持。不会强行叠加或删除未转移成功的状态。
因此当前实现是带边界的三分支接入，并非任意状态全覆盖。

## 验证与交付状态

[验证汇总](yan_xing_evidence/verification_summary.txt)保留专项、全量、清洁进程注册核验、
三种子完整引擎演示、Stage13-D1及青州兵独立审计结果。
核心冻结owner保持哈希一致；工程测试和用户暂定模型不等同于Gameplay实证冻结。
远端发布/PR/合并应作为后续独立步骤核验，本次不提前宣称完成。
