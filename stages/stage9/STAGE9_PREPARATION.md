# Stage 9 Preparation Audit

> Status: `PRE-DESIGN`
>
> This document is preparatory, not a frozen implementation contract.

## 1. Baseline lock

Stage 9 preparation starts from battle-repo `main` exact HEAD:

```text
660fefe2b92d19358772d8c221c072d58a7eb52c
```

That HEAD records Stage 8 as `FROZEN` and Stage 9 as `NOT STARTED / READY FOR DESIGN`.

Pinned state-mechanics research baseline observed for this preparation pass:

```text
repository: lxy2005051020-commits/sgs-state-mechanics-research
commit/tree: 7f1345681812864d4e34fae453bd69f766202c4c
```

No production code changes are authorized by this document.

---

## 2. Why Stage 9 needs a new orchestration layer

Current normal attack flow is intentionally linear:

```text
ActionSystem
→ NormalAttackSystem
→ TargetSystem.random_enemy
→ DamageResolutionSystem.calculate
→ NORMAL_ATTACK fact
→ DamageResolutionSystem.apply_result
→ TroopSystem
```

Current Stage 7 hook flow is also intentionally linear:

```text
RuleHookSystem
→ TriggerSystem.collect
→ EffectExecutor
```

Current `EventBus` is fact-only. It records and distributes facts that already happened; it must not become a hidden combat decision engine.

Stage 9 introduces mechanisms that break the one-input/one-output assumption:

```text
one action → another normal attack       (combo)
one normal attack → extra damage         (cleave)
one received normal attack → reaction    (counterattack)
one intended target → another target     (guard / taunt / confusion policy)
one damage result → multiple recipients  (damage_split / damage_share)
one damage occurrence → linked losses    (chain_link)
```

Therefore Stage 9 must design explicit orchestration rather than recursively calling existing systems from state-specific code.

---

## 3. Required design families

### 3.1 Target resolution / redirect policy

Stage 9 needs a typed target-resolution contract able to distinguish at least:

```text
candidate-set construction
forced target selection
random selection
post-selection interception / redirect
final resolved target
```

This distinction is required because the candidate states are not semantically identical:

```text
confusion = changes friend/foe eligibility during target selection

taunt = forces a normal attack toward the taunt source

guard = after a protected ally is selected, redirects the normal attack to the guard source

combo attack #2 = performs a fresh target-selection process rather than inheriting attack #1 target
```

The formal design must explicitly arbitrate interactions such as:

```text
confusion vs taunt
taunt vs guard
multiple taunt sources
multiple guard sources
guard-source death
battle termination between target intent and resolved execution
```

No ordering may be derived from incidental Python call order.

### 3.2 Action / reaction resolution queue

Stage 9 needs an explicit non-recursive resolution model for derived behaviors.

Candidate conceptual shape:

```text
Primary Action / Attack
↓
Resolve current operation completely
↓
Collect eligible derived operations
↓
Order them deterministically
↓
Enqueue typed operations
↓
Resolve next operation
```

The exact class names are not frozen, but the design must prevent:

```text
NormalAttackSystem.execute()
  → counterattack
    → NormalAttackSystem.execute()
      → counterattack
        → ...
```

Derived operations need provenance/lineage sufficient to answer:

```text
what created this operation?
which root action does it belong to?
what parent operation created it?
is it an ordinary standard normal attack or a special damage operation?
which observers are allowed to react to it?
```

### 3.3 Recursion and loop guard

A Stage 9 guard must be semantic, not a crude global depth integer alone.

The design must define at least:

```text
root resolution id
operation id
parent operation id
operation kind
reaction lineage
allowed / forbidden re-entry families
hard termination on battle end / actor death where applicable
```

Examples that must be representable without accidental recursion:

```text
normal attack → counterattack
normal attack → cleave
normal attack → guard redirect
combo attack #2 → normal attack observers
linked damage/loss → must not automatically create infinite chain-link propagation
```

Whether a specific derived operation may itself trigger another state is an evidence question, not an implementation convenience.

### 3.4 Damage fan-out / redirect contract

Stage 8 owns calculation of one `DamageRequest` through the frozen damage pipeline. Stage 9 must decide how a single logical incoming damage operation relates to multiple final recipients without silently changing that pipeline.

The design must distinguish:

```text
damage_split
= one original damage amount partitioned into multiple recipient shares

damage_share
= part of the original target's incoming damage transferred to another bearer

chain_link
= after damage occurs, linked targets receive calculated feedback loss / damage-family result
```

The formal contract must answer, per family:

```text
Does Stage 8 calculate once or once per recipient?
Is split/share based on requested final_damage or actual troop loss?
Does each recipient independently run prevention/hit/modifier logic?
Can redirected/derived damage trigger recovery, lifesteal, counterattack, cleave, or chain link?
What provenance is retained from the original DamageRequest?
How are rounding remainders assigned deterministically?
What happens if a recipient dies before its share resolves?
```

Until those answers are evidence-backed, official production bindings remain gated.

### 3.5 Deterministic ordering and RNG ownership

Stage 9 must preserve the project rule that combat randomness comes only from `RandomSystem`.

The design must explicitly define when RNG is consumed for:

```text
normal target selection
confusion-expanded target selection
combo second-attack re-targeting
multiple eligible redirect sources, only if evidence says random arbitration
any probability-bearing reaction
```

If a result is deterministic, no RNG may be consumed merely because a generic helper was called.

Derived operation order must use explicit policy fields / typed ordering rules. Instance-id sorting may be used only where the design explicitly declares it an engineering tiebreaker and where that choice cannot masquerade as an official rule.

### 3.6 Event ownership

`EventBus` remains fact-only.

Stage 9 may add factual events/traces such as candidate examples:

```text
TARGET_REDIRECTED
DERIVED_OPERATION_QUEUED
DERIVED_OPERATION_RESOLVED
DAMAGE_REDIRECTED
DAMAGE_SPLIT
REACTION_TRIGGERED
```

Names are not frozen. The important boundary is:

```text
resolution system decides
→ event system reports
```

not:

```text
event handler decides combat outcome
```

---

## 4. Evidence readiness findings

The research baseline is uneven.

### 4.1 Strongest candidate: combo / 连击

`combo` has a dedicated question-driven research set covering Q01-Q51 plus counterexample and cross-question consistency audits.

Key researched topology includes:

```text
attack #1 completes all downstream reactions
→ Extra Attack Checkpoint
→ dynamically read current combo state
→ enqueue/execute one independent standard normal attack
→ fresh target selection
```

The second attack is researched as a true standard normal attack whose normal observers can respond. The research also explicitly rejects recursive combo producing more than two physical normal attacks in one action window.

This makes `combo` suitable as the first design-driving reference state, subject to Stage 9 design audit and pinned evidence citation.

### 4.2 Remaining eight candidates

The currently inspected documents for the following remain `MINIMUM_USABLE` skeletons and explicitly defer material accuracy questions:

```text
cleave
counterattack
damage_split
damage_share
chain_link
guard
confusion
taunt
```

Typical unresolved fields include:

```text
precise event ordering
multi-source arbitration
formula / ratio
eligible source families
interaction with Stage 8 hit/prevention/modifier rules
redirect precedence
source death handling
```

These unresolved questions are architecture-relevant. They cannot be hidden behind implementation defaults.

---

## 5. Stage 8 frozen boundary audit

Stage 9 must treat these Stage 8 properties as upstream contracts:

```text
DamageRequest participant validation
StateDamageRuleProvider / immutable rule collection
damage prevention
hit resolution
formula policy
frozen base formula
coefficient
damage modifiers
finalization
DamageResult + DamagePipelineTrace
DamageResolutionSystem / TroopSystem ownership
```

A Stage 9 design may add an orchestration layer around requests/results, but must not silently reorder or reinterpret these frozen stages.

If a Stage 9 mechanism proves that Stage 8 lacks a required extension point, the preferred solution is:

```text
add an explicit compatible extension seam
```

not:

```text
rewrite Stage 8 semantics
```

Any true contradiction with a frozen Stage 8 contract requires a formal reopen finding.

---

## 6. Proposed Stage 9 design sequence

The next design pass should proceed in this order:

```text
1. Freeze operation taxonomy and lineage model
2. Freeze target-selection / forced-target / redirect topology
3. Freeze derived-operation queue and recursion guard
4. Freeze damage split/share/propagation boundary around Stage 8
5. Freeze deterministic ordering and RNG policy
6. Freeze death / battle-end short-circuit policy
7. Freeze events / trace / provenance
8. Map only evidence-qualified official states
9. Write STAGE9.md
10. Run independent design audit
```

This order is intentional. State mappings depend on the shared topology; the shared topology must not be reverse-engineered from nine state-specific `if` branches.

---

## 7. Preparation exit criteria

Stage 9 is allowed to move from `PRE-DESIGN` to formal design only when:

```text
[ ] operation / reaction vocabulary is defined
[ ] target arbitration questions are explicitly listed and evidence-gated
[ ] split/share/chain-link semantic questions are explicitly listed
[ ] recursion / loop prevention requirements are explicit
[ ] Stage 8 frozen boundary is preserved
[ ] every candidate state has a pinned evidence row
[ ] unknown official behavior is marked DEFER / RESEARCH_REQUIRED
[ ] no production code has been written prematurely
```

Current result:

```text
PREPARATION STRUCTURE = READY
EVIDENCE SET          = MIXED
FORMAL DESIGN         = NOT YET FROZEN
PRODUCTION CODE       = NOT STARTED
```
