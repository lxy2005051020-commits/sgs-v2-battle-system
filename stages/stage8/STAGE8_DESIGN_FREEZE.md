# Stage 8 Design Freeze Record

> Project: 三国志战略版战斗模拟器 V2
>
> Repository: `lxy2005051020-commits/sgs-v2-battle-system`
>
> Scope: Stage 8 Damage Rule / Hit Resolution / Modifier Pipeline
>
> Status: `DESIGN FROZEN`

---

# 1. Freeze basis

Stage 8 v2 reviewed design commit:

```text
c4c61b71f7054c9473245c6542eb3551cc76f663
docs(stage8): revise design after first independent audit
```

Stage 8 Evidence Matrix commit:

```text
b13f97573a8863e38899c7cc4d37a96d8754ef6d
docs(stage8): add initial evidence matrix
```

Second independent design review verdict:

```text
BLOCKER   = 0
MAJOR     = 0
MINOR     = 2
HARDENING = 3

VERDICT = DESIGN READY
```

The second review confirmed that all first-review MAJOR findings `M-01 ~ M-07` were CLOSED.

The two remaining MINOR findings were limited to:

```text
1. numeric validation ownership should be made explicit
2. PipelineTrace stage execution state should use an explicit typed status
```

Neither finding changes Stage 8 pipeline topology, formula semantics, provider/binding architecture, modifier model, runtime dependency truth, event ownership, or Stage 8 / Stage 9 boundary.

Therefore no third full architecture review is required before design freeze.

---

# 2. Normative freeze-prep addendum

This file is a **normative addendum** to `STAGE8.md` at reviewed commit `c4c61b71f7054c9473245c6542eb3551cc76f663`.

If this file conflicts with the pre-freeze wording in `STAGE8.md` only on the two items below, this file takes precedence.

No other Stage 8 design contract is changed.

## 2.1 Public numeric boundary validation ownership

Stage 8 freezes the following rule:

```text
Every public numeric value entering the Damage Pipeline
must be validated before calculation, RNG consumption,
modifier application, event publication, or troop mutation.
```

Ownership is explicit:

```text
DamageRequest.coefficient
→ validated at DamageRequest construction boundary

DamageEffect.coefficient
→ validated at DamageEffect construction boundary

StateRuntimeParams probability / rate / operand
→ validated by the corresponding typed params construction boundary

non-State provider DamageModifierContribution.operand
→ validated at contribution construction/provider boundary

DamageModifierSystem operation output
→ validated immediately before it can feed the next contribution or finalization
```

For applicable numeric values:

```text
bool      → reject
NaN       → reject
+inf/-inf → reject
out-of-domain value → reject
```

For existing damage coefficients:

```text
finite
>= 0
bool rejected
```

For Stage 8 modifier output entering finalization:

```text
finite
>= 0
```

A shared, stage-neutral pure numeric validation helper is allowed, but it must contain no battle-rule semantics.

Internal calculation must not rely on accidental Python behavior such as:

```text
int(NaN)
int(inf)
bool behaving as int
NaN comparison quirks
infinite arithmetic propagation
```

to discover invalid inputs.

Invalid public numeric input must fail fast before RNG consumption and before any EventBus or troop side effect.

This hardening may only tighten previously undefined invalid-input behavior. It must not change any valid finite Stage 1-7 observable behavior.

## 2.2 Typed PipelineTrace stage execution status

Stage 8 freezes an explicit trace execution status:

```text
StageEvaluationStatus
- EXECUTED
- NOT_EVALUATED
```

`DamagePipelineTrace` must represent every stage using both a status and its typed result, conceptually:

```text
prevention_status: StageEvaluationStatus
prevention_result: DamagePermissionResult | None

hit_status: StageEvaluationStatus
hit_result: HitResolutionResult | None

formula_policy_status: StageEvaluationStatus
formula_policy_result: DamageFormulaPolicyResult | None

modifier_status: StageEvaluationStatus
modifier_result: DamageModificationResult | None
```

The following invariant is mandatory:

```text
status == EXECUTED
↔ result is not None

status == NOT_EVALUATED
↔ result is None
```

`pipeline_trace is None` has exactly one meaning:

```text
legacy/manual DamageResult without a Stage 8 trace
```

A canonical `DamageSystem.calculate()` result must always have a non-None `DamagePipelineTrace`.

For any valid DamageRequest entering the pipeline:

```text
prevention_status = EXECUTED
```

If an earlier stage short-circuits, every downstream stage must be explicitly `NOT_EVALUATED`.

Examples:

```text
weakness prevented
→ prevention = EXECUTED / PREVENTED
→ hit = NOT_EVALUATED / None
→ formula policy = NOT_EVALUATED / None
→ modifier = NOT_EVALUATED / None

barrier/evasion prevented
→ prevention = EXECUTED / ALLOWED
→ hit = EXECUTED / PREVENTED
→ formula policy = NOT_EVALUATED / None
→ modifier = NOT_EVALUATED / None

normal damage
→ all four stages = EXECUTED
→ all four typed results present
```

A fake identity result must never be created merely to make the trace appear complete.

`StageEvaluationStatus` is trace metadata only. It is not a rule trigger and must never be used by EventBus as a reverse execution signal.

---

# 3. Frozen Stage 8 architecture

The following Stage 8 topology is now frozen:

```text
DamageRequest
↓
participant validation
↓
StateDamageRuleProvider / binding adapter
↓
immutable DamageRuleCollection
↓
DamagePreventionSystem
↓
HitResolutionSystem
↓
DamageFormulaPolicySystem
↓
Frozen Base Formula
↓
coefficient
↓
DamageModifierSystem
↓
finalization
↓
DamageResult + DamagePipelineTrace
↓
DamageResolutionSystem
↓
TroopSystem
```

Frozen architecture contracts include:

```text
DamageSystem.calculate()
= unique theoretical-damage entry

DamageResolutionSystem
= unique theoretical-result → troop mutation / damage-event coordinator

TroopSystem
= unique troop mutation entry

runtime StateRegistry
= context.states only

runtime RNG
= context.random only

EventBus
= facts only, never a damage-rule engine

Stage 8 calculation systems
= no battle-fact publication

DamageResolutionSystem.apply_result()
= owner of DAMAGE_PREVENTED / DAMAGE_DEALT / existing UNIT_DEFEATED publication
```

The provider/binding boundary is also frozen:

```text
binding / adapter layer
MAY know concrete official state_id

core Prevention / Hit / FormulaPolicy / Modifier resolvers
MUST NOT dispatch on OfficialStateId
```

Synthetic rules must use the same provider/binding path as production rules.

---

# 4. Frozen formula boundary

Stage 8 freezes the typed formula-policy input described in `STAGE8.md`:

```text
DamageFormulaContext
    defense_policy: DamageDefensePolicy
```

The frozen base formula may only receive this through a backward-compatible keyword-only extension.

The normal path must remain exact-equivalent to Stage 7:

```text
formula_context=None
→ NORMAL
```

`IGNORE_RELEVANT_TARGET_DEFENSE` may only replace the target defensive contribution for the current calculation.

It must not create a second formula, mutate UnitRuntime, permanently mutate AttributeSystem, alter F(N), level scaling, troop scaling, troop counter, morale, frozen random-percent behavior, or low-damage floor behavior.

---

# 5. Frozen modifier model

The Stage 8 typed modifier model remains frozen as separate semantic axes:

```text
phase
kind
operation
operand/value
scope/filter
order
provenance
```

`kind`, `operation`, and `phase` must remain distinct concepts.

The absence of official stacking evidence must not be filled with guessed arithmetic.

The phase order remains an engineering determinism decision unless evidence proves an official order.

No empty `FINAL` phase is required in Stage 8 v1.

Damage-reduction pierce infrastructure may identify `INCOMING_REDUCTION`, but official pierce aggregation/stacking/rounding remains Evidence-Gated.

---

# 6. Evidence Gate at design freeze

Formal matrix:

```text
stages/stage8/STAGE8_EVIDENCE_MATRIX.md
```

Current production gate remains:

```text
weakness                  PASS_STAGE8

evasion                   DEFER
barrier                   DEFER
sure_hit                  DEFER
defense_pierce            DEFER
vigilance                 DEFER
critical                  DEFER
strategy_critical         DEFER
damage_reduction_pierce   DEFER
rebellion                 DEFER
```

`weakness` PASS means only migration of already-frozen observable behavior into the new prevention architecture.

It does not authorize new scope, stacking, source-type, consumption, or probability semantics.

A `DEFER` state may be represented by synthetic infrastructure tests, but it must not have an official production binding until its Matrix row becomes `PASS_STAGE8` from pinned evidence.

---

# 7. Stage 8 / Stage 9 boundary remains frozen

Stage 8 must not implement:

```text
Reaction Queue
AFTER_DAMAGE
first_aid
weapon_lifesteal
strategy_lifesteal
counterattack
cleave
damage split/share
chain link
guard
target redirect
taunt
confusion
combo
```

`DamageModifierSystem` must not:

```text
consume/remove state
restore troops
enqueue reaction
publish battle fact
create secondary DamageRequest
```

Those remain later-stage responsibilities.

---

# 8. Accepted non-blocking hardening

The second design review left three non-blocking hardening recommendations that may be implemented without reopening design:

```text
1. duplicate provider_key / order_key startup validation
2. architecture tests should validate typed resolver input boundaries, not rely only on string search
3. automated Evidence Matrix lint, including verdict whitelist and DEFER → no production binding
```

These are accepted implementation hardening items.

They do not alter the frozen Stage 8 architecture.

---

# 9. Reopening rule

Stage 8 DESIGN may only be reopened before implementation freeze if new evidence or implementation discovery requires a material change to one of the following:

```text
pipeline topology
provider/binding semantics
formula-policy semantics
modifier semantic model
runtime RNG / StateRegistry truth
DamageSystem constructor behavior
provenance contract
Event ownership
Stage 8 / Stage 9 boundary
Evidence Gate policy
```

Ordinary implementation choices such as helper placement, internal naming, file split, or test helper structure do not reopen design.

---

# 10. Freeze decision

Final design state:

```text
Stage 8
= DESIGN FROZEN
= implementation NOT STARTED
```

Next allowed workflow:

```text
STAGE8.md
+ STAGE8_DESIGN_FREEZE.md
+ STAGE8_EVIDENCE_MATRIX.md
↓
stages/stage8/STAGE8_BUILD_PROMPT.md
↓
Stage 8 implementation branch
↓
implementation
↓
pytest + demo + CI
↓
independent implementation audit
↓
fix / re-audit
↓
STAGE8_FINAL_AUDIT.md
↓
merge main
↓
main exact-head CI
↓
Stage 8 FROZEN
```

`DESIGN FROZEN` is not the same as implementation `FROZEN`.
