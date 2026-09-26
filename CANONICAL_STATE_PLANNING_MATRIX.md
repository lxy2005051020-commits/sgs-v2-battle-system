# Canonical State Planning Matrix

> Status: **CURRENT CROSS-REPO PROJECT AUTHORITY**
>
> Reconciled: 2026-09-26
>
> Project Stage and Runtime Maturity authority: this Battle repository.
>
> Research Maturity and Mechanism Authority source: `lxy2005051020-commits/sgs-state-mechanics-research`.

> **2026-09-26 Stage11 final authority:** Share × 倒戈/攻心 authority conflict is resolved; Stage11 Runtime is **FROZEN** and independent Post-Freeze Acceptance is **PASS / CONFIRMED**. Acceptance Audit SHA `5a0a4164e7624c28eae2c7aa28f66061ef3c9313`, CI `36170063365`; Research post-acceptance mirror `9ad990da544ad87047e74a664cc1984f890bb274`. Stage12 Activation Gate is **CLEARED**, while Stage12 Active remains **NO**.

## 1. Canonical baseline

```text
Official States                 = 40
Research FROZEN                 = 37
Runtime FROZEN TO CONTRACT      = 33
Strict Complete                 = 32
Stage11 Scope                   = 17
Stage11 Research FROZEN         = 16
Stage11 Runtime FROZEN          = 17
Stage12 Scope                   = 7
Stage12 Research FROZEN         = 5
Evidence-Blocked / Deferred     = 0
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
| 690086 | 分摊 DISTRIBUTION | RUNTIME_READY_WITH_RESEARCH_DEBT | RUNTIME_FROZEN_TO_CONTRACT | NO | Stage11 | Research Debt Closure | Stage9 distribution freeze record | Maintain Stage11 Runtime Freeze; regression only | DSTS9-B02 OPEN / UNOBSERVED; Distribution × LifeSteal participant exclusion is PROJECT_RUNTIME_DEFAULT |
| 690090 | 先攻 FIRST_STRIKE | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage11 | Research Wave 3 | Research states/functional/first_strike/MECHANISM_CONTRACT.md | Maintain Stage11 Runtime Freeze; regression only | Q1-Q17 CLOSED; deterministic tie migration green |
| 690091 | 遇袭 SURPRISE | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage11 | Research Wave 3 | Research states/functional/surprise/MECHANISM_CONTRACT.md | Maintain Stage11 Runtime Freeze; regression only | PROJECT-FROZEN MIRROR CONTRACT |
| 690102 | 缴械 DISARM | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage11 | Research Wave 3 | Research states/control/disarm/MECHANISM_CONTRACT.md | Maintain Stage11 Runtime Freeze; regression only | reflected/proxy admission boundary preserved |
| 690104 | 虚弱 WEAKNESS | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage11 | Research Wave 3 | Research states/control/weakness/MECHANISM_CONTRACT.md | Maintain Stage11 Runtime Freeze; regression only | legal-zero topology frozen; bounded debt preserved |
| 690105 | 禁疗 HEALING_BAN | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage11 | Research Wave 3 | Research states/control/healing_block/MECHANISM_CONTRACT.md | Maintain Stage11 Runtime Freeze; regression only | positive-request interception after recovery modifier |
| 690111 | 震慑 STUN | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage11 | Research Wave 3 | Research states/control/stun/MECHANISM_CONTRACT.md | Maintain Stage11 Runtime Freeze; regression only | natural-action admission; bounded research debt preserved |
| 690082 | 规避 EVASION | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage11 | Research Wave 2 | Research evasion contract | Maintain Stage11 Runtime Freeze; regression only |  |
| 690083 | 抵御 RESISTANCE | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage11 | Research Wave 2 | Research resistance contract | Maintain Stage11 Runtime Freeze; regression only |  |
| 690092 | 必中 SURE_HIT | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage11 | Research Wave 2 | Research sure_hit contract | Maintain Stage11 Runtime Freeze; regression only |  |
| 690093 | 破阵 BREAK_FORMATION | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage11 | Research Wave 2 | Research break_formation contract | Maintain Stage11 Runtime Freeze; regression only | persistent/application-bound limits explicit |
| 690099 | 警戒 ALERT | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage11 | Research Wave 2 | Research states/functional/alert/MECHANISM_CONTRACT.md | Maintain Stage11 Runtime Freeze; regression only | threshold equality / rounding / holder-death / Share micro-order debt preserved |
| 690070 | 会心 CRITICAL | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage11 | Research Wave 2 | Research critical contract | Maintain Stage11 Runtime Freeze; regression only | exact micro-read / bonus-latch timing boundary preserved |
| 690069 | 奇谋 STRATEGY_CRITICAL | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage11 | Research Wave 2 | Research strategy_critical contract | Maintain Stage11 Runtime Freeze; regression only | PROJECT-FROZEN MIRROR CONTRACT; timing debt preserved |
| 690221 | 看破 DAMAGE_REDUCTION_PIERCE | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage11 | Research Wave 2 | Research states/functional/damage_reduction_pierce/MECHANISM_CONTRACT.md | Maintain Stage11 Runtime Freeze; regression only | unsupported damage families remain explicit boundary |
| 690094 | 倒戈 LIFE_STEAL | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage11 | Research Wave 2 | Research life_steal contract + Stage11 authority resolution | Maintain Stage11 Runtime Freeze; regression only | Share assigned-damage basis + double-stage CEIL integrated; B11-FRZ-001 CLOSED |
| 690095 | 攻心 STRATEGY_LIFE_STEAL | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage11 | Research Wave 2 | Research strategy_life_steal contract + Stage11 authority resolution | Maintain Stage11 Runtime Freeze; regression only | PROJECT-FROZEN MIRROR CONTRACT; shared RecoverySystem second-CEIL owner |
| 690089 | 洞察 INSIGHT | FROZEN | PARTIAL | NO | Stage12 | Research Wave 4 | Research states/functional/insight/MECHANISM_CONTRACT.md | Stage12 contract-aligned Runtime Design | Contract v0.2-frozen; Freeze Audit PASSED; PD-INS-001/002 frozen; special-state debts preserved |
| 690101 | 计穷 EXHAUSTION | FROZEN | NOT_INTEGRATED | NO | Stage12 | Research Wave 4 | Research states/control/exhaustion/MECHANISM_CONTRACT.md | Stage12 contract-aligned Runtime Design | Contract v0.2-frozen; full-corpus falsification PASS; 23,002 reports / 18,487 EXHAUSTION executions / TRUE_COUNTEREXAMPLE=0; B-EXH-01..05 preserved |
| 690107 | 伪报 FALSE_REPORT | FROZEN | NOT_INTEGRATED | NO | Stage12 | Research Wave 4 | Research states/control/false_report/MECHANISM_CONTRACT.md | Stage12 contract-aligned Runtime Design | Contract v1.0.1-frozen; final falsification + coverage repair PASS; stronger-vs-weaker / unseen immunity / special NPC / untested Equipment subtype debt bounded and non-blocking |
| 690108 | 挑拨 PROVOCATION | FROZEN | NOT_INTEGRATED | NO | Stage12 | Research Wave 4 | Research states/control/provocation/MECHANISM_CONTRACT.md | Stage12 contract-aligned Runtime Design | Contract v1.0-frozen; Round 1–6 + adversarial falsification PASS; final correction audit 20/20 PASS; Q43 restored; bounded unknowns explicit; cfg_71 excluded from state core |
| 690222 | 威慑 INTIMIDATION | FROZEN | NOT_INTEGRATED | NO | Stage12 | Research Wave 4 | Research states/control/intimidation/MECHANISM_CONTRACT.md | Stage12 contract-aligned Runtime Design | Contract v1.0-frozen; repaired adversarial falsification PASS; Q1-Q80 canonical governance PASS; OPEN_BLOCKING=0; source-skill counter separated; BU-01..10 explicit/non-blocking |
| 690109 | 破坏 SABOTAGE | MINIMUM_USABLE | NOT_INTEGRATED | NO | Stage12 | Research Wave 5 | Research minimum_usable authority | Targeted research before Stage12 design |  |
| 690110 | 捕获 CAPTURE | MINIMUM_USABLE | NOT_INTEGRATED | NO | Stage12 | Research Wave 5 | Research minimum_usable authority | Targeted research before Stage12 design |  |

## 4. Stage11 Final Acceptance Snapshot

```text
Stage11 Runtime: FROZEN
Stage11 Post-Freeze Acceptance: PASS
Stage11 Runtime Freeze: CONFIRMED
Stage11 Reopen Required: NO
B11-FRZ-001: CLOSED
Runtime Tested SHA: ce42bc62cfb26f8ca0b448e74b26533604bb0505
Freeze Declaration SHA: 8cde73ce15c8d02a70b3e0913efbfc5a2887e92b
Post-Freeze Acceptance SHA: 5a0a4164e7624c28eae2c7aa28f66061ef3c9313
Acceptance CI: 36170063365 / 913 passed / demo PASS
Research post-acceptance mirror: 9ad990da544ad87047e74a664cc1984f890bb274
Stage12 Activation Gate: CLEARED
Stage12 Readiness: READY
Stage12 Active: NO
```

Residual debt remains explicit and does not block the confirmed Stage11 Runtime Freeze.

## 5. 40-state conservation

```text
Stage≤9 ownership = 8
Stage10 ownership = 8
Stage11 ownership = 17
Stage12 ownership = 7
Total             = 40

Duplicate Project Stage ownership = 0
Missing Project Stage ownership   = 0
```

## 6. Stage10 runtime audit basis

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

## 7. Governance invariants

- Research Wave may be reordered; Project Stage may not be silently renumbered.
- Stage11 exit gate is satisfied; Runtime Freeze is confirmed by independent post-freeze acceptance.
- Research FROZEN does not imply Runtime FROZEN.
- Runtime default with research debt does not count as Strict Complete.
- 690069, 690095 and 690091 retain their Project-Frozen Mirror distinction.
- 690099 and 690221 are Research FROZEN and Runtime FROZEN TO CONTRACT; bounded debt remains explicit and non-blocking.
- Stage12 research has begun ahead of production activation: 690089 INSIGHT, 690101 EXHAUSTION, 690107 FALSE_REPORT, 690108 PROVOCATION and 690222 INTIMIDATION are Research FROZEN. Research Wave 4 is complete; Stage12 Active remains NO and their Runtime work is not yet frozen.
- Stage12 Activation Gate is CLEARED and Stage12 Readiness is READY; Stage12 Active remains NO. Stage13 is not activated.
