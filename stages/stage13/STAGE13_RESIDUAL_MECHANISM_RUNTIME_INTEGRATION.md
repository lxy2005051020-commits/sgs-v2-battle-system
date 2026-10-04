# Stage13 Residual Mechanism Runtime Integration

> Status: IMPLEMENTED ON MAIN / MERGED-MAIN CI PASS / RUNTIME SLICE FROZEN
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

Special recovery families do not enter `TreatmentFormulaSystem`. `RecoveryModelKind.SPECIAL_RECOVERY_AMOUNT` is the explicit typed lane for a dedicated special-family owner to hand a pre-resolved amount into the shared RecoverySystem settlement tail. Family-specific basis math remains separately owned.

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

Merged-main validation:

```text
Commit              = 43c5b4e335895b0fb2c21fe49875480f49158206
GitHub Actions Run  = 37206514602
pytest              = 1691 passed
demo smoke          = PASS
audit snapshot      = PASS / uploaded
workflow conclusion = SUCCESS
```

Freeze verdict:

```text
690221 ACTIVE_SKILL applicability runtime = FROZEN TO CONTRACT
690221 DOT/PERIODIC applicability runtime = FROZEN TO CONTRACT
690099 6% inclusive threshold runtime     = FROZEN TO CONTRACT
690086 DSTS9-B02 runtime authority        = FROZEN_P0
Special recovery family isolation        = FROZEN AS ARCHITECTURAL BOUNDARY
```

This does not freeze the internal basis formula of every special recovery family; those remain dedicated family/skill contracts.
