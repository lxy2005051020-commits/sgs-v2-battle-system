# Stage9 Phase 9.6 Capability Closure Report

## Baseline Authority

- **Starting remote main**: `bda47588b09599322d33ddb0a815dd5eb77ac9d4`
- **Parent commit**: `bda47588b09599322d33ddb0a815dd5eb77ac9d4`
- **Build Prompt blob**: `835206ba39ce64c42a822a7138afeee307e0a492`
- **State authority**: `15ed915435f328a6ecd8f488d98b5b9e13c913b5`

---

## Capability Closure Finding Dispositions

### 1. FR96-R2-B01: Coordinator Direct ActionScope Admission Bypass (High)
- **Status**: **CLOSED**
- **Disposition**:
  - Direct public admission via `coordinator.admit_action_scope` is completely blocked (raises `RuntimeError` on ActionScope, `TypeError` on naked ActionId).
  - The only legitimate path to an admitted ActionScope is:
    `BattleEngine -> FutureAdmissionGate.request_admission(NEXT_ACTION) -> authentic FutureAdmissionPermit -> admit_action_scope factory consumes permit -> ActionId allocation -> ActionScope construction -> private coordinator._register_admitted_action_scope`.

### 2. FR96-R2-B02: Mutable ActionScope Fields Used as Admission/Replay Authority (High)
- **Status**: **CLOSED**
- **Disposition**:
  - `BattleFinalizationCoordinator` now creates and owns an immutable `ActionScopeAdmissionRecord` at registration containing the ActionId, actor_id snapshot, exact scope object reference, owning_context_id, execution_state, and primary NormalAttack consumption flag.
  - Mutating `scope.actor_id` cannot alter admission ownership (`test_fr96_r2_a03`).
  - Mutating `scope.execution_state` or `scope.terminal` cannot bypass replay or reopen scope (`test_fr96_r2_a04`, `test_fr96_r2_a05`).
  - Coordinator's record state machine (`ADMITTED -> EXECUTING -> COMPLETED / TERMINAL`) is the sole lifecycle authority.

### 3. FR96-R2-B03: NormalAttackSystem Can Use/Replay Stage9 ActionScope Outside ActionSystem Lifecycle (High)
- **Status**: **CLOSED**
- **Disposition**:
  - `NormalAttackSystem.execute` now verifies that the provided `ActionScope` is authentic, belongs to current BattleContext, matches the admission actor snapshot, and is currently in the `EXECUTING` lifecycle state.
  - Merely `ADMITTED` scopes are rejected with `RuntimeError` (`test_fr96_r2_a06`), resulting in 0 physical count and 0 NA IDs.
  - Enforced single primary NormalAttack entry per Action: once consumed, calling `NormalAttackSystem.execute` again with the same scope is rejected (`test_fr96_r2_a07`).
  - Total physical NormalAttacks per Action strictly capped at $\le 2$ under replay and direct API abuse (`test_fr96_r2_a08`).

### 4. FR96-R2-M01: ActionScope Completion is ActionId-Only and Lifecycle Authority is Split (Medium)
- **Status**: **CLOSED**
- **Disposition**:
  - `coordinator.complete_action_scope` now requires the exact authentic `ActionScope` capability, rejecting naked `ActionId` (`TypeError`) and imposter scopes (`ValueError`).
  - Scope can be completed exactly once; duplicate completion is rejected with `RuntimeError` (`test_fr96_r2_a11`).
  - Unified lifecycle state to coordinator-owned `execution_state` (`ADMITTED -> EXECUTING -> COMPLETED / TERMINAL`). `scope.terminal` is a projection.

### 5. Context Pre-Validation Gaps
- **Status**: **CLOSED**
- **Disposition**:
  - `admit_action_scope` pre-validates `context` against coordinator before permit consumption and before ActionId allocation (`test_fr96_r2_a12`).
  - `AssaultDispatchPort.dispatch` pre-validates `context` against coordinator before permit consumption (`test_fr96_r2_a13`).

---

## Verification Matrix

| Check / Contract | Status | Details |
|---|---|---|
| Coordinator direct ActionScope admission bypass | **BLOCKED** | Direct call raises `RuntimeError` |
| ActionId-only admission bypass | **BLOCKED** | Direct call raises `TypeError` |
| Actor ownership snapshot | **PASS** | Coordinator validates against immutable snapshot |
| Mutable `actor_id` bypass | **BLOCKED** | Mutated actor rejected before side effects |
| Mutable `execution_state` replay | **BLOCKED** | Mutated state rejected by coordinator record |
| NormalAttack direct ActionScope bypass | **BLOCKED** | Merely `ADMITTED` scope rejected |
| Primary NA per Action | **<= 1** | Multiple primary entries rejected |
| Total physical NA per Action | **<= 2** | Capped at 2; replay attempts fail |
| Completion exact-scope authenticity | **PASS** | Exact object identity verified |
| ActionId-only completion | **BLOCKED** | Naked ActionId rejected with `TypeError` |
| Completion replay | **BLOCKED** | Second completion raises `RuntimeError` |
| Action lifecycle single authority | **PASS** | Coordinator record owns state machine |
| Cross-context admission pre-validation | **PASS** | Rejected before permit consume and ID allocation |
| Assault cross-context permit consumption | **BLOCKED** | Rejected before permit consume |
| REG-TGT-05..07 | **PASS** | Fresh resolution, live Guard, pre-guard intended preserved |
| REG-CMB-01..05 | **PASS** | Action start maintenance, revoke on remove, suppress, atomic consume, death cancel |
| INV-06..12 | **PASS** | Runtime identities, counts, and caps verified |
| INV-39..42 | **PASS** | Victory latch, coordinator single owner, lineage |
| Stage8 reopen | **NO** | No formulas, modifiers, or policies modified |
| Phase 9.7 leakage | **0** | No Cleave, Chain, Counter, ReactionBatch |
| Tests | **PASS** | 56 / 56 Phase 9.6 tests; 585 / 585 full suite tests |
| Demo (`python demo.py`) | **PASS** | 7 rounds complete simulation |
| Capability Closure Gate | **PASS** | All findings closed |

---

## Conclusion

Phase 9.6 Capability Closure Repair is COMPLETE. All capability bypasses, mutable authority leaks, and completion gaps are closed.
