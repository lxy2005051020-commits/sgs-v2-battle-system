# Stage 9 Phase 9.3 Repair Report (Round 1)

Phase:
9.3 Repair Round 1 — Target Resolution + Authority Alignment

Round 1 Repair Commit:
5367b2e1996ebc9fa2a97fd1324e17cc817da852

Round 1 Parent (Implementation Commit):
d00df3b4d7cd28a092bce16c3e53902888518c2f

Implementation Commit Parent:
5458db83a1893e5d5557c1e4ca94d05909d45779

Build Prompt Blob:
835206ba39ce64c42a822a7138afeee307e0a492

---

## 1. Executive Summary

Phase 9.3 implementation commit `d00df3b4d7cd28a092bce16c3e53902888518c2f` was rejected at the exit gate due to 6 specific authority violations against frozen architecture and state contracts (Confusion P0, Taunt P0, Guard P0).
This repair systematically resolves all 6 findings with minimal surgical changes, strictly adheres to the frozen authorities, updates affected tests, and adds 13 explicit regression tests.

---

## 2. Findings Resolved

### P93-M01: Stage9StateRuntime Dependency Injection
- **Issue**: `Stage9StateRuntime.__init__` had a default fallback to construct `StateLifecycleSystem()`, bypassing proper dependency injection and risking lifecycle system fragmentation.
- **Fix**: Constructor injection of `state_lifecycle_system: StateLifecycleSystem` is now required and type-validated. `StateLifecycleSystem()` default instantiation fallback removed. Production composition root confirmed in `BattleSystems`.

### P93-M02: NormalAttackInstanceId Generator Ownership
- **Issue**: `TargetResolutionSystem.resolve()` auto-allocated `NormalAttackInstanceId` if None, violating generator ownership (NormalAttackSystem is sole generator).
- **Fix**: `normal_attack_id: NormalAttackInstanceId` is now a required keyword-only argument. If None or missing, TypeError is raised. TargetResolutionSystem allocates only `TargetResolutionId`.

### P93-B01: Insight vs Confusion Runtime Suppression
- **Issue**: `Stage9StateRuntime.get_operational_confusion` checked `has_operational_insight` at JIT targeting resolution, suppressing active Confusion.
- **Fix**: In frozen Confusion P0, Insight is *application immunity only* (prevents new application), NOT runtime suppression of existing instances. Removed the ad-hoc `has_operational_insight` check from `get_operational_confusion`.

### P93-B02: Taunt Forced Target Authority
- **Issue**: `get_taunt_target_unit_id` allowed `TauntStateParams.taunt_target_id` to override `instance.source_id`, and `get_operational_taunt` contained an ad-hoc targeting Insight filter.
- **Fix**: In frozen Taunt P0, the authoritative forced target is strictly `instance.source_id` (the taunter). `get_taunt_target_unit_id` returns `instance.source_id`. Removed ad-hoc Insight check from `get_operational_taunt`.

### P93-B03: Guard Physical Ownership & Single-Pass Representation
- **Issue**: Guard allowed reverse representation (where protector is holder and holder owns state with `guarded_unit_id`).
- **Fix**: In frozen Guard P0, State_Owner = PROTECTED_TARGET / HOLDER. Linked protector is represented as `protector_id` on `GuardStateParams` (falling back to `instance.source_id`). Protector-owned reverse Guard is strictly rejected. Single-pass non-recursive resolution enforced.

### P93-M03: Confusion Candidate Pool TargetSystem Primitives
- **Issue**: Confusion candidate pool bypassed TargetSystem using raw list comprehension over `context.units.values()`.
- **Fix**: Candidates are now constructed strictly via TargetSystem primitives: `self._target_system.allies(context, attacker_unit, alive_only=True, include_self=False) + self._target_system.enemies(context, attacker_unit, alive_only=True)`. `TargetSystem.allies` updated with `include_self: bool = True` parameter. Exactly 1 RNG call consumed when multiple candidates exist; 0 when single candidate.

---

## 3. Production Files Modified

- `sgs_v2/battle_core/stage9_state_params.py`:
  - Updated `GuardStateParams` to have `protector_id: str | None = None` (replacing `guarded_unit_id`).
- `sgs_v2/battle_core/stage9_state_runtime.py`:
  - Enforced explicit `StateLifecycleSystem` constructor injection.
  - Removed ad-hoc Insight suppression in `get_operational_confusion` and `get_operational_taunt`.
  - `get_taunt_target_unit_id` returns strictly `instance.source_id`.
  - `get_guard_protector` checks holder-owned Guard only, rejecting protector-owned reverse Guard.
- `sgs_v2/battle_core/target_resolution_system.py`:
  - Required `normal_attack_id: NormalAttackInstanceId` in `resolve()`.
  - Replaced raw comprehension with `TargetSystem.allies(..., include_self=False) + TargetSystem.enemies(...)`.
- `sgs_v2/battle_core/target_system.py`:
  - Added `include_self: bool = True` to `allies()`.

---

## 4. Test Verification Summary

- Total tests: 428 passed, 0 failed (100% PASS).
- Demo verification: python demo.py runs cleanly to completion.

### Explicit Authority Regression Contracts
| Contract ID | Description | Status |
| :--- | :--- | :--- |
| **ARCH-P93-01** | Stage9StateRuntime cannot self-construct StateLifecycleSystem | PASS |
| **ARCH-P93-02** | BattleSystems is production composition root for Stage9StateRuntime | PASS |
| **ARCH-P93-03** | TargetResolutionSystem cannot allocate NormalAttackInstanceId | PASS |
| **ARCH-P93-04** | TargetResolutionSystem allocates only TargetResolutionId | PASS |
| **P0-CFS-P93-01** | Insight application immunity is not silently reinterpreted as JIT Confusion suppression | PASS |
| **P0-TNT-P93-01** | Taunt forced target comes from authoritative source identity | PASS |
| **P0-TNT-P93-02** | Taunt existing-state suppression is not an ad-hoc targeting Insight filter | PASS |
| **P0-GRD-P93-01** | Guard physical holder = protected target | PASS |
| **P0-GRD-P93-02** | Protector identity is explicit and immutable | PASS |
| **P0-GRD-P93-03** | Protector-owned reverse Guard representation rejected | PASS |
| **P0-GRD-P93-04** | Guard remains single-pass | PASS |
| **TARGET-P93-01** | Confusion legal candidate construction consumes TargetSystem authority | PASS |
| **TARGET-P93-02** | No extra RNG call introduced | PASS |
| **REG-TGT-01** | Confusion shadows Taunt selector | PASS |
| **REG-TGT-02** | Taunt lifecycle continues while selector is shadowed | PASS |
| **REG-TGT-03** | Guard occurs after selector | PASS |
| **REG-TGT-04** | Guard is single-pass | PASS |

---

## 5. Scope Boundary Compliance

- Phase 9.4 NOT started (no damage_instance_coordinator.py, no DamageSettlementRequest route).
- NormalAttack master cutover NOT performed.
- ActionScope NOT implemented.
- Stage 8 damage/modifier/troop-loss formulas 100% untouched.
