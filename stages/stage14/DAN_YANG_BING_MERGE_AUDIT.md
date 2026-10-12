# 丹阳兵合并审计

日期：2026-10-12。发布入口：[PR #63](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/pull/63)。
主线基线：`f189c8450b75ab380ecd622ff47df0aa0d05c9fa`。
运行时代码：`4039474950007855621243e58a6f39c1015265cb`。
结论：**PRE_MERGE_AUDIT_PASS / NO_BLOCKING_FINDINGS**。

本次为代码审计、追加独立测试文件及既有冻结检查，不是第二名人工审查者的审批。审计提交仅增加测试、审计证据和文档，不变更已审计运行时代码。

## 审计结果

| 项目 | 结果 |
|---|---|
| 生产兵种注册、盾兵身份转换、全体统率+36 | PASS |
| 用户确认生成比例1.0；陶谦判定使用主将 | PASS |
| 上一回合实际兵刃扣兵、排除谋略/敌方/直接扣兵 | PASS |
| 共用兵池、叠加、衰减、防重复、容量耗尽 | PASS |
| 状态抑制/恢复与战斗结束清理 | PASS |
| 完整EffectExecutor/伤害许可/扣兵链路 | PASS |
| 已消费许可重放无池量/扣兵/事件副作用 | PASS |
| 伤兵及实际伤害归因按抵挡后扣兵计算 | PASS |
| 分担/分配目标段抵挡，参与者直接扣兵不抵挡 | PASS |
| 携带副将阵亡后，存活队友保留既有兵池与统率 | PASS，继承既有DEATH-E提供者规则 |
| 兵池状态移除后不再生成或抵挡 | PASS |
| 生成、衰减、消耗逐笔账本守恒且非负 | PASS |
| 十进制36%取整边界 | PASS |
| Stage13 D1冻结owner哈希及对抗脚本 | PASS |

## 验证证据

- 原丹阳兵专项18 passed。
- 新增`tests/test_stage14_dan_yang_bing_merge_audit.py`：9 passed。
- 全量2219 passed，0 failed。
- `scripts/audit_stage13_d1.py`：冻结owner全部匹配，11项对抗测试通过，JSON verdict PASS。
- `demo.py`通过；全新进程注册表20245解析正确，兵种共15项。
- PR初始4039474提交的两项GitHub tests检查均SUCCESS；审计提交与合并main的CI在发布时另外核验，不以旧CI结果替代。

## 保留边界

用户只明确确认了生成比例1.0；共享范围、实际扣兵统计、衰减先于生成、向下取整、抵挡在分担/分配目标段之后及客户端ID仍需原始战报核验。
上述选择已在[接入说明](DAN_YANG_BING_INTEGRATION.md)及模块注释中披露。
合并只接受当前可运行模型，状态仍为`RUNTIME_INTEGRATED / USER_CONFIRMED_GENERATION_RATIO / GAMEPLAY_DETAILS_OPEN`，不计入玩法实证冻结。
