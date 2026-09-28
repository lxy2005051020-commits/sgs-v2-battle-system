# Stage9 Phase 9.1 Implementation Report

Phase: `9.1 — Identity / Provenance / Exact Numeric / Permit Types`

Starting remote main baseline:
`22e8d4341b5938029d1dacfa2a2aea0f2031f93f`

Parent commit:
`22e8d4341b5938029d1dacfa2a2aea0f2031f93f`

Implementation commit:
`feat(stage9): implement phase 9.1 identity foundations`

Authorized Build Prompt:
- Path: `stages/stage9/STAGE9_BUILD_PROMPT.md`
- Blob: `835206ba39ce64c42a822a7138afeee307e0a492`

---

## 1. File Changes Summary

### New Production Files (6)
- `sgs_v2/battle_core/operation_identity.py`
- `sgs_v2/battle_core/stage9_trace.py`
- `sgs_v2/battle_core/stage9_integerization.py`
- `sgs_v2/battle_core/stage9_state_params.py`
- `sgs_v2/battle_core/reaction_permission_policy.py`
- `sgs_v2/battle_core/execution_right_system.py`

### Modified Production Files (3)
- `sgs_v2/battle_core/effects.py`
- `sgs_v2/battle_core/skill_runtime.py`
- `sgs_v2/battle_core/__init__.py`

### New Test Files (2)
- `tests/test_stage9_phase_9_1_identity_foundations.py`
- `tests/test_stage9_regression_contracts.py`

### Changed Pre-existing Test Files (0)
- None

---

## 2. Verification Results

- Pre-existing tests: **326 / 326 PASS**
- Phase 9.1 new unit & contract tests: **33 / 33 PASS**
- REG-INT-01..05 integerization vectors: **5 / 5 PASS**
- Total test suite: **364 / 364 PASS**
- Production demo (`demo.py`): **PASS**

---

## 3. Mapped Invariant Foundations

- **INV-15 (Cleave integerization is FLOOR)**: Implemented via `floor_product_int_ratio` and verified against exact vector `REG-INT-05` (`55 * 0.54 = 29.7 -> 29`).
- **INV-17 (Cleave permissions identity-driven)**: Implemented via `ReactionPermissionPolicy.can_trigger_cleave` / `can_trigger_counter` blocking recursive Cleave and Counter while permitting Chain, Share, and Distribution.
- **INV-21 (Direct troop loss provenance & identity)**: `SourceType.SHARE_DIRECT_LOSS` and `SourceType.DISTRIBUTION_DIRECT_LOSS` established as non-hit attributed loss with separate lineage and strict callback suppression.
- **INV-42 (Typed identity and lineage are semantic authority)**: `SourceType`, `OperationLineage`, typed operation IDs, and `ReactionPermissionPolicy` replace call-stack, string-based, or `battle.finished` heuristics.

---

## 4. Mapped Architecture Guarantees

- **Operation IDs never gameplay comparators**:
  All operation ID classes (`ActionId`, `NormalAttackInstanceId`, `DamageInstanceId`, `PartitionTransactionId`, `ReactionBatchId`, `CounterBatchEntryId`, `CleaveEffectId`, `ChainTraversalId`, `DirectTroopLossId`, `TargetResolutionId`, `FinalizationId`), `OperationLineage`, and permit types (`FutureAdmissionPermit`, `DamageSettlementPermit`, `FinalizationProjectionPermit`) explicitly reject relational operators (`<`, `<=`, `>`, `>=`) with `TypeError`.
- **TargetResolutionId is TRACE_ONLY**: Documented and verified as trace-only correlation identity.
- **EffectSourceRef != OperationLineage**: Pre-operation provenance and runtime operation lineage are kept strictly distinct.
- **SkillSlot domain**: Frozen to `{0, 1, 2}` (`INHERENT=0`, `LEARNED_1=1`, `LEARNED_2=2`).
- **ExactRatio**: Denominator > 0, reduced gcd, sign on numerator, canonical zero `0/1`, no generic `from_float`.
- **Trace boundedness**: Ring buffer capacity capped and oldest entries dropped upon overflow.

---

## 5. Scope & Boundary Checks

- Stage8 semantic reopen: **NO** (0 changes to Stage8 formulas/pipeline)
- P0 semantic changes: **0**
- State repo changes: **0**
- Forward dependencies on Phase 9.2+: **0**
- Production stub / TODO dependencies: **0**
- Production damage reroute: **NONE**
- Production finalization reroute: **NONE**
- Future branch production admission: **NONE**

---

## 6. Phase 9.1 Exit Gate

Verdict: **PASS**

Next permitted step: **Phase 9.2 Implementation**
