# Stage13-D1 PendingWork Implementation

Date: 2026-10-04. Status: FROZEN / IMPLEMENTED / MAIN CI PASS.

## Owners and entrypoints

- `BattleContext.pending_work`: one per-battle `PendingWorkRegistry`, immutable records and typed trace.
- `BattleSystems.pending_work_system`: one `PendingWorkSystem`; create/cancel/due selection/dispatch/transition.
- `OperationIdAllocator`: stable PendingWorkId plus minimal SkillOperationId, EffectOperationId,
  RecoveryOperationId; separate counters preserve all previous allocation sequences.
- `OperationLineage`: optional parent Skill/Effect/Recovery/StateGeneration/PendingWork fields,
  retaining root Action and parent Damage/NormalAttack fields. No second provenance tree.
- `PendingWorkScheduleSpec`: exact round/phase, next phase, holder next action-start, named future trigger.
- `WorkLifetimeSpec`: ONE_SHOT, UNTIL_EXECUTED, inclusive UNTIL_ROUND implemented;
  REPEAT_N_TIMES reserved, construction raises NotImplementedError.
- `PendingWorkValidityPolicy`: typed source alive/independent and target alive/identity-locked policies.
  Provider/equipment/state/actor/target eligibility reuse ExecutionRightSpec and ExecutionRightSupport.
- `PendingWorkReadPolicy`: declared SNAPSHOT_AT_CREATION / LIVE_AT_EXECUTION keys;
  data-only deep freeze, registered live readers, no silent snapshot/live fallback.

The engine calls `process` after existing ROUND_START hooks, after UNIT_ACTION_START hooks
and state lifetime settlement, and after ROUND_END expiry; each precedes the existing
finalization barrier. Final result projection calls `cancel_future`. Explicit future signals
call `process` with a matching live clock, trigger key and positive occurrence.

## Lifecycle and failure policy

Creation preflights typed inputs, dispatcher/readers, snapshot declaration, future clock,
admission-time permissions and FutureAdmissionGate before allocating identity or storing work.
SNAPSHOT_AT_ADMISSION dimensions are checked at creation, then intentionally skipped at execution.
Due execution independently checks physical source/target requirements and canonical live rights.

Order is explicit creation_sequence; IDs remain non-orderable. Due IDs are captured once,
then records are reread before dispatch so sibling cancellation is effective. Same point
cannot run twice. Reentrant or cross-battle dispatch is rejected. Terminal snapshots are immutable.

Validity failure -> CANCELLED. Deadline/missed exact point -> EXPIRED.
Successful dispatch -> COMPLETED. Exception -> CANCELLED/DISPATCH_FAILED and rethrow;
already committed domain effects are not rolled back and failed work is never retried.
No generic composition/failure rollback framework is implied.

Pending work never registers as an admitted finalization transaction. RUNNING-only future
admission is queried on the existing gate without extending the frozen six Stage9 branch kinds.
Victory latch/finalization cancels outstanding future work, including later members of the
same batch. An executing domain transaction still drains under its existing owner.

## Snapshot/JIT contract examples

Recuperation's frozen RecoveryPotencyContext includes Rate, N, selected Attr, source/target
ordinary modifier pools and red pool. The opt-in adapter requires an explicit immutable
`recovery_potency` projection in PendingWork.snapshot_payload and verifies it against the
original immutable descriptor. HealingBlock/wounded/missing-troop settlement remain live
inside RecoveryOpportunitySystem/RecoverySystem; scheduler does not independently calculate
or cache those domain decisions. Generic live-reader frame behavior is tested separately.

DOT frozen source facts and live target defense/advancement/troops remain in their existing
owners. D1 does not migrate DOT, automatic Recuperation ticks, Sabotage or preparation.
Mechanism adapters must pass frame.lineage to domain ingress that accepts OperationLineage;
dispatch returns the actual typed child operation identity and matching lineage. The
Recuperation bridge allocates a RecoveryOperationId for the delegated invocation and retains
the existing state generation/event payloads. Work lifecycle trace is separate from EventBus.

## Proof and reproducible validation

`tests/test_stage13_d1_pending_work.py`: 37 focused cases, including T1-T8, scheduling/lifetime
boundaries, slot-0 provider invalidation, snapshot admission, deep freeze, lineage, and engine exit.
Recuperation comparisons cover probabilities 0/0.5/1 and the real StateLifecycle -> TriggerSystem
producer path. Result, every domain event, troops/wounds, state generation and RNG continuation match.

`tests/test_stage13_d1_adversarial_audit.py`: 11 independent cases with a separately constructed
context, gate closure inside a batch/read, real lethal DamageInstance transaction, forged lineage,
read failure, missing/unsupported dependencies, reserved repeat rejection and AST ownership audit.

```powershell
python -m pytest -q
python demo.py
python scripts/audit_stage13_d1.py --output .artifacts/stage13_d1_audit.json
```

Local: 1739 passed = 1691 existing + 48 D1; demo PASS; independent audit PASS.
The audit checks 21 frozen owner source hashes against the inspected baseline, then runs
the separate adversarial harness. It is an independent executable harness/source audit,
not a claim of review by another human. CI executes the same command and uploads its JSON
alongside the audit snapshot. Hashes normalize CRLF to LF for Windows/Linux equivalence.

Local verification uses `.venv` because system Python has an unrelated installed `tests`
package that shadows this repository's namespace tests. No tests were weakened for it.

## Deferred contract boundaries

D2 UsageBudget/Frequency (including future repeat admission); D3 composition; D4 attribute
read/modifier provenance; D5 RNG trace; G whole-battle replay/exit audit. Reserved repeated
work cannot dispatch or accidentally consume an extra execution. Full preparation and concrete
skills are not implemented. D1 does not declare Stage13 or the whole engine complete.
