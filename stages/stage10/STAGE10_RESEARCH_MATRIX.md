# Stage10 · Persistent State Runtime Integration · Research Matrix

> Status: `RESEARCH COMPLETE / DESIGN NOT YET FROZEN`
>
> Production implementation: `NOT AUTHORIZED`
>
> Battle repo baseline: `main` at Stage9 FROZEN
>
> Gameplay authority: `lxy2005051020-commits/sgs-state-mechanics-research`

## 1. Purpose

This matrix converts the eight frozen persistent-state mechanism contracts into a runtime-facing research summary. It does **not** invent formulas or implementation behavior.

Normative rule:

```text
Mechanism Contract > this matrix > implementation convenience
```

If this matrix and the current authority repository disagree, the current frozen mechanism contract wins and Stage10 research must be corrected before design freeze.

## 2. Shared family findings

### 2.1 Continuous-damage family

The following six states belong to one runtime family:

```text
690072 BURN / 灼烧
690073 FLOOD / 水攻
690074 POISON / 中毒
690075 ROUT / 溃逃
690076 SANDSTORM / 沙暴
690077 REBELLION / 叛逃
```

Shared frozen semantics:

```text
trigger node                 = TARGET_ACTION_START
normal reachable frequency  = max 1 tick / owner / combat round
instance limit               = one effective same-name instance per owner
same-source reapply          = REFRESH_AND_OVERWRITE
cross-source reapply         = REFRESH_AND_OVERWRITE
refresh                      = replace provenance + duration + application context + potency
first tick                   = next valid target action start
application before action    = same-round tick may occur
application after action     = first tick moves to next round
application context          = LOCKED_AT_APPLICATION
runtime source attr changes  = do not recalculate existing potency
runtime ordinary modifiers   = do not recalculate existing potency
refresh                      = rebuild application snapshot
source death                 = existing state persists
owner death                  = hard termination / state cleanup
purify                       = removes negative continuous state
stun/disarm/silence          = do not suppress an already eligible tick
confusion                    = does not redirect existing DOT tick
weakness                     = dynamic check at trigger/damage resolution
Evasion / Barrier            = dynamic check at trigger/damage resolution when those mechanisms exist
```

The six states therefore must **not** be implemented as six independent combat loops.

### 2.2 Recovery family

```text
690078 FIRST_AID / 急救
690079 RECUPERATION / 休整
```

Shared frozen semantics:

```text
one effective same-name instance per owner
same/cross-source reapply = REFRESH_AND_OVERWRITE
application-time recovery context is snapshotted
runtime recovery-modifier changes do not retroactively recalculate existing instance
owner death hard-terminates the state
healing prevention is a dynamic recovery-time gate
actual recovery is dynamically capped by current missing troops
negative cleanse does not remove these positive recovery states
```

They are **not** the same trigger topology:

```text
RECUPERATION -> TARGET_ACTION_START
FIRST_AID    -> AFTER_DAMAGE_EVENT, once per eligible resolved damage event
```

## 3. Per-state matrix

| State | Category / Damage family | Trigger | Application-time snapshot | Trigger-time dynamic inputs | Reapply | Source death | Runtime special case |
|---|---|---|---|---|---|---|---|
| `690072 BURN` | Strategy continuous damage | `TARGET_ACTION_START` | source attributes, applicable ordinary damage modifiers, strategy-crit context, potency | weakness, evasion, barrier, owner alive | refresh + overwrite | persists | strategy route |
| `690073 FLOOD` | Strategy continuous damage | `TARGET_ACTION_START` | same family snapshot | weakness, evasion, barrier, Flood external observers; Elephant delay when applicable | refresh + overwrite | persists | external observer semantics remain outside core Flood runtime |
| `690074 POISON` | Strategy continuous damage | `TARGET_ACTION_START` | same family snapshot | weakness, evasion, barrier | refresh + overwrite | persists | standard strategy DOT |
| `690075 ROUT` | Weapon continuous damage | `TARGET_ACTION_START` | source attributes, weapon modifiers, physical-crit context, potency | weakness, evasion, barrier | refresh + overwrite | persists | weapon route; no implicit defense pierce |
| `690076 SANDSTORM` | Strategy continuous damage | `TARGET_ACTION_START` | strategy family snapshot | weakness, evasion, barrier | refresh + overwrite | persists | standard strategy DOT |
| `690077 REBELLION` | Dynamic weapon/strategy continuous damage | `TARGET_ACTION_START` | route + driving attribute context + potency + matching modifiers + crit context | weakness, evasion, barrier, owner alive | refresh + overwrite + route redetermination | persists | route locked at application; relevant target defense stat ignored; opposite-family modifiers do not apply |
| `690078 FIRST_AID` | triggered recovery | `AFTER_DAMAGE_EVENT` | recovery model, probability, source attributes, source/target recovery modifiers | triggering actual damage when ratio-based, target alive, missing troops, healing ban, source-skill active gate | refresh + overwrite | persists | independent probability check per eligible damage event; no round cap |
| `690079 RECUPERATION` | periodic recovery | `TARGET_ACTION_START` | recovery potency model, source attributes, recovery modifiers | target alive, missing troops, healing ban, source-skill active gate | refresh + overwrite | active source: persists; command-aura cases externally owned | finite or battle-long lifecycle; inactive window loses tick with no catch-up |

## 4. Damage-family detail

### 4.1 Strategy DOT

```text
BURN / FLOOD / POISON / SANDSTORM
```

Required semantics:

```text
damage_type                 = STRATEGY
source_type                 = CONTINUOUS
strategy modifiers          = applicable according to frozen snapshot
weapon-only modifiers       = not applicable
strategy critical context   = participates when applicable, locked at application
physical critical context   = not applicable
```

The research contracts do **not** authorize Stage10 to claim that ordinary active strategy damage and strategy continuous damage have identical microscopic formulas. Exact formula constants remain outside the persistent-state mechanism research scope.

### 4.2 Weapon DOT

```text
ROUT
```

Required semantics:

```text
damage_type                 = WEAPON
source_type                 = CONTINUOUS
weapon modifiers            = applicable according to frozen snapshot
strategy-only modifiers     = not applicable
physical critical context   = participates when applicable, locked at application
strategy critical context   = not applicable
```

### 4.3 Rebellion

Rebellion is not a third damage type.

At application / refresh time:

```text
compare application-time effective source ATK and INT
↓
lock route = WEAPON or STRATEGY
↓
lock route-specific potency / modifier / crit context
```

At each tick:

```text
use the already locked route
DO NOT recompare runtime ATK / INT
DO NOT reroute because source attributes changed
```

Formula policy:

```text
IGNORE_RELEVANT_TARGET_DEFENSE
```

means only the relevant defensive stat contribution is bypassed. Generic percentage reductions and the matching route-specific percentage reductions remain applicable; the opposite damage-family modifiers do not become applicable.

## 5. Recovery-family detail

### 5.1 FIRST_AID

Eligible damage-event families include:

```text
normal attack
skill damage
command damage
continuous damage tick
multi-hit: each hit independently
assault / pursuit damage
counterattack damage
```

Trigger contract:

```text
one eligible resolved damage event
→ one probability opportunity
→ success creates one recovery resolution
```

No combat-round cap is authorized.

Recovery potency has at least two source-skill-defined models:

```text
A. treatment-rate model
B. triggering-damage-ratio model
```

For damage-ratio sources, the triggering damage amount is a trigger-time dynamic input. Stage10 must not freeze one universal flat `amount` as the FIRST_AID state model.

### 5.2 RECUPERATION

Trigger contract:

```text
TARGET_ACTION_START
```

If applied before the owner acts in that combat round, the state may recover in the same round. If applied after the owner already acted, there is no catch-up tick; first recovery moves to the next valid action start.

Lifecycle includes two forms:

```text
finite N-round instance
battle-long / source-lifecycle-owned instance
```

Temporary source-skill deactivation:

```text
execution suppressed
probability/recovery opportunity lost
clock continues
no duration extension
no catch-up after resume
```

## 6. Lifecycle findings

### 6.1 Same-name uniqueness

For all eight Stage10 states, current authority freezes a single effective same-name state instance per owner.

Stage10 therefore requires explicit lifecycle arbitration:

```text
incoming same-name state
→ remove/replace previous effective instance atomically under StateLifecycleSystem ownership
→ create refreshed instance with new provenance and new application snapshot
```

This is **not** a generic global stacking law for all states.

### 6.2 Expiration

The mechanism contracts express expiration relative to the state owner's future action-start opportunities, not merely a global `ROUND_START` / `ROUND_END` timer.

Required semantic invariant:

```text
N-round persistent state
→ at most N eligible action-start ticks/recovery opportunities
→ no N+1 tick
```

Suppressed/inactive opportunities are not retroactively replayed unless a specific contract says otherwise. Current Stage10 recovery authority explicitly says no catch-up.

### 6.3 Death

Owner death:

```text
clear attached persistent states
abort remaining owner-state resolution
reject later application to dead owner
```

Source death is distinct:

```text
continuous damage existing instance -> persists
FIRST_AID existing instance          -> persists
active-sourced RECUPERATION          -> persists
command-aura RECUPERATION removal    -> external command-aura lifecycle ownership
```

Stage10 must not implement “source dead => delete every sourced state”.

## 7. Ordering findings

Research does **not** authorize a universal order such as:

```text
all DOT before all recovery
or
all recovery before all DOT
```

RECUPERATION evidence observes both relative orders with DOT, and the mechanism contract classifies the internal state ordering as non-blocking/unresolved.

Therefore Stage10 may freeze an engineering-deterministic state iteration rule only if it is clearly labeled as runtime determinism rather than an official family-priority claim.

The existing Stage7 `instance_id` deterministic ordering can remain a candidate implementation rule, but Stage10 design must audit lifecycle replacement and same-node semantics before freezing it.

## 8. Research boundaries preserved

Stage10 research intentionally does not invent:

```text
exact microscopic DOT formula constants
exact treatment non-linear constants
new PRNG algorithm
universal positive dispel behavior
universal same-node family priority
external observer skill semantics
external command-aura lifecycle semantics beyond the frozen interaction boundary
unresearched official critical / evasion / barrier state application contracts
```

Those are either formula research, external mechanism ownership, or later official-state integration tasks.

## 9. Research verdict

```text
8 / 8 mechanism contracts read and classified
6 / 6 continuous-damage states share one trigger/lifecycle family
2 / 2 recovery states separated by trigger topology
same-name refresh semantics resolved
application snapshot policy resolved
death semantics resolved
RNG ownership requirement resolved
lifecycle timing requirement resolved
remaining gaps moved to STAGE10_OPEN_QUESTIONS.md

STAGE10 MECHANISM RESEARCH EXTRACTION = COMPLETE
STAGE10 DESIGN FREEZE                  = NOT YET AUTHORIZED
STAGE10 PRODUCTION IMPLEMENTATION      = NOT AUTHORIZED
```
