# Stage12 690108 PROVOCATION / BU-P02 Runtime Governance Resolution

Date: 2026-09-27  
Command: `STAGE12_690108_BU_P02_RUNTIME_GOVERNANCE_RESOLUTION`  
Classification: Runtime governance only; no 690108 gameplay integration in this round.

## A. Repository Lock

```text
Battle main at start:
939fb6ccbc3f313ba2d7dda7f491bc94ca2eeb4d

Research main at start:
e18ae56a4db5662b87458dfa8fdff25dcdd8053b
```

Both matched the commanded baselines.

## B. Governance Scope

This round resolves only the deterministic implementation micro-order for:

```text
690108 PROVOCATION
NEW_QUERY
+ RANDOM
+ CHOOSE_N(N)
+ one admissible required Source
```

It does not implement the Provocation state adapter or producer mapping.

## C. Frozen Research Boundary

```text
690108 Research = FROZEN
BU-P02 empirical micro-order = CLOSED_WITH_BOUNDED_UNKNOWN
Research Reopen Required = NO
```

The frozen observable rule remains: Source exactly once, total cardinality N preserved.

## D. Current Target Runtime Audit

Production source confirms:

```text
SkillTargetPolicy
-> emits legal required_target_ids
-> 0 RNG

SkillResolver._select_policy_targets()
-> required targets first
-> remove required IDs from remaining pool
-> slots = requested_count - required_count
-> delegate fill to TargetSystem

TargetSystem.random_units()
-> sole target random selection primitive
-> zero RandomSystem.sample when count == 0
-> zero RandomSystem.sample when all remaining candidates are selected
-> otherwise RandomSystem.sample(values, k)

BattleContext.random
-> RandomSystem
-> sole PRNG service
```

`TargetSelectionResult` is immutable and continuation modes reuse/derive/lock the prior operation identity rather than issuing a new query.

## E. Candidate A: Reserve-first

Topology:

```text
eligible
-> identify legal required Source
-> reserve Source
-> remove Source from remaining population
-> sample/fill N-1 from remaining
-> final = Source + fill
```

It matches the frozen owner topology and needs no new gameplay owner.

## F. Candidate B: Sample-then-replace

Topology:

```text
eligible
-> sample N
-> if Source absent, replace one selected target
```

This requires post-selector target mutation and, when Source is absent, a replacement-victim rule not frozen by Research or Shared Foundation.

## G. Candidate Comparison

| Dimension | Reserve-first | Sample-then-replace |
|---|---|---|
| Frozen topology compatibility | direct reuse | post-selector mutation |
| RNG owner | TargetSystem only | TargetSystem plus mutation stage |
| RNG call population | eligible - required | full eligible |
| RNG sample count | N - required_count | N |
| New micro-policy | none | replacement victim |
| Replay simplicity | single selector topology | selector + mutation |
| Existing generic code | compatible | redesign pressure |
| Shared Foundation reopen pressure | none | potentially material |

## H. Runtime Default Decision

```text
Decision = RESERVE-FIRST
```

The reason is governance compatibility and deterministic replay simplicity, not an empirical claim about the original game's hidden implementation.

## I. Default ID / Provenance

```text
RD-SF-005
PROJECT_RUNTIME_DEFAULT
NOT_EMPIRICALLY_FROZEN
```

This decision does not claim empirical evidence for the game's hidden target-selection micro-order.

## J. CHOOSE_N Selection Topology

For ordinary supported Provocation:

```text
required_count = 1
remaining_slots = N - 1
remaining_population = eligible - Source
final = Source + selector_fill
```

No post-selector replacement is allowed by RD-SF-005.

## K. RNG Owner

```text
Provocation adapter RNG = 0
SkillTargetPolicy RNG = 0
TargetSystem -> BattleContext.random = sole target RNG owner
```

## L. RNG Call Topology

Supported sufficient-candidate cases:

```text
remaining_slots == 0
-> 0 RandomSystem.sample calls

len(remaining_population) == remaining_slots
-> 0 RandomSystem.sample calls
-> deterministic all-candidate order

0 < remaining_slots < len(remaining_population)
-> exactly 1 RandomSystem.sample(remaining_population, remaining_slots)
```

## M. Draw / No-draw Cases

`N = 1` with the required Source filling the only slot consumes zero target RNG.

Selecting every remaining candidate consumes zero target RNG under the existing canonical TargetSystem rule.

Insufficient candidates are not normalized here.

## N. Replay Consequences

Same seed + same battle state + same TargetOperation + same effective Provocation + same legal candidate ordering + same required Source must produce:

```text
same target RandomSystem API topology
same final TargetSelectionResult
same subsequent RNG stream position
```

## O. NEW_QUERY / Freshness Scope

RD-SF-005 applies only to a fresh `NEW_QUERY`.

```text
INHERIT_RESOLVED
DERIVE_FROM_RESOLVED
LOCK_RESOLVED
```

do not re-run BU-P02 selection.

## P. SelectorKind Scope

```text
RANDOM
= RD-SF-005 BU-P02 micro-order applies

DETERMINISTIC
= generic required-slot architecture only; no RNG semantics added

EXPLICIT
= outside BU-P02 random micro-order; must be fully specified by its own boundary
```

## Q. Insufficient-candidate Boundary

```text
BU-P09 = UNSUPPORTED_BOUNDARY
```

The legacy `TargetSystem.random_units()` truncation behavior is not promoted into the 690108 contract by this decision.

## R. Reopen Trigger

RD-SF-005 may be reopened only by stronger authority such as:

- Tier-A/model-separating battle evidence;
- official-client evidence;
- stronger deterministic replay evidence proving a different observable micro-order;
- a higher-authority Shared Foundation redesign.

## S. Tests Added

```text
tests/test_stage12_690108_bu_p02_runtime_governance.py
```

Executable discriminators:

```text
test_choose_n_required_target_preserves_n
test_choose_n_required_target_exactly_once
test_choose_n_required_target_rng_owner_is_target_system
test_choose_n_policy_consumes_zero_rng
test_choose_n_new_query_replay_deterministic
test_choose_n_subsequent_rng_stream_stable
test_choose_n_n_equals_one_zero_target_draw_if_required_fills_slot
test_inherited_result_does_not_reselect
test_derived_result_does_not_reselect
test_locked_result_does_not_reselect
test_required_target_reserved_before_random_fill
test_random_fill_excludes_required_target
test_random_fill_count_is_n_minus_required_count
test_no_post_selector_replacement
```

## T. Static Architecture Audit

Confirmed by production source audit:

```text
SkillTargetPolicy = 0 RNG
Provocation adapter = still unregistered
TargetSystem = sole target RNG owner
no post-resolution historical rewrite
no NormalAttack change
no ActionSystem change
no Stage13 / Stage14 / Stage15 change
```

## U. Stage9 Regression

```text
PENDING PR CI
```

No Stage9 production code changed.

## V. Stage10 Regression

```text
PENDING PR CI
```

No Stage10 production code changed.

## W. Stage11 Regression

```text
PENDING PR CI
Stage11 Reopen Required = NO
```

## X. 690089 Regression

```text
PENDING PR CI
```

No 690089 production code changed.

## Y. 690101 Regression

```text
PENDING PR CI
```

No 690101 production code changed.

## Z. 690107 Regression

```text
PENDING PR CI
```

No 690107 production code changed.

## AA. Shared Foundation Regression

```text
PENDING PR CI
Owner graph unchanged
```

Only governance documentation and generic selector tests are added.

## AB. Research Changes

```text
NONE
```

Research repository remains read-only at `e18ae56a4db5662b87458dfa8fdff25dcdd8053b`.

## AC. Production Changes

Gameplay production changes:

```text
NONE
```

Generic selector production code changes:

```text
NONE
```

The existing generic reserve-first topology is governed, not rewritten.

## AD. pytest / demo / CI

```text
Baseline before round = 1299 passed
Governance suite expected to raise total above 1299
PR CI = PENDING
demo = PENDING
```

## AE. Files Created / Updated

Created:

```text
tests/test_stage12_690108_bu_p02_runtime_governance.py
stages/stage12/STAGE12_690108_BU_P02_RUNTIME_GOVERNANCE_RESOLUTION.md
```

Updated:

```text
stages/stage12/STAGE12_RUNTIME_DEFAULT_LEDGER.md
stages/stage12/STAGE12_RNG_EVENT_DEFAULT_GOVERNANCE.md
stages/stage12/STAGE12_SHARED_FOUNDATION_DESIGN_QUESTION_LEDGER.md
stages/stage12/STAGE12_CONTRACT_RUNTIME_MAPPING.md
stages/stage12/STAGE12_RUNTIME_TEST_MATRIX.md
stages/stage12/STAGE12_690108_PROVOCATION_RUNTIME_INTEGRATION.md
PROJECT_STATUS.md
```

## AF. Commit SHA

Recorded after merge.

## AG. Blocker Verdict

Subject to executable validation:

```text
BU-P02 Runtime Governance = RESOLVED
IMPLEMENTATION_BLOCKER-690108-001 = CLOSED
```

If CI contradicts the executable assumptions, the branch must be repaired before merge; the Research contract still does not reopen.

## AH. Current Gates

After successful validation:

```text
Stage11 Runtime = FROZEN
Stage12 Research = 7 / 7 FROZEN
Stage12 Shared Foundation Design = FROZEN
Stage12 Shared Foundation Implementation = COMPLETE

690089 Runtime = FROZEN
690101 Runtime = FROZEN
690107 Runtime = FROZEN

690108 Research = FROZEN
690108 Gameplay = NOT_INTEGRATED
690108 Runtime = NOT_FROZEN
IMPLEMENTATION_BLOCKER-690108-001 = CLOSED

Stage12 Runtime Frozen = 3 / 7
```

## AI. NEXT

```text
Resume 690108 PROVOCATION Runtime Integration
```

The resumed round must implement SINGLE, CHOOSE_N using RD-SF-005, FIXED_ALL, and the production SkillDefinition / SkillResolver producer mapping while preserving existing RNG ownership.
