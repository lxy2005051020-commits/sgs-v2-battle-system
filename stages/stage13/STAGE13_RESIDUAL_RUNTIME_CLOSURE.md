# Stage13-C Residual Runtime Closure

> Status: IMPLEMENTED ON FEATURE BRANCH / CI AUDIT PENDING
>
> Authority date: 2026-10-04
>
> Scope: runtime realization of residual mechanism decisions closed during Stage13-C.

## 1. 690221 See-Through applicability

Runtime now treats both of the newly closed families as applicable:

```text
ACTIVE_SKILL       -> SUPPORTED_APPLICABLE
PERIODIC_DAMAGE    -> SUPPORTED_APPLICABLE
```

`DamageSystem._stage11_pierce_rate()` already maps generic skill damage to
`ACTIVE_SKILL` and continuous damage to `PERIODIC_DAMAGE`; the Stage11
eligibility table now authorizes both routes.

## 2. 690099 Alert threshold

ALERT trigger eligibility is now derived from the holder's maximum carrying troops:

```text
threshold = target.max_troops * 0.06
trigger   = candidate_damage >= threshold
```

The historical `AlertStateParams.threshold` field is retained only for serialized
compatibility. Production eligibility no longer reads it.

## 3. 690086 Distribution commander participant death

The existing execution topology already drained all admitted participants before the
original target and only finalized after the active DamageInstance completed. The
runtime authority label is therefore promoted from `PROJECT_RUNTIME_DEFAULT` to
`FROZEN_P0`.

Canonical behavior:

```text
commander participant dies
-> latch victory/death fact
-> continue remaining admitted participants
-> commit original target Dtarget
-> complete DistributionTransaction
-> battle finalization
```

## 4. Special recovery family separation

`RecoveryModelKind.RESOLVED_SPECIAL_AMOUNT` is added as the explicit lane for
special recovery families whose own authority has already resolved a nominal amount.

It bypasses `TreatmentFormulaSystem` and enters only the shared RecoverySystem tail.

```text
family-specific special formula
-> resolved nominal amount
-> RESOLVED_SPECIAL_AMOUNT
-> RecoverySystem
-> HealingBlock
-> wounded / missing-troop capacity
```

This prevents fixed recovery, damage-derived recovery, troop-based recovery, or
other special families from being silently coerced through
`Rate(F(N)+Attr)`.

Legacy Stage10 callers that used `TREATMENT_AMOUNT + treatment_amount` remain
accepted as a compatibility seam; new special-family integrations must use the
explicit special lane.

## 5. Regression gate

Dedicated tests cover:

- See-Through ACTIVE_SKILL applicability;
- See-Through PERIODIC_DAMAGE applicability;
- ALERT 599/600 equality discriminator at MaxCarry 10,000;
- ALERT MaxCarry scaling outside 10,000;
- Distribution runtime authority promoted to FROZEN_P0;
- commander participant death does not abort the current DistributionTransaction;
- special resolved recovery bypasses ordinary treatment formula.

Final status becomes `RUNTIME FROZEN` only after branch CI and merged-main CI pass.
