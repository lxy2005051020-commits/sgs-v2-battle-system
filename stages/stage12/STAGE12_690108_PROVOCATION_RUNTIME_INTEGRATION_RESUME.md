# Stage12 690108 PROVOCATION Runtime Integration Resume

Date: 2026-09-28  
Command: `STAGE12_690108_PROVOCATION_RUNTIME_INTEGRATION_RESUME`  
Status: **GAMEPLAY IMPLEMENTED / PENDING INDEPENDENT RUNTIME AUDIT**

## A. Repository Lock

```text
Battle main at start:
9f9e8faba26fc01d264f9a4b29f4e7dcf2b18e9c

Research main at start:
e18ae56a4db5662b87458dfa8fdff25dcdd8053b
```

Both matched the commanded baselines. Research remained read-only.

## B. Resumed Integration Scope

This round implements only:

```text
690108 PROVOCATION / 挑拨
```

No gameplay implementation was added for 690222 INTIMIDATION, 690109 SABOTAGE or 690110 CAPTURE.

## C. RD-SF-005 Governance Lock

```text
RD-SF-005
= PROJECT_RUNTIME_DEFAULT
= NOT_EMPIRICALLY_FROZEN
```

For `NEW_QUERY + RANDOM + CHOOSE_N + admissible required Source`:

```text
reserve Source
-> remove Source from remaining population
-> remaining_slots = N - 1
-> TargetSystem fills remaining slots
```

No sample-then-replace path was added. The implementation and tests do not describe RD-SF-005 as battle-report confirmed or official hidden gameplay micro-order.

## D. PROVOCATION Runtime Architecture

Production path:

```text
SkillDefinition
-> SkillResolver
-> TargetOperation
-> SkillTargetPolicy
-> TargetSystem
-> TargetSelectionResult
```

`provocation_integration.py` contributes only a required-target constraint. It owns no target sampling, RandomSystem call, EventBus publication or NormalAttack target resolution.

## E. Production Producer Mapping

`SkillTargetMode` now exposes production producer intents for:

```text
SINGLE_RANDOM_ENEMY
SINGLE_DETERMINISTIC_ENEMY
CHOOSE_N_RANDOM_ENEMIES
CHOOSE_N_DETERMINISTIC_ENEMIES
FIXED_ALL_ENEMIES
```

`SkillResolver._target_contract()` canonicalizes those intents into the existing frozen:

```text
TargetRelation
TargetCardinality
TargetSelectorKind
TargetPurpose
TargetEligibilityContext
TargetOperation
```

CHOOSE_N carries an explicit `target_count`. Existing `SINGLE_RANDOM_ENEMY` remains the legacy-compatible ENEMY + SINGLE + RANDOM producer.

## F. TargetOperation Freshness

Only a fresh `TargetOperationProducer.new_query()` enters `SkillTargetPolicy`.

```text
INHERIT_RESOLVED
DERIVE_FROM_RESOLVED
LOCK_RESOLVED
```

continue from an immutable `TargetSelectionResult` and do not re-enter Provocation evaluation.

## G. Source Identity / Ownership

The implementation keeps distinct:

```text
Provocation holder = StateInstance.owner_id
Provocation Source = StateInstance.source_id
Source Provider = explicit ProviderDependency.provider_ref
Skill actor = TargetOperation.actor_id
candidate target = operation-local legal candidate
historical attribution = source_skill_id / source_skill_slot / EffectSourceRef
```

No attribution field is inferred into ProviderDependency.

## H. Source Eligibility

The Provocation adapter requires Source to remain inside the current operation-local legal candidate set after policy exclusions.

Illegal Source cases tested:

- Source absent from raw candidates;
- wrong relation;
- dead Source;
- explicit policy exclusion.

All produce no force, leave Provocation resident, and continue the original legal selector path.

## I. SINGLE Semantics

For an admissible Source:

```text
SINGLE
-> required Source occupies the only slot
-> final target = Source
-> target sample RNG = 0
```

Random and tested deterministic enemy selectors are both covered.

## J. CHOOSE_N Semantics

Under RD-SF-005:

```text
Source included exactly once
total cardinality = N
remaining population = legal candidates - Source
remaining slots = N - 1
```

RNG topology:

```text
N = 1 -> 0 sample
remaining population exactly fills remaining slots -> 0 sample
0 < remaining slots < remaining population -> exactly 1 sample(N - 1)
```

The required Source never re-enters the random population.

`BU-P09 insufficient candidates` remains an explicit unsupported boundary and is not normalized through the legacy `min(N, legal_count)` helper behavior.

## K. FIXED_ALL Semantics

```text
FIXED_ALL
-> preserve all legal eligible targets
-> legal Source already belongs to the set
-> illegal Source is not inserted
```

Provocation does not collapse FIXED_ALL into Source-only targeting.

## L. Relation Boundary

The production adapter applies only to:

```text
TargetOperationDomain.SKILL
+ TargetRelation.ENEMY
+ TargetPurpose.HOSTILE
```

Friendly and self relations are not redirected by ordinary Provocation.

## M. RNG / Replay Governance

```text
Provocation adapter RNG = 0
SkillTargetPolicy RNG = 0
TargetSystem -> BattleContext.random = sole target-selection RNG owner
```

Replay tests verify identical target result, sample-call topology, sample population and downstream RNG stream for the same seed/state/operation.

## N. NormalAttack / Taunt Separation

```text
TAUNT -> Stage9 NormalAttack TargetResolutionSystem
PROVOCATION -> SkillTargetPolicy
```

Tests prove Taunt does not change SkillTargetPolicy output and Provocation does not change NormalAttack target resolution.

## O. Confusion Priority

Frozen observable rule:

```text
when Confusion owns the target decision
-> Provocation does not additionally force Source
```

Production uses the existing `TargetEligibilityContext.restriction_keys` arbitration seam with:

```text
CONFUSION_CONTROLS_TARGET_DECISION
```

This is Skill-target metadata, not a Stage9 NormalAttack runtime import. If the concrete Skill operation does not designate Confusion as target-decision owner, Provocation is not suppressed merely because Confusion is resident.

## P. INSIGHT × PROVOCATION

Existing 690089 production integration already includes PROVOKE in the protected-control set.

Verified:

```text
effective INSIGHT + incoming PROVOCATION -> admission rejected

resident PROVOCATION + later effective INSIGHT
-> PROVOCATION remains resident
-> PROVOCATION becomes SUPPRESSED

Insight ends while Provocation still live
-> same Provocation resumes
-> only future NEW_QUERY is affected
```

Same-envelope expiry produces no transient resume.

## Q. EXHAUSTION × PROVOCATION

Existing 690101 admission remains upstream.

```text
EXHAUSTION denies ACTIVE
-> SkillResolver returns DISABLED
-> no TargetOperation
-> SkillTargetPolicy invocation count = 0
```

## R. FALSE_REPORT-source × PROVOCATION

When Provocation carries an explicit `ProviderDependency` on a tested Source Provider:

```text
FALSE_REPORT suppresses Source Provider
-> dependent Provocation becomes ineffective

Provider restored
-> still-resident Provocation resumes
-> future NEW_QUERY may force Source again
```

FALSE_REPORT on the Provocation holder does not automatically invalidate an external Source Provider.

## S. ProviderDependency / Attribution

Executable negative discriminators verify:

```text
source_skill_id only -> no dependency
source_skill_slot only -> no dependency
source_skill_id + source_skill_slot only -> no dependency
```

Only explicit `ProviderDependency` propagates Source Provider validity.

## T. Target Result Stability

A resolved `TargetSelectionResult` is not rewritten after:

- Source death;
- Provocation suppression/resume;
- Insight changes;
- Provider validity changes;
- later independent queries.

Continuation modes preserve the original operation identity and target tuple.

## U. Conflict / Reapplication

`BU-P06` remains unsupported.

Supported production application rejects a second resident Provocation attempt through an explicit `UNSUPPORTED_BOUNDARY` conflict decision rather than inventing latest-wins, strongest-wins, same-source refresh or multi-source competition.

## V. Removal / Source Death / Lifetime

Verified:

```text
Source death
-> Provocation remains resident
-> dead Source is inadmissible to later queries
-> lifetime continues

suppressed Provocation expires
-> removed normally
-> no later resume
```

Holder cleanup remains the generic unit-lifecycle responsibility.

## W. Event Semantics

```text
Provocation SkillTargetPolicy query = 0 Event
Provocation adapter = 0 direct EventBus publication
```

No `PROVOCATION_FORCED_TARGET` event was introduced. Canonical state suppression/resume events remain owned by the Shared Foundation transition path.

## X. BattleSystems Wiring

`BattleSystems` registers `register_provocation_integration()` into the existing:

- `StateConflictPolicy`;
- `StateEffectivenessPolicy`;
- `SkillTargetPolicy`.

No second state-effectiveness policy, target policy, dependency graph or target system was created.

## Y. Tests Added

Gameplay integration suite:

```text
tests/test_stage12_690108_provocation.py
```

Full-suite delta:

```text
baseline = 1314 passed
integration checkpoint = 1359 passed
delta = +45 test nodes
required minimum = >= 25
gate = PASS
```

Existing RD-SF-005 governance suite remains separate:

```text
tests/test_stage12_690108_bu_p02_runtime_governance.py
```

## Z. Stage9 Regression

```text
PASS via CI 36333059532
```

NormalAttack Confusion/Taunt/Guard and target RNG regressions remain green.

## AA. Stage10 Regression

```text
PASS via CI 36333059532
```

## AB. Stage11 Regression

```text
PASS via CI 36333059532
Stage11 Reopen Required = NO
```

## AC. 690089 Regression

```text
PASS via CI 36333059532
```

Insight admission, resident suppression/resume and same-envelope behavior remain green.

## AD. 690101 Regression

```text
PASS via CI 36333059532
```

EXHAUSTION denied-ACTIVE short-circuit remains upstream of target policy.

## AE. 690107 Regression

```text
PASS via CI 36333059532
```

Provider suppression, ownership and attribution/dependency boundaries remain green.

## AF. RD-SF-005 Regression

```text
PASS via CI 36333059532
RD-SF-005 = PROJECT_RUNTIME_DEFAULT
NOT_EMPIRICALLY_FROZEN
```

No provenance laundering occurred.

## AG. Shared Foundation Regression

```text
PASS via CI 36333059532
owner graph unchanged
```

The existing TargetOperation / TargetSelectionResult / SkillTargetPolicy / ProviderDependency / DependencyEvaluationSupport owners are reused.

## AH. Static Architecture Audit

Verified by source and executable guards:

```text
no ActionSystem Provocation blocker
no NormalAttack Provocation branch
no direct TargetSystem mutation from adapter
no direct RNG in adapter
no direct EventBus publish from adapter
no second SkillTargetPolicy
no attribution -> ProviderDependency inference
no sample-then-replace path
no BU-P09 accidental default
no gameplay implementation of 690222 / 690109 / 690110
```

## AI. Gameplay Changes

Gameplay added in this round:

```text
690108 PROVOCATION = YES
690222 INTIMIDATION = 0
690109 SABOTAGE = 0
690110 CAPTURE = 0
```

## AJ. pytest / demo / CI

Validated code/test checkpoint:

```text
d420e8130dff1b3b9cc2545f0a832eccf58abd75
CI = 36333059532 / success
pytest = 1359 passed
demo = PASS
```

Final PR validation:

```text
PR #18
head = 4bf4e28a1599d80e448086efb5b7bfb46eef7206
CI = 36333316715 / success
pytest = 1359 passed
demo = PASS
audit snapshot upload = PASS
```

## AK. Files Created / Updated

Created:

```text
sgs_v2/battle_core/provocation_integration.py
tests/test_stage12_690108_provocation.py
stages/stage12/STAGE12_690108_PROVOCATION_RUNTIME_INTEGRATION_RESUME.md
```

Production updated:

```text
sgs_v2/battle_core/skill_definition.py
sgs_v2/battle_core/skill_resolver.py
sgs_v2/battle_core/battle_systems.py
```

Regression/schema test updated:

```text
tests/test_skill_definition.py
```

Governance/status documents are synchronized in the same PR.

Research repository changes:

```text
NONE
```

## AL. Commit SHA

Validated code/test checkpoint:

```text
d420e8130dff1b3b9cc2545f0a832eccf58abd75
```

Final validated PR head:

```text
4bf4e28a1599d80e448086efb5b7bfb46eef7206
```

Merge commit:

```text
ceda9d6418f5b4ab49e7bb7cf54f7b15cebc9a17
```

## AM. Implementation Blockers

```text
NONE
```

Preserved unsupported boundaries are not implementation blockers:

```text
BU-P06 = UNSUPPORTED_BOUNDARY
BU-P09 = UNSUPPORTED_BOUNDARY
```

## AN. Current Gates

After this integration is merged:

```text
Stage11 Runtime = FROZEN
Stage11 Reopen Required = NO

Stage12 Research = 7 / 7 FROZEN
Stage12 Shared Foundation Design = FROZEN
Stage12 Shared Foundation Implementation = COMPLETE

690089 INSIGHT Runtime = FROZEN
690101 EXHAUSTION Runtime = FROZEN
690107 FALSE_REPORT Runtime = FROZEN

690108 PROVOCATION Research = FROZEN
690108 PROVOCATION Gameplay = IMPLEMENTED_PENDING_RUNTIME_AUDIT
690108 PROVOCATION Runtime = NOT YET FROZEN

Stage12 Gameplay Implementation = 4 / 7
Stage12 Runtime Frozen = 3 / 7

Stage13 / Stage14 / Stage15 Active = NO
```

This integration does not increment Runtime Frozen.

## AO. NEXT

```text
690108 PROVOCATION Independent Runtime Freeze Audit
```

Do not start 690222 Runtime Integration until the independent 690108 Runtime Freeze Audit has completed.
