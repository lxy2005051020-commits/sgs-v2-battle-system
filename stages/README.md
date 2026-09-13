# 阶段文件索引

每个阶段的设计、Prompt、证据、审计和研究材料统一存放在 `stages/stageN/`。

- [Stage 1：基础运行模型](stage1/README.md)
- [Stage 2：BattleSystem](stage2/README.md)
- [Stage 3：BattleState](stage3/README.md)
- [Stage 4：官方状态接入](stage4/README.md)
- [Stage 5：Effect](stage5/README.md)
- [Stage 6：Skill Runtime](stage6/README.md)
- [Stage 7：Trigger / Recovery](stage7/README.md)
- [Stage 8：Damage Pipeline — FROZEN](stage8/README.md)
- [Stage 9：Cross-Mechanism Runtime Orchestration — BUILD PROMPT AUDIT FAILED / REPAIR REQUIRED](stage9/README.md)

```text
Stage 8 = FROZEN
Formal Stage8 Reopen = NO
Stage 9 = wraps / coordinates / derives around Stage8 seams
Stage 9 does NOT replace the Stage8 Damage Pipeline
```

Stage 9 implementation design authority 已冻结并经 Freeze Audit 验证。Build Prompt 已完成编写并完成首轮审计，但审计结论为 `FAIL — BUILD PROMPT REPAIR REQUIRED`。Production implementation 仍未授权。

当前下一步：

```text
Stage9 Build Prompt Repair
```

共享源码保留在 `sgs_v2/`，运行测试保留在 `tests/`。阶段状态以 [PROJECT_STATUS.md](../PROJECT_STATUS.md)、对应阶段 current authority 与 Stage 9 authority map 为准。
