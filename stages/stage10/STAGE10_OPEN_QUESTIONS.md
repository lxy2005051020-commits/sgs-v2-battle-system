# Stage10 · Persistent State Runtime Integration · Open Questions

> Status: `MECHANISM RESEARCH CLOSED / DESIGN QUESTIONS OPEN`
>
> This file separates genuine gameplay research gaps from architecture decisions. Human civilization has suffered enough from documents where both are called “TODO”.

## 1. Classification

Each item is classified as one of:

```text
P0 DESIGN BLOCKER
- Stage10 build cannot begin until one architecture answer is frozen and audited.

P1 DESIGN REQUIRED
- must be resolved in STAGE10.md before implementation, but does not reopen gameplay research.

EXTERNAL DEPENDENCY / NON-BLOCKING
- Stage10 must preserve a seam and must not invent the external mechanism.

RESEARCH DEBT / NON-BLOCKING
- current mechanism authority explicitly leaves microscopic behavior unresolved, but it does not prevent a correct Stage10 family runtime.
```

## 2. P0 design blockers

### S10-B01 · Snapshot-backed continuous-damage ingress

**Classification:** `P0 DESIGN BLOCKER`

Frozen authority requires:

```text
continuous damage potency/application context locked at application or refresh
runtime source attribute changes do not recalculate existing state
```

Current DamageSystem standard path recalculates base damage from current UnitRuntime on every request.

Required Stage10 design decision:

```text
How does a continuous state submit its application-time snapshot into the one frozen damage pipeline
without duplicating Stage8 formulas or bypassing prevention/hit/modifier/finalization semantics?
```

Design must choose and prove one authoritative seam.

Forbidden answers:

```text
just keep coefficient and recalculate current source
copy DamageSystem
apply troops directly
encode final damage as DirectTroopLoss
mutate UnitRuntime to emulate snapshot values
```

**Gameplay research needed?** `NO`

This is an architecture problem created by already-frozen gameplay evidence.

---

### S10-B02 · Source-dead persistent damage execution

**Classification:** `P0 DESIGN BLOCKER`

Frozen authority:

```text
source death does not cancel an already applied continuous-damage state
```

Current DamageSystem participant validation rejects a damage source with `troops <= 0`.

Required Stage10 design decision:

```text
How can a persistent state retain historical source provenance and execute its frozen snapshot
without pretending that the source is currently an alive attacker?
```

The solution must preserve:

```text
source unit credit
source skill credit
source state / state instance
Stage9 SourceType.PERIODIC_DAMAGE
one damage transaction
```

but must not redefine general standard damage so dead units can arbitrarily attack.

**Gameplay research needed?** `NO`

---

### S10-B03 · FIRST_AID exact AFTER_DAMAGE checkpoint

**Classification:** `P0 DESIGN BLOCKER`

Frozen authority requires one FIRST_AID opportunity after each eligible damage event, including DOT and multi-hit, and fatal damage must not resurrect the dead target.

Stage9 now separates:

```text
Dtotal
Dtarget
ActualTargetTroopLoss
partition direct losses
reaction/future branches
victory latch
finalization
```

Required Stage10 design decision:

```text
At exactly which explicit coordinator checkpoint is AfterDamageHook emitted?
```

The checkpoint must define:

```text
which typed damage amount feeds damage-ratio FIRST_AID
whether prevented / zero-loss events are eligible
how target death blocks recovery
how each multi-hit DamageInstance becomes an independent opportunity
how periodic damage becomes an eligible opportunity
relative boundary to share/distribution direct loss
relative boundary to counter/cleave/chain admitted work
relative boundary to victory latch and finalization drain
```

Current mechanism authority identifies “当次受击扣减伤害量” as the dynamic ratio input. Stage10 design should therefore start from `ActualTargetTroopLoss` as the leading candidate, but the final mapping must be proven against the exact Stage9 damage-fact ownership contract before freezing.

**Gameplay research needed?** `NO` for the core FIRST_AID contract; `YES only if` a Stage9-specific ambiguity is found that cannot be derived from existing frozen semantics.

---

### S10-B04 · Owner-relative action-start expiration

**Classification:** `P0 DESIGN BLOCKER`

Current generic automatic expiration supports only:

```text
ROUND_START
ROUND_END
```

Stage10 authority requires same-round eligibility and owner-action-start lifecycle semantics.

Required design decision:

```text
How are finite persistent states represented so that refresh, action-start tick and expiration
produce exactly the authorized N opportunities with no N+1 tick and no catch-up?
```

The solution must also handle:

```text
application before owner action
application after owner action
refresh before owner action
refresh after owner action
temporary inactive opportunity loss
owner death before next opportunity
```

**Gameplay research needed?** `NO`

---

## 3. P1 design-required items

### S10-M01 · Persistent-state same-name replacement transaction

**Classification:** `P1 DESIGN REQUIRED`

Authority is clear: one effective same-name instance, refresh-and-overwrite across same/cross source.

Design must freeze whether replacement is represented as:

```text
remove old + create new instance id
or
atomic replace retaining physical instance id
```

Observable gameplay must preserve incoming provenance and reset lifecycle/snapshot. Event semantics and state-instance lineage must be explicit.

No additional battle-report research is required.

---

### S10-M02 · FIRST_AID RNG ownership and consumption order

**Classification:** `P1 DESIGN REQUIRED`

Authority is clear: one independent probability check per eligible damage event.

Design must freeze:

```text
eligibility gate order
source-skill inactive gate order
fatal-target gate order
RNG consumption point
RecoverEffect creation only after successful chance
```

All RNG must come from `context.random`.

No PRNG reverse-engineering is required for Stage10.

---

### S10-M03 · Recovery provenance extension

**Classification:** `P1 DESIGN REQUIRED`

Current `RecoverEffect / RecoveryRequest` preserve:

```text
source unit
source skill
source state
source state instance
```

Stage10 scope also asks to preserve source skill slot where applicable and operation lineage when recovery is coupled to a Stage9 damage operation.

Design must freeze whether to extend:

```text
RecoverEffect / RecoveryRequest
```

or keep operation lineage on the typed hook/result scope while state provenance remains on recovery.

The answer must remain backward-compatible with Stage7 RecoverySystem.

---

### S10-M04 · Source-skill temporary inactive gate

**Classification:** `P1 DESIGN REQUIRED`

FIRST_AID and RECUPERATION contracts observe temporary source-skill deactivation for applicable command/passive/troop sources.

Persistent states do not own the falsification/morale-shake mechanism itself, but Stage10 needs a typed query seam:

```text
is this source skill currently effective for this already-existing state instance?
```

Design must avoid copying external-control state into a second store.

No new falsification / morale-shake gameplay research is required in Stage10 unless the current runtime lacks an authoritative skill-active fact entirely.

---

### S10-M05 · Snapshot schema granularity

**Classification:** `P1 DESIGN REQUIRED`

Do not use an untyped `dict` snapshot.

Design must freeze typed application context sufficient for:

```text
strategy DOT
weapon DOT
REBELLION route + ignore defense
FIRST_AID treatment model
FIRST_AID damage-ratio model
RECUPERATION treatment model
```

The schema must distinguish:

```text
locked values
from
dynamic trigger-time gates
```

and avoid serializing unrelated UnitRuntime state.

---

### S10-M06 · Official state definition tags and Evidence Gate promotion

**Classification:** `P1 DESIGN REQUIRED`

The eight official definitions currently existed as DEFER targets in earlier stages.

Stage10 design must freeze:

```text
which official StateDefinition gets which typed runtime_params_type
which rule-hook tag(s) each state uses
which Stage7/8 evidence rows are promoted from DEFER because Stage10 authority is now frozen
```

Promotion must be explicit and auditable, not performed by simply registering a tag.

---

## 4. External dependencies / non-blocking

### S10-E01 · Evasion / Barrier official integration

Continuous-state contracts treat evasion/barrier as dynamic tick-time gates when present.

Stage8 currently keeps their official production bindings deferred.

Stage10 requirement:

```text
use the Stage8 hit-resolution seam
preserve compatibility for future official bindings
```

Stage10 must not implement the full official evasion/barrier state mechanics merely to close persistent-state integration.

**Blocking Stage10 research?** `NO`

**Blocking full cross-state integration test once those states are built?** `YES, for those future pairwise tests only`

---

### S10-E02 · Critical / strategy-critical official state integration

Persistent contracts lock applicable critical context at application.

The official critical states are outside the current Stage10 target set.

Stage10 must provide a typed snapshot seam that can receive critical context from the authoritative future source. Synthetic capability tests are allowed; claiming official critical-state integration is not.

**Blocking Stage10 core?** `NO`, provided the seam is represented and Evidence Gate remains honest.

---

### S10-E03 · Positive dispel

FIRST_AID / RECUPERATION positive-dispel behavior is unresolved/non-blocking in their contracts.

Stage10 must not guess universal positive-dispel semantics.

**Blocking?** `NO`

---

### S10-E04 · Command-aura source death

RECUPERATION associated with command aura may disappear on source death, but authority assigns ownership to the external command-aura lifecycle.

Stage10 must allow external authoritative removal of the state instance.

It must not place a generic source-death listener inside RECUPERATION.

**Blocking?** `NO`

---

### S10-E05 · FLOOD external delay / observers

Elephant Soldiers-style delay and skills that observe FLOOD or other continuous states are external mechanism behavior.

Stage10 must preserve state identity and typed queryability so those systems can interact later.

**Blocking?** `NO`

---

### S10-E06 · Cleanse skill selection logic

The negative continuous states are removable by purification, but Stage10 does not own which skill selects which removable status.

StateLifecycleSystem removal is sufficient as the mutation seam; cleanse policy remains external.

**Blocking?** `NO`

## 5. Research debt / non-blocking

### S10-RD01 · Same-node DOT vs RECUPERATION universal ordering

Authority observes both relative orders and explicitly does not freeze one universal family order.

Stage10 must therefore not manufacture one as an official claim.

A deterministic runtime iteration order may be frozen as an engineering rule if required.

**Blocking?** `NO`

---

### S10-RD02 · Microscopic formula constants

Exact non-linear formula constants for every source skill are outside the state-mechanism scope.

Stage10 runtime should model source-skill potency parameters as typed inputs and avoid pretending that one generic constant is official.

**Blocking?** `NO` for state runtime topology; individual skill fidelity may remain formula research work.

---

### S10-RD03 · Universal additional action-start generators

RECUPERATION contract notes no known official generator that gives more than the reachable action-start opportunities currently observed.

Stage10 should bind to actual typed action-start events, not hardcode “exactly once per round” as an intrinsic RECUPERATION counter.

**Blocking?** `NO`

## 6. Questions explicitly CLOSED by research

The following are **not** open anymore and must not be re-asked during Stage10 design unless new contradictory evidence appears:

```text
Q: Do continuous states snapshot source context?
A: YES, application/refresh context is locked according to each contract.

Q: Does source death cancel continuous damage?
A: NO.

Q: Does owner death allow a later DOT or FIRST_AID recovery?
A: NO, hard termination.

Q: Can same-name Stage10 states coexist as multiple effective instances?
A: NO, current authority freezes one effective instance + refresh/overwrite.

Q: Is REBELLION direct troop loss / true damage?
A: NO. It is weapon/strategy damage with relevant target defense ignored.

Q: Does REBELLION reroute when ATK/INT changes later?
A: NO. Route is locked at application/refresh.

Q: Is FIRST_AID once per round?
A: NO. It checks independently per eligible damage event.

Q: Do stun/disarm/silence inherently suppress these persistent ticks/recovery triggers?
A: NO under the frozen contracts.

Q: Does temporary source-skill inactive time pause finite RECUPERATION duration?
A: NO. Clock continues and missed opportunity is lost.

Q: Can Stage10 use Python random directly?
A: NO. Runtime RNG remains context.random.
```

## 7. Stage10 design admission gate

`STAGE10.md` may be authored only after it explicitly closes or assigns a frozen architecture answer to:

```text
S10-B01
S10-B02
S10-B03
S10-B04
S10-M01
S10-M02
S10-M03
S10-M04
S10-M05
S10-M06
```

`STAGE10_DESIGN_AUDIT.md` must reject the design if any of those remain ambiguous enough that two conforming implementers could produce observably different runtime behavior.

External/non-blocking items must remain visible and may not be silently promoted to Stage10-owned semantics.

## 8. Research closure verdict

```text
Gameplay-mechanism questions required for Stage10 core runtime: CLOSED
Additional battle-report research required before Stage10 design: NO KNOWN CORE BLOCKER
Architecture design blockers: 4
Architecture design required items: 6
External dependencies: 6
Non-blocking research debt: 3

STAGE10 RESEARCH PHASE = COMPLETE
NEXT PHASE             = STAGE10 ARCHITECTURE DESIGN
BUILD                   = NOT AUTHORIZED
```
