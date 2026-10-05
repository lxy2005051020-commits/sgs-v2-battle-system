# Stage13 Runtime Governance Gap Ledger

> Stage13-A inventory output.
>
> This ledger inventories deterministic simulator decisions. It does not create new Runtime Defaults in Stage13-A.

## 1. Inherited governance

Stage13 inherits, without relabeling, all frozen Stage11/12 project defaults and bounded boundaries.

### Battle-owned Shared Foundation defaults

| ID | Existing Decision | Provenance |
|---|---|---|
| RD-SF-001 | legacy SkillDefinition classification compatibility: ACTIVE / no preparation for pre-Stage12 schema | PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN |
| RD-SF-002 | loaded Skill Provider deterministic enumeration by SkillSlot then skill_id | PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN |
| RD-SF-003 | same-envelope lifecycle due-removal snapshot and deterministic commit order | PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN |
| RD-SF-004 | EXHAUSTION denied new ACTIVE operation consumes zero activation RNG and zero target RNG | PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN |
| RD-SF-005 | PROVOCATION supported RANDOM CHOOSE_N reserve-required-target-first topology and RandomSystem.sample signature | PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN |
| RD-SF-006 | INTIMIDATION supported eligible-Provider selection uses stable pool and one RandomSystem.choice for multi-candidate Runtime behavior | PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN |

### Other inherited project defaults

- Stage11 Design Amendment 001: exact-speed cross-team legacy context without attacker metadata uses lexicographically smallest tied team id as compatibility attacker; consumes zero RNG.
- 690099 Alert supported runtime choices retain their explicit PROJECT_RUNTIME_DEFAULT provenance.
- Distribution × LifeSteal participant direct loss exclusion remains a PROJECT_RUNTIME_DEFAULT / RESEARCH_DEBT boundary.
- INSIGHT approved project defaults retain their research-side IDs/provenance and are not renumbered as Battle empirical truth.

## 2. Stage13 governance questions

The following are questions, not decisions.

| Governance ID | Mechanism | Deterministic Choice Runtime Must Eventually Make | Why It Is Governance, Not Research | Blocking | Current Status |
|---|---|---|---|:---:|---|
| RG13-001 | Generic gameplay opportunity ordering | stable ordering of multiple typed opportunities that share one committed envelope; relation to lifecycle settlement and finalization barriers | internal decomposition/order may be observationally equivalent unless a concrete contract distinguishes it | NO | RESOLVED_BY_EXISTING_AUTHORITY |
| RG13-002 | RNG decision trace | what constitutes one replay-visible random decision record: owner, operation id, API method, population identity/count, outcome identity | replay bookkeeping is simulator architecture, not original-game truth | NO | RESOLVED_BY_EXISTING_AUTHORITY |
| RG13-003 | New random primitive no-draw fast paths | whether probability 0/1, singleton choice, full-population selection and rejected work consume zero API-level draws in each new core primitive | hidden server PRNG consumption is not observable; simulator must remain deterministic and consistent with existing policy | NO | RESOLVED_BY_EXISTING_AUTHORITY |
| RG13-004 | Generic deterministic selector comparator | stable ordering when a selector is DETERMINISTIC but no gameplay-ranked selector is requested | container iteration order is simulator structure; should not become an accidental gameplay fact | NO | FORMAL_PROJECT_RUNTIME_DEFAULT |
| RG13-005 | Multi-effect failure semantics | stop-current, continue-siblings, abort-operation, and atomic-group boundaries for generic effect sequences | architecture must define commit safety; specific gameplay may select a mode later | NO | UNSUPPORTED_UNTIL_CONCRETE_CONTRACT |
| RG13-006 | Pending-work serialization identity | stable ID allocation / lineage fields and whether IDs are replay observations but never gameplay priority comparators | identity/serialization is simulator architecture | NO | RESOLVED_BY_EXISTING_AUTHORITY |
| RG13-007 | Generic usage-budget commit point | decrement on admission, successful execution, successful effect commit, or opportunity consumption | simulator must pick only after gameplay semantics are separated per consumer; a universal hidden rule must not be invented | NO | NON_BLOCKING_FUTURE_DECISION |
| RG13-008 | Pending-work defeat/finalization barrier | deterministic cancellation/continuation processing order when defeat and already-admitted synchronous work coexist | current frozen mechanisms establish examples, but a generic scheduler needs an explicit project-level barrier model | NO | RESOLVED_BY_EXISTING_AUTHORITY |
| RG13-009 | Replay canonicalization | stable serialization order for operation/effect/state snapshots where order carries no gameplay meaning | replay representation choice is project governance | NO | RESOLVED_BY_EXISTING_AUTHORITY |
| RG13-010 | Generic modifier contribution ordering | stable ordering for semantically commutative contribution sets vs explicit phase-ordered noncommutative contributions | representation order is governance; gameplay math/stacking remains domain authority | NO | RESOLVED_BY_EXISTING_AUTHORITY |

## 3. Non-governance questions

These must not be “solved” with a Runtime Default merely because coding would be convenient:

| Question | Correct lane |
|---|---|
| Does 690221 apply to ACTIVE_SKILL? | RESEARCH_REQUIRED |
| Does 690221 apply to DOT / delayed damage? | RESEARCH_REQUIRED |
| What is a concrete skill's target priority? | future Skill Contract / Research, not Stage13 generic default |
| What is a concrete skill's snapshot/JIT attribute rule? | future Skill Contract / existing authority; Stage13 provides both primitives |
| Is a state a buff/debuff for cleanse purposes? | mechanism/category authority, not UI inference |
| Does source death cancel a specific already-created effect? | mechanism/work authority; no universal default |
| 690086 DSTS9-B02 | existing Research Debt; preserve |

## 4. Governance decision schema

Any Stage13 Runtime Default created in Stage13-C must record:

~~~text
Default ID
Mechanism
Exact deterministic choice
Scope
Canonical owner
Reason Runtime must decide
Research status
Chosen behavior
RNG consequences, if any
Ordering consequences, if any
Serialization/replay consequences, if any
PROJECT_RUNTIME_DEFAULT
NOT_EMPIRICALLY_FROZEN
Required tests
Reopen trigger
Supersession rule
~~~

No Stage13-A row above is a Default merely because it has an RG13 ID.

## 5. RNG invariants inherited into Stage13

~~~text
BattleContext.random / RandomSystem = sole PRNG service

Policy/query layers consume 0 RNG unless a mechanism-specific
random-decision owner is explicitly delegated.

No:
  import random
  random.Random()
  numpy.random
  hash-based gameplay randomness
outside RandomSystem infrastructure.

EventBus never authorizes a draw.
~~~

For deterministic replay, Stage13 governance is at the RandomSystem API decision-operation level. It does not claim CPython random.Random bit-consumption is original-game behavior.

## 6. Default laundering guard

The following transformations are forbidden:

~~~text
PROJECT_RUNTIME_DEFAULT -> "observed rule"
UNSUPPORTED_BOUNDARY    -> silent fallback
stable serialization    -> gameplay priority
attribution metadata    -> dependency
EventBus fact           -> gameplay permission
test helper behavior    -> production authority
~~~

## 7. Stage13-C governance exit

Runtime-governance closure is reached only when every implementation-required RG13 question is either:

- resolved by existing frozen authority;
- resolved by a new formal PROJECT_RUNTIME_DEFAULT;
- proven unnecessary by architecture;
- or retained as an explicit non-blocking unsupported boundary.

Architecture and implementation may then consume the decision. They may not create it implicitly.
