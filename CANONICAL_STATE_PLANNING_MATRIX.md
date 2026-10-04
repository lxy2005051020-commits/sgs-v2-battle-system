# Canonical State Planning Matrix

> Status: CURRENT CROSS-REPO PROJECT AUTHORITY
>
> Reconciled: 2026-10-04
>
> Runtime / Project Stage authority: this repository.
>
> Research mechanism authority: `lxy2005051020-commits/sgs-state-mechanics-research`.

## 1. Canonical baseline

```text
Official States                 = 40
Research FROZEN                 = 40
Runtime FROZEN TO CONTRACT      = 40
Strict Complete                 = 40

Stage10 Scope                   = 8
Stage11 Scope                   = 17
Stage12 Scope                   = 7
Stage≤9 Ownership               = 8

Research-Debt States            = 0 blocking
```

Strict Complete requires both Research FROZEN and Runtime FROZEN TO CONTRACT.

690086 DSTS9-B02 is CLOSED / FROZEN_P0 by Stage13 residual authority.

## 2. Project Stage authority

```text
Stage≤9  = historical/core orchestration states
Stage10  = persistent states / 8
Stage11  = official-state completion wave / 17
Stage12  = official-state completion wave / 7 / COMPLETE
Stage13  = Core Gameplay Mechanism Completion / ACTIVE
Stage14+ = concrete Skill System integration after Stage13 exit gate
```

Research Wave is a research-order label and does not renumber Project Stage.

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
| 690086 | 分摊 DISTRIBUTION | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage11 / Stage13 residual | CLOSED | Stage13 residual authority / Research current main | Preserve frozen transaction; regression only | DSTS9-B02 CLOSED / FROZEN_P0; current DistributionTransaction drains before finalization |
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
| 690099 | 警戒 ALERT | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage11 | Research Wave 2 | Research states/functional/alert/MECHANISM_CONTRACT.md | Maintain Stage11 Runtime Freeze; regression only | threshold = MaxCarryTroops × 6%; equality triggers; remaining bounded micro-order debt nonblocking |
| 690070 | 会心 CRITICAL | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage11 | Research Wave 2 | Research critical contract | Maintain Stage11 Runtime Freeze; regression only | exact micro-read / bonus-latch timing boundary preserved |
| 690069 | 奇谋 STRATEGY_CRITICAL | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage11 | Research Wave 2 | Research strategy_critical contract | Maintain Stage11 Runtime Freeze; regression only | PROJECT-FROZEN MIRROR CONTRACT; timing debt preserved |
| 690221 | 看破 DAMAGE_REDUCTION_PIERCE | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage11 | Research Wave 2 | Research states/functional/damage_reduction_pierce/MECHANISM_CONTRACT.md | Maintain Stage11 Runtime Freeze; regression only | ACTIVE_SKILL and DOT/DELAYED applicability integrated; other explicitly unsupported families remain bounded |
| 690094 | 倒戈 LIFE_STEAL | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage11 | Research Wave 2 | Research life_steal contract + Stage11 authority resolution | Maintain Stage11 Runtime Freeze; regression only | Share assigned-damage basis + double-stage CEIL integrated; B11-FRZ-001 CLOSED |
| 690095 | 攻心 STRATEGY_LIFE_STEAL | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage11 | Research Wave 2 | Research strategy_life_steal contract + Stage11 authority resolution | Maintain Stage11 Runtime Freeze; regression only | PROJECT-FROZEN MIRROR CONTRACT; shared RecoverySystem second-CEIL owner |
| 690089 | 洞察 INSIGHT | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage12 | Research Wave 4 | Maintain frozen Stage12 runtime; Final Completion Audit | Maintain 690089 freeze; current audit owner 690109 | Contract v0.4-frozen; independent Runtime Freeze Audit PASS; 690109 protected-overlap amendment PASS; 690110 CAPTURE exclusion preserved; PD-INS-001/002 preserved |
| 690101 | 计穷 EXHAUSTION | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage12 | Research Wave 4 | Maintain frozen Stage12 runtime; Final Completion Audit | Maintain 690101 freeze; current audit owner 690109 | Contract v0.2-frozen; independent Runtime Freeze Audit PASS; Preparation blockers CLOSED; concrete PREPARING owner + first-effective CREATE/resume interruption audited; RD-SF-004 preserved; CI 36326173066 / 1244 passed / demo PASS; B-EXH-01..05 preserved |
| 690107 | 伪报 FALSE_REPORT | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage12 | Research Wave 4 | Maintain frozen Stage12 runtime; Final Completion Audit | Maintain 690107 freeze; current audit owner 690109 | Contract v1.0.1-frozen; independent Runtime Freeze Audit PASS; audit SHA 2feb4b03; CI 36329400436 = 1299 passed + demo PASS; 54 contract-focused tests; TALENT negative discriminator closed; bounded unknowns preserved |
| 690108 | 挑拨 PROVOCATION | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage12 | Research Wave 4 | Maintain frozen Stage12 runtime; Final Completion Audit | Maintain freeze; current audit owner 690109 | Contract v1.0-frozen; independent Runtime Freeze Audit PASS; audit code/test SHA e0f9e0c24; CI 36334810169 = 1392 passed + demo PASS; RD-SF-005 provenance preserved; BU-P06/BU-P09 remain unsupported |
| 690222 | 威慑 INTIMIDATION | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage12 | Research Wave 4 | Maintain frozen Stage12 runtime; Final Completion Audit | Maintain 690222 freeze; current audit owner 690109 | Contract v1.0-frozen; independent Runtime Freeze Audit PASS; RD-SF-006 provenance preserved; full SkillProviderRef binding; REFRESH reroll / RESUME zero-RNG audited; TROOP consumer absence NON_BLOCKING NOTE; source-death/specialized-removal/multi-source boundaries preserved |
| 690109 | 破坏 SABOTAGE | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage12 | Research Wave 5 | Maintain frozen Stage12 runtime; Final Completion Audit | Maintain freeze; current owner 690110 CAPTURE | Independent Runtime Freeze Audit PASS; audit-test SHA f698cb97; CI 36380946005 = 1558 passed + demo PASS; BLOCKER 0; MAJOR 0; B-SAB-09 dynamic equipment remains explicit unsupported boundary |
| 690110 | 捕获 CAPTURE | FROZEN | RUNTIME_FROZEN_TO_CONTRACT | YES | Stage12 | Research Wave 5 | Maintain frozen Stage12 runtime; Final Completion Audit | Stage12 Final Completion / Freeze Audit | Contract v1.0-frozen; independent Runtime Freeze Audit PASS; 33 adversarial tests; local full suite 1640 passed + demo PASS; BLOCKER 0; MAJOR 0; Q16/Q23/Q34/Q42/Q44/Q45/Q63/Q70-Q74/Q78 bounded boundaries preserved |

## 4. Conservation

```text
Stage≤9 ownership = 8
Stage10 ownership = 8
Stage11 ownership = 17
Stage12 ownership = 7
Total             = 40

Duplicate ownership = 0
Missing ownership   = 0
```

## 5. Current governance

- Stage12 is FROZEN / COMPLETE.
- Stage13-B1/B2/B2.5/B3 ordinary-treatment slices are closed and integrated.
- Stage13 residual 690221/690099/690086 amendments are integrated.
- Stage13-D1 PendingWork is FROZEN.
- Core Gameplay Engine remains NOT YET FROZEN pending remaining boundary closure and whole-battle deterministic replay / exit audit.
- Large-scale concrete Skill System integration remains behind the Stage13 exit gate.

Historical entry/activation snapshots and superseded route logs are intentionally omitted from this current authority file. They remain available in Git history.
