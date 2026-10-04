# Stage13 Residual Mechanism Authority Amendment

> Status: FROZEN / RUNTIME MIGRATION INCLUDED
>
> Date: 2026-10-04
>
> Research mirror: `sgs-state-mechanics-research/STAGE13_RESIDUAL_MECHANISM_AUTHORITY_AMENDMENT.md`

## 1. 690221 See-Through

```text
ACTIVE_SKILL         = SUPPORTED_APPLICABLE
DOT / DELAYED_DAMAGE = SUPPORTED_APPLICABLE
```

Runtime mapping:

- `Stage11DamageFamily.ACTIVE_SKILL` -> applicable;
- `Stage11DamageFamily.PERIODIC_DAMAGE` -> applicable.

Both use the existing cap-before-pierce proportional transform.

## 2. 690099 Alert

```text
AlertThreshold = MaxCarryTroops × 6%
Trigger        = candidate_damage >= AlertThreshold
```

At 10,000 MaxCarry, 600 triggers. Runtime derives the threshold from `UnitRuntime.max_troops`; the old strict-`>` 600 project default is superseded.

## 3. Special recovery family separation

Special recovery families do not use the ordinary `Rate(F(N)+Attr)` nominal formula. Fixed recovery, damage-derived recovery/lifesteal, damage-taken-derived recovery, and other special bases remain separate implementations and may share only the authorized final RecoverySystem settlement tail.

## 4. 690086 Distribution DSTS9-B02

```text
commander participant dies
-> latch death / victory condition
-> continue current admitted DistributionTransaction
-> drain remaining participant commits
-> commit original target Dtarget
-> complete transaction
-> finalization barrier
-> battle end announcement
```

`DSTS9-B02 = CLOSED`. `DistributionTransactionPlan.runtime_authority` is promoted to `FROZEN_P0`.

## 5. Regression requirements

- ACTIVE_SKILL See-Through applicability;
- PERIODIC_DAMAGE See-Through applicability;
- ALERT 10k threshold: 599 false / 600 true / 601 true;
- ALERT non-10k threshold derived from MaxCarry;
- Distribution transaction authority defaults to FROZEN_P0;
- existing Stage9 finalization regressions remain green.
