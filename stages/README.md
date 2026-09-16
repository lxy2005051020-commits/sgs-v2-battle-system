# 阶段文件索引

每个阶段的设计、研究、证据、审计、冻结和实施材料统一存放在 `stages/stageN/`。

- [Stage 1：基础运行模型](stage1/README.md)
- [Stage 2：BattleSystem](stage2/README.md)
- [Stage 3：BattleState](stage3/README.md)
- [Stage 4：官方状态代表接入](stage4/README.md)
- [Stage 5：Effect](stage5/README.md)
- [Stage 6：Skill Runtime](stage6/README.md)
- [Stage 7：Trigger / Recovery](stage7/README.md)
- [Stage 8：Damage Pipeline — FROZEN](stage8/README.md)
- [Stage 9：Cross-Mechanism Runtime Orchestration — FROZEN](stage9/README.md)
- [Stage 10：Persistent State Runtime Integration — FROZEN / 已合入 main](stage10/README.md)
- [Stage 11：官方状态补全（一）— 规划中](stage11/README.md)
- [Stage 12：官方状态补全（二）— 规划中](stage12/README.md)

## 当前边界

```text
Stage 8  = FROZEN
Stage 9  = FROZEN
Stage 10 = FROZEN / MAIN INTEGRATION COMPLETE

Stage 11 = PLANNING / RESEARCH PREPARATION
Stage 12 = PLANNING ONLY
```

第十阶段正式主分支合入提交：

`30f623f9efed20b5a82044b51519db1af6da86d3`

## 当前路线

当前第十阶段后路线权威：

- [官方状态补全与战法接入总路线](../POST_STAGE10_STATE_COMPLETION_AND_SKILL_ROADMAP.md)
- [演示场景套件升级规划](../DEMO_SCENARIO_SUITE_ROADMAP.md)
- [Stage11 规划](stage11/STAGE11_PLANNING.md)
- [Stage12 规划](stage12/STAGE12_PLANNING.md)

旧的第九阶段后路线保留为历史记录，不再作为 Stage11+ 当前执行路线。

## 官方状态当前完成度

严格完成标准：

```text
机制研究冻结
+
运行时冻结到合同
```

当前：

```text
16 / 40 严格完成
24 / 40 待第十一、十二阶段补齐
```

第十一、十二阶段完成后，目标是正式达到：

```text
40 / 40 官方状态体系冻结
```

随后项目主线才进入战法正式接入。

共享源码位于 `sgs_v2/`，正式测试位于 `tests/`。
