# Stage13 Foundational Runtime Freeze Audit — B1 / B2 / B2.5

Status: PASS  
Date: 2026-10-04  
Scope: Stage13 foundational runtime slice only

## 1. Verdict

```text
Stage13-B1 Wounded / Recoverable Capacity Runtime = FROZEN TO INTEGRATED CONTRACT
Stage13-B2 Damage Modifier Runtime                 = FROZEN TO INTEGRATED CONTRACT
Stage13-B2.5 Advancement Runtime                  = FROZEN TO PROJECT DIRECTIVE

Independent PR CI                                 = PASS
Merged-main CI                                    = PASS
Core Gameplay Engine                              = NOT YET FROZEN
Stage13 Complete                                  = NO
Skill Runtime Readiness                           = NOT YET READY
```

This audit freezes only the Stage13 foundational slice already implemented. It does not declare the entire Stage13 engine complete.

## 2. Authorities consumed

- Stage13-B1 wounded-troop mechanism contract and freeze audit;
- Stage13-B2 damage-modifier mechanism contract and post-freeze restraint correction;
- Stage13-B2.5 full-damage closure verdict;
- existing Stage2 base-damage formula authorities;
- existing Stage11 critical / reduction-pierce / recovery ownership contracts.

Where B2 and B2.5 differ on advancement placement, the later B2.5 independent-multiplier directive is authoritative for Runtime.

## 3. Frozen runtime behavior

### B1

- explicit per-unit wounded pool;
- event-local `floor(0.90 * actual_loss)` generation;
- actual-loss basis after overkill truncation;
- `min(nominal, wounded_pool, missing_troops)` recovery capacity;
- 1:1 wounded-pool consumption by actual recovery;
- `floor(0.90 * W)` round-transition decay;
- no action-boundary decay;
- HealingBlock preserves pool contents;
- defeat clears recoverable capacity as the canonical runtime default;
- all troop-loss paths routed through `TroopSystem` inherit the same rule.

### B2

- ordinary outgoing increases/reductions form one algebraic outgoing pool;
- ordinary incoming increases/reductions form one algebraic incoming pool;
- each side is clamped to a minimum net modifier of `-90%`;
- outgoing and incoming sides compose multiplicatively;
- reduction pierce affects only the incoming-reduction component;
- fixed-value reduction is a typed post-multiplier subtraction and may produce zero damage;
- restraint remains `1.12 / 1.00 / 0.88`;
- morale and Stage2 base formula remain unchanged;
- final theoretical assigned damage and actual troop loss remain separate.

### B2.5

- attacker advancement multiplier: `1 + 0.02 * stars`;
- target advancement multiplier: `1 - 0.02 * stars`;
- advancement is active only when military books are active;
- advancement is independent of ordinary skill modifier pools;
- continuous-damage source advancement is snapshotted at application;
- target-side advancement remains a live defensive read at settlement;
- zero unnamed hidden damage terms were promoted.

## 4. Preserved unknowns and debts

The following remain open and are not silently implemented:

- Stage13-B3 exact general treatment formula;
- B3-Q1/Q2/Q3 exact nominal treatment mapping;
- B3 modifier stacking/cap/integerization questions that remain open or partial;
- 690086 DSTS9-B02 empirical Distribution debt;
- unresolved 690221 residual family applicability;
- generic delayed-work infrastructure beyond existing frozen mechanism-specific paths.

B3 subrules already independently frozen upstream, such as capacity clamp, overheal truncation and defeated-unit recovery prohibition, are satisfied by the B1/RecoverySystem integration. Partial Round-2 formula findings are not promoted into production constants.

## 5. Regression evidence

### Pre-merge branch

```text
head = cb231a17de88430eb0095f5fd0ddc07e3d6e12a8
PR = #34
PR CI run = 37198293256
pytest = 1683 passed
demo = PASS
```

### Merged main

```text
merge SHA = d4eea5b0d4725336777e7b0ecb131c7f55d3dca2
main CI run = 37198353900
pytest = 1683 passed
demo = PASS
```

The pre-integration main baseline had one stale Stage13 route assertion failure. That governance-only failure was corrected; no runtime regression remains in the merged main suite.

## 6. Exit statement

```text
FOUNDATIONAL_RUNTIME_FREEZE_AUDIT = PASS
BLOCKER = 0
unresolved MAJOR in integrated slice = 0

Stage13-B1/B2/B2.5 runtime slice = FROZEN
Stage13 overall                  = ACTIVE
NEXT                             = continue unresolved Stage13 research and core-engine completion
```
