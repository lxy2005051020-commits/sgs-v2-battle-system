# Stage11 Runtime Adversarial Audit — Authority Conflict

Verdict: **BLOCKED / RUNTIME NOT FROZEN**

Audit baseline: Battle `main` `b79019e5fcc56dbfad2abdd13a4ed592f9b4680c`; Research `main` `d1b6c74b352de373fb46c99b546e970eaaf1f77e`. The latest Battle `main` CI run at intake was [36147076741](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/actions/runs/36147076741), with 888 passed and 10 failed. A clean clone reproduced the same counts. This document records a targeted independent adversarial authority audit; it is not a full Stage11 runtime audit or a freeze record.

## Blocking counterexample: Cleave secondary Share × Life Steal

Two formally FROZEN research contracts require different recovery bases for the same event:

1. Research `states/functional/damage_share/MECHANISM_CONTRACT.md` sections 14, 23 and test requirement T12 say attacker 倒戈/攻心 reads the protected target's post-Share `Dtarget` only, excluding the sharer's direct loss. Battle Stage9 `STAGE9_FREEZE_RECORD.md` and `repairs/RF_P06_CLEAVE_DAMAGE_LAYER_AND_RECOVERY_BASIS_REFREEZE.md` repeat this for a Cleave secondary target.
2. Research `states/functional/life_steal/MECHANISM_CONTRACT.md` (Basis Resolution) says `ShareChainBasis = ActualPrimaryTroopLoss + ActualSharedTroopLoss`, with no second trigger. Its `FREEZE_AUDIT.md` confirms the sum. The frozen 690095 mirror contract carries the same rule into the STRATEGY lane.

Minimal discriminating event: a WEAPON Cleave secondary DamageInstance assigns 100 damage; Share splits it so the target actually loses 50 and the sharer actually loses 50; both survive; the attacker has one active 10% Life Steal source and at least 10 recoverable capacity. The 690087/Stage9 rule yields basis 50 and heal 5. The 690094 rule yields basis 100 and heal 10. Both cannot hold for that event. No explicit supersession, Design Reopen or cross-contract priority was found in either current `main`. The Stage11 design's choice of the sum does not itself revise the frozen Stage9/690087 authority.

There is a separate integerization conflict in the Stage9 RF-P06 secondary-Share vector: it expects `floor(267 × 0.10) = 26`, whereas frozen 690094 requires `ceil(267 × 0.10) = 27` even before resolving the basis conflict.

The existing nonlethal test `test_share_nonlethal_sharer_loss_is_excluded_from_recovery` exposes the basis conflict: actual target loss 267, actual sharer loss 47, runtime basis 314, legacy expected basis 267. Changing that assertion or runtime to make CI green would silently select one frozen authority. The overkill test is a separate stale assertion: target loss 55, pending sharer loss discarded, so neither frozen actual-loss rule supports its expected basis 267.

## Intake failure triage

| Failing test | Classification | Reason / required disposition |
|---|---|---|
| Stage4 exact-tier/speed shuffle | A OUTDATED_TEST_AUTHORITY | Frozen deterministic tie consumes no shuffle RNG. Migrate test. |
| Stage4 Weakness normal formula bypass | A OUTDATED_TEST_AUTHORITY | Frozen legal-zero requires a resolved hit and permits upstream formula. Migrate test. |
| Stage4 Weakness strategy formula bypass | A OUTDATED_TEST_AUTHORITY | Same; fixture must supply valid formula inputs. |
| Stage7 Weakness prevented-event provenance | A OUTDATED_TEST_AUTHORITY | Weakness now emits legal-zero damage, not `DAMAGE_PREVENTED`; preserve provenance in the new topology. |
| Stage8 default Weakness prevention binding | A OUTDATED_TEST_AUTHORITY | Weakness no longer belongs to the early prevention provider. |
| Stage8 Weakness formula/RNG short circuit | A OUTDATED_TEST_AUTHORITY | Same legal-zero contract; migrate assertions while checking RNG ownership. |
| Stage9 finite Combo duration × STUN | E TEST_FIXTURE_INVALID | The fixture expects two blocked natural actions but omits explicit `StunStateParams(remaining_blocks=2)`; frozen N=1 blocks one opportunity. Verify after fixture migration. |
| Stage9 Cleave Share overkill basis 267 vs 55 | A OUTDATED_TEST_AUTHORITY | Actual target loss is 55; target death discards pending sharer loss. |
| Stage9 Cleave Distribution basis `None` vs 50 | C RESEARCH_BOUNDARY_EXPOSED | Stage11 design records parent actual target loss 50 as `PROJECT_RUNTIME_DEFAULT`; participant loss remains research debt. Migrate with provenance after authority resolution. |
| Stage9 Cleave nonlethal Share basis 267 vs 314 | C RESEARCH_BOUNDARY_EXPOSED | Direct collision between frozen 690087/Stage9 and 690094/690095 contracts. Formal authority decision required. |

These are classifications, not fixes. No failing test was deleted, skipped, xfailed or weakened. The full suite is not green; demo smoke and the complete 20-point adversarial audit have not passed this gate.

## Required authority resolution

Research owners must explicitly reconcile 690087 with 690094/690095 for a Share chain, including Cleave secondary DamageInstances, actual-loss versus assigned-damage wording, overkill and target-death interruption, and CEIL versus the Stage9 RF-P06 FLOOR example. Record which clauses are superseded and update both frozen contracts and Stage9 freeze/vector authority through a formal reopen or equivalent project decision. Then update runtime/tests, rerun the full suite and demo, perform the complete independent runtime audit, and only then assess Runtime Freeze.

Until that decision: **Stage11 Runtime = BLOCKED; Stage12 = NOT READY**.
