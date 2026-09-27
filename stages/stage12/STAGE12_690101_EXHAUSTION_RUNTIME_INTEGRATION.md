# Stage12 · 690101 EXHAUSTION Runtime Integration

> Date: **2026-09-27**  
> Research Contract: **v0.2-frozen**  
> Dependency-resolution baseline: **b1937c553a3d35ab0ee5afe8b3c8652c8e56cf36**  
> Research baseline: **e18ae56a4db5662b87458dfa8fdff25dcdd8053b**  
> Integration status: **IMPLEMENTED_PENDING_RUNTIME_AUDIT / NOT YET FROZEN**  
> Stage12 Runtime Frozen: **1 / 7**

## A. Repository Lock

Battle repository:

```text
lxy2005051020-commits/sgs-v2-battle-system
dependency-resolution baseline main = b1937c553a3d35ab0ee5afe8b3c8652c8e56cf36
```

Research repository:

```text
lxy2005051020-commits/sgs-state-mechanics-research
baseline main = e18ae56a4db5662b87458dfa8fdff25dcdd8053b
```

Research authority remains read-only and unchanged.

## B. Integration Scope

Implemented only:

```text
690101 EXHAUSTION / 计穷
```

Not implemented:

```text
690107 FALSE_REPORT
690108 PROVOCATION
690109 SABOTAGE
690110 CAPTURE
690222 INTIMIDATION
```

## C. EXHAUSTION Runtime Adapter

Canonical owner:

```text
SkillPermissionPolicy
```

Rule:

```text
effective EXHAUSTION
+ NEW_ADMISSION
+ SkillType.ACTIVE
-> DENY_STATE_PERMISSION
```

The adapter queries `StateEffectivenessPolicy.has_effective(...)`; resident-but-suppressed EXHAUSTION therefore does not deny Active admission.

## D. Skill Type Boundary

Denied:

```text
ACTIVE
ACTIVE + PreparationMode.NONE
ACTIVE + PreparationMode.REQUIRED
legacy SkillDefinition -> ACTIVE + NONE
```

Not denied by ordinary EXHAUSTION:

```text
ASSAULT
PASSIVE
COMMAND
TROOP
FORMATION
```

No expansion beyond the frozen ACTIVE boundary was introduced.

## E. ACTIVE Permission Denial

The rule is holder-level and operation-level.

It does not mutate:

```text
SkillRuntime.enabled
SkillDefinition
SkillRuntimeRegistry
```

`CONTINUATION` remains `CONTINUATION_NOT_REEVALUATED`.

## F. Non-ACTIVE Behavior

The EXHAUSTION adapter returns no decision for non-ACTIVE skill types, so the canonical permission policy remains authoritative for any other blockers.

## G. Natural Action / Normal Attack Boundary

No EXHAUSTION code is registered in `ActionSystem`.

Executable coverage verifies that effective EXHAUSTION does not by itself prevent the natural action from reaching a legal normal attack.

## H. RD-SF-004 RNG Governance

Runtime ordering remains:

```text
ProviderValidityPolicy
-> SkillPermissionPolicy
-> SkillOperationAdmissionDecision
-> activation RNG
-> TargetOperation
-> target RNG
```

Therefore a NEW ACTIVE denied by effective EXHAUSTION consumes:

```text
0 activation RNG
0 TargetOperation allocation
0 target-selection RNG
```

Classification remains:

```text
PROJECT_RUNTIME_DEFAULT
NOT_EMPIRICALLY_FROZEN
RD-SF-004
```

No research claim is made about hidden server RNG ordering.

## I. ProviderValidity / Permission Ordering

`SkillOperationAdmissionCoordinator` remains unchanged.

A missing, identity-mismatched, baseline-disabled or suppressed Provider still returns `DENY_PROVIDER_INVALID` before holder permission is evaluated.

## J. Target-layer Short Circuit

A denied ACTIVE operation returns before target operation construction. No Provocation/Capture target logic is reached.

## K. Preparation Interruption

The former integration dependency is now resolved by the dedicated dependency-resolution round.

Production now provides:

```text
PreparationStateOwner = canonical minimal PREPARING truth owner
BattleSystems default PreparationInterruptionPort = PreparationStateOwner
NoopPreparationInterruptionPort = non-production/test compatibility only
```

First effective CREATE uses a separate generic post-commit seam:

```text
physical CREATE commit
-> dependency commit
-> canonical effectiveness evaluation
-> CommittedEffectiveStateActivation
-> PreparationInterruptionActivationAdapter
-> HOLDER_ACTIVE interruption
```

Resident resume remains:

```text
SUPPRESSED -> EFFECTIVE
-> EffectivenessTransitionCoordinator
-> PreparationInterruptionTransitionAdapter
-> HOLDER_ACTIVE interruption
```

The two paths converge on the same typed `PreparationInterruptionPort` without inventing an `ABSENT` effectiveness status. Initial SUPPRESSED CREATE, rejected application, same-envelope expiry and non-final suppression removal do not interrupt preparation.

Detailed authority:
`STAGE12_690101_PREPARATION_INTEGRATION_DEPENDENCY.md`.

Verdict:

```text
BLOCKER-690101-PREP-001 = CLOSED
BLOCKER-690101-PREP-002 = CLOSED
Stage15 Active = NO
```

## L. INSIGHT × EXHAUSTION

Covered behavior:

```text
effective INSIGHT + incoming EXHAUSTION
-> admission rejected

resident EXHAUSTION + later INSIGHT
-> EXHAUSTION remains resident
-> becomes SUPPRESSED
-> ACTIVE permission restored

INSIGHT removed while EXHAUSTION remains resident
-> EXHAUSTION SUPPRESSED -> EFFECTIVE
-> ACTIVE denial returns
-> interruption bridge is invoked

EXHAUSTION expires while suppressed
-> no later resume

same-envelope INSIGHT + EXHAUSTION expiry
-> no ghost denial
```

## M. State Conflict / Reapplication

The frozen 690101 research contract does not establish same-state refresh/replace semantics.

Current Shared Foundation behavior is preserved:

```text
resident EXHAUSTION + incoming EXHAUSTION
-> UNSUPPORTED_BOUNDARY
```

No Insight-specific reapplication rule was copied onto EXHAUSTION.

## N. Removal / Source Death / Lifetime

No new 690101 removal rule was invented.

Infrastructure natural expiry remains available through Shared Foundation. Ordinary/specialized cleanse boundaries remain unsupported unless later authority freezes them.

Suppression does not pause the resident state's lifetime.

## O. Event Semantics

Current `EventType` does not contain `SKILL_OPERATION_BLOCKED` or `PREPARATION_INTERRUPTED`.

No query-time EventBus publication was added, and no new public vocabulary was invented during this partial integration.

## P. BattleSystems Wiring

Production `BattleSystems` now constructs one minimal `PreparationStateOwner` and uses it as the default `PreparationInterruptionPort`. It passes the canonical `StateEffectivenessPolicy` into `StateApplicationCoordinator` and binds both EXHAUSTION interruption routes:

```text
effective first CREATE -> generic committed activation adapter
resident resume       -> effectiveness transition adapter
```

No preparation scheduler, queue, progress engine or Stage15 execution runtime was introduced.

## Q. Tests Added

Existing `tests/test_stage12_690101_exhaustion.py` remains the permission/lifecycle contract suite.

Added:

```text
tests/test_stage12_690101_preparation_integration.py
```

It covers canonical preparation identity, holder/provider interruption, duplicate interruption prevention, production non-Noop binding, first effective CREATE, initial SUPPRESSED CREATE, INSIGHT rejection, resident resume, multiple suppression causes, same-envelope expiry, zero-RNG/query-event behavior and Stage15 leakage/static architecture guards.

## R. RNG Regression

PASS under the full regression suite.

Denied NEW ACTIVE EXHAUSTION coverage proves zero activation RNG, zero TargetOperation allocation and zero target-selection RNG under RD-SF-004.

## S. Stage9 Regression

PASS under the full regression suite.

## T. Stage10 Regression

PASS under the full regression suite.

## U. Stage11 Regression

PASS under the full regression suite.

Expected governance remains:

```text
Stage11 Reopen Required = NO
```

## V. 690089 Regression

PASS under the full regression suite, including the existing 690089 dedicated tests and the new EXHAUSTION pair coverage.

690089 remains:

```text
Runtime = FROZEN
```

## W. Shared Foundation Regression

PASS under the full regression suite.

## X. Static Architecture Audit

The 690101 integration module contains:

```text
no SkillRuntime.enabled mutation
no direct random use
no TargetSystem access
no ActionSystem natural-action denial
no EventBus publication
no implementation of other Stage12 gameplay states
```

## Y. Gameplay Changes

Implemented:

```text
effective EXHAUSTION denies NEW ACTIVE skill operation admission
real PREPARING identity has a minimal production owner
effective EXHAUSTION first CREATE interrupts existing holder Active preparation
resident EXHAUSTION resume interrupts existing holder Active preparation
```

Not implemented:

```text
preparation round progression
prepared-skill completion/execution
Stage15 scheduler/queue/runtime
```

## Z. pytest / demo / CI

Latest pre-documentation dependency-resolution validation:

```text
SHA    = 9dd4affbbacf75f8145da537d20dd3417cac0654
CI     = 36314683277 / success
pytest = 1229 passed
demo   = PASS
```

A fresh documentation-complete CI and post-merge `main` CI remain mandatory before final round closure.

## AA. Files Created / Updated

Created:

```text
sgs_v2/battle_core/exhaustion_integration.py
tests/test_stage12_690101_exhaustion.py
stages/stage12/STAGE12_690101_EXHAUSTION_RUNTIME_INTEGRATION.md
```

Updated:

```text
sgs_v2/battle_core/battle_systems.py
stages/stage12/README.md
PROJECT_STATUS.md
```

## AB. Commit SHA

```text
Tested implementation snapshot:
d8dbfa1537cb93a77505b4da5be5240c814193c6

Pull Request:
#14
```

The final documentation-only evidence commit is expected to differ from the tested implementation snapshot; no production code changes occur after the snapshot above.

## AC. Implementation Blockers

```text
BLOCKER-690101-PREP-001 = CLOSED
BLOCKER-690101-PREP-002 = CLOSED
```

There is no remaining preparation architecture blocker for 690101. Runtime Freeze itself still requires an independent audit.

## AD. Current Gates

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

```text
690101 EXHAUSTION Independent Runtime Freeze Audit
```

Do not enter 690107 before that audit passes. Only an audit PASS may change 690101 Runtime to FROZEN and Stage12 Runtime Frozen to 2 / 7.
