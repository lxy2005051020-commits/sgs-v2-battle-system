# Stage13-B2.5 Full Damage Advancement & Hidden Mechanism Replan

> Status: CURRENT STAGE13 ROUTE AMENDMENT
>
> Effective: 2026-09-29
>
> Runtime code changes authorized: NO

## 1. Decision

Stage13-B1 wounded-troop research and Stage13-B2 damage-modifier research have reached frozen research verdicts. Before Stage13-B3 treatment-formula research, Stage13 inserts one focused damage-closure campaign:

```text
Stage13-B2.5
Full Damage Oracle — Advancement & Hidden Mechanism Closure
```

This campaign is not a wholesale reopen of B2 and is not a replacement for the existing Stage2 base-damage implementation.

## 2. Existing base-damage baseline

Stage2 already provides the repository's V1 reverse-engineered base-damage baseline:

- `NORMAL_ATTACK_FORMULA_V1.md`
- `STRATEGY_DAMAGE_FORMULA_V1.md`
- `sgs_v2/battle_core/weapon_damage_formula.py`
- `sgs_v2/battle_core/strategy_damage_formula.py`
- `data/normal_attack/troop_function_table_1_10000.csv`

The research campaign must reconcile this V1 baseline with the newer Stage13-B2 modifier authority. Runtime code is not evidence, but the existing implementation is the correct engineering baseline to validate rather than discard.

## 3. Official restraint authority

The project-confirmed original-game troop-restraint values are:

```text
ADVANTAGE    = 1.12
NEUTRAL      = 1.00
DISADVANTAGE = 0.88
```

The Runtime Stage2 weapon formula already uses these values. No gameplay code change is needed for this correction.

## 4. Primary unresolved damage question

The principal remaining arithmetic question is advancement modifier placement:

```text
same-pool outgoing:
  1 + ΣOI + E_out - ΣOD

independent outgoing:
  (1 + ΣOI - ΣOD) * (1 + E_out)

same-pool incoming:
  1 + ΣII - ΣID - E_in

independent incoming:
  (1 + ΣII - ΣID) * (1 - E_in)
```

Q43 and Q45 enter this campaign as METHOD_GATE. The research goal is to discriminate these models with high-separation battle-report cases and full-event replay.

## 5. Hidden-mechanism residual gate

After applying the Stage2 V1 base formula, Stage13-B2 frozen modifier rules, and official restraint values, every clean damage event must be replayed.

For an unobserved discrete RNG draw, compare the observed value against the full legal candidate set. Define:

```text
event_error = minimum absolute distance to any legal predicted candidate
```

Then:

```text
0  = EXACT
1  = acceptable integerization boundary
>1 = ANOMALY / investigation required
```

Repeated clean residual clusters may spawn focused hidden-mechanism research. They may not be dismissed as generic RNG unless the observed value is actually reachable by the documented RNG model.

## 6. Current Stage13 sequence

```text
Stage13-A    Inventory Audit                              COMPLETE
Stage13-B1   Wounded / Recoverable Capacity               FROZEN
Stage13-B2   Damage Increase / Reduction                  FROZEN
Stage13-B2.5 Full Damage Advancement / Hidden Mechanisms  ACTIVE / NEXT
Stage13-B3   Recovery / Treatment Formula                 AFTER B2.5
Stage13-C    Residual State Mechanism Closure             AFTER B3
Stage13-D+   Runtime governance / design / implementation AFTER research gates
```

## 7. Runtime boundary

During Stage13-B2.5:

```text
sgs_v2/battle_core/* gameplay changes = FORBIDDEN
research tooling / offline replay       = ALLOWED
governance documentation                = ALLOWED
```

Only a later explicit Stage13 implementation authorization may change production runtime behavior.
