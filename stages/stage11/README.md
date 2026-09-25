# Stage11 — State Runtime Integration

Status: **DESIGN FROZEN / RUNTIME FROZEN**

Canonical Project Scope: **17 states**

## Current snapshot

- Runtime Tested SHA: `a38b5150dec36f50b3aa21587a0c0c70397c17e0`
- Freeze Declaration SHA: `809f0c67b323ee2cca3cb30bc70375b33caacc14`
- Research Authority SHA: `80c4a9dd435b7ec1ed1baed1a957310159c1232a`
- CI run: `36166249971` — success
- pytest: **917 passed / 0 failed / 0 skipped / 0 xfailed**
- demo smoke: **PASS**
- Share × LifeSteal authority conflict: **RESOLVED**
- B11-FRZ-001: **CLOSED**
- Final Runtime Freeze: **FROZEN**
- Stage12 Readiness: **READY**
- Stage12 Active: **NO**

## Scope

`690086, 690090, 690091, 690102, 690104, 690105, 690111, 690082, 690083, 690092, 690093, 690099, 690070, 690069, 690221, 690094, 690095`.

## Governance navigation

- [Design Freeze Record](STAGE11_DESIGN_FREEZE_RECORD.md)
- [Design Amendment 001](STAGE11_DESIGN_AMENDMENT_001.md)
- [Runtime Integration Design](STAGE11_RUNTIME_INTEGRATION_DESIGN.md)
- [Implementation Ledger](STAGE11_IMPLEMENTATION_LEDGER.md)
- [Runtime Adversarial Audit](STAGE11_RUNTIME_ADVERSARIAL_AUDIT.md)
- [Runtime Freeze Record](STAGE11_RUNTIME_FREEZE_RECORD.md)
- [Historical Share × LifeSteal Reopen](STAGE11_SHARE_LIFESTEAL_AUTHORITY_REOPEN.md)
- Research authority: `sgs-state-mechanics-research/STAGE11_SHARE_LIFESTEAL_AUTHORITY_RESOLUTION.md`

## Recovery authority

Share recovery remains:

```text
RecoveryBasis =
PrimaryAssignedDamage
+
SharedAssignedDamage
```

Target death and overkill may reduce committed troop loss without reducing Share RecoveryBasis. Cleave child Share follows its own assignment-owned facts. Distribution remains separate research debt / project runtime default.

Recovery integerization is now:

```text
RecoveryBasis
→ LifeSteal ratio
→ FIRST CEIL
→ Recovery Modifier
→ SECOND CEIL
→ HealingBlock
→ recovery capacity
→ ActualRecoveredTroops
```

Ownership:
- `Stage11AttackerRecoverySystem`: basis, ratio, first CEIL.
- `RecoverySystem`: typed modifier eligibility, modifier application, second CEIL, HealingBlock.
- `TroopSystem.restore`: capacity clamp and troop mutation.

Discriminating regression:

```text
101 × 10% → 11
11 × 110% → 13
single-stage would be 12
```

## Regression result

The Runtime Freeze candidate passed **917 tests** and demo smoke on GitHub Actions run `36166249971`. Dedicated tests also cover HealingBlock ordering, capacity ordering, 100% identity, multi-source integerization, StrategyLifeSteal and Cleave reuse.

## Remaining debt

Research debt and bounded unknowns remain explicit, including Distribution/DSTS9-B02, Distribution × LifeSteal project default, ALERT boundaries, Critical timing, DISARM proxy/reflection admission and See-Through unsupported families. Runtime Freeze does not relabel these as empirical facts.

## Next stage

```text
Stage12 Readiness: READY
Stage12 Active: NO
```

Stage11 is complete. Stage12 may be started by a separate authorized task; this Freeze does not start Stage12 gameplay work automatically.
