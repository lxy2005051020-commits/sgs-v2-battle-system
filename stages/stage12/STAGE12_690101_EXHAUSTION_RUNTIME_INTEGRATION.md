# Stage12 · 690101 EXHAUSTION Runtime Integration

> Date: **2026-09-27**  
> Research Contract: **v0.2-frozen**  
> Battle baseline: **6374f528d6db8af2df34ea6a4d012ffe7529fde1**  
> Research baseline: **e18ae56a4db5662b87458dfa8fdff25dcdd8053b**  
> Integration status: **PARTIAL / FREEZE_BLOCKED**  
> Stage12 Runtime Frozen: **1 / 7**

## A. Repository Lock

Battle repository:

```text
lxy2005051020-commits/sgs-v2-battle-system
baseline main = 6374f528d6db8af2df34ea6a4d012ffe7529fde1
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

Shared Foundation currently provides:

```text
PreparationInterruptionPort = IMPLEMENTED
PreparationInterruptionTransitionAdapter = IMPLEMENTED
Concrete PREPARING owner = NOT AVAILABLE
BattleSystems default port = NoopPreparationInterruptionPort
```

This integration wires resident EXHAUSTION `SUPPRESSED/INACTIVE -> EFFECTIVE` transitions into the canonical interruption bridge. With an injected concrete/fake port, the transition synchronously issues a `HOLDER_ACTIVE` interruption request.

However, two required production facts are still unavailable:

1. There is no concrete PREPARING owner to interrupt.
2. A first state `CREATE` is not represented by the current transition coordinator as `ABSENT -> EFFECTIVE`; therefore first-application EXHAUSTION cannot yet command a production preparation owner through the existing transition seam.

No Stage15 scheduler, preparation queue, progress engine or fake production owner was created.

Verdict:

```text
INTEGRATION_DEPENDENCY_BLOCKER
Concrete Preparation Owner required
First-application PREPARING interruption command seam required
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

Added exactly one mechanism registration:

```text
register_exhaustion_integration(...)
```

It registers:

```text
SkillPermissionPolicy rule adapter
EffectivenessTransitionCoordinator
  -> PreparationInterruptionTransitionAdapter
  -> existing PreparationInterruptionPort
```

No `ExhaustionRuntime` facade was created.

## Q. Tests Added

New file:

```text
tests/test_stage12_690101_exhaustion.py
```

Coverage includes application/effectiveness, ACTIVE/non-ACTIVE taxonomy, legacy Active compatibility, preparation-mode boundary, continuation, enabled-state immutability, pre-RNG denial, target short-circuit, ProviderValidity precedence, natural action/normal attack, INSIGHT admission/suppression/resume/expiry, same-envelope expiry, preparation resume bridge, reapplication unsupported boundary and static architecture guards.

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
resident EXHAUSTION resume can command the canonical preparation interruption port
```

Not implemented:

```text
concrete PREPARING state/progress owner
first-application PREPARING interruption completion
```

## Z. pytest / demo / CI

Validated implementation snapshot:

```text
SHA    = d8dbfa1537cb93a77505b4da5be5240c814193c6
CI     = 36313725482 / success
pytest = 1215 passed
demo   = PASS
```

Baseline was 1186 passed, so this integration adds 29 executable tests while preserving the prior suite.

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
BLOCKER-690101-PREP-001
Concrete Preparation Owner does not exist.

BLOCKER-690101-PREP-002
Current EffectivenessTransitionCoordinator does not emit a first CREATE
as ABSENT -> EFFECTIVE, so first-application preparation interruption
has no lawful existing command seam.
```

These are external architecture dependencies. They are not permission-layer defects.

## AD. Current Gates

```text
Stage11 Runtime = FROZEN
Stage11 Reopen Required = NO

Stage12 Research = 7 / 7 FROZEN
Stage12 Shared Foundation Design = FROZEN
Stage12 Shared Foundation Implementation = COMPLETE
690089 Runtime = FROZEN

690101 Gameplay = PARTIAL
690101 Runtime = FREEZE_BLOCKED
Stage12 Runtime Frozen = 1 / 7

Stage13 Active = NO
Stage14 Active = NO
Stage15 Active = NO
```

## AE. NEXT

Do **not** enter 690107 yet.

Required next governance action:

```text
resolve explicit 690101 preparation integration dependency
without activating Stage15 as a whole
```

Only after the concrete preparation requirement is lawfully closed may 690101 proceed to Independent Runtime Freeze Audit.
