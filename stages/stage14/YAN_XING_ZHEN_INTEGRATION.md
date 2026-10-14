# 雁行阵接入记录

2026-10-14；本次基线main `3c23534ecd33ff8a72160bf106e4838daa6cdce2`。
状态：`USER_APPROVED_COMPLETE_TRANSFER_MODEL / ATTRIBUTE_SCALING_DEFERRED / NOT_GAMEPLAY_FROZEN`。
本记录替换PR74的bounded转移范围；旧版来源、测试和审计保留在原证据目录及Git历史。

## 已确认的暂定规则

用户要求：“除了属性放缩部分的，其他全部接入”。随后明确批准：

- 保留原效果数值和已冻结伤害快照；转移后的来源为雁行阵携带者。
- 嘲讽、挑拨指向携带者；威慑通过既有组件在新目标的合法战法中重新绑定。
- 同类状态覆盖/刷新，不叠加，持续到本回合结束；不同属性、发动率类型/槽位、伤害类型分开保留。
- 动态减伤按转移瞬间原目标的属性/当前回合取值，转移后固定到本回合结束。
  武锋阵仅移动减伤部分，原目标的优先选人机制保留。

原先确认的回合开始触发、三个分支独立判定、实时最低统率、
并列按主将→副将1→副将2、负面状态按种类抽1–2种继续保持。
多个同类来源按编队/实例的确定顺序转移，后转入的覆盖先转入的，不累计数值。

## 唯一暂缓的功能

**携带者属性放缩仍未实现：**

1. 携带者统率对三个分支概率的放缩及其读取时点。
2. 携带者统率对偷取量的放缩及其读取时点。

继续使用静态等级基础值；满级每种分支35%，每名敌军偷取10统率。
没有补入推测公式，也没有将暂定转移模型标记为客户端实证冻结。

## 完整接入范围

| 分支/能力 | 当前行为 |
|---|---|
| 静态受到伤害降低 | 移动指定伤害类型及负号修饰；不带走无关维度 |
| 持续伤害 | 灼烧、水攻、中毒、溃逃、沙暴、叛逃均可迁移；保留源兵力/属性/等级/士气/进阶/修饰/会心快照和系数 |
| 普通负面状态 | 计穷、缴械、混乱、虚弱、禁疗、震慑、遇袭及负面属性修饰等 |
| 关系型负面状态 | 嘲讽、挑拨、捕获、铁索连环、伪报、破坏、威慑；复用正式准入和机制绑定 |
| 动态减伤 | 武锋阵取实时原目标属性快照；形一阵等曲线取当前回合值；转入固定一回合减伤 |
| 关联/依赖 | 显式StateNode边、参数内parent/prerequisite引用及持续伤害关联子状态递归迁移、拓扑重绑定 |
| 同类覆盖 | 同类同维度覆盖；保留不同属性/伤害类型和无关正负修饰；覆盖前先通过目标免疫准入 |
| 统率偷取 | 存活且合法敌军各减基础量，最低统率友军加总和；回合结束恢复 |

读取友军负面状态属于团队状态查询，不把友军作为新增益的施加目标；
因此被捕获的友军仍可提供待转移状态。新状态的敌军接收目标继续通过正式目标/免疫政策。
目标免疫、没有合法战法可供威慑绑定、目标死亡或来源失效属于明确的准入/执行结果，
不会删除未成功转移的原状态，也不属于缺少转移实现。

## 来源、身份与生命周期

静态客户端ID `20862`，阵法，五基础兵种；十级原文、HTML、完整配置和SHA256继续保存在
[原始静态行](yan_xing_evidence/static_levels.csv)及[原始来源清单](yan_xing_evidence/source_manifest.json)。
这些是2026-08-08静态来源，不代表新客户端实证。

持续伤害原始快照不重算；新来源武将/战法/槽位、新physical ID和generation由现有组件建立。
历史伤害来源随新代际重绑定，原来源与旧代际另记在transfer history/原移除事件。
关联子状态保留原系数及快照，绑定到新的父状态；不额外制造一次新的施加反应。
原状态有未转移的维度时，保留原physical ID、来源、期限及依赖，只删除对应维度。

转移后的状态统一使用当前回合结束的typed期限。实际引擎的到期协调同时完成物理移除、
依赖清理和来源有效性恢复；底层Lifecycle物理接口本身不替代该协调入口。
携带者死亡或不可用继续按已批准的阵法来源规则失效/清理；跨队及来源槽位保持隔离。
重复消费已移除的来源或旧代际不重放效果，也不消耗绑定RNG。

## 组件树

```text
FORMATION_SKILL_REGISTRY[20862] / SkillDefinition / PRE_BATTLE
  RoundTeamTransferParams -> RoundStartHook / 一回合一次
    3个独立基础概率
    TargetSystem / SkillTargetPolicy
    StateTransferSupport
      StateCandidate -> StateAdmissionPolicy
      TransferConflictPolicy（只对明确TRANSFER操作启用覆盖）
      StateApplicationCoordinator -> TransferStateLifecycle参数准备
        转移伤害快照绑定新identity -> canonical Lifecycle物理提交
      StateRemovalCoordinator / TransferRemovalPolicy（操作内限定实例）
      原关联子状态和StateNode依赖拓扑迁移
      Typed ROUND_END期限 / 原Engine到期协调
    AttributeSystem最低统率 -> 成对准入 -> 偷取守恒
```

新增/扩展公共组件：`state_transfer_support.py`、`state_transfer_policy.py`、
`transferred_potency.py`；BattleSystems仅配置组合。没有修改冻结的Engine、
伤害/恢复/兵力、StateApplication、StateRemoval、StateLifecycle、RNG及TargetSystem源文件。
普通状态的重施、免疫、净化和威慑选择仍沿用原有合同；转移例外仅限明确的操作上下文。

## 验证

[完成审计](YAN_XING_ZHEN_COMPLETION_AUDIT.md)记录独立测试、全量回归、冻结owner哈希、
真实持续伤害与控制绑定、跨状态依赖、完整战斗及确定性回放。
当前工程模型补齐了上述非属性放缩范围；客户端精细微时序仍需实证验证。
GitHub发布/PR/main合并/CI状态以实际结果为准，不预写成功。

发动率降低（含有界叠层来源）也参与负面转移：保留当前单个效果数值，转入后按类型和槽位覆盖，正面发动率加成及其他槽位分别保留。
