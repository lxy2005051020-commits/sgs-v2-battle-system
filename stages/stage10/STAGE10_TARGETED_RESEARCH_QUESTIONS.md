# Stage10 Targeted Research Closure Record

> Origin: `Stage10 Design Repair R1-A / Authority Gap Triage`  
> R1-C status: `TARGETED RESEARCH INPUT COMPLETE`  
> Production implementation: `NOT AUTHORIZED`

This file preserves the two original targeted RNG questions and records the additional FIRST_AID zero-loss closure supplied to R1-C. It must not be read as permission to modify Gameplay Authority or as evidence that hidden official PRNG scheduling has become observable.

---

## 0. Repository synchronization boundary

R1-C pinned Gameplay Authority at:

```text
lxy2005051020-commits/sgs-state-mechanics-research
main
61f2be7e87e6bfab1433657ee7f766ae0c53da9d
```

At that exact HEAD, the task-referenced result files:

```text
stage10/RECOVERY_RNG_EDGE_RESEARCH.md
stage10/FIRST_AID_ZERO_LOSS_ELIGIBILITY_RESEARCH.md
```

are not present in the repository tree, and the checked-in FIRST_AID mechanism contract still predates the zero-loss eligibility correction.

Therefore this Battle-repository closure record distinguishes:

```text
repository-pinned Gameplay Authority
from
project-owner supplied targeted-research closure used by R1-C
```

R1-C does not modify or silently rewrite the Gameplay Authority repository.

---

## 1. S10-TR-01 · Guaranteed recovery RNG consumption

Original question:

```text
When final effective recovery probability == 100%,
does the official runtime still consume a probability RNG draw?
```

Research conclusion supplied to R1-C:

```text
OFFICIAL HIDDEN PRNG CONSUMPTION
= UNKNOWN / UNOBSERVABLE
```

No battle-report/protocol evidence uniquely discriminates:

```text
CONSUME_ONE_DRAW
vs
CONSUME_ZERO_DRAWS
```

Therefore the official question is **not converted into a gameplay fact**.

R1-C disposition:

```text
Gameplay blocker                 = NO
Official authority classification= OFFICIAL UNKNOWN
Simulator exact replay behavior  = ENGINEERING DETERMINISM POLICY
```

The chosen simulator policy is documented only in `STAGE10.md`.

---

## 2. S10-TR-02 · Zero recoverable gap RNG consumption

Original question:

```text
When recoverable_gap == 0,
does the official runtime consume the probability draw before actual recovery is capped to zero?
```

Research conclusion supplied to R1-C:

```text
OFFICIAL HIDDEN PRNG CONSUMPTION
= UNKNOWN / UNOBSERVABLE
```

Again, no official fact is claimed for draw count.

However the observable opportunity topology **is** closed:

```text
recoverable_gap == 0
!=
skip recovery opportunity
```

For RECUPERATION:

```text
full troops
→ opportunity is admitted/observable
→ recovery execution may occur
→ actual recovery is capped to 0
```

R1-C therefore separates:

```text
opportunity existence        = GAMEPLAY FROZEN
hidden draw consumption      = OFFICIAL UNKNOWN
simulator draw implementation= ENGINEERING DETERMINISM
```

---

## 3. S10-TR-03 · FIRST_AID zero-loss eligibility

R1-C targeted-research closure supplied by the project owner establishes:

```text
FIRST_AID eligibility
!= ActualTargetTroopLoss > 0
```

Required topology:

### WEAKNESS_ZERO

```text
resolved damage-event topology exists
ActualTargetTroopLoss == 0
target survives
→ FIRST_AID opportunity = YES
```

### BARRIER_ZERO

```text
resolved damage-event topology exists
ActualTargetTroopLoss == 0
target survives
→ FIRST_AID opportunity = YES
```

### EVASION / MISS

```text
no resolved-hit damage event
ActualTargetTroopLoss == 0
→ FIRST_AID opportunity = NO
```

This closes the architecture question that Draft V1 had represented with an insufficient:

```text
if actual_target_troop_loss <= 0:
    stop
```

or a single ambiguous:

```text
if prevented:
    stop
```

Both shortcuts are forbidden by Draft V2.

---

## 4. Full-troop FIRST_AID reachability

The old R1-A question assumed positive damage was required before FIRST_AID and therefore treated zero-gap FIRST_AID as potentially unreachable.

S10-TR-03 supersedes that assumption.

A resolved zero-loss damage event can create a FIRST_AID opportunity while the target remains at full troops:

```text
resolved zero-loss hit
+
target full troops
→ FIRST_AID opportunity exists
→ actual recovery may be 0
```

A resolved zero-loss hit can also occur while the target already has unrelated missing troops:

```text
resolved zero-loss hit
+
existing missing troops > 0
+
TREATMENT_AMOUNT model
→ opportunity exists
→ successful recovery can be > 0
```

For a `TRIGGER_DAMAGE_RATIO` model:

```text
ActualTargetTroopLoss == 0
→ opportunity still exists
→ nominal ratio amount may be 0
```

Eligibility and amount are separate contracts.

---

## 5. Simulator determinism boundary

Because the official draw count is unobservable, Stage10 architecture is allowed to choose one simulator contract provided it is labeled honestly.

R1-C chooses:

```text
Every admitted RecoveryOpportunity
→ exactly one context.random.chance(probability) call
→ including probability == 0.0
→ including probability == 1.0
→ regardless of recoverable_gap
```

This policy occurs only after opportunity admission gates pass.

Classification:

```text
ENGINEERING DETERMINISM
NOT OFFICIAL GAMEPLAY AUTHORITY
```

This file records the architecture handoff but does not promote the policy into Gameplay Authority.

---

## 6. Explicitly still not admitted as new gameplay research

The targeted-research closure does not reopen:

```text
continuous-damage trigger timing
same-name refresh/overwrite
application-time snapshot policy
source-death persistence
owner-death hard termination
REBELLION route / defense-stat bypass
FIRST_AID per-damage-event frequency
RECUPERATION action-start timing
source-skill inactive/no-catch-up
healing-ban ordering
Share DirectTroopLoss → FIRST_AID
Distribution DirectTroopLoss → FIRST_AID
```

Nor does it authorize complete production implementation of:

```text
EVASION
BARRIER
CRITICAL
STRATEGY_CRITICAL
DAMAGE_REDUCTION_PIERCE
positive dispel
```

Evasion/Barrier are used only as typed aftermath topology examples for FIRST_AID eligibility.

---

## 7. Research package verdict

```text
S10-TR-01 official PRNG draw count = UNKNOWN / UNOBSERVABLE
S10-TR-02 official PRNG draw count = UNKNOWN / UNOBSERVABLE
S10-TR-02 opportunity at zero gap  = CLOSED: opportunity not skipped
S10-TR-03 zero-loss FIRST_AID      = CLOSED

Additional battle-report research required for R1-C architecture repair = NO
Gameplay research blocker for R1-C                                = NO
Simulator PRNG policy                                              = ENGINEERING-DEFINED
Gameplay Authority repository modified by R1-C                     = NO
```

Next gate:

```text
Stage10 Architecture Draft V2
→ Independent Design Re-Audit Round 2
```
