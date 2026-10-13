# 已完成阵法统一同步

日期：2026-10-13；分支 `stage14/completed-formations-sync`。
基线：已合并武锋阵的origin/main `dfd5453a1991934d62e022fdb36ad3b65e82cff7`。
原始完成提交：八门金锁阵 `d6585de`、箕形阵 `1d82ee3`、三势阵 `8f252a8`。
原工作树、原始来源快照与既有测试记录保留，本次通过独立同步分支发布。

## 合并范围

| ID | 阵法 | 已实现范围 |
|---|---|---|
| 20066 | 锋矢阵 | Lv10；已有main接入 |
| 20025 | 八门金锁阵 | Lv1–10；用户指定智力缩放及发动时快照 |
| 20178 | 箕形阵 | Lv10；用户指定武力缩放 |
| 22012 | 三势阵 | Lv1–10；用户确认平局及旧效果清除规则 |
| 22031 | 武锋阵 | Lv10完整模型；低等级仅显式副将模式 |

本次新增注册八门、箕形、三势，原锋矢、武锋保持注册。没有将形一、潜龙、鱼鳞标为已实现。

八门/箕形复用一份OutgoingDamageReductionProvider；三势/武锋复用一份DamageRateModifierProvider。
RoleSplitRuleHookSystem继承PeriodicTeamSupportRuleHookSystem：先执行原普通状态批次，再执行对应的武锋奇偶支援和三势副将分配。两种driver按各自provider隔离，不覆盖对方钩子。
UnitRuntime同时保留faction与troop_aptitude可选字段。没有修改冻结DamageSystem、SkillResolver、RecoverySystem、TroopSystem、EffectExecutor、TriggerSystem、RuleHookSystem、BattleEngine或StateLifecycleSystem。

## 机制来源与未决项

每个战法原文、用户确认规则、公开组件树与模型假设分别见：

- [八门金锁阵](BA_MEN_JIN_SUO_ZHEN_INTEGRATION.md)
- [箕形阵](JI_XING_ZHEN_INTEGRATION.md)
- [三势阵](SAN_SHI_ZHEN_INTEGRATION.md)
- [武锋阵](WU_FENG_ZHEN_INTEGRATION.md)
- [锋矢阵](FENG_SHI_ZHEN_INTEGRATION.md)

沿用USER_SPECIFIED/USER_APPROVED模型边界，不升级为完整Gameplay实证冻结。
各阵法低等级公式、精细触发时序、死亡/净化交互等原有OPEN项继续保留。

## 本次验证

新进程canonical registry必须恰含20066、20025、20178、22012、22031。
五阵法原专项回归与跨阵法合并专项保存在
[focused_tests.txt](formation_sync_evidence/focused_tests.txt)。
跨阵法专项验证双方分别携带三势阵和武锋阵的驱动均执行、换回合互不清除对方贡献、
一方携带者阵亡不删除另一方driver。全量、demo与冻结审计见
[全量输出](formation_sync_evidence/full_regression.txt)、
[D1审计](formation_sync_evidence/stage13_d1_audit.json)、
[青州审计](formation_sync_evidence/qingzhou_audit.json)。
远端PR CI及merged-main CI需完成后才报告主线交付成功，旧工作树测试数不作为本次组合结果。

本次本地组合验证：五阵法专项及新增跨阵法专项 **211 passed**；全量 **2450 passed**；demo smoke PASS；Stage13-D1冻结Owner哈希与11项独立对抗审计PASS；青州兵独立兼容审计PASS；新进程registry唯一注册五项。
