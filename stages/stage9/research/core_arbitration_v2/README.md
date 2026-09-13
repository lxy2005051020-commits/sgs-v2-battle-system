# Stage 9 Core Arbitration V2 — Research Archive & Current Navigation

> **RF-C02 status**: current-facing navigation synchronized on 2026-09-13.  
> **Role**: research evidence archive + links to current P0.  
> **Not authority**: historical R1-R8 wording does not override later Freeze Records / Repair Packages / shared P0.

## Current authority entry

- [Stage 9 current README](../../README.md)
- [RF-C02 Stage 9 Authority Map](../../docsync/STAGE9_AUTHORITY_MAP.md)
- [RF-C02 Documentation Sync Report](../../docsync/RF_C02_DOCUMENTATION_SYNC_REPORT.md)

## Shared arbitration P0

- [STAGE9_CORE_ARBITRATION_RULES_V2.md](STAGE9_CORE_ARBITRATION_RULES_V2.md)
- [STAGE9_EXECUTION_RIGHT_AND_DEATH_SCOPE_CONTRACT.md](STAGE9_EXECUTION_RIGHT_AND_DEATH_SCOPE_CONTRACT.md)
- [STAGE9_BATTLE_FINALIZATION_BARRIER_CONTRACT.md](STAGE9_BATTLE_FINALIZATION_BARRIER_CONTRACT.md)

Later Repair Packages explicitly supersede older research wording only on the repaired boundary. In particular, universal death-abort and universal own-open-action death-continuation summaries are historical; current death/finalization semantics are owned by the two shared P0 contracts above.

## Mechanism Freeze Records

- [CLEAVE](STAGE9_CLEAVE_MECHANICS_FREEZE_RECORD.md)
- [CHAIN_LINK](STAGE9_CHAIN_MECHANICS_FREEZE_RECORD.md)
- [DAMAGE_SHARE](STAGE9_DAMAGE_SHARE_MECHANICS_FREEZE_RECORD.md)
- [DISTRIBUTION](STAGE9_DISTRIBUTION_MECHANICS_FREEZE_RECORD.md)
- [COUNTERATTACK](STAGE9_COUNTERATTACK_MECHANICS_FREEZE_RECORD.md)
- [TAUNT](STAGE9_TAUNT_MECHANICS_FREEZE_RECORD.md)
- [GUARD battle mirror](../../STATE_690098_GUARD_MECHANISM_CONTRACT.md)

COMBO、CONFUSION、CLEAVE、DAMAGE_SHARE、GUARD 的 current mechanism authority 还在 state-mechanics repo 中拥有正式 P0；跨仓 authority ownership 见 RF-C02 Authority Map，避免把多个镜像误当成互相竞争的 P0。

## Evidence Matrix

- [STAGE9_EVIDENCE_MATRIX_V2.md](STAGE9_EVIDENCE_MATRIX_V2.md) — historical evidence trace + current contract overlay after RF-C02.

## R1-R8 historical evidence reports

以下文件保持 **HISTORICAL**，用于证据来源、样本与研究过程追踪；当其状态词、死亡全称规则或旧术语与 later P0 不一致时，不是 current implementation authority：

- [R1 Attack Lifecycle / Reaction Order](R1_ATTACK_LIFECYCLE_AND_REACTION_ORDER.md)
- [R2 Target Redirect / Guard](R2_TARGET_REDIRECT_AND_GUARD.md)
- [R3 Damage Derivation Pipeline](R3_DAMAGE_DERIVATION_PIPELINE.md)
- [R4 Recursion Permission Matrix](R4_RECURSION_PERMISSION_MATRIX.md)
- [R5 Death Termination Matrix](R5_DEATH_TERMINATION_MATRIX.md)
- [R6 Multi-source Rules](R6_MULTI_SOURCE_RULES.md)
- [R7 RNG / Determinism](R7_RNG_AND_DETERMINISM.md)
- [R8 Provenance Model](R8_PROVENANCE_MODEL.md)

Canonical terminology in current navigation:

```text
CLEAVE / 群攻          (legacy SPLASH allowed only in historical material / legacy filename)
DAMAGE_SHARE / 分担
DISTRIBUTION / 分摊
CHAIN_LINK / 铁索连环
COUNTERATTACK / 反击
COMBO / 连击
RESISTANCE / 抵御      (legacy Barrier wording is historical)
```

## Current research gate

```text
Nine Stage9 mechanisms: runtime-ready
Architecture blockers: 0
Runtime ambiguities: 0
DSTS9-B02 empirical debt: OPEN / UNOBSERVED
DSTS9-B02 runtime: CLOSED BY EXPLICIT PROJECT_RUNTIME_DEFAULT
Stage8: FROZEN
Formal Stage8 Reopen: NO
STAGE9.md: NOT CREATED
```

There is no “Next Core Research Target = CONFUSION/COMBO” here anymore. The next project step is the Stage9 Global Cross-Mechanism Final Audit, outside RF-C02.
