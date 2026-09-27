# Stage12 690108 PROVOCATION Runtime Integration

Date: 2026-09-27  
Round: `STAGE12_690108_PROVOCATION_RUNTIME_INTEGRATION`  
Status: **IMPLEMENTATION BLOCKED / NO PRODUCTION GAMEPLAY MUTATION**  
Battle baseline: `02aa9c5eed74aa35c5af68d9029a73ff069b3d68`  
Research baseline: `e18ae56a4db5662b87458dfa8fdff25dcdd8053b`

## A. Repository Lock

Both real `main` heads were re-read before integration work.

```text
Battle main   = 02aa9c5eed74aa35c5af68d9029a73ff069b3d68
Research main = e18ae56a4db5662b87458dfa8fdff25dcdd8053b
```

They match the command-agent baselines. Research remains frozen and is not reopened by this integration attempt.

## B. Integration Scope

Authorized state:

```text
690108 PROVOCATION / 挑拨
```

Not authorized for gameplay implementation in this round:

```text
690222 INTIMIDATION
690109 SABOTAGE
690110 CAPTURE
```

This round stopped before registering a 690108 production gameplay adapter because a frozen Runtime-governance prerequisite is unresolved.

## C. PROVOCATION Runtime Architecture

Frozen owner remains:

```text
SkillTargetPolicy
```

Existing production seam is suitable:

```text
TargetOperation
-> raw candidates
-> SkillTargetPolicy
-> TargetSystem / selector
```

No second SkillTargetPolicy, ProvocationRuntime facade, TargetResolutionSystem hook, global TargetSystem candidate mutation, direct RNG owner or EventBus authority is needed.

## D. TargetOperation Freshness

The current Shared Foundation already enforces:

```text
NEW_QUERY -> allocate TargetOperationId -> SkillTargetPolicy
INHERIT_RESOLVED -> no new TargetOperation
DERIVE_FROM_RESOLVED -> no new TargetOperation
LOCK_RESOLVED -> no new TargetOperation
```

No freshness redesign is required for 690108.

## E. Source Identity / Ownership

StateInstance already preserves:

```text
owner_id
source_id
source_skill_id
source_skill_slot
current_generation_id
lifetime
```

Explicit ProviderDependency is carried independently by the Shared Foundation dependency graph. Attribution fields are not inferred into ProviderDependency.

## F. Source Eligibility

The existing SkillTargetPolicy receives an operation-local raw candidate set and only retains required targets that remain in the eligible set. This is a valid seam for the frozen rule:

```text
Source not admissible
-> do not force Source
-> do not remove/consume Provocation
```

No global candidate mutation is required.

## G. SINGLE Semantics

The current selector architecture can represent the frozen SINGLE rule without new hidden gameplay law:

```text
admissible Source
-> required_target_ids = (Source,)
-> SINGLE cardinality = 1
-> selector remaining slots = 0
-> target RNG = 0
```

This path is implementation-ready after the global 690108 gate is unblocked.

## H. CHOOSE_N Semantics

### IMPLEMENTATION_BLOCKER-690108-001

Frozen observable rule:

```text
CHOOSE_N(N)
+ admissible Source
-> Source included exactly once
-> total cardinality N preserved
```

Frozen Research boundary:

```text
BU-P02
exact internal slot / RNG micro-order
= CLOSED_WITH_BOUNDED_UNKNOWN
```

The two possible implementation topologies consume different replay streams:

```text
reserve Source then sample N-1
vs
sample N then replace one
```

This blocker is now resolved by **RD-SF-005** in the canonical Runtime Default Ledger.

Frozen project Runtime rule:

```text
PROJECT_RUNTIME_DEFAULT
NOT_EMPIRICALLY_FROZEN

NEW_QUERY + RANDOM + CHOOSE_N
+ admissible required Provocation Source
-> reserve required Source first
-> Source consumes one cardinality slot
-> remove Source from random population
-> TargetSystem fills N-1 remaining slots
-> no post-selector replacement
```

The decision is not derived from code accident. It is adopted because it preserves the frozen Shared Foundation owner topology, introduces no new RNG owner, requires no replacement-victim micro-policy, and gives deterministic replay a single explicit call topology.

Random ownership remains:

```text
Provocation adapter RNG = 0
SkillTargetPolicy RNG = 0
TargetSystem -> BattleContext.random = sole target-sampling RNG path
```

Supported no-draw cases:

```text
N = 1 and Source fills the only slot
-> remaining_slots = 0
-> 0 RandomSystem.sample calls

remaining candidate count == remaining_slots
-> deterministic all-candidate fill
-> 0 RandomSystem.sample calls
```

When `0 < remaining_slots < len(remaining)`, TargetSystem performs one `RandomSystem.sample(remaining, remaining_slots)` call.

BU-P09 insufficient candidates is not answered by RD-SF-005; the legacy helper truncation remains outside the supported 690108 contract.

Research does **not** reopen. Shared Foundation ownership does **not** reopen. BU-P02 remains empirically bounded; only the simulator implementation choice is frozen.

## I. FIXED_ALL Semantics

The Shared Foundation can represent the frozen FIXED_ALL rule without changing the target set:

```text
FIXED_ALL
-> every eligible candidate
-> Provocation adds no target-set change
```

No hidden RNG rule is required for the target-set semantics.

## J. Relation Boundary

The frozen contract limits ordinary Provocation redirection to eligible enemy-directed target-producing operations.

SELF and friendly/support operations remain negative boundaries. No generic forced-target abstraction is authorized.

## K. RNG Governance

Verified ownership remains:

```text
Provocation adapter    = 0 RNG
SkillTargetPolicy      = 0 RNG
TargetSystem / selector = RNG owner
```

Forced legal SINGLE is compatible with zero target RNG.

CHOOSE_N is blocked specifically because the selector call topology is not yet frozen.

## L. Normal Attack / Taunt Separation

No 690108 production code was added to:

```text
TargetResolutionSystem
NormalAttackSystem
ActionSystem
```

Stage9 Taunt remains Normal Attack arbitration authority.

## M. Confusion Priority

The frozen rule remains:

```text
when Confusion owns the target decision
-> Provocation does not additionally force Source
```

No Stage9 target architecture was modified in this blocked round.

## N. INSIGHT x PROVOCATION

Existing 690089 production integration already includes PROVOKE in the ordinary Insight-protected set and binds protected resident states to Insight effectiveness dependencies.

No new 690089 gameplay law is required.

## O. EXHAUSTION x PROVOCATION

Existing 690101 Skill admission short-circuit remains upstream of activation/TargetOperation creation.

No 690108 target-policy evaluation occurs for a denied ACTIVE admission.

## P. FALSE_REPORT-source x PROVOCATION

Existing Shared Foundation + 690107 production support already provides:

```text
explicit ProviderDependency
-> ProviderValidity
-> dependent state effectiveness
```

and preserves:

```text
EffectSourceRef / source_skill_id / source_skill_slot
!= automatic ProviderDependency
```

A future 690108 application must attach only contract-authorized explicit dependencies.

## Q. ProviderDependency Semantics

No dependency inference change is required. Provider restore can resume the same still-resident state through canonical effectiveness recomputation; it does not reapply or refresh the state.

## R. Target Result Stability / No Replay

Current TargetSelectionResult and continuation provenance already provide the required architectural separation. No retroactive rewrite path was added.

## S. Conflict / Reapplication

Research BU-P06 remains unsupported for simultaneous multi-source / reapplication semantics.

This round does not invent latest-wins, strongest-wins, random-source or multi-required-source behavior.

## T. Removal / Source Death / Lifetime

Frozen source-death rule remains:

```text
Source dies
-> Provocation remains resident
-> dead Source is inadmissible
-> later query does not force it
-> lifetime continues normally
```

No universal source-death cleanup is authorized.

## U. Event Semantics

No generic PROVOCATION_FORCED_TARGET public event is introduced.

Policy evaluation remains a zero-event query. State suppression/resume facts remain owned by the canonical effectiveness transition path.

## V. BattleSystems Wiring

No 690108 adapter is registered while IMPLEMENTATION_BLOCKER-690108-001 remains open.

The existing one-owner graph remains unchanged.

## W. Tests Added

Added generic governance suite:

```text
tests/test_stage12_690108_bu_p02_runtime_governance.py
```

It verifies required-target cardinality, exactly-once identity, reserve-first population/slot topology, TargetSystem RNG ownership, policy zero-RNG, draw/no-draw behavior, deterministic replay, downstream RNG-stream stability, continuation no-reselection, and absence of post-selector replacement.

No 690108 gameplay adapter is registered by this governance round.

## X. Stage9 Regression

Expected unchanged. No Stage9 production code was modified.

## Y. Stage10 Regression

Expected unchanged. No Stage10 production code was modified.

## Z. Stage11 Regression

Expected unchanged.

```text
Stage11 Reopen Required = NO
```

## AA. 690089 Regression

Expected unchanged. Existing Insight protection/suppression ownership is reused.

## AB. 690101 Regression

Expected unchanged. Existing EXHAUSTION admission short-circuit is reused.

## AC. 690107 Regression

Expected unchanged. Existing explicit ProviderDependency propagation is reused.

## AD. Shared Foundation Regression

No Shared Foundation production owner or policy implementation is changed by this blocker sync.

## AE. Static Architecture Audit

This integration attempt preserves:

```text
no ActionSystem Provocation branch
no NormalAttack TargetResolution Provocation branch
no direct TargetSystem mutation
no direct Provocation RNG
no direct Provocation EventBus publish
no second SkillTargetPolicy
no attribution -> ProviderDependency inference
no 690222 / 690109 / 690110 gameplay implementation
```

## AF. Gameplay Changes

```text
NONE
```

This is deliberate. Partially activating SINGLE while leaving mandatory CHOOSE_N semantics unresolved would create a misleading IMPLEMENTED state.

## AG. pytest / demo / CI

This document is committed on an integration-blocker branch and must pass the repository's normal GitHub Actions workflow before merge.

Expected unchanged baseline:

```text
pytest = 1299 passed
demo = PASS
```

Final CI run is recorded after GitHub validation.

## AH. Files Created / Updated

Created:

```text
stages/stage12/STAGE12_690108_PROVOCATION_RUNTIME_INTEGRATION.md
```

Updated:

```text
PROJECT_STATUS.md
```

Research repository files changed:

```text
NONE
```

## AI. Commit SHA

Recorded after merge.

## AJ. Implementation Blockers

```text
IMPLEMENTATION_BLOCKER-690108-001 = CLOSED

Resolution:
RD-SF-005

Classification:
PROJECT_RUNTIME_DEFAULT
NOT_EMPIRICALLY_FROZEN

Selection topology:
reserve-first

Research contract:
FROZEN / NOT REOPENED

Shared Foundation owner architecture:
FROZEN / NOT REOPENED
```

Secondary implementation gap, not a research blocker:

```text
SkillDefinition / SkillResolver production target modes currently expose only SINGLE_RANDOM_ENEMY.
CHOOSE_N and FIXED_ALL production producer mappings must be implemented after BU-P02 is resolved,
using the already-frozen TargetOperation model rather than redesigning the Shared Foundation.
```

## AK. Current Gates

```text
Stage11 Runtime = FROZEN
Stage11 Reopen Required = NO

Stage12 Research = 7 / 7 FROZEN
Stage12 Shared Foundation Design = FROZEN
Stage12 Shared Foundation Implementation = COMPLETE

690089 INSIGHT Runtime = FROZEN
690101 EXHAUSTION Runtime = FROZEN
690107 FALSE_REPORT Runtime = FROZEN

690108 PROVOCATION Gameplay = NOT_INTEGRATED
690108 PROVOCATION Runtime = NOT_FROZEN
690108 Integration = READY_TO_RESUME
IMPLEMENTATION_BLOCKER-690108-001 = CLOSED

Stage12 Runtime Frozen = 3 / 7

Stage13 Active = NO
Stage14 Active = NO
Stage15 Active = NO
```

## AL. NEXT

```text
Resume STAGE12_690108_PROVOCATION_RUNTIME_INTEGRATION using RD-SF-005 for CHOOSE_N.
Implement SINGLE / CHOOSE_N / FIXED_ALL producer mapping and the production Provocation target-policy adapter without changing RNG ownership.
Do not start 690108 Independent Runtime Freeze Audit before integration exit gate passes.
Do not start 690222 Runtime Integration while 690108 remains the active integration owner.
```


## AM. BU-P02 Governance Resolution Amendment

Authority:

```text
stages/stage12/STAGE12_RUNTIME_DEFAULT_LEDGER.md
RD-SF-005
```

Current status:

```text
BU-P02 Runtime Governance = RESOLVED
IMPLEMENTATION_BLOCKER-690108-001 = CLOSED

690108 Research = FROZEN
690108 Gameplay = NOT_INTEGRATED
690108 Runtime = NOT_FROZEN
Stage12 Runtime Frozen = 3 / 7
```

The blocker closure authorizes resuming 690108 integration. It does not itself implement Provocation gameplay and does not count as a fourth frozen Stage12 Runtime.


## AN. 2026-09-28 Resume Completion

The post-BU-P02 integration resume is complete.

```text
690108 Gameplay = IMPLEMENTED_PENDING_RUNTIME_AUDIT
690108 Runtime = NOT_YET_FROZEN
Stage12 Runtime Frozen = 3 / 7
pytest = 1359 passed
demo = PASS
CI = 36333059532 / success
NEXT = 690108 PROVOCATION Independent Runtime Freeze Audit
```

Canonical completion record:

`STAGE12_690108_PROVOCATION_RUNTIME_INTEGRATION_RESUME.md`
