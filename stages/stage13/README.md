# Stage13 · Core Gameplay Mechanism Completion

> Current status: ACTIVE / ENTRY GATE PASS / FOUNDATIONAL RESEARCH REPLAN ACTIVE
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
           B1 Wounded-Troop / Recoverable-Capacity Mechanics
           B2 Damage Increase / Reduction Mechanics
           B3 Recovery / Treatment Formula Mechanics
           CURRENT

Stage13-C  Residual State Mechanism Closure

Stage13-D  Consolidated Gap Classification + Runtime Governance
Stage13-E  Core Runtime Architecture Design
Stage13-F  Core Mechanism Implementation
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

## 3. Entry verdict

~~~text
CORE_GAMEPLAY_MECHANISM_INVENTORY       = COMPLETE
STAGE13_ENTRY_GATE                = PASS
Stage13 Readiness                       = READY
Stage13 Active                    = YES

Stage12 Runtime                         = FROZEN
Stage12 Complete                        = YES
Stage1-12 Reopen Required               = NO

Research FROZEN                         = 39 / 40
Runtime FROZEN TO CONTRACT              = 40 / 40
Strict Complete                         = 39 / 40
690086 DSTS9-B02                        = OPEN / UNOBSERVED
~~~

Inventory activation does not mean the Core Gameplay Engine is frozen:

~~~text
CORE_GAMEPLAY_ENGINE              = NOT YET FROZEN
Skill Runtime Readiness           = NOT YET READY
~~~

## 4. Foundational empirical research gate

Before architecture/implementation, Stage13 now requires three research programs.

### B1 — Wounded troops / recoverable capacity

Current Runtime clamps recovery by missing troops. That is not empirical proof that missing troops and recoverable wounded troops are universally identical in the original game.

Research must discriminate independent wounded-pool, missing-troop-equivalence, family-specific, and unobservable/default models.

### B2 — Damage increase / damage reduction

The Runtime already has typed modifier phases, but Stage13 must independently establish observable stacking, phase ordering, caps/floors and rounding instead of treating current code as the source of truth.

### B3 — Recovery / treatment formula

Recovery timing and lifecycle are mature, and LifeSteal has strong frozen arithmetic. The general treatment-rate/attribute-to-recovery mapping is not equivalently closed. Stage13 must research the numerical family and modifier ordering before declaring the recovery foundation complete.

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

Known entries include 690221 ACTIVE_SKILL, 690221 DOT/DELAYED, 690086 DSTS9-B02 and bounded 690099 issues. Existing frozen state contracts remain frozen outside the exact clause being reopened.

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

## 8. NEXT

~~~text
NEXT =
STAGE13_B1_WOUNDED_TROOP_AND_RECOVERABLE_CAPACITY_RESEARCH
~~~

B2 damage increase/reduction research follows, then B3 recovery/treatment-formula research, then Stage13-C residual state-mechanism closure.
