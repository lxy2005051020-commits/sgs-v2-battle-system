# Stage9 Phase 9.4 Repair Report

## Phase Information

Phase:
9.4 Repair — Typed Settlement Lifecycle & Coordinator State Hardening

Implementation commit:
a8aa1360bd86bc620e947bc28729fb19fcfa5447 feat(stage9): implement phase 9.4 settlement core

Parent:
a8aa1360bd86bc620e947bc28729fb19fcfa5447

State authority baseline:
15ed915435f328a6ecd8f488d98b5b9e13c913b5

Build Prompt blob:
835206ba39ce64c42a822a7138afeee307e0a492

Lifecycle status:
Phase 9.4 Repair = COMPLETE / PASS
Phase 9.5 = NOT AUTHORIZED

---

## 1. Findings Addressed & Technical Resolutions

### P94-M01: Legacy path must traverse typed LEGACY_COMPAT request
- **Root Cause**: resolve() and apply_result() executed troop mutation directly without forming a DamageSettlementRequest.
- **Resolution**:
  - apply_result(context, damage) constructs a typed DamageSettlementRequest(damage_result=damage, assigned_target_damage=damage.final_damage, damage_instance_id=None, lineage=None, origin=SettlementOrigin.LEGACY_COMPAT).
  - Added private execution seam _settle_legacy(context, request) strictly accepting request.origin == SettlementOrigin.LEGACY_COMPAT.
  - resolve(context, request) calculates damage and routes through apply_result() -> _settle_legacy().
  - Public signature of apply_result() remains strictly (context: BattleContext, damage: DamageResult) -> DamageResolutionResult with ZERO optional parameters.
  - settle() continues to strictly accept ONLY request.origin == SettlementOrigin.STAGE9.

### P94-M02: DamageInstance capability state must be strictly operation-local
- **Root Cause**: Coordinator stored completed instances indefinitely in _completed_instances: set[DamageInstanceId], and permits were allocated before calculation, causing potential leaks if calculation raised.
- **Resolution**:
  - Removed _completed_instances set to prevent unbounded memory growth.
  - In execute_standard_damage_instance():
    1. Call DamageSystem.calculate() FIRST (if calculation raises, 0 permits are allocated or registered).
    2. Allocate damage_instance_id and issue permit = self.issue_settlement_permit().
    3. Execute settlement in a try ... finally: self.release_damage_instance(damage_instance_id) block.
  - On completion (or exception), permit tracking is immediately cleaned up with 0 residue.
  - Replay protection after cleanup: if an old/completed permit is submitted to validate_and_consume_permit(), it is not in _permits, raising ValueError (Permit '...' was not issued by this coordinator, closed, or not active) with 0 mutations and 0 events.

### P94-M03: DamageResolutionResult identity pair invariant
- **Root Cause**: DamageResolutionResult allowed inconsistent states where damage_instance_id was set without lineage, or vice versa.
- **Resolution**:
  - Enforced in DamageResolutionResult.__post_init__:
    if (self.damage_instance_id is None) != (self.lineage is None):
        raise ValueError(damage_instance_id and lineage must either both be None (legacy) or both be non-None (Stage9))

### P94-DOC01 & Package Export Audit
- **Root Cause**: DamageInstanceCoordinator was missing from sgs_v2.battle_core.__all__, and a Phase 9.2 negative assertion blocked exporting it.
- **Resolution**:
  - Added DamageInstanceCoordinator to sgs_v2/battle_core/__init__.py and __all__.
  - Updated tests/test_stage9_phase_9_2_future_admission.py to check assert not hasattr(bc, DamageInstanceScope), matching the docstring contract without blocking the authorized coordinator.
  - Updated STAGE9_PHASE_9_4_IMPLEMENTATION_REPORT.md to document implementation commit a8aa1360bd86bc620e947bc28729fb19fcfa5447, audit failure, and repair requirement.

---

## 2. Verification Matrix

| Test ID | Description | Result |
| :--- | :--- | :--- |
| **P94-R01** | resolve() traverses typed _settle_legacy with LEGACY_COMPAT | **PASS** |
| **P94-R02** | apply_result() traverses typed _settle_legacy with unchanged signature | **PASS** |
| **P94-R03** | Successful execution leaves 0 permit tracking residue | **PASS** |
| **P94-R04** | Calculation exception causes 0 permit leak | **PASS** |
| **P94-R05** | Replaying completed permit raises ValueError with 0 mutation / 0 events | **PASS** |
| **P94-R06** | DamageResolutionResult rejects damage_instance_id without lineage | **PASS** |
| **P94-R07** | DamageResolutionResult rejects lineage without damage_instance_id | **PASS** |

### Suite-Wide Verification
- **Unit & Integration Tests**: 470 passed in 0.76s (100% pass rate).
- **Demo verification**: demo.py completed with 0 errors.
- **Stage8 formulas / policies**: 0 modifications.
- **EffectExecutor**: production routing remains legacy (0 cutovers).
- **Phase 9.5 scope**: 0 leaks (no partition system, no DirectTroopLoss).
