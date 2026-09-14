# Stage9 Phase 9.6 Terminal Capability Repair Report

## Baseline Authority

- **Starting remote**: `9d2b1788b34e2656152c33421d41e5ba86745322`
- **Build Prompt blob**: `835206ba39ce64c42a822a7138afeee307e0a492`
- **State authority**: `15ed915435f328a6ecd8f488d98b5b9e13c913b5`

---

## Root Cause & Architecture Repair

### FR96-R3-B01
- **Vulnerability**: `ActionScope.mark_terminal()` invoked `coordinator._mark_action_scope_terminal(self.action_id)` which directly mutated coordinator-owned `ActionScopeAdmissionRecord.execution_state` using only `ActionId`. This allowed a forged `ActionScope` with identical `action_id` to terminalize the coordinator's record without validating exact scope capability identity, context binding, or actor ownership, thereby releasing the admitted-work finalization barrier early.
- **Resolution**:
  1. **Removed ActionId-only mutation seam**: Deleted `_mark_action_scope_terminal` helper from `BattleFinalizationCoordinator`.
  2. **Decoupled projection from authority**: Modified `ActionScope.mark_terminal()` to only update its local compatibility/projection fields (`self.terminal = True`, `self.execution_state = ActionExecutionState.TERMINAL`). It does not mutate or access coordinator authoritative records.
  3. **Direct capability completion in BattleEngine**: Removed caller-side `action_scope.mark_terminal()` from `BattleEngine.run()` finally block. Engine now directly invokes `coordinator.complete_action_scope(context, action_scope)`.
  4. **Strict single lifecycle authority**: The coordinator's `ActionScopeAdmissionRecord.execution_state` remains the sole lifecycle authority for barrier drainage (`active_action_scope_ids`, `has_admitted_work`), normal attack execution permission, and replay prevention.
  5. **Exact scope capability barrier release**: Only the exact legitimate `ActionScope` passed to `coordinator.complete_action_scope` can transition the coordinator record to `COMPLETED` and release the admitted work barrier.

---

## Verification & Metric Matrix

| Check / Contract | Status | Details |
|---|---|---|
| Starting remote | `9d2b1788b34e2656152c33421d41e5ba86745322` | Exact match |
| Build Prompt blob | `835206ba39ce64c42a822a7138afeee307e0a492` | Exact match |
| State authority | `15ed915435f328a6ecd8f488d98b5b9e13c913b5` | Exact match |
| ActionScope lifecycle authority | **COORDINATOR ONLY** | Coordinator record is the sole authority |
| ActionId-only terminal mutation | **BLOCKED** | Helper removed, ActionId cannot mutate state |
| Forged same-id terminalization | **BLOCKED** | Forged scope mark_terminal cannot alter legitimate record |
| Forged terminalization releases barrier | **NO** | Barrier remains held while legitimate scope executes |
| Legitimate exact completion | **PASS** | Exact capability releases barrier |
| Completion exactly once | **PASS** | Duplicate completion rejected with RuntimeError |
| Victory drain preserved until exact completion | **PASS** | Termination state remains draining until legitimate completion |
| FR96-R3-01..06 | **PASS** | All 6 new regression tests pass |
| FR96-R2-A01..A13 | **PASS** | All Phase 9.6 round 2 tests pass |
| REG-TGT-05..07 | **PASS** | Target resolution regression suite passes |
| REG-CMB-01..05 | **PASS** | Combo state & grant regression suite passes |
| INV-06..12 | **PASS** | Runtime invariant contracts pass |
| INV-39..42 | **PASS** | Victory barrier and lineage authority pass |
| Stage8 reopen | **NO** | Zero modifications to Stage 8 damage formulas |
| Phase9.7 leakage | **0** | Zero Phase 9.7 mechanics implemented |
| Tests | **PASS** | 62 / 62 Phase 9.6 tests; 591 / 591 full test suite |
| Demo | **PASS** | `python demo.py` finishes complete 7-round battle |
| Terminal Capability Repair Gate | **PASS** | All requirements fulfilled |

---

## Lifecycle Status

- **Phase 9.1..9.5**: COMPLETE / PASS
- **Phase 9.6 Implementation**: COMPLETE
- **Phase 9.6 Independent Audit**: FAIL
- **Phase 9.6 Audit Repair #1**: COMPLETE
- **Phase 9.6 Final Re-Audit #1**: FAIL
- **Phase 9.6 Final Repair #1**: COMPLETE
- **Phase 9.6 Final Re-Audit Round 2**: FAIL
- **Phase 9.6 Capability Closure Repair**: COMPLETE
- **Phase 9.6 Final Re-Audit Round 3**: FAIL
- **Phase 9.6 Terminal Capability Repair**: COMPLETE / PASS
- **Phase 9.7**: NOT AUTHORIZED / NOT STARTED
