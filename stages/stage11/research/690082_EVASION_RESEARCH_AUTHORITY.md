# 690082 EVASION / 规避 — Stage11 Research Authority Bridge

Status: `RESEARCH_FROZEN / RUNTIME_NOT_INTEGRATED`
Date: `2026-09-17`

## 1. Purpose

本文件只负责把 `sgs-v2-battle-system` 的 Stage11 规划与已经冻结的外部研究 authority 连接起来。

本仓库不得复制并另行维护第二份 690082 机制正文；正式机制 authority 位于：

- Repository: `lxy2005051020-commits/sgs-state-mechanics-research`
- Contract: `states/functional/evasion/MECHANISM_CONTRACT.md`
- Research Question Ledger: `states/functional/evasion/RESEARCH_QUESTION_LEDGER.md`
- Frozen commit: `32341b548f2ef9f83335a5e47c6a650842d4d093`
- Freeze date: `2026-09-17`
- Evidence maturity: `HIGH_CONFIDENCE`

问题总账保存本轮完整研究轨迹：

```text
Q1-Q18 = 18 个主问题
Q13-B / Q15-B / Q18-B = 3 个补证/修复轮次
总研究轮次 = 21
```

## 2. Current Battle-Repo Status

```text
Research: FROZEN
Runtime: NOT_INTEGRATED
Strict completion: NO
Stage owner: Stage11
Production implementation: NOT YET AUTHORIZED BY THIS RECORD
```

## 3. Frozen Behavior Summary

The external contract freezes, at minimum:

- successful evasion invalidates the current eligible damage instance and yields zero troop loss;
- direct skill damage, DOT ticks, normal-attack-derived cleave secondary damage, and observed counterattack damage can enter evasion;
- observed 【连环计】 feedback damage and standard share-recipient troop loss do not re-enter evasion;
- adjudication is per target / per independent damage instance / per DOT tick;
- sure-hit suppresses the visible evasion verdict protocol;
- observable ordering is evasion before resistance/barrier;
- mid-round application can become effective immediately;
- natural removal is aligned to the holder action-start boundary;
- different evasion sources retain source-scoped contribution/lifecycle semantics;
- same-source reapplication is source-specific (e.g. 【兴云布雨】 additive contribution, 【灵巧】 value-unchanged continuation/refresh behavior);
- visible multi-contribution probability composition follows
  `P_total = 1 - Π(1 - P_i)`;
- battle reports expose one final holder-level verdict per damage instance, while one-roll vs hidden multi-roll remains `UNOBSERVABLE`.

This summary is navigational only. If this file and the research contract ever disagree, the pinned research contract is authoritative.

## 4. Runtime Integration Rule

Stage11 implementation must consume the frozen research contract rather than the old minimum-usable skeleton. Any implementation choice that is not empirically observable (for example one aggregate RNG roll versus hidden multi-roll) must be explicitly documented as an engineering-compatible choice, not an official fact.

Do not modify Stage8/9/10 frozen semantics merely to accommodate EVASION.
