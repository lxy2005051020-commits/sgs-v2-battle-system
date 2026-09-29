# Stage13 Research Gap Ledger

> Status: CURRENT / foundational-research replan active
>
> Historical Stage13-A intake remains preserved, but its conclusion that only one new blocking empirical family existed is superseded by STAGE13_FOUNDATIONAL_RESEARCH_PRIORITY_REPLAN.md.
>
> Rule: Runtime behavior is not empirical evidence. Only observable original-game questions belong here.

## 1. Current research intake verdict

~~~text
Foundational empirical research families     4-step route
  B1 wounded-troop / recoverable capacity — FROZEN
  B2 damage increase / reduction mechanics — FROZEN
  B2.5 full damage advancement / hidden mechanism closure — ACTIVE / BLOCKED BY DATA REPRODUCIBILITY
  B3 recovery / treatment formula mechanics — AFTER B2.5 EXIT

Residual-state research phase                AFTER B1-B3
Known residual state questions               PRESERVED
Existing non-blocking research debt          PRESERVED
Stage1-12 automatic wholesale reopen         NO
~~~

## 2. Priority research ledger

| Question ID | Mechanism | Exact Unknown | Why It Matters | Existing Authority | Priority | Blocking? | Disposition |
|---|---|---|---|---|---|:---:|---|
| RQ13-B1 | Wounded troops / recoverable capacity | Independent wounded-pool semantics and recovery-capacity behavior | Foundation for all later recovery math | Frozen Stage13-B1 mechanism contract | P0-1 | CLOSED | FROZEN |
| RQ13-B2 | Damage increase / reduction | Same-side accumulation, cross-side composition, clamp, crit, morale, temporal and overkill modifier semantics | Foundation for full-event damage replay | Frozen Stage13-B2 unified mechanism contract; official restraint correction = 1.12/1.00/0.88 | P0-2 | CLOSED | FROZEN |
| RQ13-B2.5 | Full damage advancement / hidden mechanism closure | Do advancement outgoing/incoming modifiers enter ordinary same-side pools or independent multiplicative layers, and do clean full-event residuals expose any additional hidden damage mechanisms? | A wrong advancement placement or hidden factor prevents per-event damage explanation even with B2 topology frozen | Stage2 Base Damage Formula V1 exists; Q43/Q45 remain METHOD_GATE; historical candidate CSVs are zero-byte on current research main | P0-2.5 | YES | ACTIVE / BLOCKED_BY_DATA_REPRODUCIBILITY |
| RQ13-B3 | Recovery / treatment formula | How do treatment rate, INT/COMMAND and recovery modifiers map to nominal recovery before final capacity clamp? | Recovery states and healing skills cannot be numerically faithful without this | Trigger/lifecycle contracts are strong; exact formula constants are explicitly FORMULA_RESEARCH_OUT_OF_SCOPE in current state contracts | P0-3 | YES | RESEARCH_REQUIRED |
| RQ13-001 | 690221 See-Through / ACTIVE_SKILL | Does cap-before-pierce apply to ACTIVE_SKILL damage? | Needed for broad Active Skill interaction fidelity | Frozen contract says UNSUPPORTED_UNKNOWN / zero observed | P1 | YES | DEFER_TO_STAGE13_C / RESEARCH_REQUIRED |
| RQ13-002 | 690221 See-Through / DOT-DELAYED | Does cap-before-pierce apply to DOT or other delayed damage? | Needed for delayed/persistent skill-produced damage | Frozen contract says UNSUPPORTED_UNKNOWN / zero observed | P1 | YES | DEFER_TO_STAGE13_C / RESEARCH_REQUIRED |
| RQ13-003 | 690086 Distribution / DSTS9-B02 | Existing empirical Distribution boundary remains unobserved | Runtime has explicit project default; truth/debt separation must remain | Research maturity RUNTIME_READY_WITH_RESEARCH_DEBT | P2 | NO | STAGE13_C_AUDIT / DO_NOT_AUTO_REOPEN |
| RQ13-004 | 690099 Alert bounded debt | Exact 600 equality and selected teardown/basis details remain unobserved | May matter to final state-debt completeness, but does not block B1-B3 | Frozen with bounded debt | P2 | NO | STAGE13_C_AUDIT |
| RQ13-005 | 690070 Critical micro-read timing | Hidden micro-read/latch placement is not currently battle-report distinguishable | Simulator needs deterministic placement, but empirical closure may be impossible | Frozen contract classifies it as unobservable/engineering choice | P3 | NO | RUNTIME_GOVERNANCE_REQUIRED |

## 3. RQ13-B1 required discrimination

Research must distinguish at least:

~~~text
A. MISSING_TROOPS_EQUIVALENCE
   recoverable capacity == max_troops - current_troops

B. INDEPENDENT_WOUNDED_POOL
   only a subset of lost troops is recoverable

C. DAMAGE_FAMILY_DEPENDENT
   wound generation differs by damage/direct-loss family

D. CONTEXT_DEPENDENT
   overkill, defeat, share/distribution or other context changes recoverability

E. UNOBSERVABLE
   battle reports cannot discriminate the hidden quantity
~~~

Required evidence areas:
- ordinary weapon and strategy damage;
- DOT where available;
- repeated damage followed by recovery;
- large recovery requests that can reveal a cap;
- direct troop loss / Share / Distribution where discriminating samples exist;
- overkill and near-defeat boundaries;
- positive and negative controls.

## 4. RQ13-B2 required discrimination

Research must separately test:
- outgoing increase with outgoing increase;
- outgoing reduction with outgoing reduction;
- incoming increase with incoming increase;
- incoming reduction with incoming reduction;
- outgoing versus incoming cross-family composition;
- coefficient versus modifier ordering;
- critical/strategy-critical versus ordinary modifiers;
- morale and troop-restraint ordering where observable;
- stage-local versus final-only integerization;
- caps/floors;
- 690221 ordinary incoming-reduction pool formation.

Competing models must include additive, multiplicative and family-grouped composition. Do not assume one universal rule before evidence separates the families.

## 5. RQ13-B3 required discrimination

Research must separately establish:
- fixed treatment-rate family;
- INT-scaled treatment family;
- COMMAND-scaled recovery family where explicitly present;
- source-side recovery modifier;
- target-side received-recovery modifier;
- state-specific recovery modifier;
- modifier stacking/order;
- integerization points;
- application-time snapshot versus resolution-time reads;
- final interaction with the B1 recoverable-capacity result.

Existing 690094/690095 RecoveryBasis and first/second CEIL authority stays frozen unless contradictory evidence directly forces a reopen.

## 6. Stage13-C residual state mechanism audit

After B1-B3, scan all 40 state contracts for unresolved clauses using these markers:

~~~text
OPEN
UNOBSERVED
BOUNDED_UNKNOWN
UNSUPPORTED_UNKNOWN
PROJECT_RUNTIME_DEFAULT
RESEARCH_DEBT
FORMULA_RESEARCH_OUT_OF_SCOPE
~~~

Each clause is classified as:
- CLOSE_NOW_BY_RESEARCH;
- PRESERVE_NONBLOCKING_DEBT;
- RUNTIME_GOVERNANCE_ONLY;
- UNOBSERVABLE_WITH_EXPLICIT_DEFAULT;
- NOT_REQUIRED_FOR_CORE_ENGINE.

Only the clause is reopened. A frozen state is not wholesale reopened.

## 7. Research closure rule

A research question can close only through:
1. Question Ledger;
2. Evidence Ledger;
3. positive / negative / boundary controls;
4. competing-model discrimination;
5. counterexample search;
6. contract or foundation-authority amendment;
7. independent freeze audit.

A Runtime Default may resolve deterministic simulator behavior when original-game behavior is unobservable. It may not relabel observable-but-unobserved behavior as researched truth.

## 8. Current next target

~~~text
STAGE13_FULL_DAMAGE_ADVANCEMENT_HIDDEN_MECHANISM_RESEARCH
~~~

B1 and B2 are frozen. B2.5 must use the existing Stage2 Base Damage Formula V1 as baseline, test advancement same-pool vs independent models with high-separation cases, and treat clean nearest-legal-prediction residuals greater than 1 as anomaly leads.


## 9. B2.5 execution checkpoint

Research has built the B2.5 normalized event / replay / residual-analysis toolchain, but the historical candidate datasets referenced by B2 prose are not reproducible from committed CSV artifacts because those CSVs are empty. This does not reopen B2. It blocks only B2.5 closure until the external raw corpus is replayed.

```text
RQ13-B2.5 = ACTIVE / BLOCKED_BY_DATA_REPRODUCIBILITY
Q43 = METHOD_GATE
Q45 = METHOD_GATE
FULL_DAMAGE_ORACLE = NOT CLOSED
B3 START = NOT AUTHORIZED YET
Runtime gameplay modification = NOT AUTHORIZED
```
