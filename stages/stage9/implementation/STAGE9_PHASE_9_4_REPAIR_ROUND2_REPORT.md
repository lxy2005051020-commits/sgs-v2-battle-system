# Stage9 Phase 9.4 Repair Round 2 Report

## Phase Information

Phase:
9.4 Repair Round 2 — DamageInstance Lifecycle Ordering & Permit Cardinality Hardening

Starting remote main:
352968e74e947a5919225102bd522fa4cb22c960 fix(stage9): repair phase 9.4 settlement lifecycle

Parent:
352968e74e947a5919225102bd522fa4cb22c960

State authority baseline:
15ed915435f328a6ecd8f488d98b5b9e13c913b5

Build Prompt blob:
835206ba39ce64c42a822a7138afeee307e0a492

Lifecycle status:
Phase 9.4 Repair Round 2 = COMPLETE / PASS
Phase 9.5 = NOT AUTHORIZED

---

## 1. Audit Findings Addressed & Architectural Hardening

### R2-M01: Restore Frozen DamageInstance Identity Lifetime Ordering
- **Root Cause**: In Repair Round 1, DamageSystem.calculate() was executed prior to allocating DamageInstanceId. While this avoided permit issuance upon calculation failure, it broke the frozen identity lifetime invariant requiring DamageInstanceId to exist when calculation runs.
- **Resolution**:
  - Implemented begin_damage_instance(context, lineage) on DamageInstanceCoordinator, allocating a fresh DamageInstanceId, binding lineage, and opening an active operation-local scope record _ActiveDamageInstanceRecord.
  - In execute_standard_damage_instance():
    1. Call begin_damage_instance() FIRST.
    2. Execute DamageSystem.calculate() while the DamageInstance identity is actively registered and verifiable via is_instance_active().
    3. Issue exactly one permit for the active instance.
    4. Settle via DamageResolutionSystem.settle().
    5. In finally, close and release the active scope via close_damage_instance().
  - If calculation fails: DamageInstanceId was allocated, 0 permits were issued, and active scope is cleaned up cleanly in finally. The allocator sequence creates an intentional gap for the next instance.

### R2-M02: One Permit Per DamageInstance Lifetime & Scope Ownership
- **Root Cause**: In Repair Round 1, permits were checked against currently stored mapping. Once an instance completed and its mapping was popped, calling issue_settlement_permit(dmg_1, ...) with the old ID could issue a new permit #2, violating Architecture #10.
- **Resolution**:
  - Introduced internal _ActiveDamageInstanceRecord tracking active micro-scopes:
    damage_instance_id, lineage, permit_id, permit_issued, permit_consumed, closed.
  - issue_settlement_permit() strictly verifies:
    1. damage_instance_id is currently in coordinator's _active_instances.
    2. Active record is NOT closed.
    3. record.lineage == lineage.
    4. record.permit_issued == False (rejecting any duplicate permit issuance attempt during active lifetime).
  - Closed instances and arbitrary manually crafted DamageInstanceIds are rejected immediately because they do not exist as active coordinator-owned records.
  - No battle-long tombstones (_active_instances and _permits are empty when no instances are executing; zero unbounded memory growth).
  - Replaying closed requests with fresh minted permits or replaying old permits is structurally impossible and completely blocked with 0 troop mutations and 0 events.

---

## 2. Verification Matrix

| Test ID | Description | Result |
| :--- | :--- | :--- |
| **P94-R2-01** | DamageInstanceId exists BEFORE DamageSystem.calculate() | **PASS** |
| **P94-R2-02** | Calculate failure: ID allocated, 0 permits issued, scope cleaned, gap in sequence | **PASS** |
| **P94-R2-03** | Same active DamageInstance rejects duplicate permit issuance | **PASS** |
| **P94-R2-04** | Closed DamageInstance rejects permit re-issuance | **PASS** |
| **P94-R2-05** | Arbitrary manually constructed DamageInstanceId rejected for permit issuance | **PASS** |
| **P94-R2-06** | Foreign coordinator or inactive permit rejected by settle() | **PASS** |
| **P94-R2-07** | Replay attack with minted permit or cross-instance pairing blocked (0 mutation/0 events) | **PASS** |
| **P94-R01..R07** | Round 1 regression suite | **PASS** |

### Suite-Wide Verification
- **Unit & Integration Tests**: 477 passed in 0.79s (100% pass rate).
- **Demo verification**: demo.py completed with 0 errors.
- **Stage8 formulas / policies**: 0 modifications.
- **EffectExecutor**: production routing remains legacy (0 cutovers).
- **Phase 9.5 scope**: 0 leaks (no partition system, no DirectTroopLoss).

---

## 3. Final Re-Audit

Final Re-Audit:
FAIL

Remaining finding:
DamageInstance BattleContext ownership

