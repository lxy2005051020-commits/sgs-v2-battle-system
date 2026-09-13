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
- [Stage 9：Contract Closure / Design Admission Ready](stage9/README.md)

```text
Stage 8 = FROZEN
Formal Stage8 Reopen = NO
Stage 9 = wraps / coordinates / derives around Stage8 seams
Stage 9 does NOT replace the Stage8 Damage Pipeline
```

Stage 9 当前仍处于合同闭环与文档封口阶段。`STAGE9.md` 尚未创建；下一步是 Global Cross-Mechanism Final Audit，只有 final audit 通过后才允许正式编写 Stage 9 implementation design authority。

共享源码保留在 `sgs_v2/`，运行测试保留在 `tests/`。阶段状态以 [PROJECT_STATUS.md](../PROJECT_STATUS.md)、对应阶段 current authority 与 Stage 9 authority map 为准。
