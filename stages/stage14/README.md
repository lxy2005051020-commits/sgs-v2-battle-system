# Stage14 · Concrete Skill Integration

> Status: **ACTIVE / MAINLINE GATE OPEN**

Stage14 begins concrete skill integration on top of the frozen Stage13 core gameplay engine.

## Entry gate

```text
STAGE13_FINAL_EXIT_AUDIT = PASS
CORE_GAMEPLAY_ENGINE     = FROZEN
SKILL_RUNTIME_READINESS  = READY
STAGE14 MAINLINE GATE    = OPEN
```

Stage14 no longer waits on the Stage13 exit gate.

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

## Mainline policy

A concrete skill or mechanism-family batch may enter `main` only when its own gates pass:

```text
selected skill/family Research Contract         = CLOSED/FROZEN
runtime seam mapping                             = REVIEWED
implementation                                   = COMPLETE
skill-specific regression                        = PASS
full regression / demo                           = PASS
independent runtime audit                        = PASS
PR CI                                            = PASS
```

Future functionality must extend existing canonical owners where possible. A concrete skill must not invent gameplay truth from Battle code.

## First pilot: 西凉铁骑

西凉铁骑 is the first Stage14 vertical pilot.

Current Research status:

```text
BASE_XILIANG_MECHANISM_CONTRACT = FROZEN
MATENG_COMMANDER_SCALING        = FROZEN
```

Current Runtime work is maintained in Battle PR #42 pending its final mainline audit and merge.

The pilot exercises:

```text
SkillType.TROOP
-> PRE_BATTLE special troop conversion
-> base-family restraint inheritance
-> team-wide temporary crit state
-> current PRE_BATTLE AttributeSystem speed read
-> Ma Teng commander scaling
-> provider identity / invalidation lifecycle
-> duration expiry
-> BattleEngine automatic PRE_BATTLE wiring
```

It intentionally avoids unresolved storage/battery families represented by 象兵、飞熊军、丹阳兵.

## Batch policy after the pilot

Bulk TROOP integration is allowed only by mechanism family after the relevant shared contract is frozen.

Examples:

```text
simple/static troop skills
-> reusable Stage14 batch lane

trigger-driven troop skills
-> Trigger Family contract first
-> then batch integration

storage / delayed-settlement troop skills
-> Storage Family contract first
-> then integration
```

A skill that requires a new Core primitive leaves the batch lane and receives focused research/runtime review.

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
