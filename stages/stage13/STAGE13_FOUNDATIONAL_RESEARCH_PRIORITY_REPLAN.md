# Stage13 Foundational Research Priority Replan

> Status: CURRENT STAGE13 ROUTE AMENDMENT
>
> Effective: 2026-09-28
>
> Supersedes: the Stage13-A conclusion that only 690221 family applicability constitutes new blocking empirical research.
>
> Preserves: Stage13-A inventory as a historical audit of the then-visible Runtime surface. It is not rewritten or deleted.

## 1. Decision

Stage13 remains **Core Gameplay Mechanism Completion**, but its research order is changed.

Before generic runtime architecture work or large-scale state-gap closure, the project must first resolve three foundational empirical domains:

1. **Wounded-troop / recoverable-capacity mechanics**;
2. **Damage increase / damage reduction aggregation and ordering**;
3. **General recovery / treatment-value formula mechanics**.

Only after those three foundations reach an auditable research verdict does Stage13 proceed to systematic residual state-mechanism closure.

This change exists because Runtime support is not equivalent to empirical closure. Current production code can settle recovery and damage modifiers, but it does not by itself prove the original game's hidden wounded-pool model, universal damage-modifier mathematics, or treatment-rate-to-recovery formula.

## 2. New Stage13 sequence

~~~text
Stage13-A  Core Gameplay Mechanism Inventory Audit
           COMPLETE

Stage13-B  Foundational Empirical Mechanics Research
           B1 Wounded-Troop / Recoverable-Capacity Mechanics — FROZEN
           B2 Damage Increase / Reduction Mechanics — FROZEN
           B2.5 Full Damage Advancement / Hidden Mechanism Closure — ACTIVE
           B3 Recovery / Treatment Formula Mechanics — AFTER B2.5

Stage13-C  Residual State Mechanism Closure
           audit all 40 state contracts for OPEN / UNOBSERVED /
           BOUNDED / UNSUPPORTED empirical debt
           then run focused evidence campaigns where closure is useful

Stage13-D  Consolidated Gap Classification + Runtime Governance
Stage13-E  Core Runtime Architecture Design
Stage13-F  Core Mechanism Implementation
Stage13-G  Independent Engine Completion / Deterministic Replay Audit
~~~

Stage14+ remains the Skill System.

## 3. Stage13-B1 — wounded-troop / recoverable-capacity research

Current Runtime behavior:

~~~text
recoverable capacity = max_troops - current_troops
~~~

This is a simulator rule, not proof that the original game has no independent wounded-troop pool.

Research must determine, as far as battle-report observability permits:

- whether all troop loss is recoverable;
- whether recoverable wounded troops differ from irreversible losses;
- whether damage family changes wounded generation;
- whether direct troop-loss effects, Share and Distribution participate identically;
- whether overkill changes recoverable capacity;
- whether wounded capacity accumulates, decays or is consumed by other rules;
- whether target defeat hard-zeros an otherwise existing wounded pool;
- whether end-of-battle treatment semantics expose a distinguishable wounded quantity;
- whether observed healing caps equal simple missing troops or a smaller wounded quantity.

Allowed verdicts include a frozen independent-pool rule, a frozen equivalence rule, a bounded family-specific rule, or explicit UNOBSERVABLE with a Runtime Default. The research must not assume an independent pool merely because the client uses a wounded-troop concept.

## 4. Stage13-B2 — damage increase / reduction mechanics

The current Runtime has typed modifier phases and deterministic ordering. Stage13-B2 must determine the observable game mathematics rather than inferring truth from the current implementation.

Research scope includes:

- stacking of multiple outgoing damage increases;
- stacking of multiple outgoing damage reductions;
- stacking of multiple incoming damage increases;
- stacking of multiple incoming damage reductions;
- same-family additive vs multiplicative behavior;
- cross-family combination behavior;
- cap/floor behavior where observable;
- ordering against coefficient, critical/strategy critical, morale, troop-type restraint and single-hit adjustments;
- integerization / rounding boundaries between modifier stages;
- source/provider-specific exceptions;
- the ordinary reduction pool used by 690221 See-Through.

The goal is not to force one universal formula if evidence instead shows distinct modifier families.

## 5. Stage13-B3 — recovery / treatment formula mechanics

Trigger timing, lifecycle, HealingBlock and several recovery-family interactions are already frozen. Stage13-B3 focuses on **how nominal recovery amount is calculated**.

Research scope includes:

- treatment-rate to recovery conversion;
- source Intelligence influence;
- source Command influence where the skill explicitly uses it;
- fixed-rate vs attribute-scaled families;
- source-side recovery increase/decrease;
- target-side received-recovery increase/decrease;
- state-specific recovery modifiers;
- stacking and ordering of recovery modifiers;
- integerization / rounding points;
- application-time snapshot vs resolution-time reads;
- interaction with the Stage13-B1 recoverable-capacity result.

Existing LifeSteal / StrategyLifeSteal first-CEIL and canonical recovery-modifier second-CEIL authority remains frozen unless direct contradictory evidence requires reopen.

## 6. Stage13-C — residual state mechanism closure

After B1-B3, conduct a ledger audit across all 40 official-state contracts.

The audit must enumerate, not hide:

~~~text
OPEN
UNOBSERVED
BOUNDED_UNKNOWN
UNSUPPORTED_UNKNOWN
PROJECT_RUNTIME_DEFAULT
RESEARCH_DEBT
FORMULA_RESEARCH_OUT_OF_SCOPE
~~~

Each item must then be classified as:

~~~text
CLOSE_NOW_BY_RESEARCH
PRESERVE_NONBLOCKING_DEBT
RUNTIME_GOVERNANCE_ONLY
UNOBSERVABLE_WITH_EXPLICIT_DEFAULT
NOT_REQUIRED_FOR_CORE_ENGINE
~~~

This stage includes the already-known:
- 690221 ACTIVE_SKILL applicability;
- 690221 DOT / DELAYED applicability;
- 690086 DSTS9-B02;
- 690099 bounded threshold / teardown debt;
- any formula-out-of-scope clauses exposed by B1-B3.

A frozen state is not automatically reopened wholesale. Only the identified unresolved clause is reopened.

## 7. Governance

- Evidence authority remains official/client evidence, then Tier-A battle reports, then discriminating controls.
- Runtime code is never evidence for original-game behavior.
- PROJECT_RUNTIME_DEFAULT never becomes empirical truth by repetition.
- Existing Stage1-12 frozen contracts remain valid outside explicitly reopened clauses.
- No Skill Runtime implementation begins before Stage13-G exit.
- No CoreGameplayGodObject is allowed; REUSE -> EXTEND -> COMPOSE remains the runtime architecture policy.

## 8. Immediate next action

The original 2026-09-28 ordering has progressed: B1 and B2 are now frozen. A 2026-09-29 amendment inserts B2.5 before B3 so the project can reconcile Stage2 Base Damage Formula V1 with the frozen B2 modifier contract and close advancement arithmetic / hidden damage residuals.

~~~text
NEXT =
STAGE13_FULL_DAMAGE_ADVANCEMENT_HIDDEN_MECHANISM_RESEARCH
~~~

Authority: `STAGE13_FULL_DAMAGE_ADVANCEMENT_HIDDEN_MECHANISM_REPLAN.md`.

B3 follows B2.5. Runtime implementation remains unauthorized.
