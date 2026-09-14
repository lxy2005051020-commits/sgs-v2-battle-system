# Stage9 Phase 9.6 Implementation Report

## Status

Phase 9.6 production implementation is complete and verified.

- Starting baseline commit: `ba9535088f767a49974167892adff12e31c91174`
- Authorized Build Prompt blob: `835206ba39ce64c42a822a7138afeee307e0a492`
- Frozen state research authority: `15ed915435f328a6ecd8f488d98b5b9e13c913b5`
- Target Branch: `main`
- Stage8 semantic reopen: **NO**
- Phase 9.7: **NOT STARTED / UNAUTHORIZED**

---

## 1. NormalAttack Master Lifecycle & Cutover

`NormalAttackSystem` is now the sole authoritative execution master for all physical normal attacks in Stage9:
- Production `BattleEngine` no longer dispatches through legacy routes. Each unit action is admitted via `FutureAdmissionGate` with `FutureBranchKind.NEXT_ACTION`, producing an `ActionScope`.
- `ActionScope` is admitted through `finalization_coordinator.admit_action_scope(...)` and completed in a strict `try ... finally: coordinator.complete_action_scope(scope)` boundary in `BattleEngine`.
- `NormalAttackSystem` implements the complete 7-step master sequence:
  1. Live gating (`actor.is_alive`, troops > 0, STUN / DISARM checks).
  2. ID & Lineage allocation (`ActionId` -> `NormalAttackInstanceId`).
  3. Dynamic target resolution via `TargetResolutionSystem` (Confusion -> Taunt -> Default enemy selector -> Guard redirection).
  4. Target lock and `DamageRequest(source_type=NORMAL_ATTACK, coefficient=1.0)` construction.
  5. Observation hook publishing `EventType.NORMAL_ATTACK` with full Stage9 execution metadata before damage settlement.
  6. Damage execution routed authoritatively through `DamageInstanceCoordinator.execute_partitioned_damage_instance(...)` with Stage9 partition semantics (Share / Distribution).
  7. Pre-checkpoint synchronous lifecycle:
     - Assault seam admission via `AssaultDispatchPort`
     - Combo checkpoint atomic consume and conditional Second Normal Attack execution.

---

## 2. Hard Gate Sequencing

In compliance with Stage9 architectural rules:
- **NEXT_ACTION**: The `FutureAdmissionPermit` is requested and consumed *before* `ActionId` allocation and before any action execution begins.
- **COMBO_SECOND_NORMAL_ATTACK**:
  - The checkpoint verifies attacker liveness, battle running state (not latched or finalized), valid non-consumed `ComboActionGrant`.
  - Atomically consumes `grant` and advances `combo_checkpoint_state = CONSUMED`.
  - Live checks (liveness, STUN, DISARM) are re-verified.
  - The `FutureAdmissionGate.request_admission(FutureBranchKind.COMBO_SECOND_NORMAL_ATTACK, ...)` is called.
  - **Crucial**: The permit is consumed via `gate.consume_permit(...)` **strictly BEFORE** `context.id_allocator.allocate_normal_attack_instance_id()` is invoked for NormalAttack #2.
  - NormalAttack #2 executes under the *same* `ActionScope` / root `ActionId`, with its own distinct `NormalAttackInstanceId`, fresh target resolution, fresh Guard evaluation, and isolated `DamageInstanceCoordinator` execution.
  - At most 2 physical normal attacks can occur in a single action (`INV-42`).

---

## 3. Target Resolution Integration (REG-TGT-05..07)

- `TargetResolutionSystem.resolve()` handles full target selection and redirection:
  - **REG-TGT-05**: Taunt forces intended target to the taunt source, overriding random enemy selection.
  - **REG-TGT-06**: Guard redirects the damage recipient to the protector while preserving the intended attack target fact.
  - **REG-TGT-07**: Taunt + Guard compound correctly (intended target = taunter; actual target = protector of taunter).
  - Intended and actual targets, as well as `TargetResolutionResult`, are published in `NORMAL_ATTACK` event facts and tracked on `NormalAttackResult`.

---

## 4. Combo State Machine & P0 Contract (REG-CMB-01..05, FINAL_03)

- **REG-CMB-01 (Holder Maintenance & Expiration)**:
  - `ComboStateParams(remaining_actions, is_suppressed)` is registered in `OfficialStateCatalog`.
  - Decremented at `ACTION_START` of the holder's turn via `state_lifecycle_system.process_combo_action_start(...)`.
  - If `remaining_actions <= 0` at action start, physical removal occurs immediately and no `ComboActionGrant` is created.
- **REG-CMB-02 (P0 First-In-Wins)**:
  - Duplicate application of `COMBO` state on the same unit is rejected immediately; existing instance remains untouched with original duration and source.
- **REG-CMB-03 (Single Action Grant & Validity)**:
  - Exactly one `ComboActionGrant` per action created during action setup.
  - If suppressed by other states, grant remains valid (physical presence suffices per state research frozen authority).
  - If physically removed mid-action before the checkpoint, `is_valid(context)` returns `False` and transitions grant state to `REVOKED_BY_PHYSICAL_REMOVE`.
- **REG-CMB-04 (Fresh Target Resolution & Guard Pass)**:
  - NormalAttack #2 does NOT reuse target from attack #1; it executes a completely fresh target resolution pass, which dynamically re-evaluates Confusion, Taunt, Default, and Guard.
- **REG-CMB-05 (Facts & Checkpoint Transitions)**:
  - Emits `COMBO_OPPORTUNITY_CONSUMED` exactly once with `action_id`, `granting_instance_id`, `source_unit`, `source_skill`.
  - Action scope progresses through `NOT_REACHED -> REACHED -> CONSUMED`.
- **FINAL_03 (Battle Termination Protection)**:
  - If battle is latched or finalized before or at the checkpoint (e.g. enemy commander eliminated by attack #1), the second attack is cleanly aborted without dangling permits or leaks.

---

## 5. Seam-Only AssaultDispatchPort

- `AssaultDispatchPort` is registered in `BattleSystems` as an explicit, seam-only admission dispatch point for Phase 9.7 Assault.
- Validates gate admission, caller scope identity, and consumes the `ASSAULT` permit.
- Dispatches zero gameplay logic and produces zero unmanaged side effects in Phase 9.6.

---

## 6. Runtime Invariants Verified

- `INV-06`: Unique monotonic operation identities allocated across all systems.
- `INV-07`: Source identity and lineage (`OperationLineage`) preserved through NormalAttack -> DamageInstance.
- `INV-08`: Event ordering invariant: `NORMAL_ATTACK` event fact published *prior* to damage calculation / settlement facts.
- `INV-09`: Settlement capability invariant: damage executed via `DamageInstanceCoordinator`.
- `INV-10`: No legacy fallback during production normal attack execution.
- `INV-11`: Finalization barrier integrity: action scope admitted and tracked in coordinator until scope completion.
- `INV-12`: Hard future gate integrity: permits consumed before downstream ID allocations.
- `INV-39`: Combo single-grant per action.
- `INV-40`: Combo P0 First-In-Wins non-stacking.
- `INV-41`: Combo atomic consume and fact emission.
- `INV-42`: Physical normal attack count per action strictly <= 2.

---

## 7. Verification Summary

- **Phase 9.6 Dedicated Regression Suite**:
  - `tests/test_stage9_phase_9_6_normal_attack.py`: **20 passed, 0 failed** in 0.18s.
- **Full Project Test Suite**:
  - `python -m pytest`: **549 passed, 0 failed** in 1.08s.
- **Full Simulation Demo**:
  - `python demo.py`: **PASS** (Full 7-round battle simulation completing with valid victory latch).

All Stage9 Phase 9.6 requirements are satisfied and verified.
