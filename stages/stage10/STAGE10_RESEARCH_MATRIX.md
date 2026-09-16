# Stage10 · Persistent State Runtime Integration · Research Matrix R1-C

> Status: `MECHANISM RESEARCH COMPLETE / R1-C NORMALIZED`  
> Architecture: `STAGE10.md DRAFT V2`  
> Production implementation: `NOT AUTHORIZED`

This matrix summarizes the mechanism facts Stage10 is allowed to consume. Architecture choices belong in `STAGE10.md`; hidden simulator policies must not be promoted to gameplay facts.

---

## 1. Shared continuous-damage family

Members:

```text
690072 BURN
690073 FLOOD
690074 POISON
690075 ROUT
690076 SANDSTORM
690077 REBELLION
```

Frozen family semantics:

```text
trigger node                 = TARGET_ACTION_START
max effective opportunity   = 1 per owner per combat round
same-name effective limit   = 1
same-source reapply          = REFRESH_AND_OVERWRITE
cross-source reapply         = REFRESH_AND_OVERWRITE
application context          = LOCKED_AT_APPLICATION
refresh                      = rebuild complete application context
source attributes            = locked at application/refresh
ordinary source/target mods  = locked at application/refresh
matching crit context        = locked at application/refresh when applicable
weakness                     = dynamic at tick
Evasion / Barrier topology   = dynamic at tick when those mechanisms exist
source death                 = existing state persists
owner death                  = clear states + abort remaining state resolution/action
purify                       = removes negative continuous state
stun/disarm/silence          = do not suppress an already reached action-start tick
confusion                    = does not redirect existing DOT tick by default
```

Application-time context and tick-time dynamic gates are distinct contracts.

---

## 2. Damage-family mapping

| State | Damage route | Application-time locked context | Tick-time dynamic topology | Special rule |
|---|---|---|---|---|
| BURN | STRATEGY | source formula facts, matching ordinary modifiers, strategy-crit context, source potency | weakness, evasion, barrier, target liveness | standard strategy continuous damage |
| FLOOD | STRATEGY | same strategy family context | weakness, evasion, barrier | external FLOOD observers/delay remain external |
| POISON | STRATEGY | same strategy family context | weakness, evasion, barrier | standard strategy continuous damage |
| ROUT | WEAPON | source formula facts, matching weapon/generic modifiers, physical-crit context, source potency | weakness, evasion, barrier | no implicit defense pierce |
| SANDSTORM | STRATEGY | same strategy family context | weakness, evasion, barrier | standard strategy continuous damage |
| REBELLION | WEAPON or STRATEGY, locked at application | selected route, matching source formula facts/modifiers/crit context, potency | weakness, evasion, barrier | relevant target defense ignored by Stage8 formula policy |

REBELLION is explicitly:

```text
not DirectTroopLoss
not true damage
not a third damage family
```

Its route is redetermined only on successful reapplication/refresh.

---

## 3. Recovery family

Members:

```text
690078 FIRST_AID
690079 RECUPERATION
```

Shared frozen semantics:

```text
same-name effective limit = 1
reapply                   = REFRESH_AND_OVERWRITE
recovery potency context  = LOCKED_AT_APPLICATION
owner death               = hard termination
healing ban               = dynamic RecoverySystem gate
actual troop restore cap  = dynamic TroopSystem cap
full troops               != skip opportunity
```

Trigger topology differs:

```text
FIRST_AID    = eligible DamageAftermath
RECUPERATION = TARGET_ACTION_START
```

---

## 4. FIRST_AID corrected eligibility matrix

Eligibility and recovery amount are separate.

| Damage aftermath | Resolved-hit damage event exists | ActualTargetTroopLoss | Target survives | FIRST_AID opportunity |
|---|---:|---:|---:|---:|
| ordinary positive nonfatal settlement | YES | `> 0` | YES | YES |
| WEAKNESS_ZERO | YES | `0` | YES | YES |
| BARRIER_ZERO | YES | `0` | YES | YES |
| EVASION / MISS | NO | `0` | YES | NO |
| fatal resolved hit | YES | `>= 0` | NO | NO |
| Share DirectTroopLoss | not a DamageEvent aftermath | any | any | NO |
| Distribution DirectTroopLoss | not a DamageEvent aftermath | any | any | NO |

Normative negative statement:

```text
FIRST_AID eligibility
!= ActualTargetTroopLoss > 0
```

No single `prevented: bool` can encode this table.

---

## 5. FIRST_AID potency models

At minimum two source-defined models exist:

### 5.1 TREATMENT_AMOUNT

```text
potency basis = frozen application-time treatment context
```

Therefore:

```text
zero-loss resolved hit
+
existing missing troops > 0
→ eligible opportunity can recover > 0 after successful probability check
```

### 5.2 TRIGGER_DAMAGE_RATIO

```text
potency basis includes dynamic ActualTargetTroopLoss
```

Therefore:

```text
ActualTargetTroopLoss == 0
→ eligible opportunity still exists
→ nominal ratio amount may be 0
```

The amount being zero does not erase the opportunity.

---

## 6. RECUPERATION lifecycle

```text
trigger = TARGET_ACTION_START
```

Finite lifecycle facts:

```text
apply before owner action in R
→ R can be first eligible round

apply after owner action in R
→ first eligible round is R+1

refresh
→ lifecycle + potency + provenance replaced from refresh application

temporary source-skill inactive
→ current opportunity suppressed
→ duration clock continues
→ no catch-up
```

PRE_BATTLE is a distinct lifecycle domain. R1-C architecture maps PRE_BATTLE application to first combat eligibility at Round1; this is an architecture correction to the Draft V1 arithmetic, not a new family research claim.

---

## 7. Full-troop opportunity boundary

Target full troops is not an eligibility short-circuit:

```text
recoverable_gap == 0
→ opportunity may still be admitted
→ probability policy still belongs to that admitted opportunity
→ successful recovery request may resolve actual recovery = 0
```

This applies to RECUPERATION and to eligible FIRST_AID aftermath.

---

## 8. Recovery PRNG authority boundary

Official hidden PRNG consumption for these edge cases is not observable:

```text
probability == 100%
recoverable_gap == 0
```

Classification:

```text
OFFICIAL GAMEPLAY FACT = UNKNOWN / UNOBSERVABLE
```

Any simulator choice about draw consumption is:

```text
ENGINEERING DETERMINISM POLICY
```

and must remain in Battle architecture documentation, not Gameplay Authority.

---

## 9. Source-skill lifecycle boundary

Persistent source gate modes used by architecture:

```text
ALWAYS_ACTIVE
QUERY_SKILL_RUNTIME
EXTERNAL_LIFECYCLE
```

Gameplay boundary:

```text
source death alone does not generically delete already-applied persistent effects
```

`QUERY_SKILL_RUNTIME` must not reinterpret source death as temporary skill inactive.

`EXTERNAL_LIFECYCLE` means an external authoritative lifecycle owner may remove the state; it is not evidence for a generic per-opportunity callback.

---

## 10. Evidence-gated external mechanisms

The following remain outside Stage10 official production promotion unless separately evidenced:

```text
EVASION complete official binding
BARRIER complete official binding
CRITICAL complete official binding
STRATEGY_CRITICAL complete official binding
DAMAGE_REDUCTION_PIERCE complete official binding
positive dispel universal behavior
```

Their typed topology may be referenced to define integration boundaries without claiming full implementation authority.

---

## 11. Authority synchronization note

Pinned Gameplay Authority for R1-C:

```text
61f2be7e87e6bfab1433657ee7f766ae0c53da9d
```

At this exact repository HEAD, the task-referenced targeted-research result files are not present and the checked-in FIRST_AID contract still predates the zero-loss correction.

R1-C therefore records the project-owner supplied targeted-research closures separately rather than falsifying the repository history. Gameplay Authority is unchanged by this Battle-repo repair.

---

## 12. Research verdict

```text
Core Stage10 mechanism research          = COMPLETE
FIRST_AID zero-loss eligibility          = CLOSED
full-troop opportunity semantics         = CLOSED
hidden official recovery PRNG behavior   = UNKNOWN / NON-BLOCKING
new battle-report research for R1-C      = NOT REQUIRED
architecture re-audit                    = REQUIRED
production implementation                = NOT AUTHORIZED
```
