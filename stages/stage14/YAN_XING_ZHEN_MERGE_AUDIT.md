# 雁行阵合并前审计

2026-10-14；[PR #74](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/pull/74)。
main基线 `4357a6b0a46f379945193c0e203a1373dd1c6e03`；
首次发布head `fb4f146841f85a8efb40aa999a92215f28c9babe`。
发布文件树 `484ca3d12d5e79e1234edae1fa565405625ffe29` 与本地实现提交完全一致。

## 方法与结论

本代理逐项复核代码和冻结owner，另建不使用原专项fixture的独立对抗测试。
这是自动化工程审计，不是第二位人工审查者，也不是客户端战报实证验证。

初始实现经审计发现动态伤害修饰分类未按实际回合读取：无减伤时可能误触发复杂转移报错，
后续实际出现增伤时又可能漏掉负面候选。本次改为读取既有 `rates_at(round_no)` 的结果；
真正需要转移动态效果时仍保持缺失合同报错，不补造动态转移规则。

同时补强两处公共边界：通用转移入口先确认对应可转移维度，避免删除无关增益；
原状态存在下游依赖时，在任何转移写操作前明确拒绝，避免拆分重建后断开关联状态。
属性缩放与既有复杂快照/关系转移未实装范围保持原声明。

审计修复后，本地结论为 **PASS（在声明的bounded base-value范围内）**。
状态施加、移除、生命周期、伤害、属性读取、选人与RNG继续使用既有owner；
不修改冻结核心或增加Engine战法ID分支。

## 验证

- [独立对抗测试](../../tests/test_stage14_yan_xing_merge_audit.py)：10项通过。
  覆盖动态分类四回合、无减伤曲线跳过、真实动态转移报错且无变更、
  下游依赖拒绝、混合维度剩余期限与原依赖、受限移除授权、不含转移维度的增益保护。
- 原专项及组合：56项通过；合并前新增10项；最终全量 **2669 passed**（67.69秒），
  见[最终回归输出](yan_xing_evidence/merge_full_tests.txt)。
- [独立基线owner/结构审计](yan_xing_evidence/merge_owner_audit.json)：25项PASS。
  Engine、Shared Foundation状态施加/移除、生命周期、伤害/恢复、选人/RNG与基线哈希一致。
- Stage13-D1冻结审计及11项对抗测试、青州兵独立审计均PASS，来源文件SHA256匹配。
- 三种子7/41/127完整8回合演示PASS，[结果](yan_xing_evidence/merge_demo_runs.json)。

首次发布head的[PR CI 38522015607](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/actions/runs/38522015607)
已 `completed/success`。本次审计补充head须通过自身PR CI后才可合并；
main合并及merged-main CI以GitHub实际状态核验，不在合并前预写成功。

## 保留边界

`USER_APPROVED_BASE_VALUE_MODEL / ATTRIBUTE_SCALING_DEFERRED / BOUNDED_TRANSFER / NOT_GAMEPLAY_FROZEN`。
携带者统率对概率、偷取量的缩放仍未执行；复杂快照、关联状态、动态减伤的转移仍报错。
目标免疫、来源移除保护及同类冲突继续服从canonical政策；失败时保留源状态并记录结果。
这些未实装分支不能被解读为雁行阵任意状态全覆盖或Gameplay实证冻结。
