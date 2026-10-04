# Stage13 · Core Gameplay Mechanism Completion

> Current status: ACTIVE / B1+B2+B2.5 RUNTIME FROZEN / B3 ORDINARY-TREATMENT CORE INTEGRATED, SPECIAL FAMILY BOUNDARIES OPEN
>
> Activated: 2026-09-28 by STAGE13_CORE_GAMEPLAY_MECHANISM_INVENTORY_AUDIT
>
> Current route amendment: [STAGE13_FOUNDATIONAL_RESEARCH_PRIORITY_REPLAN.md](STAGE13_FOUNDATIONAL_RESEARCH_PRIORITY_REPLAN.md)
>
> Original route authority: [STAGE13_CORE_GAMEPLAY_MECHANISM_REPLAN.md](STAGE13_CORE_GAMEPLAY_MECHANISM_REPLAN.md)

Stage13 completes the reusable game-engine substrate before large-scale skill-system integration.

Stage13-A completed the original inventory. A later route review found that Runtime support had been treated too generously as evidence of empirical completion for three foundational domains: wounded/recoverable capacity, damage increase/reduction mathematics, and treatment-value formulas. The inventory remains historical authority, but its research-priority conclusion is superseded by the current amendment.

## 1. Current Stage model

~~~text
Stage13-A  Core Gameplay Mechanism Inventory Audit
           COMPLETE / ENTRY GATE PASS

Stage13-B  Foundational Empirical Mechanics Research
           B1 Wounded-Troop / Recoverable-Capacity Mechanics — FROZEN
           B2 Damage Increase / Reduction Mechanics — FROZEN
           B2.5 Full Damage Advancement / Hidden Mechanism Closure — CLOSED
           B3 Recovery / Treatment Formula Mechanics — ORDINARY FORMULA CORE FROZEN / SPECIAL FAMILIES OPEN

Stage13-C  Residual State Mechanism Closure

Stage13-D  Consolidated Gap Classification + Runtime Governance
Stage13-E  Core Runtime Architecture Design
Stage13-F  Core Mechanism Implementation
           Foundational slice B1/B2/B2.5 — IMPLEMENTED / RUNTIME FREEZE AUDIT PASS
           B3 ordinary-treatment core — IMPLEMENTED / MERGED-MAIN CI PASS / RUNTIME CORE FROZEN
Stage13-G  Independent Engine Completion / Deterministic Replay Audit
~~~

## 2. Current authorities

- [Stage13 Foundational Research Priority Replan](STAGE13_FOUNDATIONAL_RESEARCH_PRIORITY_REPLAN.md)
- [Core Gameplay Mechanism Inventory](STAGE13_CORE_GAMEPLAY_MECHANISM_INVENTORY.md)
- [Core Gameplay Gap Ledger](STAGE13_CORE_GAMEPLAY_GAP_LEDGER.md)
- [Core Runtime Owner Matrix](STAGE13_CORE_RUNTIME_OWNER_MATRIX.md)
- [Core Mechanism Test Matrix](STAGE13_CORE_MECHANISM_TEST_MATRIX.md)
- [Research Gap Ledger](STAGE13_RESEARCH_GAP_LEDGER.md)
- [Runtime Governance Gap Ledger](STAGE13_RUNTIME_GOVERNANCE_LEDGER.md)
- [Foundational Runtime Integration](STAGE13_FOUNDATIONAL_RUNTIME_INTEGRATION.md)
- [Foundational Runtime Freeze Audit](STAGE13_FOUNDATIONAL_RUNTIME_FREEZE_AUDIT.md)

## 3. Entry verdict

~~~text
CORE_GAMEPLAY_MECHANISM_INVENTORY       = COMPLETE
STAGE13_ENTRY_GATE                = PASS
Stage13 Readiness                       = READY
Stage13 Active                    = YES

Stage12 Runtime                         = FROZEN
Stage12 Complete                        = YES
Stage1-12 Reopen Required               = NO

Research FROZEN                         = 40 / 40
Runtime FROZEN TO CONTRACT              = 40 / 40
Strict Complete                         = 40 / 40
690086 DSTS9-B02                        = CLOSED
~~~

Inventory activation does not mean the Core Gameplay Engine is frozen:

~~~text
CORE_GAMEPLAY_ENGINE              = NOT YET FROZEN
Skill Runtime Readiness           = NOT YET READY
~~~

## 4. Foundational empirical research gate

Before architecture/implementation, Stage13 now requires three research programs.

### B1 — Wounded troops / recoverable capacity

B1 research is frozen. Runtime now carries an explicit wounded pool with 90% event-local generation, wounded-capacity recovery clamp, round-transition decay and defeat cleanup. Missing troops are no longer the canonical runtime recovery capacity.

### B2 — Damage increase / damage reduction

B2 and B2.5 research are closed for the implemented slice. Runtime now uses same-side algebraic modifier pools, cross-side multiplication, the -90% same-side floor, and the B2.5 independent advancement multiplier directive.

### B3 — Recovery / treatment formula

The ordinary treatment-rate core is now contract-frozen and integrated:

```text
H = CEIL(
    Rate
    × (F(N) + Attr)
    × SourceOrdinaryPool
    × TargetOrdinaryPool
    × RedPool
)
```

The selected attribute coefficient is 1. Same-side ordinary modifiers add algebraically, source/target sides multiply, red-degree is an independent pool, and persistent treatment replays application-time formula state. The final HealingBlock and wounded/missing-troop capacity tail remains live in RecoverySystem/TroopSystem.

Special recovery families remain independently owned and are not silently collapsed into this formula.

## 5. Residual state research comes after B1-B3

Stage13-C performs a systematic residual-debt audit across all 40 state contracts and extracts only unresolved clauses:

~~~text
OPEN
UNOBSERVED
BOUNDED_UNKNOWN
UNSUPPORTED_UNKNOWN
PROJECT_RUNTIME_DEFAULT
RESEARCH_DEBT
FORMULA_RESEARCH_OUT_OF_SCOPE
~~~

The previously blocking residual clauses are now closed: 690221 applies to ACTIVE_SKILL and DOT/DELAYED damage; 690086 DSTS9-B02 drains the current DistributionTransaction before battle finalization; 690099 uses MaxCarryTroops × 6% with equality triggering. Remaining Stage13-C work is limited to truly unresolved micro-debt and governance-only items.

## 6. Runtime architecture boundary

The project still follows:

~~~text
REUSE -> EXTEND -> COMPOSE
~~~

A CoreGameplayGodObject is forbidden.

Runtime code is not evidence for original-game mechanics. Explicit project defaults retain their provenance and must never be upgraded to empirical truth merely because they are already implemented.

## 7. Skill-system boundary

~~~text
Stage14+ = Skill System / exact subtype numbering deferred until Stage13 exit audit
~~~

The previous Assault-first route remains superseded. Concrete skill runtimes remain deferred until the Stage13 exit gate declares:

~~~text
Core Gameplay Engine = FROZEN
Skill Runtime Readiness = READY
~~~

## 8. Current runtime checkpoint

```text
Stage13-B1 Runtime Integration   = IMPLEMENTED
Stage13-B2 Runtime Integration   = IMPLEMENTED
Stage13-B2.5 Runtime Integration = IMPLEMENTED
Stage13-B3 Treatment Core        = IMPLEMENTED / RUNTIME CORE FROZEN
Branch CI 37198181258            = 1683 passed / demo PASS
Independent PR/Main Audit        = PASS
Merged-main CI 37198353900        = 1683 passed / demo PASS
B3 merged-main commit            = a27785a830e6d3f89b0c17d93bdaa31f84c48207
B3 merged-main CI 37200488246     = PASS / demo PASS / audit snapshot PASS
```

B3 ordinary-treatment formula core is now integrated. Special recovery-family boundaries and other residual Stage13 debt remain open.

## 9. NEXT

```text
NEXT =
complete the remaining Stage13 core-engine architecture/governance and deterministic replay audit
special recovery families remain separate from ordinary treatment and are implemented under dedicated family contracts
```
