# 阶段文件索引

每个阶段的设计、Prompt、证据、审计和研究材料统一存放在 `stages/stageN/`。

- [Stage 1：基础运行模型](stage1/README.md)
- [Stage 2：BattleSystem](stage2/README.md)
- [Stage 3：BattleState](stage3/README.md)
- [Stage 4：官方状态代表接入](stage4/README.md)
- [Stage 5：Effect](stage5/README.md)
- [Stage 6：Skill Runtime](stage6/README.md)
- [Stage 7：Trigger / Recovery](stage7/README.md)
- [Stage 8：Damage Pipeline — FROZEN](stage8/README.md)
- [Stage 9：Cross-Mechanism Runtime Orchestration — FROZEN](stage9/README.md)
- [Stage 10：Persistent State Runtime Integration — RESEARCH / DESIGN](stage10/README.md)

```text
Stage 8 = FROZEN
Formal Stage8 Reopen = NO
Stage 9 = FROZEN
Stage 10 = RESEARCH / DESIGN
Stage10 Production Implementation = NOT AUTHORIZED
```

Stage 9 final authorities：

- [Final Audit](stage9/STAGE9_FINAL_AUDIT.md)
- [Freeze Record](stage9/STAGE9_FREEZE_RECORD.md)
- [Audited Build Prompt](stage9/STAGE9_BUILD_PROMPT.md)

Post-Stage9 当前路线：

- [Research & Runtime Integration Roadmap](../POST_STAGE9_RESEARCH_AND_INTEGRATION_ROADMAP.md)
- [Stage10 Research Scope](stage10/STAGE10_RESEARCH_SCOPE.md)

当前状态完善计划采用严格完成口径：

```text
Research FROZEN
+
Runtime FROZEN TO CONTRACT
```

旧 Stage 中已有代表行为，不自动表示对应官方状态机制已经彻底完成。

共享源码保留在 `sgs_v2/`，运行测试保留在 `tests/`。当前状态以 [PROJECT_STATUS.md](../PROJECT_STATUS.md)、Post-Stage9 roadmap 与各阶段 final authority 为准。
