# 飞熊军合并前工程审计

日期：2026-10-12。PR：[#62](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/pull/62)。
被审计运行时代码提交：`2dbcbcd5a76645c9e4581c798bae6ec78d9004ca`，文件树：`c4370d3911cb1b644504ce443a18f23017f651fb`。
结论：**PASS / READY_TO_MERGE_AS_USER_SPECIFIED_MODEL**，未发现阻塞实现问题。
这是本次代码复核和自动化工程审计，不是另一位人工审计员或原始战报玩法冻结。

## 审计范围与结果

- 实际恢复只读取已结算TROOPS_RECOVERED.actual_recovery，按治疗提供者所属队伍统计；不重复读取汇总、请求值或溢出治疗。
- H/10在普通最终伤害后追加，每目标独立加相同值，不被奇谋或普通增减伤再次缩放；拦截门控仍有效。
- 两目标由SkillResolver一次选出，共享同一个快照；累计在执行伤害前消费，期间真实吸血恢复属于下一次。概率失败保留累计。
- 携带者提供战法，主将执行伤害并读取智力；不伪造主将技能槽位。状态有效性、提供者、执行权和战斗终结门控复用既有owner。
- 累计游标按战斗、状态实例及generation隔离；通用组件不绑定战法编号，不直接修改兵力或物理状态。
- 冻结owner源码哈希无漂移；原架构伤害生产入口与事件结算边界保持原有契约。
- 20247独立进程注册检查通过，当前注册兵种总数14。

## 重跑验证

| 检查 | 结果 |
|---|---|
| 全套pytest | 2192 passed，14.65秒 |
| Stage13-D1独立冻结owner与对抗审计 | PASS |
| 青州独立运行时审计及标准demo | PASS |
| 飞熊军真实准入及完整引擎回放 | PASS：恢复116/120，H1000各加100，下一快照200 |
| 注册检查 | PASS：20247 CONFIG/factory/SKILL一致 |
| 原发布提交PR CI | [SUCCESS](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/actions/runs/38213373227) |

本次审计后仅同步文档状态和本审计记录，不修改运行时代码或测试。最终PR head必须再通过CI，合并后检查merged-main CI。最终合并与CI实时状态以GitHub为准。

## 保留边界

用户指定公式、实际恢复口径和快照规则继续标注USER_SPECIFIED_FINAL_ADDITIVE_MODEL / NOT_GAMEPLAY_FROZEN。更细触发时序、提供者/状态生命周期、伤害被阻止时累计消费、敌军不足2人的显式异常及最终取整均保留既有开放边界；本次合并不把它们升级为游戏事实。完整规则见[接入说明](FEI_XIONG_JUN_INTEGRATION.md)。
