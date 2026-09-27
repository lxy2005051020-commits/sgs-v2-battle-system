# Stage12 Shared Foundation Implementation Status

Date: 2026-09-27  
Current round: `STAGE12_SHARED_FOUNDATION_IMPLEMENTATION_ROUND3_SKILL_PERMISSION_PREPARATION_TARGET`  
Round 3 implementation code SHA: `7ed9c55bfe503b69f5e0c8bcf36a2066182310ad`  
Round 3 validation CI run: `36304712981` / success  
Status: **ROUND 3 PASS / SHARED FOUNDATION IMPLEMENTATION PARTIAL**

## 1. Repository lock

- Battle Round 3 start: `c60a61346022ffb1e12141a198f1e1f3d57d029b`
- Research Round 3 start/final: `e18ae56a4db5662b87458dfa8fdff25dcdd8053b`
- Research repository changes in Round 3: **NONE**
- Stage11 Reopen Required: **NO**

Round 1 and Round 2 remain accepted production infrastructure and are not reimplemented:

- stable `ProviderRef` / `SkillProviderRef` / `EquipmentProviderRef`;
- `DependencyEvaluationSupport`;
- `StateEffectivenessPolicy`;
- `ProviderValidityPolicy`;
- state admission / conflict / transaction / removal / lifetime runtime;
- `EffectivenessTransitionCoordinator`;
- RD-SF-003 same-envelope settlement;
- Stage9 / Stage11 shared-policy seams;
- DQ-SF-21 slot-0 Provider migration.

## 2. Implementation matrix

| Capability | Designed | Implemented | Tested | Integrated |
| --- | --- | --- | --- | --- |
| Stable Provider identity | YES | YES | YES | YES |
| DependencyEvaluationSupport | YES | YES | YES | YES |
| StateEffectivenessPolicy core | YES | YES | YES | YES |
| ProviderValidityPolicy core | YES | YES | YES | YES |
| StateCandidate / Admission / Conflict | YES | YES | YES | YES |
| StateApplicationTransaction / Coordinator | YES | YES | YES | YES |
| StateRemoval / Lifetime / Transition | YES | YES | YES | YES |
| RD-SF-003 same-envelope settlement | YES | YES | YES | YES |
| SkillType / PreparationMode schema | YES | YES | YES | YES |
| SkillPermissionPolicy runtime | YES | YES | YES | YES |
| SkillOperationAdmissionCoordinator | YES | YES | YES | YES |
| ProviderValidity / Permission pre-RNG topology | YES | YES | YES | YES |
| PreparationInterruptionPort infrastructure | YES | YES | YES | GENERIC INFRASTRUCTURE |
| Concrete Preparation Owner | FUTURE STAGE15 | NO | N/A | NOT YET AVAILABLE |
| TargetOperationId | YES | YES | YES | YES |
| TargetOperation / QueryMode | YES | YES | YES | YES |
| TargetSelectionResult / Provenance | YES | YES | YES | YES |
| SkillTargetPolicy runtime | YES | YES | YES | YES |
| SkillResolver migration | YES | YES | YES | BEHAVIOR-PRESERVING |
| BattleSystems Round3 canonical wiring | YES | YES | YES | YES |
| EquipmentEffectivenessPolicy runtime | YES | NO | NO | NO |
| EquipmentContributionRegistry runtime | YES | NO | NO | NO |
| ExecutionRight remaining runtime | YES | NO | NO | PARTIAL LEGACY FOUNDATION |
| Capture composite generic seams | YES | NO | NO | NO |
| Final Stage12 Event transition integration | YES | PARTIAL | PARTIAL | PARTIAL |

## 3. Skill permission runtime

`SkillPermissionPolicy` is now the canonical holder-level permission owner for Skill operation admission.

Typed input includes:

- actor identity;
- exact `SkillProviderRef`;
- `SkillType`;
- `PreparationMode`;
- operation kind (`NEW_ADMISSION` / `CONTINUATION`).

Typed results include:

- `ALLOW`;
- `DENY_STATE_PERMISSION`;
- `DENY_UNSUPPORTED_BOUNDARY`;
- `CONTINUATION_NOT_REEVALUATED`.

The policy is pure:

- no RNG;
- no EventBus publication;
- no state mutation;
- no mutation of `SkillRuntime.enabled`.

No real Stage12 state adapter is registered in Round 3. Executable tests use synthetic denial adapters only.

## 4. Skill operation admission

`SkillOperationAdmissionCoordinator` now composes:

```text
SkillProviderRef
-> ProviderValidityPolicy
-> SkillPermissionPolicy
-> SkillOperationAdmissionDecision
```

Provider validity is evaluated first. A Provider decision other than `VALID` rejects admission without invoking downstream activation or target RNG.

Typed admission results are:

- `ALLOW`;
- `DENY_PROVIDER_INVALID`;
- `DENY_PERMISSION`;
- `UNSUPPORTED_BOUNDARY`.

`SkillRuntime.enabled` remains only a baseline Provider fact consumed by `ProviderValidityPolicy`. Transient suppression is not written back into it.

## 5. Skill classification compatibility

Production `SkillDefinition` now carries the frozen Shared Foundation metadata:

- `SkillType`;
- `PreparationMode`.

RD-SF-001 is executable compatibility behavior:

```text
legacy SkillDefinition
-> SkillType.ACTIVE
-> PreparationMode.NONE
```

No existing caller must add metadata merely to retain pre-Stage12 behavior.

## 6. Preparation interruption infrastructure

Round 3 implements:

- `PreparationInterruptionPort`;
- `PreparationInterruptionRequest`;
- `PreparationInterruptionResult`;
- scopes `HOLDER_ACTIVE` and `PROVIDER`;
- results `INTERRUPTED`, `NOT_PREPARING`, `PROVIDER_NOT_MATCHED`, `UNSUPPORTED`;
- `PreparationInterruptionTransitionAdapter` for synchronous binding to state/provider effectiveness transition ports.

Production composition currently uses explicit:

```text
NoopPreparationInterruptionPort
```

with the hard invariant that the current production runtime contains no PREPARING work.

This placeholder is **NON-COMPLETE** and is not evidence that any Stage12 state requiring real preparation interruption is Runtime Frozen.

```text
Concrete Preparation Owner = NOT YET AVAILABLE
Stage15 Active = NO
```

No preparation scheduler, progress engine or Stage15 active-preparation runtime is implemented.

## 7. Target operation runtime

Round 3 implements typed:

- `TargetOperationId`;
- `TargetOperation`;
- `TargetRelation = ENEMY / ALLY / SELF`;
- `TargetCardinality = SINGLE / CHOOSE_N / FIXED_ALL`;
- `TargetSelectorKind = RANDOM / DETERMINISTIC / EXPLICIT`;
- `TargetEligibilityContext`;
- producer Provider identity and admitted-operation key.

`TargetOperationId` is:

- immutable;
- deterministic per battle;
- value-equal;
- explicitly non-orderable for gameplay priority;
- distinct from Stage9 `TargetResolutionId`.

## 8. Query freshness and selection provenance

Round 3 implements:

```text
NEW_QUERY
INHERIT_RESOLVED
DERIVE_FROM_RESOLVED
LOCK_RESOLVED
```

Only an explicit `NEW_QUERY` creates a new `TargetOperation` / `TargetOperationId`.

`TargetSelectionResult` carries:

- operation id;
- target ids;
- provenance.

Provenance is:

```text
FRESH_SELECTED
INHERITED
DERIVED
LOCKED
```

Inherited, derived and locked continuations reuse the original operation identity and do not allocate a fresh query merely because a new child Effect or hit exists.

## 9. Skill target policy

`SkillTargetPolicy` is now the canonical Shared Foundation target-constraint owner for already-admitted fresh Skill target operations.

It produces a typed `TargetPolicyDecision` containing:

- eligible candidate ids;
- required target ids;
- excluded target ids;
- cardinality-preservation flag;
- explicit unsupported boundary marker.

The policy consumes zero RNG.

`TargetSystem` remains the owner of:

- raw relationship candidate primitives;
- random selection primitives;
- target RNG through `BattleContext.random`.

Round 3 registers no real target-state adapter. Required/excluded behavior is tested with synthetic adapters only.

## 10. SkillResolver migration

Production `BattleSystems.skill_resolver` now receives the canonical:

- `SkillOperationAdmissionCoordinator`;
- `SkillTargetPolicy`.

For slot-bearing canonical Skill providers, the runtime path is:

```text
SkillProviderRef
-> ProviderValidityPolicy
-> SkillPermissionPolicy
-> admitted
-> legacy-compatible empty-pool preflight
-> activation RNG
-> explicit NEW_QUERY
-> TargetOperation
-> SkillTargetPolicy
-> TargetSystem selector
-> TargetSelectionResult
-> existing Effect construction
```

The pre-activation empty-pool check is retained because pre-Stage12 SkillResolver already guaranteed that an empty target pool consumes no activation RNG. It is enumeration-only: it creates no `TargetOperation`, evaluates no `SkillTargetPolicy`, and consumes no target RNG.

Failed activation creates no `TargetOperation` and consumes no target RNG.

The existing external `SkillResolutionResult` field surface is unchanged.

Legacy direct slotless SkillResolver construction remains an explicit compatibility seam. It does not construct a fallback canonical `ProviderValidityPolicy`.

## 11. Normal Attack boundary

Normal Attack remains completely outside `SkillTargetPolicy`.

Its owner remains:

```text
TargetResolutionSystem
-> Confusion
-> Taunt
-> default selector
-> Guard
```

Static architecture tests verify:

- `TargetResolutionSystem` does not depend on `SkillTargetPolicy`;
- `SkillTargetPolicy` does not depend on `TargetResolutionSystem`.

## 12. BattleSystems canonical wiring

One production `BattleSystems` graph constructs exactly one:

- `SkillPermissionPolicy`;
- `SkillOperationAdmissionCoordinator`;
- `SkillTargetPolicy`;
- explicit Preparation interruption port placeholder.

`SkillResolver` and `RecoveryOpportunitySystem` continue to share the same canonical `ProviderValidityPolicy`.

No consumer constructs a fallback `ProviderValidityPolicy`.

## 13. RNG ownership

Round 3 preserves:

```text
ProviderValidityPolicy = 0 RNG
SkillPermissionPolicy = 0 RNG
SkillOperationAdmissionCoordinator = 0 RNG
PreparationInterruptionPort infrastructure = 0 RNG
SkillTargetPolicy = 0 RNG
```

Owned draws remain:

- activation probability -> SkillResolver / BattleContext.random;
- target randomization -> TargetSystem / BattleContext.random.

Executable tests prove:

- missing/mismatched/baseline-disabled/suppressed Provider rejection consumes zero activation and target RNG;
- permission denial consumes zero activation and target RNG;
- failed activation consumes no target RNG;
- policy evaluation consumes zero target RNG;
- random selector remains the target RNG owner.

## 14. Static architecture audit

Round 3 semantic/static checks pass:

- no `random` module import in permission/admission/preparation/target-policy modules;
- no `context.random` use in those pure foundation modules;
- no Stage12 seven-state IDs in Round 3 production modules;
- no Stage12 state-name switch ladder in Round 3 production modules;
- no SkillTargetPolicy / TargetResolutionSystem dependency cycle;
- no SkillResolver fallback construction of `ProviderValidityPolicy`;
- exactly one canonical Round 3 policy/coordinator instance in `BattleSystems`.

## 15. Tests, demo and CI

Round 2 validated baseline: **1006 passed**.

Round 3 implementation SHA `7ed9c55bfe503b69f5e0c8bcf36a2066182310ad`:

- pytest: **1061 passed**;
- Round 3 executable-test delta: **+55**;
- demo: **PASS**;
- GitHub Actions run: **36304712981 / success**.

The full suite includes Stage9, Stage10, Stage11 and Round1/2 Shared Foundation regressions.

## 16. Gameplay change boundary

Stage12 individual-state gameplay implemented in Round 3: **NONE**.

No production adapter or state-id switch implements:

- INSIGHT gameplay;
- EXHAUSTION Active denial or preparation interruption;
- FALSE_REPORT Provider suppression;
- PROVOCATION target constraints;
- INTIMIDATION Provider binding/suppression;
- SABOTAGE equipment suppression;
- CAPTURE target/action/damage/recovery behavior.

RD-SF-004 remains a generic topology rule only:

```text
permission denial
-> before activation RNG
```

It does not mean EXHAUSTION gameplay is implemented.

## 17. Current gates

```text
STAGE12_SHARED_FOUNDATION_IMPLEMENTATION_ROUND1 = PASS
STAGE12_SHARED_FOUNDATION_IMPLEMENTATION_ROUND2_STATE_TRANSACTION_TRANSITION = PASS
STAGE12_SHARED_FOUNDATION_IMPLEMENTATION_ROUND3_SKILL_PERMISSION_PREPARATION_TARGET = PASS

Stage11 Runtime = FROZEN
Stage11 Reopen Required = NO

Stage12 Research = 7 / 7 FROZEN
Stage12 Shared Foundation Design = FROZEN
Stage12 Shared Foundation Implementation = PARTIAL

Skill Permission Runtime = IMPLEMENTED
Skill Admission Coordinator = IMPLEMENTED
Preparation Port Infrastructure = IMPLEMENTED
Concrete Preparation Owner = NOT YET AVAILABLE
TargetOperation / TargetSelectionResult = IMPLEMENTED
SkillTargetPolicy = IMPLEMENTED

Stage12 individual state gameplay = NONE
Stage12 Runtime Frozen = 0 / 7

Stage13 Active = NO
Stage14 Active = NO
Stage15 Active = NO
```

Round 3 does not make Shared Foundation complete.

Remaining foundation work includes:

- EquipmentContributionRegistry runtime;
- EquipmentEffectivenessPolicy runtime;
- EquipmentContributionDependency;
- remaining ExecutionRight runtime;
- per-dimension SNAPSHOT / JIT runtime;
- Capture composite generic seams;
- remaining Trigger/equipment JIT infrastructure;
- final committed transition/event seams;
- remaining cross-domain wiring.

## 18. Next

`Shared Foundation Implementation Round 4: Equipment Effectiveness + ExecutionRight + Remaining Runtime`

Round 4 must continue to avoid formal gameplay integration of SABOTAGE, equipment-linked FALSE_REPORT and CAPTURE until their registered state-specific adapters are deliberately connected.
