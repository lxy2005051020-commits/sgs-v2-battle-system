# Stage13 · Core Gameplay Mechanism Completion

> Status: ACTIVE / FOUNDATIONAL + RESIDUAL + D1 SLICES FROZEN / EXIT AUDIT REMAINS

Stage13 completes the reusable game-engine substrate before large-scale concrete-skill integration.

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

Stage13 entry gate:

```text
STAGE13_ENTRY_GATE                = PASS
Stage13 Active                    = YES
```

Concrete skill runtimes remain deferred until the Stage13 exit gate.

Official-state baseline:

```text
Research FROZEN            = 40 / 40
Runtime FROZEN TO CONTRACT = 40 / 40
Strict Complete            = 40 / 40
```

## Current authorities

- [Core gameplay gap ledger](STAGE13_CORE_GAMEPLAY_GAP_LEDGER.md)
- [Core runtime owner matrix](STAGE13_CORE_RUNTIME_OWNER_MATRIX.md)
- [Core mechanism test matrix](STAGE13_CORE_MECHANISM_TEST_MATRIX.md)
- [Research gap ledger](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/95e7fe78430d623c0240e9615f5f054515a90ce9/STAGE13_RESEARCH_GAP_LEDGER.md)
- [Runtime governance ledger](STAGE13_RUNTIME_GOVERNANCE_LEDGER.md)
- [Foundational runtime integration](STAGE13_FOUNDATIONAL_RUNTIME_INTEGRATION.md)
- [Foundational runtime freeze audit](STAGE13_FOUNDATIONAL_RUNTIME_FREEZE_AUDIT.md)
- [B3 treatment runtime integration](STAGE13_B3_TREATMENT_RUNTIME_INTEGRATION.md)
- [Residual mechanism runtime integration](STAGE13_RESIDUAL_MECHANISM_RUNTIME_INTEGRATION.md)
- [D1 design](STAGE13_D1_PENDING_WORK_RUNTIME_DESIGN.md)
- [D1 implementation](STAGE13_D1_PENDING_WORK_IMPLEMENTATION.md)
- [D1 freeze audit](STAGE13_D1_PENDING_WORK_FREEZE_AUDIT.md)

## D1 evidence

```text
main HEAD = f0339729a94685f1d1ae226e1975ad4298b7f81f
CI        = 37208949453 / SUCCESS
pytest    = 1739 passed
demo      = PASS
audit     = PASS
```

ONE_SHOT / UNTIL_EXECUTED / UNTIL_ROUND are implemented. REPEAT_N_TIMES remains a reserved unsupported seam.

## Current remaining work

Do not mechanically create D2/D3/D4 subsystems merely because an older gap row used the word MISSING.

Current Stage13 exit work is:

```text
1. reconcile remaining core capability boundaries against existing owners
2. close only true core blockers
3. define/complete RNG decision observability needed for replay
4. run whole-battle deterministic replay / exit audit
5. if PASS:
   Core Gameplay Engine = FROZEN
   Skill Runtime Readiness = READY
```

Special recovery families remain separate from ordinary treatment and retain family-specific formula ownership.

```text
Core Gameplay Engine    = NOT YET FROZEN
Skill Runtime Readiness = NOT YET READY
```

Historical Stage13 replans, intermediate model-comparison reports and superseded question ledgers are available from Git history rather than the current authority tree.


## Machine-checked exit declarations

```text
CORE_GAMEPLAY_ENGINE              = NOT YET FROZEN
Skill Runtime Readiness           = NOT YET READY
```

Stage14+ concrete skill integration remains behind the exit gate.

Exit target:

```text
Skill Runtime Readiness = READY
```


Research Authority:
Repository: lxy2005051020-commits/sgs-state-mechanics-research
Commit: 95e7fe78430d623c0240e9615f5f054515a90ce9
Path: RESEARCH_AUTHORITY_INDEX.md
Status: CURRENT INDEX; individual contracts retain scoped status
