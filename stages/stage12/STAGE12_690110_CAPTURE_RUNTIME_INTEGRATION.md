# Stage12 690110 CAPTURE Runtime Integration

Date: 2026-09-28  
Status: **IMPLEMENTED_PENDING_RUNTIME_AUDIT / RUNTIME NOT YET FROZEN**

## A. Repository Lock

```text
Battle main at integration start
= 824c0749d3e9c2540765b1d0ae0d4eae7e547f21

Research main
= e18ae56a4db5662b87458dfa8fdff25dcdd8053b

Research repository
= READ ONLY / UNCHANGED

Pre-integration full-suite baseline
= 1558 passed
```

Research authority: `states/control/capture/MECHANISM_CONTRACT.md` v1.0-frozen.

## B. Integration Scope

690110 CAPTURE is integrated only to its frozen positive scope:

- Natural Action denial.
- verified NEW actor-driven outgoing damage denial.
- Counter opportunity may exist, but Counter damage is denied.
- PASSIVE / COMMAND Provider suppression.
- attached Active-origin periodic damage continues.
- received Recovery is prevented by the canonical RecoverySystem prevention seam.
- fresh friendly SINGLE / CHOOSE_N target queries exclude the captured holder before selector RNG.
- Equipment ATTRIBUTE contribution becomes ineffective.
- ordinary Insight does not reject Capture.
- ordinary cleanse does not remove Capture.
- source death does not end established Capture.
- restoration is future-only RESUME.

No bounded research question is silently promoted into gameplay.

## C. CAPTURE Composite Runtime Architecture

CAPTURE is implemented as typed rule contributors attached to existing canonical owners:

```text
CAPTURE State fact
├─ ActionSystem / CurrentActorPermissionPolicy
├─ DamageInstanceCoordinator / DamageExecutionRightPort
├─ ProviderValidityPolicy
├─ RecoverySystem / RecoveryExecutionPreventionPolicy
├─ SkillTargetPolicy
├─ EquipmentEffectivenessPolicy
├─ StateConflictPolicy
├─ StateRemovalPolicy
└─ StateLifecycleSystem remains the physical lifetime owner
```

There is no `CaptureRuntime`, `CaptureManager`, `CaptureEngine`, or second gameplay universe.

## D. Frozen / Bounded Contract Map

Frozen positive scope is executable. The following remain explicit boundaries:

```text
Q16  already-created DamageRequest
Q23  detached Passive state without explicit dependency
Q34  Emergency Aid discriminator
Q42  ALL_ALLIES
Q44  delayed friendly work
Q45  already-locked friendly target
Q63  equipment reactive / non-ATTRIBUTE contribution
Q70-Q74 reapplication / multi-source semantics
Q78  holder-death cleanup internals
hidden universal damage gate = NON-CLAIM
```

Where a production seam needs an answer inside those areas, the runtime exposes `UNSUPPORTED_BOUNDARY` rather than inventing one.

## E. Natural Action Restriction

`CurrentActorPermissionPolicy` receives the typed `NATURAL_ACTION` query. Effective Capture contributes a DENY reason before STUN consumption and before NormalAttack creation.

## F. STUN Interaction

Capture and STUN remain independent. When both are effective, Capture blocks the action first and STUN `remaining_blocks` is not consumed.

## G. NormalAttack Short-circuit

A Capture-denied natural action returns before NormalAttack execution, target resolution and target selector RNG. No synthetic NormalAttack is created and cancelled later.

## H. Damage Work Taxonomy

The existing Shared Foundation taxonomy is used unchanged:

```text
NEW_ACTOR_DRIVEN_DAMAGE
COUNTER_DAMAGE
ATTACHED_EXISTING_DOT
FREE_PROXY_DAMAGE
ALREADY_CREATED_DAMAGE_REQUEST
OTHER_BOUNDED
```

No Capture-specific parallel damage taxonomy was created.

## I. NEW Actor-driven Damage

Production Active-skill `DamageEffect` is classified as `NEW_ACTOR_DRIVEN_DAMAGE`. Its current-actor permission is `RECHECK_AT_EXECUTION`. A captured current actor is denied before a `DamageRequest` or `DamageInstance` exists.

This is a permission denial, not the WEAKNESS zero-damage path.

## J. Counter Damage

`CounterSystem` preserves Counter registration and the Counter opportunity/event. Before creating Counter `DamageRequest`, it queries the same typed execution-right seam with `COUNTER_DAMAGE`.

A captured Counter owner therefore produces no Counter damage while the Counter architecture itself remains intact.

## K. Attached Active DOT

Production `PERIODIC_DAMAGE` is classified as `ATTACHED_EXISTING_DOT` with the actor-permission dimension `NOT_APPLICABLE`. Capture on the historical source therefore does not reinterpret an already attached DOT tick as new outgoing actor work.

## L. Free Proxy Damage

The runtime decision is based on the typed current actor and work kind, not historical provenance alone. A free proxy actor B remains allowed when historical source A is captured.

## M. Already-created DamageRequest Boundary

Q16 remains executable as `UNSUPPORTED_BOUNDARY`. No JIT-reject or universal-snapshot answer was invented.

## N. ExecutionRight Integration

`ExecutionRightSpec` is reused directly. Capture does not introduce universal JIT or universal snapshot semantics. Only the dimensions required by the classified work are queried.

## O. PASSIVE / COMMAND Provider Suppression

At Capture application, currently loaded target-owned PASSIVE / COMMAND Providers are explicitly bound to the Capture `StateNode` through Shared Foundation dependency topology.

`ProviderValidityPolicy` contributes suppression while Capture is effective. Provider identity and `SkillRuntime.enabled` are retained.

ACTIVE / ASSAULT / TROOP / FORMATION / TALENT are not silently added to Capture scope.

## P. ProviderDependency / Attribution

Historical `source_skill_id`, slot and `EffectSourceRef` do not create dependency by themselves.

A dependent state follows Capture-caused Provider suppression only when it carries an explicit `ProviderDependency`. Detached Passive-origin state without that dependency is not inferred.

## Q. Recovery Restriction

Capture plugs into `RecoveryExecutionPreventionPolicy`, which is consumed by the real `RecoverySystem`. Received Recovery is prevented after the existing modifier stage and resolves with no troop restoration.

## R. HEALING_BLOCK Interaction

When Capture and HEALING_BLOCK coexist, final recovery remains zero. The existing public HEALING_BLOCK reason remains canonical when it applies, while internal reason composition retains the Capture prevention key rather than deleting either cause.

## S. Friendly Target Exclusion

Capture contributes only to SKILL + ALLY + FRIENDLY_SUPPORT fresh target operations. Captured candidates are removed from the eligible pool before selection.

SELF and enemy relations are not changed by this rule.

## T. SINGLE / CHOOSE_N

New explicit friendly producer modes map `SkillDefinition -> SkillResolver -> TargetOperation` into the existing ALLY SINGLE / CHOOSE_N taxonomy.

Both production routes consume `SkillTargetPolicy`. Exclusion happens before random selection. Existing CHOOSE_N insufficient-candidate behavior remains the Shared Foundation boundary and is not replaced by `min(N, count)`.

## U. ALL_ALLIES / Delayed / Locked Boundaries

`FIXED_ALL_ALLIES` with a captured candidate returns the target-policy unsupported boundary.

`LOCK_RESOLVED` and inherited continuation keep their already-resolved target identity and do not become new queries merely because Capture appears later.

## V. Equipment ATTRIBUTE Restriction

Capture contributes an `EquipmentEffectivenessPolicy` suppression cause only for `EquipmentContributionKind.ATTRIBUTE`.

The real `AttributeSystem` gather path omits the equipment contribution while Capture is effective and the same contribution resumes after Capture expires.

Equipment identity is never removed.

## W. SABOTAGE Equipment Boundary

Sabotage keeps its broader frozen equipment scope. Capture does not inherit it.

For Capture, non-ATTRIBUTE equipment contribution categories return `UNSUPPORTED_BOUNDARY` rather than being silently suppressed. Capture and Sabotage ATTRIBUTE causes compose independently; removing Capture does not restore a contribution still suppressed by Sabotage.

## X. INSIGHT × CAPTURE

The existing Insight admission policy explicitly treats CAPTURE as non-protected. Effective Insight therefore does not reject incoming Capture.

Capture itself does not automatically suppress Insight.

## Y. Cleanse / Removal

`StateRemovalPolicy` returns `REJECT_CONTRACT_PROTECTED` for ordinary cleanse of Capture.

Specialized/scripted removal remains unsupported. Infrastructure removal operations such as natural expiry remain owned by Shared Foundation lifecycle.

## Z. Source Death

Established Capture is target-held and does not gain source-dependency semantics. Defeating the source leaves the same Capture instance resident and effective inside its normal lifetime.

## AA. Reapplication / Multi-source

Resident Capture plus incoming Capture returns `UNSUPPORTED_BOUNDARY` through `StateConflictPolicy`.

No refresh, replace, stack, extension, strongest-wins, latest-wins or multi-source arbitration was invented.

## AB. Lifetime / Restoration

Physical lifetime remains `StateLifetimeSpec + StateLifecycleSystem`.

Expiry restores future permissions/effectiveness only:

- future natural action may proceed;
- future new actor-driven damage may proceed;
- PASSIVE / COMMAND Provider future opportunities resume;
- future Recovery may resolve;
- future friendly NEW_QUERY may target the holder;
- the same equipment ATTRIBUTE contribution becomes effective again.

No missed action, Counter, Provider trigger, Recovery or target query is replayed.

## AC. RNG Governance

```text
Capture adapters = 0 RNG
Capture policy queries = 0 RNG
Capture action denial = 0 downstream NormalAttack target RNG
friendly exclusion = before selector RNG
provider suppression = before provider-owned opportunity RNG
```

The integration creates no local random source and no reroll loop.

## AD. Event Governance

Capture adapters publish no direct public events. Canonical domain owners continue to publish committed facts such as `ACTION_BLOCKED`, `RECOVERY_PREVENTED` and Counter execution facts.

No CAPTURE-specific EventBus authority was introduced.

## AE. BattleSystems Wiring

`register_capture_integration()` is called from the single `BattleSystems` composition root and registers typed contributors into the existing owners.

No second Action, Damage, Provider, Recovery, Target, Equipment or Lifecycle subsystem was added.

## AF. Production Consumer Coverage

Production tests reach:

- `BattleEngine -> ActionSystem`;
- `EffectExecutor -> DamageInstanceCoordinator -> DamageExecutionRightPort`;
- `CounterSystem -> DamageExecutionRightPort`;
- `ProviderValidityPolicy` through registered Skill Providers;
- `RecoverySystem`;
- `SkillDefinition -> SkillResolver -> TargetOperation -> SkillTargetPolicy -> TargetSystem`;
- `AttributeSystem -> EquipmentEffectivenessPolicy`;
- `StateRemovalCoordinator` and `StateLifecycleSystem`.

## AG. Tests Added

Primary executable specification:

```text
tests/test_stage12_690110_capture.py
```

Validated test delta:

```text
pre-integration = 1558 passed
validated integration = 1607 passed
net new test nodes = +49
```

Coverage includes application/effectiveness, Insight, cleanse, source death, reapplication boundary, expiry, Action/STUN, BattleEngine, Active damage, Weakness separation, Counter, DOT, free proxy, Q16, Provider scope/composition/dependency, Recovery, target producers/boundaries, equipment, Sabotage composition, RNG/event/static architecture.

## AH. Stage9 Regression

```text
PASS
included in 1607-test full suite
```

NormalAttack, Taunt, Confusion, Guard, Counter and Stage9 RNG regressions all remain green.

## AI. Stage10 Regression

```text
PASS
included in 1607-test full suite
```

## AJ. Stage11 Regression

```text
PASS
Stage11 Reopen Required = NO
```

STUN, WEAKNESS, HEALING_BLOCK and Recovery pipeline tests remain green.

## AK. 690089 Regression

```text
PASS
ordinary INSIGHT does not reject CAPTURE
```

## AL. 690101 Regression

```text
PASS
SkillPermission / ExecutionRight scopes remain separate
```

## AM. 690107 Regression

```text
PASS
ProviderValidity multi-cause composition preserved
```

## AN. 690108 Regression

```text
PASS
NEW_QUERY freshness / LOCK_RESOLVED separation preserved
```

## AO. 690222 Regression

```text
PASS
Provider suppression composition / binding invariants preserved
```

## AP. 690109 Regression

```text
PASS
Sabotage broad equipment scope remains independent from Capture ATTRIBUTE-only scope
```

## AQ. Shared Foundation Regression

```text
PASS
```

ActionSystem, ProviderValidityPolicy, ExecutionRightSpec, damage execution-right seam, RecoverySystem, SkillTargetPolicy, TargetOperation freshness, EquipmentEffectivenessPolicy, StateLifecycleSystem, StateRemovalPolicy, DependencyEvaluationSupport and existing Runtime Defaults remain green.

## AR. Static Architecture Audit

Executable static guards confirm:

- no Capture God Object;
- no Capture = STUN / WEAKNESS alias;
- no provider deletion or `SkillRuntime.enabled` mutation;
- no Capture-owned RNG;
- no direct Capture EventBus publish;
- no locked/delayed target requery;
- no hidden universal damage gate in the Capture adapter;
- no non-ATTRIBUTE equipment scope laundering.

## AS. Gameplay Changes

Gameplay added is exactly the frozen 690110 positive scope listed in sections E through Z.

No Research rule was reopened or redefined.

## AT. pytest / demo / CI

Validated code/test checkpoint:

```text
Code/test SHA
= 03c18d10fbfafa093e11f08ea779ac83c2e0d751

PR
= #26

Validated code/test CI
= 36383693483 / success / 1607 passed / demo PASS

Final PR-head CI
= 36383957010 / success / 1607 passed / demo PASS

Integration merge SHA
= 4f41906d6f0ba18ea6c09e3ca600af4f5491e2c7

Merged-main CI
= 36384025882 / success / 1607 passed in 4.74s / demo PASS
```

The same CI run executed the repository demo smoke step successfully and produced the independent-audit snapshot artifact.

## AU. Files Created / Updated

Production:
- `sgs_v2/battle_core/capture_integration.py`
- `sgs_v2/battle_core/battle_systems.py`
- `sgs_v2/battle_core/damage_instance_coordinator.py`
- `sgs_v2/battle_core/counter_system.py`
- `sgs_v2/battle_core/effect_result.py`
- `sgs_v2/battle_core/effect_executor.py`
- `sgs_v2/battle_core/skill_definition.py`
- `sgs_v2/battle_core/skill_resolver.py`
- `sgs_v2/battle_core/__init__.py`

Tests:
- `tests/test_stage12_690110_capture.py`

Governance:
- this integration record;
- Stage12 README;
- Stage12 Runtime Test Matrix;
- project status;
- canonical planning matrix;
- root README.

Research repository: unchanged.

## AV. Commit SHA

Validated code/test SHA:

```text
03c18d10fbfafa093e11f08ea779ac83c2e0d751
```

Integration merge SHA:

```text
4f41906d6f0ba18ea6c09e3ca600af4f5491e2c7
```

Merged-main CI:

```text
36384025882 / success / 1607 passed / demo PASS
```

## AW. Implementation Blockers

```text
IMPLEMENTATION_BLOCKER-690110-xxx = NONE
Research reopen = NO
Runtime governance reopen = NO
Shared Foundation reopen = NO
```

Preserved bounded questions are not blockers because the implementation can represent them explicitly without inventing behavior.

## AX. Current Gates

```text
Stage11 Runtime
= FROZEN

Stage11 Reopen Required
= NO

Stage12 Research
= 7 / 7 FROZEN

Stage12 Shared Foundation Design
= FROZEN

Stage12 Shared Foundation Implementation
= COMPLETE

690089 Runtime
= FROZEN

690101 Runtime
= FROZEN

690107 Runtime
= FROZEN

690108 Runtime
= FROZEN TO CONTRACT

690222 Runtime
= FROZEN TO CONTRACT

690109 Runtime
= FROZEN TO CONTRACT

690110 CAPTURE Research
= FROZEN

690110 CAPTURE Gameplay
= IMPLEMENTED_PENDING_RUNTIME_AUDIT

690110 CAPTURE Runtime
= NOT YET FROZEN

Stage12 Gameplay Implementation
= 7 / 7

Stage12 Runtime Frozen
= 6 / 7

Stage12 Complete
= NO

Stage13 / Stage14 / Stage15
= NO
```

## AY. NEXT

```text
690110 CAPTURE Independent Runtime Freeze Audit
```

This integration checkpoint has no authority to declare 690110 Runtime frozen or Stage12 complete.


## AZ. Post-Integration Independent Freeze Outcome — 2026-09-28

The separate independent Runtime Freeze Audit has now completed.

```text
690110 CAPTURE Research = FROZEN
690110 CAPTURE Gameplay = IMPLEMENTED
690110 CAPTURE Runtime = FROZEN TO CONTRACT
Independent Runtime Freeze Audit = PASS
Audit test commit = f1db21211ce7d01fc867bc8c26c94cb82f11af49
Independent adversarial tests = 33
Local full pytest = 1640 passed
Local demo = PASS
BLOCKER = 0
unresolved MAJOR = 0
Stage12 Gameplay Implementation = 7 / 7
Stage12 Runtime Frozen = 7 / 7
Stage12 Complete = NO
Stage13 / Stage14 / Stage15 Active = NO
NEXT = Stage12 Final Completion / Freeze Audit
```

Freeze authority: `STAGE12_690110_CAPTURE_RUNTIME_FREEZE_AUDIT.md`.

The historical Integration checkpoint above remains an integration-era record and is not retroactively rewritten into freeze authority.
