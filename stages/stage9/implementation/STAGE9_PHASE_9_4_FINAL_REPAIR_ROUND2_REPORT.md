# Stage9 Phase 9.4 Final Repair Round 2 Report

## Phase Information

Phase:
9.4 Final Repair Round 2 — Exact Issued Capability Authenticity & Context-Bound DamageInstance Lifecycle

Baseline:
a894e268082bd5c86ddc9b9e111e59fc89b0ab0f

Parent:
a894e268082bd5c86ddc9b9e111e59fc89b0ab0f

State authority baseline:
15ed915435f328a6ecd8f488d98b5b9e13c913b5

Build Prompt:
835206ba39ce64c42a822a7138afeee307e0a492

Lifecycle status:
Phase 9.1 = COMPLETE / PASS
Phase 9.2 = COMPLETE / PASS
Phase 9.3 = COMPLETE / PASS
Phase 9.4 Final Repair Round 2 = COMPLETE / PASS
Phase 9.5 = NOT AUTHORIZED

---

## 1. Audit Findings Addressed

### FR2-B01: Same-value Cross-Context Permit Alias & Forged Clone Rejection
- **Status**: CLOSED
- **Problem**:
  In Phase 9.4 Final Repair Round 1, `DamageSettlementPermit` equality was checked using dataclass structural equality (`record.permit != permit`). Under concurrent battles with identical ID allocations (e.g. `ctx_A` and `ctx_B` both producing `dmg_1` / `dsp_1`), or when a user forged a clone `DamageSettlementPermit(dsp_1, dmg_1)`, structural equality matched even though the object identity was distinct (`permit_A is not permit_B`). If `permit_A` was passed to `ctx_B`, it could collide with `ctx_B`'s record, consuming `ctx_B`'s permit and corrupting capability authenticity.
- **Resolution**:
  - Maintained frozen public `DamageSettlementPermit` schema (0 extra public fields; no `context_id`, `battle_id`, `nonce`, etc.).
  - Maintained default `DamageSettlementPermit.__eq__` semantics.
  - Enforced exact capability authenticity inside `DamageInstanceCoordinator.validate_and_consume_permit()`:
    1. Pre-checks whether the exact capability object (`r.permit is permit`) was issued for a different `BattleContext` (`r.owning_context is not context`). If so, raises `ValueError` immediately **before** inspecting or consuming any local records.
    2. Validates that `record.permit is permit` (exact object identity), rejecting any synthetic forged clone with `ValueError("Permit capability authenticity failure... forged clone rejected")`.
    3. Guarantees that failed foreign attempts consume neither local nor foreign permits, preserving both legitimate capabilities.

### FR2-B02: Contextless Close/Release Ambiguity Narrowed
- **Status**: CLOSED
- **Problem**:
  `close_damage_instance(damage_instance_id, context=None)` allowed callers to omit `context`, falling back to iterating all active records across all contexts matching that ID and closing them all. Since multiple battles can legitimately have concurrent active instances with ID `dmg_1`, this created cross-battle mass-release ambiguity.
- **Resolution**:
  - Narrowed signature: `close_damage_instance(damage_instance_id: DamageInstanceId, context: BattleContext)`.
  - Narrowed signature: `release_damage_instance(damage_instance_id: DamageInstanceId, context: BattleContext)`.
  - Strictly requires `isinstance(context, BattleContext)`: passing `None` raises `TypeError` with zero state mutation.
  - Closing `dmg_1` on `ctx_A` strictly removes `(id(ctx_A), dmg_1)`, leaving `ctx_B`'s `dmg_1` completely active and its permit intact and settleable.

---

## 2. Gate Verification Summary

| Item | Status |
| :--- | :--- |
| **Baseline** | a894e268082bd5c86ddc9b9e111e59fc89b0ab0f |
| **Build Prompt** | 835206ba39ce64c42a822a7138afeee307e0a492 |
| **FR2-B01** | CLOSED |
| **FR2-B02** | CLOSED |
| **Same-value forged permit** | REJECTED |
| **Cross-context collision permit** | REJECTED |
| **Foreign attempt consumes local permit** | NO |
| **Legitimate A permit afterward** | PASS |
| **Legitimate B permit afterward** | PASS |
| **Context-bound close** | PASS |
| **context=None close** | REJECTED |
| **Round1 regressions** | PASS |
| **Round2 regressions** | PASS |
| **Final Repair Round1 regressions** | PASS |
| **Stage8 reopen** | NO |
| **Phase9.5 leakage** | 0 |
| **Tests** | PASS (487/487) |
| **Demo** | PASS |

---

## 3. Detailed Test Matrix

| Test ID | Test Name / Focus | Result |
| :--- | :--- | :--- |
| **P94-FR2-01** | Same-context forged equal-value permit clone rejected; legitimate permit remains usable | **PASS** |
| **P94-FR2-02** | `ctx_A` and `ctx_B` own `dmg_1`/`dsp_1`; `permit_A` passed to `ctx_B` rejected before consume | **PASS** |
| **P94-FR2-03** | After collision rejection, `permit_A` succeeds on `ctx_A` and `permit_B` succeeds on `ctx_B` | **PASS** |
| **P94-FR2-04** | Cross-context attempt consumes neither legitimate record; 0 troop mutation, 0 events | **PASS** |
| **P94-FR2-05** | Closing `dmg_1` on `ctx_A` does not close `ctx_B` `dmg_1`; `ctx_B` settles successfully | **PASS** |
| **P94-FR2-06** | `close_damage_instance` and `release_damage_instance` with `context=None` raise `TypeError` (0 mutation) | **PASS** |
| **P94-FR-01..06** | Final Repair Round 1 test suite | **PASS** |
| **P94-R2-01..07** | Repair Round 2 test suite | **PASS** |
| **P94-R01..07** | Repair Round 1 test suite | **PASS** |
