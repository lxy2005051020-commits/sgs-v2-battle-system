# Stage13-B3 Treatment Formula Runtime Freeze Audit

> Audit verdict: PASS
>
> Scope: ordinary treatment-rate formula core only
>
> Contract authority: `sgs-state-mechanics-research/STAGE13_B3_RECOVERY_FORMULA_MECHANISM_CONTRACT.md`
>
> Research contract merge: `40d5945231eddab138b0ad5a91bb6f071e029ed3`
>
> Runtime integration merge: `a27785a830e6d3f89b0c17d93bdaa31f84c48207`

## 1. Frozen runtime contract

The integrated ordinary-treatment lane is:

```text
H_nominal = CEIL(
    Rate
    * (F(N) + Attr)
    * SourceOrdinaryPool
    * TargetOrdinaryPool
    * RedPool
)
```

The audit confirms:

- `Rate` is the skill treatment ratio;
- `F(N)` uses the existing canonical repository troop-function lookup;
- the selected recovery attribute coefficient is exactly 1;
- ordinary modifiers on the same side combine algebraically;
- source-side and target-side ordinary pools compose multiplicatively;
- red-degree / advancement is an independent multiplier pool;
- ordinary treatment integerization is CEIL;
- persistent treatment formula inputs are replayed from application-time snapshot state;
- HealingBlock, execution prevention, wounded pool and missing-troop capacity remain live settlement-time owners.

## 2. Ownership audit

| Concern | Runtime owner | Verdict |
|---|---|---|
| ordinary treatment nominal formula | `TreatmentFormulaSystem` | PASS |
| canonical `F(N)` lookup | existing repository troop-function table | PASS |
| persistent formula snapshot payload | `RecoveryPotencyContext` | PASS |
| treatment opportunity formula dispatch | `RecoveryOpportunitySystem` | PASS |
| HealingBlock / prevention | `RecoverySystem` | PRESERVED |
| wounded / missing-troop clamp | `TroopSystem` via `RecoverySystem` | PRESERVED |
| damage-derived attacker recovery | `Stage11AttackerRecoverySystem` | PRESERVED / SEPARATE |

No duplicate wounded-capacity owner or recovery-settlement god object was introduced.

## 3. Regression discriminators

`tests/test_stage13_b3_treatment_runtime.py` proves:

1. same-side modifier algebraic pooling;
2. cross-side multiplication;
3. independent red pool;
4. CEIL rather than floor/round-half-up;
5. application-time persistent snapshot survives later live source troop/stat mutation;
6. incomplete ordinary-treatment snapshots fail closed.

Existing recovery, state, damage, wounded-pool and demo paths are covered by the full suite.

## 4. CI evidence

### Pull request validation

- PR: #36
- Head: `de9c23ec48bd7439dab9d0903bf9b89b2197afb4`
- Workflow run: `37200385546`
- Result: PASS
- Pytest: `1687 passed`
- Demo smoke test: PASS
- Independent audit snapshot upload: PASS

The preceding failed run `37200323337` was diagnosed as two invalid test fixtures that violated the pre-existing `BattleContext` two-team invariant. It reported `1685 passed, 2 failed`; no treatment-formula production assertion failed. The fixtures were corrected without modifying the formula implementation.

### Merged-main validation

- Runtime main merge: `a27785a830e6d3f89b0c17d93bdaa31f84c48207`
- Workflow run: `37200488246`
- Result: PASS
- Pytest: `1687 passed in 11.70s`
- Demo smoke test: PASS
- Independent audit snapshot upload: PASS

## 5. Historical-authority reconciliation

The earlier Stage13-B3 Round 2 empirical report inferred that living troops did not enter the nominal treatment formula and modeled skill-specific affine intercepts. That inference is retained as historical provenance but is explicitly superseded by the later contract authority.

Runtime must not reintroduce:

```text
Rate * (100 + INT)
Rate * (skill_constant + Attr)
```

as the generic ordinary-treatment formula.

## 6. Preserved boundaries

This audit does not claim that every recovery mechanic shares the ordinary-treatment formula. The following remain separately owned:

- explicit fixed recovery amounts;
- trigger-damage-ratio recovery;
- damage-dealt-ratio / lifesteal-like recovery;
- other separately frozen special recovery bases.

Likewise, this audit freezes the red-degree pool topology, not an otherwise unproven red-degree coefficient. Runtime consumes an authoritative multiplier supplied by the relevant advancement authority rather than inventing one.

## 7. Final verdict

```text
Stage13-B3 Ordinary Treatment Research Core = FROZEN
Stage13-B3 Ordinary Treatment Runtime       = FROZEN TO CONTRACT
PR CI                                       = PASS
Merged-main CI                              = PASS
G13-022 Ordinary Treatment Core             = CLOSED

Special Recovery Families                   = SEPARATELY BOUNDED / NOT COLLAPSED
Core Gameplay Engine                        = NOT YET FROZEN
Stage13 Complete                            = NO
Skill Runtime Readiness                     = NOT YET READY
```
