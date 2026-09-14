# Stage 9 Phase 9.3 Repair Round 2 Report

## Phase Information

Phase:
9.3 Repair Round 2 — Target Resolution + Authority Alignment

Round 2 Baseline:
5367b2e1996ebc9fa2a97fd1324e17cc817da852

Round 1 Repair Commit:
5367b2e1996ebc9fa2a97fd1324e17cc817da852

Round 1 Parent:
d00df3b4d7cd28a092bce16c3e53902888518c2f

Build Prompt Blob:
835206ba39ce64c42a822a7138afeee307e0a492

---

## 1. Executive Summary

During Phase 9.3 Repair Re-Audit following Round 1 (5367b2e1996ebc9fa2a97fd1324e17cc817da852), authority violations were detected regarding:
1. Taunt suppression lifecycle under Insight: Insight does not remove Taunt from StateRegistry, but suppresses it operationally without introducing a second physical state store.
2. Taunt target authority disagreement: taunt_target_id must not contradict authoritative source_id.
3. Guard disabled gate: Guard supports an operational disabling flag (is_disabled) where physical state remains in StateRegistry but redirection is disabled until re-enabled.
4. Attacker equals protector legality: In P0 Guard semantics, attacker == protector is legal and must not be artificially rejected.
5. Guard protector identity and sourceUnit provenance separation: protector_id is an explicit, required non-empty string distinct from caster source_id. Self-guard is forbidden.
6. Repair report metadata accuracy: Fixed commit references and eliminated string escape / control-character corruptions.

All Round 2 findings have been systematically resolved, preserving zero Phase 9.4 leakage and zero Stage 8 regression.

---

## 2. Findings Resolved (Round 2)

### 1. Taunt Suppression Lifecycle Model
- **Contract**:
  - TauntLifecycleState enum: ACTIVE, SUPPRESSED.
  - SuppressionReason enum: INSIGHT, SOURCE_SKILL_DISABLED.
  - When holder possesses active Insight, Taunt is dynamically evaluated as SUPPRESSED via get_taunt_lifecycle_state.
  - Physical state remains in StateRegistry (context.states) throughout; no second state store is introduced.
  - When Insight expires or is removed, Taunt immediately returns to ACTIVE.
  - Source unit death is decoupled from suppression lifecycle (lifecycle_state remains ACTIVE, but is_taunt_operational checks source_unit.is_alive).
- **Implementation**:
  - Defined TauntLifecycleState and SuppressionReason in sgs_v2/battle_core/stage9_state_runtime.py and exported in __init__.py.
  - Implemented get_taunt_suppressors(), get_taunt_lifecycle_state(), is_taunt_operational(), and get_operational_taunt().

### 2. Taunt Target Authority Enforcement
- **Contract**:
  - Authoritative forced target is strictly instance.source_id.
  - If runtime_params specifies taunt_target_id that disagrees with source_id, StateLifecycleSystem.apply() immediately raises ValueError.
  - get_taunt_target_unit_id() validates agreement and returns instance.source_id.
- **Implementation**:
  - Validated in StateLifecycleSystem.apply() and StateLifecycleSystem.update_runtime_params().
  - Guaranteed in Stage9StateRuntime.get_taunt_target_unit_id().

### 3. Guard Disabled Gate & Re-enabling
- **Contract**:
  - GuardStateParams carries is_disabled: bool = False.
  - When is_disabled is True, is_guard_operational() returns False and get_guard_protector() returns None. Physical state remains in StateRegistry.
  - When updated via StateLifecycleSystem.update_runtime_params(), Guard becomes operational again.
- **Implementation**:
  - Added is_disabled: bool = False to GuardStateParams.
  - Added is_guard_operational() and updated get_guard_protector() to check operational status.
  - Implemented StateLifecycleSystem.update_runtime_params() allowing lifecycle-managed mutation without a second state store.

### 4. Attacker == Protector Legality
- **Contract**:
  - If attacker equals protector (e.g. A attacks B, B is guarded by A), redirection to A is legal in P0 Guard semantics.
  - get_guard_protector() does not reject attacker == protector.
- **Implementation**:
  - Allowed attacker == protector in get_guard_protector().

### 5. Guard Protector Explicit Identity & Provenance Separation
- **Contract**:
  - protector_id: str is a required non-empty string (frozen dataclass).
  - Self-guard (protector_id == owner_id) is strictly rejected with ValueError at apply time.
  - protector_id is read directly from runtime_params; source_id is strictly caster provenance.
- **Implementation**:
  - GuardStateParams validates protector_id as non-empty string.
  - StateLifecycleSystem.apply() enforces protector_id != owner_id.
  - get_guard_protector() reads inst.runtime_params.protector_id explicitly.

### 6. Repair Report Metadata and Control Characters
- **Fix**: Corrected Round 1 and Round 2 report commit hashes, parent references, and eliminated character corruptions (normal_attack_id, resolve(), etc.).

---

## 3. Production Files Modified

- sgs_v2/battle_core/stage9_state_params.py:
  - GuardStateParams: protector_id: str (required non-empty string), is_disabled: bool = False.
  - TauntStateParams: added suppressors: frozenset[str] = field(default_factory=frozenset).
- sgs_v2/battle_core/stage9_state_runtime.py:
  - Added TauntLifecycleState, SuppressionReason.
  - Added get_taunt_suppressors(), get_taunt_lifecycle_state(), is_taunt_operational().
  - Updated get_operational_taunt() to check is_taunt_operational().
  - Added is_guard_operational(), updated get_guard_protector() with explicit protector_id and attacker == protector legality.
- sgs_v2/battle_core/state_lifecycle_system.py:
  - Enforced self-guard rejection in apply() and update_runtime_params().
  - Enforced taunt_target_id == source_id agreement validation.
  - Added update_runtime_params().
- sgs_v2/battle_core/__init__.py:
  - Exported TauntLifecycleState and SuppressionReason.
- tests/test_stage9_phase_9_3_target_resolution.py:
  - Added full Round 2 test suite (P93-R2-TNT-01..05, P93-R2-GRD-01..07).

---

## 4. Test Verification Summary

- Total tests: 434 passed, 0 failed (100% PASS).
- Demo verification: python demo.py runs cleanly to completion.

### Round 2 Authority Regression Suite
| Test ID | Description | Status |
| :--- | :--- | :--- |
| **P93-R2-TNT-01** | Existing Taunt + Insight -> physical state remains, Taunt operationally SUPPRESSED, no Taunt override | PASS |
| **P93-R2-TNT-02** | Remove final suppressor -> Taunt becomes operational again | PASS |
| **P93-R2-TNT-03** | Suppressed Taunt still occupies slot/registry | PASS |
| **P93-R2-TNT-04** | Source dead remains independent from suppression lifecycle | PASS |
| **P93-R2-TNT-05** | Taunt target authority cannot disagree with source_id | PASS |
| **P93-R2-GRD-01** | Disabled Guard physically remains but does not redirect | PASS |
| **P93-R2-GRD-02** | Re-enabled operational Guard may redirect again | PASS |
| **P93-R2-GRD-03** | Attacker == protector is legal | PASS |
| **P93-R2-GRD-04** | Dead protector does not redirect | PASS |
| **P93-R2-GRD-05** | Protector explicit identity required; self-guard forbidden | PASS |
| **P93-R2-GRD-06** | Protector identity and sourceUnit provenance remain distinct | PASS |
| **P93-R2-GRD-07** | Guard remains single-pass | PASS |

### Preserved Phase 9.3 Contracts
| Test ID | Description | Status |
| :--- | :--- | :--- |
| **ARCH-P93-01** | Stage9StateRuntime cannot self-construct StateLifecycleSystem | PASS |
| **ARCH-P93-02** | BattleSystems is production composition root for Stage9StateRuntime | PASS |
| **ARCH-P93-03** | TargetResolutionSystem cannot allocate NormalAttackInstanceId | PASS |
| **ARCH-P93-04** | TargetResolutionSystem allocates only TargetResolutionId | PASS |
| **P0-CFS-P93-01** | Insight application immunity is not silently reinterpreted as JIT Confusion suppression | PASS |
| **TARGET-P93-01** | Confusion legal candidate construction consumes TargetSystem authority | PASS |
| **TARGET-P93-02** | No extra RNG call introduced | PASS |
| **REG-TGT-01** | Confusion shadows Taunt selector | PASS |
| **REG-TGT-02** | Taunt lifecycle continues while selector is shadowed | PASS |
| **REG-TGT-03** | Guard occurs after selector | PASS |
| **REG-TGT-04** | Guard is single-pass | PASS |

---

## 5. Scope Boundary Compliance

- Phase 9.4 NOT started (damage_instance_coordinator.py does not exist, no DamageSettlementRequest production route).
- No second physical state store introduced (StateRegistry is the sole physical storage).
- StateLifecycleSystem is the sole physical state mutation authority.
- No EventBus orchestration introduced into targeting.
- Stage 8 formulas and research repo untouched (diff = 0).
- NormalAttack master cutover NOT performed.
