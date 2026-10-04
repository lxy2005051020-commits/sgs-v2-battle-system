# Stages / 项目阶段索引

本目录只保留当前设计/冻结权威、必要兼容记录、最终审计和当前阶段治理材料。已被最终权威取代的 authoring、round-by-round repair、临时 research mirror 与 implementation progress 报告已从当前树移除；历史仍可从 Git history 追溯。

## 阶段导航

- [Stage 1](stage1/README.md)
- [Stage 2](stage2/README.md)
- [Stage 3](stage3/README.md)
- [Stage 4](stage4/README.md)
- [Stage 5](stage5/README.md)
- [Stage 6](stage6/README.md)
- [Stage 7](stage7/README.md)
- [Stage 8 — FROZEN](stage8/README.md)
- [Stage 9 — FROZEN](stage9/README.md)
- [Stage 10 — FROZEN](stage10/README.md)
- [Stage 11 — FROZEN](stage11/README.md)
- [Stage 12 — FROZEN / COMPLETE](stage12/README.md)
- [Stage 13 — ACTIVE](stage13/README.md)

## 当前统一状态

```text
Official States            = 40
Research FROZEN            = 40 / 40
Runtime FROZEN TO CONTRACT = 40 / 40
Strict Complete            = 40 / 40

Stage12                    = COMPLETE
Stage13-D1 PendingWork     = FROZEN
Core Gameplay Engine       = NOT YET FROZEN
Skill Runtime Readiness    = NOT YET READY
```

690086 Distribution / DSTS9-B02 已关闭：主将作为分摊承担者阵亡时，当前 DistributionTransaction 必须完成后才进入战斗终局。

## 当前工作原则

```text
Repository reality > historical roadmap assumption
REUSE -> EXTEND -> COMPOSE
```

Stage13 当前负责底层能力最终收口与 deterministic replay / exit audit。历史阶段过程稿不再作为当前路线权威。
