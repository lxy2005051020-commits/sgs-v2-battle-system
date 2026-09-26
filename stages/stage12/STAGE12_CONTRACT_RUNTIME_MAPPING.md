# Stage12 Contract → Runtime Mapping Skeleton

> Status: **SKELETON / ENTRY GATE OUTPUT**  
> Date: **2026-09-27**  
> Rule-level expansion is mandatory before each state's implementation begins.

| State | Contract Rule Group | Runtime Owner / Hook Candidate | Required discriminator | Mapping Status |
|---|---|---|---|---|
| INSIGHT | protected-control incoming admission | Stage12 state-admission policy → StateLifecycleSystem.apply seam | protected control rejected vs FALSE_REPORT/INTIMIDATION/CAPTURE special boundaries | DESIGN_MAPPING |
| INSIGHT | existing protected control suppression | Stage12 effective-state read/policy | resident-but-suppressed vs physically removed | DESIGN_MAPPING |
| INSIGHT | resume after Insight ends | lifecycle + effective-state policy | resume if lifetime alive vs recreate/restart | DESIGN_MAPPING |
| INSIGHT | v0.4 protected taxonomy | canonical contract data/constants | SABOTAGE protected; CAPTURE not protected | DESIGN_MAPPING |
| EXHAUSTION | ACTIVE_SKILL permission | Stage12 skill-permission policy | Active blocked vs Basic Attack allowed | DESIGN_MAPPING |
| EXHAUSTION | preparation start/interruption | minimal preparation interoperability hook | existing PREPARING interrupted; no Stage15 runtime | DESIGN_MAPPING |
| EXHAUSTION | already-activated instance | admission boundary | in-flight activated skill not rolled back | DESIGN_MAPPING |
| FALSE_REPORT | admission exceptions | Stage12 state-admission policy | ordinary Insight does not reject | DESIGN_MAPPING |
| FALSE_REPORT | PASSIVE/COMMAND Provider suppression | provider-validity policy | Provider suppressed vs Holder-only model | DESIGN_MAPPING |
| FALSE_REPORT | tested equipment specials boundary | equipment effectiveness policy | tested provider dependent effect inactive vs physical deletion | DESIGN_MAPPING |
| FALSE_REPORT | restoration | provider-validity + lifecycle | future behavior resumes; no missed-trigger replay | DESIGN_MAPPING |
| PROVOCATION | eligible skill target operation/query | SkillResolver target policy seam | operation-level forcing vs blanket target overwrite | DESIGN_MAPPING |
| PROVOCATION | Source admissibility | target policy + state effective query | live/admissible source vs dead source | DESIGN_MAPPING |
| PROVOCATION | Resident != Effective | Stage12 effective-state policy | source death leaves state resident | DESIGN_MAPPING |
| PROVOCATION | Taunt/Confusion boundaries | existing NormalAttack/target arbitration + Stage12 skill target policy | Confusion pre-emption; Provocation does not own Normal Attack | DESIGN_MAPPING |
| INTIMIDATION | single selected Provider binding | provider-validity policy + Stage12 params | one provider disabled vs all skills disabled | DESIGN_MAPPING |
| INTIMIDATION | refresh reroll | provider-validity policy + RandomSystem | release old → exactly one reroll → no multi-disable stack | DESIGN_MAPPING |
| INTIMIDATION | resume preserves binding | provider-validity + lifecycle | resume does not reroll; lifetime continues | DESIGN_MAPPING |
| INTIMIDATION | source-skill counter separation | source-skill boundary ledger | no counter/damage branch inside state core | DESIGN_MAPPING |
| SABOTAGE | equipment effectiveness suppression | equipment-effectiveness policy | suppressed contribution vs physical unequip/delete | DESIGN_MAPPING |
| SABOTAGE | existing effects/remote ownership | provider/equipment validity seam | tested dependent effect ineffective vs universal deletion | DESIGN_MAPPING |
| SABOTAGE | restoration | equipment policy + lifecycle | resume vs full reinitialize / replay | DESIGN_MAPPING |
| CAPTURE | natural action denial | ActionSystem | action denied independently of skill permission | DESIGN_MAPPING |
| CAPTURE | actor-driven new damage denial | DamageSystem admission seam | counterattack no damage vs attached Active-origin DOT continues | DESIGN_MAPPING |
| CAPTURE | PASSIVE/COMMAND invalidation | provider-validity policy | provider behavior suspended vs historical effect deletion | DESIGN_MAPPING |
| CAPTURE | recovery to zero | RecoverySystem | Capture recovery denial vs HealingBlock regression/order | DESIGN_MAPPING |
| CAPTURE | friendly target exclusion | SkillResolver target eligibility policy | friendly selector excludes captured holder | DESIGN_MAPPING |
| CAPTURE | restoration | composed owners + lifecycle | RESUME / future-only; no replay | DESIGN_MAPPING |
| CAPTURE | source death independence | lifecycle | applied Capture remains after source death | DESIGN_MAPPING |

## Completion rule

A row may move from `DESIGN_MAPPING` to `GREEN` only after:

```text
contract rule identified
→ canonical owner fixed
→ concrete method/hook named
→ positive test
→ negative test
→ discriminating test
→ required cross-state test
→ regression green
```

Bounded unknowns that require an engineering choice must be linked to `STAGE12_RUNTIME_DEFAULT_LEDGER.md` and labelled `PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN`.

## SF-0 mapping qualification — 2026-09-27

This remains a skeleton. [Reconnaissance](STAGE12_SHARED_FOUNDATION_ARCHITECTURE_RECONNAISSANCE.md)
section 2 maps all seven current contracts to rule groups; the method-level completed design is future work.
INSIGHT existing-control suppression must include the AR-SF-01 legacy CONFUSION discriminator.
Provider validity must cover RecoveryOpportunitySystem's existing gate, not TriggerSystem alone.
Capture equipment attributes, ordinary-cleanse resistance, actor/proxy provenance, and queued-work
boundaries are tracked in DQ-SF-11/19/23/25 and must not disappear from the completed mapping.


## SF Round 2 frozen design bindings — 2026-09-27

These rows are DESIGN_FROZEN_FOUNDATION, not GREEN. GREEN still requires implementation and tests.

| Foundation item | Authority | Frozen design binding | Implementation status |
|---|---|---|---|
| Insight × existing Confusion | STAGE12_INSIGHT_CONFUSION_AUTHORITY_MIGRATION.md + Insight v0.4 §§3/4/7/8/21/22 | resident Confusion becomes ineffective under effective Insight; timer continues; surviving instance resumes; old P0-CFS-P93-01 claim narrowly superseded | NOT IMPLEMENTED |
| Skill taxonomy | DQ-SF-04 | SkillType ACTIVE/ASSAULT/PASSIVE/COMMAND/TROOP/FORMATION; PreparationMode orthogonal; Normal Attack non-skill operation; equipment special separate ProviderCategory | NOT IMPLEMENTED |
| Skill Provider identity | DQ-SF-05 | SkillProviderRef(owner_id, slot, skill_id); Registry resolves owner+slot and validates expected skill ID | NOT IMPLEMENTED |
| Equipment Provider identity | DQ-SF-05 / DQ-SF-11 boundary | EquipmentProviderRef(owner_id, provider_key) enters typed ProviderRef union without masquerading as Skill | DESIGN ONLY |
| Provider enumeration | RD-SF-002 | deterministic slot order 0/1/2 for identity enumeration; no implied Intimidation weighting | NOT IMPLEMENTED |
| Legacy SkillDefinition classification | RD-SF-001 | compatibility default ACTIVE + PreparationMode.NONE; new Stage12 definitions explicit | NOT IMPLEMENTED |
| Recovery source gate migration | DQ-SF-21 | slot 0 checked by is-not-None semantics; expected skill mismatch and missing ref explicit; current validity delegated later to DQ-SF-08 | NOT IMPLEMENTED |
| Intimidation × Insight provenance | AR-SF-02 / DQ-SF-28 | use Intimidation §§5/11 as positive outcome authority; preserve Insight DIRECT_OVERLAP_UNOBSERVED evidence label | DESIGN AUTHORITY CLOSED |

Future mapping work must not move these rows to GREEN until code and discriminating tests exist.


## SF Round 3 frozen design bindings — effectiveness / Provider validity

These bindings are `DESIGN_FROZEN_FOUNDATION`, not GREEN.

| State / concern | Resident model | Effective dependency | Provider dependency | Suppression / authority target | Concrete shared hook |
|---|---|---|---|---|---|
| INSIGHT | physical StateInstance remains in Registry until Lifecycle removes it | suppressed if an explicit live Provider dependency is non-valid; otherwise effective subject to local lifecycle facts | explicit `ProviderDependency` only when the Insight contract/source requires live provider validity | protected-control StateEffectiveness decisions | `StateEffectivenessPolicy.evaluate_state` → protected-control rule |
| EXHAUSTION | resident timed control | effective unless independently suppressed/inactive; Insight can suppress existing Exhaustion | none inferred from source provenance | ACTIVE skill admission authority | shared state decision consumed later by SkillPermissionPolicy |
| FALSE_REPORT | resident control | own effectiveness is shared-state truth; ordinary Insight does not suppress it | none inferred globally | PASSIVE/COMMAND Provider validity; tested equipment boundary remains DQ-SF-11 | `ProviderValidityPolicy.evaluate_provider` |
| PROVOCATION | resident even when it cannot currently force a legal Source | shared policy may expose SOURCE_INADMISSIBLE/local inactivity; fine-grained operation admissibility remains DQ-SF-09 | none inferred globally | eligible skill target-operation authority only | state decision + future target policy |
| INTIMIDATION | resident control with stable selected ProviderRef binding | if Intimidation itself is ineffective, binding is preserved and produces no suppression | binding targets exactly one ProviderRef; any live dependency of Intimidation itself must be explicit | exactly selected Provider | state decision → ProviderValidityPolicy cause |
| SABOTAGE | resident protected control | Insight may suppress existing Sabotage under frozen protected-control rules | equipment linkage is explicit, not EffectSourceRef inference | tested equipment contributions/effects | StateEffectivenessPolicy; DQ-SF-11 equipment policy remains open |
| CAPTURE | resident control; source death does not remove established Capture | own current effectiveness from shared policy; ordinary Insight does not suppress Capture | none inferred from source survival | verified PASSIVE/COMMAND Providers; other composite restrictions remain domain-owned | ProviderValidityPolicy + later DQ-SF-19 consumers |

### Shared method-level migration map

| Existing method / consumer | Round 3 migration binding |
|---|---|
| Stage9StateRuntime.has_operational_insight | delegate to `StateEffectivenessPolicy.has_effective(owner, INSIGHT)` |
| Stage9StateRuntime.get_operational_confusion | resident read stays local; return only instance whose shared decision is EFFECTIVE |
| Stage9StateRuntime.get_taunt_suppressors | obtain effective Insight/shared suppression causes from StateEffectivenessPolicy; no `Registry.has(INSIGHT)` authority |
| Stage9StateRuntime.get_taunt_lifecycle_state / is_taunt_operational | shared state decision first; target/source domain checks remain Stage9 |
| Stage11StateRuntime.is_effective | thin delegate to StateEffectivenessPolicy |
| Stage11StateRuntime.effective_instances / has_effective | derive from delegated shared decisions |
| Stage11 remaining-use/source-dependent checks | migrate as local rule adapters consumed by StateEffectivenessPolicy; do not remain a second canonical truth |
| RecoveryOpportunitySystem JIT source skill gate | future DQ-SF-21 implementation resolves SkillProviderRef then delegates current validity to ProviderValidityPolicy before RNG |

No row is GREEN until production code and discriminating tests exist.
