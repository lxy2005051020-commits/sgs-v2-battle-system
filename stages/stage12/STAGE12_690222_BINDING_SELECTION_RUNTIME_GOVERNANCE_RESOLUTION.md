# Stage12 690222 INTIMIDATION Binding Selection Runtime Governance Resolution

Date: 2026-09-28  
Command: `STAGE12_690222_BINDING_SELECTION_RUNTIME_GOVERNANCE_RESOLUTION`  
Scope: Runtime governance only. No 690222 gameplay adapter is implemented in this round.

## A. Repository Lock

```text
Battle repository = lxy2005051020-commits/sgs-v2-battle-system
Battle main baseline = e113cb44e8537b21276e58e8d4745aeacd8d500b

Research repository = lxy2005051020-commits/sgs-state-mechanics-research
Research main baseline = e18ae56a4db5662b87458dfa8fdff25dcdd8053b
Research repository mode = READ ONLY
```

Both baselines were re-read before this resolution. The Research repository is intentionally unchanged.

## B. Governance Scope

This round resolves exactly one implementation-required unknown:

```text
690222 INTIMIDATION
+ two or more supported eligible Skill Providers
-> what probability distribution does the simulator use for the single binding decision?
```

It does not implement Intimidation gameplay and does not reopen Shared Foundation ownership.

## C. Frozen Research Boundary

Frozen Research remains:

```text
exactly one eligible skill is randomly selected
refresh performs selection again
uniform / equal / 1/N is not empirically proven
```

Therefore this resolution must not be cited as evidence of original-game hidden weights.

## D. Current Runtime Governance Audit

Before this round:

```text
RD-SF-002 = deterministic Provider enumeration only
Intimidation exact weights = DEFERRED
RandomSystem = sole battle RNG service
Intimidation CREATE / successful REFRESH = binding decision
Intimidation RESUME = no binding decision
empty eligible pool = UNSUPPORTED_BOUNDARY
```

The integration gate now makes the weighting choice mandatory, so DQ-SF-14 governance requires an explicit Project Runtime Default.

## E. Eligible Provider Pool Boundary

The input population is the already-governed Intimidation supported pool built from loaded Skill Provider identity and frozen type taxonomy:

```text
SUPPORTED
ACTIVE
ACTIVE + PreparationMode.REQUIRED (Preparation Active)
ASSAULT
PASSIVE
COMMAND
TROOP

EXCLUDED
FORMATION

OUTSIDE DOMAIN
NORMAL_ATTACK

UNSUPPORTED / NOT FROZEN
TALENT
EQUIPMENT
BINGSHU
```

The Shared Foundation identity design already states that loaded Provider enumeration does not itself filter ProviderValidity. A loaded Provider is not turned into MISSING merely because it is BASELINE_DISABLED or currently SUPPRESSED. This resolution therefore does not invent an additional validity-based denominator filter.

TALENT eligibility remains UNSUPPORTED / NOT FROZEN. TALENT is not added to the supported eligible pool.

## F. RD-SF-002 Stable Ordering

Before any random selection, the supported pool is serialized in RD-SF-002 owner-local order:

```text
INHERENT / slot 0
-> LEARNED_1 / slot 1
-> LEARNED_2 / slot 2
-> skill_id deterministic consistency tiebreaker
```

No set iteration, dict incidental order, or registry insertion accident may define the random population order.

## G. Candidate Distribution A

Candidate A:

```text
Uniform over currently supported eligible Providers
P(provider_i) = 1 / N
```

Engineering properties:

- symmetric when no weight evidence exists;
- no extra metadata;
- no second RNG owner;
- one direct final choice;
- simple replay signature;
- trivial future replacement if stronger authority arrives.

Its limitation is explicit: it is not empirically proven.

## H. Candidate Distribution B

Candidate B: slot-weighted selection.

Rejected because no frozen authority provides slot weights. Assigning different probabilities to INHERENT / LEARNED_1 / LEARNED_2 would introduce extra gameplay parameters unrelated to the observable Research contract.

## I. Candidate Distribution C

Candidate C: SkillType-weighted selection.

Rejected because no frozen authority supplies ACTIVE / ASSAULT / PASSIVE / COMMAND / TROOP weights. This would introduce more invented metadata than Candidate A.

## J. Candidate Comparison

A deterministic hash mapping is also rejected. It would bypass the canonical RandomSystem decision stream and alter replay accounting while pretending to satisfy the word "random".

The minimum-additional-assumption choice is Candidate A. "Minimum assumption" is an engineering criterion, not a claim that the game uses uniform weights.

## K. Runtime Default Decision

```text
DECISION = UNIFORM OVER THE ALREADY-CONSTRUCTED SUPPORTED ELIGIBLE PROVIDER POOL
```

For `N >= 2`:

```text
P(provider_i) = 1 / N
```

For `N == 1`, selection is deterministic and consumes no binding RNG.

For `N == 0`, this resolution does not choose gameplay semantics; the existing unsupported boundary remains.

## L. Runtime Default ID / Provenance

```text
RD-SF-006
Mechanism = 690222 INTIMIDATION
Classification = PROJECT_RUNTIME_DEFAULT
Evidence status = NOT_EMPIRICALLY_FROZEN
```

RD-SF-006 does not claim the original game's hidden binding weights.

## M. Probability Distribution

The denominator is:

```text
N = number of members in the supported Intimidation eligible pool
    after loaded-Provider enumeration and frozen SkillType-domain filtering
```

It is not all skill slots, all runtime records, Equipment, Formation, TALENT, Bingshu, or Normal Attack.

## N. RNG Owner / API

Sole RNG service:

```text
BattleContext.random
-> RandomSystem
```

Multi-candidate API:

```text
RandomSystem.choice(stable_eligible_pool)
```

Exactly one `choice` API operation selects the final Provider. No local `random`, NumPy RNG, hash mapping, sampling-plus-indexing, or second Intimidation RNG service is permitted.

## O. Single-candidate Topology

```text
eligible_count = 1
-> select sole Provider
-> 0 binding RNG
```

The next RandomSystem decision must be at the same stream position as a baseline that performed no binding draw.

## P. Multi-candidate Topology

```text
eligible_count >= 2
-> RD-SF-002 stable pool
-> exactly one RandomSystem.choice(pool)
-> selected Provider
```

No pre-choice shuffle and no secondary draw are authorized.

## Q. CREATE RNG Topology

```text
admission
-> conflict
-> deterministic preflight
-> supported eligible pool construction
-> binding selection if pool cardinality requires RNG
-> transaction commit
```

Rejected application -> 0 binding RNG.

Gangyi rejection -> 0 binding RNG.

## R. REFRESH RNG Topology

A successful Intimidation REFRESH:

```text
rebuild supported eligible pool
-> perform a new RD-SF-006 binding decision
-> commit refreshed generation/binding
```

For a multi-candidate pool this is exactly one new `RandomSystem.choice` operation. For a single-candidate pool it is a new binding decision but 0 RNG because the result is forced.

## S. RESUME RNG Topology

```text
SUPPRESSED -> EFFECTIVE
-> retain exact bound Provider
-> 0 binding-selection RNG
-> same application generation
-> same lifetime progress
```

Resume never rerolls.

## T. Same-provider Refresh Semantics

A REFRESH may select the same Provider that was bound before the refresh.

That result still means:

```text
new binding-selection operation occurred
application generation advances
lifetime refresh semantics apply
binding value happens to be equal
```

It must not be reclassified as "binding retained without selection".

## U. Replay Signature

Replay inputs for the binding decision include at least:

```text
RandomSystem seed / current RNG state
holder identity
application generation
RD-SF-002 stable supported eligible Provider list
Provider identities
RD-SF-006 version/provenance
```

Equal inputs must reproduce the same selected Provider and the same subsequent RandomSystem stream position.

## V. Downstream RNG Stability

Governance tests pin API-level stream behavior:

- one-candidate path makes zero `choice` calls;
- multi-candidate path makes exactly one `choice` call;
- same seed + same pool gives the same binding;
- after the binding decision, the next RandomSystem result matches a reference stream with the same governed call topology.

This governs RandomSystem API operations, not CPython's undocumented internal bit consumption as a historical-game fact.

## W. Empty-pool Boundary

```text
empty eligible pool remains UNSUPPORTED_BOUNDARY
```

RD-SF-006 does not choose "no binding", fallback to Formation, rejection semantics, or another random domain.

## X. TALENT Boundary

```text
TALENT eligibility remains UNSUPPORTED / NOT FROZEN
TALENT is not added to the supported eligible pool
```

The 690107 taxonomy amendment created a TALENT discriminator only; it did not authorize Intimidation eligibility.

## Y. Reopen Trigger

RD-SF-006 may be replaced only by stronger authority, including:

- Tier-A model-separating battle evidence;
- official-client evidence;
- deterministic observations distinguishing uniform from weighted selection;
- higher-authority gameplay evidence;
- a future audited/frozen 690222 contract update;
- a later Shared Foundation governance decision that explicitly supersedes this default.

## Z. Tests Added

```text
tests/test_stage12_690222_binding_selection_governance.py
```

The suite covers provenance, RD-SF-002 ordering, single/multi-candidate call topology, deterministic replay, downstream RNG position, REFRESH, same-provider REFRESH, RESUME, empty-pool/TALENT boundaries, and deterministic seed reachability.

These are governance/executable-spec tests. They do not pretend a production 690222 gameplay adapter exists.

## AA. Static Architecture Audit

Expected and preserved:

```text
690222 production gameplay adapter = absent / unregistered
no Intimidation gameplay branch introduced
no direct random import introduced
RandomSystem remains sole RNG service
RD-SF-002 ordering unchanged
TALENT not added
FORMATION not added
NORMAL_ATTACK not added
690109 / 690110 gameplay not introduced
```

## AB. Stage9 Regression

```text
PENDING CI VALIDATION
```

## AC. Stage10 Regression

```text
PENDING CI VALIDATION
```

## AD. Stage11 Regression

```text
PENDING CI VALIDATION
```

## AE. 690089 Regression

```text
PENDING CI VALIDATION
```

## AF. 690101 Regression

```text
PENDING CI VALIDATION
```

## AG. 690107 Regression

```text
PENDING CI VALIDATION
```

## AH. 690108 Regression

```text
PENDING CI VALIDATION
```

## AI. Shared Foundation Regression

```text
PENDING CI VALIDATION
```

## AJ. Research Changes

```text
NONE
Research repository remains read-only at e18ae56a4db5662b87458dfa8fdff25dcdd8053b
```

## AK. Production Gameplay Changes

```text
NONE
```

No 690222 gameplay adapter, StateInstance binding mutation, ProviderValidity suppression adapter, preparation interruption branch, or source-skill counter behavior is implemented in this round.

## AL. pytest / demo / CI

Baseline before this governance round:

```text
1392 passed
demo = PASS
```

Final branch/PR validation is recorded after CI completes.

## AM. Files Created / Updated

Created:

```text
stages/stage12/STAGE12_690222_BINDING_SELECTION_RUNTIME_GOVERNANCE_RESOLUTION.md
tests/test_stage12_690222_binding_selection_governance.py
stages/stage12/STAGE12_690222_INTIMIDATION_RUNTIME_INTEGRATION.md
```

Updated governance/status files are listed in the final validated revision.

## AN. Commit SHA

```text
PENDING VALIDATED PR HEAD / MERGE SHA
```

## AO. Blocker Verdict

Governance decision:

```text
Binding Governance = RESOLVED SUBJECT TO CI
IMPLEMENTATION_BLOCKER-690222-BINDING-WEIGHTS-001 = CLOSED SUBJECT TO CI
```

No new binding-pool blocker is opened because existing frozen Shared Foundation identity design already supplies the pool-construction boundary used by this default.

## AP. Current Gates

Until CI validation and merge:

```text
690222 Research = FROZEN
690222 Gameplay = NOT_INTEGRATED
690222 Runtime = NOT_FROZEN
Binding Governance = RESOLVED SUBJECT TO CI
Stage12 Runtime Frozen = 4 / 7
Research Reopen Required = NO
Shared Foundation Reopen Required = NO
```

Blocker closure does not increment Stage12 Runtime Frozen.

## AQ. NEXT

After CI validation and merge:

```text
Resume 690222 INTIMIDATION Runtime Integration
```

The resumed integration may implement the frozen pool construction, RD-SF-006 binding selection, resident binding storage, selected-Provider suppression, REFRESH reroll, RESUME stable binding, preparation interruption, Gangyi rejection, and contract-required cross-state interactions.