# Stage13 Residual Mechanism Runtime Integration

> Status: IMPLEMENTED ON MAIN / CI AUDIT PENDING
>
> Date: 2026-10-04

## 1. Scope

This integration applies the final Stage13 residual mechanism authority amendments without reopening already-frozen owners.

Implemented authority changes:

- 690221 SEE_THROUGH applies to ACTIVE_SKILL damage;
- 690221 SEE_THROUGH applies to PERIODIC / DOT damage;
- 690099 ALERT threshold is MaxCarryTroops × 6%;
- 690099 ALERT triggers on equality;
- 690086 DISTRIBUTION commander-participant death drains the current DistributionTransaction before battle finalization;
- special recovery families remain separate from ordinary FB1 treatment and use dedicated/pre-resolved recovery lanes.

## 2. Runtime changes

### 2.1 690221 See-Through

`Stage11StateRuntime.see_through_eligibility()` now classifies:

```text
ACTIVE_SKILL     -> SUPPORTED_APPLICABLE
PERIODIC_DAMAGE  -> SUPPORTED_APPLICABLE
```

The existing `DamageSystem._stage11_pierce_rate()` already maps continuous damage to `PERIODIC_DAMAGE` and non-special skill damage to `ACTIVE_SKILL`, so no parallel pierce owner was introduced.

### 2.2 690099 Alert

`Stage11StateRuntime.alert_threshold(max_carry_troops)` owns the generic threshold:

```text
threshold = max_carry_troops × 6%
trigger   = candidate_damage >= threshold
```

The historical `AlertStateParams.threshold` field remains only for serialized/backward compatibility and is no longer runtime authority.

### 2.3 690086 Distribution

`DistributionTransactionPlan.runtime_authority` now defaults to `FROZEN_P0` rather than `PROJECT_RUNTIME_DEFAULT`.

The settlement loop already had the correct transaction semantics:

```text
participant death
-> observe death / latch victory if applicable
-> continue remaining participant commits
-> commit original target Dtarget
-> finish DistributionTransaction
-> only then reach battle finalization barrier
```

No behavioral rewrite was required; only the authority provenance was upgraded.

### 2.4 Special recovery family isolation

Ordinary FB1 treatment remains:

```text
CEIL(Rate × (F(N)+Attr) × SourcePool × TargetPool × RedPool)
```

Special recovery families do not enter `TreatmentFormulaSystem`. Existing dedicated owners may provide a pre-resolved `treatment_amount` or their own recovery basis and share only the separately-authorized RecoverySystem settlement tail.

## 3. Regression coverage

Added/extended tests cover:

- ACTIVE_SKILL See-Through applicability;
- PERIODIC/DOT See-Through applicability;
- 10,000 MaxCarry -> 600 ALERT threshold;
- non-10k MaxCarry threshold derivation;
- inclusive equality boundary;
- Distribution authority promoted to FROZEN_P0;
- pre-resolved special recovery bypasses ordinary treatment formula inputs.

## 4. Freeze boundary

This integration does not invent formulas for special recovery families. Their basis math remains owned by their dedicated contracts.

CI status will be updated after merged-main validation.
