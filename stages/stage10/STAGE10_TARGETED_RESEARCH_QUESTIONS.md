# Stage10 Targeted Research Closure Record

> Origin: `Stage10 Design Repair R1-A / Authority Gap Triage`  
> R2-B status: `TARGETED RESEARCH FORMALLY PROMOTED & CLOSED`  
> Authority synchronization: `PASS (a9a05ceffa2a9489cdc1e0a000a4c27bac81a5fe)`  
> Production implementation: `NOT AUTHORIZED`

This file preserves the original targeted research questions (S10-TR-01, S10-TR-02, S10-TR-03) and records their formal promotion into Gameplay Authority.

---

## 0. Repository synchronization boundary

Gameplay Authority `main` is canonically pinned at:

```text
lxy2005051020-commits/sgs-state-mechanics-research
branch: main
canonical authoritative HEAD: a9a05ceffa2a9489cdc1e0a000a4c27bac81a5fe
```

Following Stage10 R2-A3 local provenance recovery and R2-A4 formal promotion:
- Commit `4661f4ffa1074045ce17d9158499dc03a8dfbec3` added the full targeted research documentation, research tools, raw logs, and parsed tables to Gameplay Authority.
- Commit `0b9e172a4d3ce3b29025347b086738c0253e56ac` updated `states/persistent/first_aid/MECHANISM_CONTRACT.md` with zero-loss, full-troop, and trigger eligibility alignment.
- Commit `a9a05ceffa2a9489cdc1e0a000a4c27bac81a5fe` completed the formal promotion record (`PROMOTION_STAGE10_R2_A4.md`).

Authority synchronization is complete (`Authority Sync = PASS`). The dual-evidence distinction is closed.

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
S10-TR-01 official PRNG draw count = UNKNOWN / UNOBSERVABLE (PROMOTED to Authority main)
S10-TR-02 official PRNG draw count = UNKNOWN / UNOBSERVABLE (PROMOTED to Authority main)
S10-TR-02 opportunity at zero gap  = CLOSED: opportunity not skipped (PROMOTED to Authority main)
S10-TR-03 zero-loss FIRST_AID      = CLOSED (PROMOTED to Authority main)

Additional battle-report research required for R2-B architecture repair = NO
Gameplay research blocker for R2-B                                = NO
Simulator PRNG policy                                              = ENGINEERING-DEFINED
Gameplay Authority formal promotion                                = PASS (HEAD a9a05ceffa2a9489cdc1e0a000a4c27bac81a5fe)
```

Next gate:

```text
Stage10 Architecture Draft V3
→ Independent Design Re-Audit Round 3
```
