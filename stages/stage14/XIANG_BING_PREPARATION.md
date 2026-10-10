# 象兵接入准备清单

更新日期：2026-10-11。

状态：**DEFERRED / PREPARATION ONLY（暂缓接入，仅维护清单）**。

用户决定暂时放置象兵，不继续研究、设计或实现。象兵尚未实现、尚未注册，不计入已接入兵种数量。本清单不构成 Research 冻结合同或实现授权。

## 基线与接口缺口

本次核查 Battle main 基线为 `e3e4ffc1247289f8a4787fff3548f784d20f76a0`，对应 [CI](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/actions/runs/37358803541) 已通过。该记录仅是准备阶段基线，不代表象兵已运行。

当前兵种模块可参考 `SkillDefinition`、`TroopSkillConfig`、`SKILL`、`CONFIG`，并复用 PRE_BATTLE 准入。候选模块位置为 `sgs_v2/battle_core/troop_skills/xiang_bing.py`，目前未创建。

现有 `DirectTroopLossResolver` 仅接受分担、分配两类直接兵损，`SourceType` 尚无延后结算身份。象兵需要先设计伤害拆分、债务保存和到期扣兵的通用接口；不能伪装为分担、分配或持续伤害绕过校验，也不能在战法模块直接修改兵力。

代码依据：[operation_identity.py](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/blob/e3e4ffc1247289f8a4787fff3548f784d20f76a0/sgs_v2/battle_core/operation_identity.py)、[direct_troop_loss_system.py](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/blob/e3e4ffc1247289f8a4787fff3548f784d20f76a0/sgs_v2/battle_core/direct_troop_loss_system.py)。

## 恢复前的待办

- [ ] 核实正式战法原文、版本、编号及各等级参数；不得凭旧示例确定比例和结算次数。
- [ ] 手动检查至少 5 份代表性原始战报，保存原始事件顺序、JSON Pointer、输入哈希和缺失数据标记；不强行配对债务。
- [ ] 确认延后比例、是否另有减伤、统领加成及属性读取时点。
- [ ] 确认结算时钟、当回合是否计入、分期比例、取整顺序与余数结清规则。
- [ ] 确认普攻、战法、反击、持续伤害及分担/分配等来源适用范围与结算顺序。
- [ ] 确认灼烧交互、概率、随机作用域、持续时间和净化/免疫边界。
- [ ] 确认效果提供者死亡、受击者死亡、暂时失效、治疗、伤兵和战斗提前结束时债务的处理。
- [ ] 确认攻击者、提供者、执行者、伤害信用和原始伤害实例的归因，以及吸血、反应和统计的触发边界。
- [ ] 建立证据限定的 Research 合同；未关闭问题保持 OPEN，暂定模型需另有明确授权。
- [ ] 建立 Runtime requirement map，明确受击拆分、债务存储、时钟、扣兵、事件、伤兵与死亡清理的 owner。
- [ ] 对缺失通用接口进行设计审计，再实现战法；不得隐式修改冻结核心语义。
- [ ] 恢复实现后验证债务守恒、目标隔离、取整、禁止重复修饰/递归入池及生命周期边界；完成相关回归、全套测试、demo、独立审计、PR CI 和 merged-main CI。

## 同步约定

本文件 `stages/stage14/XIANG_BING_PREPARATION.md` 为准备清单的 GitHub 维护入口，本地清单与本文件内容一致。后续明确恢复接入或提供新资料时，更新本清单并同步远端，保留证据来源和 OPEN 边界。

当前只发布和同步准备清单；不创建后台定时任务，不启动象兵实现。项目状态导航如后续更新，应引用本清单并保留暂缓状态，不增加已接入计数。
