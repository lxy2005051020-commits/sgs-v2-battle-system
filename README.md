# 三国志战略版 V2 战斗系统

雁行阵 `20862` 本分支已接入Lv1–10基础值暂定模型，属性缩放继续暂缓。
普通状态转移、静态减伤转移及统率偷取复用既有owner；复杂状态转移保留明确边界。
见[接入与验证记录](stages/stage14/YAN_XING_ZHEN_INTEGRATION.md)。本条不表示已合入main或Gameplay实证冻结。

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

青州兵（20153）：[接入说明](stages/stage14/QING_ZHOU_BING_INTEGRATION.md)，
演示 `python scripts/demo_qingzhou.py`。治疗采用用户授权的暂定D/10模型，曹操额外统率加成为空白占位。

研究过程材料不再复制到 Runtime 仓库。冻结机制的原始证据、问题账本和研究轮次材料由 Research 仓库保存；本仓库只保留 Runtime 所需的合同映射、最终冻结审计、当前治理文件和可执行审计工具。

## 维护原则

```text
Research truth -> Research repo
Runtime truth  -> production code + tests
Current governance -> current README / matrices / freeze audits
Historical process -> Git history
```

已被最终冻结记录取代的中间 prompt、repair report、round-by-round audit 与重复路线稿不再作为当前树中的权威文件。

## 武锋阵接入（2026-10-13）

武锋阵 `22031` 支持Lv10完整运行：前5回合概率优先选中主将及同次战法的实时统率减伤，携带者行动时触发奇数回合副将随机治疗另外两名队友、偶数回合叠加增伤。采用用户指定公式与选人规则，标记 `USER_SPECIFIED_MODEL / NOT_GAMEPLAY_FROZEN`；低等级统率缩放未推导。

[接入记录、组件与验证证据](stages/stage14/WU_FENG_ZHEN_INTEGRATION.md)。

## 五个已完成阵法统一同步（2026-10-13）

实现注册数为5：锋矢阵、八门金锁阵、箕形阵、三势阵、武锋阵。范围与保留的未决项见[同步记录](stages/stage14/FORMATION_COMPLETED_SYNC.md)。原本地候选记录属于历史验证快照；本次整合保留用户指定模型边界，不把实现合并等同于Gameplay实证冻结。
