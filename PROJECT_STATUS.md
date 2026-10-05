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
Stage14    = ACTIVE / XILIANG CAVALRY MERGED TO MAIN
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

## Stage14 当前状态

首个兵种战法 **西凉铁骑** 已完成 Research、Runtime、自动 PRE_BATTLE 接入、独立审计并合并进入 `main`。

后续单战法或机制家族进入 main 仍需同时满足：

```text
1. Stage13 exit gate = PASS
2. Selected troop skill mechanism contract = CLOSED/FROZEN
3. Pilot-specific tests = PASS
4. No unresolved core primitive is guessed into Runtime
```

首个已正式接入战法：**西凉铁骑（20097）**。

```text
Research Contract            = FROZEN
Ma Teng Speed Scaling        = FROZEN
Runtime Integration          = MERGED TO MAIN
BattleEngine PRE_BATTLE      = AUTO-WIRED
Merged-main CI               = PASS
```

## 当前边界

```text
Core Gameplay Engine      = FROZEN
Skill Runtime Readiness   = READY
Stage14 First Troop Skill   = XILIANG CAVALRY / IN MAIN
Stage14 Mainline Gate     = OPEN
Bulk Troop Integration    = NOT AUTHORIZED
```

详细权威：

- [Stage13 README](stages/stage13/README.md)
- [Stage14 README](stages/stage14/README.md)
- [Stage13 Gap Ledger](stages/stage13/STAGE13_CORE_GAMEPLAY_GAP_LEDGER.md)
- [Stage13 Owner Matrix](stages/stage13/STAGE13_CORE_RUNTIME_OWNER_MATRIX.md)
