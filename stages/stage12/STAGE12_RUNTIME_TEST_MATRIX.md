# Stage12 Runtime Test Matrix Skeleton

> Status: **SKELETON / ENTRY GATE OUTPUT**  
> Baseline: **913 passed / demo PASS** at Battle SHA `b4c27511824001210f781bf8e750c74c9107da72`.

| State / Foundation | Positive Case | Negative Case | Primary Discriminator | Cross-State Required | Minimum |
|---|---|---|---|---|---:|
| Shared State Admission | protected control rejected under effective Insight | unprotected/special-boundary state not rejected | reject candidate vs apply-then-delete | Insight × all explicit contract overlaps | contract-driven |
| Shared Resident/Effective | resident state can be temporarily ineffective | effective state acts normally | suppression vs removal | Insight/Provocation/provider suppression | contract-driven |
| Skill Permission | Exhaustion blocks ACTIVE_SKILL | Basic Attack and standard Assault remain eligible | permission block vs generic cannot-act | Insight × Exhaustion; Exhaustion × Capture | contract-driven |
| Provider Validity | targeted Provider becomes ineffective | unrelated Provider remains effective | Provider vs Holder | FalseReport × Intimidation × Capture | contract-driven |
| Target Policy | eligible Provocation query forces/includes Source | friendly/healing/self/inherited target not cross-forced | operation/query granularity | Confusion/Taunt/Insight/Exhaustion/FalseReport/Capture | contract-driven |
| Equipment Effectiveness | Sabotage disables tested equipment contribution | equipment object remains present | resume vs unequip/reinit | Insight × Sabotage; FalseReport × Sabotage; Sabotage × Capture | contract-driven |
| INSIGHT | protected application rejection + existing suppression/resume | FALSE_REPORT / INTIMIDATION / CAPTURE boundaries preserved | protected vs unprotected/special | Exhaustion, FalseReport, Provocation, Intimidation, Sabotage, Capture | per contract |
| EXHAUSTION | Active permission denied | legal Basic Attack remains | EXHAUSTION ≠ STUN | Insight, Provocation, FalseReport, Intimidation, Capture | per contract |
| FALSE_REPORT | Passive/Command Provider suppressed | Holder-only unrelated effect remains | Provider suppression vs deletion | Insight, Exhaustion, Intimidation, Capture, Sabotage | >= 30 |
| PROVOCATION | admissible Source forced in eligible operation | dead/inadmissible Source not forced | state remains resident after Source death | Confusion, Taunt, Insight, Exhaustion, FalseReport, Capture | >= 25 |
| INTIMIDATION | exactly one eligible Provider suppressed | all-skill suppression forbidden | refresh reroll vs resume-preserve-binding | Insight, Exhaustion, FalseReport, Capture | >= 21 |
| SABOTAGE | equipment contribution suppressed | no physical unequip/delete | resume vs reinitialize | Insight, FalseReport, Capture | per contract |
| CAPTURE | action/damage/provider/recovery/target restrictions | attached Active-origin DOT continues | composite owners vs universal boolean | Insight, Exhaustion, FalseReport, Provocation, Intimidation, Sabotage + Stage11 controls | per contract |

## Mandatory Stage12 cross-state matrix

```text
Insight × Exhaustion
Insight × FalseReport
Insight × Provocation
Insight × Intimidation
Insight × Sabotage
Insight × Capture

Exhaustion × Provocation
Exhaustion × FalseReport
Exhaustion × Intimidation
Exhaustion × Capture

FalseReport × Intimidation
FalseReport × Capture
FalseReport × Sabotage

Provocation × Confusion
Provocation × Taunt
Provocation × Capture

Intimidation × Capture
Sabotage × Capture
```

## Mandatory Stage11 × Stage12 regressions

```text
STUN × CAPTURE
WEAKNESS × CAPTURE
HEALING_BLOCK × CAPTURE
CONFUSION × PROVOCATION
TAUNT × PROVOCATION
DISARM × INSIGHT
STUN × INSIGHT
existing Damage Pipeline × CAPTURE
existing Recovery Pipeline × CAPTURE
```

## RNG obligations

For every randomized application, target selection, Intimidation binding or refresh reroll, tests must record:

- canonical RNG owner = `BattleContext.random`;
- exact decision point that consumes RNG;
- negative branches that must not consume RNG;
- deterministic replay under identical seed.

## Lifecycle obligations

Each state must test only contract-authorized boundaries among:

```text
application
effective timing
refresh / reapplication
same-source
different-source
removal
cleanse
expiry
holder death
source death
battle finalization
```

A `BOUNDED_UNKNOWN` must never become a normal-looking test assertion unless it is explicitly listed in the Runtime Default Ledger.
