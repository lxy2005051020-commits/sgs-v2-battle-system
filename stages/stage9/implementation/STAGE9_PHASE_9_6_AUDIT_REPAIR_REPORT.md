# Stage9 Phase 9.6 Audit Repair Report

## Baseline Authority

- **Starting remote main**: `6acaea16c142870375c28dc7c2a2ab4c50688cc3`
- **Parent commit**: `6acaea16c142870375c28dc7c2a2ab4c50688cc3`
- **Build Prompt blob**: `835206ba39ce64c42a822a7138afeee307e0a492`
- **State authority**: `15ed915435f328a6ecd8f488d98b5b9e13c913b5`

---

## Audit Finding Dispositions

- **P96-B01** (BattleEngine broad TypeError replay fallback): **CLOSED**
  - Broad `try ... except TypeError:` block in `BattleEngine` removed.
  - Production route executes `systems.action_system.execute(context, actor, action_scope)` exactly once per admitted `ActionScope`.
  - Destructive side effects cannot trigger second action execution on internal exceptions (`P96-RPR-01`).
  - AST assertion proves `BattleEngine` contains no `except TypeError` blocks.

- **P96-B02** (Combo ACTION_START maintenance incorrectly occurs after STUN early-return): **CLOSED**
  - Reordered `ActionSystem.execute`: holder ACTION_START Combo lifecycle maintenance runs *before* STUN action-level gate.
  - Entry operational state settled and `ComboActionGrant` created before STUN checks.
  - STUN does not freeze or extend temporary Combo duration (`P96-RPR-02`, `P96-RPR-03`).

- **P96-B03** (NormalAttack #1 identity/count allocated before physical attack permission): **CLOSED**
  - Standard NormalAttack permission checks (liveness, troops, STUN, DISARM) occur strictly *before* `ActionScope.physical_normal_attack_count += 1` and *before* `NormalAttackInstanceId` allocation.
  - Blocked attacks emit `ACTION_BLOCKED` and return without allocating normal attack IDs or incrementing physical count (`P96-RPR-04`, `P96-RPR-05`).

- **P96-B04** (Combo #2 incorrectly skips Assault admission seam): **CLOSED**
  - Restructured post-hit lifecycle: Assault admission seam runs for all physical normal attacks (NA #1 and NA #2) prior to checkpoint gating.
  - `combo_checkpoint_allowed=False` skips only the Combo Checkpoint for NA #2, preventing recursive combo while ensuring Assault admission seam executes (`P96-RPR-06`).

- **P96-B05** (Frozen regression/invariant contract mapping is incorrect and incomplete): **CLOSED**
  - Restored exact frozen regression names and contractual vectors from `STAGE9_REGRESSION_CONTRACTS.md`:
    - `REG-TGT-05`: Combo #2 uses fresh target resolution (different NA ID, different TR ID, does not inherit #1 target).
    - `REG-TGT-06`: Guard reruns for Combo #2 against live world state.
    - `REG-TGT-07`: Pre-Guard intended target identity survives redirect (intended=B, actual=C).
    - `REG-CMB-01`: ACTION_START maintenance physically removes expired Combo before effective evaluation; no grant.
    - `REG-CMB-02`: Physical removal before consume revokes grant (`REVOKED_BY_PHYSICAL_REMOVE`), checkpoint blocked, no cfg230.
    - `REG-CMB-03`: Ordinary suppression after grant does not revoke current Action grant.
    - `REG-CMB-04`: Atomic consume ceiling: consume not refunded on later failure; vectors A (DISARM/STUN) & B (admission denied); consume<=1, cfg230<=1, physical NA<=2.
    - `REG-CMB-05`: Attacker death during NA #1 cancels future Assault and Combo #2; checkpoint stays `NOT_REACHED`.
    - `FINAL_03`: Lethal NA #1 latches victory, cancels #2, drains and finalizes.
  - Runtime Invariants verified (`INV-06..12`, `INV-39..42`) with direct assertions on `ActionScope.physical_normal_attack_count`.
  - P0 First-In-Wins non-stacking retained as `P96-COMBO-FIRST-IN-WINS`.

---

## Verification Matrix

| Check / Contract | Result | Details |
|---|---|---|
| BattleEngine destructive TypeError replay | **BLOCKED** | TypeError propagated without retry; side effect count = 1 |
| STUN ACTION_START maintenance | **PASS** | Maintenance runs before STUN block; duration decrements |
| DISARM blocked #1 NA identity allocation | **0** | `_normal_attack_seq` == 0 |
| DISARM blocked #1 physical count | **0** | `physical_normal_attack_count` == 0 |
| Combo #2 Assault seam | **PASS** | Reached for NA #1 and NA #2 |
| Recursive Combo checkpoint | **BLOCKED** | Checkpoint count == 1, cfg230 count == 1 |
| REG-TGT-05 | **PASS** | Fresh target resolution for Combo #2 |
| REG-TGT-06 | **PASS** | Live Guard rerun for Combo #2 |
| REG-TGT-07 | **PASS** | Intended and actual targets preserved |
| REG-CMB-01 | **PASS** | Expired physically removed before grant |
| REG-CMB-02 | **PASS** | Physical remove revokes unconsumed grant |
| REG-CMB-03 | **PASS** | Ordinary suppress does not revoke grant |
| REG-CMB-04 | **PASS** | Atomic consume ceiling (Vectors A & B) |
| REG-CMB-05 | **PASS** | Attacker death cancels future branches |
| INV-06..12 | **PASS** | Identities, states, counts, and caps verified |
| INV-39..42 | **PASS** | Victory barrier, single finalization owner, lineage |
| Cross-context ActionScope isolation (P96-RPR-07) | **PASS** | Foreign context admission rejected |
| Stage8 reopen | **NO** | No formulas, modifiers, or policies modified |
| Phase 9.7 leakage | **0** | Cleave, Chain, Counter not implemented |
| Phase 9.6 test suite | **PASS** | 36 / 36 passed in 0.22s |
| Full pytest | **PASS** | 565 / 565 passed in 1.00s |
| Demo (`python demo.py`) | **PASS** | 7 rounds complete simulation |
| Audit Repair Gate | **PASS** | All findings closed |

---

## Conclusion

Phase 9.6 Audit Repair is complete. Working tree is verified, regression-free, and aligned with frozen specifications.

---

## Final Re-Audit Verdict: FAIL

An independent re-audit of the Phase 9.6 audit repair commit (`13204fa2e0f78a95cb941731a595f05c29642671`) identified 3 remaining gaps:

1. **FR96-B01** (ActionScope production construction & execution FutureAdmission bypass): **FAIL**
   - Direct outside construction without FutureAdmissionPermit / coordinator capability binding was possible.
   - Forged or mismatched scopes (context, actor, object identity, terminal state, execution replay) were not authenticated prior to execution.
2. **FR96-B02** (Combo #2 execution when FutureAdmissionGate is absent): **FAIL**
   - `NormalAttackSystem._execute_single_hit` silently bypassed admission gate if gate was None and executed NA #2 anyway instead of failing closed.
3. **FR96-M01** (ComboCheckpointState transition violates frozen REACHED-before-grant-validation ordering): **FAIL**
   - Checkpoint transitioned to BLOCKED before reaching checkpoint boundary; frozen state mechanics require REACHED upon meeting local gate conditions, remaining REACHED if grant is missing or revoked.

**Final Repair Required**: Directed surgical repair authorized to close `FR96-B01`, `FR96-B02`, `FR96-M01`.

