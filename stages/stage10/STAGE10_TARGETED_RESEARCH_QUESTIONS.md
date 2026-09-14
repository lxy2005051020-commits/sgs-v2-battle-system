# Stage10 Targeted Research Questions

> Work package: `Stage10 Design Repair R1-A`
>
> Admission source: `STAGE10_AUTHORITY_GAP_TRIAGE.md`
>
> Scope rule: this file contains only gameplay facts that passed the Research Admission Gate. It does not reopen FIRST_AID, RECUPERATION, or the continuous-damage family as a whole.

---

## 0. Admission Boundary

Current authority already closes:

```text
FIRST_AID
- one opportunity per eligible resolved damage event
- no round cap
- fatal damage cannot resurrect
- inactive source skill suppresses opportunity
- healing ban acts at recovery resolution

RECUPERATION
- TARGET_ACTION_START
- inactive source skill loses the opportunity with no catch-up
- duration clock continues
- healing ban acts at recovery resolution
- missing-troop cap is dynamic

RNG owner in simulator
- BattleContext.random only
- Python random outside RandomSystem forbidden
```

This file does **not** ask any of those questions again.

The unresolved gameplay fact is only whether particular otherwise-valid recovery opportunities consume a probability draw in two edge conditions that affect deterministic replay sequence.

---

## S10-TR-01

### Topic

Guaranteed recovery RNG consumption

### States

```text
690078 FIRST_AID / 急救
690079 RECUPERATION / 休整
```

### Question

When the final effective recovery probability is exactly `100%`, does the official runtime still consume one probability RNG draw?

### Known

```text
1. FIRST_AID gives one probability opportunity per eligible resolved damage event.
2. RECUPERATION sources can include guaranteed recovery behavior.
3. 100% FIRST_AID sources have observed success with no failure cases.
4. Temporary source-skill inactivity suppresses the opportunity and therefore no probability check occurs in that inactive window.
5. Existing contracts explicitly keep PRNG internals / scheduling outside the currently frozen mechanism result.
6. Current simulator RandomSystem.chance(1.0) calls random() and therefore consumes one draw.
```

Observed `100% success` is **not** sufficient evidence that a random value was consumed.

### Unknown

```text
Does official p == 1.0 enter the same probability-sampling path as 0 < p < 1,
or is it deterministically short-circuited before PRNG consumption?
```

### Hypothesis A · DRAW_AT_1_0

```text
opportunity reached
→ consume one RNG value
→ compare against 1.0
→ guaranteed success
→ recovery resolution
```

### Hypothesis B · SHORT_CIRCUIT_1_0

```text
opportunity reached
→ detect guaranteed probability
→ no RNG draw
→ success
→ recovery resolution
```

### Observable Difference

The immediate recovery outcome can be identical under both hypotheses.

The difference appears in every later RNG consumer:

```text
critical / proc / target-selection / chance event / other random factor
```

A simulator choosing the wrong hypothesis will diverge in deterministic replay even while the current recovery log looks correct.

### Required Samples

A valid sample must expose sequence position, not merely success:

```text
A. reproducible battle seed / replay-equivalent raw trace, if available
B. one guaranteed FIRST_AID or RECUPERATION opportunity at a known point
C. a downstream RNG-sensitive event whose result can discriminate one-draw offset
D. a matched control where the guaranteed opportunity is absent but every earlier RNG consumer is identical
```

Preferred shapes:

```text
pair 1:
control battle without guaranteed recovery opportunity
vs
same setup with guaranteed recovery opportunity

pair 2:
same deterministic seed / same preceding event stream
→ compare first downstream stochastic branch
```

If the available official battle-report format does not reveal seeds or enough downstream stochastic structure, raw protocol/event traces or another evidence source capable of proving draw position are required. Do not infer draw consumption from cfg success/failure frequency alone.

### Acceptance Criteria

Close only when evidence uniquely supports one of:

```text
GUARANTEED_RECOVERY_RNG = CONSUME_ONE_DRAW
or
GUARANTEED_RECOVERY_RNG = CONSUME_ZERO_DRAWS
```

Minimum acceptance:

```text
- no unmatched earlier RNG consumer in the comparison
- downstream discriminator behaves consistently with exactly one hypothesis
- at least one FIRST_AID guaranteed-source case and one RECUPERATION guaranteed-source case,
  unless shared official probability machinery is independently proven to be common and sufficient
```

A large number of `100% -> success` observations without sequence discrimination does not close the question.

### Impact if unresolved

```text
Stage10 cannot truthfully freeze exact deterministic RNG replay semantics for p == 1.0.
Stage10 architecture repair unrelated to this RNG edge may continue.
Production recovery RNG implementation must not be frozen on an engineering guess.
```

### Blocking Stage10 design?

`YES`, limited to the recovery RNG-admission contract.

---

## S10-TR-02

### Topic

Zero recoverable gap / full-troop recovery opportunity RNG consumption

### States

```text
690079 RECUPERATION / 休整
690078 FIRST_AID / 急救, only if an authority-valid eligible opportunity can reach zero recoverable gap
```

### Question

When a recovery opportunity is otherwise reached while `target.troops == target.max_troops`, does the official runtime consume the probability draw before recovery is capped to zero, or does zero missing troop short-circuit probability evaluation?

### Known

```text
1. Missing-troop cap is a dynamic recovery-time fact.
2. RECUPERATION battle evidence contains normal effect execution with actual recovery 0 under full/no-gap conditions.
3. Healing-ban evidence proves that a recovery state/opportunity can still execute even when final actual recovery becomes 0.
4. Healing-ban ordering does not answer the full-troop RNG question.
5. Current frozen authority does not state whether missing-troop eligibility is tested before or after probability sampling.
```

For FIRST_AID, ordinary positive troop loss normally creates missing troops before its AFTER_DAMAGE opportunity. Therefore the first research step for FIRST_AID is reachability: prove that an official eligible FIRST_AID opportunity can actually arrive at this checkpoint with zero recoverable gap. If not, this edge is RECUPERATION-only rather than a forced synthetic FIRST_AID case.

### Unknown

```text
Whether zero recoverable gap prevents the probability draw.
```

### Hypothesis A · ROLL_THEN_CAP

```text
active opportunity reached
→ probability draw
→ on success compute/submit recovery
→ missing-troop cap = 0
→ actual recovery = 0
```

### Hypothesis B · ZERO_GAP_SHORT_CIRCUIT

```text
active opportunity reached
→ missing troops == 0
→ opportunity terminates before probability draw
→ actual recovery = 0
```

### Hypothesis C · OTHER

Any other sequencing is admissible only if directly supported by evidence and documented precisely enough to determine RNG consumption.

### Observable Difference

```text
Immediate troops:
usually identical at 0 recovered

Deterministic replay:
different downstream RNG sequence if A consumes a draw and B does not

Possible protocol/log difference:
probability success/failure marker may be present or absent at zero gap
```

### Required Samples

#### RECUPERATION primary sample

Prefer a **non-guaranteed** source so the probability path itself can be observed:

```text
target at exact max troops
+ RECUPERATION active at TARGET_ACTION_START
+ source skill active
+ no healing ban
+ opportunity definitely reaches trigger node
+ source probability strictly between 0 and 1
+ downstream RNG-sensitive discriminator
```

Collect both apparent success/failure or protocol variants if available.

#### FIRST_AID reachability sample

Do not manufacture this case in the simulator.

First establish an official battle-report/protocol case satisfying:

```text
eligible AFTER_DAMAGE_EVENT
+ FIRST_AID opportunity admitted by the frozen contract
+ target has zero recoverable gap at that exact opportunity checkpoint
```

If no such official path exists because positive `ActualTargetTroopLoss` necessarily creates a gap and prevented/zero-loss events are ineligible, record:

```text
FIRST_AID_ZERO_GAP = UNREACHABLE_BY_FROZEN_ELIGIBILITY
```

and scope the RNG question to RECUPERATION.

### Minimum Battle-Report Sample Shape

```text
RECUPERATION:
- max troops verified immediately before action-start recovery window
- active probabilistic source
- cfg/state execution evidence at that window
- later stochastic event usable as sequence discriminator
- matched/replay-equivalent control where possible

FIRST_AID:
- only after official reachability is proven
- exact damage-event and troop snapshots around AFTER_DAMAGE checkpoint
```

### Acceptance Criteria

Close only when authority can freeze one of:

```text
ZERO_GAP_RECOVERY_RNG = CONSUME_ONE_DRAW
ZERO_GAP_RECOVERY_RNG = CONSUME_ZERO_DRAWS
```

or, for FIRST_AID specifically:

```text
FIRST_AID_ZERO_GAP = UNREACHABLE_BY_FROZEN_ELIGIBILITY
```

Evidence showing only `actual recovery = 0` is insufficient. The research must distinguish probability-path admission / draw consumption.

### Impact if unresolved

```text
Stage10 cannot freeze exact RNG admission at zero recoverable gap.
Downstream deterministic replay may diverge.
No broader RECUPERATION or FIRST_AID re-research is justified.
```

### Blocking Stage10 design?

`YES`, limited to exact recovery RNG-admission ordering.

---

## Explicitly Not Admitted

The following are closed or architectural and must not be added to the battle-report queue under R1-A:

```text
continuous damage trigger timing
same-name refresh / overwrite
application-time snapshot policy
source death persistence
owner death hard termination
REBELLION route and defense-stat bypass
FIRST_AID per-damage-event frequency
FIRST_AID fatal no-resurrection
RECUPERATION action-start timing
source-skill inactive window / no catch-up
HEALING_BAN versus recovery resolution ordering
dead-source historical WEAKNESS snapshot
Share DirectTroopLoss -> FIRST_AID
Distribution DirectTroopLoss -> FIRST_AID
Stage7 Hook death abort implementation
PRE_BATTLE lifecycle representation
Stage8 frozen-basis producer design
DamagePipelineTrace representation
SkillRuntime registry / lookup
refresh application identity
standard/Cleave aftermath port
```

---

## Research Stop Rule

Research stops as soon as `S10-TR-01` and `S10-TR-02` are authoritatively closed.

It must not expand into:

```text
re-study BURN
re-study FLOOD
re-study POISON
re-study ROUT
re-study SANDSTORM
re-study REBELLION
re-study all FIRST_AID mechanics
re-study all RECUPERATION mechanics
```

The question is the unit of admission. The state family is not.
