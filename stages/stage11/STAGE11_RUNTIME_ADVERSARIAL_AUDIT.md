# Stage11 Runtime Adversarial Audit

Date: 2026-09-26  
Verdict: **PASS / RUNTIME FROZEN**  
Former blocker: **B11-FRZ-001 — CLOSED**

## 1. Audit Snapshot

- Runtime Tested SHA: `a38b5150dec36f50b3aa21587a0c0c70397c17e0`
- Freeze Declaration SHA: `809f0c67b323ee2cca3cb30bc70375b33caacc14`
- Research Authority SHA: `80c4a9dd435b7ec1ed1baed1a957310159c1232a`
- GitHub Actions run: `36166249971`
- workflow conclusion: `success`
- pytest: **917 passed / 0 failed / 0 skipped / 0 xfailed**
- demo smoke: **PASS**

This audit supersedes the prior 904-test BLOCKED snapshot.

## 2. Canonical 17-state scope

`690086 DISTRIBUTION, 690090 FIRST_STRIKE, 690091 SURPRISE, 690102 DISARM, 690104 WEAKNESS, 690105 HEALING_BLOCK, 690111 STUN, 690082 EVASION, 690083 RESISTANCE, 690092 SURE_HIT, 690093 BREAK_FORMATION, 690099 ALERT, 690070 CRITICAL, 690069 STRATEGY_CRITICAL, 690221 DAMAGE_REDUCTION_PIERCE, 690094 LIFE_STEAL, 690095 STRATEGY_LIFE_STEAL`.

## 3. B11-FRZ-001 closure — PASS

Canonical recovery pipeline is now executable:

```text
RecoveryBasis
→ LifeSteal / StrategyLifeSteal ratio
→ FIRST CEIL
→ typed RecoveryRequest
→ Recovery Modifier
→ SECOND CEIL
→ HealingBlock
→ recovery capacity
→ ActualRecoveredTroops
```

Semantic owners:
- `Stage11AttackerRecoverySystem`: RecoveryBasis, per-source ratio, first CEIL.
- `RecoverySystem`: typed modifier eligibility, modifier operand, second CEIL, HealingBlock ordering.
- `TroopSystem.restore`: final capacity clamp and troop mutation.

The modifier seam uses `ExactRatio`; no float integerization path was introduced.

## 4. Discriminating rounding audit — PASS

Test `test_recovery_modifier_double_stage_ceil_discriminator_101_10pct_110pct` proves:

```text
CEIL(101 × 10%) = 11
CEIL(11 × 110%) = 13

forbidden single-stage:
CEIL(101 × 10% × 110%) = 12
```

The test asserts 13, so a single-stage implementation cannot pass accidentally.

A 100% modifier test proves identity without an off-by-one. Multiple-source tests prove each source independently enters both integerization stages.

## 5. HealingBlock / capacity ordering — PASS

HealingBlock is evaluated after the modifier stage. Under the 101 / 10% / 110% fixture, the Runtime preserves:
- RecoveryBasis = 101;
- BaseRecovery = 11;
- ModifiedRecovery = 13;
- ActualRecoveredTroops = 0 under HealingBlock.

Capacity is later still: when ModifiedRecovery is 13 and only 7 troops are recoverable, ActualRecoveredTroops is 7 while calculated ModifiedRecovery remains 13.

Generic Stage10 recovery requests default to modifier-ineligible. No unsupported FirstAid/Recuperation modifier behavior was inferred.

## 6. Share × LifeSteal — PASS

Authority remains:

```text
RecoveryBasis =
PrimaryAssignedDamage
+
SharedAssignedDamage
```

Target death, primary overkill and Share-receiver overkill do not shrink RecoveryBasis. Committed actual loss does not leak back into basis construction. Share direct troop loss creates no second LifeSteal trigger.

## 7. Cleave — PASS

Cleave attacker recovery reuses `Stage11AttackerRecoverySystem` for the first CEIL and the same canonical `RecoverySystem` modifier owner for the second CEIL. No Cleave-local recovery-modifier arithmetic exists.

## 8. StrategyLifeSteal — PASS

690095 follows the STRATEGY lane and reuses the same modifier owner and double-stage CEIL contract as 690094. No separate Strategy modifier implementation exists.

## 9. Distribution debt preservation — PASS

No 690086 Runtime or Research authority was modified. Distribution participant direct loss remains excluded from the LifeSteal basis under the existing `PROJECT_RUNTIME_DEFAULT / RESEARCH_DEBT`.

## 10. RNG audit — PASS

The repair introduces no new RNG calls. No `random`, `shuffle`, `choice` or `randint` owner was added. Existing Stage11 randomness remains routed through `BattleContext.random`.

## 11. Mutation-owner audit — PASS

The repair adds no direct `StateRegistry` mutation. `StateLifecycleSystem` remains the physical mutation owner. RecoverySystem reads HealingBlock state and delegates troop mutation to TroopSystem.

## 12. Integerization-owner audit — PASS

- LifeSteal first CEIL has one semantic owner: `Stage11AttackerRecoverySystem`.
- Recovery modifier second CEIL has one semantic owner: `RecoverySystem`.
- The attacker recovery caller does not apply the recovery modifier.
- RecoverySystem does not recompute the first LifeSteal CEIL.
- modifier-ineligible requests bypass the modifier provider.
- zero eligible requests do not invoke the modifier provider.

## 13. Other Stage11 topology — PASS

No changes were made to:
- Weakness legal-zero topology;
- action-order ownership;
- STUN natural-action admission;
- DISARM NormalAttack admission;
- Critical / StrategyCritical routing;
- Break Formation formula ownership;
- See-Through operand transformation;
- ALERT ordering;
- Stage9 partition ownership;
- Stage10 persistent-state scheduling.

The full 917-test regression and demo smoke are green.

## 14. Preserved research debt

Still explicit:
- 690086 Distribution / DSTS9-B02 research debt;
- Distribution × LifeSteal project default;
- ALERT threshold equality / generic threshold / positive integerization / holder-death / Share micro-order boundaries;
- Critical / StrategyCritical exact micro-read and bonus-latch timing;
- DISARM reflected/proxy admission boundary;
- See-Through unsupported damage families.

These are governed residual boundaries, not Freeze blockers.

## 15. Final verdict

```text
B11-FRZ-001: CLOSED
Stage11 Runtime: FROZEN
Stage12 Readiness: READY
Stage12 Active: NO
```
