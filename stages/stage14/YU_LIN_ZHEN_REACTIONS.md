# 鱼鳞阵受击分支接入

2026-10-14；分支 `stage14/yu-lin-reactions`；Runtime基线
`6b97b86aab597c73978b11c9118b7b227e09d654`（PR75已合并的仅统率版本）。
状态：`USER_APPROVED_BASE_VALUE_MODEL / ATTRIBUTE_SCALING_DEFERRED / NOT_GAMEPLAY_FROZEN`。

用户要求继续实现其余复杂机制，并确认：“携带者 零伤害触发,这些你可以去研究仓库中获取信息”。
既有“武力和统率加成暂缓”继续有效。默认入口现在运行基础值受击模型，
`command_only=True`仍可用于只启用副将统率。

## 行为

- Lv1–10副将固定统率提升保持原静态十级值；满级两名副将各+55。
- 第1–3回合，两名真实副将每次合格受击独立检定基础概率，成功获得1次抵御。
  满级25%，无每回合次数限制；同一个damage instance在同一driver generation中仅判定一次。
- 第4回合不触发上述抵御或治疗分支。此前生成且未消耗的抵御继续保留。
- 第5回合起，真实主将每次合格受击独立检定同等级基础概率；成功后获得基础治疗。
  满级概率25%、治疗率30%；来源为携带者在该反应时的当前兵力，属性项置0，
  通过既有TreatmentFormulaSystem与RecoverEffect/RecoverySystem计算和结算。
  不是直接恢复携带者兵力的30%；伤兵、禁疗和恢复修饰由正式恢复管线处理。
- 携带者可以在三个位置任意一处；来源槽位与受击者身份分别追踪。
- 抵御、虚弱、正常结算等零损失命中均有机会；规避未命中无机会。
  普攻、主动/指挥、突击、持续伤害、反击和群攻的合格aftermath均可进入；
  反馈、分担、分配接收端按已有ReactionPermissionPolicy排除。
- 已有抵御时新施加不叠加、不覆盖、不刷新；旧抵御在该次伤害中耗尽后，
  同次零损失aftermath可以重新获得1次抵御，供后续伤害消费。
- 暂停/失效的driver、死亡来源、死亡目标、战斗结束或finalization latch不消耗新概率RNG。
  携带者阵亡继续按已批准的阵法清理规则移除所属效果，包含新生成的抵御。

## 研究依据与工程边界

研究主线核对为 `d9d20e16c85355d7349bbb6df2b1b148d44292a4`。
固定提交合同副本与哈希见[来源清单](yu_lin_reaction_evidence/source_manifest.json)。

- [抵御正式合同](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/d9d20e16c85355d7349bbb6df2b1b148d44292a4/states/functional/resistance/MECHANISM_CONTRACT.md)
  §1/§10冻结已有抵御时不叠加、不覆盖、不刷新；§2/§5按独立伤害实例消费；
  §9说明持续时间由具体来源定义，不统一写死。
- [急救正式合同](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/d9d20e16c85355d7349bbb6df2b1b148d44292a4/states/persistent/first_aid/MECHANISM_CONTRACT.md)
  §3给出零损失命中资格和未命中排除。本次只复用共享受击资格与恢复owner，
  不给鱼鳞阵安装官方急救状态，避免和草船/陷阵营等发生急救单槽覆盖。
- 鱼鳞阵原始静态描述、全部等级值继续使用原证据目录，未插值。

研究仓库尚无鱼鳞阵专项定本，以下明确属于工程模型而非鱼鳞实证结论：

1. 原文未规定单次抵御持续时限，当前保持至消费、拥有者死亡、阵法携带者死亡或战斗结束；
   不把前3回合产生窗口误作已产生抵御的统一到期时间。
2. 新支援adapter在既有先登属性反应及急救aftermath之后执行；携带者兵力在此时读取。
   与急救、其他反应并发时的精细先后顺序尚待专项战报验证。
3. 携带者阵亡移除抵御沿用项目先前用户批准的阵法来源清理规则。
   通用抵御合同的来源死亡可保留规则未被改写；本模型的阵法政策具有独立用户授权。
4. 受击来源资格复用当前公共ReactionPermissionPolicy，无新拓扑扩张。
5. 主将武力/统率概率缩放、治疗统率缩放及其属性读取时点继续
   `DEFERRED_BY_USER / NOT_IMPLEMENTED`。

## 组件树与文件

```text
FormationSkillConfig[20836] / PRE_BATTLE
  canonical runtime + complete living lineup
  ApplyStateEffect -> 两副将 AttributeBonusParams(defense, exact_level_bonus)
  默认基础值模式:
    两副将 AfterDamageSupportParams(probability, rounds 1..3,
      ApplyStateSkillEffectSpec(barrier, ResistanceStateParams(1)), reject_existing_state=True)
    主将 AfterDamageSupportParams(probability, rounds 5.., recovery_rate)
    drivers: StateNode -> ProviderNode
  DamageAftermathPort -> 既有aftermath -> AfterDamageSupportPort
    hit/permission/window/alive/provider/effectiveness/duplicate gates -> 一次概率
    成功: ApplyStateEffect(barrier) 或 TreatmentFormulaSystem -> RecoverEffect
    状态冲突/伤害免除/抵御消费/治疗预防/扣兵/阵亡/结束: 全部既有owner
```

新增公共组件为 `after_damage_support.py`，不引用鱼鳞阵名称或ID；BattleSystems仅组合端口。
战法模块仅配置效果树；原统率测试更新默认模式合同，新增受击行为及通用参数测试。
源追踪和去重在每场context metadata中维护，无全局可变状态。
未修改冻结伤害、扣兵、恢复、状态生命周期、execution-right或finalization owner。

## 验证

专项与既有受击管线回归314项通过；全量2900项通过。审计过程及保留边界见
[受击分支合并审计](YU_LIN_ZHEN_REACTIONS_AUDIT.md)。

见[专项记录](yu_lin_reaction_evidence/focused_tests.txt)、
[全量记录](yu_lin_reaction_evidence/full_tests.txt)、
[四个确定性种子完整引擎验证](yu_lin_reaction_evidence/source_manifest.json)，
以及同目录的Stage13-D1、青州兵、雁行阵审计和demo。
覆盖等级数值、主副将/回合边界、各种零损失、重复事实、跨generation/战斗隔离、
全体SourceType门控、真实DamageEffect与普攻抵御消费/重获、携带者来源和三个槽位、
阵亡/disabled、禁疗/受治疗修饰/满兵概率、引擎自动运行。
工程回归不能关闭本节列明的鱼鳞专项实证边界。发布与main状态以GitHub实际PR记录为准。
