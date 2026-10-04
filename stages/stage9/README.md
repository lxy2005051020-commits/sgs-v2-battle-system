# Stage9 · Cross-Mechanism Runtime Orchestration

> Status: FROZEN

Stage9 冻结跨机制编排、Target/Redirect/Reaction、Damage partition、Battle Finalization 与相关整数化边界。

## Current authority

- [Runtime authority map](docsync/STAGE9_AUTHORITY_MAP.md)
- [Typed Runtime contracts](hardening/STAGE9_TYPED_RUNTIME_CONTRACTS.md)
- [Runtime invariants](hardening/STAGE9_RUNTIME_INVARIANTS.md)
- [Regression contracts](hardening/STAGE9_REGRESSION_CONTRACTS.md)
- [Global cross-mechanism final audit](audits/STAGE9_GLOBAL_CROSS_MECHANISM_FINAL_AUDIT.md)
- [Frozen design](STAGE9.md)
- [Design freeze](STAGE9_DESIGN_FREEZE.md)
- [Final audit](STAGE9_FINAL_AUDIT.md)
- [Freeze record](STAGE9_FREEZE_RECORD.md)
- [Stage9 → Stage10 compatibility](STAGE9_STAGE10_COMPATIBILITY_ADDENDUM.md)
- [690098 Guard contract](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/95e7fe78430d623c0240e9615f5f054515a90ce9/states/functional/guard/MECHANISM_CONTRACT.md)

## Frozen scope

```text
CONFUSION
TAUNT
GUARD
COMBO
CLEAVE
CHAIN_LINK
DAMAGE_SHARE
COUNTERATTACK
DISTRIBUTION
```

Distribution 的历史 DSTS9-B02 未观察边界已由 Stage13 后续权威关闭：

```text
commander participant death
-> current DistributionTransaction continues
-> remaining participant commits continue
-> original target Dtarget commits
-> transaction completes
-> battle finalization
```

因此当前状态：

```text
690086 DISTRIBUTION = FROZEN
DSTS9-B02           = CLOSED / FROZEN_P0
```

Stage9 不再保留逐 phase implementation/repair 报告；这些过程可从 Git history 追溯。当前 Runtime 只以生产代码、测试和上述最终冻结权威为准。


Research Authority:
Repository: lxy2005051020-commits/sgs-state-mechanics-research
Commit: 95e7fe78430d623c0240e9615f5f054515a90ce9
Path: RESEARCH_AUTHORITY_INDEX.md
Status: CURRENT INDEX; individual contracts retain scoped status
