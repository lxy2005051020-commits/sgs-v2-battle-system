# Stage12 SkillType Taxonomy & Provider Identity Design

Date: 2026-09-27
Round: STAGE12_SF_ROUND2_AUTHORITY_AND_IDENTITY_DESIGN
Status: SHARED FOUNDATION DESIGN DECISION
Runtime implementation in this round: NONE

This document closes DQ-SF-04 and DQ-SF-05 for Shared Foundation design use. It fixes the minimum classification and stable identity model needed by Stage12. It does not implement Active execution, Assault execution, preparation scheduling, ProviderValidityPolicy, Intimidation selection, or any Stage13+ gameplay system.

## 1. Evidence and existing architecture

Existing Battle facts:

- SkillDefinition currently has no SkillType field and explicitly states that classification was deferred.
- SkillSlot is an IntEnum with INHERENT = 0, LEARNED_1 = 1, LEARNED_2 = 2.
- SkillRuntimeRegistry authoritative key is (owner_id, SkillSlot).
- SkillRuntimeRegistry.lookup validates expected_skill_id when supplied.
- Registry entries survive source-unit defeat; defeat is not equivalent to provider disappearance.
- EffectSourceRef carries attribution fields source_unit_id, source_skill_id and source_skill_slot.
- RecoveryOpportunitySystem currently performs a JIT source-skill enabled check and uses source_skill_slot in a truthiness condition, so INHERENT == 0 can bypass the gate.
- Current SkillResolver behavior is an Active-skill-shaped legacy path and emits ACTIVE_SKILL provenance.

Contract requirements used:

- EXHAUSTION blocks ACTIVE admission, interrupts preparing Active skills, and does not itself block Assault, Passive, Command, or Basic Attack.
- FALSE_REPORT suppresses PASSIVE and COMMAND Provider behavior; tested Equipment Specials are a separate observable category and are not proven to be Passive or Command internally.
- INTIMIDATION eligible skill domain includes Active, Preparation Active, Assault, Passive, Command, Troop; Formation is excluded; Normal Attack is outside the target domain.
- CAPTURE requires Passive and Command live Provider invalidation among its composite restrictions.

## 2. DQ-SF-04 final taxonomy

The minimum Shared Foundation taxonomy is:

- SkillType.ACTIVE
- SkillType.ASSAULT
- SkillType.PASSIVE
- SkillType.COMMAND
- SkillType.TROOP
- SkillType.FORMATION

Preparation is an orthogonal characteristic:

- PreparationMode.NONE
- PreparationMode.REQUIRED

Provider category is separate from skill type:

- ProviderCategory.SKILL
- ProviderCategory.EQUIPMENT_SPECIAL

Normal Attack remains an operation owned by the Normal Attack runtime. It is not a SkillType.

### Formal classification table

| Concept | Category | Representation | Stage12 Consumer | Why |
|---|---|---|---|---|
| ACTIVE | SkillType | SkillType.ACTIVE + PreparationMode.NONE | EXHAUSTION, INTIMIDATION | Active admission is a distinct permission domain |
| PREPARATION_ACTIVE | Skill characteristic, not independent SkillType | SkillType.ACTIVE + PreparationMode.REQUIRED | EXHAUSTION, INTIMIDATION, preparation interruption port | Preparation changes lifecycle/interruption, not the core skill family |
| ASSAULT | SkillType | SkillType.ASSAULT | EXHAUSTION negative case, INTIMIDATION | Remains eligible under Exhaustion but can be selected by Intimidation |
| PASSIVE | SkillType | SkillType.PASSIVE | FALSE_REPORT, INTIMIDATION, CAPTURE | Provider effectiveness is required independently of action permission |
| COMMAND | SkillType | SkillType.COMMAND | FALSE_REPORT, INTIMIDATION, CAPTURE | Same Provider-effectiveness requirement with separate contract semantics |
| TROOP | SkillType | SkillType.TROOP | INTIMIDATION | Positively eligible for Intimidation; not collapsed into Passive/Command |
| FORMATION | SkillType | SkillType.FORMATION | INTIMIDATION exclusion, FalseReport negative boundary | Must be identifiable to exclude without pretending it is a non-skill operation |
| NORMAL_ATTACK | OperationType / non-skill operation | Normal Attack runtime, not SkillType | EXHAUSTION negative case, INTIMIDATION exclusion | Existing canonical owner is NormalAttackSystem; contracts treat it separately |
| EQUIPMENT_SPECIAL | Provider category / non-skill contribution source | ProviderCategory.EQUIPMENT_SPECIAL | FALSE_REPORT tested boundary, SABOTAGE future equipment policy | Research explicitly does not prove equipment specials are Passive/Command skills |

### Preparation rule

Stage12 treats Preparation Active as ACTIVE plus PreparationMode.REQUIRED.

This permits:

- EXHAUSTION to ask one Active permission question.
- the preparation interoperability port to interrupt PREPARING work.
- INTIMIDATION to select the same Skill Provider identity whether the Active is currently preparing or not.

No Preparation scheduler is introduced here.

### Legacy SkillDefinition compatibility

When the schema scaffold is eventually added, pre-Stage12 SkillDefinition construction must preserve existing behavior through the explicit project runtime default RD-SF-001:

- legacy skill_type = ACTIVE
- legacy preparation_mode = NONE

New Stage12-authored definitions should specify classification explicitly instead of relying on the compatibility default.

This is an engineering compatibility choice, not Research evidence about the original game.

## 3. DQ-SF-05 final Provider Identity model

Provider Identity, Provider Category, and Provider Current Validity are three different concepts.

### SkillProviderRef

Minimum semantic fields:

- owner_id: stable unit identity
- skill_slot: SkillSlot
- skill_id: expected immutable skill definition identity

Canonical identity tuple:

(owner_id, skill_slot, skill_id)

Resolution rule:

1. Look up SkillRuntimeRegistry by (owner_id, skill_slot).
2. If no runtime exists: MISSING.
3. If a runtime exists but runtime.definition.skill_id != skill_id: IDENTITY_MISMATCH.
4. Otherwise identity resolution succeeds and returns that exact runtime.
5. A mismatch must never silently rebind the reference to the new skill.

Consequences:

- A.SkillSlot1.SkillX != B.SkillSlot1.SkillX.
- A.Inherent.SkillX != A.Learned1.SkillX.
- A.Inherent.SkillX is valid even though the numeric slot value is 0.
- Replacing slot contents does not mutate an old reference into a reference to the replacement skill.

### EquipmentProviderRef

Equipment is not forced into SkillProviderRef.

Stage12 adopts a typed shared abstraction:

ProviderRef = SkillProviderRef | EquipmentProviderRef

Minimum EquipmentProviderRef fields for Shared Foundation design:

- owner_id
- provider_key

provider_key must be stable, serializable, deterministic, and unique for an equipment contribution within its owner. DQ-SF-11 owns the eventual equipment subsystem and may refine how the key is derived from an equipment slot or contribution record.

This avoids an optional-field mega-structure and avoids pretending that SABOTAGE targets a Skill.

## 4. Identity resolution is not Provider validity

Identity-layer outcomes are:

- RESOLVED
- MISSING
- IDENTITY_MISMATCH

The following are NOT identity failures:

- runtime.enabled == false
- Provider temporarily suppressed by FalseReport, Intimidation, Capture, or another reason
- Provider owner defeated
- source dependency currently ineffective
- Provider contribution suspended while its object remains resident

Those belong to DQ-SF-08 ProviderValidityPolicy and contract-specific lifecycle rules.

In particular, SkillRuntimeRegistry explicitly preserves entries across source-unit defeat, so owner defeat cannot be redefined as “missing Provider” at the identity layer.

## 5. EffectSourceRef boundary

EffectSourceRef remains attribution/provenance.

Attribution != live Provider dependency.

The presence of source_skill_id or source_skill_slot proves where an effect came from. It does not prove that the effect must disappear whenever that skill becomes invalid.

A live dependency must be explicit in the effect/state/opportunity contract or runtime metadata.

Future conversion from EffectSourceRef to SkillProviderRef is permitted only when:

- source_unit_id exists,
- source_skill_slot is not None,
- source_skill_id exists,
- and the consumer has explicit live-provider-dependency semantics.

No consumer may infer live dependency solely from attribution fields.

## 6. Loaded Provider enumeration

SkillRuntimeRegistry is the canonical source of loaded Skill Providers.

A future public enumeration method must return stable SkillProviderRef values, not Python object identity.

Owner-local enumeration order is the project runtime default RD-SF-002:

1. ascending numeric SkillSlot: INHERENT 0, LEARNED_1 1, LEARNED_2 2;
2. skill_id only as a deterministic consistency tiebreaker.

Duplicate owner/slot registration remains illegal.

Whole-battle enumeration, if ever required, must additionally sort owner_id before slot.

The enumeration API returns loaded identity. It does not itself filter Provider validity and does not define random-selection weights.

### INTIMIDATION consumer boundary

For an Intimidation holder, future selection design will:

loaded Skill Providers for holder
→ classify by SkillType
→ include ACTIVE, ASSAULT, PASSIVE, COMMAND, TROOP
→ ACTIVE includes both PreparationMode.NONE and REQUIRED
→ exclude FORMATION
→ exclude NORMAL_ATTACK because it is not a Skill Provider
→ do not include EQUIPMENT_SPECIAL unless future Research closes BU-07

Selection weighting is still unproven. RD-SF-002 does not mean uniform random and does not authorize a 1/N research claim.

Empty eligible-pool behavior is not selected in Round 2. That decision belongs to later binding/admission design and must enter the Runtime Default Ledger if implementation requires a choice without Research authority.

## 7. Slot-0 migration obligation

Current RecoveryOpportunitySystem contains a real hazard because it checks source_skill_slot by truthiness.

SkillSlot.INHERENT == 0 is a valid identity and MUST be treated exactly like other slots.

Future implementation obligation:

- replace truthiness tests with explicit is not None semantics;
- resolve through SkillProviderRef / SkillRuntimeRegistry with expected_skill_id validation;
- distinguish MISSING from IDENTITY_MISMATCH;
- then delegate current effectiveness to ProviderValidityPolicy;
- do not consume the recovery RNG draw when the applicable Provider-validity gate rejects execution.

Required future tests:

- inherent slot 0 disabled/suppressed is gated exactly like slot 1/2;
- expected skill ID mismatch is explicit and never rebinds;
- missing slot is explicit;
- temporarily suppressed Provider is not treated as physically missing;
- source defeat is not automatically identity-missing;
- no recovery RNG draw occurs after Provider-validity rejection.

No code fix is made in Round 2.

## 8. Serialization and replay

Provider refs must serialize only stable semantic values.

Forbidden identity sources:

- id(obj)
- memory address
- process-local pointer identity
- hash values whose stability depends on Python process randomization

SkillProviderRef serialization contains owner_id, skill_slot numeric/name representation, and skill_id.
EquipmentProviderRef serialization contains owner_id and provider_key.

Deserialization must reproduce the same semantic identity and must re-resolve against current battle registries.

## 9. Owner decisions

- SkillDefinition owns static SkillType and PreparationMode metadata.
- SkillRuntimeRegistry owns loaded Skill Provider registration, identity resolution, and deterministic enumeration.
- ProviderValidityPolicy, designed in DQ-SF-08, owns current effectiveness of a resolved Provider.
- EffectSourceRef remains attribution.
- Equipment identity enters the shared ProviderRef union without masquerading as a Skill.
- Intimidation binding stores ProviderRef, not SkillRuntime object identity.

## 10. Explicit non-goals

Round 2 does not implement:

- Active execution runtime.
- Assault execution runtime.
- Preparation scheduler or preparation resolution engine.
- SkillPermissionPolicy.
- ProviderValidityPolicy.
- Intimidation binding RNG or weighting.
- Equipment effectiveness runtime.
- Recovery slot-0 code repair.
- Stage13/14/15 gameplay.

## 11. Closure

DQ-SF-04 = CLOSED_BY_SHARED_FOUNDATION_DESIGN.
DQ-SF-05 = CLOSED_BY_SHARED_FOUNDATION_DESIGN.
DQ-SF-21 remains DESIGN_REQUIRED for implementation migration, but its identity and slot-0 obligations are now formally mapped.

Shared Foundation Design Freeze = NOT YET.
Stage12 Runtime Frozen = 0 / 7.
Stage13 Active = NO.
