# Stage13 · Core Gameplay Mechanism Completion

> Status: **COMPLETE / CORE GAMEPLAY ENGINE FROZEN / SKILL RUNTIME READY**

Stage13 completed the reusable game-engine substrate required before concrete-skill integration.

## Final exit result

```text
STAGE13_FINAL_EXIT_AUDIT = PASS
CORE_GAMEPLAY_ENGINE     = FROZEN
SKILL_RUNTIME_READINESS  = READY
STAGE13                  = COMPLETE / FROZEN
STAGE14 MAINLINE GATE    = OPEN
```

The final exit audit is authoritative:

- [Stage13 Final Exit Audit](STAGE13_FINAL_EXIT_AUDIT.md)
- [Final Gap Reconciliation](STAGE13_FINAL_GAP_RECONCILIATION.md)
- [Final Governance Reconciliation](STAGE13_FINAL_GOVERNANCE_RECONCILIATION.md)
- [Whole-Battle Replay Audit](STAGE13_WHOLE_BATTLE_REPLAY_AUDIT.md)

## Completed slices

```text
B1 Wounded-Troop / Recoverable-Capacity Mechanics — FROZEN
B1 Runtime                         = IMPLEMENTED
B2 Damage Increase / Reduction Mechanics — FROZEN
B2 Runtime                         = IMPLEMENTED
B2.5 Advancement / Damage Closure  = CLOSED / IMPLEMENTED
B3 Ordinary Treatment Core         = FROZEN / IMPLEMENTED

690221 ACTIVE_SKILL + DOT           = CLOSED / INTEGRATED
690099 MaxCarry × 6%, equality      = CLOSED / INTEGRATED
690086 DSTS9-B02                    = CLOSED / FROZEN_P0

D1 PendingWork Foundation           = FROZEN / IMPLEMENTED
```

Official-state baseline:

```text
Research FROZEN            = 40 / 40
Runtime FROZEN TO CONTRACT = 40 / 40
Strict Complete            = 40 / 40
```

## Exit audit evidence

```text
Merged-main SHA       = b6e14da446ab0d47430f8990f2afe6479c76d65e
Merged-main CI        = 37272295169 / SUCCESS
Final full regression = 1744 passed
Demo                  = PASS
D1 frozen-owner audit = PASS
Whole-battle replay   = PASS
True exit blockers    = 0
```

Whole-battle deterministic replay established:

- same input + same seed: 25/25 canonical projections identical;
- changed seeds: deterministic divergence attributable to authorized RNG decisions;
- zero-RNG fast paths: PASS;
- `RandomSystem` remains the sole PRNG owner.

## Current authorities

- [Core gameplay gap ledger](STAGE13_CORE_GAMEPLAY_GAP_LEDGER.md)
- [Core runtime owner matrix](STAGE13_CORE_RUNTIME_OWNER_MATRIX.md)
- [Core mechanism test matrix](STAGE13_CORE_MECHANISM_TEST_MATRIX.md)
- [Runtime governance ledger](STAGE13_RUNTIME_GOVERNANCE_LEDGER.md)
- [Foundational runtime integration](STAGE13_FOUNDATIONAL_RUNTIME_INTEGRATION.md)
- [Foundational runtime freeze audit](STAGE13_FOUNDATIONAL_RUNTIME_FREEZE_AUDIT.md)
- [B3 treatment runtime integration](STAGE13_B3_TREATMENT_RUNTIME_INTEGRATION.md)
- [Residual mechanism runtime integration](STAGE13_RESIDUAL_MECHANISM_RUNTIME_INTEGRATION.md)
- [D1 design](STAGE13_D1_PENDING_WORK_RUNTIME_DESIGN.md)
- [D1 implementation](STAGE13_D1_PENDING_WORK_IMPLEMENTATION.md)
- [D1 freeze audit](STAGE13_D1_PENDING_WORK_FREEZE_AUDIT.md)

## Preserved explicit boundaries

Stage13 freeze does **not** mean every future concrete-skill capability was preimplemented.

Examples deliberately left to future concrete contracts include:

- `REPEAT_N_TIMES` scheduled work;
- generic usage/cooldown/charge budgets;
- broad category cleanse before an authoritative taxonomy exists;
- future selector/ranking semantics not yet required by a frozen skill contract;
- complex multi-effect rollback/atomic-group semantics not yet required by a consumer.

These are explicit future extension boundaries, not Stage13 exit blockers.

## Stage14 handoff

The Stage13 exit gate has passed.

Concrete skill integration may now enter `main` when the selected Stage14 skill or mechanism family independently satisfies:

```text
Research Contract / Game Truth     = CLOSED / FROZEN
Runtime Requirement Mapping         = REVIEWED
Implementation                      = COMPLETE
Skill-specific regression           = PASS
Full regression / demo              = PASS
Independent Runtime Audit           = PASS
PR CI                               = PASS
```

Stage13 must not be reopened merely because a future skill needs a new extension seam. Reopen only when new evidence proves a frozen core contract or canonical owner is wrong.

## Machine-checked exit declarations

```text
CORE_GAMEPLAY_ENGINE    = FROZEN
Skill Runtime Readiness = READY
STAGE13                 = COMPLETE / FROZEN
STAGE14 MAINLINE GATE   = OPEN
```

Research Authority:
Repository: `lxy2005051020-commits/sgs-state-mechanics-research`  
Path: `RESEARCH_AUTHORITY_INDEX.md`  
Status: CURRENT INDEX; individual contracts retain scoped status.
