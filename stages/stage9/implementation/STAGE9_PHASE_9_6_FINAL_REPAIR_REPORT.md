# Stage9 Phase 9.6 Final Repair Report

## Baseline Authority

- **Starting remote main**: `13204fa2e0f78a95cb941731a595f05c29642671`
- **Parent commit**: `13204fa2e0f78a95cb941731a595f05c29642671`
- **Build Prompt blob**: `835206ba39ce64c42a822a7138afeee307e0a492`
- **State authority**: `15ed915435f328a6ecd8f488d98b5b9e13c913b5`

---

## Final Audit Finding Dispositions

### 1. FR96-B01: ActionScope Production Construction & Execution FutureAdmission Bypass (High)
- **Status**: **CLOSED**
- **Resolution**:
  - Defined `ActionExecutionState` enum (`ADMITTED`, `EXECUTING`, `COMPLETED`, `TERMINAL`).
  - Hardened `ActionScope` with `execution_state: ActionExecutionState`, `_coordinator: BattleFinalizationCoordinator | None`, and `_owning_context_id: int | None`.
  - Updated `admit_action_scope` to bind the issuing coordinator and context ID, registering the exact scope object in `coordinator._active_action_scopes`.
  - Added `BattleFinalizationCoordinator.validate_action_scope` to verify context binding, exact object identity (`is`), actor ownership (`scope.actor_id == expected_actor_id`), terminal state, and execution state (`ADMITTED`).
  - Added upfront capability authentication in `ActionSystem.execute` before any side effects (before Combo action start maintenance, grant creation, STUN checks, and normal attack). Transitioned `execution_state` immediately to `EXECUTING` to prevent replay.

### 2. FR96-B02: Combo #2 Execution when FutureAdmissionGate is Absent (High)
- **Status**: **CLOSED**
- **Resolution**:
  - In `NormalAttackSystem._execute_single_hit`, inside the Combo Checkpoint before #2 admission:
    ```python
    if self._future_admission_gate is None:
        raise RuntimeError(
            "NormalAttackSystem requires FutureAdmissionGate to admit COMBO_SECOND_NORMAL_ATTACK"
        )
    ```
  - Strictly enforces fail-closed behavior: when the gate is absent, no NormalAttack ID is allocated, no target resolution occurs, no damage is calculated, and no troop loss is applied.

### 3. FR96-M01: ComboCheckpointState Transition Order (Medium)
- **Status**: **CLOSED**
- **Resolution**:
  - Aligned with frozen state mechanics ordering:
    1. Local pre-checkpoint gates (actor alive, battle not latched/finalized). If failing, returns `hit_result` with checkpoint remaining `NOT_REACHED`.
    2. Checkpoint reached: marks `action_scope.combo_checkpoint_state = ComboCheckpointState.REACHED`.
    3. Grant validation: `grant = action_scope.combo_grant`. If missing or invalid (e.g. physically removed), returns `hit_result` with checkpoint remaining `REACHED`.
    4. Valid grant: atomic consume (`grant.consume()`), marks `combo_checkpoint_state = ComboCheckpointState.CONSUMED`, publishes `COMBO_OPPORTUNITY_CONSUMED`, then proceeds to can_normal_attack checks and #2 admission.
  - Updated `REG-CMB-02` test assertion to verify `combo_checkpoint_state == ComboCheckpointState.REACHED`.

---

## Regression & Invariant Verification Matrix

| Test Identifier | Finding / Contract | Result | Details |
|---|---|---|---|
| `test_fr96_act_01_direct_constructed_scope_without_coordinator_rejected` | `FR96-B01` | **PASS** | Direct constructor call without capability origin rejected with `RuntimeError` |
| `test_fr96_act_02_identity_mismatch_forged_scope_rejected` | `FR96-B01` | **PASS** | Scope with duplicate values but forged object identity rejected with `ValueError` |
| `test_fr96_act_03_actor_mismatch_rejected_before_side_effects` | `FR96-B01` | **PASS** | Scope actor mismatch rejected before side effects; physical count remains 0 |
| `test_fr96_act_04_execution_state_transition_prevents_replay` | `FR96-B01` | **PASS** | `ADMITTED` -> `EXECUTING`; second execution attempt rejected with `RuntimeError` |
| `test_fr96_act_05_terminal_scope_rejected` | `FR96-B01` | **PASS** | Scope in `TERMINAL` state cannot be executed |
| `test_fr96_cmb_01_combo_second_attack_without_gate_fails_closed` | `FR96-B02` | **PASS** | Missing gate on NA #2 raises `RuntimeError`, fails closed |
| `test_fr96_cmb_02_no_grant_checkpoint_remains_reached` | `FR96-M01` | **PASS** | Without grant, checkpoint reaches boundary and remains `REACHED` |
| `test_reg_cmb_02_physical_remove_revokes_unconsumed_grant` | `REG-CMB-02` / `FR96-M01` | **PASS** | Physically removed state leaves grant revoked and checkpoint `REACHED` |
| `tests/test_stage9_phase_9_6_normal_attack.py` | Phase 9.6 suite | **PASS** | 43 / 43 passed in 0.27s |
| Full pytest test suite | Complete test suite | **PASS** | 572 / 572 passed in 1.12s |
| Simulation demo (`python demo.py`) | Production engine | **PASS** | 7 rounds complete simulation |

---

## Architectural & Boundary Checks

- **Stage8 Integrity**: Zero changes to Stage8 damage formulas, modifiers, or policies.
- **Phase 9.7 Boundary**: No Cleave, Chain, Counter, or ReactionBatch code introduced. Seam remains closed.
- **Frozen State Authority**: 100% compliant with `sgs-state-mechanics-research` commit `15ed915435f328a6ecd8f488d98b5b9e13c913b5`.
- **Authorized Build Prompt**: Zero drift on `stages/stage9/STAGE9_BUILD_PROMPT.md` (`835206ba39ce64c42a822a7138afeee307e0a492`).

---

## Final Re-Audit Verdict

**ALL AUDIT FINDINGS RESOLVED (PASS). STAGE9 PHASE 9.6 IS COMPLETE.**

---

## Final Re-Audit Round 2 = FAIL

An independent re-audit identified 4 capability closure gaps:
1. **FR96-R2-B01**: BattleFinalizationCoordinator public ActionScope admission bypass (caller could directly register arbitrary ActionScope or naked ActionId, bypassing NEXT_ACTION FutureAdmissionPermit).
2. **FR96-R2-B02**: Mutable ActionScope fields are incorrectly used as admission/replay authority (mutating scope.actor_id, execution_state, terminal could bypass ownership and replay guards).
3. **FR96-R2-B03**: NormalAttackSystem can use/replay Stage9 ActionScope outside ActionSystem lifecycle (merely ADMITTED scope could execute physical NA, and second primary NA could execute for the same Action).
4. **FR96-R2-M01**: ActionScope completion is ActionId-only and terminal/completed lifecycle authority is split (barrier removal did not require exact ActionScope capability).

**Phase 9.6 Capability Closure Repair**: REQUIRED.
