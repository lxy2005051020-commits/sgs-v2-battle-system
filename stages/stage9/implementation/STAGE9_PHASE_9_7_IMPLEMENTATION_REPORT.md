# Stage9 Phase 9.7 Implementation

Starting remote main: `162410de0d32e1c5a5b896bee3bc01904450a647`

Build Prompt blob: `835206ba39ce64c42a822a7138afeee307e0a492`

State authority: `15ed915435f328a6ecd8f488d98b5b9e13c913b5`

Scope: Cleave, Chain and Counter production orchestration. Phase 9.6 remains
COMPLETE / PASS. This is an implementation self-check, not the independent audit.
Next lifecycle step: **Phase 9.7 Independent Implementation Audit**.
Phase 9.8: **NOT STARTED**.

## Authoritative correction to construction instruction 32

The previous implementation stop was a VALID SAFETY STOP CAUSED BY PROMPT DEFECT.
STAGE9 DESIGN REOPEN REQUIRED = NO. The user corrected the construction instruction;
no Frozen authority document was changed.

RF-P06 section 10.2 remains authoritative:

* Cleave derived damage uses the parent main hit's ActualTargetTroopLoss and FLOOR.
* A secondary's troop mutation clamps its post-share Dtarget to current troops.
* Attacker Lifesteal / StrategyRecovery receives secondary post-share Dtarget,
  not that secondary's clamped ActualTargetTroopLoss and not Dsharer.
* Dtarget 267 with 55 remaining troops commits loss 55 and supplies recovery basis 267.
* Distribution participant recovery attribution remains the 690094/690095
  contract's decision. Cleave exposes its primary resolved fact and a delegation
  marker; it does not independently add or exclude external attributed losses.
* FirstAid has its own callback input. It does not reuse the attacker recovery fact.

## Production implementation and ownership

`BattleSystems` constructs one instance of each reaction service. NormalAttackSystem
keeps ordering ownership: main damage, Cleave effects with inline secondary Chain,
deferred main Chain, Counter batch, existing Assault seam, Combo checkpoint.
The shared callback is also injected into DamageInstanceCoordinator, so the existing
EffectExecutor ingress for ACTIVE_SKILL and PERIODIC_DAMAGE reaches Chain without
reverse inference from Stage8 DamageSourceType.

`CleaveDerivedDamageResolver` has its own immutable request/result types. It uses
ExactRatio/FLOOR, the existing hit resolver with Evasion before Resistance, shared
partition calculation, DirectTroopLossResolver, TroopSystem, separate recovery
inputs, and the shared Chain callback. It never synthesizes a standard DamageRequest
or DamageResult and never calls Stage8 base formula, modifiers or Crit. CleaveEffect
freezes each effect's secondary plan; targets are checked alive immediately before
execution. Effects use authoritative skill slots, run effect-major, and have no
NormalAttack identity of their own. Removed future sources are skipped before admission.

ChainDeferredWork retains parent damage, trigger node, trigger amount and provenance.
ChainSystem uses the battle slot roster once, a monotonic cursor, and current linked
state/liveness at each step. The trigger's current Chain owner and ratio govern
feedback. An applier's death alone does not cancel the link. Feedback commits only
restricted true troop loss, attribution and death observation: no standard damage,
hit, partition, FirstAid or recursive reaction pipeline.

CounterSystem consumes an already-issued permit before snapshotting eligible state
entries and allocating their IDs. CounterBatch and entries are immutable. Later
removal or suppression does not revoke admitted entries; current owner death does.
A dead target emits CounterExecute plus attributed zero loss, with no damage instance,
formula or callbacks. A live target uses a standard WEAPON/COUNTER damage instance and
the existing formula/partition/callback route. ExactRatio is converted at the unchanged
Stage8 coefficient boundary; no new Stage9 integerization rule is introduced.

All three admitted operation types register exact context-bound capability objects
with the existing finalization coordinator. Their admitted and executing lifetimes
hold its barrier. Execution is one-shot; completed, copied and foreign capabilities
fail. After victory latch, new global permits are denied while admitted local steps
drain. Only a Counter batch can authorize a local standard-damage continuation;
Cleave and Chain capabilities cannot unlock that formula route.

## Necessary integration seams

| File | Why required; frozen owner preserved |
| --- | --- |
| battle_finalization_coordinator.py | Registers the three real operation lifetimes and local damage continuation; remains the sole finalization owner. |
| damage_instance_coordinator.py | Forwards immutable resolved facts and accepts authenticated Counter local continuation; contains no Chain state lookup or admission decision. |
| damage_partition_system.py | Extracts existing amount-based calculation into a shared private routine and exposes typed derived input; the original standard plan contract and all Share/Distribution arithmetic remain unchanged. |
| normal_attack_system.py | Orders the new services and owns COUNTER_BATCH admission; target selection, action grants, Assault seam and Combo rules retain their previous owners. |
| stage9_state_runtime.py | Reads typed Cleave/Chain/Counter states and source slots; StateRegistry remains the sole store. Counter eligibility is read at admission only. |
| state_lifecycle_system.py | Applies same-source Cleave/Counter refresh and Chain replacement through the existing sole mutation owner. |
| official_state_catalog.py | Connects the three existing official IDs to their already-frozen typed parameter classes. |
| events.py | Adds observation events for slot traversal, feedback and Counter execution/zero loss; adds no SourceType or FutureBranch. |
| battle_systems.py | Wires unique production instances and explicit effect-owned hit/recovery/eligibility adapters. |

## Evidence limits and deterministic defaults

This phase does not activate Stage8 official DEFER mappings. Existing generic hit
policies can be supplied through `cleave_hit_rules`; prevention consumption belongs
to that policy's effect owner. FirstAid and attacker recovery are distinct optional
effect-owned adapters. Tests exercise the actual hit resolver and RecoverySystem
through those adapters, not newly invented official formulas. The Dtarget recovery
fact exists independently of whether an eligible recovery source is present.

Counter source-specific eligibility may be supplied by its contract owner through
`counter_operationality`. The immutable batch does not consult that policy again.
Absent a policy, typed registered Counter states are eligible. This does not claim
to implement individual tactic suppression predicates. Existing lifecycle expiration
remains authoritative; no new duration model is introduced here.

Counter entry ordering is a PROJECT_DETERMINISTIC_DEFAULT: available skill slots
first, with stable registration order for equal/absent slots. It is not claimed as
an official mechanic. Cleave's slot requirement is authoritative and rejects missing
or duplicate required slots. Stage7/8 evidence gates and unresolved mappings remain
unchanged. Green tests establish the implemented contracts, not unknown game mechanics.

## Regression evidence

Test file: `tests/test_stage9_phase_9_7_cleave_chain_counter.py` (77 cases including
parameterized cases). Existing baseline: 591 passed. Final full pytest: **668 passed**.
Command: `python -m pytest -q --tb=short`. Demo: `python demo.py`, exit 0,
round 7 A-team victory after B-team commander defeat.

| Gate | Result | Evidence |
| --- | --- | --- |
| CleaveDerivedDamageResolver | PASS | Dedicated typed request/result and production secondary execution |
| Cleave basis ActualTargetTroopLoss / FLOOR | PASS | REG-CLV-01, REG-INT-05: 55 x 0.54 -> 29 |
| Cleave formula re-entry | BLOCKED | Formula/modifier spies fail if entered |
| Cleave source slot / effect-major / JIT secondary | PASS | Missing slot domain error, ordered two effects, skipped dead secondary, no replacement |
| Cleave missing required slot | DOMAIN ERROR | No effect identity allocated |
| Cleave recursive trigger | BLOCKED | Typed permission tests |
| REG-CLV-01..05 / INV-13..18 | PASS | Derived basis, hit/recovery/partition permissions, 0/1/2 targets, post-Guard anchor |
| P97-CLV-REC-01 | PASS | Dtarget 267, actual 55, recovery 267; nonlethal case also proves actual sharer loss 47 excluded |
| P97-CLV-REC-02 | PASS | Distribution participant loss exists but recovery attribution remains delegated |
| DamageCallbackAdmissionPoint | PASS | Shared typed ingress and real EffectExecutor ACTIVE_SKILL/PERIODIC_DAMAGE integration |
| ChainSystem self-admission | BLOCKED | Only DamageCallbackAdmissionPoint requests CHAIN_TRAVERSAL |
| Chain snapshot/live split / monotonic cursor | PASS | Live owner replacement, removed trigger, late link, no revisit |
| Chain TRUE_FEEDBACK restricted settlement | PASS | Exact feedback with forbidden pipeline spies |
| CHAIN_TRUE_FEEDBACK standard DamageRequest | 0 | Direct restricted settlement only |
| Chain recursive trigger | BLOCKED | Feedback/share/distribution direct losses cannot admit traversal |
| REG-CHN-01..04 | PASS | Narrow snapshot, cursor, commander-death drain, zero-damage traversal |
| Counter trigger-time immutable batch | PASS | Removal and post-admission eligibility change do not revoke |
| Counter owner liveness gate | PASS | Dead owner yields no CounterExecute |
| Counter dead-target zero terminal | PASS | Second entry executes at zero after first kills target; no pipeline invocation |
| Positive Counter standard DamageInstance | PASS | Real Stage8 formula, Share and Chain integration |
| Counter recursive trigger | BLOCKED | Typed lineage permission matrix |
| REG-CTR-01..05 | PASS | Immutable membership, owner death, zero drain, skipped positive pipeline, Combo blocked |
| Cleave / Chain / Counter FutureAdmission no-bypass | PASS | Missing, forged, foreign-gate, wrong-parent, wrong-branch and replayed permits fail without new IDs |
| CleaveEffect / ChainTraversal / CounterBatch finalization barrier | PASS | Real admitted/executing/completed operations and foreign/copied capability rejection |
| FINAL_01 / FINAL_02 / FINAL_04 | PASS | Chain commander drain / Counter zero drain / current Cleave effect drain |
| INV-32..42 | PASS | Snapshot, liveness, restricted routes, immutable entries, real barriers, typed capability checks |
| REG-INT-01 | PASS | Production main -> Cleave/inline Chain -> deferred Chain -> Counter ordering |
| REG-INT-05 | PASS | Main overkill uses actual loss for derived damage |
| All six FutureBranch families structurally permit-gated | PASS | Existing Phase9.6 coverage plus three new factory families and latch denials |
| Stage9.5 damage route / Phase9.6 regression | PASS | All 591 baseline tests remain green |
| Tests / Demo | PASS | 668 passed / exit 0 |
| Phase 9.7 Implementation Gate | PASS | Implementation self-check; independent audit next |

## Diff and delivery audit

Comparison uses the exact GitHub baseline blob contents, not an old local checkout.
Git transport was unavailable, so delivery uses GitHub Git-data tree/commit/ref
operations with the exact baseline parent and a non-force main update. Remote main
is checked again before ref advancement. The committed tree includes only these
implementation files, the regression file and this report; validation fixtures,
downloaded authority copies and logs are not uploaded.

* STAGE9_BUILD_PROMPT diff = 0; all Frozen authority edits = 0.
* State authority repository writes = 0.
* Stage8 semantic changes / reopen = 0 / NO.
* Phase9.6 gameplay changes = 0 beyond the documented reaction integration seams.
* Assault gameplay = NOT IMPLEMENTED; Phase9.8 leakage = 0.
* New FutureBranch / SourceType / integerization rules = 0.
* Reverse DamageSourceType inference = 0.
* context.ended writes outside Engine = 0.

No freeze certification is asserted by this report. Stop for the independent
Phase 9.7 implementation audit; do not start Phase 9.8.
