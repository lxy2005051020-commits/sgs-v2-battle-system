# Stage11 Share × Life Steal Authority Reopen

Date: 2026-09-25  
Current status (updated 2026-09-26): **RESOLVED / PROVENANCE ONLY**

This file preserves the historical formal reopen that exposed contradictions between Stage9/690087 target-only recovery and 690094/690095 committed-actual-sum recovery.

The combined authority question is now resolved by Research:

`sgs-state-mechanics-research/STAGE11_SHARE_LIFESTEAL_AUTHORITY_RESOLUTION.md`

Research authority SHA at the final governance audit: `80c4a9dd435b7ec1ed1baed1a957310159c1232a`.

## Historical falsification result

The reopen established that:
- clean nonlethal Share examples falsified target-only recovery;
- lethal Share and sharer-overflow examples falsified an unconditional committed-actual-sum rule;
- no-Share controls independently supported base CEIL;
- RF-P06's historical recovery FLOOR example was synthetic and did not override the empirical CEIL contract.

Those findings remain provenance. They are not deleted merely because the question was later resolved.

## Superseding combined rule

For one eligible DamageInstance entering DAMAGE_SHARE:

```text
RecoveryBasis =
PrimaryAssignedDamage
+
SharedAssignedDamage
```

Under the conserved Stage9 Share partition:

```text
PrimaryAssignedDamage = Dtarget
SharedAssignedDamage  = Dsharer_theoretical
RecoveryBasis         = Dtotal
```

Target death or troop-cap overkill may reduce committed actual troop loss without shrinking the assignment-owned RecoveryBasis. A Share direct-loss commit does not create a second LifeSteal trigger. Cleave children use their own child partition assignment.

Distribution does not inherit this Share rule.

## Runtime migration status

The assigned-damage Share rule is implemented at Battle audited SHA `eff9efcff878afcdd3a5c8609ef719d18fc58cdf`, and the full suite is green.

This historical authority conflict is **not** the current Runtime Freeze blocker.

The current blocker is separately recorded as **B11-FRZ-001** in `STAGE11_RUNTIME_ADVERSARIAL_AUDIT.md` and `STAGE11_RUNTIME_FREEZE_RECORD.md`: the authority-required recovery-modifier second-stage CEIL has no canonical Runtime owner/test seam.
