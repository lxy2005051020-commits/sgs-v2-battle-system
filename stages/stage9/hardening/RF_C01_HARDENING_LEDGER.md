# RF-C01 Hardening Ledger

Package: `RF-C01 — IMPLEMENTATION_HARDENING`

Scope: translate already-frozen Stage9 semantics into typed runtime invariants, admission/liveness rules, data-structure contracts, regression specifications, and implementation guardrails. This ledger does **not** create new game rules and does **not** reopen Stage8.

## Baseline authority

- RF-P01: integerization call sites frozen.
- RF-P02: NormalAttack lifecycle ownership and Combo grant model repaired.
- RF-P03: execution-right/death scope frozen.
- RF-P04: battle finalization barrier frozen; `DSTS9-B02` runtime side closed by explicit project engineering default while empirical status remains open.
- RF-P05: Share target-death interrupt confirmed; Distribution ordinary participant-death continuation confirmed.
- RF-P06: Cleave base = `ActualTargetTroopLoss`; Cleave integerization = `FLOOR`.
- RF-P07: Cleave source-bound effect list, effect-major ordering, global-slot secondary ordering, and JIT liveness revalidation frozen.

## HARDENING_LEDGER

| Finding ID | Mechanism | Frozen semantic source | Runtime risk | Required type / invariant | Required regression | Production code now? | Closure proof |
|---|---|---|---|---|---|---|---|
| `SHS9-N01` | Share / Distribution replacement | Damage Share P0 + Distribution P0; replacement is not suppression | A displaced Distribution instance could be left dormant and accidentally resume when Share expires | Exclusive `DamagePartitionSelection`; displaced cross-family instance enters terminal replaced state and cannot resurrect | `REG-SHR-04` Share replaces Distribution; after Share expires the displaced Distribution does not resume | NO | `CLOSED BY RUNTIME CONTRACT` |
| `TAS9-H01` | Taunt / Combo death boundary | TAUNT audit finding superseded by RF-P03 reachable-death classification | Old lower-authority open-action-death wording could incorrectly let a dead actor reach Combo #2 and re-read Taunt | Future-branch admission requires live actor and non-finalized battle; target selector is never entered for dead actor after #1 death | `REG-CMB-05` dead actor after #1 cannot admit #2, therefore no Taunt/Confusion/Guard target pass occurs | NO | `CLOSED BY RF-P03 + RF-C01 REGRESSION CONTRACT` |
| `GDS9-H01` | Guard | Guard P0 | One mutable `targetId` can silently change meaning from selected target to redirected recipient; recursive Guard is easy to introduce | Typed `SelectedTarget`, `IntendedAttackTarget`, `PostRedirectActualTarget`, `DamageRecipient`; one atomic `TargetResolutionResult`; one Guard pass | `REG-TGT-03`, `04`, `05`, `06`, `07` | NO | `CLOSED BY RUNTIME CONTRACT` |
| `CBS9-H01` | Combo / death / execution right | RF-P02 + RF-P03 + RF-P04 | A generic `if actor.is_dead` or `if battle.finished` can cancel admitted work or allow forbidden future branches | `ComboStateInstance`, `ComboActionGrant`, `ComboCheckpointState`; scoped `can_admit_new_work()` plus local liveness gates | `REG-CMB-01..05`, `REG-FIN-02..03` | NO | `CLOSED BY RF-P03/RF-P04 + RF-C01 RUNTIME CONTRACT` |
| `CLVS9-H01` | Cleave | RF-P06 + RF-P07 | Cleave can be implemented as another full normal `DamageRequest`, re-entering formulas/modifiers/Crit/Counter | Typed `DerivedDamageRequest` with `sourceType=CLEAVE`, inherited `damageType`, `baseFact=ActualTargetTroopLoss`, `integerization=FLOOR`, `normalAttackIdentity=false`, explicit permission policy | `REG-CLV-01..05`, `REG-INT-05` | NO | `CLOSED BY RUNTIME CONTRACT` |
| `CHNS9-H01` | Chain | Chain P0 + RF-P01 + RF-P04 | Giant snapshot can freeze fields that must be live-read; generic damage re-entry can reopen forbidden callbacks; visited slots can repeat | `ChainDeferredWork{immutableTriggerSnapshot,liveExecutionLookup}` + typed `ChainTraversalId` + visited-slot set + restricted settlement policy | `REG-CHN-01..04`, `REG-FIN-01`, `REG-INT-01` | NO | `CLOSED BY RUNTIME CONTRACT` |
| `SHS9-H01` | Damage partition arbitration | Damage Share P0 + Distribution P0 | Share and Distribution may both execute serially against one DamageEvent | Single `DamagePartitionResolver` returning exactly one of `SHARE`, `DISTRIBUTION`, `NONE` | `REG-SHR-04` plus partition exclusivity assertion | NO | `CLOSED BY RUNTIME CONTRACT` |
| `SHS9-H02` | Share / Distribution participant loss | Damage Share P0 + Distribution P0 | Participant loss may be represented as DamageEvent and recursively trigger defense, hit callbacks, Share/Distribution, Chain, FirstAid, Counter | Typed `AttributedDirectTroopLoss`; no `DamageType` unless a future P0 explicitly gives one; `normalHitPipeline=false` invariant | `REG-SHR-03`, `REG-DST-04` | NO | `CLOSED BY RUNTIME CONTRACT` |
| `DSTS9-H01` | Distribution | Distribution P0 + RF-P05 + RF-P04 runtime default | Re-reading `current_allies` inside the loop can change N, amounts, ordering, or add new participants | Immutable `DistributionTransactionPlan{participantIds,N,Dtarget,Dparticipant}`; per-step JIT eligibility can only SKIP | `REG-DST-01..04`, `REG-FIN-06` | NO | `CLOSED BY RUNTIME CONTRACT` |
| `CTS9-H01` | Counter | Counter P0 + RF-P03 | Trigger-time state admission can be confused with execution-time owner liveness; suppression/removal might wrongly revoke queued entry | Immutable `CounterBatchEntry` admission snapshot + separate execution-time `ownerAlive` gate | `REG-CTR-01`, `REG-CTR-02` | NO | `CLOSED BY RUNTIME CONTRACT` |
| `CTS9-H02` | Counter / finalization | Counter P0 + RF-P04 | Commander death caused by C1 may cause premature global finalization and delete already-admitted C2 | `ReactionBatchId`, immutable batch membership, `BattleTerminationState=VICTORY_LATCHED/DRAINING_ADMITTED_WORK` until batch drain | `REG-CTR-03`, `REG-FIN-02` | NO | `CLOSED BY RF-P04 + RF-C01 REGRESSION CONTRACT` |
| `CTS9-H03` | Counter dead-target sibling | Counter P0 + RF-P04 | C2 can re-enter full weapon formula against a target already at 0 troops and accidentally trigger Evasion/Resistance/Share/Chain/FirstAid | Explicit `CounterZeroLossTerminalPath`; emits CounterExecute + attributed zero troop loss only | `REG-CTR-04`, `REG-FIN-02` | NO | `CLOSED BY RUNTIME CONTRACT` |

## Ledger verdict

```text
Finding count                 = 12
CLOSED BY RUNTIME CONTRACT    = 12
REMAINS OPEN                  = 0
P0 conflict discovered        = 0
Production code changed       = NO
Stage8 formal reopen          = NO
```
