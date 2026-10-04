# Stage14 · Concrete Skill Integration

> Status: **PILOT PREPARATION ACTIVE / MAINLINE MERGE GATED**

Stage14 begins concrete skill integration after the reusable game-mechanism foundation work.

## Research foundation

Canonical Research authority:

- [MC-STAGE14-TROOP-FOUNDATION-01](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/main/Stage14_Troop_Skill_Research/00_Governance/TROOP_SKILL_IDENTITY_AND_PROVIDER_LIFECYCLE_CONTRACT.md)
- [Troop question ledger](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/main/Stage14_Troop_Skill_Research/00_Governance/TROOP_SKILL_QUESTION_LEDGER.md)

Frozen shared rules:

```text
special troop conversion = PRE_BATTLE
special troop restraint  = inherit base troop family
PRE_BATTLE visibility    = later skills read prior applied mutations
provider                 = holder-bound skill instance
temporary invalidation   != provider death
```

## Pilot policy

One skill at a time.

A pilot may be researched and implemented on an isolated branch before Stage13 exit, but **must not merge into main** unless:

```text
Stage13 exit gate                         = PASS
selected skill mechanism contract         = CLOSED/FROZEN
runtime seam mapping                      = REVIEWED
skill-specific regression tests           = PASS
full regression / demo / independent audit = PASS
```

Bulk TROOP integration is forbidden until the relevant family contracts are closed.

## First pilot candidate

### 西凉铁骑

Recommended because it is a small vertical slice through:

```text
SkillType.TROOP
-> PRE_BATTLE special troop conversion
-> team-wide temporary crit modifier/state
-> provider identity / invalidation lifecycle
-> duration expiry
```

It intentionally avoids the unresolved storage/battery families represented by 象兵、飞熊军、丹阳兵.

### Do not hard-code from historical guides

Before implementation, Research must freeze the current-version 西凉铁骑 contract, including:

- exact current client text and version boundary;
- full-level crit rate;
- first-three-round duration semantics;
- 马腾统领 speed scaling, if present in the target version;
- stacking with other crit sources;
- snapshot vs JIT for any speed-dependent scaling;
- provider invalidation/death behavior as inherited from the shared foundation;
- whether the special troop identity and the crit rule are represented as separate Runtime concerns.

## Runtime rule

Battle code is not evidence.

The integration sequence is:

```text
GAME TRUTH
-> SKILL CONTRACT
-> RUNTIME REQUIREMENT MAP
-> IMPLEMENTATION
-> REGRESSION
-> INDEPENDENT AUDIT
-> MAINLINE MERGE
```
