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
- Provider-validity cycle fallback.
- Any Stage13/14/15 execution behavior.

DQ-SF-14 remains CONTRACT_DEPENDENT / OPEN. The ledger now exists so later design choices have a lawful place to live.
