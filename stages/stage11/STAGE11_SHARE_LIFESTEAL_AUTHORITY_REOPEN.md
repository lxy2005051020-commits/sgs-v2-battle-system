# Stage11 Share × Life Steal Authority Reopen

Date: 2026-09-25. **RESOLUTION-D: AUTHORITY CONFLICT REMAINS BLOCKED.** This is a Battle documentation mirror of the Research [competition matrix](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/main/STAGE11_SHARE_LIFESTEAL_COMPETITION_MATRIX.md) and [raw-evidence falsification audit](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/main/STAGE11_SHARE_LIFESTEAL_FALSIFICATION_AUDIT.md). It records a scoped formal reopen of the historical Stage9 recovery-basis authority; no Battle Runtime was edited.

## Disposition

1. Stage9 690087 sections 14/23/T12, Cleave section 10.2, RF-P06 sections 10.2/14 and `STAGE9_FREEZE_RECORD.md` Cleave recovery clause are **REOPENED**, not silently superseded. Independently-known-ratio raw nonlethal Share logs refute their target-only observable recovery rule: `304+52` at 9.2% recovers 33 (target-only CEIL 28); `242+43` at 15% recovers 43 (target-only CEIL 37). The Stage9 Share partition, target-first commit/death interrupt, direct-loss lineage, Cleave child admission and Cleave damage FLOOR remain outside this reopen.
2. Research 690094/690095 unconditional `actual primary + actual committed shared` Q12 wording is also **REOPENED**. Raw lethal Share logs show target 36, sharer committed loss 0, fixed 9.2% recovery 8 (committed-loss CEIL 4), and independently target 308, sharer loss 0, fixed 15% recovery 78 (committed-loss CEIL 47). No healing-amplifier event appears in the relevant log windows. The assigned/planned damage was not exposed, so the exact alternative basis cannot be frozen.
   A separate sharer-overflow event has target actual loss 498, sharer actual loss 52, fixed 15% recovery 88, versus committed-sum CEIL 83. The frozen Share partition equation uniquely gives theoretical share 88 and pre-share total 586. This supports a planned/theoretical contribution but cannot distinguish `Dtotal` from `actual primary + planned share` while the target survives.
3. Recovery base **CEIL** is separately supported by no-Share controls: `352 × 9.2% -> 33`, `494 × 15% -> 75`. RF-P06's `floor(267 × 10%) -> 26` is a synthetic recovery vector, not direct mechanism evidence; its Cleave-derived-*damage* FLOOR remains frozen. One recovery trigger per eligible DamageInstance and separate sources remain distinct from basis composition.
4. The corpus search produced no clean Cleave-secondary Share + recovery discriminator. No Cleave-only basis exception or automatic inheritance is newly frozen. Distribution participant recovery remains a separate `PROJECT_RUNTIME_DEFAULT / RESEARCH_DEBT`.

## Existing test provenance and required handling

| Test | Provenance | Next action after authority resolution |
|---|---|---|
| `test_p97_clv_rec_01_share_overkill_recovery_uses_267_not_55` | **Primary C** provisional historical basis; secondary D runtime compatibility; synthetic 314/267/55, not a raw evidence vector | Preserve as conflict fixture. Do not switch expected 267 to 55 or 314 without an independently measured lethal-Share rule. |
| `test_p97_clv_rec_02_distribution_participant_recovery_delegated` | **Primary B** architecture-only; secondary D runtime compatibility; separate Distribution boundary | Keep in Distribution debt review; no Share-based migration. |
| `test_share_nonlethal_sharer_loss_is_excluded_from_recovery` | **Primary C** provisional historical target-only assumption; secondary D compatibility; synthetic 267+47 | Migrate only after formal resolution, with direct fixed-ratio nonlethal Share evidence and a separate lethal Share test. |

The current `Stage11AttackerRecoverySystem` and `CleaveDerivedDamageResolver` already implement an actual committed sum and CEIL in some paths. That behavior matches reviewed nonlethal arithmetic but is **not validated at lethal Share / overflow**. Do not change those files or the failing tests as an authority shortcut. After the next evidence round, inspect `damage_instance_coordinator.py`, `cleave_derived_damage_system.py`, `stage11_attacker_recovery.py`, recovery capacity, and the relevant tests together. The formal Runtime unblock handoff is **withheld** until an exact rule for normal and Cleave Share, especially death/overkill and sharer overflow, is established.

Stage11 Runtime Freeze remains `BLOCKED / NOT FROZEN`; Stage12 remains `NOT READY`. Research Stage11 individual frozen-state counts do not certify the inconsistent combined topology.
