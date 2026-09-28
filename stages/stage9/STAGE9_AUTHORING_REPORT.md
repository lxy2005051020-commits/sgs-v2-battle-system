# Stage9 Implementation Specification Authoring Report

> Date: 2026-09-13  
> Scope: Stage9 Implementation Design Authority authoring only  
> Verdict target: `STAGE9 SPEC AUTHORED — DESIGN AUDIT REQUIRED`

## 1. Baseline

```text
battle repository:
lxy2005051020-commits/sgs-v2-battle-system
remote main at authoring start:
4745d061345181aaf12c454ada9890d7b69c5598

authority/state repository:
lxy2005051020-commits/sgs-state-mechanics-research
remote main at authoring start:
15ed915435f328a6ecd8f488d98b5b9e13c913b5
```

No battle-report corpus research was run. The state repository was read-only and was not modified.

## 2. Admission

Consumed gate:

```text
STAGE9_PRE_SPEC_DELTA_AUDIT
DELTA VERDICT = PASS
STAGE9 SPEC AUTHORING ADMISSION = READY
Remaining blocking findings = 0
Remaining pre-spec findings = 0
P0 semantic change = 0
Runtime ambiguity = 0
P0 conflict = 0
Stage8 reopen = NO
```

`DSTS9-B02` remained:

```text
EMPIRICAL OPEN / UNOBSERVED
RUNTIME CLOSED BY PROJECT_RUNTIME_DEFAULT
DESIGN NON-BLOCKING
RESEARCH DEBT YES
```

## 3. Inputs Re-read

Current authoring inputs included:

- Stage9 Authority Map;
- Global Cross-Mechanism Final Audit;
- Pre-Spec Delta Audit;
- RF-C01 typed runtime contracts;
- all 42 RF-C01 runtime invariants;
- all 45 RF-C01 regression contracts;
- RF-P01..RF-P07 authority bridge set;
- shared Core Arbitration / Execution Right / Finalization P0;
- current mechanism P0/Freeze authority referenced by the map;
- Stage8 `STAGE8.md`, Design Freeze and Freeze Record;
- current production architecture under `sgs_v2/battle_core/`;
- current tests layout and existing API seams.

## 4. Existing Architecture Impact Decision

Chosen minimum-intrusion strategy:

```text
BattleSystems remains composition root.
ActionSystem remains Action owner.
Existing NormalAttackSystem becomes the unique master NormalAttack orchestrator.
TargetSystem remains low-level candidate/RNG seam.
DamageSystem Stage8 semantics remain untouched.
DamageResolutionSystem receives only a narrow future settlement seam.
TroopSystem remains the sole troop writer.
VictorySystem becomes pure condition evaluator under a new BattleFinalizationCoordinator.
EventBus remains facts-only.
StateRegistry/StateLifecycleSystem remain the one state runtime/write path.
EffectExecutor standard DamageEffect will route through the future DamageInstanceCoordinator.
```

No BattleEngine 2.0 was designed.

## 5. Specification Output

Created:

```text
stages/stage9/STAGE9.md
```

Top-level numbered sections:

```text
0 through 30
TOTAL = 31
```

The document covers:

- authority and Stage8 boundary;
- actual existing architecture baseline;
- global runtime topology and sequences;
- operation IDs / lineage / source identity;
- target resolution and Guard;
- NormalAttack master orchestration;
- Combo;
- partition / Share / Distribution;
- AttributedDirectTroopLoss;
- Cleave / Chain / Counter;
- execution right / operation barriers;
- finalization;
- recursion/permission policy;
- integerization;
- existing state/recovery/trigger integration;
- trace/observability;
- 42-invariant mapping;
- 45-regression mapping;
- real-path file plan;
- eight implementation phases;
- research debt and acceptance gates.

## 6. Planned File Impact

Future implementation plan, not changes in this authoring commit:

```text
planned new production files     = 16
planned modified production files = 11
existing control-flow classes planned modified = 8
implementation phases             = 8
future Stage9 test groups          = 10
```

The design explicitly marks Stage8 formula/resolver semantics as DO NOT TOUCH.

## 7. Invariant Coverage Audit

```text
RF-C01 invariants total = 42
Mapped                   = 42
Unmapped                 = 0
Contradiction            = 0
```

Every invariant is mapped to at least one of:

```text
structural guarantee
typed/runtime assertion
unit/integration/architecture/golden-trace test
```

## 8. Regression Coverage Audit

```text
Target          7/7
Combo           5/5
Cleave          5/5
Chain           4/4
Share           4/4
Distribution    4/4
Counter         5/5
Finalization    6/6
Integerization  5/5
TOTAL          45/45
Unmapped        0
Semantic conflict 0
```

No production test code was created in this round.

## 9. Authority / Semantic Drift Audit

Gameplay-affecting runtime choices are traced back to current P0, RF-Pxx or RF-C01 representation/regression contracts. Engineering-only choices are limited to class/file placement, typed composition seams, allocator/trace structure, and dependency direction.

```text
P0 semantic drift = 0
new gameplay rule = 0
Stage8 reopen = NO
```

Assault remains an ordered dispatch port only because the current production tree contains no Assault runtime. No Assault gameplay was invented.

## 10. Stage8 Boundary Audit

Authoring changed no Stage8 authority or production file.

```text
Stage8 = FROZEN
Formal Stage8 Reopen = NO
production code changes = 0
test code changes = 0
Stage8 authority changes = 0
```

The spec preserves the frozen Stage8 pipeline and `DamageResult` meaning.

## 11. Dependency Cycle Audit

Planned direction:

```text
identity / state / policy
→ target + damage-local coordinators
→ mechanism-local systems
→ NormalAttack master
→ Action / Engine
→ finalization owner
```

Mechanism-local systems return results to the master and do not import/call the master to advance lifecycle. Finalization consumes typed facts/barriers and does not import mechanism algorithms.

```text
known design dependency cycle = 0
```

## 12. Navigation Changes

Minimal navigation sync only:

```text
stages/stage9/README.md
stages/README.md
```

The stale “STAGE9.md not created / next step Global Final Audit” wording is replaced by:

```text
STAGE9.md = DRAFT — DESIGN AUDIT REQUIRED
NEXT STEP = Stage9 Design Audit Round 1
```

Root README is intentionally unchanged.

## 13. Authoring Self-Audit Verdict

```text
Authority Trace Audit       = PASS
Stage8 Boundary Audit       = PASS
42 Invariant Coverage Audit = PASS
45 Regression Mapping Audit = PASS
File Plan Completeness      = PASS
Dependency Cycle Audit      = PASS
P0 Semantic Drift Audit     = PASS
```

## 14. Final Status

```text
STAGE9.md status = DRAFT — DESIGN AUDIT REQUIRED
Stage9 FROZEN = NO
Ready for implementation = NO

FINAL VERDICT:
STAGE9 SPEC AUTHORED — DESIGN AUDIT REQUIRED

NEXT STEP:
Stage9 Design Audit Round 1
```
