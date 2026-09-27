# Stage12 · 690101 EXHAUSTION Preparation Integration Dependency Resolution

> Date: **2026-09-27**  
> Command: **STAGE12_690101_PREPARATION_INTEGRATION_DEPENDENCY_RESOLUTION**  
> Research Contract: **690101 v0.2-frozen**  
> Battle start baseline: **b1937c553a3d35ab0ee5afe8b3c8652c8e56cf36**  
> Research baseline: **e18ae56a4db5662b87458dfa8fdff25dcdd8053b**  
> Dependency verdict: **BLOCKERS CLOSED / INDEPENDENT RUNTIME AUDIT REQUIRED**  
> Stage15 Active: **NO**

## A. Repository Lock

Battle repository:

```text
lxy2005051020-commits/sgs-v2-battle-system
start main = b1937c553a3d35ab0ee5afe8b3c8652c8e56cf36
```

Research repository:

```text
lxy2005051020-commits/sgs-state-mechanics-research
main = e18ae56a4db5662b87458dfa8fdff25dcdd8053b
mode = READ ONLY
```

Both heads were re-read before implementation. Research was not modified.

## B. Dependency Resolution Scope

This round closes only:

```text
BLOCKER-690101-PREP-001
Concrete Preparation Owner required

BLOCKER-690101-PREP-002
First-application EXHAUSTION needs lawful PREPARING interruption command seam
```

No Stage13, Stage14 or Stage15 gameplay runtime was activated.

## C. Existing Preparation Architecture Audit

Existing production already had:

- typed `PreparationInterruptionPort`;
- `HOLDER_ACTIVE` and `PROVIDER` scopes;
- typed `INTERRUPTED / NOT_PREPARING / PROVIDER_NOT_MATCHED / UNSUPPORTED` results;
- `PreparationInterruptionTransitionAdapter` for resident effectiveness/provider transitions.

The production composition root still defaulted to `NoopPreparationInterruptionPort`, and no owner existed for real PREPARING work.

## D. Concrete Preparation Owner

Added:

```text
sgs_v2/battle_core/preparation_state.py
PreparationStateOwner
```

Its authority is deliberately narrow:

```text
record already-admitted PREPARING identity
query PREPARING identity
interrupt PREPARING identity
clear PREPARING identity
```

It does not perform Skill admission, Provider validity decisions, target selection, RNG, preparation progress, round advancement or prepared-skill execution.

## E. Preparation Record Identity

Canonical minimal record:

```text
holder_id
provider_ref
skill_id
admitted_operation_id
status = PREPARING
```

The record is immutable. Provider identity must match holder and skill identity.

## F. PreparationInterruptionPort Production Binding

`BattleSystems` now creates one `PreparationStateOwner`. When no explicit test/non-production port is injected:

```text
BattleSystems.preparation_interruption_port
is
BattleSystems.preparation_state_owner
```

Production no longer uses `NoopPreparationInterruptionPort` for 690101.

## G. HOLDER_ACTIVE Interruption

A `HOLDER_ACTIVE` request removes every currently PREPARING record owned by that holder in one command and returns the interrupted Provider refs.

A repeated command cannot interrupt the same record twice.

## H. PROVIDER Interruption

A `PROVIDER` request matches the exact `SkillProviderRef`.

Other Providers owned by the same holder remain PREPARING. A holder with preparation but no exact Provider match returns `PROVIDER_NOT_MATCHED`.

## I. First Effective CREATE Seam

Added a generic post-commit fact:

```text
CommittedEffectiveStateActivation
```

and registration seam on `StateApplicationCoordinator`.

Ordering is:

```text
candidate/admission/conflict
-> transaction preflight
-> physical StateLifecycle commit
-> dependency topology commit
-> existing effectiveness transition settlement
-> canonical effectiveness evaluation of new CREATE
-> if EFFECTIVE: CommittedEffectiveStateActivation
-> mechanism adapter
-> domain command
```

This does not invent `ABSENT` as a `StateEffectivenessStatus`.

## J. SUPPRESSED -> EFFECTIVE Resume Seam

Resident EXHAUSTION resume continues to use the existing lawful path:

```text
SUPPRESSED -> EFFECTIVE
-> EffectivenessTransitionCoordinator
-> PreparationInterruptionTransitionAdapter
-> PreparationInterruptionPort
```

First CREATE and later resume therefore converge on the same interruption capability without pretending they are the same transition type.

## K. Exactly-once Interruption

An effective CREATE produces exactly one activation command path. It is not also represented as an effectiveness transition.

A resident resume produces the existing transition command path only.

The Preparation owner removes matched records before returning, so repeating the same interruption command cannot repeat the consequence.

## L. Initial Suppressed Application

A committed CREATE whose canonical initial effectiveness is `SUPPRESSED` does not publish `CommittedEffectiveStateActivation` and does not interrupt preparation.

## M. Failed Application Atomicity

Activation ports are invoked only after a successful physical commit and dependency commit.

Admission rejection, conflict rejection/unsupported boundaries and other pre-commit failures cannot reach the committed-effective activation seam.

Post-commit port exceptions follow the frozen transaction governance: they are implementation/invariant failures and do not roll back the already committed Registry state.

## N. INSIGHT × EXHAUSTION Preparation Interaction

Covered:

```text
effective INSIGHT + incoming EXHAUSTION
-> EXHAUSTION rejected
-> no activation seam
-> preparation continues

resident EXHAUSTION suppressed by INSIGHT
+ holder begins PREPARING
+ INSIGHT removed
-> EXHAUSTION resumes EFFECTIVE
-> preparation interrupted synchronously
```

## O. Same-envelope Expiry

When INSIGHT and its suppressed EXHAUSTION are both due in the same removal envelope, both are physically removed before transition settlement. No EXHAUSTION resume and no ghost interruption occurs.

## P. Stage15 Boundary Audit

Not introduced:

```text
PreparationScheduler
PreparationTurnMachine
PreparationProgressEngine
PreparationQueue
PreparationRoundResolver
ActiveSkillPreparationRuntime
Stage15Runtime
```

The new owner has no preparation timer/progress/completion logic.

```text
Stage15 Active = NO
```

## Q. Static Architecture Audit

Executable/static guards verify:

- production BattleSystems does not construct the Noop port;
- Preparation owner imports no `random` and does not use `context.random`;
- owner imports neither `SkillPermissionPolicy` nor `ProviderValidityPolicy`;
- owner does not select targets or advance rounds;
- no Stage15 scheduler class is introduced;
- `StateApplicationCoordinator` activation seam is generic and contains no EXHAUSTION/SILENCE branch.

## R. 690101 Regression

690101 permission, skill-type boundary, natural action, normal attack, RD-SF-004, Provider precedence, target short-circuit, INSIGHT interaction, conflict boundary and lifetime coverage remain in the full suite.

## S. 690089 Regression

690089 remains Runtime FROZEN. INSIGHT admission protection, resident suppression, presence/effectiveness distinction and same-envelope behavior remain covered by the full suite.

## T. Stage9 Regression

Covered by the repository-wide pytest run.

## U. Stage10 Regression

Covered by the repository-wide pytest run.

## V. Stage11 Regression

Covered by the repository-wide pytest run.

```text
Stage11 Reopen Required = NO
```

## W. Shared Foundation Regression

Shared Foundation Round 1-4/completion/INSIGHT tests are included in the repository-wide suite. The former Round 3 expectation that production must use a Noop preparation port was deliberately superseded by this blocker-resolution round.

## X. Tests Added / Updated

Added:

```text
tests/test_stage12_690101_preparation_integration.py
```

Coverage includes:

- admitted preparation identity;
- holder interruption and repeat idempotence;
- exact Provider interruption;
- Provider mismatch;
- zero-event query / zero-RNG architecture;
- production non-Noop binding;
- production first effective EXHAUSTION CREATE interruption;
- exactly-once first CREATE;
- initially suppressed CREATE;
- INSIGHT-rejected candidate;
- resident resume;
- multiple suppression causes;
- same-envelope expiry;
- Stage15 leakage/static architecture guards.

Existing 690101 and Shared Foundation tests were updated where their old expectations encoded the now-closed Noop/first-CREATE blocker.

## Y. Gameplay Changes

The only new gameplay capability is:

```text
real PREPARING state can now be represented and interrupted

effective EXHAUSTION first CREATE
-> immediate HOLDER_ACTIVE interruption

resident EXHAUSTION SUPPRESSED -> EFFECTIVE
-> immediate HOLDER_ACTIVE interruption
```

No other Stage12 gameplay was added.

## Z. pytest / demo / CI

Pre-documentation implementation validation:

```text
implementation head = d1fd6f3ecbe80278cb87ff350f1a6002ab42c595
push CI             = 36314620250 / success
pytest              = 1228 passed
demo                = PASS
```

A final fresh CI is required on the documentation-complete head and again after merge to `main`.

## AA. Files Created / Updated

Created:

```text
sgs_v2/battle_core/preparation_state.py
tests/test_stage12_690101_preparation_integration.py
stages/stage12/STAGE12_690101_PREPARATION_INTEGRATION_DEPENDENCY.md
```

Updated:

```text
sgs_v2/battle_core/state_application.py
sgs_v2/battle_core/preparation_interruption.py
sgs_v2/battle_core/exhaustion_integration.py
sgs_v2/battle_core/battle_systems.py
sgs_v2/battle_core/__init__.py
tests/test_stage12_690101_exhaustion.py
tests/test_stage12_shared_foundation_round3.py
stages/stage12/STAGE12_690101_EXHAUSTION_RUNTIME_INTEGRATION.md
stages/stage12/README.md
PROJECT_STATUS.md
CANONICAL_STATE_PLANNING_MATRIX.md
```

## AB. Commit SHA

Dependency-resolution work is developed on:

```text
stage12-690101-preparation-dependency
PR #15
```

Final merged `main` SHA is recorded by the final execution report after the merge gate.

## AC. Blocker Closure Verdict

```text
BLOCKER-690101-PREP-001 = CLOSED
BLOCKER-690101-PREP-002 = CLOSED
```

Closure is conditional only on the normal final regression/merge CI gate, not on a remaining architecture dependency.

## AD. Current Gates

After dependency resolution and before independent Runtime Freeze Audit:

```text
Stage11 Runtime = FROZEN
Stage11 Reopen Required = NO

Stage12 Research = 7 / 7 FROZEN
Stage12 Shared Foundation Design = FROZEN
Stage12 Shared Foundation Implementation = COMPLETE

690089 Runtime = FROZEN

690101 Gameplay = IMPLEMENTED_PENDING_RUNTIME_AUDIT
690101 Runtime = NOT YET FROZEN
Stage12 Runtime Frozen = 1 / 7

690107 Runtime Integration = NOT STARTED

Stage13 Active = NO
Stage14 Active = NO
Stage15 Active = NO
```

## AE. NEXT

The only next governance action is:

```text
690101 EXHAUSTION Independent Runtime Freeze Audit
```

Only a PASS there may change:

```text
690101 Runtime = FROZEN
Stage12 Runtime Frozen = 2 / 7
```

and only then may 690107 Runtime Integration begin.
