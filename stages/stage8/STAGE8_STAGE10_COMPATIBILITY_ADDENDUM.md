# Stage 8 → Stage 10 Compatibility Addendum

> Project: 三国志战略版战斗模拟器 V2  
> Scope: Stage10 continuous-damage application snapshots  
> Status: `LIMITED COMPATIBILITY REOPEN / DESIGN ADDENDUM`  
> Production implementation: `NOT AUTHORIZED BY THIS DOCUMENT`
>
> `STAGE8_DESIGN_FREEZE.md` remains authoritative except for the clauses explicitly reopened here.

---

## 1. Original frozen contract

The Stage8 live theoretical-damage pipeline is:

```text
DamageRequest
→ participant validation
→ DamageRuleProvider.collect
→ DamagePreventionSystem
→ HitResolutionSystem
→ DamageFormulaPolicySystem
→ WeaponBaseDamageFormula / StrategyBaseDamageFormula
→ coefficient
→ DamageModifierSystem
→ final theoretical damage
→ DamageResult + DamagePipelineTrace
```

Current `LIVE_RUNTIME` also freezes:

```text
source exists and source.troops > 0
target exists and target.troops > 0
context.states is runtime rule truth
context.random is runtime RNG truth
DamageSystem.calculate is the unique standard theoretical-damage owner
```

The base formulas read current source combat facts and consume their existing random-percent / low-floor RNG. `DamageModifierSystem` may also consume RNG for probabilistic modifier contributions.

---

## 2. Stage10 conflict

Stage10 continuous-damage authority requires:

```text
application / refresh context = LOCKED_AT_APPLICATION
applicable source attributes   = LOCKED_AT_APPLICATION
applicable ordinary modifiers  = LOCKED_AT_APPLICATION
applicable crit context         = LOCKED_AT_APPLICATION
source death                    = existing state persists
weakness / evasion / barrier    = dynamic tick-time gates
```

Therefore the ordinary LIVE path is not sufficient. A tick may not:

```text
re-read current source offense
re-read current source troops/level/morale/troop type as formula-source facts
re-discover current ordinary source/target modifiers
re-roll an application-locked crit/modifier decision
reject solely because the historical source now has 0 troops
```

At the same time, Stage10 may not assume that “locked at application” means “precompute the complete final theoretical damage”.

R1-C therefore chooses a **frozen-input replay model**, not a final-`nominal_damage` model.

---

## 3. What is reopened

Only these Stage8 surfaces are reopened:

```text
1. DamageRequest calculation-basis discriminator
2. typed FROZEN_APPLICATION basis input
3. participant validation exception for authorized historical periodic sources
4. base-formula input adapter that accepts frozen source facts without UnitRuntime mutation
5. deterministic replay of application-resolved ordinary modifier / crit context
6. DamagePipelineTrace representation for frozen-input consumption
```

The following remain frozen:

```text
LIVE_RUNTIME behavior and arithmetic
normal source/target validation
DamagePreventionSystem ownership
HitResolutionSystem ownership
DamageFormulaPolicy semantic model
Weapon/Strategy base formula mathematical topology
coefficient position
DamageModifier semantic axes
DamageResult role
DamageResolutionSystem / Stage9 settlement boundary
TroopSystem mutation ownership
EventBus observation-only policy
Evidence Gate
```

No Stage10 implementation may use this addendum to change ordinary live damage.

---

## 4. Calculation-basis discriminator

Stage8 receives one typed calculation basis:

```text
DamageCalculationBasis
- LIVE_RUNTIME
- FROZEN_APPLICATION
```

Default is `LIVE_RUNTIME`, preserving every existing caller.

`FROZEN_APPLICATION` is legal only when all of the following hold:

```text
source_type == DamageSourceType.CONTINUOUS
source state provenance exists
application_generation_id exists
FrozenContinuousDamageBasis exists
historical source_id still identifies a unit in this BattleContext roster
```

It is forbidden for ordinary attacks, ordinary active skill damage, Counter, or any caller to use FROZEN_APPLICATION merely to bypass live-source validation.

---

## 5. Application-time producer

Stage8 gains one typed producer, conceptually:

```text
ContinuousDamageBasisProducer
.capture(context, ContinuousDamageApplicationRequest)
→ FrozenContinuousDamageBasis
```

It is a Stage8 service. It is **not** implemented inside `StateInstance`, `TriggerSystem`, EventBus, or a source-skill callback.

The producer runs only when the persistent state is successfully applied/refreshed and captures the application-time inputs that authority says must remain stable.

It does **not** execute a future tick and does **not** precompute the complete tick theoretical damage.

### 5.1 Frozen source formula facts

To reuse the current Weapon/Strategy formula without reading the mutable source `UnitRuntime`, the basis contains typed source-side formula facts equivalent to the current formula inputs:

```text
FrozenSourceFormulaFacts
- source_troops_at_application
- source_combat_attribute_at_application   # ATK or INT according to route
- source_level_at_application
- source_morale_at_application
- source_troop_type_at_application
```

These are immutable values, not a copied `UnitRuntime`.

Target-side base-formula facts are **not** silently added to the application snapshot. Under `NORMAL` defense policy the tick reads the current target formula facts; under `IGNORE_RELEVANT_TARGET_DEFENSE` the base-formula policy removes the relevant target defensive contribution. This is the narrowest model consistent with the authority's explicit application-time source/modifier/crit freeze.

### 5.2 Formula-policy result

The application producer resolves and freezes the formula-policy result for the state generation:

```text
DamageFormulaPolicyResult
→ NORMAL
or
→ IGNORE_RELEVANT_TARGET_DEFENSE
```

REBELLION therefore freezes its route and `IGNORE_RELEVANT_TARGET_DEFENSE` policy at application/refresh and the Stage8 consumer actually passes that policy into the base formula.

### 5.3 Coefficient / potency input

The source-skill-defined coefficient/potency parameter used by the Stage8 formula is frozen as a typed validated numeric value.

Exact source-skill formula constants remain outside Stage10 unless already authoritative; the runtime contract merely requires that the resolved parameter entering the basis is immutable and validated.

### 5.4 Ordinary modifier / crit plan

Application-time ordinary source/target damage modifiers are discovered through the Stage8 provider/binding architecture and converted into an immutable typed **resolved modifier plan**.

The plan contains only contributions that apply to this route/source type and stores, in deterministic Stage8 order:

```text
semantic kind
operation
validated operand
scope already resolved for this generation
provenance
whether a probabilistic/crit participation check was admitted at application
```

If an applicable ordinary modifier or crit contribution itself requires a probability decision, that participation decision is consumed **once at application/refresh** and the admitted/rejected result is frozen. It is not rolled again at each tick.

This clause does not promote CRITICAL / STRATEGY_CRITICAL official bindings. It only defines how an already-authorized future contribution is snapshotted.

---

## 6. `FrozenContinuousDamageBasis` V2 schema

R1-C replaces the Draft V1 `nominal_damage` schema.

Conceptually:

```text
FrozenContinuousDamageBasis
- application_generation_id: StateApplicationGenerationId
- historical_source: HistoricalDamageSourceRef
- damage_type: DamageType
- source_formula_facts: FrozenSourceFormulaFacts
- formula_policy_result: DamageFormulaPolicyResult
- coefficient: float
- locked_modifier_plan: FrozenDamageModifierPlan
- locked_crit_context: FrozenCritContext | None
- formula_producer_provenance: FormulaProducerProvenance
```

`HistoricalDamageSourceRef` contains typed identity/provenance, including:

```text
source_unit_id
source_skill_id | None
source_skill_slot | None
source_state_id
physical_state_instance_id
application_generation_id
```

The basis must contain **none** of:

```text
UnitRuntime
mutable StateInstance
callable / callback
untyped dict
EventBus handle
BattleSystems / service locator
```

Nested numeric/value objects own validation at construction. The outer basis validates type/domain relationships and cross-field invariants. This closes the Stage8 audit's numeric-validation ownership question.

---

## 7. Tick-time consumer

`DamageSystem` remains the unique theoretical-damage owner. It receives either live source facts or the frozen source facts through one internal formula-input abstraction; it does not clone the formulas.

Conceptual internal shape:

```text
DamageSystem.calculate(context, request)
  if basis == LIVE_RUNTIME:
      existing path exactly
  if basis == FROZEN_APPLICATION:
      validate authorized periodic provenance
      validate current target
      execute dynamic prevention
      execute dynamic hit resolution
      consume frozen formula-policy result
      execute the same Weapon/Strategy base-formula arithmetic
          source side = FrozenSourceFormulaFacts
          target side = current target formula facts
          formula RNG = current context.random at this tick
      multiply frozen coefficient
      apply frozen modifier plan deterministically, without modifier/crit reroll
      finalize
      return DamageResult + truthful trace
```

The base-formula implementation may be internally refactored into a pure typed input core so long as LIVE_RUNTIME golden tests prove exact equivalence. Mutating a `UnitRuntime` to impersonate historical source values is forbidden.

---

## 8. Per-layer matrix

Legend is normative:

```text
LIVE          = unchanged live Stage8 behavior
FROZEN INPUT  = immutable application-generation value is consumed
REUSED RESULT = typed application-time Stage8 result is reused
SKIPPED       = live stage is intentionally not executed on this lane
DYNAMIC       = evaluated at tick against current battle context
NOT APPLICABLE= layer does not participate
```

| Stage8 layer | LIVE_RUNTIME | FROZEN_APPLICATION | Owner / exact meaning |
|---|---|---|---|
| participant validation | LIVE | DYNAMIC | Stage8; target existence/alive is current. Historical source must exist in roster but source-alive check is skipped only for authorized periodic frozen basis. |
| source historical identity | LIVE | FROZEN INPUT | `HistoricalDamageSourceRef`; identity survives source death. |
| target alive validation | LIVE | DYNAMIC | current target must be alive before tick calculation. |
| Prevention | LIVE | DYNAMIC | current Stage8 prevention contributions; source Weakness remains tick-time. |
| Hit Resolution | LIVE | DYNAMIC | current hit topology; evasion/barrier future bindings remain Evidence-Gated. |
| Damage Formula Policy | LIVE | REUSED RESULT | application producer's typed `DamageFormulaPolicyResult`. |
| Base Formula | LIVE | DYNAMIC | same formula arithmetic at tick using frozen source facts + current target formula facts + existing base-formula RNG. |
| coefficient | LIVE | FROZEN INPUT | application-generation coefficient/potency input. |
| locked potency input | NOT APPLICABLE | FROZEN INPUT | typed source-skill application potency facts. |
| ordinary modifier | LIVE | FROZEN INPUT | resolved ordered application-time modifier plan; no live rediscovery and no tick reroll. |
| weakness | LIVE | DYNAMIC | current source Weakness gate; source death clears source states through defeat cleanup, it does not invalidate historical attribution. |
| crit | LIVE | FROZEN INPUT | application-time crit context/participation when an authorized binding exists. |
| RNG | LIVE | DYNAMIC | **only existing base-formula tick RNG is dynamic**. Modifier/crit participation RNG that belongs to locked context is already consumed at application and is not rerolled. |
| defense policy | LIVE | REUSED RESULT | frozen `DamageFormulaPolicyResult`; REBELLION consumes `IGNORE_RELEVANT_TARGET_DEFENSE`. |
| final theoretical result | LIVE | DYNAMIC | calculated each tick from the above unique inputs; not stored as Draft V1 `nominal_damage`. |
| DamageResult | LIVE | DYNAMIC | canonical Stage8 result generated for this tick. |
| PipelineTrace | LIVE | DYNAMIC | canonical tick trace plus typed frozen-application provenance described below. |

No cell is left to implementation discretion.

---

## 9. Historical-source validation

`LIVE_RUNTIME` remains exactly:

```text
source exists
source.troops > 0
target exists
target.troops > 0
```

`FROZEN_APPLICATION` is exactly:

```text
historical source_id exists in BattleContext roster
request is authorized PERIODIC_DAMAGE / CONTINUOUS
basis provenance matches state/generation provenance
target exists
target.troops > 0
```

It does **not** require historical source troops > 0.

The exception is scoped to this lane. It is not a general permission for dead units to attack.

---

## 10. Dynamic weakness after source death

The basis does not snapshot Weakness.

At tick time Stage8 asks the current rule provider for dynamic prevention facts. If the source is dead, Stage10 authoritative defeat cleanup has already removed the dead owner's attached states, so a former Weakness state is not resurrected from the frozen basis.

Thus:

```text
historical source attribution persists
!=
source runtime states persist
```

---

## 11. REBELLION contract

At application / refresh:

```text
choose route WEAPON or STRATEGY from authoritative application context
freeze route
freeze matching source formula facts
freeze matching ordinary modifier/crit context
resolve formula_policy_result = IGNORE_RELEVANT_TARGET_DEFENSE
```

At tick:

```text
route is not recomputed
opposite-family modifiers are not discovered
formula-policy result is reused
base formula consumes the ignore-defense policy
current relevant target defense contribution is therefore omitted
other authorized percentage factors come only from the frozen modifier plan
```

REBELLION remains ordinary WEAPON/STRATEGY damage identity, not DirectTroopLoss and not a third damage family.

---

## 12. DamagePipelineTrace representation

R1-C selects the **separate typed frozen trace field** model. The alternative `REUSED_FROZEN_INPUT` extension to the existing `StageEvaluationStatus` is rejected for this design.

Backward-compatible extension:

```text
DamagePipelineTrace
- existing prevention/hit/formula_policy/modifier status/result fields
- calculation_basis: LIVE_RUNTIME | FROZEN_APPLICATION
- frozen_application_trace: FrozenApplicationTrace | None
```

For `LIVE_RUNTIME`:

```text
calculation_basis = LIVE_RUNTIME
frozen_application_trace = None
all existing Stage8 status/result semantics unchanged
```

For `FROZEN_APPLICATION`:

```text
prevention_status / hit_status
→ truthfully report tick-time execution

formula_policy_status
→ NOT_EVALUATED at tick
modifier_status
→ NOT_EVALUATED at tick

frozen_application_trace
→ REQUIRED
→ records application_generation_id
→ formula_policy_result reused
→ source formula facts provenance
→ coefficient provenance
→ frozen modifier/crit plan provenance
→ application-time RNG decisions associated with locked modifier/crit context
```

The trace must never manufacture `EXECUTED` results for stages that were not executed at tick time.

The base-formula/finalization values remain visible through `DamageResult` and may be added to the frozen trace as typed numeric facts if needed, but the trace may not claim they were application-time calculated when they were not.

---

## 13. Evidence Gate boundary

This addendum does **not** promote:

```text
EVASION
BARRIER
CRITICAL
STRATEGY_CRITICAL
DAMAGE_REDUCTION_PIERCE
```

from Stage8 `DEFER` to production PASS.

Stage10 may use the existing typed topology and synthetic contributions to validate aftermath/frozen-input behavior, but official bindings require their own Evidence Gate promotion.

REBELLION's Stage10 promotion, when performed, is limited to the already-frozen persistent-state authority and its `IGNORE_RELEVANT_TARGET_DEFENSE` formula policy.

---

## 14. Backward compatibility obligations

Mandatory future implementation regression:

```text
LIVE_RUNTIME request corpus
→ exact same DamageResult values
→ exact same RNG consumption
→ exact same existing DamagePipelineTrace semantics

FROZEN_APPLICATION
→ no current source attribute/formula-source read
→ no current ordinary modifier rediscovery
→ no modifier/crit reroll
→ source-dead periodic tick remains legal
→ current target death still rejects calculation
→ dynamic weakness/hit gates still run
→ REBELLION defense policy is actually consumed by base formula
```

---

## 15. Compatibility verdict

```text
Stage8 original freeze                    = STILL AUTHORITATIVE
LIVE_RUNTIME                              = UNCHANGED GUARANTEE
FROZEN_APPLICATION                        = LIMITED NEW COMPATIBILITY LANE
Frozen model                              = INPUT SNAPSHOT / NOT FINAL NOMINAL DAMAGE
DamageSystem theoretical owner            = UNCHANGED
Base formula mathematical topology        = UNCHANGED
Evidence Gate                             = UNCHANGED
Production implementation                 = NOT AUTHORIZED
Independent Stage10 re-audit              = REQUIRED
```
