# 鱼鳞阵合并前审计

2026-10-14；主线同步基线 `1ed7e7c6dc85be8a224d87c652a2db3b528ef6ea`。
状态：`USER_APPROVED_PARTIAL / COMMAND_ONLY / FULL_MODEL_FAIL_CLOSED / NOT_GAMEPLAY_FROZEN`。
审计为独立测试fixture、代码审阅和冻结owner哈希核对，不声称第二位人工审阅者参与。

## 审计范围与结论

本次仅接入十级副将固定统率提升（27.5至55），显式 `command_only=True`。
武力和统率对概率的缩放、治疗统率缩放按用户指令继续
`DEFERRED_BY_USER / NOT_IMPLEMENTED`；抵御和治疗受击分支均未启用。
默认完整模式在任何开场被动效果、状态安装或RNG消耗之前抛出 `NotImplementedError`。

- ID20836、等级原文、兵种限制核对保存的静态CSV和完整config；没有插值或猜测缩放。
- 单战法模块复用canonical `FormationSkillConfig`、TargetSystem、ApplyStateEffect、
  AttributeBonusParams、StateNode/ProviderNode及现有属性/状态生命周期。
- 主线雁行阵已有相同通用validator接口。本次合并复用该接口，保留雁行阵validator，
  不引入平行校验系统；原接入文档描述的新增接口属于旧分支历史。
- 同步雁行阵主线冲突仅为validator注释、注册数量和文档；两者代码和注册均保留。
  当前canonical registry含9个阵法定义，鱼鳞阵明确为部分接入。
- 来源携带者与接收副将区分明确；三个SkillSlot均验证；固定统率加法不随回合或
  后续属性变更按比例重算；正常移除和携带者阵亡通过既有owner清理。
- 不修改伤害、治疗、扣兵、状态生命周期、EventBus、RNG等冻结核心owner。
- 非法编队、定义篡改、重复安装、同队双阵法、非法阶段与默认完整模式均拒绝；
  对方合法阵法也不会在完整模式失败前先安装状态。
- 鱼鳞阵与雁行阵双方安装、来源和阵亡清理独立；不会产生鱼鳞抵御或急救状态。

未发现阻止本次授权部分范围合并的实现问题。此结论不将未接入受击分支或属性缩放
升级为已实现，也不作客户端机制实证冻结。

## 当前验证证据

- [专项及组合测试](yu_lin_evidence/merge_focused_tests.txt)：254项通过。
- [同步主线后的全量回归](yu_lin_evidence/merge_full_tests.txt)：2842项通过。
- [Stage13-D1冻结owner及运行时审计](yu_lin_evidence/merge_audit_stage13_d1.json)：PASS。
- [青州兵审计](yu_lin_evidence/merge_audit_qingzhou.json)：PASS。
- [雁行阵审计](yu_lin_evidence/merge_audit_yan_xing.json)：PASS。
- [demo](yu_lin_evidence/merge_demo_smoke.txt)：exit0。
- [独立进程注册核验](yu_lin_evidence/merge_registry_check.txt)：9定义，20836工厂等于SKILL。
- `git diff --check`通过；新增adversarial fixture见
  `tests/test_stage14_yu_lin_merge_audit.py`。

`yu_lin_evidence`中无`merge_`前缀的验证文件为2026-10-13原始分支快照，
其中8个注册定义和2772项全量测试计数是历史结果，不能替代本次同步后验证。
合并门禁：最新PR提交CI `completed/success`后合并，随后核对merged-main CI成功。
实际PR、merge SHA和CI链接以GitHub在线记录为准；本文件不预先声明合并完成。
