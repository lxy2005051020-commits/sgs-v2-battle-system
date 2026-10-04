# 三国志战略版 V2 战斗系统

This repository owns runtime implementation.
Runtime Implementation Owner = Battle Repository.
Gameplay truth belongs to the [Research repository](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/95e7fe78430d623c0240e9615f5f054515a90ce9/RESEARCH_AUTHORITY_INDEX.md).
Research truth = consumed by reference. Research body != duplicated locally.

本仓库只维护生产代码、Runtime 数据、行为测试、实现/冻结审计与项目进度治理。

## 当前状态

```text
Official States                 = 40
Research FROZEN (MIRROR ONLY)   = 40 / 40
Runtime FROZEN TO CONTRACT      = 40 / 40
Strict Complete                 = 40 / 40

Stage12                        = FROZEN / COMPLETE
Stage13                        = ACTIVE
Stage13-D1 PendingWork         = FROZEN / IMPLEMENTED
Core Gameplay Engine           = NOT YET FROZEN
Skill Runtime Readiness        = NOT YET READY
```

当前 Stage13 入口与执行权威以 [Stage13 README](stages/stage13/README.md) 为准。

## 当前权威导航

- [当前项目状态](PROJECT_STATUS.md)
- [当前项目路线](PROJECT_ROADMAP.md)
- [40 状态规划矩阵](CANONICAL_STATE_PLANNING_MATRIX.md)
- [阶段索引](stages/README.md)
- [Stage13](stages/stage13/README.md)
- [Stage13 Core Gap Ledger](stages/stage13/STAGE13_CORE_GAMEPLAY_GAP_LEDGER.md)
- [Stage13 Runtime Owner Matrix](stages/stage13/STAGE13_CORE_RUNTIME_OWNER_MATRIX.md)
- [Stage13 Test Matrix](stages/stage13/STAGE13_CORE_MECHANISM_TEST_MATRIX.md)
- [Stage13-D1 Freeze Audit](stages/stage13/STAGE13_D1_PENDING_WORK_FREEZE_AUDIT.md)

## Runtime

生产代码：`sgs_v2/battle_core/`

测试：`tests/`

演示：`demo.py`

研究过程材料不再复制到 Runtime 仓库。冻结机制的原始证据、问题账本和研究轮次材料由 Research 仓库保存；本仓库只保留 Runtime 所需的合同映射、最终冻结审计、当前治理文件和可执行审计工具。

## 维护原则

```text
Research truth -> Research repo
Runtime truth  -> production code + tests
Current governance -> current README / matrices / freeze audits
Historical process -> Git history
```

已被最终冻结记录取代的中间 prompt、repair report、round-by-round audit 与重复路线稿不再作为当前树中的权威文件。
