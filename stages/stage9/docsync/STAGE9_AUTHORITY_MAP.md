# STAGE9_AUTHORITY_MAP

RF-C02 current authority map. This file is navigation, not a replacement for P0 text.

## Status vocabulary

```text
FROZEN
RUNTIME_READY_WITH_RESEARCH_DEBT
SUPERSEDED
HISTORICAL
OPEN
```

`READY` is reserved for an admission/gate statement, not a synonym for `FROZEN`. Historical audit verdicts such as `PASS WITH DOC SYNC` or `NARROW REOPEN` remain valid descriptions of their audit moment but do not describe current closure state after later Repair Packages.

## Domain authority map

| Domain | Current authority | Notes |
|---|---|---|
| Target arbitration | [`STAGE9_CORE_ARBITRATION_RULES_V2.md`](../research/core_arbitration_v2/STAGE9_CORE_ARBITRATION_RULES_V2.md) + mechanism P0s | CONFUSION / TAUNT / GUARD precedence and target identity |
| Execution / death scope | [`STAGE9_EXECUTION_RIGHT_AND_DEATH_SCOPE_CONTRACT.md`](../research/core_arbitration_v2/STAGE9_EXECUTION_RIGHT_AND_DEATH_SCOPE_CONTRACT.md) | P0 shared rule; replaces universal death slogans |
| Finalization | [`STAGE9_BATTLE_FINALIZATION_BARRIER_CONTRACT.md`](../research/core_arbitration_v2/STAGE9_BATTLE_FINALIZATION_BARRIER_CONTRACT.md) | P0 shared barrier; `VictoryConditionSatisfied != BattleFinalized` |
| COMBO | [state P0](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/main/states/functional/combo/MECHANISM_CONTRACT.md) | sole mechanism P0 owner; RF-P02/P03/P04 are closure records |
| CLEAVE | [state P0](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/main/states/functional/cleave/MECHANISM_CONTRACT.md) | battle Freeze Record + RF-P06/P07/P04 are supporting repair/freeze evidence |
| CHAIN_LINK | [`STAGE9_CHAIN_MECHANICS_FREEZE_RECORD.md`](../research/core_arbitration_v2/STAGE9_CHAIN_MECHANICS_FREEZE_RECORD.md) | RF-P01 closes integerization |
| DAMAGE_SHARE | [state P0](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/main/states/functional/damage_share/MECHANISM_CONTRACT.md) | battle Freeze Record is synchronized mirror/supporting record, not a competing semantic authority |
| DISTRIBUTION | [`STAGE9_DISTRIBUTION_MECHANICS_FREEZE_RECORD.md`](../research/core_arbitration_v2/STAGE9_DISTRIBUTION_MECHANICS_FREEZE_RECORD.md) + Finalization Barrier | deterministic runtime with isolated empirical debt `DSTS9-B02` |
| COUNTERATTACK | [`STAGE9_COUNTERATTACK_MECHANICS_FREEZE_RECORD.md`](../research/core_arbitration_v2/STAGE9_COUNTERATTACK_MECHANICS_FREEZE_RECORD.md) | runtime deterministic; nonblocking fidelity notes do not reopen P0 |
| TAUNT | [`STAGE9_TAUNT_MECHANICS_FREEZE_RECORD.md`](../research/core_arbitration_v2/STAGE9_TAUNT_MECHANICS_FREEZE_RECORD.md) | FROZEN |
| GUARD | [state P0](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/main/states/functional/guard/MECHANISM_CONTRACT.md) | battle `STATE_690098_GUARD_MECHANISM_CONTRACT.md` is compatibility mirror/navigation |
| CONFUSION | [state P0](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/main/states/control/confusion/MECHANISM_CONTRACT.md) | RF-P03 closes old CFS9-B01 path as unreachable |
| Runtime typed contracts | [`STAGE9_TYPED_RUNTIME_CONTRACTS.md`](../hardening/STAGE9_TYPED_RUNTIME_CONTRACTS.md) | RF-C01 engineering contract |
| Runtime invariants | [`STAGE9_RUNTIME_INVARIANTS.md`](../hardening/STAGE9_RUNTIME_INVARIANTS.md) | RF-C01 |
| Regression contracts | [`STAGE9_REGRESSION_CONTRACTS.md`](../hardening/STAGE9_REGRESSION_CONTRACTS.md) | RF-C01 |

## STAGE9_MECHANISM_STATUS_MATRIX

| ID | Mechanism | Current status | Runtime ready | Research debt | P0 |
|---:|---|---|---|---|---|
| 690103 | CONFUSION | FROZEN | YES | NO blocking debt | state `states/control/confusion/MECHANISM_CONTRACT.md` |
| 690106 | TAUNT | FROZEN | YES | NO blocking debt | battle Taunt Freeze Record |
| 690098 | GUARD | FROZEN | YES | NO blocking debt | state `states/functional/guard/MECHANISM_CONTRACT.md` |
| 690081 | COMBO | FROZEN | YES | NO blocking debt | state `states/functional/combo/MECHANISM_CONTRACT.md` |
| 690084 | CLEAVE | FROZEN | YES | NO blocking debt | state `states/functional/cleave/MECHANISM_CONTRACT.md` |
| 690097 | CHAIN_LINK | FROZEN | YES | NO blocking debt | battle Chain Freeze Record |
| 690087 | DAMAGE_SHARE | FROZEN | YES | NO blocking debt | state `states/functional/damage_share/MECHANISM_CONTRACT.md` |
| 690086 | DISTRIBUTION | RUNTIME_READY_WITH_RESEARCH_DEBT | YES | YES: `DSTS9-B02` empirical OPEN / UNOBSERVED | battle Distribution Freeze Record + Finalization Barrier |
| 690085 | COUNTERATTACK | FROZEN | YES | nonblocking universal comparator/dispel fidelity notes; no runtime ambiguity | battle Counterattack Freeze Record |

## DSTS9-B02 dual status

```text
Empirical Status: OPEN / UNOBSERVED
Runtime Status: CLOSED BY EXPLICIT PROJECT_RUNTIME_DEFAULT
Design Admission: NOT BLOCKING
Research Debt: YES
```

Runtime default: an already admitted `DistributionTransaction` completes its planned local commits before handing control to the finalization barrier. This is explicitly a **project runtime default, not empirically proven official game behavior**.

## Stage 8 boundary

```text
Stage8 = FROZEN
Formal Stage8 Reopen = NO
```

Stage 9 wraps / coordinates / derives around Stage 8 seams. It does not replace Stage 8 formula ownership or the Stage 8 Damage Pipeline.

## Historical authority classification

- `audits/*_CONTRACT_AUDIT.md` = HISTORICAL independent audits; findings remain immutable history.
- [`STAGE9_OPEN_FINDING_CONSOLIDATION.md`](../audits/STAGE9_OPEN_FINDING_CONSOLIDATION.md) = HISTORICAL CONSOLIDATION SNAPSHOT, superseded for current status by RF-P01..P07 + RF-C01 + RF-C02.
- `research/core_arbitration_v2/R1..R8` = HISTORICAL evidence/research reports where later P0 has re-frozen a boundary.
- state repo `minimum_usable` entries with formal P0 = SUPERSEDED compatibility navigation.

## Design admission boundary

```text
Architecture blockers = 0
Runtime ambiguities = 0
RF-C01 hardening findings open = 0
RF-C02 DOC_DRIFT open = 0
STAGE9 DESIGN ADMISSION = READY
STAGE9.md = NOT CREATED
```

Next step is the Stage9 Global Cross-Mechanism Final Audit. RF-C02 does not execute it.
