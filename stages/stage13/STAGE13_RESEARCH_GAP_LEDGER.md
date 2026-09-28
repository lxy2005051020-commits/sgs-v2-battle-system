# Stage13 Research Gap Ledger

> Stage13-A output.
>
> Rule: only a row whose disposition is RESEARCH_REQUIRED may open a focused empirical campaign. Runtime determinism questions stay in the Runtime Governance Ledger.

## 1. Research intake verdict

~~~text
New broad corpus scan                    FORBIDDEN
New focused blocking research families   1
Blocking exact questions                 2
Existing non-blocking research debt      PRESERVED
Stage1-12 automatic reopen               NO
~~~

The one blocking family is 690221 See-Through damage-family applicability. It contains two exact questions because ACTIVE_SKILL and DOT/DELAYED are distinct lanes in the frozen contract.

## 2. Canonical ledger

| Question ID | Mechanism | Exact Unknown | Why Runtime Needs It | Existing Evidence / Authority | What Would Discriminate | Priority | Blocking? | Disposition |
|---|---|---|---|---|---|---|:---:|---|
| RQ13-001 | 690221 See-Through / ACTIVE_SKILL | When 690221 is effective and a damage instance belongs to ACTIVE_SKILL, is the incoming reduction operand eligible for the frozen cap-before-pierce transform? | Full Active Skill damage integration would otherwise hit ContractBoundaryViolation whenever this state interaction is reachable | 690221 contract explicitly classifies ACTIVE_SKILL as UNSUPPORTED_UNKNOWN / 0 observed; frozen observed families must not be generalized | Tier-A battle reports with effective 690221, positive incoming reduction and directly attributable Active Skill damage; compare invocation/quantitative reduction against no-pierce model | P0 | YES | RESEARCH_REQUIRED |
| RQ13-002 | 690221 See-Through / DOT-DELAYED | When 690221 is effective and damage is DOT or other delayed damage, does 690221 transform the incoming reduction operand? | Delayed/persistent work is a Stage13 core gap and future skills may produce DOT; silent standard-reduction fallback would invent a rule | 690221 contract explicitly classifies DOT/DELAYED as UNSUPPORTED_UNKNOWN / 0 observed | Tier-A cases where source owns effective 690221, target carries measurable reduction, and a clearly attributable DOT/delayed instance settles; compare transformed vs ordinary reduction | P0 | YES | RESEARCH_REQUIRED |
| RQ13-003 | 690086 Distribution / DSTS9-B02 | The original empirical Distribution boundary recorded by Stage9/11 remains unobserved | Runtime already has an explicit project default; Stage13 must preserve truth/debt separation | Research maturity RUNTIME_READY_WITH_RESEARCH_DEBT; DSTS9-B02 OPEN / UNOBSERVED | Only direct model-separating evidence specified by the existing Distribution authority | P2 | NO | EXISTING_RESEARCH_DEBT / DO_NOT_AUTO_REOPEN |
| RQ13-004 | 690099 Alert bounded debt | Exact 600 equality and selected cross-provider teardown / basis details remain unobserved | Current frozen supported lane already has explicit project defaults or bounded debt; no Stage13 primitive depends on resolving these today | 690099 contract: FROZEN WITH BOUNDED DEBT; 600 equality UNOBSERVED / NON_BLOCKING | exact-threshold or cross-provider cases with unambiguous contributor provenance | P3 | NO | PRESERVE_BOUNDED_DEBT |
| RQ13-005 | 690070 Critical micro-read timing | hidden CritChance micro-read and critical bonus latch placement are not empirically distinguishable at current observability | Deterministic simulator placement is required, but the frozen contract explicitly classifies this as engineering choice / unobservable | 690070 frozen contract; blocking mechanics unknown = 0 | no current battle-report discriminator established | P3 | NO | RUNTIME_GOVERNANCE_REQUIRED, NOT RESEARCH |

## 3. RQ13-001 focused research prompt

~~~text
You are the Stage13 RQ13-001 690221 ACTIVE_SKILL Applicability Research Agent.

Goal:
Determine only whether effective 690221 See-Through applies its already-frozen
cap-before-pierce transform to ACTIVE_SKILL damage instances.

Do not re-research:
- 690221 state identity;
- cap-before-pierce math;
- observed NormalAttack / authorized Assault / observed command/reaction lanes;
- provider-specific Speed formula;
- generic Skill Runtime architecture.

Competing models:
A. ACTIVE_APPLICABLE
B. ACTIVE_NOT_APPLICABLE
C. FAMILY_OR_PROVIDER_CONDITIONAL
D. STILL_UNOBSERVED

Required evidence:
1. effective 690221 on the source at the relevant instance;
2. target has a quantitatively distinguishable incoming reduction;
3. damage is directly attributable to an Active Skill;
4. positive and negative controls;
5. quantitative model comparison;
6. counterexample search.

Output:
- Question Ledger;
- Evidence Ledger;
- discriminating cases;
- counterexamples;
- proposed contract amendment or explicit STILL_UNOBSERVED verdict;
- independent freeze audit prompt.

Do not infer hidden server behavior from current Runtime.
~~~

## 4. RQ13-002 focused research prompt

~~~text
You are the Stage13 RQ13-002 690221 DOT/DELAYED Applicability Research Agent.

Goal:
Determine only whether effective 690221 See-Through applies its frozen
cap-before-pierce transform to DOT / delayed damage instances.

Competing models:
A. DOT_DELAYED_APPLICABLE
B. DOT_DELAYED_NOT_APPLICABLE
C. APPLICATION_TIME_SNAPSHOT_DEPENDENT
D. SOURCE_OR_PROVIDER_CONDITIONAL
E. STILL_UNOBSERVED

Required evidence:
1. source has effective 690221 with provenance clear at the relevant time;
2. target has measurable incoming reduction;
3. damage instance is unambiguously DOT/delayed and not direct Active/NormalAttack;
4. source/provider validity and source-death context are recorded;
5. positive/negative controls;
6. quantitative discriminator and counterexample search.

Do not silently convert 690070/690069 application-bound critical rules into a
690221 timing rule. Those are separate authorities.

Output:
- Question Ledger;
- Evidence Ledger;
- candidate-model comparison;
- counterexamples;
- proposed contract amendment or explicit STILL_UNOBSERVED verdict;
- independent freeze audit prompt.
~~~

## 5. Research closure rule

RQ13-001/002 can close only as one of:

~~~text
NEW FROZEN RESEARCH AUTHORITY
or
EXPLICIT STAGE13 NON-BLOCKING UNSUPPORTED BOUNDARY
    with a documented reason Skill Runtime readiness does not require the lane
~~~

A Runtime Default may decide simulator mechanics only when the original-game behavior is unobservable and the project actually needs a deterministic choice. It may not relabel an observable-but-unobserved damage-family question as researched truth.
