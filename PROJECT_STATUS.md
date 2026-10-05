> Gameplay Research status is MIRROR ONLY. Research truth and evidence: [Research authority](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/main/RESEARCH_AUTHORITY_INDEX.md). This document owns Runtime/project progress.

# 当前项目状态

> Reconciled: 2026-10-05

## 总体完成度

```text
Official States                 = 40
Research FROZEN                 = 40 / 40
Runtime FROZEN TO CONTRACT      = 40 / 40
Strict Complete                 = 40 / 40

Stage14 Troop Foundation        = FROZEN in Research
Stage14 Concrete Skill Integration = ACTIVE
```

## 阶段状态

```text
Stage 1-8  = COMPLETE / FROZEN as applicable
Stage 9    = FROZEN
Stage10    = FROZEN
Stage11    = RUNTIME FROZEN / POST-FREEZE ACCEPTED
Stage12    = FROZEN / COMPLETE
Stage13    = COMPLETE / FROZEN
Stage14    = ACTIVE / 8 BOUNDED-FROZEN BASELINES + 1 USER-PROVISIONAL INTEGRATION
```

Stage13 当前已完成：

```text
B1 Wounded / Recoverable Capacity  = FROZEN / IMPLEMENTED
B2 Damage Modifier Mathematics     = FROZEN / IMPLEMENTED
B2.5 Advancement / Damage Closure  = CLOSED / IMPLEMENTED
B3 Ordinary Treatment Core         = FROZEN / IMPLEMENTED
Residual state closure             = CLOSED / INTEGRATED
D1 PendingWork Foundation          = FROZEN / IMPLEMENTED
```

## Stage14 兵种战法基础合同

Research 已冻结：

```text
MC-STAGE14-TROOP-FOUNDATION-01 = FROZEN
MC-STAGE14-TROOP-BATCH01-04-BASELINE-01 = FROZEN_BASELINE / EXTENSIONS_OPEN

- 特殊兵种在 PRE_BATTLE / 准备阶段完成进阶
- 特殊兵种继承基础兵种克制家族
- 后续准备阶段战法读取前序效果修改后的当前状态
- Provider 为 holder-bound skill instance
- Provider 临时失效与 Provider 阵亡是不同生命周期
```

Canonical Research contract:
[Stage14 troop foundation](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/main/Stage14_Troop_Skill_Research/00_Governance/TROOP_SKILL_IDENTITY_AND_PROVIDER_LIFECYCLE_CONTRACT.md)

## Stage14 当前状态

当前已有 **8 个兵种战法** 完成 Research gate、Runtime 审计与 merged-main CI 并进入 `main`：西凉铁骑、白马义从、虎豹骑、无当飞军、陷阵营、白毦兵、大戟士、藤甲兵。

本次新增 **青州兵20153**，采用用户授权的暂定模型，见[接入说明](stages/stage14/QING_ZHOU_BING_INTEGRATION.md)
与[PR #52](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/pull/52)。
其D/10、统计口径和分配策略不声明实证冻结，曹操额外统率加成为空白占位。
Research合同经PR #13进入main；暂定模型接入与上方八个bounded freeze分开记录。

后续单战法或机制家族进入 main 仍需同时满足：

```text
1. Stage13 exit gate = PASS
2. Selected troop skill mechanism contract = CLOSED/FROZEN, or explicitly user-authorized provisional model with named open boundaries
3. Pilot-specific tests = PASS
4. No unresolved core primitive is guessed into Runtime
```

当前正式接入：

```text
20097 西凉铁骑
20075 白马义从
20098 虎豹骑
20100 无当飞军
20096 陷阵营
20099 白毦兵
20125 大戟士
20095 藤甲兵
20153 青州兵 (USER_PROVISIONAL_MODEL / CAO_CAO_PLACEHOLDER)

Troop Skills Registered      = 9 (8 bounded-frozen + 1 user-provisional)
Latest Merged-main CI        = PASS
Batch01-04 Runtime Audit     = PASS
```

## 当前边界

```text
Core Gameplay Engine      = FROZEN
Skill Runtime Readiness   = READY
Stage14 Troop Skills Registered = 9 (8 bounded-frozen + 1 user-provisional)
Stage14 Mainline Gate        = OPEN
Batch Integration             = ACTIVE / FAMILY-GATED
```

详细权威：

- [Stage13 README](stages/stage13/README.md)
- [Stage14 README](stages/stage14/README.md)
- [Stage14 Batch01-04 Mainline Audit](stages/stage14/BATCH01_04_MAINLINE_AUDIT.md)
- [Stage13 Gap Ledger](stages/stage13/STAGE13_CORE_GAMEPLAY_GAP_LEDGER.md)
- [Stage13 Owner Matrix](stages/stage13/STAGE13_CORE_RUNTIME_OWNER_MATRIX.md)
