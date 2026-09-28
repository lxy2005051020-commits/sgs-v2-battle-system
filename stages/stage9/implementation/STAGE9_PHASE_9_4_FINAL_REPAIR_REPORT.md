# Stage9 Phase 9.4 Final Repair Report

## Phase Information

Phase:
9.4 Final Repair — DamageInstance BattleContext Ownership Boundary

Starting remote main:
c7ebbd1d80a29c0f947a61afe73ef732aebd0a6b fix(stage9): close phase 9.4 damage instance lifecycle

Parent:
c7ebbd1d80a29c0f947a61afe73ef732aebd0a6b

State authority baseline:
15ed915435f328a6ecd8f488d98b5b9e13c913b5

Build Prompt blob:
835206ba39ce64c42a822a7138afeee307e0a492

Lifecycle status:
Phase 9.1 = COMPLETE / PASS
Phase 9.2 = COMPLETE / PASS
Phase 9.3 = COMPLETE / PASS
Phase 9.4 Final Repair = COMPLETE / PASS
Phase 9.5 = NOT AUTHORIZED

---

## 1. Audit Finding Addressed: FINAL-B01

### DamageInstance BattleContext Ownership Boundary
- **Root Cause**:
  In Phase 9.4 Round 2, `DamageInstanceCoordinator` tracked active instances and permits solely by their ID strings (`DamageInstanceId` / `permit_id`). Although `BattleContext` was passed to certain methods, the active records and permits did not enforce strict ownership binding to the originating `BattleContext`. Passing `context=None` was not strictly rejected by type checks, and cross-battle permit consumption could either destroy valid capability permits before verification or fail to detect context mismatch. Furthermore, if two concurrent `BattleContext`s had synchronized ID allocator counters (e.g. both beginning at `dmg_1`), they would collide in coordinator state.
- **Architectural Resolution**:
  1. **Strict Context Binding**:
     - `_ActiveDamageInstanceRecord` and `_PermitRecord` now hold `owning_context: BattleContext`.
     - Coordinator state is partitioned by context identity:
       `_active_instances` is keyed by `(id(context), damage_instance_id)`.
       `_permits` is keyed by `(id(context), permit_id)`.
  2. **Rejection of context=None**:
     - `begin_damage_instance(context, lineage)` and `allocate_damage_instance_id(context)` require a valid `BattleContext` instance; passing `None` immediately raises `TypeError` without mutating any state.
  3. **Allocator Authority**:
     - All IDs (`DamageInstanceId` and permit IDs) are strictly allocated via `context.id_allocator`.
  4. **Pre-Consumption Cross-Context Verification**:
     - In `validate_and_consume_permit(context, permit, request)`:
       The coordinator first verifies whether `permit` was issued for a different `BattleContext`. If so, it raises `ValueError` **before** marking the permit consumed, ensuring that cross-context misuse does not destroy the legitimate capability on its home context.
  5. **Post-Rejection Usability**:
     - A permit rejected due to cross-context invocation remains valid and can subsequently settle on its legitimate owning `BattleContext` exactly once.
  6. **Zero Memory Leak / Zero Battle-Long Tombstones**:
     - Operation-local scopes are cleanly released upon instance completion (`close_damage_instance`), ensuring `_active_instances` and `_permits` return to empty with zero memory residue.

---

## 2. Verification Matrix

| Test ID | Verification Target | Result |
| :--- | :--- | :--- |
| **P94-FR-01** | `begin_damage_instance(ctx_A, lineage)` binds active record to `ctx_A` | **PASS** |
| **P94-FR-02** | `begin_damage_instance(None, lineage)` raises `TypeError` without state mutation | **PASS** |
| **P94-FR-03** | Cross-context settlement rejected before consume; 0 troop mutation, 0 events on both contexts | **PASS** |
| **P94-FR-04** | Rejected permit remains usable on original `ctx_A` exactly once; subsequent settlement rejected | **PASS** |
| **P94-FR-05** | `issue_settlement_permit(dmg_id, lineage, context=wrong_ctx)` raises `ValueError` ("Supplied context does not match") | **PASS** |
| **P94-FR-06** | Concurrent `BattleContext`s with identical ID sequence (`dmg_1`) run isolated on same coordinator | **PASS** |
| **P94-R2-01..07** | Round 2 DamageInstance lifecycle and permit cardinality suite | **PASS** |
| **P94-R01..07** | Round 1 regression suite | **PASS** |

---

## 3. System-Wide Verification & Invariant Audit

1. **Test Suite Status**:
   - `python -m pytest -q` passed 483/483 tests (100% pass rate).
   - `python demo.py` executed complete 7-round battle simulation with zero errors.
2. **Three-Layer Separation Invariant**:
   - Distinct values maintained for `Dtotal`, `Dtarget`, and `actual_target_troop_loss`.
3. **Stage 8 Invariant Preservation**:
   - 0 modifications to Stage 8 damage calculation formulas, modifier policies, or prevention rules.
4. **EffectExecutor Invariant**:
   - Production routing remains legacy; 0 premature cutovers.
5. **Phase 9.5 Invariant**:
   - 0 Phase 9.5 files created; zero execution of damage share/distribution or direct troop loss systems.

---

## 4. Final Re-Audit

Final Re-Audit:
FAIL

Remaining findings:
FR2-B01 same-value cross-context permit alias
FR2-B02 contextless close/release ambiguity

