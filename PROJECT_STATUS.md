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
Stage14 Pilot Preparation       = ACTIVE
```

## 阶段状态

```text
Stage 1-8  = COMPLETE / FROZEN as applicable
Stage 9    = FROZEN
Stage10    = FROZEN
Stage11    = RUNTIME FROZEN / POST-FREEZE ACCEPTED
Stage12    = FROZEN / COMPLETE
Stage13    = ACTIVE / EXIT AUDIT REMAINS
Stage14    = PILOT PREPARATION ACTIVE / MAINLINE RUNTIME MERGE GATED
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

- 特殊兵种在 PRE_BATTLE / 准备阶段完成进阶
- 特殊兵种继承基础兵种克制家族
- 后续准备阶段战法读取前序效果修改后的当前状态
- Provider 为 holder-bound skill instance
- Provider 临时失效与 Provider 阵亡是不同生命周期
```

Canonical Research contract:
[Stage14 troop foundation](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/main/Stage14_Troop_Skill_Research/00_Governance/TROOP_SKILL_IDENTITY_AND_PROVIDER_LIFECYCLE_CONTRACT.md)

## Stage14 Pilot policy

允许开始**单战法 Pilot 准备与隔离分支实现**，但禁止批量兵种战法接入。

Mainline merge 仍需同时满足：

```text
1. Stage13 exit gate = PASS
2. Selected troop skill mechanism contract = CLOSED/FROZEN
3. Pilot-specific tests = PASS
4. No unresolved core primitive is guessed into Runtime
```

首个推荐 Pilot：**西凉铁骑**。

原因：

- 能覆盖 PRE_BATTLE 特殊兵种转换；
- 主要复用既有会心机制；
- 不需要象兵/飞熊军/丹阳兵那类 storage/battery 原语；
- 适合作为 TROOP Skill Runtime 的最小纵切验证。

其精确版本文本、倍率、马腾统领加成与快照/JIT 边界必须先由 Research 合同冻结，不能依据旧攻略直接写死。

## 当前边界

```text
Core Gameplay Engine      = NOT YET FROZEN
Skill Runtime Readiness   = NOT YET READY FOR MAINLINE MERGE
Stage14 Pilot Branch Work = ALLOWED
Bulk Troop Integration    = NOT AUTHORIZED
```

详细权威：

- [Stage13 README](stages/stage13/README.md)
- [Stage14 README](stages/stage14/README.md)
- [Stage13 Gap Ledger](stages/stage13/STAGE13_CORE_GAMEPLAY_GAP_LEDGER.md)
- [Stage13 Owner Matrix](stages/stage13/STAGE13_CORE_RUNTIME_OWNER_MATRIX.md)
