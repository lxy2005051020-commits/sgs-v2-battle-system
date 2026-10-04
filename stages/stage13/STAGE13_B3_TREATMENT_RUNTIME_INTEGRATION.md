# Stage13-B3 Treatment Formula Runtime Integration

> Status: IMPLEMENTED ON MAIN / MERGED-MAIN CI PASS / RUNTIME CORE AUDITED
>
> Contract authority: `sgs-state-mechanics-research/STAGE13_B3_RECOVERY_FORMULA_MECHANISM_CONTRACT.md`

## 1. Integrated ordinary-treatment formula

The runtime now owns the ordinary treatment-rate family as:

[
H =
leftlceil
Rate
	imes (F(N)+Attr)
	imes M_{source}
	imes M_{target}
	imes M_{red}
ightceil
]

Rules:

- `Rate` is the skill treatment ratio;
- `F(N)` reuses the repository's canonical troop-function table;
- selected recovery attribute coefficient is 1;
- same-side ordinary modifiers add algebraically;
- source-side and target-side pools multiply;
- red-degree / advancement remains an independent pool;
- integerization is CEIL.

## 2. Runtime ownership

### TreatmentFormulaSystem

New owner:

`sgs_v2/battle_core/treatment_formula.py`

Responsibilities:

- canonical `F(N)` lookup reuse;
- exact modifier-pool composition;
- final CEIL;
- no wounded-pool or HealingBlock ownership.

### RecoveryPotencyContext

Persistent recovery potency now carries application-time formula facts:

- source troops;
- selected source recovery attribute;
- source-side modifier deltas;
- target-side modifier deltas;
- independent red-pool multiplier.

The legacy `treatment_amount` lane remains an explicit already-resolved amount for compatibility and separately-owned recovery families.

### RecoveryOpportunitySystem

For `TREATMENT_AMOUNT` opportunities:

- explicit `treatment_amount` remains unchanged;
- rate-based ordinary treatment now calls `TreatmentFormulaSystem`;
- incomplete rate-based snapshots fail closed instead of inventing live reads.

## 3. Persistent-treatment snapshot boundary

The formula head is frozen at application:

```text
Rate
N
Attr
source ordinary pool
target ordinary pool
red pool
```

At later ticks, these values are replayed from `RecoveryPotencyContext`.

The settlement tail remains live:

```text
HealingBlock / execution prevention
current wounded pool
current missing troops
TroopSystem restore
```

This preserves Stage13-B1 capacity ownership and the Stage10 persistent-state lifecycle architecture.

## 4. Explicitly separate recovery families

The 2026-10-04 Stage13 authority freezes the family boundary: special recovery is **not ordinary treatment** and must be implemented through separate family owners.

The ordinary `Rate(F(N)+Attr)` lane does not reinterpret:

- fixed already-resolved recovery amounts;
- trigger-damage-ratio recovery;
- Stage11 damage-derived attacker recovery / lifesteal;
- other separately frozen recovery bases.

Separate families may reuse the final canonical RecoverySystem settlement tail only where their own contracts authorize it. They must not be routed through the ordinary-treatment nominal formula for implementation convenience.

## 5. Regression discriminators

`tests/test_stage13_b3_treatment_runtime.py` covers:

1. same-side algebraic pooling vs sequential multiplication;
2. source/target cross-side multiplication;
3. independent red pool;
4. CEIL integerization;
5. persistent application-time snapshot despite later live source changes;
6. fail-closed behavior for incomplete formula snapshots.

## 6. Verification and freeze boundary

Merged-main verification:

- main commit: `a27785a830e6d3f89b0c17d93bdaa31f84c48207`;
- GitHub Actions run: `37200488246`;
- workflow conclusion: `success`;
- test step: PASS;
- demo smoke test: PASS;
- independent audit snapshot: PASS.

Therefore the Stage13-B3 ordinary-treatment runtime core is frozen to the canonical contract.

This freeze applies only to the ordinary treatment formula family. It does not claim that every special recovery family in the game has been collapsed into this formula.
