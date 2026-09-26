# Stage12 Runtime Owner Matrix

> Status: **ENTRY-AUDITED / DESIGN INPUT**  
> Date: **2026-09-27**  
> Canonical constraint: one responsibility may not have two competing canonical owners.

| Responsibility | Current Owner | Stage12 Owner Decision | States | Change |
|---|---|---|---|---|
| State physical storage | StateRegistry | StateRegistry | all 7 | REUSE |
| State lifecycle mutation | StateLifecycleSystem | StateLifecycleSystem | all 7 | REUSE / EXTEND |
| State physical lifetime clock | mixed Stage10/11 mechanisms | `StateLifecycleSystem` with explicit clock domains / typed Stage12 lifetime metadata | all 7 | DESIGN FIXED / FUTURE EXTEND |
| Resident/effective interpretation | Stage9/Stage11 local readers | `StateEffectivenessPolicy` | all resident states requiring current authority | NEW CANONICAL SHARED OWNER; Stage9/11 DELEGATE |
| State admission / immunity | Stage11-specific application policy only | `StateAdmissionPolicy` pure decision owner, invoked before state conflict | INSIGHT + protected/special boundaries | NEW CANONICAL SHARED OWNER |
| State conflict / reapplication | mixed rules inside Lifecycle/application modules | `StateConflictPolicy` pure per-contract decision owner | all 7 | NEW CANONICAL SHARED OWNER |
| State application transaction orchestration | implicit inside Lifecycle.apply | `StateApplicationCoordinator` prepares immutable transaction; `StateLifecycleSystem` alone commits | all 7 | NEW NON-WRITING COORDINATOR |
| State removal / cleanse eligibility | no shared canonical owner | `StateRemovalPolicy` pure gameplay-removal eligibility owner; Lifecycle keeps physical remove primitive | all 7 | NEW CANONICAL SHARED OWNER |
| Natural action admission | ActionSystem | ActionSystem | CAPTURE | EXTEND |
| Normal attack permission | NormalAttackSystem | NormalAttackSystem | EXHAUSTION negative discriminator; Capture action interaction | REUSE |
| Skill identity / slots | SkillRuntime + SkillRuntimeRegistry | same registry + frozen SkillProviderRef(owner_id, slot, skill_id) identity | EXHAUSTION, FALSE_REPORT, INTIMIDATION, CAPTURE | REUSE / DESIGN FIXED |
| Skill category recognition | insufficient general taxonomy | SkillDefinition metadata: SkillType ACTIVE/ASSAULT/PASSIVE/COMMAND/TROOP/FORMATION + PreparationMode NONE/REQUIRED | EXHAUSTION, FALSE_REPORT, INTIMIDATION, CAPTURE | DESIGN FIXED / FUTURE SCHEMA |
| Skill permission | none canonical | SkillPermissionPolicy, holder-level permission only | EXHAUSTION | NEW CANONICAL MINIMAL OWNER; DESIGN FIXED |
| Skill operation admission composition | SkillResolver local enabled gate | SkillOperationAdmissionCoordinator composes ProviderValidityPolicy + SkillPermissionPolicy before observable activation/RNG | EXHAUSTION + all skill Providers | NEW THIN COORDINATOR; DESIGN FIXED |\n| Preparation interruption request | none | PreparationInterruptionPort implemented later by the true preparation owner | EXHAUSTION, INTIMIDATION | NEW MINIMAL PORT; DESIGN FIXED / IMPLEMENTATION DEPENDENCY |\n| Skill Provider validity | none canonical | `ProviderValidityPolicy` after ProviderRef identity resolution | FALSE_REPORT, INTIMIDATION, CAPTURE; explicit provider-dependent effects | NEW CANONICAL SHARED OWNER |
| Skill target candidate construction | SkillResolver + TargetSystem | same + Stage12 eligibility/forcing policy seam | PROVOCATION, CAPTURE | EXTEND |
| Normal Attack target arbitration | TargetResolutionSystem | TargetResolutionSystem | TAUNT/CONFUSION regression, Provocation non-domain | REUSE |
| Damage permission | DamageSystem / existing prevention seams | canonical damage admission seam in DamageSystem stack | CAPTURE | EXTEND |
| Recovery | RecoverySystem | RecoverySystem | CAPTURE | EXTEND |
| Equipment effectiveness | no canonical production owner | minimal equipment-effectiveness query policy | SABOTAGE (+ tested FalseReport equipment boundary) | NEW MINIMAL OWNER |
| Trigger collection | TriggerSystem | TriggerSystem querying provider/equipment policy | FALSE_REPORT, SABOTAGE, CAPTURE | EXTEND |
| RNG | BattleContext.random / RandomSystem | same | PROVOCATION, INTIMIDATION, any randomized application/selection | REUSE |
| Event facts | domain owner → EventBus | same | all 7 | REUSE |
| Composition / wiring | BattleSystems | BattleSystems | shared foundation | EXTEND WIRING |

## Owner rules

1. `StateRegistry` remains storage. It must not become the policy engine.
2. `StateLifecycleSystem` remains the sole physical state mutation owner.
3. Existing Stage11 owners are not duplicated merely because Stage12 also needs a similar question.
4. A new Stage12 owner is allowed only where the Entry Audit identifies a genuine gap.
5. Skill Permission and Provider Validity are distinct semantic questions even if the final design composes them in one small policy object.
6. Target policy must keep Normal Attack arbitration separate from skill target operations.
7. Equipment suppression means effectiveness query, not physical unequip/delete/recreate.
8. EventBus records facts and never decides permission.
9. All randomized decisions consume `BattleContext.random`, with explicit consume/no-consume tests.

## Design-open items

The following remain open after Round 4:

- DQ-SF-06 CLOSED in Round 5: SkillPermissionPolicy + pre-RNG SkillOperationAdmissionCoordinator;
- DQ-SF-07 preparation interruption port;
- DQ-SF-09 / 10 target-operation policy and query granularity;
- DQ-SF-11 minimal equipment-effectiveness runtime abstraction;
- DQ-SF-12 final RNG signatures / ordering outside the Round 4 candidate and refresh boundaries;
- DQ-SF-13 public event model;
- DQ-SF-17 composition-root wiring;
- DQ-SF-19 Capture composite execution;
- DQ-SF-21 CLOSED_BY_SHARED_FOUNDATION_DESIGN in Round 5: RecoveryOpportunitySystem Gate 4 migration contract frozen; implementation remains pending;
- DQ-SF-23 queued / in-flight semantics;
- DQ-SF-26 independent Shared Foundation design audit.

Admission, effectiveness, Provider validity, lifecycle transaction, clock and removal-policy owner names are no longer open architecture questions.

These remaining items are architecture decisions, not new Research questions unless a named contract boundary is explicitly reopened.

## SF-0 owner qualification — 2026-09-27

Status remains DESIGN INPUT, not COMPLETE or FROZEN.
The [current capability inventory and gap ledger](STAGE12_SHARED_FOUNDATION_ARCHITECTURE_RECONNAISSANCE.md)
adds omitted owners: Stage9StateRuntime (Taunt/Insight effective read),
RecoveryOpportunitySystem (existing JIT source-skill gate), AttributeSystem and modifier-provider
seams. Stage11ApplicationPolicy is a module of conflict/ingress functions, not a general immunity class.
Shared effectiveness must migrate/delegate existing Stage9 and Stage11 readers, not duplicate them.
AR-SF-01 legacy Confusion semantics requires authority disposition first.
The [28-question ledger](STAGE12_SHARED_FOUNDATION_DESIGN_QUESTION_LEDGER.md) precedes method-level owner freeze.


## SF Round 2 owner decisions — 2026-09-27

Authority records:
- STAGE12_INSIGHT_CONFUSION_AUTHORITY_MIGRATION.md
- STAGE12_SKILLTYPE_PROVIDER_IDENTITY_DESIGN.md
- STAGE12_RUNTIME_DEFAULT_LEDGER.md

Fixed for downstream Shared Foundation design:

1. SkillDefinition owns static SkillType and PreparationMode metadata.
2. PREPARATION_ACTIVE is represented as ACTIVE + PreparationMode.REQUIRED, not as an independent SkillType.
3. NORMAL_ATTACK remains an operation owned by NormalAttackSystem and is not a SkillType.
4. Equipment specials are a separate ProviderCategory and are not coerced into SkillType.
5. SkillRuntimeRegistry owns loaded skill identity resolution and deterministic enumeration.
6. SkillProviderRef identity is (owner_id, SkillSlot, skill_id); slot 0 is fully valid.
7. EffectSourceRef remains attribution and cannot implicitly create a live Provider dependency.
8. Provider current validity remains a separate DQ-SF-08 owner; disabled/suppressed does not mean identity missing.
9. Intimidation binding will store ProviderRef rather than Python object identity.
10. RecoveryOpportunitySystem slot-0 truthiness is a formal migration obligation, not repaired in this design round.

No gameplay implementation is authorized by these owner decisions.


## SF Round 3 owner decisions — 2026-09-27

Authority record:
- STAGE12_STATE_EFFECTIVENESS_PROVIDER_VALIDITY_DESIGN.md

Canonical owner split:

| Responsibility | Canonical owner | Non-owner collaborators |
|---|---|---|
| physical state residency | StateRegistry | policies may read only |
| physical state mutation / expiry | StateLifecycleSystem | transition coordinator observes before/after decisions |
| current state gameplay authority | StateEffectivenessPolicy | Stage9StateRuntime / Stage11StateRuntime delegate |
| Provider identity resolution | SkillRuntimeRegistry and future typed equipment resolver | ProviderValidityPolicy consumes resolved identity facts |
| current Provider validity | ProviderValidityPolicy | state policy may depend on its decision |
| dependency propagation / transition awareness | EffectivenessTransitionCoordinator | policies remain the decision owners |
| domain arbitration | existing Stage9/11/12 domain systems | consume effective/valid decisions |
| observable event publication | deciding domain owner → EventBus | coordinator may surface internal transition facts but EventBus never decides |

Owner invariants:

- StateEffectivenessPolicy and ProviderValidityPolicy remain separate because StateInstance identity and ProviderRef identity are different domains.
- EffectivenessTransitionCoordinator is deliberately not a God object. It owns neither Registry/Lifecycle nor Action/Damage/Recovery/Target/RNG.
- Shared policies never mutate `SkillRuntime.enabled` or state runtime params to represent transient suppression.
- Explicit Intimidation ProviderRef binding remains state-owned gameplay data; it is not a mutable suppression ledger.
- Equipment Provider identity can enter ProviderRef, but DQ-SF-11 still owns the equipment-effectiveness semantics and adapter.

No gameplay implementation is authorized by these owner decisions.

## SF Round 4 owner decisions — 2026-09-27

Authority record:
- STAGE12_STATE_LIFECYCLE_TRANSACTION_DESIGN.md

Canonical Round 4 split:

| Responsibility | Canonical owner | Non-owner collaborators |
|---|---|---|
| incoming state admission | StateAdmissionPolicy | source operation creates candidate first; conflict policy runs only after ALLOW |
| same-state / reapplication conflict | StateConflictPolicy | per-state contract adapters; Lifecycle does not invent generic stacking |
| application transaction preparation | StateApplicationCoordinator | pure policies, Provider selection/binding preparation, transition coordinator |
| physical create/refresh/replace/remove | StateLifecycleSystem | Registry remains storage only |
| physical state lifetime clock | StateLifecycleSystem | domain-specific helpers/counters remain separate |
| gameplay removal eligibility | StateRemovalPolicy | cleanse/source operation supplies typed RemovalOperation |
| effectiveness after commit | StateEffectivenessPolicy | EffectivenessTransitionCoordinator re-evaluates affected closure |
| Provider validity after commit | ProviderValidityPolicy | same transition closure |
| same-envelope project ordering | RD-SF-003 | Lifecycle snapshots due removals before transition recomputation |

Round 4 invariants:

- decision first, mutation second;
- a rejected admission/removal request changes nothing physical;
- REFRESH = same physical instance + new application generation;
- REPLACE = old physical instance terminates + new physical instance begins;
- resume is not refresh;
- suppression does not pause physical lifetime;
- Stage12 clock metadata must not accidentally opt into Stage10 persistence;
- ordinary cleanse policy is distinct from expiry/defeat/teardown infrastructure;
- no global source-death cleanup rule exists.

No gameplay implementation is authorized by these owner decisions.


## SF Round 5 owner closure

| Responsibility | Canonical owner | Non-owner collaborators | Frozen boundary |
|---|---|---|---|
| holder-level skill permission | SkillPermissionPolicy | StateEffectivenessPolicy supplies effective Exhaustion fact | no Provider validity, RNG, targeting or execution |
| new skill operation admission composition | SkillOperationAdmissionCoordinator | ProviderValidityPolicy + SkillPermissionPolicy | pure/pre-RNG decision seam only |
| Provider current validity | ProviderValidityPolicy | SkillRuntimeRegistry resolves identity | unchanged from Round 3 |
| preparation progress/storage | future Stage15 preparation owner | PreparationInterruptionPort exposes only interruption command | Stage12 never stores progress |
| preparation interruption transition dispatch | EffectivenessTransitionCoordinator | StateEffectivenessPolicy / ProviderValidityPolicy transition facts + PreparationInterruptionPort | synchronous, non-authoritative |
| recovery JIT source gate | RecoveryOpportunitySystem remains opportunity owner; validity delegated to ProviderValidityPolicy | typed SkillProviderRef construction | rejection before probability RNG |

Owner invariants:

- SkillPermissionPolicy and ProviderValidityPolicy remain separate truth domains.
- SkillOperationAdmissionCoordinator may aggregate blockers, but it may not invent a second permission/validity truth.
- Provider resume means only future behavior may become eligible; it never auto-activates a skill or resumes old preparation.
- EventBus records committed/decided facts and does not decide interruption.
