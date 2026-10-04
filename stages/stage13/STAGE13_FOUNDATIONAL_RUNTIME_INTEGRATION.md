# Stage13 Foundational Runtime Integration — B1 / B2 / B2.5

Status: IMPLEMENTED / BRANCH REGRESSION PASS / INDEPENDENT MAIN FREEZE AUDIT PENDING  
Date: 2026-10-04

## 1. Scope

This integration implements only Stage13 foundational mechanics whose research is already closed enough to authorize runtime behavior:

- Stage13-B1 Wounded-Troop / Recoverable-Capacity mechanics;
- Stage13-B2 Damage Increase / Reduction aggregation mechanics;
- Stage13-B2.5 Full Damage Advancement directive and damage-pipeline reconciliation.

Stage13-B3 general treatment-value formula research is not frozen and is not implemented here.

## 2. Authority precedence

Where older B2 documents and the later B2.5 closure differ on advancement placement, the later B2.5 authority wins:

- attacker advancement: independent multiplier `1 + 0.02 * stars`;
- target advancement: independent multiplier `1 - 0.02 * stars`;
- only active when military books are active;
- advancement is not silently merged into ordinary skill modifier pools.

## 3. Runtime changes

### Wounded pool

`UnitRuntime` now carries explicit `wounded_troops`.

`TroopSystem` remains the sole troop-mutation owner and now owns:

- event-local generation: `floor(0.90 * actual_troop_loss)`;
- recovery capacity clamp: `min(requested, wounded_pool, missing_troops)`;
- 1:1 wounded-pool consumption by actual recovery;
- round-transition decay: `floor(0.90 * wounded_pool)`;
- defeat cleanup to zero as the Stage13-B1 canonical runtime default.

All damage paths already routing through `TroopSystem` inherit the same wounded logic, including standard damage and direct Share/Distribution losses. HealingBlock prevents settlement before pool consumption, so it preserves the physical wounded pool.

A migration-only compatibility seam exists for historical tests/snapshots that mutate `UnitRuntime.troops` directly. The first canonical `TroopSystem` operation claims wounded-pool authority; after that, missing troops are never reused as wounded truth.

### Damage modifier aggregation

`DamageModifierSystem.resolve_phases` now uses the frozen B2 topology:

- outgoing increase/reduction contributions are algebraically pooled on the outgoing side;
- incoming increase/reduction contributions are algebraically pooled on the incoming side;
- each side has an absolute `-90%` net floor, equivalent to a minimum multiplier of `0.10`;
- outgoing and incoming sides remain separate multiplicative layers;
- reduction pierce scales only the incoming-reduction component before net incoming composition;
- typed CRITICAL and SINGLE_HIT lanes remain distinct.

### Advancement

`UnitRuntime` now carries `advancement_stars` and `military_books_active`.

The production damage pipeline applies:

```text
F_adv_out = 1 + 0.02 * source_stars
F_adv_in  = 1 - 0.02 * target_stars
```

when military books are active.

For continuous damage, source advancement is snapshotted at application time together with source-side damage facts. Target advancement remains a live target-side defensive read at settlement, matching the latest B2.5 closure direction.

### Existing damage foundations preserved

The existing Stage2 base formula remains authoritative for:

- F(N) troop lookup;
- restraint multipliers 1.12 / 1.00 / 0.88;
- morale scaling;
- discrete random layer and low-damage floor.

The Stage13 integration does not invent a new base-damage formula.

## 4. Regression evidence

Branch checkpoint:

```text
head = 4cd32002d2f2283f28fe956c7300db7b44c8139a
GitHub Actions run = 37198006176
pytest = 1682 passed
demo = PASS
```

The pre-existing main baseline had one stale Stage13 route assertion failure before this work. That stale assertion was corrected as part of the Stage13 governance sync.

## 5. Preserved boundaries

Not closed or implemented by this integration:

- Stage13-B3 general treatment-rate / attribute-to-healing formula;
- 690086 DSTS9-B02 empirical Distribution debt;
- generic delayed-work infrastructure beyond already frozen mechanism-specific paths;
- any unnamed hidden damage term, because B2.5 promoted none.

## 6. Current verdict

```text
Stage13-B1 Runtime Integration   = IMPLEMENTED
Stage13-B2 Runtime Integration   = IMPLEMENTED
Stage13-B2.5 Runtime Integration = IMPLEMENTED

Branch Regression               = PASS
Independent PR/Main Audit       = PENDING
Core Gameplay Engine            = NOT YET FROZEN
Skill Runtime Readiness         = NOT YET READY
```
