# Stage12 Shared Foundation Implementation Status

Date: 2026-09-27  
Current round: `STAGE12_SHARED_FOUNDATION_IMPLEMENTATION_ROUND2_STATE_TRANSACTION_TRANSITION`  
Round 2 implementation code SHA: `7bf32c7bdb4157e9f3f17972d06f66989a5634e4`  
Round 2 validation CI run: `36303239602` / success  
Status: **ROUND 2 PASS / SHARED FOUNDATION IMPLEMENTATION PARTIAL**

## 1. Repository lock

- Battle Round 2 start: `32d029b2703d4aa3e91d1635987e8cddeb641f6e`
- Research Round 2 start/final: `e18ae56a4db5662b87458dfa8fdff25dcdd8053b`
- Research repository changes in Round 2: **NONE**
- Stage11 Reopen Required: **NO**

Round 1 remains accepted production infrastructure and is not reimplemented:

- `ProviderRef` / `SkillProviderRef` / `EquipmentProviderRef`
- `DependencyEvaluationSupport`
- `StateEffectivenessPolicy`
- `ProviderValidityPolicy`
- `BattleSystems` canonical wiring
- Stage9 behavior-preserving effectiveness seam
- Stage11 shared-policy migration
- DQ-SF-21 slot-0 repair

## 2. Implementation matrix

| Capability | Designed | Implemented | Tested | Integrated |
| --- | --- | --- | --- | --- |
| Stable Provider identity | YES | YES | YES | YES |
| DependencyEvaluationSupport | YES | YES | YES | YES |
| StateEffectivenessPolicy core | YES | YES | YES | YES |
| ProviderValidityPolicy core | YES | YES | YES | YES |
| StateCandidate | YES | YES | YES | YES |
| StateAdmissionPolicy | YES | YES | YES | YES |
| StateConflictPolicy | YES | YES | YES | YES |
| StateApplicationTransaction | YES | YES | YES | YES |
| StateApplicationCoordinator | YES | YES | YES | YES |
| CREATE / REFRESH / REPLACE generation semantics | YES | YES | YES | YES |
| StateRemovalPolicy | YES | YES | YES | YES |
| StateRemovalCoordinator | YES | YES | YES | YES |
| StateLifetimeSpec | YES | YES | YES | YES |
| RD-SF-003 same-envelope settlement | YES | YES | YES | YES |
| EffectivenessTransitionCoordinator | YES | YES | YES | YES |
| State / Provider transition ports | YES | YES | YES | GENERIC INFRASTRUCTURE |
| Pre-commit dependency cycle validation | YES | YES | YES | YES |
| Legacy Lifecycle.apply compatibility | YES | YES | YES | PRESERVED |
| SkillPermissionPolicy runtime | YES | NO | NO | NO |
| SkillOperationAdmissionCoordinator full runtime | YES | NO | NO | NO |
| PreparationInterruptionPort integration | YES | NO | NO | NO |
| SkillTargetPolicy runtime | YES | NO | NO | NO |
| EquipmentEffectivenessPolicy runtime | YES | NO | NO | NO |
| ExecutionRight remaining runtime | YES | NO | NO | PARTIAL LEGACY FOUNDATION |
| Capture composite seams | YES | NO | NO | NO |
| Final Stage12 RNG/Event integration | YES | PARTIAL | PARTIAL | PARTIAL |

## 3. State application topology

Round 2 production ingress is:

```text
StateCandidate validation
-> StateAdmissionPolicy
-> StateConflictPolicy
-> immutable StateApplicationTransaction preparation
-> dependency topology preflight
-> resident/generation precondition validation
-> authorized StateApplicationGenerationId allocation
-> StateLifecycleSystem physical commit
-> dependency topology commit
-> affected closure recompute
-> typed transition ports
-> typed StateApplicationResult
```

The coordinator never calls `StateRegistry.add/remove/replace`. `StateLifecycleSystem` remains the physical state writer.

Rejected admission/conflict/unsupported/cycle paths do not allocate a candidate generation and do not emit committed state facts.

## 4. Candidate and admission

`StateCandidate` is non-resident and contains only Shared Foundation application inputs:

- state and owner identity;
- source attribution;
- typed runtime parameter candidate;
- typed physical lifetime;
- optional strength / priority metadata;
- explicit `ProviderDependency` records;
- application provenance.

It contains no physical `instance_id` and no application generation id.

`StateAdmissionPolicy` returns typed decisions:

- `ALLOW`
- `REJECT_IMMUNITY`
- `REJECT_SPECIAL_PROTECTION`
- `REJECT_INVALID_TARGET`
- `REJECT_UNSUPPORTED_BOUNDARY`

Admission is pure: no registry write, RNG, EventBus fact, conflict resolution or generation allocation.

## 5. Conflict and transaction semantics

`StateConflictPolicy` returns:

- `CREATE`
- `REFRESH`
- `REPLACE`
- `REJECT_CONFLICT`
- `UNSUPPORTED_BOUNDARY`

With no resident match the foundation may CREATE. With a resident match and no registered contract adapter, the default is explicit `UNSUPPORTED_BOUNDARY`; there is no universal same-state refresh rule.

Generation semantics are executable:

| Disposition | Physical instance | Generation |
| --- | --- | --- |
| CREATE | new | new |
| REFRESH | same | new |
| REPLACE | new | new |
| reject / unsupported | unchanged | no candidate allocation |

Resume remains an effectiveness transition only. It does not invoke refresh, allocate a generation, reset lifetime or consume RNG.

## 6. Dependency and cycle atomicity

Round 2 extends `DependencyEvaluationSupport` with:

- pure prospective topology replacement validation;
- multi-root affected closure;
- deterministic node cleanup after physical removal.

Cycle validation happens before generation allocation and before physical mutation. The cycle discriminator test proves a rejected cycle leaves Registry, EventBus and candidate generation allocation unchanged.

## 7. StateLifetimeSpec

Typed physical lifetime domains now exist independently from Stage10 persistence:

- `ROUND_CALENDAR`
- `HOLDER_ACTION_WINDOW`
- `EXPLICIT_PHASE_EXPIRY`

Stage12 typed lifetime is stored in `StateInstance.lifetime_spec`; it is not encoded by passing legacy `duration_rounds/lifecycle_window` through the Stage10 persistence detector.

Behavioral counters remain outside `StateLifetimeSpec`. In particular Stage11 STUN `remaining_blocks` remains a gameplay opportunity counter.

Suppression does not pause physical lifetime. Holder-action and phase/round lifetime settlement does not query StateEffectiveness before advancing/removing a due state.

## 8. RD-SF-003 same-envelope runtime

RD-SF-003 is now production behavior:

```text
1. snapshot complete due set
2. deterministic instance_id ordering
3. physically remove complete due set
4. publish committed expiry facts
5. remove dependency nodes / recompute affected closure
6. invoke typed transition ports
7. only then later gameplay continues
```

The first expiry event in an envelope already observes every member of that due set as physically absent.

If a suppressed state and its suppression cause are both due in the same envelope, the due state cannot transiently resume because it is absent before transition recomputation.

Owner-defeat cleanup and battle teardown also batch physical state removal before their per-state observable facts.

## 9. Removal architecture

`StateRemovalPolicy` distinguishes gameplay eligibility from infrastructure lifecycle removal.

Gameplay operations:

- `ORDINARY_CLEANSE`
- `SPECIALIZED_CLEANSE`
- `SCRIPTED_GAMEPLAY_REMOVE`

Infrastructure operations:

- `NATURAL_EXPIRY`
- `OWNER_DEFEAT_CLEANUP`
- `BATTLE_TEARDOWN`

Infrastructure operations return the lifecycle allow path before gameplay cleanse adapters. Gameplay removal without an evidence-backed adapter remains explicit `UNSUPPORTED_BOUNDARY`.

Rejected gameplay removal preserves the exact resident state. Committed removal uses `StateLifecycleSystem.remove()`, then settles the affected dependency closure.

## 10. Effectiveness transition runtime

`EffectivenessTransitionCoordinator` is non-authoritative and owns no Registry, Lifecycle, Damage, Recovery, Target, Action, RNG or Provider identity.

It:

- captures canonical StateEffectiveness / ProviderValidity decisions for an affected reverse-dependency closure;
- recomputes only that closure after a committed mutation;
- emits an internal typed transition only when status actually changes;
- invokes generic synchronous State / Provider transition ports;
- emits no public EventBus suppression/resume event in Round 2.

Covered transitions include:

- EFFECTIVE -> SUPPRESSED;
- SUPPRESSED -> EFFECTIVE;
- VALID -> SUPPRESSED;
- SUPPRESSED -> VALID;
- multi-cause removal with no false resume;
- removed-state no-resume behavior;
- unchanged query with no duplicate transition.

## 11. Legacy compatibility and architecture

Legacy Stage1-11 `StateLifecycleSystem.apply()/refresh()` remains available.

The Stage9 / Stage11 existing conflict failure surface remains `ValueError` where it was already `ValueError`. A dedicated regression covers the legacy Stage9 COMBO conflict surface.

Static architecture tests enforce:

- Round 2 policy/coordinator modules do not physically mutate `StateRegistry`;
- `StateApplicationCoordinator` calls the Lifecycle transaction seam;
- Lifecycle does not instantiate `StateApplicationCoordinator`;
- transition coordinator does not mutate Registry;
- Round 2 transaction modules import/use no random module and do not touch `context.random`;
- Round 2 foundation production modules contain no seven-state gameplay switches.

## 12. Tests, demo and CI

Round 1 validated baseline: **951 passed**.

Round 2 validated implementation SHA `7bf32c7bdb4157e9f3f17972d06f66989a5634e4`:

- pytest: **1006 passed**
- Round 2 delta: **+55 executable tests**
- demo: **PASS**
- GitHub Actions run: **36303239602 / success**

The full suite includes Stage9, Stage10 and Stage11 regressions; this was not a Round2-only test selection.

## 13. Gameplay change boundary

Stage12 individual state gameplay implemented in Round 2: **NONE**.

No production adapter or state-id switch implements:

- INSIGHT protected controls;
- EXHAUSTION skill blocking;
- FALSE_REPORT Provider suppression;
- PROVOCATION target constraints;
- INTIMIDATION binding / RNG;
- SABOTAGE equipment suppression;
- CAPTURE action/damage/recovery behavior.

The tests use synthetic state and suppression adapters only.

## 14. Frozen design conformance

Round 2 implementation was checked against:

- DQ-SF-01: State Admission;
- DQ-SF-22: State Application Transaction;
- DQ-SF-24: Lifecycle Clock;
- DQ-SF-25: Removal/Cleanse architecture;
- RD-SF-003: same-envelope settlement.

No implementation drift requiring a design or Stage11 reopen was found.

## 15. Current gates

```text
STAGE12_SHARED_FOUNDATION_IMPLEMENTATION_ROUND1 = PASS
STAGE12_SHARED_FOUNDATION_IMPLEMENTATION_ROUND2_STATE_TRANSACTION_TRANSITION = PASS

Stage11 Runtime = FROZEN
Stage11 Reopen Required = NO

Stage12 Research = 7 / 7 FROZEN
Stage12 Shared Foundation Design = FROZEN
Stage12 Shared Foundation Implementation = PARTIAL

Stage12 individual state gameplay = NONE
Stage12 Runtime Frozen = 0 / 7

Stage13 Active = NO
Stage14 Active = NO
Stage15 Active = NO
```

Round 2 does not make Shared Foundation complete. Remaining foundation work includes Skill Permission, Skill Operation Admission, Preparation interruption, target policy, equipment effectiveness, remaining ExecutionRight seams, Capture composite seams and final RNG/Event integration.

## 16. Next

`Shared Foundation Implementation Round 3: Skill Permission + Preparation + Target Runtime`

Planned scope:

- `SkillPermissionPolicy` runtime;
- `SkillOperationAdmissionCoordinator`;
- `PreparationInterruptionPort` infrastructure;
- `SkillTargetPolicy`;
- `TargetOperation`;
- `TargetSelectionResult`;
- `NEW_QUERY / INHERIT / DERIVE / LOCK`;
- Provider-invalid / permission-denied pre-RNG topology.

Round 3 must continue to avoid formal gameplay integration of EXHAUSTION, PROVOCATION and CAPTURE until their registered state-specific adapters are deliberately connected.
