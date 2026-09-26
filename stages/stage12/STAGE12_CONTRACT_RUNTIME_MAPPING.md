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
