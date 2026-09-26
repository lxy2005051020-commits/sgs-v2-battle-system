# Stage12 Runtime Default Ledger

Date: 2026-09-27
Status: OPEN / PARTIAL
Purpose: record only engineering choices that Runtime must make where Research does not freeze an original-game answer.

Every entry in this ledger is PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN unless explicitly stated otherwise.

This ledger is intentionally small. Round 2 does not pre-fill future unknowns merely to make the table look productive.

## RD-SF-001 — Legacy SkillDefinition classification compatibility

Mechanism: Shared Skill Taxonomy
Question: How should pre-Stage12 SkillDefinition instances be classified when the new metadata scaffold is introduced?
Research status: No historical-game claim. Existing Battle runtime currently routes SkillDefinition through an Active-skill-shaped SkillResolver.
Why Runtime must decide: adding mandatory classification without a migration rule would break existing constructors or silently change behavior.
Chosen Runtime default:

- legacy skill_type = ACTIVE
- legacy preparation_mode = NONE

Scope:

- compatibility for definitions created through the pre-Stage12 schema/API;
- newly authored Stage12 definitions should declare their classification explicitly.

Evidence classification:

PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN

Reopen trigger:

- discovery of an existing pre-Stage12 SkillDefinition that canonically represents a non-Active category;
- replacement of the legacy SkillResolver contract with a broader execution architecture.

Required tests:

- existing SkillDefinition behavior remains unchanged after schema scaffold;
- explicit non-Active metadata is not overwritten by the compatibility default.

## RD-SF-002 — Loaded Skill Provider enumeration order

Mechanism: Provider Identity / Enumeration
Question: What deterministic order does the registry expose for serializable loaded Skill Provider enumeration?
Research status: Intimidation proves eligible categories and random single selection, but does not prove server container order or selection weighting.
Why Runtime must decide: deterministic replay and serialization require stable enumeration independent of dict insertion history.
Chosen Runtime default:

Owner-local enumeration:
1. SkillSlot numeric order ascending: INHERENT 0, LEARNED_1 1, LEARNED_2 2.
2. skill_id as deterministic consistency tiebreaker.

If whole-battle enumeration is later needed, owner_id precedes slot in the canonical sort key.

Scope:

- identity enumeration only;
- does NOT define Intimidation selection weighting;
- does NOT prove uniform 1/N selection;
- does NOT decide empty eligible-pool behavior.

Evidence classification:

PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN

Reopen trigger:

- a later authoritative architecture establishes another canonical loadout order;
- Research exposes observable selection ordering that requires a different deterministic mapping.

Required tests:

- same registered providers enumerate identically regardless of insertion order;
- INHERENT slot 0 is retained and ordered before learned slots;
- duplicate owner/slot remains rejected.

## Explicitly not decided in Round 2

The following are not defaults yet:

- Intimidation uniform/equal selection probability.
- Intimidation empty eligible-pool behavior.
- Equipment/Bingshu eligibility for Intimidation.
- Provider-validity cycle fallback: no gameplay fallback is selected. Round 3 declares dependency cycles an explicit unsupported boundary that raises `DependencyCycleError`; this is not a PROJECT_RUNTIME_DEFAULT because no allow/deny value is invented.
- Any Stage13/14/15 execution behavior.

DQ-SF-14 remains CONTRACT_DEPENDENT / OPEN. The ledger now exists so later design choices have a lawful place to live.


## SF Round 3 default disposition — 2026-09-27

New Runtime Defaults added: **NONE**.

Round 3 deliberately avoids three fake defaults:

1. Suppression-cause ordering is semantically a set. Implementations may sort stable serialization keys for deterministic output, but order has no gameplay authority and is not a server-behavior claim.
2. Dependency cycles have no guessed gameplay answer. Evaluation/topology validation raises `DependencyCycleError`; no fixed-point, ALLOW, DENY, or “last writer wins” fallback is chosen.
3. Source death has no universal Provider/state invalidation default. A liveness dependency exists only when a contract/runtime record explicitly declares it.

Therefore RD-SF-001 and RD-SF-002 remain the only Shared Foundation Runtime Defaults after Round 3.

## RD-SF-003 — Same-envelope lifecycle settlement ordering

Mechanism: Shared State Lifecycle / Effectiveness Transition  
Question: If a state and one of its suppression sources are both due to leave in the same lifecycle envelope, does Runtime expose a transient resume before the due state is removed?

Research status: Insight freezes only the observable boundary that expiry / suppression-source removal settles before later behavior depending on the resulting privilege. It does not prove hidden function-level micro-order for two states due in the same envelope.

Why Runtime must decide: transaction/transition architecture needs a deterministic order and must avoid a due-to-expire state briefly regaining gameplay authority merely because its suppressor is removed first.

Chosen Runtime default:

1. Snapshot the complete set of states due for physical expiry/removal at the current lifecycle settlement envelope.
2. Commit that due-removal set in deterministic `instance_id` order.
3. Only after the due-removal batch is complete, recompute the affected StateEffectiveness / ProviderValidity dependency closure.
4. Invoke synchronous transition ports and permit later gameplay behavior.
5. A state included in the due-removal snapshot cannot emit/own a transient resume in that envelope.

Scope:

- same-envelope lifecycle settlement ordering only;
- does not change a contract's duration;
- does not define server-internal call order;
- does not authorize removal classes that a contract leaves bounded;
- deterministic `instance_id` ordering is a project serialization/observation choice, not original-game evidence.

Evidence classification:

`PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN`

Reopen trigger:

- model-separating evidence proves an observable transient resume in this exact same-envelope case;
- a later authoritative lifecycle contract freezes another externally visible order.

Required tests:

- state and suppressor both due in same envelope -> due state never transiently resumes;
- suppressor due but state remains live -> state resumes after due-removal batch;
- multiple due states settle deterministically without replay;
- no later gameplay behavior observes a pre-settlement privilege.

## SF Round 4 default disposition — 2026-09-27

New Runtime Defaults added: **RD-SF-003 only**.

No defaults are added for Provocation/Capture reapplication, Intimidation specialized removal/source death, FalseReport stronger/weaker conflict, Sabotage stronger different-source replacement, or unknown cleanse classes. Those remain explicit bounded/unsupported contract edges.
