# Stage11 Runtime Adversarial Audit

Date: 2026-09-26  
Verdict: **PASS / RUNTIME FREEZE CANDIDATE ACCEPTED**  
Blocker: **B11-FRZ-001 — CLOSED**
Post-Freeze Acceptance: **PASS / FREEZE CONFIRMED**
Acceptance Audit: `STAGE11_POST_FREEZE_ACCEPTANCE_AUDIT.md`
Acceptance Audit SHA: `5a0a4164e7624c28eae2c7aa28f66061ef3c9313`
Acceptance CI: `36170063365`
Research post-acceptance mirror: `9ad990da544ad87047e74a664cc1984f890bb274`
Stage12 Activation Gate: **CLEARED**

## 1. Audit Snapshot

- Runtime-tested Battle SHA: `ce42bc62cfb26f8ca0b448e74b26533604bb0505`
- Research authority SHA: `80c4a9dd435b7ec1ed1baed1a957310159c1232a`
- GitHub Actions run: `36166160197`
- Workflow conclusion: `success`
- pytest: **913 passed / 0 failed / 0 skipped / 0 xfailed**
- demo smoke: **PASS**
- pre-freeze Research governance mirror: `0f2d8fab6899a9c179936dd4b1c8077f0c7d2b2d`

This re-audit supersedes the earlier 904-test blocked snapshot. The blocked record remains provenance for why B11-FRZ-001 existed; it is not the current verdict.

## 2. Canonical 17-state scope

`690086 DISTRIBUTION, 690090 FIRST_STRIKE, 690091 SURPRISE, 690102 DISARM, 690104 WEAKNESS, 690105 HEALING_BLOCK, 690111 STUN, 690082 EVASION, 690083 RESISTANCE, 690092 SURE_HIT, 690093 BREAK_FORMATION, 690099 ALERT, 690070 CRITICAL, 690069 STRATEGY_CRITICAL, 690221 DAMAGE_REDUCTION_PIERCE, 690094 LIFE_STEAL, 690095 STRATEGY_LIFE_STEAL`.

## 3. Authority reconciliation — PASS

The Share × attacker-recovery authority conflict is resolved by Research `STAGE11_SHARE_LIFESTEAL_AUTHORITY_RESOLUTION.md`.

Canonical rule:

```text
RecoveryBasis =
PrimaryAssignedDamage
+
SharedAssignedDamage
```

For the current conserved Share partition, this equals pre-Share finalized damage. It is not equivalent to committed actual troop loss when death or overkill truncates settlement.

Battle runtime at the audited SHA reads `DamageShareTransactionPlan.dtarget + dsharer_theoretical` for parent Share and Cleave-child Share. Dedicated tests cover normal nonlethal Share, target-death interruption, sharer/both-side overkill, per-source base CEIL, HealingBlock interception and STRATEGY lane mirroring. Legacy Cleave Share tests were migrated to the same authority.

Distribution remains separate: participant direct loss is excluded from LifeSteal basis under an explicit `PROJECT_RUNTIME_DEFAULT / RESEARCH_DEBT`.

## 4. Pipeline ordering audit — PASS

The Stage11 topology remains typed and ordered: critical-family decision, hit arbitration, formula policy, ordinary modifiers/reduction, See-Through transform, Weakness legal-zero, ALERT single-hit adjustment, central damage integerization, Stage9 partition/settlement, then attacker recovery.

No audit evidence was found that restores Weakness as an early-return prevention path, reruns Break base formula on a derived Cleave child, or gives Share direct troop loss a second LifeSteal trigger.

## 5. Action-control audit — PASS

- exact action-order ties are deterministic and consume no shuffle RNG;
- the approved Design Amendment 001 provides the legacy-context attacker-team fallback without claiming it as empirical game truth;
- STUN owns natural-action admission rather than generic RuleIntent suppression;
- DISARM owns standard NormalAttack admission; Counterattack is not routed through that gate;
- Combo #2 re-enters standard NormalAttack admission.

The legacy tests that contradicted these rules were migrated in the Stage11 implementation series and the full suite is green.

## 6. Recovery audit — PASS

The canonical pipeline is now executable:

```text
RecoveryBasis
↓
LifeSteal Ratio
↓
FIRST CEIL                    [Stage11AttackerRecoverySystem]
↓
Recovery Modifier
↓
SECOND CEIL                   [RecoverySystem]
↓
HealingBlock                  [RecoverySystem]
↓
Recovery Capacity             [TroopSystem.restore]
↓
Actual Recovered Troops
```

### B11-FRZ-001 Closure Record

```text
Status: CLOSED
Canonical owner: RecoverySystem
Pipeline position: after BaseRecovery, before HealingBlock and capacity
First CEIL owner: Stage11AttackerRecoverySystem
Second CEIL owner: RecoverySystem
Eligibility seam: RecoveryModifierPolicy
Modifier operand seam: RecoveryModifierProvider -> ExactRatio
Runtime-tested SHA: ce42bc62cfb26f8ca0b448e74b26533604bb0505
CI run: 36166160197
```

Required discriminator:

```text
CEIL(101 × 10%) = 11
CEIL(11 × 110%) = 13

single-stage would produce:
CEIL(101 × 10% × 110%) = 12
```

Dedicated tests:
- `test_recovery_modifier_double_stage_ceil_discriminator_101_10pct_110pct`
- `test_recovery_modifier_precedes_healing_block_without_zeroing_calculated_amounts`
- `test_recovery_modifier_precedes_capacity_clamp`
- `test_recovery_modifier_100_percent_does_not_add_one`
- `test_multiple_lifesteal_sources_each_own_first_ceil_and_reenter_modifier_stage`
- `test_strategy_lifesteal_uses_same_recovery_modifier_owner_and_second_ceil`
- `test_recovery_modifier_owner_applies_exact_second_ceil`
- `test_recovery_modifier_policy_none_preserves_generic_recovery_and_skips_provider`
- `test_zero_recovery_request_does_not_invoke_modifier_provider`

Share target-death / overkill regressions remain green. Actual troop loss does not leak back into Share RecoveryBasis. Cleave reuses the same attacker-recovery path and therefore the same RecoverySystem modifier owner. Distribution is unchanged and retains its explicit project default.

## 7. Persistent-damage audit — PASS

Stage10 persistent application/tick ownership remains intact. Stage11 does not move tick scheduling, application-bound frozen damage context, source-death handling, or recovery-opportunity ownership into a Stage11 state monolith. Full Stage7-10 regression is green.

## 8. RNG audit — PASS

Gameplay Stage11 randomness routes through `BattleContext.random`. The direct Python `random` implementation remains isolated in `RandomSystem`. Exact action-order ties consume no RNG.

## 9. Mutation-owner audit — PASS

Physical state mutation remains owned by `StateLifecycleSystem`. The Stage9 architecture regression `test_arch_07_ast_scan_state_registry_mutations_only_in_lifecycle_system` is green as part of the 904-test suite. Stage11 runtime façades request lifecycle mutations rather than becoming a second registry owner.

## 10. Integerization audit — PASS

- central damage integerization ownership: PASS;
- per-source LifeSteal first CEIL: PASS;
- RecoverySystem second CEIL: PASS;
- no float modifier path: PASS;
- no duplicate second-CEIL owner: PASS;
- modifier after first CEIL: PASS;
- HealingBlock after modifier: PASS;
- capacity after modifier: PASS;
- 100% modifier identity: PASS;
- multiple LifeSteal sources remain independently integerized: PASS;
- 690095 mirrors the same owner: PASS;
- ALERT / See-Through local-rounding prohibitions unchanged: PASS.

## 11. Zero-damage topology audit — PASS

Weakness is a resolved legal-zero damage result, not restored as Stage8 early prevention. Zero remains visible to the downstream topology required by Stage9/Stage10 while ALERT does not consume on the zero result.

## 12. Derived-damage audit — PASS

Cleave child DamageInstances retain independent partition assignment. Share-child recovery uses child assigned facts. The Share authority migration does not authorize critical rerolls or Break base-formula reruns.

## 13. Research-debt preservation audit — PASS

The audit preserves, rather than launders into “official truth”:
- 690086 Distribution / DSTS9-B02 research debt;
- Distribution × LifeSteal participant-loss exclusion as PROJECT_RUNTIME_DEFAULT;
- ALERT threshold equality, generic threshold origin, positive integerization, holder-death and Share micro-order boundaries;
- Critical/StrategyCritical exact micro-read / bonus-latch timing boundary;
- DISARM reflected/proxy admission boundary;
- See-Through unsupported damage families.

## 14. Stage7-10 regression audit — PASS

Run `36166160197` checked out Runtime-tested SHA `ce42bc62cfb26f8ca0b448e74b26533604bb0505` and completed:

```text
913 passed
0 failed
0 skipped
0 xfailed
demo PASS
```

Existing Share target-death / overkill, Cleave, Distribution and Stage7-10 lifecycle / recovery regressions remain green.

## 15. Stage12 scope-leak audit — PASS

No Stage12 runtime implementation is authorized or performed by this governance round.

## 16. Final verdict

```text
Stage11 Runtime: FROZEN
B11-FRZ-001: CLOSED
Stage12 Readiness: READY
Stage12 Active: NO
```

The remaining items are explicitly governed research debt / project runtime defaults, not missing required Runtime owners.

## 17. Cross-repository synchronization

Research authority remains `80c4a9dd435b7ec1ed1baed1a957310159c1232a`. Pre-freeze Research governance mirror is `0f2d8fab6899a9c179936dd4b1c8077f0c7d2b2d`.

After the Battle freeze declaration reaches `main`, Research must record:
- Battle Runtime Tested SHA;
- Battle Freeze Declaration SHA;
- Battle freeze record path;
- B11-FRZ-001 = CLOSED;
- Stage11 Runtime = FROZEN;
- Stage12 Readiness = READY.

