# Canonical State Planning Matrix

> Status: **CURRENT CROSS-REPO PROJECT AUTHORITY**
>
> Reconciled: 2026-09-24
>
> Project Stage and Runtime Maturity authority: this Battle repository.
>
> Research Maturity and Mechanism Authority source: `lxy2005051020-commits/sgs-state-mechanics-research`.

## 1. Canonical baseline

```text
Official States                 = 40
Research FROZEN                 = 29
Runtime FROZEN TO CONTRACT      = 16
Strict Complete                 = 16
Stage11 Scope                   = 17
Stage11 Research FROZEN         = 13
Stage11 Runtime FROZEN          = 0
Stage12 Scope                   = 7
Evidence-Blocked / Deferred     = 2
Research-Debt States            = 1
```

Strict Complete means exactly:

```text
Research FROZEN
+
Runtime FROZEN TO CONTRACT
```

## 2. Project Stage authority

```text
Stage11 = 官方状态补全（一） / 17 states
Stage12 = 官方状态补全（二） / 7 states
Stage13 = 突击战法运行时
Stage14 = 普通主动战法
Stage15 = 准备战法
Stage16+ = 被动 / 指挥 / 阵法 / 兵种等
```

Research Wave is a separate research-order label and never renumbers Project Stage.

## 3. Canonical 40-state matrix

| ID | State | Research Maturity | Runtime Maturity | Strict Complete | Project Stage | Research Wave | Authority | Next Action | Evidence / Debt |
|---:|---|---|---|:---:|---|---|---|---|---|
| 690072 | 灼烧 BURN | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage10 | Research Wave 1 | Research persistent/burn contract + Stage10 Implementation Freeze | Frozen; regression only |  |
| 690073 | 水攻 FLOOD | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage10 | Research Wave 1 | Research persistent/flood contract + Stage10 Implementation Freeze | Frozen; regression only |  |
| 690074 | 中毒 POISON | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage10 | Research Wave 1 | Research persistent/poison contract + Stage10 Implementation Freeze | Frozen; regression only |  |
| 690075 | 溃逃 ROUT | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage10 | Research Wave 1 | Research persistent/rout contract + Stage10 Implementation Freeze | Frozen; regression only |  |
| 690076 | 沙暴 SANDSTORM | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage10 | Research Wave 1 | Research persistent/sandstorm contract + Stage10 Implementation Freeze | Frozen; regression only |  |
| 690077 | 叛逃 REBELLION | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage10 | Research Wave 1 | Research persistent/rebellion contract + Stage10 Implementation Freeze | Frozen; regression only |  |
| 690078 | 急救 FIRST_AID | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage10 | Research Wave 1 | Research persistent/first_aid contract + Stage10 Implementation Freeze | Frozen; regression only |  |
| 690079 | 休整 RECUPERATION | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage10 | Research Wave 1 | Research persistent/recuperation contract + Stage10 Implementation Freeze | Frozen; regression only | RE-FROZEN research authority |
| 690081 | 连击 COMBO | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage≤9 | Historical | Research combo contract + frozen runtime | Frozen; regression only |  |
| 690084 | 群攻 CLEAVE | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage≤9 | Historical | Research cleave contract + frozen runtime | Frozen; regression only |  |
| 690085 | 反击 COUNTERATTACK | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage≤9 | Historical | Stage9 counterattack freeze record | Frozen; regression only |  |
| 690087 | 分担 DAMAGE_SHARE | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage≤9 | Historical | Research damage_share contract + frozen runtime | Frozen; regression only |  |
| 690097 | 铁索连环 CHAIN_LINK | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage≤9 | Historical | Stage9 chain freeze record | Frozen; regression only |  |
| 690098 | 援护 GUARD | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage≤9 | Historical | Research guard contract + frozen runtime | Frozen; regression only |  |
| 690103 | 混乱 CONFUSION | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage≤9 | Historical | Research confusion contract + frozen runtime | Frozen; regression only |  |
| 690106 | 嘲讽 TAUNT | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage≤9 | Historical | Stage9 taunt freeze record | Frozen; regression only |  |
| 690086 | 分摊 DISTRIBUTION | RUNTIME_READY_WITH_RESEARCH_DEBT | RUNTIME_DEFAULT_WITH_RESEARCH_DEBT | NO | Stage11 | Research Debt Closure | Stage9 distribution freeze record | Close DSTS9-B02 debt | Empirical OPEN / UNOBSERVED; runtime default only |
| 690090 | 先攻 FIRST_STRIKE | FROZEN | SKELETON_ONLY | NO | Stage11 | Research Wave 3 | Research states/functional/first_strike/MECHANISM_CONTRACT.md | Runtime Integration Design | Q1-Q17 CLOSED; Unified Falsification Audit PASSED; true counterexamples 0 |
| 690091 | 遇袭 SURPRISE | FROZEN | SKELETON_ONLY | NO | Stage11 | Research Wave 3 | Research states/functional/surprise/MECHANISM_CONTRACT.md | Runtime Integration Design | PROJECT-FROZEN MIRROR CONTRACT of 690090; opposite priority direction; shared mechanics unchanged |
| 690102 | 缴械 DISARM | FROZEN | SKELETON_ONLY | NO | Stage11 | Research Wave 3 | Research states/control/disarm/MECHANISM_CONTRACT.md | Runtime Integration Design | Contract v0.4; full-corpus falsification SURVIVED; independent Freeze Readiness PASSED; B01-B05 preserved |
| 690104 | 虚弱 WEAKNESS | FROZEN | SKELETON_ONLY | NO | Stage11 | Research Wave 3 | Research states/control/weakness/MECHANISM_CONTRACT.md | Stage11 Runtime Integration Design | Research Freeze Audit PASSED after canonical-ledger / denominator / 690087 / 690078 repair; Runtime unchanged |
| 690105 | 禁疗 HEALING_BAN | MINIMUM_USABLE | SKELETON_ONLY | NO | Stage11 | Research Wave 3 | Research minimum_usable authority | Targeted research → contract → freeze |  |
| 690111 | 震慑 STUN | FROZEN | SKELETON_ONLY | NO | Stage11 | Research Wave 3 | Research states/control/stun/MECHANISM_CONTRACT.md | Runtime Integration Design | Contract v1.2-frozen; Q01-Q23 closed/bounded; 11,970-report adversarial falsification true CE=0; Independent Freeze Audit PASSED; B01-B05 preserved |
| 690082 | 规避 EVASION | FROZEN | NOT_INTEGRATED | NO | Stage11 | Research Wave 2 | Research evasion contract | Runtime Integration Design |  |
| 690083 | 抵御 RESISTANCE | FROZEN | NOT_INTEGRATED | NO | Stage11 | Research Wave 2 | Research resistance contract | Runtime Integration Design |  |
| 690092 | 必中 SURE_HIT | FROZEN | NOT_INTEGRATED | NO | Stage11 | Research Wave 2 | Research sure_hit contract | Runtime Integration Design |  |
| 690093 | 破阵 BREAK_FORMATION | FROZEN | NOT_INTEGRATED | NO | Stage11 | Research Wave 2 | Research break_formation contract | Runtime Integration Design |  |
| 690099 | 警戒 VIGILANCE | MINIMUM_USABLE | NOT_INTEGRATED | NO | Stage11 | Research Wave 2 | Research minimum_usable authority | Acquire evidence; targeted research | EVIDENCE BLOCKED / DEFERRED |
| 690070 | 会心 CRITICAL | FROZEN | NOT_INTEGRATED | NO | Stage11 | Research Wave 2 | Research critical contract | Runtime Integration Design | Empirical-Frozen |
| 690069 | 奇谋 STRATEGY_CRITICAL | FROZEN | NOT_INTEGRATED | NO | Stage11 | Research Wave 2 | Research strategy_critical contract | Runtime Integration Design | PROJECT-FROZEN MIRROR CONTRACT |
| 690221 | 看破 DAMAGE_REDUCTION_PIERCE | NOT_INDEXED | NOT_INTEGRATED | NO | Stage11 | Research Wave 2 | No current indexed contract | Acquire evidence; create authority | EVIDENCE BLOCKED / DEFERRED |
| 690094 | 倒戈 LIFE_STEAL | FROZEN | NOT_INTEGRATED | NO | Stage11 | Research Wave 2 | Research life_steal contract | Runtime Integration Design | Empirical-Frozen / HIGH_CONFIDENCE |
| 690095 | 攻心 STRATEGY_LIFE_STEAL | FROZEN | NOT_INTEGRATED | NO | Stage11 | Research Wave 2 | Research strategy_life_steal contract | Runtime Integration Design | PROJECT-FROZEN MIRROR CONTRACT |
| 690089 | 洞察 INSIGHT | MINIMUM_USABLE | PARTIAL | NO | Stage12 | Research Wave 4 | Research minimum_usable authority | Targeted research before Stage12 design |  |
| 690101 | 计穷 EXHAUSTION | MINIMUM_USABLE | NOT_INTEGRATED | NO | Stage12 | Research Wave 4 | Research minimum_usable authority | Targeted research before Stage12 design |  |
| 690107 | 伪报 FALSE_REPORT | MINIMUM_USABLE | NOT_INTEGRATED | NO | Stage12 | Research Wave 4 | Research minimum_usable authority | Targeted research before Stage12 design |  |
| 690108 | 挑拨 PROVOCATION | MINIMUM_USABLE | NOT_INTEGRATED | NO | Stage12 | Research Wave 4 | Research minimum_usable authority | Targeted research before Stage12 design |  |
| 690222 | 威慑 INTIMIDATION | NOT_INDEXED | NOT_INTEGRATED | NO | Stage12 | Research Wave 4 | No current indexed contract | Create research authority before Stage12 design |  |
| 690109 | 破坏 SABOTAGE | MINIMUM_USABLE | NOT_INTEGRATED | NO | Stage12 | Research Wave 5 | Research minimum_usable authority | Targeted research before Stage12 design |  |
| 690110 | 捕获 CAPTURE | MINIMUM_USABLE | NOT_INTEGRATED | NO | Stage12 | Research Wave 5 | Research minimum_usable authority | Targeted research before Stage12 design |  |

## 4. 40-state conservation

```text
Stage≤9 ownership = 8
Stage10 ownership = 8
Stage11 ownership = 17
Stage12 ownership = 7
Total             = 40

Duplicate Project Stage ownership = 0
Missing Project Stage ownership   = 0
```

## 5. Stage10 runtime audit basis

The eight Stage10 persistent states are Runtime FROZEN TO CONTRACT.

Current `main` production and test subtrees still equal the formal Stage10 frozen pins:

```text
sgs_v2 tree = 05511f7576b10efc9664e4e70d9dad88d364966a
tests tree  = 122ffd68f1aac06ce353572fd3568aa54d19b5dd
```

Authority:
- `stages/stage10/STAGE10_IMPLEMENTATION_FREEZE.md`
- `stages/stage10/STAGE10_POST_FREEZE_MERGE_AUDIT.md`
- main integration commit `30f623f9efed20b5a82044b51519db1af6da86d3`

## 6. Governance invariants

- Research Wave may be reordered; Project Stage may not be silently renumbered.
- Stage11 remains active until its exit gate is satisfied.
- Research FROZEN does not imply Runtime FROZEN.
- Runtime default with research debt does not count as Strict Complete.
- 690069, 690095 and 690091 retain their Project-Frozen Mirror distinction.
- 690099 and 690221 remain research-open / evidence-blocked or deferred.
- No Stage12 or Stage13 activation is authorized by this reconciliation.
