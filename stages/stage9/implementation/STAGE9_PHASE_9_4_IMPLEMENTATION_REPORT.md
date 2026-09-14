# Stage9 Phase 9.4 Implementation Report

## Phase Information

Phase:
9.4 — Typed Settlement + Isolated DamageInstance

Starting remote main:
c7afd68de69243c7ad3fee9849da911e4c19de1d

Implementation commit:
a8aa1360bd86bc620e947bc28729fb19fcfa5447 feat(stage9): implement phase 9.4 settlement core

Parent:
c7afd68de69243c7ad3fee9849da911e4c19de1d

Implementation Audit:
FAIL

Repair required:
YES

Repair report:
stages/stage9/implementation/STAGE9_PHASE_9_4_REPAIR_REPORT.md

Build Prompt blob:
835206ba39ce64c42a822a7138afeee307e0a492

---

## 1. File Changes Summary

New production files:
- `sgs_v2/battle_core/damage_instance_coordinator.py`

Modified production files:
- `sgs_v2/battle_core/damage_resolution_system.py`
- `sgs_v2/battle_core/battle_systems.py`
- `sgs_v2/battle_core/__init__.py`

Changed tests:
- `tests/test_stage9_phase_9_4_typed_settlement.py` (NEW)
- `tests/test_stage9_phase_9_4_damage_instance.py` (NEW)

---

## 2. Core Mechanism Verification Matrix

DamageSettlementRequest:
PASS

SettlementOrigin:
PASS

DamageResolutionResult Model A:
PASS

Dtotal / Dtarget / ActualLoss separation:
PASS

DAMAGE_DEALT requested damage:
PASS

Permit issuer ownership:
PASS

Permit replay:
REJECTED

Fake permit:
REJECTED

Identity mismatch:
REJECTED

Lineage mismatch:
REJECTED

Prevented settlement:
PASS

Legacy resolve:
PASS

Legacy apply_result:
PASS

EffectExecutor cutover:
NO

Partition:
NOT STARTED

DirectTroopLoss:
NOT STARTED

Stage8 reopen:
NO

P0 semantic changes:
0

State repo changes:
0

Forward dependency:
0

Existing tests:
PASS

Phase 9.1:
PASS

Phase 9.2:
PASS

Phase 9.3:
PASS

Phase 9.4:
PASS

Demo:
PASS

Exit Gate:
PASS

---

## 3. Invariant & Architecture Compliance

- **INV-05 (Concrete settlement owns recipient)**:
  `DamageSettlementRequest` and `DamageResolutionResult` explicitly encapsulate target, amount, damage instance ID, and lineage. Early target selection queries are not conflated with final troop mutation.
- **INV-26 (Four-layer damage facts permanently separated)**:
  `Dtotal` (`DamageResult.final_damage`), `Dtarget` (`DamageSettlementRequest.assigned_target_damage`), `ActualTargetTroopLoss` (`DamageResolutionResult.actual_target_troop_loss`), and `CreditedDamage` (`DamageResolutionResult.credited_damage`) remain strictly unaliased. Verified via fixture `Dtotal(300) != Dtarget(180) != ActualLoss(100)`.
- **Architecture #10 (Damage settlement one-shot capability)**:
  `DamageSettlementPermit` is issued exclusively by `DamageInstanceCoordinator` (at most one per `DamageInstanceId`) and validated/consumed atomically inside `DamageResolutionSystem.settle()` before calling `TroopSystem.apply_damage` or emitting events. Replayed permits, fake permits, ID mismatches, and lineage mismatches are rejected as domain errors with zero side effects.
- **Architecture #1 (Stage8 import inversion blocked)**:
  `DamageSystem` and Stage8 calculation modules do not import or know about `DamageInstanceCoordinator`. Dependency direction strictly points from Stage9 coordinator down to Stage8 calculation services.
- **Legacy Compatibility**:
  Existing `DamageResolutionSystem.resolve()` and `apply_result()` interfaces remain 100% compatible. Calls are wrapped in stack-local `LEGACY_COMPAT` requests and are not rejected by the Stage9 one-shot permit guard. No optional `assigned_amount` parameter was added to `apply_result()`.
- **Production Routing Isolation**:
  `EffectExecutor` continues to route standard damage through the legacy `DamageResolutionSystem` pathway. Zero production cutover was performed in Phase 9.4; cutover is preserved strictly for Phase 9.5.
