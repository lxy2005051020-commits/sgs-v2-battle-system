# Stage14 第三批：白毦兵 + 大戟士

状态：`BASELINE_FROZEN / MERGED_MAIN / CI_PASS`。
日期：2026-10-05。分支：`stage14-troop-batch-03`。

> Post-merge note：PR #48 已合并至 `main`，merge SHA `d9b890490596a6fe368fff103ae3bdf6a23670c5`，merged-main CI `37314228006 / SUCCESS`。20099 / 20125 的 bounded baseline 已由 `MC-STAGE14-TROOP-BATCH01-04-BASELINE-01` 冻结；细时序、lineage 等扩展问题继续 OPEN。下文旧的 stacked-PR 描述保留为历史记录。

## 来源与边界

`batch03/source_snapshot.json` 保留本地客户端文本 CSV 的 SHA-256、两个战法各十级
原记录、Runtime 基线、当前远端 Runtime / Research main SHA。实现采用满级文本
2009910 / 2012510；暂未扩展等级参数入口。本地提取文本不等于独立验证现行客户端。
身份、基础兵种克制与来源生命周期继承 Research 的
`MC-STAGE14-TROOP-FOUNDATION-01`，伤害/攻心/连击复用既有正式执行所有者。

## 战法拆分

| 项目 | 白毦兵 | 大戟士 |
|---|---|---|
| 身份 | TROOP / SPEAR -> BAI_ER_BING | TROOP / SPEAR -> DA_JI_SHI |
| Trigger | PRE_BATTLE 安装；每次物理普攻后的既有接缝 | 同左 |
| 发动概率 / 准备 | 追加伤害 45%；无准备 | 35%，张郃统领 40%；无准备 |
| Conditions | 来源有效、执行者存活、战斗未锁定终结、继承目标存活 | 来源有效、执行者存活、战斗未锁定终结、有合法敌军 |
| Target | 全队安装；追加伤害继承普攻重定向后的实际目标 | 全队安装；追加伤害随机敌军单体；连击只安装到张郃主将 |
| Effect Tree | 全队攻心 12% + 追加谋略伤害 110%（陈到主将 130%） | 全队武力 +14 + 追加兵刃伤害 122% + 张郃主将概率连击 45% |
| Status / Modifier | STRATEGY_LIFESTEAL、runtime_normal_attack_followup | 属性修饰、runtime_normal_attack_followup、COMBO 的概率参数子类 |
| 运行时状态 | StateRegistry 保存每友军监听器及原携带者来源；无全局可变数据 | 同左；连击 grant 仍归 ActionSystem，至多第二次普攻 |
| 组件是否足够 | 复用伤害/治疗/选目标所有者，扩展普攻后监听桥与目标继承入口 | 同左，补充概率连击 read adapter 与主将目标声明 |

统领条件延续前两批口径：队伍 `LineupPosition.COMMANDER` 的姓名匹配。
统领者与携带者可不同；陈到/张郃仅为副将不启用强化。
连击第二次物理普攻同样可产生追加伤害，但追加伤害自身不能开启普攻、突击或连击。

## 来源、数值与目标

战法携带者、监听器所有者、物理伤害执行者分开保存。监听器的 source_id / skill_id /
slot 指向真实携带者；伤害 source_id、公式兵力/属性、伤害归属与攻心恢复指向当前
普攻执行者。队友不伪造携带者的技能槽位；DamageEffect 保留来源状态及实例身份。

白毦兵的 1.10 / 1.30 为本批固定文本伤害率，智力与兵力影响通过现有谋略伤害基础
公式完成。没有未经确认地添加额外智力缩放公式；是否还存在“伤害率本身受智力影响”
的独立缩放及其数值时点，保留 OPEN，不能把本批结果称为战报校准公式。

白毦兵使用绑定目标入口：不创建 fresh TargetOperation、不重新抽目标、不重新应用
fresh ENEMY 筛选，支持援护实际受击者及混乱选中的友军。目标已死亡时跳过概率
检定，不转移至另一名敌军。继承结果使用 INHERITED provenance，但目前未补充
parent-normal-attack OperationLineage；需在独立触发合同中继续审查来源链。

大戟士复用现有 SkillResolver / TargetPolicy / TargetSystem 随机选单体。
目前该 fresh skill query 的权限及 TargetOperation actor 是原携带者，物理伤害执行者
在执行阶段单独绑定。Capture 等持有者相关选目标约束与队友触发的结合口径仍待
独立合同裁决，不能宣称已证明应由执行者或携带者接收这些约束。

## 生命周期与时序

全队安装无概率掷骰。来源禁用或威慑时，追加伤害与概率连击在 RNG 前拦截；威慑
到期后按现存监听器恢复，不重装、不补偿漏掉的触发。副将携带者死亡后，已挂载的
存活友军监听器可继续，遵循 independently-mounted 的基础生命周期口径。
该战法独立死亡样本仍待 Research 收口。

普攻触发桥组合冻结的 AssaultDispatchPort，先验证/消耗 authentic permit，再产出
效果，不修改 NormalAttackSystem、ActionSystem 或 ExecutionRightSystem。
当前检查点在普攻同步伤害、溅射、铁索、反击之后，连击检查点之前。
白毦兵“普攻后”和大戟士“普攻时”的更细顺序，规避/抵御阻断普攻时是否仍触发，
以及继承目标死亡时是否应消耗概率，尚无独立证据。当前行为明确继承既有接缝：
被 hit-prevention 提前截断的普攻不产生追加伤害。

张郃连击概率在当前行动的 grant 读取时检定一次；被冻结的 ActionSystem 与
NormalAttackSystem 继续拥有 grant 创建、消费和最多两次物理普攻的约束。
该概率检查点相对于行动许可的精细时序尚待战法合同验证。
主将致死造成终结锁定时，不再创建后续伤害或掷骰；最终清理由已有终结所有者完成。

## 通用扩展

- `NormalAttackFollowupPort` / `NormalAttackFollowupParams`：状态驱动的普攻后追加伤害桥。
- `ProbabilisticComboParams` / `ProbabilisticComboRuntime`：仅对概率参数子类启用 RNG，
  旧 ComboStateParams 保持原有读取行为；来源有效性委托已有 ProviderValidity。
- `SkillResolver.inherited_target_ids`：已有解析器接受绑定的单个目标，跳过 fresh 查询。
- `SkillTargetMode.TEAM_COMMANDER`：固定主将目标，无随机选目标。
- `TroopSkillConfig.requires_provider_slot` / `supplemental_definition_resolver`：在 mutation
  前解析附加定义并拒绝缺少 canonical slot 的监听器，安装仍由共享准入入口执行。
- `tests/__init__.py` 与 pytest 的 `pythonpath`：兼容已有 package 和裸模块两类跨测试
  导入，避免新工作区被 site-packages 的 tests 包遮蔽，不跳过任何测试。

两个独立战法模块导出 SKILL / CONFIG，沿用项目实际 TROOP_SKILL_REGISTRY；
没有添加另一套 register_skill 或自动发现框架。没有修改 frozen owner 清单、审计脚本
或伤害/治疗/终结权限。验证结果见 `batch03/VALIDATION.md`。
