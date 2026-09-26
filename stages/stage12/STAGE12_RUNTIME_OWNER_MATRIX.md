# Stage12 Runtime Owner Matrix

> Status: **ENTRY-AUDITED / DESIGN INPUT**  
> Date: **2026-09-27**  
> Canonical constraint: one responsibility may not have two competing canonical owners.

| Responsibility | Current Owner | Stage12 Owner Decision | States | Change |
|---|---|---|---|---|
| State physical storage | StateRegistry | StateRegistry | all 7 | REUSE |
| State lifecycle mutation | StateLifecycleSystem | StateLifecycleSystem | all 7 | REUSE / EXTEND |
| Resident/effective interpretation | Stage11StateRuntime only for Stage11 | Stage12 policy/read façade, exact class name TBD by design | INSIGHT, PROVOCATION, provider suppression | NEW MINIMAL OWNER |
| State admission / immunity | Stage11-specific application policy only | Stage12 admission policy seam invoked by lifecycle | INSIGHT + protected/special boundaries | NEW MINIMAL OWNER |
| Natural action admission | ActionSystem | ActionSystem | CAPTURE | EXTEND |
| Normal attack permission | NormalAttackSystem | NormalAttackSystem | EXHAUSTION negative discriminator; Capture action interaction | REUSE |
| Skill identity / slots | SkillRuntime + SkillRuntimeRegistry | same registry + frozen SkillProviderRef(owner_id, slot, skill_id) identity | EXHAUSTION, FALSE_REPORT, INTIMIDATION, CAPTURE | REUSE / DESIGN FIXED |
| Skill category recognition | insufficient general taxonomy | SkillDefinition metadata: SkillType ACTIVE/ASSAULT/PASSIVE/COMMAND/TROOP/FORMATION + PreparationMode NONE/REQUIRED | EXHAUSTION, FALSE_REPORT, INTIMIDATION, CAPTURE | DESIGN FIXED / FUTURE SCHEMA |
| Skill permission | none canonical | Stage12 skill-permission policy | EXHAUSTION | NEW MINIMAL OWNER |
| Skill Provider validity | none canonical | Stage12 provider-validity policy | FALSE_REPORT, INTIMIDATION, CAPTURE | NEW MINIMAL OWNER |
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

- exact API names for Stage12 state admission/effectiveness policy;
- whether Skill Permission and Provider Validity share one policy object or two;
- minimal equipment-provider runtime abstraction without starting a full equipment subsystem;
- precise injection points in SkillResolver / TriggerSystem / DamageSystem / RecoverySystem;
- ProviderValidityPolicy composition and selected Intimidation binding execution semantics;
- Stage12 RuntimeParams types needed for source/binding/lifetime facts.

These are architecture decisions, not research questions.

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
