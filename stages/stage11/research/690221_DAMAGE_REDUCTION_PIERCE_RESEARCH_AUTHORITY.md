# 690221 DAMAGE_REDUCTION_PIERCE / 看破 — Stage11 Research Authority Bridge

Status: RESEARCH_FROZEN / RUNTIME_NOT_INTEGRATED  
Date: 2026-09-25

## 1. Purpose

本文件只负责把 Battle 仓库 Stage11 规划与 Research 仓库 690221「看破」FROZEN authority 连接起来。

Battle 仓库不得复制维护第二份 current mechanism truth，也不得用已有 Runtime 反向证明游戏机制。

正式研究 authority：

- Repository: `lxy2005051020-commits/sgs-state-mechanics-research`
- Contract: `states/functional/damage_reduction_pierce/MECHANISM_CONTRACT.md`
- Research Ledger: `states/functional/damage_reduction_pierce/RESEARCH_QUESTION_LEDGER.md`
- Freeze Audit: `states/functional/damage_reduction_pierce/FREEZE_AUDIT.md`
- Frozen research head: `1126114a925905e4fcaacf1a7fea9e7f351367e8`
- Freeze date: 2026-09-25

## 2. Current Battle-Repo Status

```text
Research: FROZEN
Runtime: NOT_INTEGRATED
Strict Completion: NO
Stage owner: Stage11
Production implementation: NOT AUTHORIZED BY THIS BRIDGE
```

## 3. Frozen Behavior Summary

Stage11 Runtime Integration Design must consume the external contract:

- holder is the damage source;
- eligible incoming percentage reductions are functionally aggregated;
- observable ordering is **90% cap before pierce**;
- frozen transform is `R_eff = R_cap * (1-P)`;
- `P` is externally/provider-resolved; Provider 20250 exact `P(Speed)` function and read timing are not 690221 state semantics;
- zero eligible reduction yields no extra amplification and no armor/defense pierce;
- target reduction states are not deleted, shortened, or mutated;
- Alert is outside the 690221 eligible operand; 690221 does not alter AlertRate;
- transform resolution is per eligible resolved damage branch/target, while execution-log cardinality is explicitly **not guaranteed 1:1** with DamageEvents;
- observed applicable lanes: Normal Attack, observed Assault family, 【解烦卫】, 【以直报怨】;
- observed no-invocation members: 【踩踏】, 【冲阵】, 【荆棘】, 【气凌三军】;
- ACTIVE_SKILL and DOT/DELAYED remain `UNSUPPORTED_UNKNOWN`, not “confirmed no-pierce”.

## 4. Runtime Integration Constraints

Stage11 design / implementation must not:

- calculate or hardcode SP马超 `P(Speed)` inside generic state 690221;
- invent a 95% P cap;
- assume P is snapshot or JIT without Provider authority;
- silently map UNKNOWN families to “no pierce”;
- generalize 【气凌三军】 to all counterattacks;
- assume every SEE_THROUGH log maps 1:1 to one DamageEvent;
- move Alert into the pierced operand;
- implement final damage rounding inside the state transform;
- mutate defender reduction buffs;
- use existing runtime defaults as evidence.

## 5. Integration Direction

Recommended design boundary:

```text
Provider / skill layer
-> resolves effective P and lifecycle

Damage-family routing
-> checks authorized applicability

690221 state transform
-> eligible reduction aggregate
-> 90% cap
-> proportional pierce
-> R_eff only

Shared Damage Pipeline
-> continues final damage / mitigation / integerization
```

Any runtime need outside this frozen boundary must be explicitly designed as unsupported, deferred, or reopened with new evidence.
